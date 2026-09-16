"""Harvest GitHub repositories through the ``gh`` CLI (already authenticated).

Queries (each with ``stars:>500 created:<since>..<until>``):
  topic:llm-agent, topic:ai-agent, topic:coding-agent, topic:llm-agents, topic:agent-framework,
  and the keyword queries "agent harness", "coding agent", "computer-use agent",
  "browser agent" llm  (searched in name, description and README).

GitHub search returns at most 1000 results per query, so any query with more hits is split
recursively on the ``created`` date range. Hits are deduplicated by ``full_name``; then each
repo's README is fetched (``gh api repos/{full_name}/readme``) and the repo is kept when the
README or description matches the LLM block regex. Search calls are paced at 2 s
(30/min limit); content calls at 0.25 s.

Record fields: title = full_name, abstract = description + first 1500 README characters,
``extra`` = {stars, created_at, pushed_at, topics, description, language, readme_excerpt,
queries}.

Usage:
    python scripts/harvest/github.py --since 2022-10-01 --until 2026-08-31 \
        --out data/raw/github.jsonl [--count-only] [--min-stars 500]
"""

from __future__ import annotations

import base64
import json
import logging
import subprocess
import sys
import time
from datetime import date, timedelta
from typing import Any

from common import (
    LLM_RE,
    LLM_TERMS,
    JsonlWriter,
    RateLimiter,
    Record,
    build_parser,
    now_iso,
    print_summary,
    setup_logging,
)

GH = r"C:\Program Files\GitHub CLI\gh.exe"
TOPIC_QUERIES = ("topic:llm-agent", "topic:ai-agent", "topic:coding-agent", "topic:llm-agents", "topic:agent-framework")
KEYWORD_QUERIES = ('"agent harness"', '"coding agent"', '"computer-use agent"', '"browser agent" llm')
KEYWORD_FIELDS = "in:name,description,readme"
SEARCH_INTERVAL = 2.1  # 30 search requests / minute
CONTENT_INTERVAL = 0.25
SEARCH_CAP = 1000
README_EXCERPT = 1500


class GhError(RuntimeError):
    pass


class Gh:
    """Thin wrapper around ``gh api`` with pacing and retries on rate-limit errors."""

    def __init__(self, log: logging.Logger, exe: str = GH) -> None:
        self.exe = exe
        self.log = log
        self.search_limiter = RateLimiter(SEARCH_INTERVAL)
        self.content_limiter = RateLimiter(CONTENT_INTERVAL)
        self.calls = 0

    def api(self, endpoint: str, fields: dict[str, Any] | None = None, *, search: bool = False, retries: int = 5) -> Any:
        cmd = [self.exe, "api", "-X", "GET", endpoint]
        for k, v in (fields or {}).items():
            cmd += ["-f", f"{k}={v}"]
        (self.search_limiter if search else self.content_limiter).wait()
        for attempt in range(retries + 1):
            self.calls += 1
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
            if proc.returncode == 0:
                return json.loads(proc.stdout) if proc.stdout.strip() else None
            err = (proc.stderr or proc.stdout).strip()
            if "HTTP 404" in err:
                return None
            if attempt >= retries:
                raise GhError(f"gh api {endpoint}: {err[:300]}")
            wait = 60.0 if ("rate limit" in err.lower() or "HTTP 403" in err or "HTTP 429" in err) else 3.0 * (attempt + 1)
            self.log.warning("gh api %s failed (%s); retry %d in %.0fs", endpoint, err[:120], attempt + 1, wait)
            time.sleep(wait)
        raise GhError("unreachable")


def full_query(base: str, min_stars: int, d0: str, d1: str) -> str:
    return f"{base} stars:>{min_stars} created:{d0}..{d1}"


def search_total(gh: Gh, q: str) -> int:
    data = gh.api("search/repositories", {"q": q, "per_page": 1}, search=True)
    return int(data.get("total_count", 0)) if data else 0


def search_all(gh: Gh, base: str, min_stars: int, d0: str, d1: str, log: logging.Logger) -> list[dict[str, Any]]:
    """All repos for a query; splits the created-date range when a slice exceeds 1000 hits."""
    q = full_query(base, min_stars, d0, d1)
    total = search_total(gh, q)
    if total > SEARCH_CAP and d0 < d1:
        a, b = date.fromisoformat(d0), date.fromisoformat(d1)
        mid = a + (b - a) / 2
        log.info("%s: %d > %d hits; splitting %s..%s", base, total, SEARCH_CAP, d0, d1)
        return search_all(gh, base, min_stars, d0, mid.isoformat(), log) + search_all(
            gh, base, min_stars, (mid + timedelta(days=1)).isoformat(), d1, log
        )
    items: list[dict[str, Any]] = []
    page = 1
    while len(items) < min(total, SEARCH_CAP):
        data = gh.api("search/repositories", {"q": q, "per_page": 100, "page": page, "sort": "stars", "order": "desc"}, search=True)
        batch = (data or {}).get("items", [])
        if not batch:
            break
        items.extend(batch)
        page += 1
    return items


