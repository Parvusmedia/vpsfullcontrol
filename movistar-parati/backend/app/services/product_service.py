from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.services.nocodb import nocodb


@dataclass
class Product:
    record_id: str | int | None
    id: str
    slug: str
    active: bool
    brand: str
    name: str
    model: str
    capacity: str
    color: str
    category: str
    price: float | None
    previous_price: float | None
    monthly_price: float | None
    previous_monthly_price: float | None
    months: int | None
    original_price: float | None
    saving: float | None
    discount_percentage: float | None
    promotion: str | None
    gift: str | None
    image_url: str | None
    product_url: str | None
    is_new: bool
    featured: bool
    deal_score: float | None
    camera_score: int
    battery_score: int
    business_score: int
    premium_score: int
    value_score: int

    @property
    def display_name(self) -> str:
        parts = [self.name, self.capacity]
        return " ".join(p for p in parts if p).strip()

    def card_text(self, *, deal: bool = False) -> str:
        lines = [f"📱 <b>{self.display_name}</b>\n"]
        if deal and self.previous_monthly_price and self.monthly_price and self.monthly_price < self.previous_monthly_price:
            lines.append("🔥 <b>OFERTA PARA TI</b>\n")
            lines.append(f"Antes: <s>{self.previous_monthly_price:.2f} €/mes</s>")
            lines.append(f"Ahora: <b>{self.monthly_price:.2f} €/mes</b>")
            if self.months:
                lines.append(f"<i>{self.months} meses</i>")
        elif self.monthly_price is not None:
            lines.append(f"💳 <b>{self.monthly_price:.2f} €/mes</b>")
            if self.months:
                lines.append(f"<i>{self.months} meses</i>")
        if self.price is not None:
            lines.append(f"\n💰 Precio total: {self.price:.0f} €")
        if self.saving:
            lines.append(f"🔥 Ahorras {self.saving:.0f} €")
        if self.promotion:
            lines.append(f"\n🏷️ {self.promotion}")
        if self.gift:
            lines.append(f"\n🎁 {self.gift}")
        lines.append("\n<i>Demo conceptual · precios ilustrativos</i>")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "brand": self.brand,
            "name": self.name,
            "model": self.model,
            "capacity": self.capacity,
            "category": self.category,
            "price": self.price,
            "previous_price": self.previous_price,
            "monthly_price": self.monthly_price,
            "previous_monthly_price": self.previous_monthly_price,
            "months": self.months,
            "original_price": self.original_price,
            "saving": self.saving,
            "discount_percentage": self.discount_percentage,
            "promotion": self.promotion,
            "gift": self.gift,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "is_new": self.is_new,
            "featured": self.featured,
            "deal_score": self.deal_score or compute_deal_score(self),
        }


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v: Any, default: int = 0) -> int:
    if v is None or v == "":
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.lower() in {"1", "true", "yes", "si", "sí"}
    return False


def parse_product(row: dict) -> Product:
    f = row if "slug" in row else row.get("fields", row)
    pid = str(f.get("id") or f.get("slug") or "")
    return Product(
        record_id=row.get("Id") or row.get("id"),
        id=pid,
        slug=str(f.get("slug") or pid),
        active=_bool(f.get("active", True)),
        brand=str(f.get("brand") or ""),
        name=str(f.get("name") or ""),
        model=str(f.get("model") or ""),
        capacity=str(f.get("capacity") or ""),
        color=str(f.get("color") or ""),
        category=str(f.get("category") or "smartphone"),
        price=_num(f.get("price")),
        previous_price=_num(f.get("previous_price")),
        monthly_price=_num(f.get("monthly_price")),
        previous_monthly_price=_num(f.get("previous_monthly_price")),
        months=_int(f.get("months"), 48) or None,
        original_price=_num(f.get("original_price")),
        saving=_num(f.get("saving")),
        discount_percentage=_num(f.get("discount_percentage")),
        promotion=f.get("promotion") or None,
        gift=f.get("gift") or None,
        image_url=f.get("image_url") or None,
        product_url=f.get("product_url") or None,
        is_new=_bool(f.get("is_new")),
        featured=_bool(f.get("featured")),
        deal_score=_num(f.get("deal_score")),
        camera_score=_int(f.get("camera_score")),
        battery_score=_int(f.get("battery_score")),
        business_score=_int(f.get("business_score")),
        premium_score=_int(f.get("premium_score")),
        value_score=_int(f.get("value_score")),
    )


def compute_deal_score(p: Product) -> float:
    score = 0.0
    if p.discount_percentage and p.discount_percentage >= 30:
        score += 30
    if p.saving and p.saving >= 250:
        score += 20
    if p.monthly_price and p.monthly_price <= 15:
        score += 15
    if p.promotion:
        score += 15
    if p.gift:
        score += 10
    if p.featured:
        score += 10
    return min(score, 100)


def commercial_signature(p: Product) -> str:
    payload = {
        "price": p.price,
        "monthly_price": p.monthly_price,
        "original_price": p.original_price,
        "discount_percentage": p.discount_percentage,
        "promotion": p.promotion,
        "gift": p.gift,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


class NocoDBProductSource:
    async def get_products(self, *, active_only: bool = True) -> list[Product]:
        table_id = get_settings().nocodb_products_table_id
        if not table_id:
            return []
        rows = await nocodb.list_records(table_id, limit=200)
        products = [parse_product(r) for r in rows]
        if active_only:
            products = [p for p in products if p.active]
        return products

    async def get_product(self, product_id: str) -> Product | None:
        for p in await self.get_products(active_only=False):
            if p.id == product_id or p.slug == product_id:
                return p
        return None

    async def get_deals(self, limit: int = 5) -> list[Product]:
        products = await self.get_products()
        ranked = sorted(products, key=lambda p: p.deal_score or compute_deal_score(p), reverse=True)
        return ranked[:limit]

    async def get_new_products(self, limit: int = 5) -> list[Product]:
        return [p for p in await self.get_products() if p.is_new][:limit]

    async def get_featured_products(self, limit: int = 5) -> list[Product]:
        return [p for p in await self.get_products() if p.featured][:limit]

    async def get_products_by_brand(self, brand: str, limit: int = 5) -> list[Product]:
        brand_l = brand.lower()
        return [p for p in await self.get_products() if p.brand.lower() == brand_l][:limit]

    async def get_products_under_monthly_price(self, price: float, limit: int = 5) -> list[Product]:
        return [
            p for p in await self.get_products()
            if p.monthly_price is not None and p.monthly_price <= price
        ][:limit]

    async def get_brands(self) -> list[str]:
        brands = sorted({p.brand for p in await self.get_products() if p.brand})
        return brands

    async def update_monthly_price(self, product: Product, new_price: float) -> Product | None:
        table_id = get_settings().nocodb_products_table_id
        if not product.record_id:
            return None
        await nocodb.update_record(
            table_id,
            product.record_id,
            {
                "previous_monthly_price": product.monthly_price,
                "monthly_price": new_price,
            },
        )
        return await self.get_product(product.id)


product_source = NocoDBProductSource()


def product_card_text(p: Product, *, deal: bool = False) -> str:
    return p.card_text(deal=deal)
