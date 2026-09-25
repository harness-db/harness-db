"""The HARNESS-DB query tools, as plain functions over the loaded release.

Every function returns a JSON-serialisable dict, so the tests (and any Python caller) can use them
without an MCP client; ``server.py`` registers the same functions as MCP tools. Bad input never
raises: it comes back as ``{"error": ..., "hint": ...}`` so an agent can correct its call.

Every response that contains a ``not_reported`` cell, or a ``not_reported`` count above zero,
carries the three-state rule once, in a top-level ``note`` field.
"""

from __future__ import annotations

import math
import re
from bisect import bisect_right
from typing import Any

from .db import (
    STATE_CODED,
    STATE_NOT_REPORTED,
    STATE_UNRESOLVED,
    STATES,
    THREE_STATE_RULE,
    HarnessDB,
    cell_state,
    cell_values,
    split_evidence,
)

MAX_COMPARE = 6
MAX_LIMIT = 200

_DB: HarnessDB | None = None


def get_db() -> HarnessDB:
    """The process-wide release, loaded on first use."""
    global _DB
    if _DB is None:
        _DB = HarnessDB.load()
    return _DB


def set_db(db: HarnessDB | None) -> None:
    """Replace the process-wide release (``None`` forces a reload on next use)."""
    global _DB
    _DB = db


# ------------------------------------------------------------------------------ shared helpers


def _error(message: str, **extra: Any) -> dict[str, Any]:
    return {"error": message, **extra}


def _with_note(resp: dict[str, Any], has_not_reported: bool) -> dict[str, Any]:
    """Attach the three-state rule once, at the top of the response, when silence is present."""
    if has_not_reported:
        return {"note": THREE_STATE_RULE, **resp}
    return resp


def _r(x: float | None, nd: int = 4) -> float | None:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return round(float(x), nd)


def _unknown_dimension(db: HarnessDB, ident: Any) -> dict[str, Any]:
    return _error(f"Unknown dimension {ident!r}.",
                  hint="Use a dimension key such as 'network_policy' or an id such as 'G3'. "
                       "Call describe_schema() for the full list.",
                  valid_dimensions=[d["key"] for d in db.dims])


def _unknown_system(db: HarnessDB, ident: Any) -> dict[str, Any]:
    return _error(f"Unknown system id {ident!r}.",
                  hint="Use search_systems(query=...) to find the id.",
                  did_you_mean=db.suggest_systems(str(ident)))


def _dim_ref(spec: dict) -> dict[str, Any]:
    return {"key": spec["key"], "id": spec["id"], "name": spec["name"], "layer": spec["layer"],
            "type": spec["type"], "multi": bool(spec.get("multi"))}


def _value_out(spec: dict, cell: dict) -> Any:
    if cell_state(cell) != STATE_CODED:
        return None
    return cell.get("value")


def _full_cell(db: HarnessDB, spec: dict, cell: dict | None) -> dict[str, Any]:
    """One cell with everything behind it: value, state, quote, locator, confidence."""
    cell = cell or {}
    state = cell_state(cell)
    quote, locator = split_evidence(cell.get("evidence"))
    return {
        "dimension": spec["key"],
        "dimension_id": spec["id"],
        "dimension_name": spec["name"],
        "layer": spec["layer"],
        "state": state,
        "value": _value_out(spec, cell),
        "confidence": cell.get("confidence"),
        "quote": quote,
        "locator": locator,
        "coder": cell.get("coder"),
        "coder_note": cell.get("note"),
    }


def _compact_cell(spec: dict, cell: dict | None) -> dict[str, Any]:
    cell = cell or {}
    return {"dimension": spec["key"], "state": cell_state(cell), "value": _value_out(spec, cell),
            "confidence": cell.get("confidence")}


def _state_counts(system: dict, specs: list[dict]) -> dict[str, int]:
    counts = dict.fromkeys(STATES, 0)
    for spec in specs:
        counts[cell_state(system["coding"].get(spec["key"]))] += 1
    return counts


