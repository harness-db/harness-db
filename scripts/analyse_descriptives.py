#!/usr/bin/env python
"""Descriptive synthesis, under-reporting and convergence-over-time for the coded corpus
(Phase 7, plan tasks 47 and 50; RQ1 "what do harnesses look like", RQ4 "what do they not say").

WHY this script exists, and why each number is reported the way it is
--------------------------------------------------------------------
The corpus is a *stratified sample*, and every cell is in one of *three* states. Both facts
change what a descriptive table is allowed to say, so both are carried through every output
instead of being flattened at the start:

1. Three cell states, never collapsed (``data/systems.json``):

   ``coded``         a value with re-openable evidence (50.7% of the 47,614 cells)
   ``not_reported``  the sources were read and say nothing (48.9%). This is a FINDING, not a
                     missing datum: it is the quantity RQ4 counts.
   ``unresolved``    the coder could not settle it and claims nothing at all (0.3%).

   ``unresolved`` cells are excluded from EVERY denominator here - distributions, under-reporting
   rates and entropy alike - because they are the one state that asserts nothing about the
   sources. Folding them into ``not_reported`` would inflate the headline under-reporting rate;
   folding them into ``coded`` would invent values. They are counted and reported separately so
   the exclusion is visible (see the ``n_unresolved`` column of every table).

2. Two populations, hence two numbers for every share (``data/coding_frame.csv``):

   UNWEIGHTED describes *what was coded*: 1,253 released systems, over-representing the complete
   high-visibility stratum H (weight 1). It is the right number for "of the systems we read, how
   many did X" and for any statement about the coded set itself.

   WEIGHTED is the *estimate for the field*: each coded system carries its stratum weight
   (H = 1 complete; P ~ 4.55; O ~ 48.37) so the shares estimate the 6,504-system census that
   screening produced. It is the right number for "in the population of released harnesses,
   what share does X". Because stratum O is sampled at ~1/48, a single O system moves a weighted
   share by ~0.7 points, so weighted shares are noisier than unweighted ones; a design-based
   standard error (stratified, with a finite-population correction, so the complete H stratum
   contributes zero variance) is reported beside every weighted rate.

   Both columns appear in the same table, always. Where they disagree the disagreement IS the
   result: H-stratum systems are the well-documented ones, so weighted under-reporting is higher
   than unweighted for most dimensions, and reading only the unweighted column would understate
   how little the field as a whole reports.

   23 released systems carry weight 0: they were coded although they fell outside the drawn P/O
   samples (16 in O, 7 in P; none in the complete stratum H, by construction). They are in the
   unweighted columns and contribute nothing to the weighted ones, which
   is what design-based estimation requires (their inclusion probability is not the design one).
   The weighted totals therefore rest on 1,230 systems and sum to ~6,500, not 6,504; the script
   logs both.

Release year (for the year-resolved outputs) comes from ``data/systems_candidates.csv``
``release_date`` by default, NOT from the coded ``first_release_date`` dimension: the harvested
date covers 995/1,253 systems where the coded dimension covers 408 (it is ``not_reported`` for
67% of systems, and that missingness is correlated with exactly the poor documentation this
analysis is measuring, so using it would condition the time series on being well documented).
Where the harvested date is absent the coded date is used as a fallback (+6 systems), and
``--year-source coded`` runs the alternative. The two agree on the year for 388/402 systems where
both exist. The coverage is itself uneven and is logged on every run: every sampled P and O system
has a harvested date, but only 728 of 980 H systems do, so the year-resolved outputs lean slightly
more on the sampled strata than the corpus as a whole does. That is a reason to read the cohort
figures as cohorts and not as a census time series.

Convergence over time, and the two traps
----------------------------------------
Convergence is measured as the Shannon entropy (nats) of a dimension's value distribution among
the systems first released in a given year. For a multi-valued dimension the outcome is the whole
coded *value set* ("react+plan_execute" is one category, distinct from "react"), because that is
the design a system actually has; a normalised marginal over values would not be the entropy of
any single random variable.

Trap 1 - the plug-in entropy is biased DOWNWARD at small n, by about (k-1)/2n. The corpus thins
badly before 2023 (3 systems in 2022, 68 in 2023 against 385 in 2026), so early years look more
converged than they are. Two defences: the MILLER-MADOW estimator, H_MM = H_plugin + (k_hat-1)/2n
with k_hat the observed support, is reported beside the plug-in value; and any dimension-year cell
resting on fewer than ``--min-n`` systems (default 20) is SUPPRESSED - kept in the table so a
reader can see exactly what was withheld, but flagged ``suppressed=True``, given no bootstrap
interval, excluded from every convergence verdict, and drawn as a hatched cell labelled "n<20"
rather than plotted or silently dropped. 20 is chosen because the correction itself is then at most (7-1)/40 = 0.15 nats
for a single-valued dimension (the widest is 7 values), i.e. under 8% of that dimension's ln 7 =
1.95 nat range: a correction, not the estimate. Below 20 the correction becomes a large fraction
of the range and the plug-in value is mostly bias. A percentile bootstrap (systems resampled
within the dimension-year, fixed seed) gives an interval so "converged" is not read off two point
estimates.

Trap 2 - A FALLING ENTROPY WITH A RISING n IS NOT EVIDENCE OF CONVERGENCE. The year cohorts are
not a panel: no system is re-observed, and the 2026 cohort differs from the 2023 cohort in stratum
mix, source type (repo-only grey releases dominate the late years) and how much evidence was
available per system. Worse, entropy here is computed over *coded* cells only, so it conditions on
reporting, and reporting rates themselves move year to year - a dimension can lose entropy simply
because the systems that still report it became more homogeneous. The estimator bias runs the
other way (rising n removes downward bias, so it inflates late years and understates a real fall,
while a RISING entropy alongside a rising n is the pattern most easily faked by sample size), but
neither correction makes the cohorts exchangeable. Every convergence claim in the output therefore
carries n for both endpoints, and the tables are built so that no claim can be quoted without it.

Non-enum dimensions (2 integer, 1 date, 1 free-text string) get distributions but no entropy:
entropy over ``pinned_version`` or ``stars`` measures how many distinct systems were coded, not
how varied the field is. Integer dimensions are tabulated in data-derived quartile bins, the date
dimension by year, and the string dimension by coverage only. Nothing about the schema is
hardcoded: layers, dimensions, cardinality and value lists are read from ``schema/dimensions.json``
(1.0.0), so a schema change flows through.

Outputs
-------
Tables (``data/analysis/``):
  ``value_distributions.csv``          one row per dimension-value: unweighted and weighted share.
  ``under_reporting_by_dimension.csv`` per-dimension not_reported rate, both weightings, with a
                                       design SE, and a reproduction check against the existing
                                       ``data/coded/not_reported_by_dimension.csv``.
  ``under_reporting_layer_year.csv``   layer x release-year not_reported rates (long form).
  ``entropy_by_dimension_year.csv``    per dimension-year: n, k_hat, plug-in and Miller-Madow
                                       entropy, bootstrap CI, suppression flag.
  ``convergence_summary.csv``          first-to-last-usable-year change per dimension, with n at
                                       both ends and a bootstrap CI on the change.
  ``summary_one_screen.csv`` / ``.md`` the one-screen layer x dimension summary.

Figures (``paper/figures/``, SVG + PDF, Agg backend, captions in the functions' docstrings):
  ``descriptives_value_distributions``      small multiples, weighted bar + unweighted marker.
  ``descriptives_under_reporting_by_dimension``  dumbbell, unweighted vs weighted.
  ``descriptives_under_reporting_layer_year``    layer x year heatmap, sequential grey.
  ``descriptives_entropy_by_year``               dimension x year entropy heatmap.
  ``descriptives_entropy_trajectories``          the largest falls and rises, with n at each point.

Usage:
    python scripts/analyse_descriptives.py [--min-n 20] [--year-source candidates|coded]
                                           [--bootstrap 1000] [--no-figures] [--quiet]
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("analyse_descriptives")

#: Okabe-Ito, colourblind-safe categorical palette (8 hues, distinguishable in print and in
#: deuteranopia/protanopia simulation). Layers are also given distinct markers so colour is never
#: the only channel carrying the distinction.
OKABE_ITO = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442",
             "#999999", "#000000")
MARKERS = ("o", "s", "D", "^", "v", "P", "X", "*", "<")
LINESTYLES = ("-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2)))

STATE_CODED = "coded"
STATE_NOT_REPORTED = "not_reported"
STATE_UNRESOLVED = "unresolved"

csv.field_size_limit(10 ** 8)


# --------------------------------------------------------------------------------------- loading


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def cell_state(cell: dict) -> str:
    """Map one coded cell to exactly one of the three states.

    ``unresolved`` wins over ``not_reported`` (a cell flagged both ways claims nothing), and a
    cell with neither flag and no value is treated as unresolved rather than invented - it is
    logged, because the release should not contain one.
    """
    if cell.get("unresolved"):
        return STATE_UNRESOLVED
    if cell.get("not_reported"):
        return STATE_NOT_REPORTED
    if cell.get("value") is None or cell.get("value") == []:
        return STATE_UNRESOLVED
    return STATE_CODED


def cell_values(cell: dict) -> tuple:
    """The coded value(s) as a tuple (single-valued dimensions give a 1-tuple)."""
    v = cell.get("value")
    if v is None:
        return ()
    return tuple(v) if isinstance(v, list) else (v,)


def value_set_label(values: tuple) -> str:
    """The categorical outcome for entropy: the whole coded value set, order-insensitive."""
    return "+".join(sorted(str(x) for x in values))


def release_year(system: dict, harvested: dict[str, str], prefer: str) -> tuple[int | None, str]:
    """Release year plus the source it came from. See the module docstring for why harvested wins."""
    coded = system.get("coding", {}).get("first_release_date") or {}
    coded_v = coded.get("value") if cell_state(coded) == STATE_CODED else None
    options = [("candidates", harvested.get(system["id"])), ("coded", coded_v)]
    if prefer == "coded":
        options.reverse()
    for source, raw in options:
        text = str(raw or "").strip()
        if len(text) >= 4 and text[:4].isdigit():
            return int(text[:4]), source
    return None, "none"


def build_cells(systems: list[dict], dims: dict, frame: dict[str, dict], harvested: dict[str, str],
                year_source: str) -> pd.DataFrame:
    """One row per system x dimension: 1,253 x 38 cells with state, values, weight and year.

    Every later table is a group-by on this frame, so the three states and the two weightings are
    decided once, here, and cannot drift between outputs.
    """
    layer_names = {lay["id"]: lay["name"] for lay in dims["layers"]}
    specs = dims["dimensions"]
    rows = []
    odd = 0
    for system in systems:
        sid = system["id"]
        fr = frame.get(sid, {})
        weight = float(fr.get("weight") or 0.0)
        year, ysrc = release_year(system, harvested, year_source)
        coding = system.get("coding", {})
        for spec in specs:
            cell = coding.get(spec["key"]) or {}
            if not cell:
                odd += 1
            state = cell_state(cell)
            values = cell_values(cell) if state == STATE_CODED else ()
            rows.append({
                "system_id": sid,
                "stratum": fr.get("stratum", "?"),
                "weight": weight,
                "year": year,
                "year_source": ysrc,
                "dim_id": spec["id"],
                "key": spec["key"],
                "layer": spec["layer"],
                "layer_name": layer_names.get(spec["layer"], spec["layer"]),
                "dtype": spec["type"],
                "multi": bool(spec.get("multi")),
                "state": state,
                "values": values,
                "label": value_set_label(values) if values else None,
            })
    if odd:
        LOG.warning("%d cells were absent from a system's coding block and counted as unresolved", odd)
    df = pd.DataFrame(rows)
    df["year"] = df["year"].astype("Int64")
    return df


# ------------------------------------------------------------------------------------- estimators


def entropy_plugin(counts) -> float:
    """Plug-in (maximum-likelihood) Shannon entropy in nats.

    Exactly 0.0 for a single-valued sample and exactly ln(k) for a uniform sample over k values -
    the two anchors the tests pin. Biased DOWNWARD at small n; see ``entropy_miller_madow``.
    """
    c = np.asarray([x for x in np.asarray(counts, dtype=float).ravel() if x > 0])
    n = c.sum()
    if n <= 0:
        return float("nan")
    p = c / n
    return float(max(0.0, -np.sum(p * np.log(p))))


def entropy_miller_madow(counts) -> float:
    """Miller-Madow bias-corrected entropy: H_plugin + (k_hat - 1) / (2n), in nats.

    ``k_hat`` is the observed support size, so the correction vanishes for a single-valued sample
    (H stays 0.0) and shrinks as 1/n. It removes the leading term of the plug-in's downward bias
    only; it does not make cohorts of different size comparable.
    """
    c = np.asarray([x for x in np.asarray(counts, dtype=float).ravel() if x > 0])
    n = c.sum()
    if n <= 0:
        return float("nan")
    return entropy_plugin(c) + (len(c) - 1) / (2.0 * n)


def bootstrap_entropy_ci(counts, reps: int, rng: np.random.Generator,
                         alpha: float = 0.05) -> tuple[float, float]:
    """Percentile CI for the Miller-Madow entropy, resampling systems within the cell."""
    c = np.asarray([x for x in np.asarray(counts, dtype=float).ravel() if x > 0])
    n = int(c.sum())
    if reps <= 0 or n <= 1:
        return (float("nan"), float("nan"))
    p = c / c.sum()
    draws = rng.multinomial(n, p, size=reps)
    vals = np.array([entropy_miller_madow(row) for row in draws])
    return (float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2)))


def weighted_share(sub: pd.DataFrame, flag: pd.Series, strata_sizes: dict[str, float]
                   ) -> tuple[float, float, float]:
    """Weighted share of ``flag`` over ``sub``, its design SE, and the weight base.

    The estimator is the stratified ratio Sum(w*flag)/Sum(w) over the rows given (one row per
    system). The SE is the stratified-SRS standard error of a proportion with a
    finite-population correction,

        Var = Sum_h (N_h/N)^2 (1 - n_h/N_h) p_h(1-p_h)/(n_h - 1),

    so the COMPLETE stratum H (n_h = N_h) contributes exactly zero variance, which is the point of
    coding it exhaustively. It ignores the (small) extra variance from treating N_h as known and
    from the 4 frame systems that did not reach the release; it is a design SE, not a model SE.
    """
    w = sub["weight"].to_numpy(dtype=float)
    f = flag.to_numpy(dtype=float)
    base = float(w.sum())
    if base <= 0:
        return (float("nan"), float("nan"), 0.0)
    rate = float((w * f).sum() / base)
    var = 0.0
    total_N = sum(strata_sizes.values())
    for stratum, N_h in strata_sizes.items():
        mask = (sub["stratum"].to_numpy() == stratum) & (w > 0)
        n_h = int(mask.sum())
        if n_h < 2 or N_h <= 0:
            continue
        p_h = float(f[mask].mean())
        fpc = max(0.0, 1.0 - n_h / float(N_h))
        var += (N_h / total_N) ** 2 * fpc * p_h * (1 - p_h) / (n_h - 1)
    return (rate, float(math.sqrt(var)), base)


# ----------------------------------------------------------------------------------------- tables


def _numeric_bin_labels(values: list[float]) -> dict[float, str]:
    """Quartile bins for an integer dimension, labelled from the data (no magic cut points)."""
    arr = np.asarray(sorted(values), dtype=float)
    edges = sorted({float(np.quantile(arr, q)) for q in (0.0, 0.25, 0.5, 0.75, 1.0)})
    if len(edges) < 2:
        return {v: f"{int(v)}" for v in arr}
    out: dict[float, str] = {}
    for v in arr:
        idx = int(np.searchsorted(edges[1:-1], v, side="right")) if len(edges) > 2 else 0
        lo = edges[idx]
        hi = edges[idx + 1] if idx + 1 < len(edges) else edges[-1]
        out[v] = f"{int(lo)}-{int(hi)}" if hi > lo else f"{int(lo)}"
    return out


def distribution_labels(cells: pd.DataFrame, dims: dict) -> pd.DataFrame:
    """Add a ``dist_label`` column: the value(s) each coded cell contributes to its distribution.

    enum      one row per coded value (multi-valued dimensions contribute several, so their shares
              sum above 1 and the table says so in ``multi``).
    integer   data-derived quartile bins - the raw values are near-unique per system.
    date      the year.
    string    not tabulated (free text); coverage only.
    """
    cells = cells.copy()
    cells["dist_label"] = [[] for _ in range(len(cells))]
    for spec in dims["dimensions"]:
        mask = (cells["key"] == spec["key"]) & (cells["state"] == STATE_CODED)
        if not mask.any():
            continue
        if spec["type"] == "enum":
            labels = [[str(x) for x in v] for v in cells.loc[mask, "values"]]
        elif spec["type"] == "integer":
            raw = [float(v[0]) for v in cells.loc[mask, "values"]]
            binmap = _numeric_bin_labels(raw)
            labels = [[binmap[x]] for x in raw]
        elif spec["type"] == "date":
            labels = [[str(v[0])[:4]] for v in cells.loc[mask, "values"]]
        else:
            labels = [["(free text: not tabulated)"] for _ in range(int(mask.sum()))]
        cells.loc[mask, "dist_label"] = pd.Series(labels, index=cells.index[mask]).values
    return cells


def value_distributions(cells: pd.DataFrame, dims: dict, strata_sizes: dict[str, float]
                        ) -> pd.DataFrame:
    """Per dimension-value shares, unweighted (what was coded) and weighted (the field estimate).

    Denominator for both is the systems whose cell is CODED for that dimension: ``not_reported``
    systems are excluded from the share of values (they are the subject of the under-reporting
    table instead) and ``unresolved`` systems are excluded from every base. For multi-valued
    dimensions the denominator is still systems, so shares are "share of systems that use X" and
    sum above 1.
    """
    labelled = distribution_labels(cells, dims)
    order = {spec["key"]: i for i, spec in enumerate(dims["dimensions"])}
    value_order = {spec["key"]: {v: i for i, v in enumerate(spec.get("values") or [])}
                   for spec in dims["dimensions"]}
    rows = []
    for key, grp in labelled.groupby("key", sort=False):
        spec = next(s for s in dims["dimensions"] if s["key"] == key)
        coded = grp[grp["state"] == STATE_CODED]
        n_base = len(coded)
        w_base = float(coded["weight"].sum())
        n_nr = int((grp["state"] == STATE_NOT_REPORTED).sum())
        n_un = int((grp["state"] == STATE_UNRESOLVED).sum())
        seen: dict[str, list[int]] = {}
        for idx, labels in zip(coded.index, coded["dist_label"]):
            for lab in labels:
                seen.setdefault(lab, []).append(idx)
        declared = list(value_order.get(key) or {})
        labels_all = declared + [lab for lab in seen if lab not in declared] if spec["type"] == "enum" \
            else sorted(seen)
        for lab in labels_all:
            idxs = seen.get(lab, [])
            sub = coded.loc[idxs]
            flag = pd.Series(1.0, index=coded.index)
            flag.loc[:] = 0.0
            flag.loc[idxs] = 1.0
            w_rate, w_se, _ = weighted_share(coded, flag, strata_sizes)
            rows.append({
                "layer": spec["layer"], "layer_name": grp["layer_name"].iloc[0],
                "dim_id": spec["id"], "key": key, "type": spec["type"],
                "multi": bool(spec.get("multi")), "value": lab,
                "in_schema": lab in (value_order.get(key) or {}),
                "n_systems": len(idxs), "share_unweighted": len(idxs) / n_base if n_base else float("nan"),
                "weight_systems": float(sub["weight"].sum()),
                "share_weighted": w_rate, "se_weighted": w_se,
                "n_base_coded": n_base, "weight_base_coded": w_base,
                "n_not_reported": n_nr, "n_unresolved": n_un,
            })
    out = pd.DataFrame(rows)
    out["_d"] = out["key"].map(order)
    out["_v"] = [value_order.get(k, {}).get(v, 10 ** 6) for k, v in zip(out["key"], out["value"])]
    out = out.sort_values(["_d", "_v", "value"]).drop(columns=["_d", "_v"]).reset_index(drop=True)
    return out


def under_reporting_by_dimension(cells: pd.DataFrame, strata_sizes: dict[str, float]) -> pd.DataFrame:
    """Per-dimension ``not_reported`` rate over the non-unresolved cells, both weightings."""
    rows = []
    for key, grp in cells.groupby("key", sort=False):
        base = grp[grp["state"] != STATE_UNRESOLVED]
        flag = (base["state"] == STATE_NOT_REPORTED).astype(float)
        w_rate, w_se, w_base = weighted_share(base, flag, strata_sizes)
        rows.append({
            "layer": grp["layer"].iloc[0], "layer_name": grp["layer_name"].iloc[0],
            "dim_id": grp["dim_id"].iloc[0], "key": key,
            "n_cells": len(grp), "n_unresolved": int((grp["state"] == STATE_UNRESOLVED).sum()),
            "n_base": len(base), "n_coded": int((base["state"] == STATE_CODED).sum()),
            "n_not_reported": int(flag.sum()),
            "rate_unweighted": float(flag.mean()) if len(base) else float("nan"),
            "weight_base": w_base, "weight_not_reported": float((base["weight"] * flag).sum()),
            "rate_weighted": w_rate, "se_weighted": w_se,
        })
    out = pd.DataFrame(rows)
    out["weighted_minus_unweighted"] = out["rate_weighted"] - out["rate_unweighted"]
    return out.sort_values("rate_weighted", ascending=False).reset_index(drop=True)


def check_against_reference(table: pd.DataFrame, reference: Path, tol: float = 5e-4) -> list[str]:
    """Reproduce ``data/coded/not_reported_by_dimension.csv`` and report every disagreement.

    The existing table is a prior artefact of the coding phase, not an authority: it is
    recomputed from ``data/systems.json`` here and only the differences are reported.
    """
    if not reference.exists():
        LOG.warning("reference table %s not found; reproduction check skipped", reference)
        return []
    ref = {r["dimension"]: r for r in read_csv_rows(reference)}
    problems = []
    ours = table.set_index("key")
    for key, row in ref.items():
        if key not in ours.index:
            problems.append(f"{key}: in reference, absent from recomputed table")
            continue
        got = ours.loc[key]
        for col, ref_col in (("n_base", "n"), ("n_not_reported", "not_reported"),
                             ("rate_unweighted", "rate"), ("rate_weighted", "weighted_rate")):
            want = float(row[ref_col])
            have = float(got[col])
            if abs(have - want) > (tol if "rate" in ref_col else 0.5):
                problems.append(f"{key}.{ref_col}: reference {want} vs recomputed {have:.6g}")
    for key in set(ours.index) - set(ref):
        problems.append(f"{key}: recomputed but missing from the reference table")
    return problems


def under_reporting_layer_year(cells: pd.DataFrame, strata_sizes: dict[str, float], min_n: int
                               ) -> pd.DataFrame:
    """Layer x release-year ``not_reported`` rate, long form, with the systems behind each cell.

    A cell resting on fewer than ``min_n`` systems is flagged ``suppressed`` (the estimate is kept
    in the table so a reader can see what was withheld, and the figure hatches it).
    """
    rows = []
    for (layer, year), grp in cells.groupby(["layer", "year"], dropna=False, sort=True):
        base = grp[grp["state"] != STATE_UNRESOLVED]
        if base.empty:
            continue
        flag = (base["state"] == STATE_NOT_REPORTED).astype(float)
        w_rate, w_se, w_base = weighted_share(base, flag, strata_sizes)
        n_systems = int(base["system_id"].nunique())
        rows.append({
            "layer": layer, "layer_name": grp["layer_name"].iloc[0],
            "year": (int(year) if pd.notna(year) else pd.NA),
            "n_systems": n_systems, "n_base_cells": len(base),
            "n_not_reported": int(flag.sum()),
            "rate_unweighted": float(flag.mean()), "rate_weighted": w_rate, "se_weighted": w_se,
            "weight_base": w_base, "suppressed": n_systems < min_n,
        })
    out = pd.DataFrame(rows)
    out["year"] = out["year"].astype("Int64")
    return out.sort_values(["layer", "year"], na_position="last").reset_index(drop=True)


def entropy_by_dimension_year(cells: pd.DataFrame, dims: dict, min_n: int, reps: int,
                              seed: int) -> pd.DataFrame:
    """Entropy of each enum dimension's value-set distribution per release year.

    Only enum dimensions: entropy over ``stars``, ``tool_count``, ``pinned_version`` or a date
    counts distinct systems, not design diversity (see the module docstring).
    """
    rng = np.random.default_rng(seed)
    enum_keys = [s["key"] for s in dims["dimensions"] if s["type"] == "enum"]
    k_max = {s["key"]: len(s.get("values") or []) for s in dims["dimensions"]}
    rows = []
    coded = cells[(cells["state"] == STATE_CODED) & cells["key"].isin(enum_keys) & cells["year"].notna()]
    for (key, year), grp in coded.groupby(["key", "year"], sort=True):
        counts = list(Counter(grp["label"]).values())
        n = int(sum(counts))
        k_hat = len(counts)
        h = entropy_plugin(counts)
        h_mm = entropy_miller_madow(counts)
        lo, hi = bootstrap_entropy_ci(counts, reps if n >= min_n else 0, rng)
        rows.append({
            "layer": grp["layer"].iloc[0], "dim_id": grp["dim_id"].iloc[0], "key": key,
            "multi": bool(grp["multi"].iloc[0]), "year": int(year),
            "n_systems": n, "k_observed": k_hat, "k_schema_values": k_max.get(key),
            "h_plugin_nats": h, "h_miller_madow_nats": h_mm,
            "mm_correction_nats": h_mm - h,
            "h_ci_lo": lo, "h_ci_hi": hi,
            "max_possible_nats": math.log(k_hat) if k_hat else float("nan"),
            "suppressed": n < min_n,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    order = {s["key"]: i for i, s in enumerate(dims["dimensions"])}
    out["_d"] = out["key"].map(order)
    return out.sort_values(["_d", "year"]).drop(columns="_d").reset_index(drop=True)


def convergence_summary(entropy: pd.DataFrame, delta_threshold: float, reps: int, seed: int,
                        cells: pd.DataFrame | None = None) -> pd.DataFrame:
    """First-to-last usable year change in Miller-Madow entropy, with n at both ends.

    ``verdict`` is "converged" / "diversified" only when the change exceeds
    ``delta_threshold`` nats (default 0.15, i.e. at least the largest Miller-Madow correction that
    survives the n>=20 suppression rule for a single-valued dimension) AND the bootstrap interval
    for the change excludes 0. Everything else is "stable (within estimator noise)". n_first and
    n_last are carried so no verdict can be quoted without the sample behind it.
    """
    rng = np.random.default_rng(seed + 1)
    rows = []
    if entropy.empty:
        return pd.DataFrame(rows)
    usable = entropy[~entropy["suppressed"]]
    labels = None
    if cells is not None:
        coded = cells[cells["state"] == STATE_CODED]
        labels = {(k, int(y)): list(Counter(g["label"]).values())
                  for (k, y), g in coded.groupby(["key", "year"], sort=False) if pd.notna(y)}
    for key, grp in usable.groupby("key", sort=False):
        grp = grp.sort_values("year")
        if len(grp) < 2:
            continue
        first, last = grp.iloc[0], grp.iloc[-1]
        delta = float(last["h_miller_madow_nats"] - first["h_miller_madow_nats"])
        lo = hi = float("nan")
        if labels is not None and reps > 0:
            c0 = labels.get((key, int(first["year"])))
            c1 = labels.get((key, int(last["year"])))
            if c0 and c1:
                n0, n1 = int(sum(c0)), int(sum(c1))
                p0, p1 = np.array(c0) / n0, np.array(c1) / n1
                d0 = rng.multinomial(n0, p0, size=reps)
                d1 = rng.multinomial(n1, p1, size=reps)
                diffs = np.array([entropy_miller_madow(b) - entropy_miller_madow(a)
                                  for a, b in zip(d0, d1)])
                lo, hi = float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))
        significant = not (math.isnan(lo) or math.isnan(hi)) and (lo > 0 or hi < 0)
        if delta <= -delta_threshold and (significant or math.isnan(lo)):
            verdict = "converged"
        elif delta >= delta_threshold and (significant or math.isnan(lo)):
            verdict = "diversified"
        else:
            verdict = "stable (within estimator noise)"
        rows.append({
            "layer": first["layer"], "dim_id": first["dim_id"], "key": key,
            "multi": bool(first["multi"]),
            "first_year": int(first["year"]), "last_year": int(last["year"]),
            "n_usable_years": len(grp),
            "n_first": int(first["n_systems"]), "n_last": int(last["n_systems"]),
            "k_first": int(first["k_observed"]), "k_last": int(last["k_observed"]),
            "h_first_nats": float(first["h_miller_madow_nats"]),
            "h_last_nats": float(last["h_miller_madow_nats"]),
            "delta_nats": delta, "delta_ci_lo": lo, "delta_ci_hi": hi,
            "ci_excludes_zero": significant, "verdict": verdict,
        })
    out = pd.DataFrame(rows)
    return out.sort_values("delta_nats").reset_index(drop=True) if not out.empty else out


def one_screen_summary(cells: pd.DataFrame, dists: pd.DataFrame, under: pd.DataFrame,
                       strata_sizes: dict[str, float], dims: dict) -> pd.DataFrame:
    """One screen: per layer and per dimension, the cell states, the modal value and the base n.

    ``modal_value`` is the most common coded value by WEIGHTED share (the field estimate) with the
    unweighted share beside it, because the two can pick different winners; ``n_systems_coded`` and
    ``n_systems_weight_bearing`` are the samples the estimate rests on - the second excludes the
    23 coded systems that carry weight 0.
    """
    order = {s["key"]: i for i, s in enumerate(dims["dimensions"])}
    layer_order = [lay["id"] for lay in dims["layers"]]
    rows = []

    def states(grp: pd.DataFrame) -> dict:
        n = len(grp)
        return {
            "n_cells": n,
            "share_coded": float((grp["state"] == STATE_CODED).mean()),
            "share_not_reported": float((grp["state"] == STATE_NOT_REPORTED).mean()),
            "share_unresolved": float((grp["state"] == STATE_UNRESOLVED).mean()),
        }

    for layer in layer_order:
        lgrp = cells[cells["layer"] == layer]
        if lgrp.empty:
            continue
        base = lgrp[lgrp["state"] != STATE_UNRESOLVED]
        w_rate, w_se, _ = weighted_share(base, (base["state"] == STATE_NOT_REPORTED).astype(float),
                                         strata_sizes)
        rows.append({
            "level": "layer", "layer": layer, "layer_name": lgrp["layer_name"].iloc[0],
            "dim_id": "", "key": f"({lgrp['key'].nunique()} dimensions)",
            **states(lgrp),
            "rate_not_reported_weighted": w_rate, "se_weighted": w_se,
            "modal_value": "", "modal_share_weighted": float("nan"),
            "modal_share_unweighted": float("nan"),
            "n_systems_coded": int(lgrp.loc[lgrp["state"] == STATE_CODED, "system_id"].nunique()),
            "n_systems_weight_bearing": int(lgrp.loc[(lgrp["state"] == STATE_CODED)
                                                     & (lgrp["weight"] > 0), "system_id"].nunique()),
        })
        for key in sorted(lgrp["key"].unique(), key=lambda k: order.get(k, 999)):
            dgrp = lgrp[lgrp["key"] == key]
            dd = dists[dists["key"] == key].sort_values("share_weighted", ascending=False)
            u = under[under["key"] == key].iloc[0]
            top = dd.iloc[0] if not dd.empty else None
            coded = dgrp[dgrp["state"] == STATE_CODED]
            rows.append({
                "level": "dimension", "layer": layer, "layer_name": dgrp["layer_name"].iloc[0],
                "dim_id": dgrp["dim_id"].iloc[0], "key": key,
                **states(dgrp),
                "rate_not_reported_weighted": float(u["rate_weighted"]),
                "se_weighted": float(u["se_weighted"]),
                "modal_value": "" if top is None else str(top["value"]),
                "modal_share_weighted": float("nan") if top is None else float(top["share_weighted"]),
                "modal_share_unweighted": float("nan") if top is None else float(top["share_unweighted"]),
                "n_systems_coded": len(coded),
                "n_systems_weight_bearing": int((coded["weight"] > 0).sum()),
            })
    return pd.DataFrame(rows)


def summary_markdown(summary: pd.DataFrame) -> str:
    """Render the one-screen summary as a markdown table (layer rows in bold)."""
    head = ("| level | layer | dimension | cells | coded | not_reported | unresolved | "
            "NR weighted | modal value (weighted share) | n coded | n weight-bearing |")
    lines = [head, "|" + "---|" * 11]
    for _, r in summary.iterrows():
        name = f"**{r['layer']} {r['layer_name']}**" if r["level"] == "layer" else r["layer"]
        dim = f"**{r['key']}**" if r["level"] == "layer" else f"{r['dim_id']} {r['key']}"
        modal = "" if not r["modal_value"] else f"{r['modal_value']} ({r['modal_share_weighted']:.0%})"
        lines.append(
            f"| {r['level']} | {name} | {dim} | {r['n_cells']} | {r['share_coded']:.1%} | "
            f"{r['share_not_reported']:.1%} | {r['share_unresolved']:.2%} | "
            f"{r['rate_not_reported_weighted']:.1%} +/- {r['se_weighted']:.1%} | {modal} | "
            f"{r['n_systems_coded']} | {r['n_systems_weight_bearing']} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------- figures


def _new_figure(*args, **kwargs):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8,
        "axes.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "figure.dpi": 150, "savefig.bbox": "tight",
    })
    return plt, plt.subplots(*args, **kwargs)


def save_figure(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("svg", "pdf"):
        p = stem.with_suffix(f".{ext}")
        fig.savefig(p, format=ext, bbox_inches="tight")
        paths.append(p)
    import matplotlib.pyplot as plt

    plt.close(fig)
    return paths


def fig_value_distributions(dists: pd.DataFrame, dims: dict, stem: Path, ncols: int = 4) -> list[Path]:
    """Figure: value distribution of every enum dimension, weighted and unweighted.

    Caption: Distribution of coded values for each of the categorical harness dimensions, one panel
    per dimension (layer and dimension id in the panel title). Bars give the WEIGHTED share of the
    6,504-system census (stratum weights: H = 1, P ~ 4.55, O ~ 48.37); open diamonds give the
    UNWEIGHTED share of the coded systems, which over-represents the exhaustively coded
    high-visibility stratum. Denominator is systems whose cell is coded for that dimension, so
    `not_reported` systems are excluded here and quantified in the under-reporting figure, and
    `unresolved` cells are excluded throughout; multi-valued dimensions (marked *) let a system
    carry several values, so their bars sum above 100%. Non-categorical dimensions (tool count,
    stars, first release date, pinned version) are tabulated in
    data/analysis/value_distributions.csv instead, because a share per distinct integer or string
    describes the sample, not the field.
    """
    enum = dists[dists["type"] == "enum"]
    keys = [s["key"] for s in dims["dimensions"] if s["type"] == "enum" and s["key"] in set(enum["key"])]
    nrows = math.ceil(len(keys) / ncols)
    _plt, (fig, axes) = _new_figure(nrows, ncols, figsize=(3.1 * ncols, 1.30 * nrows + 1.2))
    axes = np.atleast_1d(axes).ravel()
    for ax, key in zip(axes, keys):
        sub = enum[enum["key"] == key]
        sub = sub[(sub["n_systems"] > 0) | sub["in_schema"]]
        y = np.arange(len(sub))[::-1]
        ax.barh(y, sub["share_weighted"] * 100, height=0.62, color=OKABE_ITO[0], alpha=0.85,
                label="weighted (census estimate)")
        ax.plot(sub["share_unweighted"] * 100, y, linestyle="none", marker="D", markersize=3.4,
                markerfacecolor="none", markeredgecolor="#000000", markeredgewidth=0.8,
                label="unweighted (coded set)")
        ax.set_yticks(y)
        ax.set_yticklabels([str(v)[:24] for v in sub["value"]],
                           fontsize=6.6 if len(sub) > 5 else 7.2)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        star = " *" if bool(sub["multi"].iloc[0]) else ""
        ax.set_title(f"{sub['dim_id'].iloc[0]} {key}{star}  (n={int(sub['n_base_coded'].iloc[0])})",
                     loc="left")
        ax.grid(axis="x", color="#dddddd", linewidth=0.5)
        ax.set_axisbelow(True)
    for ax in axes[len(keys):]:
        ax.axis("off")
    for ax in axes[max(0, len(keys) - ncols):len(keys)]:
        ax.set_xlabel("share of systems with a coded value (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, -0.012))
    fig.suptitle("Coded value distributions, weighted to the census and unweighted "
                 "(* = multi-valued dimension; shares may exceed 100%)", y=1.002, fontsize=9)
    fig.tight_layout()
    return save_figure(fig, stem)


def fig_under_reporting_by_dimension(under: pd.DataFrame, stem: Path) -> list[Path]:
    """Figure: per-dimension not_reported rate, unweighted vs weighted.

    Caption: Share of systems for which each dimension is `not_reported` - the sources were read
    and say nothing - over all cells except `unresolved` ones. Each dimension is a row, sorted by
    the weighted rate; the filled circle is the WEIGHTED estimate for the 6,504-system census with
    a design-based 95% interval (stratified, finite-population corrected, so the complete H
    stratum adds no variance), the open square is the UNWEIGHTED rate over the 1,253 coded
    systems, and the connecting line is the gap between what was coded and what the field looks
    like. Colour and marker together identify the layer. The ordering makes the pattern legible:
    what a harness DOES (control loop, meta) is documented; how it is BOUNDED (sandbox, budget,
    observability) is not.
    """
    layers = list(dict.fromkeys(under.sort_values("rate_weighted")["layer"]))
    colour = {lay: OKABE_ITO[i % len(OKABE_ITO)] for i, lay in enumerate(sorted(layers))}
    marker = {lay: MARKERS[i % len(MARKERS)] for i, lay in enumerate(sorted(layers))}
    d = under.sort_values("rate_weighted", ascending=True).reset_index(drop=True)
    plt, (fig, ax) = _new_figure(figsize=(7.2, 9.0))
    for i, r in d.iterrows():
        c = colour[r["layer"]]
        ax.plot([r["rate_unweighted"] * 100, r["rate_weighted"] * 100], [i, i], color=c,
                linewidth=1.1, alpha=0.7, zorder=1)
        ax.errorbar(r["rate_weighted"] * 100, i, xerr=1.96 * r["se_weighted"] * 100, fmt="none",
                    ecolor=c, elinewidth=0.9, capsize=2.0, zorder=2)
        ax.plot(r["rate_weighted"] * 100, i, marker=marker[r["layer"]], markersize=5, color=c,
                zorder=3)
        ax.plot(r["rate_unweighted"] * 100, i, marker="s", markersize=4.2, markerfacecolor="white",
                markeredgecolor=c, markeredgewidth=0.9, zorder=3)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels([f"{r['dim_id']} {r['key']}  ({r['layer']})" for _, r in d.iterrows()])
    ax.set_ylim(-0.8, len(d) - 0.2)
    ax.set_xlim(0, 100)
    ax.set_xlabel("systems for which the dimension is not reported (%)")
    ax.set_ylabel("dimension (layer in brackets), sorted by the weighted rate")
    ax.grid(axis="x", color="#dddddd", linewidth=0.5)
    ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker=marker[lay], color=colour[lay], linestyle="none",
                          markersize=5, label=lay) for lay in sorted(layers)]
    handles += [plt.Line2D([], [], marker="s", color="#444444", linestyle="none", markersize=4.2,
                           markerfacecolor="white", label="unweighted (coded set)"),
                plt.Line2D([], [], marker="o", color="#444444", linestyle="none", markersize=5,
                           label="weighted (census), 95% design CI")]
    ax.legend(handles=handles, loc="lower right", ncol=2, frameon=False)
    ax.set_title("Under-reporting by dimension: what the sources do not say", loc="left")
    fig.tight_layout()
    return save_figure(fig, stem)


def fig_under_reporting_layer_year(ly: pd.DataFrame, under: pd.DataFrame, stem: Path,
                                   min_n: int) -> list[Path]:
    """Figure: layer x release-year under-reporting heatmap.

    Caption: Weighted share of `not_reported` cells by harness layer (rows) and year of first
    release (columns). Rows are ordered by the layer's overall weighted rate - best-documented at
    the top - rather than alphabetically, so the gradient from what a harness does to how it is
    bounded is readable off the figure. Column headers give the number of coded systems in that
    release cohort; cells resting on fewer than the suppression threshold are hatched and not
    estimated. Sequential single-hue map (prints legibly in greyscale); annotations are the
    weighted percentage. `unresolved` cells are excluded from every denominator. Years are cohorts,
    not a panel: no system appears in two columns.
    """
    order = under.groupby("layer")["rate_weighted"].mean().sort_values().index.tolist()
    years = sorted([int(y) for y in ly["year"].dropna().unique()])
    names = dict(zip(ly["layer"], ly["layer_name"]))
    mat = np.full((len(order), len(years)), np.nan)
    ann = np.empty(mat.shape, dtype=object)
    supp = np.zeros(mat.shape, dtype=bool)
    nsys = {y: 0 for y in years}
    for _, r in ly.iterrows():
        if pd.isna(r["year"]):
            continue
        i, j = order.index(r["layer"]), years.index(int(r["year"]))
        nsys[int(r["year"])] = max(nsys[int(r["year"])], int(r["n_systems"]))
        if r["suppressed"]:
            supp[i, j] = True
            ann[i, j] = f"n<{min_n}"
        else:
            mat[i, j] = r["rate_weighted"] * 100
            ann[i, j] = f"{r['rate_weighted'] * 100:.0f}%"
    plt, (fig, ax) = _new_figure(figsize=(1.05 * len(years) + 3.6, 0.46 * len(order) + 2.0))
    im = ax.imshow(mat, cmap="Greys", vmin=0, vmax=100, aspect="auto")
    for i in range(len(order)):
        for j in range(len(years)):
            if supp[i, j]:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#f2f2f2",
                                           edgecolor="#bbbbbb", hatch="////", linewidth=0.4))
            if ann[i, j]:
                val = mat[i, j]
                colour = "white" if (not np.isnan(val) and val > 55) else "#111111"
                ax.text(j, i, ann[i, j], ha="center", va="center", color=colour, fontsize=7)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([f"{y}\n(n={nsys[y]})" for y in years])
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{lay}  {names.get(lay, '')}" for lay in order])
    ax.set_xlabel("year of first release (cohort)")
    ax.set_ylabel("layer, ordered by overall weighted under-reporting")
    ax.set_title("Under-reporting by layer and release year (weighted to the census)", loc="left")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("cells not reported (%)")
    ax.set_xticks(np.arange(-0.5, len(years), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(order), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8)
    ax.tick_params(which="minor", length=0)
    fig.tight_layout()
    return save_figure(fig, stem)


def fig_entropy_by_year(ent: pd.DataFrame, dims: dict, stem: Path, min_n: int) -> list[Path]:
    """Figure: dimension x year entropy heatmap (convergence over time).

    Caption: Miller-Madow bias-corrected Shannon entropy (nats) of each categorical dimension's
    coded value distribution, by year of first release. For multi-valued dimensions the outcome is
    the whole coded value set, so their ceiling is higher than ln(number of schema values). Cells
    resting on fewer than the suppression threshold of systems are hatched and not estimated,
    because the plug-in estimator's downward bias, about (k-1)/2n, is then a large fraction of the
    range. A cell marked with a dash had no coded system at all in that cohort, which is a different
    thing from a suppressed estimate. Annotations are the entropy; the n behind each cell is in
    data/analysis/entropy_by_dimension_year.csv. Sequential map, dimensions grouped by layer.
    A fall along a row is NOT by itself evidence of convergence: the cohorts differ in composition
    and in how much they report, and entropy is computed over coded cells only.
    """
    keys = [s["key"] for s in dims["dimensions"] if s["key"] in set(ent["key"])]
    years = sorted(ent["year"].unique())
    mat = np.full((len(keys), len(years)), np.nan)
    ann = np.empty(mat.shape, dtype=object)
    supp = np.zeros(mat.shape, dtype=bool)
    for _, r in ent.iterrows():
        i, j = keys.index(r["key"]), years.index(r["year"])
        if r["suppressed"]:
            supp[i, j] = True
            ann[i, j] = f"n<{min_n}"
        else:
            mat[i, j] = r["h_miller_madow_nats"]
            ann[i, j] = f"{r['h_miller_madow_nats']:.2f}"
    vmax = float(np.nanmax(mat)) if np.isfinite(mat).any() else 1.0
    plt, (fig, ax) = _new_figure(figsize=(1.1 * len(years) + 4.2, 0.30 * len(keys) + 1.8))
    im = ax.imshow(mat, cmap="cividis", vmin=0, vmax=vmax, aspect="auto")
    mid = vmax * 0.55
    for i in range(len(keys)):
        for j in range(len(years)):
            if supp[i, j]:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#f2f2f2",
                                           edgecolor="#bbbbbb", hatch="////", linewidth=0.4))
            elif ann[i, j] is None:  # no coded system in that cohort at all
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="white",
                                           edgecolor="#cccccc", linewidth=0.4))
                ax.text(j, i, "–", ha="center", va="center", color="#777777", fontsize=7)
            if ann[i, j]:
                val = mat[i, j]
                colour = "#111111" if (np.isnan(val) or val > mid) else "white"
                ax.text(j, i, ann[i, j], ha="center", va="center", color=colour, fontsize=6.5)
    ids = dict(zip(ent["key"], ent["dim_id"]))
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([f"{ids[k]} {k}" for k in keys])
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlabel("year of first release (cohort)")
    ax.set_ylabel("dimension (grouped by layer)")
    ax.set_title("Value-distribution entropy by release year (Miller-Madow, nats)", loc="left")
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("entropy (nats)")
    ax.set_xticks(np.arange(-0.5, len(years), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(keys), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.7)
    ax.tick_params(which="minor", length=0)
    fig.tight_layout()
    return save_figure(fig, stem)


def fig_entropy_trajectories(ent: pd.DataFrame, conv: pd.DataFrame, stem: Path, top: int = 6
                             ) -> list[Path]:
    """Figure: the dimensions that lost and gained the most entropy, with n at every point.

    Caption: Entropy trajectories (Miller-Madow, nats) for the categorical dimensions with the
    largest fall (left) and largest rise (right) between their first and last year that clears the
    suppression threshold. Shaded bands are percentile bootstrap 95% intervals; the small number
    beside each marker is the number of systems behind that point, which is the only way to read
    the figure honestly - the cohorts grow by an order of magnitude across the window, and a fall
    against a rising n is a change in the coded cohort as much as a change in the field. Colour,
    marker and line style are redundant so the panels survive greyscale printing.
    """
    usable = ent[~ent["suppressed"]]
    _plt, (fig, axes) = _new_figure(1, 2, figsize=(10.5, 4.6), sharey=True)
    panels = [("largest fall in entropy", conv.head(top)),
              ("largest rise in entropy", conv.tail(top).iloc[::-1])]
    for ax, (title, sel) in zip(axes, panels):
        for i, (_, r) in enumerate(sel.iterrows()):
            g = usable[usable["key"] == r["key"]].sort_values("year")
            c = OKABE_ITO[i % len(OKABE_ITO)]
            ax.plot(g["year"], g["h_miller_madow_nats"], marker=MARKERS[i % len(MARKERS)],
                    linestyle=LINESTYLES[i % len(LINESTYLES)], color=c, linewidth=1.3,
                    markersize=4.2, label=f"{r['dim_id']} {r['key']} ({r['verdict'].split(' ')[0]})")
            ax.fill_between(g["year"], g["h_ci_lo"], g["h_ci_hi"], color=c, alpha=0.12,
                            linewidth=0)
            for _, p in g.iterrows():
                ax.annotate(f"{int(p['n_systems'])}", (p["year"], p["h_miller_madow_nats"]),
                            textcoords="offset points", xytext=(3, 4), fontsize=5.8, color=c)
        ax.set_title(title, loc="left")
        ax.set_xlabel("year of first release (cohort); label = n systems")
        ax.grid(color="#dddddd", linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_xticks(sorted(usable["year"].unique()))
        ax.legend(loc="upper left", frameon=False, fontsize=6.5)
    axes[0].set_ylabel("entropy of the coded value distribution (nats)")
    fig.suptitle("Convergence and diversification, 95% bootstrap bands, n annotated", fontsize=9)
    fig.tight_layout()
    return save_figure(fig, stem)


# ------------------------------------------------------------------------------------------- main


def strata_sizes_from_frame(frame_rows: list[dict[str, str]]) -> dict[str, float]:
    """Census size of each stratum (N_h) - the population the weights scale up to."""
    return {k: float(v) for k, v in Counter(r["stratum"] for r in frame_rows).items()}


def run(args) -> int:
    dims = load_json(Path(args.dimensions))
    systems = load_json(Path(args.systems))
    frame_rows = read_csv_rows(Path(args.frame))
    frame = {r["system_id"]: r for r in frame_rows}
    harvested = {}
    cand_path = Path(args.candidates)
    if cand_path.exists():
        harvested = {r["system_id"]: r.get("release_date", "") for r in read_csv_rows(cand_path)}
    else:
        LOG.warning("%s not found; falling back to the coded first_release_date only", cand_path)
    strata = strata_sizes_from_frame(frame_rows)
    LOG.info("schema %s: %d dimensions in %d layers", dims.get("schema_version"),
             len(dims["dimensions"]), len(dims["layers"]))
    LOG.info("census strata (N_h): %s -> %d systems",
             {k: int(v) for k, v in sorted(strata.items())}, int(sum(strata.values())))

    cells = build_cells(systems, dims, frame, harvested, args.year_source)
    states = cells["state"].value_counts()
    total = len(cells)
    LOG.info("%d systems x %d dimensions = %d cells: coded %d (%.1f%%), not_reported %d (%.1f%%), "
             "unresolved %d (%.2f%%; excluded from every denominator)",
             cells["system_id"].nunique(), cells["key"].nunique(), total,
             states.get(STATE_CODED, 0), 100 * states.get(STATE_CODED, 0) / total,
             states.get(STATE_NOT_REPORTED, 0), 100 * states.get(STATE_NOT_REPORTED, 0) / total,
             states.get(STATE_UNRESOLVED, 0), 100 * states.get(STATE_UNRESOLVED, 0) / total)
    per_system = cells.drop_duplicates("system_id")
    zero = per_system[per_system["weight"] <= 0]
    LOG.info("weighted estimates rest on %d of %d coded systems (sum of weights %.1f of census "
             "%d); %d coded systems carry weight 0 (coded outside the drawn sample) and enter the "
             "unweighted columns only",
             len(per_system) - len(zero), len(per_system), per_system["weight"].sum(),
             int(sum(strata.values())), len(zero))
    yr = per_system["year_source"].value_counts()
    LOG.info("release year from %s: %s; %d systems have no year and are excluded from the "
             "year-resolved outputs", args.year_source, dict(yr), int(per_system["year"].isna().sum()))

    tables = Path(args.tables)
    tables.mkdir(parents=True, exist_ok=True)
    dists = value_distributions(cells, dims, strata)
    under = under_reporting_by_dimension(cells, strata)
    problems = check_against_reference(under, Path(args.reference))
    if problems:
        for p in problems:
            LOG.warning("reference disagreement: %s", p)
    elif Path(args.reference).exists():
        LOG.info("reproduction check: recomputed rates match %s on every dimension",
                 Path(args.reference).name)
    ly = under_reporting_layer_year(cells, strata, args.min_n)
    ent = entropy_by_dimension_year(cells, dims, args.min_n, args.bootstrap, args.seed)
    conv = convergence_summary(ent, args.delta_threshold, args.bootstrap, args.seed, cells)
    summary = one_screen_summary(cells, dists, under, strata, dims)

    written: list[Path] = []
    for name, frame_out in (("value_distributions.csv", dists),
                            ("under_reporting_by_dimension.csv", under),
                            ("under_reporting_layer_year.csv", ly),
                            ("entropy_by_dimension_year.csv", ent),
                            ("convergence_summary.csv", conv),
                            ("summary_one_screen.csv", summary)):
        path = tables / name
        frame_out.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        written.append(path)
    md = tables / "summary_one_screen.md"
    md.write_text(summary_markdown(summary), encoding="utf-8")
    written.append(md)

    if not ent.empty:
        n_supp = int(ent["suppressed"].sum())
        LOG.info("entropy: %d dimension-year cells, %d suppressed at n<%d; largest retained "
                 "Miller-Madow correction %.3f nats",
                 len(ent), n_supp, args.min_n,
                 float(ent.loc[~ent["suppressed"], "mm_correction_nats"].max()))

    if not args.no_figures:
        figures = Path(args.figures)
        written += fig_value_distributions(dists, dims, figures / "descriptives_value_distributions")
        written += fig_under_reporting_by_dimension(
            under, figures / "descriptives_under_reporting_by_dimension")
        written += fig_under_reporting_layer_year(
            ly, under, figures / "descriptives_under_reporting_layer_year", args.min_n)
        if not ent.empty:
            written += fig_entropy_by_year(ent, dims, figures / "descriptives_entropy_by_year",
                                           args.min_n)
        if not conv.empty:
            written += fig_entropy_trajectories(ent, conv,
                                                figures / "descriptives_entropy_trajectories")

    for path in written:
        LOG.info("wrote %s (%d bytes)", path, path.stat().st_size)
    if args.print_summary:
        print(summary_markdown(summary))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--systems", default=str(REPO / "data/systems.json"))
    p.add_argument("--dimensions", default=str(REPO / "schema/dimensions.json"))
    p.add_argument("--frame", default=str(REPO / "data/coding_frame.csv"),
                   help="per-system stratum and weight")
    p.add_argument("--candidates", default=str(REPO / "data/systems_candidates.csv"),
                   help="harvested release_date per system")
    p.add_argument("--reference", default=str(REPO / "data/coded/not_reported_by_dimension.csv"),
                   help="existing under-reporting table, recomputed and diffed (read-only)")
    p.add_argument("--tables", default=str(REPO / "data/analysis"))
    p.add_argument("--figures", default=str(REPO / "paper/figures"))
    p.add_argument("--year-source", choices=("candidates", "coded"), default="candidates",
                   help="which release date wins; the other is the fallback")
    p.add_argument("--min-n", type=int, default=20,
                   help="suppress a year cell resting on fewer systems than this (default 20; see "
                        "the module docstring for the justification)")
    p.add_argument("--delta-threshold", type=float, default=0.15,
                   help="nats of entropy change needed to call convergence or diversification")
    p.add_argument("--bootstrap", type=int, default=1000, help="bootstrap replicates (0 to skip)")
    p.add_argument("--seed", type=int, default=20260924)
    p.add_argument("--no-figures", action="store_true")
    p.add_argument("--print-summary", action="store_true",
                   help="print the one-screen summary table to stdout")
    p.add_argument("--quiet", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO,
                        format="%(levelname)s %(message)s")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
