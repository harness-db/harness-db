# Search freeze run — notes for the orchestrator (2026-09-16)

Written by the harvesting task. Nothing below is estimated: every number comes from a script
`SUMMARY` line, a log, or `scripts/harvest/known_items.py`. `scripts/dedupe.py` was **not**
run and `search_log.md` was **not** edited (orchestrator's job).

## 1. Timeline (UTC, 2026-09-16)

| step | command (run from repo root) | start | end | outcome |
|---|---|---|---|---|
| S2 count-only | `python scripts/harvest/s2.py --since 2022-10-01 --until 2026-08-31 --count-only --with-structure-block` | 19:47:21 | 19:47:24 | both blocks 20,019; + structure 6,744 |
| OpenAlex count-only | `python scripts/harvest/openalex.py --since 2022-10-01 --until 2026-08-31 --count-only --with-structure-block` | 19:47:35 | 19:47:41 | title+abstract 40,607; + structure 14,812; `search=` full text 128,906 |
| arXiv, attempt 1 | `python scripts/harvest/arxiv.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/arxiv.jsonl` | 19:46:57 | 19:55:04 | **failed at 10,000/11,242**: arXiv API returns HTTP 500/503 for `start >= 10000` (8 × 5xx, 6 retries) |
| arXiv, attempt 2 (date-sliced code) | same command, after adding recursive submittedDate slicing (`--slice-max 2000`) | 19:56:45 | 20:01:19 | 4,811 written, then **HTTP 429 after 6 retries** (arXiv throttling; 11 × 429) |
| arXiv, attempt 3 (resume) | `python scripts/harvest/arxiv.py --since 2025-12-07 --until 2026-08-31 --max-records 0 --resume --out data/raw/arxiv.jsonl` | 20:02:04 | 20:11:14 | +5,750 (7 × 429, all recovered with 10 s-base backoff) |
| arXiv, attempt 4 (resume, cut slice) | `python scripts/harvest/arxiv.py --since 2025-09-09 --until 2025-12-07 --max-records 0 --resume --out data/raw/arxiv.jsonl` | 20:11:35 | 20:12:32 | +681 → **11,242 = server total** |
| ACL Anthology | `python scripts/harvest/acl.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/acl.jsonl` | 19:47:03 | 19:47:44 | ok, 1,363 (cached bib, no download) |
| OpenReview | `python scripts/harvest/openreview.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/openreview.jsonl` | 19:47:09 | 19:48:35 | ok, 1,686 (login from `.env`, 80 requests, 11/11 venues) |
| GitHub | `python scripts/harvest/github.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/github.jsonl` | 19:47:15 | 20:07:49 | ok, 1,361 (2,606 `gh api` calls) |
| Semantic Scholar | `python scripts/harvest/s2.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --with-structure-block --out data/raw/s2.jsonl` | 19:47:52 | 19:48:04 | ok, 6,744 (9 requests, API key present) |
| OpenAlex | `python scripts/harvest/openalex.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --with-structure-block --out data/raw/openalex.jsonl` | 19:47:58 | 20:03:18 | **partial: 8,200 of 14,812** — OpenAlex daily API budget exhausted (see failures) |
| awesome-lists | `python scripts/harvest/awesome_lists.py --out data/raw/awesome.jsonl` | 19:51:03 | 19:51:06 | ok, 822 |
| known-item recall (before snowball) | `python scripts/harvest/known_items.py --json` | 20:12 | | 31/48 |
| snowball, attempt 1 | `python scripts/harvest/s2.py --since 2022-10-01 --until 2026-08-31 --snowball 2606.20683 2604.03515 2605.12239 2609.00006 2605.13357 2605.27922 2607.22585 2608.26218 2405.15793 2407.16741 2210.03629 --snowball-title "Agent Harness Engineering: A Survey" "Agent Harness for Large Language Model Agents: A Survey" --out data/raw/snowball.jsonl` | 19:57:10 | 19:58:40 | 10,323 written but ReAct citations aborted with `HTTP 400 offset + limit must be < 10000` |
| snowball, attempt 2 (ceiling fix) | same command | 20:00:04 | 20:01:27 | ok, **11,289** written (13,269 listed before the date filter; 35 requests) |
| known-item recall (after snowball) | `python scripts/harvest/known_items.py --include-snowball --include-awesome --json` | 20:12 | | 42/48 |
| freeze copies | `gzip -9` of every `data/raw/*.jsonl` into `data/raw/frozen/` (Python `gzip`) | 20:12:53 | | 8 files |

Date window on every source: 2022-10-01 → 2026-08-31 inclusive. Cap: none (`--max-records 0`,
now the default in `common.py`).

## 2. Query strings as issued (v2 harness block, protocol section 6)

Harness block (`common.HARNESS_TERMS`, verbatim from the protocol):
`"agent harness" OR harness OR "agent scaffold*" OR "agentic framework" OR "agent framework" OR "LLM agent*" OR "LM agent*" OR "language agent*" OR "AI agent*" OR "computer agent*" OR "multi-agent" OR "tool-use agent" OR "coding agent" OR "software engineering agent" OR "computer-use agent" OR "GUI agent" OR "web agent" OR "multi-agent framework" OR "agent orchestration" OR "LLM orchestration"`

LLM block: `"large language model" OR LLM OR "foundation model" OR "language model agent"`

Structure block (`--with-structure-block`, **S2 and OpenAlex only**):
`"tool call*" OR "function call*" OR "control loop" OR "context management" OR memory OR sandbox OR verification OR retry OR planning`

Per-source translation (details and rationale in `scripts/harvest/README.md`):

* **arXiv**: `(ti:"agent harness" OR abs:"agent harness" OR ti:harness OR abs:harness OR ti:"agent scaffold" OR abs:"agent scaffold" OR ... OR ti:"LLM agent" OR abs:"LLM agent" OR ... OR ti:"LLM orchestration" OR abs:"LLM orchestration") AND (ti:"large language model" OR abs:"large language model" OR ti:LLM OR abs:LLM OR ti:"foundation model" OR abs:"foundation model" OR ti:"language model agent" OR abs:"language model agent") AND (cat:cs.AI OR cat:cs.CL OR cat:cs.SE OR cat:cs.LG) AND submittedDate:[<slice start>0000 TO <slice end>2359]`. Wildcard terms sent as their stem (arXiv stems). The window was split into 8 submittedDate slices (≤ 2,000 results each) because the API cannot page past 10,000 results: 2022-10-01..2024-09-15 (1,329), 2024-09-16..2025-03-13 (1,064), 2025-03-14..2025-09-08 (1,818), 2025-09-09..2025-12-07 (1,281), 2025-12-07..2026-02-11 (991), 2026-02-12..2026-04-19 (1,321), 2026-04-20..2026-06-25 (1,903), 2026-06-26..2026-08-31 (1,544). Slices sum to 11,251 (2025-12-07 belongs to two slices; the writer skips duplicate ids) and the file holds exactly the 11,242 the API reports for the whole window.
* **Semantic Scholar** (`/graph/v1/paper/search/bulk`, `fieldsOfStudy=Computer Science`, `publicationDateOrYear=2022-10-01:2026-08-31`, `sort=citationCount:desc`): `("agent harness" | harness | "agent scaffold" | "agent scaffolding" | "agent scaffolds" | "agentic framework" | "agent framework" | "LLM agent" | "LLM agents" | "LM agent" | "LM agents" | "language agent" | "language agents" | "AI agent" | "AI agents" | "computer agent" | "computer agents" | "multi-agent" | "tool-use agent" | "coding agent" | "software engineering agent" | "computer-use agent" | "GUI agent" | "web agent" | "multi-agent framework" | "agent orchestration" | "LLM orchestration") + ("large language model" | "large language models" | LLM | LLMs | "foundation model" | "foundation models" | "language model agent") + ("tool call" | "tool calls" | "tool calling" | "function call" | "function calls" | "function calling" | "control loop" | "context management" | memory | sandbox | verification | retry | planning)`
* **OpenAlex** (`/works`, `mailto`, cursor pagination 200/page, `sort=cited_by_count:desc`): `filter=from_publication_date:2022-10-01,to_publication_date:2026-08-31,concepts.id:C41008148,title_and_abstract.search:("agent harness" OR harness OR "agent scaffold" OR "agentic framework" OR "agent framework" OR "LLM agent" OR "LM agent" OR "language agent" OR "AI agent" OR "computer agent" OR "multi-agent" OR "tool-use agent" OR "coding agent" OR "software engineering agent" OR "computer-use agent" OR "GUI agent" OR "web agent" OR "multi-agent framework" OR "agent orchestration" OR "LLM orchestration") AND ("large language model" OR LLM OR "foundation model" OR "language model agent") AND ("tool call" OR "function call" OR "control loop" OR "context management" OR memory OR sandbox OR verification OR retry OR planning)`
* **OpenReview / ACL Anthology**: local case-insensitive regexes (`common.HARNESS_RE` AND `common.LLM_RE`) on title + abstract; no structure block.
* **GitHub**: unchanged from the test run (topic + keyword queries, `stars:>500 created:2022-10-01..2026-08-31`, README/description filtered on the LLM regex); the protocol blocks are not GitHub queries. Same 1,361 repositories as the test run.

## 3. Per-source counts

| source | server hits (harness AND LLM) | with structure block | records written | capped | status |
|---|---:|---:|---:|---|---|
| arXiv | 11,242 (harness only 19,900; LLM only 86,299) | n/a | **11,242** | no | complete after 4 attempts (see failures) |
| Semantic Scholar | 20,019 | 6,744 | **6,744** | no | ok |
| OpenAlex (title+abstract, CS concept) | 40,607 (full-text `search=`: 128,906) | 14,812 | **8,200** | no (budget-truncated) | **partial, 55%** — daily API budget exhausted; ordered by `cited_by_count desc`, so the 6,612 missing works all have `cited_by_count = 0` (the minimum in the written file is 0) |
| OpenReview | 70,268 submissions scanned | n/a | **1,686** | no | ok (ICLR 2023 1 / 2024 68 / 2025 254 / 2026 823; NeurIPS 2023 11 / 2024 51 / 2025 101; ICML 2023 1 / 2024 25 / 2025 58 / 2026 293) |
| ACL Anthology | 1,363 (harness only 1,702; LLM only 21,654; 50,461 entries in 2022–2026 of 131,040) | n/a | **1,363** | no | ok |
| GitHub | 3,228 search hits → 2,555 unique repos → 1,361 LLM-matching | n/a | **1,361** | no | ok (5 repos without README) |
| **six search sources** | | | **30,596** | | |
| snowball (S2, 11 seeds) | 13,269 listed | n/a | **11,289** (date-filtered) | ReAct citations at S2 ceiling | ok |
| awesome-lists (3 lists) | 825 entries parsed | n/a | **822** | no | ok |
| **all raw files** | | | **42,707** | | |

Year distribution of written records (arXiv / S2 / OpenAlex / OpenReview / ACL / GitHub): 2022: 7/2/2/0/0/6 · 2023: 397/147/146/60/20/129 · 2024: 1,513/599/656/273/175/166 · 2025: 3,825/2,078/2,591/853/570/416 · 2026: 5,500/3,918/4,805/500/598/644.

Test-run comparison (v1 block, 5,000 cap): arXiv 4,030 → 11,242 (2.8×); S2 7,570 hits → 20,019 (with structure block 6,744 harvested); OpenAlex 15,994 → 40,607 (with structure block 14,812); ACL 420 → 1,363; OpenReview 483 → 1,686; GitHub 1,361 → 1,361.

### Structure block usage

Applied only on S2 and OpenAlex (`--with-structure-block`), as instructed. Effect: S2 20,019 → 6,744 (−66%), OpenAlex 40,607 → 14,812 (−64%). Both scripts record both counts in their `SUMMARY`. Recall cost measured on S2: a diagnostic S2 harvest **without** the structure block (20,018 records, written to the scratchpad, not to `data/raw/`) finds 29/48 known items vs 20/48 with it; the 9 items lost on S2 are all also in the arXiv file, so the union recall is unchanged. Re-running S2 without the block is one command (12 s) if the orchestrator prefers volume over precision there.

## 4. Known-item set and recall

`data/raw/known_items.txt`: **48 arXiv ids** = every `eprint` in `paper/references/must_cite.bib` (48 unique; the 12 test-run ids are all among them). Matching: normalised arXiv id, else normalised exact title (used for OpenReview/ACL/awesome records without an arXiv id).

Recall **before snowballing** (six search sources): arXiv 30/48, S2 20/48, OpenAlex 11/48, OpenReview 6/48, ACL 0/48, GitHub 0/48 (n/a: repositories) — **union 31/48 = 65%**.

Recall **after snowballing** (+ `snowball.jsonl` 37/48, + `awesome.jsonl` 20/48): **union 42/48 = 88%**.

Missing after search only (17): 2607.10113 2607.22585 2608.26218 2609.17394 2605.29682 2606.17454 2606.12344 2603.10044 2606.25514 2608.10178 2302.04761 2305.10601 2310.06770 2404.07972 2307.13854 2311.12983 2406.12045.

Missing after snowball (6): **2607.10113 2607.22585 2608.26218 2609.17394 2606.17454 2603.10044**.

Diagnosis of the 17 search misses (arXiv metadata fetched by `id_list`, blocks tested with `common.HARNESS_RE` / `LLM_RE`; all 17 are in cs.AI/CL/SE/LG):

| cause | ids | note |
|---|---|---|
| **harness block matches, LLM block does not** (abstract says "harness", "coding agent", "multi-agent", "AI agent" but never "large language model", "LLM", "foundation model" or "language model agent") | 2608.26218, 2606.17454, 2606.12344, 2607.22585, 2605.29682, 2606.25514, 2608.10178, 2603.10044 (8) | This is the binding constraint on the 2026 harness literature: the papers this review is about increasingly write "model"/"agent" without the LLM vocabulary. Candidate amendment for the protocol owner: relax the LLM block for records that match a *strong* harness term (`"agent harness"`, `harness` AND `agent*`, `"agent scaffold*"`, `"coding agent"`) — or drop the LLM block entirely on arXiv where the category filter already restricts the domain. Not applied. |
| LLM block matches, harness block does not | 2607.10113 (Dynamic Agent Skills lifecycle survey) | abstract has "large language model" and "verification" but no phrase from the harness block (it says "agent skills", not "LLM agent"/"AI agent"). Still missing after snowball. |
| neither block (pre-harness classics: SWE-bench, Toolformer, ToT, OSWorld, WebArena, GAIA, τ-bench) | 2310.06770, 2302.04761, 2305.10601, 2404.07972, 2307.13854, 2311.12983, 2406.12045 (7) | expected; **all 7 recovered** by the snowball/awesome files (none is in the missing-after-snowball list). Of the 8 "harness-but-not-LLM" papers, 4 were also recovered that way (2605.29682, 2606.12344, 2606.25514, 2608.10178); the other 4 plus 2607.10113 and the out-of-window 2609.17394 remain missing. |
| outside the date window | 2609.17394 (submitted 2026-09-15) | cannot be found by any search with `--until 2026-08-31`; must be added by hand if kept in the bib. |

ReAct (2210.03629) is found by OpenAlex (id) and by the snowball file; it is not in the arXiv file (abstract never says "agent"), as predicted in the protocol.

## 5. Snowball seed table (S2, `data/raw/snowball.jsonl`, `query_used = snowball:<citations|references>:<seed>`)

| seed | S2 id | references found | citers found | note |
|---|---|---:|---:|---|
| 2606.20683 (QA → task completion survey) | ARXIV:2606.20683 | 222 | 5 | |
| 2604.03515 (Inside the Scaffold) | ARXIV:2604.03515 | 40 | 13 | |
| 2605.12239 (Harness Engineering as Categorical Architecture) | ARXIV:2605.12239 | 8 | 0 | |
| 2609.00006 (Barbaste et al., Harness Engineering anatomy) | ARXIV:2609.00006 | 0 | 1 | S2 lists no references yet |
| 2605.13357 (AI Harness Engineering runtime substrate) | ARXIV:2605.13357 | 12 | 12 | |
| 2605.27922 (Harness-Bench) | ARXIV:2605.27922 | 19 | 25 | |
| 2607.22585 (Scaffold Effect) | ARXIV:2607.22585 | 7 | 3 | |
| 2608.26218 (Same Model, Different Harness) | ARXIV:2608.26218 | 3 | 1 | |
| 2405.15793 (SWE-agent) | ARXIV:2405.15793 | 0 | 1,784 | S2 lists no references for this paper |
| 2407.16741 (OpenHands) | ARXIV:2407.16741 | 50 | 1,025 | |
| 2210.03629 (ReAct) | ARXIV:2210.03629 | 40 | 9,999 | **truncated**: S2 exposes at most 9,999 citations per paper (`offset + limit must be < 10000`); the paper has far more citers. Flagged in the summary as `citations_truncated_at_s2_ceiling`. |
| "Agent Harness Engineering: A Survey" (OpenReview eONq7FdiHa) | — | — | — | **not indexed by S2** (`/paper/search/match` 404 and the relevance search returns unrelated papers) |
| "Agent Harness for Large Language Model Agents: A Survey" (Preprints.org 202604.0428) | — | — | — | **not indexed by S2** (same check) |

Totals: 13,269 records listed by S2 (11 seeds × 2 directions), 11,289 within the date window and written (11,024 citations + 265 references; 11,289 unique S2 paperIds — a paper reached through several seeds is written once, under the first seed/direction). The two surveys' bibliographies are therefore *not* in the snowball set; their companion catalogs are covered by the awesome-list harvest (next section), which is the only machine-readable form of them.

## 6. Awesome-lists (`data/raw/awesome.jsonl`, `source = awesome`, `query_used = awesome-list:<list>:<url>`)

| list | file fetched | entries parsed | written | papers (arXiv id) | GitHub repos | other links |
|---|---|---:|---:|---:|---:|---:|
| picrew (Agent Harness Engineering: A Survey) | `https://raw.githubusercontent.com/picrew/LLM-Harness/main/projects.yaml` → **404**; the picrew/LLM-Harness README points to the catalog repo `Picrew/awesome-agent-harness`, whose git tree (GitHub API) contains `data/projects.yaml` (240 KB, `last_verified: 2026-09-14`) → fetched `https://raw.githubusercontent.com/Picrew/awesome-agent-harness/main/data/projects.yaml` | 368 | 368 | 0 | 334 | 34 (blogs/docs) |
| Gloriaameng/Awesome-Agent-Harness (`README.md`) | `https://raw.githubusercontent.com/Gloriaameng/Awesome-Agent-Harness/main/README.md` | 160 | 158 | 118 | 14 | 26 |
| ggjy/Awesome-Agent-Engineering (`README.md`) | `https://raw.githubusercontent.com/ggjy/Awesome-Agent-Engineering/main/README.md` | 297 | 296 | 270 | 13 | 13 |
| **total** | | 825 | **822** | 388 | 361 | 73 |

(3 entries were duplicates of an earlier entry within the same list — same URL — and were skipped.) Repository entries carry `title = owner/repo` so they merge with `github.jsonl` in `dedupe.py`; paper entries carry `arxiv_id`. Awesome-list entries are seed material and were not filtered by date or by the protocol blocks.

## 7. Failures, caps and workarounds

1. **OpenAlex partial (8,200 / 14,812).** Since 2026 the free OpenAlex API has a daily spending budget; at 19:49 UTC every request began returning `HTTP 429 {"error":"Rate limit exceeded","message":"Insufficient budget. This request costs $0.001 but you only have $0 remaining. Resets at midnight UTC ..."}` with `Retry-After` ≈ 4 h. The test run, the count-only calls and 41 pages of the harvest consumed the day's budget (boolean queries cost 10 credits each; the daily limit reads `X-RateLimit-Limit: 1000`). The client retried 8 times (2 min each) and aborted at 20:03 UTC; the 8,200 records written are the top of the `cited_by_count desc` order, i.e. the file is effectively a citation-ordered cap and everything missing has 0 citations. The running process predates the checkpoint code, so no cursor was saved. **To complete after 00:00 UTC on 2026-09-17**: re-run the OpenAlex command from section 1 unchanged (it truncates and refetches: 3 count requests + 75 pages ≈ 78 requests, within one day's budget if nothing else hits OpenAlex that day). `openalex.py` now writes `<out>.cursor.json` after every page and `--resume` continues from it in append mode, so a second budget interruption no longer loses the run. The `SUMMARY` of the aborted run says `written: 0` — a reporting bug (the exception escaped before `written` was set), fixed in `openalex.py` and `s2.py`; the file really holds 8,200 unique records.
2. **arXiv deep paging.** The arXiv API answers HTTP 500/503 (and empty pages) for `start >= 10000`; attempt 1 died at exactly 10,000 of 11,242. Fixed by recursive submittedDate slicing (`--slice-max`, default 2,000). Attempt 2 was then stopped by a burst of HTTP 429 (arXiv rate limiting despite 3 s pacing; 6 retries exhausted at 2 s-base backoff). Fixed by raising the retry budget (8 retries, 10 s base) and adding `--resume` (append mode, skip ids already present); attempts 3 and 4 completed the file. The final file has 11,242 unique records = the API's count for the whole window; the 4 `SUMMARY` lines are in the scratchpad logs, the union is what matters.
3. **S2 snowball ceiling.** `/paper/{id}/citations` rejects `offset + limit >= 10000`; ReAct has more citers than that. `_paginated` now stops at 9,999 and marks the seed `citations_truncated_at_s2_ceiling`. ReAct's citers are not a harness-specific set anyway; the 9,999 retrieved are S2's default ordering.
4. **Two seed surveys not on S2.** Neither *Agent Harness Engineering: A Survey* nor *Agent Harness for Large Language Model Agents: A Survey* is indexed by Semantic Scholar (OpenReview-only and Preprints.org-only). Their reference lists could be added manually from the PDFs if wanted; their catalogs are in `awesome.jsonl`.
5. **picrew `projects.yaml` 404** — resolved via the GitHub API as described in section 6; `awesome_lists.py` does this automatically.
6. **2609.17394** is dated after the window end and cannot be found by the frozen search.
7. No caps were applied (`--max-records 0` everywhere). No source exceeded 60,000 records (largest server count: OpenAlex 40,607 without the structure block; harvested with it: 14,812).
8. `data/raw/grey.jsonl` and `data/raw/leaderboards.jsonl` (and `scripts/harvest/grey.py`, `README_grey.md`) appeared at 20:08 UTC while this run was in progress; they were produced by another task, not by this one, and were **not** included in `data/raw/frozen/` (their gz copies were removed again) nor in the counts above. `dedupe.py` will pick them up from `data/raw/` unless excluded.

