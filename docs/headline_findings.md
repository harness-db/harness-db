# Headline findings (Phase 7 memo, 2026-09-24)

What the analysis supports, what it does not, and the order the paper should make the claims in.
Every number here is reproducible from `data/` (see `make figures`); the per-claim sources are named.

The corpus: **6,504 systems** identified, **1,253 coded** on all 38 dimensions (47,614 cells) under a
stratified design — stratum H complete (981 systems, weight 1), P sampled 150 of 683 (weight 4.55), O
sampled 100 of 4,837 (weight 48.37). Claims about *the field* use the weighted estimates; claims about
*what was coded* use the unweighted ones. The two differ enough to invert sentences, which is finding 1.

---

## 1. The coded set is not the field, and weighting changes the story

`primary_artifact` inverts: **69.3% of coded systems are repository-primary, but only 33.3% of the
field is** — paper-primary goes from 27.5% coded to **66.0%** weighted. "Most agent harnesses ship as
repositories" is true of what a survey can easily code and false of what exists.

Six other dimensions change their modal value under weighting, and three cross the "mostly reported"
line: `open_source` 38% → 70% not reported, `execution_isolation` 42% → 64%, `tracing` 39% → 59%. MCP
adoption falls from 23.7% to 15.3% — **the MCP story is a high-visibility-stratum story.**

*Why it matters beyond this paper:* every prior harness survey we compare against samples the
well-known systems. This is the first estimate of how far that sampling distorts the picture, and the
answer is: enough to reverse the headline claim about what a harness even is.

Source: `data/analysis/value_distributions.csv`, weighted rates with stratified design SEs.

## 2. Systems document what they do, not how they are bounded

Weighted share of cells where the sources are silent, by layer:

| layer | not reported |
|---|---|
| C control loop | **24.9% ± 1.4** |
| M meta | 34.7% ± 1.3 |
| A context assembly | 40.2% ± 1.8 |
| E verification and repair | 61.0% ± 2.0 |
| D memory and state | 63.3% ± 2.0 |
| F budget and termination | 65.1% ± 2.0 |
| B tool interface | 71.4% ± 1.4 |
| H observability and governance | 72.8% ± 1.5 |
| G sandbox and environment | **81.7% ± 1.2** |

Worst individually: `network_policy` **93.3%**, `replayability` 90.6%, `filesystem_access` 87.5%,
`rollback` 86.4%, `state_persistence` 86.2%.

The gradient is not random. What a harness *is* — its loop, its topology — gets described. What bounds
it — sandboxing, permissions, budgets, rollback, replay — does not. **The layers that matter for
deploying an agent safely are precisely the undocumented ones**, and that is the paper's most
consequential single result. It is also a measurement claim, not a safety claim: we observe silence,
not absence. Amendment 9 exists because those two were being confused, and the corrected rate (48.9%
of all cells) is nearly double the pre-correction figure.

Source: `data/coded/not_reported_by_dimension.csv`, `data/analysis/under_reporting_layer_year.csv`.

## 3. The field has not converged; it has diversified

Across 38 dimensions, 2023 → 2026: **3 converged, 8 diversified, 23 stable** within estimator noise
(Miller–Madow corrected entropy, bootstrap CIs, year-dimension cells with n < 20 suppressed).

Diversifying fastest: `termination_condition` (+0.77 nats), `human_in_loop` (+0.70), `edit_primitive`
(+0.60), `tool_schema_source` (+0.42). The only solid convergence is `state_persistence` (−0.27), and
it is solid precisely because reporting *improved* while diversity fell (81% → 63% not reported).

*The honest caveat, which belongs in the text and not a footnote:* these are cohorts, not a panel, n
rises sharply each year, and entropy is conditioned on reporting. A falling entropy with rising n is
not evidence of convergence. `env_context_strategy` is the cautionary case — entropy fell while
reporting got worse in 2026, so its apparent convergence is the weakest of the three.

Source: `data/analysis/entropy_by_dimension_year.csv`, `convergence_summary.csv`.

## 4. There are no clean design families — and that is a result

Hierarchical clustering on Gower distance over the 580 systems reporting at least half their
dimensions: best eligible **k = 9, mean silhouette 0.126** against a pre-stated floor of 0.25, and
**bootstrap stability 0.547** against a floor of 0.60. It beats a marginals-and-missingness-preserving
null, but it fails both quality bars, across four linkages. **Verdict: negative.**

Three clusters are large enough and coherent enough to describe, and are labelled provisional
throughout: subagent-spawning orchestrators with explicit plan objects and full resume (n = 259);
single-agent ReAct-style loops with no delegation and no edit primitive (n = 203); pipeline and
role-handoff designs (n = 75).

This matters because taxonomy papers in this area routinely assert families. On the largest coded
corpus yet assembled, with a pre-registered quality bar, the families do not separate. Harness design
is better described as a set of **weakly coupled independent choices** than as a small number of
architectures — which is also what finding 5 shows from the association side.

Not a documentation artifact: across the three clusters holding ≥5% of the set, mean coded share is
65/68/68% — a spread of 3.5 points. The Kruskal–Wallis p = 0.00011 is driven by 4–8 system clusters.

