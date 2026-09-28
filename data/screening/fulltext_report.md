# Full-text screening report

Generated 2026-09-28 18:01 UTC by `scripts/validate_screening.py`.
Scope: 9967 records (data/screening/fulltext_queue.csv); pass-1 rows 4272, pass-2 rows 0, final rows 8435, systems 6504.

## 1. Decisions

Model(s): {'claude-opus-5': 4124, 'claude-opus-4-8': 56, 'claude-sonnet-5': 16}; prompt(s): {'ft-v2-2026-09-18': 4272}.

- Pass-1 include rate, all records in scope: 2921/4272 = 68.4% [95% CI 67.0%, 69.8%]
- Pass-1 include rate, records with full text (LLM read): 2921/4196 = 69.6% [95% CI 68.2%, 71.0%]
- not_retrievable (index says not ok; no LLM call): 76
- Pending (in scope, no pass-1 row yet): 5696
- Final (after pass 2 and the registry): {'exclude': 1931, 'include': 6504}; systems in registry: 6504

Include rate by pilot stratum (pass 1):

| stratum | n | not retrievable | include / all | include / with full text |
|---|---|---|---|---|
| known_system | 15 | 0 | 15/15 = 100.0% [95% CI 79.6%, 100.0%] | 15/15 = 100.0% [95% CI 79.6%, 100.0%] |
| metadata_mismatch | 60 | 32 | 13/60 = 21.7% [95% CI 13.1%, 33.6%] | 13/28 = 46.4% [95% CI 29.5%, 64.2%] |
| random | 250 | 36 | 172/250 = 68.8% [95% CI 62.8%, 74.2%] | 172/214 = 80.4% [95% CI 74.5%, 85.1%] |

Include rate by source (pass 1):

| source | n | not retrievable | include rate (all) |
|---|---|---|---|
| arxiv | 2062 | 0 | 1459/2062 = 70.8% [95% CI 68.8%, 72.7%] |
| s2_snowball | 944 | 10 | 713/944 = 75.5% [95% CI 72.7%, 78.2%] |
| openalex | 393 | 19 | 202/393 = 51.4% [95% CI 46.5%, 56.3%] |
| s2 | 277 | 46 | 132/277 = 47.7% [95% CI 41.8%, 53.5%] |
| github | 223 | 0 | 173/223 = 77.6% [95% CI 71.7%, 82.6%] |
| leaderboard | 101 | 1 | 45/101 = 44.6% [95% CI 35.2%, 54.3%] |
| openreview | 84 | 0 | 64/84 = 76.2% [95% CI 66.1%, 84.0%] |
| acl | 81 | 0 | 52/81 = 64.2% [95% CI 53.3%, 73.8%] |
| awesome | 69 | 0 | 55/69 = 79.7% [95% CI 68.8%, 87.5%] |
| grey | 21 | 0 | 21/21 = 100.0% [95% CI 84.5%, 100.0%] |
| survey_refs | 17 | 0 | 5/17 = 29.4% [95% CI 13.3%, 53.1%] |

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
| duplicate_system | survey | 20 | 1.5% |
| no_harness_description | other | 17 | 1.3% |
| other | language | 8 | 0.6% |
| no_harness_description | - | 2 | 0.1% |
| out_of_scope | other | 1 | 0.1% |
| duplicate_system | other | 1 | 0.1% |
| out_of_scope | date | 1 | 0.1% |
| no_harness_description | codability | 1 | 0.1% |

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
| 10 | 84 |
| 11 | 113 |
| 12 | 2921 |

Confidence: exclude/high: 111, exclude/low: 118, exclude/medium: 1046, include/high: 354, include/low: 493, include/medium: 2074

## 3. Codability (criterion b; count of the 38 dimensions the evidence bundle supports)

Amendment 5: the count is recorded at screening and enforced at coding; step 7 only excludes a record with no admissible artifact at all (`no_harness_description` / `no_artifact`).

| codable_count | all LLM-read records | records reaching step 7 | pass-1 includes |
|---|---|---|---|
| 0-4 | 451 | 103 | 21 |
| 5-9 | 975 | 444 | 366 |
| 10-14 | 1313 | 1166 | 1109 |
| 15-18 | 783 | 762 | 753 |
| 19-22 | 411 | 410 | 409 |
| 23-26 | 180 | 180 | 180 |
| 27-30 | 69 | 69 | 69 |
| 31-38 | 14 | 14 | 14 |

