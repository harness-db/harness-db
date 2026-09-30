# Awesome-list pull requests

Verified 2026-09-30 with the GitHub API: repository metadata, README and CONTRIBUTING text, and merged
and closed pull requests. Star counts and dates are that day's values. Every list below merged a pull
request from an outside contributor in 2026. Open the PRs from a fork after the arXiv listing is live, one
list per day, and always disclose that you are the author.

The paper title, for lists that cite papers (from `paper/main.tex`), is *The Anatomy of Agent Harnesses: A
Systematic Review, Unified Taxonomy, and Coded Dataset (HARNESS-DB) of LLM Agent Scaffolding,
2022–2026*. GitHub detects the repository licence as MIT, which is the code licence. The data licence is
CC BY 4.0, in `LICENSE-DATA`. Give both wherever a list asks for the licence.

| # | List | Stars | Last push | Ready now? |
|---:|---|---:|---|---|
| 1 | walkinglabs/awesome-harness-engineering | 4,238 | 2026-08-19 | yes |
| 2 | Jenqyang/Awesome-AI-Agents | 1,249 | 2026-09-29 | yes |
| 3 | benchflow-ai/awesome-evals | 933 | 2026-09-24 | after arXiv; has a traction rule (see below) |
| 4 | zjunlp/LLMAgentPapers | 3,123 | 2026-09-12 | after arXiv |
| 5 | VoltAgent/awesome-ai-agent-papers | 1,809 | 2026-09-21 | after arXiv |
| 6 | Gloriaameng/Awesome-Agent-Harness | 362 | 2026-07-28 | after arXiv, and after the email to Meng et al. (`08`) |
| 7 | kyrolabs/awesome-agents | 2,867 | 2026-09-29 | wait until the repository has some history (auto-rejects brand-new repos) |
| 8 | punkpeye/awesome-mcp-servers | 95,709 | 2026-09-27 | blocked: needs a Glama listing, which needs a Dockerfile |
| 9 | RyanAlberts/best-of-Agent-Harnesses | 1,010 | 2026-09-27 | by issue, not PR |

---

## 1. walkinglabs/awesome-harness-engineering

- **Repo:** <https://github.com/walkinglabs/awesome-harness-engineering>.
- **Merge record:** 54 merged PRs, e.g. #76 and #74 (both merged 2026-08-19). Merges come in batches: 30 PRs
  were open, the oldest from 2026-08-20, so expect a wait.
- **CONTRIBUTING rules:**
  - format `- [Name](https://example.com) - Short description focused on why this matters for harness
    engineering.`;
  - put the entry in the most specific section, and in one section only;
  - **disclose your affiliation**;
  - no promotional claims, badges or campaign parameters.
- **Section:** `## Foundations`, which already lists the HarnessCard position paper. Alternative:
  `### Evaluation Design` under `## Evals & Observability`.
- **Neighbouring line (verbatim, shortened):** `- [Harness Engineering for Language Agents: The Harness Layer as
  Control, Agency, and Runtime](https://www.preprints.org/manuscript/202603.1756) - A position paper that
  treats the harness layer as a first-class research object, ...`

PR title: `Add HARNESS-DB (coded dataset of agent harness designs) to Foundations`

Line:

```markdown
- [HARNESS-DB](https://github.com/harness-db/harness-db) - Open dataset of 1,256 LLM agent harnesses coded on 38 design dimensions (context, tools, loop, memory, verification, budgets, sandbox, observability), each value backed by a verbatim quote and a file:line@commit locator, so harness designs can be compared and checked against their source.
```

PR body:

```markdown
Adds HARNESS-DB to Foundations.

Disclosure: I am the author and maintainer.

What it is: a coded dataset of 1,256 agent harnesses on 38 design dimensions, from a pre-registered systematic review (osf.io/ab2wn). Every coded value has a verbatim quote and a locator; cells with no evidence are marked not_reported. Data CC BY 4.0, code MIT. Paper: https://arxiv.org/abs/[arXiv id]

Placed in Foundations next to the HarnessCard paper; happy to move it to Evals & Observability if you prefer.
```

## 2. Jenqyang/Awesome-AI-Agents

- **Repo:** <https://github.com/Jenqyang/Awesome-AI-Agents>. Active: external PRs #528 and #532 were merged
  on 2026-09-29.
- **CONTRIBUTING rules:**
  - format `- [ProjectName](https://github.com/org/repo) - Neutral one-line description. ![GitHub Repo
    stars](https://img.shields.io/github/stars/org/repo?style=social)`;
  - one entry per PR;
  - an open-source licence visible in the GitHub metadata (detected here: MIT);
  - "no unverifiable claims like 'best'/'first'".
