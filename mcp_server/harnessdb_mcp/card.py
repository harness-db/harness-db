"""The ``harnessdb://dataset-card`` resource: a short Markdown card computed from the loaded release.

Every number on the card is counted from the files at serve time, so the card cannot drift from
the data it describes.
"""

from __future__ import annotations

import re
from collections import Counter

from .db import (
    STATE_CODED,
    STATE_NOT_REPORTED,
    STATE_UNRESOLVED,
    THREE_STATE_RULE,
    HarnessDB,
    cell_state,
)


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "n/a"


def _cff_field(cff: str, name: str) -> str | None:
    m = re.search(rf"^{name}:\s*\"?(.+?)\"?\s*$", cff, re.MULTILINE)
    return m.group(1) if m else None


def dataset_card(db: HarnessDB) -> str:
    n_sys = len(db.systems)
    states: Counter = Counter()
    conf: Counter = Counter()
    for s in db.systems:
        for spec in db.dims:
            cell = s["coding"].get(spec["key"]) or {}
            st = cell_state(cell)
            states[st] += 1
            if st == STATE_CODED:
                conf[cell.get("confidence") or "unstated"] += 1
    n_cells = sum(states.values())
    lines = ["# HARNESS-DB dataset card", ""]
    if db.citation:
        title = _cff_field(db.citation, "title")
        if title:
            lines += [f"**{title}**", ""]
    if db.definition:
        lines += ["## What a harness is", "", db.definition.replace("**", ""), ""]
    lines += [
        "## Contents", "",
        (f"- **{n_sys:,} systems**, each coded on **{len(db.dims)} dimensions** in "
         f"**{len(db.layers)} layers** (schema {db.schema.get('schema_version')}): "
         f"{n_cells:,} cells."),
        ("- Every cell carries a state, and a coded cell carries a verbatim evidence quote, a "
         "locator (path:line@commit, URL or paper section) and a confidence (high/medium/low)."),
        "",
        "| state | cells | share |", "|---|---|---|",
    ]
    for st in (STATE_CODED, STATE_NOT_REPORTED, STATE_UNRESOLVED):
        lines.append(f"| `{st}` | {states[st]:,} | {_pct(states[st], n_cells)} |")
    lines += ["", "Confidence of coded cells: "
              + ", ".join(f"{k} {v:,}" for k, v in conf.most_common()) + ".", "",
              "## Read silence correctly", "", THREE_STATE_RULE, ""]
    if db.has_weights:
        by_stratum: Counter = Counter()
        w_systems = 0
        w_sum = 0.0
        for s in db.systems:
            by_stratum[db.stratum(s["id"]) or "?"] += 1
            w = db.weight(s["id"])
            if w > 0:
                w_systems += 1
                w_sum += w
        strata = (db.frame_meta or {}).get("strata") or {}
        lines += ["## Sampling and weights", "",
                  (f"The released systems are a stratified sample of a {len(db.frame):,}-system "
                   "sampling frame. Unweighted numbers describe the coded set; weighted numbers "
                   "estimate the field and use only weight-bearing systems."), "",
                  "| stratum | frame size | released | design weight |", "|---|---|---|---|"]
        order = [*strata, *sorted(k for k in by_stratum if k not in strata)]
        for st in [k for k in order if k in by_stratum]:
            meta = strata.get(st) or {}
            lines.append(f"| {st} | {int(db.strata_sizes.get(st, 0)):,} | {by_stratum[st]:,} | "
                         f"{meta.get('weight', '')} |")
        lines += ["", (f"Weight-bearing systems: {w_systems:,} (weights sum to {w_sum:,.0f}); "
                       f"{n_sys - w_systems} released systems were coded outside the draw and "
                       "carry weight 0."), ""]
    lines += ["## Provenance and reliability", ""]
    coders = Counter(c.get("coder") for s in db.systems for c in s["coding"].values())
    lines.append("Coders: " + ", ".join(f"`{k}` ({v:,} cells)" for k, v in coders.most_common())
                 + ". Cells were coded by an LLM against the frozen coding manual; see the "
                 "repository's docs/coding_reliability.md for the double-coded agreement.")
    if db.schema.get("status"):
        lines += ["", f"Schema status: {db.schema['status']}"]
    lines += ["", "## Licence and citation", "",
              "Data: CC BY 4.0 (LICENSE-DATA). Code: MIT (LICENSE-CODE).", ""]
    if db.citation:
        lines += ["```yaml", db.citation.strip(), "```", ""]
    return "\n".join(lines)
