#!/usr/bin/env python
"""Fetch the repository half of the evidence bundle (protocol Amendment 5, no LLM).

Amendment 5 reads a record as an EVIDENCE BUNDLE: the paper, the repository at its pinned
reference, and official documentation. ``scripts/fetch_fulltext.py`` fetches one document per
record (usually the paper PDF); this script adds the repository for every record whose document
was not itself a repository, so that codability and the implementation-bearing steps of the
decision procedure are judged on code, not on prose about code.

For each record with an ``ok`` full text in ``data/screening/fulltext_index.csv``:

1. Candidates. Every ``github.com/<owner>/<repo>`` in the fetched text, plus the candidate's own
   ``url`` in ``data/raw/candidates.csv``.
2. Scoring. Frequency in the text, a bonus for appearing next to a release phrase ("code is
   available", "we release", "implementation", ...), for standing early in the document (where a
   paper links its own code), for being the candidate's own URL and for a repository name that
   matches the document title. Obvious non-project repositories are dropped: GitHub's own paths,
   ``awesome-*``, paper/reading lists, ``.github``, project pages (``*.github.io``), docs-only
   repositories, and ``*-data`` / ``*-bench`` benchmark-data repositories unless one of those is
   the only hit. Below a score of 7 nothing is attached (wrong repository evidence is worse than
   none: a paper's evaluation section cites many repositories that are not its own). A document
   that links only a GitHub Pages project page is resolved through that owner's repository list,
   keeping a repository whose name matches the title.
3. Pin (protocol 4.5). ``gh api repos/<o>/<r>`` for stars, default branch, ``pushed_at``,
   license and archived flag; the last tag dated on or before 2026-08-31 (GraphQL, tagger date
   for annotated tags), falling back to the last default-branch commit before that date.
4. Clone. Shallow (``--depth 1``), blobless (``--filter=blob:none``), no checkout: the bundle's
   files are read out of the object store with ``git cat-file --batch``, so no working tree is
   written (Windows-invalid paths elsewhere in the tree cannot break the read). Cache:
   ``data/raw/cache/repos/<owner>__<repo>``, shared with ``fetch_fulltext.py``; an existing clone
   is reused and never deleted (that script may be running) and clones are sequential. When the
   API does not know the repository (a renamed owner: ``noahshinn024/reflexion``) git still
   redirects, so a full-history blobless clone is made and pinned with ``rev-list --before``.
5. Bundle. ``data/fulltext/<safe id>__repo.txt``: header (record_id, repo url, ref, stars,
   fetched_at, license, archived), README (first 30,000 chars), ``docs/**/*.md(x)`` up to 20,000
   chars, the file tree (paths only, first 500), and the first 200 lines of up to 8 files whose
   path matches ``(agent|loop|runner|executor|tool|prompt|config|sandbox|session|memory)``
   ``\\.(py|ts|js|go|rs)`` - the files that carry the evidence for layers A-H.

Appends one row per record to ``data/screening/repo_index.csv`` (record_id, repo_url, ref, stars,
archived, license, bundle_chars, status, reason_if_skipped). Resumable: records already in that
file are skipped. GitHub API calls are rate-limited to ~1/s across all workers.

Usage:
    python scripts/fetch_repos.py --ids-file data/screening/fulltext_pilot.csv
    python scripts/fetch_repos.py --limit 200 --workers 4
    python scripts/fetch_repos.py --dry-run --ids-file data/screening/fulltext_pilot.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

REPO = Path(__file__).resolve().parents[1]
SCREEN_DIR = REPO / "data" / "screening"
FULLTEXT_DIR = REPO / "data" / "fulltext"
INDEX = SCREEN_DIR / "fulltext_index.csv"
OUT_INDEX = SCREEN_DIR / "repo_index.csv"
CANDIDATES = REPO / "data" / "raw" / "candidates.csv"
REPO_CACHE = REPO / "data" / "raw" / "cache" / "repos"

CUTOFF_DATE = "2026-08-31"  # protocol 4.5 version cutoff
CUTOFF_TS = f"{CUTOFF_DATE}T23:59:59Z"
README_CAP = 30_000
DOCS_CAP = 20_000
TREE_CAP = 500
CODE_FILES = 8
CODE_LINES = 200
CODE_FILE_CAP = 20_000  # chars per code file, a guard against minified or generated files
GH_MIN_INTERVAL = 1.0  # seconds between GitHub API calls, across all workers

COLUMNS = ["record_id", "repo_url", "ref", "stars", "archived", "license", "bundle_chars", "status", "reason_if_skipped"]

log = logging.getLogger("fetch_repos")


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_id(record_id: str) -> str:
    """File-system-safe id, identical to ``fetch_fulltext.safe_id``."""
    s = re.sub(r"[:/\\]", "__", record_id)
    return re.sub(r'[<>"|?*\x00-\x1f]', "_", s)


def bundle_path(record_id: str, root: Path = FULLTEXT_DIR) -> Path:
    return root / f"{safe_id(record_id)}__repo.txt"


def fulltext_path(record_id: str, root: Path = FULLTEXT_DIR) -> Path:
    return root / f"{safe_id(record_id)}.txt"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    csv.field_size_limit(10**8)
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def key_of(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


class RateLimiter:
    """At most one call per ``interval`` seconds, across threads."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._next - now
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
            self._next = now + self.interval


