"""The HARNESS-DB loader: one object holding systems, cells, results, papers and the schema."""

from __future__ import annotations

import difflib
import json
import os
import warnings
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from ._locate import Sources, locate
from ._stats import ratio_estimate
from .schema import Schema

CODED = "coded"
NOT_REPORTED = "not_reported"
UNRESOLVED = "unresolved"
#: The three cell states, in this order everywhere the loader reports them.
STATES: tuple[str, str, str] = (CODED, NOT_REPORTED, UNRESOLVED)

#: Frame size of each stratum (N_h), used only when neither the frame nor the release metadata
#: gives it. Taken from ``data/coding_frame.json`` (sampling frame of 6,504 systems).
DESIGN_STRATA: dict[str, float] = {"H": 984.0, "P": 683.0, "O": 4837.0}

_QUOTE_CHARS = ('"', "“", "'")
_STATE_DTYPE = pd.CategoricalDtype(list(STATES), ordered=False)
_CELL_COLUMNS = ["system_id", "layer", "dimension_key", "state", "value", "quote", "locator",
                 "confidence", "dimension_id", "multi", "evidence", "coder", "note",
                 "validation_flags"]


# ------------------------------------------------------------------------------ small helpers


def cell_state(cell: dict[str, Any]) -> str:
    """Map one raw cell to exactly one of ``coded``, ``not_reported``, ``unresolved``.

    ``unresolved`` wins over ``not_reported``; a cell with neither flag and no value is
    ``unresolved`` (nothing is invented for it). ``scripts/analyse_descriptives.py`` uses the
    same rule, so the loader's counts and the paper's agree.
    """
    if _truthy(cell.get("unresolved")):
        return UNRESOLVED
    if _truthy(cell.get("not_reported")):
        return NOT_REPORTED
    v = cell.get("value")
    if v is None or (isinstance(v, (list, str)) and len(v) == 0):
        return UNRESOLVED
    return CODED


def split_evidence(evidence: str | None) -> tuple[str | None, str | None]:
    """Split an evidence string into ``(quote, locator)``.

    Evidence is written as a verbatim quote followed by its locator in parentheses, e.g.
    ``'"max_turns=2" (README.md@e9bc1c2)'`` or ``'"we rate all the steps" (paper Sec. 3.2)'``.
    The locator is the last balanced parenthesised group at the end of the string (locators may
    contain parentheses themselves, e.g. ``README.md (Tools)@e23c462``). The quote loses its
    surrounding double quotes. A string that is neither quoted nor followed by a group is a bare
    locator (58 cells in the release, e.g. ``'README.md@585fe7c'``) and comes back as
    ``(None, locator)``; a quoted string with no group comes back as ``(quote, None)``. The raw
    string is always kept in ``cells.evidence``.
    """
    if evidence is None:
        return None, None
    s = str(evidence).strip()
    if not s:
        return None, None
    quote, locator = s, None
    if s.endswith(")"):
        depth = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ")":
                depth += 1
            elif s[i] == "(":
                depth -= 1
                if depth == 0:
                    if i > 0:
                        quote, locator = s[:i].strip(), s[i + 1:-1].strip() or None
                    break
    if locator is None and not s.startswith(_QUOTE_CHARS):
        return None, s
    for left, right in (('"', '"'), ("“", "”"), ("'", "'")):
        if len(quote) >= 2 and quote.startswith(left) and quote.endswith(right):
            quote = quote[1:-1].strip()
            break
    return (quote or None), locator


def _stratum_order(strata: dict[str, float]) -> list[str]:
    """H, P, O first (the design's order), anything else after, alphabetically."""
    known = [h for h in ("H", "P", "O") if h in strata]
    return known + sorted(h for h in strata if h not in known)


def _truthy(v: Any) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y", "t")
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return False
    return bool(v)


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        try:
            return pd.read_parquet(path)
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise ImportError(f"{path.name} is Parquet; install pyarrow "
                              "(pip install pyarrow)") from exc
    if path.suffix in (".jsonl", ".ndjson"):
        return pd.read_json(path, lines=True, dtype=False)
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".jsonl", ".ndjson"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("systems", data.get("data"))
    if not isinstance(data, list):
        raise TypeError(f"{path}: expected a list of systems")
    return data


def _parse_value(raw: Any, spec: dict[str, Any]) -> Any:
    """Coerce a tabular value back to the JSON shape: list for multi, int for integer dims."""
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    if isinstance(raw, (list, tuple, np.ndarray)):
        items = [str(x) for x in raw]
    elif isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        if s.startswith("["):
            try:
                items = [str(x) for x in json.loads(s)]
            except json.JSONDecodeError:
                items = [s]
        elif spec.get("multi"):
            items = [x.strip() for x in s.split("|") if x.strip()]
        else:
            items = [s]
    else:
        items = [raw]
    if spec.get("multi"):
        return list(items)
    v = items[0] if items else None
    if spec.get("type") == "integer" and v is not None:
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return v
    return v


