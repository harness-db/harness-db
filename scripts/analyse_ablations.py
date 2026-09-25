#!/usr/bin/env python
"""Meta-analysis of PUBLISHED ABLATIONS: the strongest evidence this review has for RQ3 (Phase 7).

WHY THIS SCRIPT EXISTS
----------------------
`scripts/analyse_outcomes.py` answers RQ3 ("does harness design affect task outcomes") from
cross-paper leaderboard comparisons, and says honestly what that can carry: ~143 rows inside ~36
comparable keys over ~53 systems, no mixed model identifiable, every estimate a LOWER bound because
of scaffold drift (`docs/benchmark_caveats.md` sec. 5) and self-selected reporting (sec. 3).

There is a second body of evidence in the harvest that is *better identified* and was being thrown
away. `scripts/extract_results.py` rejects a row with `reason=not_own_system` whenever the row's
`reported_system_name` is not the paper's own system. 3,280 rows were rejected that way, and a large
minority of those labels are not rival systems at all - they are the paper's OWN ablations and
variants: "Ours w/o memory", "w/o Planner", "Single agent", "- verification", "Ret Expert only".

An ablation row and the paper's own full-system row for the SAME benchmark, split, metric and base
model form a CONTROLLED WITHIN-STUDY CONTRAST: one team, one codebase, one evaluation harness, one
scoring script, one component deliberately switched off. Nothing in the cross-paper data is that
clean. Pooling those contrasts by design dimension is the standard way to get a component-level
effect that the observational data cannot give.

Four of the five cross-cutting caveats in `docs/benchmark_caveats.md` are ABSORBED by that design,
and saying which is half the argument for this script. Versioning (sec. 1) and scaffold drift
(sec. 5) cannot bite, because both arms of a contrast are the same codebase at the same commit,
measured in the same experiment - the confound that "most threatens the regression" in
`analyse_outcomes.py` is definitionally absent here. Contamination (sec. 2) is shared by the two
arms and differences it out. Harness-model entanglement (sec. 4) is held fixed by requiring the same
base model on both arms. What is left is sec. 3, self-reporting, and it is not merely left - it is
concentrated, because an ablation table is the most self-serving table in a paper.

AND WHY ITS ANSWER IS AN UPPER BOUND
------------------------------------
The mirror image of `analyse_outcomes.py`. There, measurement error on the design variable
attenuates effects towards zero, so estimates are lower bounds. Here the problem is the opposite and
it is selection, not attenuation: *authors run an ablation in order to show that their component
helps*, and they report the ablation table when it comes out the way the paper needs. A contrast
that showed the component was useless is a contrast that stayed in a lab notebook or was folded into
a sentence with no number. So the pooled effect per dimension is an UPPER BOUND on the causal
contribution of that component in that system, and a badly biased one if the sign distribution says
so. Section 4 of this script's output does not *mention* that threat, it measures it: funnel plot,
Egger's regression, trim-and-fill, a Copas-style null-fill bound, and the share of contrasts whose
sign favours the authors' own component. Every figure caption carries the bound.

Three further limits, stated once and repeated in the outputs:

* **the effect is conditional on the host system.** "Removing long-term memory costs X%" is measured
  inside the systems whose authors chose to ablate memory, on the benchmarks they chose. It is not
  the effect of adding memory to an arbitrary harness.
* **the effect is confounded with implementation quality.** An ablation removes one team's
  implementation of a component, not the component.
* **no sampling variances are published.** Papers report a point score, not a standard error, so the
  within-contrast variance here is APPROXIMATED (see `contrast_variance`) and the pooled interval is
  only as good as that approximation. An equal-weight paper-level mean with a t interval is reported
  beside every inverse-variance pooled estimate as the assumption-light check, and `--sensitivity`
  re-runs the pooling at other assumed benchmark sizes.

WHAT IT DOES, IN ORDER
----------------------
1. `load_candidates` - the `not_own_system` rejects whose label or extractor note looks like an
   ablation or a variant (a deliberately wide net; the model does the judging, not the regex).
2. `classify_labels` - ONE model call per batch of labels, the only model use in this script. For
   each (system, label) it returns a category (`ablation`, `augmentation`, `own_full_alias`,
   `rival_system`, `non_harness_baseline`, `model_or_training_variant`, `unmapped`), the dimension
   key from `schema/dimensions.json` it removes or changes, a direction, and a confidence. A label
   the model cannot map to a dimension is recorded `unmapped` WITH ITS REASON and excluded from
   pooling. It is never forced into the nearest dimension - a wrongly-mapped contrast would show up
   as a real component effect, which is the one error this analysis must not make. Results are
   cached by (system_id, label) so a re-run costs nothing.
3. `build_contrasts` - pair each ablation row with the paper's own full-system score on the
   IDENTICAL benchmark, split, metric and model. Primary effect measure: the RELATIVE change,
   `(with_component - without_component) / with_component`, because metrics differ across papers.
   Secondary: the raw percentage-point delta, pooled only within a metric family that is on a
   percentage scale and never across metrics. Every pair that cannot be formed is counted with its
   reason (`no_full_row`, `metric_mismatch`, `split_mismatch`, `model_mismatch`,
   `full_score_ambiguous`, `denominator_too_small`, ...) and the counts are published.
4. `pool_by_dimension` - DerSimonian-Laird random effects per dimension, with the number of
   contrasts and the number of independent PAPERS (contrasts from one paper are averaged first: two
   benchmarks in one paper are not two studies), I-squared, and a Higgins-Thompson prediction
   interval. A dimension backed by fewer than `--min-papers` (default 3) papers is reported as
   INSUFFICIENT EVIDENCE with its raw contrasts listed, never pooled.
5. `bias_diagnostics` - per dimension with enough papers: Egger's intercept test, trim-and-fill,
   null-fill sensitivity, sign share with an exact binomial p.
6. figures to `paper/figures/` (SVG + PDF), tables to `data/analysis/`.

Model calls: step 2 only, through `scripts/screen_llm.py::vote_batch_claude_code` or
`scripts/code_system.py::make_api_backend`. Everything else is pandas / numpy / scipy /
statsmodels / matplotlib(Agg). No network anywhere else.

Run: python scripts/analyse_ablations.py --classify          (model call for uncached labels)
     python scripts/analyse_ablations.py                     (cache only, no model call)
     python scripts/analyse_ablations.py --no-render          (numbers only)
     python scripts/analyse_ablations.py --sensitivity        (+ assumed-n sensitivity table)
     python scripts/analyse_ablations.py --corpus --sensitivity
            coded-set + corpus-wide full-text contrasts (scripts/harvest_ablations_corpus.py), with
            a provenance column and Hartung-Knapp intervals beside the z intervals; every output is
            written with a _corpus suffix and the coded-set outputs are left exactly as they are.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
REJECTS = ROOT / "data" / "results_rejects.csv"
RESULTS = ROOT / "data" / "results.csv"
SYSTEMS = ROOT / "data" / "systems.json"
DIMENSIONS = ROOT / "schema" / "dimensions.json"
OUT_DIR = ROOT / "data" / "analysis"
FIG_DIR = ROOT / "paper" / "figures"
CACHE = OUT_DIR / "ablation_label_cache.json"

log = logging.getLogger("analyse_ablations")

# ------------------------------------------------------------------------------------------------
# the caveat that goes in every caption and every output file
# ------------------------------------------------------------------------------------------------
UPPER_BOUND_CAVEAT = (
    "UPPER BOUND. These are the authors' own published ablations, and an ablation is run and "
    "reported in order to show that the component helps: contrasts that came out null are "
    "systematically less likely to have been written down with a number. The pooled effect is "
    "therefore an upper bound on the component's contribution, not an estimate of it. It is also "
    "conditional on the host systems whose authors chose to ablate that component, on the "
    "benchmarks they chose, and on one team's implementation of the component rather than on the "
    "component itself. Papers publish no standard errors, so the within-contrast variance is "
    "approximated (see scripts/analyse_ablations.py::contrast_variance) and the interval inherits "
    "that approximation. Mirror image of scripts/analyse_outcomes.py, whose cross-paper estimates "
    "are lower bounds (docs/benchmark_caveats.md sec. 5)."
)

POOLED_COLUMNS = [
    "dimension", "n_contrasts", "n_papers", "n_systems", "n_benchmarks", "mean_confidence",
    "share_favouring_component", "raw_effects", "pooled", "verdict", "mu_rel", "se", "ci_low",
    "ci_high", "tau2", "i2", "q", "q_p", "pi_low", "pi_high", "mu_fe", "mean_rel_unweighted",
    "ew_ci_low", "ew_ci_high", "mu_pp", "pp_ci_low", "pp_ci_high", "pp_papers", "pp_contrasts",
    "pp_poolable",
]
BIAS_COLUMNS = [
    "dimension", "n_papers", "n_contrasts", "egger_intercept", "egger_t", "egger_p",
    "trimfill_k0", "mu_observed", "mu_filled", "trimfill_ci_low", "trimfill_ci_high",
    "trimfill_shrinkage", "nullfill_shrinkage", "discount", "size_slope", "size_p", "distinct_n",
    "mu_one_null_each", "nulls_to_halve", "nulls_to_ci_crosses_zero",
    "sign_share_papers", "sign_p_papers", "sign_share_contrasts", "sign_p_contrasts",
]
CREDIBLE_COLUMNS = [
    "dimension", "n_papers", "n_contrasts", "mu_rel", "ci_low", "ci_high", "i2",
    "discount_factor", "mu_discounted", "ci_low_discounted", "mu_trimfill",
    "ci_excludes_zero", "ew_ci_excludes_zero", "pi_excludes_zero", "survives_discount",
]
# `--corpus` only: the pooled table gains the Hartung-Knapp interval and the provenance split.
HK_COLUMNS = ["hk_se", "hk_ci_low", "hk_ci_high", "hk_ci_excludes_zero", "hk_narrower_than_z"]
PROVENANCE_COLUMNS = ["n_contrasts_coded", "n_contrasts_corpus", "n_papers_coded", "n_papers_corpus"]
POOLED_COLUMNS_CORPUS = POOLED_COLUMNS + HK_COLUMNS + PROVENANCE_COLUMNS
CREDIBLE_COLUMNS_CORPUS = CREDIBLE_COLUMNS + ["hk_ci_low", "hk_ci_high", "hk_ci_excludes_zero",
                                              "hk_ci_low_discounted", "survives_discount_hk"]
SENSITIVITY_COLUMNS = ["default_n", "dimension", "mu_rel", "ci_low", "ci_high", "i2", "tau2", "n_papers"]

MIN_PAPERS = 3  # below this a dimension is reported unpooled; 2 papers cannot carry a tau-squared.
DEFAULT_N = 200  # assumed benchmark item count when the split size is unknown; see contrast_variance.
SENSITIVITY_N = (50, 200, 800)
ASSUMED_REL_SE = 0.10  # fallback within-contrast relative SE for a metric that is not proportion-like.
BATCH_SIZE = 40
CONF_FLOOR = 0.5  # a classification below this confidence is treated as unmapped.

# Benchmark/split item counts, used only for the variance approximation. Each is the published size
# of the evaluation set; where a size is not known the analysis falls back to --default-n and says so.
BENCHMARK_N: dict[tuple[str, str], int] = {
    ("swe-bench", "verified"): 500,
    ("swe-bench", "lite"): 300,
    ("swe-bench", "test"): 2294,
    ("swe-bench", "multimodal"): 517,
    ("gaia", "validation"): 165,
    ("gaia", "test"): 300,
    ("osworld", "verified"): 369,
    ("osworld", "test"): 369,
    ("webarena", ""): 812,
    ("visualwebarena", ""): 910,
    ("terminal-bench", ""): 80,
    ("humaneval", ""): 164,
    ("mbpp", ""): 500,
    ("gsm8k", "test"): 1319,
    ("math", "test"): 5000,
    ("aime 2024", ""): 30,
    ("aime 2025", ""): 30,
    ("mmlu", "test"): 14042,
    ("hotpotqa", ""): 7405,
    ("alfworld", ""): 134,
    ("webshop", ""): 500,
    ("mind2web", ""): 1013,
    ("scienceworld", ""): 270,
    ("agentbench", ""): 1091,
    ("tau-bench", "airline"): 50,
    ("tau-bench", "retail"): 115,
    ("tau2-bench", "airline"): 50,
    ("tau2-bench", "retail"): 114,
    ("tau2-bench", "telecom"): 114,
}

# Metric polarity. A meta-analysis that pools a success rate and a mean squared error without
# flipping one of them would report the sign of the arithmetic, not the sign of the finding.
HIGHER_IS_BETTER_RE = re.compile(
    r"(?i)\b(acc|acc\.|accuracy|success|sr|pass|pass@\d+|pass\^\d+|resolved|f1|em|exact|"
    r"precision|recall|score|reward|win|wr|bleu|rouge|meteor|correct|solve|completion|"
    r"performance|top-?\d|avg|mean|overall|ex|match|rate|quality|helpful|coverage|yield)\b"
)
LOWER_IS_BETTER_RE = re.compile(
    r"(?i)\b(mse|rmse|mae|mad|error|err|loss|perplexity|ppl|wer|cer|latency|cost|usd|time|"
    r"seconds|steps|turns|tokens|regret|violation|violations|hallucination|failure|fail|"
    r"penalty|overhead|drop)\b"
)
# A metric on a 0-100 (or 0-1) proportion scale: only these may have their raw deltas pooled, and
# only these get the binomial-delta variance.
PROPORTION_RE = re.compile(
    r"(?i)\b(acc|acc\.|accuracy|success|success rate|sr|pass|pass@\d+|pass\^\d+|resolved|"
    r"% resolved|f1|em|exact match|precision|recall|win rate|wr|winning rates|rate|"
    r"solve rate|completion rate|avg@\d+|mean@\d+|top-?\d+ accuracy|correct|ex)\b"
)

# The extractor's own note and the label are both used to cast the candidate net wide.
LABEL_HINT_RE = re.compile(
    r"(?i)(?:w/o|w/out|without|w/ |ablat|\bours\b|\bonly\b|minus|remov|single|variant|"
    r"^\s*[-+]|[-+]\s|no[ _-]|\bno\b|base(?:line)?$|vanilla|naive|plain|full\b)"
)
NOTE_HINT_RE = re.compile(r"(?i)(?:ablat|variant|configuration|our own|own system)")

CATEGORIES = (
    "ablation",                  # the paper's own system with a component switched OFF
    "augmentation",              # the paper's own system with a component switched ON on top of it
    "own_full_alias",            # another name for the paper's own full system: not a contrast
    "rival_system",              # a different team's harness
    "non_harness_baseline",      # a bare LLM, a human, a retrieval-only pipeline, a fine-tune
    "model_or_training_variant", # a different base model or training recipe, not a harness change
    "unmapped",                  # cannot be decided, or maps to no dimension
)
POOLABLE_CATEGORIES = ("ablation", "augmentation")
DIRECTIONS = ("component_removed", "component_added", "component_changed", "unclear")


# ------------------------------------------------------------------------------------------------
# loading
# ------------------------------------------------------------------------------------------------
def load_dimensions(path: Path = DIMENSIONS) -> list[dict[str, Any]]:
    """The 38 coded dimensions, with the layer-M metadata ones flagged.

    Layer M (`target_domain`, `open_source`, `model_agnostic`, `primary_artifact`,
    `first_release_date`, `pinned_version`, `stars`) records what a system IS, not how it is built.
    Nothing can be ablated from it, so a label the model maps there is recorded `unmapped`.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    layers = {layer["id"]: layer["name"] for layer in doc.get("layers", [])}
    dims = []
    for d in doc["dimensions"]:
        dims.append({
            "key": d["key"],
            "id": d.get("id", ""),
            "name": d.get("name", d["key"]),
            "layer": d.get("layer", ""),
            "layer_name": layers.get(d.get("layer", ""), ""),
            "values": list(d.get("values") or []),
            "design": d.get("layer") != "M",
        })
    return dims


