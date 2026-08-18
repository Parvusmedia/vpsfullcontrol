"""Configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    access_key: str
    data_dir: Path
    quote_timeout: float
    quote_max_concurrent: int
    mock_quotes: bool
    amadeus_client_id: str
    amadeus_client_secret: str
    amadeus_host: str
    network_feed_url: str


def load_settings() -> Settings:
    token = _env("TELEGRAM_BOT_TOKEN")
    access_key = _env("ACCESS_KEY")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    if not access_key:
        raise RuntimeError("ACCESS_KEY is required")

    data_dir = Path(_env("DATA_DIR", "/var/lib/flightsdemobot"))
    return Settings(
        telegram_token=token,
        access_key=access_key,
        data_dir=data_dir,
        quote_timeout=float(_env_int("QUOTE_TIMEOUT_SECONDS", 12)),
        quote_max_concurrent=_env_int("QUOTE_MAX_CONCURRENT", 4),
        mock_quotes=_env("MOCK_QUOTES", "0") in ("1", "true", "yes"),
        amadeus_client_id=_env("AMADEUS_CLIENT_ID"),
        amadeus_client_secret=_env("AMADEUS_CLIENT_SECRET"),
        amadeus_host=_env("AMADEUS_HOST", "https://test.api.amadeus.com").rstrip("/"),
        network_feed_url=_env(
            "NETWORK_FEED_URL",
            "https://flights.pmediaplus.com/fares/network.json",
        ),
    )
