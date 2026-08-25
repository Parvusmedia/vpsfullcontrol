#!/usr/bin/env python3
"""Migrate movistar_* tables to another NocoDB base."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

# Allow: OLD_BASE_ID, NEW_BASE_ID, OLD_*_TABLE_ID env overrides
BASE_URL = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com").rstrip("/")
OLD_BASE_ID = os.environ.get("OLD_BASE_ID", "pgva30uz3lan434")
NEW_BASE_ID = os.environ.get("NEW_BASE_ID", "pzyr6ncnc9dk4h0")
OLD_TABLES = {
    "movistar_products": os.environ.get("OLD_PRODUCTS_TABLE_ID", "m1w7d2yrckbhqyy"),
    "movistar_alerts": os.environ.get("OLD_ALERTS_TABLE_ID", "mv74470alllp2fv"),
    "movistar_events": os.environ.get("OLD_EVENTS_TABLE_ID", "m2fc6453wmhk6l2"),
}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.provision_nocodb import TABLES, load_token, req  # noqa: E402


def list_all_records(table_id: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        data = req("GET", f"/api/v2/tables/{table_id}/records?limit=100&offset={offset}")
        batch = data.get("list", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
    return rows


def strip_meta(row: dict) -> dict:
  out = {}
  skip = {"Id", "id", "CreatedAt", "UpdatedAt", "nc_order", "CreatedBy", "UpdatedBy"}
  for k, v in row.items():
    if k in skip or k.startswith("nc_"):
      continue
    out[k] = v
  return out


def main() -> None:
    global req
    token = load_token()

    def _req(method: str, path: str, body: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        r = httpx.request(
            method, url, headers={"xc-token": token, "Content-Type": "application/json"}, json=body, timeout=60
        )
        if r.status_code >= 400:
            raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text}")
        return r.json() if r.content else {}

    req = _req

    # Export from old base
    exported: dict[str, list[dict]] = {}
    for name, tid in OLD_TABLES.items():
        exported[name] = [strip_meta(r) for r in list_all_records(tid)]
        print(f"exported {name}: {len(exported[name])} rows")

    # Create tables in new base
    existing = {t["title"]: t["id"] for t in req("GET", f"/api/v2/meta/bases/{NEW_BASE_ID}/tables").get("list", [])}
    new_ids: dict[str, str] = {}
    for key, definition in TABLES.items():
        if definition["title"] in existing:
            new_ids[key] = existing[definition["title"]]
            print(f"exists in new base: {key} -> {new_ids[key]}")
        else:
            created = req("POST", f"/api/v2/meta/bases/{NEW_BASE_ID}/tables", definition)
            new_ids[key] = created["id"]
            print(f"created in new base: {key} -> {new_ids[key]}")

    # Import rows (skip if products already populated)
    for name, rows in exported.items():
        tid = new_ids[name]
        current = req("GET", f"/api/v2/tables/{tid}/records?limit=1").get("list", [])
        if current:
            print(f"skip import {name}: already has data")
            continue
        for row in rows:
            req("POST", f"/api/v2/tables/{tid}/records", row)
        print(f"imported {name}: {len(rows)} rows")

    out = ROOT / ".env.provisioned"
    lines = [
        f"NOCODB_BASE_URL={BASE_URL}",
        f"NOCODB_BASE_ID={NEW_BASE_ID}",
        f"NOCODB_PRODUCTS_TABLE_ID={new_ids['movistar_products']}",
        f"NOCODB_ALERTS_TABLE_ID={new_ids['movistar_alerts']}",
        f"NOCODB_EVENTS_TABLE_ID={new_ids['movistar_events']}",
    ]
    out.write_text("\n".join(lines) + "\n")
    print("--- NEW CONFIG ---")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
