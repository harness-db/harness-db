#!/usr/bin/env python
"""Validate the automated full-text screening and write its report and audit data.

Measures (protocol Amendments 4 and 5):
* Recall of the POSITIVE reference set (``data/screening/validation_systems.csv``: must-cite
  systems plus systems catalogued by Rombaut, Barbaste and Meng) at each stage: search candidates,
  forwarded by the title stage (``fulltext_queue.csv``), full-text include (pass 1), the system
  registry (``data/systems_candidates.csv``) and the Amendment 5 coding frame (``in_frame`` on
  that file: >= 100 stars, catalogued or on a leaderboard, vendor product, or peer-reviewed with a
  public implementation). A reference system is matched by arXiv id,
  repository URL, or name/alias (rapidfuzz ratio >= 90 on alphanumerics; names of four characters
  or fewer exactly) against candidate titles, ``system_name`` and ``systems_mentioned``. Every
  missing system is listed with the stage where it was lost.
* Specificity on the NEGATIVE reference set (surveys, benchmarks, evaluation studies).
* Pass-1 vs pass-2 agreement: Cohen's kappa (``scripts/kappa.py``) and the include/exclude
  confusion table, raw and re-weighted to the population (pass 2 coverage is uneven: the executed
  run escalated every tier-1 exclude and every low-confidence decision, so it over-samples excludes
  and disputed includes; the re-weighting corrects for that, and note that pass 2 does NOT read every
  pass-1 include, but
  only 10% of excludes).
* Wilson 95% intervals; exclusion codes and sub-reasons; deciding-step distribution;
  codable_count distribution; include rate by source and by pilot stratum; post-hoc flags
  (quotes not found verbatim, include below the codability rule, ...); time and list-equivalent
  cost per record and projections to the whole queue.

Writes ``data/screening/fulltext_report.md`` and ``data/screening/fulltext_audit.js`` (the data of
``screening/fulltext_audit.html``).

Usage:
    python scripts/validate_screening.py                       # whole queue
    python scripts/validate_screening.py --pilot               # restrict to data/screening/fulltext_pilot.csv
    python scripts/validate_screening.py --pilot --votes data/screening/fulltext_votes.csv   # the v1 pilot
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kappa import cohen_kappa
from rapidfuzz import fuzz
from system_registry import key_of, keys_match, names_match, repo_key

REPO = Path(__file__).resolve().parents[1]
SCREEN_DIR = REPO / "data" / "screening"
REFS = SCREEN_DIR / "validation_systems.csv"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"
QUEUE = SCREEN_DIR / "fulltext_queue.csv"
PILOT = SCREEN_DIR / "fulltext_pilot.csv"
INDEX = SCREEN_DIR / "fulltext_index.csv"
PASS1 = SCREEN_DIR / "fulltext_votes_v2.csv"
PASS2 = SCREEN_DIR / "fulltext_votes_v2_pass2.csv"
FINAL = SCREEN_DIR / "fulltext_votes_final.csv"
SYSTEMS = REPO / "data" / "systems_candidates.csv"
REPORT = SCREEN_DIR / "fulltext_report.md"
AUDIT_JS = SCREEN_DIR / "fulltext_audit.js"

NAME_THRESHOLD = 90
TITLE_THRESHOLD = 90
PASS2_EXCLUDE_FRACTION = 0.10  # must match scripts/fulltext_screen.py
EXPECTED_SYSTEMS = (150, 300)  # protocol expectation (plan)
STAGES = ["search", "title_forward", "fulltext_include", "registry", "coding_frame"]


# --------------------------------------------------------------------------------------
# Small statistics
# --------------------------------------------------------------------------------------


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def ci(k: int, n: int) -> str:
    if n == 0:
        return "n/a (n = 0)"
    p, lo, hi = wilson(k, n)
    return f"{k}/{n} = {p:.1%} [95% CI {lo:.1%}, {hi:.1%}]"


def weighted_kappa(pairs: list[tuple[str, str]], weights: list[float]) -> tuple[float, float]:
    """Cohen's kappa and observed agreement with per-pair weights (population re-weighting)."""
    tot = sum(weights)
    if not tot:
        return float("nan"), float("nan")
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(w for (a, b), w in zip(pairs, weights, strict=True) if a == b) / tot
    pa = {c: sum(w for (a, _), w in zip(pairs, weights, strict=True) if a == c) / tot for c in cats}
    pb = {c: sum(w for (_, b), w in zip(pairs, weights, strict=True) if b == c) / tot for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats)
    return (1.0 if pe == 1 else (po - pe) / (1 - pe)), po


# --------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    csv.field_size_limit(10**8)
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def jl(s: str) -> list[Any]:
    try:
        v = json.loads(s or "[]")
        return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})")


