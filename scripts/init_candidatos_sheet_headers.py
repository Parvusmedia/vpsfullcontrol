#!/usr/bin/env python3
"""Crea cabeceras en Google Sheet via webhook n8n temporal."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from n8n_env import load_n8n_env  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILE = ROOT / "n8n" / "workflows" / "init-candidatos-sheet-headers.json"
WORKFLOW_NAME = "Init Candidatos Sheet Headers"
WEBHOOK_PATH = "init-candidatos-sheet-headers"
SHEET_ID = "1a6dDwT5VWQH5YMGx1kX-7HVVnozD-bspuzPLThjL1bQ"


def api(method: str, url: str, api_key: str, payload: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "X-N8N-API-KEY": api_key}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def main() -> int:
    load_n8n_env()
    base = os.getenv("N8N_URL", "https://pmedia.app.n8n.cloud").rstrip("/")
    api_key = os.getenv("N8N_REST_API_KEY") or os.getenv("N8N_API_KEY")
    if not api_key:
        print("Falta N8N_API_KEY", file=sys.stderr)
        return 1

    workflow = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
    payload = {
        "name": WORKFLOW_NAME,
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": workflow.get("settings", {}),
    }

    existing = None
    cursor = None
    while True:
        url = f"{base}/api/v1/workflows?limit=100"
        if cursor:
            url += f"&cursor={cursor}"
        data = api("GET", url, api_key)
        for item in data.get("data", []):
            if item.get("name") == WORKFLOW_NAME:
                existing = item
                break
        if existing or not data.get("nextCursor"):
            break
        cursor = data.get("nextCursor")

    if existing:
        wf_id = existing["id"]
        api("PUT", f"{base}/api/v1/workflows/{wf_id}", api_key, payload)
    else:
        created = api("POST", f"{base}/api/v1/workflows", api_key, payload)
        wf_id = created["id"]

    api("POST", f"{base}/api/v1/workflows/{wf_id}/activate", api_key, {})
    time.sleep(2)

    webhook_url = f"{base}/webhook/{WEBHOOK_PATH}"
    req = urllib.request.Request(webhook_url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            print("headers_init_status", response.status)
            print(response.read()[:500].decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        print("headers_init_error", exc.code, exc.read()[:500].decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    api("POST", f"{base}/api/v1/workflows/{wf_id}/deactivate", api_key, {})
    print(f"sheet_id={SHEET_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
