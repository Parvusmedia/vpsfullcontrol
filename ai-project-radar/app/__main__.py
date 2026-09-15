from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

from app.config import Settings, clear_settings_cache
from app.deps import AppContext
from app.telegram.formatter import format_alert


def _settings_from_env() -> Settings:
    clear_settings_cache()
    return Settings()


async def cmd_scan(use_mocks: bool | None = None) -> None:
    settings = _settings_from_env()
    if use_mocks is True:
        settings.use_mocks = True
    ctx = AppContext(settings)
    try:
        summary = await ctx.pipeline.run()
        print(json.dumps(summary.model_dump(mode="json"), indent=2))
        if isinstance(ctx.telegram_client, object) and hasattr(ctx.telegram_client, "messages"):
            messages = getattr(ctx.telegram_client, "messages")
            print(f"\n--- Telegram alerts: {len(messages)} ---")
            for msg in messages:
                print(msg["text"])
                print("---")
    finally:
        ctx.close()


async def cmd_stats() -> None:
    settings = _settings_from_env()
    ctx = AppContext(settings)
    try:
        print(json.dumps(ctx.db.stats(), indent=2))
    finally:
        ctx.close()


async def cmd_latest() -> None:
    settings = _settings_from_env()
    ctx = AppContext(settings)
    try:
        items = ctx.db.latest_qualified(settings.min_notify_score, limit=5)
        if not items:
            print("No qualified opportunities.")
            return
        for opp in items:
            if opp.scoring:
                print(format_alert(opp))
                print("---")
    finally:
        ctx.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="AI Project Radar CLI")
    parser.add_argument("command", choices=["scan", "stats", "latest", "serve"])
    parser.add_argument("--mocks", action="store_true", help="Force USE_MOCKS=true")
    args = parser.parse_args()

    if args.mocks:
        os.environ["USE_MOCKS"] = "true"
        clear_settings_cache()

    if args.command == "serve":
        import uvicorn

        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
        return

    if args.command == "scan":
        asyncio.run(cmd_scan(use_mocks=True if args.mocks else None))
    elif args.command == "stats":
        asyncio.run(cmd_stats())
    elif args.command == "latest":
        asyncio.run(cmd_latest())


if __name__ == "__main__":
    # Allow running from repo root or project dir.
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    main()
