from __future__ import annotations

import logging
from typing import Any

from app.services.change_detection import create_alert, alert_type_label, deactivate_alert, get_user_alerts
from app.services.product_image import get_normalized_product_image
from app.services.product_pager import handle_pager_callback, open_product_pager
from app.services.product_service import Product, product_card_text, product_source
from app.services.recommend import recommend_products
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.bot")

_user_state: dict[int, dict[str, Any]] = {}

# Botones grandes del teclado inferior (siempre visibles).
BTN_OFERTAS = "🔥 Ofertas"
BTN_MOVILES = "📱 Móviles"
BTN_NOVEDADES = "🆕 Novedades"
BTN_PARAMI = "💙 Para mí"
BTN_MENU = "🏠 Menú"

_GREETINGS = {
    "hola", "buenas", "buenos dias", "buenos días", "buenas tardes", "buenas noches",
    "hey", "hi", "hello", "inicio", "empezar", "menu", "menú", "start",
}


def _state(chat_id: int) -> dict[str, Any]:
    return _user_state.setdefault(chat_id, {})


def _home_row() -> list[dict[str, str]]:
    return [{"text": "🏠 Menú principal", "callback_data": "menu:home"}]


def _reply_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": BTN_OFERTAS}, {"text": BTN_MOVILES}],
            [{"text": BTN_NOVEDADES}, {"text": BTN_PARAMI}],
            [{"text": BTN_MENU}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
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
    keyboard = product_keyboard(product)
    photo_bytes = await get_normalized_product_image(product)
    result = await telegram_client.send_photo_bytes(
        chat_id,
        photo_bytes,
        caption=text,
        reply_markup=keyboard,
    )
    if result.get("ok"):
        return
    logger.warning("sendPhoto bytes failed for %s, falling back to text", product.id)
    await telegram_client.send_message(chat_id, text, reply_markup=keyboard)


async def show_main_menu(chat_id: int, *, greeting: bool = True, first_time: bool = False) -> None:
    _state(chat_id).pop("flow", None)
    _state(chat_id).pop("pager", None)
    if first_time or greeting:
        text = (
            "👋 <b>¡Hola! Bienvenido a Movistar Para Ti</b>\n\n"
            "Te ayudamos a encontrar móviles y ofertas que encajen contigo, "
            "y te avisamos si bajan de precio.\n\n"
            "👉 Solo tienes que elegir un botón para navegar por las opciones. "
            "También puedes usar el menú <b>☰</b> abajo a la izquierda del teclado.\n\n"
            "<i>Concept Demo — datos de ejemplo, no ofertas reales de Movistar.</i>"
        )
        _state(chat_id)["onboarded"] = True
    else:
        text = (
            "🏠 <b>Menú principal</b>\n\n"
            "Elige una opción con los botones de abajo o abre el menú "
            "<b>☰</b> a la izquierda del teclado."
        )
    await telegram_client.send_message(chat_id, text, reply_markup=_reply_keyboard())


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
    mine = await get_user_alerts(user_id)
    if not mine:
        await telegram_client.send_message(
            chat_id,
            "No tienes avisos activos.\n\nCrea uno desde cualquier ficha con <b>🔔 Avísame</b>.",
            reply_markup=_reply_keyboard(),
        )
        return
    lines = ["🔔 <b>Tus avisos</b>\n"]
    for alert in mine:
        lines.append(f"• {alert.get('product_name')} — {alert_type_label(alert.get('alert_type'))}")
    lines.append("\nPulsa <b>✏️ Editar</b> para eliminar alguno.")
    await telegram_client.send_message(
        chat_id,
        "\n".join(lines),
        reply_markup={
            "inline_keyboard": [
                [{"text": "✏️ Editar", "callback_data": "alerts:edit"}],
                [{"text": "🏠 Menú principal", "callback_data": "menu:home"}],
            ]
        },
    )


async def show_alerts_edit_menu(chat_id: int, user_id: int) -> None:
    mine = await get_user_alerts(user_id)
    if not mine:
        await telegram_client.send_message(
            chat_id,
            "Ya no tienes avisos activos.",
            reply_markup=_reply_keyboard(),
        )
        return

    rows: list[list[dict[str, str]]] = []
    for alert in mine:
        record_id = alert.get("_record_id")
        if not record_id:
            continue
        name = str(alert.get("product_name") or "Producto")
        label = alert_type_label(alert.get("alert_type"))
        button_text = f"❌ {name}"[:60]
        rows.append([{"text": button_text, "callback_data": f"alerts:del:{record_id}"}])

    rows.append([{"text": "« Volver a la lista", "callback_data": "menu:alerts"}])
    rows.append([{"text": "🏠 Menú principal", "callback_data": "menu:home"}])

    await telegram_client.send_message(
        chat_id,
        "✏️ <b>Editar avisos</b>\n\nPulsa el aviso que quieres <b>eliminar</b>:",
        reply_markup={"inline_keyboard": rows},
    )


async def show_help(chat_id: int) -> None:
    help_text = (
        "ℹ️ <b>Ayuda — Movistar Para Ti</b>\n\n"
        "Concept Demo — datos de ejemplo, no ofertas reales de Movistar.\n\n"
        "<b>Navegación</b>\n"
        "Usa los botones de abajo del teclado o el menú <b>☰</b> a la izquierda.\n\n"
        "<b>Comandos</b>\n"
        "/start — Empezar / bienvenida\n"
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
    await telegram_client.send_message(chat_id, help_text, reply_markup=_reply_keyboard())


def _command_name(text: str) -> str | None:
    if not text.startswith("/"):
        return None
    head = text.split()[0]
    return head.split("@", 1)[0].lower()


def _is_casual_greeting(text: str) -> bool:
    normalized = text.strip().lower().rstrip("!.?")
    return normalized in _GREETINGS


async def _route_text_action(chat_id: int, user_id: int, text: str) -> bool:
    actions = {
        BTN_OFERTAS: show_deals,
        BTN_MOVILES: show_phones_menu,
        BTN_NOVEDADES: show_new_products,
        BTN_PARAMI: start_forme_flow,
        BTN_MENU: lambda cid: show_main_menu(cid, greeting=False),
    }
    action = actions.get(text.strip())
    if action:
        await action(chat_id)
        return True
    return False


async def handle_update(update: dict[str, Any]) -> None:
    try:
        if "message" in update:
            await _handle_message(update["message"])
        elif "callback_query" in update:
            await _handle_callback(update["callback_query"])
    except Exception:
        logger.exception("Failed to handle Telegram update")


async def _handle_message(message: dict[str, Any]) -> None:
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = (message.get("text") or "").strip()
    command = _command_name(text)
    st = _state(chat_id)

    if command == "/start":
        first_time = not st.get("onboarded")
        await show_main_menu(chat_id, greeting=True, first_time=first_time)
        return
    if command == "/menu":
        await show_main_menu(chat_id, greeting=False)
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

    if await _route_text_action(chat_id, user_id, text):
        return

    if _is_casual_greeting(text) or not st.get("onboarded"):
        await show_main_menu(chat_id, greeting=not st.get("onboarded"), first_time=not st.get("onboarded"))
        return

    await telegram_client.send_message(
        chat_id,
        "No he entendido ese mensaje.\n\nPulsa <b>🏠 Menú</b> abajo o escribe /menu.",
        reply_markup=_reply_keyboard(),
    )


async def _handle_callback(callback: dict[str, Any]) -> None:
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback.get("data", "")
    st = _state(chat_id)

    if data.startswith("pager:"):
        await telegram_client.answer_callback(callback["id"])
        await handle_pager_callback(chat_id, st, data)
        return

    await telegram_client.answer_callback(callback["id"])

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
    elif data == "alerts:edit":
        await show_alerts_edit_menu(chat_id, user_id)
    elif data.startswith("alerts:del:"):
        record_id = data.split(":", 2)[2]
        removed = await deactivate_alert(record_id, user_id)
        if removed:
            remaining = await get_user_alerts(user_id)
            if remaining:
                await telegram_client.send_message(chat_id, "✅ Aviso eliminado.")
                await show_alerts_edit_menu(chat_id, user_id)
            else:
                await telegram_client.send_message(
                    chat_id,
                    "✅ Aviso eliminado.\n\nYa no tienes avisos activos.",
                    reply_markup=_reply_keyboard(),
                )
        else:
            await telegram_client.send_message(chat_id, "No se pudo eliminar ese aviso.")