def _list_field(raw: Any) -> list[str]:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return []
    if isinstance(raw, (list, tuple, np.ndarray)):
        return [str(x) for x in raw]
    s = str(raw).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            return [str(x) for x in json.loads(s)]
        except json.JSONDecodeError:
            pass
    sep = ";" if ";" in s else "|"
    return [x.strip() for x in s.split(sep) if x.strip()]


def _systems_from_tables(sys_df: pd.DataFrame, cells_df: pd.DataFrame,
                         schema: Schema) -> list[dict[str, Any]]:
    """Rebuild the nested ``systems.json`` shape from a tabular (systems + cells) release."""
    id_col = "system_id" if "system_id" in sys_df.columns else "id"
    key_col = next(c for c in ("dimension_key", "key", "dimension") if c in cells_df.columns)
    systems: dict[str, dict[str, Any]] = {}
    for rec in sys_df.to_dict("records"):
        sid = str(rec[id_col])
        urls = rec.get("urls")
        if isinstance(urls, str) and urls.strip().startswith("{"):
            urls = json.loads(urls)
        if not isinstance(urls, dict):
            urls = {"repo": rec["repo_url"]} if rec.get("repo_url") else {}
        s: dict[str, Any] = {
            "id": sid, "name": rec.get("name"),
            "papers": _list_field(rec.get("papers", rec.get("paper_ids"))),
            "version_label": rec.get("version_label") or rec.get("version") or None, "urls": urls,
            "coded_at": rec.get("coded_at") or None, "notes": rec.get("notes") or None,
            "aliases": _list_field(rec.get("aliases")), "coding": {},
        }
        for extra in ("stratum", "weight"):
            if extra in rec and rec[extra] not in (None, ""):
                s[extra] = rec[extra]
        systems[sid] = s
    for rec in cells_df.to_dict("records"):
        sid = str(rec["system_id"])
        key = schema.key(str(rec[key_col]))
        spec = schema.dimension(key)
        state = str(rec.get("state") or "").strip()
        if state == "value":  # the release's cells.csv calls the coded state "value"
            state = CODED
        cell: dict[str, Any] = {
            "value": _parse_value(rec.get("value"), spec),
            "not_reported": state == NOT_REPORTED if state else _truthy(rec.get("not_reported")),
            "confidence": rec.get("confidence") or None,
            "coder": rec.get("coder") or None,
            "note": rec.get("note") or None,
        }
        if (state == UNRESOLVED) or (not state and _truthy(rec.get("unresolved"))):
            cell["unresolved"] = True
        quote = rec.get("quote", rec.get("evidence_quote")) or None
        locator = rec.get("locator", rec.get("evidence_locator")) or None
        if rec.get("evidence"):
            cell["evidence"] = rec["evidence"]
        elif quote or locator:
            cell["evidence"] = (f'"{quote}" ({locator})' if quote and locator
                                else (f'"{quote}"' if quote else locator))
        if quote or locator:
            cell["_quote"], cell["_locator"] = quote, locator
        if rec.get("flags"):
            cell["flags"] = rec["flags"]
        systems.setdefault(sid, {"id": sid, "name": sid, "papers": [], "coding": {}})
        systems[sid]["coding"][key] = cell
    return list(systems.values())


# --------------------------------------------------------------------------------- result types


@dataclass(frozen=True)
class Evidence:
    """What one cell says and where it says it.

    ``value`` is ``None`` whenever ``state`` is not ``coded``: a ``not_reported`` cell records
    documented silence, not an absent feature, and the loader never turns it into a value.
    """

    system_id: str
    name: str
    dimension_key: str
    dimension_id: str
    layer: str
    state: str
    value: Any
    quote: str | None
    locator: str | None
    confidence: str | None
    evidence: str | None
    note: str | None
    coder: str | None

    def __str__(self) -> str:
        head = f"{self.name} [{self.system_id}] / {self.dimension_id} {self.dimension_key}"
        lines = [head, f"  state:      {self.state}"]
        if self.state == CODED:
            lines.append(f"  value:      {self.value!r}")
        lines.append(f"  confidence: {self.confidence}")
        if self.quote:
            lines.append(f"  quote:      {self.quote}")
        if self.locator:
            lines.append(f"  locator:    {self.locator}")
        if self.note:
            lines.append(f"  note:       {self.note}")
        return "\n".join(lines)


