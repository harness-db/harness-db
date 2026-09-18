#!/usr/bin/env python
"""Merge the human's decisions.csv into triage.csv -> final title/abstract decisions.

Inputs:
    data/screening/triage.csv       from scripts/screen_triage.py
    data/screening/decisions.csv    exported by screening/screen.html
                                    (record_id, human_decision, exclusion_reason, decided_at)

Outputs:
    data/screening/screened.csv          one row per candidate: final decision and its source
    data/screening/screening_stats.json  human-vs-model kappa, verification error rates, counts
    data/prisma_counts.json              screened_title_abstract, excluded_title_abstract,
                                         sought_full_text updated in place (other keys kept)
    paper/figures/prisma_flow.{svg,pdf}  re-rendered via scripts/prisma_diagram.py

Final decision per record (first that applies):
    human decision present        include -> include; exclude -> exclude;
                                  unsure  -> include (forwarded to full text, flagged human_unsure)
    auto_decision present         rule / model_agree / model_rule (see decision_source)
    otherwise                     undecided (pending second vote or human queue not finished)

Statistics on human-decided rows (decisions.csv, one row per record, latest decided_at wins):
    kappa human vs model 1 and vs model 2, 3-class (include/exclude/unsure) and binarised
    (exclude vs forward = include or unsure), overall and per sample type;
    agreed-exclude error rate = share of `verify_exclude` records the human did NOT exclude
    (strict: human include; lenient: human include or unsure), with a Wilson 95 % CI, split by
    tier (T1 both-exclude vs T4 rule-exclude); the same for `verify_include` (human exclude).

Usage:
    python scripts/screen_merge.py [--decisions ...] [--triage ...] [--no-render]
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from kappa import cohen_kappa

HUMAN_TO_FINAL = {"include": "include", "exclude": "exclude", "unsure": "include"}
HUMAN_TO_3CLASS = {"include": "include", "exclude": "exclude", "unsure": "unsure"}
SOURCE_BY_TIER = {"T0": "rule", "T1": "model_agree", "T2": "model_agree", "T4": "model_rule", "T5": "model_tiebreak"}
SCREENED_COLUMNS = [
    "record_id", "title", "year", "source", "tier", "tier_rule", "auto_decision", "human_sample_type",
    "human_decision", "exclusion_reason", "decided_at", "final_decision", "decision_source",
]


def binarise(v: str) -> str:
    return "exclude" if v == "exclude" else "forward"


def _num(x: float) -> float | None:
    """NaN -> None so the stats file is strict JSON."""
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else x


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def load_decisions(path: Path) -> pd.DataFrame:
    """decisions.csv -> one row per record_id (latest decided_at wins); skips unknown values."""
    if not path.exists():
        return pd.DataFrame(columns=["record_id", "human_decision", "exclusion_reason", "decided_at"])
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    d["human_decision"] = d["human_decision"].str.strip().str.lower()
    d = d[d.human_decision.isin(HUMAN_TO_FINAL)]
    d = d.sort_values("decided_at").drop_duplicates("record_id", keep="last")
    return d[["record_id", "human_decision", "exclusion_reason", "decided_at"]].reset_index(drop=True)


def merge(triage: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    df = triage.fillna("").astype(str).merge(decisions, on="record_id", how="left").fillna("")
    final, source = [], []
    for r in df.itertuples(index=False):
        if r.human_decision:
            final.append(HUMAN_TO_FINAL[r.human_decision])
            source.append("human_unsure" if r.human_decision == "unsure" else "human")
        elif r.auto_decision:
            final.append(r.auto_decision)
            source.append(SOURCE_BY_TIER.get(r.tier, "model_rule"))
        else:
            final.append("")
            source.append("")
    df["final_decision"], df["decision_source"] = final, source
    return df


def _kappa_block(h: pd.DataFrame, model_col: str) -> dict:
    sub = h[h[model_col] != ""]
    a3 = sub.human_decision.map(HUMAN_TO_3CLASS).tolist()
    b3 = sub[model_col].tolist()
    k3, po3, n = cohen_kappa(a3, b3)
    k2, po2, _ = cohen_kappa([binarise(x) for x in a3], [binarise(x) for x in b3])
    return {"n": int(n), "kappa_3class": _num(k3), "agreement_3class": _num(po3), "kappa_binary": _num(k2), "agreement_binary": _num(po2)}


def _error_block(sub: pd.DataFrame, wrong_strict: set[str], wrong_lenient: set[str]) -> dict:
    n = len(sub)
    ks = int(sub.human_decision.isin(wrong_strict).sum())
    kl = int(sub.human_decision.isin(wrong_lenient).sum())
    return {
        "n_verified": n,
        "strict_errors": ks, "strict_rate": ks / n if n else None, "strict_ci95": wilson(ks, n),
        "lenient_errors": kl, "lenient_rate": kl / n if n else None, "lenient_ci95": wilson(kl, n),
    }


def stats(df: pd.DataFrame) -> dict:
    h = df[df.human_decision != ""]
    out: dict = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "n_candidates": len(df),
        "n_human_decided": len(h),
        "human_decisions": {k: int(v) for k, v in h.human_decision.value_counts().items()},
        "final_decisions": {k or "undecided": int(v) for k, v in df.final_decision.value_counts().items()},
        "decision_sources": {k or "undecided": int(v) for k, v in df.decision_source.value_counts().items()},
        "human_vs_model": {},
        "verification": {},
    }
    for label, sub in [("all", h)] + [(st, h[h.human_sample_type == st]) for st in sorted(x for x in h.human_sample_type.unique() if x)]:
        if len(sub):
            out["human_vs_model"][label] = {"model_1": _kappa_block(sub, "vote_1"), "model_2": _kappa_block(sub, "vote_2")}
    ve = h[h.human_sample_type == "verify_exclude"]
    vi = h[h.human_sample_type == "verify_include"]
    out["verification"]["agreed_exclude"] = {
        "definition": "share of verify_exclude records the human did not exclude; strict = human include, lenient = human include or unsure",
        "all": _error_block(ve, {"include"}, {"include", "unsure"}),
        "T1_both_exclude": _error_block(ve[ve.tier == "T1"], {"include"}, {"include", "unsure"}),
        "T4_rule_exclude": _error_block(ve[ve.tier == "T4"], {"include"}, {"include", "unsure"}),
        "T5_tiebreak_exclude": _error_block(ve[ve.tier == "T5"], {"include"}, {"include", "unsure"}),
    }
    out["verification"]["agreed_include"] = {
        "definition": "share of verify_include records the human excluded (strict) or did not include outright (lenient)",
        "all": _error_block(vi, {"exclude"}, {"exclude", "unsure"}),
        "T2_both_include": _error_block(vi[vi.tier == "T2"], {"exclude"}, {"exclude", "unsure"}),
        "T4_rule_include": _error_block(vi[vi.tier == "T4"], {"exclude"}, {"exclude", "unsure"}),
        "T5_tiebreak_include": _error_block(vi[vi.tier == "T5"], {"exclude"}, {"exclude", "unsure"}),
    }
    # projected excluded-in-error count = error rate x number of auto-excludes (for the paper's limitations)
    n_auto_ex = int(((df.decision_source.isin(["model_agree", "model_rule", "model_tiebreak"])) & (df.final_decision == "exclude")).sum())
    rate = out["verification"]["agreed_exclude"]["all"]["lenient_rate"]
    out["verification"]["projected_missed_by_auto_exclude"] = None if rate is None else round(rate * n_auto_ex)
    return out


def update_prisma(df: pd.DataFrame, path: Path) -> dict:
    counts = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    decided = df[df.final_decision != ""]
    complete = len(decided) == len(df)
    counts["screened_title_abstract"] = len(decided)
    counts["excluded_title_abstract"] = int((decided.final_decision == "exclude").sum())
    counts["sought_full_text"] = int((decided.final_decision == "include").sum())
    notes = counts.setdefault("_notes", {})
    notes["screening_status"] = (
        f"{'complete' if complete else 'partial'}: {len(decided):,} of {len(df):,} candidates decided at title/abstract "
        f"({int((df.decision_source == 'rule').sum()):,} by hard rule, {int((df.decision_source == 'model_agree').sum()):,} by model agreement, "
        f"{int((df.decision_source == 'model_rule').sum()):,} by rule R4, {int(df.decision_source.isin(['human', 'human_unsure']).sum()):,} by the human); "
        f"scripts/screen_merge.py {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    if complete:
        notes.pop("later_stages", None)
    path.write_text(json.dumps(counts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return counts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--triage", default=str(REPO / "data/screening/triage.csv"))
    p.add_argument("--decisions", default=str(REPO / "data/screening/decisions.csv"))
    p.add_argument("--out", default=str(REPO / "data/screening/screened.csv"))
    p.add_argument("--stats", default=str(REPO / "data/screening/screening_stats.json"))
    p.add_argument("--prisma", default=str(REPO / "data/prisma_counts.json"))
    p.add_argument("--no-render", action="store_true", help="skip prisma_diagram.py")
    args = p.parse_args(argv)

    triage = pd.read_csv(args.triage, dtype=str, keep_default_na=False)
    decisions = load_decisions(Path(args.decisions))
    unknown = set(decisions.record_id) - set(triage.record_id)
    if unknown:
        print(f"warning: {len(unknown)} decisions for record_ids not in triage.csv (ignored): {sorted(unknown)[:3]}", file=sys.stderr)
    df = merge(triage, decisions)
    df[SCREENED_COLUMNS].to_csv(args.out, index=False, encoding="utf-8", lineterminator="\n")
    st = stats(df)
    Path(args.stats).write_text(json.dumps(st, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    counts = update_prisma(df, Path(args.prisma))

    print(f"records {len(df):,}; final: " + ", ".join(f"{k}={v:,}" for k, v in st['final_decisions'].items()))
    print(f"human decided {st['n_human_decided']:,}: " + ", ".join(f"{k}={v}" for k, v in st["human_decisions"].items()))
    fmt = lambda x: "n/a" if x is None else f"{x:.3f}"
    for label, blk in st["human_vs_model"].items():
        m1, m2 = blk["model_1"], blk["model_2"]
        print(f"kappa [{label}] vs model_1 n={m1['n']} 3-class {fmt(m1['kappa_3class'])} binary {fmt(m1['kappa_binary'])}; "
              f"vs model_2 n={m2['n']} 3-class {fmt(m2['kappa_3class'])} binary {fmt(m2['kappa_binary'])}")
    ae = st["verification"]["agreed_exclude"]["all"]
    ai = st["verification"]["agreed_include"]["all"]
    print(f"agreed-exclude error: n={ae['n_verified']} strict {fmt(ae['strict_rate'])} lenient {fmt(ae['lenient_rate'])}; "
          f"agreed-include error: n={ai['n_verified']} strict {fmt(ai['strict_rate'])} lenient {fmt(ai['lenient_rate'])}")
    print(f"prisma: screened={counts['screened_title_abstract']:,} excluded={counts['excluded_title_abstract']:,} sought={counts['sought_full_text']:,} ({counts['_notes']['screening_status'].split(':')[0]})")
    if not args.no_render:
        complete = counts["screened_title_abstract"] == len(df)
        cmd = [sys.executable, str(REPO / "scripts/prisma_diagram.py"), "--counts", args.prisma] + (["--check"] if complete else [])
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        tail = (res.stdout + res.stderr).strip().splitlines()[-2:]
        print("prisma_diagram.py: " + ("ok " if res.returncode == 0 else f"exit {res.returncode} ") + " | ".join(tail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
