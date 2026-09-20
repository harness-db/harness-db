#!/usr/bin/env python
"""Phase 4 coding: fill the 38 dimensions of ``schema/dimensions.json`` for every sampled system,
one verbatim evidence quote and one locator per cell.

Screening (phase 3) decided scope and recorded how many dimensions each bundle *could* support;
``scripts/coding_strata.py`` decided *which* systems are coded (``data/coding_frame.csv``,
``coded=1``). What is left is the expensive part of the review: 955 systems x 38 dimensions =
36,290 cells, each of which the protocol requires to carry evidence a reader can re-open. Coding
that by hand is out of reach, so an LLM pre-fills every cell (coder id ``llm-prefill``, manual
general rule 9) and a human overwrites cells later; this script is what makes the pre-fill
auditable rather than a wall of unsourced enum values:

* EVIDENCE BUNDLE. One bundle per system: the full texts of its member records (reference lists
  removed) followed by the REPOSITORY EVIDENCE section that ``scripts/fetch_repos.py`` built for
  its ``repo_url``. Capped at ``--bundle-chars`` characters and water-filled between papers and
  repositories, with every cut recorded per part, and the exact text sent kept with the answer so
  that any quote can be re-checked against what the model actually saw.
* TWO PASSES OVER THE SAME BUNDLE. ``--pass A`` asks for all 38 dimensions in one call. ``--pass
  B`` re-reads only the cells pass A left unresolved (sentinel, invalid, no quote, or a quote that
  is not verbatim in the bundle) and sends keyword windows around that dimension's key terms
  instead of the whole bundle, which is roughly a tenth of the input for the handful of cells that
  need it. A resolved pass-B cell supersedes the pass-A cell; the pass-A attempt stays in
  ``cells.csv`` (``pass`` column) and in the system's ``history`` block, because "the reader
  changed their mind on re-reading" is itself data for the reliability section.
* NOTHING IS SILENTLY COERCED. Every cell is validated against the schema (enum membership, multi
  -> list vs scalar, integer/boolean/date parsing) and against the coding manual's general rules
  (``docs/coding_manual.md``: the sentinel for "the source does not say" is ``not_reported: true``
  with ``value: null``, which is NOT the same as the genuine absence ``none``; ``none`` never
  appears beside another value; an absence still needs a quote). A cell that breaks a rule is
  written with a flag and counted as unresolved - it is never repaired into a plausible value,
  because a repaired cell is indistinguishable from a coded one afterwards.
* QUOTES ARE CHECKED. Every quote must appear verbatim (whitespace- and punctuation-normalised, as
  in ``scripts/fulltext_screen.py``) in the bundle text that was sent; a paraphrase is flagged
  ``quote_not_in_bundle`` and counted in the summary, never rewritten.
* DOUBLE CODING. ``--double-sample 0.2 --seed <str>`` names a deterministic hash sample (the
  ``sample_hash`` of ``scripts/coding_strata.py``); ``--double`` codes exactly that sample a second
  time into ``cells_pass2.csv`` / ``systems_coded_pass2.jsonl`` / ``json_pass2/``. The two codings
  are never merged or averaged: ``scripts/kappa.py coding data/coded/json data/coded/json_pass2``
  reads them as two coders and reports per-dimension kappa (>= 0.6 is the freeze condition for
  schema v1).

Prompt (``code-v1-2026-09-20``): the system text is assembled at run time from
``schema/dimensions.json`` (ids, types, value sets) and ``docs/coding_manual.md`` (the ``General
rules`` section verbatim, plus each dimension's definition, values, decision rule and evidence
rule). Nothing about the 38 dimensions is hardcoded here, so a schema or manual amendment reaches
the prompt and the validator without touching this file.

Backend: Claude Code headless through ``scripts/screen_llm.py::vote_batch_claude_code`` (one system
per call, subscription login, tools disabled, JSON schema validated locally), injectable as
``main(..., backend=...)`` so the tests run without a model. ``cost_usd`` is Claude Code's
list-price equivalent, not a charge, and is recorded per call on each of that call's rows.

Outputs in ``data/coded/`` (all resumable: an existing ``(system_id, pass)`` row is skipped,
``--redo <system_id>`` drops that system's rows and codes it again):

    cells.csv                one row per system x dimension x pass, with value, quote, locator,
                             confidence, flags, pass, model, prompt_version and the cost columns
    systems_coded.jsonl      one object per system per pass: bundle manifest + merged coding
    json/<system_id>.json    authoritative merged coding, in the shape kappa.py reads
    cells_pass2.csv, systems_coded_pass2.jsonl, json_pass2/   the independent second coding
    run.log                  the run log; the last line of a run is SUMMARY {json}

Usage:
    python scripts/code_system.py --pass A [--limit 20] [--bundle-chars 110000]
    python scripts/code_system.py --pass B
    python scripts/code_system.py --pass A --double --double-sample 0.2 --seed code-2026-09-20
    python scripts/code_system.py --bundle swe-agent          # print one bundle, no model call
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import coding_strata
import fulltext_screen as fs
import screen_llm

REPO = Path(__file__).resolve().parents[1]
DIMENSIONS = REPO / "schema" / "dimensions.json"
MANUAL = REPO / "docs" / "coding_manual.md"
FRAME = REPO / "data" / "coding_frame.csv"
FULLTEXT_DIR = REPO / "data" / "fulltext"
REPO_INDEX = REPO / "data" / "screening" / "repo_index.csv"
OUT_DIR = REPO / "data" / "coded"

PROMPT_VERSION = "code-v1-2026-09-20"
CODER = {False: "llm-prefill", True: "llm-prefill-2"}  # double? -> manual general rule 9
DEFAULT_SEED = "code-2026-09-20"

BUNDLE_CHARS = 110_000  # whole bundle, papers + repository evidence
REPO_SHARE = 0.4        # of the cap reserved for repository evidence (an unused share flows back)
WINDOW_CHARS = 600      # pass B: characters of context on each side of a key-term hit
PASS_B_CHARS = 12_000   # pass B: cap on the excerpts sent per system
PASS_B_SHARE = 0.5      # pass B: and never more than this share of the pass-A bundle
QUOTE_MAX_WORDS = 40
CONFIDENCES = ("high", "medium", "low")

CELL_COLUMNS = [
    "system_id", "dimension_id", "dimension_key", "layer", "type", "multi", "value", "not_reported",
    "evidence_quote", "evidence_locator", "quote_verbatim", "confidence", "note", "flags", "resolved",
    "pass", "stratum", "weight", "coder", "coded_at", "model", "prompt_version", "effort",
    "bundle_chars", "doc_chars", "call_id", "tokens_in", "tokens_out", "cache_read", "cache_write", "cost_usd",
]

#: flags that make a cell invalid: it is written, flagged and counted unresolved, never coerced.
INVALID_FLAGS = ("cell_missing", "cell_not_object", "not_in_enum", "scalar_for_multi", "list_for_single",
                 "empty_multi", "bad_integer", "bad_boolean", "bad_date", "none_with_other_values")
#: flags that mean the cell carries no usable evidence even when the value parses.
NO_EVIDENCE_FLAGS = ("missing_quote", "quote_not_in_bundle")

csv.field_size_limit(10 ** 8)


# --------------------------------------------------------------------------------------
# Schema and coding manual (both read at run time; nothing about the 38 dimensions is hardcoded)
# --------------------------------------------------------------------------------------


def load_dimensions(path: Path = DIMENSIONS) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return list(doc["dimensions"])


def schema_version(path: Path = DIMENSIONS) -> str:
    return str(json.loads(path.read_text(encoding="utf-8")).get("schema_version", ""))


MANUAL_HEADING_RE = re.compile(r"^####\s+([A-Z]\d+)\s+(\w+)\s*(?:\(([^)]*)\))?\s*$", re.MULTILINE)


def manual_sections(path: Path = MANUAL) -> dict[str, str]:
    """``#### A1 system_prompt_style (single)`` .. next heading -> {"A1": "definition, values, rules"}."""
    md = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    hits = list(MANUAL_HEADING_RE.finditer(md))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(md)
        body = md[m.end():end]
        nxt = re.search(r"^#{1,3}\s+\S", body, re.MULTILINE)  # a later ## / ### ends the section
        out[m.group(1)] = body[: nxt.start()].strip() if nxt else body.strip()
    return out


