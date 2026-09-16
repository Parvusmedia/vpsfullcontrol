#!/usr/bin/env python3
"""Configura nombre y descripción del bot en Telegram (Bot API)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.telegram_client import telegram_client

BOT_NAME = "Movistar Para Ti"
BOT_DESCRIPTION = (
    "Te ayudo a ver móviles, ofertas y novedades, encontrar el que mejor encaja contigo, "
    "comparar compra libre y cuotas para clientes Movistar, y crear avisos si baja el precio. "
    "Demo conceptual — datos de ejemplo. Pulsa /start."
)
BOT_SHORT_DESCRIPTION = "Móviles, recomendaciones personalizadas y avisos de precio."


async def main() -> None:
    if not telegram_client.configured:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    for label, method, value in (
        ("setMyName", telegram_client.set_my_name, BOT_NAME),
        ("setMyDescription", telegram_client.set_my_description, BOT_DESCRIPTION),
        ("setMyShortDescription", telegram_client.set_my_short_description, BOT_SHORT_DESCRIPTION),
    ):
        result = await method(value)
        print(f"{label}: {result}")
        if not result.get("ok"):
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
