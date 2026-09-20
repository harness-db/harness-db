"""Turn the independent-search includes into the PRISMA "identified via other methods" arm.

Amendment 7: an independently built pipeline, given the same definition and criteria, included 411
records, 103 of which our frozen search never retrieved. Those records cannot be added to the frozen
harvest (it is registered and dated), so they enter the review as a separate identification arm with
their own record ids, and are then fetched and screened by exactly the same full-text procedure.

Writes, without touching any frozen file:
    data/raw/elicit_supp.jsonl                 raw records (picked up by the RAW_DIR glob)
    data/raw/candidates_supplementary.csv      candidate rows for the supplementary arm alone
    data/raw/candidates_plus_supp.csv          frozen candidates + the supplementary arm
    data/screening/supplementary_queue.csv     record_id queue for fetch and screening

Usage:
    python scripts/supplementary_arm.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
SCREEN = REPO / "data" / "screening"
CANDIDATES = RAW / "candidates.csv"

csv.field_size_limit(10 ** 8)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower())).strip()


def norm_doi(d: str) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (d or "").strip().lower())


def arxiv_from_doi(doi: str) -> str:
    m = re.match(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", (doi or "").lower())
    return m.group(1) if m else ""


def record_id(row: dict[str, str], taken: set[str]) -> str:
    """arxiv:<id> when the DOI is an arXiv DOI, else a stable elicit:<hash> id."""
    ax = arxiv_from_doi(norm_doi(row.get("DOI", "")))
    if ax and f"arxiv:{ax}" not in taken:
        return f"arxiv:{ax}"
    pid = (row.get("Paper ID") or "").strip()
    key = pid or norm_title(row.get("Title", ""))
    return f"elicit:{pid}" if pid else "elicit:" + hashlib.sha256(key.encode()).hexdigest()[:12]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--screen", type=Path, default=SCREEN / "elicit_screen.csv")
    p.add_argument("--misses", type=Path, default=SCREEN / "elicit_included_not_in_pool.csv")
    p.add_argument("--candidates", type=Path, default=CANDIDATES)
    args = p.parse_args(argv)

    frozen = read_csv(args.candidates)
    cols = list(frozen[0])
    taken = {r["id"] for r in frozen}
    wanted = {norm_title(r["title"]) for r in read_csv(args.misses) if r.get("title")}

    rows, raws, seen = [], [], set()
    for r in read_csv(args.screen):
        nt = norm_title(r.get("Title", ""))
        if nt not in wanted or nt in seen:
            continue
        seen.add(nt)
        rid = record_id(r, taken)
        taken.add(rid)
        doi = norm_doi(r.get("DOI", ""))
        url = (r.get("DOI link") or "").strip() or (f"https://doi.org/{doi}" if doi else "")
        ax = arxiv_from_doi(doi) or (rid.split(":", 1)[1] if rid.startswith("arxiv:") else "")
        rows.append({c: "" for c in cols} | {
            "id": rid, "title": (r.get("Title") or "").strip(), "abstract": (r.get("Abstract") or "").strip(),
            "year": (r.get("Year") or "").strip(), "venue": (r.get("Venue") or "").strip(),
            "url": url, "source": "elicit_supp", "sources_all": "elicit_supp",
            "arxiv_id": ax, "doi": doi,
        })
        raws.append({"id": rid, "source": "elicit_supp", "title": (r.get("Title") or "").strip(),
                     "abstract": (r.get("Abstract") or "").strip(), "url": url, "doi": doi,
                     "arxiv_id": ax, "year": (r.get("Year") or "").strip(),
                     "venue": (r.get("Venue") or "").strip(),
                     "extra": {"elicit_paper_id": (r.get("Paper ID") or "").strip(),
                               "elicit_judgement": (r.get("Screening judgement") or "").strip()}})

    (RAW / "elicit_supp.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in raws), encoding="utf-8")
    for path, data in ((RAW / "candidates_supplementary.csv", rows),
                       (RAW / "candidates_plus_supp.csv", frozen + rows)):
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
    with (SCREEN / "supplementary_queue.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id"])
        w.writerows([[r["id"]] for r in rows])

    by_prefix: dict[str, int] = {}
    for r in rows:
        by_prefix[r["id"].split(":", 1)[0]] = by_prefix.get(r["id"].split(":", 1)[0], 0) + 1
    print(f"supplementary arm: {len(rows)} records ({by_prefix})")
    print(f"with arXiv ids: {sum(1 for r in rows if r['arxiv_id'])}; with DOI: {sum(1 for r in rows if r['doi'])}")
    print(f"frozen candidates {len(frozen)} + supplementary {len(rows)} = {len(frozen) + len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
