"""Drive Phase 4 coding to completion across usage-limit windows, unattended.

`scripts/code_system.py` is resumable but single-shot: when the plan's allowance runs out every
remaining system fails with HTTP 429 and the run ends (that is how pass A stopped on 2026-09-20 with
358 of 1,116 systems coded). This driver re-invokes it until every system in the coding frame has
been read, waiting out each limit window, then runs the repair pass, the double-coded reliability
sample, and the release build. Stages are idempotent, so it can be killed and restarted at any point.

Run it under Task Scheduler, never from a session console: a console-attached job dies with the
session, and a subagent teardown once sent Ctrl-C to the whole process group.

    schtasks --% /Create /TN HarnessDB-Phase4-Coding /TR "cmd /c <repo>\\scripts\\run_coding.cmd" ...

Progress: data/coded/phase4_status.json and data/coded/autopilot.log.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CODED = REPO / "data" / "coded"
FRAME = REPO / "data" / "coding_frame.csv"
CELLS = CODED / "cells.csv"
CELLS2 = CODED / "cells_pass2.csv"
STATUS = CODED / "phase4_status.json"
PY = sys.executable

log = logging.getLogger("phase4")
csv.field_size_limit(10 ** 8)


def setup_logging() -> None:
    CODED.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(CODED / "autopilot.log", encoding="utf-8")):
        h.setFormatter(fmt)
        root.addHandler(h)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def frame_ids() -> list[str]:
    return [r["system_id"] for r in read_csv(FRAME) if r.get("coded") == "1"]


def coded_ids(path: Path, pass_name: str | None = None) -> set[str]:
    return {r["system_id"] for r in read_csv(path)
            if pass_name is None or (r.get("pass") or "").upper() == pass_name}


def status(stage: str, **fields: object) -> None:
    doc = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {"stages": {}}
    doc["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    doc["stage"] = stage
    doc["stages"].setdefault(stage, {}).update(fields)
    STATUS.write_text(json.dumps(doc, indent=2), encoding="utf-8")


def run(cmd: list[str], log_path: Path) -> int:
    log.info("run: %s", " ".join(cmd[:10]))
    with log_path.open("a", encoding="utf-8") as fh:
        return subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=REPO, check=False).returncode


def code_cmd(args: argparse.Namespace, pass_name: str, extra: list[str] | None = None) -> list[str]:
    return [PY, "scripts/code_system.py", "--pass", pass_name, "--model", args.model,
            "--effort", args.effort, "--workers", str(args.workers), "--text-json", *(extra or [])]


def drive(label: str, target: list[str], done_fn, cmd: list[str], args: argparse.Namespace,
          deadline: float) -> bool:
    """Re-invoke ``cmd`` until every id in ``target`` is done, waiting out usage-limit windows."""
    stalls = 0
    while True:
        left = sorted(set(target) - done_fn())
        status(label, target=len(target), done=len(target) - len(left), model=args.model)
        if not left:
            log.info("%s: complete (%d systems)", label, len(target))
            return True
        if time.time() > deadline:
            log.error("%s: deadline reached with %d systems left", label, len(left))
            return False
        before = len(left)
        run(cmd, CODED / f"autopilot_{label}.log")
        after = len(set(target) - done_fn())
        if after == 0:
            continue
        if after < before:
            stalls = 0
            log.info("%s: %d systems left after this run", label, after)
            continue
        stalls += 1
        wait = args.limit_wait * 60
        log.warning("%s: no progress (%d left, stall %d); waiting %d min for the allowance to reset",
                    label, after, stalls, args.limit_wait)
        status(label, waiting_until=datetime.fromtimestamp(time.time() + wait, UTC).isoformat(timespec="seconds"))
        time.sleep(wait)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--model", default="opus")
    p.add_argument("--effort", default="low")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--limit-wait", type=int, default=30, help="minutes to wait when a run makes no progress")
    p.add_argument("--deadline-hours", type=float, default=72.0)
    p.add_argument("--double-sample", type=float, default=0.2)
    p.add_argument("--seed", default="code-2026-09-20")
    p.add_argument("--skip-double", action="store_true")
    args = p.parse_args(argv)
    setup_logging()

    deadline = time.time() + args.deadline_hours * 3600
    target = frame_ids()
    log.info("phase 4 autopilot start: %d systems in the coding frame, model=%s effort=%s workers=%d",
             len(target), args.model, args.effort, args.workers)

    # 1. pass A: every system read once
    if not drive("passA", target, lambda: coded_ids(CELLS, "A"), code_cmd(args, "A"), args, deadline):
        return 1

    # 2. pass B: repairs the cells pass A left unresolved, invalid or non-verbatim. It only touches
    #    systems that have such cells, so "done" is any system carrying a pass-B row plus those that
    #    never needed one; re-running it is cheap and idempotent once there is nothing left to repair.
    run(code_cmd(args, "B"), CODED / "autopilot_passB.log")
    status("passB", systems_with_repairs=len(coded_ids(CELLS, "B")))

    # 3. double coding for per-dimension kappa
    if not args.skip_double:
        run(code_cmd(args, "A", ["--double", "--double-sample", str(args.double_sample), "--seed", args.seed]),
            CODED / "autopilot_double.log")
        status("double", systems_double_coded=len(coded_ids(CELLS2)))

    # 4. release tables + validation + agreement
    run([PY, "scripts/build_tables.py"], CODED / "autopilot_build.log")
    run([PY, "scripts/validate.py"], CODED / "autopilot_validate.log")
    if CELLS2.exists():
        run([PY, "scripts/kappa.py", "coding", "data/coded/json", "data/coded/json_pass2"],
            CODED / "autopilot_kappa.log")

    # 5. commit whatever landed
    run(["git", "add", "data/coded/cells.csv", "data/coded/cells_pass2.csv", "data/coded/json",
         "data/coded/json_pass2", "data/systems.json", "data/papers.csv", "data/coded/phase4_status.json"],
        CODED / "autopilot_git.log")
    run(["git", "commit", "-m",
         "Phase 4 coding (autopilot): 38 dimensions per system with evidence per cell\n\n"
         "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"],
        CODED / "autopilot_git.log")
    run(["git", "push", "origin", "main"], CODED / "autopilot_git.log")
    status("done", finished_at=datetime.now(UTC).isoformat(timespec="seconds"))
    log.info("phase 4 autopilot finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
