# HARNESS-DB human audit: instructions for the coder

You are checking how agent harnesses are built, by reading their source code and papers. Your
reading is the reference that the released dataset will be scored against, so it has to be your own.
The full protocol is `docs/human_audit_protocol.md`; this page is all you need while coding.

## Before you start

1. **Do not open** `model_answers.csv`, `results.*`, `data/systems.json`, `data/coded/`, the
   explorer, or any other file that carries the dataset's codings. If you see one by accident, write
   that in `human_note` for the cells concerned and carry on.
2. Read `docs/coding_manual.md`, "General rules" (rules 1-9), once. Rule 5 matters most.
3. Fill **one** of `human_sheet.xlsx` (dropdowns) or `human_sheet.csv`, not both. Do not add, delete,
   reorder or edit the grey columns to the left of `human_state`.
4. Put your coder id (`c1`, `c2`, ...) in `coder_id` on every row you fill.

## For each system (7 rows in a row)

1. **Pin the sources.** Open the repository at the version in `pinned_version` (the tag or commit,
   not `main`). If the row says "no pin recorded", pin it yourself: the latest tag on or before
   2026-08-31, otherwise the latest default-branch commit on or before that date, and write the commit
   in `human_locator`. Open the papers in `paper_refs`. **These are your only sources**: no blog posts,
   issues, other forks or later versions, and no web search for what "people say" about the system.
2. Skim the README, the config/settings files, the CLI entry point, the tool registry and the main
   agent loop once; these are shared by all 7 rows.

## For each row (one dimension)

1. Read `dim_name`, `value_glosses` and `decision_rule`. The rule and the glosses are the manual's.
2. **Time-box: 8 minutes per cell.** Start the clock when you start this row. If you cannot settle it
   by then, stop and record `unresolved`.
3. Decide the state, in this order (general rule 5):
   - Found evidence for a feature value -> `coded`, with that value.
   - Did the sources contain **the place where the feature would be declared if it existed** (the
     config schema or settings model, the CLI flags, the tool or plugin registry, the run loop itself,
     a feature list in the docs)? **Yes, and the feature is not there** -> `coded` with the absence
     value (`none`, `open`, ...); cite the place you opened and the search you ran
     (e.g. `grep -rni network src/ -> 0 hits`).
   - **No such place** (only a paper, a thin README, a truncated or missing repository) ->
     `not_reported`. A text that simply never mentions the feature is *not* evidence that the feature
     is absent.
   - Cannot settle it in 8 minutes -> `unresolved`, and say why in `human_note`.
4. Code the **default configuration**; for a multi-valued dimension also list every value reachable by
   shipped configuration without code changes (general rule 4), joined with `|`
   (`self_critique|test_execution`). Never list `none` with other values.
5. Fill:
   - `human_state`: `coded` / `not_reported` / `unresolved`;
   - `human_value`: only when `coded`; values from `permitted_values`, exactly as spelled;
   - `human_evidence_quote`: verbatim code line or paper sentence (not a paraphrase);
   - `human_locator`: `path/to/file.py:LINE@<short-hash>` or `arXiv id Sec. N`;
   - `human_confidence`: `high` (explicit statement or code on the cited line), `medium` (inferred
     from adjacent code, a default or a figure; the ceiling for an absence value unless the docs state
     the absence), `low` (inferred from prose);
   - `human_minutes`: minutes spent on the row, including an even share (1/7) of the time you spent
     pinning and skimming the system;
   - `human_note`: anything a reviewer should know (paper and repo disagree, value list does not fit,
     where the closest value came from).

## When you finish

Save the file where it is and tell the project lead. The analysis
(`python scripts/human_audit.py --analyse`) checks the sheet, refuses rows with invalid states or
values, and only then compares it with the model's answers.

Expected effort: 50 systems x 7 cells = 350 cells; about 36 hours at a realistic pace, never more
than 47 hours at the 8-minute ceiling. Work in sessions of at most 2-3 hours to limit fatigue.
