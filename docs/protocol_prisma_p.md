# Review protocol (PRISMA-P)

Status: draft. This file mirrors the OSF pre-registration. Once registered, add the OSF
DOI and timestamp here and do not edit the registered sections; log amendments below.

OSF project: https://osf.io/vkjer/ (private, created 2026-09-16)
OSF registration: https://osf.io/ab2wn/ (Generalized Systematic Review Registration v6; approved 2026-09-16; embargoed until 2026-10-31, to be ended early on arXiv posting)
Registered on: 2026-09-16 18:12 UTC, before any searching or screening
Registration DOI: _minted by OSF when the embargo ends; add here_
Registration update 1 (search strings v2): filed 2026-09-16 as schema response 6aaaf3afc098c3275558de31, pending contributor approval

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
An agent harness is the software layer between a language model M and a task environment E that
repeatedly assembles the model's input, executes the model's chosen actions, and decides whether
to continue, so that a model that can only emit text becomes a system that completes multi-step
tasks. Formally, given M (weights plus decoding configuration) and E (state, executable
operations, task), a harness H implements eight functions, each coded by one layer of
`schema/dimensions.json`: (i) assembles the model's input at each step (layer A); (ii) exposes
and executes actions and tools (B); (iii) decides continuation and termination (C, F1);
(iv) holds state across steps and runs (D); (v) verifies and repairs (E); (vi) enforces budgets
and permissions (F, G4, C5); (vii) isolates execution (G); (viii) records and governs (H).
Clauses (i)–(iii) are necessary; (iv)–(viii) may be trivial and are then coded `none`, not
`not_reported`. ReAct is the minimal harness and the earliest system in the corpus. An agent is
the run-time composition (M, H, E); the harness is the unit we code. The harness is not the
model (weights, decoding, trained tool-call syntax), not a prompt alone (a harness contains
prompts), not a framework (a construction kit; its shipped default agent is a harness), not a
runtime or sandbox product alone (part of the harness only when the harness chooses and
configures it), not a benchmark (its reference agent is a harness), and not training (out of
scope unless it changes the harness). The full definition, boundary rules with worked examples,
and the resolved edge cases are in `docs/definition.md`.

Decision procedure (applied in order; stop at the first exclusion; log the deciding step):
1. Name the candidate system. No named system that runs a model: `no_harness_description`.
   Record only evaluates or discusses existing systems: go to step 10.
2. Loop test. More than one model call per task, with call t+1 depending on an action taken
   after call t? If not: `out_of_scope` (no_loop).
3. Action test. Model output selects an operation executed outside the model with the result
   fed back? If not: `out_of_scope` (no_actions).
4. Input-assembly test. Any description of how the model's input is built per step? If not,
   the record will fail step 7.
5. Whole-versus-part test. Sandbox, MCP server, memory store, skills pack, tracing SDK,
   protocol spec, or tool library on its own: `out_of_scope` (component_only); record in
   `data/components.csv`.
6. Framework test. Construction kit with a shipped runnable default agent: continue with that
   default as the system. No default agent: `out_of_scope` (framework_no_default).
7. Codability test (criterion b). At least 19 of 38 dimensions codable with evidence from paper,
   pinned repo, and official docs, with at least one dimension in each of layers A, B, C? If not:
   `no_harness_description`. Leaked or decompiled source is not admissible.
8. Domain and date test (criteria a, c). Embodied robotics: `out_of_scope` (embodied). First
   public release outside 2022-10-01..2026-08-31: `out_of_scope` (date).
9. Language test (criterion d). No English paper or documentation: `other` (language).
10. Duplicate test. Same system, same major version already in `systems`: link the record as a
    paper (and results), log `duplicate_system`. Major redesign per §4.4: new versioned row.
11. Training test. Record only changes the model: `out_of_scope` (training_only); side-table
    entry if it modifies any harness component.
12. Include: assign `system_id`, pin the version per §4.5, pass to coding.

## 4. Eligibility criteria
Include a record if all of: (a) it describes a system that wraps an LLM in a loop with tools
or an environment, i.e. satisfies clauses (i)–(iii) of §3; (b) enough detail is available to
code at least 50% of dimensions (19 of 38) from paper, repository, or official documentation,
per §4.7; (c) the system's first public release is between 2022-10-01 and 2026-08-31
inclusive; (d) the paper or documentation is available in English, per §4.6.
Exclude: training/RL-only work with no harness description (side table if it changes the
harness); embodied robotics; benchmarks with no reference harness (recorded for the outcomes
table only); single-prompt agents without a loop; components that implement one clause without
the loop (sandboxes, MCP servers, skills packs, protocol specs, tracing SDKs); frameworks with
no shipped default agent; duplicate descriptions of one system (keep the canonical one, link
the rest).

### 4.1 Unit of analysis
The unit is the system: one named harness at one pinned version. `systems` has one row per
system-version; `papers` is many-to-many with systems; `results` is many-to-one with systems
(system, model, benchmark, split). A framework enters as one system through its shipped default
agent at default configuration. A benchmark's reference agent enters as a system named
"<benchmark> reference agent". Reported counts (PRISMA "studies included") are counts of
systems; counts of records are reported separately.

### 4.2 Multiple papers per system
All papers, repositories, and technical reports that describe a system are linked to it in
`papers`. The canonical source is the one that first names the system; if that source is a
repository, the canonical source is the repository. Evidence for a coded cell may come from any
linked source, but where linked sources conflict, the pinned version (§4.5) decides and the
conflict is noted in the cell's evidence. A record that adds no new system and no new version is
logged `duplicate_system` at full-text screening and is still linked and, if it reports scores,
still contributes `results` rows.

