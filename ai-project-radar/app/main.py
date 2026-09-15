from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.deps import AppContext
from app.scheduler import build_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

ctx: AppContext | None = None


async def _poll_telegram(context: AppContext) -> None:
    offset: int | None = None
    client = context.telegram_client
    while True:
        try:
            updates = await client.get_updates(offset=offset, timeout=25)
            for update in updates:
                offset = int(update["update_id"]) + 1
                await context.bot.handle_update(update)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Telegram polling error")
            await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global ctx
    settings = get_settings()
    ctx = AppContext(settings)
    app.state.ctx = ctx
    scheduler = None
    poll_task = None
    if settings.enable_scheduler:
        scheduler = build_scheduler(ctx.pipeline, settings)
        scheduler.start()
    if settings.enable_telegram_polling and settings.telegram_bot_token and not settings.use_mocks:
        poll_task = asyncio.create_task(_poll_telegram(ctx))
        logger.info("Telegram long polling started")
    logger.info(
        "AI Project Radar up provider=%s mocks=%s db=%s",
        ctx.search.name,
        settings.use_mocks,
        settings.database_path,
    )
    try:
        yield
    finally:
        if poll_task:
            poll_task.cancel()
            try:
                await poll_task
            except asyncio.CancelledError:
                pass
        if scheduler:
            scheduler.shutdown(wait=False)
        if ctx:
            ctx.close()
        ctx = None


app = FastAPI(title="AI Project Radar", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "provider": settings.search_provider if not settings.use_mocks else "mock",
        "mocks": str(settings.use_mocks).lower(),
    }


@app.post("/scan")
async def scan() -> JSONResponse:
    context: AppContext = app.state.ctx
    summary = await context.pipeline.run()
    return JSONResponse(summary.model_dump(mode="json"))


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    context: AppContext = app.state.ctx
    if not context.settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram not configured")
    update = await request.json()
    await context.bot.handle_update(update)
    return {"ok": True}


@app.get("/stats")
async def stats() -> dict[str, int]:
    context: AppContext = app.state.ctx
    return context.db.stats()