- **Section:** `## Reference Repo`, which already holds best-of-Agent-Harnesses and the Orca incident database.
- **Neighbouring line (verbatim, shortened):** `- [Orca AI Incident Archive](https://github.com/Continuum-AI-Corp/Orca-AI-Incident-Archive) - Open database of publicly disclosed AI agent security incidents since January 2025 ... ![GitHub Repo stars](...)`

PR title: `Reference Repo: add HARNESS-DB (coded dataset of 1,256 agent harnesses)`

Line:

```markdown
- [HARNESS-DB](https://github.com/harness-db/harness-db) - Open dataset of 1,256 LLM agent harnesses coded on 38 design dimensions, each value with a verbatim quote and a file:line@commit or paper-section locator, with a Python loader, an MCP server and a web explorer (data CC BY 4.0, code MIT). ![GitHub Repo stars](https://img.shields.io/github/stars/harness-db/harness-db?style=social)
```

PR body:

```markdown
Adds one entry to Reference Repo. Disclosure: I am the author.
Repository licence: MIT (code) and CC BY 4.0 (data, LICENSE-DATA). Paper: https://arxiv.org/abs/[arXiv id]
```

## 3. benchflow-ai/awesome-evals ("Awesome Agent Evals")

- **Repo:** <https://github.com/benchflow-ai/awesome-evals>.
- **Merge record:** 31 merged, e.g. #74 and #73 (both 2026-08-20). 43 were open.
- **CONTRIBUTING rules:**
  - format `- **[Title](https://url)** — Author/Org — <https://url> · *type* — one-line note. 🆕 (if 2025–2026)`;
  - self-submissions are welcome with disclosure;
  - **every number must appear verbatim in the linked source**. The README does carry "1,256 systems",
    "38 design dimensions" and "48.9% of cells are documented silence";
  - one change per PR.
- **Risk:** "Tools need evidence someone else uses them ... a brand-new repo with no users outside the
  authoring org is a 'come back later'." Submitting it as a `*dataset*` with the paper may put it outside
  that bar, but this is **not confirmed**. If the PR is closed as "come back later", resubmit once outside
  use is visible (issues, forks, citations).
- **Section:** `## 3 · The model / harness / skill decomposition`. Alternative: `## 9 · Agent-specific evaluation`.
- **Neighbouring line (verbatim, shortened):** `- **[Holistic Agent Leaderboard (HAL)](https://hal.cs.princeton.edu/)** — Princeton SAgE team (Kapoor, Narayanan, et al.) — <https://hal.cs.princeton.edu/> · *benchmark* — Standardized, cost-aware harness ... 🆕`

PR title: `Add HARNESS-DB (dataset of harness designs) to the model/harness/skill section`

