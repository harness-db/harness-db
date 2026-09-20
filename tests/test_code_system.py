"""Tests for phase-4 coding (``scripts/code_system.py``): cell validation against
``schema/dimensions.json`` and the coding manual's general rules, verbatim quote checking, evidence
bundle assembly, resumability, the cheap targeted pass B, and the separation of the double coding.

No network and no LLM calls: the backend is a fake injected into ``main(..., backend=...)``.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import code_system as cs
import screen_llm

DIMS = {d["id"]: d for d in cs.load_dimensions()}
BUNDLE_TEXT = "the agent loop renders a jinja template for the system prompt at every step"
#: a span that is verbatim both in BUNDLE_TEXT and in the paper written by ``write_inputs``
QUOTE = "renders a jinja template for the system prompt"


# ---------------------------------------------------------------- helpers


def squashed(text: str = BUNDLE_TEXT) -> str:
    import fulltext_screen as fs
    return fs._squash(text)


def cell(value, quote=QUOTE, locator="config/default.yaml:6@0f3acaf", confidence="medium", **extra):
    c = {"value": value, "evidence_quote": quote, "evidence_locator": locator, "confidence": confidence}
    c.update(extra)
    return c


def check(dim_id: str, value, **kw) -> cs.CellCheck:
    return cs.check_cell(DIMS[dim_id], cell(value, **kw), squashed())


class FakeBackend:
    """Stands in for ``screen_llm.vote_batch_claude_code``: records every call, invents no cost."""

    def __init__(self, cell_for=None):
        self.calls: list[dict] = []
        self.cell_for = cell_for or (lambda dim_id, item: cell(default_value(dim_id)))

    def __call__(self, exe, model, system_file, batch, effort=None, schema=None, prompt=None, text_json=False):
        text = prompt(batch)
        self.calls.append({"dims": list(batch[0]["dims"]), "prompt_chars": len(text),
                           "document": batch[0]["document"], "schema": schema, "system_id": batch[0]["id"]})
        votes = [{"record_id": it["id"], "cells": {d: self.cell_for(d, it) for d in it["dims"]}} for it in batch]
        return screen_llm.BatchResult(votes, "claude-opus-fake", 1000, 200, 0, 0, 0.05)


def default_value(dim_id: str):
    """A plausible, schema-valid answer for one dimension."""
    d = DIMS[dim_id]
    if d["type"] == "enum":
        v = d["values"][-1]
        return [v] if d.get("multi") else v
    if d["type"] == "integer":
        return 3
    if d["type"] == "date":
        return "2025-02-13"
    return "v1.1.0"


PAPER = """record_id: test:rec1
source_used: arxiv_html
fetched_url: https://example.org/paper
fetched_title: AgentX, a harness with a loop
fetched_at: 2026-09-19T00:00:00Z

Abstract
AgentX runs a ReAct loop in a docker container and renders a jinja template for the system prompt.

3 Method
The agent calls a bash tool and a str_replace_editor tool, and stops after at most 30 steps.
{filler}

References
[1] Somebody. A cited paper that must not reach the bundle. 2024.
[2] Someone Else. Another citation that must not reach the bundle. 2025.

A Prompt Templates
The appendix states that the system prompt is rendered once per run.
"""

REPO = """record_id: test:rec1
repo_url: https://github.com/acme/agentx
ref: commit:main 8248df0d247a 2026-05-09
stars: 1234
fetched_at: 2026-09-19T14:37:42Z

