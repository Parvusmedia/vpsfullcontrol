"""LinkedIn connection + follow-up copy for CDE SalesNav outbound."""

from __future__ import annotations

from typing import Any

from .config import PRODUCT_URL


def _first_name(lead: dict[str, Any]) -> str:
    first = str(lead.get("first_name") or "").strip()
    if first:
        return first.split()[0]
    title = str(lead.get("Title") or lead.get("name") or "").strip()
    return title.split()[0] if title else "there"


def _region_hint(lead: dict[str, Any]) -> str:
    loc = str(lead.get("location") or lead.get("country") or "").lower()
    if any(x in loc for x in ("spain", "españa", "madrid", "barcelona")):
        return "es"
    return "en"


def build_connection_message(lead: dict[str, Any]) -> str:
    first = _first_name(lead)

    if _region_hint(lead) == "es":
        return (
            f"Hola {first},\n\n"
            f"Emiliano. También en ventas/outbound.\n\n"
            f"Un saludo,\n"
            f"Emiliano"
        )

    return (
        f"Hi {first},\n\n"
        f"Emiliano here — also in sales/outbound.\n\n"
        f"Cheers,\n"
        f"Emiliano"
    )


def build_followup_message(lead: dict[str, Any]) -> str:
    first = _first_name(lead)
    url = PRODUCT_URL.rstrip("/")

    if _region_hint(lead) == "es":
        return (
            f"Hola {first},\n\n"
            f"Gracias por conectar.\n\n"
            f"Por si os sirve algún día: sacar listas de Sales Navigator a CSV → {url}\n"
            f"Hay demo gratis con una lista pequeña.\n\n"
            f"Emiliano"
        )

    return (
        f"Hi {first},\n\n"
        f"Thanks for connecting.\n\n"
        f"In case it's useful: export Sales Navigator lists to CSV → {url}\n"
        f"Free demo on a small list.\n\n"
        f"Emiliano"
    )


def compose_row_messages(lead: dict[str, Any]) -> dict[str, str]:
    return {
        "connection_message": build_connection_message(lead),
        "followup_message": build_followup_message(lead),
        "mensaje_estado": "Pendiente confirmar",
    }
