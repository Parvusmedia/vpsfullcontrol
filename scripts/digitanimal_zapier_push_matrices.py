#!/usr/bin/env python3
"""Push digitanimal_sheets_matrices.json to Google Sheets via Zapier MCP (run inside Cursor agent).

This module is imported by the agent after matrices are exported; it prints the three
PUT payloads as separate JSON lines for batch tool calls.
"""
from __future__ import annotations

import json
import os
import sys

SPREADSHEET_ID = "1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw"
# Optional: Zapier Google Sheets connection with edit access to Digitanimal_Leads
CONNECTION_ID = os.environ.get("DIGITANIMAL_ZAPIER_SHEETS_CONNECTION_ID", "")


def _put_spec(tab: str, values: list[list[str]], start_row: int = 1) -> dict:
    cell = f"'{tab}'!A{start_row}"
    return {
        "connection_id": CONNECTION_ID,
        "url": (
            f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/"
            f"{cell}?valueInputOption=USER_ENTERED"
        ),
        "body": json.dumps({"values": values}, ensure_ascii=False),
    }


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "/opt/cursor/artifacts/digitanimal_sheets_matrices.json"
    data = json.load(open(path, encoding="utf-8"))
    specs: list[dict] = []
    for tab, matrix in data.items():
        if tab == "meta_DigitanimalES" and len(matrix) > 20:
            mid = 1 + (len(matrix) - 1) // 2
            specs.append(_put_spec(tab, matrix[:mid], 1))
            specs.append(_put_spec(tab, matrix[mid:], mid + 1))
        else:
            specs.append(_put_spec(tab, matrix, 1))
    for s in specs:
        print(json.dumps(s, ensure_ascii=False))


if __name__ == "__main__":
    main()
