---
name: harness-paper
description: House writing standard for the HARNESS-Review manuscript (paper/). Numeric integrity rules, claim-strength vocabulary, PRISMA 2020 reporting duties, citation rules and LaTeX conventions. Load before writing or editing anything under paper/.
---

# HARNESS-Review house writing standard

This paper's entire contribution is that it measures what a literature claims and shows where the
claims outrun the evidence. A single invented number, overstated effect or fabricated citation destroys
that contribution more thoroughly than a weak result ever could. The rules below are therefore not style
preferences. Rules marked **HARD** are inviolable.

## 1. Numeric integrity

**HARD: every number in the manuscript must be traceable to a named file in this repository.** When you
write a number, you must have read it, in this session, from one of:

- `data/analysis/*.csv` / `*.json` — all analysis outputs
- `data/coded/*.csv` / `*.json` — coded dataset and reliability
- `data/prisma_counts.json` — every PRISMA flow count
- `paper/tables/*.csv` / `*.json` — the published tables
- `docs/headline_findings.md` — the Phase 7 memo, which names its own source per claim

**HARD: never compute a new statistic in your head or by hand.** If the number you want does not exist
in a file, you have three options, in order of preference: (a) write the sentence without it; (b) use the
closest number that does exist and say exactly what it is; (c) leave `\TODO{needs X, not in data/}` and
report it. Never estimate, never round from memory, never infer a percentage from two other percentages.

**HARD: no number may appear in the text that contradicts a number in a table or figure.** If you find a
conflict, stop and report it — do not pick one.

Write numbers with the precision the source file carries and no more. A rate given as `0.8508` in the
file is `85.1%` in prose, not `85%` in one place and `85.08%` in another. Every effect estimate carries
its interval. Every *n* is stated. A percentage whose denominator is not obvious from the sentence gets
the denominator: "784 of 819 comparator arms (95.7%)", never a bare "95.7% of arms".

## 2. Claim-strength vocabulary

This project has spent its whole length distinguishing three things that are easy to conflate. Get these
right or the paper says something false.

**`not_reported` means the sources were read and are silent. It is a measurement claim about the
literature, never a claim about the system.**

- Correct: "the sources are silent on network policy for 93.3% of systems"
- Correct: "network policy is undocumented in 93.3% of systems"
- **FORBIDDEN**: "93.3% of systems have no network policy", "lack sandboxing", "are unsafe"

**`unresolved` means our coder could not settle the cell.** It is an admission about us, not a finding
about them. It is excluded from under-reporting rates. Never pool the two.

**Bound discipline.** Two estimates of design effects point in opposite directions and must never be
described as if they were the same kind of number:

- The cross-paper association (§7, `multi_agent_topology` +1.01 within-key sd) is a **lower bound** on
  magnitude: measurement error on the regressor attenuates towards zero.
- The within-study ablation pooled effects are an **upper bound**: they are author-reported, and the
  design leaves self-reporting as the surviving bias.
- **HARD**: never write an ablation effect without its bound direction or its discount. The claim is
  "at most about +7% relative for self-verification", never "+7%".

**Absence of evidence.** Layers F, G and H carry zero published ablations. That is a fact about the
literature. **FORBIDDEN**: any phrasing implying those components do not matter, or that removing them
is harmless.

**Statistical vocabulary.** "Significant" means a stated test crossed a stated threshold; always give
the test and the p-value. Never "trend towards significance". A null is reported with its **minimum
detectable effect**, so the reader knows what could have been seen. A prediction interval that crosses
zero is disclosed in the sentence that gives the pooled effect, not in a later footnote. Reliability
figures are **reproducibility, not correctness**: both readings are model readings, and any sentence
about kappa must not imply agreement with a human coder.

## 3. Positioning — claims about our own novelty

**HARD: never write "the first systematic review" of this area, or any equivalent.** Seven prior works
exist and all seven are cited: Li et al. (ETCLOVG), Meng et al. (H=(E,T,C,S,L,V)), Guo et al.
(arXiv:2606.20683), Rombaut (arXiv:2604.03515), Barbaste (arXiv:2609.00006), Zhong and Zhu
(arXiv:2605.13357), Banu (arXiv:2605.12239). See `docs/positioning.md`, which is authoritative.

The defensible claims, and the only ones to make: first **pre-registered** review of this area with
per-dimension reliability reported; depth × breadth × **evidence per cell**; first analysis on **coded
design dimensions** rather than harness identity; a **crosswalk** of all prior taxonomies.

## 4. Amendments and adverse results

**HARD: disclose, do not bury.** Eleven accepted protocol amendments exist (12 and 12a filed, pending) and the manuscript states that nine of
eleven are pre-stage and evidence-backed (9 was taken mid-stage; 11 followed the assembly of the comparable set, and its +1.01 is superseded by +0.88 on the rebuilt release). The codability gate as implemented counts `not_reported` as settled — a logged deviation from registered §4.7, never to be described as the registered criterion. The two that draw fire are amendment 4 (no human screener) and
amendment 9 (a coding rule rewritten mid-project); both are stated in the main text, in the methods, not
in an appendix. For amendment 9 the defence is the sequence: the rule was rewritten, validated on 217
systems, and only then applied — say it in that order.

