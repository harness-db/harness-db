"""Shared helpers for the HARNESS-Review harvesting scripts.

Every harvester in this package imports from here:

* the protocol search blocks (``HARNESS_TERMS``, ``LLM_TERMS``) and regexes built from them
  for local title+abstract filtering;
* a common CLI (``build_parser``) with ``--since/--until/--out/--count-only/--max-records``;
* ``HttpClient`` (rate limiting, retries with exponential backoff, ``Retry-After`` support);
* ``Record`` (the JSONL schema) and ``JsonlWriter``;
* small utilities (arXiv id / DOI normalisation, ISO timestamps, summary printing).

Nothing here has import-time side effects beyond defining constants.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import random
import re
import time
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import requests

# --------------------------------------------------------------------------------------
# Protocol constants (docs/protocol_prisma_p.md section 6; plan section 3.1)
# --------------------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
CACHE_DIR = RAW_DIR / "cache"

DEFAULT_SINCE = "2022-10-01"
DEFAULT_UNTIL = "2026-08-31"
DEFAULT_MAX_RECORDS = 0  # 0 = unlimited (freeze run); the test run used 5000

USER_AGENT = "harness-db-harvest/0.1 (https://github.com/harness-db/harness-db; mailto:gurrambhaskar.ai@gmail.com)"
CONTACT_EMAIL = "gurrambhaskar.ai@gmail.com"

#: Harness block, verbatim from the protocol (v2, 2026-09-16; docs/protocol_prisma_p.md
#: section 6 and the Amendments table). ``*`` marks a wildcard (``scaffold*``, ``agent*``).
HARNESS_TERMS: tuple[str, ...] = (
    "agent harness",
    "harness",
    "agent scaffold*",
    "agentic framework",
    "agent framework",
    "LLM agent*",
    "LM agent*",
    "language agent*",
    "AI agent*",
    "computer agent*",
    "multi-agent",
    "tool-use agent",
    "coding agent",
    "software engineering agent",
    "computer-use agent",
    "GUI agent",
    "web agent",
    "multi-agent framework",
    "agent orchestration",
    "LLM orchestration",
)

#: LLM block, verbatim from the protocol.
LLM_TERMS: tuple[str, ...] = (
    "large language model",
    "LLM",
    "foundation model",
    "language model agent",
)

#: Optional structure block (precision only; protocol section 6: "optional structure block for
#: precision on the two largest sources"). ANDed in when a script is run with
#: ``--with-structure-block``; in the freeze run that flag is used on S2 and OpenAlex only.
STRUCTURE_TERMS: tuple[str, ...] = (
    "tool call*",
    "function call*",
    "control loop",
    "context management",
    "memory",
    "sandbox",
    "verification",
    "retry",
    "planning",
)

#: Proposal v3 (measured at search freeze, NOT part of the protocol unless the Amendments
#: table says so): "strong" harness terms whose presence waives the LLM block
#: (``--waive-llm-on-strong``). Deliberately excludes bare ``harness`` (test/wiring harness
#: noise) and ``multi-agent`` / ``AI agent*`` / ``LLM agent*`` (too broad or already imply LLM).
STRONG_TERMS: tuple[str, ...] = (
    "agent harness*",
    "agentic harness*",
    "coding agent*",
    "agent scaffold*",
    "agentic scaffold*",
    "software engineering agent*",
    "computer-use agent*",
    "GUI agent*",
    "web agent*",
)

ARXIV_CATEGORIES: tuple[str, ...] = ("cs.AI", "cs.CL", "cs.SE", "cs.LG")


def expand_wildcards(term: str) -> list[str]:
    """Expand a protocol term with a trailing ``*`` into explicit variants.

    Sources whose query language has no phrase-internal wildcard (S2) get every variant;
    sources that stem server-side (arXiv, OpenAlex) take only the first one (the stem).
    ``scaffold*`` -> ``scaffold``, ``scaffolding``, ``scaffolds``; ``agent*`` -> ``agent``,
    ``agents``; ``call*`` -> ``call``, ``calls``, ``calling``. Terms without ``*`` are
    returned unchanged. The expansion is documented in ``scripts/harvest/README.md``.
    """
    if not term.endswith("*"):
        return [term]
    stem = term[:-1]
    if stem.endswith("agent"):
        return [stem, stem + "s"]
    if stem.endswith("harness"):
        return [stem, stem + "es"]
    if stem.endswith("call"):
        return [stem, stem + "s", stem + "ing"]
    return [stem, stem + "ing", stem + "s"]


def _term_regex(term: str) -> str:
    """Translate a protocol term into a regex fragment (case-insensitive use).

    Hyphen and whitespace inside phrases match any run of whitespace/hyphen so that
    "tool-use agent" also matches "tool use agent" and "computer-use agent" matches
    "computer use agent". Trailing ``*`` becomes ``\\w*``. A trailing ``s`` is allowed on the
    last word (plural tolerance) for every term, which is what the search engines' stemming
    does server-side.
    """
    words = re.split(r"[\s-]+", term.strip())
    parts: list[str] = []
    for i, w in enumerate(words):
        if w.endswith("*"):
            parts.append(re.escape(w[:-1]) + r"\w*")
        elif i == len(words) - 1:
            parts.append(re.escape(w) + r"s?")
        else:
            parts.append(re.escape(w))
    return r"\b" + r"[\s\-]+".join(parts) + r"\b"


def block_regex(terms: Iterable[str]) -> re.Pattern[str]:
    """Compile a case-insensitive regex that matches if ANY of the block's terms occurs."""
    return re.compile("|".join(f"(?:{_term_regex(t)})" for t in terms), re.IGNORECASE)