def _system_header(db: HarnessDB, system: dict) -> dict[str, Any]:
    stars_cell = system["coding"].get("stars") or {}
    return {
        "id": system["id"],
        "name": system.get("name"),
        "aliases": system.get("aliases") or [],
        "repo": (system.get("urls") or {}).get("repo"),
        "version_label": system.get("version_label"),
        "stratum": db.stratum(system["id"]),
        "weight": db.weight(system["id"]) if db.has_weights else None,
        "stars": stars_cell.get("value") if cell_state(stars_cell) == STATE_CODED else None,
    }


def _normalise_state(state: str | None) -> str | None:
    if state is None:
        return None
    s = str(state).strip().lower().replace("-", "_").replace(" ", "_")
    return {"value": STATE_CODED, "valued": STATE_CODED, "reported": STATE_CODED,
            "silent": STATE_NOT_REPORTED, "notreported": STATE_NOT_REPORTED}.get(s, s)


_CMP = re.compile(r"^\s*(>=|<=|>|<|=|==)?\s*(.+?)\s*$")


def _value_matcher(db: HarnessDB, spec: dict, value: Any):
    """A predicate over a coded cell for ``value``, or an error dict if ``value`` is invalid."""
    kind = spec["type"]
    text = str(value).strip()
    if kind == "enum":
        permitted = list(spec.get("values") or [])
        allowed = {v.lower(): v for v in [*permitted, *sorted(db.observed_values.get(spec["key"],
                                                                                    ()))]}
        if text.lower() not in allowed:
            return _error(f"{text!r} is not a permitted value of {spec['key']}.",
                          permitted_values=permitted,
                          hint="To find systems that are silent on this dimension use "
                               "state='not_reported', not a value.")
        target = allowed[text.lower()]
        return lambda cell: target in [str(v) for v in cell_values(cell)]
    m = _CMP.match(text)
    op, operand = (m.group(1) or "="), m.group(2)
    if kind == "integer":
        try:
            num = int(float(operand))
        except ValueError:
            return _error(f"{spec['key']} is an integer dimension; got {text!r}.",
                          hint="Pass a number, optionally with an operator: '>=1000', '<5', '12'.")
        ops = {"=": lambda a: a == num, "==": lambda a: a == num, ">=": lambda a: a >= num,
               "<=": lambda a: a <= num, ">": lambda a: a > num, "<": lambda a: a < num}
        return lambda cell: any(isinstance(v, (int, float)) and ops[op](v) for v in cell_values(cell))
    if kind == "date":
        if op in ("=", "=="):
            return lambda cell: any(str(v).startswith(operand) for v in cell_values(cell))
        ops = {">=": lambda a: a >= operand, "<=": lambda a: a[:len(operand)] <= operand,
               ">": lambda a: a[:len(operand)] > operand, "<": lambda a: a < operand}
        return lambda cell: any(ops[op](str(v)) for v in cell_values(cell))
    low = text.lower()
    return lambda cell: any(low in str(v).lower() for v in cell_values(cell))


def _text_rank(system: dict, q: str) -> int | None:
    """0 exact id/name/alias, 1 prefix, 2 substring in id/name/alias, 3 substring in repo/version."""
    labels = [system["id"], system.get("name") or "", *(system.get("aliases") or [])]
    labels = [lab.lower() for lab in labels]
    if q in labels:
        return 0
    if any(lab.startswith(q) for lab in labels):
        return 1
    if any(q in lab for lab in labels):
        return 2
    other = [*(system.get("urls") or {}).values(), system.get("version_label") or ""]
    if any(q in str(o).lower() for o in other):
        return 3
    return None


# ------------------------------------------------------------------------------ tools


