# Human correctness audit: protocol (pre-registerable, v1, 2026-09-28)

**Status: design fixed, sheet built, not yet coded by a human.** No result exists yet. The paper
must not `\input{tables/human_audit}` until `scripts/human_audit.py --analyse` has written it, and
the script refuses to write that fragment from an empty or incomplete sheet.

## Why this audit exists

Everything HARNESS-DB currently reports about coding quality is model-model: two procedurally
identical model readings of the same 247 systems agree at mean per-dimension kappa 0.784
(`docs/coding_reliability.md`). That measures whether the coding procedure is *reproducible*. It does
not measure whether it is *right* — two readings can agree on the same wrong answer, and the most
likely shared error (reading silence as absence, or absence as silence) is exactly the one the
under-reporting result (RQ4) rests on. Reference-set recall (27/27) and the pipeline cross-check test
coverage, not cell correctness.

This audit puts a blinded human reading beside the released model reading on a fixed sample of cells
and reports **accuracy of the model reading against the human reading**, with intervals. It is the
only step that turns reliability into an accuracy estimate. The human reading is treated as the
reference; where the two disagree, a post-unblinding adjudication classifies the cause (below), but
the registered accuracy figure is computed *before* adjudication so that it cannot be tuned.

## 1. Cells audited

### 1.1 Dimensions (7)

| id | key | why | multi | absence-type value |
|---|---|---|---|---|
| G3 | `network_policy` | highest weighted silence (93.4%) | no | `open` |
| H2 | `replayability` | 2nd highest silence (90.6%) | no | `none` |
| G2 | `filesystem_access` | 3rd (87.5%) | no | `full` |
| E3 | `rollback` | 4th (86.4%) | no | `none` |
| D3 | `state_persistence` | 5th (86.2%) | no | `none` |
| C3 | `multi_agent_topology` | headline design dimension (RQ2) | no | `single` |
| E1 | `self_verification` | headline design dimension; multi-valued | yes | `none` |