def design_dimension_keys(dims: Sequence[dict[str, Any]]) -> set[str]:
    return {d["key"] for d in dims if d["design"]}


def load_system_names(path: Path = SYSTEMS) -> dict[str, str]:
    """system_id -> the system's name, for the classification prompt."""
    if not path.exists():
        return {}
    systems = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"]: (s.get("name") or s["id"]) for s in systems}


def load_candidates(path: Path = REJECTS) -> pd.DataFrame:
    """The `not_own_system` rejects that might be the paper's own ablation or variant.

    The net is deliberately wide: the regexes only decide what gets *shown to the model*, and a
    false positive here costs one line in a batch, while a false negative loses a controlled
    contrast for good. The model, not the regex, decides what an ablation is.
    """
    need = ["reason", "system_id", "record_id", "reported_system_name", "benchmark", "split",
            "metric", "score", "model", "evidence_quote", "note"]
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(f"{path}: missing column(s) {missing}")
    df = df[df["reason"] == "not_own_system"].copy()
    label = df["reported_system_name"].fillna("").astype(str)
    note = df["note"].fillna("").astype(str)
    keep = label.str.contains(LABEL_HINT_RE, regex=True) | note.str.contains(NOTE_HINT_RE, regex=True)
    df = df[keep].copy()
    df["label"] = label[keep].str.strip()
    df = df[df["label"] != ""].copy()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["label_key"] = df["system_id"].str.strip() + "|" + df["label"].str.lower()
    return df.reset_index(drop=True)


def load_own_full_rows(path: Path = RESULTS) -> pd.DataFrame:
    """The paper-sourced rows of results.csv: each paper's own full system, one row per measurement.

    `notes` carries `source=paper` for the rows `scripts/extract_results.py` accepted as the paper's
    own system (as opposed to `source=leaderboard`). Those are the full-system arms of the contrasts.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in ("system_id", "benchmark", "split", "metric", "score", "model", "notes"):
        if col not in df.columns:
            raise SystemExit(f"{path}: missing column {col!r}")
    df = df[df["notes"].astype(str).str.contains("source=paper", regex=False)].copy()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    return df[df["score"].notna()].reset_index(drop=True)


MATCH_KEYS = ("system_id", "benchmark", "split", "metric", "model")


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def full_system_index(own: pd.DataFrame) -> dict[tuple[str, ...], list[float]]:
    """(system, benchmark, split, metric, model) -> the distinct own scores recorded for it.

    A key with more than one distinct score is ambiguous about which number is "the full system",
    and the pair is dropped rather than resolved by taking the best one: taking the maximum would
    inflate every effect in exactly the direction publication bias already pushes.
    """
    index: dict[tuple[str, ...], list[float]] = {}
    for row in own.itertuples(index=False):
        key = tuple(_norm(getattr(row, k)) for k in MATCH_KEYS)
        index.setdefault(key, [])
        score = float(row.score)
        if not any(math.isclose(score, s, rel_tol=1e-9, abs_tol=1e-9) for s in index[key]):
            index[key].append(score)
    return index


def partial_indexes(own: pd.DataFrame) -> dict[str, set[tuple[str, ...]]]:
    """Coarser keys, used only to say WHY an exact match failed."""
    out = {"bm": set(), "bm_metric": set(), "bm_metric_split": set()}
    for row in own.itertuples(index=False):
        sid, bm = _norm(row.system_id), _norm(row.benchmark)
        metric, split = _norm(row.metric), _norm(row.split)
        out["bm"].add((sid, bm))
        out["bm_metric"].add((sid, bm, metric))
        out["bm_metric_split"].add((sid, bm, metric, split))
    return out


# ------------------------------------------------------------------------------------------------
# step 2: classification (the only model call)
# ------------------------------------------------------------------------------------------------
CLASSIFY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["votes"],
    "properties": {
        "votes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["record_id", "category", "dimension", "direction", "confidence", "reason"],
                "properties": {
                    "record_id": {"type": "string"},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "dimension": {"type": ["string", "null"]},
                    "direction": {"type": "string", "enum": list(DIRECTIONS)},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reason": {"type": "string"},
                },
            },
        }
    },
}


def classify_system_prompt(dims: Sequence[dict[str, Any]]) -> str:
    """The system prompt for the label classifier: the dimension menu plus the refusal rule."""
    menu = "\n".join(
        f"  {d['key']}  ({d['id']}, layer {d['layer']} = {d['layer_name']})"
        + (f"  values: {', '.join(d['values'])}" if d["values"] else "")
        for d in dims if d["design"]
    )
    meta = ", ".join(d["key"] for d in dims if not d["design"])
    return f"""You are classifying row labels taken from the results tables of research papers about
LLM agent harnesses (agent scaffolds). Each label named one arm of one paper's own results table.
For each label, decide what that arm WAS, relative to the paper's own full system.

CATEGORIES (pick exactly one):
  ablation                  - the paper's OWN system with one component switched OFF, removed,
                              disabled or replaced by nothing. "Ours w/o memory", "w/o Planner",
                              "- verification", "no scheduling", "Single agent" (when the paper's
                              system is multi-agent), "React-Only" (when the paper's system adds
                              something to ReAct).
  augmentation              - the paper's OWN system with one component switched ON *on top of* a
                              simpler configuration, i.e. the arm has a component the full system
                              row may not. "+ Memory", "+ Planning", "w/ Verifier".
  own_full_alias            - just another name, spelling or "(Ours)" variant of the paper's own
                              FULL system. No component differs. This is NOT a contrast.
  rival_system              - a different team's harness or agent framework.
  non_harness_baseline      - a bare LLM with no scaffold, a human, a retrieval-only pipeline, a
                              classical (non-agentic) method, a random or oracle baseline.
  model_or_training_variant - the SAME harness with a different base model, a different amount or
                              kind of training/fine-tuning/RL/SFT, a different decoding or
                              sampling budget, or a different dataset. A harness component is NOT
                              what changed. Examples: "+ weak-sup IT All", "SFT", "GPT-4o",
                              "+ In-Domain", "+ Test-time Search (K=16)", "w/ Uniform Rewards".
  unmapped                  - you cannot tell what the arm was, or it is an ablation of something
                              that is not one of the design dimensions below.

DIMENSION: if and only if the category is `ablation` or `augmentation`, give the ONE dimension key
from this list that the arm removes, adds or changes. Otherwise give null.

{menu}

These keys are metadata about a system, not components of it, and can NEVER be the answer; a label
that changes one of them is `unmapped`: {meta}

DIRECTION (relative to the paper's own full system):
  component_removed - the component is present in the full system and ABSENT in this arm.
  component_added   - the component is ABSENT in the full system (or in the simpler configuration
                      this arm builds on) and PRESENT in this arm.
  component_changed - the component is present in both but set to a different value.
  unclear           - you cannot tell which way round it is.
The label's own wording decides this in almost every case and you should use it: a label that starts
with "w/o", "w/out", "without", "no ", "-" or "minus", or that ends in "-free", is
`component_removed`; a label that starts with "+", "w/" or "with" is `component_added`; a label of
the form "X only", "single X", "X-Only" is `component_removed` (everything else was taken away).
Answer `unclear` only when the label genuinely gives no direction.

REFUSE TO GUESS. This is the rule that matters most. The labels are short and many of them are
genuinely undecidable from the text you are given ("w/o GA", "+JO", "w/o CTX", "Menu (Ours)"). If
you cannot say with real confidence which dimension changed, answer category `unmapped`, dimension
null, and put the reason in `reason` ("acronym not defined in the quote", "could be planning or
delegation", "quote does not say what was removed"). An unmapped label is EXCLUDED from the
analysis and costs nothing. A label forced into the nearest-looking dimension corrupts a pooled
component effect and is the single worst error you can make here. Never stretch a label to fit.

`confidence` is your probability that BOTH the category and the dimension are right, in [0, 1], and
it is used as a hard threshold, so calibrate it and use the whole range:
  >= 0.8  the label names the component outright ("w/o Memory Module", "Single agent"), and the
          dimension it belongs to is not in doubt.
  ~ 0.6   you would defend this mapping to a reviewer: the component is named or unambiguous from
          the quote, and one dimension fits it better than any other.
  ~ 0.4   you can see which dimension it probably is, but a reviewer could reasonably name a
          different one.
  <= 0.3  you are guessing. Answer category `unmapped` instead - do not report a dimension with a
          low confidence and hope it is filtered out; say `unmapped` and give the reason.
Do not reflexively answer 0.5: a number at the threshold is the least useful answer you can give.
`reason` is at most 25 words, concrete, and quotes the words you relied on.

Answer for every record_id you are given, in the same order.
"""


def classify_items(frame: pd.DataFrame, names: dict[str, str]) -> list[dict[str, Any]]:
    """One prompt item per unique (system, label): the label, the paper's system, benchmark, quote."""
    items: list[dict[str, Any]] = []
    for i, (key, group) in enumerate(frame.groupby("label_key", sort=True), start=1):
        head = group.iloc[0]
        quotes: list[str] = []
        for q in group["evidence_quote"].astype(str).tolist():
            q = re.sub(r"\s+", " ", q).strip()
            if q and q not in quotes:
                quotes.append(q[:400])
            if len(quotes) >= 3:
                break
        notes = sorted({re.sub(r"\s+", " ", str(n)).strip() for n in group["note"].astype(str) if str(n).strip()})
        items.append({
            "id": f"L{i:04d}",
            "label_key": key,
            "label": head["label"],
            "own_system_id": head["system_id"],
            "own_system_name": names.get(head["system_id"], head["system_id"]),
            "benchmarks": sorted({str(b) for b in group["benchmark"] if str(b).strip()})[:4],
            "metrics": sorted({str(m) for m in group["metric"] if str(m).strip()})[:4],
            "extractor_note": "; ".join(notes)[:300],
            "quotes": quotes,
        })
    return items


def classify_prompt(batch: list[dict[str, Any]]) -> str:
    payload = [{k: v for k, v in item.items() if k != "label_key"} for item in batch]
    return ("Row labels to classify (JSON). `label` is the arm's label in the paper's table, "
            "`own_system_name` is the paper's own system, `quotes` are verbatim lines from the "
            "paper around that number, `extractor_note` is an earlier human/model note on the row.\n"
            + json.dumps(payload, ensure_ascii=False, indent=None))


def load_cache(path: Path = CACHE) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("%s is not readable JSON; starting from an empty cache", path)
        return {}
    return data.get("labels", data) if isinstance(data, dict) else {}


def save_cache(cache: dict[str, dict[str, Any]], path: Path = CACHE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"labels": cache}, ensure_ascii=False, indent=1, sort_keys=True),
                    encoding="utf-8")


def normalise_vote(vote: dict[str, Any], design_keys: set[str], conf_floor: float = CONF_FLOOR) -> dict[str, Any]:
    """One model answer, made safe: an out-of-menu or metadata dimension becomes `unmapped`.

    Four ways a vote is demoted to `unmapped`, each recorded in `demoted` with its reason so the
    demotion is auditable rather than silent: an unknown category; a poolable category with no
    dimension; a dimension outside the 31 design dimensions (including a layer-M metadata key,
    which nothing can be ablated from); and a confidence below the floor. The demotion is the whole
    point of the refusal rule - a guessed mapping is worse than no mapping. An unorientable
    DIRECTION is not demoted here; it is dropped by `build_contrasts`, which counts it separately.
    """
    category = str(vote.get("category") or "").strip()
    dimension = vote.get("dimension")
    dimension = None if dimension in (None, "", "null", "None") else str(dimension).strip()
    direction = str(vote.get("direction") or "unclear").strip()
    reason = re.sub(r"\s+", " ", str(vote.get("reason") or "")).strip()[:300]
    try:
        confidence = float(vote.get("confidence"))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = min(max(confidence, 0.0), 1.0)

    if category not in CATEGORIES:
        return {"category": "unmapped", "dimension": None, "direction": "unclear",
                "confidence": confidence, "reason": f"model returned unknown category {category!r}",
                "demoted": "unknown_category"}
    if direction not in DIRECTIONS:
        direction = "unclear"
    if category in POOLABLE_CATEGORIES:
        if dimension is None:
            return {"category": "unmapped", "dimension": None, "direction": direction,
                    "confidence": confidence, "reason": reason or "no dimension given",
                    "demoted": "no_dimension"}
        if dimension not in design_keys:
            return {"category": "unmapped", "dimension": None, "direction": direction,
                    "confidence": confidence,
                    "reason": (reason + f" [dimension {dimension!r} is not a design dimension]").strip(),
                    "demoted": "dimension_not_design"}
        if confidence < conf_floor:
            return {"category": "unmapped", "dimension": None, "direction": direction,
                    "confidence": confidence,
                    "reason": (reason + f" [confidence {confidence:.2f} below floor {conf_floor:.2f}]").strip(),
                    "demoted": "low_confidence"}
    else:
        dimension = None
    return {"category": category, "dimension": dimension, "direction": direction,
            "confidence": confidence, "reason": reason, "demoted": ""}


def resolve_classifications(cache: dict[str, dict[str, Any]], dims: Sequence[dict[str, Any]],
                            *, conf_floor: float = CONF_FLOOR) -> dict[str, dict[str, Any]]:
    """Cache entries -> the normalised classification used by the analysis.

    Kept separate from the model call on purpose. The cache holds what the model said; the
    confidence floor, the dimension menu and the demotion rules are applied here, at analysis time,
    so that tightening or loosening any of them costs nothing and can be reported as a sensitivity
    (`--sensitivity` writes `data/analysis/ablation_sensitivity_confidence.csv`) instead of being
    baked into the stored answers.
    """
    design_keys = design_dimension_keys(dims)
    out: dict[str, dict[str, Any]] = {}
    for key, entry in cache.items():
        raw = entry.get("raw") if isinstance(entry, dict) and "raw" in entry else entry
        if not isinstance(raw, dict):
            continue
        out[key] = normalise_vote(raw, design_keys, conf_floor) | {
            "label": entry.get("label", ""), "own_system_id": entry.get("own_system_id", ""),
            "model": entry.get("model", ""),
            "raw_dimension": (raw.get("dimension") or ""),
            "raw_category": (raw.get("category") or ""),
        }
    return out