## 8. Frozen copies (`data/raw/frozen/`, gzip -9; originals left in place for `dedupe.py`)

| file | records | raw size | gz size |
|---|---:|---:|---:|
| arxiv.jsonl.gz | 11,242 | 36.66 MB | 7,506,121 B (7.51 MB) |
| s2.jsonl.gz | 6,744 | 20.54 MB | 4,874,979 B (4.87 MB) |
| openalex.jsonl.gz | 8,200 (partial) | 26.23 MB | 6,258,690 B (6.26 MB) |
| openreview.jsonl.gz | 1,686 | 4.49 MB | 1,140,558 B (1.14 MB) |
| acl.jsonl.gz | 1,363 | 3.30 MB | 755,577 B (0.76 MB) |
| github.jsonl.gz | 1,361 | 6.57 MB | 1,098,835 B (1.10 MB) |
| snowball.jsonl.gz | 11,289 | 24.32 MB | 7,293,773 B (7.29 MB) |
| awesome.jsonl.gz | 822 | 0.93 MB | 108,564 B (0.11 MB) |
| **total** | **42,707** | 123.0 MB | 29,037,097 B (29.0 MB) |

If OpenAlex is completed tomorrow, re-gzip `openalex.jsonl` into `frozen/` and update this table.

## 9. Code changes made for the freeze (all under `scripts/harvest/`, ruff-clean)

