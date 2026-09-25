"""harnessdb-mcp: query HARNESS-DB (coded LLM agent harnesses) from any MCP client.

The query functions live in :mod:`harnessdb_mcp.tools` and need only the standard library; the
MCP wiring is in :mod:`harnessdb_mcp.server`.
"""

from .tools import (
    compare,
    describe_schema,
    dimension_distribution,
    get_evidence,
    get_system,
    search_systems,
    under_reporting,
)

__version__ = "0.1.0"

__all__ = ["compare", "describe_schema", "dimension_distribution", "get_evidence", "get_system",
           "search_systems", "under_reporting"]
