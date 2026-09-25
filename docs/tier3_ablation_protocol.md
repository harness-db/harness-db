# Tier 3: our own controlled ablation of self-verification

**Status: pre-specified, no data collected.** This document is written and frozen *before* any run, and
filed as OSF amendment 12, for the reason that the rest of the paper is about: findings 6 and 7 are both
author-reported, and an unregistered ablation of our own would be one more self-report. Nothing below may
be changed after the first confirmatory instance is scored; changes before that point are logged here
with a date and a reason.

Tracker task 51. Supersedes the task's original wording ("five-system API validation of one headline
finding, budget 200-500 USD"): the target is a design dimension, not five systems, because finding 7
identified a specific dimension worth the money and a five-system spot-check would not have a
counterfactual.

## Why this dimension

`self_verification` is the only dimension in finding 7 that survives its own bias diagnostics:
pooled +0.139 relative, discounted to **+0.069**, on 14 papers and 20 contrasts, with trim-and-fill
finding nothing to impute. It is also the dimension with the most ablations in the corpus, so if the
literature is right about anything, it is right about this. Every one of those 20 contrasts is an author
reporting on their own component.

## The hypothesis the literature actually supports, and the one it does not

The published contrasts compare a harness *with* a verification step against the same harness *without*
it. A verification step issues extra model calls: generate, run checks, read failures, repair. So each
published contrast varies two things at once, and its estimate answers:

> **H1 (what the literature tests).** A harness that verifies scores higher than the same harness that
> does not. Confounded with compute.

It cannot answer the question a harness designer actually has:

> **H2 (what we test).** At *equal compute*, a harness that spends its extra calls on verifying and
> repairing scores higher than one that spends them on unguided retries.

H2 is the contribution. If H2 holds, self-verification is a design choice. If H2 is null while H1 holds,
then the +0.069 in finding 7 is a **compute effect wearing a design label**, and every paper in that
forest plot has mismeasured its own contribution. Either result is publishable and neither is available
anywhere in the 6,504-system census, because **no paper in the corpus runs a compute-matched control.**

## Arms

Three arms, one codebase, one model, one temperature, one task suite, one scoring script. The only
difference between arms is what the harness does with its call budget.

| arm | calls | what it does |
|---|---|---|
| **A** baseline | 1 | one attempt, no checking, no retry |
| **B** verification | up to *k* | attempt, then run self-written checks, read the failures, repair; stop when checks pass or *k* is spent |
| **C** compute-matched | exactly the number B used on that instance | independent unguided attempts, no checks, no feedback; final answer by self-consistency where the task admits it, else last attempt |

**C is matched per instance, not on average.** B's call count is recorded while B runs, and C is then
given that same count on that same instance. An average match would let a few expensive B instances
subsidise cheap ones and reintroduce the confound at the instance level.

Primary comparison: **B vs C, paired by instance.** Secondary: B vs A (this reproduces the literature's
design and should recover something near +0.069 if our setup is comparable to theirs — it is the
calibration check, not the result). Also reported: C vs A, which is the pure compute effect.

## Task suite: chosen by pilot, against pre-stated criteria

Chosen *before* the confirmatory run by a pilot on a disjoint instance set, on criteria fixed now:

1. **Automatically scorable** against hidden checks the harness never sees.
2. **Baseline (arm A) accuracy in the 25-70% band.** Outside it, ceiling or floor destroys the power to
   see a 7-point move. This is the criterion that rules out saturated suites; HumanEval-style sets sit
   above the band for current models and are excluded on that ground, not on taste.
3. **A continuous per-instance score** (fraction of hidden checks passed), not only pass/fail. A binary
   outcome needs roughly 500 paired instances for 80% power at +7pp; the continuous one needs far fewer,
   and the binary version is still reported as a secondary.
4. **Post-cutoff or contamination-resistant** where it can be had, and the contamination risk stated
   where it cannot. Contamination inflates all three arms and is largely differenced out by the pairing,
   which is a genuine advantage of this design and is claimed as no more than that.

The pilot reports arm-A accuracy per candidate suite and the suite is picked by criterion 2 alone. If no
candidate lands in the band, **that is reported as a failed experiment** and no arm comparison is
published — not a re-tuned band.

## Model

Whatever tier the pilot shows to sit in the accuracy band, run on the subscription path (`claude -p`),
recorded per row. If that is a smaller model than the frontier, the claim is scoped to it explicitly:
verification plausibly helps weaker generators more, so a positive H2 on a small model is an **upper
bound** for frontier harnesses and is worded that way. Scoping the claim is the cost of not having API
budget; misstating its scope is not an acceptable alternative.

## Analysis, fixed now

- **Primary:** paired difference in per-instance check-pass fraction, B − C. Bootstrap CI over
  **instances** (10,000 resamples), plus a within-instance permutation test that swaps arm labels.
- **Secondary:** McNemar on binary success, B vs C.
- **Seeds:** *s* independent runs per arm per instance, averaged within instance before the paired
  contrast, so run-to-run variance does not masquerade as an effect. *s* fixed by the pilot's observed
  variance, minimum 3.
- **Minimum detectable effect reported whether or not the result is significant**, computed the same way
  as in `analyse_outcomes.py`, so a null is interpretable rather than silent.
- **Stopping rule:** the instance count is fixed by the pilot power calculation and run to completion.
  No peeking, no stopping early on a significant interim, no adding instances after seeing the estimate.
- **Pre-specified subgroup, one only:** instances where arm A failed. Verification cannot help where the
  first attempt already succeeded, so the effect should concentrate there; any further subgroup is
  exploratory and labelled so.

## What would make us wrong

Stated in advance so the result cannot be reinterpreted afterwards:

- **B ≈ C with both > A** → self-verification is a compute effect; finding 7's +0.069 is an upper bound
  on a quantity that is not a design choice. This is the outcome that most changes the paper.
