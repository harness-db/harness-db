# Coding manual (v0.2)

Status: draft for the pilot. Becomes v1 after the 30-system pilot and per-dimension
kappa >= 0.6. Schema: `schema/dimensions.json` 0.1.0 (38 dimensions, 9 layers).

Two worked examples are coded end to end in `data/examples/` (LLM pre-fill, not yet
human-verified):

| system | pinned version | evidence prefix |
|---|---|---|
| SWE-agent 1.x | `v1.1.0` @ `0f3acafacabc0def8cc76b4e48acb4b6cf302cb9` (2025-05-22) | `path:line@0f3acaf` (repo-root relative) |
| OpenHands | `v1.16.0` @ `64c1269655012698bc66538967989996191beb6c` (2026-08-27), which pins `software-agent-sdk v1.44.0` @ `322dec7d777497e376f81e093ed1eb0196bbbb39` (2026-08-27) | `OpenHands/path:line@64c126965`, `software-agent-sdk/path:line@322dec7d` |

Every dimension section below ends with those two cells. Full cells (with `note`)
are in the JSON files; the manual shows value + primary evidence only.

## General rules

1. **Pin first.** Code the system at its pinned version (`M6`). If the paper and the
   repo disagree, code the repo at the pinned commit and put the paper's claim in
   `note`. If the harness spans several repos (OpenHands), pin each and prefix
   evidence paths with the repo name.
2. **Evidence is verbatim.** Either `path/to/file.py:LINE@<short-hash>` pointing at a
   line you opened, or a verbatim paper quote with its section number. No
   paraphrase. If you cannot point at it, set `not_reported: true`, `value: null` —
   except where the value you are recording *is* an absence, which rule 5 governs.
3. **Confidence.** `high` = explicit statement or code on the cited line; `medium` =
   inferred from adjacent code, a default value, or a figure; `low` = inferred from
   prose describing behaviour.
4. **Default first, capability second.** Code the shipped *default configuration* of
   the pinned artifact (the config file or factory the README/CLI selects). For
   multi-valued dimensions, additionally include every value reachable through shipped
   configuration options without code changes, and say in `note` which value is the
   default. For single-valued dimensions, code the default and list config-reachable
   alternatives in `note`. Never include `none` alongside other values.
5. **Absence is not silence.** "I looked and found nothing" splits into two different
   codings, and the split decides the under-reporting result (RQ4), so decide it in
   this order and never by feel:

   a. Does the evidence contain **the place where this feature would be declared if it
      existed** — the config schema or settings model, the CLI flags, the tool or
      plugin registry, the run loop itself, or a feature list in the documentation?

   b. **YES, and the feature is not there** → code the absence value (`none`, `open`,
      `unbounded`, ...). Evidence is that place: cite the config model, registry or
      loop you opened, plus where useful the search you ran
      (`grep -rli mcp sweagent/ -> 0 hits`). Confidence at most `medium` unless the
      documentation states the absence outright.

   c. **NO — the evidence has no such place** (no config surface in the bundle, the
      repository was truncated, or only a paper was available) → `not_reported: true`,
      `value: null`, and say in `note` which place was missing.

   Never turn the absence of a *mention* into an absence value: prose that does not
   discuss rollback is not evidence that rollback is absent. Equally, never record
   `not_reported` once you have opened the place where the feature would be declared —
   at that point you have read the sources and they have answered.

   Why this rule is written so tightly: on the first double-coded sample (217 systems,
   2026-09-23) the two readings agreed on the evidence and disagreed only on this
   split, which alone pushed 19 of 38 dimensions below the reliability threshold —
   `rollback` 0.97 of its disagreements, `replayability` 0.96, `network_policy` 0.94,
   with notes on both sides reading "no replay facility found".
6. **Closest value + note.** When a value list does not fit, pick the closest value,
   write the mismatch in `note`, and add the case to "Ambiguities" below. Value lists
   change only through `schema/dimensions.json` plus a changelog line.
7. **Line numbers are real.** Open the file at the pinned commit and cite the line you
   read; ranges (`:123-130`) are fine. Do not cite from memory or from `main`.
8. **Paper quotes** carry the arXiv id and section (`paper Sec. 3`, `App. A.2`). Use
   the HTML version where available; fall back to the PDF.
9. **Coder id** is `llm-prefill` for machine pre-fill, `c1`/`c2`/... for humans. A
   human verifying a pre-filled cell overwrites `coder`.

## Dimensions

### Layer A: Context assembly

#### A1 system_prompt_style (single)
Definition: how the system prompt that opens every model call is produced.

Values:
- `static`: one fixed string, identical for every task and step.
- `templated`: a template with task/environment variables rendered once per run.
- `dynamically_composed`: assembled at runtime from multiple sources (sections,
  tools present, repo files, skills), possibly changing between steps.
- `model_generated`: a model writes or rewrites the prompt.

Decision rule: find where the system message is built (search `system_template`,
`system_prompt`, `render`). Variables in a template -> `templated`. Conditional
sections, runtime-loaded files, or per-step recomposition -> `dynamically_composed`.
Paper-only: "we prompt the model with" without mechanism -> `static`, `low`.

Evidence: the line that renders/assembles the prompt, plus the default prompt file.

- SWE-agent: `templated` — `sweagent/agent/agents.py:570@0f3acaf` (Jinja `Template(...).render(**format_dict)`), `config/default.yaml:6-7@0f3acaf`.
- OpenHands: `dynamically_composed` — `software-agent-sdk/openhands-sdk/openhands/sdk/agent/base.py:356-364,372-380,517-522@322dec7d` (static tier from a section registry + dynamic tier from `agent_context`).

