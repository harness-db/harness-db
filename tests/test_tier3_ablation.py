"""Tests for the Tier 3 controlled ablation (``scripts/tier3_ablation.py``).

No network and no model calls: every test injects a fake backend with the signature of
``screen_llm.vote_batch_claude_code``, and every usage-limit test injects a fake sleeper, so nothing
here waits on a clock or on a subscription.

The invariants under test are the ones that would silently invalidate the experiment if they broke:
arm C's per-instance call match to arm B, the impossibility of the harness reading a hidden check,
partial credit, a killed infinite loop, a crashed instance that does not abort the run, resume
without double counting, and the single shared generation path.
"""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import screen_llm
import tier3_ablation as t3

ADD_CODE = "def add(a, b):\n    return a + b\n"
BAD_CODE = "def add(a, b):\n    return a - b\n"
LOOP_CODE = "def add(a, b):\n    while True:\n        pass\n"


# ---------------------------------------------------------------- fixtures and fakes


def instance(iid: str = "fake/1") -> t3.Instance:
    return t3.Instance(id=iid, suite="fake", visible_prompt="Add two numbers a and b.",
                       entry_point="add")


def checks(iid: str = "fake/1") -> t3.HiddenChecks:
    return t3.HiddenChecks(iid, "asserts", {
        "asserts": ["assert add(1, 2) == 3", "assert add(-4, 4) == 0", "assert add(7, 5) == 12",
                    "assert add(0, 0) == 0"],
        "imports": [], "entry_point": "add"}, 4)


def fake_suite(n: int = 3) -> t3.Suite:
    insts = [instance(f"fake/{i}") for i in range(n)]
    return t3.Suite("fake", insts, {i.id: checks(i.id) for i in insts})


class FakeBackend:
    """Same signature as ``screen_llm.vote_batch_claude_code``; returns queued answers."""

    def __init__(self, answers, checks_src="assert add(1, 1) == 2\n"):
        self.answers = list(answers)
        self.checks_src = checks_src
        self.calls: list[dict] = []

    def __call__(self, exe, model, system_file, batch, effort=None, schema=None, prompt=None,
                 text_json=False):
        text = prompt(batch) if prompt else ""
        self.calls.append({"prompt": text, "schema": schema, "model": model,
                           "text_json": text_json})
        code = self.answers[min(len(self.calls) - 1, len(self.answers) - 1)]
        if callable(code):
            code = code(len(self.calls) - 1, text)
        vote = {"record_id": batch[0]["id"], "code": code}
        if schema and "checks" in schema["properties"]["votes"]["items"]["properties"]:
            vote["checks"] = self.checks_src
        return screen_llm.BatchResult([vote], model or "fake-model", 10, 5, 0, 0, 0.0)


def gen_from(backend, model="fake-model", tmp_path: Path | None = None):
    sysfile = (tmp_path or Path(".")) / "system.txt"
    sysfile.write_text(t3.SYSTEM_PROMPT, encoding="utf-8")
    return t3.make_gen(backend, "claude", model, sysfile, sysfile.parent / "run.log",
                       sleeper=lambda _s: None)


# ---------------------------------------------------------------- hidden checks stay hidden


def test_prompt_builder_cannot_reach_the_hidden_tests():
    """The prompt builder takes an Instance; there is no parameter and no field for a check."""
    import inspect

    params = set(inspect.signature(t3.build_prompt).parameters) - {"inst"}
    # feedback_kind (amendment 12a) picks a template by name; it cannot carry text of its own
    assert params == {"with_checks", "feedback", "previous_code", "nonce", "feedback_kind"}
    fields = {f.name for f in __import__("dataclasses").fields(t3.Instance)}
    assert fields == {"id", "suite", "visible_prompt", "entry_point", "preamble"}
    # and the free-text parameters refuse a HiddenChecks rather than stringifying it into a prompt
    with pytest.raises(TypeError):
        t3.build_prompt(instance(), feedback=checks())
    with pytest.raises(TypeError):
        t3.build_prompt(checks())  # type: ignore[arg-type]


def test_no_hidden_check_appears_in_any_prompt_variant():
    t3.verify_no_leak(instance(), checks())


def test_a_hidden_test_leak_is_detected():
    """A task statement that quotes one of its own hidden checks must fail loudly."""
    leaky = t3.Instance(id="fake/1", suite="fake", entry_point="add",
                        visible_prompt="Add a and b. For example, assert add(1, 2) == 3.")
    with pytest.raises(t3.HiddenTestLeak):
        t3.verify_no_leak(leaky, checks())


def test_leak_detection_survives_reformatting():
    """The same check written with different punctuation is still a leak."""
    inst = t3.Instance(id="fake/1", suite="fake", entry_point="f",
                       visible_prompt="Example: f((3, 4, 5, 6), (5, 7, 4, 10)) -> (4, 5)")
    hidden = t3.HiddenChecks("fake/1", "io",
                             {"cases": [{"input": [[3, 4, 5, 6], [5, 7, 4, 10]], "expected": None}],
                              "atol": 0, "entry_point": "f"}, 1)
    with pytest.raises(t3.HiddenTestLeak):
        t3.verify_no_leak(inst, hidden)


def test_prepared_suite_load_enforces_the_invariant(tmp_path, monkeypatch):
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path)
    leaky = t3.Instance(id="fake/1", suite="fake", entry_point="add",
                        visible_prompt="Add a and b, e.g. assert add(1, 2) == 3")
    t3.save_suite(t3.Suite("fake", [leaky], {"fake/1": checks()}))
    with pytest.raises(t3.HiddenTestLeak):
        t3.load_suite("fake")


# ---------------------------------------------------------------- scoring


def test_scoring_gives_partial_credit():
    score = t3.score_candidate(BAD_CODE, checks(), timeout=30)
    assert (score.passed, score.total) == (1, 4)  # only add(0, 0) == 0 holds for subtraction
    assert score.fraction == pytest.approx(0.25)
    assert score.binary == 0
    full = t3.score_candidate(ADD_CODE, checks(), timeout=30)
    assert (full.passed, full.total, full.binary) == (4, 4, 1)
    assert full.fraction == 1.0


def test_an_infinite_loop_is_killed_and_scored_zero():
    score = t3.score_candidate(LOOP_CODE, checks(), timeout=5)
    assert score.timed_out and score.passed == 0
    assert score.total == 4, "a timeout must score 0/total, never 0/0"


def test_an_uncompilable_candidate_scores_zero_not_an_exception():
    score = t3.score_candidate("def add(a, b:\n", checks(), timeout=20)
    assert (score.passed, score.total) == (0, 4)


def test_generated_code_never_runs_in_the_parent_process():
    """A candidate that kills its interpreter must leave the runner alive."""
    score = t3.score_candidate("import os\nos._exit(7)\n", checks(), timeout=20)
    assert score.passed == 0 and score.total == 4


def test_the_sandbox_environment_carries_no_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-must-not-leak")
    assert "ANTHROPIC_API_KEY" not in t3.sandbox_env()


# ---------------------------------------------------------------- arms


