# Count reconciliation (2026-09-24, release rebuilt 2026-09-25)

> **Superseding note, 2026-09-25.** The release (`data/systems.json`) was rebuilt on 2026-09-25 at
> 06:17 against the repaired grouping, exactly as the 2026-09-24 section below predicted a rebuild
> would do. **The released coded set is now 1,256 systems and 47,728 cells**, not 1,253 / 47,614. Every
> count in this note that mentions 1,253 or 47,614 describes the *previous* release; the numbers below
> are the ones the manuscript must use, and every analysis output was regenerated from this release
> after the rebuild.
>
> | quantity | previous release | **current release** | derivation |
> |---|---|---|---|
> | released systems | 1,253 | **1,256** | 1,234 frame-coded − 1 (`con`) + 23 out-of-frame |
> | released cells | 47,614 | **47,728** | 1,256 × 38 |
> | coded with a value and evidence | 24,160 (50.7%) | **24,228 (50.8%)** | `data/systems.json` |
> | `not_reported` | 23,290 (48.9%) | **23,337 (48.9%)** | `data/systems.json` |
> | `unresolved` | 164 (0.3%) | **163 (0.3%)** | `data/systems.json` |
> | strata in the release | H 980 / P 157 / O 116 | **H 983 / P 157 / O 116** | join to `data/coding_frame.csv` |
> | weighted base | 1,230 systems, weights sum 6,500 | **1,233 systems, weights sum 6,503** | drawn-sample systems only; 23 out-of-frame at weight 0 |
> | frame-coded ids absent from the release | `agent-s`, `agent-s-v2`, `agentk`, `con` | **`con` only** | the three were restored by the rebuild |
>
> The bridge is therefore **1,234 − 1 + 23 = 1,256**. `con` remains the single coded-but-unreleased
> system: its coding is on disk as `con-sys.json` (renamed around the Windows reserved device name) but
> its `system_id` field is still `con`, and the release build cannot write a file of that name on
> Windows. It is a release defect of one system, disclosed rather than repaired at this stage. The
> weighted sum is 6,503 rather than 6,504 for the same reason (`con` is stratum H at weight 1).
>
> Nothing in the reliability figures changes (they rest on the 247-system double-coded sample), and
> the drawn weights (H 1, P 4.5533, O 48.37) are unchanged.

Five counts in this repository disagreed, and section authors were told to report the conflict rather
than pick one. This file resolves them from the data. **It is the authority for every count in the
manuscript.** Derived by comparing `data/coding_frame.csv`, `data/systems.json` and the files in
`data/coded/json/`.

## The corpus

| count | value | source | what it is |
|---|---|---|---|
| sampling frame | **6,504** | `data/coding_frame.csv` (row count), `data/coding_frame.json` `systems_total` | the frame the stratified sample was drawn from |
| census after grouping, as registered in amendment 10 | 6,501 | `docs/protocol_prisma_p.md` | superseded by the regrouping repair; differs by 3 |
| PRISMA `included_systems` | 6,172 | `data/prisma_counts.json` | **STALE.** Predates the grouping repair. Must be regenerated before submission, or the PRISMA flow will contradict the frame |

**Use 6,504, and call it the sampling frame.** Do not write "6,504 systems identified" beside a PRISMA
diagram that says 6,172. Regenerating `data/prisma_counts.json` is an open task.

## The coded set

The frame's `coded` flag and the coded files on disk disagree, because the grouping repair ran after the
sample was drawn. Exactly:

| count | value | derivation |
|---|---|---|
| flagged coded in the frame | **1,234** | H 984 (weight 1) + P 150 (weight 4.5533) + O 100 (weight 48.37) |
| coded files on disk | **1,257** | `data/coded/json/*.json` |
| released | **1,253** | `data/systems.json`; 1,253 × 38 = 47,614 cells |

The three sets reconcile as:

```
1,234  flagged coded in the frame
  - 4  frame-coded ids absent from the release
 + 23  coded systems that are not in the frame's coded set
------
1,253  released
```

**The 4 frame-coded ids absent from the release** are `agent-s`, `agent-s-v2`, `agentk` and `con`. The
first three are the single-letter-tail grouping collision the census repair fixed (`Agent S` against
`Agents`); they were dissolved or merged when grouping was corrected. `con` was renamed `con-sys`
because `con` is a reserved device name on Windows and could not be committed as `con.json`; it is
present in the release under the new id, so it is a renaming, not a loss.

