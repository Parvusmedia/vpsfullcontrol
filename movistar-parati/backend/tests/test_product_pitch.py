from app.services.product_pitch import forme_results_intro, preference_ask_message, product_pitch
from app.services.product_service import Product


def _product(**kwargs) -> Product:
    base = dict(
        record_id=1,
        id="pixel-11-256",
        slug="pixel-11-256",
        active=True,
        brand="Google",
        name="Google Pixel 9",
        model="Pixel 9",
        capacity="256 GB",
        color="Negro",
        category="smartphone",
        price=599,
        previous_price=None,
        monthly_price=12,
        previous_monthly_price=None,
        months=48,
        original_price=None,
        saving=None,
        discount_percentage=None,
        promotion="Superoferta",
        gift=None,
        image_url=None,
        product_url="https://example.com",
        is_new=False,
        featured=True,
        deal_score=80,
        camera_score=5,
        battery_score=4,
        business_score=3,
        premium_score=4,
        value_score=5,
    )
    base.update(kwargs)
    return Product(**base)


def test_preference_ask_message_camera():
    text = preference_ask_message("camera")
    assert "buena cámara" in text.lower()


def test_product_pitch_camera_explains_why():
    product = _product(camera_score=5, brand="Google")
    pitch = product_pitch(product, "camera", rank=1, max_monthly=15)
    assert "mejor recomendación" in pitch.lower()
    assert "cámara" in pitch.lower() or "detalle" in pitch.lower()
    assert "Google" in pitch
    assert "15" in pitch


def test_product_pitch_battery_lower_score():
    product = _product(battery_score=2, brand="Xiaomi")
    pitch = product_pitch(product, "battery", rank=2)
    assert "batería" in pitch.lower() or "autonomía" in pitch.lower()


def test_forme_results_intro():
    intro = forme_results_intro("camera", max_monthly=20, brand="Google", count=3)
    assert "buena cámara" in intro
    assert "Google" in intro
    assert "20" in intro
    assert "por qué encaja" in intro.lower()
