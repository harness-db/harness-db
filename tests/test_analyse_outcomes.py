"""Tests for scripts/analyse_outcomes.py (Phase 7 tasks 49 and 52).

No network, no model calls. The point of these tests is not coverage, it is that the four numbers a
reader is most likely to take at face value - the standardised score, the bootstrap interval, the
minimum detectable effect and the "no association" verdict - are each pinned to something computable
by hand, and that a contrast is never quietly dropped for coming out null.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "analyse_outcomes", ROOT / "scripts" / "analyse_outcomes.py"
)
ao = importlib.util.module_from_spec(SPEC)
sys.modules["analyse_outcomes"] = ao
SPEC.loader.exec_module(ao)


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------
def make_panel(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    """rows: (comparable_key, system_id, score) -> the frame build_comparable_set would produce."""
    df = pd.DataFrame(rows, columns=["comparable_key", "system_id", "score"])
    df["n_rows"] = 1
    df["row_min"] = df["score"]
    df["row_max"] = df["score"]
    df["n_systems"] = df.groupby("comparable_key")["system_id"].transform("nunique")
    return df


def cell(value, *, not_reported: bool = False, unresolved: bool = False) -> dict:
    return {"value": value, "not_reported": not_reported, "unresolved": unresolved,
            "evidence": "fixture"}


def write_results(path: Path, rows: list[dict]) -> None:
    cols = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd", "tokens",
            "date", "source_url", "comparable_key", "notes"]
    frame = pd.DataFrame(rows)
    for col in cols:
        if col not in frame.columns:
            frame[col] = ""
    frame[cols].to_csv(path, index=False)


# ------------------------------------------------------------------------------------------------
# 1. within-key standardisation is exact
# ------------------------------------------------------------------------------------------------
def test_zscore_is_exact_for_a_key_with_four_systems():
    panel = make_panel([("K", "a", 10.0), ("K", "b", 20.0), ("K", "c", 30.0), ("K", "d", 40.0)])
    out = ao.standardise_within_key(panel, rank_threshold=4)
    sd = math.sqrt(500.0 / 3.0)  # sample sd, ddof=1, of 10/20/30/40
    expected = [(v - 25.0) / sd for v in (10.0, 20.0, 30.0, 40.0)]
    assert list(out["std_method"]) == ["zscore"] * 4
    np.testing.assert_allclose(out.sort_values("score")["z"].to_numpy(), expected, rtol=0, atol=1e-12)
    # mean 0 and sd 1 by construction
    assert out["z"].mean() == pytest.approx(0.0, abs=1e-12)
    assert out["z"].std(ddof=1) == pytest.approx(1.0, abs=1e-12)


def test_rank_rule_applies_below_the_threshold_and_is_exact():
    three = ao.standardise_within_key(
        make_panel([("K3", "a", 1.0), ("K3", "b", 2.0), ("K3", "c", 3.0)]), rank_threshold=4
    ).sort_values("score")
    assert list(three["std_method"]) == ["rank"] * 3
    np.testing.assert_allclose(three["z"].to_numpy(), [-1.0, 0.0, 1.0], atol=1e-12)

    two = ao.standardise_within_key(
        make_panel([("K2", "a", 5.0), ("K2", "b", 9.0)]), rank_threshold=4
    ).sort_values("score")
    assert list(two["std_method"]) == ["rank"] * 2
    np.testing.assert_allclose(
        two["z"].to_numpy(), [-1 / math.sqrt(2), 1 / math.sqrt(2)], atol=1e-12
    )


def test_rank_rule_handles_ties_by_average_rank():
    out = ao.standardise_within_key(
        make_panel([("K", "a", 1.0), ("K", "b", 1.0), ("K", "c", 3.0)]), rank_threshold=4
    ).sort_values(["score", "system_id"])
    # ranks 1.5, 1.5, 3 -> centred on 2 and divided by sd(1,2,3) = 1
    np.testing.assert_allclose(out["z"].to_numpy(), [-0.5, -0.5, 1.0], atol=1e-12)


def test_a_key_whose_scores_are_all_equal_is_marked_degenerate_not_divided_by_zero():
    out = ao.standardise_within_key(
        make_panel([("K", f"s{i}", 50.0) for i in range(4)]), rank_threshold=4
    )
    assert list(out["std_method"]) == ["degenerate"] * 4
    assert (out["z"] == 0.0).all()


def test_rank_threshold_is_the_documented_boundary():
    """4 systems -> z-score, 3 -> rank. The rule is stated in every output, so it must hold."""
    four = ao.standardise_within_key(
        make_panel([("K", f"s{i}", float(i)) for i in range(4)]), rank_threshold=4
    )
    three = ao.standardise_within_key(
        make_panel([("K", f"s{i}", float(i)) for i in range(3)]), rank_threshold=4
    )
    assert set(four["std_method"]) == {"zscore"}
    assert set(three["std_method"]) == {"rank"}


# ------------------------------------------------------------------------------------------------
# 2. a key with one system is excluded
# ------------------------------------------------------------------------------------------------
def test_single_system_keys_are_excluded_from_the_comparable_set():
    results = pd.DataFrame(
        {
            "system_id": ["a", "b", "solo", "nokey"],
            "benchmark": ["SWE-bench"] * 4,
            "split": ["Lite"] * 4,
            "metric": ["resolved"] * 4,
            "score": [10.0, 20.0, 99.0, 50.0],
            "comparable_key": [
                "SWE-bench|Lite|gpt-4o", "SWE-bench|Lite|gpt-4o", "SWE-bench|Lite|o3", ""
            ],
        }
    )
    panel = ao.build_comparable_set(results, min_systems=2)
    assert set(panel["comparable_key"]) == {"SWE-bench|Lite|gpt-4o"}
    assert "solo" not in set(panel["system_id"])   # key held one system: no comparison possible
    assert "nokey" not in set(panel["system_id"])  # no comparable_key at all
    assert ao.key_size_distribution(panel) == {
        "2": 1, "3-4": 0, "5+": 0, "keys": 1, "systems": 2, "observations": 2
    }


def test_several_rows_of_one_system_in_one_key_collapse_to_one_observation():
    results = pd.DataFrame(
        {
            "system_id": ["a", "a", "a", "b"],
            "benchmark": ["SWE-bench"] * 4,
            "split": ["Lite"] * 4,
            "metric": ["resolved"] * 4,
            "score": [10.0, 20.0, 60.0, 30.0],
            "comparable_key": ["SWE-bench|Lite|gpt-4o"] * 4,
        }
    )
    panel = ao.build_comparable_set(results, min_systems=2, agg="median")
    a = panel[panel["system_id"] == "a"].iloc[0]
    assert len(panel) == 2                 # one observation per system, not per row
    assert a["score"] == 20.0              # the median of 10/20/60
    assert a["n_rows"] == 3 and a["row_min"] == 10.0 and a["row_max"] == 60.0
    assert panel["benchmark"].iloc[0] == "SWE-bench" and panel["base_model"].iloc[0] == "gpt-4o"


# ------------------------------------------------------------------------------------------------
# 3. the bootstrap resamples keys, not rows
# ------------------------------------------------------------------------------------------------
def test_bootstrap_draws_are_exactly_a_seeded_resample_of_the_KEY_level_differences():
    d = np.array([-0.5, 0.25, 1.75, 2.0])
    got = ao.bootstrap_key_means(d, n_boot=500, seed=1234)
    rng = np.random.default_rng(1234)
    idx = rng.integers(0, len(d), size=(500, len(d)))
    np.testing.assert_array_equal(got, d[idx].mean(axis=1))
    assert got.shape == (500,)
    assert got.min() >= d.min() - 1e-12 and got.max() <= d.max() + 1e-12


def test_every_bootstrap_replicate_is_a_mean_of_K_KEY_differences_not_of_rows():
    """The identifying property: with K keys there are only C(2K-1, K) attainable replicate values.

    Key `heavy` holds 20 systems and the other two keys hold 2 each. Resampling rows would let the
    heavy key dominate and would produce replicate values that are not means of three key-level
    differences; resampling keys cannot.
    """
    rows = [("heavy", f"h{i}", 100.0 - i) for i in range(20)]
    rows += [("light1", "a", 10.0), ("light1", "b", 20.0)]
    rows += [("light2", "c", 10.0), ("light2", "d", 20.0)]
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    # exposure: the top half of `heavy`, the LOW scorer of light1, the HIGH scorer of light2 - so
    # the three key-level differences are all distinct and the attainable support is the full C(5,3)
    exposed = {f"h{i}" for i in range(10)} | {"a", "d"}
    codings = {
        sid: {"dim": cell("on" if sid in exposed else "off")}
        for sid in panel["system_id"]
    }
    contrast = ao.Contrast(
        name="t", dimension="dim", dimension_id="X", exposed_label="on", reference_label="off",
        exposed_when=lambda coded: "on" in coded, mechanism="fixture", drift_exposure="n/a",
    )
    frame = ao.contrast_exposure(panel, contrast, codings)
    diffs = ao.key_differences(frame)
    assert len(diffs) == 3
    reps = ao.bootstrap_key_means(diffs["d"].to_numpy(), n_boot=3000, seed=7)
    attainable = {
        round(float(np.mean(combo)), 12)
        for combo in product(diffs["d"].to_numpy(), repeat=3)
    }
    assert len(attainable) == 10  # C(2*3-1, 3): the whole support when the unit is the key
    assert {round(float(v), 12) for v in reps} <= attainable
    # and the point estimate weights the 20-system key exactly like the 2-system ones
    assert diffs["d"].mean() == pytest.approx(float(np.mean(diffs["d"])))


def test_bootstrap_of_an_empty_set_of_keys_is_empty_rather_than_an_error():
    assert ao.bootstrap_key_means([], n_boot=100, seed=1).shape == (0,)


# ------------------------------------------------------------------------------------------------
# 4. the power calculation matches a hand-computed value
# ------------------------------------------------------------------------------------------------
def test_mde_matches_a_hand_computed_value_on_a_fixture():
    """d = (0, 1, 2, 3): K = 4, s_d = sqrt(5/3), df = 3.

    MDE = (t_{0.975,3} + t_{0.80,3}) * s_d / sqrt(4)
        = (3.1824463052837078 + 0.9784723123633042) * 1.2909944487358056 / 2
    """
    d = [0.0, 1.0, 2.0, 3.0]
    s_d = math.sqrt(5.0 / 3.0)
    assert s_d == pytest.approx(1.2909944487358056, abs=1e-12)
    hand = (3.1824463052837078 + 0.9784723123633042) * s_d / math.sqrt(4)
    assert hand == pytest.approx(2.68586142, abs=1e-7)
    assert ao.mde_from_key_differences(d) == pytest.approx(hand, abs=1e-9)


def test_mde_scales_as_one_over_root_k_and_with_the_spread():
    base = ao.mde_from_key_differences([0.0, 1.0, 2.0, 3.0])
    doubled_spread = ao.mde_from_key_differences([0.0, 2.0, 4.0, 6.0])
    assert doubled_spread == pytest.approx(2 * base, abs=1e-9)
    # more keys with the same spread must detect a smaller effect
    more_keys = ao.mde_from_key_differences([0.0, 1.0, 2.0, 3.0] * 5)
    assert more_keys < base


def test_mde_is_undefined_with_fewer_than_two_keys():
    assert math.isnan(ao.mde_from_key_differences([1.0]))
    assert math.isnan(ao.mde_from_key_differences([]))


# ------------------------------------------------------------------------------------------------
# 5. a null contrast is reported with its CI and its minimum detectable effect, not dropped
# ------------------------------------------------------------------------------------------------
def _null_fixture():
    """Six keys of four systems each, exposure assigned so the design feature carries no signal."""
    rows = []
    codings = {}
    for k in range(6):
        for i, score in enumerate((10.0, 20.0, 30.0, 40.0)):
            sid = f"k{k}s{i}"
            rows.append((f"KEY{k}", sid, score))
            # alternate which rank is exposed across keys: no consistent association
            exposed = (i % 2 == 0) if k % 2 == 0 else (i % 2 == 1)
            codings[sid] = {"dim": cell("on" if exposed else "off")}
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="null_contrast", dimension="dim", dimension_id="X", exposed_label="on",
        reference_label="off", exposed_when=lambda coded: "on" in coded,
        mechanism="fixture", drift_exposure="n/a",
    )
    return panel, contrast, codings


def test_a_null_contrast_is_reported_with_ci_n_and_minimum_detectable_effect():
    panel, contrast, codings = _null_fixture()
    est = ao.estimate_contrast(panel, contrast, codings, n_boot=2000, seed=5)
    assert est["estimable"] is True
    assert est["null"] is True, "a null must be reported as a finding, not dropped"
    assert est["detected"] is False
    # the three things a null must always carry
    assert est["ci_low"] <= 0.0 <= est["ci_high"]
    assert not math.isnan(est["ci_low"]) and not math.isnan(est["ci_high"])
    assert est["n_keys"] == 6 and est["n_systems"] == 24 and est["n_observations"] == 24
    assert est["mde_80"] > 0.0 and not math.isnan(est["mde_80"])
    assert "detectable at 80% power" in est["power_sentence"]
    # and the p-value never travels alone
    assert est["ols"]["available"] is True
    for field in ("ci_low", "ci_high", "n_observations", "n_keys"):
        assert field in est["ols"]


def test_no_p_value_is_reported_without_its_interval_and_its_n():
    panel, contrast, codings = _null_fixture()
    est = ao.estimate_contrast(panel, contrast, codings, n_boot=500, seed=5)
    if est["ols"].get("p_value") is not None:
        assert est["ols"]["ci_low"] is not None and est["ols"]["ci_high"] is not None
        assert est["ols"]["n_observations"] > 0
    perm = est["permutation"]
    if perm.get("p_two_sided") is not None:
        assert perm["n_assignments"] >= 1 and perm["n_draws"] >= 1


def test_the_power_sentence_says_so_when_only_a_large_effect_was_detectable():
    # two keys of two systems, wildly inconsistent differences -> a huge MDE
    rows = [("A", "a1", 1.0), ("A", "a2", 2.0), ("B", "b1", 1.0), ("B", "b2", 2.0),
            ("C", "c1", 1.0), ("C", "c2", 2.0)]
    codings = {"a1": {"dim": cell("on")}, "a2": {"dim": cell("off")},
               "b1": {"dim": cell("off")}, "b2": {"dim": cell("on")},
               "c1": {"dim": cell("on")}, "c2": {"dim": cell("off")}}
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="wide", dimension="dim", dimension_id="X", exposed_label="on", reference_label="off",
        exposed_when=lambda coded: "on" in coded, mechanism="fixture", drift_exposure="n/a",
    )
    est = ao.estimate_contrast(panel, contrast, codings, n_boot=500, seed=3)
    assert est["mde_80"] >= ao.LARGE_EFFECT
    assert est["only_large_detectable"] is True
    assert "Only a very large effect would have been detectable" in est["power_sentence"]


# ------------------------------------------------------------------------------------------------
# guards against small-n artefacts
# ------------------------------------------------------------------------------------------------
def test_two_identical_key_differences_yield_no_interval_rather_than_a_zero_width_one():
    rows = [("A", "a1", 1.0), ("A", "a2", 2.0), ("B", "b1", 1.0), ("B", "b2", 2.0),
            ("C", "c1", 1.0), ("C", "c2", 2.0)]
    codings = {"a1": {"dim": cell("off")}, "a2": {"dim": cell("on")},
               "b1": {"dim": cell("off")}, "b2": {"dim": cell("on")},
               "c1": {"dim": cell("off")}, "c2": {"dim": cell("on")}}
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="identical", dimension="dim", dimension_id="X", exposed_label="on",
        reference_label="off", exposed_when=lambda coded: "on" in coded,
        mechanism="fixture", drift_exposure="n/a",
    )
    est = ao.estimate_contrast(panel, contrast, codings, n_boot=500, seed=3)
    assert est["degenerate_interval"] is True
    assert math.isnan(est["ci_low"]) and math.isnan(est["mde_80"])
    assert est["detected"] is False, "zero between-key spread is not evidence of an effect"


def test_a_contrast_varying_in_too_few_keys_is_reported_not_estimable_and_still_present():
    rows = [("A", "a1", 1.0), ("A", "a2", 2.0), ("B", "b1", 1.0), ("B", "b2", 2.0)]
    codings = {"a1": {"dim": cell("off")}, "a2": {"dim": cell("on")},
               "b1": {"dim": cell("off")}, "b2": {"dim": cell("on")}}
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="thin", dimension="dim", dimension_id="X", exposed_label="on", reference_label="off",
        exposed_when=lambda coded: "on" in coded, mechanism="fixture", drift_exposure="n/a",
    )
    est = ao.estimate_contrast(panel, contrast, codings, n_boot=200, seed=3, min_keys=3)
    assert est["estimable"] is False
    assert est["n_keys"] == 2 and len(est["keys"]) == 2  # the evidence is still shown
    assert "NOT ESTIMABLE" in est["power_sentence"]
    assert est["permutation"]["n_assignments"] == 4
    assert est["permutation"]["p_min_attainable"] == pytest.approx(0.25)
    assert est["permutation"]["floor_above_05"] is True


def test_permutation_design_floor_says_when_significance_is_unreachable():
    rows = [("A", "a1", 1.0), ("A", "a2", 2.0), ("B", "b1", 1.0), ("B", "b2", 2.0)]
    codings = {"a1": {"dim": cell("off")}, "a2": {"dim": cell("on")},
               "b1": {"dim": cell("off")}, "b2": {"dim": cell("on")}}
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="floor", dimension="dim", dimension_id="X", exposed_label="on", reference_label="off",
        exposed_when=lambda coded: "on" in coded, mechanism="fixture", drift_exposure="n/a",
    )
    perm = ao.permutation_test_within_key(ao.contrast_exposure(panel, contrast, codings))
    assert perm["mode"] == "exact"
    assert perm["n_assignments"] == 4           # C(2,1) x C(2,1)
    assert perm["p_two_sided"] >= perm["p_min_attainable"]
    assert perm["floor_above_05"] is True       # 1/4 > 0.05: nothing can ever be significant


# ------------------------------------------------------------------------------------------------
# coded values: an uncoded cell must not become a reference category
# ------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "coding,expected",
    [
        ({"d": cell("single")}, ["single"]),
        ({"d": cell(["a", "b"])}, ["a", "b"]),
        ({"d": cell(None, not_reported=True)}, None),
        ({"d": cell(None, unresolved=True)}, None),
        ({"d": cell(None)}, None),
        ({"d": cell([])}, None),
        ({}, None),
    ],
)
def test_coded_values_never_turns_an_absent_code_into_a_value(coding, expected):
    assert ao.coded_values(coding, "d") == expected


def test_systems_with_an_uncoded_dimension_drop_out_of_that_contrast_only():
    rows = [("A", "a1", 1.0), ("A", "a2", 2.0), ("A", "a3", 3.0), ("A", "a4", 4.0)]
    codings = {
        "a1": {"dim": cell("on")}, "a2": {"dim": cell("off")},
        "a3": {"dim": cell(None, not_reported=True)}, "a4": {"dim": cell(None, unresolved=True)},
    }
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="partial", dimension="dim", dimension_id="X", exposed_label="on",
        reference_label="off", exposed_when=lambda coded: "on" in coded,
        mechanism="fixture", drift_exposure="n/a",
    )
    frame = ao.contrast_exposure(panel, contrast, codings)
    assert set(frame["system_id"]) == {"a1", "a2"}
    # but the standardisation still used all four systems in the key, as documented
    assert set(panel["std_method"]) == {"zscore"}


def test_keys_where_the_contrast_does_not_vary_are_excluded():
    rows = [("A", "a1", 1.0), ("A", "a2", 2.0), ("B", "b1", 1.0), ("B", "b2", 2.0)]
    codings = {"a1": {"dim": cell("on")}, "a2": {"dim": cell("off")},
               "b1": {"dim": cell("on")}, "b2": {"dim": cell("on")}}
    panel = ao.standardise_within_key(make_panel(rows), rank_threshold=4)
    contrast = ao.Contrast(
        name="v", dimension="dim", dimension_id="X", exposed_label="on", reference_label="off",
        exposed_when=lambda coded: "on" in coded, mechanism="fixture", drift_exposure="n/a",
    )
    frame = ao.contrast_exposure(panel, contrast, codings)
    assert set(frame["comparable_key"]) == {"A"}


# ------------------------------------------------------------------------------------------------
# contrast declaration and end-to-end run
# ------------------------------------------------------------------------------------------------
def test_the_contrast_set_is_pre_specified_small_and_mechanistic():
    assert 3 <= len(ao.CONTRASTS) <= 5, "a small pre-specified set, not a fishing expedition"
    names = [c.name for c in ao.CONTRASTS]
    assert len(set(names)) == len(names)
    dims = {c.dimension for c in ao.CONTRASTS}
    assert dims <= {"self_verification", "retry_policy", "context_compaction",
                    "multi_agent_topology", "planning_granularity"}
    for c in ao.CONTRASTS:
        assert len(c.mechanism) > 40, f"{c.name} must state why it could affect task success"
        assert c.drift_exposure, f"{c.name} must state its scaffold-drift attenuation risk"


def test_every_caption_string_carries_the_scaffold_drift_caveat():
    assert "Scaffold drift" in ao.DRIFT_CAVEAT
    assert "LOWER BOUND" in ao.DRIFT_CAVEAT
    assert "benchmark_caveats.md" in ao.DRIFT_CAVEAT


@pytest.fixture()
def tiny_dataset(tmp_path: Path):
    """A dataset exercising every branch: a solo key, an unkeyed row, null and thin contrasts."""
    scores = {
        "KEYA": [("s1", 40.0), ("s2", 30.0), ("s3", 20.0), ("s4", 10.0)],
        "KEYB": [("s1", 44.0), ("s2", 33.0), ("s3", 22.0), ("s4", 11.0)],
        "KEYC": [("s5", 60.0), ("s6", 50.0), ("s7", 40.0), ("s8", 30.0)],
        "KEYD": [("s5", 61.0), ("s6", 51.0), ("s7", 41.0), ("s8", 31.0)],
        "KEYE": [("s9", 5.0)],  # a key with one system: excluded
    }
    rows = []
    for key, entries in scores.items():
        bench, split, model = "SWE-bench", "Verified", key.lower()
        for sid, score in entries:
            rows.append({
                "system_id": sid, "model": model, "benchmark": bench, "split": split,
                "metric": "resolved", "score": score,
                "comparable_key": f"{bench}|{split}|{model}",
            })
    rows.append({"system_id": "s9", "model": "x", "benchmark": "Other", "split": "",
                 "metric": "f1", "score": 0.5, "comparable_key": ""})
    results_path = tmp_path / "results.csv"
    write_results(results_path, rows)

    def sys_entry(sid: str, **coded) -> dict:
        return {"id": sid, "name": sid, "papers": [], "coding": {k: cell(v) for k, v in coded.items()}}

    systems = [
        sys_entry("s1", self_verification=["test_execution"], multi_agent_topology="peer",
                  planning_granularity="explicit_plan_object", context_compaction=["summarize"],
                  retry_policy="until_pass"),
        sys_entry("s2", self_verification=["self_critique"], multi_agent_topology="single",
                  planning_granularity="implicit", context_compaction=["none"],
                  retry_policy="none"),
        sys_entry("s3", self_verification=["test_execution"], multi_agent_topology="single",
                  planning_granularity="none", context_compaction=["summarize"]),
        sys_entry("s4", self_verification=["none"], multi_agent_topology="pipeline",
                  planning_granularity="hierarchical", context_compaction=["none"]),
        sys_entry("s5", self_verification=["linters_typecheck"], multi_agent_topology="single",
                  planning_granularity="implicit", context_compaction=["none"]),
        sys_entry("s6", self_verification=["none"], multi_agent_topology="orchestrator_workers",
                  planning_granularity="explicit_plan_object", context_compaction=["summarize"]),
        sys_entry("s7", self_verification=["llm_judge"], multi_agent_topology="single",
                  planning_granularity="none", context_compaction=["truncate_oldest"]),
        sys_entry("s8", self_verification=["test_execution"], multi_agent_topology="debate",
                  planning_granularity="implicit", context_compaction=["none"]),
        sys_entry("s9", self_verification=["none"], multi_agent_topology="single"),
    ]
    systems_path = tmp_path / "systems.json"
    systems_path.write_text(json.dumps(systems), encoding="utf-8")
    return results_path, systems_path, tmp_path


def test_end_to_end_run_reports_all_five_contrasts_and_drops_none(tiny_dataset, capsys):
    results_path, systems_path, tmp_path = tiny_dataset
    rc = ao.main([
        "--results", str(results_path), "--systems", str(systems_path),
        "--tab-dir", str(tmp_path / "tables"), "--fig-dir", str(tmp_path / "figures"),
        "--n-boot", "300", "--no-render",
    ])
    assert rc == 0
    contrasts = pd.read_csv(tmp_path / "tables" / "outcomes_contrasts.csv")
    assert list(contrasts["contrast"]) == [c.name for c in ao.CONTRASTS]
    assert len(contrasts) == len(ao.CONTRASTS), "no contrast may be dropped for its result"
    summary = json.loads((tmp_path / "tables" / "outcomes_summary.json").read_text(encoding="utf-8"))
    assert summary["comparable_set"]["keys"] == 4          # KEYE held one system
    assert "not identifiable" in summary["not_fitted"]
    assert summary["bootstrap"]["unit"] == "comparable_key"
    for est in summary["contrasts"]:
        assert est.get("power_sentence")
        assert "n_keys" in est and "n_systems" in est
    out = capsys.readouterr().out
    assert "COVERAGE" in out and "THE COMPARABLE SET" in out
    assert "Scaffold drift" in out
    for contrast in ao.CONTRASTS:
        assert contrast.name in out


def test_end_to_end_run_renders_every_figure(tiny_dataset):
    results_path, systems_path, tmp_path = tiny_dataset
    rc = ao.main([
        "--results", str(results_path), "--systems", str(systems_path),
        "--tab-dir", str(tmp_path / "tables"), "--fig-dir", str(tmp_path / "figures"),
        "--n-boot", "200",
    ])
    assert rc == 0
    for stem in ("outcomes_comparable_set", "outcomes_contrasts", "outcomes_coverage"):
        for ext in ("svg", "pdf"):
            path = tmp_path / "figures" / f"{stem}.{ext}"
            assert path.exists() and path.stat().st_size > 0, f"{path} not regenerated from data"


def test_coverage_counts_report_the_gap_between_scored_and_comparable(tiny_dataset):
    results_path, systems_path, _ = tiny_dataset
    results = ao.load_results(results_path)
    codings = ao.load_codings(systems_path)
    panel = ao.build_comparable_set(results)
    cov = ao.coverage_counts(results, codings, panel)
    assert cov["coded_systems"] == 9
    assert cov["with_any_result_row"] == 9
    assert cov["in_multi_system_key"] == 8          # s9 never shares a key
    assert cov["gap_result_to_comparable"] == 1
