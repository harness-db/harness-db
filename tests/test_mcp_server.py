"""Tests for the HARNESS-DB MCP server (mcp_server/harnessdb_mcp), on the real release.

Every tool function is called directly; the expected numbers are recounted here from
data/systems.json and checked against the release's analysis tables, so a tool that drifts from the
release fails loudly.
"""

import asyncio
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp_server"))

from harnessdb_mcp import tools as T
from harnessdb_mcp.card import dataset_card
from harnessdb_mcp.db import (
    THREE_STATE_RULE,
    HarnessDB,
    cell_state,
    parse_manual,
    split_evidence,
)

SYSTEMS = json.loads((ROOT / "data" / "systems.json").read_text(encoding="utf-8"))
DIMS = json.loads((ROOT / "schema" / "dimensions.json").read_text(encoding="utf-8"))
ANALYSIS = ROOT / "data" / "analysis"


@pytest.fixture(scope="module", autouse=True)
def db():
    loaded = HarnessDB.load(ROOT)
    T.set_db(loaded)
    yield loaded
    T.set_db(None)


def recount(key):
    return Counter(cell_state(s["coding"].get(key)) for s in SYSTEMS)


def read_csv(name):
    with (ANALYSIS / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- release counts


def test_release_totals_match_systems_json(db):
    assert len(db.systems) == len(SYSTEMS)
    overall = T.under_reporting("dimension")["overall"]
    states = Counter(cell_state(c) for s in SYSTEMS for c in s["coding"].values())
    assert overall["n_cells"] == len(SYSTEMS) * len(DIMS["dimensions"])
    assert overall["n_coded"] == states["coded"]
    assert overall["n_not_reported"] == states["not_reported"]
    assert overall["n_unresolved"] == states["unresolved"]


def test_under_reporting_by_dimension_equals_release_table():
    rows = {r["dimension"]: r for r in T.under_reporting("dimension")["rows"]}
    release = read_csv("under_reporting_by_dimension.csv")
    assert set(rows) == {r["key"] for r in release}
    for ref in release:
        got = rows[ref["key"]]
        for col in ("n_cells", "n_unresolved", "n_coded", "n_not_reported"):
            assert got[col] == int(ref[col]), (ref["key"], col)
        for col in ("rate_unweighted", "rate_weighted", "se_weighted"):
            assert got[col] == pytest.approx(float(ref[col]), abs=1e-4), (ref["key"], col)


def test_under_reporting_by_layer_pools_every_cell(db):
    out = T.under_reporting("layer")
    assert {r["layer"] for r in out["rows"]} == {lay["id"] for lay in DIMS["layers"]}
    assert sum(r["n_cells"] for r in out["rows"]) == len(SYSTEMS) * len(DIMS["dimensions"])
    g = next(r for r in out["rows"] if r["layer"] == "G")
    expected_nr = sum(recount(d["key"])["not_reported"] for d in DIMS["dimensions"]
                      if d["layer"] == "G")
    assert g["n_not_reported"] == expected_nr
    assert out["note"] == THREE_STATE_RULE
    assert "error" in T.under_reporting("system")


@pytest.mark.parametrize("weighted", [False, True])
def test_dimension_distribution_equals_release_table(weighted):
    release = read_csv("value_distributions.csv")
    for spec in DIMS["dimensions"]:
        out = T.dimension_distribution(spec["key"], weighted=weighted)
        got = {r["value"]: r for r in out["values"]}
        refs = [r for r in release if r["key"] == spec["key"]]
        assert set(got) == {r["value"] for r in refs}, spec["key"]
        for ref in refs:
            row = got[ref["value"]]
            if weighted:
                assert row["share"] == pytest.approx(float(ref["share_weighted"]), abs=1e-4)
                assert row["se"] == pytest.approx(float(ref["se_weighted"]), abs=1e-4)
            else:
                assert row["n_systems"] == int(ref["n_systems"])
                assert row["share"] == pytest.approx(float(ref["share_unweighted"]), abs=1e-4)
                assert out["n_not_reported"] == int(ref["n_not_reported"])
                assert out["n_unresolved"] == int(ref["n_unresolved"])


def test_weighted_distribution_uses_only_weight_bearing_systems(db):
    bearing = [s for s in SYSTEMS if db.weight(s["id"]) > 0]
    assert 0 < len(bearing) < len(SYSTEMS)  # the out-of-draw systems carry weight 0
    out = T.dimension_distribution("network_policy", weighted=True)
    assert out["n_systems"] == len(bearing)
    states = Counter(cell_state(s["coding"]["network_policy"]) for s in bearing)
    assert (out["n_coded"], out["n_not_reported"], out["n_unresolved"]) == (
        states["coded"], states["not_reported"], states["unresolved"])
    assert out["weight_total"] == pytest.approx(sum(db.weight(s["id"]) for s in bearing), abs=1e-2)
    unweighted = T.dimension_distribution("network_policy")
    assert unweighted["n_systems"] == len(SYSTEMS)
    assert unweighted["n_not_reported"] == recount("network_policy")["not_reported"]
    assert "error" in T.dimension_distribution("no_such_dimension")


# --------------------------------------------------------------------------- search


def test_search_not_reported_filter_returns_exactly_the_silent_systems():
    out = T.search_systems(dimension="network_policy", state="not_reported", limit=200)
    assert out["total_matches"] == recount("network_policy")["not_reported"]
    assert out["returned"] == 200 and out["truncated"]
    for row in out["results"]:
        (cell,) = row["cells"]
        assert cell["state"] == "not_reported" and cell["value"] is None
    assert out["note"] == THREE_STATE_RULE
    assert list(out).count("note") == 1
    # the id alias "G3" addresses the same dimension
    assert T.search_systems(dimension="G3", state="not_reported")["total_matches"] == \
        out["total_matches"]


def test_search_value_filter_and_errors():
    expected = sum(1 for s in SYSTEMS if cell_state(s["coding"]["network_policy"]) == "coded"
                   and s["coding"]["network_policy"]["value"] == "none")
    out = T.search_systems(dimension="network_policy", value="none", limit=5)
    assert out["total_matches"] == expected
    assert all(r["cells"][0]["value"] == "none" for r in out["results"])
    bad = T.search_systems(dimension="network_policy", value="absent")
    assert "error" in bad and "none" in bad["permitted_values"]
    assert "error" in T.search_systems(state="not_reported")  # no dimension to test
    assert "error" in T.search_systems(dimension="network_policy", value="none",
                                       state="not_reported")
    assert "error" in T.search_systems(layer="G", dimension="tracing")
    assert "error" in T.search_systems(limit=0)


def test_search_multi_valued_integer_and_layer_filters():
    mcp_hits = T.search_systems(dimension="protocol_standardization", value="mcp", limit=1)
    assert mcp_hits["total_matches"] == sum(
        1 for s in SYSTEMS if cell_state(s["coding"]["protocol_standardization"]) == "coded"
        and "mcp" in s["coding"]["protocol_standardization"]["value"])
    big = T.search_systems(dimension="stars", value=">=10000", limit=200)
    assert big["total_matches"] > 0
    assert all(r["cells"][0]["value"] >= 10000 for r in big["results"])
    layer_ids = [d["key"] for d in DIMS["dimensions"] if d["layer"] == "G"]
    all_silent = T.search_systems(layer="G", state="not_reported", layer_match="all", limit=200)
    assert all_silent["total_matches"] == sum(
        1 for s in SYSTEMS if all(cell_state(s["coding"][k]) == "not_reported" for k in layer_ids))
    any_silent = T.search_systems(layer="G", state="not_reported")
    assert any_silent["total_matches"] >= all_silent["total_matches"]


def test_search_text_query_ranks_exact_match_first():
    target = SYSTEMS[0]
    out = T.search_systems(query=target["name"].upper(), limit=5)
    assert out["results"][0]["id"] == target["id"]
    assert T.search_systems(query="zz-no-such-harness-zz")["total_matches"] == 0


# --------------------------------------------------------------------------- one system


def test_get_system_returns_all_cells_with_evidence():
    sid = SYSTEMS[0]["id"]
    out = T.get_system(sid)
    assert len(out["cells"]) == len(DIMS["dimensions"])
    assert [c["dimension"] for c in out["cells"]] == [d["key"] for d in DIMS["dimensions"]]
    counts = Counter(c["state"] for c in out["cells"])
    assert out["state_counts"] == {k: counts.get(k, 0) for k in ("coded", "not_reported",
                                                                 "unresolved")}
    for cell in out["cells"]:
        if cell["state"] == "coded":
            assert cell["value"] is not None and cell["locator"]
        else:
            assert cell["value"] is None
    unknown = T.get_system("definitely-not-a-harness")
    assert "error" in unknown and isinstance(unknown["did_you_mean"], list)


def test_get_evidence_splits_quote_and_locator():
    sid, key, cell = next((s["id"], k, c) for s in SYSTEMS for k, c in s["coding"].items()
                          if cell_state(c) == "coded" and c.get("evidence", "").startswith('"'))
    out = T.get_evidence(sid, key)
    assert out["state"] == "coded" and out["value"] == cell["value"]
    assert out["quote"] and out["locator"]
    assert f'"{out["quote"]}" ({out["locator"]})' == cell["evidence"].strip()
    assert "note" not in out  # a coded cell carries no silence, so no rule is attached
    nr_sid, nr_key = next((s["id"], k) for s in SYSTEMS for k, c in s["coding"].items()
                          if cell_state(c) == "not_reported")
    silent = T.get_evidence(nr_sid, nr_key)
    assert silent["state"] == "not_reported" and silent["value"] is None
    assert silent["note"] == THREE_STATE_RULE
    assert "error" in T.get_evidence(sid, "not_a_dimension")


def test_split_evidence_handles_bare_locators():
    assert split_evidence('"x (y) z" (README.md:3@abc)') == ("x (y) z", "README.md:3@abc")
    assert split_evidence("README.md@585fe7c") == (None, "README.md@585fe7c")
    assert split_evidence(None) == (None, None)


# --------------------------------------------------------------------------- compare


def test_compare_handles_unknown_ids_cleanly():
    a, b = SYSTEMS[0]["id"], SYSTEMS[1]["id"]
    out = T.compare([a, "no-such-system", b, a])
    assert [s["id"] for s in out["systems"]] == [a, b]  # duplicate dropped, order kept
    assert out["unknown_ids"][0]["id"] == "no-such-system"
    assert isinstance(out["unknown_ids"][0]["did_you_mean"], list)
    assert "error" not in out
    assert len(out["rows"]) == len(DIMS["dimensions"])
    for row in out["rows"]:
        assert set(row["cells"]) == {a, b}
        assert row["differs"] == (
            (row["cells"][a]["state"], json.dumps(row["cells"][a]["value"]))
            != (row["cells"][b]["state"], json.dumps(row["cells"][b]["value"])))
    none_known = T.compare(["nope-1", "nope-2"])
    assert none_known["rows"] == [] and "error" in none_known and len(none_known["unknown_ids"]) == 2
    assert "error" in T.compare([])
    assert "error" in T.compare([s["id"] for s in SYSTEMS[:7]])


# --------------------------------------------------------------------------- schema and card


def test_describe_schema_lists_layers_dimensions_and_glosses():
    out = T.describe_schema()
    assert out["n_layers"] == len(DIMS["layers"]) and out["n_dimensions"] == len(DIMS["dimensions"])
    listed = [d for lay in out["layers"] for d in lay["dimensions"]]
    assert [d["key"] for d in listed] == [d["key"] for d in DIMS["dimensions"]]
    for spec, got in zip(DIMS["dimensions"], listed):
        if spec["type"] == "enum":
            assert [v["value"] for v in got["values"]] == spec["values"]
    net = T.describe_schema("G3")
    assert net["dimension"]["key"] == "network_policy"
    assert {v["value"]: v["gloss"] for v in net["dimension"]["values"]}["none"]
    assert net["dimension"]["decision_rule"]
    assert "note" not in out  # no cells, so no rule attached
    assert "error" in T.describe_schema("nope")


def test_manual_parser_covers_every_enum_value():
    manual = parse_manual((ROOT / "docs" / "coding_manual.md").read_text(encoding="utf-8"))
    for spec in DIMS["dimensions"]:
        assert spec["key"] in manual
        if spec["type"] == "enum":
            assert set(manual[spec["key"]]["values"]) == set(spec["values"]), spec["key"]


def test_dataset_card_reports_release_counts(db):
    card = dataset_card(db)
    states = Counter(cell_state(c) for s in SYSTEMS for c in s["coding"].values())
    assert f"{len(SYSTEMS):,} systems" in card
    for n in states.values():
        assert f"{n:,}" in card
    assert "NOT evidence that the feature is absent" in card


# --------------------------------------------------------------------------- MCP wiring


def test_server_registers_tools_and_resources(db):
    pytest.importorskip("mcp")
    from harnessdb_mcp.server import build_server

    server = build_server(db)
    tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == {f.__name__ for f in T.TOOLS}
    search = next(t for t in tools if t.name == "search_systems")
    schema = getattr(search, "input_schema", None) or search.inputSchema
    assert schema["properties"]["state"]["anyOf"][0]["enum"] == ["coded", "not_reported",
                                                                 "unresolved"]
    assert "not_reported" in search.description
    resources = {str(r.uri) for r in asyncio.run(server.list_resources())}
    assert resources == {"harnessdb://schema", "harnessdb://dataset-card"}
    templates = asyncio.run(server.list_resource_templates())
    assert [getattr(t, "uri_template", None) or t.uriTemplate for t in templates] == \
        ["harnessdb://system/{system_id}"]
