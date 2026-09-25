"""Independent check of paper/sections/05_unified_taxonomy.tex and A1_coding_sheet.tex against
schema/dimensions.json. Parses the .tex as written (does not import the generator)."""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent.parent  # repository root
SEC = REPO / "paper" / "sections"
schema = json.loads((REPO / "schema/dimensions.json").read_text(encoding="utf-8"))
D = {d["id"]: d for d in schema["dimensions"]}
LNAME = {l["id"]: l["name"] for l in schema["layers"]}
s5 = (SEC / "05_unified_taxonomy.tex").read_text(encoding="utf-8")
a1 = (SEC / "A1_coding_sheet.tex").read_text(encoding="utf-8")
errors = []


def untt(x):
    return re.sub(r"\\texttt\{([^}]*)\}", r"\1", x).replace(r"\_", "_").strip()


def env_with_label(tex, label):
    for m in re.finditer(r"\\begin\{table\}.*?\\end\{table\}", tex, re.DOTALL):
        if f"\\label{{{label}}}" in m.group(0):
            return m.group(0)
    raise SystemExit(f"missing {label}")


# ---- Section 5 consolidated table
t = env_with_label(s5, "tab:dimensions")
rows = re.findall(r"^(.*?) & ([A-M]\d) & \\texttt\{([^}]*)\} & (.*?) & (.*?) \\\\$", t, re.MULTILINE)
seen5 = []
for lay, i, key, desc, cnt in rows:
    d = D.get(i)
    if not d:
        errors.append(f"s5 unknown id {i}"); continue
    seen5.append(i)
    if untt(key) != d["key"]: errors.append(f"s5 key {i}")
    if i[0] != d["layer"]: errors.append(f"s5 layer {i}")
    if len(desc.split()) > 8: errors.append(f"s5 desc >8 words {i}")
    if d["type"] == "enum":
        exp = f"$\\{{{len(d['values'])}\\}}$" if d["multi"] else str(len(d["values"]))
    else:
        exp = f"\\emph{{{d['type']}}}"
    if cnt.strip() != exp: errors.append(f"s5 count {i}: {cnt} != {exp}")
if sorted(seen5) != sorted(D) or len(seen5) != 38:
    errors.append(f"s5 has {len(seen5)} rows / missing {set(D)-set(seen5)}")
# layer labels in first column appear in the right group
for L in LNAME:
    first = next(r for r in rows if r[1].startswith(L))
    if not first[0].startswith(f"{L}\\enspace"): errors.append(f"s5 layer label {L}")
n_multi = sum(1 for r in rows if r[4].startswith("$\\{"))
n_type = sum(1 for r in rows if r[4].startswith("\\emph"))

amb = env_with_label(s5, "tab:ambiguities")
n_amb = len(re.findall(r"^\d+ & ", amb, re.MULTILINE))
if n_amb != 26: errors.append(f"ambiguities {n_amb}")

# ---- A1 per-layer tables
seenA = []
for L, lname in LNAME.items():
    t = env_with_label(a1, f"tab:coding-{L}")
    if lname not in t: errors.append(f"A1 caption layer name {L}")
    for m in re.finditer(r"^\\texttt\{([A-M]\d)\} & \\raggedright (.*?) \\newline \\texttt\{([^}]*)\} & "
                         r"\\raggedright (.*?) & (\w+), (single|multi) & \\raggedright (.*?) \\tabularnewline$",
                         t, re.MULTILINE):
        i, name, key, desc, typ, card, vals = m.groups()
        d = D[i]
        seenA.append(i)
        if d["layer"] != L: errors.append(f"A1 {i} in wrong layer table")
        if name != d["name"]: errors.append(f"A1 name {i}: {name}")
        if untt(key) != d["key"]: errors.append(f"A1 key {i}")
        if typ != d["type"]: errors.append(f"A1 type {i}")
        if (card == "multi") != d["multi"]: errors.append(f"A1 multi {i}")
        if d["type"] == "enum":
            got = [untt(v) for v in vals.split(", ")]
            if got != d["values"]: errors.append(f"A1 values {i}: {got} != {d['values']}")
        else:
            if vals != f"no enumerated set ({d['type']})": errors.append(f"A1 non-enum {i}")
if sorted(seenA) != sorted(D) or len(seenA) != 38:
    errors.append(f"A1 has {len(seenA)} rows / missing {set(D)-set(seenA)}")

# ---- worked-example table against released files
ex = {"swe": json.loads((REPO / "data/examples/swe-agent-1x.json").read_text(encoding="utf-8"))["coding"],
      "oh": json.loads((REPO / "data/examples/openhands.json").read_text(encoding="utf-8"))["coding"]}
