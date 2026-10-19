#!/usr/bin/env python3
"""Rebuild Digitanimal Spain Meta LeadAds blueprint (with phone router)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from patch_digitanimal_spain_phone_router import patch_blueprint

SHEETS_VALUES = {
    "ad": "{{1.adsetName}}",
    "adid": "{{1.adId}}",
    "date": "{{1.dateCreated}}",
    "name": "{{1.data.full_name}}",
    "adset": "{{1.adsetName}}",
    "email": "{{1.data.email}}",
    "formid": "{{1.formId}}",
    "leadid": "{{1.leadgenId}}",
    "source": "meta_{{1.pageId}}",
    "adsetid": "{{1.adgroupId}}",
    "custom4": "{{1.homeListing}}",
    "custom5": "{{1.partnerName}}",
    "custom6": "{{1.retailerItemId}}",
    "campaign": "{{1.campaignName}}",
    "province": "{{1.data.province}}",
    "campaignid": "{{1.campaignId}}",
    "tipo_animal": "{{1.data.`¿qué_tipo_de_ganado_tienes?`[]}}",
    "cant-animales": "{{1.data.`¿cuántos_animales_tienes?`[]}}",
}


def sheets_module(module_id: int, phone: str, y: int) -> dict:
    values = dict(SHEETS_VALUES)
    values["phone"] = phone
    return {
        "id": module_id,
        "module": "google-sheets:addRow",
        "version": 2,
        "parameters": {"__IMTCONN__": 1253622},
        "mapper": {
            "mode": "fromAll",
            "values": values,
            "sheetId": "meta_DigitanimalES",
            "spreadsheetId": "1uYhrrc9ovN_47BGJPf-FDaPI8k3uukeQn6db-1rsruw",
            "includesHeaders": True,
            "insertDataOption": "INSERT_ROWS",
            "useColumnHeaders": True,
            "valueInputOption": "USER_ENTERED",
            "insertUnformatted": False,
        },
        "metadata": {
            "designer": {"x": -327, "y": y},
            "restore": {
                "expect": {
                    "mode": {"label": "Select from all"},
                    "sheetId": {"mode": "chose", "label": "meta_DigitanimalES"},
                    "includesHeaders": {"label": "Yes"},
                    "insertDataOption": {"mode": "chose", "label": "Insert rows"},
                    "useColumnHeaders": {"label": "Yes"},
                    "valueInputOption": {"mode": "chose", "label": "User entered"},
                    "insertUnformatted": {"mode": "chose"},
                },
                "parameters": {
                    "__IMTCONN__": {
                        "data": {"scoped": "true", "connection": "google"},
                        "label": "Emiliano Parvus (emiliano@parvusmedia.com)",
                    }
                },
            },
        },
    }


def build_original_blueprint() -> dict:
    mod1 = {
        "id": 1,
        "mapper": {},
        "module": "facebook-lead-ads:NewLeadMultiple",
        "version": 2,
        "parameters": {
            "v": "2",
            "fields": [
                "id",
                "ad_id",
                "ad_name",
                "adset_id",
                "adset_name",
                "campaign_id",
                "campaign_name",
                "created_time",
                "custom_disclaimer_responses",
                "field_data",
                "form_id",
                "home_listing",
                "is_organic",
                "partner_name",
                "platform",
                "retailer_item_id",
                "vehicle",
            ],
            "__IMTHOOK__": 3901228,
        },
        "metadata": {
            "restore": {
                "parameters": {
                    "__IMTHOOK__": {
                        "data": {"editable": "false"},
                        "label": "Digitanimal_Meta-Leads",
                    }
                }
            },
            "designer": {"x": -984, "y": -159},
        },
    }
    mod4 = {
        "id": 4,
        "mapper": {"number": "{{1.data.phone_number}}", "defaultCountry": "ES"},
        "module": "phonenumber:TransformerParseNumber",
        "version": 1,
        "parameters": {},
        "metadata": {
            "restore": {"expect": {"defaultCountry": {"mode": "chose", "label": "Spain (ES)"}}},
            "designer": {"x": -684, "y": -159},
        },
    }
    mod2 = sheets_module(2, "{{4.e164}}", -161)
    return {
        "flow": [mod1, mod4, mod2],
        "name": "Digitanimal_Spain_Meta-LeadAds",
        "metadata": {
            "instant": True,
            "version": 1,
            "designer": {
                "orphans": [],
                "samples": {
                    "1": {
                        "adId": None,
                        "data": {
                            "email": "parvusmedia.development_digitanimal-es@gmail.com",
                            "province": "Alicante",
                            "full_name": "Emiliano Parvus test",
                            "phone_number": "+34664331172",
                            "¿cuántos_animales_tienes?": ["21_-_50"],
                            "¿qué_tipo_de_ganado_tienes?": ["caprino"],
                        },
                        "formId": "1593102499206086",
                        "pageId": "1057071361086931",
                        "leadgenId": "1815239626415945",
                        "dateCreated": "2026-10-14T09:23:05.000Z",
                    }
                },
            },
            "scenario": {
                "dlq": False,
                "slots": None,
                "dataloss": False,
                "maxErrors": 3,
                "autoCommit": True,
                "roundtrips": 1,
                "sequential": False,
                "confidential": False,
                "freshVariables": False,
                "autoCommitTriggerLast": True,
            },
        },
        "scheduling": {"type": "immediately", "maximum_runs_per_minute": 100},
        "interface": {"input": [], "output": []},
    }


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/opt/cursor/artifacts/digitanimal_spain_blueprint_patched.json")
    patched = patch_blueprint(build_original_blueprint())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(patched, ensure_ascii=False))
    print(out, len(out.read_text()))


if __name__ == "__main__":
    main()
