import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.change_detection import _format_price_drop_message
from app.services.demo_scenarios import activate_black_friday, open_iphone_preorder
from app.services.product_service import Product


def _product(product_id: str, monthly: float) -> Product:
    return Product(
        record_id=1,
        id=product_id,
        slug=product_id,
        active=True,
        brand="Google",
        name="Pixel 11",
        model="Pixel 11",
        capacity="256 GB",
        color="Negro",
        category="smartphone",
        price=799,
        previous_price=None,
        monthly_price=monthly,
        previous_monthly_price=None,
        months=48,
        original_price=None,
        saving=None,
        discount_percentage=None,
        promotion=None,
        gift=None,
        image_url=None,
        product_url="https://example.com",
        is_new=False,
        featured=False,
        deal_score=None,
        camera_score=8,
        battery_score=7,
        business_score=6,
        premium_score=7,
        value_score=8,
    )


def test_price_drop_message_includes_cta_and_saving():
    product = _product("pixel-11-256", 8)
    product.promotion = "Black Friday"
    text = _format_price_drop_message(product, 12, 8)
    assert "Tu aviso se ha activado" in text
    assert "4.00" in text
    assert "aprovecha" in text.lower()
    assert "Black Friday" in text


def test_activate_black_friday_updates_products():
    product = _product("galaxy-s25", 12)

    async def _run():
        with (
            patch(
                "app.services.demo_scenarios.product_source.get_product",
                new=AsyncMock(side_effect=lambda pid: product if pid == "galaxy-s25" else None),
            ),
            patch(
                "app.services.demo_scenarios.product_source.update_product",
                new=AsyncMock(return_value=product),
            ) as mock_update,
            patch("app.services.demo_scenarios.poll_catalogue_changes", new=AsyncMock(return_value={"changes": 1})),
            patch("app.services.demo_scenarios.log_event", new=AsyncMock()),
        ):
            result = await activate_black_friday()
            assert "galaxy-s25" in result["products"]
            assert mock_update.await_count >= 1

    asyncio.run(_run())


def test_open_iphone_preorder():
    product = _product("iphone-16-pro", 28)
    product.id = "iphone-16-pro"

    async def _run():
        with (
            patch(
                "app.services.demo_scenarios.product_source.get_product",
                new=AsyncMock(return_value=product),
            ),
            patch(
                "app.services.demo_scenarios.product_source.update_product",
                new=AsyncMock(return_value=product),
            ) as mock_update,
            patch("app.services.demo_scenarios.poll_catalogue_changes", new=AsyncMock(return_value={})),
            patch("app.services.demo_scenarios.log_event", new=AsyncMock()),
        ):
            result = await open_iphone_preorder()
            assert result["products"] == ["iphone-16-pro"]
            fields = mock_update.await_args.args[1]
            assert fields["is_new"] is True
            assert "Preventa" in fields["promotion"]

    asyncio.run(_run())
