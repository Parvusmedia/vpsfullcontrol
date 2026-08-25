from __future__ import annotations

import logging
from typing import Any

from app.services.change_detection import create_alert
from app.services.product_pager import handle_pager_callback, open_product_pager
from app.services.product_service import Product, product_card_text, product_source
from app.services.recommend import recommend_products
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.bot")

_user_state: dict[int, dict[str, Any]] = {}


def _state(chat_id: int) -> dict[str, Any]:
    return _user_state.setdefault(chat_id, {})


def _home_row() -> list[dict[str, str]]:
    return [{"text": "🏠 Menú principal", "callback_data": "menu:home"}]


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
            _home_row(),
        ]
    }


def product_keyboard(p: Product) -> dict:
    buttons = []
    if p.product_url:
        buttons.append([{"text": "👀 Ver oferta", "url": p.product_url}])
    buttons.append([{"text": "🔔 Avísame", "callback_data": f"alert:menu:{p.id}"}])
    buttons.append(_home_row())
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


async def show_main_menu(chat_id: int, *, greeting: bool = True) -> None:
    _state(chat_id).pop("flow", None)
    if greeting:
        text = (
            "👋 Hola\n\n"
            "Soy <b>Movistar Para Ti</b>.\n\n"
            "Te ayudo a descubrir móviles y ofertas que pueden interesarte "
            "y puedo avisarte cuando cambien sus condiciones.\n\n"
            "¿Qué quieres ver?"
        )
    else:
        text = "🏠 <b>Menú principal</b>\n\nElige una opción o usa el botón ☰ junto al teclado."
    await telegram_client.send_message(chat_id, text, reply_markup=_main_menu())


async def show_phones_menu(chat_id: int) -> None:
    await telegram_client.send_message(chat_id, "📱 <b>Ver móviles</b>\n\nElige marca o filtro:", reply_markup=_brand_menu())


async def show_deals(chat_id: int) -> None:
    products = await product_source.get_deals(5)
    await open_product_pager(chat_id, _state(chat_id), products, "🔥 Mejores ofertas", deal=True)


async def show_new_products(chat_id: int) -> None:
    products = await product_source.get_new_products(5)
    await open_product_pager(chat_id, _state(chat_id), products, "🆕 Novedades")


async def start_forme_flow(chat_id: int) -> None:
    st = _state(chat_id)
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
                _home_row(),
            ]
        },
    )


async def show_user_alerts(chat_id: int, user_id: int) -> None:
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


async def show_help(chat_id: int) -> None:
    help_text = (
        "ℹ️ <b>Ayuda — Movistar Para Ti</b>\n\n"
        "Concept Demo — datos de ejemplo, no ofertas reales de Movistar.\n\n"
        "<b>Navegación</b>\n"
        "Pulsa el botón <b>☰</b> junto al teclado para ver todos los comandos.\n\n"
        "<b>Comandos</b>\n"
        "/menu — Volver al menú principal\n"
        "/ofertas — Mejores ofertas del catálogo\n"
        "/moviles — Móviles por marca y filtros\n"
        "/novedades — Productos nuevos\n"
        "/parami — Recomendaciones según tus preferencias\n"
        "/avisos — Tus alertas de precio activas\n"
        "/ayuda — Esta ayuda\n\n"
        "En cualquier ficha puedes pulsar <b>Avísame</b> para recibir un aviso "
        "cuando cambien precio o condiciones."
    )
    await telegram_client.send_message(chat_id, help_text, reply_markup=_main_menu())


def _command_name(text: str) -> str | None:
    if not text.startswith("/"):
        return None
    head = text.split()[0]
    return head.split("@", 1)[0].lower()


async def handle_update(update: dict[str, Any]) -> None:
    if "message" in update:
        await _handle_message(update["message"])
    elif "callback_query" in update:
        await _handle_callback(update["callback_query"])


async def _handle_message(message: dict[str, Any]) -> None:
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = (message.get("text") or "").strip()
    command = _command_name(text)

    if command in {"/start", "/menu"}:
        await show_main_menu(chat_id, greeting=command == "/start")
        return
    if command == "/ofertas":
        await show_deals(chat_id)
        return
    if command == "/novedades":
        await show_new_products(chat_id)
        return
    if command == "/moviles":
        await show_phones_menu(chat_id)
        return
    if command == "/parami":
        await start_forme_flow(chat_id)
        return
    if command == "/avisos":
        await show_user_alerts(chat_id, user_id)
        return
    if command in {"/ayuda", "/help"}:
        await show_help(chat_id)
        return

    await telegram_client.send_message(
        chat_id,
        "No entendí ese mensaje. Usa /menu o /ayuda.",
        reply_markup=_main_menu(),
    )


async def _handle_callback(callback: dict[str, Any]) -> None:
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback.get("data", "")
    await telegram_client.answer_callback(callback["id"])
    st = _state(chat_id)

    if data == "menu:home":
        _state(chat_id).pop("pager", None)
        await show_main_menu(chat_id, greeting=False)
    elif data == "menu:deals":
        await show_deals(chat_id)
    elif data == "menu:new":
        await show_new_products(chat_id)
    elif data == "menu:phones":
        await show_phones_menu(chat_id)
    elif data.startswith("brand:"):
        brand = data.split(":")[1]
        products = await product_source.get_products_by_brand(brand, 5)
        await open_product_pager(chat_id, st, products, f"📱 {brand}")
    elif data.startswith("filter:monthly:"):
        max_p = float(data.split(":")[2])
        products = await product_source.get_products_under_monthly_price(max_p, 5)
        await open_product_pager(chat_id, st, products, f"💸 Menos de {max_p:.0f} €/mes")
    elif data == "menu:forme":
        await start_forme_flow(chat_id)
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
                    _home_row(),
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
                    _home_row(),
                ]
            },
        )
    elif data.startswith("forme:brand:"):
        brand = data.split(":")[2]
        picks = await recommend_products(st.get("preference", "value"), st.get("max_monthly"), brand)
        await open_product_pager(chat_id, st, picks, "💙 Para mí")
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
        await show_user_alerts(chat_id, user_id)
    elif await handle_pager_callback(chat_id, st, data):
        return
