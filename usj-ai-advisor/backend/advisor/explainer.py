from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id
from .eligibility import GOOD, LIKELY, REVIEW

FORBIDDEN = (
    "guarantees you a better salary",
    "you are accepted",
    "job guarantee",
    "admission guaranteed",
    "estás admitido",
    "plaza garantizada",
    "mejor salario garantizado",
)


def _safe(text: str) -> str:
    low = text.lower()
    for bad in FORBIDDEN:
        if bad in low:
            return "Esta orientación se basa solo en las señales del motor de encaje y en el catálogo."
    return text


def explain(profile: dict[str, Any], match: dict[str, Any], eligibility: dict[str, Any]) -> str:
    programme = programme_by_id(match["programme_id"]) or {}
    reasons = match.get("reasons") or []
    name = programme.get("name") or match.get("programme")
    bits = []
    if reasons:
        bits.append("Encaja porque: " + "; ".join(reasons[:3]).lower() + ".")
    else:
        bits.append(f"{name} es la opción más cercana de este catálogo de demostración.")
    status = eligibility.get("status")
    if status == GOOD:
        bits.append("Tu titulación está entre los perfiles preferentes del catálogo.")
    elif status == LIKELY:
        bits.append("Tu perfil se acerca a los perfiles aceptados, pero la admisión sigue a revisión.")
    elif status == REVIEW:
        bits.append("La elegibilidad no es automática: un asesor debe revisar tu caso.")
        if programme.get("foundation_modules_possible"):
            bits.append("El catálogo contempla complementos formativos si falta base técnica.")
    if any("semipresencial" in r.lower() or "hybrid" in r.lower() for r in reasons):
        bits.append("La modalidad semipresencial del catálogo puede ayudar si sigues trabajando.")
    if profile.get("education") == "law" and match.get("programme_id") == "ai-applied":
        bits.append("Este demo no incluye un máster de derecho digital; IA Aplicada es la opción tecnológica más cercana.")
    bits.append("Es orientación dentro del anuncio, no una oferta de plaza.")
    return _safe(" ".join(bits))
