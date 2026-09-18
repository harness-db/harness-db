# Title/abstract triage report

Generated 2026-09-18 18:03 UTC by `scripts/screen_triage.py` (seed 20260917).

Candidates: 27,747. First votes present: 27,747. Second votes present: 27,747 (second-vote coverage among non-T0 records: 27,688 of 27,688). Tiebreak votes present: 13,483.

## Tiers

| tier | rule | n | auto_decision | to human |
|---|---|---:|---|---:|
| T0 | date_arxiv_before_window | 17 | exclude | 0 |
| T0 | date_year_before_window | 11 | exclude | 0 |
| T0 | non_english_text | 24 | exclude | 0 |
| T0 | leaderboard_bare_model_name | 6 | exclude | 0 |
| T0 | empty_title | 1 | exclude | 0 |
| **T0 total** | | **59** | | **0** |
| T1 | both_exclude | 7,709 | exclude | 85 |
| **T1 total** | | **7,709** | | **85** |
| T2 | both_include | 4,703 | include | 110 |
| **T2 total** | | **4,703** | | **110** |
| T3 | include_vs_exclude | 3 | - | 3 |
| **T3 total** | | **3** | | **3** |
| T4 | R4a_both_negative | 1,301 | exclude | 25 |
| T4 | R4b_include_plus_unsure_no_negative | 438 | include | 6 |
| T4 | R4_human_hedge | 43 | - | 43 |
| T4 | R4_human_unresolved | 7 | - | 7 |
| T4 | R4_human_leaderboard_record | 1 | - | 1 |
| **T4 total** | | **1,790** | | **82** |
| T5 | T5_tiebreak_exclude | 4,771 | exclude | 58 |
| T5 | T5_majority_include | 2,078 | include | 53 |
| T5 | T5_tiebreak_include | 1,895 | include | 49 |
| T5 | T5_majority_exclude | 4,036 | exclude | 39 |
| T5 | T5_human_three_way_split | 618 | - | 618 |
| T5 | T5_human_low_confidence_contradiction | 85 | - | 85 |
| **T5 total** | | **13,483** | | **902** |
| pending | - | 0 | | 0 |

Rule definitions:

- T0 `empty_title`: no title. `date_year_before_window`: year < 2022 (the window starts 2022-10-01; year-only dates cannot resolve the month, so 2022 is kept). `date_year_after_window`: year > 2026. `date_arxiv_before_window`: validated arXiv id YYMM < 2210. No upper date bound from the paper date: a paper posted after 2026-08-31 may describe a system first released inside the window (criterion c is about the system). `leaderboard_bare_model_name`: source = leaderboard and the title is a bare model name (family + version, optional vendor in parentheses) with no agent vocabulary. `non_english_text`: fraction of ASCII letters in title+abstract < 0.6.
- T1 `both_exclude`: both models vote exclude -> exclude; verification sample = records with hash(seed, record_id) < 1%.
- T2 `both_include`: both models vote include -> forwarded to full text; verification sample = hash < 2%.
- T3 `include_vs_exclude`: the human decides (sample type `conflict`).
- T4 (at least one unsure, no include/exclude conflict), rule R4 applied to the two reasons and decision steps:
    - `R4_human_leaderboard_record`: source = leaderboard (a pseudo-record for a system without a paper, protocol 4.3): human.
    - `R4_human_hedge`: any reason contains a hedge (reference, ship, default agent, may, might, could, likely, unclear, cannot, insufficient, no abstract, needs full text, title only, whether, ...): human.
    - `R4a_both_negative`: both votes carry a step 1-3 negative signal (an `exclude` at step 1-3, or an `unsure` at step 1-3 whose reason matches survey / benchmark_only / dataset / position_paper / no_loop / no_actions) and no hedge -> exclude; a 1% verification sample goes to the human.
    - `R4b_include_plus_unsure_no_negative`: one `include` (decision_step none) + one `unsure` whose reason has no negative signal -> forwarded to full text; a 2% verification sample goes to the human.
    - `R4_human_unresolved`: everything else (unsure+unsure without two clean negatives, exclude at step 8 + unsure, include + unsure with a negative signal): human.
- T5 (a tiebreak vote exists; checked before T1-T4): the records T3/T4 had sent to the human as `conflict` / `unsure` got a decisive third vote (`scripts/screen_llm.py --mode tiebreak`, prompt ta-v2-tiebreak-2026-09-17, include/exclude only, with a confidence high/medium/low). A prior vote supports the tiebreak when it is the same vote and opposes it when it is the other definite vote; `unsure` does neither. The human gets the record iff no two of the three votes agree on include or exclude (`T5_human_three_way_split`: include / exclude / unsure), or the tiebreak is low-confidence and contradicts a definite prior vote (`T5_human_low_confidence_contradiction`); sample type `tiebreak`. Otherwise the tiebreak decides: `T5_majority_include` / `T5_majority_exclude` (a prior vote agrees with it) or `T5_tiebreak_include` / `T5_tiebreak_exclude` (both priors were unsure); a verification sample of the automatic decisions (same per-stratum rates as T1/T2: 1.12% of excludes, 2.19% of includes) (hash(seed 20260916, record_id)) goes to the human as `verify_include` / `verify_exclude`.
- `pending`: the second vote is not available yet (or came from the same model as the first); re-run after the second pass advances.