## README (README.md)
AgentX is a harness. The default config sets max_steps to 30 and runs every command in docker.
{filler}
"""


def write_inputs(tmp_path: Path, paper_filler: int = 200, repo_filler: int = 200) -> tuple[Path, Path]:
    """A one-system frame plus the fetched evidence on disk, in the real file layout."""
    ft = tmp_path / "fulltext"
    ft.mkdir()
    (ft / "test__rec1.txt").write_text(PAPER.format(filler="lorem ipsum dolor " * paper_filler), encoding="utf-8")
    (ft / "test__rec1__repo.txt").write_text(REPO.format(filler="repo code line " * repo_filler), encoding="utf-8")
    frame = tmp_path / "coding_frame.csv"
    with frame.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["system_id", "name", "version", "repo_url", "stars", "stratum", "coded",
                                           "weight", "codability_flag", "max_codable_count",
                                           "canonical_record_id", "member_record_ids"])
        w.writeheader()
        w.writerow({"system_id": "agentx", "name": "AgentX", "version": "v1", "stars": "1234",
                    "repo_url": "https://github.com/acme/agentx", "stratum": "H", "coded": "1", "weight": "1.0",
                    "codability_flag": "pass", "max_codable_count": "30",
                    "canonical_record_id": "test:rec1", "member_record_ids": "test:rec1"})
    return frame, ft


def run(tmp_path: Path, backend: FakeBackend, *extra: str) -> int:
    frame, ft = tmp_path / "coding_frame.csv", tmp_path / "fulltext"
    argv = ["--frame", str(frame), "--fulltext-dir", str(ft), "--out-dir", str(tmp_path / "coded"),
            "--repo-index", str(tmp_path / "no_repo_index.csv"), "--workers", "1", *extra]
    return cs.main(argv, backend=backend)


def cells_of(tmp_path: Path, name: str = "cells.csv") -> list[dict[str, str]]:
    return cs.read_csv(tmp_path / "coded" / name)


# ---------------------------------------------------------------- cell validation


def test_good_cell_passes():
    chk = check("A1", "templated")
    assert chk.flags == []
    assert chk.value == "templated" and chk.resolved and chk.quote_verbatim and not chk.not_reported


def test_good_multi_cell_is_sorted_list():
    chk = check("A3", ["summarize", "truncate_oldest"])
    assert chk.flags == [] and chk.value == ["summarize", "truncate_oldest"] and chk.resolved
    assert cs.value_text(chk.value) == "summarize|truncate_oldest"


def test_wrong_enum_value_is_flagged_not_coerced():
    chk = check("A1", "jinja")
    assert "not_in_enum" in chk.flags and chk.invalid and not chk.resolved
    assert chk.value == "jinja"  # recorded as answered, never silently replaced


def test_scalar_for_multi_is_flagged():
    chk = check("A3", "summarize")
    assert "scalar_for_multi" in chk.flags and chk.invalid and not chk.resolved
    assert chk.value == ["summarize"]


def test_list_for_single_is_flagged():
    chk = check("A1", ["templated", "static"])
    assert "list_for_single" in chk.flags and chk.invalid


def test_unparseable_integer_is_flagged():
    chk = check("B2", "about five")
    assert "bad_integer" in chk.flags and chk.invalid and chk.value is None
    assert check("B2", "17").value == 17 and check("B2", 17).flags == []


def test_bad_date_is_flagged():
    assert "bad_date" in check("M5", "Feb 2025").flags
    assert check("M5", "2025-02-13").flags == []


def test_none_beside_other_values_is_flagged():
    chk = check("A3", ["none", "summarize"])
    assert "none_with_other_values" in chk.flags and chk.invalid


def test_sentinel_is_not_the_same_as_absence():
    """Manual general rule 2: 'the source does not say' is not_reported + value null."""
    nr = cs.check_cell(DIMS["E3"], cell(None, quote="", not_reported=True), squashed())
    assert nr.not_reported and nr.value is None and not nr.resolved
    assert "missing_quote" not in nr.flags  # a sentinel needs no quote
    absent = check("E3", "none")
    assert not absent.not_reported and absent.value == "none" and absent.resolved  # a genuine absence, with evidence
    assert "absence_without_evidence" in cs.check_cell(DIMS["E3"], cell("none", quote=""), squashed()).flags


def test_null_value_without_the_flag_is_still_a_sentinel_but_flagged():
    chk = cs.check_cell(DIMS["A1"], cell(None, quote=""), squashed())
    assert chk.not_reported and "null_without_not_reported" in chk.flags


# ---------------------------------------------------------------- quote verification


def test_verbatim_quote_passes_and_paraphrase_is_flagged():
    ok = check("A1", "templated", quote="renders a jinja template")
    assert ok.quote_verbatim and "quote_not_in_bundle" not in ok.flags and ok.resolved
    # whitespace, case and punctuation differences are still verbatim (the fulltext_screen rule)
    loose = check("A1", "templated", quote="Renders a  JINJA\ntemplate,")
    assert loose.quote_verbatim
    para = check("A1", "templated", quote="the prompt is built from a template engine")
    assert "quote_not_in_bundle" in para.flags and not para.quote_verbatim and not para.resolved


def test_missing_quote_and_locator_are_flagged():
    chk = cs.check_cell(DIMS["A1"], cell("templated", quote="", locator=""), squashed())
    assert "missing_quote" in chk.flags and "missing_locator" in chk.flags and not chk.resolved


# ---------------------------------------------------------------- evidence bundle


def test_bundle_strips_reference_list_but_keeps_the_appendix(tmp_path):
    write_inputs(tmp_path)
    row = cs.frame_rows(tmp_path / "coding_frame.csv")[0]
    b = cs.assemble_bundle(row, cap=400_000, root=tmp_path / "fulltext")
    assert "must not reach the bundle" not in b.text
    assert "The appendix states that the system prompt is rendered once per run." in b.text
    assert "renders a jinja template" in b.text            # paper evidence
    assert "runs every command in docker" in b.text        # repository evidence


def test_bundle_records_what_was_truncated(tmp_path):
    write_inputs(tmp_path, paper_filler=2000, repo_filler=2000)
    row = cs.frame_rows(tmp_path / "coding_frame.csv")[0]
    cap = 6000
    b = cs.assemble_bundle(row, cap=cap, root=tmp_path / "fulltext")
    assert b.chars <= cap and b.truncated
    assert "[TRUNCATED:" in b.text
    kinds = {p["kind"]: p for p in b.parts}
    assert set(kinds) == {"paper", "repo"}
    for p in b.parts:
        assert p["truncated"] and 0 < p["chars_used"] < p["chars_available"]
    assert kinds["repo"]["chars_used"] >= int(0.2 * cap)  # repository evidence keeps its reserved share
    big = cs.assemble_bundle(row, cap=400_000, root=tmp_path / "fulltext")
    assert not big.truncated and "[TRUNCATED:" not in big.text


def test_bundle_notes_missing_evidence(tmp_path):
    write_inputs(tmp_path)
    row = dict(cs.frame_rows(tmp_path / "coding_frame.csv")[0])
    row["member_record_ids"] = "test:rec1;test:absent"
    b = cs.assemble_bundle(row, root=tmp_path / "fulltext")
    assert b.missing == ["test:absent"] and "no fetched full text for: test:absent" in b.text


# ---------------------------------------------------------------- a whole run


def test_pass_a_writes_every_cell_once_and_is_resumable(tmp_path):
    write_inputs(tmp_path)
    backend = FakeBackend()
    assert run(tmp_path, backend) == 0
    assert len(backend.calls) == 1 and backend.calls[0]["dims"] == list(DIMS)
    rows = cells_of(tmp_path)
    assert len(rows) == len(DIMS)
    assert {r["dimension_id"] for r in rows} == set(DIMS)
    assert all(r["pass"] == "A" and r["prompt_version"] == cs.PROMPT_VERSION for r in rows)
    assert all(r["coder"] == "llm-prefill" and r["quote_verbatim"] == "1" for r in rows)
    assert all(r["cost_usd"] and r["tokens_in"] and r["call_id"] for r in rows)
    assert set(rows[0]) == set(cs.CELL_COLUMNS)

    again = FakeBackend()
    assert run(tmp_path, again) == 0
    assert again.calls == []                       # nothing re-coded
    assert len(cells_of(tmp_path)) == len(DIMS)    # and nothing re-written

    redo = FakeBackend()
    assert run(tmp_path, redo, "--redo", "agentx") == 0
    assert len(redo.calls) == 1 and len(cells_of(tmp_path)) == len(DIMS)


def test_pass_a_writes_the_system_json_for_kappa(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend())
    rec = json.loads((tmp_path / "coded" / "json" / "agentx.json").read_text(encoding="utf-8"))
    assert rec["system_id"] == "agentx" and rec["bundle"]["chars"] > 0
    assert set(rec["coding"]) == {d["key"] for d in DIMS.values()}
    assert rec["coding"]["system_prompt_style"]["evidence_quote"]
    assert "not_reported" in rec["coding"]["system_prompt_style"]
    lines = (tmp_path / "coded" / "systems_coded.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["pass"] == "A"


# ---------------------------------------------------------------- pass B


UNRESOLVED = ("A1", "B2", "C3", "G1")


def pass_a_with_holes(dim_id, item):
    """Pass-A answers that leave four cells unresolved, one per failure mode."""
    if dim_id == "A1":
        return cell(None, quote="", not_reported=True)                      # sentinel
    if dim_id == "B2":
        return cell("about five")                                           # invalid integer
    if dim_id == "C3":
        return cell("single", quote="")                                     # no quote
    if dim_id == "G1":
        return cell("container", quote="it runs everything inside a sandboxed image")  # paraphrase
    return cell(default_value(dim_id))


def test_pass_b_only_targets_unresolved_cells_and_sends_less_text(tmp_path):
    write_inputs(tmp_path, paper_filler=800, repo_filler=800)
    a = FakeBackend(pass_a_with_holes)
    assert run(tmp_path, a) == 0
    rows = {r["dimension_id"]: r for r in cells_of(tmp_path)}
    assert {i for i, r in rows.items() if r["resolved"] == "0"} == set(UNRESOLVED)
    assert "quote_not_in_bundle" in rows["G1"]["flags"] and rows["A1"]["not_reported"] == "1"

    b = FakeBackend()
    assert run(tmp_path, b, "--pass", "B") == 0
    assert len(b.calls) == 1
    assert b.calls[0]["dims"] == list(UNRESOLVED)                       # only the unresolved cells
    assert b.calls[0]["prompt_chars"] < a.calls[0]["prompt_chars"]      # strictly less text than pass A
    assert len(b.calls[0]["document"]) < len(a.calls[0]["document"])
    assert "system_prompt_style" in b.calls[0]["document"]              # keyword windows, per dimension

    rows2 = cells_of(tmp_path)
    assert len(rows2) == len(DIMS) + len(UNRESOLVED)                    # the pass-A attempts stay in the file
    b_rows = {r["dimension_id"]: r for r in rows2 if r["pass"] == "B"}
    assert set(b_rows) == set(UNRESOLVED) and all(r["resolved"] == "1" for r in b_rows.values())

    rec = json.loads((tmp_path / "coded" / "json" / "agentx.json").read_text(encoding="utf-8"))
    assert rec["pass"] == "B" and rec["cells_unresolved"] == []
    assert rec["coding"]["system_prompt_style"]["resolved"]             # pass B superseded pass A
    assert set(rec["history"]) == set(UNRESOLVED)
    assert rec["history"]["B2"]["superseded_pass"] == "A"

    third = FakeBackend()
    assert run(tmp_path, third, "--pass", "B") == 0
    assert third.calls == []                                           # pass B is resumable too


def test_pass_b_document_is_smaller_than_any_bundle():
    text = ("padding " * 500) + "the sandbox is a docker container with no network access " + ("padding " * 500)
    doc = cs.pass_b_document(text, [DIMS["G1"], DIMS["G3"]])
    assert 0 < len(doc) < len(text)
    assert "docker container" in doc
    tiny = cs.pass_b_document("short text about a docker container", [DIMS["G1"]])
    assert 0 < len(tiny) < len("short text about a docker container")


def test_pass_b_does_nothing_without_a_first_pass(tmp_path):
    write_inputs(tmp_path)
    b = FakeBackend()
    assert run(tmp_path, b, "--pass", "B") == 0
    assert b.calls == [] and cells_of(tmp_path) == []


# ---------------------------------------------------------------- double coding


def test_double_coding_is_a_separate_file_and_a_deterministic_sample(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend())
    sample = cs.double_sample(cs.frame_rows(tmp_path / "coding_frame.csv"), 1.0, "seed-x")
    assert sample == ["agentx"]
    assert cs.double_sample(cs.frame_rows(tmp_path / "coding_frame.csv"), 0.0, "seed-x") == []

    d = FakeBackend()
    assert run(tmp_path, d, "--double", "--double-sample", "1.0", "--seed", "seed-x") == 0
    assert len(d.calls) == 1
    assert len(cells_of(tmp_path, "cells_pass2.csv")) == len(DIMS)
    assert len(cells_of(tmp_path)) == len(DIMS)  # the first coding is untouched, never merged
    assert all(r["coder"] == "llm-prefill-2" for r in cells_of(tmp_path, "cells_pass2.csv"))
    assert (tmp_path / "coded" / "json_pass2" / "agentx.json").exists()
    assert json.loads((tmp_path / "coded" / "double_sample.json").read_text(encoding="utf-8"))["n"] == 1


def test_double_without_a_sample_is_refused(tmp_path):
    write_inputs(tmp_path)
    assert run(tmp_path, FakeBackend(), "--double") == 2


# ---------------------------------------------------------------- prompt and schema plumbing


def test_prompt_and_schema_come_from_the_schema_and_the_manual():
    dims = cs.load_dimensions()
    assert len(dims) == 38
    sections = cs.manual_sections()
    assert set(sections) >= {d["id"] for d in dims}
    sp = cs.system_prompt(dims)
    assert "not_reported" in sp and "General rules" not in sp.split("\n")[0]
    for d in dims:                                    # every dimension's rule text reaches the prompt
        assert d["key"] in sp
        if d["type"] == "enum":
            assert d["values"][0] in sp
    schema = cs.batch_schema([d["id"] for d in dims])
    props = schema["properties"]["votes"]["items"]["properties"]["cells"]["properties"]
    assert set(props) == {d["id"] for d in dims}
    assert props["A1"]["required"] == ["value", "evidence_quote", "evidence_locator", "confidence"]


def test_summary_line_is_emitted(tmp_path, capsys):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend())
    out = [ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("SUMMARY ")]
    assert len(out) == 1
    s = json.loads(out[0][len("SUMMARY "):])
    for k in ("pass", "cells_coded", "cells_unresolved", "quotes_non_verbatim", "tokens_in", "tokens_out",
              "cost_usd", "wall_seconds", "bundle_chars_mean", "prompt_version"):
        assert k in s
    assert s["cells_coded"] == len(DIMS) and s["quotes_non_verbatim"] == 0
    assert (tmp_path / "coded" / "run.log").exists()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
