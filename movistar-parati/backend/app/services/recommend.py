from __future__ import annotations

from app.services.product_service import Product, product_source

PREFERENCE_MAP = {
    "camera": "camera_score",
    "battery": "battery_score",
    "work": "business_score",
    "premium": "premium_score",
    "value": "value_score",
}


async def recommend_products(
    preference: str,
    max_monthly: float | None,
    brand: str | None,
    limit: int = 3,
) -> list[Product]:
    products = await product_source.get_products()
    score_field = PREFERENCE_MAP.get(preference, "value_score")

    def pref_score(p: Product) -> float:
        base = float(getattr(p, score_field, 0) or 0)
        deal = p.deal_score or 0
        monthly_penalty = 0
        if max_monthly and p.monthly_price and p.monthly_price > max_monthly:
            monthly_penalty = -10
        brand_bonus = 3 if brand and p.brand.lower() == brand.lower() else 0
        return base * 10 + deal + monthly_penalty + brand_bonus

    filtered = products
    if brand and brand.lower() not in {"any", "me da igual", "cualquiera"}:
        filtered = [p for p in products if p.brand.lower() == brand.lower()] or products
    if max_monthly:
        affordable = [p for p in filtered if p.monthly_price is not None and p.monthly_price <= max_monthly]
        if affordable:
            filtered = affordable

    ranked = sorted(filtered, key=pref_score, reverse=True)
    return ranked[:limit]
