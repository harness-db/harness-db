"""Tests for scripts/mark_comparable.py (Phase 6 task 45).

What is worth testing here is not that the script runs but that its two dangerous decisions are
right: that canonicalisation collapses only what is genuinely the same thing, and that every
reason for refusing a key actually fires. A false collapse pools two different measurements and
invents a comparison; a false split hides one. Both are silent in the output, so they are tested
explicitly.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mark_comparable import (  # noqa: E402
    RESULT_COLUMNS,
    canon_benchmark,
    canon_metric,
    canon_model,
    canon_split,
    evaluate_row,
    mark_rows,
    read_results,
    write_results,
)


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------
def row(**over) -> dict[str, str]:
    """A row that is comparable in every respect, so a test can break exactly one thing."""
    base = {
        "system_id": "swe-agent",
        "model": "gpt-4o-2024-05-13",
        "benchmark": "SWE-bench",
        "split": "Verified",
        "metric": "% resolved",
        "score": "33.6",
        "cost_usd": "1.50",
        "tokens": "120000",
        "date": "2024-08-01",
        "source_url": "https://www.swebench.com/",
        "comparable_key": "",
        "notes": "",
    }
    base.update(over)
    return base


def key_of(**over) -> str:
    return evaluate_row(row(**over))[0]


def reasons_of(**over) -> list[str]:
    return evaluate_row(row(**over))[1]


# --------------------------------------------------------------------------------------
# model canonicalisation: collapse snapshots, never collapse generations
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("variants", [
    ["gpt-4o-2024-05-13", "GPT-4o", "gpt-4o", "openai/gpt-4o", "GPT-4o (2024-08-06)",
     "gpt-4o-2024-11-20", "  gpt-4o  "],
    ["claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet", "claude-3.5-sonnet",
     "anthropic/claude-3-5-sonnet-20240620", "claude-sonnet-3.5"],
    ["claude-sonnet-4-5-20250929", "Claude Sonnet 4.5", "claude-sonnet-4.5",
     "us.anthropic.claude-sonnet-4-5-20250929-v1:0"],
    ["gpt-4-0613", "gpt-4", "GPT-4", "gpt-4-1106"],
    ["gemini-2.5-pro", "Gemini 2.5 Pro", "GEMINI-2.5-PRO", "google/gemini-2.5-pro"],
    # yearless vendor snapshot suffixes (Google, OpenAI) are dates, not versions
    ["gemini-2.5-pro-preview-05-06", "gemini-2.5-pro-preview-03-25",
     "Gemini 2.5 Pro Preview"],
])
def test_vendor_date_suffixes_collapse_to_one_base_model(variants):
    canon = {canon_model(v)[0] for v in variants}
    assert len(canon) == 1, f"{variants} -> {canon}"
    assert None not in canon


def test_preview_checkpoints_stay_distinct_from_the_released_model():
    # o1-preview and o1, gpt-4-turbo-preview and gpt-4-turbo, gemini preview and GA all
    # reported different scores. Keeping them apart splits a key a reader might have pooled,
    # which is the safe direction to be wrong in.
    assert canon_model("gemini-2.5-pro-preview-05-06")[0] != canon_model("gemini-2.5-pro")[0]
    assert canon_model("o1-preview")[0] != canon_model("o1")[0]


@pytest.mark.parametrize("a,b", [
    # generations and point releases are different models and must not collapse
    ("claude-sonnet-5", "claude-sonnet-4-6"),
    ("claude-sonnet-4-6", "claude-sonnet-4-5"),
    ("claude-sonnet-4-6", "claude-sonnet-4"),
    ("claude-3-5-sonnet", "claude-3-7-sonnet"),
    ("claude-sonnet-4-5", "claude-opus-4-5"),
    ("gpt-4o", "gpt-4"),
    ("gpt-4o", "gpt-4o-mini"),
    ("gpt-5", "gpt-5.1"),
    ("o1", "o1-preview"),          # different models with different reported scores
    ("o1", "o3"),
    ("gemini-2.5-pro", "gemini-3-pro"),
    ("llama-3.1-405b-instruct", "llama-3.1-70b-instruct"),
])
def test_model_generations_do_not_collapse(a, b):
    assert canon_model(a)[0] != canon_model(b)[0]


def test_moe_parameter_notation_is_not_two_models():
    # "480B/A35B" is total/active parameters of one MoE model; the slash must not read as "or"
    assert canon_model("Qwen3-Coder 480B/A35B Instruct")[1] is None
    assert canon_model("gpt-4o/claude-sonnet-4")[1] == "model_unidentifiable"


def test_two_spellings_of_one_model_produce_one_key():
    assert key_of(model="gpt-4o-2024-05-13") == key_of(model="GPT-4o")
    assert key_of(model="claude-sonnet-4-6") != key_of(model="claude-sonnet-5")


# --------------------------------------------------------------------------------------
# benchmark and split canonicalisation
# --------------------------------------------------------------------------------------
def test_benchmark_names_are_case_and_punctuation_insensitive():
    for spelling in ("SWE-bench", "swebench", "SWE_Bench", "swe bench", "SWE-Bench"):
        assert canon_benchmark(spelling)[0] == "SWE-bench"


def test_qualified_benchmark_name_resolves_into_the_split():
    # the same measurement written both ways must land on one key
    assert key_of(benchmark="SWE-bench Verified", split="") == \
           key_of(benchmark="SWE-bench", split="Verified")
    assert key_of(benchmark="SWE-bench Lite", split="") == \
           key_of(benchmark="SWE-bench", split="lite")


def test_swe_bench_test_split_folds_to_full_but_gaia_test_does_not():
    assert canon_split("SWE-bench", "test") == "full"
    assert canon_split("GAIA", "test") == "test"
    assert canon_split("GAIA", "validation") == "val"


def test_swe_bench_versions_are_different_keys():
    keys = {key_of(split=s) for s in ("Verified", "Lite", "test", "Multimodal")}
    assert len(keys) == 4


def test_unrecognised_benchmark_and_split_blank_the_row():
    assert reasons_of(benchmark="MysteryBench") == ["benchmark_unrecognised"]
    assert reasons_of(split="first 100 instances") == ["split_unrecognised"]


def test_qualified_benchmark_contradicting_the_split_is_a_conflict():
    assert reasons_of(benchmark="SWE-bench Verified", split="Lite") == \
           ["benchmark_split_conflict"]
    assert reasons_of(benchmark="SWE-bench Lite", split="Multimodal") == \
           ["benchmark_split_conflict"]


def test_a_vacuous_split_defers_to_the_qualifier_instead_of_conflicting():
    # "SWE-bench Verified" + split "test" is the HuggingFace split name of the Verified set,
    # not a claim about the 2,294-instance full set, so it keys as Verified.
    assert key_of(benchmark="SWE-bench Verified", split="test") == \
           key_of(benchmark="SWE-bench", split="Verified")
    assert key_of(benchmark="SWE-bench Verified", split="all") == \
           key_of(benchmark="SWE-bench", split="Verified")


def test_a_leaderboard_name_in_the_benchmark_column_is_resolved_from_the_split():
    # HAL runs nine benchmarks; the harvest records family="HAL" and the benchmark in the split
    assert key_of(benchmark="HAL", split="corebench_hard", metric="accuracy %") == \
           "CORE-Bench|hard|gpt-4o"
    # ... and HAL's SWE-bench rows still fail the metric test, which is the documented cost of
    # refusing to read "accuracy" as "% resolved" on SWE-bench
    assert reasons_of(benchmark="HAL", split="swebench_verified_mini",
                      metric="accuracy %") == ["metric_nonstandard"]


def test_a_benchmark_name_in_the_split_column_is_reported_as_a_conflict():
    # the WebArena board family carries VisualWebArena rows with the benchmark in the split
    assert reasons_of(benchmark="WebArena", split="VisualWebArena",
                      metric="success rate %") == ["benchmark_split_conflict"]


def test_board_split_strings_from_the_real_harvest_resolve():
    # strings taken verbatim from data/raw/leaderboards.jsonl
    assert canon_split("Terminal-Bench", "Terminal-Bench 1.0 (terminal-bench-core@0.1.1)") == \
           canon_split("Terminal-Bench", "Terminal-Bench 1.0 (terminal-bench-core:0.1.1)")
    assert canon_split("Terminal-Bench", "Terminal-Bench 4.0") == "core@4.0"
    assert canon_split("OSWorld", "self-reported/Screenshot_A11y_tree") == \
           "self-reported/screenshot+a11y"
    assert canon_split("tau2-bench", "voice/telecom") == "voice/telecom"
    assert canon_split("tau2-bench", "text-legacy/airline") == "text-legacy/airline"


def test_modality_and_dataset_version_are_part_of_the_split():
    # voice is not text, and Terminal-Bench 1.0 is not 4.0: these must never pool
    assert canon_split("tau2-bench", "voice/airline") != canon_split("tau2-bench", "text/airline")
    assert canon_split("Terminal-Bench", "Terminal-Bench 1.0") != \
           canon_split("Terminal-Bench", "Terminal-Bench 4.0")
    assert canon_split("OSWorld", "Verified") != canon_split("OSWorld", "self-reported/A11y_tree")


def test_tau_bench_domains_and_generations_stay_apart():
    assert canon_benchmark("τ-bench")[0] == "tau-bench"
    assert canon_benchmark("τ2-bench")[0] == "tau2-bench"
    k1 = key_of(benchmark="tau-bench", split="airline", metric="pass^1 %")
    k2 = key_of(benchmark="tau-bench", split="retail", metric="pass^1 %")
    k3 = key_of(benchmark="tau2-bench", split="airline", metric="pass^1 %")
    assert k1 and k2 and k3
    assert len({k1, k2, k3}) == 3


# --------------------------------------------------------------------------------------
# metric: board vocabulary collapses, different measurements do not
# --------------------------------------------------------------------------------------
def test_board_wording_for_one_computation_collapses():
    assert canon_metric("OSWorld", "success rate %") == canon_metric("OSWorld", "accuracy")
    assert canon_metric("Terminal-Bench", "accuracy % (mean of runs)") == \
           canon_metric("Terminal-Bench", "success rate")
    assert canon_metric("SWE-bench", "% resolved") == canon_metric("SWE-bench", "resolve rate")


def test_accuracy_on_swe_bench_is_not_percent_resolved():
    assert canon_metric("SWE-bench", "accuracy") != canon_metric("SWE-bench", "% resolved")
    assert reasons_of(metric="accuracy") == ["metric_nonstandard"]
    assert key_of(metric="% resolved")


def test_pass_at_1_and_pass_hat_1_are_different_estimators():
    assert canon_metric("tau-bench", "pass@1") != canon_metric("tau-bench", "pass^1")
    assert reasons_of(benchmark="tau-bench", split="airline", metric="pass@1") == \
           ["metric_nonstandard"]


# --------------------------------------------------------------------------------------
# every blanking reason fires
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("reason,over", [
    ("system_id_missing", {"system_id": ""}),
    ("system_id_missing", {"system_id": "   "}),
    ("model_missing", {"model": ""}),
    ("model_unidentifiable", {"model": "various"}),
    ("model_unidentifiable", {"model": "n/a"}),
    ("model_unidentifiable", {"model": "gpt-4o + claude-sonnet-4"}),
    ("model_unidentifiable", {"model": "gpt-4o/claude-sonnet-4"}),
    ("benchmark_unrecognised", {"benchmark": "SomeNewBench"}),
    ("benchmark_unrecognised", {"benchmark": ""}),
    ("split_missing", {"split": ""}),
    ("split_missing", {"split": "  "}),
    ("split_unrecognised", {"split": "subset of 50"}),
    ("benchmark_split_conflict", {"benchmark": "SWE-bench Lite", "split": "Verified"}),
    ("metric_missing", {"metric": ""}),
    ("metric_nonstandard", {"metric": "accuracy"}),
    ("metric_nonstandard", {"metric": "files localised"}),
    ("score_missing", {"score": ""}),
    ("score_not_numeric", {"score": "~40"}),
    ("score_not_numeric", {"score": "n/a"}),
    ("score_not_numeric", {"score": "nan"}),
])
def test_each_blanking_reason_triggers(reason, over):
    key, reasons = evaluate_row(row(**over))
    assert key == ""
    assert reason in reasons, f"{over} -> {reasons}"


def test_a_clean_row_is_keyed_with_no_reason():
    key, reasons = evaluate_row(row())
    assert reasons == []
    assert key == "SWE-bench|Verified|gpt-4o"


def test_reasons_accumulate_and_are_ordered_by_precedence():
    key, reasons = evaluate_row(row(system_id="", split="", score=""))
    assert key == ""
    assert reasons == ["system_id_missing", "split_missing", "score_missing"]


def test_blanked_row_records_its_reasons_in_notes_without_losing_existing_notes():
    rows = [row(system_id="", notes="score read from Table 3")]
    mark_rows(rows)
    assert rows[0]["comparable_key"] == ""
    assert "score read from Table 3" in rows[0]["notes"]
    assert "[not-comparable: system_id_missing]" in rows[0]["notes"]


def test_rerunning_does_not_duplicate_the_note_and_clears_it_when_fixed():
    rows = [row(system_id="", notes="from the paper")]
    mark_rows(rows)
    mark_rows(rows)
    assert rows[0]["notes"].count("[not-comparable:") == 1
    rows[0]["system_id"] = "swe-agent"
    mark_rows(rows)
    assert rows[0]["notes"] == "from the paper"
    assert rows[0]["comparable_key"] == "SWE-bench|Verified|gpt-4o"


def test_percent_sign_on_the_score_is_tolerated():
    assert evaluate_row(row(score="33.6%"))[1] == []


# --------------------------------------------------------------------------------------
# --min-systems
# --------------------------------------------------------------------------------------
def two_system_rows() -> list[dict[str, str]]:
    return [
        row(system_id="swe-agent"),
        row(system_id="agentless"),
        row(system_id="openhands", split="Lite"),        # singleton key
    ]


def test_singletons_are_visible_by_default():
    rows = two_system_rows()
    summary = mark_rows(rows, min_systems=1)
    assert summary["rows_keyed"] == 3
    assert summary["key_system_distribution"] == {"1": 1, "2": 1, "3+": 0}
    assert summary["rows_in_keys_with_2plus_systems"] == 2
    assert rows[2]["comparable_key"] == "SWE-bench|Lite|gpt-4o"


def test_min_systems_2_blanks_singleton_keys():
    rows = two_system_rows()
    summary = mark_rows(rows, min_systems=2)
    assert rows[0]["comparable_key"] == "SWE-bench|Verified|gpt-4o"
    assert rows[1]["comparable_key"] == "SWE-bench|Verified|gpt-4o"
    assert rows[2]["comparable_key"] == ""
    assert "[not-comparable: singleton_key]" in rows[2]["notes"]
    assert summary["rows_keyed"] == 2
    assert summary["keys_dropped_by_min_systems"] == 1
    # the distribution still reports the diagnosis, not the result of the filter
    assert summary["key_system_distribution"] == {"1": 1, "2": 1, "3+": 0}


def test_two_rows_from_one_system_are_not_a_comparison():
    rows = [row(system_id="swe-agent"), row(system_id="swe-agent", model="GPT-4o")]
    summary = mark_rows(rows, min_systems=2)
    assert summary["rows_keyed"] == 0
    assert summary["key_system_distribution"] == {"1": 1, "2": 0, "3+": 0}


def test_surviving_benchmarks_are_reported():
    rows = two_system_rows() + [
        row(system_id="os-copilot", benchmark="OSWorld", split="Verified",
            metric="success rate %", score="10.2"),
        row(system_id="agent-s2", benchmark="OSWorld", split="Verified",
            metric="success rate %", score="27.0"),
    ]
    summary = mark_rows(rows, min_systems=2)
    assert set(summary["benchmarks_surviving"]) == {"SWE-bench", "OSWorld"}
    assert summary["benchmarks_surviving"]["OSWorld"]["multi_system_keys"] == 1


# --------------------------------------------------------------------------------------
# CSV round trip and the CLI
# --------------------------------------------------------------------------------------
def test_keyed_row_round_trips_through_the_csv_with_columns_intact(tmp_path):
    src = tmp_path / "results.csv"
    original = [row(system_id="swe-agent", notes="Table 3"),
                row(system_id="agentless", notes=""),
                row(system_id="", model="various", split="", score="x")]
    write_results(src, original)
    back = read_results(src)
    assert [c for c in csv.DictReader(src.open(encoding="utf-8")).fieldnames] == RESULT_COLUMNS

    mark_rows(back, min_systems=1)
    out = tmp_path / "out.csv"
    write_results(out, back)
    final = read_results(out)

    assert len(final) == 3
    assert list(final[0]) == RESULT_COLUMNS
    assert final[0]["comparable_key"] == "SWE-bench|Verified|gpt-4o"
    assert final[0]["notes"] == "Table 3"
    # every other field survives untouched
    for col in RESULT_COLUMNS:
        if col not in ("comparable_key", "notes"):
            assert final[0][col] == original[0][col]
    assert final[2]["comparable_key"] == ""
    assert "not-comparable" in final[2]["notes"]


def test_read_results_rejects_a_wrong_header(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("system_id,model,score\na,b,1\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        read_results(bad)


def test_cli_writes_csv_summary_and_backup(tmp_path):
    src = tmp_path / "results.csv"
    write_results(src, [row(system_id="swe-agent"), row(system_id="agentless"),
                        row(system_id="", model="")])
    summary = tmp_path / "comparable_summary.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "mark_comparable.py"),
         "--in", str(src), "--summary", str(summary), "--min-systems", "2"],
        capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "results.csv.bak").exists()

    s = json.loads(summary.read_text(encoding="utf-8"))
    assert s["rows_in"] == 3
    assert s["rows_keyed"] == 2
    assert s["rows_blank"] == 1
    assert s["min_systems"] == 2
    assert s["blanked_by_primary_reason"]["system_id_missing"] == 1
    assert "rows in" in proc.stdout

    rows = read_results(src)
    assert [r["comparable_key"] for r in rows] == \
        ["SWE-bench|Verified|gpt-4o", "SWE-bench|Verified|gpt-4o", ""]


def test_cli_dry_run_writes_nothing(tmp_path):
    src = tmp_path / "results.csv"
    write_results(src, [row(system_id="swe-agent")])
    before = src.read_text(encoding="utf-8")
    summary = tmp_path / "s.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "mark_comparable.py"),
         "--in", str(src), "--summary", str(summary), "--dry-run"],
        capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert src.read_text(encoding="utf-8") == before
    assert not summary.exists()
    assert not (tmp_path / "results.csv.bak").exists()


# --------------------------------------------------------------------------------------
# the real data file, if it has rows
# --------------------------------------------------------------------------------------
def test_repo_results_csv_has_the_expected_header():
    rows = read_results(ROOT / "data" / "results.csv")
    assert all(list(r) == RESULT_COLUMNS for r in rows)
