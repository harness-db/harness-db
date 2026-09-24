# Benchmark caveats (Phase 6 task 46)

This document says what a reported benchmark score in `data/results.csv` does and does not mean.
It exists because the review's central claim — that harness design choices explain benchmark
outcomes — rests on comparing numbers that other people produced under conditions they mostly did
not record. `scripts/mark_comparable.py` handles the part of that problem which is mechanical: it
blanks `comparable_key` for any row whose benchmark, split, metric, model or harness cannot be
pinned down, so that only rows measuring the same thing on the same task set with the same model
are ever placed beside one another. What follows is the part that no script can fix.

Read it as a risk-of-bias section (protocol §10) with the specifics filled in. Every claim is
either sourced or marked **unverified**. "Unverified" means we believe it but have not confirmed
it against the primary source at the level of detail stated; it is not a hedge on whether the
caveat matters.

## What is actually in the data

Counts below are from our own harvest, `data/raw/leaderboards.jsonl`, at the search freeze of
2026-09-16, and are reproducible from that file. They describe eight board families and 4,887
leaderboard entries; the papers arm (`scripts/extract_results.py`) adds rows with the same columns
and the same problems.

| board family | entries | splits present | metric string on the board |
|---|---|---|---|
| GAIA | 3,773 | `test` 3,679, `validation` 94 | `accuracy %` |
| SWE-bench | 323 | `Verified` 180, `Lite` 84, `Test` 24, `Multimodal` 22, `Multilingual` 13 | `% resolved` |
| HAL | 246 | nine different benchmarks in the split column | `accuracy %` |
| OSWorld | 245 | `Verified` 145, four `self-reported/<modality>` sheets 100 | `success rate %` |
| tau2-bench | 159 | `{text, voice, text-legacy}` x `{airline, retail, telecom, banking_knowledge}` | `pass^1 %` |
| WebArena | 85 | `WebArena` 47, `VisualWebArena` 38 | `success rate %` |
| Terminal-Bench | 42 | `1.0 (terminal-bench-core@0.1.1)` 25, `4.0` 17 | `accuracy %`, `accuracy % (mean of runs)` |
| tau-bench | 14 | `airline` 7, `retail` 7 | `pass^1 %` |

Two facts from that table are worth stating in the paper as they stand. First, **the metric string
is not a metric**: the same computation — the fraction of tasks whose checker passed — is written
`success rate %` by OSWorld and WebArena, `accuracy %` by GAIA, HAL and Terminal-Bench, and
`% resolved` by SWE-bench. `mark_comparable.py` aliases those per benchmark, and refuses to alias
them where the wording is genuinely ambiguous (see SWE-bench below). Second, **two thirds of the
GAIA rows do not name a model at all** (2,523 of 3,773), which is why the single largest blanking
reason in the pipeline is `model_missing`.

## Per-benchmark

### SWE-bench

*Source:* Jimenez et al., "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?",
ICLR 2024, arXiv:2310.06770. 2,294 task instances drawn from pull requests in 12 Python
repositories; the agent must produce a patch that makes hidden tests pass.

**Versioning is the first-order problem, and "SWE-bench" without a qualifier is ambiguous.** At
least five task sets carry the name:

- **full** (the original `test` split, 2,294 instances). The HuggingFace split is called `test`;
  the community calls it "full". Our canonicaliser folds both to `full`.
- **Lite**, 300 instances, selected by the SWE-bench team for cheaper evaluation.
- **Verified**, 500 instances, human-validated with the SWE-bench authors and published by OpenAI
  in August 2024 ("Introducing SWE-bench Verified"). Verified exists *because* a sizeable share of
  the original instances were under-specified or had broken tests, so Verified scores are
  systematically higher than full or Lite scores on the same system. The size of that gap varies
  by system and is **unverified** as a general figure.
- **Multimodal**, 517 JavaScript instances (arXiv:2410.03859).
- **Multilingual**, 300 instances (size from our harvest's split table; the accompanying paper is
  **unverified**).

A bare "SWE-bench" is therefore not a benchmark identity, and a row that gives no split gets no
key. This is not pedantry: in our harvest, `Verified`, `Lite` and `Test` rows coexist in one board
family, and pooling them would put a 500-instance curated set beside a 2,294-instance raw one.

