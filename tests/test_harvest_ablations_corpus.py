"""Tests for scripts/harvest_ablations_corpus.py and the `--corpus` pooling in analyse_ablations.py.

No network and no model calls: the extractor is a fake backend. What is pinned here is what a reader
of the corpus-wide pooled table has to take on trust - that every number in it was printed in the
paper (the verbatim guard), that nothing is counted twice (the coded-harvest duplicate flag), that
the guards reuse the coded-set analysis' own dimension menu, confidence floor and orientation rather
than parallel ones, that the Hartung-Knapp interval is the textbook one, and that `--corpus` leaves
the coded-set outputs alone.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


aa = _load("analyse_ablations", ROOT / "scripts" / "analyse_ablations.py")
h = _load("harvest_ablations_corpus", ROOT / "scripts" / "harvest_ablations_corpus.py")

DIMS = aa.load_dimensions()
DESIGN = aa.design_dimension_keys(DIMS)

WINDOW = """TITLE: GraphBit
=== passage A ===
4.7 Memory Architecture Ablation
Configuration Acc. (%) Mem. (MB)∆Acc.
Full GraphBit67.6 126.1—
w/o ephemeral scratch 64.7 189.2−2.9
w/o structured state 57.4 138.7−10.2
Table 3: Ablation study on the three-tier memory architecture.
"""


def row(**kw) -> dict:
    base = {"system": "GraphBit", "full_arm": "Full GraphBit", "ablated_arm": "w/o structured state",
            "component": "structured state tier", "category": "ablation",
            "dimension": "short_term_state", "direction": "component_removed", "benchmark": "GAIA",
            "split": "", "metric": "Acc. (%)", "base_model": "GPT-5.2", "same_base_model": True,
            "full_score": "67.6", "ablated_score": "57.4", "confidence": 0.8,
            "evidence": "w/o structured state 57.4", "reason": "fixture"}
    return base | kw


# ------------------------------------------------------------------------------------------------
# stage 1: prefilter
# ------------------------------------------------------------------------------------------------
def test_record_ids_map_to_their_text_file_and_never_to_the_repo_bundle(tmp_path):
    assert h.safe_id("arxiv:2605.13848") == "arxiv__2605.13848"
    assert h.safe_id("github:owner/repo") == "github__owner__repo"
    p = h.fulltext_path("arxiv:2605.13848", tmp_path)
    assert p.name == "arxiv__2605.13848.txt" and not p.name.endswith("__repo.txt")


def test_the_fetch_header_is_split_from_the_body():
    meta, body = h.split_header("record_id: a:b\nfetched_title: T\n\nBody line\nmore")
    assert meta["fetched_title"] == "T"
    assert body == "Body line\nmore"
    meta2, body2 = h.split_header("No header here\n\nsecond paragraph")
    assert meta2 == {} and body2.startswith("No header")


def test_prefilter_score_counts_ablat_and_w_o_even_when_pdf_glues_words():
    score, counts = h.prefilter_score("Ablation study. We ablate X. thew/o RAGandw/o Profiling w/out Y")
    assert counts["ablat"] == 2
    assert counts["w/o"] == 3
    assert score == 5


@pytest.mark.parametrize("score,chars,tier", [(10, 9000, "T10"), (9, 9000, "T3"), (3, 9000, "T3"),
                                               (2, 9000, "below"), (50, 100, "no_fulltext")])
def test_tiers(score, chars, tier):
    assert h.tier_of(score, chars) == tier


def test_prefilter_ranks_the_high_tier_first_and_is_resumable(tmp_path):
    root = tmp_path / "ft"
    root.mkdir()
    body_hi = "x " * 1200 + " ablation " * 12
    body_lo = "x " * 1200 + " ablation w/o " * 2
    (root / "a__hi.txt").write_text("record_id: a:hi\nfetched_title: Hi\n\n" + body_hi, encoding="utf-8")
    (root / "a__lo.txt").write_text("record_id: a:lo\nfetched_title: Lo\n\n" + body_lo, encoding="utf-8")
    (root / "a__stub.txt").write_text("record_id: a:stub\n\nshort", encoding="utf-8")
    out = tmp_path / "pf.csv"
    df = h.run_prefilter(["a:lo", "a:stub", "a:hi"], root=root, out=out, coded={"a:lo"})
    assert list(df["record_id"]) == ["a:hi", "a:lo", "a:stub"]
    assert list(df["tier"]) == ["T10", "T3", "no_fulltext"]
    assert df.set_index("record_id").loc["a:lo", "in_coded_harvest"] == 1
    assert "ablat=12" in df.loc[0, "reasons"]
    # a second run re-reads nothing: the file is the cache
    (root / "a__hi.txt").unlink()
    df2 = h.run_prefilter(["a:lo", "a:stub", "a:hi"], root=root, out=out)
    assert list(df2["tier"]) == ["T10", "T3", "no_fulltext"]


# ------------------------------------------------------------------------------------------------
# stage 2: localisation
# ------------------------------------------------------------------------------------------------
BODY = ("Intro text about agents.\n" * 30 + WINDOW.split("=== passage A ===\n")[1]
        + "Unrelated discussion.\n" * 30
        + "Table 5: Main results against baselines.\nReAct 40.1 30.2\nReflexion 41.0 31.5\n"
        + "Closing words.\n" * 10)


def test_localise_keeps_the_ablation_table_and_its_caption():
    text, info = h.localise(BODY)
    assert "w/o structured state 57.4" in text
    assert "Full GraphBit67.6" in text
    assert "Table 3: Ablation study" in text
    assert info["n_segments"] >= 1


def test_localise_returns_nothing_for_a_paper_without_numbers_or_ablations():
    text, _ = h.localise("We discuss agents.\n" * 200)
    assert text == ""


def test_localise_respects_its_character_budget():
    blocks = []
    for t in range(60):   # sixty separate ablation tables, each well under the per-region cap
        rows = "\n".join(f"w/o component {i} {50 + i}.{t % 10} {60 + i}.{i}" for i in range(8))
        blocks.append(f"Table {t}: Ablation of part {t}.\n{rows}\nprose\nprose\nprose\nprose")
    text, info = h.localise("\n".join(blocks), max_chars=3000)
    assert len(text) <= 3000 + 200   # plus passage labels
    assert info["truncated"] is True


def test_passage_labels_contain_no_digits_so_they_can_never_be_read_as_scores():
    assert [h._letters(i) for i in (0, 1, 25, 26, 27)] == ["A", "B", "Z", "AA", "AB"]


def test_build_window_prepends_title_and_setup_and_is_hashed():
    meta = {"fetched_title": "GraphBit"}
    body = "We use GPT-4o as the backbone model for all runs. " + BODY
    text, info = h.build_window(meta, body)
    assert text.startswith("TITLE: GraphBit")
    assert "SETUP MENTIONS" in text and "GPT-4o" in text
    assert info["chars"] == len(text)
    assert h.window_sha(text) == h.window_sha(text) and len(h.window_sha(text)) == 16


# ------------------------------------------------------------------------------------------------
# stage 4: the guards
# ------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text,value", [("67.6", 67.6), ("67.6%", 67.6), (" 0.412 ", 0.412),
                                        ("−2.9", -2.9), ("1,234", 1234.0), ("54*", 54.0)])
def test_parse_score(text, value):
    assert h.parse_score(text) == pytest.approx(value)


def test_a_mean_plus_minus_sd_cell_is_read_as_its_mean():
    assert h.parse_score("34.1±14.2") == pytest.approx(34.1)
    assert h.parse_score("66.67 ± 5.77") == pytest.approx(66.67)
    assert h.scores_in_window("34.1±14.2", "29.6 ± 9.2", "Full 34.1±14.2 w/o X 29.6±9.2")


@pytest.mark.parametrize("text", ["", None, "n/a", "67.6 / 68.1", "~60", "sixty"])
def test_parse_score_refuses_anything_that_is_not_one_number(text):
    assert h.parse_score(text) is None


def test_scores_must_appear_verbatim_in_the_window():
    assert h.scores_in_window("67.6", "57.4", WINDOW)
    assert not h.scores_in_window("67.6", "57.5", WINDOW)      # a mis-copied number
    assert not h.scores_in_window("67.60", "57.4", WINDOW)     # reformatted
    assert not h.scores_in_window("68", "57.4", WINDOW)        # rounded


def test_the_verbatim_match_respects_number_boundaries():
    w = "x 67.61 y 167 z 5"
    assert not h.score_positions("67.6", w)       # not a prefix of a longer number
    assert not h.score_positions("67", w)         # not inside 167 or 67.61
    assert h.score_positions("5", w) == [16]


def test_a_decimal_glued_to_the_previous_pdf_cell_matches_and_is_flagged():
    w = "i1_onN=20100.0%Invariant\nDIVER-longNL 37349.35 52.02"
    assert h.scores_in_window("100.0", "49.35", w)
    assert h.score_match("100.0", "49.35", w) == "glued"
    assert h.score_match("52.02", "49.35", "a 52.02 b 49.35") == "bounded"
    # an integer never gets the glued allowance
    assert not h.score_positions("20", "N=20100")
    # a decimal may also run straight into the next decimal cell, but not into a longer number
    assert h.scores_in_window("65.51", "63.71", "∆C 65.5163.71 59.40")
    assert not h.score_positions("67.6", "x 67.61 y")


def test_scores_must_be_colocated():
    far = "full 67.6 " + ("filler " * 600) + " ablated 57.4"
    assert h.scores_in_window("67.6", "57.4", far)
    assert not h.scores_colocated("67.6", "57.4", far)
    assert h.scores_colocated("67.6", "57.4", WINDOW)


def test_delta_scale_metric_and_variant_predicates():
    assert h.is_signed_delta("67.6", "-10.2")
    assert not h.is_signed_delta("67.6", "57.4")
    assert not h.is_signed_delta("-1.2", "-3.4")
    assert h.scale_mismatch(0.67, 67.0)
    assert not h.scale_mismatch(0.67, 0.61) and not h.scale_mismatch(67.0, 61.0)
    for m in ("Cost ($)", "latency (s)", "Tokens", "# steps", "Time"):
        assert not h.is_performance_metric(m), m
    for m in ("Acc. (%)", "pass@1", "% resolved", "Success Rate", "F1",
              "Success Rate (%) 50 steps", "Overall (%) 50 steps accuracy"):
        assert h.is_performance_metric(m), m
    assert h.is_model_or_training_variant(row(category="model_or_training_variant"))
    assert h.is_model_or_training_variant(row(same_base_model=False))
    assert h.is_model_or_training_variant(row(ablated_arm="w/o SFT", component="supervised fine-tuning"))
    assert h.is_model_or_training_variant(row(ablated_arm="Ours (GPT-4o)", component="base model"))
    assert h.is_model_or_training_variant(row(ablated_arm="Ours (Qwen2.5-7B)", component="7B model"))
    assert not h.is_model_or_training_variant(row())
    # a model that labels BOTH arms is the shared base model, not a variant
    assert not h.is_model_or_training_variant(row(full_arm="DualGraph (GPT-4.1)",
                                                  ablated_arm="DualGraph w/o KG (GPT-4.1)"))
    assert h.is_model_or_training_variant(row(full_arm="DualGraph (GPT-4.1)",
                                              ablated_arm="DualGraph (GPT-4o-mini)"))


def test_a_clean_row_survives_and_is_oriented_by_the_shared_function():
    reason, out = h.guard_row(row(), WINDOW, DESIGN)
    assert reason == ""
    assert out["rel_effect"] == pytest.approx((67.6 - 57.4) / 67.6)
    assert out["delta_raw"] == pytest.approx(10.2)
    oriented, _ = aa.orient_contrast(67.6, 57.4, direction="component_removed", metric="Acc. (%)",
                                     benchmark="GAIA", split="")
    for k, v in oriented.items():
        assert out[k] == v, k


def test_an_augmentation_is_oriented_the_other_way_round():
    # the arm is labelled as an addition: a "w/o" label oriented as an addition is dropped by
    # `direction_contradicts_label` (tested below)
    reason, out = h.guard_row(row(category="augmentation", direction="component_added",
                                  full_arm="Base", ablated_arm="+ structured state",
                                  full_score="57.4", ablated_score="67.6"), WINDOW, DESIGN)
    assert reason == ""
    assert out["rel_effect"] == pytest.approx((67.6 - 57.4) / 67.6)


@pytest.mark.parametrize("kw,reason", [
    ({"full_score": "n/a"}, "malformed_row"),
    ({"ablated_score": "57.5"}, "score_not_in_text"),
    ({"ablated_score": "−10.2"}, "signed_delta_as_score"),
    ({"metric": "Mem. (MB)", "ablated_score": "138.7", "full_score": "126.1"}, "not_a_performance_metric"),
    ({"category": "model_or_training_variant"}, "model_or_training_variant"),
    ({"same_base_model": False}, "model_or_training_variant"),
    ({"dimension": "open_source"}, "dimension_not_design"),        # layer M cannot be ablated
    ({"dimension": "memory_magic"}, "dimension_not_design"),       # not a schema key at all
    ({"confidence": 0.45}, "low_confidence"),
    ({"dimension": "unmapped"}, "unmapped"),
    ({"category": "unmapped", "dimension": "unmapped"}, "unmapped"),
    ({"category": "rival_system", "dimension": "unmapped"}, "not_an_ablation:rival_system"),
    ({"category": "banana"}, "not_an_ablation:unknown"),
    ({"direction": "unclear"}, "direction_unclear"),
    ({"direction": "component_changed"}, "direction_component_changed"),
])
def test_every_guard_drops_with_its_own_reason(kw, reason):
    got, _ = h.guard_row(row(**kw), WINDOW, DESIGN)
    assert got == reason


def test_the_confidence_floor_is_the_coded_set_one():
    assert h.guard_row(row(confidence=aa.CONF_FLOOR), WINDOW, DESIGN)[0] == ""
    assert h.guard_row(row(confidence=aa.CONF_FLOOR - 0.01), WINDOW, DESIGN)[0] == "low_confidence"


def test_every_drop_reason_maps_to_a_funnel_stage():
    for r in ("not_an_ablation:rival_system", "direction_unclear", "denominator_too_small",
              "variance_not_finite", "score_not_in_text"):
        assert h.guard_stage(r) in h.GUARD_ORDER


# ------------------------------------------------------------------------------------------------
# de-duplication against the coded-set harvest
# ------------------------------------------------------------------------------------------------
CODED = pd.DataFrame([{"record_id": "p1", "label": "Ours w/o Memory Module", "benchmark": "SWE-bench",
                       "metric": "% resolved", "full_score": 50.0, "ablated_score": 40.0}])


def test_a_corpus_contrast_already_in_the_coded_harvest_is_flagged_by_key():
    corpus = pd.DataFrame([{"record_id": "p1", "component": "memory module", "label": "w/o memory",
                            "benchmark": "SWE-bench Verified", "metric": "% Resolved",
                            "full_score": 51.0, "ablated_score": 39.0}])
    assert list(aa.flag_coded_duplicates(corpus, CODED)) == ["key"]


def test_a_corpus_contrast_with_the_same_two_numbers_is_flagged_whatever_its_labels():
    corpus = pd.DataFrame([{"record_id": "p1", "component": "long-term store", "label": "LTS off",
                            "benchmark": "SWEB", "metric": "acc", "full_score": 50.0,
                            "ablated_score": 40.0}])
    assert list(aa.flag_coded_duplicates(corpus, CODED)) == ["scores"]


def test_other_papers_and_other_components_are_not_duplicates():
    corpus = pd.DataFrame([
        {"record_id": "p2", "component": "memory module", "label": "w/o memory", "benchmark": "SWE-bench",
         "metric": "% resolved", "full_score": 50.0, "ablated_score": 40.0},
        {"record_id": "p1", "component": "planner", "label": "w/o planner", "benchmark": "SWE-bench",
         "metric": "% resolved", "full_score": 50.0, "ablated_score": 45.0},
    ])
    assert list(aa.flag_coded_duplicates(corpus, CODED)) == ["", ""]
    assert list(aa.flag_coded_duplicates(corpus, pd.DataFrame())) == ["", ""]


def test_component_tokens_drop_the_ablation_wording():
    assert aa.component_tokens("Ours w/o Memory Module") == frozenset({"memory"})
    assert aa.component_tokens("- verification") == frozenset({"verification"})


# ------------------------------------------------------------------------------------------------
# building the outputs from the cache
# ------------------------------------------------------------------------------------------------
def _prefilter(ids):
    return pd.DataFrame([{"rank": i + 1, "record_id": r, "score": 20, "tier": "T10"}
                         for i, r in enumerate(ids)])


def _windows(ids, text=WINDOW):
    return {r: {"record_id": r, "version": h.WINDOW_VERSION, "sha": h.window_sha(text),
                "window": text, "info": {"n_segments": 1}} for r in ids}


def test_build_outputs_applies_the_guards_flags_coded_duplicates_and_logs_every_paper():
    ids = ["p1", "p2", "p3", "p4"]
    windows = _windows(ids[:3]) | {"p4": {"record_id": "p4", "version": h.WINDOW_VERSION, "sha": "",
                                          "window": "", "info": {}}}
    sha = h.window_sha(WINDOW)
    cache = {
        "p1": {"record_id": "p1", "window_sha": sha, "rows": [row(), row(), row(ablated_score="99.9")],
               "model": "m", "note": ""},
        "p2": {"record_id": "p2", "window_sha": sha, "rows": [row(confidence=0.2)], "model": "m"},
        "p3": {"record_id": "p3", "window_sha": "stale", "rows": [row()], "model": "m"},
    }
    coded = pd.DataFrame([{"record_id": "p1", "label": "w/o structured state", "benchmark": "GAIA",
                           "metric": "Acc. (%)", "full_score": 1.0, "ablated_score": 2.0}])
    built = h.build_outputs(_prefilter(ids), windows, cache, DIMS, coded_contrasts=coded,
                            system_map={"p1": [("graphbit", "GraphBit")]})
    rows = built["rows"]
    assert sorted(rows["drop_reason"]) == sorted(["", "duplicate_contrast", "score_not_in_text",
                                                   "low_confidence", "stale_window"])
    con = built["contrasts"]
    assert list(con.columns[: len(aa.CONTRAST_COLUMNS)]) == aa.CONTRAST_COLUMNS
    assert len(con) == 1
    assert con.loc[0, "system_id"] == "graphbit"
    assert con.loc[0, "provenance"] == h.PROVENANCE
    assert con.loc[0, "already_in_coded_harvest"] == 1        # same paper, benchmark, metric, component
    assert built["summary"]["pool_eligible_contrasts"] == 0
    out = built["outcomes"].set_index("record_id")
    assert out.loc["p1", "status"] == "extracted" and out.loc["p1", "rows_proposed"] == 3
    assert out.loc["p1", "rows_already_in_coded_harvest"] == 1
    assert "score_not_in_text=1" in out.loc["p1", "drop_reasons"]
    assert out.loc["p3", "status"] == "stale"
    assert out.loc["p4", "status"] == "no_window"
    funnel = built["funnel"].set_index("stage")
    assert funnel.loc["rows_proposed", "surviving"] == 5
    assert funnel.iloc[-1]["surviving"] == 0


def test_a_paper_without_a_coded_system_gets_a_corpus_system_id():
    assert h.resolve_system_id("p9", "Foo", {}) == "corpus:p9"
    m = {"p1": [("a", "AlphaAgent"), ("b", "BetaAgent")]}
    assert h.resolve_system_id("p1", "BetaAgent", m) == "b"
    assert h.resolve_system_id("p1", "Unknown", m) == "a"


# ------------------------------------------------------------------------------------------------
# stage 3: extraction loop (fake backend)
# ------------------------------------------------------------------------------------------------
class FakeExtractor:
    def __init__(self, fail_first: str | None = None, fail_ids: set[str] | None = None):
        self.calls = 0
        self.fail_first = fail_first
        self.fail_ids = fail_ids or set()
        self.sent: list[list[str]] = []

    def __call__(self, exe, model, system_file, batch, effort=None, schema=None, prompt=None,
                 text_json=False):
        self.calls += 1
        assert text_json is True and schema is h.EXTRACT_SCHEMA
        assert "window" in prompt(batch)
        assert "REFUSE TO GUESS" in Path(system_file).read_text(encoding="utf-8")
        self.sent.append([it["record_id"] for it in batch])
        if self.fail_first and self.calls == 1:
            raise RuntimeError(self.fail_first)
        if any(it["record_id"] in self.fail_ids for it in batch):
            raise ValueError("model JSON has no 'votes' array")
        return type("R", (), {"votes": [{"record_id": it["id"], "rows": [row()], "note": ""}
                                        for it in batch],
                              "model": "fake", "tokens_in": 10, "tokens_out": 5})()


def _args(**kw):
    base = {"tiers": ("T10",), "limit": 0, "batch_size": 2, "max_batch_chars": 10 ** 6,
            "workers": 1, "model": "sonnet", "effort": "low", "deadline_hours": 1.0,
            "max_failures": 2, "rebuild_every": 1, "max_stalls": 3, "limit_wait": 30}
    return argparse.Namespace(**(base | kw))


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    for name in ("CACHE_JSONL", "FAILURES_JSON", "STATUS_JSON", "RUN_LOG"):
        monkeypatch.setattr(h, name, tmp_path / name.lower())
    return tmp_path


def test_extraction_caches_every_paper_and_a_rerun_sends_nothing(workdir):
    ids = ["p1", "p2", "p3"]
    fake = FakeExtractor()
    stats_ = h.run_extract(_args(), _prefilter(ids), _windows(ids), DIMS, fake, "")
    assert stats_["papers_done"] == 3 and fake.calls == 2
    cache = h.load_jsonl(h.CACHE_JSONL)
    assert set(cache) == set(ids)
    assert cache["p1"]["window_sha"] == h.window_sha(WINDOW)
    fake2 = FakeExtractor()
    assert h.run_extract(_args(), _prefilter(ids), _windows(ids), DIMS, fake2, "")["papers_done"] == 0
    assert fake2.calls == 0


def test_a_usage_limit_requeues_the_batch_and_waits_for_the_reset(workdir):
    ids = ["p1", "p2"]
    waits: list[float] = []
    fake = FakeExtractor(fail_first="claude result error: You've hit your session limit · resets 2:50am")
    stats_ = h.run_extract(_args(), _prefilter(ids), _windows(ids), DIMS, fake, "", sleep=waits.append)
    assert stats_["limit_waits"] == 1 and len(waits) == 1
    assert stats_["papers_done"] == 2
    assert fake.sent[0] == fake.sent[1], "the limited batch is retried, not dropped"


def test_a_failing_batch_is_split_and_a_bad_paper_is_given_up_on(workdir):
    ids = ["p1", "p2"]
    fake = FakeExtractor(fail_ids={"p2"})
    stats_ = h.run_extract(_args(max_failures=2), _prefilter(ids), _windows(ids), DIMS, fake, "")
    assert stats_["papers_done"] == 1
    assert set(h.load_jsonl(h.CACHE_JSONL)) == {"p1"}
    failures = json.loads(h.FAILURES_JSON.read_text(encoding="utf-8"))
    assert failures["p2"]["count"] == 2


def test_limit_kinds():
    assert h.limit_kind("You've hit your session limit · resets 2:50am (America/New_York)") == "usage"
    assert h.limit_kind("api_error_status=429 rate_limit_error") == "transient"
    assert h.limit_kind("Overloaded") == "transient"
    assert h.limit_kind("model JSON has no 'votes' array") == ""


def test_pack_batches_by_count_and_by_characters():
    items = [{"window": "x" * n} for n in (10, 10, 10, 100, 10)]
    assert [len(b) for b in h.pack_batches(items, 2, 10 ** 6)] == [2, 2, 1]
    assert [len(b) for b in h.pack_batches(items, 9, 50)] == [3, 1, 1]


def test_the_subscription_path_only(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    h.subscription_env()
    import os
    assert "ANTHROPIC_API_KEY" not in os.environ
    src = (ROOT / "scripts" / "harvest_ablations_corpus.py").read_text(encoding="utf-8")
    assert "make_api_backend" not in src and "import anthropic" not in src
    assert "vote_batch_claude_code" in src


def test_the_prompt_carries_the_menu_the_metadata_refusal_and_the_verbatim_rule():
    prompt = h.extract_system_prompt(DIMS)
    for key in DESIGN:
        assert key in prompt
    assert "can NEVER be the answer" in prompt and "open_source" in prompt
    assert "EXACTLY as printed" in prompt


# ------------------------------------------------------------------------------------------------
# pooling: Hartung-Knapp and --corpus
# ------------------------------------------------------------------------------------------------
def test_hartung_knapp_matches_hand_computed_values():
    # y = (0, 1), v = (1, 1), tau2 = 0: mu = 0.5, q = 0.5, SE = sqrt(0.5/2) = 0.5, t(1) = 12.7062
    se, lo, hi = aa.hartung_knapp([0.0, 1.0], [1.0, 1.0], 0.0)
    assert se == pytest.approx(0.5)
    assert hi - 0.5 == pytest.approx(12.706204736 * 0.5, rel=1e-6)
    # y = (1, 2, 3), v = 1, tau2 = 0: mu = 2, q = 1, SE = sqrt(1/3), t(2) = 4.302653
    se, lo, hi = aa.hartung_knapp([1.0, 2.0, 3.0], [1.0, 1.0, 1.0], 0.0)
    assert se == pytest.approx(math.sqrt(1 / 3))
    assert lo == pytest.approx(2 - 4.302652730 * math.sqrt(1 / 3), rel=1e-6)
    assert all(math.isnan(x) for x in aa.hartung_knapp([1.0], [1.0], 0.0))


def test_hartung_knapp_is_wider_than_z_with_few_heterogeneous_studies():
    y, v = [0.05, 0.30, 0.12, 0.22], [0.002, 0.003, 0.002, 0.004]
    p = aa.dersimonian_laird(y, v)
    _, lo, hi = aa.hartung_knapp(y, v, p.tau2)
    assert hi - lo > p.ci_high - p.ci_low


def _contrast(record_id, dim="long_term_memory", full=50.0, abl=40.0, system_id=None):
    oriented, _ = aa.orient_contrast(full, abl, direction="component_removed", metric="% resolved",
                                     benchmark="SWE-bench", split="Verified")
    return {"record_id": record_id, "system_id": system_id or f"s-{record_id}", "label": "w/o memory",
            "dimension": dim, "category": "ablation", "direction": "component_removed",
            "confidence": 0.8, "benchmark": "SWE-bench", "split": "Verified", "metric": "% resolved",
            "model": "gpt-4o", **oriented}


def test_the_corpus_pooled_table_carries_hk_and_provenance_and_the_default_does_not():
    coded = pd.DataFrame([_contrast("c1"), _contrast("c2")], columns=aa.CONTRAST_COLUMNS)
    corpus = pd.DataFrame([_contrast("k1", abl=45.0), _contrast("k2", abl=30.0)])
    corpus["provenance"] = "corpus_fulltext"
    both = aa.combine_contrasts(coded, corpus)
    assert list(both["provenance"]) == ["coded_harvest"] * 2 + ["corpus_fulltext"] * 2
    table, _ = aa.pool_by_dimension(both, corpus_columns=True)
    r = table.set_index("dimension").loc["long_term_memory"]
    assert r["n_papers"] == 4 and r["n_papers_coded"] == 2 and r["n_papers_corpus"] == 2
    assert r["hk_ci_low"] < r["mu_rel"] < r["hk_ci_high"]
    plain, _ = aa.pool_by_dimension(coded)
    assert list(plain.columns) == aa.POOLED_COLUMNS


def test_revariance_changes_only_the_assumed_size_rows():
    frame = pd.DataFrame([_contrast("c1")])
    frame.loc[0, "n_source"] = "default"
    out = aa.revariance(frame, 50)
    assert out.loc[0, "n_items"] == 50 and out.loc[0, "variance"] > frame.loc[0, "variance"]
    frame.loc[0, "n_source"] = "table"
    assert aa.revariance(frame, 50).loc[0, "variance"] == frame.loc[0, "variance"]


REJECT_COLUMNS = ["reason", "row_id", "system_id", "record_id", "reported_system_name", "benchmark",
                  "split", "metric", "score", "model", "evidence_quote", "evidence_locator", "note"]
OWN_COLUMNS = ["system_id", "model", "benchmark", "split", "metric", "score", "cost_usd", "tokens",
               "date", "source_url", "comparable_key", "notes"]


def test_main_corpus_mode_writes_only_suffixed_outputs_and_never_counts_twice(tmp_path):
    rejects, own = [], []
    for i in range(2):
        rejects.append({"reason": "not_own_system", "system_id": f"s{i}", "record_id": f"p{i}",
                        "reported_system_name": "Ours w/o memory", "benchmark": "SWE-bench",
                        "split": "Verified", "metric": "% resolved", "score": "40", "model": "gpt-4o",
                        "evidence_quote": "w/o memory", "note": "ablation"})
        own.append({"system_id": f"s{i}", "model": "gpt-4o", "benchmark": "SWE-bench",
                    "split": "Verified", "metric": "% resolved", "score": 50.0,
                    "notes": "source=paper"})
    paths = {k: tmp_path / v for k, v in {"rejects": "rej.csv", "results": "res.csv",
                                          "systems": "sys.json", "cache": "cache.json",
                                          "out": "analysis", "fig": "fig",
                                          "corpus": "corpus.csv"}.items()}
    pd.DataFrame([{c: "" for c in REJECT_COLUMNS} | r for r in rejects]).to_csv(paths["rejects"], index=False)
    pd.DataFrame([{c: "" for c in OWN_COLUMNS} | r for r in own]).to_csv(paths["results"], index=False)
    paths["systems"].write_text("[]", encoding="utf-8")
    paths["cache"].write_text(json.dumps({"labels": {
        f"s{i}|ours w/o memory": {"raw": {"category": "ablation", "dimension": "long_term_memory",
                                          "direction": "component_removed", "confidence": 0.9,
                                          "reason": "x"}, "label": "Ours w/o memory",
                                  "own_system_id": f"s{i}", "model": "fake"} for i in range(2)}}),
        encoding="utf-8")
    corpus = pd.DataFrame([_contrast("k1", abl=45.0), _contrast("k2", abl=30.0),
                           _contrast("p0", full=50.0, abl=40.0)])   # p0 duplicates the coded contrast
    corpus["provenance"] = "corpus_fulltext"
    corpus["component"] = "memory"
    corpus.to_csv(paths["corpus"], index=False)
    before = paths["cache"].read_text(encoding="utf-8")
    code = aa.main(["--rejects", str(paths["rejects"]), "--results", str(paths["results"]),
                    "--systems", str(paths["systems"]), "--out-dir", str(paths["out"]),
                    "--fig-dir", str(paths["fig"]), "--cache", str(paths["cache"]), "--no-render",
                    "--corpus", "--corpus-contrasts", str(paths["corpus"]), "--sensitivity"])
    assert code == 0
    written = {p.name for p in paths["out"].iterdir()}
    assert "ablation_pooled_corpus.csv" in written and "ablation_credible_corpus.csv" in written
    assert "ablation_sensitivity_n_corpus.csv" in written
    assert not any(n.startswith("ablation_") and "_corpus" not in n for n in written), written
    assert paths["cache"].read_text(encoding="utf-8") == before
    pooled = pd.read_csv(paths["out"] / "ablation_pooled_corpus.csv").set_index("dimension")
    r = pooled.loc["long_term_memory"]
    assert r["n_papers"] == 4 and r["n_papers_coded"] == 2 and r["n_papers_corpus"] == 2
    assert {"hk_ci_low", "hk_ci_high"} <= set(pooled.columns)
    con = pd.read_csv(paths["out"] / "ablation_contrasts_corpus.csv")
    assert (con["record_id"] == "p0").sum() == 1, "the duplicate corpus contrast must not be pooled"
    summary = json.loads((paths["out"] / "ablation_summary_corpus.json").read_text(encoding="utf-8"))
    assert summary["provenance"]["already_in_coded_harvest"] == 1
    assert summary["dimensions_poolable"] == 1


# ------------------------------------------------------------------------------------------------
# classification guards (report time): each known mis-mapping is a fixture, copied from the cache
# ------------------------------------------------------------------------------------------------
def known(window: str, **kw) -> tuple[dict, str]:
    """A row as the extractor answered it, and the window its numbers are printed in."""
    return row(**kw), window


ZHULONG = known(
    "Component ablation (vs. ZhuLong Full)\nZhuLong(Full)78.5 +3.2 pp\nZhuLong w/o Self-Expl. 75.3 -3.2 pp\n"
    "ZhuLong w/o Sandbox 37.3 -41.2 pp\n",
    system="ZhuLong", full_arm="ZhuLong(Full)", ablated_arm="ZhuLong w/o Sandbox",
    component="sandbox execution", dimension="execution_isolation", metric="Pass@1", benchmark="PyAether",
    full_score="78.5", ablated_score="37.3", evidence="ZhuLong w/o Sandbox 37.3 -41.2 pp",
    reason="sandbox execution is the execution_isolation component")
WEBDESIGNITER = known(
    "Full System 34.90 48.10\nw/o Sandbox 31.60 (-3.30) 43.20 (-4.90)\n",
    full_arm="Full System", ablated_arm="w/o Sandbox", component="sandbox execution module",
    dimension="execution_isolation", metric="Pass@1", full_score="34.90", ablated_score="31.60",
    evidence="w/o Sandbox 31.60 (-3.30) 43.20 (-4.90)")
IAC_EVAL = known(
    "Full MACOG (all components) 11.86 80.54 94.10 74.02\n– DevOps (no plan/apply sandbox) 9.47 74.82 88.57 56.93\n",
    full_arm="Full MACOG (all components)", ablated_arm="– DevOps (no plan/apply sandbox)",
    component="DevOps plan/apply sandbox", dimension="execution_isolation", metric="IaC-Eval",
    full_score="74.02", ablated_score="56.93",
    evidence="– DevOps (no plan/apply sandbox) 9.47 74.82 88.57 56.93")
DPIAGENT = known(
    "Full w/o Prot. w/o Isol. w/o Divd.\nS.↑ 74.2870.90 72.70 67.66\n∆C↑ 71.7465.98 64.03 61.03\n",
    full_arm="Full", ablated_arm="w/o Isol.", component="phase-specific tool gating",
    dimension="permission_model", metric="S.", full_score="74.28", ablated_score="72.70",
    evidence="S.↑ 74.2870.90 72.70 67.66", reason="exposing all tools across phases removes tool gating")
SOLAGENT = known(
    "w/o Tools: The agent cannot access the file system to read dependencies or project structure.\n"
    "SolAgent Claude-Sonnet-4.5 64.39%\nw/o Tools Claude-Sonnet-4.5 57.66%\n",
    system="SolAgent", full_arm="SolAgent", ablated_arm="w/o Tools", component="file-system access tools",
    dimension="filesystem_access", metric="Pass@1 (%)", full_score="64.39", ablated_score="57.66",
    evidence="w/o Tools: The agent cannot access the file system to read dependencies or project "
             "structure. ... w/o Tools Claude-Sonnet-4.5 ... 57.66%")
SAFETY_FILTER = known(
    "Ours (w/o safety filter) 0.3557 0.5515 0.4325 0.265015.80\nOurs (w/ safety filter) 0.3611 0.5103 0.4229\n",
    full_arm="Ours (w/ safety filter)", ablated_arm="Ours (w/o safety filter)", component="safety filter",
    category="augmentation", dimension="guardrails", direction="component_added", metric="F1",
    full_score="0.4229", ablated_score="0.4325",
    evidence="Ours (w/o safety filter) 0.3557 0.5515 0.4325 0.265015.80 ... Ours (w/ safety filter) "
             "0.3611 0.5103 0.4229")
EFFGEN = known(
    "Configuration Acc∆ Acc∆ Acc∆\nFull EFFGEN 47.44 – 63.07 – 70.97 –\n−Complexity Routing 43.87−3.6 56.84−6.2\n",
    system="EFFGEN", full_arm="Full EFFGEN", ablated_arm="−Complexity Routing",
    component="complexity-based model routing", dimension="cost_controls", metric="Acc",
    full_score="47.44", ablated_score="43.87", evidence="−Complexity Routing 43.87 −3.6",
    reason="routing maps to cost_controls (model_routing)")
GRASP = known(
    "GRASP(full) 86.0±4.4 88.8±5.8\nw/o regression budget 81.2±6.5 81.8±1.8\n",
    full_arm="GRASP (full)", ablated_arm="w/o regression budget", component="regression budget",
    dimension="cost_controls", metric="Test", full_score="88.8", ablated_score="81.8",
    evidence="w/o regression budget 81.2±6.5 81.8±1.8")
CACHING = known(
    "w/o Caching 83.10 78.81 79.49\nProposed Framework 86.89 82.34 84.21\n",
    full_arm="Proposed Framework", ablated_arm="w/o Caching", component="caching mechanism",
    dimension="cost_controls", metric="Accuracy (%)", full_score="84.21", ablated_score="79.49",
    evidence="w/o Caching 83.10 78.81 79.49 ... Proposed Framework 86.89 82.34 84.21")


def guarded(fixture):
    r, w = fixture
    return h.guard_row(r, w, DESIGN)


@pytest.mark.parametrize("fixture", [ZHULONG, WEBDESIGNITER, IAC_EVAL],
                         ids=["zhulong", "webdesigniter", "iac-eval"])
def test_sandbox_is_execution_feedback_moves_the_known_sandbox_rows_to_self_verification(fixture):
    reason, out = guarded(fixture)
    assert reason == ""
    assert out["norm_dimension"] == "self_verification"
    assert out["dimension_before_guard"] == "execution_isolation"
    assert out["guard_applied"] == "sandbox_is_execution_feedback"


def test_the_zhulong_contrast_keeps_its_numbers_when_it_moves():
    _, out = guarded(ZHULONG)
    assert (out["full_value"], out["ablated_value"]) == (78.5, 37.3)
    assert out["rel_effect"] == pytest.approx((78.5 - 37.3) / 78.5)


@pytest.mark.parametrize("kw", [
    {"ablated_arm": "w/o container isolation", "component": "Docker container",
     "evidence": "w/o container isolation (code runs directly on the host) 37.3"},
    {"ablated_arm": "w/o Sandbox", "component": "sandbox", "metric": "Attack success rate (%)"},
])
def test_execution_isolation_stays_only_for_a_boundary_or_a_safety_metric(kw):
    r, w = ZHULONG
    reason, out = h.guard_row(r | kw, w, DESIGN)
    assert reason == "" and out["norm_dimension"] == "execution_isolation"
    assert out.get("remap_action") == "retained" and "guard_applied" not in out


def test_an_execution_isolation_row_naming_neither_execution_nor_a_boundary_is_unmapped():
    r, w = ZHULONG
    reason, _ = h.guard_row(r | {"ablated_arm": "w/o Guard Layer", "component": "guard layer",
                                 "evidence": "w/o Guard Layer 37.3"}, w, DESIGN)
    assert reason == "sandbox_is_execution_feedback"


def test_tool_gating_is_tool_interface_on_the_dpiagent_row():
    r, w = DPIAGENT
    clean = r | {"evidence": "w/o Isol. 72.70"}          # the printed row, without the glued cell
    reason, out = h.guard_row(clean, w, DESIGN)
    assert reason == "" and out["norm_dimension"] == "tool_count"
    assert out["guard_applied"] == "tool_gating_is_tool_interface"
    # as cached, its evidence runs 74.28 into 70.90: dropped, with the remap still on the audit trail
    reason, out = h.guard_row(r, w, DESIGN)
    assert reason == "scores_not_separable"
    assert "tool_gating_is_tool_interface" in out["guards_matched"].split(";")


def test_permission_model_stays_only_for_an_enforced_authorisation():
    r, w = DPIAGENT
    kw = {"ablated_arm": "w/o user approval", "component": "per-call user approval", "evidence": "72.70"}
    reason, out = h.guard_row(r | kw, w, DESIGN)
    assert reason == "" and out["norm_dimension"] == "permission_model"
    kw = {"ablated_arm": "w/o Authority Manifolds", "component": "authority manifolds", "evidence": "72.70"}
    assert h.guard_row(r | kw, w, DESIGN)[0] == "tool_gating_is_tool_interface"


def test_tools_ablation_is_context_moves_solagent_to_env_context_strategy():
    reason, out = guarded(SOLAGENT)
    assert reason == "" and out["norm_dimension"] == "env_context_strategy"
    assert out["guard_applied"] == "tools_ablation_is_context"


def test_a_tools_ablation_that_only_loses_write_access_stays_and_a_bare_one_is_the_tool_set():
    r, w = SOLAGENT
    write = r | {"component": "file tools", "evidence": "w/o Tools: read-only workspace, no file writes 57.66%"}
    reason, out = h.guard_row(write, w, DESIGN)
    assert reason == "" and out["norm_dimension"] == "filesystem_access"
    bare = r | {"component": "tools", "evidence": "w/o Tools 57.66%"}
    reason, out = h.guard_row(bare, w, DESIGN)
    assert reason == "" and out["norm_dimension"] == "tool_count"
    other = r | {"ablated_arm": "read-only FS", "component": "write access", "evidence": "57.66%"}
    reason, out = h.guard_row(other, w, DESIGN)
    assert out["norm_dimension"] == "filesystem_access" and "remap_action" not in out


@pytest.mark.parametrize("evidence", ["S.↑ 74.2870.90 72.70 67.66",
                                      "Ours (w/o safety filter) 0.3557 0.5515 0.4325 0.265015.80"])
def test_scores_not_separable_sees_run_together_numbers(evidence):
    assert h.scores_not_separable(evidence)


def test_scores_not_separable_leaves_ordinary_and_label_glued_cells_alone():
    for ev in ("w/o structured state 57.4 138.7−10.2", "Full GraphBit67.6 126.1—", "0.4229 0.4325",
               "81.2±6.5 81.8±1.8", "version 2.10.1 scored 67.6"):
        assert not h.scores_not_separable(ev), ev


def test_the_dpiagent_and_safety_filter_rows_are_dropped_as_not_separable():
    assert guarded(DPIAGENT)[0] == "scores_not_separable"
    reason, out = guarded(SAFETY_FILTER)
    assert reason == "scores_not_separable"
    assert out["guard_applied"] == "scores_not_separable"


@pytest.mark.parametrize("metric", ["∆C", "Δ Acc", "delta SR", "Gain (%)", "Improvement", " ∆Acc."])
def test_delta_metric_as_score_drops_unsigned_difference_columns(metric):
    r, w = DPIAGENT
    reason, _ = h.guard_row(r | {"metric": metric, "evidence": "72.70"}, w, DESIGN)
    assert reason == "delta_metric_as_score"


@pytest.mark.parametrize("metric", ["Acc. (%)", "SR", "Pass@1", "Success gain-adjusted score"])
def test_delta_metric_as_score_leaves_score_columns_alone(metric):
    assert not h.is_delta_metric(metric)


def test_cost_component_not_a_limit_drops_routing_regression_budget_and_unscoped_caching():
    assert guarded(EFFGEN)[0] == "cost_component_not_a_limit"
    assert guarded(GRASP)[0] == "cost_component_not_a_limit"
    reason, out = guarded(CACHING)
    assert reason == "cost_component_not_a_limit" and "scope" in out["guard_note"]


def test_effgen_routing_is_not_a_model_variant_because_its_arms_share_a_base_model():
    # the paper routes between a single ReAct agent and decomposed execution on ONE model per
    # column; only the extractor's paraphrase says "model routing"
    assert not h.is_model_or_training_variant(EFFGEN[0])
    assert h.is_model_or_training_variant(row(ablated_arm="w/o model router", component="router"))
    assert h.is_model_or_training_variant(row(ablated_arm="single LLM",
                                              component="routing between small and large models"))


@pytest.mark.parametrize("kw,dim", [
    ({"component": "program caching", "evidence": "caches programs for reuse on similar future tasks 79.49"},
     "state_persistence"),
    ({"component": "tool-result caching", "evidence": "memoises repeated tool calls within a run 79.49"},
     "short_term_state"),
    ({"component": "token budget", "ablated_arm": "w/o token budget"}, "cost_controls"),
    ({"component": "early stop to save cost", "ablated_arm": "w/o cost-aware stopping"}, "cost_controls"),
])
def test_cost_controls_holds_only_spending_limits_and_caching_moves_to_state(kw, dim):
    r, w = CACHING
    reason, out = h.guard_row(r | kw, w, DESIGN)
    assert reason == "" and out["norm_dimension"] == dim


def test_a_timeouts_contrast_whose_component_is_not_a_limit_is_flagged_not_dropped():
    r, w = CACHING
    reason, out = h.guard_row(r | {"dimension": "timeouts", "component": "retry handler",
                                   "ablated_arm": "w/o retry handler"}, w, DESIGN)
    assert reason == "" and out["guard_flag"] == h.LIMIT_FLAG
    reason, out = h.guard_row(r | {"dimension": "timeouts", "component": "timeout handling",
                                   "ablated_arm": "w/o Timeout Handling"}, w, DESIGN)
    assert reason == "" and "guard_flag" not in out


def test_direction_contradicts_label_catches_the_backwards_safety_filter_row():
    r, w = SAFETY_FILTER
    assert "signals removal" in h.direction_contradicts_label(r)
    # as cached it is also not separable, which decides it; the audit still names this rule
    _, out = h.guard_row(r, w, DESIGN)
    assert "direction_contradicts_label" in out["guards_matched"].split(";")
    # with the glued cell gone, this rule alone drops it - the sign is never flipped by hand
    reason, out = h.guard_row(r | {"evidence": "Ours (w/o safety filter) 0.4325"}, w, DESIGN)
    assert reason == "direction_contradicts_label"
    assert "rel_effect" not in out


@pytest.mark.parametrize("full_arm,arm,direction,category,bad", [
    ("Full (Kv=3)", "Kv=0 (no verifiers)", "component_added", "augmentation", True),
    ("Full", "−Memory", "component_added", "ablation", True),
    ("Base", "+ Memory", "component_removed", "ablation", True),
    ("w/o memory, w/o planner", "w/o memory", "component_added", "augmentation", False),  # cumulative
    ("Full HMT", "w/ Flat Memory", "component_removed", "ablation", False),               # replacement
    ("Full", "w/ Single Agent Scaffold", "component_removed", "ablation", False),
    ("SPIKE (Full)", "Dual Controller + Global Memory", "component_removed", "ablation", False),  # a listing
    ("Base", "w/ verifier", "component_added", "augmentation", False),
    ("Full", "w/o verifier", "component_removed", "ablation", False),
])
def test_direction_contradicts_label_cases(full_arm, arm, direction, category, bad):
    r = row(full_arm=full_arm, ablated_arm=arm, direction=direction, category=category)
    assert bool(h.direction_contradicts_label(r)) is bad


def test_every_classification_guard_is_a_funnel_stage_in_order():
    for g in h.CLASSIFICATION_GUARDS:
        assert h.guard_stage(g) == g and g in h.GUARD_ORDER
    stages = [h.GUARD_ORDER.index(s) for s in (
        "signed_delta_as_score", "delta_metric_as_score", "scores_not_separable", "model_or_training_variant",
        "not_an_ablation", "sandbox_is_execution_feedback", "direction", "direction_contradicts_label",
        "orientation")]
    assert stages == sorted(stages)


def test_guards_never_mutate_the_row_they_read():
    for fixture in (ZHULONG, DPIAGENT, SOLAGENT, SAFETY_FILTER, EFFGEN, CACHING):
        r, w = fixture
        before = copy.deepcopy(r)
        h.guard_row(r, w, DESIGN)
        h.classification_matches(r)
        assert r == before


def test_build_outputs_writes_the_guard_audit_and_counts_every_guard_in_the_funnel():
    fixtures = {"arxiv:2608.07925": ZHULONG, "arxiv:2608.23341": DPIAGENT, "arxiv:2601.23009": SOLAGENT,
                "arxiv:2605.29146": SAFETY_FILTER, "arxiv:2602.00887": EFFGEN}
    ids = list(fixtures)
    windows = {rid: {"record_id": rid, "version": h.WINDOW_VERSION, "sha": h.window_sha(w), "window": w,
                     "info": {"n_segments": 1}} for rid, (_, w) in fixtures.items()}
    cache = {rid: {"record_id": rid, "window_sha": h.window_sha(w), "rows": [r], "model": "m"}
             for rid, (r, w) in fixtures.items()}
    built = h.build_outputs(_prefilter(ids), windows, cache, DIMS, coded_contrasts=pd.DataFrame(),
                            system_map={})
    audit = built["audit"]
    assert list(audit.columns) == h.AUDIT_COLUMNS
    got = {(a.record_id, a.guard, a.action) for a in audit.itertuples()}
    assert ("arxiv:2608.07925", "sandbox_is_execution_feedback", "remapped") in got
    assert ("arxiv:2601.23009", "tools_ablation_is_context", "remapped") in got
    assert ("arxiv:2608.23341", "scores_not_separable", "dropped") in got
    assert ("arxiv:2608.23341", "tool_gating_is_tool_interface", "also_matched") in got
    assert ("arxiv:2605.29146", "scores_not_separable", "dropped") in got
    assert ("arxiv:2605.29146", "direction_contradicts_label", "also_matched") in got
    assert ("arxiv:2602.00887", "cost_component_not_a_limit", "dropped") in got
    z = audit[(audit.record_id == "arxiv:2608.07925")].iloc[0]
    assert (z.dimension_before, z.dimension_after, z.final_status) == \
        ("execution_isolation", "self_verification", "pool_eligible")
    funnel = built["funnel"].set_index("stage")
    assert funnel.loc["sandbox_is_execution_feedback", "remapped"] == 1
    assert funnel.loc["scores_not_separable", "dropped"] == 2
    assert funnel.loc["cost_component_not_a_limit", "dropped"] == 1
    assert funnel.iloc[-1]["surviving"] == 2
    con = built["contrasts"].set_index("record_id")
    assert con.loc["arxiv:2608.07925", "dimension"] == "self_verification"
    assert con.loc["arxiv:2608.07925", "dimension_before_guard"] == "execution_isolation"
    assert con.loc["arxiv:2601.23009", "dimension"] == "env_context_strategy"
    out = built["outcomes"].set_index("record_id")
    assert "sandbox_is_execution_feedback:remapped=1" in out.loc["arxiv:2608.07925", "guard_actions"]
    assert "scores_not_separable=1" in out.loc["arxiv:2608.23341", "drop_reasons"]
    s = built["summary"]["classification_guards"]
    assert s["sandbox_is_execution_feedback"]["remapped"] == 1
    assert s["sandbox_is_execution_feedback"]["papers"] == ["arxiv:2608.07925"]


def test_the_report_never_rewrites_the_extract_stage_cache(tmp_path, monkeypatch):
    """Guards run at report time on the cached raw answers: the cache and windows files are read,
    never written, and the extract stage's prompt version and schema are the ones the cache holds."""
    fixtures = {"arxiv:2608.07925": ZHULONG, "arxiv:2605.29146": SAFETY_FILTER}
    work = tmp_path / "corpus_ablation"
    work.mkdir()
    pf = tmp_path / "prefilter.csv"
    _prefilter(list(fixtures)).to_csv(pf, index=False)
    h.append_jsonl(work / "windows.jsonl", [
        {"record_id": rid, "version": h.WINDOW_VERSION, "sha": h.window_sha(w), "window": w, "info": {}}
        for rid, (_, w) in fixtures.items()])
    h.append_jsonl(work / "extract_cache.jsonl", [
        {"record_id": rid, "window_sha": h.window_sha(w), "prompt_version": h.PROMPT_VERSION,
         "rows": [r], "model": "m", "note": ""} for rid, (r, w) in fixtures.items()])
    monkeypatch.setattr(h, "PREFILTER_CSV", pf)
    monkeypatch.setattr(h, "WINDOWS_JSONL", work / "windows.jsonl")
    monkeypatch.setattr(h, "CACHE_JSONL", work / "extract_cache.jsonl")
    for name in ("ROWS_CSV", "CONTRASTS_CSV", "OUTCOMES_CSV", "FUNNEL_CSV", "SUMMARY_JSON", "GUARD_AUDIT_CSV"):
        monkeypatch.setattr(h, name, tmp_path / getattr(h, name).name)
    monkeypatch.setattr(h, "OUT_DIR", tmp_path)
    cache_bytes = (work / "extract_cache.jsonl").read_bytes()
    window_bytes = (work / "windows.jsonl").read_bytes()
    cache_before = h.load_jsonl(work / "extract_cache.jsonl")
    built = h.rebuild_all(DIMS)
    assert (work / "extract_cache.jsonl").read_bytes() == cache_bytes
    assert (work / "windows.jsonl").read_bytes() == window_bytes
    assert h.load_jsonl(work / "extract_cache.jsonl") == cache_before
    assert cache_before["arxiv:2608.07925"]["rows"][0]["dimension"] == "execution_isolation"
    assert (tmp_path / "corpus_ablation_guard_audit.csv").exists()
    assert built["contrasts"].loc[0, "dimension"] == "self_verification"
    # the extract stage the scheduler runs is unchanged: same prompt version and schema
    assert h.PROMPT_VERSION == "corpus-ablation-v1-2026-09-25"
    assert hashlib.sha1(json.dumps(h.EXTRACT_SCHEMA, sort_keys=True).encode()).hexdigest() == \
        "acb002dba043acf8d03364f59714558abaee4fbf"
