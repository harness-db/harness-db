# What is an agent harness? Working definition for HARNESS-Review

Status: v0.1, 2026-09-16. This document is the Background/definition section of the paper and the
gate for screening (protocol §3–4) and coding (`docs/coding_manual.md`). Changes after OSF
registration are logged in `docs/protocol_prisma_p.md` under Amendments.

Companion files: `schema/dimensions.json` (38 dimensions, layers A–H plus M),
`docs/protocol_prisma_p.md` (§3 short form, §4 eligibility).

---

## 1. One-sentence definition

An **agent harness** is the software layer between a language model and a task environment that
repeatedly assembles the model's input, executes the model's chosen actions, and decides whether to
continue, so that a model that can only emit text becomes a system that can complete multi-step tasks.

## 2. Formal statement

Let **M** be a model: a function from an input token sequence to an output token sequence, together
with its decoding configuration (weights, sampling parameters, native tool-call format, reasoning
mode). Let **E** be a task environment: a state space, a set of executable operations with observable
results (files, shells, browsers, APIs, humans), and a task specification. **M** cannot act on **E**
and **E** cannot read **M**; the harness is the only thing that connects them.

A harness **H** is a software layer that, given **M** and **E**, implements the following eight
functions. Each clause names the layer of `schema/dimensions.json` that codes it.

| # | Clause | What the harness does | Layer |
|---|---|---|---|
| (i) | **Assembles input** | At every step, constructs the sequence the model sees: system prompt, task, prior steps, tool results, retrieved context, memory; decides what is dropped, summarized, or reformatted as the transcript grows. | **A** Context assembly (A1–A4) |
| (ii) | **Exposes and executes actions** | Declares to the model which operations exist and in what syntax, parses the model's output into an operation, executes it against **E**, and returns the result as an observation. | **B** Tool interface (B1–B5) |
| (iii) | **Decides continuation and termination** | After each step, chooses the next step: call the model again, branch, delegate to a sub-agent, ask a human, or stop; and defines the conditions under which a run ends. | **C** Control loop (C1–C5); termination condition in **F1** |
| (iv) | **Holds state** | Keeps information that outlives a single model call (within a run: scratchpads, plans, task state) and optionally a single run (across runs: notes, skill libraries, checkpoints, resumable sessions). | **D** Memory and state (D1–D3) |
| (v) | **Verifies and repairs** | Checks the model's outputs or the environment's state against some oracle (tests, linters, a judge, self-critique) and triggers retry, rollback, or repair. | **E** Verification and repair (E1–E3) |
| (vi) | **Enforces budgets and permissions** | Bounds a run in steps, tokens, cost, or wall-clock time; gates which operations the model may execute, with or without a human in the loop. | **F** Budget and termination (F1–F3); **G4** permission model; **C5** human-in-the-loop |
| (vii) | **Isolates execution** | Chooses and configures where actions execute and what they may touch: process, container, VM, remote runtime; filesystem scope; network policy. | **G** Sandbox and environment (G1–G3) |
| (viii) | **Records and governs** | Emits traces, supports replay, exposes evaluation hooks, and applies guardrails to inputs, outputs, or actions. | **H** Observability and governance (H1–H4) |

Compactly, **H = ⟨α, τ, κ, σ, ν, β, ι, ρ⟩** for clauses (i)–(viii), and an **agent** is the run-time
composition **Agent = (M, H, E)**: the same H with a different M is a different agent and the same
(M, H) on a different E is a different agent, but H is the same system in all three cases. This is
what makes the "harness effect" a well-posed question: hold M and E fixed and vary H.

### 2.1 Minimality: which clauses are necessary

Clauses **(i), (ii), (iii)** are necessary. A layer that does not assemble input, does not execute
actions, or does not loop is not a harness (it is a prompt, a tool server, or a pipeline
respectively). Clauses **(iv)–(viii)** may be trivial in a given harness (no memory, no verification,
a fixed step cap, no sandbox, no tracing); a trivial value is still a value and is coded as such
(`none`) rather than `not_reported`. The **minimal harness** is therefore a loop that (i) formats
the transcript, (ii) parses and executes one or more actions, and (iii) stops on a finish action or
a step cap. ReAct (Yao et al., 2022) is exactly this and is the earliest system in the corpus.

### 2.2 What the definition deliberately does not require

- It does not require the harness to be **model-agnostic**. A harness that only works with one
  model family is still a harness (M3 records this).
- It does not require **source code**. A harness is defined by what it does, not by whether we can
  read it; closed systems enter the corpus if their behavior is documented well enough to code
  (§5.1, case 5).
