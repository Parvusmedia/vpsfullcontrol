"""Smartlead campaigns for prospección consultoras (SME externo)."""

from __future__ import annotations

import os
from typing import Any

_UA = "Mozilla/5.0 (compatible; ProspeccionConsultoras/0.1)"
BASE = "https://server.smartlead.ai/api/v1"

CAMPAIGN_NAME_ES = "Consultoras · SME externo · ES · tag:consultoras_es"
CAMPAIGN_NAME_EN = "Consultoras · SME externo · EN · tag:consultoras_en"
REMINDER_DELAY_DAYS = 7

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
    "--------------------------------------------------------------------------"
)


def _html(paragraphs: list[str]) -> str:
    parts = [
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        'line-height:1.55;color:#0b1220;max-width:560px">'
    ]
    for p in paragraphs:
        parts.append(f'<p style="margin:0 0 14px 0;font-size:14px;line-height:1.55">{p}</p>')
    parts.append("</div>")
    return "".join(parts)


EMAIL_1_SUBJECT_ES = "{{company_name}} — colaboración como especialista externo"
EMAIL_1_BODY_ES = _html(
    [
        "Hola {{first_name}}, encantado.",
        "Te escribo para ver si podrías indicarme qué persona o equipo sería el adecuado dentro de "
        "<b>{{company_name}}</b>.",
        "Llevo más de 20 años trabajando entre negocio y tecnología, ayudando a empresas a mejorar marketing, "
        "automatización, uso de datos y desarrollar nuevas soluciones digitales. He trabajado con empresas como "
        "Telefónica, Havas y WPP.",
        "Me gustaría explorar la posibilidad de colaborar con <b>{{company_name}}</b> como consultor o especialista "
        "externo, apoyando proyectos concretos donde mi experiencia pueda aportar valor y ayudar a generar nuevo "
        "negocio.",
        "Si crees que puede tener sentido, encantado de contarte un poco más sobre mi trayectoria. También te "
        "agradecería mucho tu orientación sobre con quién debería hablar internamente.",
        f"Muchas gracias,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_2_SUBJECT_ES = "Re: {{company_name}} — colaboración como especialista externo"
EMAIL_2_BODY_ES = _html(
    [
        "Hola {{first_name}}, solo consultaré si pudiste ver mi correo anterior.",
        "Sigo interesado en explorar cómo podría colaborar con <b>{{company_name}}</b> como consultor o especialista "
        "externo, aportando valor en proyectos concretos y ayudando a generar nuevo negocio cuando encaje.",
        "Si no eres la persona adecuada, te agradecería mucho me remitas al equipo o persona que gestione este tipo "
        "de colaboraciones.",
        f"Muchas gracias,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_1_SUBJECT_EN = "{{company_name}} — external specialist collaboration"
EMAIL_1_BODY_EN = _html(
    [
        "Hi {{first_name}}, nice to meet you.",
        "I'm reaching out to see if you could point me to the right person or team at <b>{{company_name}}</b>.",
        "I have more than 20 years of experience working between business and technology, helping companies improve "
        "marketing, automation, data use and develop new digital solutions. I've worked with companies such as "
        "Telefónica, Havas and WPP.",
        "I'd like to explore the possibility of collaborating with <b>{{company_name}}</b> as an external consultant "
        "or specialist, supporting specific projects where my experience can add value and help generate new business.",
        "If you think it could make sense, I'd be happy to share a bit more about my background. I'd also really "
        "appreciate your guidance on who would be the right person to speak with internally.",
        f"Thank you,<br><br>{EMAIL_SIGNATURE}",
    ]
)

EMAIL_2_SUBJECT_EN = "Re: {{company_name}} — external specialist collaboration"
EMAIL_2_BODY_EN = _html(
    [
        "Hi {{first_name}}, just checking whether you had a chance to see my previous email.",
        "I'm still interested in exploring how I could collaborate with <b>{{company_name}}</b> as an external "
        "consultant or specialist, bringing value to specific projects and helping generate new business where it "
        "makes sense.",
        "If you're not the right person, I'd really appreciate it if you could point me to the team or person who "
        "manages this kind of collaboration.",
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


def smartlead_api_key() -> str:
    return (
        os.environ.get("SMARTLEAD_CONSULTORAS_API_KEY")
        or os.environ.get("SMARTLEAD_PM_API_KEY")
        or os.environ.get("SMARTLEAD_DFM_API_KEY")
        or os.environ.get("SMARTLEAD_API_KEY")
        or ""
    ).strip()


def smartlead_email_account_ids() -> list[int]:
    raw = (
        os.environ.get("SMARTLEAD_CONSULTORAS_EMAIL_ACCOUNT_IDS")
        or os.environ.get("SMARTLEAD_PM_EMAIL_ACCOUNT_IDS")
        or "22230159,22230157,21979685"
    )
    out: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out


def campaign_id_for_locale(locale: str) -> str:
    loc = (locale or "en").strip().lower()
    if loc == "es":
        return (
            os.environ.get("SMARTLEAD_CONSULTORAS_ES_CAMPAIGN_ID")
            or os.environ.get("SMARTLEAD_CONSULTORAS_CAMPAIGN_ID_ES")
            or ""
        ).strip()
    return (
        os.environ.get("SMARTLEAD_CONSULTORAS_EN_CAMPAIGN_ID")
        or os.environ.get("SMARTLEAD_CONSULTORAS_CAMPAIGN_ID_EN")
        or ""
    ).strip()


def smartlead_enabled() -> bool:
    return str(os.environ.get("CONSULTORAS_SMARTLEAD_ENABLED", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def enroll_lead(
    *,
    email: str,
    first_name: str,
    last_name: str = "",
    company_name: str = "",
    linkedin_url: str = "",
    job_title: str = "",
    campaign_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    import httpx

    if not smartlead_enabled() and not dry_run:
        return {"ok": False, "skipped": True, "reason": "smartlead_disabled"}
    email_clean = (email or "").strip().lower()
    camp = (campaign_id or "").strip()
    key = smartlead_api_key()
    if not email_clean or "@" not in email_clean:
        return {"ok": False, "skipped": True, "reason": "missing_email"}
    if not camp and not dry_run:
        return {"ok": False, "skipped": True, "reason": "missing_campaign_id"}
    if not key and not dry_run:
        return {"ok": False, "skipped": True, "reason": "missing_api_key"}

    lead_payload = {
        "first_name": first_name or "",
        "last_name": last_name or "",
        "email": email_clean,
        "company_name": company_name or "",
        "linkedin_profile": linkedin_url or "",
        "custom_fields": {
            "job_title": job_title or "",
            "linkedin_url": linkedin_url or "",
            "segment": "consultoras_sme",
        },
    }
    if dry_run:
        return {"ok": True, "dry_run": True, "lead": lead_payload, "campaign_id": camp or None}

    try:
        resp = httpx.post(
            f"{BASE}/campaigns/{camp}/leads",
            params={"api_key": key},
            headers={"User-Agent": _UA, "Content-Type": "application/json"},
            json={"lead_list": [lead_payload]},
            timeout=45,
        )
        resp.raise_for_status()
        return {"ok": True, "status": "enrolled", "response": resp.json() if resp.content else {}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