- **B > C** → self-verification is a real design choice; our estimate is the only unbiased one in the
  literature and finding 7's +0.069 gains a floor.
- **B < C** → verification actively wastes budget at this scale; report it, and check the repair prompt
  for a defect before believing it.
- **A outside the 25-70% band in the confirmatory run** despite the pilot → report the run as
  uninformative and say so; do not switch suites post hoc.

## Threats this design does *not* remove

- One harness, ours. Generalisation to the 6,504-system census is an argument, not a measurement.
- One task suite, and verification is more natural in some domains (code with runnable tests) than
  others. The result is scoped to the domain the pilot picks.
- Our own repair prompt could be weak, which would understate B. Mitigation: the prompt is written once,
  before the pilot, and not tuned between arms or after seeing results. Any change is logged here.
- We are the authors of this ablation, which is the exact bias finding 7a measures. Mitigation is
  procedural and partial: this document is frozen and registered first, the compute-matched control is
  the arm that can embarrass us, and the raw per-run logs are released so the contrast can be recomputed
  by anyone.

## Outputs

`data/tier3/runs.jsonl` (one row per instance per arm per seed: prompt, response, calls, tokens, score,
model, timestamp), `data/tier3/instance_scores.csv`, `data/analysis/tier3_summary.json`,
`paper/figures/tier3_arms.svg`. The pilot writes to `data/tier3/pilot/` and is never pooled with the
confirmatory run.

## Protocol notes

Dated log entries, appended. Nothing above this heading has been edited, and no entry below changes
the band, the arms, the primary outcome or the analysis plan.

### 2026-09-25 — first pilot failed the band; candidate set extended under unchanged criteria; a suite now selects on criterion 2 but cannot supply the instances the analysis plan requires

**1. What the first pilot found.** Arm A only, on the disjoint pilot pool, into `data/tier3/pilot/`,
scored on the primary outcome of criterion 3 (mean per-instance fraction of hidden checks passed):

| suite @ tier | instances × seeds | arm A, continuous | arm A, binary |
|---|---|---|---|
| `mbpp` @ sonnet | 25 × 3 | 0.933 | 0.933 |
| `mbppplus` @ sonnet | 25 × 3 | 0.927 | 0.893 |
| `bigcodebench_hard` @ sonnet | 16 × 3 | 0.754 | 0.542 |

All three sit above the pre-stated 25-70% band, `selected` was null, and the rule in *Task suite*
fired: a failed experiment, not a re-tuned band.

**2. What was extended, and what was not.** The frozen text above fixes the selection *criteria*, not
the list of candidates, so the search continued with the band, the arms, the primary outcome and the
analysis plan untouched, and selection still by criterion 2 on the continuous measure. The failure
mode was a ceiling, so the two admissible levers were a harder suite and a weaker generator. Every
addition satisfies criteria 1, 3 and 4 as before — automatically scorable against hidden checks the
harness never sees, a continuous per-instance score, no Docker, runs on Windows, contamination stated
— and everything ran on the subscription path (`claude -p`). The Anthropic API was not used at any
point.

1. **A weaker generator tier: `haiku`** (`claude-haiku-4-5`), the weakest tier the subscription path
   offers, across the suites already prepared. Per *Model*, a positive result at this tier would be
   scoped to it as an upper bound for frontier harnesses.
2. **`bigcodebench_hard_instruct`** — the Instruct presentation of BigCodeBench-Hard. Same 148 tasks,
   same hidden `unittest` methods, same scorer, same gold filter; the docstring's worked examples are
   withheld and the specification is given as prose, so the model is shown less of it. Harder by
   construction, and not a change of measurement. No new download: the raw release was already in
   `data/tier3/suites/raw/`. 57 instances survive the gold filter (23 pilot / 34 confirmatory).
3. **`bigcodebench` and `bigcodebench_instruct`** — the full 1,140-task split in both presentations,
   added because the Hard split leaves only 34-41 confirmatory instances after the no-Docker gold
   filter, well under the instance counts in §5. Raw file also already local. The full split was
   prepared: **555 instances survive the gold filter** (156 pilot / 399 confirmatory, 585 dropped),
   so instance supply is not the constraint there. **Neither full-split candidate was measured**, on
   instruction to stop extending the candidate set; both stay registered in `SUITE_SOURCES` and
   `BUILDERS`, and `bigcodebench` is prepared on disk.

**3. The extended grid.** Arm A, pilot pool, `data/tier3/pilot/pilot_summary.json`:

| suite @ tier | instances × seeds | arm A, continuous | arm A, binary | in band |
|---|---|---|---|---|
| `mbpp` @ sonnet | 25 × 3 | 0.933 | 0.933 | no |
| `mbpp` @ haiku | 25 × 1 | 0.800 | 0.800 | no |
| `mbppplus` @ sonnet | 25 × 3 | 0.927 | 0.893 | no |
| `mbppplus` @ haiku | 25 × 1-3 | 0.924 | 0.867 | no |
| `bigcodebench_hard` @ sonnet | 16 × 3 | 0.754 | 0.542 | no |
| `bigcodebench_hard` @ haiku | 16 × 1 | 0.717 | 0.375 | no |
| `bigcodebench_hard_instruct` @ sonnet | 23 × 3 | 0.741 | 0.464 | no |
| **`bigcodebench_hard_instruct` @ haiku** | **23 × 3** | **0.648** | **0.246** | **yes** |
| `bigcodebench_instruct` @ either | not measured | — | — | — |
| `bigcodebench` @ either | not measured | — | — | — |

One cell is inside the band on the primary outcome, and `summarise_arm_a` selects it by criterion 2:
`bigcodebench_hard_instruct` @ haiku, 0.648. Stated with it, because it matters for what follows: with
`sd_between = 0.288` on 23 instances the standard error of that estimate is 0.060, so its 95% interval
is roughly [0.53, 0.77] and crosses the band's 0.70 ceiling. The point estimate is 5 points inside the
band; the interval is not.