def test_arm_c_matches_arm_b_call_count_on_the_same_instance(tmp_path):
    """B repairs three times; C then gets exactly three independent attempts."""
    backend = FakeBackend([BAD_CODE, BAD_CODE, ADD_CODE], checks_src="assert add(1, 1) == 2\n")
    gen = gen_from(backend, tmp_path=tmp_path)
    inst, hidden = instance(), checks()
    b = t3.run_arm("B", inst, hidden, gen=gen, k=4, timeout=30)
    assert b.calls == 3, "B stops on the first attempt whose own checks pass"
    c = t3.run_arm("C", inst, hidden, gen=gen, calls_required=b.calls, timeout=30)
    assert c.calls == b.calls == 3


def test_arm_c_matches_b_when_b_stops_early(tmp_path):
    """B's first attempt passes its own checks, so B spends 1 call and C must spend 1, not k."""
    backend = FakeBackend([ADD_CODE], checks_src="assert add(1, 1) == 2\n")
    gen = gen_from(backend, tmp_path=tmp_path)
    b = t3.run_arm("B", instance(), checks(), gen=gen, k=6, timeout=30)
    assert b.calls == 1 and b.stopped_early
    c = t3.run_arm("C", instance(), checks(), gen=gen, calls_required=b.calls, timeout=30)
    assert c.calls == 1


def test_arm_c_refuses_to_run_without_bs_count(tmp_path):
    gen = gen_from(FakeBackend([ADD_CODE]), tmp_path=tmp_path)
    with pytest.raises(ValueError, match="calls_required"):
        t3.run_arm("C", instance(), checks(), gen=gen, timeout=30)
    with pytest.raises(ValueError):
        t3.run_arm("C", instance(), checks(), gen=gen, calls_required=0, timeout=30)


def test_arm_a_is_exactly_one_call(tmp_path):
    gen = gen_from(FakeBackend([BAD_CODE, ADD_CODE]), tmp_path=tmp_path)
    a = t3.run_arm("A", instance(), checks(), gen=gen, k=5, timeout=30)
    assert a.calls == 1 and a.score.fraction == pytest.approx(0.25)


def test_arm_b_spends_k_at_most(tmp_path):
    gen = gen_from(FakeBackend([BAD_CODE]), tmp_path=tmp_path)
    b = t3.run_arm("B", instance(), checks(), gen=gen, k=3, timeout=30)
    assert b.calls == 3 and not b.stopped_early


def test_the_three_arms_share_one_generation_path(tmp_path, monkeypatch):
    """Every arm's model call goes through ``generate``; nothing else reaches a backend."""
    seen: list[str] = []
    real = t3.generate

    def spy(inst, **kw):
        seen.append(kw.get("nonce", ""))
        return real(inst, **kw)

    monkeypatch.setattr(t3, "generate", spy)
    backend = FakeBackend([BAD_CODE])
    gen = gen_from(backend, tmp_path=tmp_path)  # make_gen closes over t3.generate at call time
    t3.run_arm("A", instance(), checks(), gen=gen, timeout=30)
    t3.run_arm("B", instance(), checks(), gen=gen, k=2, timeout=30)
    t3.run_arm("C", instance(), checks(), gen=gen, calls_required=2, timeout=30)
    assert len(seen) == 5 == len(backend.calls), "1 (A) + 2 (B) + 2 (C) calls, all through generate"


def test_only_arm_b_is_asked_for_checks(tmp_path):
    backend = FakeBackend([ADD_CODE])
    gen = gen_from(backend, tmp_path=tmp_path)
    t3.run_arm("A", instance(), checks(), gen=gen, timeout=30)
    t3.run_arm("C", instance(), checks(), gen=gen, calls_required=1, timeout=30)
    for call in backend.calls:
        assert "checks" not in call["schema"]["properties"]["votes"]["items"]["properties"]
        assert "Do not write tests" in call["prompt"]
    t3.run_arm("B", instance(), checks(), gen=gen, k=1, timeout=30)
    assert "checks" in backend.calls[-1]["schema"]["properties"]["votes"]["items"]["properties"]


def test_arm_c_self_consistency_picks_the_majority(tmp_path):
    gen = gen_from(FakeBackend([ADD_CODE, BAD_CODE, ADD_CODE]), tmp_path=tmp_path)
    c = t3.run_arm("C", instance(), checks(), gen=gen, calls_required=3, timeout=30)
    assert c.selection.startswith("majority(2/3)") and c.score.fraction == 1.0


def test_arm_c_falls_back_to_the_last_attempt(tmp_path):
    """Three structurally different attempts: no majority exists, so C submits the last one."""
    answers = ["def add(a, b):\n    return b - a\n",
               "def add(a, b):\n    return int(a) + int(b)\n",
               "def add(a, b):\n    total = a + b\n    return total\n"]
    gen = gen_from(FakeBackend(answers), tmp_path=tmp_path)
    c = t3.run_arm("C", instance(), checks(), gen=gen, calls_required=3, timeout=30)
    assert c.selection == "last" and c.score.fraction == 1.0


def test_arm_b_without_model_written_checks_degenerates_to_one_call(tmp_path):
    """No checks means no failure signal: B stops, and the row says the checks never ran."""
    gen = gen_from(FakeBackend([BAD_CODE], checks_src=""), tmp_path=tmp_path)
    b = t3.run_arm("B", instance(), checks(), gen=gen, k=4, timeout=30)
    assert b.calls == 1 and b.self_checks[0]["ran"] is False


def test_the_repair_prompt_shows_the_failure_not_the_hidden_checks(tmp_path):
    backend = FakeBackend([BAD_CODE, ADD_CODE], checks_src="assert add(2, 2) == 4\n")
    gen = gen_from(backend, tmp_path=tmp_path)
    t3.run_arm("B", instance(), checks(), gen=gen, k=2, timeout=30)
    repair = backend.calls[1]["prompt"]
    assert "AssertionError" in repair
    normalised = t3._norm(repair)
    for fp in checks().fingerprints():
        assert fp not in normalised


# ---------------------------------------------------------------- the runner, rows and resume


def run_one(tmp_path, suite, inst, arms, backend, seed=1, rows_path=None, k=4):
    runs = rows_path or (tmp_path / "runs.jsonl")
    prior_rows = t3.read_rows(runs)
    return t3.run_instance(
        suite, inst, arms=arms, seed=seed, gen=gen_from(backend, tmp_path=tmp_path),
        out_path=runs, phase="test", model="fake-model", k=k, timeout=30,
        done=t3.done_keys(prior_rows), prior=t3.latest_ok(prior_rows)), runs


def test_run_instance_runs_b_before_c_and_records_the_match(tmp_path):
    suite = fake_suite(1)
    backend = FakeBackend([BAD_CODE, ADD_CODE])
    written, runs = run_one(tmp_path, suite, suite.instances[0], ["A", "B", "C"], backend)
    arms = [r["arm"] for r in written]
    assert arms == ["A", "B", "C"], "C can only be matched once B has run"
    by_arm = {r["arm"]: r for r in written}
    assert by_arm["C"]["calls"] == by_arm["B"]["calls"]
    assert by_arm["C"]["calls_matched_from"] == {"arm": "B", "calls": by_arm["B"]["calls"],
                                                 "source": "same-run"}
    assert len(t3.read_rows(runs)) == 3


