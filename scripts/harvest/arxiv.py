"""Harvest arXiv via the export API (http://export.arxiv.org/api/query).

Query = (harness block) AND (LLM block) AND (cs.AI|cs.CL|cs.SE|cs.LG) AND submittedDate range.
Each protocol term is searched in title (``ti:``) and abstract (``abs:``). arXiv's Lucene
backend stems, so ``"agent scaffold*"`` is issued as ``"agent scaffold"`` (matches
"scaffolding"/"scaffolds") and ``LLM`` matches ``LLMs``.

Pagination: 200 results per page, 3 s between requests (arXiv API policy). Per-block counts
(harness only, LLM only, both) are always reported.

Usage:
    python scripts/harvest/arxiv.py --since 2022-10-01 --until 2026-08-31 \
        --out data/raw/arxiv.jsonl [--count-only] [--max-records 5000]
"""

from __future__ import annotations

import logging
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

from common import (
    ARXIV_CATEGORIES,
    HARNESS_TERMS,
    LLM_TERMS,
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    expand_wildcards,
    normalize_arxiv_id,
    now_iso,
    print_summary,
    setup_logging,
)

API_URL = "http://export.arxiv.org/api/query"
PAGE_SIZE = 200
MIN_INTERVAL = 3.0  # seconds between requests (arXiv policy)
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _quote(term: str) -> str:
    return f'"{term}"' if " " in term or "-" in term else term


def block_query(terms: tuple[str, ...], fields: tuple[str, ...] = ("ti", "abs")) -> str:
    """Build ``(ti:"t1" OR abs:"t1" OR ...)`` for a protocol block.

    Wildcard terms are expanded to their stem only, because arXiv stems server side
    (verified: ``"agent scaffold"`` and ``"agent scaffold*"`` return identical counts).
    """
    parts: list[str] = []
    for t in terms:
        variants = expand_wildcards(t)[:1]  # stem only; arXiv stems
        for v in variants:
            for f in fields:
                parts.append(f"{f}:{_quote(v)}")
    return "(" + " OR ".join(parts) + ")"


def date_clause(since: str, until: str) -> str:
    s = since.replace("-", "") + "0000"
    u = until.replace("-", "") + "2359"
    return f"submittedDate:[{s} TO {u}]"


def category_clause(cats: tuple[str, ...] = ARXIV_CATEGORIES) -> str:
    return "(" + " OR ".join(f"cat:{c}" for c in cats) + ")"


def build_queries(since: str, until: str) -> dict[str, str]:
    """Return the three queries whose counts we record: harness-only, llm-only, both."""
    h = block_query(HARNESS_TERMS)
    l = block_query(LLM_TERMS)
    tail = f"{category_clause()} AND {date_clause(since, until)}"
    return {
        "harness_block": f"{h} AND {tail}",
        "llm_block": f"{l} AND {tail}",
        "both": f"{h} AND {l} AND {tail}",
    }


@dataclass
class Page:
    total: int
    entries: list[ET.Element]


def fetch_page(client: HttpClient, query: str, start: int, max_results: int) -> Page:
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    resp = client.get(API_URL, params=params)
    if resp.status_code != 200:
        raise HttpError(f"arXiv HTTP {resp.status_code}: {resp.text[:200]!r}")
    root = ET.fromstring(resp.content)
    total_el = root.find("os:totalResults", NS)
    total = int(total_el.text) if total_el is not None and total_el.text else 0
    return Page(total=total, entries=root.findall("atom:entry", NS))


def entry_to_record(entry: ET.Element, query: str) -> Record:
    def text(tag: str) -> str:
        el = entry.find(tag, NS)
        return (el.text or "").strip() if el is not None else ""

    raw_id = text("atom:id")
    arxiv_id = normalize_arxiv_id(raw_id) or raw_id.rsplit("/", 1)[-1]
    title = re.sub(r"\s+", " ", text("atom:title"))
    abstract = re.sub(r"\s+", " ", text("atom:summary"))
    authors = [
        (a.find("atom:name", NS).text or "").strip()
        for a in entry.findall("atom:author", NS)
        if a.find("atom:name", NS) is not None
    ]
    cats = [c.get("term", "") for c in entry.findall("atom:category", NS)]
    doi_el = entry.find("arxiv:doi", NS)
    journal_el = entry.find("arxiv:journal_ref", NS)
    published = text("atom:published")[:10]
    return Record(
        id=f"arxiv:{arxiv_id}",
        source="arxiv",
        source_id=arxiv_id,
        title=title,
        abstract=abstract,
        authors=authors,
        date=published or None,
        venue=(journal_el.text or "").strip() if journal_el is not None else None,
        url=f"https://arxiv.org/abs/{arxiv_id}",
        doi=(doi_el.text or "").strip() if doi_el is not None else None,
        arxiv_id=arxiv_id,
        categories=cats,
        query_used=query,
        retrieved_at=now_iso(),
    )


def iter_records(
    client: HttpClient, query: str, max_records: int, log: logging.Logger
) -> Iterator[Record]:
    start = 0
    total: int | None = None
    empty_pages = 0
    while True:
        page = fetch_page(client, query, start, PAGE_SIZE)
        if total is None:
            total = page.total
            log.info("arXiv reports %d total results", total)
        if not page.entries:
            # arXiv occasionally returns an empty page transiently; retry a couple of times.
            empty_pages += 1
            if start >= (total or 0) or empty_pages > 3:
                break
            log.warning("empty page at start=%d (attempt %d); retrying", start, empty_pages)
            continue
        empty_pages = 0
        for e in page.entries:
            yield entry_to_record(e, query)
        start += len(page.entries)
        if start >= total or (max_records and start >= max_records):
            break


def main(argv: list[str] | None = None) -> int:
    p = build_parser("arxiv", __doc__.split("\n\n")[0])
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    client = HttpClient(min_interval=MIN_INTERVAL, logger=log)
    queries = build_queries(args.since, args.until)

    counts: dict[str, int | None] = {}
    for name, q in queries.items():
        try:
            counts[name] = fetch_page(client, q, 0, 1).total
            log.info("%s: %s hits", name, counts[name])
        except HttpError as exc:
            log.error("%s: count failed: %s", name, exc)
            counts[name] = None

    written = 0
    capped = False
    error: str | None = None
    if not args.count_only:
        with JsonlWriter(args.out, count_only=False) as w:
            try:
                for rec in iter_records(client, queries["both"], args.max_records, log):
                    if args.max_records and w.count >= args.max_records:
                        capped = True
                        break
                    w.write(rec)
                    if w.count % 1000 == 0:
                        log.info("written %d", w.count)
            except HttpError as exc:
                error = str(exc)
                log.error("harvest aborted: %s", exc)
            written = w.count
    print_summary(
        "arxiv",
        {
            "queries": queries,
            "counts": counts,
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
