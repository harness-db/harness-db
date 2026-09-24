"""Tests for phase-6 result extraction (``scripts/extract_results.py``): the frozen output columns,
mandatory per-row evidence (a verbatim quote that contains the row's number), the own-system check
that keeps baselines and rival systems out, normalisation that never invents, and resumability.

No network and no LLM calls: the backend is a fake injected into ``main(..., backend=...)``.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_results as er
import screen_llm
import validate as validate_script

# --------------------------------------------------------------------------------------
# fixture: one system, one paper that reports its own numbers and a baseline's
# --------------------------------------------------------------------------------------

PAPER = """record_id: test:rec1
source_used: arxiv_html
fetched_url: https://example.org/agentx
fetched_title: AgentX, a harness for repository-scale coding
fetched_at: 2026-09-19T00:00:00Z

Abstract
AgentX resolves 38.0% of SWE-bench Verified instances with GPT-4o, at an average cost of $1.42 per
instance and 412,000 tokens.

4 Results
Table 3 reports the main comparison. AgentX (ours) reaches 38.0 % resolved on SWE-bench Verified
and 24.6 % resolved on SWE-bench Lite; the leaderboard snapshot was taken in March 2025.
Ours w/o memory reaches 31.2 % resolved on SWE-bench Verified.
SWE-agent reaches 12.5 % resolved on SWE-bench Verified.
{filler}

References
[1] Somebody. A cited paper that must not reach the bundle. 2024.
"""

REPO_BUNDLE = """record_id: test:rec1
repo_url: https://github.com/acme/agentx
ref: commit:main 8248df0d247a 2026-05-09
stars: 1234
fetched_at: 2026-09-19T14:37:42Z

