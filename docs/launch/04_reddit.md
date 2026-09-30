# Reddit: r/MachineLearning and r/LocalLLaMA

**Read before posting.** r/LocalLLaMA rule 3 (Wayback snapshot of the rules, 2026-08-07) says
"Completely/primarily LLM generated copy, code is not allowed", and rule 4 asks that self-promotion stay
under about 10% of your activity with affiliation disclosed. These drafts were written with an AI
assistant. Treat them as a fact sheet and an outline: **write the post yourself**, keep the numbers
exactly, and disclose that you are the author. r/MachineLearning rule 5 removes arXiv links posted without
body text, and rule 2/3 forbid marketing. Neither subreddit's live rules page could be fetched on
2026-09-30 (Reddit blocked the fetch); re-read both sidebars on launch day.

Post r/MachineLearning on the launch day after HN; post r/LocalLLaMA a day later, not the same hour.

---

## r/MachineLearning

Flair: **Research**. Title (the `[R]` tag is the long-standing convention):

```text
[R] HARNESS-DB: 1,256 LLM agent harnesses coded on 38 design dimensions, with a quote behind every value; 48.9% of cells are documented silence
```

Body outline (facts to use, in this order):

```text
Paper: https://arxiv.org/abs/[arXiv id]
Data and code: https://github.com/harness-db/harness-db (data CC BY 4.0, code MIT)
Explorer: https://harness-db.github.io/harness-db/

What it is. A pre-registered (osf.io/ab2wn) PRISMA 2020 review of agent harnesses, the software between a model and its task environment. A 6,504-system sampling frame; 1,256 systems coded on 38 dimensions in nine layers, 47,728 cells. Each cell is a value with a verbatim quote and a re-openable locator, or not_reported (sources silent), or unresolved (claims nothing).

Findings.
- 48.9% of cells are documented silence. Weighted to the field, from 24.9% ± 1.2 (control loop) to 81.6% ± 1.8 (sandbox). These are upper bounds.
- Weighting reverses the modal release artifact: repository-primary is 69.2% of 1,252 coded systems but 33.3% weighted.
- 265 of 666 dimension pairs pass a BH-adjusted permutation test only when silence is counted as a category.
- Only 53 of 1,256 systems (4.2%) share a benchmark, split and base model with a peer, so the registered regression was not fitted. Multi-agent topology reaches +0.88 within-key SD [+0.38, +1.31].
- Authors' own ablations barely separate components: 14 of 22 poolable dimensions pass a bias discount, pooled relative gains +0.114 to +0.259 before a median discount of 49.8%, all upper bounds; 7 dimensions carry none.

Limits, stated plainly. The coders were language-model instances under a fixed protocol. Two model readings agree at mean per-dimension kappa 0.784 (247 double-coded systems). A human reading of 350 cells matched the model on 57.7% [48.6, 66.9]; 117 of the 148 disagreements were in files the model's capped evidence bundle never contained, and on cells whose evidence it received it was right on 202 of 233.

Discussion question to end on: which of the silent dimensions (sandbox, network policy, replay, rollback) would you most want harness authors to document, and how would you want it reported?
```

## r/LocalLLaMA (shorter; post a day later)

Flair: **Resources** if offered (check the flair list on the day). Title:

```text
I coded 1,256 agent harnesses (OpenHands, Codex CLI, Claude Code, Hermes, nanobot, ...) on 38 design dimensions. Half the cells are "not documented".
```

Body outline:

```text
Author here (disclosure). Open dataset, CC BY 4.0: https://github.com/harness-db/harness-db
Explorer, no login: https://harness-db.github.io/harness-db/

- 38 dimensions per harness: context assembly, tool-call format, loop, memory, verification, budgets, sandbox, observability.
- Every value has a verbatim quote plus a file:line@commit or paper section.
- 48.9% of cells are silence. The sandbox layer is 81.6% silent, weighted to the field; network policy is the single least documented dimension.
- If you run local models: model_agnostic (M3) and tool_call_format (B1) are filterable in the explorer.

If your harness is in there and a cell is wrong, a wrong-cell issue with a quote fixes it in the next release. Paper: https://arxiv.org/abs/[arXiv id]
```

The "network policy is the least documented dimension" line is from `data/analysis/summary_one_screen.csv`
(G3 `network_policy`, weighted not_reported rate 0.933, the maximum over the 38 dimensions). Check that the
explorer exposes the M3 and B1 filters before posting that bullet.
