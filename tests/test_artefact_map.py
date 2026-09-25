"""Guard the generated artefact map (Supplement S5) against superseded values.

The map's descriptions are hard-coded in scripts/build_artefact_map.py, so a release rebuild or a
re-run analysis does not update them. Each literal below is a value that was once correct and has
been superseded (release 1,253 -> 1,256 systems, 47,614 -> 47,728 cells, 24,160 -> 24,228 valued
cells; multi-agent contrast +1.01 / p = 0.0003 -> +0.877 / p = 0.0013; clustering k = 9 -> 8; layer G
silence 81.7 -> 81.6). If one reappears, the map has drifted from the data.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAP = ROOT / "paper" / "sections" / "S_artefact_map.tex"
GENERATOR = ROOT / "scripts" / "build_artefact_map.py"

SUPERSEDED = {
    "1,253": r"(?<![\d,.])1,253(?![\d,])",
    "47,614": r"(?<![\d,.])47,614(?![\d,])",
    "24,160": r"(?<![\d,.])24,160(?![\d,])",
    "+1.01": r"\+1\.01(?!\d)",
    "0.0003": r"(?<![\d.])0\.0003(?!\d)",
    "k = 9": r"k\s*=\s*9(?!\d)",
    "81.7": r"(?<![\d.])81\.7(?!\d)",
    "S1--S5": r"S1--S5(?!\d)",
}


@pytest.mark.parametrize("path", [MAP, GENERATOR], ids=["generated map", "generator"])
@pytest.mark.parametrize("literal", sorted(SUPERSEDED))
def test_no_superseded_literal(path, literal):
    text = path.read_text(encoding="utf-8")
    hits = [m.start() for m in re.finditer(SUPERSEDED[literal], text)]
    assert not hits, f"superseded value {literal!r} appears in {path.name} at offsets {hits}"


def test_map_names_every_supplement_section():
    text = MAP.read_text(encoding="utf-8")
    assert "S1--S6" in text
