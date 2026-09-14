"""ICP + runtime config for Reckitt CDE Sales Nav wave (Parvus Media)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PACKAGE_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
LEADS_PATH = DATA_DIR / "leads.json"
DEFAULT_CSV_NAME = "tsk_fb6268304961e568.csv"
DEFAULT_CDE_TASK_ID = "tsk_fb6268304961e568"

NOCODB_DEFAULT_BASE_URL = "https://mpa.parvusmedia.com"
CAMPAIGN_TAG = "reckitt_cde_dfm_en"
CAMPAIGN_NAME = "CDE · Reckitt SN list · Data for Media · EN"

# CDE panel Unipile seat for emiliano@parvusmedia.com (wallet em_be8a…).
# Never fall back to /etc/linkedinreport UNIPILE_ACCOUNT_ID (other wallets).
EMILIANO_CDE_UNIPILE_ACCOUNT_ID = "HlXTa367TJC_K0ciG22YGQ"
BLOCKED_UNIPILE_ACCOUNT_IDS = frozenset(
    {
        "rq1lQcYTToC9hlWD4vO94g",  # NextConvers / CDE-salesnav shared seat
    }
)

UNIPILE_DAILY_CAP = 10
UNIPILE_NOTE_MAX_CHARS = 300
DEFAULT_COMPANY_DOMAIN = "reckitt.com"

INVITE_NOTE_EN = (
    "Hi {first_name} — Emiliano, Parvus Media. We helped Reckitt Spain plan the next "
    "7 days of media using weather + Google Trends in real time (demand by region). "
    "Happy to share how."
)


def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    raw = _env(key).lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass
class ReckittConfig:
    dry_run: bool = True
    smartlead_enabled: bool = False
    unipile_daily_cap: int = UNIPILE_DAILY_CAP
    csv_path: str = ""
    cde_task_id: str = DEFAULT_CDE_TASK_ID
    icypeas_api_key: str = ""
    unipile_base_url: str = ""
    unipile_api_key: str = ""
    unipile_account_id: str = ""
    smartlead_api_key: str = ""
    smartlead_campaign_id: str = ""
    smartlead_email_account_id: int | None = None
    nocodb_base_url: str = NOCODB_DEFAULT_BASE_URL
    nocodb_api_token: str = ""
    linkedinreport_root: str = "/opt/apps/linkedinreport"

    @classmethod
    def from_env(cls) -> "ReckittConfig":
        account = _env("SMARTLEAD_RECKITT_EMAIL_ACCOUNT_ID") or _env("SMARTLEAD_EMAIL_ACCOUNT_ID")
        csv_path = _env("RECKITT_CSV_PATH")
        if not csv_path:
            csv_path = str(DATA_DIR / DEFAULT_CSV_NAME)
        unipile_account = _env("RECKITT_UNIPILE_ACCOUNT_ID") or EMILIANO_CDE_UNIPILE_ACCOUNT_ID
        return cls(
            dry_run=_env_bool("RECKITT_DRY_RUN", True),
            smartlead_enabled=_env_bool("RECKITT_SMARTLEAD_ENABLED", False),
            unipile_daily_cap=_env_int("RECKITT_UNIPILE_DAILY_CAP", UNIPILE_DAILY_CAP),
            csv_path=csv_path,
            cde_task_id=_env("RECKITT_CDE_TASK_ID", DEFAULT_CDE_TASK_ID),
            icypeas_api_key=_env("ICYPEAS_API_KEY"),
            unipile_base_url=_env("UNIPILE_BASE_URL"),
            unipile_api_key=_env("UNIPILE_API_KEY"),
            unipile_account_id=unipile_account,
            smartlead_api_key=_env("SMARTLEAD_RECKITT_API_KEY")
            or _env("SMARTLEAD_DFM_API_KEY")
            or _env("SMARTLEAD_API_KEY"),
            smartlead_campaign_id=_env("SMARTLEAD_RECKITT_CAMPAIGN_ID"),
            smartlead_email_account_id=int(account) if account.isdigit() else None,
            nocodb_base_url=_env("NOCODB_BASE_URL", NOCODB_DEFAULT_BASE_URL).rstrip("/"),
            nocodb_api_token=_env("NOCODB_API_TOKEN"),
            linkedinreport_root=_env("LINKEDINREPORT_ROOT", "/opt/apps/linkedinreport"),
        )

    def assert_unipile_seat(self) -> None:
        aid = (self.unipile_account_id or "").strip()
        if aid in BLOCKED_UNIPILE_ACCOUNT_IDS:
            raise RuntimeError(
                "Refusing Unipile account: that seat belongs to another wallet "
                "(NextConvers / CDE-salesnav). Set RECKITT_UNIPILE_ACCOUNT_ID to "
                "emiliano@parvusmedia.com CDE panel seat."
            )

    def summary(self) -> dict:
        csv_file = Path(self.csv_path)
        return {
            "product": "Data for Media — Reckitt Spain 7-day weather + Google Trends planning",
            "campaign_name": CAMPAIGN_NAME,
            "campaign_tag": CAMPAIGN_TAG,
            "cde_task_id": self.cde_task_id,
            "csv_path": self.csv_path,
            "csv_exists": csv_file.is_file(),
            "leads_store": str(LEADS_PATH),
            "leads_store_exists": LEADS_PATH.is_file(),
            "dry_run": self.dry_run,
            "smartlead_enabled": self.smartlead_enabled,
            "smartlead_campaign_configured": bool(self.smartlead_campaign_id),
            "smartlead_email_account_configured": self.smartlead_email_account_id is not None,
            "unipile_daily_cap": self.unipile_daily_cap,
            "unipile_account_id": self.unipile_account_id,
            "unipile_seat_is_emiliano_cde": self.unipile_account_id == EMILIANO_CDE_UNIPILE_ACCOUNT_ID,
            "icypeas_configured": bool(self.icypeas_api_key),
            "unipile_configured": bool(self.unipile_api_key and self.unipile_base_url),
            "nocodb_configured": bool(self.nocodb_api_token),
            "smartlead_configured": bool(self.smartlead_api_key),
        }


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_dotenv_files() -> None:
    candidates = [
        Path("/etc/linkedinreport/app.env"),
        Path("/opt/apps/nextconvers-qualification-gate/config/deployment.local.env"),
        PACKAGE_ROOT / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                if key and key not in os.environ:
                    os.environ[key] = val
        except OSError:
            continue
