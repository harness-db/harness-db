"""Backward snowballing from the two competitor surveys that Semantic Scholar does not index.

Protocol section 5 asks for backward snowballing from the competitor surveys. Two of them are
not on S2, so ``s2.py --snowball`` cannot reach their bibliographies:

* Li et al., *Agent Harness Engineering: A Survey* (OpenReview eONq7FdiHa). PDF mirrored in
  the companion repository ``picrew/LLM-Harness`` (``docs/main.pdf``).
* Meng et al., *Agent Harness for Large Language Model Agents: A Survey* (Preprints.org
  202604.0428; the Preprints site is behind a browser challenge). PDF v4 is in the companion
  repository ``Gloriaameng/Awesome-Agent-Harness``.

The PDFs are downloaded once into ``data/raw/cache/`` (git-ignored), their reference sections
are extracted with ``pypdf`` and split into entries (``[n]``-numbered for Meng; author-year
entries ending in a year or an "Accessed <date>." marker for Li). From every entry the script
takes the arXiv id, DOI, URLs and a heuristic title (the sentence after the author list), then
resolves papers on Semantic Scholar: by arXiv id / DOI through ``POST /paper/batch``, otherwise
by ``GET /paper/search/match`` on the title (accepted only when the returned title fuzzy-matches
the parsed one at >= ``--min-ratio``). Resolved papers are written with ``source="s2_snowball"``
(same shape as ``s2.py --snowball``); GitHub links become repository records (``title`` =
``owner/repo``) and unresolved entries are written from the parsed text, both with
``source="survey_refs"``. ``query_used`` = ``snowball:references:<seed>``. The protocol date
window is applied to dated records exactly as in ``s2.py --snowball``.

Usage:
    python scripts/harvest/survey_refs.py --out data/raw/snowball_surveys.jsonl
        [--pdf li=PATH --pdf meng=PATH]   # local PDFs instead of the mirrors
        [--count-only] [--min-ratio 85]
"""

from __future__ import annotations

import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from common import (
    CACHE_DIR,
    HttpClient,
    HttpError,
    JsonlWriter,
    Record,
    build_parser,
    normalize_arxiv_id,
    normalize_doi,
    normalize_title,
    now_iso,
    print_summary,
    setup_logging,
    within,
)

API = "https://api.semanticscholar.org/graph/v1"
FIELDS = (
    "paperId,externalIds,title,abstract,authors,year,publicationDate,venue,"
    "publicationVenue,url,fieldsOfStudy,citationCount"
)

SURVEYS: dict[str, dict[str, str]] = {
    "li": {
        "seed": "openreview:eONq7FdiHa",
        "label": "Li et al. 2026, Agent Harness Engineering: A Survey (OpenReview eONq7FdiHa)",
        "pdf_url": "https://raw.githubusercontent.com/picrew/LLM-Harness/main/docs/main.pdf",
        "style": "authoryear",
    },
    "meng": {
        "seed": "preprints:202604.0428",
        "label": "Meng et al. 2026, Agent Harness for Large Language Model Agents: A Survey (Preprints.org 202604.0428, v4)",
        "pdf_url": "https://raw.githubusercontent.com/Gloriaameng/Awesome-Agent-Harness/main/Agent_Harness_for_LLM_Agents__A_Survey__v4.pdf",
        "style": "numbered",
    },
}

