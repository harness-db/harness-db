# Title/abstract triage report

Generated 2026-09-17 21:25 UTC by `scripts/screen_triage.py` (seed 20260917).

Candidates: 27,747. First votes present: 27,747. Second votes present: 4,320 (second-vote coverage among non-T0 records: 4,296 of 27,688).

## Tiers

| tier | rule | n | auto_decision | to human |
|---|---|---:|---|---:|
| T0 | date_arxiv_before_window | 17 | exclude | 0 |
| T0 | date_year_before_window | 11 | exclude | 0 |
| T0 | non_english_text | 24 | exclude | 0 |
| T0 | leaderboard_bare_model_name | 6 | exclude | 0 |
| T0 | empty_title | 1 | exclude | 0 |
| **T0 total** | | **59** | | **0** |
| T1 | both_exclude | 1,798 | exclude | 57 |
| **T1 total** | | **1,798** | | **57** |
| T2 | both_include | 565 | include | 36 |
| **T2 total** | | **565** | | **36** |
| T3 | include_vs_exclude | 52 | - | 52 |
| **T3 total** | | **52** | | **52** |
| T4 | R4_human_hedge | 1,512 | - | 1,512 |
| T4 | R4a_both_negative | 147 | exclude | 4 |
| T4 | R4_human_leaderboard_record | 75 | - | 75 |
| T4 | R4_human_unresolved | 107 | - | 107 |
| T4 | R4b_include_plus_unsure_no_negative | 40 | include | 0 |
| **T4 total** | | **1,881** | | **1,698** |
| pending | second_vote_missing | 23,392 | - | 0 |
| **pending total** | | **23,392** | | **0** |

Rule definitions:

- T0 `empty_title`: no title. `date_year_before_window`: year < 2022 (the window starts 2022-10-01; year-only dates cannot resolve the month, so 2022 is kept). `date_year_after_window`: year > 2026. `date_arxiv_before_window`: validated arXiv id YYMM < 2210. No upper date bound from the paper date: a paper posted after 2026-08-31 may describe a system first released inside the window (criterion c is about the system). `leaderboard_bare_model_name`: source = leaderboard and the title is a bare model name (family + version, optional vendor in parentheses) with no agent vocabulary. `non_english_text`: fraction of ASCII letters in title+abstract < 0.6.
- T1 `both_exclude`: both models vote exclude -> exclude; verification sample = records with hash(seed, record_id) < 3%.
- T2 `both_include`: both models vote include -> forwarded to full text; verification sample = hash < 5%.
- T3 `include_vs_exclude`: the human decides (sample type `conflict`).
- T4 (at least one unsure, no include/exclude conflict), rule R4 applied to the two reasons and decision steps:
    - `R4_human_leaderboard_record`: source = leaderboard (a pseudo-record for a system without a paper, protocol 4.3): human.
    - `R4_human_hedge`: any reason contains a hedge (reference, ship, default agent, may, might, could, likely, unclear, cannot, insufficient, no abstract, needs full text, title only, whether, ...): human.
    - `R4a_both_negative`: both votes carry a step 1-3 negative signal (an `exclude` at step 1-3, or an `unsure` at step 1-3 whose reason matches survey / benchmark_only / dataset / position_paper / no_loop / no_actions) and no hedge -> exclude; a 3% verification sample goes to the human.
    - `R4b_include_plus_unsure_no_negative`: one `include` (decision_step none) + one `unsure` whose reason has no negative signal -> forwarded to full text; a 5% verification sample goes to the human.
    - `R4_human_unresolved`: everything else (unsure+unsure without two clean negatives, exclude at step 8 + unsure, include + unsure with a negative signal): human.
- `pending`: the second vote is not available yet (or came from the same model as the first); re-run after the second pass advances.

## Human workload (current coverage)

| sample_type | n |
|---|---:|
| unsure | 1,694 |
| verify_exclude | 61 |
| conflict | 52 |
| verify_include | 36 |
| **total** | **1,843** |

At 15 s per title/abstract decision: 7.7 h; at 30 s: 15.4 h.

## Projection at full coverage

Per-record rates on the 4,296 two-vote records: human title decision 42.9%, auto-forward to full text 14.1%, auto-exclude 45.3%.

