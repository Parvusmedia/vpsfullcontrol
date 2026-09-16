from app.services.product_service import Product


def _product(**kwargs) -> Product:
    defaults = dict(
        record_id=1,
        id="test",
        slug="test",
        active=True,
        brand="Samsung",
        name="Galaxy S25",
        model="S25",
        capacity="256 GB",
        color="",
        category="smartphone",
        price=799,
        previous_price=999,
        monthly_price=14.0,
        previous_monthly_price=18.0,
        months=48,
        original_price=999,
        saving=200,
        discount_percentage=20,
        promotion="Oferta lanzamiento",
        gift=None,
        image_url=None,
        product_url=None,
        is_new=True,
        featured=True,
        deal_score=50,
        camera_score=5,
        battery_score=5,
        business_score=4,
        premium_score=5,
        value_score=4,
    )
    defaults.update(kwargs)
    return Product(**defaults)


def test_card_text_deal_shows_monthly_before_after():
    text = _product().card_text(deal=True)
    assert "OFERTA PARA TI" in text
    assert "18 €/mes" in text
    assert "14 €/mes" in text
    assert "🏷️ Oferta lanzamiento" in text


def test_card_text_includes_demo_disclaimer():
    text = _product().card_text()
    assert "Demo conceptual" in text
