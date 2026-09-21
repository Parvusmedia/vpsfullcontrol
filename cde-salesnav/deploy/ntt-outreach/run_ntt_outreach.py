#!/usr/bin/env python3
"""NTT DATA outreach: Smartlead (email) + Unipile InMail (no email) from Sales Nav CSV."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONSULTORAS = Path("/opt/apps/prospeccion-consultoras")
if CONSULTORAS.exists() and str(CONSULTORAS) not in sys.path:
    sys.path.insert(0, str(CONSULTORAS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import (  # type: ignore[import-not-found]
    INMAIL_DAILY_LIMIT,
    outreach_locale,
    send_unipile_inmail,
)
from smartlead import enroll_lead, smartlead_enabled  # type: ignore[import-not-found]
from smartlead_ntt import ENV_CAMPAIGN_EN, ENV_CAMPAIGN_ES, campaign_id_for_locale, create_campaign

DATA_DIR = CONSULTORAS / "data" if CONSULTORAS.exists() else ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_env() -> None:
    for path in (Path("/etc/linkedinreport/app.env"), CONSULTORAS / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_ntt_inmail_message(lead: dict) -> str:
    first = (lead.get("first_name") or "there").strip()
    loc = outreach_locale(lead)
    if loc == "es":
        return (
            f"Hola {first},\n\n"
            "Encantado. Busco contactar con alguien de NTT DATA en Martech o marketing automation.\n\n"
            "Soy consultor externo y trabajo con agencias o consultoras. Me gustaría explorar colaborar en "
            "proyectos en NTT DATA. Tengo +20 años de experiencia entre gestión de proyectos e implementación "
            "(automatización, campañas, analítica, con y sin IA).\n\n"
            "¿Crees que podría haber encaje para colaborar, o te agradezco si me indicas a quién contactar?\n\n"
            "Muchas gracias,\nEmiliano"
        )
    return (
        f"Hi {first},\n\n"
        "Nice to meet you. I'm looking to connect with someone at NTT DATA in MarTech or marketing automation.\n\n"
        "I'm an external consultant and work with agencies and consultancies. I'd like to explore collaborating "
        "on projects at NTT DATA. I have 20+ years of experience across project management and hands-on delivery "
        "(automation, campaigns, analytics, with and without AI).\n\n"
        "Do you think there could be a fit to collaborate, or could you point me to the right person to speak with?\n\n"
        "Thank you,\nEmiliano"
    )


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def split_leads(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    with_email: list[dict] = []
    no_email: list[dict] = []
    for row in rows:
        email = (row.get("work_email") or row.get("email") or "").strip().lower()
        if email and "@" in email:
            row = dict(row)
            row["work_email"] = email
            with_email.append(row)
        elif (row.get("linkedin_url") or "").strip():
            no_email.append(row)
    return with_email, no_email


def append_env_campaign_ids(results: list[dict]) -> None:
    env_path = CONSULTORAS / ".env"
    if not env_path.exists():
        return
    text = env_path.read_text(encoding="utf-8")
    for item in results:
        line = item.get("env_line") or ""
        if not line or "=" not in line:
            continue
        key = line.split("=", 1)[0]
        if f"{key}=" in text:
            continue
        if not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
    env_path.write_text(text, encoding="utf-8")


def cmd_create_campaigns(_: argparse.Namespace) -> int:
    results = []
    for locale in ("es", "en"):
        if campaign_id_for_locale(locale):
            print(f"skip {locale}: campaign id already set ({campaign_id_for_locale(locale)})")
            continue
        print(f"Creating Smartlead campaign {locale.upper()}…")
        results.append(create_campaign(locale=locale))
    if results:
        append_env_campaign_ids(results)
    out = DATA_DIR / "ntt_smartlead_campaigns.json"
    payload = {"campaigns": results, "existing_es": campaign_id_for_locale("es"), "existing_en": campaign_id_for_locale("en")}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def start_campaigns(locales: tuple[str, ...] = ("es", "en")) -> list[dict]:
    import httpx
    from smartlead import BASE, _UA, smartlead_api_key  # type: ignore[import-not-found]

    key = smartlead_api_key()
    out: list[dict] = []
    for loc in locales:
        cid = campaign_id_for_locale(loc)
        if not cid or not key:
            out.append({"locale": loc, "ok": False, "reason": "missing_id_or_key"})
            continue
        resp = httpx.post(
            f"{BASE}/campaigns/{cid}/status",
            params={"api_key": key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json={"status": "START"},
            timeout=45,
        )
        out.append({"locale": loc, "campaign_id": cid, "ok": resp.status_code < 400, "http_status": resp.status_code})
    return out


def cmd_start_campaigns(_: argparse.Namespace) -> int:
    results = start_campaigns()
    print(json.dumps({"started": results}, indent=2))
    return 0


def cmd_enroll(args: argparse.Namespace) -> int:
    rows = read_csv(Path(args.csv))
    with_email, _ = split_leads(rows)
    dry = not args.live
    results = []
    for row in with_email:
        loc = outreach_locale(row)
        camp = campaign_id_for_locale(loc)
        if not camp:
            results.append({"email": row["work_email"], "ok": False, "reason": "missing_campaign_id"})
            continue
        out = enroll_lead(
            email=row["work_email"],
            first_name=row.get("first_name") or "",
            last_name=row.get("last_name") or "",
            company_name="NTT DATA",
            linkedin_url=row.get("linkedin_url") or "",
            job_title=row.get("job_title") or "",
            campaign_id=camp,
            dry_run=dry,
        )
        out["email"] = row["work_email"]
        out["locale"] = loc
        results.append(out)
        print(json.dumps(out, ensure_ascii=False))
    path = DATA_DIR / "ntt_smartlead_enroll.json"
    path.write_text(json.dumps({"dry_run": dry, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    if not dry and not smartlead_enabled():
        print("warning: CONSULTORAS_SMARTLEAD_ENABLED is not true — enroll may have been skipped")
    if args.live and args.start:
        started = start_campaigns()
        print(json.dumps({"started": started}, indent=2))
    return 0


def cmd_inmail(args: argparse.Namespace) -> int:
    rows = read_csv(Path(args.csv))
    _, no_email = split_leads(rows)
    dry = not args.live
    limit = args.limit or INMAIL_DAILY_LIMIT
    wait_min, wait_max = args.wait_min, args.wait_max
    results = []
    sent = 0
    for row in no_email:
        if sent >= limit:
            break
        url = (row.get("linkedin_url") or "").strip()
        text = build_ntt_inmail_message(row)
        out = send_unipile_inmail(linkedin_url=url, text=text, dry_run=dry)
        out["name"] = f"{row.get('first_name')} {row.get('last_name')}".strip()
        out["linkedin_url"] = url
        out["locale"] = outreach_locale(row)
        results.append(out)
        print(json.dumps({k: out[k] for k in out if k != "text_preview"}, ensure_ascii=False))
        if out.get("ok") and not dry:
            sent += 1
            if sent < limit and wait_max > 0:
                wait = random.randint(wait_min, wait_max)
                print(f"wait {wait}s…")
                time.sleep(wait)
    path = DATA_DIR / "ntt_inmail_results.json"
    path.write_text(
        json.dumps(
            {
                "dry_run": dry,
                "limit": limit,
                "attempted": len(results),
                "sent_live": sent,
                "pending": max(0, len(no_email) - len(results)),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"wrote {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("create-campaigns").set_defaults(func=cmd_create_campaigns)
    p_en = sub.add_parser("enroll")
    p_en.add_argument("--csv", required=True)
    p_en.add_argument("--live", action="store_true")
    p_en.add_argument("--start", action="store_true", help="START campaigns after enroll (live only)")
    p_en.set_defaults(func=cmd_enroll)
    sub.add_parser("start-campaigns").set_defaults(func=cmd_start_campaigns)
    p_in = sub.add_parser("inmail")
    p_in.add_argument("--csv", required=True)
    p_in.add_argument("--live", action="store_true")
    p_in.add_argument("--limit", type=int, default=INMAIL_DAILY_LIMIT)
    p_in.add_argument("--wait-min", type=int, default=30)
    p_in.add_argument("--wait-max", type=int, default=90)
    p_in.set_defaults(func=cmd_inmail)
    args = parser.parse_args()
    _load_env()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
