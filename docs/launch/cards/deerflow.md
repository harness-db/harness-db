# DeerFlow: HARNESS-DB cell card

| | |
|---|---|
| System id | `deerflow` |
| Pinned version | [v2.0.0 @ `7e7f04107976`](https://github.com/bytedance/deer-flow/commit/7e7f0410797693cf882594555ba414e0361d4c6f) (2026-06-25) |
| Repository | <https://github.com/bytedance/deer-flow> |
| Stars (sampling-frame snapshot) | 82,541 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 24 coded, 14 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=deerflow> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | medium | “{subagent\_reminder}- Skill First: Always load the relevant skill before starting \*\*complex\*\* tasks.” | [docs/CODE\_CHANGE\_SUMMARY\_BY\_FILE.md (diff of backend/packages/harness/deerflow/agents/lead\_agent/prompt.py)@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/docs/CODE_CHANGE_SUMMARY_BY_FILE.md) | apply\_prompt\_template(subagent\_enabled) conditionally inserts sections; skills metadata injected. Line numbers not available in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20system_prompt_style&system=deerflow&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “The agent reads, writes, and edits files.” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | Inferred from README; file tree shows sandbox/search.py and rfc-grep-glob-tools.md. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20env_context_strategy&system=deerflow&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `summarize, tool_output_pruning` | low | “summarizing completed sub-tasks, offloading intermediate results to the filesystem, compressing what's no longer immediately relevant” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | File tree has summarization\_middleware.py and tool\_output\_budget\_middleware.py; contents not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20context_compaction&system=deerflow&dimension=A3%20context_compaction&current=summarize%7Ctool_output_pruning) |
| A4 | `observation_format` | `raw_text, screenshots` | low | “It can view images and, when configured safely, execute shell commands.” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | view\_image\_tool.py in file tree; image as observation inferred. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20observation_format&system=deerflow&dimension=A4%20observation_format&current=raw_text%7Cscreenshots) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | low | “\*\*Strong tool-use\*\* for reliable function calling and structured outputs” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | Built on LangChain tool calling; parser code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20tool_call_format&system=deerflow&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `not_reported` |  |  |  | Tool registry (tools/tools.py) content not in bundle; README lists core toolset web search, web fetch, file ops, bash. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20tool_count&system=deerflow&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | Edit tool definition (sandbox/tools.py) not in bundle; write\_file tool seen in frontend diff. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20edit_primitive&system=deerflow&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `mcp` | medium | “supports custom tools via MCP servers and Python functions” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | Native tools likely auto\_generated from LangChain Python functions, not verifiable in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20tool_schema_source&system=deerflow&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp, other` | high | “ACP agent entries are separate from model providers” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | MCP client in deerflow/mcp/client.py; ACP via invoke\_acp\_agent\_tool.py. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20protocol_standardization&system=deerflow&dimension=B5%20protocol_standardization&current=mcp%7Cother) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `react` | low | “Built on LangGraph and LangChain, it ships with everything an agent needs out of the box” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | Run loop code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20loop_primitives&system=deerflow&dimension=C1%20loop_primitives&current=react) |
| C2 | `planning_granularity` | `explicit_plan_object` | low | “is\_plan\_mode: false” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | todo\_middleware.py and frontend todos; plan mode off by default in example config. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20planning_granularity&system=deerflow&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `single` | medium | “subagent\_enabled: false” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | orchestrator\_workers reachable via subagent\_enabled (task\_tool). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20multi_agent_topology&system=deerflow&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `none` | medium | “subagent\_enabled: false” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | subagent\_spawn opt-in: 'The lead agent can spawn sub-agents on the fly'. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20delegation_mechanism&system=deerflow&dimension=C4%20delegation_mechanism&current=none) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | clarification\_tool exists (asks user) but approval-gate code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20human_in_loop&system=deerflow&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “The backend orchestrates agents that can produce \*\*artifacts\*\* (files/code) and \*\*todos\*\*.” | [docs/CODE\_CHANGE\_SUMMARY\_BY\_FILE.md (frontend/CLAUDE.md diff)@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/docs/CODE_CHANGE_SUMMARY_BY_FILE.md) | agents/thread\_state.py in tree. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20short_term_state&system=deerflow&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `file_notes, skill_library` | medium | “Across sessions, DeerFlow builds a persistent memory of your profile, preferences, and accumulated knowledge.” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | Skills loaded from skills/ library. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20long_term_memory&system=deerflow&dimension=D2%20long_term_memory&current=file_notes%7Cskill_library) |
| D3 | `state_persistence` | `full_resume` | low | “Manage threads and conversation history” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | LangGraph checkpointer (runtime/checkpointer) in tree; code not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20state_persistence&system=deerflow&dimension=D3%20state_persistence&current=full_resume) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | No verification code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20self_verification&system=deerflow&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20retry_policy&system=deerflow&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20rollback&system=deerflow&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `max_steps, model_declared, stall_detection` | low | “recursion\_limit: 100” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | loop\_detection\_middleware.py in tree. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20termination_condition&system=deerflow&dimension=F1%20termination_condition&current=max_steps%7Cmodel_declared%7Cstall_detection) |
| F2 | `cost_controls` | `not_reported` |  |  |  | token\_usage tracking exists; budget code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20cost_controls&system=deerflow&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20timeouts&system=deerflow&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “With \`LocalSandboxProvider\`, file tools still map to per-thread directories on the host, but host \`bash\` is disabled by default” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | Default provider unclear; container (AioSandboxProvider) and Kubernetes remote reachable. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20execution_isolation&system=deerflow&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `scoped` | medium | “file tools still map to per-thread directories on the host” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20filesystem_access&system=deerflow&dimension=G2%20filesystem_access&current=scoped) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20network_policy&system=deerflow&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | guardrails module exists; defaults not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20permission_model&system=deerflow&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `structured_traces` | medium | “When enabled, all LLM calls, agent runs, and tool executions are traced and visible in the LangSmith dashboard.” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | LangSmith/Langfuse off by default. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20tracing&system=deerflow&dimension=H1%20tracing&current=structured_traces) |
| H2 | `replayability` | `not_reported` |  |  |  | replay-e2e workflow is test infra; code not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20replayability&system=deerflow&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20eval_hooks&system=deerflow&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `action_policies` | low | “host \`bash\` is disabled by default because it is not a secure isolation boundary” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) | guardrails/ and GUARDRAILS.md in tree. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20guardrails&system=deerflow&dimension=H4%20guardrails&current=action_policies) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, research, swe, web` | high | “An open-source long-horizon SuperAgent harness that researches, codes, and creates.” | repo description@7e7f041 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20target_domain&system=deerflow&dimension=M1%20target_domain&current=general_tool_use%7Cresearch%7Cswe%7Cweb) |
| M2 | `open_source` | `yes` | high | “This project is open source and available under the \[MIT License\](./LICENSE).” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20open_source&system=deerflow&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “DeerFlow is model-agnostic” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20model_agnostic&system=deerflow&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “DeerFlow 2.0 is a ground-up rewrite.” | [README.md@7e7f041](https://github.com/bytedance/deer-flow/blob/7e7f0410797693cf882594555ba414e0361d4c6f/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20primary_artifact&system=deerflow&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | First 2.x tag date not in bundle; v2 launched around Feb 2026 per README. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20first_release_date&system=deerflow&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v2.0.0 @ 7e7f0410797693cf882594555ba414e0361d4c6f (2026-06-25)` | high | “ref: tag:v2.0.0 7e7f0410797693cf882594555ba414e0361d4c6f 2026-06-25” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20pinned_version&system=deerflow&dimension=M6%20pinned_version&current=v2.0.0%20%40%207e7f0410797693cf882594555ba414e0361d4c6f%20%282026-06-25%29) |
| M7 | `stars` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20stars&system=deerflow&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20network_policy&system=deerflow&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20replayability&system=deerflow&dimension=H2%20replayability&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20rollback&system=deerflow&dimension=E3%20rollback&current=not_reported)
4. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20timeouts&system=deerflow&dimension=F3%20timeouts&current=not_reported)
5. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20permission_model&system=deerflow&dimension=G4%20permission_model&current=not_reported)
6. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20cost_controls&system=deerflow&dimension=F2%20cost_controls&current=not_reported)
7. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20tool_count&system=deerflow&dimension=B2%20tool_count&current=not_reported)
8. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20human_in_loop&system=deerflow&dimension=C5%20human_in_loop&current=not_reported)
9. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20edit_primitive&system=deerflow&dimension=B3%20edit_primitive&current=not_reported)
10. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20eval_hooks&system=deerflow&dimension=H3%20eval_hooks&current=not_reported)
11. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20retry_policy&system=deerflow&dimension=E2%20retry_policy&current=not_reported)
12. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20self_verification&system=deerflow&dimension=E1%20self_verification&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20%3Cdimension%3E&system=deerflow> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=deerflow>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