#### A2 env_context_strategy (single)
Definition: how the harness gives the model knowledge of the repository/environment.

Values:
- `none`: nothing beyond the task text.
- `file_tree_summary`: a directory listing or outline is injected up front.
- `retrieval_bm25`: lexical retrieval selects snippets for the prompt.
- `embedding_rag`: vector retrieval selects snippets.
- `agent_driven_navigation`: the model explores with tools (view, grep, find).
- `mixed`: two or more of the above are on by default.

Decision rule: look at the instance/task template and the default tool list. If the
prompt contains only the task and a working directory and the tools include
view/search, code `agent_driven_navigation`. Code `mixed` only when the default
config both injects context and lets the model navigate. Opt-in helpers go in `note`.

Evidence: the instance template lines and the tool definition used for navigation.

- SWE-agent: `agent_driven_navigation` — `config/default.yaml:9-22@0f3acaf` (only `{{working_dir}}`; "find and read code relevant to the <pr_description>"), `tools/edit_anthropic/config.yaml:10@0f3acaf`.
- OpenHands: `agent_driven_navigation` — `software-agent-sdk/openhands-tools/openhands/tools/preset/default.py:55-59@322dec7d`, `.../tools/file_editor/definition.py:151-157@322dec7d`.

#### A3 context_compaction (multi)
Definition: mechanisms that shrink the history sent to the model.

Values:
- `none`: full history always sent.
- `truncate_oldest`: oldest messages dropped when a limit is hit.
- `summarize`: an LLM (or heuristic) summary replaces a span of history.
- `tool_output_pruning`: individual observations are truncated or elided.
- `structured_checkpoint`: history replaced by a structured state object.
- `model_native`: relies on provider-side context management.

Decision rule: search `history_processor`, `condenser`, `truncat`, `max_observation`,
`summar`. Per-observation truncation or "N lines omitted" -> `tool_output_pruning`.
LLM summary events -> `summarize`. Include config-reachable processors (rule 4).

Evidence: the class/function that rewrites history and the default config enabling it.

- SWE-agent: `[tool_output_pruning]` — `sweagent/agent/agents.py:691-694@0f3acaf` (observation cut at `max_observation_length`), `sweagent/agent/history_processors.py:77-78,138@0f3acaf` (`LastNObservations`).
- OpenHands: `[summarize, tool_output_pruning]` — `.../sdk/context/condenser/llm_summarizing_condenser.py:522-526@322dec7d` (`default_condenser` -> `LLMSummarizingCondenser`), `.../tools/terminal/definition.py:192-195@322dec7d` (`maybe_truncate`).

#### A4 observation_format (multi)
Definition: the modality/format of tool results as presented to the model.

Values:
- `raw_text`: plain text (stdout, file contents).
- `structured_json`: JSON objects the model is expected to parse.
- `screenshots`: images.
- `a11y_tree`: accessibility/DOM tree text.
- `set_of_marks`: screenshots annotated with element ids.

Decision rule: find where observations are converted to message content (`TextContent`,
`ImageContent`, `to_llm_content`, observation template). One value per content type
actually produced by default tools; env-dependent tools (browser) count if shipped.

Evidence: the conversion line for each content type.

- SWE-agent: `[raw_text]` — `sweagent/agent/agents.py:661-666@0f3acaf`, `config/default.yaml:28-30@0f3acaf`.
- OpenHands: `[raw_text, screenshots]` — `.../tools/terminal/definition.py:199@322dec7d` (`TextContent`), `.../tools/browser_use/definition.py:95-116@322dec7d` (`ImageContent`).

### Layer B: Tool interface

#### B1 tool_call_format (multi)
Definition: the syntax by which the model requests a tool/action.

Values:
- `native_function_calling`: provider tool-call API (OpenAI/Anthropic tools).
- `json_in_text`: JSON object embedded in the assistant text.
- `xml_tags`: tag-delimited calls parsed from text (`<function=...>`).
- `code_as_action`: the model writes a code block that is executed as the action.
- `shell_only`: the action is a shell command line.
- `cli_flags`: actions are CLI invocations with flags.

Decision rule: find the parser(s) that turn model output into an action (`parse`,
`tool_calls`, `fn_call_converter`). Default parser first; add every shipped parser
selectable by config. If every tool call is ultimately rendered to a shell command,
also include `shell_only` and say so in `note`.

Evidence: the default config line selecting the parser and the parser class line(s).

- SWE-agent: `[native_function_calling, json_in_text, xml_tags, shell_only]` — `config/default.yaml:58-59@0f3acaf`, `sweagent/tools/parsing.py:367-368,444-445,168,225,109-117@0f3acaf`.
- OpenHands: `[native_function_calling, xml_tags]` — `.../sdk/llm/llm.py:517-520@322dec7d` (`native_tool_calling=True`), `.../sdk/llm/mixins/fn_call_converter.py:1-6,49,85@322dec7d` (`<function=...>` fallback).

#### B2 tool_count (integer)
Definition: number of distinct tool definitions exposed to the model in the default
configuration at the pinned version.

Decision rule: count entries in the tool list/schema array sent with the model call:
each function schema = 1; a built-in shell/bash tool = 1 regardless of what it can
run; a "toolset" counts as its expanded tools; built-in tools attached to every agent
(finish, think) count; MCP or environment-injected tools do not count. Record the
count under the maximal shipped configuration in `note`.

Evidence: the default config listing bundles/tools plus each tool definition file.

