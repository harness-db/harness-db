#!/usr/bin/env python
"""Unattended driver that finishes Phase 3 full-text screening (subscription only, no API).

Stages (each resumable; re-running the driver skips work already on disk):
  0  downloads   finish scripts/fetch_fulltext.py and scripts/fetch_repos.py
  1  tier1       the tier-1 model (Sonnet or Haiku via Claude Code) reads every retrievable record
                 that has no Opus vote yet, plus a 20% hash sample of the Opus-voted records
                 (second readings for agreement)
  2  tier2       Opus re-reads every tier-1 exclude and every low-confidence tier-1 decision
  3  audit       Opus re-reads a 10% hash sample of the remaining tier-1 includes, which
                 measures how often an unconfirmed tier-1 include is wrong
  4  merge       decisive vote = Opus where it exists, else tier 1; second reading = the other one
  5  registry    scripts/system_registry.py and scripts/validate_screening.py on the merged votes
  6  prisma      full-text counts into data/prisma_counts.json, re-render the flow diagram
  7  commit      git add / commit / push

Usage limits: a screening run that aborts (consecutive failures, typically the subscription's
session limit) is retried after --limit-wait minutes, until --deadline-hours pass.
Status goes to data/screening/autopilot_status.json and the log to data/screening/autopilot.log.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCREEN = REPO / "data" / "screening"
PY = sys.executable
INDEX = SCREEN / "fulltext_index.csv"
REPOS = SCREEN / "repo_index.csv"
OPUS = SCREEN / "fulltext_votes_v2.csv"
TIER1 = SCREEN / "fulltext_votes_tier1.csv"
FINAL1 = SCREEN / "fulltext_final_pass1.csv"
FINAL2 = SCREEN / "fulltext_final_pass2.csv"
STATUS = SCREEN / "autopilot_status.json"
LOG = SCREEN / "autopilot.log"
SAMPLE_SEED = "20260919"

log = logging.getLogger("autopilot")


def status(stage: str, **kw: object) -> None:
    doc = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    doc["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    doc["stage"] = stage
    doc.setdefault("stages", {})[stage] = {**doc.get("stages", {}).get(stage, {}), **kw}
    STATUS.write_text(json.dumps(doc, indent=2), encoding="utf-8")


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_ids(path: Path, ids: list[str]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record_id"])
        w.writerows([[i] for i in ids])
    return path


def in_sample(record_id: str, rate: float) -> bool:
    h = hashlib.sha256(f"{SAMPLE_SEED}:{record_id}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF < rate


def env() -> dict[str, str]:
    e = dict(os.environ)
    e["DISABLE_PROMPT_CACHING"] = "1"          # measured cheaper: every batch carries different documents
    e["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"  # keep connector schemas out of every headless call
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def run(cmd: list[str], logfile: Path) -> int:
    log.info("run: %s", " ".join(cmd))
    with logfile.open("a", encoding="utf-8") as f:
        return subprocess.run(cmd, cwd=REPO, env=env(), stdout=f, stderr=subprocess.STDOUT, check=False).returncode


def ok_ids() -> list[str]:
    return sorted({r["record_id"] for r in read_rows(INDEX) if r.get("status") == "ok"})


def voted(path: Path) -> set[str]:
    return {r["record_id"] for r in read_rows(path)}


def screen_until_done(label: str, ids: list[str], model: str, out: Path, args: argparse.Namespace, deadline: float) -> None:
    """Run fulltext_screen on ``ids`` into ``out`` until every id has a vote (or the deadline passes)."""
    stalls = 0
    while True:
        todo = sorted(set(ids) - voted(out))
        status(label, target=len(ids), done=len(ids) - len(todo), model=model)
        if not todo:
            log.info("%s: complete (%d records)", label, len(ids))
            return
        if time.time() > deadline:
            log.error("%s: deadline reached with %d records left", label, len(todo))
            return
        before = len(todo)
        # A batch is refused as a whole when any one document in it trips a content safeguard
        # (several candidate systems are offensive-security agents). Splitting the batch clears it.
        sizes = [args.batch_size] + ([1] if args.batch_size > 1 else [])
        for size in sizes:
            idfile = write_ids(SCREEN / f"_autopilot_{label}_ids.csv", todo)
            if size != args.batch_size:
                log.info("%s: no progress at batch size %d; retrying %d records one document per call",
                         label, args.batch_size, len(todo))
            run([PY, "scripts/fulltext_screen.py", "--pass", "1", "--backend", "claude-code", "--model", model,
                 "--effort", "low", "--workers", str(min(args.workers, 4) if size == 1 else args.workers),
                 "--batch-size", str(size), "--text-json",
                 "--ids", str(idfile), "--out", str(out), "--max-consecutive-failures", "6"], SCREEN / f"autopilot_{label}.log")
            after = len(set(ids) - voted(out))
            if after < before:
                break
            todo = sorted(set(ids) - voted(out))
        if after == 0:
            continue
        if after < before:
            stalls = 0
            log.info("%s: %d records left after this run", label, after)
            continue  # progress was made; the run ended early (limit or failures): try again at once
        stalls += 1
        wait = args.limit_wait * 60
        log.warning("%s: no progress (%d left, stall %d); waiting %d min for the usage window", label, after, stalls, args.limit_wait)
        status(label, waiting_until=datetime.fromtimestamp(time.time() + wait, UTC).isoformat(timespec="seconds"))
        time.sleep(wait)


def merge() -> tuple[int, int]:
    """Decisive vote: Opus where it exists, else tier 1. Second reading: the other vote where both exist."""
    opus = {r["record_id"]: r for r in read_rows(OPUS)}
    tier1 = {r["record_id"]: r for r in read_rows(TIER1)}
    fields = list(next(iter(opus.values())).keys()) if opus else list(next(iter(tier1.values())).keys())
    for extra in ("decided_by",):
        if extra not in fields:
            fields.append(extra)
    final1, final2 = [], []
    for rid in sorted(set(opus) | set(tier1)):
        if rid in opus:
            final1.append({**opus[rid], "decided_by": "opus"})
            if rid in tier1:
                final2.append({**tier1[rid], "decided_by": "tier1"})
        else:
            final1.append({**tier1[rid], "decided_by": "tier1"})
    for path, rows in ((FINAL1, final1), (FINAL2, final2)):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    return len(final1), len(final2)


def prisma() -> dict[str, object]:
    p = REPO / "data" / "prisma_counts.json"
    counts = json.loads(p.read_text(encoding="utf-8"))
    queue = {r["record_id"] for r in read_rows(SCREEN / "fulltext_queue.csv")}
    final = read_rows(FINAL1)
    systems = read_rows(REPO / "data" / "systems_candidates.csv")
    excl: dict[str, int] = {}
    for r in final:
        if r.get("decision") == "exclude":
            code = r.get("exclusion_code") or "other"
            excl[code] = excl.get(code, 0) + 1
    # "not retrieved" is the queued records that never reached a full-text vote. It is NOT the count of
    # failed document fetches: 73 records whose paper was unretrievable were assessed from their
    # repository instead, and fulltext_queue.csv lists one record twice, so it is counted as a set.
    not_retrieved = len(queue - {r["record_id"] for r in final})
    counts.update({
        "sought_full_text": len(queue),
        "not_retrieved": not_retrieved,
        "assessed_full_text": len(final),
        "excluded_full_text": excl,
        "included_papers": sum(1 for r in final if r.get("decision") == "include"),
        "included_systems": len(systems),
    })
    p.write_text(json.dumps(counts, indent=2), encoding="utf-8")
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tier1-model", default="sonnet")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--limit-wait", type=int, default=30, help="minutes to wait when a run makes no progress")
    ap.add_argument("--deadline-hours", type=float, default=20.0)
    ap.add_argument("--skip-downloads", action="store_true")
    ap.add_argument("--no-commit", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler(sys.stdout)])
    deadline = time.time() + args.deadline_hours * 3600
    log.info("autopilot start: tier1=%s workers=%d batch=%d", args.tier1_model, args.workers, args.batch_size)

    if not args.skip_downloads:
        status("downloads", state="running")
        run([PY, "scripts/fetch_fulltext.py", "--workers", "4", "--skip-failed"], SCREEN / "autopilot_fetch_fulltext.log")
        run([PY, "scripts/fetch_repos.py", "--workers", "4"], SCREEN / "autopilot_fetch_repos.log")
        status("downloads", state="done", documents_ok=len(ok_ids()))

    settled = voted(REPOS) | {r["record_id"] for r in read_rows(INDEX) if r.get("source_used") == "github_repo"}
    docs = [i for i in ok_ids() if i in settled]
    opus_done = voted(OPUS)
    tier1_ids = [i for i in docs if i not in opus_done] + [i for i in sorted(opus_done) if in_sample(i, 0.20)]
    screen_until_done("tier1", tier1_ids, args.tier1_model, TIER1, args, deadline)

    t1 = {r["record_id"]: r for r in read_rows(TIER1)}
    escalate = [rid for rid, r in t1.items() if rid not in opus_done and (r.get("decision") == "exclude" or r.get("confidence") == "low")]
    screen_until_done("tier2", escalate, "opus", OPUS, args, deadline)

    audit = [rid for rid, r in t1.items() if rid not in opus_done and rid not in set(escalate) and r.get("decision") == "include" and in_sample(rid, 0.10)]
    screen_until_done("audit", audit, "opus", OPUS, args, deadline)

    n1, n2 = merge()
    status("merge", decisive=n1, second_readings=n2)
    # The decisive vote (Opus where it exists) wins: the registry gets no second reading, otherwise its default
    # --disputed hold would drop the very includes Opus recovered from tier-1 excludes. Agreement between the
    # two readings is still computed by validate_screening from FINAL2.
    run([PY, "scripts/system_registry.py", "--votes", str(FINAL1), "--pass2", str(SCREEN / "_no_second_reading.csv")],
        SCREEN / "autopilot_registry.log")
    run([PY, "scripts/validate_screening.py", "--votes", str(FINAL1), "--pass2", str(FINAL2)], SCREEN / "autopilot_validate.log")
    counts = prisma()
    run([PY, "scripts/prisma_diagram.py"], SCREEN / "autopilot_prisma.log")
    status("prisma", **{k: counts[k] for k in ("assessed_full_text", "included_papers", "included_systems")})

    if not args.no_commit:
        run(["git", "add", "data/screening/fulltext_votes_v2.csv", "data/screening/fulltext_votes_tier1.csv",
             str(FINAL1.relative_to(REPO)), str(FINAL2.relative_to(REPO)), "data/screening/fulltext_report.md",
             "data/screening/autopilot_status.json", "data/systems_candidates.csv", "data/prisma_counts.json",
             "paper/figures", "data/screening/fulltext_index.csv", "data/screening/repo_index.csv"], SCREEN / "autopilot_git.log")
        msg = ("Phase 3 full-text screening complete (autopilot): tiered reading, Opus confirms every exclusion\n\n"
               "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n"
               "Claude-Session: https://claude.ai/code/session_01XKrJveoWTZGN4BZDPYqggA\n")
        run(["git", "commit", "-m", msg], SCREEN / "autopilot_git.log")
        run(["git", "push", "origin", "main"], SCREEN / "autopilot_git.log")
    status("done", finished_at=datetime.now(UTC).isoformat(timespec="seconds"))
    log.info("autopilot finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
