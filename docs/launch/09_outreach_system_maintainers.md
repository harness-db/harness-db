# Emails to the maintainers of the 20 highest-starred coded systems

Drafts. These maintainers are the collaborators the project most wants: people who can settle a cell in
two minutes because they wrote the code. Send after launch day, in batches of 10 a day, from
gurrambhaskar.ai@gmail.com, and attach the system's card from `docs/launch/cards/<id>.md`.

**How the 20 were chosen.** `python scripts/system_card.py --top 20 --by stars` does it:

- it picks weight-bearing systems that have a GitHub repository;
- it ranks them by the sampling frame's stars snapshot;
- it keeps one system per repository. OpenHands also has a second entry, `openhands-2`, which the
  OpenHands email covers.

For each system, the three `not_reported` design dimensions listed are the ones on which the whole
field is most often silent: the weighted `not_reported` rate in `data/analysis/summary_one_screen.csv`.
This is the same order as the card's "Silent cells you can settle fastest".

**Maintaining organization.** Taken from the GitHub API on 2026-09-30: the repository owner and the
owner's profile name. An organization is named only when the repository belongs to it, and a personal
account is labelled as one. "Live stars" is that day's `stargazers_count`; "frame stars" is the
snapshot the ranking used.

**Where to send it.**

- Use a maintainer email that the repository or website prints publicly.
- Otherwise, use GitHub Discussions where they are enabled. Each variant says whether they are.
- Never file this as an issue on their tracker. It is not a bug report.
- For company-owned repositories (Anthropic, OpenAI, Microsoft, ByteDance), use the public contact
  channel. Do not guess employee addresses.

## Template

```text
Subject: HARNESS-DB coded <system> at <tag>: 3 cells you can settle in two minutes

Hello <maintainers>,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded <system> at <tag> (commit <sha12>, <date>). Its 38 cells are in the attached card and at <explorer permalink>.

<n_coded> of the 38 cells have a value. <n_nr> are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- <dim 1>: <link>
- <dim 2>: <link>
- <dim 3>: <link>

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## The 20

| # | System | Repository | Maintained by | Frame stars | Live stars | Pinned | Valued / not_reported | Top-3 silent dimensions |
|---:|---|---|---|---:|---:|---|---|---|
| 1 | Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Nous Research | 246,141 | 250,268 | v2026.8.31 `29112bef0992` | 13 / 25 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 2 | Claude Code | [anthropics/claude-code](https://github.com/anthropics/claude-code) | Anthropic | 146,623 | 148,672 | v2.1.252 `f275fa282e76` | 16 / 22 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 3 | Codex CLI | [openai/codex](https://github.com/openai/codex) | OpenAI | 125,294 | 127,379 | rust-v0.153.0-alpha.2 `73919571da60` | 31 / 6 | H2 `replayability`, E3 `rollback`, A3 `context_compaction` |
| 4 | Browser Use | [browser-use/browser-use](https://github.com/browser-use/browser-use) | Browser Use | 115,306 | 116,806 | 0.13.8 `eb4126921bea` | 11 / 27 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 5 | TradingAgents | [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | Tauric Research | 107,559 | 109,343 | v0.4.0 `2448d0a12576` | 18 / 20 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 6 | Pi coding agent | [earendil-works/pi](https://github.com/earendil-works/pi) | Earendil Works | 106,254 | 110,687 | v0.84.4 `b79e4cc83497` | 9 / 29 | H2 `replayability`, E3 `rollback`, D3 `state_persistence` |
| 7 | OpenHands (CodeActAgent) | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | OpenHands | 88,433 | 89,611 | OpenHands v1.16.0 `64c126965501` | 18 / 20 | G3 `network_policy`, H2 `replayability`, E3 `rollback` |
| 8 | DeerFlow | [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | ByteDance | 82,541 | 83,265 | v2.0.0 `7e7f04107976` | 24 / 14 | G3 `network_policy`, H2 `replayability`, E3 `rollback` |
| 9 | learn-claude-code (s15 integrated harness) | [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | shareAI | 76,962 | 77,839 | main `0dcafa2ae053` | 26 / 12 | G3 `network_policy`, H2 `replayability`, E3 `rollback` |
| 10 | Ruflo | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | (personal account) | 72,623 | 73,568 | v3.38.20 `e21aa352fdc8` | 18 / 20 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 11 | MetaGPT (software company) | [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | (personal account) | 70,499 | 70,700 | v0.8.2 `df9bc1858f7d` | 12 / 26 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 12 | oh-my-openagent | [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) | (personal account) | 69,107 | 69,672 | v5.0.0-beta.31 `62ed7952533a` | 17 / 21 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 13 | daily_stock_analysis (DSA) | [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) | (personal account) | 65,297 | 65,811 | v3.31.0 `9ab79b82992d` | 21 / 17 | G3 `network_policy`, G2 `filesystem_access`, E3 `rollback` |
| 14 | Strix | [usestrix/strix](https://github.com/usestrix/strix) | Strix | 63,014 | 65,706 | v1.5.3 `7cc9fa9faa01` | 31 / 6 | H2 `replayability`, E3 `rollback`, D3 `state_persistence` |
| 15 | AutoGen (AssistantAgent + UserProxyAgent) | [microsoft/autogen](https://github.com/microsoft/autogen) | Microsoft | 61,061 | 61,242 | python-v0.7.5 `83afbf5857aa` | 15 / 23 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 16 | CrewAI | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | crewAI | 58,663 | 59,225 | 1.15.18 `4bc5d2924218` | 14 / 24 | G3 `network_policy`, G2 `filesystem_access`, E3 `rollback` |
| 17 | Cherry Studio | [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | CherryHQ | 51,871 | 52,278 | v2.0.10 `3db6b513e492` | 7 / 31 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 18 | nanobot | [HKUDS/nanobot](https://github.com/HKUDS/nanobot) | Data Intelligence Lab@HKU | 48,224 | 48,700 | v0.3.0 `3f602fbc8c10` | 21 / 17 | G3 `network_policy`, H2 `replayability`, E3 `rollback` |
| 19 | BettaFish | [666ghj/BettaFish](https://github.com/666ghj/BettaFish) | (personal account) | 42,232 | 42,323 | v3.0.0 `9bb2d32cad11` | 12 / 24 | G3 `network_policy`, H2 `replayability`, G2 `filesystem_access` |
| 20 | DeepTutor | [HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor) | Data Intelligence Lab@HKU | 39,997 | 40,562 | v1.6.2 `3dc372f55128` | 24 / 14 | G3 `network_policy`, G2 `filesystem_access`, E3 `rollback` |

### 1. Hermes Agent (`hermes-agent`)

- Repository: <https://github.com/NousResearch/hermes-agent>, pinned v2026.8.31 @ `29112bef099274229cadff79cdff7bf7b99c4b77` (2026-08-31)
- Maintained by: GitHub org `NousResearch` (profile name "Nous Research")
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/hermes-agent.md`
- Body: 172 words, links excluded

