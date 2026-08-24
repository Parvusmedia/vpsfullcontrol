import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Alert, Campaign, CampaignInterest, MatchRecord, Notification, Product
from app.services.events import log_event
from app.services.telegram_client import telegram_client

logger = logging.getLogger("movistar-parati.matching")


@dataclass
class MatchResult:
    matched: int = 0
    queued: int = 0
    sent: int = 0
    skipped: int = 0
    details: list[dict] | None = None

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = []


def _trigger_ref(trigger_type: str, product_id: str, ref: str) -> str:
    return f"{trigger_type}:{ref}:{product_id}"


def _format_price_alert_message(product: Product, alert: Alert) -> str:
    return (
        f"🔥 Ha bajado el <b>{product.name}</b> que estabas siguiendo\n\n"
        f"Antes:\n{product.original_monthly_price:.2f} €/mes\n\n"
        f"Ahora:\n<b>{product.monthly_price:.2f} €/mes</b>\n\n"
        f"Tu alerta era:\nmenos de {alert.value:.2f} €/mes"
    )


def _format_campaign_message(product: Product, interest: CampaignInterest, campaign: Campaign) -> str:
    label = campaign.name
    rule = ""
    if interest.max_monthly_price:
        rule = f"\n\nTú pediste que te avisáramos por debajo de:\n<b>{interest.max_monthly_price:.0f} €/mes</b>"
    return (
        f"🔥 <b>{label}</b>\n\n"
        f"Ya está activa una oferta que encaja con lo que estabas esperando.\n\n"
        f"<b>{product.name}</b>\n\n"
        f"Antes:\n{product.original_monthly_price:.2f} €/mes\n\n"
        f"Ahora:\n<b>{product.monthly_price:.2f} €/mes</b>"
        f"{rule}"
    )


def _format_preorder_message(product: Product) -> str:
    return (
        f"🟢 <b>Preventa abierta</b>\n\n"
        f"Ya puedes reservar el <b>{product.name}</b> con Movistar.\n\n"
        f"Eres uno de los usuarios que pidió recibir el aviso."
    )


def _product_keyboard(product: Product) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "Ver oferta", "url": product.purchase_url}],
            [{"text": "🔔 Seguir precio", "callback_data": f"follow:{product.id}"}],
        ]
    }


async def _queue_notification(
    db: Session,
    *,
    telegram_user_id: int,
    telegram_chat_id: int,
    product: Product,
    trigger_type: str,
    trigger_ref: str,
    message: str,
    send_now: bool = True,
) -> tuple[str, bool]:
    existing = (
        db.query(Notification)
        .filter_by(
            telegram_user_id=telegram_user_id,
            product_id=product.id,
            trigger_type=trigger_type,
            trigger_ref=trigger_ref,
        )
        .first()
    )
    if existing:
        return "skipped", False

    notification = Notification(
        telegram_user_id=telegram_user_id,
        product_id=product.id,
        trigger_type=trigger_type,
        trigger_ref=trigger_ref,
        message=message,
        status="queued",
    )
    db.add(notification)
    db.flush()

    if send_now and telegram_client.configured:
        result = await telegram_client.send_message(
            telegram_chat_id,
            message,
            reply_markup=_product_keyboard(product),
        )
        if result.get("ok"):
            notification.status = "sent"
            notification.sent_at = datetime.now(timezone.utc)
            log_event(
                db,
                "telegram_notification_sent",
                telegram_user_id=telegram_user_id,
                product_id=product.id,
                payload={"trigger_type": trigger_type},
            )
            return "sent", True
        notification.status = "failed"
        return "failed", False

    return "queued", True