**Metric.** The board reports `% resolved`. We alias `% solved`, `solve rate`, `success rate` and
`fix rate` to it, because on SWE-bench those denote the same computation. We deliberately do
**not** alias `accuracy`: on SWE-bench that word has been used for file-localisation accuracy and
for patch-applies-cleanly rate as well as for resolve rate, and collapsing it would silently
average three different numbers. The visible cost is that HAL's 33 `swebench_verified_mini` rows,
which are labelled `accuracy %` and really are resolve rate, get no key. Admitting them is a
one-line change to `METRIC_ALIASES_BY_BENCHMARK`, and it should be made deliberately.

**Contamination — a live dispute, stated as such.** SWE-bench instances come from public GitHub
pull requests, most merged well before 2024. The issue text, the discussion and the fix commit are
all public, so a model whose training data postdates an instance may have seen the patch that
resolves it. Two kinds of evidence bear on this:

- *For.* Aleithan et al., "SWE-Bench+" (arXiv:2410.06992), report solution leakage — the fix, or
  enough of it, present in the issue report or its comments — in a substantial minority of the
  instances that models were credited with resolving, together with weak test coverage that lets
  wrong patches pass. We take the direction of that finding as sound; the exact percentages are
  **unverified**. Work in the same vein has shown that models can name the file to edit from the
  issue text alone at rates that pure reasoning does not explain (**unverified**: we have not
  confirmed which paper reports what).
- *Against overstating it.* Benchmarks rebuilt from post-cutoff instances (SWE-bench-Live,
  SWE-rebench, SWE-bench Pro) report lower scores than SWE-bench Verified but not collapsed ones,
  which is consistent with contamination inflating scores rather than manufacturing them
  (**unverified**: the magnitudes, and in places the existence of the comparison we are
  recalling). No one has demonstrated that a specific leaderboard row we harvested is
  contaminated.

The honest statement for the paper: SWE-bench scores are not safe as absolute capability
measurements, the inflation is not known to be uniform across systems, and we make no absolute
claims from them. What the regression uses is the *difference* between harnesses within one
(benchmark, split, model) cell, where a contamination effect that depends only on the model
cancels. It does not cancel if different harnesses exploit leakage to different degrees — an agent
that reads the issue comments verbatim benefits more than one that does not — and that is a
confounder we can name but not remove.

**Self-reporting, and the two boards that track it.** Two families in our harvest carry a
verification field, and they carry it for opposite reasons. SWE-bench records per submission
whether anyone checked it: of its 323 entries, **131 carry `checked: true`, 174 carry a false
value** (166 plain `false` plus 8 spelling it out as "false (See README.md for info on how to get
your results verified)"), **and 18 carry no flag at all** — so a majority of SWE-bench rows are
unverified submissions by the system's own authors, and the flag travels with the row in our data.
HAL carries `checked: true` on all **246** of its entries, which is not a submission review but a
property of the board: HAL runs the agents itself, so there is no submitted number to doubt. The
remaining **four thousand three hundred and eighteen** entries — GAIA 3,773, OSWorld 245,
tau2-bench 159, WebArena 85, Terminal-Bench 42, tau-bench 14 — carry no verification field of any
kind.

### OSWorld

*Source:* Xie et al., "OSWorld", NeurIPS 2024, arXiv:2404.07972. 369 real computer-use tasks in a
virtual machine, scored by per-task execution-based checkers.

**Versioning.** OSWorld-Verified is a later re-audit of the task set and its evaluators by the
OSWorld maintainers; scores before and after the audit are not the same measurement, because some
pre-audit tasks were unpassable and some checkers were wrong. The release date and the size of the
score change are **unverified**. Our harvest keeps `Verified` (145 entries) and the maintainers'
`self-reported` sheets (100) as distinct splits.

