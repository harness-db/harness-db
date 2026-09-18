#!/usr/bin/env python
"""Group full-text includes into systems (protocol 4.1-4.4) and write the final screening decisions.

Input: ``data/screening/fulltext_votes.csv`` (pass 1) and ``fulltext_votes_pass2.csv`` (the
independent second reading of every pass-1 include and 10% of excludes). A record enters the
registry when pass 1 includes it and pass 2 agrees (or has not read it yet; flagged). A pass-1
include that pass 2 excludes, and a sampled pass-1 exclude that pass 2 includes, are
``disputed`` and held out of the registry (``--disputed`` can resolve them either way instead).

Grouping, in order:
1. normalise ``system_name`` (case, dashes, quotes, parenthetical descriptors dropped) and split
   off a version token (``v2``, trailing ``2.0``, ``S2``) into a base name;
2. merge records that give the same repository (``github.com/owner/repo`` plus any sub-path, so
   agents living in sub-directories of one monorepo stay apart);
3. merge records whose base names have rapidfuzz ratio >= 92 (alphanumerics only; names of
   four characters or fewer must match exactly);
4. version rule (protocol 4.4): inside a group a member gets its own ``<system_id>-v<N>`` row only
   when its name carries a major version N >= 2 AND the document says so (the stated
   ``system_version`` has the same major, or the document's own title carries the versioned
   name, i.e. a new paper on that version); otherwise everything is one row. The second 4.4
   condition (coding differs on >= 3 dimensions) can only be checked at coding and is left to it.

Canonical record per group (protocol 4.2): the source that first names the system (earliest
arXiv month, else stated date, else year); on a tie a repository wins. Non-canonical members are
final ``exclude`` / ``duplicate_system`` (step 10), linked to the system.

Outputs: ``data/systems_candidates.csv`` (one row per system-version) and
``data/screening/fulltext_votes_final.csv`` (one row per screened record).

Usage:
    python scripts/system_registry.py
    python scripts/system_registry.py --ids data/screening/fulltext_pilot.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

REPO = Path(__file__).resolve().parents[1]
SCREEN_DIR = REPO / "data" / "screening"
PASS1 = SCREEN_DIR / "fulltext_votes.csv"
PASS2 = SCREEN_DIR / "fulltext_votes_pass2.csv"
FINAL = SCREEN_DIR / "fulltext_votes_final.csv"
SYSTEMS = REPO / "data" / "systems_candidates.csv"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"

NAME_THRESHOLD = 92
SHORT_NAME = 4

SYSTEM_COLUMNS = ["system_id", "name", "version", "repo_url", "release_date", "member_record_ids", "canonical_record_id",
                  "max_codable_count", "n_members", "name_variants", "second_reading", "grouped_by"]
FINAL_COLUMNS = ["record_id", "final_decision", "exclusion_code", "exclusion_subreason", "deciding_step", "system_id",
                 "is_canonical", "pass1_decision", "pass1_code", "pass1_step", "pass2_decision", "pass2_code", "pass2_step",
                 "agreement", "note"]


# --------------------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------------------


def norm_name(name: str) -> str:
    """Display-level normalisation: NFKC, lowercase, unified dashes/quotes, no parentheticals, single spaces."""
    s = unicodedata.normalize("NFKC", name or "").lower()
    s = re.sub(r"[‐-―−]", "-", s).replace("’", "'")
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", s)
    s = re.sub(r"^the\s+", "", s.strip())
    s = re.sub(r"[\"'`*]", "", s)
    return re.sub(r"\s+", " ", s).strip(" -:;,.")


def key_of(name: str) -> str:
    """Matching key: alphanumerics only."""
    return re.sub(r"[^a-z0-9]+", "", norm_name(name))


VERSION_PATTERNS = [
    re.compile(r"(?:^|[\s_-])v\.?\s?(?P<major>\d+)(?:\.\d+)*$"),     # "... v2", "...-v2.1"
    re.compile(r"(?:^|[\s_-])v\.?\s?(?P<major>\d+)(?:\.\d+)*(?=\s)"),  # "Foo v2 agent"
    re.compile(r"[\s_-](?P<major>\d+)(?:\.\d+)*$"),                    # "MetaGPT 2", "AutoGen 0.4"
    re.compile(r"(?<=[a-z])(?P<major>\d+)(?:\.\d+)*$"),                 # "Agent S2", "Agent S2.5"
]


def split_version(name: str) -> tuple[str, int | None]:
    """(base name, major version) from a system name; major None when the name carries none."""
    n = norm_name(name)
    for pat in VERSION_PATTERNS:
        m = pat.search(n)
        if m:
            base = (n[: m.start()] + " " + n[m.end():]).strip(" -_")
            base = re.sub(r"\s+", " ", base)
            if len(key_of(base)) >= 2:
                return base, int(m.group("major"))
    return n, None


def major_of(version: str) -> int | None:
    m = re.search(r"(\d+)", version or "")
    return int(m.group(1)) if m else None


def repo_key(url: str) -> str:
    """``github.com/owner/repo[/subpath]`` in lowercase; empty for non-repository URLs."""
    u = (url or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u).split("#")[0].split("?")[0].rstrip("/")
    m = re.match(r"^(github\.com|gitlab\.com|huggingface\.co|bitbucket\.org|codeberg\.org)/([^/]+)/([^/]+)(/.*)?$", u)
    if not m:
        return ""
    host, owner, repo, rest = m.group(1), m.group(2), re.sub(r"\.git$", "", m.group(3)), m.group(4) or ""
    sub = ""
    t = re.match(r"^/(?:tree|blob)/[^/]+/(.+)$", rest)
    if t:
        sub = "/" + re.sub(r"/(readme(\.\w+)?)$", "", t.group(1)).strip("/")
        sub = "" if sub == "/" else sub
    return f"{host}/{owner}/{repo}{sub}"


def keys_match(ka: str, kb: str, threshold: int = NAME_THRESHOLD) -> bool:
    """Name match on precomputed keys: exact for short keys, else rapidfuzz ratio >= threshold."""
    if not ka or not kb:
        return False
    if min(len(ka), len(kb)) <= SHORT_NAME:
        return ka == kb
    return fuzz.ratio(ka, kb) >= threshold


def names_match(a: str, b: str, threshold: int = NAME_THRESHOLD) -> bool:
    return keys_match(key_of(a), key_of(b), threshold)


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", norm_name(name)).strip("-")
    return s or "system"


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    csv.field_size_limit(10**8)
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def record_date(rec: dict[str, Any], cand: dict[str, str]) -> tuple[int, int]:
    """(year, month) of the record's first public appearance; (9999, 13) when unknown. Month 13 = year only."""
    rid = rec["record_id"]
    arx = (cand.get("arxiv_id") or "").strip() or (rid.split(":", 1)[1] if rid.startswith("arxiv:") else "")
    m = re.match(r"^(\d{2})(\d{2})\.\d{4,5}", arx)
    if m and 1 <= int(m.group(2)) <= 12:
        return 2000 + int(m.group(1)), int(m.group(2))
    d = re.match(r"^(\d{4})(?:-(\d{2}))?", rec.get("release_date") or "")
    if d:
        return int(d.group(1)), int(d.group(2) or 13)
    y = re.match(r"^(\d{4})", str(cand.get("year") or ""))
    return (int(y.group(1)), 13) if y else (9999, 13)


