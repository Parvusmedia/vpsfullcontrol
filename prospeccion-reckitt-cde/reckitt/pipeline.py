#!/usr/bin/env python3
"""CLI: CDE CSV → Icypeas → Smartlead / Unipile (Alarmas pattern, punctual Reckitt wave)."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reckitt.config import DATA_DIR, ReckittConfig, ensure_data_dirs, load_dotenv_files
from reckitt.csv_leads import load_csv, summarize_leads
from reckitt.email_pattern import examples_from_nocodb_rows, guess_email, learn_domain_patterns
from reckitt.icypeas import domain_for_company, icypeas_email_search
from reckitt.messages import compose_row_messages
from reckitt.smartlead import campaign_sequence_spec, enroll_lead
from reckitt.store import (
    list_all,
    list_relevantes,
    list_unipile_queue,
    load_leads,
    patch_record,
    queue_unipile_misses,
    upsert_leads,
)

logger = logging.getLogger("reckitt")


def _redact_email(email: str) -> str:
    raw = (email or "").strip()
    if "@" not in raw:
        return raw
    local, domain = raw.split("@", 1)
    if len(local) <= 2:
        masked = local[:1] + "*"
    else:
        masked = local[:2] + "***"
    return f"{masked}@{domain}"


def cmd_confirm(cfg: ReckittConfig) -> int:
    ensure_data_dirs()
    summary = cfg.summary()
    leads = load_leads(cfg=cfg)
    if not leads and Path(cfg.csv_path).is_file():
        try:
            leads = load_csv(cfg.csv_path)
            summary["csv_preview"] = summarize_leads(leads)
        except OSError as exc:
            summary["csv_preview_error"] = str(exc)
    elif leads:
        summary["store"] = summarize_leads(leads)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    spec = campaign_sequence_spec()
    print("\nSmartlead sequence (subjects):")
    print(
        json.dumps(
            {
                "name": spec["name"],
                "status_at_create": spec["status_at_create"],
                "steps": [{"step": s["step"], "delay_days": s["delay_days"], "subject": s["subject"]} for s in spec["steps"]],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_import_csv(cfg: ReckittConfig, csv_path: str | None, pendiente: bool) -> int:
    ensure_data_dirs()
    path = csv_path or cfg.csv_path
    relevante = "Pendiente" if pendiente else "Sí"
    leads = load_csv(path, relevante=relevante)
    for lead in leads:
        lead["source_task"] = cfg.cde_task_id
    result = upsert_leads(leads, cfg=cfg)
    stats = summarize_leads(load_leads(cfg=cfg))
    print(json.dumps({"import": result, "stats": stats, "csv": path, "relevante": relevante}, indent=2, ensure_ascii=False))
    return 0


def cmd_review(cfg: ReckittConfig, limit: int) -> int:
    rows = list_all(cfg=cfg, limit=limit)
    print(f"{len(rows)} leads in store\n")
    print("| Id | Nombre | Cargo | Email | LI | status | unipile | relevante |")
    print("|----|--------|-------|-------|----|--------|---------|-----------|")
    for row in rows:
        name = row.get("Title") or f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip()
        email = _redact_email(row.get("email") or "") or "—"
        li = "yes" if row.get("linkedin_url") else "no"
        print(
            f"| {row.get('Id')} | {name} | {row.get('job_title') or ''} | {email} | {li} | "
            f"{row.get('status') or ''} | {row.get('unipile_status') or ''} | {row.get('relevante') or ''} |"
        )
    stats = summarize_leads(rows)
    print("\n", json.dumps(stats, ensure_ascii=False))
    return 0


def cmd_compose_messages(cfg: ReckittConfig, live: bool, force: bool) -> int:
    rows = [r for r in load_leads(cfg=cfg) if (r.get("relevante") or "") == "Sí"]
    updated = skipped = 0
    previews = []
    for row in rows:
        if row.get("connection_message") and not force:
            skipped += 1
            continue
        msgs = compose_row_messages(row)
        preview = {
            "id": row.get("Id"),
            "name": row.get("first_name"),
            "note_chars": len(msgs["connection_message"]),
            "connection_message": msgs["connection_message"],
            "followup_message": msgs["followup_message"],
            "mensaje_estado": msgs["mensaje_estado"],
        }
        previews.append(preview)
        if live:
            patch_record(int(row["Id"]), msgs, cfg=cfg)
            updated += 1
        else:
            updated += 1
    print(
        json.dumps(
            {"dry_run": not live, "updated": updated, "skipped": skipped, "previews": previews[:8], "preview_count": len(previews)},
            indent=2,
            ensure_ascii=False,
        )
    )
    if not live:
        print("\nDry-run. Pass --live to write connection_message / followup_message (still Pendiente confirmar).")
    return 0


async def _contact_one(
    cfg: ReckittConfig,
    row: dict[str, Any],
    *,
    dry_run: bool,
    pattern_examples: list[dict[str, Any]] | None = None,
    domain_votes: dict | None = None,
) -> dict[str, Any]:
    rid = row.get("Id")
    first = row.get("first_name") or ""
    last = row.get("last_name") or ""
    company = row.get("company_name") or ""
    domain = domain_for_company(company, row.get("company_domain") or row.get("company_website"))
    linkedin = row.get("linkedin_url") or ""
    examples = pattern_examples or []
    votes = domain_votes

    email = (row.get("email") or "").strip()
    email_source = "existing" if email else ""
    icypeas_status = "skipped_existing_email"
    pattern_meta: dict[str, Any] | None = None

    if not email:
        if dry_run:
            icypeas_status = "dry_run_would_search_icypeas"
            guessed = guess_email(
                first_name=first,
                last_name=last,
                domain=domain,
                domain_votes=votes,
                examples=examples,
            )
            out: dict[str, Any] = {
                "id": rid,
                "channel": "icypeas_or_unipile",
                "email": None,
                "icypeas": icypeas_status,
                "domain": domain,
                "would_guess_pattern": bool(guessed and guessed.evidence >= 1),
                "linkedin": bool(linkedin),
            }
            if guessed and guessed.evidence >= 1:
                out["pattern"] = {
                    "pattern": guessed.pattern,
                    "evidence": guessed.evidence,
                    "email": _redact_email(guessed.email),
                }
            return out

        icy = await icypeas_email_search(
            api_key=cfg.icypeas_api_key,
            first_name=first,
            last_name=last,
            domain_or_company=domain,
        )
        email = (icy.get("email") or "") if isinstance(icy, dict) else ""
        icypeas_status = (icy or {}).get("status") or "unknown"
        if email:
            email_source = "icypeas"
            examples.append(
                {"email": email, "first_name": first, "last_name": last, "company_name": company}
            )
            if votes is not None:
                votes.clear()
                votes.update(learn_domain_patterns(examples))
            if rid:
                patch_record(
                    int(rid),
                    {"email": email, "email_source": "icypeas", "status": "icypeas_ok"},
                    cfg=cfg,
                )
        else:
            guessed = guess_email(
                first_name=first,
                last_name=last,
                domain=domain,
                domain_votes=votes,
                examples=examples,
            )
            if guessed and guessed.evidence >= 1:
                email = guessed.email
                email_source = f"pattern:{guessed.pattern}"
                pattern_meta = {
                    "pattern": guessed.pattern,
                    "evidence": guessed.evidence,
                    "examples": list(guessed.source_examples),
                }
                if rid:
                    patch_record(
                        int(rid),
                        {
                            "email": email,
                            "email_source": email_source,
                            "status": "icypeas_ok",
                            "notes": f"pattern_guess from {guessed.domain} ({guessed.pattern}, n={guessed.evidence})",
                        },
                        cfg=cfg,
                    )
            elif rid:
                patch_record(int(rid), {"status": "icypeas_miss", "email_source": "icypeas"}, cfg=cfg)

    if email:
        if not cfg.smartlead_enabled:
            out = {
                "id": rid,
                "channel": "email_held",
                "email": _redact_email(email),
                "email_source": email_source,
                "icypeas": icypeas_status,
                "result": {
                    "ok": True,
                    "skipped": True,
                    "reason": "smartlead_disabled_awaiting_copy_ok",
                },
            }
            if pattern_meta:
                out["pattern"] = pattern_meta
            if rid and not dry_run and email_source:
                patch_record(
                    int(rid),
                    {
                        "email": email,
                        "email_source": email_source or row.get("email_source") or "",
                        "status": "icypeas_ok",
                        "smartlead_status": "held_awaiting_copy",
                    },
                    cfg=cfg,
                )
            if dry_run:
                preview = enroll_lead(
                    cfg=cfg,
                    email=email,
                    first_name=first,
                    last_name=last,
                    company_name=company,
                    linkedin_url=linkedin,
                    job_title=row.get("job_title") or "",
                    location=row.get("location") or "",
                    reason_to_contact=row.get("reason_to_contact") or "",
                    dry_run=True,
                )
                out["channel"] = "smartlead"
                if isinstance(preview.get("lead"), dict) and preview["lead"].get("email"):
                    preview = {
                        **preview,
                        "lead": {**preview["lead"], "email": _redact_email(preview["lead"]["email"])},
                    }
                out["result"] = {
                    **preview,
                    "held": True,
                    "reason": "smartlead_disabled_awaiting_copy_ok",
                }
            return out

        result = enroll_lead(
            cfg=cfg,
            email=email,
            first_name=first,
            last_name=last,
            company_name=company,
            linkedin_url=linkedin,
            job_title=row.get("job_title") or "",
            location=row.get("location") or "",
            reason_to_contact=row.get("reason_to_contact") or "",
            dry_run=dry_run,
        )
        if result.get("ok") and rid and not dry_run:
            patch_record(
                int(rid),
                {
                    "status": "smartlead_enrolled",
                    "smartlead_status": "enrolled",
                    "email": email,
                    "email_source": email_source or row.get("email_source") or "",
                },
                cfg=cfg,
            )
        safe = dict(result)
        if isinstance(safe.get("lead"), dict) and safe["lead"].get("email"):
            safe["lead"] = {**safe["lead"], "email": _redact_email(safe["lead"]["email"])}
        out = {
            "id": rid,
            "channel": "smartlead",
            "email": _redact_email(email),
            "email_source": email_source,
            "icypeas": icypeas_status,
            "result": safe,
        }
        if pattern_meta:
            out["pattern"] = pattern_meta
        return out

    from reckitt.unipile import send_invite

    result = send_invite(
        cfg=cfg,
        linkedin_url=linkedin,
        first_name=first,
        company_name=company,
        dedupe_key=row.get("dedupe_key") or "",
        source_row_id=str(rid or ""),
        connection_message=row.get("connection_message") or "",
        dry_run=dry_run,
    )
    if result.get("ok") and rid and not dry_run:
        patch_record(int(rid), {"status": "unipile_sent", "unipile_status": "sent"}, cfg=cfg)
    elif rid and not dry_run and result.get("skipped") and result.get("reason") in {
        "daily_limit_reached",
        "hourly_limit_reached",
        "account_shared_daily_ceiling",
        "account_paused",
        "provider_limit",
    }:
        patch_record(
            int(rid),
            {"status": "hold", "unipile_status": "queued", "notes": f"held:{result.get('reason')}"},
            cfg=cfg,
        )
    return {"id": rid, "channel": "unipile", "icypeas": icypeas_status, "result": result}


def cmd_contact(cfg: ReckittConfig, limit: int, live: bool, csv_path: str | None) -> int:
    dry = not live
    if live:
        cfg.dry_run = False
    if csv_path or not load_leads(cfg=cfg):
        path = csv_path or cfg.csv_path
        if Path(path).is_file():
            imported = load_csv(path, relevante="Sí")
            for lead in imported:
                lead["source_task"] = cfg.cde_task_id
            upsert_leads(imported, cfg=cfg)
            print(json.dumps({"imported_from_csv": path, "rows": len(imported)}, ensure_ascii=False))
    rows = list_relevantes(cfg=cfg, limit=limit)
    all_rows = list_all(cfg=cfg, limit=500)
    examples = examples_from_nocodb_rows(all_rows)
    votes = learn_domain_patterns(examples)
    print(f"Contactando {len(rows)} filas relevante=Sí (dry_run={dry})")
    if votes:
        print("Email patterns aprendidos:", {d: dict(c) for d, c in votes.items()})
    results = []
    for row in rows:
        out = asyncio.run(
            _contact_one(cfg, row, dry_run=dry, pattern_examples=examples, domain_votes=votes)
        )
        results.append(out)
        print(json.dumps(out, ensure_ascii=False))
    path = DATA_DIR / "contact_results.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    channels: dict[str, int] = {}
    for item in results:
        channels[item.get("channel") or "unknown"] = channels.get(item.get("channel") or "unknown", 0) + 1
    print(json.dumps({"wrote": str(path), "channels": channels, "n": len(results)}, ensure_ascii=False))
    return 0


def cmd_queue_unipile(cfg: ReckittConfig) -> int:
    out = queue_unipile_misses(cfg=cfg)
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_sync_bounces(cfg: ReckittConfig, live: bool) -> int:
    from reckitt.smartlead import list_blocked_leads
    from reckitt.store import queue_bounced_to_unipile

    blocked = list_blocked_leads(cfg=cfg)
    print(
        json.dumps(
            {"blocked_found": len(blocked), "emails": [_redact_email(b.get("email") or "") for b in blocked]},
            ensure_ascii=False,
        )
    )
    if not live:
        print(json.dumps({"dry_run": True, "would_queue": len(blocked)}, ensure_ascii=False))
        return 0
    out = queue_bounced_to_unipile(cfg=cfg, blocked=blocked)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_unipile_drain(cfg: ReckittConfig, live: bool, limit: int | None) -> int:
    from reckitt import automation_limits as alimits
    from reckitt.unipile import send_invite

    dry = not live
    if live:
        cfg.dry_run = False
    cfg.assert_unipile_seat()

    if live:
        queued = list_unipile_queue(cfg=cfg, limit=200)
        unconfirmed = [
            r
            for r in queued
            if (r.get("mensaje_estado") or "").strip() != "Confirmado"
        ]
        if unconfirmed:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "linkedin_copy_not_confirmed",
                        "unconfirmed": len(unconfirmed),
                        "hint": "Run ./run.sh compose-messages --live, review notes, set mensaje_estado=Confirmado",
                    },
                    ensure_ascii=False,
                )
            )
            return 1

    rule = alimits.ensure_reckitt_limit_row(cfg=cfg)
    gate = alimits.check_invite_gate(cfg=cfg, rule=rule)
    print(
        json.dumps(
            {
                "dry_run": dry,
                "limit_key": rule.limit_key,
                "account_id": rule.account_id,
                "daily_limit": rule.daily_limit,
                "hourly_limit": rule.hourly_limit,
                "gate": gate.reason,
                "daily_count": gate.daily_count,
                "hourly_count": gate.hourly_count,
                "account_count": gate.account_count,
                "remaining_today": gate.remaining_today,
                "paused_until": rule.paused_until,
            },
            ensure_ascii=False,
        )
    )
    if not gate.ok:
        print("No envíos: gate cerrado (respetando automation_limits / techo de cuenta).")
        if not dry:
            return 0
        rows = list_unipile_queue(cfg=cfg, limit=limit or 10)
        for row in rows:
            print(
                json.dumps(
                    {
                        "id": row.get("Id"),
                        "name": row.get("first_name"),
                        "company": row.get("company_name"),
                        "would_send": False,
                        "blocked_by": gate.reason,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    budget = gate.remaining_today
    if rule.hourly_limit is not None:
        budget = min(budget, max(0, rule.hourly_limit - gate.hourly_count))
    if limit is not None:
        budget = min(budget, limit)
    if budget <= 0:
        print("Budget 0 para este ciclo.")
        return 0

    rows = list_unipile_queue(cfg=cfg, limit=200)
    rows = rows[:budget]

    print(f"Cola Unipile: {len(rows)} a procesar (budget={budget}, dry_run={dry})")
    results = []
    for row in rows:
        rid = row.get("Id")
        result = send_invite(
            cfg=cfg,
            linkedin_url=row.get("linkedin_url") or "",
            first_name=row.get("first_name") or "",
            company_name=row.get("company_name") or "",
            dedupe_key=row.get("dedupe_key") or "",
            source_row_id=str(rid or ""),
            connection_message=row.get("connection_message") or "",
            dry_run=dry,
            sleep_before=not dry,
        )
        out = {"id": rid, "name": row.get("first_name"), "company": row.get("company_name"), "result": result}
        results.append(out)
        print(json.dumps(out, ensure_ascii=False))
        if result.get("ok") and rid and not dry:
            patch_record(int(rid), {"status": "unipile_sent", "unipile_status": "sent"}, cfg=cfg)
        elif not dry and result.get("reason") in {
            "daily_limit_reached",
            "hourly_limit_reached",
            "account_shared_daily_ceiling",
            "account_paused",
            "provider_limit",
        }:
            print("Stop: límite alcanzado en mitad del ciclo.")
            break
        if not dry:
            gate = alimits.check_invite_gate(cfg=cfg, rule=rule)
            if not gate.ok:
                print(f"Stop: gate={gate.reason}")
                break

    path = DATA_DIR / "unipile_drain_results.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path}")
    return 0


def cmd_create_campaign(argv: list[str]) -> int:
    from reckitt.create_smartlead_campaign import main as create_main

    return create_main(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv_files()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(prog="reckitt")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("confirm")
    p_imp = sub.add_parser("import-csv", help="Load CDE Sales Nav CSV into data/leads.json")
    p_imp.add_argument("--csv", dest="csv_path", default=None)
    p_imp.add_argument("--pendiente", action="store_true", help="Import with relevante=Pendiente (default Sí)")
    p_rev = sub.add_parser("review", help="List stored leads")
    p_rev.add_argument("--limit", type=int, default=100)
    p_con = sub.add_parser("contact", help="Contact relevante=Sí (Icypeas → Smartlead | Unipile)")
    p_con.add_argument("--limit", type=int, default=20)
    p_con.add_argument("--live", action="store_true", help="Actually send (default dry-run)")
    p_con.add_argument("--csv", dest="csv_path", default=None)
    p_create = sub.add_parser("create-smartlead", help="Create dedicated Smartlead campaign + sequences (PAUSED)")
    p_create.add_argument("--force", action="store_true")
    p_create.add_argument("--dry-run", action="store_true")
    sub.add_parser("push-smartlead-copy", help="Update email sequences on existing Smartlead campaign")
    sub.add_parser("smartlead-start", help="Set Smartlead campaign START (only after copy OK)")
    p_msg = sub.add_parser("compose-messages", help="Draft LinkedIn connection + follow-up copy")
    p_msg.add_argument("--live", action="store_true")
    p_msg.add_argument("--force", action="store_true")
    sub.add_parser("queue-unipile", help="Mark no-email relevantes as unipile_queued")
    p_bounce = sub.add_parser("sync-bounces", help="Smartlead BLOCKED/bounced → Unipile queue")
    p_bounce.add_argument("--live", action="store_true")
    p_drain = sub.add_parser("unipile-drain", help="Drain Unipile queue (≤ automation_limits)")
    p_drain.add_argument("--live", action="store_true")
    p_drain.add_argument("--limit", type=int, default=None)

    args = parser.parse_args(argv)
    cfg = ReckittConfig.from_env()

    if args.cmd == "confirm":
        return cmd_confirm(cfg)
    if args.cmd == "import-csv":
        return cmd_import_csv(cfg, args.csv_path, args.pendiente)
    if args.cmd == "review":
        return cmd_review(cfg, args.limit)
    if args.cmd == "contact":
        return cmd_contact(cfg, args.limit, args.live, args.csv_path)
    if args.cmd == "create-smartlead":
        extra = []
        if args.force:
            extra.append("--force")
        if args.dry_run:
            extra.append("--dry-run")
        return cmd_create_campaign(extra)
    if args.cmd == "push-smartlead-copy":
        from reckitt.smartlead import push_sequences

        out = push_sequences(cfg=cfg)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 1
    if args.cmd == "smartlead-start":
        from reckitt.smartlead import set_campaign_status

        out = set_campaign_status(cfg=cfg, status="START")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 1
    if args.cmd == "compose-messages":
        return cmd_compose_messages(cfg, args.live, args.force)
    if args.cmd == "queue-unipile":
        return cmd_queue_unipile(cfg)
    if args.cmd == "sync-bounces":
        return cmd_sync_bounces(cfg, args.live)
    if args.cmd == "unipile-drain":
        return cmd_unipile_drain(cfg, args.live, args.limit)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
