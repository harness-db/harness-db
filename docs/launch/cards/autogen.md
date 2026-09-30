# AutoGen (AssistantAgent + UserProxyAgent): HARNESS-DB cell card

| | |
|---|---|
| System id | `autogen` |
| Pinned version | [python-v0.7.5 @ `83afbf5857aa`](https://github.com/microsoft/autogen/commit/83afbf5857aac683340d4c692194e548b1e8edda) (2025-09-30) |
| Repository | <https://github.com/microsoft/autogen> |
| Papers | [arXiv:2308.08155](https://arxiv.org/abs/2308.08155), [arXiv:2408.15247](https://arxiv.org/abs/2408.15247), [arXiv:2411.04468](https://arxiv.org/abs/2411.04468) |
| Stars (sampling-frame snapshot) | 61,061 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 15 coded, 23 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-24 |
| Explorer | <https://harness-db.github.io/harness-db/#system=autogen> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `not_reported` |  |  |  | Prompt-building code not in truncated bundle; README shows system\_message parameter only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20system_prompt_style&system=autogen&dimension=A1%20system_prompt_style&current=not_reported) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | General framework; no default tool list or task template in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20env_context_strategy&system=autogen&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | No context/history processor code in the truncated bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20context_compaction&system=autogen&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | Observation conversion code not in evidence; Magentic-One docs mention a11y tree and set-of-marks for WebSurfer (extension agent). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20observation_format&system=autogen&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `code_as_action, native_function_calling` | low | “the default user proxy agent in AutoGen is able to execute code suggested by LLMs, or make LLM-suggested function calls.” | [paper arXiv:2308.08155 Sec. 2.1](https://arxiv.org/abs/2308.08155) | Parser code not in bundle; inferred from paper prose (v0.2 era). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20tool_call_format&system=autogen&dimension=B1%20tool_call_format&current=code_as_action%7Cnative_function_calling) |
| B2 | `tool_count` | `not_reported` |  |  |  | README Hello World AssistantAgent passes no tools; tool registry code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20tool_count&system=autogen&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | No edit tool definition in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20edit_primitive&system=autogen&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `mcp` | medium | “from autogen\_ext.tools.mcp import McpWorkbench, StdioServerParams” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) | Only MCP schema source visible; function-tool schema generation code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20tool_schema_source&system=autogen&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp` | high | “from autogen\_ext.tools.mcp import McpWorkbench, StdioServerParams” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20protocol_standardization&system=autogen&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | medium | “implements message passing, event-driven agents, and local and distributed runtime” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) | react inferred from max\_tool\_iterations tool loop in README; run loop code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20loop_primitives&system=autogen&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | Default AssistantAgent planning not evidenced; Magentic-One Task Ledger is opt-in team. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20planning_granularity&system=autogen&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `single` | medium | “agent = AssistantAgent("assistant", model\_client=model\_client)” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) | Teams (SelectorGroupChat, Swarm, MagenticOneGroupChat, GraphFlow) reachable; paper default is assistant+user proxy two-agent chat. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20multi_agent_topology&system=autogen&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `none` | medium | “agent = AssistantAgent("assistant", model\_client=model\_client)” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) | AgentTool (subagent\_spawn-like) and Swarm handoffs opt-in. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20delegation_mechanism&system=autogen&dimension=C4%20delegation_mechanism&current=none) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | Paper describes configurable human\_input\_mode (v0.2); v0.7.5 code not in bundle; approval\_func exists for MagenticOne. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20human_in_loop&system=autogen&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20short_term_state&system=autogen&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | Docs list a Memory feature; implementation not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20long_term_memory&system=autogen&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20state_persistence&system=autogen&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20self_verification&system=autogen&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20retry_policy&system=autogen&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20rollback&system=autogen&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `max_steps` | low | “max\_tool\_iterations=10,” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) | Termination conditions code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20termination_condition&system=autogen&dimension=F1%20termination_condition&current=max_steps) |
| F2 | `cost_controls` | `caching` | low | “AutoGen also offers enhanced LLM inference features such as result caching, error handling, message templating” | [paper arXiv:2308.08155 Sec. 2.1](https://arxiv.org/abs/2308.08155) | Paper describes v0.2; not verified in pinned code. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20cost_controls&system=autogen&dimension=F2%20cost_controls&current=caching) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20timeouts&system=autogen&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | Code executor config not in bundle; docs mention LocalCommandLineCodeExecutor and recommend containers. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20execution_isolation&system=autogen&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20filesystem_access&system=autogen&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20network_policy&system=autogen&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20permission_model&system=autogen&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `logs` | low | “Log traces and internal messages” | AgentChat docs (grey:autogen) | OpenTelemetry support not evidenced in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20tracing&system=autogen&dimension=H1%20tracing&current=logs) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20replayability&system=autogen&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `built_in` | high | “\[AutoGen Bench\](./python/packages/agbench/) provides a benchmarking suite for evaluating agent performance.” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20eval_hooks&system=autogen&dimension=H3%20eval_hooks&current=built_in) |
| H4 | `guardrails` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20guardrails&system=autogen&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, swe, web` | medium | “a variety of tasks that require web browsing, code execution, and file handling.” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20target_domain&system=autogen&dimension=M1%20target_domain&current=general_tool_use%7Cswe%7Cweb) |
| M2 | `open_source` | `not_reported` |  |  |  | LICENSE file not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20open_source&system=autogen&dimension=M2%20open_source&current=not_reported) |
| M3 | `model_agnostic` | `yes` | medium | “It support specific implementation of LLM clients (e.g., OpenAI, AzureOpenAI)” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20model_agnostic&system=autogen&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “If you are upgrading from AutoGen v0.2, please refer to the \[Migration Guide\]” | [README.md@83afbf5857aa](https://github.com/microsoft/autogen/blob/83afbf5857aac683340d4c692194e548b1e8edda/README.md) | v0.7.5 postdates the 2023 paper (v0.2 design). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20primary_artifact&system=autogen&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | No tag history in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20first_release_date&system=autogen&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `python-v0.7.5 @ 83afbf5857aac683340d4c692194e548b1e8edda (2025-09-30)` | high | “ref: tag:python-v0.7.5 83afbf5857aac683340d4c692194e548b1e8edda 2025-09-30” | github:microsoft/autogen metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20pinned_version&system=autogen&dimension=M6%20pinned_version&current=python-v0.7.5%20%40%2083afbf5857aac683340d4c692194e548b1e8edda%20%282025-09-30%29) |
| M7 | `stars` | `61061` | medium | “stars: 61061” | repository evidence header grey:autogen | Other headers report 61047/61059; retrieval date not given. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20stars&system=autogen&dimension=M7%20stars&current=61061) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20network_policy&system=autogen&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20replayability&system=autogen&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20filesystem_access&system=autogen&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20rollback&system=autogen&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20state_persistence&system=autogen&dimension=D3%20state_persistence&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20timeouts&system=autogen&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20permission_model&system=autogen&dimension=G4%20permission_model&current=not_reported)
8. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20context_compaction&system=autogen&dimension=A3%20context_compaction&current=not_reported)
9. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20tool_count&system=autogen&dimension=B2%20tool_count&current=not_reported)
10. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20human_in_loop&system=autogen&dimension=C5%20human_in_loop&current=not_reported)
11. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20guardrails&system=autogen&dimension=H4%20guardrails&current=not_reported)
12. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20edit_primitive&system=autogen&dimension=B3%20edit_primitive&current=not_reported)
13. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20long_term_memory&system=autogen&dimension=D2%20long_term_memory&current=not_reported)
14. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20execution_isolation&system=autogen&dimension=G1%20execution_isolation&current=not_reported)
15. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20retry_policy&system=autogen&dimension=E2%20retry_policy&current=not_reported)
16. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20self_verification&system=autogen&dimension=E1%20self_verification&current=not_reported)
17. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20short_term_state&system=autogen&dimension=D1%20short_term_state&current=not_reported)
18. A1 `system_prompt_style` (System-prompt style): 30.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20system_prompt_style&system=autogen&dimension=A1%20system_prompt_style&current=not_reported)
19. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20env_context_strategy&system=autogen&dimension=A2%20env_context_strategy&current=not_reported)
20. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20observation_format&system=autogen&dimension=A4%20observation_format&current=not_reported)
21. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20planning_granularity&system=autogen&dimension=C2%20planning_granularity&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20%3Cdimension%3E&system=autogen> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=autogen>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
