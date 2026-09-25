# Headline findings (Phase 7 memo, 2026-09-24)

What the analysis supports, what it does not, and the order the paper should make the claims in.
Every number here is reproducible from `data/` (see `make figures`); the per-claim sources are named.

The corpus: **6,504 systems** in the sampling frame (`data/coding_frame.json`), and `data/prisma_counts.json`
now records `included_systems` as the same **6,504** (regenerated 2026-09-24; the stale 6,172 is kept as
`data/prisma_counts_pre_regroup.json` and the derivation is in `docs/count_reconciliation.md`), so the two
no longer need reconciling in the methods.  **1,256 coded** on all 38 dimensions (47,728 cells) under a
stratified design — stratum H complete (984 systems in the frame, 983 of them in the release, weight 1),
P sampled 150 of 683 (weight 4.55), O sampled 100 of 4,837 (weight 48.37). Claims about *the field* use the weighted estimates; claims about
*what was coded* use the unweighted ones. The two differ enough to invert sentences, which is finding 1.

---

## 1. The coded set is not the field, and weighting changes the story

`primary_artifact` inverts: **69.2% of coded systems are repository-primary, but only 33.3% of the
field is** — paper-primary goes from 27.5% coded to **66.0%** weighted. "Most agent harnesses ship as
repositories" is true of what a survey can easily code and false of what exists.

Six other dimensions change their modal value under weighting, and three cross the "mostly reported"
line: `open_source` 38% → 70% not reported, `execution_isolation` 42% → 64%, `tracing` 39% → 59%. On `protocol_standardization`, MCP is the value for 400 of the 487 systems that report the
dimension (82.1% unweighted) against 68.4% weighted, but the weighted design SE is 12.2 points, which is too wide to support a field-level MCP claim in either direction; the dimension is 84.0% ± 2.2 silent. **The earlier figure "23.7% → 15.3%" is withdrawn: it is not derivable from `value_distributions.csv` or any analysis output and must not be used.**

*Why it matters beyond this paper:* every prior harness survey we compare against samples the
well-known systems. This is the first estimate of how far that sampling distorts the picture, and the
answer is: enough to reverse the headline claim about what a harness even is.

Source: `data/analysis/value_distributions.csv`, weighted rates with stratified design SEs.

## 2. Systems document what they do, not how they are bounded

Weighted share of cells where the sources are silent, by layer:

| layer | not reported |
|---|---|
| C control loop | **24.9% ± 1.2** |
| M meta | 34.6% ± 1.3 |
| A context assembly | 40.2% ± 2.0 |
| E verification and repair | 60.9% ± 2.3 |
| D memory and state | 63.3% ± 2.1 |
| F budget and termination | 65.1% ± 2.0 |
| B tool interface | 71.4% ± 2.0 |
| H observability and governance | 72.8% ± 2.0 |
| G sandbox and environment | **81.6% ± 1.8** |

> **Layer SEs (2026-09-25):** the layer rows use a design SE with the *system* as the sampling unit (ratio-estimator variance, stratified, with finite-population correction). An earlier version treated each cell as an independent draw and understated the layer SEs by up to 0.6 points (G 1.2 → 1.8). Per-dimension SEs are unaffected. Largest layer SE is now 2.3 (E).

Worst individually: `network_policy` **93.3%**, `replayability` 90.6%, `filesystem_access` 87.5%,
`rollback` 86.4%, `state_persistence` 86.2%.

The gradient is not random. What a harness *is* — its loop, its topology — gets described. What bounds
it — sandboxing, permissions, budgets, rollback, replay — does not. **The layers that matter for
deploying an agent safely are precisely the undocumented ones**, and that is the paper's most
consequential single result. It is also a measurement claim, not a safety claim: we observe silence,
not absence. Amendment 9 exists because those two were being confused, and the corrected rate (48.9%
of all cells) is nearly double the pre-correction figure.

Source: `data/analysis/summary_one_screen.csv` (layer rates), `data/analysis/under_reporting_by_dimension.csv` (dimension rates), `data/analysis/under_reporting_layer_year.csv`.

## 3. The field has not converged; it has diversified

Across the **34** dimensions with a usable 2023-2026 year series (`convergence_summary.csv`; 3 + 8 + 23 = 34, not 38): **10 of 34 dimensions show a change whose bootstrap interval excludes zero** (about 1.7 expected under the global null); **9 survive Benjamini-Hochberg within the family: 3 converged, 6 diversified**. `loop_primitives` (q = 0.177) excludes zero but does not survive and is reported as stable; `self_verification` (q = 0.198) no longer excludes zero on the current release. These are **unweighted coded-set** estimates
(Miller–Madow corrected entropy, bootstrap CIs, year-dimension cells with n < 20 suppressed).

