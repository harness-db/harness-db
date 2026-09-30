# Hermes Agent: HARNESS-DB cell card

| | |
|---|---|
| System id | `hermes-agent` |
| Pinned version | [v2026.8.31 @ `29112bef0992`](https://github.com/nousresearch/hermes-agent/commit/29112bef099274229cadff79cdff7bf7b99c4b77) (2026-08-31) |
| Repository | <https://github.com/nousresearch/hermes-agent> |
| Stars (sampling-frame snapshot) | 246,141 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 13 coded, 25 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=hermes-agent> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | low | “Project context that shapes every conversation” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | Context files, SOUL.md persona, skills, memory; agent/prompt\_builder.py and agent/system\_prompt.py exist in file tree but not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20system_prompt_style&system=hermes-agent&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | Tool definitions and instance templates not in evidence bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20env_context_strategy&system=hermes-agent&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `summarize` | low | “Compress context / check usage” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | /compress command; agent/context\_compressor.py, agent/native\_compaction.py in tree (not opened); other mechanisms unverified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20context_compaction&system=hermes-agent&dimension=A3%20context_compaction&current=summarize) |
| A4 | `observation_format` | `not_reported` |  |  |  | Observation conversion code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20observation_format&system=hermes-agent&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | Parser code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tool_call_format&system=hermes-agent&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | README says '40+ tools, toolset system' but default exposed list not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tool_count&system=hermes-agent&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | Edit tool definition not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20edit_primitive&system=hermes-agent&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `mcp` | medium | “Connect any MCP server for extended capabilities” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | Native tool schema source not in bundle; only MCP confirmed. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tool_schema_source&system=hermes-agent&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp, other` | medium | “Connect any MCP server for extended capabilities” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | other = ACP; acp\_adapter/server.py in file tree (not opened). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20protocol_standardization&system=hermes-agent&dimension=B5%20protocol_standardization&current=mcp%7Cother) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `not_reported` |  |  |  | Run loop agent/conversation\_loop.py listed but not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20loop_primitives&system=hermes-agent&dimension=C1%20loop_primitives&current=not_reported) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | agent/plan\_prompt.py in tree, contents not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20planning_granularity&system=hermes-agent&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `not_reported` |  |  |  | README: 'Spawn isolated subagents for parallel workstreams'; default topology config not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20multi_agent_topology&system=hermes-agent&dimension=C3%20multi_agent_topology&current=not_reported) |
| C4 | `delegation_mechanism` | `subagent_spawn` | low | “Spawn isolated subagents for parallel workstreams.” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | Whether default-on not verified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20delegation_mechanism&system=hermes-agent&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `on_permission` | low | “Command approval, DM pairing, container isolation” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | Default policy not verified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20human_in_loop&system=hermes-agent&dimension=C5%20human_in_loop&current=on_permission) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  | State object not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20short_term_state&system=hermes-agent&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `episodic_db, file_notes, skill_library` | medium | “Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall.” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | MEMORY.md/USER.md notes; FTS5 session DB. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20long_term_memory&system=hermes-agent&dimension=D2%20long_term_memory&current=episodic_db%7Cfile_notes%7Cskill_library) |
| D3 | `state_persistence` | `not_reported` |  |  |  | Resume code path not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20state_persistence&system=hermes-agent&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | agent/verify/, agent/review\_engine.py in tree, not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20self_verification&system=hermes-agent&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  | /retry is user-triggered; harness retry policy not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20retry_policy&system=hermes-agent&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  | /undo undoes conversation turn, not files; file rollback mechanism not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20rollback&system=hermes-agent&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  | agent/iteration\_budget.py, repetition\_guard.py in tree, not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20termination_condition&system=hermes-agent&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  | agent/prompt\_caching.py in tree, not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20cost_controls&system=hermes-agent&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  | No timeout config in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20timeouts&system=hermes-agent&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “Seven terminal backends — local, Docker, SSH, Singularity, Modal, Daytona, and Vercel Sandbox.” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | Local assumed default (listed first); container/remote backends reachable. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20execution_isolation&system=hermes-agent&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `not_reported` |  |  |  | No filesystem scoping config in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20filesystem_access&system=hermes-agent&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  | Network config not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20network_policy&system=hermes-agent&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | Command approval/allowlist exists per README ('Command allowlist — approval patterns'); default policy not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20permission_model&system=hermes-agent&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  | agent/monitoring/otlp\_exporter.py and agent/trajectory.py in tree, not opened; likely opentelemetry. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tracing&system=hermes-agent&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  | Replay code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20replayability&system=hermes-agent&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | Repo truncated to 400 of 10925 paths. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20eval_hooks&system=hermes-agent&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  | agent/tool\_guardrails.py, agent/redact.py in tree, not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20guardrails&system=hermes-agent&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, swe, web` | low | “web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), cloud browser (Browser Use)” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† | General personal agent; swe inferred from terminal/coding tools. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20target_domain&system=hermes-agent&dimension=M1%20target_domain&current=general_tool_use%7Cswe%7Cweb) |
| M2 | `open_source` | `yes` | high | “MIT — see \[LICENSE\](LICENSE).” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20open_source&system=hermes-agent&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “Use any model you want” | [README.md](https://github.com/nousresearch/hermes-agent/blob/29112bef099274229cadff79cdff7bf7b99c4b77/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20model_agnostic&system=hermes-agent&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v2026.8.31 29112bef099274229cadff79cdff7bf7b99c4b77 2026-08-31” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20primary_artifact&system=hermes-agent&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | First tag not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20first_release_date&system=hermes-agent&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v2026.8.31 @ 29112bef099274229cadff79cdff7bf7b99c4b77 (2026-08-31)` | high | “ref: tag:v2026.8.31 29112bef099274229cadff79cdff7bf7b99c4b77 2026-08-31” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20pinned_version&system=hermes-agent&dimension=M6%20pinned_version&current=v2026.8.31%20%40%2029112bef099274229cadff79cdff7bf7b99c4b77%20%282026-08-31%29) |
| M7 | `stars` | `not_reported` |  |  |  | Star count not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20stars&system=hermes-agent&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20network_policy&system=hermes-agent&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20replayability&system=hermes-agent&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20filesystem_access&system=hermes-agent&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20rollback&system=hermes-agent&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20state_persistence&system=hermes-agent&dimension=D3%20state_persistence&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20timeouts&system=hermes-agent&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20permission_model&system=hermes-agent&dimension=G4%20permission_model&current=not_reported)
8. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20cost_controls&system=hermes-agent&dimension=F2%20cost_controls&current=not_reported)
9. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tool_count&system=hermes-agent&dimension=B2%20tool_count&current=not_reported)
10. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20guardrails&system=hermes-agent&dimension=H4%20guardrails&current=not_reported)
11. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20edit_primitive&system=hermes-agent&dimension=B3%20edit_primitive&current=not_reported)
12. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20eval_hooks&system=hermes-agent&dimension=H3%20eval_hooks&current=not_reported)
13. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tracing&system=hermes-agent&dimension=H1%20tracing&current=not_reported)
14. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20retry_policy&system=hermes-agent&dimension=E2%20retry_policy&current=not_reported)
15. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20tool_call_format&system=hermes-agent&dimension=B1%20tool_call_format&current=not_reported)
16. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20self_verification&system=hermes-agent&dimension=E1%20self_verification&current=not_reported)
17. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20short_term_state&system=hermes-agent&dimension=D1%20short_term_state&current=not_reported)
18. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20termination_condition&system=hermes-agent&dimension=F1%20termination_condition&current=not_reported)
19. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20env_context_strategy&system=hermes-agent&dimension=A2%20env_context_strategy&current=not_reported)
20. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20observation_format&system=hermes-agent&dimension=A4%20observation_format&current=not_reported)
21. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20planning_granularity&system=hermes-agent&dimension=C2%20planning_granularity&current=not_reported)
22. C3 `multi_agent_topology` (Multi-agent topology): 1.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20multi_agent_topology&system=hermes-agent&dimension=C3%20multi_agent_topology&current=not_reported)
23. C1 `loop_primitives` (Loop primitive(s)): 1.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20loop_primitives&system=hermes-agent&dimension=C1%20loop_primitives&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20%3Cdimension%3E&system=hermes-agent> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=hermes-agent>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
