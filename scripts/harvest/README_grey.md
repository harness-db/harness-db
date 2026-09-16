# Grey sources: leaderboards and vendor documentation

Two harvesters cover the protocol's non-bibliographic information sources (protocol section 5:
"major-lab technical reports; agent leaderboards for the outcomes table"). Both use the common
CLI from `common.py` (`--out`, `--count-only`, `--max-records`, `--log-level`; `--since/--until`
are accepted but ignored, leaderboards and docs are snapshots, not date-filtered searches),
write `common.Record` JSONL, print a final `SUMMARY {...}` line, and never raise on one failed
source: the failure is logged, recorded in the summary, and the run continues. Per-run fetch
counts and failures go to `data/raw/grey_notes.md`.

```
python scripts/harvest/leaderboards.py [--out data/raw/leaderboards.jsonl] [--count-only] [--only swebench,hal,...]
python scripts/harvest/grey.py         [--out data/raw/grey.jsonl]         [--count-only] [--only "Claude Code,Devin"]
```

Both need `requests`, `lxml`, `pandas` + `openpyxl` (xlsx leaderboards); `pyyaml` only for the
SWE-bench GitHub fallback; `gh` (authenticated) for the Terminal-Bench 1.0 logs and the
SWE-bench fallback.

## leaderboards.py

One record per **distinct system per leaderboard family** (protocol section 4.1: the unit is
the harness, not the submission). Entries are grouped on `normalize_title(system)`; a system
that appears on several splits or benchmarks of one family (e.g. SWE-agent on Verified, Lite
and Multimodal) is one record whose `extra.entries` lists every submission.

| field | content |
|---|---|
| `id` / `source_id` | `leaderboard:<family-slug>:<system-slug>` / `<family-slug>/<system-slug>` |
| `source` | `leaderboard` |
| `query_used`, `venue` | leaderboard family: `SWE-bench`, `HAL`, `OSWorld`, `WebArena`, `Terminal-Bench`, `GAIA`, `tau-bench`, `tau2-bench` |
| `title` | system (harness) name as the leaderboard labels it |
| `abstract` | one-line description + "Models and scores seen: model: score metric [split, date]; ..." (cut at 2,500 chars) |
| `url` | first non-empty entry URL (submission `site`, agent page, paper link, repo) |
| `date` | earliest submission date seen (`YYYY-MM-DD` or `YYYY-MM`); `None` for HAL (no dates on the site) |
| `authors` | organisations named for the system (agent_org / institution / submitting org) |
| `categories` | splits / sub-benchmarks the system appears on |
| `extra` | `{"benchmark", "n_entries", "splits", "entries": [{split, model, score, metric, date, url, org, raw_name, ...source fields}]}` |

