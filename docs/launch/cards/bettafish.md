# BettaFish: HARNESS-DB cell card

| | |
|---|---|
| System id | `bettafish` |
| Pinned version | [v3.0.0 @ `9bb2d32cad11`](https://github.com/666ghj/bettafish/commit/9bb2d32cad111b1eab73297400ef09978b0c5882) (2025-12-22) |
| Repository | <https://github.com/666ghj/bettafish> |
| Stars (sampling-frame snapshot) | 42,232 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 12 coded, 24 `not_reported`, 2 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=bettafish> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `templated` | low | “│ ├── prompts/ # 提示词模板” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† | Only README tree seen; prompts are template files per engine. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20system_prompt_style&system=bettafish&dimension=A1%20system_prompt_style&current=templated) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | No task template or tool registry code in evidence; domain is web/db search, not repo. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20env_context_strategy&system=bettafish&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | README lists max\_content\_length = 8000 but no history-rewriting code opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20context_compaction&system=bettafish&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20observation_format&system=bettafish&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | Parser code not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tool_call_format&system=bettafish&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tool_count&system=bettafish&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | Tool definitions not opened; the system likely has no file editing, but that cannot be confirmed from the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20edit_primitive&system=bettafish&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tool_schema_source&system=bettafish&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `not_reported` |  |  |  | No grep of source possible; README says built from scratch without frameworks. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20protocol_standardization&system=bettafish&dimension=B5%20protocol_standardization&current=not_reported) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `unresolved` |  |  |  | unresolved after the repair pass (quote\_not\_in\_bundle). Node-based pipeline with reflection rounds (max\_reflections = 2); run loop not opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20loop_primitives&system=bettafish&dimension=C1%20loop_primitives&current=unresolved) |
| C2 | `planning_granularity` | `explicit_plan_object` | low | “report\_structure\_node.py # 报告结构节点” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† | The report structure node plus the state module suggest a stored plan. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20planning_granularity&system=bettafish&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `unresolved` |  |  |  | unresolved after the repair pass (quote\_not\_in\_bundle). Three parallel agents coordinated through a forum with an LLM host, then a Report Agent; this also resembles peer/pipeline. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20multi_agent_topology&system=bettafish&dimension=C3%20multi_agent_topology&current=unresolved) |
| C4 | `delegation_mechanism` | `message_bus` | low | “forum\_reader.py # Agent间论坛通信工具” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20delegation_mechanism&system=bettafish&dimension=C4%20delegation_mechanism&current=message_bus) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | The CLI's file confirmation (y/n) is not action gating. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20human_in_loop&system=bettafish&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “state.py # Agent状态定义” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20short_term_state&system=bettafish&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20long_term_memory&system=bettafish&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  | The regenerate\_latest\_\* scripts re-render saved chapters; no resume path was opened. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20state_persistence&system=bettafish&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `self_critique` | low | “各Agent + 反思机制 + 论坛引导” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† | The README also mentions chapter JSON validation and chart repair. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20self_verification&system=bettafish&dimension=E1%20self_verification&current=self_critique) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20retry_policy&system=bettafish&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20rollback&system=bettafish&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `max_steps` | low | “max\_reflections = 2 # 反思轮次” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20termination_condition&system=bettafish&dimension=F1%20termination_condition&current=max_steps) |
| F2 | `cost_controls` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20cost_controls&system=bettafish&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20timeouts&system=bettafish&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | Docker deployment exists for the whole app, but there is no agent action execution boundary to code. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20execution_isolation&system=bettafish&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20filesystem_access&system=bettafish&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20network_policy&system=bettafish&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | The README mentions read-only DB query wrappers. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20permission_model&system=bettafish&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `logs` | low | “logs/ # 运行日志目录” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tracing&system=bettafish&dimension=H1%20tracing&current=logs) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20replayability&system=bettafish&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20eval_hooks&system=bettafish&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  | A ReportEngine sanitization test exists. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20guardrails&system=bettafish&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `research` | medium | “topics: agent-framework, data-analysis, deep-research, deep-search, llms, multi-agent-system” | github:666ghj/BettaFish repo metadata@9bb2d32 | Public-opinion analysis / deep research assistant. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20target_domain&system=bettafish&dimension=M1%20target_domain&current=research) |
| M2 | `open_source` | `yes` | high | “本项目采用 \[GPL-2.0许可证\](LICENSE)” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20open_source&system=bettafish&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “支持任意openAI调用格式的LLM提供商” | [README.md](https://github.com/666ghj/bettafish/blob/9bb2d32cad111b1eab73297400ef09978b0c5882/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20model_agnostic&system=bettafish&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v3.0.0 9bb2d32cad111b1eab73297400ef09978b0c5882 2025-12-22” | github metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20primary_artifact&system=bettafish&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | The first tag date is not in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20first_release_date&system=bettafish&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v3.0.0 @ 9bb2d32cad111b1eab73297400ef09978b0c5882 (2025-12-22)` | high | “ref: tag:v3.0.0 9bb2d32cad111b1eab73297400ef09978b0c5882 2025-12-22” | github metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20pinned_version&system=bettafish&dimension=M6%20pinned_version&current=v3.0.0%20%40%209bb2d32cad111b1eab73297400ef09978b0c5882%20%282025-12-22%29) |
| M7 | `stars` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20stars&system=bettafish&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20network_policy&system=bettafish&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20replayability&system=bettafish&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20filesystem_access&system=bettafish&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20rollback&system=bettafish&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20state_persistence&system=bettafish&dimension=D3%20state_persistence&current=not_reported)
6. B5 `protocol_standardization` (Protocol standardization): 84.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20protocol_standardization&system=bettafish&dimension=B5%20protocol_standardization&current=not_reported)
7. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20timeouts&system=bettafish&dimension=F3%20timeouts&current=not_reported)
8. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20permission_model&system=bettafish&dimension=G4%20permission_model&current=not_reported)
9. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20cost_controls&system=bettafish&dimension=F2%20cost_controls&current=not_reported)
10. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20context_compaction&system=bettafish&dimension=A3%20context_compaction&current=not_reported)
11. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tool_count&system=bettafish&dimension=B2%20tool_count&current=not_reported)
12. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20human_in_loop&system=bettafish&dimension=C5%20human_in_loop&current=not_reported)
13. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20guardrails&system=bettafish&dimension=H4%20guardrails&current=not_reported)
14. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tool_schema_source&system=bettafish&dimension=B4%20tool_schema_source&current=not_reported)
15. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20edit_primitive&system=bettafish&dimension=B3%20edit_primitive&current=not_reported)
16. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20long_term_memory&system=bettafish&dimension=D2%20long_term_memory&current=not_reported)
17. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20eval_hooks&system=bettafish&dimension=H3%20eval_hooks&current=not_reported)
18. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20execution_isolation&system=bettafish&dimension=G1%20execution_isolation&current=not_reported)
19. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20retry_policy&system=bettafish&dimension=E2%20retry_policy&current=not_reported)
20. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20tool_call_format&system=bettafish&dimension=B1%20tool_call_format&current=not_reported)
21. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20env_context_strategy&system=bettafish&dimension=A2%20env_context_strategy&current=not_reported)
22. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20observation_format&system=bettafish&dimension=A4%20observation_format&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20%3Cdimension%3E&system=bettafish> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=bettafish>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
