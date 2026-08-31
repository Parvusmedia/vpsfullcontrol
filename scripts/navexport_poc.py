#!/usr/bin/env python3
"""
NavExport PoC — export Sales Navigator leads via Unipile (Simple tier).

Requires env:
  UNIPILE_API_KEY   — API key from Unipile dashboard (same Application as the account)
  UNIPILE_ACCOUNT_ID — LinkedIn account id, e.g. acc_xxxxxxxx

Usage:
  python3 scripts/navexport_poc.py status
  python3 scripts/navexport_poc.py lists
  python3 scripts/navexport_poc.py list --list-id LIST_ID [--limit 25] [--out leads.csv]
  python3 scripts/navexport_poc.py search --url 'https://www.linkedin.com/sales/search/people?...' [--limit 25]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "https://api.unipile.com/v2"

LIST_URL_RE = re.compile(
    r"linkedin\.com/sales/lists/people/(?P<id>\d+)",
    re.I,
)


def parse_list_id(value: str) -> str:
    """Accept raw list id or full Sales Navigator list URL."""
    value = value.strip()
    m = LIST_URL_RE.search(value)
    if m:
        return m.group("id")
    if value.isdigit():
        return value
    raise SystemExit(f"Invalid list id or URL: {value!r}")


def _env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return val


def _request(
    method: str,
    path: str,
    *,
    api_key: str,
    query: dict[str, str | int] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    url = f"{BASE}{path}"
    if query:
        qs = "&".join(f"{k}={v}" for k, v in query.items())
        url = f"{url}?{qs}"

    data = None
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} {method} {path}\n{err_body}", file=sys.stderr)
        sys.exit(1)


def cmd_status(api_key: str, account_id: str) -> None:
    accounts = _request("GET", "/accounts", api_key=api_key)
    items = accounts if isinstance(accounts, list) else accounts.get("items", accounts.get("data", []))
    print(json.dumps({"accounts": items}, indent=2, ensure_ascii=False))

    match = next((a for a in items if a.get("id") == account_id), None)
    if match:
        print(f"\nOK: account {account_id} found — status={match.get('status', match.get('state', '?'))}")
    else:
        print(f"\nWARN: {account_id} not in account list. Use an id from above.", file=sys.stderr)


def cmd_lists(api_key: str, account_id: str) -> None:
    data = _request(
        "GET",
        f"/{account_id}/linkedin/sales-navigator/lead-lists",
        api_key=api_key,
        query={"limit": 100},
    )
    items = data.get("items", data.get("data", data))
    if isinstance(items, dict):
        items = items.get("items", [])
    print(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"\n{len(items)} list(s). Use list id with: list --list-id <id>")


def _flatten_lead(item: dict[str, Any]) -> dict[str, str]:
    """Map Unipile SN lead payload to Simple CSV columns."""
    company = item.get("company") or {}
    if isinstance(company, str):
        company = {"name": company}

    positions = item.get("current_positions") or item.get("positions") or []
    role = ""
    company_name = company.get("name") or item.get("company_name") or ""
    if positions and isinstance(positions[0], dict):
        role = positions[0].get("role") or positions[0].get("title") or ""
        company_name = company_name or (positions[0].get("company") or "")

    name = item.get("name") or ""
    parts = name.split(" ", 1) if name else ["", ""]
    first = item.get("first_name") or parts[0]
    last = item.get("last_name") or (parts[1] if len(parts) > 1 else "")

    return {
        "first_name": str(first or ""),
        "last_name": str(last or ""),
        "full_name": str(name or f"{first} {last}".strip()),
        "job_title": str(item.get("headline") or role or item.get("title") or ""),
        "company_name": str(company_name or ""),
        "location": str(item.get("location") or ""),
        "linkedin_url": str(item.get("public_profile_url") or item.get("profile_url") or item.get("linkedin_url") or ""),
        "sales_nav_id": str(item.get("id") or item.get("member_id") or ""),
        "open_profile": str(item.get("open_profile", item.get("open_link", ""))),
        "connection_degree": str(item.get("network_distance") or item.get("degree") or ""),
    }


def _collect_items(page: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("items", "data", "results", "leads"):
        val = page.get(key)
        if isinstance(val, list):
            return val
    return []


def _paginate_list(
    api_key: str,
    account_id: str,
    list_id: str,
    max_leads: int,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    offset = 0
    limit = min(100, max_leads)

    while len(collected) < max_leads:
        page = _request(
            "POST",
            f"/{account_id}/linkedin/sales-navigator/lead-lists/{list_id}",
            api_key=api_key,
            query={"limit": limit, "offset": offset},
            body={},
        )
        batch = _collect_items(page)
        if not batch:
            break
        collected.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break
        time.sleep(1.5)

    return collected[:max_leads]


def _paginate_search(
    api_key: str,
    account_id: str,
    search_url: str,
    max_leads: int,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    cursor: str | None = None
    limit = min(100, max_leads)

    while len(collected) < max_leads:
        query: dict[str, str | int] = {"limit": limit}
        if cursor:
            query["cursor"] = cursor

        page = _request(
            "POST",
            f"/{account_id}/linkedin/sales-navigator/search",
            api_key=api_key,
            query=query,
            body={"url": search_url},
        )
        batch = _collect_items(page)
        if not batch:
            break
        collected.extend(batch)
        cursor = page.get("next_cursor") or page.get("cursor")
        if not cursor or len(batch) < limit:
            break
        time.sleep(1.5)

    return collected[:max_leads]


def _write_csv(rows: list[dict[str, str]], out_path: Path) -> None:
    if not rows:
        print("No leads to write.", file=sys.stderr)
        sys.exit(1)
    fieldnames = list(rows[0].keys())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows → {out_path}")


def cmd_list_export(api_key: str, account_id: str, list_id: str, limit: int, out: Path) -> None:
    raw = _paginate_list(api_key, account_id, list_id, limit)
    rows = [_flatten_lead(x) for x in raw if isinstance(x, dict)]
    _write_csv(rows, out)


def cmd_search_export(api_key: str, account_id: str, url: str, limit: int, out: Path) -> None:
    raw = _paginate_search(api_key, account_id, url, limit)
    rows = [_flatten_lead(x) for x in raw if isinstance(x, dict)]
    _write_csv(rows, out)


def main() -> None:
    parser = argparse.ArgumentParser(description="NavExport PoC (Unipile Simple tier)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="List Unipile accounts and verify UNIPILE_ACCOUNT_ID")
    sub.add_parser("lists", help="List Sales Navigator lead lists for the connected account")

    p_list = sub.add_parser("list", help="Export a saved SN lead list")
    p_list.add_argument(
        "--list-id",
        help="List id or full SN list URL (e.g. .../sales/lists/people/7298...)",
    )
    p_list.add_argument("--list-url", help="Alias for --list-id when passing a URL")
    p_list.add_argument("--limit", type=int, default=25, help="Max leads (default 25 for safe test)")
    p_list.add_argument("--out", type=Path, default=Path("/opt/cursor/artifacts/navexport_test.csv"))

    p_search = sub.add_parser("search", help="Export from SN search URL")
    p_search.add_argument("--url", required=True)
    p_search.add_argument("--limit", type=int, default=25)
    p_search.add_argument("--out", type=Path, default=Path("/opt/cursor/artifacts/navexport_test.csv"))

    args = parser.parse_args()
    api_key = _env("UNIPILE_API_KEY")
    account_id = _env("UNIPILE_ACCOUNT_ID")

    if args.cmd == "status":
        cmd_status(api_key, account_id)
    elif args.cmd == "lists":
        cmd_lists(api_key, account_id)
    elif args.cmd == "list":
        raw = args.list_id or args.list_url
        if not raw:
            print("Provide --list-id or --list-url", file=sys.stderr)
            sys.exit(1)
        list_id = parse_list_id(raw)
        cmd_list_export(api_key, account_id, list_id, args.limit, args.out)
    elif args.cmd == "search":
        cmd_search_export(api_key, account_id, args.url, args.limit, args.out)


if __name__ == "__main__":
    main()
