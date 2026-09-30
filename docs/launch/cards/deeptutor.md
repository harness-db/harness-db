# DeepTutor: HARNESS-DB cell card

| | |
|---|---|
| System id | `deeptutor` |
| Pinned version | [v1.6.2 @ `3dc372f55128`](https://github.com/hkuds/deeptutor/commit/3dc372f551285ea8ffd552ba01cd5dd16c59cb25) (2026-08-31) |
| Repository | <https://github.com/hkuds/deeptutor> |
| Papers | [arXiv:2604.26962](https://arxiv.org/abs/2604.26962) |
| Stars (sampling-frame snapshot) | 39,997 |
| Stratum / sampling weight | H / 1 |
| Cells | 38: 24 coded, 14 `not_reported`, 0 `unresolved` |
| Coded on | 2026-09-23 |
| Explorer | <https://harness-db.github.io/harness-db/#system=deeptutor> |

Every cell is in one of three states. A **value** carries the verbatim quote it rests on and a locator you can re-open. `not_reported` means the sources the coder was given were read and are silent: undocumented, not absent, and it is the most useful kind of cell to settle. `unresolved` failed validation at release and claims nothing. A locator marked † names a file but no commit; its link opens that file at the pinned commit. Each row's *fix* link opens a prefilled wrong-cell issue.

## A. Context assembly

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| A1 | `system_prompt_style` | `dynamically_composed` | low | “Before each agent step, the system assembles a personalization contextCmem through two channels” | paper Sec. 2.1.2 | Paper describes per-step assembly of RAG and memory context; the code that builds the system prompt was not in the evidence bundle (BaseAgent loads prompts via PromptManager). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20system_prompt_style&system=deeptutor&dimension=A1%20system_prompt_style&current=dynamically_composed) |
| A2 | `env_context_strategy` | `mixed` | low | “The two candidate sets are fused via reciprocal rank fusion (Cormack et al., 2009), deduplicated, and truncated to a context budget, yielding the domain groundingCrag.” | paper Sec. 2.1.1 | Embedding plus graph RAG over the knowledge base, combined with tool-driven investigation. Evidence is from the paper only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20env_context_strategy&system=deeptutor&dimension=A2%20env_context_strategy&current=mixed) |
| A3 | `context_compaction` | `summarize` | low | “hierarchical compressionprogressively summarizes completed sub-goals into compact digests” | paper Sec. 2.2 | Paper-only evidence. loop.py mentions a context-window guard, but its implementation was truncated from the bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20context_compaction&system=deeptutor&dimension=A3%20context_compaction&current=summarize) |
| A4 | `observation_format` | `raw_text` | low | “on the tool label, appends the assistant + tool messages and dispatches” | [deeptutor/core/agentic/loop.py:12@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/deeptutor/core/agentic/loop.py#L12) | Tool-result format is inferred from the loop docstring; no conversion line was available. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20observation_format&system=deeptutor&dimension=A4%20observation_format&current=raw_text) |

## B. Tool interface

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| B1 | `tool_call_format` | `native_function_calling` | medium | “Native tool calling on every cloud OpenAI-compatible provider” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) | The loop also uses a first-line label protocol (THINK / tool label). DSML text tool calls are mentioned in the README; the parser was not in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20tool_call_format&system=deeptutor&dimension=B1%20tool_call_format&current=native_function_calling) |
| B2 | `tool_count` | `not_reported` |  |  |  | The tool registry was not included in the evidence bundle. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20tool_count&system=deeptutor&dimension=B2%20tool_count&current=not_reported) |
| B3 | `edit_primitive` | `not_reported` |  |  |  | No edit tool definition was in the evidence. Co-Writer diffs are a user-facing UI feature, not an agent edit primitive. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20edit_primitive&system=deeptutor&dimension=B3%20edit_primitive&current=not_reported) |
| B4 | `tool_schema_source` | `not_reported` |  |  |  | The schema-producing code was not in the evidence. MCP servers are supported per the README. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20tool_schema_source&system=deeptutor&dimension=B4%20tool_schema_source&current=not_reported) |
| B5 | `protocol_standardization` | `mcp` | medium | “built-in tools, MCP servers, CLI apps” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20protocol_standardization&system=deeptutor&dimension=B5%20protocol_standardization&current=mcp) |

