"""Tests for scripts/analyse_blocks.py (RQ3 within-paper comparison blocks).

No network, no model calls, no data file is read: every fixture is built in the test. The point is
not coverage, it is that the claims a reader would take at face value are pinned to something
computable by hand:

* a block forms on the EXACT key and a block with one arm is dropped;
* the within-block standardisation rule (z at 4+ arms, standardised rank below that, 0 when
  degenerate) is exact, and identical to the cross-paper convention in analyse_outcomes.py;
* the bootstrap resamples BLOCKS, not rows or arms - checked against an explicit seeded draw;
* excluding the authors' own arm changes a planted result, which is the whole design;
* a block whose comparators are all ablations is routed out and counted, not silently dropped;
* attribution abstains on an ambiguous name and on a vetoed one, and records the refusal.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("analyse_blocks", ROOT / "scripts" / "analyse_blocks.py")
ab = importlib.util.module_from_spec(SPEC)
sys.modules["analyse_blocks"] = ab
SPEC.loader.exec_module(ab)

import leaderboards_to_results as LB  # imported after the sys.path insert above


# ------------------------------------------------------------------------------------------------
# helpers: fixtures that never touch data/
# ------------------------------------------------------------------------------------------------
def fake_registry(names: dict[str, list[str]], repos: dict[str, str] | None = None) -> LB.Registry:
    """A registry holding exactly the systems given, built through the real RegName machinery."""
    reg = LB.Registry()
    for sid, variants in names.items():
        reg.name_of[sid] = variants[0]
        for name in variants:
            rn = LB._reg_name(sid, name)
            assert rn is not None
            reg.coded_by_key.setdefault(rn.key, set()).add(sid)
            reg.coded_names.append(rn)
            reg.keys_of_system.setdefault(sid, set()).add(rn.key)
    for sid, repo in (repos or {}).items():
        reg.repo_of[sid] = repo
    return reg


def comparator_rows(rows: list[dict]) -> pd.DataFrame:
    """The columns `build_arm_table` needs from a `results_rejects.csv` comparator row."""
    frame = pd.DataFrame(rows)
    for col, default in (("split", ""), ("metric", "accuracy"), ("model", "gpt-4o"),
                         ("note", ""), ("system_id", "own-sys")):
        if col not in frame.columns:
            frame[col] = default
    frame["score_num"] = frame["score"].astype(float)
    return frame


def own_rows(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for col, default in (("split", ""), ("metric", "accuracy"), ("model", "gpt-4o")):
        if col not in frame.columns:
            frame[col] = default
    frame["score_num"] = frame["score"].astype(float)
    return frame


def empty_own() -> pd.DataFrame:
    return own_rows([]) if False else pd.DataFrame(
        columns=["system_id", "record_id", "benchmark", "split", "metric", "model", "score_num"])


def plain_attributor(names: dict[str, list[str]] | None = None) -> ab.Attributor:
    return ab.Attributor(registry=fake_registry(names or {"react": ["ReAct"]}))


def arms_from(comparators: pd.DataFrame, own: pd.DataFrame,
              attributor: ab.Attributor | None = None) -> pd.DataFrame:
    return ab.build_arm_table(comparators, own, attributor or plain_attributor())


# ------------------------------------------------------------------------------------------------
# 1. blocks form on the exact key
# ------------------------------------------------------------------------------------------------
def test_block_key_is_exact_and_only_case_and_whitespace_folded():
    a = ab.block_key("arxiv:1", "SWE-bench", "Verified", "% resolved", "GPT-4o")
    b = ab.block_key("arxiv:1", "swe-bench", " verified ", "%  resolved", "gpt-4o")
    assert a == b == "arxiv:1|swe-bench|verified|% resolved|gpt-4o"
    # everything else keeps blocks apart: a different paper, split, metric or model is another block
    assert ab.block_key("arxiv:2", "SWE-bench", "Verified", "% resolved", "GPT-4o") != a
    assert ab.block_key("arxiv:1", "SWE-bench", "Lite", "% resolved", "GPT-4o") != a
    assert ab.block_key("arxiv:1", "SWE-bench", "Verified", "pass@1", "GPT-4o") != a
    assert ab.block_key("arxiv:1", "SWE-bench", "Verified", "% resolved", "GPT-4.1") != a
    # no benchmark canonicalisation: "SWE-bench Verified" as one string is NOT the same block
    assert ab.block_key("arxiv:1", "SWE-bench Verified", "", "% resolved", "GPT-4o") != a


def test_arms_group_on_the_exact_block_key_and_collapse_repeated_rows():
    comparators = comparator_rows([
        {"record_id": "arxiv:1", "benchmark": "SWE-bench", "split": "Verified",
         "reported_system_name": "ReAct", "score": 10.0},
        {"record_id": "arxiv:1", "benchmark": "swe-bench", "split": "verified",
         "reported_system_name": "ReAct", "score": 20.0},  # same block, same arm -> median
        {"record_id": "arxiv:1", "benchmark": "SWE-bench", "split": "Lite",
         "reported_system_name": "ReAct", "score": 99.0},  # different split -> different block
        {"record_id": "arxiv:2", "benchmark": "SWE-bench", "split": "Verified",
         "reported_system_name": "ReAct", "score": 30.0},  # different paper -> different block
    ])
    arms = arms_from(comparators, empty_own())
    assert set(arms["block"]) == {
        "arxiv:1|swe-bench|verified|accuracy|gpt-4o",
        "arxiv:1|swe-bench|lite|accuracy|gpt-4o",
        "arxiv:2|swe-bench|verified|accuracy|gpt-4o",
    }
    merged = arms[arms["block"] == "arxiv:1|swe-bench|verified|accuracy|gpt-4o"].iloc[0]
    assert merged["n_rows"] == 2
    assert merged["score"] == pytest.approx(15.0)  # median of 10 and 20
    assert merged["row_min"] == 10.0 and merged["row_max"] == 20.0


# ------------------------------------------------------------------------------------------------
# 2. a block with one arm is dropped
# ------------------------------------------------------------------------------------------------
def test_single_arm_blocks_are_dropped_and_counted():
    comparators = comparator_rows([
        {"record_id": "arxiv:1", "benchmark": "B", "reported_system_name": "ReAct", "score": 1.0},
        {"record_id": "arxiv:1", "benchmark": "B", "reported_system_name": "Rival", "score": 2.0},
        {"record_id": "arxiv:2", "benchmark": "B", "reported_system_name": "ReAct", "score": 3.0},
    ])
    arms = arms_from(comparators, empty_own())
    kept, dropped = ab.drop_single_arm_blocks(arms)
    assert dropped == 1
    assert set(kept["block"]) == {"arxiv:1|b||accuracy|gpt-4o"}
    assert len(kept) == 2


def test_one_comparator_plus_the_own_arm_is_a_block():
    """Two arms is a comparison even when one of them is the paper's own system."""
    comparators = comparator_rows([
        {"record_id": "arxiv:1", "benchmark": "B", "reported_system_name": "Rival", "score": 1.0},
    ])
    own = own_rows([{"record_id": "arxiv:1", "benchmark": "B", "system_id": "own-sys",
                     "score": 2.0}])
    kept, dropped = ab.drop_single_arm_blocks(arms_from(comparators, own))
    assert dropped == 0
    assert set(kept["role"]) == {"comparator", "own"}


