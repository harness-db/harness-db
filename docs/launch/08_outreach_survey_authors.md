# Emails to the authors of the seven prior surveys and taxonomies

Drafts. Send them from gurrambhaskar.ai@gmail.com after the arXiv listing is live, in the first batch
(`12_launch_checklist.md`). Every body is 180 words or fewer (counts in brackets, taken with a
whitespace split, excluding the subject and the signature).

Names, affiliations and addresses were verified on 2026-09-30 against each paper's arXiv page or PDF
front matter. **Only addresses printed on a paper are given.** Where none is printed, the To line says so;
do not guess an address. OpenReview and Preprints.org blocked automated fetches, so Li et al. was checked
against the PDF at picrew.github.io/LLM-Harness/main.pdf, and Meng et al. against the v4 PDF on Hugging Face.

The crosswalk is **Table 2 in Section 3** of the paper (`tab:crosswalk`). The tone rule: one true, specific
point from our data per email, framed as something that extends their work. Do not argue with their
scheme, and never write "first".

Attach each recipient's crosswalk row as plain text. If they also name systems, attach cards generated
with `python scripts/system_card.py <id> --out docs/launch/cards/`.

---

## 1. Guo et al. (arXiv:2606.20683)

To: Chang Xu `c.xu@sydney.edu.au`, Yunhe Wang `yunhe.wang@tokenrhythm.ai` (both printed as correspondence
authors). Cc: Jianyuan Guo `jianyguo@cityu.edu.hk`.
Affiliations as printed: University of Sydney (Xu); TokenRhythm Technologies (Wang); City University of
Hong Kong (Guo).

Subject: Your six runtime responsibilities, crosswalked in HARNESS-DB

```text
Dear Chang Xu, Yunhe Wang and Jianyuan Guo,

I am the author of HARNESS-DB (https://arxiv.org/abs/[arXiv id]), a pre-registered review that codes 1,256 agent harnesses on 38 dimensions with a quote behind every value.

Table 2 of the paper maps your six runtime responsibilities onto our nine layers. Your scheme folds budget and termination into control, and has no separate slot for our observability and governance layer.

One result bears on your Section 7. Only 53 of our 1,256 systems (4.2%) share a benchmark, split and base model with a peer. So the same-model leaderboard comparisons you compiled are close to the only place such evidence exists at scale. Within those keys, multi-agent topology reaches +0.88 within-key SD [+0.38, +1.31].

If our mapping of your scheme is wrong, I would be grateful for a correction. I would also welcome help keeping the dataset current, and I can share any subset as a CSV.

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[154 words]

## 2. Rombaut (arXiv:2604.03515)

To: Benjamin Rombaut. **No address or affiliation is printed on the paper.** The arXiv abstract page has a
"view email" link (login required). Use that, or do not send.

Subject: HARNESS-DB adopts your observation / classification / evidence template

```text
Dear Benjamin Rombaut,

