"""Post-unblinding adjudication of the human audit's disagreements (protocol section 4.4).

    python scripts/human_audit_adjudicate.py

Reads data/audit/results.json (the disagreements written by `human_audit.py --analyse`) and rebuilds,
with `code_system.assemble_bundle`, the exact evidence bundle the model coded each audited system from.
Writes data/audit/adjudication.csv (one row per disagreement) and data/audit/adjudication.json (counts).

The question the protocol asks first is mechanical, so it is answered mechanically: was the evidence the
human cited inside the text the model was sent?

  * A human evidence fragment is a piece of `human_evidence` split on "||" and " | ", with search
    commands (fragments containing "grep" or "->") dropped, whitespace squashed and case folded; it
    counts when it is at least 15 characters long.
  * A cited file is a path in `human_locator` (`path:LINE@hash` or `path@hash`); it is visible to the
    model when the bundle sent carries a code section `### <path> (first N lines)` and, if a line is
    cited, LINE <= N.

  evidence_in_bundle   a fragment occurs in the bundle sent, or a cited file-and-line was visible
  bundle_gap           neither; subtypes:
      cut_by_cap         a fragment occurs in the fetched evidence but past the character budget
      beyond_excerpt     a cited file was sent, but only its first N lines and the cited line is later
      not_in_bundle      the fetched evidence never contained it (file not selected, or not fetched)

Within evidence_in_bundle the protocol's remaining classes (model misread, manual ambiguity, human
error) need a reading of the case and are not assigned here: a not_reported-against-value disagreement
with the evidence in the bundle is reported as `model_missed_evidence`, and a value disagreement with the
evidence in the bundle as `value_disagreement_evidence_shared`. The reconstruction is validated first:
the share of the model's own evidence quotes, for the audited systems, found in the rebuilt bundles.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import code_system as cs

AUDIT = ROOT / "data" / "audit"


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


PROBE = 60  # characters of a fragment used for matching


def fragments(evidence: str, probe: int = PROBE) -> list[str]:
    """Match probes: each quoted piece of an evidence string, without its wrapper or trailing locator."""
    out = []
    for f in re.split(r"\|\||\s\|\s", evidence or ""):
        f = squash(f)
        f = re.sub(r"\s*\((?:paper|readme|repo|docs?|[^()]*\.(?:md|py|ts|js|json|ya?ml|toml|txt))[^()]*\)\s*$",
                   "", f)                     # trailing locator such as "(paper Sec. 3)" or "(README.md)"
        f = f.strip("`'\"“”‘’ .")
        if len(f) >= 15 and "grep" not in f and "->" not in f:
            out.append(f[:probe])
    return out


def cited_files(locator: str) -> list[tuple[str, int | None]]:
    out = []
    for part in re.split(r";", locator or ""):
        m = re.match(r"\s*([^\s:@;]+?\.[A-Za-z0-9_]+|[^\s:@;]+/)(?::(\d+)(?:-\d+)?)?@", part)
        if m:
            out.append((m.group(1).lstrip("./"), int(m.group(2)) if m.group(2) else None))
    return out


def sections(text: str) -> dict[str, int]:
    """Code sections in a bundle: path -> number of lines included."""
    out = {}
    for m in re.finditer(r"^### (.+?) \(first (\d+) lines\)", text, re.MULTILINE):
        out[m.group(1).strip().lstrip("./")] = int(m.group(2))
    for m in re.finditer(r"^### (.+?)\s*$", text, re.MULTILINE):
        out.setdefault(m.group(1).strip().lstrip("./"), 10**9)
    return out


def full_evidence(row: dict) -> str:
    """Everything fetched for the system, before the character budget was applied."""
    parts, _ = cs.collect_parts(row)
    return "\n".join(p.text for p in parts)


def main() -> None:
    res = json.loads((AUDIT / "results.json").read_text(encoding="utf-8"))
    with (ROOT / "data" / "coding_frame.csv").open(encoding="utf-8") as fh:
        frame = {r["system_id"]: r for r in csv.DictReader(fh)}
    with (AUDIT / "sample.csv").open(encoding="utf-8") as fh:
        sample = {r["system_id"] for r in csv.DictReader(fh)}
    with (AUDIT / "model_answers.csv").open(encoding="utf-8") as fh:
        model = list(csv.DictReader(fh))

    sent, fetched = {}, {}
    for sid in sorted(sample):
        row = frame[sid]
        sent[sid] = cs.assemble_bundle(row).text
        fetched[sid] = full_evidence(row)

    # Reconstruction check: are the model's own quotes in the bundle rebuilt for it?
    found = total = 0
    for m in model:
        for f in fragments(m.get("model_evidence", "")):
            total += 1
            found += f in squash(sent[m["system_id"]])
    recon = {"model_quote_fragments": total, "found_in_rebuilt_bundle": found,
             "share": round(found / total, 4) if total else None}

    rows, counts, by_type = [], Counter(), Counter()
    for d in res["disagreements"]:
        sid = d["system_id"]
        s_sent, s_all = squash(sent[sid]), squash(fetched[sid])
        frs = fragments(d.get("human_evidence", ""))
        files = cited_files(d.get("human_locator", ""))
        sec = sections(sent[sid])
        frag_sent = any(f in s_sent for f in frs)
        file_sent = any(p in sec and (ln is None or ln <= sec[p]) for p, ln in files)
        if frag_sent or file_sent:
            cls = "evidence_in_bundle"
            both_coded = d["model_label"] not in ("NR", "UNRESOLVED") and d["human_label"] not in ("NR", "UNRESOLVED")
            sub = "value_disagreement_evidence_shared" if both_coded else (
                "model_unresolved" if d["model_label"] == "UNRESOLVED" else "model_missed_evidence")
        else:
            cls = "bundle_gap"
            if any(f in s_all for f in frs):
                sub = "cut_by_cap"
            elif any(p in sec and ln is not None and ln > sec[p] for p, ln in files):
                sub = "beyond_excerpt"
            else:
                sub = "not_in_bundle"
        counts[(cls, sub)] += 1
        by_type[(d["type"], cls)] += 1
        rows.append({"cell_id": d["cell_id"], "dim_id": d["dim_id"], "stratum": d["stratum"],
                     "type": d["type"], "model_label": d["model_label"], "human_label": d["human_label"],
                     "adjudication": cls, "detail": sub, "human_fragments": len(frs),
                     "human_files": ";".join(f"{p}:{ln or ''}" for p, ln in files)})

    with open(AUDIT / "adjudication.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    gap = sum(v for (c, _), v in counts.items() if c == "bundle_gap")
    out = {
        "generated_by": "scripts/human_audit_adjudicate.py",
        "reconstruction_check": recon,
        "disagreements": n,
        "bundle_gap": gap,
        "evidence_in_bundle": n - gap,
        "by_class": {f"{c}|{s}": v for (c, s), v in sorted(counts.items())},
        "by_type_and_class": {f"{t}|{c}": v for (t, c), v in sorted(by_type.items())},
        "note": ("classes are assigned mechanically from the rebuilt bundles; model misread, manual "
                 "ambiguity and human error within evidence_in_bundle are not separated"),
    }
    # Sensitivity of the headline split, and of the reconstruction check, to the probe length.
    sens = {}
    for probe in (30, 60, 100):
        gap_p = 0
        for d in res["disagreements"]:
            sid = d["system_id"]
            s_sent, sec = squash(sent[sid]), sections(sent[sid])
            hit = any(f in s_sent for f in fragments(d.get("human_evidence", ""), probe)) or any(
                pth in sec and (ln is None or ln <= sec[pth])
                for pth, ln in cited_files(d.get("human_locator", "")))
            gap_p += not hit
        frs = [(m["system_id"], f) for m in model for f in fragments(m.get("model_evidence", ""), probe)]
        ok = sum(f in squash(sent[sid]) for sid, f in frs)
        sens[str(probe)] = {"bundle_gap": gap_p, "evidence_in_bundle": n - gap_p,
                            "reconstruction_share": round(ok / len(frs), 4) if frs else None}
    out["probe_sensitivity"] = sens
    # Accuracy once the cells whose human evidence the model was never sent are set aside: a measure of
    # reading given the bundle, not of the released coding, which is what pooled accuracy measures.
    pooled = res["pooled"]
    k, m_ = pooled["n_correct"], pooled["n_ref"] - gap
    out["accuracy_excluding_bundle_gaps"] = {"n_correct": k, "n": m_, "share": round(k / m_, 4)}
    (AUDIT / "adjudication.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