def search_systems(query: str = "", layer: str | None = None, dimension: str | None = None,
                   value: str | int | None = None, state: str | None = None, limit: int = 20,
                   layer_match: str = "any") -> dict[str, Any]:
    """Find HARNESS-DB systems by name/repo text and/or by what one dimension (or layer) says.

    Filters combine with AND; every argument is optional.

    - ``query``: case-insensitive text matched against system id, name, aliases, repo URL and
      version label. Exact matches rank first, then prefix, then substring. "" = no text filter.
    - ``dimension``: a dimension key ("network_policy") or id ("G3"). Selects the cell the
      ``value``/``state`` filters test, and each result shows that cell.
    - ``value``: keep systems whose ``dimension`` cell is CODED with this value. Enum: a permitted
      value (multi-valued cells match if the value is among them). Integer: "12", ">=1000",
      "<5". Date: a prefix such as "2025" or "2025-03", or ">=2025". String: substring.
    - ``state``: "coded", "not_reported" or "unresolved". ``state="not_reported"`` answers "which
      systems are silent on X" - silent means the sources were read and say nothing, NOT that
      the feature is absent.
    - ``layer``: a layer letter ("G") or name. Without ``dimension``, the ``value``/``state``
      filter is tested on every dimension of the layer and ``layer_match`` decides whether "any"
      (default) or "all" of them must pass; results show the layer's cells.
    - ``limit``: 1-200 results (default 20). ``total_matches`` always reports the full count.

    Each result gives id, name, repo, stratum, design weight, GitHub stars (if coded), per-state
    counts over all 38 cells, and the matched cells (value, state, confidence). Use
    get_system / get_evidence for quotes and locators.
    """
    db = get_db()
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return _error(f"limit must be an integer 1-{MAX_LIMIT}; got {limit!r}.")
    if not 1 <= limit <= MAX_LIMIT:
        return _error(f"limit must be between 1 and {MAX_LIMIT}; got {limit}.")
    layer_match = (layer_match or "any").strip().lower()
    if layer_match not in ("any", "all"):
        return _error(f"layer_match must be 'any' or 'all'; got {layer_match!r}.")

    spec = None
    if dimension:
        spec = db.resolve_dimension(dimension)
        if spec is None:
            return _unknown_dimension(db, dimension)
    lay = None
    if layer:
        lay = db.resolve_layer(layer)
        if lay is None:
            return _error(f"Unknown layer {layer!r}.",
                          valid_layers={x["id"]: x["name"] for x in db.layers})
        if spec is not None and spec["layer"] != lay["id"]:
            return _error(f"Dimension {spec['key']} is in layer {spec['layer']}, not {lay['id']}.",
                          hint="Drop layer, or pick a dimension from that layer.")
    target_specs = [spec] if spec else (db.dims_in_layer(lay["id"]) if lay else [])

    norm_state = _normalise_state(state)
    if norm_state is not None and norm_state not in STATES:
        return _error(f"Unknown state {state!r}.", valid_states=list(STATES))
    has_value = value is not None and str(value).strip() != ""
    if has_value and norm_state not in (None, STATE_CODED):
        return _error("A value filter only matches coded cells; drop state or set state='coded'.")
    if (has_value or norm_state) and not target_specs:
        return _error("value/state filters need a dimension (or a layer) to test.",
                      hint="e.g. search_systems(dimension='network_policy', state='not_reported')")

    matchers = {}
    if has_value:
        if spec is None:
            return _error("A value filter needs a single dimension, not a whole layer.")
        m = _value_matcher(db, spec, value)
        if isinstance(m, dict):
            return m
        matchers[spec["key"]] = m

    def cell_passes(s: dict, sp: dict) -> bool:
        cell = s["coding"].get(sp["key"]) or {}
        st = cell_state(cell)
        if has_value:
            return st == STATE_CODED and matchers[sp["key"]](cell)
        if norm_state:
            return st == norm_state
        return True

    q = (query or "").strip().lower()
    hits: list[tuple[int, str, dict]] = []
    for s in db.systems:
        rank = 0
        if q:
            rank = _text_rank(s, q)
            if rank is None:
                continue
        if target_specs and (has_value or norm_state):
            passes = [cell_passes(s, sp) for sp in target_specs]
            if not (all(passes) if layer_match == "all" else any(passes)):
                continue
        hits.append((rank, s["id"], s))
    hits.sort(key=lambda h: (h[0], h[1]))

    results = []
    any_nr = False
    for _, _, s in hits[:limit]:
        row = _system_header(db, s)
        row["state_counts"] = _state_counts(s, db.dims)
        any_nr = any_nr or row["state_counts"][STATE_NOT_REPORTED] > 0
        if target_specs:
            row["cells"] = [_compact_cell(sp, s["coding"].get(sp["key"])) for sp in target_specs]
        results.append(row)
    resp: dict[str, Any] = {
        "filters": {"query": query or "", "layer": lay["id"] if lay else None,
                    "dimension": spec["key"] if spec else None,
                    "value": value if has_value else None, "state": norm_state,
                    "layer_match": layer_match if (lay and not spec) else None},
        "total_matches": len(hits),
        "returned": len(results),
        "truncated": len(hits) > len(results),
        "results": results,
    }
    if resp["truncated"]:
        resp["hint"] = f"{len(hits) - len(results)} more match; raise limit (max {MAX_LIMIT}) " \
                       "or narrow the filter."
    return _with_note(resp, any_nr)


