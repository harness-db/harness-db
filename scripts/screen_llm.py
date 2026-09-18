#!/usr/bin/env python
"""LLM third vote for title/abstract screening (plan task S2 / Phase 3 item A2).

For every row of ``data/raw/candidates.csv`` the model votes ``include`` / ``exclude`` /
``unsure`` against the registered criteria, with a one-line reason and the decision-procedure
step that decided (steps 1-3 and 8 of protocol section 3 are the only ones decidable from a
title and abstract). Votes go to ``data/screening/llm_votes.csv``:

    record_id, vote, reason, decision_step, model, prompt_version, tokens_in, tokens_out, cost_usd

This file is a *separate column* in the sense of the protocol (section 7): it is never
merged into, and this script never reads or writes, the human vote files.

The prompt is built at run time from ``docs/protocol_prisma_p.md`` (harness definition
paragraph, decision-procedure steps 1-3 and 8, eligibility criteria (a)-(d) and the exclusion
list of section 4) - nothing is pasted, so a protocol amendment changes the prompt. 20 records
go in each request as a JSON array and the model answers with a JSON object validated
against ``VOTE_SCHEMA``.

Two backends (``--backend``):

* ``api`` - the Anthropic Python SDK (``pip install anthropic``), model ``claude-sonnet-5`` by
  default (plan: "claude-sonnet for cost"), protocol text as a cached system block, structured
  outputs. Needs ``ANTHROPIC_API_KEY`` (environment or repo ``.env``); absent -> exit 2.
  Sonnet 5 rejects sampling parameters, so ``temperature`` is not sent; determinism comes from
  adaptive thinking at ``effort: low`` and the schema-constrained answer.
* ``claude-code`` - Claude Code's headless mode (``claude -p --output-format json
  --json-schema ... --system-prompt-file ...``), which uses the machine's Claude Code login
  (subscription) instead of an API key; model ``opus`` (Claude Opus 5) by default. The
  protocol prompt replaces Claude Code's default system prompt and tools are disabled, but
  Claude Code still sends its own context (~60k cached tokens per call); the ``cost_usd``
  column then holds Claude Code's list-price equivalent (``total_cost_usd``), not a charge.
  The exact model id is taken from the response (``modelUsage``). The binary is found via
  ``CLAUDE_CODE_EXE`` or the ``claude`` shim on PATH.

Batches are resumable (ids already in the output are skipped), retried with exponential
backoff, and can run in parallel (``--workers``).

``--mode tiebreak`` (prompt ``ta-v2-tiebreak-2026-09-17``) is the decisive third vote of the
triage (``scripts/screen_triage.py``, tier T5): the input records are the rows of
``data/screening/triage.csv`` that the two-vote triage left to the human as ``unsure`` or
``conflict`` (verification samples stay human); each record is sent with its title, abstract,
year, source, url and both prior votes (vote, decision step, reason); the schema allows only
``include`` / ``exclude`` plus a reason and a confidence (high / medium / low); the output is
``data/screening/llm_votes_tiebreak.csv`` (``confidence`` replaces ``decision_step``).

Usage:
    python scripts/screen_llm.py --backend claude-code --dry-run 50 --seed 20260917
    python scripts/screen_llm.py --backend claude-code --workers 3          # full run, resumable
    python scripts/screen_llm.py --backend api --model claude-sonnet-5 --dry-run 50
    python scripts/screen_llm.py --mode tiebreak --backend claude-code --workers 8 --batch-size 40 --effort low
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "docs" / "protocol_prisma_p.md"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"
OUT_DIR = REPO / "data" / "screening"
TRIAGE = OUT_DIR / "triage.csv"

PROMPT_VERSION = "ta-v1-2026-09-17"
TIEBREAK_PROMPT_VERSION = "ta-v2-tiebreak-2026-09-17"
TIEBREAK_SAMPLE_TYPES = ("unsure", "conflict")  # triage.csv rows the tiebreak takes over from the human
DEFAULT_MODEL = {"api": "claude-sonnet-5", "claude-code": "opus"}
PRICES_PER_M = {  # USD per million tokens (Anthropic list prices, 2026-06)
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-opus-5": {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25},
    "claude-haiku-4-5": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
}
COLUMNS = ["record_id", "vote", "reason", "decision_step", "model", "prompt_version", "tokens_in", "tokens_out", "cost_usd"]
TIEBREAK_COLUMNS = ["record_id", "vote", "reason", "confidence", "model", "prompt_version", "tokens_in", "tokens_out", "cost_usd"]
ABSTRACT_CHARS = 1800  # per record; abstracts longer than this are cut (title always complete)

VOTE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "votes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string"},
                    "vote": {"type": "string", "enum": ["include", "exclude", "unsure"]},
                    "decision_step": {"type": "string", "enum": ["1", "2", "3", "8", "none"]},
                    "reason": {"type": "string"},
                },
                "required": ["record_id", "vote", "decision_step", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["votes"],
    "additionalProperties": False,
}

TIEBREAK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "votes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string"},
                    "vote": {"type": "string", "enum": ["include", "exclude"]},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string"},
                },
                "required": ["record_id", "vote", "confidence", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["votes"],
    "additionalProperties": False,
}

MODES = {  # mode -> (prompt version, JSON schema, output columns, per-vote extra field, default output file)
    "vote": (PROMPT_VERSION, VOTE_SCHEMA, COLUMNS, "decision_step", "llm_votes.csv"),
    "tiebreak": (TIEBREAK_PROMPT_VERSION, TIEBREAK_SCHEMA, TIEBREAK_COLUMNS, "confidence", "llm_votes_tiebreak.csv"),
}


@dataclass
class BatchResult:
    votes: list[dict[str, str]]
    model: str
    tokens_in: int  # uncached + cache reads + cache writes
    tokens_out: int
    cache_read: int
    cache_write: int
    cost_usd: float


# --------------------------------------------------------------------------------------
# Protocol text (loaded at run time)
# --------------------------------------------------------------------------------------


def _section(md: str, heading: str) -> str:
    """Text of the section whose heading line starts with ``heading`` (up to the next same-level heading)."""
    m = re.search(rf"^(#+)\s+{re.escape(heading)}.*$", md, re.MULTILINE)
    if not m:
        raise ValueError(f"heading not found in protocol: {heading!r}")
    level = len(m.group(1))
    rest = md[m.end():]
    n = re.search(rf"^#{{1,{level}}}\s", rest, re.MULTILINE)
    return rest[: n.start()].strip() if n else rest.strip()


def protocol_excerpts(path: Path = PROTOCOL) -> dict[str, str]:
    md = path.read_text(encoding="utf-8")
    sec3 = _section(md, "3. Definition of a harness")
    definition = sec3.split("Decision procedure")[0].strip()
    steps_text = sec3.split("Decision procedure", 1)[1]
    steps = {}
    for m in re.finditer(r"^(\d+)\.\s+(.*?)(?=^\d+\.\s|\Z)", steps_text, re.MULTILINE | re.DOTALL):
        steps[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
    wanted = {k: steps[k] for k in ("1", "2", "3", "8") if k in steps}
    if len(wanted) != 4:
        raise ValueError(f"decision-procedure steps 1,2,3,8 not all found: {sorted(steps)}")
    sec4 = _section(md, "4. Eligibility criteria")
    criteria = sec4.split("\n### ")[0].strip()  # the (a)-(d) paragraph and the Exclude paragraph, without subsections
    return {"definition": definition, "steps": "\n".join(f"Step {k}. {v}" for k, v in wanted.items()), "criteria": criteria}


def system_prompt(ex: dict[str, str]) -> str:
    return (
        "You are the third, non-binding screener in a pre-registered PRISMA 2020 systematic review of LLM agent "
        "harnesses (HARNESS-Review). You vote on title and abstract only. Your vote is recorded next to, and never "
        "replaces, the two human screeners' votes.\n\n"
        "== Harness definition (protocol section 3, verbatim) ==\n" + ex["definition"] + "\n\n"
        "== Decision procedure, the steps decidable from a title and abstract (protocol section 3, verbatim) ==\n"
        + ex["steps"] + "\n\n"
        "== Eligibility criteria (protocol section 4, verbatim) ==\n" + ex["criteria"] + "\n\n"
        "== How to vote ==\n"
        "Apply the steps in order and stop at the first that decides.\n"
        "- exclude: a step 1, 2, 3 or 8 exclusion is clear from the text (no named system that runs a model; no loop; no executed actions; embodied robotics or first release outside 2022-10-01..2026-08-31). Set decision_step to that step.\n"
        "- include: the text describes a named system that wraps a language model in a loop with tools or an environment (steps 1-3 pass) and nothing in the title/abstract triggers step 8. Set decision_step to \"none\" (no exclusion step fired).\n"
        "- unsure: the title/abstract does not let you decide a step (e.g. a benchmark that may ship a reference agent, a framework that may have a default agent, a component paper that may describe the whole loop, a training paper that may change the harness). Set decision_step to the step you could not decide.\n"
        "Records that only evaluate or discuss existing systems (surveys, empirical comparisons of harnesses, benchmarks) are 'unsure', not 'exclude': the protocol sends them to step 10 at full text.\n"
        "Codability (step 7), duplicates (step 10) and training-only (step 11) are NOT decided here.\n"
        "The reason is at most 25 words, concrete, and names the deciding feature of the text.\n"
        "Answer with one JSON object {\"votes\": [...]}, one entry per input record, same record_id values, same order."
    )


TIEBREAK_PARAGRAPH = (
    "Two earlier screeners disagreed or were unsure. Decide. Title/abstract screening is inclusive: include when the "
    "record could plausibly describe a named system that runs a model in a loop with tools or an environment and that "
    "could be coded from its paper, repository, or documentation; exclude only when the record is clearly a "
    "model/training-only paper, a benchmark or dataset with no reference agent, a survey/position/evaluation-only paper, "
    "a component without a loop (sandbox, MCP server, memory store, skills pack, protocol, tracing SDK), or outside the "
    "scope (robotics) or window. Do not answer unsure."
)


def tiebreak_system_prompt(ex: dict[str, str]) -> str:
    return (
        "You are the deciding third screener in a pre-registered PRISMA 2020 systematic review of LLM agent harnesses "
        "(HARNESS-Review). You vote on title and abstract only. Two earlier screeners have already voted on each record; "
        "their votes, decision steps and reasons are given with the record.\n\n"
        "== Harness definition (protocol section 3, verbatim) ==\n" + ex["definition"] + "\n\n"
        "== Decision procedure, the steps decidable from a title and abstract (protocol section 3, verbatim) ==\n"
        + ex["steps"] + "\n\n"
        "== Eligibility criteria (protocol section 4, verbatim) ==\n" + ex["criteria"] + "\n\n"
        "== Tie-break instruction ==\n" + TIEBREAK_PARAGRAPH + "\n\n"
        "== How to vote ==\n"
        "vote is include or exclude; there is no third option. "
        "confidence is high when the title/abstract settles the decision, medium when it rests on a plausible reading, "
        "low when the text barely lets you decide and full text could easily reverse it. "
        "The reason is at most 30 words, concrete, and names the deciding feature of the text (not the earlier votes).\n"
        "Answer with one JSON object {\"votes\": [...]}, one entry per input record, same record_id values, same order."
    )


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _record_item(r: dict[str, str]) -> dict[str, Any]:
    ab = _clean(r.get("abstract"))
    if len(ab) > ABSTRACT_CHARS:
        ab = ab[:ABSTRACT_CHARS] + " [...]"
    return {"record_id": r["id"], "title": _clean(r.get("title")), "year": r.get("year") or "", "source": r.get("source") or "", "abstract": ab}


def user_prompt(batch: list[dict[str, str]]) -> str:
    return "Records to vote on (JSON):\n" + json.dumps([_record_item(r) for r in batch], ensure_ascii=False)


def tiebreak_item(r: dict[str, str]) -> dict[str, Any]:
    """One tiebreak input record: the vote-mode item plus url and the two prior votes."""
    item = _record_item(r)
    item["url"] = r.get("url") or ""
    item["prior_votes"] = [
        {"screener": k, "vote": r.get(f"vote_{k}") or "", "decision_step": r.get(f"step_{k}") or "", "reason": _clean(r.get(f"reason_{k}"))}
        for k in (1, 2)
    ]
    return item


def tiebreak_user_prompt(batch: list[dict[str, str]]) -> str:
    return "Records to decide, each with the two earlier votes (JSON):\n" + json.dumps([tiebreak_item(r) for r in batch], ensure_ascii=False)


def tiebreak_records(triage_path: Path = TRIAGE, candidates_path: Path = CANDIDATES) -> list[dict[str, str]]:
    """triage.csv rows left to the human as unsure/conflict, with the abstract joined from candidates.csv."""
    with open(candidates_path, encoding="utf-8", newline="") as fh:
        abstracts = {r["id"]: r.get("abstract") or "" for r in csv.DictReader(fh)}
    with open(triage_path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = {"record_id", "needs_human", "human_sample_type", "vote_1", "vote_2", "step_1", "step_2"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{triage_path} lacks columns {sorted(missing)}; re-run scripts/screen_triage.py first")
        rows = [r for r in reader if r["needs_human"] == "1" and r["human_sample_type"] in TIEBREAK_SAMPLE_TYPES]
    for r in rows:
        r["id"] = r["record_id"]
        r["abstract"] = abstracts.get(r["record_id"], "")
    return rows


def _order_votes(votes: list[dict[str, Any]], batch: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {v["record_id"]: v for v in votes}
    missing = [r["id"] for r in batch if r["id"] not in by_id]
    if missing:
        raise ValueError(f"{len(missing)} records without a vote: {missing[:3]}")
    return [by_id[r["id"]] for r in batch]


# --------------------------------------------------------------------------------------
# Backend: Anthropic API
# --------------------------------------------------------------------------------------


def api_key() -> str | None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def _api_cost(model: str, usage: Any) -> float:
    p = PRICES_PER_M.get(model, PRICES_PER_M["claude-sonnet-5"])
    cin = getattr(usage, "input_tokens", 0) or 0
    cout = getattr(usage, "output_tokens", 0) or 0
    cr = getattr(usage, "cache_read_input_tokens", 0) or 0
    cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
    return (cin * p["in"] + cout * p["out"] + cr * p["cache_read"] + cw * p["cache_write"]) / 1e6


def vote_batch_api(client: Any, model: str, system: str, batch: list[dict[str, str]], effort: str = "low", schema: dict[str, Any] = VOTE_SCHEMA, prompt: Any = user_prompt) -> BatchResult:
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt(batch)}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"refusal: {getattr(resp, 'stop_details', None)}")
    text = "".join(b.text for b in resp.content if b.type == "text")
    votes = _order_votes(json.loads(text)["votes"], batch)
    u = resp.usage
    cr, cw = (u.cache_read_input_tokens or 0), (u.cache_creation_input_tokens or 0)
    return BatchResult(votes, model, u.input_tokens + cr + cw, u.output_tokens, cr, cw, _api_cost(model, u))


# --------------------------------------------------------------------------------------
# Backend: Claude Code headless mode (subscription login, no API key)
# --------------------------------------------------------------------------------------


def find_claude_exe() -> str | None:
    if os.environ.get("CLAUDE_CODE_EXE"):
        return os.environ["CLAUDE_CODE_EXE"]
    shim = shutil.which("claude") or shutil.which("claude.cmd")
    if not shim:
        return None
    # npm shim on Windows: the real binary sits next to it and avoids cmd.exe's 8k command-line limit
    real = Path(shim).resolve().parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
    return str(real) if real.exists() else shim


def vote_batch_claude_code(exe: str, model: str, system_file: Path, batch: list[dict[str, str]], effort: str | None = None, schema: dict[str, Any] = VOTE_SCHEMA, prompt: Any = user_prompt) -> BatchResult:
    cmd = [exe, "-p", "--output-format", "json", "--model", model, "--no-session-persistence", "--tools", "", "--system-prompt-file", str(system_file), "--json-schema", json.dumps(schema)]
    if effort:
        cmd += ["--effort", effort]
    proc = subprocess.run(cmd, input=prompt(batch), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900, check=False)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        try:  # Claude Code reports usage-limit / API errors as a JSON envelope with a human-readable result
            env = json.loads(proc.stdout)
            detail = f"{env.get('subtype')} api_error_status={env.get('api_error_status')} result={str(env.get('result'))[:400]}"
        except (json.JSONDecodeError, TypeError):
            pass
        raise RuntimeError(f"claude exited {proc.returncode}: {detail[:600]}")
    d = json.loads(proc.stdout)
    if d.get("is_error") or d.get("subtype") != "success":
        raise RuntimeError(f"claude result {d.get('subtype')}: {str(d.get('result'))[:300]}")
    so = d.get("structured_output") or json.loads(d["result"])
    votes = _order_votes(so["votes"], batch)
    u = d.get("usage") or {}
    cr, cw = u.get("cache_read_input_tokens", 0) or 0, u.get("cache_creation_input_tokens", 0) or 0
    mu = d.get("modelUsage") or {}
    main_model = max(mu, key=lambda k: mu[k].get("outputTokens", 0)) if mu else model
    canonical = (mu.get(main_model) or {}).get("canonicalModel") or main_model
    return BatchResult(votes, canonical, (u.get("input_tokens", 0) or 0) + cr + cw, u.get("output_tokens", 0) or 0, cr, cw, float(d.get("total_cost_usd") or 0.0))


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


RATE_LIMIT_RE = re.compile(r"rate.?limit|429|overloaded|too many requests|capacity", re.IGNORECASE)


def with_retries(fn: Any, log: logging.Logger, label: str, max_attempts: int = 6, max_delay: float = 90.0) -> BatchResult:
    delay = 3.0
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == max_attempts:
                raise
            if "anthropic" in type(exc).__module__ and getattr(exc, "status_code", 500) < 500 and getattr(exc, "status_code", 500) != 429:
                raise  # client-side API errors (400/401/403/404) are not retried
            wait = delay * (2 if RATE_LIMIT_RE.search(str(exc)) else 1)  # rate limits back off harder
            log.warning("%s: %s: %s; retry %d in %.0fs", label, type(exc).__name__, str(exc)[:160], attempt, wait)
            time.sleep(wait)
            delay = min(delay * 2, max_delay)
    raise RuntimeError("unreachable")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--backend", choices=("api", "claude-code"), default="api")
    p.add_argument("--mode", choices=tuple(MODES), default="vote", help="vote (default): every candidate, include/exclude/unsure; tiebreak: the triage's unsure/conflict records, include/exclude only")
    p.add_argument("--candidates", default=str(CANDIDATES))
    p.add_argument("--triage", default=str(TRIAGE), help="tiebreak mode: triage.csv from scripts/screen_triage.py")
    p.add_argument("--out", default=None, help="votes CSV (default data/screening/llm_votes.csv, tiebreak llm_votes_tiebreak.csv; dry runs use *_dryrun.csv)")
    p.add_argument("--model", default=None, help="api: claude-sonnet-5 (default); claude-code: opus (default) | sonnet | full id")
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--workers", type=int, default=1, help="parallel batches")
    p.add_argument("--effort", default=None, help="thinking effort: low|medium|high (api default low; claude-code default = CLI default)")
    p.add_argument("--max-consecutive-failures", type=int, default=5, help="stop the run (it is resumable) after this many batches fail permanently in a row, e.g. a usage-window limit")
    p.add_argument("--max-attempts", type=int, default=6, help="attempts per batch before it counts as a permanent failure")
    p.add_argument("--max-delay", type=float, default=90.0, help="cap on the exponential backoff between attempts (seconds; rate-limit errors wait twice this)")
    p.add_argument("--limit", type=int, default=0, help="stop after N new records (0 = all)")
    p.add_argument("--dry-run", type=int, default=0, metavar="N", help="vote on N random records into a separate file and report cost")
    p.add_argument("--seed", type=int, default=20260917)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("screen_llm")
    model = args.model or DEFAULT_MODEL[args.backend]
    prompt_version, schema, columns, extra_field, default_out = MODES[args.mode]
    prompt_fn = tiebreak_user_prompt if args.mode == "tiebreak" else user_prompt

    ex = protocol_excerpts()
    system = tiebreak_system_prompt(ex) if args.mode == "tiebreak" else system_prompt(ex)
    log.info("mode %s, prompt %s: system block %d chars (definition %d, steps %d, criteria %d)", args.mode, prompt_version, len(system), len(ex["definition"]), len(ex["steps"]), len(ex["criteria"]))

    if args.backend == "api":
        key = api_key()
        if not key:
            print("ANTHROPIC_API_KEY is not set (environment or .env). Nothing was sent; add the key and re-run, or use --backend claude-code.", file=sys.stderr)
            return 2
        try:
            import anthropic
        except ImportError:
            print("The 'anthropic' package is missing: pip install anthropic", file=sys.stderr)
            return 2
        client = anthropic.Anthropic(api_key=key, max_retries=2, timeout=120.0)
        tmpdir = None

        def run_batch(batch: list[dict[str, str]]) -> BatchResult:
            return vote_batch_api(client, model, system, batch, args.effort or "low", schema, prompt_fn)
    else:
        exe = find_claude_exe()
        if not exe:
            print("Claude Code CLI not found (set CLAUDE_CODE_EXE or put 'claude' on PATH).", file=sys.stderr)
            return 2
        tmpdir = tempfile.mkdtemp(prefix="screen_llm_")
        system_file = Path(tmpdir) / "system_prompt.txt"
        system_file.write_text(system, encoding="utf-8")
        log.info("claude-code backend: %s, model alias %r", exe, model)

        def run_batch(batch: list[dict[str, str]]) -> BatchResult:
            return vote_batch_claude_code(exe, model, system_file, batch, args.effort, schema, prompt_fn)

    if args.mode == "tiebreak":
        rows = tiebreak_records(Path(args.triage), Path(args.candidates))
        log.info("tiebreak input: %d unsure/conflict records from %s", len(rows), args.triage)
    else:
        with open(args.candidates, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    out = Path(args.out) if args.out else OUT_DIR / (default_out.replace(".csv", "_dryrun.csv") if args.dry_run else default_out)
    if out.name.lower().startswith(("votes", "rayyan", "asreview", "human")):
        print(f"refusing to write to {out}: looks like a human vote file", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out.exists() and not args.dry_run:
        with out.open(encoding="utf-8", newline="") as fh:
            done = {r["record_id"] for r in csv.DictReader(fh)}
        log.info("resuming: %d records already voted in %s", len(done), out)
    todo = [r for r in rows if r["id"] not in done]
    if args.dry_run:
        random.seed(args.seed)
        todo = random.sample(rows, min(args.dry_run, len(rows)))
    elif args.limit:
        todo = todo[: args.limit]
    batches = [todo[i : i + args.batch_size] for i in range(0, len(todo), args.batch_size)]
    log.info("%d records to vote in %d batches (%d candidates, %d already done, %d workers)", len(todo), len(batches), len(rows), len(done), args.workers)

    new_file = args.dry_run or not out.exists() or out.stat().st_size == 0
    n = tokens_in = tokens_out = cache_read = cache_write = failed = consecutive_failures = 0
    aborted = False
    spent = 0.0
    models: set[str] = set()
    t0 = time.time()
    with out.open("w" if args.dry_run else "a", encoding="utf-8", newline="") as fh, ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        w = csv.writer(fh)
        if new_file:
            w.writerow(columns)
        futures = {pool.submit(with_retries, (lambda b=b: run_batch(b)), log, f"batch {i + 1}/{len(batches)}", args.max_attempts, args.max_delay): b for i, b in enumerate(batches)}
        for k, fut in enumerate(as_completed(futures), 1):
            batch = futures[fut]
            if fut.cancelled():
                continue  # cancelled after the consecutive-failure stop; left for the next resume
            try:
                res = fut.result()
            except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:  # raised by with_retries after the last attempt
                failed += len(batch)
                consecutive_failures += 1
                log.error("batch of %d records failed permanently: %s", len(batch), str(exc)[:600])
                if consecutive_failures >= args.max_consecutive_failures and not aborted:
                    aborted = True
                    log.error("%d consecutive permanent failures (usage limit?): cancelling the remaining batches; re-run later to resume", consecutive_failures)
                    for f in futures:
                        f.cancel()
                continue
            consecutive_failures = 0
            per_in, per_out, per_cost = round(res.tokens_in / len(batch)), round(res.tokens_out / len(batch)), res.cost_usd / len(batch)
            for r, v in zip(batch, res.votes, strict=True):
                w.writerow([r["id"], v["vote"], v["reason"][:200], v[extra_field], res.model, prompt_version, per_in, per_out, f"{per_cost:.6f}"])
            fh.flush()
            n += len(batch)
            tokens_in += res.tokens_in
            tokens_out += res.tokens_out
            cache_read += res.cache_read
            cache_write += res.cache_write
            spent += res.cost_usd
            models.add(res.model)
            if k % 5 == 0 or k == len(batches):
                log.info("%d/%d records voted, $%.3f list-equivalent, cache read %d / write %d, %.0fs", n, len(todo), spent, cache_read, cache_write, time.time() - t0)
    if tmpdir:
        shutil.rmtree(tmpdir, ignore_errors=True)
    per_record = spent / n if n else 0.0
    secs = time.time() - t0
    summary = {
        "backend": args.backend, "mode": args.mode, "effort": args.effort, "batch_size": args.batch_size, "aborted_on_consecutive_failures": aborted, "records_voted": n, "records_failed": failed, "batches": len(batches), "workers": args.workers, "model": sorted(models) or [model], "prompt_version": prompt_version,
        "tokens_in": tokens_in, "tokens_out": tokens_out, "cache_read": cache_read, "cache_write": cache_write,
        "cost_usd": round(spent, 4), "cost_note": "Anthropic list-price equivalent; with --backend claude-code this is consumed as subscription usage, not billed",
        "cost_per_record_usd": round(per_record, 6), "extrapolated_cost_all_candidates_usd": round(per_record * len(rows), 2),
        "seconds": round(secs, 1), "seconds_per_record": round(secs / n, 2) if n else None, "extrapolated_hours_all_candidates": round(secs / n * len(rows) / 3600, 1) if n else None,
        "candidates": len(rows), "out": str(out),
    }
    print("SUMMARY " + json.dumps(summary))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