# ------------------------------------------------------------------------------------------------
# 3. the within-block standardisation rule, exactly
# ------------------------------------------------------------------------------------------------
def _std_frame(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"block": ["b"] * len(values), "value": values})


def test_zscore_rule_applies_at_four_or_more_arms():
    out = ab.standardise_within_block(_std_frame([1.0, 2.0, 3.0, 4.0]), rank_threshold=4)
    assert set(out["std_method"]) == {"zscore"}
    expected = (np.array([1.0, 2.0, 3.0, 4.0]) - 2.5) / np.std([1, 2, 3, 4], ddof=1)
    assert out["z"].to_numpy() == pytest.approx(expected)
    assert out["z"].mean() == pytest.approx(0.0)
    assert float(np.std(out["z"], ddof=1)) == pytest.approx(1.0)


def test_rank_rule_below_the_threshold_is_exactly_minus_one_zero_plus_one_at_n_three():
    out = ab.standardise_within_block(_std_frame([5.0, 9.0, 7.0]), rank_threshold=4)
    assert set(out["std_method"]) == {"rank"}
    assert out["z"].to_numpy() == pytest.approx([-1.0, 1.0, 0.0])


def test_rank_rule_at_n_two_is_plus_minus_one_over_sqrt_two():
    out = ab.standardise_within_block(_std_frame([3.0, 8.0]), rank_threshold=4)
    assert out["z"].to_numpy() == pytest.approx([-0.7071067811865475, 0.7071067811865475])