def general_rules(path: Path = MANUAL) -> str:
    """Text of the manual's ``## General rules`` section, verbatim (it defines the sentinel)."""
    md = path.read_text(encoding="utf-8")
    m = re.search(r"^##\s+General rules\s*$", md, re.MULTILINE)
    if not m:
        raise ValueError(f"{path} has no '## General rules' section")
    rest = md[m.end():]
    nxt = re.search(r"^##\s+\S", rest, re.MULTILINE)
    return (rest[: nxt.start()] if nxt else rest).strip()


def dimension_block(dims: list[dict[str, Any]], sections: dict[str, str]) -> str:
    """One block per dimension: the schema facts plus the manual's rule text for that dimension."""
    parts = []
    for d in dims:
        kind = "multi-valued (list)" if d.get("multi") else "single-valued"
        head = f"### {d['id']} {d['key']} [layer {d['layer']}] type={d['type']} {kind}"
        if d["type"] == "enum":
            head += "\nallowed values: " + ", ".join(d["values"])
        rule = sections.get(d["id"], "").strip()
        parts.append(head + ("\n" + rule if rule else ""))
    return "\n\n".join(parts)


# --------------------------------------------------------------------------------------
# Answer schema and prompts
# --------------------------------------------------------------------------------------


def cell_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": {"type": ["string", "number", "boolean", "array", "null"],
                      "items": {"type": ["string", "number"]}},
            "evidence_quote": {"type": "string"},
            "evidence_locator": {"type": "string"},
            "confidence": {"type": "string", "enum": list(CONFIDENCES)},
            "not_reported": {"type": "boolean"},
            "note": {"type": "string"},
        },
        "required": ["value", "evidence_quote", "evidence_locator", "confidence"],
        "additionalProperties": False,
    }


