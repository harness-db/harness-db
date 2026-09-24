#!/usr/bin/env python
"""Group full-text includes into systems (protocol 4.1-4.4), mark the coding frame (Amendment 5)
and write the final screening decisions.

Input: ``--votes`` (default ``data/screening/fulltext_votes_v2.csv``, pass 1) and ``--pass2``
(default ``fulltext_votes_v2_pass2.csv``, the independent second reading of every pass-1 include
and 10% of excludes). A record enters the registry when pass 1 includes it and pass 2 agrees (or
has not read it yet; flagged). A pass-1 include that pass 2 excludes, and a sampled pass-1
exclude that pass 2 includes, are ``disputed`` and held out of the registry (``--disputed`` can
resolve them either way instead).

Coding frame (Amendment 5 iii). Every in-scope system is reported in the census;  HARNESS-DB v1
codes the systems with an accessible implementation, flagged here as columns on
``data/systems_candidates.csv``:

* ``frame_stars``: the system's repository had >= 100 stars at search freeze
  (``data/screening/repo_index.csv``, ``data/raw/github.jsonl``, or the star count the screener
  read out of the repository bundle);
* ``frame_catalogue``: the system is named in a prior harness catalogue or on a tracked
  leaderboard (``data/raw/awesome.jsonl``, ``leaderboards.jsonl``, ``survey_refs`` records, and
  the reference set in ``data/screening/validation_systems.csv``);
* ``frame_vendor``: a vendor or major-lab product with official documentation (a ``grey``
  vendor-docs record, or a repository owned by a major lab or vendor);
* ``frame_peer_reviewed``: a peer-reviewed paper (ACL Anthology, an accepted OpenReview
  submission or a named non-preprint venue) with a public implementation.

``in_frame`` is their disjunction and ``frame_reason`` names the ones that fired. A random sample
of 100 in-scope systems outside the frame (hash order, seed 20260918) carries ``frame_sample``;
those are coded as well, to estimate what the frame misses.

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
    python scripts/system_registry.py --votes data/screening/fulltext_votes.csv   # the v1 pilot
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_triage import sample_hash

REPO = Path(__file__).resolve().parents[1]
SCREEN_DIR = REPO / "data" / "screening"
PASS1 = SCREEN_DIR / "fulltext_votes_v2.csv"
PASS2 = SCREEN_DIR / "fulltext_votes_v2_pass2.csv"
FINAL = SCREEN_DIR / "fulltext_votes_final.csv"
SYSTEMS = REPO / "data" / "systems_candidates.csv"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"
REPO_INDEX = SCREEN_DIR / "repo_index.csv"
VALIDATION = SCREEN_DIR / "validation_systems.csv"
RAW = REPO / "data" / "raw"

NAME_THRESHOLD = 92
SHORT_NAME = 4
FRAME_MIN_STARS = 100  # Amendment 5 (iii)
FRAME_SAMPLE_N = 100
FRAME_SAMPLE_SEED = 20260918

SYSTEM_COLUMNS = ["system_id", "name", "version", "repo_url", "release_date", "member_record_ids", "canonical_record_id",
                  "max_codable_count", "codability_flag", "n_members", "name_variants", "second_reading", "grouped_by",
                  "stars", "in_frame", "frame_reason", "frame_stars", "frame_catalogue", "frame_vendor",
                  "frame_peer_reviewed", "frame_sample"]
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


def letter_tail_conflict(a: str, b: str) -> bool:
    """True when two names flatten to the same key only because one ends in a single-letter token.

    `key_of` drops spaces, so "Agent S" and "Agents" both flatten to `agents`. Combined with version
    stripping that turns "Agent S2" into "Agent S", it merged Simular's Agent S family into AIWaves'
    "Agents" - two unrelated projects. A trailing one-character token is part of the name (Agent S,
    Claude Code W), so names that disagree about having one are not the same name. Names that merely
    disagree about spacing ("Open Hands" against "OpenHands") are unaffected, because neither ends in
    a single-character token.
    """
    ta, tb = norm_name(a).split(), norm_name(b).split()
    if not ta or not tb:
        return False
    return (len(ta[-1]) == 1) != (len(tb[-1]) == 1)


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


CODABILITY_ORDER = {"pass": 3, "borderline": 2, "fail": 1, "": 0}


def best_codability_flag(flags: list[str]) -> str:
    """The best flag among a system's records: evidence is the union of its sources (protocol 4.2)."""
    return max(flags, key=lambda f: CODABILITY_ORDER.get(f, 0), default="")


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
    # Name-based merging is deliberately weaker than repo-based merging, because it is transitive and
    # fuzzy name matching chains: no two of "RCI agent", "ACID-Agent", "AD-AGENT", "AI2Agent" match
    # each other directly (rciagent vs acidagent scores 82, under the 92 bar), but A-B, B-C, C-D links
    # pooled 129 records and 105 distinct names into one "system" row, which was then coded as if it
    # were one harness. Two rules stop that:
    #   1. a name similarity never merges records with different known repositories - protocol 4.4
    #      already treats a fork or re-implementation as a separate system;
    #   2. where a repository is missing on either side there is nothing to corroborate the name, so
    #      the normalised keys must be EQUAL, not merely similar.
    # The cost is under-merging: one system described under two spellings with no repository on either
    # side now yields two rows. That is the safe direction to be wrong in - a duplicate row is
    # detectable later from its repo or DOI, whereas a pooled row destroys the unit of analysis.
    for i in range(n):
        for j in range(i + 1, n):
            if not (base[i][0] and base[j][0]):
                continue
            ri, rj = rkeys[i], rkeys[j]
            if ri and rj:
                continue  # both repos known: the repo pass already decided, either way
            if key_of(base[i][0]) != key_of(base[j][0]):
                continue
            if letter_tail_conflict(base[i][0], base[j][0]):
                continue  # "Agent S" is not "Agents"; see letter_tail_conflict
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
                "codability_flag": best_codability_flag([recs[i].get("codability_flag_computed") or recs[i].get("codability_flag") or "" for i in idx]),
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
# Coding frame (Amendment 5 iii)
# --------------------------------------------------------------------------------------