## Human workload (current coverage)

| sample_type | n |
|---|---:|
| tiebreak | 703 |
| verify_include | 218 |
| verify_exclude | 207 |
| unsure | 51 |
| conflict | 3 |
| **total** | **1,182** |

At 15 s per title/abstract decision: 4.9 h; at 30 s: 9.8 h.

## Projection at full coverage

Per-record rates on the 27,688 two-vote records: human title decision 4.3%, auto-forward to full text 32.9%, auto-exclude 64.3%.

- Pending records now: 0. The running second pass targets 21,480 records (0 still to come); 0 records (first vote by the fallback model) need a further Opus pass to get two different-model votes.
- Projected human title decisions: 1,182 now + 0 when the second pass completes = **1,182**; + 0 more if every pending record gets a second vote = 1,182 (~7 h at 20 s each).
- Projected records forwarded to full text: 9,114 now + ~0 from pending records + whatever the human forwards.

## Model-model agreement on the overlap

n = 27,747 records with two different-model votes.

- 3-class (include / exclude / unsure): kappa = 0.564, observed agreement = 0.716
- binarised (exclude vs forward = include or unsure): kappa = 0.616, observed agreement = 0.821

| vote_1 \ vote_2 | exclude | include | unsure |
|---|---:|---:|---:|
| exclude | 7,742 | 200 | 1,780 |
| include | 187 | 4,711 | 1,053 |
| unsure | 2,799 | 1,858 | 7,417 |

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

## T5 tiebreak: rule x confidence

| rule | high | medium | low | total | to human |
|---|---:|---:|---:|---:|---:|
| T5_tiebreak_exclude | 819 | 2,693 | 1,259 | 4,771 | 58 |
| T5_majority_include | 52 | 1,114 | 912 | 2,078 | 53 |
| T5_tiebreak_include | 1 | 191 | 1,703 | 1,895 | 49 |
| T5_majority_exclude | 1,466 | 2,393 | 177 | 4,036 | 39 |
| T5_human_three_way_split | 2 | 239 | 377 | 618 | 618 |
| T5_human_low_confidence_contradiction | 0 | 0 | 85 | 85 | 85 |

Tiebreak vote vs prior votes: exclude/include -> exclude: 165, exclude/include -> include: 35, exclude/unsure -> exclude: 1,560, exclude/unsure -> include: 43, include/exclude -> exclude: 86, include/exclude -> include: 98, include/unsure -> exclude: 122, include/unsure -> include: 805, unsure/exclude -> exclude: 2,245, unsure/exclude -> include: 124, unsure/include -> exclude: 329, unsure/include -> include: 1,205, unsure/unsure -> exclude: 4,771, unsure/unsure -> include: 1,895

