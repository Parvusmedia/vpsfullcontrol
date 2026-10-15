#!/usr/bin/env python3
"""Print Make scenarios_replay MCP calls as JSONL (for manual/agent batch)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLAN = Path("/opt/cursor/artifacts/digitanimal_replay_plan.json")


def main() -> None:
    plan = json.loads(PLAN.read_text())
    for sid, ids in plan.items():
        for eid in ids:
            print(json.dumps({"scenarioId": int(sid), "executionIds": [eid]}))


if __name__ == "__main__":
    main()