- Pending records now: 23,392. The running second pass targets 21,480 records (17,184 still to come); 6,208 records (first vote by the fallback model) need a further Opus pass to get two different-model votes.
- Projected human title decisions: 1,843 now + 7,372 when the second pass completes = **9,215**; + 2,663 more if every pending record gets a second vote = 11,878 (~66 h at 20 s each).
- Projected records forwarded to full text: 605 now + ~3,294 from pending records + whatever the human forwards.

## Model-model agreement on the overlap

n = 4,320 records with two different-model votes.

- 3-class (include / exclude / unsure): kappa = 0.622, observed agreement = 0.765
- binarised (exclude vs forward = include or unsure): kappa = 0.714, observed agreement = 0.857

| vote_1 \ vote_2 | exclude | include | unsure |
|---|---:|---:|---:|
| exclude | 1,820 | 38 | 190 |
| include | 14 | 566 | 116 |
| unsure | 377 | 279 | 920 |

## T0 records (all listed so the human can eyeball the hard rules)

| rule | record_id | title | year | source |
|---|---|---|---|---|
| date_arxiv_before_window | awesome:ggjy:5bd403a2f329 | Chain-of-Thought Prompting Elicits Reasoning in Large Language Models |  | awesome |
| date_arxiv_before_window | awesome:gloriaameng:aecc14e0045f | Inner Monologue: Embodied Reasoning Through Planning with Language Models |  | awesome |
| date_arxiv_before_window | awesome:ggjy:449543a4756e | Language Models are Few-Shot Learners |  | awesome |
| date_arxiv_before_window | awesome:gloriaameng:8d3767316ee9 | OpenAI Gym |  | awesome |
| date_arxiv_before_window | awesome:ggjy:c817fe61f10e | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks |  | awesome |
| date_arxiv_before_window | awesome:ggjy:a3655fc041c8 | Training Language Models to Follow Instructions with Human Feedback |  | awesome |
| date_year_before_window | survey_refs:preprints:202604.0428:63 | Simple Smalltalk testing: With patterns | 1994 | survey_refs |
| date_year_before_window | awesome:gloriaameng:99c685622ac8 | JUnit: A Cook's Tour | 1999 | awesome |
| date_year_before_window | survey_refs:preprints:202604.0428:33 | OpenAI Gym, 2016 | 2016 | survey_refs |
| date_year_before_window | survey_refs:openreview:eONq7FdiHa:220 | Attention is all you need.Advances in neural information processing systems, 30, | 2017 | survey_refs |
| date_year_before_window | survey_refs:openreview:eONq7FdiHa:182 | The speed of containers, the security of vms | 2017 | survey_refs |
| date_year_before_window | survey_refs:openreview:eONq7FdiHa:78 | google/gvisor | 2018 | survey_refs |
| date_year_before_window | survey_refs:openreview:eONq7FdiHa:59 | Pyodide: Python distribution for the browser and node.js based on webassembly | 2018 | survey_refs |
| date_year_before_window | survey_refs:preprints:202604.0428:99 | Firecracker: Lightweight virtualization for serverless applications | 2020 | survey_refs |
| date_year_before_window | survey_refs:openreview:eONq7FdiHa:173 | The prisma 2020 statement: an updated guideline for reporting systematic reviews | 2020 | survey_refs |
| date_year_before_window | survey_refs:openreview:eONq7FdiHa:74 | A framework for few-shot language model evaluation | 2021 | survey_refs |
| date_year_before_window | survey_refs:preprints:202604.0428:62 | lm-evaluation-harness | 2021 | survey_refs |
| non_english_text | github:ArronAI007/Awesome-AGI | ArronAI007/Awesome-AGI | 2023 | github |
| non_english_text | github:EmbraceAGI/AIGC_Interview | EmbraceAGI/AIGC_Interview | 2023 | github |
| non_english_text | github:jeinlee1991/chinese-llm-benchmark | jeinlee1991/chinese-llm-benchmark | 2023 | github |
| non_english_text | github:WeThinkIn/AIGC-Interview-Book | WeThinkIn/AIGC-Interview-Book | 2023 | github |
| non_english_text | github:wikieden/Freedom-To-Chatgpt-Claude-Agent | wikieden/Freedom-To-Chatgpt-Claude-Agent | 2023 | github |
| date_arxiv_before_window | s2:1b780680bff6d176d027f193c951ce891ec76e6b | A large language model-based agent for wayfinding: simulation of spatial percept | 2024 | s2 |
| leaderboard_bare_model_name | leaderboard:osworld:minicpm-v-2-6 | MiniCPM-V 2.6 | 2024 | leaderboard |
| empty_title | openalex:W4408992007 |  | 2025 | openalex |
| leaderboard_bare_model_name | leaderboard:swe-bench:amazon-nova-premier-1-0 | Amazon Nova Premier 1.0 | 2025 | leaderboard |
| non_english_text | github:ConardLi/easy-learn-ai | ConardLi/easy-learn-ai | 2025 | github |
| non_english_text | github:IAAR-Shanghai/Awesome-AI-Memory | IAAR-Shanghai/Awesome-AI-Memory | 2025 | github |
| non_english_text | github:Linfee/spec-kit-cn | Linfee/spec-kit-cn | 2025 | github |
| non_english_text | github:lioensky/VCPToolBox | lioensky/VCPToolBox | 2025 | github |
| date_arxiv_before_window | s2:af598689eb28fe0de48f14a6f1b302ff86ac5fe9 | LLM-TripPlanner: A Large-Language-Model-Based Agent for Personalized Trip Planni | 2025 | s2 |
| date_arxiv_before_window | s2:5bfb91cba8c5a7fb353e8133a42d3d4842bb2063 | Online Reasoning Video Segmentation with Just-in-Time Digital Twins | 2025 | s2 |
| non_english_text | openalex:W4413801493 | การพฒนาแชทบอทบรการลกคาทเขาใจบรบทและเลอกใชเครองมอโดยอตโนมตดวยแบบจำลองภาษาขนาดใหญแ | 2025 | openalex |
| date_arxiv_before_window | s2:2b9e55218fb94f843124b470d07e3236e5d3c9c3 | A Comprehensive Review Tracing the Evolution of Volumetric Medical Imaging Analy | 2026 | s2 |
| date_arxiv_before_window | s2:fcaf37b7bfc9e1c15e79e1b1fb12b9a7770c6b39 | BioFlowAgent: A Registry-Constrained LLM Agent Separating Planning from Executio | 2026 | s2 |
| non_english_text | github:buchidonggua/dg-ai-notes | buchidonggua/dg-ai-notes | 2026 | github |
| leaderboard_bare_model_name | leaderboard:tau2-bench:gemini-3-1-flash-live-preview-thinking-high-sierra | gemini-3.1-flash-live-preview-thinking-high (Sierra) | 2026 | leaderboard |
| leaderboard_bare_model_name | leaderboard:tau2-bench:gpt-live-1-sierra | gpt-live-1 (Sierra) | 2026 | leaderboard |
| leaderboard_bare_model_name | leaderboard:tau2-bench:gpt-realtime-2-sierra | gpt-realtime-2 (Sierra) | 2026 | leaderboard |
| non_english_text | github:HiThink-Tech/Financial-API | HiThink-Tech/Financial-API | 2026 | github |
| date_arxiv_before_window | openalex:W7118189573 | HUAP: Toward a Trace-First Agentic Operating System A public core architecture f | 2026 | openalex |
| non_english_text | github:jiji262/build-code-agent | jiji262/build-code-agent | 2026 | github |
| non_english_text | github:KdaiP/EchoBot | KdaiP/EchoBot | 2026 | github |
| date_arxiv_before_window | s2:302c6b0468fc234b587c414fda5cb3c267f81fc3 | Large language model-driven multi-agent framework for fault detection and diagno | 2026 | s2 |
| non_english_text | github:Leey21/awesome-ai-research-writing | Leey21/awesome-ai-research-writing | 2026 | github |
| non_english_text | github:liliMozi/openhanako | liliMozi/openhanako | 2026 | github |
| date_arxiv_before_window | s2:eddd445307658518949b54ad4acc0f06c5f660a3 | Memcurrency: Memory Decay and Refresh Mechanism for Long-Running LLM Agents | 2026 | s2 |
| date_arxiv_before_window | s2:97dc26cfcaf022e95d46f948f639f3e8c80eb592 | Rule-Guided RAG and Multi-Agent Collaboration for Deterministic Legal Document A | 2026 | s2 |
| date_arxiv_before_window | s2:ced462e1e7927e92e046a6f5f0cd20f9f4a61d78 | Runtime Protection Practice for LLM Agent Security: An On-Demand Behavioral Sand | 2026 | s2 |
| non_english_text | github:Snailclimb/AIGuide | Snailclimb/AIGuide | 2026 | github |
| non_english_text | openalex:W7162227166 | The problem of controllability and verification in autonomous LLM agents | 2026 | openalex |
| date_arxiv_before_window | s2:f5e673bc833714599d06b0ed4c1fd0d99a2e0f87 | Verifier-Guided Autonomous SQL Generation Using LLM Agents and Schema-Aware Retr | 2026 | s2 |
| leaderboard_bare_model_name | leaderboard:tau2-bench:xai-realtime-sierra | xai-realtime (Sierra) | 2026 | leaderboard |
| non_english_text | github:xbtlin/ai-berkshire | xbtlin/ai-berkshire | 2026 | github |
| non_english_text | openalex:W7155464332 | Αυτόματος συντονισμός πολλαπλών εξειδικευμένων πρακτόρων για την εκτέλεση πολύπλ | 2026 | openalex |
| non_english_text | openalex:W7165204284 | Бенчмаркинг возможностей больших языковых моделей в задачах тестирования на прон | 2026 | openalex |
| non_english_text | openalex:W7161708398 | МОДЕЛЬ «Я-КВАЛИЯ МЫСЛЯЩАЯ» (ЯКМ) — НАУЧНЫЙ СКЕЛЕТ Версия 20.2: «LLM-Native Экзос | 2026 | openalex |
| non_english_text | openalex:W7204644396 | المرجع الشامل في بناء الوكلاء المستقلين (AI Agents): من النظرية إلى التطبيق" | 2026 | openalex |
| non_english_text | openalex:W7204658095 | المرجع الشامل في بناء الوكلاء المستقلين (AI Agents): من النظرية إلى التطبيق" | 2026 | openalex |

