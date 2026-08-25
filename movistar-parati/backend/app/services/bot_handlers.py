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
        "one_time_keyboard": False,
        "input_field_placeholder": "Elige una opción…",
    }


async def _restore_reply_keyboard(chat_id: int) -> None:
    """Fuerza a que Telegram vuelva a mostrar el teclado inferior tras menús inline."""
    result = await telegram_client.api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": ".",
            "reply_markup": {"remove_keyboard": True},
        },
    )
    temp_id = result.get("result", {}).get("message_id")
    if temp_id:
        await telegram_client.api("deleteMessage", {"chat_id": chat_id, "message_id": temp_id})


async def _clear_inline_keyboard(chat_id: int, message_id: int | None) -> None:
    if not message_id:
        return
    await telegram_client.api(
        "editMessageReplyMarkup",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        },
    )


def _nav_inline_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🔥 Ofertas", "callback_data": "menu:deals"},
                {"text": "📱 Móviles", "callback_data": "menu:phones"},
            ],
            [
                {"text": "🆕 Novedades", "callback_data": "menu:new"},
                {"text": "💙 Para mí", "callback_data": "menu:forme"},
            ],
            [{"text": "🔔 Mis avisos", "callback_data": "menu:alerts"}],
        ]
    }


def _segment_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🍎 Solo Apple", "callback_data": "segment:apple"},
                {"text": "🤖 Solo Android", "callback_data": "segment:android"},
            ],
            [
                {"text": "✨ Todas las marcas", "callback_data": "segment:all"},
            ],
            [_home_row()[0]],
        ]
    }


ANDROID_BRANDS = {"samsung", "google", "xiaomi"}


def filter_by_segment(products: list[Product], segment: str | None) -> list[Product]:
    if not segment or segment == "all":
        return products
    if segment == "apple":
        return [p for p in products if p.brand.lower() == "apple"]
    if segment == "android":
        return [p for p in products if p.brand.lower() in ANDROID_BRANDS]
    return products


_SEGMENT_LABELS = {
    "deals": "🔥 Mejores ofertas",
    "phones": "📱 Móviles",
    "new": "🆕 Novedades",
    "forme": "💙 Para mí",
}


async def prompt_segment_choice(chat_id: int, action: str) -> None:
    st = _state(chat_id)
    st["pending_action"] = action
    await telegram_client.send_message(
        chat_id,
        f"Has elegido <b>{_SEGMENT_LABELS.get(action, action)}</b>.\n\n"
        "¿Qué móviles quieres ver?",
        reply_markup=_segment_menu(),
    )


async def run_pending_action(chat_id: int, segment: str) -> None:
    st = _state(chat_id)
    action = st.pop("pending_action", None)
    if not action:
        return
    st["segment_filter"] = segment
    if action == "deals":
        await show_deals(chat_id)
    elif action == "new":
        await show_new_products(chat_id)
    elif action == "phones":
        await show_phones_menu(chat_id)
    elif action == "forme":
        await start_forme_flow(chat_id)


def _brand_menu(segment: str | None = None) -> dict:
    rows: list[list[dict[str, str]]] = []
    if segment == "apple":
        rows.append([{"text": "🍎 Apple", "callback_data": "brand:Apple"}])
    elif segment == "android":
        rows.extend(
            [
                [{"text": "📱 Samsung", "callback_data": "brand:Samsung"}],
                [{"text": "✨ Google", "callback_data": "brand:Google"}],
                [{"text": "📱 Xiaomi", "callback_data": "brand:Xiaomi"}],
            ]
        )
    else:
        rows.extend(
            [
                [{"text": "🍎 Apple", "callback_data": "brand:Apple"}],
                [{"text": "📱 Samsung", "callback_data": "brand:Samsung"}],
                [{"text": "✨ Google", "callback_data": "brand:Google"}],
                [{"text": "📱 Xiaomi", "callback_data": "brand:Xiaomi"}],
            ]
        )
    rows.extend(
        [
            [{"text": "🔥 Ofertas", "callback_data": "menu:deals"}],
            [{"text": "💸 Menos de 15 €/mes", "callback_data": "filter:monthly:15"}],
            _home_row(),
        ]
    )
    return {"inline_keyboard": rows}


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