class GhError(RuntimeError):
    pass


# --------------------------------------------------------------------------------------
# Repository candidates in a document
# --------------------------------------------------------------------------------------

GITHUB_RE = re.compile(r"github\.com/([\w.-]+)/([\w.-]+)", re.IGNORECASE)
#: the same URL with the whitespace a PDF extractor leaves inside it ("github. com/ owner/ repo")
GITHUB_LOOSE_RE = re.compile(r"github\s*\.\s*com\s*/\s*([\w.-]+)\s*/\s*([\w.-]+)", re.IGNORECASE)
#: a GitHub Pages project page: the owner is real, the repository name is not in the URL
GITHUB_IO_RE = re.compile(r"(?<![\w.-])([\w-]+)\.github\.io", re.IGNORECASE)
#: "our code is available at <url>" - the phrasing that marks a project's own repository
STRONG_RELEASE_RE = re.compile(
    r"(code(?:\s+and\s+\w+)?\s*(?:is|are)?\s*(?:publicly\s+)?(?:available|released|at)|we\s+(?:release|open[- ]sourced?)|"
    r"released\s+at|available\s+at|our\s+code|code(?:\s+and\s+\w+)?\s*:|(?:code|github|project)\s+repository|"
    r"artifacts?\s+(?:is|are)\s+available|project\s+(?:page|website))",
    re.IGNORECASE,
)
#: weaker company that a repository URL keeps in any related-work or evaluation paragraph
WEAK_RELEASE_RE = re.compile(r"(implementation|open[- ]source|reproduc|built\s+on|based\s+on)", re.IGNORECASE)
NEAR_BEFORE, NEAR_AFTER = 220, 140
EARLY_CHARS = 4000  # abstract, title footnote and introduction: where a paper links its own code
MIN_SCORE = 7.0  # below this the best candidate is not attached: no evidence beats wrong evidence

#: GitHub's own paths, never a project repository.
RESERVED_OWNERS = {
    "about", "account", "apps", "blog", "collections", "contact", "customer-stories", "dashboard", "enterprise",
    "events", "explore", "features", "issues", "join", "login", "logos", "marketplace", "mobile", "new",
    "notifications", "orgs", "pricing", "pulls", "readme", "search", "security", "sessions", "settings", "site",
    "sponsors", "stars", "topics", "trending", "user-attachments", "users", "watching",
}
#: repository names that are infrastructure, not a project
RESERVED_REPOS = {".github", "gist", "issues", "pulls", "raw", "releases", "wiki"}

HARD_DROP = [
    (re.compile(r"^awesome([-_]|$)|[-_]awesome[-_]|^awsome", re.IGNORECASE), "awesome_list"),
    (re.compile(r"(^|[-_])(papers?|paper[-_]?list|reading[-_]?list|paper[-_]?notes|literature|bibliography)([-_]|$)", re.IGNORECASE), "paper_list"),
    (re.compile(r"^\.github$", re.IGNORECASE), "dot_github"),
]
SOFT_DROP = [
    (re.compile(r"\.github\.io$", re.IGNORECASE), "project_page"),
    (re.compile(r"(^|[-_])(docs?|documentation|website|webpage|homepage|blog|slides|template|tutorials?)([-_]|$)", re.IGNORECASE), "docs_only"),
    (re.compile(r"[-_](data|dataset|datasets|bench|benchmark|benchmarks|eval|evals|evaluation|leaderboard)$", re.IGNORECASE), "benchmark_data"),
]


