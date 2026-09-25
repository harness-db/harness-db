#!/usr/bin/env python
"""Which harness design choices travel together, and are there design families? (Phase 7 task 48).

WHY THIS SCRIPT EXISTS
----------------------
The review codes 1,253 harnesses on 38 dimensions. Two synthesis questions follow: (1) do design
choices co-occur -- is a harness that isolates execution in a container also the kind of harness
that runs tests, keeps a plan object and traces its steps? and (2) does the corpus fall into a
small number of recognisable *design families*, or is it a continuum of ad-hoc combinations?
Both questions are answered here with categorical association statistics and hierarchical
clustering. No model calls: pandas/numpy/scipy/sklearn/matplotlib only.

THE MISSINGNESS TRAP (the reason this script is built the way it is)
-------------------------------------------------------------------
48.9% of the 47,614 coded cells are ``not_reported`` (NR): the sources were read and say nothing.
NR is *not* missing at random. Systems documented by a thin README are silent on many dimensions
at once, so NR co-occurs with NR across almost every pair of dimensions. If NR is treated as an
ordinary category, then every pair of dimensions looks strongly associated, because the
association is carried by *shared silence* rather than by *shared design*, and a clustering of the
same data separates well-documented systems from badly-documented ones while looking like it has
found design families.

Every association in this script is therefore computed BOTH ways and both are reported:

  (a) COMPLETE PAIRS ONLY -- only systems where *both* dimensions carry a value. This is the
      design signal. It rests on a smaller n, and the n is reported for every single pair, because
      a V of 0.5 on 41 systems and a V of 0.5 on 812 systems are not the same claim. THIS IS THE
      PRIMARY RESULT.
  (b) NR AS ITS OWN LEVEL -- ``«not_reported»`` is an extra level of every dimension. This
      measures DOCUMENTATION BEHAVIOUR, i.e. which dimensions tend to be documented together. It
      is reported as a contrast, never as evidence about design.

Pairs where the two treatments disagree (a significance flip at the same FDR threshold, or a
change in corrected V of at least ``--flip-delta``) are written to their own table, because that
disagreement is itself a finding: it marks the pairs whose apparent association is documentation
behaviour.

``unresolved`` cells (0.3%: the coder could not settle the value) are excluded everywhere, in both
treatments. They are neither a value nor a statement about the sources.

The clustering uses complete data only in the same sense: a Gower distance that averages over the
dimensions where *both* systems carry a value, so silence never makes two systems look alike.
And the reference (null) distribution for the clustering is built by permuting each dimension
independently *within its observed cells*, which preserves both the marginal distribution of every
dimension and the exact NR pattern of every system while destroying all cross-dimension
association. If the observed silhouette does not beat that null, the "families" are an artefact of
documentation and marginals, and the script says so.

METHOD DECISIONS (all stated, none hardcoded to a particular dimension)
----------------------------------------------------------------------
Everything -- dimension ids, keys, layers, types, ``multi`` flags, allowed values -- is read from
``schema/dimensions.json`` at runtime.

* ASSOCIATION STATISTIC. Cramer's V with the bias correction of Bergsma (2013, *Journal of the
  Korean Statistical Society* 42:323-328): phi2~ = max(0, phi2 - (r-1)(c-1)/(n-1)),
  r~ = r - (r-1)^2/(n-1), c~ = c - (c-1)^2/(n-1), V~ = sqrt(phi2~ / min(r~-1, c~-1)). Plain
  Cramer's V is inflated on sparse tables, and several dimensions here have many rarely used
  values (and, under the value-set treatment below, many rarely used combinations), so the plain
  statistic would manufacture structure. Both the corrected and the raw statistic are reported in
  every table. The corrected statistic is exactly 0 when the table is exactly independent and
  exactly 1 when the table is a permutation matrix, which is what the tests assert.

* MULTI-VALUED DIMENSIONS: VALUE-SET-AS-LEVEL (not one-hot). 15 of the 38 dimensions are
  ``multi: true``. Each system's set of selected values is sorted and joined into one composite
  level (``search_replace+unified_diff``). Reasons: (i) Cramer's V needs one categorical variable
  per dimension, so one-hot would replace the 38x38 matrix with a ~170x170 per-value matrix and
  ~14,000 tests, and the multiple-comparison correction would then dominate the result; (ii) the
  review's question is posed at the level of the dimension ("do context strategy and verification
  travel together"), not at the level of the individual value; (iii) the value set is the design
  decision -- a harness that does ``search_replace`` *and* ``unified_diff`` made a different choice
  from one that does only ``search_replace``, and one-hot encoding would score those as partly
  equal. The cost is level inflation (up to 2^7 - 1 combinations for a 7-value dimension), which is
  handled by the Bergsma correction, by the permutation test, and by pooling levels seen in fewer
  than ``--min-level-count`` systems into ``«rare»`` (reported per dimension in the dimension
  diagnostics table, and disableable with ``--min-level-count 1``). The clustering does NOT use
  this collapse: there, multi-valued dimensions are compared with a Jaccard distance between the
  value sets, which is the natural graded comparison and needs no levels at all.

* NON-CATEGORICAL DIMENSIONS. ``integer`` and ``date`` dimensions are binned into
  ``--n-bins`` quantile bins computed from the coded values only (so the bins are not defined by
  the missingness pattern), and the bin edges are printed in the diagnostics table. ``string``
  dimensions are checked for cardinality at runtime; a free-text field whose distinct values
  exceed ``--string-max-unique`` of its coded cells carries no categorical information (it is an
  identifier) and is excluded from the association matrix with a reason recorded in the
  diagnostics table -- its row and column in the 38x38 matrix are blank, not zero. The clustering
  uses the numeric dimensions as a normalised absolute difference and excludes the free-text ones.

* SIGNIFICANCE. Permutation test: one dimension's labels are shuffled within the analysis subset
  for that pair, so the test respects the observed marginals and the observed n.
  p = (1 + #{V~_perm >= V~_obs}) / (``--n-perm`` + 1). Pairs whose corrected V is exactly 0 are
  assigned p = 1 without permuting (no permutation can fall below 0). Multiplicity across the
  703 = 38*37/2 pairs is controlled with Benjamini-Hochberg FDR (primary, ``q_bh``) and
  Holm-Bonferroni (conservative, ``q_holm``), applied within each treatment separately.

* SAMPLING WEIGHTS. The corpus is a stratified sample (H = census at weight 1, P ~ 4.55,
  O ~ 48.37 from ``data/coding_frame.csv``). The primary association result is UNWEIGHTED and
  describes the coded corpus. A weighted corrected V is reported as a sensitivity column: the
  contingency table is built from summed weights and rescaled to the Kish effective sample size
  n_eff = (sum w)^2 / sum(w^2) before the bias correction, so the correction is not fed an
  inflated n. No permutation p-value is computed for the weighted variant. Systems present in
  ``data/systems.json`` but carrying weight 0 in the frame (a stale ``coded`` flag) are given
  their stratum's mean positive weight; the count is logged.

* DISTANCE FOR CLUSTERING: GOWER, not Hamming. Hamming needs complete records; with 48.9% NR a
  complete-case Hamming analysis would keep almost no systems, and filling NR to make Hamming work
  is precisely the trap. Gower averages a per-dimension dissimilarity over the dimensions
  *available in both* systems (mismatch for single-valued enums, Jaccard between value sets for
  multi-valued ones, |x-y|/range for integer and date), which is a complete-pairs distance applied
  per system pair. Systems coded on fewer than ``--min-coded-share`` of the usable dimensions are
  dropped, and any pair overlapping on fewer than ``--min-overlap`` dimensions makes the distance
  undefined; systems are dropped greedily until the matrix is complete. All drops are logged.

* LINKAGE AND k. Average linkage (UPGMA) on the precomputed Gower distance: Ward and centroid
  require Euclidean coordinates, which a Gower distance does not provide, and complete linkage is
  dominated by single outlying systems in a sparse, mixed-type space. The cophenetic correlation
  of the chosen linkage is reported. k is chosen by the mean silhouette on the precomputed
  distance over k = 2..``--kmax``, not by eye. A k where one cluster still holds more than
  ``--max-cluster-frac`` of the analysis set is ruled ineligible before the maximum is taken:
  agglomerative linkage on a sparse mixed-type distance peels single outliers first, so the top of
  an unguarded silhouette curve is typically a 6-versus-574 split, which scores well while being an
  outlier detector rather than a family structure. If *every* k is such a peel, that is itself
  recorded as evidence against families. The silhouette curve and the cophenetic correlation are
  also computed for the other admissible linkages (complete, weighted, single) as a sensitivity, so
  the verdict does not hinge on one linkage rule; Ward and centroid are not run because they assume
  Euclidean coordinates, which a Gower distance does not provide. The chosen k is only *declared*
  as families if it clears three pre-stated bars: (1) silhouette >= ``--min-silhouette``;
  (2) silhouette above the 95th percentile of the permuted null described above (the gap
  criterion), computed on the SELECTED statistic rather than per k: because k is chosen by
  maximising the observed silhouette over the eligible k, the null must be maximised the same way,
  so the reference distribution is the distribution over ``--n-null`` draws of each draw's maximum
  silhouette over the k that draw's own largest-cluster filter leaves eligible. The per-k null
  percentiles are still reported, as diagnostics, and comparing the observed maximum to the per-k
  null at the k that produced it is a winner's-curse comparison that this script does not gate on.
  (3) mean bootstrap Jaccard stability >= ``--min-stability`` over ``--n-boot`` 80% subsamples. If any bar fails, the script reports a
  NEGATIVE RESULT -- "the corpus does not fall into clean design families" -- and labels the
  best-k partition "provisional" everywhere it appears. A forced k is worse than no k.

* DOCUMENTATION CONFOUNDING. For every cluster the mean and median share of coded cells is
  reported, with a Kruskal-Wallis test across clusters and the spread between the highest and
  lowest cluster mean, both over all clusters and over the clusters holding at least
  ``--large-cluster-share`` of the analysis set (a six-system cluster can swing the spread on its
  own). If the spread exceeds ``--confound-spread`` the clusters are flagged as possible
  documentation artefacts, in the summary JSON and in the figure captions.

OUTPUTS
-------
Tables (``data/analysis/``):
  ``family_dimension_diagnostics.csv``  per dimension: type, multi, cell-state counts, coded
      share, treatment applied, levels used, levels pooled as rare, bin edges, inclusion + reason.
  ``family_associations.csv``           all 703 pairs, both treatments side by side: n, r, c,
      raw V, corrected V, permutation p, BH q, Holm q, weighted corrected V, delta and flip flag.
  ``family_associations_top.csv``       the ranked strongest associations on complete pairs, with n.
  ``family_nr_flips.csv``               pairs where treating NR as a level changes the conclusion.
  ``family_clusters.csv``               per system: cluster, silhouette, coded share, stratum, weight.
  ``family_cluster_summary.csv``        per cluster: size, weight sum, coded share, stability, examples.
  ``family_cluster_markers.csv``        per cluster: the dimensions and values that distinguish it.
  ``family_summary.json``               every decision, the silhouette curve, the null band, the
      stability numbers, the confounding test and the verdict text, for the paper to quote.

Figures (``paper/figures/``, SVG + PDF):
  ``family_association_matrix``  FIGURE CAPTION: "Pairwise association between the 38 coding
      dimensions, bias-corrected Cramer's V (Bergsma 2013). LEFT: complete pairs only -- both
      dimensions carry a value; this is the design signal, and the n behind each cell varies
      (see data/analysis/family_associations.csv). RIGHT: not_reported treated as an additional
      level of every dimension; this panel measures which dimensions are DOCUMENTED together, not
      which designs co-occur, and is shown only as a contrast. Sequential colour scale: corrected
      Cramer's V is bounded in [0, 1] and cannot be negative. Grey cells are dimensions excluded
      from the matrix (free-text identifiers) or pairs with too few complete observations.
      unresolved cells are excluded from both panels. Dimensions are ordered by schema layer;
      white lines separate layers."
  ``family_association_delta``   FIGURE CAPTION: "Corrected Cramer's V with not_reported as a
      level MINUS corrected Cramer's V on complete pairs. Diverging scale centred at zero because
      this difference, unlike V itself, can take either sign. Red cells are pairs that look more
      strongly associated once silence is counted as a design choice: their apparent association
      is documentation behaviour. Pairs marked with a dot change conclusion (significance flip at
      BH q < 0.05, or |delta| >= the flip threshold)."
  ``family_dendrogram``          FIGURE CAPTION: "LEFT: average-linkage (UPGMA) dendrogram of
      harnesses over a Gower distance computed on coded cells only (per pair of systems, the
      distance averages over the dimensions both systems report; not_reported contributes nothing
      and unresolved cells are excluded). RIGHT: mean silhouette against the number of clusters
      (solid) with the 95th percentile of a null in which every dimension is permuted within its
      observed cells, preserving both marginals and the missingness pattern (dashed). The chosen
      cut is marked; if the silhouette does not clear the pre-stated bars the partition is labelled
      provisional and no families are claimed."
  ``family_clusters_mds``        FIGURE CAPTION: "Metric MDS of the Gower distance. LEFT: coloured
      by cluster at the selected k. RIGHT: coloured by the share of the 38 dimensions the system
      reports. If the right-hand gradient reproduces the left-hand partition, the 'families' are
      documentation strata rather than design families; the per-cluster coded shares in
      data/analysis/family_cluster_summary.csv quantify that."

USAGE
-----
    python scripts/analyse_families.py                      # full run
    python scripts/analyse_families.py --n-perm 200 --n-null 5 --n-boot 5   # fast draft
    python scripts/analyse_families.py --no-figures --tables-only
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("analyse_families")

NR_LEVEL = "«not_reported»"
RARE_LEVEL = "«rare»"
EMPTY_SET_LEVEL = "«empty_set»"

# ---------------------------------------------------------------------------
# schema + data loading
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Dimension:
    id: str
    key: str
    layer: str
    name: str
    type: str
    multi: bool
    values: tuple[str, ...] = ()

    @property
    def label(self) -> str:
        return f"{self.id} {self.key}"


def load_dimensions(path: Path) -> tuple[list[Dimension], dict[str, str]]:
    """Read ``schema/dimensions.json``; return the dimensions in schema order and layer names."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    layers = {lay["id"]: lay.get("name", lay["id"]) for lay in raw.get("layers", [])}
    dims = [
        Dimension(
            id=d["id"],
            key=d["key"],
            layer=d.get("layer", ""),
            name=d.get("name", d["key"]),
            type=d.get("type", "enum"),
            multi=bool(d.get("multi", False)),
            values=tuple(d.get("values", []) or ()),
        )
        for d in raw["dimensions"]
    ]
    LOG.info("schema %s: %d dimensions in %d layers", raw.get("schema_version", "?"), len(dims), len(layers))
    return dims, layers


