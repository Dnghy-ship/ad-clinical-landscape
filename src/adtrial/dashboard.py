from pathlib import Path
import os
import pandas as pd
import plotly.express as px
import streamlit as st

from adtrial.industry import country_to_iso3
from adtrial.analytics import (
    PHASE_ORDER,
    mechanism_summary,
    mechanism_review_queue,
    historical_actual_primary_completions,
    future_estimated_primary_completions,
    approximate_trial_duration,
)

st.set_page_config(page_title="AD Clinical Landscape", page_icon="🧠", layout="wide")
root = Path(os.environ.get("ADTRIAL_PROJECT_ROOT", Path.cwd()))
processed = root / "data" / "processed"

@st.cache_data
def load_table(name):
    p = processed / f"{name}.csv"
    return pd.read_csv(p, keep_default_na=False) if p.exists() else pd.DataFrame()

studies = load_table("studies")
interventions = load_table("interventions")
outcomes = load_table("primary_outcomes")
locations = load_table("locations")
quality = load_table("data_quality")

st.title("Alzheimer's Disease Clinical Trial Competitive Landscape")
st.caption(
    "ClinicalTrials.gov API v2. API-native fields are separated from project-derived "
    "therapeutic/mechanism annotations."
)

if studies.empty:
    st.error("No v0.2 processed data found. Run `python -m adtrial all` first.")
    st.stop()

def bool_col(df, name):
    if name not in df.columns:
        return pd.Series(False, index=df.index)
    s = df[name]
    return s if s.dtype == bool else s.astype(str).str.lower().isin(["true","1","yes"])

with st.sidebar:
    st.header("Research View")
    preset = st.radio(
        "Preset",
        [
            "All interventional studies",
            "Active treatment / prevention — all modalities",
            "Active drug / biologic / genetic studies",
            "Active non-drug interventions",
            "Industry-led active drug / biologic / genetic",
        ],
        index=1,
        help=(
            "These are project-defined analytical universes. "
            "Industry active therapeutics means active therapeutic candidates with an INDUSTRY lead sponsor."
        ),
    )

base = studies.copy()
if preset == "Active treatment / prevention — all modalities":
    base = base[bool_col(base, "active_treatment_or_prevention")]
elif preset == "Active drug / biologic / genetic studies":
    base = base[bool_col(base, "active_drug_biologic_genetic")]
elif preset == "Active non-drug interventions":
    base = base[bool_col(base, "active_non_drug_intervention")]
elif preset == "Industry-led active drug / biologic / genetic":
    base = base[
        bool_col(base, "active_drug_biologic_genetic")
        & base["lead_sponsor_class"].astype(str).eq("INDUSTRY")
    ]

with st.sidebar:
    st.header("Filters")
    def multi(label, series):
        vals = sorted(x for x in series.astype(str).unique() if x)
        return st.multiselect(label, vals)

    status_sel = multi("Status", base["overall_status"])
    phase_sel = multi("Phase", base["phase"])
    sponsor_class_sel = multi("Sponsor class", base["lead_sponsor_class"])
    sponsor_sel = multi("Lead sponsor (registered name)", base["lead_sponsor"])

    mech_col = "therapeutic_mechanism_categories" if "therapeutic_mechanism_categories" in base.columns else "mechanism_categories"
    mech_vals = sorted({
        x.strip()
        for v in base[mech_col].astype(str)
        for x in v.split(";")
        if x.strip()
    })
    mechanism_sel = st.multiselect("Therapeutic mechanism", mech_vals)

    country_vals = sorted({
        x.strip()
        for v in base["countries"].astype(str)
        for x in v.split(";")
        if x.strip()
    })
    country_sel = st.multiselect("Country", country_vals)
    search = st.text_input("Text search", placeholder="sponsor, drug, NCT, endpoint...")

mask = pd.Series(True, index=base.index)
if status_sel:
    mask &= base["overall_status"].isin(status_sel)
if phase_sel:
    mask &= base["phase"].isin(phase_sel)
if sponsor_class_sel:
    mask &= base["lead_sponsor_class"].isin(sponsor_class_sel)
if sponsor_sel:
    mask &= base["lead_sponsor"].isin(sponsor_sel)
