"""Smartlead enroll — Reckitt CDE Data for Media sequence (EN).

Do not activate sending or bulk enroll until explicit copy OK
(RECKITT_SMARTLEAD_ENABLED=true + campaign START). Campaign stays PAUSED at create.
"""

from __future__ import annotations

import logging
from typing import Any

from .config import CAMPAIGN_NAME, CAMPAIGN_TAG, ReckittConfig

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (compatible; ProspeccionReckittCDE/0.1)"


def _html(paragraphs: list[str]) -> str:
    parts = [
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.55;color:#0b1220;max-width:560px">'
    ]
    for paragraph in paragraphs:
        parts.append(f'<p style="margin:0 0 14px 0;font-size:14px;line-height:1.55">{paragraph}</p>')
    parts.append("</div>")
    return "".join(parts)


EMAIL_SIGNATURE = (
    "--<br>"
    "Emiliano Tichauer<br>"
    "Managing Partner | Parvusmedia<br>"
    "<br>"
    "--------------------------------------------------------------------------<br>"
    "📞 M: +34 664331172<br>"
    '📧 E: <a href="mailto:emiliano@parvusmedia.com">emiliano@parvusmedia.com</a><br>'
    '🔗 W: <a href="https://parvusmedia.com">parvusmedia.com</a><br>'
    "📍 Madrid | Dubai<br>"
    "--------------------------------------------------------------------------<br>"
    "<br>"
    "<br>"
    '<span style="font-size:11px;line-height:1.45;color:#555555">'
    "Data Protection Notice: This email and any attached files may contain confidential "
    "information and/or information protected by privacy rights. It is intended solely for "
    "the individual or entity to whom it has been sent. If you have received this email by "
    "mistake, please notify the sender and delete the email and any attached files from your "
    "system. Any unauthorized disclosure, copying, distribution, or use of the information "
    "contained in this email is prohibited."
    "</span><br>"
    "<br>"
    "********************************************"
)