@dataclass
class RepoHit:
    owner: str
    repo: str
    freq: int = 0
    strong_release: bool = False
    weak_release: bool = False
    from_url: bool = False
    title_match: bool = False
    early: bool = False
    first_pos: int = 10**9
    soft: str = ""
    only_hit: bool = False
    via: str = "text"

    @property
    def full(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def key(self) -> str:
        return self.full.lower()

    @property
    def score(self) -> float:
        s = 2.0 * min(self.freq, 8)
        s += 6.0 if self.strong_release else (2.0 if self.weak_release else 0.0)
        s += 12.0 if self.from_url else 0.0
        s += 5.0 if self.title_match else 0.0
        s += 3.0 if self.early else 0.0
        s -= 0.0 if (self.only_hit or not self.soft) else 4.0  # a soft drop only loses when there is an alternative
        return s

    def why(self) -> str:
        bits = [f"freq={self.freq}", f"score={self.score:.0f}"]
        if self.via != "text":
            bits.append(self.via)
        if self.from_url:
            bits.append("candidate_url")
        if self.strong_release:
            bits.append("near_release_phrase")
        elif self.weak_release:
            bits.append("near_weak_phrase")
        if self.title_match:
            bits.append("name_matches_title")
        if self.early:
            bits.append("early_in_document")
        if self.soft:
            bits.append(f"soft:{self.soft}" + (",only_hit" if self.only_hit else ""))
        return ",".join(bits)


def clean_repo_name(repo: str) -> str:
    r = repo.strip().strip("().,;:'\"")
    r = re.sub(r"\.git$", "", r, flags=re.IGNORECASE)
    return r.strip(".,;:")


def classify(owner: str, repo: str) -> tuple[str, str]:
    """('', '') to keep; ('hard'|'soft', reason) otherwise."""
    if owner.lower() in RESERVED_OWNERS or repo.lower() in RESERVED_REPOS:
        return "hard", "github_reserved_path"
    for pat, reason in HARD_DROP:
        if pat.search(repo):
            return "hard", reason
    for pat, reason in SOFT_DROP:
        if pat.search(repo):
            return "soft", reason
    return "", ""


def repo_from_url(url: str) -> tuple[str, str] | None:
    m = GITHUB_RE.search(url or "")
    if not m:
        return None
    repo = clean_repo_name(m.group(2))
    return (m.group(1), repo) if repo else None


def find_repos(text: str, cand_url: str = "", title: str = "") -> list[RepoHit]:
    """Scored repository candidates for one document, best first."""
    text = text or ""
    hits: dict[str, RepoHit] = {}

    def add(owner: str, repo: str, pos: int, strong: bool, weak: bool, from_url: bool) -> None:
        repo = clean_repo_name(repo)
        if not repo or not owner:
            return
        kind, reason = classify(owner, repo)
        if kind == "hard":
            return
        h = hits.get(f"{owner}/{repo}".lower())
        if h is None:
            h = RepoHit(owner, repo, soft=reason if kind == "soft" else "")
            hits[h.key] = h
        h.freq += 0 if from_url else 1
        h.strong_release = h.strong_release or strong
        h.weak_release = h.weak_release or weak
        h.from_url = h.from_url or from_url
        h.early = h.early or (not from_url and pos < EARLY_CHARS)
        h.first_pos = min(h.first_pos, pos)

    spans: list[tuple[int, str, str]] = [(m.start(), m.group(1), m.group(2)) for m in GITHUB_RE.finditer(text)]
    if not spans:  # PDF extraction that split the URL over a line break
        spans = [(m.start(), m.group(1), m.group(2)) for m in GITHUB_LOOSE_RE.finditer(text)]
    for pos, owner, repo in spans:
        window = text[max(0, pos - NEAR_BEFORE) : pos + NEAR_AFTER]
        add(owner, repo, pos, bool(STRONG_RELEASE_RE.search(window)), bool(WEAK_RELEASE_RE.search(window)), False)
    own = repo_from_url(cand_url)
    if own:
        add(own[0], own[1], 0, False, False, True)

    tkey = key_of(title)
    for h in hits.values():
        rkey = key_of(h.repo)
        if len(rkey) >= 4 and tkey and (rkey in tkey or fuzz.partial_ratio(rkey, tkey) >= 92):
            h.title_match = True
    if len(hits) == 1:
        next(iter(hits.values())).only_hit = True
    return sorted(hits.values(), key=lambda h: (-h.score, h.first_pos, h.key))


def io_owners(text: str) -> list[str]:
    """Owners of the GitHub Pages project pages a document links (``os-copilot.github.io``)."""
    seen = Counter(m.group(1).lower() for m in GITHUB_IO_RE.finditer(text or ""))
    return [o for o, _ in seen.most_common() if o not in {"www", "pages"}]


# --------------------------------------------------------------------------------------
# GitHub API and clones
# --------------------------------------------------------------------------------------

TAGS_QUERY = (
    'query($o:String!,$r:String!,$c:String){repository(owner:$o,name:$r){'
    'refs(refPrefix:"refs/tags/",first:100,after:$c,orderBy:{field:TAG_COMMIT_DATE,direction:DESC}){'
    "pageInfo{hasNextPage endCursor}nodes{name target{__typename oid ... on Commit{committedDate} "
    "... on Tag{tagger{date} target{__typename oid ... on Commit{committedDate}}}}}}}}"
)


@dataclass
class RepoMeta:
    full: str
    stars: int = 0
    archived: bool = False
    license: str = ""
    default_branch: str = "main"
    pushed_at: str = ""
    ref: str = ""
    sha: str = ""
    ref_date: str = ""
    error: str = ""


class Gh:
    def __init__(self, exe: str, dry_run: bool = False) -> None:
        self.exe = exe
        self.dry_run = dry_run
        self.limiter = RateLimiter(GH_MIN_INTERVAL)
        self.clone_lock = threading.Lock()
        self.env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}

    # ---- API ----
    def api(self, args: list[str]) -> Any:
        last = ""
        for attempt in range(4):
            self.limiter.wait()
            try:
                proc = subprocess.run([self.exe, "api", *args], capture_output=True, timeout=120, env=self.env, check=False)
            except subprocess.TimeoutExpired:
                last = "gh api timeout"
                continue
            if proc.returncode == 0:
                return json.loads(proc.stdout.decode("utf-8", "replace") or "null")
            last = proc.stderr.decode("utf-8", "replace").strip()[:200]
            if "HTTP 404" in last or "Not Found" in last or "HTTP 451" in last or "HTTP 403" in last and "rate limit" not in last.lower():
                raise GhError(last)
            if "rate limit" in last.lower() or "HTTP 5" in last:
                time.sleep(20 * (attempt + 1))
                continue
            break
        raise GhError(last or "gh api failed")

    def latest_tag(self, owner: str, repo: str) -> tuple[str, str, str] | None:
        """(tag, sha, date) of the newest tag dated on or before the cutoff."""
        cursor: str | None = None
        best: tuple[str, str, str] | None = None
        for _page in range(10):
            args = ["graphql", "-f", f"query={TAGS_QUERY}", "-F", f"o={owner}", "-F", f"r={repo}"]
            if cursor:
                args += ["-F", f"c={cursor}"]
            data = self.api(args)
            refs = (((data or {}).get("data") or {}).get("repository") or {}).get("refs") or {}
            for node in refs.get("nodes") or []:
                tgt = node.get("target") or {}
                if tgt.get("__typename") == "Commit":
                    sha, date = tgt.get("oid"), tgt.get("committedDate")
                elif tgt.get("__typename") == "Tag":
                    inner = tgt.get("target") or {}
                    if inner.get("__typename") != "Commit":
                        continue
                    sha = inner.get("oid")
                    date = (tgt.get("tagger") or {}).get("date") or inner.get("committedDate")
                else:
                    continue
                if sha and date and date[:10] <= CUTOFF_DATE and (best is None or date > best[2]):
                    best = (node["name"], sha, date)
            if best is not None:
                return best
            info = refs.get("pageInfo") or {}
            if not info.get("hasNextPage"):
                return None
            cursor = info.get("endCursor")
        return best

    def meta(self, owner: str, repo: str) -> RepoMeta:
        info = self.api([f"repos/{owner}/{repo}"])
        full = info.get("full_name") or f"{owner}/{repo}"
        m = RepoMeta(
            full=full,
            stars=int(info.get("stargazers_count") or 0),
            archived=bool(info.get("archived")),
            license=((info.get("license") or {}) or {}).get("spdx_id") or "",
            default_branch=info.get("default_branch") or "main",
            pushed_at=(info.get("pushed_at") or "")[:10],
        )
        o, r = full.split("/", 1)
        tag = self.latest_tag(o, r)
        if tag:
            m.ref, m.sha, m.ref_date = f"tag:{tag[0]}", tag[1], tag[2][:10]
            return m
        commits = self.api([f"repos/{full}/commits?sha={m.default_branch}&until={CUTOFF_TS}&per_page=1"])
        if not commits:
            raise GhError(f"no tag and no commit on {m.default_branch} on or before {CUTOFF_DATE}")
        m.sha = commits[0]["sha"]
        m.ref_date = (((commits[0].get("commit") or {}).get("committer") or {}).get("date") or "")[:10]
        m.ref = f"commit:{m.default_branch}"
        return m

    # ---- git ----
    def git(self, *args: str, cwd: Path | None = None, timeout: int = 900) -> str:
        cmd = ["git", "-c", "core.longpaths=true", "-c", "advice.detachedHead=false", "-c", "core.quotePath=false"]
        if cwd is not None:
            cmd += ["-C", str(cwd)]
        proc = subprocess.run([*cmd, *args], capture_output=True, timeout=timeout, env=self.env, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"git {args[0]}: {proc.stderr.decode('utf-8', 'replace')[-300:]}")
        return proc.stdout.decode("utf-8", "replace")

    def head_of(self, dest: Path) -> str:
        try:
            return self.git("rev-parse", "HEAD", cwd=dest).strip()
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            return ""

    def clone(self, meta: RepoMeta) -> tuple[Path, str]:
        """Clone (or reuse) the repository at its pinned reference; returns (path, head sha).

        The cache is shared with ``fetch_fulltext.py``, which may be running: an existing clone is
        reused as it is and never deleted, and a fresh clone is built in a temporary directory and
        renamed into place."""
        dest = REPO_CACHE / meta.full.replace("/", "__")
        with self.clone_lock:
            head = self.head_of(dest) if dest.exists() else ""
            if head:
                return dest, head
            REPO_CACHE.mkdir(parents=True, exist_ok=True)
            tmp = REPO_CACHE / f".tmp_{os.getpid()}_{abs(hash(meta.full)) % 10**6}"
            _rmtree(tmp)
            url = f"https://github.com/{meta.full}.git"
            tag = meta.ref.split("tag:", 1)[1] if meta.ref.startswith("tag:") else ""
            try:
                if tag:
                    self.git("clone", "-q", "--depth", "1", "--branch", tag, "--filter=blob:none", "--no-checkout", url, str(tmp))
                else:
                    self.git("init", "-q", str(tmp))
                    self.git("remote", "add", "origin", url, cwd=tmp)
                    self.git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", meta.sha, cwd=tmp)
                    self.git("update-ref", "--no-deref", "HEAD", meta.sha, cwd=tmp)
                head = self.head_of(tmp)
                if not head:
                    raise RuntimeError("clone produced no HEAD")
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                _rmtree(tmp)
                raise
            if dest.exists():  # another process got there first
                other = self.head_of(dest)
                if other:
                    _rmtree(tmp)
                    return dest, other
                _rmtree(tmp)
                raise RuntimeError(f"{dest.name} exists but has no HEAD (another fetch in progress?)")
            try:
                tmp.rename(dest)
            except OSError:
                return tmp, head
            return dest, head

    def clone_history(self, full: str) -> tuple[Path, str, str]:
        """Blobless clone with full commit history, used when the API does not know the
        repository (a renamed owner still redirects over git). Returns (path, sha, date) of the
        last commit on or before the cutoff (protocol 4.5)."""
        dest = REPO_CACHE / full.replace("/", "__")
        with self.clone_lock:
            if not dest.exists() or not self.head_of(dest):
                REPO_CACHE.mkdir(parents=True, exist_ok=True)
                tmp = REPO_CACHE / f".tmp_{os.getpid()}_{abs(hash(full)) % 10**6}"
                _rmtree(tmp)
                try:
                    self.git("clone", "-q", "--filter=blob:none", "--no-checkout", f"https://github.com/{full}.git", str(tmp))
                except (RuntimeError, OSError, subprocess.TimeoutExpired):
                    _rmtree(tmp)
                    raise
                if dest.exists():
                    _rmtree(tmp)
                else:
                    tmp.rename(dest)
            sha = self.git("rev-list", "-1", f"--before={CUTOFF_TS}", "HEAD", cwd=dest).strip()
            if not sha:
                raise RuntimeError(f"no commit on or before {CUTOFF_DATE}")
            date = self.git("show", "-s", "--format=%cI", sha, cwd=dest).strip()[:10]
        return dest, sha, date

    def rev_in(self, dest: Path, sha: str) -> str:
        """``sha`` when that commit is in the local clone, else HEAD (a clone made for another
        record is pinned to its own reference; the bundle records the one it actually read)."""
        if sha:
            try:
                self.git("cat-file", "-e", f"{sha}^{{commit}}", cwd=dest)
                return sha
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                pass
        return self.head_of(dest) or "HEAD"

    def cat_files(self, dest: Path, rev: str, paths: list[str]) -> dict[str, str]:
        """Read files out of the object store (``git cat-file --batch``) instead of checking them
        out: no worktree is touched (the cache is shared) and Windows-invalid paths in the tree
        cannot break the read."""
        if not paths:
            return {}
        cmd = ["git", "-C", str(dest), "-c", "core.longpaths=true", "cat-file", "--batch"]
        stdin = "\n".join(f"{rev}:{p}" for p in paths) + "\n"
        proc = subprocess.run(cmd, input=stdin.encode("utf-8"), capture_output=True, timeout=900, env=self.env, check=False)
        out, pos, res = proc.stdout, 0, {}
        for p in paths:
            nl = out.find(b"\n", pos)
            if nl < 0:
                break
            head = out[pos:nl].decode("utf-8", "replace")
            parts = head.split()
            if len(parts) != 3 or not parts[2].isdigit():  # "<oid> missing" / error line
                pos = nl + 1
                res[p] = ""
                continue
            size = int(parts[2])
            res[p] = out[nl + 1 : nl + 1 + size].decode("utf-8", "replace")
            pos = nl + 1 + size + 1
        return res


