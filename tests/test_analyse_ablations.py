"""Tests for scripts/analyse_ablations.py (meta-analysis of published ablations, RQ3).

No network and no model calls: the classifier is a fake backend that counts how often it is called.

The point of these tests is not coverage. It is that the five numbers a reader of that script's
output would take at face value are each pinned to arithmetic a person can redo on paper -
the relative effect, the raw delta, the DerSimonian-Laird pooled estimate, I-squared and Egger's
intercept - and that the three refusals the design depends on actually happen: a pair whose metric
does not match is DROPPED AND COUNTED rather than fudged, a dimension with two papers is reported
UNPOOLED rather than pooled on two points, and a label the classifier could not map NEVER reaches
the pooled table.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("analyse_ablations", ROOT / "scripts" / "analyse_ablations.py")
aa = importlib.util.module_from_spec(SPEC)
sys.modules["analyse_ablations"] = aa
SPEC.loader.exec_module(aa)


# ------------------------------------------------------------------------------------------------
# fixtures / helpers
# ------------------------------------------------------------------------------------------------
CANDIDATE_COLUMNS = ["system_id", "record_id", "label", "label_key", "benchmark", "split",
                     "metric", "score", "model", "evidence_quote", "note"]

REJECT_COLUMNS = ["reason", "row_id", "system_id", "record_id", "reported_system_name", "benchmark",
                  "split", "metric", "score", "model", "evidence_quote", "evidence_locator", "note"]

OWN_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd", "tokens",
               "date", "source_url", "comparable_key", "notes"]


def candidate(system_id="sysa", record_id="p1", label="w/o memory", benchmark="SWE-bench",
              split="Verified", metric="% resolved", score=40.0, model="gpt-4o", quote="q",
              note="ablation") -> dict:
    return {"system_id": system_id, "record_id": record_id, "label": label,
            "label_key": f"{system_id}|{label.lower()}", "benchmark": benchmark, "split": split,
            "metric": metric, "score": score, "model": model, "evidence_quote": quote, "note": note}


def candidates(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)


def own_row(system_id="sysa", benchmark="SWE-bench", split="Verified", metric="% resolved",
            score=50.0, model="gpt-4o") -> dict:
    return {"system_id": system_id, "model": model, "benchmark": benchmark, "split": split,
            "metric": metric, "score": score, "cost_usd": "", "tokens": "", "date": "",
            "source_url": "", "comparable_key": "", "notes": "source=paper; row_id=x"}


def own(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=OWN_COLUMNS)
    frame["score"] = pd.to_numeric(frame["score"])
    return frame


def cls(category="ablation", dimension="long_term_memory", direction="component_removed",
        confidence=0.9, reason="fixture") -> dict:
    return {"category": category, "dimension": dimension, "direction": direction,
            "confidence": confidence, "reason": reason, "demoted": ""}


class FakeBackend:
    """A stand-in for vote_batch_claude_code that counts calls and answers from a dict."""

    def __init__(self, answers: dict[str, dict] | None = None, default: dict | None = None):
        self.answers = answers or {}
        self.default = default or cls()
        self.calls = 0
        self.seen: list[list[str]] = []
        self.system_prompts: list[str] = []

    def __call__(self, exe, model, system_file, batch, effort=None, schema=None, prompt=None,
                 text_json=False):
        self.calls += 1
        self.seen.append([item["label_key"] for item in batch])
        self.system_prompts.append(Path(system_file).read_text(encoding="utf-8"))
        assert text_json is True, "the classifier must ask for plain-text JSON"
        assert callable(prompt) and "label" in prompt(batch)
        votes = []
        for item in batch:
            answer = dict(self.answers.get(item["label_key"], self.default))
            answer["record_id"] = item["id"]
            votes.append(answer)
        return _Result(votes)


class _Result:
    def __init__(self, votes):
        self.votes = votes
        self.model = "fake-model"
        self.tokens_in = 10
        self.tokens_out = 5
        self.cost_usd = 0.0


DIMS = aa.load_dimensions()


# ------------------------------------------------------------------------------------------------
# 1. the effect measures are exact
# ------------------------------------------------------------------------------------------------
def test_relative_and_raw_effects_are_exact():
    """full 50 -> ablated 40 on % resolved: raw delta 10.0 points, relative effect 0.20."""
    frame, drops = aa.build_contrasts(
        candidates([candidate(score=40.0)]),
        {"sysa|w/o memory": cls()},
        own([own_row(score=50.0)]),
    )
    assert len(frame) == 1, drops
    row = frame.iloc[0]
    assert row["full_score"] == 50.0
    assert row["ablated_score"] == 40.0
    assert row["with_score"] == 50.0 and row["without_score"] == 40.0
    assert row["delta_raw"] == pytest.approx(10.0)
    assert row["rel_effect"] == pytest.approx(0.2)
    assert row["dimension"] == "long_term_memory"
    assert drops == {}


def test_augmentation_is_oriented_the_other_way_round():
    """`component_added`: the ROW has the component and the full-system row does not.

    full 50, row 60, "+ memory" -> with = 60, without = 50, delta = +10, rel = 10/60.
    Getting this backwards would put a positive effect in with the wrong sign, so it is pinned.
    """
    frame, drops = aa.build_contrasts(
        candidates([candidate(label="+ memory", score=60.0)]),
        {"sysa|+ memory": cls(category="augmentation", direction="component_added")},
        own([own_row(score=50.0)]),
    )
    assert len(frame) == 1, drops
    row = frame.iloc[0]
    assert row["with_score"] == 60.0 and row["without_score"] == 50.0
    assert row["delta_raw"] == pytest.approx(10.0)
    assert row["rel_effect"] == pytest.approx(10.0 / 60.0)


def test_an_ablation_that_beat_the_full_system_keeps_its_negative_sign():
    """The component that did not help must stay in the table with a negative effect."""
    frame, _ = aa.build_contrasts(
        candidates([candidate(score=55.0)]),
        {"sysa|w/o memory": cls()},
        own([own_row(score=50.0)]),
    )
    assert frame.iloc[0]["rel_effect"] == pytest.approx(-0.1)
    assert frame.iloc[0]["delta_raw"] == pytest.approx(-5.0)


def test_lower_is_better_metric_flips_the_sign_not_the_roles():
    """On an MSE, the ablation scoring WORSE means scoring higher; the effect must be positive."""
    frame, drops = aa.build_contrasts(
        candidates([candidate(metric="test MSE", score=0.5)]),
        {"sysa|w/o memory": cls()},
        own([own_row(metric="test MSE", score=0.4)]),
    )
    assert len(frame) == 1, drops
    row = frame.iloc[0]
    assert row["polarity"] == "lower"
    assert row["delta_raw"] == pytest.approx(0.1)          # 0.5 - 0.4, error grew when removed
    assert row["rel_effect"] == pytest.approx(0.1 / 0.4)   # as a fraction of the full system
    assert row["var_method"] == "assumed_rel_se"           # no binomial model for an MSE


def test_metric_polarity_puts_error_rate_on_the_lower_side():
    assert aa.metric_polarity("accuracy") == "higher"
    assert aa.metric_polarity("% resolved") == "higher"
    assert aa.metric_polarity("error rate") == "lower"   # "rate" must not win over "error"
    assert aa.metric_polarity("test MSE") == "lower"
    assert aa.metric_polarity("blorp") == "unknown"


def test_a_zero_full_system_score_is_dropped_not_divided_by():
    """The relative effect has the full-system score in the denominator; at zero it is not defined."""
    frame, drops = aa.build_contrasts(
        candidates([candidate(score=0.4)]),
        {"sysa|w/o memory": cls()},
        own([own_row(score=0.0)]),
    )
    assert frame.empty
    assert drops["denominator_too_small"] == 1


# ------------------------------------------------------------------------------------------------
# 2. a pair that does not match exactly is dropped, and counted
# ------------------------------------------------------------------------------------------------
def test_the_same_experiment_reported_twice_is_one_contrast():
    """A number printed in a table and again in the text is one experiment, not two studies."""
    rows = [candidate(score=40.0), candidate(score=40.0, quote="restated in the text")]
    frame, drops = aa.build_contrasts(candidates(rows), {"sysa|w/o memory": cls()},
                                      own([own_row(score=50.0)]))
    assert len(frame) == 1
    assert drops["duplicate_contrast"] == 1


def test_mismatched_metric_is_dropped_and_counted():
    """The paper's own row exists for the benchmark, but on another metric: no pair, counted."""
    frame, drops = aa.build_contrasts(
        candidates([candidate(metric="accuracy")]),
        {"sysa|w/o memory": cls()},
        own([own_row(metric="% resolved")]),
    )
    assert frame.empty
    assert drops["metric_mismatch"] == 1
    assert sum(drops.values()) == 1


