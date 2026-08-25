from __future__ import annotations

from typing import Any

from app.services.product_service import Product, product_card_text, product_source
from app.services.telegram_client import telegram_client

PagerState = dict[str, Any]


def pager_caption(product: Product, title: str, index: int, total: int, *, deal: bool = False) -> str:
    return f"{title} · <b>{index + 1}/{total}</b>\n\n{product_card_text(product, deal=deal)}"


def pager_keyboard(product: Product, index: int, total: int) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = [
        [
            {"text": "◀️", "callback_data": "pager:prev"},
            {"text": f"{index + 1}/{total}", "callback_data": "pager:noop"},
            {"text": "▶️", "callback_data": "pager:next"},
        ]
    ]
    if product.product_url:
        rows.append([{"text": "👀 Ver oferta", "url": product.product_url}])
    rows.append([{"text": "🔔 Avísame", "callback_data": f"alert:menu:{product.id}"}])
    rows.append([{"text": "🏠 Menú principal", "callback_data": "menu:home"}])
    return {"inline_keyboard": rows}


async def _load_products(product_ids: list[str]) -> list[Product]:
    products: list[Product] = []
    for pid in product_ids:
        product = await product_source.get_product(pid)
        if product:
            products.append(product)
    return products


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

    product_ids: list[str] = pager["product_ids"]
    products = await _load_products(product_ids)
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
        if product.image_url:
            result = await telegram_client.api(
                "editMessageMedia",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "media": {
                        "type": "photo",
                        "media": product.image_url,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    "reply_markup": keyboard,
                },
            )
        else:
            result = await telegram_client.api(
                "editMessageText",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                },
            )
        if not result.get("ok"):
            pager["message_id"] = None
            await render_product_pager(chat_id, state, edit=False)
        return

    if product.image_url:
        result = await telegram_client.api(
            "sendPhoto",
            {
                "chat_id": chat_id,
                "photo": product.image_url,
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
        )
    else:
        result = await telegram_client.send_message(chat_id, caption, reply_markup=keyboard)

    if result.get("ok"):
        pager["message_id"] = result["result"]["message_id"]


async def move_product_pager(chat_id: int, state: PagerState, delta: int) -> None:
    pager = state.get("pager")
    if not pager:
        return
    total = len(pager["product_ids"])
    if total <= 1:
        return
    pager["index"] = (int(pager["index"]) + delta) % total
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
