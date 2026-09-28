#!/usr/bin/env python
"""Build-time LaTeX fragments for the RQ3 section (section 7): tables and prose macros, never typed.

WHY THIS SCRIPT EXISTS
----------------------
The corpus-wide ablation harvest (`scripts/harvest_ablations_corpus.py`) was run in stages, and
every re-run moved every number in section 7. A number typed into the manuscript is a
number that goes stale silently. This script is the only thing allowed to put an RQ3 number into the
paper: it READS the existing analysis outputs and FORMATS them. It computes no inferential
statistic - a confidence interval, a discount, a correlation is always read from the file that
computed it - so the numbers in the PDF are exactly the numbers in `data/analysis/`. (The only
arithmetic here is descriptive: counting rows, and the range and quartiles of already-pooled
effects for `\\rqEffectRangeSurviving` / `\\rqEffectIQRSurviving`.)

It writes four fragments to `paper/tables/`, each headed by a comment naming its sources, each
source's mtime, and the generation time:

  rq3_pooled.tex    table float, label `tab:ablations`: one row per POOLED dimension
                    (`ablation_pooled_corpus.csv` + `ablation_credible_corpus.csv`)
  rq3_coverage.tex  table float, label `tab:coverage`: ablation density by layer against layer
                    silence, coded-set and corpus-wide (`ablation_coverage_*` from
                    `scripts/analyse_ablation_coverage.py`, default and `--corpus`)
  rq3_designs.tex   table float, label `tab:rq3-bounds`: the three RQ3 designs and the direction of
                    their bounds (`paper/tables/outcomes_summary.json`, `ablation_*_corpus`,
                    `data/tier3/pilot/pilot_summary.json`)
  rq3_macros.tex    `\\newcommand`s the prose uses, so a re-run updates sentences as well as tables.
                    Every macro is text-mode safe (signed numbers are wrapped in `\\ensuremath`);
                    the `*Pct` macros are bare numbers, the sentence adds `\\%`.

ONE SNAPSHOT
------------
The harvest runs under Task Scheduler and rewrites its outputs as it goes, so its own summary and
the pooled outputs can describe different snapshots. Every corpus number here comes from the
`ablation_*_corpus.*` outputs of ONE `analyse_ablations.py --corpus` run - including the harvester
facts (papers read, tier coverage, date), which that run copies into `ablation_summary_corpus.json`
under `harvest_snapshot` at the moment it reads the contrast file. The harvester's live summary is
read for one purpose only: if it no longer describes the snapshot that was pooled, the script fails
(re-run the analysis) rather than mix the two. The coverage outputs are checked against the same
run by their contrast counts.

FAILS LOUDLY
------------
A missing input file, a missing column or JSON key, a non-finite value where a number is due, or
inputs from different snapshots all stop the script with a non-zero exit BEFORE anything is
written. It never emits a placeholder number. `--allow-stale` downgrades exactly one check to a
warning - "the harvester has moved on since the analysis ran" - and the fragments then describe the
analysed snapshot, whose date they print; it never admits a missing value or a mixed snapshot.

It is idempotent: a fragment whose content (everything but the generation-time line) is unchanged is
not rewritten, so a re-run with the same inputs touches nothing.

THE TWO SENSITIVITY ANALYSES (the one exception to "computes no inferential statistic")
------------------------------------------------------------------------------------
Section 7 reports two sensitivity analyses a reviewer asked for, and their numbers are macros like
every other. Neither has an analysis output of its own, so this script computes them - but only by
calling the analysis scripts' OWN functions on the SAME snapshot, never by re-implementing a
statistic, and each first reproduces the published number it perturbs and refuses to build if it
cannot:

  pre-rule attribution   the harvest rows of the pooled snapshot are re-run through
                         `harvest_ablations_corpus.guard_row` with the seven classification rules
                         switched off; the layer densities go through
                         `analyse_ablation_coverage.coverage_by_layer`, which reproduces the
                         published rho on the rule-applied counts first. Question: do the mapping
                         rules manufacture the silence-density correlation?
  non-baseline keys      `analyse_outcomes`' own panel, contrast, bootstrap and permutation, run on
                         the cross-paper headline's keys minus those whose reference side is only
                         recurring baseline harnesses (`baseline_asymmetry`'s own rule), after the
                         full-key estimate is reproduced exactly. Question: is the headline
                         association a property of design or of baseline selection?

`--no-sensitivity` (tests only) skips both; the macro file then lacks their macros.

Run (after `analyse_ablations.py --corpus --sensitivity` and `analyse_ablation_coverage.py
--corpus`):
    python scripts/make_rq3_tables.py
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import math
import os
import statistics
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "paper" / "tables"

#: The design dimension the three-designs table and the `\\rqSV*` macros are about: it is the one
#: component that all three designs measure (tier 3 ablates self-verification).
FOCAL_DIMENSION = "self_verification"

#: The cross-paper design's headline contrast (the one the prose and the triangulation figure
#: quote). `check_headline` refuses to build if it is no longer detected and robust.
CROSS_PAPER_HEADLINE = "multi_agent_topology"

#: plain-language names for the cross-paper contrasts the designs table can show beneath the
#: headline (the contrast keys are `analyse_outcomes` identifiers, not words for a reader)
CONTRAST_LABELS = {"executable_verification": "executable checks vs none",
                   "any_retry": "any retry vs none", "any_compaction": "any compaction vs none",
                   "explicit_plan": "explicit plan vs none", "multi_agent": "multi- vs single-agent"}

#: Egger's intercept test flags a dimension below this p (the same cut `analyse_ablations.py`
#: uses for `egger_flagged_dimensions`, which is checked against the result).
EGGER_ALPHA = 0.10

#: the arm correlation at which the tier-3 analysis plan fixes its instance count (amendment 12a)
PLANNING_RHO = 0.7

#: Layers whose touched dimensions `\\rqFGHPaperCounts` lists.
SPARSE_LAYERS = ("F", "G", "H")

#: Prefix for a p-column cell: ragged right without the `array` package (acmart does not load it).
RAGGED = "\\raggedright "

#: `ablation_contrasts_corpus.csv` polarity: a metric whose name states no direction is taken as
#: higher-is-better and marked so by `analyse_ablations.orient_contrast`.
POLARITY_ASSUMED = "higher_assumed"
VAR_ASSUMED = "assumed_rel_se"

#: drop reasons the harvester applies BEFORE any classification rule is read; a row that stopped
#: there is untouched by the rules, so the pre-rule reconstruction leaves it as it was
PRE_CLASSIFICATION = frozenset({"malformed_row", "score_not_in_text", "scores_not_colocated",
                                "signed_delta_as_score", "stale_window"})
#: the sandbox layer, whose emptiness the pre-rule reconstruction tests
SANDBOX_LAYER = "G"
#: the two rules that reassign a sandbox-layer row to another dimension (the others drop it)
REMAP_OUT_OF_SANDBOX = ("sandbox_is_execution_feedback", "tools_ablation_is_context")
#: every rule that reads a sandbox-layer attribution (a row it drops named no G mechanism)
G_MAPPING_RULES = REMAP_OUT_OF_SANDBOX + ("tool_gating_is_tool_interface",)

PROVENANCE_CODED = "coded_harvest"
PROVENANCE_CORPUS = "corpus_fulltext"
TIER_ORDER = (("T10", "top-signal tier"), ("T3", "second"))

POOLED_REQUIRED = [
    "dimension", "pooled", "n_papers", "n_contrasts", "n_papers_coded", "n_papers_corpus",
    "mu_rel", "ci_low", "ci_high", "hk_ci_low", "hk_ci_high", "pi_low", "pi_high", "i2",
]
CREDIBLE_REQUIRED = [
    "dimension", "mu_rel", "mu_discounted", "discount_factor", "survives_discount",
    "survives_discount_hk", "pi_excludes_zero",
]
BIAS_REQUIRED = ["dimension", "egger_intercept", "egger_p"]
COVERAGE_REQUIRED = [
    "layer", "not_reported_pct", "dimensions", "dimensions_ablated", "contrasts",
    "contrasts_per_dimension", "in_correlation",
]
COVERAGE_CORPUS_REQUIRED = COVERAGE_REQUIRED + ["contrasts_coded_harvest"]
CONTRASTS_REQUIRED = ["record_id", "dimension", "provenance", "polarity", "rel_effect",
                      "var_method"]
HARVEST_ROWS_REQUIRED = ["record_id", "row_no", "drop_reason", "norm_dimension",
                         "guard_applied", "guards_matched"]

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December")


class RQ3InputError(RuntimeError):
    """An input is missing, incomplete or inconsistent: nothing may be written."""


# ------------------------------------------------------------------------------------------------
# inputs
# ------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Inputs:
    pooled: Path
    credible: Path
    bias: Path
    ablation_summary: Path
    coverage_coded_csv: Path
    coverage_coded_json: Path
    coverage_corpus_csv: Path
    coverage_corpus_json: Path
    harvest_summary: Path
    outcomes_summary: Path
    pilot_summary: Path
    dimensions: Path
    tier3_dir: Path
    contrasts: Path
    pilot_v2_summary: Path
    harvest_rows: Path
    harvest_outcomes: Path
    results: Path
    systems: Path
    sensitivity: bool = True

    @classmethod
    def default(cls, root: Path = ROOT) -> Inputs:
        a = root / "data" / "analysis"
        return cls(
            contrasts=a / "ablation_contrasts_corpus.csv",
            pilot_v2_summary=root / "data" / "tier3" / "pilot_v2" / "pilot_v2_summary.json",
            harvest_rows=a / "corpus_ablation_rows.csv",
            harvest_outcomes=a / "corpus_ablation_outcomes.csv",
            results=root / "data" / "results.csv",
            systems=root / "data" / "systems.json",
            pooled=a / "ablation_pooled_corpus.csv",
            credible=a / "ablation_credible_corpus.csv",
            bias=a / "ablation_bias_corpus.csv",
            ablation_summary=a / "ablation_summary_corpus.json",
            coverage_coded_csv=a / "ablation_coverage_by_layer.csv",
            coverage_coded_json=a / "ablation_coverage_summary.json",
            coverage_corpus_csv=a / "ablation_coverage_by_layer_corpus.csv",
            coverage_corpus_json=a / "ablation_coverage_summary_corpus.json",
            harvest_summary=a / "corpus_ablation_summary.json",
            outcomes_summary=root / "paper" / "tables" / "outcomes_summary.json",
            pilot_summary=root / "data" / "tier3" / "pilot" / "pilot_summary.json",
            dimensions=root / "schema" / "dimensions.json",
            tier3_dir=root / "data" / "tier3",
        )

    def files(self) -> list[Path]:
        out = [self.pooled, self.credible, self.bias, self.ablation_summary,
               self.coverage_coded_csv, self.coverage_coded_json, self.coverage_corpus_csv,
               self.coverage_corpus_json, self.harvest_summary, self.outcomes_summary,
               self.pilot_summary, self.dimensions, self.contrasts, self.pilot_v2_summary]
        if self.sensitivity:
            out += [self.harvest_rows, self.harvest_outcomes, self.results, self.systems]
        return out


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path, required: Sequence[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise RQ3InputError(f"missing input {rel(path)}")
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise RQ3InputError(f"{rel(path)}: missing column(s) {missing}")
        rows = list(reader)
    if not rows:
        raise RQ3InputError(f"{rel(path)} has no rows")
    return rows


def read_json(path: Path) -> Any:
    if not path.exists():
        raise RQ3InputError(f"missing input {rel(path)}")
    # the pilot summary carries bare NaN tokens; json accepts them, and `num` refuses them where a
    # number is due.
    return json.loads(path.read_text(encoding="utf-8"))


def need(obj: Any, dotted: str | Sequence[str], source: Path) -> Any:
    """`obj[a][b][c]` for `dotted="a.b.c"` (or `("a", "b.c")` when a key holds a dot), or a loud
    error naming the file and the key."""
    parts = dotted.split(".") if isinstance(dotted, str) else list(dotted)
    cur = obj
    for part in parts:
        if not isinstance(cur, Mapping) or part not in cur:
            raise RQ3InputError(f"{rel(source)}: missing key {'.'.join(parts)!r}")
        cur = cur[part]
    return cur


def num(value: Any, what: str) -> float:
    """A finite float or a loud error. Never a placeholder."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise RQ3InputError(f"{what}: not a number ({value!r})") from None
    if not math.isfinite(out):
        raise RQ3InputError(f"{what}: not finite ({value!r})")
    return out


