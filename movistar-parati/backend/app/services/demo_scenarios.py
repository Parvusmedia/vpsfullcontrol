"""Escenarios de demo de un clic (panel operador)."""

from __future__ import annotations

from typing import Any

from app.services.change_detection import log_event, poll_catalogue_changes
from app.services.price_formatting import round_monthly
from app.services.product_service import Product, product_source

BLACK_FRIDAY_PRODUCTS = ("galaxy-s25", "pixel-11-256", "redmi-note-14")
BLACK_FRIDAY_PROMO = "Black Friday — oferta flash limitada"
PREORDER_PRODUCT_ID = "iphone-16-pro"
PREORDER_PROMO = "Preventa iPhone — reserva ya con entrega prioritaria"


async def _apply_product_updates(product: Product, fields: dict[str, Any]) -> Product | None:
    return await product_source.update_product(product, fields)


async def activate_black_friday() -> dict[str, Any]:
    updated_ids: list[str] = []
    for product_id in BLACK_FRIDAY_PRODUCTS:
        product = await product_source.get_product(product_id)
        if not product or not product.active:
            continue
        fields: dict[str, Any] = {
            "featured": True,
            "promotion": BLACK_FRIDAY_PROMO,
        }
        if product.monthly_price and product.monthly_price > 3:
            target = round_monthly(max(product.monthly_price * 0.85, 1.0))
            if target is not None and target < product.monthly_price:
                fields["previous_monthly_price"] = product.monthly_price
                fields["monthly_price"] = target
        updated = await _apply_product_updates(product, fields)
        if updated:
            updated_ids.append(updated.id)

    poll = await poll_catalogue_changes()
    await log_event("DEMO_BLACK_FRIDAY", metadata={"products": updated_ids})
    return {"scenario": "black_friday", "products": updated_ids, "poll": poll}


async def open_iphone_preorder() -> dict[str, Any]:
    product = await product_source.get_product(PREORDER_PRODUCT_ID)
    if not product:
        return {"scenario": "iphone_preorder", "products": [], "poll": {"changes": 0, "notifications": 0}}

    fields: dict[str, Any] = {
        "active": True,
        "featured": True,
        "is_new": True,
        "promotion": PREORDER_PROMO,
    }
    updated = await _apply_product_updates(product, fields)
    product_ids = [updated.id] if updated else []
    poll = await poll_catalogue_changes()
    await log_event("DEMO_IPHONE_PREORDER", product_id=PREORDER_PRODUCT_ID, metadata={"products": product_ids})
    return {"scenario": "iphone_preorder", "products": product_ids, "poll": poll}
