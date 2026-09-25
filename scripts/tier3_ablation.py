#!/usr/bin/env python3
"""Tier 3 controlled ablation of self-verification: arms A / B / C, exactly as pre-registered.

Implements `docs/tier3_ablation_protocol.md` (OSF amendment 12). Read that document, not this
docstring, for why the design is what it is. What this module guarantees, mechanically:

* **One generation path.** `generate()` is the only function that talks to a model. Arms A, B and C
  differ only in how many times it is called and in what is done between calls, so they cannot
  drift apart.
* **C is matched to B per instance.** `run_instance()` runs B first, records `calls_used`, and
  passes that integer into C on that same instance (or reads it back from `runs.jsonl` when B was
  completed by an earlier, interrupted run). C cannot be started without it: `run_arm("C", ...)`
  raises when `calls_required` is None.
* **The harness never sees the hidden checks.** `Instance` carries only what the model may read;
  `HiddenChecks` lives in a separate structure, keyed by instance id, and `build_prompt()` accepts
  an `Instance` and nothing else. `verify_no_leak()` re-checks every instance at suite load time by
  searching the built prompts (all variants, including the repair variant) for a normalised
  fingerprint of every hidden check, and raises `HiddenTestLeak` if one is present.
* **No Anthropic API.** Model access is the subscription path only, through
  `screen_llm.vote_batch_claude_code` (`claude -p --output-format json`). There is no API backend
  here and no use of `ANTHROPIC_API_KEY`; the key is actively stripped from the sandbox environment.
* **Resumability over speed.** One JSON line per (suite, instance, arm, seed, model) is appended to
  `runs.jsonl` as it completes. A re-run skips finished triples and never double-counts them.
  Usage limits pause the run (`scripts/phase4_autopilot.py::reset_wait`); an exhausted balance stops
  it (`credits_exhausted`). Neither corrupts the file: rows are only ever appended, complete.

**The sandbox is a benchmark-runner sandbox, not a security boundary.** Model-generated code for
benign coding tasks is executed in a subprocess, in a fresh temporary working directory, with a
minimal environment (no API keys, no proxy variables), with `socket` stubbed out so a candidate
cannot reach the network by accident, and under a hard timeout that kills the whole process tree.
That is enough to keep an infinite loop or a stray file write from spoiling a benchmark row. It is
*not* a sandbox for hostile code: a determined escape is trivial. Do not point this at untrusted
tasks or untrusted models.

One thing the protocol fixes that is worth stating here, because it is a limit of the design rather
than of this code: the arms are matched on **call count**, which is what the protocol's arm table
specifies ("exactly the number B used on that instance"). They are not matched on tokens - B's calls
carry the checks it writes and the failure text it reads back - so every row records `tokens_in` and
`tokens_out` and the token asymmetry can be measured rather than assumed away.

Usage
-----
    python scripts/tier3_ablation.py prepare --suite all
    python scripts/tier3_ablation.py pilot --suites mbpp,mbppplus,bigcodebench_hard --n 25
    python scripts/tier3_ablation.py report [--runs <runs.jsonl>]
    python scripts/tier3_ablation.py confirmatory ...   # refuses without the registration marker

Amendment 12a (2026-09-25) adds arm variants Bfix and Bext, public checks for Bext, and a pilot
that runs arm A and the B variants only (no arm C, so no contrast can be formed from it):

    python scripts/tier3_ablation.py prepare-visible --suite bigcodebench_hard_instruct
    python scripts/tier3_ablation.py pilot-v2 --suites bigcodebench_hard_instruct --arms B,Bfix,Bext
    python scripts/tier3_ablation.py report-v2

Outputs: `data/tier3/suites/` (prepared instances), `data/tier3/pilot/` (the pilot, never pooled
with the confirmatory run), `data/tier3/runs.jsonl` + `data/tier3/instance_scores.csv` (confirmatory).
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import gzip
import hashlib
import json
import logging
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

# reset_wait / credits_exhausted: the usage-limit plumbing. vote_batch_claude_code /
# find_claude_exe: the subscription backend. Imported after sys.path, so this runs as a script.
import phase4_autopilot
import screen_llm

TIER3 = REPO / "data" / "tier3"
SUITES_DIR = TIER3 / "suites"
RAW_DIR = SUITES_DIR / "raw"
PILOT_DIR = TIER3 / "pilot"
#: written by hand once amendment 12 is filed; `confirmatory` refuses to score an instance without it
REGISTRATION_MARKER = TIER3 / "REGISTERED.txt"

PROTOCOL_VERSION = "tier3-v1"
#: the pre-stated band from criterion 2 of the protocol (arm-A accuracy)
BAND = (0.25, 0.70)
#: the effect the confirmatory run must be able to see, in per-instance check-pass fraction
TARGET_EFFECT = 0.07

#: Amendment 12a (2026-09-25). Rows written by the v2 arm variants carry this protocol tag; rows of
#: the v1 arms (A, B, C matched to B) keep `tier3-v1`, because their behaviour is unchanged.
PROTOCOL_VERSION_V2 = "tier3-v2-12a"
#: The arm-B variants. "B" is the v1 arm exactly as registered ("B-self" in amendment 12a): the model
#: writes its own checks and the loop stops when they pass. "Bfix" runs mandatory verify-and-repair
#: rounds whatever its checks say. "Bext" verifies against the benchmark's public worked examples
#: (never the hidden tests) and stops when those pass.
B_ARMS = ("B", "Bfix", "Bext")
ARMS_V2 = ("A", "B", "Bfix", "Bext", "C")
#: the v2 pilot's output tree; never pooled with the v1 pilot or with any confirmatory run
V2_PILOT_DIR = TIER3 / "pilot_v2"

log = logging.getLogger("tier3")


# ======================================================================================
# Data model: what the model may read, and what it may not
# ======================================================================================


@dataclass(frozen=True)
class Instance:
    """Everything the harness is allowed to see about one task. No checks live here.

    The separation is structural, not a convention: `build_prompt()` takes an `Instance`, and an
    `Instance` has no field that could carry a check. The hidden checks for this instance are in a
    `HiddenChecks` in a different mapping, reachable only from the scorer.
    """

    id: str
    suite: str
    visible_prompt: str
    entry_point: str
    #: code the candidate is expected to complete or extend (already inside `visible_prompt`)
    preamble: str = ""


@dataclass(frozen=True)
class HiddenChecks:
    """The scoring checks for one instance. Never passed to a prompt builder or to a model.

    `kind` selects the runner:

    * ``asserts``  - `payload["asserts"]`: assert statements, each run in a fresh namespace.
    * ``io``       - `payload["cases"]`: ``{"input": ..., "expected": ...}`` pairs in tagged JSON,
      compared structurally with `payload["atol"]`.
    * ``unittest`` - `payload["test"]`: a `unittest.TestCase` source; one check per test method.
    """

    instance_id: str
    kind: str
    payload: dict[str, Any]
    n_checks: int

    def fingerprints(self) -> list[str]:
        """Normalised strings that must not appear in any prompt for this instance."""
        if self.kind == "asserts":
            return [_norm(a) for a in self.payload.get("asserts", [])]
        if self.kind == "io":
            out = []
            for c in self.payload.get("cases", []):
                out.append(_norm(json.dumps(c["input"], sort_keys=True)))
                out.append(_norm(json.dumps([c["input"], c.get("expected")], sort_keys=True)))
            return out
        if self.kind == "unittest":
            src = self.payload.get("test", "")
            return [_norm(src)] + [_norm(m) for m in _test_method_names(src)]
        raise ValueError(f"unknown hidden-check kind {self.kind!r}")


@dataclass
class Suite:
    """A prepared task suite: visible instances, and hidden checks keyed by instance id."""

    name: str
    instances: list[Instance]
    hidden: dict[str, HiddenChecks]
    notes: dict[str, Any] = field(default_factory=dict)

    def by_id(self, instance_id: str) -> Instance:
        for inst in self.instances:
            if inst.id == instance_id:
                return inst
        raise KeyError(instance_id)


@dataclass(frozen=True)
class VisibleChecks:
    """Public checks for one instance: the benchmark's own worked examples (amendment 12a, arm Bext).

    The opposite of `HiddenChecks` in intent: these are *meant* to be run by the harness and their
    failures shown to the model, which is what a harness does when it runs a repository's own test
    suite. Two properties keep them from becoming a back door to the hidden tests, and both are
    enforced rather than assumed:

    * **Source.** They are parsed from the task's docstring (`build_visible_checks` takes the program
      stub, never the hidden test), so their content is the benchmark's public specification.
    * **Disjointness.** Any example whose expected output also appears in the hidden test is withheld
      at build time, and `verify_visible_disjoint` re-checks that on every load, raising
      `HiddenTestLeak` if a visible check carries a hidden one.
    """

    instance_id: str
    kind: str
    examples: list[dict[str, str]] = field(default_factory=list)
    source: str = "docstring"
    n_parsed: int = 0
    n_dropped_gold: int = 0
    n_dropped_overlap: int = 0

    @property
    def n_checks(self) -> int:
        return len(self.examples)

    def text(self) -> str:
        """Everything in these checks that a model could ever be shown, as one string."""
        return "\n".join(f"{e.get('source', '')}\n{e.get('want', '')}\n{e.get('exc_msg', '')}"
                         for e in self.examples)


class HiddenTestLeak(RuntimeError):
    """A hidden check is visible in a prompt. Any run under this condition is invalid."""


class CreditsExhausted(RuntimeError):
    """The subscription/balance wall: unlike a usage limit, it never lifts on its own."""


_NORM_RE = re.compile(r"[^0-9a-z]+")


def _norm(text: str) -> str:
    """Lowercase, alphanumerics only.

    Leak detection has to survive reformatting: ``similar_elements((3, 4, 5, 6),(5, 7, 4, 10))`` in
    a task statement and ``[[3, 4, 5, 6], [5, 7, 4, 10]]`` in a check list are the same test written
    two ways, and a naive substring search over the raw text would miss it. Both normalise to a
    string containing ``345657410``, so containment catches it.
    """
    return _NORM_RE.sub("", (text or "").lower())


def _test_method_names(test_src: str) -> list[str]:
    return re.findall(r"def\s+(test\w*)\s*\(", test_src or "")


#: A normalised fingerprint shorter than this carries no information and would fire on almost any
#: prompt: the hidden input `[[10]]` normalises to `10`, and every prompt contains a `1` and a `0`
#: somewhere (the attempt nonce alone does). Such checks are therefore not leak-testable by
#: containment, and they are also not leakable in any meaningful sense - knowing that 10 might be an
#: input is not knowing what the function should return for it. Stated rather than hidden.
MIN_FINGERPRINT = 8


def verify_no_leak(inst: Instance, hidden: HiddenChecks,
                   visible: VisibleChecks | None = None) -> None:
    """Raise `HiddenTestLeak` if any hidden check for `inst` is readable from any prompt variant.

    Checks the prompt in every shape the runner can send it: plain, with the checks request, with a
    repair feedback block, and with an attempt nonce - the last because the nonce is text in the real
    prompt and a leak test that ignored part of the real prompt would be theatre.

    Amendment 12a adds two prompt shapes and one source of text, and all three are covered: the
    forced-review block of arm Bfix, the public-examples repair block of arm Bext, and - when the
    instance has visible checks - a repair prompt whose feedback is a failure report quoting *every*
    visible example, which is the most a Bext repair prompt can ever show. The visible checks must
    also be disjoint from the hidden ones (`verify_visible_disjoint`).
    """
    if hidden.instance_id != inst.id:
        raise ValueError(f"checks for {hidden.instance_id!r} do not belong to {inst.id!r}")
    code = "def f():\n    return None\n"
    variants = [
        build_prompt(inst),
        build_prompt(inst, with_checks=True),
        build_prompt(inst, nonce="7.3"),
        build_prompt(inst, with_checks=True, feedback="AssertionError: check 1 failed",
                     previous_code=code, nonce="7.3"),
        build_prompt(inst, with_checks=True, feedback="All of your checks passed.",
                     previous_code=code, nonce="7.3", feedback_kind="review"),
        build_prompt(inst, feedback="Failed example:\n    f()\nExpected:\n    1\nGot:\n    None",
                     previous_code=code, nonce="7.3", feedback_kind="external"),
    ]
    if visible is not None:
        verify_visible_disjoint(visible, hidden)
        if visible.n_checks:
            variants.append(build_prompt(inst, feedback=render_visible_report(visible),
                                         previous_code=code, nonce="7.3",
                                         feedback_kind="external"))
    fps = [f for f in hidden.fingerprints() if len(f) >= MIN_FINGERPRINT]
    for prompt in variants:
        normalised = _norm(prompt)
        for fp in fps:
            if fp in normalised:
                raise HiddenTestLeak(
                    f"{inst.id}: a hidden check is present in the prompt "
                    f"(normalised fingerprint {fp[:60]!r})"
                )


def _hidden_text(hidden: HiddenChecks) -> str:
    """The hidden checks as one normalised string: what a visible check must not reproduce."""
    if hidden.kind == "unittest":
        return _norm(hidden.payload.get("test", ""))
    if hidden.kind == "asserts":
        return _norm("\n".join(hidden.payload.get("asserts", [])))
    if hidden.kind == "io":
        return _norm(json.dumps(hidden.payload.get("cases", []), sort_keys=True))
    raise ValueError(f"unknown hidden-check kind {hidden.kind!r}")


def example_overlaps_hidden(example: dict[str, str], hidden_norm: str) -> bool:
    """True if a public example's *expected value* is also asserted by the hidden test.

    What makes a check a check is its expected value, so that is what is compared: the example's
    expected output alone, and its call together with its expected output, each normalised as
    `_norm` does and each only when at least `MIN_FINGERPRINT` characters long (a bare ``True`` or
    ``3`` is not information about the hidden test, as in `verify_no_leak`). A setup line with no
    expected output (``>>> df = make_df()``) asserts nothing and is not a check in this sense.
    """
    want = _norm(f"{example.get('want', '')}{example.get('exc_msg', '')}")
    if not want:
        return False
    both = _norm(example.get("source", "")) + want
    return ((len(want) >= MIN_FINGERPRINT and want in hidden_norm)
            or (len(both) >= MIN_FINGERPRINT and both in hidden_norm))


def verify_visible_disjoint(visible: VisibleChecks, hidden: HiddenChecks) -> None:
    """Raise `HiddenTestLeak` unless the visible checks for an instance carry none of its hidden ones.

    Two directions. No visible example may reproduce a hidden expected value
    (`example_overlaps_hidden`), and no hidden fingerprint may appear anywhere in the visible text.
    Run at build time and again on every load, so a hand-edited or stale file cannot slip through.
    """
    if visible.instance_id != hidden.instance_id:
        raise ValueError(f"visible checks for {visible.instance_id!r} paired with hidden checks "
                         f"for {hidden.instance_id!r}")
    hidden_norm = _hidden_text(hidden)
    for i, ex in enumerate(visible.examples):
        if example_overlaps_hidden(ex, hidden_norm):
            raise HiddenTestLeak(f"{visible.instance_id}: visible example {i} reproduces a hidden "
                                 f"check ({_norm(ex.get('want', ''))[:60]!r})")
    blob = _norm(visible.text())
    for fp in hidden.fingerprints():
        if len(fp) >= MIN_FINGERPRINT and fp in blob:
            raise HiddenTestLeak(f"{visible.instance_id}: a hidden check fingerprint is present in "
                                 f"the visible checks ({fp[:60]!r})")


def render_visible_report(visible: VisibleChecks) -> str:
    """A failure report quoting every visible example: the most a Bext repair prompt can show."""
    parts = []
    for ex in visible.examples:
        parts.append("Failed example:\n    " + ex.get("source", "").rstrip().replace("\n", "\n    ")
                     + "\nExpected:\n    " + (ex.get("want", "") or ex.get("exc_msg", "")
                                              or "nothing").rstrip().replace("\n", "\n    ")
                     + "\nGot:\n    None")
    return "\n**********************************************************************\n".join(parts)


# ======================================================================================
# Prompts. Written once, before the pilot, and not tuned between arms (protocol: threats)
# ======================================================================================

SYSTEM_PROMPT = """\
You are a Python programmer solving one self-contained task. You have no tools: you cannot run
code, read files or search the web. Answer from the task statement alone.

