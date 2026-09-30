# Launch checklist

Everything here is done by the author, by hand. Nothing in this kit posts or sends anything by itself.

## Before launch day

These were checked on 2026-09-30. The repository `harness-db/harness-db` is public, and Pages serves the
explorer at <https://harness-db.github.io/harness-db/> (the page title is "HARNESS-DB explorer", and
`#system=<id>` permalinks resolve). The Hugging Face dataset `bhaskar-ai/harness-db` is public with its
`cells` and `systems` configs. Zenodo release v1.0.0 (10.5281/zenodo.23031355) is live. GitHub release
`v1.0.0` exists with one asset.

1. [ ] **Create the issue labels.** The issue forms apply `wrong-cell`, `add-system` and `request-system`,
   but **none of these labels exists in the repository** (label list on 2026-09-30). GitHub only applies
   labels that exist, so reports would arrive unlabelled and the metrics below would read zero.

   ```sh
   gh label create wrong-cell     -R harness-db/harness-db -c D93F0B -d "A coded cell is wrong, or a not_reported cell can be settled"
   gh label create add-system     -R harness-db/harness-db -c 0E8A16 -d "Claim a system to code"
   gh label create request-system -R harness-db/harness-db -c 1D76DB -d "Ask for a system to be coded"
   ```

2. [ ] **Test one prefilled link.** Open the *fix* link on any row of `docs/launch/cards/swe-agent.md` while
   logged in, check that the form arrives with the system, dimension and current value filled in, and do
   not submit it.
3. [ ] **Fix the stale public text.** `README.md` still opens with "Private during construction", and its
   Hugging Face badge says "pending" although the dataset is live. `DATASET_CARD.md` (and the HF README)
   says "arXiv identifier to be added at release".
4. [ ] **Prepare the arXiv id swap.** When the id is known, list every placeholder with
   `grep -rn "\[arXiv id\]" docs/launch` and replace each one. Then recount post lengths: see the note in
   `01_x_thread.md`.
5. [ ] **Enable GitHub Discussions** (optional), so that questions do not land in the issue tracker.
6. [ ] **Block out time.** The rule is a reply within 48 hours to every wrong-cell report, Community post
   and email reply. Block about an hour a day for the first two weeks.

## Launch day: order of operations

arXiv announces new submissions at 20:00 US Eastern, Sunday to Thursday, which is 00:00 UTC while US
daylight time is in effect. Confirm this on <https://info.arxiv.org/help/availability.html> for your week.
All times below are UTC.

| Step | When | What | File |
|---:|---|---|---|
| 1 | as soon as the listing is live | Check the abstract page, the PDF and the author name. Copy the arXiv id. Replace `[arXiv id]` everywhere (pre-launch step 4). | — |
| 2 | +0:15 | Hugging Face: index the paper, claim authorship, add the arXiv link to the dataset card, set the GitHub and project links, submit to Daily Papers (weekday, within 14 days of v1), post and pin the Community post. | `05_hf_paper_page.md` |
| 3 | +0:45 | GitHub release notes: add the paper link to `v1.0.0` (`gh release edit v1.0.0 -R harness-db/harness-db --notes-file <notes.md>`, starting from the current notes, which `gh release view v1.0.0 -R harness-db/harness-db` prints). Add the arXiv badge or link to the README. | — |
| 4 | +1:00 | X thread. Pin post 1. | `01_x_thread.md` |
| 5 | 14:00–16:00 on a Tue–Thu, or 12:00–14:00 on a Sunday | Show HN, with the first comment posted immediately. If launch day falls outside these windows, wait for the next one: the HN post does not need to be on arXiv day. | `03_show_hn.md` |
| 6 | after HN | LinkedIn. | `02_linkedin.md` |
| 7 | after HN; r/LocalLLaMA the next day | Reddit, **rewritten in your own words**. | `04_reddit.md` |
| 8 | day 1 onward, one list a day | Awesome-list PRs, in the table's order. Skip the ones marked blocked or "wait". | `06_awesome_lists.md` |
| 9 | day 1 onward | paperswithcode.co submission, if the site is up. | `07_papers_with_code.md` |
| 10 | from day 1, 10 emails a day | Emails, batched as below. | `08`, `09`, `10` |
| 11 | week 2 | Newsletter pitches, rewritten in your own words, one per outlet. | `11_press_and_newsletters.md` |

HN timing evidence is weak, so use it as a tie-breaker only:

