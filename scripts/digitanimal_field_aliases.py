"""Known Meta Lead form slugs → canonical Noco column (see docs/digitanimal-meta-lead-fields.md)."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

# Canonical field → exact slugs observed in production (Unicode apostrophe U+2019 in FR keys)
CANONICAL_FROM_SLUG: dict[str, tuple[str, ...]] = {
    "email": ("email", "correo_electrónico", "e-mail"),
    "phone": ("phone_number", "phone", "número_de_teléfono", "numéro_de_téléphone"),
    "full_name": ("full_name", "full name", "nombre_y_apellidos"),
    "first_name": ("prénom", "prenom", "first_name"),
    "last_name": ("nom_de_famille", "last_name"),
    "province": (
        "province",
        "provincia",
        "region",
        "localisation_d’élevage",
        "τοποθεσία_της_κτηνοτροφικής_μονάδας",
    ),
    "herd_count": (
        "¿cuántos_animales_tienes?",
        "how_many_animals_do_you_have?",
        "quantos_animais_você_tem?",
        "combien_d’animaux_avez-vous_?",
        "número_de_animales:",
        "πόσα_ζώα_έχετε;",
        "quanti_animali_hai?",
        "numero_di_animali",
    ),
    "livestock_type": (
        "¿qué_tipo_de_ganado_tienes?",
        "what_type_of_livestock_do_you_own?",
        "qual_o_tipo_de_gado_que_possui?",
        "quel_type_de_bétail_avez-vous_?",
        "τι_είδους_ζώα_έχεις;",
        "che_tipo_di_bestiame_hai?",
        "tipo_di_animale",
    ),
}


def _normalize_key(key: str) -> str:
    """Loose match for Meta slugs (apostrophe variants, accents)."""
    k = unicodedata.normalize("NFKC", key).lower().strip()
    k = k.replace("'", "'").replace("'", "'").replace("`", "'")
    k = re.sub(r"\s+", "_", k)
    return k


def build_slug_index(data: dict[str, Any]) -> dict[str, Any]:
    """Map normalized slug → value for all keys in Meta `data`."""
    out: dict[str, Any] = {}
    for key, val in data.items():
        out[_normalize_key(key)] = val
    return out


def pick(index: dict[str, Any], *slug_variants: str) -> Any:
    for s in slug_variants:
        if _normalize_key(s) in index:
            return index[_normalize_key(s)]
    return None
