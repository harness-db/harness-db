#!/usr/bin/env python
"""Relate harness design choices to benchmark outcomes (Phase 7, tasks 49 and 52).

This script is deliberately small in ambition, because the data is small. Read
`docs/benchmark_caveats.md` and `data/comparable_summary.json` before changing anything here.

WHAT THE DATA SUPPORTS
----------------------
`scripts/mark_comparable.py` fills `comparable_key` = `benchmark|split|base-model` on the subset of
`data/results.csv` where all three are identifiable and the metric is the benchmark's standard one.
Of ~5.9k result rows only ~390 carry a key, those form ~253 keys, and the large majority of keys
hold a single system. A key with one system supports no comparison at all, so the analysable set is
the rows inside keys that hold two or more *distinct systems*: ~143 rows, ~36 keys, ~53 systems.

With 36 clusters a mixed-effects regression of score on 38 coded dimensions is not identifiable.
Protocol §11 anticipated one; this script does not fit it, and says why in its output. What it does
instead, in order:

1. `build_comparable_set`  - the comparable set as a table: per key, the systems, their scores, and
   the spread. This is the primary output. Every later number can be checked against it.
2. `standardise_within_key` - scores are not comparable across benchmarks or metrics, so each score
   becomes a within-key standardised value. Rule, applied per key and stated in every output:
     * key with >= `--rank-threshold` (default 4) systems: z = (x - mean) / sd, sd with ddof=1;
     * key with fewer:  standardised average rank, (rank - (n+1)/2) / sd(1..n, ddof=1). For n=3 that
       is (-1, 0, +1); for n=2 it is (-0.7071, +0.7071). Mean 0 and sd 1 like the z-score, but it
       claims only an ordering, which is all two or three points can carry.
     * key where every score is identical: all values 0.0, method `degenerate`.
   No model is ever fitted on raw scores pooled across benchmarks.
3. `CONTRASTS` - five pre-specified binary design contrasts, fixed as a set before estimation and
   all five reported whatever they come out at. Each has a mechanistic reason to bear on task
   success. There is no stepwise selection and nothing is dropped for being null.
4. For each contrast, the simplest defensible estimator: a within-key difference in standardised
   score, averaged over the keys where the contrast varies, with a percentile bootstrap whose unit
   of resampling is the KEY. A key-fixed-effect OLS with key-clustered errors is reported beside it
   as a secondary check, never as the headline.
5. `mde_from_key_differences` - the minimum detectable standardised effect at 80% power given the
   actual number of keys, computed from the observed between-key spread rather than asserted. When
   only a large effect (>= 0.8 sd) would have been detectable, the script says so in the console
   output and in the figure caption.
6. `permutation_test_within_key` - a second power statement that the bootstrap cannot give. At these
   key counts a bootstrap over K key-level differences can report a narrow interval simply because
   the differences are a bounded, near-deterministic quantity (with two systems in a key the
   standardised difference can only be +-1.41). The within-key permutation test shuffles the design
   labels among the systems of each key, which is the randomisation the design actually implies, and
   its DESIGN FLOOR - one over the number of distinct label assignments - says how small a p-value
   the design could possibly produce. When that floor is above 0.05 no evidence of any strength can
   emerge from the contrast, whatever the point estimate looks like, and the script says so.

GUARDS, because small-n artefacts here would be indistinguishable from findings
-------------------------------------------------------------------------------
* a contrast varying in fewer than `--min-keys` (default 3) keys is reported as NOT ESTIMABLE, with
  its key-level differences printed descriptively: with two keys the bootstrap has one degree of
  freedom and can return a zero-width interval, which is an artefact and not a finding;
* a bootstrap whose replicates are all identical (zero between-key spread) yields no interval and no
  power statement, and is labelled as such rather than as a precise estimate;
* any estimate resting on fewer than 5 keys is flagged FRAGILE in every output.

THE CONFOUND THAT GOES IN EVERY CAPTION
---------------------------------------
`docs/benchmark_caveats.md` section 5: a leaderboard row does not say which commit of the harness
produced its number, while HARNESS-DB codes each system at a pinned commit. The harness coded may
not be the harness that scored. That is measurement error on the regressor; no fixed effect absorbs
it, and it attenuates towards zero. Every effect below is therefore a LOWER BOUND on magnitude, and
it bites hardest on the dimensions that churn between releases (retries, compaction, prompting) and
least on the architecturally stable ones (multi-agent topology). Section 3 of the same document adds
the second confound carried in every caption: which systems appear inside a key is chosen by their
own authors, who report where they do well, so a within-key comparison is not a randomised one.

No model calls. No network. pandas / numpy / scipy / statsmodels / matplotlib(Agg) only.

Run: python scripts/analyse_outcomes.py
     python scripts/analyse_outcomes.py --no-render      (numbers only, no figures)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results.csv"
SYSTEMS = ROOT / "data" / "systems.json"
COMPARABLE_SUMMARY = ROOT / "data" / "comparable_summary.json"
FIG_DIR = ROOT / "paper" / "figures"
TAB_DIR = ROOT / "paper" / "tables"

# Every figure this script writes carries this, per docs/benchmark_caveats.md section 5.
DRIFT_CAVEAT = (
    "Scaffold drift (docs/benchmark_caveats.md sec. 5): a leaderboard or paper row does not say "
    "which commit of the harness produced its number, while HARNESS-DB codes each system at a "
    "pinned commit, so the harness coded may not be the harness that scored. That is measurement "
    "error on the design variable, not the outcome; no fixed effect absorbs it and it attenuates "
    "estimates towards zero. Every effect shown is a LOWER BOUND on magnitude. Reporting is also "
    "self-selected (sec. 3): authors report where their system does well, so a within-key "
    "comparison is not a randomised one. Associational only; no causal reading is supported."
)

LARGE_EFFECT = 0.8  # Cohen's conventional "large" in sd units; the threshold for the power warning.
FRAGILE_KEYS = 5  # below this many keys, an interval is descriptive rather than inferential.


# --------------------------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------------------------
def load_results(path: Path = RESULTS) -> pd.DataFrame:
    """Read results.csv and keep the rows that carry a comparable_key."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in ("system_id", "benchmark", "split", "metric", "score", "comparable_key"):
        if col not in df.columns:
            raise SystemExit(f"{path}: missing column {col!r}")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["comparable_key"] = df["comparable_key"].astype(str).str.strip()
    return df


def load_codings(path: Path = SYSTEMS) -> dict[str, dict]:
    """system_id -> its `coding` dict, from data/systems.json."""
    systems = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"]: (s.get("coding") or {}) for s in systems}


