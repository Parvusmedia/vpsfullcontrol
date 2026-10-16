#!/usr/bin/env python3
"""Export Noco meta_leads rows as CSV rows for Google Sheets (meta_Digitanimal* columns)."""
from __future__ import annotations

import csv
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from digitanimal_noco_record import record_from_make_bundle

TABLE = "mieilgjtcw04jjr"
BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com")
HEADERS = [
    "date",
    "source",
    "campaign",
    "adset",
    "ad",
    "campaignid",
    "adsetid",
    "adid",
    "formid",
    "leadid",
    "name",
    "email",
    "phone",
    "province",
    "cant-animales",
    "tipo_animal",
    "custom4",
    "custom5",
    "custom6",
]


def _token() -> str:
    t = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not t:
        raise SystemExit("NOCO_TOKEN required")
    return t


def _fetch(token: str, scenario_id: str | None, min_id: int | None) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        url = f"{BASE}/api/v2/tables/{TABLE}/records?limit=100&offset={offset}&sort=Id"
        req = urllib.request.Request(url, headers={"xc-token": token})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("list") or []
        if not batch:
            break
        for r in batch:
            if min_id and r.get("Id", 0) < min_id:
                continue
            if scenario_id and str(r.get("make_scenario_id")) != scenario_id:
                continue
            rows.append(r)
        if len(batch) < 100:
            break
        offset += len(batch)
    return rows


def _sheet_row(row: dict) -> dict[str, str]:
    mp = row.get("meta_payload_json") or {}
    sid = str(row.get("make_scenario_id") or "")
    rec = record_from_make_bundle(mp if isinstance(mp, dict) else {}, sid)
    return {
        "date": row.get("date_created") or "",
        "source": row.get("lead_source") or "",
        "campaign": row.get("campaign_name") or "",
        "adset": row.get("adset_name") or "",
        "ad": row.get("ad_name") or "",
        "campaignid": row.get("campaign_id") or "",
        "adsetid": row.get("adgroup_id") or "",
        "adid": row.get("ad_id") or "",
        "formid": row.get("form_id") or "",
        "leadid": row.get("leadgen_id") or "",
        "name": rec.get("full_name") or row.get("full_name") or "",
        "email": rec.get("email") or row.get("email") or "",
        "phone": rec.get("phone") or row.get("phone") or "",
        "province": rec.get("province") or row.get("province") or "",
        "cant-animales": rec.get("herd_count") or row.get("herd_count") or "",
        "tipo_animal": rec.get("livestock_type") or row.get("livestock_type") or "",
        "custom4": row.get("home_listing") or "",
        "custom5": row.get("partner_name") or "",
        "custom6": row.get("retailer_item_id") or "",
    }


def main() -> None:
    scenario = None
    min_id = None
    out_path = "/opt/cursor/artifacts/digitanimal_it_sheets_backfill.csv"
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--scenario":
            scenario = args[i + 1]
            i += 2
        elif args[i] == "--min-id":
            min_id = int(args[i + 1])
            i += 2
        elif args[i] == "--out":
            out_path = args[i + 1]
            i += 2
        else:
            raise SystemExit(f"unknown arg {args[i]}")
    token = _token()
    rows = _fetch(token, scenario, min_id)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow(_sheet_row(r))
    print(json.dumps({"rows": len(rows), "out": out_path}))


if __name__ == "__main__":
    main()