@dataclass
class DimensionSummary:
    """The value distribution of one dimension, with its reporting counts.

    ``table`` has one row per value: ``n_systems`` and ``share_unweighted`` over the ``n_coded``
    systems whose cell is coded; ``weight_systems``, ``share_weighted`` and ``se_weighted`` over
    the weight-bearing coded systems only. ``not_reported`` and ``unresolved`` cells are in no
    share's denominator. For a multi-valued dimension a system counts once for every value it
    uses, so shares are "share of systems using X" and can sum past 1. Enum dimensions list every
    allowed value in schema order (zeros included); integer, date and string dimensions list the
    observed values, most frequent first.
    """

    dimension_key: str
    dimension_id: str
    layer: str
    type: str
    multi: bool
    n_systems: int
    n_coded: int
    n_not_reported: int
    n_unresolved: int
    not_reported_rate: float
    not_reported_rate_weighted: float
    not_reported_se_weighted: float
    table: pd.DataFrame = field(repr=False)

    def __str__(self) -> str:
        head = (f"{self.dimension_id} {self.dimension_key} (layer {self.layer}, {self.type}"
                f"{', multi-valued' if self.multi else ''}): {self.n_systems} systems = "
                f"{self.n_coded} coded + {self.n_not_reported} not_reported + "
                f"{self.n_unresolved} unresolved\n"
                f"not_reported rate (unresolved excluded): {self.not_reported_rate:.1%} "
                f"unweighted, {self.not_reported_rate_weighted:.1%} weighted "
                f"(SE {100 * self.not_reported_se_weighted:.1f} pts)")
        return head + "\n" + self.table.to_string(index=False)


# ---------------------------------------------------------------------------------- the loader


