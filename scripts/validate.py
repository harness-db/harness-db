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

Contribution gate, for one system file (e.g. copied from contrib/TEMPLATE_system.json):

    python scripts/validate.py --system contrib/<id>.json [--strict]

validates the file against the schema (keys starting with "_" are template hints and are ignored),
lists every cell that is still unfilled, and requires each value's evidence to read
'"<verbatim quote>" (<locator>)', where a repository locator is pinned to a commit
(path:line@<hash>) and a paper locator names its section.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
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


EVIDENCE_RE = re.compile(r'^"(?P<quote>.+)"\s*\((?P<locator>.+)\)\s*$', re.DOTALL)
COMMIT_RE = re.compile(r"@(?P<hash>[0-9a-f]{7,40})\b")
PAPER_RE = re.compile(r"\b(paper|arxiv|sec\.|section|app\.|appendix|abstract|table|fig\.)",
                      re.IGNORECASE)


def _strip_hints(obj):
    """Drop template hint keys ("_help", ...) before schema validation."""
    if isinstance(obj, dict):
        return {k: _strip_hints(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_hints(v) for v in obj]
    return obj


def check_evidence(evidence: str, pinned_commit: str | None) -> tuple[list[str], list[str]]:
    """Errors and warnings for one contributed evidence string."""
    errors: list[str] = []
    warnings: list[str] = []
    m = EVIDENCE_RE.match(evidence.strip())
    if not m or not m.group("quote").strip():
        errors.append('evidence must read "<verbatim quote>" (<locator>)')
        return errors, warnings
    loc = m.group("locator").strip()
    commit = COMMIT_RE.search(loc)
    if commit:
        h = commit.group("hash")
        if pinned_commit and not (pinned_commit.startswith(h) or h.startswith(pinned_commit)):
            warnings.append(f"locator commit {h} is not the pinned commit {pinned_commit[:12]} "
                            "(fine only for a second, separately pinned repository)")
    elif loc.lower().startswith(("http://", "https://")):
        warnings.append("locator is a URL with no pinned commit; prefer path:line@<commit> "
                        "or an archived (web.archive.org) copy")
    elif not PAPER_RE.search(loc):
        errors.append("locator is neither path:line@<commit> nor a paper section "
                      "(e.g. 'arXiv:2405.15793 Sec. 3')")
    return errors, warnings


def validate_system_file(path: Path) -> tuple[list[str], list[str]]:
    """Validate one contributed system file. Returns (errors, warnings)."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {path}: {exc}"], []
    if not isinstance(raw, dict):
        return ["a system file holds one JSON object, not a list"], []
    errors: list[str] = []
    warnings: list[str] = []
    system = _strip_hints(raw)
    sid = system.get("id", "<no id>")
    if path.stem != sid:
        warnings.append(f"file name {path.name} does not match id {sid!r}")

    coding = system.get("coding") or {}
    unfilled = {k for k, c in coding.items() if isinstance(c, dict) and not c.get("not_reported")
                and not c.get("unresolved") and c.get("value") in (None, [], "")}
    for key in (k for k in coding if k in unfilled):  # schema order, not alphabetical
        errors.append(f"{sid}.{key}: not filled - give a value with evidence and confidence, "
                      "or set not_reported: true with value null")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for err in sorted(Draft202012Validator(schema).iter_errors([system]),
                      key=lambda e: list(e.absolute_path)):
        parts = [str(p) for p in err.absolute_path][1:]
        if len(parts) >= 2 and parts[0] == "coding" and parts[1] in unfilled:
            continue  # already reported above, in plainer words
        errors.append(f"schema: {sid}/{'/'.join(parts) or '<system>'}: {err.message}")

    pinned_value = (coding.get("pinned_version") or {}).get("value")
    m = re.search(r"\b([0-9a-f]{7,40})\b", pinned_value) if isinstance(pinned_value, str) else None
    pinned_commit = m.group(1) if m else None
    if (system.get("urls") or {}).get("repo") and not pinned_commit:
        errors.append(f"{sid}.pinned_version: a system with a repository must pin a commit "
                      "('<tag> @ <full commit hash> (<date>)')")

    for key, cell in coding.items():
        if not isinstance(cell, dict) or key in unfilled:
            continue
        if cell.get("unresolved"):
            if not str(cell.get("note", "")).strip():
                errors.append(f"{sid}.{key}: an unresolved cell needs a note saying what is unclear")
            continue
        if cell.get("not_reported"):
            continue
        ev = str(cell.get("evidence", ""))
        if ev.strip():  # an empty one is already a schema error
            e, w = check_evidence(ev, pinned_commit)
            errors += [f"{sid}.{key}: {x}" for x in e]
            warnings += [f"{sid}.{key}: {x}" for x in w]
        if not str(cell.get("coder", "")).strip():
            warnings.append(f"{sid}.{key}: no coder id (use your GitHub handle, e.g. gh:octocat)")

    paper_ids: set[str] = set()
    if PAPERS.exists():
        with PAPERS.open(newline="", encoding="utf-8") as f:
            paper_ids = {r["id"] for r in csv.DictReader(f)}
    for pid in system.get("papers", []):
        if pid not in paper_ids:
            warnings.append(f"{sid}: paper id {pid!r} is not in data/papers.csv yet "
                            "(a maintainer adds the row on merge)")
    if SYSTEMS.exists():
        released = {s.get("id") for s in json.loads(SYSTEMS.read_text(encoding="utf-8"))}
        if sid in released:
            warnings.append(f"{sid}: already in data/systems.json, so this is an update; "
                            "name the cells that change in the pull request")
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate HARNESS-DB data, or one contributed system.")
    ap.add_argument("--strict", action="store_true", help="also fail on warnings")
    ap.add_argument("--system", type=Path, metavar="FILE",
                    help="validate one contributed system file (contrib/<id>.json) and nothing else")
    args = ap.parse_args()

    if args.system:
        errors, warnings = validate_system_file(args.system)
        for w in warnings:
            print(f"WARN  {w}")
        for e in errors:
            print(f"ERROR {e}")
        print(f"system={args.system} errors={len(errors)} warnings={len(warnings)}")
        if errors or (args.strict and warnings):
            return 1
        print("OK")
        return 0

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

        # 4. evidence per cell (readable message). Three states, and only one of them makes a claim
        #    that needs evidence: `not_reported` says the sources are silent, `unresolved` says the
        #    coder could not settle it and claims nothing, and anything else asserts a value and must
        #    cite where it came from. An unresolved cell carrying a value would be the real error.
        for key, cell in (s.get("coding") or {}).items():
            if not isinstance(cell, dict):
                continue
            if cell.get("unresolved"):
                if cell.get("value") is not None:
                    errors.append(f"{sid}.{key}: marked unresolved but carries a value")
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
