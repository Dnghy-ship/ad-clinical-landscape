# Project Management Guide

This repository should evolve as a small research software project, not as a single script.

## Branch model

Keep it simple:

- `main`: stable, runnable version.
- `feature/<topic>`: new capability.
- `fix/<topic>`: bug fix.
- `docs/<topic>`: documentation-only change.

Examples:

```text
feature/asset-normalization
feature/catalyst-calendar
fix/dashboard-encoding
docs/research-notes
```

## Commit style

Use short, specific commits:

```text
fix: replace unsupported chart glyph
feat: add active therapeutic pipeline filter
docs: explain mechanism annotation limits
test: add sponsor normalization fixture
refactor: separate asset-level transformations
```

Avoid commits like:

```text
update
changes
final
test2
```

## Versioning

Use semantic-style versions:

- patch: bug/UI/docs only → `0.2.2` → `0.2.3`
- minor: new research capability → `0.2.x` → `0.3.0`
- major: major redesign / incompatible data model → `1.0.0`

## Before every push

Run:

```powershell
python -m unittest discover -s tests -v
git status
git diff --cached
```

Confirm that generated research data is not being committed:

```text
data/raw/*.json
data/processed/*.csv
data/processed/*.xlsx
data/processed/*.sqlite
output/*.html
```

## Suggested issue labels

Keep only a few:

- `bug`
- `enhancement`
- `research`
- `data-quality`
- `documentation`
- `good-first-issue`

## Research vs software tasks

Every planned change should be classified as one of:

### Software
Example:
- fix dashboard rendering
- improve API retry logic
- add tests

### Data quality
Example:
- normalize sponsor names
- improve mechanism mapping
- deduplicate interventions

### Research
Example:
- define what counts as a competitive therapeutic asset
- compare Phase 2 endpoint strategies
- identify upcoming readout windows

This prevents the project from becoming a collection of code changes without analytical purpose.

## Recommended roadmap

### v0.2.x — Stabilize
- UI fixes
- baseline/change tracking
- tests
- documentation
- GitHub setup

### v0.3.0 — Asset layer
- normalize intervention/asset names
- normalize sponsor/company names
- aggregate multiple NCTs into one asset
- target/mechanism taxonomy
- active pipeline table

### v0.4.0 — Catalyst layer
- candidate readout calendar
- distinguish primary-completion date from company-guided readout
- company IR verification workflow

### v0.5.0 — Financial layer
- listed-company mapping
- cash / debt / burn / runway
- licensing transactions
- market-cap / catalyst context