def test_c_reads_bs_count_from_runs_jsonl_after_an_interrupted_run(tmp_path):
    """The count comes from the row B actually wrote, not from a constant or an average."""
    suite = fake_suite(1)
    inst = suite.instances[0]
    # arm A consumes the first answer, so B sees BAD, BAD, ADD and spends three calls
    written, runs = run_one(tmp_path, suite, inst, ["A", "B"],
                            FakeBackend([BAD_CODE, BAD_CODE, BAD_CODE, ADD_CODE]), k=3)
    b_calls = {r["arm"]: r for r in written}["B"]["calls"]
    assert b_calls == 3
    written2, _ = run_one(tmp_path, suite, inst, ["A", "B", "C"], FakeBackend([ADD_CODE]),
                          rows_path=runs, k=3)
    assert [r["arm"] for r in written2] == ["C"], "A and B are already done and are not re-run"
    assert written2[0]["calls"] == b_calls
    assert written2[0]["calls_matched_from"]["source"] == "runs.jsonl"


def test_c_is_skipped_rather_than_guessed_when_b_is_missing(tmp_path):
    suite = fake_suite(1)
    written, _ = run_one(tmp_path, suite, suite.instances[0], ["C"], FakeBackend([ADD_CODE]))
    assert written[0]["status"] == "skipped" and "cannot be matched" in written[0]["error"]


def test_a_crashed_instance_is_recorded_and_the_run_continues(tmp_path):
    suite = fake_suite(2)

    class Exploding(FakeBackend):
        def __call__(self, exe, model, system_file, batch, **kw):
            if batch[0]["id"] == "fake/0":
                raise RuntimeError("claude exited 1: transport failure")
            return super().__call__(exe, model, system_file, batch, **kw)

    runs = tmp_path / "runs.jsonl"
    backend = Exploding([ADD_CODE])
    gen = gen_from(backend, tmp_path=tmp_path)
    written = []
    for inst in suite.instances:
        written += t3.run_instance(suite, inst, arms=["A"], seed=1, gen=gen, out_path=runs,
                                   phase="test", model="fake-model", timeout=30)
    by_id = {r["instance_id"]: r for r in written}
    assert by_id["fake/0"]["status"] == "error" and "RuntimeError" in by_id["fake/0"]["error"]
    assert by_id["fake/1"]["status"] == "ok", "one broken instance must not abort the run"
    assert t3.done_keys(t3.read_rows(runs)) == {"fake|fake/1|A|1|fake-model"}


def test_resume_skips_completed_triples_and_never_double_counts(tmp_path):
    suite = fake_suite(2)
    runs = tmp_path / "runs.jsonl"
    for inst in suite.instances:
        run_one(tmp_path, suite, inst, ["A"], FakeBackend([ADD_CODE]), rows_path=runs)
    first = t3.read_rows(runs)
    assert len(first) == 2
    # a second pass over the same work writes nothing new
    for inst in suite.instances:
        written, _ = run_one(tmp_path, suite, inst, ["A"], FakeBackend([BAD_CODE]), rows_path=runs)
        assert written == []
    assert len(t3.read_rows(runs)) == 2
    # and a duplicated row (a crash between write and flush, replayed) is collapsed, not counted
    with runs.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(first[0]) + "\n")
    assert len(t3.read_rows(runs)) == 3
    assert len(t3.latest_ok(t3.read_rows(runs))) == 2
    scores = t3.write_scores_csv(t3.read_rows(runs), tmp_path / "scores.csv")
    assert len(scores.read_text(encoding="utf-8").strip().splitlines()) == 3  # header + 2 rows


def test_an_error_row_is_retried_but_an_ok_row_is_not(tmp_path):
    rows = [{"key": "s|i|A|1|m", "status": "error"},
            {"key": "s|i|B|1|m", "status": "ok", "calls": 2}]
    assert t3.done_keys(rows) == {"s|i|B|1|m"}


def test_a_truncated_last_row_is_ignored_not_fatal(tmp_path):
    runs = tmp_path / "runs.jsonl"
    runs.write_text('{"key": "a|b|A|1", "status": "ok", "score": 1.0}\n{"key": "a|b|B|1", "st',
                    encoding="utf-8")
    assert [r["key"] for r in t3.read_rows(runs)] == ["a|b|A|1"]


def test_rows_carry_what_the_protocol_asks_for(tmp_path):
    suite = fake_suite(1)
    written, _ = run_one(tmp_path, suite, suite.instances[0], ["A"], FakeBackend([ADD_CODE]))
    row = written[0]
    for key in ("prompts", "responses", "calls", "tokens_in", "tokens_out", "score", "model",
                "timestamp", "passed", "total", "binary", "prompt_sha", "protocol", "phase"):
        assert key in row, key
    blob = t3._norm(json.dumps(row))
    for fp in checks().fingerprints():
        assert fp not in blob, "a logged row must not contain a hidden check either"


# ---------------------------------------------------------------- usage limits


def test_a_usage_limit_pauses_and_then_succeeds(tmp_path):
    log_path = tmp_path / "run.log"
    log_path.write_text("You've hit your session limit - resets 2:50am\n", encoding="utf-8")
    slept: list[float] = []
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("claude result error_during_execution: usage limit reached")
        return "done"

    out = t3.with_limit_handling(flaky, log_path=log_path, label="x", default_wait=60,
                                 max_wait=120, sleeper=slept.append)
    assert out == "done" and slept and slept[0] <= 120


def test_an_exhausted_balance_stops_rather_than_looping(tmp_path):
    log_path = tmp_path / "run.log"
    log_path.write_text("your credit balance is too low\n", encoding="utf-8")
    slept: list[float] = []
    with pytest.raises(t3.CreditsExhausted):
        t3.with_limit_handling(lambda: (_ for _ in ()).throw(RuntimeError("400 billing")),
                              log_path=log_path, label="x", sleeper=slept.append)
    assert slept == [], "an exhausted balance never lifts, so it must not be waited out"


def test_a_usage_limit_during_a_run_leaves_finished_rows_intact(tmp_path):
    suite = fake_suite(1)
    runs = tmp_path / "runs.jsonl"
    (tmp_path / "run.log").write_text("your credit balance is too low\n", encoding="utf-8")

    class Dead(FakeBackend):
        def __call__(self, *a, **kw):
            raise RuntimeError("400 billing: credit balance")

    gen = gen_from(Dead([ADD_CODE]), tmp_path=tmp_path)
    with pytest.raises(t3.CreditsExhausted):
        t3.run_instance(suite, suite.instances[0], arms=["A"], seed=1, gen=gen, out_path=runs,
                        phase="test", model="fake", timeout=30)
    assert t3.read_rows(runs) == []


# ---------------------------------------------------------------- pools, suites, analysis


def test_the_pilot_pool_is_disjoint_from_the_confirmatory_pool():
    suite = t3.Suite("mbpp", [instance(f"mbpp/{i}") for i in range(300)], {})
    pilot = {i.id for i in t3.select_instances(suite, "pilot", 0)}
    conf = {i.id for i in t3.select_instances(suite, "confirmatory", 0)}
    assert pilot and conf and not (pilot & conf)
    assert pilot | conf == {i.id for i in suite.instances}
    assert t3.select_instances(suite, "pilot", 25) == t3.select_instances(suite, "pilot", 25)


