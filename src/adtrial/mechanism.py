from dataclasses import dataclass
from pathlib import Path
import csv, re, yaml

@dataclass
class MechanismResult:
    category: str
    confidence: str
    matched_terms: str
    source: str

def load_rules(path):
    p = Path(path)
    if not p.exists():
        return []
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("rules", [])

def load_overrides(path):
    p = Path(path)
    if not p.exists():
        return {}
    out = {}
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("intervention_name") or "").strip().lower()
            if name:
                out[name] = {"mechanism": (row.get("mechanism") or "").strip(), "notes": (row.get("notes") or "").strip()}
    return out

def infer_mechanism(intervention, rules, overrides):
    name = str(intervention.get("name") or "").strip()
    itype = str(intervention.get("type") or "").upper()
    other = intervention.get("otherNames") or []
    if not isinstance(other, list):
        other = [str(other)]
    if name.lower() in overrides and overrides[name.lower()].get("mechanism"):
        return MechanismResult(overrides[name.lower()]["mechanism"], "curated", name, "curated_override")
    text = " ".join([name, str(intervention.get("description") or ""), *map(str, other)]).lower()
    best_cat, best_hits = None, []
    for rule in rules:
        hits = []
        for pattern in rule.get("patterns", []):
            try:
                if re.search(pattern, text, re.I):
                    hits.append(pattern)
            except re.error:
                if pattern.lower() in text:
                    hits.append(pattern)
        if len(hits) > len(best_hits):
            best_cat, best_hits = rule.get("category"), hits
    if best_cat:
        return MechanismResult(str(best_cat), "high" if len(best_hits) >= 2 else "medium", "; ".join(best_hits), "heuristic_rule")
    if itype == "DEVICE":
        return MechanismResult("Device / neuromodulation", "low", "", "type_fallback")
    if itype in {"BEHAVIORAL","OTHER"} and any(x in text for x in ["exercise","diet","cognitive","behavior","lifestyle","sleep"]):
        return MechanismResult("Behavioral / lifestyle", "low", "", "type_fallback")
    return MechanismResult("Other / unclassified", "unclassified", "", "unclassified")