**4. Arm B mostly declines to spend its budget — measured, and not uniform across candidates.** An
arm-B-only diagnostic (`data/tier3/diagnostic/`; no arm C is run anywhere in it, so it contains no
B−C contrast and nothing in it is an effect estimate) measured how often B's own self-written checks
fail and it therefore reaches a repair at all:

| suite @ tier | rows | mean B calls | B retried | p_active |
|---|---|---|---|---|
| `bigcodebench_hard` @ sonnet | 15 | 1.13 | 2 | 0.133 |
| `mbppplus` @ sonnet | 15 | 1.00 | 0 | 0.000 |
| `bigcodebench_hard` @ haiku | 11 | 1.00 | 0 | 0.000 |
| `bigcodebench_hard_instruct` @ haiku | 15 | 1.47 | 4 | 0.267 |

The self-checks were written and executed on every row in all four cells, so this is not a plumbing
failure: it is that the model's own checks pass on code that then fails the hidden checks. On
`bigcodebench_hard_instruct` @ haiku, B stopped after a single call on instances scoring 0.167, 0.600,
0.667 and 0.800 against the hidden tests.

Where B does not retry, B stops at one call, C is matched to one call, and the two arms differ only in
the instruction to write checks alongside the answer — so the paired difference on those instances is
structurally uninformative about verification rather than merely noisy. Writing the per-instance
difference as 0 on (1 − p) of instances and g on the rest, the estimand is p·g, the required n is
(z for 1−α/2 plus z for power), squared, times (1 − p)/p, and, since g ≤ 1, **the largest average
effect this design can produce is p itself**. Reaching the pre-registered +7 points needs a gain of
0.07/p on every active instance, so **p must be at least 0.07 for +7 points to be attainable at any
sample size**:

* p = 0.000 (`bigcodebench_hard` @ haiku, `mbppplus` @ sonnet): unattainable at any n.
* p = 0.133 (`bigcodebench_hard` @ sonnet): needs a 0.525 gain on every active instance; n = 54.
* p = 0.267 (`bigcodebench_hard_instruct` @ haiku): needs 0.263; n = 24. The 95% interval on 4 of 15
  runs from about 0.08 to 0.55, so this is thin evidence, but it does **not** support a claim that the
  treatment never fires on the selected candidate.

**5. Why the selected candidate still cannot be run, and it is the analysis plan that says so, not the
band.** *Analysis* fixes the instance count by the pilot power calculation and requires it run to
completion. On `bigcodebench_hard_instruct` @ haiku the pilot gives `var_run = 0.0419`, hence `s = 12`
seeds by the pre-stated rule, and the paired instance counts for 80% power at +7 points are 282
(ρ = 0), 146 (ρ = 0.5), **93 (ρ = 0.7)** and 40 (ρ = 0.9). The split supplies **34** confirmatory
instances. The two power routes disagree — 24 by the active-fraction route in §4, 93 by the variance
route at a plausible ρ — and the binding one is the larger. So the suite selected by criterion 2
cannot supply the instances its own pilot variance demands, at any ρ below about 0.9, and 91 of the
148 BigCodeBench-Hard tasks are unavailable in the first place because they fail the gold filter
without Docker.

**6. Two things recorded as observations and deliberately not acted on.**

* **A measure ambiguity in the frozen text above, flagged and left unresolved.** Criterion 2 says
  "baseline (arm A) accuracy in the 25-70% band" without naming a measure, while criterion 3 makes the
  continuous fraction the primary outcome and the binary version a secondary. On the **binary**
  measure `bigcodebench_hard` @ sonnet is 0.542 — almost dead centre of the band. Reading criterion 2
  against the binary measure would let the experiment proceed on a suite with 41 confirmatory
  instances, which is precisely why it is not read that way here: choosing the measure that puts a
  suite in band after seeing the numbers is measure-shopping, and it would destroy the only unbiased
  estimate in the paper. **This is an open question for the author to resolve in writing, at
  registration, before any confirmatory instance is scored.** Every number in §1 and §3 is reported on
  both measures so that either resolution can be read off the same pilot.
* **The continuous measure sits far above the binary one on this family, and the two presentations
  were not measured on the same instances.** Partial credit over `unittest` methods runs well above
  the binary pass rate (0.754 vs 0.542 on `bigcodebench_hard` @ sonnet; 0.648 vs 0.246 on
  `bigcodebench_hard_instruct` @ haiku), so a suite can only reach the middle of the band on the
  continuous measure by sitting near the floor on the binary one. An earlier partial reading of this
  pilot reported the Instruct presentation as scoring *higher* on continuous (0.774) than Complete
  (0.754) while scoring *lower* on binary (0.485 vs 0.542) — the harder presentation looking easier on
  the primary measure. The completed pilot-pool measurement in §3 does not reproduce that inversion
  (Instruct @ sonnet is 0.741 continuous and 0.464 binary, both below Complete), and the two
  presentations were in any case measured on largely different instances, because the pilot pool hash
  includes the suite name: they share only 5 pilot task ids at sonnet and 2 at haiku. The inversion is
  therefore **not established by our data**; the gap between the two measures is. Recorded, not acted
  on.

**7. What is reportable with no amendment.** The arm-B diagnostic in §4 is a descriptive measurement
of our own pilot — one arm, no contrast between arms — so it can be reported as a result of this work
without amending this document. Across 56 arm-B pilot rows at two tiers on three suites, a harness
that writes its own checks and runs them accepted its first attempt on 50 of 56, including on
instances that failed most of the hidden checks. That is a measurement of how sensitive
author-written self-verification is to its own errors, and it is the mechanism finding 7's forest plot
cannot see.

