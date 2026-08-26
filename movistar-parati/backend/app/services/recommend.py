from __future__ import annotations

from app.services.product_service import Product, product_source

PREFERENCE_MAP = {
    "camera": "camera_score",
    "battery": "battery_score",
    "work": "business_score",
    "premium": "premium_score",
    "value": "value_score",
}


def _in_price_range(
    product: Product,
    *,
    price_min: float | None,
    price_max: float | None,
    purchase_mode: str = "cuotas",
) -> bool:
    terminal = product.terminal_price(purchase_mode=purchase_mode)
    if terminal is None:
        return price_min is None and price_max is None
    if price_min is not None and terminal < price_min:
        return False
    if price_max is not None and terminal > price_max:
        return False
    return True


async def recommend_products(
    preference: str,
    brand: str | None,
    *,
    price_min: float | None = None,
    price_max: float | None = None,
    purchase_mode: str = "cuotas",
    limit: int = 3,
) -> list[Product]:
    products = await product_source.get_products()
    score_field = PREFERENCE_MAP.get(preference, "value_score")

    def pref_score(p: Product) -> float:
        base = float(getattr(p, score_field, 0) or 0)
        deal = p.deal_score or 0
        brand_bonus = 3 if brand and p.brand.lower() == brand.lower() else 0
        return base * 10 + deal + brand_bonus

    filtered = products
    if brand and brand.lower() not in {"any", "me da igual", "cualquiera"}:
        filtered = [p for p in products if p.brand.lower() == brand.lower()] or products

    if price_min is not None or price_max is not None:
        in_range = [
            p
            for p in filtered
            if _in_price_range(
                p,
                price_min=price_min,
                price_max=price_max,
                purchase_mode=purchase_mode,
            )
        ]
        if in_range:
            filtered = in_range

    ranked = sorted(filtered, key=pref_score, reverse=True)
    return ranked[:limit]
