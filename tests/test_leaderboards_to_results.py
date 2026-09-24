"""Tests for scripts/leaderboards_to_results.py (Phase 6 task 44). No network, no model calls."""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import leaderboards_to_results as l2r
from validate import RESULT_COLUMNS as VALIDATE_COLUMNS

# --------------------------------------------------------------------------------------
# A small stand-in registry. `mega-group` imitates the census's over-merged `rci-agent`
# (114 pooled names) and `twin-a`/`twin-b` imitate two systems sharing one name.
# --------------------------------------------------------------------------------------

FIXTURE_SYSTEMS = [
    {"id": "openhands", "name": "OpenHands (CodeActAgent)",
     "urls": {"repo": "https://github.com/All-Hands-AI/OpenHands"}},
    {"id": "browser-use", "name": "Browser Use",
     "urls": {"repo": "https://github.com/browser-use/browser-use"}},
    {"id": "patchpilot", "name": "PatchPilot",
     "urls": {"repo": "https://github.com/ucsb-mlsec/PatchPilot"}},
    {"id": "aide", "name": "AIDE", "urls": {"repo": "https://github.com/wecoai/aideml"}},
    {"id": "jules", "name": "Jules"},
    {"id": "osworld-reference-agent", "name": "OSWorld reference agent",
     "urls": {"repo": "https://github.com/xlang-ai/OSWorld"}},
    {"id": "mega-group", "name": "Mega Group"},
    {"id": "twin-a", "name": "Twin"},
    {"id": "twin-b", "name": "Twin"},
    {"id": "agent-workflow-memory", "name": "Agent Workflow Memory (AWM)"},
]
FIXTURE_VARIANTS = {
    "mega-group": ["Mega Group", "SWE-agent", "A-Agent", "B-Agent", "C-Agent", "D-Agent",
                   "E-Agent", "F-Agent"],
    "openhands": ["OpenHands", "OpenHands (CodeActAgent)"],
    "twin-a": ["Twin"],
    "twin-b": ["Twin"],
}


@pytest.fixture(scope="module")
def registry_files(tmp_path_factory):
    d = tmp_path_factory.mktemp("registry")
    systems = d / "systems.json"
    systems.write_text(json.dumps(FIXTURE_SYSTEMS), encoding="utf-8")
    cands = d / "systems_candidates.csv"
    with cands.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=["system_id", "name", "name_variants", "repo_url"],
                           lineterminator="\n")
        w.writeheader()
        for s in FIXTURE_SYSTEMS:
            w.writerow({"system_id": s["id"], "name": s["name"],
                        "name_variants": ";".join(FIXTURE_VARIANTS.get(s["id"], [s["name"]])),
                        "repo_url": (s.get("urls") or {}).get("repo", "")})
        # a census system that was never coded: it must be reported, never attributed
        w.writerow({"system_id": "marscode-agent", "name": "MarsCode Agent",
                    "name_variants": "MarsCode Agent", "repo_url": ""})
    return systems, cands


@pytest.fixture(scope="module")
def reg(registry_files):
    return l2r.load_registry(*registry_files)


def record(venue, title, entries, url=None, date=None, benchmark=None):
    return {"venue": venue, "title": title, "url": url, "date": date,
            "extra": {"benchmark": benchmark or venue, "n_entries": len(entries),
                      "entries": entries}}


def cands_for(venue, title, entry):
    return l2r.harness_candidates(venue, record(venue, title, [entry]), entry)


# --------------------------------------------------------------------------------------
# 1. flattening
# --------------------------------------------------------------------------------------


def test_one_row_per_entry_not_per_board_record(reg):
    entries = [{"split": "Lite", "model": "GPT-4o", "score": 30.0, "metric": "% resolved"},
               {"split": "Verified", "model": "GPT-4o", "score": 40.0, "metric": "% resolved"},
               {"split": "Test", "model": "GPT-4o", "score": 20.0, "metric": "% resolved"}]
    rec = record("SWE-bench", "OpenHands", entries)
    rows, rep = l2r.convert([rec], reg)
    assert len(rows) == 3
    assert rep.rows["SWE-bench"] == 3
    assert [r["split"] for r in rows] == ["Lite", "Verified", "Test"]
    assert {r["benchmark"] for r in rows} == {"SWE-bench"}


