#!/usr/bin/env python
"""Phase 6 task 43: extract every benchmark result a paper reports FOR ITS OWN SYSTEM.

The regression at the end of the review asks whether a design choice (the 38 coded dimensions)
predicts an outcome. That needs the outcome side: for each coded system, the numbers its own
papers claim for it - benchmark, split, metric, score, the LLM behind the number, and cost or
tokens when they are stated. This script builds that table from the fetched full texts with an
LLM, and refuses every row it cannot trace back to the text.

THE MAIN RISK TO PRECISION IS ATTRIBUTION, NOT ARITHMETIC. A results table in a harness paper is
mostly other people's numbers: baselines, ablations of rival systems, leaderboard rows, and the
numbers the related-work section quotes from the systems it compares against. A model asked for
"the results in this paper" will happily hand back SWE-agent's 12.5% as if the paper's own system
had scored it, and such a row is not merely noisy - it silently swaps the dependent variable of
the regression for another system's. Three things push back, and none of them is sufficient:

1. The prompt names the system (id, frame name, registry name and aliases) and says, at length,
   that a number belonging to any other system or to a baseline must be left out.
2. ``--only-own`` (on by default) re-checks the answer: every row carries ``system_name``, the
   name the PAPER uses for the row it was read from, and a row whose name does not plausibly
   refer to this system - token-wise, or as a self-reference label like "Ours" - goes to the
   rejects file with reason ``not_own_system``. A row that does not say goes there too.
3. Each row's number must appear in that row's verbatim quote (``score_not_in_quote``), which
   catches a number carried over from a neighbouring table row.

What survives all three is still a human-checkable claim rather than a verified one: see the
residual risks at the bottom of this docstring.

EVIDENCE IS MANDATORY PER ROW. Every row is quoted, and every quote is checked verbatim
(whitespace- and punctuation-normalised, ``fulltext_screen.quote_in_text``) against the exact
bundle text that was sent, exactly as ``scripts/code_system.py`` checks a coded cell. A row whose
quote is a paraphrase, or whose number is not in its quote, is written to
``data/results_rejects.csv`` and never to ``data/results.csv``. ``data/results.csv``'s columns are
frozen by ``scripts/validate.py``, so the quote, the locator, the record it came from and every
flag live in the sidecar ``data/results_evidence.csv``, keyed by a ``row_id`` that the row's
``notes`` column repeats (``row_id=<id>``).

NOTHING IS INVENTED. A percentage becomes a bare number (``38.0``, never ``"38%"``); the metric
keeps the paper's own wording (``% resolved``, ``accuracy``, ``pass@1``); dates are ISO; cost,
tokens, split and date are left EMPTY when the paper does not state them, and an unparseable one
is dropped with a flag rather than repaired. Two splits, or two backbone models, are two rows.
``comparable_key`` is always empty: a separate script fills it once the benchmark names are
harmonised.

Evidence bundle: the member records' full texts (reference lists removed), assembled by
``code_system.assemble_bundle`` so that the text sent here and the text sent by the coder are
built the same way and a quote can be re-checked against either. ``--repo-share`` defaults to 0
because results live in papers; raise it to let a README's own benchmark table in as well.

Backend: Claude Code headless through ``screen_llm.vote_batch_claude_code`` (subscription), or
``--backend api`` through ``code_system.make_api_backend``; injectable as ``main(..., backend=...)``
so the tests run without a model. Resumable: a system in ``data/results_extract_status.csv`` is
skipped (including one that legitimately reports nothing), ``--redo <system_id>`` drops that
system from all four files and extracts it again. The last line of a run is ``SUMMARY {json}``.

Outputs (``--out-dir``, default ``data/``):
    results.csv                   the 12 frozen columns, appended
    results_evidence.csv          one row per accepted row: quote, locator, record, flags
    results_rejects.csv           one row per refused row, with the reason (never silently lost)
    results_extract_status.csv    the ledger that makes the run resumable
    results_extract.log           the run log

Usage:
    python scripts/extract_results.py --limit 20
    python scripts/extract_results.py --ids swe-agent,openhands --redo swe-agent
    python scripts/extract_results.py --backend api --model opus
    python scripts/extract_results.py --measure 25      # prompt sizes, no model call
    python scripts/extract_results.py --bundle swe-agent

Residual precision risks, which no check here removes:
  * a paper that reports its own system under a name none of our aliases carry (or only as an
    unlabelled table row) loses real rows to ``not_own_system``: this trades recall for precision;
  * a single generic alias ("ACE", "Agent") can wave through a rival with the same token;
  * a number that is genuinely in the text but belongs to a baseline row whose label the model
    copied from the wrong column passes all three checks;
  * the metric string is the paper's, so ``% resolved`` and ``resolve rate`` are two metrics until
    a human harmonises them; scores on different splits of a renamed benchmark are not comparable
    until ``comparable_key`` is filled.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
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

import code_system as cs
import coding_strata
import fulltext_screen as fs
import screen_llm

REPO = Path(__file__).resolve().parents[1]
FRAME = REPO / "data" / "coding_frame.csv"
FULLTEXT_DIR = REPO / "data" / "fulltext"
SYSTEMS_JSON = REPO / "data" / "systems.json"
PAPERS_CSV = REPO / "data" / "papers.csv"
OUT_DIR = REPO / "data"

PROMPT_VERSION = "results-v1-2026-09-24"
CODER = "llm-extract"
DEFAULT_SEED = "results-2026-09-24"

BUNDLE_CHARS = 110_000  # papers only; the p90 coded system has ~92k characters of full text
REPO_SHARE = 0.0        # results are reported in papers, not in READMEs (raise to include both)
QUOTE_MAX_WORDS = 60    # a table-row quote is longer than a prose one; a flag, not a rejection

#: frozen by scripts/validate.py::RESULT_COLUMNS - do not reorder or extend.
RESULT_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd",
                  "tokens", "date", "source_url", "comparable_key", "notes"]

EVIDENCE_COLUMNS = [
    "row_id", "system_id", "record_id", "reported_system_name", "benchmark", "split", "metric",
    "score", "score_raw", "model", "cost_usd", "tokens", "date", "source_url", "evidence_quote",
    "evidence_locator", "quote_verbatim", "score_in_quote", "flags", "note", "extracted_at",
    "coder", "extract_model", "prompt_version", "effort", "call_id",
]
REJECT_COLUMNS = ["reason", *EVIDENCE_COLUMNS]

STATUS_COLUMNS = ["system_id", "name", "rows", "rejected", "no_results", "no_results_reason",
                  "bundle_chars", "prompt_chars", "bundle_truncated", "papers", "missing_papers",
                  "tokens_in", "tokens_out", "cost_usd", "extracted_at", "coder", "extract_model",
                  "prompt_version", "effort", "call_id"]

#: a row is refused for exactly one of these reasons (the first one found, in this order)
REJECT_REASONS = ("own_system_unstated", "not_own_system", "missing_benchmark", "missing_metric",
                  "missing_score", "bad_score", "missing_quote", "quote_not_in_bundle",
                  "score_not_in_quote", "duplicate_row")

csv.field_size_limit(10 ** 8)


# --------------------------------------------------------------------------------------
# Normalisation. Every function returns the normalised text plus the flags it raised; an
# unparseable field becomes empty and flagged, never a guess.
# --------------------------------------------------------------------------------------

NUM = r"[+-]?\d+(?:\.\d+)?"
MULTIPLIER = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def _clean_number_text(raw: Any) -> str:
    """Strip the decoration a paper puts around a number: ``~``, ``%``, ``$``, ``±0.4``, ``(n=500)``."""
    s = str("" if raw is None else raw).strip()
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"\([^)]*\)", " ", s)                                   # parenthetical asides
    s = re.sub(r"\s*(?:±|±|\+/-|\+-)\s*" + NUM + r"\s*%?", "", s)  # a stated error bar
    s = re.sub(r"^(?:~|≈|≃|about|approx\.?|approximately|ca\.?)\s*", "", s, flags=re.IGNORECASE)
    s = s.replace("%", "").replace("$", "").replace(",", "")
    s = re.sub(r"\b(pp|points?|percent|percentage|usd|dollars?)\b", "", s, flags=re.IGNORECASE)
    return s.strip()


def normalise_score(raw: Any) -> tuple[str, float | None, list[str]]:
    """``"38%"`` -> ``("38", 38.0, [...])``; a range or a word -> ``("", None, ["bad_score"])``.

    The text is kept as the paper wrote the digits (``38.0`` stays ``38.0``, ``38`` stays ``38``):
    re-formatting a score through ``float`` would invent a precision the paper did not claim.
    """
    s0 = str("" if raw is None else raw).strip()
    if not s0:
        return "", None, ["missing_score"]
    flags = ["pct_sign_stripped"] if "%" in s0 else []
    s = _clean_number_text(s0)
    if re.fullmatch(NUM, s):
        return s, float(s), flags
    return "", None, [*flags, "bad_score"]


def normalise_int(raw: Any, name: str) -> tuple[str, list[str]]:
    """Token counts: ``"1.2M tokens"`` -> ``"1200000"``; anything else -> empty and flagged."""
    s0 = str("" if raw is None else raw).strip()
    if not s0:
        return "", []
    s = re.sub(r"\b(tokens?|tok|calls?|steps?)\b", "", _clean_number_text(s0), flags=re.IGNORECASE)
    m = re.fullmatch(rf"({NUM})\s*([kKmMbB])?", s.strip())
    if not m:
        return "", [f"{name}_dropped"]
    value = float(m.group(1)) * (MULTIPLIER[m.group(2).lower()] if m.group(2) else 1)
    if value < 0:
        return "", [f"{name}_dropped"]
    return str(round(value)), ([f"{name}_expanded"] if m.group(2) else [])


def normalise_cost(raw: Any) -> tuple[str, list[str]]:
    """Dollars per the paper's own unit (usually per instance); the unit, if stated, goes in notes."""
    s0 = str("" if raw is None else raw).strip()
    if not s0:
        return "", []
    s = re.sub(r"\b(per|each|instance|task|run|problem|episode|query)\b", "",
               _clean_number_text(s0), flags=re.IGNORECASE)
    s = re.sub(r"[/\s]+$", "", s.strip())
    m = re.fullmatch(rf"({NUM})\s*([kKmM])?", s.strip())
    if not m:
        return "", ["cost_dropped"]
    value = float(m.group(1)) * (MULTIPLIER[m.group(2).lower()] if m.group(2) else 1)
    if value < 0:
        return "", ["cost_dropped"]
    return (f"{value:g}"), ([] if not m.group(2) else ["cost_expanded"])


