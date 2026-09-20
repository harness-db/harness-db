"""Assign every system to a coding stratum and draw the samples that get coded (amendment 6).

Screening produced a census far larger than the 150-300 systems the registered protocol planned to
code. A single hard frame was the amendment-5 answer, but `scripts/frame_variants.py` shows every
frame variant trades something real: raising the star bar drops peer-reviewed research prototypes,
and requiring screening's codability flag drops 9 of 26 reference systems (the flag under-predicts
what is codable once a coder actually reads the sources - the same failure that amendment 5 was
written to fix). So instead of one frame, the census is stratified and each stratum is sampled at a
known rate, which keeps a complete high-visibility stratum AND supports weighted estimates for the
whole census.

    H (high visibility)  stars >= 500, or catalogued by a prior survey, or a vendor product.
                         Coded completely; weight 1. This is the stratum a reader expects to be
                         exhaustive, and it contains every reference system.
    P (peer reviewed)    not in H, but described in a peer-reviewed paper with a repository.
                         Random sample, weighted up to the stratum.
    O (remainder)        everything else: small or unreleased repositories, preprints, grey sources.
                         Random sample, weighted up to the stratum.

Codability is deliberately NOT a stratum criterion: it is recorded per system during coding and
reported as data availability.

Usage:
    python scripts/coding_strata.py [--p-sample 150] [--o-sample 100] [--seed strata-2026-09-20]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYSTEMS = REPO / "data" / "systems_candidates.csv"
OUT = REPO / "data" / "coding_frame.csv"
SUMMARY = REPO / "data" / "coding_frame.json"

H_MIN_STARS = 500
COLUMNS = ["system_id", "name", "version", "repo_url", "stars", "stratum", "coded", "weight",
           "codability_flag", "max_codable_count", "canonical_record_id", "member_record_ids"]

csv.field_size_limit(10 ** 8)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def stars_of(row: dict[str, str]) -> int:
    v = (row.get("stars") or "").strip()
    return int(v) if v.isdigit() else 0


def flag(row: dict[str, str], name: str) -> bool:
    return (row.get("frame_" + name) or "0") == "1"


def stratum_of(row: dict[str, str]) -> str:
    if stars_of(row) >= H_MIN_STARS or flag(row, "catalogue") or flag(row, "vendor"):
        return "H"
    return "P" if flag(row, "peer_reviewed") else "O"


def sample_hash(key: str, seed: str) -> float:
    h = hashlib.sha256(f"{seed}:{key}".encode()).hexdigest()[:12]
    return int(h, 16) / 0xFFFFFFFFFFFF


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--systems", type=Path, default=SYSTEMS)
    p.add_argument("--p-sample", type=int, default=150)
    p.add_argument("--o-sample", type=int, default=100)
    p.add_argument("--seed", default="strata-2026-09-20")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--summary", type=Path, default=SUMMARY)
    args = p.parse_args(argv)

    systems = read_csv(args.systems)
    strata: dict[str, list[dict[str, str]]] = {"H": [], "P": [], "O": []}
    for s in systems:
        strata[stratum_of(s)].append(s)

    coded: set[str] = {s["system_id"] for s in strata["H"]}
    sampled: dict[str, list[str]] = {}
    for name, n in (("P", args.p_sample), ("O", args.o_sample)):
        pool = sorted(strata[name], key=lambda s: sample_hash(s["system_id"], args.seed))
        take = pool[:min(n, len(pool))]
        sampled[name] = [s["system_id"] for s in take]
        coded |= set(sampled[name])

    weights = {"H": 1.0}
    for name in ("P", "O"):
        n = len(sampled[name])
        weights[name] = round(len(strata[name]) / n, 4) if n else 0.0

    rows = []
    for s in systems:
        st = stratum_of(s)
        is_coded = s["system_id"] in coded
        rows.append({
            "system_id": s["system_id"], "name": s.get("name", ""), "version": s.get("version", ""),
            "repo_url": s.get("repo_url", ""), "stars": s.get("stars", ""), "stratum": st,
            "coded": int(is_coded), "weight": weights[st] if is_coded else 0,
            "codability_flag": s.get("codability_flag", ""), "max_codable_count": s.get("max_codable_count", ""),
            "canonical_record_id": s.get("canonical_record_id", ""), "member_record_ids": s.get("member_record_ids", ""),
        })
    rows.sort(key=lambda r: (r["stratum"], -int(r["coded"]), r["system_id"]))
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    summary = {
        "seed": args.seed, "h_min_stars": H_MIN_STARS,
        "systems_total": len(systems),
        "strata": {k: {"size": len(v), "coded": sum(1 for r in rows if r["stratum"] == k and r["coded"]),
                       "weight": weights[k]} for k, v in strata.items()},
        "coded_total": sum(1 for r in rows if r["coded"]),
        "codable_flag_among_coded": sum(1 for r in rows if r["coded"] and r["codability_flag"] == "pass"),
    }
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.out} and {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
