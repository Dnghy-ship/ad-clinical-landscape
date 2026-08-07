from datetime import datetime, timezone
from pathlib import Path
import json, sqlite3
import pandas as pd
from .client import CTGovClient
from .config import load_config, resolve_path
from .extract import parse_study
from .mechanism import load_rules, load_overrides
from .industry import is_therapeutic_candidate, is_active_therapeutic_candidate

STUDY_COLUMNS = ["nct_id","brief_title","official_title","study_type","phase","phase_raw","overall_status","has_results",
"lead_sponsor","lead_sponsor_class","collaborators","conditions","keywords","intervention_names","intervention_types",
"mechanism_categories","enrollment_count","enrollment_type","allocation","intervention_model","primary_purpose","masking",
"minimum_age","maximum_age","sex","healthy_volunteers","std_ages","eligibility_criteria","inclusion_summary","exclusion_summary",
"primary_outcome_measures","primary_outcome_timeframes","countries","country_count","site_count","start_date","start_date_type",
"primary_completion_date","primary_completion_date_type","completion_date","completion_date_type","study_first_post_date",
"last_update_post_date","brief_summary","ctgov_url"]
INTERVENTION_COLUMNS = ["nct_id","intervention_index","intervention_type","intervention_name","description","other_names",
"arm_group_labels","mechanism_category","mechanism_confidence","mechanism_matched_terms","mechanism_source"]
OUTCOME_COLUMNS = ["nct_id","outcome_index","measure","description","time_frame"]
LOCATION_COLUMNS = ["nct_id","location_index","facility","location_status","city","state","zip","country","latitude","longitude"]

def _df(rows, columns):
    df = pd.DataFrame(rows)
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns]

def _allowed(srow, irows, cfg):
    q = cfg["query"]
    if q.get("interventional_only") and srow.get("study_type") != "INTERVENTIONAL":
        return False
    allowed = {str(x).upper() for x in (q.get("allowed_intervention_types") or [])}
    if allowed:
        types = {str(r.get("intervention_type","")).upper() for r in irows}
        return bool(types & allowed)
    return True

def _changes(previous, current):
    cols = ["nct_id","change_type","field","old_value","new_value","detected_at_utc"]
    if previous is None or previous.empty:
        return pd.DataFrame(columns=cols)
    prev, curr = previous.set_index("nct_id", drop=False), current.set_index("nct_id", drop=False)
    now, rows = datetime.now(timezone.utc).isoformat(), []
    for nct in curr.index.difference(prev.index):
        rows.append({"nct_id":nct,"change_type":"NEW_STUDY","field":"","old_value":"","new_value":"","detected_at_utc":now})
    for nct in curr.index.intersection(prev.index):
        for field in ["overall_status","phase","primary_completion_date","completion_date","last_update_post_date"]:
            old = "" if pd.isna(prev.at[nct,field]) else str(prev.at[nct,field])
            new = "" if pd.isna(curr.at[nct,field]) else str(curr.at[nct,field])
            if old != new:
                rows.append({"nct_id":nct,"change_type":"FIELD_CHANGED","field":field,"old_value":old,"new_value":new,"detected_at_utc":now})
    return pd.DataFrame(rows, columns=cols)

def _write_excel(path, tables):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in tables.items():
            sheet = sheet[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)
            ws = writer.book[sheet]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                values = ["" if c.value is None else str(c.value) for c in list(col)[:150]]
                ws.column_dimensions[col[0].column_letter].width = min(max([len(x) for x in values] + [8]) + 2, 50)

def _write_sqlite(path, tables):
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as con:
        for name, df in tables.items():
            df.to_sql(name, con, index=False, if_exists="replace")
        con.execute("CREATE INDEX IF NOT EXISTS idx_studies_nct ON studies(nct_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_interventions_nct ON interventions(nct_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_nct ON primary_outcomes(nct_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_locations_nct ON locations(nct_id)")


def _quality_table(studies, interventions):
    rows = []
    def add(metric, value, note=""):
        rows.append({"metric": metric, "value": int(value), "note": note})

    add("studies_total", len(studies))
    if len(studies):
        add("studies_missing_sponsor", (studies["lead_sponsor"].astype(str).str.strip() == "").sum())
        add("studies_missing_primary_outcome", (studies["primary_outcome_measures"].astype(str).str.strip() == "").sum())
        add("studies_missing_completion_date", (studies["completion_date"].astype(str).str.strip() == "").sum())
        add("studies_unclassified_mechanism", studies["mechanism_categories"].astype(str).str.contains("Other / unclassified", regex=False).sum())
        add("therapeutic_candidates", studies["therapeutic_candidate"].sum())
        add("active_therapeutic_candidates", studies["active_therapeutic_candidate"].sum())
    if len(interventions):
        add("interventions_total", len(interventions))
        add("interventions_curated_mechanism", (interventions["mechanism_source"] == "curated_override").sum())
        add("interventions_heuristic_mechanism", (interventions["mechanism_source"] == "heuristic_rule").sum())
        add("interventions_unclassified", (interventions["mechanism_source"] == "unclassified").sum())
    return pd.DataFrame(rows)


