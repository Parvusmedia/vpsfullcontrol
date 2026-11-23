#!/usr/bin/env python3
"""One-shot webhook to probe Tuya push APIs using same HTTP auth as Mateo workflow."""

from __future__ import annotations

import copy
import json
import os
import sys
import time
import uuid
import urllib.parse
import urllib.request

MATEO_WF = "DYJV0r0Z86pQIHH8"
UID = "eu1698169819562OGqFr"
BIZ = 18


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    tpl = (os.environ.get("SMARTLIFE_PUSH_TEMPLATE_ID") or os.environ.get("PUSH_TEMPLATE_ID") or "").strip()
    if not base or not key:
        print("N8N_BASE_URL and N8N_API_KEY required", file=sys.stderr)
        return 1

    headers = {"X-N8N-API-KEY": key, "Content-Type": "application/json"}
    src = json.loads(
        urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{MATEO_WF}", headers=headers)).read()
    )
    token = copy.deepcopy(next(n for n in src["nodes"] if n["name"] == "Tuya Token"))
    http = copy.deepcopy(next(n for n in src["nodes"] if n["name"] == "Enviar orden Tuya"))
    token["id"] = str(uuid.uuid4())
    token["position"] = [120, 0]
    http.update({"id": str(uuid.uuid4()), "name": "Tuya HTTP", "position": [640, 0]})

    prep_js = r"""
const wh = $("Webhook").first().json;
const q = wh.query || wh.params || {};
const action = q.action || "list_templates";
const t = $("Tuya Token").first().json.result.access_token;
if (!t) throw new Error("Tuya token failed");
const c = { uid: "eu1698169819562OGqFr", biz_type: 18 };
const templateId = String(q.template_id || "").trim();
if (action === "device_check") {
  return [{ json: { access_token: t, tuya_path: "/v1.0/devices/bf7634a37dd4e94e17r4pg" } }];
}
if (action === "push" && templateId) {
  const body = {
    uid: c.uid,
    biz_type: c.biz_type,
    template_id: templateId,
    template_param: JSON.stringify({ room: "Mateo", temp: "20", target: "21" }),
  };
  return [{
    json: {
      access_token: t,
      tuya_path: "/v1.0/iot-03/messages/app-notifications/actions/push",
      tuya_body: JSON.stringify(body),
      tuya_method: "POST",
    },
  }];
}
if (action === "create_template") {
  const body = {
    name: "n8n Mateo AC encendido",
    title: "Calefacción Mateo",
    content: "Aire Mateo encendido: ${temp}°C (objetivo ${target}°C).",
    type: 1,
    remark: "Aviso encendido aire Mateo via n8n",
  };
  return [{
    json: {
      access_token: t,
      tuya_path: "/v1.0/iot-03/msg-templates/app-notifications",
      tuya_body: JSON.stringify(body),
      tuya_method: "POST",
    },
  }];
}
return [{ json: { access_token: t, tuya_path: "/v1.0/iot-03/msg-templates/app-notifications" } }];
""".strip()

    prep = {
        "id": str(uuid.uuid4()),
        "name": "Prep",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [360, 0],
        "parameters": {"jsCode": prep_js, "mode": "runOnceForAllItems"},
    }
    wh_path = f"mateo-push-test-{uuid.uuid4().hex[:10]}"
    webhook = {
        "id": str(uuid.uuid4()),
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [-120, 0],
        "parameters": {
            "path": wh_path,
            "httpMethod": "GET",
            "responseMode": "responseNode",
            "options": {},
        },
        "webhookId": str(uuid.uuid4()),
    }
    params = {k: v for k, v in http.get("parameters", {}).items() if k not in ("sendBody", "contentType", "rawContentType", "body", "method")}
    params.update(
        {
            "method": "={{ $json.tuya_method || 'GET' }}",
            "url": '={{ "https://openapi.tuyaeu.com" + $json.tuya_path }}',
            "sendBody": "={{ !!$json.tuya_body }}",
            "contentType": "raw",
            "rawContentType": "application/json",
            "body": "={{ $json.tuya_body || '' }}",
        }
    )
    http["parameters"] = params
    respond = {
        "id": str(uuid.uuid4()),
        "name": "Respond",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [900, 0],
        "parameters": {"respondWith": "json", "responseBody": "={{ $json }}"},
    }
    twf = {
        "name": "TEMP Mateo push test",
        "nodes": [webhook, token, prep, http, respond],
        "connections": {
            "Webhook": {"main": [[{"node": "Tuya Token", "type": "main", "index": 0}]]},
            "Tuya Token": {"main": [[{"node": "Prep", "type": "main", "index": 0}]]},
            "Prep": {"main": [[{"node": "Tuya HTTP", "type": "main", "index": 0}]]},
            "Tuya HTTP": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
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
    prod = f"{base}/webhook/{wh_path}"
    test = f"{base}/webhook-test/{wh_path}"
    out: dict = {"webhook": prod, "template_env": tpl or None}

    for action in ("device_check", "list_templates", "create_template"):
        qs = urllib.parse.urlencode({"action": action})
        for label, url in (("prod", prod), ("test", test)):
            try:
                out[f"{action}_{label}"] = json.loads(urllib.request.urlopen(f"{url}?{qs}", timeout=60).read())
                break
            except Exception as e:
                out[f"{action}_{label}_err"] = str(e)

    if tpl:
        qs = urllib.parse.urlencode({"action": "push", "template_id": tpl})
        for label, url in (("prod", prod), ("test", test)):
            try:
                out[f"push_{label}"] = json.loads(urllib.request.urlopen(f"{url}?{qs}", timeout=60).read())
                break
            except Exception as e:
                out[f"push_{label}_err"] = str(e)
    else:
        out["push"] = "skipped_no_template_id_in_env"

    urllib.request.urlopen(
        urllib.request.Request(f"{base}/api/v1/workflows/{wid}/deactivate", data=b"{}", method="POST", headers=headers)
    )
    urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/workflows/{wid}", method="DELETE", headers=headers))

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())