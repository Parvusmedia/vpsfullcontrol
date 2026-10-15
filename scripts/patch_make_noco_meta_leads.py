#!/usr/bin/env python3
"""Insert NocoDB mirror steps (HTTP POST + PATCH meta payload) into Digitanimal Make scenarios."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

NOCO_URL = "https://mpa.parvusmedia.com/api/v2/tables/mieilgjtcw04jjr/records"

# Shared IML (Meta field_data coalesce)
EMAIL = "{{ifempty(1.data.email; 1.data.`correo_electrónico`; 1.data.`e-mail`)}}"
PHONE = "{{ifempty(1.data.phone_number; 1.data.`número_de_teléfono`; 1.data.`numéro_de_téléphone`)}}"
FULL_NAME = (
    "{{ifempty(1.data.full_name; 1.data.nombre_y_apellidos; "
    "trim(1.data.`prénom` & \" \" & 1.data.`nom_de_famille`))}}"
)
PROVINCE = (
    "{{ifempty(1.data.province; 1.data.provincia; 1.data.region; "
    "1.data.`localisation_d’élevage`)}}"
)
HERD = (
    "{{ifempty(1.data.`¿cuántos_animales_tienes?`[]; "
    "1.data.`how_many_animals_do_you_have?`[]; "
    "1.data.`quantos_animais_você_tem?`[]; "
    "1.data.`combien_d’animaux_avez-vous_?`[]; "
    "1.data.`número_de_animales:`[])}}"
)
LIVESTOCK = (
    "{{ifempty(1.data.`¿qué_tipo_de_ganado_tienes?`[]; "
    "1.data.`what_type_of_livestock_do_you_own?`[]; "
    "1.data.`qual_o_tipo_de_gado_que_possui?`[]; "
    "1.data.`quel_type_de_bétail_avez-vous_?`[])}}"
)


def noco_post_body(scenario_id: str) -> str:
    """POST row without meta_payload_json (avoids 422 from empty embedded JSON in one shot)."""
    lines = [
        "{",
        f'  "leadgen_id": "{{{{1.leadgenId}}}}",',
        f'  "form_id": "{{{{1.formId}}}}",',
        f'  "page_id": "{{{{1.pageId}}}}",',
        f'  "platform": "{{{{1.platform}}}}",',
        '  "is_organic": {{if(1.isOrganic; true; false)}},',
        f'  "date_created": "{{{{1.dateCreated}}}}",',
        f'  "lead_source": "meta_{{{{1.pageId}}}}",',
        f'  "campaign_id": "{{{{1.campaignId}}}}",',
        f'  "campaign_name": "{{{{1.campaignName}}}}",',
        f'  "adset_id": "{{{{1.adsetId}}}}",',
        f'  "adset_name": "{{{{1.adsetName}}}}",',
        f'  "ad_id": "{{{{1.adId}}}}",',
        f'  "ad_name": "{{{{1.adName}}}}",',
        f'  "adgroup_id": "{{{{1.adgroupId}}}}",',
        f'  "email": "{EMAIL}",',
        f'  "phone": "{PHONE}",',
        f'  "full_name": "{FULL_NAME}",',
        f'  "province": "{PROVINCE}",',
        f'  "herd_count": "{HERD}",',
        f'  "livestock_type": "{LIVESTOCK}",',
        f'  "home_listing": "{{{{1.homeListing}}}}",',
        f'  "partner_name": "{{{{1.partnerName}}}}",',
        f'  "retailer_item_id": "{{{{1.retailerItemId}}}}",',
        f'  "make_scenario_id": "{scenario_id}",',
        f'  "title": "{FULL_NAME}"',
        "}",
    ]
    return "\n".join(lines)


def noco_meta_patch_body() -> str:
    """PATCH meta_payload_json with full Meta trigger bundle (module 1 output)."""
    lines = [
        "{",
        '  "Id": {{7.data.Id}},',
        '  "meta_payload_json": {',
        '    "leadgenId": "{{1.leadgenId}}",',
        '    "formId": "{{1.formId}}",',
        '    "pageId": "{{1.pageId}}",',
        '    "dateCreated": "{{1.dateCreated}}",',
        '    "platform": "{{1.platform}}",',
        '    "isOrganic": {{if(1.isOrganic; true; false)}},',
        '    "campaignId": "{{1.campaignId}}",',
        '    "campaignName": "{{1.campaignName}}",',
        '    "adsetId": "{{1.adsetId}}",',
        '    "adsetName": "{{1.adsetName}}",',
        '    "adId": "{{1.adId}}",',
        '    "adName": "{{1.adName}}",',
        '    "adgroupId": "{{1.adgroupId}}",',
        '    "homeListing": "{{1.homeListing}}",',
        '    "partnerName": "{{1.partnerName}}",',
        '    "retailerItemId": "{{1.retailerItemId}}",',
        '    "data": {{1.data}}',
        "  }",
        "}",
    ]
    return "\n".join(lines)


def _http_mapper(xc_token: str, method: str, data: str) -> dict:
    return {
        "url": NOCO_URL,
        "method": method,
        "serializeUrl": False,
        "headers": [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "xc-token", "value": xc_token},
        ],
        "qs": [],
        "bodyType": "raw",
        "parseResponse": True,
        "authUser": "",
        "authPass": "",
        "timeout": "",
        "shareCookies": False,
        "ca": "",
        "rejectUnauthorized": True,
        "followRedirect": True,
        "useQuerystring": False,
        "gzip": True,
        "useMtls": False,
        "contentType": "application/json",
        "data": data,
        "followAllRedirects": False,
    }


def http_post_module(xc_token: str, scenario_id: str) -> dict:
    return {
        "id": 7,
        "module": "http:ActionSendData",
        "version": 3,
        "parameters": {"handleErrors": True},
        "mapper": _http_mapper(xc_token, "post", noco_post_body(scenario_id)),
        "metadata": {"designer": {"x": -620, "y": -320}},
    }


def http_patch_meta_module(xc_token: str) -> dict:
    return {
        "id": 8,
        "module": "http:ActionSendData",
        "version": 3,
        "parameters": {"handleErrors": True},
        "mapper": _http_mapper(xc_token, "patch", noco_meta_patch_body()),
        "metadata": {"designer": {"x": -460, "y": -320}},
    }


def strip_noco_modules(flow: list) -> list:
    return [m for m in flow if m.get("id") not in (6, 7, 8)]


def insert_after_trigger(flow: list, xc_token: str, scenario_id: str) -> list:
    flow = strip_noco_modules(flow)
    if not flow or flow[0].get("id") != 1:
        raise ValueError("Expected module 1 as Meta trigger")
    out = [flow[0], http_post_module(xc_token, scenario_id), http_patch_meta_module(xc_token)]
    out.extend(flow[1:])
    return out


def patch_blueprint(blueprint: dict, xc_token: str, scenario_id: str) -> dict:
    bp = copy.deepcopy(blueprint)
    bp["flow"] = insert_after_trigger(bp["flow"], xc_token, scenario_id)
    return bp


def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: patch_make_noco_meta_leads.py <scenario_get.json> <scenario_id> <xc_token> [out.json]",
            file=sys.stderr,
        )
        sys.exit(1)
    src = Path(sys.argv[1])
    scenario_id = sys.argv[2]
    token = sys.argv[3]
    out = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    data = json.loads(src.read_text(encoding="utf-8"))
    blueprint = data.get("blueprint", data)
    patched = patch_blueprint(blueprint, token, scenario_id)
    if out:
        out.write_text(json.dumps(patched, ensure_ascii=False, indent="\t"), encoding="utf-8")
        print(out)
    else:
        json.dump(patched, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