def get_system(system_id: str) -> dict[str, Any]:
    """Everything HARNESS-DB records about one system: all 38 cells, in schema order.

    ``system_id`` is the HARNESS-DB id (e.g. "swe-agent"); an exact name or alias also works.
    Each cell gives ``state`` (coded / not_reported / unresolved), ``value`` (null unless coded),
    ``quote`` (verbatim evidence), ``locator`` (path:line@commit, URL, or "paper Sec. N"),
    ``confidence`` (high/medium/low) and the coder's note. Unknown ids return an error with
    ``did_you_mean`` suggestions.
    """
    db = get_db()
    s = db.resolve_system(str(system_id))
    if s is None:
        return _unknown_system(db, system_id)
    cells = [_full_cell(db, spec, s["coding"].get(spec["key"])) for spec in db.dims]
    counts = _state_counts(s, db.dims)
    resp = {
        "system": {**_system_header(db, s), "urls": s.get("urls") or {},
                   "papers": s.get("papers") or [], "coded_at": s.get("coded_at"),
                   "release_notes": s.get("notes")},
        "state_counts": counts,
        "cells": cells,
    }
    return _with_note(resp, counts[STATE_NOT_REPORTED] > 0)


def get_evidence(system_id: str, dimension_key: str) -> dict[str, Any]:
    """The verbatim quote and locator behind one cell of one system.

    ``dimension_key`` accepts a key ("execution_isolation") or id ("G1"). Returns the cell's state
    and value, the ``quote`` and ``locator`` (a repo path:line@commit is at the system's pinned
    version, see ``pinned_version``; "paper Sec. N" refers to the paper), confidence, and the
    coder's note. A not_reported cell has no value; if it has a locator, that is where the coder
    looked and found nothing said.
    """
    db = get_db()
    s = db.resolve_system(str(system_id))
    if s is None:
        return _unknown_system(db, system_id)
    spec = db.resolve_dimension(dimension_key)
    if spec is None:
        return _unknown_dimension(db, dimension_key)
    cell = _full_cell(db, spec, s["coding"].get(spec["key"]))
    pinned = s["coding"].get("pinned_version") or {}
    resp = {
        "system_id": s["id"],
        "system_name": s.get("name"),
        "repo": (s.get("urls") or {}).get("repo"),
        "pinned_version": pinned.get("value") if cell_state(pinned) == STATE_CODED else None,
        **cell,
        "evidence_raw": (s["coding"].get(spec["key"]) or {}).get("evidence"),
    }
    if cell["state"] == STATE_CODED and cell["value"] is not None and spec["type"] == "enum":
        vals = cell["value"] if isinstance(cell["value"], list) else [cell["value"]]
        resp["value_glosses"] = {v: db.gloss(spec["key"], v) for v in vals}
    return _with_note(resp, cell["state"] == STATE_NOT_REPORTED)


