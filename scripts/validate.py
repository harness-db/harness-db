#!/usr/bin/env python
"""Validate HARNESS-DB data files. Exit code 1 on any error.

Checks
  1. data/systems.json validates against schema/harness_db.schema.json
  2. system ids are unique; every system.papers id exists in data/papers.csv
  3. every results.csv row references an existing system id
  4. every coded cell that is not not_reported carries non-empty evidence
     (the schema enforces this too; repeated here for a readable message)
  5. data/prisma_counts.json, if present, has the fields the flow diagram needs

Run: python scripts/validate.py [--strict]   (--strict also fails on warnings)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "harness_db.schema.json"
SYSTEMS = ROOT / "data" / "systems.json"
PAPERS = ROOT / "data" / "papers.csv"
RESULTS = ROOT / "data" / "results.csv"
PRISMA = ROOT / "data" / "prisma_counts.json"

PAPER_COLUMNS = ["id", "title", "authors", "year", "venue", "arxiv_id", "doi", "url",
                 "source", "included", "exclusion_reason"]
RESULT_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd",
                  "tokens", "date", "source_url", "comparable_key", "notes"]
PRISMA_FIELDS = ["identified_by_source", "duplicates_removed", "screened_title_abstract",
                 "excluded_title_abstract", "sought_full_text", "not_retrieved",
                 "assessed_full_text", "excluded_full_text", "included_papers",
                 "included_systems"]


def read_csv(path: Path, required: list[str], errors: list[str]) -> list[dict]:
    if not path.exists():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            errors.append(f"{path.name}: missing columns {missing}")
            return []
        return list(reader)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    systems = json.loads(SYSTEMS.read_text(encoding="utf-8")) if SYSTEMS.exists() else None
    if systems is None:
        errors.append("missing file: data/systems.json")
        systems = []

    # 1. schema
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(systems), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"schema: {loc}: {err.message}")

    # 2. ids and paper references
    papers = read_csv(PAPERS, PAPER_COLUMNS, errors)
    paper_ids = {p["id"] for p in papers}
    seen: set[str] = set()
    for s in systems:
        sid = s.get("id", "<no id>")
        if sid in seen:
            errors.append(f"duplicate system id: {sid}")
        seen.add(sid)
        for pid in s.get("papers", []):
            if pid not in paper_ids:
                errors.append(f"{sid}: paper id {pid!r} not in papers.csv")
        if not s.get("papers"):
            warnings.append(f"{sid}: no papers linked")

        # 4. evidence per cell (readable message)
        for key, cell in (s.get("coding") or {}).items():
            if not isinstance(cell, dict):
                continue
            if not cell.get("not_reported") and not str(cell.get("evidence", "")).strip():
                errors.append(f"{sid}.{key}: coded value without evidence")
            if cell.get("not_reported") and cell.get("value") not in (None, [], ""):
                warnings.append(f"{sid}.{key}: not_reported=true but a value is set")

    # 3. results reference systems
    results = read_csv(RESULTS, RESULT_COLUMNS, errors)
    for i, r in enumerate(results, start=2):
        if r["system_id"] not in seen:
            errors.append(f"results.csv line {i}: unknown system_id {r['system_id']!r}")
        try:
            float(r["score"])
        except ValueError:
            errors.append(f"results.csv line {i}: score {r['score']!r} is not a number")

    # 5. prisma counts
    if PRISMA.exists():
        counts = json.loads(PRISMA.read_text(encoding="utf-8"))
        for field in PRISMA_FIELDS:
            if field not in counts:
                warnings.append(f"prisma_counts.json: missing {field}")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    n_cells = sum(len(s.get("coding") or {}) for s in systems)
    print(f"systems={len(systems)} papers={len(papers)} results={len(results)} "
          f"cells={n_cells} errors={len(errors)} warnings={len(warnings)}")
    if errors or (args.strict and warnings):
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
