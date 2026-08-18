from __future__ import annotations

import re
from typing import Any

NORMALIZE = {
    "fisioterapeuta": "physiotherapy",
    "fisioterapia": "physiotherapy",
    "physiotherapist": "physiotherapy",
    "physical therapy": "physiotherapy",
    "kinesiologia": "kinesiology",
    "ciencias del deporte": "sports science",
    "sport science": "sports science",
    "sports science": "sports science",
    "ingenieria de software": "software engineering",
    "ingeniería de software": "software engineering",
    "software engineer": "software engineering",
    "software engineering": "software engineering",
    "computer science": "computer science",
    "informatica": "informatics",
    "informática": "informatics",
    "developer": "software engineering",
    "desarrollador": "software engineering",
    "programador": "software engineering",
    "data scientist": "data science",
    "ciencia de datos": "data science",
    "business administration": "business administration",
    "ade": "business administration",
    "administracion de empresas": "business administration",
    "administración de empresas": "business administration",
    "marketing digital": "digital marketing",
    "digital marketing": "digital marketing",
    "comunicacion": "communication",
    "comunicación": "communication",
    "chef": "culinary arts",
    "cocinero": "culinary arts",
    "architect": "architecture",
    "arquitecto": "architecture",
    "arquitectura": "architecture",
}

GOAL_PATTERNS = [
    ("specialization", ("specialize", "specialise", "specialization", "especializar", "especializacion", "especialización")),
    ("learn AI", ("apply ai", "inteligencia artificial", "learn ai", "machine learning")),
    ("career progression", ("progress", "management role", "promocion", "promoción", "career")),
    ("career change", ("career change", "become an architect", "cambiar de carrera", "switch")),
    ("research", ("research", "investigacion", "investigación", "phd", "doctorado")),
]

INTEREST_PATTERNS = [
    ("sports", ("athlete", "athletes", "sports", "deporte", "deportista", "deportistas")),
    ("movement analysis", ("movement", "biomechanics", "locomotion", "analisis del movimiento", "análisis")),
    ("artificial intelligence", ("ai", "artificial intelligence", "inteligencia artificial", "machine learning")),
    ("software", ("software", "developer", "code", "programming")),
    ("digital marketing", ("digital marketing", "marketing digital", "campaigns")),
    ("brand", ("brand", "marca", "communication", "comunicacion")),
    ("architecture", ("architect", "architecture", "arquitectura")),
    ("culinary", ("chef", "cook", "kitchen", "cocina")),
]

CONSTRAINT_PATTERNS = [
    ("combine work and study", ("without leaving", "continuing to work", "combine", "sin dejar", "seguir trabajando", "compatible con trabajo", "part time", "part-time")),
    ("on campus only", ("on campus", "presencial", "relocate")),
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _find_education(text: str) -> str | None:
    ordered = sorted(NORMALIZE.items(), key=lambda kv: len(kv[0]), reverse=True)
    for needle, canon in ordered:
        if needle in text:
            return canon
    return None


_WORD_YEARS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
}


def _experience_years(text: str) -> int | None:
    patterns = [
        r"(\d+)\s*(?:years?|años?)",
        r"hace\s+(\d+)\s*años",
        r"(\d+)\s*años de experiencia",
        r"(one|two|three|four|five|six|seven|eight|nine|ten|un|una|dos|tres|cuatro|cinco)\s*(?:years?|años?)",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            raw = match.group(1)
            if raw.isdigit():
                return int(raw)
            return _WORD_YEARS.get(raw)
    return None


def _first_match(text: str, table: list[tuple[str, tuple[str, ...]]]) -> str | None:
    for label, needles in table:
        if any(n in text for n in needles):
            return label
    return None


def _all_matches(text: str, table: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    found: list[str] = []
    for label, needles in table:
        if any(n in text for n in needles) and label not in found:
            found.append(label)
    return found


def _role_from_education(education: str | None, text: str) -> str | None:
    if "physiotherap" in text or "fisioterapeut" in text:
        return "Physiotherapist"
    if "developer" in text or "desarrollador" in text or "software" in text:
        return "Developer"
    if "digital marketing" in text or "marketing" in text:
        return "Digital marketing professional"
    if education == "culinary arts":
        return "Chef"
    if education:
        return education.replace("_", " ").title()
    return None


def parse_profile(message: str, priority: str | None = None) -> dict[str, Any]:
    text = _norm(message)
    education = _find_education(text)
    interests = _all_matches(text, INTEREST_PATTERNS)
    goal = _first_match(text, GOAL_PATTERNS)
    constraints = _all_matches(text, CONSTRAINT_PATTERNS)
    years = _experience_years(text)
    role = _role_from_education(education, text)

    if priority:
        p = _norm(priority)
        if "technolog" in p or "ai" in p:
            if "artificial intelligence" not in interests:
                interests.append("artificial intelligence")
            goal = goal or "learn AI"
        if "special" in p:
            goal = "specialization"
        if "brand" in p or "communication" in p or "marketing" in p:
            if "brand" not in interests:
                interests.append("brand")
            goal = goal or "marketing career"
        if "research" in p:
            goal = "research"
        if "combine" in p or "work" in p:
            if "combine work and study" not in constraints:
                constraints.append("combine work and study")
        if "career change" in p:
            goal = "career change"
        if "salary" in p or "job opportunities" in p:
            goal = goal or "career progression"

    return {
        "education": education,
        "experience_years": years,
        "current_role": role,
        "interests": interests,
        "goal": goal,
        "constraints": constraints,
        "priority": priority,
        "raw_message": message.strip(),
        "parser": "mock",
    }
