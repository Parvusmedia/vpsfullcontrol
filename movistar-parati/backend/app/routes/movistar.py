from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import Response

from app.config import get_settings
from app.services.change_detection import get_active_alerts, get_recent_events, log_event, poll_catalogue_changes
from app.services.demo_actions import demo_actions_for_product
from app.services.product_image import get_normalized_product_image
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


@router.get("/api/movistar/products/{product_id}/image")
async def get_product_image(product_id: str):
    product = await product_source.get_product(product_id)
    if not product:
        raise HTTPException(404, "Not found")
    image_bytes = await get_normalized_product_image(product)
    return Response(
        content=image_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


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


@router.get("/api/movistar/admin/dashboard")
async def admin_dashboard(_: None = Depends(_admin)):
    products = await product_source.get_products(active_only=False)
    active = [p for p in products if p.active]
    alerts = await get_active_alerts()
    events = await get_recent_events(limit=10)
    return {
        "products_total": len(products),
        "products_active": len(active),
        "featured": len([p for p in active if p.featured]),
        "new_products": len([p for p in active if p.is_new]),
        "alerts_active": len(alerts),
        "recent_events": events,
        "nocodb_products_url": (
            f"{get_settings().nocodb_base_url}/dashboard/#/nc/"
            f"{get_settings().nocodb_base_id}/{get_settings().nocodb_products_table_id}"
        ),
        "nocodb_alerts_url": (
            f"{get_settings().nocodb_base_url}/dashboard/#/nc/"
            f"{get_settings().nocodb_base_id}/{get_settings().nocodb_alerts_table_id}"
        ),
    }


@router.get("/api/movistar/admin/catalog")
async def admin_catalog(_: None = Depends(_admin)):
    products = await product_source.get_products(active_only=False)
    items = []
    for p in products:
        data = p.to_dict()
        data["record_id"] = p.record_id
        data["active"] = p.active
        data["display_name"] = p.display_name
        data["image_api_url"] = f"/api/movistar/products/{p.id}/image"
        data["demo_actions"] = demo_actions_for_product(p.id, p.monthly_price)
        items.append(data)
    items.sort(key=lambda x: (not x.get("active"), x.get("brand", ""), x.get("name", "")))
    return items


@router.get("/api/movistar/admin/alerts")
async def admin_alerts(_: None = Depends(_admin)):
    return await get_active_alerts()


@router.get("/api/movistar/admin/events")
async def admin_events(limit: int = Query(25, ge=1, le=100), _: None = Depends(_admin)):
    return await get_recent_events(limit=limit)


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
