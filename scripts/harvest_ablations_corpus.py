#!/usr/bin/env python
"""Corpus-wide harvest of published component ablations, read directly from the included full texts.

WHY THIS SCRIPT EXISTS
----------------------
`scripts/analyse_ablations.py` pools within-study ablation contrasts, and the contrasts it pools were
harvested from the outcome extraction of the 1,224 CODED systems only (`data/results_rejects.csv`,
`reason=not_own_system`). That route saw ~7% of the included corpus and yielded 75 contrasts from 42
papers, 8 dimensions poolable. The included corpus is 7,122 papers with full text on disk. Most of
the ablation tables in it were never looked at, because nothing downstream of the coding frame read
them. This script reads them.

It produces contrasts in EXACTLY the schema of `data/analysis/ablation_contrasts.csv`
(`analyse_ablations.CONTRAST_COLUMNS`), oriented, scaled and given a variance by the very same
function (`analyse_ablations.orient_contrast`), so `analyse_ablations.py --corpus` can pool them with
the coded-set contrasts. What a contrast IS does not change: the paper's own full system against the
same system with one component switched off (or on), same benchmark, same split, same metric, same
base model. Here "same" is guaranteed by construction rather than by a key join - both numbers are
read from the same table row set or the same sentence - and then CHECKED mechanically (stage 4).

STAGES (each resumable, each cached by record id)
-------------------------------------------------
1. prefilter   no model call. Every included paper's full text is scored for ablation signal
               (`SIGNAL_TERMS`: occurrences of "ablat*" and "w/o"), ranked, and written with the
               per-term counts to `data/analysis/corpus_ablation_prefilter.csv`. Tier T10 (score
               >= 10) is processed first, then T3 (3-9).
2. windows     no model call. `localise` pulls the candidate ablation passages - table regions
               whose caption or row labels look like an ablation, and the sentences that name a
               removed/added component next to a number - into one compact window per paper
               (<= `--max-window-chars`, ~2-6k tokens). Cached in `corpus_ablation/windows.jsonl`.
3. extract     model calls, SUBSCRIPTION PATH ONLY: `screen_llm.vote_batch_claude_code` (headless
               Claude Code). The Anthropic API is never imported, and ANTHROPIC_API_KEY is removed
               from the child environment so the CLI cannot fall back to API billing. Several papers
               per call; the raw answer is cached per record id (`corpus_ablation/extract_cache.jsonl`)
               together with the hash of the window it was given, so a re-run is free and a changed
               window is re-read rather than checked against text the model never saw.
4. guards      mechanical, all tested (`tests/test_harvest_ablations_corpus.py`). In order:
                 malformed_row              a score is missing or is not a number
                 score_not_in_text          either score does not occur verbatim in the window
                 scores_not_colocated       the two scores never occur within `COLOCATE_CHARS`
                 signed_delta_as_score      the "ablated score" is a signed delta (+/-x) while the
                                            full score is not: a delta column was read as a score
                 delta_metric_as_score      the metric is a difference column (∆, Δ, delta, gain,
                                            improvement) printed without a sign
                 scores_not_separable       the evidence runs two decimals together ("74.2870.90"),
                                            so the arm's column cannot be identified
                 scale_mismatch             one score on a 0-1 scale, the other on 0-100
                 not_a_performance_metric   cost / latency / tokens / steps / memory
                 model_or_training_variant  the other arm is a different base model or a training
                                            variant (category, `same_base_model=false`, the arm
                                            label names a model or a training recipe, or a router /
                                            cascade between base models)
                 not_an_ablation:<category> rival system, bare-LLM baseline, own-full alias
                 unmapped / dimension_not_design / low_confidence
                                            `analyse_ablations.normalise_vote`, unchanged: dimension
                                            must be a layer A-H key (layer M cannot be ablated),
                                            confidence floor 0.5
                 classification remaps      uniform keyword rules on the component, arm label and
                                            evidence that REMAP a mis-mapped dimension (or drop it,
                                            under the rule's own name, when nothing fits):
                   sandbox_is_execution_feedback  G1 -> E1: removing the sandbox removes run-and-read
                   tool_gating_is_tool_interface  G4 -> B2: all tools exposed / no tool gating
                   tools_ablation_is_context      G2 -> A2 ("w/o tools" loses project information)
                                                  or B2 (a bare "tools" label)
                   cost_component_not_a_limit     F2 only for spending limits; caching -> D1 / D3
                 direction_<x>              the arm cannot be oriented
                 direction_contradicts_label the printed label says removal but the row is oriented
                                            as an addition (or vice versa): dropped, never flipped
                 denominator_too_small / variance_not_finite
                                            `analyse_ablations.orient_contrast`, unchanged
                 duplicate_contrast         the same cell proposed twice for one paper
               and then a FLAG, not a drop: `already_in_coded_harvest`, by (paper, benchmark,
               metric, component) or by identical (paper, full score, ablated score), using
               `analyse_ablations.flag_coded_duplicates`. Flagged rows are kept in the file for
               audit and excluded from pooling, so no contrast is counted twice.

Every paper's outcome (rows proposed, kept, dropped and why) is logged to
`data/analysis/corpus_ablation_outcomes.csv`, so recall is auditable paper by paper. Every row a
classification guard remapped, dropped, retained or flagged is written, with the guard's name, the
dimension before and after and the rule's note, to `data/analysis/corpus_ablation_guard_audit.csv`;
the guards run at report time on the cached answers, which they never rewrite.

Usage limits: a batch that fails on a usage limit is re-queued and the run sleeps until the reset
the CLI reported, via `phase4_autopilot.reset_wait` (the same parser the coding autopilot uses).

Run:
    python scripts/harvest_ablations_corpus.py --stage prefilter
    python scripts/harvest_ablations_corpus.py --stage windows
    python scripts/harvest_ablations_corpus.py --stage extract --tier T10 --workers 3
    python scripts/harvest_ablations_corpus.py --stage report          (rebuild outputs from cache)
Long runs go through `scripts/run_ablation_harvest.cmd` under Task Scheduler (a console-attached
job dies with the session).
"""
from __future__ import annotations

import argparse
import ast
import atexit
import csv
import hashlib
import importlib.util
import json
import logging
import os
import re
import sys
import tempfile
import threading
import time
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PAPERS = ROOT / "data" / "papers.csv"
FULLTEXT_DIR = ROOT / "data" / "fulltext"
SYSTEMS = ROOT / "data" / "systems.json"
OUT_DIR = ROOT / "data" / "analysis"
WORK_DIR = OUT_DIR / "corpus_ablation"
CODED_CONTRASTS = OUT_DIR / "ablation_contrasts.csv"

PREFILTER_CSV = OUT_DIR / "corpus_ablation_prefilter.csv"
ROWS_CSV = OUT_DIR / "corpus_ablation_rows.csv"
CONTRASTS_CSV = OUT_DIR / "corpus_ablation_contrasts.csv"
OUTCOMES_CSV = OUT_DIR / "corpus_ablation_outcomes.csv"
FUNNEL_CSV = OUT_DIR / "corpus_ablation_guard_funnel.csv"
SUMMARY_JSON = OUT_DIR / "corpus_ablation_summary.json"
WINDOWS_JSONL = WORK_DIR / "windows.jsonl"
CACHE_JSONL = WORK_DIR / "extract_cache.jsonl"
FAILURES_JSON = WORK_DIR / "failures.json"
STATUS_JSON = WORK_DIR / "status.json"
RUN_LOG = WORK_DIR / "run.log"
LOCK = WORK_DIR / "extract.lock"

PROMPT_VERSION = "corpus-ablation-v1-2026-09-25"
WINDOW_VERSION = "w1"
PROVENANCE = "corpus_fulltext"

log = logging.getLogger("harvest_ablations_corpus")
csv.field_size_limit(10 ** 8)


def _load_module(name: str, path: Path) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


aa = _load_module("analyse_ablations", SCRIPTS / "analyse_ablations.py")

# ------------------------------------------------------------------------------------------------
# stage 1: prefilter
# ------------------------------------------------------------------------------------------------
# The score is the count of these two signals, nothing else: it reproduces the ~800 / ~3,000 tiers
# of the manual prefilter and is trivially explainable. `w/o` has no leading \b on purpose: PDF text
# glues words ("thew/o RAGandw/o Profiling").
SIGNAL_TERMS: dict[str, re.Pattern[str]] = {
    "ablat": re.compile(r"(?i)ablat\w*"),
    "w/o": re.compile(r"(?i)w/out|w/o"),
}
# Reported beside the score as reasons, never added to it.
AUX_TERMS: dict[str, re.Pattern[str]] = {
    "ablation_caption": re.compile(r"(?im)^\s*(?:table|tab\.)\s*[a-z]?\d+[^\n]{0,160}?ablat"),
    "marker_rows": re.compile(r"(?m)^\s*(?:[-−–+]\s*[A-Za-z]|w/o\b|without\b)[^\n]*\d+\.\d"),
    "full_rows": re.compile(r"(?im)^\s*(?:full|ours|complete)\b[^\n]*\d+\.\d"),
}
TIER_HIGH, TIER_LOW = 10, 3
MIN_BODY_CHARS = 2000   # a full-text file shorter than this is a metadata stub, not a paper
TIER_ORDER = {"T10": 0, "T3": 1, "below": 2, "no_fulltext": 3}


def safe_id(record_id: str) -> str:
    """Identical to `fetch_repos.safe_id` / `fetch_fulltext.safe_id`: `src:rest` -> `src__rest`."""
    s = re.sub(r"[:/\\]", "__", record_id)
    return re.sub(r'[<>"|?*\x00-\x1f]', "_", s)


def fulltext_path(record_id: str, root: Path = FULLTEXT_DIR) -> Path:
    """The paper's text file. Never a `__repo.txt` bundle: that is the repository, not the paper."""
    return root / f"{safe_id(record_id)}.txt"


