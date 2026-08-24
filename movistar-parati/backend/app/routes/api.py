from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Alert, CampaignInterest, Product, ProductInterest, TelegramUser
from app.services.bot_handlers import get_or_create_user
from app.services.events import log_event

router = APIRouter(prefix="/api", tags=["api"])


class AlertCreate(BaseModel):
    telegram_user_id: int
    product_id: str
    condition: str = "monthly_price_below"
    value: float


class CampaignRegister(BaseModel):
    telegram_user_id: int
    category: str | None = None
    brand: str | None = None
    max_monthly_price: float | None = None
    minimum_discount: float | None = None


class MockOtpRequest(BaseModel):
    phone: str
    code: str


@router.get("/products")
def list_products(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Product).filter(Product.active.is_(True))
    if category:
        q = q.filter(Product.category == category)
    return [_product_dict(p) for p in q.order_by(Product.monthly_price).all()]


@router.get("/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Not found")
    return _product_dict(product)


@router.post("/products/{product_id}/follow")
def follow_product(product_id: str, telegram_user_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(404, "Product not found")
    existing = (
        db.query(ProductInterest)
        .filter_by(telegram_user_id=telegram_user_id, product_id=product_id)
        .one_or_none()
    )
    if not existing:
        db.add(ProductInterest(telegram_user_id=telegram_user_id, product_id=product_id))
        log_event(db, "product_followed", telegram_user_id=telegram_user_id, product_id=product_id)
        db.commit()
    return {"ok": True}


@router.post("/alerts")
def create_alert(body: AlertCreate, db: Session = Depends(get_db)):
    db.add(
        Alert(
            telegram_user_id=body.telegram_user_id,
            product_id=body.product_id,
            condition=body.condition,
            value=body.value,
        )
    )
    log_event(db, "price_alert_created", telegram_user_id=body.telegram_user_id, product_id=body.product_id)
    db.commit()
    return {"ok": True}


@router.post("/campaigns/{campaign_id}/register")
def register_campaign(campaign_id: str, body: CampaignRegister, db: Session = Depends(get_db)):
    db.add(
        CampaignInterest(
            telegram_user_id=body.telegram_user_id,
            campaign_id=campaign_id,
            category=body.category,
            brand=body.brand,
            max_monthly_price=body.max_monthly_price,
            minimum_discount=body.minimum_discount,
            status="waiting",
        )
    )
    log_event(db, "black_friday_registered", telegram_user_id=body.telegram_user_id, campaign_id=campaign_id)
    db.commit()
    return {"ok": True}


@router.post("/auth/mock-otp")
def mock_otp(body: MockOtpRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    allowed = {n.strip() for n in settings.mock_otp_numbers.split(",") if n.strip()}
    if body.phone not in allowed or body.code != settings.mock_otp_code:
        raise HTTPException(400, "Invalid OTP")
    user = db.query(TelegramUser).filter_by(movistar_phone=body.phone).first()
    if not user:
        raise HTTPException(404, "User not found for phone")
    user.movistar_verified = True
    user.movistar_display_name = "Carlos"
    db.commit()
    return {"ok": True, "message": "Cliente Movistar identificado", "name": user.movistar_display_name}


@router.get("/miniapp/me")
def miniapp_me(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_user_id: int | None = Header(default=None, alias="X-Telegram-User-Id"),
):
    # Demo: accept header from miniapp; production would validate initData
    if not x_telegram_user_id:
        raise HTTPException(401, "Missing telegram user")
    user = db.query(TelegramUser).filter_by(telegram_id=x_telegram_user_id).one_or_none()
    if not user:
        user = TelegramUser(telegram_id=x_telegram_user_id)
        db.add(user)
        db.commit()
    log_event(db, "miniapp_opened", telegram_user_id=user.id)
    db.commit()
    return {
        "telegram_id": user.telegram_id,
        "movistar_verified": user.movistar_verified,
        "display_name": user.movistar_display_name,
    }


def _product_dict(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "image_url": p.image_url,
        "monthly_price": p.monthly_price,
        "original_monthly_price": p.original_monthly_price,
        "savings_eur": p.savings_eur,
        "stock": p.stock,
        "promotion_label": p.promotion_label,
        "purchase_url": p.purchase_url,
        "preorder_open": p.preorder_open,
    }