def test_entry_without_a_usable_score_is_dropped_and_counted(reg):
    entries = [{"split": "airline", "model": "gpt-4o", "score": 36.5, "metric": "pass^1 %"},
               {"split": "retail", "model": "gpt-4o", "score": None, "metric": "pass^1 %"}]
    rows, rep = l2r.convert([record("tau-bench", "tau-bench reference agent", entries)], reg)
    assert len(rows) == 1
    assert rep.skipped_no_score["tau-bench"] == 1


# --------------------------------------------------------------------------------------
# 2. attribution: confident yes, ambiguous no
# --------------------------------------------------------------------------------------


def test_confident_name_match_attributes_and_records_method_and_string(reg):
    entry = {"split": "Verified", "model": "Claude 3.7", "score": 60.0, "metric": "% resolved",
             "raw_name": "OpenHands + Claude 3.7 Sonnet"}
    rows, _ = l2r.convert([record("SWE-bench", "OpenHands", [entry])], reg)
    assert rows[0]["system_id"] == "openhands"
    assert "exact-key" in rows[0]["notes"]
    assert "'OpenHands'" in rows[0]["notes"]


def test_ambiguous_name_is_left_unattributed_with_both_ids_in_notes(reg):
    entry = {"split": "Verified", "model": "GPT-5", "score": 10.0, "metric": "% resolved",
             "raw_name": "Twin + GPT 5"}
    rows, _ = l2r.convert([record("SWE-bench", "Twin", [entry])], reg)
    assert rows[0]["system_id"] == ""
    assert "ambiguous" in rows[0]["notes"]
    assert "twin-a" in rows[0]["notes"] and "twin-b" in rows[0]["notes"]


def test_unknown_name_is_left_unattributed_and_says_why(reg):
    entry = {"split": "Lite", "model": "GPT-4o", "score": 38.0, "metric": "% resolved",
             "raw_name": "AbanteAI MentatBot + GPT 4o (2024-05-13)"}
    rows, _ = l2r.convert([record("SWE-bench", "AbanteAI MentatBot", [entry])], reg)
    assert rows[0]["system_id"] == ""
    assert "no registry match" in rows[0]["notes"]
    assert "MentatBot" in rows[0]["notes"]


def test_over_merged_census_group_is_refused(reg):
    """`mega-group` pools eight names, as the real `rci-agent` pools 114."""
    entry = {"split": "Verified", "model": "GPT-4o", "score": 33.0, "metric": "% resolved",
             "raw_name": "SWE-agent + GPT 4o (2024-05-13)"}
    rows, _ = l2r.convert([record("SWE-bench", "SWE-agent", [entry])], reg)
    assert rows[0]["system_id"] == ""
    assert "over-merged" in rows[0]["notes"]


def test_model_only_name_never_attributes(reg):
    entry = {"split": "text/telecom", "model": "gpt-5.2", "score": 50.0, "metric": "pass^1 %",
             "raw_name": "gpt-5.2 high [gpt-5-2_openai_2026-01-01]"}
    rows, _ = l2r.convert([record("tau2-bench", "gpt-5.2 (OpenAI)", [entry])], reg)
    assert rows[0]["system_id"] == ""
    assert l2r.is_model_string("gpt-5.2 high") is True
    assert l2r.is_model_string("Nemotron-CORTEXA") is False


def test_placeholder_submission_names_never_attribute(reg):
    match = l2r.match_system(reg, [l2r.Cand("test-agent", "record title")], unverified=True)
    assert match.system_id == ""
    assert "placeholder" in match.reason


def test_a_version_mismatch_blocks_a_base_name_match(reg):
    """PatchPilot-v1.1 is PatchPilot; "PatchPilot 2" would be a separate system (protocol 4.4)."""
    ok = l2r.match_system(reg, [l2r.Cand("PatchPilot-v1.1", "raw_name")])
    assert (ok.system_id, ok.method) == ("patchpilot", f"fuzzy-{l2r.FUZZY_THRESHOLD}")
    v2 = l2r.match_system(reg, [l2r.Cand("PatchPilot 2", "raw_name")])
    assert v2.system_id == ""


