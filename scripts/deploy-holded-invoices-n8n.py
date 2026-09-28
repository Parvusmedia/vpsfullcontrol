#!/usr/bin/env python3
"""Deploy or update n8n workflow holded-facturas-havas-cde on pmedia.app.n8n.cloud.

Secrets (webhook HMAC) are read from /opt/apps/private/cde/holded.env on the host
where this runs — never commit the secret.

Usage (on parvus-vps or with env vars):
  export N8N_BASE_URL=https://pmedia.app.n8n.cloud
  export N8N_API_KEY=n8n_api_...
  python3 scripts/deploy-holded-invoices-n8n.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

HOLDED_CONTACT_ID = "6023ce4a0a356d6caf64b163"
SPREADSHEET_ID = "1IYiaHazczGDWsMIQosu9Ggpws1Lv2JkicCkshnt5-D0"
SHEET_TAB = "Facturas"
WEBHOOK_PATH = "holded-invoices-cde"
WORKFLOW_NAME = "holded-facturas-havas-cde"
GOOGLE_SHEETS_CRED_ID = "WMPnjZZ4e80DfuGP"
GOOGLE_SHEETS_CRED_NAME = "Google Sheets account"

HOLDED_ENV = Path("/opt/apps/private/cde/holded.env")


def _load_holded_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not HOLDED_ENV.is_file():
        return env
    for line in HOLDED_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def _nid() -> str:
    return str(uuid4())


def _build_workflow(webhook_secret: str) -> dict:
    # Escape for embedding in JS string
    secret_js = json.dumps(webhook_secret)

    verify_js = f"""
const crypto = require('crypto');
const secret = {secret_js};
const item = $input.first();
const headers = item.json.headers || {{}};
const received = String(
  headers['x-holded-webhook-signature'] ||
  headers['X-Holded-Webhook-Signature'] ||
  ''
).replace(/^sha256=/, '');

let rawBody;
if (item.binary?.data) {{
  rawBody = Buffer.from(item.binary.data.data, item.binary.data.encoding || 'base64');
}} else if (item.json.rawBody) {{
  rawBody = Buffer.from(String(item.json.rawBody), 'utf8');
}} else {{
  const body = item.json.body ?? item.json;
  rawBody = Buffer.from(JSON.stringify(body), 'utf8');
}}

const expected = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
if (
  !received ||
  received.length !== expected.length ||
  !crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected))
) {{
  throw new Error('Invalid Holded webhook signature');
}}

const event =
  headers['x-holded-webhook-event'] ||
  headers['X-Holded-Webhook-Event'] ||
  '';

let payload;
try {{
  payload = JSON.parse(rawBody.toString('utf8'));
}} catch (e) {{
  throw new Error('Invalid JSON body');
}}

return [{{ json: {{ event, payload, headers }} }}];
""".strip()

    build_row_js = """
const { event, payload } = $json;
const now = new Date().toISOString();
const lines = Array.isArray(payload.lines) ? payload.lines : [];
const lineSummary = lines
  .map((l) => l.name || l.description || '')
  .filter(Boolean)
  .join('; ');
const tags = Array.isArray(payload.tags) ? payload.tags.join(';') : '';

const base = {
  invoice_id: payload.id || '',
  numero: payload.documentNumber || '',
  fecha: payload.date || '',
  vencimiento: payload.dueDate || '',
  total: payload.total != null ? String(payload.total) : '',
  moneda: payload.currency || '',
  tags_factura: tags,
  lineas_resumen: lineSummary,
  contact_id: payload.contactId || '',
};

if (event === 'invoice.create') {
  return [{
    json: {
      ...base,
      estado: 'borrador',
      creada_en: now,
      aprobada_en: '',
      email_estado: '',
      destinatarios: '',
      ultimo_error: '',
    },
  }];
}

if (event === 'invoice.approve') {
  return [{
    json: {
      ...base,
      estado: 'aprobada',
      creada_en: '',
      aprobada_en: payload.approvedAt || now,
      email_estado: 'pendiente',
      destinatarios: '',
      ultimo_error: '',
    },
  }];
}

