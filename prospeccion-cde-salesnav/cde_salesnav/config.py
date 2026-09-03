"""Env + ICP defaults for CDE SalesNav discover."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ACCOUNT_ID = "rq1lQcYTToC9hlWD4vO94g"
DEFAULT_NOCODB_TABLE_ID = "mcu2bt73u6vlybz"
DEFAULT_NOCODB_REF_TABLE_ID = "m77jzqg4z30b3ez"
DEFAULT_NOCODB_BASE_ID = "p50p7eoxibwohc7"
CAMPAIGN_TAG = "cde_salesnav_en"
PRODUCT_URL = "https://companydataenrichment.com/salesnav/"
DEFAULT_ENV_FILES = (
    Path("/etc/linkedinreport/app.env"),
    ROOT / ".env",
)

EXCLUDED_COMPANIES = ("linkedin",)
EXCLUDED_TITLE_PATTERNS = (
    (r"\bintern(s|ship|ships)?\b", "intern"),
    (r"\btrainee\b", "trainee"),
    (r"\bapprentice\b", "apprentice"),
    (r"\bstudent\b", "student"),
    (r"\bjunior\b", "junior"),
    (r"\btalent acquisition\b", "talent acquisition"),
    (r"\brecruiters?\b", "recruiter"),
    (r"\brecruiting\b", "recruiting"),
    (r"\bpeople partner\b", "people partner"),
    (r"\bhuman resources\b", "human resources"),
)

SENIORITY_INCLUDE = (
    "owner/partner",
    "cxo",
    "vice_president",
    "director",
    "experienced_manager",
    "entry_level_manager",
)

ROLE_TITLES = (
    "Head of Sales",
    "VP Sales",
    "Sales Director",
    "Head of SDR",
    "Head of BDR",
    "SDR Manager",
    "Sales Development",
    "Revenue Operations",
    "Sales Operations",
    "Outbound",
)

LOCATION_KEYWORDS = ("United States", "United Kingdom", "Europe")
INDUSTRY_KEYWORDS = (
    "Software",
    "IT Services",
    "Advertising",
    "Business Consulting",
)

HEADCOUNT_BUCKETS = (
    {"min": 11, "max": 50},
    {"min": 51, "max": 200},
    {"min": 201, "max": 500},
    {"min": 501, "max": 1000},
)


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_env() -> None:
    for path in DEFAULT_ENV_FILES:
        _load_env_file(path)


def _truthy(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


@dataclass
class CdeConfig:
    unipile_base_url: str
    unipile_api_key: str
    unipile_account_id: str
    nocodb_base_url: str = "https://mpa.parvusmedia.com"
    nocodb_api_token: str = ""
    nocodb_table_id: str = DEFAULT_NOCODB_TABLE_ID
    nocodb_ref_table_id: str = DEFAULT_NOCODB_REF_TABLE_ID
    nocodb_base_id: str = DEFAULT_NOCODB_BASE_ID
    campaign: str = CAMPAIGN_TAG
    product_url: str = PRODUCT_URL
    min_employees: int = 11
    require_premium: bool = True
    location_keywords: tuple[str, ...] = LOCATION_KEYWORDS
    industry_keywords: tuple[str, ...] = INDUSTRY_KEYWORDS
    role_titles: tuple[str, ...] = ROLE_TITLES
    seniority_include: tuple[str, ...] = SENIORITY_INCLUDE
    headcount_buckets: tuple[dict[str, int], ...] = field(default_factory=lambda: HEADCOUNT_BUCKETS)

    @classmethod
    def from_env(cls) -> "CdeConfig":
        load_env()
        base = (os.environ.get("UNIPILE_BASE_URL") or "").strip().rstrip("/")
        key = (os.environ.get("UNIPILE_API_KEY") or "").strip()
        account = (
            os.environ.get("CDE_SALESNAV_UNIPILE_ACCOUNT_ID")
            or os.environ.get("UNIPILE_ACCOUNT_ID")
            or DEFAULT_ACCOUNT_ID
        ).strip()
        if not base or not key or not account:
            raise RuntimeError("missing_unipile_config")
        return cls(
            unipile_base_url=base,
            unipile_api_key=key,
            unipile_account_id=account,
            nocodb_base_url=(os.environ.get("NOCODB_BASE_URL") or "https://mpa.parvusmedia.com").strip().rstrip("/"),
            nocodb_api_token=(os.environ.get("NOCODB_API_TOKEN") or "").strip(),
            nocodb_table_id=(os.environ.get("CDE_SALESNAV_NOCODB_TABLE_ID") or DEFAULT_NOCODB_TABLE_ID).strip(),
            nocodb_ref_table_id=(os.environ.get("CDE_SALESNAV_NOCODB_REF_TABLE_ID") or DEFAULT_NOCODB_REF_TABLE_ID).strip(),
            nocodb_base_id=(os.environ.get("CDE_SALESNAV_NOCODB_BASE_ID") or DEFAULT_NOCODB_BASE_ID).strip(),
            campaign=(os.environ.get("CDE_SALESNAV_CAMPAIGN") or CAMPAIGN_TAG).strip(),
            product_url=(os.environ.get("CDE_SALESNAV_PRODUCT_URL") or PRODUCT_URL).strip(),
            min_employees=int(os.environ.get("CDE_SALESNAV_MIN_EMPLOYEES") or 11),
            require_premium=_truthy("CDE_SALESNAV_REQUIRE_PREMIUM", True),
        )
