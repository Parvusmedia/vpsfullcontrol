"""Saudi hub airports and city labels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Airport:
    code: str
    name_en: str
    name_ar: str


SA_HUBS: tuple[Airport, ...] = (
    Airport("JED", "Jeddah", "جدة"),
    Airport("RUH", "Riyadh", "الرياض"),
    Airport("DMM", "Dammam", "الدمام"),
    Airport("MED", "Medina", "المدينة"),
    Airport("AHB", "Abha", "أبها"),
    Airport("TIF", "Taif", "الطائف"),
    Airport("ELQ", "Qassim", "القصيم"),
    Airport("GIZ", "Jizan", "جيزان"),
    Airport("TUU", "Tabuk", "تبوك"),
    Airport("HAS", "Hail", "حائل"),
)

HUB_CODES = {a.code for a in SA_HUBS}


def hub_label(code: str, lang: str) -> str:
    code = code.upper()
    for hub in SA_HUBS:
        if hub.code == code:
            name = hub.name_ar if lang == "ar" else hub.name_en
            return f"{name} ({code})"
    return code


def is_valid_iata(code: str) -> bool:
    return len(code) == 3 and code.isalpha()
