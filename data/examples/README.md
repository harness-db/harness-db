# Worked examples

These two files are the worked examples referenced by `docs/coding_manual.md`.
They were coded end to end on 2026-09-16 (`coder: "llm-prefill"`) during manual calibration, before
the final protocol (amendment 4 and the general-rule-5 rewrite) under which the released dataset was
coded. They illustrate the decision rules; they are not part of the release, and where a released cell
differs from an example the release is the record (see the reader's note at the top of the manual's
per-dimension section).

| file | system | pinned tag | commit | date |
|---|---|---|---|---|
| `swe-agent-1x.json` | SWE-agent 1.x | `v1.1.0` | `0f3acafacabc0def8cc76b4e48acb4b6cf302cb9` | 2025-05-22 |
| `openhands.json` | OpenHands (Agent Canvas) | `v1.16.0` | `64c1269655012698bc66538967989996191beb6c` | 2026-08-27 |
| `openhands.json` (agent code) | OpenHands software-agent-sdk, pinned by `OpenHands/config/defaults.json:4` (`agentServer: 1.44.0`) | `v1.44.0` | `322dec7d777497e376f81e093ed1eb0196bbbb39` | 2026-08-27 |

Notes

- Pin rule: latest tagged release before 2026-08-31 in the flagship repo. At that tag
  the OpenHands repo is the TypeScript "Agent Canvas" frontend; the agent loop, tools
  and runtime live in `OpenHands/software-agent-sdk`, so agent-behaviour cells cite
  the SDK at the version the frontend pins. Evidence strings are prefixed with the
  repo name (`OpenHands/...`, `software-agent-sdk/...`).
- Evidence format: `path:line@short-hash` for code (line numbers read at the pinned
  commit) or a verbatim quote with section number for papers
  (arXiv:2405.15793 for SWE-agent, arXiv:2407.16741 for OpenHands).
- Both files validate against `schema/harness_db.schema.json` (wrap the object in a
  list when validating); 38 cells each, 0 `not_reported`.
- Cells follow the "default first, capability second" rule (manual rule 4). The
  ambiguities uncovered are listed at the end of the manual and feed the pilot and
  the schema changelog.

Validate:

```
python -c "import json,sys; from jsonschema import Draft202012Validator as V; s=json.load(open('schema/harness_db.schema.json',encoding='utf-8')); d=json.load(open(sys.argv[1],encoding='utf-8')); errs=list(V(s).iter_errors([d])); print('\n'.join(e.json_path+': '+e.message for e in errs) or 'VALID')" data/examples/swe-agent-1x.json
```