def test_degenerate_block_is_zero_not_a_division_by_zero():
    out = ab.standardise_within_block(_std_frame([4.0, 4.0, 4.0, 4.0]), rank_threshold=4)
    assert set(out["std_method"]) == {"degenerate"}
    assert out["z"].to_numpy() == pytest.approx([0.0, 0.0, 0.0, 0.0])


def test_standardisation_matches_the_cross_paper_convention_in_analyse_outcomes():
    """The two analyses must be readable together, so the rule has to be the same rule."""
    import analyse_outcomes as ao

    values = [1.0, 2.0, 3.0, 9.0]
    mine = ab.standardise_within_block(_std_frame(values), rank_threshold=4)
    theirs = ao.standardise_within_key(
        pd.DataFrame({"comparable_key": ["k"] * 4, "system_id": list("abcd"), "score": values}),
        rank_threshold=4,
    )
    assert mine["z"].to_numpy() == pytest.approx(theirs["z"].to_numpy())
    assert list(mine["std_method"]) == list(theirs["std_method"])


def test_lower_is_better_metric_is_negated_before_standardising():
    comparators = comparator_rows([
        {"record_id": "arxiv:1", "benchmark": "B", "metric": "wall time (s)",
         "reported_system_name": "Fast", "score": 10.0},
        {"record_id": "arxiv:1", "benchmark": "B", "metric": "wall time (s)",
         "reported_system_name": "Slow", "score": 90.0},
    ])
    arms = ab.annotate_blocks(arms_from(comparators, empty_own()))
    fast = arms[arms["arm_label"] == "Fast"].iloc[0]
    slow = arms[arms["arm_label"] == "Slow"].iloc[0]
    assert fast["direction"] == "lower"
    assert fast["z_all"] > slow["z_all"]  # the quicker arm is the better arm


def test_metric_direction_reads_the_look_alikes_correctly():
    assert ab.metric_direction("accuracy (%)") == "higher"
    assert ab.metric_direction("Avg. Time per Question (s)") == "lower"
    assert ab.metric_direction("Total Cost") == "lower"
    assert ab.metric_direction("Throughput (steps/h)") == "higher"  # contains "steps"
    assert ab.metric_direction("Final Net Worth (USD)") == "higher"  # contains "usd"
    assert ab.metric_direction("Err. Fixed") == "higher"  # errors repaired, not errors made
    assert ab.metric_direction("") == "unknown"  # never silently assumed to be higher-is-better


def test_blank_metric_and_mixed_scale_blocks_are_excluded_from_estimation_not_dropped():
    comparators = comparator_rows([
        {"record_id": "arxiv:1", "benchmark": "B", "metric": "", "reported_system_name": "A",
         "score": 1.0},
        {"record_id": "arxiv:1", "benchmark": "B", "metric": "", "reported_system_name": "B",
         "score": 2.0},
        {"record_id": "arxiv:2", "benchmark": "B", "metric": "acc", "reported_system_name": "A",
         "score": 0.42},
        {"record_id": "arxiv:2", "benchmark": "B", "metric": "acc", "reported_system_name": "B",
         "score": 61.0},
    ])
    arms = ab.annotate_blocks(arms_from(comparators, empty_own()))
    reasons = dict(zip(arms["block"], arms["exclusion_reason"]))
    assert reasons["arxiv:1|b|||gpt-4o"] == "metric_direction_unknown"
    assert reasons["arxiv:2|b||acc|gpt-4o"] == "mixed_scale"
    assert not arms["estimable_block"].any()
    assert len(arms) == 4  # excluded from estimation, still in the table


