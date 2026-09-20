"""Fetch full text for the HARNESS-Review full-text screening queue.

For every ``record_id`` in ``data/screening/fulltext_pilot.csv`` (first) and
``data/screening/fulltext_queue.csv`` (then the rest) this script resolves the record by
IDENTIFIER (arXiv id, ACL id, OpenReview forum id, DOI, S2 paper id, OpenAlex work id, GitHub
repo, URL; never by title, see ``data/screening/metadata_mismatch.csv``), downloads the
document, converts it to plain text and writes

* ``data/fulltext/<safe id>.txt``: a 5-line header (record_id, source_used, fetched_url,
  fetched_title, fetched_at) followed by a blank line and the text;
* one row per attempt in ``data/screening/fulltext_index.csv`` (``status`` ok|not_retrievable);
* failures additionally in ``data/screening/not_retrievable.csv`` with the reason and every URL
  tried.

Resolution order (first success wins; see scripts/fetch_fulltext_README.md):

1. arXiv id (candidate ``arxiv_id``, a ``10.48550/arXiv.*`` DOI or an arxiv.org URL) ->
   ``https://arxiv.org/pdf/<id>``, then ``https://arxiv.org/html/<id>``;
2. ACL Anthology id (URL or ``10.18653/v1/*`` DOI) -> ``https://aclanthology.org/<id>.pdf``;
3. OpenReview forum id -> ``api2.openreview.net/pdf?id=`` (then API v1), with login;
4. GitHub repo -> pinned ref (latest tag dated <= 2026-08-31, else the default-branch commit
   before that date; protocol 4.5), shallow blobless clone into
   ``data/raw/cache/repos/<owner>__<repo>`` and a text bundle (README, docs, file tree);
5. DOI -> OpenAlex ``best_oa_location.pdf_url`` -> Semantic Scholar ``openAccessPdf`` /
   ``externalIds.ArXiv`` -> DOI landing page HTML (last resort);
6. S2 / OpenAlex records without a DOI -> S2 / OpenAlex lookup for an arXiv id, DOI or OA PDF;
7. any remaining URL (grey, leaderboard, awesome, survey_refs, repository landing pages) ->
   main text of the page (stdlib ``html.parser``).

arXiv requests are strictly serial (one request every 3 s, FIFO gate shared by all threads);
the other hosts run in a separate pool of 4 threads with per-host pacing. Every record is
appended and flushed as soon as it finishes, so the run is resumable: ids already in the index
with ``status == ok`` are skipped (``--skip-failed`` also skips recorded failures).

Usage:
    python scripts/fetch_fulltext.py --only-pilot
    python scripts/fetch_fulltext.py                      # pilot first, then the whole queue
    python scripts/fetch_fulltext.py --limit 50 --ids-file my_ids.csv
    python scripts/fetch_fulltext.py --summary --only-pilot   # counts from the index, no fetching
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import shutil
import stat
import statistics
import subprocess
import sys
import threading
import time
from collections import Counter
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Self
from urllib.parse import quote, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent / "harvest"))
from common import (
    CONTACT_EMAIL,
    REPO_ROOT,
    HttpClient,
    HttpError,
    RateLimiter,
    normalize_doi,
    read_jsonl,
)

# --------------------------------------------------------------------------------------
# Paths and constants
# --------------------------------------------------------------------------------------

SCREENING = REPO_ROOT / "data" / "screening"
QUEUE_CSV = SCREENING / "fulltext_queue.csv"
PILOT_CSV = SCREENING / "fulltext_pilot.csv"
INDEX_CSV = SCREENING / "fulltext_index.csv"
NOT_RETRIEVABLE_CSV = SCREENING / "not_retrievable.csv"
MISMATCH_CSV = SCREENING / "metadata_mismatch.csv"
CANDIDATES_CSV = REPO_ROOT / "data" / "raw" / "candidates.csv"
RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_DIR = REPO_ROOT / "data" / "fulltext"
PDF_CACHE = RAW_DIR / "cache" / "pdf"
REPO_CACHE = RAW_DIR / "cache" / "repos"
LOG_FILE = OUT_DIR / "_fetch_fulltext.log"

CUTOFF_DATE = "2026-08-31"  # protocol 4.5 version cutoff
CUTOFF_TS = f"{CUTOFF_DATE}T23:59:59Z"
USER_AGENT = (
    "harness-db-fulltext/0.1 (HARNESS-Review systematic review full-text retrieval; "
    f"https://github.com/bhaskargurram-ai; mailto:{CONTACT_EMAIL})"
)
MAX_CHARS = 250_000
MIN_CHARS_PAPER = 1500  # PDFs and arXiv HTML shorter than this are treated as failures
MIN_CHARS_LANDING = 1000  # DOI / repository landing pages
MIN_CHARS_WEB = 300  # grey / leaderboard / awesome pages
README_CAP = 100_000
DOCS_CAP = 20_000
TREE_CAP = 400
PDF_EXTRACT_TIMEOUT = 300  # seconds, hard kill of the extraction subprocess
PDF_EXTRACT_BUDGET = 150  # seconds, soft per-document budget inside the subprocess

INDEX_FIELDS = [
    "record_id",
    "status",
    "source_used",
    "fetched_url",
    "fetched_title",
    "chars",
    "ref_used",
    "fetched_at",
]
FAIL_FIELDS = ["record_id", "source", "reason", "urls_tried", "attempted_at"]

API_OPENREVIEW_V2 = "https://api2.openreview.net"
API_OPENREVIEW_V1 = "https://api.openreview.net"
S2_API = "https://api.semanticscholar.org/graph/v1/paper/"
OPENALEX_API = "https://api.openalex.org/works/"

#: (min seconds between requests, max retries, timeout) per host group.
HOST_POLICY: dict[str, tuple[float, int, float]] = {
    "arxiv": (3.0, 6, 90.0),
    "openalex": (0.15, 5, 60.0),
    "s2": (1.05, 5, 60.0),
    "acl": (1.0, 3, 90.0),
    "openreview": (1.0, 3, 90.0),
    "web": (1.0, 1, 45.0),
}

WEB_SOURCES = {"grey", "leaderboard", "awesome", "survey_refs"}
NO_WEB_FALLBACK_HOSTS = (
    "semanticscholar.org",
    "openalex.org",
    "openreview.net",
    "arxiv.org",
    "aclanthology.org",
)

log = logging.getLogger("fulltext")


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_id(record_id: str) -> str:
    """File-system-safe id: ``[:/\\]`` -> ``__`` (plus any other Windows-reserved character
    -> ``_``)."""
    s = re.sub(r"[:/\\]", "__", record_id)
    return re.sub(r'[<>"|?*\x00-\x1f]', "_", s)


def load_env() -> dict[str, str]:
    """Environment variables, falling back to the repo's .env (never committed)."""
    env: dict[str, str] = {}
    path = REPO_ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("OPENREVIEW_USERNAME", "OPENREVIEW_PASSWORD", "S2_API_KEY", "OPENALEX_API_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


# --------------------------------------------------------------------------------------
# Identifier helpers
# --------------------------------------------------------------------------------------

_NEW_ARXIV = re.compile(r"^(\d{2})(\d{2})\.(\d{4,5})$")
_OLD_ARXIV = re.compile(r"^([a-z\-]+)(\.[A-Z]{2})?/(\d{7})$")
_OLD_ARCHIVES = {
    "acc-phys", "adap-org", "alg-geom", "ao-sci", "astro-ph", "atom-ph", "bayes-an", "chao-dyn",
    "chem-ph", "cmp-lg", "comp-gas", "cond-mat", "cs", "dg-ga", "funct-an", "gr-qc", "hep-ex",
    "hep-lat", "hep-ph", "hep-th", "math", "math-ph", "mtrl-th", "nlin", "nucl-ex", "nucl-th",
    "patt-sol", "physics", "plasm-ph", "q-alg", "q-bio", "quant-ph", "solv-int", "supr-con",
}  # fmt: skip
_ARXIV_URL = re.compile(r"arxiv\.org/(?:abs|pdf|html)/([a-z\-]+(?:\.[A-Z]{2})?/\d{7}|\d{4}\.\d{4,5})",
                        re.IGNORECASE)
_ARXIV_DOI = re.compile(r"^10\.48550/arxiv\.(.+)$", re.IGNORECASE)
_ACL_ID = re.compile(r"^(\d{4}\.[a-z0-9\-]+\.\d+|[A-Z]\d{2}-\d{4})$")


def valid_arxiv_id(value: str | None) -> str | None:
    """Return a bare version-less arXiv id if ``value`` is a well-formed one, else None.

    Rejects the garbage the harvesters' loose regex let through (``gov/3812380``,
    ``2024.11511`` or ``2405.2024`` from IEEE/Elsevier DOIs, ...): new-style ids need YY in
    07..current year, MM in 01..12 and 4 (before 2015) or 5 (from 2015) sequence digits;
    old-style ids need a known archive.
    """
    if not value:
        return None
    v = re.sub(r"v\d+$", "", str(value).strip())
    m = _NEW_ARXIV.match(v)
    if m:
        yy, mm = int(m.group(1)), int(m.group(2))
        # 0704-1412: 4-digit sequence numbers; 1501 onwards: 5 digits
        if (7 <= yy <= datetime.now(UTC).year % 100 and 1 <= mm <= 12
                and len(m.group(3)) == (4 if yy < 15 else 5)):
            return v
        return None
    m = _OLD_ARXIV.match(v)
    if m and m.group(1) in _OLD_ARCHIVES:
        return v
    return None


def arxiv_from_url(url: str | None) -> str | None:
    if not url:
        return None
    m = _ARXIV_URL.search(url)
    return valid_arxiv_id(m.group(1)) if m else None


def arxiv_from_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    m = _ARXIV_DOI.match(doi)
    return valid_arxiv_id(m.group(1)) if m else None


def acl_id_of(url: str | None, doi: str | None) -> str | None:
    if url and "aclanthology.org/" in url:
        part = url.split("aclanthology.org/", 1)[1].strip("/").split("/")[0]
        part = re.sub(r"\.pdf$", "", part)
        if _ACL_ID.match(part):
            return part
    if doi and doi.startswith("10.18653/v1/"):
        part = doi.split("10.18653/v1/", 1)[1]
        if _ACL_ID.match(part):
            return part
    return None


_GH_RESERVED = {
    "orgs", "topics", "features", "marketplace", "sponsors", "settings", "apps", "collections",
    "trending", "about", "search", "login", "enterprise", "explore", "pricing", "readme", "site",
}  # fmt: skip


def github_repo_of(url: str | None) -> tuple[str, str, str] | None:
    """(owner, repo, subpath) for a github.com repository URL, else None."""
    if not url:
        return None
    try:
        p = urlparse(url.strip())
    except ValueError:
        return None
    if p.netloc.lower() not in ("github.com", "www.github.com"):
        return None
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2 or parts[0].lower() in _GH_RESERVED:
        return None
    owner, repo = parts[0], re.sub(r"\.git$", "", parts[1])
    subpath = ""
    if len(parts) > 4 and parts[2] in ("tree", "blob"):
        subpath = "/".join(parts[4:])
    return owner, repo, subpath


def valid_web_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        p = urlparse(url.strip())
    except ValueError:
        return False
    host = p.netloc.lower()
    return p.scheme in ("http", "https") and "." in host and not host.endswith(".")


# --------------------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------------------

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff]")  # + lone surrogates
_HSPACE = re.compile(r"[ \t\u00a0\u2000-\u200b\u202f\u205f\u3000]+")
REF_RE = re.compile(r"^(?:(?:\d{1,2}|[IVXL]{1,5})\.?\s+)?(?:References$|REFERENCES|Bibliography)",
                    re.MULTILINE)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CTRL.sub("", text)
    lines = [_HSPACE.sub(" ", ln).strip() for ln in text.split("\n")]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def drop_references(text: str) -> tuple[str, bool]:
    """Cut at the first reference-section heading that occurs after the first 20 % of the text
    (earlier hits are tables of contents). Everything before the heading is kept."""
    min_pos = int(len(text) * 0.2)
    for m in REF_RE.finditer(text):
        if m.start() >= min_pos:
            return text[: m.start()].rstrip(), True
    return text, False