EMAIL_1_SUBJECT = "{{company_name}} — 7-day media planning from weather + search demand"
EMAIL_1_BODY = _html(
    [
        "Hi {{first_name}}, I hope this finds you well.",
        "I'm Emiliano from Parvus Media. We recently helped Reckitt in Spain plan media for the next 7 days by connecting campaigns to weather and Google Trends in real time — so the team knew which region demand was about to land in, and could activate accordingly.",
        "The loop is straightforward: live weather + search demand → regional forecast for the coming week → media plan and activation where the demand will actually be.",
        "If you own media, digital, or performance at Reckitt, I'd like 20 minutes to show you how that planning loop worked and whether a similar setup would help {{company_name}} in your market.",
        "Would next week work for a short call?",
        f"Best regards,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_2_SUBJECT = "Re: {{company_name}} — 7-day media planning from weather + search demand"
EMAIL_2_BODY = _html(
    [
        "Hi {{first_name}}, circling back in case my previous note got buried.",
        "Happy to share a concrete walkthrough of the Reckitt Spain setup: how weather and Google Trends fed a rolling 7-day media plan, and how that translated into regional activation.",
        "If 20 minutes would be useful for {{company_name}}, tell me a couple of slots that work and I'll send a calendar invite.",
        f"Thank you,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_3_SUBJECT = "Re: {{company_name}} — closing the thread"
EMAIL_3_BODY = _html(
    [
        "Hi {{first_name}}, I'll close this thread on my side so I'm not adding noise.",
        "If someone else on the Reckitt media / performance team should see this, I'm happy to reach out — just point me in the right direction.",
        f"All the best,<br><br>{EMAIL_SIGNATURE}",
    ]
)


def campaign_sequence_spec() -> dict[str, Any]:
    return {
        "name": CAMPAIGN_NAME,
        "max_emails": 3,
        "stop_on_reply": True,
        "tone": "professional-EN",
        "language": "en",
        "status_at_create": "PAUSED",
        "steps": [
            {"step": 1, "delay_days": 0, "subject": EMAIL_1_SUBJECT, "body": EMAIL_1_BODY},
            {"step": 2, "delay_days": 3, "subject": EMAIL_2_SUBJECT, "body": EMAIL_2_BODY},
            {"step": 3, "delay_days": 4, "subject": EMAIL_3_SUBJECT, "body": EMAIL_3_BODY},
        ],
        "custom_fields": ["linkedin_url", "job_title", "reason_to_contact", "campaign", "location"],
    }


def sequences_payload() -> dict[str, Any]:
    return {
        "sequences": [
            {
                "seq_number": 1,
                "subject": EMAIL_1_SUBJECT,
                "email_body": EMAIL_1_BODY,
                "seq_delay_details": {"delay_in_days": 0},
            },
            {
                "seq_number": 2,
                "subject": EMAIL_2_SUBJECT,
                "email_body": EMAIL_2_BODY,
                "seq_delay_details": {"delay_in_days": 3},
            },
            {
                "seq_number": 3,
                "subject": EMAIL_3_SUBJECT,
                "email_body": EMAIL_3_BODY,
                "seq_delay_details": {"delay_in_days": 4},
            },
        ]
    }


def list_campaign_leads(*, cfg: ReckittConfig, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    import httpx

    camp = (cfg.smartlead_campaign_id or "").strip()
    if not camp or not cfg.smartlead_api_key:
        return []
    resp = httpx.get(
        f"https://server.smartlead.ai/api/v1/campaigns/{camp}/leads",
        params={"api_key": cfg.smartlead_api_key, "limit": limit, "offset": offset},
        headers={"User-Agent": _UA},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    rows = data.get("data") if isinstance(data, dict) else None
    return [x for x in (rows or []) if isinstance(x, dict)]


def list_blocked_leads(*, cfg: ReckittConfig, max_pages: int = 20) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    page = 100
    for _ in range(max_pages):
        batch = list_campaign_leads(cfg=cfg, limit=page, offset=offset)
        if not batch:
            break
        for row in batch:
            if (row.get("status") or "").upper() != "BLOCKED":
                continue
            lead = row.get("lead") if isinstance(row.get("lead"), dict) else {}
            email = (lead.get("email") or row.get("email") or "").strip().lower()
            out.append(
                {
                    "email": email,
                    "first_name": lead.get("first_name") or "",
                    "last_name": lead.get("last_name") or "",
                    "company_name": lead.get("company_name") or "",
                    "linkedin_url": lead.get("linkedin_profile")
                    or (lead.get("custom_fields") or {}).get("linkedin_url")
                    or "",
                    "campaign_lead_map_id": row.get("campaign_lead_map_id") or row.get("id"),
                    "smartlead_status": "BLOCKED",
                }
            )
        if len(batch) < page:
            break
        offset += page
    return out


def set_campaign_status(*, cfg: ReckittConfig, status: str = "PAUSED") -> dict[str, Any]:
    import httpx

    camp = (cfg.smartlead_campaign_id or "").strip()
    if not camp:
        return {"ok": False, "error": "missing_smartlead_campaign_id"}
    if not cfg.smartlead_api_key:
        return {"ok": False, "error": "missing_smartlead_api_key"}
    try:
        resp = httpx.post(
            f"https://server.smartlead.ai/api/v1/campaigns/{camp}/status",
            params={"api_key": cfg.smartlead_api_key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json={"status": status},
            timeout=45,
        )
        resp.raise_for_status()
        detail = httpx.get(
            f"https://server.smartlead.ai/api/v1/campaigns/{camp}",
            params={"api_key": cfg.smartlead_api_key},
            headers={"User-Agent": _UA},
            timeout=45,
        )
        body = detail.json() if detail.content else {}
        return {
            "ok": True,
            "requested": status,
            "status": body.get("status"),
            "schedule_start_time": body.get("schedule_start_time"),
        }
    except Exception as exc:
        logger.exception("smartlead status update failed")
        return {"ok": False, "error": str(exc)}


def push_schedule(*, cfg: ReckittConfig, schedule_start_time: str | None = None) -> dict[str, Any]:
    import httpx

    camp = (cfg.smartlead_campaign_id or "").strip()
    if not camp or not cfg.smartlead_api_key:
        return {"ok": False, "error": "missing_campaign_or_key"}
    payload: dict[str, Any] = {
        "timezone": "Europe/Madrid",
        "days_of_the_week": [1, 2, 3, 4, 5],
        "start_hour": "09:00",
        "end_hour": "18:00",
        "min_time_btw_emails": 3,
        "max_new_leads_per_day": 20,
    }
    if schedule_start_time:
        payload["schedule_start_time"] = schedule_start_time
    try:
        resp = httpx.post(
            f"https://server.smartlead.ai/api/v1/campaigns/{camp}/schedule",
            params={"api_key": cfg.smartlead_api_key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        detail = httpx.get(
            f"https://server.smartlead.ai/api/v1/campaigns/{camp}",
            params={"api_key": cfg.smartlead_api_key},
            headers={"User-Agent": _UA},
            timeout=45,
        ).json()
        return {
            "ok": True,
            "schedule_start_time": detail.get("schedule_start_time"),
            "status": detail.get("status"),
            "scheduler_cron_value": detail.get("scheduler_cron_value"),
        }
    except Exception as exc:
        logger.exception("smartlead schedule update failed")
        return {"ok": False, "error": str(exc)}


def push_sequences(*, cfg: ReckittConfig | None = None, campaign_id: str | None = None) -> dict[str, Any]:
    import httpx

    cfg = cfg or ReckittConfig.from_env()
    camp = (campaign_id or cfg.smartlead_campaign_id or "").strip()
    if not camp:
        return {"ok": False, "error": "missing_smartlead_campaign_id"}
    if not cfg.smartlead_api_key:
        return {"ok": False, "error": "missing_smartlead_api_key"}

    payload = sequences_payload()
    try:
        resp = httpx.post(
            f"https://server.smartlead.ai/api/v1/campaigns/{camp}/sequences",
            params={"api_key": cfg.smartlead_api_key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        body = resp.json() if resp.content else {}
        return {
            "ok": True,
            "campaign_id": camp,
            "sequences": [
                {
                    "seq_number": step["seq_number"],
                    "subject": step["subject"],
                    "delay_days": step["seq_delay_details"]["delay_in_days"],
                }
                for step in payload["sequences"]
            ],
            "response": body,
        }
    except Exception as exc:
        logger.exception("smartlead push sequences failed")
        return {"ok": False, "campaign_id": camp, "error": str(exc)}


def enroll_lead(
    *,
    cfg: ReckittConfig,
    email: str,
    first_name: str,
    last_name: str = "",
    company_name: str = "",
    linkedin_url: str = "",
    job_title: str = "",
    location: str = "",
    reason_to_contact: str = "",
    dry_run: bool | None = None,
    campaign_id: str | None = None,
) -> dict[str, Any]:
    dry = cfg.dry_run if dry_run is None else dry_run
    if not getattr(cfg, "smartlead_enabled", False) and not dry:
        return {"ok": False, "skipped": True, "reason": "smartlead_disabled_awaiting_copy_ok"}

    email_clean = (email or "").strip().lower()
    camp = (campaign_id or cfg.smartlead_campaign_id or "").strip()
    if not email_clean or "@" not in email_clean:
        return {"ok": False, "skipped": True, "reason": "missing_email"}
    if not camp and not dry:
        return {"ok": False, "skipped": True, "reason": "missing_smartlead_campaign_id"}
    if not cfg.smartlead_api_key and not dry:
        return {"ok": False, "skipped": True, "reason": "missing_smartlead_api_key"}

    lead_payload = {
        "first_name": first_name or "",
        "last_name": last_name or "",
        "email": email_clean,
        "company_name": company_name or "",
        "linkedin_profile": linkedin_url or "",
        "custom_fields": {
            "job_title": job_title or "",
            "linkedin_url": linkedin_url or "",
            "reason_to_contact": reason_to_contact or "",
            "location": location or "",
            "campaign": CAMPAIGN_TAG,
        },
    }
    if dry:
        return {"ok": True, "dry_run": True, "lead": lead_payload, "campaign_id": camp or None}

    import httpx

    url = f"https://server.smartlead.ai/api/v1/campaigns/{camp}/leads"
    try:
        resp = httpx.post(
            url,
            params={"api_key": cfg.smartlead_api_key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json={"lead_list": [lead_payload]},
            timeout=45,
        )
        resp.raise_for_status()
        return {"ok": True, "status": "enrolled", "response": resp.json() if resp.content else {}}
    except Exception as exc:
        logger.exception("smartlead enroll failed")
        return {"ok": False, "error": str(exc)}