# ------------------------------------------------------------------------------------------------
# 4. the bootstrap resamples BLOCKS, not rows
# ------------------------------------------------------------------------------------------------
def test_bootstrap_resamples_blocks_with_an_explicit_seeded_draw():
    d = [0.5, -0.25, 1.0]
    got = ab.bootstrap_block_means(d, n_boot=64, seed=7)
    rng = np.random.default_rng(7)
    idx = rng.integers(0, 3, size=(64, 3))
    assert got == pytest.approx(np.asarray(d, dtype=float)[idx].mean(axis=1))
    assert len(got) == 64


def test_bootstrap_unit_is_the_block_not_the_arm():
    """A block with many arms must not count more than a block with two.

    The frame below has one block with six arms (difference +1) and two blocks with two arms each
    (difference -1). Resampling BLOCKS gives three equally weighted differences, so the mean is
    -1/3; resampling arms would let the six-arm block dominate and pull the mean positive.
    """
    rows = []
    for i in range(3):
        rows.append({"block": "big", "record_id": "p1", "benchmark": "B", "x": 1.0, "z": 1.0,
                     "std_method": "zscore"})
        rows.append({"block": "big", "record_id": "p1", "benchmark": "B", "x": 0.0, "z": 0.0,
                     "std_method": "zscore"})
    for name in ("small1", "small2"):
        rows.append({"block": name, "record_id": "p2", "benchmark": "B", "x": 1.0, "z": 0.0,
                     "std_method": "rank"})
        rows.append({"block": name, "record_id": "p2", "benchmark": "B", "x": 0.0, "z": 1.0,
                     "std_method": "rank"})
    frame = pd.DataFrame(rows)
    diffs = ab.block_differences(frame)
    assert len(diffs) == 3  # three blocks, not ten arms
    assert sorted(diffs["d"]) == pytest.approx([-1.0, -1.0, 1.0])
    assert diffs["d"].mean() == pytest.approx(-1.0 / 3.0)
    replicates = ab.bootstrap_block_means(diffs["d"].to_numpy(), n_boot=2000, seed=1)
    # Every bootstrap replicate is a mean of three of {+1, -1, -1}: only four values are possible.
    assert set(np.round(replicates, 6)) <= {round(v, 6) for v in
                                            (1.0, 1.0 / 3.0, -1.0 / 3.0, -1.0)}


def test_paper_bootstrap_averages_a_papers_blocks_before_resampling():
    diffs = pd.DataFrame({"record_id": ["p1", "p1", "p2"], "d": [1.0, 3.0, -2.0]})
    got = ab.bootstrap_paper_means(diffs, n_boot=32, seed=5)
    expected = ab.bootstrap_block_means([2.0, -2.0], n_boot=32, seed=5)  # p1 -> mean 2.0
    assert got == pytest.approx(expected)


def test_mde_and_design_floor_are_reported_and_computable_by_hand():
    from scipy import stats as sps

    d = [0.2, 0.9, -0.1, 0.4]
    s = float(np.std(d, ddof=1))
    expected = (sps.t.ppf(0.975, 3) + sps.t.ppf(0.80, 3)) * s / np.sqrt(4)
    assert ab.mde_from_key_differences(d) == pytest.approx(expected)
    # design floor: two blocks of two arms each, one exposed per block -> 2 x 2 = 4 assignments
    frame = pd.DataFrame({
        "block": ["b1", "b1", "b2", "b2"],
        "record_id": ["p1", "p1", "p2", "p2"],
        "benchmark": ["B"] * 4,
        "x": [1.0, 0.0, 1.0, 0.0],
        "z": [1.0, -1.0, 1.0, -1.0],
        "std_method": ["rank"] * 4,
    })
    perm = ab.permutation_test_within_block(frame, n_perm=100, seed=3)
    assert perm["n_assignments"] == 4
    assert perm["p_min_attainable"] == pytest.approx(0.25)
    assert perm["floor_above_05"] is True  # no significance is reachable from two 2-arm blocks