## R4a rule excludes (random 25 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| s2:d7d4e4334bc2095f076bd6c2c3891e1b2a150a8e | Problems of Scaling Large Language Model Inference During Simultaneous | exclude: Analytic review of scaling bottlenecks, no named system that runs a model. | unsure: Analytic review of 11 sources on multi-agent inference scaling; it discusses existing systems and proposes no  | - |
| s2:afd88cee1840bd72e4f6b7233374d83c75127be8 | Goal-Based Multi-Agent AI Systems for Academic Advising: A Survey of P | unsure: Survey of goal-oriented and agentic advising architectures; discusses existing systems only, so protocol route | unsure: Survey of frameworks/policies for academic advising agents, discusses existing systems, not a single named sys | - |
| arxiv:2601.00477 | Security in the Age of AI Teammates: An Empirical Study of Agentic Pul | exclude: Empirical study of PRs authored by agents, no harness system described. | unsure: Empirical study of agent-authored GitHub PRs from AIDev dataset; only evaluates existing coding agents. | - |
| s2:c5922af13be4bd565934cd5230f66949bfd2422f | A Comprehensive Investigation of Advances in Music Understanding and G | unsure: Review of music LLM systems including agents; discusses existing systems. | exclude: Survey of music LLM systems, no single named harness described. | - |
| arxiv:2509.18420 | Instruction-Following Evaluation in Function Calling for Large Languag | unsure: Function-calling benchmark IFEval-FC; single-call evaluation, sent to step 10. | exclude: Benchmark for function calling instruction adherence, no harness system described. | - |
| s2:dc02945d8c923d7afb895d26a862e29d94cf04c0 | Safe Multi-Agent Behavior Must Be Maintained, Not Merely Asserted: Con | unsure: Position paper discussing existing multi-agent systems generally, no single named system described. | exclude: Position paper proposing the Constraint State Governance paradigm; no named system that runs a model. | - |
| s2_snowball:6f85fe04424681a9045ed955baf321a8e3bd4d62 | Large Language Models for Agentic NetOps and AIOps: Architectures, Eva | unsure: Survey of agentic NetOps/AIOps architectures, autonomy levels and assurance contracts; evaluates existing syst | unsure: Survey of agentic NetOps/AIOps architectures generally, not one named harness. | - |
| arxiv:2606.17328 | MemTrace: Probing What Final Accuracy Misses in Long-Term Memory | unsure: MemTrace is a knowledge-point benchmark evaluating 13 existing memory-system configurations; benchmark records | unsure: Benchmark probing memory accuracy across existing memory systems, not a harness. | - |
| s2_snowball:18ee9dcd91f50f62973425947b1abd34cc283dbb | From Human Memory to AI Memory: A Survey on Memory Mechanisms in the E | unsure: Survey of memory mechanisms; discusses existing systems, deferred to full text. | exclude: Survey of memory mechanisms, not a specific named harness system. | - |
| arxiv:2503.15478 | SWEET-RL: Training Multi-Turn LLM Agents on Collaborative Reasoning Ta | unsure: RL algorithm plus ColBench benchmark; training-focused, harness not described. | exclude: RL training algorithm and benchmark, no named harness system with tool loop. | - |
| openalex:W7204279246 | Agentic Artificial Intelligence: A Comprehensive Survey of Architectur | unsure: Survey of agentic AI; only discusses existing systems. | unsure: Comprehensive survey discussing multiple existing systems, not a single named harness. | - |
| arxiv:2510.08005 | Past, Present, and Future of Bug Tracking in the Generative AI Era | unsure: Vision paper for an AI bug-tracking framework; no concrete named system. | exclude: Forward-looking vision paper on bug tracking framework, no concrete named harness system described. | - |
| s2:9804dfa7a8051caf3aab28b7fdd18719961e4d36 | Exploring Generative AI Agents: Architecture, Applications, and Challe | unsure: Survey of generative agents like AutoGPT, BabyAGI; discusses existing systems. | unsure: Survey/review of generative AI agent architectures, discusses existing systems. | - |
| s2_snowball:bf14244f64db9a743944123558280294f7cd7e29 | LLM-Based Human-Agent Collaboration and Interaction Systems: A Survey | unsure: Survey of human-agent collaboration systems; discusses existing systems. | unsure: Survey of human-agent collaboration systems, no single named harness. | - |
| arxiv:2607.22319 | Towards Trustworthy and Cost-Efficient Data Integration: From Naïve RA | exclude: Vision paper tracing RAG evolution, no single named system described. | unsure: Vision and survey paper tracing RAG through to agentic RAG for data integration. It names no system and discus | - |
| arxiv:2511.17671 | MURMUR: Using cross-user chatter to break collaborative language agent | unsure: MURMUR attack framework evaluating existing multi-user agents; evaluates systems, goes to full text. | unsure: Duplicate of MURMUR, evaluates existing multi-user agents rather than describing new harness. | - |
| arxiv:2505.04651 | Scientific Hypothesis Generation and Validation: Methods, Datasets, an | unsure: Survey of LLM hypothesis generation approaches; discusses existing systems. | exclude: Survey of hypothesis generation methods, no single named harness system. | - |
| arxiv:2602.16943 | Mind the GAP: Text Safety Does Not Transfer to Tool-Call Safety in LLM | unsure: Evaluates existing agent systems for safety; no specific harness named as candidate. | unsure: GAP benchmark that evaluates tool-call safety of existing models; no new harness is evident. | - |
| s2:e131a11ad907023f655f22a4fae2b2a6f2db96f7 | Reasoning and Planning with Large Language Models in Code Development | unsure: Survey/tutorial on LLMs for code development; discusses existing systems only. | unsure: Survey discussing LLM code development techniques, no single named harness system described. | - |
| openalex:W7160334287 | Tiered Detection of Multi-Agent LLM Failures: An Empirical Calibration | exclude: Failure detection calibration pipeline, not a system running a model in a loop. | unsure: Failure-detection pipeline scoring multi-agent traces on benchmarks; evaluates existing systems rather than wr | - |
| arxiv:2608.30300 | Update from Hell: Can Coding Agents Survive Hidden Breakage in Depende | unsure: Benchmark evaluating multiple coding agent harnesses, no single named system described. | unsure: DEPBENCH benchmark evaluating existing coding agent harnesses; evaluation-only record, route to full text. | - |
| acl:wang-etal-2026-action | Action Boundary Blindness: When LLM Agents Cannot Tell Where One Actio | unsure: Empirical analysis of agents' failure modes across benchmarks; evaluates existing systems. | unsure: Evaluation study of existing agents' failure modes, no new harness described. | - |
| arxiv:2604.00026 | "Who Am I, and Who Else Is Here?" Behavioral Differentiation Without R | unsure: Experimental platform for multi-LLM discussions; conversation only, so no tool actions are evident. | exclude: Experimental platform studying LLM behavioral differentiation, not a harness that executes actions. | - |
| arxiv:2505.07078 | Can LLM-based Financial Investing Strategies Outperform the Market in  | unsure: FINSABER backtesting framework evaluating existing LLM strategies; evaluation record. | exclude: FINSABER is a backtesting evaluation framework for existing strategies, not a harness system itself. | - |
| arxiv:2606.15017 | Are Online Skill and Memory Modules Always Worth Their Tokens? A Budge | unsure: Budget-constrained comparison of existing web agent augmentations; evaluation study. | unsure: Evaluates existing memory/skill modules against baselines, no new harness system described. | - |