def normalise_date(raw: Any) -> tuple[str, list[str]]:
    """ISO or nothing: ``"March 2025"`` -> ``"2025-03"``, ``"Feb 13, 2025"`` -> ``"2025-02-13"``."""
    s = str("" if raw is None else raw).strip().rstrip(".")
    if not s:
        return "", []
    if re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", s):
        return s, []
    m = re.fullmatch(r"(\d{4})[/.](\d{1,2})(?:[/.](\d{1,2}))?", s)
    if m:
        y, mo, d = m.group(1), int(m.group(2)), m.group(3)
        if 1 <= mo <= 12:
            return (f"{y}-{mo:02d}" + (f"-{int(d):02d}" if d and 1 <= int(d) <= 31 else "")), []
    m = re.fullmatch(r"([A-Za-z]{3,9})\.?\s+(?:(\d{1,2})(?:st|nd|rd|th)?,?\s+)?(\d{4})", s)
    if m:                                    # "March 2025", "Feb 13, 2025"
        mon, day, year = m.group(1), m.group(2), m.group(3)
    else:
        m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})", s)
        if not m:                            # "13 February 2025"
            return "", ["date_dropped"]
        mon, day, year = m.group(2), m.group(1), m.group(3)
    mo = MONTHS.get(mon[:3].lower())
    if mo is None:
        return "", ["date_dropped"]
    if day and 1 <= int(day) <= 31:
        return f"{year}-{mo:02d}-{int(day):02d}", []
    return f"{year}-{mo:02d}", []