def coded_values(coding: dict, dimension: str) -> list[str] | None:
    """The coded value of one dimension as a list of tokens, or None when it asserts nothing.

    `not_reported` (the sources are silent) and `unresolved` (the coder could not settle it) both
    claim nothing and must not be folded into a reference category: they become None, i.e. missing,
    and the system drops out of that contrast. Single-valued dimensions are wrapped in a list so
    callers can treat multi- and single-valued dimensions alike.
    """
    cell = (coding or {}).get(dimension)
    if not isinstance(cell, dict):
        return None
    if cell.get("unresolved") or cell.get("not_reported"):
        return None
    value = cell.get("value")
    if value is None or value == [] or value == "":
        return None
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


# --------------------------------------------------------------------------------------------
# 1. the comparable set
# --------------------------------------------------------------------------------------------
def build_comparable_set(
    results: pd.DataFrame, min_systems: int = 2, agg: str = "median"
) -> pd.DataFrame:
    """One row per (comparable_key, system_id), restricted to keys with >= min_systems systems.

    A system can hold several rows inside one key (a paper number and a leaderboard number, or two
    configurations of the same harness). Those are aggregated to one observation, by default the
    median, so that a system reporting five numbers does not outvote a system reporting one. The
    number of rows behind each observation and their raw span travel with it.

    Keys with a single system are dropped: a key with one system supports no comparison.
    """
    if agg not in {"median", "mean", "max"}:
        raise ValueError(f"agg must be median, mean or max; got {agg!r}")
    keyed = results[(results["comparable_key"] != "") & results["score"].notna()].copy()
    grouped = keyed.groupby(["comparable_key", "system_id"], sort=True)["score"]
    panel = pd.DataFrame(
        {
            "score": getattr(grouped, agg)(),
            "n_rows": grouped.size(),
            "row_min": grouped.min(),
            "row_max": grouped.max(),
        }
    ).reset_index()
    sizes = panel.groupby("comparable_key")["system_id"].nunique()
    keep = sizes[sizes >= min_systems].index
    panel = panel[panel["comparable_key"].isin(keep)].copy()
    parts = panel["comparable_key"].str.split("|", n=2, expand=True)
    if parts.shape[1] == 3:
        panel["benchmark"], panel["split"], panel["base_model"] = (
            parts[0],
            parts[1],
            parts[2],
        )
    panel["n_systems"] = panel.groupby("comparable_key")["system_id"].transform("nunique")
    return panel.sort_values(
        ["n_systems", "comparable_key", "score"], ascending=[False, True, False]
    ).reset_index(drop=True)


def key_size_distribution(panel: pd.DataFrame) -> dict[str, int]:
    """How many keys hold 2, 3-4 and 5+ systems - the shape of the evidence base."""
    sizes = panel.groupby("comparable_key")["system_id"].nunique()
    return {
        "2": int((sizes == 2).sum()),
        "3-4": int(sizes.between(3, 4).sum()),
        "5+": int((sizes >= 5).sum()),
        "keys": len(sizes),
        "systems": int(panel["system_id"].nunique()),
        "observations": len(panel),
    }


# --------------------------------------------------------------------------------------------
# 2. within-key standardisation
# --------------------------------------------------------------------------------------------
def standardise_within_key(panel: pd.DataFrame, rank_threshold: int = 4) -> pd.DataFrame:
    """Add `z` (within-key standardised score) and `std_method` to the comparable set.

    z-score when the key holds >= rank_threshold systems, standardised average rank below that,
    0.0 everywhere when a key's scores are all identical. See the module docstring for the exact
    rule; `tests/test_analyse_outcomes.py` pins it on a fixture.
    """
    out = panel.copy()
    out["z"] = np.nan
    out["std_method"] = ""
    for key, idx in out.groupby("comparable_key").groups.items():
        scores = out.loc[idx, "score"].to_numpy(dtype=float)
        n = len(scores)
        if n < 2:
            # Cannot standardise a single point; such keys are excluded upstream.
            out.loc[idx, ["z", "std_method"]] = [0.0, "singleton"]
            continue
        if n >= rank_threshold:
            sd = float(np.std(scores, ddof=1))
            if sd == 0.0:
                out.loc[idx, "z"] = 0.0
                out.loc[idx, "std_method"] = "degenerate"
            else:
                out.loc[idx, "z"] = (scores - scores.mean()) / sd
                out.loc[idx, "std_method"] = "zscore"
        else:
            if float(np.std(scores, ddof=1)) == 0.0:
                out.loc[idx, "z"] = 0.0
                out.loc[idx, "std_method"] = "degenerate"
            else:
                ranks = stats.rankdata(scores, method="average")
                sd_rank = float(np.std(np.arange(1, n + 1, dtype=float), ddof=1))
                out.loc[idx, "z"] = (ranks - (n + 1) / 2.0) / sd_rank
                out.loc[idx, "std_method"] = "rank"
    return out


# --------------------------------------------------------------------------------------------
# 3. pre-specified contrasts
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Contrast:
    name: str
    dimension: str  # key in systems.json `coding`
    dimension_id: str  # schema/dimensions.json id, for cross-reference
    exposed_label: str
    reference_label: str
    exposed_when: Callable[[frozenset[str]], bool]
    mechanism: str
    drift_exposure: str  # how hard scaffold drift is expected to attenuate this one


def _any_of(*tokens: str) -> Callable[[frozenset[str]], bool]:
    wanted = frozenset(tokens)
    return lambda coded: bool(coded & wanted)


def _anything_but(*tokens: str) -> Callable[[frozenset[str]], bool]:
    excluded = frozenset(tokens)
    return lambda coded: bool(coded - excluded)


# Fixed as a set before estimation. All five are reported, with their CI, their n and their minimum
# detectable effect, whatever they come out at. Selected from the protocol's mechanistic candidates
# on the basis of which ones vary *within* multi-system keys at all - not on their estimates.
CONTRASTS: tuple[Contrast, ...] = (
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
    ),
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
    ),
)


def contrast_exposure(panel: pd.DataFrame, contrast: Contrast, codings: dict) -> pd.DataFrame:
    """Add `x` in {0, 1} (or NA) for one contrast, then keep only keys where x actually varies.

    A key where every system is on the same side of the contrast carries no within-key information
    and is excluded - that exclusion is what makes the estimate a within-key one.
    """
    out = panel.copy()
    exposure: list[float] = []
    for sid in out["system_id"]:
        values = coded_values(codings.get(sid, {}), contrast.dimension)
        exposure.append(np.nan if values is None else float(contrast.exposed_when(frozenset(values))))
    out["x"] = exposure
    known = out[out["x"].notna()].copy()
    varies = known.groupby("comparable_key")["x"].nunique()
    return known[known["comparable_key"].isin(varies[varies >= 2].index)].copy()


