#!/usr/bin/env python
"""Turn the harvested public leaderboards into rows of the review's results table.

Input  ``data/raw/leaderboards.jsonl`` (harvest records, one per board *submission*; the scores
       live in ``extra.entries``).
Output ``data/results_leaderboards.csv`` with the twelve columns ``scripts/validate.py``
       enforces for ``data/results.csv``. ``comparable_key`` is left empty: a separate script
       groups rows by benchmark, split and base model (protocol section 9). ``--append-to`` can
       merge into an existing results file instead, but the default is a separate file so the
       leaderboard rows and the paper-extracted rows are merged deliberately.

No network, no model calls: this is a pure re-shaping of data already on disk.

One output row per *entry*, not per harvest record: a single submission usually reports several
splits or several models.

Attribution (the hard part)
---------------------------
``system_id`` may only name a system that exists in ``data/systems.json`` (that is what
``validate.py`` checks - and it rejects an *empty* ``system_id`` as well, so whatever merges these
rows into ``data/results.csv`` must either keep the unattributed ones in their own file or relax
that check; nothing here writes ``results.csv``). Attribution is deliberately lossy and
deliberately conservative: a missing attribution costs a benchmark-level table one row of harness
metadata, whereas a wrong one silently corrupts the system-level regression. The rules:

* the matcher is ``scripts/system_registry.py`` (``norm_name``, ``key_of``, ``keys_match`` - the
  precomputed-key form of ``names_match`` - ``split_version`` and ``repo_key``) - the same
  normalisation that built the registry, never a private one;
* the registry names are every ``systems.json`` name plus that system's ``name_variants`` from
  the census (``data/systems_candidates.csv``);
* a leaderboard name mixes org, harness and model ("AbanteAI MentatBot + GPT 4o (2024-05-13)",
  "Agent S w/ Claude-3.5", "Agent Flan / Agent Flan", "20251108_abacusai-desktop_multiple"), so
  the board-specific splitters below reduce it to harness-name candidates first;
* a candidate is accepted on an exact normalised-key match, or on a single rapidfuzz match at
  96 *with a compatible major version* - "Agent S2" is not allowed to land on "Agent S", because
  protocol 4.4 gives a documented v2 its own system id. 96, not the registry's own 92: the
  registry merged names drawn from one document family, while these come from board free text,
  where 92 is loose enough to put HAL's "HF Open Deep Research" onto "Open Deep Search"
  (ratio 93.3) - two unrelated systems. ``--fuzzy-threshold`` can restore 92;
* more than one candidate system, a name that is only a model string, or a name on the
  stop-list (``RAG``, ``Undisclosed``, ``Tools``, ...) leaves ``system_id`` empty;
* three further vetoes, each of which fired on a real false positive in this data:
  - **over-merged census group**: ``rci-agent`` pools 114 names ("RCI agent", "SWE-agent",
    "Agent S3", "EnIGMA", every ``*-Agent``), so a hit on it says nothing about which system
    ran. A group holding more than ``MAX_GROUP_NAMES`` distinct name keys is refused;
  - **uncorroborated org prefix**: "CodeStory Aide" only matches ``aide`` once "CodeStory" is
    stripped, and ``aide`` is ``github.com/wecoai/aideml`` - a different AIDE. An org-stripped
    match is kept only when the org agrees with the system's repository owner or name, or when
    the registry records no repository at all (the vendor-product case: Jules, Rovo Dev);
  - **divergent name variant**: the match must survive against the system's *canonical* name, not
    only against one of its census name variants. The census merged "Agent S2" (Simular,
    ``simular-ai/Agent-S``) into ``agents-v2`` "Agents 2.0 (agent symbolic learning)"
    (``aiwaves-cn/agents``) and "CoAct-1" into ``coact`` "CoAct"; a variant that does not itself
    match the canonical name is exactly where those merges show, so such a hit is refused.
* when the name matches a *census* system that is not in ``systems.json``, the row stays
  unattributed and ``notes`` names the census id - that is the list of mappings worth adding;
* every refusal is printed at the end of the run, grouped and counted, so the census defects it
  found are visible rather than buried in the CSV.

``notes`` always records the string that was matched on and the method (or the reason for
abstaining), the provenance of ``source_url``, and where ``model`` came from.

GAIA policy
-----------
3,695 of the 3,946 harvest records are GAIA and they are included only under protest:

* the GAIA board (HF ``gaia-benchmark/results_public``) is an open submission log. Its
  submission names are free text ("0707_1", "--query", "final_v2"), 2,523 of 3,773 entries
  carry no model at all, and the board has no verification field - nothing distinguishes a
  reproducible run from a number somebody typed;
* the review's own dedupe already refuses GAIA as a *system* source
  (``scripts/dedupe.py``: ``EXCLUDED_LEADERBOARDS = {"GAIA"}``), so a GAIA submission name is
  not evidence that a harness exists, which is exactly why attribution here is exact-match only;
* so: a row is written for every GAIA entry that carries a usable score, every GAIA row is
  marked ``unverified self-reported public submission`` in ``notes``, and
  ``--skip-boards GAIA`` drops the board in one flag. Analyses that need verified numbers
  should use that flag or filter on the note.

Judgement calls worth knowing about
-----------------------------------
* HAL is a *board*, not a benchmark: its ``benchmark`` field is "HAL" and the underlying
  benchmark is in ``split`` (``corebench_hard``, ``online_mind2web``, ...). Both are kept
  verbatim and ``notes`` carries ``hal_benchmark=<split>``; HAL's own ``verified`` flag is
  recorded too, since HAL re-runs what it publishes.
* an entry with no score (tau-bench's "??" cells, OSWorld/Terminal-Bench blanks) is dropped,
  not written with an empty score: ``validate.py`` requires a numeric score.
* a SWE-bench submission with several ``model_ids`` ("Multiple") gets an empty ``model`` by
  default and the ids in ``notes`` - the score belongs to the ensemble, not to
  ``model_ids[0]``. ``--multi-model first`` restores the naive behaviour.
* ``cost_usd`` is filled from the board's own per-run cost (HAL ``cost_usd``, Terminal-Bench
  ``total_cost_usd``, tau2-bench ``cost``) and the key is named in ``notes``. SWE-bench's
  ``instance_cost`` is a *per-instance* figure in different units, so it goes to ``notes`` only.
* no board reports token counts, so ``tokens`` is always empty.

Usage
-----
    python scripts/leaderboards_to_results.py
    python scripts/leaderboards_to_results.py --skip-boards GAIA --out data/results_boards.csv
    python scripts/leaderboards_to_results.py --boards SWE-bench,OSWorld --append-to data/results.csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from system_registry import key_of, keys_match, norm_name, repo_key, split_version

ROOT = Path(__file__).resolve().parents[1]
LEADERBOARDS = ROOT / "data" / "raw" / "leaderboards.jsonl"
SYSTEMS = ROOT / "data" / "systems.json"
CANDIDATES = ROOT / "data" / "systems_candidates.csv"
DEFAULT_OUT = ROOT / "data" / "results_leaderboards.csv"

RESULT_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd",
                  "tokens", "date", "source_url", "comparable_key", "notes"]

# Public landing page of each board, used when neither the entry nor the harvest record has a url.
BOARD_URL = {
    "GAIA": "https://huggingface.co/spaces/gaia-benchmark/leaderboard",
    "SWE-bench": "https://www.swebench.com/",
    "OSWorld": "https://os-world.github.io/",
    "WebArena": "https://docs.google.com/spreadsheets/d/"
                "1M801lEpBbKSNwP-vDBkC_pF7LdyGU1f_ufZb_NWNBZQ",
    "Terminal-Bench": "https://www.tbench.ai/leaderboard",
    "HAL": "https://hal.cs.princeton.edu",
    "tau-bench": "https://github.com/sierra-research/tau-bench",
    "tau2-bench": "https://github.com/sierra-research/tau2-bench",
}

# Boards whose submission names are free text with no verification: exact-key attribution only.
UNVERIFIED_BOARDS = {"GAIA"}
GAIA_NOTE = "unverified self-reported public submission (open GAIA submission log, no verification)"

# Per-run cost keys, in the order they are trusted. Not SWE-bench `instance_cost` (per instance).
COST_KEYS = ("cost_usd", "total_cost_usd", "cost")

MIN_KEY_EXACT = 3      # shorter keys carry no information ("s", "v2")
MIN_KEY_FUZZY = 6      # fuzzy matching below this is noise; keys_match already demands exact <= 4
MIN_KEY_UNVERIFIED = 4  # a free-text submission title needs a bit more before it may attribute
FUZZY_THRESHOLD = 96   # the registry groups at 92; board free text needs more (see docstring)
MAX_GROUP_NAMES = 6    # a census group pooling more names than this cannot be pinned to an entry
MIN_TOKEN = 4          # shorter tokens are too generic to corroborate an org or a repository
GENERIC_ORG_TOKENS = {"labs", "research", "team", "technologies", "technology", "group", "inc",
                      "corp", "company", "university", "institute", "software", "systems", "code",
                      "codes", "agent", "agents", "open", "cloud", "data", "intelligence",
                      "github", "gitlab", "huggingface", "bitbucket", "codeberg", "main", "tree",
                      "blob", "results", "leaderboard", "submissions"}

# Names that are placeholders, baselines or category labels rather than systems.
STOP_KEYS = {
    # "agents" is deliberately absent: key_of("Agent S") is "agents", and that name is better
    # refused by the over-merged-group veto, which says so in the note.
    "agent", "agentic", "anonymous", "baseline", "default", "demo", "final", "human",
    "llm", "misc", "model", "multiple", "na", "none", "other", "query", "rag", "ragbaseline",
    "reference", "referenceagent", "submission", "system", "tbd", "test", "todo", "tool",
    "toolcalling", "tools", "undisclosed", "unknown", "untitled", "zeroshot",
}
# Placeholder submission names, which the open boards are full of ("test-agent", "my agent",
# "final run"). A registry system called TestAgent exists, so these have to be refused by shape.
STOP_RE = re.compile(
    r"^(test|tests|demo|tmp|temp|trial|debug|dummy|sample|example|foo|bar|baz|my|our|new|old|"
    r"final|first|second|last|best|baseline|submission|sub|run|try|attempt|copy|draft|todo|xxx)"
    r"[\s_-]?(agent|agents|bot|run|test|sub|submission|v\d+)?$")

# Model families. Used only to recognise a name that is *entirely* a model (so it cannot be a
# harness), never to reject a name that merely starts with a family ("Nemotron-CORTEXA").
MODEL_FAMILY_RE = re.compile(
    r"^(gpt|chatgpt|o[1-9]|claude|sonnet|opus|haiku|gemini|gemma|qwen|qwq|llama|codellama|"
    r"deepseek|kimi|glm|grok|mistral|mixtral|magistral|doubao|seed|ernie|yi|internlm|internvl|"
    r"phi|minimax|hunyuan|nemotron|step|vicuna|palm|command|cohere|nova|jamba|dbrx|olmo|"
    r"granite|llava|idefics|blip|computeruse|computerusepreview|operator|xairealtime|gptrealtime|"
    r"gptlive|gptoss|multiple)$",
    re.IGNORECASE,
)
# Tokens that only ever qualify a model (size, tier, decoding, date).
MODEL_QUALIFIERS = {
    "air", "base", "chat", "coder", "exp", "fast", "flash", "high", "instruct", "it", "latest",
    "lite", "live", "low", "max", "medium", "mini", "nano", "omni", "plus", "preview", "pro",
    "realtime", "reasoning", "thinking", "think", "turbo", "vision", "vl", "voice", "v",
    "sonnet", "opus", "haiku", "global", "legacy", "maverick", "scout", "nonthinking",
}
SIZE_RE = re.compile(r"^\d+(\.\d+)?[bkm]?$", re.IGNORECASE)
DATE_TOKEN_RE = re.compile(r"^(20\d{2}|\d{4}|\d{6}|\d{8})$")

# Org / vendor prefixes seen on the boards. Stripped only as an extra candidate, after the full
# name has failed to match.
ORG_PREFIXES = [
    "abanteai", "aigcode", "alibaba", "amazon", "askui", "atlassian", "bytedance", "codefuse",
    "codestory", "composio", "distyl", "emergent", "epam", "factory", "gbox", "globant", "google",
    "hf", "huawei", "ibm", "ibm research", "intelligence-indeed", "jetbrains", "kortix", "meta",
    "microsoft", "moonshot", "nebius", "northeastern university", "nvidia", "openai", "opencsg",
    "patched.codes", "pickle", "pine ai", "salesforce", "salesforce ai research", "sierra",
    "simular", "tencent", "uipath", "w&b", "zhipu",
]

# How each board glues harness, model and org together in `raw_name`.
MODEL_JOIN_RE = re.compile(r"\s+(?:w/|w\.|with|using|on|powered by|\+|/|-{2,}|\|)\s+", re.IGNORECASE)
TBENCH_RAW_RE = re.compile(r"^(?P<date>\d{8})_(?P<rest>.+)$")
MD_LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\([^)]*\)")
TRAILING_BRACKET_RE = re.compile(r"\s*\[[^\]]*\]\s*$")
TRAILING_PARENS_RE = re.compile(r"\s*\([^()]*\)\s*$")
PARAM_SIZE_RE = re.compile(r"[-_\s]\d+(\.\d+)?b$", re.IGNORECASE)


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RegName:
    """One name (canonical or variant) of one registry system."""

    system_id: str
    name: str
    key: str
    base_key: str
    major: int | None


def tokens_of(text: str) -> set[str]:
    """Informative lowercase tokens of a name, org or repository path."""
    return {t for t in re.split(r"[^a-z0-9]+", norm_name(text))
            if len(t) >= MIN_TOKEN and t not in GENERIC_ORG_TOKENS and not t.isdigit()}


def repo_tokens(rk: str) -> set[str]:
    """Owner and repository tokens of a repo key, without the forge host."""
    return tokens_of(rk.split("/", 1)[1] if "/" in rk else rk)


@dataclass
class Registry:
    """Names of the coded systems (attributable) and of census-only systems (reportable)."""

    coded_by_key: dict[str, set[str]] = field(default_factory=dict)
    coded_names: list[RegName] = field(default_factory=list)
    census_by_key: dict[str, set[str]] = field(default_factory=dict)
    name_of: dict[str, str] = field(default_factory=dict)
    keys_of_system: dict[str, set[str]] = field(default_factory=dict)
    repo_of: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.name_of)

    def overmerged(self, system_id: str) -> int:
        """Distinct name keys pooled under this id; > MAX_GROUP_NAMES means unusable."""
        return len(self.keys_of_system.get(system_id, ()))

    def identity_tokens(self, system_id: str) -> set[str]:
        """Tokens that identify the system: its canonical name plus its repository path."""
        return (tokens_of(self.name_of.get(system_id, ""))
                | repo_tokens(self.repo_of.get(system_id, "")))


def _reg_name(system_id: str, name: str) -> RegName | None:
    key = key_of(name)
    if not key:
        return None
    base, major = split_version(name)
    return RegName(system_id, name, key, key_of(base) or key, major)


def load_registry(systems_path: Path = SYSTEMS, candidates_path: Path = CANDIDATES) -> Registry:
    """systems.json ids and names, widened with the census `name_variants` of the same id."""
    systems = json.loads(systems_path.read_text(encoding="utf-8"))
    names: dict[str, set[str]] = {}
    reg = Registry()
    for s in systems:
        sid = s.get("id")
        if not sid:
            continue
        reg.name_of[sid] = s.get("name") or sid
        names.setdefault(sid, set()).add(s.get("name") or sid)
        for url in (s.get("urls") or {}).values():
            rk = repo_key(str(url or ""))
            if rk:
                reg.repo_of.setdefault(sid, rk)

    census: dict[str, set[str]] = {}
    if candidates_path.exists():
        csv.field_size_limit(10**8)
        with candidates_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                sid = (row.get("system_id") or "").strip()
                if not sid:
                    continue
                variants = {v.strip() for v in (row.get("name_variants") or "").split(";")}
                variants.add((row.get("name") or "").strip())
                variants = {v for v in variants if v}
                if sid in names:
                    names[sid] |= variants
                    rk = repo_key(row.get("repo_url") or "")
                    if rk:
                        reg.repo_of.setdefault(sid, rk)
                else:
                    census.setdefault(sid, set()).update(variants)

    for sid, variants in names.items():
        for name in variants:
            rn = _reg_name(sid, name)
            if rn is None:
                continue
            reg.coded_by_key.setdefault(rn.key, set()).add(sid)
            reg.coded_names.append(rn)
            reg.keys_of_system.setdefault(sid, set()).add(rn.key)
    for sid, variants in census.items():
        for name in variants:
            key = key_of(name)
            if key:
                reg.census_by_key.setdefault(key, set()).add(sid)
    return reg


# --------------------------------------------------------------------------------------
# Is this string a model rather than a harness?
# --------------------------------------------------------------------------------------


def is_model_string(text: str) -> bool:
    """True when `text` is *entirely* a model name ("gpt-5 high", "Claude 3.7 Sonnet", "Jedi-7B"
    is not - that one is a system in the census). Used to refuse attribution, never to match."""
    n = norm_name(text)
    tokens = [t for t in re.split(r"[^a-z0-9.]+", n) if t]
    if not tokens:
        return False
    if not MODEL_FAMILY_RE.match(tokens[0]):
        return False
    for t in tokens[1:]:
        if t in MODEL_QUALIFIERS or SIZE_RE.match(t) or DATE_TOKEN_RE.match(t):
            continue
        if re.fullmatch(r"\d+(\.\d+)*[a-z]?", t):
            continue
        if MODEL_FAMILY_RE.match(t):
            continue
        return False
    return True


# --------------------------------------------------------------------------------------
# Harness-name candidates
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Cand:
    """A harness-name candidate: the string, where it came from, and the org prefix removed."""

    text: str
    provenance: str
    org: str = ""


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("_", " ")).strip(" -_/|,;:")


def _add(cands: list[Cand], text: str | None, prov: str, org: str = "") -> None:
    text = (text or "").strip()
    if not text or any(text == c.text for c in cands):
        return
    cands.append(Cand(text, prov, org))


def split_model_off(raw: str) -> list[str]:
    """Sides of a "harness + model" / "harness w/ model" / "harness / model" string that are not
    themselves models. Left side first: every board but tau2-bench puts the harness there."""
    parts = [p.strip() for p in MODEL_JOIN_RE.split(raw) if p.strip()]
    if len(parts) < 2:
        return []
    return [p for p in parts if not is_model_string(p)]


def tbench_harness(raw: str, model: str | None) -> str:
    """"20251108_abacusai-desktop_multiple" -> "abacusai-desktop" (date prefix, model suffix)."""
    m = TBENCH_RAW_RE.match(raw.strip())
    if not m:
        return ""
    rest = m.group("rest")
    slug = re.sub(r"[^a-z0-9]+", "-", (model or "").lower()).strip("-")
    if slug:
        for sep in ("_", "-"):
            suffix = sep + slug
            if rest.lower().endswith(suffix):
                return rest[: -len(suffix)].strip("_- ")
    return rest.rsplit("_", 1)[0].strip("_- ") if "_" in rest else rest


def harness_candidates(venue: str, row: dict[str, Any], entry: dict[str, Any]) -> list[Cand]:
    """Ordered candidates to try against the registry, most literal first."""
    raw = (entry.get("raw_name") or "").strip()
    title = (row.get("title") or "").strip()
    model = entry.get("model")
    cands: list[Cand] = []

    if raw:
        if venue == "Terminal-Bench":
            _add(cands, _clean(tbench_harness(raw, model)), "raw_name minus date and model")
        elif "](" in raw:  # tau-bench: "[ReAct](https://...) (gpt-4o)"
            m = MD_LINK_RE.search(raw)
            if m:
                _add(cands, _clean(m.group("text")), "raw_name markdown link text")
        else:
            stripped = TRAILING_BRACKET_RE.sub("", raw).strip()  # tau2-bench submission dir
            _add(cands, stripped, "raw_name")
            for part in split_model_off(stripped):
                _add(cands, part, "raw_name minus model")
            no_parens = TRAILING_PARENS_RE.sub("", stripped).strip()
            _add(cands, no_parens, "raw_name minus parenthetical")

    if title:
        _add(cands, title, "record title")
        for part in split_model_off(title):
            _add(cands, part, "record title minus model")
        no_parens = TRAILING_PARENS_RE.sub("", title).strip()
        _add(cands, no_parens, "record title minus parenthetical")

    # Org prefixes ("AbanteAI MentatBot", "Simular Agent S2") and parameter-count suffixes
    # ("Aguvis-72B") name the same harness; try them once the literal forms have failed.
    orgs = [str(entry.get(k) or "") for k in ("org", "institution", "model_org", "model_organization")]
    prefixes = {norm_name(o) for o in orgs if norm_name(o)} | set(ORG_PREFIXES)
    for cand in tuple(cands):  # snapshot: the loop appends to `cands`
        n = norm_name(cand.text)
        for pfx in prefixes:
            if n.startswith(pfx + " ") and len(n) > len(pfx) + 1:
                _add(cands, n[len(pfx) + 1:].strip(),
                     f"{cand.provenance} minus org prefix {pfx!r}", org=pfx)
        if PARAM_SIZE_RE.search(n):
            _add(cands, PARAM_SIZE_RE.sub("", n), f"{cand.provenance} minus parameter count",
                 org=cand.org)
    return cands


# --------------------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------------------


@dataclass
class Match:
    system_id: str = ""
    method: str = ""
    matched_on: str = ""
    provenance: str = ""
    variant: str = ""
    reason: str = ""
    census_hint: str = ""


def _compatible(a: int | None, b: int | None) -> bool:
    """Major versions compatible: an unversioned name counts as v1 (protocol 4.4)."""
    return (a or 1) == (b or 1)


def _same_numbers(ka: str, kb: str) -> bool:
    """Two keys may only fuzzy-match when their digit groups agree. A digit inside a name is a
    version or a size, never a typo: "tau-bench reference agent" and "tau2-bench reference agent"
    sit at ratio 97.8 and are different benchmarks' agents."""
    return re.findall(r"\d+", ka) == re.findall(r"\d+", kb)