**Configuration is a split here, and it is a harness variable.** The self-reported sheet is broken
down by observation modality — screenshot only, accessibility tree only, screenshot plus a11y
tree, set-of-mark — and an agent that sees a screenshot is not solving the same problem as one
that reads the a11y tree. Our canonicaliser keeps the modality inside the split so those rows
never pool. The same logic applies to the step budget: OSWorld scores depend strongly on the
maximum number of actions allowed, which most entries do not state (**unverified** as a general
claim about the board, though it is stated in the OSWorld paper's own ablations). Where the budget
is unrecorded, a same-split comparison can still be comparing a 15-step run with a 50-step run.

22 of 245 OSWorld entries name no model.

### WebArena and VisualWebArena

*Sources:* Zhou et al., "WebArena", ICLR 2024, arXiv:2307.13854 (812 tasks on self-hosted
reproductions of five websites); Koh et al., "VisualWebArena", ACL 2024, arXiv:2401.13649 (task
count **unverified**).

**The environment is local, so two "WebArena" numbers are two different environments.** Each
evaluator stands up their own copy of the sites; version skew in the site images, the reset
procedure between tasks, and the local network all move scores, and none of it appears on the
board. This is the benchmark where we are least able to defend a cross-paper comparison, and one
of the smallest surviving cell counts in the pipeline reflects that.

**WebArena-Lite** (a 165-task re-annotation of WebArena) and **VisualWebArena** are separate
benchmarks, not splits: the task sets and in Lite's case the reward functions differ. Our harvest
files VisualWebArena rows under the WebArena board family with the benchmark name in the split
column; `mark_comparable.py` reports those 37 rows as `benchmark_split_conflict` rather than
guessing, so the extractor can re-home them.

### Terminal-Bench

*Source:* the tbench.ai leaderboard and the Laude Institute / Stanford release (2025). Task counts
and release history are **unverified**.

**The dataset is versioned and the versions are not comparable.** Our harvest contains two
generations under one family: `Terminal-Bench 1.0 (terminal-bench-core@0.1.1)` (25 entries) and
`Terminal-Bench 4.0` (17). The task set changed between them, so the version is part of the split
in our key (`core@1.0`, `core@4.0`) and 1.0 numbers never meet 4.0 numbers. This is the clearest
case in the data of a benchmark whose *name* is stable while its *content* is not.

**Run averaging.** Terminal-Bench entries come in two metric spellings, `accuracy %` and
`accuracy % (mean of runs)` (25 of 42 entries). We treat both as the same measurement, because
they estimate the same quantity, but a mean of several runs is a less noisy estimate than a single
run and the number of runs is usually not recorded. Rows differing by a point or two should not be
read as ordered.

### GAIA and GAIA2

*Source:* Mialon et al., "GAIA: a benchmark for General AI Assistants", ICLR 2024,
arXiv:2311.12983. A public validation set of roughly 165 questions and a 300-question test set
whose answers are held privately and scored by the leaderboard (exact counts **unverified**).

**GAIA is where self-reporting and attribution are worst, by a wide margin.** It supplies 3,773 of
our 4,887 harvested entries and it is the only board in the harvest that is effectively open
submission: 3,679 of its rows are on the private `test` split, **2,523 of 3,773 name no model at
all**, and 9 cannot be attributed to any system. Almost all of that volume is unusable for the
review's question, and it blanks for the stated reason rather than being quietly dropped. The
validation-set rows (94) are the ones papers usually report, and they are self-reported in the
ordinary way.

Per-level numbers (Level 1/2/3) are subsets of one split, so we keep them as separate splits; a
Level-1 score and an overall score are not the same measurement. **GAIA2** (2025, released with
Meta's agent research environment) is a different benchmark, not a GAIA split; details
**unverified**.

### tau-bench and tau2-bench

*Sources:* Yao et al., "tau-bench", arXiv:2406.12045 (Sierra; airline and retail domains,
user-simulator dialogue, `pass^k` metric); tau2-bench, arXiv:2506.07982 (adds telecom and
dual-control; **unverified**).

**`pass^1` is not `pass@1`.** `pass^k` is the probability that *all k* independent trials succeed,
which is a deliberately harsher statistic than "at least one of k". A `pass@1` row and a `pass^1`
row are different estimators, and our canonicaliser refuses to pool them.

**Domains do not average.** Airline and retail have different task counts and difficulty, so a
mean over domains is not a number that either domain's rows can be compared with. We keep the
domain in the split and provide no "all domains" token.

**tau2 adds modality to the split.** Its board reports `text`, `voice` and `text-legacy` variants
of each domain; voice adds speech recognition to the task and `text-legacy` re-runs the tau1
prompts. Those are three measurements, not one, and they stay apart.

### The HAL-run benchmarks (CORE-Bench, SciCode, ScienceAgentBench, AssistantBench, USACO, Online-Mind2Web, SWE-bench Verified Mini, GAIA, tau-bench airline)

*Source:* the Holistic Agent Leaderboard, hal.cs.princeton.edu (Princeton; arXiv id
**unverified**). 246 entries in our harvest.

HAL is the exception to most of this document and deserves saying so plainly: **it runs the agents
itself** rather than accepting a submitted number, on a fixed harness-runner, and reports cost
alongside accuracy. Its rows are the closest thing in the data to an independent evaluation, and
`mark_comparable.py` re-homes them from the board family to the benchmark named in the split so
they are not discarded as "HAL is not a benchmark".

Two limits. First, HAL's split column names the benchmark but not the benchmark's split, so 138 of
its rows blank as `split_missing`; where HAL's configuration is known, the extractor should state
the split rather than have this script assume it. Second, HAL's `swebench_verified_mini` is a small
subset of SWE-bench Verified (**unverified**: we have not confirmed the instance count), so its
numbers are not SWE-bench Verified numbers even when the metric matches.

## The four cross-cutting caveats

### 1. Versioning

Handled mechanically, and worth checking that it was. `comparable_key` puts the split inside the
key, folds a qualifier written in the benchmark column into the split position so that
`benchmark="SWE-bench Verified", split=""` and `benchmark="SWE-bench", split="Verified"` produce
one key, keeps dataset versions apart (Terminal-Bench 1.0 vs 4.0), keeps re-audited task sets
apart (OSWorld pre- and post-Verified), keeps modality apart (OSWorld observation type, tau2 voice
vs text), and refuses a key to any split string it does not recognise — because an unrecognised
split string is most often the signature of a restricted subset ("first 100 instances"), which is
exactly what must not be pooled with a full split. The residual risk is a *silent* subset: a paper
that reports "SWE-bench Verified" while having run 200 of the 500 instances is indistinguishable
from one that ran all of them.

### 2. Contamination

Argued above under SWE-bench, which is where the dispute is live. The general shape applies to any
benchmark built from public artefacts that predate a model's training cutoff, which includes GAIA
(web questions), WebArena (scripted tasks published in 2023) and USACO (published contest
problems). It applies least to the boards whose task sets were built or re-cut after the models
they score (Terminal-Bench 4.0, SWE-bench-Live-style rebuilds).

The review does not attempt to correct for contamination and does not need to for its main claim,
because the comparison is between harnesses at a fixed model. It must not be read as evidence
about model capability, and any absolute number quoted from this dataset should carry the caveat.

### 3. Self-reporting

Verified above from the harvest: SWE-bench records verification per submission and most of its
rows are unverified (174 false and 18 absent against 131 verified); HAL carries `checked: true` on
all 246 of its entries because it verifies by construction, by running the agents rather than
accepting a number; and the other six families — 4,318 entries — carry no such field at all.
Everything else is a number submitted by the people whose system it flatters, with no re-run, no
logs requirement that we can confirm, and in several cases (WebArena's Google Sheet, OSWorld's
self-reported workbook) no submission review at all.

The consequence is a publication-bias-like asymmetry that is worse than ordinary publication bias:
it is not only that unfavourable results go unpublished, it is that the favourable ones are
measured by their authors. There is no way to correct this from the data. What we can do is keep the
flag with the row it belongs to: `scripts/leaderboards_to_results.py` writes
`swebench_checked=true` into `notes` for a verified SWE-bench submission, and marks every GAIA row
`unverified self-reported public submission`. The absence of that marker is the common case, not a
missing value, so any SWE-bench result should be reported with the verified/unverified split
beside it.

### 4. Harness-model entanglement

A leaderboard row names one artefact: "SWE-agent + GPT-4o", "OpenHands with Claude Sonnet 4". The
harness's score is therefore not a property of the harness, and the same harness with a different
model is a different row. Three ways this bites:

- **The board does not always say which model.** In our SWE-bench rows the model column contains
  `Undisclosed` 50 times and `Multiple` 33 times, and GAIA omits the model on two thirds of its
  rows. Those rows cannot hold the model fixed and get no key.
- **One row can name more than one model.** `GPT-4o & Claude 3 Opus`, `Qwen2.5 (7B + 72B)`: a
  harness using a cheap model for localisation and an expensive one for editing is a real and
  common design, and it has no single model identity. Those rows also get no key. (The
  canonicaliser distinguishes this from mixture-of-experts parameter notation such as
  `Qwen3-Coder 480B/A35B Instruct`, which is one model.)
- **What the model column does not say.** Reasoning effort, thinking budget, temperature, context
  window, and any auxiliary model inside the harness (retriever, reranker, critic) are almost never
  recorded. Holding "the model" fixed by name does not hold the inference configuration fixed, and
  on current reasoning models the effort setting alone moves agent scores substantially
  (**unverified** as a quantified claim about our specific rows).

### 5. Scaffold drift

A board entry is undated relative to the harness's own version. The row may carry a submission
date, but it does not say which commit of the harness produced the number, and harnesses in this
field change fast: prompts, tool sets, retry policy and loop structure all move between releases.
HARNESS-DB codes each system at a pinned commit (`path@commit`, protocol amendment 8), and there
is no guarantee that the commit we coded is the one that produced a score submitted a year
earlier. The SWE-bench `experiments` repository is the partial exception, because each submission
lives in its own directory with a `metadata.yaml`; even there, the mapping from that directory to a
harness commit is not always stated.

This is measurement error on the independent variable, not the dependent one, and that is what
makes it the most serious of the five for the regression.

## Which caveats limit which analyses

| analysis | binding caveats | what we can still say |
|---|---|---|
| **Mixed-effects regression of score on coded harness dimensions, benchmark x model fixed effects, comparable rows only** (protocol §11) | scaffold drift first, then harness-model entanglement (unrecorded inference configuration), then differential contamination | Associational only, with these three named as confounders. Coefficients are attenuated by drift in an unknown direction per dimension. |
| **Descriptive tables: which benchmarks systems report, how many systems per benchmark, reporting completeness** | none that matter | Safe. These are counts of what authors chose to report, which is exactly the quantity of interest, and unattributed rows can be included because no harness claim is made. |
| **Under-reporting result (RQ4), from coding not from scores** | unaffected by this document | Safe. It rests on `not_reported` cells, whose reliability is addressed in `docs/coding_reliability.md`. |
| **Convergence of designs over time** | scaffold drift, versioning | Report on coded systems at their pinned commits, not on leaderboard dates. |
| **Cost and token comparisons** | self-reporting, plus prices that changed under the same model name | Descriptive only, never a ranking. HAL rows are the only ones where cost was measured by the evaluator. |
| **Any absolute capability statement ("agents resolve X% of real issues")** | contamination, self-reporting, silent subsetting | Out of scope. The review does not make these claims. |

**The caveat that most threatens the regression is scaffold drift.** The other four attack the
outcome variable, and the design answers them: keying on benchmark, split, metric and model
absorbs versioning entirely, holds the model fixed against contamination and entanglement, and
leaves self-reporting as a bias shared by the rows being compared. Scaffold drift attacks the
*treatment* variable instead. If the harness we coded is not the harness that produced the score,
then the regressor is mismeasured, no fixed effect can absorb it, and the direction of the
resulting bias differs per dimension — attenuating dimensions that changed often (prompting,
retries, tool sets) more than ones that are architecturally stable (multi-agent topology,
sandboxing). Any reported coefficient should be read as a lower bound on the association, and the
review should report, per row, how far the score's date sits from the commit we coded.

---

*Written for Phase 6 task 46. The mechanical half of this problem is implemented in
`scripts/mark_comparable.py` (task 45) and tested in `tests/test_mark_comparable.py`; the
per-run counts are in `data/comparable_summary.json`.*