- SWE-agent: `3` — `config/default.yaml:33-37,57@0f3acaf` (bash + `str_replace_editor` + `submit`), `sweagent/tools/tools.py:157-159@0f3acaf`; 17 definitions shipped across bundles.
- OpenHands: `5` — `.../sdk/tool/defaults.py:17-21@322dec7d` (terminal, file_editor, task_tracker), `.../sdk/tool/builtins/__init__.py:44@322dec7d` (`FinishTool, ThinkTool`); 19 with the 14-tool browser toolset injected when Chromium exists.

#### B3 edit_primitive (multi)
Definition: how the model expresses a file modification.

Values:
- `none`: no file-editing tool (edits only via shell).
- `whole_file_rewrite`: the model emits the complete file content (incl. new files).
- `search_replace`: old/new text pair located and swapped by the harness.
- `unified_diff`: patch syntax applied with patch semantics.
- `line_range_edit`: lines addressed by number (`edit 10:20`, `insert after line N`).
- `ast_aware`: the harness parses the file and applies a structural edit.

Decision rule: open the edit tool's command list. `str_replace` -> `search_replace`;
`create`/`write_file` with full text -> `whole_file_rewrite`; `insert_line`/`edit
start:end` -> `line_range_edit`; `apply_patch`/diff input -> `unified_diff`. Include
shipped opt-in edit tools (rule 4).

Evidence: the tool definition lines listing the commands/arguments.

- SWE-agent: `[search_replace, whole_file_rewrite, line_range_edit]` — `tools/edit_anthropic/config.yaml:22-24@0f3acaf`, `tools/windowed_edit_linting/config.yaml:3-6@0f3acaf`.
- OpenHands: `[search_replace, whole_file_rewrite, line_range_edit, unified_diff]` — `.../tools/file_editor/definition.py:151-157@322dec7d`, `.../tools/apply_patch/definition.py:124-125@322dec7d`.

#### B4 tool_schema_source (multi)
Definition: where the tool schema shown to the model comes from.

Values:
- `hand_written`: humans author the schema text (YAML/JSON/docstring), even if a
  converter reformats it.
- `auto_generated`: derived from code types or signatures (Pydantic, type hints).
- `mcp`: schemas fetched from MCP servers.
- `openapi`: schemas derived from OpenAPI specs.

Decision rule: find the function that produces the function-calling schema. If its
input is a declarative spec written by hand -> `hand_written`; if it calls
`model_json_schema()`/inspects signatures -> `auto_generated`. Add `mcp`/`openapi` if
such clients exist in the pinned repo.

Evidence: the schema-producing function and one tool definition.

- SWE-agent: `[hand_written]` — `tools/edit_anthropic/config.yaml:2-55@0f3acaf`, `sweagent/tools/commands.py:131-160@0f3acaf`.
- OpenHands: `[auto_generated, mcp]` — `.../sdk/tool/schema.py:193-199@322dec7d` (`model_json_schema()`), `.../sdk/mcp/client.py:8,24@322dec7d`.

#### B5 protocol_standardization (multi)
Definition: standard agent/tool protocols the harness speaks.

Values:
- `none`: proprietary tool interface only.
- `mcp`: Model Context Protocol client or server.
- `a2a`: Agent-to-Agent protocol.
- `other`: another published protocol (e.g. ACP); name it in `note`.

Decision rule: grep for `mcp`, `a2a`, `acp`, `fastmcp` in source and dependencies.
Package-lock hash matches do not count.

Evidence: the client import line or dependency line; for `none`, the grep result.

- SWE-agent: `[none]` — `sweagent/tools/tools.py:161-173@0f3acaf` (bundles only); grep matches only `sweagent/frontend/package-lock.json`.
- OpenHands: `[mcp, other]` — `.../sdk/mcp/client.py:8@322dec7d`, `.../sdk/agent/acp_agent.py:1-6@322dec7d` (Agent Client Protocol).

### Layer C: Control loop

#### C1 loop_primitives (multi)
Definition: the control-flow patterns that drive model calls and actions.

Values:
- `react`: think -> act -> observe loop, one or more tool calls per step.
- `plan_execute`: a plan is produced first, then steps executed against it.
- `generate_test_repair`: produce, verify (tests or judge), fix, repeat.
- `multi_attempt`: independent attempts with selection/review.
- `tree_search`: branching over states with backtracking.
- `event_driven`: components react to an event stream/callbacks.
- `fixed_pipeline`: predetermined sequence of stages.

Decision rule: read the run loop (`run`, `step`). One model call followed by executing
its tool calls -> `react`. An event log with subscribers -> add `event_driven`. Add
config-reachable loops (retry agents, critic refinement) per rule 4 and flag the
default.

Evidence: the loop lines (`while not done`), plus the class enabling each extra loop.

- SWE-agent: `[react, multi_attempt]` — `sweagent/agent/agents.py:1001-1010,1240-1242@0f3acaf`; `agents.py:226,397-400@0f3acaf` (`RetryAgent`).
- OpenHands: `[react, event_driven, generate_test_repair]` — `.../sdk/agent/agent.py:637-653,680-689,720@322dec7d`; `.../sdk/conversation/event_store.py:30-49@322dec7d`; `.../sdk/critic/base.py:20-24,39@322dec7d`.

#### C2 planning_granularity (single)
Definition: whether and how a plan is represented.

Values:
- `none`: no planning step or instruction.
- `implicit`: planning only in free-text reasoning or a fixed prompt recipe.
- `explicit_plan_object`: a structured plan (task list, PLAN file) the harness stores.
- `hierarchical`: nested plans/sub-goals with delegation.

Decision rule: `explicit_plan_object` requires a data structure or file written and
re-read across steps (task tracker, plan file). A numbered recipe in the prompt is
`implicit`.

