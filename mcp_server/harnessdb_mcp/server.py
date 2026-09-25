"""HARNESS-DB as an MCP server (stdio), built on the official ``mcp`` Python SDK.

Works with the SDK's 2.x ``MCPServer`` and falls back to 1.x ``FastMCP``; the two share the
decorator API used here. Run ``harnessdb-mcp`` (or ``python -m harnessdb_mcp``).
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
from typing import Annotated, Any, Literal

from pydantic import Field

from . import tools as T
from .card import dataset_card
from .db import THREE_STATE_RULE, HarnessDB

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

try:
    from mcp.types import ToolAnnotations
except ImportError:  # pragma: no cover
    ToolAnnotations = None  # type: ignore[assignment]

INSTRUCTIONS = (
    "HARNESS-DB is a coded, evidence-backed dataset of LLM agent harnesses (the software layer "
    "that assembles a model's input, executes its actions and decides whether to continue): "
    "1,256 systems x 38 dimensions in 9 layers (A context, B tools, C control loop, D memory, "
    "E verification, F budget, G sandbox, H observability, M meta). "
    + THREE_STATE_RULE
    + " Unweighted numbers describe the coded set; weighted numbers estimate the field. "
    "Start with describe_schema to learn dimension keys and permitted values, search_systems to "
    "find ids, get_system / get_evidence to read cells with their quotes, compare for side-by-side, "
    "dimension_distribution and under_reporting for field-level numbers. Cite the locator when "
    "you state a system's value."
)


def _annotations(title: str) -> Any:
    if ToolAnnotations is None:  # pragma: no cover
        return None
    if "read_only_hint" in getattr(ToolAnnotations, "model_fields", {}):  # mcp 2.x
        return ToolAnnotations(title=title, read_only_hint=True, destructive_hint=False,
                               idempotent_hint=True, open_world_hint=False)
    # mcp 1.x names the fields in camelCase (and would silently accept snake_case as extras)
    return ToolAnnotations(title=title, readOnlyHint=True, destructiveHint=False,
                           idempotentHint=True, openWorldHint=False)


_StateArg = Literal["coded", "not_reported", "unresolved"]


def build_server(db: HarnessDB | None = None) -> Any:
    """Create the MCP server; ``db`` overrides the process-wide release (for tests)."""
    if db is not None:
        T.set_db(db)
    server = _Server(name="harnessdb", instructions=INSTRUCTIONS)

    def tool(title: str, impl: Any):
        return server.tool(description=inspect.cleandoc(impl.__doc__ or ""),
                           annotations=_annotations(title))

    @tool("Search systems", T.search_systems)
    def search_systems(
        query: Annotated[str, Field(description="Text matched against id, name, aliases, repo URL, "
                                                "version label. Empty = no text filter.")] = "",
        layer: Annotated[str | None, Field(description="Layer letter A-H or M, or layer name.")] = None,
        dimension: Annotated[str | None, Field(description="Dimension key (e.g. 'network_policy') "
                                                           "or id (e.g. 'G3').")] = None,
        value: Annotated[str | None, Field(description="Coded value to match on `dimension`: an "
                                                       "enum value, or for integers '>=1000', for "
                                                       "dates '2025'.")] = None,
        state: Annotated[_StateArg | None, Field(description="Cell state to match on `dimension` "
                                                             "(or on the layer's dimensions).")] = None,
        limit: Annotated[int, Field(ge=1, le=T.MAX_LIMIT, description="Max results.")] = 20,
        layer_match: Annotated[Literal["any", "all"], Field(
            description="With layer and no dimension: must any or all of the layer's dimensions "
                        "pass the value/state filter.")] = "any",
    ) -> dict[str, Any]:
        return T.search_systems(query, layer, dimension, value, state, limit, layer_match)

    @tool("Get system", T.get_system)
    def get_system(
        system_id: Annotated[str, Field(description="HARNESS-DB id (e.g. 'swe-agent'); an exact "
                                                    "name or alias also resolves.")],
    ) -> dict[str, Any]:
        return T.get_system(system_id)

    @tool("Get evidence", T.get_evidence)
    def get_evidence(
        system_id: Annotated[str, Field(description="HARNESS-DB system id.")],
        dimension_key: Annotated[str, Field(description="Dimension key or id, e.g. "
                                                        "'execution_isolation' or 'G1'.")],
    ) -> dict[str, Any]:
        return T.get_evidence(system_id, dimension_key)

    @tool("Dimension distribution", T.dimension_distribution)
    def dimension_distribution(
        dimension_key: Annotated[str, Field(description="Dimension key or id.")],
        weighted: Annotated[bool, Field(description="False: the coded set (all released systems). "
                                                    "True: field estimate over weight-bearing "
                                                    "systems.")] = False,
    ) -> dict[str, Any]:
        return T.dimension_distribution(dimension_key, weighted)

    @tool("Under-reporting", T.under_reporting)
    def under_reporting(
        by: Annotated[Literal["dimension", "layer"], Field(
            description="Silence rate per dimension or pooled per layer.")] = "dimension",
    ) -> dict[str, Any]:
        return T.under_reporting(by)

    @tool("Compare systems", T.compare)
    def compare(
        system_ids: Annotated[list[str], Field(min_length=1, max_length=T.MAX_COMPARE,
                                               description="1-6 system ids.")],
    ) -> dict[str, Any]:
        return T.compare(system_ids)

    @tool("Describe schema", T.describe_schema)
    def describe_schema(
        dimension_key: Annotated[str | None, Field(description="Optional dimension key or id for "
                                                               "one dimension in detail.")] = None,
    ) -> dict[str, Any]:
        return T.describe_schema(dimension_key)

    @server.resource("harnessdb://schema", name="schema", mime_type="application/json",
                     description="Layers, dimensions, permitted values and glosses.")
    def schema_resource() -> str:
        return json.dumps(T.describe_schema(), indent=1, ensure_ascii=False)

    @server.resource("harnessdb://system/{system_id}", name="system", mime_type="application/json",
                     description="All 38 cells of one system, with quotes and locators.")
    def system_resource(system_id: str) -> str:
        return json.dumps(T.get_system(system_id), indent=1, ensure_ascii=False)

    @server.resource("harnessdb://dataset-card", name="dataset-card", mime_type="text/markdown",
                     description="What HARNESS-DB is, its counts, weighting, licence, citation.")
    def card_resource() -> str:
        return dataset_card(T.get_db())

    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harnessdb-mcp", description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="HARNESS-DB checkout or release directory "
                                       "(default: $HARNESSDB_ROOT, then this checkout)")
    args = parser.parse_args(argv)
    if args.root:
        os.environ["HARNESSDB_ROOT"] = args.root
    db = HarnessDB.load(args.root)  # fail fast, before the client connects
    build_server(db).run()
    return 0
