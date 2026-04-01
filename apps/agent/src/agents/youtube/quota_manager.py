"""
YouTube Data API v3 クォータ管理。
1日10,000ユニットの制限を永続化追跡し、安全閾値で自動停止する。
"""
import logging
from datetime import date

from src.db import get_supabase

logger = logging.getLogger(__name__)

DAILY_LIMIT = 10_000
SAFETY_THRESHOLD = 0.80  # 80%超過で警告、新規操作を停止


class QuotaManager:
    async def get_today_usage(self) -> int:
        db = get_supabase()
        result = db.table("quota_logs").select("units").eq("date", str(date.today())).execute()
        return sum(row["units"] for row in result.data)

    async def get_remaining(self) -> int:
        return DAILY_LIMIT - await self.get_today_usage()

    async def can_consume(self, units: int) -> bool:
        usage = await self.get_today_usage()
        return (usage + units) <= DAILY_LIMIT * SAFETY_THRESHOLD

    async def consume(self, units: int, operation: str) -> bool:
        """
        クォータを消費してDBに記録。
        Returns False if quota would be exceeded.
        """
        if not await self.can_consume(units):
            usage = await self.get_today_usage()
            logger.warning(
                f"Quota safety threshold reached. Used: {usage}/{DAILY_LIMIT}. "
                f"Blocked operation: {operation} ({units} units)"
            )
            return False

        db = get_supabase()
        db.table("quota_logs").insert({
            "date": str(date.today()),
            "units": units,
            "operation": operation,
        }).execute()
        logger.info(f"Quota consumed: {units} units for {operation}")
        return True


quota_manager = QuotaManager()
