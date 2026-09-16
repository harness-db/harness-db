"""Harvest the competitor awesome-lists / catalogs (protocol section 5: snowball seeds).

Three lists are fetched from raw.githubusercontent.com and every entry is written as a
``Record`` with ``source="awesome"``:

* ``picrew`` — the catalog behind *Agent Harness Engineering: A Survey* (OpenReview
  eONq7FdiHa). ``https://raw.githubusercontent.com/picrew/LLM-Harness/main/projects.yaml``
  is tried first; that path returns 404 (the picrew/LLM-Harness repository only holds the
  project page), so the script follows the "Catalog" link in that repository's README to
  ``Picrew/awesome-agent-harness`` and locates the YAML catalog (``data/projects.yaml``) in
  its git tree through the GitHub API (``gh api``). Entries are parsed with PyYAML.
* ``gloriaameng`` — ``Gloriaameng/Awesome-Agent-Harness/README.md`` (companion of *Agent
  Harness for Large Language Model Agents: A Survey*, Preprints.org 202604.0428).
* ``ggjy`` — ``ggjy/Awesome-Agent-Engineering/README.md``.

The two Markdown lists are parsed generically: every list item or table row that carries
an ``http(s)`` link is one entry. Name, title, all links, the arXiv id (from any
``arxiv.org`` link) and a plain-text description are extracted; the current section
headings are kept as ``categories``. Entries with an arXiv id become paper records
(``title`` = paper title, ``arxiv_id`` set); entries whose main link is a GitHub repository
become repository records (``title`` = ``owner/repo`` so that they merge with the GitHub
harvest in ``dedupe.py``); anything else keeps its name as title.

``query_used`` names the list and file. Nothing is filtered by date or by the protocol
blocks: awesome-lists are seed material, and every entry is kept.

Usage:
    python scripts/harvest/awesome_lists.py --out data/raw/awesome.jsonl [--count-only]
        [--lists picrew gloriaameng ggjy]
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

from common import (
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    normalize_arxiv_id,
    now_iso,
    print_summary,
    setup_logging,
)

GH = r"C:\Program Files\GitHub CLI\gh.exe"
RAW = "https://raw.githubusercontent.com"

LISTS: dict[str, dict[str, str]] = {
    "picrew": {
        "label": "picrew/LLM-Harness (Agent Harness Engineering: A Survey)",
        "primary": f"{RAW}/picrew/LLM-Harness/main/projects.yaml",
        "readme": f"{RAW}/picrew/LLM-Harness/main/README.md",
        "kind": "yaml",
    },
    "gloriaameng": {
        "label": "Gloriaameng/Awesome-Agent-Harness (Agent Harness for LLM Agents: A Survey)",
        "primary": f"{RAW}/Gloriaameng/Awesome-Agent-Harness/main/README.md",
        "kind": "markdown",
    },
    "ggjy": {
        "label": "ggjy/Awesome-Agent-Engineering",
        "primary": f"{RAW}/ggjy/Awesome-Agent-Engineering/main/README.md",
        "kind": "markdown",
    },
}

SKIP_SECTIONS = re.compile(
    r"table of contents|^contents$|citation|contributing|license|news|update log|"
    r"badge|formatting|star history|acknowledg",
    re.IGNORECASE,
)
_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
_BOLD = re.compile(r"\*\*\s*_?\s*\"?(.+?)\"?\s*_?\s*\*\*")
_U = re.compile(r"<u>(.+?)</u>", re.IGNORECASE)
_GH_REPO = re.compile(r"^https?://github\.com/([^/\s#?]+)/([^/\s#?]+?)(?:\.git)?/?$")


# --------------------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------------------


def fetch_text(client: HttpClient, url: str, log: logging.Logger) -> str | None:
    resp = client.get(url)
    if resp.status_code == 404:
        log.warning("404 %s", url)
        return None
    if resp.status_code != 200:
        raise HttpError(f"GET {url}: HTTP {resp.status_code}")
    resp.encoding = "utf-8"
    return resp.text


def gh_api(endpoint: str) -> Any:
    proc = subprocess.run([GH, "api", "-X", "GET", endpoint], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if proc.returncode != 0:
        raise HttpError(f"gh api {endpoint}: {(proc.stderr or proc.stdout).strip()[:300]}")
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def discover_catalog(client: HttpClient, readme_url: str, log: logging.Logger) -> tuple[str, str] | None:
    """Follow the catalog link in the picrew README and find the YAML file via the GitHub API.

    Returns ``(raw_url, "owner/repo:path")`` or None.
    """
    readme = fetch_text(client, readme_url, log) or ""
    repos: list[str] = []
    for m in re.finditer(r"https?://github\.com/([\w.-]+/[\w.-]+)", readme):
        full = m.group(1).rstrip("/")
        if "awesome" in full.lower() and full not in repos:
            repos.append(full)
    for full in repos:
        try:
            meta = gh_api(f"repos/{full}")
            branch = meta.get("default_branch", "main")
            tree = gh_api(f"repos/{full}/git/trees/{branch}?recursive=1")
        except HttpError as exc:
            log.warning("discover %s: %s", full, exc)
            continue
        paths = [t["path"] for t in tree.get("tree", []) if t.get("type") == "blob"]
        for pat in (r"(^|/)projects\.ya?ml$", r"\.ya?ml$", r"\.json$"):
            hit = next((p for p in paths if re.search(pat, p) and not p.startswith(".github")), None)
            if hit:
                log.info("catalog for %s: %s/%s", readme_url, meta["full_name"], hit)
                return f"{RAW}/{meta['full_name']}/{branch}/{hit}", f"{meta['full_name']}:{hit}"
    return None


# --------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------


@dataclass
class Entry:
    name: str
    title: str
    url: str | None
    arxiv_id: str | None
    description: str
    links: list[tuple[str, str]] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


def parse_yaml_catalog(text: str, log: logging.Logger) -> list[Entry]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise HttpError("PyYAML is required to parse the picrew catalog (pip install pyyaml)") from exc
    doc = yaml.safe_load(text)
    items = doc.get("entries") if isinstance(doc, dict) else doc
    entries: list[Entry] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or it.get("title") or "").strip()
        url = it.get("repo_url") or it.get("url") or it.get("link") or it.get("homepage")
        links = [(k, str(v)) for k, v in it.items() if isinstance(v, str) and v.startswith("http")]
        arxiv_id = None
        for _, u in links:
            if "arxiv.org" in u:
                arxiv_id = normalize_arxiv_id(u)
                break
        desc = str(it.get("summary_en") or it.get("summary") or it.get("description") or "").strip()
        why = str(it.get("why_included") or "").strip()
        entries.append(
            Entry(
                name=name,
                title=name,
                url=str(url) if url else None,
                arxiv_id=arxiv_id,
                description=desc + (f"\n\nWhy included: {why}" if why else ""),
                links=links,
                sections=[str(it.get("category") or "")],
                extra={k: v for k, v in it.items() if k not in ("summary_zh", "name_zh")},
            )
        )
    log.info("yaml catalog: %d entries (%s)", len(entries), ", ".join(f"{k}={len(v) if isinstance(v, list) else '-'}" for k, v in (doc.items() if isinstance(doc, dict) else [])))
    return entries


def _plain(md: str) -> str:
    t = _IMG.sub("", md)
    t = re.sub(r"\[([^\]]*)\]\((?:https?://[^)\s]+|#[^)]*)\)", r"\1", t)
    t = re.sub(r"</?u>|</?b>|</?i>|</?sub>|</?sup>|<br\s*/?>", "", t, flags=re.IGNORECASE)
    t = t.replace("**", "").replace("__", "")
    t = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", t)
    t = re.sub(r"^\s*[-*+]\s+|^\s*\d+\.\s+", "", t)
    t = re.sub(r"\s*\|\s*", " | ", t).strip(" |")
    return re.sub(r"\s+", " ", t).strip()


def parse_markdown_list(text: str, log: logging.Logger) -> list[Entry]:
    entries: list[Entry] = []
    sections: dict[int, str] = {}
    skipping = False
    for raw in text.splitlines():
        line = raw.rstrip()
        hm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if hm:
            level = len(hm.group(1))
            title = _plain(hm.group(2)).strip()
            sections[level] = title
            for lv in list(sections):
                if lv > level:
                    del sections[lv]
            skipping = bool(SKIP_SECTIONS.search(title))
            continue
        if skipping:
            continue
        is_item = bool(re.match(r"^\s*([-*+]|\d+\.)\s+", line))
        is_row = line.lstrip().startswith("|") and not re.match(r"^\s*\|?\s*:?-{2,}", line)
        if not (is_item or is_row):
            continue
        stripped = _IMG.sub("", line)
        links = [(t.strip(), u) for t, u in _LINK.findall(stripped)]
        if not links:
            continue
        if is_row and all(t.lower() in ("paper", "code", "link", "name", "system", "benchmark") for t, _ in links) and "---" in line:
            continue
        arxiv_id = None
        for _, u in links:
            if "arxiv.org" in u:
                arxiv_id = normalize_arxiv_id(u)
                if arxiv_id:
                    break
        um = _U.search(line)
        bm = _BOLD.search(stripped)
        name = _plain(um.group(1)) if um else ""
        title = _plain(bm.group(1)) if bm else ""
        first_text = next((t for t, _ in links if t and not t.startswith("!")), "")
        if not name:
            name = first_text or title
        if not title:
            title = name or first_text
        title = title.strip(" .,:;\"'")
        name = name.strip(" .,:;\"'")
        if not title:
            continue
        entries.append(
            Entry(
                name=name,
                title=title,
                url=None,
                arxiv_id=arxiv_id,
                description=_plain(line),
                links=links,
                sections=[sections[k] for k in sorted(sections) if k >= 2],
            )
        )
    log.info("markdown list: %d entries", len(entries))
    return entries


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------


def entry_to_record(e: Entry, list_key: str, query: str) -> Record:
    gh_url = next((u for _, u in e.links if _GH_REPO.match(u)), None)
    arxiv_url = next((u for _, u in e.links if "arxiv.org" in u), None)
    if e.arxiv_id:
        kind, url, title = "paper", arxiv_url or e.url, e.title
    elif gh_url or (e.url and _GH_REPO.match(e.url)):
        url = e.url if e.url and _GH_REPO.match(e.url) else gh_url
        m = _GH_REPO.match(url or "")
        kind, title = "repo", (f"{m.group(1)}/{m.group(2)}" if m else e.title)
    else:
        kind, url, title = "other", e.url or (e.links[0][1] if e.links else None), e.title
    key = (url or title).lower()
    sid = f"{list_key}:{hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]}"
    return Record(
        id=f"awesome:{sid}",
        source="awesome",
        source_id=sid,
        title=title,
        abstract=e.description,
        authors=[],
        date=str(e.extra.get("updated_at")) if e.extra.get("updated_at") else None,
        venue=f"awesome:{list_key}",
        url=url,
        doi=None,
        arxiv_id=e.arxiv_id,
        categories=[s for s in e.sections if s],
        query_used=query,
        retrieved_at=now_iso(),
        extra={"kind": kind, "name": e.name, "list": list_key, "links": [{"text": t, "url": u} for t, u in e.links], **{k: v for k, v in e.extra.items() if k not in ("name",)}},
    )


def main(argv: list[str] | None = None) -> int:
    p = build_parser("awesome", __doc__.split("\n\n")[0])
    p.add_argument("--lists", nargs="*", choices=tuple(LISTS), default=list(LISTS))
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    client = HttpClient(min_interval=0.5, logger=log)

    per_list: dict[str, dict[str, Any]] = {}
    written = 0
    error: str | None = None
    with JsonlWriter(args.out, count_only=args.count_only) as w:
        for key in args.lists:
            cfg = LISTS[key]
            info: dict[str, Any] = {"label": cfg["label"], "url": cfg["primary"], "entries": 0, "written": 0, "error": None}
            try:
                text = fetch_text(client, cfg["primary"], log)
                if text is None and cfg["kind"] == "yaml":
                    found = discover_catalog(client, cfg["readme"], log)
                    if not found:
                        raise HttpError(f"{cfg['primary']} is 404 and no catalog file was found via the GitHub API")
                    info["url"], info["discovered"] = found
                    text = fetch_text(client, found[0], log)
                if text is None:
                    raise HttpError(f"{info['url']}: 404")
                entries = parse_yaml_catalog(text, log) if cfg["kind"] == "yaml" else parse_markdown_list(text, log)
                query = f"awesome-list:{key}:{info['url']}"
                n_before = w.count
                kinds: dict[str, int] = {}
                for e in entries:
                    rec = entry_to_record(e, key, query)
                    if w.write(rec):
                        kinds[rec.extra["kind"]] = kinds.get(rec.extra["kind"], 0) + 1
                info.update(entries=len(entries), written=w.count - n_before, kinds=kinds, with_arxiv_id=sum(1 for e in entries if e.arxiv_id))
            except HttpError as exc:
                info["error"] = str(exc)
                log.error("%s: %s", key, exc)
                error = (error + "; " if error else "") + f"{key}: {exc}"
            per_list[key] = info
        written = w.count
    print_summary(
        "awesome",
        {
            "query": {k: v["url"] for k, v in per_list.items()},
            "lists": per_list,
            "counts": {"both": written},
            "written": written,
            "capped": False,
            "max_records": args.max_records,
            "error": error,
            "requests": client.requests_made,
            "out": None if args.count_only else args.out,
        },
    )
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
