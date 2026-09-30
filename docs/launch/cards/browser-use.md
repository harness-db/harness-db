# Browser Use: HARNESS-DB cell card

| | |
|---|---|
| System id | `browser-use` |
| Pinned version | [0.13.8 @ `eb4126921bea`](https://github.com/browser-use/browser-use/commit/eb4126921bea3373f91afc49fb4b59d6eda7fed6) (2026-08-16) |
| Repository | <https://github.com/browser-use/browser-use> |
| Stars (sampling-frame snapshot) | 115,306 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 11 coded, 27 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=browser-use> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | low | “Only use \`extend\_system\_message\` or \`override\_system\_message\` when you intentionally want to customize the default behavior for your task.” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) | Multiple system prompt files (system\_prompt.md, \_flash, \_no\_thinking, \_anthropic\_flash) in file tree suggest selection by model/flags; mechanism not visible. Could be templated. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20system_prompt_style&system=browser-use&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `not_reported` |  |  |  | Source of browser\_use/dom/serializer and agent/service.py not in bundle; only file tree available. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20env_context_strategy&system=browser-use&dimension=A2%20env_context_strategy&current=not_reported) |
| A3 | `context_compaction` | `not_reported` |  |  |  | message\_manager/service.py listed but not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20context_compaction&system=browser-use&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `not_reported` |  |  |  | screenshot\_watchdog.py and dom serializer exist in tree but contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20observation_format&system=browser-use&dimension=A4%20observation_format&current=not_reported) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `not_reported` |  |  |  | Parser code not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tool_call_format&system=browser-use&dimension=B1%20tool_call_format&current=not_reported) |
| B2 | `tool_count` | `not_reported` |  |  |  | tools/service.py not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tool_count&system=browser-use&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | filesystem/file\_system.py exists but tool definitions not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20edit_primitive&system=browser-use&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `auto_generated, mcp` | low | “@tools.action(description='Description of what this tool does.') def custom\_tool(param: str) -\> str:” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) | Decorator over typed function implies signature-derived schema; browser\_use/mcp/client.py in tree suggests MCP client. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tool_schema_source&system=browser-use&dimension=B4%20tool_schema_source&current=auto_generated%7Cmcp) |
| B5 | `protocol_standardization` | `mcp` | medium | “\<!-- mcp-name: com.browser-use/browser-use --\>” | [README.md:1@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md#L1) | browser\_use/mcp/server.py and client.py in file tree. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20protocol_standardization&system=browser-use&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `not_reported` |  |  |  | agent/service.py run loop not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20loop_primitives&system=browser-use&dimension=C1%20loop_primitives&current=not_reported) |
| C2 | `planning_granularity` | `not_reported` |  |  |  | Prompt and agent views not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20planning_granularity&system=browser-use&dimension=C2%20planning_granularity&current=not_reported) |
| C3 | `multi_agent_topology` | `single` | low | “agent = Agent( task="Find the number of stars of the browser-use repo",” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) | Parallel-agent examples exist; delegation mechanism not visible. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20multi_agent_topology&system=browser-use&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `not_reported` |  |  |  | No agent factory code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20delegation_mechanism&system=browser-use&dimension=C4%20delegation_mechanism&current=not_reported) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | No run loop code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20human_in_loop&system=browser-use&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `not_reported` |  |  |  | agent/views.py not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20short_term_state&system=browser-use&dimension=D1%20short_term_state&current=not_reported) |
| D2 | `long_term_memory` | `not_reported` |  |  |  | skills/ module in tree; cloud README claims memory for hosted agent only; source not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20long_term_memory&system=browser-use&dimension=D2%20long_term_memory&current=not_reported) |
| D3 | `state_persistence` | `not_reported` |  |  |  | No persistence code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20state_persistence&system=browser-use&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `not_reported` |  |  |  | agent/judge.py in tree suggests llm\_judge; contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20self_verification&system=browser-use&dimension=E1%20self_verification&current=not_reported) |
| E2 | `retry_policy` | `not_reported` |  |  |  | No retry code in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20retry_policy&system=browser-use&dimension=E2%20retry_policy&current=not_reported) |
| E3 | `rollback` | `not_reported` |  |  |  | No tool definitions in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20rollback&system=browser-use&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `not_reported` |  |  |  | Run loop not in bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20termination_condition&system=browser-use&dimension=F1%20termination_condition&current=not_reported) |
| F2 | `cost_controls` | `not_reported` |  |  |  | tokens/ and llm/tests/test\_anthropic\_cache.py and examples/features/fallback\_model.py in tree; contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20cost_controls&system=browser-use&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  | browser/\_cdp\_timeout.py in tree; contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20timeouts&system=browser-use&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `subprocess` | low | “Free, and runs on your own machine” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) | Local browser; remote cloud browsers and sandbox/ module reachable. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20execution_isolation&system=browser-use&dimension=G1%20execution_isolation&current=subprocess) |
| G2 | `filesystem_access` | `not_reported` |  |  |  | filesystem/file\_system.py not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20filesystem_access&system=browser-use&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  | examples/features/restrict\_urls.py and blocked\_domains.py suggest allowlist; source not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20network_policy&system=browser-use&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | security\_watchdog.py in tree; contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20permission_model&system=browser-use&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `not_reported` |  |  |  | observability.py and examples/observability/openLLMetry.py in tree; contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tracing&system=browser-use&dimension=H1%20tracing&current=not_reported) |
| H2 | `replayability` | `not_reported` |  |  |  | examples/features/rerun\_history.py in tree; contents not provided. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20replayability&system=browser-use&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `none` | low | “Full benchmark is open source: \*\*\[browser-use/benchmark\](https://github.com/browser-use/benchmark)\*\*.” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) | Sibling eval repo (ambiguity H3); cloud\_evals workflows exist in .github. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20eval_hooks&system=browser-use&dimension=H3%20eval_hooks&current=none) |
| H4 | `guardrails` | `not_reported` |  |  |  | sensitive\_data and blocked\_domains examples exist; source not included. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20guardrails&system=browser-use&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `web` | high | “Browser Use lets an AI agent use a web browser the same way humans do” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20target_domain&system=browser-use&dimension=M1%20target_domain&current=web) |
| M2 | `open_source` | `yes` | high | “This open-source library is licensed under the MIT License.” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) | LICENSE file not opened; cloud agent is closed. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20open_source&system=browser-use&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “You only need to choose an LLM provider (like OpenAI, Google, ChatBrowserUse, or run local models with Ollama).” | [README.md@eb41269](https://github.com/browser-use/browser-use/blob/eb4126921bea3373f91afc49fb4b59d6eda7fed6/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20model_agnostic&system=browser-use&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:0.13.8 eb4126921bea3373f91afc49fb4b59d6eda7fed6 2026-08-16” | repo metadata@eb41269 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20primary_artifact&system=browser-use&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | Tag history not provided; citation year 2024. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20first_release_date&system=browser-use&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `0.13.8 @ eb4126921bea3373f91afc49fb4b59d6eda7fed6 (2026-08-16)` | high | “ref: tag:0.13.8 eb4126921bea3373f91afc49fb4b59d6eda7fed6 2026-08-16” | repo metadata@eb41269 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20pinned_version&system=browser-use&dimension=M6%20pinned_version&current=0.13.8%20%40%20eb4126921bea3373f91afc49fb4b59d6eda7fed6%20%282026-08-16%29) |
| M7 | `stars` | `not_reported` |  |  |  | Star count not in evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20stars&system=browser-use&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20network_policy&system=browser-use&dimension=G3%20network_policy&current=not_reported)
2. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20replayability&system=browser-use&dimension=H2%20replayability&current=not_reported)
3. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20filesystem_access&system=browser-use&dimension=G2%20filesystem_access&current=not_reported)
4. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20rollback&system=browser-use&dimension=E3%20rollback&current=not_reported)
5. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20state_persistence&system=browser-use&dimension=D3%20state_persistence&current=not_reported)
6. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20timeouts&system=browser-use&dimension=F3%20timeouts&current=not_reported)
7. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20permission_model&system=browser-use&dimension=G4%20permission_model&current=not_reported)
8. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20cost_controls&system=browser-use&dimension=F2%20cost_controls&current=not_reported)
9. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20context_compaction&system=browser-use&dimension=A3%20context_compaction&current=not_reported)
10. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tool_count&system=browser-use&dimension=B2%20tool_count&current=not_reported)
11. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20human_in_loop&system=browser-use&dimension=C5%20human_in_loop&current=not_reported)
12. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20guardrails&system=browser-use&dimension=H4%20guardrails&current=not_reported)
13. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20edit_primitive&system=browser-use&dimension=B3%20edit_primitive&current=not_reported)
14. D2 `long_term_memory` (Long-term memory): 69.0% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20long_term_memory&system=browser-use&dimension=D2%20long_term_memory&current=not_reported)
15. H1 `tracing` (Tracing): 58.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tracing&system=browser-use&dimension=H1%20tracing&current=not_reported)
16. E2 `retry_policy` (Retry policy): 56.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20retry_policy&system=browser-use&dimension=E2%20retry_policy&current=not_reported)
17. B1 `tool_call_format` (Tool-call format): 52.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20tool_call_format&system=browser-use&dimension=B1%20tool_call_format&current=not_reported)
18. E1 `self_verification` (Self-verification): 39.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20self_verification&system=browser-use&dimension=E1%20self_verification&current=not_reported)
19. D1 `short_term_state` (Short-term state): 34.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20short_term_state&system=browser-use&dimension=D1%20short_term_state&current=not_reported)
20. F1 `termination_condition` (Termination condition): 32.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20termination_condition&system=browser-use&dimension=F1%20termination_condition&current=not_reported)
21. C4 `delegation_mechanism` (Delegation mechanism): 31.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20delegation_mechanism&system=browser-use&dimension=C4%20delegation_mechanism&current=not_reported)
22. A2 `env_context_strategy` (Repo/environment context strategy): 27.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20env_context_strategy&system=browser-use&dimension=A2%20env_context_strategy&current=not_reported)
23. A4 `observation_format` (Observation formatting): 24.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20observation_format&system=browser-use&dimension=A4%20observation_format&current=not_reported)
24. C2 `planning_granularity` (Planning granularity): 13.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20planning_granularity&system=browser-use&dimension=C2%20planning_granularity&current=not_reported)
25. C1 `loop_primitives` (Loop primitive(s)): 1.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20loop_primitives&system=browser-use&dimension=C1%20loop_primitives&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20%3Cdimension%3E&system=browser-use> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=browser-use>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
