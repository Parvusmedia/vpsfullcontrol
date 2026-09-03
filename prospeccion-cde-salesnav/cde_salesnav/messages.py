"""LinkedIn connection + follow-up copy for CDE SalesNav outbound."""

from __future__ import annotations

import re
from typing import Any

from .config import PRODUCT_URL

_TITLE_RE = re.compile(
    r"\b(head of|vp|vice president|director|svp|chief|founder)\b.*\b(sales|gtm|outbound|sdr|bdr|commercial|revenue)\b",
    re.I,
)


def _first_name(lead: dict[str, Any]) -> str:
    first = str(lead.get("first_name") or "").strip()
    if first:
        return first.split()[0]
    title = str(lead.get("Title") or lead.get("name") or "").strip()
    return title.split()[0] if title else "there"


def _company(lead: dict[str, Any]) -> str:
    return str(lead.get("company_name") or lead.get("sn_company") or "your team").strip()


def _region_hint(lead: dict[str, Any]) -> str:
    loc = str(lead.get("location") or lead.get("country") or "").lower()
    if any(x in loc for x in ("united kingdom", "uk", "london", "england")):
        return "uk"
    if any(x in loc for x in ("united states", "usa", "u.s.", "america")):
        return "us"
    if any(x in loc for x in ("spain", "españa", "madrid", "barcelona")):
        return "es"
    return "intl"


def _role_hook(lead: dict[str, Any]) -> str:
    title = str(lead.get("job_title") or lead.get("sn_title") or "").strip()
    if _TITLE_RE.search(title):
        return "your sales leadership work"
    if re.search(r"\b(sdr|bdr|outbound)\b", title, re.I):
        return "your outbound motion"
    if re.search(r"\bgtm\b|go-to-market", title, re.I):
        return "your GTM work"
    return "your work on the sales side"


def build_connection_message(lead: dict[str, Any]) -> str:
    first = _first_name(lead)
    company = _company(lead)
    hook = _role_hook(lead)
    region = _region_hint(lead)

    if region == "es":
        return (
            f"Hola {first},\n\n"
            f"Vi {hook} en {company} y me pareció que podríamos tener temas en común "
            f"(prospección, Sales Navigator, equipos outbound).\n\n"
            f"Encantado de conectar.\n\n"
            f"Emiliano"
        )

    return (
        f"Hi {first},\n\n"
        f"Came across {hook} at {company} — looks like we overlap on prospecting and "
        f"Sales Navigator workflows.\n\n"
        f"Would be good to connect.\n\n"
        f"Emiliano"
    )


def build_followup_message(lead: dict[str, Any]) -> str:
    first = _first_name(lead)
    company = _company(lead)
    region = _region_hint(lead)
    url = PRODUCT_URL.rstrip("/")

    if region == "es":
        return (
            f"Hola {first},\n\n"
            f"Gracias por conectar.\n\n"
            f"Curiosidad rápida: ¿cómo lleváis hoy la exportación de listas desde Sales Navigator en {company}? "
            f"He estado hablando con varios equipos de ventas sobre eso.\n\n"
            f"Si te encaja, te paso un enlace con algo que hemos montado ({url}) — sin compromiso.\n\n"
            f"Emiliano"
        )

    return (
        f"Hi {first},\n\n"
        f"Thanks for connecting.\n\n"
        f"Quick question — how does your team handle Sales Navigator list exports today at {company}? "
        f"I've been chatting with a few sales leaders about that lately.\n\n"
        f"If it's relevant, happy to share something we've been using: {url}\n\n"
        f"Emiliano"
    )


def compose_row_messages(lead: dict[str, Any]) -> dict[str, str]:
    return {
        "connection_message": build_connection_message(lead),
        "followup_message": build_followup_message(lead),
        "mensaje_estado": "Pendiente confirmar",
    }