def fetch_readme(gh: Gh, full_name: str) -> str | None:
    data = gh.api(f"repos/{full_name}/readme")
    if not data or not data.get("content"):
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return None


def repo_to_record(repo: dict[str, Any], readme: str, queries: list[str], query_desc: str) -> Record:
    desc = repo.get("description") or ""
    excerpt = readme[:README_EXCERPT]
    return Record(
        id=f"github:{repo['full_name']}",
        source="github",
        source_id=repo["full_name"],
        title=repo["full_name"],
        abstract=(desc + "\n\n" + excerpt).strip(),
        authors=[(repo.get("owner") or {}).get("login", "")],
        date=(repo.get("created_at") or "")[:10] or None,
        venue="github",
        url=repo.get("html_url"),
        doi=None,
        arxiv_id=None,
        categories=list(repo.get("topics") or []),
        query_used=query_desc,
        retrieved_at=now_iso(),
        extra={
            "name": repo.get("name"),
            "description": desc,
            "stars": repo.get("stargazers_count"),
            "created_at": repo.get("created_at"),
            "pushed_at": repo.get("pushed_at"),
            "topics": list(repo.get("topics") or []),
            "language": repo.get("language"),
            "readme_excerpt": excerpt,
            "queries": queries,
        },
    )


def main(argv: list[str] | None = None) -> int:
    p = build_parser("github", __doc__.split("\n\n")[0])
    p.add_argument("--min-stars", type=int, default=500)
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    gh = Gh(log)

    bases = list(TOPIC_QUERIES) + [f"{k} {KEYWORD_FIELDS}" for k in KEYWORD_QUERIES]
    per_query: dict[str, dict[str, Any]] = {}
    repos: dict[str, dict[str, Any]] = {}
    hits_by_repo: dict[str, list[str]] = {}
    error: str | None = None
    try:
        for base in bases:
            q = full_query(base, args.min_stars, args.since, args.until)
            if args.count_only:
                per_query[q] = {"total": search_total(gh, q)}
                log.info("%s -> %d", q, per_query[q]["total"])
                continue
            items = search_all(gh, base, args.min_stars, args.since, args.until, log)
            per_query[q] = {"total": len(items)}
            log.info("%s -> %d repos", q, len(items))
            for r in items:
                repos.setdefault(r["full_name"], r)
                hits_by_repo.setdefault(r["full_name"], []).append(base)
    except GhError as exc:
        error = str(exc)
        log.error("search failed: %s", exc)

    written = 0
    capped = False
    stats = {"unique_repos": len(repos), "readme_missing": 0, "llm_match": 0}
    query_desc = f"gh search {bases} stars:>{args.min_stars} created:{args.since}..{args.until}; README/description ~ LLM block {list(LLM_TERMS)}"
    if not args.count_only and not error:
        with JsonlWriter(args.out) as w:
            for i, (name, repo) in enumerate(sorted(repos.items(), key=lambda kv: -(kv[1].get("stargazers_count") or 0)), 1):
                try:
                    readme = fetch_readme(gh, name)
                except GhError as exc:
                    log.warning("readme %s: %s", name, exc)
                    readme = None
                if readme is None:
                    stats["readme_missing"] += 1
                    readme = ""
                text = (repo.get("description") or "") + "\n" + readme
                if LLM_RE.search(text):
                    stats["llm_match"] += 1
                    if args.max_records and w.count >= args.max_records:
                        capped = True
                        continue
                    w.write(repo_to_record(repo, readme, hits_by_repo[name], query_desc))
                if i % 200 == 0:
                    log.info("processed %d/%d repos, kept %d", i, len(repos), w.count)
            written = w.count
    print_summary(
        "github",
        {
            "query": query_desc,
            "per_query": per_query,
            "counts": {"search_hits_total": sum(v["total"] for v in per_query.values()), "unique_repos": len(repos), "both": stats["llm_match"]},
            "stats": stats,
            "written": written,
            "capped": capped,
            "max_records": args.max_records,
            "error": error,
            "requests": gh.calls,
            "out": None if args.count_only else args.out,
        },
    )
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