#: repository owners that are a major lab or a vendor shipping a documented product
VENDOR_OWNERS = {
    "openai", "anthropics", "anthropic", "google", "google-deepmind", "google-research", "googleapis", "deepmind",
    "microsoft", "azure", "meta-llama", "facebookresearch", "amazon", "amazon-science", "awslabs", "aws-samples",
    "nvidia", "ibm", "ibm-granite", "salesforce", "salesforceairesearch", "huggingface", "alibaba", "alibaba-nlp",
    "qwenlm", "bytedance", "bytedance-seed", "tencent", "baidu", "deepseek-ai", "mistralai", "cohere-ai", "xai-org",
    "all-hands-ai", "cognition-ai", "cursor", "replit", "sourcegraph", "sweep-ai", "codeium", "continuedev",
    "block", "stripe", "cloudflare", "atlassian", "jetbrains", "gitlab-org", "github", "vercel", "langchain-ai",
    "llamaindex", "run-llama", "crewaiinc", "modelscope", "smol-ai", "openbmb", "servicenow", "sierra-research",
}
PREPRINT_VENUE_RE = re.compile(
    r"arxiv|zenodo|ssrn|preprint|research\s*square|techrxiv|biorxiv|medrxiv|osf|hal\b|github|awesome|"
    r"submitted to|withdrawn|reject|desk", re.IGNORECASE)