## R4b rule includes (random 15 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| s2_snowball:1c259361caa85c2d95a7d04e5e42fa98693da85b | Large Language Models as Evolutionary Optimizers | unsure: LMEA iterative LLM crossover with external evaluation; optimizer loop rather than tool-using agent, borderline | include: LMEA iteratively instructs LLM in evolutionary loop selecting/evaluating solutions across generations. | - |
| s2:ff31741b3fd43a48ae9835636693b90013d04cc4 | A Cognitive Multi-Agent System for Formula 1 Sports Analytics | unsure: AgentF1 multi-agent QA with planner and critic; external tool execution not stated. | include: Named AgentF1 multi-agent system with planner, executor, critic loop and tool use. | - |
| s2:04b96eb0b3e5be9a5a160e61dec462ca4d23a8f7 | D-RAM: A Dynamic Role-Allocation Mediator for Improving Token Efficien | unsure: Named LangGraph-based multi-agent mediator with iterative routing, but abstract never states tools or code exe | include: Named multi-agent system with dynamic routing, mediator intervention, and tool/graph execution loop. | - |
| arxiv:2511.20940 | Chatty-KG: A Multi-Agent AI System for On-Demand Conversational Questi | unsure: Chatty-KG generates SPARQL via agent pipeline; iterative loop with execution feedback not stated. | include: Multi-agent system generating and executing SPARQL queries against knowledge graphs iteratively. | - |
| arxiv:2506.17784 | AnyMAC: Cascading Flexible Multi-Agent Collaboration via Next-Agent Pr | unsure: Multi-agent communication framework; abstract doesn't mention tools or executed actions with feedback. | include: Named multi-agent system with sequential loop selecting next agent/context, actions executed and fed back. | - |
| arxiv:2601.10738 | CTHA: Constrained Temporal Hierarchical Architecture for Stable Multi- | include: CTHA is a named multi-time-scale agent architecture with inter-layer plans, policies and arbitration driving c | unsure: General architecture/framework, no specific named system with concrete loop described. | - |
| openalex:W7169827299 | Agentic AI in Enterprise Software Engineering: Multi-Agent Frameworks  | unsure: LangGraph/MCP multi-agent software engineering framework deployed in production, but no named system. | include: Multi-agent framework using LangGraph and MCP with deployment study, tool use and loop present. | - |
| github:chaitin/MonkeyCode | chaitin/MonkeyCode | unsure: AI coding platform with task management; README excerpt doesn't show agent loop details. | include: Named AI coding platform with task/model management implying tool-executing agent loop. | - |
| arxiv:2512.18202 | Sophia: A Persistent Agent Framework of Artificial Life | unsure: Sophia is a persistent-agent wrapper prototype, mostly conceptual; executed actions not clearly described. | include: Sophia is a persistent agent wrapper adding a continuous self-improvement loop onto an LLM stack with tasks. | - |
| arxiv:2606.11521 | Counterexample Guided Learning in the Large using Reasoning Agents | include: Learner LLM proposes regexes, external verifier returns counterexamples, with reflection and repair loops driv | unsure: Explores counterexample-guided and agentic reflection strategies but no single named harness system described. | - |
| arxiv:2605.19595 | A novel YOLO26-MoE optimized by an LLM agent for insulator fault detec | unsure: Detector paper; tool-augmented LLM agent for HPO only briefly mentioned. | include: Tool-augmented LLM agent coordinates hyperparameter optimization and training in a loop. | - |
| s2_snowball:8b2d6308af43aadb3c7ccdec9431be0a995b5579 | Agentic AI for Disease-Aware Adaptive Multi-Omics Embedding: A Proof o | unsure: Unnamed plan-act-verify agent; LLM use not explicit in abstract. | include: Agent plans, acts, and verifies in self-refining loop selecting normalization and embedding methods based on o | - |
| s2_snowball:9625ded46a11bdbefedc9d752854ecbb13fd7c09 | Iterating Toward Better Search: A Two-Agent Simulation Framework for E | unsure: Unnamed two-agent simulation framework evaluating responder architectures against a real search API; primarily | include: Two-agent simulation with buyer and responder integrated with real search API, iterative conversation loop. | - |
| s2:b44f55195d6f5024f174546698ddd9fffee8f043 | AI Agents: Agent GPT | unsure: Describes existing AgentGPT system generally; discussion rather than new system. | include: Agent GPT named system, plans and executes multi-step tasks using tools/APIs iteratively. | - |
| arxiv:2508.14123 | AI Agents for Photonic Integrated Circuit Design Automation | unsure: PhIDO multi-agent PIC design framework; iterative tool-execution loop not explicit in abstract. | include: Named PhIDO multi-agent framework converts requests to layouts via LLM loop. | - |

