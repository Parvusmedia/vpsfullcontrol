#!/usr/bin/env python3
"""Patch Digitanimal FR Make scenario: Noco coalesce + Sheets (meta_DigitanimalFR) + phone coalesce."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

from patch_make_digitanimal_it_sheets import _phone_expr_inner
from patch_make_noco_meta_leads import _IML_NOCO, refresh_noco_in_blueprint

SPREADSHEET_ID = "1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw"
SHEET_FR = "meta_DigitanimalFR"
CONN = 1253622
SCENARIO_ID = "7951407"


def _sheets_values() -> dict[str, str]:
    m = _IML_NOCO
    phone_inner = _phone_expr_inner()
    return {
        "ad": "{{1.adName}}",
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
            "defaultCountry": "FR",
        },
        "metadata": {
            "designer": {"x": -705, "y": -174},
            "restore": {
                "expect": {
                    "defaultCountry": {"mode": "chose", "label": "France (FR)"},
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
            "sheetId": SHEET_FR,
            "spreadsheetId": SPREADSHEET_ID,
            "includesHeaders": True,
            "insertDataOption": "INSERT_ROWS",
            "useColumnHeaders": True,
            "valueInputOption": "USER_ENTERED",
            "insertUnformatted": False,
        },
        "metadata": {"designer": {"x": -271, "y": -180}},
    }


def refresh_fr_flow(blueprint: dict, xc_token: str, scenario_id: str = SCENARIO_ID) -> dict:
    bp = refresh_noco_in_blueprint(copy.deepcopy(blueprint), xc_token, scenario_id)
    noco = [m for m in bp["flow"] if m.get("id") in (7, 8)]
    trigger = next(m for m in bp["flow"] if m.get("id") == 1)
    bp["flow"] = [trigger, *noco, _phone_module(), _sheets_module()]
    return bp


def main() -> None:
    token = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not token:
        raise SystemExit("NOCO_TOKEN required")
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/scenario_7951407.json")
    data = json.loads(src.read_text(encoding="utf-8"))
    blueprint = data.get("blueprint", data)
    patched = refresh_fr_flow(blueprint, token)
    out = Path("/tmp/scenarios_update_7951407_args.json")
    out.write_text(
        json.dumps({"scenarioId": int(SCENARIO_ID), "blueprint": patched}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(out, [m["id"] for m in patched["flow"]])


if __name__ == "__main__":
    main()
