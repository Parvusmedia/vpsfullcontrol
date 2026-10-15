#!/usr/bin/env python3
"""Write scenarios_get JSON to /tmp/scenario_<id>.json (stdin = full JSON object)."""
from __future__ import annotations

import json
import sys


def main() -> None:
    data = json.load(sys.stdin)
    sid = data.get("id")
    if not sid:
        print("JSON must include id", file=sys.stderr)
        sys.exit(1)
    path = f"/tmp/scenario_{sid}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
    print(path)


if __name__ == "__main__":
    main()
