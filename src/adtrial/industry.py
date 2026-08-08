from __future__ import annotations
import re
import pandas as pd
import pycountry

ACTIVE_STATUSES = {
    "NOT_YET_RECRUITING","RECRUITING",
    "ENROLLING_BY_INVITATION","ACTIVE_NOT_RECRUITING",
}
TREATMENT_PREVENTION_PURPOSES = {"TREATMENT","PREVENTION"}

# Appropriate for target/mechanism review.
MECHANISM_ELIGIBLE_TYPES = {"DRUG","BIOLOGICAL","COMBINATION_PRODUCT","GENETIC"}

# Kept for backward compatibility with v0.1.x fields.
THERAPEUTIC_TYPES = {"DRUG","BIOLOGICAL","COMBINATION_PRODUCT"}
THERAPEUTIC_PURPOSES = TREATMENT_PREVENTION_PURPOSES

NON_DRUG_INTERVENTION_TYPES = {
    "DEVICE","PROCEDURE","BEHAVIORAL","DIETARY_SUPPLEMENT",
    "RADIATION","DIAGNOSTIC_TEST","OTHER",
}

_CONTROL_PATTERNS = [
    r"\bplacebo\b", r"\bsham\b", r"\bvehicle\b", r"\bcontrol\b",
    r"\bstandard\s+of\s+care\b", r"\busual\s+care\b", r"\bno\s+intervention\b",
]

def is_active_status(status: str) -> bool:
    return str(status or "").upper() in ACTIVE_STATUSES

def split_semicolon(value: str) -> set[str]:
    return {x.strip().upper() for x in str(value or "").split(";") if x.strip()}

def is_treatment_or_prevention_study(row) -> bool:
    return str(row.get("primary_purpose","") or "").upper() in TREATMENT_PREVENTION_PURPOSES

def is_active_treatment_or_prevention_study(row) -> bool:
    return is_treatment_or_prevention_study(row) and is_active_status(row.get("overall_status",""))

def is_drug_biologic_genetic_study(row) -> bool:
    return bool(split_semicolon(row.get("intervention_types","")) & MECHANISM_ELIGIBLE_TYPES) and is_treatment_or_prevention_study(row)

def is_active_drug_biologic_genetic_study(row) -> bool:
    return is_drug_biologic_genetic_study(row) and is_active_status(row.get("overall_status",""))

def is_non_drug_intervention_study(row) -> bool:
    return bool(split_semicolon(row.get("intervention_types","")) & NON_DRUG_INTERVENTION_TYPES) and is_treatment_or_prevention_study(row)

def is_active_non_drug_intervention_study(row) -> bool:
    return is_non_drug_intervention_study(row) and is_active_status(row.get("overall_status",""))

def is_therapeutic_candidate(row) -> bool:
    types = split_semicolon(row.get("intervention_types",""))
    purpose = str(row.get("primary_purpose","") or "").upper()
    return bool(types & THERAPEUTIC_TYPES) and purpose in THERAPEUTIC_PURPOSES

def is_active_therapeutic_candidate(row) -> bool:
    return is_therapeutic_candidate(row) and is_active_status(row.get("overall_status",""))

def is_control_like_intervention(intervention_or_row) -> bool:
    name = str(intervention_or_row.get("name") or intervention_or_row.get("intervention_name") or "")
    desc = str(intervention_or_row.get("description") or "")
    text = f"{name} {desc}".lower()
    return any(re.search(p,text,re.I) for p in _CONTROL_PATTERNS)

def is_mechanism_analysis_eligible(intervention_or_row) -> bool:
    itype = str(intervention_or_row.get("type") or intervention_or_row.get("intervention_type") or "").upper()
    return itype in MECHANISM_ELIGIBLE_TYPES and not is_control_like_intervention(intervention_or_row)

def mechanism_review_status(intervention_or_row, mechanism_source: str) -> str:
    if is_control_like_intervention(intervention_or_row):
        return "excluded_control"
    if not is_mechanism_analysis_eligible(intervention_or_row):
        return "excluded_non_mechanism_type"
    return "needs_review" if str(mechanism_source or "")=="unclassified" else "classified"

def _parse_date(value):
    if value is None or str(value).strip()=="":
        return pd.NaT
    return pd.to_datetime(str(value), errors="coerce")

def potential_stale_record(row, as_of=None) -> tuple[bool,str]:
    if str(row.get("last_known_status","") or "").strip():
        return True, "ClinicalTrials.gov lastKnownStatus is present"
    status=str(row.get("overall_status","") or "").upper()
    if status not in ACTIVE_STATUSES:
        return False,""
    as_of_ts = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.now(tz="UTC").tz_localize(None)
    completion=_parse_date(row.get("completion_date",""))
    verified=_parse_date(row.get("status_verified_date",""))
    if pd.isna(completion) or completion>=as_of_ts:
        return False,""
    cutoff=as_of_ts-pd.DateOffset(years=2)
    if pd.isna(verified):
        return True,"Active-like status; completion date passed; verification date missing"
    if verified<cutoff:
        return True,"Active-like status; completion date passed; status verification older than 2 years"
    return False,""

COUNTRY_ALIASES = {
    "United States":"USA","United Kingdom":"GBR","Russia":"RUS","South Korea":"KOR",
    "Korea, Republic of":"KOR","Taiwan":"TWN","Iran":"IRN","Vietnam":"VNM",
    "Viet Nam":"VNM","Czechia":"CZE","Czech Republic":"CZE","Hong Kong":"HKG",
}

def country_to_iso3(name: str) -> str | None:
    name=str(name or "").strip()
    if not name: return None
    if name in COUNTRY_ALIASES: return COUNTRY_ALIASES[name]
    try: return pycountry.countries.lookup(name).alpha_3
    except LookupError: return None