def test_suite_builders_hold_every_check_back(tmp_path, monkeypatch):
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path)
    rows = [{"task_id": 11, "prompt": "Write a function to double a number.",
             "code": "def double(n):\n    return 2 * n", "test_imports": [],
             "test_list": ["assert double(3) == 6", "assert double(0) == 0",
                           "assert double(-2) == -4"]}]
    suite = t3.build_mbpp(rows)
    inst = suite.instances[0]
    assert "assert" not in inst.visible_prompt and "def double(n):" in inst.visible_prompt
    assert suite.hidden[inst.id].n_checks == 3
    t3.verify_no_leak(inst, suite.hidden[inst.id])
    assert t3.score_candidate("def double(n):\n    return 2 * n\n",
                              suite.hidden[inst.id], timeout=30).fraction == 1.0


BCB_ROW = {
    "task_id": "BigCodeBench/7", "entry_point": "task_func",
    "complete_prompt": ('def task_func(n):\n    """Double a number.\n\n    Args:\n'
                        '        n (int): the number.\n\n    Returns:\n        int: twice n.\n'
                        '    >>> task_func(3)\n    6\n    """\n'),
    "code_prompt": "def task_func(n):\n",
    "instruct_prompt": ("Double a number.\nThe function should output with:\n    int: twice n.\n"
                        "You should write self-contained code starting with:\n```\n"
                        "def task_func(n):\n```"),
    "canonical_solution": "    return 2 * n\n",
    "test": ("import unittest\nclass TestCases(unittest.TestCase):\n"
             "    def test_pos(self):\n        self.assertEqual(task_func(3), 6)\n"
             "    def test_zero(self):\n        self.assertEqual(task_func(0), 0)\n"),
}


def test_the_instruct_variant_shows_less_and_hides_the_same_checks(tmp_path, monkeypatch):
    """The Instruct presentation is a candidate, not a change of measurement.

    Same hidden tests, same scorer, same gold filter; only the amount of the specification the model
    is shown differs, which is what makes it a harder candidate under the unchanged criteria.
    """
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path)
    complete = t3.build_bigcodebench([BCB_ROW], name="bcb", timeout=30.0)
    instruct = t3.build_bigcodebench([BCB_ROW], name="bcb_i", variant="instruct", timeout=30.0)
    ci, ii = complete.instances[0], instruct.instances[0]
    assert ">>> task_func(3)" in ci.visible_prompt        # the worked example is shown ...
    assert ">>> task_func(3)" not in ii.visible_prompt    # ... and in Instruct it is not
    assert "def task_func(n):" in ii.visible_prompt
    assert complete.hidden[ci.id].payload == instruct.hidden[ii.id].payload
    assert complete.hidden[ci.id].n_checks == instruct.hidden[ii.id].n_checks == 2
    for suite, inst in ((complete, ci), (instruct, ii)):
        assert "assertEqual" not in inst.visible_prompt
        t3.verify_no_leak(inst, suite.hidden[inst.id])
    assert instruct.notes["variant"] == "instruct"


def test_an_unknown_bigcodebench_variant_is_refused():
    with pytest.raises(ValueError, match="variant"):
        t3.build_bigcodebench([BCB_ROW], name="bcb_x", variant="chatty")


def test_saved_and_reloaded_suites_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path)
    suite = fake_suite(2)
    t3.save_suite(suite)
    back = t3.load_suite("fake")
    assert [i.id for i in back.instances] == [i.id for i in suite.instances]
    assert back.hidden["fake/0"].payload == suite.hidden["fake/0"].payload


def test_arm_a_summary_reports_the_band_verdict_and_the_power_numbers():
    rows = []
    for i in range(12):
        for seed in (1, 2, 3):
            score = 0.4 + 0.02 * i + (0.05 if seed == 2 else 0.0)
            rows.append({"key": f"s|i{i}|A|{seed}|fake", "status": "ok", "suite": "s",
                         "arm": "A", "instance_id": f"i{i}", "seed": seed, "score": score,
                         "binary": 0, "model_requested": "fake", "model": "fake-1", "total": 10,
                         "calls": 1})
    out = t3.summarise_arm_a(rows)
    entry = out["suites"]["s@fake"]
    assert entry["n_instances"] == 12 and entry["seeds_per_instance"] == [3]
    assert 0.25 <= entry["arm_a_continuous"] <= 0.70 and entry["in_band"]
    assert out["selected"] == "s@fake"
    assert (out["selected_suite"], out["selected_model"]) == ("s", "fake")
    assert entry["seeds_s"] >= 3
    assert entry["power"]["rho=0.7"]["n_instances_80pct"] >= 2


def test_out_of_band_suites_are_reported_as_a_failed_experiment():
    rows = [{"key": f"s|i{i}|A|1|m", "status": "ok", "suite": "s", "arm": "A",
             "instance_id": f"i{i}", "seed": 1, "score": 0.95, "binary": 1,
             "model_requested": "m", "model": "m-1", "total": 4, "calls": 1} for i in range(8)]
    out = t3.summarise_arm_a(rows)
    assert not out["suites"]["s@m"]["in_band"]
    assert out["selected"] is None and "failed experiment" in out["verdict"]


def test_power_numbers_move_the_right_way():
    small = t3.sd_of_difference(var_between=0.05, var_run=0.01, rho=0.9, s=3)
    large = t3.sd_of_difference(var_between=0.05, var_run=0.01, rho=0.0, s=3)
    assert small < large
    assert t3.n_for_power(small) < t3.n_for_power(large)
    assert t3.mde(small, t3.n_for_power(small)) <= t3.TARGET_EFFECT + 1e-9
    assert t3.choose_seeds(0.0) == 3 and t3.choose_seeds(0.02) >= 3


# ---------------------------------------------------------------- the confirmatory guard


