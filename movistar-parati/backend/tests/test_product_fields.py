from app.services.product_fields import panel_payload_to_fields, sanitize_product_fields


def test_sanitize_monthly_price_keeps_decimals():
    out = sanitize_product_fields({"monthly_price": 8.505, "previous_monthly_price": 4.5, "active": True})
    assert out["monthly_price"] == 8.51
    assert out["previous_monthly_price"] == 4.5
    assert out["active"] is True


def test_panel_payload_mirrors_legacy_prices():
    out = panel_payload_to_fields(
        {
            "price_libre": 851,
            "price_financed_total": 671,
            "monthly_price": 8.5,
            "active": "true",
        }
    )
    assert out["price"] == 671
    assert out["original_price"] == 851
    assert out["monthly_price"] == 8.5


def test_panel_payload_filters_unknown_fields():
    out = panel_payload_to_fields({"monthly_price": 10, "hacker": "x", "active": "true"})
    assert out == {"monthly_price": 10, "active": True}


def test_panel_payload_omits_empty_strings():
    out = panel_payload_to_fields({"promotion": "", "gift": "Buds"})
    assert "promotion" not in out
    assert out["gift"] == "Buds"
