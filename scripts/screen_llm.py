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
list of section 4) - nothing is pasted, so a protocol amendment changes the prompt. The
protocol text is sent as a cached system block; 20 records go in each request as a JSON
array and the model answers with a JSON object validated by the API (structured outputs).

Model: ``claude-sonnet-5`` (plan: "claude-sonnet for cost"). Note: the Sonnet 5 API rejects
sampling parameters, so ``temperature`` is not sent; determinism comes from adaptive thinking
at ``effort: low`` and a schema-constrained answer. Prices: $2 / M input, $10 / M output,
cache reads $0.20 / M, cache writes $2.50 / M (Anthropic list prices, 2026-06).

Credentials: ``ANTHROPIC_API_KEY`` from the environment or the repo ``.env``. Absent -> the
script stops with exit code 2 and says so.

Usage:
    python scripts/screen_llm.py                         # full run, resumable (skips voted ids)
    python scripts/screen_llm.py --dry-run 50 --seed 20260917   # 50 random records -> llm_votes_dryrun.csv
    python scripts/screen_llm.py --limit 500 --batch-size 20 --model claude-sonnet-5
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "docs" / "protocol_prisma_p.md"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"
OUT_DIR = REPO / "data" / "screening"

PROMPT_VERSION = "ta-v1-2026-09-17"
DEFAULT_MODEL = "claude-sonnet-5"
PRICES_PER_M = {  # USD per million tokens
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-opus-5": {"in": 5.00, "out": 25.00, "cache_read": 0.50, "cache_write": 6.25},
    "claude-haiku-4-5": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
}
COLUMNS = ["record_id", "vote", "reason", "decision_step", "model", "prompt_version", "tokens_in", "tokens_out", "cost_usd"]
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


def user_prompt(batch: list[dict[str, str]]) -> str:
    items = []
    for r in batch:
        ab = re.sub(r"\s+", " ", r.get("abstract") or "").strip()
        if len(ab) > ABSTRACT_CHARS:
            ab = ab[:ABSTRACT_CHARS] + " [...]"
        items.append({"record_id": r["id"], "title": re.sub(r"\s+", " ", r.get("title") or "").strip(), "year": r.get("year") or "", "source": r.get("source") or "", "abstract": ab})
    return "Records to vote on (JSON):\n" + json.dumps(items, ensure_ascii=False)


# --------------------------------------------------------------------------------------
# API
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


def cost_usd(model: str, usage: Any) -> float:
    p = PRICES_PER_M.get(model, PRICES_PER_M[DEFAULT_MODEL])
    cin = getattr(usage, "input_tokens", 0) or 0
    cout = getattr(usage, "output_tokens", 0) or 0
    cr = getattr(usage, "cache_read_input_tokens", 0) or 0
    cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
    return (cin * p["in"] + cout * p["out"] + cr * p["cache_read"] + cw * p["cache_write"]) / 1e6


def vote_batch(client: Any, model: str, system: str, batch: list[dict[str, str]], log: logging.Logger, max_attempts: int = 6) -> tuple[list[dict[str, str]], Any]:
    """One request for a batch; retries with exponential backoff on rate limits, 5xx, network and bad JSON."""
    import anthropic

    delay = 2.0
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=4096,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user_prompt(batch)}],
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": VOTE_SCHEMA}},
            )
            if resp.stop_reason == "refusal":
                raise RuntimeError(f"refusal: {getattr(resp, 'stop_details', None)}")
            text = "".join(b.text for b in resp.content if b.type == "text")
            votes = json.loads(text)["votes"]
            by_id = {v["record_id"]: v for v in votes}
            missing = [r["id"] for r in batch if r["id"] not in by_id]
            if missing:
                raise ValueError(f"{len(missing)} records without a vote: {missing[:3]}")
            return [by_id[r["id"]] for r in batch], resp.usage
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError) as exc:
            err = f"{type(exc).__name__}"
        except anthropic.APIStatusError as exc:
            if exc.status_code < 500:
                raise
            err = f"HTTP {exc.status_code}"
        except (json.JSONDecodeError, KeyError, ValueError, RuntimeError) as exc:
            err = f"bad answer: {exc}"
        if attempt == max_attempts:
            raise RuntimeError(f"batch failed after {max_attempts} attempts: {err}")
        log.warning("%s; retry %d in %.0fs", err, attempt, delay)
        time.sleep(delay)
        delay = min(delay * 2, 60)
    raise RuntimeError("unreachable")


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--candidates", default=str(CANDIDATES))
    p.add_argument("--out", default=None, help="votes CSV (default data/screening/llm_votes.csv; dry runs use llm_votes_dryrun.csv)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--limit", type=int, default=0, help="stop after N new records (0 = all)")
    p.add_argument("--dry-run", type=int, default=0, metavar="N", help="vote on N random records into a separate file and report cost")
    p.add_argument("--seed", type=int, default=20260917)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("screen_llm")

    key = api_key()
    if not key:
        print("ANTHROPIC_API_KEY is not set (environment or .env). Nothing was sent; add the key and re-run.", file=sys.stderr)
        return 2
    try:
        import anthropic
    except ImportError:
        print("The 'anthropic' package is missing: pip install anthropic", file=sys.stderr)
        return 2
    client = anthropic.Anthropic(api_key=key, max_retries=2, timeout=120.0)

    ex = protocol_excerpts()
    system = system_prompt(ex)
    log.info("prompt %s: system block %d chars (definition %d, steps %d, criteria %d)", PROMPT_VERSION, len(system), len(ex["definition"]), len(ex["steps"]), len(ex["criteria"]))

    with open(args.candidates, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = Path(args.out) if args.out else OUT_DIR / ("llm_votes_dryrun.csv" if args.dry_run else "llm_votes.csv")
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
    log.info("%d records to vote (%d candidates, %d already done)", len(todo), len(rows), len(done))

    new_file = args.dry_run or not out.exists() or out.stat().st_size == 0
    n = tokens_in = tokens_out = 0
    spent = 0.0
    t0 = time.time()
    with out.open("w" if args.dry_run else "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(COLUMNS)
        for i in range(0, len(todo), args.batch_size):
            batch = todo[i : i + args.batch_size]
            votes, usage = vote_batch(client, args.model, system, batch, log)
            c = cost_usd(args.model, usage)
            per_in = round((usage.input_tokens + (usage.cache_read_input_tokens or 0) + (usage.cache_creation_input_tokens or 0)) / len(batch))
            per_out = round(usage.output_tokens / len(batch))
            for r, v in zip(batch, votes, strict=True):
                w.writerow([r["id"], v["vote"], v["reason"][:200], v["decision_step"], args.model, PROMPT_VERSION, per_in, per_out, f"{c / len(batch):.6f}"])
            fh.flush()
            n += len(batch)
            tokens_in += per_in * len(batch)
            tokens_out += usage.output_tokens
            spent += c
            if (i // args.batch_size) % 10 == 0:
                log.info("%d/%d voted, $%.4f so far (cache read %s)", n, len(todo), spent, usage.cache_read_input_tokens)
    per_record = spent / n if n else 0.0
    summary = {
        "records_voted": n, "batches": (n + args.batch_size - 1) // args.batch_size, "model": args.model, "prompt_version": PROMPT_VERSION,
        "tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": round(spent, 4), "cost_per_record_usd": round(per_record, 6),
        "extrapolated_cost_all_candidates_usd": round(per_record * len(rows), 2), "candidates": len(rows), "seconds": round(time.time() - t0, 1), "out": str(out),
    }
    print("SUMMARY " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