Diversifying fastest: `termination_condition` (+0.76 nats), `human_in_loop` (+0.69), `edit_primitive`
(+0.60), `tool_schema_source` (+0.42). The only solid convergence is `state_persistence` (−0.27), and it is solid because reporting
*improved* while diversity fell: 42 systems of the 198-system 2024 cohort reported the dimension
against 141 of the 386-system 2026 cohort. **The pair "81% → 63% not reported" is withdrawn —
there is no per-dimension-per-year under-reporting file to source it from; `under_reporting_layer_year.csv` is layer × year only.**

*The honest caveat, which belongs in the text and not a footnote:* these are cohorts, not a panel, n
rises sharply each year, and entropy is conditioned on reporting. A falling entropy with rising n is
not evidence of convergence. `env_context_strategy` is the cautionary case — entropy fell while
reporting got worse in 2026, so its apparent convergence is the weakest of the three.

Source: `data/analysis/entropy_by_dimension_year.csv`, `convergence_summary.csv`.

## 4. There are no clean design families — and that is a result

Hierarchical clustering on Gower distance over the 583 systems reporting at least half their
dimensions: best eligible **k = 8, mean silhouette 0.120** against a pre-stated floor of 0.25, and
**bootstrap stability 0.540** over 200 resamples against a floor of 0.60. It clears the marginals-and-missingness-preserving null bar once the selection of k is corrected for (95th percentile of the null's maximum over eligible k = 0.006 over 500 draws, 495 with an eligible k, selection-adjusted
p = 0.002), but it fails the other two quality bars, across four linkages. **Verdict: negative**, and it rests on the silhouette gap, which no adjustment closes.

Three clusters are large enough and coherent enough to describe, and are labelled provisional
throughout: subagent-spawning orchestrators with explicit plan objects and full resume (n = 252);
single-agent loops with no delegation (n = 212); pipeline and
role-handoff designs (n = 90).

This matters because taxonomy papers in this area routinely assert families. On the largest coded
corpus yet assembled, with a pre-registered quality bar, the families do not separate. Harness design
is better described as a set of **weakly coupled independent choices** than as a small number of
architectures — which is also what finding 5 shows from the association side.

Not a documentation artifact: across the three clusters holding ≥5% of the set, mean coded share is
65/68/68% — a spread of 3.6 points. The Kruskal–Wallis p = 4.5e-05 is driven by 4–8 system clusters.

Source: `data/analysis/family_summary.json`, `family_cluster_summary.csv`.

## 5. Design choices are weakly coupled, and shared silence manufactures the opposite impression

On complete pairs — both dimensions carrying a value — mean corrected Cramér's V is **0.167** across
the **666** dimension pairs that survive exclusion (703 pairs in `family_associations.csv`, 37 excluded on `pinned_version`). Only one pair exceeds 0.6: `multi_agent_topology × delegation_mechanism` (V = 0.720, n =
841), which is close to definitional. The next strongest sit at 0.47–0.56 on 88–285 systems.

**The methodological result matters as much as the substantive one.** Treating `not_reported` as an
ordinary category barely moves the mean V (0.168) but takes the count of "significant" pairs from
**385 to 648 of 666**. Of those, **265 pairs are significant only when silence is a level** — the
association is documentation behaviour, not design. The worst case, `tracing × eval_hooks`, goes from
V = 0.000 on 483 complete systems to 0.241 on 1,251.

Any analysis of a half-silent matrix that treats silence as a value will find a rich correlation
structure that is an artifact of who writes documentation. We report both and make complete pairs
primary.

Source: `data/analysis/family_associations.csv`, `family_nr_flips.csv`.

## 6. Under 5% of the corpus can be compared to anything

| | systems |
|---|---|
| coded | 1,256 |
| report any benchmark score | 646 (51.4%) |
| score has a canonicalisable benchmark, split and base model | 100 |
| **share such a key with another coded system** | **53 (4.2%)** |

**593 systems report a score but never against a peer** at the same benchmark, split and base model.
36 comparable keys, 106 observations; the largest is `SWE-bench|Lite|gpt-4o` with 11 systems. Half the
corpus reports no score at all, and the coded systems name **1,138 distinct values of the `benchmark` column** between them, over the 5,863 result rows in `data/results.csv` (derived 2026-09-25; the earlier **1,104 is withdrawn** — it was not in any data file).

