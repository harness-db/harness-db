"""Tests for scripts/analyse_families.py (Phase 7 task 48).

The tests exist mainly to police the missingness trap: that the bias-corrected statistic does not
manufacture association, that the complete-pairs path and the not_reported-as-a-level path are
genuinely different computations that disagree when they should, that ``unresolved`` cells never
enter any analysis, that the permutation test is reproducible, and that the cluster count is chosen
by the silhouette rather than by eye. No network, no model calls.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import analyse_families as af

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def dim(key: str, *, id_: str | None = None, layer: str = "A", type_: str = "enum", multi: bool = False,
        values: tuple[str, ...] = ()) -> af.Dimension:
    return af.Dimension(
        id=id_ or key.upper()[:2],
        key=key,
        layer=layer,
        name=key.replace("_", " "),
        type=type_,
        multi=multi,
        values=values,
    )


def cell(value=None, *, nr: bool = False, unresolved: bool = False) -> dict:
    out: dict = {"value": value, "confidence": "high", "coder": "test"}
    if nr:
        out["not_reported"] = True
    if unresolved:
        out["unresolved"] = True
    return out


def system(sid: str, coding: dict, name: str | None = None) -> dict:
    return {"id": sid, "name": name or sid.upper(), "coding": coding}


# ---------------------------------------------------------------------------
# 1. corrected Cramer's V: 0 under independence, 1 under perfect association
# ---------------------------------------------------------------------------


def test_corrected_v_is_exactly_zero_on_an_exactly_independent_table():
    # outer product table -> chi2 is identically 0, so the corrected statistic must be 0, not noise
    rows = np.array([100.0, 200.0, 300.0])
    cols = np.array([0.2, 0.3, 0.5])
    table = np.outer(rows, cols)
    a = af.cramers_v_from_table(table)
    assert a.chi2 == pytest.approx(0.0, abs=1e-9)
    assert a.v_raw == pytest.approx(0.0, abs=1e-9)
    assert a.v_corrected == pytest.approx(0.0, abs=1e-12)


def test_corrected_v_is_near_zero_on_independent_random_data_while_raw_v_is_inflated():
    """On sparse independent tables the raw statistic is visibly inflated; the corrected one is ~0."""
    rng = np.random.default_rng(7)
    n = 500
    raw, corr = [], []
    for _ in range(25):
        a = rng.integers(0, 6, n)       # 6 levels
        b = rng.integers(0, 7, n)       # 7 levels -> a sparse 6x7 table, where raw V is biased up
        assoc = af.cramers_v_from_table(af.contingency(a, b))
        assert assoc.n == n
        assert assoc.v_corrected <= assoc.v_raw
        raw.append(assoc.v_raw)
        corr.append(assoc.v_corrected)
    assert np.mean(raw) > 0.09, "raw Cramer's V is biased away from 0 on sparse independent data"
    assert np.mean(corr) < 0.03, "the Bergsma correction should shrink it to ~0 on average"
    assert np.mean(corr) < np.mean(raw) / 3


def test_corrected_v_is_one_for_a_perfect_association():
    for k in (2, 4, 8):
        table = np.eye(k) * 40.0
        assoc = af.cramers_v_from_table(table)
        assert assoc.v_raw == pytest.approx(1.0, abs=1e-9)
        assert assoc.v_corrected == pytest.approx(1.0, abs=1e-9), f"k={k}"
    # and a perfect (deterministic) mapping from labels, via the sequence API
    labels_a = [f"x{i % 5}" for i in range(250)]
    labels_b = [f"y{i % 5}" for i in range(250)]
    assert af.cramers_v(labels_a, labels_b).v_corrected == pytest.approx(1.0, abs=1e-9)


def test_corrected_v_is_nan_for_a_degenerate_table():
    assert math.isnan(af.cramers_v_from_table(np.array([[10.0, 5.0]])).v_corrected)
    assert math.isnan(af.cramers_v(["a"] * 20, ["b"] * 20).v_corrected)


def test_contingency_drops_empty_levels():
    # level 5 of `a` never occurs; counting it would over-penalise the bias correction
    a = np.array([0, 0, 1, 1, 2, 2])
    b = np.array([0, 1, 0, 1, 0, 1])
    assert af.contingency(a, b).shape == (3, 2)


# ---------------------------------------------------------------------------
# 2. complete pairs vs not_reported-as-a-level must disagree on the trap fixture
# ---------------------------------------------------------------------------


def _trap_corpus(n_complete: int = 60, n_both_nr: int = 140) -> af.Corpus:
    """Two dimensions that are independent where both are coded, but silent on the same systems.

    Complete pairs: 60 systems, values assigned so the 2x2 table is exactly independent -> V = 0.
    NR as a level: 140 further systems are silent on BOTH dimensions, adding a level whose mass
    sits entirely on the diagonal -> a large V that is pure documentation behaviour.
    """
    dims = [dim("dim_one", id_="D1", values=("a", "b")), dim("dim_two", id_="D2", values=("p", "q"))]
    systems = []
    pattern = [("a", "p"), ("a", "q"), ("b", "p"), ("b", "q")]
    for i in range(n_complete):
        v1, v2 = pattern[i % 4]
        systems.append(system(f"c{i}", {"dim_one": cell(v1), "dim_two": cell(v2)}))
    for i in range(n_both_nr):
        systems.append(system(f"n{i}", {"dim_one": cell(nr=True), "dim_two": cell(nr=True)}))
    return af.build_corpus(systems, dims, {"A": "test layer"}, None, min_level_count=1)


def test_complete_pairs_and_nr_as_level_give_different_answers():
    corpus = _trap_corpus()
    v_complete = af.cramers_v(corpus.labels_complete["dim_one"], corpus.labels_complete["dim_two"])
    v_nr = af.cramers_v(corpus.labels_nr["dim_one"], corpus.labels_nr["dim_two"])

    assert v_complete.n == 60, "the complete-pairs path must see only the systems coded on both"
    assert v_nr.n == 200, "the NR path must see every system that is not unresolved"
    assert v_complete.v_corrected == pytest.approx(0.0, abs=1e-9)
    assert v_nr.v_corrected > 0.6, "shared silence alone must manufacture a strong association"
    assert v_nr.v_corrected - v_complete.v_corrected > 0.5


def test_association_table_flags_the_trap_pair_as_a_flipped_conclusion():
    corpus = _trap_corpus()
    table = af.association_table(corpus, n_perm=200, seed=11)
    assert len(table) == 1
    row = table.iloc[0]
    assert row["n_complete"] == 60 and row["n_nr"] == 200
    assert row["v_corrected_complete"] == pytest.approx(0.0, abs=1e-9)
    assert row["v_corrected_nr"] > 0.6
    assert bool(row["flips_conclusion"]) is True
    assert "documentation" in row["flip_kind"]
    assert row["p_perm_complete"] == 1.0          # corrected V of 0 cannot be exceeded from below
    assert row["p_perm_nr"] < 0.05
    assert not bool(row["sig_complete"]) and bool(row["sig_nr"])


def test_nr_level_sentinel_only_appears_in_the_nr_frame():
    corpus = _trap_corpus()
    assert (corpus.labels_nr == af.NR_LEVEL).any().any()
    assert not (corpus.labels_complete == af.NR_LEVEL).any().any()
    # NR cells are NaN in the complete frame
    nr_rows = corpus.states.index[corpus.states["dim_one"] == "not_reported"]
    assert corpus.labels_complete.loc[nr_rows, "dim_one"].isna().all()


# ---------------------------------------------------------------------------
# 3. unresolved cells are always excluded
# ---------------------------------------------------------------------------


def test_cell_state_precedence():
    assert af.cell_state(cell("a")) == "value"
    assert af.cell_state(cell(nr=True)) == "not_reported"
    assert af.cell_state(cell(unresolved=True)) == "unresolved"
    # unresolved wins even if not_reported is also set
    assert af.cell_state({"value": None, "not_reported": True, "unresolved": True}) == "unresolved"
    assert af.cell_state(None) == "missing"
    assert af.cell_state({"value": None}) == "missing"


def test_unresolved_is_excluded_from_both_treatments_and_from_the_distance():
    dims = [dim("dim_one", id_="D1", values=("a", "b")), dim("dim_two", id_="D2", values=("p", "q"))]
    systems = [
        system("s1", {"dim_one": cell("a"), "dim_two": cell("p")}),
        system("s2", {"dim_one": cell("b"), "dim_two": cell("q")}),
        system("s3", {"dim_one": cell(unresolved=True), "dim_two": cell("p")}),
        system("s4", {"dim_one": cell(unresolved=True), "dim_two": cell(unresolved=True)}),
        system("s5", {"dim_one": cell("a"), "dim_two": cell(nr=True)}),
    ]
    corpus = af.build_corpus(systems, dims, {"A": "test"}, None, min_level_count=1)

    assert corpus.states.loc["s3", "dim_one"] == "unresolved"
    for frame in (corpus.labels_complete, corpus.labels_nr):
        assert pd.isna(frame.loc["s3", "dim_one"])
        assert pd.isna(frame.loc["s4", "dim_one"])
        assert pd.isna(frame.loc["s4", "dim_two"])
    # the NR frame labels s5's silence but never s3/s4's unresolved cell
    assert corpus.labels_nr.loc["s5", "dim_two"] == af.NR_LEVEL
    assert corpus.prep["dim_one"].n_unresolved == 2

    # n for each treatment excludes the unresolved rows
    assert af.cramers_v(corpus.labels_complete["dim_one"], corpus.labels_complete["dim_two"]).n == 2
    assert af.cramers_v(corpus.labels_nr["dim_one"], corpus.labels_nr["dim_two"]).n == 3

    # and the distance treats an unresolved cell as unavailable, not as a value
    D, overlap = af.gower_distance(corpus.raw, ["dim_one", "dim_two"])
    i3, i4 = corpus.ids.index("s3"), corpus.ids.index("s4")
    assert overlap[i3, i4] == 0 and math.isnan(D[i3, i4])
    assert overlap[i3, corpus.ids.index("s1")] == 1  # only dim_two is shared


# ---------------------------------------------------------------------------
# 4. the permutation test is reproducible under a fixed seed
# ---------------------------------------------------------------------------


def test_permutation_p_is_reproducible_under_a_fixed_seed():
    rng = np.random.default_rng(5)
    a = rng.integers(0, 3, 200)
    b = (a + rng.integers(0, 2, 200)) % 3
    obs = af.cramers_v_from_table(af.contingency(a, b)).v_corrected
    p1, used1 = af.permutation_p(a, b, obs, 300, np.random.default_rng(123))
    p2, used2 = af.permutation_p(a, b, obs, 300, np.random.default_rng(123))
    p3, _ = af.permutation_p(a, b, obs, 300, np.random.default_rng(456))
    assert used1 == used2 == 300
    assert p1 == p2
    assert 0.0 < p1 <= 1.0
    assert p3 == pytest.approx(p1, abs=0.05)  # different stream, same conclusion


def test_permutation_p_short_circuits_on_a_zero_or_nan_statistic():
    a = np.array([0, 0, 1, 1])
    b = np.array([0, 1, 0, 1])
    assert af.permutation_p(a, b, 0.0, 500, np.random.default_rng(1)) == (1.0, 0)
    p, used = af.permutation_p(a, b, float("nan"), 500, np.random.default_rng(1))
    assert math.isnan(p) and used == 0


def test_association_table_is_reproducible_under_a_fixed_seed():
    corpus = _trap_corpus(n_complete=80, n_both_nr=60)
    t1 = af.association_table(corpus, n_perm=150, seed=99)
    t2 = af.association_table(corpus, n_perm=150, seed=99)
    pd.testing.assert_frame_equal(t1, t2)


def test_bh_and_holm_adjustments():
    p = [0.001, 0.01, 0.02, 0.5, float("nan")]
    q_bh = af.bh_fdr(p)
    q_holm = af.holm(p)
    assert math.isnan(q_bh[4]) and math.isnan(q_holm[4])
    assert q_bh[0] == pytest.approx(0.004)
    assert q_holm[0] == pytest.approx(0.004)
    assert np.all(np.diff(q_bh[:4]) >= -1e-12), "BH values must be monotone in p"
    assert np.all(q_holm[:4] >= q_bh[:4] - 1e-12), "Holm is at least as conservative as BH"


# ---------------------------------------------------------------------------
# 5. silhouette selection recovers a known k
# ---------------------------------------------------------------------------


def _planted_corpus(n_clusters: int = 3, per: int = 40, n_dims: int = 12, noise: float = 0.08,
                    seed: int = 3) -> af.Corpus:
    """A corpus with `n_clusters` planted design families, fully coded, plus a little noise."""
    rng = np.random.default_rng(seed)
    dims = [dim(f"d{j}", id_=f"X{j}", layer="ABC"[j % 3], values=tuple(f"v{c}" for c in range(n_clusters)))
            for j in range(n_dims)]
    systems = []
    for c in range(n_clusters):
        for i in range(per):
            coding = {}
            for j in range(n_dims):
                v = f"v{c}" if rng.random() > noise else f"v{rng.integers(0, n_clusters)}"
                coding[f"d{j}"] = cell(v)
            systems.append(system(f"s{c}_{i}", coding, name=f"Family{c}-System{i}"))
    return af.build_corpus(systems, dims, {"A": "a", "B": "b", "C": "c"}, None, min_level_count=1)


def test_silhouette_selection_picks_the_planted_k():
    corpus = _planted_corpus()
    dist = af.build_distance(corpus, min_coded_share=0.5, min_overlap=3)
    assert len(dist.ids) == 120
    labels, choice = af.choose_k(
        corpus, dist, kmax=7, n_null=4, n_boot=4, min_silhouette=0.25, min_stability=0.6, seed=42
    )
    assert choice.best_k == 3, f"silhouette curve was {dict(zip(choice.ks, choice.silhouettes))}"
    assert choice.best_silhouette > 0.4
    assert choice.families_found is True
    assert "Design families supported" in choice.verdict
    # the planted families are recovered, not just any 3-way split
    truth = np.array([i.split("_")[0] for i in dist.ids])
    from sklearn.metrics import adjusted_rand_score

    assert adjusted_rand_score(truth, labels) > 0.9


def test_choose_k_reports_a_negative_result_when_there_is_no_structure():
    rng = np.random.default_rng(1)
    n_dims = 12
    dims = [dim(f"d{j}", id_=f"X{j}", values=tuple(f"v{c}" for c in range(3))) for j in range(n_dims)]
    systems = [
        system(f"s{i}", {f"d{j}": cell(f"v{rng.integers(0, 3)}") for j in range(n_dims)})
        for i in range(120)
    ]
    corpus = af.build_corpus(systems, dims, {"A": "a"}, None, min_level_count=1)
    dist = af.build_distance(corpus, min_coded_share=0.5, min_overlap=3)
    _, choice = af.choose_k(corpus, dist, kmax=6, n_null=4, n_boot=3, seed=42)
    assert choice.families_found is False
    assert "NEGATIVE RESULT" in choice.verdict


def test_choose_k_is_reproducible_under_a_fixed_seed():
    corpus = _planted_corpus(seed=9)
    dist = af.build_distance(corpus, min_coded_share=0.5, min_overlap=3)
    l1, c1 = af.choose_k(corpus, dist, kmax=5, n_null=3, n_boot=3, seed=7)
    l2, c2 = af.choose_k(corpus, dist, kmax=5, n_null=3, n_boot=3, seed=7)
    assert np.array_equal(l1, l2)
    assert c1.silhouettes == c2.silhouettes
    assert c1.null_p95 == c2.null_p95
    assert c1.stability == c2.stability


def test_permuted_null_preserves_marginals_and_the_missingness_pattern():
    corpus = _trap_corpus(n_complete=40, n_both_nr=40)
    keys = ["dim_one", "dim_two"]
    permuted = af.permute_raw(corpus.raw, keys, np.random.default_rng(3))
    for k in keys:
        assert np.array_equal(corpus.raw[k]["avail"], permuted[k]["avail"]), "missingness must survive"
        before = pd.Series(corpus.raw[k]["x"][corpus.raw[k]["avail"]]).value_counts().sort_index()
        after = pd.Series(permuted[k]["x"][permuted[k]["avail"]]).value_counts().sort_index()
        pd.testing.assert_series_equal(before, after), "marginals must survive"


# ---------------------------------------------------------------------------
# distance, dimension treatments, schema handling
# ---------------------------------------------------------------------------


def test_gower_averages_only_over_dimensions_both_systems_report():
    dims = [dim("a1", id_="A1"), dim("a2", id_="A2"), dim("a3", id_="A3")]
    systems = [
        system("s1", {"a1": cell("x"), "a2": cell("y"), "a3": cell("z")}),
        system("s2", {"a1": cell("x"), "a2": cell("different"), "a3": cell(nr=True)}),
    ]
    corpus = af.build_corpus(systems, dims, {"A": "a"}, None, min_level_count=1)
    D, overlap = af.gower_distance(corpus.raw, ["a1", "a2", "a3"])
    assert overlap[0, 1] == 2, "the not_reported dimension must not enter the denominator"
    assert D[0, 1] == pytest.approx(0.5)


def test_multi_valued_dimension_uses_sorted_value_sets_and_jaccard():
    d = dim("multi", id_="M1", multi=True, values=("a", "b", "c"))
    systems = [
        system("s1", {"multi": cell(["b", "a"])}),
        system("s2", {"multi": cell(["a", "b"])}),
        system("s3", {"multi": cell(["a"])}),
        system("s4", {"multi": cell(["c"])}),
    ]
    corpus = af.build_corpus(systems, [d], {"A": "a"}, None, min_level_count=1)
    labels = corpus.labels_complete["multi"]
    assert labels["s1"] == labels["s2"] == "a+b", "value sets must be order-insensitive"
    assert labels["s3"] == "a"
    D, _ = af.gower_distance(corpus.raw, ["multi"])
    assert D[0, 1] == pytest.approx(0.0)
    assert D[0, 2] == pytest.approx(0.5)   # {a,b} vs {a}: 1 - 1/2
    assert D[2, 3] == pytest.approx(1.0)   # {a} vs {c}
    assert "value-set" in corpus.prep["multi"].treatment


def test_integer_and_date_dimensions_are_binned_from_coded_values_only():
    dims = [dim("count", id_="B2", type_="integer"), dim("released", id_="M5", type_="date")]
    systems = []
    for i in range(20):
        systems.append(system(f"s{i}", {"count": cell(i), "released": cell(f"2025-{(i % 12) + 1:02d}-01")}))
    systems.append(system("sx", {"count": cell(nr=True), "released": cell(nr=True)}))
    corpus = af.build_corpus(systems, dims, {"B": "b", "M": "m"}, None, min_level_count=1, n_bins=4)
    assert corpus.prep["count"].n_levels == 4
    assert corpus.prep["count"].bin_edges
    assert pd.isna(corpus.labels_complete.loc["sx", "count"])
    assert corpus.raw["count"]["kind"] == "num"
    assert corpus.raw["released"]["kind"] == "num"
    # the numeric distance is the normalised absolute difference on the coded range
    D, _ = af.gower_distance(corpus.raw, ["count"])
    assert D[0, 19] == pytest.approx(1.0)
    assert D[0, 1] == pytest.approx(1 / 19)


def test_free_text_string_dimension_is_excluded_with_a_reason():
    dims = [dim("pinned", id_="M6", type_="string"), dim("enum", id_="A1", values=("a", "b"))]
    systems = [system(f"s{i}", {"pinned": cell(f"commit-{i}"), "enum": cell("ab"[i % 2])}) for i in range(30)]
    corpus = af.build_corpus(systems, dims, {"M": "m", "A": "a"}, None, min_level_count=1)
    assert corpus.prep["pinned"].included is False
    assert "free-text" in corpus.prep["pinned"].reason
    assert corpus.raw["pinned"]["kind"] == "skip"
    table = af.association_table(corpus, n_perm=10, seed=1)
    assert bool(table.iloc[0]["excluded"]) is True
    assert math.isnan(table.iloc[0]["v_corrected_complete"])
    # a low-cardinality string dimension is kept
    systems2 = [system(f"s{i}", {"pinned": cell("v1" if i % 2 else "v2"), "enum": cell("a")}) for i in range(30)]
    corpus2 = af.build_corpus(systems2, dims, {"M": "m", "A": "a"}, None, min_level_count=1)
    assert corpus2.prep["pinned"].included is True


def test_rare_levels_are_pooled_and_counted():
    d = dim("enum", id_="A1", values=tuple(f"v{i}" for i in range(10)))
    systems = [system(f"s{i}", {"enum": cell("v0" if i < 40 else f"v{i}")}) for i in range(46)]
    corpus = af.build_corpus(systems, [d], {"A": "a"}, None, min_level_count=5)
    assert (corpus.labels_complete["enum"] == af.RARE_LEVEL).sum() == 6
    assert corpus.prep["enum"].n_levels_pooled == 6
    assert corpus.prep["enum"].n_pooled_systems == 6
    # pooling is disableable
    corpus2 = af.build_corpus(systems, [d], {"A": "a"}, None, min_level_count=1)
    assert not (corpus2.labels_complete["enum"] == af.RARE_LEVEL).any()


def test_weighted_v_uses_the_kish_effective_sample_size():
    a = np.array([0, 0, 1, 1] * 25)
    b = np.array([0, 1, 0, 1] * 25)
    w_flat = np.ones(100)
    unweighted = af.cramers_v_from_table(af.contingency(a, b))
    weighted = af.weighted_cramers_v(a, b, w_flat)
    assert weighted.n == 100
    assert weighted.v_corrected == pytest.approx(unweighted.v_corrected, abs=1e-9)
    # unequal weights shrink the effective n below the raw n
    w = np.where(a == 0, 1.0, 40.0)
    assert af.weighted_cramers_v(a, b, w).n < 100


def test_load_dimensions_reads_ids_keys_layers_and_multi(tmp_path: Path):
    payload = {
        "schema_version": "9.9.9",
        "layers": [{"id": "A", "name": "Context assembly"}],
        "dimensions": [
            {"id": "A1", "key": "k1", "layer": "A", "name": "One", "type": "enum", "multi": False, "values": ["x"]},
            {"id": "A2", "key": "k2", "layer": "A", "name": "Two", "type": "enum", "multi": True, "values": ["y"]},
        ],
    }
    p = tmp_path / "dimensions.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    dims, layers = af.load_dimensions(p)
    assert [d.id for d in dims] == ["A1", "A2"]
    assert [d.multi for d in dims] == [False, True]
    assert layers == {"A": "Context assembly"}
    assert dims[0].label == "A1 k1"


def test_matrix_from_table_is_symmetric_with_a_nan_diagonal():
    corpus = _planted_corpus(n_clusters=2, per=10, n_dims=4)
    table = af.association_table(corpus, n_perm=10, seed=2)
    mat = af.matrix_from_table(table, corpus.dims, "v_corrected_complete")
    arr = mat.to_numpy(dtype=float)
    assert mat.shape == (4, 4)
    assert np.all(np.isnan(np.diag(arr)))
    assert np.allclose(arr, arr.T, equal_nan=True)


# ---------------------------------------------------------------------------
# end to end
# ---------------------------------------------------------------------------


def test_end_to_end_writes_every_table_and_figure(tmp_path: Path):
    rng = np.random.default_rng(4)
    n_dims = 10
    schema = {
        "schema_version": "test",
        "layers": [{"id": "A", "name": "A layer"}, {"id": "B", "name": "B layer"}],
        "dimensions": [
            {
                "id": f"X{j}",
                "key": f"d{j}",
                "layer": "A" if j < 5 else "B",
                "name": f"dim {j}",
                "type": "enum",
                "multi": j == 9,
                "values": ["v0", "v1", "v2"],
            }
            for j in range(n_dims)
        ],
    }
    (tmp_path / "schema").mkdir()
    (tmp_path / "schema" / "dimensions.json").write_text(json.dumps(schema), encoding="utf-8")

    systems = []
    frame_rows = []
    for c in range(3):
        for i in range(30):
            coding = {}
            for j in range(n_dims):
                if rng.random() < 0.25:                      # documentation silence
                    coding[f"d{j}"] = cell(nr=True)
                elif rng.random() < 0.02:
                    coding[f"d{j}"] = cell(unresolved=True)
                else:
                    v = f"v{c}" if rng.random() > 0.15 else f"v{rng.integers(0, 3)}"
                    coding[f"d{j}"] = cell([v] if j == 9 else v)
            sid = f"s{c}_{i}"
            systems.append(system(sid, coding, name=f"Fam{c} Sys{i}"))
            frame_rows.append({"system_id": sid, "stratum": "HPO"[c], "weight": [1.0, 4.55, 48.37][c]})
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "systems.json").write_text(json.dumps(systems), encoding="utf-8")
    pd.DataFrame(frame_rows).to_csv(tmp_path / "data" / "coding_frame.csv", index=False)

    tables = tmp_path / "out" / "analysis"
    figures = tmp_path / "out" / "figures"
    rc = af.main(
        [
            "--systems", str(tmp_path / "data" / "systems.json"),
            "--dimensions", str(tmp_path / "schema" / "dimensions.json"),
            "--frame", str(tmp_path / "data" / "coding_frame.csv"),
            "--tables", str(tables),
            "--figures", str(figures),
            "--n-perm", "40", "--n-null", "3", "--n-boot", "3", "--kmax", "5",
            "--min-coded-share", "0.4", "--min-overlap", "3", "--min-level-count", "1",
            "--seed", "5", "--quiet",
        ]
    )
    assert rc == 0
    for name in (
        "family_dimension_diagnostics.csv",
        "family_associations.csv",
        "family_associations_top.csv",
        "family_nr_flips.csv",
        "family_clusters.csv",
        "family_cluster_summary.csv",
        "family_cluster_markers.csv",
        "family_summary.json",
    ):
        assert (tables / name).exists(), name
        assert (tables / name).stat().st_size > 0
    for stem in ("family_association_matrix", "family_association_delta", "family_dendrogram", "family_clusters_mds"):
        for ext in ("svg", "pdf"):
            assert (figures / f"{stem}.{ext}").stat().st_size > 1000, f"{stem}.{ext}"

    summary = json.loads((tables / "family_summary.json").read_text(encoding="utf-8"))
    assert summary["association"]["n_pairs"] == n_dims * (n_dims - 1) // 2
    assert summary["cells"]["unresolved"] > 0
    assert "families_found" in summary["clustering"]
    assert summary["clustering"]["distance"].startswith("Gower")

    assoc = pd.read_csv(tables / "family_associations.csv")
    assert assoc["n_complete"].max() <= 90
    assert (assoc["n_nr"] >= assoc["n_complete"]).all(), "the NR path can only ever add systems"
    diag = pd.read_csv(tables / "family_dimension_diagnostics.csv")
    assert len(diag) == n_dims
    assert diag["n_unresolved"].sum() > 0
    clusters = pd.read_csv(tables / "family_clusters.csv")
    assert {"cluster", "coded_share", "silhouette", "stratum", "weight"} <= set(clusters.columns)


def test_dominance_ceiling_guard_rejects_an_outlier_peel():
    """Without the guard, peeling two outliers off pure noise is declared a design family."""
    corpus_dims = [dim(f"d{j}", id_=f"X{j}", values=tuple(f"v{c}" for c in range(4))) for j in range(12)]
    rng = np.random.default_rng(6)
    systems = [
        system(f"m{i}", {f"d{j}": cell(f"v{rng.integers(0, 4)}") for j in range(12)}, name=f"Noise{i}")
        for i in range(120)
    ]
    for i in range(2):                      # two systems unlike everything else
        systems.append(system(f"out{i}", {f"d{j}": cell("zz") for j in range(12)}, name=f"Outlier{i}"))
    corpus = af.build_corpus(systems, corpus_dims, {"A": "a"}, None, min_level_count=1)
    dist = af.build_distance(corpus, min_coded_share=0.5, min_overlap=3)

    _, unguarded = af.choose_k(corpus, dist, kmax=8, n_null=2, n_boot=2, max_cluster_frac=1.0,
                               sensitivity=False, seed=13)
    _, guarded = af.choose_k(corpus, dist, kmax=8, n_null=2, n_boot=2, max_cluster_frac=0.90,
                             sensitivity=False, seed=13)
    # the data are noise, so the honest answer is "no families"; only the guard gets there
    assert unguarded.best_k == 2 and unguarded.families_found is True
    assert unguarded.largest_cluster_frac[0] > 0.9
    assert guarded.eligible[0] is False, "the outlier peel must be ruled ineligible"
    assert guarded.families_found is False
    assert guarded.largest_cluster_frac[guarded.ks.index(guarded.best_k)] <= 0.90


def test_all_degenerate_k_is_reported_as_evidence_against_families():
    """If every k only peels outliers off one mass, that is a negative result in itself."""
    corpus_dims = [dim(f"d{j}", id_=f"X{j}", values=tuple(f"v{c}" for c in range(3))) for j in range(12)]
    rng = np.random.default_rng(5)
    systems = [
        system(f"m{i}", {f"d{j}": cell("v0" if rng.random() > 0.05 else "v1") for j in range(12)})
        for i in range(60)
    ]
    for i in range(4):
        systems.append(system(f"o{i}", {f"d{j}": cell(f"z{i}") for j in range(12)}))
    corpus = af.build_corpus(systems, corpus_dims, {"A": "a"}, None, min_level_count=1)
    dist = af.build_distance(corpus, min_coded_share=0.5, min_overlap=3)
    _, choice = af.choose_k(corpus, dist, kmax=6, n_null=2, n_boot=2, max_cluster_frac=0.90,
                            sensitivity=False, seed=8)
    assert all(m > 0.90 for m in choice.largest_cluster_frac)
    assert choice.families_found is False
    assert "peels outliers" in choice.verdict
    assert all(choice.eligible), "with no eligible k the guard is relaxed so a partition can be described"


def test_linkage_sensitivity_covers_the_admissible_linkages_only():
    corpus = _planted_corpus(seed=21)
    dist = af.build_distance(corpus, min_coded_share=0.5, min_overlap=3)
    _, choice = af.choose_k(corpus, dist, kmax=5, n_null=1, n_boot=1, sensitivity=True, seed=3)
    assert set(choice.linkage_sensitivity) == {"average", "complete", "weighted", "single"}
    for rec in choice.linkage_sensitivity.values():
        assert len(rec["silhouettes"]) == len(choice.ks)
        assert -1.0 <= rec["cophenetic_correlation"] <= 1.0
    # ward/centroid assume Euclidean coordinates and must not be reported for a Gower distance
    assert "ward" not in choice.linkage_sensitivity
