# `fetch_fulltext.py`: full-text retrieval for full-text screening

`scripts/fetch_fulltext.py` fetches the full text of every record in
`data/screening/fulltext_queue.csv` (9,906 ids). It starts with the 325 pilot ids in
`data/screening/fulltext_pilot.csv`, then does the rest of the queue. Each record is resolved
by **identifier** and never by title. It writes one plain-text file per record plus an
append-only index.

```
python scripts/fetch_fulltext.py --only-pilot            # pilot only
python scripts/fetch_fulltext.py --skip-failed           # pilot first, then the whole queue
python scripts/fetch_fulltext.py --ids-file ids.csv --limit 50
python scripts/fetch_fulltext.py --summary --only-pilot  # counts from the index; fetches nothing
```

| flag | meaning |
|---|---|
| `--only-pilot` | fetch only `fulltext_pilot.csv` |
| `--ids-file F` | fetch these ids, in this order. `F` is a CSV with a `record_id` column (or else its first column is used), or a plain list with one id per line |
| `--limit N` | fetch at most N records in this run (counted after skipping finished ones) |
| `--skip-failed` | also skip ids that already have a `not_retrievable` row. Without it, failures are retried |
| `--workers N` | size of the non-arXiv thread pool (default 4) |
| `--summary` | for the selected ids, print ok / not_retrievable counts by candidate source, `source_used` counts, the median number of characters, and the fetched titles that differ from the candidate title |

Requirements: `requests`, `pypdf` (plus `cryptography` for AES-encrypted PDFs), `rapidfuzz`
(only for `--summary`), `git`, and an authenticated GitHub CLI (`gh`). Credentials come from
the environment or the repo's `.env`: `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD`,
`OPENALEX_API_KEY` and `S2_API_KEY`. The S2 key is optional; without it the script uses the
shared S2 pool and backs off on 429.

## Which identifiers are used

Each queue id is the canonical record of a dedupe cluster in `data/raw/candidates.csv`. The
`arxiv_id` and `doi` columns there are **cluster-level**: `dedupe.py` takes them from the first
cluster member that has one, and that member can be a different paper. This is the root cause
of `data/screening/metadata_mismatch.csv`. For example, candidates.csv gives
`arxiv:2503.23803` the `arxiv_id` 2508.13143. The script therefore resolves in two tiers:

1. **Own identifiers.** These are the record id itself (`arxiv:<id>`, `openreview:<forum>`,
   `github:<owner>/<repo>`, `s2:<paperId>`, `openalex:W…`) plus the `arxiv_id`, `doi` and `url`
   of the canonical record's own raw harvest record in `data/raw/*.jsonl`.
2. **Cluster identifiers.** These are the candidates.csv `arxiv_id` and `doi` when they differ
   from the own ones. They are tried only after every own-identifier route has failed. If one
   of them points at a different paper, the fetched title shows it.

arXiv ids are validated before use. The harvesters' loose regex put strings such as
`gov/3812380`, `2024.11511` and `2405.2024` into `arxiv_id`; all three are really fragments of
IEEE or Elsevier DOIs. A new-style id needs YYMM with month 01-12 and 4 sequence digits (before
2015) or 5 (from 2015). An old-style id needs a known archive. A `10.48550/arXiv.*` DOI or an
arxiv.org URL also counts as an arXiv id.

## Resolution order

The first route that yields a parseable document of reasonable length wins:

1. **arXiv id**: `https://arxiv.org/pdf/<id>`, then `https://arxiv.org/html/<id>`.
2. **ACL Anthology id** (from an aclanthology.org URL or a `10.18653/v1/*` DOI):
   `https://aclanthology.org/<id>.pdf`.
3. **OpenReview forum id**: `https://api2.openreview.net/pdf?id=<id>` (API v2), then
   `https://api.openreview.net/pdf?id=<id>` (API v1, used for ICLR/ICML 2023). Both use a
   bearer token from `POST /login`.
