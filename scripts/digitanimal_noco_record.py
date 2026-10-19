#!/usr/bin/env python3
"""Build Noco meta_leads record dict from a Make Meta trigger bundle (module 1 output)."""
from __future__ import annotations

from typing import Any

from digitanimal_field_aliases import CANONICAL_FROM_SLUG, build_slug_index, pick


def _data(bundle: dict[str, Any]) -> dict[str, Any]:
    d = bundle.get("data")
    return d if isinstance(d, dict) else {}


def _first(*values: Any) -> Any:
    for v in values:
        if v is None:
            continue
        if isinstance(v, str) and v == "":
            continue
        if isinstance(v, list) and not v:
            continue
        return v
    return None


def _join_list(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, list):
        return ", ".join(str(x) for x in val) if val else None
    return str(val)


def _full_name(data: dict[str, Any]) -> str | None:
    nom_apellidos = data.get("nombre_y_apellidos")
    if isinstance(nom_apellidos, str) and nom_apellidos.strip():
        return nom_apellidos.strip()
    prenom = data.get("prénom") or data.get("prenom")
    nom = data.get("nom_de_famille")
    if prenom and str(prenom).strip():
        family = _first(nom, data.get("full_name"), data.get("full name"))
        if family:
            return " ".join(x for x in (str(prenom).strip(), str(family).strip()) if x).strip() or None
        return str(prenom).strip() or None
    direct = _first(data.get("full_name"), data.get("full name"))
    if direct:
        return str(direct)
    if prenom or nom:
        return " ".join(x for x in (prenom, nom) if x).strip() or None
    return None


def _full_name_from_index(idx: dict[str, Any]) -> str | None:
    nom_apellidos = pick(idx, "nombre_y_apellidos")
    if nom_apellidos and str(nom_apellidos).strip():
        return str(nom_apellidos).strip()
    prenom = pick(idx, *CANONICAL_FROM_SLUG["first_name"])
    nom = pick(idx, *CANONICAL_FROM_SLUG["last_name"])
    if prenom and str(prenom).strip():
        family = _first(nom, pick(idx, "full_name", "full name"))
        if family:
            return " ".join(x for x in (str(prenom).strip(), str(family).strip()) if x).strip() or None
        return str(prenom).strip() or None
    direct = pick(idx, *CANONICAL_FROM_SLUG["full_name"])
    if direct:
        return str(direct)
    if prenom or nom:
        return " ".join(x for x in (prenom, nom) if x).strip() or None
    return None


def record_from_make_bundle(bundle: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    """Map facebook-lead-ads NewLeadMultiple output to Noco column names."""
    data = _data(bundle)
    idx = build_slug_index(data)
    phone = pick(idx, *CANONICAL_FROM_SLUG["phone"])
    email = pick(idx, *CANONICAL_FROM_SLUG["email"])
    province = pick(idx, *CANONICAL_FROM_SLUG["province"])
    herd = pick(idx, *CANONICAL_FROM_SLUG["herd_count"])
    livestock = pick(idx, *CANONICAL_FROM_SLUG["livestock_type"])
    name = _full_name(data) or _full_name_from_index(idx)
    page_id = bundle.get("pageId")
    leadgen = bundle.get("leadgenId")
    return {
        "leadgen_id": leadgen,
        "form_id": bundle.get("formId"),
        "page_id": page_id,
        "platform": bundle.get("platform"),
        "is_organic": bool(bundle.get("isOrganic")),
        "date_created": bundle.get("dateCreated"),
        "lead_source": f"meta_{page_id}" if page_id else None,
        "campaign_id": bundle.get("campaignId"),
        "campaign_name": bundle.get("campaignName"),
        "adset_id": bundle.get("adsetId"),
        "adset_name": bundle.get("adsetName"),
        "ad_id": bundle.get("adId"),
        "ad_name": bundle.get("adName"),
        "adgroup_id": bundle.get("adgroupId"),
        "email": email,
        "phone": phone,
        "full_name": name,
        "province": province,
        "herd_count": _join_list(herd),
        "livestock_type": _join_list(livestock),
        "home_listing": bundle.get("homeListing"),
        "partner_name": bundle.get("partnerName"),
        "retailer_item_id": bundle.get("retailerItemId"),
        "make_scenario_id": scenario_id,
        "meta_payload_json": bundle,
        "title": name or leadgen,
    }


def record_from_sheets_row(row: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    """Best-effort row from exported Google Sheet (meta_Digitanimal* headers)."""
    leadgen = row.get("leadid") or row.get("leadgen_id")
    page_source = row.get("source") or ""
    page_id = page_source.replace("meta_", "") if page_source.startswith("meta_") else None
    payload = {
        "backfill_source": "google_sheets_csv",
        "row": {k: v for k, v in row.items() if v not in (None, "")},
    }
    return {
        "leadgen_id": leadgen,
        "form_id": row.get("formid"),
        "date_created": row.get("date"),
        "lead_source": page_source or (f"meta_{page_id}" if page_id else None),
        "campaign_name": row.get("campaign"),
        "adset_name": row.get("adset"),
        "ad_name": row.get("ad"),
        "campaign_id": row.get("campaignid"),
        "adgroup_id": row.get("adsetid"),
        "ad_id": row.get("adid"),
        "email": row.get("email"),
        "phone": row.get("phone"),
        "full_name": row.get("name"),
        "province": row.get("province"),
        "herd_count": row.get("cant-animales"),
        "livestock_type": row.get("tipo_animal"),
        "make_scenario_id": scenario_id,
        "meta_payload_json": payload,
        "title": row.get("name") or leadgen,
    }
