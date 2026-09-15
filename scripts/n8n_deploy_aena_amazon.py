#!/usr/bin/env python3
"""Push Amazon Aena processing nodes onto workflow EkaAF0yc5VuRwtVG via n8n REST API."""

from __future__ import annotations

import json
import copy
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

WORKFLOW_ID = "EkaAF0yc5VuRwtVG"
TRIGGER_NAME = "Email Trigger (IMAP)"
BLUEPRINT = Path(__file__).resolve().parents[1] / "n8n/workflows/amazon-ads-aena-to-google-sheets.json"
SHEETS_NODE_NAMES = ("Vaciar pestaña Amazon", "Pegar CSV en Amazon")


def preserve_google_sheets_setup(live_nodes: list[dict], nodes: list[dict]) -> None:
    """Keep live Google Sheets credential + document/sheet/column mapping on deploy."""
    live_by_name = {
        n["name"]: n
        for n in live_nodes
        if n.get("type") == "n8n-nodes-base.googleSheets" or "googleSheets" in n.get("type", "")
    }
    for node in nodes:
        if node["name"] not in SHEETS_NODE_NAMES:
            continue
        live = live_by_name.get(node["name"])
        if not live:
            continue
        if live.get("credentials"):
            node["credentials"] = copy.deepcopy(live["credentials"])
        live_params = live.get("parameters") or {}
        params = node.setdefault("parameters", {})
        for key in ("documentId", "sheetName"):
            if key in live_params:
                params[key] = copy.deepcopy(live_params[key])
        if node["name"] == "Pegar CSV en Amazon":
            for key in ("columns", "options"):
                if live_params.get(key):
                    params[key] = copy.deepcopy(live_params[key])
        for attr in ("typeVersion", "id"):
            if live.get(attr) is not None:
                node[attr] = live[attr]


def api_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    base = os.environ["N8N_URL"].rstrip("/")
    key = os.environ["N8N_REST_API_KEY"]
    headers = {"Accept": "application/json", "X-N8N-API-KEY": key}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{base}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            data = json.loads(raw) if raw else {"error": exc.reason}
        except json.JSONDecodeError:
            data = {"error": raw or exc.reason}
        return exc.code, data


def main() -> int:
    if not os.getenv("N8N_URL") or not os.getenv("N8N_REST_API_KEY"):
        print("Missing N8N_URL or N8N_REST_API_KEY", file=sys.stderr)
        return 1

    status, payload = api_request("GET", f"/api/v1/workflows/{WORKFLOW_ID}")
    if status != 200:
        print(json.dumps({"error": "get workflow failed", "status": status, "payload": payload}, indent=2))
        return 1
    live = payload.get("data", payload)

    blueprint = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    skip = {
        "Gmail Trigger Aena",
        "Marcar correo leido",
        "Nota setup",
        "Nota flujo",
    }
    new_nodes = [n for n in blueprint["nodes"] if n["name"] not in skip]

    imap = next((n for n in live["nodes"] if n["name"] == TRIGGER_NAME), None)
    if not imap:
        print(f"Trigger {TRIGGER_NAME} not found in live workflow", file=sys.stderr)
        return 1

    imap = copy.deepcopy(imap)
    imap.setdefault("parameters", {})
    imap["parameters"]["postProcessAction"] = "read"
    imap["parameters"].setdefault("format", "simple")
    imap["parameters"].setdefault("mailbox", "INBOX")
    imap["parameters"].setdefault("options", {})["trackLastMessageId"] = True

    nodes = [imap] + new_nodes
    preserve_google_sheets_setup(live["nodes"], nodes)
    connections = copy.deepcopy(blueprint["connections"])
    connections[TRIGGER_NAME] = {"main": [[{"node": "Validar destinatario", "type": "main", "index": 0}]]}
    connections.pop("Gmail Trigger Aena", None)
    connections.pop("Marcar correo leido", None)
    for old_if in ("Hay filas?", "Hay filas para pegar?"):
        if old_if in connections and len(connections[old_if]["main"]) > 1:
            connections[old_if]["main"][1] = []
    connections["Pegar CSV en Amazon"] = {
        "main": [[{"node": "Registrar UID procesado", "type": "main", "index": 0}]]
    }
    connections["Registrar UID procesado"] = {"main": [[]]}

    # Patch IMAP-friendly fields in code nodes
    for node in nodes:
        if node["name"] == "Validar destinatario":
            node["parameters"]["jsCode"] = node["parameters"]["jsCode"].replace(
                "const headers = $json.headers || $json.header || {};",
                "const headers = $json.headers || $json.header || $json.metadata || {};",
            )
            if "imapUid:" not in node["parameters"]["jsCode"]:
                node["parameters"]["jsCode"] = node["parameters"]["jsCode"].replace(
                    "recipientCheck: expected,\n  },\n};",
                    "recipientCheck: expected,\n    imapUid: String($json.attributes?.uid ?? $json.uid ?? ''),\n    messageIdKey: String(\n      $json.messageId ?? $json.metadata?.['message-id'] ?? $json.headers?.['message-id'] ?? ''\n    ).trim(),\n  },\n};",
                )
        if node["name"] == "Extraer enlace de descarga":
            node["parameters"]["jsCode"] = node["parameters"]["jsCode"].replace(
                "const html = String($json.html || $json.textAsHtml || $json.text || '');",
                "const html = String($json.textHtml || $json.html || $json.textAsHtml || $json.text || '');",
            ).replace(
                "const text = String($json.text || '');",
                "const text = String($json.textPlain || $json.text || '');",
            ).replace(
                "emailId: $json.id,",
                "emailId: $json.attributes?.uid || $json.id,",
            )
            if "guardKey" not in node["parameters"]["jsCode"]:
                node["parameters"]["jsCode"] = node["parameters"]["jsCode"].replace(
                    "return {\n  json: {\n    emailId:",
                    "const guardKey = String($json.guardKey || $json.imapUid || $json.attributes?.uid || $json.id || '').trim();\n\nreturn {\n  json: {\n    emailId: guardKey ||",
                )

    settings = live.get("settings", {})
    allowed_settings = {
        k: settings[k]
        for k in (
            "executionOrder",
            "callerPolicy",
            "errorWorkflow",
            "timezone",
            "saveManualExecutions",
        )
        if k in settings
    }

    body = {
        "name": live["name"],
        "nodes": nodes,
        "connections": connections,
        "settings": allowed_settings or {"executionOrder": "v1"},
        "staticData": live.get("staticData", {}),
    }

    status, updated = api_request("PUT", f"/api/v1/workflows/{WORKFLOW_ID}", body)
    if status != 200:
        print(json.dumps({"error": "put workflow failed", "status": status, "payload": updated}, indent=2))
        return 1

    data = updated.get("data", updated)
    print(
        json.dumps(
            {
                "ok": True,
                "id": data.get("id"),
                "name": data.get("name"),
                "nodeCount": len(data.get("nodes", [])),
                "active": data.get("active"),
                "url": f"{os.environ['N8N_URL'].rstrip('/')}/workflow/{WORKFLOW_ID}",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
