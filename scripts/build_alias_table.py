#!/usr/bin/env python
"""Comparator-label alias table: paper-corroborated names for the rivals in baseline tables (RQ3).

WHY THIS EXISTS BESIDE ``scripts/analyse_blocks.py``
----------------------------------------------------
``analyse_blocks.py`` turns a paper's own baseline table into a controlled comparison block. It
works, and it is bounded by one number: of 825 comparator arms only 28 could be attributed to a
coded system, which left 7 blocks holding two or more attributed comparator arms - and all 7 came
from ONE paper, so no own-arm-free contrast in that script is replicated across papers. The binding
constraint is NAME RECALL, not block count: 1,184 distinct comparator labels find no registry match,
and many of them are real harnesses written the way a paper writes them ("OH CodeActAgent v1.5",
"M3A", "Navi", "GenericAgent", "CAMEL (MASFactory)"). The existing matcher is right to abstain - a
wrong attribution attaches another system's design vector to a score and is silently fatal to every
contrast - but abstention is not free either.

THE RULE, AND IT IS THE POINT OF THE WHOLE SCRIPT
-------------------------------------------------
A proposed mapping "label L in paper P means coded system S" is accepted ONLY when P ITSELF
corroborates it. Concretely, and in this order:

1. MECHANICAL CORROBORATION IS MANDATORY AND IT IS WHAT ACCEPTS. S's canonical name, one of its
   registry ``name_variants``, its repository name, or its full ``owner/repo`` path must occur in
   P's own full text (``data/fulltext/``, the path resolved exactly as ``scripts/code_system.py``
   resolves it, through ``fulltext_screen.fulltext_path``). A paper that compares against OpenHands
   says "OpenHands" somewhere. If the name does not occur, the mapping is REFUSED however good the
   string match is. The matched span and its character offset into the fetched file are recorded as
   the evidence of every accepted alias, and are re-verified against the file before the row is
   written (``raw[offset:offset + len(span)] == span``), so every row in the output can be checked
   by hand with two lines of Python.
2. A MODEL MAY PROPOSE, NEVER ACCEPT. Proposals come from ``screen_llm.vote_batch_claude_code``
   (or ``code_system.make_api_backend``) in batches of ~30 labels with ``--text-json``, injected
   through ``main(argv, backend=...)`` so the tests need no model and no network. Each item carries
   the label, the source paper's title, the verbatim quote the extractor kept in
   ``data/results_rejects.csv``, the benchmark and metric, and a SHORTLIST of plausible coded
   systems. The model returns the chosen ``system_id`` or null, the exact string in the paper it
   expects to corroborate the choice, and a confidence. Answers are cached by (label, paper), so a
   re-run costs nothing.
3. THE SHORTLIST IS RETRIEVED AT HIGH RECALL, DELIBERATELY. Two sources are unioned: (a) the
   registry's own fuzzy matcher at a LOW threshold (``--shortlist-threshold``, default 78, against
   the registry's own grouping threshold of 92 and the leaderboard importer's 96), and (b) every
   coded system whose name occurs in P at all. (b) is not a convenience: because corroboration is
   mandatory, the systems mentioned in P are the ONLY ones that can ever be accepted, so retrieving
   them is retrieving the whole reachable candidate set. It is also the only route to a mapping no
   string metric can find - nothing in "OH CodeActAgent v1.5" is within 78 of "OpenHands". Recall is
   the retriever's job; precision is the model's job plus the corroboration check.
4. THE EXISTING GUARDS ALL STILL FIRE. This script only ADDS recall; it relaxes nothing.
   ``leaderboards_to_results.veto_reason`` is applied to every proposal (over-merged census group,
   census name variant that diverges from the canonical name, org prefix the repository does not
   corroborate), and so are that script's version-compatibility rule
   (``_compatible``, an unversioned name counts as v1) and its digit-agreement rule
   (``_same_numbers``, applied as ``match_system`` applies it: on the full keys OR on the
   version-stripped base keys). A label the base ``analyse_blocks.Attributor`` already refused as an
   ABLATION of the reporting paper's own system is never proposed, and neither is one it refused by
   a veto or as ambiguous: those are the guards, and going around them is not added recall.
   A proposal naming the REPORTING paper's own coded system is refused too - the extractor already
   judged that row ``not_own_system``, and overriding that judgement would be relaxing its guard.
5. A BARE MODEL NAME IS NEVER A HARNESS. ``is_bare_model`` extends
   ``leaderboards_to_results.is_model_string`` in the two places it misses a name a paper's baseline
   table actually writes: a family glued to its version in one token ("Gemma3-4B", "Qwen2.5-7B") and
   a "v"-prefixed version token ("DeepSeek-v3"). Together with the generic baseline-table labels
   already in ``analyse_blocks.EXTRA_STOP_KEYS`` and ``leaderboards_to_results.STOP_KEYS`` /
   ``STOP_RE``, such a label is never proposed and its row stays an ANONYMOUS comparator: it is a
   real arm, and it does establish how hard the protocol was, but it is not a harness in the census.

WHY A GENERIC NAME MAY NOT CORROBORATE
--------------------------------------
Document frequency of every registry name was measured across all 464 papers that contribute a
comparator row (``--report-mention-df`` prints the same distribution over the papers a given run
actually scans, which is the subset holding a proposable label - 262 in the run this list came from). The head of that distribution is not citations, it is English:
"agents" occurs in 94.8% of the papers, "benchmarks" in 73.9%, "core" 68.1%, "multi-agent" 52.8%,
"leads" 48.5%, "index" 32.8%, "continue" 29.7%. A bare hit on such a name is no evidence that the
paper cites that system, so ``GENERIC_NAME_KEYS`` - curated from the head of that measured
distribution - may not corroborate by itself. Those systems remain reachable through their
repository path, which is never ambiguous. "ReAct" (42.9%) is deliberately kept: in this literature
the token names the agent.

WHAT IS NOT CLAIMED
-------------------
An accepted alias says "this paper's baseline table names this coded system". It does not say the
paper ran the version HARNESS-DB codes: scaffold drift (``docs/benchmark_caveats.md`` sec. 5) is
untouched by this script, and the version-compatibility guard only stops a MAJOR-version crossing.
The alias table is an input to an associational analysis and carries every caveat
``analyse_blocks.py`` prints.

OUTPUTS
-------
``data/comparator_aliases.csv``          one row per ACCEPTED alias: label, system_id,
                                         paper_record_id, corroborating_string, char_offset,
                                         match_method, model_confidence, accepted_by (always
                                         ``mechanical_corroboration``).
``data/comparator_aliases_refused.csv``  one row per REFUSED candidate mapping, with its reason -
                                         including the labels that were never proposed (model name,
                                         generic label, existing guard), so recall can be audited
                                         and the refusals reviewed by hand.
``data/comparator_aliases_cache.json``   the model's answers, keyed by (label, paper).
``data/analysis/comparator_mentions.json``  the paper-mention index (rebuilt when the registry's
                                         name set changes).
Nothing is written under ``data/coded/``, ``data/screening/`` or ``data/fulltext/``.

CONSUMING THE TABLE FROM analyse_blocks.py
------------------------------------------
``analyse_blocks.py`` is NOT edited by this script. ``--rerun-blocks`` loads its source, applies the
ONE-LINE change below in memory, and re-runs the block construction with the alias table applied, so
the change is verified before anyone makes it. In ``build_arm_table``, replace

    att = attributor.attribute(label, note)

with

    att = attributor.attribute(label, note, record_id=str(rec.get("record_id") or "")) if getattr(attributor, "uses_record_id", False) else attributor.attribute(label, note)

That is backward compatible: the stock ``Attributor`` does not set ``uses_record_id``, so it is
called exactly as now; ``build_alias_table.AliasAttributor`` does, and receives the paper.

Run: python scripts/build_alias_table.py --dry-run          (retrieval and guards only, no model)
     python scripts/build_alias_table.py                    (propose with Claude Code, then accept)
     python scripts/build_alias_table.py --backend api
     python scripts/build_alias_table.py --rerun-blocks      (alias table -> new block counts)
"""
from __future__ import annotations

import argparse
import collections
import csv
import importlib.util
import json
import logging
import re
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The matcher, its proven guards and the block builder, imported and never re-implemented: a private
# copy of a matcher is how two scripts in one repository come to disagree about what a name means.
import analyse_blocks as AB
import fulltext_screen as fs
import leaderboards_to_results as LB
import screen_llm
from system_registry import key_of, keys_match, norm_name, split_version

FULLTEXT_DIR = ROOT / "data" / "fulltext"
SYSTEMS = ROOT / "data" / "systems.json"
CANDIDATES = ROOT / "data" / "systems_candidates.csv"
REJECTS = ROOT / "data" / "results_rejects.csv"
BLOCKS_SCRIPT = ROOT / "scripts" / "analyse_blocks.py"