class HarnessDB:
    """HARNESS-DB in memory. Build it with :func:`harnessdb.load`.

    Three rules hold for everything this object computes:

    1. ``not_reported`` is documented silence, never absence. A ``not_reported`` cell has
       ``value = None``; the loader never maps it to a value (in particular not to the schema's
       ``"none"``, which is a coded finding that the harness has no such mechanism).
    2. ``unresolved`` cells (163 in the release: cells that failed validation) are excluded from
       every rate the loader computes, numerator and denominator alike. They are still listed in
       ``cells`` and counted in ``n_unresolved`` columns.
    3. Weighted estimates use only weight-bearing systems. The 23 systems coded outside the drawn
       sample have ``weight = 0`` and are out-of-sample: they appear in every unweighted number
       and in no weighted number or design SE.

    Attributes
    ----------
    systems : DataFrame
        One row per released system: ``system_id, name, version_label, repo_url, aliases,
        papers, coded_at, notes, stratum, weight, weight_bearing, n_coded, n_not_reported,
        n_unresolved``. ``papers`` and ``aliases`` are lists.
    cells : DataFrame
        Long form, one row per system x dimension (1,256 x 38 = 47,728): ``system_id, layer,
        dimension_key, state, value, quote, locator, confidence`` then ``dimension_id, multi,
        evidence, coder, note, validation_flags``. ``state`` is categorical over
        ``coded / not_reported / unresolved``. ``value`` is a Python list for multi-valued
        dimensions, an ``int`` for ``tool_count`` and ``stars``, a string otherwise, and ``None``
        unless ``state == "coded"``.
        ``evidence`` is the raw string; ``quote`` and ``locator`` are split from it.
        ``validation_flags`` holds the release build's reasons a cell is ``unresolved``
        (``"quote_not_in_bundle|locator_no_line"``) when the source is a release whose
        ``cells.csv`` carries them, and is ``None`` otherwise.
    results : DataFrame
        Reported scores (``data/results.csv``); ``score``, ``cost_usd`` and ``tokens`` numeric.
    papers : DataFrame
        Bibliographic rows. In a checkout, ``data/papers.csv``: included and excluded, with a
        boolean ``included``. In a release, the included papers only, with ``system_ids``.
    schema : Schema
        The parsed ``dimensions.json``.
    strata_sizes : dict
        Frame size N_h of each stratum, used by the design SEs.
    source : Sources
        Where each input was read from.
    """

    def __init__(self, systems_raw: list[dict[str, Any]], schema: Schema, *, source: Sources,
                 frame: pd.DataFrame | None, strata_sizes: dict[str, float],
                 results: pd.DataFrame, papers: pd.DataFrame):
        self.schema = schema
        self.source = source
        self.strata_sizes = dict(strata_sizes)
        self._raw = {s["id"]: s for s in systems_raw}
        self.cells = self._build_cells(systems_raw)
        self.systems = self._build_systems(systems_raw, frame)
        w = self.systems.set_index("system_id")["weight"]
        st = self.systems.set_index("system_id")["stratum"]
        self._cw = self.cells["system_id"].map(w).to_numpy(dtype=float)
        self._cs = self.cells["system_id"].map(st).to_numpy(dtype=object)
        self.results = results
        self.papers = papers

    # ----------------------------------------------------------------------------- construction
    def _build_cells(self, systems_raw: list[dict[str, Any]]) -> pd.DataFrame:
        specs = self.schema["dimensions"]
        rows: list[tuple[Any, ...]] = []
        for s in systems_raw:
            coding = s.get("coding") or {}
            unknown = set(coding) - {d["key"] for d in specs}
            if unknown:
                warnings.warn(f"{s['id']}: cells for dimensions not in the schema ignored: "
                              f"{sorted(unknown)}", stacklevel=3)
            for spec in specs:
                cell = coding.get(spec["key"]) or {}
                state = cell_state(cell)
                value = cell.get("value") if state == CODED else None  # rule 1
                if value is not None and spec.get("multi") and not isinstance(value, list):
                    value = [value]
                ev = cell.get("evidence") or None
                if "_quote" in cell or "_locator" in cell:
                    quote, locator = cell.get("_quote"), cell.get("_locator")
                else:
                    quote, locator = split_evidence(ev)
                rows.append((s["id"], spec["layer"], spec["key"], state, value, quote, locator,
                             cell.get("confidence") or None, spec["id"], bool(spec.get("multi")),
                             ev, cell.get("coder") or None, cell.get("note") or None,
                             cell.get("flags") or None))
        df = pd.DataFrame.from_records(rows, columns=_CELL_COLUMNS)
        df["state"] = df["state"].astype(_STATE_DTYPE)
        return df

    def _build_systems(self, systems_raw: list[dict[str, Any]],
                       frame: pd.DataFrame | None) -> pd.DataFrame:
        fmap: dict[str, dict[str, Any]] = {}
        if frame is not None and len(frame):
            id_col = "system_id" if "system_id" in frame.columns else "id"
            fmap = {str(r[id_col]): r for r in frame.to_dict("records")}
        counts = (self.cells.groupby(["system_id", "state"], observed=False).size()
                  .unstack(fill_value=0))
        rows = []
        missing: list[str] = []
        for s in systems_raw:
            sid = s["id"]
            fr = fmap.get(sid, {})
            stratum = s.get("stratum", fr.get("stratum"))
            weight = s.get("weight", fr.get("weight"))
            if stratum in (None, "") or weight in (None, ""):
                missing.append(sid)
            try:
                wf = float(weight) if weight not in (None, "") else 0.0
            except (TypeError, ValueError):
                wf = 0.0
            urls = s.get("urls") or {}
            rows.append({
                "system_id": sid, "name": s.get("name"),
                "version_label": s.get("version_label"),
                "repo_url": urls.get("repo") if isinstance(urls, dict) else None,
                "aliases": list(s.get("aliases") or []), "papers": list(s.get("papers") or []),
                "coded_at": s.get("coded_at"), "notes": s.get("notes"),
                "stratum": (str(stratum) if stratum not in (None, "") else None),
                "weight": wf, "weight_bearing": wf > 0,
                "n_coded": int(counts.at[sid, CODED]),
                "n_not_reported": int(counts.at[sid, NOT_REPORTED]),
                "n_unresolved": int(counts.at[sid, UNRESOLVED]),
            })
        if missing:
            warnings.warn(f"{len(missing)} systems have no stratum/weight in the frame and are "
                          f"treated as weight 0 (out-of-sample): {missing[:5]}...", stacklevel=3)
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------------------ public API
    def __repr__(self) -> str:
        st = self.cells["state"].value_counts()
        wb = self.systems["weight_bearing"]
        return (f"HarnessDB({len(self.systems):,} systems, {len(self.cells):,} cells: "
                f"{st.get(CODED, 0):,} coded / {st.get(NOT_REPORTED, 0):,} not_reported / "
                f"{st.get(UNRESOLVED, 0):,} unresolved; {int(wb.sum()):,} weight-bearing; "
                f"source={self.source.kind}:{self.source.root})")

    def wide(self, multi: Literal["join", "list"] = "join", sep: str = "|") -> pd.DataFrame:
        """One row per system: ``system_id, name, stratum, weight``, one value column per
        dimension (schema order), then one ``<key>__state`` column per dimension.

        Value columns hold the coded value, and ``None``/``<NA>`` wherever the state is
        ``not_reported`` or ``unresolved`` (check the ``__state`` column to tell them apart;
        rule 1: a missing value is never "absent"). Multi-valued dimensions are pipe-joined
        strings by default (``"react|plan_execute"``, values in the dataset's sorted order);
        pass ``multi="list"`` to keep Python lists. ``tool_count`` and ``stars`` are ``Int64``.
        """
        if multi not in ("join", "list"):
            raise ValueError("multi must be 'join' or 'list'")
        keys = self.schema.keys_in_order
        vals = self.cells["value"]
        if multi == "join":
            vals = vals.map(lambda v: sep.join(map(str, v)) if isinstance(v, list) else v)
        idx = pd.MultiIndex.from_arrays([self.cells["system_id"], self.cells["dimension_key"]])
        v = pd.Series(vals.to_numpy(dtype=object), index=idx).unstack()
        s = pd.Series(self.cells["state"].astype(str).to_numpy(), index=idx).unstack()
        order = self.systems["system_id"]
        v = v.reindex(index=order, columns=keys)
        s = s.reindex(index=order, columns=keys).add_suffix("__state")
        for k in keys:
            if self.schema.type(k) == "integer":
                v[k] = pd.array([None if x is None or x is pd.NA else int(x) for x in v[k]],
                                dtype="Int64")
            else:
                v[k] = v[k].astype(object).where(v[k].notna(), None)
        head = self.systems.set_index("system_id")[["name", "stratum", "weight"]]
        out = pd.concat([head, v, s], axis=1)
        out.index.name = "system_id"
        return out.reset_index()

    def dimension(self, key: str) -> DimensionSummary:
        """Value distribution of one dimension, unweighted and weighted, plus reporting counts.

        Accepts a key (``"self_verification"``) or an id (``"E1"``). Shares are over the systems
        whose cell is ``coded``: ``not_reported`` is never a value (rule 1) and ``unresolved`` is
        excluded (rule 2). Weighted shares use only weight-bearing systems (rule 3); their SE is the
        stratified design SE. See :class:`DimensionSummary`.
        """
        spec = self.schema.dimension(key)
        key = spec["key"]
        mask = (self.cells["dimension_key"] == key).to_numpy()
        sub = self.cells[mask]
        w, st = self._cw[mask], self._cs[mask]
        state = sub["state"].astype(str).to_numpy()
        coded = state == CODED
        n_nr = int((state == NOT_REPORTED).sum())
        n_un = int((state == UNRESOLVED).sum())
        base = state != UNRESOLVED
        nr_flag = (state == NOT_REPORTED).astype(float)
        nr_w, nr_se, _, _ = ratio_estimate(nr_flag[base], np.ones(base.sum()), w[base], st[base],
                                           self.strata_sizes)
        cvals = list(sub["value"].to_numpy()[coded])
        cw, cst = w[coded], st[coded]
        sets = [set(v) if isinstance(v, list) else {v} for v in cvals]
        if spec["type"] == "enum":
            order = list(spec.get("values") or [])
            extra = sorted({x for s in sets for x in s} - set(order), key=str)
            order += extra
        else:
            order = [x for x, _ in Counter(x for s in sets for x in s).most_common()]
        n_coded = len(cvals)
        rows = []
        for val in order:
            flag = np.array([val in s for s in sets], dtype=float)
            rate_w, se_w, _, _ = ratio_estimate(flag, np.ones(n_coded), cw, cst, self.strata_sizes)
            rows.append({"value": val, "n_systems": int(flag.sum()),
                         "share_unweighted": flag.sum() / n_coded if n_coded else float("nan"),
                         "weight_systems": float((cw * flag).sum()),
                         "share_weighted": rate_w, "se_weighted": se_w})
        table = pd.DataFrame(rows, columns=["value", "n_systems", "share_unweighted",
                                            "weight_systems", "share_weighted", "se_weighted"])
        return DimensionSummary(
            dimension_key=key, dimension_id=spec["id"], layer=spec["layer"], type=spec["type"],
            multi=bool(spec.get("multi")), n_systems=len(sub), n_coded=n_coded,
            n_not_reported=n_nr, n_unresolved=n_un,
            not_reported_rate=float(nr_flag[base].mean()) if base.any() else float("nan"),
            not_reported_rate_weighted=nr_w, not_reported_se_weighted=nr_se, table=table)

    def not_reported(self, by: Literal["layer", "dimension", "stratum"] | None = "layer"
                     ) -> pd.DataFrame:
        """Under-reporting rates: the share of cells that are ``not_reported``.

        ``by`` is ``"layer"`` (default), ``"dimension"``, ``"stratum"`` or ``None`` (overall).
        The base excludes ``unresolved`` cells (rule 2); ``n_unresolved`` shows how many were
        dropped. ``rate_unweighted`` pools every released system's cells. ``rate_weighted`` is the
        field estimate, sum(w * not_reported) / sum(w) over the base cells of weight-bearing
        systems only (rule 3; the 23 weight-0 systems add nothing).

        ``se_weighted`` is the stratified design SE with systems as clusters (Taylor
        linearisation of the ratio, finite-population correction on systems; see
        :mod:`harnessdb._stats`), the estimator the manuscript uses. The numbers equal
        ``data/analysis/under_reporting_by_dimension.csv`` (by dimension) and
        ``data/analysis/summary_one_screen.csv`` (by layer).
        """
        if by not in ("layer", "dimension", "stratum", None):
            raise ValueError("by must be 'layer', 'dimension', 'stratum' or None")
        c = self.cells
        state = c["state"].astype(str).to_numpy()
        frame = pd.DataFrame({
            "system_id": c["system_id"].to_numpy(), "layer": c["layer"].to_numpy(),
            "dimension_key": c["dimension_key"].to_numpy(),
            "stratum": self._cs, "weight": self._cw,
            "base": (state != UNRESOLVED).astype(int), "nr": (state == NOT_REPORTED).astype(int),
            "unres": (state == UNRESOLVED).astype(int),
        })
        if by is None:
            groups: list[tuple[Any, pd.DataFrame]] = [("all", frame)]
        else:
            col = {"layer": "layer", "dimension": "dimension_key", "stratum": "stratum"}[by]
            if by == "layer":
                order = list(self.schema.layers)
            elif by == "dimension":
                order = self.schema.keys_in_order
            else:
                present = {str(h) for h in frame["stratum"].dropna().unique()}
                order = _stratum_order(dict.fromkeys(present, 0.0))
            g = dict(tuple(frame.groupby(col, sort=False)))
            groups = [(k, g[k]) for k in order if k in g]
        rows = []
        for gkey, grp in groups:
            per = grp.groupby("system_id", sort=False).agg(
                base=("base", "sum"), nr=("nr", "sum"), weight=("weight", "first"),
                stratum=("stratum", "first"))
            rate_w, se_w, wbase, n_w = ratio_estimate(
                per["nr"].to_numpy(), per["base"].to_numpy(), per["weight"].to_numpy(),
                per["stratum"].to_numpy(dtype=object), self.strata_sizes)
            n_base = int(grp["base"].sum())
            row: dict[str, Any] = {}
            if by == "layer":
                row = {"layer": gkey, "layer_name": self.schema.layers.get(gkey, gkey)}
            elif by == "dimension":
                spec = self.schema.dimension(gkey)
                row = {"layer": spec["layer"], "dimension_id": spec["id"], "dimension_key": gkey}
            elif by == "stratum":
                row = {"stratum": gkey}
            row.update({
                "n_systems": int(per.shape[0]), "n_cells": len(grp),
                "n_unresolved": int(grp["unres"].sum()), "n_base": n_base,
                "n_not_reported": int(grp["nr"].sum()),
                "rate_unweighted": grp["nr"].sum() / n_base if n_base else float("nan"),
                "n_weight_bearing": n_w, "weight_base": wbase,
                "rate_weighted": rate_w, "se_weighted": se_w,
            })
            rows.append(row)
        return pd.DataFrame(rows)

    def _resolve_system(self, system: str) -> str:
        if system in self._raw:
            return system
        low = system.strip().lower()
        for sid in self._raw:
            if sid.lower() == low:
                return sid
        hits = [sid for sid, s in self._raw.items()
                if str(s.get("name", "")).lower() == low
                or low in (a.lower() for a in (s.get("aliases") or []))]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise KeyError(f"{system!r} names several systems: {hits}; pass a system_id")
        close = difflib.get_close_matches(low, list(self._raw), n=5, cutoff=0.6)
        raise KeyError(f"no system {system!r}" + (f"; did you mean {close}?" if close else ""))

    def evidence(self, system: str, dimension: str | None = None) -> Evidence | pd.DataFrame:
        """The quote and locator behind one cell, or behind all 38 cells of one system.

        ``system`` is a ``system_id`` (``"openhands"``) or, failing that, an exact name or alias.
        With a ``dimension`` (key or id) it returns an :class:`Evidence`; without one, a DataFrame
        of that system's cells in schema order. A ``not_reported`` cell may still carry a quote:
        the evidence for the silence (e.g. the passage that stops short of saying).
        """
        sid = self._resolve_system(system)
        rows = self.cells[self.cells["system_id"] == sid]
        if dimension is None:
            return rows.reset_index(drop=True)
        key = self.schema.key(dimension)
        r = rows[rows["dimension_key"] == key].iloc[0]
        return Evidence(system_id=sid, name=str(self._raw[sid].get("name") or sid),
                        dimension_key=key, dimension_id=r["dimension_id"], layer=r["layer"],
                        state=str(r["state"]), value=r["value"], quote=r["quote"],
                        locator=r["locator"], confidence=r["confidence"], evidence=r["evidence"],
                        note=r["note"], coder=r["coder"])

    def _arrow_frames(self) -> dict[str, pd.DataFrame]:
        """``systems`` and ``cells`` with Arrow-safe column types (used by :meth:`to_hf`).

        ``value`` becomes a list of strings for every dimension (a single value is a 1-element
        list; integers become their decimal string) and stays null for ``not_reported`` and
        ``unresolved`` cells, so an empty list is never confused with silence.
        """
        cells = self.cells.copy()
        cells["state"] = cells["state"].astype(str)
        cells["value"] = [None if v is None else ([str(x) for x in v] if isinstance(v, list)
                                                  else [str(v)]) for v in cells["value"]]
        systems = self.systems.copy()
        return {"systems": systems, "cells": cells}

    def to_hf(self) -> Any:
        """A ``datasets.DatasetDict`` with two splits, ``systems`` and ``cells``.

        Needs the ``hf`` extra (``pip install 'harness-db[hf]'``). In the ``cells`` split,
        ``value`` is ``list<string>`` for every dimension (null unless ``state == "coded"``);
        ``stratum`` and ``weight`` live in the ``systems`` split, joinable on ``system_id``.
        """
        try:
            import datasets
        except ImportError as exc:
            raise ImportError("to_hf() needs the Hugging Face 'datasets' package: "
                              "pip install 'harness-db[hf]'") from exc
        frames = self._arrow_frames()
        str_ = datasets.Value("string")
        seq = datasets.Sequence(str_)
        sys_features = datasets.Features({
            "system_id": str_, "name": str_, "version_label": str_, "repo_url": str_,
            "aliases": seq, "papers": seq, "coded_at": str_, "notes": str_, "stratum": str_,
            "weight": datasets.Value("float64"), "weight_bearing": datasets.Value("bool"),
            "n_coded": datasets.Value("int64"), "n_not_reported": datasets.Value("int64"),
            "n_unresolved": datasets.Value("int64"),
        })
        cell_features = datasets.Features({
            "system_id": str_, "layer": str_, "dimension_key": str_, "state": str_,
            "value": seq, "quote": str_, "locator": str_, "confidence": str_,
            "dimension_id": str_, "multi": datasets.Value("bool"), "evidence": str_,
            "coder": str_, "note": str_, "validation_flags": str_,
        })
        stamp = self._fingerprint()

        def build(split: str, features: Any) -> Any:
            # Build from Arrow with an explicit fingerprint: ``Dataset.from_pandas`` would hash
            # the whole table to make one, which is slow and fails under some dill/pyarrow pairs.
            import pyarrow as pa
            table = pa.Table.from_pandas(frames[split], schema=features.arrow_schema,
                                         preserve_index=False)
            return datasets.Dataset(datasets.table.InMemoryTable(table),
                                    info=datasets.DatasetInfo(features=features),
                                    fingerprint=f"{stamp}-{split}")

        return datasets.DatasetDict({"systems": build("systems", sys_features),
                                     "cells": build("cells", cell_features)})

    def _fingerprint(self) -> str:
        """A short, stable id of the loaded data (loader version + source files' sizes/mtimes)."""
        import hashlib

        from . import __version__
        parts = [__version__, self.source.kind]
        for p in (self.source.systems, self.source.cells, self.source.schema, self.source.frame):
            if p is not None and p.is_file():
                st = p.stat()
                parts.append(f"{p.name}:{st.st_size}:{int(st.st_mtime)}")
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]

    def summary(self) -> dict[str, Any]:
        """The headline counts, as a dict (what ``python -m harnessdb --summary`` prints).

        Only counts the manuscript states, so a reader can check them one for one: systems,
        cells and the three cell states, the strata, the frame, the weight-bearing and weight-0
        systems, and the size of the results table. No estimate is included; use
        :meth:`not_reported` and :meth:`dimension` for those.
        """
        st = self.cells["state"].value_counts()
        res = self.results
        order = _stratum_order(self.strata_sizes)
        return {
            "source": f"{self.source.kind}:{self.source.root}",
            "schema_version": self.schema.version,
            "layers": len(self.schema.layers), "dimensions": len(self.schema.keys_in_order),
            "systems": len(self.systems), "cells": len(self.cells),
            "coded": int(st.get(CODED, 0)), "not_reported": int(st.get(NOT_REPORTED, 0)),
            "unresolved": int(st.get(UNRESOLVED, 0)),
            "strata": {k: int(v) for k, v in self.systems["stratum"].value_counts()
                       .reindex(order, fill_value=0).items()},
            "frame_size": int(sum(self.strata_sizes.values())),
            "strata_sizes": {k: int(self.strata_sizes[k]) for k in order},
            "weight_bearing_systems": int(self.systems["weight_bearing"].sum()),
            "weight_zero_systems": int((~self.systems["weight_bearing"]).sum()),
            "results_rows": len(res),
            "results_systems": int(res["system_id"].nunique()) if "system_id" in res else 0,
            "results_benchmarks": int(res["benchmark"].nunique()) if "benchmark" in res else 0,
        }


