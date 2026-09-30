# CrewAI: HARNESS-DB cell card

| | |
|---|---|
| System id | `crewai` |
| Pinned version | [1.15.18 @ `4bc5d2924218`](https://github.com/crewaiinc/crewai/commit/4bc5d2924218e892bd0bc91b46352b49b0d3a740) (2026-08-27) |
| Repository | <https://github.com/crewaiinc/crewai> |
| Stars (sampling-frame snapshot) | 58,663 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 14 coded, 24 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=crewai> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `templated` | low | “Use \`{placeholder}\` values in agent and task text, then set defaults in \`crew.jsonc\` under \`inputs\`.” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† | Role/goal/backstory placeholders rendered at kickoff; the prompt assembly code was not in the evidence bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20system_prompt_style&system=crewai&dimension=A1%20system_prompt_style&current=templated) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | No agent prompt-building code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20env_context_strategy&system=crewai&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | No executor or context-window code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20context_compaction&system=crewai&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | No observation conversion code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20observation_format&system=crewai&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | No parser code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tool_call_format&system=crewai&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | Tools are user-supplied per agent; there is no default tool list in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tool_count&system=crewai&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | The file tree lists docs for filewritetool; no tool definition source is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20edit_primitive&system=crewai&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  | No schema code is in the bundle; MCP docs exist (docs/edge/en/mcp/overview.mdx) but were not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tool_schema_source&system=crewai&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `a2a, mcp` | medium | “Use tools, memory, knowledge, checkpointing, async execution, and MCP/A2A support for more capable production agents.” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20protocol_standardization&system=crewai&dimension=B5%20protocol_standardization&current=a2a%7Cmcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, fixed_pipeline, react` | low | “It gives developers autonomous agent collaboration through Crews and precise, event-driven control through Flows.” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† | The sequential process is the default (fixed\_pipeline); react is inferred for the agent loop; Flows are event\_driven. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20loop_primitives&system=crewai&dimension=C1%20loop_primitives&current=event_driven%7Cfixed_pipeline%7Creact) |
| C2 | `planning_granularity` | `implicit` | low | “In addition to the sequential process, you can use the hierarchical process, which automatically assigns a manager to the defined crew to properly coordinate the planning” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† | docs/edge/en/concepts/planning.mdx exists but was not included in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20planning_granularity&system=crewai&dimension=C2%20planning_granularity&current=implicit) |
| C3 | `multi_agent_topology` | `pipeline` | medium | “"process": "sequential",” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† | The default scaffold is a sequential hand-off. The hierarchical manager process (orchestrator\_workers) is reachable by config. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20multi_agent_topology&system=crewai&dimension=C3%20multi_agent_topology&current=pipeline) |
| C4 | `delegation_mechanism` | `role_handoff` | low | “Dynamic task delegation and collaboration” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† | The tasks pass context between agents; the delegation mechanism code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20delegation_mechanism&system=crewai&dimension=C4%20delegation_mechanism&current=role_handoff) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | README claims human-in-the-loop support; the mechanism docs were not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20human_in_loop&system=crewai&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20short_term_state&system=crewai&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | README mentions memory and skills; the memory docs content is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20long_term_memory&system=crewai&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `checkpoint` | low | “Add deterministic steps, human input, structured outputs, and checkpointing as your system grows.” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20state_persistence&system=crewai&dimension=D3%20state_persistence&current=checkpoint) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20self_verification&system=crewai&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20retry_policy&system=crewai&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20rollback&system=crewai&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20termination_condition&system=crewai&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20cost_controls&system=crewai&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20timeouts&system=crewai&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | No execution backend code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20execution_isolation&system=crewai&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20filesystem_access&system=crewai&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20network_policy&system=crewai&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20permission_model&system=crewai&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `opentelemetry` | medium | “Users can disable telemetry by setting the environment variable OTEL\_SDK\_DISABLED to true.” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† | OTEL SDK is used for telemetry; traces are available via third-party integrations. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tracing&system=crewai&dimension=H1%20tracing&current=opentelemetry) |
| H2 | `replayability` | `partial` | low | “docs/edge/en/learn/replay-tasks-from-latest-crew-kickoff.mdx” | file tree | The file is named in the file tree only; its content is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20replayability&system=crewai&dimension=H2%20replayability&current=partial) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | docs/edge/en/concepts/testing.mdx exists but its content is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20eval_hooks&system=crewai&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  | Guardrails are mentioned in the docs but the mechanism is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20guardrails&system=crewai&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use` | medium | “Framework for orchestrating role-playing, autonomous AI agents.” | repo description |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20target_domain&system=crewai&dimension=M1%20target_domain&current=general_tool_use) |
| M2 | `open_source` | `yes` | high | “CrewAI is released under the \[MIT License\]” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20open_source&system=crewai&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “CrewAI supports using various LLMs through a variety of connection options.” | [README.md](https://github.com/crewaiinc/crewai/blob/4bc5d2924218e892bd0bc91b46352b49b0d3a740/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20model_agnostic&system=crewai&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:1.15.18 4bc5d2924218e892bd0bc91b46352b49b0d3a740 2026-08-27” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20primary_artifact&system=crewai&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | The bundle has no tag history. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20first_release_date&system=crewai&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `1.15.18 @ 4bc5d2924218e892bd0bc91b46352b49b0d3a740 (2026-08-27)` | high | “ref: tag:1.15.18 4bc5d2924218e892bd0bc91b46352b49b0d3a740 2026-08-27” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20pinned_version&system=crewai&dimension=M6%20pinned_version&current=1.15.18%20%40%204bc5d2924218e892bd0bc91b46352b49b0d3a740%20%282026-08-27%29) |
| M7 | `stars` | `not_reported` |  |  |  | The bundle has no star count. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20stars&system=crewai&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20network_policy&system=crewai&dimension=G3%20network_policy&current=not_reported)
2. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20filesystem_access&system=crewai&dimension=G2%20filesystem_access&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20rollback&system=crewai&dimension=E3%20rollback&current=not_reported)
4. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20timeouts&system=crewai&dimension=F3%20timeouts&current=not_reported)
5. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20permission_model&system=crewai&dimension=G4%20permission_model&current=not_reported)
6. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20cost_controls&system=crewai&dimension=F2%20cost_controls&current=not_reported)
7. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20context_compaction&system=crewai&dimension=A3%20context_compaction&current=not_reported)
8. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tool_count&system=crewai&dimension=B2%20tool_count&current=not_reported)
9. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20human_in_loop&system=crewai&dimension=C5%20human_in_loop&current=not_reported)
10. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20guardrails&system=crewai&dimension=H4%20guardrails&current=not_reported)
11. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tool_schema_source&system=crewai&dimension=B4%20tool_schema_source&current=not_reported)
12. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20edit_primitive&system=crewai&dimension=B3%20edit_primitive&current=not_reported)
13. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20long_term_memory&system=crewai&dimension=D2%20long_term_memory&current=not_reported)
14. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20eval_hooks&system=crewai&dimension=H3%20eval_hooks&current=not_reported)
15. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20execution_isolation&system=crewai&dimension=G1%20execution_isolation&current=not_reported)
16. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20retry_policy&system=crewai&dimension=E2%20retry_policy&current=not_reported)
17. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20tool_call_format&system=crewai&dimension=B1%20tool_call_format&current=not_reported)
18. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20self_verification&system=crewai&dimension=E1%20self_verification&current=not_reported)
19. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20short_term_state&system=crewai&dimension=D1%20short_term_state&current=not_reported)
20. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20termination_condition&system=crewai&dimension=F1%20termination_condition&current=not_reported)
21. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20env_context_strategy&system=crewai&dimension=A2%20env_context_strategy&current=not_reported)
22. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20observation_format&system=crewai&dimension=A4%20observation_format&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20%3Cdimension%3E&system=crewai> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=crewai>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
