#!/usr/bin/env python3
"""Create/list Tuya app notification template via temporary n8n webhook workflow."""

from __future__ import annotations

import copy
import json
import os
import sys
import time
import uuid
import urllib.request

TEMPLATE_TITLE = "Calefacción Mateo"
TEMPLATE_CONTENT = "Aire Mateo encendido: ${temp}°C (objetivo ${target}°C)."
TEMPLATE_NAME = "n8n Mateo AC encendido"


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_BASE_URL and N8N_API_KEY required", file=sys.stderr)
        return 1
    headers = {"X-N8N-API-KEY": key, "Content-Type": "application/json"}
    src = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{base}/api/v1/workflows/DYJV0r0Z86pQIHH8", headers=headers)
        ).read()
    )
    token = copy.deepcopy(next(n for n in src["nodes"] if n["name"] == "Tuya Token"))
    http = copy.deepcopy(next(n for n in src["nodes"] if n["name"] == "Enviar orden Tuya"))
    wh_id = str(uuid.uuid4())
    prep_id = str(uuid.uuid4())
    http_id = str(uuid.uuid4())
    respond_id = str(uuid.uuid4())

    list_path = "/v1.0/iot-03/msg-templates/app-notifications?page_no=1&page_size=20"
    create_body = json.dumps(
        {
            "name": TEMPLATE_NAME,
            "title": TEMPLATE_TITLE,
            "content": TEMPLATE_CONTENT,
            "type": 1,
            "remark": "Aviso al encender aire Mateo via n8n (habitacion Mateo)",
        }
    )

    prep_js = f"""
const action=$json.query?.action||"list";
const t=$("Tuya Token").first().json.result.access_token;
if(!t) throw new Error("no token");
if(action==="create"){{
  return [{{json:{{
    access_token:t,
    tuya_path:"/v1.0/iot-03/msg-templates/app-notifications",
    tuya_body:{json.dumps(create_body)}
  }}}}];
}}
return [{{json:{{access_token:t,tuya_path:"{list_path}"}}}}];
""".strip()

    webhook = {
        "id": wh_id,
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [-200, 0],
        "parameters": {"path": f"mateo-push-template-{uuid.uuid4().hex[:8]}", "httpMethod": "GET", "responseMode": "responseNode"},
        "webhookId": str(uuid.uuid4()),
    }
    token["id"] = str(uuid.uuid4())
    token["position"] = [100, 0]
    prep = {
        "id": prep_id,
        "name": "Prep",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [350, 0],
        "parameters": {"jsCode": prep_js},
    }
    http.update({"id": http_id, "name": "Tuya", "position": [600, 0]})
    http["parameters"] = {
        **http.get("parameters", {}),
        "method": "={{ $json.tuya_body ? 'POST' : 'GET' }}",
        "url": '={{ "https://openapi.tuyaeu.com" + $json.tuya_path }}',
        "sendBody": True,
        "contentType": "raw",
        "rawContentType": "application/json",
        "body": "={{ $json.tuya_body || '' }}",
    }
    respond = {
        "id": respond_id,
        "name": "Respond",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [850, 0],
        "parameters": {"respondWith": "json", "responseBody": "={{ $json }}"},
    }
    twf = {
        "name": "TEMP Mateo push template",
        "nodes": [webhook, token, prep, http, respond],
        "connections": {
            "Webhook": {"main": [[{"node": "Tuya Token", "type": "main", "index": 0}]]},
            "Tuya Token": {"main": [[{"node": "Prep", "type": "main", "index": 0}]]},
            "Prep": {"main": [[{"node": "Tuya", "type": "main", "index": 0}]]},
            "Tuya": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
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
    wid = (created.get("data") or created)["id"]
    urllib.request.urlopen(
        urllib.request.Request(f"{base}/api/v1/workflows/{wid}/activate", data=b"{}", method="POST", headers=headers)
    )
    time.sleep(2)
    wf = json.loads(urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{wid}", headers=headers)).read())
    path = next(n for n in wf["nodes"] if n["name"] == "Webhook")["parameters"]["path"]
    prod_url = f"{base}/webhook/{path}"
    test_url = f"{base}/webhook-test/{path}"

    out = {}
    for label, url_suffix in [("list", list_path), ("create", "create")]:
        for url in (prod_url, test_url):
            try:
                q = f"?action={label}" if label != "list" else ""
                resp = urllib.request.urlopen(urllib.request.Request(url + q, method="GET"), timeout=45)
                out[label] = json.loads(resp.read())
                break
            except Exception as e:
                out[f"{label}_err_{url.split('/')[-2]}"] = str(e)
                time.sleep(1)

    urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{wid}/deactivate", data=b"{}", method="POST", headers=headers))
    urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{wid}", method="DELETE", headers=headers))

    tpl_id = None
    if isinstance(out.get("create"), dict) and out["create"].get("result", {}).get("template_id"):
        tpl_id = out["create"]["result"]["template_id"]
    if not tpl_id and isinstance(out.get("list"), dict):
        for row in out["list"].get("result", {}).get("datas", []) or out["list"].get("result", {}).get("data", []) or []:
            if TEMPLATE_NAME in str(row.get("name", "")) and row.get("template_id"):
                tpl_id = row["template_id"]
                break

    print(json.dumps({"template_id": tpl_id, "probe": out}, indent=2))
    return 0 if tpl_id else 2


if __name__ == "__main__":
    raise SystemExit(main())