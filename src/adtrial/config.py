from copy import deepcopy
from pathlib import Path
import yaml

DEFAULT_CONFIG = {
    "api": {"base_url": "https://clinicaltrials.gov/api/v2", "timeout_seconds": 45, "page_size": 1000, "user_agent": "ad-clinical-landscape/0.1"},
    "query": {"condition": "Alzheimer Disease", "interventional_only": True, "allowed_intervention_types": [], "max_studies": None},
    "processing": {"eligibility_summary_chars": 1000, "mechanism_rules": "config/mechanisms.yml", "mechanism_overrides": "config/mechanism_overrides.csv"},
    "output": {"raw_dir": "data/raw", "processed_dir": "data/processed", "report_dir": "output", "excel_filename": "alzheimer_trials.xlsx", "sqlite_filename": "alzheimer_trials.sqlite", "html_report_filename": "ad_competitive_landscape.html"},
}

def _deep_update(base, override):
    out = deepcopy(base)
    for k, v in (override or {}).items():
        out[k] = _deep_update(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out

def load_config(path=None):
    cfg = deepcopy(DEFAULT_CONFIG)
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config not found: {p}")
        cfg = _deep_update(cfg, yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    return cfg

def resolve_path(value, project_root=None):
    p = Path(value)
    if p.is_absolute():
        return p
    return (Path(project_root or Path.cwd()) / p).resolve()