@pytest.mark.parametrize("field,value,reason", [
    ("model", "claude-3", "model_mismatch"),
    ("split", "Lite", "split_mismatch"),
    ("metric", "accuracy", "metric_mismatch"),
    ("benchmark", "GAIA", "no_full_row"),
])
def test_every_kind_of_mismatch_has_its_own_counted_reason(field, value, reason):
    frame, drops = aa.build_contrasts(
        candidates([candidate(**{field: value})]),
        {"sysa|w/o memory": cls()},
        own([own_row()]),
    )
    assert frame.empty
    assert drops[reason] == 1, drops


def test_ambiguous_full_system_score_is_dropped_rather_than_resolved_upwards():
    """Two different own scores in the same cell: which one is "the full system" is unknowable.

    Taking the maximum would inflate the effect in the same direction publication bias already
    pushes, so the pair is dropped and counted.
    """
    frame, drops = aa.build_contrasts(
        candidates([candidate(score=40.0)]),
        {"sysa|w/o memory": cls()},
        own([own_row(score=50.0), own_row(score=55.0)]),
    )
    assert frame.empty
    assert drops["full_score_ambiguous"] == 1


def test_a_duplicated_identical_own_score_is_not_ambiguous():
    frame, drops = aa.build_contrasts(
        candidates([candidate(score=40.0)]),
        {"sysa|w/o memory": cls()},
        own([own_row(score=50.0), own_row(score=50.0)]),
    )
    assert len(frame) == 1, drops


def test_matching_ignores_case_and_whitespace_only():
    frame, drops = aa.build_contrasts(
        candidates([candidate(benchmark="swe-bench ", metric="%  Resolved")]),
        {"sysa|w/o memory": cls()},
        own([own_row(benchmark="SWE-bench", metric="% resolved")]),
    )
    assert len(frame) == 1, drops


@pytest.mark.parametrize("category,reason", [
    ("rival_system", "not_an_ablation:rival_system"),
    ("non_harness_baseline", "not_an_ablation:non_harness_baseline"),
    ("own_full_alias", "not_an_ablation:own_full_alias"),
    ("model_or_training_variant", "not_an_ablation:model_or_training_variant"),
])
def test_non_ablation_categories_are_dropped_with_their_category_named(category, reason):
    frame, drops = aa.build_contrasts(
        candidates([candidate()]),
        {"sysa|w/o memory": cls(category=category, dimension=None)},
        own([own_row()]),
    )
    assert frame.empty
    assert drops[reason] == 1


@pytest.mark.parametrize("direction", ["component_changed", "unclear"])
def test_an_unorientable_direction_is_dropped(direction):
    frame, drops = aa.build_contrasts(
        candidates([candidate()]),
        {"sysa|w/o memory": cls(direction=direction)},
        own([own_row()]),
    )
    assert frame.empty
    assert drops[f"direction_{direction}"] == 1


