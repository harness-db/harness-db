"""Build the layer-exemplar table (design values x cited exemplar systems).

Outputs
    paper/tables/layer_exemplars.tex   booktabs table, \\label{tab:layer-exemplars}
    paper/references/corpus.bib        one BibTeX entry per exemplar not already in
                                       paper/references/must_cite.bib

Inputs (read-only)
    schema/dimensions.json, data/analysis/value_distributions.csv, data/systems.json,
    data/papers.csv, data/coding_frame.csv, paper/references/must_cite.bib

Rules (deterministic; no randomness; no network access unless --refresh-meta)

1. Dimensions and values.  DIMENSIONS below fixes one or two dimensions per design
   layer A-H and how many values to show for each.  For each dimension the values are
   ranked by ``share_weighted`` in value_distributions.csv (descending, ties by value
   name), the value ``none`` is skipped (it is the absence of a design, not a design),
   and the top N are kept.  The printed share is ``100 * share_weighted`` rounded to
   one decimal.  share_weighted is the weighted share among frame systems whose cell
   for that dimension is reported; multi-valued dimensions can sum above 100.

2. Citable record per system.  A system's papers.csv records are *relevant* when the
   normalized system name, an alias, or the system id (>= 4 characters after
   normalization) occurs in the normalized record title, or the record URL equals the
   system repository URL.  Among relevant records the preferred one is, in order: its
   arXiv id is an eprint in must_cite.bib; the title starts with the primary name
   (name or id, not an alias); the title contains the primary name; peer-reviewed
   venue > has an arXiv id > GitHub/repository record > other; URL match; record id.
   (Aliases often name follow-up papers, e.g. MetaGPT -> Data Interpreter, so an alias
   match ranks below a primary-name match.)  A system with no relevant record is not eligible as an
   exemplar (its citation cannot be resolved from the data).
   A venue counts as peer-reviewed unless it is empty or matches NON_PEER_PATTERNS
   (arXiv, preprint servers, GitHub, awesome lists, leaderboards, vendor docs, OpenReview
   submissions that were not accepted, institutional repositories).

3. Citation key.  The must_cite.bib key is reused when (a) the chosen record's arXiv id
   equals an ``eprint`` in must_cite.bib, (b) the system repository URL equals a
   must_cite.bib ``url``, or (c) the system is listed in MUST_CITE_EXTRA (checked by
   hand; reason given there).  Otherwise the key is ``hdb_<system_id>`` sanitized to
   [a-z0-9_]; its title, arXiv id and URL are copied from the papers.csv row and the
   remaining fields come from rule 5.  VERIFIED_VENUES and papers.csv venues are used
   only to decide peer-review status for ranking (rule 4), not in corpus.bib.

4. Exemplar ranking for a value.  Candidates are systems whose coded cell has that
   value (as the value or as one element of a multi-value list), is not
   ``not_reported`` and not ``unresolved``, and whose citation resolves (rule 2).
   Up to EXEMPLARS_PER_VALUE systems are chosen greedily; at each step the candidate
   with the largest tuple wins:
       (a) prominence = [peer-reviewed record] + [>= STAR_THRESHOLD GitHub stars or
                        already cited in must_cite.bib]                  (0/1/2)
       (b) confidence = high 2 / medium 1 / low 0; then has a verbatim quote in the
                        ``evidence`` field                               (1/0)
       (c) diversity  = not yet used anywhere in the table (1/0), then target_domain
                        not yet used in this row (1/0)
       then peer-reviewed (1/0), stars (desc), system id (asc).
   A system already shown in MAX_USES rows is not a candidate for further rows.
   Rows are filled in DIMENSIONS order.
   Stars are the larger of coding_frame.csv ``stars`` and the coded ``stars`` cell.

5. Bibliographic metadata.  Authors, venue, year and DOI of corpus.bib entries come from
   data/analysis/layer_exemplars_meta.json (see the "metadata" section below for the
   sources and the resolution order).  In the table every exemplar is cited as
   ``<system name>~\\citep{key}``.

Re-run:  python scripts/make_layer_exemplars.py   (twice gives byte-identical output;
         reads the metadata cache only, no network)
Refresh: python scripts/make_layer_exemplars.py --refresh-meta   (fetches any cache
         entries that are missing, then regenerates)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_TEX = ROOT / "paper" / "tables" / "layer_exemplars.tex"
OUT_BIB = ROOT / "paper" / "references" / "corpus.bib"
MUST_CITE = ROOT / "paper" / "references" / "must_cite.bib"

# (layer, dim_id, key, number of values shown)
DIMENSIONS = [
    ("A", "A2", "env_context_strategy", 2),
    ("A", "A3", "context_compaction", 2),
    ("B", "B1", "tool_call_format", 3),
    ("B", "B3", "edit_primitive", 2),
    ("C", "C3", "multi_agent_topology", 3),
    ("D", "D2", "long_term_memory", 2),
    ("E", "E1", "self_verification", 3),
    ("F", "F1", "termination_condition", 2),
    ("F", "F2", "cost_controls", 1),
    ("G", "G1", "execution_isolation", 2),
    ("H", "H1", "tracing", 2),
    ("H", "H4", "guardrails", 1),
]
EXEMPLARS_PER_VALUE = 3
MAX_USES = 2  # a system appears in at most this many rows of the table
STAR_THRESHOLD = 1000
FRAME_N = "6,504"

# Hand-checked mappings to must_cite.bib that rules 3(a)/(b) cannot find.
MUST_CITE_EXTRA = {
    # papers.csv holds the OpenAlex record of the ReAct paper (no arXiv id).
    "react": "yao2023react",
    # github.com/block/goose redirects to github.com/aaif-goose/goose (same GitHub
    # repository id 846698999; checked via api.github.com on 2026-09-28).
    "goose": "goose",
}
# Not mapped on purpose: system "opencode" is github.com/opencode-ai/opencode, while
# must_cite key "opencode" is github.com/sst/opencode (now anomalyco/opencode), a
# different repository.

# Published-venue versions of records that papers.csv lists only as arXiv/preprint.
# DBLP's search API was behind a bot-check page on 2026-09-28, so each entry was
# verified on the Semantic Scholar Graph API (paper looked up by arXiv id; the
# ``venue`` and ``year`` fields are copied verbatim from the response, nothing is
# completed from memory).  The query URL is written as a comment above the corpus.bib
# entry.  record_id -> (venue, year, verification_query_url, record_url)
VERIFIED_VENUES = {
    "arxiv:2410.08164": ("International Conference on Learning Representations", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2410.08164?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2410.08164"),  # agent-s
    "arxiv:2308.10848": ("International Conference on Learning Representations", "2023",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2308.10848?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2308.10848"),  # agentverse
    "arxiv:2309.17288": ("International Joint Conference on Artificial Intelligence", "2023",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2309.17288?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2309.17288"),  # autoagents
    "arxiv:2412.05467": ("Trans. Mach. Learn. Res.", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2412.05467?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2412.05467"),  # browsergym
    "arxiv:2303.17760": ("Neural Information Processing Systems", "2023",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2303.17760?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2303.17760"),  # camel-2
    "arxiv:2402.01030": ("International Conference on Machine Learning", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.01030?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.01030"),  # codeact
    "arxiv:2510.24428": ("Annual Meeting of the Association for Computational Linguistics", "2025",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2510.24428?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2510.24428"),  # codewiki
    "arxiv:2605.15625": ("Digital Discovery", "2026",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2605.15625?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2605.15625"),  # colpackagent
    "arxiv:2508.08709": ("International SoC Design Conference", "2025",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2508.08709?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2508.08709"),  # cradle
    "arxiv:2510.21618": ("The Web Conference", "2025",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2510.21618?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2510.21618"),  # deepagent
    "arxiv:2406.01014": ("Neural Information Processing Systems", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2406.01014?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2406.01014"),  # mobile-agent-v2
    "arxiv:2304.04370": ("Neural Information Processing Systems", "2023",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2304.04370?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2304.04370"),  # openagi
    "arxiv:2407.16741": ("International Conference on Learning Representations", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2407.16741?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2407.16741"),  # openhands
    "arxiv:2512.02589": ("The Web Conference", "2025",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2512.02589?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2512.02589"),  # paperdebugger
    "arxiv:2403.06465": ("The Web Conference", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2403.06465?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2403.06465"),  # recai
    "arxiv:2303.11366": ("Neural Information Processing Systems", "2023",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2303.11366?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2303.11366"),  # reflexion
    "arxiv:2405.15793": ("Neural Information Processing Systems", "2024",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2405.15793?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2405.15793"),  # swe-agent
    "arxiv:2504.14603": ("Trans. Mach. Learn. Res.", "2025",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2504.14603?fields=title,venue,year,publicationVenue,externalIds,publicationTypes",
        "https://api.semanticscholar.org/graph/v1/paper/arXiv:2504.14603"),  # ufo-v2
}

NON_PEER_PATTERNS = [
    r"^$", r"arxiv", r"^github$", r"^awesome:", r"^vendor-docs$", r"^swe-bench$",
    r"^osworld$", r"^webarena$", r"^tau2-bench$", r"zenodo", r"submitted to",
    r"withdrawn", r"desk rejected", r"research square", r"ssrn", r"qeios", r"^doaj",
    r"biorxiv", r"medrxiv", r"techrxiv", r"preprints", r"^hal$", r"chalmers research",
    r"rare & special", r"national university of singapore", r"underline science",
    r"^\d{4}$", r"^\d{4}\.[a-z0-9-]+\.\d+$", r"^https?://",
]
JOURNAL_PATTERNS = [
    r"journal", r"transactions", r"trans\.", r"proc\. acm", r"proceedings of the acm on",
    r"^nature$", r"^patterns$", r"scientific reports", r"ieee access", r"^electronics$",
    r"frontiers", r"^npj", r"science china", r"digital discovery", r"letters",
    r"machine learning: science", r"scipost", r"vldb endowment", r"discover data",
]

LAYER_NAMES = {
    "A": "Context assembly", "B": "Tool interface", "C": "Control loop",
    "D": "Memory and state", "E": "Verification and repair",
    "F": "Budget and termination", "G": "Sandbox and environment",
    "H": "Observability and governance",
}
CONF_RANK = {"high": 2, "medium": 1, "low": 0}


# ----------------------------------------------------------------------------- utils
def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def norm_url(u: str) -> str:
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = re.sub(r"\.git$", "", u)
    return u.rstrip("/")


def is_peer(venue: str) -> bool:
    v = (venue or "").strip().lower()
    return not any(re.search(p, v) for p in NON_PEER_PATTERNS)


def is_journal(venue: str) -> bool:
    v = (venue or "").strip().lower()
    return any(re.search(p, v) for p in JOURNAL_PATTERNS)


def tex_escape(s: str) -> str:
    s = s or ""
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
           "^": r"\textasciicircum{}"}
    return "".join(rep.get(c, c) for c in s)


def eff_venue(row) -> tuple[str, str]:
    """(venue, year) for a papers.csv row, using a DBLP-verified upgrade if present."""
    v = VERIFIED_VENUES.get(row["id"])
    return (v[0], v[1]) if v else (row["venue"].strip(), row["year"])


def bib_key(system_id: str) -> str:
    return "hdb_" + re.sub(r"_+", "_", re.sub(r"[^a-z0-9]", "_", system_id.lower())).strip("_")


def cell_values(cell) -> list[str]:
    v = cell.get("value")
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def to_int(x) -> int:
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


# ----------------------------------------------------------------------------- load
def load_must_cite():
    text = MUST_CITE.read_text(encoding="utf-8")
    keys, eprints, urls = set(), {}, {}
    for m in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,", text):
        key = m.group(1)
        keys.add(key)
        # the entry body runs until the next '@' at line start
        nxt = re.search(r"^\s*@", text[m.end():], flags=re.MULTILINE)
        body = text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]
        e = re.search(r"eprint\s*=\s*\{([^}]*)\}", body)
        if e:
            eprints[e.group(1).strip()] = key
        u = re.search(r"\burl\s*=\s*\{([^}]*)\}", body)
        if u:
            urls[norm_url(u.group(1))] = key
    return keys, eprints, urls


def load_all():
    systems = json.loads((DATA / "systems.json").read_text(encoding="utf-8"))
    with open(DATA / "papers.csv", encoding="utf-8", newline="") as f:
        papers = {r["id"]: r for r in csv.DictReader(f)}
    with open(DATA / "coding_frame.csv", encoding="utf-8", newline="") as f:
        frame = {r["system_id"]: r for r in csv.DictReader(f)}
    with open(DATA / "analysis" / "value_distributions.csv", encoding="utf-8", newline="") as f:
        dist = list(csv.DictReader(f))
    return systems, papers, frame, dist


# ----------------------------------------------------------------------------- logic
def choose_record(sysrec, papers, mc_eprints):
    """Return (record_row, match_kind) or (None, None) per rule 2."""
    primary = [sysrec["name"], re.sub(r"\s*\(.*?\)\s*", " ", sysrec["name"]), sysrec["id"]]
    pnames = sorted({norm(n) for n in primary if len(norm(n)) >= 4})
    anames = sorted({norm(n) for n in (sysrec.get("aliases") or []) if len(norm(n)) >= 4})
    repo = norm_url((sysrec.get("urls") or {}).get("repo", ""))
    best = None
    for rid in sysrec["papers"]:
        row = papers.get(rid)
        if row is None:
            continue
        nt = norm(row["title"])
        p_prefix = any(nt.startswith(n) for n in pnames)
        p_match = any(n in nt for n in pnames)
        a_match = any(n in nt for n in anames)
        url_match = bool(repo) and norm_url(row["url"]) == repo
        if not (p_match or a_match or url_match):
            continue
        kind = (3 if is_peer(eff_venue(row)[0]) else
                2 if row["arxiv_id"] else
                1 if (row["source"] in ("github", "awesome") or "github.com" in row["url"]) else 0)
        in_mc = int(bool(row["arxiv_id"]) and row["arxiv_id"] in mc_eprints)
        rank = (in_mc, int(p_prefix), int(p_match), kind, int(url_match))
        cand = (rank, tuple(-ord(c) for c in rid), row, "title" if (p_match or a_match) else "url")
        if best is None or cand[:2] > best[:2]:
            best = cand
    return (best[2], best[3]) if best else (None, None)


def resolve_citation(sysrec, row, mc_eprints, mc_urls):
    sid = sysrec["id"]
    if sid in MUST_CITE_EXTRA:
        return MUST_CITE_EXTRA[sid], True
    if row is not None and row["arxiv_id"] and row["arxiv_id"] in mc_eprints:
        return mc_eprints[row["arxiv_id"]], True
    repo = norm_url((sysrec.get("urls") or {}).get("repo", ""))
    if repo and repo in mc_urls:
        return mc_urls[repo], True
    return bib_key(sid), False


def top_values(dist, dim_id, n):
    rows = [r for r in dist if r["dim_id"] == dim_id and r["value"] != "none"]
    rows.sort(key=lambda r: (-float(r["share_weighted"]), r["value"]))
    return [(r["value"], float(r["share_weighted"])) for r in rows[:n]]


# ----------------------------------------------------------------------------- metadata
# Bibliographic metadata for corpus.bib entries is read from META_CACHE, a committed JSON
# file written by ``--refresh-meta``.  A normal run never touches the network.
#
# Cache layout: {"<source>:<id>": {"url": fetch URL, "fetched": date, "data": {...}}}
#   arxiv:<eprint>            arXiv API record (authors in listed order, title, doi, journal_ref)
#   s2:<lookup>               Semantic Scholar Graph API record (lookup = arXiv:<id> or DOI:<doi>)
#   crossref:<doi>            Crossref /works/<doi> record (type, container-title, issued, authors)
#   crossref_search:<ntitle>  Crossref bibliographic search, exact normalized-title hits only
#   openreview_search:<ntitle> OpenReview notes search, exact normalized-title hits only
#   pmlr_search:<ntitle>      PMLR volume index pages (PMLR_VOLUMES), exact title hits only
#
# Resolution for each entry (deterministic, cache only):
#   authors  arXiv record when the entry has an eprint; otherwise the Crossref record of
#            the published DOI; otherwise the Semantic Scholar record.  Names are written
#            in the source's order and spelling ("Given Family" as listed).
#   venue    (1) published DOI = papers.csv doi, else Semantic Scholar externalIds.DOI,
#                else the Crossref title-search hit (DOIs under 10.48550 = arXiv are
#                ignored); its Crossref record gives the container-title (venue), the
#                issued year and the type (journal-article -> @article, else
#                @inproceedings).
#            (2) else a PMLR proceedings record (booktitle, volume, pages, year held).
#            (3) else an accepted OpenReview record (venueid "<Conf>.cc/<year>/Conference"
#                or "TMLR") gives conference and year; the full name is taken from
#                OPENREVIEW_VENUE_NAMES, which spells out the conference abbreviations.
#            (4) else the Semantic Scholar publicationVenue name and year, if not arXiv.
#            (5) else @misc with the arXiv eprint.
#   VENUE_FIXES repairs typography in a fetched venue string (e.g. a missing space).
#   The source URL of the venue is written as a comment above the entry.
META_CACHE = DATA / "analysis" / "layer_exemplars_meta.json"
FETCH_DATE = "2026-09-28"
# PMLR volumes searched for papers without a DOI (ICML 2024, ICML 2025, CoLLAs 2024).
# A paper is taken from a volume only on an exact normalized-title match; the booktitle,
# pages and year are copied from the fetched volume index page.
PMLR_VOLUMES = ["v235", "v267", "v274"]
# Typographic repairs of fetched venue strings (the source string is otherwise kept).
VENUE_FIXES = {"Thirty-ThirdInternational": "Thirty-Third International"}
OPENREVIEW_VENUE_NAMES = {
    "ICLR.cc": "International Conference on Learning Representations",
    "ICML.cc": "International Conference on Machine Learning",
    "NeurIPS.cc": "Advances in Neural Information Processing Systems",
    "colmweb.org/COLM": "Conference on Language Modeling",
}
ARXIV_DOI = "10.48550/"


def _published_doi(doi: str) -> str:
    doi = (doi or "").strip().lower()
    return "" if (not doi or doi.startswith(ARXIV_DOI)) else doi


def _http_get(url: str, headers: dict | None = None, tries: int = 6):
    import time
    import urllib.request
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "harness-db-bibcheck/1.0", "Accept": "*/*",
                                                       **(headers or {})})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001 - retried, then reported
            last = e
            # export.arxiv.org intermittently answers 406 to urllib; curl is accepted
            import subprocess
            cmd = ["curl", "-s", "-f", "-m", "40", url]
            for k, v in (headers or {}).items():
                cmd[1:1] = ["-H", f"{k}: {v}"]
            r = subprocess.run(cmd, capture_output=True, check=False)
            if r.returncode == 0 and r.stdout:
                return r.stdout.decode("utf-8")
            time.sleep(6 * (i + 1))
    raise RuntimeError(f"fetch failed: {url}: {last}")


def _s2_key() -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("S2_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def _fetch_arxiv(eprint: str) -> dict:
    import xml.etree.ElementTree as ET
    url = f"https://export.arxiv.org/api/query?id_list={eprint}"
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(_http_get(url))
    e = root.find("a:entry", ns)
    data = {
        "id": e.findtext("a:id", default="", namespaces=ns).strip(),
        "title": " ".join(e.findtext("a:title", default="", namespaces=ns).split()),
        "authors": [a.findtext("a:name", default="", namespaces=ns).strip()
                    for a in e.findall("a:author", ns)],
        "published": e.findtext("a:published", default="", namespaces=ns).strip(),
        "doi": (e.findtext("x:doi", default="", namespaces=ns) or "").strip(),
        "journal_ref": " ".join((e.findtext("x:journal_ref", default="", namespaces=ns) or "").split()),
    }
    return {"url": url, "fetched": FETCH_DATE, "data": data}


def _fetch_s2(lookup: str) -> dict:
    import urllib.parse
    fields = "title,authors,venue,year,publicationVenue,externalIds,publicationDate"
    url = (f"https://api.semanticscholar.org/graph/v1/paper/{urllib.parse.quote(lookup, safe=':/')}"
           f"?fields={fields}")
    key = _s2_key()
    d = json.loads(_http_get(url, {"x-api-key": key} if key else None))
    pv = d.get("publicationVenue") or {}
    data = {
        "paperId": d.get("paperId"), "title": d.get("title"),
        "authors": [a.get("name") for a in d.get("authors") or []],
        "venue": d.get("venue"), "year": d.get("year"),
        "publicationDate": d.get("publicationDate"),
        "publicationVenue": {"name": pv.get("name"), "type": pv.get("type")} if pv else None,
        "externalIds": d.get("externalIds") or {},
    }
    return {"url": url, "fetched": FETCH_DATE, "data": data}


def _crossref_subset(m: dict) -> dict:
    issued = ((m.get("issued") or {}).get("date-parts") or [[None]])[0]
    return {
        "DOI": (m.get("DOI") or "").lower(), "type": m.get("type"),
        "title": (m.get("title") or [""])[0],
        "container-title": m.get("container-title") or [],
        "event": (m.get("event") or {}).get("name"),
        "issued_year": issued[0] if issued else None,
        "authors": [" ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name", "")
                    for a in m.get("author") or []],
    }


def _fetch_crossref(doi: str) -> dict:
    import urllib.parse
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    m = json.loads(_http_get(url))["message"]
    return {"url": url, "fetched": FETCH_DATE, "data": _crossref_subset(m)}


def _fetch_crossref_search(title: str) -> dict:
    import urllib.parse
    url = ("https://api.crossref.org/works?rows=10&select=DOI,title,container-title,type,"
           f"issued,author,event&query.bibliographic={urllib.parse.quote(title)}")
    items = json.loads(_http_get(url))["message"]["items"]
    hits = [_crossref_subset(i) for i in items
            if norm((i.get("title") or [""])[0]) == norm(title)
            and i.get("type") in ("proceedings-article", "journal-article")
            and _published_doi(i.get("DOI"))]
    return {"url": url, "fetched": FETCH_DATE, "data": sorted(hits, key=lambda h: h["DOI"])}


def _fetch_openreview_search(title: str) -> dict:
    import urllib.parse
    q = urllib.parse.quote(title)
    url = (f"https://api2.openreview.net/notes/search?term={q}&type=terms&content=title"
           "&source=forum&limit=10")
    notes = json.loads(_http_get(url)).get("notes") or []
    hits = []
    for n in notes:
        c = n.get("content") or {}

        def val(k, c=c):
            return (c.get(k) or {}).get("value") if isinstance(c.get(k), dict) else c.get(k)

        if norm(val("title")) != norm(title):
            continue
        hits.append({"id": n.get("id"), "venue": val("venue"), "venueid": val("venueid"),
                     "authors": val("authors") or []})
    return {"url": url, "fetched": FETCH_DATE, "data": sorted(hits, key=lambda h: h["id"])}


_PMLR_PAGES: dict[str, str] = {}


def _fetch_pmlr_search(title: str) -> dict:
    import html as htmllib
    hits = []
    for vol in PMLR_VOLUMES:
        url = f"https://proceedings.mlr.press/{vol}/"
        if vol not in _PMLR_PAGES:
            _PMLR_PAGES[vol] = _http_get(url)
        page = _PMLR_PAGES[vol]
        held = re.search(r"<title>[^<]*?Held in [^<]*? (\d{4}) Published", page)
        for m in re.finditer(r'<p class="title">(.*?)</p>\s*<p class="details">\s*'
                             r'<span class="authors">(.*?)</span>;\s*<span class="info"><i>(.*?)</i>,'
                             r'\s*PMLR (\d+):([\w-]+)</span>.*?<a href="([^"]+)">abs</a>', page, flags=re.DOTALL):
            t = htmllib.unescape(m.group(1)).strip()
            if norm(t) != norm(title):
                continue
            hits.append({"volume": m.group(4), "booktitle": htmllib.unescape(m.group(3)).strip(),
                         "pages": m.group(5), "abs": m.group(6),
                         "authors": [htmllib.unescape(a).strip() for a in
                                     m.group(2).replace("&nbsp;", " ").split(",") if a.strip()],
                         "held_year": held.group(1) if held else "", "index": url})
    return {"url": " ".join(f"https://proceedings.mlr.press/{v}/" for v in PMLR_VOLUMES),
            "fetched": FETCH_DATE, "data": hits}


def refresh_meta(rows: list[dict]) -> None:
    """Fetch any missing metadata for the given papers.csv rows into META_CACHE."""
    import time
    cache = json.loads(META_CACHE.read_text(encoding="utf-8")) if META_CACHE.exists() else {}

    def save():
        META_CACHE.write_text(json.dumps(dict(sorted(cache.items())), indent=1, ensure_ascii=False)
                              + "\n", encoding="utf-8", newline="\n")

    def get(key, fn, *args):
        if key not in cache:
            print("fetch", key, flush=True)
            cache[key] = fn(*args)
            save()
            time.sleep(3.1 if key.startswith("arxiv:") else 1.2)
        return cache[key]["data"]

    for row in rows:
        ax = row["arxiv_id"].strip()
        if ax:
            get(f"arxiv:{ax}", _fetch_arxiv, ax)
        lookup = f"arXiv:{ax}" if ax else (f"DOI:{row['doi']}" if row["doi"] else "")
        s2 = get(f"s2:{lookup}", _fetch_s2, lookup) if lookup else {}
        dois = [_published_doi(row["doi"]), _published_doi((s2.get("externalIds") or {}).get("DOI"))]
        if not any(dois):
            hits = get(f"crossref_search:{norm(row['title'])}", _fetch_crossref_search, row["title"])
            dois.append(hits[0]["DOI"] if hits else "")
        doi = next((d for d in dois if d), "")
        if doi:
            get(f"crossref:{doi}", _fetch_crossref, doi)
        else:
            get(f"pmlr_search:{norm(row['title'])}", _fetch_pmlr_search, row["title"])
            get(f"openreview_search:{norm(row['title'])}", _fetch_openreview_search, row["title"])
    save()


def resolve_meta(row: dict, cache: dict) -> dict:
    """Authors, venue, year, doi and entry type for one papers.csv row, from the cache."""
    ax = row["arxiv_id"].strip()
    arx = (cache.get(f"arxiv:{ax}") or {}).get("data") if ax else None
    lookup = f"arXiv:{ax}" if ax else (f"DOI:{row['doi']}" if row["doi"] else "")
    s2c = cache.get(f"s2:{lookup}") or {}
    s2 = s2c.get("data") or {}
    dois = [_published_doi(row["doi"]), _published_doi((s2.get("externalIds") or {}).get("DOI"))]
    cs = cache.get(f"crossref_search:{norm(row['title'])}")
    if not any(dois) and cs and cs["data"]:
        dois.append(cs["data"][0]["DOI"])
    doi = next((d for d in dois if d), "")
    cr = cache.get(f"crossref:{doi}") if doi else None
    out = {"authors": [], "authors_src": "", "venue": "", "year": "", "doi": "", "etype": "misc",
           "venue_src": ""}
    if arx and arx["authors"]:
        out["authors"], out["authors_src"] = arx["authors"], cache[f"arxiv:{ax}"]["url"]
    elif cr and cr["data"]["authors"]:
        out["authors"], out["authors_src"] = cr["data"]["authors"], cr["url"]
    elif s2.get("authors"):
        out["authors"], out["authors_src"] = s2["authors"], s2c["url"]
    if cr and cr["data"]["container-title"] and cr["data"]["type"] != "posted-content":
        d = cr["data"]
        venue = max(d["container-title"], key=len)
        for a, b in VENUE_FIXES.items():
            venue = venue.replace(a, b)
        out.update(venue=venue, year=str(d["issued_year"] or ""),
                   doi=d["DOI"], venue_src=cr["url"],
                   etype="article" if d["type"] == "journal-article" else "inproceedings")
        return out
    pm = cache.get(f"pmlr_search:{norm(row['title'])}")
    if pm and pm["data"]:
        h = pm["data"][0]
        out.update(venue=h["booktitle"], year=h["held_year"], etype="inproceedings",
                   pmlr=h, venue_src=f"{h['index']} ({h['abs']})")
        return out
    orc = cache.get(f"openreview_search:{norm(row['title'])}")
    for h in (orc or {}).get("data") or []:
        vid = h.get("venueid") or ""
        m = re.match(r"^(.+?)/(\d{4})/Conference$", vid)
        vtxt = (h.get("venue") or "").lower()
        if m and m.group(1) in OPENREVIEW_VENUE_NAMES and not re.search(
                r"submitted|withdrawn|reject", vtxt):
            out.update(venue=OPENREVIEW_VENUE_NAMES[m.group(1)], year=m.group(2),
                       etype="inproceedings", venue_src=f"{orc['url']} (note {h['id']}, venueid {vid})")
            return out
        if vid == "TMLR":
            out.update(venue="Transactions on Machine Learning Research", etype="article",
                       year=str(s2.get("year") or row["year"]),
                       venue_src=f"{orc['url']} (note {h['id']}, venueid {vid})")
            return out
    pv = (s2.get("publicationVenue") or {}).get("name") or ""
    if pv and "arxiv" not in pv.lower():
        out.update(venue=pv, year=str(s2.get("year") or ""), venue_src=s2c["url"],
                   etype="article" if (s2.get("publicationVenue") or {}).get("type") == "journal"
                   else "inproceedings")
        return out
    out["year"] = str((arx or {}).get("published", "")[:4] or row["year"])
    return out


def bib_entry(key, sysrec, row, cache):
    meta = resolve_meta(row, cache)
    fields = [("title", "{" + tex_escape(row["title"]) + "}")]
    if meta["authors"]:
        fields.append(("author", " and ".join(tex_escape(a) for a in meta["authors"])))
    else:
        fields.append(("author", ""))
        fields.append(("key", tex_escape(re.sub(r"\s*\(.*?\)\s*", " ", sysrec["name"]).strip())))
    etype = meta["etype"]
    if etype != "misc":
        fields.append(("journal" if etype == "article" else "booktitle", tex_escape(meta["venue"])))
    if meta.get("pmlr"):
        fields.append(("series", "Proceedings of Machine Learning Research"))
        fields.append(("volume", meta["pmlr"]["volume"]))
        fields.append(("pages", meta["pmlr"]["pages"].replace("-", "--")))
    if meta["year"]:
        fields.append(("year", meta["year"]))
    if row["arxiv_id"]:
        fields.append(("eprint", row["arxiv_id"]))
        fields.append(("archivePrefix", "arXiv"))
    if meta["doi"]:
        fields.append(("doi", meta["doi"]))
    url = row["url"]
    if url:
        fields.append(("url", url))
    repo = (sysrec.get("urls") or {}).get("repo", "")
    note = f"HARNESS-DB record {tex_escape(row['id'])} (system {tex_escape(sysrec['id'])})"
    if repo and norm_url(repo) != norm_url(url):
        if etype == "misc":
            fields.append(("howpublished", r"\url{" + repo + "}"))
        else:
            note += r". Code: \url{" + repo + "}"
    fields.append(("note", note))
    width = max(len(k) for k, _ in fields)
    lines = [(f"% system {sysrec['id']} ({sysrec['name']}); papers.csv row {row['id']}; "
              f"papers.csv venue '{row['venue'].strip() or '(empty)'}'"),
             f"% authors: {meta['authors_src'] or 'NOT RESOLVED'}",
             f"% venue:   {meta['venue_src'] or 'none found; arXiv preprint'}"]
    lines.append(f"@{etype}{{{key},")
    lines += [f"  {k.ljust(width)} = {{{v}}}," for k, v in fields]
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines), meta


def main():
    systems, papers, frame, dist = load_all()
    _mc_keys, mc_eprints, mc_urls = load_must_cite()

    # per-system facts
    info = {}
    for s in sorted(systems, key=lambda x: x["id"]):
        coding = s.get("coding") or {}
        row, _ = choose_record(s, papers, mc_eprints)
        key, in_mc = resolve_citation(s, row, mc_eprints, mc_urls)
        if row is None and not in_mc:
            continue  # unresolvable citation -> not eligible
        stars = max(to_int((frame.get(s["id"]) or {}).get("stars")),
                    to_int((coding.get("stars") or {}).get("value")))
        dom = cell_values(coding.get("target_domain") or {})
        info[s["id"]] = {"sys": s, "row": row, "key": key, "in_mc": in_mc, "stars": stars,
                         "peer": bool(row is not None and is_peer(eff_venue(row)[0])),
                         "domain": dom[0] if dom else "unknown", "coding": coding}

    uses: dict[str, int] = {}
    table_rows = []
    for layer, dim_id, key, n in DIMENSIONS:
        for value, share in top_values(dist, dim_id, n):
            cands = []
            for sid, it in info.items():
                cell = it["coding"].get(key) or {}
                if cell.get("not_reported") or cell.get("unresolved"):
                    continue
                if value not in cell_values(cell):
                    continue
                if uses.get(sid, 0) >= MAX_USES:
                    continue
                cands.append((sid, cell))
            chosen, row_domains = [], set()
            pool = list(cands)
            while pool and len(chosen) < EXEMPLARS_PER_VALUE:
                def score(c, row_domains=row_domains):
                    sid, cell = c
                    it = info[sid]
                    prominent = int(it["peer"]) + int(it["stars"] >= STAR_THRESHOLD or it["in_mc"])
                    quote = '"' in (cell.get("evidence") or "")
                    return (prominent, CONF_RANK.get(cell.get("confidence"), -1),
                            int(quote), int(sid not in uses),
                            int(it["domain"] not in row_domains), int(it["peer"]),
                            it["stars"], tuple(-ord(ch) for ch in sid))
                best = max(pool, key=score)
                pool.remove(best)
                chosen.append(best[0])
                row_domains.add(info[best[0]]["domain"])
            for sid in chosen:
                uses[sid] = uses.get(sid, 0) + 1
            table_rows.append((layer, dim_id, key, value, share, chosen))

    # ---------------------------------------------------------------- corpus.bib
    exemplar_ids = sorted({sid for r in table_rows for sid in r[5]})
    corpus_ids = [sid for sid in exemplar_ids if not info[sid]["in_mc"]]
    if "--refresh-meta" in sys.argv:
        refresh_meta([info[sid]["row"] for sid in corpus_ids])
    cache = json.loads(META_CACHE.read_text(encoding="utf-8")) if META_CACHE.exists() else {}
    entries, metas = [], {}
    for sid in corpus_ids:
        it = info[sid]
        text, meta = bib_entry(it["key"], it["sys"], it["row"], cache)
        entries.append(text)
        metas[sid] = meta
    bib = ["% corpus.bib - GENERATED by scripts/make_layer_exemplars.py - do not edit.",
           "% Title, arXiv id and URL are copied from data/papers.csv; the repository URL from",
           "% data/systems.json. Authors, venue, year and DOI come from the fetched records in",
           "% data/analysis/layer_exemplars_meta.json (arXiv API, Crossref, OpenReview,",
           "% Semantic Scholar); the source URL is given in the comment above each entry.",
           ""]
    OUT_BIB.write_text("\n".join(bib) + "\n\n".join(entries) + "\n", encoding="utf-8", newline="\n")

    # ---------------------------------------------------------------- table
    def brk(k):
        return tex_escape(k).replace("\\_", "\\_\\allowbreak{}")

    def cite(sid):
        it = info[sid]
        name = re.sub(r"\s*\(.*?\)\s*", " ", it["sys"]["name"]).strip()
        return tex_escape(name) + "~\\citep{" + it["key"] + "}"

    out = [
        "% Layer exemplars: principal design values per layer with cited exemplar systems",
        "% GENERATED by scripts/make_layer_exemplars.py - do not edit",
        "% sources: data/analysis/value_distributions.csv, data/systems.json, data/papers.csv,",
        "%          data/coding_frame.csv; citations in references/corpus.bib and references/must_cite.bib",
        "\\begin{table}[tbp]",
        "\\centering",
        "\\footnotesize",
        (f"\\caption{{Principal design values per harness layer, with exemplar systems. "
         f"The share beside each value is the weighted estimate for the {FRAME_N}-system frame, "
         f"computed over systems whose cell for that dimension is reported; multi-valued "
         f"dimensions can sum above 100\\%. Exemplars are coded systems with that value, chosen "
         f"by a fixed rule (prominence, then coding confidence and a verbatim quote, then "
         f"diversity of system and domain; the rule is in the replication package). Listing a "
         f"value documents a design in use; it is not evidence of prevalence beyond the share "
         f"given.}}"),
        "\\label{tab:layer-exemplars}",
        # p-columns (sum 0.90\\linewidth + 3 x 2\\tabcolsep) so the table fits the acmart
        # manuscript text width; cells are ragged-right and keys may break after "_".
        "\\begin{tabular}{@{}p{0.12\\linewidth}p{0.20\\linewidth}p{0.22\\linewidth}p{0.36\\linewidth}@{}}",
        "\\toprule",
        ("\\raggedright Layer & \\raggedright Dimension & \\raggedright Value (weighted share \\%) "
         "& \\raggedright Exemplar systems \\tabularnewline"),
        "\\midrule",
    ]
    prev_layer, prev_dim = None, None
    for layer, dim_id, key, value, share, chosen in table_rows:
        if prev_layer is not None and layer != prev_layer:
            out.append("\\addlinespace")
        lcell = f"{layer} {LAYER_NAMES[layer]}" if layer != prev_layer else ""
        dcell = f"{dim_id} \\texttt{{{brk(key)}}}" if dim_id != prev_dim else ""
        vcell = f"\\texttt{{{brk(value)}}} ({share * 100:.1f})"
        ecell = "; ".join(cite(s) for s in chosen) if chosen else "--"
        out.append(f"\\raggedright {lcell} & \\raggedright {dcell} & \\raggedright {vcell} & "
                   f"\\raggedright {ecell} \\tabularnewline")
        prev_layer, prev_dim = layer, dim_id
    out += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    OUT_TEX.write_text("\n".join(out), encoding="utf-8", newline="\n")

    # ---------------------------------------------------------------- summary
    n_peer = sum(1 for s in exemplar_ids if info[s]["peer"])
    n_auth = sum(1 for m in metas.values() if m["authors"])
    print(f"corpus entries with authors={n_auth}/{len(metas)}; unresolved authors="
          f"{[s for s, m in metas.items() if not m['authors']]}; misc (no venue)="
          f"{[s for s, m in metas.items() if m['etype'] == 'misc']}")
    for v in sorted({(m['venue'], m['year']) for m in metas.values() if m['venue']}):
        print("venue:", v[0], "|", v[1])
    print(f"rows={len(table_rows)} exemplars={len(exemplar_ids)} corpus_entries={len(entries)} "
          f"reused_must_cite={sum(1 for s in exemplar_ids if info[s]['in_mc'])} peer_reviewed={n_peer}")
    for layer, dim_id, key, value, share, chosen in table_rows:
        print(f"{dim_id} {value} {share*100:.1f}: " + ", ".join(
            f"{s}[{info[s]['key']}|{'P' if info[s]['peer'] else '-'}|{info[s]['stars']}|{info[s]['domain']}"
            f"|{(info[s]['row'] or {}).get('id','')}]" for s in chosen))


if __name__ == "__main__":
    main()
