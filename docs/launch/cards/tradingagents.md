# TradingAgents: HARNESS-DB cell card

| | |
|---|---|
| System id | `tradingagents` |
| Pinned version | [v0.4.0 @ `2448d0a12576`](https://github.com/tauricresearch/tradingagents/commit/2448d0a12576) (2026-08-31) |
| Repository | <https://github.com/tauricresearch/tradingagents> |
| Papers | [arXiv:2412.20138](https://arxiv.org/abs/2412.20138) |
| Stars (sampling-frame snapshot) | 107,559 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 18 coded, 20 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=tradingagents> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `not_reported` |  |  |  | Agent prompt files (tradingagents/agents/\*) not included in evidence; README says past context is injected into the Portfolio Manager prompt, suggesting dynamic composition, but builder not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20system_prompt_style&system=tradingagents&dimension=A1%20system_prompt_style&current=not_reported) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | Domain is finance data, not a repository; analysts call data tools (file tree lists \*\_tools.py) but tool bodies not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20env_context_strategy&system=tradingagents&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | Graph/state code not in evidence. Config limits article counts ('decrease to reduce token usage') but that is input sizing, not history compaction. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20context_compaction&system=tradingagents&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | Tool conversion code not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20observation_format&system=tradingagents&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | LangGraph-based; tool binding code not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tool_call_format&system=tradingagents&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | Tool definition files exist (core\_stock\_tools.py etc.) but contents not in evidence; tools vary per analyst. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tool_count&system=tradingagents&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `none` | low | “TradingAgents is a multi-agent trading framework that mirrors the dynamics of real-world trading firms.” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | File tree shows only data/market tools, no file editing tool; inferred from tool file names. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20edit_primitive&system=tradingagents&dimension=B3%20edit_primitive&current=none) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tool_schema_source&system=tradingagents&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `not_reported` |  |  |  | pyproject/requirements not shown; grep not possible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20protocol_standardization&system=tradingagents&dimension=B5%20protocol_standardization&current=not_reported) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `fixed_pipeline, react` | low | “All agents in TradingAgents follow the ReAct prompting framework (Yao et al., 2023), which synergizes reasoning and acting.” | paper Sec. 3.4 | Analysts-\>researchers debate-\>trader-\>risk debate-\>portfolio manager fixed LangGraph pipeline (README, paper Fig. 1); ReAct per agent per paper. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20loop_primitives&system=tradingagents&dimension=C1%20loop_primitives&current=fixed_pipeline%7Creact) |
| C2 | `planning_granularity` | `implicit` | low | “Our framework decomposes complex trading tasks into specialized roles.” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Trader produces a trading plan report in state, but no plan object re-read as a task list is evidenced. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20planning_granularity&system=tradingagents&dimension=C2%20planning_granularity&current=implicit) |
| C3 | `multi_agent_topology` | `pipeline` | medium | “Four analysts concurrently gather relevant market information. II. R ESEARCH TEAM: The team discusses and evaluates the collected data.” | paper Fig. 1 | Fixed hand-off sequence of specialised agents including debate stages (bull/bear, risk debaters with facilitator); debate is a sub-stage. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20multi_agent_topology&system=tradingagents&dimension=C3%20multi_agent_topology&current=pipeline) |
| C4 | `delegation_mechanism` | `role_handoff` | medium | “By utilizing structured reports, agents can query necessary details directly from the global state” | paper Sec. 4.2 | Control passes between role nodes sharing a global LangGraph state. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20delegation_mechanism&system=tradingagents&dimension=C4%20delegation_mechanism&current=role_handoff) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | CLI selects inputs up front; no evidence of in-run approval, but run loop/CLI code not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20human_in_loop&system=tradingagents&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “By clearly defining each agent’s state, we ensure that each role only extracts or queries the necessary information, processes it, and returns a completed report.” | paper Sec. 4.1 | agent\_states.py exists but not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20short_term_state&system=tradingagents&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `file_notes` | high | “Each completed run appends its decision to \`~/.tradingagents/memory/trading\_memory.md\`.” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Reflections injected into Portfolio Manager prompt; see tradingagents/agents/utils/memory.py get\_past\_context. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20long_term_memory&system=tradingagents&dimension=D2%20long_term_memory&current=file_notes) |
| D3 | `state_persistence` | `checkpoint` | high | “When enabled, LangGraph saves state after each node so a crashed or interrupted run resumes from the last successful step instead of starting over.” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Opt-in (checkpoint\_enabled False by default in default\_config.py); per-node checkpoint reload rather than conversation resume. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20state_persistence&system=tradingagents&dimension=D3%20state_persistence&current=checkpoint) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | Debate/manager judging is part of the pipeline; market\_data\_validator.py exists but not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20self_verification&system=tradingagents&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `none` | low | “"llm\_max\_retries": None,” | [tradingagents/default\_config.py](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/tradingagents/default_config.py)† | Only LLM transport retries configurable; no task-level retry evidenced. Run loop not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20retry_policy&system=tradingagents&dimension=E2%20retry_policy&current=none) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20rollback&system=tradingagents&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `max_steps` | medium | “"max\_recur\_limit": 100,” | [tradingagents/default\_config.py](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/tradingagents/default_config.py)† | Pipeline ends at Portfolio Manager decision; debate rounds capped by max\_debate\_rounds/max\_risk\_discuss\_rounds; max\_tokens here is per-call output cap, not run-ending. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20termination_condition&system=tradingagents&dimension=F1%20termination_condition&current=max_steps) |
| F2 | `cost_controls` | `not_reported` |  |  |  | Quick/deep model split is fixed per role, not routing; max\_tokens is per-call output cap. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20cost_controls&system=tradingagents&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20timeouts&system=tradingagents&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `none` | low | “ta = TradingAgentsGraph(debug=True, config=DEFAULT\_CONFIG.copy())” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Actions are in-process Python data-fetch calls; Docker option is for the whole app, not action isolation. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20execution_isolation&system=tradingagents&dimension=G1%20execution_isolation&current=none) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20filesystem_access&system=tradingagents&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20network_policy&system=tradingagents&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20permission_model&system=tradingagents&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `logs` | low | “"results\_dir": os.getenv("TRADINGAGENTS\_RESULTS\_DIR", os.path.join(\_TRADINGAGENTS\_HOME, "logs")),” | [tradingagents/default\_config.py](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/tradingagents/default_config.py)† | Log format not shown; could be structured. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tracing&system=tradingagents&dimension=H1%20tracing&current=logs) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20replayability&system=tradingagents&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | Paper reports backtests; no backtest runner visible in file tree listing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20eval_hooks&system=tradingagents&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20guardrails&system=tradingagents&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `other` | high | “TradingAgents: Multi-Agents LLM Financial Trading Framework” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Financial trading. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20target_domain&system=tradingagents&dimension=M1%20target_domain&current=other) |
| M2 | `open_source` | `yes` | medium | “So we decided to fully open-source the framework.” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | LICENSE file present but not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20open_source&system=tradingagents&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “The framework supports multiple LLM providers: OpenAI, Google, Anthropic, xAI, DeepSeek” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20model_agnostic&system=tradingagents&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “TradingAgents v0.4.0” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Repo v0.4.0 (2026-08) diverges from paper v7 (2025-06). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20primary_artifact&system=tradingagents&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | Tag history not in evidence; paper v1 date not given (only v7 3 Jun 2025). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20first_release_date&system=tradingagents&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v0.4.0 @ 2448d0a12576 (2026-08-31)` | high | “TradingAgents v0.4.0” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Only short hash given in evidence header. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20pinned_version&system=tradingagents&dimension=M6%20pinned_version&current=v0.4.0%20%40%202448d0a12576%20%282026-08-31%29) |
| M7 | `stars` | `107559` | medium | “TradingAgents v0.4.0” | [README.md](https://github.com/tauricresearch/tradingagents/blob/2448d0a12576/README.md)† | Star count from evidence header (stars: 107559), date not stamped. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20stars&system=tradingagents&dimension=M7%20stars&current=107559) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20network_policy&system=tradingagents&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20replayability&system=tradingagents&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20filesystem_access&system=tradingagents&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20rollback&system=tradingagents&dimension=E3%20rollback&current=not_reported)
5. B5 `protocol_standardization` (Protocol standardization): 84.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20protocol_standardization&system=tradingagents&dimension=B5%20protocol_standardization&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20timeouts&system=tradingagents&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20permission_model&system=tradingagents&dimension=G4%20permission_model&current=not_reported)
8. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20cost_controls&system=tradingagents&dimension=F2%20cost_controls&current=not_reported)
9. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20context_compaction&system=tradingagents&dimension=A3%20context_compaction&current=not_reported)
10. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tool_count&system=tradingagents&dimension=B2%20tool_count&current=not_reported)
11. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20human_in_loop&system=tradingagents&dimension=C5%20human_in_loop&current=not_reported)
12. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20guardrails&system=tradingagents&dimension=H4%20guardrails&current=not_reported)
13. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tool_schema_source&system=tradingagents&dimension=B4%20tool_schema_source&current=not_reported)
14. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20eval_hooks&system=tradingagents&dimension=H3%20eval_hooks&current=not_reported)
15. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20tool_call_format&system=tradingagents&dimension=B1%20tool_call_format&current=not_reported)
16. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20self_verification&system=tradingagents&dimension=E1%20self_verification&current=not_reported)
17. A1 `system_prompt_style` (System-prompt style): 30.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20system_prompt_style&system=tradingagents&dimension=A1%20system_prompt_style&current=not_reported)
18. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20env_context_strategy&system=tradingagents&dimension=A2%20env_context_strategy&current=not_reported)
19. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20observation_format&system=tradingagents&dimension=A4%20observation_format&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20%3Cdimension%3E&system=tradingagents> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=tradingagents>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