# ---------------------------------------------------------------------------------- load()


def _attach_flags(systems_raw: list[dict[str, Any]], cells_df: pd.DataFrame,
                  schema: Schema) -> None:
    """Copy a release cells table's validation ``flags`` onto the nested cells (in place)."""
    if "flags" not in cells_df.columns or "system_id" not in cells_df.columns:
        return
    key_col = next((c for c in ("dimension_key", "key", "dimension") if c in cells_df.columns),
                   None)
    if key_col is None:
        return
    by_id = {s["id"]: s for s in systems_raw}
    flagged = cells_df[cells_df["flags"].astype(str).str.strip().ne("")
                       & cells_df["flags"].notna()]
    for sid, key, flags in zip(flagged["system_id"], flagged[key_col], flagged["flags"],
                               strict=True):
        s = by_id.get(str(sid))
        if s is None:
            continue
        cell = (s.get("coding") or {}).get(schema.key(str(key)))
        if cell is not None:
            cell["flags"] = str(flags)


def _strata_from_meta(obj: Any, depth: int = 0) -> dict[str, float] | None:
    """Find a ``strata`` mapping ({h: N_h} or {h: {"size": N_h}}) anywhere in a JSON object."""
    if depth > 4 or not isinstance(obj, dict):
        return None
    st = obj.get("strata")
    if isinstance(st, dict) and st:
        out: dict[str, float] = {}
        for h, v in st.items():
            size = v.get("size", v.get("N")) if isinstance(v, dict) else v
            if isinstance(size, (int, float)):
                out[str(h)] = float(size)
        if out:
            return out
    for v in obj.values():
        hit = _strata_from_meta(v, depth + 1)
        if hit:
            return hit
    return None


