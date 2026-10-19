#!/usr/bin/env python3
"""Fill empty `name` cells in Digitanimal meta sheets from Noco (match on leadid).

Requires GOOGLE_APPLICATION_CREDENTIALS with edit access to spreadsheet
1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw.

Use --export-plan when Sheets API is unavailable: writes intended updates from Noco only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from digitanimal_noco_record import record_from_make_bundle
from digitanimal_sheets_regenerate_from_noco import SCENARIO_TO_TAB, SPREADSHEET_ID, _fetch_all, _token

TABLE = "mieilgjtcw04jjr"
BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com")


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


def _name_from_noco_row(row: dict) -> str | None:
    mp = row.get("meta_payload_json") or {}
    sid = str(row.get("make_scenario_id") or "")
    rec = record_from_make_bundle(mp if isinstance(mp, dict) else {}, sid)
    return rec.get("full_name") or None


def _noco_by_leadgen(scenario_id: str) -> dict[str, dict]:
    token = _token()
    out: dict[str, dict] = {}
    for row in _fetch_all(token):
        if str(row.get("make_scenario_id") or "") != scenario_id:
            continue
        lg = (row.get("leadgen_id") or "").strip()
        if not lg:
            continue
        prev = out.get(lg)
        if not prev or int(row.get("Id") or 0) > int(prev.get("Id") or 0):
            out[lg] = row
    return out


def _col_letter(idx: int) -> str:
    """0-based column index -> A1 letter(s)."""
    n = idx + 1
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _scan_sheet(svc, tab: str) -> tuple[list[str], list[list[str]]]:
    res = (
        svc.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=f"'{tab}'!A:ZZ")
        .execute()
    )
    values = res.get("values") or []
    if not values:
        return [], []
    return values[0], values[1:]


def _plan_repairs(
    tab: str,
    header: list[str],
    data_rows: list[list[str]],
    noco: dict[str, dict],
) -> list[dict]:
    lead_col = header.index("leadid") if "leadid" in header else header.index("leadgen_id")
    name_col = header.index("name")
    repairs: list[dict] = []
    for sheet_row_num, row in enumerate(data_rows, start=2):
        if lead_col >= len(row):
            continue
        lead = (row[lead_col] or "").strip()
        if not lead or lead not in noco:
            continue
        cur = row[name_col].strip() if name_col < len(row) and row[name_col] else ""
        want = _name_from_noco_row(noco[lead])
        if not want or cur == want:
            continue
        if cur:
            continue
        repairs.append(
            {
                "sheet_row": sheet_row_num,
                "leadid": lead,
                "name": want,
                "cell": f"'{tab}'!{_col_letter(name_col)}{sheet_row_num}",
            }
        )
    return repairs


def main() -> None:
    p = argparse.ArgumentParser(description="Repair empty name cells from Noco")
    p.add_argument("--scenario", default="7950608", help="Make scenario id (default ES)")
    p.add_argument("--tab", help="Sheet tab (default from scenario)")
    p.add_argument("--dry-run", action="store_true", help="Print repairs; do not write")
    p.add_argument("--write", action="store_true", help="Apply batch updates to Sheets")
    p.add_argument("--export-plan", metavar="PATH", help="Write repair plan JSON (no Sheets read)")
    args = p.parse_args()

    tab = args.tab or SCENARIO_TO_TAB.get(str(args.scenario))
    if not tab:
        raise SystemExit("Unknown scenario; pass --tab")

    noco = _noco_by_leadgen(str(args.scenario))
    if args.export_plan:
        plan = [
            {"leadid": lg, "name": _name_from_noco_row(r)}
            for lg, r in sorted(noco.items(), key=lambda x: int(x[1].get("Id") or 0))
        ]
        plan = [x for x in plan if x.get("name")]
        with open(args.export_plan, "w", encoding="utf-8") as f:
            json.dump({"tab": tab, "scenario_id": args.scenario, "rows": plan}, f, ensure_ascii=False, indent=2)
        print(json.dumps({"exported": args.export_plan, "count": len(plan)}))
        if not args.write and not args.dry_run:
            return

    if args.export_plan and not args.write and not args.dry_run:
        return

    svc = _service()
    header, data_rows = _scan_sheet(svc, tab)
    if "leadid" not in header and "leadgen_id" not in header:
        raise SystemExit(f"{tab}: missing leadid column")
    if "name" not in header:
        raise SystemExit(f"{tab}: missing name column")

    repairs = _plan_repairs(tab, header, data_rows, noco)
    print(json.dumps({"tab": tab, "repairs": len(repairs)}, indent=2))
    for item in repairs[:30]:
        print(json.dumps(item, ensure_ascii=False))
    if len(repairs) > 30:
        print(f"... and {len(repairs) - 30} more")

    if args.dry_run or not args.write:
        return

    name_col = header.index("name")
    data = []
    for item in repairs:
        data.append(
            {
                "range": f"'{tab}'!{_col_letter(name_col)}{item['sheet_row']}",
                "values": [[item["name"]]],
            }
        )
    if not data:
        return
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()
    print(json.dumps({"updated_cells": len(data)}))


if __name__ == "__main__":
    main()
