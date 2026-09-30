# MetaGPT (software company): HARNESS-DB cell card

| | |
|---|---|
| System id | `metagpt` |
| Pinned version | [v0.8.2 @ `df9bc1858f7d`](https://github.com/geekan/metagpt/commit/df9bc1858f7d) (2025-03-02) |
| Repository | <https://github.com/geekan/metagpt> |
| Papers | [arXiv:2308.00352](https://arxiv.org/abs/2308.00352), [arXiv:2402.18679](https://arxiv.org/abs/2402.18679), [arXiv:2410.17238](https://arxiv.org/abs/2410.17238) |
| Stars (sampling-frame snapshot) | 70,499 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 12 coded, 26 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=metagpt> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `templated` | low | “In MetaGPT, we specify the agent’s profile, which includes their name, profile, goal, and constraints for each role.” | paper Sec. 3.1 | Role profile fields rendered into prompts; no code for prompt assembly in evidence bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20system_prompt_style&system=metagpt&dimension=A1%20system_prompt_style&current=templated) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | No instance template or tool registry in evidence (repo truncated to README/docs). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20env_context_strategy&system=metagpt&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | No memory/history code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20context_compaction&system=metagpt&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | Observation conversion code not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20observation_format&system=metagpt&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | No action parser in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tool_call_format&system=metagpt&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | No tool list in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tool_count&system=metagpt&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | No edit tool definition in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20edit_primitive&system=metagpt&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tool_schema_source&system=metagpt&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `not_reported` |  |  |  | No dependency list or source grep available. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20protocol_standardization&system=metagpt&dimension=B5%20protocol_standardization&current=not_reported) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, fixed_pipeline, generate_test_repair, react` | low | “we follow SOP in software development, which enables all agents to work in a sequential manner.” | paper Sec. 3.1 | Default SOP pipeline; agents React-style; publish-subscribe message pool (Sec. 3.2); executable feedback until test passes or 3 retries (Sec. 3.3). SELA MCTS tree\_search exists in repo examples, not default. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20loop_primitives&system=metagpt&dimension=C1%20loop_primitives&current=event_driven%7Cfixed_pipeline%7Cgenerate_test_repair%7Creact) |
| C2 | `planning_granularity` | `implicit` | low | “the Product Manager undertakes a thorough analysis, formulating a detailed PRD that includes User Stories and Requirement Pool.” | paper Sec. 3.1 | Structured PRD/design/task documents act as plan artifacts; Data Interpreter uses a task graph (explicit plan) but is a different role. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20planning_granularity&system=metagpt&dimension=C2%20planning_granularity&current=implicit) |
| C3 | `multi_agent_topology` | `pipeline` | medium | “We define five roles in our software company: Product Manager, Architect, Project Manager, Engineer, and QA Engineer” | paper Sec. 3.1 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20multi_agent_topology&system=metagpt&dimension=C3%20multi_agent_topology&current=pipeline) |
| C4 | `delegation_mechanism` | `message_bus` | medium | “we introduce a shared message pool that allows all agents to exchange messages directly.” | paper Sec. 3.2 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20delegation_mechanism&system=metagpt&dimension=C4%20delegation_mechanism&current=message_bus) |
| C5 | `human_in_loop` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20human_in_loop&system=metagpt&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20short_term_state&system=metagpt&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20long_term_memory&system=metagpt&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  | README mentions v0.6.0 serialization but no resume code path in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20state_persistence&system=metagpt&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `test_execution` | low | “the Engineer writes and executes the corre- sponding unit test cases, and subsequently receives the test results.” | paper Sec. 3.3 | Paper-described; not verified in code. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20self_verification&system=metagpt&dimension=E1%20self_verification&current=test_execution) |
| E2 | `retry_policy` | `not_reported` |  |  |  | Paper's 3-retry loop is step-level debugging, not task-level retry. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20retry_policy&system=metagpt&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20rollback&system=metagpt&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20termination_condition&system=metagpt&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20cost_controls&system=metagpt&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20timeouts&system=metagpt&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | README mentions docker install option but default execution boundary not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20execution_isolation&system=metagpt&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20filesystem_access&system=metagpt&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20network_policy&system=metagpt&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20permission_model&system=metagpt&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tracing&system=metagpt&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20replayability&system=metagpt&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20eval_hooks&system=metagpt&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20guardrails&system=metagpt&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `research, swe` | medium | “MetaGPT takes a \*\*one line requirement\*\* as input and outputs \*\*user stories / competitive analysis / requirements / data structures / APIs / documents, etc.\*\*” | [README.md](https://github.com/geekan/metagpt/blob/df9bc1858f7d/README.md)† | Data Interpreter for data science coded as research; Researcher use case listed. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20target_domain&system=metagpt&dimension=M1%20target_domain&current=research%7Cswe) |
| M2 | `open_source` | `yes` | medium | “License: MIT” | [README.md](https://github.com/geekan/metagpt/blob/df9bc1858f7d/README.md)† | From README badge; LICENSE file not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20open_source&system=metagpt&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | medium | “api\_type: "openai" # or azure / ollama / groq etc. Check LLMType for more options” | [README.md](https://github.com/geekan/metagpt/blob/df9bc1858f7d/README.md)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20model_agnostic&system=metagpt&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | medium | “🚀 Mar. 29, 2024: \[v0.8.0\](https://github.com/geekan/MetaGPT/releases/tag/v0.8.0) released.” | [README.md](https://github.com/geekan/metagpt/blob/df9bc1858f7d/README.md)† | Pinned repo postdates ICLR 2024 paper. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20primary_artifact&system=metagpt&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | First tag date not in evidence; README: open-sourced Jun. 30, 2023, first commit Apr. 24, 2023. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20first_release_date&system=metagpt&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v0.8.2 @ df9bc1858f7d (2025-03-02)` | high | “ref: tag:v0.8.2 df9bc1858f7d 2025-03-02” | evidence header | Full hash not given. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20pinned_version&system=metagpt&dimension=M6%20pinned_version&current=v0.8.2%20%40%20df9bc1858f7d%20%282025-03-02%29) |
| M7 | `stars` | `70499` | medium | “stars: 70499” | evidence header | Retrieval date not stated; another header reports 70487. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20stars&system=metagpt&dimension=M7%20stars&current=70499) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20network_policy&system=metagpt&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20replayability&system=metagpt&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20filesystem_access&system=metagpt&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20rollback&system=metagpt&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20state_persistence&system=metagpt&dimension=D3%20state_persistence&current=not_reported)
6. B5 `protocol_standardization` (Protocol standardization): 84.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20protocol_standardization&system=metagpt&dimension=B5%20protocol_standardization&current=not_reported)
7. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20timeouts&system=metagpt&dimension=F3%20timeouts&current=not_reported)
8. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20permission_model&system=metagpt&dimension=G4%20permission_model&current=not_reported)
9. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20cost_controls&system=metagpt&dimension=F2%20cost_controls&current=not_reported)
10. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20context_compaction&system=metagpt&dimension=A3%20context_compaction&current=not_reported)
11. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tool_count&system=metagpt&dimension=B2%20tool_count&current=not_reported)
12. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20human_in_loop&system=metagpt&dimension=C5%20human_in_loop&current=not_reported)
13. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20guardrails&system=metagpt&dimension=H4%20guardrails&current=not_reported)
14. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tool_schema_source&system=metagpt&dimension=B4%20tool_schema_source&current=not_reported)
15. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20edit_primitive&system=metagpt&dimension=B3%20edit_primitive&current=not_reported)
16. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20long_term_memory&system=metagpt&dimension=D2%20long_term_memory&current=not_reported)
17. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20eval_hooks&system=metagpt&dimension=H3%20eval_hooks&current=not_reported)
18. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20execution_isolation&system=metagpt&dimension=G1%20execution_isolation&current=not_reported)
19. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tracing&system=metagpt&dimension=H1%20tracing&current=not_reported)
20. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20retry_policy&system=metagpt&dimension=E2%20retry_policy&current=not_reported)
21. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20tool_call_format&system=metagpt&dimension=B1%20tool_call_format&current=not_reported)
22. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20short_term_state&system=metagpt&dimension=D1%20short_term_state&current=not_reported)
23. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20termination_condition&system=metagpt&dimension=F1%20termination_condition&current=not_reported)
24. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20env_context_strategy&system=metagpt&dimension=A2%20env_context_strategy&current=not_reported)
25. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20observation_format&system=metagpt&dimension=A4%20observation_format&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20%3Cdimension%3E&system=metagpt> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=metagpt>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