def one_line(s: str | None, cap: int = 300) -> str:
    return re.sub(r"\s+", " ", _CTRL.sub("", s or "")).strip()[:cap]


_BAD_META_TITLE = re.compile(
    r"^(untitled|microsoft word|arxiv|main|paper|document|slide|template|title|"
    r"instructions for|formatting instructions|author guidelines|proceedings|"
    r"latex|overleaf|manuscript)\b|\.(tex|dvi|pdf|docx?|ps)$",
    re.IGNORECASE,
)
_BOILER_LINE = re.compile(
    r"^(arxiv:|published as|preprint|under review|accepted|proceedings|workshop|"
    r"https?://|doi:|\d+$|page \d)",
    re.IGNORECASE,
)


def plausible_title(t: str | None) -> bool:
    t = one_line(t)
    if len(t) < 8 or len(t) > 300 or len(re.findall(r"[A-Za-z]{2,}", t)) < 2:
        return False
    return not _BAD_META_TITLE.search(t)


def choose_pdf_title(res: dict[str, Any], text: str) -> str:
    for cand in (res.get("font_title"), res.get("meta_title")):
        if plausible_title(cand):
            return one_line(cand)
    for ln in text.split("\n")[:40]:
        ln = ln.strip()
        if len(ln.split()) >= 3 and not _BOILER_LINE.match(ln):
            return one_line(ln)
    return ""


