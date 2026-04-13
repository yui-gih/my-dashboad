"""
FastAPI ルート定義。
/agent/stream エンドポイントは SSE (Server-Sent Events) でエージェントの
実行ステップをリアルタイムにフロントエンドへ配信する。
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.config import settings
from src.db import get_supabase
from src.agents.youtube import run_youtube_agent
from src.agents.news import run_news_agent
from src.agents.portfolio import run_portfolio_agent

router = APIRouter()
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 山情報
# ──────────────────────────────────────────────

MOUNTAINS = [
    {"name": "富士山",     "elevation": 3776, "lat": 35.3606, "lon": 138.7274, "prefecture": "静岡/山梨"},
    {"name": "北岳",       "elevation": 3193, "lat": 35.6755, "lon": 138.2364, "prefecture": "山梨"},
    {"name": "槍ヶ岳",     "elevation": 3180, "lat": 36.3417, "lon": 137.6481, "prefecture": "長野/岐阜"},
    {"name": "八ヶ岳(赤岳)", "elevation": 2899, "lat": 35.9700, "lon": 138.3700, "prefecture": "長野/山梨"},
    {"name": "白馬岳",     "elevation": 2932, "lat": 36.7581, "lon": 137.7619, "prefecture": "長野"},
]

@router.get("/mountains/weather")
async def get_mountain_weather():
    if not settings.openweather_api_key:
        return {"mountains": []}
    results = []
    async with httpx.AsyncClient() as http:
        for m in MOUNTAINS:
            try:
                resp = await http.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "lat": m["lat"], "lon": m["lon"],
                        "appid": settings.openweather_api_key,
                        "units": "metric", "lang": "ja",
                    },
                    timeout=10,
                )
                d = resp.json()
                # 山頂気温推定: 計測地点から標高差で補正 (-0.65°C/100m)
                base_temp = d["main"]["temp"]
                results.append({
                    "name": m["name"],
                    "elevation": m["elevation"],
                    "prefecture": m["prefecture"],
                    "temp": round(base_temp),
                    "windSpeed": round(d["wind"]["speed"]),
                    "description": d["weather"][0]["description"],
                    "humidity": d["main"]["humidity"],
                    "icon": d["weather"][0]["icon"],
                })
            except Exception as e:
                logger.warning(f"Mountain weather failed for {m['name']}: {e}")
    return {"mountains": results}


MOUNTAIN_DB: dict[str, tuple[float, float, int, str]] = {
    # 富士山
    "富士山": (35.3606, 138.7274, 3776, "静岡/山梨"),
    # 北アルプス
    "奥穂高岳": (36.2886, 137.6472, 3190, "長野/岐阜"),
    "穂高岳":   (36.2886, 137.6472, 3190, "長野/岐阜"),
    "北穂高岳": (36.3061, 137.6481, 3106, "長野/岐阜"),
    "前穂高岳": (36.2867, 137.6386, 3090, "長野"),
    "大喰岳":   (36.3292, 137.6508, 3101, "長野"),
    "乗鞍岳":   (36.1067, 137.5531, 3026, "長野/岐阜"),
    "剱岳":     (36.6222, 137.6164, 2999, "富山"),
    "立山":     (36.5750, 137.6133, 3015, "富山"),
    "雄山":     (36.5750, 137.6133, 3003, "富山"),
    "薬師岳":   (36.5014, 137.6244, 2926, "富山"),
    "黒部五郎岳":(36.4561, 137.5814, 2840, "富山/岐阜"),
    "水晶岳":   (36.4664, 137.6417, 2986, "富山/長野"),
    "鷲羽岳":   (36.4311, 137.6436, 2924, "長野/富山"),
    "笠ヶ岳":   (36.3514, 137.5614, 2898, "岐阜"),
    "常念岳":   (36.3403, 137.8058, 2857, "長野"),
    "白馬岳":   (36.7581, 137.7619, 2932, "長野"),
    "五竜岳":   (36.6622, 137.7436, 2814, "長野/富山"),
    "鹿島槍ヶ岳":(36.6303, 137.7250, 2889, "長野/富山"),
    "爺ヶ岳":   (36.5989, 137.7431, 2670, "長野"),
    # 南アルプス
    "北岳":     (35.6755, 138.2364, 3193, "山梨"),
    "間ノ岳":   (35.6481, 138.2272, 3190, "山梨/静岡"),
    "悪沢岳":   (35.5619, 138.1831, 3141, "静岡"),
    "赤石岳":   (35.5028, 138.1717, 3121, "静岡"),
    "聖岳":     (35.4208, 138.1417, 3013, "静岡/長野"),
    "塩見岳":   (35.6222, 138.1981, 3047, "静岡/長野"),
    "仙丈ヶ岳": (35.7217, 138.1842, 3033, "山梨/長野"),
    "甲斐駒ヶ岳":(35.7667, 138.2367, 2967, "山梨/長野"),
    # 八ヶ岳
    "赤岳":     (35.9700, 138.3700, 2899, "長野/山梨"),
    "八ヶ岳":   (35.9700, 138.3700, 2899, "長野/山梨"),
    "蓼科山":   (36.1000, 138.3053, 2531, "長野"),
    # 中部・近畿
    "御嶽山":   (35.8928, 137.4803, 3067, "長野/岐阜"),
    "木曽駒ヶ岳":(35.7778, 137.8000, 2956, "長野"),
    "空木岳":   (35.7000, 137.8167, 2864, "長野"),
    "伊吹山":   (35.4178, 136.4064, 1377, "滋賀/岐阜"),
    # 上信越
    "妙高山":   (36.8889, 138.1136, 2454, "新潟"),
    "火打山":   (36.9178, 138.1267, 2462, "新潟"),
    "雨飾山":   (36.8717, 137.9803, 1963, "新潟/長野"),
    "谷川岳":   (36.8594, 138.9261, 1977, "群馬/新潟"),
    "苗場山":   (36.9119, 138.6697, 2145, "新潟/長野"),
    "浅間山":   (36.4061, 138.5236, 2568, "群馬/長野"),
    "草津白根山":(36.6219, 138.5317, 2165, "群馬"),
    # 東北
    "会津駒ヶ岳":(37.2028, 139.3317, 2133, "福島"),
    "那須岳":   (37.1150, 139.9719, 1915, "栃木"),
    "磐梯山":   (37.6042, 140.0742, 1816, "福島"),
    "月山":     (38.5556, 140.0194, 1984, "山形"),
    "鳥海山":   (39.1028, 140.0564, 2236, "山形/秋田"),
    "蔵王山":   (38.1431, 140.4467, 1841, "山形/宮城"),
    "岩手山":   (39.8500, 141.0000, 2038, "岩手"),
    "八甲田山": (40.6540, 140.8773, 1585, "青森"),
    # 北海道
    "大雪山":   (43.6644, 142.8597, 2291, "北海道"),
    "旭岳":     (43.6644, 142.8597, 2291, "北海道"),
    "トムラウシ":(43.5239, 142.8308, 2141, "北海道"),
    "十勝岳":   (43.4142, 142.6983, 2077, "北海道"),
    "羊蹄山":   (42.8278, 140.8058, 1898, "北海道"),
    # 中国・四国・九州
    "大山":     (35.3708, 133.5497, 1729, "鳥取"),
    "石鎚山":   (33.7636, 133.1125, 1982, "愛媛"),
    "剣山":     (33.8444, 134.0878, 1955, "徳島"),
    "阿蘇山":   (32.8842, 131.1044, 1592, "熊本"),
    "霧島山":   (31.9336, 130.8636, 1700, "宮崎/鹿児島"),
    "屋久島":   (30.4711, 130.5261, 1936, "鹿児島"),
}

@router.get("/mountains/search")
async def search_mountain_weather(q: str):
    """山名で天気を検索（座標DBによる部分一致）"""
    if not settings.openweather_api_key:
        return {"mountain": None, "error": "API key not configured"}

    # 完全一致 → 前方一致 → 部分一致 の順で検索
    key = q.strip()
    matched_name = None
    matched_info = None
    for name, info in MOUNTAIN_DB.items():
        if key == name:
            matched_name, matched_info = name, info
            break
    if not matched_name:
        for name, info in MOUNTAIN_DB.items():
            if name.startswith(key) or key.startswith(name):
                matched_name, matched_info = name, info
                break
    if not matched_name:
        for name, info in MOUNTAIN_DB.items():
            if key in name or name in key:
                matched_name, matched_info = name, info
                break

    if not matched_info:
        suggestions = [n for n in MOUNTAIN_DB if key[0] in n] if key else []
        hint = "・".join(suggestions[:5]) if suggestions else "富士山・乗鞍岳・御嶽山・谷川岳・大雪山"
        return {"mountain": None, "error": f"「{key}」は見つかりませんでした。例: {hint}"}

    lat, lon, elevation, prefecture = matched_info
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key, "units": "metric", "lang": "ja"},
                timeout=10,
            )
            d = resp.json()
            return {
                "mountain": {
                    "name": matched_name,
                    "elevation": elevation,
                    "prefecture": prefecture,
                    "temp": round(d["main"]["temp"]),
                    "windSpeed": round(d["wind"]["speed"]),
                    "description": d["weather"][0]["description"],
                    "humidity": d["main"]["humidity"],
                    "icon": d["weather"][0]["icon"],
                },
                "error": None,
            }
    except Exception as e:
        logger.warning(f"Mountain search failed for '{q}': {e}")
        return {"mountain": None, "error": "気象データの取得に失敗しました"}


# ──────────────────────────────────────────────
# AI ニュース
# ──────────────────────────────────────────────

LEDGE_AI_API = "https://public-strapi-v5.api.ledge-ai.the-ai.jp/api/v1/articles"

@router.get("/agent/ai-news/articles")
async def get_ai_news(limit: int = 20):
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                LEDGE_AI_API,
                params={
                    "pagination[pageSize]": limit,
                    "sort": "publishedAt:desc",
                },
                timeout=15,
            )
            data = resp.json()
            articles = []
            for a in data.get("data", []):
                slug = a.get("slug", "")
                articles.append({
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, slug)),
                    "title": a.get("title", ""),
                    "url": f"https://ledge.ai/articles/{slug}",
                    "source": "ledge.ai",
                    "publishedAt": a.get("publishedAt"),
                    "summary": a.get("meta_description") or "",
                })
            return {"articles": articles}
    except Exception as e:
        logger.warning(f"ledge.ai API fetch failed: {e}")
        return {"articles": []}


# ──────────────────────────────────────────────
# Strava
# ──────────────────────────────────────────────

_strava_token_cache: dict = {}


async def get_strava_access_token() -> str:
    """リフレッシュトークンからアクセストークンを取得（キャッシュあり）"""
    import time
    if isinstance(_strava_token_cache.get("expires_at"), (int, float)) and _strava_token_cache["expires_at"] > time.time() + 60:
        return _strava_token_cache["access_token"]

    async with httpx.AsyncClient() as http:
        resp = await http.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "refresh_token": settings.strava_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        data = resp.json()
        if not isinstance(data, dict) or "access_token" not in data:
            raise ValueError(f"Strava token error: {data}")
        _strava_token_cache["access_token"] = data["access_token"]
        _strava_token_cache["expires_at"] = data["expires_at"]
        return data["access_token"]


SPORT_ICON = {
    "Run": "🏃",
    "Ride": "🚴",
    "Swim": "🏊",
    "Walk": "🚶",
    "Hike": "🥾",
    "WeightTraining": "🏋️",
    "Yoga": "🧘",
    "Workout": "💪",
}


@router.get("/strava/activities")
async def get_strava_activities(limit: int = 10):
    if not settings.strava_client_id:
        return {"activities": [], "athlete": None, "debug": "STRAVA_CLIENT_ID not set"}
    try:
        token = await get_strava_access_token()
        async with httpx.AsyncClient() as http:
            acts_resp = await http.get(
                "https://www.strava.com/api/v3/athlete/activities",
                headers={"Authorization": f"Bearer {token}"},
                params={"per_page": limit},
                timeout=15,
            )
            athlete_resp = await http.get(
                "https://www.strava.com/api/v3/athlete",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        activities = []
        for a in acts_resp.json():
            sport = a.get("sport_type") or a.get("type", "Workout")
            dist = a.get("distance", 0)
            elapsed = a.get("elapsed_time", 0)
            moving = a.get("moving_time", 0)
            activities.append({
                "id": a["id"],
                "name": a.get("name", ""),
                "sport": sport,
                "icon": SPORT_ICON.get(sport, "🏅"),
                "date": a.get("start_date_local", "")[:10],
                "distanceKm": round(dist / 1000, 2) if dist else None,
                "elapsedSec": elapsed,
                "movingSec": moving,
                "elevationM": a.get("total_elevation_gain"),
                "avgHeartRate": a.get("average_heartrate"),
                "maxHeartRate": a.get("max_heartrate"),
                "avgSpeedKph": round(a.get("average_speed", 0) * 3.6, 1) if a.get("average_speed") else None,
                "kudos": a.get("kudos_count", 0),
                "sufferScore": a.get("suffer_score"),
            })
        athlete = athlete_resp.json()
        return {
            "activities": activities,
            "athlete": {
                "name": f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
                "profile": athlete.get("profile_medium"),
            },
        }
    except Exception as e:
        logger.warning(f"Strava fetch failed: {e}")
        return {"activities": [], "athlete": None, "debug": str(e)}


# ──────────────────────────────────────────────
# 健康データ (iPhone Shortcuts 連携)
# ──────────────────────────────────────────────

_health_store: list[dict] = []  # in-memory, 最大30日分


class HealthData(BaseModel):
    date: str                          # "2026-04-01"
    steps: Optional[int] = None       # 歩数
    sleepHours: Optional[float] = None  # 睡眠時間(h)
    heartRateAvg: Optional[int] = None  # 平均心拍数
    activeCalories: Optional[int] = None  # アクティブカロリー
    exerciseMinutes: Optional[int] = None  # 運動時間(分)
    standHours: Optional[int] = None   # スタンド時間
    weight: Optional[float] = None     # 体重(kg)


@router.post("/health/data")
async def post_health_data(data: HealthData):
    """iPhone ショートカットからヘルスデータを受信する"""
    global _health_store
    _health_store = [d for d in _health_store if d["date"] != data.date]
    _health_store.append(data.model_dump())
    _health_store.sort(key=lambda x: x["date"], reverse=True)
    _health_store = _health_store[:30]
    return {"status": "ok", "date": data.date}


@router.get("/health/data")
async def get_health_data(days: int = 7):
    return {"data": _health_store[:days]}


# ──────────────────────────────────────────────
# ヘルスチェック
# ──────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ──────────────────────────────────────────────
# YouTube エージェント
# ──────────────────────────────────────────────

@router.post("/agent/youtube/run")
async def trigger_youtube_agent():
    """YouTube解析エージェントを手動トリガー"""
    run_id = await run_youtube_agent()
    return {"runId": run_id}


@router.get("/agent/youtube/videos")
async def get_videos(limit: int = 20, offset: int = 0):
    db = get_supabase()
    result = db.table("youtube_videos").select(
        "id,video_id,channel_id,channel_title,title,published_at,thumbnail_url,"
        "priority_score,summary,transcript_source,analyzed_at"
    ).order("priority_score", desc=True).range(offset, offset + limit - 1).execute()
    videos = [
        {
            "id": v["id"],
            "videoId": v["video_id"],
            "channelId": v["channel_id"],
            "channelTitle": v.get("channel_title") or "",
            "title": v["title"],
            "publishedAt": v["published_at"],
            "thumbnailUrl": v.get("thumbnail_url") or "",
            "priorityScore": v.get("priority_score") or 0.0,
            "summary": v.get("summary") or {"oneLiner": v["title"], "keyPoints": [], "watchReason": ""},
            "transcriptSource": v.get("transcript_source") or "title_only",
            "analyzedAt": v.get("analyzed_at") or v.get("published_at") or "",
        }
        for v in result.data
    ]
    return {"videos": videos, "total": len(videos)}


# ──────────────────────────────────────────────
# ニュースエージェント
# ──────────────────────────────────────────────

@router.post("/agent/news/run")
async def trigger_news_agent():
    await run_news_agent()
    return {"status": "ok"}


@router.get("/agent/news/articles")
async def get_news(limit: int = 30):
    db = get_supabase()
    result = db.table("news_articles").select(
        "id,title,url,source,published_at,summary,impact_score,urgency,created_at"
    ).order("created_at", desc=True).limit(limit).execute()
    articles = []
    for a in result.data:
        raw_summary = a.get("summary") or {}
        impact = raw_summary.get("japanMarketImpact") or {}
        articles.append({
            "id": a["id"],
            "title": a["title"],
            "url": a["url"],
            "source": a["source"],
            "publishedAt": a.get("published_at") or a.get("created_at") or "",
            "createdAt": a.get("created_at") or "",
            "summaryLines": raw_summary.get("summaryLines") or [a["title"]],
            "japanMarketImpact": {
                "score": impact.get("score") or 0.3,
                "direction": impact.get("direction") or "neutral",
                "affectedSectors": impact.get("affectedSectors") or impact.get("affected_sectors") or [],
                "reasoning": impact.get("reasoning") or "",
            },
            "urgency": a.get("urgency") or raw_summary.get("urgency") or "background",
            "impactScore": a.get("impact_score") or 0.0,
        })
    return {"articles": articles}


# ──────────────────────────────────────────────
# ポートフォリオ
# ──────────────────────────────────────────────

@router.get("/portfolio/summary")
async def get_portfolio_summary():
    return await run_portfolio_agent()


# ──────────────────────────────────────────────
# クォータ管理
# ──────────────────────────────────────────────

@router.get("/quota/status")
async def get_quota_status():
    db = get_supabase()
    result = db.table("quota_usage_today").select("*").execute()
    data = result.data[0] if result.data else {"units_used": 0, "units_remaining": 10000}
    return {
        "usedToday": data["units_used"],
        "remaining": data["units_remaining"],
        "limit": 10000,
        "usagePercent": round(data["units_used"] / 10000 * 100, 1),
    }


# ──────────────────────────────────────────────
# SSE: エージェントの実行ログをリアルタイム配信
# ──────────────────────────────────────────────

@router.get("/agent/stream/{run_id}")
async def stream_agent_steps(run_id: str):
    """
    Server-Sent Events でエージェントの実行ステップを配信。
    フロントエンドの AgentThoughtPanel で受信してリアルタイム表示する。
    """
    async def event_generator():
        db = get_supabase()
        sent_count = 0
        max_polls = 60  # 最大60秒ポーリング

        for _ in range(max_polls):
            result = db.table("agent_run_logs").select(
                "status,steps"
            ).eq("id", run_id).execute()

            if not result.data:
                await asyncio.sleep(1)
                continue

            log = result.data[0]
            steps = log.get("steps") or []

            # 新しいステップのみ送信
            for step in steps[sent_count:]:
                yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
                sent_count += 1

            if log["status"] in ("success", "error"):
                yield f"data: {json.dumps({'node': 'DONE', 'status': log['status']})}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
