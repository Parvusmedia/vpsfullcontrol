"""LinkedIn connection + follow-up copy for CDE SalesNav outbound."""

from __future__ import annotations

import re
from typing import Any

from .config import PRODUCT_URL

_SPACE_RE = re.compile(r"\s+")


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


def build_connection_message(lead: dict[str, Any]) -> str:
    first = _first_name(lead)
    company = _company(lead)
    region = _region_hint(lead)

    if region == "es":
        return (
            f"Hola {first},\n\n"
            f"He visto tu perfil en {company} y pensé que podría interesarte: exportar listas de Sales Navigator "
            f"a CSV (nombre, cargo, empresa, URL) en minutos, sin copiar a mano.\n\n"
            f"Lo uso con equipos outbound/SDR. Si encaja, encantado de conectar.\n\n"
            f"Emiliano"
        )

    return (
        f"Hi {first},\n\n"
        f"I saw your role at {company} — I built a small tool that exports Sales Navigator lists/searches to CSV "
        f"(name, title, company, LinkedIn URL) in minutes, which SDR/outbound teams seem to find useful.\n\n"
        f"Would be glad to connect.\n\n"
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
            f"Si en {company} exportáis leads desde Sales Navigator, aquí tienes el panel: {url}\n\n"
            f"Puedes probar con una lista pequeña (demo gratis) y recargar créditos cuando os encaje.\n\n"
            f"Si te parece útil, te enseño en 10 min cómo lo usamos con listas reales.\n\n"
            f"Emiliano"
        )

    return (
        f"Hi {first},\n\n"
        f"Thanks for connecting.\n\n"
        f"If your team exports leads from Sales Navigator, here's the panel: {url}\n\n"
        f"You can run a small demo export free, then top up credits if it saves your reps time.\n\n"
        f"Happy to walk you through a real list in ~10 minutes if useful for {company}.\n\n"
        f"Emiliano"
    )


def compose_row_messages(lead: dict[str, Any]) -> dict[str, str]:
    connection = build_connection_message(lead)
    followup = build_followup_message(lead)
    return {
        "connection_message": connection,
        "followup_message": followup,
        "mensaje_estado": "Pendiente confirmar",
    }
