from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Alert, Campaign, CampaignInterest, Product, ProductInterest, ProductPrice, TelegramUser
from app.services.events import log_event
from app.services.matching_engine import run_matching

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if x_admin_key != get_settings().admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


class PriceUpdate(BaseModel):
    monthly_price: float
    original_monthly_price: float | None = None


@router.post("/products/{product_id}/price")
async def update_price(
    product_id: str,
    body: PriceUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    old_price = product.monthly_price
    product.monthly_price = body.monthly_price
    if body.original_monthly_price is not None:
        product.original_monthly_price = body.original_monthly_price
    product.savings_eur = max(0, product.original_monthly_price - product.monthly_price)
    db.add(
        ProductPrice(
            product_id=product_id,
            monthly_price=product.monthly_price,
            original_monthly_price=product.original_monthly_price,
            change_reason="admin_demo",
        )
    )
    db.commit()

    match = await run_matching(
        db,
        trigger="price_change",
        product_id=product_id,
        ref=f"{old_price}->{body.monthly_price}",
    )
    return {
        "product_id": product_id,
        "old_price": old_price,
        "new_price": body.monthly_price,
        "matched": match.matched,
        "queued": match.queued,
        "sent": match.sent,
        "skipped": match.skipped,
    }


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.active = True
    if campaign_id == "black-friday-2026":
        for p in db.query(Product).filter(Product.active.is_(True)).all():
            p.promotion_label = "Black Friday"
    db.commit()
    match = await run_matching(db, trigger="campaign_activated", campaign_id=campaign_id, ref="activate")
    return {"campaign_id": campaign_id, "active": True, "match": match.__dict__}


@router.post("/preorders/{product_id}/open")
async def open_preorder(
    product_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    product.preorder_open = True
    db.commit()
    match = await run_matching(db, trigger="preorder_opened", product_id=product_id, ref="open")
    return {"product_id": product_id, "preorder_open": True, "match": match.__dict__}


@router.post("/matching/run")
async def run_matching_manual(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    match = await run_matching(db, trigger="campaign_activated", campaign_id="black-friday-2026", ref="manual")
    return match.__dict__


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: None = Depends(verify_admin)) -> dict[str, Any]:
    interests = db.query(CampaignInterest).count()
    alerts = db.query(Alert).filter(Alert.active.is_(True)).count()
    users = db.query(TelegramUser).count()
    bf_users = db.query(CampaignInterest).filter_by(campaign_id="black-friday-2026").count()
    preorder_users = db.query(CampaignInterest).filter_by(campaign_id="iphone-preorder-2026").count()
    return {
        "demo_notice": "Concept Demo — Not Live Movistar Data",
        "users": users,
        "active_alerts": alerts,
        "campaign_interests": interests,
        "black_friday_registered": bf_users,
        "preorder_registered": preorder_users,
        "demand_seed": {
            "iPhone": 23482,
            "Samsung Galaxy": 11212,
            "PlayStation": 8430,
            "Smart TV": 6180,
            "Pixel": 3720,
        },
    }
