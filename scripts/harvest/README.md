# scripts/harvest/ — candidate harvesting (protocol task S1)

One script per information source (protocol section 5), a shared helper module, and
`scripts/dedupe.py` to merge everything into `data/raw/candidates.csv`. Every run of the
pipeline is logged in `data/raw/search_log.md` (queries, hit counts, failures, caps, known-item
recall). The search strings in `common.py` are the **v2 blocks of protocol section 6**
(harness block amended 2026-09-16; see the protocol's Amendments table). The freeze run
(2026-09-16) is documented in `data/raw/search_log.md` and `data/raw/freeze_notes.md`; the
frozen raw files are gzipped in `data/raw/frozen/`.

## Common CLI

```
python scripts/harvest/<source>.py --since 2022-10-01 --until 2026-08-31 \
    --out data/raw/<source>.jsonl [--count-only] [--max-records 0] [--log-level INFO]
    [--with-structure-block]     # s2.py and openalex.py only
```

* `--count-only` reports hit counts and writes nothing.
* `--max-records N` caps the records written per source (default `0` = unlimited since the
  freeze run; the test run used 5000). Sources that exceed a cap are fetched in citation-count
  order (S2, OpenAlex) so the cap keeps the most-cited works; the cap is recorded in the summary
  and in `search_log.md`.
* `--waive-llm-on-strong` (measurement of **proposal v3**, default off, not part of the protocol):
  a record that contains a *strong* harness term (`common.STRONG_TERMS`: `"agent harness*"`,
  `"agentic harness*"`, `"coding agent*"`, `"agent scaffold*"`, `"agentic scaffold*"`,
  `"software engineering agent*"`, `"computer-use agent*"`, `"GUI agent*"`, `"web agent*"`) is
  kept even when the LLM block does not match, i.e. `(HARNESS AND LLM) OR STRONG`. Honoured by
  `arxiv.py` (query becomes `((H AND L) OR S) AND cats AND dates`), `acl.py`, `openreview.py`
  and `github.py` (local regexes); ignored by `s2.py` and `openalex.py`. Measured at the freeze
  into `data/raw/*_v3.jsonl` scratch files (see `data/raw/freeze_notes.md`, "v3 measurement").
* `--with-structure-block` (S2 and OpenAlex only) ANDs the protocol's optional structure block
  (`common.STRUCTURE_TERMS`: `"tool call*" OR "function call*" OR "control loop" OR "context
  management" OR memory OR sandbox OR verification OR retry OR planning`) into the query. Both
  scripts always report the hit count of harness AND LLM alone (`counts.both` /
  `counts.title_abstract`) next to the count with the structure block, so the precision
  trade-off is visible in the summary. The freeze run used it on these two sources only
  (protocol: "optional structure block for precision on the two largest sources").
* Each script prints a final line `SUMMARY {...json...}` with the exact query, per-block
  counts, records written, whether it was capped, and any error.
* Exit code 1 when the source failed (partial output may still have been written).

Run from the repository root; each script is standalone (`python scripts/harvest/arxiv.py`).

## Record schema (`data/raw/*.jsonl`, one JSON object per line)

| field | meaning |
|---|---|
| `id` | `<source>:<source_id>` (unique within a file) |
| `source` | `arxiv`, `s2`, `openalex`, `openreview`, `acl`, `github`, `awesome` (`s2_snowball` for snowballing) |
| `source_id` | native identifier (arXiv id, S2 paperId, OpenAlex `W...`, OpenReview note id, Anthology key, GitHub `owner/repo`, `<list>:<sha1[:12] of url>` for awesome-lists) |
| `title`, `abstract` | text used for screening (GitHub: description + first 1500 README characters) |
| `authors` | list of names (GitHub: owner login) |
| `date` | ISO `YYYY-MM-DD`, or `YYYY-MM` / `YYYY` when that is all the source gives |
| `venue` | journal/conference/`github` |
| `url`, `doi`, `arxiv_id` | identifiers used by `dedupe.py` (`doi` and `arxiv_id` normalised) |
| `categories` | arXiv categories, S2 fields of study, OpenAlex topics, GitHub topics |
| `query_used` | exact query (or local regex filter) that produced the record; `snowball:<direction>:<seed>` for snowball records; `awesome-list:<list>:<file url>` for awesome-list entries |
| `retrieved_at` | UTC timestamp |
| `extra` | source-specific extras (citation counts, stars, README excerpt, venueid, ...) |

## Sources

### Protocol blocks (v2) and how each source receives them

Harness block (`common.HARNESS_TERMS`, 20 terms, `*` = wildcard):
`"agent harness" OR harness OR "agent scaffold*" OR "agentic framework" OR "agent framework" OR "LLM agent*" OR "LM agent*" OR "language agent*" OR "AI agent*" OR "computer agent*" OR "multi-agent" OR "tool-use agent" OR "coding agent" OR "software engineering agent" OR "computer-use agent" OR "GUI agent" OR "web agent" OR "multi-agent framework" OR "agent orchestration" OR "LLM orchestration"`

LLM block (`common.LLM_TERMS`): `"large language model" OR LLM OR "foundation model" OR "language model agent"`

Structure block (`common.STRUCTURE_TERMS`, optional, `--with-structure-block`): `"tool call*" OR "function call*" OR "control loop" OR "context management" OR memory OR sandbox OR verification OR retry OR planning`

`common.expand_wildcards` turns `agent scaffold*` into `agent scaffold` / `agent scaffolding` /
`agent scaffolds`, `... agent*` into `... agent` / `... agents`, and `... call*` into `... call` /
`... calls` / `... calling`. Sources that stem server-side (arXiv, OpenAlex) are sent the first
variant (the stem) only; S2, which has no phrase-internal wildcard, is sent every variant.

| source | harness block | LLM block | structure block |
|---|---|---|---|
| arXiv | each term as `ti:"t" OR abs:"t"`; wildcard terms as their stem (arXiv stems: `"agent scaffold"` = `"agent scaffold*"`, `"LLM agent"` matches `LLM agents`); bare `harness` and `"multi-agent"` issued as is | same, `ti:`/`abs:` | not supported (not applied) |
| Semantic Scholar | `("agent harness" \| harness \| "agent scaffold" \| "agent scaffolding" \| "agent scaffolds" \| ... \| "LLM agent" \| "LLM agents" \| ...)` (every wildcard variant spelled out, S2 does not stem phrases) | `("large language model" \| "large language models" \| LLM \| LLMs \| "foundation model" \| "foundation models" \| "language model agent")` (plurals added) | `+ ("tool call" \| "tool calls" \| "tool calling" \| "function call" \| "function calls" \| "function calling" \| "control loop" \| "context management" \| memory \| sandbox \| verification \| retry \| planning)` when `--with-structure-block` |
| OpenAlex | `title_and_abstract.search:(... OR ...)` with the stem of each wildcard term (OpenAlex stems; it also stems `agentic` to `agent`, so `"agentic framework"` = `"agent framework"` there) | `AND (... OR ...)` | `AND ("tool call" OR "function call" OR "control loop" OR "context management" OR memory OR sandbox OR verification OR retry OR planning)` when `--with-structure-block` |
| OpenReview | local regex `common.HARNESS_RE` on title + abstract | local regex `common.LLM_RE` | not applied |
| ACL Anthology | local regex `common.HARNESS_RE` on title + abstract | local regex `common.LLM_RE` | not applied |
| GitHub | topic/keyword queries (see below), not the block | README/description regex `common.LLM_RE` | not applied |
| awesome-lists | none (every entry is kept; seed material) | none | none |

### Scripts

| script | endpoint | how the protocol blocks are translated |
|---|---|---|
| `arxiv.py` | `export.arxiv.org/api/query` | `(ti:t OR abs:t ...) AND (LLM block) AND (cat:cs.AI OR cs.CL OR cs.SE OR cs.LG) AND submittedDate:[since TO until]`; 200/page, 3 s between requests, sorted by submission date. Reports harness-only / LLM-only / both counts. |
| `s2.py` | `api.semanticscholar.org/graph/v1/paper/search/bulk` | `(harness terms \| ...) + (LLM terms \| ...) [+ (structure terms \| ...)]`, `fieldsOfStudy=Computer Science`, `publicationDateOrYear=since:until`, `sort=citationCount:desc`; 1 request/s, backs off on 429; sends `x-api-key` when `S2_API_KEY` is set (environment or `.env`). `--snowball ID ...` / `--snowball-file` / `--snowball-title "..."` fetch citations + references of seed papers (arXiv ids, DOIs, S2 ids, or exact titles resolved through `/paper/search/match`) into a separate JSONL (source `s2_snowball`, `query_used = snowball:<citations|references>:<seed>`); the summary lists per-seed counts. |
| `openalex.py` | `api.openalex.org/works` (polite pool, `mailto`) | default `--mode title_abstract`: `filter=title_and_abstract.search:(harness) AND (llm) [AND (structure)],from_publication_date,to_publication_date,concepts.id:C41008148`; `--mode fulltext` uses `search=` (far broader; count reported only). Cursor pagination, 200/page, `sort=cited_by_count:desc`. OpenAlex throttles boolean queries with >5 operators (HTTP 429, sometimes with a 120 s `Retry-After`); the client backs off up to 8 times. |
| `openreview.py` | `api2.openreview.net/notes`, `api.openreview.net/notes` | ICLR 2023–2026, NeurIPS 2023–2025, ICML 2023–2026: `invitation=<venue>/-/Submission` (v2) or `/-/Blind_Submission` (v1), then local regex filter on title+abstract. **Requires credentials**: both APIs answer unauthenticated requests with a Cloudflare Turnstile challenge (`403 ChallengeRequiredError`); set `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` in the environment or `.env`. `--discover` lists invitations per venue. |
| `acl.py` | `aclanthology.org/anthology+abstracts.bib.gz` | downloads the bulk BibTeX once to `data/raw/cache/`, streams it through a minimal BibTeX parser (no dependency), keeps `year` in range (month-trimmed at the ends when given) and applies the harness AND LLM regexes to title+abstract. `--refresh` re-downloads. |
| `github.py` | `gh api search/repositories`, `gh api repos/{repo}/readme` | topic queries (`llm-agent`, `ai-agent`, `coding-agent`, `llm-agents`, `agent-framework`) and keyword queries (`"agent harness"`, `"coding agent"`, `"computer-use agent"`, `"browser agent" llm` in name/description/README), each with `stars:>500 created:since..until`; slices with >1000 hits are split by creation date; unique repos have their README fetched and are kept if README/description matches the LLM block. Uses `C:\Program Files\GitHub CLI\gh.exe` (must be authenticated). |
| `awesome_lists.py` | `raw.githubusercontent.com`, `gh api` | the three competitor catalogs: `picrew/LLM-Harness` (its `projects.yaml` URL is 404, so the script follows the README's catalog link to `Picrew/awesome-agent-harness` and finds `data/projects.yaml` via the GitHub API; parsed with PyYAML), `Gloriaameng/Awesome-Agent-Harness/README.md` and `ggjy/Awesome-Agent-Engineering/README.md` (generic Markdown parse: every list item / table row with an http link; name, title, links, arXiv id, section headings). Entries with an arXiv id become paper records; entries whose link is a GitHub repo get `title = owner/repo` so they merge with the GitHub harvest; `source="awesome"`, `query_used = awesome-list:<list>:<url>`. |
| `known_items.py` | local | known-item recall: reads `data/raw/known_items.txt` (`arxiv_id<TAB>bibkey<TAB>title`) and reports, per JSONL file and for their union, how many known items are present (match on normalised arXiv id, else on normalised title). `--include-snowball`, `--include-awesome`, `--json`. |

Local regex filters (`common.HARNESS_RE`, `common.LLM_RE`) are case-insensitive, tolerate
hyphen/space variants (`tool-use` = `tool use`) and a trailing plural.

## Dedupe

```
python scripts/dedupe.py [--raw-dir data/raw] [--out data/raw/candidates.csv] [--threshold 95] [--window 50] [--include-snowball]
```

Merges every `data/raw/*.jsonl` (snowball files excluded unless `--include-snowball`), clusters
on DOI, then arXiv id, then normalised title (exact, then `rapidfuzz.fuzz.ratio >= 95` over a
sorted-neighbour window), picks a canonical record per cluster (arxiv > acl > openreview > s2 >
openalex > github, then longest abstract) and writes `candidates.csv` with columns
`id, title, abstract, year, venue, url, source, sources_all, arxiv_id, doi`. It prints the
per-source table (raw hits / after dedupe / unique to source) used for the PRISMA counts.

## Freeze run (2026-09-16)

```
python scripts/harvest/arxiv.py      --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/arxiv.jsonl
python scripts/harvest/acl.py        --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/acl.jsonl
python scripts/harvest/openreview.py --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/openreview.jsonl   # needs OPENREVIEW_USERNAME / OPENREVIEW_PASSWORD
python scripts/harvest/github.py     --since 2022-10-01 --until 2026-08-31 --max-records 0 --out data/raw/github.jsonl
python scripts/harvest/s2.py         --since 2022-10-01 --until 2026-08-31 --max-records 0 --with-structure-block --out data/raw/s2.jsonl
python scripts/harvest/openalex.py   --since 2022-10-01 --until 2026-08-31 --max-records 0 --with-structure-block --out data/raw/openalex.jsonl
python scripts/harvest/awesome_lists.py --out data/raw/awesome.jsonl
python scripts/harvest/known_items.py                      # recall before snowballing
python scripts/harvest/s2.py --snowball <seed ids> --snowball-title "<survey title>" ... --out data/raw/snowball.jsonl
python scripts/harvest/known_items.py --include-snowball --include-awesome
python scripts/dedupe.py [--include-snowball]
```

Exact commands, timestamps, counts and failures of the freeze run: `data/raw/freeze_notes.md`
(condensed into `data/raw/search_log.md`). Frozen copies: `data/raw/frozen/<source>.jsonl.gz`.

## Maintainer notes

* `data/raw/cache/` holds the 42 MB Anthology archive. It must not be committed: please add
  `data/raw/cache/` to `.gitignore` (this directory could not be edited by the harvesting task).
* `s2.py` sends `S2_API_KEY` (from the environment or `.env`) as `x-api-key` when present;
  OpenReview needs a login; OpenAlex and arXiv are used without keys.
* Snowball seeds (competitor surveys, awesome-lists, included papers) go in a text file, one
  id per line, and run with `python scripts/harvest/s2.py --snowball-file seeds.txt --out data/raw/snowball.jsonl`
  (`dedupe.py` skips files with `snowball` in the name unless `--include-snowball`).
