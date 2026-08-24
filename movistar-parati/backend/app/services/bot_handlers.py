import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models import Alert, CampaignInterest, Product, ProductInterest, TelegramUser
from app.services.events import log_event
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.bot")


def get_or_create_user(db: Session, tg_user: dict[str, Any], source: str | None = None) -> TelegramUser:
    telegram_id = tg_user["id"]
    user = db.query(TelegramUser).filter_by(telegram_id=telegram_id).one_or_none()
    if not user:
        user = TelegramUser(
            telegram_id=telegram_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            last_name=tg_user.get("last_name"),
            source=source,
        )
        db.add(user)
        db.flush()
        log_event(db, "telegram_bot_started", telegram_user_id=user.id, source=source)
    else:
        user.username = tg_user.get("username")
        user.first_name = tg_user.get("first_name")
        user.last_name = tg_user.get("last_name")
    db.commit()
    return user


def _main_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🔥 Black Friday", "callback_data": "bf:start"}],
            [{"text": "📱 Buscar dispositivo", "callback_data": "finder:start"}],
            [{"text": "🛍 Ver ofertas", "callback_data": "offers:list"}],
            [{"text": "🟢 Preventa iPhone", "callback_data": "preorder:start"}],
            [{"text": "📲 Abrir Mini App", "web_app": {"url": "{{MINIAPP_URL}}"}}],
        ]
    }


def _replace_miniapp_url(keyboard: dict, miniapp_url: str) -> dict:
    import copy
    import json

    raw = json.dumps(keyboard).replace("{{MINIAPP_URL}}", miniapp_url)
    return copy.deepcopy(json.loads(raw))


async def handle_update(db: Session, update: dict[str, Any], miniapp_url: str) -> None:
    if "message" in update:
        await _handle_message(db, update["message"], miniapp_url)
    elif "callback_query" in update:
        await _handle_callback(db, update["callback_query"], miniapp_url)


async def _handle_message(db: Session, message: dict[str, Any], miniapp_url: str) -> None:
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()
    user = get_or_create_user(db, message["from"])

    if text.startswith("/start"):
        payload = text.split(maxsplit=1)[1] if " " in text else None
        if payload:
            user.deep_link_payload = payload
            user.source = payload.split("_")[0] if payload else None
            db.commit()
        welcome = (
            "👋 <b>Movistar Para ti</b>\n\n"
            "Ofertas y avisos personalizados. Dinos qué buscas y te avisamos cuando encaje.\n\n"
            "<i>Concept Demo — Not Live Movistar Data</i>"
        )
        kb = _replace_miniapp_url(_main_menu_keyboard(), miniapp_url)
        await telegram_client.send_message(chat_id, welcome, reply_markup=kb)
        return

    if text.startswith("/ofertas"):
        await _send_offers(db, chat_id)
        return

    await telegram_client.send_message(
        chat_id,
        "Usa los botones del menú o escribe /start para empezar.",
        reply_markup=_replace_miniapp_url(_main_menu_keyboard(), miniapp_url),
    )


