from collections import Counter
import re

from .mechanism import infer_mechanism
from .industry import (
    is_control_like_intervention,
    is_mechanism_analysis_eligible,
    mechanism_review_status,
)

def _join(values, sep=" | "):
    if values is None:
        return ""
    if not isinstance(values, list):
        values = [values]
    return sep.join(str(v).strip() for v in values if v is not None and str(v).strip())

def _clean_markup(text):
    if not text:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`#>]+", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def _summarize(text, max_chars):
    text = _clean_markup(text)
    return text if len(text) <= max_chars else text[:max_chars].rstrip() + " ..."

def summarize_eligibility(criteria, max_chars=1000):
    text = _clean_markup(criteria)
    if not text:
        return "", ""
    inc = re.search(r"(?is)\binclusion criteria\b\s*:?", text)
    exc = re.search(r"(?is)\bexclusion criteria\b\s*:?", text)
    if inc and exc:
        if inc.start() < exc.start():
            return _summarize(text[inc.end():exc.start()].strip(), max_chars), _summarize(text[exc.end():].strip(), max_chars)
        return _summarize(text[inc.end():].strip(), max_chars), _summarize(text[exc.end():inc.start()].strip(), max_chars)
    return _summarize(text, max_chars), ""

def phase_label(phases):
    phases = phases or []
    if not phases:
        return "Missing / Not reported"
    m = {
        "EARLY_PHASE1": "Early Phase 1",
        "PHASE1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE4": "Phase 4",
        "NA": "Not Applicable",
    }
    return " + ".join(m.get(p, p.replace("_"," ").title()) for p in phases)

def phase_reporting_status(phases):
    phases = phases or []
    if not phases:
        return "missing"
    if "NA" in phases:
        return "not_applicable"
    return "reported"

def parse_study(study, mechanism_rules, mechanism_overrides, eligibility_summary_chars=1000):
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    sponsor = p.get("sponsorCollaboratorsModule", {})
    conditions = p.get("conditionsModule", {})
    design = p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {})
    outcomes = p.get("outcomesModule", {})
    eligibility = p.get("eligibilityModule", {})
    locations_mod = p.get("contactsLocationsModule", {})
    desc_mod = p.get("descriptionModule", {})

    nct_id = ident.get("nctId", "")
    lead = sponsor.get("leadSponsor", {}) or {}
    collaborators = sponsor.get("collaborators", []) or []
    phases = design.get("phases") or []

    eligibility_raw = _clean_markup(eligibility.get("eligibilityCriteria", ""))
    inclusion_summary, exclusion_summary = summarize_eligibility(eligibility_raw, eligibility_summary_chars)

    intervention_rows = []
    mechanisms_all = []
    mechanisms_therapeutic = []
    intervention_names = []
    intervention_types = []
    needs_review_count = 0
    therapeutic_intervention_count = 0
    classified_therapeutic_count = 0

    for i, intervention in enumerate(arms.get("interventions", []) or [], 1):
        mech = infer_mechanism(intervention, mechanism_rules, mechanism_overrides)
        control_like = is_control_like_intervention(intervention)
        mech_eligible = is_mechanism_analysis_eligible(intervention)
        review_status = mechanism_review_status(intervention, mech.source)

        mechanisms_all.append(mech.category)
        if mech_eligible:
            therapeutic_intervention_count += 1
            if review_status == "needs_review":
                needs_review_count += 1
            else:
                classified_therapeutic_count += 1
                mechanisms_therapeutic.append(mech.category)

        intervention_names.append(intervention.get("name",""))
        intervention_types.append(intervention.get("type",""))
        intervention_rows.append({
            "nct_id": nct_id,
            "intervention_index": i,
            "intervention_type": intervention.get("type",""),
            "intervention_name": intervention.get("name",""),
            "description": _clean_markup(intervention.get("description","")),
            "other_names": _join(intervention.get("otherNames",[]), "; "),
            "arm_group_labels": _join(intervention.get("armGroupLabels",[]), "; "),
            "mechanism_category": mech.category,
            "mechanism_confidence": mech.confidence,
            "mechanism_matched_terms": mech.matched_terms,
            "mechanism_source": mech.source,
            "is_control_like": control_like,
            "mechanism_analysis_eligible": mech_eligible,
            "mechanism_review_status": review_status,
        })

    mechanisms_all = list(dict.fromkeys(x for x in mechanisms_all if x))
    mechanisms_therapeutic = list(dict.fromkeys(x for x in mechanisms_therapeutic if x))

    primary_rows = []
    primary_outcomes = outcomes.get("primaryOutcomes", []) or []
    for i, outcome in enumerate(primary_outcomes, 1):
        primary_rows.append({
            "nct_id": nct_id, "outcome_index": i,
            "measure": _clean_markup(outcome.get("measure","")),
            "description": _clean_markup(outcome.get("description","")),
            "time_frame": _clean_markup(outcome.get("timeFrame","")),
        })

    location_rows = []
    for i, loc in enumerate(locations_mod.get("locations", []) or [], 1):
        geo = loc.get("geoPoint", {}) or {}
        location_rows.append({
            "nct_id": nct_id, "location_index": i,
            "facility": loc.get("facility",""), "location_status": loc.get("status",""),
            "city": loc.get("city",""), "state": loc.get("state",""), "zip": loc.get("zip",""),
            "country": loc.get("country",""), "latitude": geo.get("lat"), "longitude": geo.get("lon"),
        })

    countries = list(Counter(r["country"] for r in location_rows if r["country"]).keys())
    enrollment = design.get("enrollmentInfo", {}) or {}
    di = design.get("designInfo", {}) or {}
    masking = (di.get("maskingInfo", {}) or {}).get("masking","")
    start = status.get("startDateStruct", {}) or {}
    primary_comp = status.get("primaryCompletionDateStruct", {}) or {}
    comp = status.get("completionDateStruct", {}) or {}
    first_post = status.get("studyFirstPostDateStruct", {}) or {}
    last_post = status.get("lastUpdatePostDateStruct", {}) or {}

    collaborator_names = [x.get("name","") for x in collaborators]
    collaborator_classes = [x.get("class","") for x in collaborators]
    has_industry_collaborator = any(str(x).upper() == "INDUSTRY" for x in collaborator_classes)

    row = {
        "nct_id": nct_id,
        "brief_title": _clean_markup(ident.get("briefTitle","")),
        "official_title": _clean_markup(ident.get("officialTitle","")),
        "study_type": design.get("studyType",""),
        "phase": phase_label(phases),
        "phase_raw": _join(phases, "; "),
        "phase_reporting": phase_reporting_status(phases),
        "overall_status": status.get("overallStatus",""),
        "last_known_status": status.get("lastKnownStatus",""),
        "status_verified_date": status.get("statusVerifiedDate",""),
        "has_results": bool(study.get("hasResults", False)),
        "lead_sponsor": lead.get("name",""),
        "lead_sponsor_class": lead.get("class",""),
        "collaborators": _join(collaborator_names, "; "),
        "collaborator_classes": _join(collaborator_classes, "; "),
        "has_industry_collaborator": has_industry_collaborator,
        "conditions": _join(conditions.get("conditions",[]), "; "),
        "keywords": _join(conditions.get("keywords",[]), "; "),
        "intervention_names": _join(intervention_names, "; "),
        "intervention_types": _join(list(dict.fromkeys(str(x) for x in intervention_types if x)), "; "),
        "mechanism_categories": _join(mechanisms_all, "; "),
        "therapeutic_mechanism_categories": _join(mechanisms_therapeutic, "; "),
        "therapeutic_intervention_count": therapeutic_intervention_count,
        "classified_therapeutic_intervention_count": classified_therapeutic_count,
        "mechanism_needs_review_count": needs_review_count,
        "enrollment_count": enrollment.get("count"),
        "enrollment_type": enrollment.get("type",""),
        "allocation": di.get("allocation",""),
        "intervention_model": di.get("interventionModel",""),
        "primary_purpose": di.get("primaryPurpose",""),
        "masking": masking,
        "minimum_age": eligibility.get("minimumAge",""),
        "maximum_age": eligibility.get("maximumAge",""),
        "sex": eligibility.get("sex",""),
        "healthy_volunteers": eligibility.get("healthyVolunteers"),
        "std_ages": _join(eligibility.get("stdAges",[]), "; "),
        "eligibility_criteria": eligibility_raw,
        "inclusion_summary": inclusion_summary,
        "exclusion_summary": exclusion_summary,
        "primary_outcome_measures": _join([x.get("measure","") for x in primary_outcomes], "; "),
        "primary_outcome_timeframes": _join([x.get("timeFrame","") for x in primary_outcomes], "; "),
        "countries": _join(countries, "; "),
        "country_count": len(countries),
        "site_count": len(location_rows),
        "start_date": start.get("date",""),
        "start_date_type": start.get("type",""),
        "primary_completion_date": primary_comp.get("date",""),
        "primary_completion_date_type": primary_comp.get("type",""),
        "completion_date": comp.get("date",""),
        "completion_date_type": comp.get("type",""),
        "study_first_post_date": first_post.get("date",""),
        "last_update_post_date": last_post.get("date",""),
        "brief_summary": _clean_markup(desc_mod.get("briefSummary","")),
        "ctgov_url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    }
    return row, intervention_rows, primary_rows, location_rows
