#!/usr/bin/env python
"""Within-paper comparison blocks: RQ3 without a cross-paper key (Phase 7, task 49b).

WHY THIS EXISTS BESIDE ``scripts/analyse_outcomes.py``
-----------------------------------------------------
``analyse_outcomes.py`` compares systems ACROSS papers on ``comparable_key`` =
benchmark|split|base-model. It reaches 36 keys / 53 systems / ~106-143 observations
(``data/comparable_summary.json``) and carries a confound it cannot remove: a leaderboard row does
not say which commit produced its number (``docs/benchmark_caveats.md`` sec. 5, scaffold drift), and
two rows in one key were produced by two teams at two times under two harness configurations.

This script uses a different unit: the BLOCK, one paper x benchmark x split x metric x model. A
paper's own baseline table is a controlled comparison - one team, one protocol, one benchmark,
usually one model, run at one time. ``data/results_rejects.csv`` holds the rows the extractor
refused as ``not_own_system``, i.e. exactly those baseline-table rows: the score a paper reported
for somebody else's system, with ``system_id`` (the reporting paper's own coded system),
``record_id`` (the paper), ``reported_system_name``, benchmark, split, metric, model, a verbatim
quote and a locator.

WHAT IT DOES, IN ORDER
----------------------
1. ``Attributor`` - attribute the rival NAMES to coded systems, conservatively. The matcher is
   ``scripts/system_registry.py`` (``norm_name``, ``key_of``, ``keys_match``, ``split_version``,
   ``repo_key``) reached through the guards already proven in
   ``scripts/leaderboards_to_results.py``: exact normalised-key match, or a single fuzzy match at
   ``--fuzzy-threshold`` (default 96, above the registry's own 92) with compatible major versions
   and agreeing digit groups, plus that script's three vetoes (over-merged census group,
   uncorroborated org prefix, divergent name variant). Three further guards are added here, because
   a paper baseline table is not a leaderboard:
     * only the LEFTMOST non-model part of a "harness + model" string may attribute - the baseline
       row "MLR-Agent o4-mini-high + Codex" names MLR-Agent, not Codex;
     * an extended stop-list of baseline-table labels ("LLM agent", "Evolved", "Solo", "Full Team",
       "ours", "vanilla", ...) - categories, not systems, and several of them collide with a real
       coded system id;
     * a row whose label marks it as an ABLATION of the reporting paper's own system is never
       attributed: the coded dimensions describe the whole system, not the variant with a part
       removed, so attributing it would attach the wrong design vector to the score.
   Every refusal is recorded with its reason and printed, grouped and counted, at the end of a run.
   An UNATTRIBUTED row is still kept as an ANONYMOUS COMPARATOR with an empty ``system_id``: it
   carries no design vector, but it does establish how hard the protocol was, so it belongs in the
   block and in the within-block standardisation.
2. ``build_arm_table`` / ``block_summary`` - the block table. One arm per (block, coded system or
   label); several rows of one arm inside one block collapse to their median, as in
   ``analyse_outcomes.py``. A block with one arm is dropped: it supports no comparison. Recorded
   per block: benchmark, arms, arms attributed to a coded system, raw spread, standardisation
   method, whether the authors' own arm is present and where it ranks.
3. ``split_ablation_blocks`` - blocks whose comparators are ALL ablations of the paper's own system
   are routed out, counted and written to their own table: they belong to
   ``scripts/analyse_ablations.py``, not here. Detection is by the comparator label and the
   extractor's own note (``ablation_label``), never silently - the routed blocks are reported.
4. ``standardise_within_block`` - scores are comparable only inside a block, so each arm gets a
   within-block standardised value. THE RULE, mirroring ``analyse_outcomes.standardise_within_key``
   so the two analyses can be read together:
     * block with >= ``--rank-threshold`` (default 4) arms: z = (x - mean) / sd, sd with ddof=1;
     * fewer: standardised average rank, (rank - (n+1)/2) / sd(1..n, ddof=1) - (-1, 0, +1) at n=3
       and (-0.7071, +0.7071) at n=2; mean 0 and sd 1 like z, but claiming only an ordering;
     * every score in the block identical: all 0.0, method ``degenerate``.
   Two standardisations are computed, because the headline must not depend on the authors' arm:
   ``z_comparator`` over the comparator arms only and ``z_all`` over every arm including the
   paper's own. Lower-is-better metrics are negated first (``metric_direction``); a block whose
   metric is blank, and a block mixing a 0-1 with a 0-100 scale, keeps its arms in the table but is
   excluded from estimation and counted.
5. ``CONTRASTS`` / ``estimate_contrast`` - a small pre-specified set of binary design contrasts with
   the PAPER as the blocking factor. For each: the within-block difference in standardised score
   between arms differing on that dimension, a percentile bootstrap resampling BLOCKS (not rows and
   not arms), a within-block permutation test with its DESIGN FLOOR (the smallest p the label
   structure can reach), and a minimum detectable effect at 80% power computed from the observed
   between-block spread. A contrast varying in fewer than ``--min-blocks`` (default 3) blocks is NOT
   ESTIMABLE and says so. Because one paper can contribute several blocks, a second bootstrap
   resampling PAPERS is reported beside the block one.

THE CONFOUND THAT MATTERS HERE - AND IT IS NOT SCAFFOLD DRIFT
------------------------------------------------------------
In a paper's own baseline table the authors' system is the one they tuned; the comparators are
usually run at default settings by people who did not build them, sometimes re-implemented, and the
table exists to show the authors' system winning. "The paper's own system wins" is therefore close
to tautological, and a contrast that separates the authors' arm from the comparator arms measures
that practice, not the design feature. So, by construction:
  (a) the HEADLINE contrast EXCLUDES the authors' own arm and compares comparator arms with each
      other (``include_own=False``, standardised on ``z_comparator``);
  (b) the version INCLUDING the authors' arm is reported separately and labelled OPTIMISTICALLY
      BIASED (``include_own=True``, standardised on ``z_all``);
  (c) how often the authors' arm ranks first is counted and reported as a result in its own right -
      it measures the reporting practice, not the designs;
  (d) when a contrast reaches significance only with the authors' arm included, the finding line
      says exactly that.
Scaffold drift has not gone away: the rival was run by the reporting paper at some commit while
HARNESS-DB codes it at a pinned commit, which may be a different one. The block removes the
cross-paper protocol difference, not the coded-commit mismatch. Both caveats travel with every
figure and every table.

Outputs: tables to ``data/analysis/``, figures (SVG + PDF) to ``paper/figures/``, house style as
``scripts/prisma_diagram.py``. Nothing is written under ``data/coded/``, ``data/screening/`` or
``data/fulltext/``.

No model calls. No network. pandas / numpy / scipy / statsmodels / matplotlib(Agg) only.

Run: python scripts/analyse_blocks.py
     python scripts/analyse_blocks.py --no-render          (numbers only, no figures)
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The matcher and its proven guards, and the estimator conventions of the cross-paper analysis.
# Imported, never re-implemented: a private copy of a matcher is how two scripts in one repository
# come to disagree about which system a name means.
import leaderboards_to_results as LB

# The exact Poisson-binomial DP lives in `analyse_ablation_coverage`; it is imported rather than
# copied so the own-arm tail computed here and the one recomputed there cannot drift apart.
from analyse_ablation_coverage import poisson_binomial_tail
from analyse_outcomes import (
    LARGE_EFFECT,
    _key_difference_options,
    coded_values,
    mde_from_key_differences,
)
from system_registry import key_of, norm_name

REJECTS = ROOT / "data" / "results_rejects.csv"
ALIASES = ROOT / "data" / "comparator_aliases.csv"
RESULTS = ROOT / "data" / "results.csv"
EVIDENCE = ROOT / "data" / "results_evidence.csv"
SYSTEMS = ROOT / "data" / "systems.json"
CANDIDATES = ROOT / "data" / "systems_candidates.csv"
FIG_DIR = ROOT / "paper" / "figures"
TAB_DIR = ROOT / "data" / "analysis"

FRAGILE_BLOCKS = 5  # below this many blocks an interval is descriptive, not inferential

OWN_ARM_CAVEAT = (
    "OWN-ARM BIAS, the confound that dominates this design: in a paper's own baseline table the "
    "authors' system is the one they tuned, while the comparators are usually run at default "
    "settings by people who did not build them, and the table exists to show the authors' system "
    "winning. 'The paper's own system wins' is therefore close to tautological. The headline "
    "estimates here EXCLUDE the authors' own arm and compare comparator arms with each other; the "
    "version including that arm is reported separately and is OPTIMISTICALLY BIASED."
)
OWN_ARM_CHANCE_CAVEAT = (
    "OWN-ARM CHANCE BASELINE, corrected: a block's chance probability is 1 / (arms that are not the "
    "reporting paper's own switched-off configurations), i.e. 1 / max(n_arms - n_ablation_arms, 1), "
    "not 1 / n_arms. An ablation arm is the paper's own system with a part removed, not an "
    "independently chosen rival: a full system beating its own ablation is the PREMISE of the "
    "ablation analysis, so counting those arms as rivals inflates the own-arm result. The uncorrected "
    "1 / n_arms figures are kept beside the corrected ones, labelled, so the correction is auditable. "
    "The exact Poisson-binomial tail also treats the blocks as independent Bernoullis, which they are "
    "not - they are pseudo-replicated within paper - so a PAPER-CLUSTERED Monte-Carlo p (one null draw "
    "per paper, applied to all that paper's blocks) and a one-block-per-paper exact p are reported "
    "beside it."
)
DRIFT_CAVEAT = (
    "Scaffold drift (docs/benchmark_caveats.md sec. 5) is reduced but not removed: the block holds "
    "one team, one protocol, one benchmark, one split, one metric and one model fixed, so the "
    "cross-paper protocol difference is gone, but the rival was run by the reporting paper at some "
    "commit while HARNESS-DB codes it at a pinned commit, which may be a different one. That is "
    "measurement error on the design variable; it attenuates towards zero, so every effect is a "
    "LOWER BOUND on magnitude. Reporting is also self-selected (sec. 3): which rivals appear in a "
    "table is the authors' choice. Associational only; no causal reading is supported."
)


# --------------------------------------------------------------------------------------------
# normalisation, block keys, metric direction
# --------------------------------------------------------------------------------------------
def norm_cell(text: object) -> str:
    """Whitespace- and case-folded cell, used for every component of a block key."""
    return re.sub(r"\s+", " ", str(text if text is not None else "")).strip().lower()


def block_key(record_id: str, benchmark: str, split: str, metric: str, model: str) -> str:
    """The exact block key: one paper x benchmark x split x metric x model.

    Every component is folded with `norm_cell` and nothing else: no benchmark canonicalisation, no
    split aliasing, no model canonicalisation. Inside one paper's table the strings come from one
    extraction of one document, so folding case and whitespace is enough, and further normalisation
    would pool columns the paper itself kept apart.
    """
    return "|".join(norm_cell(x) for x in (record_id, benchmark, split, metric, model))


# Metric direction. Almost every metric in this corpus is higher-is-better; these are the ones that
# are not, plus a handful of look-alikes that are. The overrides are checked FIRST because they
# contain the losing substrings ("Throughput (steps/h)" contains "steps", "Final Net Worth (USD)"
# contains "usd", and "Err. Fixed" counts errors repaired, which goes up when the system is better).
_HIGHER_OVERRIDE_RE = re.compile(
    r"throughput|per\s*second|per\s*hour|steps?\s*/\s*h|net\s*worth|rank\s*ic|"
    r"err(?:or)?s?\.?\s*(?:fixed|identified|found|detected|caught|repaired)|"
    r"bugs?\s*(?:fixed|found|detected)|savings?|speed\s*-?\s*up",
    re.IGNORECASE,
)
_LOWER_RE = re.compile(
    r"\berr\b|\berr\.|error|loss|\bcost|\busd\b|dollar|\bprice|latency|wall\s*time|\btime\b|"
    r"seconds|\bsecs?\b|minutes|duration|\bsteps\b|\bturns\b|tokens|\bcalls\b|\brank\b|regret|"
    r"violation|halluc|\bfail|rmse|\bmae\b|\bmse\b|\bwer\b|\bece\b|perplex|\bppl\b|overhead|"
    r"penalty",
    re.IGNORECASE,
)


def metric_direction(metric: str) -> str:
    """"higher", "lower" or "unknown" for one metric string.

    "unknown" is returned for a blank metric and is not a synonym for "higher": a block whose metric
    is blank is a table column whose measurement nobody recorded, so which end is good is not known,
    and such a block is excluded from estimation rather than assumed.
    """
    text = norm_cell(metric)
    if not text:
        return "unknown"
    if _HIGHER_OVERRIDE_RE.search(text):
        return "higher"
    if _LOWER_RE.search(text):
        return "lower"
    return "higher"


# --------------------------------------------------------------------------------------------
# ablation labels
# --------------------------------------------------------------------------------------------
# Patterns that mark a comparator row as a variant of the REPORTING paper's own system rather than a
# rival. Two tiers, because the two fields differ in reliability:
#   * STRONG patterns are trusted in the extractor's own `note` as well as in the label - "ablation"
#     is a word the extractor wrote deliberately and "w/o X" is never a rival's name;
#   * LABEL patterns are trusted only in `reported_system_name`, because in a note they catch
#     sentences about the run ("Only 3 attempted instances") rather than about the arm.
_ABLATION_STRONG: tuple[tuple[str, str], ...] = (
    ("note_ablation", r"\bablat"),
    ("without", r"\bw/\s?o\b|\bwithout\b"),
    ("variant_of", r"\bvariant of\b|\bours\b\s*(?:w/|with|minus)"),
)
_ABLATION_LABEL: tuple[tuple[str, str], ...] = (
    ("only_variant", r"\bonly\b"),
    ("leading_minus", r"^\s*[-−]\s*\w"),
    ("no_component", (r"^no[\s-]\w|\bno\s+(?:\w+\s+)?(?:module|agent|memory|feedback|planner|"
                      r"verifier|retry|plan|tool|context|critic|reflection)\b")),
    ("ours_marker", r"\bours\b"),
)


def ablation_label(name: str, note: str = "") -> str:
    """Name of the pattern marking this comparator as an ablation, or "" when none fires.

    The pattern name travels into the arm table, so every routed-out block can be audited against
    the label that routed it. An ablation arm keeps its place in the block (it is a real score at
    the same protocol) but is never attributed to a coded system: the coding describes the whole
    system, not the system with a part removed.
    """
    label = norm_cell(name)
    both = f"{label} || {norm_cell(note)}"
    for tag, pattern in _ABLATION_STRONG:
        if re.search(pattern, both, re.IGNORECASE):
            return tag
    for tag, pattern in _ABLATION_LABEL:
        if re.search(pattern, label, re.IGNORECASE):
            return tag
    return ""


# --------------------------------------------------------------------------------------------
# attribution
# --------------------------------------------------------------------------------------------
# Labels a baseline table uses for a category, a configuration or the paper's own system. Several
# collide with a real coded system id, which is why they have to be refused by name: key_of("LLM
# agent") is "llmagent" and a coded system carries that id.
EXTRA_STOP_KEYS = frozenset({
    "after", "agentteam", "base", "baseagent", "baseline", "before", "best", "ceiling",
    "chainofthought", "cot", "directprompting", "evolved", "expert", "fewshot", "full",
    "fullmodel", "fullsystem", "group", "human", "harness", "llmagent", "llmagents", "lowerbound",
    "method", "multiagent", "naive", "ours", "oursfull", "plain", "prompting", "proposed",
    "reactive", "reference", "simple", "singleagent", "solo", "standard", "team", "upperbound",
    "vanilla", "variant", "withtools", "withouttools",
})


@dataclass(frozen=True)
class Attribution:
    """The outcome of trying to name one comparator label as a coded system."""

    system_id: str = ""
    method: str = ""  # exact-key, fuzzy-<threshold>, or the kind of refusal
    matched_on: str = ""
    reason: str = ""
    census_hint: str = ""

    @property
    def attributed(self) -> bool:
        return bool(self.system_id)


def candidate_names(label: str) -> list[LB.Cand]:
    """Ordered harness-name candidates for one baseline-table label, most literal first.

    Built from `leaderboards_to_results`' own helpers so the reductions are the proven ones, with
    one difference that matters for paper tables: of a "harness + model" / "harness w/ model" split
    only the LEFTMOST non-model part may attribute. On a leaderboard either side can hold the
    harness; in a paper's baseline table the row names a harness first and its backbone second
    ("MLR-Agent o4-mini-high + Codex" is MLR-Agent's row, not Codex's), and letting the right-hand
    side attribute turned that row into a score for `codex`.
    """
    cands: list[LB.Cand] = []
    literal = LB._clean(label)
    if not literal:
        return []
    LB._add(cands, literal, "reported_system_name")
    stripped = LB.TRAILING_BRACKET_RE.sub("", literal).strip()
    LB._add(cands, stripped, "label minus trailing bracket")
    no_parens = LB.TRAILING_PARENS_RE.sub("", stripped).strip()
    LB._add(cands, no_parens, "label minus parenthetical")
    for source, provenance in (
        (literal, "label minus model"),
        (no_parens, "label minus parenthetical and model"),
    ):
        parts = LB.split_model_off(source)
        if parts:
            LB._add(cands, parts[0], provenance)  # leftmost non-model part only
    for cand in tuple(cands):  # snapshot: the loop appends to `cands`
        text = norm_name(cand.text)
        for prefix in LB.ORG_PREFIXES:
            if text.startswith(prefix + " ") and len(text) > len(prefix) + 1:
                LB._add(cands, text[len(prefix) + 1:].strip(),
                        f"{cand.provenance} minus org prefix {prefix!r}", org=prefix)
        if LB.PARAM_SIZE_RE.search(text):
            LB._add(cands, LB.PARAM_SIZE_RE.sub("", text),
                    f"{cand.provenance} minus parameter count", org=cand.org)
    return [c for c in cands if key_of(c.text) not in EXTRA_STOP_KEYS]


class Attributor:
    """Attribute comparator labels to coded systems, abstaining by default.

    A missing attribution costs one arm its design vector; a wrong one attaches another system's
    design vector to a score, which is silently fatal to every contrast. So: abstain, record the
    reason, print the vetoes.
    """

    def __init__(self, registry=None, threshold: int = LB.FUZZY_THRESHOLD,
                 systems_path: Path = SYSTEMS, candidates_path: Path = CANDIDATES) -> None:
        self.registry = registry if registry is not None else LB.load_registry(
            systems_path, candidates_path
        )
        self.threshold = int(threshold)
        self._cache: dict[tuple[str, str], Attribution] = {}
        self.vetoes: collections.Counter = collections.Counter()
        self.abstentions: collections.Counter = collections.Counter()
        self.census_hints: collections.Counter = collections.Counter()

    def attribute(self, label: str, note: str = "") -> Attribution:
        """One label -> an Attribution. An ablation label is refused before the matcher runs."""
        cache_key = (str(label), str(note))
        if cache_key in self._cache:
            return self._cache[cache_key]
        ablation = ablation_label(label, note)
        if ablation:
            out = Attribution(
                method="refused-ablation",
                reason=(f"{label!r} is a variant of the reporting paper's own system "
                        f"({ablation}); the coding describes the whole system, not the ablated "
                        "variant, so no coded system may be attached to this score"),
            )
        else:
            cands = candidate_names(label)
            if not cands:
                out = Attribution(
                    method="abstain-no-candidate",
                    reason=(f"{label!r} reduces to no usable harness name (category label, "
                            "placeholder or model name only)"),
                )
            else:
                match = LB.match_system(self.registry, cands, threshold=self.threshold)
                out = Attribution(
                    system_id=match.system_id,
                    method=match.method or "abstain-no-match",
                    matched_on=match.matched_on,
                    reason=match.reason,
                    census_hint=match.census_hint,
                )
        if not out.attributed:
            if out.method.startswith("vetoed") or out.method.startswith("ambiguous"):
                self.vetoes[f"{out.method} :: {out.reason}"] += 1
            else:
                self.abstentions[out.method] += 1
        if out.census_hint:
            self.census_hints[out.census_hint] += 1
        self._cache[cache_key] = out
        return out

    def table(self) -> pd.DataFrame:
        """Every label seen, what it became and why - the audit trail of the attribution step."""
        rows = [
            {
                "reported_system_name": label,
                "note": note,
                "system_id": a.system_id,
                "method": a.method,
                "matched_on": a.matched_on,
                "reason": a.reason,
                "census_hint": a.census_hint,
            }
            for (label, note), a in sorted(self._cache.items())
        ]
        return pd.DataFrame(rows, columns=["reported_system_name", "note", "system_id", "method",
                                           "matched_on", "reason", "census_hint"])


# --------------------------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------------------------
def load_comparators(path: Path = REJECTS) -> pd.DataFrame:
    """The comparator rows: `data/results_rejects.csv` where reason == not_own_system.

    Those are the rows the extractor refused because the score belongs to a rival, which is exactly
    what a baseline table is. A row without a numeric score is dropped (there is nothing to compare).
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in ("reason", "system_id", "record_id", "reported_system_name", "benchmark", "split",
                "metric", "score", "model", "note"):
        if col not in df.columns:
            raise SystemExit(f"{path}: missing column {col!r}")
    out = df[df["reason"] == "not_own_system"].copy()
    out["score_num"] = pd.to_numeric(out["score"], errors="coerce")
    return out[out["score_num"].notna()].reset_index(drop=True)


