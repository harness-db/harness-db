# Codex CLI: HARNESS-DB cell card

| | |
|---|---|
| System id | `codex-cli` |
| Pinned version | [rust-v0.153.0-alpha.2 @ `73919571da60`](https://github.com/openai/codex/commit/73919571da608749b867134722fe3b42c1c6097f) (2026-08-31) |
| Repository | <https://github.com/openai/codex> |
| Papers | [arXiv:2604.11518](https://arxiv.org/abs/2604.11518) |
| Stars (sampling-frame snapshot) | 125,294 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 31 coded, 6 `not_reported`, 1 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=codex-cli> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | low | “whose contents are the “user instructions,” which are not sourced from a single file but are aggregated across multiple sources” | blog 'Unrolling the Codex agent loop', Building the initial prompt | Instructions from model\_instructions\_file or model base\_instructions, plus permissions, developer\_instructions, AGENTS.md, skills and environment\_context messages. Blog source, not code. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20system_prompt_style&system=codex-cli&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `agent_driven_navigation` | low | “Let Codex inspect files, make edits, and run the tools already installed on your machine.” | grey:codex-cli web page | environment\_context injects only cwd and shell; AGENTS.md files are injected as instructions. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20env_context_strategy&system=codex-cli&dimension=A2%20env_context_strategy&current=agent_driven_navigation) |
| A3 | `context_compaction` | `not_reported` |  |  |  | The compaction code for the Rust original is not in the evidence bundle. The blog is truncated before its compaction section. The paper's three-phase compaction describes the Python port, not this repo. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20context_compaction&system=codex-cli&dimension=A3%20context_compaction&current=not_reported) |
| A4 | `observation_format` | `raw_text` | low | “"output": "\<p align=\\"center\\"\>\<code\>npm i -g @openai/codex\</code\>..."” | blog 'Unrolling the Codex agent loop', The first turn | function\_call\_output is text. Image input exists for user prompts; image tool observations are not evidenced. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20observation_format&system=codex-cli&dimension=A4%20observation_format&current=raw_text) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | medium | “"type": "function\_call",” | blog 'Unrolling the Codex agent loop', The first turn | Responses API function calls. The shell tool takes a command array. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20tool_call_format&system=codex-cli&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `not_reported` |  |  |  | No tool registry is in the bundle. The blog lists an example with shell, update\_plan and web\_search, which is not a full default list. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20tool_count&system=codex-cli&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `unified_diff` | low | “apply\_patch: Applies unified diffs to files with conflict detection.” | [arXiv:2604.11518 Sec. III.B](https://arxiv.org/abs/2604.11518) | Source is a paper on the Python port claiming 1:1 parity. The Rust tool definition is not in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20edit_primitive&system=codex-cli&dimension=B3%20edit_primitive&current=unified_diff) |
| B4 | `tool_schema_source` | `hand_written, mcp` | low | “tools provided by the user, usually via MCP servers” | blog 'Unrolling the Codex agent loop', Building the initial prompt | The hand\_written value is inferred from the JSON tool definitions shown in the blog. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20tool_schema_source&system=codex-cli&dimension=B4%20tool_schema_source&current=hand_written%7Cmcp) |
| B5 | `protocol_standardization` | `mcp` | high | “use rmcp::model::CallToolResult;” | [codex-rs/mcp-server/src/codex\_tool\_runner.rs:28@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/codex-rs/mcp-server/src/codex_tool_runner.rs#L28) | Codex acts as both MCP server and client. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20protocol_standardization&system=codex-cli&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `event_driven, react` | medium | “This process repeats until the model stops emitting tool calls and instead produces a message for the user” | blog 'Unrolling the Codex agent loop', The agent loop | event\_driven is supported by the next\_event loop in codex\_tool\_runner.rs. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20loop_primitives&system=codex-cli&dimension=C1%20loop_primitives&current=event_driven%7Creact) |
| C2 | `planning_granularity` | `explicit_plan_object` | medium | “"name": "update\_plan",” | blog 'Unrolling the Codex agent loop', Building the initial prompt |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20planning_granularity&system=codex-cli&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `single` | low | “Ask Codex to delegate focused work to specialized agents, then bring their findings back into the main terminal session.” | grey:codex-cli web page | Default is a single agent. Subagents (orchestrator\_workers) are reachable on request. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20multi_agent_topology&system=codex-cli&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `subagent_spawn` | medium | “Constructor-injected host helper for extensions that need to spawn subagents.” | [codex-rs/ext/extension-api/src/capabilities/agent.rs:9@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/codex-rs/ext/extension-api/src/capabilities/agent.rs#L9) | Subagents are spawned on model/user request. Whether this is default-enabled is unclear. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20delegation_mechanism&system=codex-cli&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `configurable, on_permission` | medium | “EventMsg::ExecApprovalRequest(ev) =\> {” | [codex-rs/mcp-server/src/codex\_tool\_runner.rs@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/codex-rs/mcp-server/src/codex_tool_runner.rs) | Approval policy is selectable via /permissions. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20human_in_loop&system=codex-cli&dimension=C5%20human_in_loop&current=configurable%7Con_permission) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “"name": "update\_plan",” | blog 'Unrolling the Codex agent loop', Building the initial prompt |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20short_term_state&system=codex-cli&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `file_notes, skill_library` | medium | “Package repeatable instructions as skills, then add plugins” | grey:codex-cli web page | AGENTS.md files are re-read across runs. Skills are loaded via ExecutorSkillProvider. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20long_term_memory&system=codex-cli&dimension=D2%20long_term_memory&current=file_notes%7Cskill_library) |
| D3 | `state_persistence` | `full_resume` | low | “Reopen a recent chat from the current repository, or search across local chats when you need to return to older work.” | grey:codex-cli web page | Based on codex resume. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20state_persistence&system=codex-cli&dimension=D3%20state_persistence&current=full_resume) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `self_critique` | low | “Run a dedicated review against uncommitted changes, a commit, or a base branch.” | grey:codex-cli web page | The /review command is user-invoked, not automatic. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20self_verification&system=codex-cli&dimension=E1%20self_verification&current=self_critique) |
| E2 | `retry_policy` | `none` | low | “each turn always ends with an assistant message” | blog 'Unrolling the Codex agent loop', The agent loop |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20retry_policy&system=codex-cli&dimension=E2%20retry_policy&current=none) |
| E3 | `rollback` | `not_reported` |  |  |  | The web page advises the user to create Git checkpoints. No harness-side undo code is in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20rollback&system=codex-cli&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `model_declared` | medium | “This process repeats until the model stops emitting tool calls and instead produces a message for the user” | blog 'Unrolling the Codex agent loop', The agent loop | The paper's 50-turn cap describes the Python port. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20termination_condition&system=codex-cli&dimension=F1%20termination_condition&current=model_declared) |
| F2 | `cost_controls` | `caching` | medium | “This is why prompt caching is so important, as it enables us to reuse computation from a previous inference call.” | blog 'Unrolling the Codex agent loop', Performance considerations |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20cost_controls&system=codex-cli&dimension=F2%20cost_controls&current=caching) |
| F3 | `timeouts` | `per_tool` | medium | “"timeout\_ms": {"description": "The timeout for the command...", ...},” | blog 'Unrolling the Codex agent loop', Building the initial prompt |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20timeouts&system=codex-cli&dimension=F3%20timeouts&current=per_tool) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `unresolved` |  |  |  | unresolved after the repair pass (quote\_not\_in\_bundle). Commands are wrapped by OS sandboxes: Seatbelt, bubblewrap/landlock, Windows sandbox (see doctor/sandbox.rs). Codex cloud is remote. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20execution_isolation&system=codex-cli&dimension=G1%20execution_isolation&current=unresolved) |
| G2 | `filesystem_access` | `scoped` | medium | “list of folders writable by Codex, if any” | blog 'Unrolling the Codex agent loop', Building the initial prompt | Modes are read-only, workspace-write and full-access. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20filesystem_access&system=codex-cli&dimension=G2%20filesystem_access&current=scoped) |
| G3 | `network_policy` | `none` | low | “"network sandbox: {}",” | [codex-rs/cli/src/doctor/sandbox.rs@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/codex-rs/cli/src/doctor/sandbox.rs) | A network sandbox policy exists. Default is believed to be network disabled in the sandbox; the paper mentions host/port rules. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20network_policy&system=codex-cli&dimension=G3%20network_policy&current=none) |
| G4 | `permission_model` | `policy_engine` | low | “The execution policy engine evaluates tool invocations against a declarative rule set before sandbox enforcement.” | [arXiv:2604.11518 Sec. III.D](https://arxiv.org/abs/2604.11518) | docs/execpolicy.md confirms an exec policy exists. Approval prompts are also used. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20permission_model&system=codex-cli&dimension=G4%20permission_model&current=policy_engine) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `logs` | medium | “Codex is written in Rust, so it honors the \`RUST\_LOG\` environment variable to configure its logging behavior.” | [docs/install.md@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/docs/install.md) | Session rollouts are likely structured but not evidenced in the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20tracing&system=codex-cli&dimension=H1%20tracing&current=logs) |
| H2 | `replayability` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20replayability&system=codex-cli&dimension=H2%20replayability&current=not_reported) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | The file tree is truncated. bazel/rules/e2e\_benchmark.bzl exists but its content is not shown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20eval_hooks&system=codex-cli&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `action_policies` | medium | “Admins can set top-level \`allow\_managed\_hooks\_only = true\`” | [docs/config.md@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/docs/config.md) | Execpolicy and approvals block actions; lifecycle hooks also exist. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20guardrails&system=codex-cli&dimension=H4%20guardrails&current=action_policies) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `swe` | medium | “\<strong\>Codex CLI\</strong\> is a coding agent from OpenAI that runs locally on your computer.” | [README.md:1@73919571da60](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/README.md#L1) | Coded from the README purpose statement. The line number is inferred from the start of the README excerpt. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20target_domain&system=codex-cli&dimension=M1%20target_domain&current=swe) |
| M2 | `open_source` | `yes` | high | “This repository is licensed under the \[Apache-2.0 License\](LICENSE).” | [README.md@73919571](https://github.com/openai/codex/blob/73919571da608749b867134722fe3b42c1c6097f/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20open_source&system=codex-cli&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | medium | “so it can be used with any endpoint that implements the Responses API” | blog 'Unrolling the Codex agent loop', Model inference | Works with any Responses API endpoint, including ollama and LM Studio. There is no litellm abstraction. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20model_agnostic&system=codex-cli&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “ref: tag:rust-v0.153.0-alpha.2 73919571da608749b867134722fe3b42c1c6097f 2026-08-31” | github\_repo metadata |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20primary_artifact&system=codex-cli&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `not_reported` |  |  |  | The first tag is not in the evidence. The blog says the CLI launched in April (2025) but gives no exact date. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20first_release_date&system=codex-cli&dimension=M5%20first_release_date&current=not_reported) |
| M6 | `pinned_version` | `rust-v0.153.0-alpha.2 @ 73919571da608749b867134722fe3b42c1c6097f (2026-08-31)` | high | “ref: tag:rust-v0.153.0-alpha.2 73919571da608749b867134722fe3b42c1c6097f 2026-08-31” | github\_repo metadata | The pinned tag is an alpha pre-release. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20pinned_version&system=codex-cli&dimension=M6%20pinned_version&current=rust-v0.153.0-alpha.2%20%40%2073919571da608749b867134722fe3b42c1c6097f%20%282026-08-31%29) |
| M7 | `stars` | `125294` | medium | “stars: 125294” | repository evidence header | Date of the star count is not stated. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20stars&system=codex-cli&dimension=M7%20stars&current=125294) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. H2 `replayability` (Replayability): 90.6% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20replayability&system=codex-cli&dimension=H2%20replayability&current=not_reported)
2. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20rollback&system=codex-cli&dimension=E3%20rollback&current=not_reported)
3. A3 `context_compaction` (Context compaction): 77.9% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20context_compaction&system=codex-cli&dimension=A3%20context_compaction&current=not_reported)
4. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20tool_count&system=codex-cli&dimension=B2%20tool_count&current=not_reported)
5. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20eval_hooks&system=codex-cli&dimension=H3%20eval_hooks&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20%3Cdimension%3E&system=codex-cli> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=codex-cli>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
