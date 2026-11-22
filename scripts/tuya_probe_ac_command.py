#!/usr/bin/env python3
"""Create temp n8n workflow: token + POST /v1.0/devices/{ac_id}/commands (heat test)."""
from __future__ import annotations

import copy
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_AC = "bf7e0c495c637dc320vt0z"  # Air Conditioner 2 @ Smart IR Matute


def main() -> int:
    ac_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_AC
    if len(sys.argv) > 2 and sys.argv[2].startswith("{"):
        body = sys.argv[2]
    else:
        temp = int(sys.argv[2]) if len(sys.argv) > 2 else 21
        body = json.dumps({"commands": [{"code": "temp", "value": temp}]})
    base = os.environ["N8N_BASE_URL"].rstrip("/")
    key = os.environ["N8N_API_KEY"]
    tpl_id = os.environ.get("N8N_TUYA_TEMPLATE_WF", "HPaa9jGQmpDex41t")
    wf = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{base}/api/v1/workflows/{tpl_id}", headers={"X-N8N-API-KEY": key})
        ).read()
    )
    token = copy.deepcopy(next(n for n in wf["nodes"] if n["name"] == "Tuya Token"))
    send = copy.deepcopy(next(n for n in wf["nodes"] if n["name"] == "Enviar orden Tuya"))
    sched = copy.deepcopy(next(n for n in wf["nodes"] if n["name"] == "Cada hora"))
    sched.update({"id": str(uuid.uuid4()), "name": "Schedule MCP", "position": [-200, 0]})

    path = f"/v1.0/devices/{ac_id}/commands"
    js = (
        'const t=$("Tuya Token").first().json.result.access_token;\n'
        'if(!t) throw new Error("no token");\n'
        f'return [{{json:{{access_token:t,tuya_path:{json.dumps(path)},tuya_body:{json.dumps(body)}}}}}];'
    )

    token["id"] = str(uuid.uuid4())
    token["position"] = [100, 0]
    prep = {
        "id": str(uuid.uuid4()),
        "name": "Prep",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [350, 0],
        "parameters": {"jsCode": js},
    }
    send.update({"id": str(uuid.uuid4()), "name": "Conn", "position": [650, 0]})
    twf = {
        "name": f"TEMP AC test ON {ac_id[-8:]}",
        "nodes": [sched, token, prep, send],
        "connections": {
            "Schedule MCP": {"main": [[{"node": "Tuya Token", "type": "main", "index": 0}]]},
            "Tuya Token": {"main": [[{"node": "Prep", "type": "main", "index": 0}]]},
            "Prep": {"main": [[{"node": "Conn", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
    }
    req_create = urllib.request.Request(
        f"{base}/api/v1/workflows",
        data=json.dumps(twf).encode(),
        method="POST",
        headers={"X-N8N-API-KEY": key, "Content-Type": "application/json"},
    )
    try:
        created = json.loads(urllib.request.urlopen(req_create).read())
    except urllib.error.HTTPError as exc:
        print(exc.read().decode(), file=sys.stderr)
        raise
    wid = (created.get("data") or created)["id"]
    req_act = urllib.request.Request(
        f"{base}/api/v1/workflows/{wid}/activate",
        data=b"{}",
        method="POST",
        headers={"X-N8N-API-KEY": key, "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req_act)
    except urllib.error.HTTPError as exc:
        print("activate:", exc.read().decode(), file=sys.stderr)
    print(json.dumps({"workflow_id": wid, "ac_id": ac_id, "path": path, "body": body}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())