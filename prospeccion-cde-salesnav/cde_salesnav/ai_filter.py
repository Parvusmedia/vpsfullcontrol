"""Detect AI references in profile names, titles, headlines and company copy."""

from __future__ import annotations

import re
from typing import Any

from .config import AI_REFERENCE_PATTERNS

_SPACE_RE = re.compile(r"\s+")


def _norm(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").strip().lower())


def profile_text_blob(lead: dict[str, Any]) -> str:
    parts = [
        lead.get("name"),
        lead.get("first_name"),
        lead.get("last_name"),
        lead.get("job_title"),
        lead.get("sn_title"),
        lead.get("headline"),
        lead.get("company_name"),
        lead.get("sn_company"),
        lead.get("industry"),
        lead.get("reason_to_contact"),
        lead.get("notes"),
    ]
    return _norm(" ".join(str(p) for p in parts if p))


def ai_reference_hit(lead: dict[str, Any]) -> str | None:
    blob = profile_text_blob(lead)
    if not blob:
        return None
    for pattern, label in AI_REFERENCE_PATTERNS:
        if re.search(pattern, blob):
            return f"ai_reference:{label}"
    return None
