"""Harvest the ACL Anthology from its bulk BibTeX export.

Downloads https://aclanthology.org/anthology+abstracts.bib.gz (about 42 MB; falls back to
anthology.bib.gz, which has no abstracts) once into ``data/raw/cache/`` (add that directory
to .gitignore; see scripts/harvest/README.md), streams it through a minimal BibTeX parser
(no extra dependency), keeps entries with ``year`` in the requested range and applies the
harness block AND LLM block as case-insensitive regexes over title + abstract.

The Anthology has no query API, so the "query" recorded is the local regex filter.

Usage:
    python scripts/harvest/acl.py --since 2022-10-01 --until 2026-08-31 --out data/raw/acl.jsonl
        [--count-only] [--refresh]   # --refresh re-downloads the archive
"""

from __future__ import annotations

import gzip
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import IO

from common import (
    CACHE_DIR,
    HARNESS_RE,
    HARNESS_TERMS,
    LLM_RE,
    LLM_TERMS,
    STRONG_RE,
    STRONG_TERMS,
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    normalize_arxiv_id,
    normalize_doi,
    now_iso,
    print_summary,
    setup_logging,
)

URLS = (
    "https://aclanthology.org/anthology+abstracts.bib.gz",
    "https://aclanthology.org/anthology.bib.gz",
)
MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ("january", "february", "march", "april", "may", "june", "july", "august",
         "september", "october", "november", "december")
    )
}

# --------------------------------------------------------------------------------------
# Minimal streaming BibTeX parser
# --------------------------------------------------------------------------------------

_ENTRY_HEAD = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.DOTALL)
_FIELD_NAME = re.compile(r"\s*(\w+)\s*=\s*", re.DOTALL)


def _read_value(text: str, i: int) -> tuple[str, int]:
    """Read a field value starting at ``i`` (brace-delimited, quoted, or bare). Return (value, next_i)."""
    n = len(text)
    if i < n and text[i] == "{":
        depth = 0
        j = i
        while j < n:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[i + 1 : j], j + 1
            j += 1
        return text[i + 1 :], n
    if i < n and text[i] == '"':
        j = i + 1
        depth = 0
        while j < n:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == '"' and depth == 0:
                return text[i + 1 : j], j + 1
            j += 1
        return text[i + 1 :], n
    m = re.compile(r"[^,}\s]+").match(text, i)
    if m:
        return m.group(0), m.end()
    return "", i


def parse_entry(chunk: str) -> tuple[str, str, dict[str, str]] | None:
    """Parse one ``@type{key, field = {...}, ...}`` chunk into (type, key, fields)."""
    m = _ENTRY_HEAD.match(chunk)
    if not m:
        return None
    etype, key = m.group(1).lower(), m.group(2)
    fields: dict[str, str] = {}
    i = m.end()
    n = len(chunk)
    while i < n:
        fm = _FIELD_NAME.match(chunk, i)
        if not fm:
            break
        name = fm.group(1).lower()
        value, i = _read_value(chunk, fm.end())
        fields[name] = value.strip()
        # skip to next comma or end
        while i < n and chunk[i] not in ",}":
            i += 1
        if i < n and chunk[i] == ",":
            i += 1
        else:
            break
    return etype, key, fields


def iter_entries(fh: IO[str]) -> Iterator[tuple[str, str, dict[str, str]]]:
    """Stream entries from a BibTeX text stream: accumulate lines between ``@`` headers."""
    buf: list[str] = []
    for line in fh:
        if line.startswith("@") and buf:
            entry = parse_entry("".join(buf))
            if entry:
                yield entry
            buf = []
        if line.startswith("@") or buf:
            buf.append(line)
    if buf:
        entry = parse_entry("".join(buf))
        if entry:
            yield entry


_TEX_ACCENT = re.compile(r"\\[`'^\"~=.uvHtcdb]\s*\{?(\w)\}?")
_TEX_CMD = re.compile(r"\\[a-zA-Z]+\s*")


