"""Harvest OpenAlex works (https://api.openalex.org/works), polite pool via ``mailto``.

Two query modes (``--mode``):

* ``title_abstract`` (default): ``filter=title_and_abstract.search:(<harness> AND <llm>)``.
  This is the mode used for the harvest; it is what the protocol means by "title/abstract".
* ``fulltext``: ``search=(<harness> AND <llm>)``, which also searches OpenAlex's full text
  index and is far broader. Its count is recorded for the log but not harvested by default.

Common filters: ``from_publication_date``, ``to_publication_date`` and a Computer Science
restriction (``--cs concept`` = ``concepts.id:C41008148``, ``--cs field`` =
``topics.field.id:17``, ``--cs none``). Pagination is cursor based (200 per page) sorted by
``cited_by_count:desc`` so that a ``--max-records`` cap keeps the most-cited works.

OpenAlex stems queries, so wildcard terms are issued as their stem and no plurals are added.
Boolean queries with more than 5 operators are throttled by OpenAlex; the client backs off on
HTTP 429 and retries.

Budget. Since 2026 the free OpenAlex API has a daily spending budget ("Insufficient budget ...
Resets at midnight UTC", HTTP 429 with a multi-hour ``Retry-After``). The harvester therefore
checkpoints the pagination cursor after every page in ``<out>.cursor.json`` and ``--resume``
reopens ``<out>`` in append mode and continues from that cursor (same query/params only; the
checkpoint records them and ``--resume`` refuses a mismatch). On success the checkpoint is
deleted.

Usage:
    python scripts/harvest/openalex.py --since 2022-10-01 --until 2026-08-31 \
        --out data/raw/openalex.jsonl [--count-only] [--mode title_abstract|fulltext] [--cs concept]
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from common import (
    CONTACT_EMAIL,
    HARNESS_TERMS,
    LLM_TERMS,
    STRUCTURE_TERMS,
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
    read_jsonl,
    setup_logging,
)

API = "https://api.openalex.org/works"
PER_PAGE = 200
MIN_INTERVAL = 0.2  # polite pool allows 10 req/s; stay well under
CS_FILTERS = {
    "concept": "concepts.id:C41008148",  # Computer science (legacy concept)
    "field": "topics.field.id:17",  # Computer Science (topics taxonomy)
    "none": "",
}
SELECT = (
    "id,doi,title,display_name,publication_date,publication_year,authorships,primary_location,"
    "ids,abstract_inverted_index,cited_by_count,topics,type,locations"
)


def _q(term: str) -> str:
    return f'"{term}"' if " " in term or "-" in term else term


def block_query(terms: tuple[str, ...]) -> str:
    # OpenAlex stems: wildcard terms become their stem only.
    return "(" + " OR ".join(_q(expand_wildcards(t)[0]) for t in terms) + ")"


def build_query(with_structure: bool = False) -> str:
    q = f"{block_query(HARNESS_TERMS)} AND {block_query(LLM_TERMS)}"
    if with_structure:
        q += f" AND {block_query(STRUCTURE_TERMS)}"
    return q


def build_params(query: str, since: str, until: str, mode: str, cs: str) -> dict[str, Any]:
    filters = [f"from_publication_date:{since}", f"to_publication_date:{until}"]
    if CS_FILTERS[cs]:
        filters.append(CS_FILTERS[cs])
    params: dict[str, Any] = {"mailto": CONTACT_EMAIL}
    if mode == "title_abstract":
        filters.append(f"title_and_abstract.search:{query}")
    elif mode == "fulltext":
        params["search"] = query
    else:
        raise ValueError(mode)
    params["filter"] = ",".join(filters)
    return params


def reconstruct_abstract(inv: dict[str, list[int]] | None) -> str:
    if not inv:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        positions.extend((i, word) for i in idxs)
    positions.sort()
    return " ".join(w for _, w in positions)


def work_to_record(w: dict[str, Any], query: str) -> Record:
    oa_id = (w.get("id") or "").rsplit("/", 1)[-1]
    arxiv_id = None
    for loc in w.get("locations") or []:
        lp = (loc or {}).get("landing_page_url") or ""
        pdf = (loc or {}).get("pdf_url") or ""
        arxiv_id = normalize_arxiv_id(lp) or normalize_arxiv_id(pdf)
        if arxiv_id:
            break
    prim = w.get("primary_location") or {}
    venue = ((prim.get("source") or {}).get("display_name")) if prim else None
    authors = [
        ((a.get("author") or {}).get("display_name") or "") for a in w.get("authorships") or []
    ]
    topics = [t.get("display_name", "") for t in (w.get("topics") or [])[:3]]
    return Record(
        id=f"openalex:{oa_id}",
        source="openalex",
        source_id=oa_id,
        title=(w.get("display_name") or w.get("title") or "").strip(),
        abstract=reconstruct_abstract(w.get("abstract_inverted_index")),
        authors=authors,
        date=w.get("publication_date") or (str(w["publication_year"]) if w.get("publication_year") else None),
        venue=venue,
        url=w.get("doi") or prim.get("landing_page_url") or w.get("id"),
        doi=normalize_doi(w.get("doi")),
        arxiv_id=arxiv_id,
        categories=topics,
        query_used=query,
        retrieved_at=now_iso(),
        extra={"cited_by_count": w.get("cited_by_count"), "type": w.get("type"), "openalex_id": w.get("id")},
    )


def iter_works(
    client: HttpClient,
    params: dict[str, Any],
    log: logging.Logger,
    cursor: str = "*",
    checkpoint: Path | None = None,
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Cursor pagination. After each page the *next* cursor is written to ``checkpoint`` so an
    interrupted run can continue with ``--resume``."""
    p = {**params, "per-page": PER_PAGE, "sort": "cited_by_count:desc", "select": SELECT}
    while cursor:
        data = client.get_json(API, params={**p, "cursor": cursor})
        total = int(data.get("meta", {}).get("count", 0))
        results = data.get("results", [])
        for w in results:
            yield total, w
        cursor = data.get("meta", {}).get("next_cursor")
        if checkpoint is not None:
            checkpoint.write_text(json.dumps({"params": params, "next_cursor": cursor, "total": total}), encoding="utf-8")
        if not results:
            break