def integer(value: Any, what: str) -> int:
    out = num(value, what)
    if out != int(out):
        raise RQ3InputError(f"{what}: expected an integer, got {value!r}")
    return int(out)


def flag(value: Any, what: str) -> bool:
    text = str(value).strip().lower()
    if text in ("1", "1.0", "true"):
        return True
    if text in ("0", "0.0", "false"):
        return False
    raise RQ3InputError(f"{what}: expected a 0/1 flag, got {value!r}")


def survival_threshold() -> float:
    """The survival threshold of `analyse_ablations.credible_after_discount`, read from its
    signature so the caption can never disagree with the analysis."""
    import inspect

    sys.path.insert(0, str(ROOT / "scripts"))
    import analyse_ablations

    param = inspect.signature(analyse_ablations.credible_after_discount).parameters.get("threshold")
    if param is None or param.default is inspect.Parameter.empty:
        raise RQ3InputError("cannot read the survival threshold from analyse_ablations")
    return float(param.default)


# ------------------------------------------------------------------------------------------------
# formatting (prose rules: signs shown, 3 decimals for effects, 1 for percentages, % escaped)
# ------------------------------------------------------------------------------------------------
LATEX_ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                 "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
                 "^": r"\textasciicircum{}"}


def tex(text: str) -> str:
    return "".join(LATEX_ESCAPES.get(ch, ch) for ch in str(text))


def breakable(text: str) -> str:
    """`tex`, with a permitted line break after each underscore (for identifiers in p-columns)."""
    return tex(text).replace(r"\_", r"\_\allowbreak{}")


def signed(x: float) -> str:
    s = f"{x:+.3f}"
    return "0.000" if s in ("+0.000", "-0.000") else s


def eff(x: float) -> str:
    """Signed effect, three decimals, in `\\ensuremath` (a real minus sign, safe in text mode)."""
    return rf"\ensuremath{{{signed(x)}}}"


def interval(lo: float, hi: float, *, sep: str = ", ") -> str:
    """Signed interval with its brackets; tables pass `sep=","` to save width."""
    return rf"\ensuremath{{[{signed(lo)}{sep}{signed(hi)}]}}"


def span(lo: float, hi: float) -> str:
    """`lo to hi`, both signed: a range, not an interval estimate."""
    return f"{eff(lo)} to {eff(hi)}"


def pct_number(share: float) -> str:
    """A share in [0, 1] as a bare percentage number, one decimal (the sentence adds the sign)."""
    return f"{share * 100:.1f}"


def pct(share: float) -> str:
    return pct_number(share) + r"\%"


def pct_value(value: float) -> str:
    """A value already in percent, one decimal, % escaped."""
    return f"{value:.1f}\\%"


def count(n: int) -> str:
    return f"{n:,}".replace(",", "{,}")


def pval(p: float) -> str:
    if p >= 0.01:
        return f"{p:.3f}"
    if p >= 0.001:
        return f"{p:.4f}"
    mant, exp = f"{p:.2e}".split("e")
    return rf"\ensuremath{{{mant} \times 10^{{{int(exp)}}}}}"


def join_prose(items: Sequence[str], empty: str = "none") -> str:
    items = list(items)
    if not items:
        return empty
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def prose_date(iso: Any, what: str) -> str:
    try:
        d = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        raise RQ3InputError(f"{what}: not an ISO timestamp ({iso!r})") from None
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


class Names:
    """Display names from the frozen schema: `Self-verification (E1)`, layer `E` names."""

    def __init__(self, path: Path):
        raw = read_json(path)
        dims = need(raw, "dimensions", path)
        layers = need(raw, "layers", path)
        self.dim = {d["key"]: (d["name"], d["id"], d["layer"]) for d in dims}
        self.layer = {lay["id"]: lay["name"] for lay in layers}
        self.path = path

    def _get(self, key: str) -> tuple[str, str, str]:
        if key not in self.dim:
            raise RQ3InputError(f"dimension {key!r} is not in {rel(self.path)}")
        return self.dim[key]

    def table(self, key: str) -> str:
        name, ident, _ = self._get(key)
        return f"{tex(name)} ({ident})"

    def prose(self, key: str) -> str:
        name, ident, _ = self._get(key)
        return f"{tex(name[:1].lower() + name[1:])} ({ident})"

    def layer_of(self, key: str) -> str:
        return self._get(key)[2]

    def order(self, key: str) -> tuple[str, int]:
        ident = self._get(key)[1]
        return ident[:1], int(ident[1:]) if ident[1:].isdigit() else 0

    def layer_name(self, layer: str) -> str:
        if layer not in self.layer:
            raise RQ3InputError(f"layer {layer!r} is not in {rel(self.path)}")
        return tex(self.layer[layer])


# ------------------------------------------------------------------------------------------------
# loading + consistency
# ------------------------------------------------------------------------------------------------
@dataclass
class Loaded:
    pooled: list[dict[str, str]]
    credible: dict[str, dict[str, str]]
    bias: list[dict[str, str]]
    summary: dict[str, Any]
    snapshot: dict[str, Any]
    cov_coded_rows: list[dict[str, str]]
    cov_coded: dict[str, Any]
    cov_corpus_rows: list[dict[str, str]]
    cov_corpus: dict[str, Any]
    harvest_live: dict[str, Any]
    outcomes: dict[str, Any]
    pilot: dict[str, Any]
    names: Names
    contrasts: list[dict[str, str]]
    pilot_v2: dict[str, Any]


def load(inp: Inputs) -> Loaded:
    summary = read_json(inp.ablation_summary)
    snapshot = need(summary, "harvest_snapshot", inp.ablation_summary)
    if not isinstance(snapshot, Mapping):
        raise RQ3InputError(f"{rel(inp.ablation_summary)}: harvest_snapshot is empty - re-run "
                            "scripts/analyse_ablations.py --corpus beside the harvester's outputs")
    return Loaded(
        pooled=read_csv(inp.pooled, POOLED_REQUIRED),
        credible={r["dimension"]: r for r in read_csv(inp.credible, CREDIBLE_REQUIRED)},
        bias=read_csv(inp.bias, BIAS_REQUIRED),
        summary=summary,
        snapshot=dict(snapshot),
        cov_coded_rows=read_csv(inp.coverage_coded_csv, COVERAGE_REQUIRED),
        cov_coded=need(read_json(inp.coverage_coded_json), "coverage_by_layer",
                       inp.coverage_coded_json),
        cov_corpus_rows=read_csv(inp.coverage_corpus_csv, COVERAGE_CORPUS_REQUIRED),
        cov_corpus=need(read_json(inp.coverage_corpus_json), "coverage_by_layer",
                        inp.coverage_corpus_json),
        harvest_live=read_json(inp.harvest_summary),
        outcomes=read_json(inp.outcomes_summary),
        pilot=read_json(inp.pilot_summary),
        names=Names(inp.dimensions),
        contrasts=read_csv(inp.contrasts, CONTRASTS_REQUIRED),
        pilot_v2=read_json(inp.pilot_v2_summary),
    )