def detex(s: str) -> str:
    """Strip the most common LaTeX markup from Anthology fields."""
    s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_").replace("--", "-")
    s = _TEX_ACCENT.sub(r"\1", s)
    s = _TEX_CMD.sub("", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def entry_date(fields: dict[str, str]) -> str | None:
    year = fields.get("year", "").strip()
    if not re.fullmatch(r"\d{4}", year):
        return None
    month = fields.get("month", "").strip().lower()
    mnum: int | None = None
    if month.isdigit():
        mnum = int(month) if 1 <= int(month) <= 12 else None
    elif len(month) >= 3:
        mnum = next((v for k, v in MONTHS.items() if k.startswith(month[:3])), None)
    return f"{year}-{mnum:02d}" if mnum else year


def entry_to_record(key: str, fields: dict[str, str], query: str) -> Record:
    title = detex(fields.get("title", ""))
    abstract = detex(fields.get("abstract", ""))
    authors = [detex(a) for a in re.split(r"\s+and\s+", fields.get("author", "")) if a.strip()]
    url = fields.get("url") or f"https://aclanthology.org/{key}"
    return Record(
        id=f"acl:{key}",
        source="acl",
        source_id=key,
        title=title,
        abstract=abstract,
        authors=authors,
        date=entry_date(fields),
        venue=detex(fields.get("booktitle") or fields.get("journal") or ""),
        url=url,
        doi=normalize_doi(fields.get("doi")),
        arxiv_id=normalize_arxiv_id(fields.get("eprint") or ""),
        categories=[],
        query_used=query,
        retrieved_at=now_iso(),
        extra={"publisher": detex(fields.get("publisher", ""))},
    )


# --------------------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------------------


def download(client: HttpClient, dest_dir: Path, refresh: bool, log: logging.Logger) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for url in URLS:
        dest = dest_dir / url.rsplit("/", 1)[-1]
        if dest.exists() and dest.stat().st_size > 0 and not refresh:
            log.info("using cached %s", dest)
            return dest
        try:
            log.info("downloading %s", url)
            resp = client.get(url, stream=True)
            if resp.status_code != 200:
                raise HttpError(f"HTTP {resp.status_code} for {url}")
            tmp = dest.with_suffix(".part")
            with tmp.open("wb") as fh:
                for chunk in resp.iter_content(1 << 20):
                    fh.write(chunk)
            tmp.replace(dest)
            log.info("saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
            return dest
        except (HttpError, OSError) as exc:
            last_error = exc
            log.error("download failed: %s", exc)
    raise HttpError(f"could not download the ACL Anthology bib: {last_error}")


def main(argv: list[str] | None = None) -> int:
    p = build_parser("acl", __doc__.split("\n\n")[0])
    p.add_argument("--refresh", action="store_true", help="re-download the archive")
    p.add_argument("--cache-dir", default=str(CACHE_DIR))
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    client = HttpClient(min_interval=0.5, timeout=300, logger=log)
    query = f"regex(title+abstract) harness={list(HARNESS_TERMS)} AND llm={list(LLM_TERMS)}"
    if args.waive_llm_on_strong:
        query += f" OR strong={list(STRONG_TERMS)}"

    error: str | None = None
    written = capped = False
    stats = {"entries_total": 0, "in_year_range": 0, "harness_only": 0, "llm_only": 0, "both": 0, "strong": 0, "strong_added": 0, "no_abstract": 0}
    since_y, until_y = args.since[:4], args.until[:4]
    try:
        path = download(client, Path(args.cache_dir), args.refresh, log)
        with JsonlWriter(args.out, count_only=args.count_only) as w, gzip.open(path, "rt", encoding="utf-8") as fh:
            for _etype, key, fields in iter_entries(fh):
                stats["entries_total"] += 1
                year = fields.get("year", "").strip()
                if not (since_y <= year <= until_y):
                    continue
                date = entry_date(fields)
                # month-level trim at the range ends when the month is known
                if date and len(date) == 7 and not (args.since[:7] <= date <= args.until[:7]):
                    continue
                stats["in_year_range"] += 1
                text = detex(fields.get("title", "")) + "\n" + detex(fields.get("abstract", ""))
                if not fields.get("abstract"):
                    stats["no_abstract"] += 1
                h, l = bool(HARNESS_RE.search(text)), bool(LLM_RE.search(text))
                stats["harness_only"] += h
                stats["llm_only"] += l
                strong = bool(STRONG_RE.search(text))
                stats["strong"] += strong
                keep = h and l
                if not keep and strong and args.waive_llm_on_strong:
                    keep = True
                    stats["strong_added"] += 1
                if keep:
                    stats["both"] += 1
                    if args.max_records and w.count >= args.max_records:
                        capped = True
                        continue
                    w.write(entry_to_record(key, fields, query))
            written = w.count
    except (HttpError, OSError, gzip.BadGzipFile) as exc:
        error = str(exc)
        log.error("harvest failed: %s", exc)
    print_summary(
        "acl",
        {
            "query": query,
            "counts": {"harness_block": stats["harness_only"], "llm_block": stats["llm_only"], "both": stats["both"]},
            "stats": stats,
            "written": written,
            "capped": capped,
            "max_records": args.max_records,
            "waive_llm_on_strong": args.waive_llm_on_strong,
            "error": error,
            "out": None if args.count_only else args.out,
        },
    )
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