def numbers_in(text: str) -> list[float]:
    """Every number in a quote, with PDF-extraction spacing (``38 . 0``) and ``1,234`` repaired."""
    t = str(text or "")
    t = re.sub(r"(?<=\d)\s*([.])\s*(?=\d)", r"\1", t)
    t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)
    out: list[float] = []
    for m in re.finditer(r"\d+(?:\.\d+)?", t):
        try:
            out.append(float(m.group()))
        except ValueError:  # pragma: no cover - the regex cannot produce one
            pass
    return out


def score_in_quote(score: float | None, quote: str) -> tuple[bool, list[str]]:
    """Is the row's number actually in the row's quote? (the check that catches a slipped table row)"""
    if score is None:
        return False, []
    nums = numbers_in(quote)
    if any(math.isclose(n, score, rel_tol=1e-9, abs_tol=1e-9) for n in nums):
        return True, []
    if any(math.isclose(n, score * 100, rel_tol=1e-6, abs_tol=1e-9)
           or math.isclose(n * 100, score, rel_tol=1e-6, abs_tol=1e-9) for n in nums):
        # the same quantity written as a fraction rather than a percentage: kept, but flagged,
        # because the digits in results.csv are then not the digits in the paper
        return True, ["score_scale_differs_from_quote"]
    return False, []


# --------------------------------------------------------------------------------------
# Whose number is it? (--only-own)
# --------------------------------------------------------------------------------------

#: how a results table labels the paper's own row when it does not use the system's name
SELF_LABELS = frozenset({
    "ours", "our", "ourmethod", "ourmethods", "oursystem", "ouragent", "ourapproach", "ourmodel",
    "ourframework", "ourpipeline", "oursfull", "fullsystem", "fullmodel", "thiswork", "thispaper",
    "proposed", "proposedmethod", "proposedsystem", "proposedapproach", "ourfullsystem", "mine",
})
GENERIC_ALIASES = frozenset({"agent", "agents", "system", "llm", "model", "framework", "harness",
                             "baseline", "ours", "tool", "bench", "benchmark", "assistant"})


def squash(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str("" if s is None else s).lower())


def norm_name(s: Any) -> str:
    """Lowercase words; a parenthetical gloss (``ACE (Actor-Critic ...)``) is not part of the name."""
    t = re.sub(r"\([^)]*\)", " ", str("" if s is None else s))
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def _sublist(needle: list[str], hay: list[str]) -> bool:
    n = len(needle)
    return n > 0 and n <= len(hay) and any(hay[i: i + n] == needle for i in range(len(hay) - n + 1))


def system_aliases(row: dict[str, str], sysrec: dict[str, Any] | None = None) -> list[str]:
    """Every name this system is plausibly called: frame name, id, registry name and aliases, repo."""
    out = [row.get("name", ""), row.get("system_id", "")]
    if sysrec:
        out.append(str(sysrec.get("name") or ""))
        out.extend(str(a) for a in (sysrec.get("aliases") or []))
    url = (row.get("repo_url") or "").rstrip("/")
    if url:
        out.append(url.rsplit("/", 1)[-1].removesuffix(".git"))
    seen: dict[str, str] = {}
    for a in out:
        n = norm_name(a)
        if not n or len(squash(n)) < 3 or n in GENERIC_ALIASES:
            continue
        seen.setdefault(squash(n), a.strip())
    return list(seen.values())


def own_system_reason(reported: Any, aliases: list[str]) -> str:
    """``""`` when ``reported`` plausibly names this system, else the rejection reason.

    Token-wise, not substring-wise: ``ACE`` must not match ``ACENet``, while ``SWE-agent (ours)``
    matches ``SWE-agent`` and ``OpenHands`` matches ``Open Hands``.
    """
    rs, rt = squash(reported), norm_name(reported).split()
    if not rs:
        return "own_system_unstated"
    if rs in SELF_LABELS or (rt and rt[0] in ("ours", "our")):
        return ""
    for a in aliases:
        at = norm_name(a).split()
        if squash(a) == rs or _sublist(at, rt) or _sublist(rt, at):
            return ""
    return "not_own_system"


# --------------------------------------------------------------------------------------
# Prompt (system text is fixed; the per-system text is the bundle)
# --------------------------------------------------------------------------------------

