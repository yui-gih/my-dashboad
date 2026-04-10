from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # YouTube
    youtube_api_key: str = ""
    youtube_quota_daily_limit: int = 10000

    # AI
    anthropic_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Weather
    openweather_api_key: str = ""

    # Agent
    agent_polling_interval_seconds: int = 1800

    # CORS (カンマ区切りで複数指定可)
    allowed_origins: str = "http://localhost:3000"


settings = Settings()
