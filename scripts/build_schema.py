#!/usr/bin/env python
"""Generate schema/harness_db.schema.json from schema/dimensions.json.

dimensions.json is the single hand-edited source of truth for the coding sheet.
The JSON Schema it produces is what validate.py checks data/systems.json against.
Run:  python scripts/build_schema.py        (writes the schema)
      python scripts/build_schema.py --check (exit 1 if the committed schema is stale)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIMS_PATH = ROOT / "schema" / "dimensions.json"
OUT_PATH = ROOT / "schema" / "harness_db.schema.json"

CONFIDENCE = ["high", "medium", "low"]


def value_schema(dim: dict) -> dict:
    t = dim["type"]
    if t == "enum":
        item = {"type": "string", "enum": dim["values"]}
        if dim.get("multi"):
            return {"type": "array", "items": item, "minItems": 1, "uniqueItems": True}
        return item
    if t == "integer":
        return {"type": "integer", "minimum": 0}
    if t == "date":
        return {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
    if t == "string":
        return {"type": "string", "minLength": 1}
    raise ValueError(f"unknown dimension type {t!r} for {dim['id']}")


def cell_schema(dim: dict) -> dict:
    """One coded cell: value + evidence + confidence + not_reported + unresolved + coder.

    Rule: a cell is either not_reported=true, or unresolved=true (both may have a null value and
    carry no evidence), or it carries a non-empty evidence string and a value matching the
    dimension's type.

    The three states are deliberately distinct. ``not_reported`` is a finding: the sources were read
    and say nothing, which is what the under-reporting result (RQ4) counts. ``unresolved`` is an
    admission: the coder could not settle the cell, so nothing is claimed about the sources at all.
    Collapsing the second into the first would inflate the very rate the review reports (schema v1,
    2026-09-23; 24% of cells were unresolved after the repair pass).
    """
    return {
        "type": "object",
        "description": f"{dim['id']} {dim['name']} (layer {dim['layer']})",
        "properties": {
            "value": {"anyOf": [value_schema(dim), {"type": "null"}]},
            "evidence": {"type": "string",
                         "description": "Verbatim quote with section, URL, or path:line@commit"},
            "confidence": {"type": "string", "enum": CONFIDENCE},
            "not_reported": {"type": "boolean", "default": False},
            "unresolved": {"type": "boolean", "default": False,
                           "description": "The coder could not settle this cell; no claim is made "
                                          "about the sources. NOT the same as not_reported."},
            "coder": {"type": "string", "description": "Coder id, e.g. c1, c2, llm"},
            "note": {"type": "string"},
        },
        "required": ["value", "not_reported"],
        "additionalProperties": False,
        "if": {"anyOf": [{"properties": {"not_reported": {"const": True}}, "required": ["not_reported"]},
                         {"properties": {"unresolved": {"const": True}}, "required": ["unresolved"]}]},
        "then": {},
        "else": {
            "required": ["value", "evidence", "confidence"],
            "properties": {"evidence": {"minLength": 1}, "value": value_schema(dim)},
        },
    }


def build(dims_doc: dict) -> dict:
    dims = dims_doc["dimensions"]
    coding_props = {d["key"]: {"$ref": f"#/$defs/dim_{d['id']}"} for d in dims}
    defs = {f"dim_{d['id']}": cell_schema(d) for d in dims}

    system = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "pattern": r"^[a-z0-9][a-z0-9\-]*$",
                   "description": "Slug, versioned on major redesign, e.g. swe-agent-1x"},
            "name": {"type": "string", "minLength": 1},
            "version_label": {"type": "string"},
            "aliases": {"type": "array", "items": {"type": "string"}},
            "urls": {"type": "object",
                     "properties": {"paper": {"type": "string"}, "repo": {"type": "string"},
                                    "docs": {"type": "string"}},
                     "additionalProperties": False},
            "papers": {"type": "array", "items": {"type": "string"},
                       "description": "ids from data/papers.csv"},
            "supersedes": {"type": "string", "description": "id of the earlier major version, if any"},
            "coding": {"type": "object", "properties": coding_props,
                       "required": list(coding_props), "additionalProperties": False},
            "coded_at": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
            "notes": {"type": "string"},
        },
        "required": ["id", "name", "papers", "coding"],
        "additionalProperties": False,
    }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/harness-db/harness-db/schema/harness_db.schema.json",
        "title": "HARNESS-DB systems",
        "description": (f"Generated from schema/dimensions.json (schema_version "
                        f"{dims_doc['schema_version']}). Do not edit by hand."),
        "x-schema-version": dims_doc["schema_version"],
        "type": "array",
        "items": {"$ref": "#/$defs/system"},
        "$defs": {"system": system, **defs},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if the committed schema is stale")
    args = ap.parse_args()

    dims_doc = json.loads(DIMS_PATH.read_text(encoding="utf-8"))
    ids = [d["id"] for d in dims_doc["dimensions"]]
    keys = [d["key"] for d in dims_doc["dimensions"]]
    if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
        print("dimensions.json: duplicate id or key", file=sys.stderr)
        return 1

    text = json.dumps(build(dims_doc), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        current = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.exists() else ""
        if current != text:
            print("schema/harness_db.schema.json is stale; run: python scripts/build_schema.py",
                  file=sys.stderr)
            return 1
        print("schema up to date")
        return 0
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(ROOT)} ({len(ids)} dimensions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