The registered mixed-effects regression is therefore not identifiable and **was not fitted**
(amendment 11). Thirty-eight design dimensions against 36 clusters would have produced coefficients
with no support.

What is reported instead: the comparable set published in full so any claim can be checked; scores
standardised within key; five pre-specified contrasts with bootstrap intervals over keys, within-key
permutation tests, and a computed minimum detectable effect each.

**One association survives both tests:** multi-agent topology, **+0.88 within-key sd [+0.38, +1.31]**,
18 keys / 62 observations / 38 systems, permutation p = 0.0013. It is an association, not an effect of
design: 7 of its 18 keys pit a purpose-built submission against a recurring baseline harness,
reporting is author-selected, and scaffold drift puts measurement error on the regressor that no fixed
effect absorbs and that attenuates — so **+0.88 is a lower bound on magnitude**, not an estimate of it.

Three of five contrasts are nulls or non-estimable, reported with what could have been detected:
`explicit_plan` +0.36 [−0.30, +0.97] with MDE 1.05; `executable_verification` null with MDE 1.87;
`any_retry` **not estimable** — its 2 keys admit only 4 label assignments, so no p below 0.25 is
reachable whatever the point estimate. `any_compaction` reaches p = 0.042 exactly on its design floor
with all 4 keys confounded, and is reported as confounded.

Source: `paper/tables/outcomes_comparable_set.csv`, `outcomes_summary.json`.

## 7. Authors' own ablations bound every component from above and cannot tell the components apart

Finding 6 says the *cross-paper* outcome literature cannot identify design effects. The within-study
literature fails in the opposite direction — it bounds from above — which is why both belong in the paper.

**Live source.** Every corpus-wide number in this finding and in 7b is an interim snapshot of
`paper/tables/rq3_macros.tex`, generated by `scripts/make_rq3_tables.py` from the `*_corpus` outputs (this
snapshot: generated 2026-09-25T15:39:43Z). At that snapshot the harvest has read **54.5% of the top-signal
tier and none of the second** (`\rqHarvestTierCoverage`). The macros file, not this memo, is authoritative;
the manuscript cites the macros, so a rerun of the harvest updates the paper without editing prose. The
coded-set numbers below are fixed.

### The coded-set harvest (v1, fixed)

Published ablations, harvested from the same extraction that produced finding 6's rejects: 1,008 distinct
(system, label) pairs classified, **75 usable contrasts over 42 papers, 42 systems, 14 dimensions**, 8 of
them with the 3 papers needed to pool. Each contrast is one codebase at one commit with one base model,
differing in one component.

| dimension | pooled (DL) | 95% CI | prediction interval | papers / contrasts | I² | after discount |
|---|---|---|---|---|---|---|
| self_verification | +0.139 | +0.066…+0.211 | −0.12…+0.40 | 14 / 20 | 76% | **+0.069** |
| multi_agent_topology | +0.261 | +0.023…+0.499 | −0.61…+1.13 | 6 / 11 | 95% | +0.131 |
| tool_count | +0.184 | +0.025…+0.342 | −0.52…+0.88 | 4 / 5 | 78% | +0.093 |
| short_term_state | +0.133 | +0.048…+0.219 | −0.48…+0.75 | 3 / 4 | 8% | +0.061 |
| long_term_memory | +0.117 | +0.033…+0.201 | −0.21…+0.44 | 4 / 4 | 55% | +0.068 |
| context_compaction | +0.107 | +0.009…+0.205 | −0.29…+0.50 | 4 / 5 | 63% | +0.053 |
| planning_granularity | +0.058 | +0.010…+0.106 | −0.05…+0.16 | 4 / 5 | 0% | +0.046 |
| env_context_strategy | +0.049 | −0.085…+0.183 | −0.37…+0.47 | 5 / 6 | 56% | +0.005 |

Relative change; positive means the component helped. Each dimension is discounted by *its own*
diagnostics — the larger of its trim-and-fill and one-null-per-contrast shrinkage — rather than by a
single global factor; the median discount is 50% (range 19–90%). **All eight prediction intervals include zero**, so
none of these effects supports a claim about the next system, only about this literature.

On the coded set alone the discount rule admitted `self_verification` cleanly (+0.139 → +0.069, discounted
CI lower bound +0.033, 14 papers, prediction interval crossing zero) and `short_term_state` on 3 papers,
and failed `multi_agent_topology` (I² = 95%, the widest prediction interval, the only Egger flag). **The v1
headline built on that — "only `self_verification` survives its bias diagnostics" — is overturned by the
corpus-wide harvest and must not be stated as a finding.** Its selectivity was a property of 3–14 papers
per dimension.

