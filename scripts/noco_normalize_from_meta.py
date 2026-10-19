#!/usr/bin/env python3
"""PATCH Noco meta_leads columns from meta_payload_json using canonical field aliases."""
from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from digitanimal_noco_record import record_from_make_bundle

TABLE = "mieilgjtcw04jjr"
BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com")


def _token() -> str:
    t = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not t:
        raise SystemExit("NOCO_TOKEN required")
    return t


def _fetch_all(token: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        url = f"{BASE}/api/v2/tables/{TABLE}/records?limit=100&offset={offset}"
        req = urllib.request.Request(url, headers={"xc-token": token})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("list") or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 100:
            break
        offset += len(batch)
    return rows


def _patch(token: str, body: dict) -> None:
    url = f"{BASE}/api/v2/tables/{TABLE}/records"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        method="PATCH",
        data=data,
        headers={"xc-token": token, "Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=60)


def main() -> None:
    dry = "--dry-run" in sys.argv
    token = _token()
    fields = ("email", "phone", "full_name", "province", "herd_count", "livestock_type", "title")
    updated = 0
    for row in _fetch_all(token):
        mp = row.get("meta_payload_json")
        if not isinstance(mp, dict) or not mp.get("data"):
            continue
        sid = str(row.get("make_scenario_id") or "")
        rec = record_from_make_bundle(mp, sid)
        patch = {"Id": row["Id"]}
        changed = False
        for f in fields:
            new = rec.get(f)
            old = row.get(f)
            if new and (old is None or str(old).strip() == ""):
                patch[f] = new
                changed = True
        if not changed:
            continue
        if dry:
            print(json.dumps({"Id": row["Id"], "leadgen_id": row.get("leadgen_id"), "patch": patch}))
        else:
            _patch(token, patch)
            updated += 1
    print(json.dumps({"updated": updated, "dry_run": dry}))


if __name__ == "__main__":
    main()
