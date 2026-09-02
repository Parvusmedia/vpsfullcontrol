import asyncio
from unittest.mock import AsyncMock, patch

from app.services.change_detection import (
    ALERT_TYPE_LABELS,
    alert_type_label,
    create_alert,
    deactivate_alert,
    user_has_product_alert,
)
from app.services.nocodb import NocoDBClient


def test_alert_type_label():
    assert alert_type_label("monthly_price_drop") == "Si baja la cuota"
    assert alert_type_label("price_drop") == "Si baja de precio"
    assert alert_type_label("unknown") == "unknown"


def test_alert_type_labels_complete():
    assert len(ALERT_TYPE_LABELS) == 3


def test_user_has_product_alert_true():
    with patch(
        "app.services.change_detection.get_user_alerts",
        new=AsyncMock(return_value=[{"product_id": "galaxy-s25", "_record_id": 1}]),
    ):
        assert asyncio.run(user_has_product_alert(123, "galaxy-s25")) is True


def test_user_has_product_alert_false():
    with patch(
        "app.services.change_detection.get_user_alerts",
        new=AsyncMock(return_value=[{"product_id": "galaxy-s25", "_record_id": 1}]),
    ):
        assert asyncio.run(user_has_product_alert(123, "iphone-16")) is False


def test_create_alert_blocks_duplicate():
    with (
        patch(
            "app.services.change_detection.user_has_product_alert",
            new=AsyncMock(return_value=True),
        ),
        patch("app.services.change_detection.nocodb.create_record", new=AsyncMock()) as mock_create,
    ):
        result = asyncio.run(
            create_alert({"telegram_user_id": "1", "product_id": "galaxy-s25", "alert_type": "price_drop"})
        )
        assert result is None
        mock_create.assert_not_called()


def test_create_alert_allows_new_product():
    with (
        patch(
            "app.services.change_detection.user_has_product_alert",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.services.change_detection.nocodb.create_record",
            new=AsyncMock(return_value={"Id": 9}),
        ) as mock_create,
        patch("app.services.change_detection.get_settings") as mock_settings,
    ):
        mock_settings.return_value.nocodb_alerts_table_id = "alerts-table"
        result = asyncio.run(
            create_alert({"telegram_user_id": "1", "product_id": "iphone-16", "alert_type": "price_drop"})
        )
        assert result == {"Id": 9}
        mock_create.assert_awaited_once()


def test_deactivate_alert_updates_active_flag():
    with (
        patch(
            "app.services.change_detection.get_user_alerts",
            new=AsyncMock(
                return_value=[
                    {
                        "_record_id": 5,
                        "product_id": "galaxy-s25",
                        "alert_type": "price_drop",
                    }
                ]
            ),
        ),
        patch(
            "app.services.change_detection.update_alert",
            new=AsyncMock(return_value={"Id": 5}),
        ) as mock_update,
        patch("app.services.change_detection.log_event", new=AsyncMock()),
    ):
        ok = asyncio.run(deactivate_alert(5, 123))
        assert ok is True
        mock_update.assert_awaited_once_with(5, {"active": False})


def test_deactivate_alert_rejects_foreign_record():
    with patch(
        "app.services.change_detection.get_user_alerts",
        new=AsyncMock(return_value=[{"_record_id": 5, "product_id": "galaxy-s25"}]),
    ):
        assert asyncio.run(deactivate_alert(99, 123)) is False


def test_nocodb_update_record_uses_bulk_patch():
    client = NocoDBClient()

    async def _run():
        with patch.object(client, "request", new=AsyncMock(return_value=[{"Id": 3}])) as mock_request:
            result = await client.update_record("tbl1", 3, {"active": False})
            mock_request.assert_awaited_once_with(
                "PATCH",
                "/api/v2/tables/tbl1/records",
                {"Id": 3, "active": False},
            )
            assert result == {"Id": 3}

    asyncio.run(_run())
