"""Entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from telegram.ext import Application

from flightsdemobot.config import load_settings
from flightsdemobot.handlers import build_handlers
from flightsdemobot.saudia.client import QuoteService
from flightsdemobot.storage import Store

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    db_path = settings.data_dir / "state.sqlite3"
    store = Store(db_path, settings.access_key)
    quotes = QuoteService(settings)

    app = (
        Application.builder()
        .token(settings.telegram_token)
        .build()
    )
    app.bot_data["store"] = store
    app.bot_data["quotes"] = quotes
    app.bot_data["settings"] = settings
    build_handlers(app)

    logger.info("flightsdemobot starting (data_dir=%s)", settings.data_dir)
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    # Allow running without installing the package.
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    main()