* `common.py`: `HARNESS_TERMS` = protocol v2 block; `STRUCTURE_RE`; `matches_blocks(text, with_structure=False)`; `build_parser(..., structure_block=True)` adds `--with-structure-block`; `DEFAULT_MAX_RECORDS = 0`; `expand_wildcards` handles `agent*` (agent/agents) and `call*` (call/calls/calling); `JsonlWriter(append=True)` (loads existing ids, appends).
* `arxiv.py`: recursive submittedDate slicing (`--slice-max`), `--resume`, 8 retries with 10 s base backoff, `slices` in the summary.
* `s2.py`: `--with-structure-block`; both counts always recorded; `--snowball-title` (S2 `/paper/search/match`); per-seed stats and truncation flag in the summary; S2 offset ceiling handled; partial `written` reported on failure.
* `openalex.py`: `--with-structure-block` (three counts recorded: title+abstract, full text, title+abstract+structure); cursor checkpoint `<out>.cursor.json` + `--resume`; partial `written` reported on failure.
* new `awesome_lists.py` (section 6) and `known_items.py` (section 4).
* `README.md`: v2 blocks, per-source translation table incl. the structure block, freeze-run command list, new scripts, `--resume` notes.
* Data: `data/raw/known_items.txt` (48 ids with bibkey and title), `data/raw/snowball.jsonl`, `data/raw/awesome.jsonl`, `data/raw/frozen/*.jsonl.gz`.

