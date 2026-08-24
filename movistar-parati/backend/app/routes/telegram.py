from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services.bot_handlers import handle_update
from app.services.telegram_client import telegram_client

router = APIRouter(tags=["telegram"])


@router.post("/api/telegram/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    settings = get_settings()
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(403, "Invalid webhook secret")
    update = await request.json()
    miniapp_url = f"{settings.public_base_url.rstrip('/')}/app/"
    await handle_update(db, update, miniapp_url)
    return {"ok": True}


@router.post("/api/telegram/setup-webhook")
async def setup_webhook(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    settings = get_settings()
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(401, "Invalid admin key")
    url = f"{settings.public_base_url.rstrip('/')}/api/telegram/webhook"
    result = await telegram_client.set_webhook(url, settings.telegram_webhook_secret)
    return {"webhook_url": url, "result": result}
