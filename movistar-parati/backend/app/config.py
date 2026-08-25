from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    public_base_url: str = "http://127.0.0.1:8020"
    demo_mode: bool = True

    nocodb_base_url: str = "https://mpa.parvusmedia.com"
    nocodb_api_token: str = ""
    nocodb_base_id: str = ""
    nocodb_products_table_id: str = ""
    nocodb_products_view_slug: str = "vwzlxuhc0956ijho/movistar_products-movistar_products"
    nocodb_alerts_table_id: str = ""
    nocodb_events_table_id: str = ""

    telegram_bot_token: str = ""
    telegram_bot_username: str = "Movistarparatibot"
    telegram_webhook_secret: str = "movistar-parati-webhook"

    admin_api_key: str = "demo-admin-change-me"
    poll_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