## 10. v3 measurement — waiving the LLM block on strong harness terms (2026-09-16, 20:18–20:45 UTC)

**Not applied to any canonical file.** Requested by the coordinator after section 4 showed that 8 of
the 17 search misses match the harness block but not the LLM block. Proposal v3: the LLM block is
waived when the record contains a *strong* harness term — `"agent harness*"`, `"agentic harness*"`,
`"coding agent*"`, `"agent scaffold*"`, `"agentic scaffold*"`, `"software engineering agent*"`,
`"computer-use agent*"`, `"GUI agent*"`, `"web agent*"` (not bare `harness`, not `multi-agent` /
`AI agent*` / `LLM agent*`). Implemented as `common.STRONG_TERMS` / `STRONG_RE` and the flag
`--waive-llm-on-strong` (default off): local filter `(HARNESS and LLM) or STRONG`; arXiv query
`((H AND L) OR S) AND cats AND dates`. Outputs went to `data/raw/{arxiv,acl,openreview}_v3.jsonl`.

### Runs and deltas

| source | v2 (canonical) | v3 | added | lost | how |
|---|---:|---:|---:|---:|---|
| arXiv | 11,242 | **12,205** (= server count for `both_or_strong`) | **+963** (+8.6%) | 0 | strong-only query alone: 2,060 hits, 1,097 already in arxiv.jsonl. `python scripts/harvest/arxiv.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --waive-llm-on-strong --out data/raw/arxiv_v3.jsonl` (20:19–20:33 UTC) reached 3,247 records and died on arXiv rate limiting (`HTTP 429 'Rate exceeded'` after 8 retries, 9 × 429; partial kept in the scratchpad). Because arxiv.jsonl already holds the complete `both` set (11,242 = server total), `arxiv_v3.jsonl` was built as arxiv.jsonl ∪ strong-only results (strong query fetched 20:34–20:40 UTC, 16 requests, 2,060/2,060; union deduplicated by id; added records carry the strong query in `query_used`). Check: union size 12,205 = the server's `both_or_strong` count, so the file is identical in content to what the flag run would have produced. |
| ACL Anthology | 1,363 | 1,432 | **+69** (+5.1%) | 0 | `python scripts/harvest/acl.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --waive-llm-on-strong --out data/raw/acl_v3.jsonl` (20:20 UTC; 162 entries match STRONG, 69 of them not the LLM block). Added: almost entirely GUI/web/mobile-agent papers that say "VLM"/"multimodal"/"vision-language" instead of "LLM" (SeeClick, OS-Genesis, AssistantBench, WebOlympus, Beyond Browsing, CowPilot, ...), plus a few coding/SE-agent papers (CTIM-Rover, CodeScout, EGSS, ParaCodex). |
| OpenReview | 1,686 | 1,837 | **+151** (+9.0%) | 0 | `python scripts/harvest/openreview.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --waive-llm-on-strong --out data/raw/openreview_v3.jsonl` (20:19–20:21 UTC, 80 requests). strong_added per venue: ICLR 2025 17, 2026 89; NeurIPS 2025 8; ICML 2025 3, 2026 34; 0 elsewhere. Same profile as ACL (AndroidWorld, Aguvis, OmniParser, WebCanvas, ST-WebAgentBench, AgentTrek, MLE-bench, ...). |
| GitHub | 1,361 | — | **not measured** | | `github.py` accepts the flag, but the freeze run kept only the 1,500-char README excerpt of the 1,361 *kept* repos; the full READMEs of the 1,194 rejected repos were not cached, so re-running needs the 2,555 README fetches again (~20 min of `gh api`). Skipped as instructed. |
| S2, OpenAlex | 6,744 / 14,812 | — | not touched | | flag ignored by these scripts (server-side queries with the structure block). |
| **three sources** | **14,291** | **15,474** | **+1,183** | 0 | |