def test_the_confirmatory_run_refuses_without_the_registration_marker(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(t3, "REGISTRATION_MARKER", tmp_path / "REGISTERED.txt")
    backend = FakeBackend([ADD_CODE])
    rc = t3.main(["confirmatory", "--suites", "mbpp", "--n", "1"], backend=backend,
                 sleeper=lambda _s: None)
    assert rc == 2 and backend.calls == []
    assert "amendment 12" in capsys.readouterr().err


def test_the_pilot_runs_arm_a_only(tmp_path, monkeypatch):
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path / "suites")
    monkeypatch.setattr(t3, "PILOT_DIR", tmp_path / "pilot")
    monkeypatch.setattr(t3, "PILOT_SHARE", 100)  # put the two fake instances in the pilot pool
    (tmp_path / "suites").mkdir(parents=True)
    t3.save_suite(fake_suite(2))
    backend = FakeBackend([ADD_CODE])
    rc = t3.main(["pilot", "--suites", "fake", "--n", "2", "--seeds", "2", "--timeout", "30"],
                 backend=backend, sleeper=lambda _s: None)
    assert rc == 0
    rows = t3.read_rows(tmp_path / "pilot" / "runs.jsonl")
    assert len(rows) == 4 and {r["arm"] for r in rows} == {"A"}
    assert all(r["phase"] == "pilot" for r in rows)
    summary = json.loads((tmp_path / "pilot" / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["suites"]["fake@sonnet"]["arm_a_continuous"] == 1.0
    assert (tmp_path / "pilot" / "pilot_scores.csv").exists()


def test_a_row_from_another_tier_does_not_satisfy_resume(tmp_path):
    """The pilot compares tiers, so a haiku row must not count as a sonnet row and vice versa."""
    suite = fake_suite(1)
    inst = suite.instances[0]
    runs = tmp_path / "runs.jsonl"
    for tier in ("sonnet", "haiku"):
        rows = t3.read_rows(runs)
        written = t3.run_instance(suite, inst, arms=["A"], seed=1,
                                  gen=gen_from(FakeBackend([ADD_CODE]), model=tier,
                                               tmp_path=tmp_path),
                                  out_path=runs, phase="test", model=tier, timeout=30,
                                  done=t3.done_keys(rows), prior=t3.latest_ok(rows))
        assert len(written) == 1 and written[0]["model_requested"] == tier
    keys = t3.done_keys(t3.read_rows(runs))
    assert keys == {"fake|fake/0|A|1|sonnet", "fake|fake/0|A|1|haiku"}
    summary = t3.summarise_arm_a(t3.read_rows(runs))
    assert set(summary["suites"]) == {"fake@sonnet", "fake@haiku"}


def test_active_fraction_power_is_the_binding_constraint():
    """With B spending extra calls on few instances, the target can become unreachable."""
    low = t3.active_fraction_power(0.13)
    assert low["max_attainable_effect"] == pytest.approx(0.13)
    assert low["min_gain_on_active_instances"] == pytest.approx(0.07 / 0.13, rel=1e-6)
    assert 40 <= low["n_instances_80pct"] <= 80
    dead = t3.active_fraction_power(0.05)
    assert dead["min_gain_on_active_instances"] > 1.0, "unreachable at any sample size"
    high = t3.active_fraction_power(0.6)
    assert high["n_instances_80pct"] < low["n_instances_80pct"]


def test_arm_b_diagnostics_reports_the_active_fraction(tmp_path):
    """Arm-B rows yield p_active; an arm-A-only file yields nothing, and no B-C contrast is formed."""
    rows = []
    for i in range(10):
        calls = 2 if i < 3 else 1
        rows.append({"key": f"s|i{i}|B|1|m", "status": "ok", "suite": "s", "arm": "B",
                     "instance_id": f"i{i}", "seed": 1, "score": 0.5, "binary": 0, "calls": calls,
                     "model_requested": "m", "model": "m-1", "total": 4,
                     "self_checks": [{"attempt": 0, "ok": calls == 1, "ran": True}]})
    diag = t3.arm_b_diagnostics(rows)["s@m"]
    assert diag["p_active"] == pytest.approx(0.3)
    assert diag["call_distribution"] == {"1": 7, "2": 3}
    assert diag["calls_per_instance_seed_all_three_arms"] == pytest.approx(1 + 2 * 1.3)
    assert diag["power"]["min_gain_on_active_instances"] == pytest.approx(0.07 / 0.3)
    assert t3.arm_b_diagnostics([{**r, "arm": "A"} for r in rows]) == {}


def test_leak_detection_covers_the_prompt_as_actually_sent():
    """The attempt nonce is part of the real prompt, so the leak test must include it."""
    inst = t3.Instance(id="fake/1", suite="fake", entry_point="add",
                       visible_prompt="Add a and b. Attempt note: " + "assert add(1, 2) == 3")
    with pytest.raises(t3.HiddenTestLeak):
        t3.verify_no_leak(inst, checks())
    calls = []
    real = t3.build_prompt

    def spy(*a, **kw):
        calls.append(kw.get("nonce", ""))
        return real(*a, **kw)

    try:
        t3.build_prompt = spy
        t3.verify_no_leak(instance(), checks())
    finally:
        t3.build_prompt = real
    assert "7.3" in calls, "a prompt variant carrying the nonce must be checked"


def test_uninformative_fingerprints_are_not_treated_as_leaks():
    """`[[10]]` normalises to '10', which appears in any prompt; it is not a leak and must not fire."""
    inst = t3.Instance(id="io/1", suite="io", visible_prompt="Return n doubled.", entry_point="f")
    hidden = t3.HiddenChecks("io/1", "io", {"cases": [{"input": [[10]], "expected": 20}],
                                            "atol": 0, "entry_point": "f"}, 1)
    assert any(len(f) < t3.MIN_FINGERPRINT for f in hidden.fingerprints())
    t3.verify_no_leak(inst, hidden)  # must not raise
    # but a long, informative case that IS in the prompt still fires
    leaky = t3.Instance(id="io/1", suite="io", entry_point="f",
                        visible_prompt="Example: f([3141592, 2718281]) == [6283184, 5436562]")
    long_case = t3.HiddenChecks("io/1", "io", {
        "cases": [{"input": [[3141592, 2718281]], "expected": [6283184, 5436562]}],
        "atol": 0, "entry_point": "f"}, 1)
    with pytest.raises(t3.HiddenTestLeak):
        t3.verify_no_leak(leaky, long_case)


def test_the_confirmatory_path_works_once_registered(tmp_path, monkeypatch):
    """With the marker in place the three arms run on the confirmatory pool, into a temp tree.

    Proves the registered path is wired without running it for real: `TIER3` is redirected, so
    nothing lands in the repo's data/tier3/runs.jsonl and no real instance is scored.
    """
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path / "suites")
    monkeypatch.setattr(t3, "TIER3", tmp_path / "tier3")
    monkeypatch.setattr(t3, "REGISTRATION_MARKER", tmp_path / "REGISTERED.txt")
    monkeypatch.setattr(t3, "PILOT_SHARE", 0)  # every fake instance is confirmatory
    (tmp_path / "suites").mkdir(parents=True)
    (tmp_path / "REGISTERED.txt").write_text("osf.io/xxxxx 2026-09-25", encoding="utf-8")
    t3.save_suite(fake_suite(2))
    backend = FakeBackend([BAD_CODE, ADD_CODE])
    rc = t3.main(["confirmatory", "--suites", "fake", "--n", "2", "--seeds", "1", "--registered",
                  "--k", "2", "--timeout", "30"], backend=backend, sleeper=lambda _s: None)
    assert rc == 0
    rows = t3.read_rows(tmp_path / "tier3" / "runs.jsonl")
    assert {r["arm"] for r in rows} == {"A", "B", "C"}
    assert all(r["phase"] == "confirmatory" for r in rows)
    by = {(r["instance_id"], r["arm"]): r for r in rows}
    for iid in ("fake/0", "fake/1"):
        assert by[(iid, "C")]["calls"] == by[(iid, "B")]["calls"]
    assert (tmp_path / "tier3" / "instance_scores.csv").exists()


# ================================================================ amendment 12a (2026-09-25)
# Arms Bfix and Bext, the visible (public) checks, the v2 pilot. Every guard below is new in 12a.

PUBLIC_EXAMPLES = [
    {"source": "add(20, 22)\n", "want": "42\n", "exc_msg": ""},
    {"source": "add(-1, 1)\n", "want": "0\n", "exc_msg": ""},
]


def visible_for(iid: str = "fake/1") -> t3.VisibleChecks:
    return t3.VisibleChecks(iid, "doctest", [dict(e) for e in PUBLIC_EXAMPLES])


def test_the_v1_prompt_wording_is_untouched_by_the_amendment():
    """12a adds templates; it must not move a single byte of the v1 prompts."""
    assert t3.prompt_sha() == t3.PROMPT_SHA_V1 == "886978ae5bec746f"
    assert t3.prompt_sha_v2() != t3.prompt_sha()
    plain = t3.build_prompt(instance(), with_checks=True, feedback="boom", previous_code="x",
                            nonce="1.1")
    assert plain == t3.build_prompt(instance(), with_checks=True, feedback="boom",
                                    previous_code="x", nonce="1.1", feedback_kind="self")
    assert "Running your own checks against it" in plain
    with pytest.raises(ValueError, match="feedback_kind"):
        t3.build_prompt(instance(), feedback="x", feedback_kind="hidden")


def test_bfix_always_spends_exactly_k_calls_even_when_its_checks_pass(tmp_path):
    backend = FakeBackend([ADD_CODE], checks_src="assert add(1, 1) == 2\n")
    gen = gen_from(backend, tmp_path=tmp_path)
    b = t3.run_arm("Bfix", instance(), checks(), gen=gen, k=4, timeout=30)
    assert b.calls == 4 and not b.stopped_early
    assert [c["ok"] for c in b.self_checks] == [True] * 4
    # rounds after a pass show the review block, not the v1 repair block
    for call in backend.calls[1:]:
        assert "your own checks passed on it" in call["prompt"]
        assert "checks" in call["schema"]["properties"]["votes"]["items"]["properties"]


def test_bfix_feeds_failures_back_like_b_and_passes_into_review(tmp_path):
    backend = FakeBackend([BAD_CODE, ADD_CODE], checks_src="assert add(1, 1) == 2\n")
    gen = gen_from(backend, tmp_path=tmp_path)
    b = t3.run_arm("Bfix", instance(), checks(), gen=gen, k=3, timeout=30)
    assert b.calls == 3 and b.score.fraction == 1.0
    assert "Running your own checks against it" in backend.calls[1]["prompt"]  # after a failure
    assert "your own checks passed on it" in backend.calls[2]["prompt"]        # after a pass


def test_bext_first_prompt_is_byte_identical_to_arm_a(tmp_path):
    """So 'Bext repaired' is exactly 'an arm-A draw failed the public examples'."""
    backend = FakeBackend([ADD_CODE])
    gen = gen_from(backend, tmp_path=tmp_path)
    t3.run_arm("A", instance(), checks(), gen=gen, seed=3, timeout=30)
    t3.run_arm("Bext", instance(), checks(), gen=gen, seed=3, timeout=30, visible=visible_for())
    assert backend.calls[0]["prompt"] == backend.calls[1]["prompt"]
    assert backend.calls[0]["schema"] == backend.calls[1]["schema"]


def test_bext_repairs_on_public_failures_and_stops_when_they_pass(tmp_path):
    backend = FakeBackend([BAD_CODE, BAD_CODE, ADD_CODE])
    gen = gen_from(backend, tmp_path=tmp_path)
    b = t3.run_arm("Bext", instance(), checks(), gen=gen, k=4, timeout=30, visible=visible_for())
    assert b.calls == 3 and b.stopped_early and b.score.fraction == 1.0
    repair = backend.calls[1]["prompt"]
    assert "public examples were run against it" in repair and "Failed example" in repair
    assert "Do not write tests" in repair, "Bext never asks the model for checks"
    for fp in checks().fingerprints():
        assert fp not in t3._norm(repair)


def test_bext_without_public_examples_degenerates_to_one_call(tmp_path):
    gen = gen_from(FakeBackend([BAD_CODE]), tmp_path=tmp_path)
    empty = t3.VisibleChecks("fake/1", "doctest", [])
    b = t3.run_arm("Bext", instance(), checks(), gen=gen, k=4, timeout=30, visible=empty)
    assert b.calls == 1 and b.self_checks[0]["ran"] is False


def test_bext_refuses_to_run_without_its_visible_checks(tmp_path):
    gen = gen_from(FakeBackend([ADD_CODE]), tmp_path=tmp_path)
    with pytest.raises(ValueError, match="visible checks"):
        t3.run_arm("Bext", instance(), checks(), gen=gen, timeout=30)
    with pytest.raises(ValueError, match="do not belong"):
        t3.run_arm("Bext", instance(), checks(), gen=gen, timeout=30, visible=visible_for("x/9"))


def test_c_is_matched_to_whichever_b_variant_ran(tmp_path):
    suite = fake_suite(1)
    inst = suite.instances[0]
    vis = {inst.id: visible_for(inst.id)}
    runs = tmp_path / "runs.jsonl"
    # A takes the first answer; Bext then sees BAD, ADD and spends two calls
    written = t3.run_instance(suite, inst, arms=["A", "Bext", "C"], seed=1,
                              gen=gen_from(FakeBackend([ADD_CODE, BAD_CODE, ADD_CODE]),
                                           tmp_path=tmp_path),
                              out_path=runs, phase="test", model="m", timeout=30, visible=vis)
    by = {r["arm"]: r for r in written}
    assert set(by) == {"A", "Bext", "C@Bext"}
    assert by["C@Bext"]["calls"] == by["Bext"]["calls"] == 2
    assert by["C@Bext"]["calls_matched_from"] == {"arm": "Bext", "calls": 2, "source": "same-run"}
    assert by["Bext"]["protocol"] == by["C@Bext"]["protocol"] == t3.PROTOCOL_VERSION_V2
    assert by["A"]["protocol"] == t3.PROTOCOL_VERSION, "arm A is unchanged, so it stays v1"
    assert by["Bext"]["fired"] and by["Bext"]["repairs"] == 1 and by["Bext"]["visible_n_checks"] == 2
    blob = t3._norm(json.dumps(written))
    for fp in checks().fingerprints():
        assert fp not in blob
    # a resumed C matched to Bext reads Bext's count back from the file, never v1 B's
    rows = t3.read_rows(runs)
    again = t3.run_instance(suite, inst, arms=["A", "Bext", "C"], seed=1,
                            gen=gen_from(FakeBackend([ADD_CODE]), tmp_path=tmp_path),
                            out_path=runs, phase="test", model="m", timeout=30, visible=vis,
                            done=t3.done_keys(rows) - {"fake|fake/0|C@Bext|1|m"},
                            prior=t3.latest_ok(rows))
    assert [r["arm"] for r in again] == ["C@Bext"]
    assert again[0]["calls_matched_from"]["source"] == "runs.jsonl" and again[0]["calls"] == 2


def test_c_refuses_to_guess_between_two_b_variants(tmp_path):
    suite = fake_suite(1)
    with pytest.raises(ValueError, match="one B variant"):
        t3.run_instance(suite, suite.instances[0], arms=["B", "Bfix", "C"], seed=1,
                        gen=gen_from(FakeBackend([ADD_CODE]), tmp_path=tmp_path),
                        out_path=tmp_path / "r.jsonl", phase="test", model="m", timeout=30)
    assert t3.c_arm_label("B") == "C" and t3.c_arm_label("Bfix") == "C@Bfix"
    with pytest.raises(ValueError):
        t3.c_arm_label("C")


# ---------------------------------------------------------------- visible checks: never hidden ones


def test_visible_checks_are_parsed_from_the_docstring_and_never_from_the_hidden_test():
    """By construction: the parser takes the program stub only, and the builder uses the hidden test
    only to delete. A marker planted in the hidden test cannot reach the visible checks."""
    import inspect

    assert set(inspect.signature(t3.parse_docstring_examples).parameters) == {
        "program_stub", "entry_point"}
    stub = ('def task_func(n):\n    """Double n.\n\n    >>> task_func(21)\n    42\n'
            '    >>> task_func(0)\n    0\n    """\n')
    hidden = t3.HiddenChecks("bcb/1", "unittest", {"test": (
        "import unittest\nclass T(unittest.TestCase):\n    def test_marker(self):\n"
        "        self.assertEqual(task_func(123456789), 246913578)\n")}, 1)
    vis = t3.build_visible_checks("bcb/1", stub, "task_func", stub + "    return 2 * n\n",
                                  hidden=hidden, timeout=30)
    assert [e["source"] for e in vis.examples] == ["task_func(21)\n", "task_func(0)\n"]
    assert "123456789" not in vis.text() and "246913578" not in vis.text()
    parsed = {e["source"] for e in t3.parse_docstring_examples(stub, "task_func")}
    assert {e["source"] for e in vis.examples} <= parsed
    t3.verify_visible_disjoint(vis, hidden)


def test_a_public_example_that_the_hidden_test_also_asserts_is_withheld():
    """visible != hidden: an example whose expected value is a hidden assertion is dropped."""
    stub = ('def task_func(s):\n    """Title-case s.\n\n    >>> task_func("random time series")\n'
            "    'Random Time Series'\n    >>> task_func('ab')\n    'Ab'\n" + '    """\n')
    hidden = t3.HiddenChecks("bcb/2", "unittest", {"test": (
        "import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n"
        "        self.assertEqual(task_func('random time series'), 'Random Time Series')\n")}, 1)
    vis = t3.build_visible_checks("bcb/2", stub, "task_func", stub + "    return s.title()\n",
                                  hidden=hidden, timeout=30)
    assert vis.n_dropped_overlap == 1 and vis.n_checks == 1
    assert vis.examples[0]["want"] == "'Ab'\n"
    # and a hand-built visible set carrying the hidden value is refused outright
    leaky = t3.VisibleChecks("bcb/2", "doctest", [
        {"source": "task_func('random time series')\n", "want": "'Random Time Series'\n",
         "exc_msg": ""}])
    with pytest.raises(t3.HiddenTestLeak):
        t3.verify_visible_disjoint(leaky, hidden)


def test_public_examples_the_gold_solution_fails_are_dropped():
    """Same gold filter as the hidden tests: a kept example is one the reference passes here."""
    stub = ('def task_func(n):\n    """Double n.\n\n    >>> task_func(2)\n    4\n'
            '    >>> open("/no/such/file").read()\n    \'x\'\n    """\n')
    hidden = t3.HiddenChecks("bcb/3", "unittest", {"test": "import unittest\n"}, 1)
    vis = t3.build_visible_checks("bcb/3", stub, "task_func", stub + "    return 2 * n\n",
                                  hidden=hidden, timeout=30)
    assert [e["source"] for e in vis.examples] == ["task_func(2)\n"] and vis.n_dropped_gold == 1


def test_the_leak_check_covers_every_prompt_bext_and_bfix_can_send():
    """verify_no_leak now builds the review and public-examples prompts, and a repair prompt quoting
    every visible example; a hidden check reachable through any of them is caught."""
    seen: list[str] = []
    real = t3.build_prompt

    def spy(*a, **kw):
        seen.append(kw.get("feedback_kind", "self"))
        return real(*a, **kw)

    try:
        t3.build_prompt = spy
        t3.verify_no_leak(instance(), checks(), visible_for())
    finally:
        t3.build_prompt = real
    assert {"self", "review", "external"} <= set(seen) and seen.count("external") >= 2
    # a visible example that carries a hidden assert verbatim is refused through verify_no_leak too
    hidden = t3.HiddenChecks("fake/1", "asserts", {"asserts": ["assert add(1234, 4321) == 5555"],
                                                   "imports": [], "entry_point": "add"}, 1)
    bad = t3.VisibleChecks("fake/1", "doctest", [
        {"source": "assert add(1234, 4321) == 5555\n", "want": "", "exc_msg": ""}])
    with pytest.raises(t3.HiddenTestLeak):
        t3.verify_no_leak(instance(), hidden, bad)


def test_build_prompt_refuses_a_visible_checks_object():
    with pytest.raises(TypeError):
        t3.build_prompt(instance(), feedback=visible_for(), feedback_kind="external")


def test_public_examples_run_in_the_sandbox_and_report_failures():
    assert t3.run_visible_checks(ADD_CODE, visible_for(), timeout=30).ok
    bad = t3.run_visible_checks(BAD_CODE, visible_for(), timeout=30)
    assert not bad.ok and bad.ran and "Failed example" in bad.output and "Expected" in bad.output
    dead = t3.run_visible_checks("import os\nos._exit(3)\n", visible_for(), timeout=30)
    assert not dead.ok


def test_the_public_example_runner_sees_the_same_environment_as_the_hidden_scorer():
    """doctest drags in ssl; the runner must not let a candidate import what the scorer refuses."""
    code = "import asyncio\n" + ADD_CODE
    assert t3.score_candidate(code, checks(), timeout=30).passed == 0
    assert not t3.run_visible_checks(code, visible_for(), timeout=30).ok


def test_load_visible_rechecks_disjointness_and_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path)
    suite = fake_suite(2)
    t3.save_suite(suite)
    good = {i.id: visible_for(i.id) for i in suite.instances}
    t3.save_visible("fake", good, {})
    assert set(t3.load_visible("fake", suite)) == {"fake/0", "fake/1"}
    # a tampered file that now carries a hidden check is refused on load
    tampered = dict(good)
    tampered["fake/0"] = t3.VisibleChecks("fake/0", "doctest", [
        {"source": "assert add(-4, 4) == 0\n", "want": "", "exc_msg": ""}])
    t3.save_visible("fake", tampered, {})
    with pytest.raises(t3.HiddenTestLeak):
        t3.load_visible("fake", suite)
    # and a file missing an instance is refused rather than silently giving it no checks
    t3.save_visible("fake", {"fake/0": good["fake/0"]}, {})
    with pytest.raises(ValueError, match="no visible-check entry"):
        t3.load_visible("fake", suite)


