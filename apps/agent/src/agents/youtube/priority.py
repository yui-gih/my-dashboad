"""
パーソナライズ優先度スコア算出。
ユーザーの興味ベクトルとの意味的類似度、チャンネルウェイト、時間的鮮度を加重合成する。
"""
import math
import json
import logging
from datetime import datetime, timezone

import numpy as np
from anthropic import AsyncAnthropic

from src.config import settings
from src.db import get_supabase

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


async def get_text_embedding(text: str) -> list[float]:
    """テキストの埋め込みベクトルを生成。OpenAI APIがなければゼロベクトルを返す。"""
    try:
        from openai import AsyncOpenAI
        openai_client = AsyncOpenAI()
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding generation failed (returning zero vector): {e}")
        return [0.0] * 1536


async def get_user_interest_vector(user_id: str) -> list[float] | None:
    """DBからユーザーの興味ベクトルを取得"""
    db = get_supabase()
    result = db.table("user_interest_profiles").select("interest_vector").eq(
        "user_id", user_id
    ).execute()
    if result.data:
        return result.data[0]["interest_vector"]
    return None


async def get_channel_weight(channel_id: str, user_id: str) -> float:
    """ユーザーのチャンネル優先度ウェイトを取得"""
    db = get_supabase()
    result = db.table("user_channel_weights").select("weight").eq(
        "user_id", user_id
    ).eq("channel_id", channel_id).execute()
    if result.data:
        return float(result.data[0]["weight"])
    return 0.5  # デフォルトウェイト


async def calculate_priority_score(
    content_embedding: list[float],
    channel_id: str,
    published_at: datetime,
    user_id: str = "00000000-0000-0000-0000-000000000001",
) -> float:
    """
    優先度スコアを算出する (0-1)。

    重み付け:
      50% - ユーザー興味ベクトルとのコサイン類似度
      30% - チャンネルウェイト (ユーザー設定)
      20% - 時間的鮮度 (指数減衰, 半減期6時間)
    """
    # 意味的類似度
    interest_vec = await get_user_interest_vector(user_id)
    if interest_vec:
        similarity = cosine_similarity(content_embedding, interest_vec)
    else:
        similarity = 0.5  # 興味ベクトル未設定の場合は中間値

    # チャンネルウェイト
    channel_weight = await get_channel_weight(channel_id, user_id)

    # 時間的鮮度 (公開から時間が経つほど指数関数的に減衰)
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    hours_since_publish = (now - published_at).total_seconds() / 3600
    freshness = math.exp(-0.1155 * hours_since_publish)  # 6時間で0.5

    score = 0.5 * similarity + 0.3 * channel_weight + 0.2 * freshness
    return min(max(score, 0.0), 1.0)