Source: `data/analysis/family_summary.json`, `family_cluster_summary.csv`.

## 5. Design choices are weakly coupled, and shared silence manufactures the opposite impression

On complete pairs — both dimensions carrying a value — mean corrected Cramér's V is **0.166** across
703 pairs. Only one pair exceeds 0.6: `multi_agent_topology × delegation_mechanism` (V = 0.721, n =
838), which is close to definitional. The next strongest sit at 0.47–0.56 on 88–285 systems.

**The methodological result matters as much as the substantive one.** Treating `not_reported` as an
ordinary category barely moves the mean V (0.168) but takes the count of "significant" pairs from
**382 to 648 of 703**. Of those, **268 pairs are significant only when silence is a level** — the
association is documentation behaviour, not design. The worst case, `tracing × eval_hooks`, goes from
V = 0.000 on 480 complete systems to 0.240 on 1,248.

Any analysis of a half-silent matrix that treats silence as a value will find a rich correlation
structure that is an artifact of who writes documentation. We report both and make complete pairs
primary.

Source: `data/analysis/family_associations.csv`, `family_nr_flips.csv`.

## 6. Under 5% of the corpus can be compared to anything

| | systems |
|---|---|
| coded | 1,253 |
| report any benchmark score | 646 (51.6%) |
| score has a canonicalisable benchmark, split and base model | 100 |
| **share such a key with another coded system** | **53 (4.2%)** |

**593 systems report a score but never against a peer** at the same benchmark, split and base model.
36 comparable keys, 106 observations; the largest is `SWE-bench|Lite|gpt-4o` with 11 systems. Half the
corpus reports no score at all, and the 1,253 systems name **1,104 distinct benchmarks** between them.

The registered mixed-effects regression is therefore not identifiable and **was not fitted**
(amendment 11). Thirty-eight design dimensions against 36 clusters would have produced coefficients
with no support.

What is reported instead: the comparable set published in full so any claim can be checked; scores
standardised within key; five pre-specified contrasts with bootstrap intervals over keys, within-key
permutation tests, and a computed minimum detectable effect each.

**One association survives both tests:** multi-agent topology, **+1.01 within-key sd [+0.53, +1.37]**,
17 keys / 60 observations / 36 systems, permutation p = 0.0003. It is an association, not an effect of
design: 7 of its 17 keys pit a purpose-built submission against a recurring baseline harness,
reporting is author-selected, and scaffold drift puts measurement error on the regressor that no fixed
effect absorbs and that attenuates — so **+1.01 is a lower bound on magnitude**, not an estimate of it.

Three of five contrasts are nulls or non-estimable, reported with what could have been detected:
`explicit_plan` +0.27 [−0.42, +0.92] with MDE 1.12; `executable_verification` null with MDE 1.87;
`any_retry` **not estimable** — its 2 keys admit only 4 label assignments, so no p below 0.25 is
reachable whatever the point estimate. `any_compaction` reaches p = 0.042 exactly on its design floor
with all 4 keys confounded, and is reported as confounded.

Source: `paper/tables/outcomes_comparable_set.csv`, `outcomes_summary.json`.

---

## The argument the paper should make, in this order

1. **A census, not a sample** — 6,504 systems identified, 1,253 coded with evidence per cell, and
   weighting shows the convenient sample inverts the basic facts (finding 1).
2. **An under-reporting audit with a gradient** — 48.9% of cells silent, and the silence concentrates
   in exactly the layers that govern safe deployment (finding 2).
3. **No convergence and no families** — the field is diversifying on more dimensions than it is
   converging on, and design choices do not cluster into architectures (findings 3, 4, 5).
4. **The outcome literature cannot answer the design question yet** — fewer than 5% of systems are
   comparable to any peer; one association survives, as a lower bound (finding 6).
5. **A method contribution** — evidence-per-cell coding at this scale, with the two traps measured
   rather than assumed: silence treated as a value manufactures correlations (268 pairs), and a
   self-contradictory absence rule halved the under-reporting rate before it was fixed (amendment 9).

## What to be careful about in review

- **Ten of eleven amendments are pre-stage and evidence-backed; say so explicitly.** The two that will
  draw fire are 4 (no human screener) and 9 (a coding rule rewritten mid-project). For 9 the defence
  is the strongest available: the rule was rewritten, validated on 217 systems, and only then applied.
- **Reliability is reproducibility, not correctness.** Pooled kappa 0.828 with 37 of 38 dimensions
  above 0.6, but both readings are model readings. Correctness rests on reference-set recall (27/27)
  and the independent-pipeline cross-check (agreement 0.84, kappa 0.66), and those belong beside the
  kappa table, not after it.
- **`loop_primitives` is below the freeze threshold** (0.586 exact-set) and is kept because it is
  multi-valued, with per-value agreement 93%. Disclose it rather than let a reviewer find it.
- **Do not let finding 6 be read as a failed analysis.** It is a measured statement about the field's
  reporting practice, and it is the reason the design-versus-outcome question stays open.
