# The HARNESS screening framework (method contribution)

No human screened any record. This file is the honest description of what did, written so it can
become the Methods subsection and be audited by a reader. Numbers are filled from
`data/screening/*_report.md` as each stage completes.

## Why a framework, not a shortcut
A single author cannot dual-screen 27,747 records, and a single LLM pass is not a review method.
We therefore built a staged, self-measuring pipeline and report its error behaviour instead of
claiming human judgement we did not apply. Every decision carries machine-readable evidence.

## Stage 1 - title and abstract, three votes
1. Vote 1: Claude Opus 5 (21,480 records) or Sonnet 5 (6,267), protocol text as system prompt,
   decision steps 1-3 and 8, answer include / exclude / unsure with a reason and the deciding step.
2. Vote 2: the other model on the same record (`llm_votes_second.csv`).
3. Rule-based triage (`scripts/screen_triage.py`): hard rules (date, language, bare model names),
   both-agree decisions, and a documented resolution rule for one-sided unsures.
4. Vote 3 (tiebreak, `ta-v2`): for every record the first two votes did not settle, a third
   reading that sees both prior votes and must answer include or exclude, no unsure.
5. Records still unresolved are forwarded, not excluded: screening is inclusive at this stage.
Reported: model-model agreement (Cohen's kappa 0.564 three-class, 0.616 binary), the tier counts,
and the share of the corpus each rule decided.

## Stage 2 - full text
Every forwarded record is read as an EVIDENCE BUNDLE: the paper (PDF to text, references removed),
the repository at its last release on or before the freeze date, and official documentation.
A model applies the protocol's 12-step decision procedure to the bundle and must return a verbatim
quote for each step it reaches, the system name, version, repository URL, and the dimensions the
bundle can support. Codability is recorded here and enforced at coding (amendment 5).
Every include, and a random 10% of excludes, is read a second time independently; the two readings
give a full-text agreement figure.

## Stage 3 - systems, not records
Includes are grouped into systems by repository URL, then by name similarity, then by the
versioning rule of protocol 4.4. The count reported as "studies included" is a count of systems;
record counts are reported separately.

## Validation, in place of a second human
- **Recall**: a reference set of known harness systems (the systems in our must-cite list plus every
  system catalogued by Rombaut, Barbaste and Meng) must survive screening. Recall is reported with
  Wilson intervals at each stage, and any reference system that is lost is named with the stage
  that lost it. This check is what exposed the paper-only codability failure.
- **Specificity**: surveys, benchmarks and evaluation studies in the must-cite list must be excluded.
- **Agreement**: three-vote agreement at title stage, two-reading agreement at full text.
- **Auditability**: `screening/fulltext_audit.html` shows every record, its decision, the deciding
  step and the quotes behind it. Nothing is hidden behind a score.

## Known limitations, stated in the paper
1. No human adjudicated any decision. Agreement statistics measure consistency between models, not
   correctness; recall against the reference set is our only external accuracy estimate.
2. The reference set is small and biased toward well-known systems, so recall on obscure systems is
   unmeasured.
3. Deduplication once merged records that shared an identifier but not a title (61 cases, found by
   an automated audit); those records were re-read from their own documents.
4. Two models with the same prompt can err the same way; a disagreement of zero would not prove
   correctness.
