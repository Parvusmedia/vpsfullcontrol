#!/usr/bin/env python3
"""Keep one Noco meta_leads row per leadgen_id (prefer meta_payload_json.data, else highest Id)."""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

TABLE = "mieilgjtcw04jjr"
BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com")


def _token() -> str:
    t = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not t:
        raise SystemExit("NOCO_TOKEN or NOCODB_API_TOKEN required")
    return t


def _fetch_all(token: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        url = f"{BASE}/api/v2/tables/{TABLE}/records?limit=100&offset={offset}"
        req = urllib.request.Request(url, headers={"xc-token": token, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        batch = data.get("list") or []
        if not batch:
            break
        rows.extend(batch)
        page_info = data.get("pageInfo") or {}
        if not page_info.get("isLastPage", len(batch) < 100):
            offset += len(batch)
        else:
            break
    return rows


def _score(row: dict) -> tuple[int, int]:
    mp = row.get("meta_payload_json")
    has_meta = (
        isinstance(mp, dict)
        and bool(mp.get("data"))
        and "backfill_source" not in mp
    )
    return (1 if has_meta else 0, int(row.get("Id") or 0))


def _delete(token: str, row_id: int) -> None:
    url = f"{BASE}/api/v2/tables/{TABLE}/records"
    body = json.dumps([{"Id": row_id}]).encode()
    req = urllib.request.Request(
        url,
        method="DELETE",
        data=body,
        headers={"xc-token": token, "Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=60)


def main() -> None:
    dry = "--dry-run" in sys.argv
    token = _token()
    rows = _fetch_all(token)
    by_leadgen: dict[str, list[dict]] = {}
    for row in rows:
        lg = row.get("leadgen_id")
        if not lg or not str(lg).strip():
            continue
        by_leadgen.setdefault(str(lg), []).append(row)
    to_delete: list[int] = []
    for lg, group in by_leadgen.items():
        if len(group) < 2:
            continue
        group.sort(key=_score, reverse=True)
        keep = group[0]
        for dup in group[1:]:
            to_delete.append(int(dup["Id"]))
        if dry:
            print(f"keep Id={keep['Id']} leadgen={lg}, delete {[d['Id'] for d in group[1:]]}")
    if dry:
        print(f"Would delete {len(to_delete)} rows")
        return
    deleted = 0
    for rid in to_delete:
        _delete(token, rid)
        deleted += 1
    print(json.dumps({"deleted": deleted, "leadgen_groups": len(by_leadgen)}))


if __name__ == "__main__":
    main()
