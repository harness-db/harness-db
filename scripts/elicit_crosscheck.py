"""Compare an independent Elicit systematic-review screen against HARNESS-Review screening.

Validation logic (protocol amendment 4, "Validation, in place of a second human"): a second,
independently built pipeline is given the same definition and criteria and runs its own search.
Papers it includes that our search never retrieved are a search-recall gap; papers it includes
that our screen excluded are candidate false negatives. Both are reported, not silently fixed.

Usage:
    python scripts/elicit_crosscheck.py --screen data/screening/elicit_screen.csv

The screen CSV is the abstract-screening export downloaded from the review's presigned URL.
Matching is by DOI, then arXiv id, then normalised title (exact, then rapidfuzz >= 95).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCREEN = REPO / "data" / "screening"

csv.field_size_limit(10 ** 8)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_title(t: str) -> str:
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_doi(d: str) -> str:
    d = (d or "").strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def norm_arxiv(a: str) -> str:
    m = re.search(r"(\d{4}\.\d{4,5})", (a or "").strip().lower())
    return m.group(1) if m else ""


def pick(row: dict[str, str], *names: str) -> str:
    """First non-empty value whose column name contains one of ``names`` (case-insensitive)."""
    for want in names:
        for k, v in row.items():
            if k and want in k.lower() and (v or "").strip():
                return v.strip()
    return ""


def elicit_decision(row: dict[str, str]) -> str:
    """include / exclude / unknown from whichever column the export uses."""
    v = pick(row, "screening judgement", "screening judgment", "screening decision", "decision",
             "included", "include", "status", "result").lower()
    if not v:
        return "unknown"
    if any(w in v for w in ("exclud", "not included", "fail", "false")) and "include" not in v:
        return "exclude"
    if any(w in v for w in ("includ", "pass", "true", "yes", "eligible")):
        return "include"
    if v.strip() == "no":
        return "exclude"
    return "unknown"


def kappa(a: list[str], b: list[str]) -> tuple[float, float, int]:
    n = len(a)
    if not n:
        return float("nan"), float("nan"), 0
    agree = sum(1 for x, y in zip(a, b) if x == y) / n
    labels = sorted(set(a) | set(b))
    exp = sum((a.count(lab) / n) * (b.count(lab) / n) for lab in labels)
    k = (agree - exp) / (1 - exp) if exp < 1 else float("nan")
    return k, agree, n


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--screen", type=Path, required=True, help="Elicit abstract-screening CSV export")
    p.add_argument("--candidates", type=Path, default=REPO / "data" / "raw" / "candidates.csv")
    p.add_argument("--queue", type=Path, default=SCREEN / "fulltext_queue.csv",
                   help="records our title/abstract stage forwarded to full text")
    p.add_argument("--final", type=Path, default=SCREEN / "fulltext_final_pass1.csv",
                   help="full-text decisions, if available")
    p.add_argument("--out", type=Path, default=SCREEN / "elicit_crosscheck.json")
    p.add_argument("--misses-out", type=Path, default=SCREEN / "elicit_included_not_in_pool.csv")
    args = p.parse_args(argv)

    cands = read_csv(args.candidates)
    by_doi: dict[str, dict[str, str]] = {}
    by_arxiv: dict[str, dict[str, str]] = {}
    by_title: dict[str, dict[str, str]] = {}
    for c in cands:
        if (d := norm_doi(c.get("doi", ""))):
            by_doi.setdefault(d, c)
        if (a := norm_arxiv(c.get("arxiv_id") or c.get("id", ""))):
            by_arxiv.setdefault(a, c)
        if (t := norm_title(c.get("title", ""))):
            by_title.setdefault(t, c)

    forwarded = {r["record_id"] for r in read_csv(args.queue)}
    final: dict[str, str] = {}
    if args.final.exists():
        final = {r["record_id"]: r["decision"] for r in read_csv(args.final)}

    titles = list(by_title)
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        process = None

    rows = read_csv(args.screen)
    matched: list[dict[str, str]] = []
    unmatched_included: list[dict[str, str]] = []
    pairs: list[tuple[str, str]] = []
    counts = {"elicit_rows": len(rows), "elicit_include": 0, "elicit_exclude": 0, "elicit_unknown": 0}
    match_how = {"doi": 0, "arxiv": 0, "title": 0, "fuzzy": 0, "none": 0}

    for r in rows:
        dec = elicit_decision(r)
        counts["elicit_" + dec] = counts.get("elicit_" + dec, 0) + 1
        title = pick(r, "title", "paper")
        cand = None
        how = "none"
        if (d := norm_doi(pick(r, "doi"))) and d in by_doi:
            cand, how = by_doi[d], "doi"
        if cand is None and (a := norm_arxiv(pick(r, "arxiv", "url", "link", "id"))) and a in by_arxiv:
            cand, how = by_arxiv[a], "arxiv"
        nt = norm_title(title)
        if cand is None and nt and nt in by_title:
            cand, how = by_title[nt], "title"
        if cand is None and nt and process is not None and titles:
            hit = process.extractOne(nt, titles, scorer=fuzz.ratio, score_cutoff=95)
            if hit:
                cand, how = by_title[hit[0]], "fuzzy"
        match_how[how] += 1
        if cand is None:
            if dec == "include":
                unmatched_included.append({"title": title, "doi": pick(r, "doi"), "year": pick(r, "year"),
                                           "url": pick(r, "url", "link")})
            continue
        rid = cand["id"]
        ours = "include" if rid in forwarded else "exclude"
        matched.append({"record_id": rid, "title": cand.get("title", ""), "elicit": dec,
                        "ours_title_stage": ours, "ours_fulltext": final.get(rid, ""), "matched_by": how})
        if dec in ("include", "exclude"):
            pairs.append((dec, ours))

    k, agree, n = kappa([x for x, _ in pairs], [y for _, y in pairs])
    cell = {f"elicit_{a}__ours_{b}": sum(1 for x, y in pairs if x == a and y == b)
            for a in ("include", "exclude") for b in ("include", "exclude")}
    ft: dict[str, int] = {}
    if final:
        both = [m for m in matched if m["ours_fulltext"]]
        ft = {
            "matched_with_fulltext_decision": len(both),
            "elicit_include__ours_fulltext_include": sum(
                1 for m in both if m["elicit"] == "include" and m["ours_fulltext"] == "include"),
            "elicit_include__ours_fulltext_exclude": sum(
                1 for m in both if m["elicit"] == "include" and m["ours_fulltext"] == "exclude"),
            "elicit_exclude__ours_fulltext_include": sum(
                1 for m in both if m["elicit"] == "exclude" and m["ours_fulltext"] == "include"),
        }

    out = {
        "elicit_counts": counts,
        "matched_to_our_pool": len(matched),
        "match_method": match_how,
        "title_stage_contingency": cell,
        "title_stage_agreement": None if n == 0 else round(agree, 4),
        "title_stage_kappa": None if n == 0 else round(k, 4),
        "title_stage_n": n,
        "elicit_included_not_in_our_pool": len(unmatched_included),
        "fulltext_contingency": ft,
    }
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    with args.misses_out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["title", "doi", "year", "url"])
        w.writeheader()
        w.writerows(unmatched_included)
    with (SCREEN / "elicit_crosscheck_matched.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["record_id", "title", "elicit", "ours_title_stage",
                                           "ours_fulltext", "matched_by"])
        w.writeheader()
        w.writerows(matched)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
