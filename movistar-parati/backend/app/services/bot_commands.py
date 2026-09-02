from __future__ import annotations

import logging

from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.bot")

# Menú nativo de Telegram (botón ☰ junto al campo de texto).
BOT_COMMANDS: list[dict[str, str]] = [
    {"command": "start", "description": "Empezar / bienvenida"},
    {"command": "menu", "description": "Menú principal"},
    {"command": "ofertas", "description": "Mejores ofertas"},
    {"command": "moviles", "description": "Ver móviles por marca"},
    {"command": "novedades", "description": "Productos nuevos"},
    {"command": "parami", "description": "Recomendaciones para ti"},
    {"command": "avisos", "description": "Mis alertas de precio"},
    {"command": "ayuda", "description": "Ayuda y comandos"},
]


async def register_bot_commands() -> bool:
    if not telegram_client.configured:
        logger.warning("Telegram token missing; skipping setMyCommands")
        return False

    result = await telegram_client.set_my_commands(BOT_COMMANDS)
    if not result.get("ok"):
        logger.error("setMyCommands failed: %s", result)
        return False

    menu_btn = await telegram_client.set_chat_menu_button("commands")
    if not menu_btn.get("ok"):
        logger.warning("setChatMenuButton failed: %s", menu_btn)

    logger.info("Telegram native command menu registered (%d commands)", len(BOT_COMMANDS))
    return True
