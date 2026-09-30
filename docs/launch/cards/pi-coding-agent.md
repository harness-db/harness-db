# Pi coding agent: HARNESS-DB cell card

| | |
|---|---|
| System id | `pi-coding-agent` |
| Pinned version | [v0.84.4 @ `b79e4cc83497`](https://github.com/earendil-works/pi/commit/b79e4cc834970cca69daebffab7df1da7d1e52c4) (2026-08-28) |
| Repository | <https://github.com/earendil-works/pi> |
| Stars (sampling-frame snapshot) | 106,254 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 9 coded, 29 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=pi-coding-agent> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `not_reported` |  |  |  | packages/agent/src/harness/system-prompt.ts exists in the file tree, but its content is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20system_prompt_style&system=pi-coding-agent&dimension=A1%20system_prompt_style&current=not_reported) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | The tool list (read, bash, edit, write) appears only as file paths; there is no instance template or tool content. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20env_context_strategy&system=pi-coding-agent&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | harness/compaction/compaction.ts and branch-summarization.ts exist in the tree, but no content is available; utils/truncate.ts is also unread. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20context_compaction&system=pi-coding-agent&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | tools/image.ts exists in the tree; its content is missing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20observation_format&system=pi-coding-agent&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | The README mentions 'tool calling', but no parser code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tool_call_format&system=pi-coding-agent&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | harness/tools/ contains bash, edit, read, write and image files; the registry (tools/index.ts) is unread. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tool_count&system=pi-coding-agent&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | edit.ts, edit-diff.ts and write.ts exist; their content is missing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20edit_primitive&system=pi-coding-agent&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  | typebox-helpers.ts suggests TypeBox schemas, but this is unverified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tool_schema_source&system=pi-coding-agent&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `not_reported` |  |  |  | The file tree is truncated (400 of 1410 paths), so no grep was possible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20protocol_standardization&system=pi-coding-agent&dimension=B5%20protocol_standardization&current=not_reported) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `not_reported` |  |  |  | agent-loop.ts content is missing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20loop_primitives&system=pi-coding-agent&dimension=C1%20loop_primitives&current=not_reported) |
| C2 | `planning_granularity` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20planning_granularity&system=pi-coding-agent&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20multi_agent_topology&system=pi-coding-agent&dimension=C3%20multi_agent_topology&current=not_reported) |
| C4 | `delegation_mechanism` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20delegation_mechanism&system=pi-coding-agent&dimension=C4%20delegation_mechanism&current=not_reported) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | The README says there is no built-in permission system, but other HITL points cannot be checked. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20human_in_loop&system=pi-coding-agent&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  | harness/session/state.ts content is missing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20short_term_state&system=pi-coding-agent&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | harness/skills.ts and .pi/skills exist in the tree; their content is missing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20long_term_memory&system=pi-coding-agent&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  | JSONL session storage files exist (session/jsonl/\*); the resume path is unverified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20state_persistence&system=pi-coding-agent&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20self_verification&system=pi-coding-agent&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  | ai/src/utils/retry.ts is an API transport retry and is not a retry policy. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20retry_policy&system=pi-coding-agent&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20rollback&system=pi-coding-agent&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20termination_condition&system=pi-coding-agent&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  | openai-prompt-cache.ts and cache tests suggest caching; the content is missing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20cost_controls&system=pi-coding-agent&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20timeouts&system=pi-coding-agent&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | medium | “By default, it runs with the permissions of the user and process that launched it.” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) | Runs on the host by default. Alternatives are documented: the Gondolin micro-VM extension, Docker, and OpenShell. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20execution_isolation&system=pi-coding-agent&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `full` | high | “Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access.” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) | Scope is relative to the host user. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20filesystem_access&system=pi-coding-agent&dimension=G2%20filesystem_access&current=full) |
| G3 | `network_policy` | `open` | high | “Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access.” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) | Network restriction is possible only via an external sandbox such as OpenShell. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20network_policy&system=pi-coding-agent&dimension=G3%20network_policy&current=open) |
| G4 | `permission_model` | `none` | high | “Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access.” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) | The documentation states the absence outright. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20permission_model&system=pi-coding-agent&dimension=G4%20permission_model&current=none) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  | The pi-telemetry package and harness/telemetry.ts exist; the export format is unverified. JSONL sessions exist. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tracing&system=pi-coding-agent&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20replayability&system=pi-coding-agent&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | The file tree is truncated, so no grep was possible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20eval_hooks&system=pi-coding-agent&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20guardrails&system=pi-coding-agent&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `swe` | medium | “Interactive coding agent CLI” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20target_domain&system=pi-coding-agent&dimension=M1%20target_domain&current=swe) |
| M2 | `open_source` | `yes` | medium | “MIT” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) | The license comes from the README License section; LICENSE:1 was not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20open_source&system=pi-coding-agent&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “Unified multi-provider LLM API (OpenAI, Anthropic, Google, etc.)” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20model_agnostic&system=pi-coding-agent&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v0.84.4 b79e4cc834970cca69daebffab7df1da7d1e52c4 2026-08-28” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20primary_artifact&system=pi-coding-agent&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | No tag history is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20first_release_date&system=pi-coding-agent&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v0.84.4 @ b79e4cc834970cca69daebffab7df1da7d1e52c4 (2026-08-28)` | high | “ref: tag:v0.84.4 b79e4cc834970cca69daebffab7df1da7d1e52c4 2026-08-28” | [README.md@b79e4cc](https://github.com/earendil-works/pi/blob/b79e4cc834970cca69daebffab7df1da7d1e52c4/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20pinned_version&system=pi-coding-agent&dimension=M6%20pinned_version&current=v0.84.4%20%40%20b79e4cc834970cca69daebffab7df1da7d1e52c4%20%282026-08-28%29) |
| M7 | `stars` | `not_reported` |  |  |  | No star count is in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20stars&system=pi-coding-agent&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20replayability&system=pi-coding-agent&dimension=H2%20replayability&current=not_reported)
2. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20rollback&system=pi-coding-agent&dimension=E3%20rollback&current=not_reported)
3. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20state_persistence&system=pi-coding-agent&dimension=D3%20state_persistence&current=not_reported)
4. B5 `protocol_standardization` (Protocol standardization): 84.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20protocol_standardization&system=pi-coding-agent&dimension=B5%20protocol_standardization&current=not_reported)
5. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20timeouts&system=pi-coding-agent&dimension=F3%20timeouts&current=not_reported)
6. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20cost_controls&system=pi-coding-agent&dimension=F2%20cost_controls&current=not_reported)
7. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20context_compaction&system=pi-coding-agent&dimension=A3%20context_compaction&current=not_reported)
8. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tool_count&system=pi-coding-agent&dimension=B2%20tool_count&current=not_reported)
9. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20human_in_loop&system=pi-coding-agent&dimension=C5%20human_in_loop&current=not_reported)
10. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20guardrails&system=pi-coding-agent&dimension=H4%20guardrails&current=not_reported)
11. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tool_schema_source&system=pi-coding-agent&dimension=B4%20tool_schema_source&current=not_reported)
12. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20edit_primitive&system=pi-coding-agent&dimension=B3%20edit_primitive&current=not_reported)
13. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20long_term_memory&system=pi-coding-agent&dimension=D2%20long_term_memory&current=not_reported)
14. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20eval_hooks&system=pi-coding-agent&dimension=H3%20eval_hooks&current=not_reported)
15. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tracing&system=pi-coding-agent&dimension=H1%20tracing&current=not_reported)
16. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20retry_policy&system=pi-coding-agent&dimension=E2%20retry_policy&current=not_reported)
17. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20tool_call_format&system=pi-coding-agent&dimension=B1%20tool_call_format&current=not_reported)
18. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20self_verification&system=pi-coding-agent&dimension=E1%20self_verification&current=not_reported)
19. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20short_term_state&system=pi-coding-agent&dimension=D1%20short_term_state&current=not_reported)
20. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20termination_condition&system=pi-coding-agent&dimension=F1%20termination_condition&current=not_reported)
21. C4 `delegation_mechanism` (Delegation mechanism): 31.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20delegation_mechanism&system=pi-coding-agent&dimension=C4%20delegation_mechanism&current=not_reported)
22. A1 `system_prompt_style` (System-prompt style): 30.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20system_prompt_style&system=pi-coding-agent&dimension=A1%20system_prompt_style&current=not_reported)
23. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20env_context_strategy&system=pi-coding-agent&dimension=A2%20env_context_strategy&current=not_reported)
24. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20observation_format&system=pi-coding-agent&dimension=A4%20observation_format&current=not_reported)
25. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20planning_granularity&system=pi-coding-agent&dimension=C2%20planning_granularity&current=not_reported)
26. C3 `multi_agent_topology` (Multi-agent topology): 1.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20multi_agent_topology&system=pi-coding-agent&dimension=C3%20multi_agent_topology&current=not_reported)
27. C1 `loop_primitives` (Loop primitive(s)): 1.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20loop_primitives&system=pi-coding-agent&dimension=C1%20loop_primitives&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20%3Cdimension%3E&system=pi-coding-agent> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=pi-coding-agent>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