def recurring_comparators(panel: pd.DataFrame, min_keys: int = 5) -> set[str]:
    """Systems that appear in many keys - in practice the community baseline harnesses.

    Computed from the data rather than named by hand: a system present in `min_keys` or more
    comparable keys is the thing other systems report against. The set matters because a design
    feature that correlates with *being a purpose-built submission rather than the baseline* will
    show up as an effect of that feature, and the key fixed effect does not absorb it.
    """
    counts = panel.groupby("system_id")["comparable_key"].nunique()
    return set(counts[counts >= min_keys].index)


def baseline_asymmetry(frame: pd.DataFrame, recurring: set[str]) -> dict:
    """How many keys of a contrast are really purpose-built submission vs recurring baseline."""
    total = 0
    asymmetric = 0
    for _key, sub in frame.groupby("comparable_key", sort=True):
        exposed = set(sub.loc[sub["x"] == 1.0, "system_id"])
        reference = set(sub.loc[sub["x"] == 0.0, "system_id"])
        if not exposed or not reference:
            continue
        total += 1
        if reference <= recurring and not (exposed & recurring):
            asymmetric += 1
    return {
        "keys": total,
        "reference_all_recurring_keys": asymmetric,
        "share": (asymmetric / total) if total else 0.0,
        "recurring_comparators": sorted(recurring),
    }


def key_differences(frame: pd.DataFrame) -> pd.DataFrame:
    """Per key: the within-key difference in standardised score, exposed minus reference."""
    rows = []
    for key, sub in frame.groupby("comparable_key", sort=True):
        exposed = sub[sub["x"] == 1.0]
        reference = sub[sub["x"] == 0.0]
        if exposed.empty or reference.empty:
            continue
        rows.append(
            {
                "comparable_key": key,
                "n_systems": len(sub),
                "n_exposed": len(exposed),
                "n_reference": len(reference),
                "std_method": sub["std_method"].iloc[0],
                "d": float(exposed["z"].mean() - reference["z"].mean()),
            }
        )
    return pd.DataFrame(rows, columns=[
        "comparable_key", "n_systems", "n_exposed", "n_reference", "std_method", "d"
    ])


# --------------------------------------------------------------------------------------------
# 4. bootstrap over KEYS, and the power statement
# --------------------------------------------------------------------------------------------
def bootstrap_key_means(d: Sequence[float], n_boot: int = 10_000, seed: int = 20260924) -> np.ndarray:
    """Percentile bootstrap of the mean of key-level differences, resampling KEYS.

    The unit of resampling is the key, not the row: one draw takes K keys with replacement from the
    K observed keys and averages their differences. Resampling rows instead would treat the eleven
    systems inside `SWE-bench|Lite|gpt-4o` as eleven independent pieces of evidence about harness
    design, which they are not - they share one benchmark, one split and one model.
    """
    d = np.asarray(d, dtype=float)
    k = len(d)
    if k == 0:
        return np.empty(0, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(int(n_boot), k))
    return d[idx].mean(axis=1)


def mde_from_key_differences(
    d: Sequence[float], alpha: float = 0.05, power: float = 0.80
) -> float:
    """Minimum detectable standardised effect at `power`, two-sided `alpha`, given K keys.

    The estimator is the mean of K key-level differences, so its standard error is
    s_d / sqrt(K) with s_d the sample sd (ddof=1) of those differences, and the smallest true effect
    a two-sided one-sample t-test would reject the null for at `power` is

        MDE = (t_{1-alpha/2, K-1} + t_{power, K-1}) * s_d / sqrt(K)

    Computed from the observed between-key spread, not asserted. Returns NaN when K < 2, because
    with one key there is no between-key spread to estimate and no power statement to make.
    """
    d = np.asarray(d, dtype=float)
    k = len(d)
    if k < 2:
        return float("nan")
    s_d = float(np.std(d, ddof=1))
    df = k - 1
    t_alpha = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    t_power = float(stats.t.ppf(power, df))
    return (t_alpha + t_power) * s_d / math.sqrt(k)


def _key_difference_options(z: np.ndarray, x: np.ndarray) -> list[float]:
    """Every within-key difference the key could have produced under relabelling.

    The exposure labels of a key are permuted among its systems, holding the number of exposed
    systems fixed. The returned list has one entry per distinct assignment, so its length is
    C(n_k, m_k) and it is the key's contribution to the design's randomisation distribution.
    """
    from itertools import combinations

    n = len(z)
    m = int(x.sum())
    options = []
    for picked in combinations(range(n), m):
        mask = np.zeros(n, dtype=bool)
        mask[list(picked)] = True
        options.append(float(z[mask].mean() - z[~mask].mean()))
    return options


def permutation_test_within_key(
    frame: pd.DataFrame,
    n_perm: int = 10_000,
    seed: int = 20260924,
    exact_limit: int = 50_000,
) -> dict:
    """Randomisation test on the design: shuffle the labels inside each key, not across keys.

    Reports the two-sided p, and - the point of it - the DESIGN FLOOR `p_min_attainable`, which is
    one over the number of distinct label assignments the design admits. A contrast whose floor sits
    above 0.05 cannot produce evidence at any conventional level however large its point estimate,
    and that is a statement about the dataset, not about harness design.
    """
    per_key: list[list[float]] = []
    for _key, sub in frame.groupby("comparable_key", sort=True):
        z = sub["z"].to_numpy(dtype=float)
        x = sub["x"].to_numpy(dtype=float)
        if x.sum() in (0.0, float(len(x))):
            continue
        per_key.append(_key_difference_options(z, x))
    if not per_key:
        return {"available": False, "reason": "no key with variation in the contrast"}
    n_assignments = 1
    for options in per_key:
        n_assignments *= len(options)
        if n_assignments > 10**12:
            break
    observed = float(key_differences(frame)["d"].mean())
    tol = 1e-12
    if n_assignments <= exact_limit:
        from itertools import product

        stats_all = np.array([float(np.mean(combo)) for combo in product(*per_key)])
        p_two = float((np.abs(stats_all) >= abs(observed) - tol).mean())
        mode = "exact"
        n_draws = len(stats_all)
    else:
        rng = np.random.default_rng(seed)
        draws = np.empty(int(n_perm), dtype=float)
        arrays = [np.asarray(o, dtype=float) for o in per_key]
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
        # Saturated: the observed labelling is the most extreme the design admits, so the p-value is
        # sitting on its own floor and one differently-ordered key would move it.
        "saturated": bool(mode == "exact" and p_two <= 1.0 / n_assignments + 1e-12),
    }


