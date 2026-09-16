# Search log — HARNESS-Review

Protocol task: "draft and test search strings; record hit counts" (plan section 3.1, protocol
sections 5–6). **This is the test run. The search is not frozen.** Every count below was
produced by the scripts in `scripts/harvest/` and `scripts/dedupe.py`; nothing is estimated.

## Run 1 — 2026-09-16 (test run)

* Start / end: 2026-09-16 18:26 UTC → 2026-09-16 18:55 UTC (local 14:26 → 14:55 EDT).
* Date window: 2022-10-01 → 2026-08-31 (inclusive) on every source.
* Cap: 5000 records per source (`--max-records 5000`); capped sources are fetched in
  citation-count order so the cap keeps the most-cited works. Lifting the cap
  (`--max-records 0`) is a one-line change for the freeze run.
* No API keys; unauthenticated rate limits respected (arXiv 3 s/request, S2 1 request/s,
  OpenAlex polite pool, GitHub via `gh` 30 search requests/min).

### Protocol blocks as issued

Harness block: `"agent harness" OR "agent scaffold*" OR "agentic framework" OR "agent framework" OR "tool-use agent" OR "coding agent" OR "software engineering agent" OR "computer-use agent" OR "GUI agent" OR "web agent" OR "multi-agent framework" OR "orchestration"`

LLM block: `"large language model" OR LLM OR "foundation model" OR "language model agent"`

Structure block: not applied (optional, precision only).

Translation decisions (per-source syntax only; the protocol strings were not changed):

| decision | why |
|---|---|
| `agent scaffold*` issued as `"agent scaffold"` on arXiv and OpenAlex | both stem server-side; verified on arXiv that `"agent scaffold*"`, `"agent scaffold"` and `"agent scaffold" OR "agent scaffolding"` all return 95 hits |
| `agent scaffold*` issued as `"agent scaffold" \| "agent scaffolding" \| "agent scaffolds"` on S2; plurals `"large language models"`, `LLMs`, `"foundation models"` added on S2 | S2 bulk search has no phrase-internal wildcard and does not stem phrases |
| arXiv: every term searched as `ti:` OR `abs:` | `all:` also matches comments/journal-ref; count was near-identical (4045 vs 4030) |
| arXiv: `cat:cs.LG` included in the category filter | protocol says "LG only with the harness block"; since both blocks are ANDed in every query this is equivalent |
| OpenAlex: `title_and_abstract.search` filter (not `search=`) used for the harvest | `search=` also matches OpenAlex full text and returns 53,099 works, 3.3× more, almost all off-topic mentions of "orchestration" |
| ACL Anthology and OpenReview: local case-insensitive regex on title + abstract (`common.HARNESS_RE`, `common.LLM_RE`) | no query API; hyphen/space variants and trailing plurals tolerated |
| GitHub: README/description filtered on the LLM block regex only | per plan section 3.1 ("then README keyword filter") |

### Exact queries per source

**arXiv** (`scripts/harvest/arxiv.py`, `http://export.arxiv.org/api/query`, 200/page, sortBy=submittedDate)

```
(ti:"agent harness" OR abs:"agent harness" OR ti:"agent scaffold" OR abs:"agent scaffold" OR ti:"agentic framework" OR abs:"agentic framework" OR ti:"agent framework" OR abs:"agent framework" OR ti:"tool-use agent" OR abs:"tool-use agent" OR ti:"coding agent" OR abs:"coding agent" OR ti:"software engineering agent" OR abs:"software engineering agent" OR ti:"computer-use agent" OR abs:"computer-use agent" OR ti:"GUI agent" OR abs:"GUI agent" OR ti:"web agent" OR abs:"web agent" OR ti:"multi-agent framework" OR abs:"multi-agent framework" OR ti:orchestration OR abs:orchestration)
AND (ti:"large language model" OR abs:"large language model" OR ti:LLM OR abs:LLM OR ti:"foundation model" OR abs:"foundation model" OR ti:"language model agent" OR abs:"language model agent")
AND (cat:cs.AI OR cat:cs.CL OR cat:cs.SE OR cat:cs.LG)
AND submittedDate:[202210010000 TO 202608312359]
```

