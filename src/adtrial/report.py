from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio
from .config import load_config, resolve_path

ACTIVE = {"NOT_YET_RECRUITING","RECRUITING","ENROLLING_BY_INVITATION","ACTIVE_NOT_RECRUITING"}

def _read(path):
    return pd.read_csv(path, keep_default_na=False) if Path(path).exists() else pd.DataFrame()

def build_report(config_path="config/alzheimer.yml", project_root=None):
    root = Path(project_root or Path.cwd()).resolve()
    cfg = load_config(config_path)
    processed = resolve_path(cfg["output"]["processed_dir"], root)
    out_dir = resolve_path(cfg["output"]["report_dir"], root)
    out_dir.mkdir(parents=True, exist_ok=True)
    studies = _read(processed/"studies.csv")
    interventions = _read(processed/"interventions.csv")
    locations = _read(processed/"locations.csv")
    if studies.empty:
        raise RuntimeError("No processed studies found. Run `adtrial collect` first.")

    figs = []
    status = studies["overall_status"].value_counts().rename_axis("Status").reset_index(name="Trials")
    figs.append(px.bar(status, x="Status", y="Trials", title="Trial Status"))

    ps = studies.groupby(["phase","overall_status"]).size().reset_index(name="Trials")
    figs.append(px.bar(ps, x="phase", y="Trials", color="overall_status", barmode="stack", title="Phase by Status"))

    sponsors = studies["lead_sponsor"].replace("","Unknown").value_counts().head(15).rename_axis("Sponsor").reset_index(name="Trials").sort_values("Trials")
    figs.append(px.bar(sponsors, x="Trials", y="Sponsor", orientation="h", title="Top 15 Lead Sponsors"))

    if not interventions.empty:
        mech = interventions["mechanism_category"].replace("","Other / unclassified").value_counts().rename_axis("Mechanism").reset_index(name="Interventions").sort_values("Interventions")
        figs.append(px.bar(mech, x="Interventions", y="Mechanism", orientation="h", title="Mechanism Classification (Intervention-Level)"))

    comp = studies.copy()
    comp["completion_dt"] = pd.to_datetime(comp["primary_completion_date"], errors="coerce")
    comp = comp.dropna(subset=["completion_dt"])
    if not comp.empty:
        comp["Quarter"] = comp["completion_dt"].dt.to_period("Q").astype(str)
        tl = comp.groupby(["Quarter","overall_status"]).size().reset_index(name="Trials").sort_values("Quarter")
        figs.append(px.bar(tl, x="Quarter", y="Trials", color="overall_status", barmode="stack", title="Primary Completion Timeline"))

    if not locations.empty:
        countries = locations[locations["country"]!=""].groupby("country")["nct_id"].nunique().sort_values(ascending=False).head(30).rename_axis("Country").reset_index(name="Trials")
        if not countries.empty:
            figs.append(px.choropleth(countries, locations="Country", locationmode="country names", color="Trials", hover_name="Country", title="Trial Geographic Footprint"))

    active_count = int(studies["overall_status"].isin(ACTIVE).sum())
    industry_count = int((studies["lead_sponsor_class"]=="INDUSTRY").sum())
    phase3_count = int(studies["phase"].str.contains("Phase 3", na=False).sum())
    country_set = set()
    for value in studies["countries"].astype(str):
        country_set.update(x.strip() for x in value.split(";") if x.strip())

    cards = f"""
    <div class="cards">
      <div class="card"><div class="value">{len(studies):,}</div><div>Total interventional studies</div></div>
      <div class="card"><div class="value">{active_count:,}</div><div>Active / recruiting</div></div>
      <div class="card"><div class="value">{industry_count:,}</div><div>Industry-led studies</div></div>
      <div class="card"><div class="value">{phase3_count:,}</div><div>Phase 3 records</div></div>
      <div class="card"><div class="value">{len(country_set):,}</div><div>Countries</div></div>
    </div>
    """

    cols = ["nct_id","brief_title","phase","overall_status","lead_sponsor","mechanism_categories","primary_completion_date","completion_date","countries"]
    table = studies[cols].head(250).to_html(index=False, escape=True, classes="data-table")
    charts = "\n".join(pio.to_html(fig, full_html=False, include_plotlyjs=False) for fig in figs)

    out = out_dir/cfg["output"]["html_report_filename"]
    out.write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>AD Clinical Trial Landscape</title>
<script src="https://cdn.plot.ly/plotly-3.1.0.min.js"></script>
<style>
body{{font-family:Arial,sans-serif;margin:26px;color:#222}} .note{{color:#555;max-width:1100px;line-height:1.5}}
.cards{{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0 24px}} .card{{border:1px solid #ddd;border-radius:12px;padding:14px 18px;min-width:155px}}
.value{{font-size:28px;font-weight:700}} .data-table{{border-collapse:collapse;width:100%;font-size:12px}}
.data-table th,.data-table td{{border:1px solid #ddd;padding:6px;vertical-align:top}} .data-table th{{background:#f6f6f6}}
</style></head><body>
<h1>Alzheimer's Disease Clinical Trial Competitive Landscape</h1>
<p class="note">Source: ClinicalTrials.gov API v2. Mechanism categories are curated/heuristic project annotations and are not a native standardized pharmacology field. Verify important assets manually before scientific, clinical, or investment use.</p>
{cards}{charts}<h2>Study Table (first 250 rows)</h2>{table}</body></html>""", encoding="utf-8")
    return out
