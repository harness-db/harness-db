# Grey-source harvest notes (leaderboards + vendor documentation)

Run date: 2026-09-16 (UTC 20:13-20:19). Scripts: `scripts/harvest/leaderboards.py`,
`scripts/harvest/grey.py` (documented in `scripts/harvest/README_grey.md`). Nothing in this
file is inferred: every count is from the scripts' `SUMMARY` lines and every failure was
observed on this date.

## leaderboards.jsonl

`python scripts/harvest/leaderboards.py --out data/raw/leaderboards.jsonl`
417 HTTP requests + `gh api` calls; 4,893 entries -> **3,946 records** (one per distinct
system per leaderboard family). No source failed in the final run (the first attempt hit a
502/429 burst on HF datasets-server for GAIA; the GAIA client now paces at 2 s with long
backoff and the re-run succeeded).

| leaderboard (query_used) | data source actually used | entries | distinct systems (records) | notes |
|---|---|---|---|---|
| SWE-bench | `https://www.swebench.com/` embedded `<script id="leaderboard-data">` JSON; splits Verified 180, Lite 84, Test 24, Multimodal 22, Multilingual 13 | 323 | 119 | The GitHub repo `SWE-bench/experiments` holds 319 `evaluation/<split>/<dir>/metadata.yaml` (verified 175, lite 84, test 24, multimodal 22, multilingual 14; tree not truncated) and is the fallback path; the site JSON was preferred because it already carries `resolved`, `date`, `site`, `agent`, `model_display`. swebench.com exposes no separate JSON endpoint (`/api/leaderboards`, `/data/leaderboards.json` -> 404). |
| HAL | `https://hal.cs.princeton.edu/{gaia,swebench_verified_mini,taubench_airline,usaco,corebench_hard,scicode,scienceagentbench,assistantbench,online_mind2web}` server-rendered tables | 246 (gaia 32, swebench_verified_mini 33, taubench_airline 26, usaco 13, corebench_hard 49, scicode 33, scienceagentbench 23, assistantbench 15, online_mind2web 22) | 12 (HAL Generalist Agent, Browser-Use, CORE-Agent, HF Open Deep Research, SAB Self-Debug, Scicode Tool Calling Agent, Scicode Zero Shot Agent, SeeAct, SWE-Agent, TAU-bench Tool Calling, USACO Episodic + Semantic, Claude Code) | No machine-readable results file exists: `princeton-pli/hal-harness` has agents/benchmarks only; HF `agent-evals/hal_traces` holds encrypted trace zips; the page's only fetch is `/update_pricing/<benchmark>`. Accuracy, CI, cost (USD), verified flag, runs and trace URL captured per entry. **No submission dates on the site** (`date=None`). The `/reliability` page was not harvested (different metric set). |
| OSWorld | `https://os-world.github.io/static/data/osworld_verified_results.xlsx` (149 rows) + `.../self_reported_results.xlsx` (Screenshot 56, A11y_tree 15, Screenshot_A11y_tree 18, Set-of-Mark 11) | 249 | 46 | 159 entries are bare models/specialized models on the OSWorld scaffold (`Approach type` = Specialized/General model: computer-use-preview, o3, claude-*, UI-TARS, OpenCUA, Qwen2.5-VL, ...) and are grouped as `OSWorld reference agent` (protocol 4.1); each keeps its `raw_name`, approach type, max steps, per-domain scores. The site JS renders exactly these two xlsx files; there is no JSON. |
| WebArena | Google Sheet `1M801lEpBbKSNwP-vDBkC_pF7LdyGU1f_ufZb_NWNBZQ` (linked from `https://webarena.dev/og/`), xlsx export; sheets WebArena 47 rows, VisualWebArena 39 rows | 86 | 42 | webarena.dev itself is now a "WebArena-x" landing page with no leaderboard. 12 WebArena and 23 VisualWebArena rows are the benchmark papers' own baselines (Work/Result Source = the benchmark, or a bare model) -> `WebArena reference agent` / `VisualWebArena reference agent`. Dates are month precision. Hyperlinks (paper/repo, trajectories) are taken from the xlsx cells; the CSV export loses them. |
| Terminal-Bench | (a) `https://www.tbench.ai/leaderboard` Next.js flight payload: Terminal-Bench 4.0, 18 rows (agents: Claude Code, Codex, Grok Build, mini-SWE-agent); (b) `laude-institute/terminal-bench-leaderboard` `results/terminal-bench-core@0.1.1` (24 submissions) + `results/terminal-bench-core:0.1.1` (1): accuracy = mean over the run dirs' `results.json` | 43 | 18 | **Terminal-Bench 2.0 leaderboard not obtained** (Terminus 2, Droid, Warp, Forge, OpenHands, Codex CLI ... on TB 2.0). Tried: live site (serves only 4.0), Harbor Hub `hub.harborframework.com/datasets/terminal-bench/terminal-bench/2?tab=leaderboard` (client-rendered; every `/api/datasets/terminal-bench/terminal-bench/2/<section>` except `tasks` answers 404), Wayback captures of `tbench.ai/leaderboard` at 2025-12, 2026-01, 2026-02, 2026-04, 2026-06 (old site: react-query client shell, no rows; `.../2.0` captures redirect to the current board), `harbor-framework/terminal-bench` tags v3.0.0/v4.0.0 (only `leaderboard/runs/*.json` job configs, no scores), `laude-institute/terminal-bench-2-leaderboard` (empty repo), `harbor-framework/terminal-bench-1` (no leaderboard files). To be re-tried at search freeze or requested from the maintainers. |
| GAIA | HF datasets-server rows API for `gaia-benchmark/results_public` config `2023`: validation 94 rows, test 3,679 rows (the dataset behind the `gaia-benchmark/leaderboard` Space) | 3,773 | 3,695 | The test split is an open submission log: most names are one-off submissions (model or team names), so GAIA contributes 3,695 of the 3,946 records. Records carry `model_family` (LLM), organisation, level-1/2/3 scores, url when given. No pyarrow on this machine, so the parquet files were not read directly; the rows API returned the same 10 columns. |
| tau-bench | `sierra-research/tau-bench` README tables (Airline 7 rows, Retail 7 rows) | 14 | 3 (`tau-bench reference agent (tool-calling)`, `(Act)`, `(ReAct)`) | Cells marked `??` in the README -> `score=None` (6 of 14). No dates. |
| tau2-bench | `https://sierra-tau-bench-public.s3.us-west-2.amazonaws.com/submissions/manifest.json` + 66 `submission.json` (29 submissions, 16 legacy, 21 voice), the files taubench.com renders | 159 (one per submission x domain) | 11 (`tau2-bench reference agent` 96 entries, `tau2-bench reference agent (tau-voice)` 42, plus 9 `custom` submissions named `<model> (<org>)`: Distyl ButtonAgent, Nemotron-Orchestrator-8B, RAFT-30B-A3B, Pine Voice Preview, grok-voice-think-fast-1.0 + tool-mentor, ...) | The tau2-bench README no longer has a results table; the leaderboard moved to taubench.com in 2026. `submission_type` standard vs custom is the leaderboard's own distinction (standard = default tau2 scaffold). |

