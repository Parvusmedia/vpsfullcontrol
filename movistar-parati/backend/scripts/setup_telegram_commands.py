#!/usr/bin/env python3
"""Registra el menú nativo de comandos de Telegram (setMyCommands)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.bot_commands import BOT_COMMANDS, register_bot_commands


async def main() -> None:
    ok = await register_bot_commands()
    if not ok:
        raise SystemExit(1)
    print(f"OK — {len(BOT_COMMANDS)} comandos registrados:")
    for cmd in BOT_COMMANDS:
        print(f"  /{cmd['command']} — {cmd['description']}")


if __name__ == "__main__":
    asyncio.run(main())
