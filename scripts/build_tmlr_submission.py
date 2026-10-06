r"""Build the anonymised TMLR submission: main.pdf and supplement.pdf with author and links masked.

    python scripts/build_tmlr_submission.py [--out release/tmlr_submission]

TMLR reviews double-blind. The named preprint build (paper/main_tmlr.tex) prints the author, and the
manuscript links the OSF registration, the Zenodo deposit, the GitHub repository and the Hugging Face
mirror, each of which names the author. This script copies paper/ to a temporary directory, switches
tmlr to its anonymous mode, masks every identifying string in the sources and the supplement, compiles
both documents from scratch (pdflatex -> bibtex -> pdflatex x2), and refuses to write the output if any
identifying string survives in the PDF text, or if there is any LaTeX error or undefined reference.
The repository sources are never modified.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
MASK = "[anonymised for review]"

# Ordered: longest first, so a DOI URL is masked whole rather than leaving a stub.
PATTERNS = [
    r"https?://doi\.org/10\.17605/OSF\.IO/AB2WN",
    r"doi:10\.17605/OSF\.IO/AB2WN",
    r"10\.17605/OSF\.IO/AB2WN",
    r"https?://osf\.io/ab2wn/?",
    r"osf\.io/ab2wn",
    r"osf\.io/vkjer",
    r"https?://doi\.org/10\.5281/zenodo\.2303135[45]",
    r"doi:10\.5281/zenodo\.2303135[45]",
    r"10\.5281/zenodo\.2303135[45]",
    r"https?://harness-db\.github\.io/harness-db/?\S*",
    r"harness-db\.github\.io/harness-db",
    r"https?://github\.com/harness-db/harness-db\S*",
    r"github\.com/harness-db/harness-db",
    r"https?://huggingface\.co/datasets/bhaskar-ai/harness-db",
    r"huggingface\.co/datasets/bhaskar-ai/harness-db",
    r"bhaskar-ai",
    r"gurrambhaskar\.ai@gmail\.com",
]
LEAK = re.compile(r"gurram|bhaskar|ab2wn|zenodo\.2303|harness-db/harness-db|harness-db\.github", re.IGNORECASE)


def _mask(text: str) -> str:
    for pat in PATTERNS:
        text = re.sub(pat, MASK, text)
    return text


def _compile(work: pathlib.Path, root: str) -> pathlib.Path:
    for cmd in (["pdflatex", "-interaction=nonstopmode", f"{root}.tex"], ["bibtex", root],
                ["pdflatex", "-interaction=nonstopmode", f"{root}.tex"],
                ["pdflatex", "-interaction=nonstopmode", f"{root}.tex"]):
        subprocess.run(cmd, cwd=work, capture_output=True, text=True, check=False)
    log = (work / f"{root}.log").read_text(encoding="utf-8", errors="replace")
    errors = [ln for ln in log.splitlines() if ln.startswith("!")]
    undefined = [ln for ln in log.splitlines()
                 if "undefined" in ln.lower() and "Font shape" not in ln and "TotPages" not in ln]
    if errors or undefined:
        sys.exit(f"{root}: build failed\n" + "\n".join(errors[:5] + undefined[:5]))
    return work / f"{root}.pdf"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "release" / "tmlr_submission"))
    a = ap.parse_args(argv)

    work = pathlib.Path(tempfile.mkdtemp(prefix="tmlr_anon_"))
    try:
        shutil.copytree(PAPER, work, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("*.aux", "*.log", "*.bbl", "*.blg", "*.out",
                                                      "*.fls", "*.fdb_latexmk", "*.pdf.tmp"))
        for tex in list(work.glob("*.tex")) + list((work / "sections").glob("*.tex")) \
                + list((work / "tables").glob("*.tex")):
            tex.write_text(_mask(tex.read_text(encoding="utf-8")), encoding="utf-8")
        for bib in (work / "references").glob("*.bib"):
            bib.write_text(_mask(bib.read_text(encoding="utf-8")), encoding="utf-8")

        mt = work / "main_tmlr.tex"
        t = mt.read_text(encoding="utf-8").replace(r"\usepackage[preprint]{tmlr}", r"\usepackage{tmlr}")
        t = re.sub(r"\\author\{.*?\}\n", r"\\author{Anonymous authors}\n", t, count=1)
        mt.write_text(t, encoding="utf-8")
        sp = work / "supplement.tex"
        s = sp.read_text(encoding="utf-8")
        s = re.sub(r"\\author\{[^}]*\}", r"\\author{Anonymous authors}", s, count=1)
        s = re.sub(r"\\email\{[^}]*\}", "", s)
        s = s.replace(r"\documentclass[", r"\documentclass[anonymous,", 1) if "anonymous" not in s else s
        sp.write_text(s, encoding="utf-8")

        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for root, name in (("main_tmlr", "main.pdf"), ("supplement", "supplement.pdf")):
            pdf = _compile(work, root)
            text = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", check=True).stdout
            leaks = sorted({m.group(0) for m in LEAK.finditer(text)})
            if leaks:
                sys.exit(f"{name}: identifying strings survive in the PDF: {leaks}")
            shutil.copy2(pdf, out / name)
            pages = re.findall(r"Output written on .*?\((\d+) pages",
                               (work / f"{root}.log").read_text(encoding="utf-8", errors="replace"))
            print(f"{out / name}: {pages[-1] if pages else '?'} pages, anonymised, 0 errors")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
