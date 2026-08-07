from pathlib import Path
import os
import pandas as pd
import plotly.express as px
import streamlit as st

from adtrial.industry import country_to_iso3

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
    "ClinicalTrials.gov API v2 | Mechanism is a curated/heuristic project annotation, "
    "not a native standardized pharmacology field."
)

if studies.empty:
    st.error("No full processed data found. Run `adtrial all` first.")
    st.stop()

with st.sidebar:
    st.header("Research View")
    preset = st.radio(
        "Preset",
        ["All interventional studies", "Active therapeutics", "Industry active therapeutics"],
        index=1,
        help="Use Active Therapeutics first when thinking about the current competitive pipeline."
    )

base = studies.copy()
if preset == "Active therapeutics":
    base = base[base["active_therapeutic_candidate"].astype(str).str.lower().isin(["true","1"])]
elif preset == "Industry active therapeutics":
    base = base[
        base["active_therapeutic_candidate"].astype(str).str.lower().isin(["true","1"])
        & (base["lead_sponsor_class"] == "INDUSTRY")
    ]

with st.sidebar:
    st.header("Filters")
    def multi(label, series):
        vals = sorted(x for x in series.astype(str).unique() if x)
        return st.multiselect(label, vals)

    status_sel = multi("Status", base["overall_status"])
    phase_sel = multi("Phase", base["phase"])
    sponsor_class_sel = multi("Sponsor class", base["lead_sponsor_class"])
    sponsor_sel = multi("Lead sponsor", base["lead_sponsor"])

    mech_vals = sorted({
        x.strip()
        for v in base["mechanism_categories"].astype(str)
        for x in v.split(";")
        if x.strip()
    })
    mechanism_sel = st.multiselect("Mechanism", mech_vals)

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
    mask &= base["mechanism_categories"].apply(
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
        "intervention_names","mechanism_categories","primary_outcome_measures"
    ]
    text = base[cols].astype(str).agg(" ".join, axis=1).str.lower()
    mask &= text.str.contains(q, regex=False)

f = base[mask].copy()
selected = set(f["nct_id"])

c1,c2,c3,c4 = st.columns(4)
c1.metric("Studies", f"{len(f):,}")
c2.metric("Industry-led", f"{(f['lead_sponsor_class']=='INDUSTRY').sum():,}")
c3.metric("Recruiting", f"{(f['overall_status']=='RECRUITING').sum():,}")
c4.metric("Phase 3", f"{f['phase'].str.contains('Phase 3',na=False).sum():,}")

st.info(
    "Thinking prompt: first ask whether this view represents the current therapeutic pipeline. "
    "Then inspect mechanism crowding, sponsor concentration, trial design, and the timing of primary completion."
)

left,right = st.columns(2)
with left:
    ps = f.groupby(["phase","overall_status"]).size().reset_index(name="Trials")
    st.plotly_chart(
        px.bar(ps,x="phase",y="Trials",color="overall_status",barmode="stack",title="Phase by Status"),
        width="stretch"
    )
with right:
    sp = (
        f["lead_sponsor"].replace("","Unknown").value_counts().head(15)
        .rename_axis("Sponsor").reset_index(name="Trials").sort_values("Trials")
    )
    st.plotly_chart(
        px.bar(sp,x="Trials",y="Sponsor",orientation="h",title="Top Lead Sponsors"),
        width="stretch"
    )

left,right = st.columns(2)
with left:
    ints = interventions[interventions["nct_id"].isin(selected)]
    if not ints.empty:
        mech = (
            ints["mechanism_category"].replace("","Other / unclassified")
            .value_counts().rename_axis("Mechanism").reset_index(name="Interventions")
            .sort_values("Interventions")
        )
        st.plotly_chart(
            px.bar(mech,x="Interventions",y="Mechanism",orientation="h",title="Mechanism Landscape"),
            width="stretch"
        )
with right:
    t = f.copy()
    t["Primary completion"] = pd.to_datetime(t["primary_completion_date"],errors="coerce")
    t = t.dropna(subset=["Primary completion"])
    if not t.empty:
        t["Quarter"] = t["Primary completion"].dt.to_period("Q").astype(str)
        tt = t.groupby(["Quarter","overall_status"]).size().reset_index(name="Trials")
        st.plotly_chart(
            px.bar(tt,x="Quarter",y="Trials",color="overall_status",barmode="stack",title="Primary Completion Timeline"),
            width="stretch"
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

with st.expander("Data quality / annotation health"):
    if quality.empty:
        st.write("Run a fresh v0.2 full collection to create data_quality.csv.")
    else:
        st.dataframe(quality, width="stretch", hide_index=True)

st.subheader("Study Table")
show = [
    "nct_id","brief_title","phase","overall_status","lead_sponsor","lead_sponsor_class",
    "intervention_names","mechanism_categories","enrollment_count",
    "primary_completion_date","completion_date","countries"
]
st.dataframe(f[show], width="stretch", hide_index=True)

st.subheader("Study Detail")
if not f.empty:
    chosen = st.selectbox("Select NCT ID", f["nct_id"].tolist())
    row = f[f["nct_id"]==chosen].iloc[0]
    a,b = st.columns(2)
    with a:
        st.markdown(f"**{row['brief_title']}**")
        st.write("Sponsor:",row["lead_sponsor"])
        st.write("Phase:",row["phase"])
        st.write("Status:",row["overall_status"])
        st.write("Mechanism:",row["mechanism_categories"])
        st.write("Primary completion:",row["primary_completion_date"],row["primary_completion_date_type"])
        st.link_button("Open ClinicalTrials.gov",row["ctgov_url"])
    with b:
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
        "- Why is this study still strategically interesting at its current phase/status?\n"
        "- Is the primary endpoint clinically meaningful, or mainly a biomarker/surrogate?\n"
        "- Does eligibility enrich for a biological subtype (e.g. amyloid-positive)?\n"
        "- Is this mechanism crowded? Which sponsor/asset is closest?\n"
        "- Is the primary completion date a plausible future catalyst, or only an administrative estimate?"
    )
