# daily\_stock\_analysis (DSA): HARNESS-DB cell card

| | |
|---|---|
| System id | `daily-stock-analysis` |
| Pinned version | [v3.31.0 @ `9ab79b82992d`](https://github.com/zhulinsen/daily_stock_analysis/commit/9ab79b82992d688f5c27e7c4c74496138d8a8d79) (2026-08-23) |
| Repository | <https://github.com/zhulinsen/daily_stock_analysis> |
| Papers | [arXiv:2608.26990](https://arxiv.org/abs/2608.26990) |
| Stars (sampling-frame snapshot) | 65,297 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 21 coded, 17 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=daily-stock-analysis> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `not_reported` |  |  |  | System prompt construction code not in the truncated evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20system_prompt_style&system=daily-stock-analysis&dimension=A1%20system_prompt_style&current=not_reported) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “Provides \`\`run\_agent\_loop\`\`, the single authoritative implementation of the ReAct execute-loop” | [src/agent/runner.py:5-6@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/src/agent/runner.py#L5-L6) | Environment is market data; agent fetches via tools (get\_realtime\_quote etc.); default report profile injects bounded evidence context instead. Closest value; domain mismatch. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20env_context_strategy&system=daily-stock-analysis&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `not_reported` |  |  |  | No history-processing code in truncated evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20context_compaction&system=daily-stock-analysis&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `structured_json` | low | “serialize\_tool\_result,” | [src/agent/runner.py:42@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/src/agent/runner.py#L42) | Tool results serialized; exact format inferred. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20observation_format&system=daily-stock-analysis&dimension=A4%20observation_format&current=structured_json) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | low | “from src.agent.llm\_adapter import LLMToolAdapter” | [src/agent/runner.py:28@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/src/agent/runner.py#L28) | Inferred from tool adapter and ToolRegistry; parser not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20tool_call_format&system=daily-stock-analysis&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `16` | medium | “"get\_stock\_backtest\_summary": "获取个股回测数据",” | [api/v1/endpoints/agent.py:24-41@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/api/v1/endpoints/agent.py#L24-L41) | Count of TOOL\_DISPLAY\_NAMES entries; actual registry not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20tool_count&system=daily-stock-analysis&dimension=B2%20tool_count&current=16) |
| B3 | `edit_primitive` | `none` | medium | “"get\_realtime\_quote": "获取实时行情",” | [api/v1/endpoints/agent.py:24-41@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/api/v1/endpoints/agent.py#L24-L41) | Tool list contains only data/analysis tools, no file edit tool. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20edit_primitive&system=daily-stock-analysis&dimension=B3%20edit_primitive&current=none) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  | Tool schema generation code not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20tool_schema_source&system=daily-stock-analysis&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `not_reported` |  |  |  | No grep over dependencies available. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20protocol_standardization&system=daily-stock-analysis&dimension=B5%20protocol_standardization&current=not_reported) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | medium | “Provides \`\`run\_agent\_loop\`\`, the single authoritative implementation of the ReAct execute-loop” | [src/agent/runner.py:5-6@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/src/agent/runner.py#L5-L6) | Default report profile is a fixed pipeline; agentic multi-agent orchestrator is also a pipeline. event\_driven from progress callbacks/SSE is weak; fixed\_pipeline could apply. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20loop_primitives&system=daily-stock-analysis&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `implicit` | low | “The agent is deciding the next action.” | [docs/agent-stream-events.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/docs/agent-stream-events.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20planning_granularity&system=daily-stock-analysis&dimension=C2%20planning_granularity&current=implicit) |
| C3 | `multi_agent_topology` | `single` | low | “支持自定义策略文件与多 Agent 编排（实验性）” | [README.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/README.md)† | Multi-agent orchestrator (technical/intelligence/risk/decision roles, pipeline) is experimental opt-in. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20multi_agent_topology&system=daily-stock-analysis&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `none` | low | “支持自定义策略文件与多 Agent 编排（实验性）” | [README.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/README.md)† | Opt-in orchestrator pipeline hand-off. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20delegation_mechanism&system=daily-stock-analysis&dimension=C4%20delegation_mechanism&current=none) |
| C5 | `human_in_loop` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20human_in_loop&system=daily-stock-analysis&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `conversation_only` | low | “Remain stateless — all mutable state lives in the caller” | [src/agent/runner.py:13@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/src/agent/runner.py#L13) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20short_term_state&system=daily-stock-analysis&dimension=D1%20short_term_state&current=conversation_only) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | Skills are strategy definitions; persistence code not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20long_term_memory&system=daily-stock-analysis&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20state_persistence&system=daily-stock-analysis&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | Paper describes schema validation and RiskGuard, not verification in this schema's sense. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20self_verification&system=daily-stock-analysis&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20retry_policy&system=daily-stock-analysis&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20rollback&system=daily-stock-analysis&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  | Loop body truncated; orchestrator has pipeline timeout. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20termination_condition&system=daily-stock-analysis&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `token_budget` | low | “The orchestrator stopped because the stage or pipeline budget expired.” | [docs/agent-stream-events.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/docs/agent-stream-events.md)† | Budget appears time-based; caching (tool cache key) also plausible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20cost_controls&system=daily-stock-analysis&dimension=F2%20cost_controls&current=token_budget) |
| F3 | `timeouts` | `per_run` | medium | “The orchestrator stopped because the stage or pipeline budget expired.” | [docs/agent-stream-events.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/docs/agent-stream-events.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20timeouts&system=daily-stock-analysis&dimension=F3%20timeouts&current=per_run) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20execution_isolation&system=daily-stock-analysis&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20filesystem_access&system=daily-stock-analysis&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20network_policy&system=daily-stock-analysis&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20permission_model&system=daily-stock-analysis&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `structured_traces` | medium | “SSE payload is a JSON object with a top-level \`type\` field.” | [docs/agent-stream-events.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/docs/agent-stream-events.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20tracing&system=daily-stock-analysis&dimension=H1%20tracing&current=structured_traces) |
| H2 | `replayability` | `none` | medium | “The current artifact does not guarantee exact replay, a full tool and model event trace, or claim-level provenance.” | paper Sec. 6.3 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20replayability&system=daily-stock-analysis&dimension=H2%20replayability&current=none) |
| H3 | `eval_hooks` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20eval_hooks&system=daily-stock-analysis&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `action_policies` | low | “\_guard\_tool\_stock\_scope,” | [src/agent/runner.py:37@9ab79b82992d](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/src/agent/runner.py#L37) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20guardrails&system=daily-stock-analysis&dimension=H4%20guardrails&current=action_policies) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `other` | high | “DSA: Evidence-Aware LLM-Agent Orchestration for Multi-Market Stock Research” | paper title | Financial stock research. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20target_domain&system=daily-stock-analysis&dimension=M1%20target_domain&current=other) |
| M2 | `open_source` | `yes` | high | “\[MIT License\](LICENSE) © 2026 ZhuLinsen” | [README.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/README.md)† | AlphaSift-derived parts Apache 2.0. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20open_source&system=daily-stock-analysis&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | medium | “LiteLLM route resolution” | [docs/agent-stream-events.md](https://github.com/zhulinsen/daily_stock_analysis/blob/9ab79b82992d688f5c27e7c4c74496138d8a8d79/docs/agent-stream-events.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20model_agnostic&system=daily-stock-analysis&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | medium | “The public repository is a moving implementation” | paper Sec. 4 | Paper evaluated revision 0ca56cbe (2026-08-26), postdating pinned tag. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20primary_artifact&system=daily-stock-analysis&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20first_release_date&system=daily-stock-analysis&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v3.31.0 @ 9ab79b82992d688f5c27e7c4c74496138d8a8d79 (2026-08-23)` | high | “ref: tag:v3.31.0 9ab79b82992d688f5c27e7c4c74496138d8a8d79 2026-08-23” | repository header |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20pinned_version&system=daily-stock-analysis&dimension=M6%20pinned_version&current=v3.31.0%20%40%209ab79b82992d688f5c27e7c4c74496138d8a8d79%20%282026-08-23%29) |
| M7 | `stars` | `65297` | medium | “stars: 65297” | repository header | Date of star count not stated in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20stars&system=daily-stock-analysis&dimension=M7%20stars&current=65297) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20network_policy&system=daily-stock-analysis&dimension=G3%20network_policy&current=not_reported)
2. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20filesystem_access&system=daily-stock-analysis&dimension=G2%20filesystem_access&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20rollback&system=daily-stock-analysis&dimension=E3%20rollback&current=not_reported)
4. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20state_persistence&system=daily-stock-analysis&dimension=D3%20state_persistence&current=not_reported)
5. B5 `protocol_standardization` (Protocol standardization): 84.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20protocol_standardization&system=daily-stock-analysis&dimension=B5%20protocol_standardization&current=not_reported)
6. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20permission_model&system=daily-stock-analysis&dimension=G4%20permission_model&current=not_reported)
7. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20context_compaction&system=daily-stock-analysis&dimension=A3%20context_compaction&current=not_reported)
8. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20human_in_loop&system=daily-stock-analysis&dimension=C5%20human_in_loop&current=not_reported)
9. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20tool_schema_source&system=daily-stock-analysis&dimension=B4%20tool_schema_source&current=not_reported)
10. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20long_term_memory&system=daily-stock-analysis&dimension=D2%20long_term_memory&current=not_reported)
11. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20eval_hooks&system=daily-stock-analysis&dimension=H3%20eval_hooks&current=not_reported)
12. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20execution_isolation&system=daily-stock-analysis&dimension=G1%20execution_isolation&current=not_reported)
13. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20retry_policy&system=daily-stock-analysis&dimension=E2%20retry_policy&current=not_reported)
14. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20self_verification&system=daily-stock-analysis&dimension=E1%20self_verification&current=not_reported)
15. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20termination_condition&system=daily-stock-analysis&dimension=F1%20termination_condition&current=not_reported)
16. A1 `system_prompt_style` (System-prompt style): 30.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20system_prompt_style&system=daily-stock-analysis&dimension=A1%20system_prompt_style&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20%3Cdimension%3E&system=daily-stock-analysis> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=daily-stock-analysis>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
