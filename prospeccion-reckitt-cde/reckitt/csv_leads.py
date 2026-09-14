"""Map CDE Sales Nav CSV rows to pipeline leads."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_PROFILE_RE = re.compile(r"linkedin\.com/in/([^/?#]+)", re.I)


def normalize_linkedin_url(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    raw = url.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
    except Exception:
        return None
    host = (parsed.netloc or "").lower().removeprefix("www.")
    if "linkedin.com" not in host:
        return None
    path = (parsed.path or "").rstrip("/")
    m = _PROFILE_RE.search(host + path) or _PROFILE_RE.search(raw)
    if not m:
        return None
    slug = m.group(1).strip().strip("/")
    if not slug:
        return None
    return f"https://www.linkedin.com/in/{slug}"


def profile_dedupe_key(lead: dict[str, Any] | None) -> str | None:
    if not isinstance(lead, dict):
        return None
    for key in ("linkedin_url", "linkedinUrl", "profileUrl", "url"):
        value = lead.get(key)
        if isinstance(value, str) and value.strip():
            normalized = normalize_linkedin_url(value)
            if normalized:
                m = _PROFILE_RE.search(normalized)
                if m:
                    return m.group(1).lower()
    email = (lead.get("email") or lead.get("work_email") or "").strip().lower()
    if email and "@" in email:
        return f"email:{email}"
    first = (lead.get("first_name") or "").strip().lower()
    last = (lead.get("last_name") or "").strip().lower()
    company = (lead.get("company_name") or "").strip().lower()
    if first and last:
        return f"name:{first}:{last}:{company}"
    return None


def _clean(value: Any) -> str:
    return str(value or "").strip()


def row_to_lead(row: dict[str, Any], *, relevante: str = "Sí") -> dict[str, Any]:
    first = _clean(row.get("first_name"))
    last = _clean(row.get("last_name"))
    full = _clean(row.get("full_name")) or " ".join(x for x in (first, last) if x)
    email = _clean(row.get("work_email") or row.get("email")).lower()
    linkedin = normalize_linkedin_url(_clean(row.get("linkedin_url"))) or _clean(row.get("linkedin_url"))
    domain = _clean(row.get("company_domain")).lower().removeprefix("www.")
    lead = {
        "Title": full or _clean(row.get("company_name")) or "lead",
        "first_name": first,
        "last_name": last,
        "full_name": full,
        "job_title": _clean(row.get("job_title")),
        "company_name": _clean(row.get("company_name")),
        "location": _clean(row.get("location")),
        "linkedin_url": linkedin,
        "company_domain": domain,
        "company_website": domain,
        "company_linkedin_url": _clean(row.get("company_linkedin_url")),
        "profile_summary": _clean(row.get("profile_summary")),
        "email": email,
        "email_status": _clean(row.get("email_status")),
        "email_confidence": _clean(row.get("email_confidence")),
        "email_source": _clean(row.get("email_source")),
        "sales_nav_id": _clean(row.get("sales_nav_id")),
        "relevante": relevante,
        "status": "imported",
        "smartlead_status": "",
        "unipile_status": "",
        "campaign": "reckitt_cde_dfm_en",
        "reason_to_contact": (
            "Reckitt media / marketing contact — Parvus Media Data for Media: "
            "7-day regional planning from weather + Google Trends (Reckitt Spain case)."
        ),
        "source_task": _clean(row.get("source_task")),
        "mensaje_estado": "",
        "connection_message": "",
        "followup_message": "",
        "notes": "",
    }
    lead["dedupe_key"] = profile_dedupe_key(lead) or full.lower() or email
    if email:
        lead["status"] = "imported_email"
    elif _clean(row.get("email_status")).lower() == "not_found":
        lead["status"] = "icypeas_miss"
        lead["email_source"] = lead.get("email_source") or "icypeas"
    return lead


def load_csv(path: str | Path, *, relevante: str = "Sí") -> list[dict[str, Any]]:
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    leads: list[dict[str, Any]] = []
    seen: set[str] = set()
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            if not isinstance(raw, dict):
                continue
            lead = row_to_lead(raw, relevante=relevante)
            key = lead.get("dedupe_key") or ""
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            leads.append(lead)
    return leads


def summarize_leads(leads: list[dict[str, Any]]) -> dict[str, Any]:
    with_email = [x for x in leads if (x.get("email") or "").strip() and "@" in (x.get("email") or "")]
    with_li = [x for x in leads if (x.get("linkedin_url") or "").strip()]
    no_email = [x for x in leads if x not in with_email]
    return {
        "total": len(leads),
        "with_email": len(with_email),
        "without_email": len(no_email),
        "with_linkedin": len(with_li),
        "email_sources": sorted({(x.get("email_source") or "") for x in with_email if x.get("email_source")}),
        "email_domains": sorted(
            {
                (x.get("email") or "").split("@", 1)[1]
                for x in with_email
                if "@" in (x.get("email") or "")
            }
        ),
    }
