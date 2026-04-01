"""
ニュース収集・要約エージェント。
RSS + News API → セマンティック重複排除 → LLM要約 → DB保存
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import TypedDict, Annotated
import operator

import feedparser
import httpx
from anthropic import AsyncAnthropic
from langgraph.graph import StateGraph, END

from src.config import settings
from src.db import get_supabase
from ..youtube.priority import get_text_embedding

logger = logging.getLogger(__name__)
client = AsyncAnthropic(api_key=settings.anthropic_api_key)

RSS_SOURCES = [
    ("Reuters (JP)", "https://feeds.reuters.com/reuters/JPBusinessNews"),
    ("NHK経済", "https://www3.nhk.or.jp/rss/news/cat6.xml"),
    ("Bloomberg JP", "https://feeds.bloomberg.co.jp/bloomberg/businessnews"),
]


# ──────────────────────────────────────────────
# State
# ──────────────────────────────────────────────

class NewsState(TypedDict):
    raw_articles: list[dict]
    deduplicated: list[dict]
    analyzed: list[dict]
    errors: Annotated[list, operator.add]


# ──────────────────────────────────────────────
# ノード
# ──────────────────────────────────────────────

def fetch_rss(state: NewsState) -> dict:
    """RSS フィードから記事を収集"""
    articles = []
    for source_name, url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                articles.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "source": source_name,
                    "published_at": entry.get("published", None),
                    "content": entry.get("summary", entry.get("title", "")),
                })
        except Exception as e:
            logger.error(f"RSS fetch failed for {source_name}: {e}")

    # News API (設定されている場合)
    if settings.news_api_key:
        try:
            response = httpx.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "jp", "category": "business", "apiKey": settings.news_api_key},
                timeout=10,
            )
            for article in response.json().get("articles", [])[:10]:
                articles.append({
                    "title": article["title"] or "",
                    "url": article["url"] or "",
                    "source": article["source"]["name"],
                    "published_at": article.get("publishedAt"),
                    "content": article.get("description") or article.get("title", ""),
                })
        except Exception as e:
            logger.error(f"News API fetch failed: {e}")

    logger.info(f"Fetched {len(articles)} raw articles")
    return {"raw_articles": articles}


async def deduplicate_articles(state: NewsState) -> dict:
    """
    セマンティック重複排除。
    タイトルのベクトルを生成し、pgvector で既存記事との類似度を計算。
    コサイン類似度 > 0.92 を重複とみなす。
    """
    db = get_supabase()
    unique = []

    # URL ベースの即時重複チェック
    existing_urls = {
        row["url"]
        for row in db.table("news_articles").select("url").execute().data
    }

    for article in state["raw_articles"]:
        if article["url"] in existing_urls:
            continue
        try:
            embedding = await get_text_embedding(article["title"])
            result = db.rpc("match_news_articles", {
                "query_embedding": embedding,
                "match_threshold": 0.92,
                "match_count": 1,
            }).execute()
            if not result.data:
                unique.append({**article, "embedding": embedding})
        except Exception as e:
            logger.error(f"Dedup failed for '{article['title']}': {e}")
            unique.append(article)  # エラー時は追加（安全側）

    logger.info(f"After dedup: {len(unique)}/{len(state['raw_articles'])} articles")
    return {"deduplicated": unique}


async def analyze_news(state: NewsState) -> dict:
    """LLM による日本市場への影響度付き要約を並列生成"""
    def fallback_analysis(article: dict) -> dict:
        return {**article, "analysis": {
            "summary_lines": [article["title"][:30]],
            "japan_market_impact": {"score": 0.3, "direction": "neutral", "affected_sectors": [], "reasoning": "AI分析未実施"},
            "urgency": "background",
        }}

    async def analyze_one(article: dict) -> dict:
        try:
            prompt = f"""
あなたは日本株・マクロ経済の専門アナリストです。以下のニュース記事を分析してください。

## 記事
タイトル: {article['title']}
本文: {article['content'][:2000]}

## 出力形式 (JSON のみ)
{{
  "summary_lines": ["1行目（30字以内）", "2行目", "3行目"],
  "japan_market_impact": {{
    "score": 0.0から1.0の数値,
    "direction": "positive か negative か neutral",
    "affected_sectors": ["影響を受けるセクター名"],
    "reasoning": "影響の根拠（1文）"
  }},
  "urgency": "breaking か today か background"
}}

重要: score > 0.7 の場合のみ affected_sectors を具体的に列挙すること。
"""
            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(raw)
            return {**article, "analysis": parsed}
        except Exception as e:
            logger.warning(f"Analysis failed for '{article['title']}', using fallback: {e}")
            return fallback_analysis(article)

    results = await asyncio.gather(*[analyze_one(a) for a in state["deduplicated"]])
    analyzed = [r for r in results if r is not None]
    return {"analyzed": analyzed}


def save_news(state: NewsState) -> dict:
    """解析済み記事を Supabase に保存"""
    db = get_supabase()
    saved = 0
    for article in state["analyzed"]:
        analysis = article.get("analysis", {})
        impact = analysis.get("japan_market_impact", {})
        try:
            db.table("news_articles").insert({
                "title": article["title"],
                "url": article["url"],
                "source": article["source"],
                "published_at": article.get("published_at"),
                "embedding": article.get("embedding"),
                "summary": {
                    "summaryLines": analysis.get("summary_lines", []),
                    "japanMarketImpact": impact,
                    "urgency": analysis.get("urgency", "background"),
                },
                "impact_score": impact.get("score", 0.0),
                "urgency": analysis.get("urgency", "background"),
            }).execute()
            saved += 1
        except Exception as e:
            logger.error(f"Save failed for '{article['title']}': {e}")

    logger.info(f"Saved {saved} news articles")
    return {}


# ──────────────────────────────────────────────
# グラフ構築
# ──────────────────────────────────────────────

def build_news_agent():
    workflow = StateGraph(NewsState)
    workflow.add_node("fetch_rss", fetch_rss)
    workflow.add_node("deduplicate", deduplicate_articles)
    workflow.add_node("analyze", analyze_news)
    workflow.add_node("save", save_news)

    workflow.set_entry_point("fetch_rss")
    workflow.add_edge("fetch_rss", "deduplicate")
    workflow.add_edge("deduplicate", "analyze")
    workflow.add_edge("analyze", "save")
    workflow.add_edge("save", END)

    return workflow.compile()


news_agent = build_news_agent()


async def run_news_agent() -> None:
    initial: NewsState = {
        "raw_articles": [],
        "deduplicated": [],
        "analyzed": [],
        "errors": [],
    }
    await news_agent.ainvoke(initial)