def _rmtree(path: Path) -> None:
    def onexc(func: Any, p: str, _exc: Any) -> None:
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if path.exists():
        shutil.rmtree(path, onexc=onexc)


# --------------------------------------------------------------------------------------
# The bundle
# --------------------------------------------------------------------------------------

CODE_KEYWORDS = ["agent", "loop", "runner", "executor", "sandbox", "session", "memory", "tool", "prompt", "config"]
CODE_RE = re.compile(rf"({'|'.join(CODE_KEYWORDS)})\.(py|ts|js|go|rs)$", re.IGNORECASE)
CODE_PATH_RE = re.compile(rf"({'|'.join(CODE_KEYWORDS)})\.(py|ts|js|go|rs)", re.IGNORECASE)
SKIP_PATH_RE = re.compile(
    r"(^|/)(tests?|testing|node_modules|vendor|third_party|3rdparty|examples?|samples?|fixtures?|dist|build|"
    r"site-packages|\.venv|venv|migrations|\.git)(/|$)|(^|/)(test_[^/]*|[^/]*_test|[^/]*\.min)\.(py|ts|js|go|rs)$",
    re.IGNORECASE,
)


TREE_NOISE_RE = re.compile(
    r"(^|/)\.[^/]+/|(^|/)(node_modules|vendor|third_party|dist|build|site-packages|__pycache__)(/)|"
    r"\.(png|jpe?g|gif|svg|ico|webp|mp4|mov|pdf|zip|tar|gz|whl|so|dll|dylib|bin|pkl|pt|safetensors|lock|map)$|"
    r"(^|/)(package-lock\.json|yarn\.lock|poetry\.lock|uv\.lock|Cargo\.lock|go\.sum)$",
    re.IGNORECASE,
)


