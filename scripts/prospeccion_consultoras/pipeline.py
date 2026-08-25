#!/usr/bin/env python3
"""Prospección consultoras: Harvest (filtros estrictos) → scoring → NocoDB."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
    ("invitation_id", "SingleLineText"),
    ("connection_sent_at", "DateTime"),
    ("accepted_at", "DateTime"),
    ("followup_sent_at", "DateTime"),
]

INVITE_MIN_WAIT = int(os.environ.get("CONSULTORAS_INVITE_MIN_WAIT", "30"))
INVITE_MAX_WAIT = int(os.environ.get("CONSULTORAS_INVITE_MAX_WAIT", "90"))
INMAIL_WAIT_SECONDS = int(os.environ.get("CONSULTORAS_INMAIL_WAIT_SECONDS", "0"))
INMAIL_DAILY_LIMIT = int(os.environ.get("CONSULTORAS_INMAIL_DAILY_LIMIT", "20"))
POLL_MIN_WAIT = int(os.environ.get("CONSULTORAS_POLL_MIN_WAIT", "30"))
POLL_MAX_WAIT = int(os.environ.get("CONSULTORAS_POLL_MAX_WAIT", "90"))
FOLLOWUP_MIN_WAIT = int(os.environ.get("CONSULTORAS_FOLLOWUP_MIN_WAIT", "30"))
FOLLOWUP_MAX_WAIT = int(os.environ.get("CONSULTORAS_FOLLOWUP_MAX_WAIT", "90"))
DEFAULT_FOLLOWUP_MIN_HOURS = int(os.environ.get("CONSULTORAS_FOLLOWUP_MIN_HOURS", "0"))
PROCESS_MIN_SCORE = 4

HARD_EXCLUDE = (
    "recruiter",
    "talent acquisition",
    "talent & workforce",
    "talent and workforce",
    "workforce lead",
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
    "partner development",
    "business development director",
    "director de arte",
    "art director",
    "creative director",
    "director creativo",
    "director creativa",
    "graphic design",
    "visual design",
    "brand design",
    "ux design",
    "ui design",
    "product design",
    "design & digital",
    "design and digital",
    "digital factory",
    "diseño gráfico",
    "diseño visual",
    "ilustrador",
    "ilustradora",
    "fotograf",
    "copywriter",
    "content creator",
    "social media manager",
)

SME_PRACTICE_MARKERS = (
    "marketing",
    "commerce",
    "customer",
    "crm",
    "martech",
    "adtech",
    "marketing technology",
    "digital transformation",
    "transformación digital",
    "automation",
    "automatización",
    "innovation",
    "innovación",
    "experience",
    "experiencia",
    "personalization",
    "personalización",
    "engagement",
    "analytics",
    "generative ai",
    "agentic ai",
    "intelligent automation",
    "digital marketing",
    "marketing transformation",
    "digital channels",
    "digital experience",
    "customer experience",
    "sales b2b",
    "song",
    "deloitte digital",
    "accenture song",
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
    "pwc": "https://www.linkedin.com/company/1048",
    "everis": "https://www.linkedin.com/company/8339",
    "ntt_data": "https://www.linkedin.com/company/19141006",
    "kpmg": "https://www.linkedin.com/company/1079",
    "kpmg_spain": "https://www.linkedin.com/company/2525300",
    "making_science": "https://www.linkedin.com/company/37596418",
    "idom": "https://www.linkedin.com/company/164711",
}

FIRM_BRANDS = {
    "deloitte": "Deloitte Digital",
    "deloitte_digital": "Deloitte Digital",
    "accenture": "Accenture Song",
    "pwc": "PwC",
    "everis": "everis",
    "ntt_data": "NTT DATA",
    "kpmg": "KPMG",
    "making_science": "Making Science",
    "idom": "IDOM",
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


def build_sme_queries() -> list[HarvestQuery]:
    """Directores/socios digitales para outreach SME vía Sales Navigator InMail."""
    es_digital_leaders = (
        "Socio Marketing,Socia Marketing,Socio Digital,Socia Digital,"
        "Partner Marketing,Partner Digital,Partner Customer,Partner Innovation,"
        "Director Marketing,Directora Marketing,Director Digital,Directora Digital,"
        "Director Customer Experience,Director CRM,Director MarTech,Director Innovación,"
        "Director Transformación Digital,Director Marketing Digital,"
        "Managing Director Marketing,Managing Director Digital"
    )
    en_digital_leaders = (
        "Partner Marketing,Partner Customer,Partner Digital,Partner Digital Transformation,"
        "Partner MarTech,Partner Innovation,Managing Director Marketing,Managing Director Digital,"
        "Managing Director Customer,Director Marketing Commerce,Director Customer Experience,"
        "Director Digital Transformation,Director MarTech,Director Marketing Technology,"
        "Director Innovation,Director Digital,Director CRM,Director Marketing,"
        "Practice Lead Marketing,Practice Lead Customer"
    )
    return [
        HarvestQuery(
            "sme_deloitte_digital_es",
            "Spain",
            COMPANY_URLS["deloitte_digital"],
            es_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM OR transformación",
        ),
        HarvestQuery(
            "sme_accenture_song_es",
            "Spain",
            COMPANY_URLS["accenture"],
            es_digital_leaders,
            "Accenture Song marketing OR customer OR digital OR martech",
        ),
        HarvestQuery(
            "sme_pwc_es",
            "Spain",
            COMPANY_URLS["pwc"],
            es_digital_leaders,
            "digital OR marketing OR customer OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_everis_es",
            "Spain",
            COMPANY_URLS["everis"],
            es_digital_leaders,
            "marketing OR customer OR digital OR transformación",
        ),
        HarvestQuery(
            "sme_ntt_es",
            "Spain",
            COMPANY_URLS["ntt_data"],
            es_digital_leaders,
            "marketing OR customer OR digital OR transformación OR martech",
        ),
        HarvestQuery(
            "sme_ntt_uk",
            "United Kingdom",
            COMPANY_URLS["ntt_data"],
            en_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_ntt_us",
            "United States",
            COMPANY_URLS["ntt_data"],
            en_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_kpmg_es",
            "Spain",
            COMPANY_URLS["kpmg_spain"],
            es_digital_leaders,
            "marketing OR customer OR digital OR transformación OR martech",
        ),
        HarvestQuery(
            "sme_kpmg_uk",
            "United Kingdom",
            COMPANY_URLS["kpmg"],
            en_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_kpmg_us",
            "United States",
            COMPANY_URLS["kpmg"],
            en_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_making_science_es",
            "Spain",
            COMPANY_URLS["making_science"],
            es_digital_leaders,
            "marketing OR martech OR digital OR performance",
        ),
        HarvestQuery(
            "sme_idom_es",
            "Spain",
            COMPANY_URLS["idom"],
            es_digital_leaders,
            "digital OR innovación OR transformación OR datos OR marketing",
        ),
        HarvestQuery(
            "sme_deloitte_digital_uae",
            "United Arab Emirates",
            COMPANY_URLS["deloitte_digital"],
            en_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_accenture_song_uae",
            "United Arab Emirates",
            COMPANY_URLS["accenture"],
            en_digital_leaders,
            "Accenture Song marketing OR customer OR digital",
        ),
        HarvestQuery(
            "sme_pwc_uae",
            "United Arab Emirates",
            COMPANY_URLS["pwc"],
            en_digital_leaders,
            "digital OR marketing OR customer OR martech",
        ),
        HarvestQuery(
            "sme_deloitte_digital_uk",
            "United Kingdom",
            COMPANY_URLS["deloitte_digital"],
            en_digital_leaders,
            "marketing OR customer OR digital OR martech OR CRM",
        ),
        HarvestQuery(
            "sme_accenture_song_uk",
            "United Kingdom",
            COMPANY_URLS["accenture"],
            en_digital_leaders,
            "Accenture Song marketing OR customer OR digital",
        ),
        HarvestQuery(
            "sme_pwc_uk",
            "United Kingdom",
            COMPANY_URLS["pwc"],
            en_digital_leaders,
            "digital OR marketing OR customer OR martech",
        ),
        HarvestQuery(
            "sme_making_science_uk",
            "United Kingdom",
            COMPANY_URLS["making_science"],
            en_digital_leaders,
            "marketing OR martech OR digital OR performance",
        ),
    ]


def processable_score(score: int | float | None) -> bool:
    return int(score or 0) >= PROCESS_MIN_SCORE


def should_process_lead(lead: dict[str, Any]) -> bool:
    if str(lead.get("source_query") or "").startswith("seed:"):
        return True
    return processable_score(lead.get("score"))


def status_for_score(score: int) -> str:
    return "reviewed" if processable_score(score) else "not_relevant"


def hard_exclude_reason(lead: dict[str, Any]) -> str | None:
    if is_manual_lead(lead):
        return None
    blob = _norm(" ".join([
        str(lead.get("job_title") or ""),
        str(lead.get("headline") or ""),
        str(lead.get("title") or ""),
    ]))
    if not blob.strip():
        return "empty_title"
    for marker in HARD_EXCLUDE:
        if marker.strip() == "intern" and "international" in blob:
            continue
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
    if "martech" in b or "marketing technology" in b:
        return "MarTech"
    if "digital transformation" in b or "transformacion digital" in b:
        return "Digital Transformation"
    if "innovation" in b or "innovacion" in b:
        return "Innovation"
    if "technology" in b and "transformation" in b:
        return "Technology & Transformation"
    if any(k in b for k in ("marketing", "commerce", "crm", "adtech", "automation", "automatizacion")):
        return "Digital"
    if "deloitte digital" in b or "accenture song" in b:
        return "Digital"
    return ""


def detect_seniority(title: str) -> str:
    t = _norm(title)
    if "managing partner" in t or re.search(r"\bpartner\b", t):
        return "Partner"
    if "managing director" in t:
        return "Managing Director"
    if "executive manager" in t or "executive director" in t:
        return "Director"
    if "practice lead" in t or re.search(r"\blead\b", t):
        return "Director"
    if "director" in t:
        return "Director"
    if "senior manager" in t:
        return "Senior Manager"
    return "Other"


def is_manual_lead(lead: dict[str, Any]) -> bool:
    return str(lead.get("source_query") or "").startswith("manual:")


def is_sme_lead(lead: dict[str, Any]) -> bool:
    if lead.get("contact_type") == "sme_inmail":
        return True
    return str(lead.get("source_query") or "").startswith("sme_")


def has_sme_practice_signal(blob: str) -> bool:
    b = _norm(blob)
    return any(marker in b for marker in SME_PRACTICE_MARKERS)


def is_generic_senior_title(title: str) -> bool:
    t = _norm(title)
    if not t:
        return True
    generic = (
        "partner",
        "socio",
        "socia",
        "managing director",
        "director general",
        "senior managing director",
        "principal",
    )
    if t in generic:
        return True
    if t in {"director", "directora"}:
        return True
    if re.fullmatch(r"(senior )?managing director", t):
        return True
    return False


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
    sme = is_sme_lead(lead)
    practice_signal = bool(practice) or has_sme_practice_signal(blob)

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

    if sme:
        if not practice_signal:
            score = min(score, 2.5)
        elif is_generic_senior_title(title) and not keywords:
            score = min(score, 3)
        if re.search(r"\b(design|diseño|arte|creative|creativ|visual|brand)\b", _norm(blob)):
            score = 1

    final = max(1, min(5, int(round(score))))
    practice_label = practice or "unclear practice"
    reason = (
        f"{seniority} in {practice_label} at {lead.get('company_name') or lead.get('company') or 'target firm'} "
        f"— relevant for customer/MarTech/automation workstreams in {country or lead.get('location') or 'region'}."
    )
    if sme and not practice_signal:
        reason = (
            f"{seniority} at {lead.get('company_name') or lead.get('company') or 'target firm'} "
            f"— no clear MarTech/customer/automation signal in title or headline."
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


def firm_brand(lead: dict[str, Any]) -> str:
    tier = str(lead.get("company_tier") or "")
    if tier in FIRM_BRANDS:
        return FIRM_BRANDS[tier]
    blob = _norm(" ".join([str(lead.get("company") or ""), str(lead.get("headline") or ""), str(lead.get("source_query") or "")]))
    if "accenture" in blob and "song" in blob:
        return "Accenture Song"
    if "deloitte" in blob:
        return "Deloitte Digital"
    if "pwc" in blob or "pricewaterhouse" in blob:
        return "PwC"
    if "making science" in blob:
        return "Making Science"
    if "kpmg" in blob:
        return "KPMG"
    if "everis" in blob or "ntt" in blob:
        return "everis" if "everis" in blob else "NTT DATA"
    return str(lead.get("company") or "la consultora")


def use_spanish_outreach(lead: dict[str, Any]) -> bool:
    country = str(lead.get("country") or lead.get("location") or "")
    return any(x in country for x in ("Spain", "España"))


def build_sme_inmail_message(lead: dict[str, Any]) -> str:
    first = (lead.get("first_name") or "there").strip()
    brand = firm_brand(lead)
    if use_spanish_outreach(lead):
        return (
            f"Hola {first}, encantado.\n\n"
            f"Te escribo para ver si podrías indicarme qué persona o equipo sería el adecuado dentro de {brand}.\n\n"
            f"Llevo más de 20 años trabajando entre negocio y tecnología, ayudando a empresas a mejorar marketing, "
            f"automatización, uso de datos y desarrollar nuevas soluciones digitales. He trabajado con empresas como "
            f"Telefónica, Havas y WPP.\n\n"
            f"Me gustaría explorar la posibilidad de colaborar con {brand} como consultor o especialista externo, "
            f"apoyando proyectos concretos donde mi experiencia pueda ser útil.\n\n"
            f"Si crees que puede tener sentido, encantado de contarte un poco más sobre mi trayectoria. También te "
            f"agradecería mucho tu orientación sobre con quién debería hablar internamente.\n\n"
            f"Muchas gracias,\nEmiliano"
        )
    return (
        f"Hi {first}, nice to meet you.\n\n"
        f"I'm reaching out to see if you could point me to the right person or team at {brand}.\n\n"
        f"I have more than 20 years of experience working between business and technology, helping companies improve "
        f"marketing, automation, data use and develop new digital solutions. I've worked with companies such as "
        f"Telefónica, Havas and WPP.\n\n"
        f"I'd like to explore the possibility of collaborating with {brand} as an external consultant or specialist, "
        f"supporting specific projects where my experience could be useful.\n\n"
        f"If you think it could make sense, I'd be happy to share a bit more about my background. I'd also really "
        f"appreciate your guidance on who would be the right person to speak with internally.\n\n"
        f"Thank you,\nEmiliano"
    )


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
        tier = "deloitte_digital" if "digital" in cl or "deloitte_digital" in query.label else "deloitte"
    elif "accenture" in cl:
        tier = "accenture"
    elif "pwc" in cl or "pricewaterhouse" in cl:
        tier = "pwc"
    elif "making science" in cl:
        tier = "making_science"
    elif "idom" in cl:
        tier = "idom"
    elif "kpmg" in cl:
        tier = "kpmg"
    elif "everis" in cl or "ntt" in cl:
        tier = "everis" if "everis" in cl else "ntt_data"

    sme = query.label.startswith("sme_")
    contact_type = "sme_inmail" if sme else "practice_leader"

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
        "contact_type": contact_type,
        "status": "new",
    }
    s, reason, kws = score_lead(lead)
    lead["score"] = s
    lead["reason_for_fit"] = reason
    lead["relevant_keywords"] = kws
    lead["practice"] = detect_practice(f"{title} {headline}")
    lead["seniority"] = detect_seniority(title)
    if s >= 4:
        if sme:
            lead["connection_message"] = build_sme_inmail_message(lead)
            lead["followup_message"] = ""
        else:
            cm, fm = build_messages(lead)
            lead["connection_message"] = cm
            lead["followup_message"] = fm
    lead["status"] = status_for_score(s)
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


RESCORE_MUTABLE_STATUSES = frozenset({
    "new",
    "reviewed",
    "connection_ready",
    "inmail_ready",
})

PROTECTED_STATUSES = frozenset({
    "connection_ready",
    "connection_sent",
    "accepted",
    "followup_ready",
    "followup_sent",
    "inmail_ready",
    "inmail_sent",
})


SYNC_SKIP_STATUSES = frozenset({
    "not_relevant",
    *PROTECTED_STATUSES,
})


def upsert_lead(lead: dict[str, Any]) -> dict[str, Any]:
    if not should_process_lead(lead):
        return {
            "action": "skip",
            "dedupe_key": lead.get("dedupe_key") or dedupe_key(lead.get("linkedin_url")),
            "reason": f"score_below_min:{lead.get('score')}",
        }
    base, token = nocodb_creds()
    row = row_for_nocodb(lead)
    key = row.get("dedupe_key") or ""
    headers = {"xc-token": token, "Content-Type": "application/json", "Accept": "application/json"}
    existing = find_by_dedupe(base, token, key)
    with httpx.Client(timeout=45) as client:
        if existing and existing.get("Id") is not None:
            if str(existing.get("status") or "") in SYNC_SKIP_STATUSES:
                return {
                    "action": "skip",
                    "id": existing["Id"],
                    "dedupe_key": key,
                    "reason": f"protected_status:{existing.get('status')}",
                }
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
        max_pages = max(2, min(4, (max_items + 24) // 25))
        for page in range(1, max_pages + 1):
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


def _name_tokens(name: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", _norm(name)) if len(t) > 1}


def resolve_sn_profile(*, keywords: str, expect_name: str = "") -> dict[str, Any] | None:
    base_url = os.environ.get("UNIPILE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("UNIPILE_API_KEY", "")
    account_id = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not (base_url and api_key and account_id):
        return None
    headers = {"X-API-KEY": api_key, "Accept": "application/json", "Content-Type": "application/json"}
    body = {"api": "sales_navigator", "category": "people", "keywords": keywords}
    expect_parts = [t for t in re.split(r"\s+", expect_name.strip()) if t]
    expect_first = _norm(expect_parts[0]) if expect_parts else ""
    expect_last_parts = [_norm(p) for p in expect_parts[1:]] if len(expect_parts) > 1 else []
    best: tuple[int, dict[str, Any]] | None = None
    with httpx.Client(timeout=45) as client:
        resp = client.post(
            f"{base_url}/linkedin/search",
            params={"account_id": account_id},
            headers=headers,
            json=body,
        )
        if resp.status_code >= 400:
            return None
        for item in resp.json().get("items") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            headline = str(item.get("headline") or "")
            blob = _norm(f"{name} {headline}")
            name_tokens = _name_tokens(name)
            if expect_first and expect_first not in name_tokens and expect_first not in _norm(name):
                continue
            if expect_last_parts and not all(p in name_tokens or p in _norm(name) for p in expect_last_parts):
                continue
            score = 0
            if expect_first and expect_first in name_tokens:
                score += 4
            score += 2 * sum(1 for p in expect_last_parts if p in name_tokens)
            if "ntt" in blob or "everis" in blob:
                score += 4
            if "sap" in blob:
                score += 2
            if "director" in blob or "head" in blob or "partner" in blob or "socio" in blob:
                score += 1
            if score < 8:
                continue
            pid = item.get("public_identifier")
            if pid:
                lookup = client.get(
                    f"{base_url}/users/{pid}",
                    params={"account_id": account_id},
                    headers={"X-API-KEY": api_key, "Accept": "application/json"},
                )
                if lookup.status_code < 400 and lookup.content:
                    occ = _norm(str(lookup.json().get("headline") or lookup.json().get("occupation") or headline))
                    if "ntt" not in occ and "everis" not in occ:
                        continue
            candidate = {
                "name": name,
                "headline": headline,
                "public_identifier": pid,
                "profile_url": item.get("profile_url"),
                "member_id": item.get("id"),
            }
            if best is None or score > best[0]:
                best = (score, candidate)
    return best[1] if best else None


def prepare_manual_lead(raw: dict[str, Any], *, source_query: str) -> dict[str, Any]:
    first = str(raw.get("first_name") or "").strip()
    last = str(raw.get("last_name") or "").strip()
    title = str(raw.get("job_title") or "").strip()
    company = str(raw.get("company") or "NTT DATA Europe & Latam").strip()
    country = str(raw.get("country") or "Spain").strip()
    city = str(raw.get("city") or "").strip()
    headline = str(raw.get("headline") or title).strip()
    url = normalize_linkedin_url(raw.get("linkedin_url"))
    if not url:
        resolved = resolve_sn_profile(
            keywords=str(raw.get("sn_keywords") or f"{first} {last} {company}"),
            expect_name=f"{first} {last}",
        )
        if resolved:
            pid = resolved.get("public_identifier")
            if pid:
                url = normalize_linkedin_url(f"https://www.linkedin.com/in/{pid}")
            headline = headline or str(resolved.get("headline") or "")
    lead: dict[str, Any] = {
        "first_name": first,
        "last_name": last,
        "linkedin_url": url or "",
        "company": company,
        "company_tier": "ntt_data",
        "country": country,
        "city": city,
        "job_title": title,
        "headline": headline,
        "location": city or country,
        "source_query": source_query,
        "dedupe_key": dedupe_key(url),
        "contact_type": "sme_inmail",
        "status": "reviewed",
    }
    lead["practice"] = detect_practice(f"{title} {headline}") or "Digital Transformation"
    lead["seniority"] = detect_seniority(title)
    lead["score"] = 4
    if lead["seniority"] in {"Partner", "Managing Director"}:
        lead["score"] = 5
    lead["reason_for_fit"] = (
        f"Importación manual SN — {lead['seniority']} SAP en {company} ({country}). "
        f"Perfil solicitado para colaboración externa."
    )
    lead["relevant_keywords"] = [k for k in ("sap", "crm", "cx", "successfactors") if k in _norm(f"{title} {headline}")]
    lead["connection_message"] = build_sme_inmail_message(lead)
    lead["followup_message"] = ""
    return lead


def cmd_import_manual(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_absolute():
        path = DATA_DIR / path
    if not path.exists():
        print(f"no existe {path}")
        return 1
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        print("el fichero debe ser un array JSON")
        return 1
    source_query = args.source_query or "manual:ntt_sap_sn_spain"
    imported = 0
    skipped = 0
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        lead = prepare_manual_lead(raw, source_query=source_query)
        if not lead.get("linkedin_url"):
            print(f"SKIP sin URL: {lead.get('first_name')} {lead.get('last_name')}")
            skipped += 1
            continue
        result = upsert_lead(lead)
        imported += 1
        print(
            f"{result.get('action')} id={result.get('id')} "
            f"{lead['first_name']} {lead['last_name']} score={lead['score']} "
            f"url={lead['linkedin_url']}"
        )
    print(f"imported={imported} skipped={skipped}")
    return 0 if imported else 1


def parse_saved_search_id(value: str) -> str:
    text = (value or "").strip()
    m = re.search(r"savedSearchId=(\d+)", text, re.I)
    if m:
        return m.group(1)
    if text.isdigit():
        return text
    raise ValueError(f"no savedSearchId in: {value[:120]}")


def split_person_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def infer_country_from_location(location: str) -> str:
    loc = _norm(location)
    if not loc:
        return ""
    hints = (
        ("united kingdom", "United Kingdom"),
        ("greater london", "United Kingdom"),
        ("london", "United Kingdom"),
        ("united states", "United States"),
        ("san francisco", "United States"),
        ("new york", "United States"),
        ("spain", "Spain"),
        ("españa", "Spain"),
        ("madrid", "Spain"),
        ("barcelona", "Spain"),
        ("germany", "Germany"),
        ("france", "France"),
        ("italy", "Italy"),
        ("portugal", "Portugal"),
        ("ireland", "Ireland"),
        ("netherlands", "Netherlands"),
        ("belgium", "Belgium"),
        ("switzerland", "Switzerland"),
        ("poland", "Poland"),
        ("mexico", "Mexico"),
        ("brazil", "Brazil"),
        ("india", "India"),
        ("uae", "United Arab Emirates"),
        ("dubai", "United Arab Emirates"),
    )
    for needle, country in hints:
        if needle in loc:
            return country
    return location.strip()


def fetch_sn_saved_search(saved_search_id: str, *, limit: int = 0) -> list[dict[str, Any]]:
    base_url = os.environ.get("UNIPILE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("UNIPILE_API_KEY", "")
    account_id = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not (base_url and api_key and account_id):
        raise RuntimeError("missing_unipile_config")
    headers = {"X-API-KEY": api_key, "Accept": "application/json", "Content-Type": "application/json"}
    body = {"api": "sales_navigator", "category": "people", "saved_search_id": str(saved_search_id)}
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    with httpx.Client(timeout=60) as client:
        while True:
            params: dict[str, Any] = {"account_id": account_id}
            if cursor:
                params["cursor"] = cursor
            resp = client.post(f"{base_url}/linkedin/search", params=params, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            batch = [x for x in (data.get("items") or []) if isinstance(x, dict)]
            rows.extend(batch)
            cursor = data.get("cursor")
            if limit and len(rows) >= limit:
                return rows[:limit]
            if not batch or not cursor:
                break
    return rows


def lead_from_sn_item(item: dict[str, Any], *, source_query: str) -> dict[str, Any]:
    full_name = str(item.get("name") or "").strip()
    first, last = split_person_name(full_name)
    headline = str(item.get("headline") or "").strip()
    location = str(item.get("location") or "").strip()
    pid = str(item.get("public_identifier") or "").strip()
    url = normalize_linkedin_url(item.get("linkedin_url") or (f"https://www.linkedin.com/in/{pid}" if pid else ""))
    company = "NTT DATA Europe & Latam"
    tier = "ntt_data"
    if "tangity" in _norm(headline):
        company = "NTT DATA / Tangity"
    lead: dict[str, Any] = {
        "first_name": first,
        "last_name": last,
        "linkedin_url": url or "",
        "company": company,
        "company_tier": tier,
        "country": infer_country_from_location(location),
        "city": location,
        "job_title": headline,
        "headline": headline,
        "location": location,
        "source_query": source_query,
        "dedupe_key": dedupe_key(url),
        "contact_type": "sme_inmail",
        "status": "new",
    }
    score, reason, kws = score_lead(lead)
    lead["score"] = score
    lead["reason_for_fit"] = reason
    lead["relevant_keywords"] = kws
    lead["practice"] = detect_practice(headline)
    lead["seniority"] = detect_seniority(headline)
    if score >= 4:
        lead["connection_message"] = build_sme_inmail_message(lead)
        lead["followup_message"] = ""
    lead["status"] = status_for_score(score)
    return lead


def sme_import_reject_reason(lead: dict[str, Any]) -> str | None:
    ex = hard_exclude_reason(lead)
    if ex:
        return ex
    if not lead.get("linkedin_url"):
        return "missing_url"
    seniority = lead.get("seniority") or detect_seniority(str(lead.get("job_title") or ""))
    if seniority not in SME_SENIORITY_OK:
        return f"seniority:{seniority}"
    blob = f"{lead.get('job_title') or ''} {lead.get('headline') or ''}"
    if not has_sme_practice_signal(blob):
        return "no_practice_signal"
    if int(lead.get("score") or 0) < PROCESS_MIN_SCORE:
        return f"score:{lead.get('score')}"
    return None


def cmd_import_sn(args: argparse.Namespace) -> int:
    source_query = args.source_query or ""
    if args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = DATA_DIR / path
        if not path.exists():
            print(f"no existe {path}")
            return 1
        raw_items = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            print("el fichero debe ser un array JSON")
            return 1
        saved_search_id = parse_saved_search_id(args.saved_search) if args.saved_search else "file"
    else:
        saved_search_id = parse_saved_search_id(args.saved_search or "")
        raw_items = fetch_sn_saved_search(saved_search_id, limit=args.limit or 0)
        export_path = DATA_DIR / f"sn_saved_{saved_search_id}.json"
        export_path.write_text(
            json.dumps(
                [
                    {
                        "name": it.get("name"),
                        "headline": it.get("headline"),
                        "public_identifier": it.get("public_identifier"),
                        "linkedin_url": (
                            f"https://www.linkedin.com/in/{it.get('public_identifier')}"
                            if it.get("public_identifier")
                            else None
                        ),
                        "location": it.get("location"),
                        "member_id": it.get("id"),
                    }
                    for it in raw_items
                ],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"fetched {len(raw_items)} -> {export_path}")
    if not source_query:
        source_query = f"sn:{saved_search_id}"

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        lead = lead_from_sn_item(item, source_query=source_query)
        reason = sme_import_reject_reason(lead)
        row = {
            "name": f"{lead.get('first_name')} {lead.get('last_name')}".strip(),
            "headline": lead.get("headline"),
            "score": lead.get("score"),
            "seniority": lead.get("seniority"),
            "linkedin_url": lead.get("linkedin_url"),
            "reason": reason,
        }
        if reason:
            rejected.append(row)
            if args.verbose:
                print(f"REJECT {row['name']} | {reason} | {row['headline'][:80]}")
        else:
            accepted.append(lead)
            if args.verbose:
                print(f"ACCEPT {row['name']} | score={row['score']} | {row['headline'][:80]}")

    filter_report = DATA_DIR / f"sn_filter_{saved_search_id}.json"
    filter_report.write_text(
        json.dumps({"accepted": len(accepted), "rejected": len(rejected), "rejected_rows": rejected}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"filter: raw={len(raw_items)} accepted={len(accepted)} rejected={len(rejected)} -> {filter_report}")

    if args.dry_run:
        preview = DATA_DIR / f"sn_accepted_{saved_search_id}.json"
        preview.write_text(
            json.dumps(
                [
                    {
                        "name": f"{l.get('first_name')} {l.get('last_name')}".strip(),
                        "score": l.get("score"),
                        "seniority": l.get("seniority"),
                        "practice": l.get("practice"),
                        "country": l.get("country"),
                        "linkedin_url": l.get("linkedin_url"),
                        "headline": l.get("headline"),
                    }
                    for l in accepted
                ],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"dry-run preview -> {preview}")
        return 0

    imported = 0
    for lead in accepted:
        result = upsert_lead(lead)
        imported += 1
        print(
            f"{result.get('action')} id={result.get('id')} "
            f"{lead.get('first_name')} {lead.get('last_name')} score={lead.get('score')}"
        )
    print(f"imported={imported}")
    return 0


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


SME_SENIORITY_OK = frozenset({"Partner", "Director", "Managing Director"})


def sme_discover_ok(lead: dict[str, Any]) -> bool:
    title = str(lead.get("job_title") or lead.get("title") or "")
    headline = str(lead.get("headline") or "")
    blob = f"{title} {headline}"
    seniority = lead.get("seniority") or detect_seniority(title)
    if seniority not in SME_SENIORITY_OK:
        return False
    return has_sme_practice_signal(blob)


async def cmd_discover(args: argparse.Namespace) -> int:
    segment = getattr(args, "segment", "hire") or "hire"
    queries = build_sme_queries() if segment == "sme" else build_queries()
    if args.query:
        queries = [q for q in queries if q.label == args.query]
    min_score = PROCESS_MIN_SCORE
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
            if lead.get("score", 0) < min_score:
                continue
            if segment == "sme" and not sme_discover_ok(lead):
                continue
            seen.add(key)
            leads.append(lead)
            accepted += 1
        print(f"  raw={len(raw)} accepted={accepted}")
    out = DATA_DIR / ("discovered_sme_leads.json" if segment == "sme" else "discovered_leads.json")
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
    segment = getattr(args, "segment", "hire") or "hire"
    path = DATA_DIR / ("discovered_sme_leads.json" if segment == "sme" else "discovered_leads.json")
    if not path.exists():
        print(f"no {path.name}")
        return 1
    leads = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for lead in leads[: args.limit or len(leads)]:
        upsert_lead(lead)
        n += 1
    print(f"synced {n} leads from {path.name}")
    return 0


NOTE_MAX_CHARS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    return (dt or utc_now()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def random_wait(min_s: int, max_s: int, *, label: str) -> int:
    wait_s = random.randint(min_s, max(min_s, max_s))
    if wait_s > 0:
        print(f"    waiting {wait_s}s ({label})…")
        time.sleep(wait_s)
    return wait_s


def truncate_note(text: str, max_chars: int = NOTE_MAX_CHARS) -> str:
    note = re.sub(r"\s+", " ", (text or "").strip())
    if len(note) <= max_chars:
        return note
    cut = note[: max_chars - 1].rsplit(" ", 1)[0]
    return cut.rstrip(".,;") + "…"


def list_rows_by_status(status: str, *, limit: int = 50) -> list[dict[str, Any]]:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            params={"where": f"(status,eq,{status})", "limit": limit},
        )
        r.raise_for_status()
        rows = r.json().get("list") or []
    rows.sort(key=lambda x: (-int(x.get("score") or 0), x.get("country") or ""))
    return rows


def list_connection_ready(*, limit: int = 50) -> list[dict[str, Any]]:
    return list_rows_by_status("connection_ready", limit=limit)


def patch_row(rid: int, fields: dict[str, Any]) -> None:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=45) as client:
        client.patch(
            f"{base}/api/v2/tables/{TABLE_ID}/records",
            headers=headers,
            json={"Id": rid, **fields},
        ).raise_for_status()


def unipile_public_id(linkedin_url: str) -> str | None:
    url = normalize_linkedin_url(linkedin_url) or linkedin_url
    m = re.search(r"linkedin\.com/in/([^/?#]+)", url or "", re.I)
    return m.group(1) if m else None


def lookup_unipile_profile(public_id: str) -> dict[str, Any]:
    base_url = os.environ.get("UNIPILE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("UNIPILE_API_KEY", "")
    account_id = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not (base_url and api_key and account_id):
        return {"ok": False, "reason": "missing_unipile_config"}
    headers = {"X-API-KEY": api_key, "Accept": "application/json"}
    with httpx.Client(timeout=45) as client:
        resp = client.get(
            f"{base_url}/users/{public_id}",
            params={"account_id": account_id},
            headers=headers,
        )
        if resp.status_code >= 400:
            return {"ok": False, "http_status": resp.status_code, "error": (resp.text or "")[:500]}
        body = resp.json() if resp.content else {}
        return {
            "ok": True,
            "provider_id": body.get("provider_id") or body.get("id"),
            "network_distance": body.get("network_distance"),
            "is_relationship": bool(body.get("is_relationship")),
            "public_identifier": body.get("public_identifier"),
        }


def profile_is_connected(profile: dict[str, Any]) -> bool:
    if profile.get("is_relationship"):
        return True
    return str(profile.get("network_distance") or "").upper() == "FIRST_DEGREE"


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
    public_id = unipile_public_id(url or "")
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
        body = resp.json() if resp.content else {}
        invitation_id = body.get("invitation_id")
        if not invitation_id and isinstance(body.get("object"), str):
            invitation_id = body.get("id")
        return {
            "ok": True,
            "http_status": resp.status_code,
            "invitation_id": invitation_id,
            "provider_id": provider_id,
        }


def send_unipile_message(
    *,
    provider_id: str,
    text: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    base_url = os.environ.get("UNIPILE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("UNIPILE_API_KEY", "")
    account_id = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not (base_url and api_key and account_id):
        return {"ok": False, "reason": "missing_unipile_config"}
    if not provider_id:
        return {"ok": False, "reason": "missing_provider_id"}
    text = (text or "").strip()
    if not text:
        return {"ok": False, "reason": "missing_message"}

    if dry_run:
        return {"ok": True, "dry_run": True, "provider_id": provider_id, "text_preview": text[:120]}

    headers = {"X-API-KEY": api_key, "Accept": "application/json"}
    with httpx.Client(timeout=45) as client:
        resp = client.post(
            f"{base_url}/chats",
            headers=headers,
            data={
                "account_id": account_id,
                "text": text,
                "attendees_ids": provider_id,
            },
        )
        if resp.status_code >= 400:
            return {"ok": False, "http_status": resp.status_code, "error": (resp.text or "")[:500]}
        body = resp.json() if resp.content else {}
        return {"ok": True, "http_status": resp.status_code, "chat_id": body.get("chat_id") or body.get("id")}


def send_unipile_inmail(
    *,
    linkedin_url: str,
    text: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Sales Navigator InMail a perfiles no conectados (linkedin[inmail]=true)."""
    base_url = os.environ.get("UNIPILE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("UNIPILE_API_KEY", "")
    account_id = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not (base_url and api_key and account_id):
        return {"ok": False, "reason": "missing_unipile_config"}

    url = normalize_linkedin_url(linkedin_url) or linkedin_url
    public_id = unipile_public_id(url or "")
    text = (text or "").strip()
    if not text:
        return {"ok": False, "reason": "missing_message"}

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "linkedin_url": url,
            "public_id": public_id,
            "text_preview": text[:160],
            "chars": len(text),
        }

    headers = {"X-API-KEY": api_key, "Accept": "application/json"}
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
        if not provider_id:
            return {"ok": False, "reason": "missing_provider_id"}

        resp = client.post(
            f"{base_url}/chats",
            headers=headers,
            data={
                "account_id": account_id,
                "text": text,
                "attendees_ids": provider_id,
                "linkedin[inmail]": "true",
                "linkedin[api]": "sales_navigator",
            },
        )
        if resp.status_code >= 400:
            return {"ok": False, "http_status": resp.status_code, "error": (resp.text or "")[:500]}
        body = resp.json() if resp.content else {}
        return {
            "ok": True,
            "http_status": resp.status_code,
            "chat_id": body.get("chat_id") or body.get("id"),
            "provider_id": provider_id,
        }


