# HARNESS-DB launch and outreach kit

Drafts and tools for the day the arXiv preprint posts. **Nothing in this directory has been sent,
posted or submitted.** Every step is done by the author, by hand, in the order given in
`12_launch_checklist.md`.

## Files

| File | What it is |
|---|---|
| `01_x_thread.md` | An 8-post X thread, with character counts (raw and X-weighted) and alt text for the one image |
| `02_linkedin.md` | One LinkedIn post, 211 words, 4 hashtags |
| `03_show_hn.md` | Show HN title (80 characters), URL, first comment, and prepared answers |
| `04_reddit.md` | r/MachineLearning `[R]` post and a shorter r/LocalLLaMA variant, as outlines to rewrite |
| `05_hf_paper_page.md` | Hugging Face Papers: index, claim, link the dataset, and the first Community post |
| `06_awesome_lists.md` | Nine verified awesome-lists: the section, the exact line, and the PR title and body for each |
| `07_papers_with_code.md` | What replaced Papers with Code, and the steps that work now |
| `08_outreach_survey_authors.md` | Seven emails, one to each prior survey or taxonomy |
| `09_outreach_system_maintainers.md` | A template and 20 filled emails to the maintainers of the highest-starred coded systems |
| `10_outreach_researchers.md` | Ten emails to authors of harness-effect work the paper cites |
| `11_press_and_newsletters.md` | Eight outlets, how each takes tips, and a short pitch for each |
| `12_launch_checklist.md` | Pre-flight, launch-day order, email batches, and the daily metrics with `gh` and `curl` commands |
| `cards/` | Cell cards for the 20 highest-starred coded systems, plus `cards/README.md`, the index |

The cards are generated, not written by hand. Regenerate them after any data change:

```sh
python scripts/system_card.py --top 20 --by stars --out docs/launch/cards/
python scripts/system_card.py <system_id> --out docs/launch/cards/     # any other system, on demand
```

## The rules

1. **Never claim "first".** Seven prior surveys and taxonomies structure the agent harness
   (`docs/positioning.md`; paper Section 3, Table 2). HARNESS-DB differs from them in a specific way:
   it is pre-registered, its matrix has depth, breadth and evidence, its outcome analysis runs on coded
   dimensions, and it crosswalks the seven schemes. Say that instead. Do not write "first", "largest",
   "only", "definitive" or "state of the art" in anything you send.
2. **Every number must be traceable.** Use only numbers that appear in `paper/sections/00_abstract.tex` or
   `docs/count_reconciliation.md`, or that `scripts/system_card.py` renders from `data/systems.json` (a
   system's own cell counts, and the per-dimension field silence rates taken from
   `data/analysis/summary_one_screen.csv`). One number used in the kit is derived rather than printed in the
   abstract: 86.7%, which is 202 of 233, from `paper/sections/04_methodology.tex`. The table below lists
   every number the kit uses.
3. **Always pair the audit's two numbers.** If you quote 86.7% (202 of 233, the cells whose evidence the
   coder received), also say that the overall agreement on 350 cells was 57.7%, and that silence rates are
   upper bounds.
4. **Silence is not absence.** `not_reported` means the sources were read and are silent. Never write "81.6%
   of harnesses have no sandbox"; the rate is a share of cells, weighted to the field, and an upper bound.
5. **A wrong-cell report is a gift.** Thank the reporter, re-open the locator, and either queue the fix for
   the next versioned release or reply with the reason the cell stands. Credit accepted corrections.
   Released versions are never edited in place.
6. **Respond within 48 hours** to every wrong-cell issue, Hugging Face Community post, email reply and
   public correction.
7. **Write public posts and pitches in your own words.** These drafts were written with an AI assistant.
   r/LocalLLaMA bans primarily LLM-generated posts, and press platforms screen for them. Keep the facts and
   rewrite the prose. Any quote attributed to you must be something you actually said or wrote. Never
   fabricate a quote from anyone.
8. **Use only printed contact details.** Every email address in `08`–`10` is printed on the recipient's
   paper, or on the outlet's own page for `11`. Where none is printed, the draft says so. Do not guess
   addresses, and do not email company employees at guessed addresses.
9. **No emojis,** except at most one, in the first X post. (Two awesome-lists require their own marker
   emoji in the entry line; `06` notes where.)
10. **Placeholders.** `[arXiv id]` appears throughout. Replace every instance on launch day
    (`grep -rn "\[arXiv id\]" docs/launch`).

## Numbers used in this kit, and where each one comes from

| Number | Meaning | Source |
|---|---|---|
| 1,256 / 38 / 9 / 47,728 | systems, dimensions, layers, cells | abstract; count_reconciliation |
| 6,504 | sampling frame | abstract; count_reconciliation |
| 48.9% (23,337) | cells `not_reported` | abstract; count_reconciliation |
| 50.8% (24,228) / 0.3% (163) | valued / `unresolved` cells | count_reconciliation |
| 24.9% ± 1.2 / 81.6% ± 1.8 | field-weighted silence, control loop / sandbox | abstract |
| 69.2% of 1,252 to 33.3% | repository-primary share, unweighted to weighted | abstract |
| 265 of 666 | pairs associated only when silence counts as a category | abstract |
| 53 of 1,256 (4.2%) | systems sharing a benchmark, split and base model with a peer | abstract |
| +0.88 [+0.38, +1.31] | multi-agent topology, within-key SD | abstract |
| 14 of 22; +0.114 to +0.259; 49.8%; 7 | ablation dimensions passing the bias discount; pooled relative gains; median discount; dimensions with no ablation | abstract (macros in `paper/tables/rq3_macros.tex`) |
| κ 0.784; 247 | mean per-dimension kappa; double-coded systems | abstract; count_reconciliation |
| 350; 57.7% [48.6, 66.9]; 41–63%; 117 of 148 | human audit: cells, agreement, share of silent cells confirmed, disagreements outside the evidence bundle | abstract |
| 202 of 233 (86.7%) | coder correct where it had the evidence | `paper/sections/04_methodology.tex` |
| 5,863 | reported benchmark scores in `data/results.csv` | `README.md`, `DATASET_CARD.md` |
| per-system counts, per-dimension silence rates | e.g. Claude Code 16 of 38 valued; `network_policy` 93.3% | `scripts/system_card.py` from `data/systems.json` and `data/analysis/summary_one_screen.csv` |

## Facts to use verbatim

- GitHub: `harness-db/harness-db` (public)
- Explorer: <https://harness-db.github.io/harness-db/>, and `#system=<id>` for one system
- Hugging Face: `bhaskar-ai/harness-db` (configs `cells` and `systems`, split `train`)
- Zenodo concept DOI: `10.5281/zenodo.23031354` (v1.0.0: `10.5281/zenodo.23031355`)
- Pre-registration: `osf.io/ab2wn`
- Author: Bhaskar Gurram, gurrambhaskar.ai@gmail.com
- Paper: *The Anatomy of Agent Harnesses: A Systematic Review, Unified Taxonomy, and Coded Dataset
  (HARNESS-DB) of LLM Agent Scaffolding, 2022–2026*, arXiv `[arXiv id]`
- Licences: data CC BY 4.0, code MIT
