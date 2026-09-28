#!/usr/bin/env python
"""Framework figures for the v2 manuscript: the study pipeline (Fig. 1), the two named frameworks,
the filed compute-matched ablation, and the RQ3 triangulation.

WHY this script exists
----------------------
The rewrite presents the method as named frameworks with figures (paper-writing skill, sections 2
and 3). A framework figure is the kind of figure that drifts silently: it is drawn once, the data
move, and the boxes keep saying what they said. So every number that appears in these figures is
read from a data file or a reconciliation document AT RENDER TIME, registered on the layout object
together with the file it came from, and checked by ``tests/test_plot_frameworks.py`` against an
independent reading of the same file. The tests also scan every string in every figure for digits
and fail if any number on the page was not registered, so a count typed into a label is a test
failure, not a style choice. The only things this file decides are words and geometry.

The five figures (each written as ``paper/figures/<name>.svg`` and ``.pdf``):

``pipeline_overview``   search -> deduplication -> Two-Tier Escalation Screening -> system grouping
                        -> stratified coding frame -> Evidence-Anchored Coding -> analyses, with
                        the count at every stage. Counts: ``data/prisma_counts.json``,
                        ``data/coding_frame.json``, ``docs/count_reconciliation.md``.
``coding_framework``    Evidence-Anchored Coding: evidence bundle -> stage 1 full read ->
                        mechanical verbatim check -> stage 2 targeted repair, the ordered
                        "absence is not silence" test, the Three-State Cell Contract as three
                        boxes, and the reliability gate. Counts: ``docs/count_reconciliation.md``,
                        ``schema/dimensions.json``.
``screening_framework`` Two-Tier Escalation Screening: the title/abstract votes with the third-vote
                        tiebreak, then the full-text tier-1 reading, escalation rules and decisive
                        tier-2 reading, with how often tier 2 overturned tier 1 on the records
                        read twice. Counts: ``data/screening/fulltext_report.md``,
                        ``data/prisma_counts.json``, ``data/screening/triage.csv``,
                        ``data/screening/fulltext_final_pass1.csv`` + ``fulltext_final_pass2.csv``
                        (the overturn rates are their cross-tab, merged on ``record_id``).
``tier3_design``        the three arms of the filed ablation per instance, the per-instance
                        call match from B to C, and an inset of the arm-A pilot grid against the
                        pre-stated band. Numbers: ``data/tier3/pilot/pilot_summary.json``.
``rq3_triangulation``   the three RQ3 designs on one axis of what each can identify, with their
                        headline estimate and bound direction. Numbers:
                        ``paper/tables/outcomes_summary.json``, ``data/analysis/ablation_*.{csv,json}``,
                        ``data/tier3/pilot/pilot_summary.json``; a fourth "corpus-wide" row is drawn
                        only if ``data/analysis/ablation_pooled_corpus.csv`` exists at render time.
                        That row reads exactly the sources ``scripts/make_rq3_tables.py`` formats
                        into the manuscript's macros: its pooled total (contrasts, papers) from
                        ``ablation_summary_corpus.json`` ``funnel``, and the self-verification
                        estimate from ``ablation_pooled_corpus.csv``. A test checks the printed
                        values against ``paper/tables/rq3_macros.tex``.

Where the specification and the data disagree, the data win and the figure says what the data say:

* the third-vote tiebreak belongs to the TITLE/ABSTRACT stage (``scripts/screen_triage.py`` rule T5).
  At full text the tier-2 reading is decisive where it exists and there is no third vote
  (``scripts/phase3_autopilot.py::merge``), so no tiebreak is drawn after tier 2;
* the verbatim check normalises whitespace and punctuation before matching
  (``scripts/code_system.py``), so it is described as a verbatim match, not a byte-for-byte one.

Units and size. Every figure is laid out in inches at the width it is printed at: ``\\linewidth``
of the acmart ``manuscript`` format used by ``paper/main.tex``, whose ``\\textwidth`` is 430.0 pt
= 5.95 in (``paper/main.log``). Include each at ``width=\\linewidth`` and the scale factor is 1.0,
so the point sizes below are the printed sizes: body text 6.5 pt, notes 5.9 pt, titles 7.4 pt.
Heights follow from the content (at the 2026-09-25 data: pipeline 3.46 in, coding 4.83 in,
screening 4.27 in, tier 3 4.82 in, RQ3 3.02 in, 3.69 in with the corpus-wide row). Nothing depends
on colour: states and bound directions are carried by text, border style (solid / dashed /
dotted) and hatching, and every fill is a grey. Text is measured with the Agg renderer itself and
``check_fit`` refuses a figure in which any line leaves its box; ``main`` exits 1 if one does.

The release counts (1,253 systems, 47,614 cells, the three-state split) are printed from
``docs/count_reconciliation.md`` because that document is the stated authority. ``main`` also
recounts ``data/systems.json`` and prints a WARNING when the two disagree, so a rebuilt release
that the reconciliation has not caught up with is noticed rather than silently drawn.

Usage:
    python scripts/plot_frameworks.py [--only NAME ...] [--out-dir paper/figures] [--no-render]
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from prisma_diagram import DATABASES, OTHER

FIGURES = ("pipeline_overview", "coding_framework", "screening_framework", "tier3_design",
           "rq3_triangulation")

# ---------------------------------------------------------------------------------------- style

WIDTH = 5.95          # \linewidth in the acmart manuscript format, inches
MARGIN = 0.04
FONT = "DejaVu Sans"
SIZE = {"title": 7.4, "body": 6.5, "big": 8.2, "em": 6.5, "note": 5.9, "tag": 5.9, "head": 6.8}
BOLD = {"title", "big", "em", "head"}
ITALIC = {"note", "tag"}
LINE = 1.27           # line height as a multiple of the point size
PADX = 0.06
PADY = 0.045
SWATCH = 0.13         # indent taken by a swatch in front of a key/value row
BAR_H = 0.085

INK = "#222222"
WHITE = "#ffffff"
STRIP = "#e4e4e4"     # title strips: carries no information
PALE = "#f3f3f3"      # group backgrounds
MID = "#8a8a8a"
DARK = "#4d4d4d"

SW_CODED = (DARK, None, "solid")        # swatches: fill, hatch, border style
SW_NR = (WHITE, "////", "dashed")
SW_UN = (MID, None, "dotted")

LS = {"solid": "solid", "dashed": (0, (3.0, 1.6)), "dotted": (0, (1.0, 1.3))}

SHORT_SOURCE = {"arxiv": "arXiv", "semantic_scholar": "Semantic Scholar", "openalex": "OpenAlex",
                "acl_anthology": "ACL Anthology", "openreview": "OpenReview", "github": "GitHub",
                "grey": "grey literature", "snowball": "citation snowball"}


def lh(style: str) -> float:
    """Line height in inches for a text style."""
    return SIZE[style] * LINE / 72.0


_MEASURE: dict = {}


@functools.cache
def tw(s: str, style: str) -> float:
    """Width in inches of ``s`` in a text style, as the Agg renderer lays it out.

    Measured with the renderer itself rather than estimated from glyph outlines, because every box
    width, every wrap and every fit test in this file rests on it: an estimate that is 5% short on
    bold text is what lets a title run over its strip.
    """
    if not s:
        return 0.0
    if "fig" not in _MEASURE:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure

        fig = Figure(figsize=(2, 2), dpi=288)
        FigureCanvasAgg(fig)
        _MEASURE["fig"] = fig
        _MEASURE["renderer"] = fig.canvas.get_renderer()
    fig = _MEASURE["fig"]
    t = fig.text(0, 0, s, fontdict={"family": FONT, "size": SIZE[style],
                                    "weight": "bold" if style in BOLD else "normal",
                                    "style": "italic" if style in ITALIC else "normal"})
    w = t.get_window_extent(_MEASURE["renderer"]).width / fig.dpi
    t.remove()
    return w


def wrap(text: str, max_w: float, style: str) -> list[str]:
    """Greedy word wrap of ``text`` to a measured width in inches."""
    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and tw(trial, style) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def fmt_int(v: float) -> str:
    return f"{round(v):,}"


def fmt_pct(num: float, den: float, nd: int = 1) -> str:
    return f"{100.0 * num / den:.{nd}f}%"


def fmt_signed(v: float, nd: int = 2) -> str:
    return f"{v:+.{nd}f}".replace("-", "−")


def fmt_dec(v: float, nd: int = 3) -> str:
    return f"{v:.{nd}f}".replace("-", "−")


def fmt_weight(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


# ---------------------------------------------------------------------------------------- model
# Coordinates are inches with y measured DOWN from the top edge; the renderer inverts the axis.


@dataclass
class Shape:
    key: str
    kind: str                     # box | strip | diamond | rect | group
    x: float
    y: float                      # top edge
    w: float
    h: float
    fill: str = WHITE
    edge: str | None = INK
    lw: float = 0.8
    ls: str = "solid"
    hatch: str | None = None
    z: float = 2.0
    parent: str | None = None
    rounded: bool = True

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class Label:
    key: str
    x: float
    y: float                      # vertical centre of the line
    text: str
    style: str = "body"
    ha: str = "left"
    rotation: float = 0.0
    z: float = 5.0
    bg: bool = False
    structural: bool = False      # stage numerals, arm letters: not data, exempt from the scan
    bounds: tuple[float, float] | None = None   # horizontal extent the text must stay inside

    @property
    def extent(self) -> tuple[float, float]:
        w = tw(self.text, self.style)
        if self.ha == "left":
            return self.x, self.x + w
        if self.ha == "right":
            return self.x - w, self.x
        return self.x - w / 2, self.x + w / 2


@dataclass
class Link:
    key: str
    points: list[tuple[float, float]]
    arrow: bool = True
    ls: str = "solid"
    lw: float = 0.8
    z: float = 3.0
    color: str = INK


@dataclass
class Mark:
    key: str
    x: float
    y: float
    marker: str = "o"
    size: float = 3.2
    filled: bool = True
    z: float = 6.0


@dataclass
class Number:
    name: str
    value: object
    text: str
    key: str                      # the shape / label group it is printed in
    source: str


@dataclass
class Diagram:
    name: str
    width: float = WIDTH
    height: float = 0.0
    shapes: list[Shape] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    marks: list[Mark] = field(default_factory=list)
    numbers: list[Number] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def num(self, name: str, value: object, text: str, key: str, source: str) -> str:
        """Register a number printed in ``key`` and return its text, so it can be put in a label."""
        self.numbers.append(Number(name, value, text, key, source))
        return text

    def number(self, name: str) -> Number:
        hits = [n for n in self.numbers if n.name == name]
        if not hits:
            raise KeyError(f"{self.name}: no number {name!r}")
        return hits[0]

    def shape(self, key: str) -> Shape:
        for s in self.shapes:
            if s.key == key and s.kind in ("box", "diamond", "group", "rect"):
                return s
        raise KeyError(f"{self.name}: no shape {key!r}")

    def text_of(self, key: str) -> str:
        return " ".join(lb.text for lb in self.labels if lb.key == key)

    @property
    def all_text(self) -> str:
        return " ".join(lb.text for lb in self.labels)


# ------------------------------------------------------------------------------- box builders


@dataclass(frozen=True)
class Item:
    """One row of a box body."""

    text: str = ""
    style: str = "body"
    value: str | None = None                          # right-aligned value (key/value row)
    swatch: tuple[str, str | None, str] | None = None  # (fill, hatch, border style)
    bar: tuple[tuple[float, str, str | None], ...] | None = None  # stacked bar segments
    center: bool = False


def T(text: str, style: str = "body", center: bool = False) -> Item:
    return Item(text=text, style=style, center=center)


def KV(key: str, value: str, style: str = "body",
       swatch: tuple[str, str | None, str] | None = None) -> Item:
    return Item(text=key, value=value, style=style, swatch=swatch)


def BAR(segments: tuple[tuple[float, str, str | None], ...]) -> Item:
    return Item(bar=segments)


def _rows(inner: float, items: tuple[Item, ...] | list[Item]) -> list[Item]:
    """Wrap each body item to the inner width; key/value rows and bars are not wrapped."""
    out: list[Item] = []
    for it in items:
        if it.bar is not None or it.value is not None:
            out.append(it)
            continue
        avail = inner - (SWATCH if it.swatch else 0.0)
        for i, ln in enumerate(wrap(it.text, avail, it.style)):
            out.append(Item(text=ln, style=it.style, swatch=it.swatch if i == 0 else None,
                            center=it.center))
    return out


def _row_h(it: Item) -> float:
    return BAR_H + 0.05 if it.bar is not None else lh(it.style)


def box_height(w: float, title: str, items, strip: bool = True) -> float:
    """Natural height of a box of width ``w`` holding ``title`` and ``items``."""
    inner = w - 2 * PADX
    h = 0.0
    if title:
        tl = wrap(title, inner, "title")
        h += len(tl) * lh("title") + (2 * PADY if strip else PADY)
    rows = _rows(inner, items)
    if rows:
        h += sum(_row_h(r) for r in rows) + 2 * PADY
    return h


def add_box(d: Diagram, key: str, x: float, y: float, w: float, title: str = "", items=(),
            *, h: float | None = None, strip: bool = True, fill: str = WHITE, ls: str = "solid",
            lw: float = 0.8, center_title: bool = False, structural_title: bool = True,
            valign: str = "top", z: float = 2.0, parent: str | None = None,
            structural: bool = False) -> Shape:
    """Place a box with a title strip and a body; returns the box shape.

    Every text row carries the horizontal bounds it must fit in, which the tests measure; a body
    taller than an explicit ``h`` is an error here rather than an overflow on the page.
    """
    items = list(items)
    natural = box_height(w, title, items, strip)
    if h is None:
        h = natural
    elif natural > h + 1e-6:
        raise ValueError(f"{d.name}/{key}: content needs {natural:.3f} in, box is {h:.3f} in")
    shape = Shape(key, "box", x, y, w, h, fill=fill, ls=ls, lw=lw, z=z, parent=parent)
    d.shapes.append(shape)
    inner = w - 2 * PADX
    x0, x1 = x + PADX, x + w - PADX
    cy = y
    if title:
        tl = wrap(title, inner, "title")
        th = len(tl) * lh("title") + (2 * PADY if strip else PADY)
        if strip:
            d.shapes.append(Shape(key, "strip", x, y, w, th, fill=STRIP, edge=None, z=z + 0.1,
                                  parent=key, rounded=False))
        ty = y + (PADY if strip else PADY * 0.8)
        for ln in tl:
            d.labels.append(Label(key, (x + w / 2) if center_title else x0, ty + lh("title") / 2,
                                  ln, "title", ha="center" if center_title else "left",
                                  structural=structural_title, bounds=(x0, x1)))
            ty += lh("title")
        cy = y + th
    rows = _rows(inner, items)
    if not rows:
        return shape
    body_h = sum(_row_h(r) for r in rows)
    ry = cy + PADY
    if valign == "center":
        ry = cy + (y + h - cy - body_h) / 2
    for r in rows:
        rh = _row_h(r)
        mid = ry + rh / 2
        if r.bar is not None:
            bx = x0
            for share, fill_, hatch in r.bar:
                d.shapes.append(Shape(key, "rect", bx, mid - BAR_H / 2, inner * share, BAR_H,
                                      fill=fill_, hatch=hatch, lw=0.5, z=z + 0.3, parent=key,
                                      rounded=False))
                bx += inner * share
            ry += rh
            continue
        tx = x0
        if r.swatch is not None:
            fill_, hatch, sls = r.swatch
            d.shapes.append(Shape(key, "rect", x0, mid - 0.04, 0.09, 0.08, fill=fill_,
                                  hatch=hatch, ls=sls, lw=0.6, z=z + 0.3, parent=key,
                                  rounded=False))
            tx = x0 + SWATCH
        if r.value is not None:
            vw = tw(r.value, r.style)
            d.labels.append(Label(key, x1, mid, r.value, r.style, ha="right",
                                  bounds=(x1 - vw, x1), structural=structural))
            d.labels.append(Label(key, tx, mid, r.text, r.style, bounds=(tx, x1 - vw - 0.05),
                                  structural=structural))
        elif r.center:
            d.labels.append(Label(key, x + w / 2, mid, r.text, r.style, ha="center",
                                  bounds=(x0, x1), structural=structural))
        else:
            d.labels.append(Label(key, tx, mid, r.text, r.style, bounds=(tx, x1),
                                  structural=structural))
        ry += rh
    return shape


def add_diamond(d: Diagram, key: str, cx: float, cy: float, w: float, h: float,
                lines: list[str], style: str = "tag") -> Shape:
    """A decision diamond with centred text; each line's bounds are the diamond's width there."""
    shape = Shape(key, "diamond", cx - w / 2, cy - h / 2, w, h, z=2.5)
    d.shapes.append(shape)
    n = len(lines)
    y = cy - (n - 1) * lh(style) / 2
    for ln in lines:
        dy = abs(y - cy) + lh(style) / 2
        half = max(w / 2 * (1 - 2 * dy / h) - 0.03, 0.0)
        d.labels.append(Label(key, cx, y, ln, style, ha="center", bounds=(cx - half, cx + half)))
        y += lh(style)
    return shape


def add_link(d: Diagram, key: str, pts: list[tuple[float, float]], label: str | None = None,
             at: tuple[float, float] | None = None, *, ha: str = "center", ls: str = "solid",
             arrow: bool = True, style: str = "tag", bg: bool = True, lw: float = 0.8,
             structural: bool = False) -> Link:
    link = Link(key, pts, arrow=arrow, ls=ls, lw=lw)
    d.links.append(link)
    if label:
        lx, ly = at if at is not None else ((pts[0][0] + pts[-1][0]) / 2,
                                            (pts[0][1] + pts[-1][1]) / 2)
        d.labels.append(Label(key, lx, ly, label, style, ha=ha, bg=bg, structural=structural))
    return link


def add_text(d: Diagram, key: str, x: float, y: float, text: str, style: str = "body", *,
             ha: str = "left", rotation: float = 0.0, bounds: tuple[float, float] | None = None,
             structural: bool = False, bg: bool = False) -> Label:
    lb = Label(key, x, y, text, style, ha=ha, rotation=rotation, bounds=bounds,
               structural=structural, bg=bg)
    d.labels.append(lb)
    return lb


TOL = 0.004   # inches: rounding slack for the fit checks


def check_fit(d: Diagram) -> list[str]:
    """Every problem with the geometry of ``d`` (empty = everything fits).

    * each label stays inside the horizontal bounds its box gave it, and inside the page;
    * each shape stays inside the page;
    * no two sibling boxes or diamonds overlap.
    """
    problems = []
    for lb in d.labels:
        a, b = lb.extent
        if lb.rotation == 0 and (a < -TOL or b > d.width + TOL):
            problems.append(f"{d.name}: label {lb.text!r} runs off the page ({a:.3f}-{b:.3f})")
        if lb.bounds is not None and (a < lb.bounds[0] - TOL or b > lb.bounds[1] + TOL):
            problems.append(f"{d.name}/{lb.key}: {lb.text!r} spans {a:.3f}-{b:.3f}, allowed "
                            f"{lb.bounds[0]:.3f}-{lb.bounds[1]:.3f}")
    for s in d.shapes:
        if s.x < -TOL or s.right > d.width + TOL or s.y < -TOL or s.bottom > d.height + TOL:
            problems.append(f"{d.name}/{s.key}: {s.kind} outside the page")
    solid = [s for s in d.shapes if s.kind in ("box", "diamond")]
    for i, s in enumerate(solid):
        for t in solid[i + 1:]:
            if s.parent != t.parent or s.key == t.parent or t.key == s.parent:
                continue
            if (s.x < t.right - TOL and t.x < s.right - TOL and s.y < t.bottom - TOL
                    and t.y < s.bottom - TOL):
                problems.append(f"{d.name}: {s.key} overlaps {t.key}")
    return problems


# --------------------------------------------------------------------------------- data access


@dataclass(frozen=True)
class Paths:
    prisma: Path = REPO / "data/prisma_counts.json"
    frame: Path = REPO / "data/coding_frame.json"
    reconciliation: Path = REPO / "docs/count_reconciliation.md"
    schema: Path = REPO / "schema/dimensions.json"
    fulltext_report: Path = REPO / "data/screening/fulltext_report.md"
    triage: Path = REPO / "data/screening/triage.csv"
    fulltext_final: Path = REPO / "data/screening/fulltext_final_pass1.csv"
    fulltext_second: Path = REPO / "data/screening/fulltext_final_pass2.csv"
    pilot: Path = REPO / "data/tier3/pilot/pilot_summary.json"
    tier3_runs: Path = REPO / "data/tier3/runs.jsonl"
    outcomes: Path = REPO / "paper/tables/outcomes_summary.json"
    credible: Path = REPO / "data/analysis/ablation_credible.csv"
    pooled: Path = REPO / "data/analysis/ablation_pooled.csv"
    ablation_summary: Path = REPO / "data/analysis/ablation_summary.json"
    corpus: Path = REPO / "data/analysis/ablation_pooled_corpus.csv"
    #: the corpus-wide run's summary: its funnel is the pooled total (contrasts, papers) that
    #: ``make_rq3_tables.py`` prints as ``\\rqTotalContrasts`` / ``\\rqTotalPapers``
    corpus_summary: Path = REPO / "data/analysis/ablation_summary_corpus.json"
    systems: Path = REPO / "data/systems.json"


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return p.as_posix()


def _int(s: str) -> int:
    return int(s.replace(",", ""))


def _need(pattern: str, text: str, what: str, flags: int = 0) -> re.Match:
    m = re.search(pattern, text, flags)
    if not m:
        raise ValueError(f"cannot find {what} (pattern {pattern!r}); the document changed shape")
    return m


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def read_csv(p: Path) -> list[dict[str, str]]:
    csv.field_size_limit(10 ** 8)
    with p.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_reconciliation(text: str) -> dict:
    """The released-set, cell-state and reliability counts of ``docs/count_reconciliation.md``.

    The document opens with a dated *superseding* section whenever the release has been rebuilt
    since the base note was written; its table carries a ``current release`` column in bold. When
    that section is present its values win, so a rebuilt release reaches the figures without editing
    the older table below it. Otherwise the base table is read as before.
    """
    out: dict = {}
    m = _need(r"\|\s*sampling frame\s*\|\s*\*\*([\d,]+)\*\*", text, "sampling frame")
    out["sampling_frame"] = _int(m.group(1))
    sup = re.search(r"\*\*Superseding note, (\d{4}-\d{2}-\d{2})\.\*\*", text)
    if sup:
        # | released systems | 1,253 | **1,256** | ... |     | released cells | 47,614 | **47,728** |
        m = _need(r"\|\s*released systems\s*\|[^|\n]*\|\s*\*\*([\d,]+)\*\*", text,
                  "superseding released systems")
        out["released_systems"] = _int(m.group(1))
        m = _need(r"\|\s*released cells\s*\|[^|\n]*\|\s*\*\*([\d,]+)\*\*\s*\|\s*([\d,]+)\s*×\s*(\d+)",
                  text, "superseding released cells")
        out["cells"] = _int(m.group(1))
        out["released_systems_in_product"] = _int(m.group(2))
        out["dimensions"] = int(m.group(3))
        for label, k in (("coded with a value and evidence", "coded"),
                         ("`not_reported`", "not_reported"), ("`unresolved`", "unresolved")):
            # | coded with a value and evidence | 24,160 (50.7%) | **24,228 (50.8%)** |
            m = _need(r"\|\s*" + re.escape(label) + r"\s*\|[^|\n]*\|\s*\*\*([\d,]+)\s*\(([\d.]+)%\)\*\*",
                      text, f"superseding cell state {k}")
            out[f"cells_{k}"] = _int(m.group(1))
            out[f"pct_{k}"] = float(m.group(2))
        out["superseding_date"] = sup.group(1)
    else:
        m = _need(r"\|\s*released\s*\|\s*\*\*([\d,]+)\*\*\s*\|[^|\n]*?([\d,]+)\s*×\s*(\d+)\s*=\s*"
                  r"([\d,]+)\s*cells", text, "released row")
        out["released_systems"] = _int(m.group(1))
        out["released_systems_in_product"] = _int(m.group(2))
        out["dimensions"] = int(m.group(3))
        out["cells"] = _int(m.group(4))
        for label, k in (("coded with a value and evidence", "coded"),
                         ("`not_reported`", "not_reported"), ("`unresolved`", "unresolved")):
            m = _need(r"\|\s*" + re.escape(label) + r"\s*\|\s*([\d,]+)\s*\|\s*\*\*([\d.]+)%\*\*",
                      text, f"cell state {k}")
            out[f"cells_{k}"] = _int(m.group(1))
            out[f"pct_{k}"] = float(m.group(2))
    m = _need(r"\|\s*flagged coded in the frame\s*\|\s*\*\*([\d,]+)\*\*", text, "frame-coded row")
    out["frame_coded"] = _int(m.group(1))
    m = _need(r"\*\*(\d+)\*\*\s+double-coded systems", text, "double-coded systems")
    out["double_coded"] = int(m.group(1))
    m = _need(r"per-dimension Cohen's kappa \*\*([\d.]+)\*\*", text, "mean kappa")
    out["mean_kappa"] = float(m.group(1))
    m = _need(r"\*\*(\d+) of (\d+)\*\* dimensions at or above ([\d.]+)", text, "kappa floor")
    out["dims_passing"] = int(m.group(1))
    out["dims_total_kappa"] = int(m.group(2))
    out["kappa_floor"] = float(m.group(3))
    return out


def parse_fulltext_report(text: str) -> dict:
    """The second-reading sample size, agreement and reference-set recall of the screening report.

    The report's "Pass-1 includes confirmed by pass 2" line is not read: its pass 1 is the decision
    of record, not the first reading, so it counts includes OF RECORD among the escalated set
    (``docs/count_reconciliation.md``, "What 1,403 / 2,073 counts"). The overturn rates come from
    the raw decision files instead (``decided_by_counts``).
    """
    out: dict = {}
    out["read_twice"] = int(_need(r"Records read twice: (\d+)", text, "records read twice")
                            .group(1))
    m = _need(r"Cohen's kappa \(sample as drawn\): ([\d.]+); observed agreement (\d+)/(\d+) = "
              r"([\d.]+)%", text, "kappa as drawn")
    out["kappa"] = float(m.group(1))
    out["agree_n"], out["agree_d"] = int(m.group(2)), int(m.group(3))
    out["agreement_pct"] = float(m.group(4))
    out["reference_n"] = int(_need(r"Positive set: (\d+) known harness systems", text,
                                   "reference set").group(1))
    block = _need(r"Recall by stage:\s*\n(.*?)\n\s*\n", text, "recall block", re.DOTALL).group(1)
    stages = re.findall(r"^- (\w+): (\d+)/(\d+) = ", block, re.MULTILINE)
    if not stages:
        raise ValueError("no recall-by-stage lines in the screening report")
    out["recall_stages"] = [(s, int(a), int(b)) for s, a, b in stages]
    return out


def triage_counts(p: Path) -> dict:
    rows = read_csv(p)
    auto = Counter(r["auto_decision"] for r in rows)
    return {"records": len(rows), "tiebreak": sum(1 for r in rows if r.get("vote_3", "")),
            "auto_include": auto["include"], "auto_exclude": auto["exclude"],
            "no_decision": auto[""]}


def decided_by_counts(final: Path, second: Path) -> dict:
    """Who decided each full-text record, and who read it.

    ``fulltext_final_pass1.csv`` holds the decision of record (``decided_by`` = the tier-2 model
    where it read the record, else tier 1); ``fulltext_final_pass2.csv`` holds the other reading
    where both exist, which is always the tier-1 one. A row whose ``model`` is ``none`` is a record
    with no retrievable text, excluded without any reading. So tier 1 read the records it decided
    plus every real reading in the second file; the rest were read by the tier-2 model alone.

    The same merge (on ``record_id``) gives the overturn rates: of the records read twice, those
    tier 1 excluded (every one escalated) and how many the decision of record turned to include,
    and those tier 1 included (low-confidence or hash-sampled) and how many it turned to exclude.
    """
    rows = read_csv(final)
    ids = {r["record_id"] for r in rows}
    second_rows = [r for r in read_csv(second) if r["record_id"] in ids]
    of_record = {r["record_id"]: r["decision"] for r in rows}
    cross = Counter((r["decision"], of_record[r["record_id"]]) for r in second_rows)
    no_read = sum(1 for r in rows if r["model"] == "none")
    tier2 = sum(1 for r in rows if r["decided_by"] == "opus" and r["model"] != "none")
    tier1 = [r for r in rows if r["decided_by"] == "tier1"]
    tier1_read = len(tier1) + sum(1 for r in second_rows if r["model"] != "none")
    return {"rows": len(rows), "tier2": tier2, "tier1": len(tier1), "no_read": no_read,
            "tier1_includes_stand": sum(1 for r in tier1 if r["decision"] == "include"),
            "tier1_decisions": sorted({r["decision"] for r in tier1}),
            "second_rows": len(second_rows),
            "second_by": sorted({r["decided_by"] for r in second_rows}),
            "tier1_read": tier1_read, "tier2_only": len(rows) - tier1_read - no_read,
            "t1_exclude": cross[("exclude", "include")] + cross[("exclude", "exclude")],
            "t1_exclude_overturned": cross[("exclude", "include")],
            "t1_include": cross[("include", "include")] + cross[("include", "exclude")],
            "t1_include_overturned": cross[("include", "exclude")]}


def pilot_cells(pilot: dict) -> list[dict]:
    """The arm-A pilot grid with a t interval per cell: estimate +/- t(n-1) * sd_between / sqrt(n).

    The interval is the one the protocol notes use for the band decision (0.852 [0.757, 0.948] on
    25 instances), so a cell 'inside the band' on its interval is one whose whole interval is.
    """
    from scipy import stats

    lo, hi = pilot["band"]
    cells = []
    for key, s in pilot["suites"].items():
        n = int(s["n_instances"])
        est = float(s["arm_a_continuous"])
        se = float(s["sd_between_instances"]) / math.sqrt(n)
        t = float(stats.t.ppf(0.975, n - 1))
        cells.append({"key": key, "suite": s["suite"], "model": s["model_requested"], "n": n,
                      "est": est, "ci_low": est - t * se, "ci_high": est + t * se,
                      "in_band_point": bool(s["in_band"]),
                      "in_band_interval": lo <= est - t * se and est + t * se <= hi})
    return cells


def suite_label(suite: str, model: str) -> str:
    name = (suite.replace("bigcodebench", "BCB").replace("_hard", "-Hard")
            .replace("_instruct", "-Instruct").replace("mbppplus", "MBPP+").replace("mbpp", "MBPP"))
    return f"{name} @ {model}"


def corpus_row(p: Path) -> dict | None:
    """The corpus-wide harvest row, if another process has written the file; None otherwise.

    Columns are read by the names ``ablation_pooled.csv`` uses; the self_verification row is taken
    when a ``dimension`` column exists, else the only row. A file with no usable estimate is
    reported and omitted rather than drawn half-empty.
    """
    if not p.exists():
        return None
    rows = read_csv(p)
    if not rows:
        return None
    row = rows[0]
    if "dimension" in rows[0]:
        hits = [r for r in rows if r.get("dimension") == "self_verification"]
        if not hits:
            return None
        row = hits[0]

    def f(*names: str) -> float | None:
        for n in names:
            v = row.get(n, "")
            if v not in ("", None):
                try:
                    x = float(v)
                except ValueError:
                    continue
                if not math.isnan(x):
                    return x
        return None

    out = {"mu": f("mu_rel", "mu", "estimate"), "ci_low": f("ci_low"), "ci_high": f("ci_high"),
           "pi_low": f("pi_low"), "pi_high": f("pi_high"), "n_contrasts": f("n_contrasts"),
           "n_papers": f("n_papers"), "dimension": row.get("dimension", "self_verification")}
    return out if out["mu"] is not None else None


def corpus_total(p: Path) -> tuple[int, int] | None:
    """(contrasts, papers) pooled by the corpus-wide run, from its summary's ``funnel``; None when
    the summary is absent or carries no funnel. ``make_rq3_tables.py`` reads the same two keys."""
    if not p.exists():
        return None
    funnel = read_json(p).get("funnel") or {}
    try:
        return int(funnel["contrasts"]), int(funnel["papers"])
    except (KeyError, TypeError, ValueError):
        return None


def release_drift(paths: Paths, rec: dict) -> dict:
    """Compare the reconciliation's released-set counts with ``data/systems.json`` as it stands.

    The figures print the reconciliation's counts (it is the stated authority); this check is how
    a rebuilt release that the reconciliation has not caught up with gets noticed.
    """
    if not paths.systems.exists():
        return {"checked": False}
    systems = read_json(paths.systems)
    states = Counter()
    for s in systems:
        for cell in s.get("coding", {}).values():
            if cell.get("unresolved"):
                states["unresolved"] += 1
            elif cell.get("not_reported"):
                states["not_reported"] += 1
            elif cell.get("value") is None or cell.get("value") == []:
                states["unresolved"] += 1
            else:
                states["coded"] += 1
    cells = sum(states.values())
    return {"checked": True, "systems": len(systems), "cells": cells, "states": dict(states),
            "matches": len(systems) == rec["released_systems"] and cells == rec["cells"]}


# ------------------------------------------------------------------------ Fig. 1: the pipeline


def layout_pipeline(paths: Paths) -> Diagram:
    """Fig. 1: seven stages in two rows, one per unit of analysis (records, then systems)."""
    d = Diagram("pipeline_overview")
    pc = read_json(paths.prisma)
    fr = read_json(paths.frame)
    rec = parse_reconciliation(paths.reconciliation.read_text(encoding="utf-8"))
    P, F, R = rel(paths.prisma), rel(paths.frame), rel(paths.reconciliation)

    ids = pc["identified_by_source"]
    order = [k for k in DATABASES + OTHER if k in ids]
    identified = sum(ids[k] for k in order)
    exc_ft = sum(pc["excluded_full_text"].values())

    row_label_w = 0.17
    x0 = MARGIN + row_label_w
    avail = WIDTH - MARGIN - x0
    g1, g2 = 0.26, 0.2
    # widths follow content: the source list and the screening ledger need the room
    w_row1 = [0.34, 0.25, 0.41]
    w_row2 = [0.21, 0.265, 0.29, 0.235]
    ws1 = [f * (avail - 2 * g1) for f in w_row1]
    ws2 = [f * (avail - 3 * g2) for f in w_row2]

    k = "search"
    items1 = [T(d.num("identified", identified, f"{fmt_int(identified)} records", k, P), "big")]
    for src in order:
        items1.append(KV(SHORT_SOURCE.get(src, src),
                         d.num(f"source_{src}", ids[src], fmt_int(ids[src]), k, P)))
    items1.append(T("search frozen " + d.num("frozen", pc["search_frozen_on"],
                                             pc["search_frozen_on"], k, P), "note"))

    k = "dedupe"
    items2 = [T(d.num("unique", pc["screened_title_abstract"],
                      f"{fmt_int(pc['screened_title_abstract'])} unique", k, P), "big"),
              KV("duplicates", d.num("duplicates", pc["duplicates_removed"],
                                     fmt_int(pc["duplicates_removed"]), k, P)),
              T("matched on DOI, arXiv id and normalised title", "note")]

    k = "screen"
    items3 = [T("Title and abstract: two votes, tiebreak", "em"),
              KV("screened", d.num("screened_ta", pc["screened_title_abstract"],
                                   fmt_int(pc["screened_title_abstract"]), k, P)),
              KV("forwarded to full text", d.num("sought", pc["sought_full_text"],
                                                 fmt_int(pc["sought_full_text"]), k, P)),
              KV("excluded", d.num("excluded_ta", pc["excluded_title_abstract"],
                                   fmt_int(pc["excluded_title_abstract"]), k, P)),
              T("Full text: tier 1, escalation to tier 2", "em"),
              KV("assessed", d.num("assessed", pc["assessed_full_text"],
                                   fmt_int(pc["assessed_full_text"]), k, P)),
              KV("not retrieved", d.num("not_retrieved", pc["not_retrieved"],
                                        fmt_int(pc["not_retrieved"]), k, P)),
              KV("excluded, with reasons", d.num("excluded_ft", exc_ft, fmt_int(exc_ft), k, P)),
              T(d.num("included_papers", pc["included_papers"],
                      f"{fmt_int(pc['included_papers'])} papers included", k, P), "big")]

    heads1 = ["1  Search", "2  Deduplication", "3  Two-Tier Escalation Screening"]
    all1 = (items1, items2, items3)
    h_row1 = max(box_height(w, t, it) for w, t, it in zip(ws1, heads1, all1, strict=True))
    y1 = MARGIN
    xs1 = [x0 + sum(ws1[:i]) + i * g1 for i in range(3)]
    for key, x, w, t, it in zip(("search", "dedupe", "screen"), xs1, ws1, heads1, all1,
                                strict=True):
        add_box(d, key, x, y1, w, t, it, h=h_row1)

    # row 2: systems
    k = "group"
    items4 = [T(d.num("systems", pc["included_systems"],
                      f"{fmt_int(pc['included_systems'])} systems", k, P), "big"),
              T("from the " + d.num("included_papers_g", pc["included_papers"],
                                    fmt_int(pc["included_papers"]), k, P) + " included papers"),
              T("merged on a shared repository, or on equal names where a repository is "
                "missing; the census is the sampling frame", "note")]

    k = "frame"
    st = fr["strata"]
    items5 = [T(d.num("coded_total", fr["coded_total"],
                      f"{fmt_int(fr['coded_total'])} drawn", k, F), "big")]
    for s in ("H", "P", "O"):
        items5.append(KV(f"{s}  " + d.num(f"stratum_{s}_coded", st[s]["coded"],
                                           fmt_int(st[s]["coded"]), k, F) + " of "
                         + d.num(f"stratum_{s}_size", st[s]["size"], fmt_int(st[s]["size"]), k,
                                 F),
                         "w " + d.num(f"stratum_{s}_weight", st[s]["weight"],
                                      fmt_weight(st[s]["weight"]), k, F)))
    items5.append(T("H: ≥ " + d.num("h_min_stars", fr["h_min_stars"],
                                          fmt_int(fr["h_min_stars"]), k, F)
                    + " stars, catalogued or vendor, coded in full; P peer-reviewed and O the "
                    "rest, sampled; w = inverse inclusion probability", "note"))

    k = "coding"
    cells = rec["cells"]
    items6 = [T(d.num("cells", cells, f"{fmt_int(cells)} cells", k, R), "big"),
              T(d.num("released", rec["released_systems"], fmt_int(rec["released_systems"]), k, R)
                + " systems × " + d.num("dimensions", rec["dimensions"],
                                             str(rec["dimensions"]), k, R) + " dimensions"),
              BAR(((rec["cells_coded"] / cells, DARK, None),
                   (rec["cells_not_reported"] / cells, WHITE, "////"),
                   (rec["cells_unresolved"] / cells, MID, None))),
              KV("value + evidence", d.num("pct_coded", rec["pct_coded"],
                                           f"{rec['pct_coded']:.1f}%", k, R), swatch=SW_CODED),
              KV("not_reported", d.num("pct_not_reported", rec["pct_not_reported"],
                                       f"{rec['pct_not_reported']:.1f}%", k, R), swatch=SW_NR),
              KV("unresolved", d.num("pct_unresolved", rec["pct_unresolved"],
                                     f"{rec['pct_unresolved']:.1f}%", k, R), swatch=SW_UN),
              T("gate passed: " + d.num("dims_passing", rec["dims_passing"],
                                        str(rec["dims_passing"]), k, R) + " of "
                + d.num("dims_total_kappa", rec["dims_total_kappa"],
                        str(rec["dims_total_kappa"]), k, R)
                + " dimensions at κ ≥ " + d.num("kappa_floor", rec["kappa_floor"],
                                                          f"{rec['kappa_floor']:g}", k, R)
                + ", " + d.num("double_coded", rec["double_coded"], str(rec["double_coded"]),
                               k, R) + " systems coded twice", "note")]

    k = "analyses"
    items7 = [T("RQ1  taxonomy and its reliability"),
              T("RQ2  variation and convergence"),
              T("RQ3  design against outcomes, three designs"),
              T("RQ4  under-reporting"),
              T("field estimates weighted to the frame; the coded set unweighted", "note")]

    heads2 = ["4  System grouping", "5  Stratified coding frame", "6  Evidence-Anchored Coding",
              "7  Analyses"]
    all2 = (items4, items5, items6, items7)
    h_row2 = max(box_height(w, t, it) for w, t, it in zip(ws2, heads2, all2, strict=True))
    channel = 0.3
    y2 = y1 + h_row1 + channel
    xs2 = [x0 + sum(ws2[:i]) + i * g2 for i in range(4)]
    for key, x, w, t, it in zip(("group", "frame", "coding", "analyses"), xs2, ws2, heads2, all2,
                                strict=True):
        add_box(d, key, x, y2, w, t, it, h=h_row2, structural=(key == "analyses"))

    ya = y1 + 0.2
    for i in range(2):
        add_link(d, "flow", [(xs1[i] + ws1[i] + 0.02, ya), (xs1[i + 1] - 0.02, ya)])
    yb = y2 + 0.2
    for i in range(3):
        add_link(d, "flow", [(xs2[i] + ws2[i] + 0.02, yb), (xs2[i + 1] - 0.02, yb)])
    # screening -> grouping: down out of box 3, along the channel, into box 4
    sx = xs1[2] + ws1[2] / 2
    ymid = y1 + h_row1 + channel / 2
    gx = xs2[0] + ws2[0] / 2
    add_link(d, "handover", [(sx, y1 + h_row1 + 0.01), (sx, ymid), (gx, ymid),
                             (gx, y2 - 0.01)],
             "the unit changes: included papers are grouped into systems",
             at=((sx + gx) / 2, ymid))

    for y, h, text in ((y1, h_row1, "unit: records"), (y2, h_row2, "unit: systems")):
        add_text(d, "rowlabel", MARGIN + 0.07, y + h / 2, text, "tag", ha="center", rotation=90)

    d.height = y2 + h_row2 + MARGIN
    d.meta["reconciliation"] = rec
    return d

# ------------------------------------------------------- Fig. 2: Evidence-Anchored Coding framework


def layout_coding(paths: Paths) -> Diagram:
    """Fig. 2: the four modules, the ordered absence test, the three states and the gate.

    Each state box sits directly under the module that sends cells to it (the absence test sends
    not_reported, the verbatim check sends value + evidence, stage 2 sends unresolved), so no flow
    crosses another; that is why the states read not_reported | value + evidence | unresolved.
    """
    d = Diagram("coding_framework")
    rec = parse_reconciliation(paths.reconciliation.read_text(encoding="utf-8"))
    schema = read_json(paths.schema)
    R, S = rel(paths.reconciliation), rel(paths.schema)
    n_dim = len(schema["dimensions"])

    xs = [MARGIN, 1.42, 2.94, 4.60]
    ws = [1.16, 1.30, 1.24, WIDTH - MARGIN - 4.60]
    y0 = MARGIN
    heads = ["Evidence bundle", "Stage 1  Full read", "Mechanical verbatim check",
             "Stage 2  Targeted repair"]
    items = [
        [T("the papers' full texts (references removed), the repository at a pinned commit, "
           "and official documentation"),
         T("the exact text sent is kept for re-checking", "note")],
        [T("one reading fills all " + d.num("dims_s1", n_dim, str(n_dim), "stage1", S)
           + " cells, each with a value, a verbatim quote and a locator (file:line@commit or "
           "paper section)"),
         T("no feature found: the ordered test below decides", "note")],
        [T("each quote is matched verbatim against the bundle text that was sent"),
         T("whitespace and punctuation normalised; a paraphrase is flagged, never rewritten",
           "note")],
        [T("re-reads only the cells that failed or were left unresolved, on keyword windows "
           "rather than the whole bundle"),
         T("the first attempt is kept as history", "note")],
    ]
    keys = ["bundle", "stage1", "check", "stage2"]
    h_a = max(box_height(w, t, it) for w, t, it in zip(ws, heads, items, strict=True))
    for k, x, w, t, it in zip(keys, xs, ws, heads, items, strict=True):
        add_box(d, k, x, y0, w, t, it, h=h_a)
    b, s1, ck, s2 = (d.shape(k) for k in keys)
    ya = y0 + 0.2
    add_link(d, "flow", [(b.right + 0.02, ya), (s1.x - 0.02, ya)])
    add_link(d, "flow", [(s1.right + 0.02, ya), (ck.x - 0.02, ya)])
    add_link(d, "flow", [(ck.right + 0.02, ya), (s2.x - 0.02, ya)], "fail",
             at=((ck.right + s2.x) / 2, ya - 0.075))
    yr = y0 + h_a - 0.16
    add_link(d, "flow", [(s2.x - 0.02, yr), (ck.right + 0.02, yr)], "re-check",
             at=((ck.right + s2.x) / 2, yr - 0.075))

    # the three state boxes first: their x positions fix where the flows land
    gx0, gx1 = MARGIN, WIDTH - MARGIN
    sgap = 0.12
    ix0, ix1 = gx0 + 0.08, gx1 - 0.08
    span = ix1 - ix0 - 2 * sgap
    sws = [0.30 * span, 0.40 * span, 0.30 * span]
    sxs = [ix0, ix0 + sws[0] + sgap, ix0 + sws[0] + sws[1] + 2 * sgap]

    # the ordered absence test, centred over the not_reported box
    dia_w, dia_h = 1.98, 0.8
    dcx = max(sxs[0] + sws[0] / 2, MARGIN + dia_w / 2 + 0.02)
    dia_top = s1.bottom + 0.3
    dcy = dia_top + dia_h / 2
    dia = add_diamond(d, "absence", dcx, dcy, dia_w, dia_h,
                      ["Absence is not silence:", "is the place it would be",
                       "declared in the evidence?"])
    fx = s1.x + 0.16
    ymid = s1.bottom + 0.15
    add_link(d, "flow", [(fx, s1.bottom + 0.01), (fx, ymid), (dcx, ymid), (dcx, dia.y - 0.01)])
    add_text(d, "flow", fx + 0.05, s1.bottom + 0.075, "feature not found", "tag")

    cells = rec["cells"]
    state_items = [
        [T("not_reported", "em", center=True),
         T("sources read, and silent", center=True),
         T("a finding: counted as under-reporting", "note", center=True),
         T(d.num("cells_not_reported", rec["cells_not_reported"],
                 fmt_int(rec["cells_not_reported"]), "s_nr", R) + " cells, "
           + d.num("pct_not_reported", rec["pct_not_reported"],
                   f"{rec['pct_not_reported']:.1f}%", "s_nr", R), center=True)],
        [T("value + evidence", "em", center=True),
         T("a schema value with its quote and locator", center=True),
         T("an absence value cites the place it would be declared", "note", center=True),
         T(d.num("cells_coded", rec["cells_coded"], fmt_int(rec["cells_coded"]), "s_val", R)
           + " cells, " + d.num("pct_coded", rec["pct_coded"], f"{rec['pct_coded']:.1f}%",
                                "s_val", R), center=True)],
        [T("unresolved", "em", center=True),
         T("the coder could not settle it", center=True),
         T("an admission: excluded from every rate", "note", center=True),
         T(d.num("cells_unresolved", rec["cells_unresolved"],
                 fmt_int(rec["cells_unresolved"]), "s_un", R) + " cells, "
           + d.num("pct_unresolved", rec["pct_unresolved"],
                   f"{rec['pct_unresolved']:.1f}%", "s_un", R), center=True)],
    ]
    skeys = ["s_nr", "s_val", "s_un"]
    sstyle = [("dashed", WHITE, 0.9), ("solid", WHITE, 1.3), ("dotted", PALE, 1.0)]
    h_s = max(box_height(w, "", it) for w, it in zip(sws, state_items, strict=True))
    title = ("Three-State Cell Contract: every one of the " + d.num(
        "cells_total", cells, fmt_int(cells), "contract", R) + " released cells is in exactly "
             "one state")
    tl = wrap(title, gx1 - gx0 - 2 * PADX, "title")
    th = len(tl) * lh("title") + 2 * PADY
    gy = dia.bottom + 0.2
    gh = 0.08 + h_s + 0.06 + th
    grp = Shape("contract", "box", gx0, gy, gx1 - gx0, gh, fill=PALE, z=1.0)
    d.shapes.append(grp)
    d.shapes.append(Shape("contract", "strip", gx0 + 0.01, gy + gh - th, gx1 - gx0 - 0.02,
                          th - 0.012, fill=STRIP, edge=None, z=1.1, parent="contract",
                          rounded=False, ls="top-rule"))
    for j, ln in enumerate(tl):
        d.labels.append(Label("contract", (gx0 + gx1) / 2,
                              gy + gh - th + PADY + (j + 0.5) * lh("title"), ln, "title",
                              ha="center", bounds=(gx0 + PADX, gx1 - PADX)))
    for k, x, w, it, (ls_, fill_, lw_) in zip(skeys, sxs, sws, state_items, sstyle, strict=True):
        add_box(d, k, x, gy + 0.08, w, "", it, h=h_s, ls=ls_, fill=fill_, lw=lw_, z=2.0,
                parent="contract")
    snr, sval, sun = (d.shape(k) for k in skeys)

    # flows into the contract
    add_link(d, "flow", [(dcx, dia.bottom + 0.01), (dcx, snr.y - 0.01)])
    yes_x = sval.x + 0.3
    add_text(d, "flow", dcx + 0.05, dia.bottom + 0.1, "no: not_reported", "tag",
             bounds=(dcx, yes_x - 0.03))
    add_link(d, "flow", [(dia.right - 0.01, dcy), (yes_x, dcy), (yes_x, sval.y - 0.01)])
    px = ck.right - 0.22
    add_text(d, "flow", yes_x + 0.05, dcy + 0.07, "yes: an absence value", "tag",
             bounds=(yes_x, px - 0.03))
    add_text(d, "flow", yes_x + 0.05, dcy + 0.07 + lh("tag"), "(none, open, unbounded, ...)",
             "tag", bounds=(yes_x, px - 0.03))
    add_link(d, "flow", [(px, ck.bottom + 0.01), (px, sval.y - 0.01)])
    add_text(d, "flow", px + 0.05, ck.bottom + 0.075, "pass", "tag")
    add_link(d, "flow", [(sun.cx, s2.bottom + 0.01), (sun.cx, sun.y - 0.01)])
    add_text(d, "flow", sun.cx + 0.05, s2.bottom + 0.075, "still failing", "tag")

    # the reliability gate
    ry = gy + gh + 0.22
    gate_title = "Reliability gate: the schema is frozen only after it is passed"
    steps = [
        [T("an independent second coding of " + d.num("double_coded", rec["double_coded"],
                                                        str(rec["double_coded"]), "gate", R)
           + " systems, never merged with the first", center=True)],
        [T("per-dimension Cohen's κ ≥ " + d.num("kappa_floor", rec["kappa_floor"],
                                                          f"{rec['kappa_floor']:g}", "gate", R)
           + " on the point estimate", center=True),
         T(d.num("dims_passing", rec["dims_passing"], str(rec["dims_passing"]), "gate", R)
           + " of " + d.num("dims_total_kappa", rec["dims_total_kappa"],
                            str(rec["dims_total_kappa"]), "gate", R) + " dimensions pass; mean "
           "κ " + d.num("mean_kappa", rec["mean_kappa"], f"{rec['mean_kappa']:.3f}", "gate",
                             R), "note", center=True)],
        [T("schema and coding manual frozen; any later change is a logged amendment",
           center=True)],
    ]
    gtw = gx1 - gx0
    gth = box_height(gtw, gate_title, [])
    arrow_gap = 0.3
    stw = (gtw - 0.16 - 2 * arrow_gap) / 3
    h_st = max(box_height(stw, "", it) for it in steps)
    add_box(d, "gate", gx0, ry, gtw, gate_title, [], h=gth + 0.08 + h_st + 0.08, fill=PALE,
            z=1.0, structural_title=False)
    stx = [gx0 + 0.08 + i * (stw + arrow_gap) for i in range(3)]
    for i, (x, it) in enumerate(zip(stx, steps, strict=True)):
        add_box(d, f"gate{i}", x, ry + gth + 0.08, stw, "", it, h=h_st, parent="gate")
    yy = ry + gth + 0.08 + h_st / 2
    for i in range(2):
        add_link(d, "flow", [(stx[i] + stw + 0.02, yy), (stx[i + 1] - 0.02, yy)])
    add_link(d, "flow", [(sval.cx, gy + gh + 0.01), (sval.cx, ry - 0.01)],
             "a sample of systems is coded twice", at=(sval.cx + 0.06, (gy + gh + ry) / 2),
             ha="left")
    for lb in d.labels:
        if lb.key in ("gate0", "gate1", "gate2"):
            lb.key = "gate"   # the gate's numbers are registered on the band as a whole
    d.height = ry + gth + 0.08 + h_st + 0.08 + MARGIN
    return d

# ---------------------------------------------------- Fig. 3: Two-Tier Escalation Screening


def layout_screening(paths: Paths) -> Diagram:
    """Fig. 3: the title/abstract votes, then the full-text two-tier escalation, then what it changed.

    The third-vote tiebreak is drawn in the title/abstract row because that is where it runs: at
    full text the tier-2 reading is decisive wherever it exists and there is no third vote.
    """
    d = Diagram("screening_framework")
    pc = read_json(paths.prisma)
    rep = parse_fulltext_report(paths.fulltext_report.read_text(encoding="utf-8"))
    tri = triage_counts(paths.triage)
    dec = decided_by_counts(paths.fulltext_final, paths.fulltext_second)
    P, Q, TR, FF = (rel(paths.prisma), rel(paths.fulltext_report), rel(paths.triage),
                    rel(paths.fulltext_final))
    F2 = rel(paths.fulltext_second)
    inc, exc = pc["included_papers"], sum(pc["excluded_full_text"].values())

    row_label_w = 0.17
    x0 = MARGIN + row_label_w
    g = 0.24
    w = (WIDTH - MARGIN - x0 - 3 * g) / 4
    xs = [x0 + i * (w + g) for i in range(4)]

    by_rule = pc["sought_full_text"] - tri["auto_include"] - tri["no_decision"]
    ta = [
        ("Two independent votes", [
            T("two models vote on every record"),
            T(d.num("ta_records", tri["records"], fmt_int(tri["records"]), "ta1", TR)
              + " records", "big"),
            T("agreeing votes, or a fixed rule on their stated reasons, decide", "note")]),
        ("Third-vote tiebreak", [
            T("no two-vote decision: a third, decisive vote"),
            T(d.num("tiebreak", tri["tiebreak"], fmt_int(tri["tiebreak"]), "ta2", TR)
              + " records", "big"),
            T("two of three agreeing votes decide", "note")]),
        ("Inclusive default", [
            T("no two-of-three decision: forwarded, never excluded"),
            T(d.num("no_decision", tri["no_decision"], fmt_int(tri["no_decision"]), "ta3", TR)
              + " records", "big"),
            T("a missed harness costs more than one extra reading", "note")]),
        ("Title/abstract outcome", [
            KV("voted include", d.num("auto_include", tri["auto_include"],
                                      fmt_int(tri["auto_include"]), "ta4", TR)),
            KV("undecided", d.num("no_decision_4", tri["no_decision"],
                                  fmt_int(tri["no_decision"]), "ta4", TR)),
            KV("forwarded by rule", d.num("by_rule", by_rule, fmt_int(by_rule), "ta4", P)),
            KV("to full text", d.num("sought", pc["sought_full_text"],
                                     fmt_int(pc["sought_full_text"]), "ta4", P), "em"),
            KV("excluded", d.num("excluded_ta", pc["excluded_title_abstract"],
                                 fmt_int(pc["excluded_title_abstract"]), "ta4", P))]),
    ]
    y1 = MARGIN
    h1 = max(box_height(w, t, it) for t, it in ta)
    for i, (x, (t, it)) in enumerate(zip(xs, ta, strict=True)):
        add_box(d, f"ta{i + 1}", x, y1, w, t, it, h=h1, structural_title=False)
    ya = y1 + 0.2
    for i in range(3):
        add_link(d, "flow", [(xs[i] + w + 0.02, ya), (xs[i + 1] - 0.02, ya)])

    ft = [
        ("Tier-1 reader", [
            T("reads the retrieved record: a verbatim quote per decision step, and a stated "
              "confidence"),
            T(d.num("tier1_read", dec["tier1_read"], fmt_int(dec["tier1_read"]), "ft1", FF)
              + " read", "big"),
            T("of the " + d.num("assessed", pc["assessed_full_text"],
                                fmt_int(pc["assessed_full_text"]), "ft1", P) + " assessed, "
              + d.num("tier2_only", dec["tier2_only"], fmt_int(dec["tier2_only"]), "ft1", FF)
              + " were read at tier 2 only", "note")]),
        ("Escalation rules", [
            T("→ tier 2: every tier-1 exclude"),
            T("→ tier 2: every low-confidence decision"),
            T("→ tier 2: a hash-selected audit of the other includes"),
            T("otherwise the tier-1 include stands", "note")]),
        ("Tier-2 reader, decisive", [
            T("a stronger model reads the record independently; its vote is the decision of "
              "record"),
            T(d.num("tier2_decided", dec["tier2"], fmt_int(dec["tier2"]), "ft3", FF)
              + " decided", "big"),
            T("no third vote at this stage", "note")]),
        ("Full-text outcome", [
            KV("included", d.num("included", inc, fmt_int(inc), "ft4", P), "em"),
            KV("excluded", d.num("excluded_ft", exc, fmt_int(exc), "ft4", P)),
            KV("decided at tier 2", d.num("tier2_decided_4", dec["tier2"],
                                          fmt_int(dec["tier2"]), "ft4", FF)),
            KV("stands at tier 1", d.num("tier1_stands", dec["tier1_includes_stand"],
                                         fmt_int(dec["tier1_includes_stand"]), "ft4", FF)),
            KV("no text, no reading", d.num("no_read", dec["no_read"], fmt_int(dec["no_read"]),
                                            "ft4", FF))]
         + ([T("tier 1 alone never excludes", "note")] if dec["tier1_decisions"] == ["include"]
            else [])),
    ]
    channel = 0.34
    y2 = y1 + h1 + channel
    h2 = max(box_height(w, t, it) for t, it in ft)
    for i, (x, (t, it)) in enumerate(zip(xs, ft, strict=True)):
        add_box(d, f"ft{i + 1}", x, y2, w, t, it, h=h2, structural_title=False)
    yb = y2 + 0.2
    for i in range(3):
        add_link(d, "flow", [(xs[i] + w + 0.02, yb), (xs[i + 1] - 0.02, yb)])
    # not-escalated tier-1 includes bypass tier 2
    yby = y2 + h2 + 0.12
    add_link(d, "flow", [(xs[1] + w / 2, y2 + h2 + 0.01), (xs[1] + w / 2, yby),
                         (xs[3] + w / 2, yby), (xs[3] + w / 2, y2 + h2 + 0.01)],
             "not escalated: the tier-1 include stands",
             at=((xs[1] + xs[3] + w) / 2, yby))
    # title stage -> full text
    sx = xs[3] + w / 2
    ym = y1 + h1 + channel / 2
    fx = xs[0] + w / 2
    add_link(d, "handover", [(sx, y1 + h1 + 0.01), (sx, ym), (fx, ym), (fx, y2 - 0.01)],
             d.num("assessed_h", pc["assessed_full_text"], fmt_int(pc["assessed_full_text"]),
                   "handover", P) + " assessed; "
             + d.num("not_retrieved", pc["not_retrieved"], fmt_int(pc["not_retrieved"]),
                     "handover", P) + " sought but never retrieved",
             at=((sx + fx) / 2, ym))

    # what the escalation changed: how often the decisive tier-2 reading overturned tier 1
    cy = yby + 0.2
    read_twice = rep["read_twice"]
    overturn_rows = (
        ("exclude", "tier-1 excludes (every one escalated) overturned to include"),
        ("include", "tier-1 includes (low-confidence or sampled) overturned to exclude"),
    )
    cov_items = [
        KV(label, d.num(f"{p}_overturned", dec[f"t1_{p}_overturned"],
                        fmt_int(dec[f"t1_{p}_overturned"]), "coverage", FF) + " of "
           + d.num(f"{p}_escalated", dec[f"t1_{p}"], fmt_int(dec[f"t1_{p}"]), "coverage", FF)
           + "  (" + d.num(f"{p}_overturn_rate", dec[f"t1_{p}_overturned"] / dec[f"t1_{p}"],
                           fmt_pct(dec[f"t1_{p}_overturned"], dec[f"t1_{p}"]), "coverage", FF)
           + ")")
        for p, label in overturn_rows
    ] + [
        KV("agreement of the two readings on those records", "κ = " + d.num(
            "kappa", rep["kappa"], f"{rep['kappa']:.3f}", "coverage", Q) + ",  "
           + d.num("agreement", rep["agreement_pct"], f"{rep['agreement_pct']:.1f}%",
                   "coverage", Q) + " of " + d.num("read_twice", read_twice,
                                                   fmt_int(read_twice), "coverage", Q)),
    ]
    stages = rep["recall_stages"]
    lo = min(a for _, a, _ in stages)
    ref_n = rep["reference_n"]
    all_same = all(a == lo and b == ref_n for _, a, b in stages)
    ref_text = (d.num("ref_found", lo, str(lo), "coverage", Q) + " of "
                + d.num("ref_n", ref_n, str(ref_n), "coverage", Q)
                + (" at every stage, search to coding frame" if all_same else
                   " at the weakest stage"))
    cov_items.append(KV("known harnesses in the reference set kept", ref_text))
    cov_items.append(T("Escalation fires on an exclude or on low confidence, so the records "
                       "read twice are a non-random sample tilted towards excludes and hard "
                       "cases, and κ describes that sample, not the corpus. The sampled includes "
                       "hold every low-confidence one, so their overturn rate bounds the "
                       "false-include rate of the unescalated includes from above.", "note"))
    cw = WIDTH - MARGIN - x0
    add_box(d, "coverage", x0, cy, cw, "What the escalation changed", cov_items,
            ls="dashed", fill=PALE, structural_title=False)
    for y, h, text in ((y1, h1, "title / abstract"), (y2, h2, "full text")):
        add_text(d, "rowlabel", MARGIN + 0.07, y + h / 2, text, "tag", ha="center", rotation=90)
    d.meta["decided_by"] = dec
    d.meta["second_source"] = F2
    d.height = cy + d.shape("coverage").h + MARGIN
    return d

# ---------------------------------------------------- Fig. 4: the filed ablation design


def layout_tier3(paths: Paths) -> Diagram:
    """Fig. 4: the three arms on one instance, the per-instance call match, and the pilot inset."""
    d = Diagram("tier3_design")
    pilot = read_json(paths.pilot)
    PI = rel(paths.pilot)
    lo, hi = pilot["band"]

    top = MARGIN + 0.02
    inst_w = 0.74
    lane_x = MARGIN + inst_w + 0.2
    bx = lane_x + 0.66
    score_x = 4.8
    content_r = score_x - 0.2
    ci = "cᵢ"

    def lane_label(arm: str, y: float, sub: str) -> None:
        add_text(d, f"lane{arm}", lane_x, y, f"Arm {arm}", "head", structural=True)
        add_text(d, f"lane{arm}", lane_x, y + lh("head"), sub, "tag", structural=True,
                 bounds=(lane_x, bx - 0.04))

    # arm A
    ya = top + 0.08
    a1 = add_box(d, "A_attempt", bx, ya, 0.8, "", [T("one attempt", center=True)],
                 valign="center")
    lane_label("A", a1.cy - lh("head") / 2, "1 call")
    add_text(d, "A_note", a1.right + 0.1, a1.cy, "no checks, no retry", "tag",
             bounds=(a1.right, content_r))

    # arm B
    yb = a1.bottom + 0.3
    b1 = add_box(d, "B_attempt", bx, yb, 0.62, "", [T("attempt", center=True)], valign="center")
    b2 = add_box(d, "B_checks", b1.right + 0.18, yb, 0.86, "",
                 [T("write and run its own checks", center=True)], valign="center")
    b1.h = b2.h
    for lb in d.labels:
        if lb.key == "B_attempt":
            lb.y = b1.cy
    dia = add_diamond(d, "B_pass", b2.right + 0.42, b2.cy, 0.7, 0.46, ["checks", "pass?"])
    lane_label("B", b1.cy - lh("head") / 2, "up to k calls")
    rep = add_box(d, "B_repair", b2.x, b2.bottom + 0.24, dia.cx - 0.12 - b2.x, "",
                  [T("repair, with the failures fed back", center=True)], valign="center")
    counter = add_box(d, "B_counter", bx, rep.y, 0.8, "",
                      [T(f"records {ci},", "note", center=True),
                       T("the calls B used", "note", center=True)], valign="center",
                      ls="dashed")
    add_link(d, "flow", [(b1.right + 0.02, b1.cy), (b2.x - 0.02, b1.cy)])
    add_link(d, "flow", [(b2.right + 0.02, b2.cy), (dia.x - 0.01, b2.cy)])
    add_link(d, "flow", [(dia.cx, dia.bottom + 0.01), (dia.cx, rep.cy),
                         (rep.right + 0.02, rep.cy)])
    add_text(d, "flow", dia.cx + 0.05, dia.bottom + 0.08, "no, calls left", "tag",
             bounds=(dia.cx, content_r))
    add_link(d, "flow", [(b2.x + 0.3, rep.y - 0.01), (b2.x + 0.3, b2.bottom + 0.01)])

    # arm C
    yc = max(rep.bottom, counter.bottom) + 0.36
    boxes = []
    cx_ = bx
    for i, lab in enumerate(("try 1", "try 2", "…", f"try {ci}")):
        w_ = 0.24 if lab == "…" else 0.44
        boxes.append(add_box(d, f"C_try{i}", cx_, yc, w_, "", [T(lab, center=True)],
                             valign="center", ls="dotted" if lab == "…" else "solid",
                             structural=True))
        cx_ += w_ + 0.06
    cfin = add_box(d, "C_final", cx_ + 0.08, yc, content_r - (cx_ + 0.08), "",
                   [T("self-consistency, else the last attempt", center=True)],
                   valign="center")
    for bxx in boxes:
        bxx.h = cfin.h
    for lb in d.labels:
        if lb.key.startswith("C_try"):
            lb.y = cfin.cy
    add_link(d, "flow", [(boxes[-1].right + 0.02, cfin.cy), (cfin.x - 0.02, cfin.cy)])
    lane_label("C", cfin.cy - lh("head") / 2, f"exactly {ci} calls")
    add_text(d, "C_note", bx, cfin.bottom + 0.09,
             "unguided: no checks, no feedback between tries", "tag",
             bounds=(bx, content_r))
    mx = boxes[0].cx
    add_link(d, "match", [(mx, counter.bottom + 0.01), (mx, yc - 0.01)], ls="dashed", lw=1.1)
    add_text(d, "match", mx + 0.07, (counter.bottom + yc) / 2,
             f"matched per instance: C gets exactly {ci} calls on instance i", "tag",
             bounds=(mx, content_r))

    lanes_bottom = cfin.bottom + 0.09 + lh("tag")
    inst = add_box(d, "instance", MARGIN, top, inst_w, "Instance i",
                   [T("one task; every arm runs on it, so arms are compared in pairs")],
                   h=lanes_bottom - top)
    for y in (a1.cy, b1.cy, cfin.cy):
        add_link(d, "flow", [(inst.right + 0.02, y), (lane_x - 0.04, y)])

    sc = add_box(d, "scorer", score_x, top, WIDTH - MARGIN - score_x, "Hidden-check scorer",
                 [T("checks the harness never sees"),
                  T("per-instance score: the fraction of hidden checks passed"),
                  T("several runs per arm, averaged within the instance first", "note")],
                 h=lanes_bottom - top)
    add_link(d, "flow", [(a1.right + 0.02 + tw("no checks, no retry", "tag") + 0.12, a1.cy),
                         (sc.x - 0.02, a1.cy)])
    add_link(d, "flow", [(dia.right + 0.01, dia.cy), (sc.x - 0.02, dia.cy)])
    add_text(d, "flow", dia.right + 0.05, dia.cy - 0.075, "yes, or k spent", "tag",
             bounds=(dia.right, sc.x))
    add_link(d, "flow", [(cfin.right + 0.02, cfin.cy), (sc.x - 0.02, cfin.cy)])

    # contrasts
    top2 = lanes_bottom + 0.22
    target = pilot["target_effect"]
    con = add_box(d, "contrasts", MARGIN, top2, 2.0, "Pre-stated contrasts",
                  [KV("primary", "B − C", "em"),
                   T("paired by instance: checking and repair against the same number of "
                     "calls spent on unguided retries", "note"),
                   KV("secondary", "B − A"),
                   T("the literature's design, confounded with compute; a calibration check",
                     "note"),
                   KV("also reported", "C − A"),
                   T("the effect of compute alone", "note"),
                   T("target effect " + d.num("target", target, f"+{100 * target:.0f} points",
                                               "contrasts", PI), "note")],
                  structural=True)

    # the pilot inset
    cells = sorted(pilot_cells(pilot), key=lambda c: c["est"])
    ix0, ix1 = con.right + 0.18, WIDTH - MARGIN
    inset_title = "Pilot, arm A only: the baseline score against the pre-stated band"
    ith = box_height(ix1 - ix0, inset_title, [])
    row = 0.12
    lab_col = max(tw(suite_label(c["suite"], c["model"]) + f"  n = {c['n']}", "tag")
                  for c in cells)
    ax0 = ix0 + PADX + lab_col + 0.1
    ax1 = ix1 - PADX - 0.06
    plot_top = top2 + ith + 0.16
    plot_h = row * len(cells)
    axis_y = plot_top + plot_h + 0.03
    foot_y = axis_y + 0.03 + lh("tag") + 0.05
    n_point = sum(c["in_band_point"] for c in cells)
    n_int = sum(c["in_band_interval"] for c in cells)
    ran = paths.tier3_runs.exists()
    foot = [
        "● inside the band on the point estimate: " + d.num(
            "n_in_band_point", n_point, str(n_point), "inset", PI) + " of "
        + d.num("n_cells", len(cells), str(len(cells)), "inset", PI) + " cells",
        "bars: 95% t intervals; wholly inside the band: " + d.num(
            "n_in_band_interval", n_int, str(n_int), "inset", PI) + " of "
        + d.num("n_cells_2", len(cells), str(len(cells)), "inset", PI),
        "confirmatory comparison: " + ("run" if ran else "not run, as the protocol requires "
                                                         "when the pilot fails"),
    ]
    foot_lines = [ln for f in foot for ln in wrap(f, ix1 - ix0 - 2 * PADX, "tag")]
    ih = max(foot_y - top2 + len(foot_lines) * lh("tag") + PADY, con.h)
    add_box(d, "inset", ix0, top2, ix1 - ix0, inset_title, [], h=ih, structural_title=False)

    def X(v: float) -> float:
        return ax0 + (ax1 - ax0) * v

    d.shapes.append(Shape("inset_band", "rect", X(lo), plot_top - 0.02, X(hi) - X(lo),
                          plot_h + 0.04, fill=PALE, hatch="....", edge=MID, lw=0.4, z=2.2,
                          parent="inset", rounded=False))
    add_text(d, "inset", (X(lo) + X(hi)) / 2, plot_top - 0.02 - lh("tag") / 2 - 0.01,
             "pre-stated band " + d.num("band_low", lo, f"{100 * lo:.0f}", "inset", PI)
             + "–" + d.num("band_high", hi, f"{100 * hi:.0f}%", "inset", PI), "tag",
             ha="center", bounds=(ax0 - 0.3, ix1 - PADX))
    d.links.append(Link("inset_axis", [(ax0, axis_y), (ax1, axis_y)], arrow=False, lw=0.6))
    for v in (0.0, 0.25, 0.5, 0.7, 1.0):
        d.links.append(Link("inset_axis", [(X(v), axis_y), (X(v), axis_y + 0.03)],
                            arrow=False, lw=0.6))
    for v, txt in ((0.0, "0"), (0.5, "0.5"), (1.0, "1")):
        add_text(d, "inset_axis", X(v), axis_y + 0.03 + lh("tag") / 2, txt, "tag",
                 ha="center", structural=True)
    add_text(d, "inset_axis", ax0 - 0.08, axis_y + 0.03 + lh("tag") / 2,
             "share of hidden checks passed", "tag", ha="right", structural=True,
             bounds=(ix0 + PADX, ax0 - 0.04))
    for i, c in enumerate(cells):
        yy = plot_top + (i + 0.5) * row
        lab = suite_label(c["suite"], c["model"])
        add_text(d, "inset", ix0 + PADX, yy, lab + "  n = " + d.num(
            f"pilot_n_{c['key']}", c["n"], str(c["n"]), "inset", PI), "tag",
                 bounds=(ix0 + PADX, ax0 - 0.04))
        # a score is a fraction, so the t interval is drawn clipped to [0, 1]
        d.links.append(Link("inset_marks", [(X(max(c["ci_low"], 0.0)), yy),
                                            (X(min(c["ci_high"], 1.0)), yy)],
                            arrow=False, lw=0.8, z=5.5))
        d.marks.append(Mark(f"pilot:{c['key']}", X(c["est"]), yy, "o", 3.0,
                            filled=c["in_band_point"]))
    for j, ln in enumerate(foot_lines):
        add_text(d, "inset", ix0 + PADX, foot_y + (j + 0.5) * lh("tag"), ln, "tag",
                 bounds=(ix0 + PADX, ix1 - PADX))
    d.meta["pilot_cells"] = cells
    d.meta["x_of"] = (ax0, ax1)
    d.height = top2 + ih + MARGIN
    return d

# ------------------------------------------------------------- Fig. 5: RQ3 triangulation


def layout_rq3(paths: Paths) -> Diagram:
    """Fig. 5: the RQ3 designs on one ordinal axis of what each can identify.

    The bars do not encode a number: their length is the rung of identification a design reaches
    (association; a component effect confounded with compute and with selective reporting; the
    effect at equal compute), and the fill says which way its estimate is biased. The estimates
    sit in the right-hand column on their own axes, because the three designs do not share a unit.
    """
    d = Diagram("rq3_triangulation")
    out = read_json(paths.outcomes)
    abl = read_json(paths.ablation_summary)
    cred = {r["dimension"]: r for r in read_csv(paths.credible)}
    pooled = {r["dimension"]: r for r in read_csv(paths.pooled)}
    pilot = read_json(paths.pilot)
    O, AS, CR, PO, PI = (rel(paths.outcomes), rel(paths.ablation_summary), rel(paths.credible),
                         rel(paths.pooled), rel(paths.pilot))
    corpus = corpus_row(paths.corpus)

    ma = next(c for c in out["contrasts"] if c["dimension"] == "multi_agent_topology")
    sv_c = cred["self_verification"]
    sv_p = pooled["self_verification"]
    cells = pilot_cells(pilot)
    lo, hi = pilot["band"]

    col1 = (MARGIN, 1.5)
    col2 = (1.62, 3.42)
    col3 = (3.58, WIDTH - MARGIN)
    levels = ["association", "component effect, confounded", "effect at equal compute"]
    hy = MARGIN
    for x, txt in ((col1[0], "Design"), (col2[0], "What it can identify"),
                   (col3[0], "Headline estimate, in its own units")):
        add_text(d, "head", x, hy + lh("head") / 2, txt, "head", structural=True)
    lvl_y = hy + lh("head") + 0.04
    third = (col2[1] - col2[0]) / 3
    lvl_x = [col2[0] + third * (i + 1) for i in range(3)]
    n_lv = 1
    for x, lvl in zip(lvl_x, levels, strict=True):
        lines = wrap(lvl, third - 0.05, "tag")
        n_lv = max(n_lv, len(lines))
        for j, ln in enumerate(lines):
            add_text(d, "levels", x - 0.02, lvl_y + (j + 0.5) * lh("tag"), ln, "tag",
                     ha="right", bounds=(x - third + 0.02, x), structural=True)
    top = lvl_y + n_lv * lh("tag") + 0.07
    d.links.append(Link("levels", [(col2[0], top - 0.035), (col2[1] + 0.06, top - 0.035)],
                        arrow=True, lw=0.6))
    for x in lvl_x:
        d.links.append(Link("levels", [(x, top - 0.06), (x, top - 0.01)], arrow=False, lw=0.6))

    rows = [
        {"key": "cross", "level": 1, "bound": "lower", "title": "Cross-paper association",
         "sub": d.num("keys", out["comparable_set"]["keys"], str(out["comparable_set"]["keys"]),
                      "cross", O)
         + " comparable keys (benchmark, split, model) over "
         + d.num("key_systems", out["comparable_set"]["systems"],
                 str(out["comparable_set"]["systems"]), "cross", O) + " systems",
         "bound_text": "lower bound: scaffold drift pulls it towards zero"},
        {"key": "within", "level": 2, "bound": "upper", "title": "Within-study meta-analysis",
         "sub": d.num("contrasts", abl["funnel"]["contrasts"], str(abl["funnel"]["contrasts"]),
                      "within", AS) + " of the authors' own ablation contrasts, "
         + d.num("papers", abl["funnel"]["papers"], str(abl["funnel"]["papers"]), "within", AS)
         + " papers",
         "bound_text": "upper bound: null ablations go unreported"},
    ]
    if corpus is not None:
        # the row's subtitle is the POOLED total, from the same run summary the manuscript's
        # macros are generated from, then the self-verification counts behind its estimate
        sub = "the same design, harvested across the whole corpus"
        total = corpus_total(paths.corpus_summary)
        if total is not None:
            CS = rel(paths.corpus_summary)
            sub = (d.num("corpus_total_contrasts", total[0], fmt_int(total[0]), "corpus", CS)
                   + " contrasts from "
                   + d.num("corpus_total_papers", total[1], fmt_int(total[1]), "corpus", CS)
                   + " papers, same design")
            if corpus["n_contrasts"] is not None and corpus["n_papers"] is not None:
                sub += ("; self-verification "
                        + d.num("corpus_contrasts", corpus["n_contrasts"],
                                fmt_int(corpus["n_contrasts"]), "corpus", rel(paths.corpus))
                        + " from "
                        + d.num("corpus_papers", corpus["n_papers"], fmt_int(corpus["n_papers"]),
                                "corpus", rel(paths.corpus)))
        rows.append({"key": "corpus", "level": 2, "bound": "upper", "title": "corpus-wide",
                     "sub": sub, "bound_text": "upper bound, as above"})
    rows.append({"key": "ablation", "level": 3, "bound": "unbiased",
                 "title": "Filed compute-matched ablation",
                 "sub": "arms paired by instance; verification against unguided retries at "
                        "equal calls",
                 "bound_text": "unbiased by design, once it can run"})

    # the right-hand column: estimate text per row, built first so row heights can use it
    est_text = {
        "cross": ["multi-agent topology " + d.num("ma_effect", ma["effect"],
                                                  fmt_signed(ma["effect"]), "cross", O)
                  + " within-key sd, 95% CI " + d.num("ma_ci_low", ma["ci_low"],
                                                       fmt_dec(ma["ci_low"], 2), "cross", O)
                  + " to " + d.num("ma_ci_high", ma["ci_high"], fmt_dec(ma["ci_high"], 2),
                                   "cross", O)
                  + ", on " + d.num("ma_keys", ma["n_keys"], str(ma["n_keys"]), "cross", O)
                  + " keys"],
    }
    pi = (float(sv_p["pi_low"]), float(sv_p["pi_high"]))
    est_text["within"] = [
        "self-verification " + d.num("sv_mu", float(sv_p["mu_rel"]),
                                     fmt_signed(float(sv_p["mu_rel"]), 3), "within", PO)
        + " relative (" + d.num("sv_contrasts", int(sv_p["n_contrasts"]),
                                str(int(sv_p["n_contrasts"])), "within", PO) + " contrasts, "
        + d.num("sv_papers", int(sv_p["n_papers"]), str(int(sv_p["n_papers"])), "within", PO)
        + " papers); discounted for selective reporting "
        + d.num("sv_disc", float(sv_c["mu_discounted"]),
                fmt_signed(float(sv_c["mu_discounted"]), 3), "within", CR)
        + "; prediction interval " + d.num("sv_pi_low", pi[0], fmt_dec(pi[0]), "within", PO)
        + " to " + d.num("sv_pi_high", pi[1], fmt_dec(pi[1]), "within", PO)
        + (" crosses zero" if pi[0] < 0 < pi[1] else "")]
    if corpus is not None:
        C = rel(paths.corpus)
        t = ("self-verification " + d.num("corpus_mu", corpus["mu"],
                                          fmt_signed(corpus["mu"], 3), "corpus", C) + " relative")
        if corpus["ci_low"] is not None and corpus["ci_high"] is not None:
            t += (", 95% CI " + d.num("corpus_ci_low", corpus["ci_low"],
                                      fmt_dec(corpus["ci_low"]), "corpus", C) + " to "
                  + d.num("corpus_ci_high", corpus["ci_high"], fmt_dec(corpus["ci_high"]),
                          "corpus", C))
        if corpus["pi_low"] is not None and corpus["pi_high"] is not None:
            t += ("; prediction interval " + d.num("corpus_pi_low", corpus["pi_low"],
                                                   fmt_dec(corpus["pi_low"]), "corpus", C)
                  + " to " + d.num("corpus_pi_high", corpus["pi_high"],
                                   fmt_dec(corpus["pi_high"]), "corpus", C)
                  + (" crosses zero" if corpus["pi_low"] < 0 < corpus["pi_high"] else ""))
        est_text["corpus"] = [t]
    n_int = sum(c["in_band_interval"] for c in cells)
    n_pt = sum(c["in_band_point"] for c in cells)
    est_text["ablation"] = [
        "no estimate: the pilot failed its band. "
        + d.num("abl_in_band_interval", n_int, str(n_int), "ablation", PI) + " of "
        + d.num("abl_cells", len(cells), str(len(cells)), "ablation", PI)
        + " baseline cells lie inside " + d.num("abl_band_low", lo, f"{100 * lo:.0f}",
                                                "ablation", PI)
        + "–" + d.num("abl_band_high", hi, f"{100 * hi:.0f}%", "ablation", PI)
        + " on their 95% interval (" + d.num("abl_in_band_point", n_pt, str(n_pt), "ablation",
                                             PI)
        + " on the point estimate), so no arm comparison is published"]

    forest_h = 0.26
    bar_h = 0.16
    bound_style = {"lower": (WHITE, None), "upper": (PALE, "////"), "unbiased": (DARK, None)}
    y = top
    for i, r in enumerate(rows):
        k = r["key"]
        indent = 0.14 if k == "corpus" else 0.0
        t_lines = wrap(r["title"], col1[1] - col1[0] - indent, "head")
        s_lines = wrap(r["sub"], col1[1] - col1[0] - indent, "tag")
        b_lines = wrap(r["bound_text"], col2[1] - col2[0], "tag")
        e_lines = [ln for t in est_text[k] for ln in wrap(t, col3[1] - col3[0], "tag")]
        has_forest = k != "ablation"
        h1 = len(t_lines) * lh("head") + len(s_lines) * lh("tag")
        h2 = bar_h + 0.04 + len(b_lines) * lh("tag")
        h3 = (forest_h if has_forest else 0.0) + len(e_lines) * lh("tag")
        rh = max(h1, h2, h3) + 0.12
        if i:
            d.links.append(Link("rule", [(MARGIN, y - 0.04), (WIDTH - MARGIN, y - 0.04)],
                                arrow=False, lw=0.35, color=MID))
        yy = y + 0.02
        for ln in t_lines:
            add_text(d, k, col1[0] + indent, yy + lh("head") / 2, ln, "head", structural=True,
                     bounds=(col1[0], col1[1]))
            yy += lh("head")
        for ln in s_lines:
            add_text(d, k, col1[0] + indent, yy + lh("tag") / 2, ln, "tag",
                     bounds=(col1[0], col1[1]))
            yy += lh("tag")
        fill, hatch = bound_style[r["bound"]]
        d.shapes.append(Shape(k, "rect", col2[0], y + 0.03, lvl_x[r["level"] - 1] - col2[0],
                              bar_h, fill=fill, hatch=hatch, lw=0.8, z=2.2, rounded=False))
        yy = y + 0.03 + bar_h + 0.04
        for ln in b_lines:
            add_text(d, k, col2[0], yy + lh("tag") / 2, ln, "tag", bounds=(col2[0], col2[1]))
            yy += lh("tag")
        yy = y + (forest_h if has_forest else 0.02)
        for ln in e_lines:
            add_text(d, k, col3[0], yy + lh("tag") / 2, ln, "tag", bounds=(col3[0], col3[1]))
            yy += lh("tag")
        r["y"] = y
        r["h"] = rh
        y += rh + 0.08

    ex0, ex1 = col3[0] + 0.12, col3[1] - 0.12

    def forest(key: str, y: float, pts: dict, toward_zero: bool,
               share: tuple[dict, ...] = ()) -> None:
        """One estimate on its own axis; rows in ``share`` (same unit) share the scale."""
        vals = [0.0, *pts["ci"], *pts.get("pi", ())]
        for other in share:
            vals += [*other["ci"], *other.get("pi", ())]
        lo_, hi_ = min(vals), max(vals)
        pad = 0.06 * (hi_ - lo_)
        span_lo, span_hi = lo_ - pad, hi_ + pad

        def X(v: float) -> float:
            return ex0 + (ex1 - ex0) * (v - span_lo) / (span_hi - span_lo)

        yy = y + 0.14
        d.links.append(Link(key, [(X(0), yy - 0.08), (X(0), yy + 0.06)], arrow=False,
                            ls="dashed", lw=0.6))
        add_text(d, key, X(0), yy - 0.08 - lh("tag") / 2 - 0.005, "0", "tag", ha="center",
                 structural=True)
        if "pi" in pts:
            a, b_ = pts["pi"]
            d.links.append(Link(key, [(X(a), yy), (X(b_), yy)], arrow=False, lw=0.7,
                                ls="dotted"))
            for v in (a, b_):
                d.links.append(Link(key, [(X(v), yy - 0.035), (X(v), yy + 0.035)],
                                    arrow=False, lw=0.7))
        a, b_ = pts["ci"]
        d.links.append(Link(key, [(X(a), yy), (X(b_), yy)], arrow=False, lw=1.8, z=5.0))
        d.marks.append(Mark(key, X(pts["est"]), yy, "o", 3.6, filled=True))
        if "disc" in pts:
            d.marks.append(Mark(key, X(pts["disc"]), yy, "D", 3.4, filled=False, z=6.5))
        # the bound direction: which side of the estimate the true value lies on
        e = X(pts["est"])
        tip = e - 0.2 if toward_zero else e + 0.2
        d.links.append(Link(key, [(e, yy - 0.05), (e, yy - 0.09), (tip, yy - 0.09)],
                            arrow=True, lw=0.6))

    by = {r["key"]: r for r in rows}
    forest("cross", by["cross"]["y"], {"est": float(ma["effect"]),
                                       "ci": (float(ma["ci_low"]), float(ma["ci_high"]))},
           toward_zero=False)
    within_pts = {"est": float(sv_p["mu_rel"]),
                  "ci": (float(sv_p["ci_low"]), float(sv_p["ci_high"])), "pi": pi,
                  "disc": float(sv_c["mu_discounted"])}
    corpus_pts: dict = {}
    if corpus is not None:
        corpus_pts = {"est": corpus["mu"]}
        ci = (corpus["ci_low"], corpus["ci_high"])
        corpus_pts["ci"] = ci if None not in ci else (corpus["mu"], corpus["mu"])
        if corpus["pi_low"] is not None and corpus["pi_high"] is not None:
            corpus_pts["pi"] = (corpus["pi_low"], corpus["pi_high"])
    # the two within-study rows are in the same unit, so they share one scale
    forest("within", by["within"]["y"], within_pts, toward_zero=True,
           share=(corpus_pts,) if corpus_pts else ())
    if corpus_pts:
        forest("corpus", by["corpus"]["y"], corpus_pts, toward_zero=True, share=(within_pts,))

    d.meta["pi_crosses_zero"] = pi[0] < 0 < pi[1]
    d.meta["rows"] = [r["key"] for r in rows]
    d.meta["levels"] = {r["key"]: r["level"] for r in rows}
    d.meta["bounds"] = {r["key"]: r["bound"] for r in rows}
    legend_y = y - 0.02
    d.links.append(Link("rule", [(MARGIN, legend_y - 0.02), (WIDTH - MARGIN, legend_y - 0.02)],
                        arrow=False, lw=0.35, color=MID))
    leg = ("Bars: the rung each design reaches; white = lower bound, hatched = upper bound, "
           "dark = unbiased. ● estimate with its 95% CI; ◇ discounted for selective "
           "reporting; dotted, prediction interval; small arrow, the side of the estimate on "
           "which the true value lies.")
    last = legend_y
    for j, ln in enumerate(wrap(leg, WIDTH - 2 * MARGIN, "tag")):
        add_text(d, "legend", MARGIN, legend_y + 0.02 + (j + 0.5) * lh("tag"), ln, "tag",
                 bounds=(MARGIN, WIDTH - MARGIN))
        last = legend_y + 0.02 + (j + 1) * lh("tag")
    d.height = last + MARGIN
    return d

LAYOUTS = {"pipeline_overview": layout_pipeline, "coding_framework": layout_coding,
           "screening_framework": layout_screening, "tier3_design": layout_tier3,
           "rq3_triangulation": layout_rq3}


def build(name: str, paths: Paths | None = None) -> Diagram:
    return LAYOUTS[name](paths or Paths())


# ---------------------------------------------------------------------------------- rendering


def render(d: Diagram, out_stem: Path, exts: tuple[str, ...] = ("svg", "pdf"),
           dpi: int = 300) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

    plt.rcParams["hatch.linewidth"] = 0.5
    plt.rcParams["svg.fonttype"] = "path"
    plt.rcParams["pdf.fonttype"] = 42
    fig, ax = plt.subplots(figsize=(d.width, d.height))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, d.width)
    ax.set_ylim(d.height, 0)          # y measured down from the top edge
    ax.set_aspect("equal")
    ax.axis("off")

    for s in d.shapes:
        ls = LS.get(s.ls, "solid")
        if s.kind == "diamond":
            ax.add_patch(Polygon([(s.cx, s.y), (s.right, s.cy), (s.cx, s.bottom), (s.x, s.cy)],
                                 closed=True, facecolor=s.fill, edgecolor=s.edge or "none",
                                 linewidth=s.lw, zorder=s.z))
        elif s.rounded and s.kind in ("box", "group"):
            ax.add_patch(FancyBboxPatch((s.x, s.y), s.w, s.h,
                                        boxstyle="round,pad=0,rounding_size=0.035",
                                        facecolor=s.fill, edgecolor=s.edge or "none",
                                        linewidth=s.lw, linestyle=ls, zorder=s.z))
        else:
            ax.add_patch(Rectangle((s.x, s.y), s.w, s.h, facecolor=s.fill,
                                   edgecolor=s.edge if s.edge else "none",
                                   linewidth=s.lw if s.edge else 0, linestyle=ls,
                                   hatch=s.hatch, zorder=s.z))
            if s.kind == "strip":
                ry = s.y if s.ls == "top-rule" else s.bottom
                ax.plot([s.x, s.right], [ry, ry], color=INK, linewidth=0.5, zorder=s.z + 0.05)

    for lk in d.links:
        ls = LS.get(lk.ls, lk.ls)
        pts = lk.points
        if lk.arrow:
            if len(pts) > 2:
                ax.plot([p[0] for p in pts[:-1]], [p[1] for p in pts[:-1]], color=lk.color,
                        linewidth=lk.lw, linestyle=ls, zorder=lk.z, solid_capstyle="butt")
            ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=7,
                                         linewidth=lk.lw, color=lk.color, linestyle=ls,
                                         shrinkA=0, shrinkB=0, zorder=lk.z))
        else:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=lk.color, linewidth=lk.lw,
                    linestyle=ls, zorder=lk.z, solid_capstyle="butt")

    for m in d.marks:
        ax.plot([m.x], [m.y], marker=m.marker, markersize=m.size,
                markerfacecolor=INK if m.filled else WHITE, markeredgecolor=INK,
                markeredgewidth=0.7, linestyle="none", zorder=m.z)

    for lb in d.labels:
        kw = {"family": FONT, "size": SIZE[lb.style],
              "weight": "bold" if lb.style in BOLD else "normal",
              "style": "italic" if lb.style in ITALIC else "normal"}
        ax.text(lb.x, lb.y, lb.text, ha=lb.ha, va="center_baseline" if not lb.rotation else
                "center", rotation=lb.rotation, fontdict=kw, zorder=lb.z, color=INK,
                bbox={"facecolor": WHITE, "edgecolor": "none", "pad": 0.5} if lb.bg else None)

    out_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in exts:
        p = out_stem.with_suffix(f".{ext}")
        fig.savefig(p, format=ext, dpi=dpi)
        paths.append(p)
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--only", nargs="*", choices=FIGURES, help="render only these figures")
    p.add_argument("--out-dir", default=str(REPO / "paper/figures"))
    p.add_argument("--png", action="store_true", help="also write a PNG preview of each")
    p.add_argument("--no-render", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    paths = Paths()
    rec = parse_reconciliation(paths.reconciliation.read_text(encoding="utf-8"))
    drift = release_drift(paths, rec)
    if drift.get("checked") and not drift["matches"]:
        print(f"WARNING: docs/count_reconciliation.md states {rec['released_systems']:,} released "
              f"systems and {rec['cells']:,} cells, but data/systems.json now holds "
              f"{drift['systems']:,} systems and {drift['cells']:,} cells "
              f"({drift['states']}). The figures print the reconciliation's counts; update the "
              "reconciliation (or rebuild the release) so the two agree.")
    if not paths.corpus.exists():
        print(f"note: {rel(paths.corpus)} not present; rq3_triangulation drawn without the "
              "corpus-wide row")
    status = False
    for name in args.only or FIGURES:
        d = build(name, paths)
        print(f"{name}: {d.width:.2f} x {d.height:.2f} in, {len(d.numbers)} numbers from "
              f"{len({n.source for n in d.numbers})} files")
        problems = check_fit(d)
        for pr in problems:
            print("  FIT:", pr)
        status = status or bool(problems)
        if args.no_render:
            continue
        exts = ("svg", "pdf", "png") if args.png else ("svg", "pdf")
        for path in render(d, Path(args.out_dir) / name, exts):
            print("  wrote", rel(path), path.stat().st_size, "bytes")
    return 1 if status else 0


if __name__ == "__main__":
    sys.exit(main())
