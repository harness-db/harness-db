# Papers with Code, and what replaced it

Checked 2026-09-30.

## What happened

- **Shutdown.** Meta shut Papers with Code down without notice around 24 July 2025. The date comes from
  secondary sources: Coursera (<https://www.coursera.org/articles/papers-with-code>, updated 2026-07-21) and
  HyperAI (<https://hyper.ai/en/news/42900>).
- **Redirect.** A GitHub issue on the old data repository, dated 2025-08-14, reads "paperswithcode.com now
  redirects to huggingface" (<https://github.com/paperswithcode/paperswithcode-data/issues/116>). On
  2026-09-30, `https://paperswithcode.com` returned HTTP 302 to `https://huggingface.co/papers/trending`.
- **Archive.** The old paper-to-code links survive as a frozen snapshot from July 2025 in the Hugging Face
  org `pwc-archive` (<https://huggingface.co/pwc-archive>). Its card says it "will not be updated", so a
  new paper cannot be added there.
- **Revival site.** paperswithcode.co is a revival built by Hugging Face with Meta AI and the original
  creators (<https://huggingface.co/blog/nielsr/paperswithcode-launch>, 2026-05-24). It takes submissions at
  `paperswithcode.co/submit`, and "AI will automatically enrich it with task and method tags, the GitHub
  repo, evals, and more". **On 2026-09-30 both `paperswithcode.co` and `/submit` returned HTTP 500.**
  Check again on launch day.

So there is no single "add dataset + paper" form any more. The current equivalent has two parts:

1. **Hugging Face Papers and Trending Papers.** This is the official redirect target. A paper appears on
   Trending once it has an HF paper page with a linked GitHub repository. The ranking formula is not
   documented (**unverified**).
2. **paperswithcode.co/submit**, if the site is up.

## Steps

1. **Do everything in `05_hf_paper_page.md`.** Index the paper, claim authorship, put the arXiv link in
   the dataset card, set the GitHub repository and project page on the paper page, and submit to Daily
   Papers within 14 days of arXiv v1. This lists the paper, the code and the dataset together, which is
   what the old PwC page did.
2. **Submit at paperswithcode.co** once `https://paperswithcode.co/submit` loads. Give the arXiv id and
   `https://github.com/harness-db/harness-db`, then check the page it creates:
   - the task tags should be about agents, systematic review and dataset. Correct any tag that implies a
     benchmark leaderboard;
   - there should be **no "results" rows**. HARNESS-DB reports no model scores of its own. The 5,863 rows
     in `data/results.csv` are author-reported scores collected from the corpus, not results of this paper.
3. **Dataset entry.** The revival's dataset flow could not be checked while the site was down
   (**unverified**). If it has one, describe the dataset in one sentence taken from the dataset card:
   "HARNESS-DB is a coded dataset of LLM agent harnesses: 1,256 systems from 2022 to 2026 on 38 design
   dimensions, 47,728 cells, each a value with a verbatim quote and locator, `not_reported`, or
   `unresolved`." Link Hugging Face (`bhaskar-ai/harness-db`) and Zenodo (doi:10.5281/zenodo.23031354).
4. **Do not use third-party mirrors as a substitute.** CatalyzeX, CodeSOTA, Hyper.ai and Wizwand are
   listed by Coursera as alternatives, but none of them is official. Only use one if a reader asks for it.
