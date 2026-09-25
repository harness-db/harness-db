#!/usr/bin/env python
"""Build the curated, public HARNESS-DB dataset release from this working repository.

    python scripts/release_dataset.py --version 1.0.0 --out release/

writes ``release/harness-db-1.0.0/`` and ``release/harness-db-1.0.0.zip`` (for Zenodo).

WHY a separate release build
----------------------------
The working repository holds things we may not redistribute (fetched full texts, harvested
records, screening exports, coder bundles and logs) next to the things we publish. The release is
therefore built from an ALLOW-list: every file in it is either copied from a named source or
generated here, and ``forbidden_paths`` re-checks the finished tree against the deny-list
(``data/fulltext/``, ``data/raw/``, ``data/coded/``, ``data/screening/``, ``paper/``, ``*.log``,
``*.bak``, ``*.sqlite``, scratch) so that a future edit to the allow-list cannot leak one silently.

Every data file is DERIVED from ``data/systems.json`` at build time, never hand-copied, so the
four forms (JSON, long CSV, wide CSV, Parquet when ``pyarrow`` is importable) cannot disagree:

    data/systems.json                  the release, byte for byte
    data/cells.csv                     one row per system x dimension (47,728 rows in v1.0.0)
    data/systems_wide.csv              one row per system, a value and a ``_state`` column per dimension
    data/systems.parquet, cells.parquet   the same two tables, when pyarrow is importable
    data/papers.csv                    included papers only, bibliographic fields
    data/results.csv                   reported scores (validated: every system_id is released)
    data/not_reported_by_dimension.csv regenerated here, unweighted and design-weighted
    data/reliability.csv               per-dimension inter-coder reliability with bootstrap CIs
    data/prisma_counts.json            PRISMA 2020 flow numbers (working-file paths in notes put in words)
    data/examples/                     the coding manual's two worked examples (schema-validated)

plus schema/ (dimensions, JSON Schema, generated data dictionary), docs/ (coding manual, protocol,
coding reliability, count reconciliation, schema changelog), licences, CITATION.cff, VERSION,
README.md, VALIDATION.txt, datapackage.json (Data Package v2) and CHECKSUMS.sha256.

Every cell is in exactly one of three states, and the release keeps them apart because they mean
different things: ``coded`` (a value with re-openable evidence), ``not_reported`` (the
sources were read and are silent: a FINDING, the quantity the under-reporting result counts) and
``unresolved`` (the coder could not settle it and claims nothing).

The build fails - and leaves no release directory behind - if the released ``systems.json`` does
not validate against the JSON Schema, if a system links a paper that is not released, if a result
names an unreleased system, if a CSV value does not cast to the type ``datapackage.json`` declares
for it, if any path matches the deny-list, or if a local path or a secret from ``.env`` appears in
any released file.

Reproducibility: two builds of the same data are byte-identical except for the build timestamp,
which appears only in ``datapackage.json`` (``created``) and hence in ``CHECKSUMS.sha256`` and the
zip. Pass ``--timestamp`` (or set ``SOURCE_DATE_EPOCH``) to pin it; ``date-released`` in the
released ``CITATION.cff`` is the timestamp's date.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]
PACKAGE = "harness-db"

STATE_VALUE, STATE_NR, STATE_UNRESOLVED = "coded", "not_reported", "unresolved"
STATES = (STATE_VALUE, STATE_NR, STATE_UNRESOLVED)
MULTI_SEP = "|"

#: deny-list, checked against every relative path in the finished release (posix form)
FORBIDDEN_DIR_PREFIXES = ("data/fulltext/", "data/raw/", "data/coded/", "data/screening/",
                          "data/prefill/", "data/tier3/", "data/osf/", "paper/", "screening/",
                          ".claude/", ".git/")
FORBIDDEN_SUFFIXES = (".log", ".bak", ".sqlite", ".sqlite3", ".tmp", ".lock", ".pyc")
FORBIDDEN_NAMES = ("synergy_cache.sqlite", ".env")
FORBIDDEN_SUBSTRINGS = ("scratchpad",)

CC_BY = {"name": "CC-BY-4.0", "title": "Creative Commons Attribution 4.0 International",
         "path": "https://creativecommons.org/licenses/by/4.0/"}
MIT = {"name": "MIT", "title": "MIT License", "path": "https://opensource.org/licenses/MIT"}

SYSTEM_JSON_FIELDS = ("id", "name", "version_label", "aliases", "urls", "papers", "supersedes",
                      "coding", "coded_at", "notes")
RESULT_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd",
                  "tokens", "date", "source_url", "comparable_key", "notes"]
PAPER_BIB_COLUMNS = ["id", "title", "authors", "year", "venue", "arxiv_id", "doi", "url", "source"]
UNRESOLVED_FLAGS = re.compile(r"^unresolved after the repair pass \(([^)]*)\)")

csv.field_size_limit(10 ** 8)


class ReleaseError(RuntimeError):
    """The release cannot be published as built; the message says why."""


# ----------------------------------------------------------------------------------- cell helpers


def cell_state(cell: dict) -> str:
    if cell.get("unresolved"):
        return STATE_UNRESOLVED
    if cell.get("not_reported"):
        return STATE_NR
    if cell.get("value") is None or cell.get("value") == []:
        return STATE_UNRESOLVED  # schema forbids this in the release; never invent a value
    return STATE_VALUE


def value_text(value: object) -> str:
    """One CSV cell for a coded value: lists pipe-joined in coded order, None as empty."""
    if value is None:
        return ""
    if isinstance(value, list):
        return MULTI_SEP.join(str(v) for v in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def split_evidence(evidence: str) -> tuple[str, str]:
    """Split a release evidence string back into (quote, locator).

    ``scripts/build_tables.py`` writes ``"<quote>" (<locator>)`` when it has both, and the bare
    locator when there is no quote (every such string in v1.0.0 is a path, section or URL). The
    LAST ``" (`` is the separator, so a quote that itself contains ``" (`` still splits correctly
    and a locator such as ``README.md (Installation)`` keeps its parentheses.
    """
    e = (evidence or "").strip()
    if not e:
        return "", ""
    if e.startswith('"') and e.endswith(")") and (i := e.rfind('" (')) > 0:
        return e[1:i], e[i + 3:-1]
    if len(e) >= 2 and e.startswith('"') and e.endswith('"'):
        return e[1:-1], ""
    return "", e


def cell_flags(cell: dict) -> list[str]:
    """Flags that kept an unresolved cell unresolved (recorded in its note by the release build)."""
    m = UNRESOLVED_FLAGS.match(str(cell.get("note") or ""))
    if not (cell.get("unresolved") and m):
        return []
    return [f.strip() for f in m.group(1).split(",") if f.strip()]


# ---------------------------------------------------------------------------------------- loading


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def manual_glosses(manual: str, dims: list[dict]) -> dict[str, dict[str, object]]:
    """Definition and per-value glosses for every dimension, from docs/coding_manual.md.

    The JSON Schema names the permitted values but does not gloss them; the coding manual (which is
    released alongside) is the source of the definitions. Two layouts occur: a bullet list
    ``- `value`: gloss`` (continuation lines indented) and an inline ``Values: `a` (gloss), `b```.
    """
    heads = list(re.finditer(r"^#### (\w+) (\w+) \(", manual, re.MULTILINE))
    out: dict[str, dict[str, object]] = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(manual)
        body = manual[h.end():end]
        body = body.split("\n## ", 1)[0]
        definition = ""
        if (m := re.search(r"^Definition:\s*(.+?)(?:\n\s*\n|\nValues|\nDecision)", body, re.MULTILINE | re.DOTALL)):
            definition = " ".join(m.group(1).split())
        glosses: dict[str, str] = {}
        for m in re.finditer(r"^- `([^`]+)`(?::\s*(.*(?:\n  .*)*))?", body, re.MULTILINE):
            glosses[m.group(1)] = " ".join((m.group(2) or "").split())
        if (m := re.search(r"^Values:\s*(`.+?)(?:\n\s*\n|\nDecision)", body, re.MULTILINE | re.DOTALL)):
            for v, g in re.findall(r"`([^`]+)`(?:\s*\(([^)]*)\))?", " ".join(m.group(1).split())):
                glosses.setdefault(v, g)
        out[h.group(2)] = {"id": h.group(1), "definition": definition, "values": glosses}
    return {d["key"]: out.get(d["key"], {"definition": "", "values": {}}) for d in dims}


# ------------------------------------------------------------------------------- table builders


CELL_COLUMNS = [
    ("system_id", "string", "Release id of the system (systems.json `id`)."),
    ("layer", "string", "Layer id (A-H, M); see schema/data_dictionary.md."),
    ("dimension_id", "string", "Dimension id, e.g. A1."),
    ("dimension_key", "string", "Dimension key, e.g. system_prompt_style."),
    ("state", "string", "coded | not_reported | unresolved. Exactly one per cell."),
    ("value", "string", ("The coded value when state=coded, else empty. Multi-valued dimensions are "
                        "pipe-joined (|) in coded order.")),
    ("evidence_quote", "string", ("Verbatim quote supporting the value (or the absence), without "
                                 "surrounding quotation marks; empty when only a locator was given.")),
    ("evidence_locator", "string", "Where the quote is: paper section, URL, or path:line@commit."),
    ("confidence", "string", ("high | medium | low for coded cells; empty for not_reported and "
                             "unresolved cells.")),
    ("flags", "string", ("For unresolved cells, the validator flags that kept the cell unresolved "
                        "(pipe-joined); empty otherwise.")),
    ("coder", "string", "Coder id (llm-<model>-<prompt version>)."),
    ("note", "string", "Coder's note, e.g. which source was missing for a not_reported cell."),
]
WIDE_META = [
    ("system_id", "string", "Release id of the system."),
    ("name", "string", "System name."),
    ("version", "string", "Version label the coding refers to, when one was recorded."),
    ("repo_url", "string", "Source repository URL, when known."),
    ("stratum", "string", "Sampling stratum: H (high-visibility, coded completely), P, O."),
    ("weight", "number", ("Design weight (inverse inclusion probability). 0 for the systems coded "
                         "outside the drawn sample: they count in unweighted statements only.")),
    ("primary_paper_id", "string", "The system's canonical record in papers.csv."),
    ("paper_ids", "string", "Every papers.csv id describing the system, pipe-joined."),
    ("coded_at", "date", "Date the coding was produced."),
]


def dimension_field_type(dim: dict) -> str:
    if dim.get("multi"):
        return "string"
    return {"integer": "integer", "date": "date"}.get(dim["type"], "string")


def build_cell_rows(systems: list[dict], dims: list[dict]) -> list[dict[str, str]]:
    rows = []
    for s in systems:
        coding = s.get("coding") or {}
        for d in dims:
            cell = coding.get(d["key"]) or {}
            state = cell_state(cell)
            quote, loc = split_evidence(str(cell.get("evidence") or ""))
            rows.append({
                "system_id": s["id"], "layer": d["layer"], "dimension_id": d["id"],
                "dimension_key": d["key"], "state": state,
                "value": value_text(cell.get("value")) if state == STATE_VALUE else "",
                "evidence_quote": quote, "evidence_locator": loc,
                # the source records a placeholder "low" on every not_reported cell; confidence is a
                # judgement about a value, so it is published only where there is one
                "confidence": str(cell.get("confidence") or "") if state == STATE_VALUE else "",
                "flags": MULTI_SEP.join(cell_flags(cell)),
                "coder": str(cell.get("coder") or ""), "note": str(cell.get("note") or ""),
            })
    return rows


def fmt_weight(raw: str) -> str:
    return repr(float(raw)) if str(raw).strip() else ""


def build_wide_rows(systems: list[dict], dims: list[dict], frame: dict[str, dict]
                    ) -> list[dict[str, str]]:
    rows = []
    for s in systems:
        fr = frame.get(s["id"], {})
        papers = s.get("papers") or []
        row = {
            "system_id": s["id"], "name": s.get("name", ""), "version": s.get("version_label", ""),
            "repo_url": (s.get("urls") or {}).get("repo", ""), "stratum": fr.get("stratum", ""),
            "weight": fmt_weight(fr.get("weight", "")),
            "primary_paper_id": papers[0] if papers else "",
            "paper_ids": MULTI_SEP.join(papers), "coded_at": s.get("coded_at", ""),
        }
        coding = s.get("coding") or {}
        for d in dims:
            cell = coding.get(d["key"]) or {}
            state = cell_state(cell)
            row[d["key"]] = value_text(cell.get("value")) if state == STATE_VALUE else ""
            row[f"{d['key']}_state"] = state
        rows.append(row)
    return rows


def wide_columns(dims: list[dict]) -> list[tuple[str, str, str]]:
    cols = list(WIDE_META)
    for d in dims:
        kind = "multi-valued, pipe-joined" if d.get("multi") else d["type"]
        cols.append((d["key"], dimension_field_type(d),
                     f"{d['id']} {d['name']} ({kind}); empty unless {d['key']}_state=coded."))
        cols.append((f"{d['key']}_state", "string", (f"State of {d['id']}: coded | not_reported | "
                                                    "unresolved.")))
    return cols


def build_paper_rows(papers: list[dict], systems: list[dict]) -> tuple[list[str], list[dict]]:
    """Included papers only, bibliographic fields, plus the released systems each one describes.

    A bibliographic column that is empty on every row (``authors`` in v1.0.0: the frozen candidate
    table did not carry it) is dropped rather than shipped blank, so nobody reads it as data.
    """
    described: dict[str, list[str]] = {}
    for s in systems:
        for pid in s.get("papers") or []:
            described.setdefault(pid, []).append(s["id"])
    included = [p for p in papers if str(p.get("included", "")).strip() == "1"]
    cols = [c for c in PAPER_BIB_COLUMNS if any(str(p.get(c) or "").strip() for p in included)]
    rows = []
    for p in sorted(included, key=lambda r: r["id"]):
        row = {c: str(p.get(c) or "").strip() for c in cols}
        row["system_ids"] = MULTI_SEP.join(sorted(described.get(p["id"], [])))
        rows.append(row)
    return cols + ["system_ids"], rows


def build_nr_rows(systems: list[dict], dims_doc: dict, frame_rows: list[dict]) -> list[dict]:
    """Per-dimension not_reported rate, unweighted and design-weighted, regenerated from the release.

    Uses the estimators of ``scripts/analyse_descriptives.py`` (unresolved cells leave every
    denominator; stratified SE with finite-population correction) so the released table is the one
    the paper reports, recomputed from the released systems.json rather than copied.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import analyse_descriptives as ad

    frame = {r["system_id"]: r for r in frame_rows}
    cells = ad.build_cells(systems, dims_doc, frame, {}, "candidates")
    table = ad.under_reporting_by_dimension(cells, ad.strata_sizes_from_frame(frame_rows))
    order = {d["key"]: i for i, d in enumerate(dims_doc["dimensions"])}
    table = table.assign(_o=table["key"].map(order)).sort_values("_o").drop(columns="_o")
    rows = []
    for rec in table.to_dict("records"):
        row = {}
        for k, v in rec.items():
            if isinstance(v, float):
                row[k] = "" if math.isnan(v) else repr(round(v, 6))
            else:
                row[k] = str(v)
        rows.append(row)
    return rows


def build_reliability_rows(rel: dict, dims: list[dict]) -> tuple[list[str], list[dict]]:
    by_key = {d["key"]: d for d in dims}
    entries = rel.get("dimensions") or []
    keys: list[str] = []
    for e in entries:
        keys += [k for k in e if k not in keys and k != "dimension"]
    cols = ["layer", "dimension_id", "dimension_key"] + keys
    rows = []
    for e in sorted(entries, key=lambda e: [d["key"] for d in dims].index(e["dimension"])):
        d = by_key[e["dimension"]]
        row = {"layer": d["layer"], "dimension_id": d["id"], "dimension_key": d["key"]}
        row.update({k: value_text(e.get(k)) for k in keys})
        rows.append(row)
    return cols, rows


# -------------------------------------------------------------------------------------- writers


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_text(path: Path, text: str) -> None:
    write_bytes(path, text.encode("utf-8"))


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    w.writerows(rows)
    write_text(path, buf.getvalue())


def write_parquet(path: Path, columns: list[tuple[str, str, str]], rows: list[dict]) -> None:
    """Parquet copy of a CSV table, typed like its Table Schema (empty string -> null)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    arrow = {"integer": pa.int64(), "number": pa.float64(), "date": pa.date32()}
    fields, arrays = [], []
    for name, kind, _ in columns:
        vals = [r.get(name, "") for r in rows]
        if kind == "integer":
            data = [int(v) if v != "" else None for v in vals]
        elif kind == "number":
            data = [float(v) if v != "" else None for v in vals]
        elif kind == "date":
            data = [dt.date.fromisoformat(v) if v != "" else None for v in vals]
        else:
            data = [v if v != "" else None for v in vals]
        typ = arrow.get(kind, pa.string())
        fields.append(pa.field(name, typ))
        arrays.append(pa.array(data, type=typ))
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_arrays(arrays, schema=pa.schema(fields)), str(path),
                   compression="zstd")


def pyarrow_available() -> bool:
    try:
        import pyarrow
        import pyarrow.parquet  # noqa: F401
    except ImportError:
        return False
    return True


# ------------------------------------------------------------------------------- documentation


def data_dictionary(dims_doc: dict, glosses: dict, version: str) -> str:
    layers = {lay["id"]: lay["name"] for lay in dims_doc["layers"]}
    out = [
        f"# HARNESS-DB {version} data dictionary",
        "",
        (f"Generated from `schema/dimensions.json` (schema version {dims_doc['schema_version']}) "
        "and the value definitions in `docs/coding_manual.md`. "
        f"{len(dims_doc['dimensions'])} dimensions in {len(layers)} layers; every system is coded "
        "on every dimension."),
        "",
        "## Cell states",
        "",
        ("Every cell (one system x one dimension) is in exactly one of three states. They are kept "
        "apart because they mean different things; do not merge them."),
        "",
        "| state | meaning | value | evidence |",
        "|---|---|---|---|",
        ("| `coded` | A coded value, backed by evidence a reader can re-open. | set | quote and/or "
        "locator, always |"),
        ("| `not_reported` | The sources were read and are silent on this dimension. This is a "
        "finding (it is what the under-reporting analysis counts), not missing data. | empty | "
        "usually none; sometimes the place that was checked |"),
        ("| `unresolved` | The coder could not settle the cell. Nothing is claimed about the "
        "sources. Exclude these from denominators; do not count them as not reported. | empty | "
        "none; `flags` says why |"),
        "",
        ("In `data/systems.json` the state is carried by `not_reported: true` or `unresolved: true` "
        "on the cell; a cell with neither is a coded value. In `data/cells.csv` it is the `state` "
        "column; in `data/systems_wide.csv` it is the `<key>_state` column beside each value."),
        "",
        ("Conventions in the CSV files: multi-valued dimensions are pipe-joined (`a|b`) in the "
        "order coded; for multi-valued dimensions the shipped default is listed in the cell note "
        "(coding manual rule 4); `confidence` is published for `coded` cells only and is empty "
        "for `not_reported` and `unresolved` cells in `cells.csv` (in `systems.json` the build "
        "records a placeholder `low` on every `not_reported` cell; it is not a judgement and "
        "should be ignored); `none` is a coded absence (the place where the feature would be "
        "declared was opened and it is not there), which is different from `not_reported`."),
        "",
        ("Weights: `systems_wide.csv` carries each system's sampling `stratum` and design `weight`. "
        "Weighted shares estimate the full frame; unweighted shares describe the coded set. "
        "Systems with weight 0 were coded outside the drawn sample and belong in unweighted "
        "statements only."),
        "",
        "## Dimensions",
    ]
    for lid, lname in layers.items():
        out += ["", f"### Layer {lid}: {lname}"]
        for d in (x for x in dims_doc["dimensions"] if x["layer"] == lid):
            g = glosses.get(d["key"], {})
            multi = "yes" if d.get("multi") else "no"
            out += ["", f"#### {d['id']} `{d['key']}`: {d['name']}", "",
                    f"Layer {lid} ({lname}) · type `{d['type']}` · multi-valued: {multi}"]
            if (definition := str(g.get("definition") or "")):
                out += ["", definition[:1].upper() + definition[1:]]
            if d.get("values"):
                out += ["", "| value | meaning |", "|---|---|"]
                for v in d["values"]:
                    gloss = (g.get("values") or {}).get(v) or ""
                    if not gloss and v == "none":
                        gloss = "coded absence: the feature is not present where it would be declared"
                    out.append(f"| `{v}` | {gloss.replace('|', '/') or '-'} |")
            else:
                shape = {"integer": "a non-negative integer", "date": "a date, YYYY-MM-DD",
                         "string": "free text"}.get(d["type"], d["type"])
                out += ["", f"Value: {shape}."]
    return "\n".join(out) + "\n"


def citation_for_release(text: str, version: str, released: str) -> str:
    """The repo's CITATION.cff with ``version`` and ``date-released`` set (released copy only)."""
    if not re.search(r"^version:", text, re.MULTILINE):
        raise ReleaseError("CITATION.cff has no top-level version field")
    text = re.sub(r"^version:.*$", f"version: {version}", text, count=1, flags=re.MULTILINE)
    if re.search(r"^date-released:", text, re.MULTILINE):
        text = re.sub(r"^date-released:.*$", f'date-released: "{released}"', text, count=1,
                      flags=re.MULTILINE)
    else:
        text = text.rstrip("\n") + f'\ndate-released: "{released}"\n'
    return text


def cff_field(text: str, field: str) -> str:
    m = re.search(rf'^{field}:\s*"?(.*?)"?\s*$', text, re.MULTILINE)
    return m.group(1) if m else ""


def cff_keywords(text: str) -> list[str]:
    m = re.search(r"^keywords:\n((?:\s+- .*\n)+)", text, re.MULTILINE)
    return [k.strip()[2:].strip().strip('"') for k in m.group(1).splitlines()] if m else []


def release_readme(card: str, version: str, counts: dict, parquet: bool) -> str:
    """The release README: the Hugging Face dataset card (DATASET_CARD.md, YAML front matter and
    ``configs`` intact, so uploading the release directory is a complete dataset repo) followed by
    the notes this build generates under "## Release notes"."""
    if not card.startswith("---\n"):
        raise ReleaseError("DATASET_CARD.md must start with YAML front matter (---)")
    c = counts
    fmt = ("JSON (`data/systems.json`), CSV (`data/cells.csv`, `data/systems_wide.csv` and the "
           "companion tables)")
    fmt += (", and Parquet (`data/cells.parquet`, `data/systems.parquet`, the same two tables)."
            if parquet else ". Parquet was not built: pyarrow was not importable at build time.")

    def pct(n: int) -> str:
        return f"{100 * n / c['cells']:.2f}%"

    notes = f"""
## Release notes

Generated by `scripts/release_dataset.py` for HARNESS-DB {version}. Every table is derived from
`data/systems.json` at build time; `VALIDATION.txt` records the checks and `CHECKSUMS.sha256`
lists a SHA-256 for every file (`sha256sum -c CHECKSUMS.sha256`).

### Formats in this build

{fmt} `datapackage.json` is a Frictionless Data Package (v2) descriptor giving every column's
type. Read the CSVs with `pd.read_csv(path, keep_default_na=False)` so empty cells stay empty
strings and no text value is read as NaN.

### Validation counts

| quantity | count |
|---|---:|
| systems | {c['systems']:,} |
| dimensions | {c['dimensions']} (in {c['layers']} layers) |
| cells | {c['cells']:,} |
| `{STATE_VALUE}` | {c[STATE_VALUE]:,} ({pct(c[STATE_VALUE])}) |
| `{STATE_NR}` | {c[STATE_NR]:,} ({pct(c[STATE_NR])}) |
| `{STATE_UNRESOLVED}` | {c[STATE_UNRESOLVED]:,} ({pct(c[STATE_UNRESOLVED])}) |
| weight-bearing systems | {c['weighted_systems']:,} ({c['weight_zero']} at weight 0) |

`confidence` is published on `{STATE_VALUE}` cells only; it is empty for `{STATE_NR}` and
`{STATE_UNRESOLVED}` cells.

### Reading prisma_counts.json

`included_systems` ({c['frame_size']:,}) is the number of systems screening produced: the sampling
frame. The coded, released dataset is a stratified sample of that frame: {c['systems']:,} systems.
The two numbers are not in conflict. Notes in the released copy describe working files of the
source repository in words rather than by path; the numbers are unchanged.
`docs/count_reconciliation.md` reconciles every count.

### Third-party content

Full texts of the reviewed papers, harvested search records and screening exports are not part of
this release: they are third-party content we cannot redistribute. The evidence quotes in the cells
are short verbatim excerpts from the cited papers and repositories, included so every coded value
can be checked; they remain the work of their authors and are not covered by the CC BY licence.
"""
    return card.rstrip("\n") + "\n" + notes


# ------------------------------------------------------------------------------- package descriptor


def table_schema(columns: list[tuple[str, str, str]], primary_key=None, foreign_keys=None,
                 enums: dict[str, list[str]] | None = None) -> dict:
    fields = []
    for name, kind, desc in columns:
        f = {"name": name, "type": kind, "description": desc}
        if enums and name in enums:
            f["constraints"] = {"enum": enums[name]}
        fields.append(f)
    schema: dict = {"fields": fields, "missingValues": [""]}
    if primary_key:
        schema["primaryKey"] = primary_key
    if foreign_keys:
        schema["foreignKeys"] = foreign_keys
    return schema


def infer_columns(columns: list[str], types: dict[str, str], descs: dict[str, str]
                  ) -> list[tuple[str, str, str]]:
    return [(c, types.get(c, "string"), descs.get(c, "")) for c in columns]


def cast_ok(value: str, kind: str) -> bool:
    if value == "":
        return True
    try:
        if kind == "integer":
            int(value)
        elif kind == "number":
            float(value)
        elif kind == "date":
            dt.date.fromisoformat(value)
        elif kind == "boolean":
            return value in ("true", "false")
    except ValueError:
        return False
    return True


def check_types(name: str, columns: list[tuple[str, str, str]], rows: list[dict]) -> list[str]:
    errs = []
    for col, kind, _ in columns:
        if kind == "string":
            continue
        bad = [r[col] for r in rows if not cast_ok(r.get(col, ""), kind)]
        if bad:
            errs.append(f"{name}.{col}: {len(bad)} values do not cast to {kind}, e.g. {bad[0]!r}")
    return errs


#: shipped so the coding manual's cross-references resolve
EXTRA_DOCS = ("coding_reliability.md", "count_reconciliation.md", "schema_changelog.md")
EXAMPLES = ("README.md", "openhands.json", "swe-agent-1x.json")
RELEASED_DOCS = frozenset({"docs/coding_manual.md", "docs/protocol_prisma_p.md",
                           *(f"docs/{d}" for d in EXTRA_DOCS)})
DATAPACKAGE_V2 = "https://datapackage.org/profiles/2.0/datapackage.json"

#: working-file paths named in data/prisma_counts.json notes, and how the released copy says them
PATH_TOKEN = re.compile(r"\b(?:data|scripts|docs|paper)/[\w./*-]*\w|\b[\w-]+\.(?:jsonl|csv|json|md|py|ris)\b")
PATH_WORDS = {
    "data/raw/*.jsonl": "the per-source harvest files",
    "data/raw/search_log.md": "the search log",
    "data/raw/candidates.csv": "the deduplicated candidate table",
    "data/screening/fulltext_queue.csv": "the full-text screening queue",
    "data/screening/fulltext_final_pass1.csv": "the full-text screening decisions",
    "data/screening/elicit_crosscheck.json": "the Elicit cross-check",
    "elicit_disagreement_queue.csv": "the Elicit disagreement queue",
    "data/systems_candidates.csv": "the system census table",
    "data/coding_frame.csv": "the sampling frame table",
    "data/prisma_counts_pre_regroup.json": "the pre-regrouping PRISMA counts",
}


def path_in_words(token: str, released: frozenset[str]) -> str:
    """A released file keeps its path; a working file is described instead of named."""
    if token in released:
        return token
    if token in PATH_WORDS:
        return PATH_WORDS[token]
    if (m := re.fullmatch(r"scripts/(\w+)\.py", token)):
        return f"the source repository's {m.group(1)} script"
    if (m := re.fullmatch(r"([\w-]+)\.jsonl", token)):
        return f"the {m.group(1)} harvest file"
    if token.startswith("data/raw/"):
        return "the raw harvest records"
    if token.startswith("data/screening/"):
        return "the screening records"
    return "an internal working file"


def released_prisma(counts: dict, released: frozenset[str]) -> str:
    """data/prisma_counts.json for the release: numbers untouched, working-file paths in words."""
    def fix(o):
        if isinstance(o, dict):
            return {k: fix(v) for k, v in o.items()}
        if isinstance(o, list):
            return [fix(v) for v in o]
        if isinstance(o, str):
            return PATH_TOKEN.sub(lambda m: path_in_words(m.group(0), released), o)
        return o

    out = fix(counts)
    out["_release_note"] = ("Released copy: notes that named working files of the source "
                            "repository describe them in words instead; every number is "
                            "unchanged. included_systems is the sampling frame; the released "
                            "coded sample is the systems in data/systems.json.")
    return json.dumps(out, indent=1, ensure_ascii=False) + "\n"


def stratum_order(strata: Counter) -> list[str]:
    """H, P, O (the order the paper reports them), then anything else, sorted."""
    known = [k for k in ("H", "P", "O") if k in strata]
    return known + sorted(k for k in strata if k and k not in known)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------- auditing


def forbidden_paths(paths) -> list[str]:
    """Every relative path (posix) that the deny-list forbids in a public release."""
    bad = []
    for p in paths:
        rel = str(PurePosixPath(p))
        low = rel.lower()
        name = low.rsplit("/", 1)[-1]
        if (any(low.startswith(d) or f"/{d}" in low for d in FORBIDDEN_DIR_PREFIXES)
                or low.endswith(FORBIDDEN_SUFFIXES) or name in FORBIDDEN_NAMES
                or any(s in low for s in FORBIDDEN_SUBSTRINGS)):
            bad.append(rel)
    return bad


def tree_files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


SECRET_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL", re.IGNORECASE)


def env_secrets(repo: Path) -> list[str]:
    """Values of the secret-bearing variables in .env (keys, tokens, passwords; not usernames,
    which may legitimately be the public author e-mail in CITATION.cff)."""
    env = repo / ".env"
    if not env.exists():
        return []
    vals = []
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if SECRET_NAME.search(k) and len(v) >= 8:
                vals.append(v)
    return vals


def leak_problems(root: Path, repo: Path) -> list[str]:
    """Local absolute paths or .env secret values inside any released text file."""
    needles = [str(repo), repo.as_posix(), str(Path.home()), Path.home().as_posix()]
    needles = [n for n in dict.fromkeys(needles) if len(n) > 3]
    secrets = env_secrets(repo)
    out = []
    for rel in tree_files(root):
        if rel.endswith(".parquet"):
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        for n in needles:
            if n.lower() in low or n.lower().replace("\\", "\\\\") in low:
                out.append(f"{rel}: contains the local path {n!r}")
        for s in secrets:
            if s in text:
                out.append(f"{rel}: contains a value from .env")
    return out


# ------------------------------------------------------------------------------------- the build


def parse_timestamp(raw: str | None) -> dt.datetime:
    if raw:
        ts = dt.datetime.fromisoformat(raw)
        return (ts if ts.tzinfo else ts.replace(tzinfo=dt.UTC)).astimezone(dt.UTC)
    if (epoch := os.environ.get("SOURCE_DATE_EPOCH")):
        return dt.datetime.fromtimestamp(int(epoch), tz=dt.UTC)
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def make_zip(root: Path, zip_path: Path, ts: dt.datetime) -> None:
    """Deterministic zip: sorted entries, fixed mtimes and permissions, top folder = release name."""
    stamp = max(ts, dt.datetime(1980, 1, 1, tzinfo=dt.UTC)).timetuple()[:6]
    tmp = zip_path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in tree_files(root):
            info = zipfile.ZipInfo(f"{root.name}/{rel}", date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            zf.writestr(info, (root / rel).read_bytes(), compresslevel=9)
    os.replace(tmp, zip_path)


def validate_version(version: str) -> str:
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        raise ReleaseError(f"--version {version!r} is not a semantic version (e.g. 1.0.0)")
    return version


def build(version: str, out: Path, timestamp: str | None = None, repo: Path = REPO,
          quiet: bool = False) -> Path:
    """Build ``<out>/harness-db-<version>/`` and its zip; return the release directory."""
    version = validate_version(version)
    out = out.resolve()
    for guarded in (repo / "data", repo / "paper"):
        if out == guarded.resolve() or guarded.resolve() in out.parents:
            raise ReleaseError(f"--out {out} is inside {guarded}; the release never writes there")
    ts = parse_timestamp(timestamp)
    released_on = ts.date().isoformat()
    say = (lambda *a: None) if quiet else (lambda *a: print(*a))

    name = f"{PACKAGE}-{version}"
    final, stage = out / name, out / f".{name}.building"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        counts = _build_into(stage, version, ts, released_on, repo, say)
        if (bad := forbidden_paths(tree_files(stage))):
            raise ReleaseError("forbidden paths in the release: " + ", ".join(bad))
        if (leaks := leak_problems(stage, repo)):
            raise ReleaseError("leak check failed:\n  " + "\n  ".join(leaks))
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    if final.exists():
        shutil.rmtree(final)
    os.replace(stage, final)
    zip_path = out / f"{name}.zip"
    make_zip(final, zip_path, ts)
    say(f"release: {final}")
    say(f"zip    : {zip_path} ({zip_path.stat().st_size:,} bytes)")
    say(f"counts : {counts['systems']:,} systems, {counts['cells']:,} cells "
        f"(coded {counts[STATE_VALUE]:,} / not_reported {counts[STATE_NR]:,} / "
        f"unresolved {counts[STATE_UNRESOLVED]:,})")
    if not counts["parquet"]:
        say("parquet: SKIPPED - pyarrow is not importable; install pyarrow and rebuild to add "
            "data/systems.parquet and data/cells.parquet")
    return final


def _build_into(root: Path, version: str, ts: dt.datetime, released_on: str, repo: Path,
                say) -> dict:
    src = {
        "systems": repo / "data" / "systems.json",
        "papers": repo / "data" / "papers.csv",
        "results": repo / "data" / "results.csv",
        "prisma": repo / "data" / "prisma_counts.json",
        "frame": repo / "data" / "coding_frame.csv",
        "reliability": repo / "data" / "coded" / "reliability_final.json",
        "dims": repo / "schema" / "dimensions.json",
        "schema": repo / "schema" / "harness_db.schema.json",
        "manual": repo / "docs" / "coding_manual.md",
        "protocol": repo / "docs" / "protocol_prisma_p.md",
        "citation": repo / "CITATION.cff",
        "license_data": repo / "LICENSE-DATA",
        "license_code": repo / "LICENSE-CODE",
        "card": repo / "DATASET_CARD.md",
    }
    extra = [repo / "docs" / d for d in EXTRA_DOCS] + [repo / "data" / "examples" / e
                                                       for e in EXAMPLES]
    if (missing := [str(p.relative_to(repo)) for p in [*src.values(), *extra] if not p.exists()]):
        raise ReleaseError("missing source files: " + ", ".join(missing))

    systems_bytes = src["systems"].read_bytes()
    systems = json.loads(systems_bytes.decode("utf-8"))
    dims_doc, schema = read_json(src["dims"]), read_json(src["schema"])
    dims = dims_doc["dimensions"]

    # 1. the release must validate before anything is derived from it
    errors = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
              for e in Draft202012Validator(schema).iter_errors(systems)]
    if errors:
        raise ReleaseError(f"systems.json fails the JSON Schema ({len(errors)} errors):\n  "
                           + "\n  ".join(errors[:20]))
    ids = [s["id"] for s in systems]
    if len(set(ids)) != len(ids):
        raise ReleaseError("duplicate system ids in systems.json")
    write_bytes(root / "data" / "systems.json", systems_bytes)

    # 2. long and wide forms
    frame_rows = read_csv(src["frame"])
    frame = {r["system_id"]: r for r in frame_rows}
    cell_rows = build_cell_rows(systems, dims)
    wide_rows = build_wide_rows(systems, dims, frame)
    cell_cols = list(CELL_COLUMNS)
    wide_cols = wide_columns(dims)

    # 3. companion tables
    paper_cols, paper_rows = build_paper_rows(read_csv(src["papers"]), systems)
    released_papers = {r["id"] for r in paper_rows}
    dangling = sorted({f"{s['id']}->{p}" for s in systems for p in s["papers"]
                       if p not in released_papers})
    if dangling:
        raise ReleaseError(f"{len(dangling)} system->paper links point at unreleased papers, e.g. "
                           + ", ".join(dangling[:5]))
    result_src = read_csv(src["results"])
    unknown = sorted({r["system_id"] for r in result_src if r["system_id"] not in set(ids)})
    if unknown:
        raise ReleaseError(f"results.csv names {len(unknown)} unreleased systems, e.g. {unknown[:5]}")
    result_rows = [{c: r.get(c, "") for c in RESULT_COLUMNS} for r in result_src]
    nr_rows = build_nr_rows(systems, dims_doc, frame_rows)
    rel_cols, rel_rows = build_reliability_rows(read_json(src["reliability"]), dims)

    paper_desc = {
        "id": "Record id (source:key); systems.json `papers` refers to it.",
        "title": "Title.", "authors": "Authors.", "year": "Publication year.",
        "venue": "Venue.", "arxiv_id": "arXiv id.", "doi": "DOI.", "url": "URL.",
        "source": "Identification source (arxiv, s2, openalex, acl, github, awesome, leaderboard, "
                  "snowball, ...).",
        "system_ids": "Released systems this paper describes, pipe-joined (empty: the paper's "
                      "system was not in the coded sample).",
    }
    paper_columns = infer_columns(paper_cols, {"year": "integer"}, paper_desc)
    result_desc = {
        "system_id": "Released system id.", "model": "Backbone model as reported.",
        "benchmark": "Benchmark.", "split": "Split or subset.", "metric": "Metric as reported.",
        "score": "Reported score, in the metric's own units.", "cost_usd": "Reported cost (USD).",
        "tokens": "Reported token count.", "date": "Date of the result (YYYY, YYYY-MM or YYYY-MM-DD).",
        "source_url": "Where the score was reported.",
        "comparable_key": "Rows sharing benchmark, split and model share this key; empty = not "
                          "comparable across systems.",
        "notes": "Extraction notes, including why a row is not comparable.",
    }
    result_columns = infer_columns(RESULT_COLUMNS, {"score": "number", "cost_usd": "number",
                                                    "tokens": "integer"}, result_desc)
    nr_types = {k: "integer" for k in ("n_cells", "n_unresolved", "n_base", "n_coded",
                                       "n_not_reported")}
    nr_types.update({k: "number" for k in ("rate_unweighted", "weight_base", "weight_not_reported",
                                           "rate_weighted", "se_weighted",
                                           "weighted_minus_unweighted")})
    nr_desc = {
        "n_cells": "Released cells on this dimension.", "n_unresolved": "Unresolved cells "
        "(excluded from both denominators).", "n_base": "n_cells - n_unresolved.",
        "n_coded": "Cells with a value.", "n_not_reported": "Cells coded not_reported.",
        "rate_unweighted": "n_not_reported / n_base.",
        "weight_base": "Sum of design weights over the base (weight-0 systems contribute 0).",
        "weight_not_reported": "Sum of design weights over the not_reported cells.",
        "rate_weighted": "Design-weighted not-reported rate (estimate for the frame).",
        "se_weighted": "Stratified design SE with finite-population correction.",
        "weighted_minus_unweighted": "rate_weighted - rate_unweighted.",
    }
    nr_cols = list(nr_rows[0].keys()) if nr_rows else []
    nr_columns = infer_columns(nr_cols, nr_types, nr_desc)
    rel_types: dict[str, str] = {}
    for c in rel_cols[3:]:
        vals = [r[c] for r in rel_rows if r[c] != ""]
        if vals and all(v in ("true", "false") for v in vals):
            rel_types[c] = "boolean"
        elif vals and all(re.fullmatch(r"-?\d+", v) for v in vals):
            rel_types[c] = "integer"
        elif vals and all(cast_ok(v, "number") for v in vals):
            rel_types[c] = "number"
    rel_columns = infer_columns(rel_cols, rel_types, {
        "n": "Double-coded systems compared.", "agreement": "Observed exact-set agreement.",
        "kappa": "Cohen's kappa on the exact value set.", "ac1": "Gwet's AC1.",
        "per_value_kappa": "Kappa averaged over per-value presence/absence.",
        "reading": "Interpretation against the 0.6 floor.",
        "kappa_ci_lo": "95% cluster-bootstrap interval, lower (system is the resampling unit).",
        "kappa_ci_hi": "95% cluster-bootstrap interval, upper.",
    })

    # every value must cast to its declared type, or datapackage.json would lie
    type_errors = (check_types("cells", cell_cols, cell_rows)
                   + check_types("systems_wide", wide_cols, wide_rows)
                   + check_types("papers", paper_columns, paper_rows)
                   + check_types("results", result_columns, result_rows)
                   + check_types("not_reported_by_dimension", nr_columns, nr_rows)
                   + check_types("reliability", rel_columns, rel_rows))
    if type_errors:
        raise ReleaseError("CSV values do not match their declared types:\n  "
                           + "\n  ".join(type_errors))

    write_csv(root / "data" / "cells.csv", [c[0] for c in cell_cols], cell_rows)
    write_csv(root / "data" / "systems_wide.csv", [c[0] for c in wide_cols], wide_rows)
    write_csv(root / "data" / "papers.csv", paper_cols, paper_rows)
    write_csv(root / "data" / "results.csv", RESULT_COLUMNS, result_rows)
    write_csv(root / "data" / "not_reported_by_dimension.csv", nr_cols, nr_rows)
    write_csv(root / "data" / "reliability.csv", rel_cols, rel_rows)
    write_text(root / "data" / "prisma_counts.json",
               released_prisma(read_json(src["prisma"]), RELEASED_DOCS))

    parquet = pyarrow_available()
    if parquet:
        write_parquet(root / "data" / "systems.parquet", wide_cols, wide_rows)
        write_parquet(root / "data" / "cells.parquet", cell_cols, cell_rows)

    # 4. schema, docs, licences, citation, version
    write_bytes(root / "schema" / "dimensions.json", src["dims"].read_bytes())
    write_bytes(root / "schema" / "harness_db.schema.json", src["schema"].read_bytes())
    glosses = manual_glosses(src["manual"].read_text(encoding="utf-8"), dims)
    write_text(root / "schema" / "data_dictionary.md", data_dictionary(dims_doc, glosses, version))
    write_bytes(root / "docs" / "coding_manual.md", src["manual"].read_bytes())
    write_bytes(root / "docs" / "protocol_prisma_p.md", src["protocol"].read_bytes())
    for doc in EXTRA_DOCS:
        write_bytes(root / "docs" / doc, (repo / "docs" / doc).read_bytes())
    for ex in EXAMPLES:
        ex_path = repo / "data" / "examples" / ex
        write_bytes(root / "data" / "examples" / ex, ex_path.read_bytes())
        if ex.endswith(".json"):
            bad = list(Draft202012Validator(schema).iter_errors([read_json(ex_path)]))
            if bad:
                raise ReleaseError(f"data/examples/{ex} fails the JSON Schema: {bad[0].message}")
    cff = src["citation"].read_text(encoding="utf-8")
    write_text(root / "CITATION.cff", citation_for_release(cff, version, released_on))
    write_bytes(root / "LICENSE-DATA", src["license_data"].read_bytes())
    write_bytes(root / "LICENSE-CODE", src["license_code"].read_bytes())
    write_text(root / "VERSION", version + "\n")

    # 5. counts, validation report, readme
    states = Counter(r["state"] for r in cell_rows)
    strata = Counter(r["stratum"] for r in wide_rows)
    weights = [float(r["weight"]) if r["weight"] else 0.0 for r in wide_rows]
    frame_strata = Counter(r["stratum"] for r in frame_rows)
    counts = {
        "systems": len(systems), "dimensions": len(dims), "layers": len(dims_doc["layers"]),
        "cells": len(cell_rows), **{k: states.get(k, 0) for k in STATES},
        "weighted_systems": sum(1 for w in weights if w > 0),
        "weight_zero": sum(1 for w in weights if w <= 0), "weight_sum": sum(weights),
        "frame_size": len(frame_rows), "parquet": parquet,
    }
    if counts["cells"] != counts["systems"] * counts["dimensions"]:
        raise ReleaseError(f"cells.csv has {counts['cells']} rows, expected systems x dimensions")
    no_frame = sum(1 for r in wide_rows if not r["stratum"])

    def pct(n: int) -> str:
        return f"{100 * n / counts['cells']:.2f}%"

    validation = "\n".join([
        f"HARNESS-DB {version} release validation",
        "",
        f"source data/systems.json sha256 {hashlib.sha256(systems_bytes).hexdigest()}",
        "JSON Schema (schema/harness_db.schema.json, Draft 2020-12): 0 errors",
        "system ids unique: ok",
        "every system's paper ids are in data/papers.csv: ok",
        "every data/results.csv system_id is a released system: ok",
        "every CSV value casts to the type declared in datapackage.json: ok",
        "deny-list (full texts, raw harvests, coder bundles, screening, logs, paper/): ok",
        "",
        f"systems        {counts['systems']:>7,}",
        f"dimensions     {counts['dimensions']:>7,}  in {counts['layers']} layers",
        f"cells          {counts['cells']:>7,}  (= {counts['systems']:,} x {counts['dimensions']})",
        f"  coded        {counts[STATE_VALUE]:>7,}  ({pct(counts[STATE_VALUE])})",
        f"  not_reported {counts[STATE_NR]:>7,}  ({pct(counts[STATE_NR])})",
        f"  unresolved   {counts[STATE_UNRESOLVED]:>7,}  ({pct(counts[STATE_UNRESOLVED])})",
        "",
        "strata in the release  " + " / ".join(f"{k} {strata[k]:,}" for k in stratum_order(strata)),
        (f"weight-bearing systems {counts['weighted_systems']:,} (sum of weights "
        f"{counts['weight_sum']:,.3f}); {counts['weight_zero']} systems carry weight 0"),
        "sampling frame (N_h)   " + " / ".join(f"{k} {frame_strata[k]:,}"
                                               for k in stratum_order(frame_strata))
        + f" = {len(frame_rows):,}",
        *([f"systems without a frame row (no stratum/weight): {no_frame}"] if no_frame else []),
        "",
        f"data/cells.csv rows          {len(cell_rows):,}",
        f"data/systems_wide.csv rows   {len(wide_rows):,}",
        f"data/papers.csv rows         {len(paper_rows):,} (included papers)",
        f"data/results.csv rows        {len(result_rows):,}",
        f"data/reliability.csv rows    {len(rel_rows):,}",
        "parquet                      " + ("written" if parquet else
                                           "skipped: pyarrow not importable at build time"),
        "",
    ])
    write_text(root / "VALIDATION.txt", validation)
    title = cff_field(cff, "title")
    write_text(root / "README.md", release_readme(src["card"].read_text(encoding="utf-8"),
                                                  version, counts, parquet))

    # 6. datapackage.json, then checksums over everything else
    cells_fk = [{"fields": ["system_id"], "reference": {"resource": "systems-wide",
                                                        "fields": ["system_id"]}}]
    enum_values = {d["key"]: d["values"] for d in dims if d.get("values") and not d.get("multi")}
    enum_values.update({f"{d['key']}_state": list(STATES) for d in dims})
    tabular = [
        ("cells", "data/cells.csv", "Cells, long form",
         table_schema(cell_cols, ["system_id", "dimension_key"], cells_fk,
                      {"state": list(STATES), "confidence": ["high", "medium", "low"]})),
        ("systems-wide", "data/systems_wide.csv", "Systems, wide form",
         table_schema(wide_cols, ["system_id"], None, enum_values)),
        ("papers", "data/papers.csv", "Included papers", table_schema(paper_columns, ["id"])),
        ("results", "data/results.csv", "Reported results",
         table_schema(result_columns, None, cells_fk)),
        ("not-reported-by-dimension", "data/not_reported_by_dimension.csv",
         "Not-reported rate by dimension", table_schema(nr_columns, ["key"])),
        ("reliability", "data/reliability.csv", "Inter-coder reliability by dimension",
         table_schema(rel_columns, ["dimension_key"])),
    ]
    other = [
        ("systems", "data/systems.json", "Systems (canonical JSON)", "json", "application/json",
         "The release. Validates against schema/harness_db.schema.json."),
        ("prisma-counts", "data/prisma_counts.json", "PRISMA 2020 flow counts", "json",
         "application/json", ""),
        ("dimensions", "schema/dimensions.json", "Coding sheet: layers, dimensions, values",
         "json", "application/json", ""),
        ("json-schema", "schema/harness_db.schema.json", "JSON Schema for data/systems.json",
         "json", "application/schema+json", ""),
        ("data-dictionary", "schema/data_dictionary.md", "Data dictionary", "md", "text/markdown",
         ""),
        ("coding-manual", "docs/coding_manual.md", "Coding manual", "md", "text/markdown", ""),
        ("protocol", "docs/protocol_prisma_p.md", "Review protocol (PRISMA-P)", "md",
         "text/markdown", ""),
        ("coding-reliability", "docs/coding_reliability.md", "Coding reliability", "md",
         "text/markdown", ""),
        ("count-reconciliation", "docs/count_reconciliation.md",
         "Count reconciliation (authority for every count)", "md", "text/markdown", ""),
        ("schema-changelog", "docs/schema_changelog.md", "Schema changelog", "md",
         "text/markdown", ""),
        ("example-swe-agent", "data/examples/swe-agent-1x.json",
         "Worked example: SWE-agent 1.x", "json", "application/json",
         "Coded end to end in the coding manual; validates against the JSON Schema."),
        ("example-openhands", "data/examples/openhands.json", "Worked example: OpenHands", "json",
         "application/json",
         "Coded end to end in the coding manual; validates against the JSON Schema."),
        ("examples-readme", "data/examples/README.md", "Worked examples README", "md",
         "text/markdown", ""),
        ("readme", "README.md", "Dataset card (Hugging Face) and release notes", "md",
         "text/markdown", ""),
        ("validation", "VALIDATION.txt", "Validation report", "txt", "text/plain", ""),
        ("citation", "CITATION.cff", "Citation metadata", "cff", "text/plain", ""),
        ("version", "VERSION", "Version", "txt", "text/plain", ""),
        ("license-data", "LICENSE-DATA", "CC BY 4.0 legal code", "txt", "text/plain", ""),
        ("license-code", "LICENSE-CODE", "MIT licence (for the build code in the source repository)",
         "txt", "text/plain", ""),
    ]
    if parquet:
        other[1:1] = [
            ("systems-parquet", "data/systems.parquet", "Systems, wide form (Parquet)", "parquet",
             "application/vnd.apache.parquet", "Same table as data/systems_wide.csv."),
            ("cells-parquet", "data/cells.parquet", "Cells, long form (Parquet)", "parquet",
             "application/vnd.apache.parquet", "Same table as data/cells.csv."),
        ]
    resources = []
    for rname, path, rtitle, tschema in tabular:
        resources.append({
            "name": rname, "path": path, "title": rtitle, "type": "table",
            "profile": "tabular-data-resource",
            "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
            "dialect": {"delimiter": ",", "lineTerminator": "\n", "quoteChar": '"',
                        "doubleQuote": True, "header": True},
            "bytes": (root / path).stat().st_size, "hash": "sha256:" + sha256_file(root / path),
            "licenses": [CC_BY], "schema": tschema,
        })
    for rname, path, rtitle, fmt, media, desc in other:
        res = {"name": rname, "path": path, "title": rtitle, "profile": "data-resource",
               "format": fmt, "mediatype": media, "encoding": "utf-8",
               "bytes": (root / path).stat().st_size, "hash": "sha256:" + sha256_file(root / path),
               "licenses": [MIT if rname == "license-code" else CC_BY]}
        if fmt == "parquet":
            del res["encoding"]
        if desc:
            res["description"] = desc
        if rname == "systems":
            res["jsonSchema"] = "schema/harness_db.schema.json"
        resources.append(res)
    authors = re.findall(r"- family-names: (.+)\n\s+given-names: (.+)", cff)
    package = {
        "$schema": DATAPACKAGE_V2,
        "name": PACKAGE,
        "title": title,
        "description": (f"{counts['systems']:,} LLM agent harnesses coded on "
                        f"{counts['dimensions']} dimensions ({counts['cells']:,} cells), each "
                        "coded value backed by a verbatim quote and a locator. Cells are in one of "
                        f"three states: {', '.join(STATES)}."),
        "version": version,
        "created": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "homepage": cff_field(cff, "repository-code"),
        "keywords": cff_keywords(cff),
        "licenses": [CC_BY],
        "contributors": [{"title": f"{g.strip()} {f.strip()}", "roles": ["author"]}
                         for f, g in authors[:1]],
        "resources": resources,
    }
    write_text(root / "datapackage.json", json.dumps(package, indent=2, ensure_ascii=False) + "\n")

    lines = [f"{sha256_file(root / rel)}  {rel}" for rel in tree_files(root)
             if rel != "CHECKSUMS.sha256"]
    write_text(root / "CHECKSUMS.sha256", "\n".join(lines) + "\n")
    say(f"built {len(lines) + 1} files in {root.name}")
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", required=True, help="release version, e.g. 1.0.0")
    ap.add_argument("--out", type=Path, default=REPO / "release", help="output directory")
    ap.add_argument("--timestamp", help="build timestamp, ISO 8601 UTC (default: SOURCE_DATE_EPOCH "
                                        "or now)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    try:
        build(args.version, args.out, args.timestamp, quiet=args.quiet)
    except ReleaseError as exc:
        print(f"release FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