```text
Subject: HARNESS-DB coded Hermes Agent at v2026.8.31: 3 cells you can settle in two minutes

Hello Nous Research team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Hermes Agent at v2026.8.31 (commit 29112bef0992, 2026-08-31). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=hermes-agent.

13 of the 38 cells have a value. 25 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20network_policy&system=hermes-agent&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20replayability&system=hermes-agent&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20hermes-agent%20%2F%20filesystem_access&system=hermes-agent&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 2. Claude Code (`claude-code`)

- Repository: <https://github.com/anthropics/claude-code>, pinned v2.1.252 @ `f275fa282e76c5e5456912268f2c367a7f4f4797` (2026-08-31)
- Maintained by: GitHub org `anthropics` (profile name "Anthropic")
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/claude-code.md`
- Body: 171 words, links excluded

```text
Subject: HARNESS-DB coded Claude Code at v2.1.252: 3 cells you can settle in two minutes

Hello Anthropic team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Claude Code at v2.1.252 (commit f275fa282e76, 2026-08-31). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=claude-code.

16 of the 38 cells have a value. 22 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20network_policy&system=claude-code&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20replayability&system=claude-code&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20claude-code%20%2F%20filesystem_access&system=claude-code&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 3. Codex CLI (`codex-cli`)

- Repository: <https://github.com/openai/codex>, pinned rust-v0.153.0-alpha.2 @ `73919571da608749b867134722fe3b42c1c6097f` (2026-08-31)
- Maintained by: GitHub org `openai` (profile name "OpenAI")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/codex-cli.md` (1 cell `unresolved`)
- Body: 171 words, links excluded

