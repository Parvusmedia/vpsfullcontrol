"""Normalize Unipile discover hits before NocoDB."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_PAREN_RE = re.compile(r"\([^)]*\)")
_EMOJI_RE = re.compile(r"[^\w\s.&'\-]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_PROFILE_RE = re.compile(r"linkedin\.com/in/([^/?#]+)", re.I)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [_as_text(v) for v in value if v]
        return ", ".join(p for p in parts if p)
    if isinstance(value, dict):
        return str(value.get("name") or value.get("title") or value.get("text") or "").strip()
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].replace("'", "").replace('"', "")
        return _SPACE_RE.sub(" ", inner).strip().strip(",")
    return text


def clean_person_name(value: Any) -> str:
    text = str(value or "")
    text = _PAREN_RE.sub(" ", text)
    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = _EMOJI_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def split_name(full_name: str, *, first: str = "", last: str = "") -> tuple[str, str]:
    first = clean_person_name(first)
    last = clean_person_name(last)
    if first and last:
        return first, last
    parts = [p for p in clean_person_name(full_name).split() if p]
    if not parts:
        return first, last
    if len(parts) == 1:
        return parts[0], last
    return parts[0], " ".join(parts[1:])


def clean_industry(value: Any) -> str:
    return _as_text(value)


def normalize_linkedin_url(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    match = _PROFILE_RE.search(raw)
    if match:
        slug = match.group(1).strip().strip("/")
        return f"https://www.linkedin.com/in/{slug}"
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    path = parsed.path.rstrip("/")
    if path:
        return f"https://www.linkedin.com{path}" if "linkedin.com" in (parsed.netloc or raw) else raw.rstrip("/")
    return raw


def public_id_from_url(url: str) -> str:
    match = _PROFILE_RE.search(url or "")
    return match.group(1).strip().strip("/") if match else ""


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "si", "sí"}


def clean_lead(lead: dict[str, Any]) -> dict[str, Any]:
    url = normalize_linkedin_url(str(lead.get("linkedin_url") or ""))
    public_id = str(lead.get("public_identifier") or "").strip() or public_id_from_url(url)
    first, last = split_name(
        str(lead.get("name") or ""),
        first=str(lead.get("first_name") or ""),
        last=str(lead.get("last_name") or ""),
    )
    title = _SPACE_RE.sub(" ", str(lead.get("job_title") or lead.get("headline") or "").strip())
    company = _SPACE_RE.sub(" ", str(lead.get("company_name") or "").strip())
    industry = clean_industry(lead.get("industry"))
    location = _SPACE_RE.sub(" ", str(lead.get("location") or "").strip())
    premium = as_bool(lead.get("premium"))
    open_profile = as_bool(lead.get("open_profile"))
    display = " ".join(x for x in [first, last] if x) or company or public_id
    reason_bits = [b for b in ("Premium" if premium else "", title, company, industry, location) if b]
    return {
        **lead,
        "name": display,
        "first_name": first,
        "last_name": last,
        "job_title": title,
        "sn_title": title,
        "headline": _SPACE_RE.sub(" ", str(lead.get("headline") or title).strip()),
        "company_name": company,
        "sn_company": company,
        "industry": industry,
        "location": location,
        "linkedin_url": url,
        "public_identifier": public_id,
        "dedupe_key": public_id or url,
        "premium": premium,
        "open_profile": open_profile,
        "relevante": lead.get("relevante") or "Pendiente",
        "status": lead.get("status") or "discovered",
        "source": lead.get("source") or "unipile",
        "reason_to_contact": lead.get("reason_to_contact") or " · ".join(reason_bits),
    }