## T5 majority excludes (random 15 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| s2_snowball:7db7fc58c75e158d3aa231cec1eec1ba2ed74110 | Actions Speak Louder than Prompts: A Large-Scale Study of LLMs for Gra | unsure: Empirical study comparing LLM graph interaction modes; evaluation-only. | exclude: Empirical study comparing LLM-graph interaction modes, not a named harness system. | exclude (high): Large-scale evaluation study comparing LLM-graph interaction modes; it doesn't present a new named system. |
| arxiv:2509.06436 | Tree of Agents: Improving Long-Context Capabilities of Large Language  | exclude: Agents read context chunks and exchange information; no executed tool actions. | unsure: Multi-agent reasoning framework unclear if actions are executed outside model with feedback. | exclude (medium): Multi-agent reasoning framework processes text chunks; no evidence of executed external tool actions. |
| arxiv:2603.13791 | DeceptGuard :A Constitutional Oversight Framework For Detecting Decept | unsure: DeceptGuard monitors agent trajectories in sandboxed environments; monitors observe rather than run the loop,  | exclude: DeceptGuard is a monitoring framework observing agents, not itself a system that runs a model in a loop. | exclude (high): Deception monitors and benchmark observing agent trajectories; monitoring component, not a system running the  |
| arxiv:2607.04240 | Biological Motifs for Agentic Control | unsure: Theoretical design-pattern paper with a reference implementation; unclear whether a named harness running a mo | exclude: Theoretical/conceptual paper on biological motifs, no named implemented harness system. | exclude (medium): Theoretical design-pattern/formal paper mapping biological motifs; no named running harness system. |
| arxiv:2601.19311 | Balancing Sustainability And Performance: The Role Of Small-Scale LLMs | unsure: Energy comparison of model sizes in multi-agent system; evaluation of existing systems. | exclude: Comparative study of model scales' energy use, no named harness system. | exclude (high): Study comparing the energy use of different model sizes; evaluation only, no named system. |
| arxiv:2606.06708 | Signal-Driven Observation for Long-Horizon Web Agents | exclude: Proposes conceptual observation strategy, no named implemented system with loop. | unsure: Position paper proposing Signal-Driven Observation for web agents; observation-layer proposal, and unclear whe | exclude (medium): Position paper proposing an observation strategy and outlining open problems. No implemented system is describ |
| s2_snowball:e78960d1984f01e4e7cea708c7eba948f118c5a3 | Evaluating LLM Trade-offs for Enterprise Automation: Lessons from Work | exclude: Fixed monolithic versus piecewise workflow-generation pipelines; stages chain model outputs, no call depends o | unsure: Evaluates workflow generation pipelines; unclear if a named looping harness system is described. | exclude (medium): Fixed workflow-generation pipelines without action-feedback loop. |
| s2_snowball:8c5d0df99e0b2e65053bf56b0a783dbe522b76be | Shopfloor layout generation method based on large language models | unsure: Think-generate-evaluate prompt loop for layouts; executed actions unclear. | exclude: Prompt engineering method for layout generation, no named system with executed actions. | exclude (medium): A prompt-engineering generation cycle; no external actions are executed. |
| s2_snowball:7ca88aef24fff1998358422f8b1af56045ea9a33 | Contextual Prompt Enabler for Mental Health (CPEMH): An Agent-Based LL | exclude: Prompt evaluation and selection pipeline for depression screening; no model-selected tool actions fed back. | unsure: Agent-based framework for prompt evaluation, unclear if actions executed in loop. | exclude (medium): Prompt evaluation/selection pipeline for classification; no model-chosen executed actions. |
| arxiv:2406.06461 | Reasoning in Token Economies: Budget-Aware Evaluation of LLM Reasoning | unsure: Budget-aware evaluation of existing reasoning strategies including Reflexion; evaluation-only record. | exclude: Evaluation framework analyzing compute budget, not a named harness system. | exclude (high): Evaluation of existing reasoning strategies under compute budgets; evaluation-only. |
| openreview:Bp2axGAs18 | On the Resilience of Multi-Agent Systems with Malicious Agents | unsure: Earlier version of resilience study of existing multi-agent systems; likely duplicate, evaluates existing syst | exclude: Duplicate resilience study of existing systems, no new harness named. | exclude (medium): Resilience evaluation of existing multi-agent structures; no new harness. |
| openalex:W7150060738 | Agents | exclude: No abstract and generic title; no named system. | unsure: Empty abstract, cannot determine system or loop details. | exclude (medium): Generic book chapter titled 'Agents' with no abstract; no named system. |
| s2_snowball:4040d930de985c159306547cf2059cec9c1e7c5a | Persona Dynamics: Unveiling the Impact of Personality Traits on Agents | unsure: PANDA text-game agents with trained policy; unclear if LLM-based harness. | exclude: Personality-conditioned RL policy agents in text games, no described tool-using loop harness. | exclude (medium): Personality integrated into policy learning; training-focused, not LLM harness. |
| arxiv:2608.03585 | From Social Coding to Agentic Coding: Productivity and Relational Reco | unsure: Simulation study measuring coding-agent effects on GitHub communities; simulation harness unnamed and the pape | exclude: Simulation study of generic coding agents' social effects, no specific harness system described. | exclude (medium): Social simulation study of coding-agent effects on communities; analysis only. |
| arxiv:2603.24579 | MARCH: Multi-Agent Reinforced Self-Check for LLM Hallucination | unsure: Duplicate MARCH record; fixed three-agent verification pipeline with MARL training, loop dependence on execute | exclude: Same MARCH pipeline; no external action execution loop, just claim verification against retrieved text. | exclude (medium): Duplicate MARCH record: a fixed verification pipeline with MARL training and no executed-action loop. |

