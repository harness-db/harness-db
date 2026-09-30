# HARNESS-DB

> Private during construction; the public release is planned alongside arXiv v1.

[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-blue)](LICENSE-DATA)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue)](LICENSE-CODE)
[![Dataset 1.0.0](https://img.shields.io/badge/dataset-1.0.0-informational)](CITATION.cff)
[![validate](https://github.com/harness-db/harness-db/actions/workflows/validate.yml/badge.svg)](https://github.com/harness-db/harness-db/actions/workflows/validate.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23031354.svg)](https://doi.org/10.5281/zenodo.23031354)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-pending-lightgrey)](DATASET_CARD.md)
[![Pre-registered](https://img.shields.io/badge/pre--registered-osf.io%2Fab2wn-green)](https://osf.io/ab2wn)

HARNESS-DB is a dataset of LLM agent harnesses: the software between a language model and a task
environment that assembles the model's input, runs the actions it chooses, and decides whether to
continue. It codes **1,256 systems** from 2022 to 2026 on **38 design dimensions** in nine layers,
**47,728 cells** in all. Every cell holds either a value backed by a verbatim quote and a locator you
can re-open (a file, usually with a line, at a pinned commit, or a paper section) or an explicit `not_reported`.
What the cells show:

- **48.9% of cells are documented silence.** The sources were read, and they do not say.
- **The least-described layers govern safe deployment.** Weighted to the field, 81.6% of sandbox and
  environment cells are not reported, against 24.9% for the control loop.
- **Silence counted as a value creates associations that are not there.** 265 of 666 dimension
  pairs test as associated only when `not_reported` is treated as a category.

If you build, compare or study agent harnesses, you can query this table and check any cell in it
against its source.

## Quickstart

```bash
git clone https://github.com/harness-db/harness-db && pip install -e ./harness-db
```

```python
import harnessdb as hdb
db = hdb.load()                                        # inside the clone; or hdb.load("harness-db-1.0.0/")
db.not_reported(by="layer")                            # silence per layer, unweighted and field-weighted, with SEs
db.evidence("mini-swe-agent", "execution_isolation")   # the value, quote and locator behind one cell
```

`db.cells` is the long table (one row per system and dimension), `db.wide()` has one row per system,
`db.systems` carries stratum and sampling weight, and `db.to_hf()` returns a Hugging Face
`DatasetDict`. Outside a clone, point `hdb.load()` at an unzipped release or set `HARNESSDB_DATA`.

## The nine layers

| Layer | What it covers | Dimensions | Not reported, field-weighted |
|---|---|---:|---:|
| A. Context assembly | What the model sees each turn: system prompt, repository or environment context, compaction, observation format | 4 | 40.2% |
| B. Tool interface | How actions are expressed: call format, tool count, edit primitive, schema source, protocols (MCP, A2A) | 5 | 71.4% |
| C. Control loop | Loop primitives (ReAct, plan-execute, tree search, ...), planning, multi-agent topology, delegation, human in the loop | 5 | 24.9% |
| D. Memory and state | Short-term state, long-term memory, persistence and resume | 3 | 63.3% |
| E. Verification and repair | Self-verification, retry policy, rollback | 3 | 60.9% |
| F. Budget and termination | Termination conditions, cost controls, timeouts | 3 | 65.1% |
| G. Sandbox and environment | Execution isolation, filesystem access, network policy, permission model | 4 | 81.6% |
| H. Observability and governance | Tracing, replayability, evaluation hooks, guardrails | 4 | 72.8% |
| M. Meta | Target domain, open source, model-agnostic, primary artifact, first release, pinned version, stars | 7 | 34.6% |

Every dimension, with its allowed values, is in [`schema/dimensions.json`](schema/dimensions.json)
(schema 1.0.0, frozen). The definition of each value and the coding rules are in
[`docs/coding_manual.md`](docs/coding_manual.md). The crosswalk to earlier taxonomies is in the schema.

## What a cell is

One real cell: mini-swe-agent, dimension G1 `execution_isolation`, as stored in `data/systems.json`
(the `coder` and `note` fields are omitted here):

```json
{
  "value": "subprocess",
  "evidence": "\"By default, actions are executed as `subprocess.run`, i.e., every action is independent of the previous ones.\" (docs/faq.md@a83fcae)",
  "confidence": "high",
  "not_reported": false
}
```

The evidence string is the verbatim **quote** followed by its **locator** in parentheses: here the
file `docs/faq.md` at commit `a83fcae`, which is the system's pinned version (`v2.4.6`). The release's
`cells.csv` and the loader split the two into separate columns. Every cell is in exactly one of three
states:

| State | Cells | Meaning |
|---|---:|---|
| coded value | 24,228 (50.8%) | A value with a quote, a locator and a confidence (`high`, `medium`, `low`). A value such as `none` is a coded finding: the place where the feature would be declared was read and the feature is not there. |
| `not_reported` | 23,337 (48.9%) | The sources were read and they are silent. This means undocumented, not absent. |
| `unresolved` | 163 (0.3%) | The cell failed validation at release and claims nothing. It is excluded from every rate. |

Two rules for analysis follow. Never recode `not_reported` as a value. For claims about the field,
use the sampling weights: the coded systems were drawn by stratum from a 6,504-system frame
(stratum H complete, P and O sampled), and the 23 systems coded outside the draw carry weight 0. The loader
applies both rules for you.

## Formats and downloads

| File | Contents |
|---|---|
| `data/systems.json` | The source of record: one nested object per system, all 38 cells with evidence |
| `data/cells.csv` | Long table, one row per system and dimension (47,728 rows): `state`, `value`, `evidence_quote`, `evidence_locator`, `confidence` |
| `data/systems_wide.csv` | One row per system, a value column and a `_state` column per dimension, plus stratum and weight |
| `data/systems.parquet`, `data/cells.parquet` | The same two tables in Parquet (written when `pyarrow` is present at build time) |
| `data/results.csv`, `data/papers.csv` | Reported benchmark scores (5,863 rows) and the included papers |
| `data/reliability.csv`, `data/not_reported_by_dimension.csv` | Per-dimension reliability and under-reporting rates |
| `datapackage.json` | [Frictionless](https://frictionlessdata.io/) descriptor with the type of every column |
| `harness-db-1.0.0.zip` | Everything above, with checksums and a validation report: the Zenodo deposit |

Where to get it: GitHub Releases, Zenodo (doi:10.5281/zenodo.23031354; v1.0.0 is 10.5281/zenodo.23031355), and Hugging Face (pending; see
[`DATASET_CARD.md`](DATASET_CARD.md)). You can also build it from a clone with
`python scripts/release_dataset.py --version 1.0.0 --out release/`. The build derives every file
from `data/systems.json` and stops if the data fails validation.

## Reliability, and what it does and does not measure

The coders were model instances working under a fixed protocol (coding manual v1.0 and a versioned
prompt). **247 systems were coded twice**, independently and through the same procedure. The figures
below therefore measure how reproducible that procedure is (model–model agreement). They do not
measure accuracy against a human reading.

| | value |
|---|---|
| systems double-coded / cells compared | 247 / 9,386 |
| observed agreement | 0.870 |
| Cohen's κ, mean of the 38 per-dimension values (the registered measure) | **0.784** [0.765, 0.800] |
| Gwet's AC1, same mean | 0.855 |
| dimensions with κ ≥ 0.6 | 37 of 38 on the point estimate |

The intervals are 95% cluster-bootstrap intervals with the system as the unit (2,000 draws). Four
dimensions have an interval that includes the 0.6 floor: `loop_primitives` 0.590 [0.523, 0.657],
`edit_primitive` 0.628 [0.537, 0.711], `network_policy` 0.668 [0.527, 0.793] and `retry_policy`
0.676 [0.587, 0.765]. `loop_primitives` is the one dimension below the floor. It is kept and
flagged: it is multi-valued, exact-set matching scores any extra listed primitive as a total
mismatch, and its per-value κ is 0.731. No single κ is quoted for all cells stacked together,
because stacking inflates it. The reasoning is in [`docs/coding_reliability.md`](docs/coding_reliability.md).

The checks outside the coding procedure test coverage, not cell values. Reference-set recall is
27/27. An independently built screening pipeline agreed with the inclusion decisions at 0.84
(κ 0.66). To check a cell's value, open its locator; if the value is wrong,
[report it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml).

<details>
<summary>Per-dimension κ with 95% intervals (all 38)</summary>

| dimension | κ | 95% CI | AC1 | agreement |
|---|---:|---|---:|---:|
| A1 `system_prompt_style` | 0.793 | [0.732, 0.853] | 0.823 | 0.854 |
| A2 `env_context_strategy` | 0.737 | [0.665, 0.801] | 0.778 | 0.806 |
| A3 `context_compaction` | 0.805 | [0.733, 0.872] | 0.890 | 0.895 |
| A4 `observation_format` | 0.691 | [0.614, 0.764] | 0.791 | 0.802 |
| B1 `tool_call_format` | 0.763 | [0.700, 0.824] | 0.821 | 0.830 |
| B2 `tool_count` | 0.817 | [0.722, 0.897] | 0.938 | 0.939 |
| B3 `edit_primitive` † | 0.628 | [0.537, 0.711] | 0.782 | 0.793 |
| B4 `tool_schema_source` | 0.717 | [0.638, 0.788] | 0.799 | 0.818 |
| B5 `protocol_standardization` | 0.899 | [0.847, 0.946] | 0.932 | 0.939 |
| C1 `loop_primitives` † | 0.590 | [0.523, 0.657] | 0.628 | 0.636 |
| C2 `planning_granularity` | 0.766 | [0.702, 0.828] | 0.792 | 0.830 |
| C3 `multi_agent_topology` | 0.856 | [0.797, 0.906] | 0.885 | 0.899 |
| C4 `delegation_mechanism` | 0.784 | [0.724, 0.843] | 0.795 | 0.834 |
| C5 `human_in_loop` | 0.729 | [0.651, 0.800] | 0.837 | 0.846 |
| D1 `short_term_state` | 0.735 | [0.660, 0.807] | 0.784 | 0.830 |
| D2 `long_term_memory` | 0.745 | [0.672, 0.807] | 0.813 | 0.822 |
| D3 `state_persistence` | 0.820 | [0.747, 0.883] | 0.893 | 0.911 |
| E1 `self_verification` | 0.738 | [0.670, 0.807] | 0.808 | 0.818 |
| E2 `retry_policy` † | 0.675 | [0.587, 0.765] | 0.815 | 0.838 |
| E3 `rollback` | 0.805 | [0.700, 0.895] | 0.932 | 0.939 |
| F1 `termination_condition` | 0.848 | [0.794, 0.896] | 0.879 | 0.883 |
| F2 `cost_controls` | 0.744 | [0.664, 0.817] | 0.852 | 0.862 |
| F3 `timeouts` | 0.837 | [0.762, 0.904] | 0.923 | 0.931 |
| G1 `execution_isolation` | 0.813 | [0.750, 0.873] | 0.844 | 0.866 |
| G2 `filesystem_access` | 0.833 | [0.758, 0.899] | 0.908 | 0.919 |
| G3 `network_policy` † | 0.668 | [0.527, 0.793] | 0.907 | 0.915 |
| G4 `permission_model` | 0.841 | [0.767, 0.904] | 0.907 | 0.919 |
| H1 `tracing` | 0.802 | [0.734, 0.860] | 0.828 | 0.866 |
| H2 `replayability` | 0.831 | [0.730, 0.915] | 0.943 | 0.951 |
| H3 `eval_hooks` | 0.792 | [0.717, 0.863] | 0.836 | 0.883 |
| H4 `guardrails` | 0.790 | [0.718, 0.861] | 0.883 | 0.891 |
| M1 `target_domain` | 0.735 | [0.674, 0.794] | 0.755 | 0.761 |
| M2 `open_source` | 0.820 | [0.751, 0.884] | 0.875 | 0.899 |
| M3 `model_agnostic` | 0.799 | [0.706, 0.876] | 0.899 | 0.919 |
| M4 `primary_artifact` | 0.843 | [0.765, 0.914] | 0.918 | 0.935 |
| M5 `first_release_date` | 0.841 | [0.779, 0.898] | 0.906 | 0.907 |
| M6 `pinned_version` | 0.896 | [0.858, 0.934] | 0.898 | 0.899 |
| M7 `stars` | 0.964 | [0.932, 0.989] | 0.976 | 0.976 |

† interval includes the 0.6 floor. Source: `data/coded/reliability_final.json`; released as `data/reliability.csv`.
</details>

## Cite

Please cite the paper, and the dataset with the version you used.

```bibtex
@article{gurram2026anatomy,
  title   = {The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded
             Dataset ({HARNESS-DB}) of {LLM} Agent Scaffolding, 2022--2026},
  author  = {Gurram, Bhaskar},
  journal = {arXiv preprint arXiv:XXXX.XXXXX},
  year    = {2026},
  note    = {arXiv identifier to be added at release}
}

@misc{gurram2026harnessdb,
  title     = {{HARNESS-DB}: A Coded Dataset of {LLM} Agent Harnesses, 2022--2026},
  author    = {Gurram, Bhaskar},
  year      = {2026},
  version   = {1.0.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23031354},
  url       = {https://github.com/harness-db/harness-db},
  url       = {https://doi.org/10.5281/zenodo.23031354}
}
```

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff).

## Contribute

You can add a system, correct a cell, or ask for a system to be coded. The template, the evidence
rule and the validator gate are in [`CONTRIBUTING.md`](CONTRIBUTING.md).
[`docs/COVERAGE_WANTED.md`](docs/COVERAGE_WANTED.md), generated from the data, lists the
most-starred uncoded systems and the dimensions where evidence is thinnest.

Built with a pre-registered protocol ([osf.io/ab2wn](https://osf.io/ab2wn); amendments logged in
[`docs/protocol_prisma_p.md`](docs/protocol_prisma_p.md)) and an evidence-per-cell design: no value
enters the dataset without a quote and a locator that a reader can re-open.

## License

Data, schema and documentation: [CC BY 4.0](LICENSE-DATA). Code (loader, scripts, validator,
explorer, CI): [MIT](LICENSE-CODE).

<details>
<summary>Repository layout and maintainer commands</summary>

```
schema/dimensions.json        the coding sheet: 9 layers, 38 dimensions, allowed values, crosswalk (hand-edited)
schema/harness_db.schema.json JSON Schema generated from dimensions.json (do not edit)
data/systems.json             the release: one object per system, every dimension coded with evidence
data/coding_frame.csv         the 6,504-system sampling frame: stratum, weight, coded flag
data/papers.csv               bibliographic rows, inclusion decisions, exclusion reasons
data/results.csv              reported scores per system, model, benchmark, split
data/analysis/                analysis outputs behind the paper's findings
data/prisma_counts.json       numbers for the PRISMA 2020 flow diagram
data/raw/, data/screening/    harvested candidates and screening votes (not redistributed in the release)
harnessdb/                    the Python loader (import harnessdb as hdb)
mcp_server/                   an MCP server over the dataset
contrib/                      TEMPLATE_system.json and contributed system files
docs/                         protocol (PRISMA-P), coding manual, reliability, count reconciliation, findings
scripts/                      schema build, validator, kappa, release build, harvest, screening, analysis
explorer/                     single-file static explorer
paper/                        manuscript and figures
tests/                        schema, script and loader tests
```

```
pip install -e ".[dev]"
python scripts/build_schema.py --check      # JSON Schema is current with dimensions.json
python scripts/validate.py                  # schema, referential integrity, evidence per cell
python scripts/coverage_wanted.py           # regenerate docs/COVERAGE_WANTED.md
python scripts/release_dataset.py --version 1.0.0 --out release/
python scripts/build_explorer.py            # rebuild explorer/index.html
python scripts/push_hf.py --repo harness-db/harness-db --release release/harness-db-1.0.0   # needs HF_TOKEN
pytest -q
```

CI runs the schema freshness check, the validator and the tests on every push and pull request.
Every count in the paper is reconciled against the data in
[`docs/count_reconciliation.md`](docs/count_reconciliation.md).
</details>
