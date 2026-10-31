#!/usr/bin/env python3
"""Inject min-interval + jitter delta gates into selected n8n workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
import urllib.error
import urllib.request
from typing import Any

# workflow_id -> seconds (min spacing between run starts, random jitter cap)
DELTA_TARGETS: dict[str, dict[str, int | str]] = {
    "7mjdfYNYECQi9tTR": {"min": 5, "jitter": 4, "note": "MPA WhatsAPP Biz / Gallabox"},
    "NjgWkbjZpBSh1J3f": {"min": 5, "jitter": 4, "note": "MPA WhatsApp lead recibido"},
    "LUAErUvtnTx65hPe": {"min": 15, "jitter": 10, "note": "Apify AAPEX"},
    "JTg8kZYug7H5QkiE": {"min": 15, "jitter": 10, "note": "Apify Antevenio"},
    "oHdmZjTz11iDAAT4": {"min": 8, "jitter": 5, "note": "Prosegur AR Meta/TikTok webhook"},
    "0mhSYR5Alx2KVdtH": {"min": 20, "jitter": 15, "note": "LinkedIn queue processor"},
    "NTrKmynexdrPWXwf": {"min": 45, "jitter": 20, "note": "Prosegur AR confirma envios"},
    "wR7aXsGy9UKc2cA2": {"min": 60, "jitter": 30, "note": "NextConvers step2 throttled"},
    "7A1xSnh6x5QeynjU": {"min": 30, "jitter": 15, "note": "TefSeguros NocoDB → Pipedrive"},
    "cqTvAfPOWqa6Vtqj": {"min": 10, "jitter": 5, "note": "WhatsApp Emi Unipile"},
}

COMPUTE_NODE_NAME = "Delta gate (ops) — compute"
WAIT_NODE_NAME = "Delta gate (ops) — wait"

ALLOWED_WORKFLOW_SETTINGS = {
    "executionOrder",
    "timezone",
    "saveManualExecutions",
    "saveDataErrorExecution",
    "saveDataSuccessExecution",
    "executionTimeout",
    "errorWorkflow",
    "callerPolicy",
}

TRIGGER_TYPES = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.formTrigger",
    "n8n-nodes-base.emailReadImap",
    "n8n-nodes-base.cron",
}


def _js_code(min_delta: int, jitter: int) -> str:
    return f"""// Delta gate (ops): min spacing + jitter before third-party calls
const MIN_DELTA_SECONDS = {min_delta};
const JITTER_MAX_SECONDS = {jitter};

const sd = $getWorkflowStaticData('global');
if (!sd.__deltaGate) sd.__deltaGate = {{ lastReservedMs: 0 }};

const now = Date.now();
const elapsedSec = sd.__deltaGate.lastReservedMs
  ? (now - sd.__deltaGate.lastReservedMs) / 1000
  : MIN_DELTA_SECONDS + 1;

const jitter = JITTER_MAX_SECONDS > 0
  ? Math.floor(Math.random() * (JITTER_MAX_SECONDS + 1))
  : 0;

let waitSeconds = 0;
if (elapsedSec < MIN_DELTA_SECONDS) {{
  waitSeconds = Math.ceil(MIN_DELTA_SECONDS - elapsedSec) + jitter;
}} else if (jitter > 0) {{
  waitSeconds = jitter;
}}

sd.__deltaGate.lastReservedMs = now + waitSeconds * 1000;