INSTRUCTIONS = f"""\
You are extracting benchmark results for a PRISMA systematic review of LLM agent harnesses. For
each SYSTEM below you are given the full text of its own paper(s). Return every quantitative
benchmark or evaluation result THAT PAPER REPORTS FOR THAT SYSTEM, and nothing else.

Answer with one JSON object and no prose:
{{"votes": [{{"record_id": "<system_id>", "results": [ {{...}}, ... ], "no_results_reason": "..."}}]}}

ONLY THIS SYSTEM'S OWN RESULTS. A results table in such a paper is mostly other systems' numbers.
Leave out every number that belongs to: a baseline, a prior or rival system, a leaderboard row for
someone else, a human-performance row, a number the related-work or introduction section quotes
from another paper, and any dataset statistic that is not a result (sizes, counts of instances,
hyper-parameters, prices of models). If you cannot tell whose row a number is, leave it out. An
ablation or variant OF THIS SYSTEM is this system's own result: keep it and say which variant it
is in "note". If the paper reports no results for this system, return "results": [] and say why in
"no_results_reason".

Each element of "results" is:
1. "benchmark": the evaluation set as the paper names it (e.g. SWE-bench, WebArena, GAIA, HumanEval,
   or an internal set with the paper's own name for it).
2. "split": the subset or variant, as the paper names it ("Verified", "Lite", "test", "full",
   "dev"). Empty string if the paper does not say. Two splits are two elements, never one row.
3. "metric": the metric string THE PAPER USES, copied, not translated: "% resolved", "accuracy",
   "pass@1", "success rate", "F1". Do not rename it.
4. "score": the number only, with no percent sign and no error bar: 38.0 for "38.0%", 0.71 for
   "0.71". Never a range, never "38-41", never "best". If the paper gives mean +- sd, give the mean.
5. "model": the LLM / backbone this number was produced with, as the paper writes it
   ("GPT-4o", "claude-3-5-sonnet-20241022", "Llama-3.1-70B"). Empty string if the paper does not
   say. The same system with two backbones is two elements.
6. "system_name": THE NAME THE PAPER USES for the row this number came from - the label in the
   table or the sentence ("AgentX", "AgentX (ours)", "Ours", "Ours w/o memory"). Copy that label;
   do not substitute the system id. This is how the row's attribution is re-checked.
7. "cost_usd": dollars per the paper's own unit, if the paper states a cost for this run; else "".
8. "tokens": the token count, if the paper states one for this run; else "".
9. "date": the date of the run or the leaderboard snapshot, ISO (YYYY-MM-DD, or YYYY-MM if that is
   all the paper gives); else "".
10. "record_id": the id of the PAPER block above that this number came from.
11. "evidence_quote": at most {QUOTE_MAX_WORDS} words COPIED CHARACTER FOR CHARACTER from the
    evidence, containing the score itself and, if possible, the system label and the metric. Every
    quote is checked against the evidence and every score is checked against its quote: a
    paraphrase, or a quote that does not contain the number, makes the row unusable.
12. "evidence_locator": where you read it - "paper Table 3", "paper Sec. 4.2", "paper p. 7",
    "paper Abstract".
13. "note": optional, short: the variant or ablation, the unit of the cost, a caveat.

LEAVE A FIELD EMPTY RATHER THAN GUESSING. An empty split, model, cost, token count or date is
data; an invented one is a fabricated result. Use only the evidence below - nothing you know about
these systems from elsewhere, and no number you have to compute yourself.

Answer with the JSON object only: no prose, no code fences.
"""


def result_schema() -> dict[str, Any]:
    str_or_num = {"type": ["string", "number"]}
    return {
        "type": "object",
        "properties": {
            "benchmark": {"type": "string"}, "split": {"type": "string"},
            "metric": {"type": "string"}, "score": str_or_num,
            "model": {"type": "string"}, "system_name": {"type": "string"},
            "cost_usd": str_or_num, "tokens": str_or_num, "date": {"type": "string"},
            "record_id": {"type": "string"}, "evidence_quote": {"type": "string"},
            "evidence_locator": {"type": "string"}, "note": {"type": "string"},
        },
        "required": ["benchmark", "metric", "score", "system_name", "evidence_quote",
                     "evidence_locator"],
        "additionalProperties": False,
    }


def batch_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "votes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "record_id": {"type": "string"},  # the system_id (screen_llm orders on it)
                        "results": {"type": "array", "items": result_schema()},
                        "no_results_reason": {"type": "string"},
                    },
                    "required": ["record_id", "results"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["votes"],
        "additionalProperties": False,
    }


def system_prompt() -> str:
    return "== Extraction instructions ==\n" + INSTRUCTIONS


def extract_prompt(batch: list[dict[str, Any]]) -> str:
    out = []
    for it in batch:
        h = it.get("header") or {}
        lines = [f"=== SYSTEM {it['id']}"]
        for k in ("name", "version", "repo_url"):
            if h.get(k):
                lines.append(f"{k}: {h[k]}")
        names = ", ".join(it.get("aliases") or []) or h.get("name", "") or it["id"]
        lines.append(f"This paper's own system is the one called: {names}.")
        lines.append("Extract ONLY results reported for THAT system; every other number in the "
                     "paper belongs to a baseline or a rival system and must be left out.")
        out.append("\n".join(lines) + f"\n--- EVIDENCE for {it['id']} (begin) ---\n{it['document']}\n"
                                      f"--- EVIDENCE for {it['id']} (end) ---")
    return "\n\n".join(out)


# --------------------------------------------------------------------------------------
# Evidence bundle (the coder's, restricted to the papers)
# --------------------------------------------------------------------------------------