async def show_main_menu(
    chat_id: int,
    *,
    greeting: bool = True,
    first_time: bool = False,
    restore_keyboard: bool = False,
    source_message_id: int | None = None,
) -> None:
    _state(chat_id).pop("flow", None)
    _state(chat_id).pop("pager", None)
    if source_message_id:
        await _clear_inline_keyboard(chat_id, source_message_id)
    if restore_keyboard:
        await _restore_reply_keyboard(chat_id)
    if first_time or greeting:
        text = (
            "👋 <b>¡Hola! Bienvenido a Movistar Para Ti</b>\n\n"
            "Te ayudamos a encontrar móviles y ofertas que encajen contigo, "
            "y te avisamos si bajan de precio.\n\n"
            "👉 Elige una opción con los <b>botones de este mensaje</b>. "
            "También puedes abrir el menú <b>☰</b> (abajo a la izquierda) "
            "para ver los comandos.\n\n"
            "<i>Concept Demo — datos de ejemplo, no ofertas reales de Movistar.</i>"
        )
        _state(chat_id)["onboarded"] = True
    else:
        text = (
            "🏠 <b>Menú principal</b>\n\n"
            "Elige una opción con los botones de este mensaje."
        )
    await telegram_client.send_message(chat_id, text, reply_markup=_nav_inline_menu())


async def _empty_segment_message(chat_id: int, action_label: str) -> None:
    await telegram_client.send_message(
        chat_id,
        f"No hay resultados de <b>{action_label}</b> para esta selección.\n\n"
        "Prueba con <b>✨ Todas las marcas</b> o vuelve al menú principal.",
        reply_markup=_nav_inline_menu(),
    )


async def show_phones_menu(chat_id: int) -> None:
    segment = _state(chat_id).get("segment_filter")
    if segment == "apple":
        products = filter_by_segment(await product_source.get_products_by_brand("Apple", 8), segment)
        if not products:
            await _empty_segment_message(chat_id, "móviles Apple")
            return
        await open_product_pager(chat_id, _state(chat_id), products[:5], "📱 Apple")
        return
    await telegram_client.send_message(
        chat_id,
        "📱 <b>Ver móviles</b>\n\nElige marca o filtro:",
        reply_markup=_brand_menu(segment),
    )


async def show_deals(chat_id: int) -> None:
    segment = _state(chat_id).get("segment_filter")
    products = filter_by_segment(await product_source.get_deals(12), segment)[:5]
    if not products:
        await _empty_segment_message(chat_id, "ofertas")
        return
    await open_product_pager(chat_id, _state(chat_id), products, "🔥 Mejores ofertas", deal=True)


async def show_new_products(chat_id: int) -> None:
    segment = _state(chat_id).get("segment_filter")
    products = filter_by_segment(await product_source.get_new_products(12), segment)[:5]
    if not products:
        await _empty_segment_message(chat_id, "novedades")
        return
    await open_product_pager(chat_id, _state(chat_id), products, "🆕 Novedades")


