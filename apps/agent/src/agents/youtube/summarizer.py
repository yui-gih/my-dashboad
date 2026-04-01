"""
動画字幕の要約生成。
長文字幕は Map-Reduce パターンで処理し、LLM のコンテキスト制限を回避する。
"""
import asyncio
import json
import logging

from anthropic import AsyncAnthropic

from src.config import settings

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)
MODEL = "claude-sonnet-4-6"
ANALYSIS_VERSION = "v1"

CHUNK_SIZE = 4000   # 文字数
CHUNK_OVERLAP = 200


def _split_text(text: str) -> list[str]:
    """
    テキストをチャンクに分割。文の途中で切れないよう句点・改行を優先する。
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        if end >= len(text):
            chunks.append(text[start:])
            break
        # 句点・改行での分割を優先
        for sep in ["。\n", "。", ".\n", ".", "\n", " "]:
            idx = text.rfind(sep, start, end)
            if idx > start:
                end = idx + len(sep)
                break
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks


async def _chunk_summarize(chunk: str, chunk_idx: int, total_chunks: int) -> str:
    """Map フェーズ: 各チャンクの中間要約を生成"""
    prompt = (
        f"動画字幕のパート {chunk_idx + 1}/{total_chunks} を要約してください。\n"
        f"重要なポイントを200文字以内で箇条書きにしてください。\n\n{chunk}"
    )
    response = await client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


async def _direct_summarize(text: str, metadata: dict) -> dict:
    """短い字幕を直接要約（Map-Reduce 不要なケース）"""
    return await _reduce_summaries([text], metadata)


async def _reduce_summaries(summaries: list[str], metadata: dict) -> dict:
    """Reduce フェーズ: 中間要約を統合して最終要約を生成"""
    combined = "\n\n---\n\n".join(summaries)
    prompt = f"""
あなたはYouTube動画のコンテンツアナリストです。
以下の動画情報と要約から、視聴者にとっての価値を分析してください。

## 動画情報
タイトル: {metadata.get('title', '')}
チャンネル: {metadata.get('channel_title', '')}

## 内容要約
{combined}

## 出力形式 (JSON のみ、他のテキスト不要)
{{
  "one_liner": "この動画を一文で表すと（30文字以内）",
  "key_points": [
    "重要ポイント1",
    "重要ポイント2",
    "重要ポイント3"
  ],
  "watch_reason": "あなたがこの動画を見るべき理由（具体的に、50文字以内）"
}}
"""
    response = await client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    # JSON 抽出
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    parsed = json.loads(raw)
    return {
        "oneLiner": parsed["one_liner"],
        "keyPoints": parsed["key_points"][:3],
        "watchReason": parsed["watch_reason"],
    }, response.usage.input_tokens + response.usage.output_tokens


async def summarize(text: str, metadata: dict) -> tuple[dict, int]:
    """
    メイン要約エントリーポイント。
    Returns: (summary_dict, tokens_used)
    """
    chunks = _split_text(text)
    if len(chunks) == 1:
        return await _direct_summarize(chunks[0], metadata)

    logger.info(f"Map-Reduce: {len(chunks)} chunks for video {metadata.get('video_id')}")
    # Map: 並列処理
    intermediate = await asyncio.gather(*[
        _chunk_summarize(chunk, i, len(chunks))
        for i, chunk in enumerate(chunks)
    ])
    # Reduce: 統合
    return await _reduce_summaries(list(intermediate), metadata)
