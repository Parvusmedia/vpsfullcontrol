"""Hard ICP filters for CDE SalesNav leads."""

from __future__ import annotations

import re
from typing import Any

from .config import EXCLUDED_COMPANIES, EXCLUDED_TITLE_PATTERNS, CdeConfig

_HEADCOUNT_RE = re.compile(r"(\d[\d,]*)\s*[-–]?\s*(\d[\d,]*)?")


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def parse_employees(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).replace(",", "")
    if text.isdigit():
        return int(text)
    match = _HEADCOUNT_RE.search(text)
    if not match:
        return None
    low = int(match.group(1).replace(",", ""))
    high = match.group(2)
    if high:
        return int(high.replace(",", ""))
    return low


def is_linkedin_company(company: str) -> bool:
    blob = _norm(company)
    if not blob:
        return False
    return any(marker == blob or blob.startswith(f"{marker} ") for marker in EXCLUDED_COMPANIES)


def title_excluded(title: str) -> str | None:
    blob = _norm(title)
    for pattern, label in EXCLUDED_TITLE_PATTERNS:
        if re.search(pattern, blob):
            return f"title:{label}"
    return None


def score_lead(lead: dict[str, Any], *, cfg: CdeConfig | None = None) -> dict[str, Any]:
    cfg = cfg or CdeConfig.from_env()
    title = str(lead.get("job_title") or lead.get("headline") or "")
    company = str(lead.get("company_name") or "")
    employees = parse_employees(lead.get("company_employees") or lead.get("company_headcount"))
    premium = lead.get("premium")
    if isinstance(premium, str):
        premium = premium.strip().lower() in {"1", "true", "yes"}

    reasons: list[str] = []
    hard_reject = None

    if is_linkedin_company(company) or ("linkedin" in _norm(title) and "microsoft" in _norm(company)):
        hard_reject = "excluded_company:linkedin"
    title_hit = title_excluded(title)
    if title_hit:
        hard_reject = hard_reject or title_hit
    if cfg.require_premium and premium is not True:
        hard_reject = hard_reject or "not_premium"
    if employees is not None and employees < cfg.min_employees:
        hard_reject = hard_reject or f"company_too_small:{employees}"

    if premium is True:
        reasons.append("premium")
    if employees:
        reasons.append(f"size:{employees}")
    if company:
        reasons.append(f"company:{company}")

    return {
        "ok": hard_reject is None,
        "hard_reject": hard_reject,
        "reasons": reasons,
        "premium": premium,
        "company_employees": employees,
    }
