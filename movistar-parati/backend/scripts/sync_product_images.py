#!/usr/bin/env python3
"""Actualiza image_url en NocoDB con las fotos locales de /static/product-images/."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.nocodb import nocodb
from app.services.product_image import clear_image_cache
from app.services.product_service import parse_product

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / "data" / "product-image-map.json"
IMAGES_DIR = ROOT / "static" / "product-images"


def image_public_url(filename: str) -> str:
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}/static/product-images/{filename}"


async def main() -> None:
    settings = get_settings()
    table_id = settings.nocodb_products_table_id
    if not table_id or not settings.nocodb_api_token:
        raise SystemExit("NocoDB not configured (table id / API token)")

    image_map: dict[str, str] = json.loads(MAP_FILE.read_text())
    missing_files = [f for f in image_map.values() if not (IMAGES_DIR / f).is_file()]
    if missing_files:
        raise SystemExit(f"Missing image files: {', '.join(missing_files)}")

    rows = await nocodb.list_records(table_id, limit=500)
    updated = skipped = 0

    for row in rows:
        product = parse_product(row)
        if not product.record_id:
            continue
        filename = image_map.get(product.id)
        if not filename:
            skipped += 1
            print(f"skip (no map): {product.id}")
            continue
        url = image_public_url(filename)
        if product.image_url == url:
            print(f"unchanged: {product.id}")
            continue
        await nocodb.update_record(table_id, product.record_id, {"image_url": url})
        updated += 1
        print(f"updated: {product.id} -> {filename}")

    clear_image_cache()
    print(f"Done. updated={updated} skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())
