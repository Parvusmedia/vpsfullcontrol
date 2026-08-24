from __future__ import annotations

import logging
from typing import Any

from app.services.change_detection import create_alert
from app.services.product_service import Product, product_source
from app.services.recommend import recommend_products
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.bot")

_user_state: dict[int, dict[str, Any]] = {}


def _state(chat_id: int) -> dict[str, Any]:
    return _user_state.setdefault(chat_id, {})


def _main_menu() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🔥 Mejores ofertas", "callback_data": "menu:deals"}],
            [{"text": "📱 Ver móviles", "callback_data": "menu:phones"}],
            [{"text": "🆕 Novedades", "callback_data": "menu:new"}],
            [{"text": "💙 Para mí", "callback_data": "menu:forme"}],
            [{"text": "🔔 Mis avisos", "callback_data": "menu:alerts"}],
        ]
    }


def _brand_menu() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🍎 Apple", "callback_data": "brand:Apple"}],
            [{"text": "📱 Samsung", "callback_data": "brand:Samsung"}],
            [{"text": "✨ Google", "callback_data": "brand:Google"}],
            [{"text": "📱 Xiaomi", "callback_data": "brand:Xiaomi"}],
            [{"text": "🔥 Ofertas", "callback_data": "menu:deals"}],
            [{"text": "💸 Menos de 15 €/mes", "callback_data": "filter:monthly:15"}],
        ]
    }


def product_card_text(p: Product, *, deal: bool = False) -> str:
    lines = [f"📱 <b>{p.display_name}</b>\n"]
    if p.monthly_price is not None:
        lines.append(f"💳 <b>{p.monthly_price:.2f} €/mes</b>")
        if p.months:
            lines.append(f"{p.months} meses")
    if p.price is not None:
        lines.append(f"\n💰 Precio: {p.price:.0f} €")
    if p.saving:
        lines.append(f"\n🔥 Ahorras {p.saving:.0f} €")
    if p.gift:
        lines.append(f"\n🎁 {p.gift}")
    elif p.promotion:
        lines.append(f"\n🎁 {p.promotion}")
    if deal and p.previous_price and p.price and p.price < p.previous_price:
        lines.insert(1, f"🔥 <b>OFERTA PARA TI</b>\n\nAntes: {p.previous_price:.0f} €\nAhora: {p.price:.0f} €\n")
    return "\n".join(lines)


def product_keyboard(p: Product) -> dict:
    buttons = []
    if p.product_url:
        buttons.append([{"text": "👀 Ver oferta", "url": p.product_url}])
    buttons.append([{"text": "🔔 Avísame", "callback_data": f"alert:menu:{p.id}"}])
    return {"inline_keyboard": buttons}


async def send_product(chat_id: int, product: Product, *, deal: bool = False) -> None:
    text = product_card_text(product, deal=deal)
    if product.image_url:
        await telegram_client.api(
            "sendPhoto",
            {
                "chat_id": chat_id,
                "photo": product.image_url,
                "caption": text,
                "parse_mode": "HTML",
                "reply_markup": product_keyboard(product),
            },
        )
    else:
        await telegram_client.send_message(chat_id, text, reply_markup=product_keyboard(product))


async def handle_update(update: dict[str, Any]) -> None:
    if "message" in update:
        await _handle_message(update["message"])
    elif "callback_query" in update:
        await _handle_callback(update["callback_query"])


async def _handle_message(message: dict[str, Any]) -> None:
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()
    if text.startswith("/start"):
        welcome = (
            "👋 Hola\n\n"
            "Soy <b>Movistar Para Ti</b>.\n\n"
            "Te ayudo a descubrir móviles y ofertas que pueden interesarte "
            "y puedo avisarte cuando cambien sus condiciones.\n\n"
            "¿Qué quieres ver?"
        )
        await telegram_client.send_message(chat_id, welcome, reply_markup=_main_menu())
        return
    await telegram_client.send_message(chat_id, "Usa /start para comenzar.", reply_markup=_main_menu())