def assemble_bundle(row: dict[str, str], cap: int = BUNDLE_CHARS, repo_share: float = REPO_SHARE,
                    root: Path = FULLTEXT_DIR) -> cs.Bundle:
    """The exact text sent for one system, with every cut recorded per part.

    ``code_system.assemble_bundle`` verbatim when repository evidence is wanted; the same assembly
    over the papers alone when it is not (the default), because a repository bundle handed a zero
    budget would otherwise leave an empty REPOSITORY EVIDENCE heading in every prompt.
    """
    if repo_share > 0:
        return cs.assemble_bundle(row, cap, repo_share, root, {})
    parts, missing = cs.collect_parts(row, root, {})
    parts = [p for p in parts if p.kind == "paper"]
    for p in parts:
        p.chars_available = len(p.text)
    head = (f"SYSTEM {row['system_id']}\nname: {row.get('name', '')}\n"
            f"version: {row.get('version', '')}\nrepo_url: {row.get('repo_url', '')}\n")
    cs._water_fill(parts, max(0, cap - len(head) - sum(len(p.heading) + 80 for p in parts)))
    blocks = [head]
    for p in parts:
        note = ("" if not p.truncated else f"\n[TRUNCATED: {p.chars_available - p.chars_used} of "
                                          f"{p.chars_available} characters omitted]")
        blocks.append(f"--- {p.heading} ---\n{p.text[: p.chars_used]}{note}")
    if missing:
        blocks.append("--- MISSING EVIDENCE ---\nno fetched full text for: " + ", ".join(missing))
    b = cs.Bundle(row["system_id"], "\n\n".join(blocks))
    b.parts = [p.manifest() for p in parts]
    b.missing = missing
    return b


# --------------------------------------------------------------------------------------
# One answered row, validated
# --------------------------------------------------------------------------------------


@dataclass
class Ctx:
    """What one system's rows are checked against."""
    system_id: str
    aliases: list[str]
    squashed: str                      # the exact text sent, squashed (fulltext_screen rule)
    urls: dict[str, str] = field(default_factory=dict)   # record_id -> url from papers.csv
    member_ids: tuple[str, ...] = ()
    only_own: bool = True
    quote_max_words: int = QUOTE_MAX_WORDS


@dataclass
class RowCheck:
    row_id: str
    result: dict[str, str]     # the 12 frozen columns
    evidence: dict[str, Any]   # the sidecar row
    flags: list[str]
    reason: str                # "" when the row is accepted

    @property
    def ok(self) -> bool:
        return not self.reason


def check_row(raw: Any, ctx: Ctx, seq: int) -> RowCheck:
    """Validate one answered result. Nothing is repaired into a plausible value."""
    flags: list[str] = []
    r = raw if isinstance(raw, dict) else {}
    if not isinstance(raw, dict):
        flags.append("row_not_object")
    row_id = f"{ctx.system_id}#{seq:02d}"

    benchmark = str(r.get("benchmark") or "").strip()
    split = str(r.get("split") or "").strip()
    metric = str(r.get("metric") or "").strip()
    llm = str(r.get("model") or "").strip()
    reported = str(r.get("system_name") or "").strip()
    quote = str(r.get("evidence_quote") or "").strip()
    locator = str(r.get("evidence_locator") or "").strip()
    note = " ".join(str(r.get("note") or "").split())
    record_id = str(r.get("record_id") or "").strip()

    score_raw = "" if r.get("score") is None else str(r.get("score")).strip()
    score, score_f, f = normalise_score(r.get("score"))
    flags += f
    cost, f = normalise_cost(r.get("cost_usd"))
    flags += f
    tokens, f = normalise_int(r.get("tokens"), "tokens")
    flags += f
    date, f = normalise_date(r.get("date"))
    flags += f

    verbatim = bool(quote) and fs.quote_in_text(quote, ctx.squashed)
    if quote and not verbatim:
        flags.append("quote_not_in_bundle")
    if quote and len(quote.split()) > ctx.quote_max_words:
        flags.append("long_quote")
    traced, f = score_in_quote(score_f, quote) if verbatim else (False, [])
    flags += f
    if not locator:
        flags.append("missing_locator")
    if record_id and ctx.member_ids and record_id not in ctx.member_ids:
        flags.append("record_id_unknown")
        record_id = ""
    source_url = ctx.urls.get(record_id, "") if record_id else ""
    if not source_url:
        source_url = ctx.urls.get(ctx.member_ids[0], "") if ctx.member_ids else ""
        if record_id:
            flags.append("url_from_canonical_record")

    own = own_system_reason(reported, ctx.aliases) if ctx.only_own else ""
    if own:
        flags.append(own)

    reason = ""
    if own:
        reason = own
    elif not benchmark:
        reason = "missing_benchmark"
    elif not metric:
        reason = "missing_metric"
    elif "missing_score" in flags:
        reason = "missing_score"
    elif "bad_score" in flags:
        reason = "bad_score"
    elif not quote:
        reason = "missing_quote"
    elif not verbatim:
        reason = "quote_not_in_bundle"
    elif not traced:
        reason = "score_not_in_quote"

    notes = "; ".join(x for x in (f"row_id={row_id}", note) if x)
    result = {"system_id": ctx.system_id, "model": llm, "benchmark": benchmark, "split": split,
              "metric": metric, "score": score, "cost_usd": cost, "tokens": tokens, "date": date,
              "source_url": source_url, "comparable_key": "", "notes": notes}
    evidence = {"row_id": row_id, "system_id": ctx.system_id, "record_id": record_id,
                "reported_system_name": reported, "benchmark": benchmark, "split": split,
                "metric": metric, "score": score, "score_raw": score_raw, "model": llm,
                "cost_usd": cost, "tokens": tokens, "date": date, "source_url": source_url,
                "evidence_quote": quote, "evidence_locator": locator,
                "quote_verbatim": int(verbatim), "score_in_quote": int(traced),
                "flags": ";".join(flags), "note": note}
    return RowCheck(row_id, result, evidence, flags, reason)


