#!/usr/bin/env python3
"""Build patched blueprint JSON for Digitanimal Spain (stdout)."""
from __future__ import annotations

import copy
import json
import sys

# Fetched from Make scenarios_get(7950608) — keep in sync if scenario is edited manually.
SCENARIO_BLUEPRINT = json.loads(
    r"""
{
  "flow": [],
  "name": "Digitanimal_Spain_Meta-LeadAds",
  "metadata": {
    "instant": true,
    "version": 1,
    "designer": {"orphans": [], "samples": {}},
    "scenario": {
      "dlq": false,
      "slots": null,
      "dataloss": false,
      "maxErrors": 3,
      "autoCommit": true,
      "roundtrips": 1,
      "sequential": false,
      "confidential": false,
      "freshVariables": false,
      "autoCommitTriggerLast": true
    }
  },
  "scheduling": {"type": "immediately", "maximum_runs_per_minute": 100},
  "interface": {"input": [], "output": []}
}
"""
)


def main() -> None:
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not src_path:
        print("Usage: apply_digitanimal_spain_router.py /path/to/scenario_get.json", file=sys.stderr)
        sys.exit(1)
    data = json.loads(open(src_path, encoding="utf-8").read())
    blueprint = data["blueprint"]
    from patch_digitanimal_spain_phone_router import patch_blueprint

    patched = patch_blueprint(blueprint)
    json.dump(patched, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