### The corpus-wide harvest (v2, interim)

Snapshot values, each with the macro that carries it in the paper:

- **1,472 corpus contrasts from 276 papers** (490 papers read; 8 duplicates of the coded set dropped),
  plus the 75 coded-set contrasts: **1,547 contrasts over 314 papers** (`\rqCorpusContrasts`,
  `\rqCorpusPapersWithContrast`, `\rqCorpusPapersExtracted`, `\rqTotalContrasts`, `\rqTotalPapers`).
- **19 dimensions reach the 3 papers needed to pool**, against 8 on the coded set (`\rqPoolableDims`).
- **8 of 19 pass the discount rule on the z interval, 10 on Hartung-Knapp** (`\rqDiscountSurviveZ`,
  `\rqDiscountSurviveHK`), with pooled effects of **+0.097 to +0.240** relative across the z survivors
  (`\rqEffectRangeSurviving`; interquartile +0.149 to +0.191, `\rqEffectIQRSurviving`). The median
  per-dimension discount is 48.8% (`\rqMedianDiscountPct`), so the rule reduces to asking whether an
  interval clears zero, which more contrasts make easier whatever produced the effect.
- **92.6% of contrasts favour the ablated component** (`\rqSignSharePct`), and 18 of 19 prediction
  intervals include zero; the one that does not is context compaction, lower bound +0.001
  (`\rqPIIncludesZeroCount`, `\rqPIExcludesZeroDims`, `\rqPIExcludesZeroLower`).
- `self_verification`: +0.155, z CI [+0.124, +0.186], on 134 papers and 405 contrasts, discounted to
  **+0.081**, prediction interval [−0.160, +0.471] (`\rqSVPooled`, `\rqSVCIz`, `\rqSVPapers`,
  `\rqSVContrasts`, `\rqSVDiscounted`, `\rqSVPI`).

**The honest finding is that authors' own ablations cannot tell design dimensions apart.** Components as
different as long-term memory, multi-agent topology and context compaction show gains of similar size
with the same bias signature. One reporting filter applied to every component produces that; a set of
equal real effects would be a coincidence. Self-verification's estimate is stable across the two
harvests and no longer distinguished: the claim is "at most about +0.081 relative for self-verification"
(`\rqSVDiscounted`), never "+0.081", and a sentence of the same form can be written for most of the table.

**Every one of these estimates is an upper bound, where finding 6's is a lower bound.** The within-study design absorbs
four of the five caveats in `docs/benchmark_caveats.md` — benchmark versioning, contamination,
harness–model entanglement, and the scaffold drift that most threatens the cross-paper regression —
because both arms are one codebase at one commit. What survives is §3, self-reporting, concentrated:
every one of these numbers is an author reporting on their own component. The two designs fail in
opposite directions and agree on direction for `multi_agent_topology`, on different scales (within-key sd
against relative change), so they corroborate each other's sign without bracketing a common magnitude.

### 7a. Publication bias, measured on the sign distribution (and what the baseline tables really show)

**67 of the 75 contrasts (89.3%) favour the authors' own component, and 54 of the 60 (90.0%) inside
the eight poolable dimensions** (exact binomial p = 4e-05 for `self_verification` alone; 100% for
`context_compaction`, `tool_count`, `short_term_state`). Always give the denominator. A component
that genuinely helped only sometimes, in some systems, would produce far more dissent than one contrast
in ten.

**That sign distribution is the bias evidence, and it is the only route. Do not say "measured twice by
independent routes".** The within-paper own-arm test used to be presented as a second, independent
route; a statistics review found the defect and it is fixed here. The old chance baseline of `1/n_arms`
counted the reporting paper's **own switched-off configurations** as if they were independently chosen
rival comparators — 89 of the arms in the 75 blocks are the papers' own ablations, and a full system
beating its own ablation is the *premise* of finding 7, not evidence about comparator choice. The blocks
are also pseudo-replicated: 75 blocks from **37 papers** (one paper contributes 9, one 5, three 4,
three 3, eleven 2), while the Poisson-binomial treats them as independent Bernoullis.

