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
    SPANISH_SPEAKING_MARKERS,
    outreach_locale,
    send_unipile_inmail,
)

# Ubicaciones hispanohablantes que no traen país en el CSV de Sales Nav.
NTT_EXTRA_SPANISH_MARKERS = (
    "Madrid",
    "Barcelona",
    "Valencia",
    "Seville",
    "Sevilla",
    "Bilbao",
    "Latam",
    "Latin America",
    "América Latina",
    "Bogotá",
    "Bogota",
    "Buenos Aires",
    "Santiago",
    "Valparaíso",
    "Valparaiso",
    "Lima",
    "Montevideo",
    "Quito",
    "Caracas",
    "Ciudad de México",
    "Mexico City",
)
from smartlead import enroll_lead, smartlead_enabled  # type: ignore[import-not-found]
from smartlead_ntt import ENV_CAMPAIGN_EN, ENV_CAMPAIGN_ES, campaign_id_for_locale, create_campaign

DATA_DIR = CONSULTORAS / "data" if CONSULTORAS.exists() else ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
INMAIL_RESULTS_PATH = DATA_DIR / "ntt_inmail_results.json"
INMAIL_HISTORY_PATH = DATA_DIR / "ntt_inmail_sent_urls.json"


def ntt_outreach_locale(lead: dict) -> str:
    country = str(lead.get("country") or lead.get("location") or "")
    if any(marker in country for marker in SPANISH_SPEAKING_MARKERS):
        return "es"
    if any(marker in country for marker in NTT_EXTRA_SPANISH_MARKERS):
        return "es"
    return outreach_locale(lead)


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
    loc = ntt_outreach_locale(lead)
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


def normalize_linkedin_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if u and "?" in u:
        u = u.split("?", 1)[0]
    return u


def load_sent_inmail_urls() -> set[str]:
    urls: set[str] = set()
    if INMAIL_HISTORY_PATH.exists():
        try:
            data = json.loads(INMAIL_HISTORY_PATH.read_text(encoding="utf-8"))
            urls.update(normalize_linkedin_url(u) for u in data.get("urls") or [])
        except json.JSONDecodeError:
            pass
    if INMAIL_RESULTS_PATH.exists():
        try:
            data = json.loads(INMAIL_RESULTS_PATH.read_text(encoding="utf-8"))
            for row in data.get("results") or []:
                if row.get("ok") and not row.get("dry_run"):
                    urls.add(normalize_linkedin_url(str(row.get("linkedin_url") or "")))
        except json.JSONDecodeError:
            pass
    return {u for u in urls if u}