Your source-code taxonomy of 13 coding scaffolds is the evidence standard HARNESS-DB follows (https://arxiv.org/abs/[arXiv id]). We adopted your observation, classification and evidence template and several of your value sets, and applied them to documents for 1,256 systems.

Our human audit supports reading source code as you did. A human reading of 350 cells matched our model coder on 57.7%. But 117 of the 148 disagreements were in files the coder's capped evidence bundle never contained. Where it had the evidence, it was right on 202 of 233. Our silence rates are therefore upper bounds.

Table 2 crosswalks your twelve dimensions. The paper states that three of them have no dimension of ours: loop driver, tool discovery strategy and multi-model routing. The last two are touched only partly.

Would you be interested in co-designing a loop-driver dimension for the next schema version, or in correcting how we mapped your scheme?

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[154 words]

## 3. Banu (arXiv:2605.12239)

To: Bogdan Banu `bogdan@banu.be` (printed). No affiliation printed. The paper is marked "Preprint – Feedback
Welcome".

Subject: Model-parametric harnesses, and what 1,256 coded systems can and cannot test

```text
Dear Bogdan Banu,

I read "Harness Engineering as Categorical Architecture" while building HARNESS-DB (https://arxiv.org/abs/[arXiv id]). It codes 1,256 agent harnesses on 38 dimensions, with a verbatim quote behind every value.

Table 2 of our paper maps your (G, Know, Φ) triple onto our nine layers. Φ relates only to model agnosticism (M3), and we say in the paper that our schema has no dimension for multi-model routing.

One number supports your choice of certificates over benchmark runs. Only 53 of our 1,256 systems (4.2%) share a benchmark, split and base model with a peer. So an observational test of whether harness structure is model-parametric has very little data to work with.

Since you invite feedback, I would welcome yours on our mapping. I would also like to discuss whether a routing dimension, built on Φ, belongs in the next schema version.

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[143 words]

## 4. Li et al., "Agent Harness Engineering: A Survey" (OpenReview eONq7FdiHa)

To: Chandan K. Reddy `reddy@cs.vt.edu` and Tianyang Wang (the correspondence glyph follows both names). Cc:
Junjie Li. **The survey prints no email.** Reddy's address is printed on a different paper he co-authored,
Zhang et al., arXiv:2605.23950. **No address was found for Tianyang Wang or Junjie Li**, so leave them off
unless you find one printed.
Affiliations as printed: Virginia Tech (Reddy); UAB (Wang); CMU and UAB (Li).
Coordination: Reddy is also senior author of the disclosure paper in `10_outreach_researchers.md` (#4).
Send this email first, and send #4 to Yunbei Zhang only, a week later.

Subject: ETCLOVG crosswalked against 1,256 coded harnesses

```text
Dear Chandan K. Reddy and Tianyang Wang,

HARNESS-DB (https://arxiv.org/abs/[arXiv id]) codes 1,256 agent harnesses on 38 dimensions, with a verbatim quote behind every value. Table 2 of our paper maps our nine layers onto ETCLOVG. Our unit is an agent system, while yours also admits sandboxes, tracers and benchmarks, and the paper says so.

One result sits beside your Section 2.9, which finds observability and governance thinnest in open-source coverage. Inside system documentation, the thinnest layer we find is the one matching your Execution environment. Weighted to the field, our sandbox layer is 81.6% silent, against 24.9% for the control loop. These are upper bounds.

The position paper "Stop Comparing LLM Agents Without Disclosing the Harness", which Chandan co-authored, argues for disclosure from outcomes. Our 48.9% silent cells measure how much is not disclosed.

Would you correct our mapping of ETCLOVG where it is wrong? I would also welcome a joint look at which of your catalogue entries are in our release.

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[164 words]

## 5. Meng et al., "Agent Harness for Large Language Model Agents: A Survey" (Preprints.org 202604.0428)

To: the addresses printed on the v4 PDF, `liyichencly@gmail.com` and `gloriamenng@gmail.com`. Liyi Chen is
the printed corresponding author and Qianyu Meng the first author. The PDF prints the addresses without
saying whose each one is, so do not write "your address" to either person.
Affiliations as printed: Xiaohongshu Inc. (Chen; Meng); Minzu University of China (Meng).
Send before opening the awesome-list PR to their catalogue (`06`, #6).

Subject: A "not documented" state for the Harness Completeness Matrix

```text
Dear Liyi Chen, Qianyu Meng and colleagues,

Your H = (E, T, C, S, L, V) definition is one of the seven schemes HARNESS-DB crosswalks (https://arxiv.org/abs/[arXiv id], Table 2). HARNESS-DB codes 1,256 agent harnesses on 38 dimensions, with a verbatim quote behind every value.

One result may be useful for the Harness Completeness Matrix. Our cells have three states: a value with evidence, not_reported, and unresolved. 48.9% of all cells are not_reported, meaning the sources were read and are silent. In a check / partial / cross matrix, those cells have to become a cross or a partial. The layer you treat as a cross-cutting challenge, sandboxing, is 81.6% silent when weighted to the field.

Several systems your survey discusses, for example Claude Code, OpenHands and AIOS, are in our release at pinned versions. I would be glad to send their cells with quotes, and to hear where our mapping of your tuple is wrong.

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[157 words]

## 6. Barbaste et al. (arXiv:2609.00006)

To: Paul Barbaste (printed as "Lead and corresponding author"). **No email is printed.** Find his address
on the Inclusive Brains or Wavestone AI Lab site, or on the arXiv "view email" link. Do not guess.
Affiliations as printed: Inclusive Brains and Wavestone AI Lab (Barbaste); Wavestone AI Lab (Darrigol, Vu,
Wiltberger).

Subject: Your eleven harnesses, and our silent cells for them

```text
Dear Paul Barbaste,

HARNESS-DB (https://arxiv.org/abs/[arXiv id]) codes 1,256 agent harnesses on 38 dimensions, with a verbatim quote behind every value. Table 2 of our paper adds your seven subsystems to the crosswalk, mapped after our schema froze.

These systems from your study are in our release at pinned commits: Claude Code, Codex CLI, Gemini CLI, Mistral Vibe, OpenHands, Aider, mini-swe-agent, Hermes Agent, Pi, OpenCode and Omnigent. Our coder read documents, not code, and it shows. Mistral Vibe has 35 of 38 cells valued, while Aider and Pi have 9 each; the rest are not_reported. A human audit found most of our misses in files the coder never saw, so these silence rates are upper bounds.

Your source reading could settle many of those cells. Would you look at the attached cards and tell us where we are wrong? We would credit every correction.

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[145 words]

Attach cards: `python scripts/system_card.py <id> --out docs/launch/cards/` for `claude-code`, `codex-cli`,
`gemini-cli`, `mistral-vibe`, `openhands`, `aider`, `mini-swe-agent`, `hermes-agent`, `pi-coding-agent`,
`opencode` and `omnigent`. Five of these (Claude Code, Codex CLI, OpenHands, Hermes Agent, Pi) are among the top-20 cards already generated; render the other six on the day. The valued
counts quoted above come from those cards (release 1.0.0): Mistral Vibe 35, Aider 9, Pi 9. Our release has
no system called OpenClaw; `openclaw-net` and `clawteam-openclaw` are different projects.

## 7. Zhong and Zhu (arXiv:2605.13357)

To: Shengxin Zhu `shengxin.zhu@bnu.edu.cn` (printed; corresponding). Cc: Hailin Zhong (no address printed).
Affiliations as printed: Hong Kong Baptist University (Zhong); Beijing Normal University, Zhuhai (Zhu; the
paper prints "Beijin").

Subject: Your H0–H3 ladder is the kind of evidence our ablation pool lacks

```text
Dear Shengxin Zhu and Hailin Zhong,

HARNESS-DB (https://arxiv.org/abs/[arXiv id]) codes 1,256 agent harnesses on 38 dimensions and pools authors' own published ablations by design dimension. Table 2 of our paper crosswalks your eleven responsibilities, mapped after our schema froze. You fold permission model, guardrails and approval gates into one permission boundary. Four of your responsibilities have no dimension of ours: task interface, failure attribution, entropy auditor and intervention logger.

One result makes your cumulative ladder valuable. Across the literature, authors' ablations barely separate design dimensions. 14 of 22 poolable dimensions pass a publication-bias discount, with relative gains of +0.114 to +0.259 before a median discount of 49.8%. 7 design dimensions carry no ablation at all. Controlled ladders like H0–H3 are the missing evidence.

Would you consider running the ladder on more tasks, with our dimensions as the unit? I would gladly help with a joint analysis.

Data: https://github.com/harness-db/harness-db

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
```

[148 words]