Reference-agent naming applied (protocol 4.1): `OSWorld reference agent`, `WebArena reference
agent`, `VisualWebArena reference agent`, `tau-bench reference agent (*)`, `tau2-bench reference
agent (*)`. SWE-bench "RAG baseline" rows are kept under that label (non-looping baseline,
definition.md 5.1 case 6). HAL rows always name a scaffold. Terminal-Bench 4.0 rows always name
an agent; TB 1.0 folder names give the agent.

## grey.jsonl

`python scripts/harvest/grey.py --out data/raw/grey.jsonl`
185 URLs tried for 48 systems: **160 pages resolved, 25 failed, 48 records** (every system
has at least one resolving page; no system dropped). One record per system; the record's
abstract is the first 1,500 characters of the first resolving page, and `extra.docs` lists
every page (URL, final URL, title, declared date, size, 400-char excerpt).

Systems and vendors (pages ok / failed): Claude Code (12/0), Claude Agent SDK (4/0), Codex CLI
(6/0), OpenAI Agents SDK (5/0), OpenAI Operator / CUA (3/0), Gemini CLI (5/0), Jules (3/1),
Antigravity (3/1), Google ADK (3/0), Devin (7/0), Cursor Agent (6/0), Replit Agent (2/2),
GitHub Copilot coding agent (3/2), GitHub Copilot CLI (3/0), Amazon Q Developer CLI (4/1), Kiro
(5/0), DeepSeek Harness (dsh) (1/1), Qwen Code (1/2), Qwen-Agent (2/0), Manus (2/1), OpenClaw
(4/0), Goose (2/4), OpenCode (4/0), Cline (3/0), Roo Code (3/0), Aider (5/0), Warp Agent (Oz)
(5/1), Windsurf Cascade (3/1), Factory Droid (3/1), Augment Agent (Auggie) (3/1), Amp (2/1),
Mistral Vibe (6/0), Grok Build (3/0), Perplexity Computer (2/1), AutoGen (3/0), Magentic-One
(2/0), Semantic Kernel Agents (2/0), Microsoft Agent Framework (2/0), Deep Agents (3/0), pi
(4/0), OpenHands (4/0), Trae Agent (1/1), Junie (1/1), Zed Agent (3/0), Kimi CLI (2/0), Crush
(1/0), Continue (2/1), Copilot agent mode (2/1).