class _HTMLText(HTMLParser):
    """Minimal HTML-to-text: drops scripts/styles/navigation, keeps block structure, prefers
    the ``<main>``/``<article>`` subtree when it holds the bulk of the text, collects the
    title from ``citation_title`` / ``og:title`` / ``<title>`` / first ``<h1>``."""

    SKIP = frozenset({
        "script", "style", "nav", "header", "footer", "noscript", "svg", "form", "button",
        "iframe", "template", "aside", "select", "canvas", "dialog",
    })  # fmt: skip
    BLOCK = frozenset({
        "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table",
        "section", "article", "main", "pre", "blockquote", "dt", "dd", "dl", "figcaption",
        "figure", "hr", "caption", "summary", "details", "tbody", "thead",
    })  # fmt: skip
    VOID = frozenset({"br", "hr", "img", "meta", "link", "input", "wbr", "area", "base", "col",
                      "embed", "source", "track", "param"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.math = 0
        self.in_main = 0
        self.in_title = False
        self.in_h1 = False
        self.parts: list[str] = []
        self.main_parts: list[str] = []
        self.title = ""
        self.h1 = ""
        self.meta: dict[str, str] = {}

    def _emit(self, s: str) -> None:
        self.parts.append(s)
        if self.in_main:
            self.main_parts.append(s)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            if name in ("citation_title", "og:title", "dc.title") and a.get("content"):
                self.meta.setdefault(name, a["content"])
            return
        if self.skip:
            if tag in self.SKIP:
                self.skip += 1
            return
        if tag in self.SKIP:
            self.skip += 1
            return
        if tag == "math":
            if not self.math and a.get("alttext"):
                self._emit(" " + a["alttext"] + " ")
            self.math += 1
            return
        if tag in ("main", "article"):
            self.in_main += 1
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_h1 = True
        if tag in self.BLOCK:
            self._emit("\n")
        elif tag in ("td", "th"):
            self._emit(" \t ")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == "math":
            self.math = max(0, self.math - 1)
            return
        if tag in ("main", "article"):
            self.in_main = max(0, self.in_main - 1)
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
        if tag in self.BLOCK:
            self._emit("\n")

    def handle_data(self, data: str) -> None:
        if self.in_title and not self.skip:
            self.title += data
            return
        if self.skip or self.math:
            return
        if self.in_h1 and len(self.h1) < 500:
            self.h1 += data
        self._emit(data)


def html_to_text(html_str: str) -> tuple[str, str]:
    """(title, text) of an HTML document."""
    p = _HTMLText()
    try:
        p.feed(html_str)
        p.close()
    except (AssertionError, ValueError, IndexError) as exc:  # keep what was parsed so far
        log.debug("html parse error: %r", exc)
    full = normalize_text("".join(p.parts))
    main = normalize_text("".join(p.main_parts))
    text = main if len(main) >= 500 else full
    title = ""
    for cand in (p.meta.get("citation_title"), p.meta.get("og:title"), p.meta.get("dc.title"),
                 p.title, p.h1):
        if cand and one_line(cand):
            title = one_line(cand)
            break
    title = re.sub(r"^\[[^\]]{4,20}\]\s*", "", title)  # arXiv HTML: "[2401.01234] Title"
    return title, text


def decode_html(resp: requests.Response) -> str:
    ct = resp.headers.get("Content-Type", "")
    m = re.search(r"charset=([\w\-]+)", ct, re.IGNORECASE)
    body = resp.content
    enc = m.group(1) if m else None
    if not enc:
        m2 = re.search(rb"charset=[\"']?([\w\-]+)", body[:4096], re.IGNORECASE)
        enc = m2.group(1).decode("ascii", "ignore") if m2 else None
    for e in (enc, "utf-8"):
        if not e:
            continue
        try:
            return body.decode(e)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("cp1252", errors="replace")


def is_pdf(body: bytes) -> bool:
    return b"%PDF" in body[:1024]


# --------------------------------------------------------------------------------------
# PDF extraction (runs in a subprocess: hard timeout, crash isolation, real parallelism)
# --------------------------------------------------------------------------------------


def _pdf_worker(path: str) -> dict[str, Any]:
    """Extract text + title candidates from a PDF. Called in a child process."""
    logging.disable(logging.CRITICAL)
    import warnings

    warnings.filterwarnings("ignore")
    from pypdf import PdfReader

    out: dict[str, Any] = {"text": "", "pages": 0, "pages_read": 0, "meta_title": "",
                           "font_title": "", "truncated": False, "error": ""}
    try:
        reader = PdfReader(path, strict=False)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:  # noqa: BLE001
                out["error"] = f"encrypted: {exc!r}"[:300]
                return out
        try:
            meta = reader.metadata
            out["meta_title"] = str(meta.title) if meta and meta.title else ""
        except Exception as exc:  # noqa: BLE001
            out["meta_title"] = ""
            out["error"] = f"metadata: {exc!r}"[:200]
        pages = reader.pages
        out["pages"] = len(pages)
        runs: list[tuple[float, float, str]] = []

        def visitor(text: str, cm: Any, tm: Any, _font: Any, size: Any) -> None:
            if not text or not text.strip() or not size:
                return
            try:
                if abs(tm[1]) > 1e-3 or abs(tm[2]) > 1e-3 or abs(cm[1]) > 1e-3 or abs(cm[2]) > 1e-3:
                    return  # rotated (the arXiv side stamp)
                eff = abs(float(size) * float(tm[3]) * float(cm[3] or 1))
                y = float(tm[4]) * float(cm[1]) + float(tm[5]) * float(cm[3]) + float(cm[5])
            except (TypeError, ValueError, IndexError):
                return
            runs.append((round(eff, 1), y, text))

        texts: list[str] = []
        start = time.monotonic()
        total = 0
        for i, page in enumerate(pages):
            try:
                if i == 0:
                    t = page.extract_text(visitor_text=visitor) or ""
                else:
                    t = page.extract_text() or ""
            except Exception:  # noqa: BLE001
                t = ""
            texts.append(t)
            total += len(t)
            out["pages_read"] = i + 1
            if total > 2 * MAX_CHARS or time.monotonic() - start > PDF_EXTRACT_BUDGET:
                out["truncated"] = i + 1 < len(pages)
                break
        out["text"] = "\n\n".join(texts)
        if runs and pages:
            try:
                box = pages[0].mediabox
                bottom, height = float(box.bottom), float(box.top) - float(box.bottom)
            except Exception:  # noqa: BLE001
                bottom, height = 0.0, 792.0
            out["font_title"] = _font_title(runs, bottom, height)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"[:300]
    return out


def _font_title(runs: list[tuple[float, float, str]], bottom: float, height: float) -> str:
    """Title = the largest-font text in the upper part of page 1.

    Upper zone = top 40 % of the page, then top 60 % (page-1 teaser figures often carry big
    labels lower down). For the largest size, every run on the same baselines with at least
    55 % of that size is added back in content order, which restores small-caps titles
    (``R`` + ``EACT``). Same-line runs are concatenated, lines are joined with a space.
    Groups of >= 3 words win over shorter ones."""
    for zone in (0.6, 0.4):
        upper = [r for r in runs if r[1] >= bottom + zone * height
                 and not re.match(r"\s*arXiv:\d", r[2])]
        groups: list[str] = []
        for size in sorted({r[0] for r in upper}, reverse=True)[:6]:
            lines = {r[1] for r in upper if abs(r[0] - size) < 0.6}
            band = [r for r in upper if r[0] >= 0.55 * size
                    and any(abs(r[1] - y) <= 0.35 * size for y in lines)]
            parts: list[str] = []
            prev_y: float | None = None
            for _sz, y, t in band:
                if prev_y is not None and abs(y - prev_y) > 1.0:
                    parts.append(" ")
                parts.append(t.replace("\n", " "))
                prev_y = y
            joined = re.sub(r"\s+", " ", "".join(parts)).strip()
            if len(re.findall(r"[A-Za-z]", joined)) >= 8 and len(joined) <= 300:
                groups.append(joined)
        for g in groups:
            if len(re.findall(r"[A-Za-z]{2,}", g)) >= 3:
                return g
        if groups:
            return groups[0]
    return ""


def extract_pdf(path: Path) -> dict[str, Any]:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--_extract-pdf", str(path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=PDF_EXTRACT_TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        return {"error": f"pdf extraction timed out after {PDF_EXTRACT_TIMEOUT}s"}
    if proc.returncode != 0:
        return {"error": f"pdf extraction crashed: {proc.stderr[-300:].decode('utf-8', 'ignore')}"}
    try:
        return json.loads(proc.stdout.decode("ascii", "ignore"))
    except json.JSONDecodeError:
        return {"error": "pdf extraction returned no JSON"}


# --------------------------------------------------------------------------------------
# Concurrency primitives
# --------------------------------------------------------------------------------------


class FairGate:
    """FIFO (ticket) lock: whoever asked first gets the next arXiv request slot."""

    def __init__(self) -> None:
        self._cv = threading.Condition()
        self._next = 0
        self._serving = 0

    def __enter__(self) -> Self:
        with self._cv:
            ticket = self._next
            self._next += 1
            while ticket != self._serving:
                self._cv.wait()
        return self

    def __exit__(self, *exc: object) -> None:
        with self._cv:
            self._serving += 1
            self._cv.notify_all()


class SharedLimiter(RateLimiter):
    """Thread-safe RateLimiter shared by every thread's client of one host group."""

    def __init__(self, min_interval: float) -> None:
        super().__init__(min_interval)
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            super().wait()


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------


@dataclass
class Item:
    """One queue record. ``arxiv_id`` / ``doi`` / ``url`` are the record's OWN identifiers
    (record id + its raw harvest record). ``cluster_arxiv`` / ``cluster_doi`` are the merged
    identifiers of its dedupe cluster from candidates.csv; they can belong to a different
    paper (data/screening/metadata_mismatch.csv) and are only tried after everything else."""

    record_id: str
    source: str
    title: str
    url: str
    arxiv_id: str | None
    doi: str | None
    cluster_arxiv: str | None = None
    cluster_doi: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def prefix(self) -> str:
        return self.record_id.split(":", 1)[0]

    @property
    def local_id(self) -> str:
        return self.record_id.split(":", 1)[1] if ":" in self.record_id else self.record_id


@dataclass
class Doc:
    source_used: str
    fetched_url: str
    title: str
    text: str
    ref_used: str = ""


class Attempt:
    """Per-record log of every URL tried and why it failed."""

    def __init__(self) -> None:
        self.tried: list[str] = []
        self.whys: list[str] = []
        self.urls: set[str] = set()
        self.s2_done = False

    def fail(self, url: str, why: str) -> None:
        self.tried.append(f"{url} [{why}]")
        if why not in self.whys:
            self.whys.append(why)
        log.debug("  fail %s: %s", url, why)

    def note(self, url: str, what: str) -> None:
        """A lookup that answered but gave nothing fetchable (kept in urls_tried)."""
        self.tried.append(f"{url} [{what}]")

    def reason(self) -> str:
        return "; ".join(self.whys)[:300] or "no route applicable"

    def seen(self, url: str) -> bool:
        if url in self.urls:
            return True
        self.urls.add(url)
        return False


def read_ids(path: Path) -> list[str]:
    """Ids from a CSV with a header (``record_id`` column, else the first column) or from a
    plain list with one id per line."""
    text = path.read_text(encoding="utf-8-sig")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    first = lines[0].split(",")[0].strip()
    if "," in lines[0] or first == "record_id":
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames or []
            col = "record_id" if "record_id" in fields else fields[0]
            return [r[col].strip() for r in reader if (r.get(col) or "").strip()]
    return lines


def load_items(ids: list[str]) -> dict[str, Item]:
    wanted = set(ids)
    rows: dict[str, dict[str, str]] = {}
    with CANDIDATES_CSV.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["id"] in wanted:
                rows[r["id"]] = r
    raws: dict[str, dict[str, Any]] = {}
    for f in sorted(RAW_DIR.glob("*.jsonl")):
        for d in read_jsonl(f):
            if d.get("id") in wanted and d["id"] not in raws:
                raws[d["id"]] = d
    items: dict[str, Item] = {}
    for rid in ids:
        r = rows.get(rid)
        if r is None:
            log.warning("%s not in candidates.csv; skipped", rid)
            continue
        raw = raws.get(rid) or {}
        extra = raw.get("extra") or {}
        prefix, _, local = rid.partition(":")
        # own identifiers: the record id itself, then the canonical raw record
        url = str(raw.get("url") or "").strip()
        if not url:
            alt = extra.get("repo_url") or next(iter(extra.get("urls") or []), "")
            url = str(alt or "").strip()
        if not url and not raw:
            url = (r.get("url") or "").strip()
        doi = normalize_doi(raw.get("doi"))
        ax = (valid_arxiv_id(local) if prefix == "arxiv" else None) or valid_arxiv_id(
            raw.get("arxiv_id")) or arxiv_from_doi(doi) or arxiv_from_url(url)
        # cluster-level identifiers (fallback only)
        c_doi = normalize_doi(r.get("doi"))
        c_url = (r.get("url") or "").strip()
        c_ax = valid_arxiv_id(r.get("arxiv_id")) or arxiv_from_doi(c_doi) or arxiv_from_url(c_url)
        items[rid] = Item(rid, r.get("source") or prefix, r.get("title") or "", url, ax, doi,
                          c_ax if c_ax != ax else None, c_doi if c_doi != doi else None, extra)
    return items


# --------------------------------------------------------------------------------------
# Fetcher
# --------------------------------------------------------------------------------------


class Fetcher:
    def __init__(self, env: dict[str, str]) -> None:
        self.env = env
        self.gate = FairGate()
        self.limiters: dict[str, SharedLimiter] = {
            g: SharedLimiter(pol[0]) for g, pol in HOST_POLICY.items() if g != "web"
        }
        self.web_limiters: dict[str, SharedLimiter] = {}
        self._lim_lock = threading.Lock()
        self._tls = threading.local()
        self._or_tokens: dict[str, str | None] = {}
        self._or_lock = threading.Lock()
        self.gh = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
        self.git_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
        self.s2_headers = {"x-api-key": env["S2_API_KEY"]} if env.get("S2_API_KEY") else {}
        self.openalex_params: dict[str, str] = {"mailto": CONTACT_EMAIL}
        if env.get("OPENALEX_API_KEY"):
            self.openalex_params["api_key"] = env["OPENALEX_API_KEY"]
        self.arxiv_requests = 0

    # ---- HTTP plumbing ---------------------------------------------------------------

    def client(self, group: str, host: str = "") -> HttpClient:
        clients = getattr(self._tls, "clients", None)
        if clients is None:
            clients = self._tls.clients = {}
        key = f"web:{host}" if group == "web" else group
        c = clients.get(key)
        if c is None:
            interval, retries, timeout = HOST_POLICY[group]
            c = HttpClient(min_interval=interval, max_retries=retries, timeout=timeout,
                           headers={"User-Agent": USER_AGENT},
                           backoff_base=10.0 if group == "arxiv" else 2.0,
                           logger=logging.getLogger(f"fulltext.http.{group}"))
            if group == "web":
                with self._lim_lock:
                    lim = self.web_limiters.setdefault(host, SharedLimiter(interval))
            else:
                lim = self.limiters[group]
            c.limiter = lim
            clients[key] = c
        return c

    def get(self, group: str, url: str, **kw: Any) -> requests.Response:
        if group == "arxiv":
            with self.gate:  # strictly serial: one arXiv request (incl. body) at a time
                self.arxiv_requests += 1
                return self.client("arxiv").get(url, **kw)
        host = urlparse(url).netloc.lower() if group == "web" else ""
        return self.client(group, host).get(url, **kw)

    def download_pdf(self, url: str, cache_key: str, group: str, att: Attempt,
                     headers: dict[str, str] | None = None) -> Path | None:
        path = PDF_CACHE / f"{safe_id(cache_key)}.pdf"
        if path.exists() and path.stat().st_size > 1000:
            with path.open("rb") as fh:
                if is_pdf(fh.read(1024)):
                    return path
        if att.seen(url):
            return None
        try:
            resp = self.get(group, url, headers=headers)
        except HttpError as exc:
            att.fail(url, str(exc)[:160])
            return None
        if resp.status_code != 200:
            att.fail(url, f"HTTP {resp.status_code}")
            return None
        body = resp.content
        if not is_pdf(body):
            att.fail(url, f"not a PDF ({resp.headers.get('Content-Type', '?')[:40]})")
            return None
        PDF_CACHE.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{threading.get_ident()}.part")
        tmp.write_bytes(body)
        os.replace(tmp, path)
        return path

    def pdf_doc(self, path: Path, source_used: str, url: str, att: Attempt) -> Doc | None:
        res = extract_pdf(path)
        if res.get("error") and not res.get("text"):
            att.fail(url, res["error"][:160])
            return None
        text = normalize_text(res.get("text") or "")
        m = re.search(r"arXiv:(\d{4}\.\d{4,5}v\d+|[a-z\-]+/\d{7}v\d+)", text[:20000])
        ref = f"arXiv:{m.group(1)}" if m and source_used.startswith("arxiv") else ""
        title = choose_pdf_title(res, text)
        text, _ = drop_references(text)
        text = text[:MAX_CHARS]
        if len(text) < MIN_CHARS_PAPER:
            att.fail(url, f"PDF text too short ({len(text)} chars; scanned or placeholder?)")
            return None
        return Doc(source_used, url, title, text, ref)

    def html_doc(self, url: str, group: str, source_used: str, att: Attempt, min_chars: int,
                 cache_key: str | None = None, papers: bool = False) -> Doc | None:
        """Fetch a URL; parse a PDF body as PDF and anything else as HTML."""
        cache = PDF_CACHE / f"{safe_id(cache_key)}.html" if cache_key else None
        final_url = url
        if cache and cache.exists() and cache.stat().st_size > 2000:
            html_str = cache.read_text(encoding="utf-8", errors="replace")
        else:
            if att.seen(url):
                return None
            try:
                resp = self.get(group, url)
            except HttpError as exc:
                att.fail(url, str(exc)[:160])
                return None
            if resp.status_code != 200:
                att.fail(url, f"HTTP {resp.status_code}")
                return None
            final_url = resp.url or url
            body = resp.content
            ctype = resp.headers.get("Content-Type", "").lower()
            if is_pdf(body) or "application/pdf" in ctype:
                if not is_pdf(body):
                    att.fail(url, "declared PDF but body is not a PDF")
                    return None
                key = "url__" + hashlib.sha1(url.encode()).hexdigest()[:16]
                path = PDF_CACHE / f"{key}.pdf"
                PDF_CACHE.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                return self.pdf_doc(path, source_used.replace("_html", "_pdf"), final_url, att)
            if ctype and not any(t in ctype for t in ("html", "xml", "text/plain")):
                att.fail(url, f"unsupported content type {ctype[:40]}")
                return None
            html_str = decode_html(resp)
            if cache:
                PDF_CACHE.mkdir(parents=True, exist_ok=True)
                cache.write_text(html_str, encoding="utf-8")
        if "<" in html_str[:2000]:
            title, text = html_to_text(html_str)
        else:
            title, text = "", normalize_text(html_str)
        if papers:
            text, _ = drop_references(text)
        text = text[:MAX_CHARS]
        if len(text) < min_chars:
            att.fail(url, f"page text too short ({len(text)} chars)")
            return None
        if not title:
            title = next((one_line(ln) for ln in text.split("\n") if len(ln.split()) >= 2), "")
        return Doc(source_used, final_url, title, text)

    # ---- routes ----------------------------------------------------------------------

    def via_arxiv(self, ax: str, att: Attempt) -> Doc | None:
        key = "arxiv__" + ax
        url = f"https://arxiv.org/pdf/{ax}"
        path = self.download_pdf(url, key, "arxiv", att)
        if path:
            doc = self.pdf_doc(path, "arxiv_pdf", url, att)
            if doc:
                return doc
        html_url = f"https://arxiv.org/html/{ax}"
        return self.html_doc(html_url, "arxiv", "arxiv_html", att, MIN_CHARS_PAPER,
                             cache_key=key, papers=True)

    def via_acl(self, acl_id: str, att: Attempt) -> Doc | None:
        url = f"https://aclanthology.org/{acl_id}.pdf"
        path = self.download_pdf(url, f"acl__{acl_id}", "acl", att)
        return self.pdf_doc(path, "acl_pdf", url, att) if path else None

    def openreview_token(self, base: str) -> str | None:
        with self._or_lock:
            if base in self._or_tokens:
                return self._or_tokens[base]
            token = None
            user, pw = self.env.get("OPENREVIEW_USERNAME"), self.env.get("OPENREVIEW_PASSWORD")
            if user and pw:
                try:
                    resp = self.client("openreview").request(
                        "POST", f"{base}/login", json_body={"id": user, "password": pw})
                    if resp.status_code == 200:
                        token = resp.json().get("token")
                    else:
                        log.warning("OpenReview login %s failed: HTTP %s", base, resp.status_code)
                except (HttpError, ValueError) as exc:
                    log.warning("OpenReview login %s failed: %r", base, exc)
            self._or_tokens[base] = token
            return token

    def via_openreview(self, forum: str, att: Attempt) -> Doc | None:
        for base in (API_OPENREVIEW_V2, API_OPENREVIEW_V1):
            token = self.openreview_token(base)
            headers = {"Authorization": f"Bearer {token}"} if token else None
            url = f"{base}/pdf?id={forum}"
            path = self.download_pdf(url, f"openreview__{forum}", "openreview", att, headers)
            if path:
                doc = self.pdf_doc(path, "openreview_pdf", f"https://openreview.net/pdf?id={forum}",
                                   att)
                if doc:
                    return doc
                break
        return None

    def via_pdf_url(self, url: str, source_used: str, att: Attempt) -> Doc | None:
        ax = arxiv_from_url(url)
        if ax:
            return self.via_arxiv(ax, att)
        key = "url__" + hashlib.sha1(url.encode()).hexdigest()[:16]
        path = self.download_pdf(url, key, "web", att)
        return self.pdf_doc(path, source_used, url, att) if path else None

    def s2_paper(self, key: str, att: Attempt) -> dict[str, Any] | None:
        url = S2_API + quote(key, safe=":/")
        try:
            resp = self.get("s2", url, params={"fields": "title,externalIds,openAccessPdf"},
                            headers=self.s2_headers or None)
        except HttpError as exc:
            att.fail(url, str(exc)[:160])
            return None
        if resp.status_code != 200:
            att.fail(url, f"HTTP {resp.status_code}")
            return None
        try:
            data = resp.json()
        except ValueError:
            att.fail(url, "bad JSON")
            return None
        att.s2_done = True  # S2 knows this paper; a second lookup by another id is redundant
        ext = data.get("externalIds") or {}
        oa = (data.get("openAccessPdf") or {}).get("url") or "-"
        att.note(url, f"S2: arXiv={ext.get('ArXiv') or '-'} DOI={ext.get('DOI') or '-'} "
                      f"oa_pdf={oa}")
        return data

    def openalex_work(self, key: str, att: Attempt) -> dict[str, Any] | None:
        url = OPENALEX_API + quote(key, safe=":/")
        params = {**self.openalex_params,
                  "select": "id,doi,title,best_oa_location,locations,ids"}
        try:
            resp = self.get("openalex", url, params=params)
        except HttpError as exc:
            att.fail(url, str(exc)[:160])
            return None
        if resp.status_code != 200:
            att.fail(url, f"HTTP {resp.status_code}")
            return None
        try:
            work = resp.json()
        except ValueError:
            att.fail(url, "bad JSON")
            return None
        pdfs = self.openalex_pdfs(work)
        att.note(url, f"OpenAlex: oa_pdfs={len(pdfs)} arXiv={self.openalex_arxiv(work) or '-'} "
                      f"doi={normalize_doi(work.get('doi')) or '-'}")
        return work

    @staticmethod
    def openalex_arxiv(work: dict[str, Any]) -> str | None:
        ax = arxiv_from_doi(normalize_doi(work.get("doi")))
        if ax:
            return ax
        for loc in work.get("locations") or []:
            for k in ("landing_page_url", "pdf_url"):
                ax = arxiv_from_url(loc.get(k))
                if ax:
                    return ax
        return None

    @staticmethod
    def openalex_pdfs(work: dict[str, Any]) -> list[str]:
        urls: list[str] = []
        best = (work.get("best_oa_location") or {}).get("pdf_url")
        if best:
            urls.append(best)
        for loc in work.get("locations") or []:
            u = loc.get("pdf_url")
            if u and u not in urls and loc.get("is_oa"):
                urls.append(u)
        return urls[:3]

    def try_s2_result(self, paper: dict[str, Any], att: Attempt, tried_ax: set[str]) -> Doc | None:
        ext = paper.get("externalIds") or {}
        ax = valid_arxiv_id(ext.get("ArXiv"))
        if ax and ax not in tried_ax:
            tried_ax.add(ax)
            doc = self.via_arxiv(ax, att)
            if doc:
                return doc
        oa = (paper.get("openAccessPdf") or {}).get("url")
        if oa:
            doc = self.via_pdf_url(oa, "s2_oa_pdf", att)
            if doc:
                return doc
        return None

    def via_doi(self, doi: str, att: Attempt, tried_ax: set[str]) -> Doc | None:
        """OpenAlex OA PDF -> S2 (arXiv id / OA PDF). The landing page is tried later."""
        work = self.openalex_work(f"doi:{doi}", att)
        oa_ax = None
        if work:
            for pdf_url in self.openalex_pdfs(work):
                ax = arxiv_from_url(pdf_url)
                if ax and ax in tried_ax:
                    continue
                if ax:
                    tried_ax.add(ax)
                doc = self.via_pdf_url(pdf_url, "openalex_oa_pdf", att)
                if doc:
                    return doc
            oa_ax = self.openalex_arxiv(work)
        paper = self.s2_paper(f"DOI:{doi}", att)
        if paper:
            doc = self.try_s2_result(paper, att, tried_ax)
            if doc:
                return doc
        if oa_ax and oa_ax not in tried_ax:
            tried_ax.add(oa_ax)
            return self.via_arxiv(oa_ax, att)
        return None

    # ---- GitHub ----------------------------------------------------------------------

    def gh_api(self, args: list[str]) -> Any:
        last = ""
        for attempt in range(4):
            try:
                proc = subprocess.run([self.gh, "api", *args], capture_output=True, timeout=120,
                                      env=self.git_env, check=False)
            except subprocess.TimeoutExpired:
                last = "gh api timeout"
                continue
            if proc.returncode == 0:
                return json.loads(proc.stdout.decode("utf-8", "replace") or "null")
            last = proc.stderr.decode("utf-8", "replace").strip()[:200]
            if "HTTP 404" in last or "Not Found" in last or "HTTP 451" in last:
                raise HttpError(f"gh api {args[0]}: {last}")
            if "rate limit" in last.lower() or "HTTP 403" in last or "HTTP 5" in last:
                time.sleep(30 * (attempt + 1))
                continue
            break
        raise HttpError(f"gh api {args[0]}: {last}")

    def latest_tag(self, owner: str, repo: str) -> tuple[str, str, str] | None:
        """(tag name, commit sha, date) of the latest tag dated on/before the cutoff.

        Tag date = tagger date for annotated tags, commit date for lightweight tags."""
        query = (
            "query($o:String!,$r:String!,$c:String){repository(owner:$o,name:$r){"
            "refs(refPrefix:\"refs/tags/\",first:100,after:$c,"
            "orderBy:{field:TAG_COMMIT_DATE,direction:DESC}){pageInfo{hasNextPage endCursor}"
            "nodes{name target{__typename oid ... on Commit{committedDate} ... on Tag{"
            "tagger{date} target{__typename oid ... on Commit{committedDate}}}}}}}}"
        )
        cursor = None
        best: tuple[str, str, str] | None = None
        for _page in range(10):
            args = ["graphql", "-f", f"query={query}", "-F", f"o={owner}", "-F", f"r={repo}"]
            if cursor:
                args += ["-F", f"c={cursor}"]
            data = self.gh_api(args)
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
                if not sha or not date:
                    continue
                d = date[:10]
                if d <= CUTOFF_DATE and (best is None or date > best[2]):
                    best = (node["name"], sha, date)
            if best is not None:
                return best
            info = refs.get("pageInfo") or {}
            if not info.get("hasNextPage"):
                return None
            cursor = info.get("endCursor")
        return best

    def git(self, *args: str, cwd: Path | None = None, timeout: int = 600) -> str:
        cmd = ["git", "-c", "core.longpaths=true", "-c", "advice.detachedHead=false",
               "-c", "core.quotePath=false"]
        if cwd is not None:
            cmd += ["-C", str(cwd)]
        proc = subprocess.run([*cmd, *args], capture_output=True, timeout=timeout,
                              env=self.git_env, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"git {args[0]}: {proc.stderr.decode('utf-8', 'replace')[-300:]}")
        return proc.stdout.decode("utf-8", "replace")

    @staticmethod
    def _rmtree(path: Path) -> None:
        def onexc(func: Any, p: str, _exc: Any) -> None:
            os.chmod(p, stat.S_IWRITE)
            func(p)

        if path.exists():
            shutil.rmtree(path, onexc=onexc)

    def clone(self, full_name: str, tag: str | None, sha: str, subpath: str) -> Path:
        """Shallow (depth 1), blobless clone at the pinned ref; only README*, docs/**/*.md(x)
        and the URL's subpath are checked out (sparse). ``git sparse-checkout disable``
        inside the clone hydrates the full tree when the code itself is needed."""
        dest = REPO_CACHE / full_name.replace("/", "__")
        if dest.exists():
            try:
                if self.git("rev-parse", "HEAD", cwd=dest).strip() == sha:
                    self._sparse(dest, subpath)
                    return dest
            except RuntimeError:
                pass
            self._rmtree(dest)
        REPO_CACHE.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/{full_name}.git"
        if tag:
            self.git("clone", "-q", "--depth", "1", "--branch", tag, "--filter=blob:none",
                     "--no-checkout", url, str(dest))
        else:
            self.git("init", "-q", str(dest))
            self.git("remote", "add", "origin", url, cwd=dest)
            self.git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", sha, cwd=dest)
            self.git("update-ref", "--no-deref", "HEAD", sha, cwd=dest)
        self._sparse(dest, subpath)
        return dest

    def _sparse(self, dest: Path, subpath: str) -> None:
        patterns = ["/README*", "/readme*", "/Readme*", "/docs/*.md", "/docs/**/*.md",
                    "/docs/*.mdx", "/docs/**/*.mdx", "/doc/*.md", "/doc/**/*.md"]
        if subpath:
            sp = subpath.strip("/")
            patterns += [f"/{sp}/README*", f"/{sp}/readme*", f"/{sp}/*.md"]
        self.git("config", "core.sparseCheckout", "true", cwd=dest)
        self.git("config", "core.sparseCheckoutCone", "false", cwd=dest)
        info = dest / ".git" / "info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "sparse-checkout").write_text("\n".join(patterns) + "\n", encoding="utf-8")
        self.git("read-tree", "-mu", "HEAD", cwd=dest)

    def via_github(self, owner: str, repo: str, subpath: str, att: Attempt) -> Doc | None:
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        if att.seen(api_url):
            return None
        try:
            info = self.gh_api([f"repos/{owner}/{repo}"])
        except HttpError as exc:
            att.fail(api_url, str(exc)[:160])
            return None
        full = info.get("full_name") or f"{owner}/{repo}"
        default = info.get("default_branch") or "main"
        o, r = full.split("/", 1)
        try:
            tag = self.latest_tag(o, r)
        except HttpError as exc:
            att.fail(f"graphql tags {full}", str(exc)[:160])
            tag = None
        if tag:
            tag_name, sha, date = tag
            ref_used = f"tag:{tag_name} {sha} {date[:10]}"
        else:
            try:
                commits = self.gh_api(
                    [f"repos/{full}/commits?sha={quote(default)}&until={CUTOFF_TS}&per_page=1"])
            except HttpError as exc:
                att.fail(f"{api_url}/commits", str(exc)[:160])
                return None
            if not commits:
                att.fail(f"{api_url}/commits", f"no commit on {default} on/before {CUTOFF_DATE}")
                return None
            tag_name = None
            sha = commits[0]["sha"]
            date = ((commits[0].get("commit") or {}).get("committer") or {}).get("date") or ""
            ref_used = f"commit:{default} {sha} {date[:10]}"
        try:
            dest = self.clone(full, tag_name, sha, subpath)
            tree = [p for p in self.git("ls-tree", "-r", "--name-only", "HEAD", cwd=dest)
                    .splitlines() if p]
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            att.fail(f"https://github.com/{full}.git", f"clone failed: {str(exc)[:160]}")
            return None
        text = self.repo_bundle(dest, full, info, ref_used, tree, subpath)
        if len(text) < MIN_CHARS_WEB:
            att.fail(f"https://github.com/{full}", f"repo bundle too short ({len(text)} chars)")
            return None
        ref_name = tag_name or sha
        return Doc("github_repo", f"https://github.com/{full}/tree/{ref_name}", full,
                   text[:MAX_CHARS], ref_used)

    @staticmethod
    def _read(p: Path) -> str:
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def repo_bundle(self, dest: Path, full: str, info: dict[str, Any], ref_used: str,
                    tree: list[str], subpath: str) -> str:
        out = [f"# {full}", f"ref: {ref_used}",
               f"description: {one_line(info.get('description'), 1000)}",
               f"topics: {', '.join(info.get('topics') or [])}", ""]
        readmes = sorted((p for p in tree if "/" not in p and p.lower().startswith("readme")),
                         key=lambda p: (not p.lower().endswith((".md", ".markdown")),
                                        p.lower() != "readme.md", len(p)))
        if readmes:
            body = normalize_text(self._read(dest / readmes[0]))[:README_CAP]
            out += [f"## README ({readmes[0]})", body, ""]
        if subpath:
            sp = subpath.strip("/")
            sub = [p for p in tree if p.startswith(sp + "/") and "/" not in p[len(sp) + 1:]
                   and p.lower().split("/")[-1].startswith("readme")]
            if sub:
                body = normalize_text(self._read(dest / sub[0]))[:README_CAP]
                out += [f"## Subpath README ({sub[0]})", body, ""]
        docs = [p for p in tree if re.match(r"^docs?/.+\.mdx?$", p, re.IGNORECASE)]
        docs.sort(key=lambda p: (p.count("/"), not re.search(r"(index|readme|overview|intro)",
                                                             p, re.IGNORECASE), p.lower()))
        budget = DOCS_CAP
        doc_parts: list[str] = []
        for p in docs:
            if budget <= 0:
                break
            body = normalize_text(self._read(dest / p))
            if not body:
                continue
            chunk = f"### {p}\n{body}"[:budget]
            doc_parts.append(chunk)
            budget -= len(chunk)
        if doc_parts:
            out += [f"## docs (first {DOCS_CAP} chars of {len(docs)} files)", *doc_parts, ""]
        out += [f"## File tree (first {min(TREE_CAP, len(tree))} of {len(tree)} paths)",
                *tree[:TREE_CAP]]
        return "\n".join(out).strip()

    # ---- orchestration ---------------------------------------------------------------

    def fetch(self, it: Item) -> tuple[Doc | None, Attempt]:
        """Try every applicable route in order; the first document that parses wins."""
        att = Attempt()
        tried_ax: set[str] = set()
        for step in self._steps(it, att, tried_ax):
            doc = step()
            if doc is not None:
                return doc, att
        if not att.tried:
            if it.url and not valid_web_url(it.url):
                att.fail(it.url, "invalid or truncated URL")
            else:
                att.fail("-", "no identifier (no arXiv id, DOI, ACL/OpenReview/S2/OpenAlex id,"
                              " GitHub repo or URL); not fetched by title")
        return None, att

    def _arxiv_once(self, ax: str | None, att: Attempt, tried_ax: set[str]) -> Doc | None:
        if not ax or ax in tried_ax:
            return None
        tried_ax.add(ax)
        return self.via_arxiv(ax, att)

    def _s2_by_id(self, s2_id: str, it: Item, att: Attempt, tried_ax: set[str]) -> Doc | None:
        """S2 record without a DOI: arXiv id / OA PDF from S2, then the DOI route."""
        paper = self.s2_paper(s2_id, att)
        if not paper:
            return None
        doc = self.try_s2_result(paper, att, tried_ax)
        if doc:
            return doc
        new_doi = normalize_doi((paper.get("externalIds") or {}).get("DOI"))
        if new_doi and not arxiv_from_doi(new_doi):
            it.doi = new_doi
            return self.via_doi(new_doi, att, tried_ax)
        return None

    def _openalex_by_id(self, wid: str, it: Item, att: Attempt,
                        tried_ax: set[str]) -> Doc | None:
        """OpenAlex record without a DOI: arXiv location / OA PDF, then S2 by its DOI."""
        work = self.openalex_work(wid, att)
        if not work:
            return None
        doc = self._arxiv_once(self.openalex_arxiv(work), att, tried_ax)
        if doc:
            return doc
        for pdf_url in self.openalex_pdfs(work):
            doc = self.via_pdf_url(pdf_url, "openalex_oa_pdf", att)
            if doc:
                return doc
        new_doi = normalize_doi(work.get("doi"))
        if new_doi and not arxiv_from_doi(new_doi):
            it.doi = new_doi
            paper = self.s2_paper(f"DOI:{new_doi}", att)
            if paper:
                return self.try_s2_result(paper, att, tried_ax)
        return None

    def _steps(self, it: Item, att: Attempt, tried_ax: set[str]) -> list[Any]:
        """Ordered route closures: the record's own identifiers first, then its cluster's
        identifiers from candidates.csv, then landing pages (rarely more than an abstract)."""
        steps: list[Any] = []
        web_source = it.source in WEB_SOURCES or it.prefix in WEB_SOURCES
        url_host = urlparse(it.url).netloc.lower() if valid_web_url(it.url) else ""
        # 1. own arXiv id
        steps.append(lambda: self._arxiv_once(it.arxiv_id, att, tried_ax))
        # 2. ACL Anthology
        acl = acl_id_of(it.url, it.doi)
        if acl:
            steps.append(lambda: self.via_acl(acl, att))
        # 3. OpenReview
        if it.prefix == "openreview":
            steps.append(lambda: self.via_openreview(it.local_id, att))
        # 4. GitHub repository
        repo = github_repo_of(it.url)
        if repo is None and it.prefix == "github" and "/" in it.local_id:
            owner, name = it.local_id.split("/", 1)
            repo = (owner, name, "")
        if repo:
            steps.append(lambda: self.via_github(repo[0], repo[1], repo[2], att))
        # 5. own DOI: OpenAlex OA PDF -> S2 (arXiv id / OA PDF)
        if it.doi and not arxiv_from_doi(it.doi):
            own_doi = it.doi
            steps.append(lambda: self.via_doi(own_doi, att, tried_ax))
        # 6. S2 / OpenAlex records without a DOI: look up arXiv id / DOI / OA PDF
        s2_id = it.local_id if it.prefix in ("s2", "s2_snowball") else None
        if s2_id is None and "semanticscholar.org/paper/" in it.url:
            s2_id = it.url.rstrip("/").split("/")[-1]
        if s2_id and re.fullmatch(r"[0-9a-f]{40}", s2_id) and not it.doi:
            steps.append(lambda: None if att.s2_done else self._s2_by_id(s2_id, it, att,
                                                                           tried_ax))
        if it.prefix == "openalex" and re.fullmatch(r"W\d+", it.local_id) and not it.doi:
            steps.append(lambda: self._openalex_by_id(it.local_id, it, att, tried_ax))
        # 7. web sources: the page itself
        fallback_ok = url_host and not repo and not any(h in url_host
                                                        for h in NO_WEB_FALLBACK_HOSTS)
        if web_source and fallback_ok:
            steps.append(lambda: self.html_doc(it.url, "web", "web_html", att, MIN_CHARS_WEB))
        # 8. cluster-level identifiers (may belong to another paper; fetched_title shows it)
        if it.cluster_arxiv:
            steps.append(lambda: self._arxiv_once(it.cluster_arxiv, att, tried_ax))
        if it.cluster_doi and not arxiv_from_doi(it.cluster_doi):
            c_doi = it.cluster_doi
            c_acl = acl_id_of(None, c_doi)
            if c_acl and c_acl != acl:
                steps.append(lambda: self.via_acl(c_acl, att))
            steps.append(lambda: self.via_doi(c_doi, att, tried_ax))
        # 9. landing pages, last resort
        steps.append(lambda: self._landing(it.doi, att))
        if fallback_ok and not web_source:
            steps.append(lambda: self.html_doc(it.url, "web", "landing_html", att,
                                               MIN_CHARS_LANDING, papers=True))
        if it.cluster_doi:
            steps.append(lambda: self._landing(it.cluster_doi, att))
        return steps

    def _landing(self, doi: str | None, att: Attempt) -> Doc | None:
        if not doi or arxiv_from_doi(doi):
            return None
        return self.html_doc(f"https://doi.org/{doi}", "web", "doi_landing_html", att,
                             MIN_CHARS_LANDING, papers=True)


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------


class Sink:
    """Append-and-flush writer for the .txt files, the index and the failure list."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        self.index_fh = self._open(INDEX_CSV, INDEX_FIELDS)
        self.fail_fh = self._open(NOT_RETRIEVABLE_CSV, FAIL_FIELDS)
        self.index = csv.DictWriter(self.index_fh, fieldnames=INDEX_FIELDS)
        self.fails = csv.DictWriter(self.fail_fh, fieldnames=FAIL_FIELDS)

    @staticmethod
    def _open(path: Path, fields: list[str]) -> Any:
        new = not path.exists() or path.stat().st_size == 0
        fh = path.open("a", encoding="utf-8", errors="replace", newline="")
        if new:
            csv.writer(fh).writerow(fields)
            fh.flush()
        return fh

    @staticmethod
    def _sync(fh: Any) -> None:
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass

    def ok(self, it: Item, doc: Doc) -> None:
        at = now_utc()
        header = [
            f"record_id: {it.record_id}",
            f"source_used: {doc.source_used}",
            f"fetched_url: {doc.fetched_url}",
            f"fetched_title: {one_line(doc.title)}",
            f"fetched_at: {at}",
        ]
        path = OUT_DIR / f"{safe_id(it.record_id)}.txt"
        tmp = path.with_suffix(f".{threading.get_ident()}.tmp")
        tmp.write_text("\n".join(header) + "\n\n" + doc.text + "\n", encoding="utf-8",
                       errors="replace")
        os.replace(tmp, path)
        row = {"record_id": it.record_id, "status": "ok", "source_used": doc.source_used,
               "fetched_url": doc.fetched_url, "fetched_title": one_line(doc.title),
               "chars": len(doc.text), "ref_used": doc.ref_used, "fetched_at": at}
        with self.lock:
            self.index.writerow(row)
            self._sync(self.index_fh)

    def fail(self, it: Item, att: Attempt, reason: str | None = None) -> None:
        at = now_utc()
        tried = att.tried or ["-"]
        reason = reason or att.reason()
        with self.lock:
            self.index.writerow({"record_id": it.record_id, "status": "not_retrievable",
                                 "source_used": "", "fetched_url": "", "fetched_title": "",
                                 "chars": 0, "ref_used": "", "fetched_at": at})
            self._sync(self.index_fh)
            self.fails.writerow({"record_id": it.record_id, "source": it.source,
                                 "reason": reason[:300], "urls_tried": " | ".join(tried),
                                 "attempted_at": at})
            self._sync(self.fail_fh)

    def close(self) -> None:
        self.index_fh.close()
        self.fail_fh.close()


def read_index() -> list[dict[str, str]]:
    if not INDEX_CSV.exists():
        return []
    with INDEX_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def select_ids(args: argparse.Namespace) -> list[str]:
    if args.ids_file:
        ids = read_ids(Path(args.ids_file))
    else:
        pilot = read_ids(PILOT_CSV)
        ids = list(pilot)
        if not args.only_pilot:
            seen = set(pilot)
            ids += [i for i in read_ids(QUEUE_CSV) if i not in seen]
    out: list[str] = []
    seen2: set[str] = set()
    for i in ids:
        if i not in seen2:
            seen2.add(i)
            out.append(i)
    return out


def _squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def title_in_text(record_id: str, title: str) -> bool:
    """True if the candidate title occurs (space/punctuation-insensitive, partial_ratio >= 90)
    in the first 5,000 characters of the fetched text (after the 5-line header)."""
    from rapidfuzz import fuzz

    path = OUT_DIR / f"{safe_id(record_id)}.txt"
    if not path.exists() or len(_squash(title)) < 8:
        return False
    body = path.read_text(encoding="utf-8", errors="replace").split("\n\n", 1)[-1]
    return fuzz.partial_ratio(_squash(title), _squash(body[:5000])) >= 90


def summarize(ids: Iterable[str]) -> None:
    """Counts by candidate source and status (latest index row per id), median chars, and
    fetched titles that differ from the candidate title (token_set_ratio < 70)."""
    from rapidfuzz import fuzz, utils

    ids = list(ids)
    wanted = set(ids)
    latest: dict[str, dict[str, str]] = {}
    for r in read_index():
        latest[r["record_id"]] = r
    with CANDIDATES_CSV.open(encoding="utf-8", newline="") as fh:
        cand = {r["id"]: r for r in csv.DictReader(fh) if r["id"] in wanted}
    mism = set()
    if MISMATCH_CSV.exists():
        with MISMATCH_CSV.open(encoding="utf-8", newline="") as fh:
            mism = {r["record_id"] for r in csv.DictReader(fh)}
    tab: Counter[tuple[str, str]] = Counter()
    used: Counter[str] = Counter()
    chars: list[int] = []
    differ: list[tuple[str, float, str, str, bool, bool]] = []
    for i in ids:
        row = latest.get(i)
        src = (cand.get(i) or {}).get("source", "?")
        status = row["status"] if row else "pending"
        tab[(src, status)] += 1
        if row and status == "ok":
            used[row["source_used"]] += 1
            chars.append(int(row["chars"] or 0))
            ct = (cand.get(i) or {}).get("title", "")
            ft = row["fetched_title"]
            score = fuzz.token_set_ratio(ct, ft, processor=utils.default_process)
            if score < 70:
                differ.append((i, score, ct, ft, i in mism, title_in_text(i, ct)))
    sources = sorted({s for s, _ in tab})
    print(f"{'source':<14}{'ok':>7}{'not_retr':>10}{'pending':>9}")
    for s in sources:
        print(f"{s:<14}{tab[(s, 'ok')]:>7}{tab[(s, 'not_retrievable')]:>10}{tab[(s, 'pending')]:>9}")
    tot: Counter[str] = Counter()
    for (_s, st), n in tab.items():
        tot[st] += n
    print(f"{'TOTAL':<14}{tot['ok']:>7}{tot['not_retrievable']:>10}{tot['pending']:>9}")
    print("source_used:", dict(used.most_common()))
    if chars:
        print(f"median chars (ok): {statistics.median(chars):,.0f}")
    print(f"fetched title differs from candidate title (token_set_ratio < 70): {len(differ)}"
          f" ({sum(d[4] for d in differ)} listed in metadata_mismatch.csv; candidate title found"
          f" in the first 5k chars of the fetched text for {sum(d[5] for d in differ)}, i.e."
          f" title-extraction misses rather than a different document)")
    for i, score, ct, ft, m, found in sorted(differ, key=lambda d: (d[5], d[1])):
        flags = (" MISMATCH-LIST" if m else "") + (" title-in-text" if found else " DIFFERENT-DOC?")
        print(f"  {i} [{score:.0f}{flags}]\n"
              f"      candidate: {one_line(ct, 110)}\n      fetched:   {one_line(ft, 110)}")


def run(args: argparse.Namespace) -> int:
    ids = select_ids(args)
    done: set[str] = set()
    for r in read_index():
        if r["status"] == "ok" or (args.skip_failed and r["status"] == "not_retrievable"):
            done.add(r["record_id"])
    todo = [i for i in ids if i not in done]
    n_done = len(ids) - len(todo)
    if args.limit:
        todo = todo[: args.limit]
    log.info("selected %d ids; %d already done; %d to fetch", len(ids), n_done, len(todo))
    if not todo:
        return 0
    items = load_items(todo)
    fetcher = Fetcher(load_env())
    sink = Sink()
    stats: Counter[str] = Counter()
    n_ax = sum(1 for i in items.values() if i.arxiv_id)
    log.info("arXiv stream: %d records; other stream: %d records", n_ax, len(items) - n_ax)
    start = time.monotonic()

    def process(it: Item) -> tuple[str, str]:
        try:
            doc, att = fetcher.fetch(it)
        except Exception as exc:  # one bad record must not stop the run
            log.exception("error on %s", it.record_id)
            att = Attempt()
            att.fail("-", f"error: {type(exc).__name__}: {str(exc)[:150]}")
            doc = None
        if doc is not None:
            try:
                sink.ok(it, doc)
                return "ok", doc.source_used
            except Exception as exc:  # e.g. an unwritable character; record, keep going
                log.exception("could not write %s", it.record_id)
                att.fail(doc.fetched_url, f"write error: {type(exc).__name__}: {str(exc)[:120]}")
        sink.fail(it, att)
        return "not_retrievable", it.source

    ax_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="arxiv")
    gen_pool = ThreadPoolExecutor(max_workers=args.workers, thread_name_prefix="other")
    futures = {}
    for it in items.values():
        pool = ax_pool if it.arxiv_id else gen_pool
        futures[pool.submit(process, it)] = it
    try:
        for n, fut in enumerate(as_completed(futures), 1):
            try:
                status, what = fut.result()
            except Exception:  # never let one future end the run (and the interpreter)
                log.exception("unhandled error on %s", futures[fut].record_id)
                status, what = "error", futures[fut].source
            stats[status] += 1
            stats[f"{status}:{what}"] += 1
            if n % 25 == 0 or n == len(futures):
                el = time.monotonic() - start
                log.info("progress %d/%d ok=%d fail=%d arxiv_requests=%d elapsed=%.0fs "
                         "rate=%.2f rec/min eta=%.0f min", n, len(futures), stats["ok"],
                         stats["not_retrievable"], fetcher.arxiv_requests, el, 60 * n / el,
                         (len(futures) - n) * el / n / 60)
    except KeyboardInterrupt:
        log.warning("interrupted; finished records are saved, re-run to resume")
        ax_pool.shutdown(wait=False, cancel_futures=True)
        gen_pool.shutdown(wait=False, cancel_futures=True)
        sink.close()
        return 130
    ax_pool.shutdown()
    gen_pool.shutdown()
    sink.close()
    el = time.monotonic() - start
    log.info("done: %d records in %.0fs (%.1f s/record); %s", len(futures), el,
             el / max(1, len(futures)), dict(sorted(stats.items())))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--only-pilot", action="store_true", help="fetch only fulltext_pilot.csv")
    p.add_argument("--ids-file", help="CSV with a record_id column (or one id per line)")
    p.add_argument("--limit", type=int, default=0, help="fetch at most N records this run")
    p.add_argument("--skip-failed", action="store_true",
                   help="also skip ids already recorded as not_retrievable")
    p.add_argument("--workers", type=int, default=4, help="non-arXiv thread pool size (4)")
    p.add_argument("--summary", action="store_true",
                   help="print counts for the selected ids from the index and exit")
    p.add_argument("--log-level", default="INFO")
    p.add_argument("--candidates", help="candidate table to resolve ids against; defaults to the "
                                       "frozen data/raw/candidates.csv. The supplementary arm "
                                       "(amendment 7) passes candidates_plus_supp.csv so the frozen "
                                       "harvest stays untouched")
    p.add_argument("--_extract-pdf", dest="extract_pdf", help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.candidates:
        global CANDIDATES_CSV
        CANDIDATES_CSV = Path(args.candidates)

    if args.extract_pdf:
        sys.stdout.write(json.dumps(_pdf_worker(args.extract_pdf), ensure_ascii=True))
        return 0
    if args.summary:
        summarize(select_ids(args))
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(threadName)s %(name)s: %(message)s",
                            "%H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in (logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")):
        h.setFormatter(fmt)
        root.addHandler(h)
    log.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
