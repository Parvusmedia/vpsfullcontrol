#!/usr/bin/env python3
"""Sincroniza el catálogo demo héroe en NocoDB (8 productos activos)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.config import get_settings
from app.services.nocodb import nocodb
from app.services.product_service import parse_product

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed-products.json"
HERO_IDS = {p["id"] for p in json.loads(SEED.read_text())}

_INT_FIELDS = {
    "price", "previous_price", "monthly_price", "previous_monthly_price",
    "months", "original_price", "saving", "discount_percentage",
    "camera_score", "battery_score", "business_score", "premium_score", "value_score",
}


def _sanitize_fields(fields: dict) -> dict:
    clean: dict = {}
    for key, value in fields.items():
        if value is None:
            continue
        if key in _INT_FIELDS and isinstance(value, (int, float)):
            clean[key] = int(round(value))
        else:
            clean[key] = value
    return clean


async def main() -> None:
    settings = get_settings()
    table_id = settings.nocodb_products_table_id
    if not table_id:
        raise SystemExit("NOCODB_PRODUCTS_TABLE_ID not configured")

    seed_by_id = {p["id"]: p for p in json.loads(SEED.read_text())}
    rows = await nocodb.list_records(table_id, limit=500)
    updated = deactivated = 0

    for row in rows:
        product = parse_product(row)
        record_id = product.record_id
        if not record_id:
            continue
        if product.id in HERO_IDS:
            fields = _sanitize_fields({k: v for k, v in seed_by_id[product.id].items() if k != "id"})
            fields["active"] = True
            await nocodb.update_record(table_id, record_id, fields)
            updated += 1
            print(f"updated: {product.id}")
        elif product.active:
            await nocodb.update_record(table_id, record_id, {"active": False})
            deactivated += 1
            print(f"deactivated: {product.id}")

    print(f"Done. updated={updated} deactivated={deactivated}")


if __name__ == "__main__":
    asyncio.run(main())