if mechanism_sel:
    mask &= base[mech_col].apply(
        lambda x: any(m in [z.strip() for z in str(x).split(";")] for m in mechanism_sel)
    )
if country_sel:
    mask &= base["countries"].apply(
        lambda x: any(c in [z.strip() for z in str(x).split(";")] for c in country_sel)
    )
if search.strip():
    q = search.strip().lower()
    cols = [
        "nct_id","brief_title","official_title","lead_sponsor",
        "intervention_names",mech_col,"primary_outcome_measures"
    ]
    text = base[cols].astype(str).agg(" ".join, axis=1).str.lower()
    mask &= text.str.contains(q, regex=False)

f = base[mask].copy()
selected = set(f["nct_id"])

industry_lead = f["lead_sponsor_class"].astype(str).eq("INDUSTRY")
industry_collab = bool_col(f, "has_industry_collaborator")
industry_involved = industry_lead | industry_collab

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Studies", f"{len(f):,}")
c2.metric("Industry-led", f"{industry_lead.sum():,}", help="Lead sponsor class is INDUSTRY in the API record.")
c3.metric("Industry-involved", f"{industry_involved.sum():,}", help="Industry lead sponsor and/or industry-class collaborator.")
c4.metric("Recruiting", f"{(f['overall_status']=='RECRUITING').sum():,}")
c5.metric("Phase 3", f"{f['phase'].str.contains('Phase 3',na=False).sum():,}")

st.info(
    "Interpretation rule: first identify the analytical universe and counting unit. "
    "API-native fields (phase/status/sponsor/date) are not the same thing as project-derived mechanism annotations."
)

tab_overview, tab_interventions, tab_mech, tab_time, tab_explorer = st.tabs(
    ["Overview", "Intervention Landscape", "Mechanisms & QA", "Timeline", "Study Explorer"]
)

with tab_overview:
    left,right = st.columns(2)
    with left:
        ps = f.groupby(["phase","overall_status"]).size().reset_index(name="Trials")
        st.plotly_chart(
            px.bar(
                ps, x="phase", y="Trials", color="overall_status", barmode="stack",
                title="Phase by Status",
                category_orders={"phase": PHASE_ORDER},
            ),
            width="stretch"
        )
        st.caption(
            "`Not Applicable` means the API explicitly reports phase as not applicable. "
            "`Missing / Not reported` means no phase value was present."
        )
    with right:
        sp = (
            f["lead_sponsor"].replace("","Unknown").value_counts().head(15)
            .rename_axis("Sponsor").reset_index(name="Trials").sort_values("Trials")
        )
        st.plotly_chart(
            px.bar(sp,x="Trials",y="Sponsor",orientation="h",title="Top Lead Sponsors (as registered)"),
            width="stretch"
        )
        st.caption(
            "Exact registered lead-sponsor strings are counted. No fuzzy matching, acquisition mapping, "
            "subsidiary roll-up, or parent-company normalization is applied."
        )

    loc = locations[locations["nct_id"].isin(selected)].copy()
    if not loc.empty:
        country = (
            loc[loc["country"]!=""].groupby("country")["nct_id"].nunique()
            .rename("Trials").reset_index()
        )
        country["iso3"] = country["country"].map(country_to_iso3)
        country = country.dropna(subset=["iso3"])
        if not country.empty:
            st.plotly_chart(
                px.choropleth(
                    country, locations="iso3", locationmode="ISO-3",
                    color="Trials", hover_name="country", title="Geographic Footprint"
                ),
                width="stretch"
            )


with tab_interventions:
    ints = interventions[interventions["nct_id"].isin(selected)].copy()
    st.subheader("Intervention Landscape")
    st.caption(
        "All registered intervention types are retained here. This is the place to inspect "
        "devices, procedures/surgery, behavioral approaches, genetic interventions, dietary "
        "supplements, diagnostics and other non-drug strategies."
    )
    if ints.empty:
        st.info("No intervention rows in the current filter.")
    else:
        type_counts = (
            ints["intervention_type"].replace("", "Missing")
            .value_counts().rename_axis("Intervention type")
            .reset_index(name="Intervention rows")
            .sort_values("Intervention rows")
        )
        st.plotly_chart(
            px.bar(type_counts, x="Intervention rows", y="Intervention type",
                   orientation="h", title="Intervention Type Landscape"),
            width="stretch"
        )
        names = (
            ints.assign(intervention_name=ints["intervention_name"].replace("", "(missing name)"))
            .groupby(["intervention_name","intervention_type"], dropna=False)
            .agg(trial_count=("nct_id","nunique"), intervention_rows=("nct_id","size"))
            .reset_index()
            .sort_values(["trial_count","intervention_rows","intervention_name"],
                         ascending=[False,False,True])
            .head(50)
        )
        st.subheader("Top intervention names (as registered)")
        st.dataframe(names, width="stretch", hide_index=True)

