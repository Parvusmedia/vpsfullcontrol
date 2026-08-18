from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id
from .eligibility import GOOD, LIKELY, REVIEW

FORBIDDEN = (
    "guarantees you a better salary",
    "you are accepted",
    "job guarantee",
    "admission guaranteed",
)


def _safe(text: str) -> str:
    low = text.lower()
    for bad in FORBIDDEN:
        if bad in low:
            return "This recommendation is based on the catalogue match signals only."
    return text


def explain(profile: dict[str, Any], match: dict[str, Any], eligibility: dict[str, Any]) -> str:
    programme = programme_by_id(match["programme_id"]) or {}
    reasons = match.get("reasons") or []
    name = programme.get("name") or match.get("programme")
    bits = []
    if reasons:
        joined = ", ".join(reasons[:3]).lower()
        bits.append(f"This programme matches {joined}.")
    else:
        bits.append(f"{name} is the closest catalogue option based on the signals we extracted.")
    status = eligibility.get("status")
    if status == GOOD:
        bits.append("Your background sits among the preferred profiles in the approved catalogue.")
    elif status == LIKELY:
        bits.append("Your background looks close to accepted profiles, but admission still requires review.")
    elif status == REVIEW:
        bits.append("Eligibility is not automatic: an advisor needs to review your case.")
    if "Hybrid format may fit your situation" in reasons:
        bits.append("The hybrid format in the catalogue may help if you want to keep working.")
    bits.append("This is orientation inside the ad, not an offer of admission.")
    return _safe(" ".join(bits))