def is_repo_record(rec: dict[str, Any], cand: dict[str, str]) -> bool:
    rid = rec["record_id"].lower()
    src = f"{rec.get('source_used', '')} {cand.get('source', '')}".lower()
    return rid.startswith("github:") or "github" in src or bool(repo_key(cand.get("url") or "") and cand.get("source") in ("github", "awesome"))


def docs_confirm_version(rec: dict[str, Any], major: int) -> bool:
    if major_of(rec.get("system_version") or "") == major:
        return True
    name_key = key_of(rec.get("system_name") or "")
    return bool(name_key) and name_key in key_of(rec.get("document_title_seen") or "")


class UnionFind:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def group_records(recs: list[dict[str, Any]], cands: dict[str, dict[str, str]] | None = None) -> list[dict[str, Any]]:
    """Group included records into system rows. Each rec needs record_id, system_name, system_version,
    repo_url, release_date, document_title_seen, codable_count_computed (or codable_count)."""
    cands = cands or {}
    n = len(recs)
    uf = UnionFind(n)
    how: dict[int, set[str]] = defaultdict(set)
    base = [split_version(r.get("system_name") or "") for r in recs]
    rkeys = [repo_key(r.get("repo_url") or "") for r in recs]
    by_repo: dict[str, int] = {}
    for i, k in enumerate(rkeys):
        if k:
            if k in by_repo:
                uf.union(i, by_repo[k])
                how[i].add("repo")
                how[by_repo[k]].add("repo")
            else:
                by_repo[k] = i
    for i in range(n):
        for j in range(i + 1, n):
            if base[i][0] and base[j][0] and names_match(base[i][0], base[j][0]):
                uf.union(i, j)
                how[i].add("name")
                how[j].add("name")
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)

    rows = []
    for members in groups.values():
        parts: dict[int | None, list[int]] = defaultdict(list)
        for i in members:
            major = base[i][1]
            eff = major if (major is not None and major >= 2 and docs_confirm_version(recs[i], major)) else None
            parts[eff].append(i)
        # a confirmed major version keeps its -v<N> id even when no earlier version is in the corpus,
        # so that ids stay stable as more records are screened
        for eff, idx in parts.items():
            def order(i: int) -> tuple[Any, ...]:
                c = cands.get(recs[i]["record_id"], {})
                return (record_date(recs[i], c), 0 if is_repo_record(recs[i], c) else 1, recs[i]["record_id"])

            idx = sorted(idx, key=order)
            canon = recs[idx[0]]
            base_name = base[idx[0]][0] or norm_name(canon.get("system_name") or "")
            sid = slug(base_name) + (f"-v{eff}" if eff is not None else "")
            repos = Counter(rkeys[i] for i in idx if rkeys[i])
            dates = sorted(d for i in idx if (d := (recs[i].get("release_date") or "").strip()) and re.match(r"^\d{4}", d))
            versions = [recs[i].get("system_version") for i in idx if recs[i].get("system_version")]
            rows.append({
                "system_id": sid,
                "name": canon.get("system_name") or base_name,
                "version": (canon.get("system_version") or (versions[0] if versions else "")) or (str(eff) if eff else ""),
                "repo_url": ("https://" + repos.most_common(1)[0][0]) if repos else "",
                "release_date": dates[0] if dates else "",
                "member_record_ids": ";".join(recs[i]["record_id"] for i in idx),
                "canonical_record_id": canon["record_id"],
                "max_codable_count": max(int(recs[i].get("codable_count_computed") or recs[i].get("codable_count") or 0) for i in idx),
                "n_members": len(idx),
                "name_variants": ";".join(sorted({recs[i].get("system_name") or "" for i in idx})),
                "second_reading": ";".join(sorted({recs[i].get("_second", "") for i in idx} - {""})),
                "grouped_by": ";".join(sorted(set().union(*(how[i] for i in idx)))) or "single",
            })
    # system_id collisions (different systems whose names slug alike): suffix -2, -3
    seen: Counter[str] = Counter()
    for r in sorted(rows, key=lambda r: r["canonical_record_id"]):
        seen[r["system_id"]] += 1
        if seen[r["system_id"]] > 1:
            r["system_id"] = f"{r['system_id']}-{seen[r['system_id']]}"
    return sorted(rows, key=lambda r: r["system_id"])


