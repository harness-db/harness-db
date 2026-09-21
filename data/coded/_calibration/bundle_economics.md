# Where the coding tokens go, and what cannot be cut (measured 2026-09-21)

Pass A costs ~$0.35 per system: ~50,000 input tokens and ~3,700 output tokens, at Opus list rates
($5/$25 per million). With 1,116 systems in the coded set that is ~$390. Four ways to cut it were
measured against the real data before any change was made. Three of them do not exist.

## 1. Boilerplate in the evidence bundle - 4.4%, not worth removing

Across 40 assembled bundles (2.83M characters), pattern-matching for junk found:

| what | share of bundle |
|---|---|
| duplicate long lines | 3.7% |
| long hashes / base64 blobs | 0.3% |
| numeric result tables | 0.2% |
| bare URL lines, badges, licence text, citations, acknowledgements | 0.2% combined |
| **total identifiable waste** | **4.4%** |

Reference lists are already stripped by `strip_references`, which is why citation lines are ~0%.
A trimmer would recover at most 4%, and the duplicate-line share includes legitimately repeated
content (a README quoted in docs), so the real ceiling is lower.

## 2. Truncating the bundle - rejected, the tail carries evidence

For 60 coded systems, every pass-A evidence quote was located in the exact bundle the coder was
given (1,760 quotes found, 172 not - paraphrases and pass-B repairs). Where the evidence sits:

| quotes | fall within the first |
|---|---|
| 50% | 31% of the bundle |
| 75% | 59% |
| 90% | 82% |
| 95% | 90% |
| 99% | 98% |

So cutting the last 25% of each bundle would save ~25% of input and lose **14% of all evidence
quotes**; cutting half would lose a third. Evidence is spread through the whole document, which is
what one would expect when the 38 dimensions cover eight different layers of a system. The 110,000
character cap stays.

## 3. Amortising the system prompt over several systems per call - 7% at best

The system prompt (manual rules for all 38 dimensions) is 39,153 characters, ~9,800 tokens, and is
re-sent on every call because the CLI backend caches the whole prompt including the unique bundle
and therefore never gets a cache hit (see `coding_config_calibration.json`). It costs $0.049 per
call. Coding two systems per call would amortise it: $0.367 vs $0.391 per system, **-7%**; three
gives -4.8% more, four -3.6% more, with diminishing returns and rising risk - a batch is refused as
a whole when one system in it is an offensive-security agent, and a single response carrying 76
coded cells is likelier to be truncated or sloppy.

Trimming the manual's worked examples from the prompt (11,299 characters, 28.9% of it) would save a
further ~5% of input, at the cost of the examples that keep coding consistent.

**Neither was adopted, and the reason is not the size of the saving.** Changing the prompt or the
bundle mid-run splits the dataset across two procedures: systems coded before and after would have
seen different evidence, and the double-coded reliability sample would mix the two. A 7-12% token
saving does not justify a methodological seam through the middle of the coded set. If the coded set
is ever rebuilt from scratch, batching two systems per call is the first thing to revisit.

## 4. What was adopted instead - waiting on the clock, not on a timer

The binding constraint is not money (the plan is already paid for) but the rate limit, so the only
thing worth optimising is how much of each window gets used. The limit message states exactly when
it lifts ("You've hit your session limit - resets 2:50am (America/New_York)"). The driver now parses
that and sleeps until then instead of retrying every 30 minutes: at 22:00 that replaces ten futile
retries with one wait, and the next window starts within a minute of opening rather than up to half
an hour late. A reset time more than six hours out is treated as a stale message and retried at
once, so a passed reset never costs a day.
