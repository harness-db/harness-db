# OpenHands (CodeActAgent): HARNESS-DB cell card

| | |
|---|---|
| System id | `openhands` |
| Pinned version | [OpenHands v1.16.0 @ `64c126965501`](https://github.com/all-hands-ai/openhands/commit/64c126965501) (2026-08-27) |
| Repository | <https://github.com/all-hands-ai/openhands> |
| Papers | [arXiv:2407.16741](https://arxiv.org/abs/2407.16741) |
| Stars (sampling-frame snapshot) | 88,433 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 18 coded, 20 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-24 |
| Explorer | <https://harness-db.github.io/harness-db/#system=openhands> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | low | “The frontend forwards that backend-provided information into new conversations as an agent context suffix so agents can use the correct URLs instead of guessing ports.” | [docs/architecture.md@64c126965501](https://github.com/all-hands-ai/openhands/blob/64c126965501/docs/architecture.md) | The prompt builder lives in software-agent-sdk, which is not in the evidence bundle. This value is inferred only from the runtime context suffix that Canvas appends. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20system_prompt_style&system=openhands&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “It allows the agent to access a bash terminal to run code and command line tools” | paper Sec. 2.2 | Paper-only (v0 architecture). The SDK tool preset is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20env_context_strategy&system=openhands&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `not_reported` |  |  |  | The condenser code in software-agent-sdk is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20context_compaction&system=openhands&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `a11y_tree, raw_text, screenshots` | low | “HTML, DOM, accessibility tree (Mozilla), screenshot, opened tabs, etc.” | paper Sec. 2.2 | Paper-only description of browser observations. Bash output is raw text. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20observation_format&system=openhands&dimension=A4%20observation_format&current=a11y_tree%7Craw_text%7Cscreenshots) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `code_as_action` | low | “including executing bash commands, Python code, or browser-specific programming language” | paper Sec. 3 | Paper (CodeAct v1.x). The pinned SDK parser is not in the bundle; the paper also mentions JSON-style function calling. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tool_call_format&system=openhands&dimension=B1%20tool_call_format&current=code_as_action) |
| B2 | `tool_count` | `not_reported` |  |  |  | The tool registry is in the SDK, which is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tool_count&system=openhands&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `line_range_edit` | low | “edit\_file, which allows modifying an existing file from a specified line” | paper Sec. 2.3 | Paper-only AgentSkills description. The pinned SDK editor is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20edit_primitive&system=openhands&dimension=B3%20edit_primitive&current=line_range_edit) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  | The schema generation code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tool_schema_source&system=openhands&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `other` | high | “Use with OpenHands, Claude Code, Codex, Gemini, or any agent with Agent-Client Protocol (ACP).” | [README.md@64c126965501](https://github.com/all-hands-ai/openhands/blob/64c126965501/README.md) | The other protocol is ACP (Agent Client Protocol). MCP could not be checked because the SDK is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20protocol_standardization&system=openhands&dimension=B5%20protocol_standardization&current=other) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | low | “through an event stream architecture that is powerful and flexible” | paper Sec. 1 | Paper-only. The run loop is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20loop_primitives&system=openhands&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | The tool preset and plan object are not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20planning_granularity&system=openhands&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `not_reported` |  |  |  | The paper describes AgentDelegateAction, but the default agent factory is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20multi_agent_topology&system=openhands&dimension=C3%20multi_agent_topology&current=not_reported) |
| C4 | `delegation_mechanism` | `not_reported` |  |  |  | The paper mentions delegation to BrowsingAgent. The pinned default could not be verified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20delegation_mechanism&system=openhands&dimension=C4%20delegation_mechanism&current=not_reported) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | The confirmation policy code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20human_in_loop&system=openhands&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “the state is a data structure that encapsulates all relevant information for the agent’s execution” | paper Sec. 2.1 | Paper-only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20short_term_state&system=openhands&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | The SDK memory and skills code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20long_term_memory&system=openhands&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  | The conversation persistence code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20state_persistence&system=openhands&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | The critic code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20self_verification&system=openhands&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  | The run loop is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20retry_policy&system=openhands&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  | The editor tool is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20rollback&system=openhands&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `model_declared` | low | “return AgentFinishAction()” | paper Sec. 2.1 Fig. 3 | Taken from a minimal example agent. The step and cost caps could not be checked. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20termination_condition&system=openhands&dimension=F1%20termination_condition&current=model_declared) |
| F2 | `cost_controls` | `not_reported` |  |  |  | The LLM config is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20cost_controls&system=openhands&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `per_tool` | low | “ws.send(JSON.stringify({ command, cwd, timeout }));” | [src/hooks/use-bash-command-runner.ts@64c126965501](https://github.com/all-hands-ai/openhands/blob/64c126965501/src/hooks/use-bash-command-runner.ts) | Only the frontend bash runner, which passes a per-command timeout to the agent-server, is visible. A run-level timeout could not be checked. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20timeouts&system=openhands&dimension=F3%20timeouts&current=per_tool) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | medium | “It runs locally on your machine by default” | [README.md@64c126965501](https://github.com/all-hands-ai/openhands/blob/64c126965501/README.md) | Docker sandbox, VM and cloud backends are optional. The paper describes a Docker sandbox for v0. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20execution_isolation&system=openhands&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `full` | high | “the agent will have full access to your filesystem!” | [README.md@64c126965501](https://github.com/all-hands-ai/openhands/blob/64c126965501/README.md) | Applies to the host in the default no-sandbox mode. The Docker option scopes access to PROJECTS\_PATH. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20filesystem_access&system=openhands&dimension=G2%20filesystem_access&current=full) |
| G3 | `network_policy` | `not_reported` |  |  |  | The workspace and network config are not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20network_policy&system=openhands&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | The security and confirmation code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20permission_model&system=openhands&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  | The observability code is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tracing&system=openhands&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  | No replay code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20replayability&system=openhands&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | The paper Sec. 4 describes an evaluation framework, but the pinned repos' eval code is not in the bundle and the file list was truncated. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20eval_hooks&system=openhands&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  | The SDK security and hooks code is not in the bundle. DefenseClaw is an external integration. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20guardrails&system=openhands&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, swe, web` | medium | “including software engineering (e.g., SWE-BENCH ) and web browsing (e.g., WEBARENA ), among others” | paper Abstract | general\_tool\_use comes from the README's third-party integrations. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20target_domain&system=openhands&dimension=M1%20target_domain&current=general_tool_use%7Cswe%7Cweb) |
| M2 | `open_source` | `yes` | medium | “Released under the permissive MIT license” | paper Abstract | The LICENSE file is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20open_source&system=openhands&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | medium | “Use with any LLM” | [README.md@64c126965501](https://github.com/all-hands-ai/openhands/blob/64c126965501/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20model_agnostic&system=openhands&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “tag:v1.16.0 64c126965501 2026-08-27” | evidence header | The repo postdates the ICLR 2025 paper. The harness now lives in software-agent-sdk. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20primary_artifact&system=openhands&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | No tag history is in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20first_release_date&system=openhands&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `OpenHands v1.16.0 @ 64c126965501 (2026-08-27)` | high | “tag:v1.16.0 64c126965501 2026-08-27” | evidence header | Only a short hash is available. The SDK pin is not in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20pinned_version&system=openhands&dimension=M6%20pinned_version&current=OpenHands%20v1.16.0%20%40%2064c126965501%20%282026-08-27%29) |
| M7 | `stars` | `88433` | high | “stars: 88433” | evidence header | The date is not stated in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20stars&system=openhands&dimension=M7%20stars&current=88433) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20network_policy&system=openhands&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20replayability&system=openhands&dimension=H2%20replayability&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20rollback&system=openhands&dimension=E3%20rollback&current=not_reported)
4. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20state_persistence&system=openhands&dimension=D3%20state_persistence&current=not_reported)
5. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20permission_model&system=openhands&dimension=G4%20permission_model&current=not_reported)
6. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20cost_controls&system=openhands&dimension=F2%20cost_controls&current=not_reported)
7. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20context_compaction&system=openhands&dimension=A3%20context_compaction&current=not_reported)
8. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tool_count&system=openhands&dimension=B2%20tool_count&current=not_reported)
9. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20human_in_loop&system=openhands&dimension=C5%20human_in_loop&current=not_reported)
10. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20guardrails&system=openhands&dimension=H4%20guardrails&current=not_reported)
11. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tool_schema_source&system=openhands&dimension=B4%20tool_schema_source&current=not_reported)
12. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20long_term_memory&system=openhands&dimension=D2%20long_term_memory&current=not_reported)
13. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20eval_hooks&system=openhands&dimension=H3%20eval_hooks&current=not_reported)
14. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20tracing&system=openhands&dimension=H1%20tracing&current=not_reported)
15. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20retry_policy&system=openhands&dimension=E2%20retry_policy&current=not_reported)
16. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20self_verification&system=openhands&dimension=E1%20self_verification&current=not_reported)
17. C4 `delegation_mechanism` (Delegation mechanism): 31.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20delegation_mechanism&system=openhands&dimension=C4%20delegation_mechanism&current=not_reported)
18. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20planning_granularity&system=openhands&dimension=C2%20planning_granularity&current=not_reported)
19. C3 `multi_agent_topology` (Multi-agent topology): 1.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20multi_agent_topology&system=openhands&dimension=C3%20multi_agent_topology&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20%3Cdimension%3E&system=openhands> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=openhands>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
