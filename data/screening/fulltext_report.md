# Full-text screening report

Generated 2026-09-20 05:13 UTC by `scripts/validate_screening.py`.
Scope: 9906 records (data/screening/fulltext_queue.csv); pass-1 rows 6984, pass-2 rows 273, final rows 6984, systems 4814.

## 1. Decisions

Model(s): {'claude-sonnet-5': 5571, 'claude-opus-5': 1313, 'claude-opus-4-8': 32}; prompt(s): {'ft-v2-2026-09-18': 6984}.

- Pass-1 include rate, all records in scope: 5448/6984 = 78.0% [95% CI 77.0%, 79.0%]
- Pass-1 include rate, records with full text (LLM read): 5448/6916 = 78.8% [95% CI 77.8%, 79.7%]
- not_retrievable (index says not ok; no LLM call): 68
- Pending (in scope, no pass-1 row yet): 2922
- Final (after pass 2 and the registry): {'exclude': 2170, 'include': 4814}; systems in registry: 4814

Include rate by pilot stratum (pass 1):

| stratum | n | not retrievable | include / all | include / with full text |
|---|---|---|---|---|
| known_system | 15 | 0 | 15/15 = 100.0% [95% CI 79.6%, 100.0%] | 15/15 = 100.0% [95% CI 79.6%, 100.0%] |
| metadata_mismatch | 60 | 32 | 13/60 = 21.7% [95% CI 13.1%, 33.6%] | 13/28 = 46.4% [95% CI 29.5%, 64.2%] |
| random | 250 | 36 | 172/250 = 68.8% [95% CI 62.8%, 74.2%] | 172/214 = 80.4% [95% CI 74.5%, 85.1%] |

Include rate by source (pass 1):

| source | n | not retrievable | include rate (all) |
|---|---|---|---|
| arxiv | 3604 | 0 | 2861/3604 = 79.4% [95% CI 78.0%, 80.7%] |
| s2_snowball | 1714 | 9 | 1423/1714 = 83.0% [95% CI 81.2%, 84.7%] |
| openalex | 410 | 17 | 239/410 = 58.3% [95% CI 53.5%, 63.0%] |
| github | 380 | 0 | 323/380 = 85.0% [95% CI 81.1%, 88.2%] |
| s2 | 370 | 42 | 238/370 = 64.3% [95% CI 59.3%, 69.0%] |
| acl | 133 | 0 | 99/133 = 74.4% [95% CI 66.4%, 81.1%] |
| openreview | 115 | 0 | 86/115 = 74.8% [95% CI 66.1%, 81.8%] |
| awesome | 105 | 0 | 81/105 = 77.1% [95% CI 68.2%, 84.1%] |
| leaderboard | 102 | 0 | 61/102 = 59.8% [95% CI 50.1%, 68.8%] |
| grey | 32 | 0 | 31/32 = 96.9% [95% CI 84.3%, 99.4%] |
| survey_refs | 19 | 0 | 6/19 = 31.6% [95% CI 15.4%, 54.0%] |

## 2. Exclusion reasons and deciding steps (pass 1)

| exclusion_code | sub-reason | n | % of excludes |
|---|---|---|---|
| out_of_scope | no_loop | 436 | 28.4% |
| out_of_scope | no_actions | 280 | 18.2% |
| out_of_scope | component_only | 201 | 13.1% |
| out_of_scope | benchmark_only | 131 | 8.5% |
| out_of_scope | training_only | 120 | 7.8% |
| no_harness_description | no_artifact | 97 | 6.3% |
| duplicate_system | evaluation_only | 93 | 6.1% |
| not_retrievable | - | 68 | 4.4% |
| out_of_scope | embodied | 34 | 2.2% |
| out_of_scope | framework_no_default | 29 | 1.9% |
| duplicate_system | survey | 16 | 1.0% |
| no_harness_description | other | 16 | 1.0% |
| no_harness_description | - | 5 | 0.3% |
| other | language | 4 | 0.3% |
| out_of_scope | date | 2 | 0.1% |
| no_harness_description | codability | 1 | 0.1% |
| duplicate_system | benchmark_only | 1 | 0.1% |
| out_of_scope | other | 1 | 0.1% |
| duplicate_system | other | 1 | 0.1% |

| deciding step | n |
|---|---|
| - | 68 |
| 1 | 62 |
| 2 | 566 |
| 3 | 281 |
| 5 | 203 |
| 6 | 29 |
| 7 | 56 |
| 8 | 36 |
| 9 | 4 |
| 10 | 111 |
| 11 | 120 |
| 12 | 5448 |

Confidence: exclude/high: 146, exclude/low: 157, exclude/medium: 1165, include/high: 469, include/low: 848, include/medium: 4131

## 3. Codability (criterion b; count of the 38 dimensions the evidence bundle supports)

Amendment 5: the count is recorded at screening and enforced at coding; step 7 only excludes a record with no admissible artifact at all (`no_harness_description` / `no_artifact`).

| codable_count | all LLM-read records | records reaching step 7 | pass-1 includes |
|---|---|---|---|
| 0-4 | 569 | 119 | 50 |
| 5-9 | 1165 | 541 | 482 |
| 10-14 | 2172 | 1959 | 1943 |
| 15-18 | 1521 | 1494 | 1491 |
| 19-22 | 982 | 976 | 975 |
| 23-26 | 377 | 377 | 377 |
| 27-30 | 108 | 108 | 108 |
| 31-38 | 22 | 22 | 22 |

Includes: median codable_count 15.0, min 2, max 35; exact distribution {2: 9, 3: 15, 4: 26, 5: 54, 6: 51, 7: 113, 8: 106, 9: 158, 10: 249, 11: 348, 12: 395, 13: 458, 14: 493, 15: 437, 16: 394, 17: 335, 18: 325, 19: 356, 20: 239, 21: 211, 22: 169, 23: 140, 24: 97, 25: 73, 26: 67, 27: 44, 28: 33, 29: 17, 30: 14, 31: 7, 32: 8, 33: 5, 34: 1, 35: 1}.
Records reaching step 7: 5596; excluded there for a missing artifact: 44.
codability_flag (all LLM-read records): borderline 2979, fail 2470, pass 1467; among pass-1 includes: borderline 2859, fail 1129, pass 1460.
Repository evidence in the bundle (Amendment 5): 2045/6916 = 29.6% [95% CI 28.5%, 30.7%]; median codable_count 18 with a repository vs 12 without; include rate 1753/2045 = 85.7% [95% CI 84.1%, 87.2%] vs 3695/4871 = 75.9% [95% CI 74.6%, 77.0%].
Layer coverage among includes: A 4997/5448, B 4353/5448, C 5371/5448, D 4659/5448, E 3672/5448, F 3920/5448, G 2130/5448, H 1944/5448.

## 4. Evidence quality and systematic checks

- Quotes found verbatim in the excerpt the model saw (case/punctuation-insensitive): 39848/41380 = 96.3% [95% CI 96.1%, 96.5%]
- Post-hoc flags (pass 1): {'include_below_codability_rule': 3988, 'no_evidence_for_deciding_step': 1279, 'quote_not_in_excerpt': 1226, 'layers_normalized': 244, 'codability_flag_mismatch': 65, 'corrective_retry': 20, 'long_quote': 14, 'include_without_system_name': 14, 'count_mismatch': 8}
- Excerpt words: median 3989.0, max 4151; full-text words: median 5252.5, sent whole (<= cap): 1572
- Document title seen differs from the candidate title (fuzzy < 80): 122 records (arxiv:2311.10776: 'Chemist-X: Large Language Model-Powered Agent for Recommendi'; arxiv:2503.15937: 'V-Droid: Advancing Mobile GUI Agent Through Generative Verif'; arxiv:2504.11788: 'Get Stuck at Errors Rollback by Values'; arxiv:2506.00714: 'RFCAUDIT: AI Agent for Auditing Protocol Implementations Aga'; arxiv:2506.10954: 'SWE Data Construction, Automatically! (SWE-Factory)'; arxiv:2507.14800: 'Large Language Model as An Operator: An Experience-Driven So'; arxiv:2508.20996: 'CHATTHERO: A LANGUAGE AGENT FOR RECOVERY SUPPORT'; arxiv:2510.08952: 'Rethinking Graph Structure Learning in the Era of LLMs (LAGA'; arxiv:2602.15631: 'Meflex: Supporting Entrepreneurial Ideation Through Nonlinea'; arxiv:2603.03686: 'Scientific Discovery under Imperfect Evaluators: Diversity-A'; arxiv:2605.17242: 'From Runnable Code to Shippable Applications: Test-Driven De'; arxiv:2606.20758: 'OpsCortex: Operational Memory for Self-Diagnosing Microservi' ...)

Full-text source used: {'arxiv_pdf': 5478, 'github_repo': 523, 'doi_landing_html': 350, 'openalex_oa_pdf': 195, 'acl_pdf': 137, 'openreview_pdf': 107, 'web_html': 104, 'landing_html': 18, 's2_oa_pdf': 2, 'landing_pdf': 1, 'doi_landing_pdf': 1}

## 5. Independent second reading (pass 1 vs pass 2)

Records read twice: 273 (every pass-1 include plus a hash-based 10% of pass-1 LLM excludes).

|  | pass 2 include | pass 2 exclude |
|---|---|---|
| pass 1 include | 175 | 21 |
| pass 1 exclude | 23 | 54 |

- Cohen's kappa (sample as drawn): 0.599; observed agreement 229/273 = 83.9% [95% CI 79.1%, 87.8%]
- Population-weighted (excludes weighted x10): kappa 0.425, agreement 74.0%
- Pass-1 includes confirmed by pass 2: 175/196 = 89.3% [95% CI 84.2%, 92.9%]
- Sampled pass-1 excludes confirmed by pass 2: 54/77 = 70.1% [95% CI 59.2%, 79.2%]
- Same exclusion code among both-exclude pairs: 51/54 = 94.4% [95% CI 84.9%, 98.1%]; same deciding step: 45/54 = 83.3% [95% CI 71.3%, 91.0%]
- Same system name among both-include pairs (fuzzy >= 90): 163/175 = 93.1% [95% CI 88.4%, 96.0%]
- |codable_count pass 1 - pass 2|: median 2, mean 2.8, max 19