def batch_schema(dim_ids: list[str]) -> dict[str, Any]:
    """The whole answer: one vote per system, one cell per requested dimension."""
    return {
        "type": "object",
        "properties": {
            "votes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "record_id": {"type": "string"},  # the system_id (screen_llm orders on it)
                        "cells": {
                            "type": "object",
                            "properties": {i: cell_schema() for i in dim_ids},
                            "required": list(dim_ids),
                            "additionalProperties": False,
                        },
                    },
                    "required": ["record_id", "cells"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["votes"],
        "additionalProperties": False,
    }


INSTRUCTIONS = f"""\
You are coding systems for a PRISMA systematic review of LLM agent harnesses. For each SYSTEM
below, code every dimension you are asked for and answer with one JSON object:
{{"votes": [{{"record_id": "<system_id>", "cells": {{"A1": {{...}}, ...}}}}]}}

Each cell is {{"value", "evidence_quote", "evidence_locator", "confidence"}} plus optional
"not_reported" and "note":

1. value: for a single-valued dimension one allowed value (a string, or a number for an integer
   dimension); for a multi-valued dimension a JSON ARRAY of allowed values, never a bare string.
   An integer dimension takes a bare number, not "about 5". A date takes YYYY-MM-DD.
2. evidence_quote: a span of at most {QUOTE_MAX_WORDS} words COPIED CHARACTER FOR CHARACTER from
   the EVIDENCE below (same wording and spelling, no ellipsis inside, no paraphrase). Every quote
   is checked against the evidence text; a quote that is not found there makes the cell unusable.
3. evidence_locator: for repository evidence `path/to/file.py:LINE@<short-commit>` (the path and
   the commit as the evidence section states them); for a paper the section or page you quoted,
   e.g. `paper Sec. 3.2` or `paper p. 4`.
4. confidence: high (explicit statement or code on the cited line), medium (inferred from adjacent
   code, a default value or a figure), low (inferred from prose describing behaviour).
5. THE SOURCE DOES NOT SAY is not the same as THE FEATURE IS ABSENT. If the evidence does not let
   you point at an answer, set "not_reported": true with "value": null and leave the quote empty:
   do not guess, and do not use the value `none` for it. `none` means the feature genuinely is not
   there, and like every other value it needs a quote at the place where it would be registered
   if it existed (tool registry, config model, run loop).
6. Code the shipped DEFAULT configuration of the pinned version. For a multi-valued dimension add
   every value reachable through shipped configuration without code changes and say in "note"
   which one is the default. Never put `none` in a list with other values.
7. Use only the EVIDENCE below. Do not use anything you know about these systems from elsewhere,
   and do not invent file paths, line numbers or commits.

Answer with the JSON object only: no prose, no code fences.
"""


def system_prompt(dims: list[dict[str, Any]], manual: Path = MANUAL, dimensions: Path = DIMENSIONS) -> str:
    sections = manual_sections(manual)
    return (
        "== Coding manual: general rules (docs/coding_manual.md, verbatim) ==\n" + general_rules(manual) + "\n\n"
        f"== Dimensions (schema/dimensions.json {schema_version(dimensions)}) and their coding rules ==\n"
        + dimension_block(dims, sections) + "\n\n"
        "== Coding instructions ==\n" + INSTRUCTIONS
    )


def _header_block(item: dict[str, Any]) -> str:
    h = item.get("header") or {}
    lines = [f"SYSTEM {item['id']}"]
    for k in ("name", "version", "repo_url", "stratum"):
        if h.get(k):
            lines.append(f"{k}: {h[k]}")
    return "\n".join(lines)


def pass_a_prompt(batch: list[dict[str, Any]]) -> str:
    out = []
    for it in batch:
        out.append(f"=== {_header_block(it)}\nCode all {len(it['dims'])} dimensions: {', '.join(it['dims'])}\n"
                   f"--- EVIDENCE for {it['id']} (begin) ---\n{it['document']}\n"
                   f"--- EVIDENCE for {it['id']} (end) ---")
    return "\n\n".join(out)


def pass_b_prompt(batch: list[dict[str, Any]]) -> str:
    out = []
    for it in batch:
        why = "; ".join(f"{d}: {r}" for d, r in (it.get("reasons") or {}).items())
        out.append(f"=== {_header_block(it)}\nA first reading left these dimensions unresolved: {why}.\n"
                   "Code ONLY those dimensions, from the excerpts below (they are the passages of the same evidence "
                   "that mention those dimensions' terms). If the excerpts still do not answer a dimension, say so "
                   "with not_reported true and value null rather than guessing.\n"
                   f"--- EVIDENCE EXCERPTS for {it['id']} (begin) ---\n{it['document']}\n"
                   f"--- EVIDENCE EXCERPTS for {it['id']} (end) ---")
    return "\n\n".join(out)


# --------------------------------------------------------------------------------------
# Evidence bundle
# --------------------------------------------------------------------------------------


def strip_references(text: str) -> str:
    """Drop the references/bibliography region (up to an appendix-like heading), as the condenser
    of ``scripts/fulltext_screen.py`` does, so the cap is not spent on citations."""
    kept, refs = [], False
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        s = line.strip()
        if fs.REFERENCES_RE.match(s):
            refs = True
            continue
        if refs and fs.AFTER_REFS_RE.match(s):
            refs = False
        if not refs:
            kept.append(line)
    return "\n".join(kept).strip()


def _norm_repo(url: str) -> str:
    u = (url or "").strip().lower().rstrip("/")
    u = re.sub(r"^(https?://|git@)", "", u).replace("github.com:", "github.com/")
    return u.removesuffix(".git")


@dataclass
class Part:
    kind: str            # "paper" | "repo"
    record_id: str
    heading: str
    text: str
    chars_available: int = 0
    chars_used: int = 0

    @property
    def truncated(self) -> bool:
        return self.chars_used < self.chars_available

    def manifest(self) -> dict[str, Any]:
        return {"kind": self.kind, "record_id": self.record_id, "chars_available": self.chars_available,
                "chars_used": self.chars_used, "truncated": self.truncated}


@dataclass
class Bundle:
    system_id: str
    text: str
    parts: list[dict[str, Any]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def chars(self) -> int:
        return len(self.text)

    @property
    def truncated(self) -> bool:
        return any(p["truncated"] for p in self.parts)

    def manifest(self) -> dict[str, Any]:
        return {"chars": self.chars, "truncated": self.truncated, "parts": self.parts, "missing": self.missing}


def member_ids(row: dict[str, str]) -> list[str]:
    """The records whose evidence belongs to this system, canonical record first."""
    ids = [i.strip() for i in (row.get("member_record_ids") or "").split(";") if i.strip()]
    canon = (row.get("canonical_record_id") or "").strip()
    if canon:
        ids = [canon] + [i for i in ids if i != canon]
    return list(dict.fromkeys(ids))


def collect_parts(row: dict[str, str], root: Path = FULLTEXT_DIR,
                  repo_urls: dict[str, str] | None = None) -> tuple[list[Part], list[str]]:
    """Repository evidence first (the system's own repo_url before any other member's), then papers."""
    papers: list[Part] = []
    repos: list[tuple[int, Part]] = []
    missing: list[str] = []
    want = _norm_repo(row.get("repo_url", ""))
    for rid in member_ids(row):
        p = fs.fulltext_path(rid, root)
        if p.exists():
            header, body = fs.parse_fulltext(p.read_text(encoding="utf-8", errors="replace"))
            title = header.get("fetched_title", "")
            head = (f"PAPER {rid} (source: {header.get('source_used', '?')}"
                    + (f", title: {title}" if title else "") + ")")
            papers.append(Part("paper", rid, head, strip_references(body)))
        else:
            missing.append(rid)
        rp = fs.repo_bundle_path(rid, root)
        if rp.exists():
            header, body = fs.parse_repo_bundle(rp.read_text(encoding="utf-8", errors="replace"))
            got = _norm_repo(header.get("repo_url", "") or (repo_urls or {}).get(rid, ""))
            head = (f"REPOSITORY EVIDENCE {rid} (repo: {header.get('repo_url', '?')}, "
                    f"ref: {header.get('ref', '?')}, stars: {header.get('stars', '?')})")
            repos.append((0 if want and got == want else 1, Part("repo", rid, head, body)))
    repos.sort(key=lambda t: t[0])
    return [p for _, p in repos] + papers, missing


def _water_fill(parts: list[Part], budget: int) -> int:
    """Split ``budget`` evenly over ``parts``; a part shorter than its share releases the remainder."""
    remaining = list(parts)
    left = budget
    while remaining and left > 0:
        share = left // len(remaining)
        if share <= 0:
            break
        small = [p for p in remaining if len(p.text) <= share]
        if not small:
            for p in remaining:
                p.chars_used = share
            left -= share * len(remaining)
            break
        for p in small:
            p.chars_used = len(p.text)
            left -= len(p.text)
        remaining = [p for p in remaining if p not in small]
    return max(0, left)


def assemble_bundle(row: dict[str, str], cap: int = BUNDLE_CHARS, repo_share: float = REPO_SHARE,
                    root: Path = FULLTEXT_DIR, repo_urls: dict[str, str] | None = None) -> Bundle:
    """The exact text sent for one system, with every cut recorded per part."""
    parts, missing = collect_parts(row, root, repo_urls)
    for p in parts:
        p.chars_available = len(p.text)
    repos = [p for p in parts if p.kind == "repo"]
    papers = [p for p in parts if p.kind == "paper"]
    head = (f"SYSTEM {row['system_id']}\nname: {row.get('name', '')}\nversion: {row.get('version', '')}\n"
            f"repo_url: {row.get('repo_url', '')}\n")
    budget = max(0, cap - len(head) - sum(len(p.heading) + 80 for p in parts))
    repo_budget = int(budget * repo_share) if papers else budget
    if not repos:
        repo_budget = 0
    leftover = _water_fill(repos, repo_budget)
    _water_fill(papers, budget - repo_budget + leftover)

    blocks = [head]
    for p in parts:
        body = p.text[: p.chars_used]
        note = ("" if not p.truncated else
                f"\n[TRUNCATED: {p.chars_available - p.chars_used} of {p.chars_available} characters omitted]")
        blocks.append(f"--- {p.heading} ---\n{body}{note}")
    if missing:
        blocks.append("--- MISSING EVIDENCE ---\nno fetched full text for: " + ", ".join(missing))
    b = Bundle(row["system_id"], "\n\n".join(blocks))
    b.parts = [p.manifest() for p in parts]
    b.missing = missing
    return b


# --------------------------------------------------------------------------------------
# Pass B: keyword windows around one dimension's key terms
# --------------------------------------------------------------------------------------

STOPWORDS = {"none", "other", "mixed", "yes", "no", "full", "partial", "single", "and", "the", "for", "not", "per",
             "built", "in", "on", "of", "at", "to", "a", "an", "or", "with", "only", "based", "first", "date"}


def key_terms(dim: dict[str, Any]) -> list[str]:
    """Search terms for one dimension: its key, its name and its value labels, split on _ and -."""
    words: list[str] = []
    for s in [dim["key"], dim.get("name", "")] + list(dim.get("values") or []):
        for w in re.split(r"[^A-Za-z0-9]+", str(s)):
            w = w.lower()
            if len(w) >= 3 and w not in STOPWORDS:
                words.append(w)
    return list(dict.fromkeys(words))


def keyword_windows(text: str, terms: list[str], window: int = WINDOW_CHARS, cap: int = PASS_B_CHARS) -> str:
    """Merged +-``window`` character windows around the hits of ``terms``, in document order."""
    if not terms or cap <= 0:
        return ""
    pat = re.compile("|".join(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])" for t in terms), re.IGNORECASE)
    spans: list[list[int]] = []
    for m in pat.finditer(text):
        a, b = max(0, m.start() - window), min(len(text), m.end() + window)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    out, used = [], 0
    for a, b in spans:
        if used >= cap:
            break
        chunk = text[a: min(b, a + (cap - used))]
        used += len(chunk)
        out.append(f"[chars {a}-{a + len(chunk)}]\n{chunk}")
    return "\n...\n".join(out)


def pass_b_document(bundle_text: str, dims: list[dict[str, Any]], window: int = WINDOW_CHARS,
                    cap: int = PASS_B_CHARS, share: float = PASS_B_SHARE) -> str:
    """One excerpt block per unresolved dimension, always strictly smaller than the pass-A bundle."""
    limit = max(1, min(cap, int(len(bundle_text) * share), max(1, len(bundle_text) - 1)))
    per = max(200, limit // max(1, len(dims)))
    blocks = []
    for d in dims:
        terms = key_terms(d)
        w = keyword_windows(bundle_text, terms, window, per)
        blocks.append(f"## excerpts for {d['id']} {d['key']} (terms: {', '.join(terms[:12])})\n"
                      + (w if w else "[no passage of the evidence mentions these terms]"))
    return "\n\n".join(blocks)[:limit]


# --------------------------------------------------------------------------------------
# Cell validation (the schema plus the manual's general rules)
# --------------------------------------------------------------------------------------

LOCATOR_REPO_RE = re.compile(r"^[\w./\\+-]+:\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*@[0-9a-fA-F]{6,40}$")
LOCATOR_PAPER_RE = re.compile(r"(sec\.|section|app\.|appendix|table|fig\.|figure|p\.|page|abstract|readme|"
                              r"file tree|listing)", re.IGNORECASE)


@dataclass
class CellCheck:
    value: Any
    not_reported: bool
    quote: str
    locator: str
    confidence: str
    note: str
    quote_verbatim: bool
    flags: list[str]

    @property
    def invalid(self) -> bool:
        return any(f in INVALID_FLAGS for f in self.flags)

    @property
    def resolved(self) -> bool:
        """A cell a reader can act on: a parseable value with a quote that is in the evidence."""
        return not self.invalid and not self.not_reported and self.quote_verbatim

    def reason(self) -> str:
        if self.invalid:
            return "invalid: " + ",".join(f for f in self.flags if f in INVALID_FLAGS)
        if self.not_reported:
            return "not_reported in the first reading"
        bad = [f for f in self.flags if f in NO_EVIDENCE_FLAGS]
        if bad:
            return "no usable evidence: " + ",".join(bad)
        return "unresolved"

    def cell(self) -> dict[str, Any]:
        """The cell as stored (``scripts/kappa.py`` reads ``value`` and ``not_reported``)."""
        c: dict[str, Any] = {"value": self.value, "not_reported": self.not_reported,
                             "evidence_quote": self.quote, "evidence_locator": self.locator,
                             "confidence": self.confidence, "quote_verbatim": self.quote_verbatim,
                             "flags": self.flags, "resolved": self.resolved}
        if self.note:
            c["note"] = self.note
        return c


def _parse_scalar(dim: dict[str, Any], v: Any, flags: list[str]) -> Any:
    """Parse one scalar for ``dim``; an unparseable value is flagged and becomes None, not a guess."""
    t = dim["type"]
    if t == "enum":
        s = str(v).strip()
        if s not in (dim.get("values") or []):
            flags.append("not_in_enum")
        return s
    if t == "integer":
        if isinstance(v, bool):
            flags.append("bad_integer")
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            if float(v).is_integer():
                return int(v)
            flags.append("bad_integer")
            return None
        s = str(v).strip().replace(",", "").replace("_", "")
        if re.fullmatch(r"[+-]?\d+", s):
            return int(s)
        flags.append("bad_integer")
        return None
    if t == "boolean":
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("true", "yes", "1"):
            return True
        if s in ("false", "no", "0"):
            return False
        flags.append("bad_boolean")
        return None
    if t == "date":
        s = str(v).strip()
        if re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", s):
            return s
        flags.append("bad_date")
        return None
    return str(v).strip()


def check_cell(dim: dict[str, Any], cell: Any, bundle_squashed: str,
               quote_max_words: int = QUOTE_MAX_WORDS) -> CellCheck:
    """Validate one answered cell. Nothing is repaired: every problem becomes a flag."""
    flags: list[str] = []
    if cell is None:
        return CellCheck(None, True, "", "", "", "", False, ["cell_missing"])
    if not isinstance(cell, dict):
        return CellCheck(None, False, "", "", "", "", False, ["cell_not_object"])
    quote = str(cell.get("evidence_quote") or "").strip()
    locator = str(cell.get("evidence_locator") or "").strip()
    conf = str(cell.get("confidence") or "").strip().lower()
    note = str(cell.get("note") or "").strip()
    nr = bool(cell.get("not_reported"))
    raw = cell.get("value")
    if conf and conf not in CONFIDENCES:
        flags.append("bad_confidence")

    empty = raw is None or (isinstance(raw, str) and not raw.strip()) or raw == []
    if nr or empty:
        # the manual's sentinel for "the source does not say" (general rule 2)
        if nr and not empty:
            flags.append("not_reported_with_value")
        if empty and not nr:
            flags.append("null_without_not_reported")
        value: Any = None
        nr = True
    elif dim.get("multi"):
        items = raw if isinstance(raw, list) else [raw]
        if not isinstance(raw, list):
            flags.append("scalar_for_multi")
        vals = [_parse_scalar(dim, x, flags) for x in items]
        vals = [v for v in dict.fromkeys(vals) if v is not None]
        if not vals:
            flags.append("empty_multi")
        if "none" in vals and len(vals) > 1:
            flags.append("none_with_other_values")  # manual general rule 4
        value = sorted(vals, key=str)
    else:
        if isinstance(raw, list):
            flags.append("list_for_single")
            value = [_parse_scalar(dim, x, flags) for x in raw]
        else:
            value = _parse_scalar(dim, raw, flags)

    verbatim = bool(quote) and fs.quote_in_text(quote, bundle_squashed)
    if quote and not verbatim:
        flags.append("quote_not_in_bundle")
    if quote and len(quote.split()) > quote_max_words:
        flags.append("long_quote")
    absence = value == "none" or value == ["none"]
    if not nr:
        if not quote:
            flags.append("missing_quote")
            if absence:
                flags.append("absence_without_evidence")  # manual general rule 5
        if not locator:
            flags.append("missing_locator")
        elif not (LOCATOR_REPO_RE.match(locator) or LOCATOR_PAPER_RE.search(locator)):
            flags.append("locator_shape_unrecognised")
        if absence and conf == "high":
            flags.append("absence_high_confidence")  # rule 5 caps an absence at medium
    return CellCheck(value, nr, quote, locator, conf, note, verbatim, flags)


def value_text(value: Any) -> str:
    """CSV form of a value: a multi-valued cell as ``a|b`` (the form ``scripts/kappa.py`` compares)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join("" if v is None else str(v) for v in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


# --------------------------------------------------------------------------------------
# Input / output
# --------------------------------------------------------------------------------------


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def frame_rows(path: Path = FRAME, all_rows: bool = False) -> list[dict[str, str]]:
    rows = read_csv(path)
    return rows if all_rows else [r for r in rows if (r.get("coded") or "") == "1"]


def repo_url_index(path: Path = REPO_INDEX) -> dict[str, str]:
    """record_id -> repo_url for the repository evidence that was fetched (status ``ok``)."""
    return {r["record_id"]: r.get("repo_url", "") for r in read_csv(path) if (r.get("status") or "") == "ok"}


def double_sample(rows: list[dict[str, str]], fraction: float, seed: str) -> list[str]:
    """Deterministic hash sample, the technique of ``scripts/coding_strata.py::sample_hash``."""
    return [r["system_id"] for r in rows if coding_strata.sample_hash(r["system_id"], seed) < fraction]


def out_paths(out_dir: Path, double: bool) -> dict[str, Path]:
    sfx = "_pass2" if double else ""
    return {"cells": out_dir / f"cells{sfx}.csv",
            "systems": out_dir / f"systems_coded{sfx}.jsonl",
            "json": out_dir / f"json{sfx}",
            "log": out_dir / "run.log",
            "sample": out_dir / "double_sample.json"}


def done_pairs(path: Path) -> set[tuple[str, str]]:
    """The ``(system_id, pass)`` pairs already written: a resumed run skips them."""
    return {(r["system_id"], r["pass"]) for r in read_csv(path)}


def pass_a_state(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    """system_id -> dimension_id -> the pass-A row, for pass B's targeting and merge."""
    out: dict[str, dict[str, dict[str, str]]] = {}
    for r in read_csv(path):
        if r.get("pass") == "A":
            out.setdefault(r["system_id"], {})[r["dimension_id"]] = r
    return out


def rewrite_without(path: Path, system_ids: set[str]) -> int:
    rows = read_csv(path)
    keep = [r for r in rows if r["system_id"] not in system_ids]
    if len(keep) == len(rows):
        return 0
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CELL_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(keep)
    return len(rows) - len(keep)


def rewrite_jsonl_without(path: Path, system_ids: set[str]) -> None:
    if not path.exists():
        return
    kept = [ln for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and json.loads(ln).get("system_id") not in system_ids]
    path.write_text("".join(ln + "\n" for ln in kept), encoding="utf-8")


def open_cells(path: Path) -> tuple[Any, csv.DictWriter]:
    new = not path.exists() or path.stat().st_size == 0
    fh = path.open("a", encoding="utf-8", newline="")
    w = csv.DictWriter(fh, fieldnames=CELL_COLUMNS, extrasaction="ignore")
    if new:
        w.writeheader()
    return fh, w


def cell_row(row: dict[str, str], dim: dict[str, Any], chk: CellCheck, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "system_id": row["system_id"], "dimension_id": dim["id"], "dimension_key": dim["key"],
        "layer": dim["layer"], "type": dim["type"], "multi": int(bool(dim.get("multi"))),
        "value": value_text(chk.value), "not_reported": int(chk.not_reported),
        "evidence_quote": chk.quote, "evidence_locator": chk.locator,
        "quote_verbatim": int(chk.quote_verbatim), "confidence": chk.confidence, "note": chk.note,
        "flags": ";".join(chk.flags), "resolved": int(chk.resolved),
        "stratum": row.get("stratum", ""), "weight": row.get("weight", ""), **meta,
    }


def system_record(row: dict[str, str], bundle: Bundle, coding: dict[str, CellCheck],
                  history: dict[str, dict[str, Any]], meta: dict[str, Any],
                  dims: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {d["id"]: d for d in dims}
    rec: dict[str, Any] = {
        "system_id": row["system_id"], "name": row.get("name", ""), "version": row.get("version", ""),
        "repo_url": row.get("repo_url", ""), "stratum": row.get("stratum", ""), "weight": row.get("weight", ""),
        "schema_version": schema_version(), "bundle": bundle.manifest(),
        "coding": {by_id[i]["key"]: chk.cell() for i, chk in coding.items() if i in by_id},
        "cells_unresolved": sorted(i for i, chk in coding.items() if not chk.resolved),
        "flag_counts": dict(Counter(f for chk in coding.values() for f in chk.flags)),
    }
    if history:
        rec["history"] = history
    rec.update(meta)
    return rec


def write_system_json(directory: Path, rec: dict[str, Any]) -> None:
    """The per-system file ``scripts/kappa.py coding`` reads (the authoritative merge for one coder)."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{fs.safe_id(rec['system_id'])}.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")


def _check_from_row(row: dict[str, str], dim: dict[str, Any]) -> CellCheck:
    """Rebuild a pass-A cell from its CSV row (pass B keeps the pass-A cells it did not resolve)."""
    raw = row.get("value") or ""
    value: Any = None
    if raw:
        if dim.get("multi"):
            value = sorted(raw.split("|"))
        elif dim["type"] == "integer" and re.fullmatch(r"[+-]?\d+", raw):
            value = int(raw)
        else:
            value = raw
    return CellCheck(value, (row.get("not_reported") or "0") == "1", row.get("evidence_quote") or "",
                     row.get("evidence_locator") or "", row.get("confidence") or "", row.get("note") or "",
                     (row.get("quote_verbatim") or "0") == "1",
                     [f for f in (row.get("flags") or "").split(";") if f])


# --------------------------------------------------------------------------------------
# One system, one call
# --------------------------------------------------------------------------------------


@dataclass
class Answer:
    system_id: str
    checks: dict[str, CellCheck]
    result: Any
    doc_chars: int


def call_backend(backend: Callable[..., Any], exe: str, model: str, system_file: Path, item: dict[str, Any],
                 dims: list[dict[str, Any]], bundle_squashed: str,
                 prompt: Callable[[list[dict[str, Any]]], str], effort: str | None,
                 text_json: bool) -> Answer:
    """One model call for one system; every answered cell comes back validated."""
    by_id = {d["id"]: d for d in dims}
    asked = [by_id[i] for i in item["dims"]]
    res = backend(exe, model, system_file, [item], effort=effort,
                  schema=batch_schema([d["id"] for d in asked]), prompt=prompt, text_json=text_json)
    cells = (res.votes[0].get("cells") or {}) if res.votes else {}
    checks = {d["id"]: check_cell(d, cells.get(d["id"]), bundle_squashed) for d in asked}
    return Answer(item["id"], checks, res, len(prompt([item])))


def _safe(fn: Callable[[Any], Answer], job: Any, log: logging.Logger) -> Answer | None:
    try:
        return fn(job)
    except Exception as exc:  # noqa: BLE001 - one system failing must not stop the run; it is retried next time
        log.error("%s failed: %s", job[0]["id"], str(exc)[:300])
        return None


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None, backend: Callable[..., Any] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--pass", dest="pass_no", choices=("A", "B"), default="A")
    p.add_argument("--frame", type=Path, default=FRAME)
    p.add_argument("--all", action="store_true", help="code every frame row, not only coded=1")
    p.add_argument("--ids", default=None, help="comma-separated system_ids restricting the input")
    p.add_argument("--limit", type=int, default=0, help="stop after N systems (0 = all)")
    p.add_argument("--backend", choices=("claude-code",), default="claude-code")
    p.add_argument("--model", default="opus")
    p.add_argument("--effort", default=None)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--bundle-chars", type=int, default=BUNDLE_CHARS)
    p.add_argument("--repo-share", type=float, default=REPO_SHARE,
                   help="share of the cap reserved for repository evidence")
    p.add_argument("--window-chars", type=int, default=WINDOW_CHARS, help="pass B: context around a key-term hit")
    p.add_argument("--pass-b-chars", type=int, default=PASS_B_CHARS, help="pass B: cap on the excerpts per system")
    p.add_argument("--pass-b-share", type=float, default=PASS_B_SHARE, help="pass B: cap as a share of the bundle")
    p.add_argument("--double-sample", type=float, default=0.0, help="fraction of systems that are double coded")
    p.add_argument("--double", action="store_true", help="this run IS the second, independent coding")
    p.add_argument("--seed", default=DEFAULT_SEED, help="seed for the double-coding sample and the run order")
    p.add_argument("--redo", action="append", default=[], metavar="SYSTEM_ID",
                   help="drop this system's rows from the output and code it again (repeatable)")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--fulltext-dir", type=Path, default=FULLTEXT_DIR)
    p.add_argument("--repo-index", type=Path, default=REPO_INDEX)
    p.add_argument("--bundle", metavar="SYSTEM_ID", help="print one system's bundle and exit (no model call)")
    p.add_argument("--print-prompt", action="store_true", help="print the system prompt and exit")
    p.add_argument("--text-json", action="store_true", help="ask for JSON as plain text instead of --json-schema")
    p.add_argument("--keep-mcp", action="store_true", help="keep claude.ai MCP connectors loaded in the child")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:  # pytest's capture object has none
        reconfigure(encoding="utf-8")
    dims = load_dimensions()
    by_id = {d["id"]: d for d in dims}
    if args.print_prompt:  # the read-only exits happen before anything is created on disk
        print(system_prompt(dims))
        return 0

    rows = {r["system_id"]: r for r in frame_rows(args.frame, args.all)}
    if args.bundle:
        row = rows.get(args.bundle)
        if row is None:
            print(f"{args.bundle} is not a frame row with coded=1 (try --all)", file=sys.stderr)
            return 2
        b = assemble_bundle(row, args.bundle_chars, args.repo_share, args.fulltext_dir,
                            repo_url_index(args.repo_index))
        print(b.text)
        print("\nBUNDLE " + json.dumps(b.manifest()))
        return 0
    if args.double and not args.double_sample:
        print("--double needs --double-sample (the sample it codes)", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    paths = out_paths(args.out_dir, args.double)
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S", force=True,
                        handlers=[logging.StreamHandler(), logging.FileHandler(paths["log"], encoding="utf-8")])
    log = logging.getLogger("code_system")

    universe = list(rows)
    if args.ids:
        want = {i.strip() for i in args.ids.split(",") if i.strip()}
        universe = [s for s in universe if s in want]
    sample: list[str] = []
    if args.double_sample:
        sample = double_sample([rows[s] for s in universe], args.double_sample, args.seed)
        paths["sample"].write_text(json.dumps({"fraction": args.double_sample, "seed": args.seed,
                                               "n": len(sample), "system_ids": sample}, indent=1),
                                   encoding="utf-8")
        log.info("double-coding sample: %d of %d systems (fraction %.3f, seed %s)",
                 len(sample), len(universe), args.double_sample, args.seed)
        if args.double:
            universe = sample

    if args.redo:
        drop = set(args.redo)
        n = rewrite_without(paths["cells"], drop)
        rewrite_jsonl_without(paths["systems"], drop)
        log.info("--redo: dropped %d rows for %s", n, ", ".join(sorted(drop)))
    done = done_pairs(paths["cells"])
    prior = pass_a_state(paths["cells"]) if args.pass_no == "B" else {}
    todo = [s for s in universe if (s, args.pass_no) not in done]
    if args.pass_no == "B":
        todo = [s for s in todo if s in prior]  # pass B has nothing to re-read without pass A
    todo.sort(key=lambda s: coding_strata.sample_hash(s, args.seed))
    if args.limit:
        todo = todo[: args.limit]
    log.info("pass %s%s: %d systems in scope, %d already coded, %d to code", args.pass_no,
             " (second coding)" if args.double else "", len(universe),
             sum(1 for s in universe if (s, args.pass_no) in done), len(todo))

    if not args.keep_mcp:
        # the claude.ai connectors add ~58k tokens of tool schemas to every headless call and break
        # the prompt cache (measured for scripts/fulltext_screen.py)
        os.environ["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    if backend is None:
        backend = screen_llm.vote_batch_claude_code
    exe = ""
    if backend is screen_llm.vote_batch_claude_code:
        exe = screen_llm.find_claude_exe() or ""
        if todo and not exe:
            print("claude executable not found (set CLAUDE_CODE_EXE)", file=sys.stderr)
            return 2

    repo_urls = repo_url_index(args.repo_index)
    tmpdir = Path(tempfile.mkdtemp(prefix="code_system_"))
    system_file = tmpdir / "system_prompt.txt"
    system_file.write_text(system_prompt(dims), encoding="utf-8")
    prompt = pass_a_prompt if args.pass_no == "A" else pass_b_prompt
    coder = CODER[bool(args.double)]
    fh: Any = None
    writer: csv.DictWriter | None = None
    t0 = time.time()
    n_sys = n_cells = n_unres = n_nonverbatim = n_sentinel = n_invalid = failed = 0
    tok_in = tok_out = 0
    spent = 0.0
    bundle_chars: list[int] = []
    doc_chars: list[int] = []
    truncated_systems = 0

    def build(system_id: str) -> tuple[dict[str, Any], Bundle, dict[str, str]] | None:
        """Bundle + prompt item for one system, or None when there is nothing to send."""
        row = rows[system_id]
        bundle = assemble_bundle(row, args.bundle_chars, args.repo_share, args.fulltext_dir, repo_urls)
        if not bundle.parts:
            log.warning("%s: no evidence on disk (%d member records missing): skipped",
                        system_id, len(bundle.missing))
            return None
        if args.pass_no == "A":
            asked = [d["id"] for d in dims]
            doc, reasons = bundle.text, {}
        else:
            state = prior.get(system_id, {})
            asked = [d["id"] for d in dims if (state.get(d["id"], {}).get("resolved") or "0") != "1"]
            if not asked:
                log.info("%s: pass A resolved every cell, nothing for pass B", system_id)
                return None
            reasons = {i: (state[i].get("flags") or "unresolved") if i in state else "missing in pass A"
                       for i in asked}
            doc = pass_b_document(bundle.text, [by_id[i] for i in asked], args.window_chars,
                                  args.pass_b_chars, args.pass_b_share)
        item = {"id": system_id, "document": doc, "dims": asked, "reasons": reasons,
                "header": {"name": row.get("name", ""), "version": row.get("version", ""),
                           "repo_url": row.get("repo_url", ""), "stratum": row.get("stratum", "")}}
        return item, bundle, row

    for start in range(0, len(todo), max(1, args.workers)):
        built = [b for b in (build(s) for s in todo[start: start + max(1, args.workers)]) if b is not None]
        if not built:
            continue
        squashed = {job[0]["id"]: fs._squash(job[1].text) for job in built}

        def run(job: tuple[dict[str, Any], Bundle, dict[str, str]], sq: dict[str, str] = squashed) -> Answer:
            item = job[0]
            return call_backend(backend, exe, args.model, system_file, item, dims, sq[item["id"]],
                                prompt, args.effort, args.text_json)

        with ThreadPoolExecutor(max_workers=len(built)) as pool:
            answers = list(pool.map(lambda j: _safe(run, j, log), built))

        for (item, bundle, row), ans in zip(built, answers, strict=True):
            if ans is None:
                failed += 1
                continue
            res = ans.result
            meta = {"pass": args.pass_no, "coder": coder,
                    "coded_at": datetime.now(UTC).isoformat(timespec="seconds"),
                    "model": getattr(res, "model", args.model) or args.model,
                    "prompt_version": PROMPT_VERSION, "effort": args.effort or "",
                    "bundle_chars": bundle.chars, "doc_chars": ans.doc_chars,
                    "call_id": f"{args.pass_no}{'2' if args.double else ''}-{item['id']}-{n_sys + 1:05d}",
                    "tokens_in": res.tokens_in, "tokens_out": res.tokens_out,
                    "cache_read": res.cache_read, "cache_write": res.cache_write,
                    "cost_usd": f"{res.cost_usd:.6f}"}
            if writer is None:  # the output file appears only when there is something to write
                fh, writer = open_cells(paths["cells"])
            for i, chk in ans.checks.items():
                writer.writerow(cell_row(row, by_id[i], chk, meta))
            fh.flush()

            coding: dict[str, CellCheck] = dict(ans.checks)
            history: dict[str, dict[str, Any]] = {}
            if args.pass_no == "B":  # a resolved pass-B cell supersedes pass A; the attempt is kept
                state = prior.get(item["id"], {})
                merged: dict[str, CellCheck] = {}
                for d in dims:
                    old, new = state.get(d["id"]), ans.checks.get(d["id"])
                    if new is not None and new.resolved:
                        merged[d["id"]] = new
                        if old is not None:
                            history[d["id"]] = {"superseded_pass": "A", "value": old.get("value", ""),
                                                "flags": old.get("flags", ""),
                                                "reason": "pass A left it unresolved"}
                    elif old is not None:
                        merged[d["id"]] = _check_from_row(old, d)
                        if new is not None:
                            history[d["id"]] = {"superseded_pass": "B", "value": value_text(new.value),
                                                "flags": ";".join(new.flags),
                                                "reason": "pass B did not resolve it either"}
                    elif new is not None:
                        merged[d["id"]] = new
                coding = merged
            rec = system_record(row, bundle, coding, history, meta, dims)
            with paths["systems"].open("a", encoding="utf-8") as jf:
                jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            write_system_json(paths["json"], rec)

            n_sys += 1
            n_cells += len(ans.checks)
            unres = sum(1 for c in ans.checks.values() if not c.resolved)
            n_unres += unres
            n_invalid += sum(1 for c in ans.checks.values() if c.invalid)
            n_sentinel += sum(1 for c in ans.checks.values() if c.not_reported)
            n_nonverbatim += sum(1 for c in ans.checks.values() if "quote_not_in_bundle" in c.flags)
            tok_in += res.tokens_in
            tok_out += res.tokens_out
            spent += res.cost_usd
            bundle_chars.append(bundle.chars)
            doc_chars.append(ans.doc_chars)
            truncated_systems += int(bundle.truncated)
            log.info("%s: %d cells, %d unresolved, %d chars sent, $%.4f (%d/%d systems, $%.2f this run)",
                     item["id"], len(ans.checks), unres, ans.doc_chars, res.cost_usd, n_sys, len(todo), spent)
    if fh is not None:
        fh.close()
    shutil.rmtree(tmpdir, ignore_errors=True)

    secs = time.time() - t0
    summary = {
        "pass": args.pass_no, "double": bool(args.double), "prompt_version": PROMPT_VERSION,
        "schema_version": schema_version(), "model": args.model, "effort": args.effort,
        "workers": args.workers, "systems_in_scope": len(universe), "systems_coded_now": n_sys,
        "systems_failed": failed, "cells_coded": n_cells, "cells_unresolved": n_unres,
        "cells_invalid": n_invalid, "cells_not_reported": n_sentinel, "quotes_non_verbatim": n_nonverbatim,
        "bundle_chars_mean": round(sum(bundle_chars) / len(bundle_chars)) if bundle_chars else None,
        "bundle_chars_max": max(bundle_chars) if bundle_chars else None,
        "doc_chars_mean": round(sum(doc_chars) / len(doc_chars)) if doc_chars else None,
        "bundles_truncated": truncated_systems, "tokens_in": tok_in, "tokens_out": tok_out,
        "cost_usd": round(spent, 3), "cost_per_system_usd": round(spent / n_sys, 4) if n_sys else None,
        "wall_seconds": round(secs, 1), "wall_seconds_per_system": round(secs / n_sys, 2) if n_sys else None,
        "double_sample_n": len(sample) or None, "seed": args.seed, "out": str(paths["cells"]),
    }
    print("SUMMARY " + json.dumps(summary))
    log.info("SUMMARY %s", json.dumps(summary))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
