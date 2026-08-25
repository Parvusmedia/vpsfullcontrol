from __future__ import annotations

import logging
from typing import Any

from app.services.product_image import get_normalized_product_image
from app.services.product_service import Product, product_card_text, product_source
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.pager")

PagerState = dict[str, Any]

PAGER_NAV_HINT = (
    "Puedes ir navegando cada oferta haciendo clic en los botones "
    "<b>▶️</b> para el siguiente producto o <b>◀️</b> para volver al anterior."
)


def pager_caption(product: Product, title: str, index: int, total: int, *, deal: bool = False) -> str:
    parts: list[str] = []
    if total > 1:
        parts.append(f"<i>{PAGER_NAV_HINT}</i>\n\n")
    parts.append(f"{title} · <b>{index + 1}/{total}</b>\n\n{product_card_text(product, deal=deal)}")
    return "".join(parts)


def _pager_nav_row(index: int, total: int) -> list[dict[str, str]]:
    counter = {"text": f"{index + 1}/{total}", "callback_data": "pager:noop"}
    if total <= 1:
        return [counter]
    if index <= 0:
        return [counter, {"text": "▶️", "callback_data": "pager:next"}]
    if index >= total - 1:
        return [{"text": "◀️", "callback_data": "pager:prev"}, counter]
    return [
        {"text": "◀️", "callback_data": "pager:prev"},
        counter,
        {"text": "▶️", "callback_data": "pager:next"},
    ]


def pager_keyboard(product: Product, index: int, total: int) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = [_pager_nav_row(index, total)]
    if product.product_url:
        rows.append([{"text": "👀 Ver oferta", "url": product.product_url}])
    rows.append([{"text": "🔔 Avísame", "callback_data": f"alert:menu:{product.id}"}])
    rows.append([{"text": "🏠 Menú principal", "callback_data": "menu:home"}])
    return {"inline_keyboard": rows}


async def _resolve_products(state: PagerState) -> list[Product]:
    pager = state.get("pager")
    if not pager:
        return []

    cached = pager.get("products")
    if cached:
        return cached

    product_ids: list[str] = pager.get("product_ids", [])
    all_products = await product_source.get_products()
    by_id = {p.id: p for p in all_products}
    products = [by_id[pid] for pid in product_ids if pid in by_id]
    pager["products"] = products
    return products


async def _send_pager_message(
    chat_id: int,
    product: Product,
    caption: str,
    keyboard: dict[str, Any],
) -> dict[str, Any]:
    photo_bytes = await get_normalized_product_image(product)
    result = await telegram_client.send_photo_bytes(
        chat_id,
        photo_bytes,
        caption=caption,
        reply_markup=keyboard,
    )
    if result.get("ok"):
        return result

    logger.warning("sendPhoto bytes failed for %s, falling back to text", product.id)
    return await telegram_client.send_message(chat_id, caption, reply_markup=keyboard)


async def _edit_pager_message(
    chat_id: int,
    message_id: int,
    product: Product,
    caption: str,
    keyboard: dict[str, Any],
) -> dict[str, Any]:
    photo_bytes = await get_normalized_product_image(product)
    result = await telegram_client.edit_message_media_bytes(
        chat_id,
        message_id,
        photo_bytes,
        caption=caption,
        reply_markup=keyboard,
    )
    if result.get("ok"):
        return result

    logger.warning("editMessageMedia bytes failed for %s, falling back to editMessageText", product.id)
    return await telegram_client.api(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": caption,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
        },
    )


async def open_product_pager(
    chat_id: int,
    state: PagerState,
    products: list[Product],
    title: str,
    *,
    deal: bool = False,
) -> None:
    if not products:
        await telegram_client.send_message(chat_id, f"{title}\n\nNo hay productos disponibles.")
        return

    state["pager"] = {
        "product_ids": [p.id for p in products],
        "products": products,
        "index": 0,
        "title": title,
        "deal": deal,
        "message_id": None,
    }
    await render_product_pager(chat_id, state)


async def render_product_pager(chat_id: int, state: PagerState, *, edit: bool = False) -> None:
    pager = state.get("pager")
    if not pager:
        return

    products = await _resolve_products(state)
    if not products:
        await telegram_client.send_message(chat_id, "No hay productos disponibles.")
        state.pop("pager", None)
        return

    total = len(products)
    index = int(pager["index"]) % total
    pager["index"] = index
    product = products[index]
    title = str(pager["title"])
    deal = bool(pager.get("deal"))
    caption = pager_caption(product, title, index, total, deal=deal)
    keyboard = pager_keyboard(product, index, total)
    message_id = pager.get("message_id")

    if message_id and edit:
        result = await _edit_pager_message(chat_id, message_id, product, caption, keyboard)
        if not result.get("ok"):
            pager["message_id"] = None
            await render_product_pager(chat_id, state, edit=False)
        return

    result = await _send_pager_message(chat_id, product, caption, keyboard)
    if result.get("ok"):
        pager["message_id"] = result["result"]["message_id"]
    else:
        logger.error("Failed to render pager for chat %s product %s: %s", chat_id, product.id, result)
        await telegram_client.send_message(
            chat_id,
            "No he podido mostrar la ficha del producto. Prueba de nuevo con /ofertas.",
        )


async def move_product_pager(chat_id: int, state: PagerState, delta: int) -> None:
    pager = state.get("pager")
    if not pager:
        return
    total = len(pager.get("products") or pager.get("product_ids") or [])
    if total <= 1:
        return
    new_index = int(pager["index"]) + delta
    if new_index < 0 or new_index >= total:
        return
    pager["index"] = new_index
    await render_product_pager(chat_id, state, edit=True)


async def handle_pager_callback(chat_id: int, state: PagerState, data: str) -> bool:
    if data == "pager:prev":
        await move_product_pager(chat_id, state, -1)
        return True
    if data == "pager:next":
        await move_product_pager(chat_id, state, 1)
        return True
    if data == "pager:noop":
        return True
    return False
