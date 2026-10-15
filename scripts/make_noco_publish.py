#!/usr/bin/env python3
"""Patch Make scenario snapshot JSON files with Noco mirror modules (writes /tmp/bp_*_noco.json)."""
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
            "Usage: make_noco_publish.py <scenario_id>:<scenarios_get.json> ...",
            file=sys.stderr,
        )
        sys.exit(1)
    for spec in sys.argv[1:]:
        sid, path = spec.split(":", 1)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        blueprint = data.get("blueprint", data)
        patched = patch_blueprint(blueprint, token, sid)
        out = Path(f"/tmp/bp_{sid}_noco.json")
        out.write_text(
            json.dumps(patched, ensure_ascii=False, indent="\t"),
            encoding="utf-8",
        )
        print(out)


if __name__ == "__main__":
    main()
