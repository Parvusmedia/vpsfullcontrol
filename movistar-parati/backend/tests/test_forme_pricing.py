from app.services.product_pitch import (
    forme_client_question,
    forme_price_question,
    forme_results_intro,
    product_pitch,
)
from app.services.product_service import Product
from app.services.recommend import _in_price_range


def _product(**kwargs) -> Product:
    base = dict(
        record_id=1,
        id="galaxy-s25",
        slug="galaxy-s25",
        active=True,
        brand="Samsung",
        name="Samsung Galaxy S25",
        model="Galaxy S25",
        capacity="256 GB",
        color="Grafito",
        category="smartphone",
        price=799,
        previous_price=999,
        monthly_price=14,
        previous_monthly_price=18,
        months=48,
        original_price=999,
        saving=200,
        discount_percentage=20,
        promotion="Oferta lanzamiento",
        gift=None,
        image_url=None,
        product_url="https://example.com",
        is_new=True,
        featured=True,
        deal_score=80,
        camera_score=5,
        battery_score=5,
        business_score=4,
        premium_score=5,
        value_score=4,
        battery_mah=4000,
        fast_charge_w=45,
    )
    base.update(kwargs)
    return Product(**base)


def test_terminal_price_client_vs_non_client():
    product = _product()
    assert product.terminal_price(is_client=True) == 799
    assert product.terminal_price(is_client=False) == 999


def test_card_text_non_client_shows_client_benefit():
    text = _product().card_text(is_client=False)
    assert "999" in text
    assert "799" in text
    assert "cliente Movistar" in text


def test_card_text_client_shows_installments():
    text = _product().card_text(is_client=True)
    assert "14" in text
    assert "799" in text


def test_forme_price_question_mentions_terminal_and_client_benefit():
    text = forme_price_question("battery")
    assert "terminal" in text.lower()
    assert "cliente movistar" in text.lower()
    assert "cuotas" in text.lower()


def test_forme_client_question():
    text = forme_client_question()
    assert "cliente movistar" in text.lower()
    assert "cuotas" in text.lower()


def test_forme_results_intro_with_price_and_client():
    intro = forme_results_intro(
        "battery",
        price_min=400,
        price_max=700,
        is_client=False,
        brand="Samsung",
        count=2,
    )
    assert "400" in intro
    assert "700" in intro
    assert "sin ser cliente" in intro.lower()
    assert "Samsung" in intro


def test_in_price_range_non_client_uses_original_price():
    product = _product()
    assert _in_price_range(product, price_min=900, price_max=None, is_client=False)
    assert not _in_price_range(product, price_min=None, price_max=850, is_client=False)
    assert _in_price_range(product, price_min=None, price_max=850, is_client=True)


def test_product_pitch_non_client_mentions_savings():
    product = _product()
    pitch = product_pitch(product, "battery", rank=1, is_client=False)
    assert "799" in pitch
    assert "999" in pitch or "ahorro" in pitch.lower()
