#!/usr/bin/env python3
"""Apply Mateo AC configuration to n8n workflow DYJV0r0Z86pQIHH8 (requires VPS env on parvus-vps)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

WORKFLOW_ID = "DYJV0r0Z86pQIHH8"
TEMPLATE_WORKFLOW_ID = "HPaa9jGQmpDex41t"
ROOT = Path(__file__).resolve().parent

CONFIG_JS = """return [{json:{
  room:"Mateo",
  sensor_id:"bf7634a37dd4e94e17r4pg",
  radiator_id:"bfa6454e40fd2820fdwlra",
  ir_hub_id:"bf89c842ee56fd3393t695",
  temperature_code:"temp_current",
  scale:1,
  min_c:22,
  target_c:22,
  target_mode:"heat",
  target_fan:"auto",
  max_age_minutes:30,
  dry_run:false,
  manual_commands:true,
  force_ac_test:false
}}];"""
# AC virtual confirmado: Air Conditioner 7 (sub Smart IR Matute)


def main() -> int:
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        print("N8N_BASE_URL and N8N_API_KEY required", file=sys.stderr)
        return 1

    decidir = (ROOT / "n8n_mateo_ac_decidir.js").read_text(encoding="utf-8").strip()
    validar = (ROOT / "n8n_mateo_ac_validar.js").read_text(encoding="utf-8").strip()

    headers = {"X-N8N-API-KEY": key}

    def fetch(workflow_id: str) -> dict:
        return json.loads(
            urllib.request.urlopen(
                urllib.request.Request(f"{base}/api/v1/workflows/{workflow_id}", headers=headers)
            ).read()
        )

    wf = fetch(WORKFLOW_ID)
    template = fetch(TEMPLATE_WORKFLOW_ID)
    template_http = {
        n["name"]: n
        for n in template.get("nodes") or []
        if n.get("type") == "n8n-nodes-base.httpRequest"
    }

    for node in wf.get("nodes") or []:
        name = node.get("name")
        if name == "Configuracion":
            node.setdefault("parameters", {})["jsCode"] = CONFIG_JS
        elif name == "Decidir temperatura":
            node.setdefault("parameters", {})["jsCode"] = decidir
        elif name == "Validar resultado":
            node.setdefault("parameters", {})["jsCode"] = validar
        elif name == "Preparar verificacion":
            node.setdefault("parameters", {})["jsCode"] = (
                ROOT / "n8n_mateo_ac_preparar_verificacion.js"
            ).read_text(encoding="utf-8").strip()
        if node.get("type") == "n8n-nodes-base.httpRequest":
            ref = template_http.get(name or "")
            if ref and ref.get("credentials"):
                node["credentials"] = ref["credentials"]
                params = node.setdefault("parameters", {})
                for auth_key in ("authentication", "genericAuthType"):
                    if auth_key in ref.get("parameters", {}):
                        params[auth_key] = ref["parameters"][auth_key]

    body = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
    }
    settings = wf.get("settings") or {}
    allowed_settings = {
        k: settings[k]
        for k in (
            "executionOrder",
            "timezone",
            "callerPolicy",
            "saveDataErrorExecution",
            "saveDataSuccessExecution",
            "saveManualExecutions",
            "errorWorkflow",
            "executionTimeout",
        )
        if k in settings
    }
    allowed_settings["saveManualExecutions"] = True
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