def fixed_effect_ols(frame: pd.DataFrame) -> dict:
    """Secondary check: z ~ x + C(key), errors clustered on key. Never the headline.

    With a handful of clusters a cluster-robust p-value is anti-conservative, which is why this sits
    beside the bootstrap rather than replacing it. Reported with its CI and its n, never alone.
    """
    out: dict = {"available": False}
    n_keys = frame["comparable_key"].nunique()
    if len(frame) < 3 or n_keys < 1 or frame["x"].nunique() < 2:
        out["reason"] = "too few observations or no variation in the contrast"
        return out
    try:
        import statsmodels.formula.api as smf
    except Exception as exc:  # pragma: no cover - statsmodels is a declared dependency
        out["reason"] = f"statsmodels unavailable: {exc}"
        return out
    data = frame.rename(columns={"comparable_key": "key"})[["z", "x", "key"]].copy()
    formula = "z ~ x" if n_keys < 2 else "z ~ x + C(key)"
    try:
        fit = smf.ols(formula, data=data).fit(
            cov_type="cluster", cov_kwds={"groups": data["key"]}
        )
        ci = fit.conf_int().loc["x"]
        out.update(
            available=True,
            formula=formula,
            coef=float(fit.params["x"]),
            ci_low=float(ci[0]),
            ci_high=float(ci[1]),
            p_value=float(fit.pvalues["x"]),
            n_observations=len(data),
            n_keys=int(n_keys),
            note="cluster-robust on key; with few clusters the p-value is anti-conservative",
        )
    except Exception as exc:
        out["reason"] = f"fit failed: {exc}"
    return out


def estimate_contrast(
    panel: pd.DataFrame,
    contrast: Contrast,
    codings: dict,
    n_boot: int = 10_000,
    seed: int = 20260924,
    min_keys: int = 3,
) -> dict:
    """Everything reportable about one pre-specified contrast, estimable or not.

    A contrast is never dropped. When it varies in fewer than `min_keys` keys it is reported as NOT
    ESTIMABLE with its key-level differences attached, because with one or two keys the between-key
    spread has 0 or 1 degrees of freedom and the bootstrap can return a zero-width interval that
    looks like precision and is an artefact of the design.
    """
    frame = contrast_exposure(panel, contrast, codings)
    diffs = key_differences(frame)
    n_keys = len(diffs)
    d = diffs["d"].to_numpy(dtype=float)
    result: dict = {
        "name": contrast.name,
        "dimension": contrast.dimension,
        "dimension_id": contrast.dimension_id,
        "exposed": contrast.exposed_label,
        "reference": contrast.reference_label,
        "mechanism": contrast.mechanism,
        "drift_exposure": contrast.drift_exposure,
        "n_keys": n_keys,
        "n_systems": int(frame["system_id"].nunique()) if len(frame) else 0,
        "n_observations": len(frame),
        "n_exposed_obs": int((frame["x"] == 1.0).sum()) if len(frame) else 0,
        "n_reference_obs": int((frame["x"] == 0.0).sum()) if len(frame) else 0,
        "keys": diffs.to_dict(orient="records"),
        "key_differences": [float(v) for v in d],
        "estimable": n_keys >= min_keys,
        "fragile": bool(0 < n_keys < FRAGILE_KEYS),
        "effect": float(d.mean()) if n_keys else float("nan"),
        "ci_low": float("nan"),
        "ci_high": float("nan"),
        "mde_80": float("nan"),
        "se": float("nan"),
        "bootstrap_unit": "comparable_key",
        "n_boot": int(n_boot),
        "seed": int(seed),
        "degenerate_interval": False,
    }
    result["permutation"] = (
        permutation_test_within_key(frame, n_perm=n_boot, seed=seed)
        if n_keys else {"available": False, "reason": "no key with variation in the contrast"}
    )
    result["baseline_asymmetry"] = baseline_asymmetry(frame, recurring_comparators(panel))
    if n_keys >= min_keys:
        replicates = bootstrap_key_means(d, n_boot=n_boot, seed=seed)
        spread = float(np.std(d, ddof=1))
        if spread == 0.0:
            # Every key gave the identical difference. The bootstrap then has nothing to resample
            # and would report a zero-width interval; that is not precision, it is no information
            # about between-key variability at all.
            result["degenerate_interval"] = True
            result["degenerate_reason"] = (
                f"all {n_keys} key-level differences are identical ({d[0]:+.3f}), so the "
                "between-key spread is zero and neither an interval nor a power statement is defined"
            )
        else:
            result["ci_low"] = float(np.percentile(replicates, 2.5))
            result["ci_high"] = float(np.percentile(replicates, 97.5))
            result["mde_80"] = mde_from_key_differences(d)
            result["se"] = spread / math.sqrt(n_keys)
        result["ols"] = fixed_effect_ols(frame)
    else:
        result["not_estimable_reason"] = (
            f"the contrast varies inside only {n_keys} comparable key(s); {min_keys} is the "
            "pre-specified minimum, below which the between-key spread has too few degrees of "
            "freedom for an interval or a power statement"
        )
        result["ols"] = {"available": False, "reason": "not estimable"}
    interval_usable = bool(
        result["estimable"]
        and not result["degenerate_interval"]
        and not np.isnan(result["ci_low"])
    )
    result["ci_excludes_zero"] = bool(
        interval_usable and not (result["ci_low"] <= 0.0 <= result["ci_high"])
    )
    perm_p = result["permutation"].get("p_two_sided")
    result["perm_rejects"] = bool(perm_p is not None and perm_p < 0.05)
    # Both have to agree before anything is called detected. The bootstrap interval over a handful
    # of key-level differences is the weaker of the two - it assumes the K differences represent
    # their own sampling distribution - so when they disagree the randomisation test wins and the
    # reported finding is the null one.
    result["detected"] = bool(result["ci_excludes_zero"] and result["perm_rejects"])
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
    """A p-value never printed as 0.000, because no finite resampling supports that."""
    if p is None:
        return "n/a"
    if floor is not None and p <= floor + 1e-15:
        return f"<{max(floor, 1e-4):.4f}"
    if p < 1e-4:
        return "<0.0001"
    return f"{p:.4f}"


