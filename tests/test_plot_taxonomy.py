"""Tests for scripts/plot_taxonomy.py (the section 5 taxonomy map).

The figure carries no data, so the only way it can be wrong is by drifting from
``schema/dimensions.json``. These tests therefore run against the REAL schema, not a fixture, and
assert the two things a reader of the figure would otherwise have to take on trust:

1. every string and every count in the figure is one the schema supplies (ids, keys, layer names,
   ``len(values)``, ``multi``, ``type``), and none is hard-coded in the plotting script; and
2. the frozen v1 shape of the taxonomy is what got drawn - 38 dimensions, 9 layers, the stated
   per-layer counts, 15 multi-valued dimensions and 4 non-enumerated ones.

The per-layer counts are written out by hand below so that a schema edit fails HERE, loudly, next
to a number a human chose, rather than quietly producing a different-looking figure.

Nothing renders to a screen: matplotlib is forced onto the Agg backend before the module is
imported, and the one rendering test writes to ``tmp_path``.
"""

import copy
import json
import sys
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plot_taxonomy as pt

SCHEMA_PATH = ROOT / "schema/dimensions.json"

# The frozen v1 shape, by hand.
N_DIMENSIONS = 38
N_LAYERS = 9
PER_LAYER = {"A": 4, "B": 5, "C": 5, "D": 3, "E": 3, "F": 3, "G": 4, "H": 4, "M": 7}
N_MULTI = 15
NON_ENUM = {"B2": "integer", "M5": "date", "M6": "string", "M7": "integer"}


@pytest.fixture(scope="module")
def schema():
    return pt.load(SCHEMA_PATH)


@pytest.fixture(scope="module")
def lay(schema):
    return pt.layout(schema)


# ------------------------------------------------------------------ the schema is what we assume

def test_schema_has_the_frozen_v1_shape(schema):
    assert len(schema["dimensions"]) == N_DIMENSIONS
    assert len(schema["layers"]) == N_LAYERS
    counts = {ly["id"]: 0 for ly in schema["layers"]}
    for d in schema["dimensions"]:
        counts[d["layer"]] += 1
    assert counts == PER_LAYER
    assert sum(PER_LAYER.values()) == N_DIMENSIONS


# ----------------------------------------------------------------------------- what layout() emits

def test_layout_emits_every_dimension_once_across_nine_layers(lay, schema):
    entries = lay.entries
    assert len(entries) == N_DIMENSIONS
    assert len(lay.blocks) == N_LAYERS
    assert len({b.layer for b in lay.blocks}) == N_LAYERS
    assert [e.dim_id for e in entries] == [d["id"] for d in schema["dimensions"]], \
        "entries must be emitted in schema order"


def test_per_layer_entry_counts_equal_the_schema(lay):
    drawn = {b.layer: len(b.entries) for b in lay.blocks}
    assert drawn == PER_LAYER
    for b in lay.blocks:
        assert all(e.layer == b.layer for e in b.entries)


def test_layer_row_order_matches_schema_layer_order(schema):
    """The explicit row assignment is the only ordering the script adds; it must not reorder."""
    flat = pt.ROW1_LAYERS + pt.ROW2_LAYERS + pt.BAND_LAYERS
    assert list(flat) == [ly["id"] for ly in schema["layers"]]
    assert len(set(flat)) == len(flat)
    assert pt.ROW1_LAYERS == ("A", "B", "C")
    assert pt.BAND_LAYERS == ("M",), "M is a detached band, not a clause layer"


def test_every_label_is_a_string_the_schema_supplies(lay, schema):
    ids = {d["id"] for d in schema["dimensions"]}
    keys = {d["key"] for d in schema["dimensions"]}
    names = {ly["name"] for ly in schema["layers"]}
    types = {d["type"] for d in schema["dimensions"]}
    for e in lay.entries:
        assert e.dim_id in ids
        assert e.key in keys
        assert e.label == f"{e.dim_id} {e.key}"
        assert e.value_field.strip("{}") in {str(n) for n in range(1, 100)} | types
    for b in lay.blocks:
        assert b.name in names
        assert b.title.startswith(f"{b.layer}  {b.name}")
        assert "".join(b.title_lines).replace(" ", "") == b.title.replace(" ", "")


def test_value_counts_are_the_schema_value_counts(lay, schema):
    by_id = {d["id"]: d for d in schema["dimensions"]}
    for e in lay.entries:
        d = by_id[e.dim_id]
        if d["type"] == "enum":
            assert e.n_values == len(d["values"])
            assert e.value_field.strip("{}") == str(len(d["values"]))
        else:
            assert e.n_values is None


# ------------------------------------------------------------------------------ the two flag marks

def test_multi_valued_dimensions_are_flagged_and_there_are_fifteen(lay, schema):
    multi = [e for e in lay.entries if e.multi]
    assert len(multi) == N_MULTI
    assert {e.dim_id for e in multi} == {d["id"] for d in schema["dimensions"] if d["multi"]}
    for e in lay.entries:
        # The set braces are the mark, so it survives a greyscale print; the grey row band behind
        # a multi-valued row is redundant with it, never the only signal.
        assert e.value_field.startswith("{") == e.multi
        assert e.value_field.endswith("}") == e.multi


