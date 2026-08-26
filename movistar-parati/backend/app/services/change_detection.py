from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.services.nocodb import nocodb
from app.services.product_service import Product, commercial_signature, product_source
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.changes")

_signatures: dict[str, str] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_event(
    event_type: str,
    *,
    product_id: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    metadata: dict | None = None,
) -> None:
    table_id = get_settings().nocodb_events_table_id
    if not table_id:
        return
    await nocodb.create_record(
        table_id,
        {
            "product_id": product_id,
            "event_type": event_type,
            "old_value": old_value,
            "new_value": new_value,
            "metadata": str(metadata or {}),
            "created_at": _now_iso(),
        },
    )


async def get_active_alerts() -> list[dict]:
    table_id = get_settings().nocodb_alerts_table_id
    if not table_id:
        return []
    rows = await nocodb.list_records(table_id, limit=500)
    alerts = []
    for row in rows:
        f = row
        if not f.get("telegram_user_id") and "fields" in row:
            f = row["fields"]
        if str(f.get("active", True)).lower() in {"0", "false", "no"}:
            continue
        f["_record_id"] = row.get("Id") or row.get("id")
        alerts.append(f)
    return alerts


async def user_has_product_alert(user_id: int | str, product_id: str) -> bool:
    alerts = await get_user_alerts(user_id)
    product_id = str(product_id)
    return any(str(a.get("product_id")) == product_id for a in alerts)


async def create_alert(fields: dict) -> dict | None:
    user_id = fields.get("telegram_user_id")
    product_id = fields.get("product_id")
    if user_id and product_id and await user_has_product_alert(user_id, str(product_id)):
        return None
    table_id = get_settings().nocodb_alerts_table_id
    fields = {**fields, "active": True, "created_at": _now_iso()}
    return await nocodb.create_record(table_id, fields)


async def update_alert(record_id: str | int, fields: dict) -> dict:
    table_id = get_settings().nocodb_alerts_table_id
    return await nocodb.update_record(table_id, record_id, fields)


ALERT_TYPE_LABELS = {
    "price_drop": "Si baja de precio",
    "monthly_price_drop": "Si baja la cuota",
    "better_deal": "Mejor oferta",
}


def alert_type_label(alert_type: str | None) -> str:
    return ALERT_TYPE_LABELS.get(alert_type or "", alert_type or "Alerta")


async def get_user_alerts(user_id: int | str) -> list[dict]:
    alerts = await get_active_alerts()
    return [a for a in alerts if str(a.get("telegram_user_id")) == str(user_id)]


async def deactivate_alert(record_id: str | int, user_id: int | str) -> bool:
    alerts = await get_user_alerts(user_id)
    owned = next((a for a in alerts if str(a.get("_record_id")) == str(record_id)), None)
    if not owned:
        return False
    await update_alert(record_id, {"active": False})
    await log_event(
        "ALERT_DEACTIVATED",
        product_id=str(owned.get("product_id") or ""),
        metadata={"telegram_user_id": str(user_id), "alert_type": owned.get("alert_type")},
    )
    return True


def _format_price_drop_message(product: Product, old_monthly: float, new_monthly: float) -> str:
    gift = f"\n\n🎁 {product.gift}" if product.gift else ""
    promo = f"\n🔥 {product.promotion}" if product.promotion else ""
    saving = old_monthly - new_monthly
    saving_line = f"\n\n💰 Ahorras <b>{saving:.2f} €/mes</b> — ¡aprovecha antes de que suba!" if saving > 0 else ""
    return (
        f"🔔 <b>¡Tu aviso se ha activado!</b>\n\n"
        f"El <b>{product.display_name}</b> que sigues acaba de bajar de cuota.\n\n"
        f"Antes: <s>{old_monthly:.2f} €/mes</s>\n"
        f"Ahora: <b>{new_monthly:.2f} €/mes</b>"
        f"{saving_line}{promo}{gift}\n\n"
        f"👉 Pulsa abajo para ver la oferta."
    )


