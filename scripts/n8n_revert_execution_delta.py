#!/usr/bin/env python3
"""Remove Delta gate (ops) nodes injected by n8n_apply_execution_delta.py."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

PREFIX = "Delta gate (ops)"

TARGET_WORKFLOW_IDS = [
    "7mjdfYNYECQi9tTR",
    "NjgWkbjZpBSh1J3f",
    "LUAErUvtnTx65hPe",
    "JTg8kZYug7H5QkiE",
    "oHdmZjTz11iDAAT4",
    "0mhSYR5Alx2KVdtH",
    "NTrKmynexdrPWXwf",
    "wR7aXsGy9UKc2cA2",
    "7A1xSnh6x5QeynjU",
    "cqTvAfPOWqa6Vtqj",
]


def _request(method: str, url: str, api_key: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    headers = {"Accept": "application/json", "Content-Type": "application/json", "X-N8N-API-KEY": api_key}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:500]}
        return exc.code, payload


def _compute_name_for_wait(wait_name: str) -> str:
    return wait_name.replace("— wait", "— compute")


def revert_workflow(base_url: str, api_key: str, workflow_id: str, dry_run: bool) -> dict[str, Any]:
    status, payload = _request("GET", f"{base_url}/api/v1/workflows/{workflow_id}", api_key)
    if status != 200:
        return {"workflow_id": workflow_id, "ok": False, "error": payload}

    wf = payload.get("data", payload)
    nodes: list[dict[str, Any]] = list(wf.get("nodes") or [])
    connections: dict[str, Any] = dict(wf.get("connections") or {})

    wait_nodes = [n["name"] for n in nodes if (n.get("name") or "").startswith(PREFIX) and "wait" in (n.get("name") or "").lower()]
    if not wait_nodes:
        return {"workflow_id": workflow_id, "name": wf.get("name"), "ok": True, "changes": ["no_delta_gates"]}

    changes: list[str] = []
    gate_names: set[str] = set()

    for wname in wait_nodes:
        cname = _compute_name_for_wait(wname)
        gate_names.update({wname, cname})
        downstream = connections.get(wname, {}).get("main", [[]])[0]
        if not downstream:
            continue
        for src, conn in connections.items():
            if src in gate_names:
                continue
            main = conn.get("main") or []
            new_main = []
            touched = False
            for branch in main:
                new_branch = []
                for edge in branch or []:
                    if isinstance(edge, dict) and edge.get("node") == cname:
                        new_branch.extend(downstream)
                        touched = True
                    else:
                        new_branch.append(edge)
                new_main.append(new_branch)
            if touched:
                connections[src] = {"main": new_main}
                changes.append(f"rewired:{src}->{downstream[0].get('node')}")

    for gname in gate_names:
        connections.pop(gname, None)

    nodes = [n for n in nodes if (n.get("name") or "") not in gate_names]
    changes.append(f"removed_gates:{len(gate_names)}")

    result = {"workflow_id": workflow_id, "name": wf.get("name"), "ok": True, "changes": changes}
    if dry_run:
        result["dry_run"] = True
        return result

    raw_settings = wf.get("settings") or {}
    settings: dict[str, Any] = {"executionOrder": raw_settings.get("executionOrder") or "v1"}
    if isinstance(raw_settings.get("timezone"), str):
        settings["timezone"] = raw_settings["timezone"]
    if isinstance(raw_settings.get("executionTimeout"), int):
        settings["executionTimeout"] = raw_settings["executionTimeout"]

    put_status, put_payload = _request(
        "PUT",
        f"{base_url}/api/v1/workflows/{workflow_id}",
        api_key,
        {"name": wf.get("name"), "nodes": nodes, "connections": connections, "settings": settings},
    )
    result["put_status"] = put_status
    if put_status != 200:
        result["ok"] = False
        result["error"] = put_payload
    return result


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    base_url = os.getenv("N8N_URL", "").rstrip("/")
    api_key = os.getenv("N8N_REST_API_KEY")
    if not api_key:
        legacy = os.getenv("N8N_API_KEY") or ""
        if legacy.startswith("n8n_api_"):
            api_key = legacy
    if not base_url or not api_key:
        print(json.dumps({"error": "Requiere N8N_URL y N8N_REST_API_KEY."}, indent=2))
        return 1

    results = [revert_workflow(base_url, api_key, wid, dry_run) for wid in TARGET_WORKFLOW_IDS]
    print(json.dumps({"ok": all(r.get("ok") for r in results), "results": results}, indent=2, ensure_ascii=False))
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    main()