# ------------------------------------------------------------------------------------------------
# 3. DerSimonian-Laird matches a hand-computed example
# ------------------------------------------------------------------------------------------------
def test_dersimonian_laird_matches_a_hand_computed_example():
    """y = (0.2, 0.4, 0.6), v = (0.01, 0.01, 0.04). Worked through on paper:

        w      = (100, 100, 25),  sum w = 225
        mu_FE  = (100*0.2 + 100*0.4 + 25*0.6) / 225 = 75/225 = 1/3
        Q      = 100*(0.2-1/3)^2 + 100*(0.4-1/3)^2 + 25*(0.6-1/3)^2 = 4.0
        C      = 225 - (100^2 + 100^2 + 25^2)/225 = 225 - 20625/225 = 400/3
        tau^2  = (4 - 2) / (400/3) = 0.015
        w*     = (40, 40, 1/0.055 = 200/11),  sum w* = 1080/11
        mu     = (40*0.2 + 40*0.4 + (200/11)*0.6) / (1080/11) = 0.35555...
        SE     = sqrt(11/1080) = 0.1009216...
        I^2    = (4 - 2)/4 = 50%
    """
    pooled = aa.dersimonian_laird([0.2, 0.4, 0.6], [0.01, 0.01, 0.04])
    assert pooled.k == 3
    assert pooled.mu_fe == pytest.approx(1.0 / 3.0)
    assert pooled.q == pytest.approx(4.0)
    assert pooled.tau2 == pytest.approx(0.015)
    assert pooled.mu == pytest.approx(0.35555555555, rel=0, abs=1e-9)
    assert pooled.se == pytest.approx(math.sqrt(11.0 / 1080.0), abs=1e-12)
    assert pooled.i2 == pytest.approx(50.0)
    assert pooled.ci_low == pytest.approx(pooled.mu - 1.959963984540054 * pooled.se)
    assert pooled.ci_high == pytest.approx(pooled.mu + 1.959963984540054 * pooled.se)
    assert sum(pooled.weights) == pytest.approx(1.0)


def test_homogeneous_studies_give_tau2_zero_and_the_fixed_effect_answer():
    pooled = aa.dersimonian_laird([0.3, 0.3, 0.3], [0.01, 0.02, 0.04])
    assert pooled.q == pytest.approx(0.0)
    assert pooled.tau2 == 0.0
    assert pooled.i2 == 0.0
    assert pooled.mu == pytest.approx(0.3)
    assert pooled.mu == pytest.approx(pooled.mu_fe)


def test_prediction_interval_is_wider_than_the_confidence_interval_and_absent_below_three():
    pooled = aa.dersimonian_laird([0.1, 0.4, 0.7], [0.01, 0.01, 0.01])
    assert pooled.pi_low < pooled.ci_low and pooled.pi_high > pooled.ci_high
    two = aa.dersimonian_laird([0.1, 0.4], [0.01, 0.01])
    assert math.isnan(two.pi_low) and math.isnan(two.pi_high)


def test_dersimonian_laird_refuses_a_non_positive_variance():
    with pytest.raises(ValueError):
        aa.dersimonian_laird([0.1, 0.2], [0.0, 0.01])


def test_paper_level_aggregation_credits_no_precision_gain():
    """Two contrasts in one paper average to one study, with v = mean(v), not mean(v)/2."""
    frame = pd.DataFrame([
        {"dimension": "d", "record_id": "p1", "rel_effect": 0.2, "variance": 0.01,
         "delta_raw": 10.0, "system_id": "s", "benchmark": "b1", "direction": "component_removed",
         "proportion": True, "n_items": 200},
        {"dimension": "d", "record_id": "p1", "rel_effect": 0.4, "variance": 0.03,
         "delta_raw": 20.0, "system_id": "s", "benchmark": "b2", "direction": "component_removed",
         "proportion": True, "n_items": 400},
    ])
    papers = aa.aggregate_to_papers(frame)
    assert len(papers) == 1
    assert papers.iloc[0]["n_contrasts"] == 2
    assert papers.iloc[0]["y"] == pytest.approx(0.3)
    assert papers.iloc[0]["v"] == pytest.approx(0.02)
    assert papers.iloc[0]["delta_raw"] == pytest.approx(15.0)
    assert papers.iloc[0]["n_items"] == pytest.approx(300.0)


