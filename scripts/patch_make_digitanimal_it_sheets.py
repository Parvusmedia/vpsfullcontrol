#!/usr/bin/env python3
"""Patch Digitanimal IT Make scenario: Noco coalesce + Sheets (meta_DigitanimalIT) + phone parse."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

from patch_make_noco_meta_leads import _IML_NOCO, refresh_noco_in_blueprint

SPREADSHEET_ID = "1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw"
SHEET_IT = "meta_DigitanimalIT"
CONN = 1253622


def _phone_expr_inner() -> str:
    """Make `ifempty(...)` without outer {{ }} for nesting inside another ifempty."""
    wrapped = _IML_NOCO["PHONE"]
    assert wrapped.startswith("{{") and wrapped.endswith("}}")
    return wrapped[2:-2]


def _sheets_values() -> dict[str, str]:
    m = _IML_NOCO
    phone_inner = _phone_expr_inner()
    return {
        "ad": "{{1.adsetName}}",
        "adid": "{{1.adId}}",
        "date": "{{1.dateCreated}}",
        "name": m["FULL_NAME"],
        "adset": "{{1.adsetName}}",
        "email": m["EMAIL"],
        "phone": "{{ifempty(3.e164; " + phone_inner + ")}}",
        "formid": "{{1.formId}}",
        "leadid": "{{1.leadgenId}}",
        "source": "meta_{{1.pageId}}",
        "adsetid": "{{1.adgroupId}}",
        "custom4": "{{1.homeListing}}",
        "custom5": "{{1.partnerName}}",
        "custom6": "{{1.retailerItemId}}",
        "campaign": "{{1.campaignName}}",
        "province": m["PROVINCE"],
        "campaignid": "{{1.campaignId}}",
        "tipo_animal": m["LIVESTOCK"],
        "cant-animales": m["HERD"],
    }


def _phone_module() -> dict:
    return {
        "id": 3,
        "module": "phonenumber:TransformerParseNumber",
        "version": 1,
        "parameters": {},
        "mapper": {
            "number": _IML_NOCO["PHONE"],
            "defaultCountry": "IT",
        },
        "metadata": {
            "designer": {"x": -300, "y": -172},
            "restore": {
                "expect": {
                    "defaultCountry": {"mode": "chose", "label": "Italy (IT)"},
                }
            },
        },
    }


def _sheets_module() -> dict:
    return {
        "id": 2,
        "module": "google-sheets:addRow",
        "version": 2,
        "parameters": {"__IMTCONN__": CONN},
        "mapper": {
            "mode": "fromAll",
            "values": _sheets_values(),
            "sheetId": SHEET_IT,
            "spreadsheetId": SPREADSHEET_ID,
            "includesHeaders": True,
            "insertDataOption": "INSERT_ROWS",
            "useColumnHeaders": True,
            "valueInputOption": "USER_ENTERED",
            "insertUnformatted": False,
        },
        "metadata": {"designer": {"x": -602, "y": -172}},
    }


def refresh_it_flow(blueprint: dict, xc_token: str, scenario_id: str = "7952998") -> dict:
    bp = refresh_noco_in_blueprint(copy.deepcopy(blueprint), xc_token, scenario_id)
    noco = [m for m in bp["flow"] if m.get("id") in (7, 8)]
    trigger = next(m for m in bp["flow"] if m.get("id") == 1)
    bp["flow"] = [trigger, *noco, _phone_module(), _sheets_module()]
    return bp


def main() -> None:
    token = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not token:
        raise SystemExit("NOCO_TOKEN required")
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/scenario_7952998.json")
    data = json.loads(src.read_text(encoding="utf-8"))
    blueprint = data.get("blueprint", data)
    patched = refresh_it_flow(blueprint, token)
    out = Path("/tmp/scenarios_update_7952998_args.json")
    out.write_text(
        json.dumps({"scenarioId": 7952998, "blueprint": patched}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(out, [m["id"] for m in patched["flow"]])


if __name__ == "__main__":
    main()