**Semantic Scholar** (`scripts/harvest/s2.py`, `/graph/v1/paper/search/bulk`, `fieldsOfStudy=Computer Science`, `publicationDateOrYear=2022-10-01:2026-08-31`, `sort=citationCount:desc`)

```
("agent harness" | "agent scaffold" | "agent scaffolding" | "agent scaffolds" | "agentic framework" | "agent framework" | "tool-use agent" | "coding agent" | "software engineering agent" | "computer-use agent" | "GUI agent" | "web agent" | "multi-agent framework" | orchestration)
+ ("large language model" | "large language models" | LLM | LLMs | "foundation model" | "foundation models" | "language model agent")
```

**OpenAlex** (`scripts/harvest/openalex.py`, `/works`, `mailto=gurrambhaskar.ai@gmail.com`, cursor pagination 200/page, `sort=cited_by_count:desc`)

```
filter=from_publication_date:2022-10-01,to_publication_date:2026-08-31,concepts.id:C41008148,
       title_and_abstract.search:("agent harness" OR "agent scaffold" OR "agentic framework" OR "agent framework" OR "tool-use agent" OR "coding agent" OR "software engineering agent" OR "computer-use agent" OR "GUI agent" OR "web agent" OR "multi-agent framework" OR orchestration) AND ("large language model" OR LLM OR "foundation model" OR "language model agent")
```

**OpenReview** (`scripts/harvest/openreview.py`): `GET /notes?invitation=<venue>/-/Submission` (v2) then `/-/Blind_Submission` (v1) for ICLR.cc/2023–2026/Conference, NeurIPS.cc/2023–2025/Conference, ICML.cc/2023–2026/Conference; local regex filter (harness AND LLM) on title + abstract.

**ACL Anthology** (`scripts/harvest/acl.py`): `https://aclanthology.org/anthology+abstracts.bib.gz` (42.4 MB, cached in `data/raw/cache/`), entries with `year` 2022–2026 (month-trimmed at the window ends when the month is given), local regex filter (harness AND LLM) on title + abstract.

**GitHub** (`scripts/harvest/github.py`, `gh api search/repositories`, then `gh api repos/{repo}/readme`): each of
`topic:llm-agent`, `topic:ai-agent`, `topic:coding-agent`, `topic:llm-agents`, `topic:agent-framework`,
`"agent harness" in:name,description,readme`, `"coding agent" in:name,description,readme`,
`"computer-use agent" in:name,description,readme`, `"browser agent" llm in:name,description,readme`
with `stars:>500 created:2022-10-01..2026-08-31`; slices over 1000 hits split by creation date; unique repos kept when README or description matches the LLM block regex.

### Raw hit counts per source

| source | query hits (server) | records written | capped? | status |
|---|---:|---:|---|---|
| arXiv | 4,030 | 4,030 | no | ok (24 requests, 0 retries) |
| Semantic Scholar | 7,570 | 5,000 | **yes** (top 5,000 by citation count) | ok (2 × 429 backoffs) |
| OpenAlex (title+abstract) | 15,994 | 5,000 | **yes** (top 5,000 by cited_by_count) | ok (11 × 429 backoffs; OpenAlex throttles boolean queries with >5 operators) |
| OpenAlex (`search=` full text, count only) | 53,099 | – | – | recorded for comparison, not harvested |
| OpenReview | – | 0 | – | **failed**: all 11 venues return `403 ChallengeRequiredError` (Cloudflare Turnstile) on api2 and api v1; plain `python-requests` UA gets nginx `429`. Needs an OpenReview login (`OPENREVIEW_USERNAME`/`OPENREVIEW_PASSWORD`) |
| ACL Anthology | 420 | 420 | no | ok (131,040 entries parsed; 50,461 in 2022–2026; 3,642 of those without abstract) |
| GitHub | 3,227 search hits → 2,554 unique repos | 1,361 | no | ok (2,605 `gh api` calls, 0 retries; 5 repos without README; 1,361 of 2,554 READMEs/descriptions match the LLM block) |

