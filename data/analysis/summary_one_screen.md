| level | layer | dimension | cells | coded | not_reported | unresolved | NR weighted | modal value (weighted share) | n coded | n weight-bearing |
|---|---|---|---|---|---|---|---|---|---|---|
| layer | **A Context assembly** | **(4 dimensions)** | 5024 | 55.4% | 44.2% | 0.38% | 40.2% +/- 2.0% |  | 1088 | 1068 |
| dimension | A | A1 system_prompt_style | 1256 | 62.5% | 37.0% | 0.48% | 30.9% +/- 3.4% | templated (49%) | 785 | 772 |
| dimension | A | A2 env_context_strategy | 1256 | 66.1% | 33.4% | 0.48% | 27.5% +/- 3.3% | agent_driven_navigation (31%) | 830 | 814 |
| dimension | A | A3 context_compaction | 1256 | 30.7% | 69.0% | 0.32% | 77.9% +/- 3.0% | summarize (49%) | 385 | 379 |
| dimension | A | A4 observation_format | 1256 | 62.5% | 37.3% | 0.24% | 24.3% +/- 3.1% | raw_text (89%) | 785 | 769 |
| layer | **B Tool interface** | **(5 dimensions)** | 6280 | 36.3% | 62.9% | 0.73% | 71.4% +/- 2.0% |  | 965 | 950 |
| dimension | B | B1 tool_call_format | 1256 | 48.5% | 51.0% | 0.56% | 52.6% +/- 3.7% | json_in_text (36%) | 609 | 598 |
| dimension | B | B2 tool_count | 1256 | 21.0% | 79.0% | 0.00% | 77.5% +/- 3.1% | 2-5 (37%) | 264 | 259 |
| dimension | B | B3 edit_primitive | 1256 | 33.0% | 64.1% | 2.95% | 70.8% +/- 3.3% | none (47%) | 414 | 406 |
| dimension | B | B4 tool_schema_source | 1256 | 40.4% | 59.4% | 0.16% | 72.1% +/- 3.2% | hand_written (70%) | 508 | 501 |
| dimension | B | B5 protocol_standardization | 1256 | 38.8% | 61.2% | 0.00% | 84.0% +/- 2.2% | mcp (68%) | 487 | 480 |
| layer | **C Control loop** | **(5 dimensions)** | 6280 | 72.6% | 26.9% | 0.48% | 24.9% +/- 1.2% |  | 1212 | 1190 |
| dimension | C | C1 loop_primitives | 1256 | 92.0% | 7.6% | 0.32% | 1.4% +/- 0.0% | react (50%) | 1156 | 1136 |
| dimension | C | C2 planning_granularity | 1256 | 75.4% | 24.0% | 0.64% | 13.7% +/- 2.4% | implicit (48%) | 947 | 929 |
| dimension | C | C3 multi_agent_topology | 1256 | 90.9% | 8.8% | 0.32% | 1.8% +/- 0.1% | single (41%) | 1142 | 1121 |
| dimension | C | C4 delegation_mechanism | 1256 | 67.8% | 31.7% | 0.48% | 31.4% +/- 3.5% | role_handoff (50%) | 852 | 840 |
| dimension | C | C5 human_in_loop | 1256 | 36.7% | 62.7% | 0.64% | 76.7% +/- 2.9% | on_permission (39%) | 461 | 454 |
| layer | **D Memory and state** | **(3 dimensions)** | 3768 | 47.1% | 52.5% | 0.45% | 63.3% +/- 2.1% |  | 1005 | 991 |
| dimension | D | D1 short_term_state | 1256 | 64.8% | 34.4% | 0.80% | 34.1% +/- 3.6% | structured_task_state (65%) | 814 | 802 |
| dimension | D | D2 long_term_memory | 1256 | 45.4% | 54.2% | 0.40% | 69.0% +/- 3.3% | skill_library (45%) | 570 | 563 |
| dimension | D | D3 state_persistence | 1256 | 31.1% | 68.8% | 0.16% | 86.2% +/- 2.1% | full_resume (56%) | 390 | 384 |
| layer | **E Verification and repair** | **(3 dimensions)** | 3768 | 35.0% | 64.9% | 0.19% | 60.9% +/- 2.3% |  | 750 | 735 |
| dimension | E | E1 self_verification | 1256 | 51.3% | 48.4% | 0.32% | 39.4% +/- 3.6% | test_execution (42%) | 644 | 630 |
| dimension | E | E2 retry_policy | 1256 | 34.7% | 65.2% | 0.08% | 56.8% +/- 3.7% | fixed_n (46%) | 436 | 429 |
| dimension | E | E3 rollback | 1256 | 18.9% | 81.0% | 0.16% | 86.4% +/- 2.4% | snapshot (58%) | 237 | 234 |
| layer | **F Budget and termination** | **(3 dimensions)** | 3768 | 38.4% | 61.4% | 0.27% | 65.1% +/- 2.0% |  | 902 | 886 |
| dimension | F | F1 termination_condition | 1256 | 60.4% | 39.2% | 0.40% | 32.7% +/- 3.5% | max_steps (77%) | 759 | 743 |
| dimension | F | F2 cost_controls | 1256 | 30.3% | 69.4% | 0.24% | 80.2% +/- 2.8% | token_budget (65%) | 381 | 373 |
| dimension | F | F3 timeouts | 1256 | 24.4% | 75.5% | 0.16% | 82.4% +/- 2.7% | per_tool (74%) | 306 | 298 |
| layer | **G Sandbox and environment** | **(4 dimensions)** | 5024 | 33.3% | 66.4% | 0.28% | 81.6% +/- 1.8% |  | 775 | 763 |
| dimension | G | G1 execution_isolation | 1256 | 58.4% | 41.5% | 0.16% | 64.3% +/- 3.4% | subprocess (33%) | 733 | 722 |
| dimension | G | G2 filesystem_access | 1256 | 29.0% | 70.9% | 0.16% | 87.5% +/- 2.0% | full (49%) | 364 | 360 |
| dimension | G | G3 network_policy | 1256 | 15.2% | 84.6% | 0.24% | 93.3% +/- 1.5% | open (77%) | 191 | 187 |
| dimension | G | G4 permission_model | 1256 | 30.7% | 68.8% | 0.56% | 81.4% +/- 2.7% | none (32%) | 385 | 381 |
| layer | **H Observability and governance** | **(4 dimensions)** | 5024 | 40.2% | 59.6% | 0.20% | 72.8% +/- 2.0% |  | 975 | 959 |
| dimension | H | H1 tracing | 1256 | 60.8% | 38.9% | 0.32% | 58.7% +/- 3.5% | structured_traces (52%) | 764 | 755 |
| dimension | H | H2 replayability | 1256 | 14.9% | 85.1% | 0.00% | 90.6% +/- 2.0% | partial (82%) | 187 | 185 |
| dimension | H | H3 eval_hooks | 1256 | 49.6% | 50.3% | 0.08% | 67.3% +/- 3.2% | built_in (95%) | 623 | 611 |
| dimension | H | H4 guardrails | 1256 | 35.4% | 64.2% | 0.40% | 74.7% +/- 3.1% | action_policies (79%) | 445 | 439 |
| layer | **M Meta** | **(7 dimensions)** | 8792 | 72.5% | 27.4% | 0.11% | 34.6% +/- 1.3% |  | 1256 | 1233 |
| dimension | M | M1 target_domain | 1256 | 99.9% | 0.0% | 0.08% | 0.0% +/- 0.0% | other (52%) | 1255 | 1232 |
| dimension | M | M2 open_source | 1256 | 61.8% | 38.1% | 0.16% | 69.7% +/- 3.0% | yes (79%) | 776 | 767 |
| dimension | M | M3 model_agnostic | 1256 | 88.1% | 11.6% | 0.32% | 22.8% +/- 3.3% | yes (84%) | 1106 | 1084 |
| dimension | M | M4 primary_artifact | 1256 | 99.7% | 0.2% | 0.08% | 0.0% +/- 0.0% | paper (66%) | 1252 | 1229 |
| dimension | M | M5 first_release_date | 1256 | 32.8% | 67.0% | 0.16% | 50.2% +/- 3.7% | 2026 (52%) | 412 | 406 |
| dimension | M | M6 pinned_version | 1256 | 83.1% | 16.9% | 0.00% | 33.5% +/- 3.6% | (free text: not tabulated) (100%) | 1044 | 1025 |
| dimension | M | M7 stars | 1256 | 42.1% | 57.9% | 0.00% | 66.2% +/- 3.3% | 13-134 (37%) | 529 | 513 |
