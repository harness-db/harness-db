# ASReview stopping rule and session log (screener 1)

**Registered rule (protocol section 7 / execution plan Phase 3):** screener 1 screens in the order
proposed by ASReview and stops when **100 consecutive records have been labelled irrelevant after
every known item has been found** (the 46 known-item priors listed in `prior_knowledge.csv`;
2 of the 48 registered ids are not in the candidate set: 2607.10113, 2609.17394). Screener 2 screens
the full set in random order. The rule is stated before screening starts and may only be changed
by a protocol amendment.

Prior knowledge entered in ASReview: 46 relevant (known items) + 20 irrelevant
(`prior_knowledge.csv`, rules `date` and `model_paper`).

ASReview version: ____ · feature extractor: ____ (default TF-IDF) · classifier: ____ (default
Naive Bayes) · query strategy: ____ (default max) · balance: ____ (default dynamic resampling).

| session date | screener | records screened this session | cumulative screened | longest run of consecutive irrelevant | known items found so far (of 46) | stop condition met? | note |
|---|---|---:|---:|---:|---:|---|---|
| | | | | | | | |

Stop when the last column reads "yes" **and** all 46 known items have been found. Record the
final cumulative count here and in `data/prisma_counts.json` (`screened_title_abstract` is the
union of both screeners' records, not this number).
