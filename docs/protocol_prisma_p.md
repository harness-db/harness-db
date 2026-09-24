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

Amendment 2 (v3', 2026-09-16, before screening): the LLM block is waived when a strong harness term is present
("agent harness*", "agentic harness*", "coding agent*", "agent scaffold*", "agentic scaffold*", "software engineering agent*",
"web agent*"), because 2026 harness papers frequently omit "LLM"/"large language model". Applied to arXiv, ACL and
OpenReview; not to Semantic Scholar/OpenAlex (structure block) nor GitHub (README cache unavailable).

Search frozen 2026-09-16 (20:59 UTC): 50,724 raw records, 27,747 candidates after dedupe. Known-item recall (48 ids):
81% search-only, 96% with one round of snowballing and the curated lists (threshold 90%). Full record: `data/raw/search_log.md`.

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
| 2026-09-24 | 4.1, 4.4 | Amendment 10: SYSTEM GROUPING CORRECTED. Records were grouped into systems by repository identity OR fuzzy name similarity, and union-find made the name rule transitive. No two of "RCI agent", "ACID-Agent", "AD-AGENT", "AI2Agent" match each other directly (rciagent against acidagent scores 82, under the 92 threshold), but A-B, B-C, C-D links pooled **129 records carrying 105 distinct names into a single system row**, which was then coded as though it were one harness; `bench-reference-agent` pooled 29 benchmarks' reference agents and `lagent` pooled Lagent, LMAgent, TL Agent, LocAgent, VLAgent and VulAgent. SWE-agent had no row of its own at all, having been absorbed into the chain. Two rules now bound name-based merging: a name similarity never merges records with different known repositories (4.4 already treats a fork or re-implementation as a separate system), and where a repository is missing on either side the normalised name keys must be EQUAL rather than merely similar. Repository identity still merges transitively, which is sound. Effect: the census rises from 6,172 to **6,501 systems**, reference-set recall is unchanged at 27/27, SWE-agent appears as its own system with 7 records, the worst remaining group holds 5 name variants against 114 before, and the coded set is redrawn at **1,231 systems** (H 981 complete, 150 of 683 in P, 100 of 4,837 in O). 1,047 existing codings stand unchanged; 46 were produced from evidence that has since changed and are re-coded, along with 138 newly sampled systems. ACKNOWLEDGED COST: the rule can under-merge. A project spread over several repositories now yields more than one row - OpenHands is the documented case, with four records sharing the name across all-hands-ai/openhands, openhands/openhands and openhands/software-agent-sdk - and the alternative was worse, because records naming "AutoAgent" belong to three unrelated projects (hkuds, vicfigure, thirdlayerinc) that an exact-name rule would have pooled. A split row is visible and explainable; a pooled row destroys the unit of analysis. | Found while attributing leaderboard results to systems: the attribution refused ~50 rows of SWE-agent and Agent S results because the census offered them only inside an over-merged group. The defect propagated from grouping into the coded set, so it had to be fixed before the outcomes table could be joined to the coding. To be filed as an OSF registration update |
| 2026-09-23 | coding manual general rules 2 and 5 | Amendment 9: ABSENCE IS NOT SILENCE. The manual contained two rules that contradicted each other on the commonest case in coding. Rule 2 said that a coder who cannot point at evidence records `not_reported`; rule 5 said that an absence is coded as a value (`none`, `open`) citing the place where the feature would be registered if it existed. A coder who searches for rollback and finds nothing satisfies both, and the two readings of the double-coded sample split on exactly that: their notes agreed on the evidence ("no replay facility found") while one recorded a value and the other recorded silence. That split alone put 19 of 38 dimensions below the 0.6 reliability threshold - `rollback` on 0.97 of its disagreements, `replayability` 0.96, `network_policy` 0.94. Rule 5 is rewritten as an ordered test: if the evidence contains the place where the feature would be declared (config schema, CLI flags, tool or plugin registry, the run loop, a documented feature list) and the feature is not there, code the absence value and cite that place, confidence at most medium; if the evidence contains no such place, code `not_reported` and name the missing place in the note. The absence of a mention in prose is never evidence of absence, and `not_reported` is never correct once the declaring place has been opened. Prompt version bumped to `code-v2-2026-09-23`. | The reliability of the under-reporting result (RQ4) rests entirely on this distinction, and it was unreliable because the manual was ambiguous rather than because the dimensions were ill-defined. Being measured before the dataset is rebuilt: the same 217-system sample is being coded twice under the revised rule so the change is validated, not assumed. To be filed as an OSF registration update |
| 2026-09-20 | coding manual rule 7 | Amendment 8: LOCATOR GRANULARITY. Rule 7 requires a repository locator of the form `path:line@commit`. The evidence bundle presents repository excerpts without their original line numbers, so a coder physically cannot cite a real line; requiring one would only produce fabricated line numbers that nothing downstream could check. v1 therefore accepts `path@commit` as the repository locator, records it with the flag `locator_no_line`, and treats the verbatim quote - verified character-for-character against the exact text the coder was given - as the primary evidence for every cell. Locators that match neither the repository nor the paper form keep the flag `locator_shape_unrecognised` and are counted. In pass A, 489 cells carried a well-formed `path@commit` locator that the original validator had rejected. A v2 update will number the lines inside the bundle so that cited lines can be machine-resolved at the pinned commit. | The requirement was unsatisfiable as written given how evidence is presented to the coder, and the alternative (demand a line number anyway) trades a checkable weaker claim for an uncheckable stronger one. Quote verification is unaffected and remains mechanical. To be filed as an OSF registration update |
| 2026-09-20 | 6 | Amendment 7: SUPPLEMENTARY INDEPENDENT SEARCH, reported as the PRISMA 2020 "identified via other methods" arm. An independently built systematic-review pipeline (Elicit) was given the same definition and eligibility criteria and ran its own search (5 queries, semantic and keyword; abstract-stage screening at thorough depth): 987 records, 411 included. 434 of its records matched our candidate pool, giving an external agreement of 0.843 and Cohen's kappa 0.664 (include/include 246; it-include/we-exclude 62; it-exclude/we-include 6; exclude/exclude 120). 103 of its includes were absent from our 27,747 candidates and 102 were absent from the entire 50,724-record raw harvest. Diagnosis of those 102 against the frozen Boolean: 36 would have matched it (a database-coverage miss) and 66 would not (a vocabulary miss; these are domain-application agent frameworks - chart generation, education, clinical reasoning, autoformalization - whose abstracts use no harness vocabulary). All 103 enter the review through the supplementary arm and are screened by the same full-text procedure, and the 62 title-stage disagreements are re-read at full text. Outputs: `data/screening/elicit_crosscheck.json`, `elicit_gap_diagnosis.json`, `elicit_gap_querytest.json`. | The registered search was validated only against a reference set of well-known systems (46/48 recall), which cannot detect a tail of application-domain frameworks. An independent pipeline gives an external recall estimate: 75% (308/411) of its included set was in our pool. To be filed as an OSF registration update |
| 2026-09-20 | 4, 8 | Amendment 6: the single coding frame of amendment 5 is replaced by a STRATIFIED CODED SET, because full-text screening yielded a census of 6,162 systems against the 150-300 the protocol planned to code. Strata: H (high visibility - a repository with 500+ stars at freeze, or catalogued by a prior harness survey, or a vendor/major-lab product) = 866 systems, coded completely, weight 1; P (not in H but described in a peer-reviewed paper with a public implementation) = 661 systems, random sample of 150, weight 4.41; O (remainder) = 4,635 systems, random sample of 100, weight 46.35. Total coded = 1,116 systems; census-level proportions are reported as weighted estimates with the strata reported separately. Codability is explicitly NOT a stratum criterion: measured on the screening flag it would have dropped 11 of the 27 reference systems present in the census (16/27 kept), the same over-strictness amendment 5 was written to fix; it is recorded per system during coding and reported as data availability. Frame variants measured before deciding, in `data/screening/frame_variants.json` (registered frame 1,669 systems; 500-star bar 1,527; without the peer-reviewed criterion 866; 1,000-star bar 731). Sampling seed `strata-2026-09-20`, assignment in `data/coding_frame.csv` (`scripts/coding_strata.py`). | A single frame cannot both retain peer-reviewed research prototypes and stay within the project's compute budget, and a frame alone supports no inference to the census. Stratified sampling with known rates does both, and keeps the stratum a reader expects to be exhaustive complete. To be filed as an OSF registration update |
| 2026-09-18 | 3, 4 | Amendment 5, after a measured failure in the full-text pilot (325 records): (i) EVIDENCE BUNDLE - a record is read as paper + repository at its pinned reference + official documentation, with repository URLs extracted from the document text; previously only one document was read, so 306 of 325 pilot records were judged on a paper alone. (ii) STEP 7 DEFERRED - the codability count is recorded at screening but no longer excludes there; it is enforced at coding, when the pinned artifact is in hand. Paper-only evidence systematically understates codability: under the old rule 11 of 15 reference systems were excluded, including ReAct, CodeAct, AutoGen, MetaGPT, Reflexion, OS-Copilot and the OSWorld and tau-bench reference agents, all of which the worked examples show are codable from their repositories. Screening therefore decides scope (steps 1-6 and 8-11) plus the existence of an accessible artifact. (iii) CODING FRAME - every in-scope system is reported in the census; HARNESS-DB v1 codes the subset with an accessible implementation meeting at least one of: a public repository with 100 or more stars at search freeze; being named in a prior harness catalogue (Li, Meng, Rombaut, Barbaste) or on a tracked leaderboard; being a vendor or major-lab product with official documentation; or a peer-reviewed paper with a public implementation. A random sample of 100 in-scope systems outside the frame is coded as well, to estimate what the frame misses. (iv) NO HUMAN SCREENING - every screening decision is made by models; the screening framework and its validation are reported as a methodological contribution, with three-vote title agreement, dual full-text agreement, recall against a reference set of known harness systems, and a public per-record audit page. | Measured recall failure of the paper-only codability test; single author with no second screener; the author directed that screening be fully automated and that the framework be described honestly as such. To be filed as an OSF registration update |
| 2026-09-18 | 7 | Amendment 4: human screening removed. Title/abstract: records without a two-of-three model decision (tiebreak split, unsure, conflict) are forwarded to full text (inclusive screening); verification samples keep their automatic decision. Records whose canonical metadata disagrees with the records sharing its identifier (61, a deduplication artefact) go to full text regardless of the title decision. Full text: an LLM applies the decision procedure of section 3 to the retrieved full text (paper, repository, or documentation) with a verbatim quote per step, names the system, and estimates codability; a second independent LLM reading on every include and a random 10% of excludes gives agreement. Validation: recall on a reference set of known harness systems (must-cite systems plus systems catalogued by Rombaut, Barbaste and Meng) with Wilson intervals; not_retrievable records are reported, not decided from abstracts. | Single author without a second screener; the author decided that all screening decisions are automated and validated rather than human-made. To be filed as an OSF registration update |
| 2026-09-17 | 7 | Amendment 3: second human screener replaced by dual-LLM screening with human adjudication. Every record receives two independent model votes (Claude Opus 5 via Claude Code headless; Claude Sonnet 5 via the Messages API; identical prompt ta-v1-2026-09-17). The single human screener (first author) decides every model-model conflict and every 'unsure', and screens a random verification sample of model-agreed includes and excludes (n = 400, stratified) to estimate the error rate of agreed decisions. Reported: model-model kappa, human-vs-each-model kappa on the verification sample and on conflicts, and the agreed-exclude error rate. Full-text screening remains a human decision per record. | No second human coder available; registered dual human screening infeasible for one person on 27,747 records. Filed as OSF registration update 3 |
| 2026-09-16 | 6 | Amendment 2: LLM block waived for 7 strong harness terms (v3'); search frozen the same day at 27,747 candidates, recall 46/48 | 8 known 2026 harness papers matched the harness block but not the LLM block; measured on arXiv (+963 records at ~30% clearly relevant for the 9-term form; 7-term form adopted, +593) |
| 2026-09-16 | 6 | Harness block broadened (v2): add `harness`, "LLM agent*", "LM agent*", "language agent*", "AI agent*", "computer agent*", "multi-agent"; replace bare `orchestration` with "agent orchestration"/"LLM orchestration" | Registered validation rule (known-item recall < 90%) triggered on the test run: v1 recall 3/12, v2 11/12. Applied before screening; to be filed as a registration update on OSF |
