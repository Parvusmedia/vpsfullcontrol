from app.services.product_pitch import (
    forme_price_question,
    forme_purchase_mode_question,
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
        price_libre=999,
        price_financed_total=799,
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


def test_terminal_price_libre_vs_cuotas():
    product = _product()
    assert product.terminal_price(purchase_mode="cuotas") == 799
    assert product.terminal_price(purchase_mode="libre") == 999


def test_card_text_libre_shows_compra_libre():
    text = _product().card_text(purchase_mode="libre")
    assert "Compra libre" in text
    assert "999" in text
    assert "799" in text


def test_card_text_cuotas_shows_movistar_wording():
    text = _product().card_text(purchase_mode="cuotas")
    assert "cuotas" in text.lower()
    assert "14" in text
    assert "799" in text
    assert "Libre" in text


def test_forme_price_question_mentions_libre_and_cuotas():
    text = forme_price_question("battery")
    assert "terminal" in text.lower()
    assert "libre" in text.lower()
    assert "cuotas" in text.lower()


def test_forme_purchase_mode_question():
    text = forme_purchase_mode_question()
    assert "compra libre" in text.lower()
    assert "cuotas" in text.lower()
    assert "clientes movistar" in text.lower()
    assert "pack" not in text.lower()
    assert "suele salir más barato" not in text.lower()


def test_forme_results_intro_alternatives():
    intro = forme_results_intro(
        "battery",
        price_min=400,
        price_max=700,
        purchase_mode="cuotas",
        brand="Samsung",
        count=2,
        match_type="alternatives",
    )
    assert "No tengo modelos exactamente dentro de ese rango" in intro
    assert "más cercanas" in intro
    assert "entre" not in intro.lower() or "exactamente" in intro


def test_card_text_decimal_monthly():
    product = _product(monthly_price=8.5, price_financed_total=408, price=408, months=48)
    text = product.card_text(purchase_mode="cuotas")
    assert "8,50 €/mes" in text


def test_forme_results_intro_with_price_and_mode():
    intro = forme_results_intro(
        "battery",
        price_min=400,
        price_max=700,
        purchase_mode="libre",
        brand="Samsung",
        count=2,
    )
    assert "400" in intro
    assert "700" in intro
    assert "compra libre" in intro.lower()
    assert "Samsung" in intro


def test_in_price_range_libre_uses_price_libre():
    product = _product()
    assert _in_price_range(product, price_min=900, price_max=None, purchase_mode="libre")
    assert not _in_price_range(product, price_min=None, price_max=850, purchase_mode="libre")
    assert _in_price_range(product, price_min=None, price_max=850, purchase_mode="cuotas")


def test_product_pitch_libre_mentions_financing_option():
    product = _product()
    pitch = product_pitch(product, "battery", rank=1, purchase_mode="libre")
    assert "799" in pitch
    assert "999" in pitch or "libre" in pitch.lower()
