# Full-text screening report

Generated 2026-09-20 18:09 UTC by `scripts/validate_screening.py`.
Scope: 9967 records (data/screening/fulltext_queue.csv); pass-1 rows 8435, pass-2 rows 3075, final rows 8435, systems 6172.

## 1. Decisions

Model(s): {'claude-opus-5': 4123, 'claude-sonnet-5': 4180, 'claude-opus-4-8': 56}; prompt(s): {'ft-v2-2026-09-18': 8435}.

- Pass-1 include rate, all records in scope: 7085/8435 = 84.0% [95% CI 83.2%, 84.8%]
- Pass-1 include rate, records with full text (LLM read): 7085/8359 = 84.8% [95% CI 84.0%, 85.5%]
- not_retrievable (index says not ok; no LLM call): 76
- Pending (in scope, no pass-1 row yet): 1532
- Final (after pass 2 and the registry): {'exclude': 2263, 'include': 6172}; systems in registry: 6172

Include rate by pilot stratum (pass 1):

| stratum | n | not retrievable | include / all | include / with full text |
|---|---|---|---|---|
| known_system | 15 | 0 | 15/15 = 100.0% [95% CI 79.6%, 100.0%] | 15/15 = 100.0% [95% CI 79.6%, 100.0%] |
| metadata_mismatch | 60 | 32 | 13/60 = 21.7% [95% CI 13.1%, 33.6%] | 13/28 = 46.4% [95% CI 29.5%, 64.2%] |
| random | 250 | 36 | 172/250 = 68.8% [95% CI 62.8%, 74.2%] | 172/214 = 80.4% [95% CI 74.5%, 85.1%] |

Include rate by source (pass 1):

| source | n | not retrievable | include rate (all) |
|---|---|---|---|
| arxiv | 4352 | 0 | 3750/4352 = 86.2% [95% CI 85.1%, 87.2%] |
| s2_snowball | 2077 | 10 | 1846/2077 = 88.9% [95% CI 87.5%, 90.2%] |
| openalex | 473 | 19 | 282/473 = 59.6% [95% CI 55.1%, 63.9%] |
| s2 | 458 | 46 | 313/458 = 68.3% [95% CI 63.9%, 72.4%] |
| github | 451 | 0 | 401/451 = 88.9% [95% CI 85.7%, 91.5%] |
| acl | 164 | 0 | 135/164 = 82.3% [95% CI 75.8%, 87.4%] |
| openreview | 142 | 0 | 122/142 = 85.9% [95% CI 79.2%, 90.7%] |
| leaderboard | 126 | 1 | 70/126 = 55.6% [95% CI 46.8%, 63.9%] |
| awesome | 125 | 0 | 111/125 = 88.8% [95% CI 82.1%, 93.2%] |
| grey | 45 | 0 | 45/45 = 100.0% [95% CI 92.1%, 100.0%] |
| survey_refs | 22 | 0 | 10/22 = 45.5% [95% CI 26.9%, 65.3%] |

## 2. Exclusion reasons and deciding steps (pass 1)

| exclusion_code | sub-reason | n | % of excludes |
|---|---|---|---|
| out_of_scope | no_actions | 346 | 25.6% |
| out_of_scope | no_loop | 229 | 17.0% |
| out_of_scope | component_only | 158 | 11.7% |
| no_harness_description | no_artifact | 136 | 10.1% |
| out_of_scope | training_only | 114 | 8.4% |
| out_of_scope | benchmark_only | 109 | 8.1% |
| not_retrievable | - | 76 | 5.6% |
| duplicate_system | evaluation_only | 62 | 4.6% |
| out_of_scope | embodied | 42 | 3.1% |
| out_of_scope | framework_no_default | 28 | 2.1% |
| duplicate_system | survey | 19 | 1.4% |
| no_harness_description | other | 17 | 1.3% |
| other | language | 8 | 0.6% |
| no_harness_description | - | 2 | 0.1% |
| out_of_scope | date | 1 | 0.1% |
| no_harness_description | codability | 1 | 0.1% |
| out_of_scope | other | 1 | 0.1% |
| duplicate_system | other | 1 | 0.1% |

| deciding step | n |
|---|---|
| - | 73 |
| 1 | 53 |
| 2 | 344 |
| 3 | 346 |
| 5 | 154 |
| 6 | 28 |
| 7 | 105 |
| 8 | 43 |
| 9 | 8 |
| 10 | 83 |
| 11 | 113 |
| 12 | 7085 |

Confidence: exclude/high: 111, exclude/low: 118, exclude/medium: 1045, include/high: 652, include/low: 493, include/medium: 5940

## 3. Codability (criterion b; count of the 38 dimensions the evidence bundle supports)

Amendment 5: the count is recorded at screening and enforced at coding; step 7 only excludes a record with no admissible artifact at all (`no_harness_description` / `no_artifact`).

| codable_count | all LLM-read records | records reaching step 7 | pass-1 includes |
|---|---|---|---|
| 0-4 | 450 | 103 | 21 |
| 5-9 | 1061 | 526 | 452 |
| 10-14 | 2591 | 2440 | 2387 |
| 15-18 | 2140 | 2119 | 2110 |
| 19-22 | 1373 | 1372 | 1371 |
| 23-26 | 547 | 547 | 547 |
| 27-30 | 169 | 169 | 169 |
| 31-38 | 28 | 28 | 28 |

Includes: median codable_count 16, min 3, max 35; exact distribution {3: 6, 4: 15, 5: 44, 6: 46, 7: 91, 8: 101, 9: 170, 10: 220, 11: 389, 12: 494, 13: 610, 14: 674, 15: 635, 16: 549, 17: 474, 18: 452, 19: 496, 20: 338, 21: 307, 22: 230, 23: 190, 24: 152, 25: 116, 26: 89, 27: 67, 28: 49, 29: 34, 30: 19, 31: 10, 32: 11, 33: 5, 34: 1, 35: 1}.
Records reaching step 7: 7304; excluded there for a missing artifact: 99.
codability_flag (all LLM-read records): borderline 4029, fail 2246, pass 2084; among pass-1 includes: borderline 3920, fail 1082, pass 2083.
Repository evidence in the bundle (Amendment 5): 2460/8359 = 29.4% [95% CI 28.5%, 30.4%]; median codable_count 19 with a repository vs 13 without; include rate 2260/2460 = 91.9% [95% CI 90.7%, 92.9%] vs 4825/5899 = 81.8% [95% CI 80.8%, 82.8%].
Layer coverage among includes: A 6673/7085, B 6031/7085, C 7025/7085, D 6058/7085, E 5057/7085, F 5230/7085, G 2730/7085, H 2666/7085.

## 4. Evidence quality and systematic checks

- Quotes found verbatim in the excerpt the model saw (case/punctuation-insensitive): 58426/60881 = 96.0% [95% CI 95.8%, 96.1%]
- Post-hoc flags (pass 1): {'include_below_codability_rule': 5002, 'quote_not_in_excerpt': 1938, 'no_evidence_for_deciding_step': 1309, 'layers_normalized': 181, 'codability_flag_mismatch': 103, 'corrective_retry': 64, 'long_quote': 22, 'include_without_system_name': 19, 'count_mismatch': 6}
- Excerpt words: median 3989, max 4151; full-text words: median 5270, sent whole (<= cap): 1853
- Document title seen differs from the candidate title (fuzzy < 80): 156 records (arxiv:2311.10776: 'Chemist-X: Large Language Model-Powered Agent for Recommendi'; arxiv:2503.15937: 'V-Droid: Advancing Mobile GUI Agent Through Generative Verif'; arxiv:2504.11788: 'Get Stuck at Errors Rollback by Values'; arxiv:2506.00714: 'RFCAUDIT: AI Agent for Auditing Protocol Implementations Aga'; arxiv:2506.10954: 'SWE Data Construction, Automatically! (SWE-Factory)'; arxiv:2507.14800: 'Large Language Model as An Operator: An Experience-Driven So'; arxiv:2508.20996: 'CHATTHERO: A LANGUAGE AGENT FOR RECOVERY SUPPORT'; arxiv:2510.08952: 'RETHINKING GRAPH STRUCTURE LEARNING IN THE ERA OF LLMS'; arxiv:2602.15631: 'Meflex: Supporting Entrepreneurial Ideation Through Nonlinea'; arxiv:2603.03686: 'Scientific Discovery under Imperfect Evaluators: Diversity-A'; arxiv:2603.19896: 'Utility-Guided Orchestration for Cost-Efficient Tool-Augment'; arxiv:2605.17242: 'From Runnable Code to Shippable Applications: Test-Driven De' ...)

Full-text source used: {'arxiv_pdf': 6641, 'github_repo': 629, 'doi_landing_html': 406, 'openalex_oa_pdf': 235, 'acl_pdf': 170, 'openreview_pdf': 130, 'web_html': 125, 'landing_html': 18, 'doi_landing_pdf': 2, 's2_oa_pdf': 2, 'landing_pdf': 1}

## 5. Independent second reading (pass 1 vs pass 2)

Records read twice: 3075 (every pass-1 include plus a hash-based 10% of pass-1 LLM excludes).

|  | pass 2 include | pass 2 exclude |
|---|---|---|
| pass 1 include | 1403 | 670 |
| pass 1 exclude | 140 | 862 |

- Cohen's kappa (sample as drawn): 0.473; observed agreement 2265/3075 = 73.7% [95% CI 72.1%, 75.2%]
- Population-weighted (excludes weighted x10): kappa 0.471, agreement 82.9%
- Pass-1 includes confirmed by pass 2: 1403/2073 = 67.7% [95% CI 65.6%, 69.7%]
- Sampled pass-1 excludes confirmed by pass 2: 862/1002 = 86.0% [95% CI 83.7%, 88.0%]
- Same exclusion code among both-exclude pairs: 787/862 = 91.3% [95% CI 89.2%, 93.0%]; same deciding step: 658/862 = 76.3% [95% CI 73.4%, 79.1%]
- Same system name among both-include pairs (fuzzy >= 90): 1221/1403 = 87.0% [95% CI 85.2%, 88.7%]
- |codable_count pass 1 - pass 2|: median 3, mean 3.8, max 25

Disagreements:

