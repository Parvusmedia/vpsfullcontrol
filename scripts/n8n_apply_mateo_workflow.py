#!/usr/bin/env python3
"""Apply Mateo AC configuration to n8n workflow DYJV0r0Z86pQIHH8 (requires VPS env on parvus-vps)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

WORKFLOW_ID = "DYJV0r0Z86pQIHH8"
ROOT = Path(__file__).resolve().parent

CONFIG_JS = """return [{json:{
  room:"Mateo",
  sensor_id:"bf7634a37dd4e94e17r4pg",
  radiator_id:"bf7e0c495c637dc320vt0z",
  ir_hub_id:"bf89c842ee56fd3393t695",
  temperature_code:"temp_current",
  scale:1,
  min_c:21,
  target_c:21,
  target_mode:"heat",
  target_fan:"auto",
  max_age_minutes:30,
  dry_run:false,
  manual_commands:true
}}];"""


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_BASE_URL and N8N_API_KEY required", file=sys.stderr)
        return 1

    decidir = (ROOT / "n8n_mateo_ac_decidir.js").read_text(encoding="utf-8").strip()
    validar = (ROOT / "n8n_mateo_ac_validar.js").read_text(encoding="utf-8").strip()

    wf = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/v1/workflows/{WORKFLOW_ID}",
                headers={"X-N8N-API-KEY": key},
            )
        ).read()
    )

    for node in wf.get("nodes") or []:
        name = node.get("name")
        if name == "Configuracion":
            node.setdefault("parameters", {})["jsCode"] = CONFIG_JS
        elif name == "Decidir temperatura":
            node.setdefault("parameters", {})["jsCode"] = decidir
        elif name == "Validar resultado":
            node.setdefault("parameters", {})["jsCode"] = validar

    # n8n API expects a subset of fields on PUT
    settings = wf.get("settings") or {}
    allowed_settings = {k: settings[k] for k in ("executionOrder", "timezone", "callerPolicy") if k in settings}
    body = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
    }
    if allowed_settings:
        body["settings"] = allowed_settings

    req = urllib.request.Request(
        f"{base}/api/v1/workflows/{WORKFLOW_ID}",
        data=json.dumps(body).encode("utf-8"),
        method="PUT",
        headers={"X-N8N-API-KEY": key, "Content-Type": "application/json"},
    )
    updated = json.loads(urllib.request.urlopen(req).read())
    print(json.dumps({"ok": True, "id": updated.get("id"), "name": updated.get("name"), "updatedAt": updated.get("updatedAt")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())