## C. Control loop

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| C1 | `loop_primitives` | `fixed_pipeline, generate_test_repair, react` | medium | “The agentic loop drives a conversation with the LLM until one of the caller-declared \*terminal labels\* fires.” | [deeptutor/core/agentic/loop.py:3-4@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/deeptutor/core/agentic/loop.py#L3-L4) | The default chat path is the react loop. Question generation uses validator-driven regeneration (paper Sec. 2.3). Deep Research is a multi-stage pipeline. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20loop_primitives&system=deeptutor&dimension=C1%20loop_primitives&current=fixed_pipeline%7Cgenerate_test_repair%7Creact) |
| C2 | `planning_granularity` | `explicit_plan_object` | low | “it produces a tutoring planP=⟨𝑠 1,...,𝑠 𝐾⟩ of concrete, annotated sub-goals.” | paper Sec. 2.2 | Paper-only evidence. Mastery Path also stores a plan. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20planning_granularity&system=deeptutor&dimension=C2%20planning_granularity&current=explicit_plan_object) |
| C3 | `multi_agent_topology` | `single` | low | “A single agent loop executes every capability” | paper Sec. 3 | Consultable subagents (consult\_subagent) are reachable. Some capabilities use multiple specialised agents. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20multi_agent_topology&system=deeptutor&dimension=C3%20multi_agent_topology&current=single) |
| C4 | `delegation_mechanism` | `subagent_spawn` | low | “consult\_subagenttool (bounded rounds)” | paper Table 1 | Consults external agents (Claude Code, Codex) or Partners. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20delegation_mechanism&system=deeptutor&dimension=C4%20delegation_mechanism&current=subagent_spawn) |
| C5 | `human_in_loop` | `not_reported` |  |  |  | No confirmation or permission code was in the evidence. The loop mentions pause handling, and book spine approval exists per the README. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20human_in_loop&system=deeptutor&dimension=C5%20human_in_loop&current=not_reported) |

## D. Memory and state

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| D1 | `short_term_state` | `structured_task_state` | low | “self-notesdistill each step’s outcome into a concise takeaway” | paper Sec. 2.2 |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20short_term_state&system=deeptutor&dimension=D1%20short_term_state&current=structured_task_state) |
| D2 | `long_term_memory` | `episodic_db, file_notes, skill_library, vector_store` | low | “Every node carries a dense embedding, enabling similarity-based retrieval across the entire forest.” | paper Sec. 2.1.2 | Evidence covers the trace forest (episodic, embedded), the learner profile, and installable skills. The file\_notes value is inferred from the profile store. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20long_term_memory&system=deeptutor&dimension=D2%20long_term_memory&current=episodic_db%7Cfile_notes%7Cskill_library%7Cvector_store) |
| D3 | `state_persistence` | `not_reported` |  |  |  | The README mentions a restart-safe turn runtime, but no code was in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20state_persistence&system=deeptutor&dimension=D3%20state_persistence&current=not_reported) |

## E. Verification and repair

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| E1 | `self_verification` | `llm_judge, test_execution` | low | “LLM-based verification assesses template alignment, factual correctness, and pedagogical soundness for all items, while computational questions undergo additional sandboxed code execution.” | paper Sec. 2.3 | Applies to question generation only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20self_verification&system=deeptutor&dimension=E1%20self_verification&current=llm_judge%7Ctest_execution) |
| E2 | `retry_policy` | `until_pass` | low | “Failed pairs receive structured diagnostic feedback and are regenerated until both pedagogical and factual constraints are met.” | paper Sec. 2.3 | Applies to question generation only. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20retry_policy&system=deeptutor&dimension=E2%20retry_policy&current=until_pass) |
| E3 | `rollback` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20rollback&system=deeptutor&dimension=E3%20rollback&current=not_reported) |