Rules that apply to every answer:
- Write Python 3 for the standard CPython interpreter. Only import modules the task itself names or
  that the standard library provides, unless the task's own code already imports something else.
- Your code must be complete and runnable on its own: include every import and helper it needs.
- Define exactly the function name the task asks for, with exactly the parameters it specifies.
- Do not print anything, do not read from standard input, and do not call exit().
- Do not attempt any network access.
- Return your answer as JSON, in the shape the task specifies. Put the code in the JSON string; do
  not wrap it in Markdown fences.
- Every object in the "votes" array must carry "record_id" set to exactly the task identifier given
  in the task heading.
"""

_TASK_BLOCK = """\
# Task {instance_id}

{visible_prompt}

The function you must define is named `{entry_point}`.
"""

_CHECKS_BLOCK = """\
Also write your own checks for the solution, as the `checks` field: a Python snippet of `assert`
statements that will be executed in the same namespace as your code, immediately after it. Your
checks are for your own benefit - they are run and their failures are shown back to you so you can
repair the code. Test the behaviour the task describes, including the edge cases you think are most
likely to be wrong. Do not print anything in the checks.
"""

_NO_CHECKS_BLOCK = """\
Return only the code. Do not write tests.
"""

_FEEDBACK_BLOCK = """\
Your previous attempt is below. Running your own checks against it produced the output that
follows. Repair the code so that the checks pass and the task is still solved as stated. Return the
full corrected program, not a diff, and return your checks again (repaired too, if a check was
itself wrong).

## Your previous code

```python
{code}
```

## Output of your checks

```
{output}
```
"""

_NONCE_BLOCK = """\
(Independent attempt {nonce}. Solve the task from scratch; this identifier carries no information.)
"""

# ---- Amendment 12a (2026-09-25): two new feedback blocks, written once before the v2 pilot. The v1
# templates above are untouched (`prompt_sha()` still hashes exactly them; a test pins its value).

#: Arm Bfix, a mandatory round after the model's own checks *passed*. Without it a forced round would
#: have no feedback to show; with it the round is still verification, not an unguided retry.
_REVIEW_BLOCK = """\
Your previous attempt is below, and your own checks passed on it. Checks you wrote yourself can pass
on code that is still wrong, so verify it again: re-read the task statement, compare it with the
code, look for required behaviour your checks do not exercise, strengthen the checks, and repair the
code if anything is wrong. Return the full program (unchanged if you find nothing to fix), not a
diff, and return your checks again.

## Your previous code

```python
{code}
```

## Output of your checks

```
{output}
```
"""

#: Arm Bext: the harness ran the task's public worked examples (never the hidden tests).
_EXTERNAL_FEEDBACK_BLOCK = """\
Your previous attempt is below. The task's public examples were run against it and produced the
output that follows. Repair the code so that the examples pass and the task is still solved as
stated. Return the full corrected program, not a diff.

## Your previous code

```python
{code}
```

## Output of the public examples