**The 23 out-of-frame coded systems** are: `airtbench-reference-agent`, `car`, `cfgm`, `compagent`,
`d-artemis`, `dive`, `docagent`, `ehragent`, `evaluation-agent`, `forge`, `graphimind`, `idea-agent`,
`incalmo`, `lightmanus-jarvis`, `madevolve`, `orchestral`, `rci-agent`, `seer`, `simagent`,
`spider2-v-reference-agent`, `storm`, `tartanmaroon`, `waragent` (plus `con-sys`, which is `con`
renamed and is therefore in-frame). Several are benchmark reference agents, coded because the
reference-set recall check required them.

### The consequence that must be stated in the methods

**These 23 systems carry weight 0, and that is correct rather than an open item.** They are in the frame
and have strata (16 in O, 7 in P; none in H, by construction), so the released set composes as H 980 /
P 157 / O 116 = 1,253. But they were coded for reasons other than the draw - several are benchmark
reference agents needed for the recall check - so their inclusion probability is not the design one.
Weighting them would bias the field estimate; `scripts/analyse_descriptives.py` therefore gives them
weight 0 and documents it.

The consequence to state in the methods: **every weighted, field-level estimate rests on the 1,230 drawn
systems, whose weights sum to 6,500, while every unweighted statement about the coded set rests on
1,253.** The two denominators differ by 23 systems and the manuscript must not imply that 1,253 systems
were weighted to the frame. The drawn weights (H 1, P 683/150 = 4.5533, O 4,837/100 = 48.37) are the
correct ones: they are the draw's inverse inclusion probabilities, not ratios of the realized counts.
Re-weighting to the realized 157 and 116 would be wrong, because the extra systems were not sampled.

## Cell states in the release

Verified by aggregating `data/systems.json` over all 47,614 released cells:

| state | cells | share |
|---|---|---|
| coded with a value and evidence | 24,160 | **50.7%** |
| `not_reported` | 23,290 | **48.9%** |
| `unresolved` | 164 | **0.3%** |

`docs/schema_changelog.md` and `docs/coding_reliability.md` previously recorded the `unresolved` share as
1.0%; that is stale and is corrected. The raw codings on disk contain **no** `unresolved` cells — the
state is assigned by the release build when a cell fails validation, which is why the raw and released
figures differ.

## Reliability

Recomputed 2026-09-24 from `data/coded/json` against `data/coded/json_pass2` with `scripts/kappa.py`:
**247** double-coded systems (not 217), 9,386 cells compared, observed agreement **0.870**, mean
per-dimension Cohen's kappa **0.784**, mean Gwet's AC1 **0.855**, **37 of 38** dimensions at or above 0.6 on the point estimate, with four dimensions' 95%
cluster-bootstrap intervals including the floor. See `docs/coding_reliability.md` for why no stacked all-cells kappa is quoted. The **217** figure
remains correct for two other things: the pilot, and the amendment-9 validation set (agreement
0.597 → 0.872, kappa 0.564 → 0.832, pass A only on both sides).

### The double-coded sample: 245 drawn, 247 coded, 217 historical

Three numbers, all defensible, and the methods section must say which is which.

| count | value | source |
|---|---|---|
| deterministic sample drawn | **245** | `data/coded/double_sample.json` (seed `code-2026-09-20`) |
| systems actually double-coded | **247** | `data/coded/json_pass2/*.json`; the 245 drawn ids are all present, plus 2 coded beyond the sample |
| reliability computed on | **247** | the overlap between `data/coded/json` and `data/coded/json_pass2` |
| earlier sample, used for the amendment-9 validation | **217** | `docs/coding_manual.md`, `docs/protocol_prisma_p.md` |

So 217 and 247 are **different samples, not a corrected figure**: the amendment-9 rule change was validated
on the sample as it stood then (217 systems, agreement 0.597 to 0.872, kappa 0.564 to 0.832, pass A only
on both sides), and the released reliability is computed on the sample as it stands now (247). Report both
with their purposes named. The 2-system excess over the drawn 245 is disclosed rather than trimmed,
because silently dropping two systems to make a round number is the kind of thing this paper objects to.

## Convergence denominator

The convergence verdicts (3 converged, 6 diversified, 25 stable; corrected 2026-09-25 from a stale 8 and 23) sum to **34**, which is the row count of
`data/analysis/convergence_summary.csv` — the dimensions with a usable 2023-2026 year series. Not 38.