def veto_reason(reg: Registry, sid: str, cand: Cand, variant: str = "",
                threshold: int = FUZZY_THRESHOLD) -> str:
    """Why this otherwise-good match must be refused; empty string when it may stand."""
    pooled = reg.overmerged(sid)
    if pooled > MAX_GROUP_NAMES:
        return (f"census group {sid} pools {pooled} distinct names (over-merged: a hit on it does "
                f"not identify the system that ran {cand.text!r})")

    canonical = reg.name_of.get(sid, "")
    if variant and not keys_match(key_of(variant), key_of(canonical), threshold):
        return (f"{cand.text!r} matches only the census name variant {variant!r} of {sid}, whose "
                f"canonical name is {canonical!r}; a variant that differs from the canonical name "
                "is where the census's own name merges go wrong (\"Agent S2\" sits under "
                "\"Agents 2.0 (agent symbolic learning)\")")

    ident = reg.identity_tokens(sid)
    if cand.org:
        org_tokens = tokens_of(cand.org)
        sys_repo = reg.repo_of.get(sid, "")
        if sys_repo and org_tokens and not (org_tokens & ident):
            return (f"{cand.text!r} matches {sid} only after removing the org prefix "
                    f"{cand.org!r}, and that system's repository is {sys_repo} - a different "
                    "owner, so the org does not corroborate the match")

    return ""


