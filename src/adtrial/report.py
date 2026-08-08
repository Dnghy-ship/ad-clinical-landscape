from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio

from .config import load_config, resolve_path
from .analytics import (
    PHASE_ORDER, mechanism_summary,
    historical_actual_primary_completions,
    future_estimated_primary_completions,
)

def build_report(config_path="config/alzheimer.yml", project_root=None):
    root = Path(project_root or Path.cwd()).resolve()
    cfg = load_config(config_path)
    processed = resolve_path(cfg["output"]["processed_dir"], root)
    out_dir = resolve_path(cfg["output"]["report_dir"], root)
    out_dir.mkdir(parents=True, exist_ok=True)

    studies = pd.read_csv(processed/"studies.csv", keep_default_na=False)
    interventions = pd.read_csv(processed/"interventions.csv", keep_default_na=False)

    figs = []

    ps = studies.groupby(["phase","overall_status"]).size().reset_index(name="Trials")
    figs.append(px.bar(
        ps, x="phase", y="Trials", color="overall_status", barmode="stack",
        category_orders={"phase": PHASE_ORDER}, title="Phase by Status"
    ))

    sponsors = (
        studies["lead_sponsor"].replace("","Unknown").value_counts().head(15)
        .rename_axis("Sponsor").reset_index(name="Trials").sort_values("Trials")
    )
    figs.append(px.bar(
        sponsors, x="Trials", y="Sponsor", orientation="h",
        title="Top Lead Sponsors (as registered)"
    ))

    _, mech, stats = mechanism_summary(interventions)
    if not mech.empty:
        figs.append(px.bar(
            mech.sort_values("Interventions"), x="Interventions", y="Mechanism",
            orientation="h",
            title=f"Therapeutic Mechanism Landscape — classified ({stats['coverage_pct']:.1f}% coverage)"
        ))

    hist = historical_actual_primary_completions(studies)
    if not hist.empty:
        h = hist.groupby(["quarter","overall_status"]).size().reset_index(name="Trials")
        figs.append(px.bar(
            h, x="quarter", y="Trials", color="overall_status", barmode="stack",
            title="Historical Primary Completions — ACTUAL"
        ))

    future = future_estimated_primary_completions(studies)
    if not future.empty:
        fu = future.groupby(["quarter","overall_status"]).size().reset_index(name="Trials")
        figs.append(px.bar(
            fu, x="quarter", y="Trials", color="overall_status", barmode="stack",
            title="Future Candidate Primary Completions — ESTIMATED + active"
        ))

    industry_count = int((studies["lead_sponsor_class"]=="INDUSTRY").sum())
    recruiting_count = int((studies["overall_status"]=="RECRUITING").sum())
    phase3_count = int(studies["phase"].str.contains("Phase 3", na=False).sum())

    cards = f"""
    <div style="display:flex;gap:20px;flex-wrap:wrap;margin:18px 0;">
      <div class="card"><div class="value">{len(studies):,}</div><div>Studies</div></div>
      <div class="card"><div class="value">{industry_count:,}</div><div>Industry-led</div></div>
      <div class="card"><div class="value">{recruiting_count:,}</div><div>Recruiting</div></div>
      <div class="card"><div class="value">{phase3_count:,}</div><div>Phase 3 records</div></div>
      <div class="card"><div class="value">{stats['coverage_pct']:.1f}%</div><div>Mechanism coverage</div></div>
    </div>
    """

    parts = [
        "<html><head><meta charset='utf-8'><title>AD Clinical Landscape</title>",
        """<style>
        body{font-family:Arial,sans-serif;max-width:1500px;margin:30px auto;padding:0 20px;color:#222}
        .card{border:1px solid #ddd;border-radius:10px;padding:14px 20px;min-width:150px}
        .value{font-size:28px;font-weight:700}
        .note{background:#f5f7fb;padding:14px;border-radius:8px}
        </style></head><body>""",
        "<h1>Alzheimer's Disease Clinical Trial Competitive Landscape</h1>",
        "<p class='note'>Lead sponsors are exact registered strings; mechanism is a project-derived annotation. "
        "Mechanism counts exclude obvious controls and non-therapeutic interventions. "
        "Future completion chart uses ESTIMATED primary-completion dates with active-like statuses.</p>",
        cards,
    ]
    for fig in figs:
        parts.append(pio.to_html(fig, full_html=False, include_plotlyjs="cdn"))

    cols = [
        "nct_id","brief_title","phase","overall_status","lead_sponsor",
        "therapeutic_mechanism_categories","primary_completion_date",
        "primary_completion_date_type","completion_date","countries"
    ]
    cols = [c for c in cols if c in studies.columns]
    parts.append("<h2>Study table (first 250)</h2>")
    parts.append(studies[cols].head(250).to_html(index=False, escape=True))
    parts.append("</body></html>")

    out = out_dir/cfg["output"]["html_report_filename"]
    out.write_text("\n".join(parts), encoding="utf-8")
    return out