ACCEPTED_OPENREVIEW_RE = re.compile(r"poster|oral|spotlight|accept|proceedings|camera", re.IGNORECASE)
CATALOGUE_SOURCES = {"awesome", "leaderboard", "survey_refs"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


@dataclass
class FrameData:
    stars: dict[str, int] = field(default_factory=dict)        # repo key -> stars at freeze
    catalogue_repos: set[str] = field(default_factory=set)     # repo keys named by a catalogue / leaderboard
    catalogue_names: set[str] = field(default_factory=set)     # name keys named by a catalogue / leaderboard
    vendor_records: set[str] = field(default_factory=set)      # record ids of vendor documentation


def load_frame_data(repo_index: Path = REPO_INDEX, raw: Path = RAW, validation: Path = VALIDATION) -> FrameData:
    """Star counts and prior catalogues, from the frozen search harvest and the repository fetch."""
    d = FrameData()
    for r in read_csv(repo_index):
        k = repo_key(r.get("repo_url") or "")
        if k and (r.get("stars") or "").isdigit():
            d.stars[k] = max(d.stars.get(k, 0), int(r["stars"]))
    for row in read_jsonl(raw / "github.jsonl"):
        extra = row.get("extra")
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except json.JSONDecodeError:
                extra = {}
        k = repo_key(row.get("url") or "")
        stars = int((extra or {}).get("stars") or 0)
        if k and stars:
            d.stars[k] = max(d.stars.get(k, 0), stars)
    # curated catalogues (awesome lists) and tracked leaderboards name systems; the survey
    # reference harvest names papers, so those records enter through their candidate source instead
    for name in ("awesome.jsonl", "leaderboards.jsonl"):
        for row in read_jsonl(raw / name):
            k = repo_key(row.get("url") or "")
            if k:
                d.catalogue_repos.add(k)
            title = str(row.get("title") or "")
            nk = key_of(title.rsplit("/", 1)[-1] if "/" in title else title)
            if 3 <= len(nk) <= 40 and re.search(r"[a-z]{3}", nk):
                d.catalogue_names.add(nk)
    for r in read_csv(validation):  # the reference set is drawn from Li, Meng, Rombaut and Barbaste
        for u in (r.get("repo_url") or "").split(";"):
            if (k := repo_key(u)):
                d.catalogue_repos.add(k)
        for n in [r.get("name") or "", *((r.get("aliases") or "").split(";"))]:
            if (nk := key_of(n)):
                d.catalogue_names.add(nk)
    for row in read_jsonl(raw / "grey.jsonl"):
        if "vendor" in str(row.get("venue") or "").lower() and row.get("id"):
            d.vendor_records.add(str(row["id"]))
    return d


def catalogued(name_keys: set[str], repos: set[str], d: FrameData) -> bool:
    if repos & d.catalogue_repos:
        return True
    if name_keys & d.catalogue_names:
        return True
    long_keys = [k for k in name_keys if len(k) > SHORT_NAME]
    return any(keys_match(k, c, NAME_THRESHOLD) for k in long_keys for c in d.catalogue_names if abs(len(c) - len(k)) <= 3)


def frame_flags(srow: dict[str, Any], members: list[dict[str, str]], cands: dict[str, dict[str, str]], d: FrameData) -> dict[str, Any]:
    """The four Amendment 5 coding-frame criteria for one system row."""
    repos = {k for k in (repo_key(srow.get("repo_url") or ""), *(repo_key(m.get("repo_url") or "") for m in members)) if k}
    repos |= {k for m in members if (k := repo_key(m.get("repo_bundle_url") or ""))}
    stars = max([d.stars.get(k, 0) for k in repos] + [int(m["repo_bundle_stars"]) for m in members
                                                      if (m.get("repo_bundle_stars") or "").isdigit()] + [0])
    name_keys = {k for n in [srow.get("name") or "", *((srow.get("name_variants") or "").split(";"))] if (k := key_of(n))}
    member_ids = [m["record_id"] for m in members]
    sources = {(cands.get(rid, {}).get("source") or "") for rid in member_ids}
    venues = [(cands.get(rid, {}).get("venue") or "") for rid in member_ids]

    f_stars = stars >= FRAME_MIN_STARS
    f_cat = bool(sources & CATALOGUE_SOURCES) or catalogued(name_keys, repos, d)
    f_vendor = bool(set(member_ids) & d.vendor_records) or any(k.split("/")[1] in VENDOR_OWNERS for k in repos if "/" in k)
    def peer_reviewed(rid: str, ven: str) -> bool:
        src = cands.get(rid, {}).get("source") or ""
        if src == "acl":  # the ACL Anthology is peer-reviewed by construction
            return True
        if not ven or PREPRINT_VENUE_RE.search(ven):
            return False
        if src == "openreview":
            return bool(ACCEPTED_OPENREVIEW_RE.search(ven))
        return src not in ("github", "awesome", "leaderboard", "grey")

    f_peer = any(peer_reviewed(rid, ven) for rid, ven in zip(member_ids, venues, strict=True)) and bool(repos)
    reasons = [n for n, ok in (("stars", f_stars), ("catalogue", f_cat), ("vendor", f_vendor), ("peer_reviewed", f_peer)) if ok]
    return {"stars": stars or "", "frame_stars": int(f_stars), "frame_catalogue": int(f_cat), "frame_vendor": int(f_vendor),
            "frame_peer_reviewed": int(f_peer), "in_frame": int(bool(reasons)), "frame_reason": ";".join(reasons)}


def mark_frame(systems: list[dict[str, Any]], recs: list[dict[str, str]], cands: dict[str, dict[str, str]],
               d: FrameData | None = None, sample_n: int = FRAME_SAMPLE_N, seed: int = FRAME_SAMPLE_SEED) -> list[dict[str, Any]]:
    """Add the coding-frame columns and draw the out-of-frame sample (in place; returns ``systems``)."""
    d = d or load_frame_data()
    by_id = {r["record_id"]: r for r in recs}
    for s in systems:
        members = [by_id[rid] for rid in s["member_record_ids"].split(";") if rid in by_id]
        s.update(frame_flags(s, members, cands, d))
        s["frame_sample"] = 0
    outside = sorted((s for s in systems if not s["in_frame"]), key=lambda s: sample_hash(s["system_id"], seed))
    for s in outside[:sample_n]:
        s["frame_sample"] = 1
    return systems


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
    p.add_argument("--votes", "--pass1", dest="votes", default=str(PASS1), help="pass-1 votes (default fulltext_votes_v2.csv)")
    p.add_argument("--pass2", default=str(PASS2))
    p.add_argument("--ids", default=None, help="restrict to the record_ids of this CSV (e.g. the pilot)")
    p.add_argument("--disputed", choices=("hold", "include", "exclude"), default="hold")
    p.add_argument("--no-frame", action="store_true", help="skip the Amendment 5 coding-frame columns")
    p.add_argument("--systems-out", default=str(SYSTEMS))
    p.add_argument("--final-out", default=str(FINAL))
    args = p.parse_args(argv)

    p1, p2 = read_csv(Path(args.votes)), read_csv(Path(args.pass2))
    if args.ids:
        keep = {r["record_id"] for r in read_csv(Path(args.ids))}
        p1 = [r for r in p1 if r["record_id"] in keep]
        p2 = [r for r in p2 if r["record_id"] in keep]
    if not p1:
        print(f"no pass-1 votes in {args.votes}", file=sys.stderr)
        return 2
    cands = {r["id"]: r for r in read_csv(CANDIDATES)}
    reg, final = combine(p1, p2, args.disputed)
    systems = group_records(reg, cands)
    if not args.no_frame:
        mark_frame(systems, reg, cands)
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
               "in_frame": sum(int(s.get("in_frame") or 0) for s in systems),
               "frame_reasons": dict(Counter(x for s in systems for x in (s.get("frame_reason") or "").split(";") if x)),
               "frame_sample": sum(int(s.get("frame_sample") or 0) for s in systems),
               "codability_flag": dict(Counter(s.get("codability_flag") or "-" for s in systems)),
               "systems_out": args.systems_out, "final_out": args.final_out}
    print("SUMMARY " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