t = env_with_label(a1, "tab:coding-examples")
for m in re.finditer(r"^\\texttt\{([A-M]\d)\} & \\texttt\{([^}]*)\} & \\raggedright (.*?) & \\raggedright (.*?) \\tabularnewline$", t, re.MULTILINE):
    i, key, a, b = m.groups()
    for s, cell in (("swe", a), ("oh", b)):
        v = ex[s][D[i]["key"]]["value"]
        v = [str(x) for x in (v if isinstance(v, list) else [v])]
        if [untt(x) for x in cell.split(", ")] != v: errors.append(f"example {s} {i}")

# ---- structure, refs, figures, citations, forbidden words
alltex = "".join(p.read_text(encoding="utf-8") for p in SEC.glob("*.tex"))


def doc_labels(root):
    txt = (REPO / "paper" / root).read_text(encoding="utf-8")
    files = re.findall(r"\\input\{sections/([^}]*)\}", txt)
    out = set(re.findall(r"\\label\{([^}]*)\}", txt))
    for f in files:
        fp = SEC / (f + ".tex")
        if fp.exists():
            out |= set(re.findall(r"\\label\{([^}]*)\}", fp.read_text(encoding="utf-8")))
    return out, files


main_labels, main_files = doc_labels("main.tex")
supp_labels, supp_files = doc_labels("supplement.tex")
assert "05_unified_taxonomy" in main_files and "A1_coding_sheet" in supp_files
for name, tex in (("s5", s5), ("A1", a1)):
    labels = main_labels if name == "s5" else supp_labels
    if tex.count("\\section") != 1: errors.append(f"{name} section count")
    for r in re.findall(r"\\ref\{([^}]*)\}", tex):
        if r not in labels: errors.append(f"{name} dangling ref {r}")
    for g in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]*)\}", tex):
        if not list((REPO / "paper/figures").glob(g + ".*")): errors.append(f"{name} missing fig {g}")
    bib = "".join(p.read_text(encoding="utf-8") for p in (REPO / "paper/references").glob("*.bib"))
    for c in re.findall(r"\\cite[tp]?\{([^}]*)\}", tex):
        for k in c.split(","):
            if "{" + k.strip() + "," not in bib: errors.append(f"{name} missing bib {k}")
    body = re.sub(r"%.*", "", tex)
    for w in ["clearly", "obviously", "evidently", "naturally", "of course", "dramatically", "drastically",
              "significantly", " very ", "quite", "novel", "robust", "comprehensive", "state-of-the-art"]:
        if re.search(r"\b" + w.strip() + r"\b", body, re.IGNORECASE): errors.append(f"{name} forbidden word '{w.strip()}'")
    if name == "s5":
        for pat in [r"docs/", r"data/", r"scripts/", r"schema/", r"\.json", r"\.md\b", r"\.py\b", r"coding manual \\S"]:
            if re.search(pat, body): errors.append(f"s5 file/path reference {pat}")
labels5 = set(re.findall(r"\\label\{([^}]*)\}", s5))
dups = [l for l in labels5 | set(re.findall(r"\\label\{([^}]*)\}", a1))
        if alltex.count("\\label{" + l + "}") > 1]
if dups: errors.append(f"duplicate labels {dups}")


def prose_words(tex):
    t = re.sub(r"(?m)%.*$", "", tex)
    t = re.sub(r"\\begin\{(table|figure)\}.*?\\end\{\1\}", " ", t, flags=re.DOTALL)
    t = re.sub(r"\\(label|ref|cite[tp]?|includegraphics)(\[[^]]*\])?\{[^}]*\}", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    t = re.sub(r"[{}$~\\]", " ", t)
    return len([w for w in t.split() if re.search(r"[A-Za-z0-9]", w)])


def caption_words(tex):
    caps = re.findall(r"\\caption\{(.*?)\}\s*\n?\\label", tex, re.DOTALL)
    return sum(prose_words(c) for c in caps)


print("Section 5: table rows", len(rows), "| multi", n_multi, "| non-enum", n_type, "| ambiguities", n_amb)
print("A1: dimension rows", len(seenA))
print("s5 prose words (excl. floats):", prose_words(s5), "| + captions:", prose_words(s5) + caption_words(s5),
      "| raw wc:", len(s5.split()))
print("A1 prose words (excl. floats):", prose_words(a1), "| raw wc:", len(a1.split()))
long = [s for s in re.split(r"(?<=[.;:])\s+", re.sub(r"\\begin\{(table|figure)\}.*?\\end\{\1\}", "", s5, flags=re.DOTALL)) if len(s.split()) > 40]
print("s5 sentences > 40 words:", len(long))
for s in long: print("   ", s[:120])
print("ERRORS:" if errors else "ALL CHECKS PASS", *errors, sep="\n  ")
