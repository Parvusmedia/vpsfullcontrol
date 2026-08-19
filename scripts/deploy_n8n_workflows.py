#!/usr/bin/env python3
"""Deploy workflows listados en config/n8n-deploy.json a n8n Cloud."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from deploy_linkedin_applicants_workflow import list_workflows, request  # noqa: E402
from n8n_env import load_n8n_env  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_CONFIG = ROOT / "config" / "n8n-deploy.json"


def deploy_workflow(base_url: str, api_key: str, workflow_file: Path, workflow_name: str, workflow_id: str | None) -> str:
    workflow = json.loads(workflow_file.read_text(encoding="utf-8"))
    workflow["name"] = workflow_name

    target_id = workflow_id
    if not target_id:
        existing = next((w for w in list_workflows(base_url, api_key) if w.get("name") == workflow_name), None)
        target_id = existing["id"] if existing else None

    if target_id:
        remote = request("GET", f"{base_url.rstrip('/')}/api/v1/workflows/{target_id}", api_key)
        remote_nodes = {n.get("name"): n for n in remote.get("nodes", []) if isinstance(n, dict)}
        for node in workflow.get("nodes", []):
            if node.get("name") != "Config" or node.get("name") not in remote_nodes:
                continue
            remote_assignments = {
                a.get("name"): a.get("value")
                for a in remote_nodes["Config"].get("parameters", {})
                .get("assignments", {})
                .get("assignments", [])
                if isinstance(a, dict)
            }
            for assignment in node.get("parameters", {}).get("assignments", {}).get("assignments", []):
                name = assignment.get("name")
                if not assignment.get("value") and remote_assignments.get(name):
                    assignment["value"] = remote_assignments[name]

    payload = {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": {
            **workflow.get("settings", {}),
            "availableInMCP": True,
        },
    }

    target_id = workflow_id
    if not target_id:
        existing = next((w for w in list_workflows(base_url, api_key) if w.get("name") == workflow_name), None)
        target_id = existing["id"] if existing else None

    if target_id:
        request("PUT", f"{base_url.rstrip('/')}/api/v1/workflows/{target_id}", api_key, payload)
        return target_id

    created = request("POST", f"{base_url.rstrip('/')}/api/v1/workflows", api_key, payload)
    return str(created.get("id", ""))


def main() -> int:
    load_n8n_env()
    base_url = os.getenv("N8N_URL", "https://pmedia.app.n8n.cloud")
    api_key = os.getenv("N8N_REST_API_KEY") or os.getenv("N8N_API_KEY")
    if not api_key:
        print("Falta N8N_API_KEY. Copia config/n8n.local.env.example a config/n8n.local.env", file=sys.stderr)
        return 1
    if not DEPLOY_CONFIG.exists():
        print(f"No existe {DEPLOY_CONFIG}", file=sys.stderr)
        return 1

    config = json.loads(DEPLOY_CONFIG.read_text(encoding="utf-8"))
    for entry in config.get("workflows", []):
        workflow_file = ROOT / entry["file"]
        workflow_name = entry.get("n8n_name") or workflow_file.stem
        workflow_id = entry.get("workflow_id")
        deployed_id = deploy_workflow(base_url, api_key, workflow_file, workflow_name, workflow_id)
        print(f"{workflow_name}: {deployed_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
