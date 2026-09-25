#!/usr/bin/env python
"""Cohen's kappa for screening votes and for coded dimensions.

Screening (two vote columns in one CSV):
    python scripts/kappa.py votes data/screening/votes.csv --a screener1 --b screener2

Coding (two directories of per-system JSON files, one per coder, same file names):
    python scripts/kappa.py coding data/coding/c1 data/coding/c2

Multi-valued dimensions are compared as sorted joined strings (exact set match).
Cells where either coder marked not_reported count as the value "NR".

The coding subcommand also reports a CLUSTER BOOTSTRAP interval for every coefficient
(``--bootstrap``, default 2000 draws, ``--bootstrap-seed`` fixed). The resampling unit is the
SYSTEM, not the cell: the 38 dimensions of one system are read from the same evidence by the same
prompt, so cells within a system are not independent and a cell-level interval would be too narrow.
Each draw resamples the double-coded systems with replacement, recomputes every dimension's kappa,
AC1 and per-value kappa and the three macro means, and the reported interval is the percentile
interval over draws. ``--bootstrap 0`` restores the pre-bootstrap behaviour exactly.

A pre-registered floor applied to point estimates cannot be checked by a reader, so the JSON output
carries a ``gate`` block: how many point estimates reach the threshold, and how many dimensions'
intervals still include it.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path


def cohen_kappa(a: list[str], b: list[str]) -> tuple[float, float, int]:
    """Return (kappa, observed_agreement, n).

    ``kappa`` is NaN when expected agreement is exactly 1, which happens only when both readings
    used a single category for every unit. Chance agreement is then complete, the coefficient is
    0/0, and there is no evidence of reproducibility to report. Returning 1.0 there would be a
    spurious perfect score, and it would propagate: ``multilabel_kappa`` averages a per-value kappa
    over the values a dimension uses, so a value present for every system in both readings would
    enter that mean as a 1.0 and pull it up. NaN makes the caller drop it instead.
    """
    if len(a) != len(b):
        raise ValueError("vectors differ in length")
    n = len(a)
    if n == 0:
        return float("nan"), float("nan"), 0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1.0:
        return float("nan"), po, n
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
        # Skip values with no chance-corrected estimate: ones neither coder ever used, and ones both
        # coders recorded for every system (expected agreement 1, kappa 0/0). Both would otherwise
        # distort the mean, the second by entering it as a spurious 1.0.
        if not math.isnan(k):
            ks.append(k)
            pos.append(po)
    if not ks:
        return float("nan"), float("nan"), len(values)
    return sum(ks) / len(ks), sum(pos) / len(pos), len(values)


# ------------------------------------------------------------------ cluster bootstrap intervals


def _finite(values) -> list[float]:
    return [float(v) for v in values if math.isfinite(v)]


def _percentile(values, q: float) -> float:
    """Linear-interpolated percentile over the finite draws (NumPy's default method)."""
    v = sorted(_finite(values))
    if not v:
        return float("nan")
    if len(v) == 1:
        return v[0]
    pos = q * (len(v) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return v[lo] if lo == hi else v[lo] + (v[hi] - v[lo]) * (pos - lo)


def _mean(values) -> float:
    v = _finite(values)
    return sum(v) / len(v) if v else float("nan")


def _sd(values) -> float:
    v = _finite(values)
    if len(v) < 2:
        return float("nan")
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def cluster_bootstrap(columns: dict[str, tuple[list, list]], n_systems: int, draws: int,
                      seed: int, level: float = 0.95) -> tuple[dict[str, dict], dict[str, float]]:
    """Percentile intervals for every coefficient from a bootstrap over SYSTEMS, not cells.

    ``columns`` maps a dimension key to two lists of length ``n_systems``, the two readings of that
    dimension for each double-coded system, with ``None`` where the system has no comparable cell.
    Each draw takes ``n_systems`` systems with replacement and recomputes, on that draw only, every
    dimension's exact-set Cohen's kappa, Gwet's AC1 and per-value kappa, plus the three macro means
    over dimensions. The cell is not the unit because one system's 38 cells come from one reading of
    one evidence bundle; a cell-level resample would treat them as 38 independent observations and
    report an interval several times too narrow.

    Returns (per-dimension interval dict, macro interval dict).
    """
    rng = random.Random(seed)
    keys = list(columns)
    draw_k: dict[str, list[float]] = {k: [] for k in keys}
    draw_ac1: dict[str, list[float]] = {k: [] for k in keys}
    draw_pv: dict[str, list[float]] = {k: [] for k in keys}
    macro_k: list[float] = []
    macro_ac1: list[float] = []
    macro_agree: list[float] = []
    for _ in range(draws):
        idx = [rng.randrange(n_systems) for _ in range(n_systems)]
        ks, acs, pos = [], [], []
        for key in keys:
            av, bv = columns[key]
            a = [av[i] for i in idx if av[i] is not None]
            b = [bv[i] for i in idx if bv[i] is not None]
            k, po, _ = cohen_kappa(a, b)
            ac1 = gwet_ac1(a, b)
            pv, _, _ = multilabel_kappa(a, b)
            draw_k[key].append(k)
            draw_ac1[key].append(ac1)
            draw_pv[key].append(pv)
            ks.append(k)
            acs.append(ac1)
            pos.append(po)
        macro_k.append(_mean(ks))
        macro_ac1.append(_mean(acs))
        macro_agree.append(_mean(pos))
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    per_dim = {
        key: {
            "kappa_ci_lo": _percentile(draw_k[key], lo_q),
            "kappa_ci_hi": _percentile(draw_k[key], hi_q),
            "kappa_boot_se": _sd(draw_k[key]),
            "ac1_ci_lo": _percentile(draw_ac1[key], lo_q),
            "ac1_ci_hi": _percentile(draw_ac1[key], hi_q),
            "per_value_kappa_ci_lo": _percentile(draw_pv[key], lo_q),
            "per_value_kappa_ci_hi": _percentile(draw_pv[key], hi_q),
            "n_draws_usable": len(_finite(draw_k[key])),
        }
        for key in keys
    }
    macro = {
        "mean_kappa_ci_lo": _percentile(macro_k, lo_q),
        "mean_kappa_ci_hi": _percentile(macro_k, hi_q),
        "mean_kappa_boot_se": _sd(macro_k),
        "mean_ac1_ci_lo": _percentile(macro_ac1, lo_q),
        "mean_ac1_ci_hi": _percentile(macro_ac1, hi_q),
        "mean_agreement_ci_lo": _percentile(macro_agree, lo_q),
        "mean_agreement_ci_hi": _percentile(macro_agree, hi_q),
    }
    return per_dim, macro


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
    # One column pair per dimension, aligned to the system index, so that the bootstrap can
    # resample systems rather than cells. None marks a system with no comparable cell there.
    columns: dict[str, tuple[list[str | None], list[str | None]]] = {}
    for i, name in enumerate(names):
        s1 = json.loads((d1 / name).read_text(encoding="utf-8"))
        s2 = json.loads((d2 / name).read_text(encoding="utf-8"))
        for key in (s1.get("coding") or {}):
            if key not in (s2.get("coding") or {}):
                continue
            av, bv = columns.setdefault(key, ([None] * len(names), [None] * len(names)))
            av[i] = norm(s1["coding"][key])
            bv[i] = norm(s2["coding"][key])
    per_dim: dict[str, tuple[list[str], list[str]]] = {
        key: ([x for x in av if x is not None], [x for x in bv if x is not None])
        for key, (av, bv) in columns.items()
    }
    boot_dim: dict[str, dict] = {}
    boot_macro: dict[str, float] = {}
    if args.bootstrap > 0:
        boot_dim, boot_macro = cluster_bootstrap(columns, len(names), args.bootstrap,
                                                 args.bootstrap_seed, args.ci_level)
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
        if not math.isnan(mk) and mk >= args.threshold > k:
            reading = (f"multi-valued: exact-set kappa {k:.3f} is harsh; per-value kappa {mk:.3f} "
                       f"over {nvals} values")
        row = {"dimension": key, "n": n, "agreement": round(po, 4), "kappa": round(k, 4),
               "per_value_kappa": None if math.isnan(mk) else round(mk, 4),
               "per_value_agreement": None if math.isnan(mpo) else round(mpo, 4),
               "ac1": round(ac1, 4), "majority_share": round(top, 4),
               "disagreement_rate": round(dis, 4),
               "nr_flip_share_of_disagreements": round(nrflip, 4),
               "reading": reading}
        ci = boot_dim.get(key)
        if ci:
            row.update({name: (None if math.isnan(v) else round(v, 4)) for name, v in ci.items()
                        if name != "n_draws_usable"})
            row["n_bootstrap_draws_usable"] = ci["n_draws_usable"]
            row["kappa_ci_includes_threshold"] = bool(
                row["kappa_ci_lo"] is not None and row["kappa_ci_hi"] is not None
                and row["kappa_ci_lo"] <= args.threshold <= row["kappa_ci_hi"])
        rows.append(row)
        band = ""
        if ci:
            band = f" [{ci['kappa_ci_lo']:.3f}, {ci['kappa_ci_hi']:.3f}]"
        print(f"{key:28} {n:4d} {po:6.3f} {k:6.3f}{band} {ac1:6.3f} {top:5.2f} {nrflip:7.2f}  {reading}")
    genuine = [r for r in rows if r["reading"].startswith("GENUINE")]
    print(f"\nsystems={len(names)} dimensions={len(per_dim)} "
          f"below_threshold_kappa={low_k} below_threshold_ac1={low_ac1} "
          f"genuinely_unreliable={len(genuine)}")
    if genuine:
        print("revise or drop (protocol 4.4 / tracker task 33): "
              + ", ".join(r["dimension"] for r in genuine))
    macro = {
        "mean_kappa": round(_mean([r["kappa"] for r in rows]), 4),
        "mean_ac1": round(_mean([r["ac1"] for r in rows]), 4),
        "mean_agreement": round(_mean([r["agreement"] for r in rows]), 4),
    }
    macro.update({k: (None if math.isnan(v) else round(v, 4)) for k, v in boot_macro.items()})
    straddle = [r["dimension"] for r in rows if r.get("kappa_ci_includes_threshold")]
    gate = {
        "threshold": args.threshold,
        "n_dimensions": len(rows),
        "n_point_estimates_at_or_above_threshold": sum(1 for r in rows
                                                       if r["kappa"] >= args.threshold),
        "n_intervals_including_threshold": len(straddle) if args.bootstrap > 0 else None,
        "dimensions_with_interval_including_threshold": straddle if args.bootstrap > 0 else None,
        "note": ("the registered freeze condition is a floor on the point estimate; the interval "
                 "column says for how many dimensions the point estimate's side of the floor is "
                 "not resolved by the data"),
    }
    if args.bootstrap > 0:
        print(f"\ncluster bootstrap: {args.bootstrap} draws over {len(names)} systems, seed "
              f"{args.bootstrap_seed}, {args.ci_level:.0%} percentile intervals")
        print(f"macro mean kappa {macro['mean_kappa']:.3f} "
              f"[{macro['mean_kappa_ci_lo']:.3f}, {macro['mean_kappa_ci_hi']:.3f}]; "
              f"macro mean AC1 {macro['mean_ac1']:.3f} "
              f"[{macro['mean_ac1_ci_lo']:.3f}, {macro['mean_ac1_ci_hi']:.3f}]; "
              f"macro mean agreement {macro['mean_agreement']:.3f} "
              f"[{macro['mean_agreement_ci_lo']:.3f}, {macro['mean_agreement_ci_hi']:.3f}]")
        print(f"gate: {gate['n_point_estimates_at_or_above_threshold']} of {len(rows)} point "
              f"estimates at or above {args.threshold}; {len(straddle)} dimensions' intervals "
              f"include it" + (": " + ", ".join(straddle) if straddle else ""))
    if args.json:
        out = {"systems": len(names), "threshold": args.threshold}
        if args.bootstrap > 0:
            out["bootstrap"] = {
                "draws": args.bootstrap,
                "seed": args.bootstrap_seed,
                "level": args.ci_level,
                "unit": "system",
                "method": ("cluster bootstrap: resample the double-coded systems with replacement, "
                           "recompute every dimension's exact-set Cohen's kappa, Gwet's AC1 and "
                           "per-value kappa and the three macro means on each draw, and report "
                           "percentile intervals over draws"),
                "why_the_system_is_the_unit": ("one system's 38 cells are one reading of one "
                                               "evidence bundle, so a cell-level resample would "
                                               "treat them as independent and report an interval "
                                               "several times too narrow"),
            }
        out["macro"] = macro
        out["gate"] = gate
        out["dimensions"] = rows
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
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
    c.add_argument("--bootstrap", type=int, default=2000,
                   help="cluster-bootstrap draws over systems for the intervals (0 disables, "
                        "restoring the pre-bootstrap output exactly)")
    c.add_argument("--bootstrap-seed", type=int, default=20260924,
                   help="fixed seed for the cluster bootstrap, so the intervals are reproducible")
    c.add_argument("--ci-level", type=float, default=0.95,
                   help="coverage of the percentile intervals")
    c.add_argument("--json", help="also write the per-dimension table as JSON")
    c.set_defaults(fn=cmd_coding)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