def count(client: HttpClient, params: dict[str, Any]) -> int:
    data = client.get_json(API, params={**params, "per-page": 1, "select": "id"})
    return int(data.get("meta", {}).get("count", 0))


def main(argv: list[str] | None = None) -> int:
    p = build_parser("openalex", __doc__.split("\n\n")[0], structure_block=True)
    p.add_argument("--mode", choices=("title_abstract", "fulltext"), default="title_abstract")
    p.add_argument("--cs", choices=tuple(CS_FILTERS), default="concept", help="Computer Science restriction")
    p.add_argument("--resume", action="store_true", help="append to --out and continue from <out>.cursor.json")
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    client = HttpClient(min_interval=MIN_INTERVAL, max_retries=8, logger=log)
    query = build_query(args.with_structure_block)
    log.info("query: %s", query)

    counts: dict[str, int | None] = {}
    variants = [("title_abstract", build_query(False)), ("fulltext", build_query(False))]
    if args.with_structure_block:
        variants.append(("title_abstract_structure", query))
    for name, q in variants:
        mode = "fulltext" if name == "fulltext" else "title_abstract"
        try:
            counts[name] = count(client, build_params(q, args.since, args.until, mode, args.cs))
            log.info("%s: %s", name, counts[name])
        except HttpError as exc:
            log.error("count %s failed: %s", name, exc)
            counts[name] = None

    params = build_params(query, args.since, args.until, args.mode, args.cs)
    written = 0
    resumed_from = 0
    capped = False
    error: str | None = None
    checkpoint = Path(args.out + ".cursor.json")
    cursor = "*"
    if args.resume:
        if not checkpoint.exists():
            log.error("--resume: no checkpoint %s", checkpoint)
            return 1
        ck = json.loads(checkpoint.read_text(encoding="utf-8"))
        if ck.get("params") != params:
            log.error("--resume: checkpoint params differ from this query; refusing")
            return 1
        cursor = ck.get("next_cursor") or ""
        resumed_from = sum(1 for _ in read_jsonl(args.out)) if Path(args.out).exists() else 0
        log.info("resuming %s from cursor %s (%d records already written)", args.out, cursor, resumed_from)
    if not args.count_only:
        try:
            with JsonlWriter(args.out, append=args.resume) as w:
                try:
                    for _total, work in iter_works(client, params, log, cursor, checkpoint):
                        if args.max_records and w.count >= args.max_records:
                            capped = True
                            break
                        w.write(work_to_record(work, f"{args.mode}:{query}"))
                        if w.count % 1000 == 0:
                            log.info("written %d", w.count)
                finally:
                    written = w.count  # also on failure: partial output is real
            if checkpoint.exists() and not capped:
                checkpoint.unlink()
        except HttpError as exc:
            error = str(exc)
            log.error("harvest aborted after %d records: %s (checkpoint kept in %s; re-run with --resume)", written, exc, checkpoint)
    print_summary(
        "openalex",
        {
            "query": query,
            "params": params,
            "mode": args.mode,
            "with_structure_block": args.with_structure_block,
            "counts": counts,
            "written": written,
            "resumed_from": resumed_from,
            "written_total": written + resumed_from,
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