ALIASES_OUT = ROOT / "data" / "comparator_aliases.csv"
REFUSED_OUT = ROOT / "data" / "comparator_aliases_refused.csv"
CACHE_PATH = ROOT / "data" / "comparator_aliases_cache.json"
MENTION_CACHE = ROOT / "data" / "analysis" / "comparator_mentions.json"

ALIAS_COLUMNS = ["label", "system_id", "paper_record_id", "corroborating_string", "char_offset",
                 "match_method", "model_confidence", "accepted_by"]
REFUSED_COLUMNS = ["label", "system_id", "paper_record_id", "reason", "detail",
                   "corroborating_string", "char_offset", "match_method", "model_confidence",
                   "shortlist"]

ACCEPTED_BY = "mechanical_corroboration"
PROMPT_VERSION = "alias-v1-2026-09-24"

SHORTLIST_THRESHOLD = 78   # LOW on purpose: the registry groups at 92, the board importer needs 96
MAX_SHORTLIST = 24         # the model reads one shortlist per paper; beyond this it is noise
BATCH_SIZE = 30
MIN_CONFIDENCE = 0.6
MIN_LABEL_KEY = 3          # mirrors LB.MIN_KEY_EXACT: shorter carries no information ("IS", "RC")
MIN_MENTION_KEY = 4        # a 3-character token is not a citation

DEFAULT_MODEL = "opus"
DEFAULT_EFFORT = "low"

# --------------------------------------------------------------------------------------------
# a bare model name is never a harness
# --------------------------------------------------------------------------------------------
# ``LB.is_model_string`` anchors the family token exactly (``^(gpt|...|gemma|...)$``), which is right
# for a leaderboard's ``raw_name`` and wrong for a paper's baseline table: the table writes
# "Gemma3-4B" and "Qwen2.5-7B-Instruct" with the version fused to the family, and "DeepSeek-v3" with
# a "v". Both are bare models. This extends that function; it never replaces it, and it is only ever
# used to REFUSE, never to match.
_FAMILY = (r"(?:gpt|chatgpt|claude|sonnet|opus|haiku|gemini|gemma|qwen|qwq|llama|codellama|"
           r"deepseek|kimi|glm|grok|mistral|mixtral|magistral|doubao|ernie|yi|internlm|internvl|"
           r"phi|minimax|hunyuan|nemotron|vicuna|palm|command|cohere|nova|jamba|dbrx|olmo|granite|"
           r"llava|idefics|gptoss|gptrealtime|o[1-9])")
_FAMILY_TOKEN_RE = re.compile(rf"^{_FAMILY}[-_.]?\d*(?:\.\d+)*$")
_EXTRA_QUALIFIERS = frozenset({"chat", "base", "instruct", "it", "thinking", "nonthinking",
                               "reasoning", "think", "distill", "distilled", "chatmodel", "oss",
                               "large", "small", "tiny", "xl", "xxl", "huge", "ultra", "coder",
                               "codestral", "math", "moe", "a3b", "a22b"})
# A version or release token: "3.1", "v3", "r1", "k2", "20b". A single letter with digits is how
# every vendor writes a model release ("DeepSeek-R1", "Kimi-K2", "GLM-4.6"), never a harness name.
_VERSION_TOKEN_RE = re.compile(r"^(?:v|r|k|e|b|s|m)?\d+(?:\.\d+)*[a-z]?$")


def is_bare_model(label: str) -> bool:
    """True when the label is ENTIRELY a model name or family, so it can never name a harness."""
    if LB.is_model_string(label):
        return True
    tokens = [t for t in re.split(r"[^a-z0-9.]+", norm_name(label)) if t]
    if not tokens or not _FAMILY_TOKEN_RE.match(tokens[0]):
        return False
    for tok in tokens[1:]:
        if tok in LB.MODEL_QUALIFIERS or tok in _EXTRA_QUALIFIERS:
            continue
        if LB.SIZE_RE.match(tok) or LB.DATE_TOKEN_RE.match(tok) or _VERSION_TOKEN_RE.match(tok):
            continue
        if _FAMILY_TOKEN_RE.match(tok):
            continue
        return False
    return True


# Generic baseline-table labels. Both sets are imported rather than copied: EXTRA_STOP_KEYS is
# ``analyse_blocks``' own list of baseline-table category words, STOP_KEYS / STOP_RE the board
# importer's placeholder list.
GENERIC_LABEL_KEYS = frozenset(AB.EXTRA_STOP_KEYS | LB.STOP_KEYS)

# Registry names whose occurrence in a paper proves nothing, because the name is an ordinary word of
# this literature. Curated from the measured document frequency over all 464 comparator papers
# (``--report-mention-df``); the share each one reached is in the comment. Such a system stays
# reachable through its repository path, which is never ambiguous. "react" (42.9%) is deliberately
# absent: in this literature the token names the agent.
GENERIC_NAME_KEYS = frozenset({
    "agent", "agents", "agentframework", "agentic", "aiagent", "llmagent", "llmagents",  # 94.8-10.3%
    "benchmark", "benchmarks",        # 73.9%
    "core",                           # 68.1%
    "multiagent", "singleagent",      # 52.8%
    "leads",                          # 48.5%
    "exact",                          # 36.2%
    "index",                          # 32.8%
    "simply",                         # 30.0%
    "continue",                       # 29.7%
    "automate", "automated",          # 23.9%
    "stop",                           # 20.5%
    "terminal",                       # 19.2%
    "inspect",                        # 19.0%
    "harness",                        # 18.3%
    "safe",                           # 17.2%
    "atomic",                         # 14.0%
    "coder",                          # 12.3%
    "magnitude",                      # 12.3%
    "ical",                           # 11.6%
    "audit",                          # 11.2%
    "orchestrator",                   # 10.3%
    "deepresearch",                   # 8.8%
    "thread",                         # 6.0%
    "craft",                          # 6.2%
    "sage", "sagent", "eigen", "halo", "advance", "pipeline", "planner", "router", "memory",
    "prompt", "prompts", "search", "select", "verify", "reflect", "summary", "report", "trace",
})


def stoplist_reason(label: str) -> str:
    """Why this label may never be proposed as a harness name; "" when it may."""
    if is_bare_model(label):
        return "stoplist_model_name"
    key = key_of(label)
    if not key:
        return "stoplist_no_name"
    if key in GENERIC_LABEL_KEYS:
        return "stoplist_generic_label"
    if LB.STOP_RE.match(norm_name(label)):
        return "stoplist_placeholder"
    if len(key) < MIN_LABEL_KEY:
        return "stoplist_key_too_short"
    return ""


# --------------------------------------------------------------------------------------------
# the paper-mention index: the mechanical corroboration, and the retrieval
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Mention:
    """One occurrence, in one paper, of one name of one coded system."""

    system_id: str
    name: str
    kind: str        # canonical | variant | repo_name | repo_path
    span: str        # the exact text matched in the paper
    offset: int      # 0-based character offset into the fetched file, header included


_SEP = r"[\s\-_.‐-―/]*"


def _mention_pattern(name: str) -> str:
    """A separator-tolerant pattern for one name: "SWE-agent" also matches "SWE agent", "SWEagent"."""
    tokens = [t for t in re.split(r"[^a-z0-9]+", norm_name(name)) if t]
    return _SEP.join(re.escape(t) for t in tokens) if tokens else ""


