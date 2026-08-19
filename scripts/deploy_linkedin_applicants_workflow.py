#!/usr/bin/env python3
"""Deploy LinkedIn Hiring Applicants AI workflow to n8n Cloud."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from n8n_env import load_n8n_env

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILE = ROOT / "n8n" / "workflows" / "linkedin-hiring-applicants-ai.json"
WORKFLOW_NAME = "LinkedIn Hiring Applicants AI"


def request(method: str, url: str, api_key: str, payload: dict | None = None) -> dict:
    headers = {
        "Accept": "application/json",
        "X-N8N-API-KEY": api_key,
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        raise RuntimeError(f"{method} {url} -> {exc.code}: {detail}") from exc


def list_workflows(base_url: str, api_key: str) -> list[dict]:
    workflows: list[dict] = []
    cursor = None
    while True:
        url = f"{base_url.rstrip('/')}/api/v1/workflows?limit=100"
        if cursor:
            url += f"&cursor={cursor}"
        data = request("GET", url, api_key)
        workflows.extend(data.get("data", []))
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return workflows


def main() -> int:
    load_n8n_env()
    base_url = os.getenv("N8N_URL", "https://pmedia.app.n8n.cloud")
    api_key = os.getenv("N8N_REST_API_KEY") or os.getenv("N8N_API_KEY")
    if not api_key:
        print("Falta N8N_REST_API_KEY o N8N_API_KEY en entorno.", file=sys.stderr)
        return 1
    if not WORKFLOW_FILE.exists():
        print(f"No existe {WORKFLOW_FILE}", file=sys.stderr)
        return 1

    workflow = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
    workflow["name"] = WORKFLOW_NAME

    payload = {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": workflow.get("settings", {}),
    }

    existing = next((w for w in list_workflows(base_url, api_key) if w.get("name") == WORKFLOW_NAME), None)
    if existing:
        workflow_id = existing["id"]
        request("PUT", f"{base_url.rstrip('/')}/api/v1/workflows/{workflow_id}", api_key, payload)
        print(f"Workflow actualizado: {workflow_id}")
    else:
        created = request("POST", f"{base_url.rstrip('/')}/api/v1/workflows", api_key, payload)
        workflow_id = created.get("id")
        print(f"Workflow creado: {workflow_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