def cmd_ready(_: argparse.Namespace) -> int:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{base}/api/v2/tables/{TABLE_ID}/records", headers=headers, params={"limit": 200})
        r.raise_for_status()
        rows = r.json().get("list") or []
    n = 0
    for row in rows:
        if int(row.get("score") or 0) < PROCESS_MIN_SCORE:
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


def cmd_ready_inmail(_: argparse.Namespace) -> int:
    base, token = nocodb_creds()
    headers = {"xc-token": token, "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{base}/api/v2/tables/{TABLE_ID}/records", headers=headers, params={"limit": 300})
        r.raise_for_status()
        rows = r.json().get("list") or []
    n = 0
    for row in rows:
        if row.get("contact_type") != "sme_inmail":
            continue
        if int(row.get("score") or 0) < PROCESS_MIN_SCORE:
            continue
        if row.get("status") in {"inmail_sent", "connection_sent", "accepted", "followup_sent"}:
            continue
        rid = row.get("Id")
        if rid is None:
            continue
        patch_row(int(rid), {"status": "inmail_ready"})
        n += 1
        print(f"inmail_ready id={rid} {row.get('first_name')} {row.get('last_name')} score={row.get('score')}")
    print(f"marked inmail_ready: {n}")
    return 0


def list_inmail_ready(*, limit: int = 50) -> list[dict[str, Any]]:
    return list_rows_by_status("inmail_ready", limit=limit)


