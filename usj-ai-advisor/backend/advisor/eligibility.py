from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id

GOOD = "BUEN ENCAJE"
LIKELY = "PROBABLEMENTE ELEGIBLE"
REVIEW = "ADMISIÓN A REVISAR"


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def classify(profile: dict[str, Any], programme_id: str) -> dict[str, Any]:
    programme = programme_by_id(programme_id)
    if not programme:
        return {
            "status": REVIEW,
            "note": "Este programa no está en el catálogo aprobado.",
        }
    eligibility = programme.get("eligibility") or {}
    education = _norm(profile.get("education"))
    preferred = [_norm(x) for x in eligibility.get("preferred_backgrounds") or []]
    accepted = [_norm(x) for x in eligibility.get("accepted_backgrounds") or []]
    extra = bool(eligibility.get("additional_training_possible") or programme.get("foundation_modules_possible"))

    if education and any(education == p or education in p or p in education for p in preferred):
        return {
            "status": GOOD,
            "note": "Tu titulación está entre los perfiles preferentes del catálogo. La admisión nunca es automática.",
        }
    if education and any(education == a or education in a or a in education for a in accepted):
        return {
            "status": LIKELY,
            "note": "Tu titulación se acerca a los perfiles aceptados. Admisiones revisa cada caso.",
        }
    if extra:
        return {
            "status": REVIEW,
            "note": "Puede haber complementos formativos. Un asesor debe revisar tu elegibilidad.",
        }
    return {
        "status": REVIEW,
        "note": "Esta combinación no es un encaje listado. Un asesor de USJ puede valorar otras opciones.",
    }
