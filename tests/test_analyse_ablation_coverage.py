"""Tests for scripts/analyse_ablation_coverage.py - the two derived statistics behind finding 7b."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import analyse_ablation_coverage as mod

# --------------------------------------------------------------------------- rank helpers


def test_ranks_average_ties():
    assert mod.ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]


def test_spearman_perfect_monotone_is_one():
    assert mod.spearman([1, 2, 3, 4], [5, 6, 7, 8]) == pytest.approx(1.0)


def test_spearman_perfect_inverse_is_minus_one():
    assert mod.spearman([1, 2, 3, 4], [8, 7, 6, 5]) == pytest.approx(-1.0)


def test_spearman_is_rank_based_not_value_based():
    """A monotone transform of y must not change rho - that is the point of using ranks."""
    xs = [1, 2, 3, 4, 5]
    ys = [2, 4, 8, 16, 32]
    assert mod.spearman(xs, ys) == pytest.approx(mod.spearman(xs, [y**3 for y in ys]))


def test_spearman_constant_input_is_zero_not_nan():
    assert mod.spearman([1, 2, 3], [7, 7, 7]) == 0.0


# --------------------------------------------------------------------------- exact permutation p


def test_exact_p_perfect_inverse_is_one_over_n_factorial():
    xs = [1, 2, 3, 4]
    ys = [4, 3, 2, 1]
    assert mod.spearman_exact_p(xs, ys, negative=True) == pytest.approx(1 / math.factorial(4))


def test_exact_p_refuses_to_silently_sample_when_too_large():
    n = mod.MAX_EXACT_N + 1
    with pytest.raises(ValueError, match="exact enumeration refused"):
        mod.spearman_exact_p(list(range(n)), list(range(n)), negative=True)


def test_exact_p_is_a_probability():
    xs = [1, 5, 2, 8, 3]
    ys = [9, 2, 7, 1, 6]
    p = mod.spearman_exact_p(xs, ys, negative=True)
    assert 0.0 < p <= 1.0


# --------------------------------------------------------------------------- Poisson-binomial


def test_poisson_binomial_reduces_to_binomial_when_probs_equal():
    """With equal p it must match the ordinary binomial tail exactly."""
    probs = [0.5] * 6
    expected, p = mod.poisson_binomial_tail(probs, 5)
    binom = sum(math.comb(6, k) * 0.5**6 for k in range(5, 7))
    assert expected == pytest.approx(3.0)
    assert p == pytest.approx(binom)


def test_poisson_binomial_differs_from_binomial_when_probs_vary():
    """The whole reason this exists: a pooled-average binomial gives a different answer."""
    probs = [0.5] * 10 + [0.1] * 10
    _, exact = mod.poisson_binomial_tail(probs, 9)
    mean = sum(probs) / len(probs)
    pooled = sum(math.comb(20, k) * mean**k * (1 - mean) ** (20 - k) for k in range(9, 21))
    assert exact != pytest.approx(pooled, rel=1e-3)


def test_poisson_binomial_tail_at_zero_is_one():
    _, p = mod.poisson_binomial_tail([0.3, 0.4], 0)
    assert p == pytest.approx(1.0)


def test_poisson_binomial_expected_is_sum_of_probs():
    expected, _ = mod.poisson_binomial_tail([0.25, 0.5, 0.125], 1)
    assert expected == pytest.approx(0.875)


# --------------------------------------------------------------------------- layer coverage


@pytest.fixture
def layers():
    return {
        "c_one": "C", "c_two": "C",
        "g_one": "G", "g_two": "G",
        "m_one": "M",
    }


def test_layer_m_is_excluded_from_the_correlation(layers):
    """Metadata cannot be ablated, so its zero must not be allowed to drive the correlation."""
    from collections import Counter
    rows, stats = mod.coverage_by_layer(
        layers, Counter({"c_one": 4, "c_two": 2}), {"C": 25.0, "G": 80.0, "M": 30.0}
    )
    assert stats["excluded_layers"] == ["M"]
    assert "M" not in stats["layers_in_correlation"]
    m_row = next(r for r in rows if r["layer"] == "M")
    assert m_row["in_correlation"] is False


def test_zero_contrast_layers_and_their_dimensions_are_named(layers):
    from collections import Counter
    _, stats = mod.coverage_by_layer(
        layers, Counter({"c_one": 4, "c_two": 2}), {"C": 25.0, "G": 80.0, "M": 30.0}
    )
    assert stats["zero_contrast_layers"] == ["G"]
    assert stats["zero_contrast_dimensions"] == ["g_one", "g_two"]
    assert stats["n_zero_contrast_dimensions"] == 2


def test_contrasts_per_dimension_divides_by_all_dimensions_not_only_ablated_ones(layers):
    """A layer where one of two dimensions is ablated twice has density 1.0, not 2.0."""
    from collections import Counter
    rows, _ = mod.coverage_by_layer(
        layers, Counter({"c_one": 2}), {"C": 25.0, "G": 80.0, "M": 30.0}
    )
    c = next(r for r in rows if r["layer"] == "C")
    assert c["dimensions"] == 2
    assert c["dimensions_ablated"] == 1
    assert c["contrasts_per_dimension"] == 1.0


def test_layer_with_no_silence_figure_is_dropped_from_the_correlation(layers):
    from collections import Counter
    _, stats = mod.coverage_by_layer(layers, Counter({"c_one": 1}), {"C": 25.0, "M": 30.0})
    assert "G" not in stats["layers_in_correlation"]


# --------------------------------------------------------------------------- own-arm test


@pytest.fixture
def blocks_summary():
    """A summary in the pre-correction shape: only `by_arms`, no per-block detail.

    Kept deliberately old-shaped, because `own_arm_test` must still work from it (the by_arms means
    are the documented fallback) while preferring `blocks_detail` when a current run supplies it.
    """
    return {
        "own_arm_ranks_first": {
            "blocks_with_own_arm": 10,
            "own_first": 7,
            "share_first": 0.7,
            "mean_own_rank": 1.4,
            "mean_own_z": 0.3,
            "by_arms": {
                "2": {"blocks": 6, "own_first": 3, "share_first": 0.5, "chance_share": 0.5},
                "5": {"blocks": 4, "own_first": 4, "share_first": 1.0, "chance_share": 0.2},
            },
        }
    }


@pytest.fixture
def blocks_summary_corrected():
    """The current shape: per-block chance probabilities, corrected and uncorrected.

    Two 5-arm blocks in one paper, each holding three of the reporting paper's own ablation arms, so
    the corrected chance is 1/2 per block and the uncorrected one 1/5 - the whole point of the fix.
    """
    detail = [
        {"block": f"p1|b{i}", "record_id": "p1", "n_arms": 5, "n_ablation_arms": 3,
         "n_non_ablation_arms": 2, "chance": 0.5, "chance_uncorrected": 0.2, "own_first": True}
        for i in (1, 2)
    ]
    return {
        "own_arm_ranks_first": {
            "blocks_with_own_arm": 2,
            "own_first": 2,
            "share_first": 1.0,
            "mean_own_rank": 1.0,
            "mean_own_z": 0.8,
            "papers": 1,
            "n_ablation_arms": 6,
            "chance_baseline": "1 / max(n_arms - n_ablation_arms, 1)",
            "paper_clustered": {"p": 0.5, "draws": 10, "seed": 1, "papers": 1},
            "one_block_per_paper": {"blocks": 1, "own_first": 1, "expected_by_chance": 0.5,
                                    "exact_poisson_binomial_p": 0.5, "rule": "largest block"},
            "by_arms": {
                "5": {"blocks": 2, "own_first": 2, "share_first": 1.0, "chance_share": 0.5,
                      "chance_share_uncorrected": 0.2, "ablation_arms": 6},
            },
            "blocks_detail": detail,
        }
    }


def test_own_arm_chance_excludes_the_papers_own_ablation_arms(blocks_summary_corrected):
    """The correction itself: 1/(non-ablation arms), with 1/n_arms kept only as an audit trail."""
    _, stats = mod.own_arm_test(blocks_summary_corrected)
    assert stats["chance_baseline"].startswith("1 / max(n_arms - n_ablation_arms")
    assert stats["expected_by_chance"] == pytest.approx(1.0)      # 2 blocks x 1/2
    assert stats["exact_poisson_binomial_p"] == pytest.approx(0.25)
    # the superseded variant survives as a labelled audit figure, never as the headline
    assert stats["uncorrected"]["expected_by_chance"] == pytest.approx(0.4)   # 2 blocks x 1/5
    assert stats["uncorrected"]["exact_poisson_binomial_p"] == pytest.approx(0.04)
    assert stats["uncorrected"]["exact_poisson_binomial_p"] < stats["exact_poisson_binomial_p"]


def test_own_arm_carries_through_the_paper_clustered_p(blocks_summary_corrected):
    """The clustered p is computed once, in analyse_blocks, and must reach the summary unaltered."""
    _, stats = mod.own_arm_test(blocks_summary_corrected)
    assert stats["paper_clustered"]["p"] == pytest.approx(0.5)
    assert stats["one_block_per_paper"]["blocks"] == 1
    assert "not a second independent measurement" in stats["reading"]


def test_own_arm_uses_per_block_chance_not_a_single_baseline(blocks_summary):
    _, stats = mod.own_arm_test(blocks_summary)
    # 6 blocks at 0.5 + 4 blocks at 0.2 = 3.8 expected
    assert stats["expected_by_chance"] == pytest.approx(3.8)


def test_own_arm_reports_two_arm_blocks_separately_and_flags_no_advantage(blocks_summary):
    """The honest nuance: a two-arm table at exactly chance must not be reported as an advantage."""
    _, stats = mod.own_arm_test(blocks_summary)
    assert stats["two_arms_only"]["above_chance"] is False


def test_own_arm_five_plus_subgroup_is_computed_on_its_own_baseline(blocks_summary):
    _, stats = mod.own_arm_test(blocks_summary)
    f = stats["five_plus_arms"]
    assert f["blocks"] == 4 and f["own_first"] == 4
    assert f["expected_by_chance"] == pytest.approx(0.8)
    assert f["exact_poisson_binomial_p"] == pytest.approx(0.2**4)


def test_own_arm_rows_carry_the_excess_over_chance(blocks_summary):
    rows, _ = mod.own_arm_test(blocks_summary)
    two = next(r for r in rows if r["arms"] == 2)
    five = next(r for r in rows if r["arms"] == 5)
    assert two["excess"] == pytest.approx(0.0)
    assert five["excess"] == pytest.approx(0.8)


# --------------------------------------------------------------------------- end to end


def test_main_writes_both_outputs_and_rejects_unknown_dimensions(tmp_path):
    dims = tmp_path / "dimensions.json"
    dims.write_text(json.dumps([
        {"key": "c_one", "layer": "C", "name": "C one", "id": "C1"},
        {"key": "g_one", "layer": "G", "name": "G one", "id": "G1"},
        {"key": "m_one", "layer": "M", "name": "M one", "id": "M1"},
    ]), encoding="utf-8")

    contrasts = tmp_path / "contrasts.csv"
    contrasts.write_text("dimension\nc_one\nc_one\n", encoding="utf-8")

    nr = tmp_path / "nr.csv"
    nr.write_text(
        "dimension,layer,id,n,not_reported,rate,weighted_rate\n"
        "c_one,C,C1,100,20,0.2,0.25\n"
        "g_one,G,G1,100,80,0.8,0.82\n"
        "m_one,M,M1,100,30,0.3,0.31\n",
        encoding="utf-8",
    )

    out = tmp_path / "out"
    argv = ["--dimensions", str(dims), "--contrasts", str(contrasts),
            "--nr-by-dimension", str(nr), "--out-dir", str(out),
            "--blocks-summary", str(tmp_path / "absent.json")]
    assert mod.main(argv) == 0

    rows = list(csv.DictReader((out / "ablation_coverage_by_layer.csv").open(encoding="utf-8")))
    assert {r["layer"] for r in rows} == {"C", "G", "M"}
    summary = json.loads((out / "ablation_coverage_summary.json").read_text(encoding="utf-8"))
    assert summary["coverage_by_layer"]["zero_contrast_layers"] == ["G"]
    # blocks summary absent -> skipped, not crashed, and not silently faked
    assert "own_arm_test" not in summary
    assert not (out / "blocks_own_arm_test.csv").exists()

    # a contrast naming a dimension outside the schema must stop the run, not be dropped
    contrasts.write_text("dimension\nc_one\nnot_a_dimension\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="absent from the schema"):
        mod.main(argv)


def test_real_outputs_reproduce_the_memo_numbers():
    """Guard the two figures quoted in docs/headline_findings.md finding 7b."""
    path = mod.OUT_DIR / "ablation_coverage_summary.json"
    if not path.exists():
        pytest.skip("run scripts/analyse_ablation_coverage.py first")
        return
    s = json.loads(path.read_text(encoding="utf-8"))
    cov = s["coverage_by_layer"]
    assert cov["excluded_layers"] == ["M"]
    assert sorted(cov["zero_contrast_layers"]) == ["F", "G", "H"]
    assert cov["n_zero_contrast_dimensions"] == 11
    assert cov["spearman_rho"] == pytest.approx(-0.854, abs=0.002)
    assert cov["exact_permutation_p_one_sided"] == pytest.approx(0.0065, abs=0.0005)
    arm = s["own_arm_test"]
    assert arm["own_first"] == 42 and arm["blocks"] == 75
    # The chance baseline excludes the reporting papers' own ablation arms, and with it the OVERALL
    # own-arm advantage does not survive: these pins are the corrected numbers, not the published ones.
    assert arm["chance_baseline"].startswith("1 / max(n_arms - n_ablation_arms")
    assert arm["ablation_arms"] == 89
    assert arm["expected_by_chance"] == pytest.approx(34.95, abs=0.01)
    assert arm["exact_poisson_binomial_p"] == pytest.approx(0.0609, abs=0.0005)
    # blocks are pseudo-replicated within paper; both de-clustered views are non-significant too
    assert arm["paper_clustered"]["p"] == pytest.approx(0.21, abs=0.02)
    assert arm["one_block_per_paper"]["blocks"] == 37
    assert arm["one_block_per_paper"]["own_first"] == 17
    assert arm["one_block_per_paper"]["exact_poisson_binomial_p"] == pytest.approx(0.570, abs=0.005)
    # what survives the correction is the five-or-more-arm subgroup, and only that
    assert arm["five_plus_arms"]["own_first"] == 14
    assert arm["five_plus_arms"]["blocks"] == 17
    assert arm["five_plus_arms"]["expected_by_chance"] == pytest.approx(6.95, abs=0.01)
    assert arm["five_plus_arms"]["exact_poisson_binomial_p"] == pytest.approx(4.4e-4, rel=0.05)
    assert arm["two_arms_only"]["above_chance"] is False
    # the superseded 1/n_arms figures stay in the file, labelled, so the correction is auditable
    assert arm["uncorrected"]["expected_by_chance"] == pytest.approx(27.61, abs=0.01)
    assert arm["uncorrected"]["exact_poisson_binomial_p"] == pytest.approx(2.929e-4, rel=0.05)
    assert arm["uncorrected"]["five_plus_arms"]["expected_by_chance"] == pytest.approx(2.61, abs=0.01)


# --------------------------------------------------------------------------- --corpus


def _corpus_fixture(tmp_path, rows):
    """Four ablatable layers with one dimension each, plus metadata; silence 10/20/30/40 %."""
    dims = tmp_path / "dimensions.json"
    dims.write_text(json.dumps({"layers": [], "dimensions": [
        {"key": "a_one", "layer": "A", "name": "A one", "id": "A1"},
        {"key": "e_one", "layer": "E", "name": "E one", "id": "E1"},
        {"key": "f_one", "layer": "F", "name": "F one", "id": "F1"},
        {"key": "g_one", "layer": "G", "name": "G one", "id": "G1"},
        {"key": "m_one", "layer": "M", "name": "M one", "id": "M1"},
    ]}), encoding="utf-8")
    nr = tmp_path / "nr.csv"
    nr.write_text(
        "dimension,weighted_rate\n"
        "a_one,0.10\ne_one,0.20\nf_one,0.30\ng_one,0.40\nm_one,0.05\n", encoding="utf-8")
    contrasts = tmp_path / "ablation_contrasts_corpus.csv"
    with contrasts.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id", "dimension", "provenance"])
        w.writerows(rows)
    out = tmp_path / "out"
    argv = ["--corpus", "--dimensions", str(dims), "--contrasts", str(contrasts),
            "--nr-by-dimension", str(nr), "--out-dir", str(out)]
    return argv, out


# A: 3 contrasts, E: 1, F: 2, G: 0 - density against silence 10/20/30/40.
CORPUS_ROWS = [
    ("p1", "a_one", "coded_harvest"), ("p2", "a_one", "corpus_fulltext"),
    ("p2", "a_one", "corpus_fulltext"),
    ("p3", "e_one", "coded_harvest"),
    ("p4", "f_one", "corpus_fulltext"), ("p5", "f_one", "corpus_fulltext"),
]


def test_corpus_rho_and_exact_p_reproduce_a_hand_computation(tmp_path):
    """Hand computation, no ties: silence ranks x = (1,2,3,4), density ranks y = (4,2,3,1);
    d = (-3,0,0,3), sum d^2 = 18, rho = 1 - 6*18 / (4*(16-1)) = -0.8. One-sided exact p = share of
    the 24 relabellings of y with sum d^2 >= 18 (rho <= -0.8): (4,3,2,1) 20, (4,2,3,1) 18,
    (4,3,1,2) 18, (3,4,2,1) 18 - four of 24, p = 1/6."""
    argv, out = _corpus_fixture(tmp_path, CORPUS_ROWS)
    assert mod.main(argv) == 0
    cov = json.loads((out / "ablation_coverage_summary_corpus.json").read_text(encoding="utf-8"))
    cov = cov["coverage_by_layer"]
    assert cov["layers_in_correlation"] == ["A", "E", "F", "G"]
    assert cov["spearman_rho"] == pytest.approx(-0.8)
    assert cov["exact_permutation_p_one_sided"] == pytest.approx(1 / 6, abs=1e-6)
    assert cov["permutations"] == 24
    # and an independent brute force of the same hand formula agrees
    from itertools import permutations
    hits = sum(1 for perm in permutations([1, 2, 3, 4])
               if sum((i + 1 - v) ** 2 for i, v in enumerate(perm)) >= 18)
    assert hits / 24 == pytest.approx(cov["exact_permutation_p_one_sided"], abs=1e-6)


def test_corpus_layer_table_carries_the_provenance_split_and_paper_count(tmp_path):
    argv, out = _corpus_fixture(tmp_path, CORPUS_ROWS)
    assert mod.main(argv) == 0
    rows = {r["layer"]: r for r in csv.DictReader(
        (out / "ablation_coverage_by_layer_corpus.csv").open(encoding="utf-8"))}
    assert rows["A"]["contrasts"] == "3"
    assert rows["A"]["contrasts_coded_harvest"] == "1"
    assert rows["A"]["contrasts_other_harvests"] == "2"
    assert rows["A"]["papers"] == "2"
    assert rows["G"]["contrasts"] == "0"
    assert rows["M"]["in_correlation"] == "False"
    cov = json.loads((out / "ablation_coverage_summary_corpus.json").read_text(encoding="utf-8"))
    cov = cov["coverage_by_layer"]
    assert cov["total_contrasts"] == 6
    assert cov["total_papers"] == 5
    assert cov["contrasts_by_provenance"] == {"coded_harvest": 2, "corpus_fulltext": 4}
    assert cov["papers_by_provenance"] == {"coded_harvest": 2, "corpus_fulltext": 3}


def test_corpus_zero_list_is_per_dimension_and_excludes_metadata(tmp_path):
    """Once a harvest touches a layer the layer-level zero list forgets its empty dimensions; the
    per-dimension list must not. Metadata is never listed: it cannot be ablated."""
    rows = CORPUS_ROWS + [("p6", "g_one", "corpus_fulltext")]
    argv, out = _corpus_fixture(tmp_path, [r for r in rows if r[1] != "e_one"])
    assert mod.main(argv) == 0
    cov = json.loads((out / "ablation_coverage_summary_corpus.json").read_text(encoding="utf-8"))
    cov = cov["coverage_by_layer"]
    assert cov["zero_contrast_layers"] == ["E"]
    assert cov["dimensions_without_contrast"] == ["e_one"]
    assert cov["n_dimensions_without_contrast"] == 1
    assert cov["n_ablatable_dimensions"] == 4
    assert cov["dimensions_without_contrast_by_layer"] == {"E": ["e_one"]}
    assert "m_one" not in cov["contrasts_by_dimension"]


def test_corpus_mode_writes_only_suffixed_outputs(tmp_path):
    argv, out = _corpus_fixture(tmp_path, CORPUS_ROWS)
    assert mod.main(argv) == 0
    assert sorted(p.name for p in out.iterdir()) == [
        "ablation_coverage_by_layer_corpus.csv", "ablation_coverage_summary_corpus.json"]


def test_corpus_mode_refuses_a_file_without_provenance(tmp_path):
    argv, _ = _corpus_fixture(tmp_path, CORPUS_ROWS)
    contrasts = Path(argv[argv.index("--contrasts") + 1])
    contrasts.write_text("record_id,dimension\np1,a_one\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="provenance"):
        mod.main(argv)


def test_corpus_mode_refuses_unknown_dimensions(tmp_path):
    argv, _ = _corpus_fixture(tmp_path, CORPUS_ROWS + [("p9", "nope", "corpus_fulltext")])
    with pytest.raises(SystemExit, match="absent from the schema"):
        mod.main(argv)


def test_real_corpus_outputs_are_internally_consistent():
    """Numbers move with the harvest, so this pins structure, not values."""
    path = mod.OUT_DIR / "ablation_coverage_summary_corpus.json"
    if not path.exists():
        pytest.skip("run scripts/analyse_ablation_coverage.py --corpus first")
    cov = json.loads(path.read_text(encoding="utf-8"))["coverage_by_layer"]
    assert cov["excluded_layers"] == ["M"]
    assert sum(cov["contrasts_by_provenance"].values()) == cov["total_contrasts"]
    assert cov["n_dimensions_without_contrast"] == len(cov["dimensions_without_contrast"])
    assert set(cov["dimensions_without_contrast"]) == {
        k for k, n in cov["contrasts_by_dimension"].items() if n == 0}
    assert -1.0 <= cov["spearman_rho"] <= 1.0
    assert 0.0 < cov["exact_permutation_p_one_sided"] <= 1.0