def load_own_arms(results: Path = RESULTS, evidence: Path = EVIDENCE) -> pd.DataFrame:
    """The reporting papers' own rows: `data/results.csv` with `source=paper` in `notes`.

    `results.csv` carries no `record_id`, only `row_id=<id>` inside `notes`; the paper that a row
    came from is recovered by joining that id on `data/results_evidence.csv`, which is the same
    extraction with its provenance columns still attached. A row whose paper cannot be recovered
    cannot be placed in a block and is dropped (counted in the run report).
    """
    df = pd.read_csv(results, dtype=str, keep_default_na=False)
    for col in ("system_id", "benchmark", "split", "metric", "score", "model", "notes"):
        if col not in df.columns:
            raise SystemExit(f"{results}: missing column {col!r}")
    own = df[df["notes"].str.startswith("source=paper")].copy()
    own["row_id"] = own["notes"].str.extract(r"row_id=([^;\s]+)")[0].fillna("")
    ev = pd.read_csv(evidence, dtype=str, keep_default_na=False)
    mapping = dict(zip(ev["row_id"], ev["record_id"]))
    own["record_id"] = own["row_id"].map(mapping).fillna("")
    own["score_num"] = pd.to_numeric(own["score"], errors="coerce")
    own["note"] = ""
    own["reported_system_name"] = "(the paper's own system)"
    kept = own[(own["record_id"] != "") & own["score_num"].notna()].copy()
    kept.attrs["dropped_no_record"] = int((own["record_id"] == "").sum())
    kept.attrs["dropped_no_score"] = int(own["score_num"].isna().sum())
    return kept.reset_index(drop=True)


def load_codings(path: Path = SYSTEMS) -> dict[str, dict]:
    """system_id -> its `coding` dict, from data/systems.json."""
    systems = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"]: (s.get("coding") or {}) for s in systems}


# --------------------------------------------------------------------------------------------
# the arm table
# --------------------------------------------------------------------------------------------
ARM_COLUMNS = [
    "block", "record_id", "benchmark", "split", "metric", "model", "role", "arm_label", "arm_key",
    "own_system_id", "system_id", "attribution_method", "attribution_reason", "ablation",
    "direction", "score", "value", "n_rows", "row_min", "row_max",
]


def build_arm_table(comparators: pd.DataFrame, own: pd.DataFrame, attributor: Attributor,
                    agg: str = "median") -> pd.DataFrame:
    """One row per arm of every block: the paper's own system plus every comparator row.

    `role` is one of
      * `own`          - a row of the reporting paper's own system from `results.csv`;
      * `own_variant`  - a comparator row that attribution resolved to the reporting paper's OWN
                         coded system (a re-run or a renamed configuration of it). It is the tuned
                         system too, so it counts as the authors' arm, never as a rival;
      * `comparator`   - a rival's row, attributed to a coded system or anonymous.
    Several rows of one arm inside one block are collapsed to their median (as `analyse_outcomes`
    collapses several rows of one system inside one key), so a comparator quoted five times does
    not outvote one quoted once. `value` is the direction-adjusted score: the score itself for a
    higher-is-better metric, its negation for a lower-is-better one.
    """
    if agg not in {"median", "mean", "max"}:
        raise ValueError(f"agg must be median, mean or max; got {agg!r}")
    rows: list[dict] = []
    for rec in comparators.to_dict(orient="records"):
        label = str(rec.get("reported_system_name") or "")
        note = str(rec.get("note") or "")
        # Alias-aware attributors need the source paper, because an alias is only ever valid for the
        # paper whose text corroborated it. The stock Attributor sets no flag and is called as before.
        att = (
            attributor.attribute(label, note, record_id=str(rec.get("record_id") or ""))
            if getattr(attributor, "uses_record_id", False)
            else attributor.attribute(label, note)
        )
        own_sid = str(rec.get("system_id") or "")
        role = "own_variant" if (att.system_id and att.system_id == own_sid) else "comparator"
        rows.append({
            "block": block_key(rec["record_id"], rec["benchmark"], rec["split"], rec["metric"],
                               rec["model"]),
            "record_id": rec["record_id"],
            "benchmark": rec["benchmark"],
            "split": rec["split"],
            "metric": rec["metric"],
            "model": rec["model"],
            "role": role,
            "arm_label": label,
            "arm_key": att.system_id or f"label:{key_of(label) or norm_cell(label)}",
            "own_system_id": own_sid,
            "system_id": att.system_id,
            "attribution_method": att.method,
            "attribution_reason": att.reason,
            "ablation": ablation_label(label, note),
            "score": float(rec["score_num"]),
        })
    for rec in own.to_dict(orient="records"):
        sid = str(rec.get("system_id") or "")
        rows.append({
            "block": block_key(rec["record_id"], rec["benchmark"], rec["split"], rec["metric"],
                               rec["model"]),
            "record_id": rec["record_id"],
            "benchmark": rec["benchmark"],
            "split": rec["split"],
            "metric": rec["metric"],
            "model": rec["model"],
            "role": "own",
            "arm_label": "(the paper's own system)",
            "arm_key": sid or "own",
            "own_system_id": sid,
            "system_id": sid,
            "attribution_method": "own-row",
            "attribution_reason": "",
            "ablation": "",
            "score": float(rec["score_num"]),
        })
    if not rows:
        return pd.DataFrame(columns=ARM_COLUMNS)
    frame = pd.DataFrame(rows)
    frame["direction"] = frame["metric"].map(metric_direction)
    grouped = frame.groupby(["block", "role", "arm_key"], sort=True)
    collapsed = grouped.agg(
        record_id=("record_id", "first"),
        benchmark=("benchmark", "first"),
        split=("split", "first"),
        metric=("metric", "first"),
        model=("model", "first"),
        arm_label=("arm_label", "first"),
        own_system_id=("own_system_id", "first"),
        system_id=("system_id", "first"),
        attribution_method=("attribution_method", "first"),
        attribution_reason=("attribution_reason", "first"),
        ablation=("ablation", "first"),
        direction=("direction", "first"),
        score=("score", agg),
        n_rows=("score", "size"),
        row_min=("score", "min"),
        row_max=("score", "max"),
    ).reset_index()
    collapsed["value"] = np.where(collapsed["direction"] == "lower",
                                 -collapsed["score"], collapsed["score"])
    return collapsed[ARM_COLUMNS].sort_values(["block", "role", "arm_key"]).reset_index(drop=True)