def test_fuzzy_threshold_keeps_open_deep_research_off_open_deep_search(reg):
    """The real false positive this threshold was raised for (ratio 93.3 at the registry's 92)."""
    assert l2r.keys_match("opendeepresearch", "opendeepsearch", 92) is True
    assert l2r.keys_match("opendeepresearch", "opendeepsearch", l2r.FUZZY_THRESHOLD) is False


def test_uncorroborated_org_prefix_is_refused_but_a_vendor_without_a_repo_is_kept(reg):
    aide = l2r.match_system(reg, l2r.harness_candidates(
        "SWE-bench", record("SWE-bench", "CodeStory Aide", []),
        {"raw_name": "CodeStory Aide + Mixed Models", "model": "Mixed"}))
    assert aide.system_id == ""
    assert "does not corroborate" in aide.reason

    jules = l2r.match_system(reg, l2r.harness_candidates(
        "SWE-bench", record("SWE-bench", "Google Jules", []),
        {"raw_name": "Google Jules", "model": "Gemini 2.5 Pro"}))
    assert jules.system_id == "jules"


def test_census_only_system_is_reported_but_not_attributed(reg):
    entry = {"split": "Verified", "model": "GPT-4o", "score": 50.0, "metric": "% resolved",
             "raw_name": "MarsCode Agent + GPT 4o"}
    rows, rep = l2r.convert([record("SWE-bench", "MarsCode Agent", [entry])], reg)
    assert rows[0]["system_id"] == ""
    assert "census-only system marscode-agent" in rows[0]["notes"]
    assert any(k.startswith("marscode-agent <-") for k in rep.census_hints)


# --------------------------------------------------------------------------------------
# 3. model vs harness
# --------------------------------------------------------------------------------------


def test_model_comes_from_model_ids_when_present():
    entry = {"split": "Lite", "model": "GPT-4o", "score": 38.0, "metric": "% resolved",
             "raw_name": "AbanteAI MentatBot + GPT 4o (2024-05-13)",
             "model_ids": ["gpt-4o-2024-05-13"]}
    model, note = l2r.model_of("SWE-bench", {}, entry, ["AbanteAI MentatBot"])
    assert model == "gpt-4o-2024-05-13"
    assert note == "model from model_ids"


def test_model_is_parsed_from_raw_name_when_the_board_gives_none():
    entry = {"split": "Lite", "score": 38.0, "metric": "% resolved", "model": None,
             "raw_name": "AbanteAI MentatBot + GPT 4o (2024-05-13)"}
    model, note = l2r.model_of("SWE-bench", {}, entry, ["AbanteAI MentatBot"])
    assert model == "GPT 4o (2024-05-13)"
    assert "parsed from raw_name" in note


def test_several_model_ids_leave_the_model_empty_unless_asked_otherwise():
    entry = {"split": "Verified", "model": "Multiple", "score": 76.4, "metric": "% resolved",
             "model_ids": ["claude-4-sonnet", "gpt-5-0807-global"]}
    blank, note = l2r.model_of("SWE-bench", {}, entry, ["ACoder"])
    assert blank == ""
    assert "claude-4-sonnet" in note and "gpt-5-0807-global" in note
    first, _ = l2r.model_of("SWE-bench", {}, entry, ["ACoder"], multi_model="first")
    assert first == "claude-4-sonnet"


def test_the_harness_name_never_lands_in_the_model_column(reg):
    """WebArena's sheet repeats the submission name in its model column."""
    entry = {"split": "WebArena", "model": "Agent Workflow Memory", "score": 35.5,
             "metric": "success rate %", "raw_name": "AWM / Agent Workflow Memory"}
    rows, _ = l2r.convert([record("WebArena", "AWM", [entry])], reg)
    assert rows[0]["system_id"] == "agent-workflow-memory"
    assert rows[0]["model"] == ""
    assert "repeats the submission name" in rows[0]["notes"]


def test_terminal_bench_names_are_split_into_harness_and_model():
    raw = "20251012_openhands_claude-4-5-sonnet"
    assert l2r.tbench_harness(raw, "claude-4-5-sonnet") == "openhands"
    model, note = l2r.model_of("Terminal-Bench", {}, {"raw_name": raw, "model": "claude-4-5-sonnet"},
                               ["openhands"])
    assert model == "claude-4-5-sonnet"
    assert note == "model from the board's model column"


