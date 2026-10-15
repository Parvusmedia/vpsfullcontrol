#!/usr/bin/env python3
"""Build scenarios_update payload JSON for Digitanimal Noco mirror (writes /tmp/scenarios_update_<id>_args.json)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from patch_make_noco_meta_leads import patch_blueprint


def main() -> None:
    token = os.environ.get("NOCO_TOKEN") or os.environ.get("NOCODB_API_TOKEN")
    if not token:
        print("NOCO_TOKEN or NOCODB_API_TOKEN required", file=sys.stderr)
        sys.exit(2)
    if len(sys.argv) < 2:
        print(
            "Usage: make_apply_noco_updates.py <scenario_id> [scenarios_get.json ...]",
            file=sys.stderr,
        )
        sys.exit(1)
    for spec in sys.argv[1:]:
        if ":" in spec:
            sid, path = spec.split(":", 1)
        else:
            sid, path = spec, f"/tmp/scenario_{spec}.json"
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        blueprint = data.get("blueprint", data)
        patched = patch_blueprint(blueprint, token, sid)
        out = Path(f"/tmp/scenarios_update_{sid}_args.json")
        out.write_text(
            json.dumps(
                {"scenarioId": int(sid), "blueprint": patched},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(out)


if __name__ == "__main__":
    main()