_ARXIV_PREFIXED = re.compile(r"(?:arXiv:|arxiv\.org/(?:abs|pdf)/)\s*(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE)
_ARXIV_BARE = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")
_DOI = re.compile(r"\b(10\.\d{4,9}/[^\s,;]+)")
_URL = re.compile(r"https?://[^\s]+")
_GH = re.compile(r"github\.com/([\w.-]+)/([\w.-]+?)(?:[/.#?)]|$)", re.IGNORECASE)
_ENTRY_END = re.compile(r"((?:19|20)\d\d[a-z]?\.|Accessed [A-Za-z]+ \d{1,2}, \d{4}\.|Accessed: \d{4}-\d{2}-\d{2}\.)\s*$")
_NUMBERED = re.compile(r"^\[(\d+)\]\s*")


@dataclass
class Entry:
    n: int
    text: str
    authors: str = ""
    title: str = ""
    year: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    urls: list[str] = field(default_factory=list)
    github: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------------------
# PDF -> reference entries
# --------------------------------------------------------------------------------------


def pdf_text(path: Path) -> str:
    from pypdf import PdfReader  # local import: optional dependency

    rd = PdfReader(str(path))
    return "\n".join((p.extract_text() or "") for p in rd.pages)


def reference_section(text: str) -> str:
    heads = [m.start() for m in re.finditer(r"\n\s*(References|REFERENCES|Bibliography)\s*\n", text)]
    if not heads:
        raise ValueError("no References heading found")
    sec = text[heads[-1] :]
    # cut at a trailing appendix if the survey has one after the bibliography
    m = re.search(r"\n\s*(?:[A-Z]\s+)?(Appendix|APPENDIX|Supplementary Material)\b", sec)
    return sec[: m.start()] if m else sec


def _join_lines(lines: list[str]) -> str:
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out.endswith("-") and ln[:1].islower():
            out = out[:-1] + ln
        else:
            out = (out + " " + ln).strip()
    return out


def split_entries(section: str, style: str) -> list[str]:
    lines = [
        ln
        for ln in section.splitlines()
        if ln.strip()
        and not re.fullmatch(r"\s*\d{1,3}\s*", ln)
        and not re.fullmatch(r"\s*(References|REFERENCES|Bibliography)\s*", ln)
    ]
    entries: list[str] = []
    if style == "numbered":
        cur: list[str] = []
        for ln in lines:
            if _NUMBERED.match(ln.strip()) and cur:
                entries.append(_join_lines(cur))
                cur = []
            cur.append(ln)
        if cur:
            entries.append(_join_lines(cur))
        return [re.sub(r"^\[\d+\]\s*", "", e) for e in entries]
    cur = []
    for ln in lines:
        cur.append(ln)
        if _ENTRY_END.search(ln.strip()):
            entries.append(_join_lines(cur))
            cur = []
    if cur:
        entries.append(_join_lines(cur))
    # a continuation that only carries the URL / access date belongs to the previous entry
    merged: list[str] = []
    for e in entries:
        if merged and re.match(r"^(URL\s*)?(https?://|Accessed\b)", e):
            merged[-1] = merged[-1] + " " + e
        else:
            merged.append(e)
    return merged


def _split_sentences(text: str) -> list[str]:
    """Split on '. ' boundaries that are not initials ('J. Smith'), 'et al.' or 'pp.'."""
    parts: list[str] = []
    buf = ""
    tokens = re.split(r"(\. )", text)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == ". ":
            prev = buf.rstrip()
            last = prev.split()[-1] if prev.split() else ""
            if re.fullmatch(r"[A-Z]", last) or last.lower() in ("pp", "vol", "no", "eds", "ed", "st", "jr", "dr") or re.fullmatch(r"[A-Z]\.[A-Z]", last):
                buf += tok
            else:
                parts.append(buf.strip())
                buf = ""
        else:
            buf += tok
        i += 1
    if buf.strip():
        parts.append(buf.strip())
    return [p for p in parts if p]


def parse_entry(n: int, text: str) -> Entry:
    e = Entry(n=n, text=text)
    m = _ARXIV_PREFIXED.search(text) or _ARXIV_BARE.search(text)
    e.arxiv_id = normalize_arxiv_id(m.group(1)) if m else None
    d = _DOI.search(text)
    e.doi = normalize_doi(d.group(1).rstrip(".")) if d else None
    e.urls = [u.rstrip(".,;)") for u in _URL.findall(text)]
    g = _GH.search(text.replace(" ", ""))
    if g:
        e.github = f"{g.group(1)}/{g.group(2)}"
    y = re.search(r"\b((?:19|20)\d\d)[a-z]?\b", text)
    e.year = y.group(1) if y else None
    clean = _URL.sub(" ", text)
    clean = re.sub(r"\bURL\s*(?=Accessed|$)", " ", clean)
    clean = re.sub(r"\.(In)(?=[A-Z])", r". \1 ", clean)  # pypdf glues "agents.InInternational"
    clean = re.sub(r"\.(arXiv|CoRR|Proceedings|Java|IEEE|ACM)", r". \1", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    sents = _split_sentences(clean)
    if len(sents) >= 2:
        e.authors, e.title = sents[0], sents[1]
    elif sents:
        e.title = sents[0]
    e.title = re.sub(r",?\s*(?:19|20)\d\d[a-z]?$", "", e.title).strip(" .,:;\"'")
    if e.title.startswith("In ") and len(sents) > 2:
        e.title = ""
    return e


# --------------------------------------------------------------------------------------
# Semantic Scholar resolution
# --------------------------------------------------------------------------------------


def s2_api_key() -> str | None:
    if os.environ.get("S2_API_KEY"):
        return os.environ["S2_API_KEY"]
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("S2_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def batch_lookup(client: HttpClient, ids: list[str], log: logging.Logger) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i in range(0, len(ids), 400):
        chunk = ids[i : i + 400]
        resp = client.request("POST", f"{API}/paper/batch", params={"fields": FIELDS}, json_body={"ids": chunk})
        if resp.status_code != 200:
            raise HttpError(f"batch HTTP {resp.status_code}: {resp.text[:200]}")
        for sid, paper in zip(chunk, resp.json(), strict=True):
            if paper:
                out[sid] = paper
    log.info("batch lookup: %d/%d ids resolved", len(out), len(ids))
    return out


def title_lookup(client: HttpClient, title: str, min_ratio: int, log: logging.Logger) -> tuple[dict[str, Any] | None, float]:
    from rapidfuzz import fuzz

    resp = client.get(f"{API}/paper/search/match", params={"query": title, "fields": FIELDS})
    if resp.status_code == 404:
        return None, 0.0
    if resp.status_code != 200:
        raise HttpError(f"match HTTP {resp.status_code}: {resp.text[:200]}")
    data = (resp.json().get("data") or [None])[0]
    if not data:
        return None, 0.0
    ratio = fuzz.ratio(normalize_title(title), normalize_title(data.get("title") or ""))
    if ratio < min_ratio:
        log.debug("rejected match %.0f: %r -> %r", ratio, title, data.get("title"))
        return None, ratio
    return data, ratio


def paper_record(p: dict[str, Any], e: Entry, seed: str, how: str, ratio: float | None) -> Record:
    ext = p.get("externalIds") or {}
    return Record(
        id=f"survey_refs:{seed}:{e.n}",
        source="s2_snowball",
        source_id=p["paperId"],
        title=(p.get("title") or "").strip(),
        abstract=(p.get("abstract") or "").strip(),
        authors=[a.get("name", "") for a in p.get("authors") or []],
        date=p.get("publicationDate") or (str(p["year"]) if p.get("year") else None),
        venue=p.get("venue") or (p.get("publicationVenue") or {}).get("name") or None,
        url=p.get("url") or f"https://www.semanticscholar.org/paper/{p['paperId']}",
        doi=normalize_doi(ext.get("DOI")),
        arxiv_id=normalize_arxiv_id(ext.get("ArXiv")) or e.arxiv_id,
        categories=list(p.get("fieldsOfStudy") or []),
        query_used=f"snowball:references:{seed}",
        retrieved_at=now_iso(),
        extra={"citationCount": p.get("citationCount"), "seed": seed, "direction": "references", "resolved": how, "match_ratio": ratio, "ref_no": e.n, "ref_text": e.text[:400]},
    )


def fallback_record(e: Entry, seed: str) -> Record:
    if e.github:
        kind, title, url = "repo", e.github, f"https://github.com/{e.github}"
    else:
        kind, title, url = ("paper" if e.arxiv_id else "other"), e.title or e.text[:120], (f"https://arxiv.org/abs/{e.arxiv_id}" if e.arxiv_id else (e.urls[0] if e.urls else None))
    return Record(
        id=f"survey_refs:{seed}:{e.n}",
        source="survey_refs",
        source_id=f"{seed}:{e.n}",
        title=title,
        abstract=e.text,
        authors=[a.strip() for a in re.split(r",\s*|\s+and\s+", e.authors) if a.strip()][:20],
        date=e.year,
        venue=None,
        url=url,
        doi=e.doi,
        arxiv_id=e.arxiv_id,
        categories=[],
        query_used=f"snowball:references:{seed}",
        retrieved_at=now_iso(),
        extra={"kind": kind, "seed": seed, "direction": "references", "resolved": "none", "ref_no": e.n, "parsed_title": e.title, "urls": e.urls},
    )


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def download_pdf(client: HttpClient, key: str, url: str, log: logging.Logger) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / f"survey_{key}.pdf"
    if dest.exists() and dest.stat().st_size > 0:
        log.info("using cached %s", dest)
        return dest
    resp = client.get(url, stream=True)
    if resp.status_code != 200:
        raise HttpError(f"GET {url}: HTTP {resp.status_code}")
    with dest.open("wb") as fh:
        for chunk in resp.iter_content(1 << 20):
            fh.write(chunk)
    log.info("saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest


def main(argv: list[str] | None = None) -> int:
    p = build_parser("snowball_surveys", __doc__.split("\n\n")[0])
    p.add_argument("--pdf", action="append", default=[], metavar="KEY=PATH", help="local PDF for li or meng")
    p.add_argument("--min-ratio", type=int, default=85, help="min title fuzz ratio to accept an S2 title match")
    p.add_argument("--surveys", nargs="*", choices=tuple(SURVEYS), default=list(SURVEYS))
    args = p.parse_args(argv)
    log = setup_logging(args.log_level)
    key = s2_api_key()
    client = HttpClient(min_interval=1.0, timeout=180, logger=log, headers={"x-api-key": key} if key else None)
    log.info("Semantic Scholar API key: %s", "present" if key else "absent")
    local = dict(kv.split("=", 1) for kv in args.pdf)

    per: dict[str, dict[str, Any]] = {}
    error: str | None = None
    with JsonlWriter(args.out, count_only=args.count_only) as w:
        for skey in args.surveys:
            cfg = SURVEYS[skey]
            seed = cfg["seed"]
            info: dict[str, Any] = {"seed": seed, "label": cfg["label"], "pdf": None, "entries": 0}
            try:
                pdf = Path(local[skey]) if skey in local else download_pdf(client, skey, cfg["pdf_url"], log)
                info["pdf"] = str(pdf)
                entries = [parse_entry(i + 1, t) for i, t in enumerate(split_entries(reference_section(pdf_text(pdf)), cfg["style"]))]
                info["entries"] = len(entries)
                info["with_arxiv_id"] = sum(1 for e in entries if e.arxiv_id)
                info["with_doi"] = sum(1 for e in entries if e.doi and not e.arxiv_id)
                info["github"] = sum(1 for e in entries if e.github)
                # 1) batch by identifier
                ids: dict[str, Entry] = {}
                for e in entries:
                    if e.arxiv_id:
                        ids[f"ARXIV:{e.arxiv_id}"] = e
                    elif e.doi:
                        ids[f"DOI:{e.doi}"] = e
                found = batch_lookup(client, list(ids), log) if ids else {}
                resolved: dict[int, tuple[dict[str, Any], str, float | None]] = {}
                for sid, e in ids.items():
                    if sid in found:
                        resolved[e.n] = (found[sid], "id", None)
                # 2) title match for the rest (papers only: skip pure GitHub/blog entries)
                n_title_tried = n_title_ok = 0
                for e in entries:
                    if e.n in resolved or e.github or not e.title or len(e.title) < 12:
                        continue
                    if e.urls and not any(x in " ".join(e.urls) for x in ("arxiv.org", "openreview.net", "aclanthology", "doi.org", "neurips", "proceedings", "acm.org", "ieee")) and not e.year:
                        continue
                    n_title_tried += 1
                    paper, ratio = title_lookup(client, e.title, args.min_ratio, log)
                    if paper:
                        n_title_ok += 1
                        resolved[e.n] = (paper, "title", ratio)
                info["title_lookups"] = n_title_tried
                info["title_matched"] = n_title_ok
                # 3) write
                counts = {"s2_paper": 0, "repo": 0, "unresolved_paper": 0, "other": 0, "outside_window": 0}
                for e in entries:
                    if e.n in resolved:
                        paper, how, ratio = resolved[e.n]
                        rec = paper_record(paper, e, seed, how, ratio)
                        if not within(rec.date, args.since, args.until):
                            counts["outside_window"] += 1
                            continue
                        counts["s2_paper"] += 1
                    else:
                        rec = fallback_record(e, seed)
                        counts[{"repo": "repo", "paper": "unresolved_paper", "other": "other"}[rec.extra["kind"]]] += 1
                    w.write(rec)
                info["written"] = counts
            except (HttpError, OSError, ValueError, ImportError) as exc:
                info["error"] = str(exc)
                error = (error + "; " if error else "") + f"{skey}: {exc}"
                log.error("%s: %s", skey, exc)
            per[skey] = info
        written = w.count
    print_summary(
        "snowball_surveys",
        {
            "query": {k: f"snowball:references:{v['seed']}" for k, v in per.items()},
            "surveys": per,
            "counts": {"both": written},
            "written": written,
            "capped": False,
            "max_records": args.max_records,
            "date_window": f"{args.since}:{args.until}",
            "error": error,
            "requests": client.requests_made,
            "out": None if args.count_only else args.out,
        },
    )
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
