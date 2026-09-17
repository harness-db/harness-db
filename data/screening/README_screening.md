# Title/abstract screening: triage framework (Amendment 3)

One page on how 27,747 candidates become title/abstract decisions with two model votes and one
human screener, per `docs/protocol_prisma_p.md` Amendment 3 (2026-09-17). Everything below is
implemented in `scripts/screen_triage.py`, `screening/screen.html` and `scripts/screen_merge.py`;
the numbers reach the paper only through `data/prisma_counts.json` and
`data/screening/screening_stats.json`.

## Inputs

| file | content |
|---|---|
| `data/raw/candidates.csv` | frozen candidate set (27,747 rows) |
| `data/screening/llm_votes.csv` | vote 1 per record: Claude Opus 5 for 21,480 records, Claude Sonnet 5 fallback for 6,267; prompt `ta-v1-2026-09-17` |
| `data/screening/llm_votes_second.csv` | vote 2 (Claude Sonnet 5) for the 21,480 Opus-voted records, still being appended by a background job |

Each vote is `include` / `exclude` / `unsure` with a one-line reason and the decision step of
`docs/definition.md` section 5 that fired (1 no named system, 2 no loop, 3 no actions, 8 embodied
or date, `none` for include).

## Tiers (applied in order; the first that fires wins)

| tier | rule | decision | human sees |
|---|---|---|---|
| T0 | hard rule, no model: empty title; year < 2022; year > 2026; validated arXiv id YYMM < 2210; leaderboard row whose title is a bare model name (GPT/Claude/Gemini/Llama/Qwen/o-series/Mistral/Grok/DeepSeek/Nova/MiniCPM + version, no agent vocabulary); fraction of ASCII letters in title+abstract < 0.6 | exclude | nothing (all T0 rows are listed in `triage_report.md` for eyeballing) |
| T1 | both models `exclude` | exclude | 3 % verification sample (`verify_exclude`) |
| T2 | both models `include` | forward to full text | 5 % verification sample (`verify_include`) |
| T3 | `include` vs `exclude` | human | every record (`conflict`) |
| T4 | at least one `unsure` | rule R4 below | what R4 cannot resolve (`unsure`) + 3 % / 5 % of R4 excludes / includes |
| pending | second vote missing, or both votes from the same model | none | nothing yet; re-run the script |

No upper date bound is taken from the paper date: a paper posted after 2026-08-31 can describe a
system first released inside the window (criterion c is about the system, decided at full text).

### Rule R4 (T4 only)

Applied to the two reasons and decision steps; the human gets everything the rule does not resolve.

1. `R4_human_leaderboard_record`: source = leaderboard -> human. A leaderboard row is a
   pseudo-record for a system without a paper (protocol 4.3); "leaderboard entry, no harness
   detail" is lack of information, not a negative signal.