| record | pass 1 | pass 2 | title seen |
|---|---|---|---|
| acl:arias-russi-etal-2025-uniandes | exclude out_of_scope s3 c7 | include  s12 c20 | Uniandes at TSAR 2025 Shared Task: Multi-Agent CEFR Text Simplificatio |
| acl:fan-etal-2025-llm | include  s12 c14 | exclude out_of_scope s2 c5 | An LLM-based Framework for Biomedical Terminology Normalization in Soc |
| acl:han-etal-2026-experience | include  s12 c14 | exclude out_of_scope s3 c14 | Experience-Driven Multi-Agent Optimization for Black-Box Jailbreak Att |
| acl:hashimoto-etal-2026-heard | include  s12 c11 | exclude out_of_scope s3 c4 | From Heard to Lived Opinions: Simulating Opinion Dynamics with Grounde |
| acl:leite-etal-2026-llm | include  s12 c15 | exclude out_of_scope s2 c8 | LLM-Based Multi-Agent System with Retrieval-Augmented Generation for M |
| acl:li-etal-2026-med | include  s12 c15 | exclude out_of_scope s2 c6 | Med-SRAF: A Multi-Agent Framework for Medical Reasoning via Semantic R |
| acl:li-etal-2026-multi | include  s12 c15 | exclude out_of_scope s3 c8 | Multi-Hop Knowledge Editing via Critic-Guided Multi-Agent Reasoning |
| acl:li-lu-2026-decoding | include  s12 c24 | exclude out_of_scope s2 c13 | Decoding the Market's Pulse: Context-Enriched Agentic Retrieval Augmen |
| acl:lu-etal-2026-covaph | include  s12 c16 | exclude out_of_scope s2 c8 | CoVaPh: A Vision-Language Multi-Agent Dialogue System for Tool-Augment |
| acl:lyn-graham-2025-translatex | include  s12 c9 | exclude out_of_scope s2 c5 | TransLaTeX: Exposing the Last-Mile Execution Gap in LLM-Agent for Scie |
| acl:mao-etal-2025-alympics | include  s12 c7 | exclude out_of_scope s3 c6 | ALYMPICS: LLM Agents Meet Game Theory |
| acl:mo-hu-2024-expertease | include  s12 c13 | exclude out_of_scope s2 c9 | ExpertEase: A Multi-Agent Framework for Grade-Specific Document Simpli |
| acl:raj-etal-2026-harpo | exclude out_of_scope s3 c5 | include  s12 c8 | HARPO: Hierarchical Agentic Reasoning for User-Aligned Conversational  |
| acl:sahu-etal-2025-occutriage | include  s12 c14 | exclude out_of_scope s3 c10 | OccuTriage: An AI Agent Orchestration Framework for Occupational Healt |
| acl:wang-etal-2025-inreact | include  s12 c16 | exclude out_of_scope s11 c9 | INREACT: An Inspire-Then-Reinforce Training Framework For Multimodal G |
| acl:wang-etal-2025-tunable | exclude out_of_scope s3 c9 | include  s12 c12 | Tunable LLM-based Proactive Recommendation Agent |
| acl:wang-etal-2026-ledger | include  s12 c13 | exclude out_of_scope s2 c8 | LEDGER: Scaling Agentic Document Editing with Dependency-aware Graph R |
| acl:wu-etal-2026-reflective | exclude out_of_scope s11 c8 | include  s12 c12 | Reflective RAG: Self-Evaluation Driven Strategy Optimization in Agenti |
| acl:ye-etal-2026-mobilecity | include  s12 c21 | exclude out_of_scope s3 c14 | MobileCity: An Efficient Framework for Large-Scale Urban Behavior Simu |
| acl:zhang-etal-2026-evohyper | include  s12 c14 | exclude out_of_scope s3 c9 | EvoHyper: Evolving Hypergraph Topologies for Unified Collaboration in  |
| acl:zhou-etal-2025-merit | include  s12 c7 | exclude out_of_scope s3 c7 | MERIT: Multi-Agent Collaboration for Unsupervised Time Series Represen |
| arxiv:2305.11854 | exclude out_of_scope s11 c3 | include  s12 c11 | Multimodal Web Navigation with Instruction-Finetuned Foundation Models |
| arxiv:2306.06070 | include  s12 c21 | exclude out_of_scope s2 c12 | MIND2WEB: Towards a Generalist Agent for the Web |
| arxiv:2306.16092 | include  s12 c15 | exclude out_of_scope s2 c7 | Chatlaw: A Multi-Agent Legal Assistant based on a Role-Aligned Mixture |
| arxiv:2307.08962 | exclude out_of_scope s3 c10 | include  s12 c10 | REX: Rapid Exploration and eXploitation for AI Agents |
| arxiv:2308.03688 | include  s12 c26 | exclude out_of_scope s2 c13 | AGENTBENCH: EVALUATING LLMS AS AGENTS |
| arxiv:2310.11954 | include  s12 c20 | exclude out_of_scope s2 c8 | MusicAgent: An AI Agent for Music Understanding and Generation with La |
| arxiv:2310.12821 | include  s12 c16 | exclude out_of_scope s3 c6 | GestureGPT: Toward Zero-Shot Free-Form Hand Gesture Understanding with |
| arxiv:2310.18940 | include  s12 c13 | exclude out_of_scope s2 c8 | Language Agents with Reinforcement Learning for Strategic Play in the  |
| arxiv:2310.19998 | include  s12 c14 | exclude duplicate_system s10 c7 | Generative retrieval-augmented ontologic graph and multi-agent strateg |
| arxiv:2311.10813 | exclude out_of_scope s8 c18 | include  s12 c13 | A Language Agent for Autonomous Driving |
| arxiv:2402.01622 | include  s12 c12 | exclude out_of_scope s2 c6 | TravelPlanner: A Benchmark for Real-World Planning with Language Agent |
| arxiv:2402.02172 | include  s12 c18 | exclude out_of_scope s3 c13 | CodeAgent: Autonomous Communicative Agents for Code Review |
| arxiv:2402.02330 | include  s12 c17 | exclude out_of_scope s2 c9 | Enhance Reasoning for Large Language Models in the Game Werewolf |
| arxiv:2402.09742 | include  s12 c21 | exclude out_of_scope s3 c8 | AI Hospital: Benchmarking Large Language Models in a Multi-agent Medic |
| arxiv:2402.11941 | include  s12 c20 | exclude out_of_scope s2 c10 | CoCo-Agent: A Comprehensive Cognitive MLLM Agent for Smartphone GUI Au |
| arxiv:2403.11905 | include  s12 c13 | exclude out_of_scope s2 c6 | TUR[K]INGBENCH: A Challenge Benchmark for Web Agents |
| arxiv:2403.14783 | include  s12 c11 | exclude out_of_scope s2 c6 | Multi-Agent VQA: Exploring Multi-Agent Foundation Models in Zero-Shot  |
| arxiv:2403.17804 | include  s12 c13 | exclude out_of_scope s3 c7 | Improving Text-to-Image Consistency via Automatic Prompt Optimization |
| arxiv:2404.09127 | include  s12 c25 | exclude out_of_scope s2 c11 | Confidence Calibration and Rationalization for LLMs via Multi-Agent De |
| arxiv:2404.11446 | include  s12 c20 | exclude out_of_scope s3 c11 | Open-Ended Wargames with Large Language Models |
| arxiv:2404.17662 | include  s12 c19 | exclude out_of_scope s3 c13 | PLAYER*: Enhancing LLM-based Multi-Agent Communication and Interaction |
| arxiv:2404.18081 | include  s12 c17 | exclude out_of_scope s3 c10 | ComposerX: Multi-Agent Symbolic Music Composition with LLMs |
| arxiv:2405.16887 | include  s12 c13 | exclude out_of_scope s2 c6 | A Large Language Model-based multi-agent manufacturing system for inte |
| arxiv:2405.19946 | include  s12 c9 | exclude out_of_scope s3 c5 | Learning to Discuss Strategically: A Case Study on One Night Ultimate  |
| arxiv:2406.05381 | include  s12 c12 | exclude out_of_scope s2 c6 | Experimenting with Multi-Agent Software Development: Towards a Unified |
| arxiv:2406.07275 | include  s12 c15 | exclude out_of_scope s2 c6 | DCA-Bench: A Benchmark for Dataset Curation Agents |
| arxiv:2406.18082 | include  s12 c11 | exclude out_of_scope s2 c7 | Octo-planner: On-device Language Model for Planner-Action Agents |
| arxiv:2407.12165 | include  s12 c14 | exclude out_of_scope s2 c5 | Building AI Agents for Autonomous Clouds: Challenges and Design Princi |
| arxiv:2407.15073 | include  s12 c14 | exclude out_of_scope s2 c6 | Multi-Agent Causal Discovery Using Large Language Models |
| arxiv:2407.17544 | include  s12 c25 | exclude out_of_scope s2 c13 | MathViz-E: A Case-study in Domain-Specialized Tool-Using Agents |
| arxiv:2408.11058 | include  s12 c8 | exclude out_of_scope s2 c8 | LLM Agents Improve Semantic Code Search |
| arxiv:2408.12680 | include  s12 c10 | exclude duplicate_system s10 c2 | Can LLMs Understand Social Norms in Autonomous Driving Games? |
| arxiv:2409.01575 | include  s12 c11 | exclude out_of_scope s3 c7 | An Implementation of Werewolf Agent That does not Truly Trust LLMs |
| arxiv:2409.02711 | include  s12 c13 | exclude out_of_scope s2 c8 | Creating a Gen-AI based Track and Trace Assistant MVP (SuperTracy) for |
| arxiv:2409.03440 | include  s12 c12 | exclude out_of_scope s2 c7 | Rx Strategist: Prescription Verification using LLM Agents System |
| arxiv:2409.04465 | include  s12 c9 | exclude out_of_scope s2 c4 | Here's Charlie! Realising the Semantic Web vision of Agents in the age |
| arxiv:2409.06351 | include  s12 c12 | exclude out_of_scope s2 c8 | MAGDA: Multi-agent guideline-driven diagnostic assistance |
| arxiv:2409.12089 | include  s12 c19 | exclude duplicate_system s10 c5 | The Impact of Element Ordering on LM Agent Performance |
| arxiv:2410.04360 | include  s12 c19 | exclude out_of_scope s3 c10 | GenSim: A General Social Simulation Platform with Large Language Model |
| arxiv:2410.08345 | include  s12 c18 | exclude out_of_scope s3 c7 | Large Legislative Models: Towards Efficient AI Policymaking in Economi |
| arxiv:2410.09403 | include  s12 c18 | exclude out_of_scope s3 c7 | Many Heads Are Better Than One: Improved Scientific Idea Generation by |
| arxiv:2410.14368 | exclude out_of_scope s8 c14 | include  s12 c13 | CoMAL: Collaborative Multi-Agent Large Language Models for Mixed-Auton |
| arxiv:2410.15665 | include  s12 c6 | exclude duplicate_system s10 c2 | Long Term Memory: The Foundation of AI Self-Evolution |
| arxiv:2410.17236 | include  s12 c12 | exclude out_of_scope s11 c4 | Large Language Models Empowered Personalized Web Agents |
| arxiv:2410.19855 | exclude no_harness_description s1 c4 | include  s12 c11 | Personalized Recommendation Systems using Multimodal, Autonomous, Mult |
| arxiv:2410.22552 | include  s12 c10 | exclude out_of_scope s2 c8 | Auto-Intent: Automated Intent Discovery and Self-Exploration for Large |
| arxiv:2411.01643 | include  s12 c12 | exclude out_of_scope s5 c1 | EcoAct: Economic Agent Determines When to Register What Action |
| arxiv:2411.06264 | include  s12 c12 | exclude out_of_scope s2 c7 | GuidelineGuard: An Agentic Framework for Medical Note Evaluation with  |
| arxiv:2411.08063 | exclude out_of_scope s8 c7 | include  s12 c5 | MatPilot: an LLM-enabled AI Materials Scientist under the Framework of |
| arxiv:2411.13902 | include  s12 c20 | exclude out_of_scope s3 c9 | PIORS: Personalized Intelligent Outpatient Reception based on Large La |
| arxiv:2412.17259 | include  s12 c16 | exclude out_of_scope s2 c8 | LegalAgentBench: Evaluating LLM Agents in Legal Domain |
| arxiv:2412.18890 | include  s12 c18 | exclude out_of_scope s3 c10 | CoEvo: Continual Evolution of Symbolic Solutions Using Large Language  |
| arxiv:2412.20005 | exclude out_of_scope s3 c11 | include  s12 c14 | OneKE: A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction |
| arxiv:2501.04575 | include  s12 c17 | exclude out_of_scope s11 c16 | InfiGUIAgent: A Multimodal Generalist GUI Agent with Native Reasoning  |
| arxiv:2501.06695 | exclude out_of_scope s3 c4 | include  s12 c8 | DVM: Towards Controllable LLM Agents in Social Deduction Games |
| arxiv:2501.06706 | include  s12 c18 | exclude out_of_scope s2 c6 | AIOpsLab: A Holistic Framework to Evaluate AI Agents for Enabling Auto |
| arxiv:2501.14731 | include  s12 c9 | exclude no_harness_description s1 c6 | From Critique to Clarity: A Pathway to Faithful and Personalized Code  |
| arxiv:2502.00415 | include  s12 c14 | exclude out_of_scope s2 c10 | MarketSenseAI 2.0: Enhancing Stock Analysis through LLM Agents |
| arxiv:2502.00757 | include  s12 c10 | exclude out_of_scope s2 c8 | AgentBreeder: Mitigating the AI Safety Risks of Multi-Agent Scaffolds  |
| arxiv:2502.01630 | include  s12 c11 | exclude out_of_scope s2 c8 | TReMu: Towards Neuro-Symbolic Temporal Reasoning for LLM-Agents with M |
| arxiv:2502.09156 | exclude out_of_scope s3 c6 | include  s12 c10 | Improving TCM Question Answering through Tree-Organized Self-Reflectiv |
| arxiv:2502.09596 | include  s12 c17 | exclude out_of_scope s2 c7 | KIMAs: A Configurable Knowledge Integrated Multi-Agent System |
| arxiv:2502.11435 | include  s12 c13 | exclude out_of_scope s11 c3 | SMART: Self-Aware Agent for Tool Overuse Mitigation |
| arxiv:2502.17506 | include  s12 c19 | exclude out_of_scope s2 c15 | RAG-Enhanced Collaborative LLM Agents for Drug Discovery |
| arxiv:2503.00751 | include  s12 c13 | exclude out_of_scope s3 c8 | RAPID: Efficient Retrieval-Augmented Long Text Generation with Writing |
| arxiv:2503.03800 | include  s12 c13 | exclude out_of_scope s2 c10 | MULTI-AGENT SYSTEMS POWERED BY LARGE LANGUAGE MODELS: APPLICATIONS IN  |
| arxiv:2503.07675 | exclude out_of_scope s3 c12 | include  s12 c11 | DynTaskMAS: A Dynamic Task Graph-driven Framework for Asynchronous and |
| arxiv:2503.08199 | exclude out_of_scope s8 c10 | include  s12 c7 | A Cascading Cooperative Multi-agent Framework for On-ramp Merging Cont |
| arxiv:2503.11444 | include  s12 c19 | exclude out_of_scope s6 c14 | Cerebrum (AIOS SDK): A Platform for Agent Development, Deployment, Dis |
| arxiv:2503.14432 | include  s12 c12 | exclude out_of_scope s2 c4 | PLAY2PROMPT: Zero-shot Tool Instruction Optimization for LLM Agents vi |
| arxiv:2503.16463 | exclude out_of_scope s3 c7 | include  s12 c9 | Improving Interactive Diagnostic Ability of a Large Language Model Age |
| arxiv:2503.17671 | include  s12 c15 | exclude out_of_scope s2 c12 | ComfyGPT: A Self-Optimizing Multi-Agent System for Comprehensive Comfy |
| arxiv:2503.18891 | include  s12 c21 | exclude out_of_scope s3 c9 | AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-P |
| arxiv:2503.21080 | include  s12 c17 | exclude out_of_scope s3 c9 | EmoDebt: Bayesian-Optimized Emotional Intelligence for Strategic Agent |
| arxiv:2503.23145 | include  s12 c18 | exclude out_of_scope s2 c7 | CodeARC: Benchmarking Reasoning Capabilities of LLM Agents for Inducti |
| arxiv:2504.01911 | include  s12 c11 | exclude out_of_scope s2 c6 | Advancing AI-Scientist Understanding: Multi-Agent LLMs with Interpreta |
| arxiv:2504.08747 | include  s12 c12 | exclude out_of_scope s2 c6 | GridMind: A Multi-Agent NLP Framework for Unified, Cross-Modal NFL Dat |
| arxiv:2504.10497 | include  s12 c9 | exclude out_of_scope s2 c8 | Exploring Generative AI Techniques in Government: A Case Study |
| arxiv:2504.12330 | include  s12 c18 | exclude out_of_scope s2 c8 | HM-RAG: Hierarchical Multi-Agent Multimodal Retrieval Augmented Genera |
| arxiv:2504.13192 | include  s12 c9 | exclude out_of_scope s2 c4 | CheatAgent: Attacking LLM-Empowered Recommender Systems via LLM Agent |
| arxiv:2504.18316 | exclude out_of_scope s3 c14 | include  s12 c15 | Towards Adaptive Software Agents for Debugging |
| arxiv:2504.18880 | include  s12 c13 | exclude out_of_scope s2 c8 | Reshaping MOFs text mining with a dynamic multi-agents framework of la |
| arxiv:2504.20073 | include  s12 c19 | exclude out_of_scope s11 c10 | RAGEN: Understanding Self-Evolution in LLM Agents via Multi-Turn Reinf |
| arxiv:2505.06821 | include  s12 c12 | exclude out_of_scope s3 c9 | ThreatLens: LLM-guided Threat Modeling and Test Plan Generation for Ha |
| arxiv:2505.11065 | include  s12 c22 | exclude out_of_scope s2 c12 | Time Travel is Cheating: Going Live with DeepFund for Real-Time Fund I |
| arxiv:2505.11942 | include  s12 c19 | exclude out_of_scope s2 c2 | LifelongAgentBench: Evaluating LLM Agents as Lifelong Learners |
| arxiv:2505.14163 | include  s12 c14 | exclude out_of_scope s2 c10 | DSMentor: Enhancing Data Science Agents with Curriculum Learning and O |
| arxiv:2505.16832 | include  s12 c11 | exclude out_of_scope s2 c8 | From EduVisBench to EduVisAgent: A Benchmark and Multi-Agent Framework |
| arxiv:2505.17511 | include  s12 c9 | exclude out_of_scope s2 c3 | Multi-agent Systems for Misinformation Lifecycle : Detection, Correcti |
| arxiv:2505.18646 | include  s12 c10 | exclude out_of_scope s3 c6 | SEW: Self-Evolving Agentic Workflows for Automated Code Generation |
| arxiv:2505.21291 | include  s12 c15 | exclude out_of_scope s2 c7 | Complex System Diagnostics Using a Knowledge Graph-Informed and Large  |
| arxiv:2505.21966 | include  s12 c17 | exclude out_of_scope s2 c12 | MapStory: Prototyping Editable Map Animations with LLM Agents |
| arxiv:2505.22303 | include  s12 c9 | exclude out_of_scope s2 c5 | VOICE CMS: UPDATING THE KNOWLEDGE BASE OF A DIGITAL ASSISTANT THROUGH  |
| arxiv:2505.23187 | include  s12 c15 | exclude out_of_scope s3 c7 | Cross-Task Experiential Learning on LLM-based Multi-Agent Collaboratio |
| arxiv:2505.23852 | include  s12 c13 | exclude duplicate_system s10 c4 | Large language model-based agents for automated research reproducibili |
| arxiv:2505.24019 | include  s12 c14 | exclude out_of_scope s2 c4 | LLM Agents Should Employ Security Principles |
| arxiv:2506.01716 | include  s12 c14 | exclude out_of_scope s11 c4 | Self-Challenging Language Model Agents |
| arxiv:2506.02048 | include  s12 c14 | exclude out_of_scope s11 c6 | Improving LLM Agents with Reinforcement Learning on Cryptographic CTF  |
| arxiv:2506.07636 | exclude out_of_scope s11 c11 | include  s12 c10 | SWE-Dev: Building Software Engineering Agents with Training and Infere |
| arxiv:2506.08403 | include  s12 c18 | exclude out_of_scope s3 c11 | TACTIC: Translation Agents with Cognitive-Theoretic Interactive Collab |
| arxiv:2506.08726 | include  s12 c14 | exclude out_of_scope s2 c3 | Improved LLM Agents for Financial Document Question Answering |
| arxiv:2506.11237 | include  s12 c8 | exclude out_of_scope s3 c6 | LLM-as-a-Judge for Reference-less Automatic Code Validation and Refine |
| arxiv:2506.16393 | include  s12 c15 | exclude out_of_scope s2 c7 | From LLM-anation to LLM-orchestrator: Coordinating Small Models for Da |
| arxiv:2507.00979 | include  s12 c8 | exclude out_of_scope s5 c3 | Enhancing LLM Agent Safety via Causal Influence Prompting |
| arxiv:2507.02773 | include  s12 c20 | exclude out_of_scope s2 c10 | KERAP: A Knowledge-Enhanced Reasoning Approach for Accurate Zero-shot  |
| arxiv:2507.03223 | exclude out_of_scope s3 c8 | include  s12 c9 | SI-Agent: An Agentic Framework for Feedback-Driven Generation and Tuni |
| arxiv:2507.03616 | exclude out_of_scope s6 c13 | include  s12 c14 | EvoAgentX: An Automated Framework for Evolving Agentic Workflows |
| arxiv:2507.03726 | exclude out_of_scope s3 c9 | include  s12 c12 | AGENT-BASED DETECTION AND RESOLUTION OF INCOMPLETENESS AND AMBIGUITY I |
| arxiv:2507.03730 | include  s12 c10 | exclude out_of_scope s11 c5 | Less is More: Empowering GUI Agent with Context-Aware Simplification |
| arxiv:2507.08325 | include  s12 c13 | exclude out_of_scope s2 c6 | CRMAgent: A Multi-Agent LLM System for E-Commerce CRM Message Template |
| arxiv:2507.09100 | include  s12 c16 | exclude out_of_scope s2 c11 | AInsight: Augmenting Expert Decision-Making with On-the-Fly Insights G |
| arxiv:2507.14705 | include  s12 c8 | exclude out_of_scope s3 c2 | NEO: A Configurable Multi-Agent Framework for Scalable and Realistic T |
| arxiv:2507.14800 | include  s12 c14 | exclude out_of_scope s2 c7 | Large Language Model as An Operator: An Experience-Driven Solution for |
| arxiv:2507.15815 | include  s12 c19 | exclude out_of_scope s3 c8 | LLM Economist: Large Population Models and Mechanism Design in Multi-A |
| arxiv:2507.17015 | include  s12 c19 | exclude out_of_scope s2 c17 | Can External Validation Tools Improve Annotation Quality for LLM-as-a- |
| arxiv:2507.17131 | include  s12 c22 | exclude out_of_scope s2 c16 | Enabling Self-Improving Agents to Learn at Test Time With Human-In-The |
| arxiv:2507.19969 | include  s12 c19 | exclude out_of_scope s2 c9 | Text2Vis: A Challenging and Diverse Benchmark for Generating Multimoda |
| arxiv:2507.20474 | include  s12 c13 | exclude out_of_scope s2 c4 | MountainLion: A Multi-Modal LLM-Based Agent System for Interpretable a |
| arxiv:2507.21162 | include  s12 c10 | exclude out_of_scope s2 c9 | Large Language Model Powered Automated Modeling and Optimization of Ac |
| arxiv:2508.00344 | include  s12 c7 | exclude out_of_scope s11 c6 | PilotRL: Training Language Model Agents via Global Planning-Guided Pro |
| arxiv:2508.02611 | include  s12 c12 | exclude out_of_scope s3 c7 | Meta-RAG on Large Codebases Using Code Summarization |
| arxiv:2508.06457 | include  s12 c16 | exclude out_of_scope s3 c8 | ScamAgents: How AI Agents Can Simulate Human-Level Scam Calls |
| arxiv:2508.08816 | include  s12 c12 | exclude out_of_scope s2 c10 | Efficient Agent: Optimizing Planning Capability for Multimodal Retriev |
| arxiv:2508.08997 | include  s12 c13 | exclude out_of_scope s3 c12 | INTRINSIC MEMORY AGENTS: HETEROGENEOUS MULTI-AGENT LLM SYSTEMS THROUGH |
| arxiv:2508.12393 | include  s12 c17 | exclude out_of_scope s2 c11 | MedKGent: A Large Language Model Agent Framework for Constructing Temp |
| arxiv:2508.13251 | include  s12 c14 | exclude out_of_scope s2 c9 | "DIVE" into Hydrogen Storage Materials Discovery with AI Agents |
| arxiv:2508.16112 | include  s12 c17 | exclude out_of_scope s2 c9 | IR-AGENT: EXPERT-INSPIRED LLM AGENTS FOR STRUCTURE ELUCIDATION FROM IN |
| arxiv:2508.18722 | include  s12 c16 | exclude out_of_scope s8 c17 | VistaWise: Building Cost-Effective Agent with Cross-Modal Knowledge Gr |
| arxiv:2508.20019 | include  s12 c20 | exclude out_of_scope s2 c12 | Symphony: A Decentralized Multi-Agent Framework for Scalable Collectiv |
| arxiv:2508.21622 | include  s12 c14 | exclude out_of_scope s2 c7 | Integrating Large Language Models with Network Optimization for Intera |
| arxiv:2509.03380 | include  s12 c15 | exclude out_of_scope s3 c8 | Situating AI Agents in their World: Aspective Agentic AI for Dynamic P |
| arxiv:2509.03793 | include  s12 c17 | exclude out_of_scope s3 c8 | SAMVAD: A Multi-Agent System for Simulating Judicial Deliberation Dyna |
| arxiv:2509.05378 | include  s12 c17 | exclude out_of_scope s2 c10 | Code Like Humans: A Multi-Agent Solution for Medical Coding |
| arxiv:2509.06269 | include  s12 c13 | exclude out_of_scope s2 c6 | REMI: A Novel Causal Schema Memory Architecture for Personalized Lifes |
| arxiv:2509.06501 | include  s12 c22 | exclude out_of_scope s11 c14 | WebExplorer: Explore and Evolve for Training Long-Horizon Web Agents |
| arxiv:2509.08755 | include  s12 c16 | exclude out_of_scope s11 c6 | AgentGym-RL: Training LLM Agents for Long-Horizon Decision Making thro |
| arxiv:2509.10054 | include  s12 c22 | exclude out_of_scope s3 c13 | XAgents: A Unified Framework for Multi-Agent Cooperation via IF-THEN R |
| arxiv:2509.11079 | include  s12 c16 | exclude out_of_scope s2 c9 | Difficulty-Aware Agentic Orchestration for Query-Specific Multi-Agent  |
| arxiv:2509.11523 | include  s12 c15 | exclude out_of_scope s2 c12 | VulAgent: A Hypothesis Validation-Based Multi-Agent System for Softwar |
| arxiv:2509.16713 | include  s12 c22 | exclude out_of_scope s3 c15 | OPEN-THEATRE: An Open-Source Toolkit for LLM-based Interactive Drama |
| arxiv:2509.19566 | include  s12 c18 | exclude out_of_scope s2 c12 | Nano Bio-Agents (NBA): Small Language Model Agents for Genomics |
| arxiv:2509.23586 | exclude out_of_scope s5 c6 | include  s12 c12 | Reducing Cost of LLM Agents with Trajectory Reduction |
| arxiv:2509.25643 | include  s12 c16 | exclude out_of_scope s2 c8 | SOCK: A Benchmark for Measuring Self-Replication in Large Language Mod |
| arxiv:2509.26076 | include  s12 c10 | exclude out_of_scope s2 c4 | IMProofBench: Benchmarking AI on Research-Level Mathematical Proof Gen |
| arxiv:2509.26201 | exclude out_of_scope s5 c11 | include  s12 c10 | LLM Agents for Knowledge Discovery in Atomic Layer Processing |
| arxiv:2510.04607 | include  s12 c26 | exclude out_of_scope s5 c16 | From Imperative to Declarative: Towards LLM-friendly OS Interfaces for |
| arxiv:2510.04851 | include  s12 c16 | exclude out_of_scope s5 c7 | LEGOMem: Modular Procedural Memory for Multi-agent LLM Systems for Wor |
| arxiv:2510.05414 | include  s12 c16 | exclude out_of_scope s2 c11 | A Lightweight Large Language Model-Based Multi-Agent System for 2D Fra |
| arxiv:2510.06225 | include  s12 c12 | exclude out_of_scope s6 c7 | Generalized Multi-agent Social Simulation Framework |
| arxiv:2510.10047 | include  s12 c14 | exclude out_of_scope s3 c10 | SwarmSys: Decentralized Swarm-Inspired Agents for Scalable and Adaptiv |
| arxiv:2510.10824 | include  s12 c14 | exclude out_of_scope s2 c9 | Agentic RAG for Software Testing with Hybrid Vector-Graph and Multi-Ag |
| arxiv:2510.11290 | exclude out_of_scope s3 c8 | include  s12 c8 | Evolution in Simulation: AI-Agent School with Dual Memory for High-Fid |
| arxiv:2510.14401 | include  s12 c13 | exclude out_of_scope s2 c3 | The Role of Social Learning and Collective Norm Formation in Fostering |
| arxiv:2510.14980 | include  s12 c17 | exclude out_of_scope s2 c7 | Compositional Machine Design as Program Synthesis with LLMs |
| arxiv:2510.15682 | include  s12 c19 | exclude out_of_scope s2 c10 | SQuAI: Scientific Question-Answering with Multi-Agent Retrieval-Augmen |
| arxiv:2510.15974 | include  s12 c18 | exclude duplicate_system s10 c5 | Limits of Emergent Reasoning of Large Language Models in Agentic Frame |
| arxiv:2510.17064 | include  s12 c12 | exclude out_of_scope s2 c5 | BRAINCELL-AID: An Agentic AI Created Brain Cell Type Resource for Comm |
| arxiv:2510.17814 | include  s12 c17 | exclude out_of_scope s3 c11 | LLM-Assisted Alpha-Fairness for 6 GHz Wi-Fi/NR-U Coexistence: An Agent |
| arxiv:2510.18477 | include  s12 c12 | exclude out_of_scope s2 c9 | LAFA: Agentic LLM-Driven Federated Analytics over Decentralized Data S |
| arxiv:2510.19438 | include  s12 c14 | exclude out_of_scope s2 c6 | AUTOMT: A Multi-Agent LLM Framework for Automated Metamorphic Testing  |
| arxiv:2510.19995 | include  s12 c13 | exclude out_of_scope s3 c9 | Communication to Completion: Modeling Collaborative Workflows with Int |
| arxiv:2510.20102 | include  s12 c14 | exclude out_of_scope s2 c5 | Human-Centered LLM-Agent System for Detecting Anomalous Digital Asset  |
| arxiv:2510.23642 | include  s12 c15 | exclude out_of_scope s11 c3 | VISCODER2: BUILDING MULTI-LANGUAGE VISUALIZATION CODING AGENTS |
| arxiv:2510.24802 | include  s12 c10 | exclude out_of_scope s3 c6 | From Narrative to Action: A Hierarchical LLM-Agent Framework for Human |
| arxiv:2510.25595 | include  s12 c14 | exclude duplicate_system s10 c4 | Communication and Verification in LLM Agents towards Collaboration und |
| arxiv:2510.26037 | exclude out_of_scope s3 c5 | include  s12 c9 | SIRAJ: Diverse and Efficient Red-Teaming for LLM Agents via Distilled  |
| arxiv:2510.26615 | include  s12 c16 | exclude out_of_scope s2 c6 | SlideAgent: Hierarchical Agentic Framework for Multi-Page Visual Docum |
| arxiv:2511.01188 | include  s12 c26 | exclude out_of_scope s3 c10 | ZoFia: Zero-Shot Fake News Detection with Entity-Guided Retrieval and  |
| arxiv:2511.04847 | include  s12 c13 | exclude out_of_scope s11 c2 | TEST-TIME ADAPTATION FOR LLM AGENTS VIA ENVIRONMENT INTERACTION |
| arxiv:2511.06262 | include  s12 c15 | exclude no_harness_description s1 c8 | GAIA: A General Agency Interaction Architecture for LLM-Human B2B Nego |
| arxiv:2511.06417 | exclude out_of_scope s2 c6 | include  s12 c11 | AUTO-Explorer: Automated Data Collection for GUI Agent |
| arxiv:2511.07392 | include  s12 c20 | exclude out_of_scope s8 c8 | Voice-Interactive Surgical Agent for Multimodal Patient Data Control |
| arxiv:2511.09030 | include  s12 c17 | exclude out_of_scope s3 c10 | Solving a Million-Step LLM Task with Zero Errors |
| arxiv:2511.10810 | include  s12 c10 | exclude out_of_scope s2 c10 | HARNESS: Human-Agent Risk Navigation and Event Safety System for Proac |
| arxiv:2511.11770 | include  s12 c20 | exclude out_of_scope s11 c5 | Learning to Refine: An Agentic RL Approach for Iterative SPARQL Query  |
| arxiv:2511.12997 | include  s12 c23 | exclude out_of_scope s5 c15 | WEBCOACH: SELF-EVOLVING WEB AGENTS WITH CROSS-SESSION MEMORY GUIDANCE |
| arxiv:2511.14780 | include  s12 c13 | exclude out_of_scope s3 c8 | Ask WhAI: Probing Belief Formation in Role-Primed LLM Agents |
| arxiv:2511.16709 | include  s12 c11 | exclude out_of_scope s3 c8 | AutoBackdoor: Automating Backdoor Attacks via LLM Agents |
| arxiv:2511.18423 | include  s12 c25 | exclude out_of_scope s5 c18 | General Agentic Memory Via Deep Research |
| arxiv:2511.19083 | include  s12 c27 | exclude out_of_scope s2 c15 | A Multi-Agent LLM Framework for Multi-Domain Low-Resource In-Context N |
| arxiv:2511.19669 | include  s12 c10 | exclude out_of_scope s2 c4 | HeaRT: A Hierarchical Circuit Reasoning Tree-Based Agentic Framework f |
| arxiv:2512.00214 | include  s12 c8 | exclude out_of_scope s2 c11 | Towards Corpus-Grounded Agentic LLMs for Multilingual Grammatical Anal |
| arxiv:2512.07850 | include  s12 c15 | exclude out_of_scope s5 c10 | SABER: Small Actions, Big Errors — Safeguarding Mutating Steps in LLM  |
| arxiv:2512.09577 | include  s12 c11 | exclude out_of_scope s2 c9 | Auto-BenchmarkCard: Automated Synthesis of Benchmark Documentation |
| arxiv:2512.10313 | include  s12 c25 | exclude out_of_scope s2 c10 | EpiPlanAgent: Agentic Automated Epidemic Response Planning |
| arxiv:2512.10766 | include  s12 c14 | exclude out_of_scope s2 c7 | Metaphor-based Jailbreak Attacks on Text-to-Image Models |
| arxiv:2512.11485 | include  s12 c23 | exclude out_of_scope s5 c8 | Mistake Notebook Learning: Batch-Clustered Failures for Training-Free  |
| arxiv:2512.15374 | include  s12 c23 | exclude out_of_scope s5 c14 | SCOPE: Prompt Evolution for Enhancing Agent Effectiveness |
| arxiv:2512.15688 | include  s12 c18 | exclude out_of_scope s2 c9 | BashArena: A Control Setting for Highly Privileged AI Agents |
| arxiv:2512.16279 | include  s12 c23 | exclude out_of_scope s5 c12 | QuadSentinel: Sequent Safety for Machine-Checkable Control in Multi-ag |
| arxiv:2512.16848 | include  s12 c20 | exclude out_of_scope s11 c6 | Meta-RL Induces Exploration in Language Agents |
| arxiv:2512.17146 | include  s12 c9 | exclude out_of_scope s2 c3 | Biosecurity-Aware AI: Agentic Risk Auditing of Soft Prompt Attacks on  |
| arxiv:2512.18440 | include  s12 c22 | exclude out_of_scope s2 c10 | An Agentic AI Framework for Training General Practitioner Student Skil |
| arxiv:2512.18669 | include  s12 c15 | exclude out_of_scope s2 c6 | IntelliCode: A Multi-Agent LLM Tutoring System with Centralized Learne |
| arxiv:2512.20652 | include  s12 c13 | exclude out_of_scope s2 c10 | AI-Driven Decision-Making System for Hiring Process |
| arxiv:2512.21578 | include  s12 c9 | exclude out_of_scope s11 c5 | NEMO-4-PAYPAL: Leveraging NVIDIA's Nemo Framework for empowering PayPa |
| arxiv:2512.24461 | include  s12 c10 | exclude out_of_scope s8 c9 | Align While Search: Belief-Guided Exploratory Inference for World-Grou |
| arxiv:2601.03287 | include  s12 c12 | exclude out_of_scope s2 c8 | Automated Post-Incident Policy Gap Analysis via Threat-Informed Eviden |
| arxiv:2601.03335 | include  s12 c22 | exclude out_of_scope s3 c7 | Digital Red Queen: Adversarial Program Evolution in Core War with LLMs |
| arxiv:2601.05004 | include  s12 c10 | exclude out_of_scope s2 c6 | Can Large Language Models Resolve Semantic Discrepancy in Self-Destruc |
| arxiv:2601.06235 | exclude out_of_scope s2 c6 | include  s12 c5 | An Intelligent AI glasses System with Multi-Agent Architecture for Rea |
| arxiv:2601.06845 | include  s12 c14 | exclude out_of_scope s2 c10 | Code Evolution for Control: Synthesizing Policies via LLM-Driven Evolu |
| arxiv:2601.07470 | include  s12 c15 | exclude out_of_scope s5 c9 | Learning How to Remember: A Meta-Cognitive Management Method for Struc |
| arxiv:2601.08742 | include  s12 c11 | exclude out_of_scope s2 c4 | Inferring Latent Intentions: Attributional Natural Language Inference  |
| arxiv:2601.09980 | include  s12 c16 | exclude no_harness_description s1 c4 | Performance of AI agents based on reasoning language models on ALD pro |
| arxiv:2601.12148 | include  s12 c13 | exclude out_of_scope s2 c8 | Many Hands Make Light Work: An LLM-based Multi-Agent System for Detect |
| arxiv:2601.13383 | include  s12 c21 | exclude out_of_scope s2 c14 | A Lightweight Modular Framework for Constructing Autonomous Agents Dri |
| arxiv:2601.17755 | exclude out_of_scope s11 c8 | include  s12 c6 | HyperGraphPro: Progress-Aware Reinforcement Learning for Structure-Gui |
| arxiv:2601.18847 | include  s12 c12 | exclude out_of_scope s2 c8 | MulVul: Retrieval-augmented Multi-Agent Code Vulnerability Detection v |
| arxiv:2601.19174 | include  s12 c15 | exclude out_of_scope s2 c3 | SHIELD: An Auto-Healing Agentic Defense Framework for LLM Resource Exh |
| arxiv:2601.20221 | exclude out_of_scope s11 c12 | include  s12 c12 | Scaling Medical Reasoning Verification via Tool-Integrated Reinforceme |
| arxiv:2602.00755 | include  s12 c13 | exclude out_of_scope s2 c3 | Evolving Interpretable Constitutions for Multi-Agent Coordination |
| arxiv:2602.00959 | include  s12 c16 | exclude out_of_scope s3 c6 | Probing the Knowledge Boundary: An Interactive Agentic Framework for D |
| arxiv:2602.02029 | include  s12 c13 | exclude out_of_scope s2 c7 | Canonical Intermediate Representation for LLM-based optimization probl |
| arxiv:2602.05407 | include  s12 c20 | exclude out_of_scope s2 c10 | H-AdminSim: A Multi-Agent Simulator for Realistic Hospital Administrat |
| arxiv:2602.07451 | include  s12 c14 | exclude duplicate_system s10 c6 | DLLM Agent: See Farther, Run Faster |
| arxiv:2602.07943 | include  s12 c11 | exclude out_of_scope s2 c7 | IV Co-Scientist: Multi-Agent LLM Framework for Causal Instrumental Var |
| arxiv:2602.08009 | include  s12 c12 | exclude out_of_scope s3 c8 | Towards Adaptive, Scalable, and Robust Coordination of LLM Agents: A D |
| arxiv:2602.08276 | include  s12 c14 | exclude duplicate_system s10 c2 | Toward Formalizing LLM-Based Agent Designs through Structural Context  |
| arxiv:2602.11749 | include  s12 c17 | exclude out_of_scope s5 c11 | AIR: Improving Agent Safety through Incident Response |
| arxiv:2602.13379 | include  s12 c13 | exclude out_of_scope s2 c3 | Unsafer in Many Turns: Benchmarking and Defending Multi-Turn Safety Ri |
| arxiv:2602.14117 | include  s12 c14 | exclude no_harness_description s1 c7 | Toward Autonomous O-RAN: A Multi-Scale Agentic AI Framework for Real-T |
| arxiv:2602.14295 | include  s12 c16 | exclude out_of_scope s2 c9 | Machine Learning as a Tool (MLAT): A Framework for Integrating Statist |
| arxiv:2602.14968 | include  s12 c11 | exclude out_of_scope s8 c7 | PhyScensis: Physics-Augmented LLM Agents for Complex Physical Scene Ar |
| arxiv:2602.15197 | include  s12 c19 | exclude out_of_scope s2 c9 | OPAQUETOOLSBENCH: LEARNING NUANCES OF TOOL BEHAVIOR THROUGH INTERACTIO |
| arxiv:2602.17308 | include  s12 c15 | exclude out_of_scope s3 c10 | MedClarify: An information-seeking AI agent for medical diagnosis with |
| arxiv:2602.17910 | exclude out_of_scope s3 c8 | include  s12 c7 | Alignment in Time: Peak-Aware Orchestration for Long-Horizon Agentic S |
| arxiv:2602.19810 | include  s12 c29 | exclude out_of_scope s5 c11 | From Agent-Only Social Networks to Autonomous Scientific Research: Les |
| arxiv:2602.21611 | include  s12 c14 | exclude duplicate_system s10 c5 | Structurally Aligned Subtask-Level Memory for Software Engineering Age |
| arxiv:2602.22546 | include  s12 c13 | exclude out_of_scope s8 c10 | Requesting Expert Reasoning: Augmenting LLM Agents with Learned Collab |
| arxiv:2602.23079 | include  s12 c15 | exclude out_of_scope s2 c9 | Assessing Deanonymization Risks with Stylometry-Assisted LLM Agent |
| arxiv:2602.23373 | include  s12 c17 | exclude out_of_scope s2 c10 | An Agentic LLM Framework for Adverse Media Screening in AML Compliance |
| arxiv:2603.00349 | include  s12 c14 | exclude out_of_scope s2 c1 | COOP2: Defining, Observing, and Repairing Cooperation in LLM Multi-Age |
| arxiv:2603.01912 | include  s12 c12 | exclude out_of_scope s3 c11 | Demonstrating ViviDoc: Generating Interactive Documents through Human- |
| arxiv:2603.02070 | include  s12 c13 | exclude out_of_scope s2 c5 | Exploring Plan Space through Conversation: An Agentic Framework for LL |
| arxiv:2603.02274 | include  s12 c12 | exclude out_of_scope s2 c6 | Contextual Invertible World Models: A Neuro-Symbolic Agentic Framework |
| arxiv:2603.05744 | include  s12 c9 | exclude out_of_scope s2 c4 | CodeScout: Contextual Problem Statement Enhancement for Software Agent |
| arxiv:2603.06007 | include  s12 c25 | exclude out_of_scope s6 c21 | MASFactory: A Graph-Centric Framework for Orchestrating LLM-Based Mult |
| arxiv:2603.07728 | include  s12 c14 | exclude out_of_scope s2 c7 | A Novel Multi-Agent Architecture to Reduce Hallucinations of Large Lan |
| arxiv:2603.08501 | include  s12 c13 | exclude out_of_scope s2 c8 | Fanar-Sadiq: A Multi-Agent Architecture for Grounded Islamic QA |
| arxiv:2603.10098 | include  s12 c11 | exclude out_of_scope s3 c4 | Code-Space Response Oracles: Generating Interpretable Multi-Agent Poli |
| arxiv:2603.11337 | include  s12 c21 | exclude out_of_scope s2 c13 | RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engi |
| arxiv:2603.11709 | include  s12 c12 | exclude out_of_scope s2 c7 | Scaling Laws for Educational AI Agents |
| arxiv:2603.11890 | include  s12 c19 | exclude out_of_scope s3 c8 | QUARE: Quality-Aware Requirements Analysis through Multi-Agent Dialect |
| arxiv:2603.13191 | include  s12 c23 | exclude out_of_scope s5 c13 | From Experiments to Expertise: Scientific Knowledge Consolidation for  |
| arxiv:2603.17169 | include  s12 c12 | exclude duplicate_system s10 c7 | How Clued up are LLMs? Evaluating Multi-Step Deductive Reasoning in a  |
| arxiv:2603.17399 | include  s12 c11 | exclude duplicate_system s10 c5 | Bootstrapping Coding Agents: The Specification Is the Program |
| arxiv:2603.17673 | include  s12 c19 | exclude out_of_scope s11 c8 | Towards Reliable Local Security Agents: Verifiable Post-Training for L |
| arxiv:2603.18377 | include  s12 c19 | exclude out_of_scope s5 c8 | PlanTwin: Privacy-Preserving Planning Abstractions for Cloud-Assisted  |
| arxiv:2603.22083 | include  s12 c7 | exclude duplicate_system s10 c2 | A Context Engineering Framework for Improving Enterprise AI Agents bas |
| arxiv:2603.24014 | include  s12 c15 | exclude out_of_scope s3 c5 | Language-Grounded Multi-Agent Planning for Personalized and Fair Parti |
| arxiv:2603.24647 | include  s12 c24 | exclude duplicate_system s10 c4 | Can LLMs Beat Classical Hyperparameter Optimization Algorithms? A Stud |
| arxiv:2603.25770 | include  s12 c19 | exclude out_of_scope s2 c3 | ReCUBE: Evaluating Repository-Level Context Utilization in Code Genera |
| arxiv:2603.27404 | include  s12 c16 | exclude out_of_scope s3 c9 | Heterogeneous Debate Engine: Identity-Grounded Cognitive Architecture  |
| arxiv:2603.28336 | include  s12 c11 | exclude out_of_scope s2 c5 | A Multi-Agent Rhizomatic Pipeline for Non-Linear Literature Analysis |
| arxiv:2603.30031 | exclude out_of_scope s3 c5 | include  s12 c6 | Cognitive Friction: A Decision-Theoretic Framework for Bounded Deliber |
| arxiv:2604.00722 | include  s12 c14 | exclude out_of_scope s11 c0 | LangMARL: Natural Language Multi-Agent Reinforcement Learning |
| arxiv:2604.03888 | exclude out_of_scope s2 c6 | include  s12 c11 | PolySwarm: A Multi-Agent Large Language Model Framework for Prediction |
| arxiv:2604.05333 | include  s12 c21 | exclude out_of_scope s5 c8 | Graph-of-Skills: Dependency-Aware Structural Retrieval for Massive Age |
| arxiv:2604.05339 | include  s12 c16 | exclude out_of_scope s2 c5 | Human Values Matter: Investigating How Misalignment Shapes Collective  |
| arxiv:2604.05533 | include  s12 c14 | exclude out_of_scope s8 c10 | Experience Transfer for Multimodal LLM Agents in Minecraft Game |
| arxiv:2604.05808 | exclude out_of_scope s11 c8 | include  s12 c11 | Hierarchical Reinforcement Learning with Augmented Step-Level Transiti |
| arxiv:2604.06753 | include  s12 c17 | exclude duplicate_system s10 c4 | Select-then-Solve: Paradigm Routing as Inference-Time Optimization for |
| arxiv:2604.07455 | include  s12 c22 | exclude duplicate_system s10 c8 | Munkres' General Topology Autoformalized in Isabelle/HOL |
| arxiv:2604.09584 | exclude no_harness_description s1 c14 | include  s12 c13 | Agentic Exploration of PDE Spaces using Latent Foundation Models for P |
| arxiv:2604.10470 | include  s12 c15 | exclude out_of_scope s3 c9 | From Query to Counsel: Structured Reasoning with a Multi-Agent Framewo |
| arxiv:2604.10825 | include  s12 c25 | exclude out_of_scope s2 c0 | CheeseBench: Evaluating Large Language Models on Rodent Behavioral Neu |
| arxiv:2604.10989 | include  s12 c14 | exclude out_of_scope s2 c7 | MAFIG: Multi-agent Driven Formal Instruction Generation Framework |
| arxiv:2604.11661 | include  s12 c16 | exclude out_of_scope s2 c7 | Towards Autonomous Mechanistic Reasoning in Virtual Cells |
| arxiv:2604.15505 | include  s12 c14 | exclude out_of_scope s5 c5 | PolicyBank: Evolving Policy Understanding for LLM Agents |
| arxiv:2604.16337 | include  s12 c15 | exclude out_of_scope s2 c6 | HR-Agents: Using Multiple LLM-based Agents to Improve Q&A about Brazil |
| arxiv:2604.17400 | include  s12 c12 | exclude out_of_scope s3 c6 | Phase-Scheduled Multi-Agent Systems for Token-Efficient Coordination |
| arxiv:2604.17450 | include  s12 c11 | exclude out_of_scope s2 c6 | Compiling Deterministic Structure into SLM Harnesses |
| arxiv:2604.17948 | include  s12 c15 | exclude out_of_scope s2 c6 | RAVEN: Retrieval-Augmented Vulnerability Exploration Network for Memor |
| arxiv:2604.18847 | include  s12 c11 | exclude out_of_scope s2 c8 | Human-Guided Harm Recovery for Computer Use Agents |
| arxiv:2604.19022 | include  s12 c12 | exclude out_of_scope s5 c6 | On Accelerating Grounded Code Development for Research |
| arxiv:2604.19792 | include  s12 c14 | exclude out_of_scope s3 c6 | OpenCLAW-P2P v7.0: Resilient Multi-Layer Persistence, Live Reference V |
| arxiv:2604.21896 | include  s12 c10 | exclude out_of_scope s2 c5 | Nemobot Games: Crafting Strategic AI Gaming Agents for Interactive Lea |
| arxiv:2604.23626 | include  s12 c22 | exclude out_of_scope s11 c6 | GraphPlanner: Graph Memory-Augmented Agentic Routing for Multi-Agent L |
| arxiv:2604.24512 | exclude out_of_scope s3 c7 | include  s12 c11 | Beyond the Attention Stability Boundary: Agentic Self-Synthesizing Rea |
| arxiv:2604.24807 | include  s12 c15 | exclude out_of_scope s2 c10 | From Prototype to Classroom: An Intelligent Tutoring System for Quantu |
| arxiv:2604.24831 | include  s12 c13 | exclude out_of_scope s2 c8 | FGDM: Reasoning Aware Multi-Agentic Framework for Software Bug Detecti |
| arxiv:2604.25684 | include  s12 c15 | exclude out_of_scope s5 c10 | Think Before You Act — A Neurocognitive Governance Model for Autonomou |
| arxiv:2604.26805 | include  s12 c23 | exclude out_of_scope s2 c13 | Bian Que: An Agentic Framework with Flexible Skill Arrangement for Onl |
| arxiv:2604.27143 | include  s12 c18 | exclude duplicate_system s10 c2 | Enhancing Linux Privilege Escalation Attack Capabilities of Local LLM  |
| arxiv:2604.27419 | include  s12 c15 | exclude out_of_scope s2 c7 | InteractWeb-Bench: Can Multimodal Agent Escape Blind Execution in Inte |
| arxiv:2604.27616 | include  s12 c25 | exclude out_of_scope s3 c13 | RoadMapper: A Multi-Agent System for Roadmap Generation of Solving Com |
| arxiv:2605.01489 | include  s12 c12 | exclude out_of_scope s11 c5 | SciResearcher: Scaling Deep Research Agents for Frontier Scientific Re |
| arxiv:2605.01892 | include  s12 c18 | exclude out_of_scope s2 c15 | CyberAId: AI-Driven Cybersecurity for Financial Service Providers |
| arxiv:2605.03986 | include  s12 c15 | exclude out_of_scope s3 c9 | From Intent to Execution: Composing Agentic Workflows with Agent Recom |
| arxiv:2605.07001 | include  s12 c20 | exclude out_of_scope s2 c16 | SmellBench: Evaluating LLM Agents on Architectural Code Smell Repair |
| arxiv:2605.07058 | include  s12 c18 | exclude out_of_scope s11 c11 | MedExAgent: Training LLM Agents to Ask, Examine, and Diagnose in Noisy |
| arxiv:2605.07103 | include  s12 c11 | exclude out_of_scope s2 c10 | ARMOR: An Agentic Framework for Reaction Feasibility Prediction via Ad |
| arxiv:2605.08583 | include  s12 c21 | exclude out_of_scope s2 c14 | Source or It Didn't Happen: A Multi-Agent Framework for Citation Hallu |
| arxiv:2605.08761 | include  s12 c22 | exclude out_of_scope s2 c3 | Beyond the All-in-One Agent: Benchmarking Role-Specialized Multi-Agent |
| arxiv:2605.09998 | include  s12 c19 | exclude out_of_scope s8 c13 | Continual Harness: Online Adaptation for Self-Improving Foundation Age |
| arxiv:2605.10005 | include  s12 c14 | exclude out_of_scope s5 c11 | Combining Mechanical and Agentic Specification Inference for Move |
| arxiv:2605.10059 | exclude out_of_scope s3 c9 | include  s12 c9 | Strategic Exploitation in LLM Agent Markets: A Simulation Framework fo |
| arxiv:2605.10913 | include  s12 c20 | exclude out_of_scope s5 c13 | SHEPHERD: Enabling Programmable Meta-Agents via Reversible Agentic Exe |
| arxiv:2605.12213 | include  s12 c14 | exclude out_of_scope s5 c6 | Goal-Oriented Reasoning for RAG-based Memory in Conversational Agentic |
| arxiv:2605.12493 | exclude out_of_scope s2 c4 | include  s12 c9 | LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced C |
| arxiv:2605.12943 | include  s12 c13 | exclude out_of_scope s3 c8 | Reinforced Collaboration in Multi-Agent Flow Networks |
| arxiv:2605.13110 | include  s12 c16 | exclude out_of_scope s2 c12 | A Multi-Agent Orchestration Framework for Venture Capital Due Diligenc |
| arxiv:2605.13618 | include  s12 c22 | exclude out_of_scope s6 c15 | OpenAaaS: An Open Agent-as-a-Service Framework for Distributed Materia |
| arxiv:2605.14401 | include  s12 c13 | exclude out_of_scope s2 c10 | Agentic Recommender System with Hierarchical Belief-State Memory |
| arxiv:2605.16191 | include  s12 c8 | exclude duplicate_system s10 c3 | Optimized Three-Dimensional Photovoltaic Structures with LLM guided Tr |
| arxiv:2605.17159 | include  s12 c14 | exclude out_of_scope s2 c10 | MADP: A Multi-Agent Pipeline for Sustainable Document Processing with  |
| arxiv:2605.17698 | include  s12 c13 | exclude out_of_scope s2 c8 | Agent Bazaar: Enabling Economic Alignment in Multi-Agent Marketplaces |
| arxiv:2605.17792 | exclude out_of_scope s11 c13 | include  s12 c14 | HydroAgent: Closing the Gap Between Frontier LLMs and Human Experts in |
| arxiv:2605.22566 | include  s12 c10 | exclude out_of_scope s2 c3 | GraphFlow: A Graph-Based Workflow Management for Efficient LLM-Agent S |
| arxiv:2605.22897 | exclude out_of_scope s3 c5 | include  s12 c10 | From Residuals to Reasons: LLM-Guided Mechanism Inference from Tabular |
| arxiv:2605.23574 | include  s12 c16 | exclude out_of_scope s2 c2 | Push Your Agent: Measuring and Enforcing Quantitative Goal Persistence |
| arxiv:2605.23917 | include  s12 c15 | exclude out_of_scope s3 c5 | Multi-Persona Debate System for Automated Scientific Hypothesis Genera |
| arxiv:2605.24598 | include  s12 c8 | exclude out_of_scope s5 c4 | Hera: Learning Long-Horizon Coordination for Device–Cloud Collaborativ |
| arxiv:2605.25832 | exclude out_of_scope s8 c7 | include  s12 c5 | When Search Becomes Memory: Turning Robot Design Trials into Transfera |
| arxiv:2605.26087 | include  s12 c15 | exclude out_of_scope s2 c1 | DiscoverPhysics: Benchmarking LLMs for Out-of-the-Box Scientific Think |
| arxiv:2605.27071 | include  s12 c23 | exclude out_of_scope s2 c8 | Traceable Knowledge Graph Reasoning Enables LLM-Assisted Decision Supp |
| arxiv:2605.27333 | include  s12 c18 | exclude out_of_scope s5 c11 | FINHARNESS: An Inline Lifecycle Safety Harness for Finance LLM Agents |
| arxiv:2605.28120 | include  s12 c28 | exclude out_of_scope s2 c10 | LegalGraphRAG: Multi-Agent Graph Retrieval-Augmented Generation for Re |
| arxiv:2605.29966 | include  s12 c20 | exclude out_of_scope s2 c14 | Compass: Navigating Global Marine Lead Data Integration through Expert |
| arxiv:2605.30712 | include  s12 c12 | exclude out_of_scope s5 c7 | ExpGraph: Model-Agnostic Experience Learning with Graph-Structured Mem |
| arxiv:2606.01617 | include  s12 c19 | exclude out_of_scope s3 c10 | EvoPool: Evolutionary Programmatic Annotation for Label-Efficient Spec |
| arxiv:2606.01886 | include  s12 c18 | exclude out_of_scope s2 c8 | Absorbing Complexity: An Interaction-Native Knowledge Harness for Fina |
| arxiv:2606.02867 | include  s12 c15 | exclude out_of_scope s3 c6 | The Epi-LLM Framework: probing LLM behavioral priors through epidemiol |
| arxiv:2606.05342 | include  s12 c18 | exclude out_of_scope s2 c6 | SentinelBench: A Benchmark for Long-Running Monitoring Agents |
| arxiv:2606.06025 | include  s12 c15 | exclude out_of_scope s2 c4 | EGTR-Review: Efficient Evidence-Grounded Scientific Peer Review Genera |
| arxiv:2606.06525 | include  s12 c11 | exclude out_of_scope s2 c8 | Agentic Large Language Models for Automated Structural Analysis of 3D  |
| arxiv:2606.07586 | include  s12 c18 | exclude out_of_scope s5 c9 | From Human Guidance to Autonomy: Agent Skill System for End-to-End LLM |
| arxiv:2606.07909 | include  s12 c17 | exclude out_of_scope s5 c6 | MemToolAgent: Leveraging Memory for Tool Using Agents Based on Environ |
| arxiv:2606.09549 | include  s12 c16 | exclude out_of_scope s5 c5 | SecureClaw: Clawing Back Control of LLM Agents |
| arxiv:2606.10917 | include  s12 c20 | exclude out_of_scope s11 c8 | Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution |
| arxiv:2606.11290 | include  s12 c9 | exclude out_of_scope s2 c5 | FlowBank: Query-Adaptive Agentic Workflows Optimization through Precom |
| arxiv:2606.11440 | exclude out_of_scope s3 c6 | include  s12 c12 | INFRAMIND: Infrastructure-Aware Multi-Agent Orchestration |
| arxiv:2606.12848 | exclude duplicate_system s10 c7 | include  s12 c14 | (Human) Attention Is (Still) All You Need: Human oversight makes AI-as |
| arxiv:2606.12902 | include  s12 c15 | exclude out_of_scope s2 c9 | PRISM: Prosody-Integrated Multi-Agent Reasoning Framework for Empathet |
| arxiv:2606.12969 | exclude duplicate_system s10 c7 | include  s12 c12 | Multi-Modal Agents for Power Distribution Defect Detection: An Evaluat |
| arxiv:2606.13692 | include  s12 c15 | exclude no_harness_description s1 c2 | An Agentic Retrieval Framework for Autonomous Context-Aware Data Quali |
| arxiv:2606.15363 | exclude out_of_scope s3 c9 | include  s12 c10 | APEX: Adaptive Principle EXtraction — A Three-Layer Self-Evolution Fra |
| arxiv:2606.15390 | include  s12 c11 | exclude out_of_scope s5 c8 | Not All Skills Help: Measuring and Repairing Agent Knowledge |
| arxiv:2606.15874 | include  s12 c13 | exclude duplicate_system s10 c10 | LLM-as-Code: Agentic Programming for Agent Harness |
| arxiv:2606.17016 | include  s12 c10 | exclude out_of_scope s5 c8 | TokenPilot: Cache-Efficient Context Management for LLM Agents |
| arxiv:2606.17092 | include  s12 c10 | exclude duplicate_system s10 c5 | Securing Multi-Agent GIS Systems: Risk Evaluation and Prompt Hardening |
| arxiv:2606.18976 | include  s12 c14 | exclude out_of_scope s2 c6 | CAPRA: Scaling Feedback on Software Architecture Deliverables with a M |
| arxiv:2606.19501 | include  s12 c18 | exclude out_of_scope s2 c15 | DeXposure-Claw: An Agentic System for DeFi Risk Supervision |
| arxiv:2606.21123 | include  s12 c12 | exclude out_of_scope s2 c10 | A Multi-Agent Audit Framework for High-Stakes Reasoning |
| arxiv:2606.27397 | include  s12 c14 | exclude out_of_scope s2 c6 | SidConArena: An Environment Evaluating Agents in Open-Ended, Positive- |
| arxiv:2606.30877 | include  s12 c13 | exclude out_of_scope s3 c9 | A Systematic Approach to Multi-Agent AI from Advanced Regulatory Contr |
| arxiv:2607.00555 | include  s12 c11 | exclude out_of_scope s2 c8 | Rise From The Ashes: LLM-based Static Analysis for Deep Learning Frame |
| arxiv:2607.00918 | include  s12 c16 | exclude out_of_scope s3 c11 | From Personas to Plot: Character-Grounded Multi-Agent Story Generation |
| arxiv:2607.01063 | include  s12 c13 | exclude out_of_scope s2 c4 | AutoRestTest at the SBFT 2026 Tool Competition |
| arxiv:2607.02134 | include  s12 c20 | exclude out_of_scope s5 c2 | Coding-agents can replicate scientific machine learning papers |
| arxiv:2607.02389 | include  s12 c14 | exclude no_harness_description s1 c8 | Steerability via constraints: a substrate for scalable oversight of co |
| arxiv:2607.02846 | include  s12 c15 | exclude out_of_scope s5 c1 | Object-Centric Environment Modeling for Agentic Tasks |
| arxiv:2607.03025 | include  s12 c24 | exclude out_of_scope s3 c15 | Human-Centric Reflective Architecture for Human-AI Collaborative Decis |
| arxiv:2607.03702 | include  s12 c18 | exclude out_of_scope s11 c5 | Agent Reinforcement Learning via Pivotal-Aware Self-Feedback Retry |
| arxiv:2607.03730 | include  s12 c13 | exclude out_of_scope s2 c7 | ProACT: Towards Breakdown-Aware Proactive Agent in Multi-User Collabor |
| arxiv:2607.04391 | exclude out_of_scope s5 c10 | include  s12 c14 | Memory-Orchestrated Semantic System (MOSS): An Auditable Agentic Memor |
| arxiv:2607.05001 | include  s12 c21 | exclude out_of_scope s2 c17 | TACTIC-KG: Toward Small Agent Teams for Cyber Threat Intelligence Know |
| arxiv:2607.07619 | include  s12 c13 | exclude duplicate_system s10 c7 | Rethinking Code Performance Benchmarks for LLMs |
| arxiv:2607.08028 | include  s12 c15 | exclude out_of_scope s2 c10 | From Prompts to Contracts: Harness Engineering for Auditable Enterpris |
| arxiv:2607.09600 | include  s12 c19 | exclude out_of_scope s2 c8 | Agora: Enhancing LLM Agent Reasoning Via Auction-Based Task Allocation |
| arxiv:2607.11276 | include  s12 c12 | exclude out_of_scope s2 c7 | Automated Textbook Auditing with Multi-Agent LLM Systems |
| arxiv:2607.11334 | include  s12 c15 | exclude no_harness_description s1 c11 | Verifier-Guided Twelve-Tone Composition: A Generate–Verify–Repair Harn |
| arxiv:2607.11503 | include  s12 c16 | exclude out_of_scope s5 c10 | GEIS: A Generation–Evaluation–Improvement Loop of Agent Skills for Lon |
| arxiv:2607.12122 | include  s12 c26 | exclude out_of_scope s3 c13 | An Agentic AI Scientific Community for Automated Neural Operator Disco |
| arxiv:2607.13179 | include  s12 c15 | exclude out_of_scope s2 c12 | SoftBoard: A Multi-Agent Tool for the Creation and Evaluation of Low-F |
| arxiv:2607.15095 | include  s12 c16 | exclude out_of_scope s3 c5 | DIGITAL PANTHEON: SIMULATING AND AUDITING COALITION FORMATION WITH LLM |
| arxiv:2607.15544 | include  s12 c13 | exclude out_of_scope s2 c8 | EpiNarrate: Agentic Generation of Grounded Narratives from Epidemiolog |
| arxiv:2607.15854 | include  s12 c16 | exclude out_of_scope s3 c4 | Agentic Synthesis against Counterexample-Supplemented Sketches |
| arxiv:2607.16621 | include  s12 c18 | exclude out_of_scope s5 c9 | From Memory to Skills: Evidence-Grounded Co-Evolution Governance for L |
| arxiv:2607.16745 | include  s12 c12 | exclude out_of_scope s3 c4 | RELIC: Revealed Principles for Learning Interpretable Composable Skill |
| arxiv:2607.17437 | include  s12 c10 | exclude duplicate_system s10 c2 | Empirical Grounding Improves the Realism of LLM Agents Simulating Huma |
| arxiv:2607.21799 | include  s12 c19 | exclude out_of_scope s2 c5 | Copyright-Bench: Agentic Evaluation of Copyright Law Compliance |
| arxiv:2607.22555 | include  s12 c19 | exclude out_of_scope s3 c12 | DeepLens Diagnosis Agent: Agentic Workflow Design Lets a Small Reasoni |
| arxiv:2607.22917 | include  s12 c22 | exclude out_of_scope s5 c11 | Agent Team Work Zone: An Automated, Persistent Workspace for Long-Live |
| arxiv:2607.24779 | include  s12 c18 | exclude out_of_scope s3 c8 | HOBA: Hierarchical On-Policy Bidding Agents for Adaptive Online Advert |
| arxiv:2607.25140 | exclude out_of_scope s3 c8 | include  s12 c11 | How Affect Propagates among LLM Agents: Emergent Emotional Contagion i |
| arxiv:2607.26220 | include  s12 c17 | exclude no_harness_description s1 c5 | Model-Driven Requirements Configuration with Three-Valued Uncertainty  |
| arxiv:2607.26393 | exclude out_of_scope s3 c9 | include  s12 c9 | CaM-Wolf: Causal-Aware Multimodal Agents for Social Deduction Games |
| arxiv:2607.28200 | include  s12 c13 | exclude out_of_scope s5 c8 | Vibe-FDTR: An agent-oriented framework for reproducible frequency-doma |
| arxiv:2608.00326 | include  s12 c17 | exclude no_harness_description s1 c9 | Learning to Coordinate Symbolic Tools: LLM Agents for Verified Sum-of- |
| arxiv:2608.00808 | include  s12 c21 | exclude out_of_scope s5 c10 | Turning Interaction History into Execution State: A Runtime Layer for  |
| arxiv:2608.01050 | include  s12 c12 | exclude out_of_scope s5 c5 | Don't Offer What Can't Be Done: Deterministic Executability Gating for |
| arxiv:2608.01652 | include  s12 c16 | exclude out_of_scope s8 c8 | SyncPlan: Long-Horizon LLM Coordination with Explicit Synchronization  |
| arxiv:2608.01772 | include  s12 c18 | exclude out_of_scope s5 c5 | FRAMES: Guarded and Dual-Objective Skill Evolution for Agents in Polic |
| arxiv:2608.02113 | include  s12 c16 | exclude out_of_scope s5 c11 | MemArbiter: Decision-Time Memory Arbitration for Long-Horizon LLM Agen |
| arxiv:2608.03134 | include  s12 c12 | exclude out_of_scope s2 c4 | CLEAR: Causal Context-Based Agentic Reasoning for Vulnerability Detect |
| arxiv:2608.05446 | include  s12 c17 | exclude out_of_scope s8 c11 | EvoHarness-RL: Learning Self-Evolving Runtime Harness for Long-Horizon |
| arxiv:2608.05519 | include  s12 c11 | exclude out_of_scope s2 c3 | EcoAgent-Bench: Evaluating Economic Decision-Making in Budget-Constrai |
| arxiv:2608.06153 | include  s12 c9 | exclude out_of_scope s5 c5 | Learning Globally Reusable Skills for Coding Agents |
| arxiv:2608.07169 | include  s12 c13 | exclude out_of_scope s5 c11 | Agent Memory Distillation: Empowering Small LLM Agents with Hierarchic |
| arxiv:2608.07651 | include  s12 c14 | exclude out_of_scope s2 c7 | An Agentic AI Framework Overcomes Fundamental Limitations of Large Lan |
| arxiv:2608.08055 | include  s12 c29 | exclude out_of_scope s5 c16 | SodaMem: Evidence-Grounded Temporal Graph Memory for LLM Agents |
| arxiv:2608.08264 | include  s12 c15 | exclude out_of_scope s5 c11 | OBLIVION: Workflow-Level Operational Skill Unlearning for Deployed Age |
| arxiv:2608.09044 | include  s12 c12 | exclude out_of_scope s5 c3 | Tree-of-Experience: Hierarchical Experience Management for Self-Evolvi |
| arxiv:2608.09443 | include  s12 c18 | exclude out_of_scope s3 c11 | Coupled Graph–Policy Distillation for Personalized Medication Safety i |
| arxiv:2608.10157 | include  s12 c10 | exclude out_of_scope s2 c7 | SBCO: Self-Supervised, Verifier-Grounded Harness Optimization For Plan |
| arxiv:2608.11338 | include  s12 c10 | exclude out_of_scope s8 c10 | Better, Faster, Stronger: Programmatic Skill Learning Best Reduces Age |
| arxiv:2608.12984 | include  s12 c22 | exclude out_of_scope s2 c13 | Reconcile Once, Write Anytime: A Trust-Tiered Librarian and a Multi-Ag |
| arxiv:2608.15424 | include  s12 c18 | exclude out_of_scope s5 c9 | ETHOS: Towards a Modular Ethics Framework for Clinical Multi-Agent Sys |
| arxiv:2608.16447 | include  s12 c23 | exclude out_of_scope s8 c12 | HaReCAP: Habitual-action Grounding for Recursive Large Language Model  |
| arxiv:2608.16934 | include  s12 c13 | exclude out_of_scope s5 c8 | SeqFeed: Improving LLM-Based RTL Code Generation with Sequential Behav |
| arxiv:2608.17433 | include  s12 c15 | exclude duplicate_system s10 c6 | Task-Aware Harness Provisioning for LLM Agents in Mission-Critical Inf |
| arxiv:2608.18050 | include  s12 c21 | exclude out_of_scope s5 c8 | StagedWorkspace: A Versioned Workspace for Knowledge-Work Agents |
| arxiv:2608.19974 | include  s12 c17 | exclude out_of_scope s2 c4 | ReguSim: Evaluating LLM Agent Rule Grounding in Financial Compliance |
| arxiv:2608.21027 | include  s12 c14 | exclude out_of_scope s5 c0 | DON'T SOLVE, JUST COMPARE: TINY ADVISORS FOR RUNTIME INTERVENTION IN L |
| arxiv:2608.21868 | include  s12 c20 | exclude out_of_scope s3 c12 | HiMA-MDD: A Hierarchical Multi-Agent Harness for Interpretable Multimo |
| arxiv:2608.22167 | include  s12 c16 | exclude out_of_scope s11 c7 | MCP-Universe RL: A Framework for Training MCP Tool-Use Agents via Rein |
| arxiv:2608.22339 | include  s12 c12 | exclude out_of_scope s5 c6 | When Not to Imitate: Boundary-Aware Skill Memory for Reliable Tool-Use |
| arxiv:2608.23867 | include  s12 c12 | exclude out_of_scope s2 c6 | Markets, Not Planners: Decentralized Orchestration of LLM Agents with  |
| arxiv:2608.24747 | include  s12 c11 | exclude out_of_scope s11 c5 | SkillForge: Evolving Verifiable Skills for Reinforcement Learning Agen |
| arxiv:2608.26114 | include  s12 c13 | exclude out_of_scope s2 c12 | CIFQA: A Deterministic Tool-Grounded Multi-Agent LLM Framework for Fin |
| arxiv:2608.27427 | include  s12 c13 | exclude no_harness_description s1 c1 | Persona–Execution Separation: An Architecture Pattern for Evolving LLM |
| arxiv:2608.27466 | include  s12 c14 | exclude out_of_scope s2 c8 | PACE: Publisher-Adaptive Content Extraction via Agentic Automation |
| arxiv:2608.27808 | exclude out_of_scope s2 c2 | include  s12 c13 | CURA: Certified Runtime Alarms for Computer-Use Agents |
| arxiv:2608.27998 | include  s12 c13 | exclude out_of_scope s2 c11 | Automated Analysis Framework for Multilingual Climate-Health Literatur |
| arxiv:2608.28027 | include  s12 c23 | exclude out_of_scope s5 c16 | String: An Agentic OS Where Every App Is a Markdown File |
| arxiv:2608.28264 | include  s12 c10 | exclude out_of_scope s5 c6 | Finding Where the Buck Stops: An Automated Failure Attribution-Based R |
| arxiv:2608.28624 | include  s12 c17 | exclude out_of_scope s2 c11 | MA-RAG: Multi-Agent Retrieval-Augmented Generation for Query-Driven Su |
| arxiv:2608.28632 | include  s12 c16 | exclude out_of_scope s8 c13 | AUTOSCIENTIST-QUANT: SELF-EVOLVING CODING AGENTS FOR AUTOMATIC RESEARC |
| arxiv:2608.29133 | exclude out_of_scope s3 c6 | include  s12 c8 | AI Historian: Helping historians organize and verify person-centred te |
| arxiv:2608.29305 | include  s12 c16 | exclude out_of_scope s11 c5 | Learning Simple Test-Time Environments for LLM Web Agents |
| arxiv:2608.30207 | exclude out_of_scope s3 c5 | include  s12 c13 | SIR: Self-improving Red-teaming for Computer Use Agents |
| arxiv:2608.31076 | include  s12 c18 | exclude out_of_scope s5 c13 | Learning to Evaluate Before Improving: Automatic Rubric Induction for  |
| arxiv:2608.31128 | include  s12 c17 | exclude out_of_scope s2 c10 | DIASENTINEL: An Auditable Multi-Agent System for Guideline-Grounded Di |
| arxiv:2609.00077 | include  s12 c15 | exclude duplicate_system s10 c8 | Beneath the Diff: Diagnosing and Mitigating Algorithmic Mode Collapse  |
| arxiv:2609.01608 | include  s12 c16 | exclude out_of_scope s11 c2 | WMLLM: Self-Evolving Optimization Agents via Predict-Then-Act World Mo |
| arxiv:2609.01617 | include  s12 c21 | exclude out_of_scope s3 c10 | Hybrid Retrieval-Augmented Generation with Knowledge Graph Expansion,  |
| arxiv:2609.05441 | exclude out_of_scope s2 c5 | include  s12 c15 | When Does Memory Help? A Cost-Aware Evaluation of Long-Term Memory in  |
| awesome:ggjy:0475edfdcc30 | include  s12 c5 | exclude out_of_scope s2 c3 | VisualWebArena: Evaluating Multimodal Agents on Realistic Visual Web T |
| awesome:ggjy:7135c83979fe | include  s12 c17 | exclude out_of_scope s5 c9 | OpenHands/OpenHands |
| awesome:ggjy:a944cbe68471 | include  s12 c21 | exclude out_of_scope s11 c6 | SEAgent: Self-Evolving Computer Use Agent with Autonomous Learning fro |
| awesome:picrew:0c600aca3176 | include  s12 c26 | exclude out_of_scope s5 c11 | paperclipai/paperclip |
| awesome:picrew:1c712cad4f64 | exclude out_of_scope s5 c8 | include  s12 c7 | trycua/cua |
| awesome:picrew:25246c2b662a | include  s12 c18 | exclude out_of_scope s5 c11 | github/copilot-sdk |
| awesome:picrew:4ba15d27de59 | include  s12 c18 | exclude out_of_scope s6 c14 | google/adk-python |
| awesome:picrew:5be75d75f637 | include  s12 c24 | exclude out_of_scope s5 c19 | sd0xdev/sd0x-harness |
| awesome:picrew:878db8f9445a | include  s12 c16 | exclude out_of_scope s5 c5 | harbor-framework/harbor |
| awesome:picrew:b1df4cee2b04 | include  s12 c20 | exclude out_of_scope s6 c9 | VoltAgent/voltagent |
| awesome:picrew:d111f3534aeb | include  s12 c9 | exclude duplicate_system s10 c4 | How GPT-5.6 fuses frontier intelligence with frontier efficiency |
| awesome:picrew:dd09a96a5899 | include  s12 c15 | exclude out_of_scope s5 c9 | google/ax |
| awesome:picrew:eefb5e67005f | include  s12 c22 | exclude out_of_scope s5 c14 | multica-ai/multica |
| github:Deuz-AI/Deuz-SDK | exclude out_of_scope s6 c17 | include  s12 c28 | Deuz-AI/Deuz-SDK |
| github:Dpro-at/Tel-Agent | include  s12 c17 | exclude out_of_scope s2 c5 | Dpro-at/Tel-Agent |
| github:HKUDS/ClawTeam | include  s12 c22 | exclude out_of_scope s5 c16 | HKUDS/ClawTeam |
| github:SomeOddCodeGuy/WilmerAI | include  s12 c25 | exclude out_of_scope s2 c12 | SomeOddCodeGuy/WilmerAI |
| github:StonyBrookNLP/appworld | include  s12 c23 | exclude out_of_scope s5 c16 | StonyBrookNLP/appworld |
| github:agiresearch/AIOS | include  s12 c17 | exclude out_of_scope s5 c11 | agiresearch/AIOS |
| github:browser-use/video-use | include  s12 c21 | exclude out_of_scope s5 c11 | browser-use/video-use |
| github:browser-use/web-ui | exclude out_of_scope s5 c6 | include  s12 c9 | browser-use/web-ui |
| github:crewAIInc/crewAI | include  s12 c18 | exclude out_of_scope s6 c11 | crewAIInc/crewAI |
| github:echoVic/boss-skill | include  s12 c24 | exclude out_of_scope s5 c18 | echoVic/boss-skill |
| github:hoolulu/deep-research | include  s12 c16 | exclude out_of_scope s5 c10 | hoolulu/deep-research |
| github:iusztinpaul/designing-real-world-ai-agents-workshop | exclude out_of_scope s5 c13 | include  s12 c15 | iusztinpaul/designing-real-world-ai-agents-workshop |
| github:joinly-ai/joinly | include  s12 c16 | exclude out_of_scope s5 c8 | joinly-ai/joinly |
| github:karpathy/autoresearch | exclude out_of_scope s5 c5 | include  s12 c13 | karpathy/autoresearch |
| github:nyldn/claude-octopus | include  s12 c26 | exclude out_of_scope s5 c11 | nyldn/claude-octopus |
| github:oliver-kriska/claude-elixir-phoenix | include  s12 c23 | exclude out_of_scope s5 c14 | oliver-kriska/claude-elixir-phoenix |
| github:ruvnet/metaharness | include  s12 c23 | exclude out_of_scope s6 c8 | ruvnet/metaharness |
| github:sandeco/reversa | include  s12 c22 | exclude out_of_scope s5 c8 | sandeco/reversa |
| github:sentient-agi/OpenDeepSearch | include  s12 c14 | exclude out_of_scope s5 c7 | sentient-agi/OpenDeepSearch |
| github:smallnest/goclaw | include  s12 c29 | exclude other s9 c23 | smallnest/goclaw |
| github:strongdm/attractor | include  s12 c5 | exclude out_of_scope s5 c2 | strongdm/attractor |
| github:trypromptly/LLMStack | exclude out_of_scope s6 c3 | include  s12 c4 | trypromptly/LLMStack |
| github:ultraworkers/claw-code-parity | exclude no_harness_description s7 c3 | include  s12 c8 | ultraworkers/claw-code-parity |
| github:wanikua/danghuangshang | include  s12 c18 | exclude other s9 c9 | wanikua/danghuangshang |
| github:xpander-ai/xpander.ai | include  s12 c14 | exclude out_of_scope s5 c6 | xpander-ai/xpander.ai |
| grey:semantic-kernel-agents | include  s12 c10 | exclude out_of_scope s6 c2 | Semantic Kernel Agent Architecture |
| leaderboard:osworld:aguvis-72b | exclude out_of_scope s11 c3 | include  s12 c6 | Aguvis: Unified Pure Vision Agents for Autonomous GUI Interaction |
| leaderboard:osworld:turix-computer-13-50-steps | include  s12 c10 | exclude no_harness_description s1 c2 | xlang-ai/OSWorld |
| leaderboard:osworld:uipath-screen-agent | include  s12 c11 | exclude no_harness_description s7 c1 | xlang-ai/OSWorld |
| leaderboard:swe-bench:amazon-q-developer-agent | exclude no_harness_description s7 c3 | include  s12 c4 | Amazon Q Developer |
| leaderboard:swe-bench:augment-agent-v1 | include  s12 c7 | exclude out_of_scope s5 c5 | Augment Code: Agentic software development at organizational scale |
| leaderboard:swe-bench:entropo-r2e | include  s12 c15 | exclude out_of_scope s11 c5 | hubertyoo/R2E-Gym |
| leaderboard:swe-bench:factory-code-droid | exclude no_harness_description s7 c2 | include  s12 c4 | Factory / Agent-Native Software Development |
| leaderboard:swe-bench:kgcompass | exclude out_of_scope s2 c5 | include  s12 c5 | GLEAM-Lab/KGCompass |
| leaderboard:swe-bench:qodo-command | exclude out_of_scope s2 c2 | include  s12 c7 | Qodo / AI Agents for Code, Review & Workflows |
| leaderboard:terminal-bench:codex | exclude no_harness_description s7 c2 | include  s12 c2 | Codex / AI Coding Partner from OpenAI |
| leaderboard:webarena:browsergym | include  s12 c11 | exclude out_of_scope s2 c6 | ServiceNow/BrowserGym |
| leaderboard:webarena:narada-ai | exclude no_harness_description s7 c8 | include  s12 c8 | Narada AI Web Agent Operator |
| openalex:W4402074932 | include  s12 c7 | exclude no_harness_description s7 c1 | Selecting from Multiple Strategies Improves the Foreseeable Reasoning  |
| openalex:W4402683907 | include  s12 c15 | exclude out_of_scope s2 c10 | GeoAgent: To Empower LLMs using Geospatial Tools for Address Standardi |
| openalex:W4405266245 | include  s12 c11 | exclude out_of_scope s2 c5 | CoordiLang: Assessing Multi-Agent Coordination Skills in Large Languag |
| openalex:W7105853558 | include  s12 c21 | exclude out_of_scope s3 c11 | Persistent Mind Model (PMM) v1.1 — A Deterministic, Event-Sourced, Per |
| openalex:W7110530286 | exclude no_harness_description s7 c4 | include  s12 c5 | apex™ |
| openalex:W7127081122 | include  s12 c14 | exclude out_of_scope s5 c9 | Synthesis: A Federated Capability Ecosystem for Safe AI Self-Extension |
| openalex:W7127543793 | include  s12 c5 | exclude no_harness_description s7 c3 | LLM-Assisted Translation and Bounded Model Checking of Python Code |
| openalex:W7127571647 | include  s12 c13 | exclude out_of_scope s2 c7 | (Hi.) Eyes: Deterministic Multi‑Agent Image Editing Orchestration |
| openalex:W7128303707 | exclude no_harness_description s7 c5 | include  s12 c6 | Project Quine: Autopoietic Intelligence via Fractal POSIX Processes (P |
| openalex:W7128487447 | include  s12 c6 | exclude out_of_scope s2 c2 | Friday Cognition: A Substrate-First Architecture for Emergent Artifici |
| openalex:W7134124258 | include  s12 c8 | exclude duplicate_system s10 c3 | Using agentic AI to assign gene function across multiple genomes |
| openalex:W7134818528 | include  s12 c8 | exclude out_of_scope s2 c5 | Jennifer: A Persistence-Kernel Runtime for Constraint-Bounded Alignmen |
| openalex:W7135026369 | include  s12 c6 | exclude no_harness_description s7 c4 | AIvilization: Explore the Future of Human-AI Coexistence, Co-building  |
| openalex:W7135055119 | include  s12 c11 | exclude out_of_scope s2 c9 | Rithan377/QueryRouter-AI: QueryRouter-AI |
| openalex:W7135197943 | exclude out_of_scope s2 c5 | include  s12 c4 | NeuralRiverOps: An Operational Framework for Implementing MLOps and Ag |
| openalex:W7135204538 | include  s12 c7 | exclude no_harness_description s7 c3 | Integrating Large Language Models into Climate and Geoscientific Data  |
| openalex:W7135204979 | include  s12 c8 | exclude no_harness_description s7 c2 | Development of a Context-Aware AI Agent for Forest Applications Using  |
| openalex:W7135244153 | include  s12 c6 | exclude no_harness_description s7 c2 | TunnelSentinel: An Agentic AI Framework for Geo-Structural Resilience  |
| openalex:W7135246736 | include  s12 c9 | exclude out_of_scope s3 c3 | Climate Service Recipes: automatic multi-hazard climate information wo |
| openalex:W7135386085 | exclude no_harness_description s7 c5 | include  s12 c5 | Improved multi-agent knowledge sharing system using knowledge graphs f |
| openalex:W7138897955 | include  s12 c5 | exclude out_of_scope s2 c0 | The End of Code-Centric AI: Living FDS as a Deterministic Single Sourc |
| openalex:W7139107003 | include  s12 c18 | exclude out_of_scope s2 c6 | roger-creus/agentick: Agentick v1.0 launch |
| openalex:W7140221938 | include  s12 c7 | exclude out_of_scope s5 c3 | MemTool: Optimizing Short-Term Memory Management for Dynamic Tool Retr |
| openalex:W7140293303 | include  s12 c21 | exclude out_of_scope s3 c14 | OncoBiome Swarm: A Large Language Model-Based Multi-Agent Framework fo |
| openalex:W7141355999 | exclude out_of_scope s2 c4 | include  s12 c5 | LLM-Augmented Academic Administration: A Role-Aware Architecture for S |
| openalex:W7142602175 | exclude no_harness_description s7 c5 | include  s12 c2 | Cognate: A Controller-Based Cognitive Architecture for Experience-Guid |
| openalex:W7147346078 | include  s12 c11 | exclude out_of_scope s2 c5 | MASLM: Multi-Agent System for Library Migration |
| openalex:W7147625625 | include  s12 c6 | exclude out_of_scope s2 c3 | Automatic Scaling Mechanism for LLM Multi-Agent Systems: Peristaltic C |
| openalex:W7148391534 | exclude no_harness_description s7 c4 | include  s12 c5 | BioGAIP: A Scalable, User-Friendly and Robust LLM-Powered Multi-Agent  |
| openalex:W7149471451 | exclude out_of_scope s3 c6 | include  s12 c5 | The Experience Provides the Stimulus: How LLM Agents Learn to Stop Pro |
| openalex:W7153550998 | exclude no_harness_description s7 c4 | include  s12 c5 | Deliberation and Exploration: A Dual-Mode Cognitive Architecture for M |
| openalex:W7154336515 | exclude no_harness_description s7 c3 | include  s12 c3 | OphAgent: A Generalisable Ophthalmic Agentic System for Global Eye Car |
| openalex:W7154505765 | exclude out_of_scope s3 c3 | include  s12 c4 | Self-Play Harness for Cross-Domain Knowledge Growth in Agentic LLM Sys |
| openalex:W7160703631 | exclude out_of_scope s3 c8 | include  s12 c10 | LeJEPA + I-JEPA: A World-Model-Grounded Multi-Agent Framework for Medi |
| openalex:W7160980456 | include  s12 c7 | exclude no_harness_description s1 c1 | Harnessing AI for Scalable Analysis of Simulation Data |
| openalex:W7161578727 | include  s12 c15 | exclude no_harness_description s1 c1 | Agentic AI in Enterprise Integration: A Governed Multi-Agent Architect |
| openalex:W7162129998 | include  s12 c24 | exclude duplicate_system s10 c10 | ybkim95/agent-scaling: v2.1.0 |
| openalex:W7162187778 | include  s12 c26 | exclude out_of_scope s2 c11 | SecureAgent: A Multi-Agent Large Language Model Framework for Context- |
| openalex:W7162770570 | exclude no_harness_description s7 c5 | include  s12 c6 | LiNDA OS: A Deterministic Multi-Agent Cognitive Architecture with Hybr |
| openalex:W7162938990 | exclude out_of_scope s5 c2 | include  s12 c4 | SHARD: Composable Infrastructure for Self-Healing, Persistent LLM Agen |
| openalex:W7163564845 | exclude out_of_scope s2 c6 | include  s12 c17 | LLM-Guided Digital Twin Agents for Autonomous Threat Detection and Res |
| openalex:W7163638919 | exclude no_harness_description s7 c8 | include  s12 c9 | DAIDALOS OS: An Autonomous Multi-Agent Pipeline for Deterministic Code |
| openalex:W7163809406 | exclude no_harness_description s7 c4 | include  s12 c5 | VIBE SHIELD - Agentic Evolving Guard Intelligence System (AEGIS) For W |
| openalex:W7164673764 | include  s12 c10 | exclude out_of_scope s5 c6 | Public GYE Explorer |
| openalex:W7164821032 | exclude no_harness_description s7 c4 | include  s12 c3 | PIA/DMA: Persistent Identity and Dual-Mode Autonomous Scheduling for L |
| openalex:W7165029308 | exclude out_of_scope s3 c6 | include  s12 c7 | Distributed Cognitive Architectures (DCA) — Theory I: Atomic Agents ·  |
| openalex:W7165445438 | exclude out_of_scope s5 c4 | include  s12 c5 | DROS for Shielding Prompt Contamination and Hallucination: Runtime Gov |
| openalex:W7165466906 | exclude out_of_scope s5 c5 | include  s12 c6 | Neutralizing Prompt Injection and LLM Hallucinations: The Deterministi |
| openalex:W7165532782 | exclude no_harness_description s7 c3 | include  s12 c6 | Blue Synergy Core: A Decoupled, Multi-Agent Cognitive Platform with Ze |
| openalex:W7165543356 | include  s12 c6 | exclude out_of_scope s2 c3 | SERTG: Test Script Generation for Domain-Specific Software via Summary |
| openalex:W7165973887 | exclude no_harness_description s7 c5 | include  s12 c7 | Automated Power BI report generation using an event-driven agentic wor |
| openalex:W7166540766 | exclude no_harness_description s7 c4 | include  s12 c11 | An agentic framework for multi-modal content generation |
| openalex:W7167211500 | exclude no_harness_description s7 c4 | include  s12 c5 | DevAI: Multi-agent Co-pilot for Intelligent Assistance in Software Dev |
| openalex:W7167253045 | include  s12 c14 | exclude out_of_scope s2 c6 | Chasing ABPMS Vision: The BAB Framework Approach for LLM Agents Over M |
| openalex:W7167362546 | exclude out_of_scope s3 c5 | include  s12 c7 | School of Specialists (SoS): A Network-First Architecture for Right-Si |
| openalex:W7167459595 | exclude out_of_scope s2 c4 | include  s12 c4 | Enhancing LLM-Based Proof Synthesis for Rust Programs via Semantic Chu |
| openalex:W7167479635 | exclude no_harness_description s7 c5 | include  s12 c6 | APT-Agent: A Training-Free, Unsupervised, LLM-Based Multi-agent Framew |
| openalex:W7168026747 | include  s12 c5 | exclude out_of_scope s5 c3 | Domain Adaptation of MLLM-Based GUI Agents in Documentation-Rich Envir |
| openalex:W7168087887 | exclude no_harness_description s7 c5 | include  s12 c5 | AutoCode4HW: Knowledge-Graph Enhanced Multimodal LLM Agents for Genera |
| openalex:W7168185695 | include  s12 c19 | exclude out_of_scope s5 c11 | Shared Selective Persistent Memory for Agentic LLM Systems |
| openalex:W7169649420 | include  s12 c7 | exclude out_of_scope s5 c4 | State-Control Architecture: Deterministic Context Management for LLM A |
| openalex:W7169844055 | include  s12 c19 | exclude out_of_scope s2 c12 | RECON: A Recipe-Driven, Evidence-Fused, Neuro-Symbolic Multi-Agent Arc |
| openalex:W7169845775 | exclude no_harness_description s7 c6 | include  s12 c4 | TerriScan audit bundle — doctrine-governed multi-agent LLM production  |
| openalex:W7170034797 | include  s12 c7 | exclude duplicate_system s10 c2 | From Resonance to Rigor: A Longitudinal Case Study of Multi-Model LLM  |
| openalex:W7170060653 | include  s12 c19 | exclude out_of_scope s5 c11 | Decision Intelligence Runtime (DIR) - Reference Implementation |
| openalex:W7171050850 | include  s12 c22 | exclude out_of_scope s2 c11 | Tomobit: a Living Harness that learns which AI to trust, in which cont |
| openalex:W7172070528 | exclude no_harness_description s7 c2 | include  s12 c3 | Assessing the Validity of Large Language Models as Synthetic Survey Re |
| openalex:W7172225937 | exclude no_harness_description s7 c4 | include  s12 c3 | MileGraph: Flexible Task Control via Milestone-Guided Hierarchical Pla |
| openalex:W7172413477 | include  s12 c5 | exclude out_of_scope s2 c2 | TruthLens: An Explainable Multi-Agent Framework for Hallucination Dete |
| openalex:W7172574914 | exclude no_harness_description s7 c4 | include  s12 c5 | Large Language Model Agents in Dynamic Mine Planning: A Modular Decisi |
| openalex:W7202041694 | include  s12 c6 | exclude out_of_scope s2 c5 | Propose, Judge, Commit: Ternary Verdicts with External State Authority |
| openalex:W7202059996 | exclude no_harness_description s7 c5 | include  s12 c8 | From Legacy to Reactive: Interpreting Source Code into Requirements fo |
| openalex:W7202178008 | include  s12 c6 | exclude out_of_scope s2 c2 | Beyond Scale, Agents, and Embodiment: Governed Experience Compounding  |
| openalex:W7202192482 | exclude no_harness_description s7 c4 | include  s12 c3 | Applying Large Language Model (LLM) Agents for Automated Lifelog Retri |
| openalex:W7203466707 | include  s12 c9 | exclude out_of_scope s2 c3 | SCU3.0 Architecture and Extension Plan: Three-Dimensional Separation o |
| openalex:W7203499242 | include  s12 c6 | exclude no_harness_description s7 c0 | VibeGen: Autonomous Multi-Agent Swarm Orchestration and Deterministic  |
| openalex:W7203744066 | include  s12 c8 | exclude out_of_scope s3 c2 | RoCoMAP: A Role-Based Collaborative Multi-Agent Framework for Patent S |
| openalex:W7203879756 | exclude no_harness_description s7 c5 | include  s12 c7 | Evaluation of a Retrieval-Augmented AI Agent for Power Grid Switching  |
| openalex:W7204143120 | exclude no_harness_description s7 c4 | include  s12 c4 | Reinforcement Learning Enhanced LLM Agents for Complex Vehicle Routing |
| openalex:W7204772346 | exclude no_harness_description s7 c5 | include  s12 c7 | Contract-Grounded Cognitive Composition: Deterministic Topology, Inter |
| openalex:W7204913923 | include  s12 c5 | exclude no_harness_description s7 c2 | Verifiable Trust for Autonomous LLMs |
| openreview:9twwDW60Bw | include  s12 c12 | exclude out_of_scope s11 c3 | Self-Guided Hierarchical Exploration for Generalist Foundation Model W |
| openreview:EzpJxPDqXB | include  s12 c21 | exclude out_of_scope s3 c8 | MarketSim: Simulating Stock Markets with Large-Scale Generative Agents |
| openreview:GbYHY1RVUa | include  s12 c12 | exclude out_of_scope s2 c2 | Failure-Driven Workflow Refinement |
| openreview:Hl3HR6Scs2 | include  s12 c17 | exclude out_of_scope s11 c8 | UItron: Foundational GUI Agent with Advanced Perception and Planning |
| openreview:IljH2Bt6jO | include  s12 c9 | exclude out_of_scope s11 c4 | TRAINING A VISION-LANGUAGE MODEL FOR DIVERSE EXPLORATION IN OPEN GUI W |
| openreview:KPsrOYaU79 | include  s12 c19 | exclude out_of_scope s11 c10 | Salus: Strategic Diagnostic Testing for Complex Diagnosis via Multi-Ag |
| openreview:L9pTokEb8L | include  s12 c19 | exclude out_of_scope s11 c11 | Towards Specialized Web Agents Using Production-Scale Workflow Data |
| openreview:LOqTK59rxd | exclude out_of_scope s3 c7 | include  s12 c12 | Symbolic Planning Using LLM Agents: A Cut-Based Reprompting Approach |
| openreview:RiaCWdGVGk | include  s12 c13 | exclude out_of_scope s5 c6 | Improving Tool-Using Language Agents via MDL-Guided Rule Learning |
| openreview:SY78p0rIYt | include  s12 c11 | exclude out_of_scope s2 c7 | Automated Movie Generation via Multi-Agent CoT Planning |
| openreview:SzhezVoaNB | include  s12 c13 | exclude out_of_scope s3 c9 | Scenethesis: A Language and Vision Agentic Framework for 3D Scene Gene |
| openreview:ToP9Cr0PUq | exclude out_of_scope s2 c2 | include  s12 c11 | SATISFYING COMPLEX USER NEEDS: M^3 AGENT FOR CONVERSATIONAL MULTI-ITEM |
| openreview:gkG8JOOUF4 | include  s12 c17 | exclude out_of_scope s2 c6 | Adaptive Preference Arithmetic: Modeling Dynamic Preference Strengths  |
| openreview:jiNw5AgBbw | include  s12 c18 | exclude out_of_scope s5 c7 | Think Twice Before You Act: Protecting LLM Agents Against Tool Descrip |
| openreview:lNmZrawUMu | exclude out_of_scope s11 c12 | include  s12 c9 | AlphaAgentEvo: Evolution-Oriented Alpha Mining via Self-Evolving Agent |
| openreview:oycEeFXX74 | include  s12 c14 | exclude duplicate_system s10 c4 | SHELL GAMES: CONTROL PROTOCOLS FOR ADVERSARIAL AI AGENTS |
| openreview:p5B4ABjuT2 | include  s12 c11 | exclude out_of_scope s11 c8 | EVOLVING ROLLOUTS: Harnessing Historical Experience for Web Agent Evol |
| openreview:qXwVXj03nO | include  s12 c15 | exclude out_of_scope s2 c4 | A Collaborative Multi-Agent LLM Approach for Knowledge Graph Curation  |
| openreview:uhSqCIVc0B | include  s12 c15 | exclude out_of_scope s2 c5 | QiMeng-LibBench: Benchmarking LLM Agents for Library-Scale Cross-Archi |
| s2:03ebfea35124ed27f7f954332794209a96fff7c5 | include  s12 c18 | exclude out_of_scope s3 c6 | Game-Theoretic Multi-Agent Control for Robust Contextual Reasoning in  |
| s2:0a01a1a69372656eb45a882f62f645b8385946b3 | include  s12 c27 | exclude out_of_scope s8 c22 | You Don't Need To Stay in The Loop: An Agentic Robotics Loop for Robot |
| s2:155fcbe08b56fcddc5a17a9156d3d42153c5af19 | include  s12 c14 | exclude out_of_scope s2 c8 | NexusMind: Agentic AI Orchestration Model |
| s2:2856fc1cd03062c26baff261e0dd9aa1968cd799 | exclude no_harness_description s7 c3 | include  s12 c2 | FraudTrace: Verifying Fraudulent News to Prevent Online Scam Campaigns |
| s2:3299a327306f16e228e7f9258d866ad778828aee | exclude out_of_scope s2 c6 | include  s12 c8 | Lightweight Adaptive Topological Layout And Semantic Mapping in Vision |
| s2:34d84165c52054ea3e826ae0c3ad4990384d2cf8 | include  s12 c15 | exclude out_of_scope s3 c8 | A multi-agent GraphRAG framework for pharmacotherapy safety verificati |
| s2:4a0489402f8ff1d23294010e626947e87b8ad425 | include  s12 c4 | exclude out_of_scope s2 c2 | RESPOND: Realistic Environment Simulation of Population and Natural Di |
| s2:6080633c613ba9deada38a4b9e2687d036d07cff | include  s12 c7 | exclude out_of_scope s2 c7 | Intelligent Multi-Agent System for Research Automation |
| s2:63c8eab2d3170ae1a106b8fe8d96181ad7f95c2e | include  s12 c19 | exclude out_of_scope s3 c8 | Emergence of Social Norms in Generative Agent Societies: Principles an |
| s2:6d1f287a7b12bed6b8f799012ce1368be3fc9640 | include  s12 c19 | exclude out_of_scope s3 c10 | Casevo: A Cognitive Agents and Social Evolution Simulator |
| s2:78ebc17ae82ce25f63a424ab17b90d7d6fac0217 | include  s12 c12 | exclude out_of_scope s2 c5 | TrustTrade: Human-Inspired Selective Consensus Reduces Decision Uncert |
| s2:7b80f6b0ecb28bb72aefc920939805c3235545c7 | include  s12 c10 | exclude out_of_scope s2 c3 | Causal-Aware LLM Agents for PHM Co-Pilots: Health Monitoring and Inter |
| s2:7cbb1a73bb9583d516ace20f96d1e130fee05854 | include  s12 c17 | exclude out_of_scope s2 c12 | SuccessionAI: An Intelligent Multi-Agent System for Personalized Indiv |
| s2:7f102a8a58d331a142935e4af6397eb68d35c5ef | include  s12 c13 | exclude out_of_scope s2 c14 | Development and validation of a multi-agent AI pipeline for automated  |
| s2:8273b825a4c8ec77f8ac9ab379daafedea08554b | include  s12 c12 | exclude out_of_scope s3 c7 | Towards Transparent and Incentive-Compatible Collaboration in Decentra |
| s2:84d6cecc23c91609bef3fdc659996b4843b0b7f9 | exclude no_harness_description s7 c4 | include  s12 c4 | Multi-agent autonomous GeoAI framework for scalable and self-improving |
| s2:8eba6c41adb6db2bb0112724dbf7f3a5b40bb38c | include  s12 c21 | exclude out_of_scope s2 c12 | Bridging the Post-discharge Gap: A Traceable Multi-agent Framework for |
| s2:8faa9140f3b76a494c030fc5a14801dc283d0968 | exclude out_of_scope s8 c14 | include  s12 c10 | Augmenting large language models with psychologically grounded models  |
| s2:92dd049eee0eb48fa3ae3300d675b3cdd1f80b50 | include  s12 c15 | exclude out_of_scope s2 c8 | Surgical AI Copilot: Energy-Based Fourier Gradient Low-Rank Adaptation |
| s2:933cd65c17473a58b09e46602e6516873d40e5cc | exclude out_of_scope s3 c8 | include  s12 c12 | InEx: Hallucination Mitigation via Introspection and Cross-Modal Multi |
| s2:95264f2fd070e9ee21dd2d36196a69c91a63e852 | exclude out_of_scope s3 c6 | include  s12 c9 | TRADING GPT: MULTI-AGENT SYSTEM WITH LAYERED MEMORY AND DISTINCT CHARA |
| s2:97f29ad60653e3ebf502afb39d5bcbf825446bf8 | include  s12 c26 | exclude out_of_scope s2 c16 | RAGentA: Multi-Agent Retrieval-Augmented Generation for Attributed Que |
| s2:a90209620070c37a79c5c6138f2702adcc09f9a2 | include  s12 c16 | exclude out_of_scope s2 c8 | Multi-Agent Retrieval Augmented Generation System for Legal Applicatio |
| s2:a94ad4474cd0d695d00f4561fac9884896dc6f70 | exclude out_of_scope s3 c5 | include  s12 c13 | LLM-Enhanced Symbolic Control for Safety-Critical Applications |
| s2:ac74bf475c42057ef9e85b5ee48b0517c1a679a7 | include  s12 c21 | exclude out_of_scope s2 c10 | Evidence-in-the-Loop: Trace-Driven Optimization for Customer-Service L |
| s2:afd4f4171f99be0fe8c100cee4a5ff6e2de41ada | include  s12 c12 | exclude out_of_scope s2 c4 | ADCanvas: Accessible and Conversational Audio Description Authoring fo |
| s2:bd903d542d0c0a90fea25a0b670385c2b0410f26 | exclude out_of_scope s5 c9 | include  s12 c22 | Agentic Diagrammatica: Towards Autonomous Symbolic Computation in High |
| s2:bd998002160607cfb8d6fa5c8d6c0932ebb9b79e | include  s12 c9 | exclude out_of_scope s2 c7 | How Well Can Modern LLMs Act as Agent Cores in Radiology Environments? |
| s2:c01f82087d29cffe359d57b045d1863023ded4e0 | include  s12 c11 | exclude out_of_scope s2 c8 | LLandMark: A Multi-Agent Framework for Landmark-Aware Multimodal Inter |
| s2:cfe4fa474674f37e7d437e11006e6fe5d42384bc | include  s12 c9 | exclude out_of_scope s2 c5 | VERIFY-DD: An Evidence-Grounded Agentic AI Framework for Hallucination |
| s2:d3ff047355e7998a216f963fd926e97ba00db35d | include  s12 c11 | exclude out_of_scope s2 c4 | LLM-Empowered Agentic AI for QoE-Aware Network Slicing Management in I |
| s2:d5038559f5083ffca86baa818ad6d79d1fd665c7 | exclude out_of_scope s2 c7 | include  s12 c14 | AI-Powered Multi-Agent Personalized Trip Planning Platform Using LLMs, |
| s2:d7c4e98ab2dde39c264f2f9b4ba096862dd58335 | include  s12 c15 | exclude out_of_scope s2 c7 | EvoMDT: a self-evolving multi-agent system for structured clinical dec |
| s2:dbf32da69632bab08143d26cbc802e88e50b128b | include  s12 c13 | exclude out_of_scope s2 c10 | Skill-Based Autonomous Agents for Material Creep Database Construction |
| s2:e55362fa2060104f1bd22d52964967bcf3d4667b | include  s12 c27 | exclude out_of_scope s2 c12 | RefLens: End-to-End Evidence-Grounded Citation Verification with LLM A |
| s2:e80052b89aa35b2ee92677a588f92402f2f4d122 | exclude no_harness_description s1 c10 | include  s12 c14 | Agentic AI Modernization: Transforming Institutional Infrastructure Th |
| s2:e97ab13fb2a142c61a2c1192d097e98e6662a7ac | include  s12 c16 | exclude out_of_scope s2 c9 | Can Large Language Models Trade? Testing Financial Theories with LLM A |
| s2:edfa9e382f8ac89ce9bffe927832bb0da6b43627 | include  s12 c19 | exclude out_of_scope s2 c9 | LungCURE: Benchmarking Multimodal Real-World Clinical Reasoning for Pr |
| s2:ee7b13e777917f654cf8a4f2d8cb6da8daf72257 | include  s12 c18 | exclude out_of_scope s2 c6 | LangGraph-Orchestrated LLM Agents for Scalable Movie Knowledge Graphs  |
| s2:f617958fe0fc32bda1b915b79537857f033fd44f | exclude no_harness_description s7 c5 | include  s12 c5 | TRELLIS: a reinforcement learning–enhanced typed-anchor-graph architec |
| s2_snowball:02edeec830ee24acc90f1eb3b2f065ae8b7196b9 | include  s12 c23 | exclude out_of_scope s5 c16 | PatchWrite: One Line, Not One Section — Compile-Gated, Validity-Preser |
| s2_snowball:07cf296e70b789ce6a57c0f33318d1a14fc295ce | include  s12 c13 | exclude duplicate_system s10 c2 | When Is Enough Not Enough? Illusory Completion in Search Agents |
| s2_snowball:0c4af47e57ef2d4b78867f84bdc8c0df32fdfd89 | exclude out_of_scope s11 c12 | include  s12 c12 | WikiLoop: Jointly Learning to Build and Navigate Agent-Native Wikis wi |
| s2_snowball:0d97cf488300377dede62e0855aa678161c14635 | include  s12 c13 | exclude out_of_scope s5 c8 | Toward Exascale AI for Science: A Scalable AI Skill for Autonomous Mic |
| s2_snowball:0fe1a9e4709ff44054fc68c24b5fbc516de8ab4b | include  s12 c16 | exclude duplicate_system s10 c3 | Grounding LLM Reasoning with Knowledge Graphs |
| s2_snowball:10ea2571b0950a1af3a3ff33a91dde7cb8ad716f | include  s12 c12 | exclude duplicate_system s10 c1 | REPOMIRAGE: Probing Repository Context Reasoning in Code Agents with P |
| s2_snowball:125d40a7ffed39475123ba13479e6245c32eeece | include  s12 c12 | exclude out_of_scope s2 c11 | ProgramTab: Boosting Table Reasoning of LLMs via Programmatic Paradigm |
| s2_snowball:15a073f6f8db724b10fe88c02b4da5bac3d85165 | include  s12 c13 | exclude out_of_scope s5 c7 | Beyond Textual Repository Exploration: Dual-Modal Structural Reasoning |
| s2_snowball:16b3d17621c7063738d1bfc7aa38489ae38b015e | include  s12 c17 | exclude out_of_scope s2 c1 | EarthVerse: Benchmarking Scientific Agents Across Dynamic Earth System |
| s2_snowball:1790009da85b88c150d745b6a083fc3b1650a870 | include  s12 c17 | exclude out_of_scope s11 c7 | Dynamic Skill Lifecycle Management for Agentic Reinforcement Learning |
| s2_snowball:17be7f076d70be99b4c3c531b0816901543d7981 | include  s12 c13 | exclude out_of_scope s5 c8 | Mechanistic Attention Guidance for Agent Memory Refinement |
| s2_snowball:18bae6292176eab10aca54065add84dd438c1288 | include  s12 c15 | exclude out_of_scope s5 c8 | PRIME: Training Free Proactive Reasoning via Iterative Memory Evolutio |
| s2_snowball:1971405a882f7f77cda06eff65f2b1005090acea | exclude out_of_scope s11 c7 | include  s12 c10 | VeriOS: Query-Driven Proactive Human-Agent-GUI Interaction for Trustwo |
| s2_snowball:1bfe92dfee18b56d11cf27044b431aa97a6acf70 | include  s12 c18 | exclude out_of_scope s5 c8 | Ask the World Before Acting: Environment Probing for Calibrated Agent  |
| s2_snowball:1c259361caa85c2d95a7d04e5e42fa98693da85b | include  s12 c19 | exclude out_of_scope s3 c7 | Large Language Models as Evolutionary Optimizers |
| s2_snowball:1c531773db902aa0fc523e9566fae31344b6fab6 | include  s12 c15 | exclude out_of_scope s11 c4 | ABBEL: Learning Natural-Language Belief States for Memory-Efficient In |
| s2_snowball:1c9f28d97dca913cbf977fcc14f8a45faac7e9f2 | exclude no_harness_description s1 c9 | include  s12 c15 | Agentic Diagnostic Reasoning over Telecom and Datacenter Infrastructur |
| s2_snowball:1e98a9532d4e1fcf947d5b215e2cfabbf6cc41e0 | exclude out_of_scope s8 c9 | include  s12 c13 | TREE-PLANNER: EFFICIENT CLOSE-LOOP TASK PLANNING WITH LARGE LANGUAGE M |
| s2_snowball:1f3dafc54c504537210f75174180cc07e39b8a65 | include  s12 c11 | exclude out_of_scope s2 c5 | Epistemic Closure: Autonomous Mechanism Completion for Physically Cons |
| s2_snowball:1fc366e80c6d91ec17531145c176d8e548031280 | exclude out_of_scope s2 c5 | include  s12 c7 | An Explainable Multimodal Vision Transformer Framework with Agentic AI |
| s2_snowball:2060bc4630167d873d626967b340edddb346c545 | include  s12 c16 | exclude out_of_scope s11 c4 | ProMMSearchAgent: A Generalizable Multimodal Search Agent Trained with |
| s2_snowball:2115f8185f8b126a30bb0c7e453ee39b2d611727 | include  s12 c11 | exclude out_of_scope s2 c7 | Vinedresser3D: Agentic Text-guided 3D Editing |
| s2_snowball:266a13a98fd271fc5f76acbdc1e155c18b6fc298 | include  s12 c10 | exclude out_of_scope s2 c7 | APQF: Agentic Profiling-Guided Structured Pruning and Mixed-Precision  |
| s2_snowball:26d932590eb7e4f36e2b7c262e0a43dd7268830c | include  s12 c13 | exclude out_of_scope s2 c12 | Question-Aware Evidence Ledgers for Video Relational Reasoning |
| s2_snowball:2897abb396eae57f4935d110e050e5a7784ba397 | exclude out_of_scope s11 c6 | include  s12 c7 | IACM-RL: Intent-Aware Context Management and Reinforcement Learning fo |
| s2_snowball:299ec08b60dbb993f96cf45c011c387477e3f9c8 | include  s12 c11 | exclude out_of_scope s3 c4 | Automatic Red Teaming LLM-based Agents with Model Context Protocol Too |
| s2_snowball:2a7720c878c20ed21608978e31507ca9d9936d1c | include  s12 c13 | exclude out_of_scope s3 c4 | SEAKR: Self-aware Knowledge Retrieval for Adaptive Retrieval Augmented |
| s2_snowball:2b6474c561d5c6792af0acdc72240ce3cbf5fb15 | include  s12 c19 | exclude out_of_scope s5 c9 | EscapeCraft: A 3D Room Escape Environment for Benchmarking Complex Mul |
| s2_snowball:2d0971511b5459352ef3dc6e4f2295b328de5370 | include  s12 c20 | exclude out_of_scope s11 c9 | DeepDive: Advancing Deep Search Agents with Knowledge Graphs and Multi |
| s2_snowball:2d427ff2eabde83312b12c7682f4baa7aa4ee3ad | include  s12 c13 | exclude duplicate_system s10 c0 | Exploring ReAct Prompting for Task-Oriented Dialogue: Insights and Sho |
| s2_snowball:2dc1c6fca791d06a1c6e0d3ccf567da2dd4835ee | include  s12 c15 | exclude out_of_scope s3 c11 | CyberJustice Tutor: An Agentic AI Framework for Cybersecurity Learning |
| s2_snowball:2e17ce9b323ac4599bc9221ccb7a1ed928e21aee | include  s12 c17 | exclude out_of_scope s5 c7 | Intent-Driven Situation Tracking for User-Centric Multi-Turn Agents |
| s2_snowball:2ebcc7ea5a284a18968a515dc2c88ebb9e3af52b | include  s12 c10 | exclude out_of_scope s2 c7 | ChatGraph: Chat with Your Graphs |
| s2_snowball:306f46d1287351365e398a59960ab05f8cd1ab23 | include  s12 c17 | exclude out_of_scope s5 c8 | PREPING: Building Agent Memory without Tasks |
| s2_snowball:3072ad4982cd916606ac88ea1883d4d725c4eda4 | include  s12 c19 | exclude out_of_scope s2 c7 | AGENTGYM: Evolving Large Language Model-based Agents across Diverse En |
| s2_snowball:31b44ae603a6b6568f9e9d949cd2711df3678096 | exclude out_of_scope s5 c9 | include  s12 c7 | Sutradhara: An Intelligent Orchestrator-Engine Co-design for Tool-base |
| s2_snowball:320dff4ab4af703999f49b7c2394ac589b673088 | include  s12 c14 | exclude out_of_scope s2 c5 | StarBench: A Turn-Based RPG Benchmark for Agentic Multimodal Decision- |
| s2_snowball:3221180558265e528a81e26891ab54dad5c2cb97 | include  s12 c13 | exclude out_of_scope s2 c10 | AutoM3L: An Automated Multimodal Machine Learning Framework with Large |
| s2_snowball:3254af2440a22ad79b8aa5c99366b41ada1d9bbc | include  s12 c12 | exclude out_of_scope s2 c5 | “I Want It That Way”: Enabling Interactive Decision Support Using Larg |
| s2_snowball:3268c1a172d6e6aa3769b7e9aebdebbd630bc64f | include  s12 c18 | exclude out_of_scope s2 c7 | ShortcutsBench: A Large-Scale Real-world Benchmark for API-based Agent |
| s2_snowball:3310af14d6bca10061fd911838e85aeb7e4d1f22 | include  s12 c20 | exclude out_of_scope s5 c10 | Stop-RAG: Value-Based Retrieval Control for Iterative RAG |
| s2_snowball:33eed6ea6805b59617fed7c41ef5825b5e4d1621 | include  s12 c12 | exclude out_of_scope s2 c9 | TPTU-v2: Boosting Task Planning and Tool Usage of Large Language Model |
| s2_snowball:3496c072397fe185c48b83f9b91aa8d5a52bcb87 | exclude out_of_scope s3 c12 | include  s12 c15 | AdaRefiner: Refining Decisions of Language Models with Adaptive Feedba |
| s2_snowball:34f72306da1ab04d9256c64175f1fc6f1e552b3e | include  s12 c13 | exclude out_of_scope s2 c4 | SPICE: An Automated SWE-Bench Labeling Pipeline for Issue Clarity, Tes |
| s2_snowball:3a1b0c059cd499eaa0de6e2ac0de15cd69d7de29 | include  s12 c16 | exclude out_of_scope s2 c6 | Optimizing Life Sciences Agents in Real-Time using Reinforcement Learn |
| s2_snowball:3db608b3377818c7ccef7945ea3f92b8bbaa1c54 | include  s12 c19 | exclude out_of_scope s2 c8 | Open Security Benchmark: Towards Autonomous Enterprise Cyber Defense |
| s2_snowball:3e692f4c9ffec5c30b370142a576af0d9ac005b7 | include  s12 c15 | exclude out_of_scope s11 c5 | ECHO: Prune to act, trace to learn with selective turn memory in agent |
| s2_snowball:3e6c37f2b70f9ba232d8a50f1e8cac2f9f6984e7 | include  s12 c15 | exclude out_of_scope s11 c7 | QuarkMedSearch: A Long-Horizon Deep Search Agent for Exploring Medical |
| s2_snowball:3eb25b4eb27808f9a6c619cdcd764140d691dea8 | exclude out_of_scope s5 c5 | include  s12 c17 | From Exploration to Mastery: Enabling LLMs to Master Tools via Self-Dr |
| s2_snowball:3eefee2bb745762ba6e8eacc2f38ab8f8839d62f | include  s12 c11 | exclude out_of_scope s2 c8 | Bridge the Last-Mile Gap to Semantic Analytics: Compiling Natural-Lang |
| s2_snowball:3fe940a1f121f083cb90c568fc6fa2951bb27dda | include  s12 c13 | exclude out_of_scope s2 c6 | Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generati |
| s2_snowball:40776e2aba7dd99d2dadc993e370a0592a750cb3 | include  s12 c13 | exclude out_of_scope s2 c2 | From Prediction to Prescription: Large Language Model Agent for Contex |
| s2_snowball:40a7e877cb4d60599a6dafef5487d75018a70fd7 | include  s12 c11 | exclude out_of_scope s11 c5 | COMPUTERRL: SCALING END-TO-END ONLINE REINFORCEMENT LEARNING FOR COMPU |
| s2_snowball:40d2a94eafbe4100269fe85ac2803a0e8d374e5f | include  s12 c18 | exclude out_of_scope s2 c8 | TRACE-QA: Task-routed constraint elimination for auditable multi-agent |
| s2_snowball:4112104eb14c98cbfd08f20112bc86e25334ca00 | include  s12 c24 | exclude out_of_scope s11 c12 | Scaling Agentic Reinforcement Learning for Tool-Integrated Reasoning i |
| s2_snowball:42ed2516e0895da4c4863dcbf47fd1496380730c | exclude out_of_scope s2 c7 | include  s12 c12 | Enhancing repository-level software repair via repository-aware knowle |
| s2_snowball:471cfc2e3239ee4e67591a8b765a27248d6a60a8 | include  s12 c11 | exclude out_of_scope s2 c8 | Solving General Natural-Language-Description Optimization Problems wit |
| s2_snowball:49bcb213722c17e52819d3398218b924eadf42c4 | include  s12 c16 | exclude out_of_scope s5 c12 | You Live More Than Once: Towards Hierarchical Skill Meta-Evolving |
| s2_snowball:4c0e15901a64698d70dd4ffb8b882bbc0846cf5e | include  s12 c11 | exclude duplicate_system s10 c0 | Rethinking Experience Utilization in Self-Evolving Language Model Agen |
| s2_snowball:4d58325ceeeb5cdbc4638dccad53a96d558c04f6 | include  s12 c17 | exclude out_of_scope s2 c9 | PhishAgent: A Robust Multimodal Agent for Phishing Webpage Detection |
| s2_snowball:4e112479c28ed33fd291a672d539b098d6684f00 | include  s12 c19 | exclude out_of_scope s2 c7 | Boosting the Potential of Large Language Models with an Intelligent In |
| s2_snowball:4fc87dc2ac306a1527c60f3cd55534d412de078b | include  s12 c15 | exclude out_of_scope s2 c5 | Tree-of-Reasoning Question Decomposition for Complex Question Answerin |
| s2_snowball:50005db6732784a1f1ef816900d55db9915867e5 | include  s12 c20 | exclude out_of_scope s11 c5 | MAS-Orchestra: Understanding and Improving Multi-Agent Reasoning Throu |
| s2_snowball:510682c34bef8a0fda851fe6633b1d93cb74b76e | include  s12 c15 | exclude out_of_scope s3 c6 | DQA: Diagnostic Question Answering for IT Support |
| s2_snowball:5115942664d75d29f9f2814d89211af6a169ab05 | include  s12 c14 | exclude out_of_scope s11 c6 | NNetNav: Unsupervised Learning of Browser Agents Through Environment I |
| s2_snowball:53fc0cf46460706d549bea199095a2d3c06eda29 | include  s12 c15 | exclude out_of_scope s5 c10 | A Case for Agentic Tuning: From Documentation to Action in PostgreSQL |
| s2_snowball:550f6ebd4d60d5e5bb1be68330362c4314971dcd | include  s12 c19 | exclude duplicate_system s10 c0 | VAKRA: Evaluating Multi-Hop Reasoning Across APIs and Retrieval Under  |
| s2_snowball:55be92434d1140c4308e8a54e8c14cdc2eaeb613 | exclude out_of_scope s2 c8 | include  s12 c13 | AgenticRAG: Tool-Augmented Foundation Models for Zero-Shot Explainable |
| s2_snowball:58b6dcf1d574e1da64cdf5211ab6b3d27a43ebc6 | include  s12 c17 | exclude out_of_scope s5 c15 | From Neural Intent to Cryptographic Authorization: Securing AI-Driven  |
| s2_snowball:59a87c40c1f9747cadc83ec8e19f4cd0c4f1d048 | exclude out_of_scope s11 c9 | include  s12 c8 | IntPro: A Proxy Agent for Context-Aware Intent Understanding via Retri |
| s2_snowball:5cce9e65ac43a91cd69538761f1cab900b547405 | include  s12 c12 | exclude out_of_scope s2 c6 | From GUI Tests to Conversational Interaction: A New Perspective on App |
| s2_snowball:5d79598a86cc3df7a2641dd6aa2439cef29ec782 | include  s12 c15 | exclude duplicate_system s10 c4 | Recovering Wasted Compute in Autoresearch Agents |
| s2_snowball:6301743a104da2ffee26469690640f7373972ca7 | include  s12 c22 | exclude out_of_scope s11 c8 | Waking Up Blind: Cold-Start Optimization of Supervision-Free Agentic T |
| s2_snowball:645ea8d2d1e412551a3d55a55b857b35987f6b1b | include  s12 c13 | exclude duplicate_system s10 c0 | From Agent Loops to Deterministic Graphs: Execution Lineage for Reprod |
| s2_snowball:649058f9e736232ba5f5b7ed384cdbcb51b7d042 | include  s12 c13 | exclude out_of_scope s2 c7 | BENCHMARKING MOBILE DEVICE CONTROL AGENTS ACROSS DIVERSE CONFIGURATION |
| s2_snowball:666a88cc754e1090fd38addfba70fbb30ffb737a | include  s12 c22 | exclude out_of_scope s3 c10 | Beyond Chunks and Graphs: Retrieval-Augmented Generation through Tripl |
| s2_snowball:696782b3cea9d571ee1f71e009ea06b926864b3d | include  s12 c18 | exclude out_of_scope s2 c6 | A-MAR: Agent-based Multimodal Art Retrieval for Fine-Grained Artwork U |
| s2_snowball:69deb977c72bb6b1b0513e020f81f21395d0e54c | include  s12 c15 | exclude duplicate_system s10 c2 | AI Scientists Are Only as Good as Their Evidence: A Stratified Ablatio |
| s2_snowball:6c95608b50d360fc9b2043d5caf89ce804ed5696 | include  s12 c24 | exclude out_of_scope s2 c4 | PrivacyLens: Evaluating Privacy Norm Awareness of Language Models in A |
| s2_snowball:6dcf0119d44c5ca2be51751e7ad6b24fe684e5d8 | include  s12 c13 | exclude out_of_scope s8 c4 | An Agentic Pipeline for Natural Language-Driven Robot Simulation Envir |
| s2_snowball:6dff0041c0ff72ab5828b105876e4d399183bef5 | include  s12 c16 | exclude out_of_scope s2 c7 | TALES: Text Adventure Learning Environment Suite |
| s2_snowball:6f6ad7cce8f47cf6c9f97d50deed618c46251f3f | exclude out_of_scope s2 c1 | include  s12 c2 | ChatTwin: Enabling Natural Language Interactions with Infrastructure D |
| s2_snowball:709f18b538642480baeb2b97c45341efe40f7320 | include  s12 c16 | exclude out_of_scope s2 c10 | OSCAR: Optimization-Steered Agentic Planning for Composed Image Retrie |
| s2_snowball:72fd3b18d3dd7100fe18639eb30c24a1996e65ef | include  s12 c21 | exclude out_of_scope s3 c20 | LLM-Steered Power Allocation for Parallel QPSK-AWGN Channels |
| s2_snowball:7394555bc2e803cc3b54a14ebadd6ff3096ebc75 | include  s12 c13 | exclude out_of_scope s2 c10 | Human-Agent Collaborative Paper-to-Page Crafting |
| s2_snowball:74b4dbd3fb7ef0cf5590a3845defad28b353fe7b | include  s12 c19 | exclude out_of_scope s2 c2 | SemPlan: Benchmarking Structured Semantic Planning for LLM-Based Queri |
| s2_snowball:74bb2ddd18635e1fd4a8b46b111caf387c0b12fd | include  s12 c16 | exclude out_of_scope s2 c6 | EO-Gym: A Multimodal, Interactive Environment for Earth Observation Ag |
| s2_snowball:770ea02c6906994742a70e2ede3e81c9adb4aeff | exclude out_of_scope s3 c9 | include  s12 c11 | EpiEvolve: Self-Evolving Agents for Streaming Pandemic Forecasting und |
| s2_snowball:77d871e44569ad38e88464421f81c627d8809af1 | include  s12 c12 | exclude out_of_scope s8 c8 | Large Language Models for Control |
| s2_snowball:7942253c4806b4f1200515a95a743313c1ee10bb | include  s12 c12 | exclude duplicate_system s10 c4 | An Empirical Study on Failures in Automated Issue Solving |
| s2_snowball:7960db210436c75c4d877d8f9b9452451fa4018c | include  s12 c20 | exclude out_of_scope s11 c3 | From Self-Evolving Synthetic Data to Verifiable-Reward RL: Post-Traini |
| s2_snowball:7aad335d1a4c7154583e87d9996b51045512efb2 | include  s12 c14 | exclude duplicate_system s10 c4 | From Natural Language to Control Signals: A Conceptual Framework for S |
| s2_snowball:7c428255710646035f55c4f8658e24db657cf5c3 | include  s12 c15 | exclude out_of_scope s5 c9 | Polymer-Agent: Large Language Model Agent for Polymer Design |
| s2_snowball:7cf8351bc69a2c356528cbfca441a304d425020a | include  s12 c11 | exclude out_of_scope s5 c6 | CONTRAMEM: Learning Self-Evolving Procedural Memory from Contrasting M |
| s2_snowball:7cfdad882beaf3fbc588536c0a5194df2ab33a3e | include  s12 c16 | exclude out_of_scope s8 c11 | STMA: A Spatio-Temporal Memory Agent for Long-Horizon Embodied Task Pl |
| s2_snowball:7f5120db8f2ed7665bbfbff6f04e3e46fb7e0be9 | exclude out_of_scope s11 c0 | include  s12 c19 | Large Action Models: From Inception to Implementation |
| s2_snowball:7ff1a721846c7b157214001fd598df4a33fbbfe3 | include  s12 c18 | exclude out_of_scope s2 c4 | MobileSafetyBench: Evaluating Safety of Autonomous Agents in Mobile De |
| s2_snowball:83bef919fd8f3e97e47ababd6dcda4097fe3bbc5 | include  s12 c19 | exclude out_of_scope s3 c12 | Select-Then-Decompose: From Empirical Analysis to Adaptive Selection S |
| s2_snowball:87e2b0fa4194609fb9c08d4c13c9e97479973043 | include  s12 c20 | exclude out_of_scope s2 c9 | PresentAgent: Multimodal Agent for Presentation Video Generation |
| s2_snowball:8b0c7652b31f50f2e36cf3a729917d947d82b5e8 | include  s12 c13 | exclude out_of_scope s5 c6 | From Faulty Memories to Corrected Actions: Dependency-Guided Rollback  |
| s2_snowball:8f37a586e2901f87b0be012e238c5ea27a880a53 | exclude out_of_scope s3 c7 | include  s12 c9 | Single-agent vs. Multi-agents for Automated Video Analysis of On-Scree |
| s2_snowball:926525b978ff0dfb54be8e5602b1f61991e09c96 | include  s12 c14 | exclude out_of_scope s3 c8 | ReflecSched: Solving Dynamic Flexible Job-Shop Scheduling via LLM-Powe |
| s2_snowball:97afc428341eca1011a142daf269c9b01230f410 | include  s12 c14 | exclude out_of_scope s3 c7 | Reverse Chain: A Generic-Rule for LLMs to Master Multi-API Planning |
| s2_snowball:9a793119e2e13fb15de3782eae64317c543fe566 | include  s12 c14 | exclude out_of_scope s2 c9 | ECO: An AI-Driven Code Efficiency Optimizer for Warehouse Scale Comput |
| s2_snowball:9bf0567e0e40eff96af5ce1ee28aed8a5a487b82 | include  s12 c14 | exclude out_of_scope s5 c11 | From Historical Patches to Repair Plans: Outcome-Conditioned Reasoning |
| s2_snowball:9c03c7b9ae5bc182134edd736c6d48946f4aaaaf | include  s12 c22 | exclude out_of_scope s5 c16 | ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory |
| s2_snowball:9c52ab31f329f259a51e41323450f81de04ba234 | exclude out_of_scope s2 c5 | include  s12 c10 | Learning Project-wise Subsequent Code Edits via Interleaving Neural-ba |
| s2_snowball:9c96e104d7e1981b9bc8932cf3b28a370f79ce5e | include  s12 c10 | exclude out_of_scope s3 c9 | LRCTI: A Large Language Model-Based Framework for Multi-Step Evidence  |
| s2_snowball:9d54c1efee146e6984c13f575ae4fcad54a96afc | exclude out_of_scope s8 c10 | include  s12 c11 | Seeing Isn't Believing: Mitigating Belief Inertia via Active Intervent |
| s2_snowball:9e389211108432a0964d69bf8c783f19f713c344 | include  s12 c9 | exclude out_of_scope s2 c2 | Application of MATEC (Multi-AI Agent Team Care) Framework in Sepsis Ca |
| s2_snowball:9e89ff0aab4cfe683c6c434c4f684b550622da3b | include  s12 c17 | exclude out_of_scope s2 c8 | FUSE: Failure-aware Usage of Subagent Evidence for MultiModal Search a |
| s2_snowball:a2b5d282a3723600c31a56dc38082ea720315ac7 | include  s12 c29 | exclude out_of_scope s5 c12 | AgentRadio: Passive Awareness for Long-Horizon Multi-Agent Collaborati |
| s2_snowball:a3393690aab9e45f7ebdfd290a4a69859b387dd5 | include  s12 c17 | exclude out_of_scope s2 c5 | ENTERPRISEOPS-GYM: Environments and Evaluations for Stateful Agentic P |
| s2_snowball:a54fa51e792aa255c04e1c58e8a4e2dde9768b88 | include  s12 c12 | exclude out_of_scope s3 c5 | Causal-aware Large Language Models: Enhancing Decision-Making Through  |
| s2_snowball:a629e06280ae5764a8fc3e6a46d9fece6641c6f5 | include  s12 c12 | exclude out_of_scope s3 c7 | D2F-ReAG: Dynamic Decomposition and Filtering for Multi-Hop Reasoning- |
| s2_snowball:a9e4c7ef528acb31e7be91eae811ef1e6fbf8e8b | include  s12 c13 | exclude out_of_scope s8 c9 | City Navigation in the Wild: Exploring Emergent Navigation from Web-Sc |
| s2_snowball:ab786c97fe7dc1e989403a9e5878141afb1fccfa | include  s12 c26 | exclude out_of_scope s2 c16 | RepoReviewer: A Local-First Multi-Agent Architecture for Repository-Le |
| s2_snowball:af5e693960bba9748bbe9ab776712af7742cee8f | include  s12 c13 | exclude out_of_scope s5 c11 | Reducing Cost of LLM Agents with Trajectory Reduction |
| s2_snowball:b02e8ce41cab6656af38dc0d65b61f56bbb91072 | include  s12 c25 | exclude out_of_scope s6 c10 | SymbolicAI: A framework for logic-based approaches combining generativ |
| s2_snowball:b11cc2b7f3e53ffadeef5cbb7d6aab7c02788684 | include  s12 c20 | exclude out_of_scope s3 c9 | Execution Guided Line-by-Line Code Generation |
| s2_snowball:b173420ed0c6ec7db79b4424d9c5507ecc9aa0f9 | exclude out_of_scope s11 c10 | include  s12 c10 | Curriculum-Guided Reinforcement Learning for Efficient Multi-Hop Retri |
| s2_snowball:b2c9f9366e7be11d358e99192fe797dda7c2e76b | include  s12 c15 | exclude out_of_scope s5 c6 | Efficient On-Device Agents via Adaptive Context Management |
| s2_snowball:b716391ee541d4ebfedae3679739a8bff315d3fb | include  s12 c21 | exclude out_of_scope s5 c12 | SelfMem: Self-Optimizing Memory for AI Agents |
| s2_snowball:b724bc035a211d1fb1afccc558bc3421de51cb1f | include  s12 c15 | exclude out_of_scope s2 c6 | Language Models Don't Know What You Want: Evaluating Personalization i |
| s2_snowball:b84f8a3d6def86ae7c998fda7cfa549c233cadbc | include  s12 c17 | exclude out_of_scope s2 c8 | T1: A Tool-Oriented Conversational Dataset for Multi-Turn Agentic Plan |
| s2_snowball:bae8e0add41cdf7ae06f059241e8483e2ac61abe | include  s12 c14 | exclude out_of_scope s2 c14 | IC-EO: Interpretable Code-based assistant for Earth Observation |
| s2_snowball:c13d6e1569c9e98306a93eed8fa9dcd179b7201b | include  s12 c27 | exclude out_of_scope s2 c12 | Discovering Agentic Safety Specifications from 1-Bit Danger Signals |
| s2_snowball:c3f1c747db1918b5bf11a60081bfa9bf4a93c00b | include  s12 c16 | exclude out_of_scope s6 c10 | PPDL: LLM-Based Flows as Probabilistic Programs |
| s2_snowball:cb4887f4216fdd649b443311eac5576c350b8097 | include  s12 c12 | exclude out_of_scope s3 c7 | Textual-to-Visual Iterative Self-Verification for Slide Generation |
| s2_snowball:cf9f14adc07d511d59a8181a4f0b20a21de9c513 | include  s12 c16 | exclude out_of_scope s3 c10 | AI-DRIVEN DAY-TO-DAY ROUTE CHOICE |
| s2_snowball:cfcf8ab7c595c1849e8396167a29f3bd3359107c | include  s12 c11 | exclude out_of_scope s3 c4 | Agent Alignment in Evolving Social Norms |
| s2_snowball:d23864f4ccbff7bdac38df27a5e42ab325c37c89 | include  s12 c11 | exclude out_of_scope s11 c5 | IEA: Amateur-Friendly Conversational Image Editing Agent via Three Sta |
| s2_snowball:d2d8e17499982f61314952405038b45acdc13699 | include  s12 c9 | exclude out_of_scope s2 c5 | PaveBench: A Versatile Benchmark for Pavement Distress Perception and  |
| s2_snowball:d3b3482ca558641e7923bcf15858464e914c2f52 | include  s12 c24 | exclude out_of_scope s11 c14 | KnowCoder-A1: Incentivizing Agentic Reasoning Capability with Outcome  |
| s2_snowball:d6088529d15f384e69cbc5c0b4b67a3746ef163e | include  s12 c11 | exclude out_of_scope s3 c8 | Yo'City: Personalized and Boundless 3D Realistic City Scene Generation |
| s2_snowball:d71dacc73a423c735dfeb6abc09a311d3e7ab872 | include  s12 c12 | exclude out_of_scope s2 c7 | Tree-of-Ideas: Automated Research Ideation via Cross-Trajectory Reason |
| s2_snowball:dcb22b5924fb0ff6ef2b310eabfbea66682cca0b | exclude out_of_scope s8 c12 | include  s12 c7 | ITCMA: A Generative Agent Based on a Computational Consciousness Struc |
| s2_snowball:dd336bb6c7fdcd4d6d87b7525cb04dcc26d87fac | include  s12 c18 | exclude out_of_scope s5 c10 | ResearchStudio-Reel: Automate the Last Mile of Research from Paper to  |
| s2_snowball:de0dc75961366c9f38d02e227491d672a335d30e | exclude out_of_scope s3 c9 | include  s12 c12 | AB-RAG: Adaptive Budgeted Retrieval-Augmented Generation for Reliable  |
| s2_snowball:de3d79017865b98fece6ea9f7fbbaa6f0035acd4 | include  s12 c19 | exclude out_of_scope s2 c12 | Towards Agentic Runtime Healing |
| s2_snowball:e2e65dc8d997da994d88aba8d41e3bd6a5b3e328 | include  s12 c14 | exclude out_of_scope s11 c3 | DecomposeR: Planner-Centric Reinforcement Learning for Deep Research w |
| s2_snowball:e2f636ea5b04c8264142197d2dd98f3fad93b284 | include  s12 c19 | exclude out_of_scope s5 c2 | AgentWorld: Personality-Aware Reliability Evaluation for Agentic Infor |
| s2_snowball:e34768928bfb6a11647856f4751a4bf080d32118 | include  s12 c14 | exclude out_of_scope s2 c8 | RIZZ: Routing Interactions to Near Zero-Interference Zones for Continu |
| s2_snowball:e41482f4ee984f17382f6cdd900df094d928be06 | include  s12 c20 | exclude out_of_scope s2 c5 | WEBARENA: A REALISTIC WEB ENVIRONMENT FOR BUILDING AUTONOMOUS AGENTS |
| s2_snowball:e768ac48f31fc20d3b36946151a6a8c2cf9647c5 | include  s12 c16 | exclude out_of_scope s5 c7 | AI Research Preference Models |
| s2_snowball:e8ee8dc3a806495c6084389323ca09aca3238836 | include  s12 c20 | exclude out_of_scope s2 c5 | LangProp: A code optimization framework using Large Language Models ap |
| s2_snowball:e9084292886ec61ebeffb79b9ab62e004fda8205 | include  s12 c14 | exclude out_of_scope s2 c11 | QuantumMind: Constraint-Grounded Agentic Reasoning for Speedup Analysi |
| s2_snowball:e97167d88eee01ccd901c04ad63f22c64d1bfa8c | include  s12 c19 | exclude out_of_scope s3 c4 | FORMALJUDGE: A Neuro-Symbolic Paradigm for Agentic Oversight |
| s2_snowball:ec37ae28907638a87c8b229a296f57a6539e6838 | include  s12 c13 | exclude out_of_scope s3 c4 | BED-LLM: Intelligent Information Gathering with LLMs and Bayesian Expe |
| s2_snowball:ec46ec24c252cfa46a0d4a4128855b91cb7c5f31 | include  s12 c13 | exclude duplicate_system s10 c5 | Agent Privilege Separation in OpenClaw: A Structural Defense Against P |
| s2_snowball:f0497ee0afc1afbb6d44d5c34248cd29d6cefe75 | include  s12 c11 | exclude out_of_scope s2 c7 | Specializing Large Models for Oracle Bone Script Interpretation via Co |
| s2_snowball:f113cf61f49b1f85a1e9dc20d3d4e42a00917f68 | include  s12 c19 | exclude out_of_scope s2 c11 | Trident : How to Break Deep Reinforcement Learning Cyber Defenses (Age |
| s2_snowball:f16dcf47b70ea2d008c458892e5cfa393378da26 | include  s12 c14 | exclude out_of_scope s2 c6 | Q-Router: Agentic Video Quality Assessment with Expert Model Routing a |
| s2_snowball:f1f63620e87facef02234e82864c4b8adee081ec | include  s12 c19 | exclude out_of_scope s2 c8 | VisualAgentBench: Towards Large Multimodal Models as Visual Foundation |
| s2_snowball:f240aa06c6c0d4f250a6aaafbd9e2435af6be5ee | include  s12 c18 | exclude out_of_scope s5 c12 | MCP4IFC: IFC-Based Building Design Using Large Language Models |
| s2_snowball:f30d44d7a2143dd65fa14cde825f01b216a6a0eb | include  s12 c13 | exclude no_harness_description s2 c4 | Continuous Interaction Diffusion: A Diffusion-Native Runtime for Async |
| s2_snowball:f31f4b7c433b7fec98f7e6cf9fd88451e8e3fc28 | include  s12 c23 | exclude out_of_scope s2 c7 | Spider2-V: How Far Are Multimodal Agents From Automating Data Science  |
| s2_snowball:f53fb304adedf43791e967967761f306499c3d9b | include  s12 c16 | exclude out_of_scope s11 c7 | Skywork-R1V4: Toward Agentic Multimodal Intelligence through Interleav |
| s2_snowball:f807bac8eb55aa347303a2ae2b78ba71f43bc6cd | include  s12 c21 | exclude out_of_scope s2 c11 | OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Source |
| s2_snowball:f9a902a0c6549f708a50e3becce3c75abedfe7a6 | include  s12 c24 | exclude out_of_scope s11 c6 | HiPRAG: Hierarchical Process Rewards for Efficient Agentic Retrieval A |
| s2_snowball:fa8fa745f58d362925dd44f02750bab1b30a1189 | include  s12 c12 | exclude out_of_scope s8 c11 | RL-GPT: Integrating Reinforcement Learning and Code-as-policy |
| s2_snowball:fc55403e8d2d14516c8ec1b169a964c87a8b51d1 | include  s12 c13 | exclude out_of_scope s2 c7 | PhysMent: An Interactive Approach For LLM Reasoning In Physics Problem |
| s2_snowball:fe6e47d9279570d4eec086792994cf679be92c9d | include  s12 c22 | exclude out_of_scope s3 c12 | Explainable Innovation Engine: Dual-Tree Agent-RAG with Methods-as-Nod |
| s2_snowball:fe9e16938e57722d0ebce0fe3cda84f340853445 | exclude out_of_scope s6 c13 | include  s12 c10 | The Auton Agentic AI Framework |
| s2_snowball:ffea1f0412dfa8149535dbfc3ca0e94e629afad7 | include  s12 c13 | exclude out_of_scope s2 c3 | KernelBench: Can LLMs Write Efficient GPU Kernels? |
| survey_refs:openreview:eONq7FdiHa:77 | include  s12 c16 | exclude out_of_scope s6 c12 | github/gh-aw |
| survey_refs:preprints:202604.0428:163 | include  s12 c19 | exclude out_of_scope s3 c9 | AFLOW: AUTOMATING AGENTIC WORKFLOW GENERATION |
| survey_refs:preprints:202604.0428:170 | include  s12 c18 | exclude out_of_scope s6 c5 | harbor-framework/harbor |
| survey_refs:preprints:202604.0428:92 | exclude out_of_scope s3 c6 | include  s12 c14 | Identifying the Risks of LM Agents with an LM-Emulated Sandbox |

## 6. Reference sets

Positive set: 27 known harness systems.

Recall by stage:

- search: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- title_forward: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- fulltext_include: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- registry: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- coding_frame: 27/27 = 100.0% [95% CI 87.5%, 100.0%]

| system | candidate records | forwarded | pass-1 include records | in registry | in coding frame | mentioned in n records | lost at |
|---|---|---|---|---|---|---|---|
| ReAct | 9 | 7 | 9 | yes | yes: catalogue;peer_reviewed | 2462 | - |
| Reflexion | 4 | 4 | 1 | yes | yes: catalogue | 1049 | - |
| CodeAct | 2 | 2 | 3 | yes | yes: stars;catalogue | 129 | - |
| SWE-agent | 10 | 10 | 10 | yes | yes: stars;catalogue;vendor;peer_reviewed | 500 | - |
| OpenHands | 6 | 6 | 4 | yes | yes: stars;catalogue;vendor | 426 | - |
| AutoGen | 4 | 4 | 6 | yes | yes: stars;catalogue;vendor;peer_reviewed | 747 | - |
| MetaGPT | 1 | 1 | 3 | yes | yes: stars;catalogue;peer_reviewed | 613 | - |
| Agent S | 27 | 18 | 17 | yes | yes: catalogue;stars;catalogue;stars;catalogue;vendor;peer_reviewed | 84 | - |
| OS-Copilot | 2 | 2 | 2 | yes | yes: stars;catalogue | 26 | - |
| WebArena reference agent | 2 | 2 | 2 | yes | yes: catalogue | 4 | - |
| OSWorld reference agent | 3 | 3 | 4 | yes | yes: stars;catalogue;stars;catalogue;peer_reviewed | 2 | - |
| tau-bench reference agent | 5 | 4 | 28 | yes | yes: catalogue;vendor;stars;stars;catalogue;vendor;peer_reviewed | 2 | - |
| BrowserGym generic agent | 4 | 4 | 4 | yes | yes: stars;catalogue;stars;catalogue;vendor | 9 | - |
| mini-SWE-agent | 2 | 2 | 1 | yes | yes: catalogue | 123 | - |
| Aider | 4 | 3 | 3 | yes | yes: catalogue;vendor | 99 | - |
| Cline | 2 | 2 | 2 | yes | yes: catalogue;vendor | 30 | - |
| Codex CLI | 3 | 2 | 4 | yes | yes: stars;catalogue;vendor | 149 | - |
| Gemini CLI | 2 | 2 | 2 | yes | yes: catalogue;vendor | 91 | - |
| OpenCode | 4 | 3 | 3 | yes | yes: stars;catalogue;vendor | 168 | - |
| Moatless Tools | 1 | 1 | 1 | yes | yes: catalogue | 34 | - |
| Prometheus | 2 | 2 | 2 | yes | yes: stars;catalogue | 2 | - |
| Claude Code | 5 | 3 | 3 | yes | yes: stars;catalogue;vendor | 776 | - |
| Mistral Vibe | 2 | 2 | 2 | yes | yes: stars;catalogue;vendor | 2 | - |
| Hermes Agent | 1 | 1 | 1 | yes | yes: stars;catalogue | 46 | - |
| Pi | 2 | 2 | 3 | yes | yes: stars;catalogue;vendor | 51 | - |
| OpenClaw | 4 | 3 | 4 | yes | yes: catalogue;vendor | 213 | - |
| AIOS | 3 | 1 | 1 | yes | yes: stars;catalogue | 18 | - |

Negative set: 13 surveys, benchmarks and evaluation studies (expected exclude).

| record | candidate records | forwarded | full-text screened | full-text decision |
|---|---|---|---|---|
| Guo et al. survey | 1 | 0 | 0 | - |
| Li et al. Agent Harness Engineering survey | 0 | 0 | 0 | - |
| Meng et al. survey | 1 | 0 | 0 | - |
| Rombaut Inside the Scaffold | 1 | 0 | 0 | - |
| Barbaste Harness Engineering anatomy | 1 | 0 | 0 | - |
| Banu Harness Engineering as Categorical Architecture | 1 | 0 | 0 | - |
| Harness-Bench | 1 | 0 | 0 | - |
| SWE-bench | 1 | 0 | 0 | - |
| GAIA | 1 | 0 | 0 | - |
| Toolformer | 1 | 0 | 0 | - |
| Tree of Thoughts | 1 | 0 | 0 | - |
| The Scaffold Effect | 1 | 0 | 0 | - |
| Same Model Different Harness | 1 | 0 | 0 | - |

- Specificity at full text (negatives screened at full text and excluded): n/a (n = 0)

## 7. Time and cost

- pass 1: 8362 LLM records; busy wall time 131.1 min (union of batch intervals; effective concurrency 3.7); 0.9 s/record wall, 3.5 s/record serial; list-equivalent $554.74 = $0.066/record; tokens/record in 9890, out 554
- pass 2: 3063 LLM records; busy wall time 109.5 min (union of batch intervals; effective concurrency 4.7); 2.1 s/record wall, 10.0 s/record serial; list-equivalent $108.04 = $0.035/record; tokens/record in 5112, out 251

Projection to the whole queue (9967 records), from all pass-1 records and the measured rates:

- not retrievable: 0.9% of records -> about 90 without an LLM reading, 9877 read
- includes (pass 1): 7085/8435 = 84.0% [95% CI 83.2%, 84.8%] -> about 8372 records [8292, 8448]
- pass 1: 2.6 h wall at the measured concurrency (3.7), $655 list-equivalent
- pass 2 (8522 records): 5.1 h wall, $301 list-equivalent
- total: 7.7 h, $956 list-equivalent (consumed as Claude Code subscription usage, not billed)

**Warning: the projected include count (~8372 records, 95% CI 8292-8448) is far above the 150-300 systems the protocol expected.** Deduplication into systems will lower it (pilot: 6172 systems from 6172 final includes), but not by that factor if most includes are one-paper systems. The codable_count distribution of includes is in section 3; tightening criterion (b) is the author's decision.

## 8. System registry

6172 systems from 7085 included records; 503 with more than one record.

| system_id | name | members | canonical | max codable | repo |
|---|---|---|---|---|---|
| 1code | 1Code | 1 | awesome:picrew:733956ebc630 | 15 | https://github.com/21st-dev/1code |
| 2 | (EC)2 | 1 | arxiv:2607.26201 | 19 |  |
| 3cb-reference-agent | 3CB reference agent (3CB Harness) | 1 | arxiv:2410.09114 | 12 | https://github.com/apartresearch/3cb |
| 3dgen | 3DGen | 1 | s2_snowball:df2ecc6482ec2d3880142ac5904a60006f7784f1 | 14 |  |
| 3dify | 3Dify | 1 | arxiv:2510.04536 | 17 |  |
| 3dmedagent | 3DMedAgent | 1 | s2_snowball:f9756057aed446be3a4d2cef2366e1b256a3286a | 20 | https://github.com/jinlab-imvr/3dmedagent |
| 4-agent-multi-llm-klee-pipeline | 4-agent multi-LLM KLEE pipeline | 1 | arxiv:2605.00034 | 15 | https://github.com/zeyad-ab/symbolic-execution-with-multi-llm-architecture-for-rust-security |
| 6gagentgym | 6GAgentGym (6GAgent-8B) | 1 | s2_snowball:af78384afb660c94ec2d6915b396a3d886fab642 | 13 |  |
| a-b-agent | A/B Agent | 1 | s2_snowball:a69b25a6f8397a0b044c149bf7af8a54bfba4e5b | 15 |  |
| a-cegis | A-CEGIS | 1 | s2_snowball:3a1cc106a8a8e2255faa291aa348f971b7d6e503 | 13 |  |
| a-dec | A-DEC | 1 | s2_snowball:36cb8569b74a7fae0ccb5128c552c8c34795e35a | 18 |  |
| a-dot-planner | A.DOT Planner | 1 | s2_snowball:da7f5c25dc647cd395e3c8745c775d3a714fbc72 | 14 |  |
| a-mapreduce | A-MapReduce | 1 | arxiv:2602.01331 | 23 | https://github.com/mingju-c/amapreduce |
| a-mar | A-MAR | 2 | s2_snowball:696782b3cea9d571ee1f71e009ea06b926864b3d | 18 | https://github.com/shuaiwang97/a-mar |
| a-pros | A-ProS | 1 | arxiv:2605.18073 | 19 |  |
| a-rag | A-RAG | 1 | s2_snowball:54fc75b6dbc48dcda85c73a7a2e4c9d7ef037399 | 23 | https://github.com/ayanami0730/arag |
| a-sr | A-SR | 1 | arxiv:2608.04872 | 11 |  |
| a1 | A1 | 1 | arxiv:2507.05558 | 22 |  |
| a1-environment-augmented-generation | a1 / Environment Augmented Generation (EAG) | 1 | s2_snowball:b5563fdbb1b7ced8b164e827e3c7bea0086ab65f | 15 |  |
| a11yrepair | A11YRepair | 1 | s2_snowball:7d826acdc15bce16e3b9dd7458256d217e2c6726 | 13 |  |
| a2a-agent-hub | A2A Agent Hub | 1 | s2_snowball:5b8a4b6bb719f96f0bc60471a7d3638ad158d838 | 20 | https://github.com/taotaotao3/a2a-agent-hub |
| a2h-mas | A2H-MAS | 2 | arxiv:2508.10904 | 12 |  |
| a2o | A2O | 1 | acl:sekii-sato-2026-a2o | 8 |  |
| a2rag | A2RAG | 1 | s2_snowball:2b890cd109c2292051f812858e30c0ad3bb7de0c | 12 |  |
| a3d | A3D | 1 | arxiv:2605.15237 | 17 |  |
| aaas-an | AaaS-AN | 1 | s2_snowball:151698fed4610b0242531fac2bfcf0f0c37a7230 | 10 |  |
| aallm | AaLLM | 1 | arxiv:2608.13472 | 17 |  |
| abaqusagent | AbaqusAgent | 1 | arxiv:2606.00138 | 20 | https://github.com/liram-lin/abaqusagent |
| abbel | ABBEL | 2 | s2_snowball:1c531773db902aa0fc523e9566fae31344b6fab6 | 15 | https://github.com/jakob-bjorner/optimal-explorer-dev |
| abe-ralph | ABE-Ralph | 1 | arxiv:2608.26753 | 14 | https://github.com/flavorfish/autorepro |
| abex | ABEX | 1 | arxiv:2608.28230 | 14 |  |
| ablatecell | AblateCell | 1 | arxiv:2604.19606 | 14 |  |
| abseeker | ABSeeker | 1 | s2_snowball:d917d2c285201cc6aa89df46bf87b28bf8cda69a | 18 | https://github.com/polarseeker/abseeker |
| acal | ACAL | 1 | arxiv:2602.18916 | 15 | https://github.com/loc110504/acal |
| accelerator-assistant | Accelerator Assistant | 1 | s2_snowball:94462c231aa0c3d7994971013972b5fb9d2cbb3f | 25 |  |
| accelopt | AccelOpt | 1 | arxiv:2511.15915 | 19 | https://github.com/zhang677/accelopt |
| accessibility-repair-browser-agent | Accessibility repair browser agent (audit-inject-verify loop) | 1 | arxiv:2608.24913 | 22 |  |
| accord | ACCORD | 1 | arxiv:2606.16432 | 15 | https://github.com/jianglai-0023/accord |
| acdc | ACDC (Automated Certificate Detection and Correction) | 1 | arxiv:2607.28928 | 13 | https://github.com/rinard/axontestandrepair |
| ace | ACE (Actor-Critic Embodied Agent, AssistGUI reference agent) | 4 | s2_snowball:24fc9ad715372358bd0108eeb7c944b915963293 | 25 | https://github.com/escottrose01/ace-llm |
| ace-cap | ACE-Cap | 1 | s2_snowball:40fdb8e2572680bf159d8afb29d7b8848acb094b | 8 |  |
| acecoder | ACECODER | 1 | arxiv:2601.04203 | 7 |  |
| acie | ACIE | 1 | s2_snowball:5169283558e49be90dd55390f294c248d03d7641 | 12 |  |
| acm | ACM (Agentic Context Management agent) | 1 | s2_snowball:6c1501f6032c2625aee9d5917ebd520bc9f06239 | 20 | https://github.com/lixiaochuan2020/agentic-context-management |
| acmap | ACMAP | 1 | s2_snowball:7f583a90890d8c4ae750676bb66d8f54afd8c97a | 16 |  |
| acoder | ACoder | 1 | leaderboard:swe-bench:acoder | 5 | https://github.com/acoder-ai/acoder |
| acon | ACON (reference ReAct agents) | 1 | arxiv:2510.00615 | 15 | https://github.com/microsoft/acon |
| acquire | ACQUIRE | 1 | arxiv:2607.11111 | 21 | https://github.com/lionlin2003/acquire |
| acrouter | ACRouter | 1 | s2_snowball:6b98c79a18c433ed2e025a5a36fe6eab67015c28 | 22 | https://github.com/lancezpf/agent-as-a-router |
| act | ACT | 1 | acl:nakatsuji-etal-2025-act | 14 |  |
| act-debugger-chained-system | ACT + Debugger chained system | 1 | arxiv:2505.02133 | 14 | https://github.com/nazmus-ashrafi/multiagent_vs_debugger |
| actio | Actio | 1 | arxiv:2607.23740 | 13 |  |
| actionengine | ActionEngine | 1 | arxiv:2602.20502 | 17 |  |
| actionrating | ActionRating | 1 | arxiv:2606.11349 | 15 |  |
| active-epistemic-control | Active Epistemic Control (AEC) | 1 | arxiv:2602.03974 | 16 |  |
| active-inference-agent | Active Inference Agent (active inference research agent) | 1 | arxiv:2412.10425 | 15 | https://github.com/rpd123-byte/active-inference-for-self-organizing-multi-llm-systems-a-bayesian-thermodynamic-approach-to-adaptat |
| activecontext | ActiveContext | 1 | arxiv:2604.11462 | 14 |  |
| activegraph | ActiveGraph (Diligence pack) | 1 | arxiv:2605.21997 | 28 | https://github.com/yoheinakajima/activegraph |
| activemem | ActiveMem | 1 | arxiv:2606.10532 | 12 |  |
| activepieces | Activepieces (Agents) | 1 | github:activepieces/activepieces | 19 | https://github.com/activepieces/activepieces |
| actor | ACToR | 2 | arxiv:2510.03879 | 13 |  |
| actor-critic-pcg-dual-agent | Actor-Critic PCG dual-agent | 1 | arxiv:2512.10501 | 19 |  |
| acv-llm | ACV-LLM (LLM-based multi-agent microservice management framework) | 1 | arxiv:2407.14402 | 17 |  |
| ad-care | AD-CARE | 1 | arxiv:2603.25322 | 15 |  |
| ad-mir | AD-MIR | 1 | s2_snowball:01aef622a0a9ed400765ab6dd3b857d08dd90678 | 24 | https://github.com/little-fridge/ad-mir |
| ada | Ada | 1 | arxiv:2606.08500 | 17 |  |
| adacoder | AdaCoder | 1 | arxiv:2504.04220 | 26 | https://github.com/yxingo/adacoder |
| adacom | AdaCoM | 1 | arxiv:2605.30785 | 13 |  |
| adaexplore | AdaExplore | 1 | arxiv:2604.16625 | 21 | https://github.com/stiglidu/adaexplore |
| adalflow | AdalFlow (Agent/Runner) | 1 | github:SylphAI-Inc/AdalFlow | 15 | https://github.com/sylphai-inc/adalflow |
| adam | ADAM (Agent for Digital Atoms and Molecules) | 1 | s2:554099a752231fa2aab45ec15b35d3cc74173b74 | 11 |  |
| adamem | AdaMEM | 1 | s2_snowball:adfe20397d0460994e7ab34dc04c545e28a77cde | 18 | https://github.com/yunx-z/adamem |
| adapa-agent | AdaPA-Agent | 1 | openreview:gkG8JOOUF4 | 17 | https://github.com/sirius11311/adapa |
| adaplan | AdaPlan (PilotRL) | 2 | arxiv:2508.00344 | 15 | https://github.com/import-myself/ahp |
| adaplanner | AdaPlanner | 1 | arxiv:2305.16653 | 19 | https://github.com/haotiansun14/adaplanner |
| adapt | ADaPT | 1 | s2_snowball:0725b276e351bba6b2a52ecb64f3c964b9acc2f9 | 13 |  |
| adaptagent | AdaptAgent | 2 | arxiv:2411.13451 | 15 |  |
| adaptevolve | AdaptEvolve | 1 | arxiv:2602.11931 | 9 |  |
| adaptive-auto-harness | Adaptive Auto-Harness | 1 | arxiv:2606.01770 | 22 |  |
| adaptive-command | Adaptive Command | 1 | s2_snowball:2ede39666689be19181ca4b534fa651251449271 | 9 |  |
| adaptive-influence-graphs | Adaptive Influence Graphs (AIGs) | 1 | arxiv:2608.24361 | 14 |  |
| adaptive-orchestrator-with-cross-episode-memory | Adaptive orchestrator with cross-episode memory | 1 | s2:dc1eaac1847c7d53c01be2adbcc52d104781b278 | 16 | https://github.com/mlukei/adaptive-multi-agent-orchestrator-benchmarks |
| adaptive-rag | Adaptive-RAG | 1 | s2_snowball:e5e8c6ac537e0f5b5db14170bc232d6f9e641bbc | 13 | https://github.com/starsuzi/adaptive-rag |
| adaptive-reasoning-and-acting-doctor-agent | Adaptive reasoning and acting doctor agent | 1 | arxiv:2410.10020 | 10 |  |
| adaptive-retrieval-augmented-reasoning-agent | Adaptive Retrieval-Augmented Reasoning Agent | 1 | arxiv:2602.07213 | 10 |  |
| adaptive-self-improvement-agentic-system | Adaptive self-improvement agentic system (PCL-lite) | 1 | arxiv:2502.02534 | 11 | https://github.com/zhang677/pcl-lite |
| adaptjobrec | AdaptJobRec | 1 | s2_snowball:973e29d323c8e72f2fed765dd38e648ce581d535 | 14 |  |
| adaptorch | AdaptOrch | 1 | arxiv:2602.16873 | 19 | https://github.com/adaptorch/adaptorch |
| adaskill | AdaSkill | 1 | s2_snowball:599c6b79f98b23348511d49e4f18344243417cf0 | 14 | https://github.com/tencent/adaskill |
| adavdr | AdaVDR | 1 | s2_snowball:849c928e36699043836bf08c8b9fa4a8ea76fa14 | 13 | https://github.com/accio-lab/adavdr |
| adcanvas | ADCanvas | 1 | s2:afd4f4171f99be0fe8c100cee4a5ff6e2de41ada | 12 |  |
| adema | ADEMA | 1 | arxiv:2604.25849 | 12 |  |
| adept | ADEPT (ScientificWorkflowAgent) | 1 | openalex:W4417066576 | 24 | https://github.com/pnnl/adept-agentic-framework-core |
| adias | ADIAS | 1 | arxiv:2608.06410 | 23 | https://github.com/scylj1/adias |
| adk-arena-llm-as-a-developer-agent | ADK Arena LLM-as-a-Developer agent | 1 | arxiv:2606.05548 | 20 | https://github.com/jintao-h/adk-arena |
| adk-based-proactive-contact-center-multi-agent-system | ADK-based proactive contact-center multi-agent system | 1 | openalex:W4417093006 | 8 |  |
| adk-compliance-healing-agent | ADK compliance-healing agent (opa-correction-agentic-adk) | 1 | openalex:W7205452011 | 19 |  |
| adk-rust | ADK-Rust (CodingAgent) | 1 | github:zavora-ai/adk-rust | 26 | https://github.com/zavora-ai/adk-rust |
| adma-copilot | ADMA Copilot | 1 | arxiv:2411.00188 | 12 |  |
| admem | AdMem | 1 | arxiv:2606.06787 | 14 |  |
| adore | ADORE | 1 | s2_snowball:8fb1dbf6ca0021d9f787ab481ce6d202e9f1ce3c | 13 |  |
| adr | ADR | 1 | arxiv:2605.17380 | 18 |  |
| adrd | ADRD | 1 | arxiv:2506.14299 | 18 | https://github.com/bjbcjwsq/adrd |
| adsl | aDSL | 1 | s2:14cde52442db5685ca78bcb90a3c53b6dcc4b82a | 23 | https://github.com/sig-pku/adsl |
| adsl-pde | ADSL-PDE | 1 | s2_snowball:b95f5389c759147baf2ce8ce2e5d800401ad95eb | 15 | https://github.com/super-kongcc/improving-auto-design-of-neural-pde-solvers-with-a-domain-specific-language |
| adsmind | AdsMind | 1 | arxiv:2606.19152 | 28 | https://github.com/nagatobigseven/adsmind |
| adsorb-agent | Adsorb-Agent | 1 | arxiv:2410.16658 | 18 | https://github.com/hoon-ock/catalystaigent |
| adsworldengine | AdsWorldEngine | 1 | s2_snowball:c6109ca668b998549ac743b1d07446611dbee83c | 7 |  |
| adventureagent | AdventureAgent | 1 | openalex:W7163154287 | 5 |  |
| adverintent-agent | AdverIntent-Agent | 1 | arxiv:2505.13008 | 12 |  |
| adversarial-review | Adversarial Review (AR) | 1 | arxiv:2608.18167 | 12 |  |
| adversarially-aligned-llm-defense-agent-framework | Adversarially aligned LLM defense-agent framework | 1 | openalex:W7165153886 | 12 |  |
| advertest | AdverTest | 1 | arxiv:2602.08146 | 23 | https://github.com/jmueducn/advertest |
| advisingwise | AdvisingWise | 1 | arxiv:2511.05706 | 18 |  |
| advisor-constructor-multi-agent-framework | Advisor-Constructor multi-agent framework | 1 | openalex:W7130935429 | 6 |  |
| adwise | ADWISE | 1 | s2_snowball:37f83a2ee320174b1732c2f20d2562038b5c4a26 | 13 |  |
| aegis | Aegis | 4 | acl:shi-etal-2024-aegis | 21 | https://github.com/evandiewald/aegis |
| ael | AEL | 1 | arxiv:2604.21725 | 13 | https://github.com/wujiangxu/ael |
| aeloon | Aeloon | 1 | s2_snowball:bf55d7d5b908158fb6653c89080fbd1a924ecf52 | 19 | https://github.com/aetherheart-ai/aeloon |
| aema | AEMA | 1 | arxiv:2601.11903 | 12 |  |
| aeon | Aeon | 1 | github:aeonfun/aeon | 23 | https://github.com/aeonfun/aeon |
| aera | AERA | 1 | s2_snowball:b4c32599339be8f1b0bb98cd347a424dfbb6f78c | 13 | https://github.com/farmountain/aera-arc3-paper |
| aerobat | AEROBAT | 1 | s2_snowball:81abc3df38dec6b8bb35ea27c3fedaf363155cdc | 24 | https://github.com/syleeheal/aerobat |
| aerocopilotbench-reference-agent | AeroCopilotBench reference agent | 1 | arxiv:2608.16349 | 14 |  |
| aerotherm-gpt | AeroTherm-GPT | 1 | arxiv:2604.01738 | 16 | https://github.com/tps-qxx/aerotherm-gpt |
| aether | Aether | 1 | s2_snowball:f26f86e103f04ae5af8aa9e85258a4ea245ed885 | 16 |  |
| aevo | AEVO | 1 | s2_snowball:66a87d7b834aa0641bee00d6437195a6315e5598 | 17 |  |
| affordable-generative-agents | Affordable Generative Agents (AGA) | 1 | arxiv:2402.02053 | 15 | https://github.com/affordablegenerativeagents/affordable-generative-agents |
| afl | AFL | 1 | arxiv:2510.16701 | 17 | https://github.com/zhang-ni/afl |
| aflow | AFlow | 1 | survey_refs:preprints:202604.0428:163 | 19 | https://github.com/foundationagents/aflow |
| afm | AFM2 | 1 | arxiv:2506.03530 | 17 | https://github.com/guanzhou-ke/afm2 |
| afm-messenger-afm-pilot-afm-doctor-agentic-framework | AFM Messenger / AFM Pilot / AFM Doctor agentic framework | 1 | arxiv:2608.26198 | 15 |  |
| afspp | AFSPP | 1 | arxiv:2401.02870 | 8 |  |
| aftervibe | AfterVibe | 1 | arxiv:2607.09900 | 12 |  |
| afuzz | AFuzz | 1 | arxiv:2605.10074 | 16 |  |
| ag-v2 | AG2 (Agent) | 1 | github:ag2ai/ag2 | 18 | https://github.com/ag2ai/ag2 |
| agao | AGAO | 1 | arxiv:2607.23678 | 12 | https://github.com/mingzhoufan97/agao |
| agel-comp | AGEL-Comp | 1 | arxiv:2604.26522 | 16 | https://github.com/place-beyond-bytes/agel-comp |
| agemem | AgeMem | 1 | arxiv:2601.01885 | 17 |  |
| agensflow | AgensFlow | 1 | arxiv:2605.27466 | 29 | https://github.com/nicolepcx/agensflow |
| agent | Agent0 | 2 | arxiv:2507.18993 | 16 |  |
| agent-agnostic-performance-optimization-scaffold | Agent-agnostic performance optimization scaffold | 1 | s2:7f49e8136ea8820991e0598fb894e426b8772f74 | 18 |  |
| agent-alpha | Agent Alpha | 1 | s2_snowball:3d53bb6020cf87a11d34176517acfb3c5265b53c | 11 |  |
| agent-as-a-judge | Agent-as-a-Judge | 1 | s2_snowball:10d2842131634263b5a6875319ff53c0da6a7398 | 21 | https://github.com/metauto-ai/agent-as-a-judge |
| agent-as-tool | Agent-as-tool | 1 | arxiv:2507.01489 | 11 |  |
| agent-assisted-harness | Agent-Assisted Harness (mlsys26-flashinfer-contest) | 1 | arxiv:2607.17979 | 20 | https://github.com/syhya/mlsys26-flashinfer-contest |
| agent-automatic-graph-exploration-framework | Agent / Automatic Graph Exploration framework | 1 | s2_snowball:0fe1a9e4709ff44054fc68c24b5fbc516de8ab4b | 16 |  |
| agent-banana | Agent Banana | 1 | s2_snowball:3fad43c53fa50fae8e20c51c0cb9eb36943d7b91 | 18 |  |
| agent-based-post-hoc-correction-of-agricultural-yield-forecasts | Agent-Based Post-Hoc Correction of Agricultural Yield Forecasts | 1 | arxiv:2605.12375 | 15 |  |
| agent-based-service-architecture | Agent-Based Service Architecture (ASA) | 1 | openalex:W7130653430 | 13 |  |
| agent-bazaar | Agent Bazaar | 1 | arxiv:2605.17698 | 13 |  |
| agent-brace | Agent-BRACE | 1 | arxiv:2605.11436 | 25 | https://github.com/joykirat18/agent-brace |
| agent-breakage | agent-breakage (agent under test: Emily) | 1 | s2_snowball:08649f99062f1d9624ec0c9017c4666b6ab3e5ad | 19 | https://github.com/odmarkj/agent-breakage |
| agent-capsules | Agent Capsules | 1 | arxiv:2605.00410 | 20 | https://github.com/aray-17/agent-capsules |
| agent-coevo | Agent-CoEvo | 1 | arxiv:2604.04580 | 15 |  |
| agent-contracts | Agent Contracts | 1 | s2_snowball:46682696b006815a79af4b04926200d4d8e3b99c | 15 | https://github.com/flyersworder/agent-contracts |
| agent-development-kit | Agent Development Kit (ADK) | 1 | awesome:picrew:4ba15d27de59 | 18 | https://github.com/google/adk-python |
| agent-distillation | Agent Distillation | 1 | arxiv:2505.17612 | 21 | https://github.com/nardien/agent-distillation |
| agent-driven-corpus-linguistics | Agent-Driven Corpus Linguistics | 1 | arxiv:2604.07189 | 13 |  |
| agent-e | Agent-E | 3 | arxiv:2407.13032 | 27 | https://github.com/emergenceai/agent-e |
| agent-enhanced-heterogeneous-graph-rag | Agent-Enhanced Heterogeneous Graph RAG | 1 | s2_snowball:95aecbb57bdccfeac6f6386815cf3b7c3db21171 | 15 |  |
| agent-event-coder | Agent-Event-Coder (AEC) | 1 | arxiv:2511.13118 | 14 | https://github.com/uestc-gqj/agent-event-coder |
| agent-expver | Agent-ExpVer | 1 | s2_snowball:20699a99cd939f3faeabd9f16dd2c3536ef89001 | 15 |  |
| agent-factory | Agent Factory (HLS) | 2 | arxiv:2603.25719 | 25 | https://github.com/zzatpku/agentfactory |
| agent-for-user | Agent for User (multi-agent TikTok testing) | 1 | arxiv:2504.15474 | 11 |  |
| agent-g | AGENT-G | 3 | openreview:g2C947jjjQ | 22 | https://github.com/sunyuanfu/agentgl |
| agent-guided-pruning | agent-guided pruning | 1 | arxiv:2601.09694 | 15 |  |
| agent-hospital | Agent Hospital | 1 | s2_snowball:0d69f44a47babaa522dee90baf632d9a8419bca3 | 9 |  |
| agent-hunt | Agent Hunt | 1 | arxiv:2603.06737 | 15 | https://github.com/mgwiki/alg_top |
| agent-jit | Agent JIT (JIT-Planner/JIT-Scheduler) | 1 | arxiv:2605.21470 | 17 |  |
| agent-laboratory | Agent Laboratory | 1 | arxiv:2501.04227 | 25 |  |
| agent-libos | Agent libOS | 1 | arxiv:2606.03895 | 29 | https://github.com/yingqi-z20/agent-libos |
| agent-lite-medical-assistant | Agent Lite Medical Assistant | 1 | s2_snowball:6c54d04a1cb780f97bbf2de36ec88d036bc5dcc5 | 12 |  |
| agent-memory-distillation | Agent Memory Distillation (AMD) | 1 | arxiv:2608.07169 | 13 |  |
| agent-native | Agent-Native | 1 | github:BuilderIO/agent-native | 9 | https://github.com/builderio/agent-native |
| agent-nexus | Agent-Nexus | 1 | s2_snowball:1c088c3acd9878fc53667cb10b289437964fb6ad | 12 |  |
| agent-om | Agent-OM | 1 | arxiv:2312.00326 | 24 | https://github.com/qzc438/ontology-llm |
| agent-on-graph | Agent-on-Graph (AoG) | 1 | openalex:W7168032230 | 7 | https://github.com/xuduyinuo/aog |
| agent-orchestrated-adaptive-rag | Agent-Orchestrated Adaptive RAG | 1 | arxiv:2606.05658 | 14 |  |
| agent-orchestrator | Agent Orchestrator | 1 | awesome:picrew:081771e5aa9d | 15 | https://github.com/untrivial-ai/agent-orchestrator |
| agent-pro | Agent-Pro | 1 | s2_snowball:789485978d69e248832df358ee0fb062012925b8 | 19 | https://github.com/zwq2018/agent-pro |
| agent-q | Agent Q | 2 | arxiv:2408.07199 | 14 | https://github.com/vostride/agent-qa |
| agent-q-mix | Agent Q-Mix | 1 | arxiv:2604.00344 | 19 | https://github.com/ericjiang18/agent-q-mix |
| agent-rosetta | Agent Rosetta | 1 | arxiv:2603.15952 | 18 |  |
| agent-sama | Agent-SAMA | 1 | arxiv:2505.23596 | 17 |  |
| agent-scaling | Agent Scaling | 1 | openalex:W7162129998 | 24 | https://github.com/ybkim95/agent-scaling |
| agent-security-bench | Agent Security Bench | 1 | s2_snowball:5f4efbe3aae1d8f44ceab1da257ae685d6beb00b | 17 | https://github.com/agiresearch/asb |
| agent-skill-framework-for-creep-database-construction | Agent-Skill framework for creep database construction | 1 | s2:dbf32da69632bab08143d26cbc802e88e50b128b | 13 |  |
| agent-skill-system | Agent Skill System (deploy-new-llm) | 1 | arxiv:2606.07586 | 18 |  |
| agent-squad | Agent Squad (BedrockLLMAgent) | 1 | survey_refs:preprints:202604.0428:61 | 13 | https://github.com/2fastlabs/agent-squad |
| agent-system-interface-mapper-agent | Agent-System Interface mapper agent (Trace + AutoGuide) | 1 | s2_snowball:4e71d7bee58aedf1cb095b371f9be6a2cfbd26e7 | 15 |  |
| agent-tars-ui-tars-desktop | Agent TARS / UI-TARS Desktop (GUIAgent) | 1 | github:bytedance/UI-TARS-desktop | 20 | https://github.com/bytedance/ui-tars-desktop |
| agent-team-work-zone | Agent Team Work Zone (ATWZ) | 1 | arxiv:2607.22917 | 22 | https://github.com/sr-a-w/agent-team-work-zone |
| agent-teams-ai | Agent Teams AI | 1 | github:777genius/agent-teams-ai | 18 | https://github.com/777genius/agent-teams-ai |
| agent-testing-agent | Agent-Testing Agent (ATA) | 1 | arxiv:2508.17393 | 21 | https://github.com/khalilmrini/agent-testing-agent |
| agent-unirag | Agent-UniRAG | 1 | arxiv:2505.22571 | 17 |  |
| agent-v2 | Agent2 | 1 | arxiv:2509.13368 | 13 |  |
| agent-workflow-memory | Agent Workflow Memory (AWM) | 1 | survey_refs:preprints:202604.0428:80 | 19 | https://github.com/zorazrw/agent-workflow-memory |
| agent0-vl | Agent0-VL | 1 | s2_snowball:ed71e484c8d368302e21c09e614d78a13e467ad6 | 16 | https://github.com/aiming-lab/agent0 |
| agent2world | Agent2World | 2 | arxiv:2512.22336 | 19 |  |
| agent2world-multi | Agent2World Multi | 1 | openreview:LdQmNo5iVX | 14 |  |
| agent4ct | Agent4CT | 1 | arxiv:2607.22824 | 20 | https://github.com/akmaier/agent4ct |
| agent4debate | Agent4Debate | 1 | arxiv:2408.04472 | 13 | https://github.com/zhangyiqun018/agent-for-debate |
| agent4decompile | Agent4Decompile | 1 | arxiv:2604.23940 | 19 |  |
| agent4dl | Agent4DL | 1 | s2_snowball:e285c0c0afa39198c79b806fc28ef6a698b37a54 | 10 | https://github.com/padas-lab-de/icadl24-agent4dl |
| agentada | AgentAda | 1 | s2_snowball:70886a79f8c61d1a11d5640f812c730197bdf7f0 | 19 | https://github.com/servicenow/agentada |
| agentao | Agentao | 1 | arxiv:2608.13574 | 29 | https://github.com/jin-bo/agentao |
| agentbench-reference-agent | AgentBench reference agent | 8 | arxiv:2308.03688 | 26 | https://github.com/snap-stanford/mlagentbench |
| agentboard-reference-agent | AgentBoard reference agent | 1 | arxiv:2401.13178 | 15 | https://github.com/hkust-nlp/agentboard |
| agentbreeder | AgentBreeder | 1 | arxiv:2502.00757 | 10 | https://github.com/jrosseruk/agentbreeder |
| agentbrew | AgentBrew | 1 | arxiv:2607.16851 | 16 | https://github.com/hkuds/upskill |
| agentbuild | AgentBuild | 1 | arxiv:2606.12834 | 14 |  |
| agentcard | AgentCARD | 1 | arxiv:2606.20629 | 23 | https://github.com/auto-cap/agentcap |
| agentcaster-reference-agent | AgentCaster reference agent | 1 | arxiv:2510.03349 | 13 |  |
| agentcat | AgentCAT | 2 | arxiv:2602.18479 | 11 |  |
| agentcoder | AgentCoder | 1 | arxiv:2312.13010 | 13 |  |
| agentcodereview | AgentCodeReview | 1 | s2:4baaec6777466cce8d134008395c5027b73019df | 13 |  |
| agentcollab | AgentCollab | 1 | arxiv:2603.26034 | 11 |  |
| agentcomp | AgentComp | 1 | s2_snowball:02ef2fb085a21f03e3afeb3e27bb8c65ef5f655c | 12 | https://github.com/armanzarei/agentcomp |
| agentcot | AgentCOT | 1 | arxiv:2409.12411 | 14 |  |
| agentcvr | AgentCVR | 1 | s2_snowball:6e9e50d30928b7b86dfbcaf7c6d50bb2f1a960ea | 20 | https://github.com/wang-jh24/agentcvr |
| agentdebug | AgentDebug | 2 | arxiv:2509.25370 | 19 | https://github.com/ulab-uiuc/agentdebug |
| agentdiet | AgentDiet | 1 | s2_snowball:af5e693960bba9748bbe9ab776712af7742cee8f | 13 |  |
| agentdojo-reference-agent | AgentDojo reference agent | 1 | arxiv:2406.13352 | 18 | https://github.com/ethz-spylab/agentdojo |
| agentdroid | AgentDroid | 1 | arxiv:2503.12163 | 14 | https://github.com/wwstarry/llm4fraud |
| agentdropout | AgentDropout | 1 | arxiv:2503.18891 | 21 | https://github.com/wangzx1219/agentdropout |
| agentdse | AgentDSE | 1 | arxiv:2606.21836 | 12 |  |
| agentdynex | AgentDynEx | 1 | arxiv:2504.09662 | 13 |  |
| agentehr | AgentEHR (RetroSum agent) | 1 | s2_snowball:d1972db80f51d43ecc222cac9a737dd820558932 | 18 | https://github.com/bluezeros/agentehr |
| agentevolver | AgentEvolver | 1 | s2_snowball:dde18f29056365d8d84460f8cd8a3532077b3137 | 25 | https://github.com/modelscope/agentevolver |
| agentexecutor | AgentExecutor | 1 | arxiv:2608.05959 | 16 |  |
| agentfair | AgentFAIR | 1 | arxiv:2607.15781 | 28 | https://github.com/mingchen-github/agentfair |
| agentfinvqa | AgentFinVQA | 1 | s2_snowball:dd277c0e0c55ae6ada0dcfc7c8a6d724ff82392b | 18 |  |
| agentfl | AgentFL | 2 | arxiv:2403.16362 | 20 | https://github.com/agent-one-lab/agentfly |
| agentflow | AgentFlow | 3 | arxiv:2510.05592 | 17 |  |
| agentflux | AgentFlux | 1 | arxiv:2510.00229 | 13 |  |
| agentforge | AgentForge | 2 | arxiv:2601.13383 | 21 | https://github.com/001shahab/agentforge |
| agentfox | AgentFoX | 1 | s2_snowball:0733167a4e3fac92bc16aeb61cf8df1d7ecf2d0e | 22 | https://github.com/suncore946/agentfox |
| agentfugue | AgentFugue (Cabeza) | 1 | s2_snowball:5413c1700410467f3a7a9f921c2ecf44aa8201fa | 20 | https://github.com/qhjqhj00/cabeza |
| agentgroupchat-v2 | AgentGroupChat-V2 | 1 | arxiv:2506.15451 | 18 | https://github.com/mikegu721/agentgroupchat-v2 |
| agentguard | AgentGuard | 1 | arxiv:2502.09809 | 14 |  |
| agentguardutil | AgentGuardUtil | 1 | arxiv:2608.23282 | 17 |  |
| agentgym | AgentGym | 2 | s2_snowball:3072ad4982cd916606ac88ea1883d4d725c4eda4 | 19 | https://github.com/woooodyy/agentgym |
| agentgym-rl | AgentGym-RL | 1 | arxiv:2509.08755 | 16 | https://github.com/woooodyy/agentgym-rl |
| agenthijack-agent | AgentHijack-Agent | 1 | arxiv:2605.25707 | 12 |  |
| agenthoi | AgentHOI | 1 | arxiv:2607.13881 | 9 | https://github.com/oceanflowlab/agenthoi |
| agenthpo | AgentHPO | 1 | arxiv:2402.01881 | 14 |  |
| agentic-additive-manufacturing-alloy-evaluation | Agentic Additive Manufacturing Alloy Evaluation (Claude Code multi-agent) | 1 | arxiv:2510.02567 | 16 | https://github.com/baratilab/agentic-additive-manufacturing-alloy-evaluation |
| agentic-adversarial-rewriting-framework | Agentic adversarial rewriting framework (Attacker Agent + Prompt Optimization Agent) | 1 | s2_snowball:23073976b112080f9607fdc6a03d244ff852fcd8 | 13 |  |
| agentic-ai-architecture-for-autonomous-incident-resolution | Agentic AI architecture for autonomous incident resolution | 1 | s2_snowball:6f9297b462beaf2e228ea35636f777774c4a7dfb | 24 |  |
| agentic-ai-autonomous-defense-framework | Agentic AI Autonomous Defense Framework | 1 | arxiv:2512.23480 | 15 |  |
| agentic-ai-control-plane-for-6g-network-slicing | Agentic AI Control Plane for 6G Network Slicing | 1 | arxiv:2602.13227 | 10 |  |
| agentic-ai-framework | Agentic AI framework (clinical interviews) | 2 | openalex:W7154572019 | 15 |  |
| agentic-ai-framework-for-cell-free-o-ran | Agentic AI framework for cell-free O-RAN | 1 | arxiv:2602.22539 | 11 |  |
| agentic-ai-framework-for-glaucoma-detection | Agentic AI framework for glaucoma detection | 1 | arxiv:2608.07651 | 14 |  |
| agentic-ai-framework-for-training-general-practitioner-student-skills | Agentic AI Framework for Training General Practitioner Student Skills | 1 | arxiv:2512.18440 | 22 | https://github.com/victordmz/agentic-framework-gp-skills |
| agentic-ai-hardware-design-and-verification-mas | Agentic AI hardware design and verification MAS | 1 | arxiv:2507.02660 | 15 |  |
| agentic-ai-hems | Agentic AI HEMS | 1 | s2_snowball:37a5d33d8f313358915f802801b4ab8071232399 | 23 | https://github.com/redaelmakroum/agentic-ai-hems |
| agentic-ai-wi-fi-mapc-framework | Agentic AI Wi-Fi MAPC framework | 1 | arxiv:2511.20719 | 14 |  |
| agentic-autosurvey | Agentic AutoSurvey | 1 | arxiv:2509.18661 | 15 |  |
| agentic-bitween | Agentic Bitween | 1 | arxiv:2412.18134 | 13 | https://github.com/ferhaterata/learning-randomized-reductions |
| agentic-breaking-change-repair-system | Agentic breaking-change repair system | 1 | s2_snowball:ff78bd4dc3353b438a25f01f9f43391195e8d81d | 18 |  |
| agentic-cloud-workflow-engineering | Agentic Cloud Workflow Engineering | 1 | arxiv:2609.00050 | 25 |  |
| agentic-clustering | Agentic Clustering | 1 | arxiv:2606.01255 | 13 |  |
| agentic-cognitive-profiling | Agentic Cognitive Profiling (ACP) | 1 | s2:c170babdb9793768b4b18d7e70015e45e15383d7 | 19 |  |
| agentic-collaborative-cognition | Agentic Collaborative Cognition | 1 | s2:5ebbdd61a24baaf57d369ccd6921154cb1ef8de5 | 15 | https://github.com/zhangbo135/agentic-collaborative-cognition |
| agentic-commerce-multi-retrieval-framework | Agentic Commerce multi-retrieval framework | 1 | s2:71c6f60188ed070abdae2ede61e062d1814360c4 | 15 |  |
| agentic-context-cracking | Agentic Context Cracking | 1 | arxiv:2608.31082 | 7 |  |
| agentic-control-plane | Agentic Control Plane (ACP) | 1 | s2:94752218d894e2b20bd9b6b1938626488c092c40 | 11 |  |
| agentic-counterfactual-graphrag | Agentic Counterfactual GraphRAG | 1 | s2_snowball:c0327249d40124efad3c0d1e45f229a218518b05 | 8 |  |
| agentic-data-scientist | Agentic Data Scientist | 1 | github:K-Dense-AI/agentic-data-scientist | 24 | https://github.com/k-dense-ai/agentic-data-scientist |
| agentic-engineering-design | Agentic Engineering Design (MAS) | 1 | arxiv:2507.08619 | 22 | https://github.com/soheylm/agentic-eng-design |
| agentic-episodic-control | Agentic Episodic Control (AEC) | 1 | s2_snowball:966423188dcdb22dcb29bfc08890f32b7791e83a | 15 | https://github.com/xidong-yang/agentic_episodic_control |
| agentic-erp | Agentic ERP | 1 | arxiv:2607.17331 | 18 |  |
| agentic-esg-framework | Agentic ESG framework (multi-agent architecture) | 1 | arxiv:2603.10646 | 11 | https://gitlab.com/for_peer_review-group/esg_assistant |
| agentic-flow | Agentic Flow | 1 | github:ruvnet/agentic-flow | 13 | https://github.com/ruvnet/agentic-flow |
| agentic-form-like-document-extraction-framework | Agentic form-like document extraction framework | 1 | arxiv:2505.13504 | 16 |  |
| agentic-framework-for-metamaterial-inverse-design | Agentic Framework for Metamaterial Inverse Design | 1 | arxiv:2506.06935 | 14 |  |
| agentic-geospatial-intelligence-system | agentic geospatial intelligence system | 1 | s2_snowball:957fdc12104581fe987d267218570ee32bb6c45e | 21 | https://github.com/mashrekur/alpha_geom |
| agentic-graphrag | Agentic GraphRAG (SHAB) | 1 | s2_snowball:2fdcfc04b63bc00d4f9ccb458ff9d1eb38e53e5e | 17 |  |
| agentic-graphrag-with-word-spotting | Agentic GraphRAG with word spotting (historical KG) | 1 | s2_snowball:61f4db0ee7b7732270f93668d1ef25ac0808a2e9 | 12 |  |
| agentic-ideation | Agentic-Ideation | 1 | arxiv:2606.31229 | 10 |  |
| agentic-incident-response-multiscale-planner | Agentic incident response multiscale planner | 1 | arxiv:2608.02422 | 11 | https://github.com/taoli-nyu/agentic-incident-response-esorics26 |
| agentic-interpretation | agentic interpretation | 1 | s2_snowball:8347381ceb6ee4a2a7e22f3da2380eff38b4c264 | 11 |  |
| agentic-ioev-framework | Agentic IoEV framework | 1 | arxiv:2509.12233 | 11 |  |
| agentic-keyword-search-agent | Agentic keyword search agent | 1 | arxiv:2602.23368 | 16 |  |
| agentic-llm-framework-for-3d-frame-structural-analysis | Agentic LLM framework for 3D frame structural analysis | 1 | arxiv:2606.06525 | 11 |  |
| agentic-ltpo | Agentic-LTPO | 1 | s2_snowball:04cb552cc3540e3e3d30b66ae94e4a4740761c88 | 10 |  |
| agentic-lybic | Agentic Lybic | 1 | leaderboard:osworld:agentic-lybic-maestro | 15 | https://github.com/xlang-ai/osworld/mm_agents/maestro |
| agentic-matrix-deflation | Agentic Matrix Deflation | 1 | arxiv:2601.08219 | 14 | https://github.com/pie115/agentic-deflation |
| agentic-mcp-syntax-repair-flow | Agentic MCP syntax repair flow | 1 | arxiv:2512.14762 | 14 |  |
| agentic-memory-augmented-retrieval-and-evidence-grounding-system | Agentic memory-augmented retrieval and evidence grounding system | 1 | s2:5ae2867fb5272ceaa7a70d03d2a1321bab4e09d5 | 14 |  |
| agentic-meta-orchestrator | Agentic Meta-orchestrator (AMO) | 1 | s2_snowball:db6141df6f0880ba44c84069997312d525864e6b | 11 | https://github.com/xiaofengzhu/amo |
| agentic-mipr-framework | agentic MIPR framework | 1 | arxiv:2605.09186 | 15 |  |
| agentic-monte-carlo | Agentic Monte Carlo (AMC) | 1 | arxiv:2606.05296 | 14 | https://github.com/layer6ai-labs/agentic-monte-carlo |
| agentic-nesting | Agentic Nesting (Application-as-Agent framework) | 1 | s2_snowball:d908d6693ff3f5dfe79b49daa712ccd514e9bc0a | 14 |  |
| agentic-ooda-framework | Agentic OODA Framework | 1 | openalex:W7172333118 | 18 |  |
| agentic-operating-system-for-hospitals | Agentic Operating System for Hospitals | 1 | arxiv:2603.11721 | 22 |  |
| agentic-optimization | agentic-optimization (Orchestrator/Investigator/Reviewer) | 1 | arxiv:2603.27415 | 21 | https://github.com/yitao416/agentic-optimization |
| agentic-pbt-agent | Agentic PBT agent | 1 | s2_snowball:e46ee1e13f118c63cbddbaeb59fdd7d5dba86988 | 20 | https://github.com/mmaaz-git/agentic-pbt |
| agentic-policy-search | Agentic Policy Search (APS) | 1 | s2_snowball:48f00745feca6545a293d9dbaee0f4c189121542 | 12 |  |
| agentic-pytorch-to-jax-translation-framework | agentic PyTorch-to-JAX translation framework | 1 | openalex:W7164273583 | 11 |  |
| agentic-rag-assurance-case-generator | Agentic RAG assurance case generator | 1 | s2_snowball:22feaeac62e91f08d1346ad22565521bef8b1a7b | 15 |  |
| agentic-rag-chatbot | Agentic RAG Chatbot (blockchain multi-agent chatbot) | 1 | openalex:W4409852380 | 14 | https://github.com/duc-nsh/blockchain-chatbot |
| agentic-rag-framework | Agentic RAG framework (OB-Radix) | 1 | s2_snowball:f0497ee0afc1afbb6d44d5c34248cd29d6cefe75 | 11 |  |
| agentic-rag-framework-for-software-testing | Agentic RAG framework for software testing | 1 | arxiv:2510.10824 | 14 |  |
| agentic-rag-framework-for-time-series-analysis | Agentic RAG framework for time series analysis | 1 | s2_snowball:206b0021c5c7a1acc85f2fdee0c419e780dbca74 | 12 |  |
| agentic-rag-underwriting-pipeline | Agentic RAG underwriting pipeline | 1 | arxiv:2607.07858 | 15 | https://github.com/drbob-richardson/agentic-bop-underwriting |
| agentic-re-identification-pipeline | Agentic re-identification pipeline | 1 | s2_snowball:f1bf8ec347222adcbe5376aeb25fd2c77df74243 | 14 |  |
| agentic-reasoning | Agentic Reasoning | 1 | arxiv:2502.04644 | 19 | https://github.com/theworldofagents/agentic-reasoning |
| agentic-redux | Agentic Redux | 1 | arxiv:2606.04903 | 17 | https://github.com/thistleseeds/agentic-redux |
| agentic-researcher | The Agentic Researcher | 1 | arxiv:2603.15914 | 23 | https://github.com/zib-iol/the-agentic-researcher |
| agentic-retrieval-framework-for-autonomous-context-aware-data-quality-assessment | Agentic–retrieval framework for autonomous context-aware data quality assessment | 1 | arxiv:2606.13692 | 15 |  |
| agentic-retrobiosynthesis-framework | Agentic Retrobiosynthesis Framework | 1 | s2_snowball:43d820f694dc9b72a4010f513688165acda4a9d9 | 9 |  |
| agentic-risk-aware-set-based-engineering-design-framework | Agentic Risk-Aware Set-Based Engineering Design framework | 1 | arxiv:2604.16687 | 13 |  |
| agentic-rl-harness | Agentic-RL-harness (Harness MDP controller) | 1 | arxiv:2607.05458 | 20 | https://github.com/hik289/agentic-rl-harness |
| agentic-router | Agentic Router | 1 | arxiv:2608.09184 | 16 |  |
| agentic-rpm | Agentic RPM (AIRA-dojo with RPM) | 1 | s2_snowball:e768ac48f31fc20d3b36946151a6a8c2cf9647c5 | 16 |  |
| agentic-rubrics | Agentic Rubrics | 1 | s2_snowball:2d758cf3e9c5815e6d2f1bb8b23d331ba8bbcad9 | 12 |  |
| agentic-scheduler | agentic scheduler | 1 | s2:eb3e4d1edd73880aabb947a24b8a20a006234898 | 12 |  |
| agentic-semantic-layer | Agentic Semantic Layer (schema refinement) | 1 | arxiv:2412.07786 | 13 | https://github.com/agapir/agentic-semantic-layer |
| agentic-smart-contract-pipeline | Agentic smart contract pipeline | 1 | s2_snowball:95c322759bce6fb7ba564621fa0bf2f60e88a786 | 13 |  |
| agentic-spatio-temporal-text-to-sql-pipeline | Agentic spatio-temporal Text-to-SQL pipeline | 1 | arxiv:2510.25997 | 12 |  |
| agentic-swmm | Agentic SWMM | 1 | s2_snowball:cab5089a8583ad829f430fab366b21ebf7fd4e4c | 16 | https://github.com/zhonghao1995/agentic-swmm-workflow |
| agentic-tool-making-pipeline-alarm-triage-agent | agentic tool-making pipeline / alarm-triage agent (built on Eluna) | 1 | arxiv:2607.08010 | 20 |  |
| agentic-torch2jax | Agentic Torch2JAX | 1 | openalex:W7163839364 | 12 |  |
| agentic-user-simulation-framework | Agentic user simulation framework (User Agent + sub-agents) | 1 | arxiv:2601.15290 | 14 |  |
| agentic-visualization-refinement-pipeline | Agentic Visualization Refinement Pipeline | 1 | arxiv:2604.15319 | 10 |  |
| agentic-xai | Agentic XAI | 1 | s2_snowball:87466ae6388c564befdd116a62f96db570bde5e3 | 9 |  |
| agenticad | AgenticAD | 1 | arxiv:2510.08578 | 12 |  |
| agenticaita | AGENTICAITA | 1 | arxiv:2605.12532 | 21 |  |
| agenticcann | AgenticCANN | 1 | s2_snowball:1e2fc04a7809053ffe1716c31087d1ff2b79593a | 18 |  |
| agenticdata | AgenticData | 1 | s2_snowball:04cfb90a12972f114b17c757ed89f944c3777aa1 | 14 |  |
| agenticdb | AgenticDB | 1 | s2_snowball:29a577c328abb08bb8f8007f89491878486724dd | 25 | https://github.com/xinyueyangiscas/agenticdb |
| agenticeco | AgenticECO | 1 | s2_snowball:b3b54e0c8571ed07b1645b9ccda912b17dcd1d5e | 20 |  |
| agenticeval | AgenticEval | 1 | arxiv:2509.26100 | 10 |  |
| agenticfs4eeg | AgenticFS4EEG | 1 | acl:aiersilan-qu-2026-agentic | 17 | https://github.com/ezharjan/agenticfs4eeg |
| agenticgeo | AgenticGEO | 1 | arxiv:2603.20213 | 12 | https://github.com/aicling/agentic_geo |
| agentick | Agentick (LLM/VLM agent harness) | 2 | openalex:W7139107003 | 18 | https://github.com/roger-creus/agentick |
| agenticpa | AgenticPA | 1 | openreview:tX2mU5O0Ux | 17 |  |
| agenticpd | AgenticPD | 1 | arxiv:2607.04758 | 17 |  |
| agenticpruner | AgenticPruner | 1 | s2_snowball:0ca75fb721cd4e3b1b05a146d690c2a44dd1885f | 14 |  |
| agenticrag | AgenticRAG | 2 | arxiv:2605.05538 | 18 | https://github.com/jiangxinke/harness-rl |
| agenticrec | AgenticRec | 1 | arxiv:2603.21613 | 15 |  |
| agenticrectune | AgenticRecTune | 1 | arxiv:2604.26969 | 14 |  |
| agenticrepair | AgenticRepair | 1 | arxiv:2607.29422 | 19 |  |
| agenticrobotics | AgenticRobotics | 1 | s2:0a01a1a69372656eb45a882f62f645b8385946b3 | 27 |  |
| agenticscr | AgenticSCR | 1 | arxiv:2601.19138 | 14 |  |
| agenticseek | AgenticSeek | 1 | github:Fosowl/agenticSeek | 22 | https://github.com/fosowl/agenticseek |
| agenticsts | AgenticSTS | 1 | arxiv:2607.02255 | 18 | https://github.com/alayalab/agenticsts |
| agenticszz | AgenticSZZ | 1 | arxiv:2602.02934 | 21 | https://github.com/sailresearch/agenticszz |
| agentictcad | AgenticTCAD | 1 | arxiv:2512.23742 | 11 |  |
| agentictyper | AgenticTyper | 1 | s2_snowball:ad43bca5e1c254dc968f20624ea8fc483d549206 | 14 | https://github.com/clemens-mw/agentic-typer |
| agenticvau | AgenticVAU | 1 | s2_snowball:ac66da6db38f4f95847682f760cb2ca05ad21abe | 13 |  |
| agentigraph | AGENTiGraph | 2 | arxiv:2410.11531 | 18 | https://github.com/sinketsuzao/agentigraph |
| agentiloop-agent | AgentiLoop Agent! | 1 | github:AgentiLoop/Agent | 26 | https://github.com/agentiloop/agent |
| agentkgv | AgentKGV | 1 | s2_snowball:b86f4f1b2c6a5e131f517a9e44b7b95ee70a50fd | 15 |  |
| agentkit | AgentKit | 1 | arxiv:2404.11483 | 14 |  |
| agentlance | AgentLance | 1 | arxiv:2608.23867 | 12 |  |
| agentlens | AgentLens | 1 | s2_snowball:ee53f2d80b6791c81bbe44008e1fa78bd34284da | 18 | https://github.com/kim-jeong-hyeon/agentlens |
| agentlite | AgentLite (BaseAgent) | 1 | arxiv:2402.15538 | 20 | https://github.com/salesforceairesearch/agentlite |
| agentloop | AgentLoop (S1-DeepResearch) | 1 | s2_snowball:bc782e71f962182b94ac69eca75771a6c0666c75 | 12 | https://github.com/scienceone-ai/s1-deepresearch |
| agentmandering | Agentmandering | 1 | arxiv:2511.04076 | 20 | https://github.com/lihaogx/agentmandering |
| agentmap | AgentMap | 1 | arxiv:2607.27130 | 11 |  |
| agentmaster | AgentMaster | 1 | arxiv:2507.21105 | 9 |  |
| agentmath | AgentMath | 1 | arxiv:2512.20745 | 9 |  |
| agentmd | AgentMD | 1 | arxiv:2402.13225 | 9 |  |
| agentmesh | AgentMesh | 1 | arxiv:2507.19902 | 16 |  |
| agentmob | AgentMob | 1 | arxiv:2606.05130 | 14 |  |
| agentmodernize | AgentModernize | 1 | arxiv:2605.17535 | 15 |  |
| agentnav | AgentNav | 1 | s2_snowball:a9e4c7ef528acb31e7be91eae811ef1e6fbf8e8b | 13 |  |
| agentnet | AgentNet | 1 | arxiv:2504.00587 | 9 |  |
| agentnlq | AgentNLQ | 1 | arxiv:2605.19010 | 20 |  |
| agentoccam | AgentOccam | 1 | arxiv:2410.13825 | 16 | https://github.com/amazon-science/agentoccam |
| agentode | AgentODE | 1 | s2_snowball:b6ffc021cfc54bd9868f1e08568b7392cf11b94b | 21 | https://github.com/hanningyang/agentode |
| agentodrl | AgentODRL | 1 | arxiv:2512.00602 | 19 | https://github.com/ruc-mas/agentodrl |
| agentopia | Agentopia | 2 | arxiv:2606.07513 | 23 | https://github.com/neph0s/agentopia |
| agentoptics | AgentOptics | 1 | s2_snowball:63e43566276e5f8e2fbfb5b6b410cb2e69344ef1 | 11 |  |
| agentorchestra | AgentOrchestra | 3 | arxiv:2506.12508 | 21 |  |
| agentpanel | AgentPanel | 1 | arxiv:2608.03283 | 19 |  |
| agentpoirot | AgentPoirot | 1 | s2_snowball:739526c3ba9536953b65373d66d3469138e227ef | 12 | https://github.com/servicenow/insight-bench |
| agentprobe | AgentProbe | 1 | openalex:W7204584025 | 18 | https://github.com/ayanverse-io/agentprobe |
| agentradio | AgentRadio | 1 | s2_snowball:a2b5d282a3723600c31a56dc38082ea720315ac7 | 29 | https://github.com/coral-protocol/agentradio |
| agentran | AgentRAN | 1 | arxiv:2508.17778 | 14 |  |
| agentrca | AgentRCA | 1 | arxiv:2607.22385 | 16 |  |
| agentrewind | AgentRewind | 1 | arxiv:2608.14380 | 19 | https://github.com/futuresis/replay-agent-recorder |
| agentrr | AgentRR | 1 | arxiv:2505.17716 | 17 |  |
| agentrxiv | AgentRxiv | 1 | arxiv:2503.18102 | 12 |  |
| agents-help-agents | Agents Help Agents (AHA) | 1 | openreview:hREMYJ5ZmD | 14 |  |
| agents-last-exam-reference-agent | Agents' Last Exam reference agent (ALE-Claw) | 1 | github:rdi-berkeley/agents-last-exam | 11 | https://github.com/rdi-berkeley/agents-last-exam |
| agents-llm | AGENTS-LLM | 1 | arxiv:2507.13729 | 12 | https://github.com/boschresearch/agents-llm |
| agents-of-discovery | Agents of Discovery | 1 | s2_snowball:0c5579abc943c0c5ef4af5b26cf83bdb6b86faf2 | 23 | https://github.com/uhh-pd-ml/agentsofdiscovery |
| agents-research-environments-reference-agent | Agents Research Environments (ARE) reference agent | 1 | arxiv:2602.11964 | 8 |  |
| agents-v2 | Agents 2.0 (agent symbolic learning) | 2 | arxiv:2406.18532 | 20 | https://github.com/aiwaves-cn/agents |
| agents4gov | Agents4Gov | 1 | s2:3186582f676f8b7a11d8841af203c35d6c5b8565 | 17 | https://github.com/labic-icmc-usp/agents4gov |
| agents4plc | Agents4PLC | 1 | arxiv:2410.14209 | 16 | https://github.com/luoji-zju/agents4plc_release |
| agentsandbox | AgentSandbox | 1 | arxiv:2505.24019 | 14 |  |
| agentscad | AgentsCAD | 1 | s2:cd1756ca3352f02d9ac304907441e03c7cb82192 | 14 |  |
| agentschool | AgentSchool | 1 | arxiv:2605.30144 | 29 | https://github.com/epitome-aiss/agentschool |
| agentscope | AgentScope (ReAct Agent) | 5 | github:agentscope-ai/agentscope | 25 | https://github.com/agentscope-ai/agentscope |