Per-block counts (each block alone, same category and date filter):

| source | harness block only | LLM block only | harness AND LLM |
|---|---:|---:|---:|
| arXiv | 6,527 | 86,299 | **4,030** |
| Semantic Scholar (CS) | 24,228 | – | **7,570** |
| OpenAlex (title+abstract, no CS filter) | 94,304 | – | 16,213 (16,025 with CS concept; 15,994 in the harvest run) |
| ACL Anthology (2022–2026) | 573 | 21,654 | **420** |

OpenAlex per-harness-term counts (each term AND the LLM block, title+abstract, 2022-10-01..2026-08-31):
"agent harness" 410 · "agent scaffold" 91 · "agentic framework" 5,434 · "agent framework" 5,434 (OpenAlex stems "agentic"→"agent", so these two are the same query) · "tool-use agent" 318 · "coding agent" 1,629 · "software engineering agent" 123 · "computer-use agent" 135 · "GUI agent" 268 · "web agent" 352 · "multi-agent framework" 2,541 · orchestration 8,863.

GitHub per-query totals (server `total_count`): topic:llm-agent 64 · topic:ai-agent 389 · topic:coding-agent 98 · topic:llm-agents 59 · topic:agent-framework 75 · "agent harness" 356 · "coding agent" 1,957 (split into 4 date slices to get past the 1,000-result cap) · "computer-use agent" 100 · "browser agent" llm 129 (sum 3,227; 2,554 unique).

Year distribution of harvested records (arXiv / S2 / OpenAlex / ACL): 2023: 63 / 85 / 96 / 3 · 2024: 350 / 542 / 615 / 43 · 2025: 1,423 / 2,173 / 3,184 / 161 · 2026: 2,194 / 2,200 / 1,105 / 213. No *paper* dated 2022 survived any query (the harness vocabulary post-dates ChatGPT-era agent work); the only 2022-dated candidates are 6 GitHub repositories created Oct–Dec 2022. GitHub records by creation year: 2022: 6 · 2023: 129 · 2024: 166 · 2025: 415 · 2026: 644 (from `candidates.csv`).

### Dedupe (`scripts/dedupe.py`: DOI → arXiv id → normalised title exact → rapidfuzz ratio ≥ 95)

| source | raw hits | after dedupe | unique to source |
|---|---:|---:|---:|
| arxiv | 4,030 | 3,991 | 788 |
| acl | 420 | 420 | 101 |
| openreview | 0 | 0 | 0 |
| s2 | 5,000 | 4,825 | 784 |
| openalex | 5,000 | 3,797 | 1,127 |
| github | 1,361 | 1,360 | 1,360 |
| **total** | **15,811** | **8,358** | |

Merge events: DOI 2,703 · arXiv id 5,335 · exact normalised title 7,167 · fuzzy title (ratio ≥ 95, window 50) 48. The 39 arXiv-internal and 1 GitHub-internal merges are same-title re-submissions / near-identical repo names. `after dedupe` = clusters the source contributes to; `unique to source` = clusters seen by that source only.

**Total candidates: 8,358 (6,998 papers + 1,360 repositories, before any screening; OpenReview contributed nothing)** → `data/raw/candidates.csv`.

### Known-item recall check (12 arXiv ids)