# ---------------------------------------------------------------- the v2 pilot and its guards


def v2_suite(tmp_path, monkeypatch, n=2):
    monkeypatch.setattr(t3, "SUITES_DIR", tmp_path / "suites")
    monkeypatch.setattr(t3, "TIER3", tmp_path / "tier3")
    monkeypatch.setattr(t3, "PILOT_DIR", tmp_path / "tier3" / "pilot")
    monkeypatch.setattr(t3, "V2_PILOT_DIR", tmp_path / "tier3" / "pilot_v2")
    monkeypatch.setattr(t3, "REGISTRATION_MARKER", tmp_path / "tier3" / "REGISTERED.txt")
    (tmp_path / "suites").mkdir(parents=True)
    suite = fake_suite(n)
    t3.save_suite(suite)
    t3.save_visible("fake", {i.id: visible_for(i.id) for i in suite.instances}, {})
    return suite


def test_the_v2_pilot_refuses_arm_c(tmp_path, monkeypatch):
    v2_suite(tmp_path, monkeypatch)
    backend = FakeBackend([ADD_CODE])
    for arms in ("B,C", "Bext,C@Bext", "C"):
        rc = t3.main(["pilot-v2", "--suites", "fake", "--arms", arms], backend=backend,
                     sleeper=lambda _s: None)
        assert rc == 2
    assert backend.calls == []


