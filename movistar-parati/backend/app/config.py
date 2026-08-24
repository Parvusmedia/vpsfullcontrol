from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://movistar_parati:movistar_parati@127.0.0.1:5432/movistar_parati"
    public_base_url: str = "http://127.0.0.1:8020"
    demo_mode: bool = True

    telegram_bot_token: str = ""
    telegram_bot_username: str = "Movistarparatibot"
    telegram_webhook_secret: str = "movistar-parati-webhook"

    admin_api_key: str = "demo-admin-change-me"
    mock_otp_code: str = "123456"
    mock_otp_numbers: str = "600000001,600000002"

    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