def match_system(reg: Registry, cands: list[Cand], *, unverified: bool = False,
                 threshold: int = FUZZY_THRESHOLD,
                 board_keys: set[str] | None = None) -> Match:
    """First confident candidate wins; an ambiguous or vetoed candidate stops the search."""
    board_keys = board_keys or set()
    min_len = MIN_KEY_UNVERIFIED if unverified else MIN_KEY_EXACT
    tried: list[str] = []
    skipped: list[str] = []
    census_hint = ""
    for cand in cands:
        text, prov = cand.text, cand.provenance
        key = key_of(text)
        if not key or len(key) < min_len:
            continue
        if key in STOP_KEYS or STOP_RE.match(norm_name(text)):
            skipped.append(f"{text!r} is a placeholder or category label")
            continue
        if key in board_keys:  # a submission named after the board is not a system
            skipped.append(f"{text!r} names the board itself")
            continue
        if is_model_string(text):
            tried.append(f"{text!r} reads as a model name")
            continue
        tried.append(repr(text))

        ids = reg.coded_by_key.get(key)
        if ids:
            if len(ids) == 1:
                sid = next(iter(ids))
                veto = veto_reason(reg, sid, cand, text, threshold)
                if veto:
                    return Match(method="vetoed-exact", matched_on=text, provenance=prov,
                                 reason=f"{text!r} matches {sid} but was refused: {veto}",
                                 census_hint=census_hint)
                return Match(sid, "exact-key", text, prov, variant=text, census_hint=census_hint)
            return Match(reason=f"ambiguous: {text!r} matches {len(ids)} systems "
                                f"({', '.join(sorted(ids))})", matched_on=text, provenance=prov,
                         method="ambiguous-exact", census_hint=census_hint)

        if not census_hint:
            cids = reg.census_by_key.get(key)
            if cids:
                census_hint = (f"census-only system {', '.join(sorted(cids))} matches {text!r} "
                               "but is not in systems.json")

        if unverified or len(key) < MIN_KEY_FUZZY:
            continue
        base, major = split_version(text)
        base_key = key_of(base) or key
        hits: dict[str, str] = {}
        for rn in reg.coded_names:
            if not _compatible(major, rn.major):
                continue
            if (_same_numbers(key, rn.key) and keys_match(key, rn.key, threshold)) or (
                    len(base_key) >= MIN_KEY_FUZZY and _same_numbers(base_key, rn.base_key)
                    and keys_match(base_key, rn.base_key, threshold)):
                hits.setdefault(rn.system_id, rn.name)
        if len(hits) == 1:
            sid, name = next(iter(hits.items()))
            veto = veto_reason(reg, sid, cand, name, threshold)
            if veto:
                return Match(method="vetoed-fuzzy", matched_on=text, provenance=prov,
                             reason=f"{text!r} is within {threshold} of {sid} but was refused: "
                                    f"{veto}", census_hint=census_hint)
            return Match(sid, f"fuzzy-{threshold}", text, prov, variant=name,
                         census_hint=census_hint)
        if len(hits) > 1:
            return Match(method="ambiguous-fuzzy", matched_on=text, provenance=prov,
                         reason=f"ambiguous: {text!r} is within {threshold} of "
                                f"{len(hits)} systems ({', '.join(sorted(hits))})",
                         census_hint=census_hint)
    if not tried:
        why = "; ".join(skipped[:2]) or "placeholder or model name only"
        return Match(reason=f"no usable harness name on the entry ({why})", census_hint=census_hint)
    return Match(reason=f"no registry match for {'; '.join(tried[:3] + skipped[:1])}",
                 census_hint=census_hint)


