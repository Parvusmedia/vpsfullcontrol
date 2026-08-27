import json
from pathlib import Path

from app.services.product_service import parse_product
from scripts.migrate_products import build_migration_payload, build_report_row


def _product_row(**fields) -> dict:
    base = {
        "Id": 1,
        "id": "iphone-16-128",
        "slug": "iphone-16-128",
        "active": True,
        "brand": "Apple",
        "name": "iPhone 16",
        "model": "iPhone 16",
        "capacity": "128 GB",
        "price": 671,
        "previous_price": 851,
        "monthly_price": 14,
        "months": 48,
        "original_price": 851,
    }
    base.update(fields)
    return base


def test_build_migration_payload_from_legacy():
    product = parse_product(_product_row())
    payload, note = build_migration_payload(product)
    assert payload["price_libre"] == 851
    assert payload["price_financed_total"] == 671
    assert "libre_from_original_price" in note


def test_build_migration_payload_skips_existing_canonical():
    product = parse_product(_product_row(price_libre=900, price_financed_total=700))
    payload, note = build_migration_payload(product)
    assert payload == {}
    assert note == "noop"


def test_build_migration_payload_ambiguous_original_price():
    product = parse_product(
        _product_row(original_price=900, previous_price=800, price=700, price_libre=None)
    )
    payload, note = build_migration_payload(product)
    assert "price_libre" not in payload
    assert "ambiguous_libre" in note
    assert payload.get("price_financed_total") == 700


def test_seed_migration_report_snapshot():
    seed_path = Path(__file__).resolve().parents[1] / "data" / "seed-products.json"
    rows = json.loads(seed_path.read_text())
    report = []
    for row in rows:
        product = parse_product({"Id": row["id"], **row})
        _, note = build_migration_payload(product)
        report.append(build_report_row(product, note))
    assert len(report) == 8
    assert all("libre_from_" in r["note"] or r["note"] == "noop" for r in report)