Negative results are reported as results. The design-family clustering **failed** its pre-stated quality
bars and the paper says "verdict: negative" rather than describing the clusters as if they had passed.
The registered mixed-effects regression **was not fitted** because it is not identifiable, and the paper
says so and gives the numbers that show it.

## 5. Citations

**HARD: never invent a citation, a key, an author list, a venue or a year.** Two legitimate sources:

1. **`paper/references/must_cite.bib`** (67 entries) — use these keys. Verify a key exists before you
   cite it; a `\citet` to a missing key is a compile error and a fabrication risk.
2. **`data/papers.csv`** — real corpus records with `title`, `authors`, `year`, `venue`, `arxiv_id`,
   `doi`, `url`. To cite a corpus system's paper, copy the metadata from that row into
   `paper/references/corpus.bib`, and put the record `id` in a `note = {HARNESS-DB record <id>}` field
   so any entry can be traced back. **Copy; never complete from memory.** If `authors` is empty in the
   row, leave the bib field empty rather than filling it in.

Cite with `\citet{}` when the authors are the sentence's subject and `\citep{}` otherwise; the class uses
`acmauthoryear`. Do not cite a system's repository as if it were a paper.

## 6. LaTeX conventions

- Class is `acmart` (`main.tex`); TMLR variant shares `sections/` and `references/`. Write only inside
  `paper/sections/*.tex`. **Do not edit `main.tex`** — the inputs are already wired.
- Each section file opens with its own `\section{}` and uses `\label{sec:...}`. Subsections
  `\label{subsec:...}`, tables `\label{tab:...}`, figures `\label{fig:...}`.
- Tables use `booktabs` (`\toprule`, `\midrule`, `\bottomrule`) — no vertical rules, no `\hline`.
- **HARD: only `\includegraphics` a file that exists in `paper/figures/`.** Check the directory first.
  `\graphicspath{{figures/}}` is set, so reference by basename without extension.
- Numbers in tables are right-aligned; use `S` columns only if `siunitx` is added to `main.tex`, which it
  is not — so plain `r` columns.
- Escape `%`, `&`, `_`, `#` in prose. Use `--` for ranges and `---` for em dashes. Non-breaking space
  before a reference: `Table~\ref{tab:x}`.
- No `\todo` package; use `\TODO{...}` only if you also define it, otherwise leave a `% TODO:` comment.

## 7. Prose

Write for a reviewer who is looking for the weak point. Plain, exact, and short.

- **Lead with the claim**, then the evidence, then the caveat. Never open a paragraph with
  throat-clearing ("It is important to note that", "In recent years, with the rapid development of").
- **Forbidden words**: clearly, obviously, evidently, naturally, of course, dramatically, drastically,
  significantly (unless statistical), very, quite, novel (of our own work), robust (unless a stated
  robustness check), comprehensive (of our own work), "state-of-the-art" as a compliment.
- One core claim per paragraph. If a paragraph has two, split it.
- Prefer the active voice where the actor matters ("we froze the schema"), the passive where the object
  does ("47,614 cells were coded").
- Define every term on first use, including `harness` itself (`docs/definition.md` is authoritative).
  Use one name per concept for the whole paper — `not_reported`, not "missing" or "absent" as synonyms.
- American spelling throughout. Oxford comma. `Cohen's kappa` in prose, `$\kappa$` in tables.
- No bulleted lists in the main argument of a section; lists are for enumerable items (criteria, steps).
- Do not pad. A section that says what it needs in 600 words should be 600 words.

## 8. PRISMA 2020 reporting duties

The methods section is checked item by item against the PRISMA 2020 checklist
(`paper/sections/A2_prisma_checklist.tex`). It must contain, each with its number from
`data/prisma_counts.json`: eligibility criteria; every information source with its search date; the full
search strategy; the selection process including who (or what) screened and how conflicts were resolved;
the data-collection process; the list of variables; the risk-of-bias assessment; effect measures; the
synthesis methods; reporting-bias assessment; and certainty assessment. The registration must be named
with its identifier (`osf.io/ab2wn`) and **every deviation from it flagged as an amendment**.

## 9. Before you hand a section back

1. Every number appears in a file you read, at the precision you wrote it.
2. Every `\cite*` key exists in `must_cite.bib` or in an entry you copied from `papers.csv`.
3. Every `\ref` has a `\label`, and every `\includegraphics` names a file in `paper/figures/`.
4. No forbidden word from §7; no forbidden phrasing from §2.
5. No claim of being first; all seven prior works cited where relevant.
6. `python -c "import pathlib;print(pathlib.Path('paper/sections/<yours>.tex').read_text(encoding='utf-8').count(chr(92)+'section'))"` is 1.
7. State in your report: word count, the files you drew numbers from, and every place you left a TODO.