def _strata_sizes(src: Sources, frame: pd.DataFrame | None, n_released: int) -> dict[str, float]:
    """N_h per stratum: the full frame's row counts, else release metadata, else the design."""
    if frame is not None and "stratum" in frame.columns and len(frame) > n_released:
        return {str(k): float(v) for k, v in frame["stratum"].value_counts().items()}
    hit = _strata_from_meta(src.meta)
    if hit:
        return hit
    if src.frame_summary is not None and src.frame_summary.is_file():
        hit = _strata_from_meta(json.loads(src.frame_summary.read_text(encoding="utf-8")))
        if hit:
            return hit
    # A release that ships only the released systems (``systems_wide.csv``) cannot give N_h;
    # the design's frame sizes are then the right ones, as long as the strata are the design's.
    labels = set() if frame is None or "stratum" not in frame.columns else {
        str(x) for x in frame["stratum"] if str(x).strip()}
    if not labels <= set(DESIGN_STRATA):
        warnings.warn(f"stratum sizes not found for strata {sorted(labels)}; using the published "
                      f"design {DESIGN_STRATA}, so design SEs may be wrong", stacklevel=3)
    return dict(DESIGN_STRATA)


def _results(path: Path | None) -> pd.DataFrame:
    if path is None or not path.is_file():
        return pd.DataFrame(columns=["system_id", "model", "benchmark", "split", "metric",
                                     "score", "cost_usd", "tokens", "date", "source_url",
                                     "comparable_key", "notes"])
    df = _read_table(path)
    for col in ("score", "cost_usd", "tokens"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace("", None), errors="coerce")
    return df


