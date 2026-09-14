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
        "As I mentioned, we helped Reckitt Spain using data driven signals for "
        "Strepsils campaigns by region.\n"
        "If this could be relevant for your market, I'd be happy to show you how it "
        "works in a short 20-minute call or by email if you consider.\n\n"
        "Thanks.\n\n"
        "Emiliano"
    )


def compose_row_messages(lead: dict[str, Any]) -> dict[str, str]:
    return {
        "connection_message": build_connection_message(lead),
        "followup_message": build_followup_message(lead),
        "mensaje_estado": "Pendiente confirmar",
    }