## Layer standard errors corrected (2026-09-25)

The layer rows of `data/analysis/summary_one_screen.csv` (and `data/analysis/under_reporting_layer_year.csv`) are
weighted `not_reported` rates over a layer's 3-7 cells per system. Until 2026-09-25 their design SE
was computed by the stratified-proportion formula with each **cell** as a draw, which (a) ignores that
a system's cells are correlated and (b) compares cell counts with frame sizes counted in systems, so
the finite-population term collapsed to zero for stratum H in every layer and for P in the 5- and
7-dimension layers. `weighted_share` now uses the system as the sampling unit (stratified
ratio-estimator variance of the residual total, with finite-population correction); with one row per
system it is identical to the old formula, so **no per-dimension SE changed**. Layer SEs, rates
unchanged: A 2.0 (was 1.8), B 2.0 (1.4), C 1.2 (1.4), D 2.1 (2.0), E 2.3 (2.0), F 2.0 (2.0),
G 1.8 (1.2), H 2.0 (1.5), M 1.3 (1.3). The paper's "24.9 ± 1.4 to 81.6 ± 1.2" is therefore
"24.9 ± 1.2 to 81.6 ± 1.8", and "standard errors of at most 2.0 points" becomes "at most 2.3".
Found by the `harnessdb` loader's independent implementation; test
`test_layer_se_clusters_by_system_and_reduces_to_proportion_se` pins the behaviour.

## Null-fill discount cap lifted (2026-09-28)

`null_fill_sensitivity` in `scripts/analyse_ablations.py` added at most 500 null contrasts. On the
completed harvest self_verification has 1,687 contrasts from 525 papers, so the one-null-per-contrast
world was never reached and the dimension was silently left undiscounted (`discount` 0). The cap is now
`max(500, 2k)`. Self-verification: pooled +0.152, one-null-each +0.076, nulls-to-halve 528, discount
50%. No other dimension changed. The paper's "at most about +0.076 relative" (§1, §7, §8, §9) is the
discounted value.

## Withdrawn figures

Not derivable from any data file, and not to be used:

- **MCP adoption "23.7% → 15.3%"**. Use `protocol_standardization` instead: MCP for 400 of the 487
  systems reporting the dimension (82.1% unweighted) against 68.4% weighted with a design SE of 12.2
  points, on a dimension that is 84.0% ± 2.2 silent.
- **`state_persistence` "81% → 63% not reported"**. There is no per-dimension-per-year under-reporting
  file; `under_reporting_layer_year.csv` is layer × year only.
- **"1,104 distinct benchmarks"**. Present only in `docs/headline_findings.md`; needs a source file or
  removal.

## The PRISMA flow regenerated (appended 2026-09-24)

`data/prisma_counts.json` has been regenerated so that every stage is re-derived from the data. The
superseded file is kept as `data/prisma_counts_pre_regroup.json` (it is the evidence for this entry and
for amendment 10, and is not deleted). `paper/figures/prisma_flow.{svg,pdf}` were re-rendered and
`python scripts/prisma_diagram.py --check` now exits 0 with no reported problem.

**Only one stage count was wrong**: `included_systems`. Every other stage already reconciled.

| stage | stored before | now | derivation |
|---|---:|---:|---|
| identified, databases and registers | 37,899 | 37,899 | line counts of `data/raw/{arxiv,s2,openalex,acl,openreview,github}.jsonl` |
| identified, other methods | 12,825 | 12,825 | grey 299 = `grey.jsonl` 48 + 251 non-GAIA leaderboard systems; snowball 12,526 = `snowball.jsonl` 11,289 + `snowball_surveys.jsonl` 415 + `awesome.jsonl` 822 |
| duplicates removed | 22,977 | 22,977 | 50,724 raw − 27,747 unique ids in `data/raw/candidates.csv` |
| records screened | 27,747 | 27,747 | `data/screening/triage.csv` rows (= candidates.csv ids) |
| excluded at title/abstract | 17,780 | 17,780 | 27,747 − 9,967 forwarded; equivalently 17,876 `auto_decision = exclude` − 35 − 61 forwarded anyway |
| reports sought for retrieval | 9,967 | 9,967 | the distinct ids of `fulltext_queue.csv` = 9,871 forwarded by the title rule (9,114 auto-include + 757 with no two-of-three decision, amendment 4) + 35 canonical-metadata-mismatch records not already forwarded + 61 amendment-7 re-reads. Exact set identity, asserted |
| reports not retrieved | 1,532 | 1,532 | queued records that never reached a full-text vote |
| reports assessed at full text | 8,435 | 8,435 | `fulltext_final_pass1.csv` rows (all inside the queue) |
| excluded at full text, with reasons | 1,350 | 1,350 | `exclusion_code` tally over `fulltext_final_pass1.csv`: out_of_scope 1,028; duplicate_system 82; no_harness_description 156; not_retrievable 76; other 8 |
| included papers (reports) | 7,085 | 7,085 | `decision = include` in `fulltext_final_pass1.csv` |
| **included systems after grouping** | **6,172** | **6,504** | `scripts/system_registry.py` re-run on `fulltext_final_pass1.csv`; 7,085 includes group into 6,504 systems (407 multi-member). The id set is **identical** to `data/systems_candidates.csv` and to `data/coding_frame.csv` |

