#!/usr/bin/env python3
"""Create Smartlead campaigns for consultoras SME outreach (ES + EN, PAUSED)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from smartlead import (  # noqa: E402
    BASE,
    CAMPAIGN_NAME_EN,
    CAMPAIGN_NAME_ES,
    REMINDER_DELAY_DAYS,
    _UA,
    sequences_payload_en,
    sequences_payload_es,
    smartlead_api_key,
    smartlead_email_account_ids,
)

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_env() -> None:
    for path in (Path("/etc/linkedinreport/app.env"), ROOT / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            import os

            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def create_campaign(*, locale: str) -> dict:
    key = smartlead_api_key()
    if not key:
        raise RuntimeError("Missing Smartlead API key")

    name = CAMPAIGN_NAME_ES if locale == "es" else CAMPAIGN_NAME_EN
    payload = sequences_payload_es() if locale == "es" else sequences_payload_en()
    schedule_tz = "Europe/Madrid" if locale == "es" else "Europe/London"

    create = httpx.post(
        f"{BASE}/campaigns/create",
        params={"api_key": key},
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
        json={"name": name},
        timeout=45,
    )
    create.raise_for_status()
    body = create.json() if create.content else {}
    campaign_id = body.get("id") or body.get("campaign_id")
    if not campaign_id:
        raise RuntimeError(f"create failed: {body}")
    campaign_id = int(campaign_id)

    httpx.post(
        f"{BASE}/campaigns/{campaign_id}/sequences",
        params={"api_key": key},
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    ).raise_for_status()

    schedule = {
        "timezone": schedule_tz,
        "days_of_the_week": [1, 2, 3, 4, 5],
        "start_hour": "09:00",
        "end_hour": "18:00",
        "min_time_btw_emails": 15,
        "max_new_leads_per_day": 20,
    }
    try:
        httpx.post(
            f"{BASE}/campaigns/{campaign_id}/schedule",
            params={"api_key": key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json=schedule,
            timeout=45,
        ).raise_for_status()
    except Exception as exc:
        print(f"schedule warning ({locale}): {exc}", file=sys.stderr)

    accounts = smartlead_email_account_ids()
    if accounts:
        try:
            httpx.post(
                f"{BASE}/campaigns/{campaign_id}/email-accounts",
                params={"api_key": key},
                headers={"User-Agent": _UA, "Content-Type": "application/json"},
                json={"email_account_ids": accounts},
                timeout=45,
            ).raise_for_status()
        except Exception as exc:
            print(f"email-accounts warning ({locale}): {exc}", file=sys.stderr)

    httpx.post(
        f"{BASE}/campaigns/{campaign_id}/status",
        params={"api_key": key},
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
        json={"status": "PAUSED"},
        timeout=45,
    ).raise_for_status()

    env_key = "SMARTLEAD_CONSULTORAS_ES_CAMPAIGN_ID" if locale == "es" else "SMARTLEAD_CONSULTORAS_EN_CAMPAIGN_ID"
    return {
        "locale": locale,
        "campaign_id": campaign_id,
        "name": name,
        "status": "PAUSED",
        "timezone": schedule_tz,
        "reminder_delay_days": REMINDER_DELAY_DAYS,
        "email_account_ids": accounts,
        "env": f"{env_key}={campaign_id}",
        "sequences": [
            {"seq": 1, "delay_days": 0},
            {"seq": 2, "delay_days": REMINDER_DELAY_DAYS},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locale", choices=("es", "en", "all"), default="all")
    args = parser.parse_args()
    _load_env()

    locales = ["es", "en"] if args.locale == "all" else [args.locale]
    results = []
    for locale in locales:
        print(f"Creating {locale.upper()} campaign…")
        results.append(create_campaign(locale=locale))

    out = DATA_DIR / "smartlead_campaigns.json"
    out.write_text(json.dumps({"campaigns": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"campaigns": results}, indent=2, ensure_ascii=False))
    print(f"\nWrote {out}")
    for item in results:
        print(item["env"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