## T5 tiebreak excludes, both priors unsure (random 15 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| arxiv:2608.00101 | Agentic Coding in the Wild: Characterizing GitHub Copilot Traces at Pr | unsure: Workload characterization of Copilot traces; studies existing systems. | unsure: Characterizes production traces of existing coding agents; no new harness system described, discussion of exis | exclude (high): Characterization of production Copilot traces; evaluation of existing systems. |
| openalex:W7104377404 | AIGATE: The OS for AI Civilization - A Fractal Governance Architecture | unsure: Conceptual governance OS architecture; unclear implemented agent loop. | unsure: Governance architecture description unclear whether it implements a concrete model loop. | exclude (medium): Conceptual governance OS architecture; no concrete model-action loop described. |
| github:VILA-Lab/Dive-into-Claude-Code | VILA-Lab/Dive-into-Claude-Code | unsure: Analysis of existing system Claude Code, not introducing a new harness itself. | unsure: Source-level analysis of an existing system (Claude Code) and a design-space discussion. The protocol routes t | exclude (high): Analysis of existing system Claude Code; no new harness. |
| openreview:b1vVm6Ldrd | Entering Real Social World! Benchmarking the Theory of Mind and Social | unsure: EgoSocialArena evaluation benchmark with interactive environments; may include reference agent. | unsure: Benchmark for ToM/socialization; may include reference agent implementation unclear from abstract. | exclude (medium): EgoSocialArena is an evaluation benchmark; no reference harness indicated. |
| s2_snowball:ab4fff7e381bc988304571ce1ad3d225f4e671fc | SastBench: A Benchmark for Testing Agentic SAST Triage | unsure: Benchmark for agentic SAST triage, may include reference harness agent. | unsure: Agent-agnostic benchmark for SAST triage agents that evaluates several agents. Unclear whether it ships a refe | exclude (medium): Agent-agnostic benchmark; no reference harness introduced. |
| arxiv:2603.07191 | Governance Architecture for Autonomous Agent Systems: Threats, Framewo | unsure: Layered Governance Architecture adds sandboxing, intent verification and auditing around OpenClaw; unclear whe | unsure: Proposes governance layers applied to existing OpenClaw framework; unclear if full harness loop described. | exclude (medium): Governance layers (sandbox, intent judge, audit) added to OpenClaw; guardrail components evaluated on tool-cal |
| s2:dfd9cb73721e1d1650ae987a1b9ad63aaf59f05a | EASE Configuration Facilitates A Reproducible Science of LLM Social Si | unsure: EASE is a modular configuration standard and SiliSocS sandbox for social simulation; unclear whether a default | unsure: Modular simulation framework SiliSocS; unclear if it satisfies loop/action clauses as harness. | exclude (low): Social simulation framework; agents converse, no task-completing tool loop. |
| s2_snowball:5feb11d2b43139d1fee9720d61702aa36de733fd | Unlocking Complex Visual Generation via Closed-Loop Verified Reasoning | unsure: Closed-loop visual generation framework; unclear if it constitutes an LLM agent harness. | unsure: CLVR couples VLM planning with diffusion generation and verification; unclear if generation is an executed ext | exclude (medium): Model-training contribution (data engine, PPRL, weight merge) for text-to-image generation; not an agent harne |
| github:microsoft/agent-framework-go | microsoft/agent-framework-go | unsure: Go port of agent framework; shipped default agent unclear; possible duplicate. | unsure: Go port of framework; unclear if default agent shipped meets harness criteria. | exclude (medium): Go port of Microsoft Agent Framework; duplicate of the canonical repository. |
| arxiv:2406.03007 | BadAgent: Inserting and Activating Backdoor Attacks in LLM Agents | unsure: Backdoor attack on LLM agents; evaluates agents, no new harness. | unsure: BadAgent studies backdoors in existing LLM agents, evaluates rather than proposes new harness. | exclude (medium): Backdoor attack study via fine-tuning; no new harness. |
| openalex:W7115682614 | [V] Use of an AI Peer Review Panel to Assess Clarity, Novelty, and Imp | unsure: Multi-agent peer review panel with literature database lookup; unclear whether the model selects executed acti | unsure: Multi-agent peer review panel; unclear tool execution loop with environment. | exclude (low): Zero-shot prompted role agents in a fixed review pipeline; no model-selected executed actions with feedback de |
| s2_snowball:b7c19759ae7ab39465b056c51919c70035f7caf2 | How Agents Represent Humans: Human-Directed Stereotypes in an Open Age | unsure: Discourse/bias analysis of posts on the existing Moltbook agent platform; studies an existing system rather th | unsure: Studies agent social behavior on a platform, unclear harness description. | exclude (high): Discourse analysis of posts on existing Moltbook platform; no harness described. |
| s2:7784ba20be5ab819fb3a81d08c7443ee290c594a | Data Space and LLM Enabled Decision-Making Support System: An Applicat | unsure: Decision-support framework with LLM and AI-Agent; unnamed system, loop and tools unclear. | unsure: Framework integrates Data Space and AI-Agent but loop/action details unclear from abstract. | exclude (low): Unnamed decision-support framework design; no loop, tool execution or codable detail indicated. |
| s2_snowball:8b02d8734c5fa67be04398f8fa23407eeeae4293 | Repurposing Synthetic Data for Fine-grained Search Agent Supervision | unsure: E-GRPO training method for search agents; the harness may not be described. | unsure: Training method for search agents; unclear if new harness system is named/described. | exclude (high): E-GRPO reward and training method for search agents; training only. |
| arxiv:2506.11425 | Agent-RLVR: Training Software Engineering Agents via Guidance and Envi | unsure: Agent-RLVR RL training for SWE agents; harness guidance mechanism may matter, training-focused. | unsure: Agent-RLVR is primarily a training method; harness description for the agent itself unclear from abstract. | exclude (medium): Agent-RLVR is an RL training method for SWE agents; training-focused. |