# --------------------------------------------------------------------------------------
# Row building
# --------------------------------------------------------------------------------------

JUNK_MODELS = {"", "multiple", "n/a", "na", "none", "unknown", "-", "--", "—", "?", "??"}


def model_of(venue: str, row: dict[str, Any], entry: dict[str, Any],
             harness_names: list[str] | None = None,
             multi_model: str = "blank") -> tuple[str, str]:
    """(model, note). Never the harness name: `model` is the LLM under the harness. Some boards
    repeat the submission name in their model column (WebArena's "Agent Flan / Agent Flan"), so a
    model string that matches one of the harness-name candidates is dropped, with a note."""
    harness_keys = {key_of(h) for h in (harness_names or []) if key_of(h)}
    ids = [str(m).strip() for m in (entry.get("model_ids") or []) if str(m).strip()]
    if len(ids) == 1:
        return ids[0], "model from model_ids"
    if len(ids) > 1:
        listed = ", ".join(ids)
        if multi_model == "first":
            return ids[0], f"model from model_ids[0]; submission lists {len(ids)}: {listed}"
        return "", f"model left empty: submission lists {len(ids)} models ({listed})"

    board = str(entry.get("model") or "").strip()
    if board.lower() not in JUNK_MODELS:
        if key_of(board) and key_of(board) in harness_keys:
            return "", ("model left empty: the board's model column repeats the submission name "
                        f"({board!r})")
        return board, "model from the board's model column"
    if board.lower() in {"multiple", "n/a", "na", "unknown"} and board:
        return "", f"model left empty: board reports {board!r}"

    raw = (entry.get("raw_name") or "").strip()
    if raw:
        parts = [p.strip() for p in MODEL_JOIN_RE.split(TRAILING_BRACKET_RE.sub("", raw)) if p.strip()]
        for p in parts[1:] or parts:
            if is_model_string(p):
                return p, "model parsed from raw_name"
        m = TRAILING_PARENS_RE.search(raw)
        if m:
            inner = m.group(0).strip().strip("()")
            if inner and is_model_string(inner):
                return inner, "model parsed from raw_name parenthetical"
        if venue == "Terminal-Bench":
            tb = TBENCH_RAW_RE.match(raw)
            if tb:
                harness_slug = tbench_harness(raw, entry.get("model"))
                rest = tb.group("rest")
                if harness_slug and rest.lower().startswith(harness_slug.lower()):
                    tail = rest[len(harness_slug):].strip("_- ")
                    if tail:
                        return tail, "model parsed from raw_name suffix"
    return "", "no model reported by the board"


