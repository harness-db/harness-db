# Ruflo: HARNESS-DB cell card

| | |
|---|---|
| System id | `ruflo` |
| Pinned version | [v3.38.20 @ `e21aa352fdc8`](https://github.com/ruvnet/ruflo/commit/e21aa352fdc80fd2d3cc4e83404a76a18d118b96) (2026-08-24) |
| Repository | <https://github.com/ruvnet/ruflo> |
| Stars (sampling-frame snapshot) | 72,623 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 18 coded, 20 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=ruflo> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `not_reported` |  |  |  | No prompt-assembly code in evidence bundle (README/docs/file tree only). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20system_prompt_style&system=ruflo&dimension=A1%20system_prompt_style&current=not_reported) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | Harness wraps Claude Code; no context-injection code in bundle. Vector RAG plugins exist (ruflo-rag-memory). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20env_context_strategy&system=ruflo&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | No history-processing code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20context_compaction&system=ruflo&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | No observation conversion code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20observation_format&system=ruflo&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | low | “One model response can fire 4–6+ tools at the same time.” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | Tools exposed via MCP to Claude Code/Codex; inferred from README prose about MCP tool calling. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20tool_call_format&system=ruflo&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `314` | low | “You don't need to learn 314 MCP tools or 26 CLI commands.” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | Tools are MCP-served, which strict B2 rule excludes; host (Claude Code) built-ins not counted. Web UI cites ~210 tools. Count is documentation claim only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20tool_count&system=ruflo&dimension=B2%20tool_count&current=314) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | Editing delegated to host agent (Claude Code/Codex); no edit tool definition in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20edit_primitive&system=ruflo&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `mcp` | low | “MCP Server -- 314 tools for coordination, memory, neural learning, and more” | [docs/index.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/docs/index.md)† | Tools served via MCP; underlying authoring method not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20tool_schema_source&system=ruflo&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp` | high | “claude mcp add claude-flow -- npx ruflo@latest mcp start” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | Ruflo is an MCP server; web UI also acts as MCP client. Federation uses custom mTLS/ed25519 protocol. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20protocol_standardization&system=ruflo&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | low | “the hooks system automatically routes tasks, learns from successful patterns, and coordinates agents in the background.” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | React loop from host Claude Code; hook-driven event handling. Autopilot loops, GOAP planner and tournaments (arena) are plugins; no loop code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20loop_primitives&system=ruflo&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `explicit_plan_object` | low | “Break big goals into plans and track progress” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | ruflo-goals plugin / GOAP planner; default CLI install status unclear. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20planning_granularity&system=ruflo&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `orchestrator_workers` | low | “Queen-led hierarchy (Raft, Byzantine, Gossip)” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | Swarm topologies hierarchical/mesh/adaptive documented; code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20multi_agent_topology&system=ruflo&dimension=C3%20multi_agent_topology&current=orchestrator_workers) |
| C4 | `delegation_mechanism` | `subagent_spawn` | low | “not the bare \`memory\_store\`/\`swarm\_init\`/\`agent\_spawn\` names the CLI-track scaffold uses” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | agent\_spawn MCP tool; federation adds cross-machine messaging. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20delegation_mechanism&system=ruflo&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | Host Claude Code permissions may apply; no Ruflo config surface in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20human_in_loop&system=ruflo&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  | No state object code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20short_term_state&system=ruflo&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `skill_library, vector_store` | low | “HNSW vector memory with sub-ms retrieval” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | AgentDB/HNSW memory across sessions; .agents/skills SKILL.md library in file tree; ReasoningBank trajectory learning. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20long_term_memory&system=ruflo&dimension=D2%20long_term_memory&current=skill_library%7Cvector_store) |
| D3 | `state_persistence` | `not_reported` |  |  |  | hive-mind-resume command and workflow resume mentioned (buggy per roadmap) but no code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20state_persistence&system=ruflo&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | Reviewer agents/testgen plugins exist; no harness-enforced verification code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20self_verification&system=ruflo&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20retry_policy&system=ruflo&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  | .claude/checkpoints/ exists in tree; mechanism not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20rollback&system=ruflo&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20termination_condition&system=ruflo&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `model_routing, token_budget` | low | “Track token usage, set budgets, get cost alerts” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | cost-tracker plugin; routing via 'Multi-Provider ... with smart routing'. Enforcement not verified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20cost_controls&system=ruflo&dimension=F2%20cost_controls&current=model_routing%7Ctoken_budget) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20timeouts&system=ruflo&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “MCP servers run locally, no data leaves your machine” | [docs/index.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/docs/index.md)† | Runs on host via Claude Code; WASM sandbox, worktree isolation and cloud Managed Agents available via plugins. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20execution_isolation&system=ruflo&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20filesystem_access&system=ruflo&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20network_policy&system=ruflo&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | Plugins declare permissions in manifest; host permission model not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20permission_model&system=ruflo&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `structured_traces` | low | “Structured logs, traces, and metrics in one place” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | ruflo-observability plugin; OTel unknown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20tracing&system=ruflo&dimension=H1%20tracing&current=structured_traces) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20replayability&system=ruflo&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | SOTA benchmarks are perf comparisons on separate branch; no task-eval runner visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20eval_hooks&system=ruflo&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `input_filters, output_filters` | low | “Block prompt injection, detect PII, safety scanning” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | ruflo-aidefence plugin; federation PII redaction. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20guardrails&system=ruflo&dimension=H4%20guardrails&current=input_filters%7Coutput_filters) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, other, swe` | medium | “Specialized agents for coding, testing, security, docs, architecture” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | Also trading/IoT domain plugins (other); browser plugin for testing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20target_domain&system=ruflo&dimension=M1%20target_domain&current=general_tool_use%7Cother%7Cswe) |
| M2 | `open_source` | `yes` | medium | “MIT - \[RuvNet\](https://github.com/ruvnet)” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† | LICENSE file not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20open_source&system=ruflo&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | low | “5 providers with failover” | [README.md](https://github.com/ruvnet/ruflo/blob/e21aa352fdc80fd2d3cc4e83404a76a18d118b96/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20model_agnostic&system=ruflo&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v3.38.20 e21aa352fdc80fd2d3cc4e83404a76a18d118b96 2026-08-24” | github:ruvnet/ruflo |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20primary_artifact&system=ruflo&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | No tag history in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20first_release_date&system=ruflo&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v3.38.20 @ e21aa352fdc80fd2d3cc4e83404a76a18d118b96 (2026-08-24)` | high | “ref: tag:v3.38.20 e21aa352fdc80fd2d3cc4e83404a76a18d118b96 2026-08-24” | github:ruvnet/ruflo |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20pinned_version&system=ruflo&dimension=M6%20pinned_version&current=v3.38.20%20%40%20e21aa352fdc80fd2d3cc4e83404a76a18d118b96%20%282026-08-24%29) |
| M7 | `stars` | `not_reported` |  |  |  | Star count not in bundle; requires gh api. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20stars&system=ruflo&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20network_policy&system=ruflo&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20replayability&system=ruflo&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20filesystem_access&system=ruflo&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20rollback&system=ruflo&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20state_persistence&system=ruflo&dimension=D3%20state_persistence&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20timeouts&system=ruflo&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20permission_model&system=ruflo&dimension=G4%20permission_model&current=not_reported)
8. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20context_compaction&system=ruflo&dimension=A3%20context_compaction&current=not_reported)
9. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20human_in_loop&system=ruflo&dimension=C5%20human_in_loop&current=not_reported)
10. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20edit_primitive&system=ruflo&dimension=B3%20edit_primitive&current=not_reported)
11. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20eval_hooks&system=ruflo&dimension=H3%20eval_hooks&current=not_reported)
12. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20retry_policy&system=ruflo&dimension=E2%20retry_policy&current=not_reported)
13. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20self_verification&system=ruflo&dimension=E1%20self_verification&current=not_reported)
14. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20short_term_state&system=ruflo&dimension=D1%20short_term_state&current=not_reported)
15. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20termination_condition&system=ruflo&dimension=F1%20termination_condition&current=not_reported)
16. A1 `system_prompt_style` (System-prompt style): 30.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20system_prompt_style&system=ruflo&dimension=A1%20system_prompt_style&current=not_reported)
17. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20env_context_strategy&system=ruflo&dimension=A2%20env_context_strategy&current=not_reported)
18. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20observation_format&system=ruflo&dimension=A4%20observation_format&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20%3Cdimension%3E&system=ruflo> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=ruflo>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