# ------------------------------------------------------------------------------------------------
# 5. excluding the authors' own arm changes a planted result
# ------------------------------------------------------------------------------------------------
def _planted_codings() -> dict:
    def cell(value):
        return {"value": value}
    return {
        "own-sys": {"multi_agent_topology": cell("orchestrator_workers")},
        "solo-rival-a": {"multi_agent_topology": cell("single")},
        "solo-rival-b": {"multi_agent_topology": cell("single")},
        "team-rival": {"multi_agent_topology": cell("pipeline")},
    }


def _planted_arms() -> pd.DataFrame:
    """Three blocks in three papers where the authors' (multi-agent) arm always wins by a mile,
    while among the comparators the multi-agent one always LOSES to the single-agent ones.

    Four arms per block, so the own-arm-inclusive standardisation is a z-score and the
    comparator-only one is a standardised rank over three arms - the two rules the script states.
    """
    rows = []
    for i, paper in enumerate(("p1", "p2", "p3")):
        rows += [
            {"record_id": paper, "benchmark": "B", "reported_system_name": "OwnSystem",
             "score": 95.0 + i, "system_id": "own-sys"},
            {"record_id": paper, "benchmark": "B", "reported_system_name": "TeamRival",
             "score": 10.0 + i, "system_id": "own-sys"},
            {"record_id": paper, "benchmark": "B", "reported_system_name": "SoloRivalA",
             "score": 40.0 + i, "system_id": "own-sys"},
            {"record_id": paper, "benchmark": "B", "reported_system_name": "SoloRivalB",
             "score": 45.0 + i, "system_id": "own-sys"},
        ]
    comparators = comparator_rows([r for r in rows if r["reported_system_name"] != "OwnSystem"])
    own = own_rows([{"record_id": r["record_id"], "benchmark": "B", "system_id": "own-sys",
                     "score": r["score"]}
                    for r in rows if r["reported_system_name"] == "OwnSystem"])
    attributor = ab.Attributor(registry=fake_registry({
        "solo-rival-a": ["SoloRivalA"], "solo-rival-b": ["SoloRivalB"],
        "team-rival": ["TeamRival"]}))
    return ab.annotate_blocks(arms_from(comparators, own, attributor))


def test_excluding_the_authors_arm_flips_the_planted_multi_agent_result():
    arms = _planted_arms()
    contrast = next(c for c in ab.CONTRASTS if c.name == "multi_agent")
    codings = _planted_codings()

    primary = ab.estimate_contrast(arms, contrast, codings, include_own=False, n_boot=500, seed=11)
    secondary = ab.estimate_contrast(arms, contrast, codings, include_own=True, n_boot=500, seed=11)

    # comparator arms only: the multi-agent rival is below the single-agent rival in every block
    assert primary["n_blocks"] == 3
    assert primary["effect"] < 0
    # with the authors' (multi-agent) arm in, the same contrast turns positive
    assert secondary["n_blocks"] == 3
    assert secondary["effect"] > 0
    assert secondary["effect"] > primary["effect"]
    assert secondary["include_own_arm"] is True and primary["include_own_arm"] is False
    assert "OPTIMISTICALLY BIASED" in secondary["arm_policy"]


def test_the_two_standardisations_differ_because_the_own_arm_stretches_the_block():
    arms = _planted_arms()
    team = arms[arms["arm_label"] == "TeamRival"].iloc[0]
    # comparator-only: three arms, so the standardised-rank rule, lowest of three = -1
    assert team["std_method_comp"] == "rank"
    assert team["z_comp"] == pytest.approx(-1.0)
    # with the authors' arm the block has four arms, so the z rule, and the value changes
    assert team["std_method_all"] == "zscore"
    assert team["z_all"] != pytest.approx(team["z_comp"])


def test_own_arm_first_is_counted_and_compared_with_arbitrary_ranking():
    arms = _planted_arms()
    blocks = ab.block_summary(arms)
    stats = ab.own_arm_first_stats(blocks)
    assert stats["blocks_with_own_arm"] == 3
    assert stats["own_first"] == 3
    assert stats["share_first"] == pytest.approx(1.0)
    assert stats["chance_share"] == pytest.approx(0.25)  # four RIVAL arms per block, none ablated
    assert stats["mean_own_rank"] == pytest.approx(1.0)