@dataclass
class MentionIndex:
    """Which coded systems each paper names, with the span and offset that prove it.

    Built once from the registry, then applied to each paper's fetched full text. The index is both
    halves of the design: it is the mechanical corroboration that ACCEPTS an alias, and - because
    corroboration is mandatory - it is also the complete set of systems a paper could ever be said
    to compare against, hence the retrieval shortlist.
    """

    registry: Any
    root: Path = FULLTEXT_DIR
    by_key: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)
    regex: Any = None
    papers: dict[str, dict[str, Mention]] = field(default_factory=dict)
    missing: set[str] = field(default_factory=set)
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.by_key:
            self.build_patterns()

    # -- construction ------------------------------------------------------------------------
    def _add(self, system_id: str, name: str, kind: str) -> None:
        key = key_of(name) if kind != "repo_path" else re.sub(r"[^a-z0-9/]+", "", name.lower())
        if kind == "repo_path":
            if name.count("/") != 1 or len(key) < MIN_MENTION_KEY:
                return
        else:
            if len(key) < MIN_MENTION_KEY or key in LB.STOP_KEYS or is_bare_model(name):
                return
        self.by_key.setdefault(key, []).append((system_id, name, kind))

    def build_patterns(self) -> None:
        reg = self.registry
        canonical = {sid: reg.name_of.get(sid, "") for sid in reg.name_of}
        for rn in reg.coded_names:
            kind = "canonical" if key_of(rn.name) == key_of(canonical.get(rn.system_id, "")) \
                else "variant"
            self._add(rn.system_id, rn.name, kind)
        for sid, rk in reg.repo_of.items():
            parts = rk.split("/")
            if len(parts) >= 3:
                self._add(sid, parts[2], "repo_name")
                self._add(sid, f"{parts[1]}/{parts[2]}", "repo_path")
        alts = []
        for entries in self.by_key.values():
            sample = max((e[1] for e in entries), key=len)
            pat = _mention_pattern(sample)
            if pat:
                alts.append(pat)
        alts.sort(key=len, reverse=True)  # longest alternative first: prefer the most specific name
        self.regex = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(alts) + r")(?![A-Za-z0-9])",
                                re.IGNORECASE) if alts else None
        self.fingerprint = f"{PROMPT_VERSION}|{len(self.by_key)}|{len(alts)}"

    # -- scanning ----------------------------------------------------------------------------
    def scan(self, record_id: str) -> dict[str, Mention]:
        """system_id -> its FIRST, most specific mention in this paper. {} when there is no text."""
        if record_id in self.papers:
            return self.papers[record_id]
        path = fs.fulltext_path(record_id, self.root)
        if not path.exists() or self.regex is None:
            self.missing.add(record_id)
            self.papers[record_id] = {}
            return {}
        raw = path.read_text(encoding="utf-8", errors="replace")
        found: dict[str, Mention] = {}
        rank = {"repo_path": 0, "canonical": 1, "variant": 2, "repo_name": 3}
        for m in self.regex.finditer(raw):
            span = m.group(0)
            key = key_of(span)
            entries = self.by_key.get(key) or self.by_key.get(
                re.sub(r"[^a-z0-9/]+", "", span.lower()), ())
            for sid, name, kind in entries:
                prior = found.get(sid)
                if prior is None or rank[kind] < rank[prior.kind]:
                    found[sid] = Mention(sid, name, kind, span, m.start())
        self.papers[record_id] = found
        return found

    def corroboration(self, record_id: str, system_id: str) -> Mention | None:
        """The mention that may corroborate system_id in this paper, or None.

        A name in ``GENERIC_NAME_KEYS`` may not corroborate on its own - its occurrence is English,
        not a citation - so such a system is reachable only through its repository path.
        """
        mention = self.scan(record_id).get(system_id)
        if mention is None:
            return None
        if mention.kind != "repo_path" and key_of(mention.name) in GENERIC_NAME_KEYS:
            return None
        return mention

    def verify(self, record_id: str, mention: Mention) -> bool:
        """Re-read the file and check the recorded span really sits at the recorded offset."""
        path = fs.fulltext_path(record_id, self.root)
        if not path.exists():
            return False
        raw = path.read_text(encoding="utf-8", errors="replace")
        return raw[mention.offset:mention.offset + len(mention.span)] == mention.span

    def find_model_string(self, record_id: str, system_id: str, text: str) -> Mention | None:
        """The model's expected corroborating string, IF it occurs in the paper AND names S.

        This is a cross-check, not the gate: the gate is `corroboration`, which asks the registry's
        own names. A model string that occurs but does not name S is ignored (and counted); one that
        does not occur at all is counted too, because a model quoting text that is not in the paper
        is worth knowing about even when the mechanical check accepts anyway.
        """
        text = (text or "").strip()
        if not text or len(key_of(text)) < MIN_MENTION_KEY:
            return None
        names = {key_of(n) for _, n, _ in
                 (e for entries in self.by_key.values() for e in entries if e[0] == system_id)}
        if not any(keys_match(key_of(text), nk, LB.FUZZY_THRESHOLD) for nk in names):
            return None
        pat = _mention_pattern(text)
        if not pat:
            return None
        path = fs.fulltext_path(record_id, self.root)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?<![A-Za-z0-9])(?:" + pat + r")(?![A-Za-z0-9])", raw, re.IGNORECASE)
        if not m:
            return None
        kind = next((k for sid, n, k in
                     (e for entries in self.by_key.values() for e in entries)
                     if sid == system_id and keys_match(key_of(n), key_of(text),
                                                        LB.FUZZY_THRESHOLD)), "variant")
        if kind != "repo_path" and key_of(text) in GENERIC_NAME_KEYS:
            return None
        return Mention(system_id, text, kind, m.group(0), m.start())

    # -- cache -------------------------------------------------------------------------------
    def load_cache(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0
        if blob.get("fingerprint") != self.fingerprint:
            return 0
        for rid, entries in (blob.get("papers") or {}).items():
            self.papers[rid] = {sid: Mention(sid, m["name"], m["kind"], m["span"], int(m["offset"]))
                                for sid, m in entries.items()}
        return len(self.papers)

    def save_cache(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        blob = {
            "fingerprint": self.fingerprint,
            "papers": {rid: {sid: {"name": m.name, "kind": m.kind, "span": m.span,
                                   "offset": m.offset}
                             for sid, m in entries.items()}
                       for rid, entries in self.papers.items()},
        }
        path.write_text(json.dumps(blob, indent=0, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------------------------
# retrieval: the shortlist the model chooses from
# --------------------------------------------------------------------------------------------
# A paper's baseline table writes "harness/model" and "harness/model/tool" with no spaces around the
# separator ("OpenCode/Qwen3-30B/Spoon", "GeminiCLI/Gemini-3.1-Pro"), which
# `leaderboards_to_results.MODEL_JOIN_RE` does not split because it requires whitespace - that regex
# was written for leaderboard `raw_name`s, where the separator is spaced. Splitting here is a PARSING
# extension, not a relaxed guard: every part still has to pass the version, digit, canonical-name and
# org vetoes, and the part that passed is recorded in `match_method`.
_TIGHT_JOIN_RE = re.compile(r"\s*(?:/|\||,|\+|w/|-{2,})\s*|\s+(?:with|using|on|powered by)\s+",
                            re.IGNORECASE)


def guard_parts(label: str) -> list[LB.Cand]:
    """Substrings of the label that may name the harness, most literal first.

    `analyse_blocks.candidate_names` supplies the proven reductions (trailing bracket, trailing
    parenthetical, leftmost non-model side of a spaced "harness + model" split, org prefix, parameter
    count); this adds the unspaced separators a paper table uses.

    ONLY THE LEFTMOST non-model part is added, which is `analyse_blocks.candidate_names`' own rule
    and is not negotiable: in a paper's baseline table the row names a harness first and its backbone
    second, so "MLR-Agent o4-mini-high + Codex" is MLR-Agent's row and not Codex's. Letting the
    right-hand side attribute turns such a row into a score for the wrong system, which is the exact
    failure that rule exists to prevent - so "OpenCode/Qwen3-30B/Spoon" offers "OpenCode" and
    nothing else.
    """
    cands = list(AB.candidate_names(label))
    for part in (p.strip(" -_/|,;:") for p in _TIGHT_JOIN_RE.split(label)):
        if not part or is_bare_model(part):
            continue
        if key_of(part) in AB.EXTRA_STOP_KEYS or len(key_of(part)) < MIN_LABEL_KEY:
            continue
        LB._add(cands, part, "label minus unspaced model/tool part", org=_org_of(part))
        break  # leftmost non-model part only
    return cands


def _org_of(label: str) -> str:
    """The org prefix the label carries, for the org-corroboration veto; "" when it carries none."""
    text = norm_name(label)
    for prefix in LB.ORG_PREFIXES:
        if text.startswith(prefix + " ") and len(text) > len(prefix) + 1:
            return prefix
    return ""


def fuzzy_shortlist(registry: Any, label: str, threshold: int = SHORTLIST_THRESHOLD) -> dict[str, str]:
    """Coded systems whose name is within `threshold` of the label - the registry's own matcher,
    run LOW so recall is high. system_id -> the name that came closest."""
    key = key_of(label)
    base, _ = split_version(label)
    base_key = key_of(base) or key
    hits: dict[str, str] = {}
    if len(key) < MIN_MENTION_KEY:
        return hits
    for rn in registry.coded_names:
        if keys_match(key, rn.key, threshold) or (
                len(base_key) >= MIN_MENTION_KEY and keys_match(base_key, rn.base_key, threshold)):
            hits.setdefault(rn.system_id, rn.name)
    return hits


def _similarity(label: str, name: str) -> int:
    """A cheap rank for the shortlist only. Never used to accept anything."""
    from rapidfuzz import fuzz
    a, b = key_of(label), key_of(name)
    if not a or not b:
        return 0
    return max(int(fuzz.ratio(a, b)), int(fuzz.partial_ratio(a, b)),
               int(fuzz.token_set_ratio(norm_name(label), norm_name(name))))


@dataclass(frozen=True)
class ShortlistEntry:
    system_id: str
    name: str
    source: str        # mentioned_in_paper | fuzzy_low | both
    mention: str       # the span found in the paper, "" when the system is not mentioned
    score: int


def shortlist_for(label: str, record_id: str, registry: Any, index: MentionIndex,
                  threshold: int = SHORTLIST_THRESHOLD,
                  limit: int = MAX_SHORTLIST) -> list[ShortlistEntry]:
    """The candidates offered to the model: mentioned-in-paper UNION low-threshold fuzzy.

    Ranked by string similarity to the label, but a system MENTIONED in the paper is never dropped
    for a merely similar one that is not: only a mentioned system can survive corroboration, and the
    mapping the string metric cannot see ("OH CodeActAgent v1.5" -> OpenHands) lives there.
    """
    mentioned = {sid: m for sid, m in index.scan(record_id).items()
                 if index.corroboration(record_id, sid) is not None}
    fuzzy = fuzzy_shortlist(registry, label, threshold)
    entries: list[ShortlistEntry] = []
    for sid, mention in mentioned.items():
        name = registry.name_of.get(sid, mention.name)
        source = "both" if sid in fuzzy else "mentioned_in_paper"
        entries.append(ShortlistEntry(sid, name, source, mention.span,
                                      _similarity(label, name) if name else 0))
    for sid, name in fuzzy.items():
        if sid in mentioned:
            continue
        entries.append(ShortlistEntry(sid, registry.name_of.get(sid, name), "fuzzy_low", "",
                                      _similarity(label, name)))
    entries.sort(key=lambda e: (e.source == "fuzzy_low", -e.score, e.system_id))
    return entries[:limit]


# --------------------------------------------------------------------------------------------
# the candidates: which (label, paper) pairs may be proposed at all
# --------------------------------------------------------------------------------------------
@dataclass
class Candidate:
    """One (label, paper) pair the alias table might name, with the context the model is given."""

    label: str
    record_id: str
    note: str = ""
    title: str = ""
    quote: str = ""
    benchmark: str = ""
    metric: str = ""
    own_system_id: str = ""
    rows: int = 1

    @property
    def item_id(self) -> str:
        return f"{self.record_id}||{self.label}"


@dataclass
class Refusal:
    label: str
    record_id: str
    system_id: str = ""
    reason: str = ""
    detail: str = ""
    corroborating_string: str = ""
    char_offset: str = ""
    match_method: str = ""
    model_confidence: str = ""
    shortlist: str = ""


def paper_titles(index: MentionIndex, record_ids: set[str]) -> dict[str, str]:
    """record_id -> the fetched title in the full-text header (blank when there is no file)."""
    out: dict[str, str] = {}
    for rid in record_ids:
        path = fs.fulltext_path(rid, index.root)
        if not path.exists():
            out[rid] = ""
            continue
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
        header, _ = fs.parse_fulltext(head)
        out[rid] = header.get("fetched_title", "")
    return out


def collect_candidates(comparators: Any, attributor: AB.Attributor
                       ) -> tuple[list[Candidate], list[Refusal], collections.Counter]:
    """Split every comparator row into (proposable candidates, pre-proposal refusals).

    A row already attributed by the base matcher is left alone. A row the base matcher refused as an
    ABLATION, by a VETO or as AMBIGUOUS keeps that refusal: those are the existing guards, and this
    script adds recall without going around them. A bare model name or a generic baseline-table
    label is refused by the stop-list. Everything else becomes one candidate per (label, paper).
    """
    by_pair: dict[tuple[str, str], Candidate] = {}
    refused: dict[tuple[str, str, str], Refusal] = {}
    counts: collections.Counter = collections.Counter()
    for rec in comparators.to_dict(orient="records"):
        label = str(rec.get("reported_system_name") or "")
        note = str(rec.get("note") or "")
        rid = str(rec.get("record_id") or "")
        counts["rows_considered"] += 1
        att = attributor.attribute(label, note)
        if att.attributed:
            counts["rows_already_attributed"] += 1
            continue
        reason, detail = "", ""
        if att.method == "refused-ablation":
            reason, detail = "existing_guard_ablation", att.reason
        elif att.method.startswith("vetoed") or att.method.startswith("ambiguous"):
            reason, detail = "existing_guard_veto", f"{att.method}: {att.reason}"
        elif att.method == "abstain-no-candidate":
            reason, detail = "no_usable_harness_name", att.reason
        else:
            reason = stoplist_reason(label)
            if reason:
                detail = ("a bare model name is a real comparator but it is not a harness in the "
                          "census" if reason == "stoplist_model_name"
                          else "a baseline-table category label, not a system")
        if reason:
            counts[reason] += 1
            refused.setdefault((label, rid, reason), Refusal(label, rid, reason=reason,
                                                             detail=detail))
            continue
        counts["rows_proposable"] += 1
        pair = (label, rid)
        if pair in by_pair:
            by_pair[pair].rows += 1
            continue
        by_pair[pair] = Candidate(
            label=label, record_id=rid, note=note,
            quote=str(rec.get("evidence_quote") or "")[:400],
            benchmark=str(rec.get("benchmark") or ""),
            metric=str(rec.get("metric") or ""),
            own_system_id=str(rec.get("system_id") or ""),
        )
    return list(by_pair.values()), list(refused.values()), counts


# --------------------------------------------------------------------------------------------
# the model: it proposes, it never accepts
# --------------------------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are helping a PRISMA systematic review of LLM agent harnesses decide what the rival names in a
paper's baseline table refer to.

You are given, in batches, comparator labels copied verbatim from papers' comparison tables. For
each one you pick, from a SHORTLIST, the coded system the label names in THAT paper - or null.

RULES

1. You PROPOSE; you do not decide. Every choice you make is afterwards checked mechanically against
   the paper's own full text, and refused if the system's name does not occur there. So there is no
   value in guessing: a guess is either caught and wasted, or - worse - corroborated by accident.
2. Answer null unless you are actually confident. null is the correct answer for:
   - a bare model name ("GPT-4o", "Qwen2.5-7B") - a model is not a harness;
   - a category or configuration label of the reporting paper itself ("Ours", "Full system",
     "w/o memory", "Single agent", "Group", "Solo", "+ retrieval");
   - a prompting technique or algorithm rather than a system ("Chain-of-Thought", "Best-of-N",
     "SFT", "RL Agent"), unless the shortlist holds the named implementation;
   - anything you have not actually heard of.
3. Pick from the shortlist by system_id, exactly as spelled. Never invent an id.
4. Abbreviations and re-implementations are the point of this exercise. "OH CodeActAgent v1.5" is
   OpenHands' CodeAct agent. "ChatDev (MASFactory)" is ChatDev, re-implemented inside the reporting
   paper's own framework - still ChatDev. A shortlist entry marked "mentioned in paper" is a system
   the paper actually names somewhere in its text, which is usually how a baseline arrives.
5. corroborating_string: the exact string you expect to find IN THE PAPER that shows it is that
   system - normally the system's own name as the paper writes it. Copy the shortlist entry's name
   if that is what you mean. Leave it "" when system_id is null.
6. confidence: 0.0-1.0. Use below 0.6 when you are guessing; such answers are discarded.

Return one entry per item, with the item's id in "record_id".
"""

PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "votes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string"},
                    "system_id": {"type": ["string", "null"]},
                    "corroborating_string": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["record_id", "system_id", "corroborating_string", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["votes"],
    "additionalProperties": False,
}


def build_prompt(batch: list[dict[str, Any]]) -> str:
    """The user prompt for one batch, grouped by paper so each shortlist is stated once."""
    by_paper: dict[str, list[dict[str, Any]]] = {}
    for item in batch:
        by_paper.setdefault(item["record_id_paper"], []).append(item)
    out: list[str] = [f"{len(batch)} comparator labels, grouped by the paper they were copied from."]
    for rid, items in by_paper.items():
        out.append("")
        out.append(f"PAPER {rid}" + (f" - {items[0]['title']}" if items[0].get("title") else ""))
        shortlist = items[0]["shortlist"]
        if shortlist:
            out.append("  shortlist of coded systems (system_id | name | retrieval):")
            for e in shortlist:
                mark = {"mentioned_in_paper": "mentioned in paper",
                        "both": "mentioned in paper, and a close name",
                        "fuzzy_low": "close name only, NOT mentioned in this paper"}[e["source"]]
                seen = f' as "{e["mention"]}"' if e["mention"] else ""
                out.append(f"    {e['system_id']} | {e['name']} | {mark}{seen}")
        else:
            out.append("  shortlist: EMPTY - no coded system is retrievable for this paper, so "
                       "every label below must be answered null.")
        for item in items:
            out.append(f"  ITEM id={item['id']}")
            out.append(f"    label      : {item['label']}")
            if item.get("benchmark"):
                out.append(f"    benchmark  : {item['benchmark']} / metric {item.get('metric','')}")
            if item.get("quote"):
                out.append(f"    table quote: {item['quote']}")
            if item.get("note"):
                out.append(f"    extractor note: {item['note']}")
    return "\n".join(out)


def batch_items(candidates: list[Candidate], registry: Any, index: MentionIndex,
                titles: dict[str, str], threshold: int, limit: int) -> list[dict[str, Any]]:
    """One prompt item per candidate, carrying its paper's shortlist."""
    items: list[dict[str, Any]] = []
    for cand in candidates:
        shortlist = shortlist_for(cand.label, cand.record_id, registry, index, threshold, limit)
        items.append({
            "id": cand.item_id,
            "record_id_paper": cand.record_id,
            "title": titles.get(cand.record_id, ""),
            "label": cand.label,
            "note": cand.note,
            "quote": cand.quote,
            "benchmark": cand.benchmark,
            "metric": cand.metric,
            "shortlist": [{"system_id": e.system_id, "name": e.name, "source": e.source,
                           "mention": e.mention} for e in shortlist],
        })
    return items


def chunk_by_paper(items: list[dict[str, Any]], size: int = BATCH_SIZE) -> list[list[dict[str, Any]]]:
    """Batches of about `size` items, keeping one paper's items together where they fit."""
    by_paper: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_paper.setdefault(item["record_id_paper"], []).append(item)
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for group in by_paper.values():
        for start in range(0, len(group), size):
            piece = group[start:start + size]
            if len(current) + len(piece) > size and current:
                batches.append(current)
                current = []
            current.extend(piece)
    if current:
        batches.append(current)
    return batches


@dataclass
class Proposal:
    label: str
    record_id: str
    system_id: str = ""
    corroborating_string: str = ""
    confidence: float = 0.0
    reason: str = ""
    shortlist_ids: tuple[str, ...] = ()
    cached: bool = False


def load_proposal_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return blob.get("proposals") or {}


def save_proposal_cache(path: Path, cache: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"prompt_version": PROMPT_VERSION, "proposals": cache},
                               indent=0, sort_keys=True), encoding="utf-8")


def cache_key(label: str, record_id: str) -> str:
    return f"{record_id}\t{label}"


def propose(items: list[dict[str, Any]], backend: Callable[..., Any], *, exe: str = "claude",
            model: str = DEFAULT_MODEL, effort: str | None = DEFAULT_EFFORT,
            cache: dict[str, dict[str, Any]] | None = None, batch_size: int = BATCH_SIZE,
            log: logging.Logger | None = None, retries: int = 6
            ) -> tuple[list[Proposal], dict[str, Any]]:
    """Ask the model for a proposal per item, reading the (label, paper) cache first.

    The cache is the whole re-run story: a (label, paper) pair whose answer is already on disk is
    never sent again, so a second run makes zero backend calls.
    """
    cache = {} if cache is None else cache
    log = log or logging.getLogger("build_alias_table")
    out: list[Proposal] = []
    pending: list[dict[str, Any]] = []
    shortlists = {i["id"]: tuple(e["system_id"] for e in i["shortlist"]) for i in items}
    by_id = {i["id"]: i for i in items}
    for item in items:
        hit = cache.get(cache_key(item["label"], item["record_id_paper"]))
        if hit is not None:
            out.append(Proposal(item["label"], item["record_id_paper"],
                                str(hit.get("system_id") or ""),
                                str(hit.get("corroborating_string") or ""),
                                float(hit.get("confidence") or 0.0),
                                str(hit.get("reason") or ""),
                                shortlists[item["id"]], cached=True))
        else:
            pending.append(item)
    stats = {"items": len(items), "from_cache": len(out), "sent": len(pending), "calls": 0,
             "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "batches_failed": 0, "model": ""}
    if not pending:
        return out, stats
    with tempfile.TemporaryDirectory(prefix="alias-prompt-") as tmp:
        system_file = Path(tmp) / "system.txt"
        system_file.write_text(SYSTEM_PROMPT, encoding="utf-8")
        for n, batch in enumerate(chunk_by_paper(pending, batch_size), start=1):
            label = f"batch {n} ({len(batch)} labels)"
            try:
                result = screen_llm.with_retries(
                    lambda b=batch: backend(exe, model, system_file, b, effort=effort,
                                            schema=PROPOSAL_SCHEMA, prompt=build_prompt,
                                            text_json=True),
                    log, label, max_attempts=retries)
            except Exception as exc:  # noqa: BLE001 - a dead batch must not kill the run
                stats["batches_failed"] += 1
                log.error("%s failed: %s", label, str(exc)[:300])
                continue
            stats["calls"] += 1
            stats["tokens_in"] += result.tokens_in
            stats["tokens_out"] += result.tokens_out
            stats["cost_usd"] += result.cost_usd
            stats["model"] = result.model
            for item, vote in zip(batch, result.votes, strict=False):
                sid = vote.get("system_id")
                rec = {
                    "system_id": "" if sid in (None, "", "null") else str(sid),
                    "corroborating_string": str(vote.get("corroborating_string") or ""),
                    "confidence": float(vote.get("confidence") or 0.0),
                    "reason": str(vote.get("reason") or "")[:300],
                    "model": result.model,
                    "prompt_version": PROMPT_VERSION,
                }
                cache[cache_key(item["label"], item["record_id_paper"])] = rec
                out.append(Proposal(item["label"], item["record_id_paper"], rec["system_id"],
                                    rec["corroborating_string"], rec["confidence"], rec["reason"],
                                    shortlists[item["id"]]))
            log.info("%s: %d answers, %d in / %d out tokens", label, len(result.votes),
                     result.tokens_in, result.tokens_out)
    _ = by_id  # kept for symmetry with screen_llm's batch protocol
    return out, stats


# --------------------------------------------------------------------------------------------
# acceptance: the corroboration check and the existing vetoes
# --------------------------------------------------------------------------------------------
def version_ok(label: str, name: str) -> tuple[bool, str]:
    """`leaderboards_to_results._compatible` on the label and the matched name."""
    _, a = split_version(label)
    _, b = split_version(name)
    if LB._compatible(a, b):
        return True, ""
    return False, (f"label major version {a or 1} against {name!r} major {b or 1}: a paper naming "
                   "one major version of a harness is not evidence about another")


def digits_ok(label: str, name: str) -> tuple[bool, str]:
    """`leaderboards_to_results._same_numbers`, applied as `match_system` applies it.

    Full keys OR version-stripped base keys: a digit inside a name is a version or a size, never a
    typo, so "OH CodeActAgent v1.5" reaches OpenHands on the base keys (both digit-free) while
    "tau2-bench reference agent" still cannot reach "tau-bench reference agent".
    """
    ka, kb = key_of(label), key_of(name)
    ba, bb = key_of(split_version(label)[0]) or ka, key_of(split_version(name)[0]) or kb
    if LB._same_numbers(ka, kb) or LB._same_numbers(ba, bb):
        return True, ""
    def digits(k: str) -> list[str]:  # for the message only
        return re.findall(r"\d+", k)

    return False, (f"digit groups disagree: {ka!r} carries {digits(ka)} and {kb!r} "
                   f"carries {digits(kb)}; a digit in a name is a version or a size")


@dataclass
class Accepted:
    label: str
    record_id: str
    system_id: str
    corroborating_string: str
    char_offset: int
    match_method: str
    model_confidence: float


def adjudicate(proposal: Proposal, registry: Any, index: MentionIndex, *,
               own_system_id: str = "", threshold: int = LB.FUZZY_THRESHOLD,
               min_confidence: float = MIN_CONFIDENCE
               ) -> tuple[Accepted | None, Refusal | None, str]:
    """One proposal -> accepted alias or refusal. The model never accepts; this function does.

    Returns (accepted, refusal, cross_check) where cross_check names what happened to the model's
    own expected corroborating string: `model_string_confirmed`, `model_string_absent` or
    `model_string_not_the_system`.
    """
    shortlist = ", ".join(proposal.shortlist_ids[:12])
    def refuse(reason: str, detail: str, mention: Mention | None = None,
               method: str = "") -> tuple[None, Refusal, str]:
        return None, Refusal(proposal.label, proposal.record_id, proposal.system_id, reason, detail,
                             mention.span if mention else "",
                             str(mention.offset) if mention else "", method,
                             f"{proposal.confidence:.2f}", shortlist), ""

    if not proposal.system_id:
        return refuse("model_answered_null", proposal.reason or "the model named no system")
    if proposal.system_id not in registry.name_of:
        return refuse("system_id_not_coded",
                      f"{proposal.system_id!r} is not an id in systems.json")
    if proposal.shortlist_ids and proposal.system_id not in proposal.shortlist_ids:
        return refuse("system_id_not_in_shortlist",
                      f"{proposal.system_id!r} was not offered for this paper")
    if proposal.confidence < min_confidence:
        return refuse("low_confidence",
                      f"confidence {proposal.confidence:.2f} < {min_confidence:.2f}")
    if own_system_id and proposal.system_id == own_system_id:
        return refuse("own_system_of_reporting_paper",
                      f"{proposal.system_id!r} is the reporting paper's own coded system, and the "
                      "extractor already judged this row not_own_system; overriding that would "
                      "relax an existing guard, not add recall")

    # -- 1. mechanical corroboration, the step that accepts --------------------------------------
    mention = index.corroboration(proposal.record_id, proposal.system_id)
    cross = "model_string_absent"
    quoted = index.find_model_string(proposal.record_id, proposal.system_id,
                                     proposal.corroborating_string)
    if quoted is not None:
        cross = "model_string_confirmed"
        mention = quoted
    elif proposal.corroborating_string.strip():
        cross = "model_string_not_the_system"
    if mention is None:
        if proposal.record_id in index.missing:
            return refuse("no_fulltext_for_paper",
                          f"no fetched full text for {proposal.record_id}, so the paper cannot "
                          "corroborate anything")
        return refuse("no_corroboration_in_paper",
                      f"no name of {proposal.system_id!r} (canonical name, census name variant, "
                      f"repository name or owner/repo path) occurs in {proposal.record_id}; a paper "
                      "that compares against a system says its name")
    if not index.verify(proposal.record_id, mention):
        return refuse("corroboration_offset_mismatch",
                      f"the recorded span {mention.span!r} is not at offset {mention.offset} of the "
                      "fetched file", mention)

    if is_bare_model(mention.name):
        return refuse("corroborating_name_is_a_model", f"{mention.name!r} reads as a model name",
                      mention)

    # -- 2. the existing guards, unrelaxed ------------------------------------------------------
    # Applied the way `match_system` applies them: over the label's harness-name candidates, most
    # literal first, accepting the first candidate that clears every veto. A candidate that carries
    # a version or a size the corroborated name does not still fails, so "SWE-agent 2.0 + GPT-4o"
    # cannot reach a v1 system through its own shorter prefix.
    label_org = _org_of(proposal.label)
    parts = guard_parts(proposal.label) or [
        LB.Cand(text=proposal.label, provenance="reported_system_name", org=label_org)]
    failures: list[tuple[str, str]] = []
    for cand in parts:
        # The org prefix is taken from the WHOLE label, not from the part, and is carried into every
        # candidate. In `match_system` the org-stripped candidate is only reached after the full name
        # fails to match, so the org veto would never be tried here (corroboration is independent of
        # the string match); applying it to every part is what keeps the guard biting.
        if label_org and not cand.org:
            cand = LB.Cand(cand.text, cand.provenance, label_org)
        veto = LB.veto_reason(registry, proposal.system_id, cand, mention.name, threshold)
        if veto:
            failures.append(("existing_veto", veto))
            continue
        ok, why = version_ok(cand.text, mention.name)
        if not ok:
            failures.append(("version_incompatible", f"{cand.text!r}: {why}"))
            continue
        ok, why = digits_ok(cand.text, mention.name)
        if not ok:
            failures.append(("digits_disagree", f"{cand.text!r}: {why}"))
            continue
        src = "model_string" if cross == "model_string_confirmed" else "mention_index"
        method = f"llm_shortlist|{mention.kind}|{src}|part={cand.text}"
        return Accepted(proposal.label, proposal.record_id, proposal.system_id, mention.span,
                        mention.offset, method, proposal.confidence), None, cross
    reason, detail = failures[0] if failures else (
        "no_harness_name_candidate", f"{proposal.label!r} reduces to no usable harness name")
    return refuse(reason, "; ".join(d for _, d in failures[:3]) or detail, mention)


# --------------------------------------------------------------------------------------------
# the alias table: writing it, reading it, and applying it to analyse_blocks.py
# --------------------------------------------------------------------------------------------
def write_aliases(accepted: list[Accepted], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=ALIAS_COLUMNS)
        w.writeheader()
        for a in sorted(accepted, key=lambda x: (x.record_id, x.label)):
            w.writerow({"label": a.label, "system_id": a.system_id,
                        "paper_record_id": a.record_id,
                        "corroborating_string": a.corroborating_string,
                        "char_offset": a.char_offset, "match_method": a.match_method,
                        "model_confidence": f"{a.model_confidence:.2f}",
                        "accepted_by": ACCEPTED_BY})
    return path


def write_refused(refused: list[Refusal], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REFUSED_COLUMNS)
        w.writeheader()
        for r in sorted(refused, key=lambda x: (x.reason, x.record_id, x.label)):
            w.writerow({"label": r.label, "system_id": r.system_id,
                        "paper_record_id": r.record_id, "reason": r.reason, "detail": r.detail,
                        "corroborating_string": r.corroborating_string,
                        "char_offset": r.char_offset, "match_method": r.match_method,
                        "model_confidence": r.model_confidence, "shortlist": r.shortlist})
    return path


def load_alias_table(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """(label, paper_record_id) -> the accepted alias row. Only ``mechanical_corroboration`` rows."""
    out: dict[tuple[str, str], dict[str, str]] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if (row.get("accepted_by") or "") != ACCEPTED_BY:
                continue
            sid = (row.get("system_id") or "").strip()
            if not sid:
                continue
            out[((row.get("label") or ""), (row.get("paper_record_id") or ""))] = row
    return out


class AliasAttributor(AB.Attributor):
    """`analyse_blocks.Attributor` widened by the paper-corroborated alias table.

    It only ever fills an ABSTENTION: the base attributor runs first, and an attribution or a
    refusal it produced is returned untouched. That is the whole safety property - the alias table
    adds recall to the labels the matcher could not name, and cannot overturn a guard it fired.
    """

    uses_record_id = True  # the one-line hook analyse_blocks.build_arm_table tests for

    def __init__(self, *args: Any, aliases: dict[tuple[str, str], dict[str, str]] | None = None,
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.aliases = aliases or {}
        self.alias_hits: collections.Counter = collections.Counter()

    def attribute(self, label: str, note: str = "", record_id: str = "") -> AB.Attribution:
        base = super().attribute(label, note)
        if base.attributed or not record_id:
            return base
        if base.method.startswith("vetoed") or base.method.startswith("ambiguous") \
                or base.method == "refused-ablation":
            return base
        row = self.aliases.get((str(label), str(record_id)))
        if row is None:
            return base
        self.alias_hits[row["system_id"]] += 1
        return AB.Attribution(
            system_id=row["system_id"],
            method=f"alias-{row.get('match_method', '')}",
            matched_on=row.get("corroborating_string", ""),
            reason=(f"alias corroborated in {record_id} at char "
                    f"{row.get('char_offset', '')}: {row.get('corroborating_string', '')!r}"),
        )


ONE_LINE_BEFORE = "        att = attributor.attribute(label, note)\n"
ONE_LINE_AFTER = (
    "        att = attributor.attribute(label, note, record_id=str(rec.get(\"record_id\") or \"\")) "
    "if getattr(attributor, \"uses_record_id\", False) else attributor.attribute(label, note)\n"
)


#: The marker that says `analyse_blocks.py` already forwards the paper id, so no patch is needed.
ALREADY_APPLIED = 'record_id=str(rec.get("record_id") or "")'


def load_patched_blocks(path: Path = BLOCKS_SCRIPT) -> Any:
    """`analyse_blocks` with the one-line change applied in memory, or as-is once it is applied on disk.

    Originally this was a dry run against an unedited `analyse_blocks.py`. The change is now applied
    on disk, so the patch is skipped when the marker is present - and still applied in memory if it
    is not, which keeps this script working against an unpatched checkout.
    """
    src = path.read_text(encoding="utf-8")
    if ALREADY_APPLIED in src:
        patched = src
    elif src.count(ONE_LINE_BEFORE) == 1:
        patched = src.replace(ONE_LINE_BEFORE, ONE_LINE_AFTER)
    else:
        raise SystemExit(f"{path}: the attribution call is neither already alias-aware nor in the "
                         f"expected unpatched form ({src.count(ONE_LINE_BEFORE)} matches); "
                         "analyse_blocks.py has changed and this hook needs re-deriving")
    spec = importlib.util.spec_from_loader("analyse_blocks_aliased", loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules["analyse_blocks_aliased"] = module
    exec(compile(patched, str(path), "exec"), module.__dict__)  # noqa: S102 - our own source
    return module


def block_counts(module: Any, attributor: Any, *, rejects: Path = REJECTS,
                 results: Path | None = None, evidence: Path | None = None,
                 systems: Path = SYSTEMS, agg: str = "median",
                 rank_threshold: int = 4) -> dict[str, Any]:
    """Run the block construction with `attributor` and return the numbers that matter for RQ3."""
    comparators = module.load_comparators(rejects)
    own = module.load_own_arms(results or module.RESULTS, evidence or module.EVIDENCE)
    arms_all = module.build_arm_table(comparators, own, attributor, agg=agg)
    arms_blocks, _ = module.drop_single_arm_blocks(arms_all)
    arms_kept, arms_routed, ablation = module.split_ablation_blocks(arms_blocks)
    arms_kept, _ = module.drop_single_arm_blocks(arms_kept)
    arms = module.annotate_blocks(arms_kept, rank_threshold=rank_threshold)
    blocks = module.block_summary(arms)
    comparator_arms = arms[arms["role"] == "comparator"]
    attributed = comparator_arms[comparator_arms["system_id"] != ""]
    per_block = attributed.groupby("block")["system_id"].nunique() if len(attributed) else None
    rich_blocks = set(per_block[per_block >= 2].index) if per_block is not None else set()
    rich = arms[arms["block"].isin(rich_blocks)]
    contrasts: list[dict[str, Any]] = []
    codings = module.load_codings(systems)
    for contrast in module.CONTRASTS:
        frame = module.contrast_frame(arms, contrast, codings, include_own=False)
        diffs = module.block_differences(frame) if len(frame) else frame
        contrasts.append({
            "name": contrast.name,
            "blocks": int(diffs["block"].nunique()) if len(diffs) else 0,
            "papers": int(diffs["record_id"].nunique()) if len(diffs) and "record_id" in diffs
            else 0,
        })
    return {
        "arms": len(arms),
        "blocks": int(arms["block"].nunique()) if len(arms) else 0,
        "papers": int(blocks["record_id"].nunique()) if len(blocks) else 0,
        "comparator_arms": len(comparator_arms),
        "attributed_comparator_arms": len(attributed),
        "distinct_systems_among_comparators": int(attributed["system_id"].nunique())
        if len(attributed) else 0,
        "anonymous_comparator_arms": int((comparator_arms["system_id"] == "").sum()),
        "own_variant_arms": int((arms["role"] == "own_variant").sum()) if len(arms) else 0,
        "blocks_two_attributed_comparators": len(rich_blocks),
        "papers_of_those_blocks": int(rich["record_id"].nunique()) if len(rich) else 0,
        "blocks_routed_ablation": ablation["blocks_routed"],
        "arms_routed_ablation": ablation["arms_routed"],
        "arms_routed_frame": len(arms_routed),
        "contrasts": contrasts,
        "arms_frame": arms,
    }


# --------------------------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------------------------
def mention_df_report(index: MentionIndex, top: int = 40) -> str:
    """Document frequency of every registry name over the scanned papers - how GENERIC_NAME_KEYS
    was derived, printable so the curation can be re-checked when the registry grows."""
    df: collections.Counter = collections.Counter()
    for entries in index.papers.values():
        for key in {key_of(m.name) for m in entries.values()}:  # once per paper, not once per id
            df[key] += 1
    n = max(len(index.papers) - len(index.missing), 1)
    lines = [(f"  name-key document frequency over {n} papers (head of the distribution; a "
              "key in GENERIC_NAME_KEYS may not corroborate on its own)")]
    for key, count in df.most_common(top):
        flag = " GENERIC" if key in GENERIC_NAME_KEYS else ""
        lines.append(f"    {count:5d} ({count / n:5.1%})  {key[:34]:36}{flag}")
    return "\n".join(lines)


def unattributed_report(comparators: Any, aliases: dict[tuple[str, str], dict[str, str]],
                        attributor: AB.Attributor, top: int = 10) -> list[tuple[str, int, str]]:
    """The `top` most frequent comparator labels still without a coded system, and why."""
    counts: collections.Counter = collections.Counter()
    why: dict[str, str] = {}
    for rec in comparators.to_dict(orient="records"):
        label = str(rec.get("reported_system_name") or "")
        note = str(rec.get("note") or "")
        rid = str(rec.get("record_id") or "")
        att = attributor.attribute(label, note)
        if att.attributed or (label, rid) in aliases:
            continue
        counts[label] += 1
        if label not in why:
            why[label] = (att.method if att.method != "abstain-no-match"
                          else (stoplist_reason(label) or "no registry match, no accepted alias"))
    return [(label, n, why.get(label, "")) for label, n in counts.most_common(top)]


def _fmt(n: float) -> str:
    return f"{n:,}" if isinstance(n, int) else f"{n:,.2f}"


# --------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------
def make_backend(kind: str, log: logging.Logger) -> Callable[..., Any] | None:
    """The proposal backend: Claude Code headless (subscription) or the Messages API."""
    if kind == "claude-code":
        exe = screen_llm.find_claude_exe()
        if not exe:
            log.error("Claude Code CLI not found (set CLAUDE_CODE_EXE or put 'claude' on PATH)")
            return None
        return screen_llm.vote_batch_claude_code
    if kind == "api":
        import code_system
        key = screen_llm.api_key()
        if not key:
            log.error("no ANTHROPIC_API_KEY (environment or repo .env)")
            return None
        try:
            import anthropic
        except ImportError:
            log.error("pip install anthropic")
            return None
        return code_system.make_api_backend(anthropic.Anthropic(api_key=key))
    raise ValueError(f"unknown backend {kind!r}")


def main(argv: list[str] | None = None, backend: Callable[..., Any] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rejects", type=Path, default=REJECTS)
    ap.add_argument("--systems", type=Path, default=SYSTEMS)
    ap.add_argument("--candidates", type=Path, default=CANDIDATES)
    ap.add_argument("--fulltext-dir", type=Path, default=FULLTEXT_DIR)
    ap.add_argument("--aliases", type=Path, default=ALIASES_OUT,
                    help="where the accepted alias table is written, and the table --rerun-blocks "
                         "feeds to analyse_blocks.py")
    ap.add_argument("--refused", type=Path, default=REFUSED_OUT)
    ap.add_argument("--cache", type=Path, default=CACHE_PATH,
                    help="model answers, keyed by (label, paper); a re-run makes no call")
    ap.add_argument("--mention-cache", type=Path, default=MENTION_CACHE)
    ap.add_argument("--backend", default="claude-code", choices=("claude-code", "api"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--shortlist-threshold", type=int, default=SHORTLIST_THRESHOLD,
                    help=f"LOW name-match threshold for retrieval only (default "
                         f"{SHORTLIST_THRESHOLD}; the registry groups at 92 and never accepts here)")
    ap.add_argument("--shortlist-size", type=int, default=MAX_SHORTLIST)
    ap.add_argument("--fuzzy-threshold", type=int, default=LB.FUZZY_THRESHOLD,
                    help="threshold used by the existing vetoes, unchanged")
    ap.add_argument("--min-confidence", type=float, default=MIN_CONFIDENCE)
    ap.add_argument("--limit", type=int, default=0, help="cap the candidates (a smoke run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="retrieval and guards only: make no backend call and write no table")
    ap.add_argument("--rerun-blocks", action="store_true",
                    help="re-run analyse_blocks.py's block construction with the alias table "
                         "applied through the one-line change, without editing that script")
    ap.add_argument("--blocks-only", action="store_true",
                    help="skip proposing; read the alias table from --aliases and only re-run blocks")
    ap.add_argument("--report-mention-df", action="store_true",
                    help="print the measured name document frequency GENERIC_NAME_KEYS came from")
    ap.add_argument("--no-write", action="store_true", help="compute and print, write nothing")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        stream=sys.stderr)
    log = logging.getLogger("build_alias_table")

    print("=" * 100)
    print("HARNESS-DB comparator alias table: paper-corroborated names for baseline-table rivals")
    print("=" * 100)
    print()
    print("THE RULE: a mapping 'label L in paper P means coded system S' is accepted only when a")
    print("name of S occurs in P's own full text. A model may propose; the paper accepts.")
    print()

    registry = LB.load_registry(args.systems, args.candidates)
    index = MentionIndex(registry, root=args.fulltext_dir)
    cached_papers = index.load_cache(args.mention_cache)
    comparators = AB.load_comparators(args.rejects)
    base = AB.Attributor(registry=registry, threshold=args.fuzzy_threshold)

    if args.blocks_only:
        aliases = load_alias_table(args.aliases)
        print(f"  alias table read from {args.aliases} ({len(aliases)} accepted rows)")
        return _rerun(args, registry, aliases, log)

    candidates, pre_refused, counts = collect_candidates(comparators, base)
    if args.limit:
        candidates = candidates[:args.limit]

    t0 = time.time()
    record_ids = {c.record_id for c in candidates}
    for rid in sorted(record_ids):
        index.scan(rid)
    titles = paper_titles(index, record_ids)
    if not args.no_write:
        index.save_cache(args.mention_cache)

    print("CANDIDATES")
    print(f"  comparator rows considered                        {counts['rows_considered']:>7,}")
    print(f"  already attributed by the existing matcher        "
          f"{counts['rows_already_attributed']:>7,}   left untouched")
    for reason in ("existing_guard_ablation", "existing_guard_veto", "no_usable_harness_name",
                   "stoplist_model_name", "stoplist_generic_label", "stoplist_placeholder",
                   "stoplist_key_too_short", "stoplist_no_name"):
        if counts.get(reason):
            print(f"  refused before any proposal: {reason:24s} {counts[reason]:>7,}")
    print(f"  rows eligible for a proposal                      {counts['rows_proposable']:>7,}")
    print(f"  distinct (label, paper) pairs proposed on         {len(candidates):>7,}   "
          f"{len({c.label for c in candidates})} distinct labels, "
          f"{len(record_ids)} papers")
    print(f"  papers scanned for name mentions                  {len(record_ids):>7,}   "
          f"({cached_papers} from cache, {len(index.missing)} without fetched full text, "
          f"{time.time() - t0:.1f}s)")
    shortlists = batch_items(candidates, registry, index, titles, args.shortlist_threshold,
                             args.shortlist_size)
    sizes = [len(i["shortlist"]) for i in shortlists]
    print(f"  shortlist size (threshold {args.shortlist_threshold}, cap {args.shortlist_size})      "
          f"             mean {sum(sizes) / max(len(sizes), 1):.1f}, "
          f"{sum(1 for s in sizes if s == 0)} pairs with an empty shortlist")
    print()

    if args.report_mention_df:
        print(mention_df_report(index))
        print()

    if args.dry_run:
        print("DRY RUN: no backend call, no table written. Retrieval and guards only.")
        print(f"  {len(shortlists)} pairs would be sent in "
              f"{len(chunk_by_paper(shortlists, args.batch_size))} batches of <= {args.batch_size}.")
        return 0

    if backend is None:
        backend = make_backend(args.backend, log)
        if backend is None:
            return 2
    cache = load_proposal_cache(args.cache)
    proposals, mstats = propose(shortlists, backend, model=args.model, effort=args.effort,
                                cache=cache, batch_size=args.batch_size, log=log,
                                exe=(screen_llm.find_claude_exe() or "claude")
                                if args.backend == "claude-code" else "api")
    if not args.no_write:
        save_proposal_cache(args.cache, cache)

    own_of = {(c.label, c.record_id): c.own_system_id for c in candidates}
    accepted: list[Accepted] = []
    refused: list[Refusal] = list(pre_refused)
    cross_checks: collections.Counter = collections.Counter()
    for prop in proposals:
        acc, ref, cross = adjudicate(prop, registry, index,
                                     own_system_id=own_of.get((prop.label, prop.record_id), ""),
                                     threshold=args.fuzzy_threshold,
                                     min_confidence=args.min_confidence)
        if acc is not None:
            accepted.append(acc)
            cross_checks[cross] += 1
        else:
            refused.append(ref)

    print("PROPOSALS (the model proposes; it never accepts)")
    print(f"  pairs sent to the model                           {mstats['sent']:>7,}   "
          f"in {mstats['calls']} calls, {mstats['batches_failed']} batches failed")
    print(f"  pairs answered from the (label, paper) cache      {mstats['from_cache']:>7,}   "
          "a re-run of this script makes no call at all")
    if mstats["calls"]:
        print(f"  tokens {mstats['tokens_in']:,} in / {mstats['tokens_out']:,} out, "
              f"list-price equivalent ${mstats['cost_usd']:.2f}, model {mstats['model']}")
    named = sum(1 for p in proposals if p.system_id)
    print(f"  proposals naming a system                         {named:>7,}   "
          f"({len(proposals) - named} answered null)")
    print()
    print("ACCEPTANCE")
    print(f"  ACCEPTED ALIASES                                  {len(accepted):>7,}   "
          f"{len({a.system_id for a in accepted})} distinct coded systems, "
          f"{len({a.record_id for a in accepted})} papers")
    print(f"  refused                                           {len(refused):>7,}")
    by_reason = collections.Counter(r.reason for r in refused)
    for reason, n in by_reason.most_common():
        print(f"    {reason:32s} {n:>7,}")
    if cross_checks:
        print("  cross-check on the model's own expected corroborating string:")
        for kind, n in cross_checks.most_common():
            print(f"    {kind:32s} {n:>7,}")
    print()

    if accepted:
        print("A HAND-CHECKABLE SAMPLE OF ACCEPTED ALIASES")
        print("  (verify any row: raw = Path(fs.fulltext_path(paper)).read_text('utf-8','replace'); "
              "raw[offset:offset+len(span)])")
        for a in sorted(accepted, key=lambda x: (x.system_id, x.record_id))[:15]:
            print(f"    {a.label[:34]:36} -> {a.system_id[:22]:24} {a.record_id[:24]:26} "
                  f"@{a.char_offset:>7} {a.corroborating_string[:24]!r}")
        print()

    if not args.no_write:
        write_aliases(accepted, args.aliases)
        write_refused(refused, args.refused)
        print(f"  written: {args.aliases}")
        print(f"           {args.refused}")
        print(f"           {args.cache}  (model answers, keyed by (label, paper))")
        print()

    aliases = {(a.label, a.record_id): {"system_id": a.system_id,
                                        "corroborating_string": a.corroborating_string,
                                        "char_offset": str(a.char_offset),
                                        "match_method": a.match_method,
                                        "accepted_by": ACCEPTED_BY}
               for a in accepted}
    print("THE TEN MOST FREQUENT STILL-UNATTRIBUTED LABELS")
    for label, n, reason in unattributed_report(comparators, aliases, base):
        print(f"    {n:4d}  {label[:44]:46} {reason[:52]}")
    print()

    if args.rerun_blocks:
        return _rerun(args, registry, aliases, log)
    print("Next: python scripts/build_alias_table.py --blocks-only --rerun-blocks")
    return 0


def _rerun(args: argparse.Namespace, registry: Any,
           aliases: dict[tuple[str, str], dict[str, str]], log: logging.Logger) -> int:
    """The dry run: analyse_blocks.py with the one-line change applied in memory, both files loaded."""
    print("RE-RUNNING analyse_blocks.py WITH THE ALIAS TABLE (the file is not edited)")
    module = load_patched_blocks()
    print(f"  loaded {BLOCKS_SCRIPT} with the one-line change applied in memory:")
    print(f"    -  {ONE_LINE_BEFORE.strip()}")
    print(f"    +  {ONE_LINE_AFTER.strip()}")
    print(f"  loaded {args.aliases}: {len(aliases)} accepted aliases")
    before = block_counts(module, module.Attributor(registry=registry,
                                                   threshold=args.fuzzy_threshold),
                          rejects=args.rejects, systems=args.systems)
    after_att = AliasAttributor(registry=registry, threshold=args.fuzzy_threshold, aliases=aliases)
    after = block_counts(module, after_att, rejects=args.rejects, systems=args.systems)
    print()
    print(f"  {'measure':52} {'before':>8} {'after':>8}")
    for key, label in (
        ("blocks", "blocks analysed"),
        ("arms", "arms in those blocks"),
        ("papers", "papers"),
        ("comparator_arms", "comparator arms"),
        ("attributed_comparator_arms", "ATTRIBUTED comparator arms"),
        ("distinct_systems_among_comparators", "distinct coded systems among comparators"),
        ("anonymous_comparator_arms", "anonymous comparator arms"),
        ("own_variant_arms", "arms resolved to the reporting paper's own system"),
        ("blocks_two_attributed_comparators", "BLOCKS WITH 2+ ATTRIBUTED COMPARATOR ARMS"),
        ("papers_of_those_blocks", "PAPERS THOSE BLOCKS SPAN"),
    ):
        print(f"  {label:52} {_fmt(before[key]):>8} {_fmt(after[key]):>8}")
    print()
    print("  per contrast, own arm EXCLUDED (blocks / papers the contrast actually varies in):")
    b_by = {c["name"]: c for c in before["contrasts"]}
    multi = 0
    for c in after["contrasts"]:
        bb = b_by.get(c["name"], {"blocks": 0, "papers": 0})
        flag = "  <- more than one paper" if c["papers"] > 1 else ""
        if c["papers"] > 1:
            multi += 1
        print(f"    {c['name']:26} {bb['blocks']:>4} / {bb['papers']:>3} papers  ->  "
              f"{c['blocks']:>4} / {c['papers']:>3} papers{flag}")
    print()
    print(f"  CONTRASTS DRAWING ON MORE THAN ONE PAPER: {multi} of {len(after['contrasts'])} "
          "(before: "
          f"{sum(1 for c in before['contrasts'] if c['papers'] > 1)})")
    print("  A contrast drawn from a single paper is not independently replicated, so this is the")
    print("  number that decides whether the attribution wall is broken or only dented.")
    log.info("block re-run complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