def dedupe(checks: list[RowCheck]) -> None:
    """Two identical rows in one answer are one result; the second is refused, not merged."""
    seen: set[tuple[str, ...]] = set()
    for c in checks:
        if c.reason:
            continue
        key = tuple(c.result[k].lower() for k in ("model", "benchmark", "split", "metric", "score"))
        if key in seen:
            c.reason = "duplicate_row"
            c.flags.append("duplicate_row")
            c.evidence["flags"] = ";".join(c.flags)
        seen.add(key)


# --------------------------------------------------------------------------------------
# Input / output
# --------------------------------------------------------------------------------------


def out_paths(out_dir: Path) -> dict[str, Path]:
    return {"results": out_dir / "results.csv",
            "evidence": out_dir / "results_evidence.csv",
            "rejects": out_dir / "results_rejects.csv",
            "status": out_dir / "results_extract_status.csv",
            "log": out_dir / "results_extract.log"}


def paper_urls(path: Path = PAPERS_CSV) -> dict[str, str]:
    """record_id -> the paper's url, for ``source_url`` (never invented here)."""
    return {r["id"]: (r.get("url") or "").strip() for r in cs.read_csv(path) if r.get("id")}


def systems_index(path: Path = SYSTEMS_JSON) -> dict[str, dict[str, Any]]:
    """system_id -> {name, aliases} from data/systems.json (missing file -> no extra aliases)."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"]: {"name": s.get("name") or "", "aliases": list(s.get("aliases") or [])}
            for s in data if isinstance(s, dict) and s.get("id")}


def done_systems(path: Path) -> set[str]:
    """The systems already extracted - including the ones that legitimately reported nothing."""
    return {r["system_id"] for r in cs.read_csv(path) if r.get("system_id")}


def rewrite_without(path: Path, system_ids: set[str], columns: list[str]) -> int:
    """Drop these systems' rows, keeping the header (what ``--redo`` needs before re-extracting)."""
    if not path.exists():
        return 0
    rows = cs.read_csv(path)
    keep = [r for r in rows if r.get("system_id") not in system_ids]
    if len(keep) == len(rows) and path.stat().st_size:
        return 0
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(keep)
    return len(rows) - len(keep)


def open_append(path: Path, columns: list[str]) -> tuple[Any, csv.DictWriter]:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    fh = path.open("a", encoding="utf-8", newline="")
    w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
    if new:
        w.writeheader()
    return fh, w


# --------------------------------------------------------------------------------------
# One system, one call
# --------------------------------------------------------------------------------------


@dataclass
class Answer:
    system_id: str
    checks: list[RowCheck]
    no_results_reason: str
    result: Any
    prompt_chars: int


def call_backend(backend: Callable[..., Any], exe: str, model: str, system_file: Path,
                 item: dict[str, Any], ctx: Ctx, effort: str | None, text_json: bool) -> Answer:
    """One model call for one system; every returned row comes back validated."""
    res = backend(exe, model, system_file, [item], effort=effort, schema=batch_schema(),
                  prompt=extract_prompt, text_json=text_json)
    vote = (res.votes[0] if res.votes else {}) or {}
    rows = vote.get("results")
    if not isinstance(rows, list):
        rows = []
    checks = [check_row(r, ctx, i) for i, r in enumerate(rows, start=1)]
    dedupe(checks)
    return Answer(item["id"], checks, str(vote.get("no_results_reason") or "").strip(), res,
                  len(extract_prompt([item])))


