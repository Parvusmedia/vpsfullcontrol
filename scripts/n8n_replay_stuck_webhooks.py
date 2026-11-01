#!/usr/bin/env python3
"""Replay stuck webhook executions by re-POSTing payload to production webhook URL."""

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


def _request(method: str, url: str, api_key: str | None = None, body: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    req_headers = headers or {}
    if api_key:
        req_headers = {**req_headers, "X-N8N-API-KEY": api_key}
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def _api_get(base: str, api_key: str, path: str) -> dict:
    status, raw = _request("GET", base + path, api_key=api_key, headers={"Accept": "application/json"})
    if status != 200:
        raise RuntimeError(f"GET {path} failed: {status} {raw[:300]}")
    return json.loads(raw)


def _execution_meta(base: str, api_key: str, execution_id: str) -> tuple[str | None, str | None, object, list[str]]:
    detail = _api_get(base, api_key, f"/api/v1/executions/{execution_id}?includeData=true")
    root = detail if detail.get("status") else detail.get("data", detail)
    rd = root.get("data", {}).get("resultData", {})
    keys = list((rd.get("runData") or {}).keys())
    wh = rd.get("runData", {}).get("Webhook", [{}])[0]
    main = wh.get("data", {}).get("main", [[], []])
    post = main[1][0].get("json", {}) if len(main) > 1 and main[1] else {}
    body = post.get("body") or []
    lead_id = None
    if isinstance(body, list) and body and isinstance(body[0], dict):
        lead_id = body[0].get("leadid")
    return lead_id, post.get("webhookUrl"), body, keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--since-madrid", default="2026-11-01 00:51:00")
    parser.add_argument("--delay-seconds", type=int, default=45)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    base = os.environ["N8N_URL"].rstrip("/")
    api_key = os.environ.get("N8N_REST_API_KEY")
    if not api_key:
        print(json.dumps({"error": "missing N8N_REST_API_KEY"}))
        return 1

    since = datetime.fromisoformat(args.since_madrid).replace(tzinfo=ZoneInfo("Europe/Madrid")).astimezone(timezone.utc)

    stuck_by_lead: dict[str, dict] = {}
    processed_leads: set[str] = set()
    cursor = None
    while True:
        params: dict[str, str | int] = {"workflowId": args.workflow_id, "limit": 100}
        if cursor:
            params["cursor"] = cursor
        listing = _api_get(base, api_key, "/api/v1/executions?" + urllib.parse.urlencode(params))
        stop = False
        for ex in listing.get("data", []):
            started = ex.get("startedAt")
            if not started:
                continue
            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            if dt < since:
                stop = True
                break
            if ex.get("mode") != "webhook":
                continue
            lead_id, webhook_url, body, keys = _execution_meta(base, api_key, ex["id"])
            if not lead_id or not webhook_url:
                continue
            if keys == ["Webhook"]:
                stuck_by_lead.setdefault(
                    lead_id,
                    {
                        "source_execution_id": ex["id"],
                        "startedAt": started,
                        "webhookUrl": webhook_url,
                        "body": body,
                    },
                )
            elif len(keys) > 1:
                processed_leads.add(lead_id)
        if stop:
            break
        cursor = listing.get("nextCursor")
        if not cursor:
            break

    todo = [item for lead, item in sorted(stuck_by_lead.items(), key=lambda kv: kv[1]["startedAt"]) if lead not in processed_leads]
    if args.limit > 0:
        todo = todo[: args.limit]

    report = {
        "workflow_id": args.workflow_id,
        "since_madrid": args.since_madrid,
        "stuck_unique_leads": len(stuck_by_lead),
        "already_processed_leads": len(processed_leads),
        "to_replay": len(todo),
        "delay_seconds": args.delay_seconds,
        "dry_run": args.dry_run,
        "results": [],
    }

    for index, item in enumerate(todo):
        lead_id = item["body"][0]["leadid"] if item["body"] else None
        entry = {
            "leadid": lead_id,
            "source_execution_id": item["source_execution_id"],
            "startedAt": item["startedAt"],
        }
        if args.dry_run:
            entry["action"] = "would_post_webhook"
            report["results"].append(entry)
            continue

        payload = json.dumps(item["body"]).encode("utf-8")
        status, raw = _request(
            "POST",
            item["webhookUrl"],
            body=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        entry["http_status"] = status
        entry["response"] = raw[:200]
        report["results"].append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
        if status >= 400:
            print(json.dumps({"warning": "replay_http_error", **entry}), flush=True)
        if args.delay_seconds > 0 and index < len(todo) - 1:
            time.sleep(args.delay_seconds)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
