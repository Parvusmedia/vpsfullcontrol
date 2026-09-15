"""Icypeas email enrichment for prospección consultoras."""

from __future__ import annotations

import asyncio
from typing import Any

_ICYPEAS_SEARCH = "https://app.icypeas.com/api/email-search"
_ICYPEAS_READ = "https://app.icypeas.com/api/bulk-single-searchs/read"

TIER_DOMAINS: dict[str, str] = {
    "deloitte": "deloitte.com",
    "deloitte_digital": "deloitte.com",
    "accenture": "accenture.com",
    "pwc": "pwc.com",
    "everis": "everis.com",
    "ntt_data": "nttdata.com",
    "kpmg": "kpmg.com",
    "kpmg_spain": "kpmg.es",
    "making_science": "makingscience.com",
    "idom": "idom.com",
}

COMPANY_NAME_DOMAINS: tuple[tuple[str, str], ...] = (
    ("deloitte", "deloitte.com"),
    ("accenture", "accenture.com"),
    ("pwc", "pwc.com"),
    ("pricewaterhouse", "pwc.com"),
    ("kpmg", "kpmg.com"),
    ("everis", "everis.com"),
    ("ntt data", "nttdata.com"),
    ("making science", "makingscience.com"),
    ("idom", "idom.com"),
    ("bain", "bain.com"),
)


def domain_for_lead(lead: dict[str, Any]) -> str:
    tier = str(lead.get("company_tier") or "").strip().lower()
    if tier and tier in TIER_DOMAINS:
        return TIER_DOMAINS[tier]
    blob = str(lead.get("company") or "").strip().lower()
    for marker, domain in COMPANY_NAME_DOMAINS:
        if marker in blob:
            return domain
    return blob


async def icypeas_email_search(
    *,
    api_key: str,
    first_name: str,
    last_name: str,
    domain_or_company: str,
    poll_attempts: int = 8,
    poll_seconds: float = 6.0,
) -> dict[str, Any]:
    key = (api_key or "").strip()
    if not key:
        return {"email": None, "certainty": None, "status": "skipped_no_api_key", "search_id": None}
    if not ((first_name or last_name) and domain_or_company):
        return {"email": None, "certainty": None, "status": "skipped_missing_fields", "search_id": None}

    import httpx

    headers = {"Authorization": key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=45) as client:
        start = await client.post(
            _ICYPEAS_SEARCH,
            headers=headers,
            json={
                "firstname": first_name,
                "lastname": last_name,
                "domainOrCompany": domain_or_company,
            },
        )
        start.raise_for_status()
        start_data = start.json() if start.content else {}
        search_id = (
            ((start_data.get("item") or {}) if isinstance(start_data, dict) else {}).get("_id")
            if isinstance(start_data, dict)
            else None
        )
        if not search_id:
            return {
                "email": None,
                "certainty": None,
                "status": "start_failed",
                "search_id": None,
            }

        best: dict[str, Any] = {}
        status = "PENDING"
        for _ in range(max(1, poll_attempts)):
            await asyncio.sleep(poll_seconds)
            read = await client.post(_ICYPEAS_READ, headers=headers, json={"id": search_id})
            read.raise_for_status()
            read_data = read.json() if read.content else {}
            items = read_data.get("items") if isinstance(read_data, dict) else None
            result_item = (items[0] if isinstance(items, list) and items else None) or (
                read_data.get("item") if isinstance(read_data, dict) else {}
            )
            if not isinstance(result_item, dict):
                result_item = {}
            status = str(result_item.get("status") or "").upper() or status
            emails = (
                ((result_item.get("results") or {}) if isinstance(result_item.get("results"), dict) else {}).get(
                    "emails"
                )
                or result_item.get("emails")
                or []
            )
            if not isinstance(emails, list):
                emails = []
            normalized: list[dict[str, Any]] = []
            for e in emails:
                if isinstance(e, dict):
                    normalized.append(e)
                elif isinstance(e, str) and "@" in e:
                    normalized.append({"email": e})
            rank = {"ultra_sure": 5, "sure": 4, "catch_all": 3, "risky": 2, "unknown": 1}
            sorted_emails = sorted(
                normalized,
                key=lambda e: rank.get(str(e.get("certainty") or "").lower(), 0),
                reverse=True,
            )
            if sorted_emails:
                best = sorted_emails[0]
            if status in {
                "FOUND",
                "NOT_FOUND",
                "FAILED",
                "ERROR",
                "DONE",
                "COMPLETED",
                "DEBITED",
            } or best.get("email"):
                break

        email = str(best.get("email") or best.get("value") or "").strip() or None
        return {
            "email": email.lower() if email else None,
            "certainty": str(best.get("certainty") or "").strip() or None,
            "status": (status or "unknown").lower(),
            "search_id": search_id,
        }