async def run_matching(
    db: Session,
    *,
    trigger: str,
    product_id: str | None = None,
    campaign_id: str | None = None,
    ref: str | None = None,
    send_notifications: bool = True,
) -> MatchResult:
    result = MatchResult()
    ref = ref or datetime.now(timezone.utc).isoformat()

    if trigger == "price_change" and product_id:
        product = db.get(Product, product_id)
        if not product:
            return result

        logger.info("[PRICE CHANGE] %s %.2f", product.name, product.monthly_price)
        alerts = db.query(Alert).filter(Alert.product_id == product_id, Alert.active.is_(True)).all()
        logger.info("[MATCH ENGINE] Checking %s price alerts", len(alerts))

        for alert in alerts:
            user = alert.telegram_user
            if alert.condition == "monthly_price_below" and product.monthly_price > alert.value:
                result.skipped += 1
                continue

            result.matched += 1
            msg = _format_price_alert_message(product, alert)
            trigger_ref = _trigger_ref("price_change", product.id, ref)
            status, created = await _queue_notification(
                db,
                telegram_user_id=user.id,
                telegram_chat_id=user.telegram_id,
                product=product,
                trigger_type="price_change",
                trigger_ref=trigger_ref,
                message=msg,
                send_now=send_notifications,
            )
            if created:
                db.add(
                    MatchRecord(
                        telegram_user_id=user.id,
                        product_id=product.id,
                        match_type="price_alert",
                        rule_summary=f"<{alert.value} EUR/mo",
                    )
                )
                log_event(db, "offer_matched", telegram_user_id=user.id, product_id=product.id)
            if status == "sent":
                result.sent += 1
            elif status == "queued":
                result.queued += 1
            else:
                result.skipped += 1
            result.details.append({"user_id": user.id, "type": "price_alert", "status": status})

        # Campaign interests for active black friday
        campaign = db.get(Campaign, "black-friday-2026")
        if campaign and campaign.active:
            await _match_campaign_interests(db, product, campaign, ref, result, send_notifications)

    elif trigger == "campaign_activated" and campaign_id:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return result
        products = db.query(Product).filter(Product.active.is_(True)).all()
        for product in products:
            await _match_campaign_interests(db, product, campaign, ref, result, send_notifications)

    elif trigger == "preorder_opened" and product_id:
        product = db.get(Product, product_id)
        if not product or not product.preorder_open:
            return result
        interests = (
            db.query(CampaignInterest)
            .filter(
                CampaignInterest.campaign_id == "iphone-preorder-2026",
                CampaignInterest.status == "waiting",
            )
            .all()
        )
        for interest in interests:
            user = interest.telegram_user
            result.matched += 1
            trigger_ref = _trigger_ref("preorder_open", product.id, ref)
            status, created = await _queue_notification(
                db,
                telegram_user_id=user.id,
                telegram_chat_id=user.telegram_id,
                product=product,
                trigger_type="preorder_open",
                trigger_ref=trigger_ref,
                message=_format_preorder_message(product),
                send_now=send_notifications,
            )
            if created:
                interest.status = "notified"
                db.add(
                    MatchRecord(
                        telegram_user_id=user.id,
                        product_id=product.id,
                        campaign_id="iphone-preorder-2026",
                        match_type="preorder",
                        rule_summary="preorder_open",
                    )
                )
            if status == "sent":
                result.sent += 1
            elif status == "queued":
                result.queued += 1

    db.commit()
    return result


async def _match_campaign_interests(
    db: Session,
    product: Product,
    campaign: Campaign,
    ref: str,
    result: MatchResult,
    send_notifications: bool,
) -> None:
    interests = (
        db.query(CampaignInterest)
        .filter(CampaignInterest.campaign_id == campaign.id, CampaignInterest.status == "waiting")
        .all()
    )
    for interest in interests:
        user = interest.telegram_user
        if interest.category and interest.category != product.category:
            continue
        if interest.brand and interest.brand.lower() != product.brand.lower():
            continue
        if interest.max_monthly_price and product.monthly_price > interest.max_monthly_price:
            continue
        if interest.minimum_discount:
            if product.original_monthly_price <= 0:
                continue
            discount = (1 - product.monthly_price / product.original_monthly_price) * 100
            if discount < interest.minimum_discount:
                continue

        result.matched += 1
        trigger_ref = _trigger_ref("campaign", product.id, f"{campaign.id}:{ref}")
        status, created = await _queue_notification(
            db,
            telegram_user_id=user.id,
            telegram_chat_id=user.telegram_id,
            product=product,
            trigger_type="campaign_match",
            trigger_ref=trigger_ref,
            message=_format_campaign_message(product, interest, campaign),
            send_now=send_notifications,
        )
        if created:
            db.add(
                MatchRecord(
                    telegram_user_id=user.id,
                    product_id=product.id,
                    campaign_id=campaign.id,
                    match_type="campaign",
                    rule_summary=f"max {interest.max_monthly_price} EUR/mo",
                )
            )
            log_event(
                db,
                "offer_matched",
                telegram_user_id=user.id,
                product_id=product.id,
                campaign_id=campaign.id,
            )
        if status == "sent":
            result.sent += 1
        elif status == "queued":
            result.queued += 1
