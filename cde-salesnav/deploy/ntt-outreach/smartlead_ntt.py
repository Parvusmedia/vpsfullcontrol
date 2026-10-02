"""Smartlead campaigns for NTT DATA MarTech outreach (ES + EN, 7-day reminder)."""

from __future__ import annotations

import os
from typing import Any

from smartlead import (  # type: ignore[import-not-found]
    BASE,
    EMAIL_SIGNATURE,
    REMINDER_DELAY_DAYS,
    _UA,
    _html,
    smartlead_api_key,
    smartlead_email_account_ids,
)

CAMPAIGN_NAME_ES = "NTT DATA · MarTech · ES · tag:ntt_martech_es"
CAMPAIGN_NAME_EN = "NTT DATA · MarTech · EN · tag:ntt_martech_en"

ENV_CAMPAIGN_ES = "SMARTLEAD_NTT_ES_CAMPAIGN_ID"
ENV_CAMPAIGN_EN = "SMARTLEAD_NTT_EN_CAMPAIGN_ID"

EMAIL_1_SUBJECT_ES = "NTT DATA — Martech y marketing automation"
EMAIL_1_BODY_ES = _html(
    [
        "Hola {{first_name}}, encantado.",
        "Busco contactar con alguien de <b>NTT DATA</b> en Martech o marketing automation.",
        "Soy consultor externo y trabajo con agencias o consultoras. Me gustaría explorar colaborar en proyectos "
        "en NTT DATA. Tengo más de 20 años de experiencia entre gestión de proyectos e implementación "
        "(automatización, campañas, analítica, con y sin IA).",
        "¿Crees que podría haber encaje para colaborar, o te agradezco si me indicas a quién contactar?",
        f"Muchas gracias,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_2_SUBJECT_ES = "Re: NTT DATA — Martech y marketing automation"
EMAIL_2_BODY_ES = _html(
    [
        "Hola {{first_name}}, solo consultaré si pudiste ver mi correo anterior.",
        "Sigo interesado en explorar cómo podría colaborar en proyectos de Martech o marketing automation en "
        "<b>NTT DATA</b>, como consultor externo.",
        "Si no eres la persona adecuada, te agradezco mucho si me remites al equipo o persona correcta.",
        f"Muchas gracias,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_1_SUBJECT_EN = "NTT DATA — MarTech and marketing automation"
EMAIL_1_BODY_EN = _html(
    [
        "Hi {{first_name}}, nice to meet you.",
        "I'm looking to connect with someone at <b>NTT DATA</b> in MarTech or marketing automation.",
        "I'm an external consultant and work with agencies and consultancies. I'd like to explore collaborating "
        "on projects at NTT DATA. I have 20+ years of experience across project management and hands-on delivery "
        "(automation, campaigns, analytics, with and without AI).",
        "Do you think there could be a fit to collaborate, or could you point me to the right person to speak with?",
        f"Thank you,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_2_SUBJECT_EN = "Re: NTT DATA — MarTech and marketing automation"
EMAIL_2_BODY_EN = _html(
    [
        "Hi {{first_name}}, just checking whether you had a chance to see my previous email.",
        "I'm still interested in exploring how I could collaborate on MarTech or marketing automation projects at "
        "<b>NTT DATA</b> as an external consultant.",
        "If you're not the right person, I'd really appreciate a pointer to the right team or contact.",
        f"Thank you,<br><br>{EMAIL_SIGNATURE}",
    ]
)


def sequences_payload_es() -> dict[str, Any]:
    return {
        "sequences": [
            {
                "seq_number": 1,
                "subject": EMAIL_1_SUBJECT_ES,
                "email_body": EMAIL_1_BODY_ES,
                "seq_delay_details": {"delay_in_days": 0},
            },
            {
                "seq_number": 2,
                "subject": EMAIL_2_SUBJECT_ES,
                "email_body": EMAIL_2_BODY_ES,
                "seq_delay_details": {"delay_in_days": REMINDER_DELAY_DAYS},
            },
        ]
    }


def sequences_payload_en() -> dict[str, Any]:
    return {
        "sequences": [
            {
                "seq_number": 1,
                "subject": EMAIL_1_SUBJECT_EN,
                "email_body": EMAIL_1_BODY_EN,
                "seq_delay_details": {"delay_in_days": 0},
            },
            {
                "seq_number": 2,
                "subject": EMAIL_2_SUBJECT_EN,
                "email_body": EMAIL_2_BODY_EN,
                "seq_delay_details": {"delay_in_days": REMINDER_DELAY_DAYS},
            },
        ]
    }


def campaign_id_for_locale(locale: str) -> str:
    loc = (locale or "en").strip().lower()
    if loc == "es":
        return os.environ.get(ENV_CAMPAIGN_ES, "").strip()
    return os.environ.get(ENV_CAMPAIGN_EN, "").strip()


def create_campaign(*, locale: str) -> dict[str, Any]:
    import httpx

    key = smartlead_api_key()
    if not key:
        raise RuntimeError("Missing Smartlead API key")

    name = CAMPAIGN_NAME_ES if locale == "es" else CAMPAIGN_NAME_EN
    payload = sequences_payload_es() if locale == "es" else sequences_payload_en()
    schedule_tz = "Europe/Madrid" if locale == "es" else "Europe/London"

    create = httpx.post(
        f"{BASE}/campaigns/create",
        params={"api_key": key},
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
        json={"name": name},
        timeout=45,
    )
    create.raise_for_status()
    body = create.json() if create.content else {}
    campaign_id = body.get("id") or body.get("campaign_id")
    if not campaign_id:
        raise RuntimeError(f"create failed: {body}")
    campaign_id = int(campaign_id)

    httpx.post(
        f"{BASE}/campaigns/{campaign_id}/sequences",
        params={"api_key": key},
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    ).raise_for_status()

    schedule = {
        "timezone": schedule_tz,
        "days_of_the_week": [1, 2, 3, 4, 5],
        "start_hour": "09:00",
        "end_hour": "18:00",
        "min_time_btw_emails": 15,
        "max_new_leads_per_day": 20,
    }
    try:
        httpx.post(
            f"{BASE}/campaigns/{campaign_id}/schedule",
            params={"api_key": key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json=schedule,
            timeout=45,
        ).raise_for_status()
    except Exception as exc:
        print(f"schedule warning ({locale}): {exc}")

    accounts = smartlead_email_account_ids()
    if accounts:
        try:
            httpx.post(
                f"{BASE}/campaigns/{campaign_id}/email-accounts",
                params={"api_key": key},
                headers={"User-Agent": _UA, "Content-Type": "application/json"},
                json={"email_account_ids": accounts},
                timeout=45,
            ).raise_for_status()
        except Exception as exc:
            print(f"email-accounts warning ({locale}): {exc}")

    httpx.post(
        f"{BASE}/campaigns/{campaign_id}/status",
        params={"api_key": key},
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
        json={"status": "PAUSED"},
        timeout=45,
    ).raise_for_status()

    env_key = ENV_CAMPAIGN_ES if locale == "es" else ENV_CAMPAIGN_EN
    return {
        "locale": locale,
        "campaign_id": campaign_id,
        "name": name,
        "status": "PAUSED",
        "reminder_delay_days": REMINDER_DELAY_DAYS,
        "env_line": f"{env_key}={campaign_id}",
    }
