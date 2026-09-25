<!-- This template is for a contributed system (contrib/<id>.json). For a code or docs change,
     delete the checklist and describe the change instead. -->

Closes #<issue>

**System:** `<id>` (new / update)
**Pinned version:** `<tag> @ <full commit hash> (<YYYY-MM-DD>)`
**Sources read:** repository at the pinned commit / paper (arXiv id) / documentation (URL)

## Evidence checklist

- [ ] `python scripts/validate.py --system contrib/<id>.json` prints `OK`, and any warnings are
      explained below.
- [ ] All 38 cells are filled: each has a value, `not_reported: true`, or `unresolved: true` with a
      note.
- [ ] Every value has a **verbatim** quote. Nothing is paraphrased or summarised.
- [ ] Every code locator is `path:line@<commit>` at the pinned commit (not `main`), and I opened
      that line.
- [ ] Every paper locator names the arXiv id (or DOI) and the section, table or figure.
- [ ] Absence values (`none`, `open`, ...) quote the place where the feature would be declared. A
      cell whose sources have no such place is `not_reported` (coding manual rule 5).
- [ ] Multi-valued cells list the shipped default plus the values that configuration can reach, and
      the `note` says which is the default (rule 4). No cell lists `none` together with other
      values.
- [ ] `confidence` follows rule 3: `high` for an explicit statement or the cited line, `medium` for
      an inference from adjacent code or a default, and `low` for an inference from prose.
- [ ] `coder` is set to my handle (`gh:<handle>`) on every cell I coded.
- [ ] For an update, the cells that change are listed below with their old and new values.

## Warnings and notes for the reviewer

<!-- List anything the gate warned about, any cells you marked unresolved, and anything you were
     unsure of. The reviewer codes the system from the same sources before reading your values,
     then settles each disagreement against the cited locator. -->
