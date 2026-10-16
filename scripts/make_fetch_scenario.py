#!/usr/bin/env python3
"""Fetch a Make scenario (with blueprint) via eu1 REST API. Requires MAKE_API_TOKEN env."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ZONE = os.environ.get("MAKE_ZONE", "eu1.make.com")


def fetch_scenario(scenario_id: int | str) -> dict:
    token = os.environ.get("MAKE_API_TOKEN") or os.environ.get("MAKE_TOKEN")
    if not token:
        raise SystemExit("MAKE_API_TOKEN or MAKE_TOKEN required")
    url = f"https://{ZONE}/api/v2/scenarios/{scenario_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Token {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: make_fetch_scenario.py <scenario_id> [out.json]", file=sys.stderr)
        sys.exit(1)
    sid = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/scenario_{sid}.json"
    data = fetch_scenario(sid)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
    print(out)


if __name__ == "__main__":
    main()
