#!/usr/bin/env python3
"""Create Mateo app-push template via n8n (same HTTP auth as main workflow)."""

from __future__ import annotations

import copy
import json
import os
import sys
import time
import uuid
import urllib.request

MATEO_WF = "DYJV0r0Z86pQIHH8"
TEMPLATE_BODY = {
    "name": "n8n Mateo AC on",
    "title": "Calefaccion Mateo",
    "content": "Aire Mateo encendido: temp ${temp}C objetivo ${target}C",
    "type": 1,
    "remark": "Aviso encendido aire Mateo via n8n",
}


def deploy_webhook(base: str, key: str, prep_js: str, http_post: bool) -> tuple[str, str]:
    headers = {"X-N8N-API-KEY": key, "Content-Type": "application/json"}
    src = json.loads(
        urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{MATEO_WF}", headers=headers)).read()
    )
    token = copy.deepcopy(next(n for n in src["nodes"] if n["name"] == "Tuya Token"))
    http = copy.deepcopy(next(n for n in src["nodes"] if n["name"] == "Enviar orden Tuya"))
    token["id"] = str(uuid.uuid4())
    token["position"] = [120, 0]
    http.update({"id": str(uuid.uuid4()), "name": "HTTP", "position": [560, 0]})
    prep = {
        "id": str(uuid.uuid4()),
        "name": "Prep",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [320, 0],
        "parameters": {"jsCode": prep_js.strip()},
    }
    wh_path = f"mateo-create-tpl-{uuid.uuid4().hex[:8]}"
    webhook = {
        "id": str(uuid.uuid4()),
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [-80, 0],
        "parameters": {"path": wh_path, "httpMethod": "GET", "responseMode": "responseNode"},
        "webhookId": str(uuid.uuid4()),
    }
    respond = {
        "id": str(uuid.uuid4()),
        "name": "Respond",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [800, 0],
        "parameters": {"respondWith": "json", "responseBody": "={{ $json }}"},
    }
    if http_post:
        http["parameters"] = {
            "method": "POST",
            "url": '={{ "https://openapi.tuyaeu.com" + $json.tuya_path }}',
            "authentication": "genericCredentialType",
            "genericAuthType": "httpCustomAuth",
            "sendBody": True,
            "contentType": "raw",
            "rawContentType": "application/json",
            "body": "={{ $json.tuya_body }}",
            "options": {"timeout": 15000},
        }
    else:
        http["parameters"] = {
            "url": '={{ "https://openapi.tuyaeu.com" + $json.tuya_path }}',
            "authentication": "genericCredentialType",
            "genericAuthType": "httpCustomAuth",
            "options": {"timeout": 15000},
        }
    twf = {
        "name": "TEMP Mateo create template",
        "nodes": [webhook, token, prep, http, respond],
        "connections": {
            "Webhook": {"main": [[{"node": "Tuya Token", "type": "main", "index": 0}]]},
            "Tuya Token": {"main": [[{"node": "Prep", "type": "main", "index": 0}]]},
            "Prep": {"main": [[{"node": "HTTP", "type": "main", "index": 0}]]},
            "HTTP": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
    }
    created = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/v1/workflows",
                data=json.dumps(twf).encode(),
                method="POST",
                headers=headers,
            )
        ).read()
    )
    wid = created["id"]
    urllib.request.urlopen(
        urllib.request.Request(f"{base}/api/v1/workflows/{wid}/activate", data=b"{}", method="POST", headers=headers)
    )
    time.sleep(2)
    url = f"{base}/webhook/{wh_path}"
    return wid, url


def call(url: str) -> dict:
    return json.loads(urllib.request.urlopen(url, timeout=60).read())


def cleanup(base: str, key: str, wid: str) -> None:
    headers = {"X-N8N-API-KEY": key}
    urllib.request.urlopen(
        urllib.request.Request(f"{base}/api/v1/workflows/{wid}/deactivate", data=b"{}", method="POST", headers=headers)
    )
    urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{wid}", method="DELETE", headers=headers))


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_BASE_URL and N8N_API_KEY required", file=sys.stderr)
        return 1
    body_literal = json.dumps(TEMPLATE_BODY, ensure_ascii=True)
    create_js = f"""
const t = $("Tuya Token").first().json.result.access_token;
if (!t) throw new Error("no token");
const body = {json.dumps(body_literal)};
return [{{
  json: {{
    access_token: t,
    tuya_path: "/v1.0/iot-03/msg-templates/app-notifications",
    tuya_body: body,
  }},
}}];
"""
    list_js = """
const t = $("Tuya Token").first().json.result.access_token;
if (!t) throw new Error("no token");
return [{ json: { access_token: t, tuya_path: "/v1.0/iot-03/msg-templates/app-notifications" } }];
"""
    wid, url = deploy_webhook(base, key, create_js, http_post=True)
    try:
        created = call(url)
        wid2, url2 = deploy_webhook(base, key, list_js, http_post=False)
        try:
            listed = call(url2)
        finally:
            cleanup(base, key, wid2)
    finally:
        cleanup(base, key, wid)

    tpl_id = None
    if isinstance(created, dict):
        tpl_id = (created.get("result") or {}).get("template_id")
    if not tpl_id and isinstance(listed, dict):
        for row in (listed.get("result") or {}).get("list") or []:
            if "Mateo" in str(row.get("name", "")):
                tpl_id = row.get("template_id")

    print(json.dumps({"create": created, "list": listed, "template_id": tpl_id}, indent=2, ensure_ascii=False))
    if tpl_id:
        # Update Mateo workflow config
        headers = {"X-N8N-API-KEY": key, "Content-Type": "application/json"}
        wf = json.loads(
            urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{MATEO_WF}", headers=headers)).read()
        )
        conf = next(n for n in wf["nodes"] if n["name"] == "Configuracion")
        js = conf["parameters"]["jsCode"]
        if 'push_template_id:""' in js:
            js = js.replace('push_template_id:""', f'push_template_id:"{tpl_id}"')
        if "notify_on_heat:false" in js:
            js = js.replace("notify_on_heat:false", "notify_on_heat:true")
        conf["parameters"]["jsCode"] = js
        settings = wf.get("settings") or {}
        allowed = {k: settings[k] for k in ("executionOrder", "timezone", "callerPolicy") if k in settings}
        allowed["saveManualExecutions"] = True
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/v1/workflows/{MATEO_WF}",
                data=json.dumps(
                    {"name": wf["name"], "nodes": wf["nodes"], "connections": wf["connections"], "settings": allowed}
                ).encode(),
                method="PUT",
                headers=headers,
            )
        )
        print(json.dumps({"mateo_config_updated": True, "template_id": tpl_id}))
    return 0 if tpl_id else 2


if __name__ == "__main__":
    raise SystemExit(main())