HARNESS_RE: re.Pattern[str] = block_regex(HARNESS_TERMS)
LLM_RE: re.Pattern[str] = block_regex(LLM_TERMS)
STRUCTURE_RE: re.Pattern[str] = block_regex(STRUCTURE_TERMS)
STRONG_RE: re.Pattern[str] = block_regex(STRONG_TERMS)


def matches_blocks(text: str, with_structure: bool = False, waive_llm_on_strong: bool = False) -> bool:
    """True if ``text`` matches the harness block AND the LLM block (AND, optionally, the
    structure block). With ``waive_llm_on_strong`` (proposal v3) a text that contains a
    strong harness term (``STRONG_RE``) is accepted even when the LLM block does not match:
    ``(HARNESS and LLM) or STRONG``."""
    ok = bool(HARNESS_RE.search(text)) and bool(LLM_RE.search(text))
    if not ok and waive_llm_on_strong:
        ok = bool(STRONG_RE.search(text))
    if ok and with_structure:
        ok = bool(STRUCTURE_RE.search(text))
    return ok


# --------------------------------------------------------------------------------------
# Record schema
# --------------------------------------------------------------------------------------


@dataclass
class Record:
    """One harvested candidate. Written as one JSON object per line."""

    id: str  # "<source>:<source_id>"
    source: str  # arxiv | s2 | openalex | openreview | acl | github
    source_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    date: str | None = None  # ISO date (YYYY-MM-DD) or YYYY / YYYY-MM when that is all we have
    venue: str | None = None
    url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    categories: list[str] = field(default_factory=list)
    query_used: str = ""
    retrieved_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)  # source-specific (stars, readme ...)

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> Record:
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


