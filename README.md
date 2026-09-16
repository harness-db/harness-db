# HARNESS-DB

A coded, evidence-backed dataset of LLM agent harnesses (2022–2026), built for the systematic review
*The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026*.

Private during construction. Public release is planned alongside arXiv v1.

## Layout

```
schema/dimensions.json        the coding sheet: 9 layers, 38 dimensions, allowed values, crosswalk (hand-edited)
schema/harness_db.schema.json JSON Schema generated from dimensions.json (do not edit)
data/systems.json             one object per harness, every dimension coded with evidence
data/papers.csv               bibliographic rows, inclusion decisions, exclusion reasons
data/results.csv              reported scores per system, model, benchmark, split
data/prisma_counts.json       numbers for the PRISMA 2020 flow diagram
data/raw/                     harvested candidates per source, never hand-edited
data/screening/               Rayyan exports, LLM votes, kappa reports
data/prefill/                 subagent pre-fill per system, before human verification
docs/                         protocol (PRISMA-P), coding manual, positioning memo, schema changelog
scripts/                      build_schema, validate, kappa; harvest, screening, prefill, analysis (see scripts/README.md)
explorer/                     single-file static explorer (release phase)
paper/                        manuscript and figures
tests/                        schema and script tests
```

## Quickstart

```
pip install -e ".[dev]"
python scripts/build_schema.py          # regenerate the JSON Schema after editing dimensions.json
python scripts/validate.py              # schema + referential integrity + evidence per cell
python scripts/kappa.py votes data/screening/votes.csv --a screener1 --b screener2
python scripts/kappa.py coding data/coding/c1 data/coding/c2
pytest -q
```

CI runs the schema freshness check, the validator, and the tests on every push and pull request.

## Coding rules in one paragraph

Every system is coded on every dimension. A cell is either `not_reported: true`, or it has a
value, a non-empty `evidence` string (verbatim quote with section, URL, or `path:line@commit`),
and a `confidence`. Humans are the coders of record; subagent pre-fill is verified cell by cell.
See `docs/coding_manual.md` and `CONTRIBUTING.md`.

## Licensing

| What | License | File |
|---|---|---|
| Code: scripts, validator, explorer, CI | MIT | [`LICENSE-CODE`](LICENSE-CODE) |
| Data and documentation: `data/`, `schema/`, `docs/`, coding manual | CC BY 4.0 | [`LICENSE-DATA`](LICENSE-DATA) |

## Citation

See [`CITATION.cff`](CITATION.cff). BibTeX will be added at release.
