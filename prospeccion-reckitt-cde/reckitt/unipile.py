"""Unipile LinkedIn invites gated by NocoDB automation_limits + action_log."""

from __future__ import annotations

import json
import logging
import random
import re
import time
from typing import Any

from . import automation_limits as limits
from .config import INVITE_NOTE_EN, UNIPILE_NOTE_MAX_CHARS, ReckittConfig
from .csv_leads import normalize_linkedin_url
from .messages import build_connection_message

logger = logging.getLogger(__name__)

_PROFILE_RE = re.compile(r"linkedin\.com/in/([^/?#]+)", re.I)


def render_invite_note(
    *,
    first_name: str,
    company: str = "",
    stored_note: str = "",
    max_chars: int = UNIPILE_NOTE_MAX_CHARS,
) -> str:
    stored = (stored_note or "").strip()
    if stored:
        note = stored
    else:
        name = (first_name or "").strip() or "there"
        note = INVITE_NOTE_EN.replace("{first_name}", name).replace("{company}", company or "")
    if len(note) > max_chars:
        note = note[: max_chars - 1].rstrip() + "…"
    return note


def _public_id(linkedin_url: str) -> str | None:
    cleaned = normalize_linkedin_url(linkedin_url) or linkedin_url
    match = _PROFILE_RE.search(cleaned or "")
    return match.group(1).strip().strip("/") if match else None