def split_header(raw: str) -> tuple[dict[str, str], str]:
    """(`key: value` header written by fetch_fulltext, body). The header ends at the first blank line."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    head, sep, body = text.partition("\n\n")
    meta: dict[str, str] = {}
    lines = head.split("\n")
    if sep and lines and all(re.match(r"^[a-z_]+:\s?", ln) for ln in lines if ln.strip()):
        for ln in lines:
            k, _, v = ln.partition(":")
            meta[k.strip()] = v.strip()
        return meta, body
    return {}, text


def read_paper(record_id: str, root: Path = FULLTEXT_DIR) -> tuple[dict[str, str], str]:
    path = fulltext_path(record_id, root)
    if not path.exists():
        return {}, ""
    return split_header(path.read_text(encoding="utf-8", errors="replace"))


def prefilter_score(body: str) -> tuple[int, dict[str, int]]:
    """(score, per-term counts). Score = sum of SIGNAL_TERMS hits; AUX_TERMS are reasons only."""
    counts = {k: len(p.findall(body)) for k, p in SIGNAL_TERMS.items()}
    score = sum(counts.values())
    counts |= {k: len(p.findall(body)) for k, p in AUX_TERMS.items()}
    return score, counts


def tier_of(score: int, body_chars: int) -> str:
    if body_chars < MIN_BODY_CHARS:
        return "no_fulltext"
    if score >= TIER_HIGH:
        return "T10"
    if score >= TIER_LOW:
        return "T3"
    return "below"


def included_ids(path: Path = PAPERS) -> list[str]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df.loc[df["included"].astype(str).str.strip() == "1", "id"].tolist()


def coded_harvest_records(path: Path = CODED_CONTRASTS) -> set[str]:
    if not path.exists():
        return set()
    return set(pd.read_csv(path, dtype=str, keep_default_na=False)["record_id"])


def run_prefilter(ids: Sequence[str], root: Path = FULLTEXT_DIR, out: Path = PREFILTER_CSV,
                  coded: set[str] | None = None) -> pd.DataFrame:
    """Score every included paper; resumable (ids already in `out` are kept, not re-read)."""
    coded = coded or set()
    done: dict[str, dict[str, Any]] = {}
    if out.exists():
        for r in pd.read_csv(out, dtype=str, keep_default_na=False).to_dict("records"):
            r.pop("rank", None)
            done[r["record_id"]] = r
    rows = []
    for n, rid in enumerate(ids, start=1):
        if rid in done:
            rows.append(done[rid])
            continue
        meta, body = read_paper(rid, root)
        score, counts = prefilter_score(body)
        rows.append({
            "record_id": rid, "title": meta.get("fetched_title", ""),
            "body_chars": len(body), "score": score, "tier": tier_of(score, len(body)),
            "reasons": ";".join(f"{k}={v}" for k, v in counts.items() if v),
            **{f"n_{re.sub(r'[^a-z0-9]+', '_', k)}": v for k, v in counts.items()},
            "in_coded_harvest": int(rid in coded),
        })
        if n % 1000 == 0:
            log.info("prefilter: %d / %d", n, len(ids))
    df = pd.DataFrame(rows)
    for col in ("score", "body_chars"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["tier_rank"] = df["tier"].map(TIER_ORDER).fillna(9).astype(int)
    df = df.sort_values(["tier_rank", "score", "record_id"], ascending=[True, False, True])
    df = df.drop(columns=["tier_rank"]).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8")
    return df


# ------------------------------------------------------------------------------------------------
# stage 2: table localisation
# ------------------------------------------------------------------------------------------------
NUM_RE = re.compile(r"(?<![\w.])[-−–+]?\d+(?:[.,]\d+)?%?")
DECIMAL_RE = re.compile(r"\d+\.\d+|\d+%")
CAPTION_RE = re.compile(r"(?i)^\s*(?:table|tab\.)\s*[a-z]?\d+")
ABLATION_WORD_RE = re.compile(
    r"(?i)ablat|w/o|w/out|without|remov|disabl|variant|component|contribution|effect of|impact of|"
    r"module|configuration|design choice")
ROW_MARKER_RE = re.compile(
    r"(?i)^\s*(?:[-−–+]\s*[a-z(]|w/o|w/out|w/\s|without\b|with\b|no\b|full\b|ours\b|"
    r"complete\b|base(?:line)?\b|vanilla\b|single\b|only\b)|w/o|\bonly\b|\bablat")
PROSE_RE = re.compile(r"(?i)ablat|w/o|remov(?:e|ed|ing)|without the|disabl|drops?\b|degrad|"
                      r"declin|decreas|falls?\b|hurts?\b|contribut")
MODEL_MENTION_RE = re.compile(
    r"(?i)\b(?:gpt-?(?:\d(?:\.\d)?o?|oss)|claude|llama|qwen|deepseek|gemini|mistral|mixtral|"
    r"phi-\d|o[134](?:-mini)?|glm|kimi|grok)")
SETUP_RE = re.compile(r"(?i)\b(?:use|using|used|backbone|base model|powered by|underlying|"
                      r"we adopt|default model|as the (?:llm|model))\b")
MAX_WINDOW_CHARS = 18000
MAX_REGION_LINES = 45
CONTEXT_BEFORE = 5
CONTEXT_AFTER = 2


def is_numeric_line(line: str) -> bool:
    """A line that looks like a table row: >= 2 numbers with at least one decimal/percentage."""
    if len(line) > 260:
        return False
    nums = NUM_RE.findall(line)
    return len(nums) >= 2 and bool(DECIMAL_RE.search(line))


def _table_regions(lines: list[str], max_gap: int = 2) -> list[tuple[int, int]]:
    """Maximal runs of numeric lines, allowing up to `max_gap` non-numeric lines inside a run."""
    regions: list[tuple[int, int]] = []
    start = last = -1
    for i, ln in enumerate(lines):
        if is_numeric_line(ln):
            if start < 0:
                start = i
            elif i - last - 1 > max_gap:
                regions.append((start, last))
                start = i
            last = i
    if start >= 0:
        regions.append((start, last))
    return regions


def _nearest_caption(lines: list[str], lo: int, hi: int, reach: int = 14) -> int:
    best, dist = -1, 10 ** 9
    for i in range(max(0, lo - reach), min(len(lines), hi + reach + 1)):
        if CAPTION_RE.match(lines[i]):
            d = 0 if lo <= i <= hi else min(abs(i - lo), abs(i - hi))
            if d < dist:
                best, dist = i, d
    return best


def localise(body: str, max_chars: int = MAX_WINDOW_CHARS) -> tuple[str, dict[str, Any]]:
    """The compact ablation window for one paper: (text, info). Empty text = nothing found.

    Candidates are (a) TABLE REGIONS - runs of numeric lines - kept when their caption mentions an
    ablation-type word or at least two of their rows carry an ablation row marker (`w/o`, a leading
    `-`/`+`, `Full`, `Ours`, `only`); and (b) PROSE - lines naming a removal/drop next to a decimal
    or a percentage, with a little context. Each candidate is scored, the best are taken until the
    character budget is spent, and they are emitted in document order, overlapping spans merged.
    The window is the ONLY text the model sees, and the verbatim guard checks against it.
    """
    lines = body.split("\n")
    spans: list[tuple[int, int, float, str]] = []   # (lo, hi, score, kind)
    for lo, hi in _table_regions(lines):
        cap = _nearest_caption(lines, lo, hi)
        cap_text = " ".join(lines[cap:cap + 3]) if cap >= 0 else ""
        cap_ablation = bool(cap_text and ABLATION_WORD_RE.search(cap_text))
        rows = lines[lo:hi + 1]
        markers = sum(1 for ln in rows if is_numeric_line(ln) and ROW_MARKER_RE.search(ln))
        context = " ".join(lines[max(0, lo - 12):hi + 12])
        near_ablat = bool(re.search(r"(?i)ablat|w/o", context))
        if not (cap_ablation or markers >= 2 or (markers >= 1 and near_ablat)):
            continue
        score = 3.0 * markers + (8.0 if cap_ablation else 0.0) + (4.0 if near_ablat else 0.0)
        if cap_text and re.search(r"(?i)ablat", cap_text):
            score += 10.0
        a = max(0, lo - CONTEXT_BEFORE)
        b = min(len(lines) - 1, hi + CONTEXT_AFTER)
        if b - a + 1 > MAX_REGION_LINES + CONTEXT_BEFORE + CONTEXT_AFTER:
            b = a + MAX_REGION_LINES + CONTEXT_BEFORE + CONTEXT_AFTER - 1
        spans.append((a, b, score, "table"))
        if cap >= 0 and not (a <= cap <= b):
            spans.append((cap, min(len(lines) - 1, cap + 2), score - 0.5, "caption"))
    for i, ln in enumerate(lines):
        if PROSE_RE.search(ln) and DECIMAL_RE.search(ln) and not is_numeric_line(ln):
            s = 2.0 + (4.0 if re.search(r"(?i)ablat|w/o|remov|without the", ln) else 0.0)
            spans.append((max(0, i - 2), min(len(lines) - 1, i + 2), s, "prose"))

    info: dict[str, Any] = {"n_tables": sum(1 for s in spans if s[3] == "table"),
                            "n_prose": sum(1 for s in spans if s[3] == "prose"),
                            "n_segments": 0, "truncated": False}
    if not any(s[3] == "table" for s in spans) and not any(s[2] >= 6.0 for s in spans):
        return "", info
    chosen: list[tuple[int, int]] = []
    used = 0
    for lo, hi, _score, _kind in sorted(spans, key=lambda s: (-s[2], s[0])):
        size = sum(len(x) + 1 for x in lines[lo:hi + 1])
        if used + size > max_chars:
            info["truncated"] = True
            continue
        chosen.append((lo, hi))
        used += size
    chosen.sort()
    merged: list[list[int]] = []
    for lo, hi in chosen:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    parts = []
    for n, (lo, hi) in enumerate(merged):
        parts.append(f"=== passage {_letters(n)} ===\n" + "\n".join(lines[lo:hi + 1]))
    info["n_segments"] = len(merged)
    return "\n".join(parts), info


def _letters(n: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA: passage labels without digits, so a label can never be read as a score."""
    out = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def setup_lines(body: str, limit: int = 4) -> list[str]:
    """Up to `limit` short sentences saying which base model the paper runs - context for `base_model`."""
    out: list[str] = []
    for sent in re.split(r"(?<=[.;])\s+", body.replace("\n", " ")):
        if MODEL_MENTION_RE.search(sent) and SETUP_RE.search(sent) and len(sent) < 300:
            s = re.sub(r"\s+", " ", sent).strip()
            if s not in out:
                out.append(s)
        if len(out) >= limit:
            break
    return out


def build_window(meta: dict[str, str], body: str, max_chars: int = MAX_WINDOW_CHARS) -> tuple[str, dict[str, Any]]:
    passages, info = localise(body, max_chars)
    if not passages:
        return "", info
    title = meta.get("fetched_title", "")
    opening = re.sub(r"\s+", " ", body[:700]).strip()
    setup = setup_lines(body)
    head = [f"TITLE: {title}", f"OPENING: {opening}"]
    if setup:
        head.append("SETUP MENTIONS: " + " | ".join(setup))
    text = "\n".join(head) + "\n" + passages
    info["chars"] = len(text)
    return text, info


def window_sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    """record_id -> the LAST entry for it (append-only files; a later line supersedes)."""
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue   # a torn last line from a killed run
            if isinstance(d, dict) and d.get("record_id"):
                out[d["record_id"]] = d
    return out


_APPEND_LOCK = threading.Lock()


