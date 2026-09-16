# Review protocol (PRISMA-P)

Status: draft. This file mirrors the OSF pre-registration. Once registered, add the OSF
DOI and timestamp here and do not edit the registered sections; log amendments below.

OSF project: https://osf.io/vkjer/ (private, created 2026-09-16)
OSF registration: https://osf.io/ab2wn/ (Generalized Systematic Review Registration v6, embargoed)
Registered on: 2026-09-16 18:12 UTC, before any searching or screening
Registration DOI: _minted by OSF when the registration is approved; add here_

The registered protocol is the text of the 61 registration responses at that timestamp. Sections below
are the working copy; any change after 2026-09-16 that affects the registered content is logged under
Amendments and, if material, filed as a registration update on OSF.

## 1. Title
The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset
(HARNESS-DB) of LLM Agent Scaffolding, 2022–2026

## 2. Objectives and research questions
- RQ1 Structural components and a reliably codable unified taxonomy (kappa >= 0.6 per dimension)
- RQ2 Variation and convergence across systems and over time
- RQ3 Design choices associated with reported success, cost, robustness (benchmark and model held constant)
- RQ4 Systematically under-reported dimensions

## 3. Definition of a harness
_To write. Distinguish from model, prompt, agent, framework, runtime._

## 4. Eligibility criteria
Include if all of: (a) wraps an LLM in a loop with tools or an environment; (b) enough
detail to code at least 50% of dimensions from paper, repo or docs; (c) released Oct 2022
to Aug 2026; (d) English.
Exclude: training/RL-only work with no harness description; embodied robotics; benchmarks
with no reference harness (recorded for the outcomes table only); single-prompt agents
without a loop; duplicate descriptions of one system (keep the canonical one).

## 5. Information sources
arXiv (cs.AI, cs.CL, cs.SE, cs.LG); Semantic Scholar and OpenAlex APIs with forward and
backward snowballing from the competitor surveys and awesome-lists; ACL Anthology;
OpenReview (ICLR, NeurIPS, ICML 2023–2026); GitHub repositories with more than 500 stars;
major-lab technical reports; agent leaderboards for the outcomes table.

## 6. Search strategy
Harness block AND LLM block (optional structure block for precision). Final strings, dates
and per-source hit counts are recorded in `data/raw/search_log.md` at search freeze.

## 7. Study records
Rayyan for blinded dual screening; ASReview active learning for screener 1 with a stated
stopping rule; a separate column of LLM votes that never replaces a human vote.

## 8. Data items
`schema/dimensions.json` (38 dimensions in 9 layers), each cell with value, evidence,
confidence, not_reported, coder.

## 9. Outcomes
Reported benchmark scores, cost and tokens per system, model, benchmark, split, with a
comparable_key for rows sharing benchmark, split and base model.

## 10. Risk of bias and confidence
Self-reported leaderboard scores; publication bias; benchmark version drift. Reported as
associational with named confounders.

## 11. Synthesis
Descriptives; co-occurrence (Cramér's V) and clustering; convergence over time; mixed-effects
regression with benchmark by model fixed effects and bootstrap CIs on comparable rows.

## 12. Use of AI assistance
Claude subagents pre-fill coding cells with evidence strings and provide a third screening
vote. Humans are the coders of record for every cell. Human-vs-LLM kappa is reported.
Reporting follows RAISE guidance.

## Amendments
| Date | Section | Change | Reason |
|---|---|---|---|
