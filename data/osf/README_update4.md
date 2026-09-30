# OSF registration update 4 (osf.io/ab2wn)

`update4_responses.json` files protocol amendments 10, 11, 12 and 12a, the 2026-09-28 deviation that has
no amendment (the codability gate), two analysis corrections (system-clustered layer standard errors;
the null-fill cap lifted), the human correctness audit, and the v1.0.0 dataset release. It revises
10 answers: 376-12, 376-48, 376-82, 376-94, 376-100, 376-106, 376-108, 376-116, 376-122, 376-134. The
dated amendment log is in `_justification`, because the registration has no amendment-log question.

It is written to apply **after update 3**. Each answer is a full replacement that already carries
update 3's content where update 3 touched the same question. Nothing has been filed.

## Before filing

1. **Update 3 must be filed and approved first.** OSF allows one pending update at a time. The script
   refuses to file while an update is waiting for approval, and it diffs against the newest *approved*
   response. On 2026-09-30 the live 376-12 still carried update 2's text ("coding is in progress"), so
   update 3 was either not filed or not approved. If it was not filed:
   `python scripts/osf_update.py --responses data/osf/update3_responses.json`
2. **Check that the script diffs against update 3.** After update 3 is approved, run
   `python scripts/osf_update.py --show`. 376-12 should begin "Searching, screening, system grouping and
   coding are complete". If it still shows update 2's text, the "newest approved first" ordering the
   script assumes does not hold. Do not file in that case, because the PATCH would write stale answers
   back.
3. **The submit comment is hard-coded.** `scripts/osf_update.py` sends
   "Amendments 2-8; see the revision justification." with every submit. That text is wrong for updates
   3 and 4. Consider changing it before filing either one. (It was not changed here.)
4. **Two answers were drafted without their full live text.** The drafter could see only the
   90-character `--show` prefix of 376-122 (analysis plan, 609 chars live) and 376-134 (sensitivity
   analyses, 240 chars live). Both replacements describe the analysis as actually run, and OSF keeps the
   registered text in the version history. Still, read the live answers on osf.io and confirm that the
   replacement drops nothing that is still true.
5. **Two answers are now wrong but were not replaced**, because their full live text was not available
   to the drafter. To include them, copy the live text from osf.io, append the sentence below, and add
   the key to the JSON before filing:
   - **376-24** ("Exploratory review; no confirmatory hypotheses ..."): *"Amendment 12 (2026-09-24;
     revised by 12a, 2026-09-25) adds one confirmatory hypothesis, H2: at equal compute, a harness that
     spends its extra calls on verifying and repairing scores higher than one that spends them on
     unguided retries. It was not tested: the pilot failed its pre-stated accuracy band and no
     confirmatory run was made."*
   - **376-16** ("2027-02-12 (planned arXiv preprint and HARNESS-DB v1.0 release) ..."): *"Revised:
     HARNESS-DB v1.0.0 was released on 2026-09-25 (Zenodo concept DOI 10.5281/zenodo.23031354), and the
     arXiv preprint is being posted ahead of the registered date."*
6. **Length.** Every answer is under 1,700 characters. The longest answer OSF has accepted so far is
   1,959. The justification is about 5,800 characters. The largest one filed so far is 2,347 (update 2),
   and update 3's 3,533 has not yet been filed. If OSF refuses the PATCH on length, shorten the SOURCES
   paragraph or move it into `_comment`. Then re-run the same command: the script resumes the draft it
   left in progress.

## File it

```
python scripts/osf_update.py --responses data/osf/update4_responses.json --dry-run
python scripts/osf_update.py --responses data/osf/update4_responses.json
```

## Order on osf.io/ab2wn

1. **Approve the pending update (update 3).** Use the approval link in the OSF email, or the pending
   update on the registration page.
2. **File update 4** with the command above, once update 3 shows as approved.
3. **Approve update 4** the same way. Until then the amendments are not on the public record.
4. **End the embargo early** from the registration page's admin controls, at arXiv posting. Every admin
   contributor must approve. The registration DOI is minted when the registration becomes public.

## What the manuscript says, and when it becomes true

`paper/sections/04_methodology.tex` §4.1 and `paper/sections/S_amendments.tex` say that the eleven
amendments "are accepted" and that amendments 12 and 12a "are filed and pending acceptance". On
2026-09-30 only amendments 1-8 were on the approved record. Amendment 9 is in update 3, and amendments
10-12a are in this update. Those sentences become true only after steps 1-3 above. Until then they
should say "to be filed". The justification says this openly.

Two more things to fix:

- Update 3's justification numbers two of its items (10) and (11) (cell states; coding complete). These
  are not protocol amendments 10 and 11. Update 4's justification states the difference.
- Update 2 filed a census of 6,162 systems. Amendment 10 in the protocol log gives the pre-repair census
  as 6,172, while `docs/count_reconciliation.md` traces 6,172 → 6,501 → 6,504. Update 4 states only
  6,504.