def _quantile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolation quantile (numpy's default), without numpy."""
    n = len(sorted_vals)
    pos = (n - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, n - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def _integer_bins(values: list[float]) -> dict[float, str]:
    """Quartile bins labelled from the data, as in scripts/analyse_descriptives.py."""
    arr = sorted(values)
    edges = sorted({_quantile(arr, q) for q in (0.0, 0.25, 0.5, 0.75, 1.0)})
    if len(edges) < 2:
        return {v: f"{int(v)}" for v in arr}
    out: dict[float, str] = {}
    inner = edges[1:-1]
    for v in arr:
        idx = bisect_right(inner, v) if len(edges) > 2 else 0
        lo = edges[idx]
        hi = edges[idx + 1] if idx + 1 < len(edges) else edges[-1]
        out[v] = f"{int(lo)}-{int(hi)}" if hi > lo else f"{int(lo)}"
    return out


def _weighted_share(rows: list[tuple[str, float, float]], strata_sizes: dict[str, float]
                    ) -> tuple[float | None, float | None, float]:
    """Stratified ratio estimate Sum(w*f)/Sum(w) and its design SE (stratified SRS with FPC).

    ``rows`` is (stratum, weight, flag) per system. Same estimator as
    ``scripts/analyse_descriptives.weighted_share``: the complete stratum H adds zero variance.
    """
    base = sum(w for _, w, _ in rows)
    if base <= 0:
        return None, None, 0.0
    rate = sum(w * f for _, w, f in rows) / base
    total_n = sum(strata_sizes.values())
    var = 0.0
    for stratum, big_n in strata_sizes.items():
        flags = [f for st, w, f in rows if st == stratum and w > 0]
        n_h = len(flags)
        if n_h < 2 or big_n <= 0:
            continue
        p_h = sum(flags) / n_h
        fpc = max(0.0, 1.0 - n_h / big_n)
        var += (big_n / total_n) ** 2 * fpc * p_h * (1 - p_h) / (n_h - 1)
    return rate, math.sqrt(var), base


def dimension_distribution(dimension_key: str, weighted: bool = False) -> dict[str, Any]:
    """How the coded systems split across one dimension's values, with silence counted apart.

    Shares are over systems whose cell is CODED for this dimension. ``not_reported`` and
    ``unresolved`` systems are NOT in the share denominator; they are reported separately as
    ``n_not_reported`` / ``n_unresolved`` (and ``not_reported_rate``, over non-unresolved cells).
    Multi-valued dimensions give "share of systems that use X", which can sum above 1.

    ``weighted=False`` (default) describes the coded set: all released systems.
    ``weighted=True`` estimates the field: only weight-bearing systems (design weight > 0; the
    out-of-draw systems carry weight 0 and are excluded), each weighted by its stratum's inverse
    inclusion probability, with a design standard error per share.

    Integer dimensions are binned at data-derived quartiles (plus a numeric summary), dates by
    year, and the free-text pinned_version reports coverage only.
    """
    db = get_db()
    spec = db.resolve_dimension(dimension_key)
    if spec is None:
        return _unknown_dimension(db, dimension_key)
    if weighted and not db.has_weights:
        return _error("weighted=True needs data/coding_frame.csv, which this data root lacks.")
    key = spec["key"]
    population = [s for s in db.systems if (db.weight(s["id"]) > 0 or not weighted)]
    states = {s["id"]: cell_state(s["coding"].get(key)) for s in population}
    coded = [s for s in population if states[s["id"]] == STATE_CODED]
    n_nr = sum(1 for v in states.values() if v == STATE_NOT_REPORTED)
    n_un = sum(1 for v in states.values() if v == STATE_UNRESOLVED)

    labels: dict[str, list[str]] = {}
    numeric_summary = None
    if spec["type"] == "enum":
        for s in coded:
            labels[s["id"]] = [str(v) for v in cell_values(s["coding"][key])]
    elif spec["type"] == "integer":
        raw = {s["id"]: float(cell_values(s["coding"][key])[0]) for s in coded}
        # Bin edges come from every released coded value, so both weightings share one binning.
        all_vals = [float(cell_values(s["coding"][key])[0]) for s in db.systems
                    if cell_state(s["coding"].get(key)) == STATE_CODED]
        binmap = _integer_bins(all_vals) if all_vals else {}
        labels = {sid: [binmap[v]] for sid, v in raw.items()}
        vals = sorted(raw.values())
        if vals:
            numeric_summary = {"n": len(vals), "min": vals[0], "q1": _quantile(vals, .25),
                               "median": _quantile(vals, .5), "q3": _quantile(vals, .75),
                               "max": vals[-1], "mean": _r(sum(vals) / len(vals), 2)}
    elif spec["type"] == "date":
        labels = {s["id"]: [str(cell_values(s["coding"][key])[0])[:4]] for s in coded}
    else:
        labels = {s["id"]: ["(free text: not tabulated)"] for s in coded}

    order = list(spec.get("values") or [])
    seen = sorted({lab for labs in labels.values() for lab in labs},
                  key=lambda x: (order.index(x) if x in order else len(order), x))
    if spec["type"] == "enum":
        seen = order + [x for x in seen if x not in order]
    elif spec["type"] == "integer":
        seen = sorted(seen, key=lambda x: float(x.split("-")[0]))

    n_base = len(coded)
    w_base = sum(db.weight(s["id"]) for s in coded)
    rows = []
    for lab in seen:
        members = [s for s in coded if lab in labels[s["id"]]]
        row: dict[str, Any] = {"value": lab, "n_systems": len(members)}
        if spec["type"] == "enum":
            row["gloss"] = db.gloss(key, lab)
            row["in_schema"] = lab in order
        if weighted:
            flagged = {s["id"] for s in members}
            est, se, _ = _weighted_share(
                [(db.stratum(s["id"]) or "?", db.weight(s["id"]),
                  1.0 if s["id"] in flagged else 0.0) for s in coded], db.strata_sizes)
            row["weight"] = _r(sum(db.weight(s["id"]) for s in members), 3)
            row["share"] = _r(est)
            row["se"] = _r(se)
        else:
            row["share"] = _r(len(members) / n_base) if n_base else None
        rows.append(row)

    non_unres = [s for s in population if states[s["id"]] != STATE_UNRESOLVED]
    if weighted:
        nr_rate, nr_se, _ = _weighted_share(
            [(db.stratum(s["id"]) or "?", db.weight(s["id"]),
              1.0 if states[s["id"]] == STATE_NOT_REPORTED else 0.0) for s in non_unres],
            db.strata_sizes)
    else:
        nr_rate = n_nr / len(non_unres) if non_unres else None
        nr_se = None
    resp: dict[str, Any] = {
        "dimension": {**_dim_ref(spec),
                      "definition": (db.manual.get(key) or {}).get("definition") or spec["name"]},
        "weighted": bool(weighted),
        "population": ("weight-bearing systems (design weight > 0), weighted to the sampling "
                       "frame" if weighted else "all released systems (the coded set), unweighted"),
        "n_systems": len(population),
        "n_coded": n_base,
        "n_not_reported": n_nr,
        "n_unresolved": n_un,
        "not_reported_rate": _r(nr_rate),
        "share_denominator": "systems whose cell is coded (n_coded"
                             + (", by weight)" if weighted else ")"),
        "values": rows,
    }
    if weighted:
        resp["weight_total"] = _r(sum(db.weight(s["id"]) for s in population), 3)
        resp["weight_coded"] = _r(w_base, 3)
        resp["weight_not_reported"] = _r(sum(db.weight(s["id"]) for s in population
                                             if states[s["id"]] == STATE_NOT_REPORTED), 3)
        resp["not_reported_rate_se"] = _r(nr_se)
    if spec.get("multi"):
        resp["multi_valued"] = ("A system can hold several values, so shares are 'share of systems "
                                "using this value' and can sum above 1.")
    if numeric_summary:
        resp["numeric_summary"] = numeric_summary
    return _with_note(resp, n_nr > 0)


def under_reporting(by: str = "dimension") -> dict[str, Any]:
    """How often the sources are silent (not_reported), per dimension or per layer.

    ``by="dimension"`` (default): one row per dimension; ``by="layer"``: one row per layer, pooling
    that layer's cells. Rates are not_reported / (coded + not_reported): unresolved cells claim
    nothing and are excluded from the base (counted in ``n_unresolved``). Each row gives the
    unweighted rate (the coded set) and the weighted rate (the field estimate: weight-bearing
    systems only, stratum weights); dimension rows also carry the weighted rate's design SE.
    Rows are sorted by weighted rate, highest first. A high rate means the field rarely documents
    that aspect of its harnesses, not that harnesses lack it.
    """
    db = get_db()
    mode = (by or "dimension").strip().lower()
    if mode not in ("dimension", "layer"):
        return _error(f"by must be 'dimension' or 'layer'; got {by!r}.")
    weighted = db.has_weights

    def tally(specs: list[dict]) -> dict[str, Any]:
        n_cells = n_un = n_coded = n_nr = 0
        w_base = w_nr = 0.0
        per_system: list[tuple[str, float, float]] = []
        for s in db.systems:
            w = db.weight(s["id"])
            for sp in specs:
                st = cell_state(s["coding"].get(sp["key"]))
                n_cells += 1
                if st == STATE_UNRESOLVED:
                    n_un += 1
                    continue
                flag = 1.0 if st == STATE_NOT_REPORTED else 0.0
                n_coded += st == STATE_CODED
                n_nr += int(flag)
                w_base += w
                w_nr += w * flag
                if len(specs) == 1:
                    per_system.append((db.stratum(s["id"]) or "?", w, flag))
        n_base = n_coded + n_nr
        row = {"n_cells": n_cells, "n_unresolved": n_un, "n_base": n_base, "n_coded": n_coded,
               "n_not_reported": n_nr,
               "rate_unweighted": _r(n_nr / n_base) if n_base else None}
        if weighted:
            row["weight_base"] = _r(w_base, 3)
            row["rate_weighted"] = _r(w_nr / w_base) if w_base else None
            if len(specs) == 1:
                row["se_weighted"] = _r(_weighted_share(per_system, db.strata_sizes)[1])
        return row

    rows = []
    if mode == "dimension":
        for spec in db.dims:
            rows.append({"dimension": spec["key"], "dimension_id": spec["id"],
                         "name": spec["name"], "layer": spec["layer"], **tally([spec])})
    else:
        for lay in db.layers:
            specs = db.dims_in_layer(lay["id"])
            rows.append({"layer": lay["id"], "layer_name": lay["name"],
                         "n_dimensions": len(specs), "dimensions": [d["key"] for d in specs],
                         **tally(specs)})
    sort_key = "rate_weighted" if weighted else "rate_unweighted"
    rows.sort(key=lambda r: -(r.get(sort_key) or 0.0))
    overall = tally(db.dims)
    resp = {
        "by": mode,
        "rate_definition": "not_reported / (coded + not_reported); unresolved excluded",
        "weighting": ("rate_unweighted = the coded set (all released systems); rate_weighted = "
                      "field estimate over weight-bearing systems" if weighted else
                      "unweighted only (no data/coding_frame.csv in this data root)"),
        "overall": overall,
        "rows": rows,
    }
    return _with_note(resp, overall["n_not_reported"] > 0)


def compare(system_ids: list[str]) -> dict[str, Any]:
    """Put up to 6 systems side by side on all 38 dimensions.

    ``system_ids``: 1-6 HARNESS-DB ids (exact names/aliases also resolve). Unknown ids do not
    fail the call: they are listed in ``unknown_ids`` with ``did_you_mean`` suggestions and the
    known ones are compared. Each row is one dimension with, per system, state, value, confidence
    and locator; ``differs`` flags rows where the known systems do not all agree. Call
    get_evidence(system_id, dimension_key) for the quote behind any cell.
    """
    db = get_db()
    if isinstance(system_ids, str):
        system_ids = [x.strip() for x in system_ids.split(",") if x.strip()]
    ids = [str(x) for x in (system_ids or [])]
    if not ids:
        return _error("Give 1-6 system ids.", hint="Use search_systems to find ids.")
    if len(ids) > MAX_COMPARE:
        return _error(f"compare takes at most {MAX_COMPARE} systems; got {len(ids)}.",
                      hint="Split the comparison into several calls.")
    found: list[dict] = []
    unknown = []
    for ident in ids:
        s = db.resolve_system(ident)
        if s is None:
            unknown.append({"id": ident, "did_you_mean": db.suggest_systems(ident)})
        elif all(s is not f for f in found):
            found.append(s)
    resp: dict[str, Any] = {"systems": [_system_header(db, s) for s in found],
                            "unknown_ids": unknown}
    if not found:
        resp["error"] = "None of the given ids is in HARNESS-DB."
        resp["rows"] = []
        return resp
    rows = []
    any_nr = False
    for spec in db.dims:
        per = {}
        for s in found:
            cell = s["coding"].get(spec["key"]) or {}
            st = cell_state(cell)
            any_nr = any_nr or st == STATE_NOT_REPORTED
            per[s["id"]] = {"state": st, "value": _value_out(spec, cell),
                            "confidence": cell.get("confidence"),
                            "locator": split_evidence(cell.get("evidence"))[1]}
        sigs = {(c["state"], repr(sorted(c["value"]) if isinstance(c["value"], list)
                                  else c["value"])) for c in per.values()}
        rows.append({"dimension": spec["key"], "dimension_id": spec["id"], "layer": spec["layer"],
                     "differs": len(sigs) > 1, "cells": per})
    resp["rows"] = rows
    resp["n_rows_differing"] = sum(r["differs"] for r in rows)
    return _with_note(resp, any_nr)


def describe_schema(dimension_key: str | None = None) -> dict[str, Any]:
    """The HARNESS-DB coding schema: 9 layers, 38 dimensions, permitted values and their glosses.

    With no argument: every layer with its dimensions (key, id, name, type, multi, definition,
    permitted values with one-line glosses). With ``dimension_key`` (key or id): that dimension
    alone, plus the coding manual's decision rule and its layer's crosswalk to other taxonomies.
    Also returns the cell-state rule every tool follows.
    """
    db = get_db()

    def dim_out(spec: dict, detail: bool) -> dict[str, Any]:
        man = db.manual.get(spec["key"]) or {}
        out = {**_dim_ref(spec), "definition": man.get("definition") or spec["name"]}
        if spec["type"] == "enum":
            out["values"] = [{"value": v, "gloss": db.gloss(spec["key"], v) or None}
                             for v in spec.get("values") or []]
        if detail:
            out["decision_rule"] = man.get("decision_rule") or None
        return out

    states = {
        STATE_CODED: "a value with a verbatim evidence quote and locator",
        STATE_NOT_REPORTED: "sources read, silent on this dimension; NOT evidence of absence",
        STATE_UNRESOLVED: "coder could not settle it; claims nothing; excluded from rates",
    }
    if dimension_key:
        spec = db.resolve_dimension(dimension_key)
        if spec is None:
            return _unknown_dimension(db, dimension_key)
        lay = db.layer_by_id[spec["layer"]]
        return {"schema_version": db.schema.get("schema_version"),
                "layer": {"id": lay["id"], "name": lay["name"],
                          "crosswalk": lay.get("crosswalk") or {}},
                "dimension": dim_out(spec, True), "cell_states": states}
    layers = []
    for lay in db.layers:
        layers.append({"id": lay["id"], "name": lay["name"],
                       "crosswalk": lay.get("crosswalk") or {},
                       "dimensions": [dim_out(d, False) for d in db.dims_in_layer(lay["id"])]})
    return {"schema_version": db.schema.get("schema_version"),
            "status": db.schema.get("status"),
            "n_layers": len(layers), "n_dimensions": len(db.dims),
            "cell_states": states, "layers": layers}


TOOLS = (search_systems, get_system, get_evidence, dimension_distribution, under_reporting,
         compare, describe_schema)
