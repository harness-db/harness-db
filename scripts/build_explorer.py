#!/usr/bin/env python
"""Build the single-file static HARNESS-DB explorer: ``explorer/index.html``.

WHAT IT WRITES
--------------
One self-contained HTML file: inline CSS, inline JavaScript, no CDN, no build step. The dataset is
embedded as gzip + base64 inside a ``<script type="application/octet-stream">`` element and
inflated in the browser with the standard ``DecompressionStream`` API, so the page works from
``file://``, offline, and from GitHub Pages alike. If the encoded payload ever exceeds
``EMBED_LIMIT`` (8 MB) the script instead writes ``explorer/data.json`` beside the page and the page
fetches it (that mode needs a web server; ``file://`` fetches are blocked by browsers).

WHAT IS EMBEDDED
----------------
Everything a visitor needs to audit a cell and nothing else: per system the id, name, aliases,
version label, repository URL, the pinned commit SHA (parsed from the coded ``pinned_version``, M6,
falling back to ``version_label``), the paper ids, and the 38 cells. A cell is
``[state, value, confidence, quote, locator, note, coder]`` with trailing nulls dropped, where
state 0 = coded value, 1 = ``not_reported`` (sources read and silent), 2 = ``unresolved`` (the
coder could not settle it; excluded from every rate). ``evidence`` is split into the verbatim quote
and its locator at the last ``" (`` of the ``"quote" (locator)`` convention; an evidence string
that does not follow the convention is kept whole as the quote with an empty locator. Paper titles
come from ``data/papers.csv``.

Integer dimensions (``tool_count``, ``stars``) are faceted in the same data-derived quartile bins
``analyse_descriptives.py`` tabulates (numpy's default linear quantile, re-implemented here so the
build needs only the standard library); dates facet by year; ``pinned_version`` facets by whether a
commit SHA was recorded.

The build is deterministic (gzip mtime 0, sorted keys, no timestamp): the same inputs give a
byte-identical page, and an unchanged page is not rewritten. It never modifies ``data/``.

Run:
    python scripts/build_explorer.py                 # writes explorer/index.html
    python scripts/build_explorer.py --paper-url https://arxiv.org/abs/XXXX.XXXXX
"""
from __future__ import annotations

import argparse
import base64
import bisect
import csv
import gzip
import hashlib
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SYSTEMS = ROOT / "data" / "systems.json"
DEFAULT_DIMS = ROOT / "schema" / "dimensions.json"
DEFAULT_PAPERS = ROOT / "data" / "papers.csv"
DEFAULT_CFF = ROOT / "CITATION.cff"
DEFAULT_OUT = ROOT / "explorer" / "index.html"
EMBED_LIMIT = 8_000_000  # bytes of base64 payload; above this the data goes to a sidecar file
FALLBACK_REPO = "https://github.com/harness-db/harness-db"

STATE_VALUE, STATE_NOT_REPORTED, STATE_UNRESOLVED = 0, 1, 2
CONFIDENCE = {"low": 0, "medium": 1, "high": 2}
SHA_RE = re.compile(r"\b([0-9a-f]{7,40})\b")
PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")


# ------------------------------------------------------------------------------------ inputs


