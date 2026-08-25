from app.services.product_pager import pager_caption, pager_keyboard
from app.services.product_service import Product, product_card_text


def _sample_product(name: str, monthly: float) -> Product:
    return Product(
        record_id=1,
        id=name.lower().replace(" ", "-"),
        slug=name.lower().replace(" ", "-"),
        active=True,
        brand="Samsung",
        name=name,
        model=name,
        capacity="256 GB",
        color="Negro",
        category="smartphone",
        price=799,
        previous_price=899,
        monthly_price=monthly,
        previous_monthly_price=monthly + 2,
        months=48,
        original_price=999,
        saving=180,
        discount_percentage=20,
        promotion="Promo demo",
        gift=None,
        image_url="https://example.com/phone.jpg",
        product_url="https://example.com",
        is_new=False,
        featured=True,
        deal_score=80,
        camera_score=8,
        battery_score=7,
        business_score=6,
        premium_score=7,
        value_score=8,
    )


def test_pager_caption_includes_counter_and_hint():
    product = _sample_product("Galaxy S25", 12.5)
    text = pager_caption(product, "🔥 Mejores ofertas", 1, 5, deal=True)
    assert "2/5" in text
    assert "Galaxy S25" in text
    assert "▶️" in text
    assert "◀️" in text
    assert product_card_text(product, deal=True) in text


def test_pager_keyboard_has_navigation_only():
    product = _sample_product("Pixel 11", 8.5)
    kb = pager_keyboard(product, 1, 5)
    rows = kb["inline_keyboard"]
    assert rows[0][0]["callback_data"] == "pager:prev"
    assert rows[0][1]["text"] == "2/5"
    assert rows[0][2]["callback_data"] == "pager:next"
    assert rows[1][0]["text"] == "👀 Ver oferta"
    assert rows[-1][0]["callback_data"] == "menu:home"
