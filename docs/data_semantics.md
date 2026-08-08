# Data Semantics: What Is API-Native vs Project-Derived?

This document is intentionally short and should be read before interpreting dashboard charts.

## API-native fields

These are extracted directly from ClinicalTrials.gov records:

- `phase_raw`
- `overall_status`
- `last_known_status`
- `status_verified_date`
- `lead_sponsor`
- `lead_sponsor_class`
- collaborator names/classes
- intervention type/name/description
- primary outcomes
- start / primary-completion / completion dates and their date types

The project may re-label values for readability, but does not infer these fields from free text.

## Project-derived fields

These are analytical constructs and should not be treated as ClinicalTrials.gov facts:

- `therapeutic_candidate`
- `active_therapeutic_candidate`
- mechanism categories
- mechanism confidence/source
- mechanism eligibility/review status
- potential stale-record flag

## Sponsor semantics

`lead_sponsor` is counted exactly as registered.

The project does **not** currently merge:

- acquisitions,
- historical company names,
- subsidiaries,
- spelling variants,
- parent corporate groups.

Therefore "Top Lead Sponsors" is not yet the same as "Top pharmaceutical companies by AD investment."

## Phase semantics

- `Not Applicable`: the API explicitly reports `NA`.
- `Missing / Not reported`: the record contains no phase value.
- other phase labels are readable mappings of the API phase enum.

## Mechanism semantics

Mechanism analysis now follows this sequence:

```text
all intervention rows
    ↓
keep DRUG / BIOLOGICAL / COMBINATION_PRODUCT
    ↓
exclude obvious placebo / sham / control interventions
    ↓
curated override or heuristic mechanism annotation
    ↓
classified OR needs_review
```

`needs_review` is not interpreted as "biology unknown." It means the current project annotation layer could not confidently classify the eligible intervention.

## Timeline semantics

Historical primary-completion plots use `ACTUAL` primary-completion dates.

Future candidate-completion plots require:

- `ESTIMATED` primary-completion date,
- a future date,
- an active-like recruitment status.

Primary completion is not automatically the same as a public company readout date.