def collect(config_path="config/alzheimer.yml", max_studies=None, project_root=None):
    root = Path(project_root or Path.cwd()).resolve()
    cfg = load_config(config_path)

    is_partial = max_studies is not None or cfg["query"].get("max_studies") is not None

    # Partial/smoke runs no longer overwrite the canonical full baseline.
    if is_partial:
        raw_dir = resolve_path("data/smoke/raw", root)
        processed = resolve_path("data/smoke/processed", root)
    else:
        raw_dir = resolve_path(cfg["output"]["raw_dir"], root)
        processed = resolve_path(cfg["output"]["processed_dir"], root)

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    rules = load_rules(resolve_path(cfg["processing"]["mechanism_rules"], root))
    overrides = load_overrides(resolve_path(cfg["processing"]["mechanism_overrides"], root))

    prev_path = processed / "studies.csv"
    previous = None
    if (not is_partial) and prev_path.exists():
        try:
            previous = pd.read_csv(prev_path, dtype=str, keep_default_na=False)
        except Exception:
            previous = None

    client = CTGovClient(
        cfg["api"]["base_url"],
        int(cfg["api"]["timeout_seconds"]),
        cfg["api"]["user_agent"],
    )
    effective_max = max_studies if max_studies is not None else cfg["query"].get("max_studies")
    result = client.search_studies(
        cfg["query"]["condition"],
        int(cfg["api"]["page_size"]),
        effective_max,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_path = raw_dir / f"ctgov_alzheimer_{stamp}.json"
    raw_path.write_text(
        json.dumps(
            {
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "query_condition": cfg["query"]["condition"],
                "api_version": result.api_version,
                "study_count_downloaded": len(result.studies),
                "is_partial": is_partial,
                "studies": result.studies,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    sr, ir, orows, lr = [], [], [], []
    for study in result.studies:
        s, ints, outs, locs = parse_study(
            study,
            rules,
            overrides,
            int(cfg["processing"]["eligibility_summary_chars"]),
        )
        if not _allowed(s, ints, cfg):
            continue
        sr.append(s)
        ir.extend(ints)
        orows.extend(outs)
        lr.extend(locs)

    studies = _df(sr, STUDY_COLUMNS).drop_duplicates("nct_id")
    interventions = _df(ir, INTERVENTION_COLUMNS)
    outcomes = _df(orows, OUTCOME_COLUMNS)
    locations = _df(lr, LOCATION_COLUMNS)

    if not studies.empty:
        studies["therapeutic_candidate"] = studies.apply(is_therapeutic_candidate, axis=1)
        studies["active_therapeutic_candidate"] = studies.apply(is_active_therapeutic_candidate, axis=1)
        studies = studies.sort_values(["overall_status", "phase", "nct_id"], kind="stable").reset_index(drop=True)
    else:
        studies["therapeutic_candidate"] = pd.Series(dtype=bool)
        studies["active_therapeutic_candidate"] = pd.Series(dtype=bool)

    # Only compare complete runs against the previous complete baseline.
    changes = _changes(previous, studies) if not is_partial else pd.DataFrame(
        columns=["nct_id","change_type","field","old_value","new_value","detected_at_utc"]
    )

    pipeline_view = studies[
        studies["active_therapeutic_candidate"] == True
    ].copy() if not studies.empty else studies.copy()

    quality = _quality_table(studies, interventions)

    tables = {
        "studies": studies,
        "interventions": interventions,
        "primary_outcomes": outcomes,
        "locations": locations,
        "changes": changes,
        "pipeline_view": pipeline_view,
        "data_quality": quality,
    }

    csv_paths = {}
    for name, df in tables.items():
        p = processed / f"{name}.csv"
        df.to_csv(p, index=False, encoding="utf-8-sig")
        csv_paths[name] = str(p)

    excel_path = processed / cfg["output"]["excel_filename"]
    sqlite_path = processed / cfg["output"]["sqlite_filename"]
    _write_excel(excel_path, tables)
    _write_sqlite(sqlite_path, tables)

    meta = {
        "run_mode": "partial_smoke" if is_partial else "full",
        "downloaded_raw_count": len(result.studies),
        "retained_study_count": len(studies),
        "active_therapeutic_candidate_count": int(studies["active_therapeutic_candidate"].sum()) if len(studies) else 0,
        "intervention_count": len(interventions),
        "primary_outcome_count": len(outcomes),
        "location_count": len(locations),
        "change_count": len(changes),
        "raw_snapshot": str(raw_path),
        "excel": str(excel_path),
        "sqlite": str(sqlite_path),
        "csv": csv_paths,
        "api_version": result.api_version,
    }
    (processed / "run_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return meta