Corrected, with chance = 1 / (arms that are not the paper's own ablations):

| test | observed | expected | p |
|---|---|---|---|
| ~~as published (chance `1/n_arms`)~~ — superseded, kept for audit | 42/75 | 27.61 | 2.929e-04 |
| chance over non-ablation arms | 42/75 | 34.95 | **0.0609** |
| + one block per paper (largest per paper) | 17/37 | 17.03 | 0.5700 |
| + paper-clustered Monte Carlo, all blocks | 42/75 | — | **0.2056** |
| **5+ arms, chance over non-ablation arms** | **14/17** | **6.95** | **4.405e-04** |

**The overall own-arm advantage does not survive** (p = 0.061 unclustered, 0.21 paper-clustered; the
Monte-Carlo p is seeded — 10,000 draws at seed 20260924 — so it is reproducible, with a Monte-Carlo
standard error of about 0.004, i.e. quote it as 0.21 and not to four digits).
Mean own-arm advantage **+0.34 within-block sd**, mean own rank 1.55 — both descriptive, neither a test.

The shape, on the corrected baseline:

| arms in block | blocks | own first | share | chance (corrected) | chance (old, wrong) |
|---|---|---|---|---|---|
| 2 | 38 | 18 | 0.474 | 0.513 | 0.500 |
| 3 | 12 | 7 | 0.583 | 0.417 | 0.333 |
| 4 | 8 | 3 | 0.375 | 0.438 | 0.250 |
| **5+** | **17** | **14** | **0.824** | **0.409** | 0.153 |

**What survives is the 5+-arm subgroup: 14 of 17 against 6.95 expected, p = 4.4e-04.** The honest
reading is narrow and it is the one to give: **large arm tables in this literature are largely the
paper's own ablation tables** — those 17 blocks hold 70 of the 89 ablation arms, and finding 7d reaches
the same place from the other side (95.7% of comparator arms cannot be tied to any system in the
census). That is a finding about what these tables *are*. It is **not** a second independent measurement
of selective comparator choice. The empirical warrant for treating finding 6's +0.88 as a lower bound and
finding 7's +0.069 as an upper one is the sign distribution alone (67 of 75 contrasts, 19 of 20 for
`self_verification`).

Egger's test is reported but **not leaned on**, and the reason is a circularity worth stating: papers
publish no standard errors, so variance is approximated from the two arm scores, which makes a larger
effect mechanically acquire a larger SE — Egger then partly tests our own variance model. The
size-based test (effect against benchmark item count) is free of that circularity and flags nothing,
but is blind for four of eight dimensions where item counts fell back to the assumed default.

### 7b. The field seldom ablates what it does not document

**Coded-set harvest (v1, fixed).** Contrasts by layer, against the weighted silence rates of finding 2:

| layer | not reported | dimensions | contrasts | per dimension |
|---|---|---|---|---|
| C control loop | 24.9% | 5 | 26 | 5.20 |
| A context assembly | 40.2% | 4 | 13 | 3.25 |
| E verification and repair | 60.9% | 3 | 23 | 7.67 |
| D memory and state | 63.3% | 3 | 8 | 2.67 |
| **F budget and termination** | 65.1% | 3 | **0** | 0.00 |
| B tool interface | 71.4% | 5 | 5 | 1.00 |
| **H observability and governance** | 72.8% | 4 | **0** | 0.00 |
| **G sandbox and environment** | 81.6% | 4 | **0** | 0.00 |

On the coded-set harvest, **layers F, G and H — 11 dimensions covering timeouts, cost controls,
termination, execution isolation, filesystem access, network policy, permission model, tracing,
replayability, guardrails and evaluation hooks — carried zero ablations**: not one of the 42 papers
reported a number for removing them. Across the eight substantive layers (M excluded: metadata cannot be
ablated) the rank correlation between silence and ablation density was **Spearman ρ = −0.854, exact
permutation p = 0.0065** (0.006548 in `ablation_coverage_summary.json`; `\rqCodedCoverageRho`,
`\rqCodedCoverageP`). The layer silence column the coverage script reads comes from
`data/coded/not_reported_by_dimension.csv`, which was not regenerated with the release; its layer ranks
match `summary_one_screen.csv`, so ρ is unaffected, but its printed rates differ in the last digit.

**Corpus-wide harvest (v2, interim, same live source as finding 7).** The v1 statement "F, G and H carry
no published ablation" does not survive the corpus harvest. The classifier now attributes contrasts to all
three layers — termination_condition 3 papers / 5 contrasts, cost_controls 3/9, timeouts 1/1,
execution_isolation 3/7, filesystem_access 1/3, permission_model 1/4, tracing 2/2, guardrails 5/7
(`\rqFGHPaperCounts`) — so no layer is empty (`\rqZeroLayerList`), and **5 of 31 ablatable dimensions
still carry no contrast: evaluation hooks, network policy, protocol standardization, replayability and
tool schema source** (`\rqZeroDimCount`, `\rqAblatableDimCount`, `\rqZeroDimList`). The rank correlation
weakens to **Spearman ρ = −0.762, exact one-sided p = 0.018** (`\rqCoverageRho`, `\rqCoverageP`).

