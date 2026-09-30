# Newsletters and blogs that cover agent tooling

Checked 2026-09-30. Each outlet below had published in September 2026. Contact channels are the ones each
outlet prints publicly; where none is printed, the entry says so. Do not look for, or guess, a private
address.

## Read this first: quotes and wording

- **Every quote attributed to the author must be the author's own words.** Speak or write it yourself.
  Do not paste a quote that an assistant drafted, and never invent a quote for anyone else.
- The three-sentence pitches below are **fact sheets written with an AI assistant**. Rewrite each one in
  your own voice before sending. Some outlets and pitch platforms screen for machine-written text, and a
  pitch that reads as generated will be discarded.
- Numbers are fixed. Any number you add must come from the abstract or `docs/count_reconciliation.md`.
  Never write "first".
- Send one pitch per outlet, once. If there is no reply, do not follow up more than once, and not before a
  week has passed.

---

## 1. Latent Space and AINews (swyx and team)

- **URL:** <https://www.latent.space>
- **Active:** AINews issue on 2026-09-30; "Claude Code's Next Era" on 2026-09-29.
- **Fit:** the about page lists "benchmarks, datasets" and "agents, coding tools" among its focus areas. It
  also runs a weekly LLM Paper Club.
- **How to pitch:** "News tips and pitches: tips@latent.space" (about page). There is also a "Write for us!"
  form.

Pitch:

> HARNESS-DB is an open dataset that codes 1,256 LLM agent harnesses, including Claude Code, Codex CLI,
> OpenHands and Hermes Agent, on 38 design dimensions, with a verbatim quote and locator behind every
> value. 48.9% of the 47,728 cells are documented silence, and the sandbox layer is the least documented at
> 81.6% (field-weighted, an upper bound). It could suit AINews or the Paper Club; the explorer needs no
> login: https://harness-db.github.io/harness-db/.

## 2. Import AI (Jack Clark)

- **URL:** <https://importai.substack.com>
- **Active:** issue #474 on 2026-09-28.
- **Fit:** a weekly research digest that often covers agent papers and datasets.
- **How to pitch:** the about page prints the address as "[firstname] at jack-clark dot net"; he is also
  @jackclarkSF. No tip instructions are given, so keep it to one short email.

Pitch:

> A pre-registered systematic review coded 1,256 agent harnesses on 38 design dimensions and found that
> the layers governing safe deployment are the least documented: 81.6% of sandbox cells are silent, against
> 24.9% for the control loop. It also finds that authors' own ablations barely separate design choices:
> 14 of 22 poolable dimensions survive a publication-bias discount, and 7 carry no ablation at all. Paper:
> https://arxiv.org/abs/[arXiv id]; data: https://github.com/harness-db/harness-db.

## 3. Interconnects (Nathan Lambert, Ai2)

- **URL:** <https://www.interconnects.ai>
- **Active:** post on 2026-09-22; "Open-Source AI & Open Models Reading List" on 2026-09-11.
- **Fit:** open models, open artifacts and reading lists.
- **How to pitch:** "mail at interconnects.ai" is printed for partnerships, and guest posts should be sent
  as a completed draft. **There is no news-tip line.** Use this address only for the reading-list angle, and
  say so in the subject.

Pitch:

> For the open-models reading list: HARNESS-DB is a CC BY 4.0 dataset of 1,256 agent harnesses coded on
> 38 design dimensions, and every value can be checked against its quote and locator. It shows how little
> of harness design is written down (48.9% of cells are silent), which matters for anyone comparing open
> models inside different harnesses. Data and loader: https://github.com/harness-db/harness-db.

## 4. AlphaSignal (editorial lead Ben Dickson)

- **URL:** <https://alphasignal.ai>
- **Active:** items posted on 2026-09-30.
- **Fit:** papers, repositories and agents.
- **How to pitch:** "Reach the newsroom directly for editorial questions, tips, and corrections" at
  editorial@alphasignal.ai (<https://alphasignal.ai/editorial-team>).

Pitch:

> New open dataset and paper: HARNESS-DB codes 1,256 agent harnesses on 38 design dimensions, with a quote
> and a file:line@commit behind every value, and ships a Python loader, an MCP server and a web explorer.
> Half its cells (48.9%) are documented silence. A human audit found the coder right on 202 of 233 cells
> where it had the evidence, so the silence rates are upper bounds. Repo:
> https://github.com/harness-db/harness-db; paper: https://arxiv.org/abs/[arXiv id].

## 5. The Batch (DeepLearning.AI)

- **URL:** <https://www.deeplearning.ai/the-batch/>
- **Active:** issue 372 on 2026-09-25 ("Running Two Models in One Agent").
- **Fit:** weekly news and research summaries, often about agents.
- **How to pitch:** only the generic contact form at deeplearning.ai/contact. **No tip or pitch address was
  found.** Low priority.

Pitch:

> Researchers coded 1,256 LLM agent harnesses on 38 design dimensions and found 48.9% of the cells
> undocumented, with sandboxing the least described layer (81.6% silent, weighted to the field). Only 53 of
> the 1,256 systems share a benchmark, split and base model with another, which limits how well harness
> designs can be compared on outcomes. The dataset is open (CC BY 4.0) at
> https://github.com/harness-db/harness-db.

## 6. Simon Willison's Weblog

- **URL:** <https://simonwillison.net>
- **Active:** live blog on 2026-09-29.
- **Fit:** heavy coverage of coding agents and agent tooling.
- **How to pitch:** **no public tip channel was found.** The about page lists only Mastodon, Bluesky and X
  (@simonw). Do not DM a pitch. If you share it, reply publicly to a relevant post of his with one line and
  the explorer link, and only when the dataset is on topic.

One-line version, for a public reply:

> Relevant to this: we coded Claude Code, Codex CLI and 1,254 other harnesses on 38 dimensions with a
> quote per value; the explorer links every cell to its source: https://harness-db.github.io/harness-db/

## 7. Ahead of AI (Sebastian Raschka)

- **URL:** <https://magazine.sebastianraschka.com>
- **Active:** post on 2026-09-29.
- **Fit:** LLM research explainers.
- **How to pitch:** the contact page (sebastianraschka.com/contact) says "I can't keep up with DMs right
  now". **Treat it as having no tip channel, and do not pitch.** It is listed only so that it is not pitched
  by mistake.

## 8. Hugging Face blog (self-published article)

- **URL:** <https://huggingface.co/docs/hub/en/blog-articles>
- **Fit:** the allowed content explicitly includes "Announce the release of an open source artifact, such as
  a model, dataset, or tool". An article by the repository owner that mentions the dataset appears in the
  dataset's sidebar.
- **How:** publish at huggingface.co/new-blog. This **requires HF PRO**, or write access in a Team or
  Enterprise org, plus a confirmed email. If the account is not PRO, skip it.
- **Content:** not a pitch. Write the article yourself: what a cell is, the three states, how to load the
  data, the silence findings with their caveats, and how to report a wrong cell.

---

Also checked and not used:

- **TLDR AI:** active, but no public tip channel (`/submit` returns 404).
- **MarkTechPost:** only a "Partner with Us" form, which looks like paid placement (unverified).
- **Last Week in AI:** its latest post date and tip channel were not confirmed.
- **Ben's Bites, The Sequence, LLM Watch:** not checked.