async def _handle_callback(callback: dict[str, Any]) -> None:
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback.get("data", "")
    await telegram_client.answer_callback(callback["id"])
    st = _state(chat_id)

    if data == "menu:deals":
        products = await product_source.get_deals(5)
        await telegram_client.send_message(chat_id, "🔥 <b>Mejores ofertas</b>")
        for p in products:
            await send_product(chat_id, p, deal=True)
    elif data == "menu:new":
        products = await product_source.get_new_products(5)
        await telegram_client.send_message(chat_id, "🆕 <b>Novedades</b>")
        for p in products:
            await send_product(chat_id, p)
    elif data == "menu:phones":
        await telegram_client.send_message(chat_id, "Elige marca o filtro:", reply_markup=_brand_menu())
    elif data.startswith("brand:"):
        brand = data.split(":")[1]
        products = await product_source.get_products_by_brand(brand, 5)
        for p in products:
            await send_product(chat_id, p)
    elif data.startswith("filter:monthly:"):
        max_p = float(data.split(":")[2])
        products = await product_source.get_products_under_monthly_price(max_p, 5)
        for p in products:
            await send_product(chat_id, p)
    elif data == "menu:forme":
        st["flow"] = "forme"
        await telegram_client.send_message(
            chat_id,
            "¿Qué móvil buscas?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "📸 Buena cámara", "callback_data": "forme:pref:camera"}],
                    [{"text": "🔋 Mucha batería", "callback_data": "forme:pref:battery"}],
                    [{"text": "💼 Trabajo", "callback_data": "forme:pref:work"}],
                    [{"text": "⭐ Gama alta", "callback_data": "forme:pref:premium"}],
                    [{"text": "💰 Calidad/precio", "callback_data": "forme:pref:value"}],
                ]
            },
        )
    elif data.startswith("forme:pref:"):
        st["preference"] = data.split(":")[2]
        await telegram_client.send_message(
            chat_id,
            "¿Cuánto quieres pagar al mes?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "< 10 €", "callback_data": "forme:budget:10"}],
                    [{"text": "10–20 €", "callback_data": "forme:budget:20"}],
                    [{"text": "20–30 €", "callback_data": "forme:budget:30"}],
                    [{"text": "Me da igual", "callback_data": "forme:budget:999"}],
                ]
            },
        )
    elif data.startswith("forme:budget:"):
        val = float(data.split(":")[2])
        st["max_monthly"] = None if val >= 900 else val
        await telegram_client.send_message(
            chat_id,
            "¿Alguna marca preferida?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Apple", "callback_data": "forme:brand:Apple"}],
                    [{"text": "Samsung", "callback_data": "forme:brand:Samsung"}],
                    [{"text": "Google", "callback_data": "forme:brand:Google"}],
                    [{"text": "Xiaomi", "callback_data": "forme:brand:Xiaomi"}],
                    [{"text": "Me da igual", "callback_data": "forme:brand:any"}],
                ]
            },
        )
    elif data.startswith("forme:brand:"):
        brand = data.split(":")[2]
        picks = await recommend_products(st.get("preference", "value"), st.get("max_monthly"), brand)
        await telegram_client.send_message(chat_id, "💙 <b>Estos son los que mejor encajan contigo</b>")
        for p in picks:
            await send_product(chat_id, p)
        st.pop("flow", None)
    elif data.startswith("product:"):
        pid = data.split(":")[1]
        p = await product_source.get_product(pid)
        if p:
            await send_product(chat_id, p)
    elif data.startswith("alert:menu:"):
        pid = data.split(":")[2]
        st["alert_product"] = pid
        await telegram_client.send_message(
            chat_id,
            "¿Qué quieres que te avisemos?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "📉 Si baja de precio", "callback_data": f"alert:set:{pid}:price_drop"}],
                    [{"text": "💳 Si baja la cuota mensual", "callback_data": f"alert:set:{pid}:monthly_price_drop"}],
                    [{"text": "🔥 Si aparece una mejor oferta", "callback_data": f"alert:set:{pid}:better_deal"}],
                    [{"text": "❌ Cancelar", "callback_data": "menu:phones"}],
                ]
            },
        )
    elif data.startswith("alert:set:"):
        _, _, pid, alert_type = data.split(":")
        p = await product_source.get_product(pid)
        if not p:
            return
        await create_alert(
            {
                "telegram_user_id": str(user_id),
                "product_id": p.id,
                "product_name": p.display_name,
                "alert_type": alert_type,
                "target_monthly_price": p.monthly_price,
                "active": True,
            }
        )
        await telegram_client.send_message(chat_id, f"✅ Te avisaremos sobre <b>{p.display_name}</b>.")
    elif data == "menu:alerts":
        from app.services.change_detection import get_active_alerts

        alerts = await get_active_alerts()
        mine = [a for a in alerts if str(a.get("telegram_user_id")) == str(user_id)]
        if not mine:
            await telegram_client.send_message(chat_id, "No tienes avisos activos.")
            return
        lines = ["🔔 <b>Tus avisos</b>\n"]
        for a in mine:
            lines.append(f"• {a.get('product_name')} ({a.get('alert_type')})")
        await telegram_client.send_message(chat_id, "\n".join(lines))
