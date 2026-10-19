#!/usr/bin/env python3
"""Patch Noco POST body in scenario blueprints (stdin: scenarios_get JSON per line or single object)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_make_noco_meta_leads import refresh_noco_in_blueprint  # noqa: E402


def _token_from_blueprint(blueprint: dict) -> str | None:
    for m in blueprint.get("flow") or []:
        if m.get("id") != 7:
            continue
        for h in (m.get("mapper") or {}).get("headers") or []:
            if h.get("name") == "xc-token" and h.get("value"):
                return str(h["value"])
    return None


def main() -> None:
    token = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("stdin required: scenarios_get JSON")
    data = json.loads(raw)
    sid = str(data.get("id") or "")
    if not sid:
        raise SystemExit("missing id")
    blueprint = data.get("blueprint") or data
    if not token:
        token = _token_from_blueprint(blueprint)
    if not token:
        raise SystemExit("NOCO_TOKEN or xc-token in module 7 required")
    patched = refresh_noco_in_blueprint(blueprint, token, sid)
    Path(f"/tmp/scenario_{sid}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent="\t"),
        encoding="utf-8",
    )
    args = {"scenarioId": int(sid), "blueprint": patched}
    out = Path(f"/tmp/scenarios_update_{sid}_args.json")
    out.write_text(json.dumps(args, ensure_ascii=False), encoding="utf-8")
    m7 = next(m for m in patched["flow"] if m.get("id") == 7)
    body = m7["mapper"]["data"]
    print(
        json.dumps(
            {
                "scenario_id": sid,
                "flow_ids": [m["id"] for m in patched["flow"]],
                "has_join_bug": "`[]; \", \")" in body or "[]; \", \");" in body,
                "has_greek_slug": "πόσα_ζώα" in body,
                "args_file": str(out),
            }
        )
    )


if __name__ == "__main__":
    main()
