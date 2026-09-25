#!/usr/bin/env python
"""Taxonomy map: the nine layers and 38 dimensions of the unified taxonomy, drawn from
``schema/dimensions.json`` (Phase 7; the figure called for by section 5's TODO).

WHY this script exists
----------------------
The taxonomy figure is the one figure in the paper that carries no data: it is a picture of the
*instrument*. That makes drift the only way it can be wrong, and drift is silent - a dimension
renamed or re-valued in the schema would leave a figure that still looks authoritative. So every
string and every count in the figure is read out of ``schema/dimensions.json`` at render time:
layer ids and names, dimension ids, dimension keys, ``multi``, ``type``, and ``len(values)``.
Nothing about the taxonomy is written down twice. The only things this file decides are geometry
(which layer sits in which row) and the two displacement arrows, and both are asserted against
the schema in ``tests/test_plot_taxonomy.py``.

Layout, and why it is the layout
--------------------------------
* Top row A, B, C - the layers that code definition clauses (i)-(iii), the three NECESSARY
  clauses (``docs/definition.md`` section 2.1: a layer that does not assemble input, execute
  actions, or loop is not a harness).
* Second row D, E, F, G, H - clauses (iv)-(viii), which may be trivial in a given harness. A
  trivial value is still a value and is coded ``none``, not ``not_reported``.
* M as a detached band beneath, because M is metadata on the system and not a clause of the
  definition at all; detaching it stops a reader counting nine clauses.
* One row per dimension inside each block: id, key, and how many values it permits.

Reading the value column
------------------------
``6``    a single-valued enumeration with 6 permitted values.
``{6}``  a MULTI-valued enumeration: a system may carry several of the 6 values at once, so the
         coded cell is a set. 15 of the 38 dimensions are multi-valued, and the braces are what
         marks them: the grey row band is redundant so the figure survives greyscale printing.
``integer`` / ``date`` / ``string``  the four non-enumerated dimensions (B2 tool count, M5 first
         release date, M6 pinned version, M7 stars). They are marked by their schema ``type``
         rather than by a value count, because "number of permitted values" is not a property
         they have.

Arrows
------
* Thin solid A -> B -> C -> A: the step loop. Context assembly feeds the tool interface, the tool
  interface feeds the control loop, and the control loop decides that there is another step, which
  re-enters context assembly. The loop is what makes the A/B/C trio necessary rather than merely
  common.
* Two dashed arrows, the two deliberate clause displacements documented in ``docs/definition.md``
  section 4. Each runs from the displaced dimension to the layer whose clause it actually codes:

  - ``F1 -> C``: the termination condition codes clause (iii) (continuation AND termination), whose
    layer is C, but it is placed in F so that termination policy and budget are reported together
    (RQ4 flags both as under-reported).
  - ``G4 -> F``: the permission model codes clause (vi) (budgets AND permissions), whose layer is
    F, but it is placed in G because in practice it is configured alongside isolation.

  Section 5's TODO asked for the second arrow as ``G4 -> C5``. The schema and
  ``docs/definition.md`` do not support that target: C5 (human-in-the-loop) is a third dimension
  co-coding clause (vi) and is itself NOT displaced - it sits in C, its own clause's layer - so an
  arrow G4 -> C5 would assert a displacement that the documented taxonomy does not contain.
  ``docs/definition.md`` section 4 names exactly two exceptions, F1 and G4, and gives G4's home
  clause as (vi), i.e. layer F. The arrow is therefore drawn G4 -> F.

Usage:
    python scripts/plot_taxonomy.py [--dimensions schema/dimensions.json]
                                    [--out paper/figures/taxonomy_map] [--no-render]

Size. The figure comes out about 7.15 x 4.25 in (it is measured, not fixed: block widths are
derived from the rendered width of the schema's own keys, so a longer key makes a wider figure).
It is meant to be included at ``width=\\linewidth`` in the acmart *manuscript* format used by
``paper/main.tex``, which is single-column with a text block of roughly 6.4-6.8 in: that is a
downscale of about 5-10%, leaving the dimension rows at ~5.8-6.1 pt and the layer titles at
~6.9-7.2 pt. Row text is set at 6.4 pt rather than the house 7.5 pt for exactly this reason -
five side-by-side blocks on the second row is what sets the width, and the width is what sets
the scale factor. Nothing in the figure depends on colour: the multi-valued mark is the braces
around the count and the non-enum mark is the italic type name, so the grey row bands and the
title strips can all go to flat grey without losing information.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Geometry, in inches. A single unit of the axes is one inch, so every number here is a physical
# size on the page before \includegraphics scales it.
ROW_FS = 6.4          # dimension rows
TITLE_FS = 7.6        # layer titles
BANNER_FS = 6.2       # the two row banners
TAG_FS = 5.6          # arrow tags and the legend note
ROW_H = 0.135         # one dimension row
TITLE_LINE_H = 0.12   # one line of a layer title
TITLE_PAD = 0.075     # padding around the title strip
PAD_X = 0.055         # horizontal padding inside a block
PAD_B = 0.065         # padding below the last row inside a block
MARGIN = 0.07
GAP_ROW1 = 0.55       # A|B and B|C: wide enough for the loop arrows
GAP_ROW2 = 0.08       # D|E, E|F, G|H
GAP_DISPLACED = 0.26  # F|G: carries the G4 -> F arrow and its tag
LOOP_H = 0.32         # headroom above row 1 for the C -> A return
BANNER_H = 0.145
INTER_ROWS = 0.34     # between row 1 and row 2: carries the F1 -> C horizontal run
BAND_GAP = 0.26       # between row 2 and the M band
NOTE_H = 0.115        # one line of the legend note
M_COLS = 4            # the M band is a band, so its 7 entries wrap into columns

# Which layer sits where. Flattened, this must equal the schema's layer order; the test asserts it.
ROW1_LAYERS = ("A", "B", "C")
ROW2_LAYERS = ("D", "E", "F", "G", "H")
BAND_LAYERS = ("M",)

# The A -> B -> C -> A step loop.
LOOP = ("A", "B", "C")

# The two deliberate clause displacements of docs/definition.md section 4, as
# (dimension, layer whose clause it codes, definition clause, one-line reason). Both are checked
# against the schema before anything is drawn: the source dimension must exist and must NOT
# already live in the target layer, or there is no displacement to draw.
DISPLACEMENTS = (
    ("F1", "C", "iii", "termination reported with budget"),
    ("G4", "F", "vi", "permission configured with isolation"),
)

INK = "#333333"
BAND_FILL = "#ececec"   # multi-valued rows; redundant with the braces, so greyscale-safe
TITLE_FILL = "#dde6f0"  # layer title strip; carries no information


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------- text measurement


def _font(size: float):
    from matplotlib.font_manager import FontProperties

    return FontProperties(family="DejaVu Sans", size=size)


def text_width(s: str, size: float, bold: bool = False) -> float:
    """Width of ``s`` in inches at ``size`` points, measured from the actual DejaVu Sans glyphs.

    Block widths are derived from this rather than from a characters-times-a-constant guess, so a
    longer key in a future schema version widens its block instead of overflowing it. TextPath
    omits side bearings, hence the 1.07 allowance; bold DejaVu Sans runs about 4% wider.
    """
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.textpath import TextPath

    if not s:
        return 0.0
    w = TextPath((0, 0), s, prop=_font(size)).get_extents().width / 72.0
    return w * 1.07 * (1.04 if bold else 1.0)


# ------------------------------------------------------------------------------------------ model


@dataclass(frozen=True)
class Entry:
    """One dimension row: what is drawn, and the schema facts it is drawn from."""

    dim_id: str
    key: str
    layer: str
    type: str
    multi: bool
    n_values: int | None    # None for the non-enumerated dimensions
    value_field: str        # "6", "{6}", or the schema type name
    label: str              # "F1 termination_condition"
    x: float = 0.0          # left edge of the label, in inches
    y: float = 0.0          # text baseline-ish centre of the row, in inches
    x_value: float = 0.0    # right edge the value field is flush against
    row_x0: float = 0.0     # extent of the row's grey band (multi-valued rows only)
    row_x1: float = 0.0


@dataclass
class Block:
    layer: str
    name: str
    title: str
    x: float
    y: float
    w: float
    h: float
    title_lines: list[str] = field(default_factory=list)
    title_h: float = 0.0
    entries: list[Entry] = field(default_factory=list)

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2


@dataclass
class Arrow:
    kind: str               # "loop" | "displacement"
    src: str                # layer id, or dimension id for a displacement
    dst: str                # layer id
    points: list[tuple[float, float]]
    tag: str = ""
    tag_xy: tuple[float, float] | None = None


@dataclass
class Layout:
    width: float
    height: float
    blocks: list[Block]
    arrows: list[Arrow]
    banners: list[tuple[float, float, str]]
    note: list[str]
    schema_version: str

    @property
    def entries(self) -> list[Entry]:
        """Every dimension entry, in schema order."""
        return [e for b in self.blocks for e in b.entries]


def value_field(dim: dict) -> str:
    """The value column for one dimension: a count, a braced count if multi-valued, or the type.

    The braces are the multi-valued marker and the type name is the non-enum marker; both are
    text, so neither depends on colour surviving a greyscale print.
    """
    if dim["type"] == "enum":
        inner = str(len(dim["values"]))
    else:
        inner = dim["type"]
    return "{" + inner + "}" if dim.get("multi") else inner


def make_entry(dim: dict) -> Entry:
    return Entry(
        dim_id=dim["id"],
        key=dim["key"],
        layer=dim["layer"],
        type=dim["type"],
        multi=bool(dim.get("multi")),
        n_values=len(dim["values"]) if dim["type"] == "enum" else None,
        value_field=value_field(dim),
        label=f"{dim['id']} {dim['key']}",
    )


def check_displacements(schema: dict) -> list[str]:
    """Return the problems with DISPLACEMENTS (empty = all supported by the schema).

    An arrow is only drawn if the schema agrees that there is something displaced: the source
    dimension must exist, the target layer must exist, and the source must not already be in the
    target layer (in which case nothing has moved and the arrow would assert a fiction).
    """
    dims = {d["id"]: d for d in schema["dimensions"]}
    layers = {ly["id"] for ly in schema["layers"]}
    problems = []
    for dim_id, target, clause, _why in DISPLACEMENTS:
        if dim_id not in dims:
            problems.append(f"{dim_id} -> {target}: no dimension {dim_id} in the schema")
            continue
        if target not in layers:
            problems.append(f"{dim_id} -> {target}: no layer {target} in the schema")
            continue
        if dims[dim_id]["layer"] == target:
            problems.append(
                f"{dim_id} -> {target}: {dim_id} already lives in layer {target}, "
                f"so clause ({clause}) is not displaced and no arrow is warranted")
    return problems


# ----------------------------------------------------------------------------------------- layout


def _block_widths(sizes: dict[str, list[dict]], layers: tuple[str, ...]) -> dict[str, float]:
    """Natural width of each layer block: widest label + a gap + widest value field + padding."""
    out = {}
    for ly in layers:
        rows = sizes[ly]
        label = max(text_width(f"{d['id']} {d['key']}", ROW_FS) for d in rows)
        val = max(text_width(value_field(d), ROW_FS) for d in rows)
        out[ly] = label + val + 0.07 + 2 * PAD_X
    return out


def wrap(text: str, max_w: float, size: float, bold: bool = False) -> list[str]:
    """Greedy word wrap to a measured width in inches (so it holds for any schema string)."""
    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, size, bold) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def layout(schema: dict) -> Layout:
    """Place every block, dimension row and arrow. Pure geometry; draws nothing.

    Everything textual comes from ``schema``: this function invents no dimension, no key and no
    count, so a schema change moves the figure rather than contradicting it.
    """
    by_layer: dict[str, list[dict]] = {ly["id"]: [] for ly in schema["layers"]}
    for d in schema["dimensions"]:
        by_layer[d["layer"]].append(d)
    names = {ly["id"]: ly["name"] for ly in schema["layers"]}

    nat = _block_widths(by_layer, ROW1_LAYERS + ROW2_LAYERS)

    # Row 2 sets the figure width: five blocks, each as wide as its own longest key needs.
    gaps2 = [GAP_DISPLACED if (a, b) == ("F", "G") else GAP_ROW2
             for a, b in itertools.pairwise(ROW2_LAYERS)]
    content_w = sum(nat[ly] for ly in ROW2_LAYERS) + sum(gaps2)

    # Row 1 has only three blocks, so it has slack; spend it on the blocks, not on the gaps,
    # keeping the two loop-arrow gaps at GAP_ROW1.
    slack = content_w - (sum(nat[ly] for ly in ROW1_LAYERS) + 2 * GAP_ROW1)
    w1 = {ly: nat[ly] + max(slack, 0.0) / len(ROW1_LAYERS) for ly in ROW1_LAYERS}

    # Layer titles are the schema's own layer names, so their length is not ours to choose: wrap
    # each one to its block and let the row's title strip take the tallest.
    titles = {ly: f"{ly}  {names[ly]}" for ly in ROW1_LAYERS + ROW2_LAYERS}
    tlines = {ly: wrap(titles[ly], (w1 if ly in ROW1_LAYERS else nat)[ly] - 2 * PAD_X,
                       TITLE_FS, bold=True)
              for ly in titles}
    t1 = max(len(tlines[ly]) for ly in ROW1_LAYERS) * TITLE_LINE_H + TITLE_PAD
    t2 = max(len(tlines[ly]) for ly in ROW2_LAYERS) * TITLE_LINE_H + TITLE_PAD
    tm = TITLE_LINE_H + TITLE_PAD

    rows1 = max(len(by_layer[ly]) for ly in ROW1_LAYERS)
    rows2 = max(len(by_layer[ly]) for ly in ROW2_LAYERS)
    rows_m = math.ceil(len(by_layer["M"]) / M_COLS)
    h1 = t1 + rows1 * ROW_H + PAD_B
    h2 = t2 + rows2 * ROW_H + PAD_B
    hm = tm + rows_m * ROW_H + PAD_B

    n_multi = sum(1 for d in schema["dimensions"] if d.get("multi"))
    note = (
        wrap("Value column: n = one of n permitted values; {n} = multi-valued, a system may "
             f"carry several of the n values at once ({n_multi} of the "
             f"{len(schema['dimensions'])} dimensions); integer / date / string = not an "
             "enumeration, so no value count.", content_w, TAG_FS)
        + wrap("Thin arrows: the A -> B -> C -> A step loop. Dashed arrows: the two deliberate "
               "clause displacements, F1 to C (clause iii, termination) and G4 to F (clause vi, "
               "permission). Generated from schema/dimensions.json v"
               f"{schema['schema_version'].split()[0]} by scripts/plot_taxonomy.py.",
               content_w, TAG_FS))

    width = content_w + 2 * MARGIN
    height = (2 * MARGIN + BANNER_H + LOOP_H + h1 + INTER_ROWS + BANNER_H + h2
              + BAND_GAP + hm + len(note) * NOTE_H + 0.06)

    blocks: list[Block] = []
    banners: list[tuple[float, float, str]] = []

    def place_row(layers: tuple[str, ...], widths: dict[str, float], gaps: list[float],
                  y: float, h: float, title_h: float) -> None:
        x = MARGIN
        for i, ly in enumerate(layers):
            blocks.append(Block(layer=ly, name=names[ly], title=titles[ly], x=x, y=y,
                                w=widths[ly], h=h, title_lines=tlines[ly], title_h=title_h))
            x += widths[ly] + (gaps[i] if i < len(gaps) else 0.0)

    y_row1 = height - MARGIN - BANNER_H - LOOP_H - h1
    place_row(ROW1_LAYERS, w1, [GAP_ROW1, GAP_ROW1], y_row1, h1, t1)
    # The banner sits above the loop arc, not between the arc and the blocks, or the C -> A
    # return would come down through it.
    banners.append((MARGIN, y_row1 + h1 + LOOP_H + 0.02,
                    "necessary clauses (i)-(iii): input assembly, action exposure, continuation"))

    y_row2 = y_row1 - INTER_ROWS - BANNER_H - h2
    place_row(ROW2_LAYERS, nat, gaps2, y_row2, h2, t2)
    # Kept short so it ends well left of the F1 -> C riser in the F|G gap.
    banners.append((MARGIN, y_row2 + h2 + 0.035,
                    "clauses (iv)-(viii): may be trivial, and a trivial value is still a value"))

    y_band = y_row2 - BAND_GAP - hm
    m_title = f"M  {names['M']} - metadata on the system, not a clause of the definition"
    blocks.append(Block(layer="M", name=names["M"], x=MARGIN, y=y_band, w=content_w, h=hm,
                        title=m_title, title_lines=[m_title], title_h=tm))

    # Dimension rows. The first row of a block sits directly under its title strip. The value
    # field is flush right against the block's own content width, not against the block edge, so
    # a block widened to fill a row does not strand its counts an inch away from their keys.
    for b in blocks:
        dims = by_layer[b.layer]
        ncols = M_COLS if b.layer == "M" else 1
        groups = [[d for j, d in enumerate(dims) if j % ncols == i] for i in range(ncols)]
        widths_lab = [max((text_width(f"{d['id']} {d['key']}", ROW_FS) for d in g), default=0.0)
                      for g in groups]
        widths_val = [max((text_width(value_field(d), ROW_FS) for d in g), default=0.0)
                      for g in groups]
        col_nat = [lab + 0.07 + val for lab, val in zip(widths_lab, widths_val, strict=True)]
        spare = (b.w - 2 * PAD_X - sum(col_nat)) / max(ncols, 1)
        col_x, x_cursor = [], b.x + PAD_X
        for cw in col_nat:
            col_x.append(x_cursor)
            x_cursor += cw + spare
        placed = []
        for i, d in enumerate(dims):
            col, row = (i % ncols, i // ncols) if ncols > 1 else (0, i)
            x0 = col_x[col]
            y = b.top - b.title_h - (row + 0.5) * ROW_H
            e = make_entry(d)
            placed.append(Entry(
                **{k: getattr(e, k) for k in
                   ("dim_id", "key", "layer", "type", "multi", "n_values", "value_field", "label")},
                x=x0, y=y, x_value=x0 + col_nat[col],
                row_x0=x0 - 0.025, row_x1=x0 + col_nat[col] + 0.025))
        b.entries = placed

    at = {b.layer: b for b in blocks}
    ent = {e.dim_id: e for b in blocks for e in b.entries}
    arrows: list[Arrow] = []

    # A -> B -> C, along the row, at 45% of the block height so they clear no text at all.
    y_arrow = y_row1 + h1 * 0.45
    for a, c in itertools.pairwise(LOOP):
        arrows.append(Arrow("loop", a, c,
                            [(at[a].right + 0.04, y_arrow), (at[c].x - 0.04, y_arrow)]))
    # C -> A: up over the top of row 1 and back, as an elbow rather than a spline so the path is
    # predictable at any figure size.
    y_top = y_row1 + h1 + LOOP_H * 0.55
    arrows.append(Arrow("loop", LOOP[-1], LOOP[0],
                        [(at[LOOP[-1]].cx, y_row1 + h1 + 0.01), (at[LOOP[-1]].cx, y_top),
                         (at[LOOP[0]].cx, y_top), (at[LOOP[0]].cx, y_row1 + h1 + 0.02)],
                        tag="next step",
                        tag_xy=((at[LOOP[0]].cx + at[LOOP[-1]].cx) / 2, y_top + 0.03)))

    # F1 -> C: right out of the F1 row into the F|G gap, up into the inter-row channel, across to
    # C, and up into C's bottom edge.
    y_channel = y_row2 + h2 + BANNER_H + INTER_ROWS * 0.45
    x_gap = at["F"].right + GAP_DISPLACED * 0.5
    e_f1 = ent[DISPLACEMENTS[0][0]]
    arrows.append(Arrow("displacement", e_f1.dim_id, DISPLACEMENTS[0][1],
                        [(at["F"].right + 0.01, e_f1.y), (x_gap, e_f1.y), (x_gap, y_channel),
                         (at[DISPLACEMENTS[0][1]].cx, y_channel),
                         (at[DISPLACEMENTS[0][1]].cx, y_row1 - 0.01)],
                        tag=f"clause ({DISPLACEMENTS[0][2]})",
                        tag_xy=((x_gap + at[DISPLACEMENTS[0][1]].cx) / 2, y_channel + 0.035)))

    # G4 -> F: a short horizontal hop across the widened F|G gap.
    e_g4 = ent[DISPLACEMENTS[1][0]]
    arrows.append(Arrow("displacement", e_g4.dim_id, DISPLACEMENTS[1][1],
                        [(at["G"].x - 0.01, e_g4.y), (at["F"].right + 0.015, e_g4.y)],
                        tag=f"({DISPLACEMENTS[1][2]})",
                        tag_xy=(x_gap, e_g4.y + 0.055)))

    return Layout(width=width, height=height, blocks=blocks, arrows=arrows, banners=banners,
                  note=note, schema_version=schema["schema_version"].split()[0])


# ----------------------------------------------------------------------------------------- render


def render(lay: Layout, out_stem: Path, exts: tuple[str, ...] = ("svg", "pdf"),
           dpi: int = 300) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

    fig, ax = plt.subplots(figsize=(lay.width, lay.height))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, lay.width)
    ax.set_ylim(0, lay.height)
    ax.set_aspect("equal")
    ax.axis("off")
    sans = {"family": "DejaVu Sans"}

    for b in lay.blocks:
        ax.add_patch(FancyBboxPatch(
            (b.x, b.y), b.w, b.h, boxstyle="round,pad=0.005,rounding_size=0.045",
            linewidth=1.0, edgecolor=INK, facecolor="white", zorder=2))
        ax.add_patch(Rectangle((b.x, b.top - b.title_h), b.w, b.title_h, linewidth=0,
                               facecolor=TITLE_FILL, zorder=2.1))
        ax.plot([b.x, b.right], [b.top - b.title_h] * 2, color=INK, linewidth=0.6, zorder=2.2)
        for i, line in enumerate(b.title_lines):
            ax.text(b.x + PAD_X, b.top - TITLE_PAD / 2 - (i + 0.5) * TITLE_LINE_H, line,
                    va="center", ha="left",
                    fontdict={**sans, "size": TITLE_FS, "weight": "bold"}, zorder=3)

        for e in b.entries:
            if e.multi:
                ax.add_patch(Rectangle((e.row_x0, e.y - ROW_H * 0.44),
                                       e.row_x1 - e.row_x0, ROW_H * 0.88,
                                       linewidth=0, facecolor=BAND_FILL, zorder=2.3))
            ax.text(e.x, e.y, e.label, va="center", ha="left",
                    fontdict={**sans, "size": ROW_FS}, zorder=3)
            ax.text(e.x_value, e.y, e.value_field, va="center", ha="right",
                    fontdict={**sans, "size": ROW_FS,
                              "style": "italic" if e.n_values is None else "normal"}, zorder=3)

    for x, y, text in lay.banners:
        ax.text(x + 0.01, y, text, va="bottom", ha="left",
                fontdict={**sans, "size": BANNER_FS, "style": "italic"}, zorder=3)

    for a in lay.arrows:
        dashed = a.kind == "displacement"
        pts = a.points
        if len(pts) > 2:
            ax.plot([p[0] for p in pts[:-1]], [p[1] for p in pts[:-1]], color=INK,
                    linewidth=0.8, linestyle=(0, (2.5, 1.5)) if dashed else "solid", zorder=2.6)
        ax.add_patch(FancyArrowPatch(
            pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=7, linewidth=0.8,
            color=INK, linestyle=(0, (2.5, 1.5)) if dashed else "solid",
            shrinkA=0, shrinkB=0, zorder=2.6))
        if a.tag and a.tag_xy:
            ax.text(a.tag_xy[0], a.tag_xy[1], a.tag, va="bottom", ha="center",
                    fontdict={**sans, "size": TAG_FS, "style": "italic"}, zorder=3,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6})

    y = MARGIN + (len(lay.note) - 1) * NOTE_H
    for line in lay.note:
        ax.text(MARGIN, y, line, va="bottom", ha="left",
                fontdict={**sans, "size": TAG_FS, "style": "italic"}, zorder=3)
        y -= NOTE_H

    out_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in exts:
        p = out_stem.with_suffix(f".{ext}")
        fig.savefig(p, format=ext, dpi=dpi)
        paths.append(p)
    plt.close(fig)
    return paths


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dimensions", default=str(REPO / "schema/dimensions.json"))
    p.add_argument("--out", default=str(REPO / "paper/figures/taxonomy_map"),
                   help="output stem (writes .svg and .pdf)")
    p.add_argument("--no-render", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    schema = load(Path(args.dimensions))
    problems = check_displacements(schema)
    for pr in problems:
        print("PROBLEM:", pr)
    if problems:
        print("refusing to draw an unsupported displacement arrow; fix DISPLACEMENTS or the schema")
        return 1
    lay = layout(schema)
    n_multi = sum(1 for e in lay.entries if e.multi)
    print(f"{len(lay.entries)} dimensions in {len(lay.blocks)} layers "
          f"({n_multi} multi-valued, {sum(1 for e in lay.entries if e.n_values is None)} non-enum); "
          f"figure {lay.width:.2f} x {lay.height:.2f} in")
    if args.no_render:
        return 0
    for path in render(lay, Path(args.out)):
        print("wrote", path, path.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
