"""Tests for scripts/analyse_descriptives.py (Phase 7 tasks 47 and 50).

No network, no model calls: everything runs on a hand-built fixture whose weights, cell states and
release years are known, so each expected number can be written out by hand in the assertion.

The fixture is a 2-layer, 4-dimension schema over a 24-system census:

    stratum H  4 systems, all coded, weight 1     (complete stratum)
    stratum O 20 systems, 8 coded,  weight 2.5    (1-in-2.5 sample)

so the weighted and unweighted pictures must differ, and the difference is computable on paper.
"""

import csv
import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyse_descriptives as ad

N_H, N_O = 4, 20
W_H, W_O = 1.0, 2.5
CODED_H = ["h0", "h1", "h2", "h3"]
CODED_O = ["o0", "o1", "o2", "o3", "o4", "o5", "o6", "o7"]
# 4 systems per release year, so a threshold of 3 keeps every year and 5 suppresses every year
YEARS = {"h0": 2023, "h1": 2024, "h2": 2025, "h3": 2023,
         "o0": 2023, "o1": 2023, "o2": 2024, "o3": 2024,
         "o4": 2024, "o5": 2025, "o6": 2025, "o7": 2025}

DIMENSIONS = {
    "schema_version": "test-1",
    "layers": [{"id": "X", "name": "Layer ex"}, {"id": "Y", "name": "Layer why"}],
    "dimensions": [
        {"id": "X1", "key": "alpha", "layer": "X", "name": "Alpha", "type": "enum",
         "multi": False, "values": ["a", "b", "c", "d"]},
        {"id": "X2", "key": "beta", "layer": "X", "name": "Beta", "type": "enum",
         "multi": True, "values": ["p", "q"]},
        {"id": "Y1", "key": "gamma", "layer": "Y", "name": "Gamma", "type": "enum",
         "multi": False, "values": ["g1", "g2"]},
        {"id": "Y2", "key": "delta", "layer": "Y", "name": "Delta", "type": "integer",
         "multi": False},
    ],
}


def _cell(value=None, not_reported=False, unresolved=False):
    cell = {"value": value, "confidence": "high", "not_reported": not_reported, "coder": "fixture"}
    if unresolved:
        cell["unresolved"] = True
    return cell


