"""Icypeas email enrichment (Reckitt / reckitt.com)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ICYPEAS_SEARCH = "https://app.icypeas.com/api/email-search"
_ICYPEAS_READ = "https://app.icypeas.com/api/bulk-single-searchs/read"

_COMPANY_DOMAINS: tuple[tuple[str, str], ...] = (
    ("reckitt", "reckitt.com"),
    ("reckitt benckiser", "reckitt.com"),
    ("rb hygiene", "reckitt.com"),
)

DEFAULT_DOMAIN = "reckitt.com"


def domain_from_url(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = urlparse(raw).hostname or ""
    except Exception:
        return ""
    return host.lower().removeprefix("www.")


def domain_for_company(company_name: str | None, website: str | None = None) -> str:
    from_web = domain_from_url(website)
    if from_web:
        return from_web
    blob = (website or "").strip().lower().removeprefix("www.")
    if blob and "." in blob and " " not in blob:
        return blob
    name = (company_name or "").strip().lower()
    for marker, domain in _COMPANY_DOMAINS:
        if marker in name:
            return domain
    return DEFAULT_DOMAIN


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
                "raw": start_data,
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
            for item in emails:
                if isinstance(item, dict):
                    normalized.append(item)
                elif isinstance(item, str) and "@" in item:
                    normalized.append({"email": item})
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