Includes: median codable_count 14, min 3, max 33; exact distribution {3: 6, 4: 15, 5: 42, 6: 42, 7: 76, 8: 81, 9: 125, 10: 131, 11: 204, 12: 237, 13: 267, 14: 270, 15: 232, 16: 208, 17: 167, 18: 146, 19: 143, 20: 91, 21: 88, 22: 87, 23: 48, 24: 56, 25: 42, 26: 34, 27: 30, 28: 17, 29: 17, 30: 5, 31: 7, 32: 5, 33: 2}.
Records reaching step 7: 3148; excluded there for a missing artifact: 99.
codability_flag (all LLM-read records): borderline 1648, fail 1887, pass 661; among pass-1 includes: borderline 1539, fail 722, pass 660.
Repository evidence in the bundle (Amendment 5): 837/4196 = 19.9% [95% CI 18.8%, 21.2%]; median codable_count 18 with a repository vs 11 without; include rate 637/837 = 76.1% [95% CI 73.1%, 78.9%] vs 2284/3359 = 68.0% [95% CI 66.4%, 69.6%].
Layer coverage among includes: A 2623/2921, B 2317/2921, C 2869/2921, D 2185/2921, E 2031/2921, F 1927/2921, G 889/2921, H 1074/2921.

## 4. Evidence quality and systematic checks

- Quotes found verbatim in the excerpt the model saw (case/punctuation-insensitive): 30171/31388 = 96.1% [95% CI 95.9%, 96.3%]
- Post-hoc flags (pass 1): {'include_below_codability_rule': 2261, 'quote_not_in_excerpt': 943, 'no_evidence_for_deciding_step': 845, 'corrective_retry': 48, 'codability_flag_mismatch': 25, 'include_without_system_name': 17, 'layers_normalized': 17, 'long_quote': 14}
- Excerpt words: median 3986.0, max 4151; full-text words: median 5108.5, sent whole (<= cap): 1176
- Document title seen differs from the candidate title (fuzzy < 80): 112 records (s2:34df9357b07509c5513420259f9c360925a63b75: 'WATOS: Efficient LLM Training Strategies and Architecture Co'; s2:9d8ffad7a696416268c42c0b742c442ebcc03258: 'Generative AI for Networking'; s2:1d9fe0a048804d8714c8b957245fd7e1122ca03e: 'A Prompt-driven Task Planning Method for Multi-drones based '; s2:02c577223d9c0380648ebb988ad55db3b9832eb4: 'PROV-AGENT: Unified Provenance for Tracking AI Agent Interac'; s2:bd54e9ddada52dab5bde02cda4b63c25c6cf8357: 'Towards Verified Code Reasoning by LLMs'; s2_snowball:90597a0d023b66996f6ba0f9f6b1ba4ed264cd60: 'ContraFix: Skill-Enhanced Contrastive Runtime Analysis for V'; leaderboard:swe-bench:swe-agent-multimodal: 'SWE-agent/SWE-agent'; openalex:W4304195432: 'ReAct: Synergizing Reasoning and Acting in Language Models'; survey_refs:preprints:202604.0428:59: 'Manus: Hands On AI'; s2:af598689eb28fe0de48f14a6f1b302ff86ac5fe9: 'Use of cumulants to quantify uncertainties in the HBT measur'; leaderboard:osworld:aworldguiagent-v1: 'inclusionAI/AWorld (AWorld GUI Agent for OSWorld Benchmark)'; leaderboard:osworld:gbox-agent: 'babelcloud/GBOXBlog' ...)

Full-text source used: {'arxiv_pdf': 3101, 'doi_landing_html': 356, 'github_repo': 334, 'openalex_oa_pdf': 140, 'web_html': 87, 'acl_pdf': 83, 'openreview_pdf': 75, 'landing_html': 18, 's2_oa_pdf': 1, 'doi_landing_pdf': 1}

## 5. Independent second reading (pass 1 vs pass 2)

No pass-2 rows in scope yet.

