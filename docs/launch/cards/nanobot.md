# nanobot: HARNESS-DB cell card

| | |
|---|---|
| System id | `nanobot` |
| Pinned version | [v0.3.0 @ `3f602fbc8c10`](https://github.com/hkuds/nanobot/commit/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec) (2026-07-25) |
| Repository | <https://github.com/hkuds/nanobot> |
| Stars (sampling-frame snapshot) | 48,224 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 21 coded, 17 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=nanobot> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | medium | “\`ContextBuilder\` combines project instructions with agent-owned profile and memory.” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | The prompt is assembled from project AGENTS.md, SOUL.md, USER.md, memory and skills. The builder code (nanobot/agent/context.py) is not in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20system_prompt_style&system=nanobot&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “use tools such as files, shell, web search, web fetch, MCP, cron, image generation, and subagents” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) | Project AGENTS.md instructions are injected, but no file-tree summary is shown in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20env_context_strategy&system=nanobot&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `not_reported` |  |  |  | Docs mention 'Session storage and compaction' in nanobot/session/manager.py and a nanobot/agent/autocompact.py file. The mechanism is not visible, so no value can be assigned. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20context_compaction&system=nanobot&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | The observation conversion code is not in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20observation_format&system=nanobot&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | The runner/provider parser is not in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20tool_call_format&system=nanobot&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | The default tool list is not in the evidence. Tool files seen include filesystem, shell, search, web, cron, message, spawn, apply\_patch and self. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20tool_count&system=nanobot&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `unified_diff` | low | “nanobot/agent/tools/apply\_patch.py” | file tree@3f602fb | Inferred from the file name only. The contents of filesystem.py edit commands were not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20edit_primitive&system=nanobot&dimension=B3%20edit_primitive&current=unified_diff) |
| B4 | `tool_schema_source` | `mcp` | medium | “MCP \| Add \`tools.mcpServers\` config” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | The native schema source (tools/schema.py) was not visible, so hand\_written vs auto\_generated is unknown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20tool_schema_source&system=nanobot&dimension=B4%20tool_schema_source&current=mcp) |
| B5 | `protocol_standardization` | `mcp` | high | “MCP tools \| \`nanobot/agent/tools/mcp.py\`” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20protocol_standardization&system=nanobot&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | medium | “feeds tool results back into the model;” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | event\_driven is based on the MessageBus inbound/outbound events plus cron and trigger automations. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20loop_primitives&system=nanobot&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | Goals are mentioned, but no plan object is visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20planning_granularity&system=nanobot&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `orchestrator_workers` | low | “Consult inline subagents without leaving the current task” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) | The subagents/spawn tool is listed among the standard tools. Whether it is on by default is unverified. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20multi_agent_topology&system=nanobot&dimension=C3%20multi_agent_topology&current=orchestrator_workers) |
| C4 | `delegation_mechanism` | `subagent_spawn` | low | “use tools such as files, shell, web search, web fetch, MCP, cron, image generation, and subagents” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) | Based on nanobot/agent/tools/spawn.py and subagent.py. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20delegation_mechanism&system=nanobot&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | goal\_permission.py exists, but its content was not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20human_in_loop&system=nanobot&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20short_term_state&system=nanobot&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `file_notes, skill_library` | high | “Long-term memory \| \`\<workspace\>/memory/MEMORY.md\`” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | Skills come from '\<workspace\>/skills/' and nanobot/skills/. Memory is consolidated by Dream. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20long_term_memory&system=nanobot&dimension=D2%20long_term_memory&current=file_notes%7Cskill_library) |
| D3 | `state_persistence` | `full_resume` | low | “Session history is the near-term conversation replay.” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | Session JSONL files persist across turns. The reload code path was not seen. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20state_persistence&system=nanobot&dimension=D3%20state_persistence&current=full_resume) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20self_verification&system=nanobot&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  | Model fallback is provider failover, not a task retry. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20retry_policy&system=nanobot&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20rollback&system=nanobot&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `max_steps, model_declared` | medium | “stops when a final answer is produced or runtime limits are hit.” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | Iteration limits are mentioned. Other limits were not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20termination_condition&system=nanobot&dimension=F1%20termination_condition&current=max_steps%7Cmodel_declared) |
| F2 | `cost_controls` | `caching` | low | “docs/guides/configure-ollama-prompt-cache.md” | file tree@3f602fb | fallbackModels is failover, not routing. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20cost_controls&system=nanobot&dimension=F2%20cost_controls&current=caching) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20timeouts&system=nanobot&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “Shell sandboxing \| \`nanobot/agent/tools/shell.py\`” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) | Runs on the host by default. Docker and a bwrap compose file are shipped as alternatives. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20execution_isolation&system=nanobot&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `scoped` | medium | “Keep \`tools.restrictToWorkspace\` enabled unless the network setup explicitly” | [docs/agent-social-network.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/agent-social-network.md) | Scoped relative to the host subprocess boundary. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20filesystem_access&system=nanobot&dimension=G2%20filesystem_access&current=scoped) |
| G3 | `network_policy` | `not_reported` |  |  |  | SSRF checks exist in security/network.py. The policy details were not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20network_policy&system=nanobot&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20permission_model&system=nanobot&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `structured_traces` | low | “Configure providers, fallback models, Langfuse, MCP, web tools, or security” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) | Langfuse integration and session JSONL are present. OTel was not confirmed. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20tracing&system=nanobot&dimension=H1%20tracing&current=structured_traces) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20replayability&system=nanobot&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | The file tree was truncated, so no grep was possible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20eval_hooks&system=nanobot&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `action_policies` | medium | “SSRF/network checks \| \`nanobot/security/network.py\`, \`nanobot/agent/tools/web.py\`” | [docs/architecture.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/docs/architecture.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20guardrails&system=nanobot&dimension=H4%20guardrails&current=action_policies) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, other, web` | medium | “nanobot is a self-hosted personal AI agent runtime.” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) | Other = personal assistant/chat. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20target_domain&system=nanobot&dimension=M1%20target_domain&current=general_tool_use%7Cother%7Cweb) |
| M2 | `open_source` | `yes` | medium | “license-MIT” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20open_source&system=nanobot&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “OpenAI-compatible APIs, local LLMs, image generation, search, and fallbacks.” | [README.md@3f602fb](https://github.com/hkuds/nanobot/blob/3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20model_agnostic&system=nanobot&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v0.3.0 3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec 2026-07-25” | repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20primary_artifact&system=nanobot&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20first_release_date&system=nanobot&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v0.3.0 @ 3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec (2026-07-25)` | high | “ref: tag:v0.3.0 3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec 2026-07-25” | repo metadata | The README at this tag still says 'Coming next: v0.3.0'. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20pinned_version&system=nanobot&dimension=M6%20pinned_version&current=v0.3.0%20%40%203f602fbc8c104b5af27aa4d3520e7dcef2fa70ec%20%282026-07-25%29) |
| M7 | `stars` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20stars&system=nanobot&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20network_policy&system=nanobot&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20replayability&system=nanobot&dimension=H2%20replayability&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20rollback&system=nanobot&dimension=E3%20rollback&current=not_reported)
4. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20timeouts&system=nanobot&dimension=F3%20timeouts&current=not_reported)
5. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20permission_model&system=nanobot&dimension=G4%20permission_model&current=not_reported)
6. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20context_compaction&system=nanobot&dimension=A3%20context_compaction&current=not_reported)
7. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20tool_count&system=nanobot&dimension=B2%20tool_count&current=not_reported)
8. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20human_in_loop&system=nanobot&dimension=C5%20human_in_loop&current=not_reported)
9. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20eval_hooks&system=nanobot&dimension=H3%20eval_hooks&current=not_reported)
10. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20retry_policy&system=nanobot&dimension=E2%20retry_policy&current=not_reported)
11. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20tool_call_format&system=nanobot&dimension=B1%20tool_call_format&current=not_reported)
12. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20self_verification&system=nanobot&dimension=E1%20self_verification&current=not_reported)
13. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20short_term_state&system=nanobot&dimension=D1%20short_term_state&current=not_reported)
14. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20observation_format&system=nanobot&dimension=A4%20observation_format&current=not_reported)
15. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20planning_granularity&system=nanobot&dimension=C2%20planning_granularity&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20%3Cdimension%3E&system=nanobot> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=nanobot>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
