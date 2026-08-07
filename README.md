# Alzheimer's Disease Clinical Trial Competitive Landscape

> A reproducible Python pipeline and interactive dashboard for exploring the Alzheimer's disease clinical-trial landscape using ClinicalTrials.gov API v2.

**Current public version: `v0.1.0`**

This project is designed as a learning and research platform at the intersection of **biomedical informatics, pharmaceutical industry intelligence, and healthcare investment research**.

It does not attempt to produce an investment recommendation. Its first goal is to build a clean, reproducible **clinical-trial intelligence layer** that can later support asset-level, catalyst, company, and financial analysis.

---

## Why this project?

A search for Alzheimer's disease on ClinicalTrials.gov returns a broad research universe that includes:

- drug and biological interventions,
- devices and neuromodulation,
- behavioral and lifestyle studies,
- academic exploratory studies,
- completed or terminated historical trials,
- industry-sponsored therapeutic development.

For industry-oriented research, these studies should not all be interpreted in the same way.

This project therefore separates:

```text
ClinicalTrials.gov records
        ↓
Interventional studies
        ↓
Therapeutic candidates
        ↓
Active therapeutic candidates
        ↓
Industry-oriented competitive landscape
```

The project is intentionally built so that the analytical definition of a "competitive therapeutic pipeline" remains explicit and can be improved over time.

---

## Research questions

The current version is designed to help explore questions such as:

1. Which therapeutic mechanisms are most represented in active Alzheimer's trials?
2. Which mechanisms are moving into Phase 2 and Phase 3 development?
3. Which organizations are the most active lead sponsors?
4. How different is the overall clinical-research universe from the active industry therapeutic pipeline?
5. Which primary endpoints are commonly used in current trials?
6. Where are future primary-completion dates clustered?
7. Which studies deserve deeper asset-level investigation?

The dashboard should be treated as a **question-generation tool**, not as a source of automatic conclusions.

---

## Current capabilities

### ClinicalTrials.gov API collection

The pipeline uses ClinicalTrials.gov API v2 and supports:

- automatic pagination,
- retry handling,
- raw JSON snapshots,
- configurable query settings,
- full and partial/smoke-test runs.

Default condition query:

```text
Alzheimer Disease
```

The current processing pipeline retains interventional studies for downstream analysis.

---

### Structured study extraction

The project extracts:

- NCT ID
- study title
- study type
- phase
- recruitment status
- lead sponsor
- sponsor class
- collaborators
- interventions
- enrollment
- study design
- age / sex eligibility
- full eligibility criteria
- primary outcomes
- study locations
- countries
- primary completion date
- study completion date
- ClinicalTrials.gov update date

Because one study can contain multiple interventions, outcomes, and locations, these are also stored as separate long-format tables.

---

### Therapeutic pipeline view

The project currently defines a preliminary therapeutic candidate using:

```text
Intervention type:
DRUG / BIOLOGICAL / COMBINATION_PRODUCT

AND

Primary purpose:
TREATMENT / PREVENTION
```

An **active therapeutic candidate** must additionally have an active trial status such as:

```text
RECRUITING
NOT_YET_RECRUITING
ACTIVE_NOT_RECRUITING
ENROLLING_BY_INVITATION
```

This is a **project-defined analytical rule**, not an official ClinicalTrials.gov classification.

Future versions will move from study-level filtering toward true **asset-level normalization**.

---

## Mechanism annotation

ClinicalTrials.gov provides structured intervention information such as:

- intervention type,
- intervention name,
- description,
- other names.

However, it does not provide a single standardized pharmacology field that is sufficient for competitive-landscape analysis.

This project therefore maintains a separate annotation layer:

```text
mechanism_category
mechanism_confidence
mechanism_matched_terms
mechanism_source
```

Annotation sources currently include:

### Curated overrides

```text
config/mechanism_overrides.csv
```

These are manually reviewed mappings and receive the highest priority.

### Heuristic rules

```text
config/mechanisms.yml
```

These use keywords / regular expressions to provide a first-pass classification.

Example categories include:

- Amyloid-beta targeting
- Tau targeting
- Neuroinflammation / microglia
- APOE / lipid metabolism
- Metabolic / insulin / GLP-1
- Synaptic / neuroprotective
- Gene / cell therapy
- Device / neuromodulation
- Behavioral / lifestyle

Mechanism annotations should always be interpreted together with:

```text
mechanism_source
mechanism_confidence
```

Important assets should be manually verified against primary scientific, regulatory, and company sources before being used in formal research.

---

## Interactive dashboard

Launch the Streamlit dashboard with:

```powershell
python -m adtrial dashboard
```

The dashboard provides three research presets:

```text
All interventional studies
Active therapeutics
Industry active therapeutics
```

Available filters include:

- recruitment status,
- phase,
- sponsor class,
- lead sponsor,
- mechanism,
- country,
- free-text search.

Current visualizations include:

- Phase by Status
- Top Lead Sponsors
- Mechanism Landscape
- Primary Completion Timeline
- Geographic Footprint

Individual study pages expose:

- interventions,
- mechanism annotations,
- primary outcomes,
- eligibility criteria,
- enrollment,
- completion dates,
- ClinicalTrials.gov links.

---

## Data-quality monitoring

The pipeline produces:

```text
data_quality.csv
```

Current checks include:

- missing sponsor information,
- missing primary outcomes,
- missing completion dates,
- unclassified mechanisms,
- curated vs heuristic mechanism coverage,
- therapeutic candidate counts.

This is important because the objective is not only to generate visualizations, but also to understand the reliability of the analytical layer behind them.

---

## Change tracking

A full data run can act as a baseline.

Subsequent full runs compare against the previous processed dataset and generate:

```text
changes.csv
```

Current tracked changes include:

- new studies,
- recruitment-status changes,
- phase changes,
- primary-completion date changes,
- study-completion date changes,
- ClinicalTrials.gov update-date changes.

Partial smoke-test runs are written separately and do **not** overwrite the full baseline.

---

## Output files

A full run generates:

```text
data/
├─ raw/
│  └─ ctgov_alzheimer_YYYYMMDD_HHMMSS.json
│
└─ processed/
   ├─ studies.csv
   ├─ interventions.csv
   ├─ primary_outcomes.csv
   ├─ locations.csv
   ├─ changes.csv
   ├─ pipeline_view.csv
   ├─ data_quality.csv
   ├─ run_metadata.json
   ├─ alzheimer_trials.xlsx
   └─ alzheimer_trials.sqlite

output/
└─ ad_competitive_landscape.html
```

Generated datasets and reports are intentionally excluded from Git version control.

---

## Installation

Python `3.10+` is recommended.

### Option 1 — Existing environment

```powershell
git clone <YOUR_REPOSITORY_URL>
cd ad-clinical-landscape

python -m pip install -e .
```

### Option 2 — Conda

```powershell
conda env create -f environment.yml
conda activate ad_trials
```

---

## Environment check

```powershell
python -m adtrial doctor
```

This checks:

- Python version,
- active interpreter,
- required packages,
- ClinicalTrials.gov API connectivity,
- API version and data timestamp.

---

## Tests

Offline unit tests:

```powershell
python -m unittest discover -s tests -v
```

Tests use local fixtures and do not require ClinicalTrials.gov network access.

GitHub Actions also runs the test suite automatically on pushes and pull requests.

---

## Recommended first run

Start with a partial smoke test:

```powershell
python -m adtrial collect --max-studies 100
```

Partial results are isolated from the full research baseline.

Then run the full pipeline:

```powershell
python -m adtrial all
```

Generate / refresh the HTML report:

```powershell
python -m adtrial report
```

Launch the dashboard:

```powershell
python -m adtrial dashboard
```

---

## Repository structure

```text
ad-clinical-landscape/
│
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  └─ workflows/
│
├─ config/
│  ├─ alzheimer.yml
│  ├─ mechanisms.yml
│  └─ mechanism_overrides.csv
│
├─ docs/
│  ├─ data_dictionary.md
│  ├─ thinking_guide.md
│  ├─ research_workflow.md
│  └─ project_management.md
│
├─ notebooks/
│
├─ scripts/
│
├─ src/
│  └─ adtrial/
│     ├─ client.py
│     ├─ config.py
│     ├─ dashboard.py
│     ├─ extract.py
│     ├─ industry.py
│     ├─ mechanism.py
│     ├─ pipeline.py
│     └─ report.py
│
├─ tests/
│
├─ CHANGELOG.md
├─ CONTRIBUTING.md
├─ LICENSE
├─ environment.yml
├─ pyproject.toml
└─ README.md
```