with tab_mech:
    ints = interventions[interventions["nct_id"].isin(selected)].copy()
    eligible, mech_counts, mstats = mechanism_summary(ints)

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Eligible therapeutic interventions", f"{mstats['eligible']:,}")
    m2.metric("Classified", f"{mstats['classified']:,}")
    m3.metric("Needs review", f"{mstats['needs_review']:,}")
    m4.metric("Annotation coverage", f"{mstats['coverage_pct']:.1f}%")

    st.caption(
        "Mechanism analysis is intentionally narrower than the Intervention Landscape. "
        "It uses DRUG, BIOLOGICAL, COMBINATION_PRODUCT and GENETIC rows after excluding obvious controls/placebos. "
        "Device, behavioral and procedural interventions remain available in the Intervention Landscape."
    )

    if not mech_counts.empty:
        plot_df = mech_counts.sort_values("Interventions")
        st.plotly_chart(
            px.bar(
                plot_df, x="Interventions", y="Mechanism", orientation="h",
                title="Therapeutic Mechanism Landscape — classified eligible interventions"
            ),
            width="stretch"
        )
    else:
        st.warning("No classified therapeutic interventions in the current filter.")

    st.subheader("Mechanism review queue")
    review = mechanism_review_queue(ints, limit=50)
    st.caption(
        "These are therapeutic interventions that survived the eligibility/control filter but were not classified. "
        "This queue is where rule gaps, sparse descriptions, aliases, and potentially novel mechanisms should be reviewed."
    )
    if review.empty:
        st.success("No mechanism-review items in the current filter.")
    else:
        st.dataframe(review, width="stretch", hide_index=True)

    with st.expander("Data quality / annotation health"):
        if quality.empty:
            st.write("Run a fresh v0.2.0 full collection to create the new data-quality metrics.")
        else:
            st.dataframe(quality, width="stretch", hide_index=True)

with tab_time:
    hist = historical_actual_primary_completions(f)
    future = future_estimated_primary_completions(f)

    if not hist.empty and not future.empty:
        left,right = st.columns(2)
        with left:
            h = hist.groupby(["quarter","overall_status"]).size().reset_index(name="Trials")
            st.plotly_chart(
                px.bar(h, x="quarter", y="Trials", color="overall_status", barmode="stack",
                       title="Historical Primary Completions — ACTUAL dates"),
                width="stretch"
            )
        with right:
            fu = future.groupby(["quarter","overall_status"]).size().reset_index(name="Trials")
            st.plotly_chart(
                px.bar(fu, x="quarter", y="Trials", color="overall_status", barmode="stack",
                       title="Future Candidate Primary Completions — ESTIMATED + active status"),
                width="stretch"
            )
    elif not future.empty:
        fu = future.groupby(["quarter","overall_status"]).size().reset_index(name="Trials")
        st.plotly_chart(
            px.bar(fu, x="quarter", y="Trials", color="overall_status", barmode="stack",
                   title="Future Candidate Primary Completions — ESTIMATED + active status"),
            width="stretch"
        )
    elif not hist.empty:
        h = hist.groupby(["quarter","overall_status"]).size().reset_index(name="Trials")
        st.plotly_chart(
            px.bar(h, x="quarter", y="Trials", color="overall_status", barmode="stack",
                   title="Historical Primary Completions — ACTUAL dates"),
            width="stretch"
        )
    else:
        st.info("No historical ACTUAL or future ESTIMATED primary-completion records in this view.")

    st.caption(
        "Primary completion is the date for final collection of primary-outcome data. "
        "It is not automatically a company data-readout or stock-market catalyst date."
    )

    duration = approximate_trial_duration(f)
    if not duration.empty:
        st.plotly_chart(
            px.box(
                duration, x="phase", y="approx_primary_duration_years",
                category_orders={"phase": PHASE_ORDER},
                points=False,
                title="Approximate Start-to-Primary-Completion Duration by Phase"
            ),
            width="stretch"
        )
        st.caption(
            "Approximate duration uses registry date strings; partial dates may be interpreted as the first day "
            "of the reported month/year, so use this chart for pattern-finding rather than exact duration claims."
        )

    stale = f[bool_col(f, "potential_stale_record")].copy()
    st.subheader(f"Potential stale-record review ({len(stale):,})")
    st.caption(
        "QA flag only. Prefer ClinicalTrials.gov lastKnownStatus when available; otherwise the project flags "
        "active-like studies whose completion date has passed and whose status verification is missing or older than 2 years."
    )
    if stale.empty:
        st.success("No potentially stale records in the current filter.")
    else:
        cols = [
            "nct_id","brief_title","overall_status","last_known_status","status_verified_date",
            "completion_date","last_update_post_date","stale_record_reason","lead_sponsor"
        ]
        cols = [c for c in cols if c in stale.columns]
        st.dataframe(stale[cols], width="stretch", hide_index=True)