### Known-item recall (48 ids), v2 vs v3, same snowball and awesome files

| configuration | arXiv | ACL | OpenReview | S2 | OpenAlex | GitHub | union (search only) | + snowball + awesome |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v2 (canonical files) | 30 | 0 | 6 | 20 | 18 | 0 | **31/48 = 65%** | **42/48 = 88%** |
| v3 (`*_v3` in place of arXiv/ACL/OpenReview) | **38** | 0 | 6 | 20 | 18 | 0 | **39/48 = 81%** | **46/48 = 96%** |

v3 recovers exactly the 8 "harness-but-not-LLM" items on arXiv: 2607.22585, 2608.26218,
2605.29682, 2606.17454, 2606.12344, 2603.10044, 2606.25514, 2608.10178. Still missing after v3
search: the 7 pre-harness classics (2302.04761, 2305.10601, 2310.06770, 2404.07972, 2307.13854,
2311.12983, 2406.12045 — all recovered by snowball/awesome), 2607.10113 (no strong term:
"agent skills") and 2609.17394 (outside the window). Missing after v3 + snowball + awesome (2):
**2607.10113, 2609.17394**. (OpenAlex shows 18 here instead of the 11 in section 4 because
`openalex.jsonl` was completed to 14,812 records at 20:19–20:21 UTC by another task — see the
note at the end of this section; the v2 union figures are unchanged, 31 and 42.)

