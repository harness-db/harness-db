---
name: paper-writing
description: Scientific-paper writing standard for the HARNESS-Review v2 rewrite — narrative-first workflow, framework presentation of the method, figure/table conventions, page budget, claim–evidence map, and the five-dimension self-review. Load before rewriting any section under paper/.
---

# Paper writing standard (v2 rewrite)

**Provenance.** Workflow, paragraph diagnostics, section skeletons, the module triad
(design / motivation / advantage), the table conventions and the five-dimension review are adapted from
[`Master-cai/Research-Paper-Writing-Skills`](https://github.com/Master-cai/Research-Paper-Writing-Skills)
(MIT), itself adapted from Prof. Peng Sida's open notes. Reworded and re-targeted from ML-methods papers
to a pre-registered systematic review; no third-party scripts installed or run. `harness-paper/SKILL.md`
still outranks this file on numeric integrity and claim strength; `paper-craft/SKILL.md` on voice.

## 0. Why the first draft did not read as a scientific paper

It narrated what tools did ("the coder ran pass A, then pass B repaired unresolved cells via `claude -p`"),
cited file names in the body (`data/prisma_counts.json`), listed results in prose that belong in tables,
had no pipeline or framework figure, and ran to 75 pages. A scientific paper presents a **method** — named,
diagrammed, decomposed into modules each with a design, a motivation and an advantage — and then
**evidence** in figures and tables that a reader can check without the prose. Fix those four things and
the paper reads as science.

## 1. Workflow (in this order, always)

1. **Narrative first.** Before touching a sentence, write the paper's one-paragraph story: task → why
   existing surveys cannot answer it → what our framework does differently → what we found → what it
   changes. Every section serves that story or is cut.
2. **Mini-outline per section**: 3–7 bullets, one per paragraph, each a *claim*. If the bullets do not
   carry the argument alone, the outline is wrong; do not draft yet.
3. **Draft one paragraph at a time.** Opening sentence states the paragraph's message. One message per
   paragraph. Every sentence connects to the previous one.
4. **Reverse-outline after each section**: list each paragraph's topic sentence; map topic → thesis and
   evidence → topic in both directions. Orphans are cut or moved.
5. **Claim–evidence map** before handing back, in this exact format, for every claim in the abstract and
   introduction: `Claim: [X] | Evidence: [figure/table/number + source file] | Status: supported / needs
   evidence / weakened`. A claim with no row is not allowed in the abstract or introduction.
6. **Five-dimension self-review** (§7) with pass / revise / needs-new-evidence per item.

## 2. The method is a framework, not a log

**HARD: the manuscript body describes named frameworks with modules; it does not narrate tooling.**

- **Name the frameworks.** The screening pipeline and the coding pipeline are each a named framework
  with a figure. Use the names the rewrite fixes (e.g. *Evidence-Anchored Coding*, *Two-Tier Escalation
  Screening*, *Three-State Cell Contract*) consistently everywhere, including captions and the abstract.
- **Each module gets the triad**: (i) *design* — inputs, what happens, outputs, in "Given …, we first …,
  then …, finally …" form; (ii) *motivation* — the specific failure this module prevents, stated as a
  problem ("A remaining problem is …"); (iii) *advantage* — the measurable behaviour it buys (a
  verifiable quote per cell; a three-state cell that cannot round silence to absence; a gate applied
  before the schema froze).
- **Implementation is a subsection, not a thread.** Model tiers, prompt versions, call budgets, the
  fact that both readings are model instances, and the absence of human cell verification are stated
  **once**, in an "Implementation and disclosure" subsection of the methods and echoed in one sentence of
  the abstract — never re-narrated per stage. This is a disclosure the registration (amendment 4) and the
  venue require; it is not removable, and it is not decoration to be repeated.
- **HARD: no file paths, script names or repository layout in the body.** Replace with "the replication
  package" and a *single* supplementary table mapping each reported quantity to its artefact. Reviewers
  need traceability; readers do not need `scripts/analyse_families.py` in a sentence.
- **No agent vocabulary** in the body: not "agent", "subagent", "autopilot", "run", "pass A/pass B" as
  narrative. Passes become numbered *stages* of the framework with names.

## 3. Figures and tables carry the evidence

- **Teaser figure** (Fig. 1) on page 1–2: the whole pipeline — search → screen → group → code → verify →
  analyse — with the counts at each stage, so the reader sees the study before reading it.
- **Framework figures**: one per named framework, modules as boxes, data flowing between them, the
  three-state cell contract drawn explicitly.
- **Every result that is a list of numbers in prose becomes a table or a figure**, with the prose
  interpreting it ("Table 3 shows X, which means Y"). Prose that enumerates ≥3 numbers is a defect.
- **Table rules**: caption *above*, `booktabs` only, no vertical rules, horizontal rules only between
  logical groups, metric direction in headers where it applies (↑ / ↓), uniform decimals per column,
  best value bold, one message per table, row labels that say what the row is. `\caption` before
  `\label`.
- **Figure rules**: readable at print width, greyscale-safe, every figure interpreted in the prose,
  generated from data by a script in the replication package so it cannot drift.
- **Results tables report**: n, estimate, interval, and the diagnostic that could have killed it, in that
  order. Bound direction (lower / upper) as a column, not a footnote.

## 4. Page budget

**Target: main text ≤ 35 pages in the `manuscript` acmart format** (≈ 20 in `acmsmall`), with a
supplementary document carrying the coding sheet, per-layer dimension tables, the full amendment log,
the PRISMA checklist, the release description and the artefact map. The budget per section:

| section | words | must contain |
|---|---|---|
| Abstract | ≤ 250 | task, gap, framework, 3–4 findings with numbers, disclosure sentence |
| 1 Introduction | ≤ 1,000 | teaser figure, four RQs, numbered contributions with bounds |
| 2 Definition & vocabulary | ≤ 900 | definition, boundary cases as a table, three-state contract |
| 3 Related work | ≤ 1,200 | seven prior works by topic, crosswalk table, four differentiators |
| 4 Framework (methods) | ≤ 2,200 | two framework figures, decision-rule table, reliability table, implementation & disclosure |
| 5 Taxonomy | ≤ 1,200 | taxonomy figure, one consolidated dimension table, ambiguities table |
| 6 Landscape results | ≤ 2,000 | findings 1–5 as figures/tables, one takeaway each |
| 7 Design vs outcomes (RQ3) | ≤ 2,400 | triangulation figure, three designs, bounds table, Tier 3 |
| 8 Open problems | ≤ 900 | checklist table, three open questions |
| 9 Threats | ≤ 1,000 | threat / direction / mitigation table, 300 words of prose |
| 10 Conclusion | ≤ 350 | problem, framework, strongest evidence, scope limitation, next step |

Everything else moves to the supplement with a one-line pointer. Compression order: cut tutorial
material → move enumerations to tables → merge paragraphs making one point → shorten sentences > 30 words.

## 5. Section skeletons for a review

- **Introduction** (five moves): task and why it matters → what prior surveys do and the technical
  reason they cannot answer the design question (not "they are incomplete" but *why*: convenience
  samples, no evidence per cell, no reliability, silence coded as absence) → our framework, teaser figure
  reference, what it changes → findings preview with numbers and bounds → contributions list.
  **Anti-pattern:** presenting a naive version and then our improvement; lead with the challenge.
- **Related work**: competitors first, grouped by topic (catalogues; taxonomies; harness-identity outcome
  studies), each paragraph = scope → representative works → limitation tied to *our* question →
  distinction. Mechanisms and assumptions, not a citation list. Never hide the strongest competitor
  (Guo et al. is the closest to RQ3 and is credited first).
- **Method**: overview (setting, contribution, pipeline figure, roadmap) → one subsection per
  framework, modules in triads → implementation and disclosure. Terminology never oscillates.
- **Results**: per finding — setup (what, on what n) → headline with interval → the diagnostic that could
  have killed it → surviving caveat → one-sentence takeaway. Negative results get the same five moves.
- **Conclusion**: "This paper addresses [gap] with [framework]. The key idea is [three-state contract /
  evidence per cell], which enables [audit of a literature's reporting]. The evidence shows [findings
  with numbers]. A current limitation is [model–model reliability; RQ3 bounded], and [human recoding /
  registered ablation] is the concrete next step."

## 6. Claim calibration (inherited, restated)

Every effect carries its bound direction. Every null carries its MDE. Prediction intervals sit beside
confidence intervals. `not_reported` is documented silence, never absence. Reliability is
reproducibility, never correctness. No claim of being first beyond the four sanctioned ones. Weaken or
remove an unsupported claim rather than assert it.

## 7. Five-dimension self-review (before every handback)

Mark each *pass / revise / needs new evidence*:

1. **Contribution** — is the value new and stated as a mechanism, not a slogan? Would a reader of the
   seven prior surveys learn something they could not get there?
2. **Writing** — could a reader reproduce the framework from §4 alone? Does every module have design,
   motivation, advantage? Any file names, agent words, tooling narrative left?
3. **Evidence strength** — is every headline number in a figure or table with its interval and its
   killing diagnostic? Is any effect written without its bound?
4. **Evaluation completeness** — does RQ3 present all three designs and say which question each can
   answer? Are the pre-registered negatives reported as negatives?
5. **Method soundness** — are the pre-registration, amendments, reliability gate and three-state contract
   presented as design decisions with reasons, and their limits stated?

Then the claim–evidence map (§1.5). A handback without both is incomplete.