Evidence: the plan object definition, or the prompt recipe lines.

- SWE-agent: `implicit` — `config/default.yaml:21-27@0f3acaf`, `sweagent/agent/agents.py:1176-1188@0f3acaf` (no plan field).
- OpenHands: `explicit_plan_object` — `.../tools/task_tracker/definition.py:42-51@322dec7d`, `.../tools/preset/default.py:58@322dec7d`.

#### C3 multi_agent_topology (single)
Definition: arrangement of agents in the default configuration.

Values:
- `single`: one agent.
- `orchestrator_workers`: one agent spawns/delegates to workers and integrates.
- `peer`: agents exchange messages as equals.
- `hierarchical`: multi-level orchestration.
- `debate`: agents argue and a judge decides.
- `pipeline`: fixed hand-off sequence of specialised agents.

Decision rule: code the default; if delegation is only reachable by a flag, code
`single` and put the reachable topology in `note` (see ambiguity C3/C4). Sequential
retries of the same agent plus a reviewer model are still `single`.

Evidence: the agent factory/config lines and the delegation tool if present.

- SWE-agent: `single` — `sweagent/agent/agents.py:216-223,412@0f3acaf`.
- OpenHands: `single` — `.../tools/preset/default.py:39,64-67@322dec7d` (`enable_sub_agents=False`); `.../tools/delegate/definition.py:13-20@322dec7d` reachable.

#### C4 delegation_mechanism (single)
Definition: how work is handed to another agent, if at all.

Values:
- `none`
- `subagent_spawn`: a new agent/conversation is created for a subtask.
- `role_handoff`: control passes to another agent role in the same conversation.
- `message_bus`: agents communicate over a shared channel.

Decision rule: as C3. `subagent_spawn` when a tool or API instantiates a new
agent/conversation object.

- SWE-agent: `none` — `sweagent/agent/agents.py:216-223@0f3acaf`.
- OpenHands: `none` (default) — `.../tools/preset/default.py:39,64-67@322dec7d`; opt-in `subagent_spawn` at `.../tools/delegate/impl.py:33-48,132@322dec7d`.

#### C5 human_in_loop (multi)
Definition: points at which a human can gate or steer the run.

Values:
- `none`
- `on_permission`: human approves individual actions/tool calls.
- `on_plan`: human approves a plan before execution.
- `on_completion`: human reviews before the result is accepted.
- `configurable`: the gating policy can be switched at runtime/config.

Decision rule: search `confirm`, `approval`, `permission`, `WAITING_FOR`. A
"human model" that replaces the LM is not HITL (code `none`, note it). `configurable`
is added when several policies are selectable.

- SWE-agent: `[none]` — `sweagent/agent/agents.py:1240-1242@0f3acaf`; `sweagent/agent/models.py:324-326@0f3acaf` (human-as-model, noted).
- OpenHands: `[on_permission, configurable]` — `.../sdk/security/confirmation_policy.py:27-61@322dec7d`, `.../sdk/conversation/impl/local_conversation.py:1895-1898@322dec7d`; default `NeverConfirm` at `.../sdk/conversation/state.py:123@322dec7d`.

### Layer D: Memory and state

#### D1 short_term_state (single)
Definition: what the harness keeps as working state within a run.

Values:
- `conversation_only`: the message list is the state.
- `scratchpad`: free-text notes the agent can write/read within the run.
- `structured_task_state`: a typed state object (status, plan, stats) beyond messages.

Decision rule: find the state object passed to `step`. A message list plus template
variables -> `conversation_only`. A typed state class with fields beyond messages, or
a plan/task object the agent maintains -> `structured_task_state`.

- SWE-agent: `conversation_only` — `sweagent/agent/agents.py:509-520,952@0f3acaf`.
- OpenHands: `structured_task_state` — `.../sdk/conversation/state.py:82,102-123,192@322dec7d`.

#### D2 long_term_memory (multi)
Definition: information persisted across runs and re-injected.

Values:
- `none`
- `file_notes`: files (MEMORY.md, notes) written/read across runs.
- `vector_store`: embeddings index.
- `skill_library`: reusable procedures/skills loaded from a library.
- `episodic_db`: database of past episodes/trajectories.

Decision rule: search `memory`, `skills`, `~/.<tool>`, `vector`, `embedding`. Static
few-shot demonstrations chosen in config are not memory.

- SWE-agent: `[none]` — `sweagent/agent/agents.py:530-565@0f3acaf` (setup reads no prior-run data).
- OpenHands: `[file_notes, skill_library]` — `.../sdk/context/memory.py:1-9@322dec7d`, `.../sdk/skills/__init__.py:10@322dec7d`, `.../sdk/skills/installed.py:33,50@322dec7d`.

#### D3 state_persistence (single)
Definition: whether an interrupted run can be continued.

Values:
- `none`: runs start from scratch (trace files may exist but cannot be resumed).
- `checkpoint`: state is saved during the run and can be reloaded at that point.
- `full_resume`: complete conversation/state reload and continuation is a supported path.

Decision rule: look for `resume`, `persistence_dir`, `load`. `checkpoint` and
`full_resume` require a code path that reads the saved state back into a running
agent; per-step trace writing alone is `none`.

- SWE-agent: `none` — `sweagent/agent/agents.py:1240-1242@0f3acaf`, `sweagent/run/run_batch.py:83@0f3acaf` (`redo_existing`, skip not resume).
- OpenHands: `full_resume` — `.../sdk/conversation/state.py:458-471@322dec7d`, `.../sdk/conversation/impl/local_conversation.py:255-256,296-297@322dec7d`.