```text
Subject: HARNESS-DB coded Codex CLI at rust-v0.153.0-alpha.2: 3 cells you can settle in two minutes

Hello OpenAI team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Codex CLI at rust-v0.153.0-alpha.2 (commit 73919571da60, 2026-08-31). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=codex-cli.

31 of the 38 cells have a value. 6 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20replayability&system=codex-cli&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20rollback&system=codex-cli&dimension=E3%20rollback&current=not_reported
- context_compaction (A3), on which 77.9% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20codex-cli%20%2F%20context_compaction&system=codex-cli&dimension=A3%20context_compaction&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 4. Browser Use (`browser-use`)

- Repository: <https://github.com/browser-use/browser-use>, pinned 0.13.8 @ `eb4126921bea3373f91afc49fb4b59d6eda7fed6` (2026-08-16)
- Maintained by: GitHub org `browser-use` (profile name "Browser Use")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/browser-use.md`
- Body: 172 words, links excluded

```text
Subject: HARNESS-DB coded Browser Use at 0.13.8: 3 cells you can settle in two minutes

Hello Browser Use team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Browser Use at 0.13.8 (commit eb4126921bea, 2026-08-16). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=browser-use.

11 of the 38 cells have a value. 27 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20network_policy&system=browser-use&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20replayability&system=browser-use&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20browser-use%20%2F%20filesystem_access&system=browser-use&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 5. TradingAgents (`tradingagents`)

- Repository: <https://github.com/TauricResearch/TradingAgents>, pinned v0.4.0 @ `2448d0a12576` (2026-08-31)
- Maintained by: GitHub org `TauricResearch` (profile name "Tauric Research")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/tradingagents.md`
- Body: 171 words, links excluded

```text
Subject: HARNESS-DB coded TradingAgents at v0.4.0: 3 cells you can settle in two minutes

Hello Tauric Research team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded TradingAgents at v0.4.0 (commit 2448d0a12576, 2026-08-31). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=tradingagents.

18 of the 38 cells have a value. 20 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20network_policy&system=tradingagents&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20replayability&system=tradingagents&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20tradingagents%20%2F%20filesystem_access&system=tradingagents&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 6. Pi coding agent (`pi-coding-agent`)

- Repository: <https://github.com/earendil-works/pi>, pinned v0.84.4 @ `b79e4cc834970cca69daebffab7df1da7d1e52c4` (2026-08-28)
- Maintained by: GitHub org `earendil-works` (profile name "Earendil Works")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/pi-coding-agent.md`
- Body: 173 words, links excluded

```text
Subject: HARNESS-DB coded Pi coding agent at v0.84.4: 3 cells you can settle in two minutes

Hello Earendil Works team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Pi coding agent at v0.84.4 (commit b79e4cc83497, 2026-08-28). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=pi-coding-agent.

9 of the 38 cells have a value. 29 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20replayability&system=pi-coding-agent&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20rollback&system=pi-coding-agent&dimension=E3%20rollback&current=not_reported
- state_persistence (D3), on which 86.2% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20pi-coding-agent%20%2F%20state_persistence&system=pi-coding-agent&dimension=D3%20state_persistence&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 7. OpenHands (CodeActAgent) (`openhands`)

- Repository: <https://github.com/OpenHands/OpenHands>, pinned OpenHands v1.16.0 @ `64c126965501` (2026-08-27)
- Maintained by: GitHub org `OpenHands` (profile name "OpenHands"); the release URL `all-hands-ai/openhands` now redirects to `OpenHands/OpenHands`
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/openhands.md`
- Body: 190 words, links excluded

```text
Subject: HARNESS-DB coded OpenHands (CodeActAgent) at OpenHands v1.16.0: 3 cells you can settle in two minutes

Hello OpenHands team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded OpenHands (CodeActAgent) at OpenHands v1.16.0 (commit 64c126965501, 2026-08-27). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=openhands. The release also has a second entry, OpenHands (Agent Canvas), at the same tag: https://harness-db.github.io/harness-db/#system=openhands-2 (9 of 38 valued).

18 of the 38 cells have a value. 20 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20network_policy&system=openhands&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20replayability&system=openhands&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20openhands%20%2F%20rollback&system=openhands&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 8. DeerFlow (`deerflow`)

- Repository: <https://github.com/bytedance/deer-flow>, pinned v2.0.0 @ `7e7f0410797693cf882594555ba414e0361d4c6f` (2026-06-25)
- Maintained by: GitHub org `bytedance` (profile name "Bytedance Inc.")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/deerflow.md`
- Body: 170 words, links excluded

