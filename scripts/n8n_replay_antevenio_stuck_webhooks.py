#!/usr/bin/env python3
"""Replay Antevenio webhook hits that ended success with only the Webhook node (POST branch).

Uses query-string leadid dedupe; does not share code with AAPEX replay helpers.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ANTEVENIO_WORKFLOW_ID = "JTg8kZYug7H5QkiE"
DEFAULT_SINCE_MADRID = "2026-11-01 00:52:00"


def http_call(
    method: str,
    url: str,
    *,
    api_key: str | None = None,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    hdrs = dict(headers or {})
    if api_key:
        hdrs["X-N8N-API-KEY"] = api_key
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def n8n_get(base: str, api_key: str, path: str) -> dict:
    status, raw = http_call("GET", base + path, api_key=api_key, headers={"Accept": "application/json"})
    if status != 200:
        raise RuntimeError(f"GET {path} -> {status}: {raw[:400]}")
    return json.loads(raw)


def _webhook_post_item(run_data: dict) -> dict | None:
    wh_runs = run_data.get("Webhook") or []
    if not wh_runs:
        return None
    main = wh_runs[0].get("data", {}).get("main") or []
    if len(main) < 2 or not main[1]:
        return None
    return main[1][0].get("json") or {}


def _webhook_any_item(run_data: dict) -> dict | None:
    wh_runs = run_data.get("Webhook") or []
    if not wh_runs:
        return None
    main = wh_runs[0].get("data", {}).get("main") or []
    for branch in main:
        if branch:
            return branch[0].get("json") or {}
    return None


def _leadid_from_item(item: dict | None) -> str | None:
    if not item:
        return None
    query = item.get("query") or {}
    if isinstance(query, dict):
        lid = query.get("leadid")
        if lid:
            return str(lid)
    body = item.get("body")
    if isinstance(body, dict):
        lid = body.get("leadid")
        if lid:
            return str(lid)
    return None


def inspect_execution(base: str, api_key: str, execution_id: str) -> tuple[list[str], dict | None, dict | None]:
    detail = n8n_get(base, api_key, f"/api/v1/executions/{execution_id}?includeData=true")
    root = detail if detail.get("status") else detail.get("data", detail)
    rd = root.get("data", {}).get("resultData") or {}
    run_data = rd.get("runData") or {}
    node_names = list(run_data.keys())
    post_item = _webhook_post_item(run_data)
    any_item = _webhook_any_item(run_data)
    return node_names, post_item, any_item


def build_replay_url(webhook_url: str, query: dict) -> str:
    clean = {k: v for k, v in query.items() if v is not None}
    qs = urllib.parse.urlencode(clean, doseq=True)
    sep = "&" if "?" in webhook_url else "?"
    return f"{webhook_url}{sep}{qs}" if qs else webhook_url


def collect_candidates(
    base: str,
    api_key: str,
    workflow_id: str,
    since_utc: datetime,
) -> tuple[dict[str, dict], set[str]]:
    stuck_by_lead: dict[str, dict] = {}
    processed_leads: set[str] = set()
    cursor: str | None = None

    while True:
        params: dict[str, str | int] = {"workflowId": workflow_id, "limit": 100}
        if cursor:
            params["cursor"] = cursor
        listing = n8n_get(base, api_key, "/api/v1/executions?" + urllib.parse.urlencode(params))
        stop = False
        for ex in listing.get("data", []):
            started = ex.get("startedAt")
            if not started:
                continue
            started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            if started_dt < since_utc:
                stop = True
                break
            if ex.get("mode") != "webhook":
                continue

            nodes, post_item, any_item = inspect_execution(base, api_key, ex["id"])
            lead_id = _leadid_from_item(post_item) or _leadid_from_item(any_item)
            if not lead_id:
                continue

            if nodes == ["Webhook"]:
                if not post_item or not post_item.get("webhookUrl"):
                    continue
                query = post_item.get("query") or {}
                if not query.get("leadid"):
                    continue
                stuck_by_lead.setdefault(
                    lead_id,
                    {
                        "source_execution_id": ex["id"],
                        "startedAt": started,
                        "webhookUrl": post_item["webhookUrl"],
                        "query": dict(query),
                    },
                )
            elif len(nodes) > 1:
                processed_leads.add(lead_id)

        if stop:
            break
        cursor = listing.get("nextCursor")
        if not cursor:
            break

    return stuck_by_lead, processed_leads


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay stuck Antevenio POST webhooks (query-string leads).")
    parser.add_argument("--since-madrid", default=DEFAULT_SINCE_MADRID)
    parser.add_argument("--delay-seconds", type=int, default=45)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    base = os.environ.get("N8N_URL", "").rstrip("/")
    api_key = os.environ.get("N8N_REST_API_KEY")
    if not base or not api_key:
        print(json.dumps({"error": "missing N8N_URL or N8N_REST_API_KEY"}))
        return 1

    since_utc = datetime.fromisoformat(args.since_madrid).replace(tzinfo=ZoneInfo("Europe/Madrid")).astimezone(
        timezone.utc
    )

    stuck_by_lead, processed_leads = collect_candidates(base, api_key, ANTEVENIO_WORKFLOW_ID, since_utc)
    todo = [
        item
        for _lead, item in sorted(stuck_by_lead.items(), key=lambda kv: kv[1]["startedAt"])
        if _lead not in processed_leads
    ]
    if args.limit > 0:
        todo = todo[: args.limit]

    report: dict = {
        "workflow_id": ANTEVENIO_WORKFLOW_ID,
        "workflow_name": "MPA-APIFY_Antevenio",
        "since_madrid": args.since_madrid,
        "stuck_unique_leads": len(stuck_by_lead),
        "already_processed_leads": len(processed_leads),
        "to_replay": len(todo),
        "delay_seconds": args.delay_seconds,
        "dry_run": args.dry_run,
        "results": [],
    }

    for index, item in enumerate(todo):
        lead_id = str(item["query"].get("leadid"))
        replay_url = build_replay_url(item["webhookUrl"], item["query"])
        entry = {
            "leadid": lead_id,
            "source_execution_id": item["source_execution_id"],
            "startedAt": item["startedAt"],
            "replay_url_path": urllib.parse.urlparse(replay_url).path,
        }
        if args.dry_run:
            entry["action"] = "would_post_webhook_with_query"
            report["results"].append(entry)
            continue

        status, raw = http_call(
            "POST",
            replay_url,
            body=b"",
            headers={"Accept": "application/json"},
        )
        entry["http_status"] = status
        entry["response"] = raw[:200]
        report["results"].append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
        if status >= 400:
            print(json.dumps({"warning": "antevenio_replay_http_error", **entry}), flush=True)
        if args.delay_seconds > 0 and index < len(todo) - 1:
            time.sleep(args.delay_seconds)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
