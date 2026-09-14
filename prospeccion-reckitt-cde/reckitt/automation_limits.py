"""NocoDB automation_limits + automation_action_log (same contract as n8n Unipile workflows)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from .config import ReckittConfig

logger = logging.getLogger(__name__)

LIMITS_TABLE_ID = "mciyo827yef4yk5"
ACTION_LOG_TABLE_ID = "mivkthw53zxy55k"

WORKFLOW_NAME = "reckitt_cde_unipile_connection_invites"
CLIENT_NAME = "ParvusMediaReckittCDE"
PROVIDER = "unipile"
ACTION_TYPE = "linkedin_connection_invite"
ACCOUNT_LABEL = "CDE panel LinkedIn (emiliano@parvusmedia.com)"

# Statuses that consume daily/hourly quota (n8n contract)
_COUNT_STATUSES = ("attempted", "success", "failed")


@dataclass
class LimitRule:
    record_id: int | None
    account_id: str
    account_label: str
    client_name: str
    workflow_name: str
    limit_key: str
    daily_limit: int
    hourly_limit: int | None
    min_wait_seconds: int
    max_wait_seconds: int
    timezone: str
    reset_hour: int
    hard_stop_on_limit: bool
    pause_hours: int
    paused_until: str | None
    pause_reason: str | None
    enabled: bool

    @property
    def account_is_paused(self) -> bool:
        if not self.paused_until:
            return False
        try:
            raw = self.paused_until.replace("Z", "+00:00")
            until = datetime.fromisoformat(raw)
            if until.tzinfo is None:
                until = until.replace(tzinfo=timezone.utc)
            return until > datetime.now(timezone.utc)
        except ValueError:
            return False


def _headers(cfg: ReckittConfig) -> dict[str, str]:
    return {
        "xc-token": cfg.nocodb_api_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def action_date_for_rule(rule: LimitRule, *, now: datetime | None = None) -> str:
    tz = ZoneInfo(rule.timezone or "Europe/Madrid")
    now = now or datetime.now(tz)
    local = now.astimezone(tz)
    if local.hour < int(rule.reset_hour or 0):
        local = local - timedelta(days=1)
    return local.strftime("%Y-%m-%d")


def limit_key_for(*, account_id: str, workflow_name: str = WORKFLOW_NAME) -> str:
    return f"{account_id}__{PROVIDER}__{ACTION_TYPE}__{workflow_name}"


def ensure_reckitt_limit_row(*, cfg: ReckittConfig) -> LimitRule:
    """Create or return the Alarmas connection-invite rule (daily_limit from config)."""
    account_id = (cfg.unipile_account_id or "").strip()
    if not account_id:
        raise RuntimeError("UNIPILE_ACCOUNT_ID missing")
    if not cfg.nocodb_api_token:
        raise RuntimeError("NOCODB_API_TOKEN missing")

    where = (
        f"(workflow_name,eq,{WORKFLOW_NAME})~and"
        f"(provider,eq,{PROVIDER})~and"
        f"(action_type,eq,{ACTION_TYPE})"
    )
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/tables/{LIMITS_TABLE_ID}/records",
        params={"where": where, "limit": 1},
        headers=_headers(cfg),
        timeout=30,
    )
    resp.raise_for_status()
    rows = (resp.json() or {}).get("list") or []
    daily = int(cfg.unipile_daily_cap)
    if rows:
        row = rows[0]
        # Keep NocoDB as source of truth; only fill missing account_id
        if not row.get("account_id"):
            httpx.patch(
                f"{cfg.nocodb_base_url}/api/v2/tables/{LIMITS_TABLE_ID}/records",
                headers=_headers(cfg),
                json={"Id": row["Id"], "account_id": account_id},
                timeout=30,
            ).raise_for_status()
            row["account_id"] = account_id
        return _rule_from_row(row, fallback_account=account_id, fallback_daily=daily)

    payload = {
        "enabled": True,
        "client_name": CLIENT_NAME,
        "workflow_name": WORKFLOW_NAME,
        "account_id": account_id,
        "account_label": ACCOUNT_LABEL,
        "provider": PROVIDER,
        "action_type": ACTION_TYPE,
        "daily_limit": daily,
        "hourly_limit": 3,
        "min_wait_seconds": 10,
        "max_wait_seconds": 45,
        "timezone": "Europe/Madrid",
        "reset_hour": 0,
        "priority": 100,
        "hard_stop_on_limit": True,
        "notes": (
            "Reckitt CDE Unipile connection invites. Seat is Emiliano CDE panel "
            "(emiliano@parvusmedia.com); do not share with NextConvers / other wallets."
        ),
        "limit_key": limit_key_for(account_id=account_id),
        "pause_hours": 24,
        "paused_until": None,
        "pause_reason": None,
    }
    # limit_key is a NocoDB formula — do not POST it
    payload.pop("limit_key", None)
    payload = {k: v for k, v in payload.items() if v is not None}
    created = httpx.post(
        f"{cfg.nocodb_base_url}/api/v2/tables/{LIMITS_TABLE_ID}/records",
        headers=_headers(cfg),
        json=payload,
        timeout=45,
    )
    created.raise_for_status()
    body = created.json() if created.content else payload
    if isinstance(body, dict) and body.get("Id") is None:
        body = {**payload, "Id": body.get("id")}
    return _rule_from_row(body if isinstance(body, dict) else payload, fallback_account=account_id, fallback_daily=daily)


def _rule_from_row(row: dict[str, Any], *, fallback_account: str, fallback_daily: int) -> LimitRule:
    account_id = (row.get("account_id") or fallback_account or "").strip()
    workflow = (row.get("workflow_name") or WORKFLOW_NAME).strip()
    return LimitRule(
        record_id=row.get("Id"),
        account_id=account_id,
        account_label=(row.get("account_label") or ACCOUNT_LABEL) or "",
        client_name=(row.get("client_name") or CLIENT_NAME) or CLIENT_NAME,
        workflow_name=workflow,
        limit_key=(row.get("limit_key") or limit_key_for(account_id=account_id, workflow_name=workflow)),
        daily_limit=int(row.get("daily_limit") if row.get("daily_limit") is not None else fallback_daily),
        hourly_limit=int(row["hourly_limit"]) if row.get("hourly_limit") is not None else None,
        min_wait_seconds=int(row.get("min_wait_seconds") or 10),
        max_wait_seconds=int(row.get("max_wait_seconds") or 45),
        timezone=(row.get("timezone") or "Europe/Madrid"),
        reset_hour=int(row.get("reset_hour") or 0),
        hard_stop_on_limit=row.get("hard_stop_on_limit") is not False,
        pause_hours=int(row.get("pause_hours") or 24),
        paused_until=row.get("paused_until"),
        pause_reason=row.get("pause_reason"),
        enabled=bool(row.get("enabled", True)),
    )


def fetch_limit_rule(*, cfg: ReckittConfig) -> LimitRule:
    return ensure_reckitt_limit_row(cfg=cfg)



def has_resolved_invite(
    *,
    cfg,
    target_ids: list[str] | None = None,
    source_row_id: str = "",
) -> bool:
    """True if this person/row already succeeded or was skipped (do not resend)."""
    for tid in [str(t).strip() for t in (target_ids or []) if str(t).strip()]:
        where = f"(target_id,eq,{tid})~and(status,in,success,skipped)"
        if _count_logs(cfg=cfg, where=where) > 0:
            return True
    src = str(source_row_id or "").strip()
    if src:
        where = f"(source_row_id,eq,{src})~and(status,in,success,skipped)"
        if _count_logs(cfg=cfg, where=where) > 0:
            return True
    return False


def _count_logs(
    *,
    cfg: ReckittConfig,
    where: str,
) -> int:
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/tables/{ACTION_LOG_TABLE_ID}/records",
        params={"where": where, "fields": "Id,status", "limit": 1},
        headers=_headers(cfg),
        timeout=30,
    )
    resp.raise_for_status()
    info = (resp.json() or {}).get("pageInfo") or {}
    return int(info.get("totalRows") or 0)


def _list_logs(*, cfg: ReckittConfig, where: str, limit: int = 200) -> list[dict[str, Any]]:
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/tables/{ACTION_LOG_TABLE_ID}/records",
        params={"where": where, "limit": limit, "sort": "-CreatedAt"},
        headers=_headers(cfg),
        timeout=30,
    )
    resp.raise_for_status()
    rows = (resp.json() or {}).get("list") or []
    return [r for r in rows if isinstance(r, dict)]


def count_today_for_limit(*, cfg: ReckittConfig, rule: LimitRule) -> int:
    action_date = action_date_for_rule(rule)
    status_in = ",".join(_COUNT_STATUSES)
    where = (
        f"(limit_key,eq,{rule.limit_key})~and"
        f"(action_date,eq,exactDate,{action_date})~and"
        f"(status,in,{status_in})"
    )
    return _count_logs(cfg=cfg, where=where)


def count_hour_for_limit(*, cfg: ReckittConfig, rule: LimitRule) -> int:
    """Count quota-consuming events in the last 60 minutes for this limit_key."""
    action_date = action_date_for_rule(rule)
    status_in = ",".join(_COUNT_STATUSES)
    where = (
        f"(limit_key,eq,{rule.limit_key})~and"
        f"(action_date,eq,exactDate,{action_date})~and"
        f"(status,in,{status_in})"
    )
    rows = _list_logs(cfg=cfg, where=where, limit=200)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    n = 0
    for r in rows:
        raw = r.get("timestamp") or r.get("CreatedAt") or ""
        try:
            ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00").replace(" ", "T", 1))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                n += 1
        except ValueError:
            continue
    return n


def count_account_today(*, cfg: ReckittConfig, rule: LimitRule) -> int:
    """All connection invites today on the shared LinkedIn account (any workflow)."""
    action_date = action_date_for_rule(rule)
    status_in = ",".join(_COUNT_STATUSES)
    where = (
        f"(account_id,eq,{rule.account_id})~and"
        f"(action_type,eq,{ACTION_TYPE})~and"
        f"(action_date,eq,exactDate,{action_date})~and"
        f"(status,in,{status_in})"
    )
    return _count_logs(cfg=cfg, where=where)


def account_daily_ceiling(*, cfg: ReckittConfig, account_id: str) -> int:
    """Max daily_limit among enabled invite rules for this account (incl. Alarmas)."""
    where = (
        f"(account_id,eq,{account_id})~and"
        f"(provider,eq,{PROVIDER})~and"
        f"(action_type,eq,{ACTION_TYPE})~and"
        f"(enabled,eq,true)"
    )
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/tables/{LIMITS_TABLE_ID}/records",
        params={"where": where, "limit": 50},
        headers=_headers(cfg),
        timeout=30,
    )
    resp.raise_for_status()
    rows = (resp.json() or {}).get("list") or []
    limits = [int(r.get("daily_limit") or 0) for r in rows if r.get("daily_limit") is not None]
    return max(limits) if limits else 15


@dataclass
class GateDecision:
    ok: bool
    reason: str
    rule: LimitRule
    action_date: str
    daily_count: int
    hourly_count: int
    account_count: int
    remaining_today: int


def check_invite_gate(*, cfg: ReckittConfig, rule: LimitRule | None = None) -> GateDecision:
    rule = rule or fetch_limit_rule(cfg=cfg)
    action_date = action_date_for_rule(rule)
    daily_count = count_today_for_limit(cfg=cfg, rule=rule)
    hourly_count = count_hour_for_limit(cfg=cfg, rule=rule) if rule.hourly_limit else 0
    account_count = count_account_today(cfg=cfg, rule=rule)
    ceiling = account_daily_ceiling(cfg=cfg, account_id=rule.account_id)
    remaining_workflow = max(0, rule.daily_limit - daily_count)
    remaining_account = max(0, ceiling - account_count)
    remaining = min(remaining_workflow, remaining_account)

    def deny(reason: str) -> GateDecision:
        return GateDecision(
            ok=False,
            reason=reason,
            rule=rule,
            action_date=action_date,
            daily_count=daily_count,
            hourly_count=hourly_count,
            account_count=account_count,
            remaining_today=0,
        )

    if not rule.enabled:
        return deny("limit_disabled")
    if rule.account_is_paused:
        return deny("account_paused")
    if rule.hard_stop_on_limit and daily_count >= rule.daily_limit:
        return deny("daily_limit_reached")
    if rule.hourly_limit is not None and hourly_count >= rule.hourly_limit:
        return deny("hourly_limit_reached")
    if account_count >= ceiling:
        return deny("account_shared_daily_ceiling")
    return GateDecision(
        ok=True,
        reason="ok",
        rule=rule,
        action_date=action_date,
        daily_count=daily_count,
        hourly_count=hourly_count,
        account_count=account_count,
        remaining_today=remaining,
    )


def log_action(
    *,
    cfg: ReckittConfig,
    rule: LimitRule,
    status: str,
    target_id: str = "",
    target_url: str = "",
    source_row_id: str = "",
    error_message: str | None = None,
    http_status: int | None = None,
    error_code: str | None = None,
    request_payload: str | None = None,
    response_payload: str | None = None,
    execution_id: str = "reckitt-cde-cli",
) -> dict[str, Any]:
    action_date = action_date_for_rule(rule)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload: dict[str, Any] = {
        "timestamp": now,
        "action_date": action_date,
        "client_name": rule.client_name,
        "workflow_name": rule.workflow_name,
        "execution_id": execution_id,
        "account_id": rule.account_id,
        "account_label": rule.account_label,
        "provider": PROVIDER,
        "action_type": ACTION_TYPE,
        "target_id": target_id or "",
        "target_url": target_url or "",
        "source_row_id": str(source_row_id or ""),
        "status": status,
        "limit_key": rule.limit_key,
    }
    if error_message:
        payload["error_message"] = error_message
    if http_status is not None:
        payload["http_status"] = http_status
    if error_code:
        payload["error_code"] = error_code
    if request_payload:
        payload["request_payload"] = request_payload
    if response_payload:
        payload["response_payload"] = response_payload
    try:
        resp = httpx.post(
            f"{cfg.nocodb_base_url}/api/v2/tables/{ACTION_LOG_TABLE_ID}/records",
            headers=_headers(cfg),
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        return {"ok": True, "status": status}
    except Exception as exc:
        logger.exception("failed to write automation_action_log")
        return {"ok": False, "error": str(exc)}


def pause_account(*, cfg: ReckittConfig, rule: LimitRule, reason: str) -> None:
    if not rule.record_id:
        return
    until = datetime.now(timezone.utc) + timedelta(hours=max(1, rule.pause_hours))
    httpx.patch(
        f"{cfg.nocodb_base_url}/api/v2/tables/{LIMITS_TABLE_ID}/records",
        headers=_headers(cfg),
        json={
            "Id": rule.record_id,
            "paused_until": until.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "pause_reason": reason[:500],
        },
        timeout=30,
    ).raise_for_status()
