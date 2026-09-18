# Title/abstract triage report

Generated 2026-09-18 02:54 UTC by `scripts/screen_triage.py` (seed 20260917).

Candidates: 27,747. First votes present: 27,747. Second votes present: 27,647 (second-vote coverage among non-T0 records: 27,588 of 27,688). Tiebreak votes present: 0.

## Tiers

| tier | rule | n | auto_decision | to human |
|---|---|---:|---|---:|
| T0 | date_arxiv_before_window | 17 | exclude | 0 |
| T0 | date_year_before_window | 11 | exclude | 0 |
| T0 | non_english_text | 24 | exclude | 0 |
| T0 | leaderboard_bare_model_name | 6 | exclude | 0 |
| T0 | empty_title | 1 | exclude | 0 |
| **T0 total** | | **59** | | **0** |
| T1 | both_exclude | 7,687 | exclude | 230 |
| **T1 total** | | **7,687** | | **230** |
| T2 | both_include | 4,686 | include | 249 |
| **T2 total** | | **4,686** | | **249** |
| T3 | include_vs_exclude | 384 | - | 384 |
| **T3 total** | | **384** | | **384** |
| T4 | R4_human_hedge | 11,197 | - | 11,197 |
| T4 | R4a_both_negative | 1,297 | exclude | 54 |
| T4 | R4_human_leaderboard_record | 156 | - | 156 |
| T4 | R4_human_unresolved | 1,746 | - | 1,746 |
| T4 | R4b_include_plus_unsure_no_negative | 435 | include | 15 |
| **T4 total** | | **14,831** | | **13,168** |
| T5 | - | 0 | | 0 |
| pending | second_vote_missing | 100 | - | 0 |
| **pending total** | | **100** | | **0** |

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
- T5 (a tiebreak vote exists; checked before T1-T4): the records T3/T4 had sent to the human as `conflict` / `unsure` got a decisive third vote (`scripts/screen_llm.py --mode tiebreak`, prompt ta-v2-tiebreak-2026-09-17, include/exclude only, with a confidence high/medium/low). A prior vote supports the tiebreak when it is the same vote and opposes it when it is the other definite vote; `unsure` does neither. The human gets the record iff no two of the three votes agree on include or exclude (`T5_human_three_way_split`: include / exclude / unsure), or the tiebreak is low-confidence and contradicts a definite prior vote (`T5_human_low_confidence_contradiction`); sample type `tiebreak`. Otherwise the tiebreak decides: `T5_majority_include` / `T5_majority_exclude` (a prior vote agrees with it) or `T5_tiebreak_include` / `T5_tiebreak_exclude` (both priors were unsure); a 3% verification sample of the automatic decisions (hash(seed 20260916, record_id)) goes to the human as `verify_include` / `verify_exclude`.
- `pending`: the second vote is not available yet (or came from the same model as the first); re-run after the second pass advances.

## Human workload (current coverage)

| sample_type | n |
|---|---:|
| unsure | 13,099 |
| conflict | 384 |
| verify_exclude | 284 |
| verify_include | 264 |
| **total** | **14,031** |

At 15 s per title/abstract decision: 58.5 h; at 30 s: 116.9 h.

## Projection at full coverage

Per-record rates on the 27,588 two-vote records: human title decision 50.9%, auto-forward to full text 18.6%, auto-exclude 32.6%.

- Pending records now: 100. The running second pass targets 21,480 records (0 still to come); 100 records (first vote by the fallback model) need a further Opus pass to get two different-model votes.
- Projected human title decisions: 14,031 now + 0 when the second pass completes = **14,031**; + 51 more if every pending record gets a second vote = 14,082 (~78 h at 20 s each).
- Projected records forwarded to full text: 5,121 now + ~19 from pending records + whatever the human forwards.

## Model-model agreement on the overlap

n = 27,647 records with two different-model votes.

- 3-class (include / exclude / unsure): kappa = 0.564, observed agreement = 0.716
- binarised (exclude vs forward = include or unsure): kappa = 0.616, observed agreement = 0.821