def load_systems(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    systems = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(systems, list):
        raise TypeError(f"{path} must hold a list of systems")
    if limit:
        systems = systems[:limit]
    LOG.info("loaded %d systems from %s", len(systems), path.name)
    return systems


def cell_state(cell: Any) -> str:
    """One of ``value`` / ``not_reported`` / ``unresolved`` / ``missing``.

    ``unresolved`` wins over everything: the coder could not settle the cell, so it is neither a
    value nor a statement that the sources are silent, and it is dropped from every analysis.
    """
    if not isinstance(cell, dict):
        return "missing" if cell is None else "value"
    if cell.get("unresolved"):
        return "unresolved"
    if cell.get("not_reported"):
        return "not_reported"
    return "value" if cell.get("value") is not None else "missing"


def load_weights(path: Path, system_ids: Sequence[str]) -> pd.DataFrame:
    """Join ``stratum`` and ``weight`` for the coded systems; repair zero weights per stratum."""
    frame = pd.read_csv(path, usecols=["system_id", "stratum", "weight"])
    frame = frame.drop_duplicates("system_id").set_index("system_id")
    out = pd.DataFrame(index=pd.Index(system_ids, name="system_id"))
    out["stratum"] = frame["stratum"].reindex(out.index).fillna("?")
    out["weight"] = pd.to_numeric(frame["weight"].reindex(out.index), errors="coerce")
    bad = out["weight"].isna() | (out["weight"] <= 0)
    if bad.any():
        pos = out.loc[~bad].groupby("stratum")["weight"].mean()
        fallback = float(out.loc[~bad, "weight"].mean()) if (~bad).any() else 1.0
        out.loc[bad, "weight"] = [float(pos.get(s, fallback)) for s in out.loc[bad, "stratum"]]
        LOG.warning(
            "%d/%d systems had weight 0 or missing in the coding frame; imputed the stratum mean "
            "positive weight (affects the weighted sensitivity column only)",
            int(bad.sum()),
            len(out),
        )
    return out


# ---------------------------------------------------------------------------
# label frames: one categorical label per (system, dimension), two treatments
# ---------------------------------------------------------------------------


@dataclass
class DimensionPrep:
    dim: Dimension
    treatment: str
    included: bool
    reason: str = ""
    n_value: int = 0
    n_not_reported: int = 0
    n_unresolved: int = 0
    n_missing: int = 0
    n_levels: int = 0
    n_levels_pooled: int = 0
    n_pooled_systems: int = 0
    bin_edges: str = ""
    distinct_raw: int = 0


@dataclass
class Corpus:
    """Everything the analyses need, derived from the schema at runtime."""

    ids: list[str]
    names: list[str]
    dims: list[Dimension]
    layers: dict[str, str]
    labels_complete: pd.DataFrame  # value labels; NaN for NR and unresolved
    labels_nr: pd.DataFrame  # same, but NR is its own level; NaN for unresolved only
    states: pd.DataFrame
    prep: dict[str, DimensionPrep]
    raw: dict[str, dict[str, Any]]  # per-dimension arrays for the Gower distance
    weights: pd.DataFrame

    @property
    def usable(self) -> list[Dimension]:
        return [d for d in self.dims if self.prep[d.key].included]

    @property
    def coded_share(self) -> pd.Series:
        """Share of the 38 dimensions on which a system carries a value."""
        return (self.states == "value").mean(axis=1)


def _multi_label(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        items = sorted(str(v) for v in value)
        return "+".join(items) if items else EMPTY_SET_LEVEL
    return str(value)


def _quantile_bins(values: np.ndarray, n_bins: int) -> tuple[np.ndarray, list[str]]:
    """Quantile bin edges from the *coded* values only, so bins never encode missingness."""
    qs = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.unique(np.quantile(values, qs))
    if edges.size < 2:
        edges = np.array([values.min(), values.min() + 1.0])
    labels = []
    for i in range(edges.size - 1):
        lo, hi = edges[i], edges[i + 1]
        last = i == edges.size - 2
        labels.append(f"[{lo:g},{hi:g}{']' if last else ')'}")
    return edges, labels


def _bin_label(x: float, edges: np.ndarray, labels: list[str]) -> str:
    idx = int(np.searchsorted(edges, x, side="right") - 1)
    return labels[min(max(idx, 0), len(labels) - 1)]


def _date_ordinal(value: Any) -> float | None:
    ts = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(ts):
        return None
    return float(ts.toordinal())


def build_corpus(
    systems: Sequence[dict[str, Any]],
    dims: Sequence[Dimension],
    layers: dict[str, str],
    weights_path: Path | None = None,
    *,
    min_level_count: int = 5,
    n_bins: int = 4,
    string_max_unique: float = 0.5,
) -> Corpus:
    """Turn the coded cells into label frames (both treatments) plus raw arrays for Gower.

    ``labels_complete`` holds a label only where the cell carries a value; ``labels_nr`` also
    labels NR cells with :data:`NR_LEVEL`. Both leave ``unresolved`` cells as NaN.
    """
    ids = [str(s.get("id")) for s in systems]
    names = [str(s.get("name") or s.get("id")) for s in systems]
    n = len(ids)
    index = pd.Index(ids, name="system_id")

    states = pd.DataFrame(index=index, columns=[d.key for d in dims], dtype=object)
    values: dict[str, list[Any]] = {}
    for d in dims:
        col_state: list[str] = []
        col_val: list[Any] = []
        for s in systems:
            cell = (s.get("coding") or {}).get(d.key)
            st = cell_state(cell)
            col_state.append(st)
            col_val.append(cell.get("value") if (st == "value" and isinstance(cell, dict)) else None)
        states[d.key] = col_state
        values[d.key] = col_val

    prep: dict[str, DimensionPrep] = {}
    labels_complete = pd.DataFrame(index=index, columns=[d.key for d in dims], dtype=object)
    raw: dict[str, dict[str, Any]] = {}

    for d in dims:
        st = states[d.key].to_numpy()
        vals = values[d.key]
        counts = {k: int((st == k).sum()) for k in ("value", "not_reported", "unresolved", "missing")}
        avail = st == "value"
        treatment = ""
        included = True
        reason = ""
        labels: list[Any] = [np.nan] * n
        bin_edges = ""

        if d.multi:
            treatment = "value-set as level; Jaccard on sets for the distance"
            for i in range(n):
                if avail[i]:
                    labels[i] = _multi_label(vals[i])
            vocab = sorted({str(v) for i in range(n) if avail[i] for v in _as_list(vals[i])})
            X = np.zeros((n, max(len(vocab), 1)), dtype=float)
            pos = {v: j for j, v in enumerate(vocab)}
            for i in range(n):
                if avail[i]:
                    for v in _as_list(vals[i]):
                        X[i, pos[str(v)]] = 1.0
            raw[d.key] = {"kind": "multi", "X": X, "avail": avail.copy(), "vocab": vocab}
        elif d.type in ("integer", "number"):
            numeric = np.array(
                [float(vals[i]) if avail[i] and _is_number(vals[i]) else np.nan for i in range(n)],
                dtype=float,
            )
            ok = ~np.isnan(numeric)
            if ok.sum() >= 2:
                edges, blabels = _quantile_bins(numeric[ok], n_bins)
                bin_edges = ",".join(f"{e:g}" for e in edges)
                treatment = f"{len(blabels)} quantile bins from coded values; |x-y|/range for the distance"
                for i in range(n):
                    if ok[i]:
                        labels[i] = _bin_label(numeric[i], edges, blabels)
            else:
                included, reason = False, "fewer than 2 numeric values"
                treatment = "excluded"
            raw[d.key] = {"kind": "num", "x": numeric, "avail": ok}
        elif d.type == "date":
            numeric = np.array(
                [(_date_ordinal(vals[i]) if avail[i] else None) or np.nan for i in range(n)], dtype=float
            )
            ok = ~np.isnan(numeric)
            if ok.sum() >= 2:
                edges, _ = _quantile_bins(numeric[ok], n_bins)
                blabels = [
                    f"[{pd.Timestamp.fromordinal(int(edges[i])).date()},"
                    f"{pd.Timestamp.fromordinal(int(edges[i + 1])).date()}"
                    f"{']' if i == edges.size - 2 else ')'}"
                    for i in range(edges.size - 1)
                ]
                bin_edges = ",".join(str(pd.Timestamp.fromordinal(int(e)).date()) for e in edges)
                treatment = f"{len(blabels)} quantile date bins from coded values; |x-y|/range for the distance"
                for i in range(n):
                    if ok[i]:
                        labels[i] = _bin_label(numeric[i], edges, blabels)
            else:
                included, reason = False, "fewer than 2 parseable dates"
                treatment = "excluded"
            raw[d.key] = {"kind": "num", "x": numeric, "avail": ok}
        else:  # enum single-valued, string, anything else categorical
            coded = [str(vals[i]) for i in range(n) if avail[i]]
            distinct = len(set(coded))
            if d.type == "string" and coded and distinct > string_max_unique * len(coded):
                included = False
                reason = (
                    f"free-text identifier: {distinct} distinct values in {len(coded)} coded cells "
                    f"(> {string_max_unique:.0%}); carries no categorical information"
                )
                treatment = "excluded from the association matrix and from the distance"
                raw[d.key] = {"kind": "skip"}
            else:
                treatment = "categorical as coded; mismatch (0/1) for the distance"
                for i in range(n):
                    if avail[i]:
                        labels[i] = str(vals[i])
                arr = np.array([str(vals[i]) if avail[i] else None for i in range(n)], dtype=object)
                raw[d.key] = {"kind": "cat", "x": arr, "avail": avail.copy()}

        ser = pd.Series(labels, index=index, dtype=object)
        n_pooled_levels = 0
        n_pooled_systems = 0
        if included and min_level_count > 1:
            vc = ser.value_counts()
            rare = set(vc.index[vc < min_level_count])
            if rare:
                mask = ser.isin(rare)
                n_pooled_levels = len(rare)
                n_pooled_systems = int(mask.sum())
                ser = ser.mask(mask, RARE_LEVEL)
        labels_complete[d.key] = ser
        prep[d.key] = DimensionPrep(
            dim=d,
            treatment=treatment,
            included=included,
            reason=reason,
            n_value=counts["value"],
            n_not_reported=counts["not_reported"],
            n_unresolved=counts["unresolved"],
            n_missing=counts["missing"],
            n_levels=int(ser.nunique(dropna=True)),
            n_levels_pooled=n_pooled_levels,
            n_pooled_systems=n_pooled_systems,
            bin_edges=bin_edges,
            distinct_raw=int(pd.Series([str(vals[i]) for i in range(n) if avail[i]]).nunique()) if avail.any() else 0,
        )
        if not included:
            LOG.info("dimension %s excluded from the matrix: %s", d.label, reason)

    # treatment (b): NR becomes its own level of every included dimension
    labels_nr = labels_complete.copy()
    for d in dims:
        if not prep[d.key].included:
            continue
        nr_mask = states[d.key] == "not_reported"
        labels_nr.loc[nr_mask, d.key] = NR_LEVEL

    weights = (
        load_weights(weights_path, ids)
        if weights_path is not None and Path(weights_path).exists()
        else pd.DataFrame({"stratum": "?", "weight": 1.0}, index=index)
    )
    corpus = Corpus(
        ids=ids,
        names=names,
        dims=list(dims),
        layers=layers,
        labels_complete=labels_complete,
        labels_nr=labels_nr,
        states=states,
        prep=prep,
        raw=raw,
        weights=weights,
    )
    tot = states.size
    LOG.info(
        "cells: %d value (%.1f%%), %d not_reported (%.1f%%), %d unresolved (%.2f%%), %d missing",
        int((states == "value").sum().sum()),
        100 * (states == "value").sum().sum() / tot,
        int((states == "not_reported").sum().sum()),
        100 * (states == "not_reported").sum().sum() / tot,
        int((states == "unresolved").sum().sum()),
        100 * (states == "unresolved").sum().sum() / tot,
        int((states == "missing").sum().sum()),
    )
    return corpus


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [] if value is None else [value]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and not (
        isinstance(value, float) and math.isnan(value)
    )


# ---------------------------------------------------------------------------
# Cramer's V with the Bergsma (2013) bias correction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Assoc:
    n: int
    r: int
    c: int
    chi2: float
    v_raw: float
    v_corrected: float


def contingency(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Contingency table of two integer-coded arrays, with empty rows and columns dropped.

    Empty levels must be dropped: after restricting to complete pairs, levels present in the full
    corpus can vanish, and counting them would make the table look sparser than it is and so
    over-penalise the bias correction.
    """
    if a.size == 0:
        return np.zeros((0, 0), dtype=float)
    ra, rb = int(a.max()) + 1, int(b.max()) + 1
    table = np.bincount(a * rb + b, minlength=ra * rb).reshape(ra, rb).astype(float)
    table = table[table.sum(axis=1) > 0][:, table.sum(axis=0) > 0]
    return table


def cramers_v_from_table(table: np.ndarray) -> Assoc:
    """Raw and Bergsma (2013) bias-corrected Cramer's V from a contingency table."""
    n = float(table.sum())
    r, c = table.shape
    if n <= 1 or r < 2 or c < 2:
        return Assoc(int(n), r, c, float("nan"), float("nan"), float("nan"))
    rows = table.sum(axis=1, keepdims=True)
    cols = table.sum(axis=0, keepdims=True)
    chi2 = float(n * ((table**2 / (rows * cols)).sum() - 1.0))
    phi2 = chi2 / n
    v_raw = math.sqrt(max(phi2, 0.0) / min(r - 1, c - 1))
    # Bergsma (2013): remove the expected value of phi2 under independence, and shrink the
    # dimensions by the same order, before dividing.
    phi2_t = max(0.0, phi2 - (r - 1) * (c - 1) / (n - 1))
    r_t = r - (r - 1) ** 2 / (n - 1)
    c_t = c - (c - 1) ** 2 / (n - 1)
    denom = min(r_t - 1, c_t - 1)
    v_corr = math.sqrt(phi2_t / denom) if denom > 0 else float("nan")
    if not math.isnan(v_corr):
        v_corr = min(v_corr, 1.0)
    return Assoc(round(n), r, c, chi2, min(v_raw, 1.0), v_corr)


def cramers_v(a: Sequence[Any], b: Sequence[Any]) -> Assoc:
    """Corrected Cramer's V between two equal-length label sequences (rows with NaN dropped)."""
    sa = pd.Series(list(a), dtype=object)
    sb = pd.Series(list(b), dtype=object)
    keep = sa.notna() & sb.notna()
    ca = pd.factorize(sa[keep], use_na_sentinel=False)[0]
    cb = pd.factorize(sb[keep], use_na_sentinel=False)[0]
    return cramers_v_from_table(contingency(ca.astype(np.int64), cb.astype(np.int64)))


def weighted_cramers_v(a: np.ndarray, b: np.ndarray, w: np.ndarray) -> Assoc:
    """Corrected V on a weight-summed table rescaled to the Kish effective sample size."""
    if a.size == 0 or w.sum() <= 0:
        return Assoc(0, 0, 0, float("nan"), float("nan"), float("nan"))
    ra, rb = int(a.max()) + 1, int(b.max()) + 1
    table = np.bincount(a * rb + b, weights=w, minlength=ra * rb).reshape(ra, rb)
    table = table[table.sum(axis=1) > 0][:, table.sum(axis=0) > 0]
    n_eff = float(w.sum() ** 2 / np.square(w).sum())
    total = table.sum()
    if total <= 0:
        return Assoc(0, 0, 0, float("nan"), float("nan"), float("nan"))
    return cramers_v_from_table(table * (n_eff / total))


def permutation_p(
    a: np.ndarray, b: np.ndarray, v_obs: float, n_perm: int, rng: np.random.Generator
) -> tuple[float, int]:
    """p = (1 + #{V~_perm >= V~_obs}) / (n_perm + 1) by shuffling ``b`` within the pair's subset.

    A corrected V of exactly 0 (the bias correction clipped the statistic) cannot be exceeded from
    below, so p = 1 is exact and no permutation is run. NaN V (a degenerate table) gives NaN.
    """
    if math.isnan(v_obs):
        return float("nan"), 0
    if v_obs <= 0.0 or n_perm <= 0:
        return 1.0, 0
    ge = 0
    perm = b.copy()
    for _ in range(n_perm):
        rng.shuffle(perm)
        v = cramers_v_from_table(contingency(a, perm)).v_corrected
        if not math.isnan(v) and v >= v_obs:
            ge += 1
    return (1.0 + ge) / (n_perm + 1.0), n_perm


# ---------------------------------------------------------------------------
# multiple comparisons
# ---------------------------------------------------------------------------


def bh_fdr(p: Sequence[float]) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaN preserved)."""
    arr = np.asarray(p, dtype=float)
    out = np.full(arr.shape, np.nan)
    ok = ~np.isnan(arr)
    m = int(ok.sum())
    if m == 0:
        return out
    idx = np.flatnonzero(ok)
    order = idx[np.argsort(arr[idx], kind="stable")]
    ranked = arr[order] * m / np.arange(1, m + 1)
    out[order] = np.minimum.accumulate(ranked[::-1])[::-1].clip(0, 1)
    return out


def holm(p: Sequence[float]) -> np.ndarray:
    """Holm-Bonferroni adjusted p-values (NaN preserved)."""
    arr = np.asarray(p, dtype=float)
    out = np.full(arr.shape, np.nan)
    ok = ~np.isnan(arr)
    m = int(ok.sum())
    if m == 0:
        return out
    idx = np.flatnonzero(ok)
    order = idx[np.argsort(arr[idx], kind="stable")]
    ranked = arr[order] * (m - np.arange(m))
    out[order] = np.maximum.accumulate(ranked).clip(0, 1)
    return out


# ---------------------------------------------------------------------------
# the 38x38 association matrix
# ---------------------------------------------------------------------------


def association_table(
    corpus: Corpus,
    *,
    n_perm: int = 2000,
    seed: int = 20260924,
    alpha: float = 0.05,
    flip_delta: float = 0.15,
) -> pd.DataFrame:
    """All 38*37/2 pairs, both treatments, with n, permutation p and multiplicity correction."""
    dims = corpus.dims
    rng = np.random.default_rng(seed)
    codes_c: dict[str, np.ndarray] = {}
    codes_n: dict[str, np.ndarray] = {}
    for d in dims:
        codes_c[d.key], _ = pd.factorize(corpus.labels_complete[d.key], use_na_sentinel=True)
        codes_n[d.key], _ = pd.factorize(corpus.labels_nr[d.key], use_na_sentinel=True)
    weight = corpus.weights["weight"].to_numpy(dtype=float)

    rows: list[dict[str, Any]] = []
    for i, da in enumerate(dims):
        for db in dims[i + 1 :]:
            rec: dict[str, Any] = {
                "dim_a_id": da.id,
                "dim_a_key": da.key,
                "layer_a": da.layer,
                "dim_b_id": db.id,
                "dim_b_key": db.key,
                "layer_b": db.layer,
                "same_layer": da.layer == db.layer,
                "multi_a": da.multi,
                "multi_b": db.multi,
            }
            usable = corpus.prep[da.key].included and corpus.prep[db.key].included
            if not usable:
                reason = "; ".join(
                    r for r in (corpus.prep[da.key].reason, corpus.prep[db.key].reason) if r
                )
                rec.update({"excluded": True, "exclusion_reason": reason})
                rows.append(rec)
                continue
            rec["excluded"] = False
            rec["exclusion_reason"] = ""
            for tag, codes in (("complete", codes_c), ("nr", codes_n)):
                a, b = codes[da.key], codes[db.key]
                keep = (a >= 0) & (b >= 0)
                aa, bb = a[keep].astype(np.int64), b[keep].astype(np.int64)
                assoc = cramers_v_from_table(contingency(aa, bb))
                p, used = permutation_p(aa, bb, assoc.v_corrected, n_perm, rng)
                rec[f"n_{tag}"] = assoc.n
                rec[f"levels_a_{tag}"] = assoc.r
                rec[f"levels_b_{tag}"] = assoc.c
                rec[f"chi2_{tag}"] = assoc.chi2
                rec[f"v_raw_{tag}"] = assoc.v_raw
                rec[f"v_corrected_{tag}"] = assoc.v_corrected
                rec[f"p_perm_{tag}"] = p
                rec[f"n_perm_{tag}"] = used
                if tag == "complete":
                    wv = weighted_cramers_v(aa, bb, weight[keep])
                    rec["v_corrected_complete_weighted"] = wv.v_corrected
                    rec["n_eff_complete_weighted"] = wv.n
            rows.append(rec)

    table = pd.DataFrame(rows)
    # excluded pairs contribute no statistics, so guarantee the columns exist even if every pair
    # involving a dimension was excluded (otherwise the multiplicity step has nothing to adjust)
    for tag in ("complete", "nr"):
        for stem in ("n", "levels_a", "levels_b", "chi2", "v_raw", "v_corrected", "p_perm", "n_perm"):
            col = f"{stem}_{tag}"
            table[col] = pd.to_numeric(table[col], errors="coerce") if col in table else np.nan
    for col in ("v_corrected_complete_weighted", "n_eff_complete_weighted"):
        table[col] = pd.to_numeric(table[col], errors="coerce") if col in table else np.nan
    for tag in ("complete", "nr"):
        table[f"q_bh_{tag}"] = bh_fdr(table[f"p_perm_{tag}"])
        table[f"q_holm_{tag}"] = holm(table[f"p_perm_{tag}"])
        table[f"sig_{tag}"] = table[f"q_bh_{tag}"] < alpha
    table["delta_v_nr_minus_complete"] = table["v_corrected_nr"] - table["v_corrected_complete"]
    table["flips_conclusion"] = (table["sig_complete"] != table["sig_nr"]) | (
        table["delta_v_nr_minus_complete"].abs() >= flip_delta
    )
    table.loc[table["excluded"], ["sig_complete", "sig_nr", "flips_conclusion"]] = False
    table["flip_kind"] = np.where(
        table["excluded"],
        "",
        np.where(
            table["sig_nr"] & ~table["sig_complete"],
            "significant only with not_reported as a level (documentation, not design)",
            np.where(
                table["sig_complete"] & ~table["sig_nr"],
                "significant only on complete pairs (silence dilutes a real association)",
                np.where(
                    table["delta_v_nr_minus_complete"] >= flip_delta,
                    "same conclusion but inflated by shared silence",
                    np.where(
                        table["delta_v_nr_minus_complete"] <= -flip_delta,
                        "same conclusion but attenuated by shared silence",
                        "",
                    ),
                ),
            ),
        ),
    )
    table = table.sort_values("v_corrected_complete", ascending=False, na_position="last").reset_index(drop=True)
    LOG.info(
        "associations: %d pairs (%d excluded); %d significant at BH q<%.2f on complete pairs, "
        "%d with not_reported as a level; %d pairs flip conclusion",
        len(table),
        int(table["excluded"].sum()),
        int(table["sig_complete"].sum()),
        alpha,
        int(table["sig_nr"].sum()),
        int(table["flips_conclusion"].sum()),
    )
    return table


def matrix_from_table(table: pd.DataFrame, dims: Sequence[Dimension], column: str) -> pd.DataFrame:
    """Square symmetric matrix of ``column`` indexed by dimension label (diagonal = NaN)."""
    labels = [d.label for d in dims]
    key_to_label = {d.key: d.label for d in dims}
    mat = pd.DataFrame(np.nan, index=labels, columns=labels, dtype=float)
    vals = pd.to_numeric(table[column], errors="coerce") if column in table else pd.Series(dtype=float)
    for pos, (_, row) in enumerate(table.iterrows()):
        a, b = key_to_label[row["dim_a_key"]], key_to_label[row["dim_b_key"]]
        val = float(vals.iloc[pos]) if pos < len(vals) else np.nan
        mat.loc[a, b] = val
        mat.loc[b, a] = val
    return mat


# ---------------------------------------------------------------------------
# Gower distance + hierarchical clustering
# ---------------------------------------------------------------------------


@dataclass
class DistanceResult:
    D: np.ndarray
    ids: list[str]
    names: list[str]
    overlap: np.ndarray
    dropped_low_coverage: list[str] = field(default_factory=list)
    dropped_low_overlap: list[str] = field(default_factory=list)
    dims_used: list[str] = field(default_factory=list)


def gower_distance(
    raw: dict[str, dict[str, Any]], keys: Sequence[str], rows: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Gower distance over coded cells only; returns (distance, overlap count).

    Per pair of systems the distance averages the per-dimension dissimilarity over the dimensions
    *both* systems report: single-valued categoricals contribute a 0/1 mismatch, multi-valued ones
    the Jaccard distance between their value sets, numeric and date ones |x-y| over the coded
    range. ``not_reported`` contributes nothing at all -- which is the whole point, since counting
    shared silence as similarity is what makes badly documented systems look like a design family.
    Pairs with no shared coded dimension get NaN.
    """
    n = None
    for k in keys:
        info = raw[k]
        if info["kind"] == "skip":
            continue
        n = len(info["avail"])
        break
    if n is None:
        raise ValueError("no usable dimensions for the distance")
    sel = np.arange(n) if rows is None else np.asarray(rows)
    m = sel.size
    num = np.zeros((m, m), dtype=float)
    den = np.zeros((m, m), dtype=float)
    for k in keys:
        info = raw[k]
        kind = info["kind"]
        if kind == "skip":
            continue
        avail = info["avail"][sel]
        both = np.outer(avail, avail)
        if not both.any():
            continue
        if kind == "cat":
            x = info["x"][sel]
            d = (x[:, None] != x[None, :]).astype(float)
        elif kind == "num":
            x = info["x"][sel]
            span = np.nanmax(x[avail]) - np.nanmin(x[avail]) if avail.any() else 0.0
            if span <= 0:
                d = np.zeros((m, m), dtype=float)
            else:
                xs = np.where(avail, x, 0.0)
                d = np.abs(xs[:, None] - xs[None, :]) / span
        else:  # multi -> Jaccard distance between value sets
            X = info["X"][sel]
            inter = X @ X.T
            sizes = X.sum(axis=1)
            union = sizes[:, None] + sizes[None, :] - inter
            with np.errstate(invalid="ignore", divide="ignore"):
                d = np.where(union > 0, 1.0 - inter / np.where(union > 0, union, 1.0), 0.0)
        num += np.where(both, d, 0.0)
        den += both.astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        D = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    np.fill_diagonal(D, 0.0)
    return D, den


def build_distance(
    corpus: Corpus, *, min_coded_share: float = 0.5, min_overlap: int = 5
) -> DistanceResult:
    """Gower distance on the systems documented well enough to be comparable."""
    keys = [d.key for d in corpus.usable if corpus.raw[d.key]["kind"] != "skip"]
    share = (corpus.states[keys] == "value").mean(axis=1)
    keep_mask = (share >= min_coded_share).to_numpy()
    dropped_cov = [corpus.ids[i] for i in np.flatnonzero(~keep_mask)]
    rows = np.flatnonzero(keep_mask)
    LOG.info(
        "distance: %d/%d systems report >= %.0f%% of the %d usable dimensions",
        rows.size,
        len(corpus.ids),
        100 * min_coded_share,
        len(keys),
    )
    D, overlap = gower_distance(corpus.raw, keys, rows)
    bad = (overlap < min_overlap) & ~np.eye(rows.size, dtype=bool)
    dropped_ov: list[str] = []
    while bad.any():
        worst = int(bad.sum(axis=1).argmax())
        dropped_ov.append(corpus.ids[rows[worst]])
        keep = np.ones(rows.size, dtype=bool)
        keep[worst] = False
        rows = rows[keep]
        D = D[np.ix_(keep, keep)]
        overlap = overlap[np.ix_(keep, keep)]
        bad = (overlap < min_overlap) & ~np.eye(rows.size, dtype=bool)
    if dropped_ov:
        LOG.info("dropped %d systems whose pairwise overlap fell below %d dimensions", len(dropped_ov), min_overlap)
    nan_pairs = int(np.isnan(D).sum())
    if nan_pairs:
        raise RuntimeError(f"{nan_pairs} distances still undefined; raise --min-coded-share")
    return DistanceResult(
        D=D,
        ids=[corpus.ids[i] for i in rows],
        names=[corpus.names[i] for i in rows],
        overlap=overlap,
        dropped_low_coverage=dropped_cov,
        dropped_low_overlap=dropped_ov,
        dims_used=keys,
    )


@dataclass
class KChoice:
    ks: list[int]
    silhouettes: list[float]
    null_p95: list[float]
    null_mean: list[float]
    null_eligible_p95: list[float]
    null_eligible_share: list[float]
    null_max_p95: float
    null_max_mean: float
    null_max_draws: int
    p_selection_adjusted: float
    beats_null_per_k: bool
    beats_null_selection_adjusted: bool
    largest_cluster_frac: list[float]
    smallest_cluster_frac: list[float]
    eligible: list[bool]
    best_k: int
    best_silhouette: float
    cophenetic: float
    stability: dict[int, float]
    mean_stability: float
    families_found: bool
    verdict: str
    linkage_sensitivity: dict[str, dict[str, Any]] = field(default_factory=dict)


def linkage_matrix(D: np.ndarray, method: str = "average") -> np.ndarray:
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import squareform

    return linkage(squareform(D, checks=False), method=method)


def silhouette_curve(D: np.ndarray, Z: np.ndarray, ks: Iterable[int]) -> list[float]:
    return [s for s, _, _ in silhouette_curve_with_sizes(D, Z, ks)]


def silhouette_curve_with_sizes(
    D: np.ndarray, Z: np.ndarray, ks: Iterable[int]
) -> list[tuple[float, float, float]]:
    """(mean silhouette, largest cluster share, smallest cluster share) for each k."""
    from scipy.cluster.hierarchy import fcluster
    from sklearn.metrics import silhouette_score

    out: list[tuple[float, float, float]] = []
    for k in ks:
        labels = fcluster(Z, t=k, criterion="maxclust")
        if len(set(labels)) < 2:
            out.append((float("nan"), 1.0, 1.0))
            continue
        sizes = np.bincount(labels)[1:]
        sizes = sizes[sizes > 0]
        out.append(
            (
                float(silhouette_score(D, labels, metric="precomputed")),
                float(sizes.max() / labels.size),
                float(sizes.min() / labels.size),
            )
        )
    return out


def permute_raw(raw: dict[str, dict[str, Any]], keys: Sequence[str], rng: np.random.Generator) -> dict[str, dict[str, Any]]:
    """Shuffle each dimension *within its observed cells*: marginals and the NR pattern survive.

    This is the reference distribution for the clustering. It keeps every system's exact set of
    documented dimensions and every dimension's exact value distribution, and destroys only the
    cross-dimension association. A silhouette that this null reproduces is therefore explained by
    documentation behaviour plus marginals, not by design families.
    """
    out: dict[str, dict[str, Any]] = {}
    for k in keys:
        info = raw[k]
        if info["kind"] == "skip":
            out[k] = info
            continue
        idx = np.flatnonzero(info["avail"])
        perm = rng.permutation(idx)
        if info["kind"] == "multi":
            X = info["X"].copy()
            X[idx] = info["X"][perm]
            out[k] = {**info, "X": X}
        else:
            x = info["x"].copy()
            x[idx] = info["x"][perm]
            out[k] = {**info, "x": x}
    return out


def bootstrap_stability(
    corpus: Corpus,
    dist: DistanceResult,
    labels: np.ndarray,
    k: int,
    *,
    method: str,
    n_boot: int,
    frac: float,
    rng: np.random.Generator,
) -> dict[int, float]:
    """Hennig-style cluster stability: mean max Jaccard of each cluster over ``n_boot`` subsamples."""
    from scipy.cluster.hierarchy import fcluster

    n = len(dist.ids)
    jacc: dict[int, list[float]] = {int(c): [] for c in np.unique(labels)}
    for _ in range(max(n_boot, 0)):
        take = rng.choice(n, size=max(round(frac * n), k + 1), replace=False)
        take.sort()
        Db = dist.D[np.ix_(take, take)]
        Zb = linkage_matrix(Db, method=method)
        lb = fcluster(Zb, t=k, criterion="maxclust")
        for c, scores in jacc.items():
            orig = set(np.flatnonzero(labels[take] == c))
            if not orig:
                continue
            best = 0.0
            for cb in np.unique(lb):
                new = set(np.flatnonzero(lb == cb))
                union = len(orig | new)
                if union:
                    best = max(best, len(orig & new) / union)
            scores.append(best)
    return {c: (float(np.mean(v)) if v else float("nan")) for c, v in jacc.items()}


def choose_k(
    corpus: Corpus,
    dist: DistanceResult,
    *,
    method: str = "average",
    kmax: int = 12,
    n_null: int = 500,
    n_boot: int = 200,
    boot_frac: float = 0.8,
    min_silhouette: float = 0.25,
    min_stability: float = 0.60,
    max_cluster_frac: float = 0.90,
    sensitivity: bool = True,
    seed: int = 20260924,
) -> tuple[np.ndarray, KChoice]:
    """Pick k by silhouette against a marginal-and-missingness-preserving null, then test stability.

    Families are declared only if all three pre-stated bars are cleared. Otherwise the best-k
    partition is kept for description but labelled provisional and the verdict is negative.
    """
    from scipy.cluster.hierarchy import cophenet, fcluster
    from scipy.spatial.distance import squareform

    rng = np.random.default_rng(seed)
    Z = linkage_matrix(dist.D, method=method)
    coph = float(cophenet(Z, squareform(dist.D, checks=False))[0])
    ks = list(range(2, max(kmax, 2) + 1))
    curve = silhouette_curve_with_sizes(dist.D, Z, ks)
    sils = [s for s, _, _ in curve]
    largest = [m for _, m, _ in curve]
    smallest = [m for _, _, m in curve]
    # Pre-stated eligibility: agglomerative linkage on a sparse mixed-type distance peels single
    # outliers first, so the top of an unguarded silhouette curve is typically "one giant cluster
    # plus a sliver", which scores well and says nothing. A k where one cluster still holds more
    # than max_cluster_frac of the analysis set is such a peel, not a partition into families, and
    # cannot win the silhouette.
    eligible = [bool(m <= max_cluster_frac) for m in largest]
    if not any(eligible):
        LOG.warning(
            "every k left one cluster holding more than %.0f%% of the analysis set: the hierarchy "
            "only peels outliers, which is itself evidence against families; the guard is ignored "
            "so that a partition can still be described",
            100 * max_cluster_frac,
        )
        eligible = [True] * len(ks)

    rows = np.array([corpus.ids.index(i) for i in dist.ids]) if len(dist.ids) != len(corpus.ids) else None
    if rows is None:
        rows = np.arange(len(corpus.ids))
    n_null = max(n_null, 0)
    null = np.full((n_null, len(ks)), np.nan)        # silhouette curve of each null draw
    null_elig = np.full((n_null, len(ks)), np.nan)   # the same curve, ineligible k masked out
    null_max = np.full(n_null, np.nan)               # max over eligible k WITHIN each draw
    for b in range(n_null):
        praw = permute_raw(corpus.raw, dist.dims_used, rng)
        Dn, _ = gower_distance(praw, dist.dims_used, rows)
        if np.isnan(Dn).any():
            Dn = np.where(np.isnan(Dn), np.nanmax(Dn), Dn)
        curve_n = silhouette_curve_with_sizes(Dn, linkage_matrix(Dn, method=method), ks)
        null[b] = [s for s, _, _ in curve_n]
        # The observed statistic is a maximum over ELIGIBLE k, so the null must be passed through
        # the same filter and the same maximisation. Two corrections, both of which matter here:
        # (1) eligibility. A null draw whose best silhouette comes from a "one giant cluster plus a
        #     sliver" cut would otherwise set a bar the observed curve was never allowed to compete
        #     for, and conversely the observed curve loses its own high-scoring small k to the
        #     filter while the null keeps them.
        # (2) selection. Comparing the observed maximum against the per-k null at the k that
        #     maximised it is a winner's-curse comparison: k was chosen by looking at the data. The
        #     reference distribution has to be the distribution of the null's own maximum over the
        #     eligible k, which is what null_max records.
        null_elig[b] = [s if m <= max_cluster_frac else np.nan for s, m, _ in curve_n]
        if not np.all(np.isnan(null_elig[b])):
            null_max[b] = float(np.nanmax(null_elig[b]))
    nan_k = [float("nan")] * len(ks)
    with np.errstate(invalid="ignore"):
        null_p95 = list(np.nanpercentile(null, 95, axis=0)) if n_null > 0 else nan_k
        null_mean = list(np.nanmean(null, axis=0)) if n_null > 0 else nan_k
        null_eligible_p95 = [
            float(np.nanpercentile(col, 95)) if np.any(~np.isnan(col)) else float("nan")
            for col in null_elig.T
        ] if n_null > 0 else nan_k
        null_eligible_share = ([float(np.mean(~np.isnan(col))) for col in null_elig.T]
                               if n_null > 0 else nan_k)
    null_max_draws = null_max[~np.isnan(null_max)]
    null_max_p95 = float(np.percentile(null_max_draws, 95)) if null_max_draws.size else float("nan")
    null_max_mean = float(np.mean(null_max_draws)) if null_max_draws.size else float("nan")

    # Linkage sensitivity: the negative/positive verdict must not hinge on one linkage rule.
    # Ward and centroid are inadmissible on a Gower distance (they assume Euclidean coordinates)
    # and are therefore not run.
    sens: dict[str, dict[str, Any]] = {}
    if sensitivity:
        for alt in ("average", "complete", "weighted", "single"):
            Za = Z if alt == method else linkage_matrix(dist.D, alt)
            cur = silhouette_curve_with_sizes(dist.D, Za, ks)
            elig = [bool(m <= max_cluster_frac) for _, m, _ in cur]
            vals = [s if e else float("nan") for (s, _, _), e in zip(cur, elig)]
            best = float(np.nanmax(vals)) if not np.all(np.isnan(vals)) else float("nan")
            sens[alt] = {
                "cophenetic_correlation": float(cophenet(Za, squareform(dist.D, checks=False))[0]),
                "silhouettes": [float(s) for s, _, _ in cur],
                "largest_cluster_share": [float(m) for _, m, _ in cur],
                "eligible": elig,
                "best_eligible_silhouette": best,
                "best_eligible_k": int(ks[int(np.nanargmax(vals))]) if not np.all(np.isnan(vals)) else None,
            }
        LOG.info(
            "linkage sensitivity (best non-degenerate silhouette): %s",
            ", ".join(f"{k}={v['best_eligible_silhouette']:.3f} at k={v['best_eligible_k']}" for k, v in sens.items()),
        )

    arr = np.where(eligible, np.array(sils, dtype=float), np.nan)
    best_i = int(np.nanargmax(arr)) if not np.all(np.isnan(arr)) else 0
    best_k, best_sil = ks[best_i], float(arr[best_i])
    labels = fcluster(Z, t=best_k, criterion="maxclust")
    stab = bootstrap_stability(
        corpus, dist, labels, best_k, method=method, n_boot=n_boot, frac=boot_frac, rng=rng
    )
    mean_stab = float(np.nanmean(list(stab.values()))) if stab else float("nan")

    beats_null_per_k = bool(n_null > 0 and not math.isnan(null_p95[best_i])
                            and best_sil > null_p95[best_i])
    # The gate is the selection-adjusted comparison, not the per-k one.
    p_selection_adjusted = (float((1 + int(np.sum(null_max_draws >= best_sil)))
                                  / (null_max_draws.size + 1))
                            if null_max_draws.size else float("nan"))
    beats_null = bool(n_null > 0 and not math.isnan(null_max_p95) and best_sil > null_max_p95)
    clears_sil = bool(best_sil >= min_silhouette)
    clears_stab = bool(not math.isnan(mean_stab) and mean_stab >= min_stability)
    all_degenerate = bool(all(m > max_cluster_frac for m in largest))
    found = clears_sil and beats_null and clears_stab and not all_degenerate
    reasons = []
    if all_degenerate:
        reasons.append(
            f"at every k from {ks[0]} to {ks[-1]} one cluster still held more than "
            f"{max_cluster_frac:.0%} of the analysis set, i.e. the hierarchy only peels outliers off "
            "a single undifferentiated mass"
        )
    if not clears_sil:
        reasons.append(f"best mean silhouette {best_sil:.3f} < the pre-stated floor {min_silhouette:.2f}")
    if n_null > 0 and not beats_null:
        reasons.append(
            f"silhouette {best_sil:.3f} does not exceed the 95th percentile of the selected "
            f"statistic's null, the maximum over eligible k of the marginal-preserving null "
            f"({null_max_p95:.3f} over {null_max_draws.size} draws, selection-adjusted "
            f"p = {p_selection_adjusted:.3f}), so the structure is not distinguishable from "
            "per-dimension marginals plus the documentation pattern once the choice of k is "
            "accounted for"
        )
    if not clears_stab:
        reasons.append(f"mean bootstrap Jaccard stability {mean_stab:.3f} < {min_stability:.2f}")
    verdict = (
        f"Design families supported: k={best_k}, mean silhouette {best_sil:.3f}, "
        f"stability {mean_stab:.3f}, above the selection-adjusted null 95th percentile "
        f"{null_max_p95:.3f} (p = {p_selection_adjusted:.3f})."
        if found
        else "NEGATIVE RESULT: the corpus does not fall into clean design families ("
        + "; ".join(reasons)
        + f"). The k={best_k} partition below is reported for description only and is labelled provisional."
    )
    LOG.info("k selection: %s", verdict)
    return labels, KChoice(
        ks=ks,
        silhouettes=[float(s) for s in sils],
        null_p95=[float(x) for x in null_p95],
        null_mean=[float(x) for x in null_mean],
        null_eligible_p95=[float(x) for x in null_eligible_p95],
        null_eligible_share=[float(x) for x in null_eligible_share],
        null_max_p95=null_max_p95,
        null_max_mean=null_max_mean,
        null_max_draws=int(null_max_draws.size),
        p_selection_adjusted=p_selection_adjusted,
        beats_null_per_k=beats_null_per_k,
        beats_null_selection_adjusted=beats_null,
        largest_cluster_frac=[float(m) for m in largest],
        smallest_cluster_frac=[float(m) for m in smallest],
        eligible=list(eligible),
        best_k=best_k,
        best_silhouette=best_sil,
        cophenetic=coph,
        stability={int(c): float(v) for c, v in stab.items()},
        mean_stability=mean_stab,
        families_found=found,
        verdict=verdict,
        linkage_sensitivity=sens,
    )


# ---------------------------------------------------------------------------
# cluster description + documentation confounding
# ---------------------------------------------------------------------------


def cluster_tables(
    corpus: Corpus,
    dist: DistanceResult,
    labels: np.ndarray,
    choice: KChoice,
    *,
    n_markers: int = 5,
    n_examples: int = 3,
    large_cluster_share: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Membership, per-cluster summary (with the documentation check) and distinguishing values."""
    from scipy.stats import kruskal
    from sklearn.metrics import silhouette_samples

    idx = pd.Index(dist.ids, name="system_id")
    share = corpus.coded_share.reindex(idx)
    sil = silhouette_samples(dist.D, labels, metric="precomputed") if len(set(labels)) > 1 else np.full(len(labels), np.nan)
    members = pd.DataFrame(
        {
            "name": dist.names,
            "cluster": labels,
            "silhouette": sil,
            "coded_share": share.to_numpy(),
            "n_coded": (corpus.states == "value").sum(axis=1).reindex(idx).to_numpy(),
            "stratum": corpus.weights["stratum"].reindex(idx).to_numpy(),
            "weight": corpus.weights["weight"].reindex(idx).to_numpy(),
            "provisional": not choice.families_found,
        },
        index=idx,
    )

    lab = corpus.labels_complete.reindex(idx)
    marker_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for c in sorted({int(x) for x in labels}):
        inm = members["cluster"].to_numpy() == c
        scores: list[tuple[float, str, str, float, float, int, int]] = []
        for d in corpus.usable:
            col = lab[d.key]
            a = col[inm].dropna()
            b = col[~inm].dropna()
            if len(a) < 3 or len(b) < 3:
                continue
            pa = a.value_counts(normalize=True)
            pb = b.value_counts(normalize=True)
            for level in pa.index:
                diff = float(pa[level] - pb.get(level, 0.0))
                scores.append((abs(diff), d.key, str(level), float(pa[level]), float(pb.get(level, 0.0)), len(a), len(b)))
        scores.sort(reverse=True)
        seen: set[str] = set()
        rank = 0
        for _, key, level, p_in, p_out, n_in, n_out in scores:
            if key in seen:
                continue
            seen.add(key)
            rank += 1
            dim = next(d for d in corpus.dims if d.key == key)
            marker_rows.append(
                {
                    "cluster": c,
                    "rank": rank,
                    "dim_id": dim.id,
                    "dim_key": key,
                    "layer": dim.layer,
                    "level": level,
                    "share_in_cluster": p_in,
                    "share_outside": p_out,
                    "difference": p_in - p_out,
                    "n_coded_in_cluster": n_in,
                    "n_coded_outside": n_out,
                }
            )
            if rank >= n_markers:
                break
        sub = np.flatnonzero(inm)
        medoid_order = sub[np.argsort(dist.D[np.ix_(sub, sub)].mean(axis=1))] if sub.size else sub
        examples = [dist.names[i] for i in medoid_order[:n_examples]]
        summary_rows.append(
            {
                "cluster": c,
                "size": int(inm.sum()),
                "share_of_analysis_set": float(inm.mean()),
                "weight_sum": float(members.loc[inm, "weight"].sum()),
                "mean_coded_share": float(members.loc[inm, "coded_share"].mean()),
                "median_coded_share": float(members.loc[inm, "coded_share"].median()),
                "mean_silhouette": float(np.nanmean(sil[inm])) if inm.any() else float("nan"),
                "bootstrap_jaccard": choice.stability.get(c, float("nan")),
                "examples": "; ".join(examples),
                "top_markers": "; ".join(
                    f"{r['dim_key']}={r['level']} ({r['share_in_cluster']:.0%} vs {r['share_outside']:.0%})"
                    for r in marker_rows
                    if r["cluster"] == c
                ),
                "provisional": not choice.families_found,
            }
        )
    summary = pd.DataFrame(summary_rows)
    markers = pd.DataFrame(marker_rows)

    groups = [members.loc[members["cluster"] == c, "coded_share"].to_numpy() for c in sorted(set(labels))]
    groups = [g for g in groups if g.size > 0]
    pooled_distinct = np.unique(np.concatenate(groups)).size if groups else 0
    if len(groups) > 1 and pooled_distinct > 1:
        try:
            h, p = kruskal(*groups)
        except ValueError:
            h, p = float("nan"), float("nan")
    else:
        h, p = float("nan"), float("nan")
    spread = float(summary["mean_coded_share"].max() - summary["mean_coded_share"].min()) if len(summary) else float("nan")
    # A six-system cluster can swing the spread on its own, so also report it over the clusters big
    # enough to matter for the paper's claims.
    big = summary.loc[summary["share_of_analysis_set"] >= large_cluster_share] if len(summary) else summary
    spread_big = (
        float(big["mean_coded_share"].max() - big["mean_coded_share"].min()) if len(big) > 1 else float("nan")
    )
    confound = {
        "mean_coded_share_by_cluster": {int(r.cluster): r.mean_coded_share for r in summary.itertuples()},
        "spread_max_minus_min": spread,
        "large_cluster_min_share": large_cluster_share,
        "n_large_clusters": len(big),
        "spread_max_minus_min_large_clusters": spread_big,
        "kruskal_h": float(h),
        "kruskal_p": float(p),
    }
    return members, summary, markers, confound


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------


def _save(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for ext in ("svg", "pdf"):
        p = stem.with_suffix(f".{ext}")
        fig.savefig(p, format=ext, bbox_inches="tight")
        out.append(p)
    import matplotlib.pyplot as plt

    plt.close(fig)
    for p in out:
        LOG.info("wrote %s (%d bytes)", p, p.stat().st_size)
    return out


def _layer_bounds(dims: Sequence[Dimension]) -> list[int]:
    bounds = []
    for i in range(1, len(dims)):
        if dims[i].layer != dims[i - 1].layer:
            bounds.append(i)
    return bounds


def figure_matrix(table: pd.DataFrame, corpus: Corpus, stem: Path) -> list[Path]:
    """Two-panel 38x38 heatmap: complete pairs (design) beside NR-as-level (documentation)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dims = corpus.dims
    labels = [d.label for d in dims]
    fig, axes = plt.subplots(1, 2, figsize=(19.5, 9.6))
    panels = [
        ("v_corrected_complete", "(a) complete pairs only — DESIGN signal\n(both dimensions carry a value; n varies per cell)"),
        ("v_corrected_nr", "(b) not_reported as its own level — DOCUMENTATION behaviour\n(shown as a contrast; not evidence about design)"),
    ]
    vmax = float(np.nanmax([table["v_corrected_complete"].max(), table["v_corrected_nr"].max(), 0.1]))
    for ax, (col, title) in zip(axes, panels):
        mat = matrix_from_table(table, dims, col)
        ax.set_facecolor("#d9d9d9")
        im = ax.imshow(mat.to_numpy(dtype=float), cmap="viridis", vmin=0.0, vmax=vmax, interpolation="nearest")
        ax.set_title(title, fontsize=9.5, pad=8)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=6.2)
        ax.set_yticklabels(labels, fontsize=6.2)
        for b in _layer_bounds(dims):
            ax.axhline(b - 0.5, color="white", linewidth=1.1)
            ax.axvline(b - 0.5, color="white", linewidth=1.1)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cb.set_label("bias-corrected Cramer's V (Bergsma 2013)", fontsize=7.5)
        cb.ax.tick_params(labelsize=7)
    fig.suptitle(
        "Do harness design choices travel together? Pairwise association of the 38 coding dimensions",
        fontsize=12,
        y=0.995,
    )
    fig.text(
        0.5,
        -0.045,
        "Sequential scale: corrected Cramer's V is bounded in [0,1] and cannot be negative. Grey = dimension excluded "
        "(free-text identifier) or too few observations. unresolved cells excluded throughout.\n"
        "Panel (a) is the primary result; per-pair n, permutation p and BH q are in data/analysis/family_associations.csv. "
        "White lines separate schema layers. Rendered by scripts/analyse_families.py.",
        ha="center",
        fontsize=7.5,
        style="italic",
    )
    fig.tight_layout()
    return _save(fig, stem)


def figure_delta(table: pd.DataFrame, corpus: Corpus, stem: Path) -> list[Path]:
    """Diverging heatmap of (NR-as-level V) - (complete-pairs V): where silence fakes structure."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dims = corpus.dims
    labels = [d.label for d in dims]
    mat = matrix_from_table(table, dims, "delta_v_nr_minus_complete")
    flip = matrix_from_table(table, dims, "flips_conclusion")
    lim = float(np.nanmax(np.abs(mat.to_numpy(dtype=float)))) if np.isfinite(mat.to_numpy(dtype=float)).any() else 0.1
    lim = max(lim, 0.05)
    fig, ax = plt.subplots(figsize=(11.0, 9.6))
    ax.set_facecolor("#d9d9d9")
    im = ax.imshow(mat.to_numpy(dtype=float), cmap="RdBu_r", vmin=-lim, vmax=lim, interpolation="nearest")
    ys, xs = np.nonzero(np.nan_to_num(flip.to_numpy(dtype=float)) > 0)
    ax.plot(xs, ys, marker=".", markersize=1.8, linestyle="none", color="black")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=6.2)
    ax.set_yticklabels(labels, fontsize=6.2)
    for b in _layer_bounds(dims):
        ax.axhline(b - 0.5, color="white", linewidth=1.1)
        ax.axvline(b - 0.5, color="white", linewidth=1.1)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label("corrected V with not_reported as a level − corrected V on complete pairs", fontsize=7.5)
    cb.ax.tick_params(labelsize=7)
    ax.set_title(
        "How much of each apparent association is shared silence rather than shared design?",
        fontsize=11,
        pad=10,
    )
    fig.text(
        0.5,
        -0.06,
        "Diverging scale centred at zero because this difference, unlike V itself, can take either sign. Red = the pair looks "
        "more associated once\nsilence counts as a design choice (documentation behaviour). Blue = silence dilutes a real "
        "association. Dots mark pairs that change conclusion\n(significance flip at BH q<0.05 or |delta| above the flip "
        "threshold); they are listed in data/analysis/family_nr_flips.csv.",
        ha="center",
        fontsize=7.5,
        style="italic",
    )
    fig.tight_layout()
    return _save(fig, stem)


def figure_dendrogram(dist: DistanceResult, Z: np.ndarray, choice: KChoice, stem: Path) -> list[Path]:
    """Dendrogram beside the silhouette-vs-k curve with the marginal-preserving null band."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import dendrogram

    k = choice.best_k
    thresh = float((Z[-(k - 1), 2] + Z[-k, 2]) / 2) if Z.shape[0] >= k else float(Z[-1, 2])
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 7.0), gridspec_kw={"width_ratios": [2.05, 1.0]})
    ax = axes[0]
    dendrogram(Z, ax=ax, no_labels=True, color_threshold=thresh, above_threshold_color="#8a8a8a")
    ax.axhline(thresh, color="#b2182b", linestyle="--", linewidth=1.0)
    ax.text(
        0.99,
        thresh,
        f" cut at k={k}" + ("" if choice.families_found else " (PROVISIONAL)"),
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=8,
        color="#b2182b",
    )
    ax.set_title(
        f"Average-linkage (UPGMA) dendrogram, Gower distance on coded cells only\n"
        f"{len(dist.ids)} systems, {len(dist.dims_used)} dimensions, cophenetic r = {choice.cophenetic:.2f}",
        fontsize=10,
    )
    ax.set_ylabel("Gower distance", fontsize=9)
    ax.set_xlabel("harnesses (leaf labels omitted; see data/analysis/family_clusters.csv)", fontsize=8.5)
    ax.tick_params(labelsize=8)

    ax2 = axes[1]
    ax2.plot(choice.ks, choice.silhouettes, color="#2166ac", linewidth=1.2, label="observed")
    ks_arr = np.array(choice.ks)
    sil_arr = np.array(choice.silhouettes, dtype=float)
    el = np.array(choice.eligible, dtype=bool)
    ax2.plot(ks_arr[el], sil_arr[el], marker="o", markersize=4.5, linestyle="none", color="#2166ac",
             label="no cluster above the dominance ceiling")
    if (~el).any():
        ax2.plot(ks_arr[~el], sil_arr[~el], marker="x", markersize=5, linestyle="none", color="#999999",
                 label="ineligible: one cluster holds more\nthan the dominance ceiling (outlier peel)")
    if not all(math.isnan(x) for x in choice.null_p95):
        ax2.plot(choice.ks, choice.null_p95, linestyle="--", color="#b2182b", linewidth=1.1,
                 label="null 95th pct (dimensions permuted\nwithin observed cells)")
        ax2.plot(choice.ks, choice.null_mean, linestyle=":", color="#b2182b", linewidth=0.9, label="null mean")
    ax2.axvline(k, color="#666666", linewidth=0.8)
    ax2.set_xlabel("number of clusters k", fontsize=9)
    ax2.set_ylabel("mean silhouette (precomputed Gower distance)", fontsize=9)
    ax2.set_title(
        ("Families supported" if choice.families_found else "Families NOT supported (negative result)")
        + f"\nbest k={k}, silhouette {choice.best_silhouette:.3f}, stability {choice.mean_stability:.2f}",
        fontsize=10,
    )
    ax2.legend(fontsize=7, loc="best")
    ax2.tick_params(labelsize=8)
    ax2.grid(alpha=0.25, linewidth=0.5)

    fig.text(
        0.5,
        -0.05,
        "Gower distance averages, for each pair of systems, only the dimensions BOTH systems report: not_reported contributes "
        "nothing and unresolved cells are excluded,\nso shared silence cannot make two harnesses look alike. The null preserves "
        "every dimension's marginal distribution and every system's missingness pattern\nwhile destroying cross-dimension "
        "association. Rendered by scripts/analyse_families.py.",
        ha="center",
        fontsize=7.5,
        style="italic",
    )
    fig.tight_layout()
    return _save(fig, stem)