Bare-model rows (the leaderboard's own scaffold run with a model) are recorded as the system
`<benchmark> reference agent` per protocol section 4.1; the row label is kept in
`entries[].raw_name`. Where this is applied is listed per leaderboard below.

### Sources and quirks

| key | source actually used | notes |
|---|---|---|
| `swebench` | `https://www.swebench.com/` embeds the whole leaderboard as JSON in `<script id="leaderboard-data">` (list of `{name, results:[...]}` for Verified, Lite, Test, Multimodal, Multilingual). | `system` = `agent` field (falls back to `name`), `model` = `model_display`, `score` = `resolved` (% resolved), `date` = submission date, `url` = `site`. Fallback when the site is unreachable: `gh api repos/SWE-bench/experiments/git/trees/main?recursive=1` → every `evaluation/<split>/<dir>/metadata.yaml` from raw.githubusercontent.com, `% resolved` recomputed from `results/results.json` against the split size (500/300/2294/517/300) when `info.resolved` is absent. Note the site JSON currently lists 323 submissions vs 319 `metadata.yaml` files in the repo (the site includes a few entries whose metadata lives elsewhere). "RAG baseline" rows are SWE-bench's non-looping baseline; they are kept under their own label and are *not* renamed to a reference agent (definition.md section 5.1 case 6 says SWE-bench ships no looping baseline). |
| `hal` | `https://hal.cs.princeton.edu/<benchmark>` for gaia, swebench_verified_mini, taubench_airline, usaco, corebench_hard, scicode, scienceagentbench, assistantbench, online_mind2web. Tables are server-rendered HTML (parsed with lxml). | No machine-readable dump was found: the site's only fetch is `/update_pricing/<benchmark>`; the `princeton-pli/hal-harness` repo holds agents and benchmarks but no results file; the HF dataset `agent-evals/hal_traces` holds encrypted trace zips, not scores. Columns: Scaffold → `system`, Primary Model/Models → `model`, Accuracy (with CI) → `score`, Cost (USD), Verified, Runs, Traces (HF zip URL), plus level columns for GAIA. No submission dates on the site (`date=None`). `url` = the site's `/agent/<name>` page. |
| `osworld` | `https://os-world.github.io/static/data/osworld_verified_results.xlsx` (OSWorld-Verified, 22 columns incl. per-domain scores) and `.../self_reported_results.xlsx` (sheets Screenshot, A11y_tree, Screenshot_A11y_tree, Set-of-Mark). These are the files the site's JS renders. | Row labels mix harnesses and models. Rule: `"X w/ Y"` → system X, model Y; otherwise use the `Approach type` column: "Agentic framework" → system = label; "Specialized model"/"General model" (or a label matching the model-name regex) → system `OSWorld reference agent`, model = label. Dates like `Mar 20, 2024` and Excel timestamps are normalised. Per-domain scores and success/total are kept under `entries[]`. |
| `webarena` | webarena.dev is now a landing page ("WebArena-x"); the original page at `https://webarena.dev/og/` links the leaderboard Google Sheet `1M801lEpBbKSNwP-vDBkC_pF7LdyGU1f_ufZb_NWNBZQ`. Exported as xlsx (`/export?format=xlsx`) because the CSV export drops the hyperlinks. Sheets: WebArena (header row 1) and VisualWebArena (header on row 3, different columns). | `system` = the `Work` (WebArena) or `Result Source` (VWA) cell unless it is a URL / "Self-reported"; then the `Model` cell. A model-only label (GPT-4, Llama3, Gemini Pro, ...) becomes `WebArena reference agent`. `url` = hyperlink of the Work/Result Source cell. Dates are month precision (`MM/YYYY` → `YYYY-MM`). |
| `terminal_bench` | (a) `https://www.tbench.ai/leaderboard`: Next.js page; rows are inside the `self.__next_f.push` flight payload as JSON objects with `leaderboard_id`, `metadata.{agent_display,model_display,agent_org,date,reasoning_effort}`, `metrics.{accuracy,n_trials,total_cost_usd,...}` (extracted by walking back from each `"leaderboard_id"` to the enclosing `{` and `json.raw_decode`). Only the current board (Terminal-Bench 4.0) is served. (b) Terminal-Bench 1.0 (`terminal-bench-core@0.1.1`): `laude-institute/terminal-bench-leaderboard` `results/<dataset>/<YYYYMMDD>_<agent>_<model>/<run>/results.json`; `accuracy` averaged over the runs (usually 5); one `gh api` listing per submission plus one raw fetch per run. | **Terminal-Bench 2.0 is a known gap**: the live site only serves 4.0; Harbor Hub (`hub.harborframework.com/datasets/terminal-bench/terminal-bench/2?tab=leaderboard`) renders rows client-side from an endpoint that answers 404 without a session (`/api/datasets/.../tasks` works, no leaderboard section does); Wayback captures of the 2025-26 site are the react-query client shell (no rows) or redirect to the current board; `harbor-framework/terminal-bench` only holds `leaderboard/runs/*.json` job configs and `laude-institute/terminal-bench-2-leaderboard` is an empty repo. |
| `gaia` | HF datasets-server: `https://datasets-server.huggingface.co/rows?dataset=gaia-benchmark/results_public&config=2023&split={validation,test}` paged 100 at a time (no pyarrow needed). This is the dataset the `gaia-benchmark/leaderboard` Space reads. | `model` column = submission/system name → `system`; `model_family` = LLM → `model`; scores ×100. The test split is an open submission log (3.7k rows, most one-off), so GAIA dominates the record count; filter on `query_used` or `extra.n_entries` if a curated subset is needed. |
| `tau_bench` | `sierra-research/tau-bench` README result tables (Airline, Retail). | Strategies TC (tool-calling), Act, ReAct with a model in parentheses → systems `tau-bench reference agent (tool-calling|Act|ReAct)`; Pass^1..4 kept raw. `??` cells → `score=None`. No dates. |
| `tau2_bench` | taubench.com is a React app that fetches `https://sierra-tau-bench-public.s3.us-west-2.amazonaws.com/submissions/manifest.json` (`submissions`, `legacy_submissions`, `voice_submissions`) then `<dir>/submission.json`. The tau2-bench README no longer has a results table. | `submission_type: standard` → `tau2-bench reference agent` (text) or `tau2-bench reference agent (tau-voice)` (voice); `custom` → system = `model_name (submitting_organization)`. One entry per domain (airline, retail, telecom, banking_knowledge) with pass^1..4 and cost. |

## grey.py

A curated map `SYSTEMS = {system: (vendor, [(url, kind), ...])}` of vendor / major-lab
harness documentation, engineering posts, announcements, READMEs and technical reports
(kinds: `docs`, `engineering`, `announcement`, `readme`, `tech_report`). Every URL is fetched
with a 1 s pacing; GitHub repo/blob URLs are read through raw.githubusercontent.com (README.md
or the file). A page counts as resolved only if it returns HTTP 200 **and** at least 300
characters of main text (`<main>`/`<article>`/`role=main`/`.markdown-body`, falling back to
`<body>`, scripts/nav/header/footer removed). Client-rendered shells and soft 404s therefore
count as failures.

One record per system (not per page):

| field | content |
|---|---|
| `id` / `source_id` | `grey:<system-slug>` / `<system-slug>` |
| `source`, `query_used`, `venue` | `grey`, `vendor-docs`, `vendor-docs` |
| `title` | system name |
| `abstract` | first 1,500 characters of the primary page (the first URL in list order that resolved) |
| `url` | primary page |
| `date` | page date from `article:published_time`/`date`/`datePublished`/`<time datetime>` when present, else retrieval date (`extra.date_source` says which) |
| `authors` | `[vendor]` |
| `categories` | kinds of the resolved pages |
| `extra` | `{"vendor", "primary_kind", "primary_title", "date_source", "docs": [{url, final_url, fetched, kind, title, date, chars, excerpt(400)}], "failed": [{url, kind, status, error}]}` |

Systems with no resolving page produce no record and are listed under `no_record` in the
SUMMARY line. Redirect chains are followed; `final_url` records where a page ended up (several
vendors moved their docs during 2025-2026: docs.claude.com → code.claude.com, docs.cursor.com
→ cursor.com/docs, Gemini CLI → Antigravity CLI).

Quirks: Mintlify/Docusaurus sites are server-rendered and parse well; `openai.com/index/*`
and `x.ai/news/*` are served through Cloudflare and may answer 403 to non-browser clients (the
client sends browser-like `Accept` headers but keeps the project User-Agent); some Google
properties (`jules.google`, `antigravity.google`) are single-page apps with little static
text. Everything that failed in the frozen run is listed in `data/raw/grey_notes.md`.

## Interaction with dedupe.py

`scripts/dedupe.py` merges every `data/raw/*.jsonl`. Leaderboard and grey records have no DOI or
arXiv id, so they only cluster by normalised title; `title` is a system name, which will
cluster identical system names across leaderboards (intended: same system) but will not match
paper titles. Record priority for canonical selection is defined in dedupe.py (paper sources
first); grey and leaderboard records mostly survive as their own candidates, which is what the
protocol wants for systems with no paper (section 4.3).
