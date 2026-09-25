#!/usr/bin/env python
"""PRISMA 2020 flow diagram from ``data/prisma_counts.json`` (plan task S2 / Phase 3 item A9).

Renders the two-column PRISMA 2020 layout (identification via databases and registers on the
left, via other methods on the right; screening; included) with matplotlib only, to SVG and
PDF. ``--check`` validates the arithmetic before rendering:

* the per-source identification counts sum to the identified total;
* identified - duplicates_removed = screened_title_abstract (once screening has started);
* screened - excluded_title_abstract = sought_full_text;
* sought - not_retrieved = assessed_full_text;
* assessed - sum(excluded_full_text) = included_papers;
* included_systems <= included_papers + grey/snowball reports (systems may combine several
  reports; a warning, not an error).

Stages still at 0 are reported as "not started" and their downstream checks are skipped, so
the diagram can be rendered at any point of the review with the boxes that are known.

Usage:
    python scripts/prisma_diagram.py [--counts data/prisma_counts.json] [--out paper/figures/prisma_flow] [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATABASES = ("arxiv", "semantic_scholar", "openalex", "acl_anthology", "openreview", "github")
OTHER = ("grey", "snowball")
LABELS = {
    "arxiv": "arXiv", "semantic_scholar": "Semantic Scholar", "openalex": "OpenAlex", "acl_anthology": "ACL Anthology",
    "openreview": "OpenReview", "github": "GitHub", "grey": "Grey literature (vendor docs, leaderboards)", "snowball": "Citation searching, bibliographies, curated lists",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(c: dict) -> list[str]:
    """Return a list of problems (empty = consistent). Prints the stage status."""
    problems: list[str] = []
    ids = c["identified_by_source"]
    db = sum(ids.get(k, 0) for k in DATABASES)
    other = sum(ids.get(k, 0) for k in OTHER)
    identified = db + other
    unknown = sorted(set(ids) - set(DATABASES) - set(OTHER))
    if unknown:
        problems.append(f"unknown sources in identified_by_source: {unknown}")
    if identified == 0:
        problems.append("identified_by_source is all zero")
    print(f"identified: databases {db:,} + other methods {other:,} = {identified:,}")
    dup = c.get("duplicates_removed", 0)
    after_dedupe = identified - dup
    print(f"duplicates removed: {dup:,} -> {after_dedupe:,} records to screen")
    if after_dedupe < 0:
        problems.append("duplicates_removed exceeds identified")
    scr = c.get("screened_title_abstract", 0)
    if scr == 0:
        print("title/abstract screening: not started (downstream checks skipped)")
        return problems
    if scr != after_dedupe:
        problems.append(f"identified - duplicates = {after_dedupe} but screened_title_abstract = {scr}")
    exc = c.get("excluded_title_abstract", 0)
    sought = c.get("sought_full_text", 0)
    if sought and scr - exc != sought:
        problems.append(f"screened - excluded_ta = {scr - exc} but sought_full_text = {sought}")
    nr = c.get("not_retrieved", 0)
    assessed = c.get("assessed_full_text", 0)
    if assessed and sought - nr != assessed:
        problems.append(f"sought - not_retrieved = {sought - nr} but assessed_full_text = {assessed}")
    exc_ft = sum(c.get("excluded_full_text", {}).values())
    inc_p = c.get("included_papers", 0)
    if inc_p and assessed - exc_ft != inc_p:
        problems.append(f"assessed - excluded_ft = {assessed - exc_ft} but included_papers = {inc_p}")
    inc_s = c.get("included_systems", 0)
    if inc_s and inc_p and inc_s > inc_p:
        print(f"warning: included_systems ({inc_s}) > included_papers ({inc_p}); allowed only if systems come from repo-only records")
    return problems


def render(c: dict, out_stem: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    ids = c["identified_by_source"]
    db = sum(ids.get(k, 0) for k in DATABASES)
    other = sum(ids.get(k, 0) for k in OTHER)
    dup = c.get("duplicates_removed", 0)
    scr = c.get("screened_title_abstract", 0) or (db + other - dup)
    exc_ta = c.get("excluded_title_abstract", 0)
    sought = c.get("sought_full_text", 0)
    nr = c.get("not_retrieved", 0)
    assessed = c.get("assessed_full_text", 0)
    exc_ft = c.get("excluded_full_text", {})
    inc_p = c.get("included_papers", 0)
    inc_s = c.get("included_systems", 0)
    frozen = c.get("search_frozen_on") or "search not frozen"
    pending = " (pending)" if c.get("screened_title_abstract", 0) == 0 else ""

    fig, ax = plt.subplots(figsize=(13, 11))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 11)
    ax.axis("off")
    font = {"family": "DejaVu Sans", "size": 8.5}

    def box(x, y, w, h, text, fc="white", bold_first=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", linewidth=1.0, edgecolor="#333333", facecolor=fc))
        ax.text(x + 0.12, y + h - 0.12, text, va="top", ha="left", fontdict=font, linespacing=1.35, wrap=True)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, linewidth=0.9, color="#333333"))

    def side(x, y, w, h, text):
        box(x, y, w, h, text, fc="#f4f4f4")

    # phase labels
    for label, y, h in (("Identification", 8.55, 2.2), ("Screening", 3.2, 5.1), ("Included", 0.35, 2.55)):
        ax.add_patch(FancyBboxPatch((0.15, y), 0.55, h, boxstyle="round,pad=0.02", linewidth=0.8, edgecolor="#333333", facecolor="#dde6f0"))
        ax.text(0.425, y + h / 2, label, rotation=90, va="center", ha="center", fontdict={"family": "DejaVu Sans", "size": 9, "weight": "bold"})

    # column headers
    ax.text(3.9, 10.85, "Identification of records via databases and registers", ha="center", va="center", fontdict={"family": "DejaVu Sans", "size": 9.5, "weight": "bold"})
    ax.text(10.3, 10.85, "Identification of records via other methods", ha="center", va="center", fontdict={"family": "DejaVu Sans", "size": 9.5, "weight": "bold"})

    db_lines = "\n".join(f"  {LABELS[k]} (n = {ids.get(k, 0):,})" for k in DATABASES)
    box(1.0, 8.6, 3.6, 2.1, f"Records identified from databases\n(n = {db:,}; search frozen {frozen}):\n{db_lines}")
    side(5.0, 8.6, 2.6, 2.1, f"Records removed before screening:\n  duplicates removed by DOI, arXiv id\n  and normalised title (n = {dup:,})")
    arrow(4.6, 9.65, 5.0, 9.65)
    other_lines = "\n".join(f"  {LABELS[k]} (n = {ids.get(k, 0):,})" for k in OTHER)
    box(8.2, 8.6, 4.4, 2.1, f"Records identified from other methods\n(n = {other:,}):\n{other_lines}")

    box(1.0, 6.5, 3.6, 1.1, f"Records screened on title and abstract{pending}\n(n = {scr:,})")
    side(5.0, 6.5, 2.6, 1.1, f"Records excluded\n(n = {exc_ta:,})")
    arrow(2.8, 8.6, 2.8, 7.6)
    arrow(4.6, 7.05, 5.0, 7.05)

    box(1.0, 4.7, 3.6, 1.1, f"Reports sought for retrieval\n(n = {sought:,})")
    side(5.0, 4.7, 2.6, 1.1, f"Reports not retrieved\n(n = {nr:,})")
    arrow(2.8, 6.5, 2.8, 5.8)
    arrow(4.6, 5.25, 5.0, 5.25)

    exc_lines = "\n".join(f"  {k} (n = {v:,})" for k, v in exc_ft.items())
    box(1.0, 3.25, 3.6, 1.1, f"Reports assessed for eligibility\n(n = {assessed:,})")
    side(5.0, 2.55, 2.6, 1.8, f"Reports excluded:\n{exc_lines}")
    arrow(2.8, 4.7, 2.8, 4.35)
    arrow(4.6, 3.8, 5.0, 3.8)

    # other-methods column: sought / assessed are merged into the database column after dedupe
    box(8.2, 6.5, 4.4, 1.1, "Other-method records enter the same deduplicated\nset and are screened with the database records")
    arrow(10.4, 8.6, 10.4, 7.6)
    # elbow: other-methods box -> below the 'excluded' arrow -> right edge of the screened box
    ax.plot([8.2, 7.85, 7.85, 4.85, 4.85], [6.75, 6.75, 6.2, 6.2, 6.7], color="#333333", linewidth=0.9)
    arrow(4.85, 6.7, 4.6, 6.7)

    box(1.0, 0.5, 3.6, 2.0, f"Systems included in the review\n(n = {inc_s:,})\nReports of included systems\n(n = {inc_p:,})")
    arrow(2.8, 3.25, 2.8, 2.5)

    ax.text(6.5, 0.15, "PRISMA 2020 flow diagram (Page et al., 2021).", ha="center", va="center", fontdict={"family": "DejaVu Sans", "size": 7, "style": "italic"})
    fig.tight_layout()
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("svg", "pdf"):
        p = out_stem.with_suffix(f".{ext}")
        fig.savefig(p, format=ext, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--counts", default=str(REPO / "data/prisma_counts.json"))
    p.add_argument("--out", default=str(REPO / "paper/figures/prisma_flow"), help="output stem (writes .svg and .pdf)")
    p.add_argument("--check", action="store_true", help="validate the arithmetic; non-zero exit on inconsistency")
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)
    c = load(Path(args.counts))
    problems = check(c)
    for pr in problems:
        print("PROBLEM:", pr)
    if args.check and problems:
        return 1
    if not args.no_render:
        for path in render(c, Path(args.out)):
            print("wrote", path, path.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
