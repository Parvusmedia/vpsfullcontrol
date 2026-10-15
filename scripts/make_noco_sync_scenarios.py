#!/usr/bin/env python3
"""Patch scenario snapshots with Noco steps and write Make update payloads.

Expects /tmp/scenario_<id>.json files (full scenarios_get objects).
Run make_apply_noco_updates.py after saving snapshots via Make MCP scenarios_get.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from patch_make_noco_meta_leads import patch_blueprint

SCENARIO_IDS = ("7950608", "7951407", "7952998")


def main() -> None:
    token = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not token:
        print("NOCO_TOKEN or NOCODB_API_TOKEN required", file=sys.stderr)
        sys.exit(2)
    ids = sys.argv[1:] if len(sys.argv) > 1 else list(SCENARIO_IDS)
    for sid in ids:
        path = Path(f"/tmp/scenario_{sid}.json")
        if not path.is_file():
            print(f"missing snapshot {path}", file=sys.stderr)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        blueprint = data.get("blueprint", data)
        patched = patch_blueprint(blueprint, token, sid)
        out = Path(f"/tmp/scenarios_update_{sid}_args.json")
        out.write_text(
            json.dumps({"scenarioId": int(sid), "blueprint": patched}, ensure_ascii=False),
            encoding="utf-8",
        )
        flow_ids = [m["id"] for m in patched["flow"]]
        print(sid, "flow", flow_ids, "->", out)


if __name__ == "__main__":
    main()