## 6. Reference sets

Positive set: 27 known harness systems.

Recall by stage:

- search: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- title_forward: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- fulltext_include: 23/27 = 85.2% [95% CI 67.5%, 94.1%]
- registry: 27/27 = 100.0% [95% CI 87.5%, 100.0%]
- coding_frame: 27/27 = 100.0% [95% CI 87.5%, 100.0%]

| system | candidate records | forwarded | pass-1 include records | in registry | in coding frame | mentioned in n records | lost at |
|---|---|---|---|---|---|---|---|
| ReAct | 9 | 7 | 3 | yes | yes: catalogue;peer_reviewed | 1203 | - |
| Reflexion | 4 | 4 | 1 | yes | yes: catalogue | 564 | - |
| CodeAct | 2 | 2 | 2 | yes | yes: stars;catalogue | 55 | - |
| SWE-agent | 10 | 10 | 6 | yes | yes: catalogue;stars;catalogue;stars;catalogue;peer_reviewed | 210 | - |
| OpenHands | 6 | 6 | 4 | yes | yes: stars;catalogue;stars;catalogue;vendor | 167 | - |
| AutoGen | 4 | 4 | 4 | yes | yes: catalogue;stars;catalogue;vendor;peer_reviewed | 349 | - |
| MetaGPT | 1 | 1 | 3 | yes | yes: stars;catalogue;peer_reviewed | 281 | - |
| Agent S | 27 | 18 | 7 | yes | yes: catalogue;catalogue;peer_reviewed;stars;catalogue;stars;catalogue;peer_reviewed | 29 | - |
| OS-Copilot | 2 | 2 | 1 | yes | yes: stars;catalogue | 9 | - |
| WebArena reference agent | 2 | 2 | 1 | yes | yes: catalogue | 4 | - |
| OSWorld reference agent | 3 | 3 | 3 | yes | yes: stars;catalogue;stars;catalogue;peer_reviewed | 2 | - |
| tau-bench reference agent | 5 | 4 | 5 | yes | yes: catalogue;catalogue;peer_reviewed;catalogue;vendor;catalogue;vendor;peer_reviewed;stars;stars;catalogue;stars;catalogue;peer_reviewed;stars;catalogue;vendor | 1 | - |
| BrowserGym generic agent | 4 | 4 | 3 | yes | yes: stars;catalogue;stars;catalogue;vendor | 3 | - |
| mini-SWE-agent | 2 | 2 | 1 | yes | yes: catalogue | 59 | - |
| Aider | 4 | 3 | 0 | yes | yes: catalogue;vendor | 55 | fulltext_include (not screened yet) |
| Cline | 2 | 2 | 1 | yes | yes: catalogue;vendor | 13 | - |
| Codex CLI | 3 | 2 | 0 | yes | yes: stars;catalogue;vendor | 66 | fulltext_include (not screened yet) |
| Gemini CLI | 2 | 2 | 1 | yes | yes: catalogue;vendor | 41 | - |
| OpenCode | 4 | 3 | 1 | yes | yes: stars;catalogue;vendor | 77 | - |
| Moatless Tools | 1 | 1 | 1 | yes | yes: catalogue | 15 | - |
| Prometheus | 2 | 2 | 0 | yes | yes: stars;catalogue | 0 | fulltext_include (not screened yet) |
| Claude Code | 5 | 3 | 2 | yes | yes: stars;catalogue;vendor | 338 | - |
| Mistral Vibe | 2 | 2 | 1 | yes | yes: stars;catalogue;vendor | 1 | - |
| Hermes Agent | 1 | 1 | 0 | yes | yes: stars;catalogue | 24 | fulltext_include (not screened yet) |
| Pi | 2 | 2 | 1 | yes | yes: stars;catalogue;vendor | 22 | - |
| OpenClaw | 4 | 3 | 4 | yes | yes: catalogue;vendor | 116 | - |
| AIOS | 3 | 1 | 1 | yes | yes: stars;catalogue | 6 | - |

Missing positive reference systems (stage where lost; the full-text decision of matched records):