| vote_1 \ vote_2 | exclude | include | unsure |
|---|---:|---:|---:|
| exclude | 7,720 | 200 | 1,777 |
| include | 184 | 4,694 | 1,043 |
| unsure | 2,790 | 1,856 | 7,383 |

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

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| arxiv:2501.13381 | Do as We Do, Not as You Think: the Conformity of Large Language Models | unsure: BenchForm conformity benchmark for LLM multi-agent interaction; evaluation study. | unsure: Benchmark BenchForm evaluates existing multi-agent systems for conformity, no new harness clearly described. | - |
| s2_snowball:ac610f55db9fdb276121b086e5ced3c1fa4590f1 | DeepStress: Stress-Testing Deep Search Agents | unsure: DeepStress is a stress-testing framework evaluating existing search agents with a synthetic retrieval environm | unsure: Stress-testing framework evaluating existing search agents, not itself a described harness. | - |
| s2_snowball:9d6fc78aba8a2a36009a5278ce953085d8fa80be | OdorAgent: Generate Odor Sequences for Movies Based on Large Language  | unsure: OdorAgent pairs an LLM with a text-image model to match odors to video; no loop described. | exclude: Single-pass generation of odor sequences, no iterative multi-step loop described. | - |
| s2:c4a9a392ce6b34a66aba95aa3096c1ad9af4c098 | RAG-Driven Memory Architectures in Conversational LLMs—A Literature Re | unsure: Literature review of memory architectures; discusses existing systems, deferred to full text. | exclude: Literature review of memory architectures, no named system described. | - |
| arxiv:2604.02211 | Multi-Agent Video Recommenders: Evolution, Patterns, and Open Challeng | unsure: Survey tracing evolution of multi-agent video recommender frameworks, discusses existing systems only. | unsure: Survey of multi-agent video recommenders (MACRec, Agent4Rec); discusses existing systems, so it goes to step 1 | - |
| s2_snowball:86de12d65a14fc10f88c97bc08ecf790f38a79ee | LocationReasoner: Evaluating LLMs on Real-World Site Selection Reasoni | unsure: Benchmark with sandbox tools evaluating ReAct/Reflexion; evaluates existing systems. | unsure: Benchmark evaluating existing agentic strategies like ReAct; no new named harness. | - |
| s2:e131a11ad907023f655f22a4fae2b2a6f2db96f7 | Reasoning and Planning with Large Language Models in Code Development | unsure: Survey/tutorial on LLMs for code development; discusses existing systems only. | unsure: Survey discussing LLM code development techniques, no single named harness system described. | - |
| arxiv:2505.07078 | Can LLM-based Financial Investing Strategies Outperform the Market in  | unsure: FINSABER backtesting framework evaluating existing LLM strategies; evaluation record. | exclude: FINSABER is a backtesting evaluation framework for existing strategies, not a harness system itself. | - |
| s2_snowball:e850a1255941cadd93e08715bc56e1cbf26523c1 | Large Language Models for Ontology Engineering: A Systematic Literatur | unsure: Systematic literature review of 36 papers on LLMs for ontology engineering with zero/few-shot prompting; revie | unsure: Systematic literature review of LLM use in ontology engineering across many papers, no single system. | - |
| arxiv:2410.18529 | Instructional Text Across Disciplines: A Survey of Representations, Do | unsure: Survey of instructional text literature; discusses existing work only. | exclude: Survey of instructional text literature, discusses no single system. | - |
| openalex:W7202139240 | Agent-to-Agent Communication | unsure: Synthesis/review of agent communication evidence; discusses existing systems. | exclude: Survey/analysis of agent-to-agent communication research, no named harness system. | - |
| openalex:W7130943401 | Agentic AI: Concepts, Architectures, Frameworks, and Challenges | unsure: Survey comparing existing frameworks; goes to step 10. | exclude: Survey/beginner's guide to agentic AI frameworks, no single named system. | - |
| s2_snowball:980cc964c8bfdcd9670265e1dcbb08f9c41749a7 | A Survey of Foundation Model-Powered Recommender Systems: From Feature | unsure: Survey of foundation-model recommenders including agentic systems. | exclude: Survey of recommender system paradigms, no named harness. | - |
| arxiv:2605.18583 | Overeager Coding Agents: Measuring Out-of-Scope Actions on Benign Task | unsure: Benchmark evaluating existing coding agent products, not a new harness description. | unsure: OverEager-Bench evaluates existing harnesses (Claude Code, OpenHands, Codex CLI, Gemini CLI). Benchmark/evalua | - |
| openalex:W7161588025 | Inference-Time Control for Trustworthy Large Language Models | unsure: Survey unifying inference-time control techniques including multi-agent orchestration; discusses existing meth | exclude: Survey/framework unifying inference-time trustworthy techniques, not a single named harness system. | - |
| arxiv:2606.26627 | Agents That Know Too Much: A Data-Centric Survey of Privacy in LLM Age | unsure: Survey of privacy in LLM agents; discusses existing systems, routed to step 10. | unsure: Survey of privacy risks in LLM agents; discusses existing systems, no new harness named. | - |
| s2_snowball:85ffc00f667e01b22160d4617e7b374ff0324ae4 | Engineering Trustworthy Agentic AI for Critical Systems | unsure: Survey of agentic-AI trustworthiness mechanisms and domains; discusses existing systems, so protocol routes it | unsure: Survey of trustworthiness across domains, discusses existing systems generally, not one harness. | - |
| arxiv:2510.12750 | VQArt-Bench: A semantically rich VQA Benchmark for Art and Cultural He | exclude: VQA benchmark built by generation pipeline; no executed actions loop. | unsure: Benchmark paper using multi-agent pipeline for dataset generation, not a described agent harness. | - |
| arxiv:2406.00252 | Towards Rationality in Language and Multimodal Agents: A Survey | unsure: Survey of rational language agents; discusses existing systems, goes to step 10. | unsure: Survey of language/multimodal agents, no single named harness system. | - |
| arxiv:2509.18420 | Instruction-Following Evaluation in Function Calling for Large Languag | unsure: Function-calling benchmark IFEval-FC; single-call evaluation, sent to step 10. | exclude: Benchmark for function calling instruction adherence, no harness system described. | - |
| openalex:W7201867232 | VATA Consolidated Findings: DSC Infrastructure Taxonomy and the AOS De | exclude: Security research report cataloguing vulnerabilities in others' systems, not a named harness. | unsure: Security report on vulnerabilities in existing agent frameworks and MCP servers. It only evaluates existing sy | - |
| s2_snowball:5cf6037bff960ed954cb4237e9d2512d66bdf39c | Time to REFLECT: Can We Trust LLM Judges for Evidence-based Research A | unsure: Meta-evaluation benchmark for LLM judges of research agents, not itself a described harness. | unsure: Meta-evaluation benchmark for LLM judges of research agents; evaluates existing systems, needs step-10 full-te | - |
| arxiv:2604.24645 | K-MetBench: A Multi-Dimensional Benchmark for Fine-Grained Evaluation  | unsure: K-MetBench is an exam-grounded evaluation benchmark over 55 models; protocol routes evaluation-only records to | exclude: A benchmark evaluating models on meteorology tasks, no named agent harness system. | - |
| s2:503f8f4d27757cdc2cb2910e17a5ef6f336219a8 | The dark side of autonomous intelligence: a survey on data leakage and | unsure: Survey discussing existing agentic AI systems' privacy risks, not a new harness. | unsure: Survey of data leakage in agentic AI; discusses existing systems, routed to full-text step 10. | - |
| arxiv:2606.00288 | Model-Native Computing Architecture: Envisioning Future System Archite | exclude: Conceptual survey/vision paper, no named system implementing harness. | unsure: Visionary survey mapping computer architecture onto agent stacks; no new system, goes to step 10. | - |