# --------------------------------------------------------------------------------------
# 4. metric, split, score, url, cost
# --------------------------------------------------------------------------------------


def test_metric_and_split_are_kept_verbatim_and_the_score_is_numeric(reg):
    entry = {"split": "Lite", "model": "GPT-4o", "score": 38.0, "metric": "% resolved"}
    rows, _ = l2r.convert([record("SWE-bench", "OpenHands", [entry])], reg)
    assert rows[0]["metric"] == "% resolved"
    assert rows[0]["split"] == "Lite"
    assert float(rows[0]["score"]) == 38.0
    assert rows[0]["comparable_key"] == ""
    assert rows[0]["tokens"] == ""


def test_source_url_falls_back_entry_then_record_then_board(reg):
    e_url = {"split": "s", "model": "m", "score": 1.0, "metric": "x", "url": "https://entry"}
    e_none = {"split": "s", "model": "m", "score": 1.0, "metric": "x"}
    rows, _ = l2r.convert([record("SWE-bench", "OpenHands", [e_url, e_none], url="https://record"),
                           record("GAIA", "sub", [e_none])], reg)
    assert rows[0]["source_url"] == "https://entry"
    assert rows[1]["source_url"] == "https://record"
    assert "from the entry" in rows[0]["notes"]
    assert "from the harvest record" in rows[1]["notes"]
    assert rows[2]["source_url"] == l2r.BOARD_URL["GAIA"]
    assert "board's public page" in rows[2]["notes"]


def test_cost_is_taken_from_the_boards_own_per_run_field(reg):
    entry = {"split": "online_mind2web", "model": "Claude Sonnet 4", "score": 40.0,
             "metric": "accuracy %", "cost_usd": 1577.26, "verified": True}
    rows, _ = l2r.convert([record("HAL", "Browser-Use", [entry])], reg)
    assert rows[0]["cost_usd"] == "1577.26"
    assert "hal_verified=true" in rows[0]["notes"]
    assert "hal_benchmark=online_mind2web" in rows[0]["notes"]


# --------------------------------------------------------------------------------------
# 5. GAIA policy and --skip-boards
# --------------------------------------------------------------------------------------


def test_every_gaia_row_is_marked_an_unverified_public_submission(reg):
    entry = {"split": "test", "model": None, "score": 1.33, "metric": "accuracy %",
             "level1": 0.0, "level2": 1.0, "level3": 0.0}
    rows, _ = l2r.convert([record("GAIA", "0707_1", [entry])], reg)
    assert len(rows) == 1
    assert "unverified self-reported public submission" in rows[0]["notes"]
    assert rows[0]["system_id"] == ""
    assert rows[0]["model"] == ""


def test_gaia_attributes_only_on_an_exact_name_never_fuzzily(reg):
    exact = {"split": "test", "model": "Claude", "score": 40.0, "metric": "accuracy %"}
    fuzzy = {"split": "test", "model": "Claude", "score": 40.0, "metric": "accuracy %"}
    rows, _ = l2r.convert([record("GAIA", "Browser Use", [exact]),
                           record("GAIA", "Browser Used", [fuzzy])], reg)
    assert rows[0]["system_id"] == "browser-use"
    assert rows[1]["system_id"] == ""


def test_skip_boards_drops_a_board_and_counts_what_it_dropped(reg):
    recs = [record("GAIA", "0707_1", [{"split": "test", "model": None, "score": 1.0,
                                       "metric": "accuracy %"}]),
            record("SWE-bench", "OpenHands", [{"split": "Lite", "model": "GPT-4o", "score": 30.0,
                                               "metric": "% resolved"}])]
    rows, rep = l2r.convert(recs, reg, skip_boards={"gaia"})
    assert [r["benchmark"] for r in rows] == ["SWE-bench"]
    assert rep.skipped_board["GAIA"] == 1
    assert rep.rows["GAIA"] == 0