**8. Where this leaves Tier 3.** No candidate measured is both in the band and able to supply the
instances the analysis plan requires, so on the evidence in hand **Tier 3 should be reported as a
failed experiment**, with the pilot grid in §3 and the diagnostic in §4 published and no arm
comparison. One untested candidate could change that and is named here so the decision is the
author's rather than an omission: **`bigcodebench_instruct` @ haiku**, the Instruct presentation of
the full split, which supplies roughly 390 confirmatory instances against the 93 that §5 needs, and
which is the same presentation and tier as the cell that selected on criterion 2. Whether its arm-A
accuracy falls in the band is unmeasured; settling it costs about 25 arm-A calls. Measuring it is
within these criteria, changes nothing above this heading, and is not a re-tuning of the band.

**9. Confirmatory status: not started.** `data/tier3/runs.jsonl` does not exist,
`data/tier3/REGISTERED.txt` does not exist, and `cmd_confirmatory` refuses to score a confirmatory
instance without both that marker and `--registered`. Everything in this entry is pilot-pool and
diagnostic data.

### 2026-09-25, later the same day — the untested candidate of §8 was measured; it is out of band; Tier 3 is a failed experiment

**Why this measurement was made after the search had been stopped.** The entry above was written under
an instruction to stop extending the candidate set, given on the belief that arm B never spends its
budget. §4 showed that belief was measured on the Complete presentation only and does not hold on the
Instruct presentation (p_active = 0.267). **The coordinating agent withdrew its own stop instruction**
on being shown that, and asked for the one cell §8 had named. The withdrawal was the coordinator's,
not this author's, and it is logged here because a reader is entitled to know why the candidate list
grew by one after a stop. Nothing frozen was touched: same band, same arms, same primary outcome, same
analysis plan, same prompts, same criteria, subscription path only.

**`bigcodebench_instruct` prepared:** the Instruct presentation of the full 1,140-task split. **556
instances survive the no-Docker gold filter** (169 pilot / **387 confirmatory**, 584 dropped) — ample
against the 93 that §5 requires, which is exactly why it was worth measuring.

**Result: out of band, and not marginally.** Arm A, 25 pilot instances, 1 seed:

| suite @ tier | instances × seeds | continuous | binary | 95% CI (continuous) | in band |
|---|---|---|---|---|---|
| `bigcodebench_instruct` @ haiku | 25 × 1 | **0.852** | 0.560 | [0.757, 0.948] | **no** |

The **entire interval sits above the band's 0.70 ceiling**, so this is not a near-miss and no further
instances would change it: the point estimate is 0.152 above the ceiling and, at `sd_between = 0.231`,
only 12 instances were needed to separate it from the boundary — 25 were run. The full split is simply
much easier than the Hard split it was drawn from (0.852 vs 0.648 at the same tier, same presentation),
which is what the Hard split was constructed to be.

Its **binary** rate is 0.560, near the centre of the band. Per §6 that is recorded and **not acted
on**; it is the same measure-shopping temptation as `bigcodebench_hard` @ sonnet at 0.542, and it is
declined for the same reason.

**Intervals for the boundary cells, as promised in §3.** The distance from each point estimate to the
nearest band boundary, and the number of pilot instances that would be needed for a 95% interval to
clear it:

| suite @ tier | continuous | distance to boundary | instances to resolve | pilot instances the split has |
|---|---|---|---|---|
| `bigcodebench_hard_instruct` @ haiku | 0.648 | 0.052 | **121** | **23** |
| `bigcodebench_hard` @ haiku | 0.717 | 0.017 | 1,280 | 16 |
| `bigcodebench_instruct` @ haiku | 0.852 | 0.152 | 12 | 169 |

So the one cell that selects on criterion 2 cannot have its band membership resolved on the split it
comes from: it would take 121 pilot instances and that split's pilot pool holds 23. This is
independent of, and additional to, the §5 finding that its 34 confirmatory instances fall short of the
93 the analysis plan requires.

**Verdict: Tier 3 is a failed experiment and should be reported as one.** Ten (suite, tier) cells were
measured on the pilot pool. Nine are out of band on the primary continuous outcome. The tenth,
`bigcodebench_hard_instruct` @ haiku at 0.648, is in band on the point estimate but (a) its 95%
interval crosses the ceiling and cannot be resolved on a 23-instance pilot pool, and (b) its split
supplies 34 confirmatory instances against a required 93. The rule in *Task suite* therefore applies as
written: **no arm comparison is published, and the band is not re-tuned.** What is published is the
pilot grid, the intervals above, and the arm-B self-check diagnostic of §4, which needs no amendment.

No confirmatory instance has been scored. `data/tier3/runs.jsonl`, `data/tier3/instance_scores.csv`
and `data/tier3/REGISTERED.txt` are all absent, and `cmd_confirmatory` refuses without the marker and
`--registered`. OSF amendment 12 remains pending on the author.

**Two writers on the pilot file, and why the pool is still sound.** A second Claude Code session was
active in this repository during this work and appended arm-A rows for `bigcodebench_hard_instruct` @
sonnet (23 instances × 3 seeds) to `data/tier3/pilot/runs.jsonl` concurrently with this author's runs.
Recorded so that no reader is surprised by it, together with the check that makes it harmless. Every
row carries `key = suite|instance_id|arm|seed|model`; `done_keys` counts only `status == "ok"` rows and
`latest_ok` keeps one row per key, so a row written twice collapses to one and can never double-count.
Verified on the final file: **454 rows, 454 `ok` rows, 454 distinct keys, 0 duplicated keys, 0
unparseable or truncated lines, 0 rows on an instance outside its suite's pilot pool, arm A only, phase
`pilot` only.** The pilot/confirmatory split is by `pool_of`, a hash of suite and instance id, so it
does not depend on which process wrote a row or in what order; no confirmatory instance was touched by
either writer.