return [];
""".strip()

    webhook_id = _nid()
    nodes = [
        {
            "parameters": {
                "httpMethod": "POST",
                "path": WEBHOOK_PATH,
                "responseMode": "onReceived",
                "options": {"rawBody": True},
            },
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [-800, 0],
            "id": _nid(),
            "name": "Holded Webhook",
            "webhookId": webhook_id,
        },
        {
            "parameters": {"jsCode": verify_js},
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [-560, 0],
            "id": _nid(),
            "name": "Verify signature",
        },
        {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "strict",
                        "version": 2,
                    },
                    "conditions": [
                        {
                            "id": _nid(),
                            "leftValue": "={{ $json.payload.contactId }}",
                            "rightValue": HOLDED_CONTACT_ID,
                            "operator": {"type": "string", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [-320, 0],
            "id": _nid(),
            "name": "Cliente Havas",
        },
        {
            "parameters": {
                "rules": {
                    "values": [
                        {
                            "conditions": {
                                "options": {
                                    "caseSensitive": True,
                                    "leftValue": "",
                                    "typeValidation": "strict",
                                    "version": 2,
                                },
                                "conditions": [
                                    {
                                        "leftValue": "={{ $json.event }}",
                                        "rightValue": "invoice.create",
                                        "operator": {
                                            "type": "string",
                                            "operation": "equals",
                                        },
                                    }
                                ],
                                "combinator": "and",
                            },
                            "renameOutput": True,
                            "outputKey": "create",
                        },
                        {
                            "conditions": {
                                "options": {
                                    "caseSensitive": True,
                                    "leftValue": "",
                                    "typeValidation": "strict",
                                    "version": 2,
                                },
                                "conditions": [
                                    {
                                        "leftValue": "={{ $json.event }}",
                                        "rightValue": "invoice.approve",
                                        "operator": {
                                            "type": "string",
                                            "operation": "equals",
                                        },
                                    }
                                ],
                                "combinator": "and",
                            },
                            "renameOutput": True,
                            "outputKey": "approve",
                        },
                    ]
                },
                "options": {},
            },
            "type": "n8n-nodes-base.switch",
            "typeVersion": 3.2,
            "position": [-80, 0],
            "id": _nid(),
            "name": "Evento",
        },
        {
            "parameters": {"jsCode": build_row_js},
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [160, -80],
            "id": _nid(),
            "name": "Build row",
        },
        {
            "parameters": {
                "operation": "appendOrUpdate",
                "documentId": {
                    "__rl": True,
                    "value": SPREADSHEET_ID,
                    "mode": "id",
                },
                "sheetName": {
                    "__rl": True,
                    "value": SHEET_TAB,
                    "mode": "name",
                },
                "columns": {
                    "mappingMode": "defineBelow",
                    "value": {
                        "invoice_id": "={{ $json.invoice_id }}",
                        "numero": "={{ $json.numero }}",
                        "fecha": "={{ $json.fecha }}",
                        "vencimiento": "={{ $json.vencimiento }}",
                        "estado": "={{ $json.estado }}",
                        "total": "={{ $json.total }}",
                        "moneda": "={{ $json.moneda }}",
                        "tags_factura": "={{ $json.tags_factura }}",
                        "lineas_resumen": "={{ $json.lineas_resumen }}",
                        "contact_id": "={{ $json.contact_id }}",
                        "creada_en": "={{ $json.creada_en }}",
                        "aprobada_en": "={{ $json.aprobada_en }}",
                        "email_estado": "={{ $json.email_estado }}",
                        "destinatarios": "={{ $json.destinatarios }}",
                        "ultimo_error": "={{ $json.ultimo_error }}",
                    },
                    "matchingColumns": ["invoice_id"],
                    "schema": [
                        {"id": "invoice_id", "displayName": "invoice_id", "type": "string", "canBeUsedToMatch": True},
                        {"id": "numero", "displayName": "numero", "type": "string"},
                        {"id": "fecha", "displayName": "fecha", "type": "string"},
                        {"id": "vencimiento", "displayName": "vencimiento", "type": "string"},
                        {"id": "estado", "displayName": "estado", "type": "string"},
                        {"id": "total", "displayName": "total", "type": "string"},
                        {"id": "moneda", "displayName": "moneda", "type": "string"},
                        {"id": "tags_factura", "displayName": "tags_factura", "type": "string"},
                        {"id": "lineas_resumen", "displayName": "lineas_resumen", "type": "string"},
                        {"id": "contact_id", "displayName": "contact_id", "type": "string"},
                        {"id": "creada_en", "displayName": "creada_en", "type": "string"},
                        {"id": "aprobada_en", "displayName": "aprobada_en", "type": "string"},
                        {"id": "email_estado", "displayName": "email_estado", "type": "string"},
                        {"id": "destinatarios", "displayName": "destinatarios", "type": "string"},
                        {"id": "ultimo_error", "displayName": "ultimo_error", "type": "string"},
                    ],
                },
                "options": {},
            },
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.7,
            "position": [400, -80],
            "id": _nid(),
            "name": "Sheets Facturas",
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": GOOGLE_SHEETS_CRED_ID,
                    "name": GOOGLE_SHEETS_CRED_NAME,
                }
            },
        },
    ]

    connections = {
        "Holded Webhook": {"main": [[{"node": "Verify signature", "type": "main", "index": 0}]]},
        "Verify signature": {"main": [[{"node": "Cliente Havas", "type": "main", "index": 0}]]},
        "Cliente Havas": {
            "main": [
                [{"node": "Evento", "type": "main", "index": 0}],
                [],
            ]
        },
        "Evento": {
            "main": [
                [{"node": "Build row", "type": "main", "index": 0}],
                [{"node": "Build row", "type": "main", "index": 0}],
            ]
        },
        "Build row": {"main": [[{"node": "Sheets Facturas", "type": "main", "index": 0}]]},
    }

    return {
        "name": WORKFLOW_NAME,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
    }


def _api(method: str, url: str, key: str, body: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {"X-N8N-API-KEY": key, "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw) if raw else {"error": exc.reason}
        except json.JSONDecodeError:
            payload = {"error": raw[:500]}
        return exc.code, payload


def _find_workflow_id(base: str, key: str) -> str | None:
    status, payload = _api("GET", f"{base}/api/v1/workflows?limit=250", key)
    if status != 200:
        return None
    for wf in payload.get("data", []):
        if wf.get("name") == WORKFLOW_NAME:
            return wf.get("id")
    return None


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "https://pmedia.app.n8n.cloud").rstrip("/")
    api_key = os.environ.get("N8N_API_KEY") or os.environ.get("N8N_REST_API_KEY")
    if not api_key:
        print("Missing N8N_API_KEY", file=sys.stderr)
        return 1

    holded = _load_holded_env()
    secret = holded.get("HOLDED_WEBHOOK_SECRET") or os.environ.get("HOLDED_WEBHOOK_SECRET")
    if not secret or not secret.startswith("whsec_"):
        print("Missing HOLDED_WEBHOOK_SECRET in holded.env", file=sys.stderr)
        return 1

    body = _build_workflow(secret)
    existing = _find_workflow_id(base, api_key)

    if existing:
        status, payload = _api("PUT", f"{base}/api/v1/workflows/{existing}", api_key, body)
        wf_id = existing
        action = "updated"
    else:
        status, payload = _api("POST", f"{base}/api/v1/workflows", api_key, body)
        wf_id = payload.get("id")
        action = "created"

    if status not in (200, 201) or not wf_id:
        print(json.dumps({"ok": False, "status": status, "payload": payload}, indent=2))
        return 1

    act_status, act_payload = _api(
        "POST", f"{base}/api/v1/workflows/{wf_id}/activate", api_key, {}
    )
    if act_status not in (200, 201):
        act_status, act_payload = _api(
            "PATCH", f"{base}/api/v1/workflows/{wf_id}", api_key, {"active": True}
        )

    print(
        json.dumps(
            {
                "ok": True,
                "action": action,
                "workflow_id": wf_id,
                "active": act_status in (200, 201),
                "webhook_url": f"{base}/webhook/{WEBHOOK_PATH}",
                "activate_status": act_status,
            },
            indent=2,
        )
    )
    return 0 if act_status in (200, 201) else 2


if __name__ == "__main__":
    raise SystemExit(main())
