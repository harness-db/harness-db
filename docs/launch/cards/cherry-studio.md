# Cherry Studio: HARNESS-DB cell card

| | |
|---|---|
| System id | `cherry-studio` |
| Pinned version | [v2.0.10 @ `3db6b513e492`](https://github.com/cherryhq/cherry-studio/commit/3db6b513e4920d829d134a308a4aef157ef5f3aa) (2026-08-28) |
| Repository | <https://github.com/cherryhq/cherry-studio> |
| Stars (sampling-frame snapshot) | 51,871 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 7 coded, 31 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=cherry-studio> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `not_reported` |  |  |  | Only README and doc index available; no prompt-building code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20system_prompt_style&system=cherry-studio&dimension=A1%20system_prompt_style&current=not_reported) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | No instance template or tool list in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20env_context_strategy&system=cherry-studio&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | No history/condenser code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20context_compaction&system=cherry-studio&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | No observation conversion code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20observation_format&system=cherry-studio&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | No parser code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tool_call_format&system=cherry-studio&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | No tool registry in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tool_count&system=cherry-studio&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | No edit tool definition in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20edit_primitive&system=cherry-studio&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `mcp` | low | “⚙️ MCP(Model Context Protocol) Server” | [README.md@3db6b513](https://github.com/cherryhq/cherry-studio/blob/3db6b513e4920d829d134a308a4aef157ef5f3aa/README.md) | Only MCP stated in README feature list; other schema sources not determinable from evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tool_schema_source&system=cherry-studio&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp` | medium | “⚙️ MCP(Model Context Protocol) Server” | [README.md@3db6b513](https://github.com/cherryhq/cherry-studio/blob/3db6b513e4920d829d134a308a4aef157ef5f3aa/README.md) | README feature list; no code seen. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20protocol_standardization&system=cherry-studio&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `not_reported` |  |  |  | No run loop in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20loop_primitives&system=cherry-studio&dimension=C1%20loop_primitives&current=not_reported) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | No plan object or prompt in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20planning_granularity&system=cherry-studio&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `not_reported` |  |  |  | README mentions 'autonomous agents' and multi-model conversations, but no agent factory in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20multi_agent_topology&system=cherry-studio&dimension=C3%20multi_agent_topology&current=not_reported) |
| C4 | `delegation_mechanism` | `not_reported` |  |  |  | No delegation code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20delegation_mechanism&system=cherry-studio&dimension=C4%20delegation_mechanism&current=not_reported) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | No confirmation/permission code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20human_in_loop&system=cherry-studio&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  | No state object in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20short_term_state&system=cherry-studio&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | Topics list 'agent-skills', 'skills' but no code; knowledge base mentioned for Enterprise only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20long_term_memory&system=cherry-studio&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  | No persistence code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20state_persistence&system=cherry-studio&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | No verification code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20self_verification&system=cherry-studio&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  | No retry code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20retry_policy&system=cherry-studio&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  | No undo/revert code in evidence; WebDAV backup is data backup, not run rollback. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20rollback&system=cherry-studio&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  | No run loop in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20termination_condition&system=cherry-studio&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  | No cost config in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20cost_controls&system=cherry-studio&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  | No timeout code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20timeouts&system=cherry-studio&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | Desktop client; execution backend not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20execution_isolation&system=cherry-studio&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  | No filesystem scoping code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20filesystem_access&system=cherry-studio&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  | No network config in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20network_policy&system=cherry-studio&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | No permission code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20permission_model&system=cherry-studio&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  | No logging/tracing code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tracing&system=cherry-studio&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  | No replay code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20replayability&system=cherry-studio&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | Repo not searchable in evidence; doc index lists only contrib docs. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20eval_hooks&system=cherry-studio&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  | No guardrail code in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20guardrails&system=cherry-studio&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, other` | low | “Cherry Studio is a desktop client that supports multiple LLM providers, available on Windows, Mac and Linux.” | [README.md@3db6b513](https://github.com/cherryhq/cherry-studio/blob/3db6b513e4920d829d134a308a4aef157ef5f3aa/README.md) | General chat/productivity client with MCP; 'other' = chat assistant. Topics mention claude-code/codex (possible swe) not verified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20target_domain&system=cherry-studio&dimension=M1%20target_domain&current=general_tool_use%7Cother) |
| M2 | `open_source` | `yes` | medium | “The Cherry Studio Community Edition is governed by the standard GNU Affero General Public License v3.0 (AGPL-3.0)” | [README.md@3db6b513](https://github.com/cherryhq/cherry-studio/blob/3db6b513e4920d829d134a308a4aef157ef5f3aa/README.md) | LICENSE file not in evidence; README states AGPL-3.0. Enterprise edition is partly closed but a separate product. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20open_source&system=cherry-studio&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | medium | “Major LLM Cloud Services: OpenAI, Gemini, Anthropic, and more” | [README.md@3db6b513](https://github.com/cherryhq/cherry-studio/blob/3db6b513e4920d829d134a308a4aef157ef5f3aa/README.md) | README; client abstraction code not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20model_agnostic&system=cherry-studio&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v2.0.10 3db6b513e4920d829d134a308a4aef157ef5f3aa 2026-08-28” | github repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20primary_artifact&system=cherry-studio&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | No tag history in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20first_release_date&system=cherry-studio&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v2.0.10 @ 3db6b513e4920d829d134a308a4aef157ef5f3aa (2026-08-28)` | high | “ref: tag:v2.0.10 3db6b513e4920d829d134a308a4aef157ef5f3aa 2026-08-28” | github repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20pinned_version&system=cherry-studio&dimension=M6%20pinned_version&current=v2.0.10%20%40%203db6b513e4920d829d134a308a4aef157ef5f3aa%20%282026-08-28%29) |
| M7 | `stars` | `not_reported` |  |  |  | Star count not in evidence; needs gh api query. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20stars&system=cherry-studio&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20network_policy&system=cherry-studio&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20replayability&system=cherry-studio&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20filesystem_access&system=cherry-studio&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20rollback&system=cherry-studio&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20state_persistence&system=cherry-studio&dimension=D3%20state_persistence&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20timeouts&system=cherry-studio&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20permission_model&system=cherry-studio&dimension=G4%20permission_model&current=not_reported)
8. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20cost_controls&system=cherry-studio&dimension=F2%20cost_controls&current=not_reported)
9. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20context_compaction&system=cherry-studio&dimension=A3%20context_compaction&current=not_reported)
10. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tool_count&system=cherry-studio&dimension=B2%20tool_count&current=not_reported)
11. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20human_in_loop&system=cherry-studio&dimension=C5%20human_in_loop&current=not_reported)
12. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20guardrails&system=cherry-studio&dimension=H4%20guardrails&current=not_reported)
13. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20edit_primitive&system=cherry-studio&dimension=B3%20edit_primitive&current=not_reported)
14. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20long_term_memory&system=cherry-studio&dimension=D2%20long_term_memory&current=not_reported)
15. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20eval_hooks&system=cherry-studio&dimension=H3%20eval_hooks&current=not_reported)
16. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20execution_isolation&system=cherry-studio&dimension=G1%20execution_isolation&current=not_reported)
17. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tracing&system=cherry-studio&dimension=H1%20tracing&current=not_reported)
18. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20retry_policy&system=cherry-studio&dimension=E2%20retry_policy&current=not_reported)
19. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20tool_call_format&system=cherry-studio&dimension=B1%20tool_call_format&current=not_reported)
20. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20self_verification&system=cherry-studio&dimension=E1%20self_verification&current=not_reported)
21. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20short_term_state&system=cherry-studio&dimension=D1%20short_term_state&current=not_reported)
22. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20termination_condition&system=cherry-studio&dimension=F1%20termination_condition&current=not_reported)
23. C4 `delegation_mechanism` (Delegation mechanism): 31.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20delegation_mechanism&system=cherry-studio&dimension=C4%20delegation_mechanism&current=not_reported)
24. A1 `system_prompt_style` (System-prompt style): 30.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20system_prompt_style&system=cherry-studio&dimension=A1%20system_prompt_style&current=not_reported)
25. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20env_context_strategy&system=cherry-studio&dimension=A2%20env_context_strategy&current=not_reported)
26. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20observation_format&system=cherry-studio&dimension=A4%20observation_format&current=not_reported)
27. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20planning_granularity&system=cherry-studio&dimension=C2%20planning_granularity&current=not_reported)
28. C3 `multi_agent_topology` (Multi-agent topology): 1.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20multi_agent_topology&system=cherry-studio&dimension=C3%20multi_agent_topology&current=not_reported)
29. C1 `loop_primitives` (Loop primitive(s)): 1.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20loop_primitives&system=cherry-studio&dimension=C1%20loop_primitives&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20%3Cdimension%3E&system=cherry-studio> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=cherry-studio>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