## README (README.md)
AgentX scores 41.0% on SWE-bench Verified on the public leaderboard.
"""

OWN = {"benchmark": "SWE-bench", "split": "Verified", "metric": "% resolved", "score": "38.0%",
       "model": "GPT-4o", "system_name": "AgentX (ours)", "cost_usd": "$1.42 per instance",
       "tokens": "412,000", "date": "March 2025", "record_id": "test:rec1",
       "evidence_quote": "AgentX (ours) reaches 38.0 % resolved on SWE-bench Verified",
       "evidence_locator": "paper Table 3", "note": "main table"}

RIVAL = {**OWN, "system_name": "SWE-agent", "score": "12.5%", "cost_usd": "", "tokens": "",
         "date": "", "note": "baseline row",
         "evidence_quote": "SWE-agent reaches 12.5 % resolved on SWE-bench Verified"}

PARAPHRASE = {**OWN, "score": "38.0", "cost_usd": "", "tokens": "", "date": "",
              "evidence_quote": "AgentX solves roughly two fifths of the tasks it is given"}

WRONG_NUMBER = {**OWN, "score": "24.6", "split": "Lite", "cost_usd": "", "tokens": "", "date": "",
                "evidence_quote": "AgentX (ours) reaches 38.0 % resolved on SWE-bench Verified"}

ABLATION = {**OWN, "system_name": "Ours w/o memory", "score": "31.2", "cost_usd": "", "tokens": "",
            "date": "", "note": "ablation without memory",
            "evidence_quote": "Ours w/o memory reaches 31.2 % resolved on SWE-bench Verified"}


class FakeBackend:
    """Stands in for ``screen_llm.vote_batch_claude_code``: records every call, invents no cost."""

    def __init__(self, rows=(OWN,), reason=""):
        self.calls: list[dict] = []
        self.rows = list(rows)
        self.reason = reason

    def __call__(self, exe, model, system_file, batch, effort=None, schema=None, prompt=None,
                 text_json=False):
        text = prompt(batch)
        self.calls.append({"system_id": batch[0]["id"], "prompt": text, "schema": schema,
                           "document": batch[0]["document"], "system": system_file.read_text(encoding="utf-8")})
        votes = [{"record_id": it["id"], "results": self.rows, "no_results_reason": self.reason}
                 for it in batch]
        return screen_llm.BatchResult(votes, "claude-opus-fake", 12_000, 800, 0, 0, 0.35)


def write_inputs(tmp_path: Path, filler: int = 50, repo: bool = False) -> None:
    """A one-system frame plus the fetched evidence on disk, in the real file layout."""
    ft = tmp_path / "fulltext"
    ft.mkdir(exist_ok=True)
    (ft / "test__rec1.txt").write_text(PAPER.format(filler="lorem ipsum dolor " * filler),
                                       encoding="utf-8")
    if repo:
        (ft / "test__rec1__repo.txt").write_text(REPO_BUNDLE, encoding="utf-8")
    frame = tmp_path / "coding_frame.csv"
    with frame.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["system_id", "name", "version", "repo_url", "stars",
                                           "stratum", "coded", "weight", "codability_flag",
                                           "max_codable_count", "canonical_record_id",
                                           "member_record_ids"])
        w.writeheader()
        w.writerow({"system_id": "agentx", "name": "AgentX", "version": "v1", "stars": "1234",
                    "repo_url": "https://github.com/acme/agentx", "stratum": "H", "coded": "1",
                    "weight": "1.0", "codability_flag": "pass", "max_codable_count": "30",
                    "canonical_record_id": "test:rec1", "member_record_ids": "test:rec1"})
        w.writerow({"system_id": "ghost", "name": "Ghost", "version": "", "stars": "3",
                    "repo_url": "", "stratum": "L", "coded": "1", "weight": "1.0",
                    "codability_flag": "pass", "max_codable_count": "12",
                    "canonical_record_id": "test:nofile", "member_record_ids": "test:nofile"})
    (tmp_path / "systems.json").write_text(json.dumps(
        [{"id": "agentx", "name": "AgentX (repository agent)", "aliases": ["AgentX Coder"],
          "papers": ["test:rec1"]}]), encoding="utf-8")
    with (tmp_path / "papers.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "title", "authors", "year", "venue", "arxiv_id",
                                           "doi", "url", "source", "included", "exclusion_reason"])
        w.writeheader()
        w.writerow({"id": "test:rec1", "title": "AgentX", "year": "2025",
                    "url": "https://example.org/agentx", "source": "arxiv", "included": "1"})


def run(tmp_path: Path, backend, *extra: str) -> int:
    argv = ["--frame", str(tmp_path / "coding_frame.csv"),
            "--fulltext-dir", str(tmp_path / "fulltext"),
            "--out-dir", str(tmp_path / "out"),
            "--systems", str(tmp_path / "systems.json"),
            "--papers", str(tmp_path / "papers.csv"),
            "--ids", "agentx", "--workers", "1", *extra]
    return er.main(argv, backend=backend)


def out(tmp_path: Path, name: str) -> list[dict[str, str]]:
    return er.cs.read_csv(tmp_path / "out" / name)


def summary(capsys) -> dict:
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("SUMMARY ")]
    assert lines, "no SUMMARY line"
    return json.loads(lines[-1][len("SUMMARY "):])


# --------------------------------------------------------------------------------------
# the output contract
# --------------------------------------------------------------------------------------


def test_columns_are_the_frozen_ones():
    assert er.RESULT_COLUMNS == validate_script.RESULT_COLUMNS


def test_good_row_is_written_with_its_evidence(tmp_path, capsys):
    write_inputs(tmp_path)
    be = FakeBackend()
    assert run(tmp_path, be) == 0
    rows = out(tmp_path, "results.csv")
    assert len(rows) == 1
    r = rows[0]
    assert list(r) == er.RESULT_COLUMNS
    assert r["system_id"] == "agentx" and r["benchmark"] == "SWE-bench" and r["split"] == "Verified"
    assert r["metric"] == "% resolved" and r["model"] == "GPT-4o"
    assert r["score"] == "38.0" and float(r["score"]) == 38.0        # validate.py parses it
    assert r["cost_usd"] == "1.42" and r["tokens"] == "412000" and r["date"] == "2025-03"
    assert r["source_url"] == "https://example.org/agentx"
    assert r["comparable_key"] == ""                                  # filled by a separate script
    assert "row_id=agentx#01" in r["notes"] and "main table" in r["notes"]

    ev = out(tmp_path, "results_evidence.csv")
    assert len(ev) == 1 and ev[0]["row_id"] == "agentx#01"
    assert ev[0]["evidence_quote"] == OWN["evidence_quote"]
    assert ev[0]["evidence_locator"] == "paper Table 3"
    assert ev[0]["quote_verbatim"] == "1" and ev[0]["score_in_quote"] == "1"
    assert ev[0]["record_id"] == "test:rec1" and ev[0]["score_raw"] == "38.0%"
    assert not (tmp_path / "out" / "results_rejects.csv").exists()   # nothing was refused

    s = summary(capsys)
    assert s["rows_extracted"] == 1 and s["rows_rejected"] == 0 and s["systems_extracted_now"] == 1
    assert s["systems_no_results"] == 0 and s["cost_usd"] == 0.35
    assert (tmp_path / "out" / "results_extract.log").exists()


def test_the_prompt_names_the_system_and_carries_the_paper(tmp_path):
    write_inputs(tmp_path)
    be = FakeBackend()
    run(tmp_path, be)
    call = be.calls[0]
    assert "AgentX" in call["prompt"] and "AgentX Coder" in call["prompt"]   # frame + registry aliases
    assert "AgentX (ours) reaches 38.0 % resolved" in call["document"]
    assert "must not reach the bundle" not in call["document"]              # references stripped
    assert "REPOSITORY EVIDENCE" not in call["document"]                    # papers only by default
    assert "ONLY THIS SYSTEM'S OWN RESULTS" in call["system"]
    props = call["schema"]["properties"]["votes"]["items"]["properties"]["results"]["items"]
    assert "system_name" in props["properties"] and "system_name" in props["required"]


# --------------------------------------------------------------------------------------
# evidence is mandatory
# --------------------------------------------------------------------------------------


def test_quote_that_is_not_in_the_text_is_rejected(tmp_path, capsys):
    write_inputs(tmp_path)
    assert run(tmp_path, FakeBackend([PARAPHRASE])) == 0
    assert out(tmp_path, "results.csv") == []
    rej = out(tmp_path, "results_rejects.csv")
    assert len(rej) == 1 and rej[0]["reason"] == "quote_not_in_bundle"
    assert rej[0]["quote_verbatim"] == "0" and rej[0]["score"] == "38.0"   # kept for the audit
    s = summary(capsys)
    assert s["rows_rejected"] == 1 and s["reject_reasons"] == {"quote_not_in_bundle": 1}
    assert s["systems_no_results"] == 1


def test_number_that_is_not_in_its_quote_is_rejected(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([WRONG_NUMBER]))
    assert out(tmp_path, "results.csv") == []
    assert out(tmp_path, "results_rejects.csv")[0]["reason"] == "score_not_in_quote"


def test_whitespace_and_case_differences_are_still_verbatim(tmp_path):
    loose = {**OWN, "evidence_quote": "agentx (OURS)  reaches 38.0 %   resolved"}
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([loose]))
    assert len(out(tmp_path, "results.csv")) == 1


def test_row_without_a_score_or_a_benchmark_is_rejected(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([{**OWN, "score": "best"}, {**OWN, "benchmark": ""},
                               {**OWN, "evidence_quote": ""}]))
    assert out(tmp_path, "results.csv") == []
    assert [r["reason"] for r in out(tmp_path, "results_rejects.csv")] == [
        "bad_score", "missing_benchmark", "missing_quote"]


# --------------------------------------------------------------------------------------
# only the system's own results
# --------------------------------------------------------------------------------------


def test_row_naming_another_system_is_rejected(tmp_path, capsys):
    write_inputs(tmp_path)
    assert run(tmp_path, FakeBackend([OWN, RIVAL])) == 0
    rows = out(tmp_path, "results.csv")
    assert len(rows) == 1 and rows[0]["score"] == "38.0"
    rej = out(tmp_path, "results_rejects.csv")
    assert len(rej) == 1
    assert rej[0]["reason"] == "not_own_system" and rej[0]["reported_system_name"] == "SWE-agent"
    assert summary(capsys)["reject_reasons"] == {"not_own_system": 1}


def test_row_that_does_not_say_whose_it_is_is_rejected(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([{**OWN, "system_name": ""}]))
    assert out(tmp_path, "results.csv") == []
    assert out(tmp_path, "results_rejects.csv")[0]["reason"] == "own_system_unstated"


def test_no_only_own_keeps_the_rival_row(tmp_path):
    """The check is a choice, and turning it off must be visible in the summary, not silent."""
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([OWN, RIVAL]), "--no-only-own")
    assert len(out(tmp_path, "results.csv")) == 2


def test_an_ablation_of_the_system_is_its_own_result(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([ABLATION]))
    rows = out(tmp_path, "results.csv")
    assert len(rows) == 1 and rows[0]["score"] == "31.2"
    assert "ablation without memory" in rows[0]["notes"]


def test_own_system_matching_is_token_wise_not_substring_wise():
    aliases = er.system_aliases({"system_id": "ace", "name": "ACE (Actor-Critic Embodied Agent)",
                                 "repo_url": "https://github.com/x/ace-llm"},
                                {"name": "ACE", "aliases": ["ACE (Agentic Context Engineering)"]})
    assert er.own_system_reason("ACE", aliases) == ""
    assert er.own_system_reason("ACE v2", aliases) == ""
    assert er.own_system_reason("Ours", aliases) == ""
    assert er.own_system_reason("ACENet", aliases) == "not_own_system"
    assert er.own_system_reason("GPT-4 + ReAct", aliases) == "not_own_system"
    assert er.own_system_reason("", aliases) == "own_system_unstated"
    # a name spelled with different punctuation is the same name
    assert er.own_system_reason("Open Hands", er.system_aliases({"system_id": "openhands",
                                                                 "name": "OpenHands"})) == ""


def test_generic_and_too_short_aliases_are_dropped():
    aliases = er.system_aliases({"system_id": "ag", "name": "Agent", "repo_url": ""})
    assert aliases == [] and er.own_system_reason("Agent Lumos", aliases) == "not_own_system"


# --------------------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------------------


def test_percentage_normalisation():
    assert er.normalise_score("38%") == ("38", 38.0, ["pct_sign_stripped"])
    assert er.normalise_score("38.0 %")[0] == "38.0"          # the paper's digits are kept
    assert er.normalise_score(38.0)[0] == "38.0"
    assert er.normalise_score("0.71") == ("0.71", 0.71, [])
    assert er.normalise_score("41.2 ± 0.8%")[0] == "41.2"     # the mean, not the error bar
    assert er.normalise_score("~38%")[0] == "38"
    assert er.normalise_score("38-41") == ("", None, ["bad_score"])
    assert er.normalise_score("best") == ("", None, ["bad_score"])
    assert er.normalise_score("") == ("", None, ["missing_score"])


def test_date_normalisation():
    assert er.normalise_date("2025-03-14") == ("2025-03-14", [])
    assert er.normalise_date("March 2025") == ("2025-03", [])
    assert er.normalise_date("Feb 13, 2025") == ("2025-02-13", [])
    assert er.normalise_date("13 February 2025") == ("2025-02-13", [])
    assert er.normalise_date("2025/03") == ("2025-03", [])
    assert er.normalise_date("spring") == ("", ["date_dropped"])
    assert er.normalise_date("") == ("", [])


def test_cost_and_token_normalisation():
    assert er.normalise_cost("$1.42 per instance") == ("1.42", [])
    assert er.normalise_cost("about $0.35") == ("0.35", [])
    assert er.normalise_cost("cheap") == ("", ["cost_dropped"])
    assert er.normalise_cost("") == ("", [])
    assert er.normalise_int("412,000 tokens", "tokens") == ("412000", [])
    assert er.normalise_int("1.2M", "tokens") == ("1200000", ["tokens_expanded"])
    assert er.normalise_int("a few", "tokens") == ("", ["tokens_dropped"])
    assert er.normalise_int("", "tokens") == ("", [])


def test_a_dropped_field_is_empty_and_flagged_but_the_row_survives(tmp_path):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([{**OWN, "date": "sometime in spring", "tokens": "many"}]))
    r = out(tmp_path, "results.csv")[0]
    assert r["date"] == "" and r["tokens"] == "" and r["score"] == "38.0"
    flags = out(tmp_path, "results_evidence.csv")[0]["flags"].split(";")
    assert "date_dropped" in flags and "tokens_dropped" in flags


def test_two_splits_are_two_rows_and_a_repeat_is_refused(tmp_path):
    lite = {**OWN, "split": "Lite", "score": "24.6", "cost_usd": "", "tokens": "", "date": "",
            "evidence_quote": "and 24.6 % resolved on SWE-bench Lite"}
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([OWN, lite, OWN]))
    rows = out(tmp_path, "results.csv")
    assert [r["split"] for r in rows] == ["Verified", "Lite"]
    assert {r["notes"].split(";")[0] for r in rows} == {"row_id=agentx#01", "row_id=agentx#02"}
    assert out(tmp_path, "results_rejects.csv")[0]["reason"] == "duplicate_row"


# --------------------------------------------------------------------------------------
# resumability and cost
# --------------------------------------------------------------------------------------


def test_second_run_makes_no_backend_calls(tmp_path, capsys):
    write_inputs(tmp_path)
    first = FakeBackend()
    run(tmp_path, first)
    capsys.readouterr()
    second = FakeBackend()
    assert run(tmp_path, second) == 0
    assert second.calls == []                                   # nothing was re-sent
    assert len(out(tmp_path, "results.csv")) == 1                # and nothing was duplicated
    s = summary(capsys)
    assert s["systems_extracted_now"] == 0 and s["cost_usd"] == 0.0


def test_a_system_with_no_results_is_not_re_asked(tmp_path, capsys):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([], reason="the paper reports no benchmark results"))
    assert out(tmp_path, "results.csv") == []
    st = out(tmp_path, "results_extract_status.csv")
    assert len(st) == 1 and st[0]["rows"] == "0" and st[0]["no_results"] == "1"
    assert st[0]["no_results_reason"] == "the paper reports no benchmark results"
    capsys.readouterr()
    again = FakeBackend()
    run(tmp_path, again)
    assert again.calls == []


def test_a_system_without_full_text_is_ledgered_not_retried(tmp_path, capsys):
    write_inputs(tmp_path)
    be = FakeBackend()
    er.main(["--frame", str(tmp_path / "coding_frame.csv"),
             "--fulltext-dir", str(tmp_path / "fulltext"), "--out-dir", str(tmp_path / "out"),
             "--systems", str(tmp_path / "systems.json"), "--papers", str(tmp_path / "papers.csv"),
             "--ids", "ghost", "--workers", "1"], backend=be)
    assert be.calls == []
    st = out(tmp_path, "results_extract_status.csv")
    assert len(st) == 1 and st[0]["system_id"] == "ghost"
    assert st[0]["no_results_reason"] == "no fetched full text on disk"
    s = summary(capsys)
    assert s["systems_without_fulltext"] == 1


def test_redo_drops_the_system_and_extracts_it_again(tmp_path, capsys):
    write_inputs(tmp_path)
    run(tmp_path, FakeBackend([OWN, RIVAL]))
    capsys.readouterr()
    again = FakeBackend([ABLATION])
    assert run(tmp_path, again, "--redo", "agentx") == 0
    assert len(again.calls) == 1
    rows = out(tmp_path, "results.csv")
    assert len(rows) == 1 and rows[0]["score"] == "31.2"        # the old row is gone, not doubled
    assert len(out(tmp_path, "results_evidence.csv")) == 1
    assert out(tmp_path, "results_rejects.csv") == []          # and so is the old rejection
    assert len(out(tmp_path, "results_extract_status.csv")) == 1


def test_limit_and_measure_do_not_call_the_model(tmp_path, capsys):
    write_inputs(tmp_path)
    rc = er.main(["--frame", str(tmp_path / "coding_frame.csv"),
                  "--fulltext-dir", str(tmp_path / "fulltext"), "--out-dir", str(tmp_path / "out"),
                  "--systems", str(tmp_path / "systems.json"), "--measure", "1"],
                 backend=FakeBackend())
    assert rc == 0
    line = [ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("MEASURE ")][-1]
    m = json.loads(line[len("MEASURE "):])
    assert m["n"] == 1 and m["prompt_chars_median"] > 500 and m["system_prompt_chars"] > 500
    assert not (tmp_path / "out").exists()                      # a read-only exit writes nothing


# --------------------------------------------------------------------------------------
# bundle
# --------------------------------------------------------------------------------------


def test_bundle_is_papers_only_unless_repo_share_is_raised(tmp_path):
    write_inputs(tmp_path, repo=True)
    row = er.cs.frame_rows(tmp_path / "coding_frame.csv")[0]
    papers_only = er.assemble_bundle(row, root=tmp_path / "fulltext")
    assert "REPOSITORY EVIDENCE" not in papers_only.text and "[TRUNCATED:" not in papers_only.text
    assert {p["kind"] for p in papers_only.parts} == {"paper"}
    with_repo = er.assemble_bundle(row, repo_share=0.4, root=tmp_path / "fulltext")
    assert "AgentX scores 41.0% on SWE-bench Verified" in with_repo.text


def test_bundle_records_what_was_truncated(tmp_path):
    write_inputs(tmp_path, filler=3000)
    row = er.cs.frame_rows(tmp_path / "coding_frame.csv")[0]
    b = er.assemble_bundle(row, cap=4000, root=tmp_path / "fulltext")
    assert b.chars <= 4000 and b.truncated and "[TRUNCATED:" in b.text
    assert b.parts[0]["chars_used"] < b.parts[0]["chars_available"]
