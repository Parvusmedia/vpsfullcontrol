#!/usr/bin/env python3
"""Rebuild meta_Digitanimal{ES,FR,IT} tabs from Noco meta_leads (one row per leadgen_id, by page_id).

Requires Application Default Credentials with Sheets scope:
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

Spreadsheet: 1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from digitanimal_noco_record import record_from_make_bundle
from digitanimal_sheets_export_from_noco import HEADERS, _sheet_row

SPREADSHEET_ID = "1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw"
TABLE = "mieilgjtcw04jjr"
BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com")

PAGE_TO_TAB: dict[str, str] = {
    "1057071361086931": "meta_DigitanimalES",
    "1323667177812599": "meta_DigitanimalFR",
    "100420486184506": "meta_DigitanimalIT",
}

SCENARIO_TO_TAB: dict[str, str] = {
    "7950608": "meta_DigitanimalES",
    "7951407": "meta_DigitanimalFR",
    "7952998": "meta_DigitanimalIT",
}


def _token() -> str:
    t = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not t:
        raise SystemExit("NOCO_TOKEN required")
    return t


def _fetch_all(token: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        url = f"{BASE}/api/v2/tables/{TABLE}/records?limit=100&offset={offset}&sort=Id"
        req = urllib.request.Request(url, headers={"xc-token": token})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("list") or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 100:
            break
        offset += len(batch)
    return rows


def _page_id(row: dict) -> str | None:
    pid = row.get("page_id")
    if pid:
        return str(pid)
    src = row.get("lead_source") or ""
    if isinstance(src, str) and src.startswith("meta_"):
        return src.replace("meta_", "", 1) or None
    mp = row.get("meta_payload_json") or {}
    if isinstance(mp, dict) and mp.get("pageId"):
        return str(mp["pageId"])
    return None


def _tab_for_row(row: dict) -> str | None:
    pid = _page_id(row)
    if pid and pid in PAGE_TO_TAB:
        return PAGE_TO_TAB[pid]
    sid = str(row.get("make_scenario_id") or "")
    return SCENARIO_TO_TAB.get(sid)


def _dedupe_by_leadgen(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Keep row with highest Noco Id per leadgen_id."""
    best: dict[str, dict] = {}
    skipped_no_lead: list[dict] = []
    for r in rows:
        lg = (r.get("leadgen_id") or "").strip()
        if not lg:
            skipped_no_lead.append(r)
            continue
        prev = best.get(lg)
        if not prev or int(r.get("Id") or 0) > int(prev.get("Id") or 0):
            best[lg] = r
    return list(best.values()), skipped_no_lead


def _partition(rows: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    by_tab: dict[str, list[dict]] = {t: [] for t in PAGE_TO_TAB.values()}
    unknown: list[dict] = []
    for r in rows:
        tab = _tab_for_row(r)
        if tab:
            by_tab[tab].append(r)
        else:
            unknown.append(r)
    for tab in by_tab:
        by_tab[tab].sort(key=lambda x: (x.get("date_created") or "", int(x.get("Id") or 0)))
    return by_tab, unknown


def _values_matrix(rows: list[dict]) -> list[list[str]]:
    out: list[list[str]] = [HEADERS]
    for r in rows:
        sr = _sheet_row(r)
        out.append([sr.get(h, "") or "" for h in HEADERS])
    return out


def _service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.isfile(creds_path):
        raise SystemExit(
            "GOOGLE_APPLICATION_CREDENTIALS must point to a service account JSON with Sheets access"
        )
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _rewrite_tab(svc, tab: str, matrix: list[list[str]], dry_run: bool) -> int:
    data_rows = max(0, len(matrix) - 1)
    if dry_run:
        print(f"{tab}: would write {data_rows} data row(s)")
        return data_rows
    svc.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{tab}'!A:ZZ",
        body={},
    ).execute()
    svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{tab}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": matrix},
    ).execute()
    return data_rows


def main() -> None:
    p = argparse.ArgumentParser(description="Regenerate Digitanimal meta sheets from Noco")
    p.add_argument("--dry-run", action="store_true", help="Print counts only; do not touch Sheets")
    p.add_argument(
        "--write",
        action="store_true",
        help="Rewrite Google Sheets (requires GOOGLE_APPLICATION_CREDENTIALS)",
    )
    p.add_argument(
        "--export-json",
        metavar="PATH",
        help="Write tab -> values matrix JSON (for external API push)",
    )
    args = p.parse_args()

    token = _token()
    raw = _fetch_all(token)
    deduped, no_lead = _dedupe_by_leadgen(raw)
    by_tab, unknown = _partition(deduped)

    summary = {
        "noco_total": len(raw),
        "after_dedupe": len(deduped),
        "skipped_no_leadgen_id": len(no_lead),
        "unknown_tab": len(unknown),
        "per_tab": {tab: len(by_tab[tab]) for tab in by_tab},
    }
    print(json.dumps(summary, indent=2))

    matrices = {tab: _values_matrix(by_tab[tab]) for tab in by_tab}
    if args.export_json:
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(matrices, f, ensure_ascii=False)
        print(f"exported {args.export_json}")

    if args.dry_run or not args.write:
        return

    svc = _service()
    for tab, matrix in matrices.items():
        n = _rewrite_tab(svc, tab, matrix, dry_run=False)
        print(f"{tab}: wrote {n} data row(s)")


if __name__ == "__main__":
    main()
