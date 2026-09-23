#!/usr/bin/env python
"""Cohen's kappa for screening votes and for coded dimensions.

Screening (two vote columns in one CSV):
    python scripts/kappa.py votes data/screening/votes.csv --a screener1 --b screener2

Coding (two directories of per-system JSON files, one per coder, same file names):
    python scripts/kappa.py coding data/coding/c1 data/coding/c2

Multi-valued dimensions are compared as sorted joined strings (exact set match).
Cells where either coder marked not_reported count as the value "NR".
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def cohen_kappa(a: list[str], b: list[str]) -> tuple[float, float, int]:
    """Return (kappa, observed_agreement, n)."""
    if len(a) != len(b):
        raise ValueError("vectors differ in length")
    n = len(a)
    if n == 0:
        return float("nan"), float("nan"), 0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1.0:
        return 1.0, po, n
    return (po - pe) / (1 - pe), po, n


def gwet_ac1(a: list[str], b: list[str]) -> float:
    """Gwet's AC1: agreement corrected for chance without Cohen's prevalence sensitivity.

    Cohen's kappa estimates chance agreement from the marginals, so when nearly every system falls
    in one category - which is what a dimension most sources are silent about looks like - expected
    agreement approaches observed agreement and kappa collapses even though the two readings agree
    almost everywhere ("the kappa paradox", Feinstein & Cicchetti 1990; Byrt, Bishop & Carlin 1993).
    AC1 (Gwet 2008) estimates chance agreement from how evenly the categories are used instead, so a
    dimension is not marked unreliable merely for having a dominant value.
    """
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    cats = set(a) | set(b)
    q = len(cats)
    if q < 2:
        return 1.0 if po == 1.0 else 0.0
    ca, cb = Counter(a), Counter(b)
    pi = {k: (ca[k] + cb[k]) / (2 * n) for k in cats}
    pe = sum(v * (1 - v) for v in pi.values()) / (q - 1)
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def disagreement_shape(a: list[str], b: list[str]) -> tuple[float, float]:
    """(share of cells that disagree, share of those disagreements that are a not_reported flip).

    A not_reported flip - one reading says the sources are silent, the other names a value - is a
    different defect from two readings naming different values: it points at the manual's sentinel
    rule rather than at the dimension's value set, and it is repaired by re-reading, not by redefining.
    """
    diffs = [(x, y) for x, y in zip(a, b) if x != y]
    if not a:
        return float("nan"), float("nan")
    if not diffs:
        return 0.0, 0.0
    nr = sum(1 for x, y in diffs if "NR" in (x, y))
    return len(diffs) / len(a), nr / len(diffs)


def majority_share(a: list[str], b: list[str]) -> float:
    """How concentrated the dimension is: the most common label's share of all codings."""
    c = Counter(a) + Counter(b)
    return max(c.values()) / sum(c.values()) if c else float("nan")


def multilabel_kappa(a: list[str], b: list[str]) -> tuple[float, float, int]:
    """Mean per-value kappa for a multi-valued dimension, plus mean per-value agreement.

    Exact-set matching is the wrong measure for a dimension that takes several values at once: two
    readings that both say a loop is ReAct, one of them also listing a fixed pipeline around it, are
    scored as a total mismatch even though they agree on the substance. The standard treatment is to
    score each allowed value as its own present/absent decision and average, which is what this does
    (`react|tree_search` becomes two independent yes/no judgements). Reported beside the exact-match
    figure, never instead of it.
    """
    values = sorted({v for lab in a + b if lab not in ("NR", "UNRESOLVED", "None")
                     for v in lab.split("|") if v})
    if not values:
        return float("nan"), float("nan"), 0
    ks, pos = [], []
    for v in values:
        xa = ["1" if v in lab.split("|") else "0" for lab in a]
        xb = ["1" if v in lab.split("|") else "0" for lab in b]
        k, po, _ = cohen_kappa(xa, xb)
        if k == k:  # skip values neither coder ever used (kappa undefined)
            ks.append(k)
            pos.append(po)
    if not ks:
        return float("nan"), float("nan"), len(values)
    return sum(ks) / len(ks), sum(pos) / len(pos), len(values)