- An analysis of 157k Show HN posts found the best breakout rate on Sunday, with 12:00 UTC the best hour in
  an 11:00–16:00 window
  (<https://www.myriade.ai/blogs/when-is-it-the-best-time-to-post-on-show-hn>, 2025-07-18).
- An analysis of all HN posts recommends Tuesday to Thursday, 14:00–17:00 UTC
  (<https://blog.alcazarsec.com/tech/posts/best-time-to-post-on-hacker-news>, 2026-03-14).
- The HN discussion of the first analysis thought timing matters little next to quality.
- Never ask anyone to upvote.

### Email batches (37 emails, 10 a day)

| Day | Emails |
|---|---|
| 1 | `08` #1–#7 (all seven survey authors), then `10` #1–#3 |
| 2 | `10` #5–#10, then `09` #1–#4 |
| 3 | `09` #5–#14 |
| 4 | `09` #15–#20 |
| 8 | `10` #4 (Yunbei Zhang), a week after the Li et al. email |

Log each send (date, recipient, file and number) in a private sheet, not in the repository.

## What to measure, daily, for four weeks

GitHub's traffic API keeps only the last 14 days. **Save the traffic output every day**, or it is lost.

| Source | Field | Why |
|---|---|---|
| GitHub repo | `stargazers_count`, `forks_count`, `subscribers_count` (watchers) | reach |
| GitHub stargazers | `starred_at` per star | stars per day, matched to each launch step |
| GitHub traffic views | `count`, `uniques` (14-day window, daily rows) | visits |
| GitHub traffic clones | `count`, `uniques` | people who took the code or data |
| GitHub referrers | `referrer`, `count`, `uniques` | which channel worked (news.ycombinator.com, t.co, reddit.com, linkedin.com, huggingface.co) |
| GitHub popular paths | `path`, `count` | whether people read the README, the explorer source, or `data/` |
| GitHub release | asset `download_count` | release zip downloads |
| GitHub issues | issues labelled `wrong-cell`: opened, closed, time to first reply | corrections, the main goal; the reply target is 48 hours |
| Hugging Face | `downloads` (rolling 30 days), `downloadsAllTime`, `likes` | dataset use |
| Zenodo v1.0.0 | `stats.views`, `stats.unique_views`, `stats.downloads`, `stats.unique_downloads` | archive use (checked 2026-09-30: all 0) |
| HN | `score`, `descendants` (comments) | HN reception |

## Commands (no scripts; `gh` and `curl` only)

Set the repository once per shell: `R=harness-db/harness-db`.

```sh
# repository counters
gh api repos/$R --jq '{stars: .stargazers_count, forks: .forks_count, watchers: .subscribers_count, open_issues: .open_issues_count}'

# stars per day (needs the star+json media type for starred_at)
gh api repos/$R/stargazers -H "Accept: application/vnd.github.star+json" --paginate --jq '.[].starred_at[0:10]' | sort | uniq -c

# traffic: views and clones, per day (save this output daily; the API keeps 14 days)
gh api repos/$R/traffic/views  --jq '.views[]  | [.timestamp[0:10], .count, .uniques] | @tsv'
gh api repos/$R/traffic/clones --jq '.clones[] | [.timestamp[0:10], .count, .uniques] | @tsv'

# where visitors came from, and what they opened (14-day totals)
gh api repos/$R/traffic/popular/referrers --jq '.[] | [.referrer, .count, .uniques] | @tsv'
gh api repos/$R/traffic/popular/paths     --jq '.[] | [.path, .count, .uniques] | @tsv'

# release asset downloads
gh api repos/$R/releases --jq '.[] | .tag_name as $t | .assets[] | [$t, .name, .download_count] | @tsv'

# wrong-cell reports: open and closed, with first-reply bookkeeping done by hand from the list
gh issue list -R $R --label wrong-cell --state all --limit 200 --json number,title,createdAt,closedAt,comments --jq '.[] | [.number, .createdAt[0:10], (.closedAt // "open")[0:10], (.comments | length), .title] | @tsv'

# Hugging Face dataset downloads and likes
curl -s "https://huggingface.co/api/datasets/bhaskar-ai/harness-db?expand[]=downloads&expand[]=downloadsAllTime&expand[]=likes"

# Zenodo v1.0.0 views and downloads (the "stats" object)
curl -s https://zenodo.org/api/records/23031355

# Hacker News item, after posting (replace <id> with the item id from the URL)
curl -s https://hacker-news.firebaseio.com/v0/item/<id>.json
```

To keep the 14-day traffic, append each day's output to a dated file outside the repository, for example
`gh api repos/$R/traffic/views > ~/harness-db-metrics/views-$(date +%F).json`. Do the same for `clones`,
`referrers` and `paths`.

## Weekly review (for four weeks)

- **Stars and traffic by channel.** Match the referrers to the launch steps. Drop channels that bring
  nothing, rather than posting in them again.
- **Wrong-cell reports.** Count them, check the median time to first reply against the 48-hour target, and
  count the corrections queued for 1.0.1. **Every accepted correction goes into the next versioned
  release. Released versions are never edited in place.**
- **Replies to the 37 emails.** Note who offered to co-maintain, correct or collaborate, and follow up with
  each of them personally.
