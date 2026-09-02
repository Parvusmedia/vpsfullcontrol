"""Helpers for reading/writing product fields in NocoDB."""

from __future__ import annotations

from typing import Any

from app.services.price_formatting import round_money, round_monthly

INT_FIELDS = {
    "price",
    "previous_price",
    "months",
    "original_price",
    "price_libre",
    "price_financed_total",
    "saving",
    "discount_percentage",
    "camera_score",
    "battery_score",
    "business_score",
    "premium_score",
    "value_score",
    "battery_mah",
    "fast_charge_w",
    "camera_main_mp",
}

DECIMAL_FIELDS = {
    "monthly_price",
    "previous_monthly_price",
}

BOOL_FIELDS = {"active", "is_new", "featured"}

TEXT_FIELDS = {
    "id",
    "slug",
    "brand",
    "name",
    "model",
    "capacity",
    "color",
    "category",
    "promotion",
    "gift",
    "image_url",
    "product_url",
    "processor",
    "spec_battery",
    "spec_camera",
    "spec_work",
    "spec_premium",
    "spec_value",
}

PANEL_EDITABLE_FIELDS = {
    "monthly_price",
    "previous_monthly_price",
    "months",
    "price_libre",
    "price_financed_total",
    "active",
    "featured",
    "is_new",
    "promotion",
    "gift",
}


def sanitize_product_fields(fields: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in INT_FIELDS | DECIMAL_FIELDS | BOOL_FIELDS | TEXT_FIELDS:
            continue
        if value is None or value == "":
            continue
        if key in BOOL_FIELDS:
            if isinstance(value, bool):
                clean[key] = value
            elif isinstance(value, str):
                clean[key] = value.lower() in {"1", "true", "yes", "si", "sí", "on"}
            else:
                clean[key] = bool(value)
        elif key in DECIMAL_FIELDS:
            rounded = round_monthly(value)
            if rounded is not None:
                clean[key] = rounded
        elif key in INT_FIELDS:
            clean[key] = int(round(float(value)))
        else:
            clean[key] = str(value)
    return clean


def panel_payload_to_fields(payload: dict[str, Any]) -> dict[str, Any]:
    fields = sanitize_product_fields({k: v for k, v in payload.items() if k in PANEL_EDITABLE_FIELDS})
    if "price_financed_total" in fields:
        fields["price"] = fields["price_financed_total"]
    if "price_libre" in fields:
        fields["original_price"] = fields["price_libre"]
    return fields