Line (the trailing 🆕 is the list's required marker for entries from 2025–2026):

```markdown
- **[HARNESS-DB](https://github.com/harness-db/harness-db)** — Bhaskar Gurram — <https://github.com/harness-db/harness-db> · *dataset* — 1,256 systems coded on 38 design dimensions with a verbatim quote behind every value; 48.9% of cells are documented silence, which is why harness configurations so often cannot be compared. Paper arXiv:[arXiv id]. 🆕
```

PR body:

```markdown
Disclosure: I am the author. Every number in the line appears verbatim in the repository README (https://github.com/harness-db/harness-db#readme). One change in this PR.
```

## 4. zjunlp/LLMAgentPapers

- **Repo:** <https://github.com/zjunlp/LLMAgentPapers>.
- **Merge record:** external PRs #66 (2026-09-12) and #65 (2026-09-05). None were open.
- **Rules:** there is no CONTRIBUTING. The README says "If you know of any important works we've missed,
  please contribute."
- **Section:** `### Overview` under `## 🌄 Papers`, a numbered list. Its last item was 10, the HarnessCard paper.
- **Neighbouring entry (verbatim):**

  ```
  10. **Harness Engineering for Language Agents: The Harness Layer as Control, Agency, and Runtime**

     *Chaoyue He, Xin Zhou, Di Wang, Hong Xu, Wei Liu, Chunyan Miao.* [[abs](https://www.preprints.org/manuscript/202603.1756/v2)], 2026.3
  ```

PR title: `Add The Anatomy of Agent Harnesses (HARNESS-DB) to Overview`

Entry. Renumber it if the list has grown, and replace `[M]` with the arXiv month:

```markdown
11. **The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026**

   *Bhaskar Gurram.* [[abs](https://arxiv.org/abs/[arXiv id])][[code](https://github.com/harness-db/harness-db)], 2026.[M]
```

PR body: `Adds a systematic review of agent harnesses with its coded dataset. Disclosure: I am the author.`

## 5. VoltAgent/awesome-ai-agent-papers

- **Repo:** <https://github.com/VoltAgent/awesome-ai-agent-papers>. External PRs #42 and #40 were merged on
  2026-09-12.
- **CONTRIBUTING rules:**
  - arXiv papers only, and the **link must point to the PDF URL**;
  - 1–2 plain-English sentences, no product-pitch tone;
  - PR title `Add paper: Paper Title`;
  - only papers from January 2026 onward.
- **Section:** "Eval & Observability", an HTML `<details>` table with the newest rows at the top.
- **Neighbouring row (verbatim, shortened):** `| **[PerspectiveGap: A Benchmark for Multi-Agent Orchestration Prompting](https://arxiv.org/pdf/2606.08878)** - A 110-scenario benchmark ... | <a href="https://arxiv.org/abs/2606.08878"><img src="https://img.shields.io/badge/arXiv-2606.08878-b31b1b.svg" alt="arXiv" /></a> |`

PR title: `Add paper: The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026`

Row, to insert at the top of the table:

```markdown
| **[The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026](https://arxiv.org/pdf/[arXiv id])** - Codes 1,256 agent harnesses on 38 design dimensions, with a quoted source behind every value. Almost half of all cells (48.9%) are undocumented, and the sandbox layer is the least documented of all. | <a href="https://arxiv.org/abs/[arXiv id]"><img src="https://img.shields.io/badge/arXiv-[arXiv id]-b31b1b.svg" alt="arXiv" /></a> |
```

## 6. Gloriaameng/Awesome-Agent-Harness

This is the companion catalogue of Meng et al.'s survey, one of the seven prior works. **Send the email to
Meng et al. (`08_outreach_survey_authors.md`) first**, and open this PR a few days later.

- **Repo:** <https://github.com/Gloriaameng/Awesome-Agent-Harness>.
- **Merge record:** #12 (from a first-time contributor) and #10 were merged on 2026-07-28. 6 were open.
- **Rules:** there is no CONTRIBUTING. A `†` after the name marks a preprint.
- **Section:** `#### Related Surveys` under `### Emerging Topics`. Alternative: `#### Evaluation Infrastructure`.
- **Neighbouring line (verbatim, from merged #12):** `- <u>ClawBench</u>†: **"ClawBench: Can AI Agents Complete Everyday Online Tasks?"**. *Zhang et al.* arXiv 2026. [[Paper](https://arxiv.org/abs/2604.08523)] [[Code](https://github.com/reacher-z/ClawBench)] [[Project](https://claw-bench.com/)]`

PR title: `Add HARNESS-DB survey and dataset to Related Surveys`

Line:

```markdown
- <u>HARNESS-DB</u>†: **"The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026"**. *Gurram*. arXiv 2026. [[Paper](https://arxiv.org/abs/[arXiv id])] [[Code](https://github.com/harness-db/harness-db)] [[Project](https://harness-db.github.io/harness-db/)]
```

PR body:

```markdown
Adds a systematic review with a coded dataset of 1,256 harnesses. Disclosure: I am the author. The paper crosswalks your H = (E, T, C, S, L, V) definition against our nine layers (Section 3, crosswalk table).
```

## 7. kyrolabs/awesome-agents

- **Repo:** <https://github.com/kyrolabs/awesome-agents>.
- **Merge record:** external PRs #804 (2026-09-29) and #798 (2026-09-26). Most recently closed PRs were not
  merged.
- **CONTRIBUTING rules:**
  - the project must be open source;
  - **add new items at the bottom** of the section;
  - submit a PR, not an issue;
  - PRs are rejected by rules "managed and applied automatically" for a "brand new repo with no history,
    brand new user, or wrong place in the list";
  - the project must relate to agentic frameworks.
- **Section:** `## Testing and Evaluation`, at the bottom.
- **Neighbouring line (verbatim, shortened):** `- [ClawMetry](https://github.com/vivekchand/clawmetry): Open-source, zero-config real-time observability dashboard for AI agent runtimes ... ![GitHub Repo stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=social)`
- **Timing:** the repository was created on 2026-09-16. Wait until it shows a few weeks of outside activity
  (issues and stars) before submitting.

PR title: `Add HARNESS-DB to Testing and Evaluation`

Line:

```markdown
- [HARNESS-DB](https://github.com/harness-db/harness-db): Open dataset of 1,256 LLM agent harnesses coded on 38 design dimensions, each value backed by a verbatim quote and a file:line@commit locator, with a Python loader, an MCP server and a web explorer. ![GitHub Repo stars](https://img.shields.io/github/stars/harness-db/harness-db?style=social)
```

## 8. punkpeye/awesome-mcp-servers (the MCP server only)

- **Repo:** <https://github.com/punkpeye/awesome-mcp-servers>.
- **Merge record:** external PRs #14672 (2026-09-21) and #13975 (2026-09-15). About 100 were open.
- **Rules (CONTRIBUTING and the `check-glama.yml` workflow):**
  - alphabetical order within the category, one server per line;
  - a public GitHub repository;
  - **the server must be listed on Glama and pass its checks**. Glama needs a Dockerfile so that the server
    starts and answers introspection;
  - the line must carry the Glama score badge;
  - the link text must equal `owner/repo`, and the first link must be `https://github.com/...`;
  - language and scope emoji (🐍 Python, 🏠 local);
  - subpath links are accepted.
- **Blocked:** `mcp_server/` has no Dockerfile today and there is no Glama listing. Do both first, then
  confirm the Glama slug, which the badge URLs below assume.
- **Section:** `### 🔬 <a name="research"></a>Research`.

PR title: `Add harness-db/harness-db (HARNESS-DB MCP server) to Research`

Line (the emoji are the list's required markers):

```markdown
- [harness-db/harness-db](https://github.com/harness-db/harness-db/tree/main/mcp_server) [![harness-db MCP server](https://glama.ai/mcp/servers/harness-db/harness-db/badges/score.svg)](https://glama.ai/mcp/servers/harness-db/harness-db) 🐍 🏠 - Query HARNESS-DB, a dataset of 1,256 LLM agent harnesses coded on 38 design dimensions, and get the verbatim evidence quote and locator behind each cell.
```

## 9. RyanAlberts/best-of-Agent-Harnesses (issue, not PR)

- **Repo:** <https://github.com/RyanAlberts/best-of-Agent-Harnesses>. It describes itself as a "Ranked list of
  150+ agent harnesses across 12 categories, rescored weekly", with JSON, llms.txt and an MCP server. It is
  **the closest neighbour to HARNESS-DB** found in the search, and the paper does not cite it.
- **Rules (CONTRIBUTING):**
  - the README and JSON are generated by `scripts/generate.py`, so direct edits cannot be merged;
  - open an issue titled `Add project: <name>` instead.
- **Section:** HARNESS-DB is not a harness, so ask for `## Related Resources`. **Not verified:** whether
  Related Resources is generated by `generate.py`.
- **Neighbouring line (verbatim):** `- [**Anthropic – Effective harnesses for long-running agents**](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): Session bridging, feature lists, incremental progress, testing`

Issue title: `Add project: HARNESS-DB (Related Resources)`

Issue body:

```markdown
HARNESS-DB is a coded dataset rather than a harness, so I am asking for Related Resources rather than a ranked category. Disclosure: I am the author.

Suggested line:
- [**HARNESS-DB – coded dataset of 1,256 agent harnesses**](https://github.com/harness-db/harness-db): 38 design dimensions per harness, a verbatim quote and locator per value, Python loader, MCP server and explorer

Several of your ranked projects are in it at a pinned commit (for example OpenHands, Codex CLI, Hermes Agent and nanobot), each with its own explorer page: https://harness-db.github.io/harness-db/
```

---

## Checked and rejected

| Repo | Reason |
|---|---|
| e2b-dev/awesome-ai-agents | Scope is "only for AI assistants and agents"; almost no external merges. |
| Hannibal046/Awesome-LLM | Last push and merge 2025-07-31. |
| WooooDyy/LLM-Agent-Paper-List | Last merged PR 2024-06-07. |
| Paitesanshi/LLM-Agent-Survey | Last push 2025-02-20. |
| AGI-Edgerunners/LLM-Agents-Papers | Last push 2025-07-12 (merge history not checked because of a rate limit). |
| Picrew/awesome-agent-harness | 0 merged PRs; the maintainer commits directly. Suggest by issue at most. Companion catalogue of Li et al. |
| ai-boost/awesome-harness-engineering | 2 merged PRs ever; entries are added by direct commit. |
| tmgthb/Autonomous-Agents | 0 merged PRs. |
| ggjy/Awesome-Agent-Engineering | No merged PRs. Companion list of Guo et al. |
| codefuse-ai/Awesome-Code-LLM | Code-LLM papers, a weak fit; last external merge 2025-12-29. |
| kaushikb11/awesome-llm-agents | Software projects only, generated from YAML, 25-star minimum. |
| bradAGI/awesome-cli-coding-agents | Entries must be CLI coding agents. |
| slavakurilyak/awesome-ai-agents | Agent projects only. |
| tensorchord/Awesome-LLMOps | No fitting section. |
| awesomedata/awesome-public-datasets | Last merged PR 2021-03-11. |
| appcypher/awesome-mcp-servers | Archived. |
| AutoJunjie/awesome-agent-harness | Stale since 2026-04-19. |
| YennNing/Awesome-Code-as-Agent-Harness-Papers, RUCAIBox/awesome-agent-harness | 0 merged PRs. |

Not verified: wong2/awesome-mcp-servers (its pulls API returned 404) and hesreallyhim/awesome-claude-code
(its rules were not evaluated).
