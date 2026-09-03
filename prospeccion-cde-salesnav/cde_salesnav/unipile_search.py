"""Unipile Sales Navigator people search for CDE SalesNav ICP."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

import httpx

from .config import CdeConfig
from .scoring import score_lead

def _headers(cfg: CdeConfig) -> dict[str, str]:
    return {
        "X-API-KEY": cfg.unipile_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _request(
    cfg: CdeConfig,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    url = f"{cfg.unipile_base_url}{path}"
    query = {"account_id": cfg.unipile_account_id}
    if params:
        query.update({k: v for k, v in params.items() if v is not None})
    with httpx.Client(timeout=timeout) as client:
        resp = client.request(
            method,
            url,
            params=query,
            headers=_headers(cfg),
            json=json_body,
        )
        text = resp.text or ""
        try:
            data = resp.json() if resp.content else {}
        except json.JSONDecodeError:
            data = {"raw": text[:800]}
        if resp.status_code >= 400:
            raise RuntimeError(
                f"unipile_http_{resp.status_code}: {text[:800]} url={url}?{urlencode(query)}"
            )
        return data if isinstance(data, dict) else {"items": data}


def lookup_parameter(cfg: CdeConfig, *, ptype: str, keywords: str) -> dict[str, Any] | None:
    data = _request(
        cfg,
        "GET",
        "/linkedin/search/parameters",
        params={
            "type": ptype,
            "keywords": keywords,
            "service": "SALES_NAVIGATOR",
            "limit": 10,
        },
    )
    items = data.get("items") or data.get("list") or []
    if not isinstance(items, list):
        return None
    needle = keywords.strip().lower()
    best = None
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("text") or "").strip()
        pid = str(item.get("id") or item.get("parameter_id") or "").strip()
        if not pid:
            continue
        if title.lower() == needle:
            return {"id": pid, "title": title}
        if needle in title.lower() and best is None:
            best = {"id": pid, "title": title}
    return best


def resolve_ids(cfg: CdeConfig, *, ptype: str, keywords: tuple[str, ...]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for kw in keywords:
        hit = lookup_parameter(cfg, ptype=ptype, keywords=kw)
        if hit:
            out.append(hit)
    return out


def search_body(cfg: CdeConfig, *, location_ids: list[str], industry_ids: list[str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "api": "sales_navigator",
        "category": "people",
        "profile_language": ["en"],
        "company": {"exclude": ["LinkedIn"]},
        "company_headcount": [dict(b) for b in cfg.headcount_buckets],
        "seniority": {"include": list(cfg.seniority_include)},
        "role": {"include": list(cfg.role_titles)},
    }
    if location_ids:
        body["location"] = {"include": location_ids}
    if industry_ids:
        body["industry"] = {"include": industry_ids}
    return body


def search_people(
    cfg: CdeConfig,
    *,
    body: dict[str, Any],
    limit: int = 25,
    cursor: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return _request(cfg, "POST", "/linkedin/search", params=params, json_body=body, timeout=90)


def _position(item: dict[str, Any]) -> dict[str, Any]:
    positions = item.get("current_positions") or item.get("current_position") or []
    if isinstance(positions, dict):
        return positions
    if isinstance(positions, list) and positions and isinstance(positions[0], dict):
        return positions[0]
    return {}


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    pos = _position(item)
    public_id = str(item.get("public_identifier") or "").strip()
    url = (
        str(item.get("public_profile_url") or item.get("profile_url") or "").strip()
        or (f"https://www.linkedin.com/in/{public_id}/" if public_id else "")
    )
    premium = item.get("premium")
    if isinstance(premium, str):
        premium = premium.strip().lower() in {"1", "true", "yes"}
    company = pos.get("company")
    employees = pos.get("company_headcount") or item.get("company_headcount")
    if isinstance(company, dict):
        company_name = company.get("name") or company.get("title") or ""
        employees = employees or company.get("headcount") or company.get("employee_count")
    else:
        company_name = company or pos.get("company_name") or item.get("current_company") or ""
    return {
        "name": str(item.get("name") or "").strip(),
        "first_name": str(item.get("first_name") or "").strip(),
        "last_name": str(item.get("last_name") or "").strip(),
        "job_title": str(pos.get("role") or item.get("headline") or "").strip(),
        "headline": str(item.get("headline") or "").strip(),
        "company_name": str(company_name or "").strip(),
        "company_employees": employees,
        "industry": str(item.get("industry") or pos.get("industry") or "").strip(),
        "location": str(item.get("location") or "").strip(),
        "premium": premium,
        "open_profile": bool(item.get("open_profile")),
        "linkedin_url": url,
        "public_identifier": public_id,
        "network_distance": item.get("network_distance"),
    }


def discover(
    cfg: CdeConfig,
    *,
    max_keep: int = 20,
    max_raw: int = 80,
    page_size: int = 25,
    include_industry: bool = True,
) -> dict[str, Any]:
    locations = resolve_ids(cfg, ptype="REGION", keywords=cfg.location_keywords)
    industries: list[dict[str, str]] = []
    if include_industry:
        industries = resolve_ids(cfg, ptype="SALES_INDUSTRY", keywords=cfg.industry_keywords)
    body = search_body(
        cfg,
        location_ids=[x["id"] for x in locations],
        industry_ids=[x["id"] for x in industries],
    )

    kept: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    raw_count = 0
    cursor = None
    pages = 0
    errors: list[str] = []

    while raw_count < max_raw and len(kept) < max_keep:
        pages += 1
        try:
            data = search_people(cfg, body=body, limit=min(page_size, max_raw - raw_count), cursor=cursor)
        except Exception as exc:  # noqa: BLE001 — surface Unipile errors in the report
            errors.append(str(exc)[:500])
            break
        items = [i for i in (data.get("items") or []) if isinstance(i, dict)]
        if not items:
            break
        for item in items:
            raw_count += 1
            lead = normalize_item(item)
            verdict = score_lead(lead, cfg=cfg)
            row = {**lead, **verdict}
            if verdict["ok"]:
                kept.append(row)
                if len(kept) >= max_keep:
                    break
            else:
                rejected.append(
                    {
                        "name": lead.get("name"),
                        "job_title": lead.get("job_title"),
                        "company_name": lead.get("company_name"),
                        "premium": lead.get("premium"),
                        "hard_reject": verdict.get("hard_reject"),
                    }
                )
            if raw_count >= max_raw:
                break
        cursor = data.get("cursor")
        if not cursor:
            break

    reject_counts: dict[str, int] = {}
    for row in rejected:
        key = str(row.get("hard_reject") or "other")
        reject_counts[key] = reject_counts.get(key, 0) + 1

    return {
        "account_id_suffix": cfg.unipile_account_id[-4:],
        "require_premium": cfg.require_premium,
        "locations": locations,
        "industries": industries,
        "search_body": body,
        "pages": pages,
        "raw_count": raw_count,
        "kept_count": len(kept),
        "rejected_count": len(rejected),
        "reject_counts": reject_counts,
        "errors": errors,
        "kept": kept[:max_keep],
        "rejected_sample": rejected[:15],
    }