## T5 majority includes (random 10 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| arxiv:2508.13413 | Large Language Models as Visualization Agents for Immersive Binary Rev | include: LLM agent queries binary analysis tools and generates VR visualizations within RE platform. | unsure: LLM agent querying tools and generating visualizations in VR; unclear loop detail. | include (medium): LLM agent queries binary analysis tools and generates visualizations; system architecture described. |
| arxiv:2505.08844 | CellTypeAgent: Trustworthy cell type annotation with Large Language Mo | unsure: CellTypeAgent LLM with database verification; multi-step loop unclear. | include: LLM-agent integrates database verification, action-feedback loop for cell type annotation. | include (low): Named LLM agent querying databases for verification; plausible action-feedback loop. |
| arxiv:2510.08578 | AgenticAD: A Specialized Multiagent System Framework for Holistic Alzh | unsure: Architectural blueprint for AD multi-agent system; unclear if implemented with iterative tool loop. | include: Named multi-agent system AgenticAD with eight specialized interoperable agents using tools and RAG. | include (low): Named eight-agent AgenticAD system with LLMs, orchestration, web scraping and database tools; plausibly codabl |
| arxiv:2505.19197 | Structuring the Unstructured: A Multi-Agent System for Extracting and  | unsure: Extraction and Text-to-SQL agents; unclear whether SQL execution results feed back into an iterative loop. | include: Multi-agent system with Extraction and Text-to-SQL agents executing operations, feeding results back. | include (low): The agents execute generated SQL and verify extracted results; a plausible loop with executed operations. |
| arxiv:2602.03045 | Clarify Before You Draw: Proactive Agents for Robust Text-to-CAD Gener | unsure: ProCAD clarifying and coding agents; whether CadQuery execution feedback loops back unclear. | include: Named ProCAD agent framework clarifies specs then synthesizes and executes CadQuery code. | include (medium): ProCAD: named multi-agent system that interacts with the user and produces executable CadQuery code; public re |
| arxiv:2601.10865 | Multi-Agent Taint Specification Extraction for Vulnerability Detection | include: SemTaint named system combining LLM with static analysis tools, iterative call resolution and vulnerability de | unsure: SemTaint: static analysis calls the LLM to resolve call edges and classify sources/sinks; unclear whether the  | include (low): SemTaint, a named multi-agent system combining the LLM with static analysis and CodeQL tools; full text is nee |
| arxiv:2408.07199 | Agent Q: Advanced Reasoning and Learning for Autonomous AI Agents | unsure: Agent Q combines MCTS with DPO fine-tuning for web agents; training-heavy, harness may be described. | include: Agent Q framework interacts with WebShop environment, executing actions with feedback loop. | include (medium): Agent Q runs MCTS with self-critique on web environments at inference, beyond training alone. |
| s2_snowball:bc0a56f3bcc69ea7e1bbea83318726965e066580 | CARE: Privacy-Compliant Agentic Reasoning with Evidence Discordance | unsure: Multi-stage agentic reasoning with evidence acquisition; loop and tool execution unclear. | include: Named multi-stage agentic pipeline CARE with LLM guidance and local LLM evidence acquisition loop. | include (low): Named agentic framework CARE where local LLM performs evidence acquisition from EHR; plausible action loop. |
| s2_snowball:6fb4d7e5f12826a6d602046af94acea0457176b8 | Agentic Simheuristic: Integrating Generative AI and Simheuristic for a | unsure: LLM coordinates simheuristic agents selecting solutions; unclear whether a tool-executing loop with feedback e | include: Named agentic simheuristic framework using LLM to iteratively select and refine solutions via tools. | include (low): LLM coordinator iteratively selects solutions for simulation-backed search agents, with results fed back. |
| s2_snowball:5896d0fca88c3bce680b5e90ea927ddefb8c07dc | Empowering Economic Simulation for Massively Multiplayer Online Games  | unsure: LLM agents with memory in MMO economy simulation; system unnamed, loop details unclear. | include: Named LLM-driven agent framework with perception, memory, reasoning loop for MMO economy simulation. | include (medium): LLM-driven agents with perception, memory and reasoning acting over time in an MMO economy simulation environm |