## R4a rule excludes (random 25 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason |
|---|---|---|---|
| s2:5bee1c50741e027e106d770a2b95e46c54d6ab4c | A Survey of LLM-based Agents: Theories, Technologies, Applications and | unsure: Survey of LLM-based agents; discusses existing systems. | exclude: General survey of LLM agent theories/technologies, no specific harness named. |
| s2_snowball:dc584ac95b0ebc138030300a3e62f23279f4a754 | On Coordinating LLMs and Platform Knowledge for Software Modernization | unsure: COLLMS framework for coordinating LLMs with platform knowledge is a proposal; no loop described. | exclude: Conceptual framework proposal for coordinating LLM services, no concrete harness system. |
| arxiv:2402.15116 | Large Multimodal Agents: A Survey | unsure: Survey of large multimodal agents; discusses existing systems. | unsure: Survey of multimodal agents, no single named harness system. |
| arxiv:2410.08224 | A Survey of Spatio-Temporal EEG data Analysis: from Models to Applicat | unsure: Survey of EEG analysis; discusses existing work. | exclude: Survey of EEG data analysis methods, unrelated to agent harnesses. |
| s2_snowball:2985af7568176c4c229e552cb0acaaf3502432df | Computational Experiments Meet Large Language Model Based Agents: A Su | unsure: Survey on LLM agents and computational experiments; discusses existing systems. | unsure: Survey/perspective on LLM agents in computational experiments, discusses existing systems. |
| s2_snowball:58f34f8786e878a55242a5b0bb8bad9a018f67da | Agent Design Pattern Catalogue: A Collection of Architectural Patterns | unsure: Architectural pattern catalogue from literature review; discusses existing systems, deferred to full text. | exclude: Pattern catalogue survey of architectures, not a specific named system. |
| s2_snowball:993159b86a19ad1310423f35918adfab30b6c10e | Large Model-Based Agents: State-of-the-Art, Cooperation Paradigms, Sec | unsure: Survey of LM agents; discusses existing systems, deferred to step 10. | unsure: Survey discussing multiple LM agent systems, no single named system described. |
| arxiv:2407.04622 | On scalable oversight with weak LLMs judging strong LLMs | exclude: Studies debate and consultancy oversight protocols; no actions executed outside the model. | unsure: Studies debate/consultancy protocols evaluating existing LLM systems, not a new harness. |
| s2_snowball:5aacf780ec16a29bdbe283a14f5a9e6b7e1f292d | AI Agents Under Threat: A Survey of Key Security Challenges and Future | unsure: Security survey of AI agents; discusses existing systems only. | unsure: Survey of security threats to AI agents, discusses existing systems generally. |
| arxiv:2406.12952 | SWT-Bench: Testing and Validating Real-World Bug-Fixes with Code Agent | unsure: SWT-Bench benchmark evaluating code agents on test generation; evaluates existing systems. | unsure: SWT-Bench benchmark evaluating existing code agents like SWE-Agent, no new harness. |
| s2_snowball:9d6fc78aba8a2a36009a5278ce953085d8fa80be | OdorAgent: Generate Odor Sequences for Movies Based on Large Language  | unsure: OdorAgent pairs an LLM with a text-image model to match odors to video; no loop described. | exclude: Single-pass generation of odor sequences, no iterative multi-step loop described. |
| arxiv:2411.07690 | World Models: The Safety Perspective | unsure: Survey of world models safety; surveys go to full text. | exclude: Survey of World Models safety, no named harness system. |
| acl:su-etal-2024-language | Language Agents: Foundations, Prospects, and Risks | exclude: Tutorial proposal discussing language agents conceptually; no system. | unsure: Tutorial/survey discussing language agents conceptually, no single system named. |
| arxiv:2406.00936 | A Survey of Useful LLM Evaluation | unsure: Survey of LLM evaluation; discusses existing work. | exclude: Survey proposing evaluation framework, no named harness system described. |
| awesome:gloriaameng:c556f44d6180 | What's Missing in Autonomous Research? A Systematization of Systems, B | unsure: Survey that systematizes autonomous research systems; it only discusses existing systems. | unsure: Survey of autonomous research systems, discusses existing systems. |
| arxiv:2408.06361 | Large Language Model Agent in Financial Trading: A Survey | unsure: Survey of LLM trading agents; discusses existing systems. | unsure: Survey of LLM trading agents, no single named harness system described in abstract. |
| s2_snowball:25ae2fce719c6f6f0b09de1e0f917a7b719e5e99 | The Landscape of Emerging AI Agent Architectures for Reasoning, Planni | unsure: Survey of agent architectures; only discusses existing systems, routed to step 10. | unsure: Survey of AI agent architectures discussing multiple existing systems, not one named system. |
| arxiv:2406.13605 | Nicer Than Humans: How do Large Language Models Behave in the Prisoner | unsure: Studies how existing LLMs play the iterated Prisoner's Dilemma; an evaluation study, so it goes to full text. | exclude: Studies LLM game behavior, no harness system described. |
| s2_snowball:5e675742ad455c57a6734d7959eeff635b25589e | A Survey on Complex Tasks for Goal-Directed Interactive Agents | unsure: Survey of interactive agent tasks and environments; discusses existing work. | exclude: Survey compiling tasks/environments for evaluating agents, no specific harness named. |
| arxiv:2401.14295 | Demystifying Chains, Trees, and Graphs of Thoughts | unsure: Survey/taxonomy of chain, tree, graph of thoughts prompting; discusses existing systems. | unsure: Survey/taxonomy of prompting structures, discusses existing systems not a single named harness. |
| arxiv:2402.01801 | Large Language Models for Time Series: A Survey | unsure: Survey of LLMs for time series; discusses existing methods. | exclude: Survey of LLMs for time series analysis, no named harness system. |
| s2_snowball:05f4f076a8f277f46dff9b6abc3feff1fcf31ff5 | SWE-Bench+: Enhanced Coding Benchmark for LLMs | unsure: Empirical analysis of SWE-bench quality using SWE-agent results; evaluates existing systems. | unsure: Analysis of SWE-bench dataset quality, discusses existing systems not new harness. |
| s2_snowball:c8b18682965ff9dccc0130dab3d679f78cefa617 | A Survey on Large Language Models for Code Generation | unsure: Survey of LLMs for code generation; discusses existing work. | exclude: Survey of LLMs for code generation, no named harness system with loop. |
| arxiv:2403.18105 | Large Language Models for Education: A Survey and Outlook | unsure: Survey of LLMs in education; only discusses existing systems. | exclude: Survey of LLM applications in education, no specific harness system named. |
| arxiv:2406.13261 | BeHonest: Benchmarking Honesty in Large Language Models | exclude: Honesty benchmark for LLMs; no agent or harness. | unsure: Benchmark for honesty evaluation, no named harness system described. |