### Layer E: Verification and repair

#### E1 self_verification (multi)
Definition: checks the harness applies (or prompts for) on the agent's work.

Values:
- `none`
- `self_critique`: the same model is prompted to review its own output.
- `test_execution`: the harness runs tests and feeds results back.
- `linters_typecheck`: linters/type checkers run automatically on edits.
- `llm_judge`: a separate model call scores/judges the output.
- `formal`: formal verification.

Decision rule: harness-enforced only. If the model *may* run tests via shell but the
harness does not run them, do not code `test_execution`. Include config-reachable
mechanisms (rule 4).

- SWE-agent: `[self_critique, linters_typecheck, llm_judge]` — `config/default.yaml:37,40-56@0f3acaf` (submit-time review), `tools/windowed_edit_linting/bin/edit:95-112@0f3acaf`, `sweagent/agent/reviewer.py:375,434-448@0f3acaf`.
- OpenHands: `[llm_judge]` — `.../sdk/critic/base.py:57-60,20-39@322dec7d`; default `critic=None` at `.../sdk/agent/base.py:282@322dec7d`.

#### E2 retry_policy (single)
Definition: task-level retry behaviour after a failed or rejected attempt.

Values:
- `none`: one attempt.
- `fixed_n`: up to N attempts.
- `until_pass`: retry until a verifier passes (no fixed cap, or cap secondary).
- `adaptive`: retries decided by cost/score heuristics.

Decision rule: scope is whole-task attempts. Step-level requery on format errors and
LLM API transport retries are not retry policy (note them). Code the default.

- SWE-agent: `none` — `sweagent/agent/agents.py:1221-1242@0f3acaf`; opt-in `fixed_n` at `sweagent/agent/reviewer.py:180-190,200-209@0f3acaf`.
- OpenHands: `none` — `.../sdk/agent/base.py:282@322dec7d`; opt-in at `.../sdk/agent/critic_mixin.py:79,101-104@322dec7d`.

#### E3 rollback (single)
Definition: mechanism to revert changes made during the run.

Values:
- `none`
- `git_based`: repo reset/checkout/branching.
- `snapshot`: filesystem or container snapshot restore (incl. per-file history stacks).

Decision rule: search `undo`, `revert`, `reset --hard`, `checkout`, `snapshot`. A
model-invocable per-file undo backed by saved copies is coded `snapshot` (see
ambiguity E3). Harness-level resets between attempts go in `note` unless default.

- SWE-agent: `snapshot` — `tools/edit_anthropic/bin/str_replace_editor:632-639@0f3acaf` (`undo_edit`); attempt reset `sweagent/environment/swe_env.py:155-161@0f3acaf` noted.
- OpenHands: `snapshot` — `.../tools/file_editor/definition.py:165@322dec7d` (`undo_edit`).

### Layer F: Budget and termination

#### F1 termination_condition (multi)
Definition: conditions that end a run.

Values:
- `model_declared`: a finish/submit tool or stop signal from the model.
- `max_steps`: cap on iterations or model calls.
- `max_tokens`: token/context limit ends the run.
- `cost_cap`: monetary budget.
- `test_pass`: run ends when tests pass.
- `stall_detection`: loop/repetition detector stops the run.

Decision rule: read the run loop and exception handlers. Count a condition only if it
sets done/stops the loop (not just logs). Off-by-default caps still count if a config
field exists (rule 4); say so in `note`.

- SWE-agent: `[model_declared, cost_cap, max_steps, max_tokens]` — `tools/review_on_submit_m/bin/submit:44-46@0f3acaf` + `sweagent/agent/agents.py:842-862@0f3acaf`; `sweagent/agent/models.py:632-637,639-642,667-669@0f3acaf`.
- OpenHands: `[model_declared, max_steps, cost_cap, stall_detection]` — `.../sdk/agent/agent.py:202-227@322dec7d`; `.../sdk/conversation/impl/local_conversation.py:217,2009-2027,683-696,2001-2007,725-727@322dec7d`.

#### F2 cost_controls (multi)
Definition: mechanisms that limit or reduce spend.

Values:
- `none`
- `token_budget`: a cap on tokens or cost per run/instance.
- `model_routing`: choosing among models by task/cost.
- `caching`: prompt/response caching.

Decision rule: search `cost_limit`, `budget`, `cache_control`, `caching`, `router`,
`fallback`. Provider failover lists are not routing unless selection is content- or
cost-based.

- SWE-agent: `[token_budget, caching]` — `sweagent/agent/models.py:73-78@0f3acaf`, `config/default.yaml:60-62@0f3acaf` + `sweagent/agent/history_processors.py:225-233@0f3acaf`.
- OpenHands: `[token_budget, caching, model_routing]` — `.../sdk/conversation/impl/local_conversation.py:235,466-467@322dec7d`, `.../sdk/llm/llm.py:496-498@322dec7d`, `.../sdk/llm/router/impl/multimodal.py:13,30@322dec7d`.

#### F3 timeouts (multi)
Definition: time limits enforced by the harness.

Values:
- `none`
- `per_tool`: per command/tool call.
- `per_run`: per task/run (wall-clock or cumulative execution time).

Decision rule: search `timeout`. Iteration caps are not timeouts.

- SWE-agent: `[per_tool, per_run]` — `sweagent/tools/tools.py:123-132@0f3acaf` (30 s per command, 1800 s cumulative).
- OpenHands: `[per_tool]` — `.../tools/terminal/definition.py:106-109@322dec7d`; no run-level timeout found in `local_conversation.py`.

### Layer G: Sandbox and environment

