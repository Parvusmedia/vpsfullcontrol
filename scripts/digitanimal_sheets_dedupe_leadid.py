#!/usr/bin/env python3
"""Delete older duplicate rows in Digitanimal meta Google Sheets (keep last row per leadid).

Requires Application Default Credentials with Sheets scope, e.g.:
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

Spreadsheet: 1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

SPREADSHEET_ID = "1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw"
DEFAULT_TABS = ("meta_DigitanimalES", "meta_DigitanimalFR", "meta_DigitanimalIT")


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


def dedupe_tab(svc, tab: str, dry_run: bool) -> tuple[int, int]:
    result = (
        svc.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=f"'{tab}'!A:ZZ")
        .execute()
    )
    values = result.get("values") or []
    if len(values) < 2:
        return 0, 0
    header = values[0]
    lead_col = None
    for name in ("leadid", "lead_id", "leadgen_id"):
        if name in header:
            lead_col = header.index(name)
            break
    if lead_col is None:
        raise SystemExit(f"{tab}: no leadid column in header {header[:12]}")

    rows_by_lead: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(values[1:], start=2):
        if lead_col >= len(row):
            continue
        lead = (row[lead_col] or "").strip()
        if lead:
            rows_by_lead[lead].append(idx)

    to_delete: list[int] = []
    for _lead, row_nums in rows_by_lead.items():
        if len(row_nums) < 2:
            continue
        to_delete.extend(sorted(row_nums)[:-1])

    if not to_delete:
        return 0, 0

    to_delete.sort(reverse=True)
    if dry_run:
        print(f"{tab}: would delete {len(to_delete)} row(s): {to_delete[:20]}{'...' if len(to_delete)>20 else ''}")
        return len(to_delete), 0

    deleted = 0
    sheet_id = _sheet_gid(svc, tab)
    for row_num in to_delete:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_num - 1,
                                "endIndex": row_num,
                            }
                        }
                    }
                ]
            },
        ).execute()
        deleted += 1
    return deleted, len(to_delete)


def _sheet_gid(svc, tab: str) -> int:
    meta = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sh in meta.get("sheets", []):
        if sh["properties"]["title"] == tab:
            return int(sh["properties"]["sheetId"])
    raise SystemExit(f"Worksheet not found: {tab}")


def main() -> None:
    p = argparse.ArgumentParser(description="Dedupe Digitanimal meta sheets by leadid")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("tabs", nargs="*", default=list(DEFAULT_TABS))
    args = p.parse_args()
    svc = _service()
    total = 0
    for tab in args.tabs:
        n, _ = dedupe_tab(svc, tab, args.dry_run)
        total += n
        if not args.dry_run and n:
            print(f"{tab}: deleted {n} duplicate row(s)")
    print(f"done total={'would_delete' if args.dry_run else 'deleted'}={total}")


if __name__ == "__main__":
    main()
