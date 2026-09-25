---
name: paper-review
description: Adversarial reviewer rubric for the HARNESS-Review manuscript — review dimensions, the questions a hostile reviewer actually asks, severity taxonomy and output format. Load when reviewing or self-critiquing anything under paper/.
---

# Adversarial review rubric

**Provenance.** The review dimensions, the severity taxonomy, the "what did this paper update in my
beliefs" framing and the meta-review concern table are adapted from
[`alexwortega/ai-peer-review-skill`](https://github.com/alexwortega/ai-peer-review-skill) (MIT), with
structure from [`shaowen-ye/manuscript-review-skill`](https://github.com/shaowen-ye/manuscript-review-skill)
(MIT). Reworded and specialised to a pre-registered systematic review; no third-party scripts installed
or run. Read `harness-paper/SKILL.md` for the claims this project may and may not make.

Review as the reviewer this paper will actually get: someone who has read the seven prior surveys, is
sceptical that an LLM-assisted review can be rigorous, and is looking for the sentence that overclaims.

## 1. Dimensions

**Evidence rigour.** What did this paper actually update in my beliefs? Does each headline claim rest on
a number that exists, at the precision stated, in the released data? Are the negative results reported as
results, or softened? Is any conclusion resting on a subgroup chosen after seeing the data?

**Claim calibration.** This is the dimension that matters most here. For every effect: is its bound
direction stated? Is the discount applied? Is the prediction interval disclosed beside the confidence
interval? Is a null reported with its minimum detectable effect? Is any `not_reported` rate described as
absence rather than silence? Is `unresolved` ever pooled with `not_reported`?

**Methodology and pre-registration.** Is every deviation from `osf.io/ab2wn` declared as an amendment
with a date and reason? Are the two contentious amendments (4, no human screener; 9, a coding rule
rewritten mid-project) in the main text rather than an appendix? For amendment 9, is the sequence stated
in the order rewritten → validated on 217 systems → applied? A reviewer who finds an undeclared deviation
will reject.

**Reliability versus correctness.** Does any sentence about kappa imply agreement with a human coder? It
must not: both readings are model readings. Is the distinction stated where the kappa table appears, not
later?

**Reproducibility.** Can an independent reader re-derive each published number from the released files?
Is the script or file named? Is the superseded pre-amendment-9 coding published and marked?

**Prior art and positioning.** Are all seven prior works cited and treated on their own terms? Is any
claim of primacy made? Guo et al. (arXiv:2606.20683) does the closest thing to our design-versus-outcome
analysis, by harness identity — is it credited as such rather than dismissed?

**Presentation.** Is every float interpreted in the prose? Does every claim in the abstract appear in the
body with its caveat? Does the paper read as if written by a machine — em-dash tics, throat-clearing
openers, uniform paragraph shapes, evaluative adjectives about its own contribution?

## 2. The questions to ask directly

1. Which single sentence in this paper is the most overstated, and what would make it exact?
2. Which number could I not find in the released data, at the precision written?
3. Which caveat is in a footnote or appendix that a fair reading would put in the main text?
4. What is the simplest alternative explanation of the headline finding, and does the paper rule it out?
5. Which design choice in the analysis was not pre-registered, and could it have gone the other way?
6. If I only read the abstract, what would I wrongly believe?
7. What would I need to see to move from "suggestive" to "established" on the main design finding?
8. Where does the paper claim a measurement about systems when it has only a measurement about documents?

## 3. Severity taxonomy

- **REJECT-LEVEL** — an undeclared protocol deviation; a number that contradicts the released data; a
  fabricated citation; a claim of primacy contradicted by prior work; a silence-as-absence claim in the
  abstract or a contribution bullet.
- **MAJOR REVISION** — an effect without its bound or discount; a missing prediction interval; a null
  without its minimum detectable effect; reliability presented as correctness; a negative result softened;
  a caveat buried; an uncredited prior work.
- **MINOR REVISION** — an uninterpreted float; a paragraph doing two jobs; a missing takeaway; wording,
  rhythm, machine-prose tells.

## 4. Output format

- **Summary** — one paragraph restating the contribution and scope as the paper actually supports it, not
  as it advertises itself.
- **Strengths** — specific and short; a review that finds none is not credible and will be discounted.
- **Concerns**, each as: the claim quoted verbatim with its file and line, the problem in one sentence,
  the severity label, and **the concrete fix**. A concern without a fix is a complaint.
- **Verdict** — Accept / Minor revision / Major revision / Reject, with the one change that would most
  raise the verdict.
- **Belief update** — what you now believe that you did not before reading, and what you still do not
  believe. If nothing changed, say so; that is itself a finding about the paper.

## 5. Rules for the reviewer

Quote before you criticise: every concern names the file and quotes the sentence. Verify before you
assert: if you claim a number is wrong, read the data file and give the correct one. Do not invent a
missing citation to accuse the authors of having missed it. Rank concerns by severity, most severe first,
and do not pad the list — five real problems beat twenty stylistic notes. If the paper is right and you
expected it to be wrong, say that plainly.
