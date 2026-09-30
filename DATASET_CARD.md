---
license: cc-by-4.0
pretty_name: HARNESS-DB
language:
- en
size_categories:
- 10K<n<100K
task_categories:
- tabular-classification
- text-classification
annotations_creators:
- machine-generated
language_creators:
- found
multilinguality:
- monolingual
source_datasets:
- original
tags:
- llm-agents
- agent-harness
- systematic-review
- taxonomy
configs:
- config_name: cells
  data_files: data/cells.csv
  default: true
- config_name: systems
  data_files: data/systems_wide.csv
---

# Dataset card for HARNESS-DB

## Dataset summary

HARNESS-DB is a coded dataset of LLM agent harnesses. A harness is the software layer between a
language model and a task environment that repeatedly assembles the model's input, executes the
model's chosen actions, and decides whether to continue. The dataset codes **1,256 systems** from
2022 to 2026 on **38 design dimensions** grouped into nine layers (context assembly, tool interface,
control loop, memory and state, verification and repair, budget and termination, sandbox and
environment, observability and governance, and meta). That is **47,728 cells** in all.

Each cell is in one of three states:

| state | cells | share |
|---|---:|---:|
| coded value, with a verbatim quote, a locator and a confidence | 24,228 | 50.8% |
| `not_reported`: the sources were read and are silent | 23,337 | 48.9% |
| `unresolved`: failed validation at release; claims nothing | 163 | 0.3% |

