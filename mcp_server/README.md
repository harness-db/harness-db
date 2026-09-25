# harnessdb-mcp

An [MCP](https://modelcontextprotocol.io) server that lets AI agents and coding assistants query
**HARNESS-DB** directly: 1,256 LLM agent harnesses, each coded on 38 dimensions in 9 layers
(context assembly, tool interface, control loop, memory, verification, budget, sandbox,
observability, meta). Every coded cell comes with a verbatim evidence quote and a locator.

It is built on the official `mcp` Python SDK and speaks stdio. It is tested against the SDK's
2.x `MCPServer`, and it falls back to the 1.x `FastMCP` class, which has the same decorator API. The query layer (`harnessdb_mcp/tools.py`) uses only the standard library.

## Install

From a clone of this repository:

```sh
pip install -e ./mcp_server
```

Keep the `./`. Without it pip looks for a package named `mcp_server` on PyPI, which is someone
else's project.

The server reads the release from a data root: a directory that contains `data/systems.json` and
`schema/dimensions.json`. It also uses `data/coding_frame.csv` for weights and
`docs/coding_manual.md` for value glosses when they are present. It looks for the root in this
order:

1. `--root` on the command line
2. the `HARNESSDB_ROOT` environment variable
3. the checkout the package sits in, which works for an editable install
4. the working directory

After a non-editable install (`pip install ./mcp_server`), set `HARNESSDB_ROOT`.

Run it with `harnessdb-mcp` or `python -m harnessdb_mcp`.

## Configure a client

**Claude Code**:

```sh
claude mcp add harnessdb -e HARNESSDB_ROOT=/path/to/harness-db -- harnessdb-mcp
```

To share it with a project instead, put this in the project's `.mcp.json`:

```json
{
  "mcpServers": {
    "harnessdb": {
      "command": "harnessdb-mcp",
      "args": [],
      "env": { "HARNESSDB_ROOT": "/path/to/harness-db" }
    }
  }
}
```

**Claude Desktop**: add the same block to `claude_desktop_config.json`, which lives at
`%APPDATA%\Claude\` on Windows and `~/Library/Application Support/Claude/` on macOS. If
`harnessdb-mcp` is not on the client's `PATH`, use the full interpreter path instead:

```json
{
  "mcpServers": {
    "harnessdb": {
      "command": "C:\\Python314\\python.exe",
      "args": ["-m", "harnessdb_mcp", "--root", "C:\\path\\to\\harness-db"]
    }
  }
}
```

## Tools

| tool | what it answers |
|---|---|
| `search_systems(query, layer, dimension, value, state, limit, layer_match)` | Finds systems by name or repo text and/or by what one dimension says. `state="not_reported"` lists the systems whose sources say nothing on that dimension. `value` accepts enum values, `">=10000"` for integers and `"2025"` for dates. |
| `get_system(system_id)` | Returns all 38 cells of one system: state, value, quote, locator, confidence and the coder's note. |
| `get_evidence(system_id, dimension_key)` | Returns the quote and locator behind one cell, with the system's pinned version. |
| `dimension_distribution(dimension_key, weighted)` | Returns value shares among coded systems, with `n_not_reported` and `n_unresolved` reported separately. With `weighted=true` it gives a field estimate over weight-bearing systems only, with design SEs. |
| `under_reporting(by)` | Returns silence rates by `"dimension"` or `"layer"`, unweighted (the coded set) and weighted (the field). |
| `compare(system_ids)` | Puts up to 6 systems side by side. Unknown ids come back in `unknown_ids` with suggestions and do not fail the call. |
| `describe_schema(dimension_key)` | Lists layers, dimensions, permitted values and their glosses. Given one dimension, it adds the coding manual's decision rule. |

**Resources:** `harnessdb://schema`, `harnessdb://system/{id}` and `harnessdb://dataset-card`.

All tools are read-only. Bad input returns `{"error": ..., "hint": ...}` instead of failing the
call.

### Silence is not absence

Every cell is `coded`, `not_reported` or `unresolved`.

- **`coded`**: the sources give a value.
- **`not_reported`**: the coder read the system's sources and they say nothing on that dimension.
  This tells you about the documentation, not about the system. When the sources do show an
  absence, it is coded as a value such as `none`.
- **`unresolved`**: the coder could not settle the cell. It claims nothing and is left out of
  every rate.

Any response that contains a `not_reported` cell or count repeats this rule once, in a top-level
`note` field, so an agent reading only that response still gets it.

## Three things to ask an agent

1. *"Which HARNESS-DB harnesses with at least 10,000 GitHub stars say nothing about their network
   policy? For each one, what does it report about execution isolation?"* The agent calls
   `search_systems(dimension="stars", value=">=10000")`, then `compare` on the results.
2. *"Compare SWE-agent, OpenHands and Aider on context compaction, self-verification and
   rollback. Cite the evidence locator for every value."* The agent calls `compare`, then
   `get_evidence`.
3. *"Across the field as a whole, what share of harnesses isolate execution in a container or VM,
   and how much of the field doesn't say?"* The agent calls
   `dimension_distribution("execution_isolation", weighted=true)` and `under_reporting()`.

## Tests

`tests/test_mcp_server.py` at the repository root calls every tool on the real release and
checks the counts against `data/systems.json` and the release tables in `data/analysis/`.
