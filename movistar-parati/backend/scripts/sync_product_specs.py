#!/usr/bin/env python3
"""Sincroniza specs técnicas (mAh, MP, procesador) desde product-specs.json a NocoDB."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.nocodb import nocodb
from app.services.product_fields import sanitize_product_fields
from app.services.product_service import parse_product

ROOT = Path(__file__).resolve().parents[1]
SPECS_FILE = ROOT / "data" / "product-specs.json"

SPEC_FIELDS = (
    "battery_mah",
    "fast_charge_w",
    "camera_main_mp",
    "processor",
    "spec_battery",
    "spec_camera",
    "spec_work",
    "spec_premium",
    "spec_value",
)


async def main() -> None:
    settings = get_settings()
    table_id = settings.nocodb_products_table_id
    if not table_id or not settings.nocodb_api_token:
        raise SystemExit("NocoDB not configured (table id / API token)")

    specs_map: dict[str, dict] = json.loads(SPECS_FILE.read_text())
    rows = await nocodb.list_records(table_id, limit=500)
    updated = skipped = 0

    for row in rows:
        product = parse_product(row)
        if not product.record_id:
            continue
        specs = specs_map.get(product.id)
        if not specs:
            skipped += 1
            print(f"skip (no specs): {product.id}")
            continue

        payload = sanitize_product_fields({k: specs[k] for k in SPEC_FIELDS if k in specs})
        if not payload:
            skipped += 1
            continue

        current = {k: getattr(product, k) for k in SPEC_FIELDS}
        if all(current.get(k) == payload.get(k) for k in payload):
            print(f"unchanged: {product.id}")
            continue

        await nocodb.update_record(table_id, product.record_id, payload)
        updated += 1
        print(f"updated: {product.id} -> {', '.join(f'{k}={payload[k]}' for k in payload)}")

    print(f"Done. updated={updated} skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())