def append_jsonl(path: Path, entries: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _APPEND_LOCK, path.open("a", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def run_windows(prefilter: pd.DataFrame, root: Path = FULLTEXT_DIR, path: Path = WINDOWS_JSONL,
                tiers: Sequence[str] = ("T10", "T3"), max_chars: int = MAX_WINDOW_CHARS) -> dict[str, dict[str, Any]]:
    windows = load_jsonl(path)
    todo = [r for r in prefilter.itertuples(index=False) if r.tier in tiers
            and windows.get(r.record_id, {}).get("version") != WINDOW_VERSION]
    batch: list[dict[str, Any]] = []
    for n, r in enumerate(todo, start=1):
        meta, body = read_paper(r.record_id, root)
        text, info = build_window(meta, body, max_chars)
        entry = {"record_id": r.record_id, "version": WINDOW_VERSION, "tier": r.tier,
                 "sha": window_sha(text) if text else "", "window": text, "info": info}
        windows[r.record_id] = entry
        batch.append(entry)
        if len(batch) >= 200:
            append_jsonl(path, batch)
            batch = []
            log.info("windows: %d / %d", n, len(todo))
    if batch:
        append_jsonl(path, batch)
    return windows


# ------------------------------------------------------------------------------------------------
# stage 3: extraction (the only model call)
# ------------------------------------------------------------------------------------------------
ROW_FIELDS = ["system", "full_arm", "ablated_arm", "component", "category", "dimension", "direction",
              "benchmark", "split", "metric", "base_model", "same_base_model", "full_score",
              "ablated_score", "confidence", "evidence", "reason"]
EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["votes"],
    "properties": {
        "votes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["record_id", "rows", "note"],
                "properties": {
                    "record_id": {"type": "string"},
                    "note": {"type": "string"},
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ROW_FIELDS,
                            "properties": {
                                "system": {"type": "string"},
                                "full_arm": {"type": "string"},
                                "ablated_arm": {"type": "string"},
                                "component": {"type": "string"},
                                "category": {"type": "string", "enum": list(aa.CATEGORIES)},
                                "dimension": {"type": "string"},
                                "direction": {"type": "string", "enum": list(aa.DIRECTIONS)},
                                "benchmark": {"type": "string"},
                                "split": {"type": "string"},
                                "metric": {"type": "string"},
                                "base_model": {"type": "string"},
                                "same_base_model": {"type": "boolean"},
                                "full_score": {"type": "string"},
                                "ablated_score": {"type": "string"},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                "evidence": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }
    },
}


def extract_system_prompt(dims: Sequence[dict[str, Any]]) -> str:
    """The extraction prompt: the classifier's categories, menu, direction and refusal rules
    (`analyse_ablations.classify_system_prompt`), preceded by what to read and how to copy numbers."""
    menu = "\n".join(
        f"  {d['key']}  ({d['id']}, layer {d['layer']} = {d['layer_name']}; {d['name']})"
        + (f"  values: {', '.join(d['values'])}" if d["values"] else "")
        for d in dims if d["design"])
    meta = ", ".join(d["key"] for d in dims if not d["design"])
    return f"""You extract COMPONENT-ABLATION results from research papers about LLM agent harnesses
(agent scaffolds). For each paper you get a WINDOW: its title, its opening, a few sentences naming the
base model, and the passages of its full text most likely to hold an ablation (tables and the
sentences around them, labelled "=== passage A ===", "=== passage B ===" ...). The text was extracted
from PDF, so table cells run together on one line: "Full GraphBit67.6 126.1-" is the row label
"Full GraphBit" followed by the cells 67.6, 126.1 and a dash; column headers are on the lines above.

WHAT TO RETURN. One row per CONTRAST: a pair of numbers from the SAME table (or the same sentence),
under the SAME column - so the same benchmark, split, metric and base model - where one number is the
paper's OWN FULL system and the other is the SAME system with ONE component switched OFF or removed
(an ablation), or switched ON on top of a simpler configuration (an augmentation). One row per
(arm, benchmark/metric column). At most 40 rows per paper; beyond that prefer each benchmark's main
metric.

NUMBERS - the rule that decides whether your row survives. `full_score` and `ablated_score` are
copied EXACTLY as printed, character for character, as a string ("67.6", "0.412", "54"), without a
% sign. Never round, never convert 0.67 to 67, never compute a number, never take a number from a
Delta / difference / change column: if the ablated row prints only its difference from the full
system and not its own score, skip that row. Every number you return is checked by machine against
the window, and a number that is not printed there deletes the row.

KEEP ONLY task-performance metrics: success rate, accuracy, pass@k, % resolved, F1, EM, reward,
score, win rate and the like. Do NOT return cost, latency, time, tokens, number of steps or calls,
or memory use. Do NOT return rows for rival systems or bare-LLM baselines at all - only the paper's
own system and its own configurations. If the paper has no qualifying contrast, return rows = []
and say why in `note` (at most 20 words).

FIELDS
  system          the paper's name for its own full system ("GraphBit").
  full_arm        the full-system row/column label as printed ("Full GraphBit", "Ours").
  ablated_arm     the other arm's label as printed ("w/o structured state").
  component       the component removed or added, in plain words ("structured state memory tier").
  category        exactly one of:
    ablation                  the paper's OWN system with one component switched OFF, removed,
                              disabled or replaced by nothing ("w/o memory", "- verification",
                              "Single agent" when the system is multi-agent, "ReAct-only" when the
                              system adds something to ReAct).
    augmentation              the paper's OWN system with one component switched ON on top of a
                              simpler configuration ("+ Memory", "w/ Verifier").
    own_full_alias            another name for the full system; no component differs.
    rival_system              a different team's harness.
    non_harness_baseline      a bare LLM, a human, a retrieval-only pipeline, a classical method.
    model_or_training_variant the SAME harness with a different base model, a different amount or
                              kind of training/fine-tuning/RL/SFT, a different decoding or sampling
                              budget, or a different dataset. A harness component is NOT what changed.
    unmapped                  you cannot tell what the arm was, or it ablates something that is not
                              one of the design dimensions below.
  dimension       if and only if the category is ablation or augmentation, the ONE key below that the
                  arm removes, adds or changes; otherwise "unmapped".
{menu}
                  These keys are metadata and can NEVER be the answer (answer "unmapped"): {meta}
  direction       relative to the full system: component_removed (present in full, absent in this
                  arm), component_added (absent in full / in the simpler configuration, present in
                  this arm), component_changed (present in both, set differently), unclear. A label
                  starting "w/o", "without", "no ", "-" or "minus" is component_removed; "+", "w/",
                  "with" is component_added; "X only" / "single X" is component_removed.
  benchmark       the benchmark as named ("SWE-bench", "GAIA", "HotpotQA"); split: the subset or
                  split if stated ("Verified", "test", "level 1"), else "".
  metric          the metric as the column header or sentence names it ("Acc. (%)", "pass@1").
  base_model      the LLM both arms run on, if the window says ("GPT-4o"); else "".
  same_base_model true when both arms run on the same base model (the normal case in an ablation
                  table); false when the arms differ in base model.
  confidence      your probability that the category, the dimension AND both numbers are right,
                  in [0, 1], used as a hard threshold - calibrate it and use the whole range:
                    >= 0.8 the arm names the component outright and its dimension is not in doubt;
                    ~ 0.6  you would defend this mapping to a reviewer;
                    ~ 0.4  a reviewer could reasonably name a different dimension;
                    <= 0.3 you are guessing: answer category unmapped instead.
                  Do not reflexively answer 0.5.
  evidence        the verbatim line(s) the two numbers came from, at most 300 characters.
  reason          at most 25 words, quoting the words you relied on.

REFUSE TO GUESS. An arm forced into the nearest-looking dimension corrupts a pooled component effect
and is the single worst error you can make; an unmapped arm is excluded and costs nothing. Acronyms
not defined in the window ("w/o GA", "+JO") are unmapped.

Answer for every paper id you are given, in the same order, with `record_id` set to that id.
"""


def extract_prompt(batch: list[dict[str, Any]]) -> str:
    payload = [{"id": it["id"], "window": it["window"]} for it in batch]
    return ("Papers to read (JSON array; `id` is what you put in `record_id`, `window` is the only "
            "text you may take numbers from).\n" + json.dumps(payload, ensure_ascii=False))


def pack_batches(items: Sequence[dict[str, Any]], batch_size: int, max_chars: int) -> list[list[dict[str, Any]]]:
    """Greedy packing by count and by total window characters; a single over-size item goes alone."""
    batches: list[list[dict[str, Any]]] = []
    cur: list[dict[str, Any]] = []
    size = 0
    for it in items:
        n = len(it["window"])
        if cur and (len(cur) >= batch_size or size + n > max_chars):
            batches.append(cur)
            cur, size = [], 0
        cur.append(it)
        size += n
    if cur:
        batches.append(cur)
    return batches


USAGE_LIMIT_RE = re.compile(r"(?i)usage limit|session limit|weekly limit|hit your|limit.{0,40}resets|"
                            r"resets\s+\d|credit balance|out of (?:extra )?usage")
TRANSIENT_RE = re.compile(r"(?i)rate.?limit|\b429\b|\b529\b|too many requests|overloaded|"
                          r"timed? ?out|econnreset|\b50[23]\b")


def limit_kind(msg: str) -> str:
    """`usage` (wait for the reported reset), `transient` (brief back-off) or "" (a real failure)."""
    if USAGE_LIMIT_RE.search(msg or ""):
        return "usage"
    if TRANSIENT_RE.search(msg or ""):
        return "transient"
    return ""


def is_limit_error(msg: str) -> bool:
    return bool(limit_kind(msg))


def subscription_env() -> None:
    """Force the subscription path: Claude Code bills an API key if it finds one in the environment."""
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        os.environ.pop(var, None)
    os.environ.setdefault("ENABLE_CLAUDEAI_MCP_SERVERS", "false")


def call_batch(backend: Callable[..., Any], exe: str, model: str, system_file: Path,
               batch: list[dict[str, Any]], effort: str | None) -> Any:
    return backend(exe, model, system_file, batch, effort=effort, schema=EXTRACT_SCHEMA,
                   prompt=extract_prompt, text_json=True)


def validate_vote(vote: Any) -> list[dict[str, Any]]:
    """The model's rows for one paper, each reduced to ROW_FIELDS; raises on a malformed answer."""
    if not isinstance(vote, dict) or not isinstance(vote.get("rows"), list):
        raise TypeError("vote without a rows array")
    out = []
    for row in vote["rows"]:
        if isinstance(row, dict):
            out.append({k: row.get(k) for k in ROW_FIELDS})
    return out


def _read_failures(path: Path = FAILURES_JSON) -> dict[str, dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    os.replace(tmp, path)


def pending_records(prefilter: pd.DataFrame, windows: dict[str, dict[str, Any]],
                    cache: dict[str, dict[str, Any]], failures: dict[str, dict[str, Any]],
                    tiers: Sequence[str], max_failures: int = 3) -> list[str]:
    """Records still to extract, in prefilter rank order: windowed, not cached against this window,
    not given up on."""
    out = []
    for r in prefilter.itertuples(index=False):
        if r.tier not in tiers:
            continue
        w = windows.get(r.record_id)
        if not w or not w.get("window"):
            continue
        c = cache.get(r.record_id)
        if c and c.get("window_sha") == w.get("sha"):
            continue
        if int(failures.get(r.record_id, {}).get("count", 0)) >= max_failures:
            continue
        out.append(r.record_id)
    return out


def run_extract(args: argparse.Namespace, prefilter: pd.DataFrame, windows: dict[str, dict[str, Any]],
                dims: Sequence[dict[str, Any]], backend: Callable[..., Any], exe: str,
                *, rebuild: Callable[[], None] | None = None,
                sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Extract every pending record of the requested tiers, waiting out usage limits.

    Batches run `args.workers` at a time. A batch that fails on a usage limit is re-queued and the
    whole run sleeps until the reported reset; a batch that fails otherwise is split into single
    papers and retried, and a paper that fails `max_failures` times alone is recorded and skipped.
    """
    phase4 = _load_module("phase4_autopilot", SCRIPTS / "phase4_autopilot.py")
    cache = load_jsonl(CACHE_JSONL)
    failures = _read_failures()
    tiers = args.tiers
    todo = pending_records(prefilter, windows, cache, failures, tiers, args.max_failures)
    if args.limit:
        todo = todo[: args.limit]
    stats_: dict[str, Any] = {"pending_at_start": len(todo), "papers_done": 0, "calls": 0,
                              "limit_waits": 0, "failed_calls": 0, "tokens_in": 0, "tokens_out": 0}
    if not todo:
        log.info("extract: nothing pending for tiers %s", ",".join(tiers))
        return stats_
    tmp = Path(tempfile.mkdtemp(prefix="corpus_ablation_"))
    system_file = tmp / "extract_system_prompt.txt"
    system_file.write_text(extract_system_prompt(dims), encoding="utf-8")
    items = [{"id": "", "record_id": rid, "window": windows[rid]["window"], "sha": windows[rid]["sha"]}
             for rid in todo]
    queue = pack_batches(items, args.batch_size, args.max_batch_chars)
    for b in queue:
        for i, it in enumerate(b, start=1):
            it["id"] = f"P{i}"
    deadline = time.time() + args.deadline_hours * 3600
    log.info("extract: %d papers in %d batches (tiers %s, model %s, workers %d)",
             len(todo), len(queue), ",".join(tiers), args.model, args.workers)
    stalls = 0
    last_rebuild = 0

    def one(batch: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Any]:
        return batch, call_batch(backend, exe, args.model, system_file, batch, args.effort)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        while queue and time.time() < deadline:
            wave, queue = queue[: args.workers], queue[args.workers:]
            futures = {pool.submit(one, b): b for b in wave}
            limit_hit = ""
            progressed = 0
            for fut in as_completed(futures):
                batch = futures[fut]
                try:
                    _, result = fut.result()
                    votes = list(getattr(result, "votes", result) or [])
                    entries = []
                    for it, vote in zip(batch, votes, strict=True):
                        rows = validate_vote(vote)
                        entries.append({
                            "record_id": it["record_id"], "window_sha": it["sha"],
                            "prompt_version": PROMPT_VERSION,
                            "model": getattr(result, "model", args.model),
                            "at": datetime.now(UTC).isoformat(timespec="seconds"),
                            "rows": rows, "note": str(vote.get("note") or "")[:300],
                            "batch_size": len(batch),
                            "tokens_in": int(getattr(result, "tokens_in", 0) or 0),
                            "tokens_out": int(getattr(result, "tokens_out", 0) or 0),
                        })
                    append_jsonl(CACHE_JSONL, entries)
                    for it in batch:
                        failures.pop(it["record_id"], None)
                    stats_["calls"] += 1
                    stats_["papers_done"] += len(batch)
                    stats_["tokens_in"] += int(getattr(result, "tokens_in", 0) or 0)
                    stats_["tokens_out"] += int(getattr(result, "tokens_out", 0) or 0)
                    progressed += len(batch)
                    log.info("batch ok: %d papers, %d rows (%d/%d done)", len(batch),
                             sum(len(e["rows"]) for e in entries), stats_["papers_done"], len(todo))
                except Exception as exc:  # noqa: BLE001 - one bad batch must not lose the others
                    msg = str(exc)
                    stats_["failed_calls"] += 1
                    log.error("batch of %d failed: %s", len(batch), msg[:700])
                    kind = limit_kind(msg)
                    if kind == "transient":
                        batch[0]["_transient"] = int(batch[0].get("_transient", 0)) + 1
                        if batch[0]["_transient"] > 3:
                            kind = ""   # a batch that keeps timing out is a failure, not a limit
                    if kind:
                        limit_hit = "usage" if "usage" in (kind, limit_hit) else kind
                        queue.insert(0, batch)
                    elif len(batch) > 1:
                        for it in batch:
                            it["id"] = "P1"
                            queue.append([it])
                    else:
                        rid = batch[0]["record_id"]
                        f = failures.setdefault(rid, {"count": 0, "errors": []})
                        f["count"] = int(f.get("count", 0)) + 1
                        f["errors"] = (list(f.get("errors", [])) + [msg[:300]])[-3:]
                        if f["count"] < args.max_failures:
                            queue.append(batch)
            _write_json(FAILURES_JSON, failures)
            _write_json(STATUS_JSON, {"updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
                                      "tiers": list(tiers), "remaining_batches": len(queue),
                                      **stats_})
            if rebuild is not None and (stats_["calls"] - last_rebuild >= args.rebuild_every or not queue):
                last_rebuild = stats_["calls"]
                try:
                    rebuild()
                except Exception as exc:  # noqa: BLE001 - reporting must never stop the harvest
                    log.error("rebuild failed: %s", exc)
            if limit_hit and not progressed:
                stalls += 1
                stats_["limit_waits"] += 1
                if stalls > args.max_stalls:
                    log.error("usage limit did not lift after %d waits; stopping", stalls - 1)
                    break
                if limit_hit == "usage":
                    wait, why = phase4.reset_wait(RUN_LOG, args.limit_wait * 60)
                else:
                    wait, why = 120, "transient rate limit / overload: short back-off"
                wait = min(wait, max(0, deadline - time.time()))
                log.warning("usage limit: waiting %d min (%s)", round(wait / 60), why)
                _write_json(STATUS_JSON, {"updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
                                          "waiting_until": (datetime.now(UTC) + timedelta(seconds=wait))
                                          .isoformat(timespec="seconds"),
                                          "tiers": list(tiers), "remaining_batches": len(queue), **stats_})
                sleep(wait)
            elif progressed:
                stalls = 0
    return stats_


# ------------------------------------------------------------------------------------------------
# stage 4: guards (mechanical)
# ------------------------------------------------------------------------------------------------
SCORE_TEXT_RE = re.compile(r"^[+\-]?\d+(?:\.\d+)?$")
MINUS_CHARS = "−–—"
COLOCATE_CHARS = 2500
NON_PERFORMANCE_RE = re.compile(
    r"(?i)(?:\$|\b(?:cost|costs|usd|price|latency|time|seconds?|secs?|minutes?|mins?|hours?|"
    r"runtime|wall[- ]?clock|tokens?|steps|turns|calls|memory usage|mb|gb|throughput|"
    r"speed|speedup|flops)\b)")
TRAINING_RE = re.compile(
    r"(?i)\b(?:sft|rlhf|rlaif|dpo|grpo|ppo|rl|lora|qlora|fine[- ]?tun\w*|finetun\w*|pre[- ]?train\w*|"
    r"post[- ]?train\w*|distill\w*|training|trained|train|checkpoints?|epochs?|reward model|"
    r"instruction[- ]tun\w*)\b")
MODEL_NAME_RE = re.compile(
    r"(?i)\b(?:gpt-?[345](?:\.\d)?o?|gpt-?4o|o[134](?:-mini)?|claude(?:[- ]\w+)?|llama[- ]?\d*|"
    r"qwen\d*(?:\.\d)?|deepseek(?:[- ]\w+)?|gemini(?:[- ]\w+)?|mistral|mixtral|phi-\d|glm-?\d*|"
    r"kimi|grok|\d+(?:\.\d+)?\s?b\b)")


def parse_score(text: Any) -> float | None:
    """A score string as the model copied it -> float, or None when it is not a plain number."""
    s = normalise_score_text(text)
    if not s or not SCORE_TEXT_RE.match(s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


PLUSMINUS_RE = re.compile(r"^([+\-]?\d+(?:\.\d+)?)\s*%?\s*\(?\s*(?:±|\+/-|\+-)\s*\d+(?:\.\d+)?\s*\)?\s*%?$")


def normalise_score_text(text: Any) -> str:
    """The score as a bare number string: signs unified, thousands commas and a trailing %/marker
    dropped, and a `mean +- sd` cell reduced to its mean (the mean is what is printed verbatim)."""
    s = str(text if text is not None else "").strip()
    for ch in MINUS_CHARS:
        s = s.replace(ch, "-")
    m = PLUSMINUS_RE.match(s)
    if m:
        s = m.group(1)
    s = s.replace(",", "") if re.fullmatch(r"[+\-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?", s) else s
    return s.rstrip("%*†‡ ").strip()


def _score_pattern(text: Any, *, glued: bool = False) -> re.Pattern[str] | None:
    """The regex a score must match in the window.

    The trailing side is always strict: "67.6" does not match "67.61" or "67.6.1". The leading side
    is strict by default ("7" does not match inside "67"); with `glued=True` a DECIMAL score may
    follow a digit, because PDF extraction runs adjacent table cells together ("N=20100.0%" is the
    cells "N=20" and "100.0%", "37349.35" is "373" and "49.35"). An integer score never gets that
    allowance: "5" glued to anything is not evidence of anything.
    """
    s = normalise_score_text(text)
    if not s or not SCORE_TEXT_RE.match(s):
        return None
    core = s.lstrip("+-")
    lead = r"(?<![.])" if (glued and "." in core) else r"(?<![\d.])"
    # trailing side: strict, except that a glued decimal may run straight into the NEXT decimal
    # cell ("65.5163.71" is 65.51 then 63.71); "67.6" still never matches "67.61 ".
    trail = r"(?:(?![\d]|\.\d)|(?=\d+\.\d))" if (glued and "." in core) else r"(?![\d]|\.\d)"
    return re.compile(lead + re.escape(core) + trail)


def score_positions(text: Any, window: str, *, glued: bool = True) -> list[int]:
    pat = _score_pattern(text, glued=glued)
    if pat is None:
        return []
    return [m.start() for m in pat.finditer(window)]


def scores_in_window(full_text: Any, ablated_text: Any, window: str) -> bool:
    """Both scores occur verbatim in the window: a character match, number-boundary aware (see
    `_score_pattern`; a decimal glued to a preceding cell counts, and is flagged by `score_match`)."""
    return bool(score_positions(full_text, window)) and bool(score_positions(ablated_text, window))


def score_match(full_text: Any, ablated_text: Any, window: str) -> str:
    """`bounded` when both scores also match with strict boundaries on both sides, else `glued`."""
    strict = (score_positions(full_text, window, glued=False)
              and score_positions(ablated_text, window, glued=False))
    return "bounded" if strict else "glued"


def scores_colocated(full_text: Any, ablated_text: Any, window: str,
                     reach: int = COLOCATE_CHARS) -> bool:
    """Some occurrence of each score lies within `reach` characters of the other: same table/sentence."""
    a, b = score_positions(full_text, window), score_positions(ablated_text, window)
    return any(abs(x - y) <= reach for x in a for y in b)


def is_signed_delta(full_text: Any, ablated_text: Any) -> bool:
    """The ablated "score" carries an explicit sign and the full score does not: a Delta column."""
    f, a = normalise_score_text(full_text), normalise_score_text(ablated_text)
    return a.startswith(("+", "-")) and not f.startswith(("+", "-"))


def scale_mismatch(full: float, ablated: float) -> bool:
    """One arm on a 0-1 scale and the other on 0-100 (e.g. 0.67 against 67): the pair is not one column."""
    lo, hi = sorted([abs(full), abs(ablated)])
    return hi > 1.5 and 0 < lo <= 1.0 and hi / lo > 20


PERFORMANCE_WORD_RE = re.compile(
    r"(?i)\b(?:acc\w*|success\w*|sr|pass\w*|resolv\w*|solve\w*|f1|em|exact|score|reward|win|"
    r"correct\w*|completion|precision|recall|bleu|rouge|hit)\b|pass@|pass\^")


def is_performance_metric(metric: str) -> bool:
    """False for cost / latency / tokens / steps / memory metrics - unless the metric names a task
    outcome and only QUALIFIES it by a budget ("Success Rate (%) 50 steps", "pass@1 within 30 min")."""
    m = str(metric or "")
    return not NON_PERFORMANCE_RE.search(m) or bool(PERFORMANCE_WORD_RE.search(m))


def is_model_or_training_variant(row: dict[str, Any]) -> bool:
    """Category says so, the arms differ in base model, or the arm LABEL names a model or a recipe.

    Only the arm label and the component are read, not the full-arm label or the benchmark: an
    ablation table run on "GPT-4o" names the model in its header, not in the ablated arm.
    """
    if str(row.get("category") or "") == "model_or_training_variant":
        return True
    if row.get("same_base_model") is False or str(row.get("same_base_model")).lower() == "false":
        return True
    arm = f"{row.get('ablated_arm') or ''} {row.get('component') or ''}"
    if TRAINING_RE.search(arm):
        return True
    if is_model_routing(row):
        return True
    # a model named in the arm label is a variant only if the full arm / base model does not name
    # the same model: "DualGraph w/o KG (GPT-4.1)" beside "DualGraph (GPT-4.1)" is an ablation.
    shared = _alnum(f"{row.get('full_arm') or ''} {row.get('base_model') or ''}")
    return any(_alnum(m.group(0)) not in shared for m in MODEL_NAME_RE.finditer(arm))


def _alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())



# Routing between BASE MODELS (a cascade, a small/large router) makes the two arms run different
# models, so the contrast is a model variant, not a harness component. Read from the PRINTED arm
# label ("w/o model router", "single LLM (no cascade)"), or from the component only when it names
# more than one model ("routing across models"): the component is the extractor's paraphrase, and a
# paraphrase saying "model routing" for a router that picks between execution strategies on one base
# model (arxiv:2602.00887, "-Complexity Routing", Fig. 4) is not evidence that the base model differs.
MODEL_ROUTING_ARM_RE = re.compile(
    r"(?i)\b(?:model|llm)s?[- ]?(?:rout\w*|cascad\w*|select\w*|switch\w*)|"
    r"\brout\w*\s+(?:\S+\s+){0,3}(?:models|llms)\b")
MODEL_ROUTING_COMPONENT_RE = re.compile(
    r"(?i)\b(?:rout\w*|cascad\w*|select\w*|switch\w*)\b[^.;]{0,40}\b(?:models|llms)\b|"
    r"\b(?:models|llms)\b[^.;]{0,20}\b(?:rout\w*|cascad\w*)")


def is_model_routing(row: dict[str, Any]) -> bool:
    """The arms differ by which base model(s) answer: a model router or cascade was removed or added."""
    return bool(MODEL_ROUTING_ARM_RE.search(str(row.get("ablated_arm") or ""))
                or MODEL_ROUTING_COMPONENT_RE.search(str(row.get("component") or "")))


# ------------------------------------------------------------------------------------------------
# classification guards: seven uniform rules on the extractor's cached answer, applied at REPORT
# time only (the cache is never rewritten, the extract stage is untouched). A spot-check found that
# every contrast the extractor put on execution_isolation was a sandbox whose removal takes away the
# agent's run-and-read loop; the fix is a rule, never an edit to a row. Each rule reads the
# component, the printed arm labels, the metric and the quoted evidence, and every row a rule
# touches is written with the rule's name to `corpus_ablation_guard_audit.csv`.
#   drop    delta_metric_as_score, scores_not_separable, direction_contradicts_label
#   remap   sandbox_is_execution_feedback, tool_gating_is_tool_interface, tools_ablation_is_context,
#           cost_component_not_a_limit  (a remap to "unmapped" drops the row under the rule's name)
# ------------------------------------------------------------------------------------------------
GUARD_AUDIT_CSV = OUT_DIR / "corpus_ablation_guard_audit.csv"
CLASSIFICATION_GUARDS = ("sandbox_is_execution_feedback", "tool_gating_is_tool_interface",
                         "tools_ablation_is_context", "scores_not_separable", "delta_metric_as_score",
                         "cost_component_not_a_limit", "direction_contradicts_label")
#: the dimension each remap rule reads; a row on any other dimension is never touched by it
REMAP_SOURCE = {"sandbox_is_execution_feedback": "execution_isolation",
                "tool_gating_is_tool_interface": "permission_model",
                "tools_ablation_is_context": "filesystem_access",
                "cost_component_not_a_limit": "cost_controls"}
#: flag (not a drop) on an F2 / F3 contrast whose component is not a limit
LIMIT_FLAG = "not_a_limit_on_task_metric"

# 1. sandbox_is_execution_feedback -----------------------------------------------------------------
# A sandbox / execution / plan-apply step whose removal means the agent can no longer run its code
# (or apply its infrastructure) and read the result is the self-verification loop (E1, value
# test_execution), not an isolation boundary. G1 stays only when the ablated arm still runs the code
# without the boundary (host vs container, no network cut), or the metric measures safety/containment.
EXEC_STEP_RE = re.compile(
    r"(?i)sandbox|\bexecut\w*|\brun(?:s|ning|time)?\b|interpreter|\bcompil\w*|plan\s*/\s*apply|"
    r"\bapply\b|terraform|\brepl\b|code runner|test harness")
FEEDBACK_LOSS_RE = re.compile(
    r"(?i)cannot (?:run|execute|test|apply|compile|observe|see the (?:output|result))|"
    r"(?:no|without) (?:code )?(?:execution|runtime|run|test) (?:feedback|results?|output)|"
    r"(?:no|without) (?:code )?execution\b|execution feedback|static(?:ally)? (?:only|generat\w*)|"
    r"never (?:runs|executes)|(?:no|without) feedback")
ISOLATION_KEPT_RE = re.compile(
    r"(?i)\bhost\b|bare[- ]metal|unsandboxed|un-?isolated|isolat\w*|container\w*|docker|\bvms?\b|"
    r"virtual machine|chroot|namespace|seccomp|gvisor|firejail|network (?:cut|isolation|access|egress)|"
    r"same process|in-process|directly on the")
SAFETY_METRIC_RE = re.compile(
    r"(?i)safe|safety|harm\w*|attack|\basr\b|escape|breach|leak\w*|violat\w*|contain\w*|"
    r"secur\w*|risk\w*|damag\w*|destructive|malicious|exploit\w*")

# 2. tool_gating_is_tool_interface -----------------------------------------------------------------
# Exposing every tool at every phase, or removing phase-specific tool selection / visibility, changes
# the tool interface the model sees (B2), not an enforced authorisation on actions (G4).
TOOL_GATING_RE = re.compile(
    r"(?i)tool[- ]?gat\w*|gat(?:ed|es|ing) (?:the )?tools?|all tools|every tool|full tool[- ]?set|"
    r"entire tool[- ]?set|(?:phase|stage|step|role)[- ]specific tools?|per[- ](?:phase|stage) tools?|"
    r"tools? (?:selection|visibility|exposure|subset\w*|filter\w*|mask\w*|restriction\w*|routing|"
    r"availability|isolation)|expos\w* (?:all|every|the full|the entire)")
AUTHORISATION_RE = re.compile(
    r"(?i)approv\w*|allow[- ]?list|deny[- ]?list|block[- ]?list|white[- ]?list|black[- ]?list|"
    r"permission\w*|capabilit\w*|authori[sz]\w*|consent|confirm\w*|access control|policy engine|"
    r"privilege\w*|\brbac\b|\bacls?\b")

# 3. tools_ablation_is_context ---------------------------------------------------------------------
# "w/o tools" on filesystem_access: an arm that loses information it had no other way to get
# (project structure, dependencies) is a context-strategy change (A2); an arm that keeps the
# information but loses write access / scope stays G2; a bare "tools" label is the tool set (B2).
TOOLS_LABEL_RE = re.compile(r"(?i)\btools?\b|\btool[- ]?(?:use|calls?|access)\b")
INFO_LOSS_RE = re.compile(
    r"(?i)cannot (?:access|read|see|inspect|browse|view|list|explore|navigate|retrieve|look up)|"
    r"(?:no|without) (?:access|visibility) to|"
    r"(?:read|inspect|explore|browse|navigate|view|look up) (?:the )?(?:\w+ )?(?:project|repo\w*|"
    r"dependenc\w*|codebase|file ?system|files|director\w*|structure)|project structure|"
    r"dependenc\w*|repository structure|codebase structure")
WRITE_LOSS_RE = re.compile(
    r"(?i)\bwrit(?:e|es|ing|ten)\b|\bmodif\w*|\bedit\w*|read[- ]only|\bscop\w*|\bcreate files?|"
    r"\bdelet\w*|workspace boundary")

# 6. cost_component_not_a_limit ---------------------------------------------------------------------
# cost_controls (F2) holds a contrast only when the component LIMITS spending: a token, step, call or
# dollar budget, a spend cap, a stop-to-save-cost rule. Caching is state (D1 within a run, D3 across
# runs); routing between base models is a model variant (`is_model_routing`, above); a "regression
# budget" or anything else not evidently about cost is unmapped.
_SPEND_OBJ = (r"(?:tokens?|steps?|turns?|calls?|iterations?|rounds?|dollars?|cost|spend\w*|compute|"
              r"api|quer(?:y|ies)|requests?|usd|money|price|inference)")
_LIMIT_WORD = r"(?:budget\w*|caps?|capped|limit\w*|ceiling|quota|constrain\w*)"
SPEND_LIMIT_RE = re.compile(
    rf"(?i)\b{_SPEND_OBJ}[- ]?{_LIMIT_WORD}|\b{_LIMIT_WORD} (?:on|of|for) (?:\w+ ){{0,2}}{_SPEND_OBJ}|"
    rf"\bmax(?:imum)?[- _]?(?:number of )?{_SPEND_OBJ}|\$\s?\d+(?:\.\d+)?\s*{_LIMIT_WORD}|"
    r"(?:stop|halt|terminat\w*|early[- ]?(?:stop|exit)\w*)[^.;]{0,40}(?:sav|reduc|limit|lower)\w*"
    r"[^.;]{0,20}(?:cost|tokens?|spend\w*|budget)|cost[- ]aware (?:stop\w*|termination|halting|exit)|"
    r"budget[- ](?:aware|control\w*|enforce\w*|manag\w*)")
CACHE_RE = re.compile(r"(?i)cach\w*|memoi[sz]\w*|\bmemo\b|kv[- ]?cache")
ACROSS_RUNS_RE = re.compile(
    r"(?i)across (?:runs|tasks|sessions|episodes|queries|problems)|future (?:tasks|runs|queries)|"
    r"persist\w*|cross[- ](?:task|session|run|episode)|on disk|between runs|previous (?:runs|tasks)|"
    r"(?:similar|later|subsequent) (?:tasks|queries|problems)")
WITHIN_RUN_RE = re.compile(
    r"(?i)within (?:a|the|one|each) (?:run|episode|task|session|trajectory)|"
    r"per[- ](?:run|task|episode|trajectory)|same (?:run|task|trajectory|episode)|intra[- ]?(?:task|run)|"
    r"kv[- ]?cache|repeated (?:tool )?calls? in")
ROUTING_RE = re.compile(r"(?i)\brout\w*|\bcascad\w*|model selection|model switch\w*")
TIMEOUT_LIMIT_RE = re.compile(
    r"(?i)time[- ]?outs?|time limit|deadline|wall[- ]?clock|max(?:imum)? (?:time|duration)|time budget")

# 4. scores_not_separable: two printed numbers run together ("74.2870.90", "0.265015.80"), so which
# column the arm's score came from cannot be told from the quoted evidence.
RUN_TOGETHER_RE = re.compile(r"\d+\.\d{2}\d+\.\d")
# 5. delta_metric_as_score: the metric column IS a difference, printed without a sign, so
# `signed_delta_as_score` cannot see it.
DELTA_METRIC_RE = re.compile(r"(?i)^\s*(?:[∆Δ]|delta\b|gain\b|improvement\b)")

# 7. direction_contradicts_label ------------------------------------------------------------------
REMOVAL_LABEL_RE = re.compile(
    r"(?i)w/o|w/out|\bwithout\b|\bno\s+\S|^\s*[-−–—]\s*\S|\bminus\b|\bremov\w*")
#: "+" counts only LEADING the label (or a parenthesis): "Dual Controller + Global Memory" lists the
#: components a reduced configuration keeps; it does not add one to the full system
ADDITION_LABEL_RE = re.compile(
    r"(?i)\bw/(?!o|out)\s*\S|\bwith\b|(?:^|\()\s*\+\s*\S|\badd(?:s|ed|ing)?\b")
#: an unambiguous addition: a leading "+ X", "add X" - never a replacement
STRONG_ADDITION_RE = re.compile(r"(?i)(?:^|\()\s*\+\s*\S|\badd(?:s|ed|ing)?\b")
#: "w/ single agent", "only w/ X", "w/ flat memory": a SIMPLER replacement, i.e. a removal
REDUCED_LABEL_RE = re.compile(
    r"(?i)\bonly\b|\bsingle\b|\bflat\b|\bdirect\w*|\bvanilla\b|\bsimple\b|\bnaive\b|"
    r"\brandom\b|\bplain\b|\bbasic\b|\bstatic\b|\bfixed\b|\bdefault\b|\buniform\b")


def _text(row: dict[str, Any], *fields: str) -> str:
    return " ".join(str(row.get(f) or "") for f in fields)


def is_delta_metric(metric: Any) -> bool:
    """The metric is a difference column (∆C, Δ Acc, delta, gain, improvement)."""
    return bool(DELTA_METRIC_RE.search(str(metric or "")))


def scores_not_separable(evidence: Any) -> bool:
    """The quoted evidence runs two decimals together, so the arm's column cannot be identified."""
    return bool(RUN_TOGETHER_RE.search(str(evidence or "")))


def label_signal(label: Any) -> str:
    """`removal`, `addition`, `both` or "" for an arm label, by its printed wording."""
    lab = str(label or "")
    rem, add = bool(REMOVAL_LABEL_RE.search(lab)), bool(ADDITION_LABEL_RE.search(lab))
    return "both" if rem and add else "removal" if rem else "addition" if add else ""


def direction_contradicts_label(row: dict[str, Any], *, direction: str | None = None,
                                category: str | None = None) -> str:
    """Why the arm's printed label contradicts its orientation ("" when it does not).

    A removal label ("w/o", "without", "no ", a leading minus, "minus", "remove") on an arm oriented
    as an ADDITION (component_added, or category augmentation) - unless the full arm's label is
    itself a reduced configuration, relative to which the arm can be an addition. An addition label
    on an arm oriented as a REMOVAL counts only when the addition is unambiguous (a leading "+",
    "add") or the full arm's label is a reduced configuration: "w/ flat memory" beside "Full HMT"
    is a simpler replacement, i.e. a removal, and is left alone. The sign is never flipped here: a
    row whose orientation the label contradicts cannot be trusted either way, and is dropped.
    """
    direction = str(direction if direction is not None else row.get("direction") or "")
    category = str(category if category is not None else row.get("category") or "")
    arm, full = str(row.get("ablated_arm") or ""), str(row.get("full_arm") or "")
    sig, full_sig = label_signal(arm), label_signal(full)
    if (sig == "removal" and (direction == "component_added" or category == "augmentation")
            and full_sig not in ("removal", "both")):
        return (f"label {arm!r} signals removal but the row is oriented as an addition "
                f"({category}/{direction}); full arm {full!r}")
    if (sig == "addition" and direction == "component_removed" and not REDUCED_LABEL_RE.search(arm)
            and (STRONG_ADDITION_RE.search(arm) or full_sig in ("removal", "both"))):
        return f"label {arm!r} signals addition but the row is oriented as a removal; full arm {full!r}"
    return ""


def remap_sandbox(row: dict[str, Any]) -> tuple[str | None, str]:
    """execution_isolation -> (new dimension, note); None keeps G1, "" unmaps."""
    text = _text(row, "component", "ablated_arm", "evidence")
    if SAFETY_METRIC_RE.search(str(row.get("metric") or "")):
        return None, "metric measures safety/containment: stays execution_isolation"
    if FEEDBACK_LOSS_RE.search(text):
        return "self_verification", "the ablated arm can no longer run the code and read the result"
    if ISOLATION_KEPT_RE.search(text):
        return None, "the code still runs, only the isolation boundary differs: stays execution_isolation"
    if EXEC_STEP_RE.search(text):
        return "self_verification", ("sandbox/execution step removed: the agent loses its run-and-read "
                                     "feedback, not an isolation boundary")
    return "", "no execution step and no isolation boundary named: unmapped"


def remap_tool_gating(row: dict[str, Any]) -> tuple[str | None, str]:
    """permission_model -> (new dimension, note); None keeps G4, "" unmaps."""
    if TOOL_GATING_RE.search(_text(row, "component", "ablated_arm", "evidence")):
        return "tool_count", ("every tool exposed / phase-specific tool selection removed: the tool "
                              "interface, not an authorisation on actions")
    if AUTHORISATION_RE.search(_text(row, "component", "ablated_arm")):
        return None, "enforced authorisation on actions: stays permission_model"
    return "", "no enforced authorisation mechanism named: unmapped"


def remap_tools_ablation(row: dict[str, Any]) -> tuple[str | None, str]:
    """filesystem_access with a "tools" arm label -> (new dimension, note); None keeps G2.
    A row whose arm label does not name tools is not this rule's business: (None, "")."""
    if not TOOLS_LABEL_RE.search(str(row.get("ablated_arm") or "")):
        return None, ""
    text = _text(row, "component", "ablated_arm", "evidence")
    if INFO_LOSS_RE.search(text):
        return "env_context_strategy", ("the ablated arm loses information it had no other way to get "
                                        "(project structure / dependencies)")
    if WRITE_LOSS_RE.search(text):
        return None, "information kept, write access/scope lost: stays filesystem_access"
    return "tool_count", "bare 'tools' label with no description: the tool set"


def remap_cost(row: dict[str, Any]) -> tuple[str | None, str]:
    """cost_controls -> (new dimension, note); None keeps F2, "" unmaps."""
    label = _text(row, "component", "ablated_arm")
    text = _text(row, "component", "ablated_arm", "evidence")
    if SPEND_LIMIT_RE.search(label):
        return None, "limits spending (token/step/dollar budget, cap, stop-to-save): stays cost_controls"
    if CACHE_RE.search(label):
        if ACROSS_RUNS_RE.search(text):
            return "state_persistence", "caching across runs"
        if WITHIN_RUN_RE.search(text):
            return "short_term_state", "caching within a run"
        return "", "caching whose scope (within / across runs) the row does not state: unmapped"
    if ROUTING_RE.search(label):
        return "", ("routing, not a spending limit, and the printed arm does not name a change of base "
                    "model (so not a model variant): unmapped")
    return "", "not evidently about limiting cost: unmapped"


REMAP_RULES: dict[str, Callable[[dict[str, Any]], tuple[str | None, str]]] = {
    "sandbox_is_execution_feedback": remap_sandbox,
    "tool_gating_is_tool_interface": remap_tool_gating,
    "tools_ablation_is_context": remap_tools_ablation,
    "cost_component_not_a_limit": remap_cost,
}


def apply_remap(row: dict[str, Any], dimension: str) -> tuple[str, str, str, str]:
    """(guard, action, dimension after, note) for a row on `dimension`; guard "" when no rule reads it.
    action: remapped (a new dimension), dropped (unmapped), retained (the rule kept the dimension)."""
    guard = next((g for g, src in REMAP_SOURCE.items() if src == dimension), "")
    if not guard:
        return "", "", dimension, ""
    new, note = REMAP_RULES[guard](row)
    if new is None:
        return (guard, "retained", dimension, note) if note else ("", "", dimension, "")
    if new == "":
        return guard, "dropped", "", note
    return guard, "remapped", new, note


def is_limit_component(row: dict[str, Any]) -> bool:
    """The component limits spending or time - the only thing F2 / F3 can hold."""
    label = _text(row, "component", "ablated_arm")
    return bool(SPEND_LIMIT_RE.search(label) or TIMEOUT_LIMIT_RE.search(label))


def classification_matches(row: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Every classification guard whose condition holds on the row as the extractor answered it,
    as [(guard, action, note)]: the audit shows each rule that would catch a row, while the funnel
    counts only the one that decided it (the first in GUARD_ORDER)."""
    out: list[tuple[str, str, str]] = []
    if is_delta_metric(row.get("metric")):
        out.append(("delta_metric_as_score", "dropped", f"metric {row.get('metric')!r} is a difference column"))
    m = RUN_TOGETHER_RE.search(str(row.get("evidence") or ""))
    if m:
        out.append(("scores_not_separable", "dropped", f"run-together numbers {m.group(0)!r} in the evidence"))
    guard, action, _new, note = apply_remap(row, str(row.get("dimension") or "").strip())
    if guard and action != "retained":
        out.append((guard, action, note))
    why = direction_contradicts_label(row)
    if why:
        out.append(("direction_contradicts_label", "dropped", why))
    return out


GUARD_ORDER = [
    "malformed_row", "score_not_in_text", "scores_not_colocated", "signed_delta_as_score",
    "delta_metric_as_score", "scores_not_separable",
    "scale_mismatch", "not_a_performance_metric", "model_or_training_variant",
    "dimension_not_design", "low_confidence", "unmapped", "not_an_ablation",
    "sandbox_is_execution_feedback", "tool_gating_is_tool_interface", "tools_ablation_is_context",
    "cost_component_not_a_limit",
    "direction", "direction_contradicts_label",
    "orientation", "duplicate_contrast",
]


def guard_row(row: dict[str, Any], window: str, design_keys: set[str], *,
              conf_floor: float = aa.CONF_FLOOR, default_n: int = aa.DEFAULT_N) -> tuple[str, dict[str, Any]]:
    """(drop reason or "", enriched row). The reasons are the GUARD_ORDER stages, in that order."""
    out = dict(row)
    full = parse_score(row.get("full_score"))
    abl = parse_score(row.get("ablated_score"))
    if full is None or abl is None:
        return "malformed_row", out
    out["full_value"], out["ablated_value"] = full, abl
    if not scores_in_window(row.get("full_score"), row.get("ablated_score"), window):
        return "score_not_in_text", out
    out["score_match"] = score_match(row.get("full_score"), row.get("ablated_score"), window)
    if not scores_colocated(row.get("full_score"), row.get("ablated_score"), window):
        return "scores_not_colocated", out
    if is_signed_delta(row.get("full_score"), row.get("ablated_score")):
        return "signed_delta_as_score", out
    # classification guards: every rule that holds is recorded for the audit (`guards_matched`);
    # the first one in GUARD_ORDER decides the row
    matched = classification_matches(row)
    out["guards_matched"] = ";".join(g for g, _a, _n in matched)
    out["_matched"] = matched
    notes = {g: n for g, _a, n in matched}
    for guard in ("delta_metric_as_score", "scores_not_separable"):
        if guard in notes:
            out["guard_applied"], out["guard_note"] = guard, notes[guard]
            return guard, out
    if scale_mismatch(full, abl):
        return "scale_mismatch", out
    if not is_performance_metric(str(row.get("metric") or "")):
        return "not_a_performance_metric", out
    if is_model_or_training_variant(row):
        return "model_or_training_variant", out
    raw_dim = str(row.get("dimension") or "").strip()
    vote = {"category": row.get("category"),
            "dimension": None if raw_dim.lower() in ("", "unmapped", "null", "none") else raw_dim,
            "direction": row.get("direction"), "confidence": row.get("confidence"),
            "reason": row.get("reason")}
    cls = aa.normalise_vote(vote, design_keys, conf_floor)
    out["norm_category"], out["norm_dimension"] = cls["category"], cls["dimension"] or ""
    out["norm_confidence"], out["demoted"] = cls["confidence"], cls["demoted"]
    category = cls["category"]
    # normalise_vote demotes to category `unmapped` for four reasons; report the reason, not the
    # category, so the funnel says WHY a poolable-looking row was lost.
    demoted = cls["demoted"]
    if demoted == "unknown_category":
        return "not_an_ablation:unknown", out
    if demoted == "dimension_not_design":
        return "dimension_not_design", out
    if demoted == "low_confidence":
        return "low_confidence", out
    if demoted == "no_dimension" or category == "unmapped":
        return "unmapped", out
    if category not in aa.POOLABLE_CATEGORIES:
        return f"not_an_ablation:{category}", out
    applied: list[str] = []
    guard, action, new_dim, note = apply_remap(row, out["norm_dimension"])
    if guard:
        out["guard_note"], out["remap_action"] = note, action
        if action != "retained":
            applied.append(guard)
            out["guard_applied"] = guard
            out["dimension_before_guard"] = out["norm_dimension"]
            out["norm_dimension"] = new_dim
        if action == "dropped":
            return guard, out
    direction = cls["direction"]
    if direction not in ("component_removed", "component_added"):
        return f"direction_{direction}", out
    why = direction_contradicts_label(row, direction=direction, category=category)
    if why:
        applied.append("direction_contradicts_label")
        out["guard_applied"] = ";".join(applied)
        out["guard_note"] = "; ".join(x for x in (out.get("guard_note", ""), why) if x)
        return "direction_contradicts_label", out
    oriented, drop = aa.orient_contrast(full, abl, direction=direction,
                                        metric=str(row.get("metric") or ""),
                                        benchmark=str(row.get("benchmark") or ""),
                                        split=str(row.get("split") or ""), default_n=default_n)
    if oriented is None:
        return drop, out
    out.update(oriented)
    if out["norm_dimension"] in ("cost_controls", "timeouts") and not is_limit_component(row):
        out["guard_flag"] = LIMIT_FLAG
    return "", out


def guard_stage(reason: str) -> str:
    """Drop reason -> its GUARD_ORDER stage (for the survival funnel)."""
    if reason in GUARD_ORDER:   # before the prefix rules: direction_contradicts_label is its own stage
        return reason
    if reason.startswith("not_an_ablation"):
        return "not_an_ablation"
    if reason.startswith("direction_"):
        return "direction"
    if reason in ("denominator_too_small", "variance_not_finite"):
        return "orientation"
    return reason


def load_system_map(path: Path = SYSTEMS) -> dict[str, list[tuple[str, str]]]:
    """record_id -> [(system_id, name)] for papers that are a coded system's source."""
    if not path.exists():
        return {}
    out: dict[str, list[tuple[str, str]]] = {}
    for s in json.loads(path.read_text(encoding="utf-8")):
        papers = s.get("papers") or []
        if isinstance(papers, str):
            try:
                papers = ast.literal_eval(papers)
            except (ValueError, SyntaxError):
                papers = [papers]
        for rid in papers or []:
            out.setdefault(str(rid), []).append((s["id"], s.get("name") or s["id"]))
    return out


def resolve_system_id(record_id: str, system_name: str, system_map: dict[str, list[tuple[str, str]]]) -> str:
    """The coded system id when the paper is a coded system's source, else `corpus:<record_id>`."""
    cands = system_map.get(record_id, [])
    if len(cands) == 1:
        return cands[0][0]
    if cands:
        key = re.sub(r"[^a-z0-9]", "", system_name.lower())
        for sid, name in cands:
            nk = re.sub(r"[^a-z0-9]", "", name.lower())
            if key and nk and (key in nk or nk in key):
                return sid
        return min(c[0] for c in cands)
    return f"corpus:{record_id}"


EXTRA_COLUMNS = ["provenance", "component", "system_name", "full_arm", "score_match", "evidence", "reason",
                 "already_in_coded_harvest", "coded_match_rule", "tier", "prefilter_score",
                 "extract_model", "prompt_version",
                 "dimension_before_guard", "guard_applied", "guard_flag"]
AUDIT_COLUMNS = ["record_id", "row_no", "guard", "action", "dimension_before", "dimension_after",
                 "final_status", "note", "system", "full_arm", "ablated_arm", "component", "category",
                 "direction", "metric", "full_score", "ablated_score", "rel_effect", "evidence",
                 "extractor_reason"]
GUARD_FUNNEL_COLUMNS = ["remapped", "retained", "flagged", "also_matched"]


def _cell(value: Any) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)


def guard_audit(rows: pd.DataFrame, coded_dups: set[tuple[str, int]] | None = None) -> pd.DataFrame:
    """One line per (row, classification guard) event: what each rule did to which row.

    action: remapped (a new dimension), dropped (the rule decided the drop), retained (a remap rule
    read the row and kept its dimension), flagged (kept, but an F2/F3 component that is not a
    limit), also_matched (the rule's condition holds, but an earlier rule decided the row).
    Only rows a classification guard acted on appear; a row dropped earlier by an unrelated guard
    (low_confidence, say) is not in the audit even if a rule would have matched it. `coded_dups`
    holds the (record_id, row_no) of kept rows flagged as already in the coded-set harvest.
    """
    coded_dups = coded_dups or set()
    out: list[dict[str, Any]] = []
    for r in rows.to_dict("records"):
        matched = r.get("_matched") if isinstance(r.get("_matched"), list) else []
        applied = [g for g in _cell(r.get("guard_applied")).split(";") if g]
        remap_action = _cell(r.get("remap_action"))
        flag = _cell(r.get("guard_flag"))
        if not (applied or remap_action or flag):
            continue
        reason = _cell(r.get("drop_reason"))
        if reason:
            final = f"dropped:{reason}"
        elif (r.get("record_id"), int(r.get("row_no"))) in coded_dups:
            final = "already_in_coded_harvest"
        else:
            final = "pool_eligible"
        before = _cell(r.get("dimension_before_guard")) or _cell(r.get("norm_dimension")) \
            or _cell(r.get("dimension"))
        after = _cell(r.get("norm_dimension"))
        base = {"record_id": r.get("record_id"), "row_no": r.get("row_no"), "final_status": final,
                "system": r.get("system"), "full_arm": r.get("full_arm"),
                "ablated_arm": r.get("ablated_arm"), "component": r.get("component"),
                "category": r.get("category"), "direction": r.get("direction"), "metric": r.get("metric"),
                "full_score": r.get("full_score"), "ablated_score": r.get("ablated_score"),
                "rel_effect": _cell(r.get("rel_effect")), "evidence": r.get("evidence"),
                "extractor_reason": r.get("reason")}
        events: list[tuple[str, str, str, str, str]] = []   # guard, action, before, after, note
        notes = {g: n for g, _a, n in matched}
        for g in applied:
            if g in REMAP_SOURCE and remap_action == "remapped":
                events.append((g, "remapped", before, after, _cell(r.get("guard_note")).split("; ")[0]))
            elif g in REMAP_SOURCE:   # remapped to unmapped: the rule drops the row
                events.append((g, "dropped", before, "", _cell(r.get("guard_note"))))
            else:
                events.append((g, "dropped", after or before, "",
                               notes.get(g) or _cell(r.get("guard_note")).split("; ")[-1]))
        if remap_action == "retained":
            g = next(g for g, src in REMAP_SOURCE.items() if src == after)
            events.append((g, "retained", after, after, _cell(r.get("guard_note"))))
        if flag:
            events.append(("cost_component_not_a_limit", "flagged", after, after,
                           f"{flag}: an {after} contrast on a task metric whose component is not a limit"))
        seen = {e[0] for e in events}
        for g, _a, n in matched:
            if g not in seen:
                events.append((g, "also_matched", before, before, n))
        for g, action, b, a, note in events:
            out.append(base | {"guard": g, "action": action, "dimension_before": b,
                               "dimension_after": a, "note": note})
    audit = pd.DataFrame(out, columns=AUDIT_COLUMNS)
    order = {g: i for i, g in enumerate(GUARD_ORDER)}
    if not audit.empty:
        audit["_o"] = audit["guard"].map(order).fillna(99)
        audit = audit.sort_values(["_o", "action", "record_id", "row_no"]).drop(columns="_o")
    return audit.reset_index(drop=True)


def build_outputs(prefilter: pd.DataFrame, windows: dict[str, dict[str, Any]],
                  cache: dict[str, dict[str, Any]], dims: Sequence[dict[str, Any]], *,
                  coded_contrasts: pd.DataFrame | None, system_map: dict[str, list[tuple[str, str]]],
                  failures: dict[str, dict[str, Any]] | None = None,
                  conf_floor: float = aa.CONF_FLOOR, default_n: int = aa.DEFAULT_N) -> dict[str, Any]:
    """Apply the guards to every cached answer; return rows, contrasts, outcomes, funnel, summary."""
    failures = failures or {}
    design_keys = aa.design_dimension_keys(dims)
    pf = prefilter.set_index("record_id")
    all_rows: list[dict[str, Any]] = []
    for rid, entry in cache.items():
        w = windows.get(rid) or {}
        window = w.get("window") or ""
        stale = bool(w) and entry.get("window_sha") != w.get("sha")
        for i, row in enumerate(entry.get("rows") or []):
            if stale:
                reason, enriched = "stale_window", dict(row)
            else:
                reason, enriched = guard_row(row, window, design_keys, conf_floor=conf_floor,
                                             default_n=default_n)
            enriched |= {"record_id": rid, "row_no": i, "drop_reason": reason,
                         "extract_model": entry.get("model", ""),
                         "prompt_version": entry.get("prompt_version", "")}
            all_rows.append(enriched)
    rows = pd.DataFrame(all_rows)
    if rows.empty:
        rows = pd.DataFrame(columns=["record_id", "row_no", "drop_reason"] + ROW_FIELDS)

    # within-corpus duplicates: one cell proposed twice for one paper is one contrast
    kept = rows["drop_reason"] == ""
    if kept.any():
        key = rows.loc[kept, ["record_id", "benchmark", "split", "metric", "full_value", "ablated_value",
                              "ablated_arm"]].astype(str).apply(lambda c: c.str.strip().str.lower())
        dup = key.duplicated(keep="first")
        rows.loc[dup[dup].index, "drop_reason"] = "duplicate_contrast"

    kept = rows["drop_reason"] == ""
    contrasts = rows[kept].copy()
    if not contrasts.empty:
        contrasts["system_id"] = [resolve_system_id(r, str(n or ""), system_map)
                                  for r, n in zip(contrasts["record_id"], contrasts["system"], strict=True)]
        contrasts["label"] = contrasts["ablated_arm"].fillna("").astype(str)
        contrasts["dimension"] = contrasts["norm_dimension"]
        contrasts["category"] = contrasts["norm_category"]
        contrasts["confidence"] = contrasts["norm_confidence"].astype(float)
        contrasts["model"] = contrasts["base_model"].fillna("").astype(str)
        contrasts["provenance"] = PROVENANCE
        contrasts["system_name"] = contrasts["system"]
        contrasts["tier"] = [pf["tier"].get(r, "") for r in contrasts["record_id"]]
        contrasts["prefilter_score"] = [pf["score"].get(r, "") for r in contrasts["record_id"]]
        coded = coded_contrasts if coded_contrasts is not None else pd.DataFrame()
        rules = aa.flag_coded_duplicates(contrasts, coded)
        contrasts["coded_match_rule"] = rules.values
        contrasts["already_in_coded_harvest"] = (rules != "").astype(int).values
        for c in aa.CONTRAST_COLUMNS + EXTRA_COLUMNS:
            if c not in contrasts.columns:
                contrasts[c] = ""
        coded_dups = {(r, int(n)) for r, n, f in zip(contrasts["record_id"], contrasts["row_no"],
                                                        contrasts["already_in_coded_harvest"], strict=True) if f}
        contrasts = contrasts[aa.CONTRAST_COLUMNS + EXTRA_COLUMNS].reset_index(drop=True)
        dup_ids = set(contrasts.loc[contrasts["already_in_coded_harvest"] == 1].index)
    else:
        contrasts = pd.DataFrame(columns=aa.CONTRAST_COLUMNS + EXTRA_COLUMNS)
        dup_ids = set()
        coded_dups = set()

    # per-paper outcomes
    out_rows = []
    by_rec = {rid: g for rid, g in rows.groupby("record_id")} if not rows.empty else {}
    con_by_rec = {rid: g for rid, g in contrasts.groupby("record_id")} if not contrasts.empty else {}
    audit = guard_audit(rows, coded_dups) if not rows.empty else pd.DataFrame(columns=AUDIT_COLUMNS)
    actions_by_rec = {rid: Counter(f"{a.guard}:{a.action}" for a in g.itertuples(index=False))
                      for rid, g in audit.groupby("record_id")} if not audit.empty else {}
    for r in prefilter.itertuples(index=False):
        if r.tier not in ("T10", "T3"):
            continue
        w = windows.get(r.record_id) or {}
        entry = cache.get(r.record_id)
        if not w:
            status = "no_window_yet"
        elif not w.get("window"):
            status = "no_window"
        elif entry is None:
            status = "failed" if r.record_id in failures else "pending"
        elif entry.get("window_sha") != w.get("sha"):
            status = "stale"
        else:
            status = "extracted"
        g = by_rec.get(r.record_id)
        cg = con_by_rec.get(r.record_id)
        reasons = Counter(g["drop_reason"]) if g is not None else Counter()
        n_dup = int(cg["already_in_coded_harvest"].sum()) if cg is not None else 0
        n_kept = (len(cg) - n_dup) if cg is not None else 0
        out_rows.append({
            "record_id": r.record_id, "tier": r.tier, "prefilter_score": r.score,
            "window_chars": len(w.get("window") or ""), "window_segments": (w.get("info") or {}).get("n_segments", 0),
            "status": status,
            "rows_proposed": len(g) if g is not None else 0,
            "rows_pool_eligible": n_kept, "rows_already_in_coded_harvest": n_dup,
            "rows_dropped": int(sum(v for k, v in reasons.items() if k)),
            "drop_reasons": ";".join(f"{k}={v}" for k, v in sorted(reasons.items()) if k),
            "dimensions": ";".join(sorted(set(cg.loc[cg["already_in_coded_harvest"] == 0, "dimension"])))
            if cg is not None else "",
            "guard_actions": ";".join(f"{k}={v}" for k, v in
                                      sorted(actions_by_rec.get(r.record_id, Counter()).items())),
            "model_note": (entry or {}).get("note", ""),
            "extract_model": (entry or {}).get("model", ""),
            "tokens_in": (entry or {}).get("tokens_in", ""), "tokens_out": (entry or {}).get("tokens_out", ""),
            "error": "; ".join(failures.get(r.record_id, {}).get("errors", []))[:300],
        })
    outcomes = pd.DataFrame(out_rows)

    # the survival funnel, guard by guard
    funnel = []
    stages = Counter(guard_stage(x) for x in rows["drop_reason"] if x)
    acts = Counter(zip(audit["guard"], audit["action"], strict=True)) if not audit.empty else Counter()
    zero = dict.fromkeys(GUARD_FUNNEL_COLUMNS, 0)
    remaining = len(rows)
    funnel.append({"stage": "rows_proposed", "dropped": 0, "surviving": remaining} | zero)
    if stages.get("stale_window"):
        remaining -= stages["stale_window"]
        funnel.append({"stage": "stale_window", "dropped": stages["stale_window"], "surviving": remaining}
                      | zero)
    for st in GUARD_ORDER:
        d = stages.get(st, 0)
        remaining -= d
        funnel.append({"stage": st, "dropped": d, "surviving": remaining}
                      | {c: acts.get((st, c), 0) for c in GUARD_FUNNEL_COLUMNS})
    remaining -= len(dup_ids)
    funnel.append({"stage": "already_in_coded_harvest (flag, excluded from pooling)",
                   "dropped": len(dup_ids), "surviving": remaining} | zero)
    funnel_df = pd.DataFrame(funnel)

    eligible = contrasts[contrasts["already_in_coded_harvest"] == 0] if not contrasts.empty else contrasts
    status_counts = Counter(outcomes["status"]) if not outcomes.empty else Counter()
    extracted = outcomes[outcomes["status"] == "extracted"] if not outcomes.empty else outcomes
    summary = {
        "prompt_version": PROMPT_VERSION, "window_version": WINDOW_VERSION,
        "prefilter": {"included": len(prefilter),
                      "tiers": dict(Counter(prefilter["tier"])),
                      "score_ge_10": int((prefilter["score"] >= TIER_HIGH).sum()),
                      "score_ge_3": int((prefilter["score"] >= TIER_LOW).sum())},
        "papers_by_status": dict(status_counts),
        "papers_extracted": len(extracted),
        "papers_extracted_with_any_row": int((extracted["rows_proposed"] > 0).sum()) if len(extracted) else 0,
        "papers_with_pool_eligible_contrast": int(eligible["record_id"].nunique()) if len(eligible) else 0,
        "rows_proposed": len(rows),
        "drop_reasons": dict(Counter(x for x in rows["drop_reason"] if x).most_common()),
        "contrasts_after_guards": len(contrasts),
        "already_in_coded_harvest": len(dup_ids),
        "pool_eligible_contrasts": len(eligible),
        "pool_eligible_by_dimension": ({d: {"contrasts": len(g), "papers": int(g["record_id"].nunique())}
                                        for d, g in eligible.groupby("dimension")} if len(eligible) else {}),
        "tokens_in": int(pd.to_numeric(extracted.get("tokens_in"), errors="coerce").fillna(0).sum()) if len(extracted) else 0,
        "tokens_out": int(pd.to_numeric(extracted.get("tokens_out"), errors="coerce").fillna(0).sum()) if len(extracted) else 0,
        "classification_guards": {
            g: {a: int(n) for (gg, a), n in sorted(acts.items()) if gg == g}
            | {"papers": sorted(set(audit.loc[(audit["guard"] == g) & (audit["action"] != "also_matched"),
                                              "record_id"]))}
            for g in CLASSIFICATION_GUARDS} if not audit.empty else {},
    }
    return {"rows": rows, "contrasts": contrasts, "outcomes": outcomes, "funnel": funnel_df,
            "summary": summary, "audit": audit}


ROWS_OUT_COLUMNS = ["record_id", "row_no", "drop_reason", *ROW_FIELDS, "full_value", "ablated_value",
                    "score_match", "norm_category", "norm_dimension", "norm_confidence", "demoted",
                    "rel_effect", "dimension_before_guard", "guard_applied", "guard_note", "guard_flag",
                    "guards_matched",
                    "extract_model", "prompt_version"]


def write_outputs(built: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = built["rows"].copy()
    for c in ROWS_OUT_COLUMNS:
        if c not in rows.columns:
            rows[c] = ""
    rows[ROWS_OUT_COLUMNS].to_csv(ROWS_CSV, index=False, encoding="utf-8")
    built["contrasts"].to_csv(CONTRASTS_CSV, index=False, encoding="utf-8")
    built["outcomes"].to_csv(OUTCOMES_CSV, index=False, encoding="utf-8")
    built["funnel"].to_csv(FUNNEL_CSV, index=False, encoding="utf-8")
    built["audit"].to_csv(GUARD_AUDIT_CSV, index=False, encoding="utf-8")
    _write_json(SUMMARY_JSON, built["summary"] | {"updated_at": datetime.now(UTC).isoformat(timespec="seconds")})


def load_coded_contrasts(path: Path = CODED_CONTRASTS) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=aa.CONTRAST_COLUMNS)
    return pd.read_csv(path, dtype={"record_id": str}, keep_default_na=False)


def rebuild_all(dims: Sequence[dict[str, Any]], conf_floor: float = aa.CONF_FLOOR) -> dict[str, Any]:
    prefilter = pd.read_csv(PREFILTER_CSV, dtype={"record_id": str}, keep_default_na=False)
    prefilter["score"] = pd.to_numeric(prefilter["score"], errors="coerce").fillna(0).astype(int)
    built = build_outputs(prefilter, load_jsonl(WINDOWS_JSONL), load_jsonl(CACHE_JSONL), dims,
                          coded_contrasts=load_coded_contrasts(), system_map=load_system_map(),
                          failures=_read_failures(), conf_floor=conf_floor)
    write_outputs(built)
    return built


def print_summary(built: dict[str, Any]) -> None:
    s = built["summary"]
    print("\n" + "=" * 96)
    print("CORPUS-WIDE ABLATION HARVEST")
    print("=" * 96)
    print(f"prefilter: {s['prefilter']['included']:,} included; score>=10: {s['prefilter']['score_ge_10']:,}; "
          f"score>=3: {s['prefilter']['score_ge_3']:,}; tiers {s['prefilter']['tiers']}")
    print(f"papers by status: {s['papers_by_status']}")
    print(f"papers extracted: {s['papers_extracted']:,} ({s['papers_extracted_with_any_row']:,} with any row, "
          f"{s['papers_with_pool_eligible_contrast']:,} with a pool-eligible contrast)")
    print(f"rows proposed: {s['rows_proposed']:,}; contrasts after guards: {s['contrasts_after_guards']:,}; "
          f"already in coded harvest: {s['already_in_coded_harvest']:,}; pool-eligible: {s['pool_eligible_contrasts']:,}")
    print("\nguard funnel:")
    for r in built["funnel"].itertuples(index=False):
        extra = ", ".join(f"{c} {getattr(r, c)}" for c in GUARD_FUNNEL_COLUMNS if getattr(r, c, 0))
        print(f"  {r.stage:<58} -{r.dropped:<6,} {r.surviving:>7,}" + (f"   ({extra})" if extra else ""))
    print("\npool-eligible by dimension:")
    for d, v in sorted(s["pool_eligible_by_dimension"].items(), key=lambda kv: -kv[1]["papers"]):
        print(f"  {d:<28} {v['papers']:>4} papers  {v['contrasts']:>5} contrasts")
    print("=" * 96 + "\n")


# ------------------------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------------------------
def setup_logging(level: str = "INFO") -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(RUN_LOG, encoding="utf-8")):
        h.setFormatter(fmt)
        root.addHandler(h)


def acquire_lock(path: Path | None = None) -> bool:
    """False when another extract run is alive: two runs would send the same papers twice."""
    path = path or LOCK
    phase4 = _load_module("phase4_autopilot", SCRIPTS / "phase4_autopilot.py")
    if path.exists():
        try:
            pid = int(path.read_text(encoding="utf-8").strip() or 0)
        except ValueError:
            pid = 0
        if pid and pid != os.getpid() and phase4._alive(pid):
            log.error("another extract run is alive (pid %d); leaving it alone", pid)
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: path.unlink(missing_ok=True))
    return True


def main(argv: Sequence[str] | None = None, backend: Callable[..., Any] | None = None) -> int:
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    p.add_argument("--stage", choices=("prefilter", "windows", "extract", "report", "all"), default="report")
    p.add_argument("--tier", choices=("T10", "T3", "all"), default="T10",
                   help="which prefilter tier to window/extract (all = T10 then T3)")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--effort", default="low", help="measured 2026-09-25 on 10 papers: low keeps the yield (45 vs 40 contrasts) at ~40%% of the time and output tokens")
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=5, help="papers per model call")
    p.add_argument("--max-batch-chars", type=int, default=60000)
    p.add_argument("--max-window-chars", type=int, default=MAX_WINDOW_CHARS)
    p.add_argument("--limit", type=int, default=0, help="extract at most N papers this run (0 = all)")
    p.add_argument("--max-failures", type=int, default=3)
    p.add_argument("--limit-wait", type=int, default=30, help="minutes to wait on a usage limit with no reset time")
    p.add_argument("--max-stalls", type=int, default=12)
    p.add_argument("--deadline-hours", type=float, default=96.0)
    p.add_argument("--rebuild-every", type=int, default=5, help="rebuild the output CSVs every N calls")
    p.add_argument("--conf-floor", type=float, default=aa.CONF_FLOOR)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(list(argv) if argv is not None else None)
    args.tiers = ("T10", "T3") if args.tier == "all" else (args.tier,)
    setup_logging(args.log_level)
    dims = aa.load_dimensions()

    if args.stage in ("prefilter", "all"):
        ids = included_ids()
        pf = run_prefilter(ids, coded=coded_harvest_records())
        tiers = Counter(pf["tier"])
        log.info("prefilter: %d included; T10 %d, T3 %d, below %d, no_fulltext %d -> %s",
                 len(pf), tiers["T10"], tiers["T3"], tiers["below"], tiers["no_fulltext"], PREFILTER_CSV)
    if not PREFILTER_CSV.exists():
        raise SystemExit("run --stage prefilter first")
    prefilter = pd.read_csv(PREFILTER_CSV, dtype={"record_id": str}, keep_default_na=False)
    prefilter["score"] = pd.to_numeric(prefilter["score"], errors="coerce").fillna(0).astype(int)

    if args.stage in ("windows", "all"):
        windows = run_windows(prefilter, tiers=("T10", "T3"), max_chars=args.max_window_chars)
        got = [w for w in windows.values() if w.get("window")]
        chars = sorted(len(w["window"]) for w in got)
        log.info("windows: %d papers windowed, %d with a non-empty window; median %d chars (~%d tokens)",
                 len(windows), len(got), chars[len(chars) // 2] if chars else 0,
                 (chars[len(chars) // 2] // 4) if chars else 0)
    if args.stage in ("extract", "all"):
        if not acquire_lock():
            return 0
        subscription_env()
        windows = load_jsonl(WINDOWS_JSONL)
        exe = ""
        if backend is None:
            sys.path.insert(0, str(SCRIPTS))
            import screen_llm  # the subscription path ONLY; the API backend is never imported
            exe = screen_llm.find_claude_exe() or ""
            if not exe:
                raise SystemExit("claude executable not found (set CLAUDE_CODE_EXE)")
            backend = screen_llm.vote_batch_claude_code
        stats_ = run_extract(args, prefilter, windows, dims, backend, exe,
                             rebuild=lambda: rebuild_all(dims, args.conf_floor))
        log.info("extract finished: %s", stats_)
    built = rebuild_all(dims, args.conf_floor)
    print_summary(built)
    return 0


if __name__ == "__main__":
    sys.exit(main())