```
{output}
```
"""

_FEEDBACK_BLOCKS = {"self": _FEEDBACK_BLOCK, "review": _REVIEW_BLOCK,
                    "external": _EXTERNAL_FEEDBACK_BLOCK}


def build_prompt(
    inst: Instance,
    *,
    with_checks: bool = False,
    feedback: str | None = None,
    previous_code: str = "",
    nonce: str = "",
    feedback_kind: str = "self",
) -> str:
    """The user prompt for one model call.

    Takes an `Instance` - the visible half of a task - and free text. There is deliberately no
    parameter through which a `HiddenChecks` could arrive, and the type guard below makes an attempt
    to pass one a loud failure rather than a silent leak. A `VisibleChecks` is refused the same way:
    what a Bext repair prompt may show is the *output* of running the public examples, produced by the
    sandbox, never the check object stringified.

    `feedback_kind` picks the repair block: ``self`` (v1, the model's own checks failed), ``review``
    (Bfix, a mandatory round after its own checks passed) or ``external`` (Bext, the public examples
    failed). The default reproduces every v1 prompt byte for byte.
    """
    if not isinstance(inst, Instance):
        raise TypeError(f"build_prompt takes an Instance, not {type(inst).__name__}")
    for name, value in (("feedback", feedback), ("previous_code", previous_code), ("nonce", nonce)):
        if isinstance(value, HiddenChecks | Suite | VisibleChecks):
            raise TypeError(f"build_prompt: {name} may not be a {type(value).__name__}")
    if feedback_kind not in _FEEDBACK_BLOCKS:
        raise ValueError(f"unknown feedback_kind {feedback_kind!r}")
    parts = [_TASK_BLOCK.format(
        instance_id=inst.id, visible_prompt=inst.visible_prompt, entry_point=inst.entry_point)]
    if nonce:
        parts.append(_NONCE_BLOCK.format(nonce=nonce))
    if feedback:
        parts.append(_FEEDBACK_BLOCKS[feedback_kind].format(code=previous_code, output=feedback))
    parts.append(_CHECKS_BLOCK if with_checks else _NO_CHECKS_BLOCK)
    return "\n".join(parts)


def prompt_sha() -> str:
    """Fingerprint of every prompt template, so a row proves which wording produced it."""
    parts = (SYSTEM_PROMPT, _TASK_BLOCK, _CHECKS_BLOCK, _NO_CHECKS_BLOCK, _FEEDBACK_BLOCK,
             _NONCE_BLOCK)
    blob = "|<>|".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


#: `prompt_sha()` as recorded on every v1 row. Pinned by a test: the v1 wording must never move.
PROMPT_SHA_V1 = "886978ae5bec746f"


def prompt_sha_v2() -> str:
    """Fingerprint of the v1 templates plus the two amendment-12a feedback blocks."""
    blob = f"{prompt_sha()}|<>|{_REVIEW_BLOCK}|<>|{_EXTERNAL_FEEDBACK_BLOCK}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def gen_schema(with_checks: bool) -> dict[str, Any]:
    """The JSON the model is asked for, in the shape `vote_batch_claude_code` validates."""
    item: dict[str, Any] = {
        "type": "object",
        "properties": {
            "record_id": {"type": "string"},
            "code": {"type": "string"},
        },
        "required": ["record_id", "code"],
        "additionalProperties": False,
    }
    if with_checks:
        item["properties"]["checks"] = {"type": "string"}
        item["required"] = ["record_id", "code", "checks"]
    return {
        "type": "object",
        "properties": {"votes": {"type": "array", "items": item}},
        "required": ["votes"],
        "additionalProperties": False,
    }


# ======================================================================================
# Sandbox. A benchmark runner, not a security boundary (see the module docstring)
# ======================================================================================

SENTINEL = "__TIER3_RESULT__"

#: Stubs the socket layer so a candidate cannot reach the network by accident, and makes hashing
#: deterministic. Best effort by construction: any code that wants out can get out.
_PREAMBLE = '''
import socket as _socket


class _NoNetwork(OSError):
    pass


def _blocked(*_a, **_k):
    raise _NoNetwork("the tier-3 benchmark sandbox has no network")


for _name in ("socket", "create_connection", "socketpair", "getaddrinfo", "gethostbyname"):
    try:
        setattr(_socket, _name, _blocked)
    except Exception:
        pass
'''

#: Encoding/decoding and comparison for `io` checks. Lives in one string so the parent's probe and
#: the child's scorer cannot disagree about what "equal" means.
_HELPERS = '''
import math


def _tag(obj):
    if isinstance(obj, tuple):
        return {"__t__": "tuple", "v": [_tag(x) for x in obj]}
    if isinstance(obj, (set, frozenset)):
        kind = "set" if isinstance(obj, set) else "frozenset"
        try:
            items = sorted(obj, key=repr)
        except Exception:
            items = list(obj)
        return {"__t__": kind, "v": [_tag(x) for x in items]}
    if isinstance(obj, bytes):
        return {"__t__": "bytes", "v": obj.decode("latin-1")}
    if isinstance(obj, complex):
        return {"__t__": "complex", "v": [obj.real, obj.imag]}
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return {"__t__": "float", "v": repr(obj)}
    if isinstance(obj, dict):
        return {"__t__": "dict", "v": [[_tag(k), _tag(v)] for k, v in obj.items()]}
    if isinstance(obj, list):
        return [_tag(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return {"__t__": "repr", "v": repr(obj)}


def _untag(obj):
    if isinstance(obj, list):
        return [_untag(x) for x in obj]
    if isinstance(obj, dict):
        t = obj.get("__t__")
        if t == "tuple":
            return tuple(_untag(x) for x in obj["v"])
        if t == "set":
            return set(_untag(x) for x in obj["v"])
        if t == "frozenset":
            return frozenset(_untag(x) for x in obj["v"])
        if t == "bytes":
            return obj["v"].encode("latin-1")
        if t == "complex":
            return complex(obj["v"][0], obj["v"][1])
        if t == "float":
            return float(obj["v"])
        if t == "dict":
            return {_untag(k): _untag(v) for k, v in obj["v"]}
        if t == "repr":
            return ("__repr__", obj["v"])
        return {k: _untag(v) for k, v in obj.items()}
    return obj


def _same(a, b, atol):
    """Structural equality, tolerant about sequence type and (when atol > 0) about floats.

    Deliberately more permissive than `==`: a solution that returns a list where the reference
    returned a tuple has solved the task. The same comparison scores the reference, so the
    tolerance is applied identically to every arm.
    """
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) or isinstance(b, float):
            if math.isnan(a) and math.isnan(b):
                return True
            tol = atol if atol else 1e-9
            return abs(a - b) <= tol + 1e-12 * max(abs(a), abs(b))
        return a == b
    if isinstance(a, (set, frozenset)) or isinstance(b, (set, frozenset)):
        if not isinstance(a, (set, frozenset, list, tuple)) or not isinstance(
                b, (set, frozenset, list, tuple)):
            return False
        xs, ys = sorted(a, key=repr), sorted(b, key=repr)
        return len(xs) == len(ys) and all(_same(x, y, atol) for x, y in zip(xs, ys))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y, atol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return False
        return all(_same(a[k], b[k], atol) for k in a)
    return a == b
'''

_ENV_KEEP = (
    "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
    "LOCALAPPDATA", "APPDATA", "PATHEXT", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "LANG",
)


def sandbox_env() -> dict[str, str]:
    """A minimal environment. No API keys, no proxies, no PYTHONPATH."""
    env = {k: v for k, v in os.environ.items() if k in _ENV_KEEP}
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "NO_COLOR": "1",
    })
    return env


@dataclass(frozen=True)
class SandboxRun:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool

    def result(self) -> dict[str, Any] | None:
        for line in reversed(self.stdout.splitlines()):
            if line.startswith(SENTINEL):
                try:
                    return json.loads(line[len(SENTINEL):])
                except json.JSONDecodeError:
                    return None
        return None

    def tail(self, limit: int = 4000) -> str:
        text = (self.stderr + ("\n" + self.stdout if self.stdout else "")).strip()
        text = "\n".join(ln for ln in text.splitlines() if not ln.startswith(SENTINEL))
        return text[-limit:]


def run_sandbox(files: dict[str, str], script: str, timeout: float) -> SandboxRun:
    """Run `script` in a throwaway directory containing `files`, and kill the tree on timeout.

    Never run model-generated code in the parent process: a candidate that calls `sys.exit`, spawns
    threads, installs signal handlers or leaks file handles would otherwise take the runner with it.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="tier3_"))
    try:
        for name, text in files.items():
            (tmpdir / name).write_text(text, encoding="utf-8")
        entry = tmpdir / "__tier3_runner.py"
        entry.write_text(script, encoding="utf-8")
        kwargs: dict[str, Any] = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(
                subprocess, "CREATE_NO_WINDOW", 0)
        else:
            kwargs["start_new_session"] = True
        proc = subprocess.Popen(  # benign benchmark code; see the module docstring
            [sys.executable, "-B", str(entry)],
            cwd=str(tmpdir), env=sandbox_env(), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", **kwargs)
        timed_out = False
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_tree(proc)
            try:
                out, err = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:  # pragma: no cover - the tree refused to die
                out, err = "", "timeout: process tree would not terminate"
        return SandboxRun(proc.returncode if proc.returncode is not None else -1,
                          out or "", err or "", timed_out)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _kill_tree(proc: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, check=False)
    else:  # pragma: no cover - this module is developed and run on Windows
        import signal
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        proc.kill()
    except OSError:  # pragma: no cover
        pass


# ======================================================================================
# Scoring against the hidden checks
# ======================================================================================


@dataclass(frozen=True)
class Score:
    passed: int
    total: int
    timed_out: bool = False
    error: str = ""

    @property
    def fraction(self) -> float:
        return (self.passed / self.total) if self.total else 0.0

    @property
    def binary(self) -> int:
        return int(self.total > 0 and self.passed == self.total)


_ASSERT_RUNNER = '''
import json
import traceback

DATA = json.loads(open("checks.json", encoding="utf-8").read())
CODE = open("candidate.py", encoding="utf-8").read()
passed, failures = 0, []
base = {"__name__": "__candidate__"}
try:
    exec(compile(CODE, "candidate.py", "exec"), base)
except BaseException:
    failures.append("candidate did not import: " + traceback.format_exc(limit=3))
    print("%s%s" % (SENT, json.dumps(
        {"passed": 0, "total": len(DATA["asserts"]), "failures": failures[:5]})))
    raise SystemExit(0)
for i, src in enumerate(DATA["asserts"]):
    ns = dict(base)
    try:
        exec(compile("\\n".join(DATA.get("imports", [])) + "\\n" + src, "check%d" % i, "exec"), ns)
        passed += 1
    except BaseException as exc:
        failures.append("check %d: %s: %s" % (i, type(exc).__name__, str(exc)[:200]))
print("%s%s" % (SENT, json.dumps(
    {"passed": passed, "total": len(DATA["asserts"]), "failures": failures[:5]})))
'''

_IO_RUNNER = '''
import json
import traceback

DATA = json.loads(open("checks.json", encoding="utf-8").read())
CODE = open("candidate.py", encoding="utf-8").read()
atol = DATA.get("atol") or 0
cases = DATA["cases"]
ns = {"__name__": "__candidate__"}
try:
    exec(compile(CODE, "candidate.py", "exec"), ns)
    fn = ns[DATA["entry_point"]]
except BaseException:
    print("%s%s" % (SENT, json.dumps({"passed": 0, "total": len(cases),
                                      "failures": ["no callable: " + traceback.format_exc(limit=3)]})))
    raise SystemExit(0)
passed, failures = 0, []
for i, case in enumerate(cases):
    try:
        args = _untag(case["input"])
        expected = _untag(case["expected"])
        got = fn(*args)
        if _same(got, expected, atol):
            passed += 1
        else:
            failures.append("case %d: got %r, expected %r" % (i, got, expected))
    except BaseException as exc:
        failures.append("case %d: %s: %s" % (i, type(exc).__name__, str(exc)[:160]))
print("%s%s" % (SENT, json.dumps({"passed": passed, "total": len(cases),
                                  "failures": failures[:5]})))
'''

_UNITTEST_RUNNER = '''
import json
import traceback
import unittest

DATA = json.loads(open("checks.json", encoding="utf-8").read())
CODE = open("candidate.py", encoding="utf-8").read()
expected_total = DATA.get("n_checks") or 0
ns = {"__name__": "__candidate__"}
try:
    exec(compile(CODE, "candidate.py", "exec"), ns)
    exec(compile(DATA["test"], "hidden_test.py", "exec"), ns)
    case = None
    for value in ns.values():
        if isinstance(value, type) and issubclass(value, unittest.TestCase):
            case = value
except BaseException:
    print("%s%s" % (SENT, json.dumps({"passed": 0, "total": expected_total,
                                      "failures": [traceback.format_exc(limit=3)]})))
    raise SystemExit(0)
if case is None:
    print("%s%s" % (SENT, json.dumps({"passed": 0, "total": expected_total,
                                      "failures": ["no TestCase in the hidden test"]})))
    raise SystemExit(0)
suite = unittest.TestLoader().loadTestsFromTestCase(case)
result = unittest.TestResult()
try:
    suite.run(result)
except BaseException:
    pass
bad = len(result.failures) + len(result.errors)
total = max(result.testsRun, expected_total)
passed = max(0, result.testsRun - bad)
failures = ["%s: %s" % (str(t), str(m)[:200]) for t, m in (result.failures + result.errors)][:5]
print("%s%s" % (SENT, json.dumps({"passed": passed, "total": total, "failures": failures})))
'''

_PROBE_RUNNER = '''
import json
import traceback

DATA = json.loads(open("checks.json", encoding="utf-8").read())
CODE = open("candidate.py", encoding="utf-8").read()
ns = {"__name__": "__reference__"}
out = []
try:
    exec(compile(CODE, "candidate.py", "exec"), ns)
    fn = ns[DATA["entry_point"]]
except BaseException:
    print("%s%s" % (SENT, json.dumps({"error": traceback.format_exc(limit=3), "outputs": []})))
    raise SystemExit(0)
for case in DATA["inputs"]:
    try:
        out.append({"ok": True, "value": _tag(fn(*_untag(case)))})
    except BaseException as exc:
        out.append({"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:120])})
print("%s%s" % (SENT, json.dumps({"error": "", "outputs": out})))
'''

_SELFCHECK_RUNNER = '''
import json
import traceback

DATA = json.loads(open("checks.json", encoding="utf-8").read())
CODE = open("candidate.py", encoding="utf-8").read()
ns = {"__name__": "__candidate__"}
try:
    exec(compile(CODE, "candidate.py", "exec"), ns)
except BaseException:
    print(traceback.format_exc(limit=4))
    print("%s%s" % (SENT, json.dumps({"ok": False, "stage": "code"})))
    raise SystemExit(0)
try:
    exec(compile(DATA["checks"], "self_checks.py", "exec"), ns)
except BaseException:
    print(traceback.format_exc(limit=4))
    print("%s%s" % (SENT, json.dumps({"ok": False, "stage": "checks"})))
    raise SystemExit(0)
print("%s%s" % (SENT, json.dumps({"ok": True, "stage": "checks"})))
'''

#: Amendment 12a, arm Bext: run the task's public docstring examples as a doctest against a candidate.
#: The report doctest prints is exactly what a Bext repair prompt shows. A non-interactive plotting
#: backend is forced because several examples call `plt.show()`, which would otherwise block.
_DOCTEST_RUNNER = '''
import doctest
import json
import traceback

try:
    import matplotlib
    matplotlib.use("Agg")
except Exception:
    pass

DATA = json.loads(open("checks.json", encoding="utf-8").read())
CODE = open("candidate.py", encoding="utf-8").read()
examples = [doctest.Example(e["source"], e.get("want", ""), exc_msg=(e.get("exc_msg") or None),
                            lineno=i) for i, e in enumerate(DATA["examples"])]
ns = {"__name__": "__candidate__"}
try:
    exec(compile(CODE, "candidate.py", "exec"), ns)
except BaseException:
    print("The program raised before any example could run:")
    print(traceback.format_exc(limit=4))
    print("%s%s" % (SENT, json.dumps({"ok": False, "passed": 0, "total": len(examples),
                                      "failed": list(range(len(examples)))})))
    raise SystemExit(0)


class _Runner(doctest.DocTestRunner):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.failed_idx = []

    def report_failure(self, out, test, example, got):
        self.failed_idx.append(example.lineno)
        super().report_failure(out, test, example, got)

    def report_unexpected_exception(self, out, test, example, exc_info):
        self.failed_idx.append(example.lineno)
        super().report_unexpected_exception(out, test, example, exc_info)


chunks = []
test = doctest.DocTest(examples, ns, "public_examples", "public_examples.py", 0, None)
runner = _Runner(verbose=False, optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
try:
    runner.run(test, out=chunks.append, clear_globs=False)
except BaseException:
    chunks.append(traceback.format_exc(limit=3))
    runner.failed_idx.extend(range(len(examples)))
failed = sorted(set(runner.failed_idx))
print("".join(chunks)[-6000:])
print("%s%s" % (SENT, json.dumps({"ok": bool(examples) and not failed,
                                  "passed": len(examples) - len(failed), "total": len(examples),
                                  "failed": failed})))
'''

_RUNNERS = {
    "asserts": _ASSERT_RUNNER,
    "io": _IO_RUNNER,
    "unittest": _UNITTEST_RUNNER,
    "probe": _PROBE_RUNNER,
    "selfcheck": _SELFCHECK_RUNNER,
    "doctest": _DOCTEST_RUNNER,
}


#: `doctest` imports `pdb`, which imports `asyncio` and hence `ssl`, and `ssl` subclasses
#: `socket.socket` - which `_PREAMBLE` has replaced by a function. So the doctest runner imports
#: `doctest` *before* the network stub, and then forgets every module that import pulled in, so the
#: candidate meets exactly the module state it meets under the hidden-test runners (where an `import
#: asyncio` fails on the stub). Without the purge a candidate could pass its public examples while
#: failing to import under the hidden tests, and the two signals would disagree about the environment.
_DOCTEST_PREIMPORT = '''
import sys as _sys
_before = set(_sys.modules)
import doctest
for _name in set(_sys.modules) - _before - {"doctest"}:
    _sys.modules.pop(_name, None)
'''


def _runner_script(kind: str) -> str:
    head = [f"SENT = {SENTINEL!r}"] + ([_DOCTEST_PREIMPORT] if kind == "doctest" else [])
    return "\n".join([*head, _PREAMBLE, _HELPERS, _RUNNERS[kind]])


def score_candidate(code: str, hidden: HiddenChecks, timeout: float = 60.0) -> Score:
    """Score one candidate against the hidden checks. Continuous: passed / total checks.

    A candidate that loops forever, crashes the interpreter or cannot even be imported scores 0 out
    of the full check count - never 0 out of 0, which would silently drop the instance.
    """
    if not (code or "").strip():
        return Score(0, hidden.n_checks, error="empty candidate")
    payload = dict(hidden.payload)
    payload["n_checks"] = hidden.n_checks
    run = run_sandbox({"candidate.py": code, "checks.json": json.dumps(payload)},
                      _runner_script(hidden.kind), timeout)
    res = run.result()
    if run.timed_out or res is None:
        return Score(0, hidden.n_checks, timed_out=run.timed_out,
                     error=("timeout" if run.timed_out else f"no result: {run.tail(300)}"))
    total = int(res.get("total") or hidden.n_checks) or hidden.n_checks
    return Score(int(res.get("passed") or 0), total,
                 error="; ".join(res.get("failures") or [])[:600])


@dataclass(frozen=True)
class SelfCheckResult:
    ok: bool
    output: str
    ran: bool


def run_self_checks(code: str, checks: str, timeout: float = 60.0) -> SelfCheckResult:
    """Run the harness's own, model-written checks. This is arm B's verification step.

    When the model wrote no checks there is no failure signal to act on, so B stops: that is the
    honest reading of "stop when checks pass", and it is recorded per row (`ran=False`) so the
    proportion of instances where B degenerated to A is reportable rather than hidden.
    """
    if not (checks or "").strip():
        return SelfCheckResult(True, "", False)
    run = run_sandbox({"candidate.py": code, "checks.json": json.dumps({"checks": checks})},
                      _runner_script("selfcheck"), timeout)
    res = run.result()
    if run.timed_out:
        return SelfCheckResult(False, "TimeoutError: your code or your checks did not finish", True)
    if res is None:
        return SelfCheckResult(False, run.tail() or "the checks did not run", True)
    return SelfCheckResult(bool(res.get("ok")), run.tail(), True)


# ---- Amendment 12a: public (visible) checks, for arm Bext


def _run_doctest(code: str, examples: Sequence[dict[str, str]],
                 timeout: float) -> tuple[bool, list[int], str, bool]:
    """(ok, failed example indices, report text, timed out) for `examples` run against `code`."""
    run = run_sandbox({"candidate.py": code,
                       "checks.json": json.dumps({"examples": list(examples)})},
                      _runner_script("doctest"), timeout)
    res = run.result()
    if run.timed_out:
        return False, list(range(len(examples))), \
            "TimeoutError: the program or the examples did not finish", True
    if res is None:
        return False, list(range(len(examples))), run.tail() or "the examples did not run", False
    return bool(res.get("ok")), [int(i) for i in res.get("failed") or []], run.tail(), False


def run_visible_checks(code: str, visible: VisibleChecks, timeout: float = 60.0) -> SelfCheckResult:
    """Arm Bext's verification step: run the public examples, never the hidden tests.

    An instance with no usable public example gives no signal, so Bext stops after one call, exactly
    as v1's B stops when the model writes no checks; `ran=False` makes that reportable.
    """
    if not visible.n_checks:
        return SelfCheckResult(True, "", False)
    ok, _failed, output, _timed_out = _run_doctest(code, visible.examples, timeout)
    return SelfCheckResult(ok, output, True)


def parse_docstring_examples(program_stub: str, entry_point: str) -> list[dict[str, str]]:
    """The worked examples (``>>>`` lines) in the docstring of `entry_point`, in order.

    Reads the program stub only. The hidden test is not an argument, so nothing parsed here can
    have come from it.
    """
    import ast
    import doctest
    import warnings

    try:
        with warnings.catch_warnings():  # stubs carry "\d" in plain docstrings; harmless here
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(program_stub or "")
    except SyntaxError:
        return []
    doc = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == entry_point:
            doc = ast.get_docstring(node, clean=True) or ""
            break
    try:
        found = doctest.DocTestParser().get_examples(doc)
    except ValueError:  # malformed docstring example (bad indentation)
        return []
    return [{"source": ex.source, "want": ex.want, "exc_msg": ex.exc_msg or ""} for ex in found]


def build_visible_checks(instance_id: str, program_stub: str, entry_point: str, gold_code: str, *,
                         hidden: HiddenChecks, timeout: float = 60.0,
                         max_rounds: int = 6) -> VisibleChecks:
    """Public checks for one instance, from its docstring examples, filtered twice.

    1. **Withheld if they reproduce a hidden check.** Any example whose expected value the hidden test
       also asserts (`example_overlaps_hidden`) is dropped. `hidden` is used only to *delete*
       examples; no hidden text can flow into the result, which is built from `program_stub` alone.
    2. **Gold filter, as for the hidden tests.** The released canonical solution must pass every
       example that is kept, in this environment. Examples that fail on the gold (a path that does not
       exist here, a clock, a plot's repr) are dropped, repeatedly, because a dropped setup line makes
       the lines after it fail too. What is left is a set the reference solution passes in full, so a
       Bext failure is a fact about the candidate, not about the environment.
    """
    parsed = parse_docstring_examples(program_stub, entry_point)
    hidden_norm = _hidden_text(hidden)
    kept = [ex for ex in parsed if not example_overlaps_hidden(ex, hidden_norm)]
    n_overlap = len(parsed) - len(kept)
    before_gold = len(kept)
    for _ in range(max_rounds):
        if not kept:
            break
        ok, failed, _out, timed_out = _run_doctest(gold_code, kept, timeout)
        if ok:
            break
        if timed_out or not failed:
            kept = []
            break
        kept = [ex for i, ex in enumerate(kept) if i not in set(failed)]
    else:
        kept = []
    # a set made only of setup lines asserts nothing beyond "does not raise"; keep it only if at
    # least one example states an expected value
    if not any((ex.get("want") or ex.get("exc_msg")) for ex in kept):
        kept = []
    vis = VisibleChecks(instance_id, "doctest", kept, "docstring", n_parsed=len(parsed),
                        n_dropped_gold=before_gold - len(kept), n_dropped_overlap=n_overlap)
    verify_visible_disjoint(vis, hidden)
    return vis


# ======================================================================================
# Generation: the one and only path to a model
# ======================================================================================


@dataclass(frozen=True)
class Generation:
    code: str
    checks: str
    prompt: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float


def generate(
    inst: Instance,
    *,
    backend: Callable[..., Any],
    exe: str,
    model: str,
    system_file: Path,
    with_checks: bool = False,
    feedback: str | None = None,
    previous_code: str = "",
    nonce: str = "",
    effort: str | None = None,
    feedback_kind: str = "self",
) -> Generation:
    """One model call. Every arm goes through here; nothing else calls a backend.

    `backend` has the signature of `screen_llm.vote_batch_claude_code`, which is the subscription
    path (`claude -p --output-format json`). Tests inject a fake with the same signature, so the
    suite never touches the network.
    """
    prompt_text = build_prompt(inst, with_checks=with_checks, feedback=feedback,
                              previous_code=previous_code, nonce=nonce,
                              feedback_kind=feedback_kind)
    batch = [{"id": inst.id, "prompt": prompt_text}]
    res = backend(exe, model, system_file, batch, effort=effort, schema=gen_schema(with_checks),
                  prompt=lambda b: b[0]["prompt"], text_json=True)
    vote = (res.votes or [{}])[0]
    return Generation(
        code=str(vote.get("code") or ""), checks=str(vote.get("checks") or ""),
        prompt=prompt_text, model=getattr(res, "model", model) or model,
        tokens_in=int(getattr(res, "tokens_in", 0) or 0),
        tokens_out=int(getattr(res, "tokens_out", 0) or 0),
        cost_usd=float(getattr(res, "cost_usd", 0.0) or 0.0))


LIMIT_RE = re.compile(
    r"usage limit|session limit|limit reached|limit will reset|rate.?limit|\b429\b|overloaded"
    r"|too many requests|capacity", re.IGNORECASE)


def with_limit_handling(
    fn: Callable[[], Any],
    *,
    log_path: Path,
    label: str,
    max_pauses: int = 8,
    default_wait: int = 1800,
    max_wait: int = 6 * 3600,
    retries: int = 2,
    retry_delay: float = 5.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> Any:
    """Call `fn`, pausing out usage-limit windows the way `phase4_autopilot` does.

    A usage limit says when it lifts, so the wait comes from the limit message itself
    (`phase4_autopilot.reset_wait` over the run log), not from a fixed poll. An exhausted balance
    never lifts (`phase4_autopilot.credits_exhausted`), so it raises `CreditsExhausted` and the
    caller stops the run with every completed row already on disk.
    """
    pauses = tries = 0
    while True:
        try:
            return fn()
        except CreditsExhausted:
            raise
        except Exception as exc:  # classified here, then paused, retried or re-raised
            text = str(exc)
            log.error("%s: %s: %s", label, type(exc).__name__, text[:600])
            if phase4_autopilot.credits_exhausted(log_path):
                raise CreditsExhausted(text[:300]) from exc
            if LIMIT_RE.search(text) and pauses < max_pauses:
                pauses += 1
                wait, why = phase4_autopilot.reset_wait(log_path, default_wait)
                wait = min(int(wait), int(max_wait))
                log.warning("%s: usage limit; pausing %ds (%s)", label, wait, why)
                sleeper(wait)
                continue
            if tries < retries and not LIMIT_RE.search(text):
                tries += 1
                sleeper(retry_delay)
                continue
            raise


# ======================================================================================
# The arms
# ======================================================================================

ARMS = ("A", "B", "C")


@dataclass
class ArmResult:
    arm: str
    calls: int
    score: Score
    final_code: str
    prompts: list[str] = field(default_factory=list)
    codes: list[str] = field(default_factory=list)
    self_checks: list[dict[str, Any]] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    model: str = ""
    selection: str = ""
    stopped_early: bool = False


def normalise_code(code: str) -> str:
    """Whitespace- and comment-insensitive form, for arm C's self-consistency vote."""
    lines = []
    for raw in (code or "").splitlines():
        line = raw.split("#", 1)[0].rstrip() if "#" in raw else raw.rstrip()
        if line.strip():
            lines.append(line)
    return "\n".join(lines)


def choose_final(arm: str, codes: Sequence[str]) -> tuple[str, str]:
    """The answer an arm submits, and how it was chosen.

    A and B submit their last attempt (B's last attempt is the repaired one). C votes: the protocol
    says "final answer by self-consistency where the task admits it, else last attempt", so C takes
    the largest cluster of syntactically identical attempts when one has more than a single member,
    and otherwise - every attempt different, which is the usual case for free-form code - the last.
    """
    if not codes:
        return "", "none"
    if arm != "C":
        return codes[-1], "last"
    clusters: dict[str, list[int]] = {}
    for i, code in enumerate(codes):
        clusters.setdefault(normalise_code(code), []).append(i)
    best = max(clusters.values(), key=lambda idx: (len(idx), -idx[0]))
    if len(best) > 1:
        return codes[best[0]], f"majority({len(best)}/{len(codes)})"
    return codes[-1], "last"


def run_arm(
    arm: str,
    inst: Instance,
    hidden: HiddenChecks,
    *,
    gen: Callable[..., Generation],
    k: int = 4,
    calls_required: int | None = None,
    seed: int = 1,
    timeout: float = 60.0,
    visible: VisibleChecks | None = None,
) -> ArmResult:
    """Run one arm on one instance. The only difference between arms lives in this function.

    * A: one call, no checking, no retry.
    * B: up to `k` calls - attempt, run the model's own checks, feed the failures back, repair;
      stop as soon as the checks pass (or there are none to fail).
    * C: exactly `calls_required` independent attempts, no checks and no feedback between them.
      `calls_required` is B's `calls` on *this* instance and is mandatory: C cannot be run without
      it, which is what makes the per-instance match impossible to forget.

    Amendment 12a adds two B variants, on the same generation path:

    * Bfix: exactly `k` calls, whatever the checks say. Attempt with self-written checks, then
      `k - 1` mandatory verify-and-repair rounds: failing checks are fed back as in B; passing checks
      trigger the review block instead of a stop. It cannot stop early, so it always spends its budget.
    * Bext: up to `k` calls, verified against `visible` - the benchmark's public examples, never the
      hidden tests. Its first prompt is byte-identical to arm A's (no checks are requested; the
      harness supplies them), so its first attempt is an arm-A draw and "Bext repaired" is exactly the
      event "an arm-A draw fails the public examples". Stops when the examples pass.
    """
    if arm not in ARMS_V2:
        raise ValueError(f"unknown arm {arm!r}")
    if arm == "C":
        if calls_required is None:
            raise ValueError("arm C requires calls_required (the call count arm B used on this "
                             "instance); it is never an average and never a constant")
        if calls_required < 1:
            raise ValueError(f"arm C: calls_required must be >= 1, got {calls_required}")
    if arm == "Bext":
        if visible is None:
            raise ValueError("arm Bext requires this instance's visible checks (an empty "
                             "VisibleChecks is the legitimate 'no public example' case; None is a "
                             "plumbing error)")
        if visible.instance_id != inst.id:
            raise ValueError(f"visible checks for {visible.instance_id!r} do not belong to "
                             f"{inst.id!r}")
    budget = {"A": 1, "B": max(1, k), "Bfix": max(1, k), "Bext": max(1, k),
              "C": calls_required or 1}[arm]
    prompts: list[str] = []
    codes: list[str] = []
    self_checks: list[dict[str, Any]] = []
    tin = tout = 0
    cost = 0.0
    model = ""
    feedback: str | None = None
    previous = ""
    kind = "self"
    stopped_early = False
    for attempt in range(budget):
        extra = {"feedback_kind": kind} if kind != "self" else {}
        out = gen(inst, with_checks=(arm in ("B", "Bfix")), feedback=feedback,
                  previous_code=previous, nonce=f"{seed}.{attempt}", **extra)
        prompts.append(out.prompt)
        codes.append(out.code)
        tin += out.tokens_in
        tout += out.tokens_out
        cost += out.cost_usd
        model = out.model or model
        if arm in ("A", "C"):
            continue
        if arm == "Bext":
            res = run_visible_checks(out.code, visible, timeout=timeout)  # type: ignore[arg-type]
        else:
            res = run_self_checks(out.code, out.checks, timeout=timeout)
        self_checks.append({"attempt": attempt, "ok": res.ok, "ran": res.ran,
                            "output": res.output[-1200:]})
        if arm == "Bfix":
            # mandatory rounds: never stop on a pass; a pass is followed by the review block
            if res.ok:
                feedback = (res.output.strip() or ("All of your checks passed." if res.ran else
                                                   "You wrote no checks."))
                kind = "review"
            else:
                feedback, kind = res.output or "your checks failed", "self"
            previous = out.code
            continue
        if res.ok:
            stopped_early = attempt + 1 < budget
            break
        feedback, previous = res.output or "your checks failed", out.code
        if arm == "Bext":
            feedback, kind = res.output or "the public examples failed", "external"
    final, selection = choose_final(arm, codes)
    score = score_candidate(final, hidden, timeout=timeout)
    return ArmResult(arm=arm, calls=len(codes), score=score, final_code=final, prompts=prompts,
                     codes=codes, self_checks=self_checks, tokens_in=tin, tokens_out=tout,
                     cost_usd=cost, model=model, selection=selection, stopped_early=stopped_early)


# ======================================================================================
# The runner: rows, resume, and the B -> C hand-off
# ======================================================================================


def row_key(suite: str, instance_id: str, arm: str, seed: int, model: str) -> str:
    """The resume key. The model tier is part of it on purpose.

    Without it, a row produced by one tier would satisfy another tier's resume check and the pilot's
    tier grid - which the protocol's Model section requires, since the tier is "whatever the pilot
    shows to sit in the accuracy band" - would silently read one tier's scores as another's.
    """
    return f"{suite}|{instance_id}|{arm}|{seed}|{model}"


def read_rows(path: Path) -> list[dict[str, Any]]:
    """Every complete JSON line. A truncated last line (a killed run) is ignored, not fatal."""
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("%s: ignoring a truncated row", path.name)
    return rows


def done_keys(rows: Iterable[dict[str, Any]]) -> set[str]:
    """Keys that are finished. An `error` row is not finished and will be retried."""
    return {r["key"] for r in rows if r.get("status") == "ok" and r.get("key")}


def latest_ok(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The last successful row per key, so a duplicated append can never double-count."""
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        if r.get("status") == "ok" and r.get("key"):
            out[r["key"]] = r
    return out


def append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _row(suite: str, inst: Instance, arm: str, seed: int, phase: str, model: str) -> dict[str, Any]:
    row = {
        "key": row_key(suite, inst.id, arm, seed, model), "protocol": PROTOCOL_VERSION,
        "phase": phase, "suite": suite, "instance_id": inst.id, "arm": arm, "seed": seed,
        # `model_requested` is the tier asked for ("sonnet"); `model` is overwritten below with the
        # canonical id the CLI reports ("claude-sonnet-5"), which is the one the paper must cite
        "model_requested": model, "model": model, "prompt_sha": prompt_sha(),
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    if arm not in ARMS:  # an amendment-12a arm: Bfix, Bext, or a C matched to one of them
        row["protocol"] = PROTOCOL_VERSION_V2
        row["prompt_sha_v2"] = prompt_sha_v2()
    return row


def c_arm_label(b_arm: str) -> str:
    """The row label of the C that is matched to `b_arm`: ``C`` for v1's B, ``C@Bext`` etc. for 12a.

    Part of the resume key, so a C matched to one B variant can never satisfy the resume check of a
    C matched to another - their budgets differ.
    """
    if b_arm not in B_ARMS:
        raise ValueError(f"not a B arm: {b_arm!r}")
    return "C" if b_arm == "B" else f"C@{b_arm}"


#: how each B variant verifies, recorded on its rows
VERIFIER = {"B": "self-written, stop on pass", "Bfix": "self-written, mandatory rounds",
            "Bext": "public examples, stop on pass"}


def run_instance(
    suite: Suite,
    inst: Instance,
    *,
    arms: Sequence[str],
    seed: int,
    gen: Callable[..., Generation],
    out_path: Path,
    phase: str,
    model: str,
    k: int = 4,
    timeout: float = 60.0,
    done: set[str] | None = None,
    prior: dict[str, dict[str, Any]] | None = None,
    visible: dict[str, VisibleChecks] | None = None,
) -> list[dict[str, Any]]:
    """Every arm for one (instance, seed), in an order that makes the match structural.

    B is always run before C, and C is handed the integer B just recorded. If B was completed by an
    earlier run, that integer is read back out of `runs.jsonl` for this exact (instance, seed) - the
    count B actually used, never an average and never a configured constant. If it cannot be had, C
    is skipped with a reason, because a C run with a guessed budget is worse than a missing one.

    Amendment 12a: `arms` may name one of the B variants (B, Bfix, Bext), and C is then matched to
    *that* variant's count on this instance and labelled `c_arm_label(variant)`. Naming C together
    with two B variants is refused: C would not know whose budget to take.
    """
    done = done or set()
    prior = prior or {}
    hidden = suite.hidden[inst.id]
    written: list[dict[str, Any]] = []
    b_arms = [a for a in _arm_order(arms) if a in B_ARMS]
    if "C" in arms and len(b_arms) > 1:
        raise ValueError(f"arm C is matched to one B variant per run, got {b_arms}")
    if "Bext" in arms and visible is None:
        raise ValueError("arm Bext needs the suite's visible checks (load_visible)")
    b_arm = b_arms[0] if b_arms else "B"
    b_calls: int | None = None
    b_source = ""
    prior_b = prior.get(row_key(suite.name, inst.id, b_arm, seed, model))
    if prior_b:
        b_calls, b_source = int(prior_b["calls"]), "runs.jsonl"
    for arm in _arm_order(arms):
        label = c_arm_label(b_arm) if arm == "C" else arm
        key = row_key(suite.name, inst.id, label, seed, model)
        if key in done:
            continue
        row = _row(suite.name, inst, label, seed, phase, model)
        if arm == "C" and b_calls is None:
            row.update({"status": "skipped", "error": f"arm {b_arm} has no recorded call count for "
                                                      "this (instance, seed); C cannot be matched"})
            append_row(out_path, row)
            written.append(row)
            continue
        vis = (visible or {}).get(inst.id) if arm == "Bext" else None
        try:
            res = run_arm(arm, inst, hidden, gen=gen, k=k, seed=seed, timeout=timeout,
                          calls_required=b_calls if arm == "C" else None, visible=vis)
        except CreditsExhausted:
            raise
        except Exception as exc:  # noqa: BLE001 - one instance must never abort the run
            log.error("%s %s seed %d failed: %s: %s", inst.id, arm, seed, type(exc).__name__,
                      str(exc)[:300])
            row.update({"status": "error", "error": f"{type(exc).__name__}: {str(exc)[:500]}"})
            append_row(out_path, row)
            written.append(row)
            continue
        if arm == b_arm:
            b_calls, b_source = res.calls, "same-run"
        row.update({
            "status": "ok", "error": res.score.error, "calls": res.calls,
            "score": res.score.fraction, "passed": res.score.passed, "total": res.score.total,
            "binary": res.score.binary, "timed_out": res.score.timed_out,
            "tokens_in": res.tokens_in, "tokens_out": res.tokens_out, "cost_usd": res.cost_usd,
            "model": res.model or model, "selection": res.selection,
            "stopped_early": res.stopped_early, "self_checks": res.self_checks,
            "calls_matched_from": ({"arm": b_arm, "calls": b_calls, "source": b_source}
                                   if arm == "C" else None),
            "prompts": res.prompts, "responses": res.codes, "final_code": res.final_code,
        })
        if arm in ("Bfix", "Bext"):
            row.update({"verifier": VERIFIER[arm], "repairs": res.calls - 1,
                        "fired": res.calls > 1})
            if arm == "Bext":
                row["visible_n_checks"] = vis.n_checks if vis else 0
        append_row(out_path, row)
        written.append(row)
    return written


def _arm_order(arms: Sequence[str]) -> list[str]:
    """A before the B variants before C. C after B is not a preference; the match requires it."""
    return [a for a in ARMS_V2 if a in set(arms)]


# ======================================================================================
# Instance pools: the pilot set is disjoint from the confirmatory set, by construction
# ======================================================================================

POOL_SALT = "tier3-pool-v1"
PILOT_SHARE = 30  # per cent of each suite reserved for the pilot


def pool_of(suite: str, instance_id: str) -> str:
    h = hashlib.sha256(f"{POOL_SALT}|{suite}|{instance_id}".encode()).hexdigest()
    return "pilot" if int(h[:8], 16) % 100 < PILOT_SHARE else "confirmatory"


def select_instances(suite: Suite, pool: str, n: int) -> list[Instance]:
    """`n` instances from one pool, in a deterministic order that does not depend on file order."""
    pooled = [i for i in suite.instances if pool_of(suite.name, i.id) == pool]
    pooled.sort(key=lambda i: hashlib.sha256(f"{POOL_SALT}|order|{i.id}".encode()).hexdigest())
    return pooled[:n] if n else pooled


# ---- Amendment 12a, section 5: disjointness is by task, not by suite name. `pool_of` hashes the
# suite name, so one BigCodeBench task can be pilot under one presentation and confirmatory under
# another; measured, 11 of the 34 Hard-Instruct confirmatory tasks had been piloted as
# `bigcodebench_hard`. A confirmatory instance must be a task no pilot or diagnostic row has touched.

_FAMILY_RE = re.compile(r"^(bigcodebench|mbpp)")


def task_key(instance_id: str) -> str:
    """The task an instance presents, whatever the presentation: `bigcodebench_hard_instruct/19`
    and `bigcodebench/19` are both `bigcodebench/19`; `mbppplus/11` and `mbpp/11` are `mbpp/11`."""
    prefix, _, number = instance_id.rpartition("/")
    m = _FAMILY_RE.match(prefix)
    return f"{m.group(1) if m else prefix}/{number}"


def piloted_tasks(roots: Sequence[Path] | None = None) -> set[str]:
    """Every task that appears in any pilot or diagnostic row, under any suite name or tier."""
    roots = list(roots) if roots is not None else [PILOT_DIR, TIER3 / "diagnostic", V2_PILOT_DIR]
    out: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("runs.jsonl")):
            out.update(task_key(r["instance_id"]) for r in read_rows(path) if r.get("instance_id"))
    return out


def confirmatory_instances(suite: Suite, n: int, piloted: set[str]) -> list[Instance]:
    """The confirmatory pool minus every task already seen in a pilot: the v2 selection rule."""
    clean = [i for i in select_instances(suite, "confirmatory", 0) if task_key(i.id) not in piloted]
    return clean[:n] if n else clean


# ======================================================================================
# Suite preparation
# ======================================================================================

SUITE_SOURCES = {
    "mbpp": ("sanitized-mbpp.json",
             ("https://raw.githubusercontent.com/google-research/google-research/master/mbpp/"
              "sanitized-mbpp.json")),
    "mbppplus": ("MbppPlus.jsonl.gz",
                 ("https://github.com/evalplus/mbppplus_release/releases/download/v0.2.0/"
                  "MbppPlus.jsonl.gz")),
    "bigcodebench_hard": ("BigCodeBench-Hard.jsonl.gz",
                          ("https://github.com/bigcode-project/bigcodebench-annotation/releases/"
                           "download/v0.1.1/BigCodeBench-Hard.jsonl.gz")),
    "bigcodebench": ("BigCodeBench.jsonl.gz",
                     ("https://github.com/bigcode-project/bigcodebench-annotation/releases/"
                      "download/v0.1.1/BigCodeBench.jsonl.gz")),
    # The Instruct presentations of the same two releases: same tasks, same hidden tests, same
    # scorer, less of the specification shown. Added to the candidate set after the first pilot
    # found every Complete candidate above the band (see the protocol notes); no new download.
    "bigcodebench_instruct": ("BigCodeBench.jsonl.gz",
                              ("https://github.com/bigcode-project/bigcodebench-annotation/"
                               "releases/download/v0.1.1/BigCodeBench.jsonl.gz")),
    "bigcodebench_hard_instruct": ("BigCodeBench-Hard.jsonl.gz",
                                   ("https://github.com/bigcode-project/bigcodebench-annotation/"
                                    "releases/download/v0.1.1/BigCodeBench-Hard.jsonl.gz")),
}
MAX_IO_CHECKS = 40  # MBPP+ ships hundreds of inputs for some tasks; 40 is plenty for a fraction


def fetch_raw(name: str, refresh: bool = False) -> Path:
    filename, url = SUITE_SOURCES[name]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / filename
    if dest.exists() and not refresh:
        return dest
    import requests
    log.info("downloading %s", url)
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def _read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _signature_of(code: str, entry_point: str) -> str:
    m = re.search(rf"^\s*def\s+{re.escape(entry_point)}\s*\(([^)]*)\)", code or "", re.MULTILINE)
    return f"def {entry_point}({m.group(1).strip()}):" if m else f"def {entry_point}(...):"


def _entry_point_from_asserts(code: str, asserts: Sequence[str]) -> str:
    defined = re.findall(r"^\s*def\s+(\w+)\s*\(", code or "", re.MULTILINE)
    for name in defined:
        if any(re.search(rf"\b{re.escape(name)}\s*\(", a) for a in asserts):
            return name
    return defined[0] if defined else ""


def build_mbpp(rows: Sequence[dict[str, Any]]) -> Suite:
    """Sanitized MBPP, 427 tasks. Hidden checks: all of the task's asserts.

    The task statement is given without its asserts - MBPP's usual "3 asserts in the prompt" recipe
    would leave nothing hidden and fail criterion 1 - so the required signature is stated explicitly
    instead, which is the only thing those asserts would otherwise have revealed.
    """
    instances, hidden = [], {}
    for r in rows:
        asserts = list(r.get("test_list") or [])
        entry = _entry_point_from_asserts(r.get("code", ""), asserts)
        if not entry or not asserts:
            continue
        iid = f"mbpp/{r['task_id']}"
        visible = (f"{r['prompt'].strip()}\n\nWrite exactly this function:\n\n"
                   f"```python\n{_signature_of(r['code'], entry)}\n```")
        instances.append(Instance(id=iid, suite="mbpp", visible_prompt=visible, entry_point=entry))
        hidden[iid] = HiddenChecks(iid, "asserts",
                                   {"asserts": asserts, "imports": list(r.get("test_imports") or []),
                                    "entry_point": entry}, len(asserts))
    return Suite("mbpp", instances, hidden,
                 {"source": "google-research/mbpp sanitized-mbpp.json",
                  "checks_per_instance": "3-4 asserts",
                  "contamination": "pre-cutoff (2021); stated, not mitigated"})


def build_mbppplus(rows: Sequence[dict[str, Any]], *, timeout: float = 30.0,
                   max_checks: int = MAX_IO_CHECKS) -> Suite:
    """EvalPlus MBPP+, 378 tasks. Hidden checks: the EvalPlus extra inputs, scored against the
    reference solution's outputs.

    The reference outputs are generated here, in the sandbox, by running the released canonical
    solution - which is how EvalPlus itself produces its ground truth. Two consequences are handled
    rather than papered over: inputs on which the reference raises are dropped (they are contract
    violations, not tests), and because some tasks' contracts want tuples where the release stores
    lists, both input shapes are probed and the one the reference survives is kept. Whatever shape
    is chosen is then used identically for every arm.
    """
    instances, hidden, dropped = [], {}, []
    for r in rows:
        iid = r["task_id"].replace("Mbpp/", "mbppplus/")
        entry = r["entry_point"]
        visible = r["prompt"].strip()
        inst = Instance(id=iid, suite="mbppplus", visible_prompt=visible, entry_point=entry)
        prompt_norm = _norm(build_prompt(inst))
        raw_inputs = [i for i in (r.get("plus_input") or []) if isinstance(i, list)]
        raw_inputs = [i for i in raw_inputs
                      if _norm(json.dumps(i, sort_keys=True)) not in prompt_norm]
        if not raw_inputs:
            dropped.append((iid, "no hidden input survives the leak filter"))
            continue
        raw_inputs = _stable_sample(raw_inputs, max_checks, iid)
        best: tuple[int, list[dict[str, Any]]] = (0, [])
        for variant in ("as-is", "tuples"):
            shaped = [[tuple(a) if variant == "tuples" and isinstance(a, list) else a for a in case]
                      for case in raw_inputs]
            probe = run_sandbox(
                {"candidate.py": r["canonical_solution"],
                 "checks.json": json.dumps({"entry_point": entry, "inputs": _tag_json(shaped)})},
                _runner_script("probe"), timeout)
            res = probe.result() or {}
            cases = [{"input": _tag_json([case])[0], "expected": o["value"]}
                     for case, o in zip(shaped, res.get("outputs") or []) if o.get("ok")]
            if len(cases) > best[0]:
                best = (len(cases), cases)
            if len(cases) == len(raw_inputs):
                break
        if best[0] < 3:
            dropped.append((iid, f"reference survives only {best[0]} inputs"))
            continue
        instances.append(inst)
        hidden[iid] = HiddenChecks(iid, "io", {"cases": best[1], "atol": r.get("atol") or 0,
                                               "entry_point": entry}, best[0])
    return Suite("mbppplus", instances, hidden,
                 {"source": "evalplus/mbppplus_release v0.2.0",
                  "checks_per_instance": f"up to {max_checks} EvalPlus extra inputs",
                  "dropped": dropped[:40], "n_dropped": len(dropped),
                  "contamination": "MBPP is pre-cutoff (2021); the extra inputs are EvalPlus's "
                                   "(2023) and are not in the task statement"})


def build_bigcodebench(rows: Sequence[dict[str, Any]], *, name: str = "bigcodebench_hard",
                       timeout: float = 90.0, variant: str = "complete") -> Suite:
    """BigCodeBench-Hard, 148 tasks. Hidden checks: the test methods of its `unittest.TestCase`.

    Every instance is gold-checked locally first: the released canonical solution must pass all of
    its own tests in this environment. BigCodeBench assumes a pinned Docker image and we have no
    Docker, so an instance whose libraries are missing here, or whose test wants a network, fails
    for the environment rather than for the model. Those are dropped at preparation time, with
    counts reported, instead of being scored as model failures.

    `variant` picks which of the two released presentations of the same task is shown:

    * ``complete`` - BigCodeBench-Complete: the full docstringed program stub (`complete_prompt`).
    * ``instruct`` - BigCodeBench-Instruct: the same task as a natural-language instruction with the
      docstring's worked examples removed (`instruct_prompt`). It is the harder of the two by
      construction, and the hidden checks, the scorer and the gold filter are identical, so the two
      differ only in how much of the specification the model is given.
    """
    if variant not in ("complete", "instruct"):
        raise ValueError(f"unknown BigCodeBench variant {variant!r}")
    instances, hidden, dropped = [], {}, []
    for r in rows:
        iid = r["task_id"].replace("BigCodeBench/", f"{name}/")
        test_src = r.get("test") or ""
        n_checks = len(_test_method_names(test_src))
        if not n_checks:
            dropped.append((iid, "no test methods"))
            continue
        entry = r.get("entry_point") or "task_func"
        if variant == "complete":
            visible = (f"Complete this program. Keep the given imports and signature, and write the "
                       f"body of `{entry}`; return the whole program.\n\n"
                       f"```python\n{r['complete_prompt'].rstrip()}\n```")
            shown = r["complete_prompt"]
        else:
            instruct = (r.get("instruct_prompt") or "").strip()
            if not instruct:
                dropped.append((iid, "no instruct_prompt"))
                continue
            visible = (f"{instruct}\n\nReturn the whole program, including the imports and the "
                       f"signature shown above.")
            shown = r.get("code_prompt") or r["complete_prompt"]
        inst = Instance(id=iid, suite=name, visible_prompt=visible, entry_point=entry,
                        preamble=shown)
        gold = r["complete_prompt"] + r["canonical_solution"]
        checks = HiddenChecks(iid, "unittest", {"test": test_src}, n_checks)
        score = score_candidate(gold, checks, timeout=timeout)
        if score.passed != score.total or score.total != n_checks:
            dropped.append((iid, f"gold scores {score.passed}/{score.total}: {score.error[:120]}"))
            continue
        instances.append(inst)
        hidden[iid] = checks
    return Suite(name, instances, hidden,
                 {"source": "bigcode-project/bigcodebench-annotation v0.1.1"
                            + (" (Hard split)" if "hard" in name else " (full split)"),
                  "variant": variant,
                  "checks_per_instance": "unittest test methods",
                  "dropped": dropped[:60], "n_dropped": len(dropped),
                  "gold_filter": "canonical solution must pass all of its own tests in this "
                                 "environment (no Docker, Windows)",
                  "contamination": "released 2024; pre-cutoff, stated not mitigated"})


def _stable_sample(items: Sequence[Any], n: int, salt: str) -> list[Any]:
    if len(items) <= n:
        return list(items)
    ranked = sorted(items, key=lambda x: hashlib.sha256(
        f"{salt}|{json.dumps(x, sort_keys=True, default=repr)}".encode()).hexdigest())
    return ranked[:n]


def _tag_json(obj: Any) -> Any:
    """Parent-side mirror of the sandbox `_tag`, for tuples the probe must receive as tuples."""
    if isinstance(obj, tuple):
        return {"__t__": "tuple", "v": [_tag_json(x) for x in obj]}
    if isinstance(obj, list):
        return [_tag_json(x) for x in obj]
    if isinstance(obj, dict):
        return {"__t__": "dict", "v": [[_tag_json(k), _tag_json(v)] for k, v in obj.items()]}
    return obj


BUILDERS: dict[str, Callable[[list[dict[str, Any]]], Suite]] = {
    "mbpp": build_mbpp,
    "mbppplus": build_mbppplus,
    "bigcodebench_hard": build_bigcodebench,
    # the full 1,140-task split: same builder, and worth having as a candidate because the Hard
    # split leaves too few instances behind the no-Docker gold filter to power anything
    "bigcodebench": lambda rows: build_bigcodebench(rows, name="bigcodebench"),
    "bigcodebench_instruct": lambda rows: build_bigcodebench(
        rows, name="bigcodebench_instruct", variant="instruct"),
    "bigcodebench_hard_instruct": lambda rows: build_bigcodebench(
        rows, name="bigcodebench_hard_instruct", variant="instruct"),
}


def prepare_suite(name: str, *, refresh: bool = False, limit: int = 0) -> Suite:
    path = fetch_raw(name, refresh=refresh)
    rows = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else \
        _read_jsonl_gz(path)
    if limit:
        rows = rows[:limit]
    suite = BUILDERS[name](rows)
    leaking = []
    for inst in list(suite.instances):
        try:
            verify_no_leak(inst, suite.hidden[inst.id])
        except HiddenTestLeak as exc:
            # A dataset whose task statement already contains one of its own checks is not a bug in
            # the harness, but the instance is unusable: drop it here, count it, and keep the
            # invariant absolute everywhere downstream (`load_suite` raises rather than filters).
            leaking.append((inst.id, str(exc)[:200]))
            suite.instances.remove(inst)
            suite.hidden.pop(inst.id, None)
    suite.notes["n_leaking_dropped"] = len(leaking)
    suite.notes["leaking_dropped"] = leaking[:40]
    save_suite(suite)
    return suite


def save_suite(suite: Suite) -> Path:
    SUITES_DIR.mkdir(parents=True, exist_ok=True)
    path = SUITES_DIR / f"{suite.name}.json"
    payload = {
        "name": suite.name, "protocol": PROTOCOL_VERSION, "prompt_sha": prompt_sha(),
        "prepared": datetime.now(UTC).isoformat(timespec="seconds"), "notes": suite.notes,
        "instances": [dataclasses.asdict(i) for i in suite.instances],
        "hidden": {k: dataclasses.asdict(v) for k, v in suite.hidden.items()},
        "pools": {i.id: pool_of(suite.name, i.id) for i in suite.instances},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def load_suite(name: str) -> Suite:
    path = SUITES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} not prepared: run `tier3_ablation.py prepare`")
    d = json.loads(path.read_text(encoding="utf-8"))
    suite = Suite(d["name"], [Instance(**i) for i in d["instances"]],
                  {k: HiddenChecks(**v) for k, v in d["hidden"].items()}, d.get("notes", {}))
    for inst in suite.instances:  # the invariant is re-checked on load, not trusted from the file
        verify_no_leak(inst, suite.hidden[inst.id])
    return suite


# ---- Amendment 12a: the visible (public) checks, stored beside the suite, never inside it. The
# prepared suite files are left byte-identical; the visible checks live in suites/visible/<name>.json.


def visible_path(name: str) -> Path:
    return SUITES_DIR / "visible" / f"{name}.json"


def save_visible(name: str, visible: dict[str, VisibleChecks], notes: dict[str, Any]) -> Path:
    path = visible_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"suite": name, "protocol": PROTOCOL_VERSION_V2,
               "prepared": datetime.now(UTC).isoformat(timespec="seconds"), "notes": notes,
               "visible": {k: dataclasses.asdict(v) for k, v in visible.items()}}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def load_visible(name: str, suite: Suite) -> dict[str, VisibleChecks]:
    """The visible checks of a prepared suite, re-verified against its hidden checks on every load.

    Every instance of the suite must have an entry (possibly with no examples); a visible check for an
    instance the suite does not contain is refused, and so is any visible check that reproduces a
    hidden one, and so is any prompt the Bext arm could send for that instance that would show one.
    """
    path = visible_path(name)
    if not path.exists():
        raise FileNotFoundError(f"{path} not prepared: run `tier3_ablation.py prepare-visible`")
    d = json.loads(path.read_text(encoding="utf-8"))
    out = {k: VisibleChecks(**v) for k, v in d["visible"].items()}
    ids = {i.id for i in suite.instances}
    stray = set(out) - ids
    if stray:
        raise ValueError(f"{path.name}: visible checks for instances not in the suite: "
                         f"{sorted(stray)[:5]}")
    missing = ids - set(out)
    if missing:
        raise ValueError(f"{path.name}: no visible-check entry for {len(missing)} instances "
                         f"(e.g. {sorted(missing)[:3]}); re-run prepare-visible")
    for inst in suite.instances:
        if out[inst.id].instance_id != inst.id:
            raise ValueError(f"{path.name}: entry {inst.id!r} holds checks for "
                             f"{out[inst.id].instance_id!r}")
        verify_no_leak(inst, suite.hidden[inst.id], out[inst.id])
    return out


def _task_number(instance_id: str) -> str:
    return instance_id.rsplit("/", 1)[-1]


def prepare_visible(name: str, *, timeout: float = 60.0, workers: int = 6,
                    only: set[str] | None = None) -> dict[str, VisibleChecks]:
    """Build the public checks for a prepared BigCodeBench-family suite from its docstring examples.

    The examples come from the released `complete_prompt` (the docstring), whichever presentation the
    suite shows: for an Instruct suite they are exactly what that presentation withholds from the
    prompt, which is why Bext changes what the model can learn and is stated as doing so (amendment
    12a). The gold solution used for the filter is the released canonical one, as for the hidden
    tests. No model is called.
    """
    from concurrent.futures import ThreadPoolExecutor

    if not name.startswith("bigcodebench"):
        raise ValueError(f"visible checks are defined for the BigCodeBench family only, not {name!r}")
    suite = load_suite(name)
    rows = {str(r["task_id"]).rsplit("/", 1)[-1]: r for r in _read_jsonl_gz(fetch_raw(name))}
    todo = [i for i in suite.instances if only is None or i.id in only]

    def one(inst: Instance) -> VisibleChecks:
        r = rows[_task_number(inst.id)]
        return build_visible_checks(inst.id, r["complete_prompt"], inst.entry_point,
                                    r["complete_prompt"] + r["canonical_solution"],
                                    hidden=suite.hidden[inst.id], timeout=timeout)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        built = dict(zip([i.id for i in todo], pool.map(one, todo)))
    if only is not None:  # keep entries already on disk for the instances not rebuilt
        try:
            built = {**load_visible_unchecked(name), **built}
        except FileNotFoundError:
            pass
    for inst in suite.instances:
        built.setdefault(inst.id, VisibleChecks(inst.id, "doctest", [], "docstring"))
    covered = [v for v in built.values() if v.n_checks]
    notes = {
        "source": "docstring examples of complete_prompt (BigCodeBench v0.1.1)",
        "gold_filter": "canonical solution must pass every kept example here (no Docker, Windows)",
        "overlap_filter": "examples whose expected value the hidden test also asserts are withheld",
        "n_instances": len(built), "n_with_visible_checks": len(covered),
        "n_examples_parsed": sum(v.n_parsed for v in built.values()),
        "n_examples_kept": sum(v.n_checks for v in built.values()),
        "n_dropped_overlap": sum(v.n_dropped_overlap for v in built.values()),
        "n_dropped_gold": sum(v.n_dropped_gold for v in built.values()),
    }
    save_visible(name, built, notes)
    return load_visible(name, suite)


def load_visible_unchecked(name: str) -> dict[str, VisibleChecks]:
    """The raw file, for merging a partial rebuild. Never used by a runner (`load_visible` is)."""
    path = visible_path(name)
    if not path.exists():
        raise FileNotFoundError(path)
    d = json.loads(path.read_text(encoding="utf-8"))
    return {k: VisibleChecks(**v) for k, v in d["visible"].items()}


# ======================================================================================
# Analysis: arm-A band, seed variance, and the instance count for 80% power
# ======================================================================================


def _t_ppf(p: float, df: int) -> float:
    from scipy import stats
    return float(stats.t.ppf(p, df))


def mde(sd_diff: float, n: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Minimum detectable paired difference, as `analyse_outcomes.mde_from_key_differences`."""
    if n < 2 or not math.isfinite(sd_diff):
        return float("nan")
    return (_t_ppf(1 - alpha / 2, n - 1) + _t_ppf(power, n - 1)) * sd_diff / math.sqrt(n)


def n_for_power(sd_diff: float, delta: float = TARGET_EFFECT, alpha: float = 0.05,
                power: float = 0.80, cap: int = 100_000) -> int:
    """Smallest paired n whose MDE is at or below `delta`. Inverts `mde` numerically."""
    if sd_diff <= 0:
        return 2
    n = max(3, math.ceil(((1.96 + 0.8416) * sd_diff / delta) ** 2))
    while n <= cap and mde(sd_diff, n, alpha, power) > delta:
        n += max(1, n // 50)
    return min(n, cap)


def sd_of_difference(var_between: float, var_run: float, rho: float, s: int) -> float:
    """SD of the per-instance B-C difference, from pilot variance components.

    Two sources. Run-to-run noise enters twice (once per arm) and is cut by averaging `s` seeds:
    `2 * var_run / s`. Instance difficulty enters through the part the pairing does *not* remove:
    `2 * (1 - rho) * var_between`, with `rho` the correlation of the two arms' instance means.
    `rho` cannot be estimated from an arm-A-only pilot, so it is reported across a range instead of
    assumed - the honest way to present a power calculation from a one-arm pilot.
    """
    return math.sqrt(max(0.0, 2 * (1 - rho) * var_between) + max(0.0, 2 * var_run / max(1, s)))


def active_fraction_power(p_active: float, delta: float = TARGET_EFFECT, alpha: float = 0.05,
                          power: float = 0.80) -> dict[str, float]:
    """Power for the B-C contrast given how often arm B actually spends more than one call.

    The variance-component calculation above assumes every instance contributes noise to the paired
    difference. It does not, and that is the dominant fact about this design. On an instance where
    B's own checks pass on the first attempt, B is one call, C is matched to one call, both arms are
    the same single generation, and the difference is *structurally* zero - not noisy, zero. Only
    the `p_active` fraction of instances where B retries can contribute anything at all.

    Model the difference as 0 on (1 - p) of instances and `g` on the rest. Then the estimand is
    `delta = p * g`, its SD is `g * sqrt(p * (1 - p))`, and the required n is

        n = (t_{1-alpha/2} + t_{power})^2 * (1 - p) / p

    which does not depend on `g` at all. What `g` decides is whether `delta` can reach the target:
    since `g <= 1`, the largest average effect this design can produce is `p`, and reaching `delta`
    at all requires a per-active-instance gain of `delta / p`. Returns both, because a target that
    needs `min_gain > 1` is unreachable at any sample size and that is a fact about the design, not
    about the budget.
    """
    p = min(max(float(p_active), 1e-9), 1.0)
    z = 1.96 + 0.8416  # normal approximation; the exact t version differs by <1 instance here
    n = z * z * (1 - p) / p
    n_int = max(2, math.ceil(n))
    df = max(1, n_int - 1)
    n_exact = max(2, math.ceil((_t_ppf(1 - alpha / 2, df) + _t_ppf(power, df)) ** 2 * (1 - p) / p))
    return {"p_active": p, "n_instances_80pct": float(n_exact),
            "max_attainable_effect": p, "min_gain_on_active_instances": delta / p}


def choose_seeds(var_run: float, delta: float = TARGET_EFFECT, minimum: int = 3,
                 maximum: int = 12) -> int:
    """Smallest s >= 3 with seed noise alone at or below half the effect: sqrt(2*var_run/s) <= d/2.

    Pre-stated here so the pilot's numbers pick `s` rather than the other way round.
    """
    for s in range(minimum, maximum + 1):
        if math.sqrt(2 * var_run / s) <= delta / 2:
            return s
    return maximum


def arm_b_diagnostics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """How much extra compute arm B actually spends, per (suite, tier), and what that buys in power.

    Empty unless the file contains arm-B rows - the registered pilot is arm A only, so this reports
    on a separate arm-B diagnostic run. It is not an effect estimate and contains no B-C contrast:
    it is the `p_active` that `active_fraction_power` needs, because an instance where B's own
    checks pass first time gives B and C the same single call and a difference of exactly zero.
    """
    b = [r for r in latest_ok(rows).values() if r.get("arm") == "B"]
    out: dict[str, Any] = {}
    for suite, tier in sorted({(r["suite"], r.get("model_requested") or r.get("model", ""))
                               for r in b}):
        rs = [r for r in b if r["suite"] == suite
              and (r.get("model_requested") or r.get("model", "")) == tier]
        calls = [int(r.get("calls") or 0) for r in rs]
        active = sum(1 for c in calls if c > 1)
        checks_written = sum(1 for r in rs
                             if (r.get("self_checks") or [{}])[0].get("ran"))
        entry = {"n_rows": len(rs), "mean_calls": statistics.fmean(calls) if calls else 0.0,
                 "call_distribution": {str(c): calls.count(c) for c in sorted(set(calls))},
                 "instances_where_b_retried": active,
                 "p_active": active / len(rs) if rs else 0.0,
                 "self_checks_written_and_run": checks_written,
                 "calls_per_instance_seed_all_three_arms":
                     1 + 2 * (statistics.fmean(calls) if calls else 0.0)}
        entry["power"] = active_fraction_power(entry["p_active"]) if rs else {}
        out[f"{suite}@{tier}"] = entry
    return out


def summarise_arm_a(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Arm-A accuracy per (suite, model tier), the band verdict, seed variance, s, and n for 80%.

    The unit is the pair, not the suite: criterion 2 is a statement about arm-A accuracy, and the
    protocol's Model section fixes the tier as "whatever the pilot shows to sit in the accuracy
    band", so a suite is only in or out of the band *for a given tier*.
    """
    ok = [r for r in latest_ok(rows).values() if r.get("arm") == "A"]
    out: dict[str, Any] = {"protocol": PROTOCOL_VERSION, "band": list(BAND),
                           "target_effect": TARGET_EFFECT, "suites": {}}
    keys = sorted({(r["suite"], r.get("model_requested") or r.get("model", "")) for r in ok})
    for suite, tier in keys:
        label = f"{suite}@{tier}"
        rs = [r for r in ok if r["suite"] == suite
              and (r.get("model_requested") or r.get("model", "")) == tier]
        per_instance: dict[str, list[float]] = {}
        for r in rs:
            per_instance.setdefault(r["instance_id"], []).append(float(r["score"]))
        means = [statistics.fmean(v) for v in per_instance.values()]
        binaries = [statistics.fmean([1.0 if s >= 1.0 else 0.0 for s in v])
                    for v in per_instance.values()]
        within = [statistics.variance(v) for v in per_instance.values() if len(v) > 1]
        var_run = statistics.fmean(within) if within else float("nan")
        var_between = statistics.variance(means) if len(means) > 1 else float("nan")
        acc = statistics.fmean(means) if means else float("nan")
        entry: dict[str, Any] = {
            "suite": suite, "model_requested": tier,
            "n_instances": len(per_instance), "n_rows": len(rs),
            "seeds_per_instance": sorted({len(v) for v in per_instance.values()}),
            "arm_a_continuous": acc,
            "arm_a_binary": statistics.fmean(binaries) if binaries else float("nan"),
            "sd_between_instances": (math.sqrt(var_between) if not math.isnan(var_between)
                                     else float("nan")),
            "var_between_instances": var_between, "var_run_within_instance": var_run,
            "sd_run_within_instance": (math.sqrt(var_run) if not math.isnan(var_run)
                                       else float("nan")),
            "in_band": bool(means) and BAND[0] <= acc <= BAND[1],
            "models": sorted({r.get("model", "") for r in rs}),
            "mean_checks_per_instance": statistics.fmean([float(r.get("total") or 0) for r in rs]),
        }
        if within and not math.isnan(var_between):
            s = choose_seeds(var_run)
            entry["seeds_s"] = s
            entry["power"] = {
                f"rho={rho}": {"sd_diff": sd_of_difference(var_between, var_run, rho, s),
                               "n_instances_80pct":
                                   n_for_power(sd_of_difference(var_between, var_run, rho, s))}
                for rho in (0.0, 0.5, 0.7, 0.9)
            }
        out["suites"][label] = entry
    out["arm_b_diagnostics"] = arm_b_diagnostics(rows)
    in_band = [s for s, e in out["suites"].items() if e.get("in_band")]
    chosen = (min(in_band, key=lambda s: abs(
        out["suites"][s]["arm_a_continuous"] - statistics.fmean(BAND))) if in_band else None)
    out["selected"] = chosen
    out["selected_suite"] = out["suites"][chosen]["suite"] if chosen else None
    out["selected_model"] = out["suites"][chosen]["model_requested"] if chosen else None
    out["verdict"] = ("selected by criterion 2 (closest to the middle of the band)" if chosen else
                      "no candidate suite/tier lands in the 25-70% band: per the protocol this is "
                      "a failed experiment, not a re-tuned band")
    return out


# ---- Amendment 12a: the v2 pilot summary (arms A and B variants only; never a contrast)


def firing_power(q_fire: float, var_between: float, var_run: float, s: int,
                 delta: float = TARGET_EFFECT,
                 rhos: Sequence[float] = (0.0, 0.5, 0.7, 0.9)) -> dict[str, Any]:
    """Instances needed for amendment 12a's primary estimand: B - C on the firing stratum.

    The v1 route (`active_fraction_power`) models the unconditional contrast as p * g and shows it is
    capped at p. v2 estimates g directly, on the instances where the treatment fires, so the paired
    n is the ordinary variance-route n for a 7-point effect *within* that stratum, and the instances
    that must be run are that n divided by the probability `q_fire` that an instance lands in it.
    """
    q = min(max(float(q_fire), 1e-9), 1.0)
    out: dict[str, Any] = {"q_fire": q, "seeds_s": s, "delta": delta}
    for rho in rhos:
        sd = sd_of_difference(var_between, var_run, rho, s)
        n_s = n_for_power(sd, delta)
        out[f"rho={rho}"] = {"sd_diff": sd, "n_firing_instances": n_s,
                             "n_instances_to_run": math.ceil(n_s / q)}
    return out


def a_visible_failures(a_rows: Sequence[dict[str, Any]], visible: dict[str, VisibleChecks],
                       timeout: float = 60.0) -> dict[str, dict[str, int]]:
    """Per instance: how many arm-A draws fail the public examples. No model is called.

    Arm Bext's first prompt is byte-identical to arm A's, so an arm-A draw that fails the public
    examples is exactly a draw on which Bext would have repaired. This is the arm-independent
    definition of the firing stratum in amendment 12a: it selects instances on arm A, which is
    neither of the two arms being contrasted.
    """
    out: dict[str, dict[str, int]] = {}
    for r in a_rows:
        vis = visible.get(r["instance_id"])
        entry = out.setdefault(r["instance_id"], {"draws": 0, "fail": 0, "has_visible": 0})
        if vis is None or not vis.n_checks:
            continue
        entry["has_visible"] = 1
        entry["draws"] += 1
        if not run_visible_checks(r.get("final_code") or "", vis, timeout=timeout).ok:
            entry["fail"] += 1
    return out


def summarise_v2(rows: Sequence[dict[str, Any]], a_rows: Sequence[dict[str, Any]] = (),
                 a_fire: dict[str, dict[str, dict[str, int]]] | None = None) -> dict[str, Any]:
    """The v2 pilot table: per (suite, tier, B variant) p_active, mean calls, accuracy, n.

    Descriptive only. There is no arm C in the v2 pilot and no difference between arms is formed
    here: arm A's accuracy on the same instances is reported beside each variant because criterion 2
    is about it, not as a comparator.
    """
    ok = [r for r in latest_ok(rows).values() if r.get("arm") in B_ARMS]
    a_ok = [r for r in latest_ok(a_rows).values() if r.get("arm") == "A"]
    out: dict[str, Any] = {"protocol": PROTOCOL_VERSION_V2, "estimand": "B-C on the firing stratum",
                           "no_contrast": True, "cells": {}}
    for suite, tier, arm in sorted({(r["suite"], r.get("model_requested") or r.get("model", ""),
                                     r["arm"]) for r in ok}):
        rs = [r for r in ok if r["suite"] == suite and r["arm"] == arm
              and (r.get("model_requested") or r.get("model", "")) == tier]
        calls = [int(r.get("calls") or 0) for r in rs]
        scores = [float(r.get("score") or 0.0) for r in rs]
        first_ok = [r for r in rs if int(r.get("calls") or 0) == 1]
        entry: dict[str, Any] = {
            "suite": suite, "model_requested": tier, "arm": arm,
            "n_rows": len(rs), "n_instances": len({r["instance_id"] for r in rs}),
            "p_active": sum(1 for c in calls if c > 1) / len(rs),
            "mean_calls": statistics.fmean(calls),
            "call_distribution": {str(c): calls.count(c) for c in sorted(set(calls))},
            "accuracy_continuous": statistics.fmean(scores),
            "accuracy_binary": statistics.fmean([float(r.get("binary") or 0) for r in rs]),
            "accepted_first_attempt": len(first_ok),
            "accepted_first_attempt_scoring_zero": sum(1 for r in first_ok
                                                       if float(r.get("score") or 0) == 0.0),
            "verification_ran_on_first_attempt": sum(
                1 for r in rs if (r.get("self_checks") or [{}])[0].get("ran")),
            "models": sorted({r.get("model", "") for r in rs}),
            "mean_cost_usd_per_call": (sum(float(r.get("cost_usd") or 0) for r in rs)
                                       / max(1, sum(calls))),
        }
        if arm == "Bext":
            covered = [r for r in rs if int(r.get("visible_n_checks") or 0) > 0]
            entry["n_with_visible_checks"] = len(covered)
            entry["p_active_where_visible_checks_exist"] = (
                sum(1 for r in covered if int(r.get("calls") or 0) > 1) / len(covered)
                if covered else float("nan"))
        ids = {r["instance_id"] for r in rs}
        a_same = [r for r in a_ok if r["suite"] == suite and r["instance_id"] in ids
                  and (r.get("model_requested") or r.get("model", "")) == tier]
        if a_same:
            per: dict[str, list[float]] = {}
            for r in a_same:
                per.setdefault(r["instance_id"], []).append(float(r["score"]))
            entry["arm_a_same_instances"] = {
                "n_instances": len(per), "n_rows": len(a_same),
                "continuous": statistics.fmean(statistics.fmean(v) for v in per.values()),
                "binary": statistics.fmean(statistics.fmean(1.0 if s >= 1.0 else 0.0 for s in v)
                                           for v in per.values())}
        out["cells"][f"{suite}@{tier}:{arm}"] = entry
    if a_fire:
        out["arm_a_fires_bext"] = {}
        for label, per in a_fire.items():
            withv = {k: v for k, v in per.items() if v["has_visible"]}
            draws = sum(v["draws"] for v in withv.values())
            out["arm_a_fires_bext"][label] = {
                "n_instances": len(per), "n_with_visible_checks": len(withv),
                "draw_level_fire_rate": (sum(v["fail"] for v in withv.values()) / draws
                                         if draws else float("nan")),
                "instances_firing_on_any_draw": sum(1 for v in withv.values() if v["fail"]),
                "instance_level_q_all_instances": (sum(1 for v in withv.values() if v["fail"])
                                                   / len(per) if per else float("nan")),
                "draws_per_instance": sorted({v["draws"] for v in withv.values()}),
            }
    return out


def write_scores_csv(rows: Sequence[dict[str, Any]], path: Path) -> Path:
    """One row per (suite, instance, arm): the seed-averaged score the contrast is computed on."""
    ok = list(latest_ok(rows).values())
    agg: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for r in ok:
        tier = r.get("model_requested") or r.get("model", "")
        agg.setdefault((r["suite"], tier, r["instance_id"], r["arm"]), []).append(r)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["suite", "model_requested", "instance_id", "arm", "seeds", "score_mean",
                    "score_sd", "binary_mean", "calls_mean", "checks_total", "model"])
        for (suite, tier, iid, arm), rs in sorted(agg.items()):
            scores = [float(r["score"]) for r in rs]
            w.writerow([suite, tier, iid, arm, len(rs), f"{statistics.fmean(scores):.6f}",
                        f"{statistics.stdev(scores):.6f}" if len(scores) > 1 else "",
                        f"{statistics.fmean([float(r['binary']) for r in rs]):.6f}",
                        f"{statistics.fmean([float(r.get('calls') or 0) for r in rs]):.4f}",
                        rs[0].get("total", ""), rs[0].get("model", "")])
    return path


# ======================================================================================
# CLI
# ======================================================================================


def setup_logging(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "run.log"
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding="utf-8")):
        h.setFormatter(fmt)
        root.addHandler(h)
    return log_path


def make_gen(
    backend: Callable[..., Any], exe: str, model: str, system_file: Path, log_path: Path,
    *, effort: str | None = None, sleeper: Callable[[float], None] = time.sleep,
    max_wait: int = 6 * 3600,
) -> Callable[..., Generation]:
    """Bind the backend into the single generation path, with usage-limit handling around it."""
    def gen(inst: Instance, **kw: Any) -> Generation:
        return with_limit_handling(
            lambda: generate(inst, backend=backend, exe=exe, model=model,
                             system_file=system_file, effort=effort, **kw),
            log_path=log_path, label=f"{inst.suite}/{inst.id}", sleeper=sleeper, max_wait=max_wait)
    return gen


def cmd_prepare(args: argparse.Namespace) -> int:
    setup_logging(TIER3)
    names = list(SUITE_SOURCES) if args.suite == "all" else args.suite.split(",")
    for name in names:
        suite = prepare_suite(name, refresh=args.refresh, limit=args.limit)
        pilot = sum(1 for i in suite.instances if pool_of(name, i.id) == "pilot")
        log.info("%s: %d instances (%d pilot / %d confirmatory), %d dropped; checks/instance "
                 "min %d median %d max %d", name, len(suite.instances), pilot,
                 len(suite.instances) - pilot, suite.notes.get("n_dropped", 0),
                 *_check_spread(suite))
    return 0


def _check_spread(suite: Suite) -> tuple[int, int, int]:
    counts = sorted(h.n_checks for h in suite.hidden.values()) or [0]
    return counts[0], counts[len(counts) // 2], counts[-1]


def phase_pool(phase: str) -> str:
    """Only the confirmatory phase ever reads the confirmatory pool; every other phase the pilot's.

    Written as an allow-list of one so that a new phase name (the v2 pilot's `pilot-v2`) can never
    fall through to the confirmatory pool by accident, which the v1 expression would have allowed.
    """
    return "confirmatory" if phase == "confirmatory" else "pilot"


def _run_phase(args: argparse.Namespace, phase: str, out_dir: Path, arms: Sequence[str],
               backend: Callable[..., Any] | None, sleeper: Callable[[float], None]) -> int:
    log_path = setup_logging(out_dir)
    runs = out_dir / "runs.jsonl"
    if backend is None:
        os.environ["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"  # ~58k tokens of tool schemas otherwise
        backend = screen_llm.vote_batch_claude_code
    exe = ""
    if backend is screen_llm.vote_batch_claude_code:
        exe = screen_llm.find_claude_exe() or ""
        if not exe:
            print("claude executable not found (set CLAUDE_CODE_EXE)", file=sys.stderr)
            return 2
    tmpdir = Path(tempfile.mkdtemp(prefix="tier3_sys_"))
    system_file = tmpdir / "system_prompt.txt"
    system_file.write_text(SYSTEM_PROMPT, encoding="utf-8")
    gen = make_gen(backend, exe, args.model, system_file, log_path, effort=args.effort,
                   sleeper=sleeper, max_wait=args.max_wait)
    rows = read_rows(runs)
    done, prior = done_keys(rows), latest_ok(rows)
    seeds = list(range(1, args.seeds + 1))
    t0 = time.time()
    n_new = 0
    try:
        for name in args.suites.split(","):
            suite = load_suite(name)
            visible = load_visible(name, suite) if "Bext" in arms else None
            if phase == "confirmatory":  # amendment 12a, s.5: never a task any pilot has touched
                chosen = confirmatory_instances(suite, args.n, piloted_tasks())
            else:
                chosen = select_instances(suite, phase_pool(phase), args.n)
            shard = getattr(args, "shard", None)
            if shard:  # "i/m": this process takes every m-th instance, from the i-th
                i, m = (int(x) for x in shard.split("/"))
                chosen = chosen[i::m]
            log.info("%s: %d instances x %d seeds x arms %s (phase %s, model %s)", name,
                     len(chosen), len(seeds), ",".join(_arm_order(arms)), phase, args.model)
            for inst in chosen:
                for seed in seeds:
                    written = run_instance(
                        suite, inst, arms=arms, seed=seed, gen=gen, out_path=runs, phase=phase,
                        model=args.model, k=args.k, timeout=args.timeout, done=done, prior=prior,
                        visible=visible)
                    for r in written:
                        if r.get("status") == "ok":
                            done.add(r["key"])
                            prior[r["key"]] = r
                    n_new += len(written)
                    if written:
                        log.info("%s seed %d: %s", inst.id, seed, ", ".join(
                            f"{r['arm']}={r.get('score', r.get('status')):.3f}"
                            if isinstance(r.get("score"), float) else f"{r['arm']}={r['status']}"
                            for r in written))
    except CreditsExhausted as exc:
        log.error("stopping: the balance/subscription is exhausted (%s). %d rows written; re-run to "
                  "resume", str(exc)[:200], n_new)
        return 3
    except KeyboardInterrupt:
        log.warning("interrupted; %d rows written, re-run to resume", n_new)
        return 130
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    log.info("%d rows in %.1f min -> %s", n_new, (time.time() - t0) / 60, runs)
    return 0


def cmd_pilot(args: argparse.Namespace, backend: Callable[..., Any] | None,
              sleeper: Callable[[float], None]) -> int:
    """Arm A only, on the disjoint pilot pool, into data/tier3/pilot/. Never pooled."""
    rc = _run_phase(args, "pilot", PILOT_DIR, ["A"], backend, sleeper)
    if rc == 0 or args.report_anyway:
        cmd_report(args)
    return rc


def cmd_report(args: argparse.Namespace) -> int:
    runs = Path(getattr(args, "runs", None) or (PILOT_DIR / "runs.jsonl"))
    rows = read_rows(runs)
    if not rows:
        print(f"no rows in {runs}", file=sys.stderr)
        return 2
    summary = summarise_arm_a(rows)
    out_dir = runs.parent
    (out_dir / "pilot_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_scores_csv(rows, out_dir / "pilot_scores.csv")
    print(json.dumps(summary, indent=2))
    return 0


def cmd_confirmatory(args: argparse.Namespace, backend: Callable[..., Any] | None,
                     sleeper: Callable[[float], None]) -> int:
    """Refuses to score a confirmatory instance until amendment 12 is registered.

    The protocol's whole point: "Nothing below may be changed after the first confirmatory instance
    is scored" only means something if the design is registered before that instance is scored.
    """
    if not REGISTRATION_MARKER.exists() or not args.registered:
        print(f"refusing to run: the protocol requires OSF amendment 12 to be registered before "
              f"the first confirmatory instance is scored. Write the OSF registration URL and date "
              f"to {REGISTRATION_MARKER} and pass --registered.", file=sys.stderr)
        return 2
    b_arm = getattr(args, "b_arm", "B") or "B"
    if b_arm not in B_ARMS:
        print(f"unknown --b-arm {b_arm!r}; one of {', '.join(B_ARMS)}", file=sys.stderr)
        return 2
    rc = _run_phase(args, "confirmatory", TIER3, ["A", b_arm, "C"], backend, sleeper)
    rows = read_rows(TIER3 / "runs.jsonl")
    if rows:
        write_scores_csv(rows, TIER3 / "instance_scores.csv")
    return rc


def cmd_prepare_visible(args: argparse.Namespace) -> int:
    setup_logging(TIER3)
    for name in args.suite.split(","):
        vis = prepare_visible(name, timeout=args.timeout, workers=args.workers)
        covered = sum(1 for v in vis.values() if v.n_checks)
        suite = load_suite(name)
        pools = {p: [i for i in suite.instances if pool_of(name, i.id) == p]
                 for p in ("pilot", "confirmatory")}
        log.info("%s: %d/%d instances have public checks (pilot %d/%d, confirmatory %d/%d)", name,
                 covered, len(vis),
                 sum(1 for i in pools["pilot"] if vis[i.id].n_checks), len(pools["pilot"]),
                 sum(1 for i in pools["confirmatory"] if vis[i.id].n_checks),
                 len(pools["confirmatory"]))
    return 0


def cmd_pilot_v2(args: argparse.Namespace, backend: Callable[..., Any] | None,
                 sleeper: Callable[[float], None]) -> int:
    """Amendment 12a's pilot: arm A and the B variants, pilot pool only, never arm C.

    No C means no contrast can be formed from this output, which is the point: the v2 pilot measures
    whether each B variant spends its budget (p_active, mean calls) and what it scores, and nothing
    that could be read as an effect. It writes under `data/tier3/pilot_v2/` and refuses the
    confirmatory tree.
    """
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    bad = [a for a in arms if a not in ("A", *B_ARMS)]
    if bad:
        print(f"refusing: the v2 pilot runs arm A and the B variants only, never {bad} (no arm C, "
              f"so no contrast is ever formed from the pilot)", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir) if args.out_dir else V2_PILOT_DIR
    if out_dir.resolve() == TIER3.resolve() or out_dir.resolve() == PILOT_DIR.resolve():
        print("refusing: the v2 pilot never writes into the confirmatory tree or the v1 pilot",
              file=sys.stderr)
        return 2
    return _run_phase(args, "pilot-v2", out_dir, arms, backend, sleeper)


def cmd_report_v2(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else V2_PILOT_DIR
    rows = [r for p in sorted(root.rglob("runs.jsonl")) for r in read_rows(p)]
    if not rows:
        print(f"no rows under {root}", file=sys.stderr)
        return 2
    a_rows = read_rows(Path(args.a_runs)) if args.a_runs else read_rows(PILOT_DIR / "runs.jsonl")
    a_fire: dict[str, dict[str, dict[str, int]]] = {}
    if not args.no_visible:
        for suite_name, tier in sorted({(r["suite"], r.get("model_requested", "")) for r in rows
                                        if r.get("arm") == "Bext"}):
            suite = load_suite(suite_name)
            ids = {r["instance_id"] for r in rows if r["suite"] == suite_name}
            a_same = [r for r in latest_ok(a_rows).values() if r.get("arm") == "A"
                      and r["suite"] == suite_name and r["instance_id"] in ids
                      and r.get("model_requested") == tier]
            a_fire[f"{suite_name}@{tier}"] = a_visible_failures(
                a_same, load_visible(suite_name, suite), timeout=args.timeout)
    summary = summarise_v2(rows, a_rows, a_fire)
    (root / "pilot_v2_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                                encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def main(argv: list[str] | None = None, backend: Callable[..., Any] | None = None,
         sleeper: Callable[[float], None] = time.sleep) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    prep = sub.add_parser("prepare", help="download and build the candidate suites")
    prep.add_argument("--suite", default="all", help="all | comma-separated suite names")
    prep.add_argument("--refresh", action="store_true", help="re-download the raw files")
    prep.add_argument("--limit", type=int, default=0, help="only the first N raw rows (smoke test)")

    for name in ("pilot", "confirmatory"):
        q = sub.add_parser(name)
        q.add_argument("--suites", default=",".join(SUITE_SOURCES))
        q.add_argument("--n", type=int, default=25, help="instances per suite (0 = the whole pool)")
        q.add_argument("--seeds", type=int, default=1, help="seeds per instance")
        q.add_argument("--model", default="sonnet", help="claude -p model: sonnet | opus | haiku")
        q.add_argument("--effort", default=None, help="thinking effort: low|medium|high")
        q.add_argument("--k", type=int, default=4, help="arm B's call ceiling")
        q.add_argument("--timeout", type=float, default=60.0, help="seconds per candidate execution")
        q.add_argument("--max-wait", type=int, default=6 * 3600,
                       help="cap on a usage-limit pause, seconds")
        if name == "pilot":
            q.add_argument("--report-anyway", action="store_true")
        else:
            q.add_argument("--registered", action="store_true",
                           help="OSF amendment 12 is filed (see data/tier3/REGISTERED.txt)")
            q.add_argument("--b-arm", default="B", help="which B variant C is matched to: "
                                                        "B (v1) | Bfix | Bext (amendment 12a)")

    rep = sub.add_parser("report",
                         help="arm-A accuracy per suite, seed variance, s, and n for 80%% power")
    rep.add_argument("--runs", default=None,
                    help="a runs.jsonl to summarise (default: the pilot's); the summary is written "
                         "beside it")

    pv = sub.add_parser("prepare-visible",
                        help="amendment 12a: public checks from the docstring examples (no model)")
    pv.add_argument("--suite", default="bigcodebench_hard_instruct,bigcodebench_instruct")
    pv.add_argument("--timeout", type=float, default=60.0)
    pv.add_argument("--workers", type=int, default=6)

    p2 = sub.add_parser("pilot-v2", help="amendment 12a pilot: arm A and B variants, no arm C")
    p2.add_argument("--suites", default="bigcodebench_hard_instruct")
    p2.add_argument("--arms", default="B,Bfix,Bext", help="subset of A,B,Bfix,Bext")
    p2.add_argument("--n", type=int, default=25, help="instances per suite (0 = the whole pool)")
    p2.add_argument("--seeds", type=int, default=1)
    p2.add_argument("--model", default="haiku")
    p2.add_argument("--effort", default=None)
    p2.add_argument("--k", type=int, default=4, help="call ceiling (Bfix: exact count)")
    p2.add_argument("--timeout", type=float, default=60.0)
    p2.add_argument("--max-wait", type=int, default=6 * 3600)
    p2.add_argument("--out-dir", default=None, help="default data/tier3/pilot_v2")
    p2.add_argument("--shard", default=None,
                    help="i/m: run every m-th selected instance from the i-th (parallel processes, "
                         "each with its own --out-dir under data/tier3/pilot_v2)")

    r2 = sub.add_parser("report-v2", help="amendment 12a pilot table (descriptive, no contrast)")
    r2.add_argument("--root", default=None, help="default data/tier3/pilot_v2 (all runs.jsonl)")
    r2.add_argument("--a-runs", default=None, help="arm-A rows (default: the v1 pilot's)")
    r2.add_argument("--timeout", type=float, default=60.0)
    r2.add_argument("--no-visible", action="store_true",
                    help="skip scoring arm-A draws against the public examples")

    args = p.parse_args(argv)
    if args.cmd == "prepare":
        return cmd_prepare(args)
    if args.cmd == "pilot":
        return cmd_pilot(args, backend, sleeper)
    if args.cmd == "report":
        return cmd_report(args)
    if args.cmd == "prepare-visible":
        return cmd_prepare_visible(args)
    if args.cmd == "pilot-v2":
        return cmd_pilot_v2(args, backend, sleeper)
    if args.cmd == "report-v2":
        return cmd_report_v2(args)
    return cmd_confirmatory(args, backend, sleeper)


if __name__ == "__main__":
    raise SystemExit(main())