Disagreements:

| record | pass 1 | pass 2 | title seen |
|---|---|---|---|
| acl:arias-russi-etal-2025-uniandes | exclude out_of_scope s3 c7 | include  s12 c20 | Uniandes at TSAR 2025 Shared Task: Multi-Agent CEFR Text Simplificatio |
| acl:mao-etal-2025-alympics | include  s12 c7 | exclude out_of_scope s3 c6 | ALYMPICS: LLM Agents Meet Game Theory |
| acl:zhou-etal-2025-merit | include  s12 c7 | exclude out_of_scope s3 c7 | MERIT: Multi-Agent Collaboration for Unsupervised Time Series Represen |
| arxiv:2305.11854 | exclude out_of_scope s11 c3 | include  s12 c11 | Multimodal Web Navigation with Instruction-Finetuned Foundation Models |
| arxiv:2402.01622 | include  s12 c12 | exclude out_of_scope s2 c6 | TravelPlanner: A Benchmark for Real-World Planning with Language Agent |
| arxiv:2408.11058 | include  s12 c8 | exclude out_of_scope s2 c8 | LLM Agents Improve Semantic Code Search |
| arxiv:2408.12680 | include  s12 c10 | exclude duplicate_system s10 c2 | Can LLMs Understand Social Norms in Autonomous Driving Games? |
| arxiv:2409.01575 | include  s12 c11 | exclude out_of_scope s3 c7 | An Implementation of Werewolf Agent That does not Truly Trust LLMs |
| arxiv:2410.19855 | exclude no_harness_description s1 c4 | include  s12 c11 | Personalized Recommendation Systems using Multimodal, Autonomous, Mult |
| arxiv:2412.20005 | exclude out_of_scope s3 c11 | include  s12 c14 | OneKE: A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction |
| arxiv:2501.14731 | include  s12 c9 | exclude no_harness_description s1 c6 | From Critique to Clarity: A Pathway to Faithful and Personalized Code  |
| arxiv:2507.00979 | include  s12 c8 | exclude out_of_scope s5 c3 | Enhancing LLM Agent Safety via Causal Influence Prompting |
| arxiv:2507.03726 | exclude out_of_scope s3 c9 | include  s12 c12 | AGENT-BASED DETECTION AND RESOLUTION OF INCOMPLETENESS AND AMBIGUITY I |
| arxiv:2507.14705 | include  s12 c8 | exclude out_of_scope s3 c2 | NEO: A Configurable Multi-Agent Framework for Scalable and Realistic T |
| arxiv:2508.00344 | include  s12 c7 | exclude out_of_scope s11 c6 | PilotRL: Training Language Model Agents via Global Planning-Guided Pro |
| arxiv:2509.23586 | exclude out_of_scope s5 c6 | include  s12 c12 | Reducing Cost of LLM Agents with Trajectory Reduction |
| arxiv:2510.11290 | exclude out_of_scope s3 c8 | include  s12 c8 | Evolution in Simulation: AI-Agent School with Dual Memory for High-Fid |
| arxiv:2511.06262 | include  s12 c15 | exclude no_harness_description s1 c8 | GAIA: A General Agency Interaction Architecture for LLM-Human B2B Nego |
| arxiv:2511.06417 | exclude out_of_scope s2 c6 | include  s12 c11 | AUTO-Explorer: Automated Data Collection for GUI Agent |
| arxiv:2512.24461 | include  s12 c10 | exclude out_of_scope s8 c9 | Align While Search: Belief-Guided Exploratory Inference for World-Grou |
| arxiv:2603.22083 | include  s12 c7 | exclude duplicate_system s10 c2 | A Context Engineering Framework for Improving Enterprise AI Agents bas |
| arxiv:2604.09584 | exclude no_harness_description s1 c14 | include  s12 c13 | Agentic Exploration of PDE Spaces using Latent Foundation Models for P |
| arxiv:2606.12848 | exclude duplicate_system s10 c7 | include  s12 c14 | (Human) Attention Is (Still) All You Need: Human oversight makes AI-as |
| arxiv:2606.30877 | include  s12 c13 | exclude out_of_scope s3 c9 | A Systematic Approach to Multi-Agent AI from Advanced Regulatory Contr |
| arxiv:2608.11338 | include  s12 c10 | exclude out_of_scope s8 c10 | Better, Faster, Stronger: Programmatic Skill Learning Best Reduces Age |
| github:Deuz-AI/Deuz-SDK | exclude out_of_scope s6 c17 | include  s12 c28 | Deuz-AI/Deuz-SDK |
| github:karpathy/autoresearch | exclude out_of_scope s5 c5 | include  s12 c13 | karpathy/autoresearch |
| github:trypromptly/LLMStack | exclude out_of_scope s6 c3 | include  s12 c4 | trypromptly/LLMStack |
| leaderboard:osworld:aguvis-72b | exclude out_of_scope s11 c3 | include  s12 c6 | Aguvis: Unified Pure Vision Agents for Autonomous GUI Interaction |
| leaderboard:swe-bench:augment-agent-v1 | include  s12 c7 | exclude out_of_scope s5 c5 | Augment Code: Agentic software development at organizational scale |
| leaderboard:swe-bench:kgcompass | exclude out_of_scope s2 c5 | include  s12 c5 | GLEAM-Lab/KGCompass |
| openreview:LOqTK59rxd | exclude out_of_scope s3 c7 | include  s12 c12 | Symbolic Planning Using LLM Agents: A Cut-Based Reprompting Approach |
| s2:a94ad4474cd0d695d00f4561fac9884896dc6f70 | exclude out_of_scope s3 c5 | include  s12 c13 | LLM-Enhanced Symbolic Control for Safety-Critical Applications |
| s2:bd998002160607cfb8d6fa5c8d6c0932ebb9b79e | include  s12 c9 | exclude out_of_scope s2 c7 | How Well Can Modern LLMs Act as Agent Cores in Radiology Environments? |
| s2_snowball:1971405a882f7f77cda06eff65f2b1005090acea | exclude out_of_scope s11 c7 | include  s12 c10 | VeriOS: Query-Driven Proactive Human-Agent-GUI Interaction for Trustwo |
| s2_snowball:1c9f28d97dca913cbf977fcc14f8a45faac7e9f2 | exclude no_harness_description s1 c9 | include  s12 c15 | Agentic Diagnostic Reasoning over Telecom and Datacenter Infrastructur |
| s2_snowball:266a13a98fd271fc5f76acbdc1e155c18b6fc298 | include  s12 c10 | exclude out_of_scope s2 c7 | APQF: Agentic Profiling-Guided Structured Pruning and Mixed-Precision  |
| s2_snowball:3eb25b4eb27808f9a6c619cdcd764140d691dea8 | exclude out_of_scope s5 c5 | include  s12 c17 | From Exploration to Mastery: Enabling LLMs to Master Tools via Self-Dr |
| s2_snowball:42ed2516e0895da4c4863dcbf47fd1496380730c | exclude out_of_scope s2 c7 | include  s12 c12 | Enhancing repository-level software repair via repository-aware knowle |
| s2_snowball:6f6ad7cce8f47cf6c9f97d50deed618c46251f3f | exclude out_of_scope s2 c1 | include  s12 c2 | ChatTwin: Enabling Natural Language Interactions with Infrastructure D |
| s2_snowball:7f5120db8f2ed7665bbfbff6f04e3e46fb7e0be9 | exclude out_of_scope s11 c0 | include  s12 c19 | Large Action Models: From Inception to Implementation |
| s2_snowball:cf9f14adc07d511d59a8181a4f0b20a21de9c513 | include  s12 c16 | exclude out_of_scope s3 c10 | AI-DRIVEN DAY-TO-DAY ROUTE CHOICE |
| s2_snowball:e41482f4ee984f17382f6cdd900df094d928be06 | include  s12 c20 | exclude out_of_scope s2 c5 | WEBARENA: A REALISTIC WEB ENVIRONMENT FOR BUILDING AUTONOMOUS AGENTS |
| s2_snowball:fa8fa745f58d362925dd44f02750bab1b30a1189 | include  s12 c12 | exclude out_of_scope s8 c11 | RL-GPT: Integrating Reinforcement Learning and Code-as-policy |

## 6. Reference sets

Positive set: 27 known harness systems.

Recall by stage:

- search: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- title_forward: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- fulltext_include: 26/27 = 96.3% [95% CI 81.7%, 99.3%]
- registry: 26/27 = 96.3% [95% CI 81.7%, 99.3%]
- coding_frame: 26/27 = 96.3% [95% CI 81.7%, 99.3%]