The coded systems are a stratified sample of a **6,504-system sampling frame** produced by a
pre-registered PRISMA 2020 systematic review ([osf.io/ab2wn](https://osf.io/ab2wn)). Sampling
weights are included, so the data supports estimates for the whole frame as well as statements
about the coded set.

- Repository: https://github.com/harness-db/harness-db
- Paper: *The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset
  (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026* (arXiv identifier to be added at release)
- Version: 1.0.0 (schema 1.0.0, frozen 2026-09-23)
- DOI: 10.5281/zenodo.23031354 (Zenodo concept DOI; version 1.0.0: 10.5281/zenodo.23031355)

## Supported uses

- **Describing harness design.** Examples: value distributions per dimension, weighted to the field
  or unweighted over the coded set, and comparisons between strata or years.
- **Auditing documentation.** Which design decisions do harness papers and repositories leave
  undocumented? `not_reported` is recorded explicitly for this purpose. Weighted to the field, the
  sandbox and environment layer is 81.6% silent and the control loop is 24.9% silent.
- **Selecting systems.** Find harnesses with a given combination of properties (for example
  container isolation with test-execution verification), then follow each cell's locator to the
  source.
- **Evidence-grounded extraction.** Every coded value has its supporting quote, so the
  `(quote, dimension) -> value` pairs can be used to evaluate or train extraction of design
  properties from technical text. Model-produced labels are the only reference available; see
  "Annotation process".
- **Linking design to outcomes.** `results.csv` holds 5,863 author-reported benchmark scores. Only
  53 systems (4.2%) share a benchmark, split and base model with another coded system, so
  cross-system comparison is limited to that subset.

**Out of scope.** Do not read a `not_reported` cell as "the system lacks this feature". Do not
treat the scores in `results.csv` as a controlled comparison between harnesses. Do not treat
unweighted shares as estimates for the field.

## Dataset structure

### Files

| file | one row / object per | fields |
|---|---|---|
| `data/systems.json` | system | `id`, `name`, `version_label`, `aliases`, `urls` (`repo`, `paper`, `docs`), `papers` (ids in `papers.csv`), `coded_at`, `notes`, and `coding`: an object keyed by the 38 dimension keys, each cell holding `value`, `evidence`, `confidence`, `not_reported`, `unresolved`, `coder`, `note` |
| `data/cells.csv` | system × dimension (47,728 rows) | `system_id`, `layer`, `dimension_id`, `dimension_key`, `state` (`coded` \| `not_reported` \| `unresolved`), `value`, `evidence_quote`, `evidence_locator`, `confidence`, `flags` (why a cell is unresolved), `coder`, `note` |
| `data/systems_wide.csv` | system (1,256 rows) | `system_id`, `name`, `version`, `repo_url`, `stratum`, `weight`, `primary_paper_id`, `paper_ids`, `coded_at`, then `<dimension_key>` and `<dimension_key>_state` for each of the 38 dimensions |
| `data/systems.parquet`, `data/cells.parquet` | as the CSV tables | the same columns (present when the release was built with `pyarrow`) |
| `data/results.csv` | reported score (5,863 rows) | `system_id`, `model`, `benchmark`, `split`, `metric`, `score`, `cost_usd`, `tokens`, `date`, `source_url`, `comparable_key`, `notes` |
| `data/papers.csv` | included paper | `id`, `title`, `year`, `venue`, `arxiv_id`, `doi`, `url`, `source`, `system_ids` |
| `data/reliability.csv` | dimension (38 rows) | agreement, Cohen's κ, Gwet's AC1 and per-value κ, each with a 95% cluster-bootstrap interval |
| `data/not_reported_by_dimension.csv` | dimension (38 rows) | counts per state, unweighted rate, field-weighted rate and design SE |
| `schema/dimensions.json`, `schema/harness_db.schema.json`, `schema/data_dictionary.md` | dimension | layers, allowed values, value definitions, and the JSON Schema that `systems.json` validates against |
| `datapackage.json` | resource | Frictionless descriptor with the type of every column |

### Values

34 of the 38 dimensions are categorical with a closed value list. Of these, 15 are multi-valued and
are pipe-joined (`a|b`) in CSV. There are two integers (`tool_count`, `stars`), one date
(`first_release_date`) and one string (`pinned_version`, as `<tag> @ <commit> (<date>)`). A value
such as `none` is a coded finding: the place where the feature would be declared was opened and
the feature is not there. It is different from `not_reported`.

### Loading

```python
import harnessdb as hdb
db = hdb.load("harness-db-1.0.0/")    # an unzipped release
db.cells                               # long table, one row per system and dimension
db.not_reported(by="layer")            # silence per layer, unweighted and field-weighted
db.evidence("openhands", "self_verification")
ds = db.to_hf()                        # datasets.DatasetDict with "systems" and "cells" splits
```

The loader and the release files use the same state names: `coded`, `not_reported`, `unresolved`.

## Curation rationale

Earlier harness surveys describe systems the authors chose, in prose, without per-claim sources.
Two problems follow. Well-known systems are over-represented. And a reader cannot tell whether a
claim that a system "has no sandbox" means the feature is absent or only that no source mentions
it. HARNESS-DB addresses both problems. The systems come from a pre-registered census with a
stratified sample and known weights. Every coded value carries a quote and a locator that can be
re-opened. Documented silence is a separate state rather than a gap in the table.

The weighting matters. 69.2% of the coded systems are repository-primary, but only 33.3% of the
field is once the sample is weighted.

## Source data

The sampling frame comes from a PRISMA 2020 search:

- **Records identified:** 37,899 from arXiv, Semantic Scholar, OpenAlex, the ACL Anthology,
  OpenReview and GitHub, plus 12,825 from other methods (grey literature, leaderboards,
  snowballing and curated lists).
- **Screening:** 27,747 records after de-duplication, 8,435 assessed at full text and 7,085
  included.
- **Frame:** the 7,085 included reports were grouped into **6,504 systems**.

The frame has three strata:

- **H (high visibility):** 984 systems, coded completely. A system is in H if its repository has
  500 or more stars, a prior harness survey catalogued it, or it is a vendor or major-lab product.
- **P:** 683 systems not in H that are described in a peer-reviewed paper with a public
  implementation. 150 were sampled (weight 4.5533).
- **O:** the remaining 4,837 systems. 100 were sampled (weight 48.37).

Another 23 systems were coded outside the draw. Several are benchmark reference agents needed for
the reference-set recall check. They are released at weight 0.

The coders read three kinds of source: each system's papers (arXiv HTML where available), its
repository at a pinned tag and commit, and its documentation. Every release artifact is derived
from `data/systems.json` by `scripts/release_dataset.py`. Full texts, raw harvests and screening
exports are not redistributed.

## Annotation process

**Coding framework.** The coding sheet is `schema/dimensions.json` (9 layers, 38 dimensions, closed
value lists, and a crosswalk to three earlier taxonomies). It is applied under
`docs/coding_manual.md` (v1.0, frozen with the schema), whose general rules are:

- Code the system at its pinned version.
- Evidence is verbatim: `path:line@commit` for code, or a quote with its paper section. No
  paraphrase.
- Confidence is `high` for an explicit statement or code on the cited line, `medium` when the
  value is inferred from adjacent code or a default, and `low` when it is inferred from prose.
- Code the shipped default first. For multi-valued dimensions, also code the values that shipped
  configuration can reach.
- **Absence is not silence.** If the place where a feature would be declared was read and the
  feature is not there, code the absence value. If no such place was available, code
  `not_reported`.

**Who coded.** The coders were model instances working under this fixed protocol with a versioned
prompt (`code-v2-2026-09-23`). The coder id is recorded on every cell. Every coding went through a
repair pass that checks the cells against the schema, and cells that still failed at release are
marked `unresolved`. Two offensive-security systems (`cai`, `pentagi`) were coded with a different
model from the same family, because the primary model's safety classifier stopped the coding on
both. After release, the author and colleagues, blind to the model's answers, re-read 50 systems on
7 dimensions (350 cells; sample and seed fixed in advance). The model coding agreed with the human
reading on 202 of 350 cells (57.7%, 95% CI 48.6–66.9); 117 of the 148 disagreements were cells whose
evidence lay in files the model's capped evidence bundle never contained, and on cells whose evidence
the model did receive it agreed on 202 of 233 (86.7%). Almost every disagreement is a `not_reported`
cell that the human could value, so every silence rate in this card is an upper bound. The audit
protocol, sheet and results are in `data/audit/` of the repository.

**Reliability.** 247 systems were coded twice, independently, through the identical procedure
(9,386 cells compared):

- observed agreement 0.870
- mean per-dimension Cohen's κ 0.784 [0.765, 0.800]
- mean Gwet's AC1 0.855
- 37 of 38 dimensions at κ ≥ 0.6 on the point estimate

Four dimensions have a 95% cluster-bootstrap interval that includes 0.6: `loop_primitives`
0.590 [0.523, 0.657], `edit_primitive`, `network_policy` and `retry_policy`. `loop_primitives` is
kept and flagged. It is multi-valued, and its per-value κ is 0.731.

The coding rule that separates absence from silence was rewritten before the schema froze
(protocol amendment 9), and the whole set was re-coded under it. On the 217-system validation
sample, κ rose from 0.564 to 0.832. Per-dimension figures are in `data/reliability.csv`.

## Personal and sensitive information

None. The units are software systems. `papers.csv` has bibliographic fields but no author column.
Repository URLs name the GitHub organisations or accounts that published the software. The star
counts are public figures, date-stamped in the evidence.

## Bias, risks and limitations

- **The coded set is not the field.** High-visibility systems are coded completely, while the
  long tail is sampled. Unweighted shares therefore describe what is easy to code, and can reverse
  when weighted. For example, repository-primary systems are 69.2% of the coded set but 33.3% of
  the field. Use the weights in `systems_wide.csv` for field-level claims. The 23 weight-0 systems
  belong in unweighted statements only.
- **Reliability is model–model reproducibility; accuracy comes from the human audit.** Both readings in
  the reliability sample came from the same kind of coder under the same protocol, so shared
  systematic errors would not show up as disagreement. The human audit (above) puts cell-level
  agreement at 57.7% overall and 86.7% where the model had the evidence; the gap is mostly
  evidence the model was never shown. Treat `not_reported` as "not found in the evidence bundle",
  not as "not documented anywhere". The quote and locator on every value let a reader check any cell.
- **Silence is not absence.** 48.9% of cells are `not_reported`. Imputing them, or treating them
  as a category in association analyses, produces artefacts. With silence counted as a level, 265
  of 666 dimension pairs test as associated that do not test as associated on complete pairs.
- **Coverage.** The frozen search strings missed application-domain frameworks whose abstracts
  use no harness vocabulary. An independent search found 103 includes that the main search did
  not, and they entered the review through a supplementary arm. Systems that are described only
  in languages other than English, or not publicly at all, are outside the frame.
- **Snapshot.** Each system is coded at one pinned version. Harnesses change quickly, and a cell
  describes that version only.
- **Release defects, disclosed.** One coded system (`con`, stratum H) is not in the release,
  because its id is a reserved file name on Windows. That is why stratum H has 983 released systems
  and the released weights sum to 6,503 rather than 6,504.
- **Scores are author-reported.** `results.csv` is not a controlled benchmark. Only 4.2% of coded
  systems share a comparable key with another coded system.

## Licensing

The data, schema and documentation are released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The code (loader, validator, build
scripts) is released under the MIT License.

## Citation

```bibtex
@article{gurram2026anatomy,
  title   = {The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded
             Dataset ({HARNESS-DB}) of {LLM} Agent Scaffolding, 2022--2026},
  author  = {Gurram, Bhaskar},
  journal = {arXiv preprint arXiv:XXXX.XXXXX},
  year    = {2026}
}

@misc{gurram2026harnessdb,
  title     = {{HARNESS-DB}: A Coded Dataset of {LLM} Agent Harnesses, 2022--2026},
  author    = {Gurram, Bhaskar},
  year      = {2026},
  version   = {1.0.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23031354},
  url       = {https://github.com/harness-db/harness-db}
}
```

## Maintainers

Bhaskar Gurram (gurrambhaskar.ai@gmail.com). Report errors and request systems through
[GitHub issues](https://github.com/harness-db/harness-db/issues). Contributions follow
[CONTRIBUTING.md](https://github.com/harness-db/harness-db/blob/main/CONTRIBUTING.md).
