from __future__ import annotations

import pytest

from app.config import Settings, clear_settings_cache
from app.db import Database
from app.deps import AppContext


@pytest.fixture
def tmp_db(tmp_path) -> Database:
    db = Database(str(tmp_path / "radar.db"))
    yield db
    db.close()


@pytest.fixture
def mock_settings(tmp_path, monkeypatch) -> Settings:
    monkeypatch.setenv("USE_MOCKS", "true")
    monkeypatch.setenv("SEARCH_PROVIDER", "mock")
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_POLLING", "false")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "radar.db"))
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("SEARCH_API_KEY", "")
    monkeypatch.setenv("MIN_NOTIFY_SCORE", "8.0")
    monkeypatch.setenv("QUERIES_PER_SCAN", "12")
    clear_settings_cache()
    settings = Settings()
    yield settings
    clear_settings_cache()


@pytest.fixture
def ctx(mock_settings) -> AppContext:
    context = AppContext(mock_settings)
    yield context
    context.close()