---

## How to think with the data

Counts alone are not conclusions.

For example, a mechanism with many active trials may represent:

- stronger biological validation,
- greater commercial interest,
- a mature and crowded competitive field.

A mechanism with few trials may represent:

- differentiation,
- weak biological validation,
- or technical difficulty.

Similarly:

```text
Phase 2 ≠ Phase 2
```

Two Phase 2 studies may differ substantially in:

- sample size,
- biomarker enrichment,
- randomization,
- comparator,
- treatment duration,
- primary endpoint,
- geographical scope,
- sponsor capabilities.

The dashboard is therefore intended to guide deeper study-level and asset-level research.

---

## Suggested research workflow

For a study that looks important:

```text
ClinicalTrials.gov
        ↓
Trial design
        ↓
Intervention / mechanism
        ↓
Primary endpoint
        ↓
Patient enrichment / biomarkers
        ↓
Sponsor / company
        ↓
Scientific readout
        ↓
Regulatory context
        ↓
Commercial positioning
        ↓
Financial context
```

A primary-completion date should be treated as a **research lead**, not automatically as a company catalyst date.

Actual readout timing should later be verified against:

- company investor relations materials,
- earnings calls,
- conference schedules,
- regulatory communications.

---

## Project roadmap

### `v0.1.x` — Stabilization

Current focus:

- reproducible collection,
- data-quality checks,
- stable dashboard,
- tests,
- documentation,
- change tracking.

### `v0.2.0` — Asset layer

Planned:

- intervention / drug-name normalization,
- aliases and development-code mapping,
- sponsor / company normalization,
- multiple NCTs aggregated into one asset,
- target taxonomy,
- standardized mechanism taxonomy,
- highest active phase,
- active asset-level pipeline table.

Target structure:

```text
NCT-level studies
        ↓
normalized clinical assets
```

### `v0.3.0` — Catalyst layer

Planned:

- candidate readout calendar,
- primary completion vs expected readout distinction,
- company-guided catalyst dates,
- conference / regulatory-event verification.

### `v0.4.0` — Company and financial layer

Planned:

- listed-company mapping,
- ticker / exchange,
- cash and short-term investments,
- debt,
- R&D spending,
- cash burn,
- estimated runway,
- licensing transactions,
- market context.

---

## Project management

Development follows a lightweight Git workflow:

```text
main
├─ feature/<topic>
├─ fix/<topic>
├─ data/<topic>
└─ docs/<topic>
```

Examples:

```text
feature/asset-normalization
data/sponsor-normalization
fix/dashboard-filter
docs/research-methodology
```

Before merging changes into `main`:

```powershell
python -m unittest discover -s tests -v
git status
git diff
```

Stable versions are tagged using:

```text
v0.1.0
v0.1.1
v0.2.0
...
```

See:

```text
CONTRIBUTING.md
docs/project_management.md
```

for the detailed workflow.

---

## Limitations

This project currently has several deliberate limitations:

1. ClinicalTrials.gov is a registry, not a standardized pharmaceutical asset database.
2. Mechanism annotations are partly heuristic.
3. Sponsor names have not yet been fully normalized to corporate entities.
4. One therapeutic asset may appear in multiple NCT records.
5. Trial phase alone does not measure asset quality.
6. Primary-completion dates are not guaranteed readout dates.
7. Clinical data alone is insufficient for commercial or investment conclusions.

These limitations define the next stages of the project rather than being hidden assumptions.

---

## Disclaimer

This repository is intended for educational, research, and data-engineering purposes.

It is **not medical advice and not investment advice**.

ClinicalTrials.gov records should be verified against primary trial, scientific, regulatory, and company sources before being used for high-stakes decisions.

---

## License

MIT License.