**Caveat on layer G.** A spot-check of the G-layer attributions finds several of them mis-mapped: the
ablated component is code-execution feedback or tool gating, read by the classifier as isolation,
filesystem scope or a permission policy. G's true count is therefore unsettled until a fixed mapping rule
is applied, and the corpus-wide G numbers above should not be quoted as sandbox ablations. (The
spot-check is not yet written to a data file; the manuscript states it qualitatively.)

So the gradient of finding 2 is not only a documentation gradient. **The layers that govern safe
deployment are the least measured**: a handful of papers each at most, and five dimensions with none.
That remains an absence of evidence about the literature, not evidence that those components do not
matter. The exception is instructive and should be stated rather than smoothed: layer E is the
most-ablated per dimension on the coded set (7.67) while still 60.9% silent — authors ablate
self-verification often and document their verification layer poorly.

Source (coded set): `data/analysis/ablation_pooled.csv`, `ablation_credible.csv`, `ablation_bias.csv`,
`ablation_contrasts.csv`, `ablation_drops.csv`, `blocks_summary.json` (`own_arm_ranks_first`). Source
(corpus-wide, interim): the `*_corpus` counterparts of the same files and
`ablation_coverage_summary_corpus.json`, all read through `paper/tables/rq3_macros.tex`. Sensitivity in
`ablation_sensitivity_n.csv` and `ablation_sensitivity_confidence.csv` (point estimates move < 0.02
across assumed benchmark sizes 50/200/800 and confidence floors 0.4/0.5/0.6).

### 7d. Papers compare their system against its own configurations, not against other harnesses

The within-paper design should have been the stronger route to RQ3: a baseline table holds team,
protocol, benchmark, split, metric and base model fixed, which is everything the cross-paper regression
could not. 332 blocks survive ablation routing and **324 are estimable**, from 131 papers (`blocks_summary.json`; there is no 333 in the file). It fails, and the reason is a finding.

Of **819 comparator arms, 784 (95.7%) cannot be tied to any system in a 6,504-system census.** Only 7
blocks carry two or more attributed comparator arms and **all 7 come from a single paper**, so no
contrast in this design is replicated across papers. The analysis script flags such a contrast
`single_paper` and refuses to call it detected whatever its p-value.

This is not a name-matching failure, and we tested that rather than assuming it. A vetted alias table
was built for the 555 genuinely proposable (label, paper) pairs, accepting a mapping **only** when the
candidate system's name is mechanically corroborated in that paper's own full text, with the matched
span and character offset stored per row. It raised attributed comparator arms from 28 to **35** and
distinct comparator systems from 7 to 9 — and moved the number that matters, blocks spanning more than
one paper, **not at all**. Of the 555 pairs, a strong model judged **383 (69%) to name no harness at
all** (`PlanAndExecute`, `OpenAIFunc`, `SMC`, `StarPO-S`, `+ SMAS`, `Structured Multimodal Feedback
Loop`), and of the 172 it did name, **149 were the reporting paper's own system under an abbreviation**
(`OH CodeActAgent v1.5` in the OpenHands paper, `M3A` in the AndroidWorld paper, `WORKFORCE` for OWL).

So a harness paper's baseline table is mostly **the paper's own configurations, prompting modes and
training variants, plus bare model names** — not rival harnesses. 13 blocks sit exactly one attribution
short of being usable, and in every one the missing arm is a paper-internal configuration that no name
table could ever resolve. The comparison the field appears to run is a comparison against itself.

Read together with finding 6: fewer than 5% of systems share a comparable key across papers, and within
papers 95.7% of comparators are unidentifiable. **Harness-to-harness comparison is not merely
under-powered in this literature; it is largely not attempted.** That is why RQ3 rests on the
within-study ablations of finding 7 and on the controlled ablation of `docs/tier3_ablation_protocol.md`.

Source: `data/analysis/blocks_summary.json`, `blocks_attribution.csv`, `data/comparator_aliases.csv`
(15 accepted, each with a re-readable corroborating offset), `data/comparator_aliases_refused.csv`
(1,684 refusals with reasons). `scripts/analyse_blocks.py --no-aliases` reproduces the pre-alias counts.

### 7c. What the ablation harvest could not reach