### Precision of the waiver: 40 random added arXiv records (seed 20260916, `random.sample` of the 963 added ids)

Labels from title + abstract. *Relevant* = the paper is about the system around the model
(architecture, control loop, tools/skills, memory, sandbox/environment, verification, harness
comparison); *maybe* = agent benchmark/behaviour study or a partly-harness component; *irrelevant* =
model training, grounding, reward modelling, capability evaluation, position papers without harness content.

| # | arXiv id | title (short) | strong term | label |
|---|---|---|---|---|
| 1 | 2602.05429 | M²-Miner: multi-agent MCTS for mobile GUI agent data mining | GUI agent | maybe (data-mining pipeline for training data) |
| 2 | 2608.23564 | SWE Refactor Bench: long-horizon repo migration for coding agents | coding agents | maybe (benchmark; agentic verification stage) |
| 3 | 2601.21352 | BEAP-Agent: backtrackable execution and adaptive planning for GUI agents | GUI agents | **relevant** (planner/executor/tracker framework, backtracking control loop) |
| 4 | 2606.02540 | SkillHarm: lifecycle-aware skill-based attacks | coding agents | maybe (security of the skills layer) |
| 5 | 2607.26587 | One Run Is Not an Idea: implementation lottery in automated research | coding-agent | irrelevant (evaluation methodology for automated research) |
| 6 | 2505.12370 | Visual grounding for GUI agents via self-evolutionary RL | GUI agent | irrelevant (model training) |
| 7 | 2602.11524 | Adaptive Milestone Reward for GUI agents | GUI agents | irrelevant (RL reward design) |
| 8 | 2608.06144 | FinEvo-Bench: longitudinal benchmark for self-evolving agents | agent scaffolds | maybe (compares four scaffolds on one backbone) |
| 9 | 2606.05525 | SciVisAgentSkills: agent skills for SciVis coding agents (Codex, Claude Code) | agent harness, coding agents | **relevant** (skills as harness components, harness-dependent results) |
| 10 | 2604.23190 | RAT: RunAnyThing, automated environment configuration agent framework | "code agents" (server-side stem match; `STRONG_RE` = none) | **relevant** (modular framework, toolset, sandbox) |
| 11 | 2607.04334 | Do GUI agents believe their eyes? pixels vs structure | GUI agents | maybe (observation-channel design, measured as model behaviour) |
| 12 | 2505.15810 | GUI-G1: R1-Zero-like training for GUI grounding | GUI agents | irrelevant (training) |
| 13 | 2510.26098 | GUI Knowledge Bench: knowledge gap of VLMs | GUI agents | irrelevant (model knowledge benchmark) |
| 14 | 2603.17441 | AdaZoom-GUI: adaptive zoom grounding with instruction refinement | GUI agent | maybe (inference-time pipeline around a VLM) |
| 15 | 2605.16565 | Skim: speculative execution for web agents | web agents | **relevant** (runtime framework: profiler, template matching, verifier, fallback) |
| 16 | 2602.06310 | Trustworthy AI Software Engineers (vision paper) | coding agents | irrelevant (conceptual, no harness content) |
| 17 | 2603.25723 | Natural-Language Agent Harnesses | agent harness | **relevant** (harness as executable NL document + runtime) |
| 18 | 2603.10178 | Video-based reward modeling for computer-use agents | computer-use agents | irrelevant (reward model training) |
| 19 | 2604.25067 | Frontier coding agents implement an AlphaZero pipeline | coding agents | irrelevant (capability evaluation) |
| 20 | 2601.04203 | FronTalk: conversational front-end code generation benchmark | web agent | irrelevant (web agent only as evaluation tool) |
| 21 | 2604.00299 | Code proficiency of AI-agent Python code in the wild | coding agents | irrelevant (code analysis of agent PRs) |
| 22 | 2603.04364 | DMAST: adversarial safety training for multimodal web agents | web agents | irrelevant (training) |
| 23 | 2604.09408 | HiL-Bench: do agents know when to ask for help? | coding agents | maybe (escalation-policy benchmark) |
| 24 | 2608.12355 | Humans are missing from AI coding agent research | coding agent | maybe (position paper on verifiability/steerability of coding agents) |
| 25 | 2607.02703 | LLMoxie: institutional platform for agentic scientific software development | coding agents | **relevant** (control plane, plugin/agent/skill hierarchy around coding agents) |
| 26 | 2607.22807 | Coding agent behaviour and token cost across programming languages | coding agents | maybe (trajectory/cost analysis) |
| 27 | 2605.16883 | SE-GA: memory-augmented self-evolution for GUI agents | GUI agents | **relevant** (hierarchical test-time memory retrieval) |
| 28 | 2606.29537 | OSWorld 2.0 benchmark | computer use agents | maybe (benchmark; outcomes-table relevance) |
| 29 | 2604.05477 | VeriGUI: action-effect verification and self-correction | GUI agents | maybe (verification loop, delivered by training) |
| 30 | 2602.16855 | Mobile-Agent-v3.5 / GUI-Owl-1.5 model release | GUI agents | irrelevant (model) |
| 31 | 2605.11212 | ReVision: temporal visual redundancy reduction for CUAs | computer-use agents | irrelevant (token pruning / training) |
| 32 | 2509.19783 | Agentic metacognition: self-aware low-code agent with human handoff | server-side stem match only (`STRONG_RE` = none) | **relevant** (monitoring layer, failure prediction, handoff pattern) |
| 33 | 2605.26546 | MobileExplorer: on-device inference acceleration via online exploration | GUI agents | **relevant** (runtime framework with structured memory around a VLM) |
| 34 | 2602.14093 | GUI-GENESIS: synthesized training environments with verifiable rewards | GUI agent | maybe (environment synthesis, training-oriented) |
| 35 | 2605.24785 | PANDO: online skill distillation for multimodal web agents | web agents | **relevant** (skill library, reflection, routing, cache-aware prompting at runtime) |
| 36 | 2604.13108 | Formal architecture descriptors as navigation primitives for coding agents | coding agents | **relevant** (context supplied to Claude Code; tool-call reduction) |
| 37 | 2508.13634 | V2P: visual attention calibration for GUI grounding | GUI agents | irrelevant (grounding model) |
| 38 | 2605.28775 | LearnWeak: automated domain specialization for small CUAs | computer-use agents | irrelevant (training) |
| 39 | 2410.00689 | Multimodal auto-validation for self-refinement in web agents (Agent-E) | web agents | **relevant** (validator + self-refinement loop in a web-agent framework) |
| 40 | 2608.02685 | BulkPR-Bench: queue-level governance of interacting PRs | coding-agent | maybe (benchmark) |