_ARXIV_ID_RE = re.compile(r"(?:(?:arxiv\.org/(?:abs|pdf)/)|(?:arxiv:))?(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE)
_ARXIV_OLD_RE = re.compile(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?", re.IGNORECASE)


def normalize_arxiv_id(value: str | None) -> str | None:
    """Return a bare, version-less arXiv id (e.g. ``2405.15793``) or None."""
    if not value:
        return None
    m = _ARXIV_ID_RE.search(value)
    if m:
        return m.group(1)
    m = _ARXIV_OLD_RE.search(value)
    if m:
        return m.group(1)
    return None


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v)
    v = re.sub(r"^doi:\s*", "", v)
    return v or None


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace (used for dedupe)."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def within(date: str | None, since: str, until: str) -> bool:
    """Compare ISO-ish date strings lexicographically. Missing date -> True (keep)."""
    if not date:
        return True
    d = date[:10]
    if len(d) == 4:  # year only
        return since[:4] <= d <= until[:4]
    if len(d) == 7:  # year-month
        return since[:7] <= d <= until[:7]
    return since <= d <= until


# --------------------------------------------------------------------------------------
# HTTP client with rate limiting and retries
# --------------------------------------------------------------------------------------


class HttpError(RuntimeError):
    """Raised when a request keeps failing after all retries."""


class RateLimiter:
    """Enforces a minimum interval between calls (seconds)."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()


class HttpClient:
    """Small ``requests`` wrapper: fixed pacing, retries with exponential backoff.

    Retries on connection errors, timeouts, HTTP 429 and 5xx. Honours ``Retry-After``.
    """

    def __init__(
        self,
        min_interval: float = 1.0,
        max_retries: int = 6,
        timeout: float = 60.0,
        headers: Mapping[str, str] | None = None,
        backoff_base: float = 2.0,
        backoff_cap: float = 120.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, **(headers or {})})
        self.limiter = RateLimiter(min_interval)
        self.max_retries = max_retries
        self.timeout = timeout
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.log = logger or logging.getLogger("harvest.http")
        self.requests_made = 0

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json_body: Any = None,
        stream: bool = False,
        retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
    ) -> requests.Response:
        attempt = 0
        while True:
            self.limiter.wait()
            self.requests_made += 1
            try:
                resp = self.session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    json=json_body,
                    timeout=self.timeout,
                    stream=stream,
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt >= self.max_retries:
                    raise HttpError(f"{method} {url}: {exc!r} after {attempt} retries") from exc
                delay = self._delay(attempt)
                self.log.warning("network error %r; retry %d in %.1fs", exc, attempt + 1, delay)
                time.sleep(delay)
                attempt += 1
                continue
            if resp.status_code in retry_statuses:
                if attempt >= self.max_retries:
                    raise HttpError(
                        f"{method} {url}: HTTP {resp.status_code} after {attempt} retries: "
                        f"{resp.text[:300]!r}"
                    )
                delay = self._delay(attempt, resp.headers.get("Retry-After"))
                self.log.warning("HTTP %s; retry %d in %.1fs", resp.status_code, attempt + 1, delay)
                time.sleep(delay)
                attempt += 1
                continue
            return resp

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def get_json(self, url: str, **kwargs: Any) -> Any:
        resp = self.get(url, **kwargs)
        if resp.status_code != 200:
            raise HttpError(f"GET {url}: HTTP {resp.status_code}: {resp.text[:300]!r}")
        return resp.json()

    def _delay(self, attempt: int, retry_after: str | None = None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), self.backoff_cap) + random.uniform(0, 1)
            except ValueError:
                pass
        return min(self.backoff_base * (2**attempt), self.backoff_cap) + random.uniform(0, 1)


# --------------------------------------------------------------------------------------
# JSONL I/O
# --------------------------------------------------------------------------------------


class JsonlWriter:
    """Writer that truncates the target on open (or appends with ``append=True``, in which
    case the ids already in the file are loaded so they are not written twice), one JSON
    object per line. ``count`` counts records written by this writer only.

    In ``count_only`` mode nothing is written but records are still counted.
    """

    def __init__(self, path: Path | str | None, count_only: bool = False, append: bool = False) -> None:
        self.path = Path(path) if path else None
        self.count_only = count_only or self.path is None
        self.append = append
        self.count = 0
        self._fh = None
        self._seen: set[str] = set()

    def __enter__(self) -> Self:
        if not self.count_only and self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.append and self.path.exists():
                self._seen = {r["id"] for r in read_jsonl(self.path)}
            self._fh = self.path.open("a" if self.append else "w", encoding="utf-8")
        return self

    def __exit__(self, *exc: object) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    def write(self, rec: Record) -> bool:
        """Write a record unless its ``id`` was already written. Returns True if written."""
        if rec.id in self._seen:
            return False
        self._seen.add(rec.id)
        self.count += 1
        if self._fh:
            self._fh.write(rec.to_json() + "\n")
        return True


def read_jsonl(path: Path | str) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def build_parser(source: str, description: str, structure_block: bool = False) -> argparse.ArgumentParser:
    """Common CLI. ``structure_block=True`` adds ``--with-structure-block`` (S2, OpenAlex)."""
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--since", default=DEFAULT_SINCE, help="inclusive start date YYYY-MM-DD")
    p.add_argument("--until", default=DEFAULT_UNTIL, help="inclusive end date YYYY-MM-DD")
    p.add_argument(
        "--out",
        default=str(RAW_DIR / f"{source}.jsonl"),
        help=f"output JSONL (default data/raw/{source}.jsonl)",
    )
    p.add_argument("--count-only", action="store_true", help="report hit counts, write nothing")
    p.add_argument(
        "--max-records",
        type=int,
        default=DEFAULT_MAX_RECORDS,
        help=f"cap on records written per source (0 = unlimited; default {DEFAULT_MAX_RECORDS})",
    )
    p.add_argument("--log-level", default="INFO")
    p.add_argument(
        "--waive-llm-on-strong",
        action="store_true",
        help="proposal v3 (measurement only): accept records that contain a strong harness term "
        "(common.STRONG_TERMS) even if the LLM block does not match; honoured by arxiv, acl, "
        "openreview and github, ignored by s2 and openalex",
    )
    if structure_block:
        p.add_argument(
            "--with-structure-block",
            action="store_true",
            help="AND the optional structure block (STRUCTURE_TERMS) into the query (precision)",
        )
    return p


def setup_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger("harvest")


def print_summary(source: str, summary: Mapping[str, Any]) -> None:
    """Print a machine-readable one-line summary (picked up when writing search_log.md)."""
    payload = {"source": source, "finished_at": now_iso(), **summary}
    print("SUMMARY " + json.dumps(payload, ensure_ascii=False))
