# Alzheimer's Disease Clinical Trial Competitive Landscape

> A reproducible Python pipeline and interactive dashboard for exploring the Alzheimer's disease clinical-trial landscape using ClinicalTrials.gov API v2.

**Current version: `v0.2.0`**

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
        鈫?Interventional studies
        鈫?Therapeutic candidates
        鈫?Active therapeutic candidates
        鈫?Industry-oriented competitive landscape
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
鈹溾攢 raw/
鈹? 鈹斺攢 ctgov_alzheimer_YYYYMMDD_HHMMSS.json
鈹?鈹斺攢 processed/
   鈹溾攢 studies.csv
   鈹溾攢 interventions.csv
   鈹溾攢 primary_outcomes.csv
   鈹溾攢 locations.csv
   鈹溾攢 changes.csv
   鈹溾攢 pipeline_view.csv
   鈹溾攢 data_quality.csv
   鈹溾攢 run_metadata.json
   鈹溾攢 alzheimer_trials.xlsx
   鈹斺攢 alzheimer_trials.sqlite

output/
鈹斺攢 ad_competitive_landscape.html
```

Generated datasets and reports are intentionally excluded from Git version control.

---

## Installation

Python `3.10+` is recommended.

### Option 1 鈥?Existing environment

```powershell
git clone <YOUR_REPOSITORY_URL>
cd ad-clinical-landscape

python -m pip install -e .
```

### Option 2 鈥?Conda

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
鈹?鈹溾攢 .github/
鈹? 鈹溾攢 ISSUE_TEMPLATE/
鈹? 鈹斺攢 workflows/
鈹?鈹溾攢 config/
鈹? 鈹溾攢 alzheimer.yml
鈹? 鈹溾攢 mechanisms.yml
鈹? 鈹斺攢 mechanism_overrides.csv
鈹?鈹溾攢 docs/
鈹? 鈹溾攢 data_dictionary.md
鈹? 鈹溾攢 thinking_guide.md
鈹? 鈹溾攢 research_workflow.md
鈹? 鈹斺攢 project_management.md
鈹?鈹溾攢 notebooks/
鈹?鈹溾攢 scripts/
鈹?鈹溾攢 src/
鈹? 鈹斺攢 adtrial/
鈹?    鈹溾攢 client.py
鈹?    鈹溾攢 config.py
鈹?    鈹溾攢 dashboard.py
鈹?    鈹溾攢 extract.py
鈹?    鈹溾攢 industry.py
鈹?    鈹溾攢 mechanism.py
鈹?    鈹溾攢 pipeline.py
鈹?    鈹斺攢 report.py
鈹?鈹溾攢 tests/
鈹?鈹溾攢 CHANGELOG.md
鈹溾攢 CONTRIBUTING.md
鈹溾攢 LICENSE
鈹溾攢 environment.yml
鈹溾攢 pyproject.toml
鈹斺攢 README.md
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
Phase 2 鈮?Phase 2
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
        鈫?Trial design
        鈫?Intervention / mechanism
        鈫?Primary endpoint
        鈫?Patient enrichment / biomarkers
        鈫?Sponsor / company
        鈫?Scientific readout
        鈫?Regulatory context
        鈫?Commercial positioning
        鈫?Financial context
```

A primary-completion date should be treated as a **research lead**, not automatically as a company catalyst date.

Actual readout timing should later be verified against:

- company investor relations materials,
- earnings calls,
- conference schedules,
- regulatory communications.

---

## Project roadmap

### `v0.1.x` 鈥?Stabilization

Current focus:

- reproducible collection,
- data-quality checks,
- stable dashboard,
- tests,
- documentation,
- change tracking.

### `v0.2.0` 鈥?Asset layer

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
        鈫?normalized clinical assets
```

### `v0.3.0` 鈥?Catalyst layer

Planned:

- candidate readout calendar,
- primary completion vs expected readout distinction,
- company-guided catalyst dates,
- conference / regulatory-event verification.

### `v0.4.0` 鈥?Company and financial layer

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
鈹溾攢 feature/<topic>
鈹溾攢 fix/<topic>
鈹溾攢 data/<topic>
鈹斺攢 docs/<topic>
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


---

## v0.2.0 鈥?Data semantics update

The v0.2.0 development release focuses on making dashboard interpretation more defensible.

### Phase
The dashboard now distinguishes:

- `Not Applicable` 鈥?explicitly reported as `NA` by ClinicalTrials.gov.
- `Missing / Not reported` 鈥?no phase value in the record.

### Sponsors
Lead sponsors are displayed **as registered**. The project still does not perform parent-company, subsidiary, acquisition, or fuzzy-name consolidation.

Industry collaborator classes are now extracted separately so "industry-led" can be distinguished from broader "industry-involved" research.

### Mechanisms
The mechanism landscape no longer treats all intervention rows as pharmacological mechanisms.

It now:

1. keeps drug / biological / combination-product interventions,
2. removes obvious placebo / sham / control rows,
3. applies curated and heuristic annotations,
4. reports annotation coverage,
5. sends unresolved eligible interventions to a review queue.

This makes `unclassified` an explicit data-quality/research workflow rather than a misleading dominant mechanism category.

### Timeline
Primary-completion analysis is split into:

- historical `ACTUAL` primary-completion dates,
- future `ESTIMATED` primary-completion dates for active-like studies.

The project also extracts status-verification information and flags records that may require stale-status review.

See `docs/data_semantics.md` and `docs/v0.2.0_upgrade.md`.


### v0.2.0 final-candidate refinement

The dashboard now separates the full **Intervention Landscape** from the narrower **Mechanism Landscape**. Non-drug approaches are retained and can be explored directly rather than being discarded.