def pooled_rows(d: Loaded, inp: Inputs) -> list[dict[str, str]]:
    rows = [r for r in d.pooled if flag(r["pooled"], f"{rel(inp.pooled)} pooled")]
    if not rows:
        raise RQ3InputError(f"{rel(inp.pooled)}: no pooled dimension")
    return sorted(rows, key=lambda r: (-integer(r["n_papers"], "n_papers"),
                                       -integer(r["n_contrasts"], "n_contrasts"), r["dimension"]))


def consistency(d: Loaded, inp: Inputs) -> tuple[list[str], list[str]]:
    """(mixed, stale). `mixed`: inputs that describe different snapshots - always fatal. `stale`: the
    harvester has moved on since the analysis ran - fatal unless `--allow-stale`."""
    mixed: list[str] = []
    s, snap = d.summary, d.snapshot
    src = inp.ablation_summary
    if not snap.get("consistent"):
        mixed.append(f"{rel(src)}: harvest_snapshot is not consistent (the harvester rewrote its "
                     f"outputs while the analysis read them{': ' + snap['error'] if 'error' in snap else ''}"
                     "): re-run scripts/analyse_ablations.py --corpus --sensitivity")
    funnel_contrasts = integer(need(s, "funnel.contrasts", src), "funnel.contrasts")
    pooled_total = sum(integer(r["n_contrasts"], "n_contrasts") for r in d.pooled)
    if pooled_total != funnel_contrasts:
        mixed.append(f"{rel(inp.pooled)} sums to {pooled_total} contrasts but {rel(src)} reports "
                     f"{funnel_contrasts}")
    pooled_dims = {r["dimension"] for r in d.pooled if flag(r["pooled"], "pooled")}
    if pooled_dims != set(d.credible):
        mixed.append(f"pooled dimensions {sorted(pooled_dims)} differ from the credible table's "
                     f"{sorted(d.credible)}")
    bias_dims = {r["dimension"] for r in d.bias}
    if bias_dims != pooled_dims:
        mixed.append(f"{rel(inp.bias)} diagnoses {sorted(bias_dims)}, not the pooled dimensions")
    in_file = integer(need(s, "provenance.corpus_rows_in_file", src), "corpus_rows_in_file")
    if integer(need(snap, "contrast_rows_read", src), "contrast_rows_read") != in_file:
        mixed.append(f"{rel(src)}: harvest_snapshot does not describe the contrast file pooled")
    cov_total = integer(need(d.cov_corpus, "total_contrasts", inp.coverage_corpus_json),
                        "total_contrasts")
    if cov_total != funnel_contrasts:
        mixed.append(f"{rel(inp.coverage_corpus_json)} counts {cov_total} contrasts but {rel(src)} "
                     f"reports {funnel_contrasts}: re-run "
                     "scripts/analyse_ablation_coverage.py --corpus")
    prov_summary = need(s, "provenance.contrasts", src)
    prov_cov = need(d.cov_corpus, "contrasts_by_provenance", inp.coverage_corpus_json)
    if {k: int(v) for k, v in prov_summary.items()} != {k: int(v) for k, v in prov_cov.items()}:
        mixed.append(f"provenance counts differ: {prov_summary} vs {prov_cov}")
    if len(d.contrasts) != funnel_contrasts:
        mixed.append(f"{rel(inp.contrasts)} holds {len(d.contrasts)} contrasts but {rel(src)} "
                     f"reports {funnel_contrasts}")
    coded_layers = {r["layer"]: integer(r["contrasts"], "contrasts") for r in d.cov_coded_rows}
    corpus_coded = {r["layer"]: integer(r["contrasts_coded_harvest"], "contrasts_coded_harvest")
                    for r in d.cov_corpus_rows}
    if coded_layers != corpus_coded:
        mixed.append(f"coded-set contrasts by layer differ between {rel(inp.coverage_coded_csv)} "
                     f"{coded_layers} and {rel(inp.coverage_corpus_csv)} {corpus_coded}")

    stale: list[str] = []
    live = d.harvest_live
    for key in ("updated_at", "contrasts_after_guards", "papers_extracted"):
        snap_key = "harvest_updated_at" if key == "updated_at" else key
        if need(live, key, inp.harvest_summary) != need(snap, snap_key, src):
            stale.append(f"the harvester has moved on since the analysis ran: {key} is "
                         f"{live[key]!r} in {rel(inp.harvest_summary)} but {snap[snap_key]!r} in "
                         f"the snapshot pooled ({rel(src)}): re-run "
                         "scripts/analyse_ablations.py --corpus --sensitivity and "
                         "scripts/analyse_ablation_coverage.py --corpus")
    return mixed, stale


# ------------------------------------------------------------------------------------------------
# fragments
# ------------------------------------------------------------------------------------------------
def header(sources: Iterable[Path], stamp: str, what: str) -> list[str]:
    lines = [f"% {what}",
             "% GENERATED by scripts/make_rq3_tables.py - do not edit; re-run the script instead.",
             "% sources (mtime, UTC):"]
    lines += [f"%   {rel(p)}  ({mtime(p)})" for p in sources]
    lines.append(f"% generated: {stamp}")
    return lines


def harvest_facts(d: Loaded, inp: Inputs) -> dict[str, Any]:
    """Papers read, tier coverage and date - from the snapshot the analysis pooled, never live."""
    src = inp.ablation_summary
    coverage = need(d.snapshot, "tier_coverage", src)
    parts, sizes, shares = [], {}, {}
    for tier, label in TIER_ORDER:
        if tier not in coverage:
            raise RQ3InputError(f"{rel(src)}: harvest_snapshot.tier_coverage has no tier {tier}")
        size = integer(need(coverage, (tier, "papers"), src), f"tier {tier} papers")
        share = num(need(coverage, (tier, "share_extracted"), src), f"tier {tier} share")
        if size <= 0:
            raise RQ3InputError(f"{rel(src)}: tier {tier} has no papers")
        sizes[tier], shares[tier] = size, share
        if share == 0:
            parts.append(f"none of the {label}")
        elif share == 1:
            parts.append(f"all of the {label}")
        else:
            parts.append(f"{pct(share)} of the {label}")
    return {
        "tier_phrase": " and ".join(parts),
        "tier_sizes": sizes,
        "tier_shares": shares,
        "papers_extracted": integer(need(d.snapshot, "papers_extracted", src), "papers_extracted"),
        "date": prose_date(need(d.snapshot, "harvest_updated_at", src),
                           f"{rel(src)} harvest_snapshot.harvest_updated_at"),
    }


