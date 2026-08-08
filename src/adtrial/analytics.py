from __future__ import annotations

import pandas as pd
from .industry import ACTIVE_STATUSES

PHASE_ORDER = [
    "Early Phase 1",
    "Phase 1",
    "Phase 1 + Phase 2",
    "Phase 2",
    "Phase 2 + Phase 3",
    "Phase 3",
    "Phase 4",
    "Not Applicable",
    "Missing / Not reported",
]


def _bool_series(series):
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def mechanism_subset(interventions: pd.DataFrame, study_ids=None) -> pd.DataFrame:
    df = interventions.copy()
    if study_ids is not None:
        df = df[df["nct_id"].isin(set(study_ids))]
    if "mechanism_analysis_eligible" in df.columns:
        df = df[_bool_series(df["mechanism_analysis_eligible"])]
    else:
        therapeutic = df["intervention_type"].astype(str).str.upper().isin(
            ["DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT"]
        )
        control = df["intervention_name"].astype(str).str.lower().str.contains(
            r"\b(placebo|sham|vehicle|control|standard of care|usual care)\b",
            regex=True,
            na=False,
        )
        df = df[therapeutic & ~control]
    return df


def mechanism_summary(interventions: pd.DataFrame, study_ids=None):
    eligible = mechanism_subset(interventions, study_ids)
    if eligible.empty:
        return eligible, pd.DataFrame(columns=["Mechanism", "Interventions"]), {
            "eligible": 0, "classified": 0, "needs_review": 0, "coverage_pct": 0.0
        }

    needs = eligible["mechanism_review_status"].astype(str).eq("needs_review") \
        if "mechanism_review_status" in eligible.columns \
        else eligible["mechanism_source"].astype(str).eq("unclassified")

    classified = eligible[~needs].copy()
    counts = (
        classified["mechanism_category"]
        .replace("", "Other / unclassified")
        .value_counts()
        .rename_axis("Mechanism")
        .reset_index(name="Interventions")
    )
    total = len(eligible)
    n_classified = len(classified)
    stats = {
        "eligible": total,
        "classified": n_classified,
        "needs_review": int(needs.sum()),
        "coverage_pct": 100.0 * n_classified / total if total else 0.0,
    }
    return eligible, counts, stats


def mechanism_review_queue(interventions: pd.DataFrame, study_ids=None, limit=None) -> pd.DataFrame:
    eligible = mechanism_subset(interventions, study_ids)
    if eligible.empty:
        return pd.DataFrame(columns=[
            "intervention_name","intervention_type","trial_count",
            "intervention_count","example_nct_ids"
        ])
    if "mechanism_review_status" in eligible.columns:
        review = eligible[eligible["mechanism_review_status"].astype(str).eq("needs_review")].copy()
    else:
        review = eligible[eligible["mechanism_source"].astype(str).eq("unclassified")].copy()
    review["intervention_name"] = review["intervention_name"].replace("", "(missing name)")
    rows = []
    for (name, itype), g in review.groupby(["intervention_name","intervention_type"], dropna=False):
        rows.append({
            "intervention_name": name,
            "intervention_type": itype,
            "trial_count": int(g["nct_id"].nunique()),
            "intervention_count": int(len(g)),
            "example_nct_ids": "; ".join(g["nct_id"].drop_duplicates().astype(str).head(5)),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["trial_count","intervention_count","intervention_name"], ascending=[False,False,True])
    return out.head(limit) if limit else out


def _with_primary_completion_dt(studies):
    df = studies.copy()
    df["primary_completion_dt"] = pd.to_datetime(df["primary_completion_date"], errors="coerce")
    return df


def historical_actual_primary_completions(studies, as_of=None):
    df = _with_primary_completion_dt(studies)
    now = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.today().normalize()
    mask = (
        df["primary_completion_date_type"].astype(str).str.upper().eq("ACTUAL")
        & df["primary_completion_dt"].notna()
        & (df["primary_completion_dt"] <= now)
    )
    out = df[mask].copy()
    if not out.empty:
        out["quarter"] = out["primary_completion_dt"].dt.to_period("Q").astype(str)
    return out


def future_estimated_primary_completions(studies, as_of=None):
    df = _with_primary_completion_dt(studies)
    now = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.today().normalize()
    mask = (
        df["primary_completion_date_type"].astype(str).str.upper().eq("ESTIMATED")
        & df["primary_completion_dt"].notna()
        & (df["primary_completion_dt"] >= now)
        & df["overall_status"].astype(str).isin(ACTIVE_STATUSES)
    )
    out = df[mask].copy()
    if not out.empty:
        out["quarter"] = out["primary_completion_dt"].dt.to_period("Q").astype(str)
    return out


def approximate_trial_duration(studies):
    df = studies.copy()
    df["start_dt"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["primary_completion_dt"] = pd.to_datetime(df["primary_completion_date"], errors="coerce")
    df["approx_primary_duration_years"] = (
        (df["primary_completion_dt"] - df["start_dt"]).dt.days / 365.25
    )
    return df[
        df["approx_primary_duration_years"].notna()
        & (df["approx_primary_duration_years"] >= 0)
        & (df["approx_primary_duration_years"] <= 30)
    ].copy()
