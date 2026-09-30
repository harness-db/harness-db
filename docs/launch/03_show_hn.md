# Show HN

Draft. Post from the author's HN account. Show HN rules (news.ycombinator.com/showhn.html, read
2026-09-30): it must be something people can try without a signup; do not ask anyone to upvote or
comment; reading material alone (the paper) is not a Show HN. So the link is the **explorer**, which
needs no login, and the paper goes in the first comment.

## Title

The suggested title, "Show HN: HARNESS-DB – 1,256 LLM agent harnesses coded on 38 dimensions, quote
per cell", is **86 characters**; HN cuts titles at 80. Use this one (80 characters, counted):

```text
Show HN: HARNESS-DB – 1,256 LLM agent harnesses, 38 dimensions, a quote per cell
```

Fallback (71 characters): `Show HN: HARNESS-DB – 1,256 agent harnesses coded with a quote per cell`

## URL

```text
https://harness-db.github.io/harness-db/
```

## First comment (post it yourself immediately after submitting; 152 words with the two link lines)

```text
I built HARNESS-DB while writing a systematic review of LLM agent harnesses: the code between a model and its task that builds the context, runs tools, and decides when to stop.

It codes 1,256 systems, sampled from a pre-registered review (osf.io/ab2wn), on 38 design dimensions. Every value has a verbatim quote and a locator (file:line@commit or paper section) you can re-open, and a cell with no evidence says not_reported instead of guessing.

What surprised me: 48.9% of cells are silence. Weighted to the field, sandboxing is 81.6% undocumented; the control loop is 24.9%. A human audit found the coder right on 202 of 233 cells where it had the evidence, and most misses were files it never saw, so those silence rates are upper bounds.

What I want: corrections (a wrong-cell issue with a quote takes five minutes) and systems we missed.

Data (CC BY 4.0) and loader: https://github.com/harness-db/harness-db
Paper: https://arxiv.org/abs/[arXiv id]
```

## Replies to prepare (answer in your own words; facts only)

- *"Isn't a model coding this unreliable?"* Two model readings agree at mean per-dimension κ 0.784 on
  247 double-coded systems, which is reproducibility, not correctness. The human audit of 350 cells
  matched the model on 57.7% [48.6, 66.9]; 117 of the 148 disagreements were in files the model's
  capped evidence bundle never contained. Both numbers are in the abstract.
- *"So which harness is best?"* The data cannot say much: only 53 of 1,256 systems (4.2%) share a
  benchmark, split and base model with a peer, so the registered regression was not fitted.
- *"Does silence mean the feature is missing?"* No. `not_reported` means undocumented, not absent, and
  it is never recoded as a value.
- *"Why not just read the code?"* Code studies give the strongest evidence per claim and stop at 11 to
  13 systems; this trades depth per system for 1,256 systems. Name Rombaut (arXiv:2604.03515) and
  Barbaste et al. (arXiv:2609.00006) as the code-level work.