def cmd_inmail(args: argparse.Namespace) -> int:
    dry_run = not args.live
    rows = list_inmail_ready(limit=args.limit or 50)
    if not rows:
        print("No hay filas con status=inmail_ready")
        return 0
    total = min(len(rows), args.limit or len(rows))
    wait_s = int(getattr(args, "wait_seconds", 0) or 0) or INMAIL_WAIT_SECONDS or 0
    wait_label = f"{wait_s}s fixed" if wait_s else f"{INVITE_MIN_WAIT}-{INVITE_MAX_WAIT}s random"
    print(f"inmail {'DRY-RUN' if dry_run else 'LIVE'} limit={total} rows={len(rows)} wait={wait_label}")
    results: list[dict[str, Any]] = []
    for i, row in enumerate(rows[: args.limit or len(rows)], 1):
        if wait_s > 0:
            random_wait(wait_s, wait_s, label=f"before InMail {i}/{total}")
        else:
            random_wait(INVITE_MIN_WAIT, INVITE_MAX_WAIT, label=f"before InMail {i}/{total}")
        rid = row.get("Id")
        text = row.get("connection_message") or build_sme_inmail_message(row)
        url = row.get("linkedin_url") or ""
        out = send_unipile_inmail(linkedin_url=url, text=text, dry_run=dry_run)
        out["id"] = rid
        out["name"] = f"{row.get('first_name')} {row.get('last_name')}".strip()
        results.append(out)
        print(f"[{i}] {out['name']} -> {json.dumps({k: out[k] for k in out if k not in {'text_preview'}}, ensure_ascii=False)}")
        if dry_run:
            print(f"    message ({out.get('chars', len(text))} chars):\n{text[:400]}…")
        elif out.get("ok") and rid is not None:
            patch_row(int(rid), {"status": "inmail_sent", "connection_sent_at": iso_utc()})
    path = DATA_DIR / "inmail_results.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def cmd_preview_inmail(args: argparse.Namespace) -> int:
    sample = {
        "first_name": args.first_name or "Flor",
        "company_tier": args.tier or "deloitte_digital",
        "company": args.company or "Deloitte Digital",
        "country": args.country or "Spain",
    }
    msg = build_sme_inmail_message(sample)
    print(msg)
    print(f"\n--- {len(msg)} chars ---")
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
        random_wait(INVITE_MIN_WAIT, INVITE_MAX_WAIT, label=f"before invite {i}/{min(len(rows), args.limit or len(rows))}")
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
            patch_row(
                int(rid),
                {
                    "status": "connection_sent",
                    "connection_sent_at": iso_utc(),
                    "invitation_id": out.get("invitation_id") or row.get("invitation_id") or "",
                },
            )
    path = DATA_DIR / "contact_results.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def cmd_poll_acceptances(args: argparse.Namespace) -> int:
    dry_run = not args.live
    rows = list_rows_by_status("connection_sent", limit=args.limit or 100)
    if not rows:
        print("No hay filas con status=connection_sent")
        return 0
    print(f"poll-acceptances {'DRY-RUN' if dry_run else 'LIVE'} rows={len(rows)}")
    results: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        random_wait(POLL_MIN_WAIT, POLL_MAX_WAIT, label=f"before profile check {i}/{len(rows)}")
        name = f"{row.get('first_name')} {row.get('last_name')}".strip()
        public_id = unipile_public_id(row.get("linkedin_url") or "")
        if not public_id:
            out = {"ok": False, "reason": "missing_public_id", "id": row.get("Id"), "name": name}
            results.append(out)
            print(f"[{i}] {name} -> {json.dumps(out, ensure_ascii=False)}")
            continue
        profile = lookup_unipile_profile(public_id)
        connected = profile.get("ok") and profile_is_connected(profile)
        out = {
            "id": row.get("Id"),
            "name": name,
            "connected": connected,
            "network_distance": profile.get("network_distance"),
            "is_relationship": profile.get("is_relationship"),
        }
        results.append(out)
        print(f"[{i}] {name} -> {json.dumps(out, ensure_ascii=False)}")
        if connected and not dry_run and row.get("Id") is not None:
            patch_row(
                int(row["Id"]),
                {
                    "status": "accepted",
                    "accepted_at": iso_utc(),
                },
            )
    path = DATA_DIR / "poll_acceptances.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def cmd_followup(args: argparse.Namespace) -> int:
    dry_run = not args.live
    min_hours = args.min_hours_after_accept
    rows = list_rows_by_status("accepted", limit=args.limit or 50)
    if not rows:
        print("No hay filas con status=accepted")
        return 0
    cutoff = utc_now() - timedelta(hours=min_hours)
    eligible: list[dict[str, Any]] = []
    for row in rows:
        accepted_at = parse_iso_utc(row.get("accepted_at"))
        if accepted_at is None or accepted_at <= cutoff:
            eligible.append(row)
    if not eligible:
        print(f"No hay aceptaciones listas para follow-up (min_hours={min_hours})")
        return 0
    print(
        f"followup {'DRY-RUN' if dry_run else 'LIVE'} "
        f"eligible={len(eligible)} min_hours={min_hours} limit={args.limit}"
    )
    results: list[dict[str, Any]] = []
    total = min(len(eligible), args.limit or len(eligible))
    for i, row in enumerate(eligible[: args.limit or len(eligible)], 1):
        random_wait(FOLLOWUP_MIN_WAIT, FOLLOWUP_MAX_WAIT, label=f"before follow-up {i}/{total}")
        rid = row.get("Id")
        name = f"{row.get('first_name')} {row.get('last_name')}".strip()
        message = (row.get("followup_message") or "").strip()
        public_id = unipile_public_id(row.get("linkedin_url") or "")
        profile = lookup_unipile_profile(public_id or "")
        provider_id = profile.get("provider_id") if profile.get("ok") else None
        if not provider_id:
            out = {"ok": False, "reason": "missing_provider_id", "id": rid, "name": name}
            results.append(out)
            print(f"[{i}] {name} -> {json.dumps(out, ensure_ascii=False)}")
            continue
        out = send_unipile_message(provider_id=str(provider_id), text=message, dry_run=dry_run)
        out["id"] = rid
        out["name"] = name
        results.append(out)
        print(f"[{i}] {name} -> {json.dumps({k: out[k] for k in out if k != 'text_preview'}, ensure_ascii=False)}")
        if dry_run:
            preview = out.get("text_preview") or message[:120]
            print(f"    message ({len(message)} chars): {preview}…")
        elif out.get("ok") and rid is not None:
            patch_row(
                int(rid),
                {
                    "status": "followup_sent",
                    "followup_sent_at": iso_utc(),
                },
            )
    path = DATA_DIR / "followup_results.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def cmd_outreach(args: argparse.Namespace) -> int:
    """Poll acceptances, send follow-ups, then drain pending invites."""
    poll_args = argparse.Namespace(live=args.live, limit=args.limit)
    follow_args = argparse.Namespace(live=args.live, limit=args.followup_limit, min_hours_after_accept=args.min_hours_after_accept)
    contact_args = argparse.Namespace(live=args.live, limit=args.contact_limit)
    cmd_poll_acceptances(poll_args)
    cmd_followup(follow_args)
    return cmd_contact(contact_args)


