"""Harvest Semantic Scholar via the Graph API bulk search, plus citation snowballing.

Bulk search: https://api.semanticscholar.org/graph/v1/paper/search/bulk
  query   = (harness block) + (LLM block)    -- S2 boolean syntax: ``|`` OR, ``+`` AND
  fieldsOfStudy = Computer Science
  publicationDateOrYear = <since>:<until>
  sort = citationCount:desc   (so that a --max-records cap keeps the most-cited papers)

No API key is used: pacing is 1 request/s and HTTP 429 triggers exponential backoff.
S2 has no phrase-internal wildcard, so ``"agent scaffold*"`` is issued as
``"agent scaffold" | "agent scaffolding" | "agent scaffolds"``. S2's search is not stemmed
for the LLM block, so ``"large language models"``/``LLMs``/``"foundation models"`` plurals
are added explicitly.

Snowballing: ``snowball(client, seed_ids)`` fetches the citations and references of each
seed (arXiv ids such as ``2405.15793`` or S2 paper ids) and yields Records. CLI:

    python scripts/harvest/s2.py --snowball 2405.15793 2308.08155 --out data/raw/s2_snowball.jsonl
    python scripts/harvest/s2.py --snowball-file seeds.txt --out ...

Usage (search):
    python scripts/harvest/s2.py --since 2022-10-01 --until 2026-08-31 --out data/raw/s2.jsonl
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from common import (
    HARNESS_TERMS,
    LLM_TERMS,
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    expand_wildcards,
    normalize_arxiv_id,
    normalize_doi,
    now_iso,
    print_summary,
    setup_logging,
    within,
)

API = "https://api.semanticscholar.org/graph/v1"
MIN_INTERVAL = 1.0  # unauthenticated: ~1 request/second
FIELDS = (
    "paperId,externalIds,title,abstract,authors,year,publicationDate,venue,"
    "publicationVenue,url,fieldsOfStudy,citationCount"
)
BULK_PAGE = 1000  # server-side page size for /search/bulk
SNOWBALL_PAGE = 1000
LLM_PLURALS = {"large language model": "large language models", "foundation model": "foundation models", "LLM": "LLMs"}


def _q(term: str) -> str:
    return f'"{term}"' if " " in term or "-" in term else term


def block_query(terms: Iterable[str], plurals: dict[str, str] | None = None) -> str:
    parts: list[str] = []
    for t in terms:
        for v in expand_wildcards(t):
            parts.append(_q(v))
        if plurals and t in plurals:
            parts.append(_q(plurals[t]))
    return "(" + " | ".join(parts) + ")"


def build_query() -> str:
    return f"{block_query(HARNESS_TERMS)} + {block_query(LLM_TERMS, LLM_PLURALS)}"


def paper_to_record(p: dict[str, Any], query: str, source_prefix: str = "s2") -> Record:
    ext = p.get("externalIds") or {}
    arxiv_id = normalize_arxiv_id(ext.get("ArXiv"))
    venue = p.get("venue") or (p.get("publicationVenue") or {}).get("name")
    date = p.get("publicationDate") or (str(p["year"]) if p.get("year") else None)
    return Record(
        id=f"{source_prefix}:{p['paperId']}",
        source=source_prefix,
        source_id=p["paperId"],
        title=(p.get("title") or "").strip(),
        abstract=(p.get("abstract") or "").strip(),
        authors=[a.get("name", "") for a in p.get("authors") or []],
        date=date,
        venue=venue or None,
        url=p.get("url") or f"https://www.semanticscholar.org/paper/{p['paperId']}",
        doi=normalize_doi(ext.get("DOI")),
        arxiv_id=arxiv_id,
        categories=list(p.get("fieldsOfStudy") or []),
        query_used=query,
        retrieved_at=now_iso(),
        extra={"citationCount": p.get("citationCount")},
    )


def bulk_search(
    client: HttpClient,
    query: str,
    since: str,
    until: str,
    log: logging.Logger,
    fields_of_study: str = "Computer Science",
    sort: str = "citationCount:desc",
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield ``(total, paper)`` for every paper in the bulk result set (token pagination)."""
    params: dict[str, Any] = {
        "query": query,
        "fields": FIELDS,
        "fieldsOfStudy": fields_of_study,
        "publicationDateOrYear": f"{since}:{until}",
        "sort": sort,
    }
    token: str | None = None
    while True:
        if token:
            params["token"] = token
        data = client.get_json(f"{API}/paper/search/bulk", params=params)
        total = int(data.get("total", 0))
        for p in data.get("data", []):
            yield total, p
        token = data.get("token")
        if not token:
            break


