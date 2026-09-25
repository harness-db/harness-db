"""Loading HARNESS-DB from a checkout or a downloaded release, with no dependency beyond the stdlib.

The server reads four files, all relative to one data root:

  data/systems.json          the release: one object per system, 38 coded cells each (required)
  schema/dimensions.json     layers, dimensions, permitted values (required)
  data/coding_frame.csv      stratum and design weight per system (optional; enables weighted=True)
  docs/coding_manual.md      per-dimension definitions and per-value glosses (optional)
  docs/definition.md         the one-sentence harness definition, for the dataset card (optional)

The root is resolved in this order: an explicit ``root`` argument, the ``HARNESSDB_ROOT``
environment variable, the checkout this package sits in (``mcp_server/..``), the working directory.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STATE_CODED = "coded"
STATE_NOT_REPORTED = "not_reported"
STATE_UNRESOLVED = "unresolved"
STATES = (STATE_CODED, STATE_NOT_REPORTED, STATE_UNRESOLVED)

THREE_STATE_RULE = (
    "Three-state rule: every HARNESS-DB cell is in exactly one state. "
    "'coded' = a value backed by a verbatim evidence quote and a locator. "
    "'not_reported' = the coder read the system's sources (paper and/or repository at the pinned "
    "version) and they say nothing on this dimension. It is a finding about documentation, NOT "
    "evidence that the feature is absent: an absence the sources show (e.g. a config schema with no "
    "network option) is coded as a value such as 'none' or 'open'. Never read not_reported as "
    "'no', 'none' or 'false'. "
    "'unresolved' = the coder could not settle the cell; it claims nothing about the sources and "
    "is excluded from every rate and share."
)

_EVIDENCE_RE = re.compile(r'^\s*"(?P<quote>.*)"\s*\((?P<locator>[^()]*(?:\([^()]*\)[^()]*)*)\)\s*$',
                          re.DOTALL)
_DIM_HEADING = re.compile(r"^####\s+([A-Z]\d+)\s+(\w+)")
_VALUE_BULLET = re.compile(r"^-\s+`([^`]+)`(?:\s*:\s*(.*))?$")
_INLINE_VALUE = re.compile(r"`([^`]+)`(?:\s*\(([^)]*)\))?")

_ENV_ROOT = "HARNESSDB_ROOT"
_REQUIRED = ("data/systems.json", "schema/dimensions.json")


class DataRootError(RuntimeError):
    """Raised when no directory containing the HARNESS-DB release can be found."""


def find_root(root: str | os.PathLike | None = None) -> Path:
    """Resolve the data root (see the module docstring for the search order)."""
    candidates: list[Path] = []
    if root:
        candidates.append(Path(root))
    if os.environ.get(_ENV_ROOT):
        candidates.append(Path(os.environ[_ENV_ROOT]))
    candidates.append(Path(__file__).resolve().parents[2])
    candidates.append(Path.cwd())
    for cand in candidates:
        if all((cand / rel).is_file() for rel in _REQUIRED):
            return cand.resolve()
    tried = ", ".join(str(c) for c in candidates)
    raise DataRootError(
        f"HARNESS-DB data not found (need {' and '.join(_REQUIRED)}). Tried: {tried}. "
        f"Set {_ENV_ROOT} to a harness-db checkout or release directory, or pass --root."
    )


# ------------------------------------------------------------------------------ cell helpers


def cell_state(cell: dict | None) -> str:
    """Map one cell to exactly one state; mirrors ``scripts/analyse_descriptives.py``.

    ``unresolved`` wins over ``not_reported``; a cell with neither flag and no value claims
    nothing and is treated as unresolved rather than invented.
    """
    cell = cell or {}
    if cell.get("unresolved"):
        return STATE_UNRESOLVED
    if cell.get("not_reported"):
        return STATE_NOT_REPORTED
    if cell.get("value") is None or cell.get("value") == []:
        return STATE_UNRESOLVED
    return STATE_CODED


def cell_values(cell: dict) -> tuple:
    """The coded value(s) as a tuple (single-valued dimensions give a 1-tuple)."""
    v = cell.get("value")
    if v is None:
        return ()
    return tuple(v) if isinstance(v, list) else (v,)


def split_evidence(evidence: str | None) -> tuple[str | None, str | None]:
    """Split a release evidence string ``"quote" (locator)`` into (quote, locator).

    A handful of cells carry a bare locator with no quote (e.g. ``README.md@585fe7c``); those
    come back as (None, locator).
    """
    if not evidence:
        return None, None
    m = _EVIDENCE_RE.match(evidence)
    if m:
        return m.group("quote"), m.group("locator").strip()
    return None, evidence.strip()


# ------------------------------------------------------------------------------ glosses


def parse_manual(text: str) -> dict[str, dict[str, Any]]:
    """Per-dimension ``definition``, ``values`` glosses and ``decision_rule`` from the manual."""
    out: dict[str, dict[str, Any]] = {}
    cur: dict[str, Any] | None = None
    mode = None
    last_value = None
    for raw in text.splitlines():
        line = raw.rstrip()
        head = _DIM_HEADING.match(line)
        if head:
            cur = {"definition": "", "values": {}, "decision_rule": ""}
            out[head.group(2)] = cur
            mode, last_value = None, None
            continue
        if line.startswith("#"):
            cur, mode = None, None
            continue
        if cur is None:
            continue
        stripped = line.strip()
        if not stripped:
            if mode in ("definition", "decision_rule", "values_inline"):
                mode = None
            last_value = None if mode != "values" else last_value
            continue
        if stripped.startswith("Definition:"):
            mode = "definition"
            cur["definition"] = stripped[len("Definition:"):].strip()
            continue
        if stripped.startswith("Values:"):
            inline = stripped[len("Values:"):].strip()
            mode = "values_inline" if inline else "values"
            for name, gloss in _INLINE_VALUE.findall(inline):
                cur["values"][name] = gloss.strip()
            continue
        if stripped.startswith("Decision rule:"):
            mode = "decision_rule"
            cur["decision_rule"] = stripped[len("Decision rule:"):].strip()
            continue
        if stripped.startswith(("Evidence:", "Rule:", "- SWE-agent", "- OpenHands")):
            if stripped.startswith("Rule:") and not cur["decision_rule"]:
                cur["decision_rule"] = stripped[len("Rule:"):].strip()
                mode = "decision_rule"
            else:
                mode = None
            continue
        if mode == "definition":
            cur["definition"] += " " + stripped
        elif mode == "decision_rule":
            cur["decision_rule"] += " " + stripped
        elif mode == "values":
            bullet = _VALUE_BULLET.match(stripped)
            if bullet:
                last_value = bullet.group(1)
                cur["values"][last_value] = (bullet.group(2) or "").strip()
            elif last_value and raw.startswith("  "):
                cur["values"][last_value] += " " + stripped
            else:
                mode = None
        elif mode == "values_inline":
            for name, gloss in _INLINE_VALUE.findall(stripped):
                cur["values"][name] = gloss.strip()
    return out


def one_sentence_definition(text: str) -> str | None:
    """The paragraph under '## 1. One-sentence definition' in docs/definition.md."""
    m = re.search(r"^##\s*1\.[^\n]*\n+(.+?)\n\s*\n", text, re.MULTILINE | re.DOTALL)
    return " ".join(m.group(1).split()) if m else None


# ------------------------------------------------------------------------------ the database


@dataclass
class HarnessDB:
    """The release held in memory, with the lookups every tool needs."""

    root: Path
    schema: dict
    systems: list[dict]
    frame: dict[str, dict[str, str]] = field(default_factory=dict)
    frame_meta: dict = field(default_factory=dict)
    manual: dict[str, dict[str, Any]] = field(default_factory=dict)
    definition: str | None = None
    citation: str | None = None

    def __post_init__(self) -> None:
        self.dims: list[dict] = list(self.schema["dimensions"])
        self.dim_by_key = {d["key"]: d for d in self.dims}
        self.dim_by_id = {d["id"].upper(): d for d in self.dims}
        self.layers: list[dict] = list(self.schema["layers"])
        self.layer_by_id = {lay["id"].upper(): lay for lay in self.layers}
        self.by_id = {s["id"]: s for s in self.systems}
        self.by_lower: dict[str, dict] = {}
        for s in self.systems:
            for label in [s["id"], s.get("name", ""), *(s.get("aliases") or [])]:
                if label:
                    self.by_lower.setdefault(label.strip().lower(), s)
        sizes = Counter(r.get("stratum", "?") for r in self.frame.values())
        self.strata_sizes = {k: float(v) for k, v in sizes.items()}
        self.observed_values: dict[str, set[str]] = {}
        for d in self.dims:
            if d["type"] != "enum":
                continue
            seen: set[str] = set()
            for s in self.systems:
                cell = s["coding"].get(d["key"]) or {}
                if cell_state(cell) == STATE_CODED:
                    seen.update(str(v) for v in cell_values(cell))
            self.observed_values[d["key"]] = seen

    # --- construction ---------------------------------------------------------------------

    @classmethod
    def load(cls, root: str | os.PathLike | None = None) -> HarnessDB:
        base = find_root(root)
        schema = json.loads((base / "schema/dimensions.json").read_text(encoding="utf-8"))
        systems = json.loads((base / "data/systems.json").read_text(encoding="utf-8"))
        frame: dict[str, dict[str, str]] = {}
        frame_path = base / "data/coding_frame.csv"
        if frame_path.is_file():
            csv.field_size_limit(10 ** 8)
            with frame_path.open(encoding="utf-8-sig", newline="") as fh:
                frame = {r["system_id"]: r for r in csv.DictReader(fh)}
        frame_meta: dict = {}
        if (base / "data/coding_frame.json").is_file():
            frame_meta = json.loads((base / "data/coding_frame.json").read_text(encoding="utf-8"))
        manual = {}
        if (base / "docs/coding_manual.md").is_file():
            manual = parse_manual((base / "docs/coding_manual.md").read_text(encoding="utf-8"))
        definition = None
        if (base / "docs/definition.md").is_file():
            definition = one_sentence_definition(
                (base / "docs/definition.md").read_text(encoding="utf-8"))
        citation = None
        if (base / "CITATION.cff").is_file():
            citation = (base / "CITATION.cff").read_text(encoding="utf-8")
        return cls(root=base, schema=schema, systems=systems, frame=frame, frame_meta=frame_meta,
                   manual=manual, definition=definition, citation=citation)

    # --- lookups --------------------------------------------------------------------------

    @property
    def has_weights(self) -> bool:
        return bool(self.frame)

    def weight(self, system_id: str) -> float:
        row = self.frame.get(system_id) or {}
        try:
            return float(row.get("weight") or 0.0)
        except ValueError:
            return 0.0

    def stratum(self, system_id: str) -> str | None:
        row = self.frame.get(system_id)
        return row.get("stratum") if row else None

    def resolve_dimension(self, ident: str | None) -> dict | None:
        """A dimension by key (``network_policy``), id (``G3``) or display name."""
        if not ident:
            return None
        text = str(ident).strip()
        if text in self.dim_by_key:
            return self.dim_by_key[text]
        if text.upper() in self.dim_by_id:
            return self.dim_by_id[text.upper()]
        low = text.lower().replace("-", "_").replace(" ", "_")
        for d in self.dims:
            if low in (d["key"].lower(), d["name"].lower().replace(" ", "_")):
                return d
        return None

    def resolve_layer(self, ident: str | None) -> dict | None:
        """A layer by letter (``G``) or name (``Sandbox and environment``)."""
        if not ident:
            return None
        text = str(ident).strip()
        if text.upper() in self.layer_by_id:
            return self.layer_by_id[text.upper()]
        for lay in self.layers:
            if lay["name"].lower() == text.lower():
                return lay
        return None

    def resolve_system(self, ident: str) -> dict | None:
        """A system by id, or by exact (case-insensitive) name or alias."""
        if ident in self.by_id:
            return self.by_id[ident]
        return self.by_lower.get(str(ident).strip().lower())

    def suggest_systems(self, ident: str, n: int = 5) -> list[str]:
        """Close ids for an unknown one: substring hits first, then fuzzy matches."""
        import difflib

        low = str(ident).strip().lower()
        hits = [s["id"] for s in self.systems
                if low and (low in s["id"].lower() or low in s.get("name", "").lower())]
        fuzzy = difflib.get_close_matches(low, list(self.by_lower), n=n, cutoff=0.6)
        for label in fuzzy:
            sid = self.by_lower[label]["id"]
            if sid not in hits:
                hits.append(sid)
        return hits[:n]

    def dims_in_layer(self, layer_id: str) -> list[dict]:
        return [d for d in self.dims if d["layer"] == layer_id]

    def gloss(self, key: str, value: str) -> str | None:
        return (self.manual.get(key) or {}).get("values", {}).get(value)
