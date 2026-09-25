"""Finding the data: the in-repo ``data/`` directory, a packaged release, or an explicit path."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Environment variable that points the loader at a data directory or ``datapackage.json``.
ENV_VAR = "HARNESSDB_DATA"


@dataclass
class Sources:
    """Where each input lives. ``kind`` is ``"repo"`` (a checkout's ``data/``) or ``"release"``."""

    kind: str
    root: Path
    systems: Path
    schema: Path
    cells: Path | None = None
    systems_wide: Path | None = None
    frame: Path | None = None
    frame_summary: Path | None = None
    results: Path | None = None
    papers: Path | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


_ROLE_NAMES: dict[str, tuple[str, ...]] = {
    "systems": ("systems", "harness_db_systems", "harnessdb_systems"),
    "cells": ("cells", "harness_db_cells", "harnessdb_cells", "coding_cells"),
    "systems_wide": ("systems_wide", "systems_table"),
    "schema": ("dimensions", "schema_dimensions", "coding_sheet", "schema"),
    "frame": ("coding_frame", "sampling_frame", "frame", "strata", "weights"),
    "frame_summary": ("coding_frame_summary", "design"),
    "results": ("results", "scores", "reported_scores"),
    "papers": ("papers", "bibliography"),
}


def _first(v: Any) -> str | None:
    if isinstance(v, list):
        return str(v[0]) if v else None
    return str(v) if v else None


def _release_sources(dp_path: Path) -> Sources:
    """Resolve the resources of a Frictionless ``datapackage.json``.

    Resources are matched by ``name`` first and by file stem second; anything the descriptor does
    not list is looked up under its conventional file name next to the descriptor.
    """
    root = dp_path.parent.resolve()
    dp = json.loads(dp_path.read_text(encoding="utf-8"))
    found: dict[str, Path] = {}
    for res in dp.get("resources", []) or []:
        rel = _first(res.get("path"))
        if not rel:
            continue
        path = (root / rel).resolve()
        if not path.is_file():
            continue
        fname = Path(rel).name
        name = _norm(str(res.get("name", "")))
        stem = _norm(fname.split(".")[0])
        for role, names in _ROLE_NAMES.items():
            if role in found or not (name in names or stem in names):
                continue
            # ``harness_db.schema.json`` is the generated JSON Schema, not the coding sheet.
            if role == "schema" and fname.endswith(".schema.json"):
                continue
            if role == "frame" and path.suffix == ".json":
                found.setdefault("frame_summary", path)
                break
            found[role] = path
            break
    meta = {k: v for k, v in dp.items() if k != "resources"}
    src = Sources(kind="release", root=root, systems=found.get("systems", Path()),
                  schema=found.get("schema", Path()), cells=found.get("cells"),
                  systems_wide=found.get("systems_wide"), frame=found.get("frame"),
                  frame_summary=found.get("frame_summary"), results=found.get("results"),
                  papers=found.get("papers"), meta=meta)
    return _fill_conventional(src, [root, root / "data", root / "schema"])


def _fill_conventional(src: Sources, dirs: list[Path]) -> Sources:
    """Fill every unresolved input from its conventional file name in ``dirs``."""
    def look(*names: str) -> Path | None:
        for d in dirs:
            for n in names:
                p = d / n
                if p.is_file():
                    return p.resolve()
        return None

    src.cells = src.cells or look("cells.parquet", "cells.csv")
    src.systems_wide = src.systems_wide or look("systems_wide.csv", "systems_wide.parquet")
    if not src.systems.is_file():
        src.systems = look("systems.json", "systems.jsonl", "systems.parquet",
                           "systems.csv") or Path()
    if not src.systems.is_file() and src.cells is not None and src.systems_wide is not None:
        src.systems = src.systems_wide  # a tabular-only release: rebuild from wide + cells
    if not src.schema.is_file():
        src.schema = look("dimensions.json") or Path()
    src.frame = src.frame or look("coding_frame.csv", "coding_frame.parquet", "strata.csv")
    src.frame_summary = src.frame_summary or look("coding_frame.json")
    src.results = src.results or look("results.csv", "results.parquet")
    src.papers = src.papers or look("papers.csv", "papers.parquet")
    return src


def _repo_sources(data_dir: Path) -> Sources:
    data_dir = data_dir.resolve()
    src = Sources(kind="repo", root=data_dir, systems=Path(), schema=Path())
    return _fill_conventional(src, [data_dir, data_dir / "schema", data_dir.parent / "schema"])


def _from_candidate(path: Path) -> Sources | None:
    """Interpret one path: a descriptor, a data directory, a release directory, or a repo root."""
    if path.is_file():
        if path.name == "datapackage.json":
            return _release_sources(path)
        if path.name.startswith("systems."):
            return _repo_sources(path.parent)
        return None
    if not path.is_dir():
        return None
    if (path / "datapackage.json").is_file():
        return _release_sources(path / "datapackage.json")
    if (path / "systems.json").is_file():
        return _repo_sources(path)
    if (path / "data" / "systems.json").is_file():
        return _repo_sources(path / "data")
    if (path / "data" / "datapackage.json").is_file():
        return _release_sources(path / "data" / "datapackage.json")
    return None


def locate(path: str | os.PathLike[str] | None = None) -> Sources:
    """Find the dataset.

    Order: the explicit ``path``; then ``$HARNESSDB_DATA``; then the current directory and its
    parents; then the directory this package was imported from and its parents (an editable
    install inside the repository). The first hit wins. A hit is a ``datapackage.json`` (a
    release), a directory holding ``datapackage.json`` (a release directory), a directory
    holding ``systems.json`` (a ``data/`` directory), or one holding ``data/systems.json``
    (a repository checkout).
    """
    if path is not None:
        src = _from_candidate(Path(path).expanduser().resolve())
        if src is None:
            raise FileNotFoundError(
                f"{path}: not a HARNESS-DB data location. Pass a release directory or its "
                "datapackage.json, a data/ directory holding systems.json, or a repository root.")
        return _check(src)
    env = os.environ.get(ENV_VAR)
    if env:
        src = _from_candidate(Path(env).expanduser().resolve())
        if src is None:
            raise FileNotFoundError(f"{ENV_VAR}={env} is not a HARNESS-DB data location")
        return _check(src)
    seen: set[Path] = set()
    for start in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for cand in (start, *start.parents):
            if cand in seen:
                continue
            seen.add(cand)
            src = _from_candidate(cand)
            if src is not None:
                return _check(src)
    raise FileNotFoundError(
        "HARNESS-DB data not found. Run from inside the repository, pass a path "
        f"(harnessdb.load('path/to/release')), or set the {ENV_VAR} environment variable.")


def _check(src: Sources) -> Sources:
    missing = [n for n, p in (("systems", src.systems), ("schema (dimensions.json)", src.schema))
               if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"{src.root}: found the data location but not {', '.join(missing)}")
    tabular = src.systems.suffix in (".csv", ".parquet")
    if tabular and (src.cells is None or not src.cells.is_file()):
        raise FileNotFoundError(f"{src.root}: a tabular systems file needs a cells table beside it")
    return src