def test_the_v2_pilot_refuses_the_confirmatory_tree_and_the_v1_pilot(tmp_path, monkeypatch):
    v2_suite(tmp_path, monkeypatch)
    backend = FakeBackend([ADD_CODE])
    for out in (tmp_path / "tier3", tmp_path / "tier3" / "pilot"):
        rc = t3.main(["pilot-v2", "--suites", "fake", "--out-dir", str(out)], backend=backend,
                     sleeper=lambda _s: None)
        assert rc == 2
    assert backend.calls == []


def test_the_v2_pilot_touches_the_pilot_pool_only_and_never_registers(tmp_path, monkeypatch):
    suite = v2_suite(tmp_path, monkeypatch, n=40)
    pilot_ids = {i.id for i in t3.select_instances(suite, "pilot", 0)}
    assert pilot_ids and len(pilot_ids) < 40
    rc = t3.main(["pilot-v2", "--suites", "fake", "--arms", "A,B,Bfix,Bext", "--n", "0",
                  "--k", "2", "--timeout", "30"], backend=FakeBackend([BAD_CODE, ADD_CODE]),
                 sleeper=lambda _s: None)
    assert rc == 0
    rows = t3.read_rows(tmp_path / "tier3" / "pilot_v2" / "runs.jsonl")
    assert {r["instance_id"] for r in rows} == pilot_ids
    assert {r["arm"] for r in rows} == {"A", "B", "Bfix", "Bext"}
    assert all(r["phase"] == "pilot-v2" for r in rows)
    assert not (tmp_path / "tier3" / "REGISTERED.txt").exists()
    assert not (tmp_path / "tier3" / "runs.jsonl").exists()
    assert t3.phase_pool("pilot-v2") == "pilot" and t3.phase_pool("confirmatory") == "confirmatory"


