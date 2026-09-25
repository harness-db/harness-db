#!/usr/bin/env python
"""Write contrib/TEMPLATE_system.json, the blank system file outside contributors start from.

Every dimension in schema/dimensions.json is present, unfilled (value null, not_reported false,
empty evidence), with "_dimension" and "_allowed" hints that scripts/validate.py --system ignores.

Run:  python scripts/make_contrib_template.py [--check]
      --check exits 1 if the template on disk is not what the schema gives.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = ROOT / "schema" / "dimensions.json"
OUT = ROOT / "contrib" / "TEMPLATE_system.json"

HELP = [
    "Copy this file to contrib/<id>.json and fill every one of the 38 cells.",
    "Keys starting with '_' are hints; the validator ignores them and a maintainer strips them.",
    ("A cell is EITHER a value with evidence and confidence: set value, set evidence to "
     "'\"<verbatim quote>\" (<locator>)', add \"confidence\": \"high\" | \"medium\" | \"low\", "
     "and keep not_reported false;"),
    ("OR not_reported: true with value null, when the sources you read are silent (say in note "
     "which place, such as a config file or tool list, the sources did not include);"),
    "OR unresolved: true with value null, when you cannot decide (say why in note).",
    ("Absence is not silence: if you opened the place where the feature would be declared "
     "(config model, CLI flags, tool registry, run loop, feature list) and it is not there, "
     "code the absence value (none, ...) and quote that place; not_reported is for when no "
     "such place was in the sources (coding manual rule 5)."),
    ("Locators: path/to/file.py:LINE@<commit> for code at the pinned commit; "
     "'arXiv:<id> Sec. N' for a paper."),
    "Fill pinned_version first. Rules for each dimension: docs/coding_manual.md.",
    "Check with: python scripts/validate.py --system contrib/<id>.json",
]


def allowed(dim: dict) -> str:
    """The value hint for one dimension, in words."""
    if dim["type"] == "enum":
        vals = " | ".join(dim["values"])
        if not dim.get("multi"):
            return f"one of: {vals}"
        text = f"a list of one or more of: {vals}"
        if "none" in dim["values"]:
            text += " (never 'none' together with other values)"
        return text
    if dim["type"] == "integer":
        return "an integer >= 0"
    if dim["type"] == "date":
        return "a date, YYYY-MM-DD"
    return "a string: '<tag> @ <full commit hash> (<YYYY-MM-DD>)'"


def build(dims_doc: dict) -> dict:
    layers = {x["id"]: x["name"] for x in dims_doc["layers"]}
    coding = {
        d["key"]: {
            "_dimension": f"{d['id']} {d['name']} (layer {d['layer']}, {layers[d['layer']]})",
            "_allowed": allowed(d),
            "value": None,
            "not_reported": False,
            "evidence": "",
            "coder": "",
            "note": "",
        }
        for d in dims_doc["dimensions"]
    }
    return {
        "_help": HELP,
        "id": "your-system-id",
        "name": "",
        "version_label": "",
        "aliases": [],
        "urls": {"repo": "", "paper": "", "docs": ""},
        "papers": [],
        "notes": "",
        "coding": coding,
    }


def render(dims_doc: dict) -> str:
    return json.dumps(build(dims_doc), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the template on disk is not what the schema gives")
    args = ap.parse_args()
    text = render(json.loads(DIMENSIONS.read_text(encoding="utf-8")))
    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
        if current != text:
            print(f"{args.out} is stale; run python scripts/make_contrib_template.py")
            return 1
        print(f"{args.out} is current")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
