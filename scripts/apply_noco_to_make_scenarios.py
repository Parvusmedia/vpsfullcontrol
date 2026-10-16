#!/usr/bin/env python3
"""Patch scenario blueprint JSON files with Noco steps. Does not call Make API."""
from __future__ import annotations

import sys
from pathlib import Path

from patch_make_noco_meta_leads import patch_blueprint


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: apply_noco_to_make_scenarios.py <xc_token> <scenario_id>:<path.json> ...",
            file=sys.stderr,
        )
        sys.exit(1)
    token = sys.argv[1]
    for spec in sys.argv[2:]:
        sid, path = spec.split(":", 1)
        data = __import__("json").loads(Path(path).read_text(encoding="utf-8"))
        blueprint = data.get("blueprint", data)
        patched = patch_blueprint(blueprint, token, sid)
        out = Path(f"/tmp/bp_{sid}_noco.json")
        out.write_text(
            __import__("json").dumps(patched, ensure_ascii=False, indent="\t"),
            encoding="utf-8",
        )
        print(out)


if __name__ == "__main__":
    main()
