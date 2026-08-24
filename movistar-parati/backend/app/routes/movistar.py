from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.config import get_settings
from app.services.change_detection import log_event, poll_catalogue_changes
from app.services.product_service import product_source
from app.services.bot_handlers import handle_update

router = APIRouter(tags=["movistar"])


@router.get("/api/movistar/products")
async def list_products(
    brand: str | None = None,
    max_monthly_price: float | None = None,
    max_price: float | None = None,
    min_discount: float | None = None,
    featured: bool | None = None,
):
    products = await product_source.get_products()
    if brand:
        products = [p for p in products if p.brand.lower() == brand.lower()]
    if max_monthly_price is not None:
        products = [p for p in products if p.monthly_price is not None and p.monthly_price <= max_monthly_price]
    if max_price is not None:
        products = [p for p in products if p.price is not None and p.price <= max_price]
    if min_discount is not None:
        products = [p for p in products if (p.discount_percentage or 0) >= min_discount]
    if featured:
        products = [p for p in products if p.featured]
    return [p.to_dict() for p in products]


@router.get("/api/movistar/products/{product_id}")
async def get_product(product_id: str):
    p = await product_source.get_product(product_id)
    if not p:
        raise HTTPException(404, "Not found")
    return p.to_dict()


@router.get("/api/movistar/deals")
async def deals():
    return [p.to_dict() for p in await product_source.get_deals()]


@router.get("/api/movistar/new")
async def new_products():
    return [p.to_dict() for p in await product_source.get_new_products()]


@router.get("/api/movistar/brands")
async def brands():
    return await product_source.get_brands()


def _admin(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    if x_admin_key != get_settings().admin_api_key:
        raise HTTPException(401, "Invalid admin key")


@router.post("/api/movistar/admin/poll")
async def admin_poll(_: None = Depends(_admin)):
    return await poll_catalogue_changes()


@router.post("/api/movistar/admin/simulate-drop/{product_id}")
async def simulate_drop(product_id: str, new_monthly: float = Query(...), _: None = Depends(_admin)):
    p = await product_source.get_product(product_id)
    if not p:
        raise HTTPException(404)
    updated = await product_source.update_monthly_price(p, new_monthly)
    result = await poll_catalogue_changes()
    await log_event("MANUAL_TELEGRAM_SEND", product_id=product_id, new_value=str(new_monthly))
    return {"product": updated.to_dict() if updated else None, "poll": result}


@router.post("/api/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != get_settings().telegram_webhook_secret:
        raise HTTPException(403, "Invalid webhook secret")
    await handle_update(await request.json())
    return {"ok": True}
