# Hugging Face: paper page, dataset link, first Community post

Sources, read 2026-09-30: the Paper Pages docs (<https://huggingface.co/docs/hub/paper-pages>), Hugging
Face's own `huggingface-papers` skill file
(<https://github.com/huggingface/skills/blob/main/skills/huggingface-papers/SKILL.md>, last commit
2026-03-23), and the HF blog guide to the Papers page
(<https://huggingface.co/blog/AdinaY/a-guide-to-hugging-faces-papers-page>, 2025-11-25). Anything marked
**unverified** below was not in the formal docs.

State on 2026-09-30: the dataset `bhaskar-ai/harness-db` is public, with configs `cells` (default) and
`systems`, each a `train` split (checked with the datasets-server `/splits` API). Its card does not yet
carry an arXiv link.

## Steps (do them in this order, on a weekday)

1. **Index the paper.** When the arXiv listing is live, open `https://huggingface.co/papers/[arXiv id]`.
   If the page does not exist, search the arXiv id on <https://huggingface.co/papers> and choose the
   option to index it. (Docs: "If the paper does not exist, you will get an option to index it.")
   Putting the arXiv URL in the dataset card (step 3) also indexes it automatically.
2. **Claim authorship.** Add the email printed on the arXiv paper (gurrambhaskar.ai@gmail.com) to the HF
   account `bhaskar-ai` first, so the automatic match can work. If the paper is still not linked, click
   your name on the paper page, then "claim authorship", and confirm in your paper settings. The admin
   team validates the claim; the page then shows as verified. Visibility on your profile:
   <https://huggingface.co/settings/papers>, "Show on profile".
3. **Link the dataset.** Edit `README.md` of `bhaskar-ai/harness-db` (and `DATASET_CARD.md` in the GitHub
   repository, which is the same text): replace "arXiv identifier to be added at release" with
   `https://arxiv.org/abs/[arXiv id]`. The Hub extracts the id into an `arxiv:[arXiv id]` tag and lists the
   dataset on the paper page. Check it worked:
   `curl "https://huggingface.co/api/datasets?filter=arxiv:[arXiv id]"` should return `bhaskar-ai/harness-db`.
4. **Link GitHub and the project page.** On the claimed paper page, set the GitHub repository to
   `https://github.com/harness-db/harness-db` and the project page to
   `https://harness-db.github.io/harness-db/`. The skill file documents this as
   `POST /api/papers/{paperId}/links` with `githubRepo` and `projectPage`, allowed for the paper author,
   the Daily Papers submitter, or a papers admin. **Unverified:** the label of the button in the web UI.
   A linked GitHub repository is what makes a paper eligible for Trending Papers
   (<https://huggingface.co/papers/trending>), which is where paperswithcode.com now redirects.
5. **Submit to Daily Papers** at <https://huggingface.co/papers/submit> (login required). Per the skill
   file and a May 2025 forum thread, submission is open for **14 days after arXiv v1**, only to users who
   have claimed a paper. **Unverified, from a January 2025 GitHub issue:** no weekend submissions, a
   per-day limit for regular users, and a paper can be submitted once.
6. **Post the first Community discussion** on the dataset (text below), then pin it.

## First Community post on `bhaskar-ai/harness-db` (Discussions tab)

Title:

```text
Start here: what a cell is, what not_reported means, and how to report a wrong cell
```

Body:

```markdown
HARNESS-DB codes 1,256 LLM agent harnesses on 38 design dimensions: 47,728 cells. It is the dataset behind
the paper at https://arxiv.org/abs/[arXiv id] (pre-registered at osf.io/ab2wn).

**Load it**

    from datasets import load_dataset
    cells = load_dataset("bhaskar-ai/harness-db", "cells", split="train")      # one row per system x dimension
    systems = load_dataset("bhaskar-ai/harness-db", "systems", split="train")  # one row per system, with stratum and weight

**Three states, and two rules**

- A value carries `evidence_quote` (verbatim) and `evidence_locator` (`path:line@commit` or a paper section).
- `not_reported` (48.9% of cells): the sources were read and are silent. Undocumented, not absent. Never recode it as a value.
- `unresolved` (0.3%): failed validation at release; claims nothing and is excluded from every rate.
- For claims about the field, use the `weight` column: the systems were drawn by stratum from a 6,504-system frame, and the 23 systems coded outside the draw carry weight 0.

**Known limits.** The coders were language-model instances. A human reading of 350 cells matched them on 57.7%; 117 of the 148 disagreements were in files the coder was never sent. Silence rates are upper bounds.

**Found a wrong cell?** Open a wrong-cell issue on GitHub with the quote and locator:
https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml
Or reply here. Every report gets an answer within 48 hours: a fix in the next release, or the reason the cell stands.

Browse and filter: https://harness-db.github.io/harness-db/
```

## After launch

- Reply to every Community post within 48 hours.
- If you have HF PRO, a Hugging Face blog article announcing the dataset is allowed ("Announce the release
  of an open source artifact, such as a model, dataset, or tool", <https://huggingface.co/docs/hub/en/blog-articles>);
  an article by the repo owner that mentions the dataset appears in the dataset's sidebar. Without PRO or
  a Team/Enterprise org, this route is closed.