def read_citation(path: Path) -> dict:
    """The few CITATION.cff fields the footer needs, by regex (no YAML dependency)."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""

    def field(name: str, block: str = text) -> str:
        m = re.search(rf"^\s*{name}:\s*\"?([^\"\n]+?)\"?\s*$", block, re.MULTILINE)
        return m.group(1).strip() if m else ""

    pref = text.split("preferred-citation:", 1)[1] if "preferred-citation:" in text else ""
    return {
        "title": field("title"),
        "version": field("version"),
        "repo": field("repository-code") or FALLBACK_REPO,
        "family": field("family-names"),
        "given": field("given-names"),
        "paper_title": field("title", pref),
        "paper_year": field("year", pref),
        "paper_journal": field("journal", pref),
        "paper_url": field("url", pref),
        "paper_doi": field("doi", pref),
    }


def split_evidence(evidence: str) -> tuple[str, str]:
    """``"quote" (locator)`` -> (quote, locator); anything else -> (whole string, "")."""
    ev = (evidence or "").strip()
    if ev.startswith('"') and ev.endswith(")"):
        i = ev.rfind('" (')
        if i > 0:
            return ev[1:i], ev[i + 3:-1]
    return ev, ""


def cell_state(cell: dict, sid: str, key: str) -> int:
    if cell.get("unresolved"):
        return STATE_UNRESOLVED
    if cell.get("not_reported"):
        return STATE_NOT_REPORTED
    if cell.get("value") is None:
        raise ValueError(f"{sid}.{key}: no value and neither not_reported nor unresolved")
    return STATE_VALUE


def pinned_sha(system: dict) -> tuple[str | None, str | None]:
    """(commit SHA, human label) from the coded pinned_version (M6), else from version_label."""
    pv = (system.get("coding") or {}).get("pinned_version") or {}
    for label in (pv.get("value") if not pv.get("not_reported") else None,
                  system.get("version_label")):
        if isinstance(label, str):
            m = SHA_RE.search(label)
            if m:
                return m.group(1), label
    return None, None


def _quantile(sorted_vals: list[float], q: float) -> float:
    """numpy.quantile's default ('linear') method."""
    pos = (len(sorted_vals) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def numeric_bins(values: list[float]) -> tuple[dict[str, str], list[str]]:
    """Quartile bins labelled from the data, as analyse_descriptives._numeric_bin_labels does.

    Returns ({str(int value): label}, labels in ascending order)."""
    arr = sorted(float(v) for v in values)
    if not arr:
        return {}, []
    edges = sorted({_quantile(arr, q) for q in (0.0, 0.25, 0.5, 0.75, 1.0)})
    out: dict[str, str] = {}
    order: list[tuple[float, str]] = []
    for v in arr:
        if len(edges) < 2:
            label, lo = f"{int(v)}", v
        else:
            idx = bisect.bisect_right(edges[1:-1], v) if len(edges) > 2 else 0
            lo = edges[idx]
            hi = edges[idx + 1] if idx + 1 < len(edges) else edges[-1]
            label = f"{int(lo)}-{int(hi)}" if hi > lo else f"{int(lo)}"
        out[str(int(v))] = label
        if (lo, label) not in order:
            order.append((lo, label))
    return out, [label for _, label in sorted(order)]


def paper_url(row: dict) -> str:
    if row.get("url", "").startswith(("http://", "https://")):
        return row["url"]
    if row.get("doi"):
        return f"https://doi.org/{row['doi']}"
    if row.get("arxiv_id"):
        return f"https://arxiv.org/abs/{row['arxiv_id']}"
    return ""


# --------------------------------------------------------------------------------- payload


def build_payload(systems: list[dict], dims_doc: dict, papers: dict[str, dict], meta: dict) -> dict:
    dims = dims_doc["dimensions"]
    keys = [d["key"] for d in dims]
    coders: list[str] = []
    coder_idx: dict[str, int] = {}
    paper_ids: list[str] = []
    paper_idx: dict[str, int] = {}

    out_dims = []
    for d in dims:
        spec = {"id": d["id"], "key": d["key"], "layer": d["layer"], "name": d["name"],
                "type": d["type"], "multi": bool(d.get("multi")), "values": d.get("values") or []}
        if d["type"] == "integer":
            raw = [s["coding"][d["key"]]["value"] for s in systems
                   if not s["coding"][d["key"]].get("not_reported")
                   and not s["coding"][d["key"]].get("unresolved")
                   and s["coding"][d["key"]].get("value") is not None]
            spec["bins"], spec["binOrder"] = numeric_bins(raw)
        out_dims.append(spec)

    out_systems = []
    for s in systems:
        coding = s.get("coding") or {}
        missing = [k for k in keys if k not in coding]
        if missing:
            raise ValueError(f"{s['id']}: missing dimension(s) {missing}")
        cells = []
        for k in keys:
            c = coding[k]
            st = cell_state(c, s["id"], k)
            quote, loc = split_evidence(c.get("evidence") or "")
            coder = c.get("coder") or ""
            if coder not in coder_idx:
                coder_idx[coder] = len(coders)
                coders.append(coder)
            cell = [st, c.get("value") if st == STATE_VALUE else None,
                    CONFIDENCE.get(c.get("confidence")), quote or None, loc or None,
                    c.get("note") or None, coder_idx[coder]]
            while cell and cell[-1] is None:
                cell.pop()
            cells.append(cell)
        pids = []
        for pid in s.get("papers") or []:
            if pid not in paper_idx:
                paper_idx[pid] = len(paper_ids)
                paper_ids.append(pid)
            pids.append(paper_idx[pid])
        sha, pin_label = pinned_sha(s)
        rec = {"i": s["id"], "n": s["name"], "p": pids, "c": cells,
               "r": (s.get("urls") or {}).get("repo"), "sha": sha, "pin": pin_label,
               "al": s.get("aliases"), "vl": s.get("version_label"),
               "at": s.get("coded_at"), "nt": s.get("notes")}
        out_systems.append({k: v for k, v in rec.items() if v not in (None, [], "")} | {"p": pids})

    out_papers = []
    for pid in paper_ids:
        row = papers.get(pid) or {}
        out_papers.append([pid, row.get("title") or pid, row.get("year") or "",
                           row.get("venue") or "", paper_url(row)])

    return {"meta": meta, "layers": [{"id": la["id"], "name": la["name"]}
                                     for la in dims_doc["layers"]],
            "dims": out_dims, "coders": coders, "papers": out_papers, "systems": out_systems}


def encode_payload(payload: dict) -> tuple[bytes, str]:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    raw_bytes = raw.encode("utf-8")
    return raw_bytes, base64.b64encode(gzip.compress(raw_bytes, compresslevel=9, mtime=0)).decode()


# ------------------------------------------------------------------------------------ render


def render(payload: dict, b64: str | None, cite: dict) -> str:
    meta = payload["meta"]
    if b64 is not None:
        data_el = ('<script id="hdb-data" type="application/octet-stream" '
                   f'data-encoding="gzip+base64">{b64}</script>')
    else:
        data_el = ('<script id="hdb-data" type="application/json" '
                   'data-src="data.json"></script>')
    e = html.escape
    repl = {
        "__N_SYSTEMS__": f"{meta['n_systems']:,}",
        "__N_DIMS__": str(meta["n_dims"]),
        "__N_LAYERS__": str(meta["n_layers"]),
        "__VERSION__": e(meta["version"]),
        "__SCHEMA_VERSION__": e(meta["schema_version"]),
        "__DATA_SHA__": e(meta["data_sha256"]),
        "__CITATION__": e(meta["citation"]),
        "__CARD_URL__": e(meta["card_url"], quote=True),
        "__PAPER_URL__": e(meta["paper_url"], quote=True),
        "__REPO_URL__": e(meta["repo_url"], quote=True),
        "__MANUAL_URL__": e(meta["manual_url"], quote=True),
        "__DATA_SCRIPT__": data_el,
    }
    out = TEMPLATE
    for k, v in repl.items():
        out = out.replace(k, v)
    left = PLACEHOLDER_RE.findall(out.replace(data_el, ""))
    if left:
        raise RuntimeError(f"unfilled template placeholder(s): {sorted(set(left))}")
    return out


def build(systems_path: Path = DEFAULT_SYSTEMS, dims_path: Path = DEFAULT_DIMS,
          papers_path: Path = DEFAULT_PAPERS, cff_path: Path = DEFAULT_CFF,
          out_path: Path = DEFAULT_OUT, paper_url_override: str | None = None,
          card_url_override: str | None = None, embed_limit: int = EMBED_LIMIT) -> dict:
    systems_bytes = systems_path.read_bytes()
    systems = json.loads(systems_bytes.decode("utf-8"))
    dims_doc = json.loads(dims_path.read_text(encoding="utf-8"))
    with papers_path.open(encoding="utf-8", newline="") as fh:
        papers = {row["id"]: row for row in csv.DictReader(fh)}
    cite = read_citation(cff_path)
    repo = cite["repo"].rstrip("/")
    paper_link = (paper_url_override or cite["paper_url"]
                  or (f"https://doi.org/{cite['paper_doi']}" if cite["paper_doi"] else "")
                  or f"{repo}/tree/main/paper")
    author = f"{cite['family']}, {cite['given'][:1]}." if cite["family"] else "Gurram, B."
    citation = (f"{author} ({cite['paper_year'] or 'n.d.'}). {cite['paper_title']}. "
                f"{cite['paper_journal']}. Dataset: HARNESS-DB v{cite['version']} "
                f"(CC BY 4.0), {repo}.").replace(". .", ".")
    meta = {
        "version": cite["version"] or "unversioned",
        "schema_version": dims_doc.get("schema_version", ""),
        "n_systems": len(systems),
        "n_dims": len(dims_doc["dimensions"]),
        "n_layers": len(dims_doc["layers"]),
        "data_sha256": hashlib.sha256(systems_bytes).hexdigest()[:12],
        "repo_url": repo,
        "card_url": card_url_override or f"{repo}/blob/main/data/README.md",
        "paper_url": paper_link,
        "manual_url": f"{repo}/blob/main/docs/coding_manual.md",
        "citation": citation,
        "licence": "CC BY 4.0",
    }
    payload = build_payload(systems, dims_doc, papers, meta)
    raw_bytes, b64 = encode_payload(payload)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = out_path.parent / "data.json"
    mode = "embedded" if len(b64) <= embed_limit else "sidecar"
    if mode == "embedded":
        page = render(payload, b64, cite)
        if sidecar.exists():
            sidecar.unlink()  # a stale sidecar from an earlier oversize build would mislead
    else:
        page = render(payload, None, cite)
        sidecar.write_bytes(raw_bytes)
    page_bytes = page.encode("utf-8")
    changed = not out_path.exists() or out_path.read_bytes() != page_bytes
    if changed:
        out_path.write_bytes(page_bytes)
    return {"out": str(out_path), "mode": mode, "bytes": len(page_bytes),
            "payload_json_bytes": len(raw_bytes), "payload_b64_bytes": len(b64),
            "n_systems": len(systems), "changed": changed}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--systems", type=Path, default=DEFAULT_SYSTEMS)
    ap.add_argument("--dims", type=Path, default=DEFAULT_DIMS)
    ap.add_argument("--papers", type=Path, default=DEFAULT_PAPERS)
    ap.add_argument("--cff", type=Path, default=DEFAULT_CFF)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--paper-url", default=None,
                    help="link for 'the paper' in the footer (default: CITATION.cff, else repo)")
    ap.add_argument("--card-url", default=None, help="link for the dataset card")
    args = ap.parse_args(argv)
    info = build(args.systems, args.dims, args.papers, args.cff, args.out,
                 args.paper_url, args.card_url)
    state = "written" if info["changed"] else "unchanged"
    print(f"explorer: {info['out']} {state} ({info['bytes'] / 1e6:.2f} MB, data {info['mode']}, "
          f"{info['n_systems']} systems; payload {info['payload_json_bytes'] / 1e6:.2f} MB JSON "
          f"-> {info['payload_b64_bytes'] / 1e6:.2f} MB gzip+base64)")
    return 0


