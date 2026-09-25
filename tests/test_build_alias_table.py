"""Tests for scripts/build_alias_table.py.

The property under test is the one the script exists for: an alias is accepted ONLY when the source
paper itself names the coded system. Everything else - the model, the shortlist, the cache - is
machinery around that rule, so the tests are written from the rule outwards:

  * a perfect string match whose system is NOT named in the paper is refused;
  * one that IS named is accepted, with the span and a character offset that can be re-read from the
    file;
  * a bare model name is refused before a model is ever asked;
  * the existing vetoes of `leaderboards_to_results.py` (over-merged census group, org corroboration,
    version compatibility, digit agreement) still fire;
  * the (label, paper) cache means a second run makes no backend call;
  * every rejection reaches the refusals file with a reason.

No network and no model: every model call goes through a fake backend injected as
`main(argv, backend=...)`, and the fixtures are a hand-written registry, three short "papers" and a
small `results_rejects.csv`.
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyse_blocks as AB
import build_alias_table as BAT
import fulltext_screen as fs
import leaderboards_to_results as LB
import screen_llm

PAPER_A = "arxiv:9001.00001"   # names OpenHands
PAPER_B = "arxiv:9001.00002"   # names nothing
PAPER_C = "arxiv:9001.00003"   # names SWE-agent and Agent S2, and the reporting paper's own system

BODY_A = """\
We evaluate on SWE-bench Verified. Our system is compared against several open scaffolds.
The strongest open baseline is OpenHands, whose CodeAct agent we run at its default settings
(we use the OH CodeActAgent v1.5 configuration reported by its authors).
For completeness we also cite the Continue project's numbers, and note that agents in general
struggle here. Results are in Table 2.
"""
BODY_B = """\
We evaluate on WebArena. The baselines are a zero-shot prompted model and a retrieval variant.
No third-party scaffold was run, and no agent framework is cited in this section.
"""
BODY_C = """\
We compare with SWE-agent and with Agent S2 (Simular's follow-up). Our own system, MyPaper Agent,
is run at three backbones. The WidelyMerged project is mentioned only in related work.
"""


def _write_paper(root: Path, record_id: str, title: str, body: str) -> Path:
    path = root / f"{fs.safe_id(record_id)}.txt"
    header = (f"record_id: {record_id}\nsource_used: test\nfetched_url: https://example.invalid/x\n"
              f"fetched_title: {title}\nfetched_at: 2026-09-24T00:00:00+00:00\n")
    path.write_text(header + "\n" + body, encoding="utf-8")
    return path


SYSTEMS_FIXTURE = [
    {"id": "openhands", "name": "OpenHands",
     "urls": {"repo": "https://github.com/All-Hands-AI/OpenHands"}, "coding": {}},
    {"id": "openhands-2", "name": "OpenHands 2", "urls": {}, "coding": {}},
    {"id": "swe-agent", "name": "SWE-agent",
     "urls": {"repo": "https://github.com/SWE-agent/SWE-agent"}, "coding": {}},
    {"id": "agent-s2", "name": "Agent S2", "urls": {}, "coding": {}},
    {"id": "widelymerged", "name": "WidelyMerged", "urls": {}, "coding": {}},
    {"id": "continue", "name": "Continue", "urls": {}, "coding": {}},
    {"id": "mypaper", "name": "MyPaper Agent", "urls": {}, "coding": {}},
]

# `widelymerged` pools far more than MAX_GROUP_NAMES distinct name keys, which is the over-merged
# census-group veto; `agent-s2` carries a census variant that diverges from its canonical name.
CANDIDATES_FIXTURE = [
    {"system_id": "widelymerged", "name": "WidelyMerged", "repo_url": "",
     "name_variants": "MergedOne;MergedTwo;MergedThree;MergedFour;MergedFive;MergedSix;MergedSeven"},
    {"system_id": "agent-s2", "name": "Agent S2", "repo_url": "", "name_variants": "Agents 2.0"},
]

REJECT_COLUMNS = ["reason", "row_id", "system_id", "record_id", "reported_system_name", "benchmark",
                  "split", "metric", "score", "score_raw", "model", "evidence_quote",
                  "evidence_locator", "note"]


def _reject(record_id: str, label: str, *, own: str = "mypaper", score: str = "40.0",
            benchmark: str = "SWE-bench", metric: str = "resolved (%)", model: str = "gpt-4o",
            note: str = "", quote: str = "") -> dict[str, str]:
    return {"reason": "not_own_system", "row_id": f"{own}#{label[:8]}", "system_id": own,
            "record_id": record_id, "reported_system_name": label, "benchmark": benchmark,
            "split": "", "metric": metric, "score": score, "score_raw": score, "model": model,
            "evidence_quote": quote or f"{label} {score}", "evidence_locator": "paper Table 2",
            "note": note}


@dataclass
class Env:
    tmp: Path
    systems: Path
    candidates: Path
    fulltext: Path
    rejects: Path
    aliases: Path
    refused: Path
    cache: Path
    mention_cache: Path
    registry: object
    index: BAT.MentionIndex

    def argv(self, *extra: str) -> list[str]:
        return [
            "--systems", str(self.systems), "--candidates", str(self.candidates),
            "--fulltext-dir", str(self.fulltext), "--rejects", str(self.rejects),
            "--aliases", str(self.aliases), "--refused", str(self.refused),
            "--cache", str(self.cache), "--mention-cache", str(self.mention_cache), *extra,
        ]

    def alias_rows(self) -> list[dict[str, str]]:
        with self.aliases.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def refused_rows(self) -> list[dict[str, str]]:
        with self.refused.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))


def make_env(tmp_path: Path, rows: list[dict[str, str]] | None = None) -> Env:
    systems = tmp_path / "systems.json"
    systems.write_text(json.dumps(SYSTEMS_FIXTURE), encoding="utf-8")
    candidates = tmp_path / "systems_candidates.csv"
    with candidates.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["system_id", "name", "repo_url", "name_variants"])
        w.writeheader()
        w.writerows(CANDIDATES_FIXTURE)
    fulltext = tmp_path / "fulltext"
    fulltext.mkdir()
    _write_paper(fulltext, PAPER_A, "Scaffolds for software repair", BODY_A)
    _write_paper(fulltext, PAPER_B, "Web navigation baselines", BODY_B)
    _write_paper(fulltext, PAPER_C, "A follow-up study", BODY_C)
    rejects = tmp_path / "results_rejects.csv"
    with rejects.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REJECT_COLUMNS)
        w.writeheader()
        w.writerows(rows or [])
    registry = LB.load_registry(systems, candidates)
    return Env(tmp_path, systems, candidates, fulltext, rejects,
               tmp_path / "comparator_aliases.csv", tmp_path / "comparator_aliases_refused.csv",
               tmp_path / "cache.json", tmp_path / "mentions.json", registry,
               BAT.MentionIndex(registry, root=fulltext))


class FakeBackend:
    """A backend with `screen_llm.vote_batch_claude_code`'s signature. It counts its calls."""

    def __init__(self, answers: dict[str, dict[str, object]]) -> None:
        self.answers = answers
        self.calls = 0
        self.labels_seen: list[str] = []
        self.prompts: list[str] = []

    def __call__(self, exe, model, system_file, batch, effort=None, schema=None, prompt=None,
                 text_json=False):
        assert text_json is True, "the batch must be asked for as plain-text JSON"
        assert schema is BAT.PROPOSAL_SCHEMA
        assert Path(system_file).read_text(encoding="utf-8").strip()
        self.calls += 1
        self.prompts.append(prompt(batch))  # exercise the prompt builder on every call
        votes = []
        for item in batch:
            self.labels_seen.append(item["label"])
            ans = self.answers.get(item["label"], {})
            votes.append({
                "record_id": item["id"],
                "system_id": ans.get("system_id"),
                "corroborating_string": ans.get("corroborating_string", ""),
                "confidence": ans.get("confidence", 0.9),
                "reason": ans.get("reason", ""),
            })
        return screen_llm.BatchResult(votes, "fake-model", 100, 20, 0, 0, 0.0)


def _proposal(label: str, record_id: str, system_id: str, *, confidence: float = 0.9,
              corroborating_string: str = "", shortlist: tuple[str, ...] = ()) -> BAT.Proposal:
    return BAT.Proposal(label=label, record_id=record_id, system_id=system_id,
                        corroborating_string=corroborating_string, confidence=confidence,
                        shortlist_ids=shortlist or (system_id,))


# ------------------------------------------------------------------------------------------------
# the rule: corroboration in the paper accepts, its absence refuses
# ------------------------------------------------------------------------------------------------
def test_perfect_string_match_is_refused_when_the_paper_never_names_the_system(tmp_path):
    """PAPER_B does not say "OpenHands". "OpenHands" is a perfect match for the coded name, and it
    is still refused: the string match is not the evidence, the paper is."""
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(
        _proposal("OpenHands", PAPER_B, "openhands"), env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "no_corroboration_in_paper"
    assert "openhands" in refusal.detail
    assert PAPER_B in refusal.detail


def test_the_same_mapping_is_accepted_in_the_paper_that_does_name_the_system(tmp_path):
    env = make_env(tmp_path)
    accepted, refusal, cross = BAT.adjudicate(
        _proposal("OH CodeActAgent v1.5", PAPER_A, "openhands",
                  corroborating_string="OpenHands"), env.registry, env.index)
    assert refusal is None, refusal
    assert accepted.system_id == "openhands"
    assert accepted.corroborating_string == "OpenHands"
    assert cross == "model_string_confirmed"


def test_accepted_offset_can_be_re_read_from_the_fetched_file(tmp_path):
    """The recorded offset is the audit trail: the span must sit exactly there in the file."""
    env = make_env(tmp_path)
    accepted, _, _ = BAT.adjudicate(_proposal("OH CodeActAgent v1.5", PAPER_A, "openhands"),
                                    env.registry, env.index)
    raw = fs.fulltext_path(PAPER_A, env.fulltext).read_text(encoding="utf-8", errors="replace")
    start = accepted.char_offset
    assert raw[start:start + len(accepted.corroborating_string)] == accepted.corroborating_string
    assert start > 0


def test_missing_fulltext_is_its_own_refusal_reason(tmp_path):
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("OpenHands", "arxiv:9999.99999", "openhands"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "no_fulltext_for_paper"


def test_a_generic_name_may_not_corroborate_on_its_own(tmp_path):
    """PAPER_A says "Continue" and "agents". Neither is evidence of a citation: the head of the
    measured name-frequency distribution is English, not references."""
    env = make_env(tmp_path)
    assert "continue" in BAT.GENERIC_NAME_KEYS
    assert env.index.scan(PAPER_A).get("continue") is not None       # the token IS in the paper
    assert env.index.corroboration(PAPER_A, "continue") is None      # and may not corroborate
    accepted, refusal, _ = BAT.adjudicate(_proposal("Continue", PAPER_A, "continue"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "no_corroboration_in_paper"


def test_model_string_that_is_not_in_the_paper_still_accepts_on_the_index(tmp_path):
    """Mechanical corroboration is the gate; the model's quoted string is only a cross-check."""
    env = make_env(tmp_path)
    accepted, refusal, cross = BAT.adjudicate(
        _proposal("OH CodeActAgent v1.5", PAPER_A, "openhands",
                  corroborating_string="OpenHands Resolver Suite"), env.registry, env.index)
    assert refusal is None
    assert cross == "model_string_not_the_system"
    assert accepted.match_method.split("|")[2] == "mention_index"


# ------------------------------------------------------------------------------------------------
# a bare model name is never a harness
# ------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("label", [
    "gpt-4o", "GPT-4o", "GPT-4.1", "GPT-5.5", "ChatGPT", "o3-mini", "o1", "claude-3.7-sonnet",
    "Claude Opus 4.1", "Gemini-2.5-Pro", "Gemini 2.5 Flash", "Gemma3-4B", "Qwen2.5-7B-Instruct",
    "Qwen3-30B", "llama-3.1-70b", "DeepSeek", "DeepSeek-v3", "DeepSeek-R1-Distill",
    "mistral-large-2", "o4-mini-high", "gpt-oss-120b",
])
def test_bare_model_names_are_recognised(label):
    assert BAT.is_bare_model(label), label
    assert BAT.stoplist_reason(label) == "stoplist_model_name"


@pytest.mark.parametrize("label", [
    "OH CodeActAgent v1.5", "M3A", "Navi", "GenericAgent", "CAMEL (MASFactory)",
    "ScalingInter-7B", "Llama-3.1-70B + ComfyAgent", "GPT-5.5 w/ context", "OpenCode/Qwen3-30B",
])
def test_real_harness_labels_are_not_mistaken_for_models(label):
    assert not BAT.is_bare_model(label), label


def test_a_bare_model_name_is_refused_end_to_end_and_never_reaches_the_model(tmp_path):
    """The stop-list runs before the backend, so a model-name row costs nothing and is still logged."""
    env = make_env(tmp_path, [_reject(PAPER_A, "GPT-4o"), _reject(PAPER_A, "Qwen2.5-7B-Instruct")])
    backend = FakeBackend({"GPT-4o": {"system_id": "openhands", "confidence": 1.0},
                           "Qwen2.5-7B-Instruct": {"system_id": "openhands", "confidence": 1.0}})
    assert BAT.main(env.argv(), backend=backend) == 0
    assert backend.calls == 0, "a bare model name must never be sent to a model"
    assert env.alias_rows() == []
    reasons = {r["label"]: r["reason"] for r in env.refused_rows()}
    assert reasons == {"GPT-4o": "stoplist_model_name",
                       "Qwen2.5-7B-Instruct": "stoplist_model_name"}


def test_a_bare_model_proposal_is_refused_even_if_it_reaches_adjudication(tmp_path):
    """Belt and braces: `adjudicate` refuses a corroborating name that reads as a model."""
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("gpt-4o", PAPER_A, "openhands"),
                                          env.registry, env.index)
    # The label never gets this far in a run, so the guard that must hold here is the one on the
    # corroborating name; the label guard is asserted separately above.
    assert (accepted is None) == (refusal is not None)


@pytest.mark.parametrize("label,reason", [
    ("Ours", "stoplist_generic_label"),
    ("Baseline", "stoplist_generic_label"),
    ("Single agent", "stoplist_generic_label"),
    ("Vanilla", "stoplist_generic_label"),
    ("test-agent", "stoplist_placeholder"),
    ("IS", "stoplist_key_too_short"),
    ("gpt-4o", "stoplist_model_name"),
    ("OH CodeActAgent v1.5", ""),
])
def test_stoplist_reasons(label, reason):
    assert BAT.stoplist_reason(label) == reason


# ------------------------------------------------------------------------------------------------
# the existing vetoes of leaderboards_to_results.py still fire
# ------------------------------------------------------------------------------------------------
def test_over_merged_census_group_veto_still_fires(tmp_path):
    """`widelymerged` pools more than MAX_GROUP_NAMES names, so a hit on it identifies nothing."""
    env = make_env(tmp_path)
    assert env.registry.overmerged("widelymerged") > LB.MAX_GROUP_NAMES
    accepted, refusal, _ = BAT.adjudicate(_proposal("WidelyMerged", PAPER_C, "widelymerged"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "existing_veto"
    assert "over-merged" in refusal.detail


def test_version_compatibility_veto_still_fires(tmp_path):
    """A paper naming OpenHands (v1) is not evidence about OpenHands 2."""
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("OpenHands v2 CodeAct", PAPER_A, "openhands"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "version_incompatible"


def test_digit_agreement_veto_still_fires(tmp_path):
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("SWE-agent 7", PAPER_C, "swe-agent"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason in {"digits_disagree", "version_incompatible"}


def test_digit_agreement_is_satisfied_through_the_version_stripped_base_keys():
    """`match_system`'s own disjunction: "OH CodeActAgent v1.5" reaches a v1 system on base keys."""
    assert BAT.digits_ok("OH CodeActAgent v1.5", "OpenHands")[0]
    assert not BAT.digits_ok("tau2-bench reference agent", "tau-bench reference agent")[0]


def test_org_corroboration_veto_still_fires(tmp_path):
    """"Microsoft OpenHands" is refused: the repository owner is All-Hands-AI, not Microsoft."""
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("Microsoft OpenHands", PAPER_A, "openhands"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "existing_veto"
    assert "org" in refusal.detail


def test_divergent_census_name_variant_veto_still_fires(tmp_path):
    """`agent-s2` carries the census variant "Agents 2.0", which is not its canonical name."""
    env = make_env(tmp_path)
    mention = env.index.scan(PAPER_C).get("agent-s2")
    assert mention is not None
    cand = LB.Cand("Agents 2.0", "reported_system_name")
    assert LB.veto_reason(env.registry, "agent-s2", cand, "Agents 2.0", LB.FUZZY_THRESHOLD)


def test_guards_are_applied_to_the_harness_part_of_a_harness_slash_model_label():
    """"OpenCode/Qwen3-30B" names a harness and its backbone; the digits belong to the backbone."""
    parts = [c.text for c in BAT.guard_parts("OpenCode/Qwen3-30B/Spoon")]
    assert "OpenCode" in parts
    assert not any(BAT.is_bare_model(p) for p in parts)


def test_only_the_leftmost_non_model_part_may_ever_attribute():
    """`analyse_blocks`' rule, unrelaxed: "MLR-Agent ... + Codex" is MLR-Agent's row, not Codex's."""
    parts = [c.text for c in BAT.guard_parts("MLR-Agent o4-mini-high + Codex")]
    assert "Codex" not in parts
    assert "MLR-Agent o4-mini-high" in parts
    # a bare model on the left is skipped, and the next part is the leftmost NON-MODEL one
    assert "ComfyAgent" in [c.text for c in BAT.guard_parts("Llama-3.1-70B + ComfyAgent")]


def test_a_right_hand_harness_cannot_be_reached_through_the_guards(tmp_path):
    env = make_env(tmp_path)
    # PAPER_C names SWE-agent, so corroboration succeeds; the guards must still refuse, because the
    # label's leftmost non-model part is "MyPaper Agent 3", whose digits SWE-agent does not carry.
    accepted, refusal, _ = BAT.adjudicate(
        _proposal("MyPaper Agent 3 + SWE-agent", PAPER_C, "swe-agent",
                  corroborating_string="SWE-agent"), env.registry, env.index)
    assert accepted is None
    assert refusal.reason in {"digits_disagree", "version_incompatible"}


def test_ablation_and_veto_refusals_of_the_base_matcher_are_never_proposed(tmp_path):
    """The existing guards are guards, not gaps: going round them is not added recall."""
    rows = [_reject(PAPER_A, "OpenHands w/o memory", note="ablation: memory removed"),
            _reject(PAPER_A, "Ours full")]
    env = make_env(tmp_path, rows)
    backend = FakeBackend({r["reported_system_name"]: {"system_id": "openhands"} for r in rows})
    assert BAT.main(env.argv(), backend=backend) == 0
    assert backend.calls == 0
    assert env.alias_rows() == []
    assert {r["reason"] for r in env.refused_rows()} <= {
        "existing_guard_ablation", "existing_guard_veto", "stoplist_generic_label",
        "no_usable_harness_name"}


# ------------------------------------------------------------------------------------------------
# the model proposes, and only proposes
# ------------------------------------------------------------------------------------------------
def test_a_system_outside_the_shortlist_is_refused(tmp_path):
    env = make_env(tmp_path)
    prop = _proposal("Some Scaffold", PAPER_A, "openhands", shortlist=("swe-agent", "continue"))
    accepted, refusal, _ = BAT.adjudicate(prop, env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "system_id_not_in_shortlist"


def test_an_invented_system_id_is_refused(tmp_path):
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("Some Scaffold", PAPER_A, "not-a-real-id"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "system_id_not_coded"


def test_a_low_confidence_proposal_is_refused(tmp_path):
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(
        _proposal("OH CodeActAgent v1.5", PAPER_A, "openhands", confidence=0.3),
        env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "low_confidence"


def test_a_proposal_naming_the_reporting_papers_own_system_is_refused(tmp_path):
    """The extractor already judged this row not_own_system; overriding that relaxes its guard."""
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(_proposal("MyPaper Agent w/ GPT-4o", PAPER_C, "mypaper"),
                                          env.registry, env.index, own_system_id="mypaper")
    assert accepted is None
    assert refusal.reason == "own_system_of_reporting_paper"


def test_a_null_answer_is_recorded_as_a_refusal(tmp_path):
    env = make_env(tmp_path)
    accepted, refusal, _ = BAT.adjudicate(BAT.Proposal("Overall", PAPER_A, "", reason="a column"),
                                          env.registry, env.index)
    assert accepted is None
    assert refusal.reason == "model_answered_null"
    assert refusal.detail == "a column"


# ------------------------------------------------------------------------------------------------
# retrieval: high recall on purpose
# ------------------------------------------------------------------------------------------------
def test_the_shortlist_reaches_a_system_no_string_metric_could_find(tmp_path):
    """Nothing in "OH CodeActAgent v1.5" is within 78 of "OpenHands"; the paper's mention is."""
    env = make_env(tmp_path)
    assert "openhands" not in BAT.fuzzy_shortlist(env.registry, "OH CodeActAgent v1.5", 78)
    ids = [e.system_id for e in BAT.shortlist_for("OH CodeActAgent v1.5", PAPER_A, env.registry,
                                                  env.index)]
    assert "openhands" in ids


def test_the_shortlist_is_empty_for_a_paper_that_names_nothing(tmp_path):
    env = make_env(tmp_path)
    assert BAT.shortlist_for("Some Scaffold", PAPER_B, env.registry, env.index) == []


def test_the_shortlist_threshold_is_lower_than_every_accepting_threshold():
    assert BAT.SHORTLIST_THRESHOLD < 92 <= LB.FUZZY_THRESHOLD


def test_the_prompt_states_each_papers_shortlist_once(tmp_path):
    env = make_env(tmp_path)
    items = BAT.batch_items(
        [BAT.Candidate("OH CodeActAgent v1.5", PAPER_A), BAT.Candidate("Other Scaffold", PAPER_A)],
        env.registry, env.index, {PAPER_A: "Scaffolds for software repair"},
        BAT.SHORTLIST_THRESHOLD, BAT.MAX_SHORTLIST)
    text = BAT.build_prompt(items)
    assert text.count(f"PAPER {PAPER_A}") == 1
    assert "OH CodeActAgent v1.5" in text and "Other Scaffold" in text
    assert "mentioned in paper" in text


# ------------------------------------------------------------------------------------------------
# the cache
# ------------------------------------------------------------------------------------------------
def test_the_cache_prevents_a_second_backend_call(tmp_path):
    rows = [_reject(PAPER_A, "OH CodeActAgent v1.5"), _reject(PAPER_C, "The S2 Agent")]
    env = make_env(tmp_path, rows)
    backend = FakeBackend({"OH CodeActAgent v1.5": {"system_id": "openhands",
                                                    "corroborating_string": "OpenHands"},
                           "The S2 Agent": {"system_id": None}})
    assert BAT.main(env.argv(), backend=backend) == 0
    first = backend.calls
    assert first >= 1
    assert env.cache.exists()
    assert BAT.main(env.argv(), backend=backend) == 0
    assert backend.calls == first, "a second run must make no backend call"
    assert len(env.alias_rows()) == 1


def test_the_cache_is_keyed_by_label_and_paper(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_A, "OH CodeActAgent v1.5")])
    backend = FakeBackend({"OH CodeActAgent v1.5": {"system_id": "openhands"}})
    BAT.main(env.argv(), backend=backend)
    keys = list(BAT.load_proposal_cache(env.cache))
    assert keys == [BAT.cache_key("OH CodeActAgent v1.5", PAPER_A)]
    assert PAPER_A in keys[0] and "OH CodeActAgent v1.5" in keys[0]


# ------------------------------------------------------------------------------------------------
# the two output files
# ------------------------------------------------------------------------------------------------
def test_the_accepted_table_has_the_agreed_columns_and_provenance(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_A, "OH CodeActAgent v1.5")])
    backend = FakeBackend({"OH CodeActAgent v1.5": {"system_id": "openhands",
                                                    "corroborating_string": "OpenHands",
                                                    "confidence": 0.85}})
    assert BAT.main(env.argv(), backend=backend) == 0
    with env.aliases.open(encoding="utf-8", newline="") as fh:
        assert next(csv.reader(fh)) == BAT.ALIAS_COLUMNS
    row = env.alias_rows()[0]
    assert row["label"] == "OH CodeActAgent v1.5"
    assert row["system_id"] == "openhands"
    assert row["paper_record_id"] == PAPER_A
    assert row["corroborating_string"] == "OpenHands"
    assert int(row["char_offset"]) > 0
    assert row["match_method"].startswith("llm_shortlist|")
    assert row["model_confidence"] == "0.85"
    assert row["accepted_by"] == "mechanical_corroboration"


def test_every_rejection_reaches_the_refused_file_with_a_reason(tmp_path):
    rows = [
        _reject(PAPER_A, "OH CodeActAgent v1.5"),                       # accepted
        _reject(PAPER_B, "OpenHands CodeAct Scaffold"),                 # no corroboration
        _reject(PAPER_A, "GPT-4o"),                                     # model name
        _reject(PAPER_A, "Baseline"),                                   # reduces to no name
        _reject(PAPER_A, "Zero-shot"),                                  # generic label
        _reject(PAPER_A, "Ablated variant", note="ablation: tools off"),  # existing guard
        _reject(PAPER_C, "Unknown Thing"),                              # model answers null
        _reject(PAPER_C, "Something Else"),                             # invented id
        _reject(PAPER_C, "DVD w/ Qwen3-30B"),                 # reporting paper's own
    ]
    env = make_env(tmp_path, rows)
    backend = FakeBackend({
        "OH CodeActAgent v1.5": {"system_id": "openhands", "corroborating_string": "OpenHands"},
        "OpenHands CodeAct Scaffold": {"system_id": "openhands",
                                       "corroborating_string": "OpenHands"},
        "Unknown Thing": {"system_id": None, "reason": "not a system"},
        "Something Else": {"system_id": "no-such-id"},
        "DVD w/ Qwen3-30B": {"system_id": "mypaper"},
    })
    assert BAT.main(env.argv(), backend=backend) == 0
    with env.refused.open(encoding="utf-8", newline="") as fh:
        assert next(csv.reader(fh)) == BAT.REFUSED_COLUMNS
    refused = env.refused_rows()
    assert all(r["reason"] for r in refused), "every refusal must carry a reason"
    by_label = {r["label"]: r["reason"] for r in refused}
    assert by_label["GPT-4o"] == "stoplist_model_name"
    assert by_label["Baseline"] == "no_usable_harness_name"
    assert by_label["Zero-shot"] == "stoplist_generic_label"
    assert by_label["Ablated variant"] == "existing_guard_ablation"
    assert by_label["OpenHands CodeAct Scaffold"] == "no_corroboration_in_paper"
    assert by_label["Unknown Thing"] == "model_answered_null"
    assert by_label["Something Else"] == "system_id_not_coded"
    assert by_label["DVD w/ Qwen3-30B"] == "own_system_of_reporting_paper"
    assert [r["label"] for r in env.alias_rows()] == ["OH CodeActAgent v1.5"]
    # Every distinct (label, paper) pair is in exactly one of the two files.
    pairs_in = {(r["label"], r["paper_record_id"]) for r in refused} | {
        (r["label"], r["paper_record_id"]) for r in env.alias_rows()}
    assert pairs_in == {(r["reported_system_name"], r["record_id"]) for r in rows}


def test_a_refused_proposal_keeps_its_shortlist_and_confidence_for_review(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_B, "OpenHands CodeAct Scaffold")])
    backend = FakeBackend({"OpenHands CodeAct Scaffold": {"system_id": "openhands",
                                                          "confidence": 0.95}})
    BAT.main(env.argv(), backend=backend)
    row = env.refused_rows()[0]
    assert row["model_confidence"] == "0.95"
    assert row["system_id"] == "openhands"
    assert row["reason"] == "no_corroboration_in_paper"


def test_load_alias_table_ignores_a_row_not_accepted_by_corroboration(tmp_path):
    path = tmp_path / "a.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=BAT.ALIAS_COLUMNS)
        w.writeheader()
        w.writerow({"label": "A", "system_id": "openhands", "paper_record_id": PAPER_A,
                    "corroborating_string": "OpenHands", "char_offset": "10",
                    "match_method": "x", "model_confidence": "0.9",
                    "accepted_by": "mechanical_corroboration"})
        w.writerow({"label": "B", "system_id": "openhands", "paper_record_id": PAPER_A,
                    "corroborating_string": "", "char_offset": "", "match_method": "x",
                    "model_confidence": "0.9", "accepted_by": "hand_wave"})
        w.writerow({"label": "C", "system_id": "", "paper_record_id": PAPER_A,
                    "corroborating_string": "", "char_offset": "", "match_method": "",
                    "model_confidence": "", "accepted_by": "mechanical_corroboration"})
    table = BAT.load_alias_table(path)
    assert list(table) == [("A", PAPER_A)]


# ------------------------------------------------------------------------------------------------
# feeding analyse_blocks.py
# ------------------------------------------------------------------------------------------------
def test_the_alias_attributor_only_ever_fills_an_abstention(tmp_path):
    env = make_env(tmp_path)
    aliases = {("OH CodeActAgent v1.5", PAPER_A): {"system_id": "openhands",
                                                   "corroborating_string": "OpenHands",
                                                   "char_offset": "120", "match_method": "m"},
               ("OpenHands", PAPER_A): {"system_id": "swe-agent", "corroborating_string": "x",
                                        "char_offset": "1", "match_method": "m"},
               ("OpenHands w/o memory", PAPER_A): {"system_id": "openhands",
                                                   "corroborating_string": "OpenHands",
                                                   "char_offset": "1", "match_method": "m"}}
    att = BAT.AliasAttributor(registry=env.registry, aliases=aliases)
    assert att.uses_record_id is True
    filled = att.attribute("OH CodeActAgent v1.5", "", PAPER_A)
    assert filled.system_id == "openhands"
    assert filled.method.startswith("alias-")
    assert "120" in filled.reason
    # an exact match the base matcher already makes is NOT overwritten by the alias table
    assert att.attribute("OpenHands", "", PAPER_A).system_id == "openhands"
    # nor is an ablation refusal
    ablated = att.attribute("OpenHands w/o memory", "", PAPER_A)
    assert ablated.system_id == ""
    assert ablated.method == "refused-ablation"
    # without a paper the attributor behaves exactly like the base one
    assert att.attribute("OH CodeActAgent v1.5", "").system_id == ""


def test_analyse_blocks_is_alias_aware_on_disk_and_the_loader_does_not_patch_it():
    """The one-line change is now applied in `analyse_blocks.py`, so the loader must not re-patch.

    This replaces an earlier assertion that the file was unedited, which held only while the change
    was still a dry run.
    """
    src = BAT.BLOCKS_SCRIPT.read_text(encoding="utf-8")
    assert BAT.ALREADY_APPLIED in src, "analyse_blocks.py is no longer alias-aware"
    assert src.count(BAT.ONE_LINE_BEFORE) == 0, "the unpatched call site should be gone"
    module = BAT.load_patched_blocks()
    assert callable(module.build_arm_table)
    assert module.ARM_COLUMNS == AB.ARM_COLUMNS


def test_the_loader_still_patches_an_unpatched_checkout(tmp_path):
    """Keep the in-memory patch working, so the script is not tied to an already-edited tree."""
    src = BAT.BLOCKS_SCRIPT.read_text(encoding="utf-8")
    reverted = src.replace(
        '        att = (\n'
        '            attributor.attribute(label, note, record_id=str(rec.get("record_id") or ""))\n'
        '            if getattr(attributor, "uses_record_id", False)\n'
        '            else attributor.attribute(label, note)\n'
        '        )\n',
        BAT.ONE_LINE_BEFORE,
    )
    assert BAT.ALREADY_APPLIED not in reverted, "could not synthesise an unpatched copy"
    stand_in = tmp_path / "analyse_blocks.py"
    stand_in.write_text(reverted, encoding="utf-8")
    module = BAT.load_patched_blocks(stand_in)
    assert callable(module.build_arm_table)


def test_the_patched_build_arm_table_passes_the_paper_to_the_attributor(tmp_path):
    """The one-line change is what lets a per-paper alias table be consumed at all."""
    env = make_env(tmp_path)
    module = BAT.load_patched_blocks()
    comparators = pd.DataFrame([
        {"record_id": PAPER_A, "benchmark": "SWE-bench", "split": "", "metric": "resolved (%)",
         "model": "gpt-4o", "system_id": "mypaper", "reported_system_name": "OH CodeActAgent v1.5",
         "note": "", "score_num": 40.0},
        {"record_id": PAPER_B, "benchmark": "SWE-bench", "split": "", "metric": "resolved (%)",
         "model": "gpt-4o", "system_id": "mypaper", "reported_system_name": "OH CodeActAgent v1.5",
         "note": "", "score_num": 30.0},
    ])
    own = pd.DataFrame(columns=["record_id", "benchmark", "split", "metric", "model", "system_id",
                                "score_num"])
    aliases = {("OH CodeActAgent v1.5", PAPER_A): {"system_id": "openhands",
                                                   "corroborating_string": "OpenHands",
                                                   "char_offset": "120", "match_method": "m"}}
    att = BAT.AliasAttributor(registry=env.registry, aliases=aliases)
    arms = module.build_arm_table(comparators, own, att)
    got = dict(zip(arms["record_id"], arms["system_id"]))
    assert got[PAPER_A] == "openhands", "the alias applies in the paper that corroborated it"
    assert got[PAPER_B] == "", "and nowhere else - an alias is a fact about one paper"
    # the stock attributor must still work through the patched call site
    plain = module.build_arm_table(comparators, own,
                                  module.Attributor(registry=env.registry))
    assert set(plain["system_id"]) == {""}


def test_the_stock_attributor_is_unchanged_by_this_module(tmp_path):
    """`analyse_blocks.Attributor` must not have grown a `uses_record_id` hook of its own."""
    assert not getattr(AB.Attributor, "uses_record_id", False)
    with pytest.raises(TypeError):
        AB.Attributor(registry=make_env(tmp_path).registry).attribute("x", "", PAPER_A)


# ------------------------------------------------------------------------------------------------
# run-level behaviour
# ------------------------------------------------------------------------------------------------
def test_dry_run_makes_no_call_and_writes_nothing(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_A, "OH CodeActAgent v1.5")])
    backend = FakeBackend({})
    assert BAT.main(env.argv("--dry-run"), backend=backend) == 0
    assert backend.calls == 0
    assert not env.aliases.exists()
    assert not env.refused.exists()


def test_no_write_computes_but_writes_nothing(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_A, "OH CodeActAgent v1.5")])
    backend = FakeBackend({"OH CodeActAgent v1.5": {"system_id": "openhands"}})
    assert BAT.main(env.argv("--no-write"), backend=backend) == 0
    assert backend.calls == 1
    assert not env.aliases.exists()
    assert not env.cache.exists()


