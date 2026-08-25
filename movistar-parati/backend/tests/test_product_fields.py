from app.services.product_fields import panel_payload_to_fields, sanitize_product_fields


def test_sanitize_monthly_price_as_int():
    out = sanitize_product_fields({"monthly_price": 13.99, "active": True})
    assert out["monthly_price"] == 14
    assert out["active"] is True


def test_panel_payload_filters_unknown_fields():
    out = panel_payload_to_fields({"monthly_price": 10, "hacker": "x", "active": "true"})
    assert out == {"monthly_price": 10, "active": True}


def test_panel_payload_omits_empty_strings():
    out = panel_payload_to_fields({"promotion": "", "gift": "Buds"})
    assert "promotion" not in out
    assert out["gift"] == "Buds"