def arxiv_of(record_id: str, cand: dict[str, str] | None = None) -> str:
    for s in ((cand or {}).get("arxiv_id") or "", record_id if record_id.startswith("arxiv:") else "", (cand or {}).get("url") or ""):
        m = ARXIV_RE.search(str(s))
        if m and ("arxiv" in str(s).lower() or s == (cand or {}).get("arxiv_id") or record_id.startswith("arxiv:")):
            return m.group(1)
    return ""


def url_key(url: str) -> str:
    u = re.sub(r"^https?://(www\.)?", "", (url or "").strip().lower()).rstrip("/")
    return u


@dataclass
class Ref:
    ref_id: str
    set: str
    expected: str
    name: str
    aliases: list[str]
    arxiv: str
    urls: list[str]
    source: str
    note: str
    repos: set[str] = field(default_factory=set)
    url_keys: set[str] = field(default_factory=set)
    name_keys: list[str] = field(default_factory=list)

    @property
    def names(self) -> list[str]:
        return [self.name] + self.aliases


def load_refs(path: Path = REFS) -> list[Ref]:
    out = []
    for r in read_csv(path):
        urls = [u.strip() for u in (r.get("repo_url") or "").split(";") if u.strip()]
        ref = Ref(r["ref_id"], r["set"], r["expected"], r["name"], [a.strip() for a in (r.get("aliases") or "").split(";") if a.strip()],
                  (r.get("arxiv_id") or "").strip(), urls, r.get("source_of_truth") or "", r.get("note") or "")
        ref.repos = {k for u in urls if (k := repo_key(u))}
        ref.url_keys = {k for u in urls if (k := url_key(u))}
        ref.name_keys = [k for n in ref.names if (k := key_of(n))]
        out.append(ref)
    return out


# --------------------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------------------


def title_head(title: str) -> str:
    t = re.sub(r"\s+", " ", title or "").strip()
    if re.fullmatch(r"[\w.-]+/[\w.-]+", t):  # "owner/repo"
        return t.split("/", 1)[1]
    return re.split(r":|\s[-–—]\s", t, maxsplit=1)[0].strip()


def name_hit(ref: Ref, name: str, threshold: int = NAME_THRESHOLD) -> bool:
    k = key_of(name)
    return bool(k) and any(keys_match(nk, k, threshold) for nk in ref.name_keys)


def title_hit(ref: Ref, title: str) -> bool:
    kt = key_of(title)
    return bool(kt) and any(len(nk) > 12 and fuzz.ratio(nk, kt) >= TITLE_THRESHOLD for nk in ref.name_keys)


@dataclass
class CandFeat:
    rid: str
    arxiv: str
    repo: str
    url: str
    head_key: str
    title_key: str


def cand_features(rid: str, cand: dict[str, str]) -> CandFeat:
    url = cand.get("url") or ""
    title = cand.get("title") or ""
    return CandFeat(rid, arxiv_of(rid, cand), repo_key(url), url_key(url), key_of(title_head(title)), key_of(title))


def match_candidate(ref: Ref, f: CandFeat) -> str:
    """Match basis of one search candidate against a reference ('' if none)."""
    if ref.arxiv and f.arxiv == ref.arxiv:
        return "arxiv"
    if ref.repos and f.repo in ref.repos:
        return "repo"
    if f.url and f.url in ref.url_keys:
        return "url"
    if ref.set == "negative":
        return "title" if f.title_key and any(len(nk) > 12 and fuzz.ratio(nk, f.title_key) >= TITLE_THRESHOLD for nk in ref.name_keys) else ""
    return "name" if any(keys_match(nk, f.head_key, NAME_THRESHOLD) for nk in ref.name_keys) else ""


def match_vote(ref: Ref, row: dict[str, str], cand: dict[str, str]) -> str:
    """Match basis of one full-text vote against a reference: name, repo, arxiv, title, or ''."""
    if ref.set == "negative":
        if ref.arxiv and arxiv_of(row["record_id"], cand) == ref.arxiv:
            return "arxiv"
        if url_key(cand.get("url") or "") in ref.url_keys:
            return "url"
        return "title" if title_hit(ref, row.get("document_title_seen") or "") else ""
    if name_hit(ref, row.get("system_name") or ""):
        return "name"
    if ref.repos and repo_key(row.get("repo_url") or "") in ref.repos:
        return "repo"
    if ref.arxiv and arxiv_of(row["record_id"], cand) == ref.arxiv:
        return "arxiv"
    return ""


def mentioned(ref: Ref, row: dict[str, str]) -> bool:
    return any(name_hit(ref, m) for m in jl(row.get("systems_mentioned", "")) if isinstance(m, str))


