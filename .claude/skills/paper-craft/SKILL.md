---
name: paper-craft
description: How to actually write a section of an academic paper — topic-sentences-first, claim-first prose, per-section rhetorical moves, voice rules, and the compression pass. Load together with harness-paper before drafting anything under paper/.
---

# Paper craft: drafting discipline

**Provenance.** The drafting pipeline, the topic-sentences-first rule, the per-section move sets, the
voice rules and the compression sequence below are adapted from
[`snl-ucsb/paper-writing-skill`](https://github.com/snl-ucsb/paper-writing-skill) (MIT), whose author
derived them from forensic analysis of accepted papers and Overleaf edit histories. The LaTeX-safety and
terminology-consistency rules draw on
[`tsinghua-fib-lab/agentsociety`](https://github.com/tsinghua-fib-lab/agentsociety)'s
`easypaper-academic-writing-rules` (Apache-2.0) and
[`jcardif/agent-skills`](https://github.com/jcardif/agent-skills)' `scientific-paper`. Reworded and
adapted here for a pre-registered systematic review; no third-party scripts are installed or run.

**`harness-paper/SKILL.md` outranks this file.** Where they conflict, its HARD rules win. One conflict is
real and is resolved in §2 below — read it before you write a sentence.

## 1. Order of work

**Topic sentences first.** Before any prose, write the section's topic sentences in order, one per
intended paragraph, as a bare list. Read them as a sequence. They must carry the section's whole argument
on their own; if they do not, the problem is the outline, not the prose, and no amount of drafting fixes
it. Only then write the paragraphs.

**One function per paragraph.** Each paragraph is a claim, evidence for a claim, or a synthesis of
claims — never two of those. 4–6 sentences. If a paragraph has two jobs, split it.

**Claim-first openings.** A section, subsection or paragraph opens with its conclusion, not with an
announcement of itself.

- Write: "Weighting inverts the basic fact about what a harness is: 69.3% of coded systems are
  repository-primary, but only 33.3% of the field is."
- Never: "In this section, we present our analysis of the primary artifact dimension."

**Interpret every figure and table in the prose.** "Table~\ref{tab:x} shows X, which means Y." Never
"see Table~\ref{tab:x}" and nothing more. A float the text does not interpret should be cut.

**End each results subsection with a takeaway sentence** that states what the reader should now believe
and how strongly.

## 2. The one conflict, resolved: confidence versus calibration

The source skill says *zero hedging* — "we show", not "we believe"; never "may help". That rule exists to
kill vagueness, and for an engineering paper it is right. **This paper is different, and getting this
wrong would make it dishonest.** Our headline contribution is that we measure how far a literature's
claims outrun its evidence, so our own claim strength has to be exactly calibrated.

Reconcile them this way:

- **Be absolutely direct about what we did and what we measured.** "We coded 47,614 cells." "48.9% of
  cells are not_reported." "The clustering failed both pre-stated bars." No hedging, no "we believe", no
  "arguably", no "it seems".
- **Be exact about the strength of an inference.** An upper bound is called an upper bound. A prediction
  interval that crosses zero is disclosed in the same sentence as the pooled effect. A null is reported
  with its minimum detectable effect. This is not hedging; it is the measurement.
- **Never use vague intensifiers to substitute for a bound.** "Substantially improves" is banned;
  "+0.069 relative, discounted, 95% CI lower bound +0.033" is what we write.

Test: if a sentence could be read as a stronger claim than the data supports, it is wrong, however
confident it sounds. If a sentence is mushy about who did what or what was found, it is also wrong.

## 3. Voice rules

- **Mean sentence length about 21 words; hard maximum 40.** Count the long ones and break them.
- **Active voice where the actor matters** ("we froze the schema"); passive only where the object is the
  real subject ("47,614 cells were coded").
- **Name things.** Every mechanism, arm, dimension and estimator gets its proper name on first use and
  the same name forever after. One term per concept across the whole paper.
- **Delete evaluative adjectives about our own work**: novel, robust, comprehensive, powerful,
  significant (unless statistical), state-of-the-art, elegant, careful.
- **Banned constructions**: rhetorical questions; exclamation marks; rule-of-three flourishes
  ("faster, cheaper, and better"); throat-clearing openers ("It is important to note that", "In recent
  years, with the rapid development of", "As is well known"); "Note that" as a paragraph opener.
- **Em dashes: at most one per paragraph, and never two in a sentence.** Prefer a comma, a colon, or a
  full stop. Heavy em-dash use is a recognised tell of machine-written prose and reviewers notice it.
- **No lists in the argument.** Bullets are for genuinely enumerable things (inclusion criteria, the
  steps of a pipeline, the three cell states). An argument rendered as bullets is an argument that has
  not been made.
- **No forward references to work the paper does not contain.** No "we leave this to future work" as a
  patch over a gap that a reviewer will call a hole; say what is missing and why it is missing.

## 4. Rhetorical moves per section

Follow the move set for the section you own. Each move is one or more paragraphs.

**Introduction** (six moves): Stakes → Problem gap → Key abstraction → What we did → Contributions →
Results preview. The contributions list is numbered, one sentence each, every claim carrying its number
and its bound.

**Background / definition** (three moves): Definition and its boundary cases → The structure that
follows from it (the nine layers) → The measurement vocabulary the rest of the paper uses.

**Related work** (three moves per prior work): Category → What it does and does well → What it does not
attempt, and therefore what remains open. Positioning comes *after* all seven prior works have been
treated on their own terms, never inside each paragraph.

**Methods**: Registration and deviations → Eligibility → Sources and search → Selection → Coding →
Reliability → Synthesis → Reporting-bias assessment. Every count from the data files; every deviation
named as an amendment.

**Results** (per finding, five moves): Setup anchoring (what was measured, on what *n*) → The headline
number with its interval → The diagnostic that could have killed it → The caveat that survives →
Takeaway. A negative result gets exactly the same five moves; do not soften it and do not bury it.

**Discussion / open problems**: What the field should do differently → What our data cannot settle →
What would settle it.

**Threats to validity**: One subsection per threat class, each stating the threat, its direction (does it
inflate or deflate our estimate), and the mitigation actually performed — not the mitigation we would
have liked.

## 5. Compression pass

After drafting, run these seven operations in order. Target 20–35% reduction on a first draft.

1. Shorten sentences over 30 words.
2. Merge paragraphs making the same point.
3. Delete adjectives and adverbs that carry no measurement.
4. Delete tutorial material a reader of this venue already knows.
5. Convert any sentence that buries its claim into claim-first order.
6. Add the missing takeaway sentence to any results subsection lacking one.
7. Promote to a figure or table anything the prose is struggling to enumerate, and cut the prose.

Never pad to reach a length. A section that needs 600 words is 600 words.

## 6. Severity labels for your own self-review

Before handing back, re-read your section and label what you find:

- **CRITICAL** — a number that is not in a data file; a claim stronger than the evidence; a fabricated
  citation; a claim of being first; `not_reported` described as absence. Fix before handback, always.
- **MAJOR** — a missing interval or bound; an uninterpreted float; a paragraph doing two jobs; a missing
  takeaway; a `\ref` with no `\label`.
- **MINOR** — wording, rhythm, a long sentence, an em-dash tic.

Report every CRITICAL you found and fixed. A handback claiming zero problems found is not credible.