def drop_single_arm_blocks(arms: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop blocks holding one arm; return the survivors and how many blocks were dropped.

    A block with one arm is a single number at a protocol nobody else ran in that paper: it supports
    no comparison at all, so it cannot enter a within-block analysis.
    """
    if arms.empty:
        return arms, 0
    sizes = arms.groupby("block")["arm_key"].size()
    keep = sizes[sizes >= 2].index
    return arms[arms["block"].isin(keep)].copy().reset_index(drop=True), int((sizes < 2).sum())


def split_ablation_blocks(arms: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Route out blocks whose comparator arms are ALL ablations of the paper's own system.

    Those blocks are an ablation study wearing a baseline table's clothes; they belong to
    `scripts/analyse_ablations.py`. They are returned separately and counted, never dropped in
    silence, and the ablation pattern that routed each one travels with it.
    """
    if arms.empty:
        return arms, arms, {"blocks_routed": 0, "arms_routed": 0, "patterns": {}}
    comparator_like = arms[arms["role"].isin(["comparator", "own_variant"])]
    per_block = comparator_like.groupby("block")["ablation"]
    all_ablation = per_block.apply(lambda s: bool(len(s)) and bool((s != "").all()))
    routed_blocks = set(all_ablation[all_ablation].index)
    routed = arms[arms["block"].isin(routed_blocks)].copy()
    kept = arms[~arms["block"].isin(routed_blocks)].copy()
    patterns = (routed.loc[routed["ablation"] != "", "ablation"].value_counts().to_dict()
                if not routed.empty else {})
    stats_out = {
        "blocks_routed": len(routed_blocks),
        "arms_routed": len(routed),
        "patterns": {k: int(v) for k, v in patterns.items()},
    }
    return kept.reset_index(drop=True), routed.reset_index(drop=True), stats_out


# --------------------------------------------------------------------------------------------
# within-block standardisation
# --------------------------------------------------------------------------------------------
def standardise_within_block(frame: pd.DataFrame, rank_threshold: int = 4,
                             value_col: str = "value", group_col: str = "block",
                             z_col: str = "z", method_col: str = "std_method") -> pd.DataFrame:
    """Add a within-block standardised value and the method used, per the rule in the docstring.

    Identical in convention to `analyse_outcomes.standardise_within_key`, so a number from this
    script and a number from that one mean the same thing: z when the block has `rank_threshold` or
    more arms, standardised average rank below that, 0.0 when every value in the block is equal.
    """
    out = frame.copy()
    out[z_col] = np.nan
    out[method_col] = ""
    if out.empty:
        return out
    for idx in out.groupby(group_col, sort=True).groups.values():
        values = out.loc[idx, value_col].to_numpy(dtype=float)
        n = len(values)
        if n < 2:
            out.loc[idx, z_col] = 0.0
            out.loc[idx, method_col] = "singleton"
            continue
        sd = float(np.std(values, ddof=1))
        if sd == 0.0:
            out.loc[idx, z_col] = 0.0
            out.loc[idx, method_col] = "degenerate"
            continue
        if n >= rank_threshold:
            out.loc[idx, z_col] = (values - values.mean()) / sd
            out.loc[idx, method_col] = "zscore"
        else:
            ranks = stats.rankdata(values, method="average")
            sd_rank = float(np.std(np.arange(1, n + 1, dtype=float), ddof=1))
            out.loc[idx, z_col] = (ranks - (n + 1) / 2.0) / sd_rank
            out.loc[idx, method_col] = "rank"
    return out


MIXED_SCALE_LOW = 1.0    # a value at or below this can be a 0-1 fraction
MIXED_SCALE_HIGH = 10.0  # a value at or above this cannot be, on the same metric


def mixed_scale_blocks(arms: pd.DataFrame) -> set[str]:
    """Blocks mixing a 0-1 and a 0-100 presentation of the same metric.

    One paper reporting 0.42 in one row and 61.0 in another of the same column means the extractor
    read two scales; a within-block z over the two is meaningless, so those blocks are excluded from
    estimation and counted rather than standardised. The test is deliberately narrow - a value at or
    below 1 together with one at or above 10 - because a block of small counts (1, 2, 4 tasks
    solved) is one scale, not two, and must not be thrown away.
    """
    if arms.empty:
        return set()
    def mixed(series: pd.Series) -> bool:
        values = series.abs().to_numpy(dtype=float)
        return bool((values <= MIXED_SCALE_LOW).any() and (values >= MIXED_SCALE_HIGH).any())
    flags = arms.groupby("block")["score"].apply(mixed)
    return set(flags[flags].index)


def annotate_blocks(arms: pd.DataFrame, rank_threshold: int = 4) -> pd.DataFrame:
    """Add both standardisations and the estimability flags to the arm table.

    `z_all` standardises over every arm of the block (the authors' own arm included) and `z_comp`
    over the comparator arms only. The headline analysis uses `z_comp`; `z_all` is the
    optimistically biased version. Standardising twice, rather than computing one z and then
    dropping the own arm from the contrast, is what makes the headline independent of that arm: with
    the own arm in the block its (usually top) score inflates the block's spread and shrinks every
    comparator difference.
    """
    out = arms.copy()
    if out.empty:
        for col in ("z_all", "std_method_all", "z_comp", "std_method_comp",
                    "estimable_block", "exclusion_reason"):
            out[col] = []
        return out
    all_std = standardise_within_block(out, rank_threshold, z_col="z_all",
                                       method_col="std_method_all")
    comp_mask = all_std["role"] == "comparator"
    comp = all_std[comp_mask].copy()
    comp_sizes = comp.groupby("block")["arm_key"].size()
    comp_ok = comp[comp["block"].isin(comp_sizes[comp_sizes >= 2].index)]
    comp_std = standardise_within_block(comp_ok, rank_threshold, z_col="z_comp",
                                        method_col="std_method_comp")
    out = all_std.merge(
        comp_std[["block", "role", "arm_key", "z_comp", "std_method_comp"]],
        on=["block", "role", "arm_key"], how="left",
    )
    mixed = mixed_scale_blocks(out)
    unknown = set(out.loc[out["direction"] == "unknown", "block"])
    reasons = []
    for block in out["block"]:
        if block in mixed:
            reasons.append("mixed_scale")
        elif block in unknown:
            reasons.append("metric_direction_unknown")
        else:
            reasons.append("")
    out["exclusion_reason"] = reasons
    out["estimable_block"] = out["exclusion_reason"] == ""
    return out


# --------------------------------------------------------------------------------------------
# block-level description, and the own-arm win rate
# --------------------------------------------------------------------------------------------
def block_summary(arms: pd.DataFrame) -> pd.DataFrame:
    """One row per block: what it holds, how far apart its arms are, and where the own arm ranks."""
    if arms.empty:
        return pd.DataFrame(columns=[
            "block", "record_id", "benchmark", "split", "metric", "model", "n_arms",
            "n_comparator_arms", "n_attributed", "n_attributed_comparators", "n_ablation_arms",
            "n_non_ablation_arms", "own_first_chance", "own_first_chance_uncorrected",
            "direction", "score_min", "score_max", "spread", "std_method_all", "has_own_arm",
            "own_rank", "own_first", "own_tied_first", "own_z_all", "estimable_block",
            "exclusion_reason",
        ])
    rows = []
    for block, sub in arms.groupby("block", sort=True):
        own = sub[sub["role"].isin(["own", "own_variant"])]
        comparators = sub[sub["role"] == "comparator"]
        values = sub["value"].to_numpy(dtype=float)
        own_rank = np.nan
        own_first = False
        own_tied = False
        own_z = np.nan
        if not own.empty:
            best = float(np.max(values))
            own_best = float(own["value"].max())
            # rank 1 = highest direction-adjusted value; ties share the top rank.
            own_rank = float(1 + int((values > own_best + 1e-12).sum()))
            own_first = bool(own_best >= best - 1e-12)
            own_tied = bool(own_first and int((values >= best - 1e-12).sum()) > 1)
            own_z = float(own["z_all"].max()) if "z_all" in own.columns else np.nan
        n_ablation = int((sub["ablation"] != "").sum())
        rows.append({
            "block": block,
            "record_id": sub["record_id"].iloc[0],
            "benchmark": sub["benchmark"].iloc[0],
            "split": sub["split"].iloc[0],
            "metric": sub["metric"].iloc[0],
            "model": sub["model"].iloc[0],
            "n_arms": len(sub),
            "n_comparator_arms": len(comparators),
            "n_attributed": int((sub["system_id"] != "").sum()),
            "n_attributed_comparators": int((comparators["system_id"] != "").sum()),
            # The ablation-arm count is what drives the chance-baseline correction below, so it is
            # emitted per block together with both baselines it implies.
            "n_ablation_arms": n_ablation,
            "n_non_ablation_arms": max(len(sub) - n_ablation, 1),
            "own_first_chance": own_arm_chance(len(sub), n_ablation),
            "own_first_chance_uncorrected": 1.0 / len(sub),
            "direction": sub["direction"].iloc[0],
            "score_min": float(sub["score"].min()),
            "score_max": float(sub["score"].max()),
            "spread": float(sub["score"].max() - sub["score"].min()),
            "std_method_all": sub["std_method_all"].iloc[0] if "std_method_all" in sub else "",
            "has_own_arm": not own.empty,
            "own_rank": own_rank,
            "own_first": own_first,
            "own_tied_first": own_tied,
            "own_z_all": own_z,
            "estimable_block": bool(sub["estimable_block"].iloc[0])
                               if "estimable_block" in sub else True,
            "exclusion_reason": sub["exclusion_reason"].iloc[0]
                                if "exclusion_reason" in sub else "",
        })
    return pd.DataFrame(rows).sort_values(["n_arms", "block"], ascending=[False, True]).reset_index(
        drop=True)


OWN_ARM_MC_DRAWS = 10_000
OWN_ARM_SEED = 20260924


def own_arm_chance(n_arms: int, n_ablation_arms: int) -> float:
    """The chance probability that the paper's own arm tops a block, over the RIVAL arms only.

    `1 / n_arms` is wrong here, and the error is not small. An arm flagged `ablation` is the
    reporting paper's own system with a component switched off; it was not chosen from the field of
    harnesses, and the paper's full system beating it is the premise of the ablation study, not
    evidence about which comparators an author assembles. The baseline is therefore one over the
    number of arms that could have topped the table on their own merits, floored at 1 so a block
    whose comparators are all ablations contributes a certainty rather than a division by zero.
    """
    return 1.0 / max(int(n_arms) - int(n_ablation_arms), 1)


def paper_clustered_tail(probs: Sequence[float], papers: Sequence[str], observed: int,
                         n_draws: int = OWN_ARM_MC_DRAWS, seed: int = OWN_ARM_SEED) -> float:
    """Monte-Carlo P(X >= observed) when the null draw is made ONCE PER PAPER.

    The exact Poisson-binomial treats the blocks as independent Bernoullis. They are not: 75 blocks
    come from 37 papers, one paper contributing nine of them, and a paper that builds big own-ablation
    tables builds several at once. This null draws one uniform per paper and applies it to every block
    of that paper (a block succeeds when the draw falls under its own chance probability), which keeps
    each block's marginal probability exactly right while making a paper's blocks perfectly
    correlated - the conservative end of the clustering, reported beside the independent tail rather
    than instead of it. Seeded, so the number in the paper is reproducible.
    """
    p = np.asarray(probs, dtype=float)
    if p.size == 0:
        return float("nan")
    order = sorted(set(papers))
    idx = np.array([order.index(str(x)) for x in papers], dtype=int)
    rng = np.random.default_rng(int(seed))
    draws = rng.random((int(n_draws), len(order)))
    hits = (draws[:, idx] < p).sum(axis=1)
    return float((hits >= int(observed)).mean())


def _tail_block(blocks: pd.DataFrame, chance_col: str) -> dict:
    """Observed count, expected count and the exact Poisson-binomial tail for one chance baseline."""
    probs = blocks[chance_col].to_numpy(dtype=float).tolist()
    observed = int(blocks["own_first"].sum())
    expected, pval = poisson_binomial_tail(probs, observed)
    return {
        "blocks": len(blocks),
        "own_first": observed,
        "share_first": float(blocks["own_first"].mean()) if len(blocks) else float("nan"),
        "expected_by_chance": float(expected),
        "exact_poisson_binomial_p": float(pval),
    }


def own_arm_first_stats(blocks: pd.DataFrame, n_draws: int = OWN_ARM_MC_DRAWS,
                        seed: int = OWN_ARM_SEED) -> dict:
    """How often the reporting paper's own arm ranks first in its own block.

    This is a measurement of the reporting practice, not of any design: it is the number that says
    how much the own-arm-inclusive estimates below should be discounted. Blocks with two arms are
    reported separately, because there a coin flip alone would put the own arm first half the time.

    Two corrections, both forced by a statistics review of the published version, and both kept
    auditable rather than applied silently:
      * the chance baseline is `own_arm_chance` - one over the NON-ABLATION arms - because the
        reporting paper's own switched-off configurations are not independently chosen rivals. The
        uncorrected `1 / n_arms` version is still computed and returned under ``uncorrected``;
      * the blocks are pseudo-replicated within paper, so beside the exact (independent) tail this
        returns a PAPER-CLUSTERED Monte-Carlo p and a one-block-per-paper exact p.
    What survives both corrections is the subgroup of blocks with five or more arms, not the overall
    share; the honest reading of that subgroup is that a large arm table in this literature is largely
    the paper's OWN ablation table.
    """
    with_own = blocks[blocks["has_own_arm"]].copy() if not blocks.empty else blocks
    n = len(with_own)
    if n == 0:
        return {"blocks_with_own_arm": 0, "own_first": 0, "share_first": float("nan"),
                "own_tied_first": 0, "mean_own_rank": float("nan"),
                "mean_own_z": float("nan"), "by_arms": {}, "chance_share": float("nan"),
                "n_ablation_arms": 0, "blocks_detail": [],
                "chance_baseline": "1 / max(n_arms - n_ablation_arms, 1)"}
    if "own_first_chance" not in with_own.columns:  # a frame from an older block_summary
        with_own["n_ablation_arms"] = with_own.get("n_ablation_arms", 0)
        with_own["own_first_chance"] = [
            own_arm_chance(a, b) for a, b in zip(with_own["n_arms"], with_own["n_ablation_arms"])
        ]
        with_own["n_non_ablation_arms"] = (
            with_own["n_arms"] - with_own["n_ablation_arms"]).clip(lower=1)
        with_own["own_first_chance_uncorrected"] = 1.0 / with_own["n_arms"]
    by_arms = {}
    for n_arms, sub in with_own.groupby("n_arms"):
        by_arms[int(n_arms)] = {
            "blocks": len(sub),
            "own_first": int(sub["own_first"].sum()),
            "share_first": float(sub["own_first"].mean()),
            # The primary baseline, averaged over the blocks of this size: the blocks of one size
            # differ in how many of their arms are the paper's own ablations.
            "chance_share": float(sub["own_first_chance"].mean()),
            "chance_share_uncorrected": float(1.0 / int(n_arms)),
            "ablation_arms": int(sub["n_ablation_arms"].sum()),
            "mean_non_ablation_arms": float(sub["n_non_ablation_arms"].mean())
                                      if "n_non_ablation_arms" in sub else float("nan"),
        }
    corrected = _tail_block(with_own, "own_first_chance")
    uncorrected = _tail_block(with_own, "own_first_chance_uncorrected")
    big = with_own[with_own["n_arms"] >= 5]
    clustered_p = paper_clustered_tail(
        with_own["own_first_chance"].to_numpy(dtype=float),
        [str(x) for x in with_own["record_id"]],
        int(with_own["own_first"].sum()), n_draws=n_draws, seed=seed,
    )
    # One block per paper removes the pseudo-replication outright instead of modelling it. The
    # largest block of each paper is the one kept (ties broken by the block key, so the choice is
    # deterministic and not a function of the outcome).
    one_per_paper = with_own.sort_values(["n_arms", "block"], ascending=[False, True]).groupby(
        "record_id", sort=True).head(1)
    return {
        "blocks_with_own_arm": int(n),
        "own_first": int(with_own["own_first"].sum()),
        "share_first": float(with_own["own_first"].mean()),
        "own_tied_first": int(with_own["own_tied_first"].sum()),
        "mean_own_rank": float(with_own["own_rank"].mean()),
        "mean_own_z": float(with_own["own_z_all"].mean()),
        "papers": int(with_own["record_id"].nunique()),
        "n_ablation_arms": int(with_own["n_ablation_arms"].sum()),
        "chance_baseline": "1 / max(n_arms - n_ablation_arms, 1)",
        "chance_share": float(with_own["own_first_chance"].mean()),
        "expected_by_chance": corrected["expected_by_chance"],
        "exact_poisson_binomial_p": corrected["exact_poisson_binomial_p"],
        "five_plus_arms": _tail_block(big, "own_first_chance") if len(big) else {},
        "paper_clustered": {
            "p": clustered_p,
            "draws": int(n_draws),
            "seed": int(seed),
            "papers": int(with_own["record_id"].nunique()),
            "null": "one uniform draw per paper, applied to every block of that paper",
        },
        "one_block_per_paper": {
            **_tail_block(one_per_paper, "own_first_chance"),
            "rule": "the largest block of each paper, ties broken by block key",
        },
        "uncorrected": {
            "chance_baseline": "1 / n_arms (counts the paper's own ablation arms as rivals)",
            "chance_share": float(with_own["own_first_chance_uncorrected"].mean()),
            "expected_by_chance": uncorrected["expected_by_chance"],
            "exact_poisson_binomial_p": uncorrected["exact_poisson_binomial_p"],
            "five_plus_arms": _tail_block(big, "own_first_chance_uncorrected") if len(big) else {},
            "why_wrong": OWN_ARM_CHANCE_CAVEAT,
        },
        "by_arms": by_arms,
        "blocks_detail": [
            {
                "block": r.block,
                "record_id": r.record_id,
                "n_arms": int(r.n_arms),
                "n_ablation_arms": int(r.n_ablation_arms),
                "n_non_ablation_arms": int(r.n_non_ablation_arms),
                "chance": float(r.own_first_chance),
                "chance_uncorrected": float(r.own_first_chance_uncorrected),
                "own_first": bool(r.own_first),
            }
            for r in with_own.itertuples()
        ],
        "reading": (
            "The overall own-arm advantage does NOT survive the corrected baseline (p = "
            f"{corrected['exact_poisson_binomial_p']:.3f} unclustered, {clustered_p:.3f} "
            "paper-clustered). What survives is the subgroup of tables with five or more arms. Read "
            "that as evidence that large arm tables in this literature are largely the paper's own "
            "ablation tables, not as a second independent measurement of selective comparator choice."
        ),
        "caveat": OWN_ARM_CHANCE_CAVEAT,
    }


# --------------------------------------------------------------------------------------------
# pre-specified contrasts
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Contrast:
    """One binary design contrast, fixed before estimation."""

    name: str
    dimension: str  # key in systems.json `coding`
    dimension_id: str  # schema/dimensions.json id
    exposed_label: str
    reference_label: str
    exposed_when: Callable[[frozenset[str]], bool]
    mechanism: str
    drift_exposure: str
    mirrors: str = ""  # the `analyse_outcomes.py` contrast this one is the block-level twin of


def _any_of(*tokens: str) -> Callable[[frozenset[str]], bool]:
    wanted = frozenset(tokens)
    return lambda coded: bool(coded & wanted)


def _anything_but(*tokens: str) -> Callable[[frozenset[str]], bool]:
    excluded = frozenset(tokens)
    return lambda coded: bool(coded - excluded)


# Fixed as a set before estimation, and all of them reported whatever they come out at. The six are
# the protocol's mechanistic candidates for RQ3; the definitions of the first five are character for
# character those of `analyse_outcomes.CONTRASTS`, so the block-level estimate and the cross-paper
# estimate of the same contrast can be put side by side. `persistent_memory` has no cross-paper twin
# and is included because a baseline table is where a memory-carrying harness meets a stateless one.
# Which of them actually VARY inside a block is a property of the data, reported per contrast; a
# contrast that varies in fewer than --min-blocks blocks is NOT ESTIMABLE and is still printed.
CONTRASTS: tuple[Contrast, ...] = (
    Contrast(
        name="multi_agent",
        dimension="multi_agent_topology",
        dimension_id="C3",
        exposed_label="multiple agents (orchestrator-workers, peer, hierarchical, debate, pipeline)",
        reference_label="single agent",
        exposed_when=_anything_but("single"),
        mechanism=(
            "Splitting a task across roles gives each a shorter context and a narrower tool set, "
            "at the cost of handoff loss between them; the sign of the net effect is the question."
        ),
        drift_exposure="low - topology is architectural and rarely changes within a system",
        mirrors="multi_agent",
    ),
    Contrast(
        name="explicit_plan",
        dimension="planning_granularity",
        dimension_id="C2",
        exposed_label="explicit plan object or hierarchical plan",
        reference_label="no plan or implicit planning only",
        exposed_when=_any_of("explicit_plan_object", "hierarchical"),
        mechanism=(
            "A materialised plan is state the loop can check progress against and return to after "
            "a detour, which is what keeps a long trajectory from wandering."
        ),
        drift_exposure="medium - plan objects are added and removed across releases",
        mirrors="explicit_plan",
    ),
    Contrast(
        name="executable_verification",
        dimension="self_verification",
        dimension_id="E1",
        exposed_label="executes tests / typecheck / formal check",
        reference_label="no executable check (none, self-critique or LLM judge only)",
        exposed_when=_any_of("test_execution", "linters_typecheck", "formal"),
        mechanism=(
            "An executable check gives the loop ground truth about whether its edit works, so it "
            "can reject a wrong candidate before submitting it; self-critique and LLM judging "
            "supply only the model's own opinion."
        ),
        drift_exposure="high - verification wiring changes often between releases",
        mirrors="executable_verification",
    ),
    Contrast(
        name="any_retry",
        dimension="retry_policy",
        dimension_id="E2",
        exposed_label="retries on failure (fixed_n, until_pass or adaptive)",
        reference_label="no retry",
        exposed_when=_anything_but("none"),
        mechanism=(
            "Sampling more than one attempt converts a per-attempt success probability into "
            "1-(1-p)^k when failures are detectable, which is the mechanism behind pass@k gains."
        ),
        drift_exposure="high - retry counts are tuning knobs that move release to release",
        mirrors="any_retry",
    ),
    Contrast(
        name="any_compaction",
        dimension="context_compaction",
        dimension_id="A3",
        exposed_label="compacts history (summarise, prune, checkpoint, truncate or model-native)",
        reference_label="no compaction",
        exposed_when=_anything_but("none"),
        mechanism=(
            "Long agent trajectories overflow the window; compaction keeps the task description "
            "and the relevant state in view instead of losing them to truncation from the front."
        ),
        drift_exposure="high - compaction is among the fastest-churning parts of a harness",
        mirrors="any_compaction",
    ),
    Contrast(
        name="persistent_memory",
        dimension="long_term_memory",
        dimension_id="D2",
        exposed_label="long-term memory (skill library, file notes, episodic db or vector store)",
        reference_label="no long-term memory",
        exposed_when=_anything_but("none"),
        mechanism=(
            "Memory that outlives one episode lets a harness reuse a solved sub-problem instead of "
            "rediscovering it, which is worth most on benchmarks whose tasks repeat structure."
        ),
        drift_exposure="medium - memory backends are added and swapped between releases",
        mirrors="",
    ),
)


def contrast_frame(arms: pd.DataFrame, contrast: Contrast, codings: dict,
                   include_own: bool) -> pd.DataFrame:
    """The arms that carry a coded value for one contrast, in the blocks where it varies.

    `include_own=False` (the headline) keeps only `role == comparator` arms and standardises on
    `z_comp`; `include_own=True` keeps every arm and standardises on `z_all`. Either way an arm
    without an attributed coded system, or whose coding of the dimension is `not_reported` /
    `unresolved`, carries no value and drops out of THIS contrast - it stays in the block and in the
    standardisation, because it is still a score at the same protocol.

    A block in which every arm sits on the same side of the contrast carries no within-block
    information and is excluded; that exclusion is what makes the estimate a within-block one.
    """
    if arms.empty:
        return arms.assign(x=[], z=[])
    frame = arms[arms["estimable_block"]].copy()
    if include_own:
        frame["z"] = frame["z_all"]
        frame["std_method"] = frame["std_method_all"]
    else:
        frame = frame[frame["role"] == "comparator"].copy()
        frame["z"] = frame["z_comp"]
        frame["std_method"] = frame["std_method_comp"]
    frame = frame[frame["z"].notna() & (frame["system_id"] != "")].copy()
    exposure: list[float] = []
    for sid in frame["system_id"]:
        values = coded_values(codings.get(sid, {}), contrast.dimension)
        exposure.append(np.nan if values is None
                        else float(contrast.exposed_when(frozenset(values))))
    frame["x"] = exposure
    known = frame[frame["x"].notna()].copy()
    if known.empty:
        return known
    varies = known.groupby("block")["x"].nunique()
    return known[known["block"].isin(varies[varies >= 2].index)].copy()


def block_differences(frame: pd.DataFrame) -> pd.DataFrame:
    """Per block: the within-block difference in standardised score, exposed minus reference."""
    rows = []
    for block, sub in frame.groupby("block", sort=True):
        exposed = sub[sub["x"] == 1.0]
        reference = sub[sub["x"] == 0.0]
        if exposed.empty or reference.empty:
            continue
        rows.append({
            "block": block,
            "record_id": sub["record_id"].iloc[0],
            "benchmark": sub["benchmark"].iloc[0],
            "n_arms": len(sub),
            "n_exposed": len(exposed),
            "n_reference": len(reference),
            "std_method": sub["std_method"].iloc[0],
            "d": float(exposed["z"].mean() - reference["z"].mean()),
        })
    return pd.DataFrame(rows, columns=["block", "record_id", "benchmark", "n_arms", "n_exposed",
                                       "n_reference", "std_method", "d"])


# --------------------------------------------------------------------------------------------
# bootstrap over BLOCKS (and over papers), power, permutation
# --------------------------------------------------------------------------------------------
def bootstrap_block_means(differences: Sequence[float], n_boot: int = 10_000,
                          seed: int = 20260924) -> np.ndarray:
    """Percentile bootstrap of the mean block-level difference, resampling BLOCKS.

    The unit of resampling is the block, never the row and never the arm: one draw takes K blocks
    with replacement from the K observed blocks and averages their differences. Resampling arms
    instead would treat the six arms of one paper's table as six independent pieces of evidence
    about harness design, when they share one paper, one benchmark, one split, one metric, one model
    and one team.
    """
    d = np.asarray(differences, dtype=float)
    k = len(d)
    if k == 0:
        return np.empty(0, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(int(n_boot), k))
    return d[idx].mean(axis=1)


def bootstrap_paper_means(diffs: pd.DataFrame, n_boot: int = 10_000,
                          seed: int = 20260924) -> np.ndarray:
    """The same bootstrap with the PAPER as the resampling unit, for the blocks-nested-in-papers case.

    A paper that contributes three blocks contributes three correlated differences - same authors,
    same implementation of every comparator, often the same table. Resampling papers, and averaging
    a paper's blocks before averaging papers, is the conservative version of the interval; it is
    reported beside the block bootstrap whenever a paper contributes more than one block.
    """
    if diffs.empty:
        return np.empty(0, dtype=float)
    per_paper = [g["d"].to_numpy(dtype=float).mean()
                 for _rid, g in diffs.groupby("record_id", sort=True)]
    return bootstrap_block_means(per_paper, n_boot=n_boot, seed=seed)


def permutation_test_within_block(frame: pd.DataFrame, n_perm: int = 10_000, seed: int = 20260924,
                                  exact_limit: int = 50_000) -> dict:
    """Randomisation test on the design: shuffle the design labels INSIDE each block.

    The labels are permuted among the arms of a block that carry a coded value, holding the number
    of exposed arms fixed, which is the randomisation the blocking implies. Reports the two-sided p
    and - the point of it - the DESIGN FLOOR `p_min_attainable`, one over the number of distinct
    label assignments the design admits. A contrast whose floor sits above 0.05 cannot produce
    evidence at any conventional level however large its point estimate, and that is a statement
    about the dataset, not about harness design.
    """
    per_block: list[list[float]] = []
    for _block, sub in frame.groupby("block", sort=True):
        z = sub["z"].to_numpy(dtype=float)
        x = sub["x"].to_numpy(dtype=float)
        if x.sum() in (0.0, float(len(x))):
            continue
        per_block.append(_key_difference_options(z, x))
    if not per_block:
        return {"available": False, "reason": "no block with variation in the contrast"}
    n_assignments = 1
    for options in per_block:
        n_assignments *= len(options)
        if n_assignments > 10 ** 12:
            break
    observed = float(block_differences(frame)["d"].mean())
    tol = 1e-12
    if n_assignments <= exact_limit:
        from itertools import product

        stats_all = np.array([float(np.mean(combo)) for combo in product(*per_block)])
        p_two = float((np.abs(stats_all) >= abs(observed) - tol).mean())
        mode = "exact"
        n_draws = len(stats_all)
    else:
        rng = np.random.default_rng(seed)
        draws = np.empty(int(n_perm), dtype=float)
        arrays = [np.asarray(o, dtype=float) for o in per_block]
        for b in range(int(n_perm)):
            draws[b] = float(np.mean([a[rng.integers(0, len(a))] for a in arrays]))
        p_two = float((1 + int((np.abs(draws) >= abs(observed) - tol).sum())) / (1 + int(n_perm)))
        mode = "monte-carlo"
        n_draws = int(n_perm)
    return {
        "available": True,
        "mode": mode,
        "observed": observed,
        "p_two_sided": p_two,
        "n_assignments": int(n_assignments),
        "p_min_attainable": 1.0 / n_assignments,
        "n_draws": n_draws,
        "floor_above_05": bool(1.0 / n_assignments > 0.05),
        "saturated": bool(mode == "exact" and p_two <= 1.0 / n_assignments + 1e-12),
    }


def estimate_contrast(arms: pd.DataFrame, contrast: Contrast, codings: dict, include_own: bool,
                      n_boot: int = 10_000, seed: int = 20260924,
                      min_blocks: int = 3) -> dict:
    """Everything reportable about one contrast under one own-arm policy, estimable or not.

    A contrast is never dropped for its result. Below `min_blocks` blocks it is reported as NOT
    ESTIMABLE with its block-level differences attached: with one or two blocks the between-block
    spread has 0 or 1 degrees of freedom and a bootstrap can return a zero-width interval that looks
    like precision and is an artefact of the design.
    """
    frame = contrast_frame(arms, contrast, codings, include_own=include_own)
    diffs = block_differences(frame)
    n_blocks = len(diffs)
    d = diffs["d"].to_numpy(dtype=float)
    result: dict = {
        "name": contrast.name,
        "dimension": contrast.dimension,
        "dimension_id": contrast.dimension_id,
        "include_own_arm": bool(include_own),
        "arm_policy": ("comparator arms only (headline)" if not include_own
                       else "authors' own arm included (OPTIMISTICALLY BIASED)"),
        "exposed": contrast.exposed_label,
        "reference": contrast.reference_label,
        "mechanism": contrast.mechanism,
        "drift_exposure": contrast.drift_exposure,
        "mirrors_cross_paper_contrast": contrast.mirrors,
        "n_blocks": n_blocks,
        "n_papers": int(diffs["record_id"].nunique()) if n_blocks else 0,
        "n_arms": len(frame),
        "n_systems": int(frame["system_id"].nunique()) if len(frame) else 0,
        "n_exposed_arms": int((frame["x"] == 1.0).sum()) if len(frame) else 0,
        "n_reference_arms": int((frame["x"] == 0.0).sum()) if len(frame) else 0,
        "benchmarks": sorted(set(diffs["benchmark"])) if n_blocks else [],
        "blocks": diffs.to_dict(orient="records"),
        "block_differences": [float(v) for v in d],
        "estimable": n_blocks >= min_blocks,
        "fragile": bool(0 < n_blocks < FRAGILE_BLOCKS),
        "effect": float(d.mean()) if n_blocks else float("nan"),
        "ci_low": float("nan"),
        "ci_high": float("nan"),
        "ci_low_paper": float("nan"),
        "ci_high_paper": float("nan"),
        "mde_80": float("nan"),
        "se": float("nan"),
        "bootstrap_unit": "block",
        "n_boot": int(n_boot),
        "seed": int(seed),
        "degenerate_interval": False,
    }
    result["permutation"] = (
        permutation_test_within_block(frame, n_perm=n_boot, seed=seed)
        if n_blocks else {"available": False, "reason": "no block with variation in the contrast"}
    )
    if n_blocks >= min_blocks:
        spread = float(np.std(d, ddof=1))
        if spread == 0.0:
            result["degenerate_interval"] = True
            result["degenerate_reason"] = (
                f"all {n_blocks} block-level differences are identical ({d[0]:+.3f}), so the "
                "between-block spread is zero and neither an interval nor a power statement is "
                "defined"
            )
        else:
            replicates = bootstrap_block_means(d, n_boot=n_boot, seed=seed)
            result["ci_low"] = float(np.percentile(replicates, 2.5))
            result["ci_high"] = float(np.percentile(replicates, 97.5))
            result["mde_80"] = float(mde_from_key_differences(d))
            result["se"] = spread / math.sqrt(n_blocks)
            if result["n_papers"] < n_blocks and result["n_papers"] >= 2:
                paper_reps = bootstrap_paper_means(diffs, n_boot=n_boot, seed=seed)
                if paper_reps.size and float(np.std(paper_reps)) > 0.0:
                    result["ci_low_paper"] = float(np.percentile(paper_reps, 2.5))
                    result["ci_high_paper"] = float(np.percentile(paper_reps, 97.5))
    else:
        result["not_estimable_reason"] = (
            f"the contrast varies inside only {n_blocks} block(s); {min_blocks} is the "
            "pre-specified minimum, below which the between-block spread has too few degrees of "
            "freedom for an interval or a power statement"
        )
    interval_usable = bool(
        result["estimable"] and not result["degenerate_interval"]
        and not np.isnan(result["ci_low"])
    )
    result["ci_excludes_zero"] = bool(
        interval_usable and not (result["ci_low"] <= 0.0 <= result["ci_high"])
    )
    perm_p = result["permutation"].get("p_two_sided")
    result["perm_rejects"] = bool(perm_p is not None and perm_p < 0.05)
    # The blocking factor is the PAPER, so blocks drawn from one paper are not replicates: they share
    # the authors, the implementation of every comparator and usually one table. A contrast whose
    # blocks all come from a single paper therefore cannot be called detected however small its
    # p-value - it is one team's table, and the bootstrap over its blocks overstates the precision.
    result["single_paper"] = bool(n_blocks and result["n_papers"] <= 1)
    result["few_papers"] = bool(n_blocks and result["n_papers"] < 3)
    # Bootstrap and randomisation test have to agree before anything is called detected, and when
    # they disagree the randomisation test wins: the bootstrap over a handful of block-level
    # differences assumes those differences represent their own sampling distribution, which at these
    # counts they do not.
    result["detected"] = bool(
        result["ci_excludes_zero"] and result["perm_rejects"] and not result["single_paper"]
    )
    result["null"] = bool(interval_usable and not result["detected"])
    result["disagreement"] = bool(
        interval_usable and result["ci_excludes_zero"] and not result["perm_rejects"]
    )
    result["only_large_detectable"] = bool(
        not np.isnan(result["mde_80"]) and result["mde_80"] >= LARGE_EFFECT
    )
    result["power_sentence"] = power_sentence(result)
    return result


def _fmt_p(p: float | None, floor: float | None = None) -> str:
    """A p-value is never printed as 0.000: no finite resampling supports that."""
    if p is None:
        return "n/a"
    if floor is not None and p <= floor + 1e-15:
        return f"<{max(floor, 1e-4):.4f}"
    if p < 1e-4:
        return "<0.0001"
    return f"{p:.4f}"


def power_sentence(result: dict) -> str:
    """The power statement in words, for the console and for the figure caption."""
    name = result["name"]
    perm = result.get("permutation") or {}
    floor = ""
    if perm.get("available"):
        n_assign = perm["n_assignments"]
        floor = (
            f" The design admits {n_assign:,} distinct within-block label assignments, so the "
            f"smallest attainable permutation p-value is "
            f"{max(perm['p_min_attainable'], 1e-4):.4f}"
            + ("; no conventional significance level is reachable from this contrast whatever the "
               "point estimate."
               if perm["floor_above_05"]
               else f" (observed {_fmt_p(perm['p_two_sided'], 1.0 / (perm['n_draws'] + 1))}).")
        )
    replication = ""
    if result.get("single_paper"):
        replication = (
            f" NOT INDEPENDENTLY REPLICATED: all {result['n_blocks']} blocks come from ONE paper, "
            "so they share the authors, the implementation of every comparator and usually one "
            "table. The paper is the blocking factor and there is only one of it; the interval "
            "describes that table, not the field, and nothing here can be called a detected "
            "association.")
    elif result.get("few_papers"):
        replication = (f" Only {result['n_papers']} papers contribute, so the between-paper "
                       "replication the design relies on is minimal.")
    if not result["estimable"]:
        return (
            f"{name}: NOT ESTIMABLE - the contrast varies inside only {result['n_blocks']} "
            f"block(s), so no interval and no minimum detectable effect are defined."
            + replication + floor
        )
    if result["degenerate_interval"]:
        return (
            f"{name}: all {result['n_blocks']} block-level differences are identical, so the "
            "between-block spread is zero and no interval or minimum detectable effect is defined; "
            "the apparent precision would be an artefact." + replication + floor
        )
    stem = (
        f"{name}: with {result['n_blocks']} blocks from {result['n_papers']} papers, "
        f"{result['n_arms']} arms and {result['n_systems']} distinct coded systems, the smallest "
        f"effect detectable at 80% power (two-sided, alpha=0.05) is {result['mde_80']:.2f} "
        f"within-block sd."
    )
    if result["only_large_detectable"]:
        stem += (" Only a very large effect would have been detectable here, so the absence of a "
                 "detected association is uninformative about anything smaller.")
    else:
        stem += " Effects smaller than that are beyond the resolution of this dataset."
    if result["fragile"]:
        stem += (f" FRAGILE: fewer than {FRAGILE_BLOCKS} blocks, so the between-block spread that "
                 "both the interval and this number rest on is itself barely estimated; treat the "
                 "interval as descriptive.")
    return stem + replication + floor


def finding_line(primary: dict, secondary: dict) -> str:
    """The one-line finding for a contrast, with the own-arm dependence stated where it exists."""
    if not primary["estimable"] and not secondary["estimable"]:
        return (f"NOT ESTIMABLE either way - varies in {primary['n_blocks']} comparator-only "
                f"block(s) and {secondary['n_blocks']} block(s) with the authors' arm included.")
    if not primary["estimable"]:
        base = (f"NOT ESTIMABLE without the authors' own arm ({primary['n_blocks']} block(s)). "
                f"With that arm included it rests on {secondary['n_blocks']} block(s)")
        if secondary["detected"]:
            return base + (" and reaches significance - but that version is optimistically biased, "
                           "so this is NOT evidence for the design feature.")
        return base + " and is null there too."
    if primary["degenerate_interval"]:
        return "NOT INTERPRETABLE - zero between-block spread among the comparator-only blocks."
    if primary["single_paper"]:
        line = (f"NOT INDEPENDENTLY REPLICATED - the {primary['n_blocks']} comparator-only blocks "
                f"all come from ONE paper, so the estimate ({primary['effect']:+.2f} sd) describes "
                "that paper's table and not the field; the paper is the blocking factor and there "
                "is only one of it.")
        if secondary["estimable"] and secondary["detected"]:
            line += (" The version with the authors' own arm reaches significance across "
                     f"{secondary['n_papers']} papers, but it is optimistically biased by "
                     "construction, so it is not evidence for the design feature either.")
        return line
    if primary["detected"]:
        line = ("ASSOCIATION DETECTED among comparator arms only (the authors' own arm excluded), "
                "with the bootstrap interval and the randomisation test agreeing.")
        if secondary["estimable"] and not secondary["detected"]:
            line += (" It does NOT survive adding the authors' own arm, which is the direction of "
                     "bias that would have inflated it, so the comparator-only result is the one "
                     "to read.")
        return line
    if primary["disagreement"]:
        return ("NO DETECTABLE ASSOCIATION - the bootstrap interval excludes zero but the "
                "within-block randomisation test does not reject, and at this block count the "
                "randomisation test is the more trustworthy of the two.")
    line = ("NO DETECTABLE ASSOCIATION among comparator arms only; the CI covers zero. Reported as "
            "a result, not an absence of one - read it with the detectable effect below.")
    if secondary.get("detected"):
        line += (" SIGNIFICANT ONLY WITH THE AUTHORS' OWN ARM INCLUDED: that version is "
                 "optimistically biased by construction (the authors' system is the tuned one), so "
                 "the significance belongs to the reporting practice, not to the design feature.")
    return line


# --------------------------------------------------------------------------------------------
# figures (house style of scripts/prisma_diagram.py: DejaVu Sans, #333 lines, SVG + PDF)
# --------------------------------------------------------------------------------------------
def _wrap(text: str, width: int = 150) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _save(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for ext in ("svg", "pdf"):
        path = stem.with_suffix(f".{ext}")
        fig.savefig(path, format=ext, bbox_inches="tight")
        written.append(path)
    return written


def figure_block_funnel(counts: dict, out_stem: Path) -> list[Path]:
    """Where the 3,280 baseline-table rows go: the attrition from row to estimable contrast arm."""
    import matplotlib.pyplot as plt

    stages = [
        ("comparator rows in paper baseline tables\n(results_rejects.csv, not_own_system)",
         counts["comparator_rows"]),
        ("in a block with 2+ arms\n(paper x benchmark x split x metric x model)",
         counts["arms_in_blocks_raw"]),
        ("after routing out all-ablation blocks\n(those belong to analyse_ablations.py)",
         counts["arms_after_ablation_routing"]),
        ("in a block the design can use\n(known metric direction, single scale)",
         counts["arms_estimable_blocks"]),
        (("COMPARATOR arms attributed to a coded system\n"
          "(the only arms an own-arm-free contrast can use)"),
         counts["attributed_comparator_arms"]),
    ]
    fig, ax = plt.subplots(figsize=(11.0, 4.6))
    ys = list(range(len(stages)))[::-1]
    total = stages[0][1] or 1
    for y, (label, n) in zip(ys, stages):
        ax.barh(y, n, height=0.55, color="#1f4e79" if y else "#b45309", alpha=0.9)
        ax.annotate(f"{n:,}   ({n / total:.1%} of the baseline-table rows)", xy=(n, y),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5,
                    color="#374151")
    ax.set_yticks(ys)
    ax.set_yticklabels([s[0] for s in stages], fontsize=8.0)
    ax.set_xlim(0, total * 1.42)
    ax.set_xlabel("arms (rows collapsed to one arm per coded system or label per block)",
                  fontsize=8)
    ax.set_title(
        "Within-paper comparison blocks: what survives to carry a design contrast\n"
        f"{counts['blocks_raw']:,} blocks with 2+ arms -> {counts['blocks_after_ablation']:,} after "
        f"ablation-only blocks are routed out -> {counts['blocks_two_attributed_comparators']:,} "
        f"with two or more coded comparator arms",
        fontsize=9.5, loc="left")
    ax.tick_params(axis="x", labelsize=7.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    caption = _wrap(
        f"The block is the unit: one paper x benchmark x split x metric x model, so one team, one "
        f"protocol and one model are held fixed by construction. The binding constraint is not the "
        f"number of blocks ({counts['blocks_after_ablation']:,} of them survive) but ATTRIBUTION: "
        f"only {counts['attributed_comparator_arms']:,} of "
        f"{counts['attributed_comparator_arms'] + counts['anonymous_comparator_arms']:,} comparator "
        f"arms carry a name that resolves to a coded system at the conservative threshold, because "
        f"a baseline table mostly names bare models, paper-internal configurations and ablations "
        f"rather than third-party harnesses. An unattributed arm is kept in the block as an "
        f"anonymous comparator - it establishes the protocol's difficulty and it enters the "
        f"within-block standardisation - but it carries no design vector, so it cannot enter a "
        f"contrast. " + OWN_ARM_CAVEAT + " " + DRIFT_CAVEAT, width=150)
    fig.text(0.0, -0.06, caption, fontsize=6.6, va="top", ha="left", color="#374151")
    return _save(fig, out_stem)


def figure_own_arm_rank(blocks: pd.DataFrame, own: dict, out_stem: Path) -> list[Path]:
    """The own-arm win rate: the measurement of the practice that biases every table in the corpus."""
    import matplotlib.pyplot as plt

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.0, 4.2),
                                 gridspec_kw={"width_ratios": [1.25, 1.0]})
    sizes = sorted(own["by_arms"])
    observed = [own["by_arms"][s]["share_first"] for s in sizes]
    chance = [own["by_arms"][s]["chance_share"] for s in sizes]
    chance_unc = [own["by_arms"][s]["chance_share_uncorrected"] for s in sizes]
    n_blocks = [own["by_arms"][s]["blocks"] for s in sizes]
    x = np.arange(len(sizes))
    ax.bar(x - 0.27, observed, width=0.26, color="#1f4e79", label="observed: own arm ranks first")
    ax.bar(x, chance, width=0.26, color="#9ca3af",
           label="chance over the arms that are not the paper's own ablations")
    ax.bar(x + 0.27, chance_unc, width=0.26, facecolor="none", edgecolor="#9ca3af", lw=0.8,
           hatch="///", label="uncorrected chance (1 / all arms), superseded")
    for i, (obs, nb) in enumerate(zip(observed, n_blocks)):
        ax.annotate(f"{obs:.0%}\nn={nb}", xy=(i - 0.27, obs), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=7, color="#374151")
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in sizes], fontsize=8)
    ax.set_xlabel("arms in the block (the authors' arm included)", fontsize=8)
    ax.set_ylabel("share of blocks where the authors' arm ranks first", fontsize=8)
    ax.set_ylim(0, 1.22)
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    ax.set_title("by block size", fontsize=8.5, loc="left")
    big = own.get("five_plus_arms") or {}
    fig.suptitle(_wrap(
        f"The authors' own arm ranks first in {own['own_first']} of {own['blocks_with_own_arm']} "
        f"blocks ({own['share_first']:.0%}) against "
        f"{own['expected_by_chance']:.2f} expected once the paper's own ablation arms are removed "
        f"from the chance baseline: exact p = {own['exact_poisson_binomial_p']:.3f}, "
        f"paper-clustered p = {own['paper_clustered']['p']:.3f}, so the overall advantage does not "
        f"survive. What survives is the 5+-arm subgroup, {big.get('own_first', 0)} of "
        f"{big.get('blocks', 0)} against {big.get('expected_by_chance', float('nan')):.2f} "
        f"expected, p = {big.get('exact_poisson_binomial_p', float('nan')):.1e}", width=118),
        fontsize=9.0, x=0.02, ha="left")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    with_own = blocks[blocks["has_own_arm"]]
    if len(with_own):
        bx.hist(with_own["own_z_all"].dropna(), bins=16, color="#b45309", alpha=0.85)
        bx.axvline(0.0, color="#333333", lw=0.9, ls="--")
        bx.set_xlabel("within-block standardised score of the authors' own arm (z over all arms)",
                      fontsize=8)
        bx.set_ylabel("blocks", fontsize=8)
        bx.set_title("distribution over blocks", fontsize=8.5, loc="left")
    for side in ("top", "right"):
        bx.spines[side].set_visible(False)
    caption = _wrap(
        "This figure is not a result about harness design: it is the measurement of the practice "
        "that makes the own-arm-inclusive estimates untrustworthy. A baseline table is written to "
        "show the authors' system winning, and in the largest tables it does - but the overall share "
        "no longer beats its chance baseline once that baseline stops counting the paper's own "
        "switched-off configurations as rival comparators, and the surviving 5+-arm result is best "
        "read as evidence that a large arm table in this literature is largely the paper's own "
        "ablation table. " + OWN_ARM_CHANCE_CAVEAT + " " + OWN_ARM_CAVEAT + " " + DRIFT_CAVEAT,
        width=150)
    fig.text(0.0, -0.10, caption, fontsize=6.6, va="top", ha="left", color="#374151")
    return _save(fig, out_stem)