def save_sent_inmail_urls(urls: set[str]) -> None:
    INMAIL_HISTORY_PATH.write_text(
        json.dumps({"urls": sorted(urls)}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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


def smartlead_lead_id_for_campaign(*, campaign_id: str, email: str) -> int | None:
    import httpx
    from smartlead import BASE, _UA, smartlead_api_key  # type: ignore[import-not-found]

    key = smartlead_api_key()
    email_clean = (email or "").strip().lower()
    if not key or not campaign_id or not email_clean:
        return None
    resp = httpx.get(
        f"{BASE}/campaigns/{campaign_id}/leads",
        params={"api_key": key, "limit": 100},
        headers={"User-Agent": _UA},
        timeout=45,
    )
    if resp.status_code >= 400:
        return None
    body = resp.json() if resp.content else {}
    rows = body if isinstance(body, list) else body.get("data") or body.get("leads") or []
    for row in rows:
        if not isinstance(row, dict):
            continue
        lead = row.get("lead") if isinstance(row.get("lead"), dict) else row
        em = str(lead.get("email") or row.get("email") or "").strip().lower()
        if em == email_clean:
            lid = lead.get("id") or row.get("lead_id") or row.get("id")
            if lid is not None:
                return int(lid)
    lookup = httpx.get(
        f"{BASE}/leads/",
        params={"api_key": key, "email": email_clean},
        headers={"User-Agent": _UA},
        timeout=45,
    )
    if lookup.status_code >= 400 or not lookup.content:
        return None
    info = lookup.json()
    if not isinstance(info, dict) or not info:
        return None
    for camp in info.get("lead_campaign_data") or info.get("campaigns") or []:
        if str(camp.get("campaign_id")) == str(campaign_id):
            lid = camp.get("lead_id") or info.get("id")
            if lid is not None:
                return int(lid)
    return int(info["id"]) if info.get("id") else None


def delete_lead_from_campaign(*, campaign_id: str, email: str) -> dict:
    import httpx
    from smartlead import BASE, _UA, smartlead_api_key  # type: ignore[import-not-found]

    key = smartlead_api_key()
    email_clean = (email or "").strip().lower()
    if not key or not campaign_id or not email_clean:
        return {"ok": False, "reason": "missing_params"}
    lead_id = smartlead_lead_id_for_campaign(campaign_id=campaign_id, email=email_clean)
    if not lead_id:
        return {"ok": False, "reason": "lead_not_found_in_campaign", "email": email_clean}
    resp = httpx.delete(
        f"{BASE}/campaigns/{campaign_id}/leads/{lead_id}",
        params={"api_key": key},
        headers={"User-Agent": _UA},
        timeout=45,
    )
    return {
        "ok": resp.status_code < 400,
        "http_status": resp.status_code,
        "lead_id": lead_id,
        "body": (resp.text or "")[:300],
    }


def cmd_fix_smartlead_locale(args: argparse.Namespace) -> int:
    """Re-enroll leads that should be ES but were placed in EN (e.g. Madrid without 'Spain')."""
    rows = read_csv(Path(args.csv))
    with_email, _ = split_leads(rows)
    en_camp = campaign_id_for_locale("en")
    es_camp = campaign_id_for_locale("es")
    fixes = []
    for row in with_email:
        loc = ntt_outreach_locale(row)
        email = row["work_email"]
        if loc != "es":
            continue
        if args.live and en_camp:
            removed = delete_lead_from_campaign(campaign_id=en_camp, email=email)
        else:
            removed = {"ok": True, "dry_run": True}
        out = enroll_lead(
            email=email,
            first_name=row.get("first_name") or "",
            last_name=row.get("last_name") or "",
            company_name="NTT DATA",
            linkedin_url=row.get("linkedin_url") or "",
            job_title=row.get("job_title") or "",
            campaign_id=es_camp,
            dry_run=not args.live,
        )
        fixes.append({"email": email, "locale": loc, "removed_from_en": removed, "enroll_es": out})
        print(json.dumps(fixes[-1], ensure_ascii=False))
    path = DATA_DIR / "ntt_smartlead_locale_fix.json"
    path.write_text(json.dumps({"fixes": fixes}, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


def cmd_enroll(args: argparse.Namespace) -> int:
    rows = read_csv(Path(args.csv))
    with_email, _ = split_leads(rows)
    dry = not args.live
    results = []
    for row in with_email:
        loc = ntt_outreach_locale(row)
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
    skip_sent = not args.no_skip_sent
    already_sent = load_sent_inmail_urls() if skip_sent else set()
    results = []
    sent = 0
    skipped = 0
    for row in no_email:
        if sent >= limit:
            break
        url = (row.get("linkedin_url") or "").strip()
        norm = normalize_linkedin_url(url)
        if norm in already_sent:
            skipped += 1
            continue
        text = build_ntt_inmail_message(row)
        try:
            out = send_unipile_inmail(linkedin_url=url, text=text, dry_run=dry)
        except Exception as exc:
            out = {"ok": False, "error": str(exc)[:500]}
        out["name"] = f"{row.get('first_name')} {row.get('last_name')}".strip()
        out["linkedin_url"] = url
        out["locale"] = ntt_outreach_locale(row)
        results.append(out)
        print(json.dumps({k: out[k] for k in out if k != "text_preview"}, ensure_ascii=False))
        if out.get("ok") and not dry:
            sent += 1
            already_sent.add(norm)
            save_sent_inmail_urls(already_sent)
            if sent < limit and wait_max > 0:
                wait = random.randint(wait_min, wait_max)
                print(f"wait {wait}s…")
                time.sleep(wait)
    if not dry and already_sent:
        save_sent_inmail_urls(already_sent)
    path = INMAIL_RESULTS_PATH
    prior: list[dict] = []
    if path.exists() and skip_sent:
        try:
            prior = json.loads(path.read_text(encoding="utf-8")).get("results") or []
        except json.JSONDecodeError:
            prior = []
    merged_results = prior + results if skip_sent and not dry else results
    path.write_text(
        json.dumps(
            {
                "dry_run": dry,
                "limit": limit,
                "skipped_already_sent": skipped,
                "attempted": len(results),
                "sent_live": sent,
                "pending": max(0, len(no_email) - skipped - len([r for r in merged_results if r.get("ok")])),
                "results": merged_results,
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
    p_fix = sub.add_parser("fix-smartlead-locale")
    p_fix.add_argument("--csv", required=True)
    p_fix.add_argument("--live", action="store_true")
    p_fix.set_defaults(func=cmd_fix_smartlead_locale)
    sub.add_parser("start-campaigns").set_defaults(func=cmd_start_campaigns)
    p_in = sub.add_parser("inmail")
    p_in.add_argument("--csv", required=True)
    p_in.add_argument("--live", action="store_true")
    p_in.add_argument("--limit", type=int, default=INMAIL_DAILY_LIMIT)
    p_in.add_argument("--wait-min", type=int, default=30)
    p_in.add_argument("--wait-max", type=int, default=90)
    p_in.add_argument(
        "--no-skip-sent",
        action="store_true",
        help="Do not skip LinkedIn URLs already sent (from ntt_inmail_results / history)",
    )
    p_in.set_defaults(func=cmd_inmail)
    args = parser.parse_args()
    _load_env()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