def _safe(fn: Callable[[Any], Answer], job: Any, log: logging.Logger) -> Answer | None:
    try:
        return fn(job)
    except Exception as exc:  # noqa: BLE001 - one system failing must not stop the run
        log.error("%s failed: %s", job[0]["id"], str(exc)[:300])
        return None


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None, backend: Callable[..., Any] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--frame", type=Path, default=FRAME)
    p.add_argument("--all", action="store_true", help="every frame row, not only coded=1")
    p.add_argument("--ids", default=None, help="comma-separated system_ids restricting the input")
    p.add_argument("--limit", type=int, default=0, help="stop after N systems (0 = all)")
    p.add_argument("--backend", choices=("claude-code", "api"), default="claude-code",
                   help="claude-code spends the subscription allowance; api bills the key in .env")
    p.add_argument("--model", default="opus")
    p.add_argument("--effort", default=None)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--bundle-chars", type=int, default=BUNDLE_CHARS)
    p.add_argument("--repo-share", type=float, default=REPO_SHARE,
                   help="share of the cap for repository evidence (0: papers only)")
    p.add_argument("--only-own", action=argparse.BooleanOptionalAction, default=True,
                   help="refuse a row whose system_name does not plausibly name this system")
    p.add_argument("--redo", action="append", default=[], metavar="SYSTEM_ID",
                   help="drop this system's rows from every output file and extract it again")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--fulltext-dir", type=Path, default=FULLTEXT_DIR)
    p.add_argument("--systems", type=Path, default=SYSTEMS_JSON, help="for names and aliases")
    p.add_argument("--papers", type=Path, default=PAPERS_CSV, help="for source_url")
    p.add_argument("--seed", default=DEFAULT_SEED, help="seed for the run order")
    p.add_argument("--bundle", metavar="SYSTEM_ID", help="print one bundle and exit (no model call)")
    p.add_argument("--print-prompt", action="store_true", help="print the system prompt and exit")
    p.add_argument("--measure", type=int, default=0, metavar="N",
                   help="assemble N prompts, print their size, and exit (no model call)")
    p.add_argument("--text-json", action="store_true", help="ask for JSON as text, not --json-schema")
    p.add_argument("--keep-mcp", action="store_true", help="keep claude.ai MCP connectors loaded")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:  # pytest's capture object has none
        reconfigure(encoding="utf-8")
    if args.print_prompt:  # the read-only exits happen before anything is created on disk
        print(system_prompt())
        return 0

    injected = backend is not None
    rows = {r["system_id"]: r for r in cs.frame_rows(args.frame, args.all)}
    sysidx = systems_index(args.systems)

    def bundle_of(row: dict[str, str]) -> cs.Bundle:
        return assemble_bundle(row, args.bundle_chars, args.repo_share, args.fulltext_dir)

    if args.bundle:
        row = rows.get(args.bundle)
        if row is None:
            print(f"{args.bundle} is not a frame row with coded=1 (try --all)", file=sys.stderr)
            return 2
        b = bundle_of(row)
        print(b.text)
        print("\nBUNDLE " + json.dumps(b.manifest()))
        return 0

    universe = list(rows)
    if args.ids:
        want = {i.strip() for i in args.ids.split(",") if i.strip()}
        universe = [s for s in universe if s in want]
    universe.sort(key=lambda s: coding_strata.sample_hash(s, args.seed))

    if args.measure:
        sizes = []
        for sid in universe[: args.measure]:
            row = rows[sid]
            b = bundle_of(row)
            item = {"id": sid, "document": b.text, "aliases": system_aliases(row, sysidx.get(sid)),
                    "header": {"name": row.get("name", ""), "version": row.get("version", ""),
                               "repo_url": row.get("repo_url", "")}}
            sizes.append({"system_id": sid, "bundle_chars": b.chars, "truncated": b.truncated,
                          "prompt_chars": len(extract_prompt([item]))})
        pc = sorted(s["prompt_chars"] for s in sizes)
        print("MEASURE " + json.dumps({
            "n": len(pc), "system_prompt_chars": len(system_prompt()),
            "prompt_chars_median": pc[len(pc) // 2] if pc else None,
            "prompt_chars_mean": round(sum(pc) / len(pc)) if pc else None,
            "prompt_chars_min": pc[0] if pc else None, "prompt_chars_max": pc[-1] if pc else None,
            "truncated": sum(1 for s in sizes if s["truncated"]),
            "total_chars_with_system_prompt": sum(pc) + len(system_prompt()) * len(pc)}))
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    paths = out_paths(args.out_dir)
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S", force=True,
                        handlers=[logging.StreamHandler(), logging.FileHandler(paths["log"], encoding="utf-8")])
    log = logging.getLogger("extract_results")

    if args.redo:
        drop = set(args.redo)
        n = rewrite_without(paths["results"], drop, RESULT_COLUMNS)
        rewrite_without(paths["evidence"], drop, EVIDENCE_COLUMNS)
        rewrite_without(paths["rejects"], drop, REJECT_COLUMNS)
        rewrite_without(paths["status"], drop, STATUS_COLUMNS)
        log.info("--redo: dropped %d result rows for %s", n, ", ".join(sorted(drop)))

    done = done_systems(paths["status"])
    todo = [s for s in universe if s not in done]
    if args.limit:
        todo = todo[: args.limit]
    log.info("%d systems in scope, %d already extracted, %d to extract",
             len(universe), sum(1 for s in universe if s in done), len(todo))

    if not args.keep_mcp:
        # the claude.ai connectors add ~58k tokens of tool schemas to every headless call and
        # break the prompt cache (measured for scripts/fulltext_screen.py)
        os.environ["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    if backend is None:
        if args.backend == "api":
            try:
                import anthropic
            except ImportError:
                print("the 'anthropic' package is missing: pip install anthropic", file=sys.stderr)
                return 2
            key = screen_llm.api_key()
            if not key:
                print("ANTHROPIC_API_KEY not found in .env or the environment", file=sys.stderr)
                return 2
            backend = cs.make_api_backend(anthropic.Anthropic(api_key=key, max_retries=3, timeout=900.0))
        else:
            backend = screen_llm.vote_batch_claude_code
    exe = ""
    if backend is screen_llm.vote_batch_claude_code:
        exe = screen_llm.find_claude_exe() or ""
        if todo and not exe:
            print("claude executable not found (set CLAUDE_CODE_EXE)", file=sys.stderr)
            return 2

    urls = paper_urls(args.papers)
    tmpdir = Path(tempfile.mkdtemp(prefix="extract_results_"))
    system_file = tmpdir / "system_prompt.txt"
    system_file.write_text(system_prompt(), encoding="utf-8")

    handles: dict[str, Any] = {}
    writers: dict[str, csv.DictWriter] = {}

    def writer_for(key: str, columns: list[str]) -> csv.DictWriter:
        if key not in writers:  # a file appears only when there is something to write into it
            handles[key], writers[key] = open_append(paths[key], columns)
        return writers[key]

    t0 = time.time()
    n_sys = n_rows = n_rej = n_empty = n_noevid = failed = 0
    tok_in = tok_out = 0
    spent = 0.0
    reasons: Counter[str] = Counter()
    flag_counts: Counter[str] = Counter()
    bundle_chars: list[int] = []
    prompt_chars: list[int] = []
    truncated = 0

    def build(system_id: str) -> tuple[dict[str, Any], cs.Bundle, dict[str, str], Ctx] | None:
        row = rows[system_id]
        bundle = bundle_of(row)
        if not bundle.parts:
            log.warning("%s: no evidence on disk (%d member records missing): skipped",
                        system_id, len(bundle.missing))
            return None
        aliases = system_aliases(row, sysidx.get(system_id))
        item = {"id": system_id, "document": bundle.text, "aliases": aliases,
                "header": {"name": row.get("name", ""), "version": row.get("version", ""),
                           "repo_url": row.get("repo_url", "")}}
        ctx = Ctx(system_id, aliases, fs._squash(bundle.text), urls,
                  tuple(cs.member_ids(row)), args.only_own)
        return item, bundle, row, ctx

    for start in range(0, len(todo), max(1, args.workers)):
        chunk = [(s, build(s)) for s in todo[start: start + max(1, args.workers)]]
        for sid, job in chunk:
            if job is not None:
                continue
            # recorded in the ledger so a resumed run does not rebuild the same empty bundle
            writer_for("status", STATUS_COLUMNS).writerow({
                "system_id": sid, "name": rows[sid].get("name", ""), "rows": 0, "rejected": 0,
                "no_results": 1, "no_results_reason": "no fetched full text on disk",
                "bundle_chars": 0, "prompt_chars": 0, "bundle_truncated": 0, "papers": 0,
                "missing_papers": len(cs.member_ids(rows[sid])), "tokens_in": 0, "tokens_out": 0,
                "cost_usd": "0.000000", "coder": CODER, "prompt_version": PROMPT_VERSION,
                "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "extract_model": "", "effort": args.effort or "", "call_id": ""})
            n_empty += 1
            n_noevid += 1
        built = [job for _, job in chunk if job is not None]
        if not built:
            continue

        def run(job: tuple[dict[str, Any], cs.Bundle, dict[str, str], Ctx]) -> Answer:
            return call_backend(backend, exe, args.model, system_file, job[0], job[3],
                                args.effort, args.text_json)

        with ThreadPoolExecutor(max_workers=len(built)) as pool:
            answers = list(pool.map(lambda j: _safe(run, j, log), built))

        for (item, bundle, row, _ctx), ans in zip(built, answers, strict=True):
            if ans is None:
                failed += 1
                continue
            res = ans.result
            meta = {"extracted_at": datetime.now(UTC).isoformat(timespec="seconds"), "coder": CODER,
                    "extract_model": getattr(res, "model", args.model) or args.model,
                    "prompt_version": PROMPT_VERSION, "effort": args.effort or "",
                    "call_id": f"R-{item['id']}-{n_sys + 1:05d}"}
            kept = [c for c in ans.checks if c.ok]
            bad = [c for c in ans.checks if not c.ok]
            for c in kept:
                writer_for("results", RESULT_COLUMNS).writerow(c.result)
                writer_for("evidence", EVIDENCE_COLUMNS).writerow({**c.evidence, **meta})
            for c in bad:
                writer_for("rejects", REJECT_COLUMNS).writerow({**c.evidence, **meta, "reason": c.reason})
                reasons[c.reason] += 1
            for c in ans.checks:
                flag_counts.update(c.flags)
            writer_for("status", STATUS_COLUMNS).writerow({
                "system_id": item["id"], "name": row.get("name", ""), "rows": len(kept),
                "rejected": len(bad), "no_results": int(not kept),
                "no_results_reason": ans.no_results_reason if not kept else "",
                "bundle_chars": bundle.chars, "prompt_chars": ans.prompt_chars,
                "bundle_truncated": int(bundle.truncated),
                "papers": sum(1 for p in bundle.parts if p["kind"] == "paper"),
                "missing_papers": len(bundle.missing), "tokens_in": res.tokens_in,
                "tokens_out": res.tokens_out, "cost_usd": f"{res.cost_usd:.6f}", **meta})
            for fh in handles.values():
                fh.flush()

            n_sys += 1
            n_rows += len(kept)
            n_rej += len(bad)
            n_empty += int(not kept)
            tok_in += res.tokens_in
            tok_out += res.tokens_out
            spent += res.cost_usd
            bundle_chars.append(bundle.chars)
            prompt_chars.append(ans.prompt_chars)
            truncated += int(bundle.truncated)
            log.info("%s: %d rows, %d rejected, %d chars sent, $%.4f (%d/%d systems, $%.2f this run)",
                     item["id"], len(kept), len(bad), ans.prompt_chars, res.cost_usd,
                     n_sys, len(todo), spent)

    for fh in handles.values():
        fh.close()
    shutil.rmtree(tmpdir, ignore_errors=True)

    secs = time.time() - t0
    summary = {
        "prompt_version": PROMPT_VERSION, "model": args.model, "effort": args.effort,
        "backend": "injected" if injected else args.backend, "only_own": bool(args.only_own),
        "workers": args.workers, "systems_in_scope": len(universe), "systems_extracted_now": n_sys,
        "systems_failed": failed, "rows_extracted": n_rows, "rows_rejected": n_rej,
        "systems_no_results": n_empty, "systems_without_fulltext": n_noevid,
        "reject_reasons": dict(reasons.most_common()),
        "flags": dict(flag_counts.most_common()),
        "bundle_chars_mean": round(sum(bundle_chars) / len(bundle_chars)) if bundle_chars else None,
        "bundle_chars_max": max(bundle_chars) if bundle_chars else None,
        "prompt_chars_mean": round(sum(prompt_chars) / len(prompt_chars)) if prompt_chars else None,
        "bundles_truncated": truncated, "tokens_in": tok_in, "tokens_out": tok_out,
        "cost_usd": round(spent, 3), "cost_per_system_usd": round(spent / n_sys, 4) if n_sys else None,
        "rows_per_system": round(n_rows / n_sys, 2) if n_sys else None,
        "wall_seconds": round(secs, 1), "wall_seconds_per_system": round(secs / n_sys, 2) if n_sys else None,
        "out": str(paths["results"]),
    }
    print("SUMMARY " + json.dumps(summary))
    log.info("SUMMARY %s", json.dumps(summary))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