def count_only(client: HttpClient, query: str, since: str, until: str) -> int:
    params = {
        "query": query,
        "fields": "paperId",
        "fieldsOfStudy": "Computer Science",
        "publicationDateOrYear": f"{since}:{until}",
    }
    return int(client.get_json(f"{API}/paper/search/bulk", params=params).get("total", 0))


# --------------------------------------------------------------------------------------
# Snowballing
# --------------------------------------------------------------------------------------


def to_s2_id(seed: str) -> str:
    """Map an arXiv id / DOI / raw S2 id to the identifier form S2 accepts."""
    a = normalize_arxiv_id(seed)
    if a:
        return f"ARXIV:{a}"
    if seed.lower().startswith("10."):
        return f"DOI:{seed}"
    return seed


def _paginated(client: HttpClient, url: str, params: dict[str, Any]) -> Iterator[dict[str, Any]]:
    offset = 0
    while True:
        page = client.get_json(url, params={**params, "offset": offset, "limit": SNOWBALL_PAGE})
        yield from page.get("data", [])
        nxt = page.get("next")
        if nxt is None:
            break
        offset = int(nxt)


def snowball(
    client: HttpClient,
    seed_ids: Iterable[str],
    log: logging.Logger,
    directions: tuple[str, ...] = ("citations", "references"),
) -> Iterator[Record]:
    """Forward (citations) and backward (references) snowballing from seed papers."""
    for seed in seed_ids:
        sid = to_s2_id(seed)
        for direction in directions:
            key = "citingPaper" if direction == "citations" else "citedPaper"
            url = f"{API}/paper/{sid}/{direction}"
            n = 0
            try:
                for item in _paginated(client, url, {"fields": FIELDS}):
                    paper = item.get(key) or {}
                    if not paper.get("paperId"):
                        continue
                    rec = paper_to_record(paper, f"snowball:{direction}:{seed}", "s2_snowball")
                    rec.extra["seed"] = seed
                    rec.extra["direction"] = direction
                    n += 1
                    yield rec
            except HttpError as exc:
                log.error("snowball %s %s failed: %s", seed, direction, exc)
            log.info("seed %s: %d %s", seed, n, direction)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = build_parser("s2", __doc__.split("\n\n")[0])
    p.add_argument("--snowball", nargs="*", metavar="ID", help="seed ids (arXiv/DOI/S2)")
    p.add_argument("--snowball-file", help="file with one seed id per line")
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    client = HttpClient(min_interval=MIN_INTERVAL, logger=log)

    seeds: list[str] = list(args.snowball or [])
    if args.snowball_file:
        seeds += [ln.strip() for ln in Path(args.snowball_file).read_text().splitlines() if ln.strip() and not ln.startswith("#")]

    if seeds:
        written = 0
        with JsonlWriter(args.out, count_only=args.count_only) as w:
            for rec in snowball(client, seeds, log):
                if within(rec.date, args.since, args.until):
                    w.write(rec)
            written = w.count
        print_summary("s2_snowball", {"seeds": seeds, "written": written, "requests": client.requests_made, "out": None if args.count_only else args.out})
        return 0

    query = build_query()
    log.info("query: %s", query)
    total: int | None = None
    written = 0
    capped = False
    error: str | None = None
    try:
        if args.count_only:
            total = count_only(client, query, args.since, args.until)
        else:
            with JsonlWriter(args.out) as w:
                for tot, paper in bulk_search(client, query, args.since, args.until, log):
                    total = tot
                    if args.max_records and w.count >= args.max_records:
                        capped = True
                        break
                    w.write(paper_to_record(paper, query))
                written = w.count
    except HttpError as exc:
        error = str(exc)
        log.error("harvest aborted: %s", exc)
    print_summary(
        "s2",
        {
            "query": query,
            "params": {"fieldsOfStudy": "Computer Science", "publicationDateOrYear": f"{args.since}:{args.until}", "sort": "citationCount:desc"},
            "counts": {"both": total},
            "written": written,
            "capped": capped,
            "max_records": args.max_records,
            "error": error,
            "requests": client.requests_made,
            "out": None if args.count_only else args.out,
        },
    )
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
