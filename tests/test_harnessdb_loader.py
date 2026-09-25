"""Tests for the ``harnessdb`` loader package, on the real release in ``data/``.

Counts are the release's (docs/count_reconciliation.md, superseding note of 2026-09-25): 1,256
systems, 47,728 cells = 24,228 coded + 23,337 not_reported + 163 unresolved; strata H 983 / P 157
/ O 116; 1,233 weight-bearing systems with weights summing to 6,503; 23 at weight 0.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
import tomllib
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import harnessdb as hdb
from harnessdb.__main__ import main as cli_main
from harnessdb._stats import ratio_estimate

N_SYSTEMS = 1256
N_CELLS = 47728
N_CODED, N_NR, N_UNRES = 24228, 23337, 163
OUT_OF_SAMPLE = {
    "airtbench-reference-agent", "car", "cfgm", "compagent", "d-artemis", "dive", "docagent",
    "ehragent", "evaluation-agent", "forge", "graphimind", "idea-agent", "incalmo",
    "lightmanus-jarvis", "madevolve", "orchestral", "rci-agent", "seer", "simagent",
    "spider2-v-reference-agent", "storm", "tartanmaroon", "waragent",
}


@pytest.fixture(scope="module")
def db() -> hdb.HarnessDB:
    return hdb.load(REPO)


@pytest.fixture(scope="module")
def schema_raw() -> dict:
    return json.loads((REPO / "schema" / "dimensions.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------ package basics


def test_version_matches_pyproject():
    meta = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    assert hdb.__version__ == meta["project"]["version"]
    assert "harnessdb" in meta["tool"]["setuptools"]["packages"]


def test_load_finds_repo_from_cwd_and_package(monkeypatch, tmp_path):
    monkeypatch.delenv(hdb.ENV_VAR, raising=False)
    monkeypatch.chdir(REPO / "docs")
    assert hdb.locate().systems == (REPO / "data" / "systems.json").resolve()
    monkeypatch.chdir(tmp_path)  # outside the repo: falls back to the package's own location
    src = hdb.locate()
    assert src.kind == "repo" and src.systems == (REPO / "data" / "systems.json").resolve()


def test_load_accepts_data_dir_file_and_env(monkeypatch):
    assert hdb.locate(REPO / "data").schema == (REPO / "schema" / "dimensions.json").resolve()
    assert hdb.locate(REPO / "data" / "systems.json").kind == "repo"
    monkeypatch.setenv(hdb.ENV_VAR, str(REPO / "data"))
    assert hdb.locate().root == (REPO / "data").resolve()


def test_load_bad_path_raises(tmp_path, monkeypatch):
    with pytest.raises(FileNotFoundError):
        hdb.load(tmp_path)
    monkeypatch.setenv(hdb.ENV_VAR, str(tmp_path))
    with pytest.raises(FileNotFoundError):
        hdb.locate()


def test_repr_mentions_counts(db):
    r = repr(db)
    assert "1,256 systems" in r and "47,728 cells" in r


# ------------------------------------------------------------------------ counts equal release


def test_systems_counts_and_columns(db):
    s = db.systems
    assert len(s) == N_SYSTEMS and s["system_id"].is_unique
    for col in ("system_id", "name", "stratum", "weight", "weight_bearing", "papers",
                "n_coded", "n_not_reported", "n_unresolved"):
        assert col in s.columns
    assert s["stratum"].value_counts().to_dict() == {"H": 983, "P": 157, "O": 116}
    assert (s[["n_coded", "n_not_reported", "n_unresolved"]].sum(axis=1) == 38).all()
    assert s["papers"].map(lambda v: isinstance(v, list)).all()


def test_cells_counts_and_columns(db):
    c = db.cells
    assert len(c) == N_CELLS == N_SYSTEMS * 38
    assert list(c.columns[:8]) == ["system_id", "layer", "dimension_key", "state", "value",
                                   "quote", "locator", "confidence"]
    assert c["state"].value_counts().to_dict() == {
        "coded": N_CODED, "not_reported": N_NR, "unresolved": N_UNRES}
    assert set(c["state"].cat.categories) == set(hdb.STATES)
    assert c.groupby("system_id").size().eq(38).all()
    assert c["layer"].nunique() == 9 and c["dimension_key"].nunique() == 38


def test_weights(db):
    s = db.systems
    wb = s[s["weight_bearing"]]
    assert len(wb) == 1233
    assert math.isclose(wb["weight"].sum(), 6503, abs_tol=0.01)
    assert set(s.loc[~s["weight_bearing"], "system_id"]) == OUT_OF_SAMPLE
    assert (s.loc[~s["weight_bearing"], "weight"] == 0).all()
    assert s.loc[s["system_id"].isin(OUT_OF_SAMPLE), "stratum"].value_counts().to_dict() == {
        "O": 16, "P": 7}
    assert db.strata_sizes == {"H": 984.0, "P": 683.0, "O": 4837.0}


def test_results_and_papers(db):
    r, p = db.results, db.papers
    assert len(r) == 5863 and r["system_id"].nunique() == 646
    assert pd.api.types.is_float_dtype(r["score"]) and r["score"].notna().all()
    assert set(r["system_id"]) <= set(db.systems["system_id"])
    assert len(p) == 8538 and int(p["included"].sum()) == 7122
    assert p["included"].dtype == bool
    linked = {pid for ids in db.systems["papers"] for pid in ids}
    assert linked <= set(p["id"])


def test_summary_and_cli(db, capsys):
    s = db.summary()
    assert (s["systems"], s["cells"], s["coded"], s["not_reported"], s["unresolved"]) == (
        N_SYSTEMS, N_CELLS, N_CODED, N_NR, N_UNRES)
    assert s["weight_bearing_systems"] == 1233 and s["weight_zero_systems"] == 23
    assert s["frame_size"] == 6504
    assert not any("rate" in k or "se_" in k for k in s)  # counts only, no estimates
    assert cli_main(["--summary", "--data", str(REPO)]) == 0
    out = capsys.readouterr().out
    for text in ("1,256", "47,728", "24,228", "23,337", "163", "50.8%", "48.9%", "0.3%",
                 "H 983 / P 157 / O 116", "6,504", "1,233", "5,863"):
        assert text in out
    out.encode("ascii")  # printable on a cp1252 Windows console
    assert cli_main(["--json", "--data", str(REPO / "data")]) == 0
    assert json.loads(capsys.readouterr().out)["cells"] == N_CELLS


# ------------------------------------------------------------------------------ the schema


def test_schema(db, schema_raw):
    sc = db.schema
    assert sc["schema_version"] == schema_raw["schema_version"] == sc.version
    assert sc.values("loop_primitives") == ["react", "plan_execute", "generate_test_repair",
                                            "multi_attempt", "tree_search", "event_driven",
                                            "fixed_pipeline"]
    assert sc.values("tool_count") == []
    assert sc.dimension("E1")["key"] == "self_verification"
    assert sc.is_multi("self_verification") and not sc.is_multi("retry_policy")
    assert len(sc.keys_in_order) == 38 and next(iter(sc.layers)) == "A"
    assert len(sc.table) == 38
    with pytest.raises(KeyError):
        sc.values("no_such_dimension")


# ------------------------------------------------------------------------ rule 1: silence


def test_rule1_not_reported_never_has_a_value(db):
    c = db.cells
    silent = c[c["state"] != "coded"]
    assert silent["value"].isna().all()
    coded = c[c["state"] == "coded"]
    assert coded["value"].notna().all()
    wide = db.wide()
    for key in ("self_verification", "network_policy", "tool_count"):
        nr = wide[f"{key}__state"] == "not_reported"
        assert nr.any() and wide.loc[nr, key].isna().all()


def test_rule1_none_is_a_value_not_silence(db):
    t = db.dimension("self_verification").table
    assert "not_reported" not in set(t["value"]) and "unresolved" not in set(t["value"])
    none_rows = db.cells[(db.cells["dimension_key"] == "self_verification")
                         & db.cells["value"].map(lambda v: isinstance(v, list) and "none" in v)]
    assert (none_rows["state"] == "coded").all() and len(none_rows) == 53


def test_rule1_evidence_for_silent_cell(db):
    ev = db.evidence("openhands", "self_verification")
    assert ev.state == "not_reported" and ev.value is None
    assert "value:" not in str(ev)


# --------------------------------------------------------------------- rule 2: unresolved


def test_rule2_unresolved_out_of_every_rate(db):
    nr = db.not_reported(by="dimension")
    assert (nr["n_base"] == nr["n_cells"] - nr["n_unresolved"]).all()
    assert nr["n_unresolved"].sum() == N_UNRES
    assert np.allclose(nr["rate_unweighted"], nr["n_not_reported"] / nr["n_base"])
    overall = db.not_reported(by=None).iloc[0]
    assert overall["n_base"] == N_CELLS - N_UNRES
    assert math.isclose(overall["rate_unweighted"], N_NR / (N_CELLS - N_UNRES))
    d = db.dimension("network_policy")
    assert d.n_unresolved == 3
    assert d.n_coded + d.n_not_reported + d.n_unresolved == N_SYSTEMS
    assert math.isclose(d.not_reported_rate, d.n_not_reported / (N_SYSTEMS - 3))
    assert math.isclose(d.table["share_unweighted"].sum(), 1.0)  # single-valued: shares sum to 1


# ------------------------------------------------------------------- rule 3: weight-bearing


def test_rule3_weighted_uses_only_weight_bearing(db):
    nr = db.not_reported(by="dimension")
    assert (nr["n_weight_bearing"] <= 1233).all()
    full = nr[nr["n_unresolved"] == 0].iloc[0]
    assert full["n_weight_bearing"] == 1233 and math.isclose(full["weight_base"], 6502.995)
    # Out-of-sample systems cannot move a weighted estimate: flip every one of their cells.
    c = db.cells
    key = "tracing"
    sub = c[c["dimension_key"] == key]
    w = sub["system_id"].map(db.systems.set_index("system_id")["weight"]).to_numpy()
    st = sub["system_id"].map(db.systems.set_index("system_id")["stratum"]).to_numpy(object)
    y = (sub["state"] == "not_reported").to_numpy(float)
    base = (sub["state"] != "unresolved").to_numpy(float)
    oos = sub["system_id"].isin(OUT_OF_SAMPLE).to_numpy()
    before = ratio_estimate(y, base, w, st, db.strata_sizes)
    y2 = y.copy()
    y2[oos] = 1 - y2[oos]
    after = ratio_estimate(y2, base, w, st, db.strata_sizes)
    assert before[:3] == after[:3]
    assert math.isclose(before[0], nr.set_index("dimension_key").at[key, "rate_weighted"])


# -------------------------------------------------------- reproduces the paper's analysis


def test_not_reported_by_dimension_matches_analysis_table(db):
    ref = pd.read_csv(REPO / "data" / "analysis" / "under_reporting_by_dimension.csv")
    got = db.not_reported(by="dimension").merge(ref, left_on="dimension_key", right_on="key",
                                                suffixes=("", "_ref"))
    assert len(got) == 38
    for col in ("n_base", "n_not_reported"):
        assert (got[col] == got[f"{col}_ref"]).all()
    for col in ("rate_unweighted", "rate_weighted", "se_weighted", "weight_base"):
        assert np.allclose(got[col], got[f"{col}_ref"], rtol=0, atol=1e-9), col


def test_dimension_matches_value_distributions_table(db):
    ref = pd.read_csv(REPO / "data" / "analysis" / "value_distributions.csv")
    ref = ref[ref["type"] == "enum"]
    checked = 0
    for key, grp in ref.groupby("key"):
        d = db.dimension(key)
        t = d.table.set_index("value")
        assert d.n_coded == int(grp["n_base_coded"].iloc[0])
        assert d.n_not_reported == int(grp["n_not_reported"].iloc[0])
        assert d.n_unresolved == int(grp["n_unresolved"].iloc[0])
        for _, r in grp.iterrows():
            row = t.loc[r["value"]]
            assert row["n_systems"] == r["n_systems"]
            for col in ("share_unweighted", "share_weighted", "se_weighted"):
                assert math.isclose(row[col], r[col], abs_tol=1e-9), (key, r["value"], col)
            checked += 1
    assert checked == len(ref) > 100


def test_not_reported_by_layer_matches_paper_one_screen_summary(db):
    """Layer rates and SEs equal the manuscript's (data/analysis/summary_one_screen.csv, written
    by scripts/analyse_descriptives.py with system-clustered SEs) to 1e-9."""
    ref = pd.read_csv(REPO / "data" / "analysis" / "summary_one_screen.csv")
    ref = ref[ref["level"] == "layer"].set_index("layer")
    got = db.not_reported(by="layer").set_index("layer")
    assert list(got.index) == list(ref.index)
    assert (got["n_base"] == ref["n_cells_base_excl_unresolved"]).all()
    for mine, theirs in (("rate_unweighted", "share_not_reported_of_base"),
                         ("rate_weighted", "rate_not_reported_weighted"),
                         ("se_weighted", "se_weighted")):
        diff = (got[mine] - ref[theirs]).abs().max()
        assert diff < 1e-9, (mine, diff)
    # rounded to 0.01 points: the clustered SEs, e.g. C 1.17, E 2.34, B 1.98, G 1.78
    for layer, se in {"C": 1.17, "E": 2.34, "B": 1.98, "G": 1.78}.items():
        assert round(100 * got.at[layer, "se_weighted"], 2) == se


def test_layer_se_treats_systems_as_clusters(db):
    """Independent recomputation for one layer: residual totals per system, not per cell."""
    c = db.cells[(db.cells["layer"] == "G") & (db.cells["state"] != "unresolved")]
    s = db.systems.set_index("system_id")
    per = pd.DataFrame({"y": (c["state"] == "not_reported").astype(float).to_numpy(),
                        "system_id": c["system_id"].to_numpy()}).groupby("system_id")["y"].agg(
        ["sum", "count"])
    per = per.join(s[["weight", "stratum"]])
    per = per[per["weight"] > 0]
    r = (per["weight"] * per["sum"]).sum() / (per["weight"] * per["count"]).sum()
    big_n = sum(db.strata_sizes.values())
    x_total = big_n * (per["weight"] * per["count"]).sum() / per["weight"].sum()
    var = 0.0
    for h, n_h_frame in db.strata_sizes.items():
        g = per[per["stratum"] == h]
        e = g["sum"] - r * g["count"]
        var += n_h_frame ** 2 * max(0.0, 1 - len(g) / n_h_frame) * e.var(ddof=1) / len(g)
    got = db.not_reported(by="layer").set_index("layer").loc["G"]
    assert math.isclose(got["rate_weighted"], r, abs_tol=1e-12)
    assert math.isclose(got["se_weighted"], math.sqrt(var) / x_total, abs_tol=1e-12)


def test_not_reported_by_layer_and_stratum(db):
    lay = db.not_reported()  # default by="layer"
    assert list(lay["layer"]) == list(db.schema.layers)
    assert lay["n_cells"].sum() == N_CELLS and lay["n_not_reported"].sum() == N_NR
    assert lay["rate_weighted"].between(0, 1).all() and (lay["se_weighted"] > 0).all()
    per_dim = db.not_reported(by="dimension")
    a = per_dim[per_dim["layer"] == "E"]
    e = lay.set_index("layer").loc["E"]
    assert e["n_not_reported"] == a["n_not_reported"].sum()
    strat = db.not_reported(by="stratum")
    assert list(strat["stratum"]) == ["H", "P", "O"]
    h = strat.set_index("stratum").loc["H"]
    assert math.isclose(h["rate_weighted"], h["rate_unweighted"])  # weight 1 throughout
    assert h["se_weighted"] < 0.001  # 983 of 984 frame systems coded: fpc ~ 0
    assert (strat.set_index("stratum").loc[["P", "O"], "se_weighted"] > 0.005).all()
    with pytest.raises(ValueError):
        db.not_reported(by="year")


def test_ratio_estimate_reduces_to_stratified_proportion():
    y = np.array([1, 0, 1, 1, 0, 0, 1, 0], float)
    x = np.ones_like(y)
    st = np.array(["A"] * 4 + ["B"] * 4, object)
    w = np.array([2.0] * 4 + [5.0] * 4)
    sizes = {"A": 8.0, "B": 20.0}
    rate, se, base, n = ratio_estimate(y, x, w, st, sizes)
    assert n == 8 and base == 28.0
    assert math.isclose(rate, (2 * 3 + 5 * 1) / 28)
    var = sum((nh / 28) ** 2 * (1 - 4 / nh) * p * (1 - p) / 3
              for nh, p in ((8.0, 0.75), (20.0, 0.25)))
    assert math.isclose(se, math.sqrt(var))
    assert math.isnan(ratio_estimate(y, x, np.zeros(8), st, sizes)[0])


# ------------------------------------------------------------------ multi-valued handling


def test_multi_valued_are_lists_in_cells(db, schema_raw):
    c = db.cells[db.cells["state"] == "coded"]
    multi = {d["key"] for d in schema_raw["dimensions"] if d["multi"]}
    is_list = c["value"].map(lambda v: isinstance(v, list))
    assert is_list.eq(c["dimension_key"].isin(multi)).all()
    assert c.loc[is_list, "value"].map(len).min() >= 1
    ints = c[c["dimension_key"].isin(["tool_count", "stars"])]["value"]
    assert ints.map(lambda v: isinstance(v, int)).all()


def test_wide_join_and_list(db):
    w = db.wide()
    assert len(w) == N_SYSTEMS and w["system_id"].is_unique
    keys = db.schema.keys_in_order
    assert list(w.columns[:4]) == ["system_id", "name", "stratum", "weight"]
    assert list(w.columns[4:42]) == keys and list(w.columns[42:]) == [f"{k}__state" for k in keys]
    row = w.set_index("system_id").loc["1code"]
    assert row["loop_primitives"] == "event_driven|plan_execute|react"
    assert row["protocol_standardization"] == "mcp|other"
    assert w["tool_count"].dtype == "Int64" and w["stars"].dtype == "Int64"
    assert (w[[f"{k}__state" for k in keys]].stack().value_counts().to_dict()
            == {"coded": N_CODED, "not_reported": N_NR, "unresolved": N_UNRES})
    wl = db.wide(multi="list").set_index("system_id")
    assert wl.at["1code", "loop_primitives"] == ["event_driven", "plan_execute", "react"]
    assert db.wide(sep=";").set_index("system_id").at["1code", "protocol_standardization"] \
        == "mcp;other"
    with pytest.raises(ValueError):
        db.wide(multi="explode")


def test_dimension_multi_valued_shares(db):
    d = db.dimension("self_verification")
    assert d.multi and d.dimension_id == "E1" and d.layer == "E"
    assert list(d.table["value"]) == db.schema.values("self_verification")
    assert d.table["share_unweighted"].sum() > 1  # a system counts once per value it uses
    n_test = int(db.cells[(db.cells["dimension_key"] == "self_verification")]["value"]
                 .map(lambda v: isinstance(v, list) and "test_execution" in v).sum())
    assert d.table.set_index("value").at["test_execution", "n_systems"] == n_test
    assert "E1 self_verification" in str(d)
    # non-enum dimensions: observed values, most frequent first
    tc = db.dimension("tool_count").table
    assert tc["n_systems"].is_monotonic_decreasing and len(tc) > 5
    assert db.dimension("E1").dimension_key == "self_verification"


# -------------------------------------------------------------------------------- evidence


def test_evidence_cell_and_system(db):
    ev = db.evidence("1code", "protocol_standardization")
    assert isinstance(ev, hdb.Evidence)
    assert ev.value == ["mcp", "other"] and ev.state == "coded"
    assert ev.quote.startswith("MCP Server Management") and ev.locator == "README.md@9f1bc76"
    assert "README.md@9f1bc76" in str(ev)
    allc = db.evidence("1code")
    assert len(allc) == 38 and list(allc["dimension_key"]) == db.schema.keys_in_order
    assert db.evidence("1Code", "B5").system_id == "1code"  # by name, dimension by id
    with pytest.raises(KeyError, match="openhands"):
        db.evidence("openhand", "self_verification")
    with pytest.raises(KeyError):
        db.evidence("1code", "no_such_dimension")


def test_split_evidence():
    f = hdb.split_evidence
    assert f('"max_turns=2" (README.md@e9bc1c2)') == ("max_turns=2", "README.md@e9bc1c2")
    assert f('"| `x` | tool |" (README.md (Tools)@e23c462)') == (
        "| `x` | tool |", "README.md (Tools)@e23c462")
    assert f('"Code for "X" (ICLR 2025)." (README.md)') == ('Code for "X" (ICLR 2025).',
                                                            "README.md")
    assert f("README.md@585fe7c") == (None, "README.md@585fe7c")
    assert f('"a quote with no locator"') == ("a quote with no locator", None)
    assert f(None) == (None, None) and f("  ") == (None, None)


def test_every_evidence_splits(db):
    c = db.cells[db.cells["evidence"].notna()]
    assert len(c) == 24308  # 24,228 coded + 80 not_reported cells that quote the silence
    assert c["locator"].notna().all()
    assert c["quote"].isna().sum() == 58  # bare locators, no quote
    coded = db.cells[db.cells["state"] == "coded"]
    assert coded["evidence"].notna().all()


def test_legacy_value_state_is_read_as_coded(tmp_path, db):
    """Early release builds spelled the coded state ``value``; the loader reports ``coded``."""
    sub_ids = [s["id"] for s in _subset(3)]
    cells = db.cells[db.cells["system_id"].isin(sub_ids)].copy()
    cells["value"] = cells["value"].map(
        lambda v: "" if v is None else ("|".join(v) if isinstance(v, list) else str(v)))
    cells["state"] = cells["state"].astype(str).replace({"coded": "value"})
    cells.to_csv(tmp_path / "cells.csv", index=False)
    db.systems[db.systems["system_id"].isin(sub_ids)].to_csv(tmp_path / "systems_wide.csv",
                                                             index=False)
    shutil.copy(REPO / "schema" / "dimensions.json", tmp_path / "dimensions.json")
    (tmp_path / "datapackage.json").write_text(json.dumps({"resources": []}), encoding="utf-8")
    rel = hdb.load(tmp_path)
    assert set(rel.cells["state"].astype(str)) <= set(hdb.STATES)
    assert (rel.cells["state"] == "coded").sum() == (
        db.cells[db.cells["system_id"].isin(sub_ids)]["state"] == "coded").sum()


def test_cell_state_rules():
    cs = hdb.cell_state
    assert cs({"value": "x", "not_reported": False}) == "coded"
    assert cs({"value": None, "not_reported": True}) == "not_reported"
    assert cs({"value": None, "not_reported": True, "unresolved": True}) == "unresolved"
    assert cs({"value": None, "not_reported": False}) == "unresolved"
    assert cs({"value": [], "not_reported": False}) == "unresolved"
    assert cs({}) == "unresolved"


# ---------------------------------------------------------------------- Hugging Face export


def test_arrow_frames_are_arrow_safe(db):
    frames = db._arrow_frames()
    cells = frames["cells"]
    assert set(frames) == {"systems", "cells"} and len(cells) == N_CELLS
    silent = cells["state"] != "coded"
    assert cells.loc[silent, "value"].isna().all()
    vals = cells.loc[~silent, "value"]
    assert vals.map(lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v)).all()


def test_to_hf(db):
    pytest.importorskip("datasets")
    dd = db.to_hf()
    assert set(dd) == {"systems", "cells"}
    assert dd["systems"].num_rows == N_SYSTEMS and dd["cells"].num_rows == N_CELLS
    states = dd["cells"]["state"]
    states = list(states) if not isinstance(states, list) else states
    assert states.count("not_reported") == N_NR and states.count("unresolved") == N_UNRES
    row = dd["cells"].filter(lambda r: r["system_id"] == "1code"
                             and r["dimension_key"] == "loop_primitives")[0]
    assert row["value"] == ["event_driven", "plan_execute", "react"]
    silent = dd["cells"].filter(lambda r: r["state"] == "not_reported").select(range(50))
    assert all(v is None for v in silent["value"])
    assert dd["systems"].features["weight"].dtype == "float64"


def test_to_hf_without_datasets_explains(db, monkeypatch):
    monkeypatch.setitem(sys.modules, "datasets", None)
    with pytest.raises(ImportError, match=r"harness-db\[hf\]"):
        db.to_hf()


# --------------------------------------------------------------------- packaged releases


def _subset(n: int = 40) -> list[dict]:
    systems = json.loads((REPO / "data" / "systems.json").read_text(encoding="utf-8"))
    keep = systems[:n] + [s for s in systems if s["id"] in ("car", "storm")]
    return keep


def test_release_nested_json_via_datapackage(tmp_path):
    sub = _subset()
    (tmp_path / "harness_db_systems.json").write_text(json.dumps(sub), encoding="utf-8")
    shutil.copy(REPO / "schema" / "dimensions.json", tmp_path / "coding_sheet.json")
    shutil.copy(REPO / "schema" / "harness_db.schema.json", tmp_path / "harness_db.schema.json")
    frame = pd.read_csv(REPO / "data" / "coding_frame.csv", dtype=str, keep_default_na=False)
    frame[frame["system_id"].isin({s["id"] for s in sub})].to_csv(tmp_path / "frame.csv",
                                                                  index=False)
    shutil.copy(REPO / "data" / "results.csv", tmp_path / "results.csv")
    dp = {"name": "harness-db", "version": "1.0.0",
          "sampling": {"strata": {"H": {"size": 984}, "P": {"size": 683}, "O": {"size": 4837}}},
          "resources": [
              {"name": "systems", "path": "harness_db_systems.json"},
              {"name": "json-schema", "path": "harness_db.schema.json"},
              {"name": "dimensions", "path": "coding_sheet.json"},
              {"name": "coding_frame", "path": "frame.csv"},
              {"name": "results", "path": "results.csv"},
          ]}
    (tmp_path / "datapackage.json").write_text(json.dumps(dp), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rel = hdb.load(tmp_path / "datapackage.json")
    assert rel.source.kind == "release" and rel.source.meta["version"] == "1.0.0"
    assert len(rel.systems) == len(sub) and len(rel.cells) == 38 * len(sub)
    assert rel.strata_sizes == {"H": 984.0, "P": 683.0, "O": 4837.0}
    assert not rel.systems.set_index("system_id").loc[["car", "storm"], "weight_bearing"].any()
    assert len(rel.papers) == 0 and len(rel.results) == 5863
    assert hdb.load(tmp_path).source.kind == "release"  # the directory works too


@pytest.mark.parametrize("style", ["plain", "release"])
def test_release_tabular_roundtrip(tmp_path, db, style):
    """A tabular-only release (no systems.json) rebuilds the same cells.

    ``release`` mimics scripts/release_dataset.py: ``systems_wide.csv`` with ``paper_ids`` and
    ``version``, ``cells.csv`` with ``evidence_quote``/``evidence_locator``, and no stratum sizes
    anywhere (the design's are used, silently).
    """
    sub_ids = [s["id"] for s in _subset()]
    systems = db.systems[db.systems["system_id"].isin(sub_ids)].copy()
    cells = db.cells[db.cells["system_id"].isin(sub_ids)].copy()
    cells["value"] = cells["value"].map(
        lambda v: "" if v is None else ("|".join(v) if isinstance(v, list) else str(v)))
    cells["state"] = cells["state"].astype(str)
    shutil.copy(REPO / "schema" / "dimensions.json", tmp_path / "dimensions.json")
    if style == "plain":
        for col in ("papers", "aliases"):
            systems[col] = systems[col].map(json.dumps)
        systems.to_csv(tmp_path / "systems.csv", index=False)
        cells.to_csv(tmp_path / "cells.csv", index=False)
        dp = {"name": "harness-db", "strata": {"H": 984, "P": 683, "O": 4837},
              "resources": [{"name": "systems", "path": "systems.csv"},
                            {"name": "cells", "path": "cells.csv"}]}
    else:
        systems = systems.rename(columns={"papers": "paper_ids", "version_label": "version"})
        systems["paper_ids"] = systems["paper_ids"].map(";".join)
        systems.drop(columns=["aliases"]).to_csv(tmp_path / "systems_wide.csv", index=False)
        cells = cells.rename(columns={"quote": "evidence_quote", "locator": "evidence_locator"})
        cells.drop(columns=["evidence"]).to_csv(tmp_path / "cells.csv", index=False)
        dp = {"name": "harness-db",
              "resources": [{"name": "systems-wide", "path": "systems_wide.csv"},
                            {"name": "cells", "path": "cells.csv"}]}
    (tmp_path / "datapackage.json").write_text(json.dumps(dp), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rel = hdb.load(tmp_path)
    assert rel.strata_sizes == {"H": 984.0, "P": 683.0, "O": 4837.0}
    got = rel.cells.set_index(["system_id", "dimension_key"])
    want = db.cells[db.cells["system_id"].isin(sub_ids)].set_index(
        ["system_id", "dimension_key"])
    assert len(got) == len(want)
    for col in ("state", "quote", "locator", "confidence"):
        assert got[col].astype(object).fillna("<na>").equals(
            want.loc[got.index, col].astype(object).fillna("<na>")), col
    assert got["value"].tolist() == want.loc[got.index, "value"].tolist()
    r = rel.systems.set_index("system_id")
    assert r.at["car", "weight"] == 0 and r.at["1code", "weight"] == 1.0
    assert r.at["1code", "papers"] == ["awesome:picrew:733956ebc630"]
    assert r.at["1code", "version_label"] == "v0.0.84"


def test_release_without_weights_warns_and_uses_design_strata(tmp_path):
    (tmp_path / "systems.json").write_text(json.dumps(_subset(5)), encoding="utf-8")
    shutil.copy(REPO / "schema" / "dimensions.json", tmp_path / "dimensions.json")
    (tmp_path / "datapackage.json").write_text(json.dumps({"resources": []}), encoding="utf-8")
    with pytest.warns(UserWarning, match="no stratum/weight"):
        rel = hdb.load(tmp_path)
    assert rel.strata_sizes == hdb.core.DESIGN_STRATA
    assert not rel.systems["weight_bearing"].any()
    assert math.isnan(rel.not_reported(by=None).iloc[0]["rate_weighted"])


def test_built_release_loads_like_the_repo(db):
    """The release built by scripts/release_dataset.py, when one is on disk, loads identically."""
    built = sorted(REPO.glob("release/harness-db-*/datapackage.json"))
    if not built:
        pytest.skip("no built release under release/")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rel = hdb.load(built[-1])
    assert rel.source.kind == "release"
    cols = [c for c in db.cells.columns if c != "validation_flags"]
    assert rel.cells[cols].astype(str).equals(db.cells[cols].astype(str))
    assert rel.systems.astype(str).equals(db.systems.astype(str))  # stratum and weight too
    assert rel.strata_sizes == db.strata_sizes
    flagged = rel.cells[rel.cells["validation_flags"].notna()]
    assert set(flagged["state"].astype(str)) <= {"unresolved"}
    assert rel.summary()["cells"] == N_CELLS