def test_the_v2_report_is_descriptive_and_forms_no_contrast(tmp_path, monkeypatch):
    v2_suite(tmp_path, monkeypatch, n=40)
    t3.main(["pilot-v2", "--suites", "fake", "--arms", "B,Bfix,Bext", "--n", "0", "--k", "2",
             "--timeout", "30"], backend=FakeBackend([BAD_CODE, ADD_CODE]),
            sleeper=lambda _s: None)
    rc = t3.main(["report-v2", "--no-visible", "--a-runs", str(tmp_path / "none.jsonl")])
    assert rc == 0
    summary = json.loads((tmp_path / "tier3" / "pilot_v2" / "pilot_v2_summary.json")
                         .read_text(encoding="utf-8"))
    assert summary["no_contrast"] is True
    cells = summary["cells"]
    assert {c["arm"] for c in cells.values()} == {"B", "Bfix", "Bext"}
    fix = next(c for c in cells.values() if c["arm"] == "Bfix")
    assert fix["p_active"] == 1.0 and fix["mean_calls"] == 2.0
    blob = json.dumps(summary).lower()
    for word in ("contrast_estimate", "difference", "effect_estimate", "b_minus"):
        assert word not in blob


def test_firing_power_divides_the_stratum_n_by_the_firing_rate():
    full = t3.firing_power(1.0, var_between=0.08, var_run=0.04, s=12)
    half = t3.firing_power(0.5, var_between=0.08, var_run=0.04, s=12)
    for rho in ("rho=0.0", "rho=0.7", "rho=0.9"):
        assert full[rho]["n_instances_to_run"] == full[rho]["n_firing_instances"]
        assert half[rho]["n_instances_to_run"] == math.ceil(half[rho]["n_firing_instances"] / 0.5)
    assert full["rho=0.7"]["n_firing_instances"] < full["rho=0.0"]["n_firing_instances"]


def test_the_confirmatory_run_still_refuses_for_every_b_variant(tmp_path, monkeypatch):
    monkeypatch.setattr(t3, "REGISTRATION_MARKER", tmp_path / "REGISTERED.txt")
    backend = FakeBackend([ADD_CODE])
    for b in ("B", "Bfix", "Bext"):
        rc = t3.main(["confirmatory", "--suites", "fake", "--n", "1", "--b-arm", b],
                     backend=backend, sleeper=lambda _s: None)
        assert rc == 2
    assert backend.calls == [] and not (tmp_path / "REGISTERED.txt").exists()


def test_disjointness_is_by_task_across_presentations():
    """Amendment 12a s.5: a task piloted under one suite name is not confirmatory under another."""
    assert t3.task_key("bigcodebench_hard_instruct/19") == t3.task_key("bigcodebench/19")
    assert t3.task_key("bigcodebench_hard/19") == "bigcodebench/19"
    assert t3.task_key("mbppplus/11") == t3.task_key("mbpp/11") == "mbpp/11"
    assert t3.task_key("bigcodebench/19") != t3.task_key("bigcodebench/190")


def test_confirmatory_selection_drops_every_task_any_pilot_touched(tmp_path):
    insts = [t3.Instance(id=f"bigcodebench_instruct/{i}", suite="bigcodebench_instruct",
                         visible_prompt="x", entry_point="task_func") for i in range(200)]
    suite = t3.Suite("bigcodebench_instruct", insts, {})
    conf = t3.select_instances(suite, "confirmatory", 0)
    victim = conf[0].id.rsplit("/", 1)[-1]
    pilot_dir = tmp_path / "other"
    t3.append_row(pilot_dir / "runs.jsonl", {  # piloted under a *different* presentation
        "key": "k", "status": "ok", "instance_id": f"bigcodebench_hard/{victim}"})
    piloted = t3.piloted_tasks([pilot_dir])
    assert piloted == {f"bigcodebench/{victim}"}
    clean = t3.confirmatory_instances(suite, 0, piloted)
    assert conf[0] not in clean and len(clean) == len(conf) - 1
    assert all(t3.pool_of(suite.name, i.id) == "confirmatory" for i in clean)