return $input.all().map((item) => ({{
  json: {{
    ...item.json,
    __delta_wait_seconds: waitSeconds,
  }},
}}));
"""


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


def _trigger_nodes(nodes: list[dict[str, Any]], connections: dict[str, Any]) -> list[dict[str, Any]]:
    incoming: set[str] = set()
    for src, conn in connections.items():
        for main_list in conn.get("main", []) or []:
            for edge in main_list or []:
                if isinstance(edge, dict) and edge.get("node"):
                    incoming.add(edge["node"])
    triggers = []
    for node in nodes:
        name = node.get("name")
        ntype = node.get("type") or ""
        if name in incoming:
            continue
        if ntype in TRIGGER_TYPES or ntype.endswith("Trigger") or "trigger" in ntype.lower():
            triggers.append(node)
    return triggers


def _suffix_from_trigger(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")
    return (cleaned[:28] or "trigger").lower()


def _node_names(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(n.get("name")): n for n in nodes if n.get("name")}


def _ensure_delta_nodes(
    workflow: dict[str, Any], min_delta: int, jitter: int
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    nodes: list[dict[str, Any]] = list(workflow.get("nodes") or [])
    connections: dict[str, Any] = dict(workflow.get("connections") or {})
    changes: list[str] = []
    by_name = _node_names(nodes)
    triggers = _trigger_nodes(nodes, connections)

    if len(triggers) <= 1:
        gate_names = (COMPUTE_NODE_NAME, WAIT_NODE_NAME)
    else:
        gate_names = None

    for trigger in triggers:
        tname = trigger.get("name")
        if not tname:
            continue
        main = connections.get(tname, {}).get("main") or []
        if not main or not main[0]:
            continue
        original_edges = main[0]
        if any((by_name.get(e.get("node", ""), {}).get("name") or "").startswith("Delta gate (ops)") for e in original_edges if isinstance(e, dict)):
            continue

        if gate_names:
            cname, wname = gate_names
        else:
            suffix = _suffix_from_trigger(tname)
            cname = f"{COMPUTE_NODE_NAME} [{suffix}]"
            wname = f"{WAIT_NODE_NAME} [{suffix}]"

        compute = by_name.get(cname)
        wait = by_name.get(wname)
        if compute and wait:
            old_code = compute.get("parameters", {}).get("jsCode", "")
            if f"MIN_DELTA_SECONDS = {min_delta}" not in old_code:
                compute["parameters"]["jsCode"] = _js_code(min_delta, jitter)
                changes.append(f"updated_constants:{cname}")
            continue

        pos = trigger.get("position") or [0, 0]
        base_x, base_y = int(pos[0]) + 220, int(pos[1])
        compute = {
            "parameters": {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": _js_code(min_delta, jitter)},
            "id": str(uuid.uuid4()),
            "name": cname,
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [base_x, base_y],
        }
        wait = {
            "parameters": {"amount": "={{ $json.__delta_wait_seconds }}", "unit": "seconds"},
            "id": str(uuid.uuid4()),
            "name": wname,
            "type": "n8n-nodes-base.wait",
            "typeVersion": 1.1,
            "position": [base_x + 220, base_y],
        }
        nodes.extend([compute, wait])
        by_name[cname] = compute
        by_name[wname] = wait
        changes.append(f"added_gate:{cname}")

        connections[tname] = {"main": [[{"node": cname, "type": "main", "index": 0}]]}
        connections[cname] = {"main": [[{"node": wname, "type": "main", "index": 0}]]}
        connections[wname] = {"main": [original_edges]}
        changes.append(f"rewired_trigger:{tname}")

    return nodes, connections, changes


def apply(base_url: str, api_key: str, workflow_id: str, cfg: dict[str, int | str], dry_run: bool) -> dict[str, Any]:
    status, payload = _request("GET", f"{base_url}/api/v1/workflows/{workflow_id}", api_key)
    if status != 200:
        return {"workflow_id": workflow_id, "ok": False, "error": "get_failed", "status": status, "payload": payload}

    wf = payload.get("data", payload)
    min_delta = int(cfg["min"])
    jitter = int(cfg["jitter"])
    nodes, connections, changes = _ensure_delta_nodes(wf, min_delta, jitter)

    result: dict[str, Any] = {
        "workflow_id": workflow_id,
        "name": wf.get("name"),
        "active": wf.get("active"),
        "note": cfg.get("note"),
        "min_delta_seconds": min_delta,
        "jitter_max_seconds": jitter,
        "changes": changes,
        "ok": True,
    }

    if not changes:
        result["changes"] = ["already_configured"]
        return result

    if dry_run:
        result["dry_run"] = True
        return result

    raw_settings = wf.get("settings") or {}
    settings: dict[str, Any] = {"executionOrder": raw_settings.get("executionOrder") or "v1"}
    if isinstance(raw_settings.get("timezone"), str):
        settings["timezone"] = raw_settings["timezone"]
    if isinstance(raw_settings.get("executionTimeout"), int):
        settings["executionTimeout"] = raw_settings["executionTimeout"]
    body = {
        "name": wf.get("name"),
        "nodes": nodes,
        "connections": connections,
        "settings": settings,
    }
    put_status, put_payload = _request("PUT", f"{base_url}/api/v1/workflows/{workflow_id}", api_key, body)
    result["put_status"] = put_status
    if put_status != 200:
        result["ok"] = False
        result["error"] = put_payload
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply delta execution gates to n8n workflows.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workflow-id", action="append", dest="workflow_ids", default=[])
    args = parser.parse_args()

    base_url = os.getenv("N8N_URL", "").rstrip("/")
    api_key = os.getenv("N8N_REST_API_KEY")
    if not api_key:
        legacy = os.getenv("N8N_API_KEY") or ""
        if legacy.startswith("n8n_api_"):
            api_key = legacy
    if not base_url or not api_key:
        print(json.dumps({"error": "Requiere N8N_URL y N8N_REST_API_KEY."}, indent=2))
        return 1

    targets = DELTA_TARGETS
    if args.workflow_ids:
        targets = {wid: DELTA_TARGETS[wid] for wid in args.workflow_ids if wid in DELTA_TARGETS}
        missing = [wid for wid in args.workflow_ids if wid not in DELTA_TARGETS]
        if missing:
            print(json.dumps({"warning": "workflow_ids sin config", "missing": missing}, indent=2))

    results = [apply(base_url, api_key, wid, cfg, args.dry_run) for wid, cfg in targets.items()]
    print(json.dumps({"ok": all(r.get("ok") for r in results), "results": results}, indent=2, ensure_ascii=False))
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
