#!/usr/bin/env python3
"""Diagnose failed Smart Life radiator workflow executions and apply safe fixes + error alerts.

Requires N8N_REST_API_KEY (n8n_api_...) against https://pmedia.app.n8n.cloud.

Example:
  python3 scripts/n8n_smartlife_radiador_fix.py --execution-id 508599 --apply
  python3 scripts/n8n_smartlife_radiador_fix.py --dry-run
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from n8n_unified import N8NClient, _detect_tokens, _print_json

SMARTLIFE_WORKFLOW_ID = "HPaa9jGQmpDex41t"
ERROR_WORKFLOW_NAME = "SmartLife Buhardilla — alertas error"


def _workflow_body(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("data"), dict) and payload["data"].get("nodes"):
        return payload["data"]
    if payload.get("nodes"):
        return payload
    return None


def _execution_body(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else None


def _first_execution_error(execution: dict[str, Any]) -> dict[str, Any] | None:
    data = execution.get("data") or {}
    result_data = data.get("resultData") or {}
    error = result_data.get("error")
    if isinstance(error, dict):
        node = error.get("node") or {}
        return {
            "message": error.get("message") or error.get("description") or "",
            "nodeName": node.get("name") if isinstance(node, dict) else None,
            "nodeType": node.get("type") if isinstance(node, dict) else None,
            "stack": error.get("stack") or "",
        }
    run_data = result_data.get("runData") or {}
    for node_name, runs in run_data.items():
        if not isinstance(runs, list):
            continue
        for run in runs:
            if not isinstance(run, dict):
                continue
            err = run.get("error")
            if isinstance(err, dict):
                return {
                    "message": err.get("message") or err.get("description") or "",
                    "nodeName": node_name,
                    "nodeType": (run.get("executionStatus") or {}).get("type"),
                    "stack": err.get("stack") or "",
                }
    return None


def _node_is_smartlife(node: dict[str, Any]) -> bool:
    blob = json.dumps(node, ensure_ascii=False).lower()
    type_name = (node.get("type") or "").lower()
    name = (node.get("name") or "").lower()
    return any(
        k in blob or k in type_name or k in name
        for k in ("smartlife", "smart life", "tuya", "thermostat", "radiador")
    )


def _find_telegram_credential(workflow: dict[str, Any]) -> dict[str, str] | None:
    for node in workflow.get("nodes") or []:
        creds = node.get("credentials") or {}
        telegram = creds.get("telegramApi")
        if isinstance(telegram, dict) and telegram.get("id"):
            return {"id": str(telegram["id"]), "name": str(telegram.get("name") or "Telegram")}
    return None


def _message_fix_plan(err: dict[str, Any], workflow: dict[str, Any]) -> list[dict[str, Any]]:
    message = (err.get("message") or "").lower()
    node_name = err.get("nodeName") or ""
    plans: list[dict[str, Any]] = []

    if "paired item" in message or "can't get" in message or "undefined" in message:
        plans.append(
            {
                "type": "expression_guard",
                "nodeName": node_name,
                "detail": "Añadir $ifEmpty / comprobar items antes de expresiones Smart Life.",
            }
        )
    if any(k in message for k in ("sign invalid", "permission deny", "token", "unauthorized", "expired")):
        plans.append(
            {
                "type": "smartlife_credential",
                "nodeName": node_name,
                "detail": "Reconectar credencial Smart Life / Tuya en n8n (expirada o revocada).",
            }
        )
    if "offline" in message or "device is not online" in message:
        plans.append({"type": "device_offline", "detail": "Dispositivo Luca offline en Smart Life; reintentos en nodo."})
    if "continue on fail" in message or "timeout" in message:
        plans.append({"type": "http_timeout", "detail": "Subir timeout y añadir reintento en nodo HTTP/Smart Life."})

    if not plans:
        for node in workflow.get("nodes") or []:
            if node.get("name") == node_name or _node_is_smartlife(node):
                params = node.get("parameters") or {}
                for key, val in list(params.items()):
                    if isinstance(val, str) and val.startswith("={{") and "$json" in val and "$input" not in val:
                        plans.append(
                            {
                                "type": "expression_root",
                                "nodeName": node.get("name"),
                                "detail": f"Revisar expresión en parámetro `{key}` (usar $input.item.json).",
                            }
                        )
                break
    return plans


def _patch_workflow(workflow: dict[str, Any], plans: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    wf = copy.deepcopy(workflow)
    applied: list[str] = []
    nodes_by_name = {n.get("name"): n for n in wf.get("nodes") or [] if n.get("name")}

    for plan in plans:
        ptype = plan.get("type")
        node_name = plan.get("nodeName")
        node = nodes_by_name.get(node_name) if node_name else None

        if ptype in {"expression_guard", "expression_root"} and node:
            params = node.setdefault("parameters", {})
            for key, val in list(params.items()):
                if isinstance(val, str) and val.startswith("={{") and "$input" not in val and "$json" in val:
                    params[key] = val.replace("$json", "$input.item.json")
                    applied.append(f"Reemplazado $json por $input.item.json en nodo `{node_name}` parámetro `{key}`.")
            if not node.get("onError"):
                node["onError"] = "continueRegularOutput"
                applied.append(f"onError=continueRegularOutput en `{node_name}` (evita abortar sin alerta).")

        if ptype == "smartlife_credential" and node:
            node["retryOnFail"] = True
            node["maxTries"] = 3
            node["waitBetweenTries"] = 2000
            applied.append(f"Reintentos activados en `{node_name}` tras fallo de credencial.")

        if ptype in {"device_offline", "http_timeout"} and node:
            node["retryOnFail"] = True
            node["maxTries"] = 5
            node["waitBetweenTries"] = 5000
            opts = node.setdefault("parameters", {}).setdefault("options", {})
            if isinstance(opts, dict) and "timeout" in opts:
                opts["timeout"] = max(int(opts.get("timeout") or 0), 60000)
            applied.append(f"Reintentos extendidos en `{node.get('name')}`.")

    settings = wf.setdefault("settings", {})
    settings.setdefault("timezone", "Europe/Madrid")
    settings["executionOrder"] = settings.get("executionOrder") or "v1"
    return wf, applied


def _build_error_workflow(
    telegram_cred: dict[str, str] | None,
    chat_id: str | None,
    notify_whatsapp: bool,
    whatsapp_to: str | None,
) -> dict[str, Any]:
    pos_x = 0
    nodes: list[dict[str, Any]] = []
    connections: dict[str, Any] = {}

    error_id = str(uuid.uuid4())
    nodes.append(
        {
            "parameters": {},
            "id": error_id,
            "name": "Error Trigger",
            "type": "n8n-nodes-base.errorTrigger",
            "typeVersion": 1,
            "position": [pos_x, 300],
        }
    )
    pos_x += 280
    last = "Error Trigger"
    main_out: list[list[dict[str, Any]]] = [[]]

    text_expr = (
        "={{ '❌ Error radiador buhardilla (Luca)\\n' "
        "+ 'Workflow: ' + ($json.workflow?.name || 'n/d') + '\\n' "
        "+ 'Ejecución: ' + ($json.execution?.id || 'n/d') + '\\n' "
        "+ 'Nodo: ' + ($json.execution?.lastNodeExecuted || 'n/d') + '\\n' "
        "+ 'Mensaje: ' + ($json.execution?.error?.message || $json.trigger?.error?.message || 'sin detalle') }}"
    )

    if telegram_cred and chat_id:
        tg_id = str(uuid.uuid4())
        nodes.append(
            {
                "parameters": {"chatId": chat_id, "text": text_expr, "additionalFields": {}},
                "id": tg_id,
                "name": "Telegram alerta",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [pos_x, 220],
                "credentials": {"telegramApi": telegram_cred},
            }
        )
        main_out[0].append({"node": "Telegram alerta", "type": "main", "index": 0})
        last = "Telegram alerta"
        pos_x += 280

    twochat_cred_id = os.getenv("TWOCHAT_CREDENTIAL_ID")
    if notify_whatsapp and whatsapp_to and twochat_cred_id:
        wa_id = str(uuid.uuid4())
        nodes.append(
            {
                "parameters": {
                    "method": "POST",
                    "url": "={{ $env.TWOCHAT_API_URL || 'https://api.p.2chat.io/open/whatsapp/send-message' }}",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": (
                        "={{ JSON.stringify({ "
                        "from_number: $env.TWOCHAT_FROM_NUMBER, "
                        "to_number: '" + whatsapp_to.replace("'", "") + "', "
                        "text: 'Error radiador buhardilla — ejecución ' + ($json.execution?.id || '') "
                        "+ ': ' + ($json.execution?.error?.message || '') "
                        "}) }}"
                    ),
                    "options": {},
                },
                "id": wa_id,
                "name": "WhatsApp 2Chat",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [pos_x, 380],
                "credentials": {
                    "httpHeaderAuth": {
                        "id": twochat_cred_id,
                        "name": os.getenv("TWOCHAT_CREDENTIAL_NAME", "2Chat API"),
                    }
                },
            }
        )
        if not main_out[0]:
            main_out[0].append({"node": "WhatsApp 2Chat", "type": "main", "index": 0})
        else:
            connections[last] = {"main": [[{"node": "WhatsApp 2Chat", "type": "main", "index": 0}]]}
            last = "WhatsApp 2Chat"

    connections["Error Trigger"] = {"main": main_out}

    return {
        "name": ERROR_WORKFLOW_NAME,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
        "active": True,
    }


def _find_workflow_id_by_name(client: N8NClient, name: str) -> str | None:
    status, payload = client.rest_get("/api/v1/workflows", params={"limit": 200})
    if status != 200:
        return None
    items = payload.get("data", []) if isinstance(payload, dict) else []
    for item in items:
        if item.get("name") == name and item.get("id"):
            return str(item["id"])
    return None


def _put_workflow(client: N8NClient, workflow_id: str, body: dict[str, Any]) -> tuple[bool, Any]:
    allowed = {
        "name",
        "nodes",
        "connections",
        "settings",
        "staticData",
        "pinData",
        "meta",
    }
    payload = {k: body[k] for k in allowed if k in body}
    if "active" in body:
        payload["active"] = body["active"]
    status, resp = client.rest_put(f"/api/v1/workflows/{workflow_id}", payload)
    return status == 200, resp


def run(args: argparse.Namespace) -> int:
    rest_key, _mcp = _detect_tokens()
    if not rest_key:
        _print_json(
            {
                "error": "Falta N8N_REST_API_KEY (prefijo n8n_api_). No puedo leer la ejecución 508599 ni corregir el workflow.",
                "workflow_id": args.workflow_id,
                "execution_id": args.execution_id,
            }
        )
        return 1

    n8n_url = os.getenv("N8N_URL")
    if not n8n_url:
        _print_json({"error": "Falta N8N_URL."})
        return 1

    client = N8NClient(n8n_url, rest_key, None)

    ex_status, ex_payload = client.rest_get(
        f"/api/v1/executions/{args.execution_id}",
        params={"includeData": "true"},
    )
    if ex_status != 200:
        _print_json({"error": "No se pudo leer ejecución.", "status": ex_status, "payload": ex_payload})
        return 1

    execution = _execution_body(ex_payload) or {}
    err = _first_execution_error(execution) or {"message": "Sin detalle en payload", "nodeName": None}

    wf_status, wf_payload = client.rest_get(f"/api/v1/workflows/{args.workflow_id}")
    if wf_status != 200:
        _print_json({"error": "No se pudo leer workflow.", "status": wf_status, "payload": wf_payload})
        return 1

    workflow = _workflow_body(wf_payload)
    if not workflow:
        _print_json({"error": "Workflow sin nodos en respuesta REST."})
        return 1

    plans = _message_fix_plan(err, workflow)
    patched, applied = _patch_workflow(workflow, plans)

    telegram_cred = _find_telegram_credential(workflow)
    chat_id = os.getenv("SMARTLIFE_NOTIFY_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    notify_wa = (
        args.notify in ("whatsapp", "both")
        and bool(os.getenv("SMARTLIFE_NOTIFY_WHATSAPP_TO"))
        and bool(os.getenv("TWOCHAT_CREDENTIAL_ID"))
    )
    notify_tg = args.notify in ("telegram", "both") and bool(telegram_cred and chat_id)

    report: dict[str, Any] = {
        "workflow_id": args.workflow_id,
        "workflow_name": workflow.get("name"),
        "execution_id": args.execution_id,
        "execution_status": execution.get("status"),
        "error": err,
        "fix_plan": plans,
        "patches_ready": applied,
        "dry_run": args.dry_run,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    if args.dry_run:
        _print_json(report)
        return 0

    ok, resp = _put_workflow(client, args.workflow_id, patched)
    if not ok:
        report["apply_error"] = resp
        _print_json(report)
        return 1
    report["workflow_patched"] = True

    if args.setup_error_alerts and (notify_tg or notify_wa):
        error_wf = _build_error_workflow(
            telegram_cred if notify_tg else None,
            chat_id,
            notify_wa,
            os.getenv("SMARTLIFE_NOTIFY_WHATSAPP_TO"),
        )
        existing_id = _find_workflow_id_by_name(client, ERROR_WORKFLOW_NAME)
        if existing_id:
            ok_err, resp_err = _put_workflow(client, existing_id, error_wf)
            error_workflow_id = existing_id if ok_err else None
            report["error_workflow"] = {"id": existing_id, "updated": ok_err, "response": resp_err if not ok_err else None}
        else:
            create_status, create_resp = client.rest_post("/api/v1/workflows", error_wf)
            error_workflow_id = None
            if create_status in (200, 201) and isinstance(create_resp, dict):
                error_workflow_id = (create_resp.get("data") or create_resp).get("id")
            report["error_workflow"] = {"created": create_status in (200, 201), "id": error_workflow_id}

        if error_workflow_id:
            patched_settings = copy.deepcopy(patched)
            patched_settings.setdefault("settings", {})["errorWorkflow"] = error_workflow_id
            ok_link, resp_link = _put_workflow(client, args.workflow_id, patched_settings)
            report["error_workflow_linked"] = ok_link
            if not ok_link:
                report["error_workflow_link_error"] = resp_link
    elif args.setup_error_alerts:
        report["error_workflow_skipped"] = (
            "Configura SMARTLIFE_NOTIFY_TELEGRAM_CHAT_ID y/o SMARTLIFE_NOTIFY_WHATSAPP_TO + TWOCHAT_CREDENTIAL_ID"
        )

    _print_json(report)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corregir workflow Smart Life buhardilla y alertas de error.")
    parser.add_argument("--workflow-id", default=SMARTLIFE_WORKFLOW_ID)
    parser.add_argument("--execution-id", default="508599")
    parser.add_argument("--dry-run", action="store_true", help="Solo diagnóstico, sin PUT.")
    parser.add_argument("--apply", action="store_true", help="Aplicar parches (implica no --dry-run).")
    parser.add_argument("--setup-error-alerts", action="store_true", default=True)
    parser.add_argument("--no-setup-error-alerts", action="store_false", dest="setup_error_alerts")
    parser.add_argument(
        "--notify",
        choices=("telegram", "whatsapp", "both"),
        default=os.getenv("SMARTLIFE_NOTIFY_CHANNEL", "both"),
    )
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False
    elif not args.dry_run:
        args.dry_run = True
    return args


if __name__ == "__main__":
    sys.exit(run(parse_args()))