def match_system(ref: Ref, srow: dict[str, str], matched_ids: set[str]) -> bool:
    if name_hit(ref, srow.get("name") or "") or any(name_hit(ref, v) for v in (srow.get("name_variants") or "").split(";")):
        return True
    if ref.repos and repo_key(srow.get("repo_url") or "") in ref.repos:
        return True
    return bool(matched_ids & set((srow.get("member_record_ids") or "").split(";")))


# --------------------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------------------


def busy_seconds(rows: list[dict[str, str]]) -> tuple[float, float, int]:
    """(union of batch intervals in seconds, sum of batch seconds, n records with an LLM call)."""
    batches: dict[str, tuple[datetime, float]] = {}
    n = 0
    for r in rows:
        if not r.get("batch_started_at"):
            continue
        n += 1
        try:
            batches[r["batch_id"]] = (datetime.fromisoformat(r["batch_started_at"]), float(r["batch_seconds"] or 0))
        except ValueError:
            continue
    ivals = sorted((s, s + timedelta(seconds=d)) for s, d in batches.values())
    union, cur_s, cur_e = 0.0, None, None
    for s, e in ivals:
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                union += (cur_e - cur_s).total_seconds()
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        union += (cur_e - cur_s).total_seconds()
    return union, sum(d for _, d in batches.values()), n


# --------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------


