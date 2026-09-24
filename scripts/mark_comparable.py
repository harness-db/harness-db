#!/usr/bin/env python
"""Fill `comparable_key` in data/results.csv: decide which reported scores can be compared.

The review asks whether harness design choices explain benchmark outcomes. A row can only
answer that if it differs from another row in the HARNESS while everything else that moves a
score is held fixed. Everything else means, at minimum, the benchmark, the task set inside it
(the split), the measurement (the metric) and the model. So `comparable_key` is a canonical

    benchmark|split|model

string, and it is EMPTY whenever the row cannot enter the regression. An empty key is not a
judgement about the paper; it says this row cannot be placed beside another one, and the reason
is written into `notes` so a reviewer can audit every exclusion.

Five substantive reasons blank a row (section 2 of the task; codes in `REASONS`):

    system_id_missing      the harness is unknown - an unattributed leaderboard entry can still
                           appear in descriptive tables, but it cannot speak to harness design
    model_missing          no model recorded, so the model cannot be held fixed
    model_unidentifiable   a model string naming nothing resolvable ("various", "LLM"), or
                           naming more than one model (the harness/model pair is not a point)
    split_missing          no split recorded; "SWE-bench" alone is three different task sets
    metric_nonstandard     the measurement is not the benchmark's standard one. A `% resolved`
                           row and an `accuracy` row on SWE-bench are not the same number
    metric_missing         no metric recorded, so we cannot check the measurement at all
    score_missing          no score
    score_not_numeric      a score that does not parse as a finite number ("~40", "n/a", "-")

Three mechanical reasons blank a row as well, because a string we do not recognise cannot be
trusted to mean the same thing as another row's string:

    benchmark_unrecognised the benchmark is not on the controlled list below
    split_unrecognised     the split is not in that benchmark's split vocabulary
    benchmark_split_conflict a qualified benchmark name and the split column disagree
                           ("SWE-bench Verified" with split "Lite")

And one that is off by default, so the diagnosis is visible before anything is dropped:

    singleton_key          with --min-systems N, a key shared by fewer than N distinct systems.
                           A key with one system supports no comparison, but seeing HOW MANY
                           keys are singletons is the finding, so the default keeps them.

Usage:
    python scripts/mark_comparable.py                       # in place, writes results.csv.bak
    python scripts/mark_comparable.py --min-systems 2       # also blank singleton keys
    python scripts/mark_comparable.py --in a.csv --out b.csv
    python scripts/mark_comparable.py --dry-run             # report only, write nothing

Caveats that survive canonicalisation - version drift, contamination, self-reporting,
harness/model entanglement, scaffold drift - are in docs/benchmark_caveats.md. This script
makes rows *commensurable*; it does not make them *trustworthy*.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "data" / "results.csv"
SUMMARY = REPO / "data" / "comparable_summary.json"

# scripts/validate.py enforces exactly this header, in this order.
RESULT_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd",
                  "tokens", "date", "source_url", "comparable_key", "notes"]

REASONS = [
    # ordered by precedence: the first applicable reason is the row's primary reason
    "system_id_missing",
    "model_missing",
    "model_unidentifiable",
    "benchmark_unrecognised",
    "split_missing",
    "split_unrecognised",
    "benchmark_split_conflict",
    "metric_missing",
    "metric_nonstandard",
    "score_missing",
    "score_not_numeric",
    "singleton_key",
]

# `[not-comparable: ...]` is a sentinel so that re-running the script replaces its own note
# instead of appending a second copy. Anything a human or the extractor wrote is preserved.
NOTE_RE = re.compile(r"\s*\[not-comparable:[^\]]*\]")


# --------------------------------------------------------------------------------------
# string normalisation
# --------------------------------------------------------------------------------------
def _fold(text: str) -> str:
    """Case- and punctuation-insensitive key: lowercase, alphanumerics only, no spaces.

    "SWE-bench Verified", "SWE_Bench_verified", "swebench verified" all fold to
    "swebenchverified". Spaces are removed rather than collapsed because the boards are not
    consistent about whether "SWE-bench" is one word, and neither are papers. The Greek tau
    used for tau-bench is spelled out first, since the boards and the papers use both.
    """
    s = (text or "").strip().lower()
    for ch in ("τ", "\U0001d70f", "ᵭ5"):  # tau, math italic tau
        s = s.replace(ch, "tau")
    return re.sub(r"[^a-z0-9]+", "", s)


# --------------------------------------------------------------------------------------
# benchmarks
# --------------------------------------------------------------------------------------
# The controlled list. Extend it as the data requires; an unlisted benchmark blanks the row
# rather than inventing a key, because two spellings we have not seen may or may not be the
# same task set and guessing is the one thing this script must not do.
#
# Qualified names are NOT separate benchmarks here even though the task's controlled list
# names "SWE-bench Verified" as one. The reason is mechanical: the same measurement arrives
# written both ways - benchmark="SWE-bench Verified", split="test", and benchmark="SWE-bench",
# split="Verified" - and if the key kept the qualifier in the benchmark position those two rows
# would never meet. So every qualifier is resolved into the split (QUALIFIED_BENCHMARKS below),
# the benchmark position always holds the family, and both spellings produce
# "SWE-bench|Verified|<model>". A qualified name that contradicts the split column is a
# conflict, not a silent overwrite.
BENCHMARK_ALIASES: dict[str, str] = {
    # SWE-bench family (Jimenez et al. 2024; swebench.com)
    "swebench": "SWE-bench",
    "swebenchfull": "SWE-bench",
    "swebenchtest": "SWE-bench",
    "swe": "SWE-bench",
    "swebenchpython": "SWE-bench",
    # computer use
    "osworld": "OSWorld",
    "osworldverified": "OSWorld",
    "webarena": "WebArena",
    "visualwebarena": "VisualWebArena",       # a different task set, not a WebArena split
    "webarenalite": "WebArena-Lite",          # ditto: re-annotated, 165 tasks, own numbers
    "webvoyager": "WebVoyager",
    "mind2web": "Mind2Web",
    "onlinemind2web": "Online-Mind2Web",
    "windowsagentarena": "WindowsAgentArena",
    "androidworld": "AndroidWorld",
    # terminal / shell
    "terminalbench": "Terminal-Bench",
    "tbench": "Terminal-Bench",
    "terminalbenchcore": "Terminal-Bench",
    # general assistant
    "gaia": "GAIA",
    "gaia2": "GAIA2",                          # separate benchmark, not a GAIA split
    "assistantbench": "AssistantBench",
    "hle": "HLE",
    "humanityslastexam": "HLE",
    # tool / dialogue
    "taubench": "tau-bench",
    "tau1bench": "tau-bench",
    "tau2bench": "tau2-bench",                 # tau2 is a rebuilt benchmark, not a tau split
    # code / science / research
    "swelancer": "SWE-Lancer",
    "swebenchmultimodal": "SWE-bench",         # handled as a split, see QUALIFIED_BENCHMARKS
    "humaneval": "HumanEval",
    "mbpp": "MBPP",
    "livecodebench": "LiveCodeBench",
    "usaco": "USACO",
    "corebench": "CORE-Bench",
    "scicode": "SciCode",
    "scienceagentbench": "ScienceAgentBench",
    "mlebench": "MLE-bench",
    "dsbench": "DSBench",
    "appworld": "AppWorld",
    "webshop": "WebShop",
    "alfworld": "ALFWorld",
    "toolbench": "ToolBench",
    "agentbench": "AgentBench",
    "cybench": "Cybench",
}

# A qualified benchmark name folds into (family, split). The split it implies must agree with
# whatever the split column says.
QUALIFIED_BENCHMARKS: dict[str, tuple[str, str]] = {
    "swebenchverified": ("SWE-bench", "Verified"),
    "swebenchlite": ("SWE-bench", "Lite"),
    "swebenchmultimodal": ("SWE-bench", "Multimodal"),
    "swebenchmultilingual": ("SWE-bench", "Multilingual"),
    "swebenchverifiedmini": ("SWE-bench", "Verified-Mini"),
    "swebenchmini": ("SWE-bench", "Verified-Mini"),
    "swebenchpro": ("SWE-bench-Pro", "full"),  # Scale AI's, not the SWE-bench family at all
    "osworldverified": ("OSWorld", "Verified"),
    "taubenchairline": ("tau-bench", "airline"),
    "taubenchretail": ("tau-bench", "retail"),
    "tau2benchairline": ("tau2-bench", "airline"),
    "tau2benchretail": ("tau2-bench", "retail"),
    "tau2benchtelecom": ("tau2-bench", "telecom"),
    "corebenchhard": ("CORE-Bench", "hard"),
    "terminalbenchcore": ("Terminal-Bench", "core"),
    "swebenchverifiedmini50": ("SWE-bench", "Verified-Mini"),
}

# A LEADERBOARD is not a benchmark. HAL (hal.cs.princeton.edu) runs nine different benchmarks,
# and the harvest records the family as "HAL" with the benchmark name in the split column, so a
# row whose benchmark column names the board is re-resolved from its split. HAL is the one board
# in the harvest that RUNS the scaffolds itself instead of accepting a submitted number, which is
# why its rows are worth rescuing rather than discarding.
BOARD_FAMILIES = {"hal", "holisticagentleaderboard"}


# --------------------------------------------------------------------------------------
# splits
# --------------------------------------------------------------------------------------
# Splits are canonicalised to the board's OWN vocabulary, per benchmark, because the same word
# means different things on different boards: "test" on SWE-bench is the full 2,294-instance
# split that everyone calls "full", while "test" on GAIA is the held-out half whose labels are
# private. So there is no global split map - only per-benchmark tables, plus a small generic
# table for benchmarks whose boards ship a single task set.
#
# A split we do not recognise blanks the row. That is deliberate: an unrecognised split string
# is the signature of a restricted subset ("first 100 instances", "Level 3 only"), and those
# are exactly the rows that must not be pooled with the full split.
SPLIT_ALIASES: dict[str, dict[str, str]] = {
    "SWE-bench": {
        # "test" is the HuggingFace split name for the full 2,294 instances; the community says
        # "full". Both fold to "full" so a paper's "SWE-bench (test)" meets a board's "full".
        "test": "full", "full": "full", "fulltest": "full", "all": "full", "2294": "full",
        "swebench": "full", "original": "full", "principal": "full",
        "lite": "Lite", "swebenchlite": "Lite", "300": "Lite",
        "verified": "Verified", "swebenchverified": "Verified", "500": "Verified",
        "verifiedmini": "Verified-Mini", "mini": "Verified-Mini", "swebenchverifiedmini":
            "Verified-Mini", "verified50": "Verified-Mini",
        "multimodal": "Multimodal", "mm": "Multimodal",
        "multilingual": "Multilingual",
        "dev": "dev", "validation": "dev", "val": "dev",  # 225 instances, rarely reported
    },
    "OSWorld": {
        # OSWorld-Verified (2025) re-checked the 369 tasks; the pre-Verified numbers are on a
        # task set with known-broken evaluators, so they are a different split, not noise.
        "verified": "Verified", "osworldverified": "Verified", "369": "Verified",
        "test": "full", "full": "full", "all": "full", "osworld": "full", "369tasks": "full",
        "selfreported": "self-reported", "selfreport": "self-reported",
        "smalltest": "small", "small": "small", "osworldsmall": "small",
        # The OSWorld self-reported sheet is split by OBSERVATION MODALITY, which is a harness
        # design choice as much as a task set. A screenshot-only agent and an a11y-tree agent
        # are not solving the same problem, so the modality stays in the split and never pools.
        "selfreportedscreenshot": "self-reported/screenshot",
        "selfreportedscreenshota11ytree": "self-reported/screenshot+a11y",
        "selfreporteda11ytree": "self-reported/a11y",
        "selfreportedsetofmark": "self-reported/set-of-mark",
        "screenshot": "self-reported/screenshot", "a11ytree": "self-reported/a11y",
        "screenshota11ytree": "self-reported/screenshot+a11y",
        "setofmark": "self-reported/set-of-mark",
    },
    "WebArena": {
        "test": "full", "full": "full", "all": "full", "webarena": "full", "812": "full",
        "val": "val", "validation": "val", "dev": "val",
    },
    "Terminal-Bench": {
        # The dataset is versioned and the versions are not comparable: Terminal-Bench 2.0
        # replaced most tasks. Version is part of the split, so 1.0 never pools with 2.0.
        "core": "core", "terminalbenchcore": "core", "tbenchcore": "core",
        "terminalbench10core": "core@1.0", "core10": "core@1.0", "10": "core@1.0",
        "terminalbench10": "core@1.0", "terminalbenchv10": "core@1.0",
        "terminalbench20core": "core@2.0", "core20": "core@2.0", "20": "core@2.0",
        "terminalbench20": "core@2.0", "terminalbenchv20": "core@2.0",
        # the strings the harvest actually produced (data/raw/leaderboards.jsonl): the board
        # labels its own release AND the pinned dataset version, and "@0.1.1" and ":0.1.1" fold
        # to the same key because punctuation is ignored
        "terminalbench10terminalbenchcore011": "core@1.0",
        "terminalbenchcore011": "core@1.0",
        "terminalbench30": "core@3.0", "terminalbench40": "core@4.0",
        "terminalbench15": "core@1.5",
        "hardcore": "hardcore",
        "test": "core", "full": "core", "all": "core",
    },
    "GAIA": {
        # GAIA's public "validation" set (165) is where nearly every reported number comes from;
        # "test" (300) is scored by the leaderboard only. They are not interchangeable.
        "validation": "val", "val": "val", "dev": "val", "public": "val", "165": "val",
        "test": "test", "private": "test", "300": "test",
        # Per-level numbers are a subset of one split and are kept distinct on purpose.
        "validationlevel1": "val/level1", "level1": "val/level1",
        "validationlevel2": "val/level2", "level2": "val/level2",
        "validationlevel3": "val/level3", "level3": "val/level3",
    },
    "tau-bench": {
        "airline": "airline", "taubenchairline": "airline", "flight": "airline",
        "retail": "retail", "taubenchretail": "retail",
        # No "all"/"average": tau-bench's two domains have different task counts and difficulty,
        # and a mean over them is not a measurement either domain's rows can be compared to.
    },
    "tau2-bench": {
        "airline": "airline", "retail": "retail", "telecom": "telecom",
        # The tau2 board splits by MODALITY as well as domain (text, voice, and a "text-legacy"
        # re-run of the tau1 prompts). Voice adds speech recognition to the task; a voice number
        # and a text number on the same domain are not the same measurement.
        "textairline": "text/airline", "textretail": "text/retail",
        "texttelecom": "text/telecom", "textbankingknowledge": "text/banking_knowledge",
        "voiceairline": "voice/airline", "voiceretail": "voice/retail",
        "voicetelecom": "voice/telecom", "voicebankingknowledge": "voice/banking_knowledge",
        "textlegacyairline": "text-legacy/airline", "textlegacyretail": "text-legacy/retail",
        "textlegacytelecom": "text-legacy/telecom",
        "bankingknowledge": "banking_knowledge",
    },
    "CORE-Bench": {"hard": "hard", "medium": "medium", "easy": "easy"},
}

# Split tokens that carry no information beyond "the whole of it". They defer to a qualifier
# already present in the benchmark name (see evaluate_row).
VACUOUS_SPLITS = {"full", "test"}

# Benchmarks whose board ships one task set: only a "this is the whole thing" split is accepted.
GENERIC_SPLITS = {
    "test": "test", "full": "full", "all": "full", "default": "full", "main": "full",
    "val": "val", "validation": "val", "dev": "val", "train": "train",
    "public": "test", "private": "test",
}


# --------------------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------------------
# Each benchmark has ONE standard measurement. Aliasing is per benchmark and only where a
# board's wording provably denotes the same computation:
#
#   * OSWorld/WebArena/GAIA/Terminal-Bench boards write "success rate", "accuracy" and
#     "resolve rate" for the identical quantity (fraction of tasks whose checker passed), so
#     those are aliased to one token.
#   * On SWE-bench they are NOT aliased. "accuracy" on SWE-bench is genuinely ambiguous - it
#     has been used for file-localisation accuracy, patch-applies-cleanly rate and resolve
#     rate - so an "accuracy" row is blanked rather than pooled with "% resolved". This costs
#     us the HAL-harvested SWE-bench-Verified-Mini rows, which are labelled "accuracy %" and
#     really are resolve rate; admitting them is a one-line, deliberate change to this table,
#     and it should be made deliberately, not by a fuzzy matcher.
#   * pass^1 (tau-bench) is not pass@1: pass^k is all-k-trials-succeed. A pass@1 row and a
#     pass^1 row are different estimators and do not pool.
STANDARD_METRIC: dict[str, str] = {
    "SWE-bench": "resolved",
    "SWE-bench-Pro": "resolved",
    "OSWorld": "success",
    "WebArena": "success",
    "WebArena-Lite": "success",
    "VisualWebArena": "success",
    "WebVoyager": "success",
    "Mind2Web": "success",
    "Online-Mind2Web": "success",
    "WindowsAgentArena": "success",
    "AndroidWorld": "success",
    "Terminal-Bench": "success",
    "GAIA": "accuracy",
    "GAIA2": "accuracy",
    "AssistantBench": "accuracy",
    "HLE": "accuracy",
    "tau-bench": "pass^1",
    "tau2-bench": "pass^1",
    "SWE-Lancer": "resolved",
    "HumanEval": "pass@1",
    "MBPP": "pass@1",
    "LiveCodeBench": "pass@1",
    "USACO": "success",
    "CORE-Bench": "accuracy",
    "SciCode": "accuracy",
    "ScienceAgentBench": "success",
    "MLE-bench": "medal",
    "DSBench": "accuracy",
    "AppWorld": "success",
    "WebShop": "success",
    "ALFWorld": "success",
    "ToolBench": "success",
    "AgentBench": "success",
    "Cybench": "success",
}

# surface spelling -> measurement token. Percent signs, "%" suffixes, "(mean of n runs)" and
# "rate" are cosmetic; the token is the computation.
METRIC_ALIASES: dict[str, str] = {
    "resolved": "resolved", "resolvedpct": "resolved", "resolvedpercent": "resolved",
    "pctresolved": "resolved", "percentresolved": "resolved", "resolverate": "resolved",
    "resolutionrate": "resolved", "issuesresolved": "resolved", "resolvedrate": "resolved",
    "success": "success", "successrate": "success", "successratepct": "success",
    "taskssuccessrate": "success", "sr": "success", "completionrate": "success",
    "taskcompletionrate": "success", "solverate": "success", "solved": "success",
    "accuracy": "accuracy", "acc": "accuracy", "accuracypct": "accuracy",
    "exactmatch": "accuracy", "em": "accuracy",
    "pass1": "pass@1", "passat1": "pass@1", "pass1pct": "pass@1",
    "passhat1": "pass^1", "passpower1": "pass^1",
    "passhat2": "pass^2", "passhat4": "pass^4",
    "medalrate": "medal", "anymedal": "medal",
}
# Per-benchmark overrides, consulted first. These are the cases where a board's or a paper's
# own wording is a known synonym for that benchmark's computation. On SWE-bench "% solved" and
# "success rate" are the resolve rate - the harness either produced a patch that passes the
# hidden tests or it did not - so they are aliased. "accuracy" is deliberately NOT: on
# SWE-bench it has been used for file-localisation accuracy and patch-apply rate as well, and
# collapsing it would silently pool three different numbers. Likewise pass@1 is not aliased
# here, because a pass@1 taken from a k>1 run is a different estimator from a single attempt.
METRIC_ALIASES_BY_BENCHMARK: dict[str, dict[str, str]] = {
    "SWE-bench": {"solved": "resolved", "solverate": "resolved", "success": "resolved",
                  "successrate": "resolved", "fixrate": "resolved"},
    "SWE-bench-Pro": {"solved": "resolved", "success": "resolved", "successrate": "resolved"},
    "SWE-Lancer": {"solved": "resolved", "success": "resolved", "successrate": "resolved"},
}

# The task-completion benchmarks are the opposite case: their boards write "success rate",
# "accuracy", "completion rate" and "solve rate" for one and the same computation - the fraction
# of tasks whose checker passed - and nothing else is on offer. OSWorld's board says "success
# rate", Terminal-Bench's says "accuracy", GAIA's says "accuracy", and all three mean it. Those
# spellings are aliased to whichever token STANDARD_METRIC names for the benchmark, so the
# metric test still bites on genuinely different measurements (pass@1, pass^1, medal rate,
# exact match on a benchmark scored by a checker) without blanking rows over board vocabulary.
TASK_COMPLETION_SYNONYMS = {"success", "successrate", "accuracy", "acc", "completionrate",
                            "taskcompletionrate", "solverate", "solved", "sr"}
for _bench, _std in STANDARD_METRIC.items():
    if _std in ("success", "accuracy") and _bench not in METRIC_ALIASES_BY_BENCHMARK:
        METRIC_ALIASES_BY_BENCHMARK[_bench] = {s: _std for s in TASK_COMPLETION_SYNONYMS}
del _bench, _std


def _fold_metric(text: str) -> str:
    s = (text or "").strip().lower()
    s = s.replace("^", "hat").replace("@", "at")
    s = re.sub(r"\(.*?\)", " ", s)          # "(mean of 5 runs)", "(pass@1)"
    s = re.sub(r"[^a-z0-9]+", "", s)
    s = re.sub(r"(pct|percent)$", "", s)
    s = re.sub(r"(meanof\d*runs?|meanover\d*runs?|avgof\d*runs?)$", "", s)
    return s


# --------------------------------------------------------------------------------------
# models
# --------------------------------------------------------------------------------------
# A row is comparable only if the model is held fixed, so what matters is BASE-MODEL IDENTITY:
# the thing a vendor would call the model, with the snapshot date removed. Date suffixes are
# snapshots of one model (`gpt-4o-2024-05-13` IS `GPT-4o`); version numbers are different
# models (`claude-sonnet-4-6` is NOT `claude-sonnet-5`, and neither is `claude-sonnet-4`).
#
# Two judgement calls worth stating:
#   * `-preview` is kept. `o1-preview` and `o1` were different models with different scores,
#     as were `gpt-4-turbo-preview` and `gpt-4-turbo`.
#   * `-instruct`, `-chat`, `-thinking`, `-high`/`-low` reasoning-effort suffixes are kept.
#     An "-instruct" checkpoint is a different set of weights; a reasoning-effort setting is a
#     different configuration and it moves agent scores a great deal. Keeping them can split
#     a key that a reader would have pooled, which is the safe direction to be wrong in.
MODEL_UNIDENTIFIABLE = {
    "", "-", "--", "n/a", "na", "none", "null", "nan", "?", "unknown", "unspecified",
    "undisclosed", "not reported", "notreported", "not stated", "various", "multiple",
    "mixed", "several", "many", "model n/a", "model na", "see paper", "proprietary",
    "closed", "closed source", "llm", "lm", "an llm", "base model", "default",
    "frontier model", "anonymous", "redacted", "tbd", "other", "custom", "finetuned",
    "fine-tuned", "self-hosted", "open source", "open-source", "agent", "n.a.", "n.r.",
}
# a model string naming more than one model cannot be held fixed
MODEL_MULTI_RE = re.compile(r"\s(?:\+|&|and|/|,|\|)\s|\+(?=[a-z])|\band\b", re.IGNORECASE)
# Used to tell a second model name after a slash ("gpt-4o/claude-sonnet-4") from a slash that is
# part of one model's name ("Qwen3-Coder 480B/A35B Instruct" is total/active MoE parameters, one
# model). Without this test the MoE notation reads as two models and the row is thrown away.
MODEL_FAMILY_RE = re.compile(
    r"^(gpt|chatgpt|o[1-9]|claude|sonnet|opus|haiku|gemini|gemma|llama|codellama|qwen|qwq|"
    r"deepseek|kimi|glm|grok|mistral|mixtral|codestral|devstral|command|nemotron|phi|minimax|"
    r"doubao|seed|step|hunyuan|internlm|internvl|yi|ernie|palm|olmo|granite|aya)\b",
    re.IGNORECASE)
# vendor route prefixes stripped from ids like "openai/gpt-4o" or "us.anthropic.claude-..."
VENDOR_PREFIXES = {
    "openai", "anthropic", "google", "googledeepmind", "deepmind", "meta", "metallama",
    "mistralai", "deepseekai", "deepseek", "qwen", "alibaba", "azure", "bedrock", "vertex",
    "vertexai", "together", "togetherai", "fireworks", "openrouter", "xai", "moonshotai",
    "zhipuai", "zai", "us", "eu", "apac", "aws", "litellm", "ollama", "hf", "huggingface",
}
# a token that is a snapshot date, not part of the model's identity
DATE_TOKEN_RE = re.compile(r"^(?:20\d{2})(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])$")   # 20240513
YEARMONTH_RE = re.compile(r"^(?:20\d{2})(?:0[1-9]|1[0-2])$")                            # 202405
# A separated date has to be removed BEFORE the string is split into tokens, otherwise
# `gpt-4o-2024-05-13` tokenises as [gpt, 4o, 2024, 05, 13] and the version-joining step turns
# the date into a version. Matches 2024-05-13, 2024_05_13, 2024/05/13 and 2024-05.
SEPARATED_DATE_RE = re.compile(
    r"(?<!\d)20\d{2}[-_/. ](?:0[1-9]|1[0-2])(?:[-_/. ](?:0[1-9]|[12]\d|3[01]))?(?!\d)")
# Yearless snapshot suffixes: `gemini-2.5-pro-preview-05-06`, `gpt-4.1-04-14`. Both halves must
# be zero-padded two-digit month/day, which is what protects generation numbers: vendors write
# `claude-sonnet-4-6`, never `claude-sonnet-04-06`, so 4.6 survives and 05-06 does not.
TRAILING_MMDD_RE = re.compile(r"[-_/. ](?:0[1-9]|1[0-2])[-_/. ](?:0[1-9]|[12]\d|3[01])$")
# OpenAI's legacy MMDD snapshots: gpt-4-0613, gpt-3.5-turbo-1106. Judgement call: a bare
# 4-digit token that reads as a month/day is a snapshot, so it is dropped. The cost if we are
# wrong is collapsing two versions that a vendor numbered oddly; the cost of keeping it is
# splitting every legacy OpenAI snapshot into its own key.
MMDD_RE = re.compile(r"^(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])$")
DROP_MODEL_TOKENS = {"latest", "snapshot", "stable", "current", "default", "model", "api"}

# post-normalisation spelling -> canonical base model. Keys are what `_normalise_model_string`
# produces, so every surface spelling that normalises the same way is collapsed for free; this
# table only has to fix the cases where a vendor RENAMED a model (Anthropic moved the family
# name before the version between 3.x and 4.x) or where a community short form is unambiguous.
MODEL_ALIASES: dict[str, str] = {
    # Anthropic: canonical form is the current vendor order, claude-<family>-<version>
    "claude-3-sonnet": "claude-sonnet-3", "claude-3-opus": "claude-opus-3",
    "claude-3-haiku": "claude-haiku-3",
    "claude-3.5-sonnet": "claude-sonnet-3.5", "claude-3.5-haiku": "claude-haiku-3.5",
    "claude-3.5-sonnet-v2": "claude-sonnet-3.5-v2",
    "claude-3.7-sonnet": "claude-sonnet-3.7",
    "claude-4-sonnet": "claude-sonnet-4", "claude-4-opus": "claude-opus-4",
    "claude-4.1-opus": "claude-opus-4.1", "claude-4.5-sonnet": "claude-sonnet-4.5",
    "claude-4.5-haiku": "claude-haiku-4.5", "claude-4.5-opus": "claude-opus-4.5",
    "claude-4.6-sonnet": "claude-sonnet-4.6",
    "sonnet-3.5": "claude-sonnet-3.5", "sonnet-3.7": "claude-sonnet-3.7",
    "sonnet-4": "claude-sonnet-4", "sonnet-4.5": "claude-sonnet-4.5",
    "sonnet-4.6": "claude-sonnet-4.6", "sonnet-5": "claude-sonnet-5",
    "opus-4": "claude-opus-4", "opus-4.1": "claude-opus-4.1", "opus-4.5": "claude-opus-4.5",
    "opus-5": "claude-opus-5", "haiku-4.5": "claude-haiku-4.5",
    # OpenAI
    "gpt4o": "gpt-4o", "gpt-4-o": "gpt-4o", "gpt-4omni": "gpt-4o",
    "gpt4omini": "gpt-4o-mini", "gpt-4o-mini": "gpt-4o-mini",
    "gpt4": "gpt-4", "gpt-4-turbo-preview": "gpt-4-turbo-preview",
    "gpt3.5-turbo": "gpt-3.5-turbo", "gpt-35-turbo": "gpt-3.5-turbo",
    "gpt4.1": "gpt-4.1", "gpt5": "gpt-5", "gpt5.1": "gpt-5.1", "gpt5-codex": "gpt-5-codex",
    "o1-mini": "o1-mini", "o3-mini": "o3-mini", "o4-mini": "o4-mini",
    # Google
    "gemini-1.5-pro": "gemini-1.5-pro", "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-2.5-pro": "gemini-2.5-pro", "gemini-3-pro": "gemini-3-pro",
    "gemini-3.0-pro": "gemini-3-pro",
    # open weights
    "llama-3.1-405b-instruct": "llama-3.1-405b-instruct",
    "llama3.1-405b-instruct": "llama-3.1-405b-instruct",
    "qwen2.5-72b-instruct": "qwen-2.5-72b-instruct",
    "qwen-2.5-coder-32b-instruct": "qwen-2.5-coder-32b-instruct",
    "deepseek-v3": "deepseek-v3", "deepseek-r1": "deepseek-r1",
    "deepseek-chat": "deepseek-v3",   # the API alias pointed at V3
}


def _normalise_model_string(raw: str) -> str:
    s = raw.strip().lower()
    # "GPT-4o (2024-05-13)" / "Claude 3.5 Sonnet (new)": keep parenthetical only if it is not a
    # snapshot marker, because "(new)" and "(v2)" did distinguish real checkpoints.
    def _paren(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        flat = re.sub(r"[^a-z0-9]+", "", inner)
        if DATE_TOKEN_RE.match(flat) or YEARMONTH_RE.match(flat) or flat in DROP_MODEL_TOKENS:
            return " "
        return "-" + inner
    s = re.sub(r"\((.*?)\)", _paren, s)
    s = re.sub(r"[:\s]*v\d+:\d+$", "", s)            # bedrock "...-v1:0"
    s = SEPARATED_DATE_RE.sub(" ", s)                # gpt-4o-2024-05-13 -> gpt-4o
    s = TRAILING_MMDD_RE.sub("", s.rstrip("-_ "))    # gemini-2.5-pro-preview-05-06 -> ...preview
    s = s.replace("‑", "-").replace("–", "-").replace("_", "-")
    # vendor route: "openai/gpt-4o", "us.anthropic.claude-sonnet-4-20250514"
    for sep in ("/", "."):
        if sep in s:
            head, _, tail = s.partition(sep)
            while re.sub(r"[^a-z0-9]+", "", head) in VENDOR_PREFIXES and tail:
                s = tail
                head, _, tail = s.partition(sep)
            if sep == ".":
                break
    s = re.sub(r"[^a-z0-9.+]+", "-", s)
    tokens = [t for t in s.split("-") if t]
    kept: list[str] = []
    for t in tokens:
        flat = t.replace(".", "")
        if DATE_TOKEN_RE.match(flat) or YEARMONTH_RE.match(flat) or MMDD_RE.match(flat):
            continue
        if t in DROP_MODEL_TOKENS:
            continue
        kept.append(t)
    # join runs of bare digits into a dotted version: claude-3-5-sonnet -> claude-3.5-sonnet,
    # claude-sonnet-4-6 -> claude-sonnet-4.6. "4o" and "72b" are not bare digits and survive.
    out: list[str] = []
    for t in kept:
        if t.isdigit() and out and re.fullmatch(r"[0-9.]+", out[-1]):
            out[-1] = out[-1] + "." + t
        else:
            out.append(t)
    return "-".join(out)


def canon_model(raw: str | None) -> tuple[str | None, str | None]:
    """Return (canonical base model, reason). Reason is None when the model resolved."""
    s = (raw or "").strip()
    if not s:
        return None, "model_missing"
    if s.lower() in MODEL_UNIDENTIFIABLE:
        return None, "model_unidentifiable"
    if MODEL_MULTI_RE.search(s):
        return None, "model_unidentifiable"
    # A residual slash after the vendor route is stripped means two models in one cell
    # ("gpt-4o/claude-sonnet-4"): the model is not held fixed, so the row cannot be keyed.
    parts = [p for p in s.lower().split("/") if p.strip()]
    while len(parts) > 1 and _fold(parts[0]) in VENDOR_PREFIXES:
        parts.pop(0)
    if len(parts) > 1 and any(MODEL_FAMILY_RE.match(p.strip()) for p in parts[1:]):
        return None, "model_unidentifiable"
    normalised = _normalise_model_string(s)
    if not normalised or not re.search(r"[a-z]", normalised):
        return None, "model_unidentifiable"
    if normalised in MODEL_UNIDENTIFIABLE:
        return None, "model_unidentifiable"
    return MODEL_ALIASES.get(normalised, normalised), None


# --------------------------------------------------------------------------------------
# benchmark / split resolution
# --------------------------------------------------------------------------------------
def canon_benchmark(raw: str | None) -> tuple[str | None, str | None]:
    """Return (canonical benchmark family, split implied by a qualified name or None)."""
    key = _fold(raw or "")
    if not key:
        return None, None
    if key in QUALIFIED_BENCHMARKS:
        return QUALIFIED_BENCHMARKS[key]
    return BENCHMARK_ALIASES.get(key), None


def canon_split(benchmark: str | None, raw: str | None) -> str | None:
    """Canonical split within `benchmark`, or None if the string is not in its vocabulary."""
    key = _fold(raw or "")
    if not key:
        return None
    table = SPLIT_ALIASES.get(benchmark or "")
    if table is not None:
        return table.get(key)
    return GENERIC_SPLITS.get(key)


def canon_metric(benchmark: str | None, raw: str | None) -> str | None:
    """Measurement token for `raw` on `benchmark`, or None if unrecognised there."""
    folded = _fold_metric(raw or "")
    override = METRIC_ALIASES_BY_BENCHMARK.get(benchmark or "", {})
    if folded in override:
        return override[folded]
    return METRIC_ALIASES.get(folded)


def parse_score(raw: str | None) -> tuple[float | None, str | None]:
    s = (raw or "").strip().rstrip("%").strip()
    if not s:
        return None, "score_missing"
    try:
        v = float(s)
    except ValueError:
        return None, "score_not_numeric"
    if not math.isfinite(v):
        return None, "score_not_numeric"
    return v, None


# --------------------------------------------------------------------------------------
# per-row decision
# --------------------------------------------------------------------------------------
def evaluate_row(row: dict[str, str]) -> tuple[str, list[str]]:
    """Return (comparable_key, reasons). An empty key always comes with >= 1 reason."""
    reasons: list[str] = []

    if not (row.get("system_id") or "").strip():
        reasons.append("system_id_missing")

    model, model_reason = canon_model(row.get("model"))
    if model_reason:
        reasons.append(model_reason)

    raw_benchmark = (row.get("benchmark") or "").strip()
    raw_split = (row.get("split") or "").strip()
    if _fold(raw_benchmark) in BOARD_FAMILIES:
        raw_benchmark, raw_split = raw_split, ""   # the split column named the benchmark
    benchmark, implied_split = canon_benchmark(raw_benchmark)
    if benchmark is None:
        reasons.append("benchmark_unrecognised")

    split = canon_split(benchmark, raw_split) if benchmark else None
    if implied_split is not None:
        if split is None and not raw_split:
            split = implied_split            # the qualifier carried the split
        elif split is None:
            reasons.append("split_unrecognised")
        elif split in VACUOUS_SPLITS:
            # "SWE-bench Verified" with split "test" is the HuggingFace split name of the
            # Verified set, not a claim that this is the 2,294-instance full set. A split column
            # that only says "the whole thing" defers to the qualifier; a split column that
            # names a DIFFERENT variant (Verified vs Lite) is a real contradiction.
            split = implied_split
        elif split != implied_split:
            reasons.append("benchmark_split_conflict")
    elif benchmark is not None:
        if not raw_split:
            reasons.append("split_missing")
        elif split is None:
            other, _ = canon_benchmark(raw_split)
            if other is not None and other != benchmark:
                # e.g. the WebArena board family carries VisualWebArena rows with the benchmark
                # in the split. That is a mis-filed row, not an exotic split; naming it as a
                # conflict tells the extractor which of the two columns to fix.
                reasons.append("benchmark_split_conflict")
            else:
                reasons.append("split_unrecognised")

    raw_metric = (row.get("metric") or "").strip()
    if benchmark is not None:
        if not raw_metric:
            reasons.append("metric_missing")
        else:
            token = canon_metric(benchmark, raw_metric)
            if token is None or token != STANDARD_METRIC.get(benchmark):
                reasons.append("metric_nonstandard")

    _, score_reason = parse_score(row.get("score"))
    if score_reason:
        reasons.append(score_reason)

    reasons.sort(key=REASONS.index)
    if reasons:
        return "", reasons
    return f"{benchmark}|{split}|{model}", []


def set_note(row: dict[str, str], reasons: list[str]) -> None:
    """Write (or clear) this script's `[not-comparable: ...]` marker, preserving other notes."""
    base = NOTE_RE.sub("", row.get("notes") or "").strip()
    if reasons:
        marker = "[not-comparable: " + "; ".join(reasons) + "]"
        row["notes"] = f"{base} {marker}".strip()
    else:
        row["notes"] = base


