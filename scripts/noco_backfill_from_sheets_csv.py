#!/usr/bin/env python3
"""Backfill or upsert Noco meta_leads from exported Google Sheet CSV (no Make replay).

Export in Google Sheets: File → Download → CSV for tabs meta_DigitanimalES / FR / IT.
Each file is processed with the matching make_scenario_id.

Requires NOCO_TOKEN or NOCODB_API_TOKEN.
"""
from __future__ import annotations

from typing import Any

import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from digitanimal_noco_record import record_from_sheets_row

TABLE = "mieilgjtcw04jjr"
BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com")


def _token() -> str:
    t = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not t:
        raise SystemExit("NOCO_TOKEN or NOCODB_API_TOKEN required")
    return t


def _find_by_leadgen(token: str, leadgen_id: str) -> dict | None:
    where = urllib.parse.quote(f"(leadgen_id,eq,{leadgen_id})")
    url = f"{BASE}/api/v2/tables/{TABLE}/records?where={where}&limit=1"
    req = urllib.request.Request(url, headers={"xc-token": token, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    rows = data.get("list") or []
    return rows[0] if rows else None


def _upsert(token: str, record: dict[str, Any]) -> str:
    leadgen = record.get("leadgen_id")
    if not leadgen:
        return "skip_no_leadgen"
    existing = _find_by_leadgen(token, str(leadgen))
    clean = {k: v for k, v in record.items() if v is not None and v != ""}
    if existing:
        clean["Id"] = existing["Id"]
        url = f"{BASE}/api/v2/tables/{TABLE}/records"
        body = json.dumps(clean).encode()
        req = urllib.request.Request(
            url,
            data=body,
            method="PATCH",
            headers={"xc-token": token, "Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=60)
        return "updated"
    url = f"{BASE}/api/v2/tables/{TABLE}/records"
    body = json.dumps(clean).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"xc-token": token, "Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=60)
    return "created"


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: noco_backfill_from_sheets_csv.py <scenario_id> <export.csv> [more.csv ...]",
            file=sys.stderr,
        )
        sys.exit(1)
    token = _token()
    stats = {"created": 0, "updated": 0, "skip_no_leadgen": 0, "error": 0}
    for spec in sys.argv[1:]:
        if ":" in spec:
            scenario_id, path = spec.split(":", 1)
        else:
            print("Use scenario_id:path.csv for each file", file=sys.stderr)
            sys.exit(1)
        with Path(path).open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rec = record_from_sheets_row(row, scenario_id)
                    action = _upsert(token, rec)
                    stats[action] = stats.get(action, 0) + 1
                except urllib.error.HTTPError as e:
                    stats["error"] += 1
                    err = e.read().decode(errors="replace")[:200]
                    print(f"HTTP {e.code} leadgen={row.get('leadid')}: {err}", file=sys.stderr)
                except Exception as e:
                    stats["error"] += 1
                    print(f"Error leadgen={row.get('leadid')}: {e}", file=sys.stderr)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
