#!/usr/bin/env python3
"""Create Smart Life app-push template (reads TUYA_ACCESS_ID + TUYA_ACCESS_SECRET from env)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request

BASE = "https://openapi.tuyaeu.com"
TEMPLATE = {
    "name": "n8n Mateo AC on",
    "title": "Calefaccion Mateo",
    "content": "Aire Mateo encendido: ${temp}C objetivo ${target}C",
    "type": 1,
    "remark": "Aviso encendido aire Mateo via n8n",
}


def _keys() -> tuple[str, str]:
    cid = os.environ.get("TUYA_ACCESS_ID") or os.environ.get("TUYA_CLIENT_ID")
    sec = os.environ.get("TUYA_ACCESS_SECRET") or os.environ.get("TUYA_CLIENT_SECRET")
    if not cid or not sec:
        raise SystemExit("Set TUYA_ACCESS_ID and TUYA_ACCESS_SECRET")
    return cid, sec


def sign(
    cid: str, sec: str, method: str, path: str, body: str, token: str | None = None
) -> dict[str, str]:
    t = str(int(time.time() * 1000))
    content_hash = hashlib.sha256(body.encode() or b"").hexdigest()
    sts = f"{method}\n{content_hash}\n\n{path}"
    base = cid + token + t + sts if token else cid + t + sts
    headers = {
        "client_id": cid,
        "sign": hmac.new(sec.encode(), base.encode(), hashlib.sha256).hexdigest().upper(),
        "t": t,
        "sign_method": "HMAC-SHA256",
    }
    if token:
        headers["access_token"] = token
    return headers


def api(method: str, path: str, body: str, cid: str, sec: str, token: str | None) -> dict:
    headers = {**sign(cid, sec, method, path, body, token), "Content-Type": "application/json"}
    req = urllib.request.Request(BASE + path, data=body.encode() if body else None, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read())


def main() -> int:
    cid, sec = _keys()
    token_data = api("GET", "/v1.0/token?grant_type=1", "", cid, sec, None)
    if not token_data.get("success"):
        print(json.dumps({"step": "token", "response": token_data}))
        return 1
    token = token_data["result"]["access_token"]

    list_path = "/v1.0/iot-03/msg-templates/app-notifications"
    listed = api("GET", list_path, "", cid, sec, token)
    existing = None
    for row in (listed.get("result") or {}).get("list") or []:
        if "Mateo" in str(row.get("name", "")):
            existing = row.get("template_id")
            break

    created = None
    if not existing:
        create_path = "/v1.0/iot-03/msg-templates/app-notifications"
        body = json.dumps(TEMPLATE, separators=(",", ":"), ensure_ascii=True)
        created = api("POST", create_path, body, cid, sec, token)

    tpl_id = existing
    if not tpl_id and isinstance(created, dict) and created.get("success"):
        tpl_id = (created.get("result") or {}).get("template_id")

    out = {
        "list_ok": listed.get("success"),
        "list_total": (listed.get("result") or {}).get("total"),
        "existing_template_id": existing,
        "create_ok": created.get("success") if created else None,
        "create_code": created.get("code") if created and not created.get("success") else None,
        "create_msg": created.get("msg") if created and not created.get("success") else None,
        "template_id": tpl_id,
    }
    print(json.dumps(out, indent=2))
    return 0 if tpl_id else 2


if __name__ == "__main__":
    raise SystemExit(main())