def test_the_chance_baseline_excludes_the_papers_own_ablation_arms():
    """The reviewer's defect: an ablation arm is not an independently chosen rival comparator.

    A paper's full system beating its own switched-off configuration is the premise of the ablation
    analysis, so those arms must leave the chance denominator. `1 / n_arms` stays available as the
    labelled audit figure.
    """
    assert ab.own_arm_chance(9, 0) == pytest.approx(1 / 9)
    assert ab.own_arm_chance(9, 6) == pytest.approx(1 / 3)
    # every comparator an ablation: no rival could have topped the table, so the null is certainty
    assert ab.own_arm_chance(4, 3) == pytest.approx(1.0)
    assert ab.own_arm_chance(4, 9) == pytest.approx(1.0)  # floored, never a division by zero

    blocks = pd.DataFrame({
        "block": ["b1", "b2"],
        "record_id": ["p1", "p1"],
        "n_arms": [5, 5],
        "n_ablation_arms": [3, 3],
        "n_non_ablation_arms": [2, 2],
        "own_first_chance": [0.5, 0.5],
        "own_first_chance_uncorrected": [0.2, 0.2],
        "has_own_arm": [True, True],
        "own_first": [True, True],
        "own_tied_first": [False, False],
        "own_rank": [1.0, 1.0],
        "own_z_all": [1.0, 1.0],
    })
    stats = ab.own_arm_first_stats(blocks, n_draws=2_000, seed=7)
    assert stats["chance_baseline"] == "1 / max(n_arms - n_ablation_arms, 1)"
    assert stats["expected_by_chance"] == pytest.approx(1.0)
    assert stats["exact_poisson_binomial_p"] == pytest.approx(0.25)
    assert stats["uncorrected"]["expected_by_chance"] == pytest.approx(0.4)
    assert stats["uncorrected"]["exact_poisson_binomial_p"] == pytest.approx(0.04)
    assert stats["n_ablation_arms"] == 6
    # both blocks are one paper, so the clustered null hits both together: p -> 1/2, not 1/4
    assert stats["paper_clustered"]["p"] == pytest.approx(0.5, abs=0.05)
    assert stats["one_block_per_paper"]["blocks"] == 1
    assert len(stats["blocks_detail"]) == 2
    assert stats["blocks_detail"][0]["n_ablation_arms"] == 3


def test_the_paper_clustered_null_is_seeded_and_never_beats_the_independent_one():
    probs = [0.25] * 9
    papers = ["p1"] * 9
    first = ab.paper_clustered_tail(probs, papers, 9, n_draws=5_000, seed=3)
    again = ab.paper_clustered_tail(probs, papers, 9, n_draws=5_000, seed=3)
    assert first == again                      # seeded: the number in the paper is reproducible
    assert first == pytest.approx(0.25, abs=0.03)  # nine blocks of one paper are one draw
    assert first > 0.25 ** 9                   # the independent tail, which is the wrong one here


def test_a_contrast_below_three_blocks_is_not_estimable():
    arms = _planted_arms()
    arms = arms[arms["record_id"] != "p3"]  # leaves two blocks
    contrast = next(c for c in ab.CONTRASTS if c.name == "multi_agent")
    est = ab.estimate_contrast(arms, contrast, _planted_codings(), include_own=False, n_boot=200,
                               seed=11, min_blocks=3)
    assert est["n_blocks"] == 2
    assert est["estimable"] is False
    assert np.isnan(est["ci_low"]) and np.isnan(est["mde_80"])
    assert "NOT ESTIMABLE" in est["power_sentence"]


def test_blocks_from_a_single_paper_cannot_be_called_a_detected_association():
    """The paper is the blocking factor; three blocks of one paper are not three replicates."""
    rows = []
    for i in range(3):
        rows += [
            {"record_id": "p1", "benchmark": f"B{i}", "reported_system_name": "TeamRival",
             "score": 90.0},
            {"record_id": "p1", "benchmark": f"B{i}", "reported_system_name": "SoloRivalA",
             "score": 10.0},
        ]
    attributor = ab.Attributor(registry=fake_registry({
        "solo-rival-a": ["SoloRivalA"], "team-rival": ["TeamRival"]}))
    arms = ab.annotate_blocks(arms_from(comparator_rows(rows), empty_own(), attributor))
    contrast = next(c for c in ab.CONTRASTS if c.name == "multi_agent")
    est = ab.estimate_contrast(arms, contrast, _planted_codings(), include_own=False, n_boot=500,
                               seed=3)
    assert est["n_blocks"] == 3 and est["n_papers"] == 1
    assert est["single_paper"] is True
    assert est["detected"] is False
    assert "NOT INDEPENDENTLY REPLICATED" in est["power_sentence"]