def classify_labels(
    frame: pd.DataFrame,
    dims: Sequence[dict[str, Any]],
    names: dict[str, str],
    backend: Callable[..., Any] | None,
    *,
    cache: dict[str, dict[str, Any]] | None = None,
    batch_size: int = BATCH_SIZE,
    model: str = "sonnet",
    effort: str | None = None,
    exe: str = "",
    limit: int = 0,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Classify every uncached (system, label) and return the RAW-answer cache.

    The returned map is the cache, not the analysis input: `resolve_classifications` turns it into
    the normalised classifications the analysis uses.

    The cache is keyed by `system_id|lowercased label`: the same label text in two papers is two
    different claims ("w/o Planner" removes different code in different systems), so the system id
    is part of the key. A cached key is never re-sent, which is what makes a re-run free.
    """
    cache = {} if cache is None else cache
    items = classify_items(frame, names)
    todo = [it for it in items if it["label_key"] not in cache]
    stats_: dict[str, Any] = {"labels_total": len(items), "labels_cached": len(items) - len(todo),
                              "labels_sent": 0, "calls": 0, "tokens_in": 0, "tokens_out": 0,
                              "cost_usd": 0.0, "failed_batches": 0}
    if todo and backend is None:
        log.warning("%d labels are not in the cache and no backend was given: they stay unclassified",
                    len(todo))
        return cache, stats_
    if limit:
        todo = todo[:limit]
    if not todo:
        log.info("all %d labels already classified (cache hit); no model call", len(items))
        return cache, stats_

    tmpdir = Path(tempfile.mkdtemp(prefix="analyse_ablations_"))
    system_file = tmpdir / "classify_system_prompt.txt"
    system_file.write_text(classify_system_prompt(dims), encoding="utf-8")
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    log.info("classifying %d labels in %d batch(es) of up to %d", len(todo), len(batches), batch_size)
    for n, batch in enumerate(batches, start=1):
        try:
            result = backend(exe, model, system_file, batch, effort=effort,
                             schema=CLASSIFY_SCHEMA, prompt=classify_prompt, text_json=True)
        except Exception as exc:  # noqa: BLE001 - one bad batch must not lose the others
            stats_["failed_batches"] += 1
            log.error("batch %d/%d failed: %s", n, len(batches), str(exc)[:300])
            continue
        votes = list(getattr(result, "votes", result) or [])
        for item, vote in zip(batch, votes, strict=False):
            # the RAW answer is cached, not the normalised one: --conf-floor and the dimension menu
            # are then re-runnable without another model call, and a demotion stays auditable
            # against what the model actually said.
            cache[item["label_key"]] = {
                "raw": {k: vote.get(k) for k in ("category", "dimension", "direction",
                                                 "confidence", "reason")},
                "label": item["label"], "own_system_id": item["own_system_id"],
                "model": getattr(result, "model", model),
            }
        stats_["calls"] += 1
        stats_["labels_sent"] += len(batch)
        stats_["tokens_in"] += int(getattr(result, "tokens_in", 0) or 0)
        stats_["tokens_out"] += int(getattr(result, "tokens_out", 0) or 0)
        stats_["cost_usd"] += float(getattr(result, "cost_usd", 0.0) or 0.0)
        log.info("batch %d/%d: %d labels, %d in / %d out, $%.4f cumulative", n, len(batches),
                 len(batch), stats_["tokens_in"], stats_["tokens_out"], stats_["cost_usd"])
    return cache, stats_


# ------------------------------------------------------------------------------------------------
# step 3: the contrast table
# ------------------------------------------------------------------------------------------------
def metric_polarity(metric: str) -> str:
    """`higher`, `lower` or `unknown` - which direction of a metric counts as better.

    `lower` wins a tie: "error rate" contains "rate", and a metric named for an error is an error.
    """
    m = _norm(metric)
    if not m:
        return "unknown"
    if LOWER_IS_BETTER_RE.search(m):
        return "lower"
    if HIGHER_IS_BETTER_RE.search(m):
        return "higher"
    return "unknown"


def is_proportion_metric(metric: str, scores: Sequence[float]) -> bool:
    """True when the metric is a success-type proportion on a 0-1 or 0-100 scale.

    Two conditions, both required: the metric NAME is one of the proportion family, and the observed
    values lie inside the implied range. A "score" of 4.2 is not a percentage however it is named.
    """
    if not PROPORTION_RE.search(_norm(metric)):
        return False
    vals = [v for v in scores if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return False
    return 0.0 <= min(vals) and max(vals) <= 100.0


def score_scale(scores: Sequence[float]) -> float:
    """100.0 for a percentage-scale pair, 1.0 for a 0-1 pair. Used for the binomial variance."""
    return 1.0 if max(scores) <= 1.0 else 100.0


def benchmark_items(benchmark: str, split: str, default_n: int = DEFAULT_N) -> tuple[int, str]:
    """(assumed item count, where it came from) for the variance approximation."""
    bm, sp = _norm(benchmark), _norm(split)
    for key in ((bm, sp), (bm, "")):
        if key in BENCHMARK_N:
            return BENCHMARK_N[key], "table"
    for (kbm, ksp), n in BENCHMARK_N.items():
        if kbm and kbm in bm and (not ksp or ksp in sp):
            return n, "table_substring"
        if kbm and bm and bm in kbm and (not ksp or ksp in sp):
            return n, "table_substring"
    return default_n, "default"


def contrast_variance(with_score: float, without_score: float, *, proportion: bool, scale: float,
                      n_items: int, assumed_rel_se: float = ASSUMED_REL_SE) -> tuple[float, str]:
    """Approximate sampling variance of the RELATIVE effect for one contrast.

    Papers publish a point score and no standard error, so a variance has to be constructed. Two
    constructions, and which one was used is recorded on every row:

    `binomial_delta` - for a proportion metric (a success/accuracy/pass rate), each arm is modelled
    as `n_items` independent Bernoulli trials, `var(p) = p(1-p)/n`, and the variance of the ratio
    `r = 1 - p_wo/p_w` follows by the delta method:
        var(r) = (p_wo/p_w)^2 * [ (1-p_wo)/(n*p_wo) + (1-p_w)/(n*p_w) ]
    The two arms are treated as independent, which is conservative (they share the task set, so the
    true variance of the difference is smaller) and therefore widens intervals rather than narrowing
    them. `n_items` comes from BENCHMARK_N where the split size is known and from --default-n where
    it is not; `--sensitivity` re-runs the pooling across assumed sizes so the reader can see how
    little the pooled point estimate depends on this choice.

    `assumed_rel_se` - for any other metric (an MSE, a cost, a bespoke score), where no sampling
    model is available at all: a flat relative standard error. This is an assumption, not a
    measurement; rows using it are counted in the output and the pooled estimate is reported with
    and without them under --sensitivity.
    """
    if not proportion:
        return float(assumed_rel_se) ** 2, "assumed_rel_se"
    n = max(int(n_items), 1)
    p_w = min(max(with_score / scale, 1.0 / (2 * n)), 1.0 - 1.0 / (2 * n))
    p_wo = min(max(without_score / scale, 1.0 / (2 * n)), 1.0 - 1.0 / (2 * n))
    ratio = p_wo / p_w
    var = ratio ** 2 * ((1.0 - p_wo) / (n * p_wo) + (1.0 - p_w) / (n * p_w))
    return float(var), "binomial_delta"


@dataclass
class Contrast:
    record_id: str
    system_id: str
    label: str
    dimension: str
    category: str
    direction: str
    confidence: float
    benchmark: str
    split: str
    metric: str
    model: str
    polarity: str
    full_score: float
    ablated_score: float
    with_score: float
    without_score: float
    delta_raw: float
    rel_effect: float
    variance: float
    var_method: str
    n_items: int
    n_source: str
    proportion: bool
    scale: float


CONTRAST_COLUMNS = [f.name for f in Contrast.__dataclass_fields__.values()]  # type: ignore[attr-defined]


def orient_contrast(full: float, ablated: float, *, direction: str, metric: str, benchmark: str,
                    split: str, default_n: int = DEFAULT_N,
                    min_denominator_pct: float = 1.0) -> tuple[dict[str, Any] | None, str]:
    """(the oriented numeric fields of a Contrast, "") or (None, drop reason).

    The single place where a (full-system score, other-arm score) pair becomes an effect. Used by
    `build_contrasts` for the coded-set harvest and by `scripts/harvest_ablations_corpus.py` for the
    corpus-wide harvest, so the two sources are oriented, scaled and given a variance by exactly the
    same arithmetic. `direction` must already be `component_removed` or `component_added`.
    """
    polarity = metric_polarity(metric)
    if polarity == "unknown":
        polarity = "higher"  # recorded on the row; see `polarity_assumed` in the summary
        polarity_assumed = True
    else:
        polarity_assumed = False
    if direction == "component_removed":
        with_score, without_score = full, ablated
    elif direction == "component_added":
        with_score, without_score = ablated, full
    else:
        return None, f"direction_{direction}"
    if polarity == "lower":
        with_score, without_score = -with_score, -without_score  # see below for the denominator

    # delta > 0 means the component helped, on whichever polarity the metric has.
    delta = with_score - without_score
    denominator = abs(with_score)
    scale = score_scale([abs(full), abs(ablated)])
    floor = min_denominator_pct if scale == 100.0 else min_denominator_pct / 100.0
    if denominator < floor:
        return None, "denominator_too_small"
    rel = delta / denominator

    proportion = polarity == "higher" and is_proportion_metric(metric, [full, ablated])
    n_items, n_source = benchmark_items(benchmark, split, default_n)
    var, var_method = contrast_variance(abs(with_score), abs(without_score),
                                        proportion=proportion, scale=scale, n_items=n_items)
    if not np.isfinite(var) or var <= 0:
        return None, "variance_not_finite"
    return {
        "polarity": polarity + ("_assumed" if polarity_assumed else ""),
        "full_score": full, "ablated_score": ablated,
        "with_score": abs(with_score) if polarity == "lower" else with_score,
        "without_score": abs(without_score) if polarity == "lower" else without_score,
        "delta_raw": delta, "rel_effect": rel, "variance": var, "var_method": var_method,
        "n_items": n_items, "n_source": n_source, "proportion": proportion, "scale": scale,
    }, ""


def build_contrasts(
    candidates: pd.DataFrame,
    classifications: dict[str, dict[str, Any]],
    own: pd.DataFrame,
    *,
    default_n: int = DEFAULT_N,
    min_denominator_pct: float = 1.0,
) -> tuple[pd.DataFrame, Counter]:
    """Pair each classified ablation row with the paper's own full-system score on the same cell.

    The match is EXACT on (system_id, benchmark, split, metric, model) after whitespace and case
    normalisation, and nothing looser is ever accepted: a "full system" row measured with another
    base model or scored on another metric is a different experiment, and pairing it would
    manufacture an effect out of the mismatch. Every row that fails to pair is counted with the
    reason, and `drops` is published as a table so the funnel from 3,280 rejects to N contrasts is
    auditable end to end.

    Orientation. `direction` says which arm has the component, and the effect is always written so
    that a POSITIVE value means the component helped:
        component_removed: with = the paper's full system,    without = this row
        component_added:   with = this row,                   without = the paper's full system
    The denominator of the relative effect is ALWAYS the with-component arm, so the effect reads as
    "the fraction of the full system's number that this component accounts for". For a
    lower-is-better metric (an MSE, a cost) the numerator is negated instead, which keeps the sign
    convention - positive means the component helped - and makes the effect a relative *increase* in
    the error when the component is removed, again as a fraction of the with-component arm.
    A `component_changed` or `unclear` direction cannot be oriented and is dropped (and counted).
    """
    index = full_system_index(own)
    partial = partial_indexes(own)
    drops: Counter = Counter()
    rows: list[Contrast] = []

    for r in candidates.itertuples(index=False):
        cls = classifications.get(r.label_key)
        if cls is None:
            drops["unclassified"] += 1
            continue
        category = cls.get("category", "unmapped")
        if category == "unmapped":
            drops["unmapped"] += 1
            continue
        if category not in POOLABLE_CATEGORIES:
            drops[f"not_an_ablation:{category}"] += 1
            continue
        dimension = cls.get("dimension")
        if not dimension:
            drops["no_dimension"] += 1
            continue
        direction = cls.get("direction", "unclear")
        if direction not in ("component_removed", "component_added"):
            drops[f"direction_{direction}"] += 1
            continue
        if r.score is None or (isinstance(r.score, float) and math.isnan(r.score)):
            drops["ablated_score_missing"] += 1
            continue

        sid, bm = _norm(r.system_id), _norm(r.benchmark)
        metric, split, model = _norm(r.metric), _norm(r.split), _norm(r.model)
        key = (sid, bm, split, metric, model)
        scores = index.get(key)
        if not scores:
            if (sid, bm, metric, split) in partial["bm_metric_split"]:
                drops["model_mismatch"] += 1
            elif (sid, bm, metric) in partial["bm_metric"]:
                drops["split_mismatch"] += 1
            elif (sid, bm) in partial["bm"]:
                drops["metric_mismatch"] += 1
            else:
                drops["no_full_row"] += 1
            continue
        if len(scores) > 1:
            drops["full_score_ambiguous"] += 1
            continue

        oriented, drop = orient_contrast(float(scores[0]), float(r.score), direction=direction,
                                         metric=str(r.metric), benchmark=str(r.benchmark),
                                         split=str(r.split), default_n=default_n,
                                         min_denominator_pct=min_denominator_pct)
        if oriented is None:
            drops[drop] += 1
            continue
        rows.append(Contrast(
            record_id=str(r.record_id), system_id=str(r.system_id), label=str(r.label),
            dimension=str(dimension), category=category, direction=direction,
            confidence=float(cls.get("confidence") or 0.0), benchmark=str(r.benchmark),
            split=str(r.split), metric=str(r.metric), model=str(r.model), **oriented,
        ))

    frame = pd.DataFrame([vars(c) for c in rows], columns=CONTRAST_COLUMNS)
    # The same ablation can appear twice in the rejects (a number printed in a table and again in
    # the text, or two locators for one cell). Two copies of one experiment are not two contrasts.
    if not frame.empty:
        before = len(frame)
        frame = frame.drop_duplicates(
            subset=["record_id", "system_id", "label", "benchmark", "split", "metric", "model",
                    "full_score", "ablated_score"]).reset_index(drop=True)
        if len(frame) < before:
            drops["duplicate_contrast"] += before - len(frame)
    return frame, drops


# ------------------------------------------------------------------------------------------------
# corpus-wide contrasts (scripts/harvest_ablations_corpus.py): de-duplication against this harvest
# ------------------------------------------------------------------------------------------------
COMPONENT_STOPWORDS = frozenset({
    "w", "o", "out", "wo", "without", "with", "no", "not", "the", "a", "an", "of", "and", "or", "ours",
    "our", "full", "module", "modules", "component", "components", "mechanism", "only", "minus",
    "remove", "removed", "removing", "ablation", "ablated", "variant", "setting", "disabled", "disable",
    "using", "use", "all", "plus", "add", "added", "adding", "for", "in", "on", "to", "by",
})


def component_tokens(label: Any) -> frozenset[str]:
    """The content words of an arm label or component name ("w/o Memory Module" -> {"memory"})."""
    words = re.findall(r"[a-z0-9]+", _norm(label))
    return frozenset(w for w in words if w not in COMPONENT_STOPWORDS)


def _alnum(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", _norm(value))


def _loose_equal(a: Any, b: Any) -> bool:
    """Equal after dropping case and punctuation, or one contained in the other (non-empty)."""
    x, y = _alnum(a), _alnum(b)
    return bool(x) and bool(y) and (x == y or x in y or y in x)


def _same_component(a: Any, b: Any) -> bool:
    ta, tb = component_tokens(a), component_tokens(b)
    if not ta or not tb:
        return False
    return ta <= tb or tb <= ta or len(ta & tb) / len(ta | tb) >= 0.5


def flag_coded_duplicates(corpus: pd.DataFrame, coded: pd.DataFrame) -> pd.Series:
    """For each corpus contrast, why it duplicates a contrast of the coded-set harvest, or "".

    Two rules, either sufficient, both restricted to the SAME paper (record_id):
      `key`    - same benchmark, same metric and same component, each compared loosely (case and
                 punctuation ignored, containment accepted; the component by its content words,
                 so "w/o Memory Module" in the coded set matches "memory module" here). An empty
                 corpus metric matches any metric.
      `scores` - the same (full score, ablated score) pair, to 1e-6. Two contrasts from one paper
                 with the same two numbers are the same cell however the labels were written.
    Deliberately generous: a false "duplicate" loses one corpus contrast, while a missed duplicate
    counts one experiment twice in a pooled estimate, which is the error that matters here.
    """
    if corpus.empty:
        return pd.Series([], dtype=str)
    if coded is None or coded.empty:
        return pd.Series([""] * len(corpus), index=corpus.index, dtype=str)
    by_rec: dict[str, list[dict[str, Any]]] = {}
    for r in coded.to_dict("records"):
        by_rec.setdefault(str(r.get("record_id", "")), []).append(r)
    comp_col = "component" if "component" in corpus.columns else "label"
    out = []
    for r in corpus.to_dict("records"):
        rule = ""
        for c in by_rec.get(str(r.get("record_id", "")), []):
            try:
                same_scores = (math.isclose(float(r["full_score"]), float(c["full_score"]), abs_tol=1e-6)
                               and math.isclose(float(r["ablated_score"]), float(c["ablated_score"]),
                                                abs_tol=1e-6))
            except (TypeError, ValueError, KeyError):
                same_scores = False
            if same_scores:
                rule = "scores"
                break
            metric_ok = not _alnum(r.get("metric")) or _loose_equal(r.get("metric"), c.get("metric"))
            comp_ok = (_same_component(r.get(comp_col), c.get("label"))
                       or _same_component(r.get("label"), c.get("label")))
            if _loose_equal(r.get("benchmark"), c.get("benchmark")) and metric_ok and comp_ok:
                rule = "key"
                break
        out.append(rule)
    return pd.Series(out, index=corpus.index, dtype=str)


# ------------------------------------------------------------------------------------------------
# step 4: random-effects pooling
# ------------------------------------------------------------------------------------------------
@dataclass
class Pooled:
    k: int
    mu: float
    se: float
    ci_low: float
    ci_high: float
    tau2: float
    q: float
    q_df: int
    q_p: float
    i2: float
    pi_low: float
    pi_high: float
    mu_fe: float
    weights: list[float] = field(default_factory=list)


def dersimonian_laird(y: Sequence[float], v: Sequence[float], *, z: float = 1.959963984540054) -> Pooled:
    """Random-effects pooling, DerSimonian-Laird moment estimator of tau-squared.

    Exactly the textbook formulae, so that a reader can reproduce any pooled row with a calculator:
        w_i      = 1 / v_i                       fixed-effect weights
        mu_FE    = sum(w_i y_i) / sum(w_i)
        Q        = sum(w_i (y_i - mu_FE)^2)
        C        = sum(w_i) - sum(w_i^2) / sum(w_i)
        tau^2    = max(0, (Q - (k - 1)) / C)
        w*_i     = 1 / (v_i + tau^2)             random-effects weights
        mu       = sum(w*_i y_i) / sum(w*_i)
        SE(mu)   = sqrt(1 / sum(w*_i))
        I^2      = max(0, (Q - (k - 1)) / Q)
    The 95% CI uses the normal quantile (DL convention). The prediction interval is
    Higgins-Thompson: mu +- t_{k-2} sqrt(tau^2 + SE^2), and is undefined for k < 3 - with two
    studies there is no third point to predict from, and a "prediction interval" computed anyway
    would be a decorative number.
    """
    y_arr = np.asarray(list(y), dtype=float)
    v_arr = np.asarray(list(v), dtype=float)
    if y_arr.size == 0:
        raise ValueError("no studies to pool")
    if y_arr.size != v_arr.size:
        raise ValueError("y and v differ in length")
    if np.any(v_arr <= 0) or not np.all(np.isfinite(v_arr)):
        raise ValueError("every variance must be finite and positive")
    k = int(y_arr.size)
    w = 1.0 / v_arr
    mu_fe = float(np.sum(w * y_arr) / np.sum(w))
    q = float(np.sum(w * (y_arr - mu_fe) ** 2))
    c = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    tau2 = max(0.0, (q - (k - 1)) / c) if (k > 1 and c > 0) else 0.0
    w_re = 1.0 / (v_arr + tau2)
    mu = float(np.sum(w_re * y_arr) / np.sum(w_re))
    se = float(math.sqrt(1.0 / np.sum(w_re)))
    i2 = float(max(0.0, (q - (k - 1)) / q) * 100.0) if (k > 1 and q > 0) else 0.0
    q_p = float(stats.chi2.sf(q, k - 1)) if k > 1 else float("nan")
    if k >= 3:
        t_crit = float(stats.t.ppf(0.975, k - 2))
        half = t_crit * math.sqrt(tau2 + se ** 2)
        pi_low, pi_high = mu - half, mu + half
    else:
        pi_low = pi_high = float("nan")
    return Pooled(k=k, mu=mu, se=se, ci_low=mu - z * se, ci_high=mu + z * se, tau2=tau2,
                  q=q, q_df=max(k - 1, 0), q_p=q_p, i2=i2, pi_low=pi_low, pi_high=pi_high,
                  mu_fe=mu_fe, weights=(w_re / np.sum(w_re)).tolist())


def hartung_knapp(y: Sequence[float], v: Sequence[float], tau2: float, *,
                  level: float = 0.95) -> tuple[float, float, float]:
    """(se, ci_low, ci_high): the Hartung-Knapp(-Sidik-Jonkman) interval around the DL estimate.

    The z interval of `dersimonian_laird` treats tau-squared as known, which it is not, and is
    anticonservative when k is small - the case for every dimension here. Hartung-Knapp replaces
    the variance of mu by a weighted residual variance and the normal quantile by t on k - 1 df:
        w*_i   = 1 / (v_i + tau^2)
        mu     = sum(w*_i y_i) / sum(w*_i)
        q_HK   = sum(w*_i (y_i - mu)^2) / (k - 1)
        SE_HK  = sqrt(q_HK / sum(w*_i))
        CI     = mu +- t_{k-1, 0.975} SE_HK
    This is the untruncated form. When the observed dispersion is smaller than the within-study
    variances imply (q_HK < 1) it can come out NARROWER than the z interval; the pooled table
    reports both side by side, and `hk_narrower_than_z` flags that case rather than hiding it
    behind the ad-hoc max(1, q_HK) truncation. Undefined (nan) for k < 2.
    """
    y_arr = np.asarray(list(y), dtype=float)
    v_arr = np.asarray(list(v), dtype=float)
    k = int(y_arr.size)
    if k < 2:
        return float("nan"), float("nan"), float("nan")
    w = 1.0 / (v_arr + float(tau2))
    mu = float(np.sum(w * y_arr) / np.sum(w))
    q_hk = float(np.sum(w * (y_arr - mu) ** 2) / (k - 1))
    se = math.sqrt(q_hk / float(np.sum(w)))
    t_crit = float(stats.t.ppf(0.5 + level / 2.0, k - 1))
    return se, mu - t_crit * se, mu + t_crit * se


def equal_weight_mean(y: Sequence[float]) -> tuple[float, float, float, float]:
    """(mean, se, ci_low, ci_high) with a t interval: the assumption-light check on the pooling.

    It uses no variance model at all, so it is immune to the `contrast_variance` approximation. When
    it and the DL estimate disagree materially, the DL interval is being driven by the assumed
    variances and should not be quoted on its own.
    """
    arr = np.asarray(list(y), dtype=float)
    k = arr.size
    mean = float(arr.mean())
    if k < 2:
        return mean, float("nan"), float("nan"), float("nan")
    se = float(arr.std(ddof=1) / math.sqrt(k))
    half = float(stats.t.ppf(0.975, k - 1)) * se
    return mean, se, mean - half, mean + half


def aggregate_to_papers(frame: pd.DataFrame) -> pd.DataFrame:
    """One effect per (dimension, paper): contrasts from one paper are not independent studies.

    A paper that ablates memory on three benchmarks contributes three correlated numbers. They are
    averaged, and the paper-level variance is the MEAN of the contrast variances rather than
    mean/m - i.e. the averaging is credited with no precision gain at all. That is the
    perfect-correlation assumption, which is conservative: it widens every interval below.
    """
    if frame.empty:
        return pd.DataFrame(columns=["dimension", "record_id", "n_contrasts", "y", "v", "delta_raw",
                                     "systems", "benchmarks", "directions", "proportion_only",
                                     "n_items"])
    out = []
    for (dim, rec), g in frame.groupby(["dimension", "record_id"], sort=True):
        out.append({
            "dimension": dim,
            "record_id": rec,
            "n_contrasts": len(g),
            "y": float(g["rel_effect"].mean()),
            "v": float(g["variance"].mean()),
            "delta_raw": float(g["delta_raw"].mean()),
            "systems": ";".join(sorted(set(g["system_id"]))),
            "benchmarks": ";".join(sorted(set(g["benchmark"]))[:5]),
            "directions": ";".join(sorted(set(g["direction"]))),
            "proportion_only": bool(g["proportion"].all()),
            "n_items": float(g["n_items"].mean()),
        })
    return pd.DataFrame(out)


def percentage_point_effect(contrasts: pd.DataFrame) -> dict[str, Any]:
    """The SECONDARY effect measure: the mean raw delta in percentage points, and only where legal.

    Raw points cannot be pooled across metrics - 10 points of SWE-bench resolution and 10 points of
    an MSE are not the same quantity, and averaging them would be arithmetic on incommensurable
    units. So this is computed only over the contrasts inside the dimension that are on a 0-100
    proportion scale (`proportion` and `scale == 100`), the rest are left out, and the count of what
    went in is published beside the number. It is reported as a companion to the relative effect,
    never in place of it: a dimension whose percentage-point row rests on three of its eleven
    contrasts is describing those three.
    """
    out: dict[str, Any] = {"mu_pp": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                           "papers": 0, "contrasts": 0}
    if contrasts.empty:
        return out
    sub = contrasts[(contrasts["proportion"]) & (contrasts["scale"] == 100.0)]
    if sub.empty:
        return out
    by_paper = sub.groupby("record_id")["delta_raw"].mean()
    out["contrasts"] = len(sub)
    out["papers"] = int(by_paper.size)
    mean, _se, lo, hi = equal_weight_mean(by_paper.tolist())
    out["mu_pp"], out["ci_low"], out["ci_high"] = mean, lo, hi
    return out


def pool_by_dimension(frame: pd.DataFrame, *, min_papers: int = MIN_PAPERS,
                      corpus_columns: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(pooled table, paper-level table). A dimension under `min_papers` papers is NOT pooled.

    "Insufficient evidence" is a verdict, not a gap: the row still appears, with its contrast count,
    its paper count and its raw effects, so a reader can see exactly what the review found and why
    no number is offered. Two papers cannot separate a between-study variance from a within-study
    one, and a DL interval computed on k=2 would be an artefact of the assumed variances.
    """
    papers = aggregate_to_papers(frame)
    rows = []
    for dim, g in (papers.groupby("dimension", sort=True) if not papers.empty else []):
        contrasts = frame[frame["dimension"] == dim]
        n_papers = int(g["record_id"].nunique())
        base = {
            "dimension": dim,
            "n_contrasts": len(contrasts),
            "n_papers": n_papers,
            "n_systems": int(contrasts["system_id"].nunique()),
            "n_benchmarks": int(contrasts["benchmark"].nunique()),
            "mean_confidence": float(contrasts["confidence"].mean()),
            "share_favouring_component": float((contrasts["rel_effect"] > 0).mean()),
            "raw_effects": ";".join(f"{x:.4f}" for x in sorted(g["y"], reverse=True)),
        }
        if n_papers < min_papers:
            rows.append(base | {"pooled": 0, "verdict": "insufficient evidence",
                                "mu_rel": float("nan"), "se": float("nan"),
                                "ci_low": float("nan"), "ci_high": float("nan"),
                                "tau2": float("nan"), "i2": float("nan"), "q": float("nan"),
                                "q_p": float("nan"), "pi_low": float("nan"), "pi_high": float("nan"),
                                "mu_fe": float("nan"),
                                "mean_rel_unweighted": float(g["y"].mean()),
                                "ew_ci_low": float("nan"), "ew_ci_high": float("nan"),
                                "mu_pp": float("nan"), "pp_ci_low": float("nan"),
                                "pp_ci_high": float("nan"), "pp_papers": 0, "pp_contrasts": 0,
                                "pp_poolable": 0})
            continue
        pooled = dersimonian_laird(g["y"].tolist(), g["v"].tolist())
        ew_mean, _ew_se, ew_lo, ew_hi = equal_weight_mean(g["y"].tolist())
        pp = percentage_point_effect(contrasts)
        if corpus_columns:
            hk_se, hk_lo, hk_hi = hartung_knapp(g["y"].tolist(), g["v"].tolist(), pooled.tau2)
            base = base | {"hk_se": hk_se, "hk_ci_low": hk_lo, "hk_ci_high": hk_hi,
                           "hk_ci_excludes_zero": int(hk_lo > 0 or hk_hi < 0),
                           "hk_narrower_than_z": int(hk_hi - hk_lo < pooled.ci_high - pooled.ci_low)}
        rows.append(base | {
            "pooled": 1, "verdict": "pooled",
            "mu_rel": pooled.mu, "se": pooled.se, "ci_low": pooled.ci_low, "ci_high": pooled.ci_high,
            "tau2": pooled.tau2, "i2": pooled.i2, "q": pooled.q, "q_p": pooled.q_p,
            "pi_low": pooled.pi_low, "pi_high": pooled.pi_high, "mu_fe": pooled.mu_fe,
            "mean_rel_unweighted": ew_mean, "ew_ci_low": ew_lo, "ew_ci_high": ew_hi,
            "mu_pp": pp["mu_pp"], "pp_ci_low": pp["ci_low"], "pp_ci_high": pp["ci_high"],
            "pp_papers": pp["papers"], "pp_contrasts": pp["contrasts"],
            "pp_poolable": int(pp["papers"] >= min_papers),
        })
    if corpus_columns:
        for row in rows:
            sub = frame[frame["dimension"] == row["dimension"]]
            prov = sub["provenance"] if "provenance" in sub.columns else pd.Series(["coded_harvest"] * len(sub))
            coded = sub[prov.values == "coded_harvest"]
            corpus = sub[prov.values != "coded_harvest"]
            row |= {"n_contrasts_coded": len(coded), "n_contrasts_corpus": len(corpus),
                    "n_papers_coded": int(coded["record_id"].nunique()),
                    "n_papers_corpus": int(corpus["record_id"].nunique())}
            for c in HK_COLUMNS:
                row.setdefault(c, float("nan"))
    table = pd.DataFrame(rows, columns=POOLED_COLUMNS_CORPUS if corpus_columns else POOLED_COLUMNS)
    if not table.empty:
        table = table.sort_values(["pooled", "n_papers", "n_contrasts"], ascending=False).reset_index(drop=True)
    return table, papers


# ------------------------------------------------------------------------------------------------
# step 5: publication-bias diagnostics
# ------------------------------------------------------------------------------------------------
def _residual_variance(resid: np.ndarray, values: np.ndarray, df: int) -> float:
    """sigma^2 for a k-point OLS, or 0.0 when the fit is perfect to within floating point.

    An exact fit (k points on a line, which happens easily at k = 3 or 4) leaves a residual sum of
    squares of ~1e-31 rather than 0, and dividing by it manufactures a p-value of 1e-16 out of
    nothing. Anything below 1e-18 of the total sum of squares is treated as no scatter at all, and
    the caller then reports the slope it found and refuses the test.
    """
    ssr = float(resid @ resid)
    tss = float(((values - values.mean()) ** 2).sum())
    if ssr <= 1e-18 * max(tss, 1e-12):
        return 0.0
    return ssr / df


def eggers_test(y: Sequence[float], v: Sequence[float]) -> dict[str, float]:
    """Egger's regression test for small-study effects.

    The standard normal deviate `y_i / se_i` is regressed on the precision `1 / se_i`, with an
    intercept, by ordinary least squares; the intercept's two-sided t test (df = k - 2) is the test.
    A non-zero intercept means small (imprecise) studies report systematically larger effects than
    large ones, which is the fingerprint selective reporting leaves. Needs k >= 3; at k = 3 it has
    one residual degree of freedom and essentially no power, so `k` is reported beside every p.
    """
    y_arr = np.asarray(list(y), dtype=float)
    se = np.sqrt(np.asarray(list(v), dtype=float))
    k = int(y_arr.size)
    out = {"k": float(k), "intercept": float("nan"), "se": float("nan"), "t": float("nan"),
           "p": float("nan"), "slope": float("nan")}
    if k < 3 or np.any(se <= 0):
        return out
    precision = 1.0 / se
    if float(np.ptp(precision)) == 0.0:
        # every study equally precise: there is no small-study gradient to regress on, and a
        # singular design would otherwise be "solved" into a meaningless intercept.
        return out
    snd = y_arr / se
    design = np.column_stack([np.ones(k), precision])
    beta, *_ = np.linalg.lstsq(design, snd, rcond=None)
    resid = snd - design @ beta
    df = k - 2
    sigma2 = _residual_variance(resid, snd, df)
    xtx_inv = np.linalg.pinv(design.T @ design)
    se_beta = math.sqrt(sigma2 * xtx_inv[0, 0]) if sigma2 > 0 else 0.0
    out["intercept"] = float(beta[0])
    out["slope"] = float(beta[1])
    if se_beta > 0:
        t = float(beta[0]) / se_beta
        out["se"] = se_beta
        out["t"] = t
        out["p"] = float(2 * stats.t.sf(abs(t), df))
    return out


def small_study_test_by_size(y: Sequence[float], n_items: Sequence[float]) -> dict[str, float]:
    """A small-study test that the variance model cannot fake: effect regressed on benchmark size.

    Egger's test regresses the effect on its own precision, and here the precision is APPROXIMATED
    from the two arm scores, so a larger effect mechanically gets a larger approximated variance (the
    delta-method ratio term grows as the arms separate). That makes some funnel asymmetry
    self-induced, and it means Egger's p cannot be read here the way it is read in a clinical
    meta-analysis. This test avoids the circularity by using a precision that does not touch the
    effect at all: the number of items in the benchmark the contrast was measured on. Under selective
    reporting, effects measured on SMALL evaluation sets are the ones large enough to survive
    selection, so the slope on `n_items` should be negative. It is Macaskill's sample-size variant of
    the funnel test, reduced to its simplest form. `nan` when every contrast used the same assumed n,
    which is itself worth knowing: it means the sizes came from --default-n and the test is blind.
    """
    y_arr = np.asarray(list(y), dtype=float)
    n_arr = np.asarray(list(n_items), dtype=float)
    k = int(y_arr.size)
    out = {"k": float(k), "slope": float("nan"), "p": float("nan"), "distinct_n": float("nan")}
    if k < 3:
        return out
    out["distinct_n"] = float(len(set(n_arr.tolist())))
    if float(np.ptp(n_arr)) == 0.0:
        return out
    design = np.column_stack([np.ones(k), n_arr])
    beta, *_ = np.linalg.lstsq(design, y_arr, rcond=None)
    resid = y_arr - design @ beta
    df = k - 2
    sigma2 = _residual_variance(resid, y_arr, df)
    out["slope"] = float(beta[1])
    if sigma2 > 0:
        se_slope = math.sqrt(sigma2 * np.linalg.pinv(design.T @ design)[1, 1])
        if se_slope > 0:
            out["p"] = float(2 * stats.t.sf(abs(beta[1] / se_slope), df))
    return out


def trim_and_fill(y: Sequence[float], v: Sequence[float], *, side: str = "auto",
                  max_iter: int = 40) -> dict[str, Any]:
    """Duval-Tweedie trim-and-fill with the L0 rank estimator of the number of missing studies.

    The algorithm: pool, centre the effects on the pooled mean, rank the absolute deviations, and
    from the sum of the ranks of the deviations on the over-represented side estimate how many
    studies are missing from the other side,
        L0 = (4 * S_r - k * (k + 1)) / (2 * k - 1)
    trim that many of the most extreme studies on the over-represented side, re-pool, and iterate to
    a fixed point. Then FILL: mirror the k0 most extreme observed studies about the trimmed mean
    (same variances) and pool the augmented set. The filled estimate is what the pooled effect would
    be if the funnel's missing side existed and were exactly symmetric. It is a sensitivity
    analysis, not a corrected estimate: nothing here observes the missing studies.

    `side="auto"` takes the side from the sign of the random-effects estimate, which is the
    convention when the expected direction of selection is the direction of the reported effect.
    """
    y_arr = np.asarray(list(y), dtype=float)
    v_arr = np.asarray(list(v), dtype=float)
    k = int(y_arr.size)
    out: dict[str, Any] = {"k": k, "k0": 0, "mu_observed": float("nan"), "mu_filled": float("nan"),
                           "ci_low_filled": float("nan"), "ci_high_filled": float("nan"),
                           "side": side, "converged": False}
    if k < 3:
        return out
    observed = dersimonian_laird(y_arr, v_arr)
    out["mu_observed"] = observed.mu
    if side == "auto":
        side = "right" if observed.mu >= 0 else "left"
    out["side"] = side
    sign = 1.0 if side == "right" else -1.0

    kept = np.ones(k, dtype=bool)
    k0 = 0
    for _ in range(max_iter):
        mu = dersimonian_laird(y_arr[kept], v_arr[kept]).mu
        dev = (y_arr - mu) * sign          # positive = on the over-represented side
        order = np.argsort(np.abs(dev), kind="mergesort")
        ranks = np.empty(k, dtype=float)
        ranks[order] = np.arange(1, k + 1, dtype=float)
        s_r = float(ranks[dev > 0].sum())
        l0 = (4.0 * s_r - k * (k + 1)) / (2.0 * k - 1.0)
        new_k0 = int(max(0, min(round(l0), k - 2)))
        if new_k0 == k0:
            out["converged"] = True
            break
        k0 = new_k0
        # trim the k0 most extreme studies on the over-represented side
        cand = np.argsort(-dev, kind="mergesort")[:k0]
        kept = np.ones(k, dtype=bool)
        kept[cand] = False
    out["k0"] = k0
    if k0 == 0:
        out["mu_filled"] = observed.mu
        out["ci_low_filled"], out["ci_high_filled"] = observed.ci_low, observed.ci_high
        return out
    mu_trim = dersimonian_laird(y_arr[kept], v_arr[kept]).mu
    dev = (y_arr - mu_trim) * sign
    extreme = np.argsort(-dev, kind="mergesort")[:k0]
    y_fill = np.concatenate([y_arr, 2.0 * mu_trim - y_arr[extreme]])
    v_fill = np.concatenate([v_arr, v_arr[extreme]])
    filled = dersimonian_laird(y_fill, v_fill)
    out["mu_filled"] = filled.mu
    out["ci_low_filled"], out["ci_high_filled"] = filled.ci_low, filled.ci_high
    return out


def null_fill_sensitivity(y: Sequence[float], v: Sequence[float], *, max_add: int = 500) -> dict[str, Any]:
    """A Copas-style bound: how many unreported NULL contrasts would flatten the pooled effect.

    The Copas selection model needs more information than this data has (it wants the selection
    probability as a function of precision, and with k around five it is not estimable). This is the
    same logic reduced to something the data can carry: null contrasts (y = 0, variance = the median
    observed variance) are added one at a time and the pooled effect is recomputed. Two numbers come
    out: the pooled effect after adding ONE null per observed contrast - the world in which every
    ablation that was run and came out null went unreported, one for one - and the number of nulls
    needed to halve the pooled effect. Small numbers here mean the finding is fragile to exactly the
    selection the design invites.
    """
    y_arr = np.asarray(list(y), dtype=float)
    v_arr = np.asarray(list(v), dtype=float)
    k = int(y_arr.size)
    out: dict[str, Any] = {"k": k, "mu_observed": float("nan"), "mu_one_null_each": float("nan"),
                           "nulls_to_halve": -1, "nulls_to_ci_crosses_zero": -1}
    if k < 3:
        return out
    v_null = float(np.median(v_arr))
    observed = dersimonian_laird(y_arr, v_arr)
    out["mu_observed"] = observed.mu
    target = observed.mu / 2.0
    crossed = False
    for m in range(1, max_add + 1):
        yy = np.concatenate([y_arr, np.zeros(m)])
        vv = np.concatenate([v_arr, np.full(m, v_null)])
        p = dersimonian_laird(yy, vv)
        if m == k:
            out["mu_one_null_each"] = p.mu
        if out["nulls_to_halve"] < 0 and abs(p.mu) <= abs(target):
            out["nulls_to_halve"] = m
        if not crossed and p.ci_low <= 0.0 <= p.ci_high:
            out["nulls_to_ci_crosses_zero"] = m
            crossed = True
        if out["nulls_to_halve"] > 0 and crossed and m >= k:
            break
    return out


def sign_test(y: Sequence[float]) -> dict[str, float]:
    """Share of contrasts favouring the authors' component, with an exact binomial p against 0.5.

    This is the plainest bias diagnostic there is, and for this data the most informative. If a
    component genuinely helps sometimes and not others, roughly a fifth to a third of contrasts
    should come out the wrong way. A distribution where nearly every contrast favours the component
    is not evidence that every component works; it is what a literature looks like when the null
    contrasts were never written down.
    """
    arr = np.asarray(list(y), dtype=float)
    k = int(arr.size)
    favour = int((arr > 0).sum())
    ties = int((arr == 0).sum())
    p = float(stats.binomtest(favour, k - ties, 0.5).pvalue) if k - ties > 0 else float("nan")
    return {"k": float(k), "favouring": float(favour), "ties": float(ties),
            "share": favour / k if k else float("nan"), "p_binomial": p}


def bias_diagnostics(papers: pd.DataFrame, contrasts: pd.DataFrame, pooled: pd.DataFrame,
                     *, min_papers: int = MIN_PAPERS) -> pd.DataFrame:
    """Egger + trim-and-fill + null-fill + sign share, per dimension that was pooled at all."""
    rows = []
    if pooled.empty:
        return pd.DataFrame(columns=BIAS_COLUMNS)
    for dim in pooled.loc[pooled["pooled"] == 1, "dimension"]:
        g = papers[papers["dimension"] == dim]
        if len(g) < min_papers:
            continue
        egger = eggers_test(g["y"].tolist(), g["v"].tolist())
        tf = trim_and_fill(g["y"].tolist(), g["v"].tolist())
        nf = null_fill_sensitivity(g["y"].tolist(), g["v"].tolist())
        sg_papers = sign_test(g["y"].tolist())
        sg_contrasts = sign_test(contrasts.loc[contrasts["dimension"] == dim, "rel_effect"].tolist())
        size = small_study_test_by_size(g["y"].tolist(), g["n_items"].tolist())
        shrink_tf = ((tf["mu_observed"] - tf["mu_filled"]) / tf["mu_observed"]
                     if tf["mu_observed"] not in (0.0,) and np.isfinite(tf["mu_observed"])
                     and np.isfinite(tf["mu_filled"]) else float("nan"))
        shrink_nf = ((nf["mu_observed"] - nf["mu_one_null_each"]) / nf["mu_observed"]
                     if nf["mu_observed"] not in (0.0,) and np.isfinite(nf["mu_observed"])
                     and np.isfinite(nf["mu_one_null_each"]) else float("nan"))
        finite = [x for x in (shrink_tf, shrink_nf) if np.isfinite(x)]
        rows.append({
            "dimension": dim,
            "n_papers": len(g),
            "n_contrasts": int((contrasts["dimension"] == dim).sum()),
            "egger_intercept": egger["intercept"], "egger_t": egger["t"], "egger_p": egger["p"],
            "trimfill_k0": tf["k0"], "mu_observed": tf["mu_observed"], "mu_filled": tf["mu_filled"],
            "trimfill_ci_low": tf["ci_low_filled"], "trimfill_ci_high": tf["ci_high_filled"],
            "trimfill_shrinkage": shrink_tf,
            "nullfill_shrinkage": shrink_nf,
            "discount": max(finite) if finite else float("nan"),
            "size_slope": size["slope"], "size_p": size["p"], "distinct_n": size["distinct_n"],
            "mu_one_null_each": nf["mu_one_null_each"],
            "nulls_to_halve": nf["nulls_to_halve"],
            "nulls_to_ci_crosses_zero": nf["nulls_to_ci_crosses_zero"],
            "sign_share_papers": sg_papers["share"], "sign_p_papers": sg_papers["p_binomial"],
            "sign_share_contrasts": sg_contrasts["share"], "sign_p_contrasts": sg_contrasts["p_binomial"],
        })
    return pd.DataFrame(rows, columns=BIAS_COLUMNS)


def bias_verdict(bias: pd.DataFrame, pooled: pd.DataFrame) -> dict[str, Any]:
    """A single stated verdict on how far the pooled effects should be discounted.

    Stated as a rule rather than a judgement call, so it is reproducible. Each dimension carries its
    OWN discount - the larger of its trim-and-fill shrinkage and its one-null-per-contrast shrinkage
    - because the two diagnostics disagree per dimension and taking a maximum across dimensions
    would let the noisiest dimension set the discount for all of them. The headline number reported
    here is the MEDIAN of those per-dimension discounts, with the range beside it; it describes the
    literature, while the discount actually applied to each effect is that dimension's own.

    The sign share decides the wording. A literature in which more than 85% of contrasts favour the
    authors' own component is described as what publication bias looks like, because at any plausible
    true effect size a component that helps some of the time in some systems would produce more
    dissent than that.
    """
    if bias.empty:
        return {"verdict": "no dimension had enough papers for a bias diagnostic",
                "overall_sign_share": float("nan"), "discount": float("nan"),
                "discount_by_dimension": {}}
    per_dim = {str(r["dimension"]): float(r["discount"]) for _, r in bias.iterrows()
               if np.isfinite(r["discount"])}
    values = sorted(per_dim.values())
    discount = float(np.median(values)) if values else float("nan")
    share = float(np.average(bias["sign_share_contrasts"], weights=bias["n_contrasts"])) \
        if bias["n_contrasts"].sum() else float("nan")
    if not np.isfinite(share):
        words = "sign share not computable"
    elif share >= 0.85:
        words = ("the sign distribution IS what publication bias looks like: "
                 f"{share:.0%} of contrasts favour the authors' own component. Read every pooled "
                 "effect below as an upper bound and not as an estimate")
    elif share >= 0.7:
        words = (f"{share:.0%} of contrasts favour the authors' own component - a strong asymmetry, "
                 "consistent with selective reporting as well as with real effects; the pooled "
                 "figures are upper bounds")
    else:
        words = (f"{share:.0%} of contrasts favour the authors' own component, which is enough "
                 "dissent that the pooled effects are not purely a reporting artefact; they remain "
                 "upper bounds")
    egger_flagged = [str(r["dimension"]) for _, r in bias.iterrows()
                     if np.isfinite(r["egger_p"]) and r["egger_p"] < 0.10]
    size_flagged = [str(r["dimension"]) for _, r in bias.iterrows()
                    if np.isfinite(r["size_p"]) and r["size_p"] < 0.10]
    return {
        "verdict": words,
        "overall_sign_share": share,
        "discount": discount,
        "discount_range": [values[0], values[-1]] if values else [],
        "discount_by_dimension": per_dim,
        "discount_basis": ("per dimension, the larger of its trim-and-fill and "
                           "one-null-per-contrast shrinkage; headline = median over dimensions"),
        "egger_flagged_dimensions": egger_flagged,
        "size_test_flagged_dimensions": size_flagged,
        "egger_caveat": ("Egger's test regresses the effect on its own approximated precision, and "
                         "that precision is computed FROM the two arm scores, so part of any funnel "
                         "asymmetry is induced by the variance model rather than by selection. The "
                         "size-based test (size_p: the effect regressed on the benchmark's item "
                         "count) is free of that circularity and is the one to read; where "
                         "distinct_n is 1 even that test is blind, because every contrast in the "
                         "dimension used the same assumed default benchmark size."),
        "n_dimensions_diagnosed": len(bias),
    }


def credible_after_discount(pooled: pd.DataFrame, bias: pd.DataFrame, *, discount: float,
                            threshold: float = 0.02,
                            per_dimension: dict[str, float] | None = None) -> pd.DataFrame:
    """Which pooled dimensions survive their own discount: the only "finding" column in the output.

    A dimension survives when, after ITS OWN discount (from its own bias diagnostics; the headline
    median is only the fallback for a dimension with no diagnostic), the discounted lower end of the
    confidence interval still clears `threshold` - 2% relative by default, the smallest effect worth
    a design recommendation - AND the trim-and-fill estimate still has the same sign as the pooled
    one. Two independent ways to fail, both reported, because with four or five papers a dimension
    can pass one and fail the other on noise alone.
    """
    if pooled.empty:
        return pd.DataFrame(columns=CREDIBLE_COLUMNS)
    per_dimension = per_dimension or {}
    rows = []
    for _, r in pooled[pooled["pooled"] == 1].iterrows():
        b = bias[bias["dimension"] == r["dimension"]]
        mu_filled = float(b["mu_filled"].iloc[0]) if len(b) else float("nan")
        own = per_dimension.get(str(r["dimension"]), discount)
        factor = 1.0 - (own if np.isfinite(own) else 0.0)
        factor = min(max(factor, 0.0), 1.0)
        disc_mu = r["mu_rel"] * factor
        disc_lo = r["ci_low"] * factor
        rows.append({
            "dimension": r["dimension"],
            "n_papers": int(r["n_papers"]), "n_contrasts": int(r["n_contrasts"]),
            "mu_rel": r["mu_rel"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "i2": r["i2"],
            "discount_factor": factor,
            "mu_discounted": disc_mu, "ci_low_discounted": disc_lo,
            "mu_trimfill": mu_filled,
            "ci_excludes_zero": int(r["ci_low"] > 0 or r["ci_high"] < 0),
            "ew_ci_excludes_zero": int(np.isfinite(r["ew_ci_low"])
                                       and (r["ew_ci_low"] > 0 or r["ew_ci_high"] < 0)),
            "pi_excludes_zero": int(np.isfinite(r["pi_low"]) and (r["pi_low"] > 0 or r["pi_high"] < 0)),
            "survives_discount": int(disc_lo > threshold and np.isfinite(mu_filled)
                                     and np.sign(mu_filled) == np.sign(r["mu_rel"])),
        })
    out = pd.DataFrame(rows, columns=CREDIBLE_COLUMNS)
    return out.sort_values("mu_rel", ascending=False).reset_index(drop=True)


def sensitivity_over_n(candidates: pd.DataFrame, classifications: dict[str, dict[str, Any]],
                       own: pd.DataFrame, *, ns: Sequence[int] = SENSITIVITY_N,
                       min_papers: int = MIN_PAPERS) -> pd.DataFrame:
    """Re-pool at other assumed benchmark sizes, to show what the variance model is doing.

    The assumed item count enters only the weights, never the effects, so the point estimates should
    barely move; the intervals will. If a pooled estimate DOES move with the assumed n, it is being
    driven by one imprecise contrast and should not be quoted.
    """
    rows = []
    for n in ns:
        contrasts, _ = build_contrasts(candidates, classifications, own, default_n=n)
        table, _ = pool_by_dimension(contrasts, min_papers=min_papers)
        for _, r in table[table["pooled"] == 1].iterrows():
            rows.append({"default_n": n, "dimension": r["dimension"], "mu_rel": r["mu_rel"],
                         "ci_low": r["ci_low"], "ci_high": r["ci_high"], "i2": r["i2"],
                         "tau2": r["tau2"], "n_papers": int(r["n_papers"])})
    return pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)


CONF_SENSITIVITY_COLUMNS = ["conf_floor", "dimension", "n_papers", "n_contrasts", "mu_rel",
                            "ci_low", "ci_high", "i2", "pooled"]


def sensitivity_over_confidence(candidates: pd.DataFrame, cache: dict[str, dict[str, Any]],
                                dims: Sequence[dict[str, Any]], own: pd.DataFrame,
                                *, floors: Sequence[float] = (0.4, 0.5, 0.6, 0.7),
                                min_papers: int = MIN_PAPERS,
                                default_n: int = DEFAULT_N) -> pd.DataFrame:
    """Re-run the whole pooling at several confidence floors, from the cached raw answers.

    The floor is where the classifier's judgement enters the analysis, so it is the assumption most
    worth showing. A dimension whose pooled effect appears only at a loose floor is a dimension held
    up by labels the classifier itself was unsure of, and is reported as such rather than quoted.
    No model call: every floor is applied to the same cached answers.
    """
    rows = []
    for floor in floors:
        resolved = resolve_classifications(cache, dims, conf_floor=floor)
        contrasts, _ = build_contrasts(candidates, resolved, own, default_n=default_n)
        table, _ = pool_by_dimension(contrasts, min_papers=min_papers)
        for _, r in table.iterrows():
            rows.append({"conf_floor": floor, "dimension": r["dimension"],
                         "n_papers": int(r["n_papers"]), "n_contrasts": int(r["n_contrasts"]),
                         "mu_rel": r["mu_rel"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                         "i2": r["i2"], "pooled": int(r["pooled"])})
    return pd.DataFrame(rows, columns=CONF_SENSITIVITY_COLUMNS)


# ------------------------------------------------------------------------------------------------
# step 6: figures
# ------------------------------------------------------------------------------------------------
def _wrap(text: str, width: int = 118) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width=width))


