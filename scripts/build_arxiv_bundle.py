"""Assemble a self-contained arXiv source bundle for the manuscript and verify it compiles.

    python scripts/build_arxiv_bundle.py [--out release/arxiv_v1.zip]

What arXiv receives:
  main.tex            the ACM manuscript root without the ``review`` option (no line numbers)
  sections/*.tex      only the files main.tex inputs
  tables/*.tex        only the fragments main.tex or a section inputs
  figures/*.pdf       only the figures actually included
  references/*.bib    the bibliography, plus main.bbl so arXiv need not run BibTeX
  (acmart.cls and the .bst are NOT shipped by default: arXiv's TeX Live provides acmart, and its
  upload checker scans any shipped .cls for \includegraphics and rejects the bundle over the
  class's own optional logo files; main.bbl is shipped, so no .bst is needed. --pin-class ships them.)
  anc/supplement.pdf  the supplementary material as an ancillary file
  00README.XXX        tells arXiv the main file

The bundle is compiled from scratch in a temporary directory with pdflatex -> bibtex -> pdflatex x2
before the zip is written; the build refuses if there is any error or undefined reference.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"

INPUT_RE = re.compile(r"\\input\{([^}]+)\}")
GRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
BIB_RE = re.compile(r"\\bibliography\{([^}]+)\}")


def _kpsewhich(name: str) -> pathlib.Path:
    out = subprocess.run(["kpsewhich", name], capture_output=True, text=True, check=False).stdout.strip()
    if not out:
        sys.exit(f"kpsewhich cannot find {name}")
    return pathlib.Path(out.splitlines()[-1])


def _collect(tex: pathlib.Path, seen: set[pathlib.Path]) -> None:
    """Follow every \\input from ``tex`` (relative to paper/)."""
    text = tex.read_text(encoding="utf-8")
    for m in INPUT_RE.finditer(text):
        rel = m.group(1)
        p = PAPER / (rel if rel.endswith(".tex") else rel + ".tex")
        if p not in seen and p.exists():
            seen.add(p)
            _collect(p, seen)


def _figures(files: set[pathlib.Path]) -> set[pathlib.Path]:
    figs: set[pathlib.Path] = set()
    for f in files:
        for m in GRAPHICS_RE.finditer(f.read_text(encoding="utf-8")):
            name = m.group(1)
            cand = [PAPER / "figures" / name, PAPER / "figures" / (name + ".pdf"), PAPER / name]
            hit = next((c for c in cand if c.exists() and c.is_file()), None)
            if hit is None:
                sys.exit(f"figure not found: {name} (from {f.name})")
            figs.add(hit)
    return figs


def _run(cmd: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "release" / "arxiv_v1.zip"))
    ap.add_argument("--keep-review", action="store_true", help="keep the acmart review option (line numbers)")
    ap.add_argument("--pin-class", action="store_true",
                    help="also ship acmart.cls and ACM-Reference-Format.bst (arXiv's checker rejects this)")
    a = ap.parse_args(argv)

    main_tex = PAPER / "main.tex"
    supplement_pdf = PAPER / "supplement.pdf"
    if not supplement_pdf.exists():
        sys.exit("paper/supplement.pdf missing; build the supplement first")

    files: set[pathlib.Path] = set()
    _collect(main_tex, files)
    figs = _figures(files | {main_tex})
    bibs = [PAPER / (b + ".bib") for m in BIB_RE.finditer(main_tex.read_text(encoding="utf-8"))
            for b in m.group(1).split(",")]

    work = pathlib.Path(tempfile.mkdtemp(prefix="arxiv_"))
    try:
        # 1. sources
        text = main_tex.read_text(encoding="utf-8")
        if not a.keep_review:
            text = re.sub(r"\\documentclass\[([^\]]*)\]\{acmart\}",
                          lambda m: "\\documentclass[{}]{{acmart}}".format(",".join(
                              o for o in m.group(1).split(",") if o.strip() != "review")), text, count=1)
        (work / "main.tex").write_text(text, encoding="utf-8")
        for f in files:
            dst = work / f.relative_to(PAPER)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
        (work / "figures").mkdir(exist_ok=True)
        for f in figs:
            shutil.copy2(f, work / "figures" / f.name)
        (work / "references").mkdir(exist_ok=True)
        for b in bibs:
            shutil.copy2(b, work / "references" / b.name)
        if a.pin_class:
            shutil.copy2(_kpsewhich("acmart.cls"), work / "acmart.cls")
            shutil.copy2(_kpsewhich("ACM-Reference-Format.bst"), work / "ACM-Reference-Format.bst")
        (work / "anc").mkdir()
        shutil.copy2(supplement_pdf, work / "anc" / "supplement.pdf")
        (work / "00README.XXX").write_text("main.tex toplevelfile\n", encoding="utf-8")

        # 2. compile from scratch, as arXiv does
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["bibtex", "main"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
            r = _run(cmd, work)
            if r.returncode != 0 and cmd[0] == "bibtex" and "error message" in r.stdout:
                sys.exit("bibtex failed:\n" + r.stdout[-2000:])
        log = (work / "main.log").read_text(encoding="utf-8", errors="replace")
        errors = [ln for ln in log.splitlines() if ln.startswith("!")]
        undefined = [ln for ln in log.splitlines()
                     if "undefined" in ln.lower() and "Font shape" not in ln and "TotPages" not in ln]
        pages = re.findall(r"Output written on main.pdf \((\d+) pages", log)
        if errors or undefined or not pages:
            sys.exit("clean build failed:\n" + "\n".join(errors[:5] + undefined[:5]))
        for junk in ("main.aux", "main.log", "main.out", "main.blg", "main.fls", "main.fdb_latexmk", "main.pdf"):
            (work / junk).unlink(missing_ok=True)

        # 3. zip
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(work.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(work).as_posix())
        n = sum(1 for p in work.rglob("*") if p.is_file())
        print(f"arXiv bundle: {out} ({out.stat().st_size:,} bytes, {n} files); clean build {pages[-1]} pages")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