def _papers(path: Path | None) -> pd.DataFrame:
    if path is None or not path.is_file():
        return pd.DataFrame(columns=["id", "title", "authors", "year", "venue", "arxiv_id",
                                     "doi", "url", "source", "included", "exclusion_reason"])
    df = _read_table(path)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"].replace("", None), errors="coerce").astype("Int64")
    if "included" in df.columns:
        df["included"] = df["included"].map(_truthy).astype(bool)
    return df


def load(path: str | os.PathLike[str] | None = None) -> HarnessDB:
    """Load HARNESS-DB.

    ``path`` may be a repository root, its ``data/`` directory, a release directory, or a
    release's ``datapackage.json``. Without a path the loader tries ``$HARNESSDB_DATA``, then the
    current directory and its parents, then the package's own location (an editable install in
    the repository). A release is read through its ``datapackage.json``; its systems may be the
    nested ``systems.json``/``.jsonl`` or a tabular ``systems`` + ``cells`` pair (CSV or Parquet).

    Rules: ``not_reported`` is documented silence and never becomes a value; ``unresolved`` is
    excluded from every rate; weighted estimates use only weight-bearing systems (the 23 systems
    at weight 0 are out-of-sample). See :class:`HarnessDB`.
    """
    src = locate(path)
    schema = Schema(json.loads(src.schema.read_text(encoding="utf-8")))
    if src.systems.suffix in (".csv", ".parquet"):
        assert src.cells is not None
        systems_raw = _systems_from_tables(_read_table(src.systems), _read_table(src.cells),
                                           schema)
    else:
        systems_raw = _load_json_records(src.systems)
        if src.cells is not None and src.cells.is_file():
            _attach_flags(systems_raw, _read_table(src.cells), schema)
    ids = [s["id"] for s in systems_raw]
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    if dupes:
        raise ValueError(f"duplicate system ids in {src.systems}: {dupes[:5]}")
    frame_path = src.frame or src.systems_wide  # a release carries stratum/weight in systems_wide
    frame = _read_table(frame_path) if frame_path is not None and frame_path.is_file() else None
    strata = _strata_sizes(src, frame, len(systems_raw))
    return HarnessDB(systems_raw, schema, source=src, frame=frame, strata_sizes=strata,
                     results=_results(src.results), papers=_papers(src.papers))