def _caption(fig: Any, text: str, *, fontsize: float = 6.2, width: int = 118) -> None:
    """Put the caveat under the axes, growing the figure to make room for it.

    `tight_layout(rect=...)` on its own cannot do this: the rectangle is in figure fractions, so a
    caption that runs to eight lines silently lands on top of the x-axis label. The figure is
    stretched by the height the wrapped caption actually needs, and the axes are then laid out in
    what is left. Every figure this script writes carries the upper-bound caveat, so the caption is
    never optional and the layout has to assume it is long.
    """
    wrapped = _wrap(text, width)
    lines = wrapped.count("\n") + 1
    needed = lines * (fontsize * 1.6 / 72.0) + 0.18   # inches
    w, h = fig.get_size_inches()
    fig.set_size_inches(w, h + needed, forward=True)
    fig.tight_layout(rect=(0, needed / (h + needed), 1, 1))
    fig.text(0.008, 0.012, wrapped, fontsize=fontsize, va="bottom", ha="left", style="italic")


def render_forest(dimension: str, papers: pd.DataFrame, pooled_row: pd.Series,
                  bias_row: pd.Series | None, out_stem: Path) -> list[Path]:
    """One forest plot: paper-level effects, the pooled diamond, the prediction interval."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    g = papers[papers["dimension"] == dimension].sort_values("y").reset_index(drop=True)
    k = len(g)
    se = np.sqrt(g["v"].to_numpy())
    lo, hi = g["y"].to_numpy() - 1.96 * se, g["y"].to_numpy() + 1.96 * se
    height = 2.7 + 0.32 * k
    fig, ax = plt.subplots(figsize=(9.5, height))
    ys = np.arange(k)
    ax.axvline(0.0, color="#888888", linewidth=0.9, linestyle="--")
    weights = (1.0 / g["v"].to_numpy())
    sizes = 30 + 170 * weights / weights.max()
    ax.hlines(ys, lo, hi, color="#33506e", linewidth=1.1)
    ax.scatter(g["y"], ys, s=sizes, color="#33506e", zorder=3, marker="s")
    labels = [f"{r.record_id[:28]}  ({r.n_contrasts} contrast{'s' if r.n_contrasts > 1 else ''})"
              for r in g.itertuples(index=False)]
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.set_ylim(-1.95, k - 0.4)

    mu, c_lo, c_hi = pooled_row["mu_rel"], pooled_row["ci_low"], pooled_row["ci_high"]
    ax.add_patch(plt.Polygon([[c_lo, -0.9], [mu, -0.65], [c_hi, -0.9], [mu, -1.15]],
                             closed=True, facecolor="#b03a2e", edgecolor="#b03a2e", zorder=4))
    if np.isfinite(pooled_row["pi_low"]):
        ax.hlines(-1.55, pooled_row["pi_low"], pooled_row["pi_high"], color="#b03a2e",
                  linewidth=1.0, linestyle=":")
        ax.text(pooled_row["pi_high"], -1.55, "  95% prediction interval", va="center",
                fontsize=7, color="#b03a2e")
    if bias_row is not None and np.isfinite(bias_row.get("mu_filled", float("nan"))):
        ax.scatter([bias_row["mu_filled"]], [-0.9], marker="|", s=180, color="#1a7f5a", zorder=5)
        ax.text(bias_row["mu_filled"], -0.45, f"trim-and-fill {bias_row['mu_filled']:+.3f}",
                fontsize=7, color="#1a7f5a", ha="center", va="bottom")

    ax.set_xlabel("relative effect of the component:  (with - without) / with\n"
                  "positive = the paper's own component helped", fontsize=8.5)
    ax.set_title(
        f"{dimension}: pooled {mu:+.3f} (95% CI {c_lo:+.3f} to {c_hi:+.3f}), "
        f"{int(pooled_row['n_papers'])} papers / {int(pooled_row['n_contrasts'])} contrasts, "
        f"I2 = {pooled_row['i2']:.0f}%",
        fontsize=10, loc="left")
    ax.tick_params(axis="x", labelsize=8)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    _caption(fig, f"Published ablations of `{dimension}`, pooled by DerSimonian-Laird random "
                  f"effects over papers (contrasts within a paper averaged first); the square area "
                  f"is the paper's weight and the whiskers are 95% intervals from an APPROXIMATED "
                  f"variance (papers publish none). {UPPER_BOUND_CAVEAT}")
    return _save(fig, out_stem)


def render_funnel(papers: pd.DataFrame, pooled: pd.DataFrame, out_stem: Path) -> list[Path]:
    """One funnel plot over every pooled dimension, each dimension centred on its own pooled mean.

    Centring per dimension is what makes a single funnel legible here: the dimensions have different
    true effects, and an uncentred funnel over all of them would show that heterogeneity rather than
    any asymmetry. The pseudo-confidence funnel is drawn around zero on the centred scale.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pooled_dims = pooled.loc[pooled["pooled"] == 1, ["dimension", "mu_rel"]]
    g = papers.merge(pooled_dims, on="dimension", how="inner").copy()
    fig, ax = plt.subplots(figsize=(8.2, 6.4))
    if g.empty:
        ax.text(0.5, 0.5, "no dimension had enough papers to pool", ha="center", va="center")
        ax.axis("off")
        return _save(fig, out_stem)
    g["centred"] = g["y"] - g["mu_rel"]
    g["se"] = np.sqrt(g["v"])
    se_max = float(g["se"].max()) * 1.08
    grid = np.linspace(1e-4, se_max, 100)
    for z, style in ((1.96, "--"), (2.576, ":")):
        ax.plot(z * grid, grid, color="#999999", linewidth=0.8, linestyle=style)
        ax.plot(-z * grid, grid, color="#999999", linewidth=0.8, linestyle=style)
    ax.axvline(0.0, color="#888888", linewidth=0.9)
    markers = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">", "h"]
    for i, (dim, sub) in enumerate(g.groupby("dimension", sort=True)):
        ax.scatter(sub["centred"], sub["se"], s=34, marker=markers[i % len(markers)],
                   label=f"{dim} (k={len(sub)})", alpha=0.85)
    ax.invert_yaxis()
    ax.set_xlabel("paper-level relative effect, centred on its dimension's pooled effect", fontsize=8.5)
    ax.set_ylabel("approximated standard error (larger = less precise, lower down)", fontsize=8.5)
    ax.set_title("Funnel plot, published harness ablations, all pooled dimensions", fontsize=10, loc="left")
    ax.legend(fontsize=6.6, loc="lower left", frameon=False, ncol=2)
    ax.tick_params(labelsize=8)
    _caption(fig, "Funnel asymmetry here would be evidence of selective reporting, but the standard "
                  "errors are APPROXIMATED from the two arm scores (papers publish no SEs), so a "
                  "larger effect mechanically gets a larger SE and part of any asymmetry is induced "
                  "by the variance model rather than by selection. Read this plot together with the "
                  "size-based small-study test and the sign shares in "
                  "data/analysis/ablation_bias.csv, not on its own. " + UPPER_BOUND_CAVEAT,
             width=104)
    return _save(fig, out_stem)


