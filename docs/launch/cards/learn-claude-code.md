# learn-claude-code (s15 integrated harness): HARNESS-DB cell card

| | |
|---|---|
| System id | `learn-claude-code` |
| Pinned version | [main @ `0dcafa2ae053`](https://github.com/shareai-lab/learn-claude-code/commit/0dcafa2ae053a1ddd6a72f265431104b08a5aa13) (2026-08-26) |
| Repository | <https://github.com/shareai-lab/learn-claude-code> |
| Stars (sampling-frame snapshot) | 76,962 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 26 coded, 12 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=learn-claude-code> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `templated` | low | “SYSTEM = f"""You are a coding agent at {WORKDIR}.” | [docs/en/s05-skill-loading.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s05-skill-loading.md) | From legacy s05 docs; s15 code.py not in evidence. Skill descriptions inserted into template; s15 may be dynamically\_composed. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20system_prompt_style&system=learn-claude-code&dimension=A1%20system_prompt_style&current=templated) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “tools (bash, read, write, edit, glob, grep, browser...)” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | Describes Claude Code; s15 tool list not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20env_context_strategy&system=learn-claude-code&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `summarize, tool_output_pruning` | medium | “four compaction steps reduce tool results first, then summarize history when it remains over the limit” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | s08 mechanism; s15 integrates course mechanisms. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20context_compaction&system=learn-claude-code&dimension=A3%20context_compaction&current=summarize%7Ctool_output_pruning) |
| A4 | `observation_format` | `raw_text` | low | “"content": output,” | [docs/en/s01-the-agent-loop.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s01-the-agent-loop.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20observation_format&system=learn-claude-code&dimension=A4%20observation_format&current=raw_text) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | medium | “block for block in response.content if block.type == "tool\_use"” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20tool_call_format&system=learn-claude-code&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `not_reported` |  |  |  | s15\_integrated\_harness/code.py content not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20tool_count&system=learn-claude-code&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `search_replace, whole_file_rewrite` | low | “"edit\_file": lambda \*\*kw: run\_edit(kw\["path"\], kw\["old\_text"\],” | [docs/en/s02-tool-use.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s02-tool-use.md) | Legacy s02 docs; write\_file also present. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20edit_primitive&system=learn-claude-code&dimension=B3%20edit_primitive&current=search_replace%7Cwhole_file_rewrite) |
| B4 | `tool_schema_source` | `hand_written, mcp` | low | “connect external tools into the same tool pool” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | Hand-written input\_schema dicts shown in docs; MCP from s14, integrated in s15. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20tool_schema_source&system=learn-claude-code&dimension=B4%20tool_schema_source&current=hand_written%7Cmcp) |
| B5 | `protocol_standardization` | `mcp` | medium | “tools, runtime context, tasks, teams, scheduling, and MCP around one loop” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20protocol_standardization&system=learn-claude-code&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `react` | medium | “(loop until stop\_reason != "tool\_use")” | [docs/en/s01-the-agent-loop.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s01-the-agent-loop.md) | s16 workflow and s17 goal loop are separate chapters, not the coded s15. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20loop_primitives&system=learn-claude-code&dimension=C1%20loop_primitives&current=react) |
| C2 | `planning_granularity` | `explicit_plan_object` | medium | “a file-backed task graph that lays the groundwork for multi-agent coordination” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20planning_granularity&system=learn-claude-code&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `orchestrator_workers` | low | “persistent teammates coordinate, claim ready tasks, and use task-bound working directories” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | s15 integrates teams; model-invoked; could be coded single if teams are opt-in tools. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20multi_agent_topology&system=learn-claude-code&dimension=C3%20multi_agent_topology&current=orchestrator_workers) |
| C4 | `delegation_mechanism` | `subagent_spawn` | medium | “Give a subtask fresh \`messages\[\]\`; its final text returns as one tool result” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | Async mailbox (message\_bus) also described for teams. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20delegation_mechanism&system=learn-claude-code&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `on_permission` | low | “check what can run, what must stop, and what needs approval” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20human_in_loop&system=learn-claude-code&dimension=C5%20human_in_loop&current=on_permission) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “TodoManager stores items with statuses.” | [docs/en/s03-todo-write.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s03-todo-write.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20short_term_state&system=learn-claude-code&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `file_notes, skill_library` | low | “three subsystems: selection, extraction, consolidation” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | s09 memory and s07 skills; storage format of memory not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20long_term_memory&system=learn-claude-code&dimension=D2%20long_term_memory&current=file_notes%7Cskill_library) |
| D3 | `state_persistence` | `not_reported` |  |  |  | s15 code not in evidence; tasks persist to disk, journal resume is s16. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20state_persistence&system=learn-claude-code&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | s17 evaluator is a separate chapter; s15 code unseen. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20self_verification&system=learn-claude-code&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20retry_policy&system=learn-claude-code&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20rollback&system=learn-claude-code&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `model_declared` | medium | “The model decides when to call tools and when to stop.” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | Subagent has range(30) safety limit. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20termination_condition&system=learn-claude-code&dimension=F1%20termination_condition&current=model_declared) |
| F2 | `cost_controls` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20cost_controls&system=learn-claude-code&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20timeouts&system=learn-claude-code&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “output = run\_bash(block.input\["command"\])” | [docs/en/s01-the-agent-loop.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s01-the-agent-loop.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20execution_isolation&system=learn-claude-code&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `scoped` | low | “raise ValueError(f"Path escapes workspace: {p}")” | [docs/en/s02-tool-use.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s02-tool-use.md) | File tools scoped; bash unconstrained. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20filesystem_access&system=learn-claude-code&dimension=G2%20filesystem_access&current=scoped) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20network_policy&system=learn-claude-code&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `static_allowlist` | low | “\`PermissionRule\` / approval pipeline” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | Rules plus approval; could be per\_call\_prompt. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20permission_model&system=learn-claude-code&dimension=G4%20permission_model&current=static_allowlist) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `structured_traces` | low | “Save transcript to .transcripts/” | [docs/en/s06-context-compact.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/docs/en/s06-context-compact.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20tracing&system=learn-claude-code&dimension=H1%20tracing&current=structured_traces) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20replayability&system=learn-claude-code&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20eval_hooks&system=learn-claude-code&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `action_policies` | low | “\`PreToolUse\` / \`PostToolUse\` / extension points” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20guardrails&system=learn-claude-code&dimension=H4%20guardrails&current=action_policies) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `swe` | medium | “A vehicle for coding. But the design patterns generalize to any domain.” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20target_domain&system=learn-claude-code&dimension=M1%20target_domain&current=swe) |
| M2 | `open_source` | `yes` | medium | “MIT” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20open_source&system=learn-claude-code&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `no` | low | “response = client.messages.create(” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | Anthropic client; ANTHROPIC\_API\_KEY configured. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20model_agnostic&system=learn-claude-code&dimension=M3%20model_agnostic&current=no) |
| M4 | `primary_artifact` | `repo` | high | “s15 reconnects the cumulative runtime” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20primary_artifact&system=learn-claude-code&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20first_release_date&system=learn-claude-code&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `main @ 0dcafa2ae053a1ddd6a72f265431104b08a5aa13 (2026-08-26)` | high | “ref: commit:main 0dcafa2ae053a1ddd6a72f265431104b08a5aa13 2026-08-26” | [README.md@0dcafa2](https://github.com/shareai-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/README.md) | No tag shown; main commit used. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20pinned_version&system=learn-claude-code&dimension=M6%20pinned_version&current=main%20%40%200dcafa2ae053a1ddd6a72f265431104b08a5aa13%20%282026-08-26%29) |
| M7 | `stars` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20stars&system=learn-claude-code&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20network_policy&system=learn-claude-code&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20replayability&system=learn-claude-code&dimension=H2%20replayability&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20rollback&system=learn-claude-code&dimension=E3%20rollback&current=not_reported)
4. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20state_persistence&system=learn-claude-code&dimension=D3%20state_persistence&current=not_reported)
5. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20timeouts&system=learn-claude-code&dimension=F3%20timeouts&current=not_reported)
6. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20cost_controls&system=learn-claude-code&dimension=F2%20cost_controls&current=not_reported)
7. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20tool_count&system=learn-claude-code&dimension=B2%20tool_count&current=not_reported)
8. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20eval_hooks&system=learn-claude-code&dimension=H3%20eval_hooks&current=not_reported)
9. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20retry_policy&system=learn-claude-code&dimension=E2%20retry_policy&current=not_reported)
10. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20self_verification&system=learn-claude-code&dimension=E1%20self_verification&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20%3Cdimension%3E&system=learn-claude-code> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=learn-claude-code>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