#### G1 execution_isolation (single)
Definition: the boundary within which agent actions execute, in the default configuration.

Values:
- `none`: in-process on the host.
- `subprocess`: host subprocess/shell, no isolation.
- `container`: Docker/OCI container.
- `vm`: virtual machine / microVM.
- `remote`: a remote execution service.

Decision rule: find the default workspace/deployment object. Multiple backends are
common; code the default and list the others in `note` (see ambiguity G1).

- SWE-agent: `container` — `sweagent/environment/swe_env.py:27-30@0f3acaf` (`DockerDeploymentConfig` default); paper App. A.2.
- OpenHands: `subprocess` — `.../sdk/conversation/conversation.py:126@322dec7d` (`LocalWorkspace` default), `.../sdk/utils/command.py:82@322dec7d` (`subprocess.Popen`), `OpenHands/README.md:64-66@64c126965`; container/remote workspaces noted.

#### G2 filesystem_access (single)
Definition: what the agent may read/write within the G1 boundary.

Values:
- `full`: unrestricted within the boundary.
- `scoped`: limited to a workspace/allowed paths.
- `read_only`
- `virtual`: an in-memory or overlay filesystem.

Decision rule: code relative to the execution boundary from G1 and say so in `note`.
Look for path allowlists, read-only mounts, or overlay FS.

- SWE-agent: `full` — `sweagent/environment/swe_env.py:187-188@0f3acaf`, `sweagent/tools/tools.py:243-244@0f3acaf` (root inside container).
- OpenHands: `full` — `OpenHands/README.md:66@64c126965` ("full access to your filesystem").

#### G3 network_policy (single)
Definition: network egress available to agent actions.

Values:
- `open`: no restriction.
- `allowlist`: only listed hosts.
- `none`: network disabled.

Decision rule: search `network`, `--network`, `egress`, `proxy`. No network
configuration at all -> `open` with `medium` confidence and the grep in evidence.

- SWE-agent: `open` — `sweagent/environment/swe_env.py:27-30,155-161@0f3acaf` (no network option; `git fetch` inside container).
- OpenHands: `open` — `software-agent-sdk/openhands-workspace/openhands/workspace/docker/workspace.py:119-122@322dec7d` (network selector only).

#### G4 permission_model (single)
Definition: how individual actions are authorised.

Values:
- `none`: everything the model emits is executed.
- `static_allowlist`: a fixed list decides (currently also used for blocklists).
- `per_call_prompt`: a human approves each call.
- `policy_engine`: risk analysis or rules decide dynamically.

Decision rule: code the default. A command blocklist is coded `static_allowlist` with
a note (ambiguity G4). Confirmation policies that default to off -> `none` + note.

- SWE-agent: `static_allowlist` — `sweagent/tools/tools.py:28-71,334-348@0f3acaf` (blocklist).
- OpenHands: `none` — `.../sdk/conversation/state.py:123@322dec7d` (`NeverConfirm` default); opt-in policy engine at `.../sdk/security/analyzer.py:15-27@322dec7d`, `confirmation_policy.py:43-61@322dec7d`.

### Layer H: Observability and governance

#### H1 tracing (single)
Definition: the richest form of run record the harness can emit.

Values:
- `none`
- `logs`: unstructured log lines.
- `structured_traces`: per-step structured records (JSON trajectory/event log).
- `opentelemetry`: OTLP/OpenTelemetry export.

Decision rule: code the highest level available in the pinned repo, even if enabled
by env vars; state what is on by default in `note`.

- SWE-agent: `structured_traces` — `sweagent/agent/agents.py:1176-1189,738-746@0f3acaf` (.traj with per-step query), `sweagent/utils/log.py:93-113@0f3acaf`.
- OpenHands: `opentelemetry` — `.../sdk/observability/laminar.py:64-69,95@322dec7d` (OTLP endpoint, Laminar), `.../sdk/conversation/event_store.py:30-49@322dec7d` (event log always on).

#### H2 replayability (single)
Definition: ability to re-run a recorded trajectory.

Values:
- `none`
- `partial`: actions or model outputs can be replayed, environment may differ.
- `deterministic`: bit-for-bit reproduction supported.

Decision rule: search `replay`, `resume`, `ReplayModel`. Claim `deterministic` only
with an explicit statement.

- SWE-agent: `partial` — `sweagent/run/run_replay.py:1-8@0f3acaf`, `sweagent/agent/models.py:186@0f3acaf`.
- OpenHands: `partial` — `.../sdk/conversation/state.py:458-461@322dec7d`, `.../sdk/event/resume_transcript.py:1-8@322dec7d`.

#### H3 eval_hooks (single)
Definition: benchmark evaluation wired into the harness's own repo(s).

Values:
- `none`
- `built_in`: an evaluation runner/hook ships in the pinned repo(s).

Decision rule: search `evaluate`, `swebench`, `benchmark` in the pinned repo. A
sibling evaluation repo is `none` + note (ambiguity H3).

- SWE-agent: `built_in` — `sweagent/run/hooks/swe_bench_evaluate.py:19,42@0f3acaf`, `sweagent/run/run_batch.py:223-226@0f3acaf`.
- OpenHands: `none` — grep of `openhands-sdk/openhands/sdk` at 322dec7d matches only the condenser file; paper Sec. 4 framework noted.

#### H4 guardrails (multi)
Definition: safety controls on inputs, outputs, and actions.

Values:
- `none`
- `input_filters`: user/task input can be blocked or rewritten.
- `output_filters`: model/tool output is masked or filtered.
- `action_policies`: actions are blocked/validated before execution.

