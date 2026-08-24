#!/usr/bin/env python3
"""Prospección consultoras: Harvest (filtros estrictos) → scoring → NocoDB."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parent
TABLE_ID = os.environ.get("NOCODB_CONSULTORAS_TABLE_ID", "mj23ak5ilm76662")
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NOCODB_COLUMNS: list[tuple[str, str]] = [
    ("first_name", "SingleLineText"),
    ("last_name", "SingleLineText"),
    ("linkedin_url", "URL"),
    ("company", "SingleLineText"),
    ("company_tier", "SingleLineText"),
    ("country", "SingleLineText"),
    ("city", "SingleLineText"),
    ("job_title", "SingleLineText"),
    ("practice", "SingleLineText"),
    ("seniority", "SingleLineText"),
    ("contact_type", "SingleLineText"),
    ("relevant_keywords", "LongText"),
    ("reason_for_fit", "LongText"),
    ("score", "Number"),
    ("connection_message", "LongText"),
    ("followup_message", "LongText"),
    ("status", "SingleLineText"),
    ("source_query", "SingleLineText"),
    ("headline", "LongText"),
    ("location", "SingleLineText"),
    ("dedupe_key", "SingleLineText"),
]

HARD_EXCLUDE = (
    "recruiter",
    "talent acquisition",
    "human resources",
    " hr ",
    "campus hire",
    "graduate program",
    "audit",
    "assurance",
    " tax ",
    "legal counsel",
    "cyber",
    "cybersecurity",
    "information security",
    "ciso",
    "data engineer",
    "data engineering",
    "data architect",
    "data governance",
    "data management",
    "machine learning engineer",
    "mlops",
    " sap ",
    "infrastructure engineer",
    "cloud infrastructure",
    "network engineer",
    "devops",
    "analyst",
    "associate consultant",
    "intern",
    "apprentice",
    "executive assistant",
    "office manager",
    "procurement",
    "sales director",
    "strategic sales",
)

POSITIVE_KEYWORDS = (
    "marketing, commerce & product",
    "marketing commerce product",
    "deloitte digital",
    "accenture song",
    "customer experience",
    "customer",
    "digital transformation",
    "digital marketing",
    "marketing transformation",
    "martech",
    "adtech",
    "marketing technology",
    "personalization",
    "customer engagement",
    "crm",
    "commerce",
    "digital experience",
    "generative ai",
    "agentic ai",
    " automation",
    "intelligent automation",
    "innovation",
    "emerging technology",
    "data-driven marketing",
    "customer analytics",
)

COMPANY_URLS = {
    "deloitte": "https://www.linkedin.com/company/1038",
    "deloitte_digital": "https://www.linkedin.com/company/2449847",
    "accenture": "https://www.linkedin.com/company/1033",
    "everis": "https://www.linkedin.com/company/8339",
    "ntt_data": "https://www.linkedin.com/company/19141006",
}

SENIORITY_IDS = "200,210,220,300,310,320"

SEEDS: list[dict[str, Any]] = [
    {
        "first_name": "Shakeel",
        "last_name": "Sawar",
        "linkedin_url": "https://www.linkedin.com/in/shakeel-a-sawar-8517024",
        "company": "Deloitte",
        "company_tier": "deloitte",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "job_title": "Partner | Marketing, Commerce & Product Leader",
        "practice": "Marketing, Commerce & Product",
        "seniority": "Partner",
        "contact_type": "practice_leader",
        "relevant_keywords": ["Marketing Commerce Product", "Customer Experience", "Deloitte Digital"],
        "score": 5,
        "source_query": "seed:priority_1",
        "headline": "Marketing & Commerce lead | Middle East",
        "location": "United Arab Emirates",
    },
    {
        "first_name": "AbdulMouhsen",
        "last_name": "Al-Madani",
        "linkedin_url": "https://www.linkedin.com/in/ACwAAADlVv0Bmk_mLHoMlaBAThUk81PDsH0Q8Jk",
        "company": "Deloitte",
        "company_tier": "deloitte",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "job_title": "Director | Marketing, Commerce & Product",
        "practice": "Marketing, Commerce & Product",
        "seniority": "Director",
        "contact_type": "practice_leader",
        "relevant_keywords": ["Marketing Commerce Product", "Customer Experience", "Riyadh"],
        "score": 5,
        "source_query": "seed:priority_2",
        "headline": "Director Marketing Commerce Product — Riyadh",
        "location": "Riyadh, Saudi Arabia",
    },
    {
        "first_name": "Dany",
        "last_name": "Hajjar",
        "linkedin_url": "https://www.linkedin.com/in/danyhajjar",
        "company": "Deloitte",
        "company_tier": "deloitte",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "job_title": "Partner | Customer Leader",
        "practice": "Customer / Digital Foundry",
        "seniority": "Partner",
        "contact_type": "practice_leader",
        "relevant_keywords": ["Customer", "Deloitte Digital", "Digital Transformation"],
        "score": 5,
        "source_query": "seed:priority_3",
        "headline": "Customer & Marketing portfolio leader for the Middle East",
        "location": "United Arab Emirates",
    },
    {
        "first_name": "Saudamini",
        "last_name": "Dubey",
        "linkedin_url": "https://www.linkedin.com/in/ACwAAAA76c0BnMv5QxQsHam_SXHNSRHqFz4INfU",
        "company": "Deloitte",
        "company_tier": "deloitte",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "job_title": "Partner | Marketing, Commerce & Product / Digital Transformation & Innovation",
        "practice": "Digital Transformation & Innovation",
        "seniority": "Partner",
        "contact_type": "practice_leader",
        "relevant_keywords": ["Digital Transformation", "Innovation", "Marketing Commerce Product"],
        "score": 5,
        "source_query": "seed:priority_4",
        "headline": "Digital Transformation & Innovation Lead Partner",
        "location": "Middle East",
    },
    {
        "first_name": "Rashid",
        "last_name": "Bashir",
        "linkedin_url": "https://www.linkedin.com/in/rashid-bashir-96579227",
        "company": "Deloitte",
        "company_tier": "deloitte",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "job_title": "CEO Consulting / Technology & Transformation Leader",
        "practice": "Technology & Transformation",
        "seniority": "Partner",
        "contact_type": "practice_leader",
        "relevant_keywords": ["Technology Transformation", "Digital Transformation"],
        "score": 3,
        "source_query": "seed:priority_5",
        "headline": "Chief Executive Officer - Deloitte Middle East Consulting",
        "location": "United Arab Emirates",
    },
]


@dataclass(frozen=True)
class HarvestQuery:
    label: str
    location: str
    current_companies: str
    current_job_titles: str
    search: str | None = None


def load_env() -> None:
    for path in (Path("/etc/linkedinreport/app.env"), ROOT / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def nocodb_creds() -> tuple[str, str]:
    base = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com").rstrip("/")
    token = os.environ.get("NOCODB_API_TOKEN", "")
    if not token:
        raise RuntimeError("NOCODB_API_TOKEN missing")
    return base, token


def harvest_creds() -> tuple[str, str]:
    con = sqlite3.connect("/opt/apps/linkedinreport/linkedinreport.db")
    row = con.execute(
        "SELECT value FROM app_settings WHERE key IN ('harvest_api_key','HARVEST_API_KEY') LIMIT 1"
    ).fetchone()
    base_row = con.execute("SELECT value FROM app_settings WHERE key='harvest_base_url'").fetchone()
    con.close()
    api_key = (row[0] if row else "") or ""
    base = ((base_row[0] if base_row else "") or "https://api.harvest-api.com").rstrip("/")
    if not api_key:
        raise RuntimeError("HARVEST_API_KEY missing")
    return api_key, base


def _norm(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def normalize_linkedin_url(url: str | None) -> str | None:
    if not url:
        return None
    raw = url.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    p = urlparse(raw)
    path = (p.path or "").rstrip("/")
    if not path or path == "/":
        return None
    return f"https://www.linkedin.com{path}"


def dedupe_key(url: str | None) -> str:
    u = normalize_linkedin_url(url) or ""
    m = re.search(r"linkedin\.com/in/([^/?#]+)", u, re.I)
    return (m.group(1) if m else u).lower()


def build_queries() -> list[HarvestQuery]:
    partner_titles = (
        "Partner Marketing,Partner Customer,Partner Digital,Partner Digital Transformation,"
        "Partner MarTech,Partner Innovation,Managing Director Marketing,Managing Director Customer"
    )
    director_titles = (
        "Director Marketing Commerce,Director Customer Experience,Director Digital Transformation,"
        "Director MarTech,Director Marketing Technology,Director Innovation,Director Digital"
    )
    sm_titles = (
        "Senior Manager Marketing,Senior Manager Customer,Senior Manager Digital,"
        "Senior Manager MarTech,Senior Manager Innovation"
    )
    return [
        HarvestQuery("deloitte_ksa_partner_mcp", "Saudi Arabia", COMPANY_URLS["deloitte"], partner_titles),
        HarvestQuery("deloitte_uae_partner_mcp", "United Arab Emirates", COMPANY_URLS["deloitte"], partner_titles),
        HarvestQuery("deloitte_digital_gcc_sm", "Saudi Arabia", COMPANY_URLS["deloitte_digital"], sm_titles),
        HarvestQuery("deloitte_digital_uae_sm", "United Arab Emirates", COMPANY_URLS["deloitte_digital"], sm_titles),
        HarvestQuery("accenture_uae_song", "United Arab Emirates", COMPANY_URLS["accenture"], director_titles, "Accenture Song"),
        HarvestQuery("accenture_uk_song", "United Kingdom", COMPANY_URLS["accenture"], director_titles, "Accenture Song"),
        HarvestQuery("accenture_us_song", "United States", COMPANY_URLS["accenture"], director_titles, "Accenture Song"),
        HarvestQuery("everis_spain_director", "Spain", COMPANY_URLS["everis"], director_titles),
        HarvestQuery("ntt_spain_director", "Spain", COMPANY_URLS["ntt_data"], director_titles),
        HarvestQuery("deloitte_spain_digital", "Spain", COMPANY_URLS["deloitte_digital"], director_titles),
        HarvestQuery("deloitte_uk_digital", "United Kingdom", COMPANY_URLS["deloitte_digital"], director_titles),
    ]


def hard_exclude_reason(lead: dict[str, Any]) -> str | None:
    blob = _norm(" ".join([
        str(lead.get("job_title") or ""),
        str(lead.get("headline") or ""),
        str(lead.get("title") or ""),
    ]))
    if not blob.strip():
        return "empty_title"
    for marker in HARD_EXCLUDE:
        if marker in blob:
            return f"exclude:{marker.strip()}"
    if re.search(r"\bconsultant\b", blob) and not re.search(
        r"\b(partner|director|senior manager|managing director|practice lead)\b", blob
    ):
        return "exclude:junior_consultant"
    if re.fullmatch(r"manager", blob) or blob == "manager":
        return "exclude:generic_manager"
    if blob == "director" and not any(k in blob for k in ("marketing", "customer", "digital", "martech", "commerce", "innovation", "experience")):
        return "exclude:generic_director"
    return None


def detect_practice(blob: str) -> str:
    b = _norm(blob)
    if "marketing" in b and ("commerce" in b or "product" in b):
        return "Marketing, Commerce & Product"
    if "customer" in b:
        return "Customer"
    if "deloitte digital" in b or "accenture song" in b:
        return "Digital"
    if "martech" in b or "marketing technology" in b:
        return "MarTech"
    if "digital transformation" in b:
        return "Digital Transformation"
    if "innovation" in b:
        return "Innovation"
    if "technology" in b and "transformation" in b:
        return "Technology & Transformation"
    return "Digital"


def detect_seniority(title: str) -> str:
    t = _norm(title)
    if "managing partner" in t or re.search(r"\bpartner\b", t):
        return "Partner"
    if "managing director" in t:
        return "Managing Director"
    if "director" in t:
        return "Director"
    if "senior manager" in t:
        return "Senior Manager"
    return "Other"


def score_lead(lead: dict[str, Any]) -> tuple[int, str, list[str]]:
    if hard_exclude_reason(lead):
        return 1, "Excluded by hard filter", []

    title = str(lead.get("job_title") or lead.get("title") or "")
    headline = str(lead.get("headline") or "")
    blob = f"{title} {headline}"
    practice = detect_practice(blob)
    seniority = detect_seniority(title)
    country = str(lead.get("country") or lead.get("_query_geo") or lead.get("location") or "")
    keywords = [k.strip() for k in POSITIVE_KEYWORDS if k in _norm(blob)]

    score = 2.0
    if seniority == "Partner":
        score += 2
    elif seniority in {"Director", "Managing Director"}:
        score += 1.5
    elif seniority == "Senior Manager":
        score += 1

    if practice in {"Marketing, Commerce & Product", "Customer", "Digital", "MarTech", "Innovation"}:
        score += 1
    if any(g in _norm(country) for g in ("saudi", "united arab emirates", "uae", "riyadh", "dubai")):
        score += 0.5
    if any(g in _norm(country) for g in ("spain", "united kingdom", "united states")):
        score += 0.25
    score += min(1.0, 0.25 * len(keywords))

    if practice == "Technology & Transformation" and seniority == "Partner" and "customer" not in _norm(blob):
        score = min(score, 3)

    final = max(1, min(5, int(round(score))))
    reason = (
        f"{seniority} in {practice} at {lead.get('company_name') or lead.get('company') or 'target firm'} "
        f"— relevant for customer/MarTech/automation workstreams in {country or lead.get('location') or 'region'}."
    )
    return final, reason, keywords[:5]


def relevant_area(lead: dict[str, Any]) -> str:
    practice = lead.get("practice") or detect_practice(
        f"{lead.get('job_title','')} {lead.get('headline','')}"
    )
    mapping = {
        "Marketing, Commerce & Product": "marketing, commerce & customer experience",
        "Customer": "customer strategy & digital customer",
        "Digital": "digital transformation & customer experience",
        "MarTech": "MarTech and marketing transformation",
        "Digital Transformation": "digital transformation",
        "Innovation": "digital innovation",
        "Technology & Transformation": "technology transformation",
    }
    return mapping.get(str(practice), "digital transformation & customer experience")


def build_messages(lead: dict[str, Any]) -> tuple[str, str]:
    first = lead.get("first_name") or "there"
    area = relevant_area(lead)
    seniority = lead.get("seniority") or detect_seniority(str(lead.get("job_title") or ""))
    country = str(lead.get("country") or "")
    score = int(lead.get("score") or 0)
    company = str(lead.get("company") or "Deloitte")

    if "Everis" in company or "NTT" in company:
        connection = (
            f"Hi {first},\n\n"
            f"He seguido el trabajo de {company} en {area} y veo mucho encaje con mi experiencia en publicidad digital, "
            f"MarTech, automatización y soluciones de customer con IA aplicada.\n\n"
            f"Me encantaría conectar.\n\nEmiliano"
        )
    elif "Spain" in country or "España" in country:
        connection = (
            f"Hi {first},\n\n"
            f"He seguido el trabajo de {company} en {area} en España y veo mucho encaje con mi experiencia "
            f"en publicidad digital, MarTech, automatización y soluciones de customer con IA aplicada.\n\n"
            f"Me encantaría conectar.\n\nEmiliano"
        )
    elif seniority == "Partner" or "Partner" in str(lead.get("job_title") or ""):
        connection = (
            f"Hi {first},\n\n"
            f"I've been looking at {company}'s work around {area} in the Middle East and see a strong overlap "
            f"with my background across AdTech/MarTech, customer acquisition, automation and AI-driven digital solutions.\n\n"
            f"Would be great to connect.\n\nEmiliano"
        )
    elif "Riyadh" in country or "Saudi" in country:
        connection = (
            f"Hi {first},\n\n"
            f"I came across your work within {company}'s {area} practice in Riyadh.\n\n"
            f"My background combines digital advertising, MarTech, automation and hands-on development of data/AI-driven customer solutions.\n\n"
            f"I'd be glad to connect.\n\nEmiliano"
        )
    elif "United Kingdom" in country:
        connection = (
            f"Hi {first},\n\n"
            f"I've been following {company}'s work around {area} in the UK and see a strong overlap with my background "
            f"in digital advertising technology, MarTech, automation and AI-driven customer solutions.\n\n"
            f"I'd be glad to connect.\n\nEmiliano"
        )
    elif "United States" in country:
        connection = (
            f"Hi {first},\n\n"
            f"I specialize in the intersection of customer, marketing and applied MarTech/AI — with hands-on delivery experience. "
            f"I'd welcome connecting to explore how senior profiles like mine typically engage with {company}'s {area} practice.\n\n"
            f"Emiliano"
        )
    else:
        connection = (
            f"Hi {first},\n\n"
            f"I've been following {company}'s work around {area} in the GCC and see a strong overlap with my background "
            f"in digital advertising technology, MarTech, automation and AI-driven customer solutions.\n\n"
            f"I'd be glad to connect.\n\nEmiliano"
        )

    followup = (
        f"Hi {first},\n\n"
        f"Thanks for connecting.\n\n"
        f"I'm currently exploring how my background could fit into GCC transformation projects, particularly around "
        f"customer experience, MarTech/AdTech, automation, AI and rapid digital product development.\n\n"
        f"I've spent most of my career combining client/business responsibilities with hands-on technology and product development.\n\n"
        f"I'm particularly interested in opportunities where {company} teams need an experienced specialist for a specific "
        f"client workstream, either directly within the team or as an external SME.\n\n"
        f"Happy to share a little more context if relevant.\n\nEmiliano"
    )

    if score >= 5 and "adobe" in _norm(str(lead.get("headline") or "")):
        followup = (
            f"Hi {first},\n\n"
            f"Thanks for connecting.\n\n"
            f"I was particularly interested in the work {company} is doing around customer experience orchestration, "
            f"combining CRM, MarTech, personalization and AI-enabled customer experiences.\n\n"
            f"That's very close to the type of work I've been developing across digital advertising, automation, "
            f"data-driven experiences and AI.\n\n"
            f"I'd be interested in exploring whether profiles like mine are ever brought into specific GCC client "
            f"workstreams as SMEs or specialist delivery support.\n\nEmiliano"
        )

    return connection, followup


def lead_from_harvest(item: dict[str, Any], query: HarvestQuery) -> dict[str, Any]:
    first = (item.get("firstName") or item.get("first_name") or "").strip()
    last = (item.get("lastName") or item.get("last_name") or "").strip()
    if not first and isinstance(item.get("name"), str) and " " in item["name"]:
        first, last = item["name"].split(" ", 1)[0], item["name"].split(" ", 1)[1]

    pos: dict[str, Any] = {}
    for list_key in ("currentPositions", "currentPosition", "experience"):
        rows = item.get(list_key)
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            pos = rows[0]
            break
        if isinstance(rows, dict):
            pos = rows
            break

    title = (
        item.get("title")
        or item.get("headline")
        or item.get("jobTitle")
        or item.get("occupation")
        or pos.get("title")
        or pos.get("position")
        or ""
    )
    title = str(title).strip()
    headline = str(item.get("headline") or "").strip()
    company = str(item.get("companyName") or item.get("company") or pos.get("companyName") or pos.get("company") or "").strip()

    location = item.get("location") or item.get("geo") or item.get("locationName") or query.location or ""
    if isinstance(location, dict):
        location = location.get("full") or location.get("country") or query.location or ""
    location = str(location).strip()

    url = normalize_linkedin_url(
        item.get("linkedinUrl") or item.get("linkedin_url") or item.get("profileUrl") or item.get("url")
    )
    tier = "other"
    cl = _norm(company)
    if "deloitte" in cl:
        tier = "deloitte"
    elif "accenture" in cl:
        tier = "accenture"
    elif "everis" in cl or "ntt" in cl:
        tier = "everis"

    lead: dict[str, Any] = {
        "first_name": first,
        "last_name": last,
        "linkedin_url": url or "",
        "company": company or query.label.split("_")[0].title(),
        "company_tier": tier,
        "country": query.location,
        "city": "",
        "job_title": title,
        "headline": headline,
        "location": location,
        "source_query": query.label,
        "dedupe_key": dedupe_key(url),
        "contact_type": "practice_leader",
        "status": "new",
    }
    s, reason, kws = score_lead(lead)
    lead["score"] = s
    lead["reason_for_fit"] = reason
    lead["relevant_keywords"] = kws
    lead["practice"] = detect_practice(f"{title} {headline}")
    lead["seniority"] = detect_seniority(title)
    if s >= 4:
        cm, fm = build_messages(lead)
        lead["connection_message"] = cm
        lead["followup_message"] = fm
        lead["status"] = "reviewed"
    elif s == 3:
        lead["status"] = "reviewed"
    else:
        lead["status"] = "not_relevant"
    return lead


def row_for_nocodb(lead: dict[str, Any]) -> dict[str, Any]:
    title = " ".join(x for x in [lead.get("first_name"), lead.get("last_name")] if x).strip()
    kws = lead.get("relevant_keywords") or []
    if isinstance(kws, list):
        kws = ", ".join(kws)
    return {
        "title": title or lead.get("dedupe_key") or "contact",
        "first_name": lead.get("first_name") or "",
        "last_name": lead.get("last_name") or "",
        "linkedin_url": lead.get("linkedin_url") or "",
        "company": lead.get("company") or "",
        "company_tier": lead.get("company_tier") or "",
        "country": lead.get("country") or "",
        "city": lead.get("city") or "",
        "job_title": lead.get("job_title") or "",
        "practice": lead.get("practice") or "",
        "seniority": lead.get("seniority") or "",
        "contact_type": lead.get("contact_type") or "practice_leader",
        "relevant_keywords": kws,
        "reason_for_fit": lead.get("reason_for_fit") or "",
        "score": lead.get("score"),
        "connection_message": lead.get("connection_message") or "",
        "followup_message": lead.get("followup_message") or "",
        "status": lead.get("status") or "new",
        "source_query": lead.get("source_query") or "",
        "headline": lead.get("headline") or "",
        "location": lead.get("location") or "",
        "dedupe_key": lead.get("dedupe_key") or "",
    }


def provision_columns() -> None:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=30) as client:
        for name, uidt in NOCODB_COLUMNS:
            payload = {"column_name": name, "title": name, "uidt": uidt}
            r = client.post(f"{base}/api/v2/meta/tables/{TABLE_ID}/columns", headers=headers, json=payload)
            if r.status_code == 200:
                print(f"column OK {name}")
            elif r.status_code == 422 and "duplicate" in r.text.lower():
                print(f"column SKIP {name}")
            else:
                print(f"column FAIL {name}: {r.status_code} {r.text[:120]}")


def find_by_dedupe(base: str, token: str, key: str) -> dict[str, Any] | None:
    if not key:
        return None
    headers = {"xc-token": token, "Accept": "application/json"}
    where = f"(dedupe_key,eq,{key})"
    with httpx.Client(timeout=30) as client:
        r = client.get(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            params={"where": where, "limit": 1},
        )
        r.raise_for_status()
        rows = r.json().get("list") or []
        return rows[0] if rows else None


def upsert_lead(lead: dict[str, Any]) -> dict[str, Any]:
    base, token = nocodb_creds()
    row = row_for_nocodb(lead)
    key = row.get("dedupe_key") or ""
    headers = {"xc-token": token, "Content-Type": "application/json", "Accept": "application/json"}
    existing = find_by_dedupe(base, token, key)
    with httpx.Client(timeout=45) as client:
        if existing and existing.get("Id") is not None:
            rid = existing["Id"]
            r = client.patch(
                f"{base}/api/v2/tables/{TABLE_ID}/records",
                headers=headers,
                json={"Id": rid, **row},
            )
            r.raise_for_status()
            return {"action": "update", "id": rid, "dedupe_key": key}
        r = client.post(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            json=row,
        )
        r.raise_for_status()
        body = r.json() if r.content else {}
        return {"action": "create", "id": body.get("Id"), "dedupe_key": key}


async def harvest_search(query: HarvestQuery, *, max_items: int = 10) -> list[dict[str, Any]]:
    api_key, base = harvest_creds()
    headers = {"X-API-Key": api_key}
    params: dict[str, Any] = {
        "page": 1,
        "currentCompanies": query.current_companies,
        "currentJobTitles": query.current_job_titles,
        "locations": query.location,
        "seniorityLevelIds": SENIORITY_IDS,
    }
    if query.search:
        params["search"] = query.search
    rows: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=60) as client:
        for page in range(1, 3):
            params["page"] = page
            resp = await client.get(f"{base}/linkedin/lead-search", params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("elements") or data.get("items") or []
            if not elements and isinstance(data.get("element"), dict):
                elements = [data["element"]]
            batch = [e for e in elements if isinstance(e, dict)]
            rows.extend(batch)
            if len(rows) >= max_items or not batch:
                break
    return rows[:max_items]


def prepare_seed(seed: dict[str, Any]) -> dict[str, Any]:
    lead = dict(seed)
    lead["dedupe_key"] = dedupe_key(lead.get("linkedin_url"))
    lead["reason_for_fit"] = (
        f"Priority seed — {lead.get('seniority')} in {lead.get('practice')} "
        f"({lead.get('country')}). Direct decision-maker for staffing and specialist hires."
    )
    if lead.get("score", 0) >= 4:
        cm, fm = build_messages(lead)
        lead["connection_message"] = cm
        lead["followup_message"] = fm
    lead["status"] = "reviewed"
    return lead


async def cmd_discover(args: argparse.Namespace) -> int:
    queries = build_queries()
    if args.query:
        queries = [q for q in queries if q.label == args.query]
    leads: list[dict[str, Any]] = []
    seen: set[str] = set()
    for q in queries[: args.max_queries]:
        print(f"HARVEST {q.label} …")
        try:
            raw = await harvest_search(q, max_items=args.max_per_query)
        except Exception as exc:
            print(f"  FAIL {exc}")
            continue
        accepted = 0
        for item in raw:
            lead = lead_from_harvest(item, q)
            key = lead.get("dedupe_key") or ""
            if not key or key in seen:
                continue
            if hard_exclude_reason(lead):
                continue
            if lead.get("score", 0) < 3:
                continue
            seen.add(key)
            leads.append(lead)
            accepted += 1
        print(f"  raw={len(raw)} accepted={accepted}")
    out = DATA_DIR / "discovered_leads.json"
    out.write_text(json.dumps(leads, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved {len(leads)} leads -> {out}")
    return 0


def cmd_seed(_: argparse.Namespace) -> int:
    for seed in SEEDS:
        lead = prepare_seed(seed)
        result = upsert_lead(lead)
        print(f"seed {lead['first_name']} {lead['last_name']} score={lead['score']} -> {result}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    path = DATA_DIR / "discovered_leads.json"
    if not path.exists():
        print("no discovered_leads.json")
        return 1
    leads = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for lead in leads[: args.limit or len(leads)]:
        upsert_lead(lead)
        n += 1
    print(f"synced {n} leads")
    return 0


NOTE_MAX_CHARS = 300


def truncate_note(text: str, max_chars: int = NOTE_MAX_CHARS) -> str:
    note = re.sub(r"\s+", " ", (text or "").strip())
    if len(note) <= max_chars:
        return note
    cut = note[: max_chars - 1].rsplit(" ", 1)[0]
    return cut.rstrip(".,;") + "…"


def list_connection_ready(*, limit: int = 50) -> list[dict[str, Any]]:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            params={"where": "(status,eq,connection_ready)", "limit": limit},
        )
        r.raise_for_status()
        rows = r.json().get("list") or []
    rows.sort(key=lambda x: (-int(x.get("score") or 0), x.get("country") or ""))
    return rows


def patch_row(rid: int, fields: dict[str, Any]) -> None:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=45) as client:
        client.patch(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            json={"Id": rid, **fields},
        ).raise_for_status()


def send_unipile_invite(
    *,
    linkedin_url: str,
    note: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    base_url = os.environ.get("UNIPILE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("UNIPILE_API_KEY", "")
    account_id = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not (base_url and api_key and account_id):
        return {"ok": False, "reason": "missing_unipile_config"}

    url = normalize_linkedin_url(linkedin_url) or linkedin_url
    m = re.search(r"linkedin\.com/in/([^/?#]+)", url or "", re.I)
    public_id = m.group(1) if m else None
    note = truncate_note(note)

    if dry_run:
        return {"ok": True, "dry_run": True, "note": note, "linkedin_url": url, "public_id": public_id}

    headers = {"X-API-KEY": api_key, "Accept": "application/json", "Content-Type": "application/json"}
    provider_id = None
    with httpx.Client(timeout=45) as client:
        if public_id:
            lookup = client.get(
                f"{base_url}/users/{public_id}",
                params={"account_id": account_id},
                headers=headers,
            )
            if lookup.status_code < 400 and lookup.content:
                body = lookup.json()
                provider_id = body.get("provider_id") or body.get("id")

        payload: dict[str, Any] = {"account_id": account_id, "message": note}
        if provider_id:
            payload["provider_id"] = provider_id
        elif public_id:
            payload["provider_public_id"] = public_id
        else:
            return {"ok": False, "reason": "missing_public_id"}

        resp = client.post(f"{base_url}/users/invite", headers=headers, json=payload)
        if resp.status_code >= 400:
            return {"ok": False, "http_status": resp.status_code, "error": (resp.text or "")[:500]}
        return {"ok": True, "http_status": resp.status_code}


def cmd_ready(_: argparse.Namespace) -> int:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{base}/api/v2/tables/{TABLE_ID}/records", headers=headers, params={"limit": 200})
        r.raise_for_status()
        rows = r.json().get("list") or []
    n = 0
    for row in rows:
        if int(row.get("score") or 0) < 4:
            continue
        if row.get("status") in {"connection_sent", "accepted", "followup_ready", "followup_sent"}:
            continue
        rid = row.get("Id")
        if rid is None:
            continue
        patch_row(int(rid), {"status": "connection_ready"})
        n += 1
        print(f"ready id={rid} {row.get('first_name')} {row.get('last_name')} score={row.get('score')}")
    print(f"marked connection_ready: {n}")
    return 0


def cmd_contact(args: argparse.Namespace) -> int:
    dry_run = not args.live
    rows = list_connection_ready(limit=args.limit or 50)
    if not rows:
        print("No hay filas con status=connection_ready")
        return 0
    print(f"contact {'DRY-RUN' if dry_run else 'LIVE'} limit={args.limit or len(rows)} rows={len(rows)}")
    results: list[dict[str, Any]] = []
    for i, row in enumerate(rows[: args.limit or len(rows)], 1):
        rid = row.get("Id")
        note = row.get("connection_message") or ""
        url = row.get("linkedin_url") or ""
        out = send_unipile_invite(linkedin_url=url, note=note, dry_run=dry_run)
        out["id"] = rid
        out["name"] = f"{row.get('first_name')} {row.get('last_name')}".strip()
        results.append(out)
        print(f"[{i}] {out['name']} -> {json.dumps({k: out[k] for k in out if k != 'note'}, ensure_ascii=False)}")
        if dry_run:
            print(f"    note ({len(truncate_note(note))} chars): {truncate_note(note)[:120]}…")
        elif out.get("ok") and rid is not None:
            patch_row(int(rid), {"status": "connection_sent"})
    path = DATA_DIR / "contact_results.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def cmd_rescore(_: argparse.Namespace) -> int:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{base}/api/v2/tables/{TABLE_ID}/records", headers=headers, params={"limit": 200})
        r.raise_for_status()
        rows = r.json().get("list") or []
    updated = 0
    for row in rows:
        if str(row.get("source_query") or "").startswith("seed:"):
            print(f"skip seed id={row.get('Id')} {row.get('first_name')} {row.get('last_name')}")
            continue
        lead = {
            "first_name": row.get("first_name"),
            "last_name": row.get("last_name"),
            "job_title": row.get("job_title"),
            "headline": row.get("headline"),
            "company": row.get("company"),
            "country": row.get("country"),
            "linkedin_url": row.get("linkedin_url"),
            "source_query": row.get("source_query"),
        }
        if hard_exclude_reason(lead):
            row["status"] = "not_relevant"
            row["score"] = 1
            row["reason_for_fit"] = "Excluded after hard-filter review"
            row["connection_message"] = ""
            row["followup_message"] = ""
        else:
            s, reason, kws = score_lead(lead)
            row["score"] = s
            row["reason_for_fit"] = reason
            row["relevant_keywords"] = ", ".join(kws)
            row["practice"] = detect_practice(f"{lead.get('job_title','')} {lead.get('headline','')}")
            row["seniority"] = detect_seniority(str(lead.get("job_title") or ""))
            if s >= 4:
                cm, fm = build_messages({**lead, **row})
                row["connection_message"] = cm
                row["followup_message"] = fm
                row["status"] = "reviewed"
            elif s == 3:
                row["status"] = "reviewed"
                row["connection_message"] = ""
                row["followup_message"] = ""
            else:
                row["status"] = "not_relevant"
        rid = row.get("Id")
        if rid is None:
            continue
        with httpx.Client(timeout=45) as client:
            client.patch(
                f"{base}/api/v2/tables/{TABLE_ID}/records",
                headers={"xc-token": token, "Content-Type": "application/json"},
                json={
                    "Id": rid,
                    "score": row.get("score"),
                    "status": row.get("status"),
                    "reason_for_fit": row.get("reason_for_fit"),
                    "relevant_keywords": row.get("relevant_keywords"),
                    "practice": row.get("practice"),
                    "seniority": row.get("seniority"),
                    "connection_message": row.get("connection_message") or "",
                    "followup_message": row.get("followup_message") or "",
                },
            ).raise_for_status()
        updated += 1
        print(f"rescore id={rid} score={row.get('score')} status={row.get('status')} {row.get('first_name')} {row.get('last_name')}")
    print(f"updated {updated} rows")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            params={"limit": 100},
        )
        r.raise_for_status()
        rows = r.json().get("list") or []
    rows.sort(key=lambda x: int(x.get("score") or 0), reverse=True)
    print(f"{'score':>5}  {'name':<28} {'company':<12} {'country':<18} status")
    print("-" * 90)
    for row in rows:
        name = f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip() or (row.get("title") or "")[:28]
        print(
            f"{int(row.get('score') or 0):>5}  {name:<28} {(row.get('company') or '')[:12]:<12} "
            f"{(row.get('country') or '')[:18]:<18} {row.get('status') or ''}"
        )
    export = DATA_DIR / "consultoras_review_table.json"
    export.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nexported -> {export}")
    return 0


def cmd_queries(_: argparse.Namespace) -> int:
    for i, q in enumerate(build_queries(), 1):
        print(f"{i:02d}. {q.label} | {q.location} | companies={q.current_companies}")
    return 0


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("provision-columns")
    sub.add_parser("queries")
    sub.add_parser("seed")
    p_disc = sub.add_parser("discover")
    p_disc.add_argument("--max-queries", type=int, default=4)
    p_disc.add_argument("--max-per-query", type=int, default=8)
    p_disc.add_argument("--query", type=str, default="")
    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--limit", type=int, default=0)
    sub.add_parser("list")
    sub.add_parser("rescore")
    sub.add_parser("ready")
    p_contact = sub.add_parser("contact")
    p_contact.add_argument("--limit", type=int, default=4)
    p_contact.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.cmd == "provision-columns":
        provision_columns()
        return 0
    if args.cmd == "queries":
        return cmd_queries(args)
    if args.cmd == "seed":
        return cmd_seed(args)
    if args.cmd == "discover":
        return asyncio.run(cmd_discover(args))
    if args.cmd == "sync":
        return cmd_sync(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "rescore":
        return cmd_rescore(args)
    if args.cmd == "ready":
        return cmd_ready(args)
    if args.cmd == "contact":
        return cmd_contact(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