def figure_contrasts(pairs: list[tuple[dict, dict]], out_stem: Path) -> list[Path]:
    """Forest plot: each contrast twice - comparator arms only (headline) and with the own arm."""
    import matplotlib.pyplot as plt

    rows: list[tuple[dict, bool]] = []
    for primary, secondary in pairs:
        rows.append((secondary, False))
        rows.append((primary, True))
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(12.5, 0.85 * len(rows) + 4.4))
    for y, (est, is_primary) in enumerate(rows):
        colour = "#1f4e79" if is_primary else "#b45309"
        has_interval = est["estimable"] and not est["degenerate_interval"] and not np.isnan(
            est["ci_low"])
        if est["block_differences"]:
            ax.scatter(est["block_differences"], [y + 0.22] * len(est["block_differences"]),
                       s=14, color="#94a3b8", zorder=2, alpha=0.9)
        if has_interval:
            mde = est["mde_80"]
            if not np.isnan(mde):
                ax.add_patch(plt.Rectangle(
                    (-mde, y - 0.28), 2 * mde, 0.42,
                    color="#fde68a" if est["only_large_detectable"] else "#e5e7eb",
                    alpha=0.6, zorder=1, lw=0))
            ax.plot([est["ci_low"], est["ci_high"]], [y, y], color=colour, lw=2.2, zorder=3,
                    solid_capstyle="butt")
            ax.scatter([est["effect"]], [y], s=58, zorder=4, color="#ffffff", edgecolors=colour,
                       linewidths=1.8)
            perm = est["permutation"]
            label = (
                f"{est['effect']:+.2f}  [{est['ci_low']:+.2f}, {est['ci_high']:+.2f}]   "
                f"K={est['n_blocks']} blocks / {est['n_papers']} papers, {est['n_arms']} arms, "
                f"{est['n_systems']} systems   MDE(80%)=+-{est['mde_80']:.2f}   "
                f"perm p={_fmt_p(perm['p_two_sided'], 1.0 / (perm['n_draws'] + 1))} "
                f"(floor >={max(perm['p_min_attainable'], 1e-4):.4f})"
                + ("   DETECTED" if est["detected"] else "   NULL")
                + ("   FRAGILE" if est["fragile"] else "")
                + ("   ONE PAPER ONLY" if est.get("single_paper") else ""))
        else:
            ax.scatter([est["effect"]], [y], s=50, marker="x", color="#9ca3af", zorder=4)
            reason = ("zero between-block spread" if est["degenerate_interval"]
                      else f"varies in only {est['n_blocks']} block(s)")
            label = (f"{est['effect']:+.2f}, NO INTERVAL - {reason}; K={est['n_blocks']} blocks, "
                     f"{est['n_arms']} arms, {est['n_systems']} systems")
            if est.get("permutation", {}).get("available"):
                label += f"   design floor p>={est['permutation']['p_min_attainable']:.3f}"
        ax.annotate(label, xy=(1.005, y), xycoords=("axes fraction", "data"), va="center",
                    ha="left", fontsize=6.6, color="#374151")
    ax.axvline(0.0, color="#111827", lw=0.9, zorder=2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(
        [(f"{e['name']} ({e['dimension_id']})  "
          + ("comparator arms only" if p else "incl. authors' arm (BIASED)"))
         for e, p in rows], fontsize=7.6, family="DejaVu Sans Mono")
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel("within-block difference in standardised score, exposed minus reference "
                  "(positive = better on the block's metric)", fontsize=8)
    ax.set_title(
        "Pre-specified harness-design contrasts inside one paper's own comparison table\n"
        "Blue: the headline, comparator arms only, the authors' own arm excluded. Amber: the same "
        "contrast with the authors' arm included - OPTIMISTICALLY BIASED, shown for comparison "
        "only.\nOpen circle: mean of block-level differences. Bar: percentile bootstrap CI "
        "resampling BLOCKS. Shaded band: +- the minimum detectable effect at 80% power (amber band "
        "= only a large effect was detectable).\nSmall grey dots: the individual block-level "
        "differences the estimate is made of.", fontsize=8.6, loc="left")
    ax.tick_params(axis="x", labelsize=7.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    caption = _wrap(
        "All contrasts were fixed as a set before estimation and all are reported, including the "
        "null ones and the ones the data cannot support; nothing was dropped for its result. A block "
        "contributes only if the contrast varies inside it, which is what makes each estimate a "
        "within-block one, and the paper is the blocking factor. A CI covering zero means no "
        "detectable association at this block count - read it with the minimum detectable effect on "
        "the same line, which is what could have been found. " + OWN_ARM_CAVEAT + " "
        + DRIFT_CAVEAT, width=152)
    powers = "\n".join(_wrap("  - " + e["power_sentence"], width=152)
                       for e, _p in rows[::-1])
    fig.text(0.0, -0.012, caption + "\n\nPower, computed from the observed between-block spread and "
             "from the design itself:\n" + powers, fontsize=6.5, va="top", ha="left",
             color="#374151")
    return _save(fig, out_stem)


# --------------------------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------------------------
def block_report(blocks: pd.DataFrame, limit: int = 12) -> str:
    """The largest blocks in brief, for the console."""
    lines = [(f"{'block (paper | benchmark | split | metric | model)':78s} {'arms':>4s} "
              f"{'attr':>4s} {'own':>4s} {'spread':>7s}")]
    for row in blocks.head(limit).itertuples():
        lines.append(
            f"{row.block[:78]:78s} {row.n_arms:4d} {row.n_attributed:4d} "
            f"{('yes' if row.has_own_arm else '-'):>4s} {row.spread:7.1f}")
    if len(blocks) > limit:
        lines.append(f"... {len(blocks) - limit} further blocks; full table in "
                     "data/analysis/blocks_summary.csv")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rejects", type=Path, default=REJECTS)
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--evidence", type=Path, default=EVIDENCE)
    ap.add_argument("--systems", type=Path, default=SYSTEMS)
    ap.add_argument("--candidates", type=Path, default=CANDIDATES)
    ap.add_argument("--fig-dir", type=Path, default=FIG_DIR)
    ap.add_argument("--tab-dir", type=Path, default=TAB_DIR)
    ap.add_argument("--fuzzy-threshold", type=int, default=LB.FUZZY_THRESHOLD,
                    help=f"name-match threshold for attribution (default {LB.FUZZY_THRESHOLD}; the "
                         "registry's own grouping threshold is 92 and is deliberately not used)")
    ap.add_argument("--rank-threshold", type=int, default=4,
                    help="blocks with fewer arms than this are standardised by rank, not z")
    ap.add_argument("--agg", default="median", choices=("median", "mean", "max"),
                    help="how to collapse several rows of one arm inside one block")
    ap.add_argument("--min-blocks", type=int, default=3,
                    help="minimum blocks in which a contrast must vary before an interval is given")
    ap.add_argument("--n-boot", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=20260924)
    ap.add_argument("--top-vetoes", type=int, default=12)
    ap.add_argument("--no-render", action="store_true", help="skip figures, print numbers only")
    ap.add_argument("--aliases", type=Path, default=ALIASES,
                    help="vetted comparator alias table (paper-corroborated); used when present")
    ap.add_argument("--no-aliases", action="store_true",
                    help="ignore the alias table, for the pre-alias comparison in the paper")
    args = ap.parse_args(argv)

    comparators = load_comparators(args.rejects)
    own = load_own_arms(args.results, args.evidence)
    codings = load_codings(args.systems)
    attributor = Attributor(threshold=args.fuzzy_threshold, systems_path=args.systems,
                            candidates_path=args.candidates)
    if not args.no_aliases and args.aliases and args.aliases.exists():
        # Imported lazily: build_alias_table imports this module, so a top-level import would cycle.
        from build_alias_table import AliasAttributor, load_alias_table
        aliases = load_alias_table(args.aliases)
        attributor = AliasAttributor(threshold=args.fuzzy_threshold, systems_path=args.systems,
                                     candidates_path=args.candidates, aliases=aliases)
        print(f"using alias table {args.aliases.name} ({len(aliases)} paper-scoped entries)")

    arms_all = build_arm_table(comparators, own, attributor, agg=args.agg)
    arms_blocks, dropped_single = drop_single_arm_blocks(arms_all)
    blocks_raw = arms_blocks["block"].nunique()
    arms_kept, arms_routed, ablation_stats = split_ablation_blocks(arms_blocks)
    # A block whose comparators were all ablations may still hold the paper's own arm; after routing
    # it out the remainder can fall back to a single arm, so the drop rule is applied again.
    arms_kept, dropped_single_again = drop_single_arm_blocks(arms_kept)
    arms = annotate_blocks(arms_kept, rank_threshold=args.rank_threshold)
    blocks = block_summary(arms)
    own_stats = own_arm_first_stats(blocks)

    comparator_arms = arms[arms["role"] == "comparator"]
    per_block_attr = comparator_arms[comparator_arms["system_id"] != ""].groupby(
        "block")["system_id"].nunique() if len(comparator_arms) else pd.Series(dtype=int)
    # Reconciles this run with the measurement quoted in the task: blocks holding two or more
    # comparator ROWS, before rows of one arm are collapsed and before any block is routed out.
    comparator_row_blocks = comparators.apply(
        lambda r: block_key(r["record_id"], r["benchmark"], r["split"], r["metric"], r["model"]),
        axis=1) if len(comparators) else pd.Series(dtype=str)
    row_block_sizes = comparator_row_blocks.value_counts() if len(comparators) else pd.Series(
        dtype=int)
    counts = {
        "comparator_rows": len(comparators),
        "comparator_row_papers": int(comparators["record_id"].nunique()),
        "blocks_two_plus_comparator_rows": int((row_block_sizes >= 2).sum()),
        "rows_in_blocks_two_plus_comparator_rows": int(
            row_block_sizes[row_block_sizes >= 2].sum()),
        "own_rows": len(own),
        "own_rows_dropped_no_record": int(own.attrs.get("dropped_no_record", 0)),
        "arms_total": len(arms_all),
        "blocks_total": int(arms_all["block"].nunique()),
        "blocks_dropped_single_arm": dropped_single + dropped_single_again,
        "blocks_raw": int(blocks_raw),
        "arms_in_blocks_raw": len(arms_blocks),
        "blocks_routed_ablation": ablation_stats["blocks_routed"],
        "arms_routed_ablation": ablation_stats["arms_routed"],
        "ablation_patterns": ablation_stats["patterns"],
        "blocks_after_ablation": int(arms["block"].nunique()),
        "arms_after_ablation_routing": len(arms),
        "blocks_estimable": int(blocks["estimable_block"].sum()) if len(blocks) else 0,
        "blocks_excluded_mixed_scale": int((blocks["exclusion_reason"] == "mixed_scale").sum())
                                       if len(blocks) else 0,
        "blocks_excluded_unknown_direction": int(
            (blocks["exclusion_reason"] == "metric_direction_unknown").sum()) if len(blocks) else 0,
        "arms_estimable_blocks": int(arms["estimable_block"].sum()) if len(arms) else 0,
        "attributed_arms": int((arms["system_id"] != "").sum()) if len(arms) else 0,
        "attributed_comparator_arms": int((comparator_arms["system_id"] != "").sum()),
        "anonymous_comparator_arms": int((comparator_arms["system_id"] == "").sum()),
        "distinct_coded_systems_attributed": int(
            arms.loc[arms["system_id"] != "", "system_id"].nunique()) if len(arms) else 0,
        "distinct_coded_systems_among_comparators": int(
            comparator_arms.loc[comparator_arms["system_id"] != "", "system_id"].nunique())
            if len(comparator_arms) else 0,
        "own_variant_arms": int((arms["role"] == "own_variant").sum()) if len(arms) else 0,
        "blocks_two_attributed_comparators": int((per_block_attr >= 2).sum()),
        "blocks_with_own_arm": int(blocks["has_own_arm"].sum()) if len(blocks) else 0,
        "papers": int(blocks["record_id"].nunique()) if len(blocks) else 0,
        "benchmarks": int(blocks["benchmark"].nunique()) if len(blocks) else 0,
    }

    print("=" * 100)
    print("HARNESS-DB within-paper block analysis (RQ3, Phase 7 task 49b). Associational only.")
    print("=" * 100)
    print()
    print("WHAT A BLOCK IS: one paper x benchmark x split x metric x model - one team, one protocol,")
    print("one model, one run date. The evidence is the paper's own comparison table.")
    print()
    print("BLOCK CONSTRUCTION")
    print(f"  comparator rows (results_rejects.csv, not_own_system, numeric score) "
          f"{counts['comparator_rows']:>6,}   from {counts['comparator_row_papers']} papers")
    print(f"  the papers' own rows (results.csv, source=paper, paper recovered)  "
          f"{counts['own_rows']:>6,}   "
          f"({counts['own_rows_dropped_no_record']} dropped: paper not recoverable)")
    print(f"  arms after collapsing rows of one arm in one block ({args.agg})       "
          f"{counts['arms_total']:>6,}   in {counts['blocks_total']:,} blocks")
    print(f"  blocks dropped for holding a single arm                            "
          f"{counts['blocks_dropped_single_arm']:>6,}")
    print(f"  blocks with 2+ arms                                               "
          f"{counts['blocks_raw']:>6,}   {counts['arms_in_blocks_raw']:,} arms")
    print(f"    (of which blocks holding 2+ comparator ROWS, pre-collapse       "
          f"{counts['blocks_two_plus_comparator_rows']:>6,}   "
          f"{counts['rows_in_blocks_two_plus_comparator_rows']:,} rows - the measurement this "
          "analysis was scoped on)")
    print(f"  routed out as all-comparators-are-ablations (analyse_ablations.py) "
          f"{counts['blocks_routed_ablation']:>6,}   "
          f"{counts['arms_routed_ablation']:,} arms; patterns: "
          + ", ".join(f"{k}={v}" for k, v in sorted(ablation_stats['patterns'].items())))
    print(f"  BLOCKS ANALYSED                                                   "
          f"{counts['blocks_after_ablation']:>6,}   "
          f"{counts['arms_after_ablation_routing']:,} arms, {counts['papers']} papers, "
          f"{counts['benchmarks']} distinct benchmark strings")
    print(f"    of which usable for estimation                                  "
          f"{counts['blocks_estimable']:>6,}   "
          f"(excluded: {counts['blocks_excluded_mixed_scale']} mixing a 0-1 and a 0-100 scale, "
          f"{counts['blocks_excluded_unknown_direction']} with no recorded metric)")
    print()
    print("ATTRIBUTION OF RIVAL NAMES TO CODED SYSTEMS (conservative; abstention is the default)")
    print(f"  distinct comparator labels seen                    "
          f"{len(attributor.table()):>6,}")
    print(f"  comparator arms attributed to a coded system       "
          f"{counts['attributed_comparator_arms']:>6,}   "
          f"({counts['distinct_coded_systems_among_comparators']} distinct coded systems; "
          f"{counts['own_variant_arms']} further arms resolved to the reporting paper's OWN system "
          "and count as its arm, not a rival's)")
    print(f"  anonymous comparator arms (kept in the block)      "
          f"{counts['anonymous_comparator_arms']:>6,}   "
          "they carry no design vector but do establish the protocol's difficulty")
    print(f"  blocks with 2+ attributed comparator arms          "
          f"{counts['blocks_two_attributed_comparators']:>6,}   "
          "<- the ceiling on every own-arm-free contrast below")
    print(f"  blocks holding the authors' own arm                "
          f"{counts['blocks_with_own_arm']:>6,}")
    if attributor.abstentions:
        print("  abstentions by kind:")
        for kind, n in attributor.abstentions.most_common():
            print(f"    {kind:28s} {n:>6,}")
    if attributor.vetoes:
        print(f"  matches refused by a veto or as ambiguous ({len(attributor.vetoes)} distinct):")
        for reason, n in attributor.vetoes.most_common(args.top_vetoes):
            print(f"    {n:>4,}x {reason[:150]}")
    if attributor.census_hints:
        print(f"  census-only systems a label matched but systems.json does not hold "
              f"({len(attributor.census_hints)} distinct; the list worth adding):")
        for hint, n in attributor.census_hints.most_common(5):
            print(f"    {n:>4,}x {hint[:140]}")
    print()
    print("THE BLOCKS (largest first)")
    print(block_report(blocks))
    print()
    print("HOW OFTEN THE AUTHORS' OWN ARM RANKS FIRST IN ITS OWN TABLE")
    print(f"  blocks holding the authors' own arm  {own_stats['blocks_with_own_arm']:>5,}"
          f"   from {own_stats['papers']} papers, carrying "
          f"{own_stats['n_ablation_arms']} ablation arms")
    print(f"  own arm ranks first                  {own_stats['own_first']:>5,}   "
          f"({own_stats['share_first']:.1%}); tied first in {own_stats['own_tied_first']}")
    print(f"  mean rank of the own arm             {own_stats['mean_own_rank']:>5.2f}   "
          f"mean standardised score {own_stats['mean_own_z']:+.2f} sd")
    print("  PRIMARY, chance = 1/(arms that are not the paper's own ablations):")
    print(f"    expected {own_stats['expected_by_chance']:.2f}, exact Poisson-binomial p = "
          f"{own_stats['exact_poisson_binomial_p']:.4g}")
    pc = own_stats["paper_clustered"]
    print(f"    paper-clustered Monte Carlo p = {pc['p']:.4g} ({pc['draws']:,} draws, seed "
          f"{pc['seed']}, one draw per paper over {pc['papers']} papers)")
    obp = own_stats["one_block_per_paper"]
    print(f"    one block per paper: {obp['own_first']}/{obp['blocks']} vs "
          f"{obp['expected_by_chance']:.2f} expected, exact p = "
          f"{obp['exact_poisson_binomial_p']:.4g} ({obp['rule']})")
    big = own_stats.get("five_plus_arms") or {}
    if big:
        print(f"    blocks with 5+ arms: {big['own_first']}/{big['blocks']} vs "
              f"{big['expected_by_chance']:.2f} expected, exact p = "
              f"{big['exact_poisson_binomial_p']:.4g}   <- the one result that survives")
    unc = own_stats["uncorrected"]
    print("  UNCORRECTED variant, kept for audit only (chance = 1/n_arms, which counts the paper's")
    print("  own switched-off configurations as independently chosen rivals):")
    print(f"    expected {unc['expected_by_chance']:.2f}, exact p = "
          f"{unc['exact_poisson_binomial_p']:.4g}; 5+ arms expected "
          f"{unc['five_plus_arms'].get('expected_by_chance', float('nan')):.2f}, exact p = "
          f"{unc['five_plus_arms'].get('exact_poisson_binomial_p', float('nan')):.4g}")
    for n_arms in sorted(own_stats["by_arms"]):
        row = own_stats["by_arms"][n_arms]
        print(f"    blocks with {n_arms:2d} arms: {row['blocks']:4d}, own arm first "
              f"{row['own_first']:4d} ({row['share_first']:.0%}; chance "
              f"{row['chance_share']:.0%}, uncorrected {row['chance_share_uncorrected']:.0%}; "
              f"{row['ablation_arms']} ablation arms)")
    print("  This is a measurement of the reporting practice, not of any design. It is also the")
    print("  reason the own-arm-inclusive estimates below are labelled optimistically biased.")
    print("  The overall share does NOT beat its corrected chance baseline; the 5+-arm subgroup does,")
    print("  and the reading of that is that large arm tables here are largely own-ablation tables.")
    print()
    print("PRE-SPECIFIED CONTRASTS, PAPER AS THE BLOCKING FACTOR")
    print("  (a) headline: comparator arms only, the authors' own arm EXCLUDED")
    print("  (b) beside it: the same contrast with the authors' arm INCLUDED - biased, for contrast")
    pairs: list[tuple[dict, dict]] = []
    for contrast in CONTRASTS:
        primary = estimate_contrast(arms, contrast, codings, include_own=False,
                                    n_boot=args.n_boot, seed=args.seed,
                                    min_blocks=args.min_blocks)
        secondary = estimate_contrast(arms, contrast, codings, include_own=True,
                                      n_boot=args.n_boot, seed=args.seed,
                                      min_blocks=args.min_blocks)
        pairs.append((primary, secondary))
        print(f"\n  {contrast.name}  ({contrast.dimension_id} {contrast.dimension})"
              + (f"   [mirrors analyse_outcomes contrast '{contrast.mirrors}']"
                 if contrast.mirrors else "   [no cross-paper twin]"))
        print(f"    exposed   : {contrast.exposed_label}")
        print(f"    reference : {contrast.reference_label}")
        for tag, est in (("(a) own arm EXCLUDED ", primary), ("(b) own arm included ", secondary)):
            perm = est.get("permutation", {})
            head = (f"    {tag}: {est['n_blocks']} blocks / {est['n_papers']} papers, "
                    f"{est['n_arms']} arms, {est['n_systems']} systems "
                    f"({est['n_exposed_arms']} exposed / {est['n_reference_arms']} reference)")
            print(head)
            if est["estimable"] and not est["degenerate_interval"] and not np.isnan(est["ci_low"]):
                print(f"        effect {est['effect']:+.3f} sd  95% CI "
                      f"[{est['ci_low']:+.3f}, {est['ci_high']:+.3f}] "
                      f"(percentile bootstrap resampling {est['n_blocks']} BLOCKS, "
                      f"{est['n_boot']:,} draws, seed {est['seed']})")
                if not np.isnan(est["ci_low_paper"]):
                    print(f"        paper-clustered CI [{est['ci_low_paper']:+.3f}, "
                          f"{est['ci_high_paper']:+.3f}] (resampling the "
                          f"{est['n_papers']} PAPERS, since blocks are nested in papers)")
                print(f"        MDE(80%) +-{est['mde_80']:.3f} sd   se {est['se']:.3f}")
            elif est["estimable"]:
                print(f"        effect {est['effect']:+.3f} sd, NO INTERVAL - "
                      f"{est.get('degenerate_reason', 'zero between-block spread')}")
            else:
                print(f"        effect {est['effect']:+.3f} sd (descriptive only, no interval): "
                      f"{est['not_estimable_reason']}")
            if perm.get("available"):
                print(f"        perm test within block: two-sided p="
                      f"{_fmt_p(perm['p_two_sided'], 1.0 / (perm['n_draws'] + 1))} "
                      f"({perm['mode']}, {perm['n_draws']:,} draws); DESIGN FLOOR p>="
                      f"{max(perm['p_min_attainable'], 1e-4):.4f} from "
                      f"{perm['n_assignments']:,} possible label assignments"
                      + ("  <- above 0.05: no significance is reachable"
                         if perm["floor_above_05"] else ""))
            if est["blocks"]:
                print("        per block: " + ", ".join(
                    f"{b['block'].split('|')[0]}/{b['benchmark'][:18]} d={b['d']:+.2f} "
                    f"({b['n_exposed']}v{b['n_reference']}, {b['std_method']})"
                    for b in est["blocks"][:8])
                    + (" ..." if len(est["blocks"]) > 8 else ""))
        print("    finding   : " + finding_line(primary, secondary))
        print(f"    power     : {primary['power_sentence']}")
        print(f"    mechanism : {contrast.mechanism}")
        print(f"    drift     : attenuation risk {contrast.drift_exposure}; the estimate is a "
              "lower bound on magnitude")

    print()
    print("HOW THIS COMPARES WITH THE CROSS-PAPER ANALYSIS")
    print(_wrap(
        f"  scripts/analyse_outcomes.py reaches 36 cross-paper keys / 53 systems on "
        f"benchmark|split|model. This script reaches {counts['blocks_after_ablation']:,} "
        f"within-paper blocks covering {counts['arms_after_ablation_routing']:,} arms and "
        f"{counts['papers']} papers - far more comparisons, and better controlled, since a block "
        f"holds one team and one protocol fixed. The constraint moves, though: only "
        f"{counts['attributed_comparator_arms']:,} comparator arms resolve to a coded system, so "
        f"{counts['blocks_two_attributed_comparators']} blocks carry two or more coded comparator "
        f"arms, and that - not the block count - is what bounds every own-arm-free contrast. A "
        f"baseline table names bare models, paper-internal configurations and ablations far more "
        f"often than it names a third-party harness.", width=112))
    print()
    print(_wrap("  " + OWN_ARM_CAVEAT, width=112))
    print(_wrap("  " + DRIFT_CAVEAT, width=112))

    # ---- machine-readable outputs -----------------------------------------------------------
    args.tab_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    arms_out = args.tab_dir / "blocks_arms.csv"
    arms.to_csv(arms_out, index=False)
    written.append(arms_out)
    blocks_out = args.tab_dir / "blocks_summary.csv"
    blocks.to_csv(blocks_out, index=False)
    written.append(blocks_out)
    routed_out = args.tab_dir / "blocks_ablation_routed.csv"
    arms_routed.to_csv(routed_out, index=False)
    written.append(routed_out)
    attr_out = args.tab_dir / "blocks_attribution.csv"
    attributor.table().to_csv(attr_out, index=False)
    written.append(attr_out)

    contrast_rows = []
    for primary, secondary in pairs:
        for est in (primary, secondary):
            contrast_rows.append({
                "contrast": est["name"],
                "dimension_id": est["dimension_id"],
                "dimension": est["dimension"],
                "own_arm_included": est["include_own_arm"],
                "arm_policy": est["arm_policy"],
                "estimable": est["estimable"],
                "effect_sd": est["effect"],
                "ci_low": est["ci_low"],
                "ci_high": est["ci_high"],
                "ci_low_paper_cluster": est["ci_low_paper"],
                "ci_high_paper_cluster": est["ci_high_paper"],
                "mde_80": est["mde_80"],
                "n_blocks": est["n_blocks"],
                "n_papers": est["n_papers"],
                "n_arms": est["n_arms"],
                "n_systems": est["n_systems"],
                "n_exposed_arms": est["n_exposed_arms"],
                "n_reference_arms": est["n_reference_arms"],
                "detected": est["detected"],
                "null_result": est["null"],
                "fragile": est["fragile"],
                "single_paper": est.get("single_paper", False),
                "few_papers": est.get("few_papers", False),
                "degenerate_interval": est["degenerate_interval"],
                "ci_perm_disagreement": est["disagreement"],
                "only_large_detectable": est["only_large_detectable"],
                "perm_p": est.get("permutation", {}).get("p_two_sided"),
                "perm_p_design_floor": est.get("permutation", {}).get("p_min_attainable"),
                "perm_floor_above_05": est.get("permutation", {}).get("floor_above_05"),
                "mirrors_cross_paper_contrast": est["mirrors_cross_paper_contrast"],
                "drift_exposure": est["drift_exposure"],
                "finding": finding_line(primary, secondary),
            })
    contrasts_out = args.tab_dir / "blocks_contrasts.csv"
    pd.DataFrame(contrast_rows).to_csv(contrasts_out, index=False)
    written.append(contrasts_out)

    summary = {
        "generated_from": {
            "rejects": str(args.rejects.name),
            "results": str(args.results.name),
            "evidence": str(args.evidence.name),
            "systems": str(args.systems.name),
        },
        "unit": "block = one paper x benchmark x split x metric x model",
        "counts": counts,
        "own_arm_ranks_first": own_stats,
        "attribution": {
            "fuzzy_threshold": args.fuzzy_threshold,
            "registry_threshold_not_used": 92,
            "distinct_labels": len(attributor.table()),
            "abstentions_by_kind": {k: int(v) for k, v in attributor.abstentions.items()},
            "vetoes": {k: int(v) for k, v in attributor.vetoes.most_common(50)},
            "census_only_hits": {k: int(v) for k, v in attributor.census_hints.most_common(50)},
        },
        "standardisation": {
            "rank_threshold": args.rank_threshold,
            "rule": "z=(x-mean)/sd (ddof=1) at or above the threshold; standardised average rank "
                    "below it; 0 when every value in the block is equal - identical to "
                    "analyse_outcomes.standardise_within_key",
            "row_aggregation": args.agg,
            "two_standardisations": "z_comp over comparator arms only (headline); z_all over every "
                                    "arm including the authors' own (biased version)",
            "methods_used_all": {k: int(v) for k, v in arms["std_method_all"].value_counts().items()}
                                if len(arms) else {},
        },
        "bootstrap": {"unit": "block", "secondary_unit": "paper", "draws": args.n_boot,
                      "seed": args.seed},
        "own_arm_caveat": OWN_ARM_CAVEAT,
        "own_arm_chance_caveat": OWN_ARM_CHANCE_CAVEAT,
        "drift_caveat": DRIFT_CAVEAT,
        "contrasts": [{"primary_comparators_only": p, "secondary_with_own_arm": s}
                      for p, s in pairs],
    }
    summary_out = args.tab_dir / "blocks_summary.json"
    summary_out.write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    written.append(summary_out)

    if not args.no_render:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams["font.family"] = "DejaVu Sans"
        written += figure_block_funnel(counts, args.fig_dir / "blocks_funnel")
        if own_stats["blocks_with_own_arm"]:
            written += figure_own_arm_rank(blocks, own_stats, args.fig_dir / "blocks_own_arm_rank")
        written += figure_contrasts(pairs, args.fig_dir / "blocks_contrasts")
    print()
    for path in written:
        try:
            print(f"wrote {path.relative_to(ROOT)}")
        except ValueError:
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