### 4.3 Systems with no paper
A system with no paper enters if it satisfies (a)–(d) and, at search freeze, its repository has
more than 500 GitHub stars or it is a released product from a major lab with published
technical documentation. `papers` receives a pseudo-record with URL, retrieval date, and a
Wayback Machine capture; `M4 primary_artifact` is `repo` or `tech_report`. Systems whose only
evidence is a leaked or decompiled artifact are not eligible.

### 4.4 Versioning on major redesign
A system gets a second row (`<system_id>-v<N>`) only when both hold: the maintainers publish a
major version with a documented architectural change (release notes, migration guide, or a new
paper), and coding at the two versions differs on at least three dimensions in layers A–H.
Otherwise the system has one row at the pinned version and earlier versions are noted in
`M6`'s evidence. Forks and re-implementations are separate systems under the same rule
(architecturally distinct on at least three A–H dimensions); otherwise `duplicate_system`.

### 4.5 Version cutoff
Every system is coded at one pinned version: the latest tagged release on or before 2026-08-31;
if the repository has no tags, the latest default-branch commit on or before 2026-08-31; for
closed systems, the vendor documentation as captured on or before 2026-08-31 (Wayback capture
URL recorded). `M6 pinned_version` records the tag, commit hash, or capture. Changes after the
pin are not coded in v1 of HARNESS-DB; they are candidates for the v2 update.

### 4.6 Language
The paper, README, or official documentation must be available in English (machine
translation by the screeners is not used). Source code, code comments, and issue threads may be
in any language. A system whose only documentation is non-English is excluded with code
`other` and sub-reason `language`, and is listed in the PRISMA flow as such.

### 4.7 Minimum codability
A record is codable if, from the union of its linked sources at the pinned version, at least 19
of the 38 dimensions in `schema/dimensions.json` can be assigned a value with a non-empty
evidence string (verbatim quote with section, URL, or `path:line@commit`), and at least one
dimension in each of layers A, B, and C is among them. `none` counts as a value when the source
states or the code shows the absence; `not_reported` does not count. Codability is assessed at
full-text screening by the screener and confirmed by the coder; a system that turns out to fall
below 19 during coding is moved to excluded with `no_harness_description` and the PRISMA counts
are updated.

### 4.8 Exclusion reasons
Each excluded record carries exactly one primary code and an optional sub-reason in
parentheses. Codes and one-line definitions:
- `out_of_scope`: passes none of, or fails, criterion (a) or (c): no loop (no_loop), no
  executed actions (no_actions), a component that implements one clause without the loop
  (component_only), a construction kit without a default agent (framework_no_default), a
  benchmark without a looping reference agent (benchmark_only), model training with no harness
  change (training_only), embodied robotics (embodied), or first release outside the window
  (date).
- `no_harness_description`: passes (a) and (c) but fails (b): a system is named, but fewer than
  19 of 38 dimensions, or none in one of layers A, B, C, can be coded with evidence from
  admissible sources.
- `duplicate_system`: the record describes a system-version already in `systems` and adds no
  new system; the record is linked as a paper and any scores go to `results`.
- `not_retrievable`: no full text, repository, or documentation could be obtained after
  searching the publisher, preprint servers, archived copies, and an author request with a
  14-day wait.
- `other`: any remaining reason, mandatory free-text sub-reason; in practice non-English
  documentation (language) or a retracted or withdrawn record (retracted).
Counts per code, and per sub-reason for `out_of_scope`, are reported in the PRISMA flow
diagram and in `data/prisma_counts.json`.

## 5. Information sources
arXiv (cs.AI, cs.CL, cs.SE, cs.LG); Semantic Scholar and OpenAlex APIs with forward and
backward snowballing from the competitor surveys and awesome-lists; ACL Anthology;
OpenReview (ICLR, NeurIPS, ICML 2023–2026); GitHub repositories with more than 500 stars;
major-lab technical reports; agent leaderboards for the outcomes table.

## 6. Search strategy
Harness block AND LLM block (optional structure block for precision on the two largest
sources). Final strings, dates and per-source hit counts are recorded in
`data/raw/search_log.md` at search freeze.

Harness block (v2, 2026-09-16, after the registered validation rule triggered; see Amendments):
"agent harness" OR harness OR "agent scaffold*" OR "agentic framework" OR "agent framework"
OR "LLM agent*" OR "LM agent*" OR "language agent*" OR "AI agent*" OR "computer agent*"
OR "multi-agent" OR "tool-use agent" OR "coding agent" OR "software engineering agent"
OR "computer-use agent" OR "GUI agent" OR "web agent" OR "multi-agent framework"
OR "agent orchestration" OR "LLM orchestration"

LLM block: "large language model" OR LLM OR "foundation model" OR "language model agent"

Validation: known-item set of 12 canonical papers (`data/raw/search_log.md`). v1 strings:
3/12 on arXiv. v2 strings: 11/12 on arXiv (11,834 hits vs 4,030). The remaining item
(ReAct, arXiv:2210.03629, whose abstract never says "agent") is reached by backward
snowballing, which is part of the protocol. Recall is re-measured at search freeze on the
full 30-item known-item set.

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
| 2026-09-16 | 6 | Harness block broadened (v2): add `harness`, "LLM agent*", "LM agent*", "language agent*", "AI agent*", "computer agent*", "multi-agent"; replace bare `orchestration` with "agent orchestration"/"LLM orchestration" | Registered validation rule (known-item recall < 90%) triggered on the test run: v1 recall 3/12, v2 11/12. Applied before screening; to be filed as a registration update on OSF |
