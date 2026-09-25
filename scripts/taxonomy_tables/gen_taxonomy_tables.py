"""Generate the Section 5 consolidated dimension table, the ambiguity table, and the
Supplement A per-layer coding tables from schema/dimensions.json, then fill the two
section templates and write them to paper/sections/.

Only the short descriptions, the full descriptions and the ambiguity rows are
hand-written; every id, key, layer, name, type, multi flag, value count and value
set comes from the schema, so the tables cannot drift from it.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent  # repository root
HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = json.loads((REPO / "schema" / "dimensions.json").read_text(encoding="utf-8"))
DIMS = SCHEMA["dimensions"]
LAYERS = {l["id"]: l["name"] for l in SCHEMA["layers"]}

# <= 8 words each, for the consolidated main-text table
SHORT = {
    "A1": "how the per-call system prompt is produced",
    "A2": "how the model learns the repository or environment",
    "A3": "mechanisms that shrink the history sent",
    "A4": "format in which tool results reach the model",
    "B1": "syntax by which the model requests actions",
    "B2": "tool definitions exposed at the default configuration",
    "B3": "how the model expresses a file edit",
    "B4": "where the tool schema comes from",
    "B5": "standard agent or tool protocols spoken",
    "C1": "control-flow patterns driving calls and actions",
    "C2": "whether and how a plan is represented",
    "C3": "arrangement of agents at the default",
    "C4": "how work is handed to another agent",
    "C5": "points where a human gates or steers",
    "D1": "working state kept within a run",
    "D2": "information persisted across runs and re-injected",
    "D3": "whether an interrupted run can continue",
    "E1": "checks the harness applies to the work",
    "E2": "task-level retry after a failed attempt",
    "E3": "mechanism that reverts changes made in the run",
    "F1": "conditions that end a run",
    "F2": "mechanisms that limit or reduce spend",
    "F3": "time limits the harness enforces",
    "G1": "boundary within which actions execute",
    "G2": "what the agent may touch inside G1",
    "G3": "network egress available to actions",
    "G4": "how individual actions are authorized",
    "H1": "richest run record the harness can emit",
    "H2": "whether a recorded trajectory can be re-run",
    "H3": "benchmark evaluation wired into its own repositories",
    "H4": "safety controls on inputs, outputs, and actions",
    "M1": "task domains the harness is built for",
    "M2": "whether the source is open",
    "M3": "whether it runs across model providers",
    "M4": "artifact the pinned version is coded from",
    "M5": "first tagged release of the coded line",
    "M6": "tag and commit per coded repository",
    "M7": "flagship-repository stars, date-stamped in evidence",
}

# full descriptions for the supplement (verbatim from the v1 Section 5 layer tables)
FULL = {
    "A1": "how the system prompt that opens every model call is produced",
    "A2": "how the model is given knowledge of the repository or environment",
    "A3": "mechanisms that shrink the history sent to the model",
    "A4": "the format in which tool results are presented to the model",
    "B1": "the syntax by which the model requests an action",
    "B2": "distinct tool definitions exposed to the model in the default configuration",
    "B3": "how the model expresses a file modification",
    "B4": "where the tool schema shown to the model comes from",
    "B5": "standard agent or tool protocols the harness speaks",
    "C1": "the control-flow patterns that drive model calls and actions",
    "C2": "whether and how a plan is represented",
    "C3": "the arrangement of agents in the default configuration",
    "C4": "how work is handed to another agent, if at all",
    "C5": "the points at which a human can gate or steer the run",
    "D1": "what the harness keeps as working state within a run",
    "D2": "information persisted across runs and re-injected",
    "D3": "whether an interrupted run can be continued",
    "E1": "checks the harness applies, or prompts for, on the agent's work",
    "E2": "task-level retry behavior after a failed or rejected attempt",
    "E3": "the mechanism that reverts changes made during the run",
    "F1": "the conditions that end a run",
    "F2": "mechanisms that limit or reduce spend",
    "F3": "time limits the harness enforces",
    "G1": "the boundary within which agent actions execute, at the default",
    "G2": "what the agent may read or write inside the G1 boundary",
    "G3": "network egress available to agent actions",
    "G4": "how individual actions are authorized",
    "H1": "the richest form of run record the harness can emit",
    "H2": "whether a recorded trajectory can be re-run",
    "H3": "benchmark evaluation wired into the harness's own repositories",
    "H4": "safety controls on inputs, outputs, and actions",
    "M1": "the task domains the harness is built for",
    "M2": "whether the source is open",
    "M3": "whether the harness runs across model providers",
    "M4": "the artifact the pinned version is coded from",
    "M5": "first tagged release of the coded line",
    "M6": "tag and full commit hash for every repository coded",
    "M7": "GitHub stars of the flagship repository, date-stamped in evidence",
}

# The coding manual's 26 ambiguities, in the manual's numbering: (dims, case, resolution)
# case and resolution <= 10 words each (LaTeX markup words excluded from the count).
AMB = [
    ("B2, C3--C5, D3, E1, E2, G1, G4", "Capability shipped but off by default",
     "Code the default; name reachable alternatives in the note"),
    ("B2", "Toolsets, built-in, injected, and MCP tools",
     "One per schema sent; toolsets expanded; injected tools excluded"),
    ("B3", "New-file creation; custom patch formats",
     r"New file \texttt{whole\_file\_rewrite}; other patches \texttt{unified\_diff}, syntax named"),
    ("B4", "Hand-written declarative specs converted to schema",
     r"\texttt{hand\_written}: human-authored in any format; \texttt{auto\_generated}: derived from code"),
    ("B1", "Command in a fenced block",
     r"Fenced command \texttt{shell\_only}; tag-delimited call \texttt{xml\_tags}"),
    ("C1", "Refinement driven by a judge model",
     r"\texttt{generate\_test\_repair}, verifier type noted"),
    ("C5", "A human replaces the model",
     r"\texttt{none}; \texttt{configurable} means runtime-selectable gating policy"),
    ("D3", "Trajectory written but not resumable",
     r"\texttt{none}; trace writing alone is not a checkpoint"),
    ("E2", "Step requery versus task-level retry",
     "Task-level only; step and transport retries noted"),
    ("E3", "Per-file tool-level undo",
     r"\texttt{snapshot}; a repository reset is \texttt{git\_based}"),
    ("F1", "Caps on API calls; exit on context overflow",
     r"\texttt{max\_steps}: iterations or calls; \texttt{max\_tokens}: budget or overflow"),
    ("F2", "Budget capped in currency",
     r"\texttt{token\_budget}, currency noted"),
    ("G1", "Several isolation backends shipped",
     "Default coded, others noted"),
    ("G2", "Full access in a container versus on the host",
     r"\texttt{full} relative to G1; note states the frame"),
    ("G3", "No network configuration anywhere",
     r"\texttt{open} at medium confidence, citing the configuration surface"),
    ("G4", "Static blocklist",
     r"\texttt{static\_allowlist}, noted as a blocklist"),
    ("H1", "Optional trace exporter versus always-on log",
     "Highest available level; default noted"),
    ("H3", "Benchmarks in a sibling repository",
     r"\texttt{built\_in} only inside the pinned repositories"),
    ("M4", "Paper describes an older version",
     r"\texttt{repo}, with the version gap noted"),
    ("M5", "Which release counts as first",
     "First tag of coded line, then first commit, then paper"),
    ("M6", "Harness spans several repositories",
     "Tag, commit, and date per repository"),
    ("M7", "Stars across several repositories",
     "Flagship repository counted; others noted"),
    ("A2", "Repository instruction files inject context",
     "Noted; no new value added"),
    ("A4", "DOM element list rendered as text",
     r"\texttt{a11y\_tree}"),
    ("B5", "Agent Client Protocol",
     r"\texttt{other}, protocol named; no \texttt{acp} value added"),
    ("General", "Evidence for an absence value",
     r"The absence rule (\S\ref{subsec:absence})"),
]

WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
         9: "nine", 15: "fifteen", 19: "nineteen"}


def tt(s):
    return r"\texttt{" + s.replace("_", r"\_") + "}"


def plain_words(latex):
    s = re.sub(r"\\texttt\{([^}]*)\}", lambda m: m.group(1).replace(r"\_", "_"), latex)
    s = re.sub(r"\\S\\ref\{[^}]*\}", "S", s)
    return len(s.split())


def count_cell(d):
    if d["type"] != "enum":
        return r"\emph{" + d["type"] + "}"
    n = len(d["values"])
    return r"$\{" + str(n) + r"\}$" if d["multi"] else str(n)


def split_name(name, width=14):
    words, lines, cur = name.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def checks():
    ids = [d["id"] for d in DIMS]
    assert len(ids) == 38 and len(set(ids)) == 38, "expected 38 unique dimensions"
    assert set(SHORT) == set(ids) and set(FULL) == set(ids)
    for k, v in SHORT.items():
        assert len(v.split()) <= 8, (k, v)
    assert len(AMB) == 26
    for dims, case, res in AMB:
        assert plain_words(case) <= 10, case
        assert plain_words(res) <= 10, res
    for d in DIMS:
        if d["type"] == "enum":
            assert d["values"], d["id"]
        else:
            assert "values" not in d, d["id"]
    return ids


def dim_table():
    rows = []
    by_layer = {}
    for d in DIMS:
        by_layer.setdefault(d["layer"], []).append(d)
    for li, (layer, dims) in enumerate(by_layer.items()):
        label = split_name(LAYERS[layer])
        label[0] = f"{layer}\\enspace {label[0]}"
        assert len(label) <= len(dims), layer
        if li:
            rows.append(r"\midrule")
        for i, d in enumerate(dims):
            lay = label[i] if i < len(label) else ""
            if i >= 1 and i < len(label):
                lay = r"\phantom{" + layer + r"}\enspace " + lay
            rows.append(f"{lay} & {d['id']} & {tt(d['key'])} & {SHORT[d['id']]} & {count_cell(d)} \\\\")
    body = "\n".join(rows)
    return (
        "% Generated from the frozen schema by the Section 5 table generator; do not edit by hand.\n"
        "% One float: main.tex does not load longtable, and the 38 single-line rows fit one float.\n"
        "\\begin{table}[tbp]\n"
        "\\caption{The 38 dimensions of the frozen schema (v1.0.0), grouped by layer. \\emph{Values}: $n$ is\n"
        "the size of a single-valued enumeration; $\\{n\\}$ is the size of a multi-valued one, whose cell holds a\n"
        "set; a type name marks the four dimensions that are not enumerations. Full value sets, the judgment\n"
        "call for each layer, and two worked examples are in Supplement~S1.}\n"
        "\\label{tab:dimensions}\n"
        "\\footnotesize\n"
        "\\begin{tabular}{@{}l l l l r@{}}\n"
        "\\toprule\n"
        "Layer & ID & Key & What it records & Values \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )


def amb_table():
    rows = []
    for i, (dims, case, res) in enumerate(AMB, 1):
        rows.append(f"{i} & {dims} & \\raggedright {case} & \\raggedright {res} \\tabularnewline")
    return (
        "% All 26 ambiguities fit as a compact table, so none is deferred to the supplement.\n"
        "% Numbering follows the coding manual's ambiguity list in the replication package.\n"
        "\\begin{table}[tbp]\n"
        "\\caption{The 26 ambiguities recorded while coding the two worked systems, each resolved by a\n"
        "coding-manual rule and none by changing a value set. Numbering follows the manual.}\n"
        "\\label{tab:ambiguities}\n"
        "\\footnotesize\n"
        "\\begin{tabular}{@{}r p{0.17\\linewidth} p{0.31\\linewidth} p{0.40\\linewidth}@{}}\n"
        "\\toprule\n"
        "\\# & Dimension & Ambiguity & Resolution \\tabularnewline\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )


def layer_table(layer):
    dims = [d for d in DIMS if d["layer"] == layer]
    rows = []
    for d in dims:
        typ = f"{d['type']}, {'multi' if d['multi'] else 'single'}"
        if d["type"] == "enum":
            vals = ", ".join(tt(v) for v in d["values"])
        else:
            vals = f"no enumerated set ({d['type']})"
        rows.append(
            f"\\texttt{{{d['id']}}} & \\raggedright {d['name']} \\newline {tt(d['key'])} & "
            f"\\raggedright {FULL[d['id']]} & {typ} & \\raggedright {vals} \\tabularnewline"
        )
    n = len(dims)
    return (
        "\\begin{table}[htbp]\n"
        f"\\caption{{Layer \\texttt{{{layer}}}, {LAYERS[layer]}: {n} dimensions, with ids, names, keys, types and value\n"
        "sets verbatim from the frozen schema (v1.0.0).}\n"
        f"\\label{{tab:coding-{layer}}}\n"
        "\\footnotesize\n"
        "\\begin{tabular}{@{}l p{0.20\\linewidth} p{0.22\\linewidth} l p{0.33\\linewidth}@{}}\n"
        "\\toprule\n"
        "ID & Dimension and key & What it records & Type & Permitted values \\tabularnewline\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )


def examples_table():
    ex = {
        "swe": json.loads((REPO / "data/examples/swe-agent-1x.json").read_text(encoding="utf-8"))["coding"],
        "oh": json.loads((REPO / "data/examples/openhands.json").read_text(encoding="utf-8"))["coding"],
    }
    pick = ["A1", "C1", "B1", "B2", "E1", "G1", "G3", "H2"]  # order as in the v1 table
    key = {d["id"]: d["key"] for d in DIMS}
    rows = []
    for i in pick:
        cells = []
        for s in ("swe", "oh"):
            v = ex[s][key[i]]["value"]
            v = v if isinstance(v, list) else [v]
            cells.append(", ".join(tt(str(x)) for x in v))
        rows.append(f"\\texttt{{{i}}} & {tt(key[i])} & \\raggedright {cells[0]} & \\raggedright {cells[1]} \\tabularnewline")
    return (
        "\\begin{table}[htbp]\n"
        "\\caption{Eight of the 38 cells of each worked example, verbatim from the released worked-example\n"
        "files. Values only; the evidence, confidence, and note of every cell are in those files.}\n"
        "\\label{tab:coding-examples}\n"
        "\\footnotesize\n"
        "\\begin{tabular}{@{}l l p{0.28\\linewidth} p{0.30\\linewidth}@{}}\n"
        "\\toprule\n"
        "ID & key & SWE-agent 1.x & OpenHands \\tabularnewline\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )


def shape_sentence():
    single = [d for d in DIMS if d["type"] == "enum" and not d["multi"]]
    multi = [d for d in DIMS if d["type"] == "enum" and d["multi"]]
    other = [d for d in DIMS if d["type"] != "enum"]
    sizes = [len(d["values"]) for d in DIMS if d["type"] == "enum"]
    assert len(multi) == 15 and len(other) == 4
    types = sorted({d["type"] for d in other})
    assert types == ["date", "integer", "string"], types
    sent = (f"{WORDS[len(single)].capitalize()} dimensions are single-valued enumerations, "
            f"{WORDS[len(multi)]} hold a set, and {WORDS[len(other)]} are an integer, a date, or a string; "
            f"the enumerations range from {WORDS[min(sizes)]} to {WORDS[max(sizes)]} values.")
    return sent, (len(single), len(multi), len(other), min(sizes), max(sizes), types)


def main():
    checks()
    sentence, stats = shape_sentence()
    s5 = (HERE / "sec05_template.tex").read_text(encoding="utf-8")
    s5 = s5.replace("%%DIMTABLE%%", dim_table()).replace("%%AMBTABLE%%", amb_table()).replace("%%SHAPE%%", sentence)
    a1 = (HERE / "a1_template.tex").read_text(encoding="utf-8")
    for layer in LAYERS:
        a1 = a1.replace(f"%%TABLE_{layer}%%", layer_table(layer))
    a1 = a1.replace("%%TABLE_EXAMPLES%%", examples_table())
    assert "%%" not in s5 and "%%" not in a1
    out = sys.argv[1] if len(sys.argv) > 1 else str(REPO / "paper" / "sections")
    out = pathlib.Path(out)
    (out / "05_unified_taxonomy.tex").write_text(s5, encoding="utf-8")
    (out / "A1_coding_sheet.tex").write_text(a1, encoding="utf-8")
    print("stats single/multi/other/min/max/types:", stats)
    print("wrote", out)


if __name__ == "__main__":
    main()
