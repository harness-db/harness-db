"""``python -m harnessdb --summary``: print the counts a reader can check against the paper."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections.abc import Sequence

from . import __version__, load


def format_summary(s: dict) -> str:
    """Render :meth:`HarnessDB.summary` as plain ASCII text. Every number is one the paper states."""
    cells = s["cells"]

    def pct(n: int) -> str:
        return f"{100 * n / cells:5.1f}%" if cells else "  n/a"

    strata = " / ".join(f"{k} {v:,}" for k, v in s["strata"].items())
    sizes = " / ".join(f"{k} {v:,}" for k, v in s["strata_sizes"].items())
    lines = [
        f"HARNESS-DB  (harnessdb {__version__}, schema {s['schema_version']})",
        f"source                  {s['source']}",
        "",
        f"systems                 {s['systems']:>7,}",
        (f"cells                   {cells:>7,}   ({s['systems']:,} systems x {s['dimensions']} "
         f"dimensions in {s['layers']} layers)"),
        f"  coded                 {s['coded']:>7,}  {pct(s['coded'])}   (value + evidence)",
        (f"  not_reported          {s['not_reported']:>7,}  {pct(s['not_reported'])}   "
         "(documented silence, never a value)"),
        (f"  unresolved            {s['unresolved']:>7,}  {pct(s['unresolved'])}   "
         "(excluded from every rate)"),
        "",
        f"strata in the release   {strata}",
        f"sampling frame          {s['frame_size']:,} systems ({sizes})",
        (f"weight-bearing systems  {s['weight_bearing_systems']:>7,}   "
         "(every weighted estimate rests on these)"),
        f"weight 0 (out-of-sample){s['weight_zero_systems']:>7,}   (unweighted statements only)",
        "",
        (f"results                 {s['results_rows']:>7,} score rows, {s['results_systems']:,} "
         f"systems, {s['results_benchmarks']:,} benchmark names"),
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m harnessdb",
        description="HARNESS-DB loader: print the dataset's headline counts.")
    p.add_argument("--summary", action="store_true",
                   help="print the counts to check against the paper (the default action)")
    p.add_argument("--data", default=None,
                   help="repository root, data/ directory, release directory or datapackage.json")
    p.add_argument("--json", action="store_true", help="print the summary as JSON")
    p.add_argument("--version", action="version", version=f"harnessdb {__version__}")
    args = p.parse_args(argv)
    with warnings.catch_warnings():
        warnings.simplefilter("default")
        db = load(args.data)
    s = db.summary()
    print(json.dumps(s, indent=2) if args.json else format_summary(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
