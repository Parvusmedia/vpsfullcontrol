#!/usr/bin/env python3
"""Register Telegram webhook for production (HTTPS required).

Stop movistar-parati-polling before running this script to avoid duplicate updates.

Usage:
  cd backend && . .venv/bin/activate
  python scripts/setup_telegram_webhook.py
  python scripts/setup_telegram_webhook.py https://example.com/api/telegram/webhook
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.telegram_client import telegram_client


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    default_url = "https://movistarparati.pmediaplus.com/api/telegram/webhook"
    webhook_url = sys.argv[1] if len(sys.argv) > 1 else default_url

    print(f"Setting webhook → {webhook_url}")
    result = await telegram_client.set_webhook(webhook_url, settings.telegram_webhook_secret)
    print("setWebhook:", result)

    info = await telegram_client.get_webhook_info()
    print("getWebhookInfo:", info)

    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
