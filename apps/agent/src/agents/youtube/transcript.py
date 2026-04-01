"""
字幕取得の多段フォールバック戦略。
manual_ja → auto_ja → manual_en → auto_en → description → title_only
の優先度で取得し、データ品質をメタデータとして保持する。
"""
import logging
from enum import Enum

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

logger = logging.getLogger(__name__)


class TranscriptSource(str, Enum):
    MANUAL_JA = "manual_ja"
    AUTO_JA = "auto_ja"
    MANUAL_EN = "manual_en"
    AUTO_EN = "auto_en"
    DESCRIPTION = "description"
    TITLE_ONLY = "title_only"


FETCH_PRIORITY = [
    (TranscriptSource.MANUAL_JA, {"languages": ["ja"]}),
    (TranscriptSource.AUTO_JA,   {"languages": ["ja"]}),
    (TranscriptSource.MANUAL_EN, {"languages": ["en"]}),
    (TranscriptSource.AUTO_EN,   {"languages": ["en"]}),
]


def fetch_transcript(video_id: str) -> tuple[str | None, TranscriptSource]:
    """
    字幕テキストと取得元を返す。
    字幕が一切取得できない場合は (None, DESCRIPTION) を返す。
    """
    for source, kwargs in FETCH_PRIORITY:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            if "auto_generated" in source.value:
                transcript = transcript_list.find_generated_transcript(
                    kwargs["languages"]
                )
            else:
                transcript = transcript_list.find_manually_created_transcript(
                    kwargs["languages"]
                )
            entries = transcript.fetch()
            text = " ".join(entry["text"] for entry in entries)
            logger.info(f"[{video_id}] Transcript fetched via {source.value} ({len(text)} chars)")
            return text, source
        except (NoTranscriptFound, TranscriptsDisabled, Exception) as e:
            logger.debug(f"[{video_id}] {source.value} failed: {e}")
            continue

    logger.info(f"[{video_id}] No transcript available, will use description")
    return None, TranscriptSource.DESCRIPTION
