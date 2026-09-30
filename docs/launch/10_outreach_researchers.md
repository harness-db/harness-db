# Emails to ten researchers whose work HARNESS-DB builds on

Drafts. Send them in the second batch, after the survey authors (`08`). Each paper below is cited in
`paper/sections/03_related_surveys_crosswalk.tex` (and, for SWE-agent, in sections 2 and 5), with its
bib entry in `paper/references/must_cite.bib`. Names, affiliations and addresses were checked on
2026-09-30 against the arXiv abstract pages and PDF front matter. **Only addresses printed on the paper
are given.** Where none is printed, the To line says so; do not guess one.

Each email gives one specific reason the dataset helps the recipient's next paper, and offers one
concrete thing: the loader, the MCP server, cells for the systems they studied, or a joint analysis.
"In our release" means present in `data/systems.json` 1.0.0. The valued counts are taken from the cell
cards (`python scripts/system_card.py <id>`).

Before sending, check two author overlaps:

- **#4 shares Chandan K. Reddy with Li et al.** Send the Li et al. email in `08` (#4) first.
- **#5 shares Yunhe Wang, Kai Han and Mengyu Zheng with Guo et al.** Send the Guo et al. email in `08`
  (#1) first, and mention it here.

---

## 1. Harness-Bench (`harnessbench2026`, arXiv:2605.27922)

To: Yilun Yao (co-first) and Tong Yang (last author), Peking University. **No email is printed.** Use the
arXiv "view email" link, or skip.

Subject: Your six harnesses, coded on 38 design dimensions

```text
Dear Yilun Yao and Tong Yang,

Harness-Bench crosses 6 harnesses with 8 models on 106 tasks. It shows that the harness matters, and it names which harness. HARNESS-DB (https://arxiv.org/abs/[arXiv id]) can help attribute that effect to design choices. Four of your harnesses, Hermes Agent, Moltis, nanobot and ZeroClaw, are in our release at pinned commits. Each is coded on 38 dimensions with a verbatim quote behind every value.

Joined to your trajectories, those cells would let a follow-up ask which dimension moves completion or cost, rather than which harness. Our own cross-paper data cannot do this well. Only 53 of 1,256 systems share a benchmark, split and base model with a peer.

I can send the four systems' cells as CSV, or set up the MCP server so an agent can query them. I would gladly help with a joint analysis.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 2. The Scaffold Effect in Coding Agents (`scaffoldeffect2026`, arXiv:2607.22585)

To: Naman Vats `naman@sentient.xyz`, Oleg Golev `oleg@sentient.xyz` (printed as `{naman, oleg}@sentient.xyz`,
"Correspondence to"). Sentient Labs.

Subject: The 40x token gap, and where the three scaffolds differ in design

```text
Dear Naman Vats and Oleg Golev,

You found tokens per solved task differing by up to 40x across Goose, OpenCode and OpenHands-SDK, while pass rates moved by 0 to 8 points. HARNESS-DB (https://arxiv.org/abs/[arXiv id]) codes Goose, OpenCode and two OpenHands entries on 38 design dimensions, including context compaction, cost controls and timeouts, with a verbatim quote behind every value. That gives your next paper candidate mechanisms for the token gap.

We record gaps honestly. Goose has only 8 of 38 cells valued in our release, so its compaction and budget cells are silent. You have run these scaffolds, so you may be able to settle those cells from source, and we would credit that.

I can send the three systems' cells, or the MCP server so your agents can query the dataset directly.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 3. Same Model, Different Harness (`samemodel2026harness`, arXiv:2608.26218)

To: Sydney Lewis. **No affiliation or email is printed.** The paper's only contact point is the code
repository `github.com/sydches/yuj`. Use a Discussion or the profile there if one is public; do not open an
issue.

Subject: Context compaction and stall handling across 1,256 harnesses

```text
Dear Sydney Lewis,

Your treatment shortens older tool results and responds to stalled work. On 169 SWE-bench Verified tasks it raised mean fail-to-pass from 28% to 49%. Those two mechanisms are two of HARNESS-DB's 38 dimensions, context compaction and termination condition (https://arxiv.org/abs/[arXiv id]).

The dataset shows how other harnesses set them, with a quote for each value. So a follow-up could test your treatment against configurations that the field actually ships. It also shows how rarely the choice is documented, and our paper reports how weakly published ablations separate one dimension from another.

If it helps, I can send the systems that use each compaction strategy, with their pinned commits, as a CSV.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 4. Stop Comparing LLM Agents Without Disclosing the Harness (`zhang2026harnessreporting`, arXiv:2605.23950)

To: Yunbei Zhang `yzhang111@tulane.edu` (printed). Tulane University. Send a week after the Li et al. email,
which goes to Chandan K. Reddy.

Subject: Measuring the disclosure gap you describe

```text
Dear Yunbei Zhang,

Your position paper argues that agent comparisons must disclose the harness. HARNESS-DB (https://arxiv.org/abs/[arXiv id]) measures how much is disclosed today. It codes 1,256 harnesses on 38 dimensions, and 48.9% of the 47,728 cells are documented silence: the sources were read and do not say. Weighted to the field, silence ranges from 24.9% for the control loop to 81.6% for the sandbox.

For your next paper, the per-dimension silence rates could rank which fields of a disclosure standard matter most, because they are the ones authors leave out. The 38 dimensions could also serve as a candidate checklist.

Would you like to work on this together? I can share the per-dimension rates with their design standard errors.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 5. Claw-SWE-Bench (`clawswebench2026`, arXiv:2606.12344)

To: Mengyu Zheng `mengyu.zheng@tokenrhythm.ai` (first author, TokenRhythm Technologies) and Yu Wang
`yu-wang@mail.tsinghua.edu.cn` (last author, Tsinghua University). Both addresses are printed. Send after the
Guo et al. email.

Subject: Attributing Claw-SWE-Bench's harness spread to design dimensions

```text
Dear Mengyu Zheng and Yu Wang,

Claw-SWE-Bench holds the model fixed and swaps seven harnesses, and our paper cites its spread of up to 27.4 points in Pass@1. HARNESS-DB (https://arxiv.org/abs/[arXiv id]) has four of those harnesses coded at pinned commits: Hermes Agent, nanobot, ZeroClaw and Meta-Harness. Each is coded on 38 design dimensions, with a quote behind every value.

For a next version of the benchmark, joining our cells to your 21 model-harness pairs would let you ask which design choice carries the spread, and not only which harness does. I have also written to your co-authors about the Guo et al. survey, which our paper crosswalks.

I can send those systems' cells, or help with the join directly.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 6. icat-agent (`icatagent2026`, arXiv:2606.25514)

To: Yang Chen (first author) and Reyhaneh Jabbarvand (last author), University of Illinois Urbana-Champaign.
**No personal email is printed** (only the ACM permissions boilerplate). Use the arXiv "view email" link or
the authors' university pages.

Subject: Multi-agent scaffolding is where our cross-paper signal is strongest

```text
Dear Yang Chen and Reyhaneh Jabbarvand,

icat-agent beats SWE-agent, mini-SWE-agent and Claude Code with the same backbones. All three baselines are coded in HARNESS-DB (https://arxiv.org/abs/[arXiv id]) at pinned commits, on 38 design dimensions with a quote behind every value.

Your result matches the strongest signal in our outcome data. Within benchmark-split-model keys, multi-agent topology reaches +0.88 within-key standard deviations [+0.38, +1.31]. The keys are few, though: only 53 of 1,256 systems share one with a peer. Controlled comparisons like yours are what that estimate needs.

Would you be willing to have icat-agent coded? You could also check our cells for your three baselines. Either way, a short joint analysis of multi-agent designs across our comparable set might interest you.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 7. Self-Harness (`selfharness2026`, arXiv:2606.09498)

To: Shuyue Hu `hushuyue@pjlab.org.cn` (corresponding) and Hangfan Zhang `zhanghangfan@pjlab.org.cn` (first
author). Both are printed as `{zhanghangfan,zhangshao,hushuyue}@pjlab.org.cn`. Lei Bai is also corresponding,
but no address is printed for him. Shanghai Artificial Intelligence Laboratory.

Subject: A design space for harnesses that edit themselves

```text
Dear Shuyue Hu and Hangfan Zhang,

Self-Harness improves held-in and held-out pass rates in all nine model-benchmark cells. That raises a question our data can help with: which design dimensions do the self-edits change?

HARNESS-DB (https://arxiv.org/abs/[arXiv id]) codes 1,256 harnesses on 38 dimensions, with a verbatim quote behind every value. Coding your initial and final harnesses on the same dimensions would place each edit in that design space. It would also show whether the edits move toward what the field ships or away from it.

We have an MCP server, so a self-editing agent could look up how other harnesses set a dimension before changing its own. I would be glad to set it up with you, or to code your harnesses for a joint note.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 8. One Recipe, Many Harnesses (`onerecipe2026harnesses`, arXiv:2608.10178)

To: Siqi Yang `siqiyang@illinois.edu` (first and corresponding author, University of Illinois
Urbana-Champaign). Cc: Martin Hirzel (IBM; no address printed).

Subject: Mapping your harness edits to a shared set of design dimensions

```text
Dear Siqi Yang,

Your paper traces every harness edit back to the failure signal that caused it, across 8 languages and 3 base models. Mapped onto a shared set of design dimensions, those edits could be compared with other work.

HARNESS-DB (https://arxiv.org/abs/[arXiv id]) offers such a set: 38 dimensions in nine layers, each value backed by a quote. mini-swe-agent, your comparison point, is in our release at a pinned commit. Labelling your edits with our dimensions would show which layers self-evolution changes. Our pooled author ablations cannot show that, because they barely separate one dimension from another.

Would you be interested in a joint analysis? I can provide the schema, the coding manual and the loader.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 9. Dissecting model behavior through agent trajectories (`intentexecution2026`, arXiv:2606.17454)

To: Gaurav Gupta `gauravaz@amazon.com` (first author) and Anoop Deoras `adeoras@amazon.com` (last author).
Both are printed as `{gauravaz, vatshc, lukehuan, adeoras}@amazon.com`. AWS AI Labs.

Subject: The harness side of your 138k trajectories

```text
Dear Gaurav Gupta and Anoop Deoras,

You held one customizable harness fixed across five model families and analysed 138k trajectories. For the next step, the model side of that design needs a harness side to vary. HARNESS-DB (https://arxiv.org/abs/[arXiv id]) codes 1,256 harnesses on 38 dimensions, with a verbatim quote behind every value. Strands Agents is in our release.

Our cells could pick harness configurations that differ on one dimension at a time, such as edit primitive, context compaction or termination condition. Your trajectory analysis could then separate model behaviour from harness behaviour on each one.

I can send the Strands Agents cells, since 15 of its 38 are valued and you could settle the rest. I can also share the loader or MCP server to choose contrasts.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

## 10. SWE-agent (`yang2024sweagent`, arXiv:2405.15793)

To: John Yang `johnby@stanford.edu` and Carlos E. Jimenez `carlosej@princeton.edu` (printed, "Correspondence
to"). Cc: Ofir Press (no address printed). Princeton Language and Intelligence, Princeton University (as
printed on v3).

Subject: SWE-agent's ACI choices are the cells our coder could not see

```text
Dear John Yang and Carlos Jimenez,

Your agent-computer interface paper is cited throughout ours, and SWE-agent v1.1.0 is in HARNESS-DB (https://arxiv.org/abs/[arXiv id]) with 17 of 38 cells valued. The 21 silent cells include tool count and edit primitive, which are exactly the ACI choices your paper ablated. Our coder never saw config/default.yaml or the tool configs, so those cells record silence rather than your design.

A human audit found that most of our coder's misses were files like these. The silence rates in the paper are upper bounds for that reason.

Could one of you settle those cells from the pinned commit? The attached card links each one, and mini-swe-agent's is ready too. For your next benchmark work, the dataset and MCP server are yours to use.

With thanks,
Bhaskar Gurram
gurrambhaskar.ai@gmail.com
https://github.com/harness-db/harness-db
```

Attach `docs/launch/cards/swe-agent.md`. Generate it with
`python scripts/system_card.py swe-agent --out docs/launch/cards/`, and do the same for `mini-swe-agent`.
The coder notes quoted in the email are the release's own `note` fields for `tool_count` ("config/default.yaml
contents are not in the bundle.") and `edit_primitive` ("Tool config files are listed but not included in the
bundle.").

---

Alternate, if one of the ten cannot be reached: `efc2026scaling` (arXiv:2605.29682, "Effective Feedback
Compute"), corresponding author Wanxiang Che, Harbin Institute of Technology. The printed addresses are
`{xuanliangzhang, dzrwang, kyxu, qfzhu, car}@ir.hit.edu.cn`. It is cited in Section 7.