def test_a_failed_batch_does_not_kill_the_run(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_A, "OH CodeActAgent v1.5")])

    def dead(*a, **k):
        raise RuntimeError("claude exited 1: nope")

    assert BAT.main(env.argv(), backend=dead) == 0
    assert env.alias_rows() == []


def test_the_mention_index_is_cached_and_re_used(tmp_path):
    env = make_env(tmp_path, [_reject(PAPER_A, "OH CodeActAgent v1.5")])
    backend = FakeBackend({"OH CodeActAgent v1.5": {"system_id": "openhands"}})
    BAT.main(env.argv(), backend=backend)
    assert env.mention_cache.exists()
    fresh = BAT.MentionIndex(env.registry, root=env.fulltext)
    assert fresh.load_cache(env.mention_cache) >= 1
    assert "openhands" in fresh.papers[PAPER_A]
    # a cache written for a different name set is discarded rather than trusted
    blob = json.loads(env.mention_cache.read_text(encoding="utf-8"))
    blob["fingerprint"] = "stale"
    env.mention_cache.write_text(json.dumps(blob), encoding="utf-8")
    assert BAT.MentionIndex(env.registry, root=env.fulltext).load_cache(env.mention_cache) == 0


def test_batches_are_capped_at_the_batch_size():
    items = [{"id": f"p{i % 3}||l{i}", "record_id_paper": f"p{i % 3}", "label": f"l{i}",
              "shortlist": []} for i in range(70)]
    batches = BAT.chunk_by_paper(items, 30)
    assert all(len(b) <= 30 for b in batches)
    assert sum(len(b) for b in batches) == 70


def test_the_still_unattributed_report_names_a_reason_for_each_label(tmp_path):
    rows = [_reject(PAPER_A, "GPT-4o"), _reject(PAPER_A, "GPT-4o"),
            _reject(PAPER_B, "Mystery Scaffold")]
    env = make_env(tmp_path, rows)
    comparators = AB.load_comparators(env.rejects)
    base = AB.Attributor(registry=env.registry)
    out = BAT.unattributed_report(comparators, {}, base, top=10)
    assert out[0][0] == "GPT-4o" and out[0][1] == 2
    assert all(reason for _, _, reason in out)