(Items 10 and 32 show no `STRONG_RE` hit because their strong term appears only in a form arXiv's
stemmer matches — "code agents", stemmed "agentic" — so the server-side query is slightly broader
than the local regex; both happen to be relevant.)

**Tally: 12 relevant, 13 maybe, 15 irrelevant** → precision of the waiver on arXiv ≈ **30%
clearly relevant (Wilson 95% CI 18–46%)**, **62% relevant-or-maybe**, **38% clearly irrelevant**.
The noise is dominated by GUI/CUA *model-training* papers (grounding, RL, reward models: 10 of the
15 irrelevant) that write "GUI agent"/"computer-use agent" without "LLM". The "agent harness*",
"agent scaffold*" and "software engineering agent*" terms contributed only relevant or maybe
records in the sample; "coding agent*" is mixed; "GUI agent*"/"computer-use agent*" is where the
precision loss is. No precision sample of the v2 harvest itself was taken, so this is an absolute,
not a relative, figure.

### Summary for the decision

* Cost: +963 arXiv (+8.6%), +69 ACL (+5.1%), +151 OpenReview (+9.0%); GitHub unmeasured (needs
  ~20 min of README refetching); S2/OpenAlex unaffected (their server-side queries would need an
  equivalent `| strong` clause — expect a similar +5–10%).
