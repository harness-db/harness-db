# scripts/harvest/ — candidate harvesting (protocol task S1)

One script per information source (protocol section 5), a shared helper module, and
`scripts/dedupe.py` to merge everything into `data/raw/candidates.csv`. Every run of the
pipeline is logged in `data/raw/search_log.md` (queries, hit counts, failures, caps, known-item
recall). The search strings are **not frozen**: these scripts exist to test them.

## Common CLI

```
python scripts/harvest/<source>.py --since 2022-10-01 --until 2026-08-31 \
    --out data/raw/<source>.jsonl [--count-only] [--max-records 5000] [--log-level INFO]
```

* `--count-only` reports hit counts and writes nothing.
* `--max-records N` caps the records written per source (default 5000; `0` = unlimited). Sources
  that exceed the cap are fetched in citation-count order (S2, OpenAlex) so the cap keeps the
  most-cited works; the cap is recorded in the summary and in `search_log.md`.
* Each script prints a final line `SUMMARY {...json...}` with the exact query, per-block
  counts, records written, whether it was capped, and any error.
* Exit code 1 when the source failed (partial output may still have been written).

Run from the repository root; each script is standalone (`python scripts/harvest/arxiv.py`).

## Record schema (`data/raw/*.jsonl`, one JSON object per line)

| field | meaning |
|---|---|
| `id` | `<source>:<source_id>` (unique within a file) |
| `source` | `arxiv`, `s2`, `openalex`, `openreview`, `acl`, `github` (`s2_snowball` for snowballing) |
| `source_id` | native identifier (arXiv id, S2 paperId, OpenAlex `W...`, OpenReview note id, Anthology key, GitHub `owner/repo`) |
| `title`, `abstract` | text used for screening (GitHub: description + first 1500 README characters) |
| `authors` | list of names (GitHub: owner login) |
| `date` | ISO `YYYY-MM-DD`, or `YYYY-MM` / `YYYY` when that is all the source gives |
| `venue` | journal/conference/`github` |
| `url`, `doi`, `arxiv_id` | identifiers used by `dedupe.py` (`doi` and `arxiv_id` normalised) |
| `categories` | arXiv categories, S2 fields of study, OpenAlex topics, GitHub topics |
| `query_used` | exact query (or local regex filter) that produced the record |
| `retrieved_at` | UTC timestamp |
| `extra` | source-specific extras (citation counts, stars, README excerpt, venueid, ...) |

## Sources

| script | endpoint | how the protocol blocks are translated |
|---|---|---|
| `arxiv.py` | `export.arxiv.org/api/query` | `(ti:t OR abs:t ...) AND (LLM block) AND (cat:cs.AI OR cs.CL OR cs.SE OR cs.LG) AND submittedDate:[since TO until]`; 200/page, 3 s between requests, sorted by submission date. arXiv stems, so `scaffold*` is issued as `scaffold` and `LLM` also matches `LLMs`. Reports harness-only / LLM-only / both counts. |
| `s2.py` | `api.semanticscholar.org/graph/v1/paper/search/bulk` | `(harness terms \| ...) + (LLM terms \| ...)`, `fieldsOfStudy=Computer Science`, `publicationDateOrYear=since:until`, `sort=citationCount:desc`; 1 request/s, backs off on 429. No wildcard: `scaffold*` -> `scaffold`/`scaffolding`/`scaffolds`; plurals of the LLM terms added. `--snowball ID ...` / `--snowball-file` fetch citations + references of seed papers (arXiv ids, DOIs or S2 ids) into a separate JSONL (source `s2_snowball`). |
| `openalex.py` | `api.openalex.org/works` (polite pool, `mailto`) | default `--mode title_abstract`: `filter=title_and_abstract.search:(harness) AND (llm),from_publication_date,to_publication_date,concepts.id:C41008148`; `--mode fulltext` uses `search=` (far broader; count reported only). Cursor pagination, 200/page, `sort=cited_by_count:desc`. OpenAlex throttles boolean queries with >5 operators; the client backs off. |
| `openreview.py` | `api2.openreview.net/notes`, `api.openreview.net/notes` | ICLR 2023–2026, NeurIPS 2023–2025, ICML 2023–2026: `invitation=<venue>/-/Submission` (v2) or `/-/Blind_Submission` (v1), then local regex filter on title+abstract. **Requires credentials**: both APIs answer unauthenticated requests with a Cloudflare Turnstile challenge (`403 ChallengeRequiredError`); set `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` in the environment or `.env`. `--discover` lists invitations per venue. |
| `acl.py` | `aclanthology.org/anthology+abstracts.bib.gz` | downloads the bulk BibTeX once to `data/raw/cache/`, streams it through a minimal BibTeX parser (no dependency), keeps `year` in range (month-trimmed at the ends when given) and applies the harness AND LLM regexes to title+abstract. `--refresh` re-downloads. |
| `github.py` | `gh api search/repositories`, `gh api repos/{repo}/readme` | topic queries (`llm-agent`, `ai-agent`, `coding-agent`, `llm-agents`, `agent-framework`) and keyword queries (`"agent harness"`, `"coding agent"`, `"computer-use agent"`, `"browser agent" llm` in name/description/README), each with `stars:>500 created:since..until`; slices with >1000 hits are split by creation date; unique repos have their README fetched and are kept if README/description matches the LLM block. Uses `C:\Program Files\GitHub CLI\gh.exe` (must be authenticated). |

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

## Full test run

```
python scripts/harvest/arxiv.py
python scripts/harvest/s2.py
python scripts/harvest/openalex.py
python scripts/harvest/openreview.py      # needs OPENREVIEW_USERNAME / OPENREVIEW_PASSWORD
python scripts/harvest/acl.py
python scripts/harvest/github.py
python scripts/dedupe.py
```

Then copy the `SUMMARY` lines and the dedupe table into `data/raw/search_log.md`.

## Maintainer notes

* `data/raw/cache/` holds the 42 MB Anthology archive. It must not be committed: please add
  `data/raw/cache/` to `.gitignore` (this directory could not be edited by the harvesting task).
* No API keys are used. A Semantic Scholar key (`x-api-key`) or OpenAlex premium key would
  raise the rate limits but are not required.
* Snowball seeds (competitor surveys, awesome-lists, included papers) go in a text file, one
  id per line, and run with `python scripts/harvest/s2.py --snowball-file seeds.txt --out data/raw/s2_snowball.jsonl`.