def cmd_rescore(args: argparse.Namespace) -> int:
    segment = getattr(args, "segment", "all") or "all"
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
        if segment == "sme" and row.get("contact_type") != "sme_inmail":
            continue
        if segment == "hire" and row.get("contact_type") == "sme_inmail":
            continue
        prev_status = str(row.get("status") or "")
        lead = {
            "first_name": row.get("first_name"),
            "last_name": row.get("last_name"),
            "job_title": row.get("job_title"),
            "headline": row.get("headline"),
            "company": row.get("company"),
            "country": row.get("country"),
            "linkedin_url": row.get("linkedin_url"),
            "source_query": row.get("source_query"),
            "contact_type": row.get("contact_type"),
            "company_tier": row.get("company_tier"),
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
                if row.get("contact_type") == "sme_inmail":
                    row["connection_message"] = build_sme_inmail_message({**lead, **row})
                    row["followup_message"] = ""
                else:
                    cm, fm = build_messages({**lead, **row})
                    row["connection_message"] = cm
                    row["followup_message"] = fm
                row["status"] = status_for_score(s)
            else:
                row["status"] = "not_relevant"
                row["connection_message"] = ""
                row["followup_message"] = ""
        if prev_status in PROTECTED_STATUSES and prev_status not in RESCORE_MUTABLE_STATUSES:
            if row["status"] != "not_relevant":
                row["status"] = prev_status
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
    print(f"{'score':>5}  {'name':<28} {'company':<12} {'country':<18} {'type':<10} status")
    print("-" * 100)
    for row in rows:
        name = f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip() or (row.get("title") or "")[:28]
        ctype = (row.get("contact_type") or "")[:10]
        print(
            f"{int(row.get('score') or 0):>5}  {name:<28} {(row.get('company') or '')[:12]:<12} "
            f"{(row.get('country') or '')[:18]:<18} {ctype:<10} {row.get('status') or ''}"
        )
    export = DATA_DIR / "consultoras_review_table.json"
    export.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nexported -> {export}")
    return 0


def cmd_queries(args: argparse.Namespace) -> int:
    segment = getattr(args, "segment", "hire") or "hire"
    queries = build_sme_queries() if segment == "sme" else build_queries()
    for i, q in enumerate(queries, 1):
        search = f" | search={q.search}" if q.search else ""
        print(f"{i:02d}. {q.label} | {q.location} | companies={q.current_companies}{search}")
    return 0


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("provision-columns")
    p_queries = sub.add_parser("queries")
    p_queries.add_argument("--segment", choices=("hire", "sme"), default="hire")
    sub.add_parser("seed")
    p_disc = sub.add_parser("discover")
    p_disc.add_argument("--segment", choices=("hire", "sme"), default="hire")
    p_disc.add_argument("--max-queries", type=int, default=4)
    p_disc.add_argument("--max-per-query", type=int, default=8)
    p_disc.add_argument("--query", type=str, default="")
    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--segment", choices=("hire", "sme"), default="hire")
    p_sync.add_argument("--limit", type=int, default=0)
    p_import = sub.add_parser("import-manual")
    p_import.add_argument(
        "--file",
        type=str,
        default="manual_ntt_sap_spain.json",
        help="JSON en data/ con perfiles importados manualmente desde Sales Navigator",
    )
    p_import.add_argument(
        "--source-query",
        type=str,
        default="manual:ntt_sap_sn_spain",
        help="Etiqueta source_query para trazabilidad en NocoDB",
    )
    p_sn = sub.add_parser("import-sn")
    p_sn.add_argument(
        "--saved-search",
        type=str,
        default="",
        help="savedSearchId o URL completa de Sales Navigator",
    )
    p_sn.add_argument(
        "--file",
        type=str,
        default="",
        help="JSON exportado previamente (p. ej. sn_saved_2007338250.json); omite fetch Unipile",
    )
    p_sn.add_argument("--limit", type=int, default=0, help="Máximo perfiles a traer de Unipile")
    p_sn.add_argument("--source-query", type=str, default="", help="Etiqueta source_query (default sn:<id>)")
    p_sn.add_argument("--dry-run", action="store_true", help="Filtrar y exportar sin escribir en NocoDB")
    p_sn.add_argument("--verbose", action="store_true", help="Imprimir cada accept/reject")
    sub.add_parser("list")
    p_rescore = sub.add_parser("rescore")
    p_rescore.add_argument("--segment", choices=("all", "hire", "sme"), default="all")
    sub.add_parser("ready")
    sub.add_parser("ready-inmail")
    p_preview = sub.add_parser("preview-inmail")
    p_preview.add_argument("--first-name", type=str, default="Flor")
    p_preview.add_argument("--tier", type=str, default="deloitte_digital")
    p_preview.add_argument("--company", type=str, default="Deloitte Digital")
    p_preview.add_argument("--country", type=str, default="Spain")
    p_contact = sub.add_parser("contact")
    p_contact.add_argument("--limit", type=int, default=4)
    p_contact.add_argument("--live", action="store_true")
    p_inmail = sub.add_parser("inmail")
    p_inmail.add_argument("--limit", type=int, default=3)
    p_inmail.add_argument("--live", action="store_true")
    p_inmail.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        help="Pausa fija entre InMails (p. ej. 180 = 3 min). Si no se indica, usa CONSULTORAS_INMAIL_WAIT_SECONDS o 30-90s.",
    )
    p_poll = sub.add_parser("poll-acceptances")
    p_poll.add_argument("--limit", type=int, default=100)
    p_poll.add_argument("--live", action="store_true")
    p_follow = sub.add_parser("followup")
    p_follow.add_argument("--limit", type=int, default=3)
    p_follow.add_argument("--live", action="store_true")
    p_follow.add_argument(
        "--min-hours-after-accept",
        type=int,
        default=DEFAULT_FOLLOWUP_MIN_HOURS,
        help="Horas tras accepted_at antes de enviar follow-up (0 = inmediato tras detectar aceptación)",
    )
    p_outreach = sub.add_parser("outreach")
    p_outreach.add_argument("--live", action="store_true")
    p_outreach.add_argument("--contact-limit", type=int, default=6)
    p_outreach.add_argument("--followup-limit", type=int, default=3)
    p_outreach.add_argument("--limit", type=int, default=100)
    p_outreach.add_argument("--min-hours-after-accept", type=int, default=DEFAULT_FOLLOWUP_MIN_HOURS)
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
    if args.cmd == "import-manual":
        return cmd_import_manual(args)
    if args.cmd == "import-sn":
        return cmd_import_sn(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "rescore":
        return cmd_rescore(args)
    if args.cmd == "ready":
        return cmd_ready(args)
    if args.cmd == "ready-inmail":
        return cmd_ready_inmail(args)
    if args.cmd == "preview-inmail":
        return cmd_preview_inmail(args)
    if args.cmd == "contact":
        return cmd_contact(args)
    if args.cmd == "inmail":
        return cmd_inmail(args)
    if args.cmd == "poll-acceptances":
        return cmd_poll_acceptances(args)
    if args.cmd == "followup":
        return cmd_followup(args)
    if args.cmd == "outreach":
        return cmd_outreach(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