* Benefit: known-item recall 31 → 39 of 48 on search alone (65% → 81%), 42 → 46 with snowballing
  (88% → 96%); every one of the 8 harness-papers-without-LLM-vocabulary is recovered; the two
  remaining misses cannot be fixed by vocabulary (2607.10113 says "agent skills", 2609.17394 is
  outside the window).
* Precision of the added records: ~30% clearly relevant, ~62% relevant-or-maybe. A narrower v3'
  that drops `"GUI agent*"` and `"computer-use agent*"` from the strong list would keep all 8
  recovered known items (they match on harness / coding-agent / scaffold terms) and remove most
  of the sampled noise; it was not measured.

### Note: OpenAlex became complete during this measurement

`data/raw/openalex.jsonl` was rewritten between 20:19 and 20:21 UTC — not by this task — and now
holds **14,812 records = the full `title_abstract_structure` count** (same query string, structure
block on, min `cited_by_count` 0, 14,812 unique ids). Sections 3, 7 and 8 above describe the
8,200-record partial file as it stood at 20:13 UTC. The frozen copy
`data/raw/frozen/openalex.jsonl.gz` was refreshed from the complete file at 20:45 UTC
(11,184,188 bytes); the frozen total is now 34,253,655 bytes for 49,319 records (six sources
37,208 + snowball 11,289 + awesome 822). The v2 known-item union is unchanged by the completion
(OpenAlex alone 11 → 18; union still 31 search-only / 42 with snowball).

Scratch files left in place for the orchestrator (delete or exclude before `dedupe.py`, which
would otherwise merge them): `data/raw/arxiv_v3.jsonl` (12,205), `data/raw/acl_v3.jsonl` (1,432),
`data/raw/openreview_v3.jsonl` (1,837). No `*_v3` file was gzipped into `frozen/`.

## 11. Decision: v3' adopted (orchestrator, 2026-09-16 ~20:50 UTC)

LLM block waived only for 7 strong terms: "agent harness*", "agentic harness*", "coding agent*", "agent scaffold*", "agentic scaffold*", "software engineering agent*", "web agent*" (dropped "GUI agent*" and "computer-use agent*", which carried most sampled noise). Added records appended to canonical arxiv/acl/openreview files with query_used suffix ' | v3prime strong-term waiver': arxiv +593, acl +30, openreview +68. GitHub not re-filtered (no README cache; noted limitation). S2/OpenAlex unchanged (structure block).
