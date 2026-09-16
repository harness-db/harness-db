# Contributing to HARNESS-DB

The dataset is under construction and private until arXiv v1. This file describes the
workflow the maintainers use now; the public contribution guide (PR template, review
rules) is finalized in the release phase.

## Adding or editing a system

1. One object per system in `data/systems.json`. Version a system on a major redesign
   (`swe-agent-0x`, `swe-agent-1x`) and link them with `supersedes`.
2. Code every dimension in `schema/dimensions.json`. A cell is either
   `not_reported: true`, or it has a `value`, a non-empty `evidence` string, and a
   `confidence`.
3. Evidence is a verbatim quote with its section, a URL, or `path:line@commit`. No
   paraphrases. If you cannot point to it, it is `not_reported`.
4. Link the system to its papers by id in `data/papers.csv`.
5. Run the checks before opening a PR:

```
python scripts/build_schema.py --check
python scripts/validate.py
pytest -q
```

## Changing the coding sheet

Edit `schema/dimensions.json` only. Then run `python scripts/build_schema.py` and commit
the regenerated `schema/harness_db.schema.json` together with a line in
`docs/schema_changelog.md`. After schema v1 is frozen, value lists may grow but existing
values are never renamed or removed without a major version bump.

## Licenses

Code is MIT (`LICENSE-CODE`). Data, schema, and docs are CC BY 4.0 (`LICENSE-DATA`).
By contributing you agree your contribution is released under the matching license.