Silence rates are the weighted `not_reported` shares in `data/coded/not_reported_by_dimension.csv`.
The five silence dimensions are the ones where a rule-5 error (general rule 5, "absence is not
silence") would move the RQ4 headline most; C3 and E1 are where the design-space claims rest. The
"absence-type value" column is used **only** to classify disagreements in the analysis (§4.4); it is
not a coding rule and is not shown to the human.

### 1.2 Sample (50 systems → 350 cells)

- **Eligible population.** Released systems (`data/systems.json`) that are weight-bearing in the
  frame (`data/coding_frame.csv`, `coded = 1`, `weight > 0`, i.e. drawn by the stratified design;
  the 23 out-of-frame systems at weight 0 are excluded), minus
  - every double-coded system already used for reliability — the union of the ids in
    `data/coded/double_sample.json` (245) and the `system_id`s of `data/coded/json_pass2/*.json`
    (247); the union is 247 systems — so that the audit is independent of the reliability sample;
  - the two manual worked examples, `swe-agent` and `openhands`, whose calibration codings are printed
    in `docs/coding_manual.md` and so would be visible to the human.
- **Strata.** H / P / O as in the frame.
- **Allocation.** Proportional to the *weighted* frame (H 983, P 150 × 4.5533 ≈ 683, O 100 × 48.37 ≈
  4,837 of 6,503), with a floor of 10 systems per stratum. Algorithm: allocate n = 50 proportionally;
  any stratum whose share is below 10 is fixed at 10 and the remainder is re-allocated proportionally
  among the others (largest-remainder rounding); repeat until stable. With these weights the proportional
  shares are H 7.6, P 5.3, O 37.2, so the floors bind and the allocation is **H 10 / P 10 / O 30**.
- **Draw.** Seed `human-audit-2026-09-28`. Within each stratum, eligible ids are sorted and
  `random.Random("<seed>:<stratum>").sample(ids, n_h)` is taken (Python's string seeding is
  version-stable). The draw, the seed, eligible and sampled counts and each system's audit weight are
  written to `data/audit/sample.csv`; re-running the build reproduces it byte for byte.
- **Audit weight.** Because the floors oversample H and P relative to the field, a sampled system
  carries `frame_weight × eligible_h / n_h`, so that weighted estimates generalise to the 6,503-weight
  frame. Unweighted per-dimension figures are the primary result (they are what the sample measures);
  the weighted pooled accuracy is reported beside them.

## 2. Blinding

The human sheet (`data/audit/human_sheet.csv`, and `human_sheet.xlsx` with dropdowns) has one row per
system × dimension (350 rows) and shows **only**:

- system id and name; the pinned version/commit (M6 value, or the version label with an instruction to
  pin per protocol §4.5 when M6 is `not_reported`); the repository URL; the paper ids with title and URL
  from `data/papers.csv`;
- the dimension id, key and name, whether it is multi-valued, its permitted values with one-line
  glosses and the decision rule, both taken verbatim from `docs/coding_manual.md`;
- the three-state rule (general rule 5, below).

It does **not** show the model's value, state, evidence, confidence or note for any of the 350 cells, nor
the system-level `notes`, nor the stratum. The model's answers go to `data/audit/model_answers.csv`,
which the human must not open. A test (`tests/test_human_audit.py`) asserts that no model value,
evidence string or state column reaches the sheet.

Rows are ordered by system (all 7 dimensions of one system together) so that the pinned sources are read
once per system; the system order is the random draw order.

## 3. What the human records

| column | content |
|---|---|
| `human_state` | `coded` / `not_reported` / `unresolved` |
| `human_value` | permitted value(s); multi-valued as a pipe-joined list (`self_critique\|test_execution`), empty unless `coded` |
| `human_evidence_quote` | verbatim quote or code line, empty only when `unresolved` |
| `human_locator` | `path:LINE@<short-hash>` or `arXiv id Sec. N` (general rule 2); for a rule-5b absence, the place opened plus the search run |
| `human_confidence` | `high` / `medium` / `low` (general rule 3) |
| `human_minutes` | minutes spent on the cell (reading shared per system is split evenly over its 7 rows) |
| `human_note` | free text, optional |
| `coder_id` | `c1`, `c2`, ... (general rule 9) |

The three-state rule, printed on every row:

> **coded** — you can point at evidence for a value. If the value is an *absence* (`none`, `open`,
> ...), you must have opened the place where the feature would be declared if it existed (config
> schema, CLI flags, tool registry, the run loop, a documented feature list) and found it missing
> (rule 5b). **not_reported** — the pinned sources contain no such place, or you could not find one
> (rule 5c); prose that does not mention the feature is *not* evidence of absence. **unresolved** — you
> cannot settle it within the time box; say why in the note.

## 4. Analysis (`python scripts/human_audit.py --analyse`)

### 4.1 Labels
Each reading of a cell is reduced to a label: `NR` (not_reported), `UNRESOLVED`, or the sorted,
pipe-joined value set. This is the same normalisation `scripts/kappa.py` uses for reliability.

### 4.2 Primary measure: accuracy
A model cell is **correct** when its label equals the human label exactly (same state, and — when both
are coded — the same value set). Cells the human marked `unresolved` have no reference and are excluded
from the accuracy denominator (their count is reported). A model `unresolved` against a human `coded`
or `not_reported` counts as incorrect.

- **Per dimension:** accuracy = correct / n_ref, with a **Wilson 95% interval**.
- **Pooled (350 cells):** accuracy with (a) a naive Wilson interval and (b) a **paper-clustered
  bootstrap** interval: systems that share any paper id are one cluster (union-find over the sample),
  clusters are resampled with replacement (2,000 draws, fixed seed), and the 2.5/97.5 percentiles are
  reported. The cell is not the unit because the 7 cells of one system are read from one set of sources.
  The same bootstrap gives the interval for the **frame-weighted** pooled accuracy (audit weights, §1.2).
- **Per stratum:** pooled accuracy for H, P and O, descriptive only.

### 4.3 Secondary measures (per dimension)
- **Three-way state agreement:** the 3 × 3 model-by-human confusion over `coded` / `not_reported` /
  `unresolved`, observed agreement and Cohen's kappa on the state alone.
- **Value agreement given both coded:** share of exact value-set matches among cells both readings coded
  (with n and a Wilson interval). For E1 (multi-valued) the per-value kappa from
  `kappa.multilabel_kappa` is reported beside it as a diagnostic.
- **Cohen's kappa and Gwet's AC1** on the full label, from `scripts/kappa.py` (`cohen_kappa`,
  `gwet_ac1`), over all filled cells.
- **Silence precision and recall** (the RQ4 check): of the cells the model marked `not_reported`, the
  share the human also marked `not_reported` (precision); of the cells the human marked
  `not_reported`, the share the model did (recall). A low precision means the under-reporting rate is
  inflated; a low recall means it is understated.

### 4.4 Disagreement table
Every disagreement is listed with both labels and **both evidence strings** (model evidence and note;
human quote, locator and note), and typed:

- `nr_vs_absence` — one reading `not_reported`, the other the dimension's absence-type value (§1.1):
  the rule-5 split;
- `nr_vs_feature` — one reading `not_reported`, the other a non-absence value;
- `value_mismatch_partial` / `value_mismatch_disjoint` — both coded, overlapping or disjoint value sets;
- `unresolved` — either reading unresolved.

The table carries an empty `adjudication` column for a post-unblinding pass, which classifies each
disagreement as `model_misread`, `bundle_gap` (the human read a file the model's evidence bundle did not
contain — the model coded from a truncated bundle, the human from the full pinned repository),
`human_error`, or `manual_ambiguity`. Adjudication is reported alongside, and never changes, the §4.2
figure.

### 4.5 Outputs
- `data/audit/results.json` — every figure above, machine-readable;
- `data/audit/results.md` — the same as tables, plus the disagreement table;
- `paper/tables/human_audit.tex` — **only** when every one of the 350 rows is filled and valid. A
  partially filled sheet can be analysed with `--allow-partial` (for monitoring), which writes the
  JSON and Markdown marked `partial` but never the LaTeX fragment. An empty sheet is refused outright.

### 4.6 Validation before analysis
The script refuses a sheet whose rows do not match the sample's 350 cell ids, whose `human_state` is not
one of the three states, whose `coded` rows have no value or a value outside the permitted list (or
several values on a single-valued dimension, or `none` alongside other values — rule 4), or whose
`not_reported`/`unresolved` rows carry a value.

## 5. Procedure for the human coder
The step-by-step instructions given to the coder are in `data/audit/README.md`: read only the pinned
sources (repository at the pinned commit, the listed papers), apply the manual and general rule 5,
time-box each cell at 8 minutes, and never open `model_answers.csv` or `data/systems.json`.

## 6. Workload and precision (planning figures)

- **Workload.** 350 cells. The hard ceiling at the 8-minute time box is 350 × 8 = 2,800 minutes ≈
  **47 hours**. Realistically the sources are read once per system (≈ 15 minutes to open the pinned
  repository and papers) and each of the 7 cells then takes ≈ 3–5 minutes, i.e. 50 × (15 + 7 × 4) ≈
  2,150 minutes ≈ **36 hours**, about one working week for one coder. A second human coder on a
  subset (e.g. 10 systems, 70 cells, ≈ 7 hours) would give a human-human baseline, and is recommended
  but not required by this protocol.
- **Precision.** With n = 50 cells per dimension and a true accuracy of 90%, the Wilson 95% interval is
  [0.786, 0.957], a **half-width of about ±8.5 points**; at 80% it is ±11 points. Per-dimension
  figures can therefore distinguish "about 90%" from "about 70%", not 90% from 85%. The pooled 350 cells
  give a naive Wilson half-width of ±3.2 points at 90%; the paper-clustered bootstrap will be wider
  (a design effect of 1.5–2 puts it near ±4–4.5 points). Human-`unresolved` cells shrink n further.

## 7. Deviations
Any change to §1–§4 after the first human row is filled is a deviation and is reported as such.

## Appendix: realised draw (2026-09-28)

Written after the build; the draw itself is `data/audit/sample.csv` (seed `human-audit-2026-09-28`),
and `python scripts/human_audit.py --build` reproduces all three files byte for byte.

| stratum | eligible | drawn | audit weight per system |
|---|---|---|---|
| H | 779 | 10 | 77.900 |
| P | 123 | 10 | 56.006 |
| O | 84 | 30 | 135.436 |

Eligible counts: H 983 weight-bearing released systems minus 202 double-coded minus the 2 manual
examples = 779; P 150 - 27 = 123; O 100 - 16 = 84. 247 double-coded systems excluded in all.

- **H**: `a-evolve`, `agentverse`, `ai-agent`, `codescout`, `epibench-reference-agent`, `github-copilot-cli`, `kdr-agent`, `musicagent`, `pybench-reference-agent`, `testagent`
- **P**: `agent-factory`, `agentic-additive-manufacturing-alloy-evaluation`, `androidgen`, `careconnect`, `cowpilot`, `executionagent`, `ipiguard`, `mdcrow`, `sandboxsocial`, `swe-search`
- **O**: `agentrca`, `agentxgcore`, `ai-office`, `aionopedia`, `apollo-2`, `autonumerics`, `ave`, `cellforge`, `docksmith`, `graphmasal`, `hierarchical-language-agent`, `human-like-planning-framework-for-travelplanner`, `icrl-prompting`, `iris`, `kernelbench`, `llm-enabled-multi-agent-manufacturing-systems-framework`, `llm-simp-controller`, `por-efr`, `reg-tsc`, `rl-llm-dt`, `self-organized-agents`, `stereotype-detection-agent`, `stop-rag`, `synthai`, `taskgen`, `tdad`, `timon-pumbaa`, `unidoc-rl`, `unrealllm`, `vdgr-rag`

The 50 systems form 50 distinct paper clusters (no two share a paper id), so the paper-clustered
bootstrap reduces to a system-level bootstrap on this draw. 23 of the 50 systems have no repository
URL (paper-only sources) and 16 have no recorded pin (the sheet tells the coder how to pin).

The distribution of the model's states over these 350 cells is deliberately not recorded here:
this protocol is linked from the coder's instructions, and a base rate is itself a hint. It is
computed from `model_answers.csv` at analysis time.