```text
Subject: HARNESS-DB coded DeerFlow at v2.0.0: 3 cells you can settle in two minutes

Hello ByteDance team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded DeerFlow at v2.0.0 (commit 7e7f04107976, 2026-06-25). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=deerflow.

24 of the 38 cells have a value. 14 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20network_policy&system=deerflow&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20replayability&system=deerflow&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deerflow%20%2F%20rollback&system=deerflow&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 9. learn-claude-code (s15 integrated harness) (`learn-claude-code`)

- Repository: <https://github.com/shareAI-lab/learn-claude-code>, pinned main @ `0dcafa2ae053a1ddd6a72f265431104b08a5aa13` (2026-08-26)
- Maintained by: GitHub org `shareAI-lab` (profile name "shareAI"). A community teaching project, **not** Anthropic
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/learn-claude-code.md`
- Body: 173 words, links excluded

```text
Subject: HARNESS-DB coded learn-claude-code (s15 integrated harness) at main: 3 cells you can settle in two minutes

Hello shareAI team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded learn-claude-code (s15 integrated harness) at main (commit 0dcafa2ae053, 2026-08-26). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=learn-claude-code.

26 of the 38 cells have a value. 12 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20network_policy&system=learn-claude-code&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20replayability&system=learn-claude-code&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20learn-claude-code%20%2F%20rollback&system=learn-claude-code&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 10. Ruflo (`ruflo`)

- Repository: <https://github.com/ruvnet/ruflo>, pinned v3.38.20 @ `e21aa352fdc80fd2d3cc4e83404a76a18d118b96` (2026-08-24)
- Maintained by: a personal account, `ruvnet` (profile name "rUv"); no organization
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/ruflo.md`
- Body: 169 words, links excluded

```text
Subject: HARNESS-DB coded Ruflo at v3.38.20: 3 cells you can settle in two minutes

Hello ruvnet,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Ruflo at v3.38.20 (commit e21aa352fdc8, 2026-08-24). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=ruflo.

18 of the 38 cells have a value. 20 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20network_policy&system=ruflo&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20replayability&system=ruflo&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20ruflo%20%2F%20filesystem_access&system=ruflo&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 11. MetaGPT (software company) (`metagpt`)

- Repository: <https://github.com/FoundationAgents/MetaGPT>, pinned v0.8.2 @ `df9bc1858f7d` (2025-03-02)
- Maintained by: GitHub org `FoundationAgents` (no profile name set); the release URL `geekan/metagpt` now redirects to `FoundationAgents/MetaGPT`
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/metagpt.md`
- Body: 171 words, links excluded

```text
Subject: HARNESS-DB coded MetaGPT (software company) at v0.8.2: 3 cells you can settle in two minutes

Hello FoundationAgents,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded MetaGPT (software company) at v0.8.2 (commit df9bc1858f7d, 2025-03-02). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=metagpt.

12 of the 38 cells have a value. 26 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20network_policy&system=metagpt&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20replayability&system=metagpt&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20metagpt%20%2F%20filesystem_access&system=metagpt&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 12. oh-my-openagent (`oh-my-openagent`)

- Repository: <https://github.com/code-yeongyu/oh-my-openagent>, pinned v5.0.0-beta.31 @ `62ed7952533a45470ac4008eb199e90be20bd09c` (2026-08-31)
- Maintained by: a personal account, `code-yeongyu` (profile name "YeonGyu-Kim"); no organization
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/oh-my-openagent.md`
- Body: 169 words, links excluded

```text
Subject: HARNESS-DB coded oh-my-openagent at v5.0.0-beta.31: 3 cells you can settle in two minutes

Hello code-yeongyu,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded oh-my-openagent at v5.0.0-beta.31 (commit 62ed7952533a, 2026-08-31). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=oh-my-openagent.

17 of the 38 cells have a value. 21 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20network_policy&system=oh-my-openagent&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20replayability&system=oh-my-openagent&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20oh-my-openagent%20%2F%20filesystem_access&system=oh-my-openagent&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 13. daily_stock_analysis (DSA) (`daily-stock-analysis`)

- Repository: <https://github.com/ZhuLinsen/daily_stock_analysis>, pinned v3.31.0 @ `9ab79b82992d688f5c27e7c4c74496138d8a8d79` (2026-08-23)
- Maintained by: a personal account, `ZhuLinsen`; no organization
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/daily-stock-analysis.md`
- Body: 170 words, links excluded

