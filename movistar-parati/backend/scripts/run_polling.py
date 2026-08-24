#!/usr/bin/env python3
"""Polling mode for local/demo when HTTPS webhook is not ready."""

import asyncio
import logging

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.services.bot_handlers import handle_update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("movistar-parati.polling")


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN missing")
    base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    offset = 0
    miniapp_url = f"{settings.public_base_url.rstrip('/')}/app/"
    async with httpx.AsyncClient(timeout=60) as client:
        await client.post(f"{base}/deleteWebhook")
        logger.info("Polling started")
        while True:
            resp = await client.get(f"{base}/getUpdates", params={"timeout": 30, "offset": offset})
            data = resp.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                db: Session = SessionLocal()
                try:
                    await handle_update(db, update, miniapp_url)
                finally:
                    db.close()
            await asyncio.sleep(0.2)


if __name__ == "__main__":
    asyncio.run(main())
