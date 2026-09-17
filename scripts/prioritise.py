#!/usr/bin/env python
"""ASReview prior knowledge and the stopping-rule log (Phase 3 item A4).

Writes

* ``data/screening/prior_knowledge.csv`` - ``record_id, label, arxiv_id, title, rule, reason``:
  the known items (label 1; those of the 48 ids in ``data/raw/known_items.txt`` that are in
  ``candidates.csv``) and 20 clear negatives (label 0) chosen by two deterministic rules:
  - ``date``: records whose year is before 2022 (criterion (c): first public release outside
    2022-10-01..2026-08-31 -> ``out_of_scope (date)``); these reach the candidate set only
    through survey bibliographies and awesome-lists (JUnit, Gym, Firecracker, ...);
  - ``model_paper``: in-window records whose title and abstract contain no agent vocabulary at
    all (none of agent, harness, scaffold, tool, action, environment, execut-, loop, sandbox,
    planning) and describe a language model or its training (criterion (a): no loop, no
    executed actions -> ``out_of_scope (no_loop)``), surveys/reviews excluded (they are ``unsure``
    at title/abstract), newest year first then title; the ``date`` rule skips titles that mention
    a harness (lm-evaluation-harness) so the priors do not teach against the key term.
  The list is short enough to read; check it once before entering it in ASReview.
* ``data/screening/stopping_rule_log.md`` - the registered stopping rule and the per-session
  table to fill in.

Usage:
    python scripts/prioritise.py [--negatives 20] [--out-dir data/screening]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "harvest"))
from common import normalize_arxiv_id

AGENT_VOCAB = re.compile(r"\b(agent|agentic|harness|scaffold|tool|action|environment|execut\w*|loop|sandbox|planning|orchestrat\w*|autonomous)\b", re.IGNORECASE)
MODEL_VOCAB = re.compile(r"\b(language model|LLM|transformer|pre-?train|fine-?tun|instruction tuning|reinforcement learning from human feedback|RLHF|scaling law|in-context learning|chain-of-thought|attention)\b", re.IGNORECASE)

STOPPING_LOG = """# ASReview stopping rule and session log (screener 1)

**Registered rule (protocol section 7 / execution plan Phase 3):** screener 1 screens in the order
proposed by ASReview and stops when **100 consecutive records have been labelled irrelevant after
every known item has been found** (the {n_pos} known-item priors listed in `prior_knowledge.csv`;
{n_missing} of the 48 registered ids are not in the candidate set: {missing}). Screener 2 screens
the full set in random order. The rule is stated before screening starts and may only be changed
by a protocol amendment.

Prior knowledge entered in ASReview: {n_pos} relevant (known items) + {n_neg} irrelevant
(`prior_knowledge.csv`, rules `date` and `model_paper`).

ASReview version: ____ · feature extractor: ____ (default TF-IDF) · classifier: ____ (default
Naive Bayes) · query strategy: ____ (default max) · balance: ____ (default dynamic resampling).

| session date | screener | records screened this session | cumulative screened | longest run of consecutive irrelevant | known items found so far (of {n_pos}) | stop condition met? | note |
|---|---|---:|---:|---:|---:|---|---|
| | | | | | | | |

Stop when the last column reads "yes" **and** all {n_pos} known items have been found. Record the
final cumulative count here and in `data/prisma_counts.json` (`screened_title_abstract` is the
union of both screeners' records, not this number).
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--candidates", default=str(REPO / "data/raw/candidates.csv"))
    p.add_argument("--known", default=str(REPO / "data/raw/known_items.txt"))
    p.add_argument("--out-dir", default=str(REPO / "data/screening"))
    p.add_argument("--negatives", type=int, default=20)
    args = p.parse_args(argv)

    known: dict[str, str] = {}
    for line in Path(args.known).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            parts = line.split("\t")
            aid = normalize_arxiv_id(parts[0])
            if aid:
                known[aid] = parts[1] if len(parts) > 1 else ""
    with open(args.candidates, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    positives = []
    found: set[str] = set()
    for r in rows:
        aid = normalize_arxiv_id(r.get("arxiv_id") or "")
        if aid in known and aid not in found:
            found.add(aid)
            positives.append({"record_id": r["id"], "label": 1, "arxiv_id": aid, "title": r["title"], "rule": "known_item", "reason": f"registered known item ({known[aid]})"})
    missing = sorted(set(known) - found)

    negatives = []
    # date rule; records whose title mentions a harness are left out so the priors do not teach against the key term
    dated = sorted(
        (r for r in rows if re.fullmatch(r"\d{4}", r.get("year") or "") and int(r["year"]) < 2022 and "harness" not in (r["title"] + " " + r["abstract"]).lower()),
        key=lambda r: (r["year"], r["title"]),
    )
    for r in dated:
        negatives.append({"record_id": r["id"], "label": 0, "arxiv_id": r.get("arxiv_id") or "", "title": r["title"], "rule": "date", "reason": f"published {r['year']}: first release outside 2022-10-01..2026-08-31 -> out_of_scope (date)"})
    model_papers = [
        r for r in rows
        if re.fullmatch(r"\d{4}", r.get("year") or "") and 2022 <= int(r["year"]) <= 2026
        and r.get("abstract", "").strip() and not AGENT_VOCAB.search(r["title"] + " " + r["abstract"])
        and "agent" not in r["title"].lower()  # system names such as 3DrawAgent have no word boundary
        and MODEL_VOCAB.search(r["title"] + " " + r["abstract"])
        and r["source"] in ("s2_snowball", "awesome", "survey_refs")
        and not re.search(r"\b(survey|review|overview|perspective)\b", r["title"], re.IGNORECASE)  # surveys are 'unsure' at title/abstract, not clear negatives
    ]
    model_papers.sort(key=lambda r: (-int(r["year"]), r["title"].lower()))  # newest first, then title
    for r in model_papers:
        if len(negatives) >= args.negatives:
            break
        negatives.append({"record_id": r["id"], "label": 0, "arxiv_id": r.get("arxiv_id") or "", "title": r["title"], "rule": "model_paper", "reason": "no agent/tool/environment vocabulary in title+abstract; describes a model or its training -> out_of_scope (no_loop)"})
    negatives = negatives[: args.negatives]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "prior_knowledge.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["record_id", "label", "arxiv_id", "title", "rule", "reason"])
        w.writeheader()
        for r in positives + negatives:
            w.writerow(r)
    (out / "stopping_rule_log.md").write_text(
        STOPPING_LOG.format(n_pos=len(positives), n_missing=len(missing), missing=", ".join(missing) or "none", n_neg=len(negatives)), encoding="utf-8"
    )
    print("SUMMARY " + json.dumps({"positives": len(positives), "known_missing_from_candidates": missing, "negatives": len(negatives), "negatives_by_rule": {k: sum(1 for n in negatives if n["rule"] == k) for k in ("date", "model_paper")}, "model_paper_pool": len(model_papers), "out": str(out)}))
    for n in negatives:
        print(f"  NEG [{n['rule']}] {n['record_id']} | {n['title'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
