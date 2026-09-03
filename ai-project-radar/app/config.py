from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    search_api_key: str = ""

    search_provider: str = "serper"
    use_mocks: bool = False
    openai_model: str = "gpt-4o-mini"
    database_path: str = "data/radar.db"
    scan_interval_hours: int = 1
    min_notify_score: float = 8.0
    max_age_hours: int = 24
    max_age_exceptional_hours: int = 72
    queries_per_scan: int = 12
    enable_scheduler: bool = True
    enable_telegram_polling: bool = True

    serper_url: str = "https://google.serper.dev/search"
    tavily_url: str = "https://api.tavily.com/search"
    bing_url: str = "https://api.bing.microsoft.com/v7.0/search"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