| arXiv id | paper | in candidates.csv? | harness-block terms present in title+abstract | LLM-block terms present |
|---|---|---|---|---|
| 2405.15793 | SWE-agent | **no** | none ("LM agents", "agent-computer interface") | "language model agents" |
| 2407.16741 | OpenHands | **no** | none ("AI agents", "generalist agents") | "large language models" |
| 2308.08155 | AutoGen | **no** | none ("multi-agent conversation framework") | LLM |
| 2308.00352 | MetaGPT | **no** | none ("multi-agent collaborative framework") | LLM |
| 2410.08164 | Agent S | yes (arxiv; s2; openalex) | "agentic framework", "GUI agents" | "large language models" |
| 2402.07456 | OS-Copilot | **no** | none ("computer agents", "generalist agents") | "large language models" |
| 2412.05467 | BrowserGym | yes (arxiv; s2; openalex) | "web agent" | "large language models" |
| 2210.03629 | ReAct | **no** | none (abstract never uses "agent") | "large language models" |
| 2402.01030 | CodeAct | **no** | none ("LLM agents") | LLM |
| 2606.20683 | survey: QA → task completion | **no** | none (bare "harness") | "foundation model", LLM |
| 2604.03515 | Inside the Scaffold | yes (arxiv; s2) | "coding agent" | LLM |
| 2605.27922 | Harness-Bench | **no** | none (bare "harness") | LLM |

**Recall: 3/12** (arXiv 3, S2 3, OpenAlex 2, ACL 0, GitHub n/a). Below the 10/12 threshold.

Diagnosis: the LLM block matches all 12 known items; the **harness block** fails 9 of them.
The protocol's harness phrases are narrower than the vocabulary of the canonical harness papers,
which say "LM agents", "LLM agents", "AI agents", "computer agents", "multi-agent
conversation/collaborative framework" or bare "harness".

### Proposed query changes (NOT applied; for the protocol owner to decide)

Measured on arXiv (each addition alone AND the LLM block AND categories AND dates; recall
tested locally against the 12 abstracts):

| addition to the harness block | arXiv hits alone | known items newly matched |
|---|---:|---|
| `harness` (bare) | 1,724 | 2605.27922, 2606.20683 |
| `"LLM agent*"` | 3,899 | 2402.01030, 2605.27922 |
| `"LM agent*"` | 22 | 2405.15793 |
| `"language model agent*"` (move from LLM block) | 551 | 2405.15793 |
| `"AI agent*"` | 1,366 | 2407.16741 |
| `"multi-agent"` (bare) | 4,214 | 2308.00352, 2308.08155 |
| `"computer agent*"` | 15 | 2402.07456 |
| `"agent-computer interface"` | 4 | 2405.15793 |
| `"generalist agent*"` | 48 | 2402.07456, 2407.16741 |
| `"language agent*"` | 242 | – |
| `"autonomous agent*"` | 782 | – |
| `"code agent*"` | 543 | – |
| `"software agent*"` | 35 | – |
| `agentic` (bare) | 16,812 | – (arXiv stems it to "agent"; same as bare `agent`) |
| `agent` (bare) | 16,812 | 8 of the 9 missing |

Combined proposals (arXiv, both blocks, categories, dates):

| proposal | arXiv hits | recall | still missing |
|---|---:|---:|---|
| protocol block (current) | 4,030 | 3/12 | 9 |
| **P1** = protocol + `harness` + `"LLM agent*"` + `"LM agent*"` + `"multi-agent"` + `"AI agent*"` | 11,700 | 10/12 | 2210.03629, 2402.07456 |
| **P2** = P1 + `"computer agent*"` + `"language agent*"` | 11,834 | 11/12 | 2210.03629 |
| P3 = protocol + bare `agent` | 17,188 | 11/12 | 2210.03629 |

Recommendation: adopt **P2** (about 2.9× the arXiv volume of the current block for a recall
jump from 3/12 to 11/12; P3 costs 46% more than P2 for the same recall). Expect S2 and
OpenAlex volumes to scale similarly (S2 was 7,570; OpenAlex 15,994), so the freeze run should
either lift the 5,000 cap or add the structure block on those two sources for precision.
ReAct (2210.03629) is unreachable by any agent-vocabulary query (its abstract describes
"reasoning traces and task-specific actions" without the word "agent"); it will be reached by
backward snowballing from essentially every included paper (protocol section 5), which is the
intended path for it. Re-test recall after the change with
`python scripts/harvest/arxiv.py --count-only` and the recall block in this log.

Secondary observations for the freeze:

* `orchestration` is the noisiest term: OpenAlex 8,863 of 15,994 title+abstract hits; on arXiv
  it matches 777 of the 4,030 records and is the *only* harness term in 651 of them (the largest
  sole-term contributor; next: "agent framework" 441, "coding agent" 380, "agentic framework" 377).
  Consider `"agent orchestration"` OR `"LLM orchestration"` OR `"orchestration framework"` instead
  of the bare word. In the ACL Anthology the picture differs: "agent framework" (240 of 420) and
  "multi-agent framework" (161) dominate and `orchestration` matches only 48.
* OpenAlex stems `agentic` → `agent`, so `"agentic framework"` and `"agent framework"` are one
  query there; harmless.
* Snowballing works: `s2.py --snowball 2405.15793 2308.08155` (smoke test, 2 seeds) returned
  4,083 date-filtered citing/cited records in 11 requests (SWE-agent: 1,784 citations, 0
  references listed by S2; AutoGen: 2,594 citations + 60 references). Output kept out of
  `data/raw/` for this run.

### Failures and caps (summary)

* **OpenReview: failed on all 11 venues** (Cloudflare Turnstile challenge for unauthenticated
  API access). `scripts/harvest/openreview.py` supports `POST /login` with
  `OPENREVIEW_USERNAME`/`OPENREVIEW_PASSWORD` from the environment or `.env`; re-run once
  credentials are available. Invitation ids to confirm with `--discover`:
  `ICLR.cc/<year>/Conference/-/Submission` (v2, 2024+), `ICLR.cc/2023/Conference/-/Blind_Submission` (v1),
  `NeurIPS.cc/<year>/Conference/-/Submission`, `ICML.cc/<year>/Conference/-/Submission`
  (`ICML.cc/2023/...` on v1). Because most ICLR/NeurIPS/ICML papers also appear on arXiv,
  the coverage loss for the test run is mainly on rejected/withdrawn submissions.
* **Semantic Scholar capped** at 5,000 of 7,570 (citation-count order).
* **OpenAlex capped** at 5,000 of 15,994 (cited_by_count order).
* arXiv, ACL Anthology, GitHub: complete, not capped.
* `data/raw/cache/anthology+abstracts.bib.gz` (42 MB) must be git-ignored by the maintainer
  (see `scripts/harvest/README.md`).

## Addendum 2026-09-16 19:08 UTC: OpenReview re-run with login

OpenReview harvested successfully once `OPENREVIEW_USERNAME`/`OPENREVIEW_PASSWORD` were set (anonymous access is blocked by a Cloudflare challenge). v1 strings, regex on title+abstract. Submissions scanned per venue: ICLR 2023 3,792 (0 matched), 2024 7,404 (6), 2025 11,672 (55), 2026 19,814 (265); NeurIPS 2023 3,395 (3), 2024 4,236 (8), 2025 5,540 (37); ICML 2023 1,828 (0), 2024 2,610 (6), 2025 3,422 (14), 2026 6,555 (89). Total 70,268 submissions scanned, 483 matched, 80 requests.

Dedupe re-run with OpenReview included:

```
| source | raw hits | after dedupe | unique to source |
|---|---:|---:|---:|
| arxiv | 4030 | 3991 | 777 |
| acl | 420 | 420 | 99 |
| openreview | 483 | 472 | 148 |
| s2 | 5000 | 4825 | 772 |
| openalex | 5000 | 3797 | 1127 |
| github | 1361 | 1360 | 1360 |
| **total** | 16294 | 8506 | |

merges: {'doi': 2703, 'arxiv_id': 5335, 'title_exact': 7497, 'title_fuzzy': 53}
candidates written: 8506 -> C:\Users\Bhaskar\Pictures\Research\harness-db\data\raw\candidates.csv
```

---

# SEARCH FREEZE — 2026-09-16 (run 19:47–20:50 UTC)

