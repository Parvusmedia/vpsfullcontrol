#!/usr/bin/env python3
"""Add Smart Life message-center push branch after Validar resultado (Mateo workflow)."""

from __future__ import annotations

import copy
import json
import os
import sys
import uuid
import urllib.request
from pathlib import Path

WORKFLOW_ID = "DYJV0r0Z86pQIHH8"
ROOT = Path(__file__).resolve().parent

CONFIG_PUSH_FIELDS = """
  smartlife_uid:"eu1698169819562OGqFr",
  push_biz_type:18,
  push_template_id:"",
  push_template_use_params:true,
  notify_on_heat:true,"""

FULL_CONFIG = """return [{json:{
  room:"Mateo",
  sensor_id:"bf7634a37dd4e94e17r4pg",
  radiator_id:"bfa6454e40fd2820fdwlra",
  ir_hub_id:"bf89c842ee56fd3393t695",
  temperature_code:"temp_current",
  scale:1,
  min_c:21,
  target_c:21,
  target_mode:"heat",
  target_fan:"auto",
  max_age_minutes:30,
  auto_off_minutes:30,
  auto_off_above_c:22,
  smartlife_uid:"eu1698169819562OGqFr",
  push_biz_type:18,
  push_template_id:"PUSH_7146108284",
  push_template_use_params:true,
  notify_on_heat:true,
  dry_run:false,
  manual_commands:true,
  force_ac_test:false
}}];"""