def test_boards_filter_keeps_only_the_named_board(reg):
    recs = [record("GAIA", "x", [{"split": "test", "model": None, "score": 1.0, "metric": "a"}]),
            record("OSWorld", "OSWorld reference agent",
                   [{"split": "Verified", "model": "GPT-4o", "score": 5.0, "metric": "b"}])]
    rows, _ = l2r.convert(recs, reg, only_boards={"osworld"})
    assert len(rows) == 1 and rows[0]["system_id"] == "osworld-reference-agent"


# --------------------------------------------------------------------------------------
# 6. the output validates against the column list validate.py enforces
# --------------------------------------------------------------------------------------


def test_columns_are_exactly_the_ones_validate_enforces():
    assert l2r.RESULT_COLUMNS == VALIDATE_COLUMNS


def test_written_rows_have_those_columns_and_numeric_scores(tmp_path, reg):
    entries = [{"split": "Lite", "model": "GPT-4o", "score": 38.0, "metric": "% resolved"}]
    rows, _ = l2r.convert([record("SWE-bench", "OpenHands", entries)], reg)
    out = tmp_path / "results_leaderboards.csv"
    l2r.write_rows(rows, out, None)
    with out.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == VALIDATE_COLUMNS
        written = list(reader)
    assert len(written) == 1
    float(written[0]["score"])
    # an attributed row must name a system that exists in the registry
    assert written[0]["system_id"] in reg.name_of


def test_append_to_an_existing_results_file_does_not_repeat_the_header(tmp_path, reg):
    target = tmp_path / "results.csv"
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(",".join(VALIDATE_COLUMNS) + "\n")
        fh.write("openhands,gpt-4o,SWE-bench,Lite,% resolved,10,,,,https://x,,from a paper\n")
    rows, _ = l2r.convert([record("SWE-bench", "OpenHands",
                                 [{"split": "Lite", "model": "GPT-4o", "score": 38.0,
                                   "metric": "% resolved"}])], reg)
    assert l2r.write_rows(rows, tmp_path / "unused.csv", target) == target
    with target.open(encoding="utf-8", newline="") as fh:
        got = list(csv.DictReader(fh))
    assert len(got) == 2
    assert got[0]["notes"] == "from a paper"
    assert not (tmp_path / "unused.csv").exists()


# --------------------------------------------------------------------------------------
# end to end through main(), no network and no model calls
# --------------------------------------------------------------------------------------


def test_cli_end_to_end(tmp_path, registry_files, capsys):
    systems, cands = registry_files
    infile = tmp_path / "leaderboards.jsonl"
    recs = [
        record("SWE-bench", "OpenHands", [
            {"split": "Verified", "model": "Claude 3.7", "score": 60.0, "metric": "% resolved",
             "raw_name": "OpenHands + Claude 3.7 Sonnet", "model_ids": ["claude-3-7-sonnet"]}]),
        record("GAIA", "0707_1", [
            {"split": "test", "model": None, "score": 1.33, "metric": "accuracy %"}]),
        record("OSWorld", "OSWorld reference agent", [
            {"split": "Verified", "model": "GPT-4o", "score": 5.0, "metric": "success rate %"},
            {"split": "Verified", "model": None, "score": None, "metric": "success rate %"}]),
    ]
    infile.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    out = tmp_path / "results_leaderboards.csv"
    argv = ["--in", str(infile), "--out", str(out), "--systems", str(systems),
            "--candidates", str(cands)]
    assert l2r.main(argv) == 0
    report = capsys.readouterr().out
    assert "attribution rate" in report and "GAIA" in report

    with out.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 3  # four entries, one without a score
    by_board = {r["benchmark"]: r for r in rows}
    assert by_board["SWE-bench"]["system_id"] == "openhands"
    assert by_board["SWE-bench"]["model"] == "claude-3-7-sonnet"
    assert by_board["GAIA"]["system_id"] == ""
    assert "unverified" in by_board["GAIA"]["notes"]
    assert by_board["OSWorld"]["system_id"] == "osworld-reference-agent"

    skipped = tmp_path / "no_gaia.csv"
    assert l2r.main(argv[:2] + ["--out", str(skipped), "--systems", str(systems),
                               "--candidates", str(cands), "--skip-boards", "GAIA"]) == 0
    with skipped.open(encoding="utf-8", newline="") as fh:
        assert "GAIA" not in {r["benchmark"] for r in csv.DictReader(fh)}
