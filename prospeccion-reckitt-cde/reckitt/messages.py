"""LinkedIn connection + follow-up copy (EN) — Reckitt Data for Media angle."""

from __future__ import annotations

from typing import Any

from .config import INVITE_NOTE_MAX_CHARS, INVITE_NOTE_EN


def _first_name(lead: dict[str, Any]) -> str:
    first = str(lead.get("first_name") or "").strip()
    if first:
        return first.split()[0]
    title = str(lead.get("Title") or lead.get("full_name") or "").strip()
    return title.split()[0] if title else "there"


def build_connection_message(lead: dict[str, Any], *, max_chars: int = INVITE_NOTE_MAX_CHARS) -> str:
    first = _first_name(lead)
    note = INVITE_NOTE_EN.replace("{first_name}", first)
    if len(note) > max_chars:
        note = note[: max_chars - 1].rstrip() + "…"
    return note


def build_followup_message(lead: dict[str, Any]) -> str:
    first = _first_name(lead)
    return (
        f"Hi {first},\n\n"
        "Thanks for connecting.\n\n"
        "We helped Reckitt in Spain plan media for the following 7 days by tying "
        "campaigns to weather and Google Trends in real time — so the team knew "
        "which region demand was about to land in, and could activate accordingly.\n\n"
        "If useful, happy to walk you through that loop in 20 minutes.\n\n"
        "Emiliano"
    )


def compose_row_messages(lead: dict[str, Any]) -> dict[str, str]:
    return {
        "connection_message": build_connection_message(lead),
        "followup_message": build_followup_message(lead),
        "mensaje_estado": "Pendiente confirmar",
    }