## F. Budget and termination

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| F1 | `termination_condition` | `max_steps, model_declared` | medium | “max-iter forced finalization” | [deeptutor/core/agentic/loop.py:20@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/deeptutor/core/agentic/loop.py#L20) | Terminal labels end the loop, which counts as model\_declared. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20termination_condition&system=deeptutor&dimension=F1%20termination_condition&current=max_steps%7Cmodel_declared) |
| F2 | `cost_controls` | `not_reported` |  |  |  | Token tracking exists but no budget code was in the evidence. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20cost_controls&system=deeptutor&dimension=F2%20cost_controls&current=not_reported) |
| F3 | `timeouts` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20timeouts&system=deeptutor&dimension=F3%20timeouts&current=not_reported) |

## G. Sandbox and environment

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| G1 | `execution_isolation` | `not_reported` |  |  |  | The README mentions a tool sandbox but gives no workspace code. Docker is a deployment option for the whole app. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20execution_isolation&system=deeptutor&dimension=G1%20execution_isolation&current=not_reported) |
| G2 | `filesystem_access` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20filesystem_access&system=deeptutor&dimension=G2%20filesystem_access&current=not_reported) |
| G3 | `network_policy` | `not_reported` |  |  |  |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20network_policy&system=deeptutor&dimension=G3%20network_policy&current=not_reported) |
| G4 | `permission_model` | `not_reported` |  |  |  | The README mentions deny-by-default MCP tools for non-admin users. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20permission_model&system=deeptutor&dimension=G4%20permission_model&current=not_reported) |

## H. Observability and governance

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| H1 | `tracing` | `structured_traces` | low | “L1 traces, L2 surface summaries, and L3 synthesis” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20tracing&system=deeptutor&dimension=H1%20tracing&current=structured_traces) |
| H2 | `replayability` | `partial` | low | “Partner conversations gain branch / resume / delete with a replayable trace” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20replayability&system=deeptutor&dimension=H2%20replayability&current=partial) |
| H3 | `eval_hooks` | `not_reported` |  |  |  | TutorBench is described in the paper; whether its code is in the repo is unknown. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20eval_hooks&system=deeptutor&dimension=H3%20eval_hooks&current=not_reported) |
| H4 | `guardrails` | `not_reported` |  |  |  | The README mentions a skill install security gate. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20guardrails&system=deeptutor&dimension=H4%20guardrails&current=not_reported) |

## M. Meta

| Dim | Dimension | Value or state | Confidence | Quote | Locator | Coder note | |
|---|---|---|---|---|---|---|---|
| M1 | `target_domain` | `general_tool_use, other, research` | high | “DeepTutor is an agent-native learning workspace that connects tutoring, problem solving, quiz generation, research, visualization, and mastery practice in one extensible system.” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) | Primary domain is education/tutoring. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20target_domain&system=deeptutor&dimension=M1%20target_domain&current=general_tool_use%7Cother%7Cresearch) |
| M2 | `open_source` | `yes` | medium | “License-Apache\_2.0” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20open_source&system=deeptutor&dimension=M2%20open_source&current=yes) |
| M3 | `model_agnostic` | `yes` | high | “Multi-provider LLM & embedding support” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20model_agnostic&system=deeptutor&dimension=M3%20model_agnostic&current=yes) |
| M4 | `primary_artifact` | `repo` | high | “✨ \*\*v1.6.2 is live.\*\*” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) | The repo postdates the paper (arXiv v3, Jul 2026). | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20primary_artifact&system=deeptutor&dimension=M4%20primary_artifact&current=repo) |
| M5 | `first_release_date` | `2026-04-04` | medium | “\*\*\[2026.4.4\]\*\* \[v1.0.0-beta.1\]” | [README.md@3dc372f55128](https://github.com/hkuds/deeptutor/blob/3dc372f551285ea8ffd552ba01cd5dd16c59cb25/README.md) | First tag of the 1.x line per the README release list. Project first release was v0.2.0 (2026-01-02) or 2025-12-29. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20first_release_date&system=deeptutor&dimension=M5%20first_release_date&current=2026-04-04) |
| M6 | `pinned_version` | `v1.6.2 @ 3dc372f551285ea8ffd552ba01cd5dd16c59cb25 (2026-08-31)` | high | “ref: tag:v1.6.2 3dc372f551285ea8ffd552ba01cd5dd16c59cb25 2026-08-31” | github:HKUDS/DeepTutor |  | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20pinned_version&system=deeptutor&dimension=M6%20pinned_version&current=v1.6.2%20%40%203dc372f551285ea8ffd552ba01cd5dd16c59cb25%20%282026-08-31%29) |
| M7 | `stars` | `39997` | medium | “stars: 39997” | evidence header | No date stamp was given. | [fix](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20stars&system=deeptutor&dimension=M7%20stars&current=39997) |