# ------------------------------------------------------------------------------------------------
# 4. a dimension with two papers is reported, unpooled
# ------------------------------------------------------------------------------------------------
def _contrast_frame(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    """rows: (dimension, record_id, rel_effect) -> a minimal contrast table."""
    out = []
    for i, (dim, rec, eff) in enumerate(rows):
        out.append({"record_id": rec, "system_id": f"s{i}", "label": "w/o x", "dimension": dim,
                    "category": "ablation", "direction": "component_removed", "confidence": 0.9,
                    "benchmark": f"b{i}", "split": "", "metric": "accuracy", "model": "m",
                    "polarity": "higher", "full_score": 50.0, "ablated_score": 50.0 * (1 - eff),
                    "with_score": 50.0, "without_score": 50.0 * (1 - eff),
                    "delta_raw": 50.0 * eff, "rel_effect": eff, "variance": 0.01,
                    "var_method": "binomial_delta", "n_items": 200, "n_source": "default",
                    "proportion": True, "scale": 100.0})
    return pd.DataFrame(out, columns=aa.CONTRAST_COLUMNS)


def test_a_dimension_with_two_papers_is_reported_but_not_pooled():
    frame = _contrast_frame([
        ("long_term_memory", "p1", 0.10), ("long_term_memory", "p2", 0.20),
        ("long_term_memory", "p3", 0.30), ("self_verification", "p4", 0.15),
        ("self_verification", "p5", 0.25),
    ])
    pooled, _papers = aa.pool_by_dimension(frame, min_papers=3)
    by_dim = pooled.set_index("dimension")
    assert by_dim.loc["long_term_memory", "pooled"] == 1
    assert by_dim.loc["long_term_memory", "verdict"] == "pooled"
    sv = by_dim.loc["self_verification"]
    assert sv["pooled"] == 0
    assert sv["verdict"] == "insufficient evidence"
    assert math.isnan(sv["mu_rel"]) and math.isnan(sv["ci_low"]) and math.isnan(sv["i2"])
    # the raw contrasts are still published, which is the point of reporting it at all
    assert sv["n_papers"] == 2 and sv["n_contrasts"] == 2
    assert sv["raw_effects"] == "0.2500;0.1500"


def test_two_contrasts_from_one_paper_are_one_paper_not_two_studies():
    frame = _contrast_frame([
        ("long_term_memory", "p1", 0.10), ("long_term_memory", "p1", 0.20),
        ("long_term_memory", "p2", 0.30),
    ])
    pooled, papers = aa.pool_by_dimension(frame, min_papers=3)
    row = pooled.iloc[0]
    assert row["n_contrasts"] == 3 and row["n_papers"] == 2
    assert row["pooled"] == 0, "3 contrasts from 2 papers must not be pooled as 3 studies"
    assert len(papers) == 2


def test_no_contrasts_gives_an_empty_table_not_a_crash():
    pooled, papers = aa.pool_by_dimension(pd.DataFrame(columns=aa.CONTRAST_COLUMNS))
    assert pooled.empty and papers.empty
    assert aa.bias_diagnostics(papers, pd.DataFrame(columns=aa.CONTRAST_COLUMNS), pooled).empty


# ------------------------------------------------------------------------------------------------
# 5. Egger's test reproduces a hand-computed value
# ------------------------------------------------------------------------------------------------
def test_eggers_test_reproduces_a_hand_computed_value():
    """se = (1, 1/2, 1/3, 1/4) so precision x = (1, 2, 3, 4); y chosen to give z = (2, 3, 5, 6).

        xbar = 2.5, zbar = 4, Sxx = 5, Sxz = 7
        slope     = 7/5 = 1.4
        intercept = 4 - 1.4*2.5 = 0.5
        residuals = (0.1, -0.3, 0.3, -0.1), SSR = 0.20, df = 2, sigma^2 = 0.1
        var(a)    = sigma^2 * (1/n + xbar^2/Sxx) = 0.1 * (0.25 + 1.25) = 0.15
        t         = 0.5 / sqrt(0.15) = 1.2909944487
        p         = 2 * P(T_2 > t) = 2 * (0.5 - t / (2*sqrt(2 + t^2))) = 0.3258001375
    """
    se = np.array([1.0, 0.5, 1.0 / 3.0, 0.25])
    z = np.array([2.0, 3.0, 5.0, 6.0])
    y = z * se
    v = se ** 2
    out = aa.eggers_test(y.tolist(), v.tolist())
    assert out["k"] == 4
    assert out["slope"] == pytest.approx(1.4)
    assert out["intercept"] == pytest.approx(0.5)
    assert out["se"] == pytest.approx(math.sqrt(0.15))
    assert out["t"] == pytest.approx(0.5 / math.sqrt(0.15))
    assert out["t"] == pytest.approx(1.2909944487, abs=1e-8)
    t = 0.5 / math.sqrt(0.15)
    assert out["p"] == pytest.approx(2 * (0.5 - t / (2 * math.sqrt(2 + t ** 2))), abs=1e-12)
    assert out["p"] == pytest.approx(0.3258001375, abs=1e-9)


def test_eggers_test_is_not_computed_below_three_studies():
    out = aa.eggers_test([0.1, 0.2], [0.01, 0.01])
    assert out["k"] == 2 and math.isnan(out["p"])


def test_a_symmetric_funnel_yields_no_trim_and_fill_studies():
    y = [0.1, 0.2, 0.3, 0.4, 0.5]
    v = [0.01, 0.02, 0.03, 0.02, 0.01]  # precision symmetric about the centre
    out = aa.trim_and_fill(y, v)
    assert out["k0"] == 0
    assert out["mu_filled"] == pytest.approx(out["mu_observed"])


def test_trim_and_fill_pulls_a_one_sided_funnel_towards_zero():
    """Small studies reporting only large effects: the filled estimate must be smaller."""
    y = [0.10, 0.12, 0.45, 0.60, 0.80]
    v = [0.001, 0.001, 0.02, 0.05, 0.09]   # the big effects are all the imprecise ones
    out = aa.trim_and_fill(y, v)
    assert out["k0"] >= 1
    assert out["mu_filled"] < out["mu_observed"]
    assert out["converged"]


def test_the_size_based_small_study_test_is_exact_and_blind_when_every_n_is_the_same():
    """OLS of the effect on the benchmark's item count. n = (100, 200, 300, 400), y = (.4,.3,.2,.1):

        the fit is exact, slope = -0.001, so sigma^2 = 0 and no p is offered - the function must
        report the slope it found and refuse the test rather than divide by zero.
    """
    out = aa.small_study_test_by_size([0.4, 0.3, 0.2, 0.1], [100, 200, 300, 400])
    assert out["slope"] == pytest.approx(-0.001)
    assert out["distinct_n"] == 4
    assert math.isnan(out["p"])

    noisy = aa.small_study_test_by_size([0.40, 0.28, 0.22, 0.10], [100, 200, 300, 400])
    assert noisy["slope"] < 0 and 0.0 < noisy["p"] < 1.0

    blind = aa.small_study_test_by_size([0.4, 0.3, 0.2], [200, 200, 200])
    assert math.isnan(blind["p"]) and blind["distinct_n"] == 1


def test_the_size_test_is_the_one_free_of_the_variance_model_circularity():
    """The approximated variance is a function of the two scores, so Egger is partly self-induced.

    Pinned as a property of `contrast_variance`, because the whole reason the size-based test exists
    is that this is true: two contrasts on the same benchmark with the same full-system score get
    different variances purely because their effects differ.
    """
    small, _ = aa.contrast_variance(50.0, 48.0, proportion=True, scale=100.0, n_items=200)
    large, _ = aa.contrast_variance(50.0, 20.0, proportion=True, scale=100.0, n_items=200)
    assert large > small or small > large, "the variance depends on the effect, not only on n"
    assert small != large


def test_null_fill_sensitivity_shrinks_the_estimate_and_counts_the_nulls():
    y = [0.20, 0.25, 0.30, 0.22]
    v = [0.01, 0.01, 0.01, 0.01]
    out = aa.null_fill_sensitivity(y, v)
    assert out["mu_observed"] > out["mu_one_null_each"] > 0
    assert out["nulls_to_halve"] >= 1


def test_sign_test_counts_the_share_favouring_the_component():
    out = aa.sign_test([0.1, 0.2, 0.3, -0.1])
    assert out["favouring"] == 3 and out["share"] == pytest.approx(0.75)
    allpos = aa.sign_test([0.1] * 10)
    assert allpos["share"] == 1.0
    assert allpos["p_binomial"] == pytest.approx(2 * 0.5 ** 10)


def test_each_dimension_is_discounted_by_its_own_diagnostics_not_by_the_worst_one():
    """A noisy dimension must not set the discount for a clean one.

    Two dimensions: one with a clean, homogeneous set of contrasts and one whose funnel is
    one-sided enough that trim-and-fill nearly wipes it out. The discount applied to the clean
    dimension has to be its own, and the headline number is the median, not the maximum.
    """
    rows = [("clean", f"c{i}", 0.20 + 0.01 * i) for i in range(5)]
    rows += [("skewed", "k0", 0.02), ("skewed", "k1", 0.03), ("skewed", "k2", 0.50),
             ("skewed", "k3", 0.70), ("skewed", "k4", 0.90)]
    frame = _contrast_frame(rows)
    frame.loc[frame["dimension"] == "clean", "dimension"] = "long_term_memory"
    frame.loc[frame["dimension"] == "skewed", "dimension"] = "self_verification"
    # give the skewed dimension a precision gradient so trim-and-fill has something to find
    frame.loc[frame["dimension"] == "self_verification", "variance"] = [0.001, 0.001, 0.02, 0.05, 0.09]
    pooled, papers = aa.pool_by_dimension(frame, min_papers=3)
    bias = aa.bias_diagnostics(papers, frame, pooled)
    verdict = aa.bias_verdict(bias, pooled)
    per_dim = verdict["discount_by_dimension"]
    assert set(per_dim) == {"long_term_memory", "self_verification"}
    assert per_dim["self_verification"] > per_dim["long_term_memory"]
    assert verdict["discount"] == pytest.approx(np.median(sorted(per_dim.values())))

    credible = aa.credible_after_discount(pooled, bias, discount=verdict["discount"],
                                          per_dimension=per_dim)
    factors = credible.set_index("dimension")["discount_factor"]
    assert factors["long_term_memory"] == pytest.approx(1.0 - per_dim["long_term_memory"])
    assert factors["self_verification"] == pytest.approx(1.0 - per_dim["self_verification"])
    assert factors["long_term_memory"] > factors["self_verification"]


def test_bias_verdict_calls_a_near_unanimous_sign_distribution_what_it_is():
    frame = _contrast_frame([("long_term_memory", f"p{i}", 0.1 + 0.02 * i) for i in range(6)])
    pooled, papers = aa.pool_by_dimension(frame, min_papers=3)
    bias = aa.bias_diagnostics(papers, frame, pooled)
    assert math.isnan(bias.iloc[0]["egger_p"]), "equal precisions leave no gradient for Egger"
    verdict = aa.bias_verdict(bias, pooled)
    assert verdict["overall_sign_share"] == 1.0
    assert "what publication bias looks like" in verdict["verdict"]
    assert verdict["discount"] > 0
    assert "circularity" in verdict["egger_caveat"]


# ------------------------------------------------------------------------------------------------
# 6. an unmapped label never reaches the pooled table
# ------------------------------------------------------------------------------------------------
def test_an_unmapped_label_never_reaches_the_pooled_table():
    rows = [candidate(system_id=f"s{i}", record_id=f"p{i}", score=40.0) for i in range(3)]
    rows.append(candidate(system_id="s9", record_id="p9", label="w/o GA", score=10.0))
    classifications = {f"s{i}|w/o memory": cls() for i in range(3)}
    classifications["s9|w/o ga"] = {"category": "unmapped", "dimension": None,
                                    "direction": "unclear", "confidence": 0.3,
                                    "reason": "acronym not defined", "demoted": "no_dimension"}
    own_rows = [own_row(system_id=f"s{i}", score=50.0) for i in range(3)]
    own_rows.append(own_row(system_id="s9", score=50.0))
    frame, drops = aa.build_contrasts(candidates(rows), classifications, own(own_rows))
    assert len(frame) == 3
    assert "w/o GA" not in set(frame["label"])
    assert drops["unmapped"] == 1
    pooled, _ = aa.pool_by_dimension(frame, min_papers=3)
    assert list(pooled["dimension"]) == ["long_term_memory"]
    assert pooled.iloc[0]["n_contrasts"] == 3


@pytest.mark.parametrize("vote,demoted", [
    ({"category": "ablation", "dimension": None, "direction": "component_removed",
      "confidence": 0.9, "reason": "r"}, "no_dimension"),
    ({"category": "ablation", "dimension": "not_a_dimension", "direction": "component_removed",
      "confidence": 0.9, "reason": "r"}, "dimension_not_design"),
    ({"category": "ablation", "dimension": "open_source", "direction": "component_removed",
      "confidence": 0.9, "reason": "r"}, "dimension_not_design"),
    ({"category": "ablation", "dimension": "long_term_memory", "direction": "component_removed",
      "confidence": 0.2, "reason": "r"}, "low_confidence"),
    ({"category": "nonsense", "dimension": "long_term_memory", "direction": "component_removed",
      "confidence": 0.9, "reason": "r"}, "unknown_category"),
])
def test_a_vote_that_cannot_be_trusted_is_demoted_to_unmapped_with_a_reason(vote, demoted):
    """A metadata dimension (layer M) can never be ablated, and a guess is worse than a refusal."""
    out = aa.normalise_vote(vote, aa.design_dimension_keys(DIMS))
    assert out["category"] == "unmapped"
    assert out["dimension"] is None
    assert out["demoted"] == demoted
    assert out["reason"]


def test_a_good_vote_survives_normalisation():
    out = aa.normalise_vote({"category": "ablation", "dimension": "self_verification",
                             "direction": "component_removed", "confidence": 0.85,
                             "reason": "quote says 'without the verifier'"},
                            aa.design_dimension_keys(DIMS))
    assert out == {"category": "ablation", "dimension": "self_verification",
                   "direction": "component_removed", "confidence": 0.85,
                   "reason": "quote says 'without the verifier'", "demoted": ""}


def test_a_non_poolable_category_keeps_its_category_and_loses_its_dimension():
    out = aa.normalise_vote({"category": "rival_system", "dimension": "long_term_memory",
                             "direction": "unclear", "confidence": 0.9, "reason": "r"},
                            aa.design_dimension_keys(DIMS))
    assert out["category"] == "rival_system" and out["dimension"] is None


def test_the_dimension_menu_offers_only_the_31_design_dimensions():
    prompt = aa.classify_system_prompt(DIMS)
    assert len(DIMS) == 38
    assert len(aa.design_dimension_keys(DIMS)) == 31
    assert "long_term_memory  (D2" in prompt or "long_term_memory  (D" in prompt
    for meta in ("open_source", "stars", "first_release_date"):
        assert meta in prompt  # named, but only in the "can NEVER be the answer" list
    assert "can NEVER be the answer" in prompt
    assert "REFUSE TO GUESS" in prompt


# ------------------------------------------------------------------------------------------------
# 7. the cache prevents a second backend call
# ------------------------------------------------------------------------------------------------
def test_the_label_cache_prevents_a_second_backend_call():
    frame = candidates([candidate(system_id=f"s{i}", record_id=f"p{i}") for i in range(5)])
    backend = FakeBackend()
    cache, stats1 = aa.classify_labels(frame, DIMS, {}, backend, cache={}, batch_size=40)
    assert backend.calls == 1
    assert stats1["labels_sent"] == 5 and stats1["labels_cached"] == 0
    assert len(cache) == 5

    cache2, stats2 = aa.classify_labels(frame, DIMS, {}, backend, cache=cache, batch_size=40)
    assert backend.calls == 1, "a cached label must never be sent to the model again"
    assert stats2["calls"] == 0 and stats2["labels_cached"] == 5
    assert cache2 == cache


def test_only_the_uncached_labels_are_sent():
    frame = candidates([candidate(system_id=f"s{i}", record_id=f"p{i}") for i in range(4)])
    backend = FakeBackend()
    cache = {"s0|w/o memory": cls(), "s1|w/o memory": cls()}
    aa.classify_labels(frame, DIMS, {}, backend, cache=cache, batch_size=40)
    assert backend.calls == 1
    assert sorted(backend.seen[0]) == ["s2|w/o memory", "s3|w/o memory"]


def test_batching_splits_the_labels_and_the_cache_round_trips_through_disk(tmp_path):
    frame = candidates([candidate(system_id=f"s{i}", record_id=f"p{i}") for i in range(7)])
    backend = FakeBackend()
    cache, st = aa.classify_labels(frame, DIMS, {}, backend, cache={}, batch_size=3)
    assert backend.calls == 3 and [len(b) for b in backend.seen] == [3, 3, 1]
    assert st["labels_sent"] == 7
    path = tmp_path / "cache.json"
    aa.save_cache(cache, path)
    assert aa.load_cache(path) == cache


def test_no_backend_and_no_cache_classifies_nothing_rather_than_guessing():
    frame = candidates([candidate()])
    cache, st = aa.classify_labels(frame, DIMS, {}, None, cache={})
    assert cache == {} and st["calls"] == 0 and st["labels_sent"] == 0
    contrasts, drops = aa.build_contrasts(frame, cache, own([own_row()]))
    assert contrasts.empty and drops["unclassified"] == 1


def test_a_failed_batch_does_not_lose_the_others():
    class Flaky(FakeBackend):
        def __call__(self, *a, **kw):
            if self.calls == 1:
                self.calls += 1
                raise RuntimeError("usage limit")
            return super().__call__(*a, **kw)

    frame = candidates([candidate(system_id=f"s{i}", record_id=f"p{i}") for i in range(4)])
    backend = Flaky()
    cache, st = aa.classify_labels(frame, DIMS, {}, backend, cache={}, batch_size=2)
    assert st["failed_batches"] == 1
    assert len(cache) == 2


def test_the_cache_stores_the_raw_answer_so_the_confidence_floor_stays_re_runnable():
    """The floor is applied at analysis time, not baked into the cache: no re-call to change it."""
    frame = candidates([candidate()])
    backend = FakeBackend(default=cls(confidence=0.45))
    cache, _ = aa.classify_labels(frame, DIMS, {}, backend, cache={})
    assert cache["sysa|w/o memory"]["raw"]["confidence"] == 0.45
    assert cache["sysa|w/o memory"]["raw"]["dimension"] == "long_term_memory"

    strict = aa.resolve_classifications(cache, DIMS, conf_floor=0.5)
    assert strict["sysa|w/o memory"]["category"] == "unmapped"
    assert strict["sysa|w/o memory"]["demoted"] == "low_confidence"
    assert strict["sysa|w/o memory"]["raw_dimension"] == "long_term_memory", "the demotion is auditable"

    loose = aa.resolve_classifications(cache, DIMS, conf_floor=0.4)
    assert loose["sysa|w/o memory"]["category"] == "ablation"
    assert backend.calls == 1, "changing the floor must not cost a model call"


def test_confidence_sensitivity_pools_at_every_floor_without_a_model_call():
    rows = [candidate(system_id=f"s{i}", record_id=f"p{i}", score=40.0) for i in range(4)]
    cache = {f"s{i}|w/o memory": {"raw": cls(confidence=0.45 if i == 3 else 0.9),
                                  "label": "w/o memory", "own_system_id": f"s{i}"}
             for i in range(4)}
    own_rows = [own_row(system_id=f"s{i}", score=50.0) for i in range(4)]
    table = aa.sensitivity_over_confidence(candidates(rows), cache, DIMS, own(own_rows),
                                          floors=(0.4, 0.5))
    by_floor = table.set_index("conf_floor")
    assert by_floor.loc[0.4, "n_papers"] == 4
    assert by_floor.loc[0.5, "n_papers"] == 3
    assert by_floor.loc[0.5, "mu_rel"] == pytest.approx(by_floor.loc[0.4, "mu_rel"], abs=0.05)


def test_the_prompt_tells_the_model_how_to_read_the_direction_from_the_label():
    prompt = aa.classify_system_prompt(DIMS)
    assert "component_removed" in prompt and "component_added" in prompt
    assert "do not report a dimension with a" in prompt  # the low-confidence instruction
    assert "Do not reflexively answer 0.5" in prompt


# ------------------------------------------------------------------------------------------------
# the variance model, and the candidate filter
# ------------------------------------------------------------------------------------------------
def test_binomial_delta_variance_matches_the_formula():
    """var(r) = (p_wo/p_w)^2 * [ (1-p_wo)/(n p_wo) + (1-p_w)/(n p_w) ], p_w = 0.5, p_wo = 0.4, n = 100."""
    var, method = aa.contrast_variance(50.0, 40.0, proportion=True, scale=100.0, n_items=100)
    expected = (0.4 / 0.5) ** 2 * ((1 - 0.4) / (100 * 0.4) + (1 - 0.5) / (100 * 0.5))
    assert method == "binomial_delta"
    assert var == pytest.approx(expected)
    bigger, _ = aa.contrast_variance(50.0, 40.0, proportion=True, scale=100.0, n_items=400)
    assert bigger == pytest.approx(expected / 4.0)


def test_a_non_proportion_metric_gets_the_flagged_assumed_variance():
    var, method = aa.contrast_variance(3.2, 2.8, proportion=False, scale=100.0, n_items=100)
    assert method == "assumed_rel_se"
    assert var == pytest.approx(aa.ASSUMED_REL_SE ** 2)


def test_benchmark_item_counts_come_from_the_table_where_known():
    n, src = aa.benchmark_items("SWE-bench", "Verified")
    assert (n, src) == (500, "table")
    n, src = aa.benchmark_items("Some Private Benchmark", "", default_n=123)
    assert (n, src) == (123, "default")


def test_is_proportion_metric_needs_the_name_and_the_range():
    assert aa.is_proportion_metric("accuracy", [80.0, 70.0])
    assert aa.is_proportion_metric("pass@1", [0.8, 0.7])
    assert not aa.is_proportion_metric("accuracy", [800.0, 700.0])
    assert not aa.is_proportion_metric("test MSE", [0.4, 0.5])


def test_load_candidates_casts_a_wide_net_but_needs_the_reject_reason(tmp_path):
    rows = [
        {"reason": "not_own_system", "reported_system_name": "Ours w/o memory", "note": ""},
        {"reason": "not_own_system", "reported_system_name": "SWE-agent", "note": "ablation"},
        {"reason": "not_own_system", "reported_system_name": "CodeStory Aide", "note": ""},
        {"reason": "score_not_in_quote", "reported_system_name": "Ours w/o planner", "note": ""},
    ]
    frame = pd.DataFrame([{c: "" for c in REJECT_COLUMNS} | r for r in rows])
    frame["system_id"] = "sysa"
    frame["score"] = "10"
    path = tmp_path / "rejects.csv"
    frame.to_csv(path, index=False)
    out = aa.load_candidates(path)
    assert sorted(out["label"]) == ["Ours w/o memory", "SWE-agent"]
    assert set(out["label_key"]) == {"sysa|ours w/o memory", "sysa|swe-agent"}


def test_load_own_full_rows_keeps_only_the_paper_sourced_rows(tmp_path):
    frame = own([own_row(score=50.0), own_row(system_id="sysb", score=60.0)])
    frame.loc[1, "notes"] = "source=leaderboard; board=SWE-bench"
    path = tmp_path / "results.csv"
    frame.to_csv(path, index=False)
    out = aa.load_own_full_rows(path)
    assert list(out["system_id"]) == ["sysa"]


# ------------------------------------------------------------------------------------------------
# end to end, with the fake backend
# ------------------------------------------------------------------------------------------------
def _write_end_to_end_fixture(tmp_path: Path) -> dict[str, Path]:
    cand_rows, own_rows = [], []
    for i in range(5):  # five papers ablate memory: poolable
        cand_rows.append({"reason": "not_own_system", "system_id": f"s{i}", "record_id": f"p{i}",
                          "reported_system_name": "Ours w/o memory", "benchmark": "SWE-bench",
                          "split": "Verified", "metric": "% resolved", "score": str(40 + i),
                          "model": "gpt-4o", "evidence_quote": "w/o memory", "note": "ablation"})
        own_rows.append(own_row(system_id=f"s{i}", score=50.0))
    for i in range(2):  # two papers ablate verification: reported, not pooled
        cand_rows.append({"reason": "not_own_system", "system_id": f"v{i}", "record_id": f"q{i}",
                          "reported_system_name": "Ours w/o verifier", "benchmark": "SWE-bench",
                          "split": "Verified", "metric": "% resolved", "score": "45",
                          "model": "gpt-4o", "evidence_quote": "w/o verifier", "note": "ablation"})
        own_rows.append(own_row(system_id=f"v{i}", score=50.0))
    cand_rows.append({"reason": "not_own_system", "system_id": "z0", "record_id": "z0",
                      "reported_system_name": "w/o GA", "benchmark": "SWE-bench", "split": "Verified",
                      "metric": "% resolved", "score": "10", "model": "gpt-4o",
                      "evidence_quote": "w/o GA", "note": "ablation"})
    own_rows.append(own_row(system_id="z0", score=50.0))
    rejects = pd.DataFrame([{c: "" for c in REJECT_COLUMNS} | r for r in cand_rows])
    paths = {"rejects": tmp_path / "results_rejects.csv", "results": tmp_path / "results.csv",
             "systems": tmp_path / "systems.json", "out": tmp_path / "analysis",
             "fig": tmp_path / "figures", "cache": tmp_path / "cache.json"}
    rejects.to_csv(paths["rejects"], index=False)
    own(own_rows).to_csv(paths["results"], index=False)
    paths["systems"].write_text(json.dumps([{"id": f"s{i}", "name": f"System {i}"} for i in range(5)]),
                                encoding="utf-8")
    return paths


def test_main_end_to_end_with_a_fake_backend(tmp_path):
    paths = _write_end_to_end_fixture(tmp_path)
    backend = FakeBackend(answers={
        **{f"s{i}|ours w/o memory": cls() for i in range(5)},
        **{f"v{i}|ours w/o verifier": cls(dimension="self_verification") for i in range(2)},
        "z0|w/o ga": {"category": "unmapped", "dimension": None, "direction": "unclear",
                      "confidence": 0.2, "reason": "acronym never defined"},
    })
    code = aa.main([
        "--rejects", str(paths["rejects"]), "--results", str(paths["results"]),
        "--systems", str(paths["systems"]), "--out-dir", str(paths["out"]),
        "--fig-dir", str(paths["fig"]), "--cache", str(paths["cache"]), "--sensitivity",
    ], backend=backend)
    assert code == 0
    assert backend.calls == 1

    pooled = pd.read_csv(paths["out"] / "ablation_pooled.csv")
    by_dim = pooled.set_index("dimension")
    assert by_dim.loc["long_term_memory", "pooled"] == 1
    assert by_dim.loc["long_term_memory", "n_papers"] == 5
    assert by_dim.loc["self_verification", "pooled"] == 0
    assert "w/o GA" not in set(pd.read_csv(paths["out"] / "ablation_contrasts.csv")["label"])

    drops = pd.read_csv(paths["out"] / "ablation_drops.csv").set_index("reason")["rows"]
    assert drops.loc["unmapped"] == 1

    labels = pd.read_csv(paths["out"] / "ablation_labels.csv").set_index("label_key")
    assert labels.loc["z0|w/o ga", "category"] == "unmapped"
    assert "acronym" in labels.loc["z0|w/o ga", "reason"]

    summary = json.loads((paths["out"] / "ablation_summary.json").read_text(encoding="utf-8"))
    assert summary["funnel"]["contrasts"] == 7
    assert "UPPER BOUND" in summary["caveat"]
    assert summary["bias_verdict"]["overall_sign_share"] == 1.0
    assert (paths["out"] / "ablation_sensitivity_n.csv").exists()
    assert (paths["out"] / "ablation_sensitivity_confidence.csv").exists()
    assert summary["label_categories_as_the_model_answered"]["ablation"] == 7

    for stem in ("ablation_forest_long_term_memory", "ablation_funnel"):
        for ext in ("svg", "pdf"):
            assert (paths["fig"] / f"{stem}.{ext}").exists()
    svg = (paths["fig"] / "ablation_funnel.svg").read_text(encoding="utf-8", errors="replace")
    assert "UPPER BOUND" in svg, "every caption must carry the upper-bound caveat"

    # a second run makes no model call at all
    backend2 = FakeBackend()
    assert aa.main([
        "--rejects", str(paths["rejects"]), "--results", str(paths["results"]),
        "--systems", str(paths["systems"]), "--out-dir", str(paths["out"]),
        "--fig-dir", str(paths["fig"]), "--cache", str(paths["cache"]), "--no-render",
    ], backend=backend2) == 0
    assert backend2.calls == 0


def test_main_without_a_backend_or_cache_still_writes_the_drop_table(tmp_path):
    paths = _write_end_to_end_fixture(tmp_path)
    assert aa.main([
        "--rejects", str(paths["rejects"]), "--results", str(paths["results"]),
        "--systems", str(paths["systems"]), "--out-dir", str(paths["out"]),
        "--fig-dir", str(paths["fig"]), "--cache", str(paths["cache"]), "--no-render",
    ]) == 0
    drops = pd.read_csv(paths["out"] / "ablation_drops.csv").set_index("reason")["rows"]
    assert drops.loc["unclassified"] == 8
    assert pd.read_csv(paths["out"] / "ablation_pooled.csv").empty