def _is_already_invited(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    return any(
        needle in hay
        for needle in (
            "already_invited_recently",
            "already_invited",
            "should delay new invitation",
            "invitation has already been sent",
        )
    )


def _is_invalid_provider(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    return http_status == 400 and (
        "user id does not match" in hay or "does not match provider" in hay
    )


def _is_provider_limit(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    if _is_already_invited(http_status, err_text):
        return False
    if http_status == 422 and ("cannot_resend" in hay or "limit" in hay and "invit" in hay):
        return True
    if http_status == 429:
        return True
    return "rate limit" in hay or "too many" in hay or "throttl" in hay


def send_invite(
    *,
    cfg: ReckittConfig,
    linkedin_url: str,
    first_name: str = "",
    company_name: str = "",
    dedupe_key: str = "",
    source_row_id: str = "",
    connection_message: str = "",
    dry_run: bool | None = None,
    sleep_before: bool = True,
) -> dict[str, Any]:
    import httpx

    cfg.assert_unipile_seat()
    dry = cfg.dry_run if dry_run is None else dry_run
    url = normalize_linkedin_url(linkedin_url) or (linkedin_url or "").strip()
    if not url:
        return {"ok": False, "skipped": True, "reason": "missing_linkedin_url"}

    try:
        rule = limits.fetch_limit_rule(cfg=cfg)
        gate = limits.check_invite_gate(cfg=cfg, rule=rule)
    except Exception as exc:
        logger.exception("automation_limits gate failed")
        return {"ok": False, "skipped": True, "reason": "limits_unavailable", "error": str(exc)}

    if not gate.ok:
        if not dry:
            limits.log_action(
                cfg=cfg,
                rule=rule,
                status="limit_reached",
                target_url=url,
                source_row_id=source_row_id or dedupe_key,
                error_message=f"{gate.reason}: workflow {gate.daily_count}/{rule.daily_limit}, "
                f"account {gate.account_count}, hour {gate.hourly_count}",
            )
        return {
            "ok": False,
            "skipped": True,
            "reason": gate.reason,
            "daily_count": gate.daily_count,
            "hourly_count": gate.hourly_count,
            "account_count": gate.account_count,
            "daily_limit": rule.daily_limit,
            "remaining_today": gate.remaining_today,
        }

    note = render_invite_note(
        first_name=first_name,
        company=company_name,
        stored_note=connection_message,
    )
    public_id = _public_id(url)
    wait_s = random.randint(rule.min_wait_seconds, max(rule.min_wait_seconds, rule.max_wait_seconds))

    if dry:
        return {
            "ok": True,
            "dry_run": True,
            "note": note,
            "wait_seconds": wait_s,
            "remaining_today": gate.remaining_today,
            "daily_limit": rule.daily_limit,
            "payload": {
                "provider_public_id": public_id,
                "message": note,
                "account_id": cfg.unipile_account_id,
            },
        }

    if not (cfg.unipile_api_key and cfg.unipile_base_url and cfg.unipile_account_id):
        return {"ok": False, "skipped": True, "reason": "missing_unipile_config"}

    if sleep_before and wait_s > 0:
        time.sleep(wait_s)

    headers = {
        "X-API-KEY": cfg.unipile_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    base = cfg.unipile_base_url.rstrip("/")
    provider_id = None
    try:
        if public_id:
            lookup = httpx.get(
                f"{base}/users/{public_id}",
                params={"account_id": cfg.unipile_account_id},
                headers=headers,
                timeout=45,
            )
            if lookup.status_code < 400:
                body = lookup.json() if lookup.content else {}
                provider_id = body.get("provider_id") or body.get("id")
    except Exception:
        logger.exception("unipile user lookup failed")

    try:
        if hasattr(limits, "has_resolved_invite") and limits.has_resolved_invite(
            cfg=cfg,
            target_ids=[str(provider_id or ""), str(public_id or "")],
            source_row_id=source_row_id or dedupe_key,
        ):
            return {
                "ok": True,
                "skipped": True,
                "reason": "already_invited_recently",
                "status": "already_resolved",
            }
    except Exception:
        logger.exception("resolved invite lookup failed")

    invite_body: dict[str, Any] = {
        "account_id": cfg.unipile_account_id,
        "message": note,
    }
    if provider_id:
        invite_body["provider_id"] = provider_id
    elif public_id:
        invite_body["provider_public_id"] = public_id
    else:
        return {"ok": False, "skipped": True, "reason": "missing_provider_id"}

    try:
        resp = httpx.post(f"{base}/users/invite", headers=headers, json=invite_body, timeout=45)
        text = resp.text or ""
        if resp.status_code >= 400:
            target = str(provider_id or public_id or "")
            src = source_row_id or dedupe_key
            if _is_already_invited(resp.status_code, text):
                limits.log_action(
                    cfg=cfg,
                    rule=rule,
                    status="skipped",
                    target_id=target,
                    target_url=url,
                    source_row_id=src,
                    http_status=resp.status_code,
                    error_code="already_invited_recently",
                    error_message=text[:800],
                    request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
                )
                return {
                    "ok": True,
                    "skipped": True,
                    "reason": "already_invited_recently",
                    "http_status": resp.status_code,
                    "status": "already_invited",
                }
            if _is_invalid_provider(resp.status_code, text):
                limits.log_action(
                    cfg=cfg,
                    rule=rule,
                    status="skipped",
                    target_id=target,
                    target_url=url,
                    source_row_id=src,
                    http_status=resp.status_code,
                    error_code="invalid_provider_id",
                    error_message=text[:800],
                    request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
                )
                return {
                    "ok": True,
                    "skipped": True,
                    "reason": "invalid_provider_id",
                    "http_status": resp.status_code,
                    "status": "invalid_provider",
                }
            limits.log_action(
                cfg=cfg,
                rule=rule,
                status="failed",
                target_id=target,
                target_url=url,
                source_row_id=src,
                http_status=resp.status_code,
                error_message=text[:800],
                request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
            )
            if _is_provider_limit(resp.status_code, text):
                try:
                    limits.pause_account(cfg=cfg, rule=rule, reason=f"provider_limit http={resp.status_code}")
                except Exception:
                    logger.exception("pause_account failed")
                return {
                    "ok": False,
                    "skipped": True,
                    "reason": "provider_limit",
                    "http_status": resp.status_code,
                    "error": text[:500],
                }
            return {
                "ok": False,
                "error": text[:500],
                "http_status": resp.status_code,
            }

        limits.log_action(
            cfg=cfg,
            rule=rule,
            status="success",
            target_id=str(provider_id or public_id or ""),
            target_url=url,
            source_row_id=source_row_id or dedupe_key,
            http_status=resp.status_code,
            response_payload=(resp.text or "")[:1500],
        )
        return {
            "ok": True,
            "status": "sent",
            "note": note,
            "wait_seconds": wait_s,
            "response": resp.json() if resp.content else {},
        }
    except Exception as exc:
        logger.exception("unipile invite failed")
        limits.log_action(
            cfg=cfg,
            rule=rule,
            status="failed",
            target_id=str(provider_id or public_id or ""),
            target_url=url,
            source_row_id=source_row_id or dedupe_key,
            error_message=str(exc)[:800],
        )
        return {"ok": False, "error": str(exc)}


# Keep a named export used by compose-messages dry-run previews.
__all__ = ["send_invite", "render_invite_note", "build_connection_message"]