def power_sentence(result: dict) -> str:
    """The power statement, in words, for the console and for the figure caption.

    Two quantities, because at these key counts neither alone is honest: the minimum detectable
    standardised effect from the observed between-key spread, and the design floor on the
    permutation p-value, which is what the contrast could achieve at best.
    """
    name = result["name"]
    perm = result.get("permutation") or {}
    floor = ""
    if perm.get("available"):
        n_assign = perm["n_assignments"]
        floor = (
            f" The design admits {n_assign:,} distinct within-key label assignments, so the smallest "
            f"attainable permutation p-value is "
            f"{max(perm['p_min_attainable'], 1e-4):.4f}"
            + (
                "; no conventional significance level is reachable from this contrast whatever the "
                "point estimate."
                if perm["floor_above_05"]
                else f" (observed "
                     f"{_fmt_p(perm['p_two_sided'], 1.0 / (perm['n_draws'] + 1))})."
            )
        )
    if not result["estimable"]:
        return (
            f"{name}: NOT ESTIMABLE - the contrast varies inside only {result['n_keys']} comparable "
            f"key(s), so no interval and no minimum detectable effect are defined." + floor
        )
    if result["degenerate_interval"]:
        return (
            f"{name}: all {result['n_keys']} key-level differences are identical, so the between-key "
            f"spread is zero and no interval or minimum detectable effect is defined; the apparent "
            f"precision would be an artefact." + floor
        )
    mde = result["mde_80"]
    stem = (
        f"{name}: with {result['n_keys']} keys, {result['n_observations']} observations and "
        f"{result['n_systems']} distinct systems, the smallest effect detectable at 80% power "
        f"(two-sided, alpha=0.05) is {mde:.2f} within-key sd."
    )
    if result["only_large_detectable"]:
        stem += (
            " Only a very large effect would have been detectable here, so the absence of a detected "
            "association is uninformative about anything smaller."
        )
    else:
        stem += " Effects smaller than that are beyond the resolution of this dataset."
    if result["fragile"]:
        stem += (
            f" FRAGILE: fewer than {FRAGILE_KEYS} keys, so the between-key spread that both the "
            "interval and this number rest on is itself barely estimated; treat the interval as "
            "descriptive."
        )
    return stem + floor


# --------------------------------------------------------------------------------------------
# framing: how far the coded corpus gets us
# --------------------------------------------------------------------------------------------
def coverage_counts(results: pd.DataFrame, codings: dict, panel: pd.DataFrame) -> dict:
    """The ceiling on this analysis: coded systems -> with a result -> keyed -> comparable."""
    coded = set(codings)
    with_rows = set(results.loc[results["score"].notna(), "system_id"]) & coded
    keyed = set(results.loc[results["comparable_key"] != "", "system_id"]) & coded
    comparable = set(panel["system_id"]) & coded
    return {
        "coded_systems": len(coded),
        "with_any_result_row": len(with_rows),
        "with_comparable_key": len(keyed),
        "in_multi_system_key": len(comparable),
        "gap_result_to_comparable": len(with_rows) - len(comparable),
        "share_of_coded_with_result": len(with_rows) / len(coded) if coded else 0.0,
        "share_of_coded_comparable": len(comparable) / len(coded) if coded else 0.0,
    }


# --------------------------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------------------------
def _wrap(text: str, width: int = 128) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _save(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for ext in ("svg", "pdf"):
        path = stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight")
        written.append(path)
    return written


def figure_comparable_set(panel: pd.DataFrame, dist: dict, out_stem: Path) -> list[Path]:
    """The comparable set itself: one strip per key on the within-key standardised axis."""
    import matplotlib.pyplot as plt

    keys = (
        panel.groupby("comparable_key")
        .agg(n=("system_id", "nunique"), lo=("score", "min"), hi=("score", "max"))
        .sort_values(["n", "comparable_key"], ascending=[True, False])
    )
    n_keys = len(keys)
    # The systems and their scores are the evidence, so they go on the figure, not only in the CSV.
    annotations = {}
    for key in keys.index:
        sub = panel[panel["comparable_key"] == key].sort_values("score", ascending=False)
        row = keys.loc[key]
        annotations[key] = (
            f"n={int(row['n'])}  spread {row['hi'] - row['lo']:.1f} pp  |  "
            + ",  ".join(f"{r.system_id} {r.score:.1f}" for r in sub.itertuples())
        )
    widest = max(len(a) for a in annotations.values())
    fig_h = max(4.0, 0.30 * n_keys + 3.4)
    fig_w = 8.5 + 0.040 * widest
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    colours = {"zscore": "#1f4e79", "rank": "#b45309", "degenerate": "#6b7280", "singleton": "#000"}
    for i, (key, row) in enumerate(keys.iterrows()):
        sub = panel[panel["comparable_key"] == key]
        method = sub["std_method"].iloc[0]
        ax.scatter(
            sub["z"], [i] * len(sub), s=34, alpha=0.85,
            color=colours.get(method, "#1f4e79"), zorder=3,
            edgecolors="white", linewidths=0.5,
        )
        ax.plot([sub["z"].min(), sub["z"].max()], [i, i], color="#cbd5e1", lw=1.0, zorder=1)
        ax.annotate(
            annotations[key],
            xy=(1.008, i), xycoords=("axes fraction", "data"),
            va="center", ha="left", fontsize=5.6, color="#374151",
            family="DejaVu Sans Mono",
        )
    ax.set_yticks(range(n_keys))
    ax.set_yticklabels(list(keys.index), fontsize=6.6, family="DejaVu Sans Mono")
    ax.set_ylim(-0.8, n_keys - 0.2)
    ax.axvline(0.0, color="#9ca3af", lw=0.8, ls="--", zorder=2)
    ax.set_xlabel("within-key standardised score (0 = key mean; see rule in caption)", fontsize=8)
    ax.set_title(
        "The comparable set: every key with two or more coded systems, with every system and score\n"
        f"{dist['keys']} keys, {dist['systems']} systems, {dist['observations']} observations "
        f"(one per key x system)   |   keys with 2 systems: {dist['2']}, "
        f"with 3-4: {dist['3-4']}, with 5+: {dist['5+']}",
        fontsize=9.5, loc="left",
    )
    ax.tick_params(axis="x", labelsize=7.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=colours["zscore"], label="z-score (key has 4+ systems)"),
        plt.Line2D([], [], marker="o", ls="", color=colours["rank"], label="standardised rank (2-3 systems)"),
        plt.Line2D([], [], marker="o", ls="", color=colours["degenerate"], label="all scores equal (set to 0)"),
    ]
    ax.legend(handles=handles, fontsize=7, loc="lower right", frameon=False)
    caption = _wrap(
        "This is the entire evidence base for any outcome claim in this review. A key is "
        "benchmark|split|base-model; a system contributes one observation per key, the median of "
        "its rows in that key. Keys holding a single system are excluded because they support no "
        "comparison. Standardisation rule: z = (x - key mean) / key sd (ddof=1) for keys with 4 or "
        "more systems, standardised average rank (rank - (n+1)/2) / sd(1..n) below that, 0 when a "
        "key's scores are identical. Raw ranges are percentage points on each benchmark's standard "
        "metric and are not comparable across keys. " + DRIFT_CAVEAT,
        width=150,
    )
    fig.text(0.0, -0.012, caption, fontsize=6.6, va="top", ha="left", color="#374151")
    return _save(fig, out_stem)


