from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id

GOOD = "STRONG FIT"
LIKELY = "LIKELY ELIGIBLE"
REVIEW = "ADMISSION REVIEW"
REVIEW_SCORE_CAP = 0.72


def cap_score_for_status(row: dict[str, Any], status: str) -> dict[str, Any]:
    if status == REVIEW:
        row["score"] = min(float(row.get("score") or 0), REVIEW_SCORE_CAP)
        row["score_pct"] = int(round(row["score"] * 100))
    return row


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def classify(profile: dict[str, Any], programme_id: str) -> dict[str, Any]:
    programme = programme_by_id(programme_id)
    if not programme:
        return {
            "status": REVIEW,
            "note": "This programme is not in the approved catalogue.",
        }
    eligibility = programme.get("eligibility") or {}
    education = _norm(profile.get("education"))
    preferred = [_norm(x) for x in eligibility.get("preferred_backgrounds") or []]
    accepted = [_norm(x) for x in eligibility.get("accepted_backgrounds") or []]
    extra = bool(eligibility.get("additional_training_possible") or programme.get("foundation_modules_possible"))

    if education and any(education == p or education in p or p in education for p in preferred):
        return {
            "status": GOOD,
            "note": "Your degree matches preferred backgrounds in the catalogue. Admission is never automatic.",
        }
    if education and any(education == a or education in a or a in education for a in accepted):
        return {
            "status": LIKELY,
            "note": "Your profile is close to accepted backgrounds. Admissions reviews each case.",
        }
    if extra:
        return {
            "status": REVIEW,
            "note": "Foundation modules may be available. An advisor should review your eligibility.",
        }
    return {
        "status": REVIEW,
        "note": "This combination is not a listed fit. An advisor can explore other options.",
    }
