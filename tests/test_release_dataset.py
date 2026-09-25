"""Tests for scripts/release_dataset.py: the public HARNESS-DB release.

The release is built twice from the real repository (two timestamps on the same day) into a
temporary directory; every test below reads those two builds. Nothing is written under data/ or
paper/.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_dataset as rd

VERSION = "1.0.0"
TS_A = "2026-09-25T10:00:00Z"
TS_B = "2026-09-25T11:30:00Z"
N_SYSTEMS, N_DIMS = 1256, 38

EXPECTED_FILES = {
    "CHECKSUMS.sha256", "CITATION.cff", "LICENSE-CODE", "LICENSE-DATA", "README.md",
    "VALIDATION.txt", "VERSION", "datapackage.json",
    "data/cells.csv", "data/systems_wide.csv", "data/systems.json", "data/papers.csv",
    "data/results.csv", "data/not_reported_by_dimension.csv", "data/reliability.csv",
    "data/prisma_counts.json",
    "docs/coding_manual.md", "docs/protocol_prisma_p.md", "docs/coding_reliability.md",
    "docs/count_reconciliation.md", "docs/schema_changelog.md",
    "data/examples/README.md", "data/examples/openhands.json", "data/examples/swe-agent-1x.json",
    "schema/dimensions.json", "schema/harness_db.schema.json", "schema/data_dictionary.md",
}
PARQUET_FILES = {"data/systems.parquet", "data/cells.parquet"}

csv.field_size_limit(10 ** 8)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def builds(tmp_path_factory):
    out_a = tmp_path_factory.mktemp("release_a")
    out_b = tmp_path_factory.mktemp("release_b")
    a = rd.build(VERSION, out_a, TS_A, quiet=True)
    b = rd.build(VERSION, out_b, TS_B, quiet=True)
    return a, b


@pytest.fixture(scope="module")
def rel(builds):
    return builds[0]


@pytest.fixture(scope="module")
def source_systems():
    return json.loads((ROOT / "data" / "systems.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dims():
    return json.loads((ROOT / "schema" / "dimensions.json").read_text(encoding="utf-8"))["dimensions"]


@pytest.fixture(scope="module")
def cells(rel):
    return read_csv(rel / "data" / "cells.csv")


@pytest.fixture(scope="module")
def wide(rel):
    return read_csv(rel / "data" / "systems_wide.csv")


# ------------------------------------------------------------------------------- what is shipped


def test_release_tree_is_exactly_the_allow_list(rel):
    files = set(rd.tree_files(rel))
    expected = EXPECTED_FILES | (PARQUET_FILES if rd.pyarrow_available() else set())
    assert files == expected


def test_nothing_on_the_deny_list_is_released(rel):
    files = rd.tree_files(rel)
    assert rd.forbidden_paths(files) == []
    for f in files:
        assert not f.startswith(("data/fulltext/", "data/raw/", "data/coded/", "data/screening/",
                                 "paper/"))
        assert not f.endswith((".log", ".bak", ".sqlite"))
        assert "synergy_cache" not in f and "scratchpad" not in f.lower()
    with zipfile.ZipFile(rel.parent / f"{rel.name}.zip") as zf:
        names = [n.split("/", 1)[1] for n in zf.namelist()]
    assert sorted(names) == files
    assert rd.forbidden_paths(names) == []


@pytest.mark.parametrize("path", [
    "data/fulltext/arxiv_2401.00001.pdf", "data/raw/arxiv.jsonl", "data/raw/candidates.csv",
    "data/coded/json/swe-agent.json", "data/coded/autopilot.log", "data/screening/votes.csv",
    "data/results_extract.log", "data/results.csv.bak", "synergy_cache.sqlite", "x/cache.sqlite",
    "paper/main.tex", "paper/figures/fig1.pdf", "notes/scratchpad/tmp.txt", ".env",
])
def test_deny_list_catches(path):
    assert rd.forbidden_paths([path]) == [path]


@pytest.mark.parametrize("path", sorted(EXPECTED_FILES | PARQUET_FILES))
def test_deny_list_passes_the_allow_list(path):
    assert rd.forbidden_paths([path]) == []


def test_no_local_paths_or_secrets(rel):
    assert rd.leak_problems(rel, ROOT) == []


def test_leak_check_catches_a_local_path(tmp_path):
    (tmp_path / "x.txt").write_text(f"see {ROOT / 'data' / 'raw'}", encoding="utf-8")
    assert rd.leak_problems(tmp_path, ROOT)


# ---------------------------------------------------------------------------------- the numbers


def test_cells_csv_has_one_row_per_system_and_dimension(cells, source_systems):
    assert len(source_systems) == N_SYSTEMS
    assert len(cells) == N_SYSTEMS * N_DIMS == 47_728
    assert len({(r["system_id"], r["dimension_key"]) for r in cells}) == len(cells)


def test_three_state_split_equals_the_release(rel, cells, source_systems):
    expected = Counter()
    for s in source_systems:
        for cell in s["coding"].values():
            if cell.get("unresolved"):
                expected["unresolved"] += 1
            elif cell.get("not_reported"):
                expected["not_reported"] += 1
            else:
                expected["coded"] += 1
    assert Counter(r["state"] for r in cells) == expected
    assert sum(expected.values()) == N_SYSTEMS * N_DIMS
    text = (rel / "VALIDATION.txt").read_text(encoding="utf-8")
    for state, n in expected.items():
        assert re.search(rf"^\s+{state}\s+{n:,}\s", text, re.MULTILINE), state
    assert re.search(rf"^systems\s+{N_SYSTEMS:,}$", text, re.MULTILINE)
    assert "0 errors" in text


def test_long_form_reproduces_systems_json(cells, source_systems):
    by = {(r["system_id"], r["dimension_key"]): r for r in cells}
    for s in source_systems:
        for key, cell in s["coding"].items():
            row = by[(s["id"], key)]
            if row["state"] == "coded":
                v = cell["value"]
                assert row["value"] == ("|".join(map(str, v)) if isinstance(v, list) else str(v))
            else:
                assert row["value"] == ""
            q, loc = row["evidence_quote"], row["evidence_locator"]
            rebuilt = f'"{q}" ({loc})' if q and loc else (q or loc)
            assert rebuilt == (cell.get("evidence") or "").strip()
            assert row["note"] == (cell.get("note") or "")
            if row["state"] == "coded":
                assert row["confidence"] == cell["confidence"]
            else:
                assert row["confidence"] == ""  # the source's "low" is a build placeholder


def test_wide_and_long_forms_agree_on_every_value(cells, wide, dims):
    assert len(wide) == N_SYSTEMS
    by_sys = {r["system_id"]: r for r in wide}
    n = 0
    for c in cells:
        w = by_sys[c["system_id"]]
        assert w[c["dimension_key"]] == c["value"], (c["system_id"], c["dimension_key"])
        assert w[c["dimension_key"] + "_state"] == c["state"]
        n += 1
    assert n == N_SYSTEMS * len(dims)
    assert all(d["key"] in wide[0] and f"{d['key']}_state" in wide[0] for d in dims)


def test_wide_metadata_columns(wide, source_systems):
    src = {s["id"]: s for s in source_systems}
    for r in wide:
        s = src[r["system_id"]]
        assert r["name"] == s["name"]
        assert r["primary_paper_id"] == s["papers"][0]
        assert r["repo_url"] == (s.get("urls") or {}).get("repo", "")
        assert r["stratum"] in {"H", "P", "O"}
        assert float(r["weight"]) >= 0
    zero = [r for r in wide if float(r["weight"]) == 0]
    assert all(r["stratum"] in {"P", "O"} for r in zero)


def test_not_reported_table_matches_the_published_analysis(rel):
    released = {r["key"]: r for r in read_csv(rel / "data" / "not_reported_by_dimension.csv")}
    reference = ROOT / "data" / "analysis" / "under_reporting_by_dimension.csv"
    assert len(released) == N_DIMS
    if not reference.exists():
        pytest.skip("no analysis output to compare against")
    for r in read_csv(reference):
        mine = released[r["key"]]
        assert int(mine["n_not_reported"]) == int(r["n_not_reported"])
        for col in ("rate_unweighted", "rate_weighted", "se_weighted"):
            assert abs(float(mine[col]) - float(r[col])) < 1e-5, (r["key"], col)


def test_papers_are_included_only_and_cover_every_link(rel, source_systems):
    papers = read_csv(rel / "data" / "papers.csv")
    ids = {p["id"] for p in papers}
    src = {p["id"]: p for p in read_csv(ROOT / "data" / "papers.csv")}
    assert all(src[i]["included"] == "1" for i in ids)
    assert ids == {i for i, p in src.items() if p["included"] == "1"}
    assert {pid for s in source_systems for pid in s["papers"]} <= ids
    assert "included" not in papers[0] and "exclusion_reason" not in papers[0]


def test_reliability_has_every_dimension_with_intervals(rel, dims):
    rows = read_csv(rel / "data" / "reliability.csv")
    assert [r["dimension_key"] for r in rows] == [d["key"] for d in dims]
    for r in rows:
        assert float(r["kappa_ci_lo"]) <= float(r["kappa"]) <= float(r["kappa_ci_hi"])


def test_data_dictionary_covers_every_dimension_and_value(rel, dims):
    text = (rel / "schema" / "data_dictionary.md").read_text(encoding="utf-8")
    for state in ("`coded`", "`not_reported`", "`unresolved`"):
        assert state in text
    for d in dims:
        assert f"#### {d['id']} `{d['key']}`" in text
        for v in d.get("values", []):
            assert f"| `{v}` |" in text
    glossed = re.findall(r"^\| `[^`]+` \| (.+) \|$", text, re.MULTILINE)
    assert sum(g != "-" for g in glossed) >= 0.9 * len(glossed)


# ------------------------------------------------------------------------- packaging and versions


def test_version_everywhere(rel):
    assert (rel / "VERSION").read_text(encoding="utf-8") == VERSION + "\n"
    cff = (rel / "CITATION.cff").read_text(encoding="utf-8")
    assert re.search(rf"^version: {re.escape(VERSION)}$", cff, re.MULTILINE)
    assert re.search(r'^date-released: "2026-09-25"$', cff, re.MULTILINE)
    pkg = json.loads((rel / "datapackage.json").read_text(encoding="utf-8"))
    assert pkg["version"] == VERSION
    # the released copy differs from the repository's only on the version and date lines
    root_lines = (ROOT / "CITATION.cff").read_text(encoding="utf-8").splitlines()
    changed = [b for a, b in zip(root_lines, cff.splitlines(), strict=True) if a != b]
    assert all(line.startswith(("version:", "date-released:")) for line in changed)


def test_licences(rel):
    assert "Attribution 4.0 International" in (rel / "LICENSE-DATA").read_text(encoding="utf-8")
    assert (rel / "LICENSE-CODE").read_text(encoding="utf-8").startswith("MIT License")


TABLE_TYPES = {"string", "number", "integer", "boolean", "date", "datetime", "year", "object",
               "array", "any"}


def test_datapackage_is_structurally_valid(rel):
    pkg = json.loads((rel / "datapackage.json").read_text(encoding="utf-8"))
    assert pkg["$schema"] == "https://datapackage.org/profiles/2.0/datapackage.json"
    assert re.fullmatch(r"[a-z0-9._-]+", pkg["name"])
    assert pkg["licenses"] and all({"name", "path"} <= set(lic) for lic in pkg["licenses"])
    assert pkg["created"].endswith("Z") and pkg["title"] and pkg["resources"]
    names = [r["name"] for r in pkg["resources"]]
    assert len(names) == len(set(names))
    paths = {r["path"] for r in pkg["resources"]}
    assert paths == set(rd.tree_files(rel)) - {"datapackage.json", "CHECKSUMS.sha256"}
    by_name = {r["name"]: r for r in pkg["resources"]}
    for res in pkg["resources"]:
        assert re.fullmatch(r"[a-z0-9._-]+", res["name"])
        f = rel / res["path"]
        assert f.is_file()
        assert res["bytes"] == f.stat().st_size
        assert res["hash"] == "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()
        assert res["licenses"] and res["mediatype"] and res["format"]
        if res.get("profile") != "tabular-data-resource":
            continue
        schema = res["schema"]
        cols = [fl["name"] for fl in schema["fields"]]
        with f.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        assert rows[0] == cols, res["name"]
        assert all(len(r) == len(cols) for r in rows[1:])
        for fl in schema["fields"]:
            assert fl["type"] in TABLE_TYPES
            if (enum := fl.get("constraints", {}).get("enum")):
                i = cols.index(fl["name"])
                assert {r[i] for r in rows[1:]} - {""} <= set(enum), (res["name"], fl["name"])
        if (pk := schema.get("primaryKey")):
            idx = [cols.index(k) for k in pk]
            keys = [tuple(r[i] for i in idx) for r in rows[1:]]
            assert len(keys) == len(set(keys)), res["name"]
        for fk in schema.get("foreignKeys", []):
            target = by_name[fk["reference"]["resource"]]
            (ref_field,) = fk["reference"]["fields"]
            (own_field,) = fk["fields"]
            with (rel / target["path"]).open(encoding="utf-8", newline="") as fh:
                tv = {r[ref_field] for r in csv.DictReader(fh)}
            i = cols.index(own_field)
            assert {r[i] for r in rows[1:]} <= tv
    assert by_name["systems"]["jsonSchema"] == "schema/harness_db.schema.json"


def test_checksums_match(rel):
    lines = (rel / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    listed = {}
    for line in lines:
        digest, path = line.split("  ", 1)
        listed[path] = digest
    assert set(listed) == set(rd.tree_files(rel)) - {"CHECKSUMS.sha256"}
    for path, digest in listed.items():
        assert hashlib.sha256((rel / path).read_bytes()).hexdigest() == digest, path


def test_released_systems_json_is_the_source_byte_for_byte(rel):
    assert (rel / "data" / "systems.json").read_bytes() == \
        (ROOT / "data" / "systems.json").read_bytes()


def test_second_run_is_byte_identical_except_the_timestamp(builds):
    a, b = builds
    assert rd.tree_files(a) == rd.tree_files(b)
    differing = {f for f in rd.tree_files(a) if (a / f).read_bytes() != (b / f).read_bytes()}
    assert differing <= {"datapackage.json", "CHECKSUMS.sha256"}
    pa = json.loads((a / "datapackage.json").read_text(encoding="utf-8"))
    pb = json.loads((b / "datapackage.json").read_text(encoding="utf-8"))
    assert pa.pop("created") != pb.pop("created")
    assert pa == pb
    ca = (a / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    cb = (b / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    assert [x for x, y in zip(ca, cb, strict=True) if x != y] == \
        [x for x in ca if x.endswith("  datapackage.json")]


def test_zip_is_deterministic(rel, tmp_path):
    ts = rd.parse_timestamp(TS_A)
    again = tmp_path / "again.zip"
    rd.make_zip(rel, again, ts)
    assert again.read_bytes() == (rel.parent / f"{rel.name}.zip").read_bytes()


def test_value_cells_all_carry_a_quote_and_absence_locators_are_not_reported(cells):
    """Every valued cell has a verbatim quote and a locator. The only locator-without-quote
    evidence is on not_reported cells (the place the coder looked), never on a value."""
    values = [r for r in cells if r["state"] == "coded"]
    assert values and all(r["evidence_quote"] and r["evidence_locator"] for r in values)
    locator_only = [r for r in cells if r["evidence_locator"] and not r["evidence_quote"]]
    assert all(r["state"] == "not_reported" for r in locator_only)


def test_examples_and_linked_docs_are_shipped_unchanged(rel):
    for f in ("docs/coding_reliability.md", "docs/count_reconciliation.md",
              "docs/schema_changelog.md", "docs/protocol_prisma_p.md",
              "data/examples/openhands.json", "data/examples/swe-agent-1x.json",
              "data/examples/README.md"):
        assert (rel / f).read_bytes() == (ROOT / f).read_bytes(), f


def test_released_prisma_counts_names_no_working_files(rel):
    src = json.loads((ROOT / "data" / "prisma_counts.json").read_text(encoding="utf-8"))
    out = json.loads((rel / "data" / "prisma_counts.json").read_text(encoding="utf-8"))
    released = set(rd.tree_files(rel))

    def numbers(o):
        if isinstance(o, dict):
            return {k: numbers(v) for k, v in o.items() if not isinstance(v, str)}
        return o

    assert numbers({k: v for k, v in out.items() if k != "_release_note"}) == numbers(src)
    text = json.dumps(out)
    for token in rd.PATH_TOKEN.findall(text):
        assert token in released, token
    assert "data/raw" not in text and "data/screening" not in text
    assert out["included_systems"] == src["included_systems"]


def test_release_readme_explains_frame_versus_sample(rel):
    text = (rel / "README.md").read_text(encoding="utf-8")
    assert "### Reading prisma_counts.json" in text
    assert "6,504" in text and f"{N_SYSTEMS:,}" in text


def test_state_vocabulary_is_coded_not_value(cells, wide, rel, dims):
    assert {r["state"] for r in cells} == {"coded", "not_reported", "unresolved"}
    # not k.endswith("_state"): short_term_state is a dimension whose value column ends that way
    states = {r[f"{d['key']}_state"] for r in wide for d in dims}
    assert states == {"coded", "not_reported", "unresolved"}
    pkg = json.loads((rel / "datapackage.json").read_text(encoding="utf-8"))
    cells_res = next(r for r in pkg["resources"] if r["name"] == "cells")
    state_field = next(f for f in cells_res["schema"]["fields"] if f["name"] == "state")
    assert state_field["constraints"]["enum"] == ["coded", "not_reported", "unresolved"]
    assert re.search(r"^\s+coded\s", (rel / "VALIDATION.txt").read_text(encoding="utf-8"), re.MULTILINE)


def test_readme_is_the_dataset_card_plus_release_notes(rel):
    card = (ROOT / "DATASET_CARD.md").read_text(encoding="utf-8")
    text = (rel / "README.md").read_text(encoding="utf-8")
    assert text.startswith(card.rstrip("\n") + "\n")
    assert text.startswith("---\n") and "configs:" in text.split("---", 2)[1]
    notes = text[len(card.rstrip("\n")):]
    assert notes.count("## Release notes") == 1
    for heading in ("### Formats in this build", "### Validation counts",
                    "### Reading prisma_counts.json", "### Third-party content"):
        assert heading in notes


def test_cells_parquet_round_trips_to_cells_csv(rel):
    pytest.importorskip("pyarrow")
    pd = pytest.importorskip("pandas")
    assert (rel / "data" / "cells.parquet").is_file()
    assert (rel / "data" / "systems.parquet").is_file()
    from_csv = pd.read_csv(rel / "data" / "cells.csv", dtype=str, keep_default_na=False)
    from_pq = pd.read_parquet(rel / "data" / "cells.parquet").fillna("")
    assert list(from_pq.columns) == list(from_csv.columns)
    assert len(from_pq) == len(from_csv) == N_SYSTEMS * N_DIMS
    pd.testing.assert_frame_equal(from_pq.astype(str), from_csv, check_dtype=False)
    wide_pq = pd.read_parquet(rel / "data" / "systems.parquet")
    wide_csv = pd.read_csv(rel / "data" / "systems_wide.csv", dtype=str, keep_default_na=False)
    assert list(wide_pq.columns) == list(wide_csv.columns)
    assert list(wide_pq["system_id"]) == list(wide_csv["system_id"])


# ------------------------------------------------------------------------------------ failures


def test_build_fails_on_schema_errors_and_leaves_nothing(tmp_path):
    fake = tmp_path / "repo"
    for rel_path in ("schema/dimensions.json", "schema/harness_db.schema.json",
                     "docs/coding_manual.md", "docs/protocol_prisma_p.md", "CITATION.cff",
                     "LICENSE-DATA", "LICENSE-CODE", "data/papers.csv", "data/results.csv",
                     "data/prisma_counts.json", "data/coding_frame.csv",
                     "data/coded/reliability_final.json", "docs/coding_reliability.md",
                     "docs/count_reconciliation.md", "docs/schema_changelog.md",
                     "data/examples/README.md", "data/examples/openhands.json",
                     "data/examples/swe-agent-1x.json", "DATASET_CARD.md"):
        (fake / rel_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel_path, fake / rel_path)
    (fake / "data" / "systems.json").write_text(json.dumps([{"id": "Not A Slug"}]),
                                                encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(rd.ReleaseError, match="JSON Schema"):
        rd.build(VERSION, out, TS_A, repo=fake, quiet=True)
    assert not any(out.iterdir())


def test_refuses_to_write_under_data(tmp_path):
    with pytest.raises(rd.ReleaseError, match="inside"):
        rd.build(VERSION, ROOT / "data" / "release", TS_A, quiet=True)


def test_rejects_non_semver():
    with pytest.raises(rd.ReleaseError):
        rd.validate_version("v1")


# ------------------------------------------------------------------------------------- helpers


@pytest.mark.parametrize("evidence,expected", [
    ('"MCP Server Management" (README.md@9f1bc76)', ("MCP Server Management", "README.md@9f1bc76")),
    ('"a " (b" and c" (README.md (Installation))',
     ('a " (b" and c', "README.md (Installation)")),
    ("README.md@585fe7c", ("", "README.md@585fe7c")),
    ("", ("", "")),
])
def test_split_evidence(evidence, expected):
    assert rd.split_evidence(evidence) == expected


def test_value_text_and_flags():
    assert rd.value_text(["mcp", "other"]) == "mcp|other"
    assert rd.value_text(12) == "12"
    assert rd.value_text(None) == ""
    cell = {"unresolved": True, "value": None,
            "note": "unresolved after the repair pass (scalar_for_multi, locator_no_line). x"}
    assert rd.cell_flags(cell) == ["scalar_for_multi", "locator_no_line"]
    assert rd.cell_flags({"not_reported": True, "note": "nothing"}) == []


def test_citation_for_release_only_touches_version_and_date():
    src = 'cff-version: 1.2.0\ntitle: "X"\nversion: 0.1.0-dev\ndate-released: "2026-09-16"\n'
    out = rd.citation_for_release(src, "1.0.0", "2026-10-01")
    assert out == 'cff-version: 1.2.0\ntitle: "X"\nversion: 1.0.0\ndate-released: "2026-10-01"\n'