# --------------------------------------------------------------------------------------
# Final decisions
# --------------------------------------------------------------------------------------


def combine(p1: list[dict[str, str]], p2: list[dict[str, str]], disputed: str = "hold") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (registry input records, final rows without system links)."""
    p2_by = {r["record_id"]: r for r in p2}
    reg, final = [], []
    for r in p1:
        s = p2_by.get(r["record_id"])
        d1, d2 = r["decision"], (s or {}).get("decision", "")
        agreement = "single" if not s else ("agree" if d1 == d2 else "disagree")
        row = {"record_id": r["record_id"], "pass1_decision": d1, "pass1_code": r["exclusion_code"], "pass1_step": r["deciding_step"],
               "pass2_decision": d2, "pass2_code": (s or {}).get("exclusion_code", ""), "pass2_step": (s or {}).get("deciding_step", ""),
               "agreement": agreement, "system_id": "", "is_canonical": "", "note": ""}
        final_dec = d1
        if agreement == "disagree":
            final_dec = {"hold": "disputed", "include": "include", "exclude": "exclude"}[disputed]
            row["note"] = f"pass 1 {d1} vs pass 2 {d2}; resolved by --disputed {disputed}"
        if final_dec == "include":
            src = r if d1 == "include" else s
            rec = dict(src)
            rec["_second"] = "agree" if agreement == "agree" else ("none" if agreement == "single" else f"disputed->{disputed}")
            reg.append(rec)
            row.update({"final_decision": "include", "exclusion_code": "", "exclusion_subreason": "", "deciding_step": "12"})
            if agreement == "single":
                row["note"] = "no second reading yet"
        elif final_dec == "exclude":
            src = r if d1 == "exclude" else s
            row.update({"final_decision": "exclude", "exclusion_code": src["exclusion_code"], "exclusion_subreason": src["exclusion_subreason"],
                        "deciding_step": src["deciding_step"]})
        else:
            row.update({"final_decision": "disputed", "exclusion_code": "", "exclusion_subreason": "", "deciding_step": ""})
        final.append(row)
    return reg, final


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--pass1", default=str(PASS1))
    p.add_argument("--pass2", default=str(PASS2))
    p.add_argument("--ids", default=None, help="restrict to the record_ids of this CSV (e.g. the pilot)")
    p.add_argument("--disputed", choices=("hold", "include", "exclude"), default="hold")
    p.add_argument("--systems-out", default=str(SYSTEMS))
    p.add_argument("--final-out", default=str(FINAL))
    args = p.parse_args(argv)

    p1, p2 = read_csv(Path(args.pass1)), read_csv(Path(args.pass2))
    if args.ids:
        keep = {r["record_id"] for r in read_csv(Path(args.ids))}
        p1 = [r for r in p1 if r["record_id"] in keep]
        p2 = [r for r in p2 if r["record_id"] in keep]
    if not p1:
        print(f"no pass-1 votes in {args.pass1}", file=sys.stderr)
        return 2
    cands = {r["id"]: r for r in read_csv(CANDIDATES)}
    reg, final = combine(p1, p2, args.disputed)
    systems = group_records(reg, cands)
    link = {}
    for s in systems:
        for rid in s["member_record_ids"].split(";"):
            link[rid] = (s["system_id"], rid == s["canonical_record_id"], s["canonical_record_id"])
    for row in final:
        if row["record_id"] in link:
            sid, canon, canon_id = link[row["record_id"]]
            row["system_id"] = sid
            row["is_canonical"] = "1" if canon else "0"
            if not canon:
                row.update({"final_decision": "exclude", "exclusion_code": "duplicate_system", "exclusion_subreason": "",
                            "deciding_step": "10", "note": (row["note"] + "; " if row["note"] else "") + f"same system as canonical {canon_id}"})
    for path, cols, rows in ((Path(args.systems_out), SYSTEM_COLUMNS, systems), (Path(args.final_out), FINAL_COLUMNS, final)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    summary = {"records": len(final), "final": dict(Counter(r["final_decision"] for r in final)), "systems": len(systems),
               "registry_records": len(reg), "multi_member_systems": sum(int(s["n_members"]) > 1 for s in systems),
               "systems_out": args.systems_out, "final_out": args.final_out}
    print("SUMMARY " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