2. `R4_human_hedge`: either reason contains a hedge -> human. Hedges: reference, baseline agent,
   ship(s), default agent, may, might, could, possibly, perhaps, likely, seems, appears, unclear,
   not clear, undetermined, cannot, insufficient, no abstract, needs/check/requires full text,
   title only, from the title, unless, if it/the, whether. ("sent to full text" and "route to
   step 10" are the models restating the prompt's survey instruction and are not hedges.)
3. `R4a_both_negative` -> exclude: both votes carry a step 1-3 negative signal. A vote counts when
   it is `exclude` with decision_step 1-3, or `unsure` with decision_step 1-3 whose reason matches
   one of: survey (survey, systematic/literature/scoping review, review of, overview of, taxonomy
   of, tutorial, mapping study, bibliometric), benchmark_only (benchmark, testbed, evaluation
   suite/instrument/study/protocol, evaluates existing; not counted when the reason says
   "evaluated on/in ..." about a system), dataset (dataset, corpus, data collection, annotation
   scheme), position_paper (position paper, perspective, vision paper, opinion, essay, roadmap,
   commentary, editorial), no_loop (no loop, single-call/turn/shot/step, one-shot, non-iterative,
   no environment/tool feedback), no_actions (no tool/action/executed/execution/external, not
   executed, only produces text, text-only, prompting method, prompt engineering,
   chain-of-thought). A 3 % hash sample goes to the human as `verify_exclude`.
4. `R4b_include_plus_unsure_no_negative` -> forward to full text: one vote is `include`
   (decision_step `none`, i.e. that model names a system with a loop) and the other is `unsure`
   with no negative signal in its reason. The human decides at full text. A 5 % hash sample goes
   to the human as `verify_include`.
5. `R4_human_unresolved` -> human: everything else (unsure+unsure without two clean negatives,
   exclude at step 8 + unsure, include + unsure with a negative signal).

R4a knowingly excludes survey/benchmark-only records that the protocol's step 10 would otherwise
link to existing systems at full text; they add no system to `systems` (their bibliographies were
already snowballed), and the verification sample measures the cost.

### Verification samples are re-run safe

A record is in a sample when `sha1(f"{20260917}:{record_id}")` mapped to [0, 1) is below the
rate. Membership never changes when the script is re-run on more coverage, so decisions already
made stay attached. Expected sample size at full coverage: about 3 % of ~10,500 T1 + 5 % of
~2,300 T2 (roughly 430, close to the n = 400 in Amendment 3).

## What the human does

Open `screening/screen.html` in a browser (double-click; no server, no network). It loads
`data/screening/human_queue.js` next to it (or pick `human_queue.json` in the file box). One
record at a time: `y` include, `n` exclude then `1`-`5` for the code (1 out_of_scope,
2 no_harness_description, 3 duplicate_system, 4 not_retrievable, 5 other), `u` unsure / needs
full text (treated as forward), `s` skip, `b` back. Filter by sample type; progress bar; every
keystroke is saved in the browser's localStorage. "Export decisions.csv" downloads
`record_id, human_decision, exclusion_reason, decided_at`; the text box is the copy fallback.
"Merge existing decisions.csv" loads a previous export (newer `decided_at` wins). Save exports as
`data/screening/decisions.csv`.

Verification records look like every other record (both model votes and the sample-type chip are
visible for all records). Decide them on the title/abstract alone, not on the votes.

## Commands, in order

```
python scripts/screen_triage.py            # re-run whenever llm_votes_second.csv has grown
#   -> data/screening/triage.csv, triage_report.md, human_queue.json, human_queue.js
#   open screening/screen.html, decide, export -> data/screening/decisions.csv
python scripts/screen_merge.py             # merge decisions; add --no-render to skip the diagram
#   -> data/screening/screened.csv, screening_stats.json, data/prisma_counts.json, paper/figures/prisma_flow.*
pytest -q tests/test_screening.py          # fixture tests for the tier logic and the merge
```

Re-running `screen_triage.py` after new second votes only moves records out of `pending`; the
human queue grows, existing decisions stay valid, and `screen_merge.py` can be run at any time
on partial coverage (`prisma_counts.json` then carries `_notes.screening_status = "partial: ..."`
and the PRISMA arithmetic check is only enforced once every candidate has a decision).

## How the numbers reach the paper

- `data/screening/screened.csv`: `final_decision` (include = sought for full text, exclude) and
  `decision_source` (`rule` T0, `model_agree` T1/T2, `model_rule` R4, `human`, `human_unsure`)
  per record. A human decision always overrides an automatic one.
- `data/prisma_counts.json`: `screened_title_abstract` (records with a decision),
  `excluded_title_abstract`, `sought_full_text`; `scripts/prisma_diagram.py` renders the flow.
- `data/screening/screening_stats.json`: model-model kappa is in `triage_report.md`; human-vs-
  model kappa (3-class and binarised exclude-vs-forward) overall and per sample type; the
  agreed-exclude error rate (share of `verify_exclude` records the human did not exclude,
  strict = human include, lenient = include or unsure, Wilson 95 % CI, split T1 vs R4a) and the
  agreed-include error rate; `projected_missed_by_auto_exclude` = lenient rate x number of
  automatic excludes, for the limitations section.
- Report in the methods: the tier table of `triage_report.md`, the two kappas, the error rates
  with their n, and the number of records the human decided.

## Current state (see `triage_report.md` for the live numbers)

Second-vote coverage is partial. Records with one vote stay `pending`; the 6,267 records whose
first vote came from the Sonnet fallback need a further Opus pass to get two different-model
votes (the API budget is spent; until then they stay pending and are reported as such).