Of 1,008 classified labels, 545 were left `unmapped` — the model refused to name a dimension, or was
demoted below the 0.5 confidence floor. 353 were model or training variants (SFT, +RL, a different base
model), not harness ablations; 178 were another name for the paper's own full system. Of the 284 rows
that *were* a mapped ablation, 26% paired exactly against a full-system row; the largest single loss is
papers ablating on a benchmark or metric for which the extractor never accepted a full-system score.
Every drop is published with its reason in `ablation_drops.csv` so the recall can be audited rather
than trusted. Ambiguous own-system cells are **dropped, not resolved to the best own score**, which
would have inflated in the same direction as the bias being measured.

### 7e. Our own controlled ablation is a failed experiment, and its pilot is the finding

Tier 3 (`docs/tier3_ablation_protocol.md`, frozen 2026-09-24) was registered to separate two hypotheses the
published contrasts fuse: whether a harness that verifies beats one that does not (H1, confounded with
compute), and whether **at equal compute** verifying beats unguided retrying (H2). Arm C is compute-matched
**per instance**. No paper among the 42 that publish a component ablation runs such a control.

**It cannot be run as registered.** Nine suite-and-tier cells were piloted; eight sit above the 25-70%
band ceiling on the pre-specified continuous measure. The one that selects,
`bigcodebench_hard_instruct` @ haiku at 0.648, fails for two independent reasons: resolving its band
membership needs 121 pilot instances against a pool of 23, and its confirmatory pool holds 34 against the
93 the analysis plan requires. The remaining candidate that could have supplied the instances was
**measured, not assumed** - the full `bigcodebench_instruct` split has 556 usable instances but arm-A
accuracy 0.852, 95% interval 0.757-0.948, entirely above the ceiling. Two cells sit in band on the
*binary* secondary measure (0.375 and 0.560); criterion 3 fixed the continuous measure as primary and we
did not substitute the one that passes. **Verdict: a failed experiment, not a re-tuned band.**

**What the pilot did establish, needing no amendment because it is descriptive and single-arm:** across 56
arm-B diagnostic runs a harness that writes its own checks, runs them and repairs on failure **accepted its
first attempt 50 times** (mean 1.16 calls), and **three of those 50 scored 0.00** against the hidden tests.
Model-written verification mostly does not fire, and when it passes it is sometimes blind to total failure
of the code it just approved. That speaks directly to the mechanism the 20 published `self_verification`
contrasts credit, without contradicting the pooled +0.069: it says the named mechanism is not obviously the
one operating where the checks are written by the model under test.

**Amendment 12a (2026-09-25): the v2 design fixes the treatment, not the supply.** Arm B was redefined so
that it must spend its budget: *B-fixed* runs *k* = 4 verify-and-repair rounds regardless of its own checks'
verdict, and *B-ext* verifies against the benchmark's public examples. Piloted at the haiku tier, arms A
and B only (144 rows, 322 calls, no arm C, no contrast): B-fixed fires on every instance by construction
and the forced rounds changed the submitted code in 17 of 48 runs; B-ext fires only where public checks
exist (10 of 27 such runs, none of the 21 without). The v1 arm replicated: first attempt accepted 41 of
48 times, three of them scoring 0.00 on the hidden tests. **B-fixed is the recommended arm** on criteria
written before the table was read (it fires; its population is the whole suite, which contains the one
in-band cell; it is still self-verification). **But the supply problem is worse, not better:** the
amendment found and fixed a pool-overlap defect that also affected v1 (pilot and confirmatory pools were
hashed by suite name, so 11 of the in-band cell's 34 confirmatory tasks had already been piloted under
another presentation), leaving **22 clean confirmatory instances against 93 required at ρ = 0.7**; the
detectable effect at 22 is about 15 points. The band is read on the continuous primary and is not moved.
A confirmatory v2 run would cost ~10,044 calls at N = 93 (~43 h at 8-way concurrency). **Tier 3 remains
a failed experiment** unless a new source supplies roughly four times as many clean in-band instances.
The estimand is conditioned on the stratum where the treatment fires as defined by arm A, not by B's own
outcome, because conditioning on a contrasted arm's outcome biases B − C against B.

Source: `data/tier3/pilot/pilot_summary.json` (9 cells), `data/tier3/diagnostic/**/runs.jsonl` (56 rows),
and the dated protocol notes appended to `docs/tier3_ablation_protocol.md` (frozen text byte-identical).

---

## The argument the paper should make, in this order

1. **A census, not a sample** — 6,504 systems identified, 1,256 coded with evidence per cell, and
   weighting shows the convenient sample inverts the basic facts (finding 1).