| system | candidate records | forwarded | pass-1 include records | in registry | in coding frame | mentioned in n records | lost at |
|---|---|---|---|---|---|---|---|
| ReAct | 9 | 7 | 9 | yes | yes: catalogue;peer_reviewed | 1877 | - |
| Reflexion | 4 | 4 | 1 | yes | yes: catalogue | 777 | - |
| CodeAct | 2 | 2 | 3 | yes | yes: stars;catalogue | 102 | - |
| SWE-agent | 10 | 10 | 7 | yes | yes: stars;catalogue;vendor;peer_reviewed | 392 | - |
| OpenHands | 6 | 6 | 3 | yes | yes: stars;catalogue;vendor | 339 | - |
| AutoGen | 4 | 4 | 5 | yes | yes: stars;catalogue;vendor;peer_reviewed | 601 | - |
| MetaGPT | 1 | 1 | 3 | yes | yes: stars;catalogue;peer_reviewed | 487 | - |
| Agent S | 27 | 18 | 14 | yes | yes: stars;catalogue;stars;catalogue;vendor;peer_reviewed | 74 | - |
| OS-Copilot | 2 | 2 | 2 | yes | yes: stars;catalogue | 21 | - |
| WebArena reference agent | 2 | 2 | 1 | yes | yes: catalogue | 2 | - |
| OSWorld reference agent | 3 | 3 | 2 | yes | yes: catalogue;stars;catalogue | 1 | - |
| tau-bench reference agent | 5 | 4 | 26 | yes | yes: catalogue;vendor;stars;stars;catalogue;vendor;peer_reviewed | 2 | - |
| BrowserGym generic agent | 4 | 4 | 2 | yes | yes: stars;catalogue;stars;catalogue;vendor | 8 | - |
| mini-SWE-agent | 2 | 2 | 1 | yes | yes: catalogue | 99 | - |
| Aider | 4 | 3 | 3 | yes | yes: catalogue;vendor | 76 | - |
| Cline | 2 | 2 | 2 | yes | yes: catalogue;vendor | 26 | - |
| Codex CLI | 3 | 2 | 4 | yes | yes: stars;catalogue;vendor | 118 | - |
| Gemini CLI | 2 | 2 | 2 | yes | yes: catalogue;vendor | 75 | - |
| OpenCode | 4 | 3 | 2 | yes | yes: stars;catalogue;vendor | 141 | - |
| Moatless Tools | 1 | 1 | 1 | yes | yes: catalogue | 26 | - |
| Prometheus | 2 | 2 | 2 | yes | yes: stars;catalogue | 1 | - |
| Claude Code | 5 | 3 | 3 | yes | yes: stars;catalogue;vendor | 644 | - |
| Mistral Vibe | 2 | 2 | 2 | yes | yes: stars;catalogue;vendor | 1 | - |
| Hermes Agent | 1 | 1 | 1 | yes | yes: stars;catalogue | 41 | - |
| Pi | 2 | 2 | 2 | yes | yes: stars;catalogue;vendor | 47 | - |
| OpenClaw | 4 | 3 | 3 | yes | yes: catalogue;vendor | 179 | - |
| AIOS | 3 | 1 | 0 | no | - | 16 | fulltext_include (not screened yet) |

Missing positive reference systems (stage where lost; the full-text decision of matched records):

| system | lost at | matched records | full-text decision(s) | catalogued by |
|---|---|---|---|---|
| AIOS | fulltext_include (not screened yet) | arxiv:2403.16971, arxiv:2608.03214, github:agiresearch/AIOS | - | Meng full-stack harness |

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

- pass 1: 6916 LLM records; busy wall time 104.3 min (union of batch intervals; effective concurrency 4.9); 0.9 s/record wall, 4.5 s/record serial; list-equivalent $372.37 = $0.054/record; tokens/record in 8038, out 420
- pass 2: 261 LLM records; busy wall time 57.5 min (union of batch intervals; effective concurrency 3.9); 13.2 s/record wall, 52.0 s/record serial; list-equivalent $9.47 = $0.036/record; tokens/record in 6103, out 283

Projection to the whole queue (9906 records), from all pass-1 records and the measured rates:

- not retrievable: 1.0% of records -> about 96 without an LLM reading, 9810 read
- includes (pass 1): 5448/6984 = 78.0% [95% CI 77.0%, 79.0%] -> about 7727 records [7630, 7822]
- pass 1: 2.5 h wall at the measured concurrency (4.9), $528 list-equivalent
- pass 2 (7936 records): 29.1 h wall, $288 list-equivalent
- total: 31.6 h, $816 list-equivalent (consumed as Claude Code subscription usage, not billed)

**Warning: the projected include count (~7727 records, 95% CI 7630-7822) is far above the 150-300 systems the protocol expected.** Deduplication into systems will lower it (pilot: 4814 systems from 4814 final includes), but not by that factor if most includes are one-paper systems. The codable_count distribution of includes is in section 3; tightening criterion (b) is the author's decision.

## 8. System registry

4814 systems from 5448 included records; 366 with more than one record.