# --------------------------------------------------------------------------------------
# whole-file pass
# --------------------------------------------------------------------------------------
def mark_rows(rows: list[dict[str, str]], min_systems: int = 1) -> dict:
    """Fill comparable_key and notes in place; return the summary dict."""
    primary: Counter[str] = Counter()
    all_reasons: Counter[str] = Counter()
    decided: list[list[str]] = []

    for row in rows:
        key, reasons = evaluate_row(row)
        row["comparable_key"] = key
        decided.append(reasons)
        if reasons:
            primary[reasons[0]] += 1
            for r in reasons:
                all_reasons[r] += 1

    # key -> distinct systems / row count, computed BEFORE any --min-systems pruning so the
    # distribution reported is the diagnosis, not the result of the filter.
    systems_per_key: dict[str, set[str]] = defaultdict(set)
    rows_per_key: Counter[str] = Counter()
    for row in rows:
        k = row["comparable_key"]
        if k:
            rows_per_key[k] += 1
            systems_per_key[k].add((row.get("system_id") or "").strip())

    dist = {"1": 0, "2": 0, "3+": 0}
    for k, sids in systems_per_key.items():
        n = len(sids)
        dist["1" if n == 1 else "2" if n == 2 else "3+"] += 1
    rows_in_multi = sum(n for k, n in rows_per_key.items() if len(systems_per_key[k]) >= 2)

    dropped_keys: list[str] = []
    if min_systems > 1:
        dropped_keys = sorted(k for k, s in systems_per_key.items() if len(s) < min_systems)
        drop = set(dropped_keys)
        for row, reasons in zip(rows, decided):
            if row["comparable_key"] in drop:
                row["comparable_key"] = ""
                reasons.append("singleton_key")
                primary["singleton_key"] += 1
                all_reasons["singleton_key"] += 1

    for row, reasons in zip(rows, decided):
        set_note(row, reasons)

    kept = {k for k, s in systems_per_key.items() if len(s) >= min_systems}
    surviving: dict[str, dict[str, int]] = {}
    for k in sorted(kept):
        bench = k.split("|", 1)[0]
        e = surviving.setdefault(bench, {"keys": 0, "rows": 0, "multi_system_keys": 0})
        e["keys"] += 1
        e["rows"] += rows_per_key[k]
        if len(systems_per_key[k]) >= 2:
            e["multi_system_keys"] += 1

    largest = sorted(systems_per_key.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:15]
    rows_keyed = sum(1 for r in rows if r["comparable_key"])
    return {
        "generated": datetime.now(tz=UTC).date().isoformat(),
        "min_systems": min_systems,
        "rows_in": len(rows),
        "rows_keyed": rows_keyed,
        "rows_blank": len(rows) - rows_keyed,
        "blanked_by_primary_reason": {r: primary[r] for r in REASONS if primary[r]},
        "blanked_reason_occurrences": {r: all_reasons[r] for r in REASONS if all_reasons[r]},
        "keys_total": len(systems_per_key),
        "key_system_distribution": dist,
        "rows_in_keys_with_2plus_systems": rows_in_multi,
        "keys_dropped_by_min_systems": len(dropped_keys),
        "benchmarks_surviving": surviving,
        "largest_keys": [{"key": k, "systems": len(s), "rows": rows_per_key[k]}
                         for k, s in largest],
    }


