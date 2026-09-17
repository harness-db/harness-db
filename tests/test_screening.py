"""Fixture tests for the title/abstract triage (scripts/screen_triage.py) and merge (scripts/screen_merge.py)."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import screen_merge as sm
import screen_triage as st

VOTE_COLS = ["record_id", "vote", "reason", "decision_step", "model"]


def cand(rid, title="A named agent that loops over tools", abstract="We present AgentX, which calls tools in a loop.",
         year="2025", source="arxiv", arxiv_id=""):
    return {"id": rid, "title": title, "abstract": abstract, "year": year, "venue": "", "url": f"https://x/{rid}",
            "source": source, "sources_all": source, "arxiv_id": arxiv_id, "doi": ""}


def vote(rid, v, reason="", step="none", model="claude-opus-5"):
    return {"record_id": rid, "vote": v, "reason": reason, "decision_step": step, "model": model}


def run(cands, v1, v2):
    return st.assign_tiers(pd.DataFrame(cands), pd.DataFrame(v1, columns=VOTE_COLS), pd.DataFrame(v2, columns=VOTE_COLS)).set_index("record_id")


# ---------------------------------------------------------------- T0 hard rules

@pytest.mark.parametrize("kw,rule", [
    ({"title": ""}, "empty_title"),
    ({"year": "2019"}, "date_year_before_window"),
    ({"year": "2027"}, "date_year_after_window"),
    ({"arxiv_id": "2203.01234"}, "date_arxiv_before_window"),
    ({"source": "leaderboard", "title": "gpt-realtime-2 (Sierra)", "abstract": ""}, "leaderboard_bare_model_name"),
    ({"source": "leaderboard", "title": "Claude 3.5 Sonnet", "abstract": ""}, "leaderboard_bare_model_name"),
    ({"title": "การพัฒนาแชทบอท", "abstract": "ภาษาไทยทั้งหมด"}, "non_english_text"),
])
def test_t0_rules_fire(kw, rule):
    assert st.t0_rule(pd.Series(cand("r", **kw))) == rule


@pytest.mark.parametrize("kw", [
    {},
    {"year": "2022"},                                   # year-only dates cannot resolve the month; kept
    {"arxiv_id": "2210.03629"},                          # ReAct, first month of the window
    {"arxiv_id": "2609.00001"},                          # posted after the window: not a hard exclude
    {"arxiv_id": "2026"},                                # polluted arxiv_id field is ignored
    {"source": "leaderboard", "title": "SWE-agent", "abstract": ""},
    {"source": "leaderboard", "title": "grok-voice-think-fast-1.0 + tool-mentor (Pickle)", "abstract": ""},
    {"source": "arxiv", "title": "GPT-4 Technical Report", "abstract": ""},   # bare-name rule only on leaderboards
])
def test_t0_rules_do_not_fire(kw):
    assert st.t0_rule(pd.Series(cand("r", **kw))) is None


def test_t0_wins_over_votes():
    df = run([cand("a", year="2010")], [vote("a", "include")], [vote("a", "include", model="claude-sonnet-5")])
    assert df.loc["a", "tier"] == "T0" and df.loc["a", "auto_decision"] == "exclude" and df.loc["a", "needs_human"] == 0


# ---------------------------------------------------------------- T1-T3, pending

def test_t1_t2_t3_and_pending():
    cands = [cand(r) for r in "abcde"]
    v1 = [vote("a", "exclude", step="1"), vote("b", "include"), vote("c", "include"), vote("d", "exclude", step="2"), vote("e", "include")]
    v2 = [vote("a", "exclude", step="1", model="claude-sonnet-5"), vote("b", "include", model="claude-sonnet-5"),
          vote("c", "exclude", step="1", model="claude-sonnet-5"), vote("e", "include", model="claude-opus-5")]
    df = run(cands, v1, v2)
    assert df.loc["a", "tier"] == "T1" and df.loc["a", "auto_decision"] == "exclude"
    assert df.loc["b", "tier"] == "T2" and df.loc["b", "auto_decision"] == "include"
    assert df.loc["c", "tier"] == "T3" and df.loc["c", "needs_human"] == 1 and df.loc["c", "human_sample_type"] == "conflict"
    assert df.loc["d", "tier"] == "pending" and df.loc["d", "tier_rule"] == "second_vote_missing" and df.loc["d", "auto_decision"] == ""
    assert df.loc["e", "tier"] == "pending" and df.loc["e", "tier_rule"] == "same_model_second_vote"
    assert set(df.reset_index().columns) >= set(st.OUT_COLUMNS)


def test_verification_sample_is_deterministic_and_near_rate():
    n = 4000
    ids = [f"rec{i}" for i in range(n)]
    cands = [cand(r) for r in ids]
    v1 = [vote(r, "exclude", step="1") for r in ids]
    v2 = [vote(r, "exclude", step="1", model="claude-sonnet-5") for r in ids]
    df = run(cands, v1, v2)
    sampled = set(df.index[df.needs_human == 1])
    assert 0.02 * n < len(sampled) < 0.04 * n
    assert (df.loc[list(sampled), "human_sample_type"] == "verify_exclude").all()
    # same records are sampled when only a subset of the coverage is present (re-runnable)
    half = ids[: n // 2]
    df2 = run([cand(r) for r in half], [v for v in v1 if v["record_id"] in set(half)], [v for v in v2 if v["record_id"] in set(half)])
    assert set(df2.index[df2.needs_human == 1]) == {r for r in sampled if r in set(half)}


# ---------------------------------------------------------------- T4 rule R4

def test_r4a_both_negative_survey():
    d, rule = st.apply_r4("unsure", "1", "Survey of LLM agents; discusses existing systems.", "exclude", "1", "Survey, no named harness.")
    assert d == "exclude" and rule.startswith("R4a_both_negative")


def test_r4a_requires_step_1_to_3():
    d, rule = st.apply_r4("unsure", "1", "Survey of LLM agents; discusses existing systems.", "exclude", "8", "Embodied robotics.")
    assert d == "" and rule == "R4_human_unresolved"


def test_r4_hedge_blocks_rule_exclude():
    d, rule = st.apply_r4("unsure", "1", "Benchmark for coding agents; may ship a reference harness.", "unsure", "1", "Benchmark paper.")
    assert d == "" and rule == "R4_human_hedge"
    d, rule = st.apply_r4("unsure", "1", "Survey of agents.", "unsure", "1", "Survey; unclear whether it proposes a system.")
    assert d == "" and rule == "R4_human_hedge"


def test_r4_negation_of_named_system_is_not_a_hedge():
    d, _ = st.apply_r4("unsure", "1", "Survey of game agents; discusses existing systems.", "exclude", "1", "Survey of game agents, no specific named harness.")
    assert d == "exclude"


def test_r4_benchmark_used_for_evaluation_is_not_negative():
    assert "benchmark_only" not in st.neg_signals("AgentX runs a tool loop; evaluated on the SWE-bench benchmark.")
    assert "benchmark_only" in st.neg_signals("SWE-bench is a benchmark for coding agents.")


def test_r4b_include_plus_clean_unsure():
    d, rule = st.apply_r4("include", "none", "AgentX wraps a model in a tool loop.", "unsure", "2", "Loop structure not stated in the abstract.")
    assert d == "include" and rule == "R4b_include_plus_unsure_no_negative"


def test_r4b_blocked_by_negative_signal_in_unsure():
    d, rule = st.apply_r4("include", "none", "AgentX wraps a model in a tool loop.", "unsure", "1", "Survey of agent frameworks.")
    assert d == "" and rule == "R4_human_unresolved"


def test_r4_leaderboard_records_go_to_human():
    d, rule = st.apply_r4("unsure", "1", "Leaderboard entry only.", "unsure", "1", "Leaderboard entry, no harness detail.", source="leaderboard")
    assert d == "" and rule == "R4_human_leaderboard_record"


def test_t4_end_to_end_sets_sample_types():
    cands = [cand("x"), cand("y"), cand("z")]
    v1 = [vote("x", "unsure", "Survey of agents; discusses existing systems.", "1"), vote("y", "include", "AgentY loops over tools."),
          vote("z", "unsure", "Benchmark; may ship reference agent.", "1")]
    v2 = [vote("x", "exclude", "Survey, no named system.", "1", "claude-sonnet-5"), vote("y", "unsure", "Loop not described.", "2", "claude-sonnet-5"),
          vote("z", "unsure", "Benchmark paper.", "1", "claude-sonnet-5")]
    df = run(cands, v1, v2)
    assert (df.tier == "T4").all()
    assert df.loc["x", "auto_decision"] == "exclude" and df.loc["x", "human_sample_type"] in ("", "verify_exclude")
    assert df.loc["y", "auto_decision"] == "include" and df.loc["y", "human_sample_type"] in ("", "verify_include")
    assert df.loc["z", "auto_decision"] == "" and df.loc["z", "needs_human"] == 1 and df.loc["z", "human_sample_type"] == "unsure"


def test_model_kappa_uses_only_different_model_pairs():
    cands = [cand(r) for r in "abc"]
    v1 = [vote("a", "include"), vote("b", "exclude", step="1"), vote("c", "include")]
    v2 = [vote("a", "include", model="claude-sonnet-5"), vote("b", "exclude", step="1", model="claude-sonnet-5"), vote("c", "include", model="claude-opus-5")]
    kap = st.model_kappa(run(cands, v1, v2).reset_index())
    assert kap["n_overlap"] == 2 and kap["kappa_3class"] == 1.0


def test_queue_files_are_valid_json(tmp_path):
    cands = [cand("a"), cand("b")]
    v1 = [vote("a", "include"), vote("b", "exclude", step="1")]
    v2 = [vote("a", "exclude", step="1", model="claude-sonnet-5"), vote("b", "exclude", step="1", model="claude-sonnet-5")]
    df = run(cands, v1, v2).reset_index()
    n = st.write_queue(df, pd.DataFrame(cands), tmp_path / "q.json", tmp_path / "q.js")
    payload = json.loads((tmp_path / "q.json").read_text(encoding="utf-8"))
    assert payload["n"] == n == int(df.needs_human.sum()) and payload["records"][0]["record_id"] == "a"
    js = (tmp_path / "q.js").read_text(encoding="utf-8")
    assert js.startswith("window.HUMAN_QUEUE = ") and json.loads(js[len("window.HUMAN_QUEUE = "):].rstrip().rstrip(";")) == payload


# ---------------------------------------------------------------- merge

def triage_fixture():
    rows = []
    def add(rid, tier, auto, sample, v1, v2, rule=""):
        rows.append({"record_id": rid, "title": rid, "year": "2025", "source": "arxiv", "url": "", "vote_1": v1, "model_1": "m1", "reason_1": "",
                     "vote_2": v2, "model_2": "m2", "reason_2": "", "tier": tier, "tier_rule": rule or tier, "auto_decision": auto,
                     "needs_human": 1 if sample else 0, "human_sample_type": sample})
    add("t0", "T0", "exclude", "", "", "")
    add("t1a", "T1", "exclude", "", "exclude", "exclude")
    add("t1b", "T1", "exclude", "verify_exclude", "exclude", "exclude")
    add("t1c", "T1", "exclude", "verify_exclude", "exclude", "exclude")
    add("t2a", "T2", "include", "verify_include", "include", "include")
    add("t3a", "T3", "", "conflict", "include", "exclude")
    add("t3b", "T3", "", "conflict", "exclude", "include")
    add("t4a", "T4", "", "unsure", "unsure", "unsure")
    add("t4b", "T4", "exclude", "verify_exclude", "unsure", "exclude", "R4a_both_negative:survey")
    add("p", "pending", "", "", "include", "")
    return pd.DataFrame(rows)


def decisions_fixture():
    return pd.DataFrame([
        {"record_id": "t1b", "human_decision": "exclude", "exclusion_reason": "out_of_scope", "decided_at": "2026-09-18T10:00:00Z"},
        {"record_id": "t1c", "human_decision": "include", "exclusion_reason": "", "decided_at": "2026-09-18T10:01:00Z"},
        {"record_id": "t2a", "human_decision": "include", "exclusion_reason": "", "decided_at": "2026-09-18T10:02:00Z"},
        {"record_id": "t3a", "human_decision": "exclude", "exclusion_reason": "no_harness_description", "decided_at": "2026-09-18T10:03:00Z"},
        {"record_id": "t3a", "human_decision": "include", "exclusion_reason": "", "decided_at": "2026-09-18T11:00:00Z"},   # later decision wins
        {"record_id": "t4a", "human_decision": "unsure", "exclusion_reason": "", "decided_at": "2026-09-18T10:04:00Z"},
        {"record_id": "t4b", "human_decision": "unsure", "exclusion_reason": "", "decided_at": "2026-09-18T10:05:00Z"},
        {"record_id": "zzz", "human_decision": "bogus", "exclusion_reason": "", "decided_at": "2026-09-18T10:06:00Z"},
    ])


def test_merge_final_decisions(tmp_path):
    dpath = tmp_path / "decisions.csv"
    decisions_fixture().to_csv(dpath, index=False)
    d = sm.load_decisions(dpath)
    assert len(d) == 6 and d.set_index("record_id").loc["t3a", "human_decision"] == "include"
    df = sm.merge(triage_fixture(), d).set_index("record_id")
    assert df.loc["t0", "final_decision"] == "exclude" and df.loc["t0", "decision_source"] == "rule"
    assert df.loc["t1a", "final_decision"] == "exclude" and df.loc["t1a", "decision_source"] == "model_agree"
    assert df.loc["t1c", "final_decision"] == "include" and df.loc["t1c", "decision_source"] == "human"   # human overrides model agreement
    assert df.loc["t3a", "final_decision"] == "include"
    assert df.loc["t3b", "final_decision"] == "" and df.loc["t3b", "decision_source"] == ""
    assert df.loc["t4a", "final_decision"] == "include" and df.loc["t4a", "decision_source"] == "human_unsure"
    assert df.loc["t4b", "final_decision"] == "include" and df.loc["t4b", "decision_source"] == "human_unsure"
    assert df.loc["p", "final_decision"] == ""


def test_merge_stats_and_prisma(tmp_path):
    dpath = tmp_path / "decisions.csv"
    decisions_fixture().to_csv(dpath, index=False)
    df = sm.merge(triage_fixture(), sm.load_decisions(dpath))
    s = sm.stats(df)
    assert s["n_human_decided"] == 6
    ae = s["verification"]["agreed_exclude"]
    assert ae["all"]["n_verified"] == 3 and ae["all"]["strict_errors"] == 1 and ae["all"]["lenient_errors"] == 2
    assert ae["T1_both_exclude"]["n_verified"] == 2 and ae["T4_rule_exclude"]["lenient_errors"] == 1
    lo, hi = ae["all"]["lenient_ci95"]
    assert 0 <= lo < ae["all"]["lenient_rate"] < hi <= 1
    ai = s["verification"]["agreed_include"]["all"]
    assert ai["n_verified"] == 1 and ai["strict_errors"] == 0
    assert s["human_vs_model"]["all"]["model_1"]["n"] == 6
    prisma = tmp_path / "prisma_counts.json"
    prisma.write_text(json.dumps({"identified_by_source": {"arxiv": 10}, "duplicates_removed": 0, "screened_title_abstract": 0, "_notes": {"later_stages": "x"}}), encoding="utf-8")
    c = sm.update_prisma(df, prisma)
    assert c["screened_title_abstract"] == 8 and c["excluded_title_abstract"] == 3 and c["sought_full_text"] == 5
    assert c["_notes"]["screening_status"].startswith("partial") and "later_stages" in c["_notes"]
    assert c["identified_by_source"] == {"arxiv": 10}


def test_wilson_bounds():
    assert sm.wilson(0, 0) == (None, None)
    lo, hi = sm.wilson(0, 100)
    assert lo == 0.0 and 0.03 < hi < 0.04
