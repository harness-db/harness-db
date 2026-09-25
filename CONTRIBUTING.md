# Contributing to HARNESS-DB

There are three ways to help, from least to most effort:

1. **[Report a wrong cell](#report-a-wrong-cell).** You know a value is wrong, or you can settle a
   `not_reported` cell with a quote. This takes about five minutes.
2. **[Request a system](#request-a-system).** A harness is missing, and you would like someone to
   code it.
3. **[Add or update a system](#add-or-update-a-system).** You code all 38 cells yourself and open a
   pull request.

[`docs/COVERAGE_WANTED.md`](docs/COVERAGE_WANTED.md) lists where each kind of help counts most: the
most-starred systems in the frame that are not coded yet, and the dimensions where the sources are
most often silent.

One rule applies to all three: **every value needs a verbatim quote and a locator that someone
else can re-open.** For code, the locator is `path/to/file.py:LINE@<commit>` at a pinned commit, not
`main`. For a paper, it is the arXiv id and section. If you cannot point to the evidence, the cell
is `not_reported`.

## Report a wrong cell

Open a [wrong cell](https://github.com/harness-db/harness-db/issues/new?template=wrong_cell.yml)
issue and give:

- the system id and the dimension;
- the value you think is right;
- the quote and its locator;
- for code, the commit the locator refers to.

A maintainer re-reads the cited source and either corrects the cell in the next release or replies
with the reason it stands. A `not_reported` cell that you can settle with evidence counts as a
correction too, and it is the most useful kind.

## Request a system

Open a [request a system](https://github.com/harness-db/harness-db/issues/new?template=request_system.yml)
issue with the system's name, repository and paper. The issue form asks you to check the system
against the working definition in [`docs/definition.md`](docs/definition.md): software between a
model and a task environment that assembles the model's input, executes its actions and decides
whether to continue. A model, a benchmark or a prompt on its own is not a harness.

## Add or update a system

You do not need the maintainers' coding pipeline (`scripts/code_system.py`) for this. You need a
text editor, the template and the validator.

1. **Claim it.** Open an [add a system](https://github.com/harness-db/harness-db/issues/new?template=add_system.yml)
   issue, so that two people do not code the same system. Check `data/systems.json` first: if the
   system is already there, you are updating it, and the issue should say which cells change.
2. **Fork and branch.** Then install the checks: `pip install -e ".[dev]"`.
3. **Copy the template.** Copy [`contrib/TEMPLATE_system.json`](contrib/TEMPLATE_system.json) to
   `contrib/<id>.json`. The id is a lowercase slug (`[a-z0-9-]`), for example `my-agent`, or
   `my-agent-2x` for a major redesign that supersedes an earlier version. Every one of the 38
   dimensions is already in the file with `value: null`, `not_reported: false` and an empty
   `evidence` slot. The `_dimension` and `_allowed` keys in each cell tell you what it means and
   which values the schema accepts. Leave them in; the validator ignores them.
4. **Pin first.** Pick the latest tagged release, or the commit you read, and fill
   `pinned_version` as `<tag> @ <full commit hash> (<YYYY-MM-DD>)`. Every code locator must point
   at that commit.
5. **Fill every cell.** Each cell ends up in exactly one of three states:

   | state | what to write |
   |---|---|
   | a value | `value`, `evidence` as `"<verbatim quote>" (<locator>)`, `confidence` (`high` \| `medium` \| `low`), `not_reported: false` |
   | silent | `value: null`, `not_reported: true`, and a `note` naming the place (config file, tool list, docs page) that the sources did not include |
   | cannot decide | `value: null`, `unresolved: true`, and a `note` saying what is unclear. A reviewer settles it. |

   **Absence is not silence** ([coding manual](docs/coding_manual.md), rule 5). Suppose you opened
   the place where a feature would be declared (the config model, the CLI flags, the tool registry,
   the run loop) and the feature is not there. That is a value (`none`, `open`, ...) whose evidence
   quotes that place. Use `not_reported` only when the sources contain no such place. The
   definitions of every value, and a worked example per dimension, are in
   [`docs/coding_manual.md`](docs/coding_manual.md).

   Put your GitHub handle in `coder` (for example `gh:octocat`). Two real cells from the release
   show the evidence format, one citing code and one citing a paper:

   ```
   ad-agent  timeouts       "DEFAULT_TIMEOUT = 120" (src/sandbox/config.py:66@f14a9c065ca8)
   openhands edit_primitive "edit_file, which allows modifying an existing file from a specified line" (paper Sec. 2.3)
   ```

6. **Run the gate.**

   ```
   python scripts/validate.py --system contrib/<id>.json
   ```

   The gate checks the file against the schema and names every cell that is still unfilled. It also
   checks that each value's evidence reads `"quote" (locator)`, and that each code locator carries a
   commit. A system with a repository must pin a commit. The gate prints `OK` when there are no
   errors. Warnings (a URL locator without a pinned commit, a paper id that is not yet in
   `data/papers.csv`) do not block the pull request, but the reviewer will ask about them.
7. **Open a pull request.** The [pull request template](.github/PULL_REQUEST_TEMPLATE.md) is the
   evidence checklist. Link the issue from step 1.

### How a pull request is reviewed

- **A second reading.** A reviewer codes the same system from the same pinned sources before
  looking at your values, then compares the two readings cell by cell. Each disagreement is settled
  by re-opening the cited locator, and the reason is recorded in the cell's `note`. The dataset's
  reliability figures come from the same kind of independent double coding.
- **The reliability gate.** Double-coded contributions are added to the per-dimension agreement
  table, and each dimension is held to the κ ≥ 0.6 floor that the schema was frozen on. If
  contributed cells on a dimension fall below it, that dimension stops accepting contributions
  until the coding manual is clarified. The fix is a clearer rule, not a looser one.
- **What merging means.** A maintainer strips the `_` hints, links the papers, and adds the system
  to `data/systems.json` in the next versioned release. Released versions are never edited in
  place, so the paper's numbers stay tied to 1.0.0. A contributed system was not drawn by the
  stratified sample, so it enters unweighted statements and carries weight 0 in field-level
  estimates, like the 23 systems in section 3 of `docs/COVERAGE_WANTED.md`.

## For maintainers

### Adding or editing a system in the working data

1. One object per system in `data/systems.json`. Version a system on a major redesign
   (`swe-agent-0x`, `swe-agent-1x`) and link the versions with `supersedes`.
2. Code every dimension in `schema/dimensions.json`. A cell is either `not_reported: true`,
   `unresolved: true`, or it has a `value`, a non-empty `evidence` string and a `confidence`.
3. Evidence is a verbatim quote with its section, a URL, or `path:line@commit`. No paraphrases.
4. Link the system to its papers by id in `data/papers.csv`.
5. Run the checks before opening a pull request:

```
python scripts/build_schema.py --check
python scripts/validate.py
python scripts/coverage_wanted.py --check
pytest -q
```

### Changing the coding sheet

Edit `schema/dimensions.json` only. Then run `python scripts/build_schema.py` and commit the
regenerated `schema/harness_db.schema.json` together with a line in `docs/schema_changelog.md`.
Schema v1 is frozen: value lists may grow, but existing values are never renamed or removed without
a major version bump, and every change needs an OSF registration update. When the schema changes,
regenerate the contributor template with `python scripts/make_contrib_template.py`;
`tests/test_contrib.py` fails until you do.

## Licenses

Code is MIT ([`LICENSE-CODE`](LICENSE-CODE)). Data, schema and docs are CC BY 4.0
([`LICENSE-DATA`](LICENSE-DATA)). By contributing, you agree that your contribution is released
under the matching license.
