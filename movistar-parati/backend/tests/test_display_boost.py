from app.services.bot_handlers import apply_display_boost
from app.services.product_service import Product


def _product(brand: str, pid: str) -> Product:
    return Product(
        record_id=1,
        id=pid,
        slug=pid,
        active=True,
        brand=brand,
        name=pid,
        model=pid,
        capacity="128 GB",
        color="",
        category="smartphone",
        price=500,
        previous_price=None,
        monthly_price=10,
        previous_monthly_price=None,
        months=48,
        original_price=None,
        saving=None,
        discount_percentage=None,
        promotion=None,
        gift=None,
        image_url=None,
        product_url=None,
        is_new=False,
        featured=False,
        deal_score=50,
        camera_score=5,
        battery_score=5,
        business_score=5,
        premium_score=5,
        value_score=5,
    )


def test_display_boost_apple_orders_apple_first():
    products = [_product("Samsung", "s1"), _product("Apple", "a1"), _product("Google", "g1")]
    boosted = apply_display_boost(products, "apple")
    assert [p.brand for p in boosted] == ["Apple", "Samsung", "Google"]


def test_display_boost_does_not_remove_brands():
    products = [_product("Apple", "a1"), _product("Samsung", "s1")]
    boosted = apply_display_boost(products, "android")
    assert len(boosted) == 2