def build_pooled(d: Loaded, inp: Inputs, stamp: str, threshold: float) -> str:
    rows = pooled_rows(d, inp)
    n_all = len(d.pooled)
    min_papers = integer(need(d.summary, "settings.min_papers", inp.ablation_summary), "min_papers")
    date = harvest_facts(d, inp)["date"]
    body = []
    for r in rows:
        dim = r["dimension"]
        c = d.credible[dim]
        w = f"{rel(inp.pooled)} {dim}"
        pi_lo, pi_hi = num(r["pi_low"], f"{w} pi_low"), num(r["pi_high"], f"{w} pi_high")
        pi_cell = interval(pi_lo, pi_hi, sep=",")
        if pi_lo > 0 or pi_hi < 0:
            pi_cell = rf"\textbf{{{pi_cell}}}"
        surv_z = "yes" if flag(c["survives_discount"], f"{dim} survives_discount") else "no"
        surv_hk = "yes" if flag(c["survives_discount_hk"], f"{dim} survives_discount_hk") else "no"
        cells = [
            RAGGED + d.names.table(dim),
            (f"{integer(r['n_papers'], w)} ({integer(r['n_papers_coded'], w)}"
             f"+{integer(r['n_papers_corpus'], w)})"),
            count(integer(r["n_contrasts"], w)),
            eff(num(r["mu_rel"], f"{w} mu_rel")),
            interval(num(r["ci_low"], f"{w} ci_low"), num(r["ci_high"], f"{w} ci_high"), sep=","),
            interval(num(r["hk_ci_low"], f"{w} hk_ci_low"), num(r["hk_ci_high"], f"{w} hk_ci_high"),
                     sep=","),
            pi_cell,
            f"{num(r['i2'], f'{w} i2'):.1f}",
            eff(num(c["mu_discounted"], f"{rel(inp.credible)} {dim} mu_discounted")),
            f"{surv_z}/{surv_hk}",
        ]
        body.append(" & ".join(cells) + r" \tabularnewline")
    caption = (
        r"Within-study meta-analysis of published ablations, coded-set and corpus-wide harvests "
        rf"combined (completed harvest, snapshot of {date}). One row per design "
        rf"dimension with contrasts from at least {min_papers} papers ({len(rows)} dimensions; "
        rf"{n_all - len(rows)} more have contrasts from fewer papers and are not pooled). Effect: "
        r"relative change $(\mathrm{with}-\mathrm{without})/\mathrm{with}$ on the paper's own "
        r"metric, $+$ = the component helped. $\hat\mu$: DerSimonian--Laird random-effects mean over "
        r"paper-level effects; 95\% CI by the normal ($z$) and Hartung--Knapp (HK) methods; 95\% PI: "
        r"prediction interval for a new host system, \textbf{bold} where it excludes zero. "
        r"Discounted $\hat\mu$ applies the dimension's own publication-bias discount. "
        rf"\emph{{Surv.}}: the discounted lower CI bound still exceeds {threshold:g} and "
        r"trim-and-fill keeps the sign, judged on the $z$ / HK bound. Papers: total (coded-set + "
        r"corpus-wide). Every estimate is an \emph{upper} bound on the component's contribution: "
        r"authors report the ablations that favour their component."
    )
    lines = header([inp.pooled, inp.credible, inp.ablation_summary, inp.dimensions], stamp,
                   "RQ3 pooled ablations")
    lines += [
        r"\begin{table}",
        r"\centering",
        rf"\caption{{{caption}}}",
        r"\label{tab:ablations}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\begin{tabular}{@{}p{0.2\linewidth}rrrcccrrc@{}}",
        r"\toprule",
        r" & & & \multicolumn{7}{c}{relative change, $+$ = component helped} \\",
        r"\cmidrule(l){4-10}",
        (r"Dimension & Papers & Contr. & $\hat\mu$ & 95\% CI ($z$) & 95\% CI (HK) & 95\% PI "
         r"& $I^2$ (\%) & Disc.\ $\hat\mu$ & Surv.\ $z$/HK \\"),
        r"\midrule",
        "% BEGIN ROWS",
        *body,
        "% END ROWS",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


def build_coverage(d: Loaded, inp: Inputs, stamp: str) -> str:
    coded = {r["layer"]: r for r in d.cov_coded_rows}
    body = []
    for r in d.cov_corpus_rows:
        layer = r["layer"]
        if layer not in coded:
            raise RQ3InputError(f"{rel(inp.coverage_coded_csv)}: no row for layer {layer!r}")
        w = f"{rel(inp.coverage_corpus_csv)} layer {layer}"
        mark = "" if flag(r["in_correlation"], f"{w} in_correlation") else r"$^\dagger$"
        cells = [
            f"{layer} {d.names.layer_name(layer)}{mark}",
            pct_value(num(r["not_reported_pct"], f"{w} not_reported_pct")),
            str(integer(r["dimensions"], w)),
            str(integer(r["dimensions_ablated"], w)),
            count(integer(coded[layer]["contrasts"], f"{rel(inp.coverage_coded_csv)} {layer}")),
            count(integer(r["contrasts"], w)),
            f"{num(r['contrasts_per_dimension'], w):.1f}",
        ]
        body.append(" & ".join(cells) + r" \\")
    cc, cd = d.cov_corpus, d.cov_coded
    src, src_c = inp.coverage_corpus_json, inp.coverage_coded_json
    rho = num(need(cc, "spearman_rho", src), "spearman_rho")
    p = num(need(cc, "exact_permutation_p_one_sided", src), "p")
    perms = integer(need(cc, "permutations", src), "permutations")
    rho_c = num(need(cd, "spearman_rho", src_c), "coded spearman_rho")
    p_c = num(need(cd, "exact_permutation_p_one_sided", src_c), "coded p")
    layers = need(cc, "layers_in_correlation", src)
    excluded = need(cc, "excluded_layers", src)
    zero = need(cc, "dimensions_without_contrast", src)
    n_abl = integer(need(cc, "n_ablatable_dimensions", src), "n_ablatable")
    footer = [
        (rf"\multicolumn{{7}}{{@{{}}l}}{{Spearman $\rho$, silence vs.\ corpus-wide density "
         rf"(layers {layers[0]}--{layers[-1]}): $\rho = {rho:+.3f}$, exact one-sided "
         rf"$p = {pval(p)}$}} \\"),
        (rf"\multicolumn{{7}}{{@{{}}l}}{{({count(perms)} permutations); coded-set density "
         rf"only: $\rho = {rho_c:+.3f}$, $p = {pval(p_c)}$}} \\"),
    ]
    caption = (
        r"Ablation coverage by layer against layer silence (weighted share of systems whose "
        r"dimension is \emph{not reported}). \emph{Coded-set}: contrasts harvested from the coded "
        r"systems' outcome extraction; \emph{corpus-wide}: coded-set plus the full-text harvest, "
        r"de-duplicated. Dimension and density columns are corpus-wide. "
        rf"$^\dagger$Layer {join_prose(list(excluded))} (metadata) cannot be ablated and is excluded "
        rf"from $\rho$. Still without a single published ablation: {len(zero)} of {n_abl} "
        rf"ablatable dimensions ({join_prose([d.names.prose(k) for k in zero])}). Absence of "
        r"evidence about the literature, not evidence that those components do not matter."
    )
    lines = header([inp.coverage_coded_csv, inp.coverage_coded_json, inp.coverage_corpus_csv,
                    inp.coverage_corpus_json, inp.dimensions], stamp, "RQ3 ablation coverage")
    lines += [
        r"\begin{table}",
        r"\centering",
        rf"\caption{{{caption}}}",
        r"\label{tab:coverage}",
        r"\footnotesize",
        r"\begin{tabular}{@{}lrrrrrr@{}}",
        r"\toprule",
        r" & Weighted & & Dims $\geq$1 & Contrasts & Contrasts & Contrasts \\",
        r"Layer & silence & Dims & contrast & (coded-set) & (corpus-wide) & per dim \\",
        r"\midrule",
        "% BEGIN ROWS",
        *body,
        "% END ROWS",
        r"\midrule",
        *footer,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


def _outcome_contrast(d: Loaded, inp: Inputs, dimension: str) -> dict[str, Any]:
    src = inp.outcomes_summary
    hits = [c for c in need(d.outcomes, "contrasts", src) if c.get("dimension") == dimension]
    if len(hits) != 1:
        raise RQ3InputError(f"{rel(src)}: expected one contrast on {dimension!r}, "
                            f"found {len(hits)}")
    return hits[0]


def cross_paper_row(d: Loaded, inp: Inputs, dimension: str, role: str) -> dict[str, str]:
    """One line of the cross-paper design. `role` is "headline" or "focal"; the focal line is
    labelled with its key count and, when `analyse_outcomes.py` marks it so, as fragile."""
    src = inp.outcomes_summary
    c = _outcome_contrast(d, inp, dimension)
    n_keys = integer(need(c, "n_keys", src), "n_keys")
    n = f"{n_keys} keys, {integer(need(c, 'n_systems', src), 'n_systems')} systems"
    if role == "headline":
        keys_all = integer(need(d.outcomes, "comparable_set.keys", src), "comparable keys")
        sys_all = integer(need(d.outcomes, "comparable_set.systems", src), "comparable systems")
        n += f" (of {keys_all} keys, {sys_all} systems)"
    fragile = bool(need(c, "fragile", src))
    label = d.names.prose(dimension)
    if role != "headline":
        label += (f", {tex(CONTRAST_LABELS.get(str(need(c, 'name', src)), 'focal contrast'))}"
                  + (f"; fragile ({n_keys} keys)" if fragile else ""))
    if not need(c, "estimable", src):
        reason = tex(str(need(c, "not_estimable_reason", src)))
        return {"n": n, "estimate": f"{label}: not estimable", "interval": "---",
                "status": f"not estimable: {reason}"}
    effect = num(need(c, "effect", src), f"cross-paper effect {dimension}")
    lo = num(need(c, "ci_low", src), f"cross-paper ci_low {dimension}")
    hi = num(need(c, "ci_high", src), f"cross-paper ci_high {dimension}")
    perm_p = num(need(c, "permutation.p_two_sided", src), f"permutation p {dimension}")
    status = (("detected" if need(c, "detected", src) else "not detected")
              + f"; exact permutation $p = {pval(perm_p)}$" + ("; fragile" if fragile else ""))
    baseline = c.get("baseline_asymmetry", {}).get("reference_all_recurring_keys", 0)
    bound = ({"bound": (f"lower for scaffold drift; in {int(baseline)} of its {n_keys} keys "
                        "baseline selection can inflate it")} if baseline else {})
    return bound | {"n": n, "estimate": f"{label}: $d = {effect:+.3f}$ within-key SD",
            "interval": interval(lo, hi) + " (bootstrap over keys)",
            "status": "complete; " + status}


def check_headline(d: Loaded, inp: Inputs, headline: str) -> None:
    """The headline cross-paper contrast must still be what the prose calls it: detected by both
    the key-bootstrap interval and the permutation test, and not fragile. A rerun that changes that
    must stop the build rather than leave the table quoting a headline the data no longer carry."""
    src = inp.outcomes_summary
    c = _outcome_contrast(d, inp, headline)
    if not (need(c, "estimable", src) and need(c, "detected", src)
            and not need(c, "fragile", src)):
        raise RQ3InputError(f"{rel(src)}: the cross-paper headline {headline!r} is no longer "
                            "detected and robust (estimable, detected, not fragile); choose the "
                            "headline again (--cross-paper-headline) and revise the prose")


def within_study_row(d: Loaded, inp: Inputs, focal: str, facts: dict[str, Any]) -> dict[str, str]:
    row = next((r for r in d.pooled if r["dimension"] == focal), None)
    if row is None or not flag(row["pooled"], "pooled") or focal not in d.credible:
        raise RQ3InputError(f"{rel(inp.pooled)}: focal dimension {focal!r} is not pooled")
    c = d.credible[focal]
    w = f"{rel(inp.pooled)} {focal}"
    total_p = integer(need(d.summary, "funnel.papers", inp.ablation_summary), "funnel.papers")
    total_c = integer(need(d.summary, "funnel.contrasts", inp.ablation_summary), "funnel.contrasts")
    sz = flag(c["survives_discount"], "survives_discount")
    shk = flag(c["survives_discount_hk"], "survives_discount_hk")
    verdict = {(True, True): "survives the bias discount ($z$ and HK)",
               (True, False): "survives the bias discount on $z$ only",
               (False, True): "survives the bias discount on HK only",
               (False, False): "does not survive the bias discount"}[(sz, shk)]
    return {
        "n": (f"{integer(row['n_papers'], w)} papers, {count(integer(row['n_contrasts'], w))} "
              f"contrasts (all dimensions: {count(total_p)} papers, {count(total_c)} contrasts)"),
        "estimate": f"{d.names.prose(focal)}: $\\hat\\mu = {num(row['mu_rel'], w):+.3f}$ "
                    "(relative change)",
        "interval": (f"$z$ {interval(num(row['ci_low'], w), num(row['ci_high'], w))}; "
                     f"HK {interval(num(row['hk_ci_low'], w), num(row['hk_ci_high'], w))}"),
        "status": f"complete (harvest read {facts['tier_phrase']}); {verdict}",
    }


def clean_supply(inp: Inputs, suite_name: str) -> tuple[int, int]:
    """(confirmatory instances, of which never piloted) for one prepared tier-3 suite.

    Amendment 12a's rule, through `tier3_ablation`'s own functions: a confirmatory instance counts
    only if its TASK has not appeared in any pilot or diagnostic row, under any presentation.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import tier3_ablation as t3

    path = inp.tier3_dir / "suites" / f"{suite_name}.json"
    suite = read_json(path)
    name = str(need(suite, "name", path))
    ids = [str(i["id"]) for i in need(suite, "instances", path)]
    conf = [i for i in ids if t3.pool_of(name, i) == "confirmatory"]
    piloted = t3.piloted_tasks([inp.tier3_dir / "pilot", inp.tier3_dir / "diagnostic",
                                inp.tier3_dir / "pilot_v2"])
    return len(conf), sum(t3.task_key(i) not in piloted for i in conf)


def registered_row(d: Loaded, inp: Inputs) -> dict[str, str]:
    """The registered compute-matched ablation: pilot grid, revision pilot, and the supply verdict.

    Everything printed is read: the number of pilot cells and the instances the analysis plan needs
    at the planning correlation from the pilot summary, the revision pilot's runs from its own
    summary, and the clean confirmatory supply from the suites and every pilot row on disk. The
    status is a verdict the numbers must support; if they stop supporting it, the build refuses.
    """
    confirmatory = inp.tier3_dir / "runs.jsonl"
    if confirmatory.exists():
        raise RQ3InputError(
            f"{rel(confirmatory)} exists: the confirmatory tier-3 run has started, and this script "
            "only knows how to report the pilot. Extend make_rq3_tables.py to read the confirmatory "
            "summary rather than let the table claim no estimate exists.")
    registered = (inp.tier3_dir / "REGISTERED.txt").exists()
    p, src = d.pilot, inp.pilot_summary
    cells = need(p, "suites", src)
    suite = need(p, ("suites", str(need(p, "selected", src))), src)
    need_n = integer(need(suite, ("power", f"rho={PLANNING_RHO}", "n_instances_80pct"), src),
                     "pilot power")
    v2 = need(d.pilot_v2, "cells", inp.pilot_v2_summary)
    runs = {k.rsplit(":", 1)[1]: 0 for k in v2}
    for k, c in v2.items():
        runs[k.rsplit(":", 1)[1]] += integer(need(c, "n_rows", inp.pilot_v2_summary), "n_rows")
    if len(set(runs.values())) != 1:
        raise RQ3InputError(f"{rel(inp.pilot_v2_summary)}: the B variants ran on different "
                            f"numbers of runs {runs}")
    n_v2 = next(iter(runs.values()))
    _, clean = clean_supply(inp, str(need(suite, "suite", src)))
    if clean >= need_n:
        raise RQ3InputError(f"the selected suite now supplies {clean} clean confirmatory instances "
                            f"against the {need_n} required: the registered row's verdict ('not "
                            "runnable') no longer holds; revise it and the prose")
    status = "registered" if registered else "filed, amendment pending"
    return {
        "n": (f"pilot: {len(cells)} suite--model cells, arm A; revision: {n_v2} runs, arms A and "
              f"B; {need_n} instances needed at $\\rho = {PLANNING_RHO}$, {clean} available"),
        "estimate": "not yet estimated",
        "interval": "---",
        "status": f"{status}; pilot failed its band; not runnable on available suites",
    }


def build_designs(d: Loaded, inp: Inputs, stamp: str, focal: str,
                  headline: str = CROSS_PAPER_HEADLINE) -> str:
    facts = harvest_facts(d, inp)
    check_headline(d, inp, headline)
    lower = "lower (attenuated towards zero by scaffold drift)"
    cross = [cross_paper_row(d, inp, headline, "headline")]
    if focal != headline:
        cross.append(cross_paper_row(d, inp, focal, "focal"))
    # (design, identifies, line, bound); a design with two lines prints its name once and its
    # second line as a continuation row with the first two cells empty.
    designs = [
        ("Cross-paper association",
         ("association between a coded design choice and standardised score across systems "
          "sharing benchmark, split and base model"),
         cross, lower),
        ("Within-study meta-analysis",
         "the component's contribution inside the host systems whose authors ablated it",
         [within_study_row(d, inp, focal, facts)], "upper (selective reporting)"),
        ("Registered compute-matched ablation",
         "causal effect of the component at a matched model-call budget, on one suite and model",
         [registered_row(d, inp)], "unbiased (for that suite and model)"),
    ]
    body = []
    for name, identifies, lines_, bound in designs:
        for i, r in enumerate(lines_):
            first = i == 0
            cells = [name if first else "", identifies if first else "", r["n"], r["estimate"],
                     r["interval"], r.get("bound", bound), r["status"]]
            # ragged p-cells: `\raggedright` redefines `\\`, so the row ends with `\tabularnewline`
            body.append(" & ".join(RAGGED + c for c in cells) + r" \tabularnewline")
    caption = (
        r"Three designs for RQ3 and the direction of their bounds. The within-study and registered "
        rf"designs are shown for {d.names.prose(focal)}, the one component all three measure; the "
        rf"cross-paper design shows its headline contrast ({d.names.prose(headline)}, the one that "
        r"survives both the key bootstrap and the permutation test) and, beneath it, the focal "
        r"dimension's own cross-paper value. The cross-paper estimate is a standardised within-key "
        r"difference ($d$, in within-key SDs); the within-study estimate is a relative change. They "
        r"are not on one scale; what they share is the direction in which each can be wrong."
    )
    lines = header([inp.outcomes_summary, inp.pooled, inp.credible, inp.ablation_summary,
                    inp.pilot_summary, inp.pilot_v2_summary, inp.dimensions], stamp,
                   "RQ3 designs and their bounds")
    lines += [
        r"\begin{table}",
        r"\centering",
        rf"\caption{{{caption}}}",
        r"\label{tab:rq3-bounds}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        (r"\begin{tabular}{@{}p{0.10\linewidth}p{0.16\linewidth}p{0.15\linewidth}"
         r"p{0.12\linewidth}p{0.12\linewidth}p{0.09\linewidth}p{0.14\linewidth}@{}}"),
        r"\toprule",
        r"Design & Identifies & $n$ & Headline estimate & Interval (95\%) & Bound & Status \\",
        r"\midrule",
        "% BEGIN ROWS",
        *body,
        "% END ROWS",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------------------------
# the sign distribution's warrant: what the sign share rests on (descriptive counts of one file)
# ------------------------------------------------------------------------------------------------
def sign_warrant(d: Loaded, inp: Inputs) -> dict[str, Any]:
    """Counts behind `\\rqSignSharePct`, from the contrast file that was pooled.

    The denominator is the one `analyse_ablations` uses for `overall_sign_share`: every contrast on
    a POOLED dimension. Within it: how many contrasts take their metric's direction by assumption
    (`higher_assumed`) rather than from the metric's name, how many favour the component under each,
    and how many carry an assumed rather than a binomially reconstructed variance. The recomputed
    share must equal the summary's, or the file is not the one that was pooled.
    """
    pooled_dims = {r["dimension"] for r in pooled_rows(d, inp)}
    rows = [r for r in d.contrasts if r["dimension"] in pooled_dims]
    fav = [num(r["rel_effect"], f"{rel(inp.contrasts)} rel_effect") > 0 for r in rows]
    share = sum(fav) / len(rows)
    published = num(need(d.summary, "bias_verdict.overall_sign_share", inp.ablation_summary),
                    "overall_sign_share")
    if abs(share - published) > 1e-9:
        raise RQ3InputError(f"{rel(inp.contrasts)} gives a sign share of {share:.6f} on the pooled "
                            f"dimensions but {rel(inp.ablation_summary)} reports {published:.6f}")
    assumed = [r["polarity"] == POLARITY_ASSUMED for r in rows]
    n_assumed = sum(assumed)
    fav_assumed = sum(f for f, a in zip(fav, assumed, strict=True) if a)
    n_stated = len(rows) - n_assumed
    if not n_stated or not n_assumed:
        raise RQ3InputError(f"{rel(inp.contrasts)}: expected contrasts with both a stated and an "
                            "assumed metric direction")
    return {"n": len(rows), "favour": sum(fav), "n_stated": n_stated,
            "fav_stated": sum(fav) - fav_assumed, "n_assumed": n_assumed,
            "fav_assumed": fav_assumed,
            "var_assumed": sum(r["var_method"] == VAR_ASSUMED for r in rows)}


def sign_warrant_macros(d: Loaded, inp: Inputs) -> list[tuple[str, str, str]]:
    w = sign_warrant(d, inp)
    return [
        ("rqSignDenom", count(w["n"]),
         "contrasts on the pooled dimensions: the denominator of rqSignSharePct"),
        ("rqPolarityStatedN", count(w["n_stated"]),
         "of those, contrasts whose metric names its direction (higher / lower is better)"),
        ("rqPolarityStatedFavour", count(w["fav_stated"]), "of those, favouring the component"),
        ("rqPolarityStatedFavourPct", pct_number(w["fav_stated"] / w["n_stated"]),
         "bare number: their share favouring the component, %"),
        ("rqPolarityAssumedN", count(w["n_assumed"]),
         "contrasts whose metric names no direction: higher-is-better assumed"),
        ("rqPolarityAssumedFavour", count(w["fav_assumed"]), "of those, favouring the component"),
        ("rqPolarityAssumedFavourPct", pct_number(w["fav_assumed"] / w["n_assumed"]),
         "bare number: their share favouring the component, %"),
        ("rqVarAssumedN", count(w["var_assumed"]),
         "contrasts whose variance is a flat assumed relative SE, not a binomial reconstruction"),
    ]


# ------------------------------------------------------------------------------------------------
# sensitivity 1: the layer correlation before the seven classification rules
# ------------------------------------------------------------------------------------------------
def snapshot_harvest_rows(d: Loaded, inp: Inputs) -> list[dict[str, str]]:
    """The harvester's rows for exactly the papers the pooled snapshot had extracted.

    The harvester keeps running after an analysis, so its row file can hold papers the pooled
    snapshot never saw. The snapshot records how many papers each prefilter tier had extracted; the
    rows kept are those of the tiers it had started, and both the paper count and the number of rows
    that passed every guard must equal the snapshot's, or the reconstruction refuses.
    """
    src = inp.ablation_summary
    status = need(d.snapshot, "tier_status", src)
    tiers = {t for t, st in status.items() if int((st or {}).get("extracted", 0)) > 0}
    expected = sum(int(status[t]["extracted"]) for t in tiers)
    outcomes = read_csv(inp.harvest_outcomes, ["record_id", "tier", "status"])
    papers = {r["record_id"] for r in outcomes if r["tier"] in tiers and r["status"] == "extracted"}
    if len(papers) != expected:
        raise RQ3InputError(f"{rel(inp.harvest_outcomes)} has {len(papers)} extracted papers in "
                            f"tiers {sorted(tiers)} but the pooled snapshot had {expected}: the "
                            "harvester has moved on inside a tier the snapshot had started; re-run "
                            "scripts/analyse_ablations.py --corpus --sensitivity")
    csv.field_size_limit(10 ** 8)
    rows = [r for r in read_csv(inp.harvest_rows, HARVEST_ROWS_REQUIRED)
            if r["record_id"] in papers]
    kept = sum(r["drop_reason"] == "" for r in rows)
    want = integer(need(d.snapshot, "contrasts_after_guards", src), "contrasts_after_guards")
    if kept != want:
        raise RQ3InputError(f"{rel(inp.harvest_rows)} keeps {kept} rows of the snapshot's papers "
                            f"but the snapshot pooled {want}")
    return rows


def without_rules(row: Mapping[str, str], design_keys: set[str]) -> tuple[str, dict[str, Any]]:
    """`harvest_ablations_corpus.guard_row` on one extracted row with the seven classification
    rules switched off and nothing else changed. The window checks are satisfied by construction:
    only rows that already passed them (reached the classification stage) are re-run."""
    from unittest import mock

    sys.path.insert(0, str(ROOT / "scripts"))
    import harvest_ablations_corpus as hv

    fields = {k: row.get(k, "") for k in hv.ROW_FIELDS}
    with mock.patch.multiple(
            hv,
            classification_matches=lambda r: [],
            apply_remap=lambda r, dim: ("", "", dim, ""),
            direction_contradicts_label=lambda r, **kw: "",
            scores_in_window=lambda *a, **kw: True,
            scores_colocated=lambda *a, **kw: True,
            score_match=lambda *a, **kw: "exact"):
        return hv.guard_row(fields, "", design_keys)


def _dup_key(r: Mapping[str, str]) -> tuple[str, ...]:
    """The harvester's within-paper duplicate key (`build_outputs`), on the row as extracted."""
    return tuple(str(r.get(c) or "").strip().lower()
                 for c in ("record_id", "benchmark", "split", "metric", "full_score",
                           "ablated_score", "ablated_arm"))


def pre_rule_sensitivity(d: Loaded, inp: Inputs) -> dict[str, Any]:
    """Spearman's rho, layer silence vs ablation density, with the seven rules undone.

    Every harvest row a rule decided or matched is re-run without the rules: a row the rules
    reassigned goes back to the dimension the extraction stage gave it, and a row the rules dropped
    is counted if it would have passed every other guard. The rule-applied counts are the pooled
    contrast file itself, on which `coverage_by_layer` must first reproduce the published rho.
    Rows of papers the coded-set harvest also read are left out of the adjustment either way,
    because the harvester may have flagged them as already counted.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import analyse_ablation_coverage as cov
    import analyse_ablations as aa

    key_to_layer = cov.load_layers(inp.dimensions)
    silence = {r["layer"]: num(r["not_reported_pct"], f"{rel(inp.coverage_corpus_csv)} silence")
               for r in d.cov_corpus_rows}
    post = Counter(r["dimension"] for r in d.contrasts)
    _, post_stats = cov.coverage_by_layer(key_to_layer, post, silence)
    published = num(need(d.cov_corpus, "spearman_rho", inp.coverage_corpus_json), "spearman_rho")
    if abs(post_stats["spearman_rho"] - published) > 1e-9:
        raise RQ3InputError(f"coverage_by_layer gives rho {post_stats['spearman_rho']} on "
                            f"{rel(inp.contrasts)} but {rel(inp.coverage_corpus_json)} reports "
                            f"{published}")
    design_keys = aa.design_dimension_keys(aa.load_dimensions(inp.dimensions))
    coded_papers = {r["record_id"] for r in d.contrasts if r["provenance"] == PROVENANCE_CODED}
    pooled_dims = {r["dimension"] for r in pooled_rows(d, inp)}
    rows = snapshot_harvest_rows(d, inp)
    kept_keys = {_dup_key(r) for r in rows if r["drop_reason"] == ""}
    pre = Counter(post)
    moved_out_of_g: Counter = Counter()
    g_fate: Counter = Counter()
    dcl = {"dropped": 0, "pooled": 0, "against": 0}
    for r in rows:
        if (r["drop_reason"] in PRE_CLASSIFICATION
                or not (r["guard_applied"] or r["guards_matched"])
                or r["record_id"] in coded_papers):
            continue
        rule = r["guard_applied"].split(";")[0]
        reason, cf = without_rules(r, design_keys)
        cf_dim = (cf.get("norm_dimension") or "") if reason == "" else ""
        if r["drop_reason"] == "":
            if not cf_dim or cf_dim == r["norm_dimension"]:
                continue
            pre[r["norm_dimension"]] -= 1        # a reassignment, undone
            pre[cf_dim] += 1
        elif cf_dim and _dup_key(r) not in kept_keys:
            pre[cf_dim] += 1                     # a drop, undone
        else:
            continue
        if key_to_layer.get(cf_dim) == SANDBOX_LAYER:
            moved_out_of_g[rule] += 1
            # what became of the row: kept under another dimension, or dropped and why
            g_fate[("reassigned", r["norm_dimension"]) if r["drop_reason"] == ""
                   else ("dropped", r["drop_reason"])] += 1
        if rule == "direction_contradicts_label":
            dcl["dropped"] += 1
            if cf_dim in pooled_dims:
                dcl["pooled"] += 1
                dcl["against"] += int(num(cf.get("rel_effect"), "rel_effect") <= 0)
    _, pre_stats = cov.coverage_by_layer(key_to_layer, pre, silence)
    return {"rho": float(pre_stats["spearman_rho"]),
            "p": float(pre_stats["exact_permutation_p_one_sided"]),
            "zero_layers": pre_stats["zero_contrast_layers"],
            "g_contrasts": sum(n for k, n in pre.items() if key_to_layer.get(k) == SANDBOX_LAYER),
            "moved_out_of_g": dict(moved_out_of_g), "g_fate": dict(g_fate), "dcl": dcl}


# ------------------------------------------------------------------------------------------------
# sensitivity 2: the cross-paper headline without the keys that compare against baselines only
# ------------------------------------------------------------------------------------------------
def non_baseline_sensitivity(d: Loaded, inp: Inputs, headline: str) -> dict[str, Any]:
    """The headline contrast re-estimated on its keys minus those whose reference side is only
    recurring baseline harnesses, with `analyse_outcomes`' own panel, bootstrap and permutation
    and the draws and seed the published summary records. The full-key estimate is reproduced
    first; a difference means the summary was not made from these inputs, and the build refuses."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import analyse_outcomes as ao
    import numpy as np

    src = inp.outcomes_summary
    c = _outcome_contrast(d, inp, headline)
    n_boot = integer(need(d.outcomes, "bootstrap.draws", src), "bootstrap draws")
    seed = integer(need(d.outcomes, "bootstrap.seed", src), "bootstrap seed")
    contrast = next((x for x in ao.CONTRASTS if x.dimension == headline), None)
    if contrast is None:
        raise RQ3InputError(f"analyse_outcomes defines no contrast on {headline!r}")
    panel = ao.build_comparable_set(ao.load_results(inp.results), min_systems=2,
                                    agg=str(need(d.outcomes, "standardisation.row_aggregation",
                                                 src)))
    panel = ao.standardise_within_key(panel, rank_threshold=integer(
        need(d.outcomes, "standardisation.rank_threshold", src), "rank_threshold"))
    codings = ao.load_codings(inp.systems)
    full = ao.estimate_contrast(panel, contrast, codings, n_boot=n_boot, seed=seed)
    for key in ("effect", "ci_low", "ci_high"):
        if abs(full[key] - num(need(c, key, src), key)) > 1e-9:
            raise RQ3InputError(f"re-estimating {headline!r} gives {key} {full[key]:.6f} but "
                                f"{rel(src)} reports {c[key]}: re-run scripts/analyse_outcomes.py")
    frame = ao.contrast_exposure(panel, contrast, codings)
    recurring = ao.recurring_comparators(panel)
    baseline_keys = set()
    for key, sub in frame.groupby("comparable_key", sort=True):
        exposed = set(sub.loc[sub["x"] == 1.0, "system_id"])
        reference = set(sub.loc[sub["x"] == 0.0, "system_id"])
        if exposed and reference and reference <= recurring and not (exposed & recurring):
            baseline_keys.add(key)
    published = integer(need(c, "baseline_asymmetry.reference_all_recurring_keys", src),
                        "reference_all_recurring_keys")
    if len(baseline_keys) != published:
        raise RQ3InputError(f"{len(baseline_keys)} baseline-only keys found; {rel(src)} "
                            f"reports {published}")
    rest = frame[~frame["comparable_key"].isin(baseline_keys)]
    diffs = ao.key_differences(rest)["d"].to_numpy(dtype=float)
    reps = ao.bootstrap_key_means(diffs, n_boot=n_boot, seed=seed)
    perm = ao.permutation_test_within_key(rest, n_perm=n_boot, seed=seed)
    return {"n_keys": len(diffs), "n_baseline_keys": len(baseline_keys),
            "n_systems": int(rest["system_id"].nunique()), "effect": float(diffs.mean()),
            "ci_low": float(np.percentile(reps, 2.5)), "ci_high": float(np.percentile(reps, 97.5)),
            "p": float(perm["p_two_sided"])}


def two_dp(x: float) -> str:
    """Signed, two decimals, text-safe: the precision the cross-paper prose uses."""
    return rf"\ensuremath{{{x:+.2f}}}"


def sensitivity_macros(d: Loaded, inp: Inputs, headline: str) -> list[tuple[str, str, str]]:
    pr = pre_rule_sensitivity(d, inp)
    nb = non_baseline_sensitivity(d, inp, headline)
    w = sign_warrant(d, inp)
    dcl, fate = pr["dcl"], pr["g_fate"]
    # a G row's fate is what finally happened to it, not which rule fired first: a row a
    # sandbox-remapping rule matched can still be dropped (its text names neither an execution
    # step nor an isolation boundary), so rule names alone would over-count the reassignments
    remapped = sorted(((n, dim) for (kind, dim), n in fate.items() if kind == "reassigned"),
                      key=lambda x: (-x[0], x[1]))
    dropped = {why: n for (kind, why), n in sorted(fate.items()) if kind == "dropped"}
    unnamed = sum(n for why, n in dropped.items() if why in G_MAPPING_RULES)
    parts = [f"{n} to {d.names.prose(dim)}" for n, dim in remapped]
    remap_list = (" and ".join(parts) if len(parts) <= 2
                  else ", ".join(parts[:-1]) + ", and " + parts[-1]) or "none"
    return [
        ("rqPreRuleRho", eff(pr["rho"]),
         "Spearman rho, silence vs density, with the seven classification rules undone"),
        ("rqPreRuleP", pval(pr["p"]), "its exact one-sided permutation p"),
        ("rqPreRuleGContrasts", count(pr["g_contrasts"]),
         "sandbox-layer (G) contrasts before the rules; after them there are none"),
        ("rqPreRuleGRemapped", count(sum(n for n, _ in remapped)),
         "of those, kept and reassigned by a rule to the dimension the removal takes away"),
        ("rqPreRuleGRemapList", remap_list,
         "those reassignments by destination dimension, largest first"),
        ("rqPreRuleGDropped", count(sum(dropped.values())),
         "of those, dropped: " + (", ".join(f"{k} {n}" for k, n in dropped.items()) or "none")),
        ("rqPreRuleGDroppedUnnamed", count(unnamed),
         "of the dropped, by a sandbox-layer mapping rule: the text names no execution step, "
         "isolation boundary or enforced authorisation"),
        ("rqPreRuleGDroppedUnread", count(sum(dropped.values()) - unnamed),
         "of the dropped, by a score-reading guard (delta metric, run-together scores)"),
        ("rqDCLDropped", count(dcl["pooled"]),
         "rows the label-contradicts-orientation rule dropped, on pooled dimensions"),
        ("rqDCLAgainst", count(dcl["against"]),
         "of those, rows that do not favour the component as the extraction stage oriented them"),
        ("rqSignShareWithDCLPct",
         pct_number((w["favour"] + dcl["pooled"] - dcl["against"]) / (w["n"] + dcl["pooled"])),
         "bare number: the sign share had those rows been kept as the extraction oriented them"),
        ("rqXPBaselineKeys", str(nb["n_baseline_keys"]),
         "headline keys whose reference side is only recurring baseline harnesses"),
        ("rqXPOtherKeys", str(nb["n_keys"]), "the headline's remaining keys"),
        ("rqXPOtherEffect", two_dp(nb["effect"]),
         "the headline effect on those keys, within-key sd"),
        ("rqXPOtherCI", rf"\ensuremath{{[{nb['ci_low']:+.2f}, {nb['ci_high']:+.2f}]}}",
         "its 95% bootstrap interval over keys, with brackets"),
        ("rqXPOtherP", pval(nb["p"]), "its two-sided within-key permutation p"),
    ]


def macro_values(d: Loaded, inp: Inputs, focal: str) -> list[tuple[str, str, str]]:
    """(name, value, one-line definition) for every prose macro, in file order."""
    s, cc, src = d.summary, d.cov_corpus, inp.ablation_summary
    facts = harvest_facts(d, inp)
    prov_c = need(s, "provenance.contrasts", src)
    prov_p = need(s, "provenance.papers", src)
    for key in (PROVENANCE_CODED, PROVENANCE_CORPUS):
        if key not in prov_c or key not in prov_p:
            raise RQ3InputError(f"{rel(src)}: provenance has no {key!r}")
    rows = pooled_rows(d, inp)
    pi_excl = [r for r in rows
               if num(r["pi_low"], "pi_low") > 0 or num(r["pi_high"], "pi_high") < 0]
    credible = [d.credible[r["dimension"]] for r in rows]
    surviving = [num(r["mu_rel"], f"{r['dimension']} mu_rel") for r in rows
                 if flag(d.credible[r["dimension"]]["survives_discount"], "survives_discount")]
    if len(surviving) >= 2:
        q1, _, q3 = statistics.quantiles(surviving, n=4, method="inclusive")
        effect_range, effect_iqr = span(min(surviving), max(surviving)), span(q1, q3)
    elif len(surviving) == 1:
        effect_range = effect_iqr = eff(surviving[0])
    else:
        effect_range = effect_iqr = "none"
    sv = next((r for r in rows if r["dimension"] == focal), None)
    if sv is None:
        raise RQ3InputError(f"{rel(inp.pooled)}: focal dimension {focal!r} is not pooled")
    sv_c = d.credible[focal]
    w = f"{rel(inp.pooled)} {focal}"
    verdict = need(s, "bias_verdict", src)
    egger = [r for r in d.bias if math.isfinite(num(r["egger_p"], f"{r['dimension']} egger_p"))
             and float(r["egger_p"]) < EGGER_ALPHA]
    egger_listed = sorted(need(verdict, "egger_flagged_dimensions", src))
    if sorted(r["dimension"] for r in egger) != egger_listed:
        raise RQ3InputError(f"{rel(inp.bias)} Egger flags {sorted(r['dimension'] for r in egger)} "
                            f"but {rel(src)} lists {egger_listed}")
    egger_items = [
        f"{tex(r['dimension'])} "
        f"(\\ensuremath{{{'+' if num(r['egger_intercept'], 'egger_intercept') >= 0 else '-'}}})"
        for r in sorted(egger, key=lambda r: d.names.order(r["dimension"]))
    ]
    sparse = sorted((r for r in d.pooled
                     if d.names.layer_of(r["dimension"]) in SPARSE_LAYERS
                     and integer(r["n_contrasts"], "n_contrasts") > 0),
                    key=lambda r: d.names.order(r["dimension"]))
    zero_dims = need(cc, "dimensions_without_contrast", inp.coverage_corpus_json)
    zero_layers = need(cc, "zero_contrast_layers", inp.coverage_corpus_json)
    ccsrc = inp.coverage_corpus_json
    return [
        ("rqCorpusPapersExtracted", count(facts["papers_extracted"]),
         "papers the corpus-wide harvest has read (snapshot pooled)"),
        ("rqCorpusPapersWithContrast", count(integer(prov_p[PROVENANCE_CORPUS], "corpus papers")),
         "corpus-harvest papers contributing >=1 pooled contrast (after de-duplication)"),
        ("rqCorpusContrasts", count(integer(prov_c[PROVENANCE_CORPUS], "corpus contrasts")),
         "corpus-harvest contrasts pooled (after de-duplication against the coded set)"),
        ("rqCodedContrasts", count(integer(prov_c[PROVENANCE_CODED], "coded contrasts")),
         "coded-set harvest contrasts"),
        ("rqCodedPapers", count(integer(prov_p[PROVENANCE_CODED], "coded papers")),
         "coded-set harvest papers"),
        ("rqTotalContrasts", count(integer(need(s, "funnel.contrasts", src), "funnel.contrasts")),
         "all contrasts pooled, coded-set + corpus"),
        ("rqTotalPapers", count(integer(need(s, "funnel.papers", src), "funnel.papers")),
         "distinct papers behind them"),
        ("rqCorpusDuplicatesDropped",
         count(integer(need(s, "provenance.already_in_coded_harvest", src), "duplicates")),
         "corpus contrasts dropped as already in the coded-set harvest"),
        ("rqPoolableDims", str(len(rows)), "dimensions pooled (>= rqMinPapers papers)"),
        ("rqMinPapers", str(integer(need(s, "settings.min_papers", src), "min_papers")),
         "papers needed to pool a dimension"),
        ("rqSignSharePct", pct_number(num(need(verdict, "overall_sign_share", src), "sign share")),
         ("bare number: % of contrasts favouring the component, coded-set + corpus, over the "
          "pooled (bias-diagnosed) dimensions, contrast-weighted")),
        ("rqPIIncludesZeroCount", str(len(rows) - len(pi_excl)),
         "pooled dimensions whose 95% prediction interval includes zero"),
        ("rqPIExcludesZeroDims", join_prose([d.names.prose(r["dimension"]) for r in pi_excl]),
         "pooled dimensions whose prediction interval excludes zero"),
        ("rqPIExcludesZeroLower",
         ", ".join(f"{tex(r['dimension'])} ({eff(num(r['pi_low'], 'pi_low'))})"
                   for r in pi_excl) or "none",
         "lower prediction-interval bound of each of those dimensions"),
        ("rqDiscountSurviveZ", str(sum(flag(c["survives_discount"], "survives_discount")
                                       for c in credible)),
         "pooled dimensions surviving the bias discount on the z interval"),
        ("rqDiscountSurviveHK", str(sum(flag(c["survives_discount_hk"], "survives_discount_hk")
                                        for c in credible)),
         "... on the Hartung-Knapp interval"),
        ("rqEffectRangeSurviving", effect_range,
         "min to max DL pooled effect over the dimensions surviving on z"),
        ("rqEffectIQRSurviving", effect_iqr,
         "first to third quartile of those effects (inclusive quartiles)"),
        ("rqMedianDiscountPct", pct_number(num(need(verdict, "discount", src), "bias discount")),
         "bare number: median per-dimension publication-bias discount, %"),
        ("rqEggerFlaggedDims", ", ".join(egger_items) or "none",
         f"dimensions with Egger p < {EGGER_ALPHA:g}, intercept sign in parentheses"),
        ("rqSVPapers", str(integer(sv["n_papers"], w)), "focal dimension: papers"),
        ("rqSVContrasts", count(integer(sv["n_contrasts"], w)), "focal dimension: contrasts"),
        ("rqSVPooled", eff(num(sv["mu_rel"], f"{w} mu_rel")), "focal dimension: DL pooled effect"),
        ("rqSVDiscounted", eff(num(sv_c["mu_discounted"], f"{rel(inp.credible)} mu_discounted")),
         "focal dimension: discounted effect"),
        ("rqSVPI", interval(num(sv["pi_low"], w), num(sv["pi_high"], w)),
         "focal dimension: 95% prediction interval, with brackets"),
        ("rqSVCIz", interval(num(sv["ci_low"], w), num(sv["ci_high"], w)),
         "focal dimension: 95% z confidence interval, with brackets"),
        ("rqSVCIHK", interval(num(sv["hk_ci_low"], w), num(sv["hk_ci_high"], w)),
         "focal dimension: 95% Hartung-Knapp interval, with brackets"),
        ("rqCoverageRho", eff(num(need(cc, "spearman_rho", ccsrc), "rho")),
         "Spearman rho, layer silence vs corpus-wide ablation density"),
        ("rqCoverageP", pval(num(need(cc, "exact_permutation_p_one_sided", ccsrc), "p")),
         "its exact one-sided permutation p"),
        ("rqCodedCoverageRho", eff(num(need(d.cov_coded, "spearman_rho", inp.coverage_coded_json),
                                       "coded rho")),
         "the same rho on the coded-set harvest only"),
        ("rqCodedCoverageP", pval(num(need(d.cov_coded, "exact_permutation_p_one_sided",
                                           inp.coverage_coded_json), "coded p")),
         "its exact p"),
        ("rqZeroDimCount", str(len(zero_dims)), "ablatable dimensions with no contrast at all"),
        ("rqAblatableDimCount", str(integer(need(cc, "n_ablatable_dimensions", ccsrc),
                                            "n_ablatable")),
         "ablatable dimensions (layers A-H)"),
        ("rqZeroDimList", join_prose([d.names.prose(k) for k in zero_dims]),
         "those dimensions"),
        ("rqZeroLayerList", join_prose([f"{lay} ({d.names.layer_name(lay).lower()})"
                                        for lay in zero_layers], empty="empty"),
         "layers with no ablated dimension ('empty' if none)"),
        ("rqFGHPaperCounts",
         ", ".join(f"{tex(r['dimension'])} ({integer(r['n_papers'], 'n_papers')}/"
                   f"{integer(r['n_contrasts'], 'n_contrasts')})" for r in sparse) or "none",
         "every F/G/H dimension with >=1 contrast: key (papers/contrasts), corpus-wide"),
        ("rqHarvestTierCoverage", facts["tier_phrase"],
         "noun phrase: share of each prefilter tier the harvest has read"),
        ("rqHarvestTopTierPapers", count(facts["tier_sizes"]["T10"]),
         "papers in the top-signal tier"),
        ("rqHarvestSecondTierPapers", count(facts["tier_sizes"]["T3"]),
         "papers in the second tier"),
        ("rqHarvestDate", facts["date"], "date of the harvest snapshot pooled"),
    ]


def build_macros(d: Loaded, inp: Inputs, stamp: str, focal: str,
                 headline: str = CROSS_PAPER_HEADLINE) -> str:
    sources = [inp.ablation_summary, inp.pooled, inp.credible, inp.bias, inp.contrasts,
               inp.coverage_coded_json, inp.coverage_corpus_json, inp.dimensions]
    if inp.sensitivity:
        sources += [inp.outcomes_summary, inp.results, inp.systems]
    lines = header(sources, stamp,
                   "RQ3 prose macros (text-mode safe; *Pct macros are bare numbers)")
    if inp.sensitivity:
        # the harvester rewrites these while it runs; only the pooled snapshot's papers are read
        # from them, so their mtime says nothing about the numbers and would defeat idempotence
        lines[-1:-1] = [f"%   {rel(p)}  (live; rows of the pooled snapshot's papers only)"
                        for p in (inp.harvest_rows, inp.harvest_outcomes)]
    values = macro_values(d, inp, focal) + sign_warrant_macros(d, inp)
    if inp.sensitivity:
        values += sensitivity_macros(d, inp, headline)
    for name, value, doc in values:
        lines.append(f"% {doc}")
        lines.append(rf"\newcommand{{\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------------------------
# writing
# ------------------------------------------------------------------------------------------------
def _strip_stamp(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("% generated:"))


def write_all(out_dir: Path, fragments: Mapping[str, str]) -> list[Path]:
    """Every fragment staged to a temporary file first, then all moved into place; unchanged
    fragments (ignoring the generation time) are left alone, so a re-run with the same inputs is a
    no-op."""
    out_dir.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for name, text in fragments.items():
            dest = out_dir / name
            if dest.exists() and _strip_stamp(dest.read_text(encoding="utf-8")) == _strip_stamp(text):
                continue
            fd, tmp = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=out_dir)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            staged.append((Path(tmp), dest))
    except BaseException:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)
        raise
    for tmp, dest in staged:
        os.replace(tmp, dest)
    return [dest for _, dest in staged]


def build(inp: Inputs, *, focal: str = FOCAL_DIMENSION, allow_stale: bool = False,
          stamp: str | None = None, headline: str = CROSS_PAPER_HEADLINE) -> dict[str, str]:
    """All four fragments as text. Raises `RQ3InputError` before anything is written."""
    missing = [rel(p) for p in inp.files() if not p.exists()]
    if missing:
        raise RQ3InputError(f"missing input(s): {missing}")
    d = load(inp)
    mixed, stale = consistency(d, inp)
    if mixed:
        raise RQ3InputError("inputs come from different snapshots:\n  - " + "\n  - ".join(mixed))
    if stale and not allow_stale:
        raise RQ3InputError("\n  - ".join(["stale analysis:", *stale]))
    for problem in stale:
        print(f"WARNING (--allow-stale): {problem}", file=sys.stderr)
    stamp = stamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    threshold = survival_threshold()
    return {
        "rq3_pooled.tex": build_pooled(d, inp, stamp, threshold),
        "rq3_coverage.tex": build_coverage(d, inp, stamp),
        "rq3_designs.tex": build_designs(d, inp, stamp, focal, headline),
        "rq3_macros.tex": build_macros(d, inp, stamp, focal, headline),
    }


def main(argv: Sequence[str] | None = None, *, inputs: Inputs | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--focal-dimension", default=FOCAL_DIMENSION)
    p.add_argument("--cross-paper-headline", default=CROSS_PAPER_HEADLINE)
    p.add_argument("--no-sensitivity", action="store_true",
                   help="skip the two sensitivity analyses (tests; the manuscript needs them)")
    p.add_argument("--allow-stale", action="store_true",
                   help="warn instead of failing when the harvester has moved on since the "
                        "analysis ran (the fragments then describe the analysed snapshot)")
    a = p.parse_args(argv)
    inp = inputs or Inputs.default()
    if a.no_sensitivity:
        inp = dataclasses.replace(inp, sensitivity=False)
    try:
        fragments = build(inp, focal=a.focal_dimension, allow_stale=a.allow_stale,
                          headline=a.cross_paper_headline)
    except RQ3InputError as exc:
        print(f"make_rq3_tables: REFUSING to write anything: {exc}", file=sys.stderr)
        return 2
    written = write_all(a.out_dir, fragments)
    for name in fragments:
        dest = a.out_dir / name
        print(f"{'wrote    ' if dest in written else 'unchanged'} {rel(dest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
