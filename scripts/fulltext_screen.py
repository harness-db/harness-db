#!/usr/bin/env python
"""Automated full-text screening (protocol section 3 decision procedure, Amendment 4).

For every record forwarded by the title/abstract stage (``data/screening/fulltext_queue.csv``)
whose full text was retrieved by ``scripts/fetch_fulltext.py`` (``data/fulltext/<safe id>.txt``,
listed ``ok`` in ``data/screening/fulltext_index.csv``), an LLM applies steps 1-12 of the
decision procedure to the document, quotes the text that decides each step, estimates
codability (criterion b, protocol 4.7) as the list of the 38 dimensions the document gives
evidence for, and names the system (name, version, repository, first release). Records the
fetcher could not retrieve are excluded ``not_retrievable`` without an LLM call; records the
fetcher has not reached yet are skipped (pending) and picked up by the next, resumable run.

Condenser. A document is cut to a focused excerpt of at most ``--cap-words`` (6,000) words:
the fetched title, the opening of the text (abstract and introduction, first 1,500 words), every
section heading, then the paragraphs that contain high-signal terms (agent, loop, tool, sandbox,
max steps, github.com, we propose, ...), deduplicated. When the high-signal paragraphs do not all
fit, the ones with the most distinct signal terms are kept (ties: earlier first) and the kept
ones are emitted in document order, so implementation details in late sections and appendices
compete with introductory prose instead of losing to it by position. The references section is
skipped. Repository bundles put the README first. A document shorter than the cap is sent whole.

Prompt (``ft-v1-2026-09-18``): the system text is built at run time from
``docs/protocol_prisma_p.md`` (harness definition paragraph, the 12-step decision procedure,
eligibility criteria, minimum codability 4.7 and exclusion codes 4.8) and
``schema/dimensions.json`` (38 dimension ids, names and value sets), plus screening instructions.
Four documents go in each request; the answer is a JSON object validated against
``BATCH_SCHEMA`` by Claude Code (``--json-schema``) and again here (``jsonschema``), and every
quote is checked for verbatim presence in the excerpt the model saw.

Backend: Claude Code headless (``claude -p``), reusing ``scripts/screen_llm.py``'s runner
(subscription login, tools disabled, protocol prompt as the system prompt). ``cost_usd`` is
Claude Code's list-price equivalent, not a charge.

Passes. ``--pass 1`` (default) writes ``data/screening/fulltext_votes.csv``. ``--pass 2`` is the
independent second reading of Amendment 4: same prompt, different document order and batch
composition (different seed), input chosen automatically as every pass-1 include plus a
hash-based random 10% of pass-1 excludes that had an LLM reading; output
``data/screening/fulltext_votes_pass2.csv``. Both files hold one row per record, JSON fields as
JSON strings, and are resumable (records already present are skipped).

Usage:
    python scripts/fulltext_screen.py --ids data/screening/fulltext_pilot.csv --workers 8
    python scripts/fulltext_screen.py --pass 2 --workers 8
    python scripts/fulltext_screen.py --excerpt arxiv:2405.15793      # print one excerpt, no LLM
    python scripts/fulltext_screen.py --print-prompt                   # print the system prompt
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screen_llm
from screen_triage import sample_hash

REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "docs" / "protocol_prisma_p.md"
DIMENSIONS = REPO / "schema" / "dimensions.json"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"
SCREEN_DIR = REPO / "data" / "screening"
FULLTEXT_DIR = REPO / "data" / "fulltext"
INDEX = SCREEN_DIR / "fulltext_index.csv"
QUEUE = SCREEN_DIR / "fulltext_queue.csv"
OUT = {1: SCREEN_DIR / "fulltext_votes.csv", 2: SCREEN_DIR / "fulltext_votes_pass2.csv"}

PROMPT_VERSION = "ft-v1-2026-09-18"
SEED = {1: 20260918, 2: 20260919}  # document order and batch composition per pass
PASS2_SAMPLE_SEED = 20260920  # which pass-1 excludes get the second reading
PASS2_EXCLUDE_FRACTION = 0.10
BATCH_SIZE = 4
CAP_WORDS = 6000
OPENING_WORDS = 1500
HEADINGS_MAX_WORDS = 500
CHUNK_WORDS = 220  # paragraphs longer than ~1.6x this are split at sentence boundaries
QUOTE_MAX_WORDS = 30
MIN_CODABLE = 19
REQUIRED_LAYERS = ("A", "B", "C")

EXCLUSION_CODES = ["out_of_scope", "no_harness_description", "duplicate_system", "not_retrievable", "other"]
SUBREASONS = ["no_loop", "no_actions", "component_only", "framework_no_default", "embodied", "date", "training_only",
              "evaluation_only", "survey", "benchmark_only", "codability", "language", "other"]
VERDICTS = ["pass", "fail", "goto_10", "not_applicable"]

COLUMNS = [
    "record_id", "pass", "decision", "exclusion_code", "exclusion_subreason", "deciding_step", "confidence",
    "system_name", "system_version", "repo_url", "release_date", "codable_count", "codable_count_computed",
    "layers_covered", "codable_dimensions", "step_evidence", "systems_mentioned", "document_title_seen",
    "candidate_title", "candidate_source", "source_used", "fetched_url", "fulltext_words", "excerpt_words",
    "quotes_total", "quotes_verbatim", "flags", "model", "prompt_version", "effort", "seed", "batch_id",
    "batch_started_at", "batch_seconds", "tokens_in", "tokens_out", "cache_read", "cache_write", "cost_usd",
]
JSON_COLUMNS = ("layers_covered", "codable_dimensions", "step_evidence", "systems_mentioned", "flags")

# --------------------------------------------------------------------------------------
# Output schema
# --------------------------------------------------------------------------------------


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"anyOf": [schema, {"type": "null"}]}


def dimension_ids(path: Path = DIMENSIONS) -> list[str]:
    return [d["id"] for d in json.loads(path.read_text(encoding="utf-8"))["dimensions"]]


def record_schema(dim_ids: list[str] | None = None) -> dict[str, Any]:
    dim_ids = dim_ids or dimension_ids()
    step = {"type": "integer", "enum": list(range(1, 13))}
    # Property order is generation order: identification and evidence (steps, codable dimensions) come
    # before the decision fields, so the decision follows from the evidence rather than the reverse.
    props: dict[str, Any] = {
        "record_id": {"type": "string"},
        "document_title_seen": {"type": "string"},
        "system_name": _nullable({"type": "string"}),
        "system_version": _nullable({"type": "string"}),
        "repo_url": _nullable({"type": "string"}),
        "release_date": _nullable({"type": "string"}),
        "systems_mentioned": {"type": "array", "items": {"type": "string"}},
        "step_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"step": step, "verdict": {"type": "string", "enum": VERDICTS}, "quote": {"type": "string"}},
                "required": ["step", "verdict", "quote"],
                "additionalProperties": False,
            },
        },
        "codable_dimensions": {"type": "array", "items": {"type": "string", "enum": dim_ids}},
        "codable_count": {"type": "integer"},
        "layers_covered": {"type": "array", "items": {"type": "string", "enum": list("ABCDEFGH")}},
        "decision": {"type": "string", "enum": ["include", "exclude"]},
        "exclusion_code": _nullable({"type": "string", "enum": EXCLUSION_CODES}),
        "exclusion_subreason": _nullable({"type": "string", "enum": SUBREASONS}),
        "deciding_step": step,
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    }
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def batch_schema(dim_ids: list[str] | None = None) -> dict[str, Any]:
    # top-level key "votes" so that screen_llm's runner (which reads so["votes"]) can be reused as is
    return {"type": "object", "properties": {"votes": {"type": "array", "items": record_schema(dim_ids)}},
            "required": ["votes"], "additionalProperties": False}


# --------------------------------------------------------------------------------------
# Full-text files and the condenser
# --------------------------------------------------------------------------------------

HEADER_KEYS = ("record_id", "source_used", "fetched_url", "fetched_title", "fetched_at")


def safe_id(record_id: str) -> str:
    return re.sub(r"[:/\\]", "__", record_id)


def fulltext_path(record_id: str, root: Path = FULLTEXT_DIR) -> Path:
    return root / f"{safe_id(record_id)}.txt"


def parse_fulltext(raw: str) -> tuple[dict[str, str], str]:
    """Split a fetched file into its 5-line header and the text.

    Header lines are read as ``key: value`` / ``key=value`` / ``key<TAB>value``; a line that does
    not carry a known key is taken positionally (record_id, source_used, fetched_url,
    fetched_title, fetched_at)."""
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header: dict[str, str] = {}
    for i, line in enumerate(lines[:5]):
        m = re.match(r"^\s*#?\s*([A-Za-z_]+)\s*(?::|=|\t)\s?(.*)$", line)
        if m and m.group(1).lower() in HEADER_KEYS:
            header[m.group(1).lower()] = m.group(2).strip()
        else:
            header[HEADER_KEYS[i]] = line.strip()
    body = lines[5:]
    while body and (not body[0].strip() or re.fullmatch(r"\s*(-{3,}|={3,})\s*", body[0])):
        body = body[1:]
    return header, "\n".join(body)


SIGNAL_TERMS: dict[str, str] = {  # term -> regex (word-bounded, case-insensitive)
    "agent": r"agents?", "loop": r"loops?", "iteration": r"iterat(?:ion|ions|ive|ively|es|ed)", "step": r"steps?",
    "tool": r"tools?", "action": r"actions?", "observation": r"observations?", "environment": r"environments?",
    "sandbox": r"sandbox(?:es|ed|ing)?", "docker": r"docker", "container": r"containers?|containeri[sz]ed",
    "execute": r"execut(?:e|es|ed|ing|ion|ions|or)", "shell": r"shell|bash", "memory": r"memor(?:y|ies)",
    "context": r"contexts?", "prompt": r"prompts?|prompting", "plan": r"plan|plans|planning|planner",
    "verify": r"verif(?:y|ies|ied|ication|ier|iers)", "test": r"tests?|testing", "retry": r"retr(?:y|ies|ied)",
    "budget": r"budgets?", "max steps": r"max(?:imum)?[ _-]?(?:number of )?(?:steps|turns|iterations)",
    "terminate": r"terminat(?:e|es|ed|ion|ing)|stop(?:ping)? (?:condition|criteri(?:on|a))",
    "trace": r"traces?|tracing|trajector(?:y|ies)", "log": r"logs?|logging|logged",
    "github.com": r"github\.com", "repository": r"repositor(?:y|ies)|repo", "open-source": r"open[- ]source[ds]?",
    "release": r"releas(?:e|es|ed|ing)", "we propose": r"we propose", "we introduce": r"we (?:introduce|present)",
    "framework": r"frameworks?",
}
SIGNAL_RE = {k: re.compile(rf"(?<![A-Za-z0-9]){v}(?![A-Za-z0-9])", re.IGNORECASE) for k, v in SIGNAL_TERMS.items()}

SECTION_WORDS = (r"abstract|introduction|related work|background|preliminar(?:y|ies)|method(?:s|ology)?|approach|design|"
                 r"architecture|implementation|experiments?|experimental setup|evaluation|results|analysis|discussion|"
                 r"conclusions?|limitations|future work|references|bibliography|appendi(?:x|ces)|acknowledge?ments?|"
                 r"overview|installation|usage|quick ?start|getting started|features|license|contributing|citation")
HEADING_RES = [
    re.compile(r"^#{1,6}\s+\S.*$"),                                                        # markdown
    re.compile(r"^\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+[A-Z][^.!?]{1,90}$"),                   # "3.2 Tool design"
    re.compile(rf"^(?:{SECTION_WORDS})\b[^.!?]{{0,50}}$", re.IGNORECASE),                  # bare section names
]
LETTER_HEADING_RE = re.compile(r"^(?:[A-H](?:\.\d{1,2}){0,3}|[IVX]{1,5})\.?\s+[A-Z][^.!?]{1,80}$")  # "A.1 Prompts", "IV Results"
TREE_HEADING_RE = re.compile(r"^file tree\b", re.IGNORECASE)
TREE_MAX_WORDS = 250
REFERENCES_RE = re.compile(r"^(?:#{1,6}\s*)?(?:\d{1,2}\.?\s+)?(references|bibliography|works cited)\s*$", re.IGNORECASE)
AFTER_REFS_RE = re.compile(r"^(?:#{1,6}\s*)?(?:[A-H](?:\.\d+)*\.?\s+|\d{1,2}\.?\s+)?(appendi(?:x|ces)|supplementary|"
                           r"additional|implementation details|prompts?)\b", re.IGNORECASE)
FILE_MARKER_RE = re.compile(r"^\s*(?:={2,}|-{2,}|#{1,6}|>{2,})?\s*(?:file:\s*|path:\s*)?"
                            r"(?P<path>[\w./-]*?(?:readme(?:\.\w+)?|[\w-]+\.(?:md|rst|txt|mdx|py|ts|js|toml|ya?ml|json)))"
                            r"\s*(?:={2,}|-{2,}|<{2,})?\s*$", re.IGNORECASE)


def _title_like(s: str) -> bool:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z-]*", s)[1:] if len(w) > 3]
    return not words or sum(w[0].isupper() for w in words) / len(words) >= 0.6


GARBAGE_CHARS = set("$@<>\\{}|~^")


def is_garbage(line: str) -> bool:
    """PDF glyph noise (figure text in shifted font encodings such as '$FW7KLQN>...'): a long token-like line
    with markup-free symbols or almost no vowels. Paths and URLs are not garbage."""
    s = line.strip()
    if len(s) < 8 or len(s.split()) > 2 or "/" in s or "." in s:
        return False
    letters = [c for c in s if c.isalpha()]
    vowels = sum(c in "aeiouyAEIOUY" for c in letters)
    return bool(GARBAGE_CHARS & set(s)) or (len(letters) >= 8 and vowels / len(letters) < 0.2)


def is_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s.split()) > 14 or len(s) > 110 or GARBAGE_CHARS & set(s) or is_garbage(s):
        return False
    if any(r.match(s) for r in HEADING_RES):
        return True
    if LETTER_HEADING_RE.match(s) and len(s.split()) <= 8 and _title_like(s):
        return True
    letters = [c for c in s if c.isalpha()]
    digits = sum(c.isdigit() for c in s)
    long_words = [w for w in re.findall(r"[A-Za-z]+", s) if len(w) >= 3]
    return (len(letters) >= 4 and len(s.split()) <= 8 and all(c.isupper() for c in letters) and "+" not in s
            and digits <= 0.2 * len(s.replace(" ", "")) and len(long_words) >= 1 and all(len(w) <= 20 for w in long_words))


def _split_long(par: str, limit: int = CHUNK_WORDS) -> list[str]:
    words = par.split()
    if len(words) <= int(limit * 1.6):
        return [par]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\[(])", par)
    out, cur, n = [], [], 0
    for s in sentences:
        k = len(s.split())
        if cur and n + k > limit:
            out.append(" ".join(cur))
            cur, n = [], 0
        if k > limit * 2:  # one giant "sentence" (e.g. extraction without punctuation): hard split
            w = s.split()
            for i in range(0, len(w), limit):
                out.append(" ".join(w[i : i + limit]))
            continue
        cur.append(s)
        n += k
    if cur:
        out.append(" ".join(cur))
    return out


@dataclass
class Unit:
    kind: str  # "heading" | "para"
    text: str
    words: int


def _join_lines(lines: list[str]) -> str:
    """Join wrapped lines; a line-break hyphen before a lowercase letter is kept but the space dropped ("vari-ous")."""
    out = ""
    for ln in lines:
        if out.endswith("-") and len(out) > 1 and out[-2].isalpha() and ln[:1].islower():
            out += ln
        else:
            out = f"{out} {ln}" if out else ln
    return re.sub(r"\s+", " ", out).strip()


def _flush(buf: list[str], out: list[Unit]) -> None:
    if buf:
        par = _join_lines(buf)
        out.extend(Unit("para", piece, len(piece.split())) for piece in _split_long(par))
        buf.clear()


def clean_markup(text: str) -> str:
    """Strip HTML tags, badge/image markdown and entities (READMEs, web pages); keep link targets."""
    t = re.sub(r"(?is)<(picture|svg|script|style)\b.*?</\1>", " ", text)
    t = re.sub(r"(?is)<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", r"\2 (\1)", t)
    t = re.sub(r"(?s)<[^>\n]{1,400}>", " ", t)
    t = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", " ", t)  # [![badge](img)](link)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)  # ![image](src)
    t = re.sub(r"&(nbsp|amp|lt|gt|quot|#\d+);", lambda m: {"nbsp": " ", "amp": "&", "lt": "<", "gt": ">", "quot": '"'}.get(m.group(1), " "), t)
    return re.sub(r"[ \t]{2,}", " ", t)


def units_of(text: str) -> list[Unit]:
    """Paragraph and heading units in document order."""
    out: list[Unit] = []
    for block in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n")):
        buf: list[str] = []
        for ln in (x for x in block.split("\n") if x.strip() and not is_garbage(x)):
            if is_heading(ln):
                _flush(buf, out)
                h = re.sub(r"\s+", " ", ln.strip().lstrip("#").strip())
                out.append(Unit("heading", h, len(h.split())))
            else:
                buf.append(ln.strip())
        _flush(buf, out)
    return out


README_HEADING_RE = re.compile(r"^\s*#{1,6}\s*(?:subpath\s+)?readme\b", re.IGNORECASE)


def readme_first(text: str) -> str:
    """For a repository bundle whose README section is not the first file section, move it to the front.

    File sections start at markdown headings that name a file (``## README (README.md)``,
    ``### docs/intro.md``) or at decorated markers (``=== path/file.md ===``)."""
    lines = text.split("\n")
    marks = []
    for i, ln in enumerate(lines):
        if README_HEADING_RE.match(ln):
            marks.append((i, True))
        elif (m := FILE_MARKER_RE.match(ln)) and re.match(r"^\s*(?:={2,}|-{2,}|#{1,6}|>{2,}|file:|path:)", ln, re.IGNORECASE):
            marks.append((i, bool(re.search(r"(^|/)readme", m.group("path"), re.IGNORECASE))))
    if not marks or marks[0][1] or not any(is_readme for _, is_readme in marks):
        return text
    bounds = [i for i, _ in marks] + [len(lines)]
    sections = [(is_readme, "\n".join(lines[i:end])) for (i, is_readme), end in zip(marks, bounds[1:], strict=True)]
    first = next(k for k, (is_readme, _) in enumerate(sections) if is_readme)
    pre = "\n".join(lines[: bounds[0]])
    return "\n".join([sections[first][1], pre] + [body for k, (_, body) in enumerate(sections) if k != first])


def signal_terms(text: str) -> set[str]:
    return {k for k, r in SIGNAL_RE.items() if r.search(text)}


@dataclass
class Excerpt:
    text: str
    words: int
    fulltext_words: int
    headings: int
    signal_paragraphs: int
    whole: bool


def _norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def condense(text: str, title: str = "", cap_words: int = CAP_WORDS, opening_words: int = OPENING_WORDS, repo_bundle: bool = False) -> Excerpt:
    """Focused excerpt of at most ``cap_words`` words (title + opening + headings + signal paragraphs)."""
    if repo_bundle:
        text = readme_first(text)
    if repo_bundle or re.search(r"<(?:p|div|a|img|br|picture)\b", text[:20000], re.IGNORECASE):
        text = clean_markup(text)
    units = units_of(text)
    total = sum(u.words for u in units)
    title_line = f"[Title as fetched] {title.strip()}" if title.strip() else "[Title as fetched] (none)"
    budget = cap_words - len(title_line.split())

    # references region: from a References heading to the next appendix-like heading;
    # file-tree region of a repository bundle: from a "File tree" heading to the next heading
    in_refs = [False] * len(units)
    in_tree = [False] * len(units)
    refs = tree = False
    for i, u in enumerate(units):
        if u.kind == "heading":
            tree = bool(TREE_HEADING_RE.match(u.text))
            if REFERENCES_RE.match(u.text):
                refs = True
            elif refs and AFTER_REFS_RE.match(u.text):
                refs = False
        in_refs[i] = refs
        in_tree[i] = tree and u.kind == "para"

    if total <= budget:  # short document: send it whole, in order
        body = "\n\n".join((f"## {u.text}" if u.kind == "heading" else u.text) for u in units)
        ex = f"{title_line}\n\n[Full text, complete]\n{body}"
        return Excerpt(ex, len(ex.split()), total, sum(u.kind == "heading" for u in units), 0, True)

    # 1. opening (abstract + introduction): the first ~opening_words words
    opening, used, i = [], 0, 0
    while i < len(units) and used < opening_words:
        u = units[i]
        if u.kind == "para":
            take = u.text if used + u.words <= opening_words + 60 else " ".join(u.text.split()[: opening_words - used]) + " [...]"
            opening.append(take)
            used += len(take.split())
        else:
            opening.append(f"## {u.text}")
            used += u.words
        i += 1
    opening_end = i

    # 2. all section headings
    heads, hw = [], 0
    for u in units:
        if u.kind == "heading" and hw + u.words <= HEADINGS_MAX_WORDS:
            heads.append(u.text)
            hw += u.words
    head_block = " | ".join(heads) if heads else "(no headings detected)"

    parts_fixed = [title_line, "[Opening: abstract and introduction]", "\n\n".join(opening), "[Section headings]", head_block,
                   "[High-signal paragraphs, document order; [...] marks skipped text]"]
    remaining = budget - sum(len(p.split()) for p in parts_fixed[1:])

    # 3. high-signal paragraphs after the opening, deduplicated, ranked by distinct-term count, emitted in order
    seen = {_norm_key(o) for o in opening}
    cands = []
    for j in range(opening_end, len(units)):
        u = units[j]
        if u.kind != "para" or in_refs[j]:
            continue
        key = _norm_key(u.text)
        if not key or key in seen:
            continue
        seen.add(key)
        terms = signal_terms(u.text)
        if terms:
            cands.append((j, 0 if in_tree[j] else len(terms), u))  # file-tree listings rank last
    chosen: list[tuple[int, Unit]] = []
    tree_words = 0
    for j, _score, u in sorted(cands, key=lambda c: (-c[1], c[0])):
        if in_tree[j] and tree_words + u.words > TREE_MAX_WORDS:
            continue
        if u.words <= remaining:
            chosen.append((j, u))
            remaining -= u.words
            tree_words += u.words if in_tree[j] else 0
        if remaining < 25:
            break
    chosen.sort(key=lambda c: c[0])
    sig, prev = [], opening_end - 1
    for j, u in chosen:
        if j != prev + 1:
            sig.append("[...]")
        sig.append(u.text)
        prev = j
    ex = "\n\n".join(parts_fixed + ["\n\n".join(sig)])
    return Excerpt(ex, len(ex.split()), total, len(heads), len(chosen), False)


def is_repo_bundle(record_id: str, source_used: str) -> bool:
    s = f"{record_id} {source_used}".lower()
    return any(k in s for k in ("github", "repo", "readme"))


# --------------------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------------------


def protocol_blocks(path: Path = PROTOCOL) -> dict[str, str]:
    md = path.read_text(encoding="utf-8")
    sec3 = screen_llm._section(md, "3. Definition of a harness")
    definition = sec3.split("Decision procedure")[0].strip()
    steps_text = sec3.split("Decision procedure", 1)[1]
    steps = {int(m.group(1)): re.sub(r"\s+", " ", m.group(2)).strip()
             for m in re.finditer(r"^(\d+)\.\s+(.*?)(?=^\d+\.\s|\Z)", steps_text, re.MULTILINE | re.DOTALL)}
    if sorted(steps) != list(range(1, 13)):
        raise ValueError(f"expected decision-procedure steps 1-12 in the protocol, found {sorted(steps)}")
    sec4 = screen_llm._section(md, "4. Eligibility criteria")
    return {
        "definition": definition,
        "steps": "\n".join(f"Step {k}. {v}" for k, v in sorted(steps.items())),
        "criteria": sec4.split("\n### ")[0].strip(),
        "codability": screen_llm._section(md, "4.7 Minimum codability"),
        "exclusions": screen_llm._section(md, "4.8 Exclusion reasons"),
    }


def dimensions_block(path: Path = DIMENSIONS) -> str:
    d = json.loads(path.read_text(encoding="utf-8"))
    names = {lay["id"]: lay["name"] for lay in d["layers"]}
    lines = []
    for lay, lay_name in names.items():
        dims = [x for x in d["dimensions"] if x["layer"] == lay]
        cells = []
        for x in dims:
            vals = f" {{{', '.join(x['values'])}}}" if x.get("values") else f" ({x['type']})"
            cells.append(f"{x['id']} {x['name']}{vals}")
        lines.append(f"Layer {lay} {lay_name}: " + "; ".join(cells))
    return "\n".join(lines)


INSTRUCTIONS = f"""\
You read each DOCUMENT (a paper, a repository README/docs bundle, or a documentation page, condensed to an excerpt) and decide include or exclude by the decision procedure above. Your decision is the screening decision of record (protocol Amendment 4); an independent second reading checks it.

1. Screen the document text. The candidate metadata (title, source) only says how the record was found and may belong to a different paper (deduplication and fetch artefacts happen). If the document is about something else, screen the document anyway and report the title you actually see in document_title_seen.
2. Apply steps 1-12 in order and stop at the first exclusion. For every step you reach, add one step_evidence entry {{step, verdict, quote}}. verdict: pass, fail, goto_10 (step 1 only: the record introduces no system and only evaluates, compares, surveys or discusses existing ones), or not_applicable (e.g. step 6 for a system that is not a construction kit). quote: a verbatim span of at most {QUOTE_MAX_WORDS} words copied exactly from the document text that decides the step (keep the document's wording and spelling; no paraphrase, no ellipsis inside); use "" only when the verdict rests on the absence of something.
3. Record types:
   - Introduces, releases or documents a named system that runs a model: apply steps 1-12.
   - Only evaluates, compares, surveys, reviews or discusses existing systems (including running an existing harness with a new model or on a new benchmark, harness-comparison studies, position papers, tutorials): step 1 verdict goto_10, then step 10 fails: decision exclude, exclusion_code duplicate_system, exclusion_subreason evaluation_only (or survey for surveys, reviews and position papers), deciding_step 10. Put every agent system/harness it names in systems_mentioned; system_name null.
   - Benchmark or dataset whose only agents are existing systems or single-call baselines: exclude, out_of_scope, benchmark_only, deciding_step 2. A benchmark that ships its own looping baseline agent is screened as the system "<benchmark> reference agent".
   - Model training, fine-tuning, RL, distillation or trajectory-data generation that introduces no new harness: exclude, out_of_scope, training_only, deciding_step 11 (earlier steps not_applicable). If it also introduces a new loop over an environment, screen that loop as the system.
   - Framework / construction kit: include only through its shipped runnable default agent, named "<framework> (<default agent>)"; no default agent: out_of_scope, framework_no_default, step 6.
   - Component on its own (sandbox, MCP server, memory store, skills pack, tracing SDK, protocol spec, tool library): out_of_scope, component_only, step 5.
   - Self-evolving or meta-optimising method: the outer search is not a system; the released or headline produced harness (else the seed harness) is.
4. Step 7 codability: list in codable_dimensions every dimension id (of the 38 below) for which the DOCUMENT states a value or explicitly states its absence (none counts when the text says so or the design clearly has no such mechanism; "not reported" does not count). Do not infer from what is typical. List a dimension only if you could quote the sentence that codes it; go through the 38 one by one and decide each on the text alone, before and independently of the decision: the threshold must not influence which dimensions you list, and a count just below it is a legitimate exclusion. M4 primary_artifact is always codable from the document itself; M7 only when a star count is stated; M5 only when a date is stated. codable_count = number of ids listed; layers_covered = the letters A-H among them. The rule is: at least {MIN_CODABLE} of 38 with at least one in each of layers {", ".join(REQUIRED_LAYERS)}; failing it is exclusion_code no_harness_description, exclusion_subreason codability, deciding_step 7. Fill codable_dimensions for every record that reaches step 7; for records excluded earlier give the ids you can see anyway (may be empty).
5. Step 8 date: first public release outside 2022-10-01..2026-08-31 is out_of_scope/date. Use release_date for the first public release of the system if the document states it (YYYY-MM-DD, YYYY-MM or YYYY), else null; an arXiv stamp in the text such as "arXiv:2405.15793v1 [cs.SE] 6 May 2024" counts.
6. Step 10 across records (same system already included elsewhere) is decided later by a registry, not by you: for a record that introduces or documents a system, step 10 verdict is pass.
7. Include: decision include, exclusion_code null, exclusion_subreason null, deciding_step 12. Exclude: the exclusion_code and exclusion_subreason of the failing step (subreason null only if none fits), deciding_step = that step.
8. system_name: the system's own name as the document writes it (for excludes: the candidate system or component, if any, else null). system_version: only if stated. repo_url: the system's own code repository URL if the document gives it (not URLs of other projects), else null.
9. systems_mentioned: for every record, up to 25 names of agent systems / harnesses / agent frameworks the document names as existing work, baselines or building blocks (not models, not benchmarks, not the record's own system).
10. confidence: high when the text settles every step you reached, medium when a step rests on a plausible reading, low when the excerpt barely lets you decide.
Answer with one JSON object {{"votes": [...]}}: one entry per document, same record_id values, same order."""


def system_prompt(blocks: dict[str, str] | None = None, dims: str | None = None) -> str:
    b = blocks or protocol_blocks()
    return (
        "You are the full-text screener of a pre-registered PRISMA 2020 systematic review of LLM agent harnesses "
        "(HARNESS-Review).\n\n"
        "== Harness definition (protocol section 3, verbatim) ==\n" + b["definition"] + "\n\n"
        "== Decision procedure, steps 1-12 (protocol section 3, verbatim) ==\n" + b["steps"] + "\n\n"
        "== Eligibility criteria (protocol section 4, verbatim) ==\n" + b["criteria"] + "\n\n"
        "== Minimum codability (protocol section 4.7, verbatim) ==\n" + b["codability"] + "\n\n"
        "== Exclusion reasons (protocol section 4.8, verbatim) ==\n" + b["exclusions"] + "\n\n"
        "== The 38 dimensions (schema/dimensions.json: id, name, values) ==\n" + (dims or dimensions_block()) + "\n\n"
        "== How to screen ==\n" + INSTRUCTIONS
    )


def document_block(item: dict[str, Any]) -> str:
    meta = f"candidate title: {item.get('candidate_title') or '(none)'}; source: {item.get('candidate_source') or ''}; year: {item.get('candidate_year') or ''}"
    fetch = (f"source_used: {item.get('source_used') or ''}; fetched_url: {item.get('fetched_url') or ''}; "
             f"full text {item.get('fulltext_words', 0)} words; excerpt {item.get('excerpt_words', 0)} words")
    return (f'<document record_id="{item["id"]}">\n<candidate_metadata>{meta}</candidate_metadata>\n<fetch>{fetch}</fetch>\n'
            f"<excerpt>\n{item['excerpt']}\n</excerpt>\n</document>")


def user_prompt(batch: list[dict[str, Any]]) -> str:
    ids = ", ".join(b["id"] for b in batch)
    return (f"Screen these {len(batch)} documents (record_ids in order: {ids}). Each is delimited by <document record_id=...>.\n\n"
            + "\n\n".join(document_block(b) for b in batch))


# --------------------------------------------------------------------------------------
# Post-hoc checks on one model answer
# --------------------------------------------------------------------------------------


def _squash(s: str) -> str:
    """Lowercase alphanumerics only: robust to case, punctuation, spacing and line-break hyphens."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def quote_in_text(quote: str, text_squashed: str) -> bool:
    q = _squash(quote)
    return bool(q) and q in text_squashed


def check_vote(v: dict[str, Any], excerpt: str, dim_ids: list[str], item_schema: dict[str, Any]) -> dict[str, Any]:
    """Validate one answer (raises jsonschema.ValidationError) and compute derived fields and flags."""
    jsonschema.validate(v, item_schema)
    flags = []
    dims = [d for d in dict.fromkeys(v["codable_dimensions"]) if d in dim_ids]
    layers = sorted({d[0] for d in dims if d[0] in "ABCDEFGH"})
    if v["codable_count"] != len(dims):
        flags.append("count_mismatch")
    rule_pass = len(dims) >= MIN_CODABLE and all(L in layers for L in REQUIRED_LAYERS)
    if v["decision"] == "include":
        if v["exclusion_code"] is not None:
            flags.append("include_with_exclusion_code")
        if v["deciding_step"] != 12:
            flags.append("include_step_not_12")
        if not rule_pass:
            flags.append("include_fails_codability_rule")
        if not v.get("system_name"):
            flags.append("include_without_system_name")
    else:
        if v["exclusion_code"] is None:
            flags.append("exclude_without_code")
        if v["deciding_step"] == 12:
            flags.append("exclude_at_step_12")
    squashed = _squash(excerpt)
    quotes = [s["quote"] for s in v["step_evidence"] if s["quote"].strip()]
    verbatim = sum(quote_in_text(q, squashed) for q in quotes)
    if any(len(q.split()) > QUOTE_MAX_WORDS for q in quotes):
        flags.append("long_quote")
    if quotes and verbatim < len(quotes):
        flags.append("quote_not_in_excerpt")
    if not any(s["step"] == v["deciding_step"] for s in v["step_evidence"]):
        flags.append("no_evidence_for_deciding_step")
    return {"dims": dims, "layers": layers, "quotes_total": len(quotes), "quotes_verbatim": verbatim, "flags": flags, "rule_pass": rule_pass}


# --------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def ok_status(row: dict[str, str]) -> bool:
    for k in ("status", "fetch_status", "ok", "result"):
        if k in row:
            return str(row[k]).strip().lower() in ("ok", "true", "1", "yes")
    return False


def load_index(path: Path = INDEX) -> dict[str, dict[str, str]]:
    """record_id -> index row (last row wins)."""
    return {r["record_id"]: r for r in read_csv(path) if r.get("record_id")}


def load_ids(path: Path) -> list[str]:
    return [r["record_id"] for r in read_csv(path) if r.get("record_id")]


def load_candidates(path: Path = CANDIDATES) -> dict[str, dict[str, str]]:
    csv.field_size_limit(10**8)
    return {r["id"]: r for r in read_csv(path)}


def pass2_selection(pass1_rows: list[dict[str, str]], fraction: float = PASS2_EXCLUDE_FRACTION, seed: int = PASS2_SAMPLE_SEED) -> list[str]:
    """Every pass-1 include plus a hash-based random ``fraction`` of pass-1 excludes that had an LLM reading."""
    def sampled(r: dict[str, str]) -> bool:
        return r["exclusion_code"] != "not_retrievable" and sample_hash(r["record_id"], seed) < fraction

    return [r["record_id"] for r in pass1_rows if r["decision"] == "include" or sampled(r)]


def build_item(rid: str, cand: dict[str, str], cap_words: int = CAP_WORDS) -> dict[str, Any]:
    header, text = parse_fulltext(fulltext_path(rid).read_text(encoding="utf-8", errors="replace"))
    ex = condense(text, header.get("fetched_title", ""), cap_words=cap_words, repo_bundle=is_repo_bundle(rid, header.get("source_used", "")))
    return {
        "id": rid, "candidate_title": re.sub(r"\s+", " ", cand.get("title") or "").strip(), "candidate_source": cand.get("source") or "",
        "candidate_year": cand.get("year") or "", "source_used": header.get("source_used", ""), "fetched_url": header.get("fetched_url", ""),
        "fulltext_words": ex.fulltext_words, "excerpt_words": ex.words, "excerpt": ex.text,
    }


# --------------------------------------------------------------------------------------
# Rows
# --------------------------------------------------------------------------------------


def _j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False)


def vote_row(item: dict[str, Any], v: dict[str, Any], chk: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": item["id"], "pass": meta["pass"], "decision": v["decision"], "exclusion_code": v["exclusion_code"] or "",
        "exclusion_subreason": v["exclusion_subreason"] or "", "deciding_step": v["deciding_step"], "confidence": v["confidence"],
        "system_name": v["system_name"] or "", "system_version": v["system_version"] or "", "repo_url": v["repo_url"] or "",
        "release_date": v["release_date"] or "", "codable_count": v["codable_count"], "codable_count_computed": len(chk["dims"]),
        "layers_covered": _j(chk["layers"]), "codable_dimensions": _j(chk["dims"]), "step_evidence": _j(v["step_evidence"]),
        "systems_mentioned": _j(v["systems_mentioned"]), "document_title_seen": v["document_title_seen"],
        "candidate_title": item["candidate_title"], "candidate_source": item["candidate_source"], "source_used": item["source_used"],
        "fetched_url": item["fetched_url"], "fulltext_words": item["fulltext_words"], "excerpt_words": item["excerpt_words"],
        "quotes_total": chk["quotes_total"], "quotes_verbatim": chk["quotes_verbatim"], "flags": _j(chk["flags"]),
        **{k: meta[k] for k in ("model", "prompt_version", "effort", "seed", "batch_id", "batch_started_at", "batch_seconds", "tokens_in", "tokens_out", "cache_read", "cache_write", "cost_usd")},
    }


def not_retrievable_row(rid: str, cand: dict[str, str], idx: dict[str, str] | None, pass_no: int) -> dict[str, Any]:
    row = {c: "" for c in COLUMNS}
    row.update({
        "record_id": rid, "pass": pass_no, "decision": "exclude", "exclusion_code": "not_retrievable", "deciding_step": "",
        "codable_count": 0, "codable_count_computed": 0, "layers_covered": "[]", "codable_dimensions": "[]", "step_evidence": "[]",
        "systems_mentioned": "[]", "flags": _j(["no_llm_call"]), "candidate_title": re.sub(r"\s+", " ", cand.get("title") or "").strip(),
        "candidate_source": cand.get("source") or "", "source_used": (idx or {}).get("source_used", ""),
        "model": "none", "prompt_version": PROMPT_VERSION, "tokens_in": 0, "tokens_out": 0, "cost_usd": "0",
    })
    return row


def rewrite_without(path: Path, drop: set[str]) -> None:
    rows = [r for r in read_csv(path) if r["record_id"] not in drop]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--pass", dest="pass_no", type=int, choices=(1, 2), default=1)
    p.add_argument("--backend", choices=("claude-code",), default="claude-code")
    p.add_argument("--model", default="opus")
    p.add_argument("--effort", default="low")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p.add_argument("--cap-words", type=int, default=CAP_WORDS)
    p.add_argument("--ids", default=None, help="CSV with a record_id column restricting the input (e.g. data/screening/fulltext_pilot.csv); default: fulltext_queue.csv")
    p.add_argument("--queue", default=str(QUEUE))
    p.add_argument("--index", default=str(INDEX))
    p.add_argument("--out", default=None)
    p.add_argument("--limit", type=int, default=0, help="stop after N new LLM records (0 = all)")
    p.add_argument("--seed", type=int, default=None, help="order/batch seed (default: 20260918 for pass 1, 20260919 for pass 2)")
    p.add_argument("--max-attempts", type=int, default=4)
    p.add_argument("--max-delay", type=float, default=90.0)
    p.add_argument("--max-consecutive-failures", type=int, default=4)
    p.add_argument("--excerpt", metavar="RECORD_ID", help="print the excerpt of one record and exit (no LLM call)")
    p.add_argument("--print-prompt", action="store_true", help="print the system prompt and exit")
    p.add_argument("--keep-mcp", action="store_true", help="keep claude.ai MCP connectors loaded in the child Claude Code (default: disabled)")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("fulltext_screen")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    if not args.keep_mcp:
        # The claude.ai connector (MCP) tool schemas add ~58k tokens to every headless call even with --tools "" and
        # change between calls, so nothing is reused from the prompt cache; without them the fixed context is ~7.7k
        # tokens and is read from cache (measured 2026-09-18: $0.67 -> $0.02 per call on a one-line document).
        os.environ["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    dim_ids = dimension_ids()
    system = system_prompt()
    if args.print_prompt:
        print(system)
        return 0
    cands = load_candidates()
    if args.excerpt:
        item = build_item(args.excerpt, cands.get(args.excerpt, {}), args.cap_words)
        print(document_block(item))
        return 0

    seed = args.seed if args.seed is not None else SEED[args.pass_no]
    out = Path(args.out) if args.out else OUT[args.pass_no]
    index = load_index(Path(args.index))
    if not index:
        print(f"{args.index} is missing or empty: run scripts/fetch_fulltext.py first", file=sys.stderr)
        return 2
    universe = load_ids(Path(args.ids)) if args.ids else load_ids(Path(args.queue))
    if args.pass_no == 2:
        sel = set(pass2_selection(read_csv(OUT[1])))
        universe = [r for r in universe if r in sel]
        log.info("pass 2 selection: %d records (all pass-1 includes + %.0f%% of pass-1 LLM excludes) within the input", len(universe), PASS2_EXCLUDE_FRACTION * 100)

    existing = read_csv(out)
    # a record excluded not_retrievable earlier whose text has since been fetched is screened again
    revived = {r["record_id"] for r in existing if r["exclusion_code"] == "not_retrievable" and ok_status(index.get(r["record_id"], {})) and fulltext_path(r["record_id"]).exists()}
    if revived:
        log.info("%d earlier not_retrievable records now have full text: re-screening them", len(revived))
        rewrite_without(out, revived)
        existing = [r for r in existing if r["record_id"] not in revived]
    done = {r["record_id"] for r in existing}

    todo, not_ret, pending = [], [], []
    for rid in universe:
        if rid in done:
            continue
        row = index.get(rid)
        if row is None:
            pending.append(rid)
        elif ok_status(row) and fulltext_path(rid).exists():
            todo.append(rid)
        elif ok_status(row):
            pending.append(rid)  # listed ok but the file is not there (yet)
        else:
            not_ret.append(rid)
    todo.sort(key=lambda r: sample_hash(r, seed))
    if args.limit:
        todo = todo[: args.limit]
    log.info("input %d records: %d already done, %d to screen, %d not_retrievable, %d pending (not fetched yet)", len(universe), len(done), len(todo), len(not_ret), len(pending))

    new_file = not out.exists() or out.stat().st_size == 0
    fh = out.open("a", encoding="utf-8", newline="")
    w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
    if new_file:
        w.writeheader()
    for rid in not_ret:
        w.writerow(not_retrievable_row(rid, cands.get(rid, {}), index.get(rid), args.pass_no))
    fh.flush()

    items = []
    for rid in todo:
        try:
            items.append(build_item(rid, cands.get(rid, {}), args.cap_words))
        except OSError as exc:
            log.error("%s: cannot read full text: %s", rid, exc)
    batches = [items[i : i + args.batch_size] for i in range(0, len(items), args.batch_size)]
    exe = screen_llm.find_claude_exe()
    if batches and not exe:
        print("Claude Code CLI not found (set CLAUDE_CODE_EXE or put 'claude' on PATH).", file=sys.stderr)
        return 2
    tmpdir = tempfile.mkdtemp(prefix="fulltext_screen_")
    system_file = Path(tmpdir) / "system_prompt.txt"
    system_file.write_text(system, encoding="utf-8")
    schema = batch_schema(dim_ids)
    item_schema = record_schema(dim_ids)
    log.info("prompt %s: system %d chars; %d batches of <= %d; model %s effort %s; %d workers; out %s", PROMPT_VERSION, len(system), len(batches), args.batch_size, args.model, args.effort, args.workers, out)

    def run_batch(batch: list[dict[str, Any]]) -> tuple[screen_llm.BatchResult, list[dict[str, Any]], str, float]:
        started = datetime.now(UTC).isoformat(timespec="seconds")
        t = time.time()
        res = screen_llm.vote_batch_claude_code(exe, args.model, system_file, batch, args.effort, schema, user_prompt)
        checks = [check_vote(v, it["excerpt"], dim_ids, item_schema) for v, it in zip(res.votes, batch, strict=True)]
        return res, checks, started, time.time() - t

    n = failed = consec = 0
    spent = 0.0
    tok_in = tok_out = 0
    aborted = False
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = {pool.submit(screen_llm.with_retries, (lambda b=b: run_batch(b)), log, f"batch {i + 1}/{len(batches)}", args.max_attempts, args.max_delay): (i, b) for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            i, batch = futs[fut]
            if fut.cancelled():
                continue
            try:
                res, checks, started, secs = fut.result()
            except (RuntimeError, ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired, jsonschema.ValidationError) as exc:
                failed += len(batch)
                consec += 1
                log.error("batch %d (%s) failed permanently: %s", i + 1, ",".join(b["id"] for b in batch), str(exc)[:500])
                if consec >= args.max_consecutive_failures and not aborted:
                    aborted = True
                    log.error("%d consecutive permanent failures (usage limit?): cancelling the rest; re-run to resume", consec)
                    for f in futs:
                        f.cancel()
                continue
            consec = 0
            k = len(batch)
            meta = {"pass": args.pass_no, "model": res.model, "prompt_version": PROMPT_VERSION, "effort": args.effort, "seed": seed,
                    "batch_id": f"p{args.pass_no}-s{seed}-b{i + 1:05d}", "batch_started_at": started, "batch_seconds": round(secs, 1),
                    "tokens_in": round(res.tokens_in / k), "tokens_out": round(res.tokens_out / k), "cache_read": round(res.cache_read / k),
                    "cache_write": round(res.cache_write / k), "cost_usd": f"{res.cost_usd / k:.6f}"}
            for it, v, chk in zip(batch, res.votes, checks, strict=True):
                w.writerow(vote_row(it, v, chk, meta))
            fh.flush()
            n += k
            spent += res.cost_usd
            tok_in += res.tokens_in
            tok_out += res.tokens_out
            log.info("%d/%d records screened, $%.2f list-equivalent, %.0fs elapsed", n, len(items), spent, time.time() - t0)
    fh.close()
    shutil.rmtree(tmpdir, ignore_errors=True)
    secs = time.time() - t0
    rows = [r for r in read_csv(out) if r["record_id"] in set(universe)]
    summary = {
        "pass": args.pass_no, "prompt_version": PROMPT_VERSION, "model": args.model, "effort": args.effort, "workers": args.workers,
        "records_screened_now": n, "records_failed": failed, "not_retrievable_now": len(not_ret), "pending_not_fetched": len(pending),
        "aborted_on_consecutive_failures": aborted, "tokens_in": tok_in, "tokens_out": tok_out, "cost_usd": round(spent, 3),
        "cost_per_record_usd": round(spent / n, 4) if n else None, "wall_seconds": round(secs, 1), "wall_seconds_per_record": round(secs / n, 2) if n else None,
        "decisions_in_file_for_input": dict(Counter(r["decision"] for r in rows)), "out": str(out),
    }
    print("SUMMARY " + json.dumps(summary))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