def read_results(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        if header != RESULT_COLUMNS:
            missing = [c for c in RESULT_COLUMNS if c not in header]
            extra = [c for c in header if c not in RESULT_COLUMNS]
            raise SystemExit(
                f"{path}: header does not match scripts/validate.py RESULT_COLUMNS\n"
                f"  missing: {missing}\n  unexpected: {extra}\n  got: {header}")
        return [{c: (r.get(c) or "") for c in RESULT_COLUMNS} for r in reader]


def write_results(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def format_summary(s: dict) -> str:
    lines = [
        f"rows in                     {s['rows_in']}",
        f"rows keyed                  {s['rows_keyed']}",
        f"rows blank                  {s['rows_blank']}",
        "",
        "blanked by primary reason:",
    ]
    for reason, n in s["blanked_by_primary_reason"].items():
        lines.append(f"  {reason:<26} {n}")
    if not s["blanked_by_primary_reason"]:
        lines.append("  (none)")
    d = s["key_system_distribution"]
    lines += [
        "",
        f"keys                        {s['keys_total']}",
        f"  with 1 distinct system    {d['1']}   (no comparison possible)",
        f"  with 2 distinct systems   {d['2']}",
        f"  with 3+ distinct systems  {d['3+']}",
        f"rows in keys with 2+        {s['rows_in_keys_with_2plus_systems']}",
    ]
    if s["min_systems"] > 1:
        lines.append(f"keys dropped (--min-systems {s['min_systems']}) "
                     f"{s['keys_dropped_by_min_systems']}")
    lines.append("")
    lines.append("benchmarks surviving:")
    for bench, e in s["benchmarks_surviving"].items():
        lines.append(f"  {bench:<26} keys={e['keys']} rows={e['rows']} "
                     f"multi_system_keys={e['multi_system_keys']}")
    if not s["benchmarks_surviving"]:
        lines.append("  (none)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--in", dest="in_path", type=Path, default=RESULTS,
                   help="results.csv, or any file with the same columns")
    p.add_argument("--out", dest="out_path", type=Path, default=None,
                   help="output file (default: in place, keeping a .bak)")
    p.add_argument("--summary", type=Path, default=SUMMARY)
    p.add_argument("--min-systems", type=int, default=1,
                   help="blank keys shared by fewer than N distinct systems (default 1: off)")
    p.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = p.parse_args(argv)

    if not args.in_path.exists():
        raise SystemExit(f"missing input: {args.in_path}")
    if args.min_systems < 1:
        raise SystemExit("--min-systems must be >= 1")

    rows = read_results(args.in_path)
    summary = mark_rows(rows, min_systems=args.min_systems)
    summary["input"] = str(args.in_path)

    print(format_summary(summary))
    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    out = args.out_path or args.in_path
    if out == args.in_path:
        shutil.copyfile(args.in_path, args.in_path.with_suffix(args.in_path.suffix + ".bak"))
    write_results(out, rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out} and {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
