#!/usr/bin/env python3
"""Create Smartlead campaign CDE · Reckitt SN list · Data for Media · EN (PAUSED)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from reckitt.config import CAMPAIGN_NAME, DATA_DIR, ensure_data_dirs, load_dotenv_files
from reckitt.smartlead import EMAIL_1_BODY, EMAIL_1_SUBJECT, EMAIL_2_BODY, EMAIL_2_SUBJECT, EMAIL_3_BODY, EMAIL_3_SUBJECT

BASE = "https://server.smartlead.ai/api/v1"
UA = "Mozilla/5.0 (compatible; ProspeccionReckittCDE/0.1)"


def _api_key() -> str:
    return (
        os.environ.get("SMARTLEAD_RECKITT_API_KEY")
        or os.environ.get("SMARTLEAD_DFM_API_KEY")
        or os.environ.get("SMARTLEAD_API_KEY")
        or ""
    ).strip()


def _existing_campaign_payload() -> dict | None:
    path = DATA_DIR / "smartlead_campaign.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and data.get("campaign_id"):
        return data
    return None


def main(argv: list[str] | None = None) -> int:
    load_dotenv_files()
    ensure_data_dirs()
    args = argv if argv is not None else sys.argv[1:]
    dry_run = "--dry-run" in args
    force = "--force" in args

    existing = _existing_campaign_payload()
    env_id = (os.environ.get("SMARTLEAD_RECKITT_CAMPAIGN_ID") or "").strip()
    if existing and not force:
        print(json.dumps({"skipped": True, "reason": "campaign_json_exists", **existing}, indent=2))
        print("\nPass --force to create another campaign (do not reuse Alarmas / NextConvers IDs).")
        return 0
    if env_id and not force and not existing:
        print(
            json.dumps(
                {
                    "skipped": True,
                    "reason": "SMARTLEAD_RECKITT_CAMPAIGN_ID already set",
                    "campaign_id": env_id,
                },
                indent=2,
            )
        )
        return 0

    sequences = {
        "sequences": [
            {
                "seq_number": 1,
                "subject": EMAIL_1_SUBJECT,
                "email_body": EMAIL_1_BODY,
                "seq_delay_details": {"delay_in_days": 0},
            },
            {
                "seq_number": 2,
                "subject": EMAIL_2_SUBJECT,
                "email_body": EMAIL_2_BODY,
                "seq_delay_details": {"delay_in_days": 3},
            },
            {
                "seq_number": 3,
                "subject": EMAIL_3_SUBJECT,
                "email_body": EMAIL_3_BODY,
                "seq_delay_details": {"delay_in_days": 4},
            },
        ]
    }
    schedule = {
        "timezone": "Europe/Madrid",
        "days_of_the_week": [1, 2, 3, 4, 5],
        "start_hour": "09:00",
        "end_hour": "18:00",
        "min_time_btw_emails": 3,
        "max_new_leads_per_day": 20,
    }
    account = (
        os.environ.get("SMARTLEAD_RECKITT_EMAIL_ACCOUNT_ID")
        or os.environ.get("SMARTLEAD_EMAIL_ACCOUNT_ID")
        or ""
    ).strip()

    if dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "name": CAMPAIGN_NAME,
                    "status": "PAUSED",
                    "sequences": [
                        {
                            "seq_number": s["seq_number"],
                            "subject": s["subject"],
                            "delay_days": s["seq_delay_details"]["delay_in_days"],
                        }
                        for s in sequences["sequences"]
                    ],
                    "schedule": schedule,
                    "email_account_configured": account.isdigit(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    import httpx

    key = _api_key()
    if not key:
        print("Missing SMARTLEAD API key", file=sys.stderr)
        return 1

    create = httpx.post(
        f"{BASE}/campaigns/create",
        params={"api_key": key},
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        json={"name": CAMPAIGN_NAME},
        timeout=45,
    )
    create.raise_for_status()
    body = create.json() if create.content else {}
    campaign_id = body.get("id") or body.get("campaign_id")
    if not campaign_id:
        print(json.dumps(body, indent=2), file=sys.stderr)
        return 1
    campaign_id = int(campaign_id)

    seq = httpx.post(
        f"{BASE}/campaigns/{campaign_id}/sequences",
        params={"api_key": key},
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        json=sequences,
        timeout=45,
    )
    seq.raise_for_status()

    try:
        httpx.post(
            f"{BASE}/campaigns/{campaign_id}/schedule",
            params={"api_key": key},
            headers={"User-Agent": UA, "Content-Type": "application/json"},
            json=schedule,
            timeout=45,
        ).raise_for_status()
    except Exception as exc:
        print(f"schedule warning: {exc}", file=sys.stderr)

    if account.isdigit():
        try:
            httpx.post(
                f"{BASE}/campaigns/{campaign_id}/email-accounts",
                params={"api_key": key},
                headers={"User-Agent": UA, "Content-Type": "application/json"},
                json={"email_account_ids": [int(account)]},
                timeout=45,
            ).raise_for_status()
        except Exception as exc:
            print(f"email account attach warning: {exc}", file=sys.stderr)

    # Keep PAUSED until explicit OK (do not START).
    try:
        httpx.post(
            f"{BASE}/campaigns/{campaign_id}/status",
            params={"api_key": key},
            headers={"User-Agent": UA, "Content-Type": "application/json"},
            json={"status": "PAUSED"},
            timeout=45,
        ).raise_for_status()
    except Exception as exc:
        print(f"pause warning: {exc}", file=sys.stderr)

    out = {
        "campaign_id": campaign_id,
        "name": CAMPAIGN_NAME,
        "status": "PAUSED",
        "env": f"SMARTLEAD_RECKITT_CAMPAIGN_ID={campaign_id}",
    }
    path = DATA_DIR / "smartlead_campaign.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
        text = env_path.read_text(encoding="utf-8")
        line = f"SMARTLEAD_RECKITT_CAMPAIGN_ID={campaign_id}"
        if "SMARTLEAD_RECKITT_CAMPAIGN_ID=" in text:
            lines = []
            for raw in text.splitlines():
                if raw.startswith("SMARTLEAD_RECKITT_CAMPAIGN_ID="):
                    lines.append(line)
                else:
                    lines.append(raw)
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            with env_path.open("a", encoding="utf-8") as handle:
                handle.write(f"\n{line}\n")

    print(json.dumps(out, indent=2))
    print(f"\nSet env: SMARTLEAD_RECKITT_CAMPAIGN_ID={campaign_id}")
    return 0


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    raise SystemExit(main())