def figure_contrasts(estimates: list[dict], out_stem: Path) -> list[Path]:
    """Forest plot of the pre-specified contrasts, with the detectability band behind each."""
    import matplotlib.pyplot as plt

    order = list(reversed(estimates))
    fig, ax = plt.subplots(figsize=(11.0, 1.15 * len(order) + 4.0))
    ymax = len(order)
    for y, est in enumerate(order):
        has_interval = est["estimable"] and not est["degenerate_interval"]
        # Always show the raw key-level differences: they are the evidence, the interval is a summary.
        if est["key_differences"]:
            ax.scatter(
                est["key_differences"], [y + 0.24] * len(est["key_differences"]),
                s=16, color="#94a3b8", zorder=2, alpha=0.9,
            )
        if has_interval:
            mde = est["mde_80"]
            ax.add_patch(
                plt.Rectangle(
                    (-mde, y - 0.30), 2 * mde, 0.44,
                    color="#fde68a" if est["only_large_detectable"] else "#e5e7eb",
                    alpha=0.65, zorder=1, lw=0,
                )
            )
            ax.plot(
                [est["ci_low"], est["ci_high"]], [y, y],
                color="#1f4e79", lw=2.2, zorder=3, solid_capstyle="butt",
            )
            ax.scatter(
                [est["effect"]], [y], s=62, zorder=4,
                color="#ffffff", edgecolors="#1f4e79", linewidths=1.8,
            )
            perm = est["permutation"]
            label = (
                f"{est['effect']:+.2f}  [{est['ci_low']:+.2f}, {est['ci_high']:+.2f}]   "
                f"K={est['n_keys']} keys, {est['n_observations']} obs, "
                f"{est['n_systems']} systems   MDE(80%)=+-{est['mde_80']:.2f}   "
                f"perm p={_fmt_p(perm['p_two_sided'], 1.0 / (perm['n_draws'] + 1))} "
                f"(floor >={max(perm['p_min_attainable'], 1e-4):.4f})"
                + (
                    "   NULL (bootstrap CI excludes 0 but the randomisation test does not reject)"
                    if est["disagreement"]
                    else ("   NULL" if est["null"] else "   DETECTED")
                )
                + ("   FRAGILE" if est["fragile"] else "")
            )
        else:
            ax.scatter([est["effect"]], [y], s=54, marker="x", color="#9ca3af", zorder=4)
            reason = ("zero between-key spread" if est["degenerate_interval"]
                      else f"varies in only {est['n_keys']} key(s)")
            label = (
                f"{est['effect']:+.2f}, NO INTERVAL - {reason}; "
                f"K={est['n_keys']} keys, {est['n_observations']} obs, "
                f"{est['n_systems']} systems"
            )
            if est.get("permutation", {}).get("available"):
                label += (f"   design floor p>={est['permutation']['p_min_attainable']:.3f}")
        ax.annotate(
            label, xy=(1.005, y), xycoords=("axes fraction", "data"),
            va="center", ha="left", fontsize=6.9, color="#374151",
        )
    ax.axvline(0.0, color="#111827", lw=0.9, zorder=2)
    ax.set_yticks(range(ymax))
    ax.set_yticklabels(
        [f"{e['name']}  ({e['dimension_id']} {e['dimension']})" for e in order],
        fontsize=8, family="DejaVu Sans Mono",
    )
    ax.set_ylim(-0.7, ymax - 0.3)
    ax.set_xlabel(
        "within-key difference in standardised score, exposed minus reference "
        "(positive = higher benchmark score)", fontsize=8,
    )
    ax.set_title(
        "Five pre-specified harness-design contrasts, estimated within benchmark x split x model\n"
        "Open circle: mean of key-level differences. Bar: percentile bootstrap CI resampling KEYS "
        "(not rows). Shaded band: +- the minimum detectable effect at 80% power (amber = only a "
        "large effect was detectable).\nSmall grey dots above each row: the individual key-level "
        "differences the estimate is made of - the evidence, of which the interval is only a summary.",
        fontsize=9.0, loc="left",
    )
    ax.tick_params(axis="x", labelsize=7.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    caption = _wrap(
        "All five contrasts were fixed as a set before estimation and all five are reported, "
        "including the null ones and the ones the data cannot support; there is no stepwise "
        "selection and nothing was dropped for its result. A key contributes only if the contrast "
        "varies inside it, which is what makes each estimate a within-key one. A CI covering zero "
        "means no detectable association at this sample size - read it together with the minimum "
        "detectable effect on the same line, which is what could have been found. A row marked NO "
        "INTERVAL is one where the design cannot support inference at all. " + DRIFT_CAVEAT,
        width=150,
    ) + "\n\nPower, computed from the observed between-key spread and from the design itself:\n" + (
        "\n".join(_wrap("  - " + e["power_sentence"], width=150) for e in estimates)
    )
    fig.text(0.0, -0.012, caption, fontsize=6.6, va="top", ha="left", color="#374151")
    return _save(fig, out_stem)


def figure_coverage(coverage: dict, out_stem: Path) -> list[Path]:
    """The real ceiling: how few coded systems reach a comparison at all."""
    import matplotlib.pyplot as plt

    stages = [
        ("coded systems in HARNESS-DB", coverage["coded_systems"]),
        ("with any result row (paper or leaderboard)", coverage["with_any_result_row"]),
        ("with a comparable key", coverage["with_comparable_key"]),
        ("inside a key shared with another system", coverage["in_multi_system_key"]),
    ]
    fig, ax = plt.subplots(figsize=(10.0, 3.9))
    ys = list(range(len(stages)))[::-1]
    total = stages[0][1]
    for y, (label, n) in zip(ys, stages):
        ax.barh(y, n, height=0.55, color="#1f4e79" if y else "#b45309", alpha=0.9)
        ax.annotate(
            f"{n:,}   ({n / total:.1%} of coded)", xy=(n, y), xytext=(6, 0),
            textcoords="offset points", va="center", fontsize=8.5, color="#374151",
        )
    ax.set_yticks(ys)
    ax.set_yticklabels([s[0] for s in stages], fontsize=8.5)
    ax.set_xlim(0, total * 1.28)
    ax.set_xlabel("systems", fontsize=8)
    ax.set_title(
        "Why the outcome analysis is small: the attrition from coded system to comparable system",
        fontsize=9.5, loc="left",
    )
    ax.tick_params(axis="x", labelsize=7.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    caption = _wrap(
        f"{coverage['with_any_result_row']:,} of {coverage['coded_systems']:,} coded systems report "
        f"any benchmark number at all, and only {coverage['in_multi_system_key']} sit in a key "
        f"shared with another coded system, which is the only configuration that supports a "
        f"comparison. The gap of {coverage['gap_result_to_comparable']:,} systems - reporting a "
        "score but never against a peer at the same benchmark, split and base model - is the "
        "ceiling on every outcome claim in this review, and it is a finding about the field's "
        "reporting practice, not a data-collection failure. " + DRIFT_CAVEAT,
        width=150,
    )
    fig.text(0.0, -0.06, caption, fontsize=6.8, va="top", ha="left", color="#374151")
    return _save(fig, out_stem)


# --------------------------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------------------------
def comparable_set_report(panel: pd.DataFrame, limit: int = 12) -> str:
    """The comparable set in brief, for the console."""
    lines = []
    keys = (
        panel.groupby("comparable_key")
        .agg(n=("system_id", "nunique"), lo=("score", "min"), hi=("score", "max"))
        .sort_values(["n", "comparable_key"], ascending=[False, True])
    )
    lines.append(f"{'key':52s} {'n':>3s} {'raw range':>16s} {'spread':>7s}  systems")
    for key, row in keys.head(limit).iterrows():
        sub = panel[panel["comparable_key"] == key].sort_values("score", ascending=False)
        systems = ", ".join(f"{r.system_id} {r.score:.1f}" for r in sub.itertuples())
        lines.append(
            f"{key[:52]:52s} {int(row['n']):3d} {row['lo']:6.1f}-{row['hi']:<9.1f} "
            f"{row['hi'] - row['lo']:7.1f}  {systems[:150]}"
        )
    if len(keys) > limit:
        lines.append(f"... {len(keys) - limit} further keys; full table in the CSV output")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--systems", type=Path, default=SYSTEMS)
    ap.add_argument("--fig-dir", type=Path, default=FIG_DIR)
    ap.add_argument("--tab-dir", type=Path, default=TAB_DIR)
    ap.add_argument("--min-systems", type=int, default=2,
                    help="minimum distinct systems for a key to be analysable (2: a comparison)")
    ap.add_argument("--rank-threshold", type=int, default=4,
                    help="keys with fewer systems than this are standardised by rank, not z")
    ap.add_argument("--agg", default="median", choices=("median", "mean", "max"),
                    help="how to collapse several rows of one system inside one key")
    ap.add_argument("--n-boot", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=20260924)
    ap.add_argument("--min-keys", type=int, default=3,
                    help="minimum keys in which a contrast must vary before an interval is reported")
    ap.add_argument("--no-render", action="store_true", help="skip figures, print numbers only")
    args = ap.parse_args(argv)

    results = load_results(args.results)
    codings = load_codings(args.systems)
    panel = build_comparable_set(results, min_systems=args.min_systems, agg=args.agg)
    panel = standardise_within_key(panel, rank_threshold=args.rank_threshold)
    dist = key_size_distribution(panel)
    coverage = coverage_counts(results, codings, panel)

    print("=" * 100)
    print("HARNESS-DB outcome analysis (Phase 7 task 49). Associational only; see the caveat below.")
    print("=" * 100)
    print()
    print("COVERAGE - the ceiling on everything that follows")
    print(f"  coded systems                                 {coverage['coded_systems']:>6,}")
    print(f"  with any result row (paper or leaderboard)     {coverage['with_any_result_row']:>6,}"
          f"  ({coverage['share_of_coded_with_result']:.1%} of coded)")
    print(f"  with a comparable key                         {coverage['with_comparable_key']:>6,}")
    print(f"  inside a key shared with another system       {coverage['in_multi_system_key']:>6,}"
          f"  ({coverage['share_of_coded_comparable']:.1%} of coded)")
    print(f"  gap (reports a score, never against a peer)   {coverage['gap_result_to_comparable']:>6,}")
    print()
    print("THE COMPARABLE SET")
    print(f"  {dist['keys']} keys, {dist['systems']} systems, {dist['observations']} observations; "
          f"keys with 2 systems: {dist['2']}, with 3-4: {dist['3-4']}, with 5+: {dist['5+']}")
    print("  standardisation: " + ", ".join(
        f"{k}={int(v)}" for k, v in panel["std_method"].value_counts().items()
    ))
    print()
    print(comparable_set_report(panel))
    print()
    print("PRE-SPECIFIED CONTRASTS (all five reported; none dropped for its result)")
    estimates = [
        estimate_contrast(panel, c, codings, n_boot=args.n_boot, seed=args.seed,
                          min_keys=args.min_keys)
        for c in CONTRASTS
    ]
    for est in estimates:
        print(f"\n  {est['name']}  ({est['dimension_id']} {est['dimension']})"
              + ("   [FRAGILE]" if est["fragile"] else ""))
        print(f"    exposed   : {est['exposed']}")
        print(f"    reference : {est['reference']}")
        print(f"    rests on  : {est['n_keys']} keys, {est['n_observations']} observations, "
              f"{est['n_systems']} distinct systems "
              f"({est['n_exposed_obs']} exposed / {est['n_reference_obs']} reference observations)")
        if est["estimable"] and not est["degenerate_interval"]:
            print(f"    effect    : {est['effect']:+.3f} within-key sd  "
                  f"95% CI [{est['ci_low']:+.3f}, {est['ci_high']:+.3f}]  "
                  f"(percentile bootstrap resampling {est['n_keys']} KEYS, "
                  f"{est['n_boot']:,} draws, seed {est['seed']})")
        elif est["estimable"]:
            print(f"    effect    : {est['effect']:+.3f} within-key sd, NO INTERVAL - "
                  f"{est['degenerate_reason']}")
        else:
            print(f"    effect    : {est['effect']:+.3f} within-key sd (descriptive only, "
                  f"no interval)")
        print("    per key   : " + ", ".join(
            f"{k['comparable_key']} d={k['d']:+.2f} (n={k['n_systems']}, "
            f"{k['n_exposed']}v{k['n_reference']}, {k['std_method']})" for k in est["keys"]
        ) if est["keys"] else "    per key   : none")
        perm = est.get("permutation", {})
        if perm.get("available"):
            print(f"    perm test : within-key randomisation, two-sided p="
                  f"{_fmt_p(perm['p_two_sided'], 1.0 / (perm['n_draws'] + 1))} ({perm['mode']}, "
                  f"{perm['n_draws']:,} draws); design floor p>="
                  f"{max(perm['p_min_attainable'], 1e-4):.4f} "
                  f"from {perm['n_assignments']:,} possible label assignments")
        ols = est.get("ols", {})
        if ols.get("available"):
            print(f"    secondary : key-FE OLS coef {ols['coef']:+.3f} "
                  f"[{ols['ci_low']:+.3f}, {ols['ci_high']:+.3f}] p={ols['p_value']:.3f} "
                  f"n={ols['n_observations']} obs / {ols['n_keys']} keys ({ols['note']})")
        ba = est.get("baseline_asymmetry", {})
        if ba.get("keys"):
            print(f"    confound  : in {ba['reference_all_recurring_keys']} of {ba['keys']} keys the "
                  f"reference side is only recurring comparator harnesses "
                  f"({', '.join(ba['recurring_comparators'])}) and no exposed system is one, so the "
                  f"contrast is partly 'purpose-built submission vs baseline'")
        if not est["estimable"]:
            print(f"    finding   : NOT ESTIMABLE - {est['not_estimable_reason']}")
        elif est["degenerate_interval"]:
            print("    finding   : NOT INTERPRETABLE - zero between-key spread, see above")
        elif est["disagreement"]:
            print("    finding   : NO DETECTABLE ASSOCIATION - the bootstrap interval excludes zero "
                  "but the within-key randomisation test does not reject, and with this many keys "
                  "the randomisation test is the more trustworthy of the two. The null is the "
                  "reported result.")
        elif est["null"]:
            print("    finding   : NO DETECTABLE ASSOCIATION - the 95% CI covers zero. Reported as "
                  "a result, not an absence of one; read it with the detectable effect below.")
        else:
            extra = ""
            if perm.get("saturated"):
                extra += (
                    " The randomisation p-value sits exactly on the design floor, i.e. the observed "
                    "ordering is the most extreme this design can produce, so a single "
                    "differently-ordered key would push it above 0.05; the test is saturated."
                )
            if ba.get("keys") and ba["share"] == 1.0:
                extra += (
                    " In every contributing key the reference side is a recurring comparator "
                    "harness, so this cannot be separated from 'purpose-built submission beats the "
                    "baseline' and should not be attributed to the design feature."
                )
            print("    finding   : ASSOCIATION DETECTED - CI excludes zero and the randomisation "
                  "test rejects. Associational only; see the confound and drift lines before "
                  "reading any design advice into it." + extra)
        print(f"    power     : {est['power_sentence']}")
        print(f"    mechanism : {est['mechanism']}")
        print(f"    drift     : attenuation risk {est['drift_exposure']}; "
              f"the estimate is a lower bound on magnitude")

    print()
    print("WHAT WAS NOT FITTED, AND WHY")
    print(_wrap(
        f"  Protocol §11 envisaged a mixed-effects regression of score on the coded dimensions with "
        f"benchmark x model fixed effects. With {dist['keys']} clusters and {dist['observations']} "
        f"observations, 38 design dimensions are not identifiable; such a fit would produce "
        f"coefficients and p-values with no support in the data. It is therefore not reported. The "
        f"within-key contrasts above are what {dist['observations']} observations across "
        f"{dist['keys']} keys can carry.", width=112))
    print()
    print(_wrap("  CAVEAT IN EVERY CAPTION: " + DRIFT_CAVEAT, width=112))

    # ---- machine-readable outputs -----------------------------------------------------------
    args.tab_dir.mkdir(parents=True, exist_ok=True)
    panel_out = args.tab_dir / "outcomes_comparable_set.csv"
    panel.to_csv(panel_out, index=False)
    contrast_rows = pd.DataFrame([
        {
            "contrast": e["name"], "dimension_id": e["dimension_id"], "dimension": e["dimension"],
            "estimable": e["estimable"], "effect_sd": e["effect"], "ci_low": e["ci_low"],
            "ci_high": e["ci_high"], "mde_80": e["mde_80"], "n_keys": e["n_keys"],
            "n_observations": e["n_observations"], "n_systems": e["n_systems"],
            "n_exposed_obs": e["n_exposed_obs"], "n_reference_obs": e["n_reference_obs"],
            "null_result": e["null"], "detected": e["detected"], "fragile": e["fragile"],
            "degenerate_interval": e["degenerate_interval"],
            "ci_perm_disagreement": e["disagreement"],
            "only_large_detectable": e["only_large_detectable"],
            "perm_p": e.get("permutation", {}).get("p_two_sided"),
            "perm_p_floor": e.get("permutation", {}).get("p_min_attainable"),
            "reference_all_recurring_keys":
                e.get("baseline_asymmetry", {}).get("reference_all_recurring_keys"),
            "ols_coef": e.get("ols", {}).get("coef"), "ols_p": e.get("ols", {}).get("p_value"),
            "drift_exposure": e["drift_exposure"],
        }
        for e in estimates
    ])
    contrast_out = args.tab_dir / "outcomes_contrasts.csv"
    contrast_rows.to_csv(contrast_out, index=False)
    summary = {
        "generated_from": str(args.results.name),
        "coverage": coverage,
        "comparable_set": dist,
        "standardisation": {
            "rank_threshold": args.rank_threshold,
            "rule": "z=(x-mean)/sd (ddof=1) at or above the threshold; "
                    "standardised average rank below it; 0 when a key is degenerate",
            "methods_used": {k: int(v) for k, v in panel["std_method"].value_counts().items()},
            "row_aggregation": args.agg,
        },
        "bootstrap": {"unit": "comparable_key", "draws": args.n_boot, "seed": args.seed},
        "not_fitted": "mixed-effects regression on 38 dimensions: not identifiable at this n",
        "caveat": DRIFT_CAVEAT,
        "contrasts": estimates,
    }
    summary_out = args.tab_dir / "outcomes_summary.json"
    summary_out.write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")

    written = [panel_out, contrast_out, summary_out]
    if not args.no_render:
        import matplotlib
        matplotlib.use("Agg")
        written += figure_comparable_set(panel, dist, args.fig_dir / "outcomes_comparable_set")
        written += figure_contrasts(estimates, args.fig_dir / "outcomes_contrasts")
        written += figure_coverage(coverage, args.fig_dir / "outcomes_coverage")
    print()
    for path in written:
        try:
            print(f"wrote {path.relative_to(ROOT)}")
        except ValueError:
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