def interesting_paths(tree: list[str]) -> list[str]:
    """The file tree without the noise that would fill the 500-path budget (hidden directories,
    vendored trees, images, lock files)."""
    kept = [p for p in tree if not TREE_NOISE_RE.search(p)]
    return kept or tree


def select_code_files(tree: list[str], limit: int = CODE_FILES) -> list[str]:
    """Up to ``limit`` implementation files, spread across the keywords, shallowest first."""
    cands = [p for p in tree if CODE_PATH_RE.search(p) and not SKIP_PATH_RE.search(p)]

    side = re.compile(r"(^|/)(ext|extensions?|contrib|plugins?|integrations?|benchmarks?|scripts?|legacy)(/)", re.IGNORECASE)
    exact = re.compile(rf"(^|/)({'|'.join(CODE_KEYWORDS)})\.(py|ts|js|go|rs)$", re.IGNORECASE)

    def rank(p: str) -> tuple[Any, ...]:
        tier = 0 if exact.search(p) else (1 if CODE_RE.search(p) else 2)
        return (tier, 1 if side.search(p) else 0, p.count("/"), len(p), p.lower())

    by_kw: dict[str, list[str]] = {k: [] for k in CODE_KEYWORDS}
    for p in sorted(cands, key=rank):
        name = p.rsplit("/", 1)[-1].lower()
        for k in CODE_KEYWORDS:
            if k in name:
                by_kw[k].append(p)
                break
    out: list[str] = []
    while len(out) < limit:
        added = False
        for k in CODE_KEYWORDS:
            if by_kw[k] and len(out) < limit:
                p = by_kw[k].pop(0)
                if p not in out:
                    out.append(p)
                    added = True
        if not added:
            break
    return out