def norm(cell) -> str:
    if not isinstance(cell, dict):
        return str(cell)
    if cell.get("not_reported"):
        return "NR"
    v = cell.get("value")
    if isinstance(v, list):
        return "|".join(sorted(str(x) for x in v))
    return str(v)


def cmd_votes(args) -> int:
    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pairs = [(r[args.a].strip().lower(), r[args.b].strip().lower())
             for r in rows if r.get(args.a, "").strip() and r.get(args.b, "").strip()]
    a, b = [p[0] for p in pairs], [p[1] for p in pairs]
    k, po, n = cohen_kappa(a, b)
    print(f"n={n} agreement={po:.3f} kappa={k:.3f}")
    return 0


def cmd_coding(args) -> int:
    d1, d2 = Path(args.dir_a), Path(args.dir_b)
    names = sorted({p.name for p in d1.glob("*.json")} & {p.name for p in d2.glob("*.json")})
    if not names:
        print("no overlapping system files", file=sys.stderr)
        return 1
    per_dim: dict[str, tuple[list[str], list[str]]] = {}
    for name in names:
        s1 = json.loads((d1 / name).read_text(encoding="utf-8"))
        s2 = json.loads((d2 / name).read_text(encoding="utf-8"))
        for key in (s1.get("coding") or {}):
            if key not in (s2.get("coding") or {}):
                continue
            a, b = per_dim.setdefault(key, ([], []))
            a.append(norm(s1["coding"][key]))
            b.append(norm(s2["coding"][key]))
    print(f"{'dimension':28} {'n':>4} {'agree':>6} {'kappa':>6} {'AC1':>6} {'top':>5} {'NRflip':>7}  reading")
    rows, low_k, low_ac1 = [], 0, 0
    for key, (a, b) in per_dim.items():
        k, po, n = cohen_kappa(a, b)
        ac1 = gwet_ac1(a, b)
        top = majority_share(a, b)
        dis, nrflip = disagreement_shape(a, b)
        # Why a dimension scores low decides what to do about it, so name it rather than only flag it.
        if k >= args.threshold:
            reading = "reliable"
        elif ac1 >= args.threshold and po >= 0.6:
            reading = "prevalence artifact: agrees, one value dominates"
        elif nrflip >= 0.5:
            reading = "not_reported flips: sentinel rule, not the value set"
        else:
            reading = "GENUINE disagreement: revise or drop"
        low_k += k < args.threshold
        low_ac1 += ac1 < args.threshold
        mk, mpo, nvals = multilabel_kappa(a, b)
        if mk == mk and mk >= args.threshold > k:
            reading = (f"multi-valued: exact-set kappa {k:.3f} is harsh; per-value kappa {mk:.3f} "
                       f"over {nvals} values")
        rows.append({"dimension": key, "n": n, "agreement": round(po, 4), "kappa": round(k, 4),
                     "per_value_kappa": None if mk != mk else round(mk, 4),
                     "per_value_agreement": None if mpo != mpo else round(mpo, 4),
                     "ac1": round(ac1, 4), "majority_share": round(top, 4),
                     "disagreement_rate": round(dis, 4), "nr_flip_share_of_disagreements": round(nrflip, 4),
                     "reading": reading})
        print(f"{key:28} {n:4d} {po:6.3f} {k:6.3f} {ac1:6.3f} {top:5.2f} {nrflip:7.2f}  {reading}")
    genuine = [r for r in rows if r["reading"].startswith("GENUINE")]
    print(f"\nsystems={len(names)} dimensions={len(per_dim)} "
          f"below_threshold_kappa={low_k} below_threshold_ac1={low_ac1} "
          f"genuinely_unreliable={len(genuine)}")
    if genuine:
        print("revise or drop (protocol 4.4 / tracker task 33): "
              + ", ".join(r["dimension"] for r in genuine))
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"systems": len(names), "threshold": args.threshold, "dimensions": rows}, indent=2),
            encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("votes")
    v.add_argument("csv")
    v.add_argument("--a", required=True)
    v.add_argument("--b", required=True)
    v.set_defaults(fn=cmd_votes)
    c = sub.add_parser("coding")
    c.add_argument("dir_a")
    c.add_argument("dir_b")
    c.add_argument("--threshold", type=float, default=0.6)
    c.add_argument("--json", help="also write the per-dimension table as JSON")
    c.set_defaults(fn=cmd_coding)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