# ---------------------------------------------------------------------------------- template

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="HARNESS-DB explorer: __N_SYSTEMS__ LLM agent harnesses coded on __N_DIMS__ dimensions, every cell with a verbatim quote and locator.">
<title>HARNESS-DB explorer</title>
<style>
:root{
  --bg:#f7f7f5;--surface:#ffffff;--ink:#161616;--ink2:#3d3d3d;--muted:#5f5f5f;
  --line:#d6d6d2;--line2:#9a9a95;--accent:#1d4f91;--val-bg:#e4ebf5;--val-line:#2f4f7a;
  --fill:#2a2a2a;--track:#ffffff;--hatch:#8a8a8a;--chip-bg:#f0f0ee;
  --radius:4px;--gap:16px;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#121212;--surface:#1b1b1b;--ink:#ededed;--ink2:#cfcfcf;--muted:#a3a3a3;
    --line:#343434;--line2:#6e6e6e;--accent:#9dbcec;--val-bg:#22324a;--val-line:#9dbcec;
    --fill:#e6e6e6;--track:#1b1b1b;--hatch:#8f8f8f;--chip-bg:#262626;color-scheme:dark;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.5}
a{color:var(--accent)}
a:hover{text-decoration-thickness:2px}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.wrap{max-width:1320px;margin:0 auto;padding:0 16px}
.skip{position:absolute;left:-9999px}
.skip:focus{left:16px;top:8px;background:var(--surface);padding:6px 10px;z-index:10}
.vh{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
header.site{background:var(--surface);border-bottom:1px solid var(--line);padding:18px 0 14px}
header.site h1{margin:0;font-size:1.35rem;letter-spacing:-.01em}
header.site h1 a{color:inherit;text-decoration:none}
header.site h1 span{font-weight:400;color:var(--muted)}
.lede{margin:.25rem 0 .75rem;color:var(--ink2);max-width:70ch}
.searchbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.searchbar input{flex:1 1 280px;min-width:0;font:inherit;padding:9px 12px;border:1px solid var(--line2);
  border-radius:var(--radius);background:var(--bg);color:var(--ink)}
kbd{font:12px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;border:1px solid var(--line2);
  border-bottom-width:2px;border-radius:3px;padding:2px 5px;background:var(--chip-bg)}
button,.btn{font:inherit;font-size:.9rem;color:var(--ink);background:var(--surface);border:1px solid var(--line2);
  border-radius:var(--radius);padding:6px 11px;cursor:pointer;min-height:36px;text-decoration:none;display:inline-flex;align-items:center;gap:6px}
button:hover,.btn:hover{border-color:var(--ink2)}
button[disabled]{opacity:.45;cursor:default}
.linkbtn{border:0;background:none;padding:0;min-height:0;color:var(--accent);text-decoration:underline;font-size:inherit}
section.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;margin:16px 0}
h2{font-size:1.1rem;margin:0 0 .4rem}
h3{font-size:1rem;margin:0}
.muted{color:var(--muted)}
.small{font-size:.85rem}
/* -------- the three cell states: solid / dashed-empty / hatched, each with a glyph and a word */
.st{display:inline-flex;align-items:center;gap:.3em;border-radius:3px;padding:0 .45em;font-size:.85em;
  line-height:1.65;white-space:nowrap;border:1px solid transparent;max-width:100%}
.st-v{background:var(--val-bg);border-color:var(--val-line);border-style:solid;color:var(--ink)}
.st-nr{border:1px dashed var(--line2);color:var(--muted);font-style:italic;background:transparent}
.st-un{border:2px double var(--ink2);color:var(--ink);
  background:repeating-linear-gradient(135deg,transparent 0 4px,var(--line) 4px 6px)}
.st .g{font-style:normal;font-weight:700}
.cell .st,.facts .st{white-space:normal;overflow-wrap:anywhere}
.cell>*{min-width:0}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.legend{display:grid;grid-template-columns:auto 1fr;gap:6px 12px;align-items:center;margin:0}
.legend dt{margin:0}.legend dd{margin:0;color:var(--ink2)}
/* -------- silence bars: filled = reported, empty dashed track = not reported */
.sil-head{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline;justify-content:space-between}
.sil-hero{font-size:1.9rem;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.sil-list{list-style:none;margin:10px 0 0;padding:0}
.sil-row{display:grid;grid-template-columns:minmax(150px,230px) minmax(0,1fr) 250px;gap:4px 12px;align-items:center;
  width:100%;text-align:left;border:0;background:none;padding:5px 4px;border-radius:var(--radius);min-height:36px}
.sil-row:hover{background:var(--chip-bg)}
button.sil-row{cursor:pointer}
.sil-row .lab{font-weight:600}
.sil-sub .sil-row .lab{font-weight:400;padding-left:18px}
.bar{position:relative;height:14px;border:1px dashed var(--line2);border-radius:2px;background:var(--track);overflow:hidden}
.bar>i{position:absolute;left:0;top:0;bottom:0;background:var(--fill);border-right:2px solid var(--surface)}
.sil-row .num{font-variant-numeric:tabular-nums;font-size:.88rem;color:var(--ink2)}
.sil-row .num b{color:var(--ink)}
.sil-sub{list-style:none;margin:2px 0 8px;padding:0;border-left:2px solid var(--line)}
.sil-key{display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:.85rem;color:var(--ink2);margin-top:8px}
.sw{display:inline-block;width:22px;height:11px;vertical-align:-1px;margin-right:5px;border-radius:2px}
.sw-fill{background:var(--fill)}.sw-empty{border:1px dashed var(--line2);background:var(--track)}
.showsilent{font-size:.8rem}
/* -------- layout */
.layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:var(--gap);align-items:start}
@media (max-width:900px){.layout{grid-template-columns:minmax(0,1fr)}.sil-row{grid-template-columns:minmax(0,1fr);gap:3px}.searchbar .hint{display:none}}
#filters-box{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius)}
#filters-box>summary{padding:10px 14px;font-weight:600;cursor:pointer;min-height:40px}
#filters{padding:0 10px 12px}
details.layer{border-top:1px solid var(--line)}
details.layer>summary{padding:8px 4px;cursor:pointer;font-weight:600;list-style-position:inside}
details.layer>summary .cnt{font-weight:400;color:var(--muted);font-size:.85rem}
fieldset.dim{border:0;margin:0 0 10px;padding:0 0 0 4px;min-width:0}
fieldset.dim legend{font-size:.88rem;font-weight:600;padding:0;margin-bottom:2px}
fieldset.dim legend .id{color:var(--muted);font-weight:400;margin-right:4px}
.opt{display:flex;align-items:center;gap:6px;font-size:.88rem;padding:2px 0;min-height:30px;cursor:pointer}
.opt input{width:17px;height:17px;margin:0;flex:none;accent-color:var(--accent)}
.opt .t{flex:1;min-width:0;overflow-wrap:anywhere}
.opt .c{font-variant-numeric:tabular-nums;color:var(--muted);font-size:.8rem}
.opt.zero{color:var(--muted)}
.opt.offschema .t::after{content:" (off-schema)";color:var(--muted);font-size:.75rem}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin-bottom:8px}
.toolbar .count{font-weight:600}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
details.menu{position:relative}
details.menu>summary{list-style:none}
details.menu>summary::-webkit-details-marker{display:none}
details.menu .pop{position:absolute;right:0;z-index:5;margin-top:4px;background:var(--surface);border:1px solid var(--line2);
  border-radius:var(--radius);padding:10px 12px;width:min(92vw,560px);max-height:65vh;overflow:auto;box-shadow:0 6px 24px rgba(0,0,0,.18)}
