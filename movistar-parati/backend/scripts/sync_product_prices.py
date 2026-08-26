#!/usr/bin/env python3
"""Migra y sincroniza price_libre / price_financed_total en NocoDB."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.nocodb import nocodb
from app.services.product_fields import sanitize_product_fields
from app.services.product_service import parse_product


def _derive_prices(product) -> dict[str, int]:
    price_libre = product.price_libre
    if price_libre is None:
        price_libre = product.original_price or product.previous_price or product.price

    price_financed = product.price_financed_total
    if price_financed is None:
        price_financed = product.price

    payload: dict[str, int] = {}
    if price_libre is not None:
        payload["price_libre"] = int(round(price_libre))
    if price_financed is not None:
        payload["price_financed_total"] = int(round(price_financed))
    return payload


async def main() -> None:
    settings = get_settings()
    table_id = settings.nocodb_products_table_id
    if not table_id or not settings.nocodb_api_token:
        raise SystemExit("NocoDB not configured (table id / API token)")

    rows = await nocodb.list_records(table_id, limit=500)
    updated = skipped = 0

    for row in rows:
        product = parse_product(row)
        if not product.record_id:
            continue
        payload = sanitize_product_fields(_derive_prices(product))
        if not payload:
            skipped += 1
            continue

        current_libre = product.price_libre or product.original_price or product.previous_price
        current_financed = product.price_financed_total or product.price
        if (
            payload.get("price_libre") == (int(current_libre) if current_libre else None)
            and payload.get("price_financed_total") == (int(current_financed) if current_financed else None)
            and product.price_libre is not None
            and product.price_financed_total is not None
        ):
            print(f"unchanged: {product.id}")
            continue

        await nocodb.update_record(table_id, product.record_id, payload)
        updated += 1
        print(
            f"updated: {product.id} -> "
            f"libre={payload.get('price_libre')} financed={payload.get('price_financed_total')}"
        )

    print(f"Done. updated={updated} skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())
