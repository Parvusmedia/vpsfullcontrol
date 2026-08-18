from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id

GOOD = "GOOD MATCH"
LIKELY = "LIKELY ELIGIBLE"
REVIEW = "ADMISSION REQUIRES REVIEW"


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def classify(profile: dict[str, Any], programme_id: str) -> dict[str, Any]:
    programme = programme_by_id(programme_id)
    if not programme:
        return {
            "status": REVIEW,
            "note": "Programme not in the approved catalogue.",
        }
    eligibility = programme.get("eligibility") or {}
    education = _norm(profile.get("education"))
    preferred = [_norm(x) for x in eligibility.get("preferred_backgrounds") or []]
    accepted = [_norm(x) for x in eligibility.get("accepted_backgrounds") or []]
    extra = bool(eligibility.get("additional_training_possible") or programme.get("foundation_modules_possible"))

    if education and any(education == p or education in p or p in education for p in preferred):
        return {
            "status": GOOD,
            "note": "Background is among the preferred profiles in the catalogue. Admission is never automatic.",
        }
    if education and any(education == a or education in a or a in education for a in accepted):
        return {
            "status": LIKELY,
            "note": "Background is close to accepted profiles. An advisor still reviews every application.",
        }
    if extra:
        return {
            "status": REVIEW,
            "note": "Foundation modules may be possible. An advisor must review eligibility.",
        }
    return {
        "status": REVIEW,
        "note": "This combination is not a listed match. An USJ advisor can review other options.",
    }
