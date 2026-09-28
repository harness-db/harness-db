"""Full-text escalation outcomes, reconstructed from the two readings on disk.

Writes data/screening/escalation_audit.json. Inputs (read-only):
  data/screening/fulltext_votes_tier1.csv   tier-1 readings (Claude Sonnet 5)
  data/screening/fulltext_votes_v2.csv      tier-2 readings (Claude Opus 5; decisive where present)
  data/screening/fulltext_final_pass1.csv   decisions of record (8,435)
  data/screening/fulltext_final_pass2.csv   the other reading of the 3,075 records read twice

Why this file exists: fulltext_report.md section 5 labels the decision of record "pass 1" and the
other reading "pass 2", so its "pass-1 includes confirmed by pass 2: 1403/2073" is includes OF RECORD
whose tier-1 reading agreed, not tier-1 includes that tier 2 confirmed. The quantity a reader needs
for the includes that stand on one reading is the audit sample: confident (medium/high) tier-1
includes that a hash sample sent to tier 2 anyway. Order of reading is taken from batch_started_at.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "data" / "screening"


def load(name: str) -> dict[str, dict]:
    with open(SCREEN / name, encoding="utf-8") as fh:
        return {r["record_id"]: r for r in csv.DictReader(fh)}


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "share": round(k / n, 4), "wilson95": wilson(k, n)}


def main() -> None:
    t1, t2 = load("fulltext_votes_tier1.csv"), load("fulltext_votes_v2.csv")
    rec, other = load("fulltext_final_pass1.csv"), load("fulltext_final_pass2.csv")

    both = set(t1) & set(t2)
    tier1_first = {k for k in both if t1[k]["batch_started_at"] < t2[k]["batch_started_at"]}
    cells = Counter((t1[k]["decision"], t1[k]["confidence"], t2[k]["decision"]) for k in tier1_first)

    def count(dec: str, confs: tuple[str, ...], out: str | None = None) -> int:
        return sum(v for (d, c, o), v in cells.items() if d == dec and c in confs and (out is None or o == out))

    confident = ("medium", "high")
    one_reading_includes = [k for k in set(t1) - set(t2) if t1[k]["decision"] == "include"]
    of_record = Counter((rec[k]["decision"], other[k]["decision"]) for k in other if k in rec)

    out = {
        "generated_by": "scripts/screening_escalation_audit.py",
        "records_read_twice": len(both),
        "tier1_first_of_those": len(tier1_first),
        "tier2_first_of_those": len(both) - len(tier1_first),
        "tier1_excludes_reread_included": rate(count("exclude", ("low",) + confident, "include"),
                                      count("exclude", ("low",) + confident)),
        "tier1_low_confidence_includes_reread_excluded": rate(count("include", ("low",), "exclude"),
                                                              count("include", ("low",))),
        "audit_sample_confident_tier1_includes_excluded": rate(count("include", confident, "exclude"),
                                                               count("include", confident)),
        "confident_tier1_includes_on_one_reading": len(one_reading_includes),
        "of_record_x_other_reading": {f"{a}|{b}": v for (a, b), v in sorted(of_record.items())},
        "note": "keys of of_record_x_other_reading: decision of record | the other reading",
    }
    (SCREEN / "escalation_audit.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
