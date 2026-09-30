# X (Twitter) thread: 8 posts

Draft. Post from the author's account on launch day, after the arXiv listing is live, and replace
`[arXiv id]` first. Every number is from the abstract or `docs/count_reconciliation.md` (the 86.7% is
202 of 233, `paper/sections/04_methodology.tex`). One emoji in the whole thread (post 1).

Character counts below: **raw** is `len()` of the text; **X-weighted** counts every URL as 23 and
an emoji as 2, which is how X counts. Both must stay at or under 280. Recount after any edit
(the real arXiv id is the same length as `[arXiv id]`, and X counts each URL as 23 whatever its length).

## 1/8  (raw 275, X-weighted 276)

```text
We coded 1,256 LLM agent harnesses on 38 design dimensions and put a verbatim quote behind every value.

48.9% of the 47,728 cells are documented silence: the sources were read, and they do not say.

Least documented layer: the sandbox, 81.6% silent, weighted to the field. 🧵
```

## 2/8  (raw 271, X-weighted 271)

```text
HARNESS-DB covers the software between a model and its task: context assembly, tools, control loop, memory, verification, budgets, sandbox, observability.

Systems from 2022 to 2026, sampled from a 6,504-system frame by a pre-registered PRISMA 2020 review (osf.io/ab2wn).
```

## 3/8  (raw 252, X-weighted 252)

```text
Every cell is in exactly one of three states:

- a value, with a verbatim quote and a locator you can re-open
- not_reported: the sources are silent (undocumented, not absent)
- unresolved: failed validation, claims nothing

One real cell in the image.
```

**Image for post 3** (render the cell as a card; a screenshot of the explorer's cell view works).
Alt text, which X allows up to 1,000 characters:

> One HARNESS-DB cell. System: mini-swe-agent. Dimension: G1 execution_isolation. Value: subprocess.
> Confidence: high. Quote: "By default, actions are executed as `subprocess.run`, i.e., every action
> is independent of the previous ones." Locator: docs/faq.md@a83fcae, the system's pinned version
> (v2.4.6).

Source of the cell: `data/systems.json`, id `mini-swe-agent`, key `execution_isolation` (also shown
in `README.md`, "What a cell is"). Explorer permalink:
<https://harness-db.github.io/harness-db/#system=mini-swe-agent>.

## 4/8  (raw 259, X-weighted 259)

```text
We audited the coder. A human re-read 350 cells and agreed with it on 57.7%.

But 117 of the 148 disagreements sat in files the coder was never sent. Where it had the evidence, it was right on 202 of 233 (86.7%).

So every silence rate here is an upper bound.
```

## 5/8  (raw 267, X-weighted 250)

```text
Authors' own ablations barely separate design choices: 14 of 22 poolable dimensions survive a publication-bias discount, and 7 design dimensions carry no ablation at all.

Browse every system, and open any quote at its source:
https://harness-db.github.io/harness-db/
```

## 6/8  (raw 268, X-weighted 268)

```text
Load it in three lines:

from datasets import load_dataset
cells = load_dataset("bhaskar-ai/harness-db", "cells", split="train")
systems = load_dataset("bhaskar-ai/harness-db", "systems", split="train")

The Python loader in the repo also applies the sampling weights.
```

## 7/8  (raw 231, X-weighted 179)

```text
A wrong cell is a gift. If you maintain or know a harness, one issue with a quote and a file:line@commit settles a cell. The not_reported cells help most.

https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml
```

## 8/8  (raw 242, X-weighted 204)

```text
Paper: https://arxiv.org/abs/[arXiv id]
Data and code: https://github.com/harness-db/harness-db
Zenodo: https://doi.org/10.5281/zenodo.23031354

We did not measure which harness is best. We measured how much of harness design is written down.
```

## Notes

- Post 4 must keep both numbers: 57.7% overall agreement and 202 of 233 on cells whose evidence the
  coder received. Quoting only the 86.7% would overstate the coding.
- "Weighted to the field" means the stratified sampling weights (6,504-system frame); do not shorten it
  to "81.6% of harnesses". The rate is a share of cells, and it is an upper bound.
- Do not add "first" anywhere. Seven prior surveys and taxonomies exist (`docs/positioning.md`).
- Pin post 1 to the profile for launch week. Reply to corrections publicly and link the issue.
