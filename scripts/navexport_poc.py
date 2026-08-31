#!/usr/bin/env python3
"""
NavExport PoC — export Sales Navigator leads via Unipile (Simple tier).

Requires env:
  UNIPILE_API_KEY      — API key from Unipile dashboard
  UNIPILE_ACCOUNT_ID   — LinkedIn account id (acc_xxx or legacy DSN id)
  UNIPILE_BASE_URL     — optional; e.g. https://api46.unipile.com:17682/api/v1
                         defaults to https://api.unipile.com/v2 (v2 API)

Usage:
  python3 scripts/navexport_poc.py status
  python3 scripts/navexport_poc.py lists
  python3 scripts/navexport_poc.py list --list-url 'https://www.linkedin.com/sales/lists/people/...' [--limit 25]
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
from urllib.parse import quote
from urllib.request import Request, urlopen

LIST_URL_RE = re.compile(
    r"(https?://(?:www\.)?linkedin\.com/sales/lists/people/\d+[^\s]*)",
    re.I,
)
LIST_ID_RE = re.compile(
    r"linkedin\.com/sales/lists/people/(?P<id>\d+)",
    re.I,
)


def resolve_config() -> tuple[str, str, bool]:
    """Return (api_base, api_key, is_v1)."""
    api_key = _env("UNIPILE_API_KEY")
    base = os.environ.get("UNIPILE_BASE_URL", "https://api.unipile.com/v2").strip().rstrip("/")
    is_v1 = "/api/v1" in base or (not base.endswith("/v2") and "api.unipile.com/v2" not in base)
    return base, api_key, is_v1


def normalize_list_url(value: str) -> str:
    value = value.strip()
    m = LIST_URL_RE.search(value)
    if m:
        return m.group(1)
    if value.isdigit():
        return f"https://www.linkedin.com/sales/lists/people/{value}"
    raise SystemExit(f"Invalid list id or URL: {value!r}")


def _env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return val


def _request(
    api_base: str,
    api_key: str,
    method: str,
    path: str,
    *,
    query: dict[str, str | int] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    url = f"{api_base}{path}"
    if query:
        qs = "&".join(f"{k}={quote(str(v), safe='')}" if k == "cursor" else f"{k}={v}" for k, v in query.items())
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
        print(f"HTTP {e.code} {method} {url}\n{err_body}", file=sys.stderr)
        sys.exit(1)


def cmd_status(api_base: str, api_key: str, account_id: str, is_v1: bool) -> None:
    path = "/accounts" if is_v1 else "/accounts"
    accounts = _request(api_base, api_key, "GET", path)
    items = accounts if isinstance(accounts, list) else accounts.get("items", accounts.get("data", []))
    print(json.dumps({"api": "v1" if is_v1 else "v2", "base": api_base, "accounts": items}, indent=2, ensure_ascii=False))

    match = next((a for a in items if a.get("id") == account_id), None)
    if match:
        print(f"\nOK: account {account_id} found — status={match.get('status', match.get('state', '?'))}")
    else:
        print(f"\nWARN: {account_id} not in account list. Use an id from above.", file=sys.stderr)


def cmd_lists(api_base: str, api_key: str, account_id: str, is_v1: bool) -> None:
    if is_v1:
        print("lists command requires Unipile v2 API. Use list --list-url with your SN list URL on v1 DSN.", file=sys.stderr)
        sys.exit(1)
    data = _request(
        api_base,
        api_key,
        "GET",
        f"/{account_id}/linkedin/sales-navigator/lead-lists",
        query={"limit": 100},
    )
    items = data.get("items", data.get("data", data))
    if isinstance(items, dict):
        items = items.get("items", [])
    print(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"\n{len(items)} list(s). Use list --list-url <url>")


def _flatten_lead(item: dict[str, Any]) -> dict[str, str]:
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


def _paginate_v1_url(
    api_base: str,
    api_key: str,
    account_id: str,
    source_url: str,
    max_leads: int,
) -> list[dict[str, Any]]:
    """v1 DSN: POST /linkedin/search?account_id=... with body {url: ...}."""
    collected: list[dict[str, Any]] = []
    cursor: str | None = None

    while len(collected) < max_leads:
        page_size = min(25, max_leads - len(collected))
        query: dict[str, str | int] = {"account_id": account_id, "limit": page_size}
        if cursor:
            query["cursor"] = cursor

        page = _request(
            api_base,
            api_key,
            "POST",
            "/linkedin/search",
            query=query,
            body={"url": source_url},
        )
        batch = _collect_items(page)
        if not batch:
            break
        collected.extend(batch)
        cursor = page.get("cursor") or page.get("next_cursor")
        if not cursor:
            break
        time.sleep(1.5)

    return collected[:max_leads]


def _paginate_v2_list(
    api_base: str,
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
            api_base,
            api_key,
            "POST",
            f"/{account_id}/linkedin/sales-navigator/lead-lists/{list_id}",
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


def _paginate_v2_search(
    api_base: str,
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
            api_base,
            api_key,
            "POST",
            f"/{account_id}/linkedin/sales-navigator/search",
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


def cmd_list_export(
    api_base: str,
    api_key: str,
    account_id: str,
    is_v1: bool,
    list_ref: str,
    limit: int,
    out: Path,
) -> None:
    if is_v1:
        list_url = normalize_list_url(list_ref)
        raw = _paginate_v1_url(api_base, api_key, account_id, list_url, limit)
    else:
        list_id = LIST_ID_RE.search(list_ref)
        lid = list_id.group("id") if list_id else list_ref.strip()
        if not lid.isdigit():
            list_url = normalize_list_url(list_ref)
            raw = _paginate_v2_search(api_base, api_key, account_id, list_url, limit)
        else:
            raw = _paginate_v2_list(api_base, api_key, account_id, lid, limit)
    rows = [_flatten_lead(x) for x in raw if isinstance(x, dict)]
    _write_csv(rows, out)


def cmd_search_export(
    api_base: str,
    api_key: str,
    account_id: str,
    is_v1: bool,
    url: str,
    limit: int,
    out: Path,
) -> None:
    if is_v1:
        raw = _paginate_v1_url(api_base, api_key, account_id, url, limit)
    else:
        raw = _paginate_v2_search(api_base, api_key, account_id, url, limit)
    rows = [_flatten_lead(x) for x in raw if isinstance(x, dict)]
    _write_csv(rows, out)


def main() -> None:
    parser = argparse.ArgumentParser(description="NavExport PoC (Unipile Simple tier)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="List Unipile accounts and verify UNIPILE_ACCOUNT_ID")
    sub.add_parser("lists", help="List Sales Navigator lead lists (v2 only)")

    p_list = sub.add_parser("list", help="Export a saved SN lead list")
    p_list.add_argument("--list-id", help="List id or full SN list URL")
    p_list.add_argument("--list-url", help="Alias for --list-id when passing a URL")
    p_list.add_argument("--limit", type=int, default=25, help="Max leads (default 25)")
    p_list.add_argument("--out", type=Path, default=Path("/opt/cursor/artifacts/navexport_test.csv"))

    p_search = sub.add_parser("search", help="Export from SN search URL")
    p_search.add_argument("--url", required=True)
    p_search.add_argument("--limit", type=int, default=25)
    p_search.add_argument("--out", type=Path, default=Path("/opt/cursor/artifacts/navexport_test.csv"))

    args = parser.parse_args()
    api_base, api_key, is_v1 = resolve_config()
    account_id = _env("UNIPILE_ACCOUNT_ID")

    if args.cmd == "status":
        cmd_status(api_base, api_key, account_id, is_v1)
    elif args.cmd == "lists":
        cmd_lists(api_base, api_key, account_id, is_v1)
    elif args.cmd == "list":
        raw = args.list_id or args.list_url
        if not raw:
            print("Provide --list-id or --list-url", file=sys.stderr)
            sys.exit(1)
        cmd_list_export(api_base, api_key, account_id, is_v1, raw, args.limit, args.out)
    elif args.cmd == "search":
        cmd_search_export(api_base, api_key, account_id, is_v1, args.url, args.limit, args.out)


if __name__ == "__main__":
    main()