def test_every_pre_specified_contrast_is_reported_even_when_it_never_varies():
    arms = _planted_arms()
    codings = _planted_codings()  # only multi_agent_topology is coded at all
    for contrast in ab.CONTRASTS:
        est = ab.estimate_contrast(arms, contrast, codings, include_own=False, n_boot=100, seed=1)
        assert est["name"] == contrast.name
        assert "power_sentence" in est
        if contrast.name != "multi_agent":
            assert est["n_blocks"] == 0 and est["estimable"] is False


# ------------------------------------------------------------------------------------------------
# 6. all-ablation blocks are routed out and counted
# ------------------------------------------------------------------------------------------------
def test_ablation_label_fires_on_the_label_and_on_the_extractors_note():
    assert ab.ablation_label("w/o Visual Analyst") == "without"
    assert ab.ablation_label("Ret Expert only") == "only_variant"
    assert ab.ablation_label("Variant A", note="ablation: memory removed") == "note_ablation"
    assert ab.ablation_label("DualMem(ours)") == "ours_marker"
    assert ab.ablation_label("ReAct") == ""
    assert ab.ablation_label("OpenHands") == ""
    # a note about the RUN rather than the arm must not route a block out
    assert ab.ablation_label("SWE-agent", note="Only 3 attempted instances; score is a count") == ""


def test_all_ablation_block_is_routed_out_and_counted_while_a_mixed_block_stays():
    comparators = comparator_rows([
        {"record_id": "p1", "benchmark": "B", "reported_system_name": "w/o memory", "score": 1.0},
        {"record_id": "p1", "benchmark": "B", "reported_system_name": "w/o planner", "score": 2.0},
        {"record_id": "p2", "benchmark": "B", "reported_system_name": "w/o memory", "score": 1.0},
        {"record_id": "p2", "benchmark": "B", "reported_system_name": "ReAct", "score": 5.0},
    ])
    arms, _ = ab.drop_single_arm_blocks(arms_from(comparators, empty_own()))
    kept, routed, stats = ab.split_ablation_blocks(arms)
    assert stats["blocks_routed"] == 1
    assert stats["arms_routed"] == 2
    assert stats["patterns"] == {"without": 2}
    assert set(routed["record_id"]) == {"p1"}
    assert set(kept["record_id"]) == {"p2"}
    # the surviving mixed block keeps its ablation arm as an anonymous comparator
    assert (kept["ablation"] != "").sum() == 1
    assert (kept.loc[kept["ablation"] != "", "system_id"] == "").all()


def test_an_ablation_arm_is_never_attributed_to_a_coded_system():
    """Its coding would be the coding of the whole system, not of the variant with a part removed."""
    attributor = plain_attributor({"react": ["ReAct"]})
    assert attributor.attribute("ReAct").system_id == "react"
    refused = attributor.attribute("ReAct w/o reflection")
    assert refused.system_id == ""
    assert refused.method == "refused-ablation"
    assert "ablated variant" in refused.reason


# ------------------------------------------------------------------------------------------------
# 7. attribution abstains and records the refusal
# ------------------------------------------------------------------------------------------------
def test_attribution_abstains_on_an_ambiguous_name_and_records_it():
    attributor = ab.Attributor(registry=fake_registry({
        "camel": ["CAMEL"], "camel-2": ["CAMEL"],  # one key, two coded systems
    }))
    out = attributor.attribute("CAMEL (MASFactory)")
    assert out.system_id == ""
    assert out.method == "ambiguous-exact"
    assert "camel" in out.reason and "camel-2" in out.reason
    assert sum(attributor.vetoes.values()) == 1
    assert any("ambiguous" in reason for reason in attributor.vetoes)
    # and the abstention is auditable in the table the run writes out
    row = attributor.table().iloc[0]
    assert row["system_id"] == "" and row["method"] == "ambiguous-exact"