Added beyond the task's starting list (found via web search for vendor agent products with
technical documentation): DeepSeek Harness (dsh, `deepseek-ai/deepseek-harness`, Aug 2026),
OpenClaw docs, Grok Build (xAI, `docs.x.ai/build`), Mistral Vibe docs, Perplexity Computer
(launch post + Perplexity Research skills article), Kiro autonomous agent, LangChain Deep
Agents, Earendil pi, Google ADK, Microsoft Agent Framework, GitHub Copilot CLI, VS Code Copilot
agent mode, OpenHands docs, ByteDance Trae Agent, JetBrains Junie, Zed Agent, Kimi CLI, Charm
Crush, Continue.

Dates: 7 records carry a date declared by the page (Gemini CLI 2026-04-17, OpenCode
2026-09-16, Roo Code 2026-05-15, Warp 2026-09-14, Amp 2026-09-02, Perplexity Computer
2026-02-25, plus dated engineering posts inside `extra.docs`, e.g. Devin 2024-03-12 /
2025-04-03 / 2025-06-12 / 2025-11-14); the other 41 use the retrieval date
(`extra.date_source = "retrieval"`), because vendor doc pages declare no publication date.

### Failed URLs (25; recorded, not retried by hand)

| system | URL | result |
|---|---|---|
| Jules | https://developers.googleblog.com/en/jules-tools-cli/ | HTTP 404 |
| Antigravity | https://antigravity.google/docs | 200 but 86 chars (client-rendered shell); `/docs/cli/overview/` and the two blog posts resolved |
| Replit Agent | https://docs.replit.com/replitai/agent-overview | HTTP 404 |
| Replit Agent | https://blog.replit.com/agent3 | HTTP 404 |
| GitHub Copilot coding agent | https://docs.github.com/en/copilot/concepts/coding-agent/about-coding-agent | HTTP 404 (moved to `/concepts/agents/coding-agent/about-coding-agent`, which resolved) |
| GitHub Copilot coding agent | https://github.blog/ai-and-ml/github-copilot/how-to-use-github-copilot-coding-agent-effectively/ | HTTP 404 |
| Amazon Q Developer CLI | https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-chat.html | 200 but 18 chars (AWS docs are client-rendered); `what-is.html`, the GitHub README and two aws.amazon.com pages resolved |
| DeepSeek Harness (dsh) | https://deepseek-harness.github.io/deepseek-harness/ | 200 but 16 chars (client-rendered); README resolved |
| Qwen Code | https://qwenlm.github.io/qwen-code-docs/en/ and `/qwen-code-docs/` | 200 but <100 chars (client-rendered); README resolved |
| Manus | https://manus.im/docs/introduction/what-is-manus | HTTP 404; `manus.im/docs` and the context-engineering post resolved |
| Goose | https://goose-docs.ai/docs/getting-started/using-goose, /docs/, /docs/guides/goose-permissions, /blog/2025/03/31/goose-architecture/ | 404 / 200-but-empty (goose-docs.ai is client-rendered after the move to the Agentic AI Foundation); READMEs of `aaif-goose/goose` and `block/goose` resolved |
| Warp Agent (Oz) | https://www.warp.dev/blog/oz | HTTP 404; five docs.warp.dev pages resolved |
| Windsurf Cascade | https://windsurf.com/cascade | HTTP 429 after 3 retries (Cloudflare); docs.windsurf.com pages and the SWE-1.5 post resolved |
| Factory Droid | https://factory.ai/news/droid-cli | HTTP 404 |
| Augment Agent (Auggie) | https://docs.augmentcode.com/setup-augment/agent | HTTP 404 |
| Amp | https://ampcode.com/news/subagents | HTTP 404 |
| Perplexity Computer | https://www.perplexity.ai/help-center/en/articles/12730642-perplexity-computer | HTTP 404 |
| Trae Agent | https://docs.trae.ai/ide/agent | 200 but 54 chars (client-rendered); README resolved |
| Junie | https://www.jetbrains.com/help/junie/get-started-with-junie.html | 200 but 0 chars (client-rendered); `jetbrains.com/junie/` resolved |
| Continue | https://docs.continue.dev/agent/how-it-works | 200 but 27 chars (client-rendered); docs root and README resolved |
| Copilot agent mode | https://code.visualstudio.com/docs/copilot/agents | HTTP 404; `/docs/copilot/chat/chat-agent-mode` and the Feb 2025 blog post resolved |

Not attempted (no public technical documentation found in the search, or product is a model
API rather than a harness): xAI "Grok agent" other than Grok Build; Alibaba "Qwen Code" docs
site (client-rendered, README used instead); Manus system card (none published).

## Caveats for screening

* Leaderboard records are for the outcomes table and for discovering systems with no paper;
  a system name on a leaderboard is not evidence of codability (protocol 4.7).
* GAIA test-split names should be screened only when they also appear elsewhere (`dedupe.py`
  clusters on normalised title, so a GAIA name that equals a repo or paper system name will
  merge with it).
* Wayback captures are not stored by these scripts; `M6 pinned_version` captures for closed
  systems (protocol 4.5) must be taken at search freeze.
