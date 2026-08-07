from __future__ import annotations

import pycountry

ACTIVE_STATUSES = {
    "NOT_YET_RECRUITING",
    "RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
}

THERAPEUTIC_TYPES = {"DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT"}
THERAPEUTIC_PURPOSES = {"TREATMENT", "PREVENTION"}


def is_active_status(status: str) -> bool:
    return str(status or "").upper() in ACTIVE_STATUSES


def split_semicolon(value: str) -> set[str]:
    return {x.strip().upper() for x in str(value or "").split(";") if x.strip()}


def is_therapeutic_candidate(row) -> bool:
    types = split_semicolon(row.get("intervention_types", ""))
    purpose = str(row.get("primary_purpose", "") or "").upper()
    return bool(types & THERAPEUTIC_TYPES) and purpose in THERAPEUTIC_PURPOSES


def is_active_therapeutic_candidate(row) -> bool:
    return is_therapeutic_candidate(row) and is_active_status(row.get("overall_status", ""))


COUNTRY_ALIASES = {
    "United States": "USA",
    "United Kingdom": "GBR",
    "Russia": "RUS",
    "South Korea": "KOR",
    "Korea, Republic of": "KOR",
    "Taiwan": "TWN",
    "Iran": "IRN",
    "Vietnam": "VNM",
    "Viet Nam": "VNM",
    "Czechia": "CZE",
    "Czech Republic": "CZE",
    "Hong Kong": "HKG",
}


def country_to_iso3(name: str) -> str | None:
    name = str(name or "").strip()
    if not name:
        return None
    if name in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None