def _read(p: Path, cap: int = 0) -> str:
    try:
        return _clip(p.read_text(encoding="utf-8", errors="replace"), cap)
    except OSError:
        return ""


def _clip(text: str, cap: int = 0) -> str:
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    return t[:cap] if cap else t


def head_lines(text: str, n: int = CODE_LINES) -> str:
    lines = text.split("\n")
    out = "\n".join(lines[:n])
    return out + (f"\n[... {len(lines) - n} more lines]" if len(lines) > n else "")


def build_bundle(record_id: str, files: dict[str, str], meta: RepoMeta, head: str, tree: list[str], code_paths: list[str]) -> str:
    ref = f"{meta.ref} {head[:12]} {meta.ref_date}".strip()
    out = [
        f"record_id: {record_id}",
        f"repo_url: https://github.com/{meta.full}",
        f"ref: {ref}",
        f"stars: {meta.stars}",
        f"fetched_at: {now_utc()}",
        f"license: {meta.license}",
        f"archived: {str(meta.archived).lower()}",
        f"default_branch: {meta.default_branch}",
        f"pushed_at: {meta.pushed_at}",
        "",
        "This is REPOSITORY EVIDENCE for the record above, at the pinned reference (protocol 4.5).",
        "",
    ]
    readmes = sorted(
        (p for p in tree if "/" not in p and p.lower().startswith("readme")),
        key=lambda p: (not p.lower().endswith((".md", ".markdown")), p.lower() != "readme.md", len(p)),
    )
    if readmes:
        out += [f"## README ({readmes[0]})", _clip(files.get(readmes[0], ""), README_CAP), ""]
    docs = [p for p in tree if re.match(r"^docs?/.+\.mdx?$", p, re.IGNORECASE)]
    docs.sort(key=lambda p: (p.count("/"), not re.search(r"(index|readme|overview|intro|architecture|agent)", p, re.IGNORECASE), p.lower()))
    budget, parts = DOCS_CAP, []
    for p in docs:
        if budget <= 0:
            break
        body = _clip(files.get(p, ""))
        if not body.strip():
            continue
        chunk = f"### {p}\n{body}"[:budget]
        parts.append(chunk)
        budget -= len(chunk)
    if parts:
        out += [f"## docs (first {DOCS_CAP} chars of {len(docs)} files)", *parts, ""]
    code = []
    for p in code_paths:
        body = _clip(files.get(p, ""), CODE_FILE_CAP)
        if body.strip():
            code.append(f"### {p} (first {CODE_LINES} lines)\n{head_lines(body)}")
    if code:
        out += [f"## Code files ({len(code)} of {len(code_paths)} selected; layers A-H evidence)", *code, ""]
    shown = interesting_paths(tree)
    tree_head = (f"## File tree (first {min(TREE_CAP, len(shown))} of {len(shown)} source paths; {len(tree)} in the tree, "
                 "dot-directories, vendored trees, assets and lock files left out)")
    out += [tree_head, *shown[:TREE_CAP]]
    return "\n".join(out).strip() + "\n"


# --------------------------------------------------------------------------------------
# Per-record work
# --------------------------------------------------------------------------------------


@dataclass
class Target:
    record_id: str
    hits: list[RepoHit] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)  # github.io owners, tried when no hit is confident
    title: str = ""
    status: str = ""
    reason: str = ""

    @property
    def best(self) -> RepoHit | None:
        return self.hits[0] if self.hits else None

    @property
    def confident(self) -> bool:
        b = self.best
        return bool(b and (b.from_url or b.score >= MIN_SCORE))


def plan(record_ids: list[str], index: dict[str, dict[str, str]], cands: dict[str, dict[str, str]],
         fulltext_dir: Path) -> list[Target]:
    """Offline phase: which repository each record points at (no network)."""
    out = []
    for rid in record_ids:
        row = index.get(rid) or {}
        t = Target(rid)
        if (row.get("status") or "").lower() != "ok":
            t.status, t.reason = "skipped", "fulltext_not_ok"
            out.append(t)
            continue
        if (row.get("source_used") or "") == "github_repo":
            t.status, t.reason = "skipped", "evidence_already_repo"
            out.append(t)
            continue
        path = fulltext_path(rid, fulltext_dir)
        if not path.exists():
            t.status, t.reason = "skipped", "fulltext_file_missing"
            out.append(t)
            continue
        text = _read(path)
        cand = cands.get(rid, {})
        t.title = f"{row.get('fetched_title') or ''} {cand.get('title') or ''}"
        t.hits = find_repos(text, cand.get("url") or "", t.title)
        t.owners = io_owners(text)[:2] if not t.confident else []
        if not t.confident and not t.owners:
            best = t.best
            t.status = "skipped"
            t.reason = f"no_confident_repo (best {best.full} {best.why()})" if best else "no_repo_url_in_document"
        out.append(t)
    return out