def figure_mds(
    dist: DistanceResult, members: pd.DataFrame, choice: KChoice, confound: dict[str, Any], stem: Path, seed: int
) -> list[Path]:
    """MDS of the Gower distance coloured by cluster and by documentation completeness."""
    import matplotlib

    matplotlib.use("Agg")
    import inspect

    import matplotlib.pyplot as plt
    from sklearn.manifold import MDS

    params = inspect.signature(MDS.__init__).parameters
    kwargs: dict[str, Any] = {"n_components": 2, "random_state": seed, "n_init": 1, "max_iter": 300,
                              "normalized_stress": "auto"}
    # sklearn renamed `dissimilarity="precomputed"` to `metric="precomputed"`; support both
    if "metric" in params and str(params["dissimilarity"].default) == "deprecated":
        kwargs["metric"] = "precomputed"
    else:
        kwargs["dissimilarity"] = "precomputed"
    if "init" in params:
        kwargs["init"] = "random"
    xy = MDS(**kwargs).fit_transform(dist.D)
    labels = members["cluster"].to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 6.4))
    cmap = plt.get_cmap("tab10")
    for c in sorted(set(labels)):
        m = labels == c
        axes[0].scatter(xy[m, 0], xy[m, 1], s=11, alpha=0.75, color=cmap((c - 1) % 10),
                        label=f"cluster {c} (n={int(m.sum())}, coded {members.loc[m, 'coded_share'].mean():.0%})")
    axes[0].legend(fontsize=6.6, loc="best", markerscale=1.4)
    axes[0].set_title(
        f"(a) cluster at k={choice.best_k}" + ("" if choice.families_found else " — PROVISIONAL, families not supported"),
        fontsize=10,
    )
    sc = axes[1].scatter(xy[:, 0], xy[:, 1], s=11, c=members["coded_share"].to_numpy(), cmap="cividis", alpha=0.85)
    cb = fig.colorbar(sc, ax=axes[1], fraction=0.046, pad=0.02)
    cb.set_label("share of the 38 dimensions the system reports", fontsize=8)
    axes[1].set_title("(b) documentation completeness", fontsize=10)
    for ax in axes:
        ax.set_xlabel("MDS 1", fontsize=9)
        ax.set_ylabel("MDS 2", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.2, linewidth=0.5)
    fig.suptitle("Are the candidate design families really documentation strata?", fontsize=12)
    fig.text(
        0.5,
        -0.06,
        "If the gradient in (b) reproduces the partition in (a), the 'families' are documentation artefacts rather than design "
        f"families. Per-cluster mean coded share spans {confound['spread_max_minus_min']:.1%} across all clusters and "
        f"{confound['spread_max_minus_min_large_clusters']:.1%} across the {confound['n_large_clusters']} clusters holding at "
        f"least {confound['large_cluster_min_share']:.0%} of the analysis set\n(Kruskal-Wallis H = {confound['kruskal_h']:.1f}, "
        f"p = {confound['kruskal_p']:.2g}); the per-cluster numbers are in data/analysis/family_cluster_summary.csv. "
        "Metric MDS on the same Gower distance as the dendrogram. Rendered by scripts/analyse_families.py.",
        ha="center",
        fontsize=7.5,
        style="italic",
    )
    fig.tight_layout()
    return _save(fig, stem)


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def _json_safe(obj: Any) -> Any:
    """NaN/Inf are not valid JSON; write them as null so strict parsers can read the summary."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not math.isfinite(float(obj)) else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def diagnostics_table(corpus: Corpus) -> pd.DataFrame:
    rows = []
    n = len(corpus.ids)
    for d in corpus.dims:
        p = corpus.prep[d.key]
        rows.append(
            {
                "dim_id": d.id,
                "dim_key": d.key,
                "layer": d.layer,
                "layer_name": corpus.layers.get(d.layer, d.layer),
                "name": d.name,
                "type": d.type,
                "multi": d.multi,
                "n_allowed_values": len(d.values),
                "n_value": p.n_value,
                "n_not_reported": p.n_not_reported,
                "n_unresolved": p.n_unresolved,
                "n_missing": p.n_missing,
                "coded_share": p.n_value / n if n else float("nan"),
                "distinct_raw_values": p.distinct_raw,
                "treatment": p.treatment,
                "n_levels_used": p.n_levels,
                "n_levels_pooled_as_rare": p.n_levels_pooled,
                "n_systems_pooled_as_rare": p.n_pooled_systems,
                "bin_edges": p.bin_edges,
                "included_in_matrix": p.included,
                "exclusion_reason": p.reason,
            }
        )
    return pd.DataFrame(rows)


def run(args: argparse.Namespace) -> dict[str, Any]:
    dims, layers = load_dimensions(Path(args.dimensions))
    systems = load_systems(Path(args.systems), limit=args.limit)
    corpus = build_corpus(
        systems,
        dims,
        layers,
        Path(args.frame) if args.frame else None,
        min_level_count=args.min_level_count,
        n_bins=args.n_bins,
        string_max_unique=args.string_max_unique,
    )
    tables_dir = Path(args.tables)
    figs_dir = Path(args.figures)
    tables_dir.mkdir(parents=True, exist_ok=True)

    diag = diagnostics_table(corpus)
    diag.to_csv(tables_dir / "family_dimension_diagnostics.csv", index=False)
    LOG.info("wrote %s", tables_dir / "family_dimension_diagnostics.csv")

    LOG.info("computing %d pairwise associations with %d permutations each (both treatments)",
             len(dims) * (len(dims) - 1) // 2, args.n_perm)
    assoc = association_table(
        corpus, n_perm=args.n_perm, seed=args.seed, alpha=args.alpha, flip_delta=args.flip_delta
    )
    assoc.to_csv(tables_dir / "family_associations.csv", index=False)
    top_cols = [
        "dim_a_id", "dim_a_key", "dim_b_id", "dim_b_key", "layer_a", "layer_b", "same_layer",
        "n_complete", "v_corrected_complete", "v_raw_complete", "levels_a_complete", "levels_b_complete",
        "p_perm_complete", "q_bh_complete", "q_holm_complete",
        "v_corrected_complete_weighted", "n_eff_complete_weighted",
        "n_nr", "v_corrected_nr", "q_bh_nr", "delta_v_nr_minus_complete", "flips_conclusion", "flip_kind",
    ]
    top = assoc.loc[~assoc["excluded"] & assoc["v_corrected_complete"].notna(), top_cols].head(args.n_top)
    top.to_csv(tables_dir / "family_associations_top.csv", index=False)
    flips = assoc.loc[assoc["flips_conclusion"], top_cols].sort_values(
        "delta_v_nr_minus_complete", ascending=False
    )
    flips.to_csv(tables_dir / "family_nr_flips.csv", index=False)
    for p in ("family_associations.csv", "family_associations_top.csv", "family_nr_flips.csv"):
        LOG.info("wrote %s", tables_dir / p)

    summary: dict[str, Any] = {
        "generated_by": "scripts/analyse_families.py",
        "inputs": {
            "systems": str(args.systems),
            "dimensions": str(args.dimensions),
            "coding_frame": str(args.frame),
        },
        "parameters": {
            k: getattr(args, k)
            for k in (
                "n_perm", "n_null", "n_boot", "seed", "alpha", "flip_delta", "min_level_count",
                "n_bins", "string_max_unique", "linkage", "kmax", "min_coded_share", "min_overlap",
                "min_silhouette", "min_stability", "max_cluster_frac", "confound_spread",
            )
        },
        "cells": {
            state: int((corpus.states == state).sum().sum())
            for state in ("value", "not_reported", "unresolved", "missing")
        },
        "dimensions_excluded": {
            d.key: corpus.prep[d.key].reason for d in corpus.dims if not corpus.prep[d.key].included
        },
        "multi_valued_treatment": (
            "value-set as a single composite level for the association matrix (not one-hot); "
            "Jaccard distance between value sets for the clustering"
        ),
        "association": {
            "n_pairs": len(assoc),
            "n_pairs_excluded": int(assoc["excluded"].sum()),
            "n_significant_complete_bh": int(assoc["sig_complete"].sum()),
            "n_significant_nr_bh": int(assoc["sig_nr"].sum()),
            "n_flips": int(assoc["flips_conclusion"].sum()),
            "flip_kinds": {k: int(v) for k, v in assoc.loc[assoc["flips_conclusion"], "flip_kind"].value_counts().items()},
            "median_n_complete": float(assoc["n_complete"].median(skipna=True)),
            "min_n_complete": float(assoc["n_complete"].min(skipna=True)),
            "max_n_complete": float(assoc["n_complete"].max(skipna=True)),
            "mean_v_corrected_complete": float(assoc["v_corrected_complete"].mean(skipna=True)),
            "mean_v_corrected_nr": float(assoc["v_corrected_nr"].mean(skipna=True)),
            "mean_v_raw_complete": float(assoc["v_raw_complete"].mean(skipna=True)),
            "top10_complete": [
                {
                    "pair": f"{r.dim_a_id} {r.dim_a_key} x {r.dim_b_id} {r.dim_b_key}",
                    "n": int(r.n_complete),
                    "v_corrected": float(r.v_corrected_complete),
                    "v_raw": float(r.v_raw_complete),
                    "q_bh": float(r.q_bh_complete),
                    "v_corrected_nr": float(r.v_corrected_nr),
                }
                for r in top.head(10).itertuples()
            ],
        },
    }

    figures: list[Path] = []
    if not args.no_figures:
        figures += figure_matrix(assoc, corpus, figs_dir / "family_association_matrix")
        figures += figure_delta(assoc, corpus, figs_dir / "family_association_delta")

    if args.no_cluster:
        summary["clustering"] = {"skipped": True}
    else:
        dist = build_distance(corpus, min_coded_share=args.min_coded_share, min_overlap=args.min_overlap)
        labels, choice = choose_k(
            corpus,
            dist,
            method=args.linkage,
            kmax=args.kmax,
            n_null=args.n_null,
            n_boot=args.n_boot,
            boot_frac=args.boot_frac,
            min_silhouette=args.min_silhouette,
            min_stability=args.min_stability,
            max_cluster_frac=args.max_cluster_frac,
            sensitivity=not args.no_linkage_sensitivity,
            seed=args.seed,
        )
        members, csummary, markers, confound = cluster_tables(
            corpus, dist, labels, choice, n_markers=args.n_markers,
            large_cluster_share=args.large_cluster_share,
        )
        members.to_csv(tables_dir / "family_clusters.csv")
        csummary.to_csv(tables_dir / "family_cluster_summary.csv", index=False)
        markers.to_csv(tables_dir / "family_cluster_markers.csv", index=False)
        for p in ("family_clusters.csv", "family_cluster_summary.csv", "family_cluster_markers.csv"):
            LOG.info("wrote %s", tables_dir / p)
        conf_all = bool(
            not math.isnan(confound["spread_max_minus_min"])
            and confound["spread_max_minus_min"] >= args.confound_spread
        )
        conf_big = bool(
            not math.isnan(confound["spread_max_minus_min_large_clusters"])
            and confound["spread_max_minus_min_large_clusters"] >= args.confound_spread
        )
        # A handful of systems can swing the all-cluster spread, so the headline flag follows the
        # clusters big enough to carry a claim whenever there are at least two of them.
        confounded = conf_big if confound["n_large_clusters"] >= 2 else conf_all
        confound["confounded_all_clusters"] = conf_all
        confound["confounded_large_clusters"] = conf_big
        confound["note"] = (
            "documentation completeness differs sharply between clusters; treat the partition as a "
            "documentation artefact"
            if confounded
            else (
                "the clusters that carry the claims do not differ materially in documentation "
                "completeness"
                + (
                    "; some small clusters do, so the all-cluster spread is flagged"
                    if conf_all
                    else ""
                )
            )
        )
        summary["clustering"] = {
            "n_systems": len(dist.ids),
            "n_dimensions_used": len(dist.dims_used),
            "dimensions_used": dist.dims_used,
            "n_dropped_low_coverage": len(dist.dropped_low_coverage),
            "n_dropped_low_overlap": len(dist.dropped_low_overlap),
            "distance": "Gower over coded cells only (mismatch / Jaccard on value sets / |x-y| over range)",
            "linkage": args.linkage,
            "cophenetic_correlation": choice.cophenetic,
            "ks": choice.ks,
            "silhouettes": choice.silhouettes,
            "null_p95": choice.null_p95,
            "null_mean": choice.null_mean,
            "null_eligible_p95": choice.null_eligible_p95,
            "null_eligible_share_of_draws": choice.null_eligible_share,
            "null_max_over_eligible_k_p95": choice.null_max_p95,
            "null_max_over_eligible_k_mean": choice.null_max_mean,
            "null_max_over_eligible_k_draws": choice.null_max_draws,
            "p_selection_adjusted": choice.p_selection_adjusted,
            "beats_null_per_k_at_selected_k": choice.beats_null_per_k,
            "beats_null_selection_adjusted": choice.beats_null_selection_adjusted,
            "null_comparison_note": (
                "the per-k figures are diagnostics; the gate is the selection-adjusted comparison, "
                "because k was chosen by maximising the observed silhouette over the eligible k. "
                "The reference distribution is the maximum over eligible k of each null draw's own "
                "silhouette curve, with the same largest-cluster eligibility filter applied to the "
                "null as to the observed curve."
            ),
            "largest_cluster_share_by_k": choice.largest_cluster_frac,
            "smallest_cluster_share_by_k": choice.smallest_cluster_frac,
            "k_eligible": choice.eligible,
            "best_k": choice.best_k,
            "best_silhouette": choice.best_silhouette,
            "bootstrap_stability_per_cluster": choice.stability,
            "mean_bootstrap_stability": choice.mean_stability,
            "linkage_sensitivity": choice.linkage_sensitivity,
            "linkages_not_run": {
                "ward": "inadmissible: assumes Euclidean coordinates, which a Gower distance does not provide",
                "centroid": "inadmissible: assumes Euclidean coordinates",
            },
            "families_found": choice.families_found,
            "verdict": choice.verdict,
            "documentation_confounding": confound,
            "documentation_confounded": confounded,
            "clusters": csummary.to_dict(orient="records"),
        }
        if not args.no_figures:
            Z = linkage_matrix(dist.D, method=args.linkage)
            figures += figure_dendrogram(dist, Z, choice, figs_dir / "family_dendrogram")
            figures += figure_mds(dist, members, choice, confound, figs_dir / "family_clusters_mds", args.seed)

    summary["figures"] = [str(p) for p in figures]
    out = tables_dir / "family_summary.json"
    out.write_text(json.dumps(_json_safe(summary), indent=2, default=str), encoding="utf-8")
    LOG.info("wrote %s", out)
    _print_report(summary, assoc, top)
    return summary


def _print_report(summary: dict[str, Any], assoc: pd.DataFrame, top: pd.DataFrame) -> None:
    a = summary["association"]
    print()
    print("=" * 100)
    print("TEN STRONGEST ASSOCIATIONS ON COMPLETE PAIRS (bias-corrected Cramer's V; n = both dimensions coded)")
    print("=" * 100)
    print(f"{'pair':<66}{'n':>6}{'V~':>7}{'V raw':>7}{'q_BH':>9}{'V~ NR':>7}")
    for r in top.head(10).itertuples():
        pair = f"{r.dim_a_id} {r.dim_a_key} x {r.dim_b_id} {r.dim_b_key}"
        print(
            f"{pair[:65]:<66}{int(r.n_complete):>6}{r.v_corrected_complete:>7.3f}"
            f"{r.v_raw_complete:>7.3f}{r.q_bh_complete:>9.4f}{r.v_corrected_nr:>7.3f}"
        )
    print(
        f"\ncomplete-pairs n ranges {a['min_n_complete']:.0f}-{a['max_n_complete']:.0f} "
        f"(median {a['median_n_complete']:.0f}); mean corrected V {a['mean_v_corrected_complete']:.3f} on complete "
        f"pairs vs {a['mean_v_corrected_nr']:.3f} with not_reported as a level; "
        f"{a['n_significant_complete_bh']}/{a['n_pairs']} pairs significant at BH q<0.05 (complete) vs "
        f"{a['n_significant_nr_bh']} (NR-as-level)."
    )
    print(
        "The weighted column is a sensitivity only: the O stratum carries weight ~48, so the Kish "
        "effective n behind a weighted pair is far below its raw n (column n_eff_complete_weighted) "
        "and the bias correction zeroes several weighted V values that are clearly non-zero unweighted."
    )
    flips = assoc.loc[assoc["flips_conclusion"]]
    counts = flips["flip_kind"].value_counts()
    print(f"\n{len(flips)} pairs change conclusion between the two treatments:")
    for kind, cnt in counts.items():
        print(f"  {cnt:>4}  {kind}")
    print("\nLargest inflations by shared silence:")
    for r in flips.sort_values("delta_v_nr_minus_complete", ascending=False).head(10).itertuples():
        print(
            f"  {r.dim_a_key} x {r.dim_b_key}: V~ {r.v_corrected_complete:.3f} (n={int(r.n_complete)}) -> "
            f"{r.v_corrected_nr:.3f} (n={int(r.n_nr)})  [{r.flip_kind}]"
        )
    c = summary.get("clustering", {})
    if c and not c.get("skipped"):
        print("\n" + "=" * 100)
        print("CLUSTERING")
        print("=" * 100)
        print(c["verdict"])
        print(
            "silhouette by k: "
            + ", ".join(
                f"k={k}: {s:.3f} (null p95 {n:.3f}, largest cluster {m:.0%}{'' if e else ', ineligible'})"
                for k, s, n, m, e in zip(
                    c["ks"], c["silhouettes"], c["null_p95"], c["largest_cluster_share_by_k"], c["k_eligible"]
                )
            )
        )
        print(
            f"n={c['n_systems']} systems, {c['linkage']} linkage, cophenetic r={c['cophenetic_correlation']:.3f}, "
            f"mean bootstrap Jaccard {c['mean_bootstrap_stability']:.3f}"
        )
        print(
            f"selected statistic {c['best_silhouette']:.3f} at k={c['best_k']} against the "
            f"distribution of the null's MAXIMUM over eligible k: 95th percentile "
            f"{c['null_max_over_eligible_k_p95']:.3f}, mean "
            f"{c['null_max_over_eligible_k_mean']:.3f} over "
            f"{c['null_max_over_eligible_k_draws']} draws, selection-adjusted p = "
            f"{c['p_selection_adjusted']:.3f} -> "
            + ("clears" if c["beats_null_selection_adjusted"] else "does NOT clear")
            + " the null bar (per-k comparison at the selected k: "
            + ("clears" if c["beats_null_per_k_at_selected_k"] else "does not clear") + ")"
        )
        conf = c["documentation_confounding"]
        print(
            "documentation confounding: mean coded share per cluster "
            + ", ".join(f"{k}: {v:.1%}" for k, v in conf["mean_coded_share_by_cluster"].items())
            + f" (spread {conf['spread_max_minus_min']:.1%} over all clusters, "
            f"{conf['spread_max_minus_min_large_clusters']:.1%} over the {conf['n_large_clusters']} clusters holding "
            f">={conf['large_cluster_min_share']:.0%} of the analysis set; Kruskal-Wallis "
            f"H={conf['kruskal_h']:.1f}, p={conf['kruskal_p']:.2g})"
            + (
                "  -> CONFOUNDED: the clusters track documentation, not only design"
                if c["documentation_confounded"]
                else ""
            )
            + "\n  " + conf.get("note", "")
        )
        for cl in c["clusters"]:
            print(
                f"  cluster {cl['cluster']}: n={cl['size']} (weighted {cl['weight_sum']:.0f}), coded "
                f"{cl['mean_coded_share']:.0%}, silhouette {cl['mean_silhouette']:.2f}, stability "
                f"{cl['bootstrap_jaccard']:.2f}\n      examples: {cl['examples']}\n      markers: {cl['top_markers']}"
            )
    print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(__doc__ or "").strip().split("\n")[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--systems", default=str(REPO / "data/systems.json"))
    p.add_argument("--dimensions", default=str(REPO / "schema/dimensions.json"))
    p.add_argument("--frame", default=str(REPO / "data/coding_frame.csv"), help="stratum and weight join")
    p.add_argument("--tables", default=str(REPO / "data/analysis"), help="output directory for CSV/JSON")
    p.add_argument("--figures", default=str(REPO / "paper/figures"), help="output directory for SVG/PDF")
    p.add_argument("--n-perm", type=int, default=20000,
                   help="permutations per pair per treatment; the smallest attainable p is "
                        "1/(n_perm+1), so a low value ties many pairs at the floor and makes the "
                        "BH ordering inside the rejected set arbitrary")
    p.add_argument("--n-null", type=int, default=500,
                   help="marginal-preserving null replicates for the silhouette; a 95th "
                        "percentile cannot be estimated from a handful of draws")
    p.add_argument("--n-boot", type=int, default=200,
                   help="bootstrap subsamples for cluster stability")
    p.add_argument("--boot-frac", type=float, default=0.8)
    p.add_argument("--seed", type=int, default=20260924)
    p.add_argument("--alpha", type=float, default=0.05, help="BH FDR threshold")
    p.add_argument("--flip-delta", type=float, default=0.15, help="|delta V| counted as a changed conclusion")
    p.add_argument("--min-level-count", type=int, default=5, help="levels rarer than this are pooled as rare (1 disables)")
    p.add_argument("--n-bins", type=int, default=4, help="quantile bins for integer/date dimensions")
    p.add_argument("--string-max-unique", type=float, default=0.5, help="free-text exclusion threshold")
    p.add_argument("--linkage", default="average", choices=["average", "complete", "single", "weighted"])
    p.add_argument("--kmax", type=int, default=15, help="largest number of clusters considered")
    p.add_argument("--min-coded-share", type=float, default=0.5, help="drop systems coded on less than this share")
    p.add_argument("--min-overlap", type=int, default=5, help="minimum shared coded dimensions per system pair")
    p.add_argument("--min-silhouette", type=float, default=0.25, help="pre-stated silhouette floor to declare families")
    p.add_argument("--min-stability", type=float, default=0.60, help="pre-stated bootstrap Jaccard floor")
    p.add_argument("--max-cluster-frac", type=float, default=0.90,
                   help="a k where one cluster still holds more than this share of the analysis set "
                        "is an outlier peel, not a partition, and cannot win the silhouette")
    p.add_argument("--no-linkage-sensitivity", action="store_true",
                   help="skip the silhouette curve for the other admissible linkages")
    p.add_argument("--confound-spread", type=float, default=0.15, help="coded-share spread that flags confounding")
    p.add_argument("--n-top", type=int, default=50, help="rows in the ranked association table")
    p.add_argument("--n-markers", type=int, default=5, help="distinguishing dimensions per cluster")
    p.add_argument("--large-cluster-share", type=float, default=0.05,
                   help="clusters at least this big are also reported separately in the "
                        "documentation-confounding check, so a handful of systems cannot swing it")
    p.add_argument("--limit", type=int, default=None, help="use only the first N systems (debugging)")
    p.add_argument("--no-figures", action="store_true")
    p.add_argument("--no-cluster", action="store_true")
    p.add_argument("--quiet", action="store_true")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