| system_id | name | members | canonical | max codable | repo |
|---|---|---|---|---|---|
| 1code | 1Code | 1 | awesome:picrew:733956ebc630 | 15 | https://github.com/21st-dev/1code |
| 2 | (EC)2 | 1 | arxiv:2607.26201 | 15 |  |
| 3cb-reference-agent | 3CB reference agent (3CB Harness) | 1 | arxiv:2410.09114 | 12 | https://github.com/apartresearch/3cb |
| 3dify | 3Dify | 1 | arxiv:2510.04536 | 17 |  |
| 3dmedagent | 3DMedAgent | 1 | s2_snowball:f9756057aed446be3a4d2cef2366e1b256a3286a | 20 | https://github.com/jinlab-imvr/3dmedagent |
| 4-agent-multi-llm-klee-pipeline | 4-agent multi-LLM KLEE pipeline | 1 | arxiv:2605.00034 | 15 | https://github.com/zeyad-ab/symbolic-execution-with-multi-llm-architecture-for-rust-security |
| 6gagentgym | 6GAgentGym | 1 | s2_snowball:af78384afb660c94ec2d6915b396a3d886fab642 | 11 |  |
| a-b-agent | A/B Agent | 1 | s2_snowball:a69b25a6f8397a0b044c149bf7af8a54bfba4e5b | 15 |  |
| a-cegis | A-CEGIS | 1 | s2_snowball:3a1cc106a8a8e2255faa291aa348f971b7d6e503 | 13 |  |
| a-dot-planner | A.DOT Planner | 1 | s2_snowball:da7f5c25dc647cd395e3c8745c775d3a714fbc72 | 14 |  |
| a-mapreduce | A-MapReduce | 1 | arxiv:2602.01331 | 23 | https://github.com/mingju-c/amapreduce |
| a-rag | A-RAG | 1 | s2_snowball:54fc75b6dbc48dcda85c73a7a2e4c9d7ef037399 | 23 | https://github.com/ayanami0730/arag |
| a-sr | A-SR | 1 | arxiv:2608.04872 | 11 |  |
| a1 | a1 (Environment Augmented Generation) | 2 | s2_snowball:b5563fdbb1b7ced8b164e827e3c7bea0086ab65f | 22 |  |
| a2h-mas | A2H-MAS | 2 | arxiv:2508.10904 | 12 |  |
| a2o | A2O | 1 | acl:sekii-sato-2026-a2o | 8 |  |
| a2rag | A2RAG | 1 | s2_snowball:2b890cd109c2292051f812858e30c0ad3bb7de0c | 12 |  |
| a3d | A3D | 1 | arxiv:2605.15237 | 15 |  |
| aaas-an | AaaS-AN | 1 | s2_snowball:151698fed4610b0242531fac2bfcf0f0c37a7230 | 10 |  |
| aallm | AaLLM | 1 | arxiv:2608.13472 | 17 |  |
| ab-rag | AB-RAG | 1 | s2_snowball:de0dc75961366c9f38d02e227491d672a335d30e | 12 |  |
| abaqusagent | AbaqusAgent | 1 | arxiv:2606.00138 | 20 | https://github.com/liram-lin/abaqusagent |
| abe-ralph | ABE-Ralph | 1 | arxiv:2608.26753 | 14 | https://github.com/flavorfish/autorepro |
| abex | ABEX | 1 | arxiv:2608.28230 | 14 |  |
| ablatecell | AblateCell | 1 | arxiv:2604.19606 | 14 |  |
| abseeker | ABSeeker | 1 | s2_snowball:d917d2c285201cc6aa89df46bf87b28bf8cda69a | 18 | https://github.com/polarseeker/abseeker |
| acal | ACAL | 1 | arxiv:2602.18916 | 15 | https://github.com/loc110504/acal |
| accelerator-assistant | Accelerator Assistant | 1 | s2_snowball:94462c231aa0c3d7994971013972b5fb9d2cbb3f | 25 |  |
| accelopt | AccelOpt | 1 | arxiv:2511.15915 | 19 | https://github.com/zhang677/accelopt |
| accord | ACCORD | 1 | arxiv:2606.16432 | 15 | https://github.com/jianglai-0023/accord |
| acdc | ACDC (Automated Certificate Detection and Correction) | 1 | arxiv:2607.28928 | 13 | https://github.com/rinard/axontestandrepair |
| ace | ACE (Actor-Critic Embodied Agent, AssistGUI reference agent) | 3 | s2_snowball:24fc9ad715372358bd0108eeb7c944b915963293 | 25 | https://github.com/escottrose01/ace-llm |
| ace-cap | ACE-Cap | 1 | s2_snowball:40fdb8e2572680bf159d8afb29d7b8848acb094b | 8 |  |
| acm | ACM (Agentic Context Management agent) | 1 | s2_snowball:6c1501f6032c2625aee9d5917ebd520bc9f06239 | 20 | https://github.com/lixiaochuan2020/agentic-context-management |
| acmap | ACMAP | 1 | s2_snowball:7f583a90890d8c4ae750676bb66d8f54afd8c97a | 16 |  |
| acoder | ACoder | 1 | leaderboard:swe-bench:acoder | 5 | https://github.com/acoder-ai/acoder |
| acon | ACON (reference ReAct agents) | 1 | arxiv:2510.00615 | 15 | https://github.com/microsoft/acon |
| acrouter | ACRouter | 1 | s2_snowball:6b98c79a18c433ed2e025a5a36fe6eab67015c28 | 16 | https://github.com/lancezpf/agent-as-a-router |
| act | ACT | 1 | acl:nakatsuji-etal-2025-act | 12 |  |
| act-debugger-chained-system | ACT + Debugger chained system | 1 | arxiv:2505.02133 | 14 | https://github.com/nazmus-ashrafi/multiagent_vs_debugger |
| actionrating | ActionRating | 1 | arxiv:2606.11349 | 15 |  |
| active-epistemic-control | Active Epistemic Control (AEC) | 1 | arxiv:2602.03974 | 14 |  |
| activecontext | ActiveContext | 1 | arxiv:2604.11462 | 11 |  |
| activegraph | ActiveGraph (Diligence pack) | 1 | arxiv:2605.21997 | 28 | https://github.com/yoheinakajima/activegraph |
| activemem | ActiveMem | 1 | arxiv:2606.10532 | 12 |  |
| actor | ACToR | 2 | arxiv:2510.03879 | 13 |  |
| actor-critic-pcg-dual-agent | Actor-Critic PCG dual-agent | 1 | arxiv:2512.10501 | 19 |  |
| actuarial-multi-agent-framework-with-bayesian-network-uncertainty-monitor | Actuarial multi-agent framework with Bayesian Network uncertainty monitor | 1 | arxiv:2607.25877 | 12 | https://github.com/bart-custers/actuarial_agents |
| acv-llm | ACV-LLM (LLM-based multi-agent microservice management framework) | 1 | arxiv:2407.14402 | 17 |  |
| ad-care | AD-CARE | 1 | arxiv:2603.25322 | 15 |  |
| ad-mir | AD-MIR | 1 | s2_snowball:01aef622a0a9ed400765ab6dd3b857d08dd90678 | 24 | https://github.com/little-fridge/ad-mir |
| ada | Ada | 1 | arxiv:2606.08500 | 17 |  |
| adacoder | AdaCoder | 1 | arxiv:2504.04220 | 26 | https://github.com/yxingo/adacoder |
| adacom | AdaCoM | 1 | arxiv:2605.30785 | 13 |  |
| adaexplore | AdaExplore | 1 | arxiv:2604.16625 | 21 | https://github.com/stiglidu/adaexplore |
| adalflow | AdalFlow (Agent/Runner) | 1 | github:SylphAI-Inc/AdalFlow | 15 | https://github.com/sylphai-inc/adalflow |
| adam | ADAM (Agent for Digital Atoms and Molecules) | 1 | s2:554099a752231fa2aab45ec15b35d3cc74173b74 | 11 |  |
| adaplan | AdaPlan (PilotRL) | 2 | arxiv:2508.00344 | 15 | https://github.com/import-myself/ahp |
| adaplanner | AdaPlanner | 1 | arxiv:2305.16653 | 19 | https://github.com/haotiansun14/adaplanner |
| adapt | ADaPT | 1 | s2_snowball:0725b276e351bba6b2a52ecb64f3c964b9acc2f9 | 13 |  |
| adaptagent | AdaptAgent | 2 | arxiv:2411.13451 | 15 |  |
| adaptevolve | AdaptEvolve | 1 | arxiv:2602.11931 | 9 |  |
| adaptive-agents-for-debugging | Adaptive Agents for Debugging | 1 | arxiv:2504.18316 | 15 | https://github.com/yacinemajdoub/adaptive-agents-for-debugging |
| adaptive-command | Adaptive Command | 1 | s2_snowball:2ede39666689be19181ca4b534fa651251449271 | 9 |  |
| adaptive-influence-graphs | Adaptive Influence Graphs (AIGs) | 1 | arxiv:2608.24361 | 14 |  |
| adaptive-rag | Adaptive-RAG | 1 | s2_snowball:e5e8c6ac537e0f5b5db14170bc232d6f9e641bbc | 13 | https://github.com/starsuzi/adaptive-rag |
| adaptive-reasoning-and-acting-doctor-agent | Adaptive reasoning and acting doctor agent | 1 | arxiv:2410.10020 | 10 |  |
| adaptive-retrieval-augmented-reasoning-agent | Adaptive Retrieval-Augmented Reasoning Agent | 1 | arxiv:2602.07213 | 10 |  |
| adaptive-self-improvement-agentic-system | Adaptive self-improvement agentic system (PCL-lite) | 1 | arxiv:2502.02534 | 11 | https://github.com/zhang677/pcl-lite |
| adaptorch | AdaptOrch | 1 | arxiv:2602.16873 | 19 | https://github.com/adaptorch/adaptorch |
| adarefiner | AdaRefiner | 1 | s2_snowball:3496c072397fe185c48b83f9b91aa8d5a52bcb87 | 15 | https://github.com/pku-rl/adarefiner |
| adas | ADAS (Meta Agent Search) | 1 | s2_snowball:c9537f656e7d9713fd4108ce7bf512290f48e562 | 14 | https://github.com/shengranhu/adas |
| adaskill | AdaSkill | 1 | s2_snowball:599c6b79f98b23348511d49e4f18344243417cf0 | 12 | https://github.com/tencent/adaskill |
| adavdr | AdaVDR | 1 | s2_snowball:849c928e36699043836bf08c8b9fa4a8ea76fa14 | 13 | https://github.com/accio-lab/adavdr |
| adema | ADEMA | 1 | arxiv:2604.25849 | 12 |  |
| adept | ADEPT (ScientificWorkflowAgent) | 1 | openalex:W4417066576 | 24 | https://github.com/pnnl/adept-agentic-framework-core |
| adias | ADIAS | 1 | arxiv:2608.06410 | 23 | https://github.com/scylj1/adias |
| adk-arena-llm-as-a-developer-agent | ADK Arena LLM-as-a-Developer agent | 1 | arxiv:2606.05548 | 20 | https://github.com/jintao-h/adk-arena |
| adk-based-proactive-contact-center-multi-agent-system | ADK-based proactive contact-center multi-agent system | 1 | openalex:W4417093006 | 8 |  |
| adk-compliance-healing-agent | ADK compliance-healing agent (opa-correction-agentic-adk) | 1 | openalex:W7205452011 | 19 |  |
| adma-copilot | ADMA Copilot | 1 | arxiv:2411.00188 | 12 |  |
| admem | AdMem | 1 | arxiv:2606.06787 | 14 |  |
| adore | ADORE | 1 | s2_snowball:8fb1dbf6ca0021d9f787ab481ce6d202e9f1ce3c | 13 |  |
| adr | ADR | 1 | arxiv:2605.17380 | 18 |  |
| adrd | ADRD | 1 | arxiv:2506.14299 | 18 | https://github.com/bjbcjwsq/adrd |
| adsl | aDSL | 1 | s2:14cde52442db5685ca78bcb90a3c53b6dcc4b82a | 23 | https://github.com/sig-pku/adsl |
| adsl-pde | ADSL-PDE | 1 | s2_snowball:b95f5389c759147baf2ce8ce2e5d800401ad95eb | 15 | https://github.com/super-kongcc/improving-auto-design-of-neural-pde-solvers-with-a-domain-specific-language |
| adsmind | AdsMind | 1 | arxiv:2606.19152 | 28 | https://github.com/nagatobigseven/adsmind |
| adsworldengine | AdsWorldEngine | 1 | s2_snowball:c6109ca668b998549ac743b1d07446611dbee83c | 7 |  |
| adventureagent | AdventureAgent | 1 | openalex:W7163154287 | 2 |  |
| adverintent-agent | AdverIntent-Agent | 1 | arxiv:2505.13008 | 12 |  |
| adversarial-review | Adversarial Review (AR) | 1 | arxiv:2608.18167 | 8 |  |
| adversarially-aligned-llm-defense-agent-framework | Adversarially aligned LLM defense-agent framework | 1 | openalex:W7165153886 | 9 |  |
| advertest | AdverTest | 1 | arxiv:2602.08146 | 20 | https://github.com/jmueducn/advertest |
| advisor-constructor-multi-agent-framework | Advisor-Constructor multi-agent framework | 1 | openalex:W7130935429 | 4 |  |
| adwise | ADWISE | 1 | s2_snowball:37f83a2ee320174b1732c2f20d2562038b5c4a26 | 13 |  |
| aegis | Aegis | 5 | acl:shi-etal-2024-aegis | 21 | https://github.com/evandiewald/aegis |
| ael | AEL | 1 | arxiv:2604.21725 | 13 | https://github.com/wujiangxu/ael |
| aeloon | Aeloon | 1 | s2_snowball:bf55d7d5b908158fb6653c89080fbd1a924ecf52 | 19 | https://github.com/aetherheart-ai/aeloon |
| aem | AEM | 1 | openalex:W7149471451 | 5 | https://github.com/zspirit/aem_project |
| aema | AEMA | 1 | arxiv:2601.11903 | 12 |  |
| aeon | Aeon | 1 | github:aeonfun/aeon | 23 | https://github.com/aeonfun/aeon |
| aerocopilotbench-reference-agent | AeroCopilotBench reference agent | 1 | arxiv:2608.16349 | 14 |  |
| aerotherm-gpt | AeroTherm-GPT | 1 | arxiv:2604.01738 | 16 | https://github.com/tps-qxx/aerotherm-gpt |
| aether | Aether | 1 | s2_snowball:f26f86e103f04ae5af8aa9e85258a4ea245ed885 | 16 |  |
| aevo | AEVO | 1 | s2_snowball:66a87d7b834aa0641bee00d6437195a6315e5598 | 17 |  |
| affordable-generative-agents | Affordable Generative Agents (AGA) | 1 | arxiv:2402.02053 | 15 | https://github.com/affordablegenerativeagents/affordable-generative-agents |
| afl | AFL | 1 | arxiv:2510.16701 | 17 | https://github.com/zhang-ni/afl |
| afm | AFM2 | 1 | arxiv:2506.03530 | 17 | https://github.com/guanzhou-ke/afm2 |
| afm-messenger-afm-pilot-afm-doctor-agentic-framework | AFM Messenger / AFM Pilot / AFM Doctor agentic framework | 1 | arxiv:2608.26198 | 15 |  |
| afspp | AFSPP | 1 | arxiv:2401.02870 | 8 |  |
| afuzz | AFuzz | 1 | arxiv:2605.10074 | 16 |  |
| ag-v2 | AG2 (Agent) | 1 | github:ag2ai/ag2 | 18 | https://github.com/ag2ai/ag2 |
| agao | AGAO | 1 | arxiv:2607.23678 | 8 | https://github.com/mingzhoufan97/agao |
| agel-comp | AGEL-Comp | 1 | arxiv:2604.26522 | 16 | https://github.com/place-beyond-bytes/agel-comp |
| agemem | AgeMem | 1 | arxiv:2601.01885 | 12 |  |
| agensflow | AgensFlow | 1 | arxiv:2605.27466 | 29 | https://github.com/nicolepcx/agensflow |
| agent | Agent0 | 1 | arxiv:2507.18993 | 11 |  |
| agent-alpha | Agent Alpha | 1 | s2_snowball:3d53bb6020cf87a11d34176517acfb3c5265b53c | 11 |  |
| agent-as-a-judge | Agent-as-a-Judge | 1 | s2_snowball:10d2842131634263b5a6875319ff53c0da6a7398 | 21 | https://github.com/metauto-ai/agent-as-a-judge |
| agent-as-tool | Agent-as-tool | 1 | arxiv:2507.01489 | 11 |  |
| agent-banana | Agent Banana | 1 | s2_snowball:3fad43c53fa50fae8e20c51c0cb9eb36943d7b91 | 17 |  |
| agent-based-post-hoc-correction-of-agricultural-yield-forecasts | Agent-Based Post-Hoc Correction of Agricultural Yield Forecasts | 1 | arxiv:2605.12375 | 15 |  |
| agent-based-service-architecture | Agent-Based Service Architecture (ASA) | 1 | openalex:W7130653430 | 13 |  |
| agent-brace | Agent-BRACE | 1 | arxiv:2605.11436 | 14 | https://github.com/joykirat18/agent-brace |
| agent-breakage | agent-breakage (Emily agent under test) | 1 | s2_snowball:08649f99062f1d9624ec0c9017c4666b6ab3e5ad | 13 | https://github.com/odmarkj/agent-breakage |
| agent-capsules | Agent Capsules | 1 | arxiv:2605.00410 | 18 | https://github.com/aray-17/agent-capsules |
| agent-distillation | Agent Distillation | 1 | arxiv:2505.17612 | 21 | https://github.com/nardien/agent-distillation |
| agent-driven-corpus-linguistics | Agent-Driven Corpus Linguistics | 1 | arxiv:2604.07189 | 13 |  |
| agent-driver | Agent-Driver | 1 | arxiv:2311.10813 | 13 |  |
| agent-e | Agent-E | 2 | arxiv:2407.13032 | 21 | https://github.com/emergenceai/agent-e |
| agent-event-coder | Agent-Event-Coder (AEC) | 1 | arxiv:2511.13118 | 14 | https://github.com/uestc-gqj/agent-event-coder |
| agent-expver | Agent-ExpVer | 1 | s2_snowball:20699a99cd939f3faeabd9f16dd2c3536ef89001 | 13 |  |
| agent-for-user | Agent for User (multi-agent TikTok testing) | 1 | arxiv:2504.15474 | 11 |  |
| agent-g | AGENT-G | 3 | openreview:g2C947jjjQ | 22 | https://github.com/sunyuanfu/agentgl |
| agent-gym | Agent Gym | 1 | arxiv:2608.15591 | 16 | https://github.com/google/adk-samples/python/agents/invoice-processing |
| agent-hunt | Agent Hunt | 1 | arxiv:2603.06737 | 13 | https://github.com/mgwiki/alg_top |
| agent-jit | Agent JIT (JIT-Planner/JIT-Scheduler) | 1 | arxiv:2605.21470 | 17 |  |
| agent-laboratory | Agent Laboratory | 1 | arxiv:2501.04227 | 25 |  |
| agent-libos | Agent libOS | 1 | arxiv:2606.03895 | 29 | https://github.com/yingqi-z20/agent-libos |
| agent-lite-medical-assistant | Agent Lite Medical Assistant | 1 | s2_snowball:6c54d04a1cb780f97bbf2de36ec88d036bc5dcc5 | 12 |  |
| agent-native | Agent-Native | 1 | github:BuilderIO/agent-native | 9 | https://github.com/builderio/agent-native |
| agent-nexus | Agent-Nexus | 1 | s2_snowball:1c088c3acd9878fc53667cb10b289437964fb6ad | 12 |  |
| agent-om | Agent-OM | 1 | arxiv:2312.00326 | 15 | https://github.com/qzc438/ontology-llm |
| agent-on-graph | Agent-on-Graph (AoG) | 1 | openalex:W7168032230 | 7 | https://github.com/xuduyinuo/aog |
| agent-orchestrated-adaptive-rag | Agent-Orchestrated Adaptive RAG | 1 | arxiv:2606.05658 | 14 |  |
| agent-q-mix | Agent Q-Mix | 1 | arxiv:2604.00344 | 17 | https://github.com/ericjiang18/agent-q-mix |
| agent-qa | agent-qa | 1 | github:vostride/agent-qa | 13 | https://github.com/vostride/agent-qa |
| agent-rosetta | Agent Rosetta | 1 | arxiv:2603.15952 | 18 |  |
| agent-sama | Agent-SAMA | 1 | arxiv:2505.23596 | 17 |  |
| agent-security-bench | Agent Security Bench | 1 | s2_snowball:5f4efbe3aae1d8f44ceab1da257ae685d6beb00b | 17 | https://github.com/agiresearch/asb |
| agent-squad | Agent Squad (BedrockLLMAgent) | 1 | survey_refs:preprints:202604.0428:61 | 13 | https://github.com/2fastlabs/agent-squad |
| agent-system-interface-mapper-agent | Agent-System Interface mapper agent (Trace + AutoGuide) | 1 | s2_snowball:4e71d7bee58aedf1cb095b371f9be6a2cfbd26e7 | 15 |  |
| agent-teams-ai | Agent Teams AI | 1 | github:777genius/agent-teams-ai | 18 | https://github.com/777genius/agent-teams-ai |
| agent-testing-agent | Agent-Testing Agent (ATA) | 1 | arxiv:2508.17393 | 21 | https://github.com/khalilmrini/agent-testing-agent |
| agent-warpp | Agent WARPP | 1 | arxiv:2507.19543 | 17 |  |
| agent-workflow-memory | Agent Workflow Memory (AWM) | 1 | survey_refs:preprints:202604.0428:80 | 19 | https://github.com/zorazrw/agent-workflow-memory |
| agent0-vl | Agent0-VL | 1 | s2_snowball:ed71e484c8d368302e21c09e614d78a13e467ad6 | 16 | https://github.com/aiming-lab/agent0 |
| agent2world | Agent2World | 1 | arxiv:2512.22336 | 9 |  |
| agent4ct | Agent4CT | 1 | arxiv:2607.22824 | 20 | https://github.com/akmaier/agent4ct |
| agent4debate | Agent4Debate | 1 | arxiv:2408.04472 | 13 | https://github.com/zhangyiqun018/agent-for-debate |
| agent4decompile | Agent4Decompile | 1 | arxiv:2604.23940 | 19 |  |
| agent4dl | Agent4DL | 1 | s2_snowball:e285c0c0afa39198c79b806fc28ef6a698b37a54 | 10 | https://github.com/padas-lab-de/icadl24-agent4dl |
| agentada | AgentAda | 1 | s2_snowball:70886a79f8c61d1a11d5640f812c730197bdf7f0 | 19 | https://github.com/servicenow/agentada |
| agentao | Agentao | 1 | arxiv:2608.13574 | 29 | https://github.com/jin-bo/agentao |
| agentbrew | AgentBrew | 1 | arxiv:2607.16851 | 16 | https://github.com/hkuds/upskill |
| agentbuild | AgentBuild | 1 | arxiv:2606.12834 | 14 |  |
| agentcard | AgentCARD | 1 | arxiv:2606.20629 | 23 | https://github.com/auto-cap/agentcap |
| agentcaster-reference-agent | AgentCaster reference agent | 1 | arxiv:2510.03349 | 13 |  |
| agentcat | AgentCAT | 2 | arxiv:2602.18479 | 11 |  |
| agentcodereview | AgentCodeReview | 1 | s2:4baaec6777466cce8d134008395c5027b73019df | 13 |  |
| agentcomp | AgentComp | 1 | s2_snowball:02ef2fb085a21f03e3afeb3e27bb8c65ef5f655c | 11 | https://github.com/armanzarei/agentcomp |
| agentcot | AgentCOT | 1 | arxiv:2409.12411 | 14 |  |
| agentcvr | AgentCVR | 1 | s2_snowball:6e9e50d30928b7b86dfbcaf7c6d50bb2f1a960ea | 20 | https://github.com/wang-jh24/agentcvr |
| agentdebugx | AgentDebugX (DeepDebug) | 1 | arxiv:2607.18754 | 19 | https://github.com/agentdebugx/agentdebugx |
| agentdojo-reference-agent | AgentDojo reference agent | 1 | arxiv:2406.13352 | 18 | https://github.com/ethz-spylab/agentdojo |
| agentdroid | AgentDroid | 1 | arxiv:2503.12163 | 14 | https://github.com/wwstarry/llm4fraud |
| agentdse | AgentDSE | 1 | arxiv:2606.21836 | 12 |  |
| agentdynex | AgentDynEx | 1 | arxiv:2504.09662 | 13 |  |
| agentehr | AgentEHR (RetroSum agent) | 1 | s2_snowball:d1972db80f51d43ecc222cac9a737dd820558932 | 18 | https://github.com/bluezeros/agentehr |
| agentexecutor | AgentExecutor | 1 | arxiv:2608.05959 | 12 |  |
| agentfactory | AgentFactory | 1 | s2_snowball:673bfc540c0d21b033076491c93c04ea90ac013a | 25 | https://github.com/zzatpku/agentfactory |
| agentfinvqa | AgentFinVQA | 1 | s2_snowball:dd277c0e0c55ae6ada0dcfc7c8a6d724ff82392b | 18 |  |
| agentfl | AgentFL | 2 | arxiv:2403.16362 | 20 | https://github.com/agent-one-lab/agentfly |
| agentflow | AgentFlow | 2 | arxiv:2510.05592 | 17 |  |
| agentflux | AgentFlux | 1 | arxiv:2510.00229 | 13 |  |
| agentfold | AgentFold | 3 | arxiv:2510.24699 | 21 | https://github.com/alibaba-nlp/deepresearch |
| agentforge | AgentForge | 1 | arxiv:2604.13120 | 21 | https://github.com/raja21068/autocodeai |
| agentfox | AgentFoX | 1 | s2_snowball:0733167a4e3fac92bc16aeb61cf8df1d7ecf2d0e | 20 | https://github.com/suncore946/agentfox |
| agentfugue | AgentFugue (Cabeza) | 1 | s2_snowball:5413c1700410467f3a7a9f921c2ecf44aa8201fa | 20 | https://github.com/qhjqhj00/cabeza |
| agentgroupchat-v2 | AgentGroupChat-V2 | 1 | arxiv:2506.15451 | 18 | https://github.com/mikegu721/agentgroupchat-v2 |
| agentguard | AgentGuard | 1 | arxiv:2502.09809 | 10 |  |
| agenthoi | AgentHOI | 1 | arxiv:2607.13881 | 9 | https://github.com/oceanflowlab/agenthoi |
| agentic-additive-manufacturing-alloy-evaluation | Agentic Additive Manufacturing Alloy Evaluation (Claude Code multi-agent) | 1 | arxiv:2510.02567 | 16 | https://github.com/baratilab/agentic-additive-manufacturing-alloy-evaluation |
| agentic-adversarial-rewriting-framework | Agentic adversarial rewriting framework (Attacker Agent + Prompt Optimization Agent) | 1 | s2_snowball:23073976b112080f9607fdc6a03d244ff852fcd8 | 16 |  |
| agentic-ai-autonomous-defense-framework | Agentic AI Autonomous Defense Framework | 1 | arxiv:2512.23480 | 15 |  |
| agentic-ai-control-plane-for-6g-network-slicing | Agentic AI Control Plane for 6G Network Slicing | 1 | arxiv:2602.13227 | 10 |  |
| agentic-ai-framework-for-cell-free-o-ran | Agentic AI framework for cell-free O-RAN | 1 | arxiv:2602.22539 | 11 |  |
| agentic-ai-framework-for-enterprise-hris | Agentic AI Framework for Enterprise HRIS | 1 | s2:3ee77afc70e2fd62861bc787a4e6843f7bfe952e | 5 |  |
| agentic-ai-framework-for-medicinal-leaf-analysis | Agentic AI framework for medicinal leaf analysis | 1 | s2_snowball:1fc366e80c6d91ec17531145c176d8e548031280 | 7 |  |
| agentic-ai-hardware-design-and-verification-mas | Agentic AI hardware design and verification MAS | 1 | arxiv:2507.02660 | 15 |  |
| agentic-ai-hems | Agentic AI HEMS | 1 | s2_snowball:37a5d33d8f313358915f802801b4ab8071232399 | 23 | https://github.com/redaelmakroum/agentic-ai-hems |
| agentic-ai-wi-fi-mapc-framework | Agentic AI Wi-Fi MAPC framework | 1 | arxiv:2511.20719 | 14 |  |
| agentic-autosurvey | Agentic AutoSurvey | 1 | arxiv:2509.18661 | 15 |  |
| agentic-bitween | Agentic Bitween | 1 | arxiv:2412.18134 | 13 | https://github.com/ferhaterata/learning-randomized-reductions |
| agentic-breaking-change-repair-system | Agentic breaking-change repair system | 1 | s2_snowball:ff78bd4dc3353b438a25f01f9f43391195e8d81d | 18 |  |
| agentic-cloud-workflow-engineering | Agentic Cloud Workflow Engineering | 1 | arxiv:2609.00050 | 25 |  |
| agentic-clustering | Agentic Clustering | 1 | arxiv:2606.01255 | 13 |  |
| agentic-collaborative-cognition | Agentic Collaborative Cognition | 1 | s2:5ebbdd61a24baaf57d369ccd6921154cb1ef8de5 | 12 | https://github.com/zhangbo135/agentic-collaborative-cognition |
| agentic-commerce-multi-retrieval-framework | Agentic Commerce multi-retrieval framework | 1 | s2:71c6f60188ed070abdae2ede61e062d1814360c4 | 15 |  |
| agentic-context-cracking | Agentic Context Cracking | 1 | arxiv:2608.31082 | 7 |  |
| agentic-control-plane | Agentic Control Plane (ACP) | 1 | s2:94752218d894e2b20bd9b6b1938626488c092c40 | 11 |  |
| agentic-counterfactual-graphrag | Agentic Counterfactual GraphRAG | 1 | s2_snowball:c0327249d40124efad3c0d1e45f229a218518b05 | 8 |  |
| agentic-cpu-gpu-scheduler | Agentic CPU-GPU scheduler | 1 | s2:eb3e4d1edd73880aabb947a24b8a20a006234898 | 10 |  |
| agentic-episodic-control | Agentic Episodic Control (AEC) | 1 | s2_snowball:966423188dcdb22dcb29bfc08890f32b7791e83a | 15 | https://github.com/xidong-yang/agentic_episodic_control |
| agentic-erp | Agentic ERP | 1 | arxiv:2607.17331 | 18 |  |
| agentic-esg-framework | Agentic ESG framework (multi-agent architecture) | 1 | arxiv:2603.10646 | 11 | https://gitlab.com/for_peer_review-group/esg_assistant |
| agentic-floor-plan-parsing-pipeline | Agentic floor plan parsing pipeline | 1 | arxiv:2604.23970 | 13 |  |
| agentic-flow | Agentic Flow | 1 | github:ruvnet/agentic-flow | 13 | https://github.com/ruvnet/agentic-flow |
| agentic-form-like-document-extraction-framework | Agentic form-like document extraction framework | 1 | arxiv:2505.13504 | 16 |  |
| agentic-graphrag | Agentic GraphRAG (SHAB) | 1 | s2_snowball:2fdcfc04b63bc00d4f9ccb458ff9d1eb38e53e5e | 17 |  |
| agentic-graphrag-with-word-spotting | Agentic GraphRAG with word spotting (historical KG) | 1 | s2_snowball:61f4db0ee7b7732270f93668d1ef25ac0808a2e9 | 12 |  |
| agentic-ideation | Agentic-Ideation | 1 | arxiv:2606.31229 | 7 |  |
| agentic-incident-resolution-architecture | Agentic incident resolution architecture (Azure Networking) | 1 | s2_snowball:6f9297b462beaf2e228ea35636f777774c4a7dfb | 24 |  |
| agentic-incident-response-multiscale-planner | Agentic incident response multiscale planner | 1 | arxiv:2608.02422 | 11 | https://github.com/taoli-nyu/agentic-incident-response-esorics26 |
| agentic-ioev-framework | Agentic IoEV framework | 1 | arxiv:2509.12233 | 11 |  |
| agentic-keyword-search-agent | Agentic keyword search agent | 1 | arxiv:2602.23368 | 16 |  |
| agentic-ltpo | Agentic-LTPO | 1 | s2_snowball:04cb552cc3540e3e3d30b66ae94e4a4740761c88 | 10 |  |
| agentic-lybic | Agentic Lybic | 1 | leaderboard:osworld:agentic-lybic-maestro | 15 | https://github.com/xlang-ai/osworld/mm_agents/maestro |
| agentic-matrix-deflation | Agentic Matrix Deflation | 1 | arxiv:2601.08219 | 14 | https://github.com/pie115/agentic-deflation |
| agentic-memory-augmented-retrieval-and-evidence-grounding-system | Agentic memory-augmented retrieval and evidence grounding system | 1 | s2:5ae2867fb5272ceaa7a70d03d2a1321bab4e09d5 | 14 |  |
| agentic-meta-orchestrator | Agentic Meta-Orchestrator (AMO) | 1 | s2_snowball:db6141df6f0880ba44c84069997312d525864e6b | 7 | https://github.com/xiaofengzhu/amo |
| agentic-modernization-architecture-for-higher-education | Agentic modernization architecture for higher education | 1 | s2:e80052b89aa35b2ee92677a588f92402f2f4d122 | 14 |  |
| agentic-monte-carlo | Agentic Monte Carlo (AMC) | 1 | arxiv:2606.05296 | 14 | https://github.com/layer6ai-labs/agentic-monte-carlo |
| agentic-nesting | Agentic Nesting (Application-as-Agent framework) | 1 | s2_snowball:d908d6693ff3f5dfe79b49daa712ccd514e9bc0a | 14 |  |
| agentic-ooda-framework | Agentic OODA Framework | 1 | openalex:W7172333118 | 15 |  |
| agentic-optimization | agentic-optimization (Orchestrator/Investigator/Reviewer) | 1 | arxiv:2603.27415 | 21 | https://github.com/yitao416/agentic-optimization |
| agentic-pbt-agent | Agentic PBT agent | 1 | s2_snowball:e46ee1e13f118c63cbddbaeb59fdd7d5dba86988 | 20 | https://github.com/mmaaz-git/agentic-pbt |
| agentic-policy-search | Agentic Policy Search (APS) | 1 | s2_snowball:48f00745feca6545a293d9dbaee0f4c189121542 | 9 |  |
| agentic-re-identification-pipeline | Agentic re-identification pipeline | 1 | s2_snowball:f1bf8ec347222adcbe5376aeb25fd2c77df74243 | 14 |  |
| agentic-reasoning | Agentic Reasoning | 1 | arxiv:2502.04644 | 19 | https://github.com/theworldofagents/agentic-reasoning |
| agentic-researcher | The Agentic Researcher | 1 | arxiv:2603.15914 | 23 | https://github.com/zib-iol/the-agentic-researcher |
| agentic-retrobiosynthesis-framework | Agentic Retrobiosynthesis Framework | 1 | s2_snowball:43d820f694dc9b72a4010f513688165acda4a9d9 | 9 |  |
| agentic-risk-aware-set-based-engineering-design-framework | Agentic Risk-Aware Set-Based Engineering Design framework | 1 | arxiv:2604.16687 | 13 |  |
| agentic-rl-harness | Agentic-RL-harness (Harness MDP controller) | 1 | arxiv:2607.05458 | 20 | https://github.com/hik289/agentic-rl-harness |
| agentic-router | Agentic Router | 1 | arxiv:2608.09184 | 16 |  |
| agentic-rubrics | Agentic Rubrics | 1 | s2_snowball:2d758cf3e9c5815e6d2f1bb8b23d331ba8bbcad9 | 12 |  |
| agentic-smart-contract-pipeline | Agentic smart contract pipeline | 1 | s2_snowball:95c322759bce6fb7ba564621fa0bf2f60e88a786 | 13 |  |
| agentic-spatio-temporal-text-to-sql-pipeline | Agentic spatio-temporal Text-to-SQL pipeline | 1 | arxiv:2510.25997 | 12 |  |
| agentic-swmm | Agentic SWMM | 1 | s2_snowball:cab5089a8583ad829f430fab366b21ebf7fd4e4c | 12 | https://github.com/zhonghao1995/agentic-swmm-workflow |
| agentic-tool-making-pipeline-alarm-triage-agent | agentic tool-making pipeline / alarm-triage agent (built on Eluna) | 1 | arxiv:2607.08010 | 20 |  |
| agentic-torch2jax | Agentic Torch2JAX | 1 | openalex:W7163839364 | 9 |  |
| agentic-visualization-refinement-pipeline | Agentic Visualization Refinement Pipeline | 1 | arxiv:2604.15319 | 10 |  |
| agentic-xai | Agentic XAI | 1 | s2_snowball:87466ae6388c564befdd116a62f96db570bde5e3 | 9 |  |
| agenticad | AgenticAD | 1 | arxiv:2510.08578 | 12 |  |
| agenticaita | AgenticAITA | 1 | arxiv:2605.12532 | 25 |  |
| agenticcann | AgenticCANN | 1 | s2_snowball:1e2fc04a7809053ffe1716c31087d1ff2b79593a | 18 |  |
| agenticdata | AgenticData | 1 | s2_snowball:04cfb90a12972f114b17c757ed89f944c3777aa1 | 14 |  |
| agenticeco | AgenticECO | 1 | s2_snowball:b3b54e0c8571ed07b1645b9ccda912b17dcd1d5e | 20 |  |
| agenticeval | AgenticEval | 1 | arxiv:2509.26100 | 10 |  |
| agenticfs4eeg | AgenticFS4EEG | 1 | acl:aiersilan-qu-2026-agentic | 17 | https://github.com/ezharjan/agenticfs4eeg |
| agentick-reference-agent | Agentick reference agent | 1 | arxiv:2605.06869 | 15 | https://github.com/roger-creus/agentick |
| agenticpa | AgenticPA | 1 | openreview:tX2mU5O0Ux | 17 |  |
| agenticpd | AgenticPD | 1 | arxiv:2607.04758 | 17 |  |
| agenticrag | AgenticRAG | 3 | s2_snowball:55be92434d1140c4308e8a54e8c14cdc2eaeb613 | 18 | https://github.com/jiangxinke/harness-rl |
| agenticrec | AgenticRec | 1 | arxiv:2603.21613 | 12 |  |
| agenticrepair | AgenticRepair | 1 | arxiv:2607.29422 | 14 |  |
| agenticscr | AgenticSCR | 1 | arxiv:2601.19138 | 14 |  |
| agenticszz | AgenticSZZ | 1 | arxiv:2602.02934 | 21 | https://github.com/sailresearch/agenticszz |
| agentictcad | AgenticTCAD | 1 | arxiv:2512.23742 | 11 |  |
| agentictyper | AgenticTyper | 1 | s2_snowball:ad43bca5e1c254dc968f20624ea8fc483d549206 | 14 | https://github.com/clemens-mw/agentic-typer |
| agenticvau | AgenticVAU | 1 | s2_snowball:ac66da6db38f4f95847682f760cb2ca05ad21abe | 13 |  |
| agentigraph | AGENTiGraph | 2 | arxiv:2410.11531 | 18 | https://github.com/sinketsuzao/agentigraph |
| agentiloop-agent | AgentiLoop Agent! | 1 | github:AgentiLoop/Agent | 26 | https://github.com/agentiloop/agent |
| agentkgv | AgentKGV | 1 | s2_snowball:b86f4f1b2c6a5e131f517a9e44b7b95ee70a50fd | 15 |  |
| agentkit | AgentKit | 1 | arxiv:2404.11483 | 14 |  |
| agentlab | AgentLab (GenericAgent) | 2 | arxiv:2403.07718 | 21 | https://github.com/servicenow/agentlab |
| agentlite | AgentLite (BaseAgent) | 1 | arxiv:2402.15538 | 20 | https://github.com/salesforceairesearch/agentlite |
| agentloop | AgentLoop (S1-DeepResearch) | 1 | s2_snowball:bc782e71f962182b94ac69eca75771a6c0666c75 | 12 | https://github.com/scienceone-ai/s1-deepresearch |
| agentmandering | Agentmandering | 1 | arxiv:2511.04076 | 14 | https://github.com/lihaogx/agentmandering |
| agentmap | AgentMap | 1 | arxiv:2607.27130 | 11 |  |
| agentmaster | AgentMaster | 1 | arxiv:2507.21105 | 9 |  |
| agentmath | AgentMath | 1 | arxiv:2512.20745 | 9 |  |
| agentmd | AgentMD | 1 | arxiv:2402.13225 | 9 |  |
| agentmesh | AgentMesh | 1 | arxiv:2507.19902 | 16 |  |
| agentmob | AgentMob | 1 | arxiv:2606.05130 | 14 |  |
| agentnet | AgentNet | 1 | arxiv:2504.00587 | 9 |  |
| agentnlq | AgentNLQ | 1 | arxiv:2605.19010 | 20 |  |
| agentoccam | AgentOccam | 1 | arxiv:2410.13825 | 16 | https://github.com/amazon-science/agentoccam |
| agentode | AgentODE | 1 | s2_snowball:b6ffc021cfc54bd9868f1e08568b7392cf11b94b | 21 | https://github.com/hanningyang/agentode |
| agentodrl | AgentODRL | 1 | arxiv:2512.00602 | 17 | https://github.com/ruc-mas/agentodrl |
| agentopia | Agentopia | 1 | arxiv:2606.07513 | 23 | https://github.com/neph0s/agentopia |
| agentoptics | AgentOptics | 1 | s2_snowball:63e43566276e5f8e2fbfb5b6b410cb2e69344ef1 | 11 |  |
| agentorchestra | AgentOrchestra | 2 | arxiv:2506.12508 | 21 |  |
| agentpanel | AgentPanel | 1 | arxiv:2608.03283 | 19 |  |
| agentpoirot | AgentPoirot | 1 | s2_snowball:739526c3ba9536953b65373d66d3469138e227ef | 12 | https://github.com/servicenow/insight-bench |
| agentprobe | AgentProbe | 1 | openalex:W7204584025 | 18 | https://github.com/ayanverse-io/agentprobe |
| agentran | AgentRAN | 1 | arxiv:2508.17778 | 14 |  |
| agentrewind | AgentRewind | 1 | arxiv:2608.14380 | 19 | https://github.com/futuresis/replay-agent-recorder |
| agentrr | AgentRR | 1 | arxiv:2505.17716 | 11 |  |
| agentrxiv | AgentRxiv | 1 | arxiv:2503.18102 | 12 |  |
| agents-help-agents | Agents Help Agents (AHA) | 1 | openreview:hREMYJ5ZmD | 14 |  |
| agents-last-exam-reference-agent | Agents' Last Exam reference agent (ALE-Claw) | 1 | github:rdi-berkeley/agents-last-exam | 11 | https://github.com/rdi-berkeley/agents-last-exam |
| agents-llm | AGENTS-LLM | 1 | arxiv:2507.13729 | 12 | https://github.com/boschresearch/agents-llm |
| agents-research-environments-reference-agent | Agents Research Environments (ARE) reference agent | 1 | arxiv:2602.11964 | 8 |  |
| agents-v2 | Agents 2.0 (agent symbolic learning) | 2 | arxiv:2406.18532 | 20 | https://github.com/aiwaves-cn/agents |
| agents4gov | Agents4Gov | 1 | s2:3186582f676f8b7a11d8841af203c35d6c5b8565 | 17 | https://github.com/labic-icmc-usp/agents4gov |
| agents4plc | Agents4PLC | 1 | arxiv:2410.14209 | 16 | https://github.com/luoji-zju/agents4plc_release |
| agentscad | AgentsCAD | 1 | s2:cd1756ca3352f02d9ac304907441e03c7cb82192 | 14 |  |
| agentschool | AgentSchool | 1 | arxiv:2605.30144 | 18 | https://github.com/epitome-aiss/agentschool |
| agentscope | AgentScope (ReAct Agent) | 5 | github:agentscope-ai/agentscope | 25 | https://github.com/agentscope-ai/agentscope |
| agentscore | AgentScore | 1 | arxiv:2601.22324 | 18 | https://github.com/sr933/agentscore-official |
| agentscourt | AgentsCourt | 1 | arxiv:2403.02959 | 11 |  |
| agentsense | AgentSense | 1 | arxiv:2510.19661 | 17 |  |
| agentsgen | AgentSGEN | 1 | arxiv:2505.13466 | 18 |  |
| agentsims | AgentSims | 1 | arxiv:2308.04026 | 9 |  |
| agentskillos | AgentSkillOS | 1 | s2_snowball:195e91c591051e2f4fa7aa57e1d915f1b4883a19 | 19 | https://github.com/ynulihao/agentskillos |
| agentslr | AgentSLR | 1 | arxiv:2603.22327 | 16 |  |
| agentsociety | AgentSociety | 1 | acl:zhang-etal-2025-parallelized | 20 | https://github.com/tsinghua-fib-lab/agentsociety |
| agentspex | AgentSPEX | 1 | arxiv:2604.13346 | 30 | https://github.com/scaleml/agentspex |
| agentsquare | AgentSquare | 1 | arxiv:2410.06153 | 15 | https://github.com/tsinghua-fib-lab/agentsquare |
| agentstore | AgentStore | 1 | s2_snowball:01101ec460b47c7a26e5a5ff26c38d1ef5bfcb97 | 13 |  |
| agentswing | AgentSwing | 1 | arxiv:2603.27490 | 15 |  |
| agentsymbiotic | AgentSymbiotic | 1 | arxiv:2502.07942 | 12 |  |
| agentsys | AgentSys | 2 | arxiv:2602.07398 | 20 | https://github.com/ruoyaow/agentsys-memory |
| agentszz | AgentSZZ | 1 | arxiv:2604.02665 | 20 |  |
| agentteams | AgentTeams | 1 | github:agentscope-ai/AgentTeams | 14 | https://github.com/agentscope-ai/agentteams |
| agenttether | AgentTether | 1 | arxiv:2607.06273 | 13 |  |
| agenttts | AgentTTS | 1 | arxiv:2508.00890 | 17 | https://github.com/fairyfali/agenttts |
| agenttutor | AgentTutor | 1 | arxiv:2601.04219 | 13 |  |
| agentverse | AgentVerse (task-solving) | 1 | s2:0e216675d4a21726872f3f4b0d4f9c446cf50aff | 20 | https://github.com/openbmb/agentverse |
| agentvisor | AgentVisor | 1 | s2:cf32c4016c102fac6ce1fef1e93539bc3de781cd | 16 |  |
| agentwebbench-reference-agent | AgentWebBench reference agent | 1 | openreview:aNtMUFWjnD | 21 | https://github.com/cxcscmu/agentwebbench |
| agentx | AgentX | 1 | s2_snowball:64925a61e72584112145bb0e89a0eab383aac6b9 | 17 |  |
| agentxgcore | AgentxGCore | 1 | arxiv:2606.00417 | 12 |  |
| agentxploit | AgentXploit | 1 | openreview:xKJ0lVQEv7 | 10 |  |
| agentxray | AgentXRay | 1 | s2_snowball:2ceca7f97c7f2ac878304f85eea573293f1a0221 | 5 |  |
| aggagent | AggAgent | 1 | s2_snowball:8af3b35420ceb85b157bfdacdfcff8a619926f2d | 19 | https://github.com/princeton-pli/aggagent |
| agi-maze-reference-agent | AGI Maze reference agent | 1 | arxiv:2607.00627 | 13 | https://github.com/necr0x0der/agimaze-bench |
| agile | AGILE | 1 | arxiv:2405.14751 | 19 | https://github.com/bytarnish/agile |
| agilecoder | AgileCoder | 1 | s2_snowball:502d27f7034157cf80c3c9a08a6fd073f0811fb4 | 20 | https://github.com/fsoft-ai4code/agilecoder |
| agilethinker | AgileThinker | 1 | s2_snowball:c1310e315f1657330a5c0c87a1017585379abe57 | 19 | https://github.com/salt-nlp/realtimegym |
| agint | Agint | 1 | arxiv:2511.19635 | 10 |  |
| agnt | AGNT | 1 | github:agnt-gg/agnt | 20 | https://github.com/agnt-gg/agnt |
| agon | Agon | 1 | awesome:gloriaameng:b656d8bb4e49 | 13 |  |
| agora-opt | Agora-Opt | 1 | arxiv:2604.25847 | 20 | https://github.com/chiangel/agora-opt |
| agr | AGR | 1 | s2:137dac17d09a94ad5fdc5cbc7b836401f34d406c | 14 |  |
| agrefactor | AgRefactor | 1 | arxiv:2606.30949 | 16 |  |
| agri-sage | Agri-SAGE | 1 | arxiv:2607.00454 | 16 |  |
| agriagent | AgriAgent | 1 | s2_snowball:91565a5111884a83e5c9c197eebd5514e63b4fb4 | 14 |  |
| agricultural-vqa-multi-agent-framework | Agricultural VQA multi-agent framework (Retriever, Reflector, Answerer, Improver) | 1 | s2_snowball:0a1083e4d0e5e7001054f4a82f96d4e9caba0750 | 13 |  |
| aguvis | Aguvis | 1 | leaderboard:osworld:aguvis-7b | 4 |  |
| aha | AHA (Agent Hacks Agent) | 1 | arxiv:2607.11698 | 22 | https://github.com/henrymao2004/auto-research-red-teaming |
| ahe | AHE (Agentic Harness Engineering) | 2 | github:china-qijizhifeng/agentic-harness-engineering | 20 | https://github.com/china-qijizhifeng/agentic-harness-engineering |
| ahois | AHOIS | 1 | s2_snowball:ad50ac19093872bf179896318e02edd24c271c33 | 13 |  |
| ahoy | Ahoy | 1 | s2_snowball:7b332428b3664ac571385edcdcca161781675797 | 20 | https://github.com/oj98/ahoy |
| ai-assisted-space-thermal-analysis-prototype | AI-assisted space thermal analysis prototype | 1 | s2:23fee115baaed0112f609c38a1749f5dc72329e8 | 5 |  |
| ai-cfd-scientist | AI CFD Scientist | 1 | arxiv:2605.06607 | 25 | https://github.com/csml-rpi/ai-cfd-scientist |
| ai-chart-review-agent | AI chart-review agent | 1 | s2:0415e9eb6fab8e4a2103b9760aaeeda92f83ef2e | 10 |  |
| ai-co-scientist-for-ranking | AI Co-Scientist for Ranking | 1 | arxiv:2603.22376 | 17 |  |
| ai-cro | AI-CRO | 1 | arxiv:2510.01115 | 15 |  |
| ai-driven-autonomous-web-testing-framework | AI-driven autonomous web testing framework | 1 | s2_snowball:340ce9eacd38ea5325859a8a11cfbf4b2d8e6f55 | 14 |  |
| ai-engineer | The AI Engineer | 1 | arxiv:2608.21976 | 19 | https://github.com/rainbowyuyu/aipengineer |
| ai-glasses-system | AI glasses system | 1 | arxiv:2601.06235 | 5 |  |
| ai-gram | AI-GRAM | 1 | arxiv:2604.21446 | 14 |  |
| ai-historian | AI Historian (AIH) | 1 | arxiv:2608.29133 | 8 |  |
| ai-hydro | AI-Hydro | 1 | openalex:W7154479624 | 22 | https://github.com/ai-hydro/ai-hydro |
| ai-job-market-consultant | AI Job Market Consultant | 1 | arxiv:2511.14767 | 12 | https://github.com/albusnotthuan/jobs-agent-streamlit |
| ai-mandel | AI-Mandel | 1 | arxiv:2511.11752 | 13 |  |
| ai-native-tdd-framework | AI-Native TDD framework | 1 | arxiv:2604.26615 | 16 |  |
| ai-office | AI Office (Team of Rivals) | 1 | s2_snowball:b4de19bfbf02de734b3ffd3947b69b7aa0812f60 | 23 |  |
| ai-powered-math-tutoring-platform | AI-Powered Math Tutoring platform | 1 | arxiv:2507.12484 | 15 | https://github.com/feilaz/ai_powered_math_tutoring |
| ai-powered-personalized-trip-planner | AI-Powered Personalized Trip Planner | 1 | s2:d5038559f5083ffca86baa818ad6d79d1fd665c7 | 14 |  |
| ai-press | AI-Press | 1 | arxiv:2410.07561 | 9 |  |
| ai-product-research-agent | AI Product Research Agent (Flipkart) | 1 | s2_snowball:376b2e2a81e1629fb948e253ff424aec31a7dbd3 | 8 |  |
| ai-researcher | AI-Researcher | 1 | arxiv:2505.18705 | 20 | https://github.com/hkuds/ai-researcher |
| ai-scientist | The AI Scientist | 1 | arxiv:2408.06292 | 19 | https://github.com/sakanaai/ai-scientist |
| ai-shopping-mate | AI Shopping Mate | 1 | s2_snowball:b92a752d42f958396b4d38a5971bdfe27217915b | 12 |  |
| ai-studio | AI Studio | 1 | openalex:W7163879843 | 11 | https://github.com/dasarathirout/dasarathi-aistudio |
| ai-telco-engineer | The AI Telco Engineer (AITE) | 1 | s2_snowball:1e78dd4968d52fac621d8a33efdd3878b673ff41 | 27 | https://github.com/nvlabs/the-ai-telco-engineer |
| ai-tour-meeting | AI Tour Meeting | 1 | arxiv:2607.18806 | 22 | https://github.com/ntt-dkiku/ai-tour-meeting |
| ai-training-manager | AI Training Manager | 1 | arxiv:2606.29871 | 18 |  |
| ai-urban-scientist | AI Urban Scientist | 1 | arxiv:2512.07849 | 16 |  |
| ai-werewolf-multi-agent-experiment-platform | AI Werewolf Multi-Agent Experiment Platform | 1 | arxiv:2607.10814 | 29 | https://github.com/jjjayden-yang/ai-werewolf |
| ai-x-ray-scientist | AI X-ray scientist | 1 | openalex:W4413766540 | 15 |  |
| ai4bayescode | AI4BayesCode | 1 | arxiv:2605.18476 | 9 |  |
| ai4s-low-code-platform | AI4S Low-code Platform (Bayesian Adversarial Multi-Agent Framework) | 1 | arxiv:2603.03233 | 13 |  |
| ai4s-sds | AI4S-SDS | 1 | arxiv:2603.03686 | 9 |  |
| aibuildai | AIBuildAI | 1 | arxiv:2604.14455 | 24 | https://github.com/aibuildai-inc/ai-build-ai |
| aibuildai-v2 | AIBuildAI-2 | 1 | s2_snowball:61ce58419d789ed4164533e591b7ddb4e3f7077f | 8 |  |
| aicce | AICCE | 1 | arxiv:2604.03330 | 11 |  |
| aicp | AICP | 1 | openalex:W7165853431 | 7 |  |
| aida | AIDA | 1 | s2_snowball:1df6ac9eb34d163d4b5d4cb8ae127ae6cc2f30d7 | 16 |  |
| aide | AIDE | 1 | s2_snowball:6eeaf1e7b3be81eb1f44f80906757964e6183fec | 33 | https://github.com/wecoai/aideml |
| aider | Aider | 3 | awesome:picrew:da950c021dac | 12 | https://github.com/aider-ai/aider |
| aila | AILA | 1 | arxiv:2501.10385 | 19 | https://github.com/m3rg-iitd/aila |
| ailice | AIlice | 1 | github:myshell-ai/AIlice | 21 | https://github.com/myshell-ai/ailice |
| ailmir | AILMIR | 1 | s2_snowball:7b29b00823400450fe153e892c5bfeabc40127c1 | 6 | https://github.com/swu-cs-medialab/ailmir |
| aim-rm | AIM-RM | 1 | arxiv:2602.05524 | 13 |  |
| aime | Aime | 1 | arxiv:2507.11988 | 14 |  |