Decision rule: blocklists, syntax checks that prevent execution, lint-revert, risk
analyzers and pre-tool hooks -> `action_policies`. Secret masking -> `output_filters`.
Prompt-submit hooks that can block -> `input_filters`.

- SWE-agent: `[action_policies]` — `sweagent/tools/tools.py:36-65@0f3acaf`, `sweagent/agent/agents.py:1091-1097@0f3acaf`, `tools/windowed_edit_linting/bin/edit:109-119@0f3acaf`.
- OpenHands: `[input_filters, output_filters, action_policies]` — `.../sdk/agent/agent.py:655-662@322dec7d`, `.../sdk/conversation/secret_registry.py:143@322dec7d`, `.../sdk/security/analyzer.py:15-27@322dec7d`, `.../sdk/hooks/types.py:12-13@322dec7d`.

### Layer M: Meta

#### M1 target_domain (multi)
Definition: task domains the harness is built for.

Values: `swe` (code repositories), `gui_computer_use`, `web` (browser tasks),
`general_tool_use` (arbitrary tools/MCP), `research`, `other`.

Decision rule: README/paper statement of purpose plus shipped tool families
(browser -> `web`; generic MCP -> `general_tool_use`).

- SWE-agent: `[swe]` — `README.md:14-15@0f3acaf`; paper title.
- OpenHands: `[swe, web, general_tool_use]` — `software-agent-sdk/README.md:30@322dec7d`, `.../tools/browser_use/definition.py:776@322dec7d`, `.../sdk/mcp/definition.py:26@322dec7d`.

#### M2 open_source (single)
Values: `yes` (OSI licence, full source), `no`, `partial` (some components closed).
Decision rule: cite `LICENSE:1`.

- SWE-agent: `yes` — `LICENSE:1@0f3acaf` (MIT).
- OpenHands: `yes` — `software-agent-sdk/LICENSE:1@322dec7d`, `OpenHands/LICENSE:1@64c126965` (MIT).

#### M3 model_agnostic (single)
Values: `yes` (any provider via an abstraction such as litellm), `no` (single vendor).
Decision rule: find the LLM client abstraction and its dependency line.

- SWE-agent: `yes` — `sweagent/agent/models.py:66-69@0f3acaf` (litellm).
- OpenHands: `yes` — `.../sdk/llm/llm.py:62,2225@322dec7d`, `software-agent-sdk/openhands-sdk/pyproject.toml:16@322dec7d`.

#### M4 primary_artifact (single)
Definition: the artifact from which the pinned version is coded.

Values: `paper` (no code, or code frozen to the paper), `repo`, `tech_report`.
Decision rule: if a repo exists and its pinned version postdates or diverges from the
paper, `repo`; record the paper-version gap in `note`.

- SWE-agent: `repo` — `README.md:10@0f3acaf`, `sweagent/__init__.py:15@0f3acaf` (1.x postdates the paper).
- OpenHands: `repo` — `OpenHands/AGENTS.md:31@64c126965`, `software-agent-sdk/README.md:14@322dec7d`.

#### M5 first_release_date (date)
Definition: first tagged release of the coded line (major version if the id is
versioned). Fallback order: first tag -> first commit -> paper v1 date. State the
basis in `note`.

- SWE-agent 1.x: `2025-02-13` — tag `v1.0.0` -> `8ed382c1`; project first tag `v0.1.0` 2024-04-05 noted.
- OpenHands: `2024-04-16` — tag `0.3.0` -> `4b4bc15f`; repo created 2024-03-13 noted.

#### M6 pinned_version (string)
Definition: tag + full commit hash (+ date) for every repo coded. Rule: latest tagged
release before the cut-off date; if the flagship repo no longer contains the harness,
follow its dependency pin and record both.

- SWE-agent: `v1.1.0 @ 0f3acafacabc0def8cc76b4e48acb4b6cf302cb9 (2025-05-22)`.
- OpenHands: `OpenHands v1.16.0 @ 64c1269655012698bc66538967989996191beb6c (2026-08-27) + software-agent-sdk v1.44.0 @ 322dec7d777497e376f81e093ed1eb0196bbbb39 (2026-08-27)` — `OpenHands/config/defaults.json:4@64c126965`.

#### M7 stars (integer)
Definition: GitHub stars of the flagship repo, date-stamped in evidence. Rule: use
`gh api repos/<owner>/<repo> --jq .stargazers_count` and write the date; for
multi-repo systems use the repo in `urls.repo` and note the others.

- SWE-agent: `20340` — `gh api repos/SWE-agent/SWE-agent` on 2026-09-16.
- OpenHands: `88161` — `gh api repos/All-Hands-AI/OpenHands` on 2026-09-16 (SDK repo 1123).

## Ambiguities found while coding

Each item names the dimension, the concrete case, and a proposal for
`schema/dimensions.json` (to be decided in the pilot and recorded in the changelog).

1. **General: default vs capability (C3, C4, C5, E1, E2, G1, G4, D3, B2).** OpenHands
   ships delegation, confirmation, Docker isolation and critic loops, all off by
   default; rule 4 codes `single`/`none`/`subprocess`/`none`. Proposal: add an
   optional per-cell field `scope: "default" | "configurable"` and allow single-valued
   capability dimensions (C3, C4, G1, G4) to carry a second value
   `configurable_value`; alternatively make C3, C4 and G4 multi-valued with the
   default listed first.
2. **B2 tool_count: counting convention.** Toolsets (browser toolset = 14 tools),
   environment-injected tools, built-ins attached to every agent, MCP tools, and one
   `bash` tool that exposes everything. Proposal: write the counting rule above into
   the dimension description and add `tool_count_max` (integer) for the maximal
   shipped configuration.