4. **GitHub repository** (source `github`, or any URL on github.com):
   * `gh api repos/<o>/<r>` gives the canonical `full_name` (renames are followed) and the
     default branch.
   * The pinned ref follows protocol §4.5: the latest tag dated on or before 2026-08-31, taken
     from GraphQL `refs(refPrefix:"refs/tags/")` ordered by commit date. The tag date is the
     tagger date for annotated tags and the commit date for lightweight tags. If no tag
     qualifies, the ref is the default-branch commit
     `gh api repos/<o>/<r>/commits?sha=<default>&until=2026-08-31T23:59:59Z`.
   * The repo is cloned into `data/raw/cache/repos/<owner>__<repo>` with
     `git clone --depth 1 --branch <tag> --filter=blob:none --no-checkout`. A commit is fetched
     with `git fetch --depth 1 --filter=blob:none origin <sha>`.
   * The checkout is sparse. It contains only `README*`, `docs/**/*.md(x)`, `doc/**/*.md` and,
     for `/tree/<ref>/<subpath>` URLs, that subpath's README. This keeps about 600 repos small
     and avoids Windows path errors. Run `git -C <dir> sparse-checkout disable` to hydrate the
     full tree at the pinned commit.
   * The text bundle is a header (full name, ref, description, topics), then the README
     (≤ 100k chars), then docs markdown (index/overview files first, ≤ 20k chars in total),
     then the file tree (first 400 paths from `git ls-tree -r`).
   * `ref_used` is `tag:<name> <sha> <date>` or `commit:<branch> <sha> <date>`, which is the
     value for M6 `pinned_version`.
5. **Own DOI** (not an arXiv DOI):
   1. OpenAlex `works/doi:<doi>`: `best_oa_location.pdf_url`, then up to two more OA
      `locations[].pdf_url`. A PDF URL on arxiv.org is routed through the arXiv stream.
   2. Semantic Scholar `paper/DOI:<doi>?fields=title,externalIds,openAccessPdf`:
      `externalIds.ArXiv` goes through the arXiv route; otherwise `openAccessPdf.url` is used.
   3. An arXiv location reported by OpenAlex.
6. **S2 or OpenAlex record without its own DOI**: S2 `paper/<paperId>` or OpenAlex
   `works/W…` gives the arXiv id, then the OA PDF, then a DOI, which goes through route 5.
7. **Web sources** (`grey`, `leaderboard`, `awesome`, `survey_refs`): the main text of the
   page at `url` (see below). If that URL is an arXiv or GitHub URL, route 1 or 4 has already
   handled it.
8. **Cluster identifiers** (see above): the cluster arXiv id, then the cluster DOI, which goes
   through ACL or route 5.
9. **Landing pages, last resort**: `https://doi.org/<doi>` for the own DOI, then the record's
   own URL, then the cluster DOI. These pages are parsed as HTML, or as PDF if the server
   returns one. No Unpaywall is used. Treat `source_used = doi_landing_html` or `landing_html`
   as "possibly abstract only".

A record with no usable identifier is written as `not_retrievable`; it is never looked up by
title. That covers title-only survey references, truncated URLs such as `https://www.anthropic`,
and similar cases.

## Text conversion

* **PDF**: pypdf reads all pages in a child process (`--_extract-pdf`). The child has a hard
  300 s timeout and a 150 s soft budget, so a pathological PDF cannot hang or crash the run.
* **Whitespace**: control characters are removed, horizontal whitespace runs collapse to one
  space, lines are stripped, and 3+ newlines become 2.
* **References**: the text is cut at the first line matching
  `^(\d+\.? |[IVX]+\.? )?(References$|REFERENCES|Bibliography)` that lies after the first
  20 % of the text; earlier matches are tables of contents. Everything before that line is
  kept, so appendices after the references are dropped. The same cut applies to arXiv HTML and
  landing pages, but not to web pages or repo bundles.
* **Cap**: text is capped at 250,000 chars.
* **Minimum length**: a paper PDF or arXiv HTML below 1,500 chars is treated as a failure
  (scanned, withdrawn or placeholder) and the next route is tried. The minimum is 1,000 chars
  for landing pages and 300 for web-source pages.
* **HTML**: the stdlib `html.parser` drops `script`, `style`, `nav`, `header`, `footer`,
  `aside`, `form`, `svg`, `noscript`, `iframe`, `template` and `button`, and keeps block
  structure. `<math>` elements become their `alttext`. The `<main>`/`<article>` subtree is
  used when it holds ≥ 500 chars.