def _save(fig: Any, out_stem: Path) -> list[Path]:
    import matplotlib.pyplot as plt
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("svg", "pdf"):
        p = out_stem.with_suffix(f".{ext}")
        fig.savefig(p, format=ext, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths


# ------------------------------------------------------------------------------------------------
# reporting
# ------------------------------------------------------------------------------------------------
def write_tables(out_dir: Path, *, labels: pd.DataFrame, contrasts: pd.DataFrame,
                 drops: Counter, pooled: pd.DataFrame, papers: pd.DataFrame,
                 bias: pd.DataFrame, credible: pd.DataFrame,
                 sensitivity: pd.DataFrame | None, summary: dict[str, Any],
                 conf_sensitivity: pd.DataFrame | None = None, suffix: str = "") -> list[Path]:
    """Every table this script writes. `suffix` ("_corpus" under --corpus) keeps the coded-set
    outputs untouched when the corpus-wide pooling is written beside them."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    frames = {
        "ablation_labels": labels,
        "ablation_contrasts": contrasts,
        "ablation_drops": pd.DataFrame(sorted(drops.items(), key=lambda kv: -kv[1]),
                                       columns=["reason", "rows"]),
        "ablation_pooled": pooled,
        "ablation_paper_effects": papers,
        "ablation_bias": bias,
        "ablation_credible": credible,
    }
    if sensitivity is not None:
        frames["ablation_sensitivity_n"] = sensitivity
    if conf_sensitivity is not None:
        frames["ablation_sensitivity_confidence"] = conf_sensitivity
    for name, frame in frames.items():
        path = out_dir / f"{name}{suffix}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        written.append(path)
    path = out_dir / f"ablation_summary{suffix}.json"
    path.write_text(json.dumps(summary, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    written.append(path)
    return written


def print_report(summary: dict[str, Any], pooled: pd.DataFrame, bias: pd.DataFrame,
                 credible: pd.DataFrame, drops: Counter) -> None:
    print("\n" + "=" * 100)
    print("META-ANALYSIS OF PUBLISHED HARNESS ABLATIONS (RQ3)")
    print("=" * 100)
    f = summary["funnel"]
    print(f"candidate reject rows considered : {f['candidate_rows']:,} "
          f"({f['candidate_labels']:,} distinct system/label pairs)")
    print(f"classified                       : {f['classified_labels']:,}  "
          f"(cache hits {f['cache_hits']:,}, model calls {f['model_calls']})")
    print(f"contrasts formed                 : {f['contrasts']:,} "
          f"over {f['papers']} papers, {f['systems']} systems, {f['dimensions']} dimensions")
    print("\nrows dropped, by reason:")
    for reason, n in sorted(drops.items(), key=lambda kv: -kv[1]):
        print(f"  {n:6,}  {reason}")
    print("\nPOOLED EFFECT BY DIMENSION (relative change; positive = the component helped)")
    print("-" * 100)
    if pooled.empty:
        print("  no dimension produced a contrast")
    else:
        for _, r in pooled.iterrows():
            if r["pooled"] == 1:
                pp = (f"  {r['mu_pp']:+.1f}pp (n={int(r['pp_papers'])}p/{int(r['pp_contrasts'])}c)"
                      if r["pp_poolable"] else "  pp: n/a")
                print(f"  {r['dimension']:<26} {r['mu_rel']:+.3f}  "
                      f"[{r['ci_low']:+.3f},{r['ci_high']:+.3f}]  "
                      f"PI[{r['pi_low']:+.3f},{r['pi_high']:+.3f}]  "
                      f"papers={int(r['n_papers'])} contrasts={int(r['n_contrasts'])} "
                      f"I2={r['i2']:.0f}% sign+={r['share_favouring_component']:.0%}"
                      f"  |  EW {r['mean_rel_unweighted']:+.3f} "
                      f"[{r['ew_ci_low']:+.3f},{r['ew_ci_high']:+.3f}]{pp}")
            else:
                print(f"  {r['dimension']:<26} INSUFFICIENT EVIDENCE  papers={int(r['n_papers'])} "
                      f"contrasts={int(r['n_contrasts'])}  raw={r['raw_effects']}")
    print("\nPUBLICATION-BIAS DIAGNOSTICS")
    print("-" * 100)
    if bias.empty:
        print("  no dimension had enough papers")
    else:
        for _, r in bias.iterrows():
            n_distinct = int(r["distinct_n"]) if np.isfinite(r["distinct_n"]) else 0
            print(f"  {r['dimension']:<26} Egger p={r['egger_p']:.3f}  "
                  f"size-test p={r['size_p']:.3f} ({n_distinct} distinct n)  "
                  f"trim-fill k0={int(r['trimfill_k0'])} mu {r['mu_observed']:+.3f}->{r['mu_filled']:+.3f}  "
                  f"one-null-each {r['mu_one_null_each']:+.3f}  "
                  f"nulls-to-halve={int(r['nulls_to_halve'])}  "
                  f"sign+ {r['sign_share_contrasts']:.0%} (p={r['sign_p_contrasts']:.3g})  "
                  f"discount {r['discount']:.0%}")
    v = summary["bias_verdict"]
    print("\nVERDICT: " + _wrap(str(v["verdict"]), 96))
    if np.isfinite(v.get("discount", float("nan"))):
        rng = v.get("discount_range") or []
        span = f" (range {rng[0]:.0%} to {rng[-1]:.0%})" if rng else ""
        print(f"  median discount across dimensions: {v['discount']:.0%}{span}; "
              "each effect below is discounted by its own")
        print("  " + _wrap(str(v["discount_basis"]), 96))
    print("  " + _wrap(str(v.get("egger_caveat", "")), 96))
    print("\nAFTER THE DISCOUNT")
    print("-" * 100)
    if credible.empty:
        print("  nothing to assess")
    else:
        for _, r in credible.iterrows():
            flags = []
            if not r["ew_ci_excludes_zero"]:
                flags.append("equal-weight CI includes 0")
            if not r["pi_excludes_zero"]:
                flags.append("prediction interval includes 0")
            print(f"  {r['dimension']:<26} {r['mu_rel']:+.3f} -> {r['mu_discounted']:+.3f} "
                  f"(x{r['discount_factor']:.2f}; discounted CI low {r['ci_low_discounted']:+.3f})  "
                  f"{'CREDIBLE' if r['survives_discount'] else 'not credible after discount'}"
                  + (f"  [{'; '.join(flags)}]" if flags else ""))
    print("\n" + _wrap(UPPER_BOUND_CAVEAT, 98))
    print("=" * 100 + "\n")


# ------------------------------------------------------------------------------------------------
# --corpus: pool the coded-set contrasts together with the corpus-wide full-text harvest
# ------------------------------------------------------------------------------------------------
CORPUS_CONTRASTS = OUT_DIR / "corpus_ablation_contrasts.csv"
CORPUS_SUFFIX = "_corpus"
PROVENANCE_CODED = "coded_harvest"


def load_corpus_contrasts(path: Path, coded: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """The pool-eligible corpus contrasts, re-checked for duplicates against the LIVE coded set.

    `scripts/harvest_ablations_corpus.py` flags `already_in_coded_harvest` when it writes the file;
    the flag is recomputed here against the coded contrasts this run just built, so a later change
    to the coded harvest can never let a contrast be counted twice.
    """
    if not path.exists():
        raise SystemExit(f"{path} not found: run scripts/harvest_ablations_corpus.py first")
    df = pd.read_csv(path, dtype={"record_id": str, "system_id": str}, keep_default_na=False)
    missing = [c for c in CONTRAST_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(f"{path}: missing contrast column(s) {missing}")
    for c in ("confidence", "full_score", "ablated_score", "with_score", "without_score",
              "delta_raw", "rel_effect", "variance", "n_items", "scale"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["proportion"] = df["proportion"].astype(str).str.lower().isin(("true", "1"))
    stats_ = {"corpus_rows_in_file": len(df)}
    df = df[df["dimension"].astype(str).str.strip() != ""]
    df = df[np.isfinite(df["rel_effect"]) & np.isfinite(df["variance"]) & (df["variance"] > 0)]
    rules = flag_coded_duplicates(df, coded)
    stats_["already_in_coded_harvest"] = int((rules != "").sum())
    df = df[(rules == "").values].copy()
    if "provenance" not in df.columns:
        df["provenance"] = "corpus_fulltext"
    df["provenance"] = df["provenance"].replace("", "corpus_fulltext")
    stats_["corpus_contrasts_pooled"] = len(df)
    return df.reset_index(drop=True), stats_


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(timespec="seconds")


def harvest_snapshot(contrasts_path: Path, rows_in_file: int) -> dict[str, Any] | None:
    """The harvester's own facts (papers read, tier coverage, date) AS OF the contrast file pooled here.

    The harvest runs under Task Scheduler and rewrites its outputs as it goes, so its summary read
    later by anything else can describe a different snapshot from the one this run pooled. Copying
    those facts into `ablation_summary_corpus.json` at the moment the contrast file is read lets
    `scripts/make_rq3_tables.py` take every RQ3 number from ONE analysis run. `consistent` is False
    when the harvester's summary and outcomes on disk do not describe the contrast file just read
    (it was rewritten between the reads); the table builder refuses such a snapshot. None when the
    harvester's summary is not beside the contrast file (a test fixture, a hand-made file).
    """
    summary_path = contrasts_path.parent / "corpus_ablation_summary.json"
    outcomes_path = contrasts_path.parent / "corpus_ablation_outcomes.csv"
    if not summary_path.exists() or not outcomes_path.exists():
        return None
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        outcomes = pd.read_csv(outcomes_path, dtype=str, keep_default_na=False)
    except (OSError, ValueError) as exc:
        return {"consistent": False, "error": f"{type(exc).__name__}: {exc}"}
    tier_status: dict[str, dict[str, int]] = {}
    if {"tier", "status"} <= set(outcomes.columns):
        for (tier, status), n in outcomes.groupby(["tier", "status"]).size().items():
            tier_status.setdefault(str(tier), {})[str(status)] = int(n)
    extracted = int((outcomes["status"] == "extracted").sum()) if "status" in outcomes else -1
    # per prefilter tier: papers in it, papers the model has read, and that share as a number, so
    # anything quoting "how much of each tier" updates itself as the harvest proceeds.
    tier_coverage = {}
    for tier, statuses in sorted(tier_status.items()):
        papers = sum(statuses.values())
        read = statuses.get("extracted", 0)
        tier_coverage[tier] = {"papers": papers, "extracted": read,
                               "share_extracted": read / papers if papers else 0.0,
                               "pct_extracted": round(100.0 * read / papers, 1) if papers else 0.0}
    snap = {
        "harvest_updated_at": summary.get("updated_at"),
        "papers_extracted": summary.get("papers_extracted"),
        "papers_with_pool_eligible_contrast": summary.get("papers_with_pool_eligible_contrast"),
        "contrasts_after_guards": summary.get("contrasts_after_guards"),
        "pool_eligible_contrasts": summary.get("pool_eligible_contrasts"),
        "prefilter_tiers": (summary.get("prefilter") or {}).get("tiers"),
        "tier_status": tier_status,
        "tier_coverage": tier_coverage,
        "contrast_rows_read": int(rows_in_file),
        "mtimes": {"contrasts": _mtime(contrasts_path), "summary": _mtime(summary_path),
                   "outcomes": _mtime(outcomes_path)},
    }
    snap["consistent"] = bool(summary.get("contrasts_after_guards") == int(rows_in_file)
                              and summary.get("papers_extracted") == extracted)
    return snap


def combine_contrasts(coded: pd.DataFrame, corpus: pd.DataFrame) -> pd.DataFrame:
    """Coded-set + corpus contrasts in the contrast schema, with a `provenance` column."""
    cols = CONTRAST_COLUMNS + ["provenance"]
    a = coded.copy()
    a["provenance"] = PROVENANCE_CODED
    frames = [f[cols] for f in (a, corpus) if not f.empty]
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)


def revariance(frame: pd.DataFrame, default_n: int) -> pd.DataFrame:
    """The contrasts re-weighted at another assumed benchmark size (rows whose n was assumed only).

    Equivalent to rebuilding the coded contrasts with `build_contrasts(default_n=...)`: the assumed
    size enters `n_items` and the variance, and nothing else.
    """
    out = frame.copy()
    for i, r in out.iterrows():
        if str(r["n_source"]) != "default":
            continue
        var, _ = contrast_variance(abs(float(r["with_score"])), abs(float(r["without_score"])),
                                   proportion=bool(r["proportion"]), scale=float(r["scale"]),
                                   n_items=default_n)
        out.at[i, "variance"] = var
        out.at[i, "n_items"] = default_n
    return out


def credible_with_hk(credible: pd.DataFrame, pooled: pd.DataFrame, *, threshold: float = 0.02) -> pd.DataFrame:
    """`credible_after_discount` plus the same survival rule applied to the Hartung-Knapp bound."""
    if credible.empty:
        return pd.DataFrame(columns=CREDIBLE_COLUMNS_CORPUS)
    hk = pooled.set_index("dimension")
    out = credible.copy()
    out["hk_ci_low"] = [hk.at[d, "hk_ci_low"] for d in out["dimension"]]
    out["hk_ci_high"] = [hk.at[d, "hk_ci_high"] for d in out["dimension"]]
    out["hk_ci_excludes_zero"] = ((out["hk_ci_low"] > 0) | (out["hk_ci_high"] < 0)).astype(int)
    out["hk_ci_low_discounted"] = out["hk_ci_low"] * out["discount_factor"]
    out["survives_discount_hk"] = ((out["hk_ci_low_discounted"] > threshold)
                                   & np.isfinite(out["mu_trimfill"])
                                   & (np.sign(out["mu_trimfill"]) == np.sign(out["mu_rel"]))).astype(int)
    return out[CREDIBLE_COLUMNS_CORPUS]


def print_corpus_table(pooled: pd.DataFrame, credible: pd.DataFrame, corpus_stats: dict[str, Any]) -> None:
    print("CORPUS-WIDE POOLING (coded-set + full-text harvest): DL z interval beside Hartung-Knapp")
    print("-" * 100)
    print(f"corpus contrasts in file {corpus_stats.get('corpus_rows_in_file', 0):,}; "
          f"dropped as already in coded harvest {corpus_stats.get('already_in_coded_harvest', 0):,}; "
          f"pooled {corpus_stats.get('corpus_contrasts_pooled', 0):,}")
    surv = credible.set_index("dimension") if not credible.empty else pd.DataFrame()
    for _, r in pooled.iterrows():
        prov = (f"coded {int(r['n_papers_coded'])}p/{int(r['n_contrasts_coded'])}c + corpus "
                f"{int(r['n_papers_corpus'])}p/{int(r['n_contrasts_corpus'])}c")
        if r["pooled"] != 1:
            print(f"  {r['dimension']:<26} INSUFFICIENT  papers={int(r['n_papers'])}  ({prov})")
            continue
        flag = ""
        if not surv.empty and r["dimension"] in surv.index:
            s = surv.loc[r["dimension"]]
            flag = (("CREDIBLE" if s["survives_discount"] else "not credible")
                    + (" / HK credible" if s["survives_discount_hk"] else " / HK not credible"))
        print(f"  {r['dimension']:<26} {r['mu_rel']:+.3f}  z[{r['ci_low']:+.3f},{r['ci_high']:+.3f}]  "
              f"HK[{r['hk_ci_low']:+.3f},{r['hk_ci_high']:+.3f}]  "
              f"PI[{r['pi_low']:+.3f},{r['pi_high']:+.3f}]  k={int(r['n_papers'])} "
              f"I2={r['i2']:.0f}%  {flag}  ({prov})")
    print()


def run_corpus(args: argparse.Namespace, *, dims: Sequence[dict[str, Any]], candidates: pd.DataFrame,
               classifications: dict[str, dict[str, Any]], cache: dict[str, dict[str, Any]],
               own: pd.DataFrame, coded: pd.DataFrame, drops: Counter, cstats: dict[str, Any]) -> int:
    """The whole analysis again over coded-set + corpus contrasts, every output suffixed `_corpus`."""
    corpus, corpus_stats = load_corpus_contrasts(args.corpus_contrasts, coded)
    snapshot = harvest_snapshot(args.corpus_contrasts, corpus_stats["corpus_rows_in_file"])
    contrasts = combine_contrasts(coded, corpus)
    pooled, papers = pool_by_dimension(contrasts, min_papers=args.min_papers, corpus_columns=True)
    bias = bias_diagnostics(papers, contrasts, pooled, min_papers=args.min_papers)
    verdict = bias_verdict(bias, pooled)
    credible = credible_after_discount(pooled, bias, discount=verdict["discount"],
                                       per_dimension=verdict.get("discount_by_dimension"))
    credible = credible_with_hk(credible, pooled)
    sensitivity = conf_sensitivity = None
    if args.sensitivity:
        rows = []
        for n in SENSITIVITY_N:
            table, _ = pool_by_dimension(revariance(contrasts, n), min_papers=args.min_papers)
            for _, r in table[table["pooled"] == 1].iterrows():
                rows.append({"default_n": n, "dimension": r["dimension"], "mu_rel": r["mu_rel"],
                             "ci_low": r["ci_low"], "ci_high": r["ci_high"], "i2": r["i2"],
                             "tau2": r["tau2"], "n_papers": int(r["n_papers"])})
        sensitivity = pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)
        rows = []
        for floor in (0.4, 0.5, 0.6, 0.7):
            resolved = resolve_classifications(cache, dims, conf_floor=floor)
            coded_f, _ = build_contrasts(candidates, resolved, own, default_n=args.default_n)
            # corpus rows below the harvest's own floor (0.5) were dropped there and are not
            # re-admitted here, so at 0.4 only the coded-set part of the pool changes.
            corpus_f = corpus[corpus["confidence"] >= floor]
            table, _ = pool_by_dimension(combine_contrasts(coded_f, corpus_f), min_papers=args.min_papers)
            for _, r in table.iterrows():
                rows.append({"conf_floor": floor, "dimension": r["dimension"],
                             "n_papers": int(r["n_papers"]), "n_contrasts": int(r["n_contrasts"]),
                             "mu_rel": r["mu_rel"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                             "i2": r["i2"], "pooled": int(r["pooled"])})
        conf_sensitivity = pd.DataFrame(rows, columns=CONF_SENSITIVITY_COLUMNS)

    prov = Counter(contrasts["provenance"]) if not contrasts.empty else Counter()
    summary = {
        "caveat": UPPER_BOUND_CAVEAT,
        "mode": ("corpus: coded-set harvest + corpus-wide full-text harvest "
                 "(scripts/harvest_ablations_corpus.py)"),
        "funnel": {
            "reject_rows_not_own_system": len(candidates), "candidate_rows": len(candidates),
            "candidate_labels": int(candidates["label_key"].nunique()),
            "classified_labels": int(sum(1 for k in candidates["label_key"].unique()
                                         if k in classifications)),
            "cache_hits": int(cstats["labels_cached"]), "model_calls": int(cstats["calls"]),
            "contrasts": len(contrasts),
            "papers": int(contrasts["record_id"].nunique()) if not contrasts.empty else 0,
            "systems": int(contrasts["system_id"].nunique()) if not contrasts.empty else 0,
            "dimensions": int(contrasts["dimension"].nunique()) if not contrasts.empty else 0,
        },
        "provenance": {"contrasts": dict(prov),
                       "papers": ({k: int(g["record_id"].nunique())
                                   for k, g in contrasts.groupby("provenance")}
                                  if not contrasts.empty else {}),
                       **corpus_stats},
        "drops_coded_set": dict(sorted(drops.items(), key=lambda kv: -kv[1])),
        "variance_methods": dict(Counter(contrasts["var_method"])) if not contrasts.empty else {},
        "n_item_sources": dict(Counter(contrasts["n_source"])) if not contrasts.empty else {},
        "polarity_assumed": (int((contrasts["polarity"] == "higher_assumed").sum())
                             if not contrasts.empty else 0),
        "dimensions_poolable": int((pooled["pooled"] == 1).sum()) if not pooled.empty else 0,
        "pooled": pooled.to_dict(orient="records"),
        "bias": bias.to_dict(orient="records"),
        "bias_verdict": verdict,
        "credible_after_discount": credible.to_dict(orient="records"),
        "harvest_snapshot": snapshot,
        "hartung_knapp_note": ("hk_ci_* is the untruncated Hartung-Knapp-Sidik-Jonkman interval on "
                               "k-1 df around the same DL estimate; hk_narrower_than_z flags where it "
                               "is narrower than the z interval (observed dispersion below what the "
                               "approximated within-study variances imply)."),
        "settings": {"min_papers": args.min_papers, "default_n": args.default_n,
                     "conf_floor": args.conf_floor, "corpus_contrasts": str(args.corpus_contrasts)},
    }
    figures: list[str] = []
    if not args.no_render and not pooled.empty:
        for _, r in pooled[pooled["pooled"] == 1].iterrows():
            b = bias[bias["dimension"] == r["dimension"]]
            for path in render_forest(r["dimension"], papers, r, b.iloc[0] if len(b) else None,
                                      args.fig_dir / f"ablation_forest_{r['dimension']}{CORPUS_SUFFIX}"):
                figures.append(str(path))
        for path in render_funnel(papers, pooled, args.fig_dir / f"ablation_funnel{CORPUS_SUFFIX}"):
            figures.append(str(path))
    summary["figures"] = figures
    labels = labels_table(candidates, classifications)
    for path in write_tables(args.out_dir, labels=labels, contrasts=contrasts, drops=drops,
                             pooled=pooled, papers=papers, bias=bias, credible=credible,
                             sensitivity=sensitivity, conf_sensitivity=conf_sensitivity,
                             summary=summary, suffix=CORPUS_SUFFIX):
        log.info("wrote %s", path)
    print_report(summary, pooled, bias, credible, Counter(summary["drops_coded_set"]))
    print_corpus_table(pooled, credible, corpus_stats)
    return 0


# ------------------------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------------------------
def resolve_backend(name: str) -> tuple[Callable[..., Any] | None, str]:
    """(backend, exe). Imported lazily so the analysis path needs neither the CLI nor the SDK."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import screen_llm
    if name == "api":
        import code_system
        try:
            import anthropic
        except ImportError as exc:
            raise SystemExit("the 'anthropic' package is missing: pip install anthropic") from exc
        key = screen_llm.api_key()
        if not key:
            raise SystemExit("ANTHROPIC_API_KEY not found in .env or the environment")
        return code_system.make_api_backend(anthropic.Anthropic(api_key=key, max_retries=3, timeout=900.0)), ""
    exe = screen_llm.find_claude_exe() or ""
    if not exe:
        raise SystemExit("claude executable not found (set CLAUDE_CODE_EXE)")
    return screen_llm.vote_batch_claude_code, exe


def labels_table(candidates: pd.DataFrame, classifications: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Every candidate (system, label) with its classification: the audit trail for step 2."""
    rows = []
    for key, g in candidates.groupby("label_key", sort=True):
        head = g.iloc[0]
        cls = classifications.get(key, {})
        rows.append({
            "label_key": key, "system_id": head["system_id"], "label": head["label"],
            "n_rows": len(g), "records": ";".join(sorted(set(g["record_id"]))[:5]),
            "benchmarks": ";".join(sorted({str(b) for b in g["benchmark"] if str(b).strip()})[:5]),
            "category": cls.get("category", ""), "dimension": cls.get("dimension") or "",
            "direction": cls.get("direction", ""), "confidence": cls.get("confidence", ""),
            "demoted": cls.get("demoted", ""), "reason": cls.get("reason", ""),
            "classifier_model": cls.get("model", ""),
        })
    return pd.DataFrame(rows)


def main(argv: Sequence[str] | None = None, backend: Callable[..., Any] | None = None) -> int:
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    p.add_argument("--rejects", type=Path, default=REJECTS)
    p.add_argument("--results", type=Path, default=RESULTS)
    p.add_argument("--systems", type=Path, default=SYSTEMS)
    p.add_argument("--dimensions", type=Path, default=DIMENSIONS)
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--fig-dir", type=Path, default=FIG_DIR)
    p.add_argument("--cache", type=Path, default=CACHE)
    p.add_argument("--classify", action="store_true",
                   help="send uncached labels to the model (the only model call in this script)")
    p.add_argument("--backend", choices=("claude-code", "api"), default="claude-code")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--effort", default=None)
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p.add_argument("--limit", type=int, default=0, help="classify at most N labels (0 = all)")
    p.add_argument("--min-papers", type=int, default=MIN_PAPERS,
                   help="fewer independent papers than this and the dimension is not pooled")
    p.add_argument("--default-n", type=int, default=DEFAULT_N,
                   help="assumed benchmark item count where the split size is unknown")
    p.add_argument("--conf-floor", type=float, default=CONF_FLOOR,
                   help="classifications below this confidence are treated as unmapped")
    p.add_argument("--sensitivity", action="store_true", help="also re-pool at other assumed n")
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--corpus", action="store_true",
                   help="pool the coded-set contrasts TOGETHER WITH the corpus-wide full-text harvest "
                        "(scripts/harvest_ablations_corpus.py); every output is written with a "
                        "_corpus suffix and the coded-set outputs are not touched")
    p.add_argument("--corpus-contrasts", type=Path, default=CORPUS_CONTRASTS)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(list(argv) if argv is not None else None)
    logging.basicConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(message)s")

    dims = load_dimensions(args.dimensions)
    candidates = load_candidates(args.rejects)
    own = load_own_full_rows(args.results)
    names = load_system_names(args.systems)
    log.info("%d candidate reject rows, %d distinct (system, label) pairs, %d own full-system rows",
             len(candidates), candidates["label_key"].nunique(), len(own))

    cache = load_cache(args.cache)
    if args.classify and backend is None:
        os.environ.setdefault("ENABLE_CLAUDEAI_MCP_SERVERS", "false")
        backend, exe = resolve_backend(args.backend)
    else:
        exe = ""
    cache, cstats = classify_labels(
        candidates, dims, names, backend if args.classify or backend is not None else None,
        cache=cache, batch_size=args.batch_size, model=args.model, effort=args.effort, exe=exe,
        limit=args.limit)
    if not args.corpus or cstats["calls"]:
        save_cache(cache, args.cache)
    classifications = resolve_classifications(cache, dims, conf_floor=args.conf_floor)

    contrasts, drops = build_contrasts(candidates, classifications, own, default_n=args.default_n)
    if args.corpus:
        return run_corpus(args, dims=dims, candidates=candidates, classifications=classifications,
                          cache=cache, own=own, coded=contrasts, drops=drops, cstats=cstats)
    pooled, papers = pool_by_dimension(contrasts, min_papers=args.min_papers)
    bias = bias_diagnostics(papers, contrasts, pooled, min_papers=args.min_papers)
    verdict = bias_verdict(bias, pooled)
    credible = credible_after_discount(pooled, bias, discount=verdict["discount"],
                                       per_dimension=verdict.get("discount_by_dimension"))
    sensitivity = (sensitivity_over_n(candidates, classifications, own, min_papers=args.min_papers)
                   if args.sensitivity else None)
    conf_sensitivity = (sensitivity_over_confidence(candidates, cache, dims, own,
                                                    min_papers=args.min_papers,
                                                    default_n=args.default_n)
                        if args.sensitivity else None)

    cat_counts = Counter(c.get("category", "missing") for c in classifications.values())
    raw_cat_counts = Counter(str(c.get("raw_category") or "missing") for c in classifications.values())
    demotions = Counter(str(c.get("demoted") or "") for c in classifications.values())
    summary = {
        "caveat": UPPER_BOUND_CAVEAT,
        "funnel": {
            "reject_rows_not_own_system": len(candidates),
            "candidate_rows": len(candidates),
            "candidate_labels": int(candidates["label_key"].nunique()),
            "classified_labels": int(sum(1 for k in candidates["label_key"].unique() if k in classifications)),
            "cache_hits": int(cstats["labels_cached"]),
            "model_calls": int(cstats["calls"]),
            "labels_sent": int(cstats["labels_sent"]),
            "failed_batches": int(cstats["failed_batches"]),
            "tokens_in": int(cstats["tokens_in"]), "tokens_out": int(cstats["tokens_out"]),
            "cost_usd": round(float(cstats["cost_usd"]), 4),
            "contrasts": len(contrasts),
            "papers": int(contrasts["record_id"].nunique()) if not contrasts.empty else 0,
            "systems": int(contrasts["system_id"].nunique()) if not contrasts.empty else 0,
            "dimensions": int(contrasts["dimension"].nunique()) if not contrasts.empty else 0,
        },
        "label_categories": dict(sorted(cat_counts.items())),
        "label_categories_as_the_model_answered": dict(sorted(raw_cat_counts.items())),
        "demotions_to_unmapped": {k: v for k, v in sorted(demotions.items()) if k},
        "drops": dict(sorted(drops.items(), key=lambda kv: -kv[1])),
        "variance_methods": (dict(Counter(contrasts["var_method"])) if not contrasts.empty else {}),
        "n_item_sources": (dict(Counter(contrasts["n_source"])) if not contrasts.empty else {}),
        "polarity_assumed": int((contrasts["polarity"] == "higher_assumed").sum()) if not contrasts.empty else 0,
        "pooled": pooled.to_dict(orient="records"),
        "bias": bias.to_dict(orient="records"),
        "bias_verdict": verdict,
        "credible_after_discount": credible.to_dict(orient="records"),
        "settings": {"min_papers": args.min_papers, "default_n": args.default_n,
                     "conf_floor": args.conf_floor,
                     # what the cached answers were ACTUALLY produced by, not the CLI default of a
                     # later re-run: the analysis is re-run from cache far more often than the
                     # classification is, and --model on those re-runs means nothing.
                     "classifier_models": dict(sorted(Counter(
                         str(c.get("model") or "unknown") for c in classifications.values()).items())),
                     "classifier_model_this_run": args.model},
    }

    figures: list[str] = []
    if not args.no_render and not pooled.empty:
        for _, r in pooled[pooled["pooled"] == 1].iterrows():
            b = bias[bias["dimension"] == r["dimension"]]
            for path in render_forest(r["dimension"], papers, r,
                                      b.iloc[0] if len(b) else None,
                                      args.fig_dir / f"ablation_forest_{r['dimension']}"):
                figures.append(str(path))
                log.info("wrote %s (%d bytes)", path, path.stat().st_size)
        for path in render_funnel(papers, pooled, args.fig_dir / "ablation_funnel"):
            figures.append(str(path))
            log.info("wrote %s (%d bytes)", path, path.stat().st_size)
    summary["figures"] = figures

    labels = labels_table(candidates, classifications)
    for path in write_tables(args.out_dir, labels=labels, contrasts=contrasts, drops=drops,
                             pooled=pooled, papers=papers, bias=bias, credible=credible,
                             sensitivity=sensitivity, conf_sensitivity=conf_sensitivity,
                             summary=summary):
        log.info("wrote %s", path)
    print_report(summary, pooled, bias, credible, drops)
    return 0


if __name__ == "__main__":
    sys.exit(main())