```text
Subject: HARNESS-DB coded daily_stock_analysis (DSA) at v3.31.0: 3 cells you can settle in two minutes

Hello ZhuLinsen,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded daily_stock_analysis (DSA) at v3.31.0 (commit 9ab79b82992d, 2026-08-23). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=daily-stock-analysis.

21 of the 38 cells have a value. 17 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20network_policy&system=daily-stock-analysis&dimension=G3%20network_policy&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20filesystem_access&system=daily-stock-analysis&dimension=G2%20filesystem_access&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20daily-stock-analysis%20%2F%20rollback&system=daily-stock-analysis&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 14. Strix (`strix`)

- Repository: <https://github.com/usestrix/strix>, pinned v1.5.3 @ `7cc9fa9faa0179fc7e35111102fe3d20a9028393` (2026-08-10)
- Maintained by: GitHub org `usestrix` (profile name "Strix")
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/strix.md` (1 cell `unresolved`)
- Body: 170 words, links excluded

```text
Subject: HARNESS-DB coded Strix at v1.5.3: 3 cells you can settle in two minutes

Hello Strix team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Strix at v1.5.3 (commit 7cc9fa9faa01, 2026-08-10). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=strix.

31 of the 38 cells have a value. 6 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20replayability&system=strix&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20rollback&system=strix&dimension=E3%20rollback&current=not_reported
- state_persistence (D3), on which 86.2% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20strix%20%2F%20state_persistence&system=strix&dimension=D3%20state_persistence&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 15. AutoGen (AssistantAgent + UserProxyAgent) (`autogen`)

- Repository: <https://github.com/microsoft/autogen>, pinned python-v0.7.5 @ `83afbf5857aac683340d4c692194e548b1e8edda` (2025-09-30)
- Maintained by: GitHub org `microsoft` (profile name "Microsoft")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/autogen.md`
- Body: 173 words, links excluded

```text
Subject: HARNESS-DB coded AutoGen (AssistantAgent + UserProxyAgent) at python-v0.7.5: 3 cells you can settle in two minutes

Hello Microsoft team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded AutoGen (AssistantAgent + UserProxyAgent) at python-v0.7.5 (commit 83afbf5857aa, 2025-09-30). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=autogen.

15 of the 38 cells have a value. 23 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20network_policy&system=autogen&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20replayability&system=autogen&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20autogen%20%2F%20filesystem_access&system=autogen&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 16. CrewAI (`crewai`)

- Repository: <https://github.com/crewAIInc/crewAI>, pinned 1.15.18 @ `4bc5d2924218e892bd0bc91b46352b49b0d3a740` (2026-08-27)
- Maintained by: GitHub org `crewAIInc` (profile name "crewAI")
- GitHub Discussions enabled: no
- Card: `docs/launch/cards/crewai.md`
- Body: 170 words, links excluded

```text
Subject: HARNESS-DB coded CrewAI at 1.15.18: 3 cells you can settle in two minutes

Hello crewAI team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded CrewAI at 1.15.18 (commit 4bc5d2924218, 2026-08-27). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=crewai.

14 of the 38 cells have a value. 24 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20network_policy&system=crewai&dimension=G3%20network_policy&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20filesystem_access&system=crewai&dimension=G2%20filesystem_access&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20crewai%20%2F%20rollback&system=crewai&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 17. Cherry Studio (`cherry-studio`)

- Repository: <https://github.com/CherryHQ/cherry-studio>, pinned v2.0.10 @ `3db6b513e4920d829d134a308a4aef157ef5f3aa` (2026-08-28)
- Maintained by: GitHub org `CherryHQ` (profile name "CherryHQ")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/cherry-studio.md`
- Body: 171 words, links excluded

```text
Subject: HARNESS-DB coded Cherry Studio at v2.0.10: 3 cells you can settle in two minutes

Hello CherryHQ team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded Cherry Studio at v2.0.10 (commit 3db6b513e492, 2026-08-28). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=cherry-studio.

7 of the 38 cells have a value. 31 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20network_policy&system=cherry-studio&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20replayability&system=cherry-studio&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20cherry-studio%20%2F%20filesystem_access&system=cherry-studio&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 18. nanobot (`nanobot`)

