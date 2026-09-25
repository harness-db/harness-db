"""Design-based estimator for the stratified HARNESS-DB sample.

The released systems were drawn from a 6,504-system sampling frame in three strata: H (the
high-visibility stratum, coded exhaustively, weight 1), P (weight 683/150 = 4.5533) and O
(weight 4,837/100 = 48.37). A weighted estimate is the field-level estimate for the frame; an
unweighted one describes the coded set.

Every weighted estimate is a stratified ratio estimator with the SYSTEM as the sampling unit
(that is what was drawn):

    R = sum_i w_i y_i / sum_i w_i x_i

over the systems with ``w_i > 0``, where ``x_i`` is the system's number of cells in the base and
``y_i`` its number of cells with the property (``x_i = 1`` for a single dimension). The design SE
is the Taylor linearisation with a finite-population correction, systems as clusters:

    Var(R) = sum_h N_h^2 (1 - n_h/N_h) s2_h / n_h / X^2,   s2_h = var(y - R x) within stratum h,
    X = N * sum(w x) / sum(w),   N = sum of N_h over the strata present,

so the complete stratum H contributes (almost) no variance. With one row per system this is the
stratified proportion variance sum_h (N_h/N)^2 (1 - n_h/N_h) p_h(1-p_h)/(n_h-1). It is the
estimator of ``weighted_share`` in ``scripts/analyse_descriptives.py``, so the loader reproduces
the manuscript's rates and SEs (by dimension and by layer). Systems with weight 0 (the 23 coded
outside the draw) never enter a weighted estimate or its SE.
"""

from __future__ import annotations

import math

import numpy as np


def ratio_estimate(y: np.ndarray, x: np.ndarray, w: np.ndarray, stratum: np.ndarray,
                   strata_sizes: dict[str, float]) -> tuple[float, float, float, int]:
    """Weighted ratio sum(w*y)/sum(w*x), its design SE, the weighted base sum(w*x), and n.

    One row per system. Only rows with ``w > 0`` and ``x > 0`` enter (a system with no cell in
    the base says nothing about the rate). Returns NaN rate and SE when the weighted base is zero.
    ``N`` in the SE is the frame size of the strata that have rows, so a single-stratum domain
    (``not_reported(by="stratum")``) gets that stratum's own SE.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    w = np.asarray(w, dtype=float)
    stratum = np.asarray(stratum, dtype=object)
    keep = (w > 0) & (x > 0)
    y, x, w, stratum = y[keep], x[keep], w[keep], stratum[keep]
    base = float((w * x).sum())
    n = int(keep.sum())
    if base <= 0:
        return float("nan"), float("nan"), 0.0, n
    rate = float((w * y).sum() / base)
    present = {h: big_n for h, big_n in strata_sizes.items() if big_n > 0 and (stratum == h).any()}
    x_total = sum(present.values()) * base / float(w.sum())
    var = 0.0
    for h, big_n in present.items():
        m = stratum == h
        n_h = int(m.sum())
        if n_h < 2:
            continue
        e = y[m] - rate * x[m]
        fpc = max(0.0, 1.0 - n_h / float(big_n))
        var += big_n ** 2 * fpc * float(e.var(ddof=1)) / n_h
    se = math.sqrt(var) / x_total if x_total > 0 else float("nan")
    return rate, float(se), base, n