def _coding(sid: str) -> dict:
    """The three states, placed so every expected number below can be derived by hand.

    alpha: H systems coded "a"; o0-o3 coded "b"; o4 UNRESOLVED; o5-o7 not_reported.
    beta:  every coded system carries ["p", "q"] except o0-o3 which carry ["p"].
    gamma: alternates g1/g2 by index so entropy is non-degenerate per year.
    delta: an integer, so it must be tabulated but never given an entropy.
    """
    idx = int(sid[1:])
    is_h = sid.startswith("h")
    if is_h:
        alpha = _cell("a")
    elif idx <= 3:
        alpha = _cell("b")
    elif idx == 4:
        alpha = _cell(unresolved=True)
    else:
        alpha = _cell(not_reported=True)
    beta = _cell(["p", "q"]) if is_h or idx > 3 else _cell(["p"])
    gamma = _cell("g1" if idx % 2 == 0 else "g2")
    delta = _cell(idx + 1)
    return {"alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta}


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> dict:
    """Write the fixture corpus to disk in the exact shapes the script reads."""
    d = tmp_path_factory.mktemp("corpus")
    systems = [{"id": sid, "name": sid.upper(), "papers": [f"p:{sid}"], "coding": _coding(sid)}
               for sid in CODED_H + CODED_O]
    (d / "systems.json").write_text(json.dumps(systems), encoding="utf-8")
    (d / "dimensions.json").write_text(json.dumps(DIMENSIONS), encoding="utf-8")

    frame_rows = []
    for sid in CODED_H:
        frame_rows.append({"system_id": sid, "stratum": "H", "coded": "1", "weight": W_H})
    for sid in CODED_O:
        frame_rows.append({"system_id": sid, "stratum": "O", "coded": "1", "weight": W_O})
    for i in range(N_O - len(CODED_O)):  # uncoded census members: they fix N_h, not the estimates
        frame_rows.append({"system_id": f"u{i}", "stratum": "O", "coded": "0", "weight": 0})
    with (d / "coding_frame.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["system_id", "stratum", "coded", "weight"])
        w.writeheader()
        w.writerows(frame_rows)

    with (d / "systems_candidates.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["system_id", "release_date"])
        w.writeheader()
        for sid, year in YEARS.items():
            w.writerow({"system_id": sid, "release_date": f"{year}-06-01"})

    return {"dir": d, "systems": systems}


@pytest.fixture(scope="module")
def parts(corpus) -> dict:
    """Build the intermediate frames once; every table-level test reads from here."""
    d = corpus["dir"]
    dims = ad.load_json(d / "dimensions.json")
    frame_rows = ad.read_csv_rows(d / "coding_frame.csv")
    frame = {r["system_id"]: r for r in frame_rows}
    harvested = {r["system_id"]: r["release_date"]
                 for r in ad.read_csv_rows(d / "systems_candidates.csv")}
    strata = ad.strata_sizes_from_frame(frame_rows)
    cells = ad.build_cells(corpus["systems"], dims, frame, harvested, "candidates")
    return {
        "dims": dims, "strata": strata, "cells": cells,
        "dists": ad.value_distributions(cells, dims, strata),
        "under": ad.under_reporting_by_dimension(cells, strata),
        "layer_year": ad.under_reporting_layer_year(cells, strata, 3),
        "entropy": ad.entropy_by_dimension_year(cells, dims, 3, 200, 7),
    }


# ------------------------------------------------------------------ the entropy estimator itself


def test_entropy_plugin_is_zero_for_a_single_valued_dimension():
    assert ad.entropy_plugin([17]) == 0.0
    assert ad.entropy_plugin([17, 0, 0]) == 0.0


def test_entropy_plugin_is_log_k_for_a_uniform_dimension():
    for k in (2, 3, 4, 7):
        assert ad.entropy_plugin([10] * k) == pytest.approx(math.log(k))


def test_miller_madow_adds_exactly_the_named_correction():
    counts = [10] * 4
    n, k = 40, 4
    assert ad.entropy_miller_madow(counts) == pytest.approx(math.log(k) + (k - 1) / (2 * n))
    # the correction vanishes on a single-valued sample, so the 0 anchor survives it
    assert ad.entropy_miller_madow([17]) == 0.0
    # and it is a correction, not the estimate: it shrinks as 1/n
    assert (ad.entropy_miller_madow([100] * 4) - math.log(4)) < (
        ad.entropy_miller_madow([5] * 4) - math.log(4))


def test_miller_madow_corrects_upward_because_the_plugin_is_biased_down():
    counts = [3, 2, 1]
    assert ad.entropy_miller_madow(counts) > ad.entropy_plugin(counts)


# ------------------------------------------------------- weighted vs unweighted, on known weights


def test_weighted_and_unweighted_not_reported_rates_differ_as_the_design_implies(parts):
    """alpha: 3 of the 11 non-unresolved systems are not_reported, and all 3 are stratum O.

    unweighted 3/11 = 0.2727; weighted (3 x 2.5) / (4 x 1 + 4 x 2.5 + 3 x 2.5) = 7.5/21.5 = 0.3488.
    The weighted rate must be the higher one: under-reporting sits in the sampled stratum.
    """
    row = parts["under"].set_index("key").loc["alpha"]
    assert row["n_base"] == 11 and row["n_not_reported"] == 3
    assert row["rate_unweighted"] == pytest.approx(3 / 11)
    assert row["rate_weighted"] == pytest.approx(7.5 / 21.5)
    assert row["rate_weighted"] > row["rate_unweighted"]
    assert row["weighted_minus_unweighted"] == pytest.approx(7.5 / 21.5 - 3 / 11)


def test_weighted_value_shares_use_the_census_weights(parts):
    """alpha is coded for 4 H systems ("a") and 4 O systems ("b").

    unweighted: 4/8 each. weighted: a = 4/(4 + 10) = 0.2857, b = 10/14 = 0.7143. Both columns are
    present in the same table, which is the point: they answer different questions.
    """
    dd = parts["dists"].set_index(["key", "value"])
    assert dd.loc[("alpha", "a"), "share_unweighted"] == pytest.approx(0.5)
    assert dd.loc[("alpha", "b"), "share_unweighted"] == pytest.approx(0.5)
    assert dd.loc[("alpha", "a"), "share_weighted"] == pytest.approx(4 / 14)
    assert dd.loc[("alpha", "b"), "share_weighted"] == pytest.approx(10 / 14)
    # declared schema values nobody uses are still rows, with a zero share
    assert dd.loc[("alpha", "c"), "n_systems"] == 0


def test_complete_stratum_contributes_no_design_variance(parts):
    """H is coded exhaustively, so its finite-population correction is 0 and only O adds variance."""
    cells = parts["cells"]
    base = cells[(cells["key"] == "alpha") & (cells["state"] != ad.STATE_UNRESOLVED)]
    flag = (base["state"] == ad.STATE_NOT_REPORTED).astype(float)
    rate, se, w_base = ad.weighted_share(base, flag, parts["strata"])
    assert w_base == pytest.approx(21.5)
    p_o = 3 / 7
    expected = math.sqrt((N_O / (N_H + N_O)) ** 2 * (1 - 7 / N_O) * p_o * (1 - p_o) / 6)
    assert se == pytest.approx(expected)
    assert rate == pytest.approx(7.5 / 21.5)


def test_multi_valued_shares_are_per_system_and_may_exceed_one(parts):
    """beta: all 12 systems carry "p", 8 of them also carry "q"."""
    dd = parts["dists"].set_index(["key", "value"])
    assert dd.loc[("beta", "p"), "share_unweighted"] == pytest.approx(1.0)
    assert dd.loc[("beta", "q"), "share_unweighted"] == pytest.approx(8 / 12)
    total = parts["dists"].query("key == 'beta'")["share_unweighted"].sum()
    assert total > 1.0


def test_integer_dimension_is_binned_not_tabulated_value_by_value(parts):
    """delta takes 12 distinct integers; a share per integer would describe the sample only."""
    dd = parts["dists"].query("key == 'delta'")
    assert len(dd) < 12
    assert dd["n_systems"].sum() == 12


# ------------------------------------------------------------------- unresolved cells, everywhere


def test_unresolved_cells_are_excluded_from_every_denominator(parts):
    """o4's alpha cell is unresolved: it claims nothing, so it enters no base and no distribution."""
    cells = parts["cells"]
    assert (cells["state"] == ad.STATE_UNRESOLVED).sum() == 1

    under = parts["under"].set_index("key").loc["alpha"]
    assert under["n_cells"] == 12 and under["n_unresolved"] == 1 and under["n_base"] == 11
    assert under["n_coded"] + under["n_not_reported"] == under["n_base"]

    dist = parts["dists"].query("key == 'alpha'")
    assert dist["n_base_coded"].iloc[0] == 8  # 12 - 3 not_reported - 1 unresolved
    assert dist["n_systems"].sum() == 8
    assert dist["n_unresolved"].iloc[0] == 1

    # o4 is in 2024; that year's alpha entropy must rest on the other 2024 systems only
    ent = parts["entropy"].set_index(["key", "year"])
    assert ent.loc[("alpha", 2024), "n_systems"] == 3

    ly = parts["layer_year"]
    layer_x = ly[ly["layer"] == "X"]
    assert layer_x["n_base_cells"].sum() == 23  # 12 systems x 2 dimensions - 1 unresolved

    summary = ad.one_screen_summary(parts["cells"], parts["dists"], parts["under"],
                                    parts["strata"], parts["dims"])
    alpha_row = summary[(summary["level"] == "dimension") & (summary["key"] == "alpha")].iloc[0]
    assert alpha_row["share_unresolved"] == pytest.approx(1 / 12)
    assert alpha_row["share_coded"] + alpha_row["share_not_reported"] + \
        alpha_row["share_unresolved"] == pytest.approx(1.0)


def test_unresolved_is_not_folded_into_not_reported(parts):
    """The headline rate would be 4/12 if the states were collapsed; it must be 3/11."""
    row = parts["under"].set_index("key").loc["alpha"]
    assert row["rate_unweighted"] != pytest.approx(4 / 12)
    assert row["rate_unweighted"] == pytest.approx(3 / 11)


# ---------------------------------------------------------------------------- small-n suppression


def test_year_below_the_threshold_is_suppressed_and_marked(corpus, parts):
    """Suppression follows n, not the year: alpha's 2025 cohort holds a single coded system
    (o5-o7 are not_reported there) and must be suppressed at min-n 3, while every cohort in the
    fixture is below min-n 5 and the whole table goes."""
    kept = parts["entropy"]
    assert kept.loc[kept["suppressed"], "n_systems"].max() < 3
    assert kept.loc[~kept["suppressed"], "n_systems"].min() >= 3
    thin = kept.set_index(["key", "year"]).loc[("alpha", 2025)]
    assert thin["n_systems"] == 1 and bool(thin["suppressed"])
    assert math.isnan(thin["h_ci_lo"])                       # suppressed: no interval
    assert kept.loc[~kept["suppressed"], "h_ci_lo"].notna().all()

    dims, cells, strata = parts["dims"], parts["cells"], parts["strata"]
    strict = ad.entropy_by_dimension_year(cells, dims, 5, 200, 7)
    assert strict["suppressed"].all()
    assert strict["h_ci_lo"].isna().all()  # a suppressed cell gets no interval
    assert strict["n_systems"].max() < 5

    # a suppressed cell can never reach a convergence verdict
    assert ad.convergence_summary(strict, 0.15, 200, 7, cells).empty
    assert not ad.convergence_summary(kept, 0.15, 200, 7, cells).empty

    strict_ly = ad.under_reporting_layer_year(cells, strata, 5)
    assert strict_ly["suppressed"].all()
    assert (~parts["layer_year"]["suppressed"]).all()


def test_entropy_skips_non_categorical_dimensions(parts):
    """delta is an integer: entropy over it would count distinct systems, not design diversity."""
    assert "delta" not in set(parts["entropy"]["key"])
    assert {"alpha", "beta", "gamma"} == set(parts["entropy"]["key"])


def test_entropy_uses_the_whole_value_set_for_multi_valued_dimensions(parts):
    """beta's outcome is "p" or "p+q", two categories, not a marginal over p and q."""
    ent = parts["entropy"].set_index(["key", "year"])
    assert ent.loc[("beta", 2023), "k_observed"] == 2
    labels = set(parts["cells"].query("key == 'beta' and state == 'coded'")["label"])
    assert labels == {"p", "p+q"}


def test_release_year_prefers_the_harvested_date_and_falls_back(corpus):
    """The harvested date wins by default; --year-source coded flips the preference."""
    system = {"id": "h0", "coding": {"first_release_date": {"value": "2019-01-01",
                                                            "not_reported": False}}}
    assert ad.release_year(system, {"h0": "2024-06-01"}, "candidates") == (2024, "candidates")
    assert ad.release_year(system, {"h0": "2024-06-01"}, "coded") == (2019, "coded")
    assert ad.release_year(system, {}, "candidates") == (2019, "coded")
    assert ad.release_year({"id": "x", "coding": {}}, {}, "candidates") == (None, "none")


# --------------------------------------------------------------------------- end to end, and I/O


@pytest.fixture(scope="module")
def run_outputs(corpus, tmp_path_factory) -> dict:
    out = tmp_path_factory.mktemp("out")
    d = corpus["dir"]
    rc = ad.main([
        "--systems", str(d / "systems.json"),
        "--dimensions", str(d / "dimensions.json"),
        "--frame", str(d / "coding_frame.csv"),
        "--candidates", str(d / "systems_candidates.csv"),
        "--reference", str(d / "does_not_exist.csv"),
        "--tables", str(out / "tables"), "--figures", str(out / "figures"),
        "--min-n", "3", "--bootstrap", "100", "--quiet",
    ])
    return {"rc": rc, "tables": out / "tables", "figures": out / "figures"}


def test_main_writes_every_table(run_outputs):
    assert run_outputs["rc"] == 0
    expected = ["value_distributions.csv", "under_reporting_by_dimension.csv",
                "under_reporting_layer_year.csv", "entropy_by_dimension_year.csv",
                "convergence_summary.csv", "summary_one_screen.csv", "summary_one_screen.md"]
    for name in expected:
        path = run_outputs["tables"] / name
        assert path.exists() and path.stat().st_size > 0, name


def test_main_writes_every_figure_in_both_formats(run_outputs):
    stems = ["descriptives_value_distributions", "descriptives_under_reporting_by_dimension",
             "descriptives_under_reporting_layer_year", "descriptives_entropy_by_year",
             "descriptives_entropy_trajectories"]
    for stem in stems:
        for ext in ("svg", "pdf"):
            path = run_outputs["figures"] / f"{stem}.{ext}"
            assert path.exists(), path
            assert path.stat().st_size > 1000, path


def test_matplotlib_stays_on_the_agg_backend(run_outputs):
    import matplotlib

    assert matplotlib.get_backend().lower() == "agg"


def test_both_weightings_are_in_the_same_table(run_outputs):
    """The two columns must never be shipped apart: one describes the coded set, one the field."""
    for name in ("value_distributions.csv", "under_reporting_by_dimension.csv"):
        header = (run_outputs["tables"] / name).read_text(encoding="utf-8").splitlines()[0]
        assert any("unweighted" in c for c in header.split(","))
        assert any(c.endswith("weighted") or "weighted" in c for c in header.split(","))


def test_summary_covers_every_layer_and_every_dimension(run_outputs):
    rows = list(csv.DictReader((run_outputs["tables"] / "summary_one_screen.csv")
                               .open(encoding="utf-8")))
    layers = {r["layer"] for r in rows if r["level"] == "layer"}
    dims = {r["key"] for r in rows if r["level"] == "dimension"}
    assert layers == {"X", "Y"}
    assert dims == {"alpha", "beta", "gamma", "delta"}
    for r in rows:
        assert r["n_systems_coded"] != ""


def test_reference_check_reports_disagreement_rather_than_trusting_it(corpus, parts, tmp_path):
    """The existing under-reporting table is recomputed and diffed, not copied."""
    ref = tmp_path / "reference.csv"
    with ref.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dimension", "layer", "id", "n", "not_reported",
                                           "rate", "weighted_rate"])
        w.writeheader()
        w.writerow({"dimension": "alpha", "layer": "X", "id": "X1", "n": 11, "not_reported": 3,
                    "rate": round(3 / 11, 4), "weighted_rate": round(7.5 / 21.5, 4)})
        w.writerow({"dimension": "gamma", "layer": "Y", "id": "Y1", "n": 12, "not_reported": 0,
                    "rate": 0.5, "weighted_rate": 0.5})  # wrong on purpose
    problems = ad.check_against_reference(parts["under"], ref)
    assert any(p.startswith("gamma.") for p in problems)
    assert not any(p.startswith("alpha.") for p in problems)
    assert any("beta" in p and "missing from the reference" in p for p in problems)


def test_layer_se_clusters_by_system_and_reduces_to_proportion_se(parts):
    """Several rows per system (a layer) must be treated as one draw per system.

    With one row per system the SE equals the stratified-proportion SE. With three rows per system
    whose flags are perfectly correlated within a system, the clustered SE must equal the one-row
    SE (no new information), whereas treating the rows as independent would shrink it by sqrt(3).
    """
    cells = parts["cells"]
    one = cells[(cells["key"] == "alpha") & (cells["state"] != ad.STATE_UNRESOLVED)]
    flag_one = (one["state"] == ad.STATE_NOT_REPORTED).astype(float)
    rate1, se1, _ = ad.weighted_share(one, flag_one, parts["strata"])
    three = pd.concat([one, one, one], ignore_index=True)
    flag_three = (three["state"] == ad.STATE_NOT_REPORTED).astype(float)
    rate3, se3, _ = ad.weighted_share(three, flag_three, parts["strata"])
    assert rate3 == pytest.approx(rate1)
    assert se3 == pytest.approx(se1)
    assert se3 > se1 / math.sqrt(3) * 1.5
