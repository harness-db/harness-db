"""Re-derive the locator flags in data/coded/cells.csv from the stored locator strings.

Pass A ran with a locator validator that accepted only `path:line@commit` for repository evidence.
The evidence bundle strips original line numbers, so a coder cannot cite a real line: the honest
form available to it is `path@commit`, which the old rule marked `locator_shape_unrecognised`
(13% of cells). The rule now accepts that as the weaker `locator_no_line` form (amendment 8).

This rewrites only the flags column, from the locator text already on each row: no model call, no
re-reading, and every other column is untouched. Run it after a pass that used the old validator.

Usage:
    python scripts/reclassify_locators.py [--cells data/coded/cells.csv] [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_system import LOCATOR_PAPER_RE, LOCATOR_REPO_NOLINE_RE, LOCATOR_REPO_RE  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OLD = "locator_shape_unrecognised"
NEW = "locator_no_line"

csv.field_size_limit(10 ** 8)


def locator_flag(locator: str) -> str | None:
    """The flag the current rule gives this locator, or None when it is fully formed."""
    if not locator:
        return "missing_locator"
    if LOCATOR_REPO_RE.match(locator):
        return None
    if LOCATOR_REPO_NOLINE_RE.match(locator):
        return NEW
    if LOCATOR_PAPER_RE.search(locator):
        return None
    return OLD


def reflag(flags_raw: str, locator: str) -> str:
    """Replace any locator flag on the row with the one the current rule gives.

    The flags column is written as a JSON list, but an empty cell is written as an empty string;
    both are preserved as they are so re-flagging only ever changes rows whose flags really change.
    """
    raw = flags_raw or ""
    as_json = raw.strip().startswith("[")
    if as_json:
        try:
            flags = json.loads(raw)
        except json.JSONDecodeError:
            flags, as_json = [f for f in raw.split(";") if f], False
    else:
        flags = [f for f in raw.split(";") if f]
    kept = [f for f in flags if f not in (OLD, NEW, "missing_locator")]
    if (f := locator_flag(locator)):
        kept.append(f)
    if not kept:
        return raw if not flags else ("[]" if as_json else "")
    return json.dumps(kept) if as_json else ";".join(kept)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--cells", type=Path, default=REPO / "data" / "coded" / "cells.csv")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    with args.cells.open(encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        cols = r.fieldnames or []
        rows = list(r)

    before = collections.Counter()
    after = collections.Counter()
    changed = 0
    for row in rows:
        old_flags = row.get("flags") or ""
        for f in (OLD, NEW, "missing_locator"):
            if f in old_flags:
                before[f] += 1
        # a not_reported cell has nothing to cite, and the validator exempts it from the
        # quote and locator checks; leave those rows exactly as they were
        if (row.get("not_reported") or "0") in ("1", "true", "True"):
            after[""] += 0
            continue
        new_flags = reflag(old_flags, row.get("evidence_locator") or "")
        if new_flags != old_flags:
            changed += 1
        row["flags"] = new_flags
        for f in (OLD, NEW, "missing_locator"):
            if f in new_flags:
                after[f] += 1

    print(f"{len(rows)} cells; {changed} rows re-flagged")
    print(f"  before: {dict(before)}")
    print(f"  after : {dict(after)}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0

    tmp = args.cells.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(args.cells)
    print(f"wrote {args.cells}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
