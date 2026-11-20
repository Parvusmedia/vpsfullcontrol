#!/usr/bin/env python3
"""Configure SmartLife error workflow Telegram alerts (uses VPS env; no secrets in stdout)."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ERROR_WORKFLOW_ID = "EltiT3iY5IoJY3yU"
MAIN_WORKFLOW_ID = "HPaa9jGQmpDex41t"
CREDENTIAL_NAME = "Fly456 Support Bot (SmartLife alerts)"
FLY456_ENV = Path("/opt/apps/fly456bot/.env")

TEXT_EXPR = (
    "={{ '❌ Error radiador buhardilla (Luca)\\n' "
    "+ 'Workflow: ' + ($json.workflow?.name || 'n/d') + '\\n' "
    "+ 'Ejecución: ' + ($json.execution?.id || 'n/d') + '\\n' "
    "+ 'Nodo: ' + ($json.execution?.lastNodeExecuted || 'n/d') + '\\n' "
    "+ 'Mensaje: ' + ($json.execution?.error?.message || $json.trigger?.error?.message || 'sin detalle') }}"
)


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip("\"'")
    return out


def api_request(method: str, url: str, key: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"X-N8N-API-KEY": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:500]}
        return e.code, payload


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", os.environ.get("N8N_URL", "")).rstrip("/")
    key = os.environ.get("N8N_API_KEY", "") or os.environ.get("N8N_REST_API_KEY", "")
    if not base or not key:
        print(json.dumps({"error": "Falta N8N_BASE_URL y N8N_API_KEY"}))
        return 1

    if not FLY456_ENV.is_file():
        print(json.dumps({"error": f"No existe {FLY456_ENV}"}))
        return 1

    fly = parse_env(FLY456_ENV)
    token = fly.get("TELEGRAM_SUPPORT_BOT_TOKEN") or fly.get("TELEGRAM_BOT_TOKEN")
    chat_id = fly.get("OWNER_NOTIFY_CHAT_ID") or fly.get("FLY456_HEALTHCHECK_TELEGRAM_TARGET")
    if not token or not chat_id:
        print(json.dumps({"error": "Falta token o chat_id en fly456 .env"}))
        return 1

    tg_url = f"https://api.telegram.org/bot{token}/getChat?{urllib.parse.urlencode({'chat_id': chat_id})}"
    with urllib.request.urlopen(tg_url, timeout=20) as r:
        chat = json.load(r)
    username = (chat.get("result") or {}).get("username")

    cred_id: str | None = None
    status, err_wf = api_request("GET", f"{base}/api/v1/workflows/{ERROR_WORKFLOW_ID}", key)
    if status == 200:
        err_body = err_wf.get("data", err_wf) if isinstance(err_wf, dict) else {}
        for node in err_body.get("nodes") or []:
            tg = (node.get("credentials") or {}).get("telegramApi")
            if isinstance(tg, dict) and tg.get("id"):
                cred_id = str(tg["id"])
                break
    if not cred_id:
        status, cred_resp = api_request(
            "POST",
            f"{base}/api/v1/credentials",
            key,
            {"name": CREDENTIAL_NAME, "type": "telegramApi", "data": {"accessToken": token}},
        )
        if status in (200, 201):
            created = (cred_resp.get("data") if isinstance(cred_resp, dict) else None) or cred_resp
            if isinstance(created, dict):
                cred_id = str(created.get("id") or "")
        if not cred_id:
            print(json.dumps({"error": "No se pudo crear credencial", "status": status, "response": cred_resp}))
            return 1

    cred_ref = {"id": cred_id, "name": CREDENTIAL_NAME}

    status, wf_resp = api_request("GET", f"{base}/api/v1/workflows/{ERROR_WORKFLOW_ID}", key)
    if status != 200:
        print(json.dumps({"error": "No se leyó workflow alertas", "status": status}))
        return 1
    body = wf_resp.get("data", wf_resp) if isinstance(wf_resp, dict) else {}

    nodes = []
    for node in body.get("nodes") or []:
        n = dict(node)
        if (n.get("type") or "").endswith("telegram"):
            n["name"] = "Telegram alerta"
            n["parameters"] = {
                "chatId": str(chat_id),
                "text": TEXT_EXPR,
                "additionalFields": {"appendAttribution": False},
            }
            n["credentials"] = {"telegramApi": cred_ref}
            n["typeVersion"] = 1.2
        nodes.append(n)

    put_payload: dict[str, object] = {
        "name": body.get("name"),
        "nodes": nodes,
        "connections": body.get("connections"),
        "settings": body.get("settings") or {"executionOrder": "v1"},
    }
    if body.get("staticData") is not None:
        put_payload["staticData"] = body.get("staticData")

    status, put_resp = api_request("PUT", f"{base}/api/v1/workflows/{ERROR_WORKFLOW_ID}", key, put_payload)
    if status != 200:
        print(json.dumps({"error": "PUT workflow alertas falló", "status": status, "response": put_resp}))
        return 1

    status, _ = api_request("POST", f"{base}/api/v1/workflows/{ERROR_WORKFLOW_ID}/activate", key, {})
    activated = status in (200, 201)

    status, main_resp = api_request("GET", f"{base}/api/v1/workflows/{MAIN_WORKFLOW_ID}", key)
    main_body = main_resp.get("data", main_resp) if isinstance(main_resp, dict) else {}
    settings = dict(main_body.get("settings") or {})
    linked = settings.get("errorWorkflow") == ERROR_WORKFLOW_ID
    if status == 200 and not linked:
        settings["errorWorkflow"] = ERROR_WORKFLOW_ID
        main_put = {
            "name": main_body.get("name"),
            "nodes": main_body.get("nodes"),
            "connections": main_body.get("connections"),
            "settings": settings,
        }
        if main_body.get("staticData") is not None:
            main_put["staticData"] = main_body.get("staticData")
        link_status, _ = api_request("PUT", f"{base}/api/v1/workflows/{MAIN_WORKFLOW_ID}", key, main_put)
        linked = link_status == 200

    test_msg = "✅ SmartLife buhardilla: alertas de error n8n → Telegram (@etichauer) listas."
    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
    send_data = urllib.parse.urlencode({"chat_id": chat_id, "text": test_msg}).encode()
    with urllib.request.urlopen(urllib.request.Request(send_url, data=send_data, method="POST"), timeout=20) as r:
        sent = json.load(r).get("ok")

    print(
        json.dumps(
            {
                "credential_id": cred_ref["id"],
                "chat_id": str(chat_id),
                "telegram_username": username,
                "error_workflow_updated": True,
                "error_workflow_active": activated,
                "main_error_workflow_linked": linked,
                "test_message_sent": bool(sent),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())