.colgrid{columns:2 220px;column-gap:16px}
.colgrid .grp{break-inside:avoid;margin-bottom:8px}
.colgrid .grp b{font-size:.8rem;color:var(--muted);display:block}
.active{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;padding:0;list-style:none}
.active button{font-size:.82rem;padding:3px 8px;min-height:30px;background:var(--chip-bg)}
.tablewrap{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius)}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:left;vertical-align:top;padding:7px 10px;border-bottom:1px solid var(--line)}
thead th{position:sticky;top:0;background:var(--surface);z-index:1;border-bottom:2px solid var(--line2);white-space:nowrap}
th button{border:0;background:none;padding:0;min-height:0;font-weight:600;font-size:.88rem;color:var(--ink)}
th[aria-sort] button::after{content:" \25B2";font-size:.7em}
th[aria-sort=descending] button::after{content:" \25BC"}
td.name a{font-weight:600}
td .sub{display:block;color:var(--muted);font-size:.8rem;overflow-wrap:anywhere}
td.numc{font-variant-numeric:tabular-nums;text-align:right}
tbody tr:hover{background:var(--chip-bg)}
.pager{display:flex;gap:8px;align-items:center;justify-content:flex-end;margin-top:10px;flex-wrap:wrap}
.empty{padding:28px 16px;text-align:center}
/* -------- system page */
.sys-nav{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin:16px 0 4px}
.sys-head h2{font-size:1.6rem;margin:.2rem 0}
.facts{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:.6rem 0 0}
.facts dt{color:var(--muted)}.facts dd{margin:0;overflow-wrap:anywhere}
.facts ul{margin:0;padding-left:1.1em}
.strip{display:flex;flex-wrap:wrap;gap:10px;margin:.6rem 0 0}
.strip .grp{display:flex;gap:2px;align-items:center}
.strip .grp b{font-size:.75rem;color:var(--muted);margin-right:3px}
.sq{width:14px;height:14px;border-radius:2px;display:inline-block}
.sq.v{background:var(--fill)}.sq.nr{border:1px dashed var(--line2)}
.sq.un{border:1px solid var(--ink2);background:repeating-linear-gradient(135deg,transparent 0 2px,var(--ink2) 2px 3px)}
.layerblock{margin:18px 0}
.layerblock>h3{padding-bottom:4px;border-bottom:2px solid var(--line2)}
.cell{display:grid;grid-template-columns:minmax(160px,250px) minmax(0,1fr);gap:4px 16px;padding:10px 0;border-bottom:1px solid var(--line)}
@media (max-width:700px){.cell{grid-template-columns:1fr}}
.cell .dn{font-weight:600}
.cell .dn .id{color:var(--muted);font-weight:400;margin-right:5px}
.cell .dn .k{display:block;font-weight:400;font-size:.78rem;color:var(--muted);font-family:ui-monospace,Menlo,Consolas,monospace}
.cell blockquote{margin:6px 0 2px;padding:4px 10px;border-left:3px solid var(--line2);color:var(--ink2);white-space:pre-wrap;overflow-wrap:anywhere}
.cell .loc{font-size:.85rem;color:var(--ink2);overflow-wrap:anywhere}
.cell .loc code{font-size:.82rem}
.cell .note{font-size:.85rem;color:var(--muted);margin:4px 0 0}
.cell .conf{font-size:.8rem;color:var(--muted);margin-left:6px}
footer{border-top:1px solid var(--line);margin-top:32px;padding:18px 0 40px;background:var(--surface);font-size:.88rem;color:var(--ink2)}
footer p{margin:.35rem 0;max-width:95ch}
footer .cite{font-family:ui-serif,Georgia,serif}
#loading{padding:24px 0}
[tabindex="-1"]:focus{outline:none}
main,.panel,.layout>*{min-width:0}
.legend{grid-template-columns:auto minmax(0,1fr)}
@media print{header.site .searchbar,#filters-box,.tools,.pager,.sys-nav{display:none}.layout{display:block}}
@media (forced-colors: active){.bar>i,.sq.v{background:CanvasText}.st-un,.sq.un{background:none}}
</style>
</head>
<body>
<a class="skip" href="#results">Skip to results</a>
<header class="site">
  <div class="wrap">
    <h1><a href="#" id="home">HARNESS-DB</a> <span>explorer</span></h1>
    <p class="lede">__N_SYSTEMS__ LLM agent harnesses (2022&ndash;2026), each coded on __N_DIMS__ design dimensions in __N_LAYERS__ layers. Every coded cell carries a verbatim quote and a locator; where the sources are silent, the cell says so.</p>
    <div class="searchbar" role="search">
      <label class="vh" for="q">Search systems by name, repository or paper title</label>
      <input id="q" type="search" placeholder="Search name, repository or paper title" autocomplete="off" spellcheck="false">
      <span class="small muted hint">Press <kbd>/</kbd> to search</span>
    </div>
  </div>
</header>
<main id="main" class="wrap">
  <noscript><p>This explorer needs JavaScript. The same data is in <code>data/systems.json</code> in the repository.</p></noscript>
  <p id="loading" role="status">Loading __N_SYSTEMS__ systems&hellip;</p>
  <section class="panel" id="legend-panel" aria-labelledby="legend-h" hidden>
    <h2 id="legend-h" class="vh">How to read a cell</h2>
    <dl class="legend">
      <dt><span class="st st-v">value</span></dt><dd>a coded value, backed by a verbatim quote and a locator.</dd>
      <dt><span class="st st-nr"><span class="g" aria-hidden="true">&empty;</span>not reported</span></dt><dd><code>not_reported</code> = sources read and silent.</dd>
      <dt><span class="st st-un"><span class="g" aria-hidden="true">?</span>unresolved</span></dt><dd><code>unresolved</code> = the coder could not settle it (excluded from rates).</dd>
    </dl>
  </section>
  <div id="list-view" hidden>
    <section class="panel" id="silence" aria-labelledby="silence-h">
      <div class="sil-head">
        <div>
          <h2 id="silence-h">Where the sources go silent</h2>
          <p class="small muted" id="sil-scope"></p>
        </div>
        <div><span class="sil-hero" id="sil-hero"></span> <span class="small muted">of cells not reported</span></div>
      </div>
      <ul class="sil-list" id="sil-list"></ul>
      <div class="sil-key" aria-hidden="true">
        <span><i class="sw sw-fill"></i>reported (coded value)</span>
        <span><i class="sw sw-empty"></i>not reported</span>
        <span>Rate = not reported &divide; (coded + not reported); unresolved cells are counted but excluded.</span>
      </div>
    </section>
    <div class="layout">
      <details id="filters-box" open>
        <summary>Filters <span id="nfilters" class="muted small"></span></summary>
        <div id="filters" role="group" aria-label="Filter by dimension"></div>
      </details>
      <section id="results" tabindex="-1" aria-labelledby="results-count">
        <div class="toolbar">
          <div class="count" id="results-count" role="status" aria-live="polite"></div>
          <div class="tools">
            <details class="menu" id="colmenu">
              <summary class="btn" role="button">Columns</summary>
              <div class="pop" id="colpop"></div>
            </details>
            <button type="button" id="csv">Export CSV</button>
            <button type="button" id="copylink">Copy link</button>
          </div>
        </div>
        <ul class="active" id="active" aria-label="Active filters"></ul>
        <div class="tablewrap"><table id="tbl"><caption class="vh">Systems matching the current filter</caption><thead></thead><tbody></tbody></table></div>
        <div class="pager" id="pager"></div>
      </section>
    </div>
  </div>
  <article id="system-view" hidden aria-live="polite"></article>
</main>
<footer>
  <div class="wrap">
    <p><strong>HARNESS-DB v__VERSION__</strong> &middot; schema v__SCHEMA_VERSION__ &middot; __N_SYSTEMS__ systems &middot; data <code>systems.json</code> sha256 <code>__DATA_SHA__</code></p>
    <p>Data licence: <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>. Explorer code: MIT.
      <a href="__CARD_URL__">Dataset card</a> &middot; <a href="__PAPER_URL__">Paper</a> &middot; <a href="__MANUAL_URL__">Coding manual</a> &middot; <a href="__REPO_URL__">Repository</a></p>
    <p class="cite">Cite: __CITATION__</p>
    <p class="small muted">Rates here are unweighted shares over the systems in view; the paper reports stratum-weighted estimates, which differ. This page holds the whole dataset and works offline once saved. Keys: <kbd>/</kbd> search, <kbd>&uarr;</kbd><kbd>&darr;</kbd> move between rows, <kbd>[</kbd> <kbd>]</kbd> previous / next system, <kbd>Esc</kbd> back to results.</p>
  </div>
</footer>
__DATA_SCRIPT__
<script id="hdb-core">
/* Pure data logic: no DOM access, so it runs under node for the smoke test. */
var HDB = (function () {
  'use strict';
  var NR = '!not_reported', UN = '!unresolved';
  var STATE_TOKENS = [null, NR, UN];
  var STATE_LABEL = ['value', 'not reported', 'unresolved'];
  var DEFAULT_COLS = ['target_domain', 'loop_primitives', 'multi_agent_topology', 'execution_isolation', '#silent'];
  var META_COLS = [
    {key: '#repo', name: 'Repository'}, {key: '#papers', name: 'Papers'},
    {key: '#silent', name: 'Cells not reported'}, {key: '#unres', name: 'Cells unresolved'}
  ];
  var PAGE = 50;

  function b64ToBytes(b64) {
    var bin = atob(b64), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  async function decode(b64) {
    if (typeof DecompressionStream === 'undefined') throw new Error('This browser lacks DecompressionStream; please use a current Chrome, Edge, Firefox or Safari.');
    var stream = new Blob([b64ToBytes(b64.trim())]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }

  function tokensFor(dim, cell) {
    var st = cell[0];
    if (st) return [STATE_TOKENS[st]];
    var v = cell[1];
    if (dim.type === 'integer') return [(dim.bins && dim.bins[String(v)]) || String(v)];
    if (dim.type === 'date') return [String(v).slice(0, 4)];
    if (dim.type === 'string') return [/\b[0-9a-f]{7,40}\b/.test(String(v)) ? 'with commit SHA' : 'label only'];
    return Array.isArray(v) ? v.map(String) : [String(v)];
  }

  function prepare(raw) {
    var d = raw;
    d.dimByKey = {};
    d.dims.forEach(function (dim, i) { dim.idx = i; d.dimByKey[dim.key] = dim; });
    d.layerById = {};
    d.layers.forEach(function (l) { l.dims = []; d.layerById[l.id] = l; });
    d.dims.forEach(function (dim) { d.layerById[dim.layer].dims.push(dim); });
    d.byId = {};
    var seen = d.dims.map(function () { return {}; });
    d.systems.forEach(function (s, si) {
      s.idx = si; d.byId[s.i] = s;
      s.nNr = 0; s.nUn = 0;
      s.tok = s.c.map(function (cell, di) {
        if (cell[0] === 1) s.nNr++; else if (cell[0] === 2) s.nUn++;
        var t = tokensFor(d.dims[di], cell);
        t.forEach(function (x) { seen[di][x] = true; });
        return t;
      });
      var titles = (s.p || []).map(function (pi) { return d.papers[pi][1]; });
      s.hay = [s.n, s.i, (s.al || []).join(' '), s.r || '', s.vl || '', titles.join(' ')].join(' \u0001 ').toLowerCase();
    });
    d.dims.forEach(function (dim, di) {
      var base;
      if (dim.type === 'enum') base = dim.values.slice();
      else if (dim.type === 'integer') base = (dim.binOrder || []).slice();
      else if (dim.type === 'string') base = ['with commit SHA', 'label only'];
      else base = Object.keys(seen[di]).filter(function (x) { return x !== NR && x !== UN; }).sort();
      var extra = Object.keys(seen[di]).filter(function (x) { return x !== NR && x !== UN && base.indexOf(x) < 0; }).sort();
      dim.offschema = {};
      extra.forEach(function (x) { dim.offschema[x] = true; });
      dim.facetOrder = base.concat(extra, [NR, UN]);
    });
    return d;
  }

  function terms(q) { return (q || '').toLowerCase().split(/\s+/).filter(Boolean); }

  function matches(s, st, skip) {
    var ts = st._terms || (st._terms = terms(st.q));
    for (var i = 0; i < ts.length; i++) if (s.hay.indexOf(ts[i]) < 0) return false;
    for (var k in st.f) {
      if (k === skip) continue;
      var set = st.f[k], toks = s.tok[st._dimIdx[k]], hit = false;
      for (var j = 0; j < toks.length; j++) if (set[toks[j]]) { hit = true; break; }
      if (!hit) return false;
    }
    return true;
  }

  function normalise(d, st) {
    st._dimIdx = {};
    Object.keys(st.f).forEach(function (k) {
      if (!d.dimByKey[k] || !Object.keys(st.f[k]).length) delete st.f[k];
      else st._dimIdx[k] = d.dimByKey[k].idx;
    });
    st._terms = terms(st.q);
    return st;
  }

  function cellText(dim, cell) {
    if (cell[0]) return STATE_LABEL[cell[0]].replace(' ', '_');
    var v = cell[1];
    return Array.isArray(v) ? v.join(';') : String(v);
  }

  function sortKey(d, s, key) {
    if (key === 'name') return [0, s.n.toLowerCase()];
    if (key === '#silent') return [0, s.nNr];
    if (key === '#unres') return [0, s.nUn];
    if (key === '#papers') return [0, (s.p || []).length];
    if (key === '#repo') return s.r ? [0, s.r.toLowerCase()] : [1, ''];
    var dim = d.dimByKey[key];
    if (!dim) return [0, ''];
    var cell = s.c[dim.idx];
    if (cell[0]) return [cell[0], ''];
    var v = cell[1];
    if (typeof v === 'number') return [0, v];
    return [0, (Array.isArray(v) ? v.join(';') : String(v)).toLowerCase()];
  }

  function filter(d, st) {
    normalise(d, st);
    var out = d.systems.filter(function (s) { return matches(s, st, null); });
    var key = st.sort.key, dir = st.sort.dir;
    var keys = out.map(function (s) { return sortKey(d, s, key); });
    var ix = out.map(function (_, i) { return i; });
    ix.sort(function (a, b) {
      var ka = keys[a], kb = keys[b];
      if (ka[0] !== kb[0]) return ka[0] - kb[0];            /* coded first, then silent, then unresolved */
      var c = typeof ka[1] === 'number' ? ka[1] - kb[1] : (ka[1] < kb[1] ? -1 : ka[1] > kb[1] ? 1 : 0);
      if (c === 0) c = out[a].n.toLowerCase() < out[b].n.toLowerCase() ? -1 : 1;
      return dir * c;
    });
    return ix.map(function (i) { return out[i]; });
  }

  function facetCounts(d, st, key) {
    normalise(d, st);
    var di = d.dimByKey[key].idx, counts = {};
    d.systems.forEach(function (s) {
      if (!matches(s, st, key)) return;
      s.tok[di].forEach(function (t) { counts[t] = (counts[t] || 0) + 1; });
    });
    return counts;
  }

  function silence(d, systems) {
    function blank() { return {val: 0, nr: 0, un: 0}; }
    var perDim = d.dims.map(blank), tot = blank();
    systems.forEach(function (s) {
      s.c.forEach(function (cell, di) {
        var b = perDim[di];
        if (cell[0] === 1) b.nr++; else if (cell[0] === 2) b.un++; else b.val++;
      });
    });
    function rate(b) { var base = b.val + b.nr; b.base = base; b.rate = base ? b.nr / base : null; return b; }
    var layers = d.layers.map(function (l) {
      var agg = blank();
      var dims = l.dims.map(function (dim) {
        var b = rate(perDim[dim.idx]);
        agg.val += b.val; agg.nr += b.nr; agg.un += b.un;
        return {key: dim.key, id: dim.id, name: dim.name, val: b.val, nr: b.nr, un: b.un, base: b.base, rate: b.rate};
      });
      tot.val += agg.val; tot.nr += agg.nr; tot.un += agg.un;
      rate(agg);
      return {id: l.id, name: l.name, val: agg.val, nr: agg.nr, un: agg.un, base: agg.base, rate: agg.rate, dims: dims};
    });
    return {layers: layers, total: rate(tot), n: systems.length};
  }

  function defaultState() { return {view: 'list', q: '', f: {}, cols: DEFAULT_COLS.slice(), sort: {key: 'name', dir: 1}, page: 1, system: null}; }

  function parseHash(hash, d) {
    var st = defaultState();
    var p = new URLSearchParams((hash || '').replace(/^#/, ''));
    if (p.get('system')) { st.view = 'system'; st.system = p.get('system'); }
    st.q = p.get('q') || '';
    p.forEach(function (v, k) {
      if (k.slice(0, 2) !== 'f.') return;
      var key = k.slice(2);
      if (!d.dimByKey[key]) return;
      (st.f[key] = st.f[key] || {})[v] = true;
    });
    if (p.has('cols')) {
      var valid = function (k) { return k && (d.dimByKey[k] || META_COLS.some(function (m) { return m.key === k; })); };
      st.cols = p.get('cols').split(',').filter(valid);
    }
    var s = p.get('sort');
    if (s) { var dir = s[0] === '-' ? -1 : 1, key = s.replace(/^-/, ''); if (key === 'name' || d.dimByKey[key] || /^#/.test(key)) st.sort = {key: key, dir: dir}; }
    var pg = parseInt(p.get('p') || '1', 10);
    st.page = pg > 0 ? pg : 1;
    return normalise(d, st);
  }

  function stateToHash(st) {
    var p = new URLSearchParams();
    if (st.view === 'system' && st.system) { p.set('system', st.system); return p.toString(); }
    if (st.q) p.set('q', st.q);
    Object.keys(st.f).sort().forEach(function (k) {
      Object.keys(st.f[k]).sort().forEach(function (v) { p.append('f.' + k, v); });
    });
    if (st.cols.join(',') !== DEFAULT_COLS.join(',')) p.set('cols', st.cols.join(','));
    if (!(st.sort.key === 'name' && st.sort.dir === 1)) p.set('sort', (st.sort.dir < 0 ? '-' : '') + st.sort.key);
    if (st.page > 1) p.set('p', String(st.page));
    return p.toString();
  }

  function pinUrl(s) {
    if (!s.r || !/^https:\/\/github\.com\//.test(s.r)) return s.r || null;
    return s.sha ? s.r.replace(/\/+$/, '') + '/tree/' + s.sha : s.r;
  }

  function locatorUrl(s, loc) {
    /* "path/to/file.py:12-30@abc1234" -> blob link at that commit, when the system has a GitHub repo */
    if (!s.r || !loc || !/^https:\/\/github\.com\//.test(s.r)) return null;
    var m = /^([A-Za-z0-9_.\-\/]+?\.[A-Za-z0-9]+)(?::(\d+)(?:-(\d+))?)?@([0-9a-f]{7,40})$/.exec(loc.trim());
    if (!m) return null;
    var url = s.r.replace(/\/+$/, '') + '/blob/' + m[4] + '/' + m[1];
    if (m[2]) url += '#L' + m[2] + (m[3] ? '-L' + m[3] : '');
    return url;
  }

  function csvField(x) {
    var t = x == null ? '' : String(x);
    if (/^[=+\-@\t\r]/.test(t) && typeof x !== 'number') t = "'" + t;
    return /[",\r\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t;
  }

  function toCSV(d, systems) {
    var head = ['id', 'name', 'repo', 'pinned_commit', 'repo_at_pinned_commit', 'paper_ids', 'paper_titles', 'cells_not_reported', 'cells_unresolved']
      .concat(d.dims.map(function (x) { return x.key; }));
    var rows = [head.map(csvField).join(',')];
    systems.forEach(function (s) {
      var ps = (s.p || []).map(function (pi) { return d.papers[pi]; });
      var r = [s.i, s.n, s.r || '', s.sha || '', s.sha ? pinUrl(s) : '',
        ps.map(function (p) { return p[0]; }).join(' | '), ps.map(function (p) { return p[1]; }).join(' | '), s.nNr, s.nUn]
        .concat(d.dims.map(function (dim) { return cellText(dim, s.c[dim.idx]); }));
      rows.push(r.map(csvField).join(','));
    });
    return rows.join('\r\n') + '\r\n';
  }

  return {NR: NR, UN: UN, STATE_LABEL: STATE_LABEL, DEFAULT_COLS: DEFAULT_COLS, META_COLS: META_COLS, PAGE: PAGE,
    decode: decode, prepare: prepare, filter: filter, facetCounts: facetCounts, silence: silence,
    parseHash: parseHash, stateToHash: stateToHash, defaultState: defaultState, cellText: cellText,
    pinUrl: pinUrl, locatorUrl: locatorUrl, toCSV: toCSV};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = HDB;
</script>
<script id="hdb-ui">
(function () {
  'use strict';
  if (typeof document === 'undefined') return;
  var D = null, ST = null, lastListHash = '', listScroll = {}, facetRefs = {}, layerOpen = {}, lastView = null;
  var $ = function (id) { return document.getElementById(id); };
  var fmt = function (n) { return n.toLocaleString('en-US'); };
  var pct = function (r) { return r == null ? 'n/a' : (100 * r).toFixed(1) + '%'; };

  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      var v = attrs[k];
      if (v == null || v === false) continue;
      if (k === 'text') el.textContent = v;
      else if (k === 'class') el.className = v;
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (var i = 2; i < arguments.length; i++) add(el, arguments[i]);
    return el;
  }
  function add(el, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { add(el, x); }); return; }
    el.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
  function safeHref(u) { return typeof u === 'string' && /^https?:\/\//.test(u) ? u : null; }

  function stateChip(st, text) {
    if (st === 1) return h('span', {class: 'st st-nr', title: 'not_reported: sources read and silent'}, h('span', {class: 'g', 'aria-hidden': 'true'}, '∅'), 'not reported');
    if (st === 2) return h('span', {class: 'st st-un', title: 'unresolved: the coder could not settle it (excluded from rates)'}, h('span', {class: 'g', 'aria-hidden': 'true'}, '?'), 'unresolved');
    return h('span', {class: 'st st-v'}, text);
  }
  function tokenLabel(t) { return t === HDB.NR ? 'not reported' : t === HDB.UN ? 'unresolved' : t; }
  function tokenChip(t) {
    if (t === HDB.NR) return stateChip(1);
    if (t === HDB.UN) return stateChip(2);
    return h('span', {class: 'opt-t'}, t);
  }
  function valueChips(dim, cell) {
    if (cell[0]) return stateChip(cell[0]);
    var v = cell[1];
    var vals = Array.isArray(v) ? v : [v];
    return h('span', {class: 'chips'}, vals.map(function (x) {
      return stateChip(0, dim.type === 'integer' && dim.key === 'stars' ? fmt(Number(x)) : String(x));
    }));
  }

  /* ------------------------------------------------------------------ navigation */
  function go(st, replace) {
    var hash = HDB.stateToHash(st);
    var url = location.pathname + location.search + (hash ? '#' + hash : '');
    if (replace) {
      try { history.replaceState(null, '', url); } catch (e) { location.hash = hash; return; }
      route();
    } else if ('#' + hash === location.hash || (!hash && !location.hash)) {
      route();
    } else {
      location.hash = hash;
    }
  }
  function mutate(fn, replace) {
    var st = HDB.parseHash(location.hash, D);
    st.view = 'list'; st.system = null;
    fn(st);
    go(st, replace);
  }
  function route() {
    ST = HDB.parseHash(location.hash, D);
    if (ST.view === 'system') renderSystem(); else renderList();
  }

  /* ------------------------------------------------------------------ static structure */
  function buildFilters() {
    var box = clear($('filters'));
    D.layers.forEach(function (layer, li) {
      var det = h('details', {class: 'layer'});
      if (li === 0) det.open = true;
      var cnt = h('span', {class: 'cnt'});
      det.appendChild(h('summary', null, layer.id + ' · ' + layer.name + ' ', cnt));
      layer.cntEl = cnt; layer.detEl = det;
      layer.dims.forEach(function (dim) {
        var fs = h('fieldset', {class: 'dim', id: 'facet-' + dim.key, 'data-key': dim.key});
        fs.appendChild(h('legend', null, h('span', {class: 'id'}, dim.id), dim.name));
        facetRefs[dim.key] = {};
        dim.facetOrder.forEach(function (tok) {
          var input = h('input', {type: 'checkbox', value: tok, 'data-key': dim.key});
          input.addEventListener('change', function () {
            var key = this.getAttribute('data-key'), val = this.value, on = this.checked;
            mutate(function (st) {
              st.f[key] = st.f[key] || {};
              if (on) st.f[key][val] = true; else delete st.f[key][val];
              st.page = 1;
            });
          });
          var c = h('span', {class: 'c'});
          var lab = h('label', {class: 'opt' + (dim.offschema[tok] ? ' offschema' : '')}, input,
            h('span', {class: 't'}, tokenChip(tok)), c);
          facetRefs[dim.key][tok] = {input: input, count: c, label: lab};
          fs.appendChild(lab);
        });
        det.appendChild(fs);
      });
      box.appendChild(det);
    });
    if (window.matchMedia && window.matchMedia('(max-width: 900px)').matches) $('filters-box').open = false;
  }

  function buildColumnMenu() {
    var pop = clear($('colpop'));
    pop.appendChild(h('p', {class: 'small muted', style: 'margin:0 0 8px'}, 'Choose the columns to show. The system name is always shown.'));
    var grid = h('div', {class: 'colgrid'});
    var meta = h('div', {class: 'grp'}, h('b', null, 'Record'));
    HDB.META_COLS.forEach(function (m) { meta.appendChild(colOption(m.key, m.name)); });
    grid.appendChild(meta);
    D.layers.forEach(function (layer) {
      var g = h('div', {class: 'grp'}, h('b', null, layer.id + ' · ' + layer.name));
      layer.dims.forEach(function (dim) { g.appendChild(colOption(dim.key, dim.id + ' ' + dim.name)); });
      grid.appendChild(g);
    });
    pop.appendChild(grid);
    pop.appendChild(h('p', {style: 'margin:8px 0 0'}, h('button', {type: 'button', onclick: function () {
      mutate(function (st) { st.cols = HDB.DEFAULT_COLS.slice(); });
    }}, 'Reset columns')));
  }
  function colOption(key, name) {
    var input = h('input', {type: 'checkbox', value: key, 'data-col': key});
    input.addEventListener('change', function () {
      var k = this.value, on = this.checked;
      mutate(function (st) {
        var i = st.cols.indexOf(k);
        if (on && i < 0) st.cols.push(k);
        if (!on && i >= 0) st.cols.splice(i, 1);
      });
    });
    return h('label', {class: 'opt'}, input, h('span', {class: 't'}, name));
  }

  /* ------------------------------------------------------------------ list view */
  function colName(key) {
    if (key === 'name') return 'System';
    var m = HDB.META_COLS.filter(function (x) { return x.key === key; })[0];
    if (m) return m.name;
    var dim = D.dimByKey[key];
    return dim ? dim.id + ' ' + dim.name : key;
  }

  function renderList() {
    $('system-view').hidden = true; $('list-view').hidden = false;
    lastListHash = location.hash;
    var q = $('q');
    if (document.activeElement !== q) q.value = ST.q;
    var rows = HDB.filter(D, ST);
    renderSilence(rows);
    renderFacets();
    renderActive();
    renderTable(rows);
    $('colpop').querySelectorAll('input[data-col]').forEach(function (i) { i.checked = ST.cols.indexOf(i.value) >= 0; });
    document.title = (ST.q || Object.keys(ST.f).length ? fmt(rows.length) + ' systems · ' : '') + 'HARNESS-DB explorer';
    if (lastView === 'system') {
      window.scrollTo(0, listScroll[location.hash] || 0);
      var back = document.querySelector('a[data-sys="' + (window._lastSys || '') + '"]');
      if (back) back.focus({preventScroll: true});
    }
    lastView = 'list';
  }

  function renderSilence(rows) {
    var sil = HDB.silence(D, rows);
    var filtered = ST.q || Object.keys(ST.f).length;
    $('sil-hero').textContent = pct(sil.total.rate);
    $('sil-scope').textContent = (filtered ? 'Over the ' + fmt(sil.n) + ' systems matching the current filter' : 'Over all ' + fmt(sil.n) + ' systems') +
      ', by layer, least silent first: ' + fmt(sil.total.nr) + ' of ' + fmt(sil.total.base) + ' cells not reported; ' +
      fmt(sil.total.un) + ' unresolved cells excluded. Select a layer for its dimensions.';
    var list = clear($('sil-list'));
    var layers = sil.layers.slice().sort(function (a, b) { return (a.rate == null ? 2 : a.rate) - (b.rate == null ? 2 : b.rate); });
    layers.forEach(function (L) {
      var open = !!layerOpen[L.id];
      var btn = h('button', {type: 'button', class: 'sil-row', 'aria-expanded': open ? 'true' : 'false',
        'aria-controls': 'sil-sub-' + L.id,
        title: L.name + ': ' + fmt(L.nr) + ' not reported, ' + fmt(L.val) + ' coded, ' + fmt(L.un) + ' unresolved (excluded)',
        onclick: function () { layerOpen[L.id] = !layerOpen[L.id]; renderSilence(HDB.filter(D, ST)); var b = document.querySelector('[aria-controls="sil-sub-' + L.id + '"]'); if (b) b.focus(); }},
        h('span', {class: 'lab'}, (open ? '▾ ' : '▸ ') + L.id + ' · ' + L.name),
        bar(L), rateText(L));
      var li = h('li', null, btn);
      if (open) {
        var sub = h('ul', {class: 'sil-sub', id: 'sil-sub-' + L.id});
        L.dims.slice().sort(function (a, b) { return (a.rate || 0) - (b.rate || 0); }).forEach(function (dm) {
          var row = h('div', {class: 'sil-row', title: dm.name + ': ' + fmt(dm.nr) + ' not reported, ' + fmt(dm.val) + ' coded, ' + fmt(dm.un) + ' unresolved (excluded)'},
            h('span', {class: 'lab'}, dm.id + ' ' + dm.name), bar(dm),
            h('span', {class: 'num'}, rateText(dm), ' ',
              dm.nr ? h('button', {type: 'button', class: 'linkbtn showsilent', onclick: function () {
                mutate(function (st) { st.f[dm.key] = {}; st.f[dm.key][HDB.NR] = true; st.page = 1; });
              }}, 'show these') : null));
          sub.appendChild(h('li', null, row));
        });
        li.appendChild(sub);
      }
      list.appendChild(li);
    });
  }
  function bar(b) {
    var filled = b.base ? 100 * b.val / b.base : 0;
    return h('span', {class: 'bar', role: 'img', 'aria-label': pct(b.rate) + ' not reported'}, h('i', {style: 'width:' + filled.toFixed(2) + '%'}));
  }
  function rateText(b) {
    return h('span', {class: 'num'}, h('b', null, pct(b.rate)), ' silent · ' + fmt(b.nr) + '/' + fmt(b.base) + (b.un ? ' · ' + fmt(b.un) + ' unres.' : ''));
  }

  function renderFacets() {
    var active = 0;
    D.layers.forEach(function (layer) {
      var nsel = 0;
      layer.dims.forEach(function (dim) {
        var counts = HDB.facetCounts(D, ST, dim.key), sel = ST.f[dim.key] || {};
        dim.facetOrder.forEach(function (tok) {
          var r = facetRefs[dim.key][tok], n = counts[tok] || 0;
          r.input.checked = !!sel[tok];
          r.count.textContent = fmt(n);
          r.label.classList.toggle('zero', n === 0);
          r.input.setAttribute('aria-label', dim.name + ': ' + tokenLabel(tok) + ', ' + n + ' systems');
          if (sel[tok]) nsel++;
        });
      });
      layer.cntEl.textContent = nsel ? '(' + nsel + ' selected)' : '';
      if (nsel) layer.detEl.open = true;
      active += nsel;
    });
    $('nfilters').textContent = active ? '(' + active + ' active)' : '';
  }

  function renderActive() {
    var ul = clear($('active'));
    var any = false;
    if (ST.q) {
      any = true;
      ul.appendChild(h('li', null, h('button', {type: 'button', 'aria-label': 'Remove search ' + ST.q, onclick: function () {
        $('q').value = ''; mutate(function (st) { st.q = ''; st.page = 1; });
      }}, 'search: “' + ST.q + '” ×')));
    }
    Object.keys(ST.f).forEach(function (key) {
      var dim = D.dimByKey[key];
      Object.keys(ST.f[key]).forEach(function (tok) {
        any = true;
        ul.appendChild(h('li', null, h('button', {type: 'button', 'aria-label': 'Remove filter ' + dim.name + ' ' + tokenLabel(tok), onclick: function () {
          mutate(function (st) { if (st.f[key]) delete st.f[key][tok]; st.page = 1; });
        }}, dim.id + ' ' + dim.name + ': ', tokenChip(tok), ' ×')));
      });
    });
    if (any) ul.appendChild(h('li', null, h('button', {type: 'button', onclick: function () {
      $('q').value = ''; mutate(function (st) { st.q = ''; st.f = {}; st.page = 1; });
    }}, 'Clear all')));
  }

  function renderTable(rows) {
    var cols = ['name'].concat(ST.cols);
    var pages = Math.max(1, Math.ceil(rows.length / HDB.PAGE));
    var page = Math.min(ST.page, pages);
    var start = (page - 1) * HDB.PAGE, slice = rows.slice(start, start + HDB.PAGE);
    $('results-count').textContent = fmt(rows.length) + ' of ' + fmt(D.systems.length) + ' systems' +
      (rows.length > HDB.PAGE ? ' · showing ' + fmt(start + 1) + '–' + fmt(start + slice.length) : '');
    var thead = clear($('tbl').tHead), tbody = clear($('tbl').tBodies[0]);
    var tr = h('tr');
    cols.forEach(function (key) {
      var sorted = ST.sort.key === key;
      tr.appendChild(h('th', {scope: 'col', 'aria-sort': sorted ? (ST.sort.dir > 0 ? 'ascending' : 'descending') : null},
        h('button', {type: 'button', title: 'Sort by ' + colName(key), onclick: function () {
          mutate(function (st) { st.sort = {key: key, dir: st.sort.key === key ? -st.sort.dir : 1}; st.page = 1; });
        }}, colName(key))));
    });
    thead.appendChild(tr);
    if (!rows.length) {
      tbody.appendChild(h('tr', null, h('td', {colspan: String(cols.length), class: 'empty'},
        'No system matches. ', h('button', {type: 'button', class: 'linkbtn', onclick: function () {
          $('q').value = ''; mutate(function (st) { st.q = ''; st.f = {}; st.page = 1; });
        }}, 'Clear the search and filters'), '.')));
    }
    slice.forEach(function (s) {
      var row = h('tr');
      cols.forEach(function (key) {
        if (key === 'name') {
          row.appendChild(h('td', {class: 'name'}, h('a', {href: '#system=' + encodeURIComponent(s.i), 'data-sys': s.i, onkeydown: rowKeys}, s.n),
            s.al && s.al.length ? h('span', {class: 'sub'}, 'also: ' + s.al.filter(function (a) { return a !== s.n; }).slice(0, 2).join('; ')) : null));
        } else if (key === '#silent') row.appendChild(h('td', {class: 'numc'}, fmt(s.nNr) + ' / ' + D.dims.length));
        else if (key === '#unres') row.appendChild(h('td', {class: 'numc'}, fmt(s.nUn)));
        else if (key === '#papers') row.appendChild(h('td', {class: 'numc'}, fmt((s.p || []).length)));
        else if (key === '#repo') {
          var u = safeHref(s.r);
          row.appendChild(h('td', null, u ? h('a', {href: u, rel: 'noopener'}, u.replace(/^https:\/\/github\.com\//, '')) : h('span', {class: 'muted'}, 'none')));
        } else {
          var dim = D.dimByKey[key];
          row.appendChild(h('td', null, valueChips(dim, s.c[dim.idx])));
        }
      });
      tbody.appendChild(row);
    });
    var pager = clear($('pager'));
    if (pages > 1) {
      pager.appendChild(h('button', {type: 'button', disabled: page <= 1, onclick: function () { mutate(function (st) { st.page = page - 1; }); }}, '← Previous'));
      pager.appendChild(h('span', {class: 'small'}, 'Page ' + page + ' of ' + pages));
      pager.appendChild(h('button', {type: 'button', disabled: page >= pages, onclick: function () { mutate(function (st) { st.page = page + 1; }); }}, 'Next →'));
    }
  }
  function rowKeys(ev) {
    if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return;
    var links = Array.prototype.slice.call(document.querySelectorAll('#tbl tbody a[data-sys]'));
    var i = links.indexOf(ev.target) + (ev.key === 'ArrowDown' ? 1 : -1);
    if (i >= 0 && i < links.length) { ev.preventDefault(); links[i].focus(); }
  }

  /* ------------------------------------------------------------------ system view */
  function renderSystem() {
    var s = D.byId[ST.system];
    var view = clear($('system-view'));
    if (lastView === 'list') listScroll[lastListHash] = window.scrollY;
    $('list-view').hidden = true; view.hidden = false;
    var backHref = lastListHash || '#';
    var back = h('a', {href: backHref, id: 'backlink'}, '← Back to results');
    if (!s) {
      view.appendChild(h('div', {class: 'sys-nav'}, back));
      view.appendChild(h('p', null, 'No system with id “' + ST.system + '” in this release.'));
      lastView = 'system';
      return;
    }
    window._lastSys = s.i;
    var listState = HDB.parseHash(lastListHash, D);
    var order = HDB.filter(D, listState), pos = order.indexOf(s);
    var prev = pos > 0 ? order[pos - 1] : null, next = pos >= 0 && pos < order.length - 1 ? order[pos + 1] : null;
    view.appendChild(h('nav', {class: 'sys-nav', 'aria-label': 'System navigation'}, back,
      h('span', {class: 'tools'},
        prev ? h('a', {class: 'btn', href: '#system=' + encodeURIComponent(prev.i), id: 'prevsys', title: prev.n + ' ( [ )'}, '← ' + prev.n) : null,
        pos >= 0 ? h('span', {class: 'small muted'}, fmt(pos + 1) + ' of ' + fmt(order.length)) : h('span', {class: 'small muted'}, 'not in the current filter'),
        next ? h('a', {class: 'btn', href: '#system=' + encodeURIComponent(next.i), id: 'nextsys', title: next.n + ' ( ] )'}, next.n + ' →') : null)));

    var head = h('header', {class: 'sys-head panel'});
    head.style.cssText = 'background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px';
    var title = h('h2', {tabindex: '-1', id: 'sys-title'}, s.n);
    head.appendChild(title);
    var facts = h('dl', {class: 'facts'});
    function fact(k, v) { if (v != null && v !== '') { facts.appendChild(h('dt', null, k)); facts.appendChild(h('dd', null, v)); } }
    fact('Id', h('code', null, s.i));
    if (s.al && s.al.length) fact('Also known as', s.al.join('; '));
    var repo = safeHref(s.r);
    if (repo) {
      var pinned = safeHref(HDB.pinUrl(s));
      fact('Repository', s.sha
        ? [h('a', {href: pinned, rel: 'noopener'}, repo.replace(/^https:\/\/github\.com\//, '') + ' @ ' + s.sha.slice(0, 12)), h('span', {class: 'muted small'}, ' (pinned commit coded from; ', h('a', {href: repo, rel: 'noopener'}, 'current default branch'), ')')]
        : [h('a', {href: repo, rel: 'noopener'}, repo.replace(/^https:\/\/github\.com\//, '')), h('span', {class: 'muted small'}, ' (no pinned commit recorded; link is to the current default branch)')]);
    } else fact('Repository', h('span', {class: 'muted'}, 'none recorded'));
    if (s.pin) fact('Pinned reference', s.pin);
    else if (s.vl) fact('Version', s.vl);
    var papers = (s.p || []).map(function (pi) { return D.papers[pi]; });
    if (papers.length) fact(papers.length > 1 ? 'Sources' : 'Source', h('ul', null, papers.map(function (p) {
      var u = safeHref(p[4]);
      return h('li', null, u ? h('a', {href: u, rel: 'noopener'}, p[1]) : p[1], h('span', {class: 'muted small'}, ' ' + [p[2], p[3]].filter(Boolean).join(', ')));
    })));
    if (s.at) fact('Coded', s.at);
    head.appendChild(facts);
    var strip = h('div', {class: 'strip', role: 'img', 'aria-label': (D.dims.length - s.nNr - s.nUn) + ' coded, ' + s.nNr + ' not reported, ' + s.nUn + ' unresolved'});
    D.layers.forEach(function (layer) {
      var g = h('span', {class: 'grp'}, h('b', null, layer.id));
      layer.dims.forEach(function (dim) {
        var c = s.c[dim.idx];
        g.appendChild(h('span', {class: 'sq ' + ['v', 'nr', 'un'][c[0]], title: dim.id + ' ' + dim.name + ': ' + (c[0] ? HDB.STATE_LABEL[c[0]] : HDB.cellText(dim, c))}));
      });
      strip.appendChild(g);
    });
    head.appendChild(h('p', {class: 'small', style: 'margin:.8rem 0 0'}, h('b', null, fmt(D.dims.length - s.nNr - s.nUn)), ' coded · ',
      h('b', null, fmt(s.nNr)), ' not reported · ', h('b', null, fmt(s.nUn)), ' unresolved, of ' + D.dims.length + ' cells'));
    head.appendChild(strip);
    view.appendChild(head);

    D.layers.forEach(function (layer) {
      var sec = h('section', {class: 'layerblock', 'aria-labelledby': 'lb-' + layer.id});
      var n = layer.dims.filter(function (dim) { return s.c[dim.idx][0] === 1; }).length;
      sec.appendChild(h('h3', {id: 'lb-' + layer.id}, layer.id + ' · ' + layer.name, h('span', {class: 'muted small', style: 'font-weight:400'}, '  ' + n + ' of ' + layer.dims.length + ' not reported')));
      layer.dims.forEach(function (dim) {
        var c = s.c[dim.idx];
        var right = h('div', null, valueChips(dim, c));
        if (c[0] === 0 && c[2] != null) right.appendChild(h('span', {class: 'conf'}, 'confidence: ' + ['low', 'medium', 'high'][c[2]]));
        if (c[3]) right.appendChild(h('blockquote', null, c[3]));
        if (c[4]) {
          var lu = safeHref(HDB.locatorUrl(s, c[4]));
          right.appendChild(h('div', {class: 'loc'}, 'Locator: ', lu ? h('a', {href: lu, rel: 'noopener'}, h('code', null, c[4])) : h('code', null, c[4])));
        } else if (c[0] === 0 && c[3]) right.appendChild(h('div', {class: 'loc muted'}, 'Locator: not separable from the evidence string'));
        if (c[0] === 1 && !c[3]) right.appendChild(h('p', {class: 'note'}, 'The coder read the sources and found nothing on this dimension.'));
        if (c[5]) right.appendChild(h('p', {class: 'note'}, (c[0] === 2 ? 'Why unresolved: ' : 'Coder note: ') + c[5]));
        sec.appendChild(h('div', {class: 'cell', id: 'cell-' + dim.key},
          h('div', {class: 'dn'}, h('span', {class: 'id'}, dim.id), dim.name, h('span', {class: 'k'}, dim.key)), right));
      });
      view.appendChild(sec);
    });
    if (s.nt) view.appendChild(h('p', {class: 'small muted'}, 'Record notes: ' + s.nt));
    document.title = s.n + ' · HARNESS-DB explorer';
    window.scrollTo(0, 0);
    title.focus({preventScroll: true});
    lastView = 'system';
  }

  /* ------------------------------------------------------------------ actions */
  function exportCSV() {
    var rows = HDB.filter(D, HDB.parseHash(location.hash, D));
    var blob = new Blob(['﻿' + HDB.toCSV(D, rows)], {type: 'text/csv;charset=utf-8'});
    var a = h('a', {href: URL.createObjectURL(blob), download: 'harness-db_' + D.meta.version + '_' + rows.length + '-systems.csv'});
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  function copyLink() {
    var btn = $('copylink'), url = location.href;
    var done = function (ok) { btn.textContent = ok ? 'Link copied' : 'Copy failed: use the address bar'; setTimeout(function () { btn.textContent = 'Copy link'; }, 1800); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(function () { done(true); }, function () { done(false); });
    else done(false);
  }

  function wire() {
    var timer = null;
    $('q').addEventListener('input', function () {
      var v = this.value;
      clearTimeout(timer);
      timer = setTimeout(function () { mutate(function (st) { st.q = v.trim(); st.page = 1; }, true); }, 140);
    });
    $('q').addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') { ev.preventDefault(); var r = $('results'); if (ST.view === 'system') mutate(function (st) { st.q = $('q').value.trim(); }); r.focus(); }
    });
    $('home').addEventListener('click', function (ev) { ev.preventDefault(); $('q').value = ''; go(HDB.defaultState()); });
    $('csv').addEventListener('click', exportCSV);
    $('copylink').addEventListener('click', copyLink);
    document.addEventListener('keydown', function (ev) {
      var t = ev.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      if (ev.key === '/' && !typing) { ev.preventDefault(); $('q').focus(); $('q').select(); return; }
      if (ev.key === 'Escape') {
        if (typing && t.id === 'q' && t.value) return;
        var menu = $('colmenu');
        if (menu.open) { menu.open = false; menu.querySelector('summary').focus(); return; }
        if (ST && ST.view === 'system') { ev.preventDefault(); location.hash = lastListHash.replace(/^#/, ''); }
        return;
      }
      if (typing || !ST || ST.view !== 'system') return;
      if (ev.key === '[' && $('prevsys')) { ev.preventDefault(); $('prevsys').click(); }
      if (ev.key === ']' && $('nextsys')) { ev.preventDefault(); $('nextsys').click(); }
    });
    window.addEventListener('hashchange', route);
  }

  async function load() {
    var el = $('hdb-data');
    if (el.getAttribute('data-src')) {
      var r = await fetch(el.getAttribute('data-src'));
      if (!r.ok) throw new Error('could not load ' + el.getAttribute('data-src') + ' (' + r.status + '); serve this folder over http');
      return r.json();
    }
    return HDB.decode(el.textContent);
  }

  load().then(function (raw) {
    D = HDB.prepare(raw);
    buildFilters(); buildColumnMenu(); wire();
    $('loading').hidden = true; $('legend-panel').hidden = false;
    route();
  }).catch(function (err) {
    $('loading').textContent = 'Could not load the dataset: ' + err.message;
  });
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
