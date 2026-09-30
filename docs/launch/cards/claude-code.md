# Claude Code: HARNESS-DB cell card

| | |
|---|---|
| System id | `claude-code` |
| Pinned version | [v2.1.252 @ `f275fa282e76`](https://github.com/anthropics/claude-code/commit/f275fa282e76c5e5456912268f2c367a7f4f4797) (2026-08-31) |
| Repository | <https://github.com/anthropics/claude-code> |
| Stars (sampling-frame snapshot) | 146,623 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 16 coded, 22 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=claude-code> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | low | “CLAUDE.md is a markdown file you add to your project root that Claude Code reads at the start of every session.” | docs Overview (code.claude.com/docs/en/overview) | Harness source not in pinned repo (closed binary); inferred from docs that project files/skills are loaded into context. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20system_prompt_style&system=claude-code&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “Claude Code is an active collaborator that can search and read code, edit files, write and run tests” | Anthropic announcement 2025-02-24 | CLAUDE.md injection also documented; no tool definitions available to confirm mixed. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20env_context_strategy&system=claude-code&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `not_reported` |  |  |  | Harness source (run loop/condenser) not in the repo bundle; repo holds plugins/examples only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20context_compaction&system=claude-code&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | No observation conversion code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20observation_format&system=claude-code&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | No parser source in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tool_call_format&system=claude-code&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | No tool registry in evidence; SWE-bench scaffold used bash + string-replace editor + planning tool, which is not the product default. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tool_count&system=claude-code&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `search_replace` | low | “a bash tool, and a file editing tool that operates via string replacements” | Anthropic announcement 2025-02-24, Appendix SWE-bench scaffolding | Describes benchmark scaffold, not necessarily pinned Claude Code tool set. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20edit_primitive&system=claude-code&dimension=B3%20edit_primitive&current=search_replace) |
| B4 | `tool_schema_source` | `mcp` | low | “With MCP, Claude Code can read your design docs in Google Drive, update tickets in Jira” | docs Overview | Built-in tool schema source not in evidence; only MCP documented. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tool_schema_source&system=claude-code&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp` | medium | “The Model Context Protocol (MCP) is an open standard for connecting AI tools to external data sources.” | docs Overview |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20protocol_standardization&system=claude-code&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `not_reported` |  |  |  | Run loop source not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20loop_primitives&system=claude-code&dimension=C1%20loop_primitives&current=not_reported) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | Docs mention 'plan review' but no plan object definition. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20planning_granularity&system=claude-code&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `single` | low | “Spawn multiple Claude Code agents that work on different parts of a task simultaneously. A lead agent coordinates the work” | docs Overview | Default single session; orchestrator\_workers reachable per docs. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20multi_agent_topology&system=claude-code&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `subagent_spawn` | low | “Spawn multiple Claude Code agents that work on different parts of a task simultaneously.” | docs Overview | Whether default or opt-in not determinable from evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20delegation_mechanism&system=claude-code&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `on_permission` | low | “use command line tools—keeping you in the loop at every step.” | Anthropic announcement 2025-02-24 | Settings examples (lax/strict) suggest configurable, but contents not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20human_in_loop&system=claude-code&dimension=C5%20human_in_loop&current=on_permission) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  | No state object in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20short_term_state&system=claude-code&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `file_notes, skill_library` | medium | “Claude also builds auto memory as it works, saving learnings across sessions without you writing anything.Create skills to package repeatable workflows” | docs Overview |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20long_term_memory&system=claude-code&dimension=D2%20long_term_memory&current=file_notes%7Cskill_library) |
| D3 | `state_persistence` | `not_reported` |  |  |  | Docs mention continuing sessions across surfaces (teleport, /desktop) but no resume code path in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20state_persistence&system=claude-code&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | Harness verification not in evidence; plugins (hookify require-tests-stop, code-review) are opt-in. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20self_verification&system=claude-code&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20retry_policy&system=claude-code&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20rollback&system=claude-code&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20termination_condition&system=claude-code&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20cost_controls&system=claude-code&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20timeouts&system=claude-code&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “Desktop scheduled tasks run on your machine, with direct access to your local files and tools” | docs Overview | Terminal CLI runs on host; .devcontainer/ and settings-bash-sandbox.json shipped (container/sandbox options); cloud/web sessions remote. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20execution_isolation&system=claude-code&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20filesystem_access&system=claude-code&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  | .devcontainer/init-firewall.sh exists (allowlist likely in devcontainer) but contents not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20network_policy&system=claude-code&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | examples/settings strict/lax files present but contents not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20permission_model&system=claude-code&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tracing&system=claude-code&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20replayability&system=claude-code&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | File tree shows no eval runner, but harness source is not in repo. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20eval_hooks&system=claude-code&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `action_policies` | low | “Hooks let you run shell commands before or after Claude Code actions” | docs Overview | examples/hooks/bash\_command\_validator\_example.py; hookify pretooluse/userpromptsubmit hooks suggest input\_filters too (plugin). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20guardrails&system=claude-code&dimension=H4%20guardrails&current=action_policies) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, swe` | medium | “Claude Code is an agentic coding tool that lives in your terminal, understands your codebase” | [README.md@f275fa2](https://github.com/anthropics/claude-code/blob/f275fa282e76c5e5456912268f2c367a7f4f4797/README.md) | general\_tool\_use via MCP. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20target_domain&system=claude-code&dimension=M1%20target_domain&current=general_tool_use%7Cswe) |
| M2 | `open_source` | `not_reported` |  |  |  | LICENSE.md present but contents not in evidence; repo lacks harness source. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20open_source&system=claude-code&dimension=M2%20open_source&current=not_reported) |
| M3 | `model_agnostic` | `no` | low | “The Terminal CLI, VS Code, and JetBrains also support third-party providers.” | docs Overview | Anthropic Claude models; third-party providers likely cloud hosts (Bedrock/Vertex). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20model_agnostic&system=claude-code&dimension=M3%20model_agnostic&current=no) |
| M4 | `primary_artifact` | `repo` | medium | “ref: tag:v2.1.252 f275fa282e76c5e5456912268f2c367a7f4f4797 2026-08-31” | github\_repo header | Repo contains plugins/docs, not harness source. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20primary_artifact&system=claude-code&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `2025-02-24` | low | “Claude Code is available as a limited research preview” | Anthropic announcement 2025-02-24 | Basis: announcement date; first tag not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20first_release_date&system=claude-code&dimension=M5%20first_release_date&current=2025-02-24) |
| M6 | `pinned_version` | `v2.1.252 @ f275fa282e76c5e5456912268f2c367a7f4f4797 (2026-08-31)` | high | “ref: tag:v2.1.252 f275fa282e76c5e5456912268f2c367a7f4f4797 2026-08-31” | github\_repo header |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20pinned_version&system=claude-code&dimension=M6%20pinned_version&current=v2.1.252%20%40%20f275fa282e76c5e5456912268f2c367a7f4f4797%20%282026-08-31%29) |
| M7 | `stars` | `not_reported` |  |  |  | Star count not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20stars&system=claude-code&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20network_policy&system=claude-code&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20replayability&system=claude-code&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20filesystem_access&system=claude-code&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20rollback&system=claude-code&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20state_persistence&system=claude-code&dimension=D3%20state_persistence&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20timeouts&system=claude-code&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20permission_model&system=claude-code&dimension=G4%20permission_model&current=not_reported)
8. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20cost_controls&system=claude-code&dimension=F2%20cost_controls&current=not_reported)
9. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20context_compaction&system=claude-code&dimension=A3%20context_compaction&current=not_reported)
10. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tool_count&system=claude-code&dimension=B2%20tool_count&current=not_reported)
11. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20eval_hooks&system=claude-code&dimension=H3%20eval_hooks&current=not_reported)
12. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tracing&system=claude-code&dimension=H1%20tracing&current=not_reported)
13. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20retry_policy&system=claude-code&dimension=E2%20retry_policy&current=not_reported)
14. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20tool_call_format&system=claude-code&dimension=B1%20tool_call_format&current=not_reported)
15. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20self_verification&system=claude-code&dimension=E1%20self_verification&current=not_reported)
16. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20short_term_state&system=claude-code&dimension=D1%20short_term_state&current=not_reported)
17. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20termination_condition&system=claude-code&dimension=F1%20termination_condition&current=not_reported)
18. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20observation_format&system=claude-code&dimension=A4%20observation_format&current=not_reported)
19. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20planning_granularity&system=claude-code&dimension=C2%20planning_granularity&current=not_reported)
20. C1 `loop_primitives` (Loop primitive(s)): 1.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20loop_primitives&system=claude-code&dimension=C1%20loop_primitives&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20%3Cdimension%3E&system=claude-code> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=claude-code>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