def source_url_of(row: dict[str, Any], entry: dict[str, Any], venue: str) -> tuple[str, str]:
    if entry.get("url"):
        return str(entry["url"]), "source_url from the entry"
    if row.get("url"):
        return str(row["url"]), "source_url from the harvest record"
    return BOARD_URL.get(venue, ""), "source_url is the board's public page (entry has none)"


def fmt_score(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    try:
        return str(float(str(value).strip().rstrip("%")))
    except ValueError:
        return ""


def cost_of(entry: dict[str, Any]) -> tuple[str, str]:
    for key in COST_KEYS:
        v = entry.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return str(v), f"cost_usd from the board's {key}"
    return "", ""


def extra_notes(venue: str, entry: dict[str, Any]) -> list[str]:
    bits: list[str] = []
    if venue in UNVERIFIED_BOARDS:
        bits.append(GAIA_NOTE)
    if venue == "HAL":
        bits.append(f"hal_benchmark={entry.get('split')} (HAL is a board; its split names the "
                    "underlying benchmark)")
        if entry.get("verified") is not None:
            bits.append(f"hal_verified={str(bool(entry.get('verified'))).lower()}")
    if isinstance(entry.get("instance_cost"), (int, float)):
        bits.append(f"instance_cost={entry['instance_cost']} (per instance, not per run)")
    if entry.get("n_runs"):
        bits.append(f"n_runs={entry['n_runs']}")
    if entry.get("checked") is True:
        bits.append("swebench_checked=true")
    if entry.get("submission_type"):
        bits.append(f"submission_type={entry['submission_type']}")
    if entry.get("result_source"):
        bits.append(f"result_source={entry['result_source']}")
    if entry.get("strategy"):
        bits.append(f"strategy={entry['strategy']}")
    return bits


def build_row(row: dict[str, Any], entry: dict[str, Any], reg: Registry,
              multi_model: str = "blank", threshold: int = FUZZY_THRESHOLD,
              ) -> dict[str, str] | None:
    """One results row, or None when the entry carries no usable score."""
    venue = str(row.get("venue") or "")
    score = fmt_score(entry.get("score"))
    if score == "":
        return None

    cands = harness_candidates(venue, row, entry)
    unverified = venue in UNVERIFIED_BOARDS
    benchmark = str((row.get("extra") or {}).get("benchmark") or venue)
    match = match_system(reg, cands, unverified=unverified, threshold=threshold,
                         board_keys={key_of(venue), key_of(benchmark)} - {""})
    url, url_note = source_url_of(row, entry, venue)
    model, model_note = model_of(venue, row, entry, [c.text for c in cands],
                                 multi_model=multi_model)
    cost, cost_note = cost_of(entry)

    notes = [f"board={venue}"]
    if match.system_id:
        canonical = reg.name_of.get(match.system_id, "")
        notes.append(f"attributed to {match.system_id} ({canonical}) by {match.method} on "
                     f"{match.matched_on!r} [{match.provenance}]")
        if match.reason:
            notes.append(match.reason)
    else:
        notes.append(f"system_id empty: {match.reason}")
    if match.census_hint and not match.system_id:
        notes.append(match.census_hint)
    notes.append(model_note)
    if cost_note:
        notes.append(cost_note)
    notes.append(url_note)
    notes.extend(extra_notes(venue, entry))

    return {
        "system_id": match.system_id,
        "model": model,
        "benchmark": benchmark,
        "split": str(entry.get("split") or ""),
        "metric": str(entry.get("metric") or ""),
        "score": score,
        "cost_usd": cost,
        "tokens": "",
        "date": str(entry.get("date") or row.get("date") or ""),
        "source_url": url,
        "comparable_key": "",
        "notes": "; ".join(n for n in notes if n),
    }


def read_records(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


@dataclass
class Report:
    rows: collections.Counter = field(default_factory=collections.Counter)
    attributed: collections.Counter = field(default_factory=collections.Counter)
    skipped_no_score: collections.Counter = field(default_factory=collections.Counter)
    skipped_board: collections.Counter = field(default_factory=collections.Counter)
    unattributed_names: collections.Counter = field(default_factory=collections.Counter)
    census_hints: collections.Counter = field(default_factory=collections.Counter)
    vetoed: collections.Counter = field(default_factory=collections.Counter)
    systems_seen: set[str] = field(default_factory=set)


def convert(records: list[dict[str, Any]], reg: Registry, *, skip_boards: set[str] | None = None,
            only_boards: set[str] | None = None, multi_model: str = "blank",
            threshold: int = FUZZY_THRESHOLD) -> tuple[list[dict[str, str]], Report]:
    skip = {b.strip().lower() for b in (skip_boards or set()) if b.strip()}
    only = {b.strip().lower() for b in (only_boards or set()) if b.strip()}
    rep = Report()
    rows: list[dict[str, str]] = []
    for rec in records:
        venue = str(rec.get("venue") or "")
        entries = (rec.get("extra") or {}).get("entries") or []
        if venue.lower() in skip or (only and venue.lower() not in only):
            rep.skipped_board[venue] += len(entries)
            continue
        for entry in entries:
            row = build_row(rec, entry, reg, multi_model=multi_model, threshold=threshold)
            if row is None:
                rep.skipped_no_score[venue] += 1
                continue
            rows.append(row)
            rep.rows[venue] += 1
            label = (entry.get("raw_name") or rec.get("title") or "").strip()
            if row["system_id"]:
                rep.attributed[venue] += 1
                rep.systems_seen.add(row["system_id"])
            else:
                if label:
                    rep.unattributed_names[f"{venue}: {label}"] += 1
                hint = re.search(r"census-only system ([^ ]+) matches", row["notes"])
                if hint:
                    rep.census_hints[f"{hint.group(1)} <- {label}"] += 1
                veto = re.search(r"but was refused: (.*?)(?:; model |$)", row["notes"])
                if veto:
                    rep.vetoed[f"{label} :: {veto.group(1)}"] += 1
    return rows, rep


def write_rows(rows: list[dict[str, str]], out: Path, append_to: Path | None) -> Path:
    target = append_to or out
    exists = target.exists() and target.stat().st_size > 0
    mode = "a" if (append_to and exists) else "w"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open(mode, encoding="utf-8", newline="\n") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS, extrasaction="raise",
                                lineterminator="\n")
        if mode == "w":
            writer.writeheader()
        writer.writerows(rows)
    return target


def print_report(rep: Report, rows: list[dict[str, str]], target: Path, top: int = 25) -> None:
    print(f"wrote {len(rows)} rows to {target}")
    print(f"{'board':16} {'rows':>6} {'attributed':>11} {'empty':>7} {'no score':>9} {'skipped':>8}")
    boards = sorted(set(rep.rows) | set(rep.skipped_no_score) | set(rep.skipped_board))
    for b in boards:
        n, a = rep.rows[b], rep.attributed[b]
        print(f"{b:16} {n:6d} {a:11d} {n - a:7d} {rep.skipped_no_score[b]:9d} "
              f"{rep.skipped_board[b]:8d}")
    total, attributed = sum(rep.rows.values()), sum(rep.attributed.values())
    rate = (100.0 * attributed / total) if total else 0.0
    print(f"{'TOTAL':16} {total:6d} {attributed:11d} {total - attributed:7d} "
          f"{sum(rep.skipped_no_score.values()):9d} {sum(rep.skipped_board.values()):8d}")
    print(f"attribution rate {attributed}/{total} = {rate:.1f}% "
          f"over {len(rep.systems_seen)} distinct systems")
    if rep.unattributed_names:
        print(f"\ntop {top} unattributed names (a mapping here may be worth adding):")
        for name, n in rep.unattributed_names.most_common(top):
            print(f"  {n:5d}  {name}")
    if rep.census_hints:
        print(f"\nnames matching a census system that is not in systems.json ({len(rep.census_hints)}):")
        for name, n in rep.census_hints.most_common(top):
            print(f"  {n:5d}  {name}")
    if rep.vetoed:
        print(f"\nmatches refused by a veto ({len(rep.vetoed)} distinct):")
        for name, n in rep.vetoed.most_common(top):
            print(f"  {n:5d}  {name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--in", dest="infile", type=Path, default=LEADERBOARDS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="write rows here (default data/results_leaderboards.csv)")
    ap.add_argument("--append-to", type=Path, default=None,
                    help="append to this results file instead (e.g. data/results.csv)")
    ap.add_argument("--skip-boards", default="", help="comma-separated venues to drop, e.g. GAIA")
    ap.add_argument("--boards", default="", help="comma-separated venues to keep (all by default)")
    ap.add_argument("--multi-model", choices=["blank", "first"], default="blank",
                    help="model column for a submission listing several model_ids")
    ap.add_argument("--fuzzy-threshold", type=int, default=FUZZY_THRESHOLD,
                    help=f"rapidfuzz ratio needed for a non-exact name match (default "
                         f"{FUZZY_THRESHOLD}; the registry's own grouping threshold is 92)")
    ap.add_argument("--systems", type=Path, default=SYSTEMS)
    ap.add_argument("--candidates", type=Path, default=CANDIDATES)
    ap.add_argument("--top", type=int, default=25, help="how many unattributed names to print")
    args = ap.parse_args(argv)

    # Board names carry CJK and emoji; the Windows console is cp1252.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    reg = load_registry(args.systems, args.candidates)
    records = read_records(args.infile)
    rows, rep = convert(records, reg,
                        skip_boards=set(args.skip_boards.split(",")),
                        only_boards=set(args.boards.split(",")) if args.boards else None,
                        multi_model=args.multi_model, threshold=args.fuzzy_threshold)
    target = write_rows(rows, args.out, args.append_to)
    print(f"registry: {len(reg)} coded systems, {len(reg.coded_names)} names, "
          f"{len(reg.census_by_key)} census-only name keys")
    print_report(rep, rows, target, top=args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
