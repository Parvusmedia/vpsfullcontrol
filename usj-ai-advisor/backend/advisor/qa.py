from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id, programmes
from .eligibility import classify


def _facts(programme: dict[str, Any]) -> str:
    return " ".join(programme.get("approved_facts") or [])


def _modality(programme: dict[str, Any]) -> str:
    raw = str(programme.get("modality") or "")
    if raw.lower() == "hybrid":
        return "semipresencial"
    if "campus" in raw.lower() or "on campus" in raw.lower():
        return "presencial"
    return raw or "la modalidad del catálogo"


def answer_question(
    question: str,
    profile: dict[str, Any],
    recommendation: dict[str, Any] | None,
    alternatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    q = (question or "").strip().lower()
    rec_id = (recommendation or {}).get("programme_id") or (recommendation or {}).get("programme")
    programme = programme_by_id(str(rec_id) if rec_id else "") if rec_id else None
    if programme is None and rec_id:
        for item in programmes():
            if item["name"].lower() == str(rec_id).lower() or item["id"] == rec_id:
                programme = item
                break
    if programme is None and recommendation:
        programme = programme_by_id("biomechanics") if "biomech" in str(recommendation).lower() else None

    if not q:
        return {"answer": "Pregunta por la modalidad, el acceso o por qué sale este máster.", "source": "catalogue"}

    if "compatibil" in q or "trabajo" in q or "combine" in q or "work" in q:
        if programme and (programme.get("work_compatible") or str(programme.get("modality")).lower() == "hybrid"):
            return {
                "answer": (
                    f"{programme['name']} figura como {_modality(programme)} en el catálogo, "
                    "lo que puede facilitar compatibilizarlo con el trabajo. Un asesor confirma el horario vigente."
                ),
                "source": "catalogue",
            }
        if programme:
            return {
                "answer": (
                    f"{programme['name']} figura como {_modality(programme)}. "
                    "Compatibilizarlo con un trabajo a tiempo completo puede ser más difícil. Un asesor puede confirmar opciones."
                ),
                "source": "catalogue",
            }

    if ("empresa" in q or "ade" in q or "business" in q) and (
        "ia" in q or "inteligencia" in q or "artificial" in q or "ai" in q
    ):
        ai = programme_by_id("ai-applied")
        elig = classify({"education": "business administration"}, "ai-applied")
        extra = (
            " El catálogo contempla complementos formativos si falta base técnica."
            if ai and ai.get("foundation_modules_possible")
            else ""
        )
        return {
            "answer": (
                "ADE no es un perfil STEM preferente para Inteligencia Artificial Aplicada. "
                f"Estado: {elig['status']}.{extra} Un asesor debe revisar la elegibilidad: este anuncio no admite a nadie."
            ),
            "source": "catalogue",
        }

    if "técnic" in q or "tecnic" in q or "technical" in q:
        if programme:
            tech = (
                "Es un programa técnico."
                if programme.get("technical")
                else "No está posicionado como un máster STEM altamente técnico."
            )
            return {"answer": f"{tech} {_facts(programme)}", "source": "catalogue"}

    if "por qué" in q or "porque" in q or "encaja" in q or "why" in q or "recommend" in q:
        reasons = (recommendation or {}).get("reasons") or []
        if reasons:
            return {
                "answer": (
                    "Sale esta opción porque: "
                    + "; ".join(reasons)
                    + ". Las razones salen del motor de encaje, no de promesas de salario o admisión."
                ),
                "source": "match-engine",
            }

    if "diferencia" in q or "entre" in q or "difference" in q or "between" in q:
        names = []
        if programme:
            names.append(programme)
        for alt in (alternatives or [])[:2]:
            other = programme_by_id(alt.get("programme_id") or "")
            if other:
                names.append(other)
        if len(names) >= 2:
            a, b = names[0], names[1]
            return {
                "answer": (
                    f"{a['name']} es {_modality(a)}, centrado en {', '.join(a['areas'][:3])}. "
                    f"{b['name']} es {_modality(b)}, centrado en {', '.join(b['areas'][:3])}. "
                    "Ambos son 60 ECTS en este catálogo demo."
                ),
                "source": "catalogue",
            }

    if programme:
        return {
            "answer": (
                f"Según el catálogo aprobado: {_facts(programme)} "
                "Solo uso estos datos: para cualquier otra cosa, habla con un asesor de USJ."
            ),
            "source": "catalogue",
        }
    return {
        "answer": "Solo puedo responder con los tres másteres de este demo. Un asesor de USJ puede ayudarte con el resto del catálogo.",
        "source": "catalogue",
    }
