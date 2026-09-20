"""Measure candidate coding frames against the same reference set, to justify the coded-set size.

Screening yields a census of systems that is far larger than the 150-300 the protocol planned to
code (amendment 5 introduced a coding frame for exactly this reason). Which frame to code is a
protocol decision, so it has to be made on measured trade-offs rather than on a target number:
for each candidate frame this script reports how many systems it admits, how many of the reference
systems it keeps (the only external accuracy check we have), and what share of admitted systems
are codable at all. The chosen variant is logged as a protocol amendment with this output attached.

Usage:
    python scripts/frame_variants.py [--systems data/systems_candidates.csv]
                                     [--out data/screening/frame_variants.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from system_registry import key_of, names_match, repo_key  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SYSTEMS = REPO / "data" / "systems_candidates.csv"
VALIDATION = REPO / "data" / "screening" / "validation_systems.csv"

csv.field_size_limit(10 ** 8)

# (name, minimum stars, criteria that also admit a system, require codability)
VARIANTS: list[tuple[str, int, tuple[str, ...], bool]] = [
    ("v0_registered", 100, ("catalogue", "vendor", "peer_reviewed"), False),
    ("v1_stars500", 500, ("catalogue", "vendor", "peer_reviewed"), False),
    ("v2_stars500_no_peer", 500, ("catalogue", "vendor"), False),
    ("v3_stars1000_no_peer", 1000, ("catalogue", "vendor"), False),
    ("v4_registered_codable", 100, ("catalogue", "vendor", "peer_reviewed"), True),
    ("v5_stars500_codable", 500, ("catalogue", "vendor", "peer_reviewed"), True),
    ("v6_stars500_no_peer_codable", 500, ("catalogue", "vendor"), True),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def stars_of(row: dict[str, str]) -> int:
    v = (row.get("stars") or "").strip()
    return int(v) if v.isdigit() else 0


def codable(row: dict[str, str]) -> bool:
    """Codability as recorded by full-text screening: >= 19 of 38 dimensions supportable."""
    return (row.get("codability_flag") or "") == "pass"


def admits(row: dict[str, str], min_stars: int, criteria: tuple[str, ...], need_codable: bool) -> bool:
    if need_codable and not codable(row):
        return False
    if stars_of(row) >= min_stars:
        return True
    return any((row.get("frame_" + c) or "0") == "1" for c in criteria)


def reference_matcher(systems: list[dict[str, str]], refs: list[dict[str, str]]) -> dict[str, str | None]:
    """Map each reference system to the system_id it grouped into, or None if it is absent."""
    by_repo: dict[str, str] = {}
    for s in systems:
        if (k := repo_key(s.get("repo_url") or "")):
            by_repo.setdefault(k, s["system_id"])
    found: dict[str, str | None] = {}
    for r in refs:
        sid = None
        if (k := repo_key(r.get("repo_url") or "")) and k in by_repo:
            sid = by_repo[k]
        if sid is None:
            wanted = [n for n in [r.get("name") or "", *((r.get("aliases") or "").split(";"))] if n.strip()]
            for s in systems:
                cands = [s.get("name") or "", *((s.get("name_variants") or "").split(";"))]
                if any(names_match(w, c) or (key_of(w) and key_of(w) == key_of(c))
                       for w in wanted for c in cands if c.strip()):
                    sid = s["system_id"]
                    break
        found[r["ref_id"]] = sid
    return found


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--systems", type=Path, default=SYSTEMS)
    p.add_argument("--validation", type=Path, default=VALIDATION)
    p.add_argument("--out", type=Path, default=REPO / "data" / "screening" / "frame_variants.json")
    args = p.parse_args(argv)

    systems = read_csv(args.systems)
    refs = [r for r in read_csv(args.validation) if (r.get("set") or "") == "positive"]
    matched = reference_matcher(systems, refs)
    present = {rid: sid for rid, sid in matched.items() if sid}
    by_id = {s["system_id"]: s for s in systems}

    out: dict[str, object] = {
        "systems_total": len(systems),
        "codable_total": sum(1 for s in systems if codable(s)),
        "reference_positives": len(refs),
        "reference_present_as_systems": len(present),
        "reference_absent": sorted(rid for rid, sid in matched.items() if not sid),
        "variants": {},
    }
    variants: dict[str, object] = {}
    for name, min_stars, criteria, need_codable in VARIANTS:
        admitted = [s for s in systems if admits(s, min_stars, criteria, need_codable)]
        kept = [rid for rid, sid in present.items() if sid in by_id and admits(by_id[sid], min_stars, criteria, need_codable)]
        lost = sorted(set(present) - set(kept))
        variants[name] = {
            "definition": {"min_stars": min_stars, "or_criteria": list(criteria), "require_codable": need_codable},
            "systems_admitted": len(admitted),
            "codable_admitted": sum(1 for s in admitted if codable(s)),
            "reference_kept": len(kept),
            "reference_of_present": f"{len(kept)}/{len(present)}",
            "reference_lost": lost,
        }
    out["variants"] = variants
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"{len(systems)} systems, {out['codable_total']} codable, "
          f"{len(present)}/{len(refs)} reference systems present")
    print(f"{'variant':<30}{'admitted':>10}{'codable':>9}{'refs kept':>11}")
    for name, v in variants.items():
        assert isinstance(v, dict)
        print(f"{name:<30}{v['systems_admitted']:>10}{v['codable_admitted']:>9}{v['reference_of_present']:>11}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