So the PRISMA flow now reads 6,504 systems and the sampling frame is 6,504 systems, and they are the
same 6,504 ids. **The frame was right; the flow diagram was stale.** The methods no longer have a
conflict to declare on this point.

Two notes on stage definitions that look like errors and are not:

* `not_retrieved` is the 1,532 queued records that never reached a full-text vote, **not** the 1,605
  records whose document fetch failed. 73 records whose paper was unretrievable were assessed from
  their repository instead (amendment 5's evidence bundle), so the fetch-status count overstates
  non-retrieval by 73 and breaks the flow arithmetic. `scripts/phase3_autopilot.py` computed it the
  wrong way and has been corrected, so a re-run reproduces this file.
* `fulltext_queue.csv` holds 9,968 rows but 9,967 distinct records: `arxiv:2409.11393` is listed twice.
  Reports sought is a count of records, so it is 9,967. `phase3_autopilot.py` used the row count and has
  been corrected.

### 6,501 against 6,504: resolved, and 6,504 is right

Both are outputs of the same grouping repair, one pass apart. The repair was run twice on 2026-09-24:

| census | artefact | time | what it is |
|---:|---|---|---|
| 6,172 | `data/coded/_pre_regroup_systems_candidates.csv` | 10:19 | before the repair; the figure the stale PRISMA file carried |
| 6,501 | `data/coded/_pre_regroup2_systems.csv` | 11:19 | first repair pass — **the figure amendment 10 registered** |
| 6,504 | `data/systems_candidates.csv`, `data/coding_frame.csv` | 11:21 | second pass, after a further fix to `scripts/system_registry.py` (11:19); the current census |

The difference is exactly three system rows, and they are named: **`agent-s` (Agent S3, 7 member
records), `agent-s-v2` (Agent S2) and `agentk` (AgentK)**. Nothing was removed between the two passes
(`set(6,504) ⊃ set(6,501)`, with no id lost). Re-running `scripts/system_registry.py` today on
`data/screening/fulltext_final_pass1.csv` reproduces 6,504 and the identical id set, so 6,504 is the
count the current grouping logic yields from the current votes. **6,501 was correct when amendment 10
was filed and is now superseded by 3; amendment 10 should be updated to 6,504 with these three ids
named, or a short amendment 11 filed recording the second pass.** H rises 981 → 984 and the drawn coded
set 1,231 → 1,234 by the same three rows; P (683) and O (4,837) are unchanged, and 984 + 683 + 4,837 =
6,504.

### Correction to "the 4 frame-coded ids absent from the release", above

The mechanism is the reverse of what this file said earlier. `data/systems.json` was built at 11:12,
i.e. from the 6,501 census, **before** the 11:21 pass created `agent-s`, `agent-s-v2` and `agentk` as
their own rows. They were therefore not dissolved or merged by the repair: they were restored by it,
after the release had been built, which is why `data/coding_frame.csv` flags them `coded = 1` (all three
in H) while `data/systems.json` does not contain them. Their codings do exist on disk
(`data/coded/json/agent-s.json`, `agent-s-v2.json`, `agentk.json`), so the release build dropped them
for not being in the census it was given, not for want of coding. Re-running the release build would
carry them in and take the released set from 1,253 to 1,257.

`con` is a separate case and the renaming account stands, with one correction: `data/coded/json/con-sys.json`
exists, but `con-sys` is **not** in `data/systems.json` and not in the frame (which carries the id `con`),
so it is coded-but-unreleased as well rather than "present in the release under the new id". The set
arithmetic in this file is unaffected and still checks exactly: 1,257 coded on disk = 1,253 released +
`agent-s` + `agent-s-v2` + `agentk` + `con-sys`, and 1,234 frame-coded − 4 absent (`agent-s`,
`agent-s-v2`, `agentk`, `con`) + 23 out-of-frame-coded = 1,253. The 23 names listed above are exact.

### One further correction inside `prisma_counts.json`

`title_stage_recovery` recorded `re_read = 62` and `confirmed_excluded = 52`; the data gives **61** and
**51**. `data/screening/elicit_crosscheck.json` counts 62 elicit-include / our-exclude **pairs**, but
they cover 61 distinct records of ours: `arxiv:2409.11393` matched two Elicit rows (434 matched pairs
cover 428 distinct records) and is listed twice in `elicit_disagreement_queue.csv`. Of those 61 records,
10 were recovered as includes and 51 confirmed excluded. Report "62 title-stage disagreements, covering
61 records" if both figures are wanted. The supplementary arm re-derives exactly as stored: 987 records
screened by the independent pipeline, 411 included, 103 not in the frozen search, 103 sought, 40 not
retrieved, 63 assessed, 26 excluded (out_of_scope 22, duplicate_system 3, no_harness_description 1),
37 included.

## Codability gate as implemented, and the 2,073 label (2026-09-28)

**The release gate is not the registered criterion (b).** Protocol §4.7 counts a dimension towards
the 19 only when it is *assigned a value with evidence* ("`not_reported` does not count") and requires
at least one such dimension in each of layers A, B and C. `scripts/build_tables.py` (the
`CODABILITY_MIN` check) counts every *settled* cell, valued or `not_reported`, and has no layer
condition. Amendment 5 moved enforcement from screening to coding but did not change the definition,
so this is a deviation, reported in §4.1, in Table 1 row (b), and in S2 (text and amendment-5 row).
Counted from `data/systems.json` (1,256 released systems, 38 cells each):

| quantity | systems |
|---|---|
| fewer than 19 **valued** cells (value with evidence; not `not_reported`, not `unresolved`) | **613** |
| at least 19 valued cells | 643 |
| fewer than 19 **settled** cells (valued or `not_reported`) — the gate as implemented | **0** (minimum settled: 29) |
| no valued cell in at least one of layers A, B, C | 396 |
| fail registered §4.7 on either clause (count or layer) | **664** (592 pass) |

Reconciliation with §6.4 (583 clustered, 673 below): the clustering keeps systems valued on at least
half of the **37** dimensions it uses (all but the free-text `pinned_version`), i.e. at least 19 of 37
(`analyse_families.build_distance`, `min_coded_share=0.5`). All 583 are among the 643 with at least 19
of 38 valued; the other 60 reach 19 of 38 only through a valued `pinned_version`. 583 + 673 = 1,256.

Recount:

    python -c "import json;d=json.load(open('data/systems.json',encoding='utf-8'));v=lambda c:not c.get('unresolved') and not c.get('not_reported');print(sum(sum(map(v,s['coding'].values()))<19 for s in d), sum(sum(not c.get('unresolved') for c in s['coding'].values())<19 for s in d))"

prints `613 0`.

**What 1,403 / 2,073 counts (settled 2026-09-28 from the raw files).** For the 3,075 twice-read
records the `fulltext_final_pass1.csv` row is the **decision of record**, produced by the tier-2 model
(Claude Opus 5 for 3,031, Opus 4.8 for 30, no call 12, Sonnet 5 for 2); `fulltext_final_pass2.csv`
holds the tier-1 reading (Claude Sonnet 5, 3,063), and `fulltext_votes_tier1.csv` reproduces it row
for row. Cross-tab (record × tier 1): tier-1 exclude 1,532 = 862 confirmed + 670 overturned to include
(43.7%, Wilson [0.413, 0.462]); tier-1 include 1,543 = 1,403 confirmed + 140 overturned to exclude
(9.1%, [0.077, 0.106]). So 2,073 is the number of includes OF RECORD among the escalated set
(1,403 + 670), not a count of first-reading includes: "2,073 of 7,085 includes read twice" was true
but uninformative, and "first-reading includes confirmed 67.7%" (the old caption of
`fulltext_report.md` §5, and one review's reading of it) is wrong. The paper now reports the two
overturn rates (methods §4.3, `tab:screening-checks`, threats table). The 9.1% is an upper bound on
the false-include rate of the unescalated includes, because the sampled includes contain every
low-confidence one.
