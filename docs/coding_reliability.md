# Coding reliability (Phase 4 result)

Two independent codings of the same 217 systems — the deterministic 20% sample of the 1,116-system
coded set (`data/coded/double_sample.json`, seed `code-2026-09-20`) — each put through pass A and the
pass-B repair, so the two sides are procedurally identical. Both are model readings under prompt
`code-v2-2026-09-23`; what they measure is the reproducibility of the coding procedure, not its
correctness. Correctness is addressed separately, by reference-set recall (27/27) and the independent
pipeline cross-check (amendment 7).

Per-dimension figures: `data/coded/reliability_final.json`. Regenerate with

    python scripts/kappa.py coding data/coded/json data/coded/json_pass2 --json data/coded/reliability_final.json

## Headline

| | value |
|---|---|
| cells compared | 8,246 |
| observed agreement | 0.879 |
| Cohen's kappa (registered primary measure) | **0.842** |
| Gwet's AC1 | 0.879 |
| dimensions at or above the 0.6 freeze threshold | **37 of 38** |
| `not_reported` share of cells | 48.2% |

## Why the first table said the opposite

The first reliability run put **30 of 38 dimensions below 0.6** (pooled kappa 0.564). Two things were
wrong with that reading, and neither was the schema:

1. **The two codings were not comparable.** The primary carried 11,136 pass-B repair rows and the
   second carried none, so the comparison measured a missing repair pass. Both sides are now repaired.
2. **The coding manual contradicted itself.** Rule 2 sent a coder who cannot point at evidence to
   `not_reported`; rule 5 sent them to an absence value citing where the feature would be declared.
   "I searched for rollback and found nothing" satisfied both, so the two readings filed identical
   evidence differently — their notes agreed ("no replay facility found") while the codings did not.
   That single ambiguity accounted for 19 of the failures: `rollback` on 0.97 of its disagreements,
   `replayability` 0.96, `network_policy` 0.94. Amendment 9 rewrote rule 5 as an ordered test.

Measured on the same systems, before and after the rewrite, pass A only on both sides:

| | agreement | kappa | AC1 | `not_reported` |
|---|---|---|---|---|
| rule 5 ambiguous | 0.597 | 0.564 | 0.596 | 26.9% |
| rule 5 rewritten | 0.872 | 0.832 | 0.872 | 48.3% |

The gains concentrate exactly where the diagnosis pointed — `replayability` 0.225 → 0.825, `rollback`
0.263 → 0.845, `guardrails` 0.291 → 0.805, `self_verification` 0.276 → 0.775, `permission_model`
0.393 → 0.881 — which is the reason to believe the mechanism rather than the number. The superseded
coding is kept at `data/coded/v1_rule5_ambiguous/` as the evidence for the change.

**The correction costs a flattering number.** The `not_reported` share nearly doubles, because prose
that never mentions rollback was being read as evidence that rollback is absent. The under-reporting
result (RQ4) gets larger and better founded.

## The one dimension below threshold

`loop_primitives` is the single dimension under 0.6 on the registered measure. It is kept, and the
figures are reported rather than smoothed:

| measure | value |
|---|---|
| observed agreement | 0.631 |
| Cohen's kappa (exact set match) | **0.586** |
| Gwet's AC1 | 0.624 |
| per-value kappa (7 values, present/absent each) | 0.738 |
| per-value agreement | 0.930 |

It is multi-valued, and exact-set matching scores two readings as a total mismatch whenever one lists
an extra primitive: `react` against `fixed_pipeline|react`, `generate_test_repair` against
`generate_test_repair|multi_attempt`. Per value the two readings agree on 93% of present/absent
decisions. Three of the four measures clear the threshold and only the harshest does not, so the
value set is not the problem and there is nothing to redefine; the dimension is flagged as the
weakest in the set and any claim resting on it should say so.

**Per-value kappa is a diagnostic, not a replacement.** It does not uniformly flatter: `retry_policy`
scores 0.671 on exact sets and 0.491 per value, and `edit_primitive` 0.648 against 0.589, because
averaging over values reintroduces the prevalence problem for values that are rarely used. The
registered exact-set kappa stays the primary measure and every figure is published beside it.

## Documented exceptions

1. **Two systems coded by a different model.** `cai` (Cybersecurity AI) and `pentagi` (autonomous
   penetration testing) are offensive-security agents, and Opus's safety classifier stops the coding
   mid-response on both — no parseable answer, across repeated attempts, with one system per call and
   so no batch to split. Both were coded with Sonnet instead, which the `model` column records on
   every row. Sonnet leaves more cells unresolved than Opus on identical bundles, so these two
   systems carry slightly thinner coding than the other 1,114 (0.2% of the coded set).
2. **Cells nobody could settle are marked, not guessed.** 1.0% of released cells are `unresolved`:
   the coder claims no value and no evidence. They are deliberately distinct from the 24% that are
   `not_reported`, which assert that the sources were read and are silent — merging the two would
   inflate the headline result.
