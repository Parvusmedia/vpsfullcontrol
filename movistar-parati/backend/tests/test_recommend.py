import asyncio

from app.services.product_service import Product
from app.services.recommend import RecommendResult, _distance_to_range, recommend_products


def _product(**kwargs) -> Product:
    base = dict(
        record_id=1,
        id="p1",
        slug="p1",
        active=True,
        brand="Samsung",
        name="Galaxy",
        model="S25",
        capacity="256 GB",
        color="",
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
        promotion=None,
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
    base.update(kwargs)
    return Product(**base)


class FakeSource:
    def __init__(self, products: list[Product]):
        self._products = products

    async def get_products(self, *, active_only: bool = True):
        return self._products if active_only else self._products


def test_distance_to_range():
    assert _distance_to_range(350, price_min=400, price_max=700) == 50
    assert _distance_to_range(900, price_min=400, price_max=700) == 200
    assert _distance_to_range(500, price_min=400, price_max=700) == 0


def test_recommend_exact_match(monkeypatch):
    products = [
        _product(id="cheap", price_financed_total=399, price=399, price_libre=499),
        _product(id="mid", price_financed_total=799, price=799, price_libre=999),
    ]
    monkeypatch.setattr("app.services.recommend.product_source", FakeSource(products))
    result = asyncio.run(
        recommend_products("value", None, price_min=350, price_max=450, purchase_mode="cuotas")
    )
    assert isinstance(result, RecommendResult)
    assert result.match_type == "exact"
    assert [p.id for p in result.products] == ["cheap"]


def test_recommend_alternatives_when_no_exact(monkeypatch):
    products = [
        _product(id="below", price_financed_total=350, price=350, price_libre=450),
        _product(id="above", price_financed_total=900, price=900, price_libre=1100),
    ]
    monkeypatch.setattr("app.services.recommend.product_source", FakeSource(products))
    result = asyncio.run(
        recommend_products("value", None, price_min=400, price_max=700, purchase_mode="cuotas")
    )
    assert result.match_type == "alternatives"
    assert result.products[0].id == "below"


def test_recommend_libre_mode(monkeypatch):
    products = [
        _product(id="libre-ok", price_libre=450, price_financed_total=350, price=350),
        _product(id="libre-high", price_libre=950, price_financed_total=799, price=799),
    ]
    monkeypatch.setattr("app.services.recommend.product_source", FakeSource(products))
    result = asyncio.run(
        recommend_products("value", None, price_min=400, price_max=500, purchase_mode="libre")
    )
    assert result.match_type == "exact"
    assert result.products[0].id == "libre-ok"
