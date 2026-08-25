#!/usr/bin/env python3
"""Provision NocoDB tables for Movistar Para Ti."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

BASE_URL = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com").rstrip("/")
BASE_ID = os.environ.get("NOCODB_BASE_ID", "pzyr6ncnc9dk4h0")
TOKEN = os.environ.get("NOCODB_API_TOKEN", "")

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed-products.json"
ENV_OUT = ROOT / ".env.provisioned"


def load_token() -> str:
    if TOKEN:
        return TOKEN
    for path in (
        ROOT / ".env",
        Path("/opt/apps/movistar-parati/backend/.env"),
        Path("/opt/apps/fly456bot/.env"),
    ):
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith("NOCODB_API_TOKEN="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit("NOCODB_API_TOKEN not set")


def req(method: str, path: str, body: dict | None = None) -> dict:
    token = load_token()
    base_id = BASE_ID or os.environ.get("NOCODB_BASE_ID") or _base_id_from_env()
    url = f"{BASE_URL}{path}"
    r = httpx.request(method, url, headers={"xc-token": token, "Content-Type": "application/json"}, json=body, timeout=60)
    if r.status_code >= 400:
        raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else {}


def _base_id_from_env() -> str:
    for path in (ROOT / ".env", Path("/opt/apps/fly456bot/.env")):
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith("NOCODB_BASE_ID="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit("NOCODB_BASE_ID not set")


def col_text(name: str, title: str | None = None) -> dict:
    return {"column_name": name, "title": title or name, "uidt": "SingleLineText"}


def col_long(name: str, title: str | None = None) -> dict:
    return {"column_name": name, "title": title or name, "uidt": "LongText"}


def col_num(name: str, title: str | None = None) -> dict:
    return {"column_name": name, "title": title or name, "uidt": "Number"}


def col_bool(name: str, title: str | None = None) -> dict:
    return {"column_name": name, "title": title or name, "uidt": "Checkbox"}


TABLES = {
    "movistar_products": {
        "title": "movistar_products",
        "table_name": "movistar_products",
        "columns": [
            col_text("id"), col_text("slug"), col_bool("active"),
            col_text("brand"), col_text("name"), col_text("model"), col_text("capacity"), col_text("color"),
            col_text("category"),
            col_num("price"), col_num("previous_price"),
            col_num("monthly_price"), col_num("previous_monthly_price"), col_num("months"),
            col_num("original_price"), col_num("saving"), col_num("discount_percentage"),
            col_text("promotion"), col_text("gift"),
            col_text("image_url"), col_text("product_url"),
            col_bool("is_new"), col_bool("featured"), col_num("deal_score"),
            col_num("camera_score"), col_num("battery_score"), col_num("business_score"),
            col_num("premium_score"), col_num("value_score"),
        ],
    },
    "movistar_alerts": {
        "title": "movistar_alerts",
        "table_name": "movistar_alerts",
        "columns": [
            col_text("telegram_user_id"), col_text("product_id"), col_text("product_name"),
            col_text("alert_type"), col_num("target_price"), col_num("target_monthly_price"),
            col_bool("active"), col_text("last_notified_signature"), col_text("created_at"), col_text("last_triggered_at"),
        ],
    },
    "movistar_events": {
        "title": "movistar_events",
        "table_name": "movistar_events",
        "columns": [
            col_text("product_id"), col_text("event_type"), col_text("old_value"), col_text("new_value"),
            col_long("metadata"), col_text("created_at"),
        ],
    },
}


def main() -> None:
    global BASE_ID
    BASE_ID = BASE_ID or _base_id_from_env()
    existing = {t["title"]: t["id"] for t in req("GET", f"/api/v2/meta/bases/{BASE_ID}/tables").get("list", [])}
    ids: dict[str, str] = {}

    for key, definition in TABLES.items():
        if definition["title"] in existing:
            ids[key] = existing[definition["title"]]
            print(f"exists: {definition['title']} -> {ids[key]}")
        else:
            created = req("POST", f"/api/v2/meta/bases/{BASE_ID}/tables", definition)
            ids[key] = created["id"]
            print(f"created: {definition['title']} -> {ids[key]}")

    if SEED.exists() and ids.get("movistar_products"):
        products = json.loads(SEED.read_text())
        current = req("GET", f"/api/v2/tables/{ids['movistar_products']}/records?limit=1").get("list", [])
        if not current:
            for row in products:
                req("POST", f"/api/v2/tables/{ids['movistar_products']}/records", row)
            print(f"seeded {len(products)} products")
        else:
            print("products already seeded, skip")

    env_lines = [
        f"NOCODB_BASE_URL={BASE_URL}",
        f"NOCODB_BASE_ID={BASE_ID}",
        f"NOCODB_PRODUCTS_TABLE_ID={ids['movistar_products']}",
        f"NOCODB_ALERTS_TABLE_ID={ids['movistar_alerts']}",
        f"NOCODB_EVENTS_TABLE_ID={ids['movistar_events']}",
    ]
    ENV_OUT.write_text("\n".join(env_lines) + "\n")
    print("Wrote", ENV_OUT)
    print("\n".join(env_lines))


if __name__ == "__main__":
    main()
