#!/usr/bin/env python3
"""Filter Make executions_list JSON to original successful webhook runs safe to replay once.

Usage: digitanimal_collect_replay_ids.py < executions.json
Or paste MCP executions_list output into a file.
"""
from __future__ import annotations

import json
import re
import sys

EXEC_ID = re.compile(r"^[0-9a-f]{32}$")


def collect(items: list) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        eid = item.get("id")
        if not isinstance(eid, str) or not EXEC_ID.match(eid):
            continue
        if item.get("status") != 1:
            continue
        if not item.get("isReplayable", True):
            continue
        if item.get("replayOfExecutionId"):
            continue
        if item.get("type") not in (None, "auto"):
            continue
        ops = item.get("operations") or 0
        if ops < 3:
            continue
        if eid in seen:
            continue
        seen.add(eid)
        out.append(eid)
    return out


def main() -> None:
    raw = sys.stdin.read()
    data = json.loads(raw)
    if isinstance(data, dict) and "executions" in data:
        items = data["executions"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    ids = collect(items)
    json.dump(ids, sys.stdout, indent=2)
    print(file=sys.stdout)


if __name__ == "__main__":
    main()
