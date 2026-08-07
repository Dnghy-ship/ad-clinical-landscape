# Contributing

This is a learning/research project for clinical-trial competitive-landscape analysis.

## Principles

1. Keep ClinicalTrials.gov raw fields separate from project-derived annotations.
2. Any mechanism/target classification should expose its provenance.
3. Do not commit downloaded raw snapshots or generated outputs.
4. Add an offline fixture/test when changing parsing logic.
5. Prefer reproducible transformations over manual spreadsheet edits.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

For a partial API smoke test:

```bash
python -m adtrial collect --max-studies 100
```

Partial runs are written under `data/smoke/` and do not overwrite the full baseline.