## R4b rule includes (random 15 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason |
|---|---|---|---|
| survey_refs:openreview:eONq7FdiHa:188 | CREATOR: Tool Creation for Disentangling Abstract and Concrete Reasoni | unsure: CREATOR creates and executes tools with rectification; iterative loop not clearly stated. | include: CREATOR disentangles tool creation and execution, actions executed and fed back. |
| s2_snowball:b0c3e3b974bea918d0972038f1606026c8736730 | dIR - Discrete Information Retrieval: Conversational Search over Unstr | unsure: dIR text-to-SQL retrieval; optional multi-step conversational agent, loop not clearly described. | include: dIR uses multi-step reasoning conversational agent querying via text-to-SQL tool execution. |
| s2:4a75ee7e27388976c6e84ede5ff2b110c5b05736 | Multi-Agent Approach to Political Discourse Translation: From Large La | unsure: MAGIC-PTF multi-agent translation pipeline; no clear tool execution beyond agent text exchange. | include: Named MAGIC-PTF system with multiple specialized agents performing multi-stage translation loop. |
| s2_snowball:2ebcc7ea5a284a18968a515dc2c88ebb9e3af52b | ChatGraph: Chat with Your Graphs | unsure: ChatGraph generates API chains; iterative execution feedback not described. | include: ChatGraph generates and executes chains of graph analysis APIs based on LLM reasoning. |
| arxiv:2404.11964 | From Language Models to Practical Self-Improving Computer Agents | unsure: Minimal querying loop with terminal access that self-augments tools; loop and actions clear but no named syste | include: Named self-improving computer agent with querying loop and executed tool actions. |
| openalex:W7110530286 | apex™ | include: apex agent performs actions on user's PC with memory and multi-agent loop. | unsure: apex named system but description vague on tool execution loop, tool-free architecture mentioned. |
| s2_snowball:1c259361caa85c2d95a7d04e5e42fa98693da85b | Large Language Models as Evolutionary Optimizers | unsure: LMEA iterative LLM crossover with external evaluation; optimizer loop rather than tool-using agent, borderline | include: LMEA iteratively instructs LLM in evolutionary loop selecting/evaluating solutions across generations. |
| survey_refs:preprints:202604.0428:69 | BabyAGI | include: BabyAGI: task-creating, executing, prioritizing LLM agent loop, 2023. | unsure: BabyAGI named system but minimal abstract detail to confirm loop/action test. |
| acl:zhang-etal-2024-mabc | mABC: Multi-Agent Blockchain-inspired Collaboration for Root Cause Ana | unsure: mABC multi-agent RCA workflow with step limits; tool execution against system not explicit. | include: mABC multi-agent system with workflow loop and voting collaboration for RCA tasks. |
| arxiv:2410.24032 | Navigating the Unknown: A Chat-Based Collaborative Interface for Perso | unsure: CARE multi-agent chat interface; tool execution with feedback not evident. | include: CARE named multi-agent LLM system with iterative interface loop and tool use. |
| survey_refs:openreview:eONq7FdiHa:156 | yoheinakajima/babyagi | include: BabyAGI task-driven autonomous agent loop creating and executing tasks. | unsure: BabyAGI citation only, minimal detail but named system known to be a harness. |
| arxiv:2410.02829 | LLMs May Not Be Human-Level Players, But They Can Be Testers: Measurin | unsure: Game-testing framework using LLM agents in Wordle and Slay the Spire; its harness is unnamed. | include: LLM agent framework plays games (Wordle, Slay the Spire) via iterative action loop with environment. |
| arxiv:2405.14751 | AGILE: A Novel Reinforcement Learning Framework of LLM Agents | unsure: RL training framework, but describes agent with memory, tools, reflection loop. | include: Named system AGILE wraps LLM with tools, memory, expert consultation in iterative loop. |
| arxiv:2403.08337 | LLM-Assisted Light: Leveraging Large Language Model Capabilities for H | include: LLM-Assisted Light: LLM uses perception and decision tools to control traffic signals in simulation. | unsure: Traffic signal LLM framework with tools; loop/action structure not fully clear. |
| openalex:W4401006767 | PEAR: A Knowledge-guided Autonomous Pipeline for Ptychography Enabled  | unsure: PEAR abstract preview; multi-LLM ptychography workflow, tool execution loop not clearly described. | include: PEAR is a named multi-agent system automating ptychography experiments with tool use. |
