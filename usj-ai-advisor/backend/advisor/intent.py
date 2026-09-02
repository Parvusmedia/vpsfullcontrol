from __future__ import annotations

from typing import Any

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


def score_intent(signals: dict[str, Any]) -> str:
    profile = bool(signals.get("profile_completed"))
    rec = bool(signals.get("recommendation_generated"))
    asked = bool(signals.get("question_asked") or (signals.get("questions_asked") or []))
    priority = bool(signals.get("priority_selected") or signals.get("priority"))
    advisor = bool(signals.get("advisor_clicked") or signals.get("lead_started") or signals.get("lead_submitted"))
    explore = bool(signals.get("programme_viewed"))

    if profile and rec and advisor:
        return HIGH
    if profile and rec and (asked or priority):
        return HIGH
    if rec and (explore or asked or priority):
        return MEDIUM
    if rec:
        return MEDIUM
    return LOW