| system | lost at | matched records | full-text decision(s) | catalogued by |
|---|---|---|---|---|
| Aider | fulltext_include (not screened yet) | awesome:picrew:da950c021dac, grey:aider, leaderboard:swe-bench:aider | - | Rombaut (positioning.md: 13 edit formats); Barbaste 11 |
| Codex CLI | fulltext_include (not screened yet) | awesome:picrew:a53af4b5fcbb, github:codingmoh/open-codex, grey:codex-cli | - | Rombaut (positioning.md: Op::Undo; Bubblewrap/Landlock); Barbaste 11 |
| Prometheus | fulltext_include (not screened yet) | arxiv:2507.19942, github:EuniAI/Prometheus | - | Rombaut (docs/definition.md 3.4 cites Rombaut 4.1.3) |
| Hermes Agent | fulltext_include (not screened yet) | github:NousResearch/hermes-agent | - | Barbaste 11 ('Hermes') |

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

- pass 1: 4199 LLM records; busy wall time 15.6 min (union of batch intervals; effective concurrency 9.9); 0.2 s/record wall, 2.2 s/record serial; list-equivalent $404.87 = $0.096/record; tokens/record in 14414, out 842

Projection to the whole queue (9967 records), from all pass-1 records and the measured rates:

- not retrievable: 1.8% of records -> about 177 without an LLM reading, 9790 read
- includes (pass 1): 2921/4272 = 68.4% [95% CI 67.0%, 69.8%] -> about 6815 records [6674, 6952]
- pass 1: 0.6 h wall at the measured concurrency (9.9), $944 list-equivalent
- pass 2 (7112 records): 0.4 h wall, $686 list-equivalent
- total: 1.0 h, $1,630 list-equivalent (consumed as Claude Code subscription usage, not billed)

**Warning: the projected include count (~6815 records, 95% CI 6674-6952) is far above the 150-300 systems the protocol expected.** Deduplication into systems will lower it (pilot: 6504 systems from 6504 final includes), but not by that factor if most includes are one-paper systems. The codable_count distribution of includes is in section 3; tightening criterion (b) is the author's decision.

## 8. System registry