def resolve_io_owner(gh: Gh, t: Target) -> RepoHit | None:
    """A project page (``os-copilot.github.io``) names the owner but not the repository: look the
    owner's repositories up and keep one whose name matches the document title."""
    tkey = key_of(t.title)
    for owner in t.owners:
        try:
            repos = gh.api([f"users/{owner}/repos?per_page=100&sort=updated"]) or []
        except (GhError, json.JSONDecodeError, TypeError):
            continue
        best: tuple[int, RepoHit] | None = None
        for r in repos if isinstance(repos, list) else []:
            name = str(r.get("name") or "")
            kind, _ = classify(owner, name)
            rkey = key_of(name)
            if kind or len(rkey) < 4 or not tkey or not (rkey in tkey or fuzz.partial_ratio(rkey, tkey) >= 92):
                continue
            hit = RepoHit(str(r.get("owner", {}).get("login") or owner), name, freq=1, title_match=True,
                          strong_release=True, via="github_io_owner")
            stars = int(r.get("stargazers_count") or 0)
            if best is None or stars > best[0]:
                best = (stars, hit)
        if best:
            return best[1]
    return None


def process(gh: Gh, t: Target, meta_cache: dict[str, Any], out_dir: Path) -> dict[str, str]:
    """Fetch metadata, clone and write the bundle for one record."""
    hit = t.best if t.confident else resolve_io_owner(gh, t)
    if hit is None:
        best = t.best
        reason = f"no_confident_repo (best {best.full} {best.why()})" if best else "no_repo_url_in_document"
        if t.owners:
            reason += f"; github.io owners {','.join(t.owners)} have no repository matching the title"
        return row_of(t.record_id, "", "", "", "", "", 0, "skipped", reason)
    key = hit.key
    lock: threading.Lock
    with meta_cache["lock"]:
        entry = meta_cache.setdefault(key, {"lock": threading.Lock(), "meta": None, "error": ""})
        lock = entry["lock"]
    with lock:
        if entry["meta"] is None and not entry["error"]:
            try:
                entry["meta"] = gh.meta(hit.owner, hit.repo)
            except (GhError, json.JSONDecodeError, KeyError) as exc:
                entry["error"] = str(exc)[:200]
                if "404" in entry["error"] or "Not Found" in entry["error"]:
                    # a renamed owner or repository: the API 404s but git still redirects
                    try:
                        dest, sha, date = gh.clone_history(hit.full)
                        entry["meta"] = RepoMeta(full=hit.full, sha=sha, ref_date=date, ref="commit:history",
                                                 error="api 404 (renamed?): stars and license unknown, pinned by commit date")
                        entry["error"] = ""
                    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc2:
                        entry["error"] = f"{entry['error']}; git fallback: {str(exc2)[:120]}"
    if entry["error"]:
        return row_of(t.record_id, f"https://github.com/{hit.full}", "", "", "", "", 0, "error", f"gh api: {entry['error']}")
    meta: RepoMeta = entry["meta"]
    try:
        dest, _head = gh.clone(meta)
        rev = gh.rev_in(dest, meta.sha)
        tree = [p for p in gh.git("ls-tree", "-r", "--name-only", rev, cwd=dest).splitlines() if p]
        code_paths = select_code_files(tree)
        readmes = [p for p in tree if "/" not in p and p.lower().startswith("readme")][:2]
        docs = [p for p in tree if re.match(r"^docs?/.+\.mdx?$", p, re.IGNORECASE)][:60]
        files = gh.cat_files(dest, rev, readmes + docs + code_paths)
        text = build_bundle(t.record_id, files, meta, rev, tree, code_paths)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        return row_of(t.record_id, f"https://github.com/{meta.full}", meta.ref, str(meta.stars), str(meta.archived).lower(),
                      meta.license, 0, "error", f"clone: {str(exc)[:200]}")
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path(t.record_id, out_dir).write_text(text, encoding="utf-8")
    reason = hit.why() + (f"; {meta.error}" if meta.error else "")
    return row_of(t.record_id, f"https://github.com/{meta.full}", f"{meta.ref} {rev[:12]} {meta.ref_date}".strip(),
                  str(meta.stars), str(meta.archived).lower(), meta.license, len(text), "ok", reason)