3. **B3 edit_primitive: `create` and custom patch formats.** `create` emits full
   content for a *new* file (coded `whole_file_rewrite`); OpenHands `apply_patch`
   uses the OpenAI `*** Begin Patch` format, not unified diff (coded
   `unified_diff`). Proposal: gloss `whole_file_rewrite` to include new-file creation;
   rename `unified_diff` to `patch_format` or add `custom_patch`.
4. **B4 tool_schema_source: hand-written declarative specs.** SWE-agent's YAML tool
   specs are hand-written but mechanically converted to JSON schema. Proposal: gloss
   `hand_written` = schema text authored by humans in any format; `auto_generated` =
   derived from code types/signatures.
5. **B1 tool_call_format: fenced command blocks.** SWE-agent's `thought_action` parser
   reads a command in triple backticks; coded `shell_only`. OpenHands' non-native
   fallback `<function=...>` is coded `xml_tags`. Proposal: add `fenced_block` or
   gloss `shell_only` as "command line in text or fenced block".
6. **C1 loop_primitives: judge-driven refinement.** OpenHands' critic loop verifies
   with an LLM critic, not tests; coded `generate_test_repair`. Proposal: rename to
   `generate_verify_repair` and gloss verifier types.
7. **C5 human_in_loop: human-as-model.** SWE-agent's `HumanModel` replaces the LM.
   Proposal: state in the gloss that human-as-model is `none`; define
   `configurable` = gating policy selectable at runtime.
8. **D3 state_persistence: unresumable checkpoints.** SWE-agent writes `.traj` after
   every step but cannot resume; coded `none`. Proposal: gloss `checkpoint` as
   "saved and re-loadable"; add `trace_only` if the pilot finds many such systems.
9. **E2 retry_policy: scope.** Step-level requery (format errors), LLM API retries,
   and task-level attempts are different things. Proposal: gloss E2 as task-level;
   consider a new dimension `step_requery` (integer) under layer E.
10. **E3 rollback: tool-level undo.** Both systems offer per-file `undo_edit`; coded
    `snapshot`. Harness-level git reset between attempts exists in SWE-agent.
    Proposal: add `tool_undo`; define `snapshot` = filesystem/container snapshot;
    `git_based` = repo reset/branching; allow multi-valued.
11. **F1 termination_condition: meaning of `max_tokens` and `max_steps`.** SWE-agent
    caps API calls (not steps) and exits on context-window overflow (not a token
    budget); exits on repeated timeouts/format errors have no value. Proposal: gloss
    `max_steps` = iterations or model calls; gloss `max_tokens` = cumulative token
    budget or context overflow (state which in note); add `error_exit`.
12. **F2 cost_controls: `token_budget` denominated in USD.** Both systems cap dollars.
    Proposal: rename to `spend_budget` (tokens or currency).
13. **G1 execution_isolation: multiple backends, paper vs code.** OpenHands defaults
    to local execution at the pinned version while the paper describes Docker.
    Proposal: make G1 multi-valued with the default first, or add
    `isolation_max`; require `note` to list backends.
14. **G2 filesystem_access: reference frame.** "full" inside a container differs from
    "full" on the host. Proposal: gloss G2 as relative to the G1 boundary and add a
    `host_mounted: yes/no` sub-flag.
15. **G3 network_policy: evidence of absence.** Neither system configures network;
    coded `open`, `medium`. Proposal: allow `open` with grep evidence and `medium`
    confidence; add `unspecified`? (prefer not: keep `open`).
16. **G4 permission_model: blocklists.** SWE-agent uses a static blocklist; coded
    `static_allowlist`. Proposal: rename to `static_list` or add `static_blocklist`.
17. **H1 tracing: optional OTel vs always-on structured log.** Proposal: make H1
    multi-valued, or keep single and adopt the "highest available" rule as written.
18. **H3 eval_hooks: sibling repos.** OpenHands' benchmarks live outside the pinned
    repos. Proposal: add `external_repo` value, or gloss `built_in` as "in the pinned
    repo(s)" (adopted here).
19. **M4 primary_artifact: paper describes an older version.** Both papers describe
    2024 architectures. Proposal: keep `repo` and add optional
    `paper_version_gap: yes/no`.
20. **M5 first_release_date: which start.** Versioned ids (swe-agent-1x) vs project
    start; repo creation vs first tag vs paper v1. Proposal: fix the rule as written
    (first tag of the coded line; fallbacks) and record `basis` in note.
21. **M6 pinned_version: multi-repo systems.** OpenHands' flagship repo is now a
    frontend; the harness is in `software-agent-sdk`. Proposal: allow `M6` to be a
    list of `{repo, tag, commit, date}` objects; add `urls.repo_secondary`.
22. **M7 stars: multi-repo systems.** Proposal: flagship repo rule as written; note
    others.
23. **A2 env_context_strategy: repo instruction files.** `.openhands/` skills,
    `MEMORY.md`, `AGENTS.md`-style files inject repo context but are not retrieval.
    Proposal: add `repo_instruction_files` to A2 (or to D2) and gloss.
24. **A4 observation_format: textual DOM/element lists.** browser-use style
    "interactive elements" text is neither `a11y_tree` nor `set_of_marks`. Proposal:
    gloss `a11y_tree` as "accessibility or DOM tree rendered as text".
25. **B5 protocol_standardization: ACP.** Coded `other`. Proposal: add `acp`.
26. **Evidence for `none`.** Adopted rule 5 (cite the registration point plus grep);
    proposal: add this to the schema description of `evidence`.