- It does not require **autonomy**. A harness with a human approval step at every action is still
  a harness (C5, G4 record the human's role).
- It does not require **multiple agents**, **planning**, or **memory**. Those are values on
  dimensions, not entry conditions.

---

## 3. Boundary rules

Each rule states what is *not* the harness, what the harness *contains* at that boundary, and a
worked example. The recurring test is: **would changing this thing, with everything else fixed,
change what the model sees, what it can do, or when it stops?** If yes, it is harness.

### 3.1 Harness vs. model (weights and decoding)

**Not harness:** the weights; the decoding configuration (temperature, top-p, reasoning effort,
max output tokens); the tool-call *syntax the model was trained to emit* (e.g., a native
function-calling format); any capability that lives inside a single forward pass.

**Harness:** the tool *schemas* handed to the model; the parser that turns model output into an
executed operation; the choice of which decoding configuration to use at which step; any retry or
re-prompt when output is malformed.

**Worked example.** Qwen-Agent runs on a Qwen model fine-tuned to emit function calls. The
fine-tuning is model (out of scope, §3.7). The `FnCallAgent` loop that registers tools, injects
their schemas, parses the call, runs it, and appends the result is harness. If we swapped Qwen for
Llama and the loop still ran, the harness would be unchanged; if we swapped the loop for
OpenHands and kept Qwen, the model would be unchanged.

**Grey zone resolved:** a "reasoning model" that decides internally when to stop thinking is doing
model-side control; the harness still owns (iii) because it decides whether to call the model
again after the answer. Model-side compaction of its own context (A3 `model_native`) is recorded as
a harness value because the harness chose to rely on it.

### 3.2 Harness vs. prompt

**Not harness:** a prompt on its own. A system prompt, a few-shot template, a chain-of-thought
instruction, or a "persona" is text sent to the model once; it does not execute anything and does
not loop.

**Harness contains prompts:** every harness has at least one prompt (clause (i)); the prompt is
part of the harness, and A1 records how it is produced. A *prompting technique* becomes a harness
the moment it specifies a loop with actions.

**Worked example.** "Let's think step by step" (Kojima et al., 2022) is a prompt: one call, no
actions. Chain-of-thought with self-consistency is still a prompt plus a sampler: N calls, but no
action on any environment and no step-dependent input. ReAct is a harness: the template *and* the
rule "parse `Action:`, run it, append `Observation:`, call again until `Finish`". The ReAct paper
is therefore included as a system (§5.1, case 3), while the CoT paper is not.

### 3.3 Harness vs. agent

**Agent** = **(M, H, E)** at run time. "SWE-agent with GPT-4 on SWE-bench Lite" is an agent;
"SWE-agent" is the harness; "GPT-4" is the model; "SWE-bench Lite" is the environment plus task.

**Coding consequence.** The `systems` table has one row per harness; the `results` table has one
row per agent-run (system × model × benchmark × split). A paper that runs one harness with five
models contributes one system and five results rows. A paper that runs five harnesses with one
model contributes up to five systems (each screened separately) and five results rows.

**Worked example.** *The Scaffold Effect* (arXiv:2607.22585) reports the same model under three
scaffolds. It introduces no new harness; it is linked as a `paper` to the three existing systems
and contributes results rows. It is not itself a system.

### 3.4 Harness vs. framework or library

**A framework is a harness-construction kit**, not a harness: LangGraph, LangChain, the OpenAI
Agents SDK, Semantic Kernel, AutoGen-core, CrewAI-core, DSPy, Pydantic AI. It supplies parts
(graph runtime, checkpointer, tool decorators) from which an application assembles a harness.

**A specific application built on a framework is a harness.** So is the framework's own
**shipped default agent**, when one exists (LangGraph `create_react_agent`, AutoGen's default
`AssistantAgent` + `UserProxyAgent` pair, CrewAI's default sequential `Crew`, MetaGPT's fixed
software-company SOP). We code a framework **only through its shipped default agent**, at the
default configuration, and set the evidence to the file that defines that default. Dimensions the
framework leaves entirely to the application are coded from the default and the note field records
"framework default; application-overridable".

**Worked example.** LangGraph the library: not a system. `langgraph.prebuilt.create_react_agent`
at the pinned release: a system named "LangGraph (prebuilt ReAct agent)", C1 = `react`, D3 =
`checkpoint` because the default checkpointer is exposed. Prometheus (Rombaut §4.1.3), an
application built on LangGraph with a compiled state machine: a separate system. Both are in the
corpus; neither is "LangGraph".

**Why this rule and not "exclude frameworks":** frameworks are the harnesses most people actually
run, and the empirical harness-effect papers compare them. Excluding them would drop AutoGen,
MetaGPT and CrewAI, which every prior survey covers. The cost is that a "default configuration" is
a convention; we make it explicit and reproducible by pinning the file and commit.

### 3.5 Harness vs. runtime or sandbox

**The runtime is part of the harness when the harness chooses and configures it.** OpenHands
launches a Docker runtime image with a defined filesystem mount and network policy; those choices
are harness values (G1 = `container`, G2, G3). SWE-agent's `SWEEnv` that shells into a container
is harness. Claude Code's per-call permission prompt and its `--dangerously-skip-permissions`
flag are harness (G4).

**A sandbox product on its own is not a harness:** E2B, Modal Sandboxes, Daytona, Firecracker,
gVisor, a browser sandbox, an MCP server, a vector database, a tracing platform (Langfuse, Phoenix).
These are *components* that a harness may adopt; they implement one clause, not the loop. They are
excluded with code `out_of_scope` (sub-reason `component_only`), and the harnesses that adopt them
record the adoption (G1, B4/B5, H1).

**Worked example.** "E2B" alone: excluded. "Open Interpreter, which executes code in a local
subprocess by default and can be configured to use E2B": included, G1 = `subprocess` at default,
note records the E2B option.

### 3.6 Harness vs. benchmark

**A benchmark is not a harness**: it is an environment plus tasks plus a scorer (E in our
notation). SWE-bench, OSWorld, WebArena, GAIA, τ-bench, Terminal-Bench are recorded in the
`results` table as benchmarks and are not systems.

**A benchmark's reference agent is a harness.** When a benchmark paper ships a runnable baseline
that loops a model over the environment with actions, that baseline is a system, named
"<benchmark> reference agent" and versioned with the benchmark release.

**Worked example.** SWE-bench (Jimenez et al., 2024) ships a retrieval-plus-generation baseline
(BM25 → single patch generation) with no loop: it is not a harness, and SWE-bench contributes no
system. WebArena ships a baseline agent that observes the accessibility tree, emits actions, and
loops until `stop`: "WebArena reference agent" is a system (A4 = `a11y_tree`, C1 = `react`).
OSWorld's baseline, BrowserGym's generic agent, and AgentBench's per-environment agents are treated
the same way. Terminal-Bench's Terminus agent is a system.

### 3.7 Harness vs. training and RL

**Model training is out of scope** unless it changes the harness. Fine-tuning a model to emit tool
calls (Toolformer, Gorilla), RL on agent trajectories (SWE-RL, ToolRL, AgentTuning), and
distillation of trajectories change **M**, not **H**. These papers are excluded with
`out_of_scope` (sub-reason `training_only`) and recorded in a side table
(`data/training_side_table.csv`) **only if** they also introduce or modify a harness component
(a new tool interface, a new observation format, a new loop) that a coder could put on a
dimension. In that case the harness component is coded as a system if it passes the codability
threshold, and the side table records the link.

**Worked example.** Toolformer: fine-tunes for API calls; the inference-time "execute the call and
splice the result" is a single-pass insertion, not a loop; excluded, side table entry "changes B1
syntax only". ToolLLM: fine-tunes ToolLLaMA **and** introduces DFSDT, a depth-first tree search
over tool calls with an environment; DFSDT passes (i)–(iii) and is coded as a system
("ToolLLM/DFSDT", C1 = `tree_search`); the fine-tuning is noted in the side table. SWE-Gym /
SWE-smith: produce training data by running an existing harness (SWE-agent/OpenHands); no new
harness; excluded, side table entry links to the harness used.

---

## 4. Relationship to the layers A–H

The eight clauses map one-to-one onto layers A–H with two deliberate exceptions, both in clause
(vi): termination lives in F (F1) because we want termination policy and budget reported together
(RQ4 flags both as under-reported), and the permission model lives in G (G4) because in practice it
is configured alongside isolation. The `M` layer (M1–M7) is metadata on the system, not a clause
of the definition. The crosswalk column in `schema/dimensions.json` records, per layer, which
ETCLOVG layer, Guo responsibility, and Rombaut dimension it corresponds to; §6 below justifies
those mappings at the definition level.

---

## 5. Decision procedure for screeners

Apply in order to each record (paper, repository, or technical report). Stop at the first
exclusion. Record the step number at which the decision was made in the screening log.

1. **Name the candidate system(s).** Does the record describe, release, or document a *named*
   software system that runs a language model (not merely use one as a black box in a single
   call)? If the record introduces no system and only evaluates or discusses existing ones, go to
   step 10. If there is no named system at all, exclude: `no_harness_description`.
2. **Loop test (clause iii).** Does the system call the model more than once per task, with the
   input to call *t+1* depending on the outcome of an action taken after call *t*? If the system is
   a single call, or N independent samples with no environment feedback (self-consistency,
   best-of-N, Tree-of-Thoughts without tools), exclude: `out_of_scope` (`no_loop`).
3. **Action test (clause ii).** Does the model's output select an operation that is executed
   against something outside the model (shell, file, browser, API, code interpreter, another agent,
   a human) and whose result is fed back? If the only "action" is producing more text, exclude:
   `out_of_scope` (`no_actions`).
4. **Input-assembly test (clause i).** Does the source say anything about how the model's input is
   constructed at each step (template, history handling, observation format)? This is almost always
   satisfied; if it is not, it will fail step 7.
5. **Whole-versus-part test.** Is the artifact the loop itself, or one part a loop could adopt
   (sandbox, MCP server, memory store, skills pack, tracing SDK, protocol spec, tool library)? A part
   is excluded: `out_of_scope` (`component_only`). Record it in `data/components.csv` so harnesses
   can be linked to it.
6. **Framework test.** Is the artifact a construction kit? If it ships a runnable default agent,
   continue with that default as the system (§3.4). If it ships no default agent, exclude:
   `out_of_scope` (`framework_no_default`).
7. **Codability test (criterion b).** From the paper, the repository at the pinned version, and
   official documentation together, can at least **19 of the 38** dimensions be coded with an
   evidence string, including at least one dimension in each of layers A, B, and C? If not, exclude:
   `no_harness_description`. Leaked or decompiled source is not admissible evidence.
8. **Domain and date test (criteria a, c).** Embodied robotics or physical actuation as the primary
   environment: `out_of_scope` (`embodied`). First public release before 2022-10-01 or after
   2026-08-31: `out_of_scope` (`date`).
9. **Language test (criterion d).** Paper or documentation not available in English: `other`
   (`language`). Code comments in any language are fine.
10. **Duplicate test.** Is the system already in `systems`? If it is the same major version, link the
    record as an additional `paper` for that system and, if it reports scores, add `results` rows; the
    record is logged `duplicate_system` and adds no system. If the record describes a major redesign
    (protocol §4.4), create a new versioned system row.
11. **Training test.** Does the record only change the model (§3.7)? Exclude `out_of_scope`
    (`training_only`), and add a side-table entry if it modifies any harness component.
12. **Include.** Assign a `system_id`, pin the version (protocol §4.5), and pass to coding.

### 5.1 Edge cases resolved

| # | Case | Decision | Steps that decide it |
|---|---|---|---|
| 1 | **Paper that only fine-tunes a model for tool use** (Toolformer, Gorilla, ToolACE) | Exclude `out_of_scope` (`training_only`); side-table entry noting any tool-call syntax it introduces. If the paper *also* contributes a loop over an environment (ToolLLM's DFSDT), the loop is screened as a system in its own right. | 2, 11 |
| 2 | **Multi-agent framework paper** (AutoGen, MetaGPT, CrewAI, CAMEL, ChatDev) | Include as a system **through its shipped default configuration** (MetaGPT's SOP pipeline; AutoGen's two-agent chat; CrewAI's sequential crew). C3/C4 record topology and delegation. The core library without a default agent is a construction kit and is not a system. | 6, 7 |
| 3 | **Prompting technique** (ReAct, Reflexion, CoT, self-consistency, ToT, LATS) | ReAct: **include**, it is the minimal harness (loop + actions + finish). Reflexion: include (adds verification (v) and cross-trial memory (iv) on top of a ReAct actor). CoT, self-consistency: exclude (`no_loop`/`no_actions`). Tree-of-Thoughts on Game-of-24 without tools: exclude (`no_actions`). LATS: include (tree search over ReAct with environment feedback). | 2, 3 |
| 4 | **Browser-automation library with an LLM plugin** (Playwright MCP, Stagehand, Browser-Use, Skyvern) | Playwright MCP server: exclude (`component_only`, it exposes actions but has no loop). Stagehand: include from the release that added its `agent()` loop; earlier `act()/extract()`-only versions are components. Browser-Use and Skyvern: include (they own the loop, the DOM observation format, and termination). | 2, 5 |
| 5 | **Vendor product, no public source, detailed technical report** (Devin, Claude Code, Codex cloud, Cursor agent) | Include if step 7 passes from vendor-published material only (docs, engineering posts, system cards, CLI help, observable behavior of a released binary). M2 = `no`, M4 = `tech_report`, and each `not_reported` cell is a data point for RQ4. Claude Code passes (extensive public docs on permissions, hooks, compaction, subagents). Devin is screened on Cognition's published posts and is expected to be borderline; the screening log records the count of codable dimensions either way. Leaked or decompiled source is not admissible. | 7 |
| 6 | **Benchmark paper that ships a baseline agent** | SWE-bench ships a non-looping retrieval baseline: no system; the benchmark is recorded for `results`. WebArena, OSWorld, BrowserGym, AgentBench, Terminal-Bench (Terminus), τ-bench ship looping baselines: **include the baseline** as "<benchmark> reference agent", versioned with the benchmark. | 1, 2, 3 |
| 7 | **Self-evolving harness paper** (Self-Harness, Darwin Gödel Machine, ADAS, Meta Agent Search) | The *outer* search over harnesses is a meta-optimizer, not a harness, and is not a system. The **released or best-reported produced harness** is the system, coded at the pinned artifact; if no produced harness is released, the **seed** harness is coded. The notes field records `self_evolving=true` and the paper is linked. If the same paper reports several evolved harnesses, code the one whose results the paper headlines. | 1, 7, 10 |
| 8 | **"Skills" library paper or repo** (Voyager's skill library, the Agent Skills spec, a SKILL.md pack) | A skills repository or spec on its own: exclude (`component_only`). A system that acquires, stores, and reuses skills inside a loop (Voyager) is a system with D2 = `skill_library`. A harness that *loads* an external skills pack (Claude Code with skills) records D2 on the harness, not on the pack. | 5 |
| 9 | **Empirical harness-comparison paper** (Harness-Bench, *Same Model, Different Harness*) | Not a system. Linked as a paper to each compared system; scores go to `results`. If the paper introduces a modified harness variant to run the comparison, the variant is screened at step 10 as a possible new version. | 1, 10 |
| 10 | **Paper that runs an existing harness with a new model** | Not a system. Linked as a paper; results rows added; `duplicate_system`. | 10 |
| 11 | **Fork or minimal re-implementation** (mini-SWE-agent vs. SWE-agent; a rebranded OpenHands fork) | Architecturally distinct → separate system (mini-SWE-agent: shell-only, no tool schema, ≈100 lines; it differs from SWE-agent on B1, B3, D1, G1). Differs only in branding, UI, or model default → `duplicate_system`. Test: at least three dimensions in layers A–H differ. | 10 |
| 12 | **Reasoning-model-native agent inside an API** (Deep Research products, hosted agent APIs) | The harness exists but is inside the vendor; screen at step 7 on published material. Most will fail codability and be excluded `no_harness_description`; the exclusion count is reported as an RQ4 finding about closed harnesses. | 7 |
| 13 | **Protocol specification** (MCP, A2A, ACP) | Exclude (`component_only`); recorded in `data/components.csv`. Adoption is coded on harnesses via B4/B5. | 5 |
| 14 | **IDE with an agent mode** (Cursor, Windsurf, Copilot agent mode, JetBrains Junie) | Same rule as vendor products (case 5). The IDE is the harness's host; only the agent mode is coded. | 7 |

---

## 6. Position against competing definitions

We fetched each source and quote it verbatim. Section numbers refer to the version stated.

### 6.1 Li et al., *Agent Harness Engineering: A Survey* (the "Picrew" survey; TMLR submission 2026, PDF at picrew.github.io/LLM-Harness/main.pdf)

*Attribution note.* Our planning documents credit this survey with the tuple H=(E,T,C,S,L,V) and a
"Harness Completeness Matrix". Neither appears in the PDF. The survey's own §1 attributes the
six-component view to a different paper: "Meng et al. (2026) describe an individual harness
through six components: an execution loop, tool registry, context manager, state store, lifecycle
hooks, and evaluation interface" (Li et al., §1), i.e., E, T, C, S, L, V. That paper is Q. Meng
et al., *Agent harness for large language model agents: A survey*, Preprints, 2026. We have not
yet fetched it; the crosswalk must cite Meng et al. for the tuple and Li et al. for ETCLOVG.
The first author is Junjie Li (CMU/UAB), not "Picrew"; "picrew" is the GitHub organization
hosting the project page.

**Their definition (§2.4, Scope):**
> "We use *agent harness* in a narrower sense than 'any software around an LLM': the harness is
> the engineered wrapper that turns model calls into bounded, stateful, tool-mediated task
> execution through execution substrates, tool interfaces, context control, orchestration,
> observability, evaluation feedback, and governance constraints […]. The unit of analysis is
> therefore the infrastructure that makes long-running agent behavior controllable, inspectable,
> and recoverable, not the foundation model or prompt alone. We draw the boundary functionally
> rather than by product category: an agent framework is in scope when it exposes reusable
> mechanisms such as stateful orchestration, tool routing, runtime policy hooks, or trace capture;
> a thin model API wrapper, prompt library, static dataset, generic container runtime, vector
> database, APM dashboard, or content filter is out of scope unless it is explicitly adapted to
> agent execution, state, evaluation, or tool-use governance."

**On prompt vs. context vs. harness (§2.2):**
> "Harness engineering expands the unit of design to the closed-loop system surrounding model
> invocation. It coordinates prompts and context with execution environments, tool interfaces,
> persistent state, lifecycle control, observability, verification, and governance. The harness
> determines how model outputs become actions, how environmental outcomes return as feedback, when
> execution continues or stops, and which operations require constraints or human approval".

**Their unit of analysis (§2.6):** included are "agent frameworks with reusable orchestration or
tool-routing logic, benchmarks that instantiate executable agent environments, sandboxes packaged
for agent execution, and memory, observability, evaluation, or governance systems that operate
over agent state, traces, actions, or policies"; excluded are "simple chatbot demos, prompt packs,
thin model-client wrappers, static datasets or leaderboards without an agent runtime, generic
infrastructure components that were not agent-facing, and product pages whose technical behavior
could not be inspected from public documentation." Coding is "multi-label" with a
"single-primary-coder protocol with author audit rather than a formal multi-coder agreement study,
so we do not report Cohen's kappa" (§2.7).

**ETCLOVG (§2.3):** "*Execution* (E) determines where agent code runs and what sandbox
constraints bound it; *Tooling* (T) specifies how external capabilities are described,
discovered, and invoked; *Context* (C) controls what the model can see over short-term,
session-level, and persistent horizons; and *Lifecycle* (L) organizes the control flow that reads
and writes that state […]. *Observability* (O) captures traces, costs, failures, and reliability
signals; *Verification* (V) turns tasks and traces into evaluation, failure attribution, and
regression feedback; and *Governance* (G) constrains behavior through permission, identity, policy,
hardening, audit, and human oversight mechanisms."

**Where we agree.** The functional boundary (§2.4: "functionally rather than by product category")
and the exclusion of prompt packs and thin wrappers are the same as ours. Their §2.2 sentence
"when execution continues or stops, and which operations require constraints or human approval" is
our clauses (iii) and (vi).

**Where ours is narrower, and why.** Their unit of analysis is the *ecosystem*: a sandbox, a memory
system, an observability platform, or a benchmark environment is a "harness project" if it
implements one layer (§2.6). Ours is the *complete loop*: a component that implements one clause is
not a system (§3.5, step 5). Reason: our RQ3 regresses outcomes on design choices, which requires
each row to be something that can be run end-to-end on a benchmark; a Langfuse row has no score.
Their design fits an ecosystem map; ours fits a coded dataset.

**Where ours is broader, and why.** They centre production infrastructure; a 2022 research scaffold
such as ReAct or Reflexion is, in their §2.2 framing, closer to prompt engineering. We include those
because the time-series RQ2 needs the minimal early harnesses as the origin, and because ReAct
satisfies (i)–(iii) (§2.1).

**Layer mapping.** ETCLOVG-E → our G (G1–G3); T → B; C → A and D (we split what the model sees per
step from what persists); L → C and F (we split control flow from budget and termination, because
termination is the most under-reported item in the pilot reading and we want it counted
separately); O → H1–H3; V → E (repair) and H3 (eval hooks); G → G4 (permissions) and H4
(guardrails). We keep O and G together in H, against their argument that they are owned by
different teams in production, because in the research corpus they are almost always reported
together or not at all.

### 6.2 Guo et al., *From Question Answering to Task Completion: A Survey on Agent System and Harness Design* (arXiv:2606.20683v1, 14 Jun 2026)

**Their definition (§2.4, "Harness as the Runtime Substrate"):**
> "we use *harness* to denote the runtime infrastructure that surrounds the model and realizes
> closed-loop agent execution. The harness is broader than an individual tool, memory module,
> prompt template, or workflow script. It is the coordinating layer that decides which observations
> reach the model, how context is assembled, how the agent loop advances, how actions are executed,
> how state and artifacts persist, and how failures are detected, governed, and recovered."

Formalized as Eq. (2), **ℋ = ⟨ℐ_obs, 𝒞, ℒ, ℐ_act, 𝒮, 𝒱⟩**, with the agent as Eq. (1)
**𝒜_LLM = ⟨ℳ, ℋ⟩**. The six responsibilities (§2.4):
- "Observation interface ℐ_obs: transforms raw environment signals into model-usable observations"
- "Context manager 𝒞: determines what information enters the model context, when it enters, and in what form"
- "Control loop ℒ: orchestrates the observe-reason-act-feedback cycle, including step scheduling, stopping criteria, retries, reflection, delegation, handoffs, and multi-agent coordination. In multi-model settings, ℒ additionally implements model routing and role assignment."
- "Action interface ℐ_act: maps model outputs to executable operations"
- "State and artifact store 𝒮: persists execution state and products"
- "Verification and governance layer 𝒱: checks, constrains, and repairs execution through tests, assertions, verifier models, sandbox policies, permission gates, rollback, retry, budget control, safety constraints, and audit traces."

**On the agent (§2.2):** "an LLM-based agent is not the foundation model alone, but a coupled
system consisting of a foundation model and an execution harness." **On the loop (§2.1):** "This
closed-loop property separates agents from single-shot model calls, static retrieval systems, and
fixed automation scripts that do not revise behavior as observations change."

**Where we agree.** This is the closest definition to ours. Agent = ⟨M, H⟩ is our Agent = (M, H, E)
with E left implicit; their "broader than an individual tool, memory module, prompt template, or
workflow script" is our §3.2 and §3.5; their §2.1 loop criterion is our step 2.

**Where ours differs, and why.** Ours is a *refinement*, not a different boundary. (1) We split
their ℒ into control (C) and budget/termination (F): they list "stopping criteria" under ℒ and
"budget control" under 𝒱, a split a coder cannot apply reliably. (2) We split their 𝒱 into
verification/repair (E), permission (G4), and guardrails/audit (H4, H1): "tests" and "permission
gates" are different engineering decisions, made by different people, and correlate differently
with outcomes. (3) We give isolation its own clause (vii); they fold "sandbox policies" into 𝒱.
(4) Their ℐ_obs and 𝒞 are both in our A (A4 observation format is their ℐ_obs). (5) Ours is
narrower in one respect: their ℒ "implements model routing"; we treat model routing as a cost
control (F2) and keep the model itself outside H (§3.1). Reason for all of these: per-dimension
κ ≥ 0.6 requires each dimension to name one decision, and Guo's six responsibilities each bundle
several.

### 6.3 Rombaut, *Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures* (arXiv:2604.03515v2, 10 Apr 2026)

**Their definition (§1, Abstract and Introduction):** the scaffold is
> "the scaffolding code that surrounds the language model (the control loop, tool definitions,
> state management, and context strategy)"

which "increasingly determines how the agent behaves, what mistakes it makes, and where it spends
its token budget" (§1). Three layers (§3.2): Control Architecture ("how the agent decides what to
do next"), Tool and Environment Interface ("how the agent interacts with code and execution
environments"), Resource Management ("how the agent manages context, state, and models"); twelve
dimensions (§4.1–4.3): control loop type, loop driver, control flow implementation, tool set and
tool interface design, edit and patch format, tool discovery strategy, context retrieval paradigm,
execution isolation model, state management strategy, context compaction approach, multi-model
routing, persistent memory.

**Their inclusion criteria (§3.1):** "Coding-specific. The agent must be designed for software
engineering tasks […] This excluded general-purpose frameworks (Open Interpreter […], Deep Agents
[…]) and multi-agent orchestration platforms (MetaGPT […], CrewAI […]), whose unit of analysis is
agent coordination rather than individual agent architecture." "Open source with readable
implementation. The agent's scaffolding code (control loop, tool definitions, state management)
must be available as readable source code in a public repository, pinned to a specific commit.
This excluded Claude Code […] which is distributed as a compiled binary with no published source
repository". "Architecturally distinct. Near-duplicate agents were removed".

**Where we agree.** Rombaut's four elements are our necessary core plus state: control loop = (iii),
tool definitions = (ii), context strategy = (i), state management = (iv). We adopt his evidence
standard (pinned commit, file:line) and his "architecturally distinct" rule for forks (§5.1, case
11). His twelve dimensions map onto ours almost one-to-one (C1, C1/C4, C1, B1/B2, B3, B4, A2, G1,
D1, A3, F2, D2).

**Where ours is broader, and why.** (1) Clauses (v)–(viii): Rombaut has no verification, budget,
permission, or observability dimension; in our pilot reading these are where harnesses differ most
in 2025–2026 (permission prompts, hooks, compaction triggers), and RQ4 is about their
under-reporting. (2) Domain: he is coding-only; we include GUI, web, and general tool-use agents
(M1), because the harness effect is reported on OSWorld and WebArena as well as SWE-bench. (3)
Openness: he requires readable source; we admit closed systems that are documented well enough to
pass the codability threshold (M2 = `no`), accepting more `not_reported` cells in exchange for
covering Claude Code, Devin, and Codex, which are the systems the harness-effect literature most
often names. (4) Frameworks: he excludes multi-agent platforms because their "unit of analysis is
agent coordination"; we include them through their default agent because coordination is a
harness decision (C3, C4).

**Where ours is narrower.** Nowhere in scope; his "multi-model routing" is a single dimension (F2)
rather than a layer.

### 6.4 Banu, *Harness Engineering as Categorical Architecture: Structural Guarantees Are Harness-Level Properties* (arXiv:2605.12239v1, Apr 2026)

**Their definition.** Abstract: "The agent harness—the system layer comprising prompts, tools,
memory, and orchestration logic that surrounds the model—has emerged as the central engineering
abstraction for LLM-based agents." §1: "The model provides intelligence; the harness—prompts, tool
selection, memory management, orchestration logic, safety checks—makes that intelligence
actionable." §3.4 ("Harness as Full Architecture (G, Know, Φ)"): "The harness is not one
component of the Architecture—it *is* the Architecture." The Architecture triple is from
ArchAgents (§2.2): "G_A is the syntactic wiring—a graph of modules, ports, and directed edges
describing how information flows"; "Know_A is the knowledge structure—the set of structural
properties, invariants, and certificates the architecture maintains"; "Φ_A is the deployment
map—the mapping between abstract capability slots and concrete model/tool implementations." §3.5:
"The deployment map Φ maps abstract capability slots to concrete implementations." §7.3: "The
model is selected by Φ; changing it changes the deployment map, while supported certificates remain
tied to preserved hooks and parameters."

**Where we agree.** Banu's G (wiring) is our (ii)+(iii); his Know (invariants, certificates) is
where our (v), (vi), (viii) live; his statement that the model is chosen by Φ while the harness's
guarantees are "harness-level properties" is the same separation as our §3.1 and our M3
(model-agnostic) flag. His Memory-as-coalgebraic-state (§3.1) is our (iv).

**Where ours is narrower, and why.** Banu's harness *includes* Φ, the binding of slots to concrete
models; ours excludes the model and treats "which model at which stage" as a harness *value* (F2
`model_routing`, M3) rather than part of H. Reason: RQ3 holds the model constant across harnesses;
if H contained the model choice, "same model, different harness" would not be expressible.

**Where ours is broader, and why.** Banu's object of study is the harness that carries
*certificates*: machine-checkable structural guarantees. Almost no system in our corpus carries
any; requiring or even coding them would give an empty column. We code the mechanisms (tests,
gates, budgets, guardrails) rather than the guarantees they might certify. His framework is
compatible with ours as a *formal semantics* for layers C, E, F, H; we cite it as such and do not
adopt its notation.

### 6.5 Summary table

| Source | Unit | Elements | Includes components alone? | Includes closed systems? | Includes frameworks? | Formal? |
|---|---|---|---|---|---|---|
| Li et al. (ETCLOVG) | ecosystem project | 7 layers | yes | only if documented | yes | no |
| Meng et al. (E,T,C,S,L,V), per Li et al. §1 | individual harness | 6 components | not stated | not stated | not stated | tuple |
| Guo et al. | runtime substrate | 6 responsibilities | no | not stated | not stated | tuple, Eq. (2) |
| Rombaut | coding scaffold | 12 dims / 3 layers | no | no | no | no |
| Banu | architecture triple | (G, Know, Φ) | no | n/a | yes (compilers) | categorical |
| **Ours** | **complete loop, one row per system-version** | **8 clauses / 8 layers / 31+7 dims** | **no** | **yes, if ≥19/38 codable** | **via default agent** | **tuple H=⟨α,τ,κ,σ,ν,β,ι,ρ⟩; Agent=(M,H,E)** |

---

## 7. Open questions for co-authors

1. Whether frameworks should be coded at their *default* agent (current rule) or excluded as
   Rombaut does; the default rule makes AutoGen/CrewAI rows depend on a convention we chose.
2. Whether closed systems (Claude Code, Devin, Codex) should enter the main corpus or a side table;
   including them raises the `not_reported` rate and mixes evidence quality.
3. Whether the codability floor should be 19/38 including M1–M7 (which are nearly always codable)
   or 16/31 over layers A–H only.
4. Whether O and G should be one layer (H) or two, as Li et al. argue.
5. Whether a self-evolving harness should be coded at the seed or the produced harness.