**Status: FROZEN.** Window 2022-10-01 to 2026-08-31. No caps. This section supersedes the test-run sections above.
Full run details, commands, retries and the v3 measurement: `data/raw/freeze_notes.md`. Frozen gzipped copies of every raw
file: `data/raw/frozen/` (also uploaded to the OSF project https://osf.io/vkjer/ storage under `frozen-harvest-2026-09-16/`).

## Final query (protocol section 6, amendments 1 and 2)
- Harness block v2 (amendment 1) AND LLM block; on Semantic Scholar and OpenAlex additionally AND the structure block.
- Amendment 2 (v3'): the LLM block is waived when a strong harness term is present: "agent harness*", "agentic harness*",
  "coding agent*", "agent scaffold*", "agentic scaffold*", "software engineering agent*", "web agent*". Applied to arXiv, ACL,
  OpenReview (local regex; GitHub not re-filtered, README cache unavailable; S2/OpenAlex unchanged). Measured before adoption:
  the broader 9-term waiver added 963 arXiv records at ~30% clearly relevant / ~38% clearly irrelevant on a 40-record sample,
  with the noise concentrated in "GUI agent*" and "computer-use agent*"; the 7-term form keeps all 8 recovered known items.
- Snowballing: one round of references + citations from 11 seeds via Semantic Scholar (ReAct citers truncated at S2's 9,999 ceiling).
- Curated lists: Picrew/awesome-agent-harness (368), Gloriaameng/Awesome-Agent-Harness (158), ggjy/Awesome-Agent-Engineering (296).
- Grey: 48 vendor/lab documentation records; leaderboards (SWE-bench, HAL, OSWorld, WebArena, Terminal-Bench, GAIA, tau-bench,
  tau2-bench) — 3,946 records kept for the outcomes table; only 251 distinct non-GAIA systems enter candidates (GAIA's open
  submission log excluded by `EXCLUDED_LEADERBOARDS`).

## Raw records per source (frozen)
| source | records | notes |
|---|---:|---|
| arXiv | 11,835 | 11,242 (v2, complete) + 593 (v3' waiver) |
| Semantic Scholar | 6,744 | structure block; 20,019 without it |
| OpenAlex | 14,812 | structure block; 40,607 without it; complete with API key |
| OpenReview | 1,754 | 1,686 + 68 (v3'); 70,268 submissions scanned, 11 venues |
| ACL Anthology | 1,393 | 1,363 + 30 (v3') |
| GitHub | 1,361 | 3,228 hits, 2,555 repos, README-filtered |
| Snowball | 11,289 | 11 seeds via Semantic Scholar |
| Survey reference lists | 415 | Li et al. and Meng et al. bibliographies parsed from PDF (not on S2); 195 papers, 81 repos, 139 other |
| Awesome-lists | 822 | 3 catalogs |
| Grey (vendor docs) | 48 | |
| Leaderboards | 3,946 | 251 non-GAIA systems enter candidates |

## Dedupe (DOI -> arXiv id -> exact normalised title -> rapidfuzz >= 95)
| source | raw hits | after dedupe | unique to source |
|---|---:|---:|---:|
| arxiv | 11835 | 11784 | 4744 |
| acl | 1393 | 1393 | 350 |
| openreview | 1754 | 1699 | 599 |
| s2 | 6744 | 6468 | 403 |
| openalex | 14812 | 8966 | 3172 |
| github | 1361 | 1360 | 1238 |
| awesome | 822 | 798 | 358 |
| grey | 48 | 48 | 43 |
| leaderboard | 251 | 241 | 201 |
| s2_snowball | 11289 | 11236 | 7218 |
| leaderboards | 0 | 0 | 0 |
| snowball | 0 | 0 | 0 |
| **total** | 50309 | 27588 | |

merges: {'doi': 7333, 'arxiv_id': 15439, 'title_exact': 22185, 'title_fuzzy': 138}
candidates written: 27588 -> C:\Users\Bhaskar\Pictures\Research\harness-db\data\raw\candidates.csv

## Known-item recall (48 ids, data/raw/known_items.txt)
- Search sources only: 39/48 (81%).
- With snowball, survey reference lists and awesome-lists: **46/48 (96%)**, above the registered 90% threshold.
- Missing: 2607.10113 (skills-library survey; no harness term) and 2609.17394 (dated 2026-09-15, outside the window).

## Next
Screening starts from `data/raw/candidates.csv` (27,747 rows after the survey-reference snowball; see addendum below): Rayyan import + ASReview prioritisation (screener 1), full random
order (screener 2), LLM third vote in a separate column.

## Addendum 2026-09-16 20:53–20:59 UTC: backward snowballing from the two surveys S2 does not index

Protocol section 5 requires backward snowballing from the competitor surveys. Two of them have no
Semantic Scholar record (checked with `/paper/search/match` and the relevance search), so
`s2.py --snowball` could not reach their bibliographies:
Li et al., *Agent Harness Engineering: A Survey* (OpenReview eONq7FdiHa) and Meng et al., *Agent
Harness for Large Language Model Agents: A Survey* (Preprints.org 202604.0428). Their PDFs were taken
from the companion repositories (`picrew/LLM-Harness/docs/main.pdf`, byte-identical to the OpenReview
PDF; `Gloriaameng/Awesome-Agent-Harness/Agent_Harness_for_LLM_Agents__A_Survey__v4.pdf`), cached in
`data/raw/cache/`, and their reference sections parsed by `scripts/harvest/survey_refs.py`:

```
python scripts/harvest/survey_refs.py --since 2022-10-01 --until 2026-08-31 --out data/raw/snowball_surveys.jsonl
```

| survey | reference entries | with arXiv id | GitHub repos | S2 resolved by id | title lookups → accepted (fuzz ≥ 85) | written: S2 papers / repos / other refs | outside window |
|---|---:|---:|---:|---:|---:|---|---:|
| Li et al. 2026 (author-year list) | 250 | 58 | 72 | 58/58 | 119 → 51 | 107 / 72 / 69 | 2 |
| Meng et al. 2026 (numbered list) | 170 | 30 (+2 DOI) | 9 | 32/32 | 127 → 59 | 88 / 9 / 70 | 3 |
| **total** | **420** | | | | | **415 records** (195 `s2_snowball` papers, 81 repos + 139 blog/doc references as `survey_refs`) | 5 |

266 S2 requests, 0 failures. `query_used = snowball:references:openreview:eONq7FdiHa` /
`snowball:references:preprints:202604.0428`; `extra.resolved` records whether S2 matched by id,
by title (with the fuzz ratio) or not at all.

Known-item recall with the survey bibliographies added: unchanged at **46/48** (the 11 known items
the two bibliographies cite were all already in the candidate set); still missing 2607.10113 and
2609.17394.

Dedupe re-run (`python scripts/dedupe.py --include-snowball`, 20:59 UTC), same settings:

| source | raw hits | after dedupe | unique to source |
|---|---:|---:|---:|
| arxiv | 11835 | 11784 | 4736 |
| acl | 1393 | 1393 | 350 |
| openreview | 1754 | 1699 | 599 |
| s2 | 6744 | 6468 | 403 |
| openalex | 14812 | 8966 | 3172 |
| github | 1361 | 1360 | 1237 |
| awesome | 822 | 798 | 273 |
| grey | 48 | 48 | 43 |
| leaderboard | 251 | 241 | 201 |
| s2_snowball (snowball.jsonl + resolved survey refs) | 11484 | 11324 | 7255 |
| survey_refs (repos + unresolved refs) | 220 | 208 | 122 |
| **total** | **50724** | **27747** | |

merges: doi 7440 · arxiv_id 15589 · title_exact 22436 · title_fuzzy 142.
**Candidates: 27,747** (was 27,588; +159 clusters, of which 122 are references only the two
surveys cite) → `data/raw/candidates.csv`. Frozen copy: `data/raw/frozen/snowball_surveys.jsonl.gz`
(171,946 bytes). Phase 2 checklist item "snowball seeds: the 4 competitor surveys' reference lists"
is now complete for all four surveys (Guo and Rombaut via S2 on 2026-09-16 20:00 UTC, Li and Meng here).
