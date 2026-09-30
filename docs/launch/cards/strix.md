# Strix: HARNESS-DB cell card

| | |
|---|---|
| System id | `strix` |
| Pinned version | [v1.5.3 @ `7cc9fa9faa01`](https://github.com/usestrix/strix/commit/7cc9fa9faa0179fc7e35111102fe3d20a9028393) (2026-08-10) |
| Repository | <https://github.com/usestrix/strix> |
| Stars (sampling-frame snapshot) | 63,014 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 31 coded, 6 `not_reported`, 1 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=strix> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | medium | “The skills are injected into the agent's system prompt, giving it access to:” | [docs/advanced/skills.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/skills.mdx)† | strix/agents/prompts/system\_prompt.jinja base template plus runtime-selected skills injected into system prompt | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20system_prompt_style&system=strix&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | medium | “Strix agents use specialized tools to test your applications like a real penetration tester would.” | [docs/tools/overview.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/tools/overview.mdx)† | agent explores via terminal, browser, code analysis tools; no upfront file tree injection described | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20env_context_strategy&system=strix&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `summarize` | medium | “Timeout in seconds for memory compression operations (context summarization).” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | strix/llm/compaction.py; STRIX\_MEMORY\_COMPRESSOR\_TIMEOUT | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20context_compaction&system=strix&dimension=A3%20context_compaction&current=summarize) |
| A4 | `observation_format` | `raw_text, screenshots` | medium | “Playwright-powered Chrome for interacting with web UIs.” | [docs/tools/overview.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/tools/overview.mdx)† | terminal/proxy produce raw\_text; browser and view\_image tool produce screenshots | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20observation_format&system=strix&dimension=A4%20observation_format&current=raw_text%7Cscreenshots) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | medium | “Applies to both the LiteLLM and native OpenAI routing paths.” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | strix/config/tool\_call\_ids.py and litellm/native OpenAI routing; parser source not shown | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20tool_call_format&system=strix&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `14` | low | “strix/tools/agents\_graph/tools.py” | file tree (strix/tools/) | counted tool modules: agent\_browser, agents\_graph, apply\_patch, finish, load\_skill, notes, proxy, reporting, respond, shell, thinking, todo, view\_image, web\_search; per-schema counts not visible | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20tool_count&system=strix&dimension=B2%20tool_count&current=14) |
| B3 | `edit_primitive` | `unified_diff` | medium | “strix/tools/apply\_patch/README.md” | file tree (strix/tools/apply\_patch/) | apply\_patch tool plus FileEditRenderer; exact edit commands not shown in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20edit_primitive&system=strix&dimension=B3%20edit_primitive&current=unified_diff) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  | tool schema production code not included in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20tool_schema_source&system=strix&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `none` | low | “This installs four skills: penetration-testing-with-strix” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | skills use SKILL.md (agentskills.io); no MCP/A2A client seen in file tree | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20protocol_standardization&system=strix&dimension=B5%20protocol_standardization&current=none) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | medium | “When remote OTEL vars are not set, Strix still writes complete run telemetry locally to:” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | events.jsonl event stream; strix/core/runner.py loop; multi-agent orchestration | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20loop_primitives&system=strix&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `explicit_plan_object` | medium | “strix/tools/todo/tools.py” | file tree (strix/tools/todo/) | todo tool tracks tasks across steps; TodoRenderer in viewer | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20planning_granularity&system=strix&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `orchestrator_workers` | medium | “Multi-agent orchestration - teams of AI pentesters that collaborate and scale” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | root\_agent coordination skill; agents\_graph spawns specialized worker agents | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20multi_agent_topology&system=strix&dimension=C3%20multi_agent_topology&current=orchestrator_workers) |
| C4 | `delegation_mechanism` | `subagent_spawn` | medium | “When Strix spawns an agent for a specific task, it selects up to 5 relevant skills” | [docs/advanced/skills.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/skills.mdx)† | strix/tools/agents\_graph/tools.py creates agents via graph | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20delegation_mechanism&system=strix&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `none` | low | “send instructions to a live scan from the browser to redirect the agents mid-run.” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | steering allows human to redirect but no per-action/plan/completion gating point; runs autonomously by default | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20human_in_loop&system=strix&dimension=C5%20human_in_loop&current=none) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | medium | “strix/tools/todo/tools.py” | file tree (strix/tools/); strix/report/state.py | todo/notes plus report state object maintained across steps | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20short_term_state&system=strix&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `skill_library` | high | “Skills are specialized knowledge packages that enhance agent capabilities. They live in \`strix/skills/\`” | [docs/contributing.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/contributing.mdx)† | continuous learning across runs is cloud-only | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20long_term_memory&system=strix&dimension=D2%20long_term_memory&current=skill_library) |
| D3 | `state_persistence` | `not_reported` |  |  |  | session/runner code not shown; resume path not evident in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20state_persistence&system=strix&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `llm_judge` | medium | “Model used to judge whether a candidate finding duplicates an existing report.” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | STRIX\_DEDUPE\_MODEL judges findings; PoC validation is agent-driven not harness-enforced | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20self_verification&system=strix&dimension=E1%20self_verification&current=llm_judge) |
| E2 | `retry_policy` | `none` | medium | “Maximum number of retries for LLM API calls on transient failures.” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | STRIX\_LLM\_MAX\_RETRIES is API-transport retry, not task-level retry | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20retry_policy&system=strix&dimension=E2%20retry_policy&current=none) |
| E3 | `rollback` | `not_reported` |  |  |  | no undo/revert/rollback surface visible in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20rollback&system=strix&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `cost_cap, max_steps, model_declared` | medium | “strix/config/tool\_call\_limits.py” | file tree (strix/config/); tests/test\_e2e\_budget\_lifecycle.py | finish tool = model\_declared; budget lifecycle = cost\_cap; tool\_call\_limits = step cap | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20termination_condition&system=strix&dimension=F1%20termination_condition&current=cost_cap%7Cmax_steps%7Cmodel_declared) |
| F2 | `cost_controls` | `model_routing, token_budget` | medium | “you can route it to a smaller/cheaper model without affecting the agents that do the actual testing.” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | budget lifecycle (tests/test\_e2e\_budget\_lifecycle.py) = token\_budget; dedupe model routing | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20cost_controls&system=strix&dimension=F2%20cost_controls&current=model_routing%7Ctoken_budget) |
| F3 | `timeouts` | `per_tool` | medium | “Maximum execution time in seconds for sandbox operations.” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | STRIX\_SANDBOX\_EXECUTION\_TIMEOUT per operation; no run-level wall clock timeout found | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20timeouts&system=strix&dimension=F3%20timeouts&current=per_tool) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `container` | high | “First run automatically pulls the sandbox Docker image.” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | STRIX\_RUNTIME\_BACKEND default=docker; STRIX\_IMAGE ghcr.io/usestrix/strix-sandbox | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20execution_isolation&system=strix&dimension=G1%20execution_isolation&current=container) |
| G2 | `filesystem_access` | `full` | low | “strix agents come equipped with a comprehensive offensive security toolkit” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | agent has terminal root inside sandbox container; scoped relative to container | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20filesystem_access&system=strix&dimension=G2%20filesystem_access&current=full) |
| G3 | `network_policy` | `unresolved` |  |  |  | unresolved after the repair pass (quote\_not\_in\_bundle). pentesting tool requires network egress to targets; no network restriction option seen | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20network_policy&system=strix&dimension=G3%20network_policy&current=unresolved) |
| G4 | `permission_model` | `none` | low | “Autonomous AI hackers that find and fix your app’s vulnerabilities.” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | runs autonomously; no per-call permission surface described | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20permission_model&system=strix&dimension=G4%20permission_model&current=none) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `opentelemetry` | high | “OTLP/Traceloop base URL for remote OpenTelemetry export.” | [docs/advanced/configuration.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/advanced/configuration.mdx)† | local events.jsonl always written; remote OTEL enabled when TRACELOOP vars set | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20tracing&system=strix&dimension=H1%20tracing&current=opentelemetry) |
| H2 | `replayability` | `not_reported` |  |  |  | transcript/events persisted but no replay/resume path shown in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20replayability&system=strix&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `built_in` | low | “benchmarks/README.md” | file tree (benchmarks/) | benchmarks directory ships in repo; runner details not shown | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20eval_hooks&system=strix&dimension=H3%20eval_hooks&current=built_in) |
| H4 | `guardrails` | `output_filters` | low | “strix/utils/secret\_files.py” | file tree (strix/utils/) | secret file handling suggests output masking; no config surface fully shown | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20guardrails&system=strix&dimension=H4%20guardrails&current=output_filters) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `swe, web` | high | “The open-source AI pentesting tool. Autonomous AI hackers that find and fix your app’s vulnerabilities.” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | security testing of code repos and live web apps | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20target_domain&system=strix&dimension=M1%20target_domain&current=swe%7Cweb) |
| M2 | `open_source` | `yes` | high | “License-Apache%202.0” | [README.md](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/README.md)† | LICENSE Apache 2.0 | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20open_source&system=strix&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “Strix uses \[LiteLLM\](https://docs.litellm.ai/docs/providers) for model compatibility, supporting 100+ LLM providers.” | [docs/llm-providers/overview.mdx](https://github.com/usestrix/strix/blob/7cc9fa9faa0179fc7e35111102fe3d20a9028393/docs/llm-providers/overview.mdx)† |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20model_agnostic&system=strix&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:v1.5.3 7cc9fa9faa0179fc7e35111102fe3d20a9028393 2026-08-10” | github:usestrix/strix |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20primary_artifact&system=strix&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | first release/tag date not provided in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20first_release_date&system=strix&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `v1.5.3 @ 7cc9fa9faa0179fc7e35111102fe3d20a9028393 (2026-08-10)` | high | “ref: tag:v1.5.3 7cc9fa9faa0179fc7e35111102fe3d20a9028393 2026-08-10” | github:usestrix/strix |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20pinned_version&system=strix&dimension=M6%20pinned_version&current=v1.5.3%20%40%207cc9fa9faa0179fc7e35111102fe3d20a9028393%20%282026-08-10%29) |
| M7 | `stars` | `not_reported` |  |  |  | star count not provided in evidence | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20stars&system=strix&dimension=M7%20stars&current=not_reported) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20replayability&system=strix&dimension=H2%20replayability&current=not_reported)
2. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20rollback&system=strix&dimension=E3%20rollback&current=not_reported)
3. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20state_persistence&system=strix&dimension=D3%20state_persistence&current=not_reported)
4. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20tool_schema_source&system=strix&dimension=B4%20tool_schema_source&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20%3Cdimension%3E&system=strix> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=strix>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