def test_non_enum_dimensions_are_marked_by_type_not_by_a_value_count(lay):
    non_enum = {e.dim_id: e for e in lay.entries if e.n_values is None}
    assert set(non_enum) == set(NON_ENUM)
    for dim_id, type_name in NON_ENUM.items():
        e = non_enum[dim_id]
        assert e.type == type_name
        assert e.value_field == type_name, "a type name, not a count"
        assert not e.value_field.strip("{}").isdigit()
    assert all(e.n_values is not None for e in lay.entries if e.dim_id not in NON_ENUM)


# ----------------------------------------------------------------------------------------- arrows

def test_the_step_loop_is_a_to_b_to_c_and_back(lay):
    loop = [(a.src, a.dst) for a in lay.arrows if a.kind == "loop"]
    assert loop == [("A", "B"), ("B", "C"), ("C", "A")]


def test_both_displacement_arrows_are_supported_by_the_schema(schema, lay):
    """F1 and G4 are drawn pointing at the layer whose definition clause they code.

    docs/definition.md section 4 names exactly two exceptions to the clause-to-layer map, both in
    clause (vi)'s neighbourhood: F1 (termination) codes clause (iii), whose layer is C, and G4
    (permission model) codes clause (vi), whose layer is F. An arrow is only legitimate if the
    schema still puts the dimension somewhere else.
    """
    assert pt.check_displacements(schema) == []
    by_id = {d["id"]: d for d in schema["dimensions"]}
    drawn = {(a.src, a.dst) for a in lay.arrows if a.kind == "displacement"}
    assert drawn == {("F1", "C"), ("G4", "F")}
    for src, dst in drawn:
        assert by_id[src]["layer"] != dst, f"{src} is not displaced relative to {dst}"
        assert dst in {ly["id"] for ly in schema["layers"]}
    assert by_id["F1"]["layer"] == "F"
    assert by_id["G4"]["layer"] == "G"


def test_no_g4_to_c5_arrow_is_drawn(lay, schema):
    """Section 5's TODO asked for G4 -> C5; the schema does not support it, so it is not drawn.

    C5 (human_in_loop) co-codes clause (vi) with G4 and F1-F3, but C5 is NOT displaced: it sits in
    C, which is its own clause's layer. Drawing G4 -> C5 would assert a third displacement that
    docs/definition.md section 4 does not contain.
    """
    targets = {(a.src, a.dst) for a in lay.arrows}
    assert ("G4", "C5") not in targets
    assert all(a.dst in {ly["id"] for ly in schema["layers"]} for a in lay.arrows), \
        "arrows point at layers, not at dimensions"
    assert {d["id"] for d in schema["dimensions"] if d["key"] == "human_in_loop"} == {"C5"}


def test_a_displacement_that_is_not_a_displacement_is_refused(schema, tmp_path, capsys):
    """If a future schema moved G4 into F, the arrow would be a lie; the script must refuse."""
    mutated = copy.deepcopy(schema)
    for d in mutated["dimensions"]:
        if d["id"] == "G4":
            d["layer"] = "F"
    problems = pt.check_displacements(mutated)
    assert len(problems) == 1
    assert "G4" in problems[0]

    path = tmp_path / "mutated.json"
    path.write_text(json.dumps(mutated), encoding="utf-8")
    assert pt.main(["--dimensions", str(path), "--no-render"]) == 1
    assert "PROBLEM" in capsys.readouterr().out


# ------------------------------------------------------------------------------- geometry and I/O

def test_every_row_fits_inside_its_block(lay):
    """Guards the one failure mode of a hand-laid-out figure: text spilling out of its box."""
    for b in lay.blocks:
        assert b.w > 0 and b.h > 0
        for e in b.entries:
            assert b.x <= e.row_x0, f"{e.dim_id} starts left of block {b.layer}"
            assert e.x_value <= b.right - pt.PAD_X * 0.5, f"{e.dim_id} overflows block {b.layer}"
            assert b.y < e.y < b.top - b.title_h
        label_w = max(pt.text_width(e.label, pt.ROW_FS) for e in b.entries)
        assert label_w > 0
    for a, c in zip(pt.ROW2_LAYERS, pt.ROW2_LAYERS[1:]):
        left = next(b for b in lay.blocks if b.layer == a)
        right = next(b for b in lay.blocks if b.layer == c)
        assert left.right < right.x, f"blocks {a} and {c} overlap"


def test_render_writes_non_empty_svg_and_pdf(lay, tmp_path):
    paths = pt.render(lay, tmp_path / "taxonomy_map")
    assert [p.name for p in paths] == ["taxonomy_map.svg", "taxonomy_map.pdf"]
    for p in paths:
        assert p.exists() and p.stat().st_size > 5_000
    svg = paths[0].read_text(encoding="utf-8")
    assert svg.lstrip().startswith("<?xml")


def test_main_renders_to_the_requested_stem(tmp_path):
    stem = tmp_path / "figures" / "taxonomy_map"
    assert pt.main(["--out", str(stem)]) == 0
    assert stem.with_suffix(".svg").stat().st_size > 5_000
    assert stem.with_suffix(".pdf").stat().st_size > 5_000
