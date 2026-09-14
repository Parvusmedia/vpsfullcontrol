"""Local JSON lead store (punctual CSV wave — NocoDB optional for limits only)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ReckittConfig, ensure_data_dirs
from .csv_leads import profile_dedupe_key


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def leads_path(cfg: ReckittConfig | None = None) -> Path:
    from . import config as cfg_mod

    return cfg_mod.LEADS_PATH


def load_leads(*, cfg: ReckittConfig | None = None) -> list[dict[str, Any]]:
    path = leads_path(cfg)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rows = data.get("leads") or []
    else:
        rows = data
    return [r for r in rows if isinstance(r, dict)]


def save_leads(rows: list[dict[str, Any]], *, cfg: ReckittConfig | None = None) -> Path:
    ensure_data_dirs()
    path = leads_path(cfg)
    payload = {"updated_at": _utcnow(), "leads": rows}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _next_id(rows: list[dict[str, Any]]) -> int:
    ids = [int(r["Id"]) for r in rows if str(r.get("Id") or "").isdigit()]
    return (max(ids) + 1) if ids else 1


def upsert_leads(incoming: list[dict[str, Any]], *, cfg: ReckittConfig | None = None) -> dict[str, Any]:
    rows = load_leads(cfg=cfg)
    by_key = {str(r.get("dedupe_key") or ""): r for r in rows if r.get("dedupe_key")}
    created = updated = 0
    for lead in incoming:
        key = str(lead.get("dedupe_key") or profile_dedupe_key(lead) or "")
        lead["dedupe_key"] = key
        lead["last_touch_at"] = _utcnow()
        existing = by_key.get(key) if key else None
        if existing:
            rid = existing.get("Id")
            for field in (
                "relevante",
                "status",
                "smartlead_status",
                "unipile_status",
                "mensaje_estado",
                "connection_message",
                "followup_message",
                "notes",
                "email",
            ):
                if existing.get(field) and field in lead and field != "email":
                    # Keep human / pipeline state unless incoming has a richer email
                    lead.pop(field, None)
                elif field == "email" and existing.get("email") and not lead.get("email"):
                    lead.pop("email", None)
            existing.update({k: v for k, v in lead.items() if v not in (None, "")})
            existing["Id"] = rid
            updated += 1
        else:
            lead["Id"] = _next_id(rows)
            rows.append(lead)
            if key:
                by_key[key] = lead
            created += 1
    save_leads(rows, cfg=cfg)
    return {"ok": True, "created": created, "updated": updated, "total": len(rows), "path": str(leads_path(cfg))}


def patch_record(record_id: int, fields: dict[str, Any], *, cfg: ReckittConfig | None = None) -> dict[str, Any]:
    rows = load_leads(cfg=cfg)
    found = False
    for row in rows:
        if int(row.get("Id") or 0) != int(record_id):
            continue
        row.update(fields)
        row["last_touch_at"] = _utcnow()
        found = True
        break
    if not found:
        return {"ok": False, "error": "not_found", "id": record_id}
    save_leads(rows, cfg=cfg)
    return {"ok": True, "id": record_id}


def list_relevantes(*, cfg: ReckittConfig | None = None, limit: int = 100) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in load_leads(cfg=cfg):
        if (row.get("relevante") or "") != "Sí":
            continue
        status = (row.get("status") or "").strip()
        if status in {"smartlead_enrolled", "unipile_sent", "hold", "dropped"}:
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out


def list_all(*, cfg: ReckittConfig | None = None, limit: int = 500) -> list[dict[str, Any]]:
    return load_leads(cfg=cfg)[:limit]


def list_unipile_queue(*, cfg: ReckittConfig | None = None, limit: int = 100) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in load_leads(cfg=cfg):
        if (row.get("relevante") or "") != "Sí":
            continue
        status = (row.get("status") or "").strip()
        unipile = (row.get("unipile_status") or "").strip().lower()
        email = (row.get("email") or "").strip()
        if status == "unipile_sent" or status == "dropped":
            continue
        if status == "hold" and unipile in {"queued", "bounce_queued"}:
            out.append(row)
        elif status == "icypeas_miss" and not email:
            out.append(row)
        elif unipile == "queued" and status != "smartlead_enrolled":
            out.append(row)
        if len(out) >= limit:
            break
    return out


def queue_unipile_misses(*, cfg: ReckittConfig | None = None) -> dict[str, Any]:
    rows = load_leads(cfg=cfg)
    queued = skipped = 0
    for row in rows:
        if (row.get("relevante") or "") != "Sí":
            skipped += 1
            continue
        email = (row.get("email") or "").strip()
        status = (row.get("status") or "").strip()
        if email or status in {"unipile_sent", "dropped", "smartlead_enrolled"}:
            skipped += 1
            continue
        if status == "hold" and (row.get("unipile_status") or "").strip().lower() in {"queued", "bounce_queued"}:
            skipped += 1
            continue
        row["status"] = "hold"
        row["unipile_status"] = "queued"
        row["notes"] = "queued_for_unipile_priority"
        row["last_touch_at"] = _utcnow()
        queued += 1
    save_leads(rows, cfg=cfg)
    return {"ok": True, "queued": queued, "skipped": skipped}


def find_by_email(*, cfg: ReckittConfig | None = None, email: str) -> dict[str, Any] | None:
    email_clean = (email or "").strip().lower()
    if not email_clean or "@" not in email_clean:
        return None
    for row in load_leads(cfg=cfg):
        if (row.get("email") or "").strip().lower() == email_clean:
            return row
    return None


def queue_bounced_to_unipile(*, cfg: ReckittConfig | None = None, blocked: list[dict[str, Any]]) -> dict[str, Any]:
    queued = skipped = missing = 0
    details: list[dict[str, Any]] = []
    for item in blocked:
        email = (item.get("email") or "").strip().lower()
        if not email:
            missing += 1
            continue
        row = find_by_email(cfg=cfg, email=email)
        if not row:
            missing += 1
            details.append({"email": email, "action": "missing_store"})
            continue
        rid = row.get("Id")
        status = (row.get("status") or "").strip()
        unipile = (row.get("unipile_status") or "").strip().lower()
        if status == "unipile_sent":
            skipped += 1
            details.append({"email": email, "id": rid, "action": "already_unipile_sent"})
            continue
        if status == "hold" and unipile in {"queued", "bounce_queued"}:
            skipped += 1
            details.append({"email": email, "id": rid, "action": "already_queued"})
            continue
        linkedin = (row.get("linkedin_url") or item.get("linkedin_url") or "").strip()
        if not linkedin:
            skipped += 1
            details.append({"email": email, "id": rid, "action": "missing_linkedin"})
            continue
        patch_record(
            int(rid),
            {
                "status": "hold",
                "unipile_status": "bounce_queued",
                "smartlead_status": "bounced",
                "notes": "smartlead_blocked_to_unipile",
                "linkedin_url": linkedin,
            },
            cfg=cfg,
        )
        queued += 1
        details.append({"email": email, "id": rid, "action": "queued"})
    return {"ok": True, "queued": queued, "skipped": skipped, "missing": missing, "details": details}