def table(header: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |" for r in rows]
    return "\n".join(out)


def codable_bins(vals: list[int]) -> list[list[Any]]:
    bins = [(0, 4), (5, 9), (10, 14), (15, 18), (19, 22), (23, 26), (27, 30), (31, 38)]
    return [[f"{a}-{b}", sum(a <= v <= b for v in vals)] for a, b in bins]


def build(args: argparse.Namespace) -> tuple[str, dict[str, Any], dict[str, Any]]:
    cands = {r["id"]: r for r in read_csv(CANDIDATES)}
    queue = {r["record_id"] for r in read_csv(QUEUE)}
    pilot_rows = read_csv(PILOT)
    why = {r["record_id"]: r.get("why", "") for r in pilot_rows}
    scope = set(why) if args.pilot else set(queue)
    p1 = [r for r in read_csv(Path(args.votes)) if r["record_id"] in scope]
    p2 = [r for r in read_csv(Path(args.pass2)) if r["record_id"] in scope]
    final = [r for r in read_csv(Path(args.final)) if r["record_id"] in scope]
    systems = read_csv(Path(args.systems))
    if args.pilot:
        systems = [s for s in systems if set(s["member_record_ids"].split(";")) & scope]
    refs = load_refs()
    p2_by = {r["record_id"]: r for r in p2}
    p1_by = {r["record_id"]: r for r in p1}
    final_by = {r["record_id"]: r for r in final}
    index = {r["record_id"]: r for r in read_csv(INDEX)}
    L: list[str] = []
    title = "Full-text screening report" + (" (pilot)" if args.pilot else "")
    L += [f"# {title}", "", f"Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} by `scripts/validate_screening.py`"
          + (" --pilot" if args.pilot else "") + ".",
          (f"Scope: {len(scope)} records ({'data/screening/fulltext_pilot.csv' if args.pilot else 'data/screening/fulltext_queue.csv'}); "
           f"pass-1 rows {len(p1)}, pass-2 rows {len(p2)}, final rows {len(final)}, systems {len(systems)}."), ""]
    if not p1:
        L.append("No pass-1 votes in scope yet.")
        return "\n".join(L), {}, {}

    llm1 = [r for r in p1 if r["exclusion_code"] != "not_retrievable"]
    inc1 = [r for r in p1 if r["decision"] == "include"]
    nr1 = [r for r in p1 if r["exclusion_code"] == "not_retrievable"]
    models = Counter(r["model"] for r in llm1)
    prompts = Counter(r["prompt_version"] for r in p1)
    L += ["## 1. Decisions", "",
          f"Model(s): {dict(models)}; prompt(s): {dict(prompts)}.", "",
          f"- Pass-1 include rate, all records in scope: {ci(len(inc1), len(p1))}",
          f"- Pass-1 include rate, records with full text (LLM read): {ci(len(inc1), len(llm1))}",
          f"- not_retrievable (index says not ok; no LLM call): {len(nr1)}",
          f"- Pending (in scope, no pass-1 row yet): {len(scope - {r['record_id'] for r in p1})}"]
    if final:
        fc = Counter(r["final_decision"] for r in final)
        L.append(f"- Final (after pass 2 and the registry): {dict(fc)}; systems in registry: {len(systems)}")
    L.append("")
    if why:
        rows = []
        for g in sorted({why[r["record_id"]] for r in p1 if r["record_id"] in why}):
            grp = [r for r in p1 if why.get(r["record_id"]) == g]
            g_llm = [r for r in grp if r["exclusion_code"] != "not_retrievable"]
            rows.append([g, len(grp), sum(r["exclusion_code"] == "not_retrievable" for r in grp),
                         ci(sum(r["decision"] == "include" for r in grp), len(grp)),
                         ci(sum(r["decision"] == "include" for r in g_llm), len(g_llm))])
        L += ["Include rate by pilot stratum (pass 1):", "", table(["stratum", "n", "not retrievable", "include / all", "include / with full text"], rows), ""]

    by_src: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in p1:
        by_src[r["candidate_source"] or (cands.get(r["record_id"], {}).get("source") or "?")].append(r)
    L += ["Include rate by source (pass 1):", "",
          table(["source", "n", "not retrievable", "include rate (all)"],
                [[s, len(v), sum(r["exclusion_code"] == "not_retrievable" for r in v), ci(sum(r["decision"] == "include" for r in v), len(v))]
                 for s, v in sorted(by_src.items(), key=lambda kv: -len(kv[1]))]), ""]

    # exclusion reasons and steps
    ex1 = [r for r in p1 if r["decision"] == "exclude"]
    codes = Counter((r["exclusion_code"], r["exclusion_subreason"] or "-") for r in ex1)
    L += ["## 2. Exclusion reasons and deciding steps (pass 1)", "",
          table(["exclusion_code", "sub-reason", "n", "% of excludes"], [[c, s, n, f"{n / len(ex1):.1%}"] for (c, s), n in codes.most_common()]) if ex1 else "(none)", ""]
    steps = Counter(r["deciding_step"] or "-" for r in p1)
    L += [table(["deciding step", "n"], [[s, n] for s, n in sorted(steps.items(), key=lambda kv: (len(kv[0]), kv[0]))]), ""]
    conf = Counter((r["decision"], r["confidence"]) for r in llm1)
    L += ["Confidence: " + ", ".join(f"{d}/{c}: {n}" for (d, c), n in sorted(conf.items())), ""]

    # codability
    cc_all = [int(r["codable_count_computed"] or 0) for r in llm1]
    cc_inc = [int(r["codable_count_computed"] or 0) for r in inc1]
    reach7 = [r for r in llm1 if any(int(s.get("step", 0)) == 7 for s in jl(r["step_evidence"]))]
    L += ["## 3. Codability (criterion b; count of the 38 dimensions the evidence bundle supports)", "",
          ("Amendment 5: the count is recorded at screening and enforced at coding; step 7 only excludes a record with no "
           "admissible artifact at all (`no_harness_description` / `no_artifact`)."), "",
          table(["codable_count", "all LLM-read records", "records reaching step 7", "pass-1 includes"],
                [[b, n, m, k] for (b, n), (_, m), (_, k) in zip(codable_bins(cc_all), codable_bins([int(r["codable_count_computed"] or 0) for r in reach7]), codable_bins(cc_inc), strict=True)]), ""]
    if cc_inc:
        L.append(f"Includes: median codable_count {statistics.median(cc_inc)}, min {min(cc_inc)}, max {max(cc_inc)}; exact distribution {dict(sorted(Counter(cc_inc).items()))}.")
    if reach7:
        L.append(f"Records reaching step 7: {len(reach7)}; excluded there for a missing artifact: {sum(r['deciding_step'] == '7' for r in reach7)}.")
    cf = Counter((r.get("codability_flag_computed") or r.get("codability_flag") or "-") for r in llm1)
    if any(k != "-" for k in cf):
        L.append("codability_flag (all LLM-read records): " + ", ".join(f"{k} {v}" for k, v in sorted(cf.items()))
                 + "; among pass-1 includes: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter((r.get("codability_flag_computed") or r.get("codability_flag") or "-") for r in inc1).items())) + ".")
    with_repo = [r for r in llm1 if (r.get("repo_evidence") or "0") == "1"]
    without_repo = [r for r in llm1 if (r.get("repo_evidence") or "0") != "1"]
    if with_repo:
        def med(rows: list[dict[str, str]]) -> str:
            vals = [int(r["codable_count_computed"] or 0) for r in rows]
            return f"{statistics.median(vals):.0f}" if vals else "n/a"

        L.append(f"Repository evidence in the bundle (Amendment 5): {ci(len(with_repo), len(llm1))}; median codable_count "
                 f"{med(with_repo)} with a repository vs {med(without_repo)} without; include rate "
                 f"{ci(sum(r['decision'] == 'include' for r in with_repo), len(with_repo))} vs "
                 f"{ci(sum(r['decision'] == 'include' for r in without_repo), len(without_repo))}.")
    layer_cov = Counter(L_ for r in inc1 for L_ in jl(r["layers_covered"]))
    if inc1:
        L.append("Layer coverage among includes: " + ", ".join(f"{k} {v}/{len(inc1)}" for k, v in sorted(layer_cov.items())) + ".")
    L.append("")

    # quality flags
    flags = Counter(f for r in llm1 for f in jl(r["flags"]))
    qt = sum(int(r["quotes_total"] or 0) for r in llm1)
    qv = sum(int(r["quotes_verbatim"] or 0) for r in llm1)
    ew = [int(r["excerpt_words"] or 0) for r in llm1]
    fw = [int(r["fulltext_words"] or 0) for r in llm1]
    mism = [r for r in llm1 if r["candidate_title"] and r["document_title_seen"] and not title_similar(r["candidate_title"], r["document_title_seen"])]
    L += ["## 4. Evidence quality and systematic checks", "",
          f"- Quotes found verbatim in the excerpt the model saw (case/punctuation-insensitive): {ci(qv, qt)}",
          f"- Post-hoc flags (pass 1): {dict(flags.most_common()) or 'none'}",
          (f"- Excerpt words: median {statistics.median(ew) if ew else 'n/a'}, max {max(ew) if ew else 'n/a'}; full-text words: median {statistics.median(fw) if fw else 'n/a'}, "
           f"sent whole (<= cap): {sum(1 for a, b in zip(ew, fw, strict=True) if b and a >= b)}"),
          f"- Document title seen differs from the candidate title (fuzzy < 80): {len(mism)} records"
          + (" (" + "; ".join(f"{r['record_id']}: '{r['document_title_seen'][:60]}'" for r in mism[:12]) + (" ..." if len(mism) > 12 else "") + ")" if mism else ""),
          ""]
    src_used = Counter(r["source_used"] or "?" for r in llm1)
    L += [f"Full-text source used: {dict(src_used.most_common())}", ""]

    # pass agreement
    L += ["## 5. Independent second reading (pass 1 vs pass 2)", ""]
    pairs, wts, both = [], [], []
    for r in p2:
        a = p1_by.get(r["record_id"])
        if a is None:
            continue
        pairs.append((a["decision"], r["decision"]))
        wts.append(1.0 if a["decision"] == "include" else 1 / PASS2_EXCLUDE_FRACTION)
        both.append((a, r))
    kap = {}
    if pairs:
        k, po, n = cohen_kappa([a for a, _ in pairs], [b for _, b in pairs])
        wk, wpo = weighted_kappa(pairs, wts)
        cm = Counter(pairs)
        kap = {"n": n, "kappa": k, "agreement": po, "weighted_kappa": wk, "weighted_agreement": wpo}
        L += [(f"Records read twice: {n}. Coverage is uneven and non-random: the executed run "
              f"used the two-tier escalation in scripts/phase3_autopilot.py, which routes every "
              f"tier-1 exclude and every low-confidence decision to the second reader, so this "
              f"sample characterises the disputed part of the screen rather than the screen as a "
              f"whole. See docs/count_reconciliation.md for the per-decision coverage."), "",
              table(["", "pass 2 include", "pass 2 exclude"], [["pass 1 include", cm[("include", "include")], cm[("include", "exclude")]],
                                                             ["pass 1 exclude", cm[("exclude", "include")], cm[("exclude", "exclude")]]]), "",
              f"- Cohen's kappa (sample as drawn): {k:.3f}; observed agreement {ci(sum(a == b for a, b in pairs), n)}",
              f"- Population-weighted (excludes weighted x{1 / PASS2_EXCLUDE_FRACTION:.0f}): kappa {wk:.3f}, agreement {wpo:.1%}",
              f"- Pass-1 includes confirmed by pass 2: {ci(cm[('include', 'include')], cm[('include', 'include')] + cm[('include', 'exclude')])}",
              f"- Sampled pass-1 excludes confirmed by pass 2: {ci(cm[('exclude', 'exclude')], cm[('exclude', 'exclude')] + cm[('exclude', 'include')])}"]
        bx = [(a, b) for a, b in both if a["decision"] == b["decision"] == "exclude"]
        if bx:
            L.append(f"- Same exclusion code among both-exclude pairs: {ci(sum(a['exclusion_code'] == b['exclusion_code'] for a, b in bx), len(bx))}; "
                     f"same deciding step: {ci(sum(a['deciding_step'] == b['deciding_step'] for a, b in bx), len(bx))}")
        bi = [(a, b) for a, b in both if a["decision"] == b["decision"] == "include"]
        if bi:
            L.append(f"- Same system name among both-include pairs (fuzzy >= 90): {ci(sum(names_match(a['system_name'], b['system_name'], NAME_THRESHOLD) for a, b in bi), len(bi))}")
        cdiff = [abs(int(a["codable_count_computed"] or 0) - int(b["codable_count_computed"] or 0)) for a, b in both]
        if cdiff:
            L.append(f"- |codable_count pass 1 - pass 2|: median {statistics.median(cdiff)}, mean {statistics.mean(cdiff):.1f}, max {max(cdiff)}")
        dis = [(a, b) for a, b in both if a["decision"] != b["decision"]]
        if dis:
            L += ["", "Disagreements:", "", table(["record", "pass 1", "pass 2", "title seen"],
                  [[a["record_id"], f"{a['decision']} {a['exclusion_code']} s{a['deciding_step']} c{a['codable_count_computed']}",
                    f"{b['decision']} {b['exclusion_code']} s{b['deciding_step']} c{b['codable_count_computed']}", a["document_title_seen"][:70]] for a, b in dis])]
    else:
        L.append("No pass-2 rows in scope yet.")
    L.append("")

    # reference sets
    L += ["## 6. Reference sets", ""]
    feats = [cand_features(rid, c) for rid, c in cands.items() if (rid in scope if args.pilot else True)]
    pos_rows, lost, details = [], [], []
    audit_ref: dict[str, str] = {}
    stage_found = Counter()
    in_scope_pos = 0
    for ref in [r for r in refs if r.set == "positive"]:
        cm_ = {f.rid: b for f in feats if (b := match_candidate(ref, f))}
        s1 = bool(cm_)
        fwd = {rid for rid in cm_ if rid in queue}
        s2 = bool(fwd)
        vm = {r["record_id"]: b for r in p1 if (b := match_vote(ref, r, cands.get(r["record_id"], {})))}
        inc = {rid for rid in vm if p1_by[rid]["decision"] == "include"}
        s3 = bool(inc)
        matched_systems = [s for s in systems if match_system(ref, s, set(vm))]
        s4 = bool(matched_systems)
        s5 = any(str(s.get("in_frame") or "0") == "1" for s in matched_systems)  # Amendment 5 coding frame
        ment = sum(mentioned(ref, r) for r in p1)
        if args.pilot and not (s1 or vm):
            continue  # reference not represented among pilot records
        in_scope_pos += 1
        for rid in set(cm_) | set(vm):
            audit_ref.setdefault(rid, ref.name)
        flags_ = [s1, s2, s3, s4, s5]
        for st, ok in zip(STAGES, flags_, strict=True):
            stage_found[st] += ok
        lost_at = next((st for st, ok in zip(STAGES, flags_, strict=True) if not ok), "")
        screened = [x for x in p1 if x["record_id"] in (set(cm_) | set(vm))]
        if lost_at == "fulltext_include":
            if not screened:
                lost_at = "fulltext_include (not screened yet)"
            elif all(x["exclusion_code"] == "not_retrievable" for x in screened):
                lost_at = "fulltext_include (not retrievable)"
        elif lost_at == "registry":
            fin = [final_by.get(x["record_id"], {}).get("final_decision", "") for x in screened if x["decision"] == "include"]
            if "disputed" in fin:
                lost_at = "registry (disputed: pass 2 disagreed)"
            elif not final:
                lost_at = "registry (not run yet)"
        elif lost_at == "coding_frame":
            lost_at = "coding_frame (in the census, outside the coded subset: " + (
                ", ".join(sorted({s["system_id"] for s in matched_systems})) or "-") + ")"
        how = "; ".join(f"{x['record_id']}: {x['decision']} {x['exclusion_code']}/{x['exclusion_subreason']} step {x['deciding_step']} codable {x['codable_count_computed']} name '{x['system_name']}'" for x in screened[:4])
        frame_cell = ("yes: " + ";".join(sorted({s.get("frame_reason", "") for s in matched_systems if s.get("frame_reason")}))) if s5 else ("no" if s4 else "-")
        pos_rows.append([ref.name, len(cm_), len(fwd), len(inc), "yes" if s4 else "no", frame_cell, ment, lost_at or "-"])
        if lost_at:
            lost.append([ref.name, lost_at, ", ".join(sorted(cm_)[:3]) or "-", how or "-", ref.source])
        details.append((ref, cm_, vm))
    L += [f"Positive set: {len([r for r in refs if r.set == 'positive'])} known harness systems"
          + (f"; {in_scope_pos} represented among pilot records (matched by a pilot candidate record or a pilot full-text vote)" if args.pilot else "") + ".", ""]
    if in_scope_pos:
        L += ["Recall by stage:", ""] + [f"- {st}: {ci(stage_found[st], in_scope_pos)}" for st in STAGES] + [""]
        L += [table(["system", "candidate records", "forwarded", "pass-1 include records", "in registry", "in coding frame", "mentioned in n records", "lost at"], pos_rows), ""]
    if lost:
        L += ["Missing positive reference systems (stage where lost; the full-text decision of matched records):", "",
              table(["system", "lost at", "matched records", "full-text decision(s)", "catalogued by"], lost), ""]
    neg_rows = []
    nk = nn = 0
    for ref in [r for r in refs if r.set == "negative"]:
        cm_ = {f.rid: b for f in feats if (b := match_candidate(ref, f))}
        vm = [r for r in p1 if match_vote(ref, r, cands.get(r["record_id"], {})) or r["record_id"] in cm_]
        fwd = [rid for rid in cm_ if rid in queue]
        dec = "; ".join(f"{r['decision']} {r['exclusion_code']}/{r['exclusion_subreason']}" for r in vm) or "-"
        if vm:
            nn += 1
            nk += all(r["decision"] == "exclude" for r in vm)
        for rid in set(cm_) | {r["record_id"] for r in vm}:
            audit_ref.setdefault(rid, "NEG: " + ref.name)
        if args.pilot and not (cm_ or vm):
            continue
        neg_rows.append([ref.name, len(cm_), len(fwd), len(vm), dec])
    L += [f"Negative set: {len([r for r in refs if r.set == 'negative'])} surveys, benchmarks and evaluation studies (expected exclude).", ""]
    if neg_rows:
        L += [table(["record", "candidate records", "forwarded", "full-text screened", "full-text decision"], neg_rows), ""]
    L += [f"- Specificity at full text (negatives screened at full text and excluded): {ci(nk, nn)}", ""]

    # time and cost
    L += ["## 7. Time and cost", ""]
    proj: dict[str, Any] = {}
    for label, rows in (("pass 1", p1), ("pass 2", p2)):
        union, serial, n = busy_seconds(rows)
        cost = sum(float(r["cost_usd"] or 0) for r in rows if r.get("batch_started_at"))
        if not n:
            continue
        conc = serial / union if union else float("nan")
        L.append(f"- {label}: {n} LLM records; busy wall time {union / 60:.1f} min (union of batch intervals; effective concurrency {conc:.1f}); "
                 f"{union / n:.1f} s/record wall, {serial / n:.1f} s/record serial; list-equivalent ${cost:.2f} = ${cost / n:.3f}/record; "
                 f"tokens/record in {statistics.mean(int(r['tokens_in'] or 0) for r in rows if r.get('batch_started_at')):.0f}, "
                 f"out {statistics.mean(int(r['tokens_out'] or 0) for r in rows if r.get('batch_started_at')):.0f}")
        proj[label] = {"n": n, "wall_s_per_rec": union / n, "cost_per_rec": cost / n, "concurrency": conc}
    N = len(queue)
    if "pass 1" in proj:
        rnd = [r for r in p1 if why.get(r["record_id"]) == "random"] if args.pilot else p1
        rnd_llm = [r for r in rnd if r["exclusion_code"] != "not_retrievable"]
        k_inc = sum(r["decision"] == "include" for r in rnd)
        p_inc, lo, hi = wilson(k_inc, len(rnd))
        nr_rate = (len(rnd) - len(rnd_llm)) / len(rnd) if rnd else 0.0
        n_llm = N * (1 - nr_rate)
        inc_proj = (p_inc * N, lo * N, hi * N)
        excl_llm = max(0.0, n_llm - inc_proj[0])
        n_p2 = inc_proj[0] + PASS2_EXCLUDE_FRACTION * excl_llm
        pp1, pp2 = proj["pass 1"], proj.get("pass 2", proj["pass 1"])
        t1, t2 = n_llm * pp1["wall_s_per_rec"], n_p2 * pp2["wall_s_per_rec"]
        c1, c2 = n_llm * pp1["cost_per_rec"], n_p2 * pp2["cost_per_rec"]
        basis = "the 250 random pilot records" if args.pilot else "all pass-1 records"
        L += ["", f"Projection to the whole queue ({N} records), from {basis} and the measured rates:", "",
              f"- not retrievable: {nr_rate:.1%} of records -> about {N - n_llm:.0f} without an LLM reading, {n_llm:.0f} read",
              f"- includes (pass 1): {ci(k_inc, len(rnd))} -> about {inc_proj[0]:.0f} records [{inc_proj[1]:.0f}, {inc_proj[2]:.0f}]",
              f"- pass 1: {t1 / 3600:.1f} h wall at the measured concurrency ({pp1['concurrency']:.1f}), ${c1:,.0f} list-equivalent",
              f"- pass 2 ({n_p2:.0f} records): {t2 / 3600:.1f} h wall, ${c2:,.0f} list-equivalent",
              f"- total: {(t1 + t2) / 3600:.1f} h, ${c1 + c2:,.0f} list-equivalent (consumed as Claude Code subscription usage, not billed)"]
        n_sys = len(systems)
        n_reg_inc = sum(1 for r in final if r["final_decision"] == "include")
        if inc_proj[0] > 2 * EXPECTED_SYSTEMS[1]:
            L += ["", (f"**Warning: the projected include count (~{inc_proj[0]:.0f} records, 95% CI {inc_proj[1]:.0f}-{inc_proj[2]:.0f}) is far above the "
                       f"150-300 systems the protocol expected.** Deduplication into systems will lower it (pilot: {n_sys} systems from {n_reg_inc} final includes), "
                       "but not by that factor if most includes are one-paper systems. The codable_count distribution of includes is in section 3; "
                       "tightening criterion (b) is the author's decision.")]
        proj["projection"] = {"queue": N, "not_retrievable_rate": nr_rate, "includes": inc_proj, "pass1_hours": t1 / 3600, "pass2_hours": t2 / 3600,
                              "cost_usd": c1 + c2, "pass2_records": n_p2}
    L.append("")

    # registry
    if systems:
        L += ["## 8. System registry", "", (f"{len(systems)} systems from {sum(int(s['n_members']) for s in systems)} included records; "
                                            f"{sum(int(s['n_members']) > 1 for s in systems)} with more than one record."), "",
              table(["system_id", "name", "members", "canonical", "max codable", "repo"],
                    [[s["system_id"], s["name"], s["n_members"], s["canonical_record_id"], s["max_codable_count"], s["repo_url"]] for s in systems[:400]]), ""]

    # audit data
    recs = []
    for r in p1:
        s = p2_by.get(r["record_id"])
        f = final_by.get(r["record_id"], {})
        c = cands.get(r["record_id"], {})
        recs.append({
            "id": r["record_id"], "title": r["document_title_seen"], "cand_title": r["candidate_title"], "source": r["candidate_source"] or c.get("source", ""),
            "url": c.get("url", ""), "fetched_url": r.get("fetched_url", ""), "used": r["source_used"], "why": why.get(r["record_id"], ""),
            "d": r["decision"], "code": r["exclusion_code"], "sub": r["exclusion_subreason"], "step": r["deciding_step"], "conf": r["confidence"],
            "sys": r["system_name"], "ver": r["system_version"], "repo": r["repo_url"], "rel": r["release_date"],
            "cc": int(r["codable_count_computed"] or 0), "layers": jl(r["layers_covered"]), "dims": jl(r["codable_dimensions"]),
            "ev": jl(r["step_evidence"]), "ment": jl(r["systems_mentioned"]), "flags": jl(r["flags"]),
            "ew": int(r["excerpt_words"] or 0), "fw": int(r["fulltext_words"] or 0),
            "p2": ({"d": s["decision"], "code": s["exclusion_code"], "sub": s["exclusion_subreason"], "step": s["deciding_step"], "sys": s["system_name"],
                    "cc": int(s["codable_count_computed"] or 0), "ev": jl(s["step_evidence"])} if s else None),
            "final": f.get("final_decision", ""), "sid": f.get("system_id", ""), "canon": f.get("is_canonical", ""), "ref": audit_ref.get(r["record_id"], ""),
            "fetch_status": (index.get(r["record_id"]) or {}).get("status", ""),
        })
    audit = {"generated": datetime.now(UTC).isoformat(timespec="seconds"), "scope": "pilot" if args.pilot else "queue",
             "prompt_version": ", ".join(prompts), "model": ", ".join(models), "n_scope": len(scope), "records": recs}
    stats = {"include_rate": wilson(len(inc1), len(p1)), "kappa": kap, "projection": proj.get("projection"), "recall": dict(stage_found), "positives_in_scope": in_scope_pos,
             "lost": lost, "specificity": (nk, nn), "flags": dict(flags), "quotes": (qv, qt)}
    return "\n".join(L), audit, stats


def title_similar(a: str, b: str) -> bool:
    ka, kb = key_of(a), key_of(b)
    return bool(ka and kb) and (fuzz.ratio(ka, kb) >= 80 or fuzz.partial_ratio(ka, kb) >= 90)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--pilot", action="store_true", help="restrict to the records of data/screening/fulltext_pilot.csv")
    p.add_argument("--votes", default=str(PASS1), help="pass-1 votes (default fulltext_votes_v2.csv)")
    p.add_argument("--pass2", default=str(PASS2), help="pass-2 votes (default fulltext_votes_v2_pass2.csv)")
    p.add_argument("--final", default=str(FINAL))
    p.add_argument("--systems", default=str(SYSTEMS))
    p.add_argument("--report", default=str(REPORT))
    p.add_argument("--audit-js", default=str(AUDIT_JS))
    args = p.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    md, audit, stats = build(args)
    Path(args.report).write_text(md + "\n", encoding="utf-8")
    if audit:
        Path(args.audit_js).write_text("window.AUDIT = " + json.dumps(audit, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("SUMMARY " + json.dumps(stats, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