with tab_explorer:
    st.subheader("Study Table")
    show = [
        "nct_id","brief_title","phase","phase_reporting","overall_status","lead_sponsor","lead_sponsor_class",
        "intervention_names","therapeutic_mechanism_categories","enrollment_count",
        "primary_completion_date","primary_completion_date_type","completion_date","countries"
    ]
    show = [c for c in show if c in f.columns]
    st.dataframe(f[show], width="stretch", hide_index=True)

    st.subheader("Study Detail")
    if not f.empty:
        chosen = st.selectbox("Select NCT ID", f["nct_id"].tolist())
        row = f[f["nct_id"]==chosen].iloc[0]
        a,b = st.columns(2)
        with a:
            st.markdown(f"**{row['brief_title']}**")
            st.write("Lead sponsor (registered):",row["lead_sponsor"])
            st.write("Phase:",row["phase"])
            st.write("Phase reporting:",row.get("phase_reporting",""))
            st.write("Status:",row["overall_status"])
            st.write("Therapeutic mechanism:",row.get("therapeutic_mechanism_categories",""))
            st.write("Primary completion:",row["primary_completion_date"],row["primary_completion_date_type"])
            st.link_button("Open ClinicalTrials.gov",row["ctgov_url"])
        with b:
            st.write("Status verified:",row.get("status_verified_date",""))
            st.write("Last known status:",row.get("last_known_status",""))
            st.write("Age:",row["minimum_age"],"to",row["maximum_age"])
            st.write("Sex:",row["sex"])
            st.write("Countries:",row["countries"])
            st.write("Enrollment:",row["enrollment_count"],row["enrollment_type"])
            st.write("Last update:",row["last_update_post_date"])

        st.markdown("#### Interventions")
        st.dataframe(
            interventions[interventions["nct_id"]==chosen],
            width="stretch", hide_index=True
        )

        st.markdown("#### Primary outcomes")
        st.dataframe(
            outcomes[outcomes["nct_id"]==chosen],
            width="stretch", hide_index=True
        )

        st.markdown("#### Inclusion summary")
        st.write(row["inclusion_summary"] or "(not parsed)")
        st.markdown("#### Exclusion summary")
        st.write(row["exclusion_summary"] or "(not parsed)")

        with st.expander("Full eligibility criteria"):
            st.text(row["eligibility_criteria"])

        st.markdown("#### Research questions")
        st.markdown(
            "- What exactly is the intervention and what is the evidence for its proposed mechanism?\n"
            "- Is the phase API-reported, not applicable, or missing?\n"
            "- Is the sponsor name a registered entity string or a normalized corporate group? (Here: registered string.)\n"
            "- Is the primary endpoint clinical, functional, biomarker-based, or a surrogate?\n"
            "- Does eligibility enrich for a biological subtype or disease stage?\n"
            "- Is the primary-completion date ACTUAL or ESTIMATED?\n"
            "- If the mechanism is unclassified, is this a rule gap, an alias, sparse metadata, or something genuinely novel?"
        )