## T5 tiebreak includes, both priors unsure (random 10 for audit)

| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |
|---|---|---|---|---|
| arxiv:2601.04203 | FronTalk: Benchmarking Front-End Development as Conversational Code Ge | unsure: Benchmark with AceCoder baseline using web agent critique; reference agent may be harness. | unsure: Benchmark FronTalk with AceCoder baseline method; unclear if AceCoder is a full harness. | include (low): Benchmark ships AceCoder baseline using autonomous web agent critique; reference agent may be codable. |
| s2_snowball:19fe0361d5000ab2c24461a2845b7ff6e918c809 | SAGE: Scalable Agentic 3D Scene Generation for Embodied AI | unsure: Agentic scene generation for embodied AI training; unclear if embodied robotics exclusion applies to this non- | unsure: Agentic tool-using scene generator with iterative critic loop; unclear whether embodied-AI scene generation fo | include (medium): Agent iteratively selects generator/critic tools in simulation software; not physical robotics. |
| openreview:v4VSoKwU5w | LinguaMate: Language‑Guided Metamaterial Discovery via Symbolic-Driven | unsure: LinguaMate multi-agent latent optimization; unclear whether LLM-chosen operations are executed with results fe | unsure: Multi-agent optimization framework for metamaterial discovery; unclear loop/action structure from abstract. | include (low): Named inference-time multi-agent optimization framework whose latent optimization is likely executed in a feed |
| arxiv:2412.01303 | RL2: Reinforce Large Language Model to Assist Safe Reinforcement Learn | unsure: RL2 LLM iteratively refines penalty functions from RL training feedback; borderline action execution loop. | unsure: RL2 mechanism refines LLM-generated functions via multi-round dialogue, unclear if actions executed and fed ba | include (low): LLM agent iteratively refines penalty functions using RL training/test feedback over multiple rounds. |
| arxiv:2510.27598 | InnovatorBench: Evaluating Agents' Ability to Conduct Innovative LLM R | unsure: Benchmark with ResearchGym and a lightweight ReAct reference agent; decided at full text. | unsure: Benchmark platform pairing with ReAct baseline agent; reference harness may or may not be canonical system. | include (medium): Benchmark ships a reference lightweight ReAct agent operating in ResearchGym with rich action spaces. |
| arxiv:2411.02305 | CRMArena: Understanding the Capacity of LLM Agents to Perform Professi | unsure: CRMArena benchmark evaluating ReAct and function-calling agents; reference agent needs full-text check. | unsure: Benchmark for CRM tasks, may include reference agent harness, unclear from abstract. | include (low): CRMArena benchmark evaluates ReAct and function-calling reference agents in a realistic CRM environment; refer |
| openalex:W4413912948 | Agentic information fusion for urban building energy services using a  | unsure: No abstract; multi-agent AI system for building energy, loop and tools undeterminable. | unsure: Named multi-agent AI system but abstract missing, unclear loop/tool details. | include (low): No abstract. The title names a multi-agent AI system for energy services, so it is plausibly a harness. |
| arxiv:2505.17012 | SpatialScore: Towards Comprehensive Evaluation for Spatial Intelligenc | unsure: Benchmark paper that also offers SpatialAgent with tools and ReAct; the agent may qualify. | unsure: Primarily a benchmark with an included SpatialAgent multi-agent tool system, needs full-text check. | include (medium): SpatialAgent: multi-agent system with 12 tools supporting ReAct and Plan-Execute loops. |
| arxiv:2607.22400 | A Self-Calibrating Agentic AI Framework for Autonomous Edge Resource A | unsure: Self-calibrating agentic framework for edge profiling; tool loop is claimed but not described concretely. | unsure: Self-calibrating agentic framework for edge allocation; loop/action structure not clearly described. | include (low): Proposes an agentic framework with tool execution and self-calibration loop for edge profiling. |
| arxiv:2410.19923 | Language Agents Meet Causality -- Bridging LLMs and Causal World Model | unsure: LLM queries causal world model simulator for planning; loop and executed actions unclear from abstract. | unsure: Causal world model framework integrated with LLM, unclear named harness system. | include (low): LLM iteratively queries and interacts with causal world-model simulator for planning; plausible action loop. |
