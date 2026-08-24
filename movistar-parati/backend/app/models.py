from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(120))
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str | None] = mapped_column(String(120))
    deep_link_payload: Mapped[str | None] = mapped_column(String(255))
    movistar_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    movistar_phone: Mapped[str | None] = mapped_column(String(20))
    movistar_display_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    alerts: Mapped[list["Alert"]] = relationship(back_populates="telegram_user")
    interests: Mapped[list["ProductInterest"]] = relationship(back_populates="telegram_user")
    campaign_interests: Mapped[list["CampaignInterest"]] = relationship(back_populates="telegram_user")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80), index=True)
    image_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    monthly_price: Mapped[float] = mapped_column(Float)
    original_monthly_price: Mapped[float] = mapped_column(Float)
    savings_eur: Mapped[float] = mapped_column(Float, default=0)
    stock: Mapped[int] = mapped_column(Integer, default=10)
    promotion_label: Mapped[str | None] = mapped_column(String(120))
    purchase_url: Mapped[str] = mapped_column(String(500))
    conditions: Mapped[str | None] = mapped_column(Text)
    promo_starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    promo_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preorder_open: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    prices: Mapped[list["ProductPrice"]] = relationship(back_populates="product")


class ProductPrice(Base):
    __tablename__ = "product_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    monthly_price: Mapped[float] = mapped_column(Float)
    original_monthly_price: Mapped[float] = mapped_column(Float)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    change_reason: Mapped[str | None] = mapped_column(String(120))

    product: Mapped["Product"] = relationship(back_populates="prices")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    condition: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    telegram_user: Mapped["TelegramUser"] = relationship(back_populates="alerts")


class ProductInterest(Base):
    __tablename__ = "product_interests"
    __table_args__ = (UniqueConstraint("telegram_user_id", "product_id", name="uq_user_product_interest"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    interest_type: Mapped[str] = mapped_column(String(64), default="follow")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    telegram_user: Mapped["TelegramUser"] = relationship(back_populates="interests")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    campaign_type: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CampaignInterest(Base):
    __tablename__ = "campaign_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.id"), index=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    category: Mapped[str | None] = mapped_column(String(80))
    brand: Mapped[str | None] = mapped_column(String(80))
    max_monthly_price: Mapped[float | None] = mapped_column(Float)
    minimum_discount: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="waiting")
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    telegram_user: Mapped["TelegramUser"] = relationship(back_populates="campaign_interests")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int | None] = mapped_column(ForeignKey("telegram_users.id"), index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    movistar_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    interest: Mapped[str | None] = mapped_column(String(255))
    product_id: Mapped[str | None] = mapped_column(String(64))
    campaign: Mapped[str | None] = mapped_column(String(64))
    intent_score: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    product_id: Mapped[str | None] = mapped_column(String(64))
    campaign_id: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str | None] = mapped_column(String(120))
    utm_source: Mapped[str | None] = mapped_column(String(120))
    utm_campaign: Mapped[str | None] = mapped_column(String(120))
    deep_link: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MatchRecord(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(64))
    match_type: Mapped[str] = mapped_column(String(64))
    rule_summary: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "telegram_user_id",
            "product_id",
            "trigger_type",
            "trigger_ref",
            name="uq_notification_dedup",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[str] = mapped_column(String(64))
    trigger_type: Mapped[str] = mapped_column(String(64))
    trigger_ref: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
