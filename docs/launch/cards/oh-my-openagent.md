# oh-my-openagent: HARNESS-DB cell card

| | |
|---|---|
| System id | `oh-my-openagent` |
| Pinned version | [v5.0.0-beta.31 @ `62ed7952533a`](https://github.com/code-yeongyu/oh-my-openagent/commit/62ed7952533a45470ac4008eb199e90be20bd09c) (2026-08-31) |
| Repository | <https://github.com/code-yeongyu/oh-my-openagent> |
| Stars (sampling-frame snapshot) | 69,107 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 17 coded, 21 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=oh-my-openagent> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | medium | “Project rules and AGENTS.md auto-loaded into the agent's context at every prompt.” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Rules injection plus IntentGate mode prompts; prompt builder code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20system_prompt_style&system=oh-my-openagent&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `mixed` | low | “Context Injection\*\*: Auto-inject AGENTS.md, README.md, conditional rules” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Injected AGENTS.md/README context plus agent-driven LSP/AST-grep/Explore navigation. Classified from README prose; code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20env_context_strategy&system=oh-my-openagent&dimension=A2%20env_context_strategy&current=mixed) |
| A3 | `context_compaction` | `not_reported` |  |  |  | README mentions 'Aggressive truncation' as experimental and recovery from context window limits; no condenser code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20context_compaction&system=oh-my-openagent&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | Observation conversion code not in bundle. Hashline-tagged text reads and multimodal looker are described in README. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20observation_format&system=oh-my-openagent&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | Parser is in the OpenCode host; not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tool_call_format&system=oh-my-openagent&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | Tool registry not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tool_count&system=oh-my-openagent&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | Opt-in hashline edit is described with LINE#ID tags (line-anchored). Default edit tool comes from the OpenCode host. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20edit_primitive&system=oh-my-openagent&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `mcp` | medium | “Built-in MCPs\*\*: websearch (Exa), context7 (docs), grep\_app (GitHub search) — injected at runtime by the plugin” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Only the MCP source is evidenced. The source of the other tool schemas is not reported. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tool_schema_source&system=oh-my-openagent&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp` | high | “Built-in MCPs\*\*: websearch (Exa), context7 (docs), grep\_app (GitHub search) — injected at runtime by the plugin” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20protocol_standardization&system=oh-my-openagent&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | low | “Hooks\*\*: 54+ lifecycle hooks (61 with Team Mode), all configurable via \`disabled\_hooks\`” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | The react loop is provided by the OpenCode host. Goal idle-continuation (default off) and Todo Enforcer continuation are described. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20loop_primitives&system=oh-my-openagent&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `explicit_plan_object` | medium | “writes a verified plan to \`.omo/plans/\` before touching code” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Prometheus plan file, executed by Atlas. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20planning_granularity&system=oh-my-openagent&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `orchestrator_workers` | medium | “Sisyphus orchestrates Hephaestus, Oracle, Librarian, Explore. A full AI dev team in parallel.” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Default Sisyphus delegates. Team Mode (peer messaging) is opt-in. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20multi_agent_topology&system=oh-my-openagent&dimension=C3%20multi_agent_topology&current=orchestrator_workers) |
| C4 | `delegation_mechanism` | `subagent_spawn` | medium | “When Sisyphus delegates to a subagent, it doesn't pick a model. It picks a \*\*category\*\*.” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | The Team Mode message bus is opt-in (team\_send\_message). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20delegation_mechanism&system=oh-my-openagent&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | The host (OpenCode) permission system is not in bundle. Prometheus interviews the user. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20human_in_loop&system=oh-my-openagent&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “Todo Enforcer” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Todo lists and boulder state are described; code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20short_term_state&system=oh-my-openagent&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `file_notes, skill_library` | medium | “Add your own under \`.opencode/skills/\*/SKILL.md\` or \`~/.config/opencode/skills/\*/SKILL.md\`.” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Also covers AGENTS.md files generated by /init-deep. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20long_term_memory&system=oh-my-openagent&dimension=D2%20long_term_memory&current=file_notes%7Cskill_library) |
| D3 | `state_persistence` | `full_resume` | low | “Session crash on a Prometheus plan? Resume with \`/ulw-execute\` (Atlas + boulder).” | [docs/manifesto.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/docs/manifesto.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20state_persistence&system=oh-my-openagent&dimension=D3%20state_persistence&current=full_resume) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | The comment checker and Momus plan review are described. No harness verification code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20self_verification&system=oh-my-openagent&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20retry_policy&system=oh-my-openagent&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20rollback&system=oh-my-openagent&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  | The run loop is in the host; not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20termination_condition&system=oh-my-openagent&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `model_routing` | medium | “The agent says what kind of work it needs; the harness picks the right model.” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | Only the category-based model routing is evidenced. The other cost controls are not reported. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20cost_controls&system=oh-my-openagent&dimension=F2%20cost_controls&current=model_routing) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20timeouts&system=oh-my-openagent&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | Runs inside the OpenCode host; execution backend not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20execution_isolation&system=oh-my-openagent&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20filesystem_access&system=oh-my-openagent&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20network_policy&system=oh-my-openagent&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | Agent permissions are configurable per the README; no policy code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20permission_model&system=oh-my-openagent&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  | Only PostHog DAU telemetry is described. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tracing&system=oh-my-openagent&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20replayability&system=oh-my-openagent&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20eval_hooks&system=oh-my-openagent&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20guardrails&system=oh-my-openagent&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `swe` | medium | “It transforms a single AI agent into a coordinated development team that actually ships code.” | [docs/guide/overview.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/docs/guide/overview.md) | The playwright skill is built in. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20target_domain&system=oh-my-openagent&dimension=M1%20target_domain&current=swe) |
| M2 | `open_source` | `partial` | low | “license-SUL--1.0” | [README.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/README.md) | The SUL-1.0 licence is not OSI; the bundle does not contain LICENSE.md. Closest value is partial. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20open_source&system=oh-my-openagent&dimension=M2%20open_source&current=partial) |
| M3 | `model_agnostic` | `yes` | medium | “Not locked to Claude. Not locked to OpenAI. Not locked to anyone.” | [docs/guide/overview.md@62ed795](https://github.com/code-yeongyu/oh-my-openagent/blob/62ed7952533a45470ac4008eb199e90be20bd09c/docs/guide/overview.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20model_agnostic&system=oh-my-openagent&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v5.0.0-beta.31 62ed7952533a45470ac4008eb199e90be20bd09c 2026-08-31” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20primary_artifact&system=oh-my-openagent&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20first_release_date&system=oh-my-openagent&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v5.0.0-beta.31 @ 62ed7952533a45470ac4008eb199e90be20bd09c (2026-08-31)` | high | “ref: tag:v5.0.0-beta.31 62ed7952533a45470ac4008eb199e90be20bd09c 2026-08-31” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20pinned_version&system=oh-my-openagent&dimension=M6%20pinned_version&current=v5.0.0-beta.31%20%40%2062ed7952533a45470ac4008eb199e90be20bd09c%20%282026-08-31%29) |
| M7 | `stars` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20stars&system=oh-my-openagent&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20network_policy&system=oh-my-openagent&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20replayability&system=oh-my-openagent&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20filesystem_access&system=oh-my-openagent&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20rollback&system=oh-my-openagent&dimension=E3%20rollback&current=not_reported)
5. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20timeouts&system=oh-my-openagent&dimension=F3%20timeouts&current=not_reported)
6. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20permission_model&system=oh-my-openagent&dimension=G4%20permission_model&current=not_reported)
7. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20context_compaction&system=oh-my-openagent&dimension=A3%20context_compaction&current=not_reported)
8. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tool_count&system=oh-my-openagent&dimension=B2%20tool_count&current=not_reported)
9. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20human_in_loop&system=oh-my-openagent&dimension=C5%20human_in_loop&current=not_reported)
10. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20guardrails&system=oh-my-openagent&dimension=H4%20guardrails&current=not_reported)
11. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20edit_primitive&system=oh-my-openagent&dimension=B3%20edit_primitive&current=not_reported)
12. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20eval_hooks&system=oh-my-openagent&dimension=H3%20eval_hooks&current=not_reported)
13. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20execution_isolation&system=oh-my-openagent&dimension=G1%20execution_isolation&current=not_reported)
14. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tracing&system=oh-my-openagent&dimension=H1%20tracing&current=not_reported)
15. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20retry_policy&system=oh-my-openagent&dimension=E2%20retry_policy&current=not_reported)
16. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20tool_call_format&system=oh-my-openagent&dimension=B1%20tool_call_format&current=not_reported)
17. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20self_verification&system=oh-my-openagent&dimension=E1%20self_verification&current=not_reported)
18. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20termination_condition&system=oh-my-openagent&dimension=F1%20termination_condition&current=not_reported)
19. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20observation_format&system=oh-my-openagent&dimension=A4%20observation_format&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20%3Cdimension%3E&system=oh-my-openagent> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=oh-my-openagent>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