def read_js(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").strip()


def inject_config(js: str) -> str:
    if "smartlife_uid" in js:
        return js
    return js.replace("  auto_off_above_c:22,", "  auto_off_above_c:22," + CONFIG_PUSH_FIELDS)


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_BASE_URL and N8N_API_KEY required", file=sys.stderr)
        return 1

    headers = {"X-N8N-API-KEY": key}
    wf = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{base}/api/v1/workflows/{WORKFLOW_ID}", headers=headers)
        ).read()
    )
    http_tpl = copy.deepcopy(next(n for n in wf["nodes"] if n["name"] == "Enviar orden Tuya"))
    validar = next(n for n in wf["nodes"] if n["name"] == "Validar resultado")
    validar.setdefault("parameters", {})["jsCode"] = read_js("n8n_mateo_ac_validar.js")

    conf = next(n for n in wf["nodes"] if n["name"] == "Configuracion")
    conf["parameters"]["jsCode"] = FULL_CONFIG

    y = validar["position"][1]
    x0 = validar["position"][0] + 260

    push_nodes = [n for n in wf["nodes"] if n.get("name") == "Notificar encendido?"]
    if not push_nodes:
        wf["nodes"].extend(
            [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Notificar encendido?",
                    "type": "n8n-nodes-base.if",
                    "typeVersion": 2.2,
                    "position": [x0, y],
                    "parameters": {
                        "conditions": {
                            "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
                            "combinator": "and",
                            "conditions": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "leftValue": "={{ $json.summary.should_notify_heat }}",
                                    "rightValue": True,
                                    "operator": {"type": "boolean", "operation": "true"},
                                },
                                {
                                    "id": str(uuid.uuid4()),
                                    "leftValue": "={{ $json.summary.status }}",
                                    "rightValue": "verified",
                                    "operator": {"type": "string", "operation": "equals"},
                                },
                                {
                                    "id": str(uuid.uuid4()),
                                    "leftValue": "={{ $('Configuracion').first().json.notify_on_heat }}",
                                    "rightValue": True,
                                    "operator": {"type": "boolean", "operation": "true"},
                                },
                                {
                                    "id": str(uuid.uuid4()),
                                    "leftValue": "={{ String($('Configuracion').first().json.push_template_id || '').trim() }}",
                                    "rightValue": "",
                                    "operator": {"type": "string", "operation": "notEquals"},
                                },
                            ],
                        }
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Preparar push SmartLife",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [x0 + 260, y - 80],
                    "parameters": {"jsCode": read_js("n8n_mateo_preparar_push.js")},
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Hay push?",
                    "type": "n8n-nodes-base.if",
                    "typeVersion": 2.2,
                    "position": [x0 + 390, y - 80],
                    "parameters": {
                        "conditions": {
                            "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
                            "combinator": "and",
                            "conditions": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "leftValue": "={{ $json.tuya_body }}",
                                    "rightValue": "",
                                    "operator": {"type": "string", "operation": "notEmpty"},
                                }
                            ],
                        }
                    },
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Push message center",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4.3,
                    "position": [x0 + 520, y - 80],
                    "parameters": {
                        **http_tpl.get("parameters", {}),
                        "method": "POST",
                    },
                    "credentials": http_tpl.get("credentials"),
                    "retryOnFail": False,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Registro push",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [x0 + 780, y - 80],
                    "parameters": {"jsCode": read_js("n8n_mateo_registro_push.js")},
                },
            ]
        )

    if not any(n.get("name") == "Hay push?" for n in wf["nodes"]):
        validar = next(n for n in wf["nodes"] if n["name"] == "Validar resultado")
        prep_ref = next(n for n in wf["nodes"] if n["name"] == "Preparar push SmartLife")
        y = prep_ref["position"][1]
        x = prep_ref["position"][0] + 130
        wf["nodes"].append(
            {
                "id": str(uuid.uuid4()),
                "name": "Hay push?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 2.2,
                "position": [x, y],
                "parameters": {
                    "conditions": {
                        "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
                        "combinator": "and",
                        "conditions": [
                            {
                                "id": str(uuid.uuid4()),
                                "leftValue": "={{ $json.tuya_body }}",
                                "rightValue": "",
                                "operator": {"type": "string", "operation": "notEmpty"},
                            }
                        ],
                    }
                },
            }
        )

    reg = next(n for n in wf["nodes"] if n["name"] == "Registro sin secretos")
    if_ = next(n for n in wf["nodes"] if n["name"] == "Notificar encendido?")
    if_push = next(n for n in wf["nodes"] if n["name"] == "Hay push?")
    if_.setdefault("parameters", {})["conditions"] = {
        "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
        "combinator": "and",
        "conditions": [
            {
                "id": str(uuid.uuid4()),
                "leftValue": "={{ $json.summary.should_notify_heat }}",
                "rightValue": True,
                "operator": {"type": "boolean", "operation": "true"},
            },
            {
                "id": str(uuid.uuid4()),
                "leftValue": "={{ $json.summary.status }}",
                "rightValue": "verified",
                "operator": {"type": "string", "operation": "equals"},
            },
            {
                "id": str(uuid.uuid4()),
                "leftValue": "={{ $('Configuracion').first().json.notify_on_heat }}",
                "rightValue": True,
                "operator": {"type": "boolean", "operation": "true"},
            },
            {
                "id": str(uuid.uuid4()),
                "leftValue": "={{ String($('Configuracion').first().json.push_template_id || '').trim() }}",
                "rightValue": "",
                "operator": {"type": "string", "operation": "notEquals"},
            },
        ],
    }
    if_push.setdefault("parameters", {})["conditions"] = {
        "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
        "combinator": "and",
        "conditions": [
            {
                "id": str(uuid.uuid4()),
                "leftValue": "={{ $json.tuya_body }}",
                "rightValue": "",
                "operator": {"type": "string", "operation": "notEmpty"},
            }
        ],
    }
    for n in wf["nodes"]:
        nname = n.get("name")
        if nname == "Preparar push SmartLife":
            n.setdefault("parameters", {})["jsCode"] = read_js("n8n_mateo_preparar_push.js")
        elif nname == "Registro push":
            n.setdefault("parameters", {})["jsCode"] = read_js("n8n_mateo_registro_push.js")

    prep = next(n for n in wf["nodes"] if n["name"] == "Preparar push SmartLife")
    push = next(n for n in wf["nodes"] if n["name"] == "Push message center")
    reg_push = next(n for n in wf["nodes"] if n["name"] == "Registro push")

    push["continueOnFail"] = True
    push.setdefault("parameters", {}).update(
        {
            "method": "POST",
            "url": '={{ "https://openapi.tuyaeu.com" + $json.tuya_path }}',
            "sendBody": True,
            "contentType": "raw",
            "rawContentType": "application/json",
            "body": "={{ $json.tuya_body }}",
        }
    )

    conn = wf.setdefault("connections", {})
    conn["Validar resultado"] = {
        "main": [[{"node": if_["name"], "type": "main", "index": 0}]]
    }
    conn[if_["name"]] = {
        "main": [
            [{"node": prep["name"], "type": "main", "index": 0}],
            [{"node": reg["name"], "type": "main", "index": 0}],
        ]
    }
    conn[prep["name"]] = {"main": [[{"node": if_push["name"], "type": "main", "index": 0}]]}
    conn[if_push["name"]] = {
        "main": [
            [{"node": push["name"], "type": "main", "index": 0}],
            [{"node": reg["name"], "type": "main", "index": 0}],
        ]
    }
    conn[push["name"]] = {"main": [[{"node": reg_push["name"], "type": "main", "index": 0}]]}
    conn[reg_push["name"]] = {"main": [[{"node": reg["name"], "type": "main", "index": 0}]]}

    settings = wf.get("settings") or {}
    allowed = {
        k: settings[k]
        for k in (
            "executionOrder",
            "timezone",
            "callerPolicy",
            "saveDataErrorExecution",
            "saveDataSuccessExecution",
            "errorWorkflow",
            "executionTimeout",
        )
        if k in settings
    }
    allowed["saveManualExecutions"] = True

    body = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": conn,
        "settings": allowed,
    }
    urllib.request.urlopen(
        urllib.request.Request(
            f"{base}/api/v1/workflows/{WORKFLOW_ID}",
            data=json.dumps(body).encode("utf-8"),
            method="PUT",
            headers={**headers, "Content-Type": "application/json"},
        )
    )
    print(json.dumps({"ok": True, "workflow_id": WORKFLOW_ID}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())