async def _handle_callback(db: Session, callback: dict[str, Any], miniapp_url: str) -> None:
    chat_id = callback["message"]["chat"]["id"]
    data = callback.get("data", "")
    user = get_or_create_user(db, callback["from"])
    await telegram_client.answer_callback(callback["id"])

    if data == "offers:list":
        await _send_offers(db, chat_id)
    elif data == "finder:start":
        await telegram_client.send_message(
            chat_id,
            "¿Qué buscas?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Móvil", "callback_data": "finder:cat:smartphone"}],
                    [{"text": "Smart TV", "callback_data": "finder:cat:tv"}],
                    [{"text": "Gaming", "callback_data": "finder:cat:gaming"}],
                    [{"text": "Informática", "callback_data": "finder:cat:computing"}],
                ]
            },
        )
    elif data.startswith("finder:cat:"):
        category = data.split(":")[-1]
        await telegram_client.send_message(
            chat_id,
            "¿Cuánto quieres pagar al mes?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "< 5 €", "callback_data": f"finder:budget:{category}:5"}],
                    [{"text": "< 10 €", "callback_data": f"finder:budget:{category}:10"}],
                    [{"text": "< 20 €", "callback_data": f"finder:budget:{category}:20"}],
                    [{"text": "Indiferente", "callback_data": f"finder:budget:{category}:999"}],
                ]
            },
        )
    elif data.startswith("finder:budget:"):
        _, _, category, budget = data.split(":")
        max_price = float(budget)
        q = db.query(Product).filter(Product.active.is_(True), Product.category == category)
        if max_price < 900:
            q = q.filter(Product.monthly_price <= max_price)
        products = q.order_by(Product.monthly_price).limit(5).all()
        if not products:
            await telegram_client.send_message(chat_id, "No encontramos dispositivos con esos criterios.")
            return
        lines = ["✅ <b>Estos dispositivos encajan contigo:</b>\n"]
        buttons = []
        for p in products:
            lines.append(f"• <b>{p.name}</b> — {p.monthly_price:.2f} €/mes")
            buttons.append([{"text": f"Ver {p.brand}", "callback_data": f"product:{p.id}"}])
        await telegram_client.send_message(chat_id, "\n".join(lines), reply_markup={"inline_keyboard": buttons})
    elif data.startswith("product:"):
        product_id = data.split(":")[1]
        product = db.get(Product, product_id)
        if not product:
            return
        await _send_product_card(db, chat_id, user, product)
    elif data.startswith("follow:"):
        product_id = data.split(":")[1]
        existing = (
            db.query(ProductInterest)
            .filter_by(telegram_user_id=user.id, product_id=product_id)
            .one_or_none()
        )
        if not existing:
            db.add(ProductInterest(telegram_user_id=user.id, product_id=product_id, interest_type="follow"))
            log_event(db, "product_followed", telegram_user_id=user.id, product_id=product_id)
            db.commit()
        await telegram_client.send_message(chat_id, "🔔 Producto seguido. Te avisaremos si baja de precio.")
    elif data.startswith("alert:"):
        product_id = data.split(":")[1]
        product = db.get(Product, product_id)
        if not product:
            return
        threshold = round(product.monthly_price - 1, 2) if product.monthly_price > 1 else product.monthly_price
        db.add(
            Alert(
                telegram_user_id=user.id,
                product_id=product_id,
                condition="monthly_price_below",
                value=threshold,
            )
        )
        log_event(db, "price_alert_created", telegram_user_id=user.id, product_id=product_id)
        db.commit()
        await telegram_client.send_message(
            chat_id,
            f"✅ Alerta creada: te avisaremos si baja de <b>{threshold:.2f} €/mes</b>.",
        )
    elif data == "bf:start":
        await telegram_client.send_message(
            chat_id,
            "🔥 <b>Black Friday Movistar</b>\n\n¿Qué quieres comprar?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "iPhone", "callback_data": "bf:cat:smartphone:Apple"}],
                    [{"text": "Samsung Galaxy", "callback_data": "bf:cat:smartphone:Samsung"}],
                    [{"text": "Smart TV", "callback_data": "bf:cat:tv:any"}],
                    [{"text": "PlayStation", "callback_data": "bf:cat:gaming:Sony"}],
                ]
            },
        )
    elif data.startswith("bf:cat:"):
        _, _, category, brand = data.split(":")
        await telegram_client.send_message(
            chat_id,
            "¿Qué haría que la oferta te interesara?",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "< 10 €/mes", "callback_data": f"bf:price:{category}:{brand}:10"}],
                    [{"text": "< 15 €/mes", "callback_data": f"bf:price:{category}:{brand}:15"}],
                    [{"text": "< 20 €/mes", "callback_data": f"bf:price:{category}:{brand}:20"}],
                    [{"text": "Cualquier oferta", "callback_data": f"bf:price:{category}:{brand}:999"}],
                ]
            },
        )
    elif data.startswith("bf:price:"):
        _, _, category, brand, price = data.split(":")
        db.add(
            CampaignInterest(
                telegram_user_id=user.id,
                campaign_id="black-friday-2026",
                category=category,
                brand=None if brand == "any" else brand,
                max_monthly_price=float(price) if float(price) < 900 else None,
                status="waiting",
            )
        )
        log_event(db, "black_friday_registered", telegram_user_id=user.id, campaign_id="black-friday-2026")
        db.commit()
        await telegram_client.send_message(
            chat_id,
            "✅ Te avisaremos cuando encontremos una oferta que encaje contigo.",
        )
    elif data == "preorder:start":
        await telegram_client.send_message(
            chat_id,
            "📱 <b>Nuevo iPhone</b>\n\nPróximamente en Movistar.",
            reply_markup={
                "inline_keyboard": [[{"text": "Quiero que me avisen", "callback_data": "preorder:register"}]]
            },
        )
    elif data == "preorder:register":
        db.add(
            CampaignInterest(
                telegram_user_id=user.id,
                campaign_id="iphone-preorder-2026",
                category="smartphone",
                brand="Apple",
                status="waiting",
            )
        )
        log_event(db, "preorder_registered", telegram_user_id=user.id, campaign_id="iphone-preorder-2026")
        db.commit()
        await telegram_client.send_message(chat_id, "✅ Registrado. Te avisaremos cuando abra la preventa.")


async def _send_offers(db: Session, chat_id: int) -> None:
    products = db.query(Product).filter(Product.active.is_(True)).order_by(Product.monthly_price).limit(8).all()
    for p in products:
        await _send_product_card(db, chat_id, None, p)


async def _send_product_card(db: Session, chat_id: int, user: TelegramUser | None, product: Product) -> None:
    if user:
        log_event(db, "product_viewed", telegram_user_id=user.id, product_id=product.id)
        db.commit()
    promo = f"\n🔥 {product.promotion_label}" if product.promotion_label else ""
    text = (
        f"<b>{product.name}</b>{promo}\n\n"
        f"<s>{product.original_monthly_price:.2f} €/mes</s>\n"
        f"<b>{product.monthly_price:.2f} €/mes</b>\n"
        f"Ahorras {product.savings_eur:.0f} €"
    )
    await telegram_client.send_message(
        chat_id,
        text,
        reply_markup={
            "inline_keyboard": [
                [{"text": "Ver oferta", "url": product.purchase_url}],
                [
                    {"text": "🔔 Seguir", "callback_data": f"follow:{product.id}"},
                    {"text": "Avísame si baja", "callback_data": f"alert:{product.id}"},
                ],
            ]
        },
    )
