from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id
from .eligibility import GOOD, LIKELY, REVIEW

FORBIDDEN = (
    "guarantees you a better salary",
    "you are accepted",
    "job guarantee",
    "admission guaranteed",
    "you are admitted",
    "place guaranteed",
    "salary guaranteed",
)


def _safe(text: str) -> str:
    low = text.lower()
    for bad in FORBIDDEN:
        if bad in low:
            return "This guidance is based only on matching signals and the approved catalogue."
    return text


def explain(profile: dict[str, Any], match: dict[str, Any], eligibility: dict[str, Any]) -> str:
    programme = programme_by_id(match["programme_id"]) or {}
    reasons = match.get("reasons") or []
    name = programme.get("name") or match.get("programme")
    bits = []
    if reasons:
        bits.append("It fits because: " + "; ".join(reasons[:3]).lower() + ".")
    else:
        bits.append(f"{name} is the closest option in this demo catalogue.")
    status = eligibility.get("status")
    if status == GOOD:
        bits.append("Your degree is among the preferred backgrounds in the catalogue.")
    elif status == LIKELY:
        bits.append("Your profile is close to accepted backgrounds, but admission still needs review.")
    elif status == REVIEW:
        bits.append("Eligibility is not automatic: an advisor should review your case.")
        if programme.get("foundation_modules_possible"):
            bits.append("The catalogue allows foundation modules if technical background is limited.")
    if any("hybrid" in r.lower() for r in reasons):
        bits.append("Hybrid delivery in the catalogue may help if you keep working.")
    if profile.get("education") == "law" and match.get("programme_id") == "ai-applied":
        bits.append("This demo has no digital law programme; Applied AI is the closest technology option.")
    bits.append("This is in-ad guidance, not a place offer.")
    return _safe(" ".join(bits))