def row_of(rid: str, url: str, ref: str, stars: str, archived: str, lic: str, chars: int, status: str, reason: str) -> dict[str, str]:
    return {"record_id": rid, "repo_url": url, "ref": ref, "stars": stars, "archived": archived, "license": lic,
            "bundle_chars": str(chars), "status": status, "reason_if_skipped": reason}


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def find_gh() -> str:
    for cand in (os.environ.get("GH_EXE"), shutil.which("gh"), r"C:\Program Files\GitHub CLI\gh.exe"):
        if cand and Path(cand).exists():
            return str(cand)
    return ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--index", default=str(INDEX))
    p.add_argument("--ids-file", default=None, help="CSV with a record_id column restricting the input (e.g. data/screening/fulltext_pilot.csv)")
    p.add_argument("--out", default=str(OUT_INDEX))
    p.add_argument("--fulltext-dir", default=str(FULLTEXT_DIR))
    p.add_argument("--limit", type=int, default=0, help="stop after N records that need a repository fetch (0 = all)")
    p.add_argument("--workers", type=int, default=4, help="parallel GitHub API calls (clones stay sequential)")
    p.add_argument("--redo", action="store_true", help="re-fetch records already in the output index")
    p.add_argument("--dry-run", action="store_true", help="plan only: print the chosen repositories, no API calls, no clones")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    index = {r["record_id"]: r for r in read_csv(Path(args.index)) if r.get("record_id")}
    if not index:
        print(f"{args.index} is missing or empty: run scripts/fetch_fulltext.py first", file=sys.stderr)
        return 2
    cands = {r["id"]: r for r in read_csv(CANDIDATES)}
    if args.ids_file:
        ids = [r["record_id"] for r in read_csv(Path(args.ids_file)) if r.get("record_id")]
    else:
        ids = [rid for rid, r in index.items() if (r.get("status") or "").lower() == "ok"]
    out_path = Path(args.out)
    done = {r["record_id"] for r in read_csv(out_path)} if not args.redo else set()
    todo_ids = [r for r in dict.fromkeys(ids) if r not in done]
    fulltext_dir = Path(args.fulltext_dir)
    targets = plan(todo_ids, index, cands, fulltext_dir)
    work = [t for t in targets if not t.status]
    skipped = [t for t in targets if t.status]
    if args.limit:
        work = work[: args.limit]
    log.info("input %d records (%d already in %s): %d to fetch, %d skipped (%s)", len(ids), len(done), out_path.name,
             len(work), len(skipped), dict(Counter(t.reason.split(" (")[0] for t in skipped)))
    if args.dry_run:
        for t in work[:80]:
            h = t.best
            chosen = f"{h.full}\t{h.why()}" if t.confident else f"(github.io owners: {','.join(t.owners)})\t-"
            print(f"{t.record_id}\t{chosen}\t" + ", ".join(f"{x.full}({x.score:.0f})" for x in t.hits[:4]))
        print("SUMMARY " + json.dumps({"to_fetch": len(work), "confident": sum(t.confident for t in work),
                                       "github_io_lookup": sum(not t.confident for t in work),
                                       "skipped": dict(Counter(t.reason.split(" (")[0] for t in skipped)),
                                       "distinct_repos": len({t.best.key for t in work if t.confident})}))
        return 0

    exe = find_gh()
    if work and not exe:
        print("GitHub CLI not found (set GH_EXE or put 'gh' on PATH).", file=sys.stderr)
        return 2
    gh = Gh(exe)
    meta_cache: dict[str, Any] = {"lock": threading.Lock()}
    new_file = not out_path.exists() or out_path.stat().st_size == 0
    fh = out_path.open("a", encoding="utf-8", newline="")
    w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
    if new_file:
        w.writeheader()
    for t in skipped:
        w.writerow(row_of(t.record_id, "", "", "", "", "", 0, "skipped", t.reason))
    fh.flush()

    rows: list[dict[str, str]] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = {pool.submit(process, gh, t, meta_cache, fulltext_dir): t for t in work}
        for k, fut in enumerate(as_completed(futs), 1):
            t = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:  # noqa: BLE001 - one bad record must not stop the run
                log.error("%s: %s: %s", t.record_id, type(exc).__name__, str(exc)[:300])
                row = row_of(t.record_id, f"https://github.com/{t.best.full}" if t.best else "", "", "", "", "", 0,
                             "error", f"{type(exc).__name__}: {str(exc)[:160]}")
            rows.append(row)
            w.writerow(row)
            fh.flush()
            if k % 10 == 0 or k == len(work):
                log.info("%d/%d records, %.0fs elapsed", k, len(work), time.time() - t0)
    fh.close()
    stars = sorted(int(r["stars"]) for r in rows if r["status"] == "ok" and r["stars"].isdigit())
    summary = {
        "records_in": len(ids), "fetched_now": len(rows), "ok": sum(r["status"] == "ok" for r in rows),
        "errors": sum(r["status"] == "error" for r in rows), "skipped_now": len(skipped),
        "skip_reasons": dict(Counter(t.reason for t in skipped)),
        "distinct_repos": len({r["repo_url"] for r in rows if r["status"] == "ok"}),
        "stars": {"min": stars[0], "median": stars[len(stars) // 2], "max": stars[-1],
                  "ge_100": sum(s >= 100 for s in stars), "ge_500": sum(s >= 500 for s in stars)} if stars else {},
        "bundle_chars_median": (sorted(int(r["bundle_chars"]) for r in rows if r["status"] == "ok")[sum(r["status"] == "ok" for r in rows) // 2]
                                if any(r["status"] == "ok" for r in rows) else 0),
        "wall_seconds": round(time.time() - t0, 1), "out": str(out_path),
    }
    print("SUMMARY " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
