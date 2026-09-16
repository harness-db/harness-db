# Coding manual (v0)

Status: draft. Becomes v1 after the pilot. Two worked examples (SWE-agent, OpenHands) to
be added before pilot coding starts.

## General rules

1. Code the system at its pinned version (`M6`). If the paper and the repo disagree, code
   the repo at the pinned commit and note the paper's claim in `note`.
2. Every cell needs evidence: a verbatim quote with section, a URL, or `path:line@commit`.
   No paraphrase. If you cannot point at it, set `not_reported: true`.
3. Confidence: `high` = explicit statement or code; `medium` = inferred from adjacent
   code or figure; `low` = inferred from behavior described in prose.
4. Multi-valued dimensions take every value that applies at the pinned version. Do not
   include `none` alongside other values.
5. When a value list does not fit, pick the closest value and write the mismatch in `note`.
   Value lists change only through `schema/dimensions.json` plus a changelog line.

## Dimension notes

Decision rules per dimension are written during the pilot. Template:

### B3 edit_primitive
- `search_replace`: the model emits an old/new block pair that the harness locates and swaps.
- `unified_diff`: the model emits diff syntax that is applied with patch semantics.
- `line_range_edit`: the model addresses lines by number (SWE-agent 0.x `edit` command).
- `whole_file_rewrite`: the model re-emits the full file.
- `ast_aware`: the harness parses the file and applies a structural edit.

_(add the remaining dimensions during the pilot)_

## Worked examples

_(SWE-agent 1.x and OpenHands, coded end to end with evidence strings, to be added)_
