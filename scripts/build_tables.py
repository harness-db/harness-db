"""Build the release tables: data/papers.csv and data/systems.json (protocol 4.1, 4.2).

Screening produces per-record decisions and a system grouping; the release needs the two tables the
schema and `scripts/validate.py` expect, with the many-to-many link between them:

    data/papers.csv    one row per record assessed at full text, in either identification arm,
                       with its decision and (for exclusions) the reason. Records are the unit here.
    data/systems.json  one object per FULLY CODED system, schema-conformant, listing the papers.csv
                       ids that describe it and carrying its 38 coded cells.

Systems are the unit of analysis, records are not: a system links to every record that describes it
(4.2), which is why `papers` is a list.

The schema requires all 38 dimensions inside `coding`, so a system enters this file only once every
cell is resolved - either a valid value or an explicit `not_reported`. Systems coding has not reached,
and systems whose cells pass B has still to repair, stay out and are counted in the run report; the
census of every included system is data/systems_candidates.csv. Nothing is coerced on the way in:
unwrapping a one-element list or guessing an out-of-enum value would put a reading in the dataset
that no reader could trace to a quote. This script is therefore re-runnable, and is meant to be run
again after each coding pass. Stratum and weight live in data/coding_frame.csv, not here, because the
release schema fixes the set of system fields.

Usage:
    python scripts/build_tables.py [--quiet]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCREEN = REPO / "data" / "screening"
CODED = REPO / "data" / "coded" / "json"

# the release shape for one coded cell (schema/harness_db.schema.json, additionalProperties: false)
CELL_FIELDS = ("value", "evidence", "confidence", "not_reported", "coder", "note")
PAPER_COLUMNS = ["id", "title", "authors", "year", "venue", "arxiv_id", "doi", "url", "source",
                 "included", "exclusion_reason"]

csv.field_size_limit(10 ** 8)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def evidence_of(cell: dict[str, object]) -> str:
    """One evidence string from the quote and its locator, as the schema and examples expect."""
    quote = str(cell.get("evidence_quote") or "").strip()
    loc = str(cell.get("evidence_locator") or "").strip()
    if quote and loc:
        return f'"{quote}" ({loc})'
    return quote or loc


def load_dimensions() -> dict[str, dict[str, object]]:
    spec = json.loads((REPO / "schema" / "dimensions.json").read_text(encoding="utf-8"))
    return {d["key"]: d for d in spec["dimensions"]}


def cell_problem(dim: dict[str, object], cell: dict[str, object]) -> str | None:
    """Why this cell cannot go into the release, or None when it can.

    A cell qualifies when it is either an explicit `not_reported` (the coder read the sources and
    they are silent) or a value of the right shape for its dimension. Anything else - an unresolved
    cell, a list where the dimension is single-valued, a value outside the enum - is left to pass B
    to repair. Nothing is coerced here: guessing what the coder meant would put a reading into the
    dataset that no reader could trace back to a quote.
    """
    value, nr = cell.get("value"), bool(cell.get("not_reported"))
    if nr:
        return None if value is None else "not_reported with a value"
    if value is None:
        return "unresolved (no value, not marked not_reported)"
    multi, kind = bool(dim.get("multi")), str(dim.get("type") or "enum")
    allowed = dim.get("values") or []
    if multi:
        if not isinstance(value, list):
            return "scalar for a multi-valued dimension"
        bad = [v for v in value if allowed and v not in allowed]
        return f"value(s) outside the enum: {bad}" if bad else None
    if isinstance(value, list):
        return "list for a single-valued dimension"
    if kind == "integer" and not isinstance(value, int):
        return "non-integer value"
    if kind == "boolean" and not isinstance(value, bool):
        return "non-boolean value"
    if kind == "enum" and allowed and value not in allowed:
        return f"value outside the enum: {value!r}"
    return None


def release_cell(cell: dict[str, object], coder: str) -> dict[str, object]:
    out: dict[str, object] = {
        "value": cell.get("value"),
        "not_reported": bool(cell.get("not_reported")),
        "confidence": cell.get("confidence") or "low",
        "coder": coder,
    }
    if (ev := evidence_of(cell)):
        out["evidence"] = ev
    if (note := str(cell.get("note") or "").strip()):
        out["note"] = note
    return {k: out[k] for k in CELL_FIELDS if k in out}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--papers-out", type=Path, default=REPO / "data" / "papers.csv")
    p.add_argument("--systems-out", type=Path, default=REPO / "data" / "systems.json")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    meta: dict[str, dict[str, str]] = {}
    for name in ("candidates.csv", "candidates_supplementary.csv"):
        for r in read_csv(REPO / "data" / "raw" / name):
            meta.setdefault(r["id"], r)

    decisions: dict[str, dict[str, str]] = {}
    for path in (SCREEN / "fulltext_final_pass1.csv", SCREEN / "fulltext_votes_supplementary.csv"):
        for r in read_csv(path):
            decisions.setdefault(r["record_id"], r)

    # 1. papers.csv - every record assessed at full text, in either arm
    papers: list[dict[str, str]] = []
    for rid, d in sorted(decisions.items()):
        m = meta.get(rid, {})
        reason = ""
        if d["decision"] == "exclude":
            reason = d.get("exclusion_code") or "excluded"
            if (sub := (d.get("exclusion_subreason") or "").strip()):
                reason = f"{reason}:{sub}"
        papers.append({
            "id": rid,
            "title": (m.get("title") or d.get("candidate_title") or d.get("document_title_seen") or "").strip(),
            "authors": "",  # not carried by the frozen candidate table; recoverable from data/raw/*.jsonl
            "year": (m.get("year") or "").strip(),
            "venue": (m.get("venue") or "").strip(),
            "arxiv_id": (m.get("arxiv_id") or "").strip(),
            "doi": (m.get("doi") or "").strip(),
            "url": (m.get("url") or d.get("fetched_url") or "").strip(),
            "source": (m.get("source") or d.get("candidate_source") or "").strip(),
            "included": "1" if d["decision"] == "include" else "0",
            "exclusion_reason": reason,
        })
    with args.papers_out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PAPER_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(papers)
    paper_ids = {r["id"] for r in papers}

    # 2. systems.json - one object per included system, with its records and any coded cells
    coded_by_id: dict[str, dict[str, object]] = {}
    if CODED.exists():
        for f in CODED.glob("*.json"):
            try:
                coded_by_id[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue  # a file being written right now is picked up on the next run

    systems: list[dict[str, object]] = []
    dims = load_dimensions()
    linked = unlinked = skipped_uncoded = skipped_unrepaired = 0
    problem_counts: collections.Counter[str] = collections.Counter()
    for s in read_csv(REPO / "data" / "systems_candidates.csv"):
        sid = s["system_id"]
        members = [m for m in (s.get("member_record_ids") or "").split(";") if m in paper_ids]
        if members:
            linked += 1
        else:
            unlinked += 1
        aliases = [a for a in (s.get("name_variants") or "").split(";") if a and a != s.get("name")]
        urls = {k: v for k, v in (("repo", (s.get("repo_url") or "").strip()),) if v}

        entry: dict[str, object] = {"id": sid, "name": s.get("name") or sid, "papers": members}
        if (ver := (s.get("version") or "").strip()):
            entry["version_label"] = ver
        if aliases:
            entry["aliases"] = aliases
        if urls:
            entry["urls"] = urls

        # The schema requires every one of the 38 dimensions inside `coding`, so a system that
        # coding has not reached yet cannot appear here: filling it with not_reported placeholders
        # would assert "the sources do not say" about cells nobody has read. Uncoded systems stay in
        # data/systems_candidates.csv, which is the census table; this file is the coded dataset.
        cd = coded_by_id.get(sid)
        if not (cd and isinstance(cd.get("coding"), dict) and cd["coding"]):
            skipped_uncoded += 1
            continue
        coding = {k: v for k, v in cd["coding"].items() if isinstance(v, dict)}
        problems = {k: why for k, v in coding.items()
                    if (dim := dims.get(k)) and (why := cell_problem(dim, v))}
        if problems or len(coding) < len(dims):
            skipped_unrepaired += 1
            for why in problems.values():
                problem_counts[why] += 1
            continue
        coder = f"llm-{cd.get('model', 'opus')}-{cd.get('prompt_version', '')}".rstrip("-")
        entry["coding"] = {k: release_cell(v, coder) for k, v in coding.items()}
        if (at := str(cd.get("coded_at") or "")):
            entry["coded_at"] = at[:10]  # schema wants a plain date

        notes = [f"grouped_by={s.get('grouped_by') or 'single'}",
                 f"codability={s.get('codability_flag') or 'unknown'}",
                 f"max_codable_count={s.get('max_codable_count') or '0'}"]
        if (rd := (s.get("release_date") or "").strip()):
            notes.append(f"release_date={rd}")
        if (fr := (s.get("frame_reason") or "").strip()):
            notes.append(f"frame={fr}")
        entry["notes"] = "; ".join(notes)
        systems.append(entry)

    args.systems_out.write_text(json.dumps(systems, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.quiet:
        inc = sum(1 for r in papers if r["included"] == "1")
        coded = sum(1 for s in systems if s["coding"])
        print(f"papers.csv : {len(papers)} records assessed ({inc} included, {len(papers) - inc} excluded)")
        print(f"systems.json: {len(systems)} systems released, every one of the {len(dims)} "
              f"dimensions resolved ({coded} carry coded cells)")
        print(f"  not yet coded        : {skipped_uncoded}")
        print(f"  coded, awaiting pass B: {skipped_unrepaired}")
        for why, n in problem_counts.most_common(6):
            print(f"      {n:5} cells  {why}")
        print(f"record links : {linked} systems link to at least one assessed record, {unlinked} to none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