async def start_forme_flow(chat_id: int) -> None:
    st = _state(chat_id)
    st["flow"] = "forme"
    segment = st.get("segment_filter")
    if segment == "apple":
        st["forme_brand_locked"] = "Apple"
    elif segment == "android":
        st["forme_brand_locked"] = "android"
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
        "Usa los botones del mensaje o el menú <b>☰</b> a la izquierda del teclado.\n\n"
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
    await telegram_client.send_message(chat_id, help_text, reply_markup=_nav_inline_menu())


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
        BTN_OFERTAS: lambda cid: prompt_segment_choice(cid, "deals"),
        BTN_MOVILES: lambda cid: prompt_segment_choice(cid, "phones"),
        BTN_NOVEDADES: lambda cid: prompt_segment_choice(cid, "new"),
        BTN_PARAMI: lambda cid: prompt_segment_choice(cid, "forme"),
        BTN_MENU: lambda cid: show_main_menu(cid, greeting=False, restore_keyboard=True),
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
        await show_main_menu(chat_id, greeting=False, restore_keyboard=True)
        return
    if command == "/ofertas":
        await prompt_segment_choice(chat_id, "deals")
        return
    if command == "/novedades":
        await prompt_segment_choice(chat_id, "new")
        return
    if command == "/moviles":
        await prompt_segment_choice(chat_id, "phones")
        return
    if command == "/parami":
        await prompt_segment_choice(chat_id, "forme")
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
        await show_main_menu(
            chat_id,
            greeting=False,
            restore_keyboard=True,
            source_message_id=callback.get("message", {}).get("message_id"),
        )
    elif data == "menu:deals":
        await prompt_segment_choice(chat_id, "deals")
    elif data == "menu:new":
        await prompt_segment_choice(chat_id, "new")
    elif data == "menu:phones":
        await prompt_segment_choice(chat_id, "phones")
    elif data.startswith("brand:"):
        brand = data.split(":")[1]
        products = filter_by_segment(
            await product_source.get_products_by_brand(brand, 8),
            st.get("segment_filter"),
        )[:5]
        if not products:
            await _empty_segment_message(chat_id, f"móviles {brand}")
            return
        await open_product_pager(chat_id, st, products, f"📱 {brand}")
    elif data.startswith("filter:monthly:"):
        max_p = float(data.split(":")[2])
        products = filter_by_segment(
            await product_source.get_products_under_monthly_price(max_p, 8),
            st.get("segment_filter"),
        )[:5]
        if not products:
            await _empty_segment_message(chat_id, f"móviles bajo {max_p:.0f} €/mes")
            return
        await open_product_pager(chat_id, st, products, f"💸 Menos de {max_p:.0f} €/mes")
    elif data == "menu:forme":
        await prompt_segment_choice(chat_id, "forme")
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
        locked = st.get("forme_brand_locked")
        if locked == "Apple":
            picks = await recommend_products(st.get("preference", "value"), st.get("max_monthly"), "Apple")
            picks = filter_by_segment(picks, "apple")
            await open_product_pager(chat_id, st, picks, "💙 Para mí")
            st.pop("flow", None)
            st.pop("forme_brand_locked", None)
            return
        if locked == "android":
            picks: list[Product] = []
            for brand in ("Samsung", "Google", "Xiaomi"):
                picks.extend(await recommend_products(st.get("preference", "value"), st.get("max_monthly"), brand))
            picks = filter_by_segment(picks, "android")[:3]
            await open_product_pager(chat_id, st, picks, "💙 Para mí")
            st.pop("flow", None)
            st.pop("forme_brand_locked", None)
            return
        brand_rows = [
            [{"text": "Apple", "callback_data": "forme:brand:Apple"}],
            [{"text": "Samsung", "callback_data": "forme:brand:Samsung"}],
            [{"text": "Google", "callback_data": "forme:brand:Google"}],
            [{"text": "Xiaomi", "callback_data": "forme:brand:Xiaomi"}],
            [{"text": "Me da igual", "callback_data": "forme:brand:any"}],
            _home_row(),
        ]
        if st.get("segment_filter") == "apple":
            brand_rows = [[{"text": "Apple", "callback_data": "forme:brand:Apple"}], _home_row()]
        elif st.get("segment_filter") == "android":
            brand_rows = [
                [{"text": "Samsung", "callback_data": "forme:brand:Samsung"}],
                [{"text": "Google", "callback_data": "forme:brand:Google"}],
                [{"text": "Xiaomi", "callback_data": "forme:brand:Xiaomi"}],
                _home_row(),
            ]
        await telegram_client.send_message(
            chat_id,
            "¿Alguna marca preferida?",
            reply_markup={"inline_keyboard": brand_rows},
        )
    elif data.startswith("forme:brand:"):
        brand = data.split(":")[2]
        picks = await recommend_products(st.get("preference", "value"), st.get("max_monthly"), brand)
        picks = filter_by_segment(picks, st.get("segment_filter"))
        await open_product_pager(chat_id, st, picks[:3], "💙 Para mí")
        st.pop("flow", None)
        st.pop("forme_brand_locked", None)
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
        created = await create_alert(
            {
                "telegram_user_id": str(user_id),
                "product_id": p.id,
                "product_name": p.display_name,
                "alert_type": alert_type,
                "target_monthly_price": p.monthly_price,
                "active": True,
            }
        )
        if not created:
            await telegram_client.send_message(
                chat_id,
                f"Ya tienes un aviso activo para <b>{p.display_name}</b>.\n\n"
                "Gestiónalo desde <b>🔔 Mis avisos</b> → <b>✏️ Editar</b>.",
                reply_markup=_nav_inline_menu(),
            )
            return
        await telegram_client.send_message(
            chat_id,
            f"✅ Aviso activo para <b>{p.display_name}</b> — {alert_type_label(alert_type)}.",
        )
    elif data == "menu:alerts":
        await show_user_alerts(chat_id, user_id)
    elif data.startswith("segment:"):
        segment = data.split(":")[1]
        await run_pending_action(chat_id, segment)
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