2. **An under-reporting audit with a gradient** — 48.9% of cells silent, and the silence concentrates
   in exactly the layers that govern safe deployment (finding 2).
3. **No convergence and no families** — the field is diversifying on more dimensions than it is
   converging on, and design choices do not cluster into architectures (findings 3, 4, 5).
4. **The outcome literature cannot answer the design question yet** — fewer than 5% of systems are
   comparable to any peer; one association survives, as a lower bound (finding 6).
5. **What the published ablations support, bounded from above, and what they cannot** — on an interim
   corpus-wide harvest (54.5% of the top-signal tier read; live values in `paper/tables/rq3_macros.tex`),
   8 of 19 poolable dimensions pass the discount rule with a similar +0.097 to +0.240 relative gain and
   the same bias signature (92.6% of contrasts favour the component), so authors' own ablations cannot
   tell design dimensions apart; self-verification is worth at most about +0.081 relative, like most of
   the table. The layers that govern safe deployment are the least ablated: the coded set had none for
   F, G and H (ρ = −0.854), the corpus harvest reaches them through a handful of papers, several G-layer
   attributions mis-mapped, with 5 dimensions still at zero (ρ = −0.762, p = 0.018) (finding 7, 7b). The
   cross-paper estimate is a lower bound and these are upper bounds, and publication bias is measured on
   the contrast sign distribution rather than invoked (finding 7a).
6. **A method contribution** — evidence-per-cell coding at this scale, with the two traps measured
   rather than assumed: silence treated as a value manufactures correlations (265 pairs), and a
   self-contradictory absence rule halved the under-reporting rate before it was fixed (amendment 9).

## What to be careful about in review

- **Ten of eleven amendments are pre-stage and evidence-backed; say so explicitly.** The two that will
  draw fire are 4 (no human screener) and 9 (a coding rule rewritten mid-project). For 9 the defence
  is the strongest available: the rule was rewritten, validated on 217 systems, and only then applied.
- **Reliability is reproducibility, not correctness.** Mean per-dimension kappa 0.784 [0.765, 0.800] (observed
  agreement 0.870, Gwet's AC1 0.855) on 247 double-coded systems, with 37 of 38 dimensions at or
  above 0.6, but both readings are model readings. Report the mean of the per-dimension kappas and
  say so; a kappa from stacking all cells into one table reads higher (0.830-0.869) only because its
  chance baseline spans all 38 value spaces at once. Correctness rests on reference-set recall (27/27)
  and the independent-pipeline cross-check (agreement 0.84, kappa 0.66), and those belong beside the
  kappa table, not after it.
- **`loop_primitives` is below the freeze threshold** (0.586 exact-set) and is kept because it is
  multi-valued, with per-value agreement 93%. Disclose it rather than let a reviewer find it.
- **The ablation pooled effects will be attacked as author-reported, and they are.** Do not defend
  them as unbiased; defend the bound. The within-study design absorbs four of the five benchmark
  caveats and leaves self-reporting; self-reporting is then measured on the contrast sign distribution
  (89.3%, and 19 of 20 for `self_verification`); and every effect is
  discounted by its own diagnostics. **Do not add the own-arm test as a second independent route** — on
  the corrected chance baseline the overall own-arm share is p = 0.061 (0.21 paper-clustered) and only
  the 5+-arm subgroup survives (14 of 17 against **6.95** expected, p = 4.4e-04), which says those
  tables are mostly own-ablation tables (finding 7a). The claim is "at most about +7% relative for self-verification",
  never "+7%".
- **All eight prediction intervals include zero**, `planning_granularity`'s ([-0.048, +0.163])
  included. Say it in the text. Eight pooled dimensions on 3-14 papers each can support a claim
  about this literature, not about the next system, and a reviewer who reads the PI column before
  the CI column will notice first.
- **Egger is reported and deliberately not leaned on.** Papers publish no standard errors, so variance
  is reconstructed from the two arm scores, which makes a larger effect mechanically acquire a larger
  SE - Egger then partly tests our own variance model. That circularity belongs in the text, not in a
  response to reviewers. The size-based test that avoids it flags nothing but is blind for four of the
  eight dimensions.
- **The zero-ablation result for layers F, G and H is an absence of evidence and must be worded as
  one.** It says no paper in this corpus published a number, which is a fact about the literature. It
  does not say those components do not matter - that is the point of raising it.
- **Do not let finding 6 be read as a failed analysis.** It is a measured statement about the field's
  reporting practice, and it is the reason the design-versus-outcome question stays open.
