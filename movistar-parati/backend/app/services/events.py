from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import Event


def log_event(
    db: Session,
    event_type: str,
    *,
    telegram_user_id: int | None = None,
    product_id: str | None = None,
    campaign_id: str | None = None,
    source: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    deep_link: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Event:
    event = Event(
        event_type=event_type,
        telegram_user_id=telegram_user_id,
        product_id=product_id,
        campaign_id=campaign_id,
        source=source,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        deep_link=deep_link,
        payload=payload or {},
    )
    db.add(event)
    return event


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