## Amendment 12a (2026-09-25)

**Status: a dated amendment to the design above, made before registration. It changes the design;
the protocol notes above did not.** Nothing is registered at OSF (amendment 12 is pending on the
author) and no confirmatory instance has been scored, so a reasoned change to the frozen text is
still legitimate; after registration it would not be. The frozen text is therefore **not edited**:
it stays byte-identical and this amendment is appended below it, with the reason and the evidence
for each change. SHA-256 of the file above this heading, i.e. the frozen text plus both protocol
notes, before this amendment was appended: `489f1c660feb7b7c8808cd5fcd6cbe058fbc0a42fbd563925bb5d4dba6527b55`
(25,364 bytes). SHA-256 of the frozen text alone (everything above `## Protocol notes`):
`e5572e379894bdd8aab4c5ece6040558c12310191b7d105c372919bbdfee8a39` (8,603 bytes). Both were
recomputed after this amendment was written and are unchanged.

"v1" below is the design above as frozen; "v2" is v1 with this amendment applied. Which one is
registered is the author's decision at registration, and §7 says what each can deliver.

### 1. What v2 keeps from v1, unchanged

H1/H2 and the reason for testing H2; three arms, one generation path, one model, one scorer; arm C
compute-matched **per instance** to the B arm that actually ran on that instance; the paired analysis
by instance (bootstrap over instances, 10,000 resamples, plus the within-instance permutation test);
McNemar as the binary secondary; the seed rule; the MDE reported whether or not the result is
significant; the stopping rule (n fixed by the pilot power calculation, run to completion, no
peeking); the one pre-specified subgroup (instances where arm A failed); the 25-70% band and the
rule that a failure to find an in-band suite is reported as a failed experiment; the subscription
path; the hidden checks unreachable by construction; the +7-point target; the "what would make us
wrong" list, read with B meaning the v2 arm. Every v1 prompt template is byte-identical
(`prompt_sha` `886978ae5bec746f`, pinned by a test), and v1 arm B is still implemented, unchanged,
as arm `B` ("B-self" below).

Three things change, each because the v1 pilot showed it broken, and one hole the amendment work
found is closed (§5).

### 2. Change 1: arm B must spend its budget

**Evidence.** In the v1 diagnostic (protocol notes, §4) arm B's model-written checks accepted the
first attempt on 50 of 56 runs (mean 1.16 calls), three of those 50 scoring 0.00 against the hidden
tests. Where B stops at one call, C is matched to one call, and the two arms differ only in the
instruction to write checks. A v1 null would therefore be uninterpretable: "our verification never
ran" would read as "verification does not help".