async def evaluate_alerts_for_product(
    product: Product,
    old_sig: str,
    new_sig: str,
    old_monthly: float | None,
    new_monthly: float | None,
) -> int:
    sent = 0
    alerts = await get_active_alerts()
    for alert in alerts:
        if str(alert.get("product_id")) not in {product.id, product.slug}:
            continue
        telegram_user_id = alert.get("telegram_user_id")
        if not telegram_user_id:
            continue
        alert_type = alert.get("alert_type") or "monthly_price_drop"
        signature = alert.get("last_notified_signature")
        if signature == new_sig:
            continue

        should_notify = False
        if alert_type == "monthly_price_drop" and old_monthly and new_monthly and new_monthly < old_monthly:
            target = alert.get("target_monthly_price")
            if target is None or new_monthly <= float(target):
                should_notify = True
        elif alert_type == "price_drop" and product.price and product.previous_price:
            if product.price < product.previous_price:
                should_notify = True
        elif alert_type == "better_deal" and old_sig != new_sig:
            should_notify = True

        if not should_notify:
            continue

        text = _format_price_drop_message(product, old_monthly or 0, new_monthly or 0)
        kb = {"inline_keyboard": [[{"text": "👉 Ver oferta", "url": product.product_url or "https://www.movistar.es/"}]]}
        result = await telegram_client.send_message(int(telegram_user_id), text, reply_markup=kb)
        if result.get("ok"):
            sent += 1
            rid = alert.get("_record_id")
            if rid:
                await update_alert(
                    rid,
                    {
                        "last_notified_signature": new_sig,
                        "last_triggered_at": _now_iso(),
                    },
                )
            await log_event(
                "ALERT_TRIGGERED",
                product_id=product.id,
                old_value=str(old_monthly),
                new_value=str(new_monthly),
                metadata={"telegram_user_id": telegram_user_id},
            )
    return sent


async def poll_catalogue_changes() -> dict[str, Any]:
    products = await product_source.get_products(active_only=False)
    changes = 0
    notifications = 0

    for product in products:
        sig = commercial_signature(product)
        old_sig = _signatures.get(product.id)
        old_monthly = None

        if old_sig and old_sig != sig:
            changes += 1
            # recover old monthly from cache file would be better; use previous_monthly_price field
            old_monthly = product.previous_monthly_price
            new_monthly = product.monthly_price
            if old_monthly and new_monthly and new_monthly < old_monthly:
                await log_event(
                    "MONTHLY_PRICE_DROP",
                    product_id=product.id,
                    old_value=str(old_monthly),
                    new_value=str(new_monthly),
                )
                notifications += await evaluate_alerts_for_product(
                    product, old_sig, sig, old_monthly, new_monthly
                )
            elif product.promotion:
                await log_event("PROMOTION_CHANGED", product_id=product.id, new_value=product.promotion or "")
        _signatures[product.id] = sig

    logger.info("[POLL] products=%s changes=%s notifications=%s", len(products), changes, notifications)
    return {"products": len(products), "changes": changes, "notifications": notifications}


async def bootstrap_signatures() -> None:
    products = await product_source.get_products(active_only=False)
    for p in products:
        _signatures[p.id] = commercial_signature(p)


async def get_recent_events(limit: int = 25) -> list[dict]:
    table_id = get_settings().nocodb_events_table_id
    if not table_id:
        return []
    rows = await nocodb.list_records(table_id, limit=min(limit, 200))
    events: list[dict] = []
    for row in rows:
        f = row if row.get("event_type") else row.get("fields", row)
        events.append(
            {
                "_record_id": row.get("Id") or row.get("id"),
                "product_id": f.get("product_id"),
                "event_type": f.get("event_type"),
                "old_value": f.get("old_value"),
                "new_value": f.get("new_value"),
                "metadata": f.get("metadata"),
                "created_at": f.get("created_at") or row.get("CreatedAt"),
            }
        )
    events.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
    return events[:limit]
