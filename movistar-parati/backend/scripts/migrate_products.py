#!/usr/bin/env python3
"""Provision schema and migrate canonical price fields in NocoDB (idempotent)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.nocodb import nocodb
from app.services.product_fields import sanitize_product_fields
from app.services.product_service import parse_product

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class MigrationStats:
    migrated: int = 0
    skipped: int = 0
    ambiguous: list[str] = field(default_factory=list)
    report_rows: list[dict] = field(default_factory=list)


def _is_empty(value) -> bool:
    return value is None or value == ""


def _derive_price_libre(product) -> tuple[int | None, str]:
    if not _is_empty(product.price_libre):
        return None, "already_set"
    if not _is_empty(product.original_price):
        if _is_empty(product.previous_price) or product.previous_price == product.original_price:
            return int(round(product.original_price)), "original_price"
        if (
            product.price
            and product.original_price > product.price
            and product.saving is not None
            and abs((product.original_price - product.price) - product.saving) < 2
        ):
            return int(round(product.original_price)), "original_price_saving_pattern"
        return None, "ambiguous_original_price"
    if not _is_empty(product.previous_price):
        return int(round(product.previous_price)), "previous_price"
    if not _is_empty(product.price):
        return int(round(product.price)), "price_fallback"
    return None, "missing"


def _derive_price_financed(product) -> tuple[int | None, str]:
    if not _is_empty(product.price_financed_total):
        return None, "already_set"
    if not _is_empty(product.price):
        return int(round(product.price)), "price"
    return None, "missing"


def build_migration_payload(product) -> tuple[dict, str]:
    payload: dict[str, int] = {}
    notes: list[str] = []

    libre, libre_source = _derive_price_libre(product)
    if libre_source == "ambiguous_original_price":
        notes.append("ambiguous_libre")
    elif libre is not None:
        payload["price_libre"] = libre
        notes.append(f"libre_from_{libre_source}")

    financed, financed_source = _derive_price_financed(product)
    if financed is not None:
        payload["price_financed_total"] = financed
        notes.append(f"financed_from_{financed_source}")
    elif financed_source == "missing":
        notes.append("missing_financed")

    return sanitize_product_fields(payload), ",".join(notes) or "noop"


def build_report_row(product, note: str) -> dict:
    return {
        "id": product.id,
        "name": product.display_name,
        "price": product.price,
        "original_price": product.original_price,
        "previous_price": product.previous_price,
        "price_libre": product.price_libre,
        "price_financed_total": product.price_financed_total,
        "monthly_price": product.monthly_price,
        "months": product.months,
        "note": note,
    }


def ensure_schema() -> None:
    from scripts import provision_nocodb as prov

    base_id = get_settings().nocodb_base_id or prov._base_id_from_env()
    tables = prov.req("GET", f"/api/v2/meta/bases/{base_id}/tables").get("list", [])
    by_title = {t["title"]: t["id"] for t in tables}
    table_id = by_title.get("movistar_products")
    if not table_id:
        raise SystemExit("movistar_products table not found; run provision_nocodb.py first")
    prov.ensure_table_columns(table_id, prov.TABLES["movistar_products"]["columns"])
    print("Schema check complete for movistar_products")


async def migrate_data(*, dry_run: bool = False, report_path: Path | None = None) -> MigrationStats:
    settings = get_settings()
    table_id = settings.nocodb_products_table_id
    if not table_id or not settings.nocodb_api_token:
        raise SystemExit("NocoDB not configured (table id / API token)")

    rows = await nocodb.list_records(table_id, limit=500)
    stats = MigrationStats()

    for row in rows:
        product = parse_product(row)
        if not product.record_id:
            continue
        payload, note = build_migration_payload(product)
        stats.report_rows.append(build_report_row(product, note))

        if "ambiguous_libre" in note:
            stats.ambiguous.append(product.id)
        if not payload:
            stats.skipped += 1
            print(f"skip: {product.id} ({note})")
            continue

        if dry_run:
            stats.migrated += 1
            print(f"would_migrate: {product.id} -> {payload} ({note})")
            continue

        await nocodb.update_record(table_id, product.record_id, payload)
        stats.migrated += 1
        print(f"migrated: {product.id} -> {payload} ({note})")

    if report_path:
        report_path.write_text(json.dumps(stats.report_rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report written to {report_path}")

    print(
        f"Done. migrated={stats.migrated} skipped={stats.skipped} "
        f"ambiguous={len(stats.ambiguous)} dry_run={dry_run}"
    )
    if stats.ambiguous:
        print("Ambiguous libre mapping:", ", ".join(stats.ambiguous))
    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Provision schema and migrate canonical product prices.")
    parser.add_argument("--schema-only", action="store_true", help="Only ensure NocoDB columns exist")
    parser.add_argument("--dry-run", action="store_true", help="Show migrations without writing")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write JSON report of all products (default: backend/data/price-migration-report.json)",
    )
    args = parser.parse_args()

    ensure_schema()
    if args.schema_only:
        return

    report_path = args.report
    if report_path is None and not args.dry_run:
        report_path = ROOT / "data" / "price-migration-report.json"
    await migrate_data(dry_run=args.dry_run, report_path=report_path)


if __name__ == "__main__":
    asyncio.run(main())
