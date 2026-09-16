"""Known-item recall of the raw harvests (protocol section 6 validation rule).

Reads ``data/raw/known_items.txt`` (one ``arxiv_id<TAB>bibkey<TAB>title`` per line, ``#``
comments) and every ``data/raw/*.jsonl`` requested, and reports for each file and for the
union how many known items are present. A record matches a known item when its
``arxiv_id`` (normalised) equals the id, or when its ``url``/``source_id`` contains the id,
or when its normalised title equals the known title (title fallback for sources without
arXiv ids, e.g. OpenReview / ACL / awesome-lists).

Usage:
    python scripts/harvest/known_items.py [--raw-dir data/raw] [--known data/raw/known_items.txt]
        [--files arxiv acl openreview s2 openalex github]   # default: the six search sources
        [--include-snowball] [--include-awesome] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import RAW_DIR, normalize_arxiv_id, normalize_title, read_jsonl

SEARCH_SOURCES = ("arxiv", "acl", "openreview", "s2", "openalex", "github")


def load_known(path: Path) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        aid = normalize_arxiv_id(parts[0]) or parts[0]
        items.append((aid, parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""))
    return items


def hits_in_file(path: Path, known: list[tuple[str, str, str]]) -> dict[str, str]:
    """Map known arXiv id -> how it matched ("id" or "title") for records in ``path``."""
    by_id = {aid for aid, _, _ in known}
    by_title = {normalize_title(t): aid for aid, _, t in known if t}
    found: dict[str, str] = {}
    for rec in read_jsonl(path):
        aid = normalize_arxiv_id(rec.get("arxiv_id")) if rec.get("arxiv_id") else None
        if not aid:
            for fld in ("url", "source_id"):
                v = rec.get(fld) or ""
                if "arxiv" in v.lower():
                    aid = normalize_arxiv_id(v)
                    if aid:
                        break
        if aid and aid in by_id:
            found[aid] = "id"
            continue
        t = normalize_title(rec.get("title") or "")
        if t and t in by_title and by_title[t] not in found:
            found[by_title[t]] = "title"
    return found


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--raw-dir", default=str(RAW_DIR))
    p.add_argument("--known", default=str(RAW_DIR / "known_items.txt"))
    p.add_argument("--files", nargs="*", default=list(SEARCH_SOURCES), help="jsonl stems to include")
    p.add_argument("--include-snowball", action="store_true")
    p.add_argument("--include-awesome", action="store_true")
    p.add_argument("--json", action="store_true", help="print a JSON summary line")
    args = p.parse_args(argv)

    raw = Path(args.raw_dir)
    known = load_known(Path(args.known))
    stems = list(args.files)
    if args.include_snowball:
        stems += sorted(q.stem for q in raw.glob("*snowball*.jsonl") if q.stem not in stems)
    if args.include_awesome and "awesome" not in stems:
        stems.append("awesome")

    per_file: dict[str, dict[str, str]] = {}
    for stem in stems:
        path = raw / f"{stem}.jsonl"
        per_file[stem] = hits_in_file(path, known) if path.exists() else {}
    union: dict[str, list[str]] = {}
    for stem, found in per_file.items():
        for aid, how in found.items():
            union.setdefault(aid, []).append(f"{stem}({how})")
    n = len(known)
    print(f"known items: {n} ({args.known})")
    print("| file | found | recall |")
    print("|---|---:|---:|")
    for stem, found in per_file.items():
        print(f"| {stem} | {len(found)} | {len(found) / n:.0%} |")
    print(f"| **union** | **{len(union)}** | **{len(union) / n:.0%}** |")
    print()
    print("| arXiv id | bibkey | found in |")
    print("|---|---|---|")
    missing: list[str] = []
    for aid, key, _ in known:
        srcs = union.get(aid)
        if not srcs:
            missing.append(aid)
        print(f"| {aid} | {key} | {', '.join(srcs) if srcs else '**missing**'} |")
    print()
    print(f"missing ({len(missing)}): {' '.join(missing)}")
    if args.json:
        print("RECALL " + json.dumps({"known": n, "files": stems, "per_file": {k: len(v) for k, v in per_file.items()}, "union": len(union), "missing": missing}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