## R4b rule includes (random 15 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| s2_snowball:1c259361caa85c2d95a7d04e5e42fa98693da85b | Large Language Models as Evolutionary Optimizers | unsure: LMEA iterative LLM crossover with external evaluation; optimizer loop rather than tool-using agent, borderline | include: LMEA iteratively instructs LLM in evolutionary loop selecting/evaluating solutions across generations. | - |
| acl:zhang-etal-2026-evohyper | EvoHyper: Evolving Hypergraph Topologies for Unified Collaboration in  | unsure: EvoHyper evolves agent communication hypergraph; abstract shows message passing and memory but no externally e | include: Named multi-agent framework with controller editing hypergraph topology during task execution loop. | - |
| openalex:W7203442841 | SCU5.0 Beta Release: Security Hardening, Asynchronous Optimization, an | include: SCU5.0 beta release describes fixes and hardening of the same conversational agent platform as SCU3.0. | unsure: SCU5.0 release notes list security and async fixes for an agent platform; the abstract does not describe the a | - |
| arxiv:2511.20940 | Chatty-KG: A Multi-Agent AI System for On-Demand Conversational Questi | unsure: Chatty-KG generates SPARQL via agent pipeline; iterative loop with execution feedback not stated. | include: Multi-agent system generating and executing SPARQL queries against knowledge graphs iteratively. | - |
| arxiv:2506.17784 | AnyMAC: Cascading Flexible Multi-Agent Collaboration via Next-Agent Pr | unsure: Multi-agent communication framework; abstract doesn't mention tools or executed actions with feedback. | include: Named multi-agent system with sequential loop selecting next agent/context, actions executed and fed back. | - |
| github:TIGER-AI-Lab/TheoremExplainAgent | TIGER-AI-Lab/TheoremExplainAgent | unsure: Agent generates Manim videos; code execution feedback loop not stated in snippet. | include: TheoremExplainAgent is a named system generating and verifying video explanations via tool use. | - |
| github:yilewang/llm-for-zotero | yilewang/llm-for-zotero | include: Named research agent system for Zotero library with tool-executing loop. | unsure: Named 'research agent system' for Zotero, but README excerpt gives no evidence of multi-step tool-calling loop | - |
| github:chaitin/MonkeyCode | chaitin/MonkeyCode | unsure: AI coding platform with task management; README excerpt doesn't show agent loop details. | include: Named AI coding platform with task/model management implying tool-executing agent loop. | - |
| arxiv:2601.15153 | How to Build AI Agents by Augmenting LLMs with Codified Human Expert D | unsure: Unnamed visualization agent with classifier, RAG code generation and codified expert rules; abstract does not  | include: Named agent system with RAG, classifier, and code generation in an executed loop. | - |
| openreview:lNmZrawUMu | AlphaAgentEvo: Evolution-Oriented Alpha Mining via Self-Evolving Agent | unsure: Agentic RL training for alpha mining with tool calls; harness change uncertain. | include: AlphaAgentEvo agent performs tool calls and iterative self-evolution loop for alpha mining. | - |
| s2:e48ac2e745cd18852bee31fc68fef6e1497b56ec | An Intelligent Fault Diagnosis Method for Catenary Based on AI Agent a | unsure: LLM agent orchestrates knowledge graph retrieval; multi-step loop not explicit. | include: AI Agent dynamically queries knowledge graph via RAG, orchestrating multi-source data retrieval and fusion loo | - |
| s2_snowball:8b2d6308af43aadb3c7ccdec9431be0a995b5579 | Agentic AI for Disease-Aware Adaptive Multi-Omics Embedding: A Proof o | unsure: Unnamed plan-act-verify agent; LLM use not explicit in abstract. | include: Agent plans, acts, and verifies in self-refining loop selecting normalization and embedding methods based on o | - |
| s2:da284361714b8d732c1c3bcbadb917a86a267058 | Evidence-Grounded Multi-Agent Planning Support for Urban Carbon Govern | unsure: Four specialized RAG agents for carbon governance; abstract reads as a staged pipeline, not clearly a model-dr | include: Multi-agent system with four specialized agents performing retrieval and generation tasks iteratively. | - |
| s2:b44f55195d6f5024f174546698ddd9fffee8f043 | AI Agents: Agent GPT | unsure: Describes existing AgentGPT system generally; discussion rather than new system. | include: Agent GPT named system, plans and executes multi-step tasks using tools/APIs iteratively. | - |
| arxiv:2508.14123 | AI Agents for Photonic Integrated Circuit Design Automation | unsure: PhIDO multi-agent PIC design framework; iterative tool-execution loop not explicit in abstract. | include: Named PhIDO multi-agent framework converts requests to layouts via LLM loop. | - |
