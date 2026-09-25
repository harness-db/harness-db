| level | layer | dimension | cells | coded | not_reported | unresolved | NR weighted | modal value (weighted share) | n coded | n weight-bearing |
|---|---|---|---|---|---|---|---|---|---|---|
| layer | **A Context assembly** | **(4 dimensions)** | 5012 | 55.4% | 44.2% | 0.40% | 40.2% +/- 1.8% |  | 1086 | 1066 |
| dimension | A | A1 system_prompt_style | 1253 | 62.5% | 37.0% | 0.48% | 30.9% +/- 3.4% | templated (49%) | 783 | 770 |
| dimension | A | A2 env_context_strategy | 1253 | 66.2% | 33.4% | 0.48% | 27.5% +/- 3.3% | agent_driven_navigation (31%) | 829 | 813 |
| dimension | A | A3 context_compaction | 1253 | 30.6% | 69.0% | 0.40% | 77.9% +/- 3.0% | summarize (49%) | 384 | 378 |
| dimension | A | A4 observation_format | 1253 | 62.5% | 37.3% | 0.24% | 24.3% +/- 3.1% | raw_text (89%) | 783 | 767 |
| layer | **B Tool interface** | **(5 dimensions)** | 6265 | 36.3% | 62.9% | 0.73% | 71.4% +/- 1.4% |  | 963 | 948 |
| dimension | B | B1 tool_call_format | 1253 | 48.4% | 51.0% | 0.56% | 52.6% +/- 3.7% | json_in_text (36%) | 607 | 596 |
| dimension | B | B2 tool_count | 1253 | 21.1% | 78.9% | 0.00% | 77.5% +/- 3.1% | 2-5 (37%) | 264 | 259 |
| dimension | B | B3 edit_primitive | 1253 | 33.0% | 64.1% | 2.95% | 70.8% +/- 3.3% | none (47%) | 413 | 405 |
| dimension | B | B4 tool_schema_source | 1253 | 40.4% | 59.5% | 0.16% | 72.1% +/- 3.2% | hand_written (70%) | 506 | 499 |
| dimension | B | B5 protocol_standardization | 1253 | 38.9% | 61.1% | 0.00% | 84.0% +/- 2.2% | mcp (68%) | 487 | 480 |
| layer | **C Control loop** | **(5 dimensions)** | 6265 | 72.5% | 27.0% | 0.48% | 24.9% +/- 1.4% |  | 1209 | 1187 |
| dimension | C | C1 loop_primitives | 1253 | 92.0% | 7.7% | 0.32% | 1.4% +/- 0.0% | react (50%) | 1153 | 1133 |
| dimension | C | C2 planning_granularity | 1253 | 75.3% | 24.0% | 0.64% | 13.7% +/- 2.4% | implicit (48%) | 944 | 926 |
| dimension | C | C3 multi_agent_topology | 1253 | 90.8% | 8.9% | 0.32% | 1.8% +/- 0.1% | single (41%) | 1138 | 1117 |
| dimension | C | C4 delegation_mechanism | 1253 | 67.8% | 31.8% | 0.48% | 31.4% +/- 3.5% | role_handoff (50%) | 849 | 837 |
| dimension | C | C5 human_in_loop | 1253 | 36.8% | 62.6% | 0.64% | 76.7% +/- 2.9% | on_permission (39%) | 461 | 454 |
| layer | **D Memory and state** | **(3 dimensions)** | 3759 | 47.1% | 52.4% | 0.45% | 63.3% +/- 2.0% |  | 1003 | 989 |
| dimension | D | D1 short_term_state | 1253 | 64.8% | 34.4% | 0.80% | 34.1% +/- 3.6% | structured_task_state (65%) | 812 | 800 |
| dimension | D | D2 long_term_memory | 1253 | 45.5% | 54.1% | 0.40% | 69.0% +/- 3.3% | skill_library (45%) | 570 | 563 |
| dimension | D | D3 state_persistence | 1253 | 31.1% | 68.7% | 0.16% | 86.2% +/- 2.1% | full_resume (56%) | 390 | 384 |
| layer | **E Verification and repair** | **(3 dimensions)** | 3759 | 34.8% | 65.0% | 0.19% | 61.0% +/- 2.0% |  | 746 | 731 |
| dimension | E | E1 self_verification | 1253 | 51.1% | 48.6% | 0.32% | 39.5% +/- 3.6% | test_execution (42%) | 640 | 626 |
| dimension | E | E2 retry_policy | 1253 | 34.6% | 65.4% | 0.08% | 56.8% +/- 3.7% | fixed_n (46%) | 433 | 426 |
| dimension | E | E3 rollback | 1253 | 18.9% | 80.9% | 0.16% | 86.4% +/- 2.4% | snapshot (58%) | 237 | 234 |
| layer | **F Budget and termination** | **(3 dimensions)** | 3759 | 38.4% | 61.3% | 0.27% | 65.1% +/- 2.0% |  | 900 | 884 |
| dimension | F | F1 termination_condition | 1253 | 60.4% | 39.2% | 0.40% | 32.7% +/- 3.5% | max_steps (77%) | 757 | 741 |
| dimension | F | F2 cost_controls | 1253 | 30.4% | 69.4% | 0.24% | 80.2% +/- 2.8% | token_budget (65%) | 381 | 373 |
| dimension | F | F3 timeouts | 1253 | 24.3% | 75.5% | 0.16% | 82.4% +/- 2.7% | per_tool (74%) | 305 | 297 |
| layer | **G Sandbox and environment** | **(4 dimensions)** | 5012 | 33.3% | 66.5% | 0.28% | 81.7% +/- 1.2% |  | 773 | 761 |
| dimension | G | G1 execution_isolation | 1253 | 58.3% | 41.5% | 0.16% | 64.3% +/- 3.4% | subprocess (33%) | 731 | 720 |
| dimension | G | G2 filesystem_access | 1253 | 28.9% | 70.9% | 0.16% | 87.5% +/- 2.0% | full (49%) | 362 | 358 |
| dimension | G | G3 network_policy | 1253 | 15.2% | 84.6% | 0.24% | 93.3% +/- 1.5% | open (77%) | 190 | 186 |
| dimension | G | G4 permission_model | 1253 | 30.6% | 68.8% | 0.56% | 81.5% +/- 2.7% | none (32%) | 384 | 380 |
| layer | **H Observability and governance** | **(4 dimensions)** | 5012 | 40.2% | 59.6% | 0.20% | 72.8% +/- 1.5% |  | 972 | 956 |
| dimension | H | H1 tracing | 1253 | 60.7% | 38.9% | 0.32% | 58.7% +/- 3.5% | structured_traces (52%) | 761 | 752 |
| dimension | H | H2 replayability | 1253 | 14.9% | 85.1% | 0.00% | 90.6% +/- 2.0% | partial (82%) | 187 | 185 |
| dimension | H | H3 eval_hooks | 1253 | 49.5% | 50.4% | 0.08% | 67.3% +/- 3.2% | built_in (95%) | 620 | 608 |
| dimension | H | H4 guardrails | 1253 | 35.5% | 64.1% | 0.40% | 74.7% +/- 3.1% | action_policies (79%) | 445 | 439 |
| layer | **M Meta** | **(7 dimensions)** | 8771 | 72.4% | 27.4% | 0.11% | 34.7% +/- 1.3% |  | 1253 | 1230 |
| dimension | M | M1 target_domain | 1253 | 99.9% | 0.0% | 0.08% | 0.0% +/- 0.0% | other (52%) | 1252 | 1229 |
| dimension | M | M2 open_source | 1253 | 61.7% | 38.1% | 0.16% | 69.7% +/- 3.0% | yes (79%) | 773 | 764 |
| dimension | M | M3 model_agnostic | 1253 | 88.1% | 11.6% | 0.32% | 22.8% +/- 3.3% | yes (84%) | 1104 | 1082 |
| dimension | M | M4 primary_artifact | 1253 | 99.7% | 0.2% | 0.08% | 0.0% +/- 0.0% | paper (66%) | 1249 | 1226 |
| dimension | M | M5 first_release_date | 1253 | 32.6% | 67.3% | 0.16% | 50.2% +/- 3.7% | 2026 (52%) | 408 | 402 |
| dimension | M | M6 pinned_version | 1253 | 83.1% | 16.9% | 0.00% | 33.6% +/- 3.6% | (free text: not tabulated) (100%) | 1041 | 1022 |
| dimension | M | M7 stars | 1253 | 42.1% | 57.9% | 0.00% | 66.2% +/- 3.3% | 13-134 (38%) | 527 | 511 |
