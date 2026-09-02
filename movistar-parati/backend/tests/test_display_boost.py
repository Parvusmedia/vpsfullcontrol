from app.services.bot_handlers import filter_by_segment
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


def test_filter_apple_only():
    products = [_product("Samsung", "s1"), _product("Apple", "a1")]
    filtered = filter_by_segment(products, "apple")
    assert len(filtered) == 1
    assert filtered[0].brand == "Apple"


def test_filter_android_excludes_apple():
    products = [_product("Apple", "a1"), _product("Samsung", "s1"), _product("Google", "g1")]
    filtered = filter_by_segment(products, "android")
    assert len(filtered) == 2
    assert all(p.brand != "Apple" for p in filtered)


def test_filter_all_keeps_everything():
    products = [_product("Apple", "a1"), _product("Samsung", "s1")]
    assert len(filter_by_segment(products, "all")) == 2