* **fetched_title**:
  * PDFs: the largest-font text in the top 40 % of page 1 (then the top 60 %), skipping the
    rotated arXiv stamp. Same-baseline runs are included, which restores small-caps titles.
    If that fails, the PDF metadata title is used when plausible, then the first
    non-boilerplate line.
  * HTML: `citation_title`, then `og:title`, `<title>`, `<h1>`.
  * Repos: `owner/repo`.

  pypdf drops inter-word spaces in some small-caps (ICLR-style) titles. `--summary` therefore
  also checks whether the candidate title occurs in the first 5k chars of the text, ignoring
  spaces and punctuation. This separates title-extraction misses from real document
  mismatches.

## Rate limits and concurrency

| stream / host | pacing | retries |
|---|---|---|
| arXiv (`arxiv.org/pdf`, `/html`) | **strictly serial**, ≥ 3 s between request starts; FIFO gate across all threads; response body read inside the gate | 6 (429/5xx; backoff 10, 20, 40, 80, 120 s, honours `Retry-After`) |
| OpenAlex | 0.15 s (API key + `mailto`) | 5 |
| Semantic Scholar | 1.05 s (key) | 5 |
| ACL Anthology, OpenReview | 1 s | 3 |
| any other host (publishers, docs sites) | 1 s per host | 1 |
| GitHub | `gh api` (5,000 req/h); 3 calls per repo; 30/60/90 s back-off on 403/5xx | 4 |

There are two thread pools. Records with an own arXiv id go to the arXiv pool (4 threads),
which exists so PDF parsing overlaps with the next download. Its network access is serialised
by the gate. All other records go to a separate pool of 4 threads. A record in that pool that
turns out to have an arXiv version queues at the same gate. The User-Agent is
`harness-db-fulltext/0.1 (…; mailto:gurrambhaskar.ai@gmail.com)`.

## Outputs

* `data/fulltext/<safe id>.txt` (safe id = record id with `[:/\]` replaced by `__`). The file
  starts with a 5-line header, then a blank line, then the text:
  ```
  record_id: arxiv:2308.08155
  source_used: arxiv_pdf
  fetched_url: https://arxiv.org/pdf/2308.08155
  fetched_title: AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation
  fetched_at: 2026-09-18T19:02:11Z
  ```
* `data/screening/fulltext_index.csv`: one row per attempt, with columns `record_id, status
  (ok|not_retrievable), source_used, fetched_url, fetched_title, chars, ref_used, fetched_at`.
  `ref_used` is the arXiv version (`arXiv:2308.08155v2`) or the pinned repo ref. **The last
  row per `record_id` is authoritative**, because a retried failure appends a new row.
* `source_used` is one of `arxiv_pdf`, `arxiv_html`, `acl_pdf`, `openreview_pdf`,
  `openalex_oa_pdf`, `s2_oa_pdf`, `github_repo`, `web_html` / `web_pdf`, `doi_landing_html` /
  `doi_landing_pdf`, or `landing_html` / `landing_pdf`.
* `data/screening/not_retrievable.csv`: `record_id, source, reason, urls_tried,
  attempted_at`. `urls_tried` lists every URL requested with its outcome, API lookups
  included; API keys are never written.
* `data/raw/cache/pdf/`: downloaded PDFs (`arxiv__<id>.pdf`, `acl__<id>.pdf`,
  `openreview__<id>.pdf`, `url__<sha1>.pdf`) and arXiv HTML (`arxiv__<id>.html`). A re-run
  reads from here and does not download again.
* `data/raw/cache/repos/<owner>__<repo>/`: shallow sparse clones at the pinned ref.
* `data/fulltext/_fetch_fulltext.log`: progress log. Every 25 records it prints counts,
  arXiv request count, rate and ETA.

## Resuming

After each record, the `.txt` is written atomically (temp file + rename), then its index row
is appended and flushed with `fsync`. A crash or Ctrl-C loses at most the records in flight.
Re-running the same command skips every id whose index has a row with `status == ok`, and
retries the rest. Add `--skip-failed` to also skip recorded failures. To force a re-fetch,
delete the id's rows from the index. The cached PDF is reused; delete it from
`data/raw/cache/pdf/` to download it again.