6504 systems from 7085 included records; 407 with more than one record.

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
| a-evolve | A-Evolve | 1 | github:A-EVO-Lab/a-evolve | 21 | https://github.com/a-evo-lab/a-evolve |
| a-mapreduce | A-MapReduce | 1 | arxiv:2602.01331 | 23 | https://github.com/mingju-c/amapreduce |
| a-mar | A-MAR | 2 | s2_snowball:696782b3cea9d571ee1f71e009ea06b926864b3d | 18 | https://github.com/shuaiwang97/a-mar |
| a-pros | A-ProS | 1 | arxiv:2605.18073 | 19 |  |
| a-rag | A-RAG | 1 | s2_snowball:54fc75b6dbc48dcda85c73a7a2e4c9d7ef037399 | 23 | https://github.com/ayanami0730/arag |
| a-sr | A-SR | 1 | arxiv:2608.04872 | 11 |  |
| a-tom-agent | A-ToM agent | 1 | arxiv:2603.16264 | 12 | https://github.com/chunjiangmonkey/adaptive-tom |
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
| acid-agent | ACID-Agent | 1 | arxiv:2608.13900 | 26 | https://github.com/tsinghuadatabasegroup/acid-agent |
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
| ad-agent | AD-AGENT | 2 | arxiv:2505.12594 | 20 | https://github.com/usc-fortis/ad-agent |
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
| adaplan | AdaPlan (PilotRL) | 1 | arxiv:2508.00344 | 7 |  |
| adaplan-h | AdaPlan-H | 1 | arxiv:2604.23194 | 15 | https://github.com/import-myself/ahp |
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
| adn-agent | ADN-Agent | 1 | arxiv:2511.12484 | 17 |  |
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
| agent-a-b | Agent A/B | 1 | arxiv:2504.09723 | 18 |  |
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
| agent-e | Agent-E | 2 | arxiv:2407.13032 | 27 | https://github.com/emergenceai/agent-e |
| agent-enhanced-heterogeneous-graph-rag | Agent-Enhanced Heterogeneous Graph RAG | 1 | s2_snowball:95aecbb57bdccfeac6f6386815cf3b7c3db21171 | 15 |  |
| agent-event-coder | Agent-Event-Coder (AEC) | 1 | arxiv:2511.13118 | 14 | https://github.com/uestc-gqj/agent-event-coder |
| agent-expver | Agent-ExpVer | 1 | s2_snowball:20699a99cd939f3faeabd9f16dd2c3536ef89001 | 15 |  |
| agent-factory | Agent Factory (HLS) | 2 | arxiv:2603.25719 | 25 | https://github.com/zzatpku/agentfactory |
| agent-for-user | Agent for User (multi-agent TikTok testing) | 1 | arxiv:2504.15474 | 11 |  |
| agent-g | AGENT-G | 1 | openreview:g2C947jjjQ | 11 |  |
| agent-guided-pruning | agent-guided pruning | 1 | arxiv:2601.09694 | 15 |  |
| agent-gym | Agent Gym | 1 | arxiv:2608.15591 | 16 | https://github.com/google/adk-samples/python/agents/invoice-processing |
| agent-hospital | Agent Hospital | 1 | s2_snowball:0d69f44a47babaa522dee90baf632d9a8419bca3 | 9 |  |
| agent-hunt | Agent Hunt | 1 | arxiv:2603.06737 | 15 | https://github.com/mgwiki/alg_top |
| agent-jit | Agent JIT (JIT-Planner/JIT-Scheduler) | 1 | arxiv:2605.21470 | 17 |  |
| agent-k | Agent K | 1 | arxiv:2411.03562 | 11 |  |
| agent-laboratory | Agent Laboratory | 1 | arxiv:2501.04227 | 25 |  |
| agent-libos | Agent libOS | 1 | arxiv:2606.03895 | 29 | https://github.com/yingqi-z20/agent-libos |
| agent-lite-medical-assistant | Agent Lite Medical Assistant | 1 | s2_snowball:6c54d04a1cb780f97bbf2de36ec88d036bc5dcc5 | 12 |  |
| agent-memory-distillation | Agent Memory Distillation (AMD) | 1 | arxiv:2608.07169 | 13 |  |
| agent-native | Agent-Native | 1 | github:BuilderIO/agent-native | 9 | https://github.com/builderio/agent-native |
| agent-nexus | Agent-Nexus | 1 | s2_snowball:1c088c3acd9878fc53667cb10b289437964fb6ad | 12 |  |
| agent-om | Agent-OM | 1 | arxiv:2312.00326 | 24 | https://github.com/qzc438/ontology-llm |
| agent-on-graph | Agent-on-Graph (AoG) | 1 | openalex:W7168032230 | 7 | https://github.com/xuduyinuo/aog |
| agent-ops | Agent-Ops | 1 | acl:singh-etal-2026-agent | 7 |  |
| agent-orchestrated-adaptive-rag | Agent-Orchestrated Adaptive RAG | 1 | arxiv:2606.05658 | 14 |  |
| agent-orchestrator | Agent Orchestrator | 1 | awesome:picrew:081771e5aa9d | 15 | https://github.com/untrivial-ai/agent-orchestrator |
| agent-pro | Agent-Pro | 1 | s2_snowball:789485978d69e248832df358ee0fb062012925b8 | 19 | https://github.com/zwq2018/agent-pro |
| agent-q | Agent Q | 1 | arxiv:2408.07199 | 14 |  |
| agent-q-mix | Agent Q-Mix | 1 | arxiv:2604.00344 | 19 | https://github.com/ericjiang18/agent-q-mix |
| agent-qa | agent-qa | 1 | github:vostride/agent-qa | 13 | https://github.com/vostride/agent-qa |
| agent-rosetta | Agent Rosetta | 1 | arxiv:2603.15952 | 18 |  |
| agent-s | Agent S3 | 7 | awesome:picrew:299eea9d8182 | 24 | https://github.com/simular-ai/agent-s |
| agent-s-v2 | Agent S2 | 1 | s2_snowball:ff996cf4b98fa59d39966bbfbc756f2f22ba9c1d | 20 | https://github.com/simular-ai/agent-s |
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
| agent2world | Agent2World | 1 | arxiv:2512.22336 | 9 |  |
| agent2world-multi | Agent2World Multi | 1 | openreview:LdQmNo5iVX | 14 |  |
| agent4ct | Agent4CT | 1 | arxiv:2607.22824 | 20 | https://github.com/akmaier/agent4ct |
| agent4debate | Agent4Debate | 1 | arxiv:2408.04472 | 13 | https://github.com/zhangyiqun018/agent-for-debate |
| agent4decompile | Agent4Decompile | 1 | arxiv:2604.23940 | 19 |  |
| agent4dl | Agent4DL | 1 | s2_snowball:e285c0c0afa39198c79b806fc28ef6a698b37a54 | 10 | https://github.com/padas-lab-de/icadl24-agent4dl |
| agentada | AgentAda | 1 | s2_snowball:70886a79f8c61d1a11d5640f812c730197bdf7f0 | 19 | https://github.com/servicenow/agentada |
| agentao | Agentao | 1 | arxiv:2608.13574 | 29 | https://github.com/jin-bo/agentao |
| agentbench-reference-agent | AgentBench reference agent | 1 | arxiv:2308.03688 | 26 | https://github.com/thudm/agentbench |
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
| agentdebug | AgentDebug | 1 | arxiv:2509.25370 | 14 | https://github.com/ulab-uiuc/agentdebug |
| agentdebugx | AgentDebugX (DeepDebug) | 1 | arxiv:2607.18754 | 19 | https://github.com/agentdebugx/agentdebugx |
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
| agentfl | AgentFL | 1 | arxiv:2403.16362 | 17 |  |
| agentflow | AgentFlow | 3 | arxiv:2510.05592 | 17 |  |
| agentflux | AgentFlux | 1 | arxiv:2510.00229 | 13 |  |
| agentfly | AgentFly | 1 | s2_snowball:342ac8f2206b052e538af2b92aa50843346fa257 | 20 | https://github.com/agent-one-lab/agentfly |
| agentfold | AgentFold | 1 | arxiv:2608.26747 | 21 | https://github.com/lmqfly/agentfold |
| agentforge | AgentForge | 1 | arxiv:2601.13383 | 21 | https://github.com/001shahab/agentforge |
| agentforge-2 | AgentForge | 1 | arxiv:2604.13120 | 21 | https://github.com/raja21068/autocodeai |
| agentfox | AgentFoX | 1 | s2_snowball:0733167a4e3fac92bc16aeb61cf8df1d7ecf2d0e | 22 | https://github.com/suncore946/agentfox |
| agentfugue | AgentFugue (Cabeza) | 1 | s2_snowball:5413c1700410467f3a7a9f921c2ecf44aa8201fa | 20 | https://github.com/qhjqhj00/cabeza |
| agentgc | AgentGC | 1 | arxiv:2601.13559 | 13 |  |
| agentgl | AgentGL | 1 | arxiv:2604.05846 | 22 | https://github.com/sunyuanfu/agentgl |
| agentgroupchat-v2 | AgentGroupChat-V2 | 1 | arxiv:2506.15451 | 18 | https://github.com/mikegu721/agentgroupchat-v2 |
| agentguard | AgentGuard | 1 | arxiv:2502.09809 | 14 |  |
| agentguardutil | AgentGuardUtil | 1 | arxiv:2608.23282 | 17 |  |
| agentgym | AgentGym | 1 | s2_snowball:3072ad4982cd916606ac88ea1883d4d725c4eda4 | 19 | https://github.com/woooodyy/agentgym |
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
| agenticrag | AgenticRAG | 1 | arxiv:2605.05538 | 18 |  |
| agenticrag-r | AGENTICRAG-R1 | 1 | arxiv:2608.29622 | 15 | https://github.com/jiangxinke/harness-rl |
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
| agentk | AgentK | 1 | s2_snowball:9cdeb9ce381ec21c03ff7a94676580ad841316a8 | 12 |  |
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
| agentopia | Agentopia | 1 | arxiv:2606.07513 | 23 | https://github.com/neph0s/agentopia |
| agentopia-2 | Agentopia (consumer GPU port) | 1 | s2:20023a0b8093b153359be30330d02154dd9516db | 18 | https://github.com/luo675/agentopia |
| agentoptics | AgentOptics | 1 | s2_snowball:63e43566276e5f8e2fbfb5b6b410cb2e69344ef1 | 11 |  |

