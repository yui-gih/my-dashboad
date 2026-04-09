"""
FastAPI アプリケーション エントリーポイント。
APScheduler によるバックグラウンドポーリングを起動時に登録する。
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import settings
from src.agents.youtube import run_youtube_agent
from src.agents.news import run_news_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="My Dashboard Agent API",
    version="0.1.0",
    description="YouTube解析・ニュース収集・ポートフォリオ管理エージェント",
)

_cors_origins = [o.strip() for o in (
    settings.allowed_origins if hasattr(settings, "allowed_origins") and settings.allowed_origins
    else "http://localhost:3000"
).split(",")]

_allow_all = _cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r".*" if _allow_all else None,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}

scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    # YouTube エージェント: 30分ごとに実行
    scheduler.add_job(
        run_youtube_agent,
        "interval",
        seconds=settings.agent_polling_interval_seconds,
        id="youtube_agent",
        replace_existing=True,
    )
    # ニュースエージェント: 15分ごとに実行
    scheduler.add_job(
        run_news_agent,
        "interval",
        seconds=900,
        id="news_agent",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Scheduler started. YouTube: every {settings.agent_polling_interval_seconds}s, "
        f"News: every 900s"
    )


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