- Repository: <https://github.com/HKUDS/nanobot>, pinned v0.3.0 @ `3f602fbc8c104b5af27aa4d3520e7dcef2fa70ec` (2026-07-25)
- Maintained by: GitHub org `HKUDS` (profile name "Data Intelligence Lab@HKU")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/nanobot.md`
- Body: 172 words, links excluded

```text
Subject: HARNESS-DB coded nanobot at v0.3.0: 3 cells you can settle in two minutes

Hello Data Intelligence Lab@HKU team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded nanobot at v0.3.0 (commit 3f602fbc8c10, 2026-07-25). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=nanobot.

21 of the 38 cells have a value. 17 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20network_policy&system=nanobot&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20replayability&system=nanobot&dimension=H2%20replayability&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20nanobot%20%2F%20rollback&system=nanobot&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 19. BettaFish (`bettafish`)

- Repository: <https://github.com/666ghj/BettaFish>, pinned v3.0.0 @ `9bb2d32cad111b1eab73297400ef09978b0c5882` (2025-12-22)
- Maintained by: a personal account, `666ghj` (profile name "BaiFu"); no organization
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/bettafish.md` (2 cells `unresolved`)
- Body: 169 words, links excluded

```text
Subject: HARNESS-DB coded BettaFish at v3.0.0: 3 cells you can settle in two minutes

Hello 666ghj,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded BettaFish at v3.0.0 (commit 9bb2d32cad11, 2025-12-22). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=bettafish.

12 of the 38 cells have a value. 24 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20network_policy&system=bettafish&dimension=G3%20network_policy&current=not_reported
- replayability (H2), on which 90.6% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20replayability&system=bettafish&dimension=H2%20replayability&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20bettafish%20%2F%20filesystem_access&system=bettafish&dimension=G2%20filesystem_access&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

### 20. DeepTutor (`deeptutor`)

- Repository: <https://github.com/HKUDS/DeepTutor>, pinned v1.6.2 @ `3dc372f551285ea8ffd552ba01cd5dd16c59cb25` (2026-08-31)
- Maintained by: GitHub org `HKUDS` (profile name "Data Intelligence Lab@HKU")
- GitHub Discussions enabled: yes
- Card: `docs/launch/cards/deeptutor.md`
- Body: 172 words, links excluded

```text
Subject: HARNESS-DB coded DeepTutor at v1.6.2: 3 cells you can settle in two minutes

Hello Data Intelligence Lab@HKU team,

HARNESS-DB is an open dataset (CC BY 4.0) that codes 1,256 agent harnesses on 38 design dimensions, and every value in it has a verbatim quote and a file:line@commit locator. We coded DeepTutor at v1.6.2 (commit 3dc372f55128, 2026-08-31). Its 38 cells are in the attached card and at https://harness-db.github.io/harness-db/#system=deeptutor.

24 of the 38 cells have a value. 14 are not_reported: our coder read the sources it was given and found nothing, which means undocumented, not absent. Three of them are on dimensions you can probably answer in two minutes:

- network_policy (G3), on which 93.3% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20network_policy&system=deeptutor&dimension=G3%20network_policy&current=not_reported
- filesystem_access (G2), on which 87.5% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20filesystem_access&system=deeptutor&dimension=G2%20filesystem_access&current=not_reported
- rollback (E3), on which 86.4% of the field is silent: https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml&title=%5Bwrong%20cell%5D%20deeptutor%20%2F%20rollback&system=deeptutor&dimension=E3%20rollback&current=not_reported

Each link opens a prefilled issue on our repository, not yours. A one-line quote and a file:line settle the cell in the next release, and we credit the correction. If a valued cell is wrong, every row of the card has a fix link.

Paper: https://arxiv.org/abs/[arXiv id]

Thank you,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## Notes

- **MetaGPT** is pinned at v0.8.2 (2025-03-02) and **AutoGen** at python-v0.7.5 (2025-09-30), both
  more than a year old. Ask the maintainers whether a newer release changes any cell. A newer version
  would be a new pinned coding, not an edit to 1.0.0.
- **Codex CLI** is pinned at an alpha tag (`rust-v0.153.0-alpha.2`), which the coder chose as the
  latest tag on 2026-08-31. Say so if they ask.
- **learn-claude-code** is by shareAI, not Anthropic. Do not mention Anthropic in that email.
- The three dimensions repeat across systems (network policy, replayability, filesystem access,
  rollback) because they are the most silent in the field. That is the finding. Do not vary the
  list to make the emails look different.