def test_attribution_records_the_over_merged_group_veto():
    names = {"rci-agent": ["RCI agent", "SWE-agent", "EnIGMA", "Agent S3", "OpenHands",
                           "MentatBot", "AutoCodeRover"]}
    attributor = ab.Attributor(registry=fake_registry(names))
    out = attributor.attribute("SWE-agent")
    assert out.system_id == ""
    assert out.method == "vetoed-exact"
    assert "over-merged" in out.reason
    assert sum(attributor.vetoes.values()) == 1


def test_only_the_leftmost_non_model_part_may_attribute():
    """A paper baseline row names its harness first and the backbone second.

    "MLR-Agent o4-mini-high + Codex" is MLR-Agent's row. Before this guard the right-hand side was
    tried too and the row became a score for `codex`, which is a different coded system.
    """
    attributor = plain_attributor({"codex": ["Codex"], "mlr-agent": ["MLR-Agent"]})
    got = attributor.attribute("MLR-Agent o4-mini-high + Codex")
    assert got.system_id != "codex"
    assert got.system_id == ""  # and the left side is too decorated to match, so it abstains
    # when the left side is a bare model it is dropped, and the harness on the right may match
    assert attributor.attribute("GPT-4-Turbo with ReAct (two-stage)").system_id == ""
    react = plain_attributor({"react": ["ReAct"]})
    assert react.attribute("GPT-4-Turbo with ReAct (two-stage)").system_id == "react"


def test_baseline_table_category_labels_are_refused_even_when_a_coded_system_shares_the_name():
    attributor = plain_attributor({"llm-agent": ["LLM agent"], "harness": ["harness"]})
    for label in ("LLM agent", "LLM Agent", "harness", "Vanilla", "Full Team", "Solo"):
        out = attributor.attribute(label)
        assert out.system_id == "", f"{label!r} should not attribute"
    assert ab.key_of("LLM agent") in ab.EXTRA_STOP_KEYS


def test_fuzzy_threshold_is_above_the_registry_default_and_digits_must_agree():
    import system_registry as sr

    assert ab.LB.FUZZY_THRESHOLD > sr.NAME_THRESHOLD  # 96 > 92, board/table free text needs more
    attributor = plain_attributor({"agent-s": ["Agent S"]})
    # a version bump is a different system under protocol 4.4, and digit groups must agree
    assert attributor.attribute("Agent S2").system_id == ""


def test_an_unattributed_comparator_stays_in_the_block_as_an_anonymous_arm():
    comparators = comparator_rows([
        {"record_id": "p1", "benchmark": "B", "reported_system_name": "ReAct", "score": 1.0},
        {"record_id": "p1", "benchmark": "B", "reported_system_name": "SomeUnknownThing",
         "score": 4.0},
    ])
    arms = ab.annotate_blocks(arms_from(comparators, empty_own()))
    anonymous = arms[arms["arm_label"] == "SomeUnknownThing"].iloc[0]
    assert anonymous["system_id"] == ""
    assert anonymous["role"] == "comparator"
    assert not np.isnan(anonymous["z_comp"])  # it enters the standardisation
    # but it cannot enter a contrast, because it carries no coded design vector
    contrast = next(c for c in ab.CONTRASTS if c.name == "multi_agent")
    frame = ab.contrast_frame(arms, contrast, {"react": {"multi_agent_topology": {"value": "single"}}},
                              include_own=False)
    assert "SomeUnknownThing" not in set(frame["arm_label"])


def test_a_comparator_resolving_to_the_reporting_papers_own_system_is_its_arm_not_a_rivals():
    comparators = comparator_rows([
        {"record_id": "p1", "benchmark": "B", "reported_system_name": "ReAct", "score": 1.0,
         "system_id": "react"},  # the reporting paper IS react here
        {"record_id": "p1", "benchmark": "B", "reported_system_name": "Other", "score": 2.0,
         "system_id": "react"},
    ])
    arms = arms_from(comparators, empty_own())
    roles = dict(zip(arms["arm_label"], arms["role"]))
    assert roles["ReAct"] == "own_variant"
    assert roles["Other"] == "comparator"
