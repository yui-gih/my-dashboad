"""
YouTube解析エージェント (LangGraph StateGraph)。

グラフ構造:
  fetch_channels → fetch_new_videos → fetch_transcripts
    ↓ (クォータ超過チェック)
  analyze_videos → save_results → END

各ノードの実行状態を StateGraph で明示的に管理し、
クォータ超過・エラー時の安全停止と再実行を実現する。
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import TypedDict, Annotated
import operator

from googleapiclient.discovery import build
from langgraph.graph import StateGraph, END

from src.config import settings
from src.db import get_supabase
from .quota_manager import quota_manager
from .transcript import fetch_transcript, TranscriptSource
from .summarizer import summarize, ANALYSIS_VERSION
from .priority import calculate_priority_score, get_text_embedding

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# State 定義
# ──────────────────────────────────────────────

class AgentState(TypedDict):
    run_id: str
    channels: list[dict]          # {channel_id, channel_title, uploads_playlist_id, weight}
    new_videos: list[dict]        # YouTube API のレスポンス
    videos_with_content: list[dict]  # transcript / description 付き
    analyzed_videos: list[dict]   # AI 解析済み
    quota_used: int               # このラン中の消費クォータ
    errors: Annotated[list, operator.add]  # エラーを蓄積 (上書きしない)
    steps: Annotated[list, operator.add]  # 実行ログ


def _log_step(state: AgentState, node: str, message: str, quota: int = 0) -> dict:
    step = {
        "node": node,
        "message": message,
        "quotaUsed": quota,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "success",
    }
    logger.info(f"[{node}] {message}")
    return {"steps": [step], "quota_used": state["quota_used"] + quota}


# ──────────────────────────────────────────────
# ノード実装
# ──────────────────────────────────────────────

def fetch_channels(state: AgentState) -> dict:
    """
    DBからユーザーの登録チャンネル一覧を取得。
    uploads_playlist_id は UC→UU 変換で APIコールなしに算出。
    """
    db = get_supabase()
    result = db.table("user_channel_weights").select("*").execute()
    channels = []
    for row in result.data:
        channel_id = row["channel_id"]
        # UC→UU 変換: APIコールゼロでアップロードプレイリストIDを取得
        uploads_id = row.get("uploads_playlist_id") or ("UU" + channel_id[2:])
        channels.append({
            "channel_id": channel_id,
            "channel_title": row["channel_title"],
            "uploads_playlist_id": uploads_id,
            "weight": row.get("weight", 0.5),
        })

    update = _log_step(state, "fetch_channels", f"{len(channels)}チャンネルを取得")
    update["channels"] = channels
    return update


def fetch_new_videos(state: AgentState) -> dict:
    """
    各チャンネルの最新5件を playlistItems.list (1 unit/call) で取得。
    search.list (100 units) は使用しない。
    """
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
    new_videos = []
    quota_used = 0

    db = get_supabase()
    # 既存の video_id を取得（重複スキップ用）
    existing = db.table("youtube_videos").select("video_id").execute()
    existing_ids = {row["video_id"] for row in existing.data}

    for ch in state["channels"]:
        try:
            # playlistItems.list: 1 unit
            response = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=ch["uploads_playlist_id"],
                maxResults=5,
            ).execute()
            quota_used += 1

            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                if video_id in existing_ids:
                    continue
                snippet = item["snippet"]
                new_videos.append({
                    "video_id": video_id,
                    "channel_id": ch["channel_id"],
                    "channel_title": ch["channel_title"],
                    "channel_weight": ch["weight"],
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "published_at": snippet["publishedAt"],
                    "thumbnail_url": (
                        snippet.get("thumbnails", {}).get("high", {}).get("url")
                        or snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                    ),
                })
        except Exception as e:
            logger.error(f"Failed to fetch videos for {ch['channel_id']}: {e}")

    update = _log_step(
        state, "fetch_new_videos",
        f"{len(new_videos)}件の新着動画を検知 (quota: {quota_used})",
        quota=quota_used,
    )
    update["new_videos"] = new_videos
    return update


def fetch_transcripts(state: AgentState) -> dict:
    """字幕または概要欄をフォールバック付きで取得"""
    videos_with_content = []
    for video in state["new_videos"]:
        text, source = fetch_transcript(video["video_id"])
        if text is None:
            # 概要欄フォールバック
            text = video.get("description") or video["title"]
            source = (
                TranscriptSource.DESCRIPTION
                if video.get("description")
                else TranscriptSource.TITLE_ONLY
            )
        videos_with_content.append({**video, "content": text, "transcript_source": source.value})

    update = _log_step(
        state, "fetch_transcripts",
        f"{len(videos_with_content)}件の字幕/概要を取得完了",
    )
    update["videos_with_content"] = videos_with_content
    return update


def should_continue(state: AgentState) -> str:
    """
    クォータ安全閾値チェック。
    超過した場合は解析をスキップして保存フェーズへ。
    """
    remaining = settings.youtube_quota_daily_limit - state["quota_used"]
    if remaining < settings.youtube_quota_daily_limit * 0.2:
        logger.warning(f"Quota threshold reached. Remaining: {remaining}. Skipping analysis.")
        return "save"
    return "analyze"


async def analyze_videos(state: AgentState) -> dict:
    """
    各動画を並列で AI 解析。
    - Map-Reduce 要約
    - 埋め込みベクトル生成
    - パーソナライズ優先度スコア算出
    """
    async def process_one(video: dict) -> dict:
        content = video["content"]
        metadata = {
            "video_id": video["video_id"],
            "title": video["title"],
            "channel_title": video["channel_title"],
        }
        published_at = datetime.fromisoformat(
            video["published_at"].replace("Z", "+00:00")
        )

        # AI要約（失敗してもフォールバック）
        try:
            summary, tokens = await summarize(content, metadata)
        except Exception as e:
            logger.warning(f"Summarize failed for {video['video_id']}: {e}")
            summary = {"headline": video["title"], "keyPoints": [], "investmentAngle": ""}
            tokens = 0

        # 埋め込み（失敗してもゼロベクトル）
        try:
            embedding = await get_text_embedding(f"{video['title']} {content[:2000]}")
        except Exception as e:
            logger.warning(f"Embedding failed for {video['video_id']}: {e}")
            embedding = [0.0] * 1536

        # 優先度スコア
        try:
            priority_score = await calculate_priority_score(
                embedding, video["channel_id"], published_at
            )
        except Exception as e:
            logger.warning(f"Priority score failed for {video['video_id']}: {e}")
            priority_score = float(video.get("channel_weight", 0.5))

        return {
            **video,
            "summary": summary,
            "content_embedding": embedding,
            "priority_score": priority_score,
            "llm_tokens_used": tokens,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    results = await asyncio.gather(*[
        process_one(v) for v in state["videos_with_content"]
    ])
    analyzed = [r for r in results if r is not None]

    update = _log_step(
        state, "analyze_videos",
        f"{len(analyzed)}/{len(state['videos_with_content'])}件の解析完了",
    )
    update["analyzed_videos"] = analyzed
    return update


def save_results(state: AgentState) -> dict:
    """解析済み動画を Supabase に保存（Realtime で UI に即時反映）"""
    db = get_supabase()
    saved = 0
    for video in state["analyzed_videos"]:
        try:
            db.table("youtube_videos").upsert({
                "video_id": video["video_id"],
                "channel_id": video["channel_id"],
                "channel_title": video["channel_title"],
                "title": video["title"],
                "published_at": video["published_at"],
                "thumbnail_url": video.get("thumbnail_url"),
                "transcript_source": video["transcript_source"],
                "priority_score": video["priority_score"],
                "summary": video["summary"],
                "content_embedding": video["content_embedding"],
                "analysis_version": ANALYSIS_VERSION,
                "llm_tokens_used": video["llm_tokens_used"],
                "analyzed_at": video["analyzed_at"],
            }, on_conflict="video_id").execute()
            saved += 1
        except Exception as e:
            logger.error(f"Save failed for {video['video_id']}: {e}")

    # 実行ログを DB に保存
    db.table("agent_run_logs").update({
        "status": "success",
        "steps": state["steps"],
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", state["run_id"]).execute()

    update = _log_step(state, "save_results", f"{saved}件をDBに保存完了")
    return update


# ──────────────────────────────────────────────
# グラフ構築
# ──────────────────────────────────────────────

def build_youtube_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("fetch_channels", fetch_channels)
    workflow.add_node("fetch_new_videos", fetch_new_videos)
    workflow.add_node("fetch_transcripts", fetch_transcripts)
    workflow.add_node("analyze_videos", analyze_videos)
    workflow.add_node("save_results", save_results)

    workflow.set_entry_point("fetch_channels")
    workflow.add_edge("fetch_channels", "fetch_new_videos")
    workflow.add_edge("fetch_new_videos", "fetch_transcripts")

    # クォータチェックによる条件分岐
    workflow.add_conditional_edges(
        "fetch_transcripts",
        should_continue,
        {"analyze": "analyze_videos", "save": "save_results"},
    )
    workflow.add_edge("analyze_videos", "save_results")
    workflow.add_edge("save_results", END)

    return workflow.compile()


youtube_agent = build_youtube_agent()


async def run_youtube_agent() -> str:
    """エージェントを実行し、run_id を返す"""
    db = get_supabase()
    run_log = db.table("agent_run_logs").insert({
        "agent_name": "youtube",
        "status": "running",
    }).execute()
    run_id = run_log.data[0]["id"]

    initial_state: AgentState = {
        "run_id": run_id,
        "channels": [],
        "new_videos": [],
        "videos_with_content": [],
        "analyzed_videos": [],
        "quota_used": 0,
        "errors": [],
        "steps": [],
    }

    await youtube_agent.ainvoke(initial_state)
    return run_id
