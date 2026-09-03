"""NocoDB upsert for cde_salesnav (mcu2bt73u6vlybz)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from .clean import clean_lead
from .config import CdeConfig
from .ai_filter import ai_reference_hit

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _headers(cfg: CdeConfig) -> dict[str, str]:
    return {
        "xc-token": cfg.nocodb_api_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def row_from_lead(lead: dict[str, Any], *, cfg: CdeConfig, status: str | None = None) -> dict[str, Any]:
    cleaned = clean_lead(lead)
    first = cleaned.get("first_name") or ""
    last = cleaned.get("last_name") or ""
    company = cleaned.get("company_name") or ""
    title_display = " ".join(x for x in [first, last] if x) or company or cleaned.get("dedupe_key") or "lead"
    employees = cleaned.get("company_employees")
    job_title = cleaned.get("job_title") or ""
    row: dict[str, Any] = {
        "Title": title_display,
        "dedupe_key": cleaned.get("dedupe_key") or "",
        "linkedin_url": cleaned.get("linkedin_url") or "",
        "first_name": first,
        "last_name": last,
        "job_title": job_title,
        "sn_title": cleaned.get("sn_title") or job_title,
        "headline": cleaned.get("headline") or "",
        "location": cleaned.get("location") or "",
        "company_name": company,
        "sn_company": cleaned.get("sn_company") or company,
        "industry": cleaned.get("industry") or "",
        "company_employees": employees,
        "company_size": cleaned.get("company_size") or employees,
        "premium": bool(cleaned.get("premium")),
        "open_profile": bool(cleaned.get("open_profile")),
        "public_identifier": cleaned.get("public_identifier") or "",
        "reason_to_contact": cleaned.get("reason_to_contact") or "",
        "relevante": cleaned.get("relevante") or "Pendiente",
        "status": status or cleaned.get("status") or "discovered",
        "source": cleaned.get("source") or "unipile",
        "campaign": cfg.campaign,
        "notes": cleaned.get("notes") or "",
        "last_touch_at": _utcnow(),
    }
    optional_empty = (
        "headline",
        "reason_to_contact",
        "notes",
        "industry",
        "public_identifier",
        "company_size",
        "linkedin_url",
    )
    for key in optional_empty:
        if not row.get(key):
            row.pop(key, None)
    return {k: v for k, v in row.items() if v is not None and v != ""}


def find_by_dedupe_key(*, cfg: CdeConfig, dedupe_key: str) -> dict[str, Any] | None:
    if not dedupe_key:
        return None
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/tables/{cfg.nocodb_table_id}/records",
        params={"where": f"(dedupe_key,eq,{dedupe_key})", "limit": 1},
        headers=_headers(cfg),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("list") if isinstance(data, dict) else None
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


def upsert_lead(lead: dict[str, Any], *, cfg: CdeConfig | None = None, status: str | None = None) -> dict[str, Any]:
    cfg = cfg or CdeConfig.from_env()
    if not cfg.nocodb_api_token:
        return {"ok": False, "skipped": True, "reason": "missing_nocodb_token"}
    row = row_from_lead(lead, cfg=cfg, status=status)
    dedupe = row.get("dedupe_key") or ""
    existing = find_by_dedupe_key(cfg=cfg, dedupe_key=dedupe)
    try:
        if existing and existing.get("Id") is not None:
            rid = existing["Id"]
            if existing.get("relevante") in {"Sí", "Si", "si", "No", "no"} and "relevante" in row:
                row.pop("relevante", None)
            resp = httpx.patch(
                f"{cfg.nocodb_base_url}/api/v2/tables/{cfg.nocodb_table_id}/records",
                headers=_headers(cfg),
                json={"Id": rid, **row},
                timeout=45,
            )
            resp.raise_for_status()
            return {"ok": True, "action": "update", "id": rid, "dedupe_key": dedupe, "title": row.get("Title")}
        resp = httpx.post(
            f"{cfg.nocodb_base_url}/api/v2/tables/{cfg.nocodb_table_id}/records",
            headers=_headers(cfg),
            json=row,
            timeout=45,
        )
        resp.raise_for_status()
        body = resp.json() if resp.content else {}
        rid = body.get("Id") if isinstance(body, dict) else None
        return {"ok": True, "action": "create", "id": rid, "dedupe_key": dedupe, "title": row.get("Title")}
    except Exception as exc:
        logger.exception("nocodb upsert failed dedupe=%s", dedupe)
        return {"ok": False, "error": str(exc)[:400], "dedupe_key": dedupe}


def list_records(
    *,
    cfg: CdeConfig | None = None,
    where: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict[str, Any]]:
    cfg = cfg or CdeConfig.from_env()
    if not cfg.nocodb_api_token:
        raise RuntimeError("missing_nocodb_token")
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if where:
        params["where"] = where
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/tables/{cfg.nocodb_table_id}/records",
        params=params,
        headers=_headers(cfg),
        timeout=45,
    )
    resp.raise_for_status()
    rows = (resp.json() or {}).get("list") or []
    return [r for r in rows if isinstance(r, dict)]


def purge_ai_rows(*, cfg: CdeConfig | None = None, dry_run: bool = True) -> dict[str, Any]:
    cfg = cfg or CdeConfig.from_env()
    rows = list_records(cfg=cfg, limit=200)
    flagged: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for row in rows:
        hit = ai_reference_hit(row)
        if hit:
            flagged.append({"id": row.get("Id"), "title": row.get("Title"), "reason": hit})
        else:
            kept.append({"id": row.get("Id"), "title": row.get("Title")})
    updated = 0
    if not dry_run:
        for item in flagged:
            rid = item.get("id")
            if rid is None:
                continue
            resp = httpx.patch(
                f"{cfg.nocodb_base_url}/api/v2/tables/{cfg.nocodb_table_id}/records",
                headers=_headers(cfg),
                json={
                    "Id": rid,
                    "relevante": "No",
                    "status": "dropped",
                    "notes": f"auto: {item['reason']}",
                    "last_touch_at": _utcnow(),
                },
                timeout=45,
            )
            resp.raise_for_status()
            updated += 1
    return {
        "ok": True,
        "dry_run": dry_run,
        "total": len(rows),
        "flagged": len(flagged),
        "kept": len(kept),
        "updated": updated,
        "flagged_rows": flagged,
        "kept_rows": kept,
    }


def sync_leads(leads: list[dict[str, Any]], *, cfg: CdeConfig | None = None) -> dict[str, Any]:
    cfg = cfg or CdeConfig.from_env()
    ok = fail = skipped = 0
    actions: list[dict[str, Any]] = []
    for lead in leads:
        if not isinstance(lead, dict):
            continue
        cleaned = clean_lead(lead)
        ai_hit = ai_reference_hit(cleaned)
        if ai_hit:
            skipped += 1
            actions.append(
                {
                    "ok": False,
                    "skipped": True,
                    "reason": ai_hit,
                    "dedupe_key": cleaned.get("dedupe_key"),
                    "title": cleaned.get("name"),
                }
            )
            continue
        result = upsert_lead(cleaned, cfg=cfg, status=cleaned.get("status") or "discovered")
        actions.append(result)
        if result.get("ok"):
            ok += 1
        else:
            fail += 1
    return {
        "ok": fail == 0,
        "upserted": ok,
        "failed": fail,
        "skipped_ai": skipped,
        "table_id": cfg.nocodb_table_id,
        "actions": actions,
    }
