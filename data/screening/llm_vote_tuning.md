# LLM third vote — backend and throughput tuning (2026-09-17)

`scripts/screen_llm.py --backend claude-code` runs Claude Code's headless mode (`claude -p
--output-format json --json-schema … --system-prompt-file … --tools ""`) on the machine's Claude
Code login, so no API key is needed and usage is consumed from the subscription. Model alias
`opus` resolved to `claude-opus-5` in every run (one batch of test B fell back to `claude-opus-4-8`
under load with default effort). Prompt `ta-v1-2026-09-17` (protocol §3 definition, decision steps
1–3 and 8, §4 criteria, loaded at run time). `cost_usd` values are Claude Code's list-price
equivalent (`total_cost_usd`), not a charge.

## Throughput tests (dry runs on random records, different seeds; all 0 failed)

| test | sessions (workers) | batch | effort | records | s/record | extrapolated for 27,747 | list-equiv. $/record | notes |
|---|---:|---:|---|---:|---:|---:|---:|---|
| dry run | 2 | 20 | default | 50 | 1.81 | 14.0 h | 0.039 | first end-to-end run |
| A | 4 | 20 | default | 80 | 0.73 | 5.7 h | 0.036 | |
| B | 8 | 20 | default | 160 | 1.39 | 10.7 h | 0.035 | contention; one batch served by opus-4-8 fallback |
| C | 8 | 40 | default | 160 | 1.15 | 8.8 h | 0.023 | one batch missed a vote, retried |
| D | 8 | 40 | **low** | 160 | 0.20 | 1.5 h | 0.018 | output tokens ÷3 (thinking) |
| E | **12** | **40** | **low** | 240 | **0.16** | **1.2 h** | 0.013 | chosen configuration |
| F | 8 | 60 | low | 120 | 0.58 | 4.5 h | 0.009 | too few batches to fill 8 sessions |
| G | 16 | 40 | low | 320 | 0.21 | 1.6 h | 0.016 | no gain over 12; one batch missed a vote, retried |

## Does low effort change the votes?

Test C (default effort) and C-low (`--effort low`) voted on the same 160 records (seed 3):
vote agreement 134/160 = 84 %, vote + decision-step agreement 109/160; **0 include↔exclude
flips**. Disagreements: include→unsure 12, unsure→exclude 7, exclude→unsure 5, unsure→include 2 —
low effort is slightly more conservative (more `unsure`), which only routes more records to
full text. Adopted for the full run.

## Full run

`python scripts/screen_llm.py --backend claude-code --workers 12 --batch-size 40 --effort low`
→ `data/screening/llm_votes.csv` (started 2026-09-17 ~14:41 UTC; resumable). The dry-run files
of the tests above are kept in `data/screening/tuning/` for the record; they are not part of the
vote file. Human screeners must not open `llm_votes.csv` before adjudication (protocol §7: the
LLM vote is a separate column that never replaces a human vote).
