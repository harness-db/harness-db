# Methods paragraph — screening (draft for `paper/sections/04_methodology.tex`)

Drafted 2026-09-17 from the registered protocol (`docs/protocol_prisma_p.md` §3, §4, §7) and the
Phase 3 tooling (`scripts/export_screening.py`, `scripts/prioritise.py`, `scripts/screen_llm.py`,
`scripts/kappa.py`). Numbers in `\num{...}` are the search-freeze values; the blanks (`\_\_`) are
filled when screening ends. Paste the block between the rules into the `.tex` file; it uses only
`\num`, `\emph`, `\citep` and `\kappa`, so it compiles with `siunitx` and `natbib`/`biblatex`.

---

```latex
\paragraph{Screening.}
The \num{27747} unique records that remained after deduplication (\num{50724} identified; duplicates merged on DOI, then arXiv identifier, then normalised title) were screened on title and abstract by two screeners working independently and blinded to each other's decisions in Rayyan. Both applied the decision procedure of the registered protocol in order (named system, loop, executed actions, domain and date) and recorded one of \emph{include}, \emph{exclude} or \emph{unsure}; at this stage every exclusion carries the code \texttt{out\_of\_scope} with, where the abstract made it evident, its sub-reason. Screener~1 screened in the order proposed by ASReview's active-learning prioritisation (TF--IDF features, naive Bayes classifier, maximum-uncertainty query), seeded with the \num{46} registered known items present in the candidate set and \num{20} rule-selected irrelevant records, and stopped under the pre-registered rule of \num{100} consecutive irrelevant records after every known item had been retrieved (\_\_ records screened). Screener~2 screened the complete set in random order. Inter-rater agreement on the records seen by both was Cohen's $\kappa = \_\_$ (\num{\_\_} records); conflicts were resolved by discussion and each resolution logged with its reason. Records not excluded by either screener proceeded to full-text retrieval and assessment against steps 5--11 of the decision procedure, including the codability threshold of at least 19 of 38 dimensions with evidence, and received exactly one primary exclusion code (\texttt{out\_of\_scope}, \texttt{no\_harness\_description}, \texttt{duplicate\_system}, \texttt{not\_retrievable}, \texttt{other}). As a secondary measurement, an LLM (Claude Opus~5, run through Claude Code's headless mode with the protocol text as its system prompt, tools disabled, schema-constrained JSON output and low reasoning effort; 40 records per call) voted on every title and abstract (
um{21480} records; the remaining 
um{6267} were voted by Claude Sonnet~5 through the Messages API with the identical prompt, schema and batch procedure after the subscription usage limit was reached; the model is recorded per record and the vote distributions of the two subsets are compared in the supplement); its votes were stored in a separate column, were never shown to the screeners before adjudication and never replaced a human decision, and we report human--LLM agreement ($\kappa = \_\_$) alongside the human--human value. In line with RAISE guidance on AI in evidence synthesis, we disclose that the model's role was limited to this third, non-binding vote and to pre-filling extraction cells later verified by a human coder; every inclusion, exclusion and coded value in HARNESS-DB was decided by a named human screener or coder of record.
```

---

Word count of the paragraph: about 330 (target 300). To shorten, drop the parenthetical model
settings of ASReview and the list of exclusion codes (they are in the protocol appendix).

Reportable now (from `data/screening/llm_vote_tuning.md`): low reasoning effort agreed with the default
setting on 84\% of votes on 160 records with no include/exclude flips (differences were moves to
\emph{unsure}); one sentence in the Threats section can cite this.

Values to fill at the end of screening: screener-1 records screened (from
`data/screening/stopping_rule_log.md`), human--human $\kappa$ and the number of records both
screeners saw (`scripts/kappa.py votes ...`), human--LLM $\kappa$ (same script, `llm_votes.csv`
joined on `record_id`).
