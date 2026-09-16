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
    print(f"{'dimension':28} {'n':>4} {'agree':>6} {'kappa':>6}  flag")
    low = 0
    for key, (a, b) in per_dim.items():
        k, po, n = cohen_kappa(a, b)
        flag = "" if k >= args.threshold else "<-- below threshold"
        low += bool(flag)
        print(f"{key:28} {n:4d} {po:6.3f} {k:6.3f}  {flag}")
    print(f"systems={len(names)} dimensions={len(per_dim)} below_threshold={low}")
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
    c.set_defaults(fn=cmd_coding)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
