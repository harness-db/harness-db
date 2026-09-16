"""Merge all data/raw/*.jsonl harvests into data/raw/candidates.csv.

Dedupe passes (union-find over records):
  1. identical normalised DOI;
  2. identical normalised arXiv id (version stripped);
  3. normalised title (lowercase, punctuation stripped): exact match, then
     ``rapidfuzz.fuzz.ratio >= 95`` against neighbours in sorted order (window) -- near-identical
     strings sort next to each other, which keeps this O(n * window).

The canonical record of each cluster is chosen by source priority
(arxiv > acl > openreview > s2 > openalex > github) and, within a source, the longest abstract.
The output keeps ``sources_all`` (every source that hit the cluster) and prints a per-source
table: raw hits, after dedupe (clusters the source contributes to), unique to source.

Usage:
    python scripts/dedupe.py [--raw-dir data/raw] [--out data/raw/candidates.csv]
        [--threshold 95] [--window 50] [--include-snowball]
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent / "harvest"))
from common import (
    RAW_DIR,
    normalize_arxiv_id,
    normalize_doi,
    normalize_title,
    read_jsonl,
)

SOURCE_PRIORITY = {"arxiv": 0, "acl": 1, "openreview": 2, "s2": 3, "openalex": 4, "github": 5}
COLUMNS = ["id", "title", "abstract", "year", "venue", "url", "source", "sources_all", "arxiv_id", "doi"]


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def load_records(raw_dir: Path, include_snowball: bool) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.jsonl")):
        if "snowball" in path.stem and not include_snowball:
            continue
        for r in read_jsonl(path):
            r["_file"] = path.name
            recs.append(r)
    return recs


def cluster(recs: list[dict[str, Any]], threshold: float, window: int) -> tuple[UnionFind, Counter[str]]:
    uf = UnionFind(len(recs))
    merges: Counter[str] = Counter()

    by_doi: dict[str, int] = {}
    by_arxiv: dict[str, int] = {}
    by_title: dict[str, int] = {}
    for i, r in enumerate(recs):
        doi = normalize_doi(r.get("doi"))
        if doi:
            if doi in by_doi:
                uf.union(by_doi[doi], i)
                merges["doi"] += 1
            else:
                by_doi[doi] = i
    for i, r in enumerate(recs):
        aid = normalize_arxiv_id(r.get("arxiv_id")) or normalize_arxiv_id(r.get("url") or "")
        if aid:
            if aid in by_arxiv:
                uf.union(by_arxiv[aid], i)
                merges["arxiv_id"] += 1
            else:
                by_arxiv[aid] = i
    titles: list[tuple[str, int]] = []
    for i, r in enumerate(recs):
        t = normalize_title(r.get("title") or "")
        if len(t) < 10:
            continue
        if t in by_title:
            uf.union(by_title[t], i)
            merges["title_exact"] += 1
        else:
            by_title[t] = i
            titles.append((t, i))
    titles.sort()
    for k, (t, i) in enumerate(titles):
        for t2, j in titles[k + 1 : k + 1 + window]:
            if abs(len(t) - len(t2)) > max(len(t), len(t2)) * (1 - threshold / 100) + 1:
                continue
            if fuzz.ratio(t, t2) >= threshold:
                uf.union(i, j)
                merges["title_fuzzy"] += 1
    return uf, merges


def canonical(members: list[dict[str, Any]]) -> dict[str, Any]:
    return min(
        members,
        key=lambda r: (SOURCE_PRIORITY.get(r["source"], 9), -len(r.get("abstract") or ""), r["id"]),
    )


def year_of(r: dict[str, Any]) -> str:
    d = r.get("date") or ""
    return d[:4] if len(d) >= 4 and d[:4].isdigit() else ""


def build_rows(recs: list[dict[str, Any]], uf: UnionFind) -> tuple[list[dict[str, Any]], dict[str, Counter[str]]]:
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for i, r in enumerate(recs):
        groups[uf.find(i)].append(r)
    rows: list[dict[str, Any]] = []
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    for members in groups.values():
        c = canonical(members)
        sources = sorted({m["source"] for m in members})
        arxiv_id = next((normalize_arxiv_id(m.get("arxiv_id")) for m in members if m.get("arxiv_id")), None)
        doi = next((normalize_doi(m.get("doi")) for m in members if m.get("doi")), None)
        rows.append(
            {
                "id": c["id"],
                "title": c.get("title") or "",
                "abstract": c.get("abstract") or "",
                "year": year_of(c) or next((year_of(m) for m in members if year_of(m)), ""),
                "venue": c.get("venue") or next((m.get("venue") for m in members if m.get("venue")), "") or "",
                "url": c.get("url") or "",
                "source": c["source"],
                "sources_all": ";".join(sources),
                "arxiv_id": arxiv_id or "",
                "doi": doi or "",
            }
        )
        for s in sources:
            stats[s]["after_dedupe"] += 1
            if len(sources) == 1:
                stats[s]["unique"] += 1
    rows.sort(key=lambda r: (r["year"], r["title"].lower()))
    return rows, stats


def format_table(raw: Counter[str], stats: dict[str, Counter[str]], total: int) -> str:
    lines = ["| source | raw hits | after dedupe | unique to source |", "|---|---:|---:|---:|"]
    for s in sorted(raw, key=lambda s: SOURCE_PRIORITY.get(s, 9)):
        lines.append(f"| {s} | {raw[s]} | {stats[s]['after_dedupe']} | {stats[s]['unique']} |")
    lines.append(f"| **total** | {sum(raw.values())} | {total} | |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--raw-dir", default=str(RAW_DIR))
    p.add_argument("--out", default=str(RAW_DIR / "candidates.csv"))
    p.add_argument("--threshold", type=float, default=95.0)
    p.add_argument("--window", type=int, default=50)
    p.add_argument("--include-snowball", action="store_true", help="also merge *snowball*.jsonl files")
    args = p.parse_args(argv)

    recs = load_records(Path(args.raw_dir), args.include_snowball)
    raw = Counter(r["source"] for r in recs)
    for path in sorted(Path(args.raw_dir).glob("*.jsonl")):  # report empty files too
        src = path.stem
        if src not in raw and ("snowball" not in src or args.include_snowball):
            raw[src] = 0
    uf, merges = cluster(recs, args.threshold, args.window)
    rows, stats = build_rows(recs, uf)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(format_table(raw, stats, len(rows)))
    print(f"\nmerges: {dict(merges)}")
    print(f"candidates written: {len(rows)} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
