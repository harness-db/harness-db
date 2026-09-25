"""Scan paper/sections/*.tex for file references (path/texttt/url) with their location label."""
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent  # repository root
SEC = ROOT / "paper" / "sections"
EXT = r"\.(csv|json|jsonl|md|py|html|pdf|svg|txt|log|cmd|tex|bib|yaml|yml|toml|cff|sqlite)$"
DIRS = ("data/", "scripts/", "schema/", "docs/", "paper/", "screening/", "tests/", "explorer/")
LIC = ("LICENSE-CODE", "LICENSE-DATA", "Makefile", "CITATION.cff")
BS = "\\"
refs = []
for f in sorted(SEC.glob("*.tex")):
    if f.name.startswith("S_"):
        continue
    text = f.read_text(encoding="utf-8")
    loc_sec = loc_sub = None
    lines = text.splitlines()
    env_stack = []
    for i, line in enumerate(lines, 1):
        s = "" if line.lstrip().startswith("%") else re.split(r"(?<!\\)%", line)[0]
        for m in re.finditer(r"\\begin\{(table\*?|figure\*?)\}", s):
            lab = None
            for j in range(i - 1, min(i + 80, len(lines))):
                mm = re.search(r"\\label\{((tab|fig):[^}]+)\}", lines[j])
                if mm:
                    lab = mm.group(1); break
                if re.search(r"\\end\{(table|figure)", lines[j]):
                    break
            env_stack.append(lab)
        mm = re.search(r"\\label\{((sec|subsec|app):[^}]+)\}", s)
        if mm:
            if mm.group(1).startswith("subsec"):
                loc_sub = mm.group(1)
            else:
                loc_sec, loc_sub = mm.group(1), None
        elif re.search(r"\\section\*?\{", s):
            sm = re.search(r"\\section\*?\{([^}]*)\}", s)
            loc_sec, loc_sub = ("*" + sm.group(1)) if sm else loc_sec, None
        for m in re.finditer(r"\\(?:path|texttt|url)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", s):
            raw = m.group(1)
            val = raw.replace(BS + "_", "_").replace(BS + "#", "#").replace(BS + "allowbreak", "").replace("{}", "").strip()
            val = re.sub(r"\\[a-z]+\s*", "", val)
            if val.startswith(DIRS) or re.search(EXT, val) or val in LIC or val.rstrip("/") in ("data", "scripts", "schema", "docs"):
                where = env_stack[-1] if env_stack else (loc_sub or loc_sec)
                refs.append({"file": val, "tex": f.name, "line": i, "where": where, "sec": loc_sec, "sub": loc_sub})
        for m in re.finditer(r"\\end\{(table\*?|figure\*?)\}", s):
            if env_stack:
                env_stack.pop()
print(len(refs), "references;", len({r['file'] for r in refs}), "distinct")
print(collections.Counter(r['tex'] for r in refs))
with open(pathlib.Path(__file__).with_name("refs.json"), "w", encoding="utf-8") as fh:
    json.dump(refs, fh, indent=1)
agg = collections.defaultdict(set)
for r in refs:
    agg[r['file']].add(f"{r['tex'][:3]}:{r['where']}")
for k in sorted(agg):
    ex = (ROOT / k.rstrip("/*")).exists()
    print(("OK " if ex else "?? ") + k, "|", ", ".join(sorted(agg[k])))