## Silent cells you can settle fastest

The design cells below are `not_reported` for this system, ordered by how often the whole field is silent on them (field-level weighted rate). If you know the answer, a quote and a file:line at the pinned commit settles the cell.

1. G3 `network_policy` (Network policy): 93.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20network_policy&system=deeptutor&dimension=G3%20network_policy&current=not_reported)
2. G2 `filesystem_access` (Filesystem access): 87.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20filesystem_access&system=deeptutor&dimension=G2%20filesystem_access&current=not_reported)
3. E3 `rollback` (Rollback / undo): 86.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20rollback&system=deeptutor&dimension=E3%20rollback&current=not_reported)
4. D3 `state_persistence` (State persistence across runs): 86.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20state_persistence&system=deeptutor&dimension=D3%20state_persistence&current=not_reported)
5. F3 `timeouts` (Timeouts): 82.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20timeouts&system=deeptutor&dimension=F3%20timeouts&current=not_reported)
6. G4 `permission_model` (Permission model): 81.4% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20permission_model&system=deeptutor&dimension=G4%20permission_model&current=not_reported)
7. F2 `cost_controls` (Cost controls): 80.2% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20cost_controls&system=deeptutor&dimension=F2%20cost_controls&current=not_reported)
8. B2 `tool_count` (Tool count at pinned version): 77.5% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20tool_count&system=deeptutor&dimension=B2%20tool_count&current=not_reported)
9. C5 `human_in_loop` (Human-in-the-loop points): 76.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20human_in_loop&system=deeptutor&dimension=C5%20human_in_loop&current=not_reported)
10. H4 `guardrails` (Guardrails): 74.7% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20guardrails&system=deeptutor&dimension=H4%20guardrails&current=not_reported)
11. B4 `tool_schema_source` (Tool schema source): 72.1% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20tool_schema_source&system=deeptutor&dimension=B4%20tool_schema_source&current=not_reported)
12. B3 `edit_primitive` (Edit primitive): 70.8% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20edit_primitive&system=deeptutor&dimension=B3%20edit_primitive&current=not_reported)
13. H3 `eval_hooks` (Evaluation hooks): 67.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20eval_hooks&system=deeptutor&dimension=H3%20eval_hooks&current=not_reported)
14. G1 `execution_isolation` (Execution isolation): 64.3% of the field silent. [Settle it](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20execution_isolation&system=deeptutor&dimension=G1%20execution_isolation&current=not_reported)

---

Is a cell wrong? Open a *wrong cell* issue: <https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20%3Cdimension%3E&system=deeptutor> (or use the row's *fix* link, which also fills in the dimension and the current value).

Explorer permalink: <https://harness-db.github.io/harness-db/#system=deeptutor>

HARNESS-DB 1.0.0 (doi:10.5281/zenodo.23031354), data CC BY 4.0. Rendered by `scripts/system_card.py` from `data/systems.json`.