Two replacement definitions were specified, implemented on the same single generation path
(`scripts/tier3_ablation.py`, arms `Bfix` and `Bext`) and piloted. Both keep v1's ceiling `k = 4`,
and C is matched per instance to whichever one ran (row label `C@Bfix` / `C@Bext`, so a C matched
to one variant can never satisfy another's resume check).

* **B-fixed (`Bfix`): mandatory verify-and-repair rounds.** Exactly `k` calls on every instance:
  the v1 first call (code plus self-written checks), then `k − 1` rounds whatever the checks say. A
  failing round is fed back with v1's repair block, unchanged. A passing round, which in v1 stopped
  the loop, is now followed by one new block, written once before this pilot and not tuned after:
  *"your own checks passed on it. Checks you wrote yourself can pass on code that is still wrong,
  so verify it again: re-read the task statement, compare it with the code, look for required
  behaviour your checks do not exercise, strengthen the checks, and repair the code if anything is
  wrong."* This keeps v1's treatment (self-verification) and removes only its option to decline.
  It cannot stop early, so p_active = 1 by construction.
* **B-ext (`Bext`): verification against externally supplied public checks.** The harness runs the
  benchmark's own worked examples - the `>>>` examples in the task docstring of BigCodeBench's
  released `complete_prompt` - and feeds the doctest failure report back with a second new block
  (*"The task's public examples were run against it and produced the output that follows. Repair
  the code so that the examples pass …"*). It stops when the examples pass, like v1. The model is
  not asked to write checks, so **B-ext's first prompt is byte-identical to arm A's** (a test pins
  this): its first attempt is an arm-A draw, and "B-ext repaired" is exactly the event "an arm-A
  draw failed the public examples". This is what real harnesses do when they run a repository's
  test suite (SWE-agent and its descendants), rather than asking the model to invent tests.

**B-ext changes the meaning of the treatment, and that is stated, not hidden.** It is no longer
*self*-verification. B-ext − C measures verification against a signal the model did not write, at
equal compute, which is exactly the distinction finding 7e raises (model-written checks pass on
code that fails). It also changes what the model can learn: on the Instruct presentation the worked
examples are precisely what the presentation withholds from the prompt, and a B-ext repair prompt
shows the ones that failed. B-ext − C therefore bundles "a verification loop" with "access to
public examples through their failures"; it cannot separate the two and is not claimed to.

**Public checks are never hidden checks, by construction and by test.**
`parse_docstring_examples` takes the program stub and the entry point and nothing else, so no public
check can have come from the hidden test. `build_visible_checks` then (a) withholds any example whose
expected value the hidden test also asserts (normalised as in `verify_no_leak`, both the expected
output alone and call-plus-output, at the same 8-character floor), and (b) applies the same gold
filter as the hidden tests: the released canonical solution must pass every kept example in this
environment, dropped iteratively because a failed setup line breaks the lines after it. The hidden
test is used only to delete. `verify_visible_disjoint` re-checks both directions on every load, and
`verify_no_leak` now also builds the forced-review prompt, the public-examples repair prompt and a
repair prompt quoting *every* public example of the instance, and raises `HiddenTestLeak` if a
hidden check is reachable through any of them. Public checks are stored beside the suites
(`data/tier3/suites/visible/`), never inside them; the prepared suite files are untouched. The public
example runner forgets the modules `doctest` imports before the candidate runs, so a candidate meets
the same import environment it meets under the hidden-test scorer (a test pins this; without it, an
`import asyncio` would pass the public examples and fail the hidden tests).

**Coverage is partial, and that scopes B-ext.** Of 186 docstring examples on the 57 Hard-Instruct
instances, 11 were withheld as overlapping a hidden assertion and 88 failed the gold filter (paths
that do not exist here, clocks, printed plot objects); 87 survive, on **27 of 57 instances** (11 of
23 pilot, 16 of 34 confirmatory). On the full split: 1,696 parsed, 100 withheld, 536 gold-dropped,
1,060 kept, on **339 of 556 instances** (101 of 169 pilot, 238 of 387 confirmatory). B-ext is
defined only on instances with at least one public check; elsewhere it cannot fire and runs one call.

### 3. Change 2: the primary estimand is conditional on the treatment firing

**Evidence: the p_active arithmetic of v1.** Protocol notes §4: writing the per-instance B − C
difference as 0 on the (1 − p) instances where B does not retry and g on the rest, v1's estimand is
p·g, its largest attainable value is p itself, +7 points needs p ≥ 0.07 at any sample size, and at
the measured p (0.000, 0.000, 0.133, 0.267) it was either unattainable or needed a gain of 0.26-0.53
on every active instance. The unconditional contrast spends almost all of its instances measuring a
difference the design has fixed near zero. v2 estimates g directly.

**Primary (v2).** The paired difference B − C in per-instance check-pass fraction, **on the
instances where the treatment fires**, each instance's B and C averaged over all *s* seeds (no seed
is dropped), analysed exactly as v1's primary (bootstrap over instances, permutation test, MDE).
**Co-primary, descriptive:** p_active (the share of B runs with at least one repair) and q (the share
of instances in the firing stratum), each with a Wilson 95% interval, so that the reader always
knows what fraction of the population the conditional estimate speaks for. **Secondary:** the
unconditional B − C over all instances (v1's primary, now reported, not tested), and McNemar on
binary success within the stratum. The single pre-specified subgroup (arm A failed) is kept.

**"Where the treatment fires" is defined on an arm that is not in the contrast.** The literal
reading - instances where B performed at least one repair - conditions on a post-randomisation
outcome of one of the two arms being compared: a B run repairs *because its first draw was bad*,
while C's draws are not selected at all, so the literal stratum biases B − C against B. v2 therefore
defines the stratum as follows, and reports the B-defined stratum as a sensitivity analysis:

* **B-fixed:** every instance. p_active = q = 1 by construction; the conditional and unconditional
  estimands coincide, and the question does not arise.
* **B-ext:** instances with at least one public check on which **at least one of the *s* arm-A draws
  fails the public examples**. Because B-ext's first prompt is byte-identical to A's, that is the
  event that makes B-ext repair, measured on arm A, which is neither B nor C. Scoring an arm-A draw
  against the public examples needs no model call.
* **B-self (v1, if registered instead):** no arm-A proxy exists (A writes no checks), so the stratum
  is B-defined and the bias above is stated as a limitation.

**What the conditional estimand costs.** It answers "when verification has something to act on,
does it beat unguided retrying at equal compute?", which is H2 in its sharpest form, but it speaks
only for the stratum; the population-level contrast is q times it (plus whatever B gains by
*accepting* a first draw that passed its checks, which C cannot do). The instance count is the
variance-route n for +7 points within the stratum, divided by q (`firing_power`).

### 4. Change 3: criterion 2 is read on the continuous primary - the ambiguity flagged in v1, resolved

Protocol notes §6 flagged that criterion 2 ("Baseline (arm A) accuracy in the 25-70% band") names no
measure, and left it for the author. **v2 resolves it on the continuous measure**, for a reason that
does not depend on which cell passes: criterion 2 states its own purpose - "outside it, ceiling or
floor destroys the power to see a 7-point move" - and the 7-point move is defined on the primary
outcome, which criterion 3 and *Analysis* make the per-instance fraction of hidden checks passed.
v2 does not change the primary outcome, so a band meant to guarantee headroom on it must be read on
it. A cell at 0.852 continuous has 0.148 of average headroom on the measure the effect is tested on,
whatever its pass rate. The competing reading - "accuracy" as the conventional name for pass@1, and
HumanEval saturation being stated in pass@1 - is acknowledged and rejected on that ground: it would
guard headroom on the secondary outcome while the test is run on the primary.

**The check that this was not chosen for its result.** On the binary reading, the in-band cells are
`bigcodebench_hard` @ haiku (0.375) and @ sonnet (0.542), `bigcodebench_hard_instruct` @ sonnet
(0.464) and `bigcodebench_instruct` @ haiku (0.560); `bigcodebench_hard_instruct` @ haiku falls out
(0.246), and v1's selection rule (closest to the band's centre) picks `bigcodebench_hard_instruct` @
sonnet, whose split supplies 22 clean confirmatory instances (§5) - no more runnable than the cell the
continuous reading selects. Neither reading rescues the experiment, so neither was chosen to.

**What it selects: unchanged.** `bigcodebench_hard_instruct` @ haiku, 0.648, the only in-band cell
of the ten measured, with the caveat of the second protocol note (interval crosses 0.70). **The band
is read on the population the estimand is defined on**, which for B-fixed is the suite. For B-ext it
is the instances with public checks, and there arm A is **above** the band on both candidates:
0.779 on the 11 Hard-Instruct pilot instances that have public checks (all 23: 0.648) and 0.869 on
the 16 full-split ones (all 25: 0.852). Instances whose docstring examples run in this environment
are easier ones. A reading that evaluates the band on B-ext's firing stratum instead was considered
and **declined**: it was conceived after v1 showed the full split out of band, and it selects nothing
anyway - arm A on the firing stratum is 0.780 (Hard-Instruct, 7 instances) and 0.770 (full split, 5).
Public-example failures track hidden-test failures only weakly: a draw that misprints a
`DataFrame.head()` fails the example and passes the tests.

### 5. A hole the amendment work found: pilot/confirmatory disjointness was per suite name, not per task

`pool_of` hashes the suite name with the instance id, so the pools are disjoint *within* a suite
but not *across presentations of the same task*. All 57 Hard-Instruct tasks are also full-split
tasks and also `bigcodebench_hard` (Complete) tasks. Measured: **11 of the 34 Hard-Instruct
confirmatory tasks were piloted under the Complete name** (`bigcodebench_hard` pilot and arm-B
diagnostic: 1022, 123, 560, 760, 870, 897, 906, 963, 971, 985, 990) **and 2 under the full-split
name** (123, 409). Protocol notes §6 recorded that the presentations share few *pilot* ids; the
confirmatory overlap was not recorded. It is a violation of "a pilot on a disjoint instance set", and
it would have reached v1 as well.

**v2 rule: disjointness is by task.** A confirmatory instance is one whose task has never appeared in
any pilot or diagnostic row, under any suite name, tier or presentation (`data/tier3/pilot/`,
`diagnostic/`, `pilot_v2/`). Clean confirmatory supply after this pilot: **Hard-Instruct 22** (10 with
public checks), **full split 369** (229 with public checks; 15 of them Hard tasks). The rule is a
filter over the v1 pools, not a re-hash, so no assignment that was already made changes.

### 6. The v2 pilot: three B variants, arms A and B only, pilot pool only

**What was run.** `tier3_ablation.py pilot-v2`, haiku tier (`claude-haiku-4-5`), subscription path
(`claude -p`) only, seed 1, `k = 4`, into `data/tier3/pilot_v2/` (summary `pilot_v2_summary.json`).
It covered all 23 pilot instances of `bigcodebench_hard_instruct` (the cell criterion 2 selects) and
the same 25 pilot instances of `bigcodebench_instruct` as v1's arm-A pilot, each under B-self,
B-fixed and B-ext: 144 rows, 144 `ok`, 0 on a non-pilot instance, 322 model calls, $18.56 notional
(the CLI's reported cost; nothing was billed to an API). **No arm C was run and no contrast was
formed.** The `pilot-v2` command refuses arm C and refuses the confirmatory tree, and the summary
carries no difference between arms. Arm A was not re-run. Its column comes from v1's pilot rows on
the same instances (69 rows at 3 seeds on Hard-Instruct, 25 at 1 seed on the full split), and
arm-A draws were scored against the public examples offline, with no model call. The
recommendation criteria in §7 were written before this table was read, and arm-B accuracy is not
one of them.

| suite @ haiku | B variant | n | p_active [95% CI] | mean calls | calls = 1 / 2 / 3 / 4 | B accuracy vs hidden, continuous (binary) | accepted first attempt, of which scored 0.00 |
|---|---|---|---|---|---|---|---|
| Hard-Instruct | **B-self** (v1) | 23 | 0.130 [0.05, 0.32] | 1.17 | 20 / 2 / 1 / 0 | 0.647 (0.217) | 20, 2 |
| Hard-Instruct | **B-fixed** | 23 | 1.000 [0.86, 1.00] | 4.00 | 0 / 0 / 0 / 23 | 0.616 (0.217) | none |
| Hard-Instruct | **B-ext** | 23 | 0.217 [0.10, 0.42]; 5 of the 11 with public checks, 0.455 [0.21, 0.72] | 1.48 | 18 / 2 / 0 / 3 | 0.613 (0.261) | 18, 2 |
| full split | **B-self** (v1) | 25 | 0.160 [0.06, 0.35] | 1.24 | 21 / 2 / 2 / 0 | 0.845 (0.600) | 21, 1 |
| full split | **B-fixed** | 25 | 1.000 [0.87, 1.00] | 4.00 | 0 / 0 / 0 / 25 | 0.872 (0.560) | none |
| full split | **B-ext** | 25 | 0.200 [0.09, 0.39]; 5 of the 16 with public checks, 0.312 [0.14, 0.56] | 1.52 | 20 / 1 / 0 / 4 | 0.875 (0.600) | 20, 0 |

Arm A on the same instances (v1 rows) scored 0.648 continuous (0.246 binary) on Hard-Instruct and
0.852 (0.560) on the full split. Arm-A draws that failed the public examples define the B-ext firing
stratum of §3. On Hard-Instruct, 17 of 33 draws failed, and 7 of 23 instances fired on at least one
of 3 seeds (q = 0.304 [0.16, 0.51]). On the full split, 5 of 16 draws failed, covering 5 of 25
instances at 1 seed (q = 0.200 [0.09, 0.39]).

**The accuracy column is descriptive, and its rows are not compared.** Without arm C, a difference
between two cells of this table estimates nothing the protocol defines. Each cell is also one seed
per instance on 23-25 instances. The column is reported because it was asked for, and so that no
number is withheld. It is not a result.

Three observations, all about the mechanism and none about an effect:

* **B-self replicates v1.** Pooled over both suites, it retried on 7 of 48 runs (0.146
  [0.07, 0.27]) and accepted 41 first attempts, 3 of which scored 0.00 on the hidden tests. The v1
  diagnostic showed the same picture (6 of 56 retried, 3 zeros among the 50 accepted), mostly on
  different instances.
* **B-fixed makes the treatment real.** Its own checks passed on the first attempt in 42 of 48 runs,
  so B-self would have stopped on all 42. The mandatory rounds then changed the submitted code on
  17 of 48 (11 of 23 on Hard-Instruct, 6 of 25 on the full split). The treatment now reaches every
  instance.
* **B-ext fires where it can, and it can only where public checks exist.** It repaired on 10 of the
  27 runs that had public checks (0.370 [0.22, 0.56]) and on none of the 21 without. Among instances
  with checks, its firing rate is about 2.5 times B-self's rate over all instances, but coverage caps
  it.

### 7. Recommendation, instance supply, and the N and budget a confirmatory v2 run needs

**Recommended arm: B-fixed.** Three criteria were fixed before the table was read:

1. *The treatment fires.* B-fixed fires on every instance by construction (48 of 48). B-ext fired
   on 37% of instances with public checks and on 20-22% of all instances.
2. *The estimand's population is in band.* B-fixed's population is the whole suite, and
   `bigcodebench_hard_instruct` @ haiku is the one in-band cell. B-ext's population is the
   instances with public checks, and arm A there scores 0.779 (Hard-Instruct) and 0.869 (full
   split), both above the ceiling. **No measured cell admits B-ext under criterion 2.**
3. *It tests what finding 7 pools.* B-fixed is still self-verification, the thing the 20 published
   contrasts credit, with only its option to decline removed. B-ext tests a different treatment.

B-ext is the more informative arm scientifically. It is the arm that could show whether a real
signal is what makes verification pay, which is the question finding 7e raises. It is recommended
as a **separately registered follow-up** on a suite whose public-check population lands in band,
not as this experiment's primary. The recommendation does not use which variant scored higher:
choosing an arm on its accuracy without a C would be choosing on the outcome.

**Instance supply, after §5's task-level rule.** Hard-Instruct supplies **22** clean confirmatory
instances (10 with public checks). The full split supplies **369** (229 with public checks), but it
is out of band on the continuous primary (0.852, with its interval entirely above 0.70). All 57 Hard
tasks are also full-split tasks, so the two supplies overlap. The 15 Hard tasks among the 369 are
15 of Hard-Instruct's clean 22, and the union is 376 distinct tasks: 22 Hard and 354 non-Hard. That
union cannot be in band: 22 tasks at about 0.65 and 354 at about 0.85 average near 0.84. **No
combination of the two prepared suites is both in band and large enough.**

**The N v2's estimand requires, and what 22 instances buy.** With the recommended B-fixed, q = 1,
so the stratum n is the full n. On the selected cell's variance components (`var_between` 0.0829,
`var_run` 0.0419, *s* = 12):

| ρ (B,C instance means) | 0.0 | 0.5 | 0.7 | 0.9 | 0.95 |
|---|---|---|---|---|---|
| instances for 80% power at +7 points | 282 | 146 | 93 | 40 | 27 |
| MDE with the 22 clean instances | - | 0.188 | 0.149 | 0.096 | 0.077 |

B-ext would need that n divided by q: at q = 0.304, that is 306 instances at ρ = 0.7 and 132 at
ρ = 0.9. The seed rule's own formula asks for *s* = 69 on this cell. `choose_seeds` caps it at 12;
the cap is in the code, not in the frozen text. It is left at 12 here and flagged for the author.

**Budget on the subscription path, for the recommended arm.** Each instance-seed costs **9 calls**:
A 1, B-fixed 4, C@Bfix 4. The pilot ran at about 3.9 calls a minute across 8 concurrent `claude -p`
processes, at about $0.062 notional per call. At the ρ = 0.7 planning value, 93 instances x 12 seeds
x 9 calls is **10,044 calls: about 43 hours of wall-clock at that concurrency and about $620
notional**, plus any usage-limit pauses. Those 93 instances do not exist. Running the 22 that do
costs 2,376 calls (about 10 hours, $150 notional), with an MDE of about 15 points at ρ = 0.7.

**Honest read: v2 cannot detect a 7-point effect on any prepared suite.** v2 fixes the defect that
made a v1 null uninterpretable. Under B-fixed the treatment reaches every instance, so a v2 null
would mean "forced self-verification at equal compute did not beat unguided retries", not "the
verification never ran". v2 does not fix the supply defect, and §5 makes it worse (34 → 22). 22
instances could resolve +7 points only if the arms' instance means correlated at about 0.95, and
nothing measured supports assuming that. Three routes could change this; none was taken here:

* (a) Make more Hard tasks pass the gold filter. 33 of the 91 dropped Hard tasks fail only because
  packages are missing (seaborn 9, bs4 6, cv2, psutil and others). At the pilot share, this adds at
  most about 20 clean confirmatory instances, which reaches the ρ = 0.9 column and no further.
* (b) Measure a new, harder candidate under the unchanged criteria, as the protocol notes did.
* (c) Move the band. This is declined.

**On the prepared suites, v2 is a better-specified experiment that is still under-powered. Tier 3
remains a failed experiment unless (a) or (b) supplies roughly four times the clean in-band
instances.**

### 8. Status

No confirmatory instance has been scored. `data/tier3/runs.jsonl`, `data/tier3/instance_scores.csv`
and `data/tier3/REGISTERED.txt` are absent. `cmd_confirmatory` still refuses without the marker and
`--registered`, for every B variant (tested), and it now also refuses any task a pilot has touched.
Everything in this amendment is pilot-pool data.

The implementation is in `scripts/tier3_ablation.py`: arms `Bfix` and `Bext`, `VisibleChecks`,
`build_visible_checks`, `verify_visible_disjoint`, the extended `verify_no_leak`, `task_key` and
`confirmatory_instances`, `firing_power`, and the commands `prepare-visible`, `pilot-v2`,
`report-v2` and `confirmatory --b-arm`. Every new guard has a test in `tests/test_tier3_ablation.py`.
Rows written by `Bfix`, `Bext` and their C carry protocol `tier3-v2-12a` and `prompt_sha_v2`
`92f5b5071260f7c5`. `B` rows keep `tier3-v1` and `886978ae5bec746f`.
