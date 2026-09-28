"""Tests for scripts/make_layer_exemplars.py (the layer-exemplar table and corpus.bib).

The script is run for real against the data files (no network: ``--refresh-meta`` is never passed,
so bibliographic metadata comes from the cached ``data/analysis/layer_exemplars_meta.json``), with
its two outputs redirected to ``tmp_path``. The tests check that the table has one row per value
the script's DIMENSIONS asks for, that its caption names no file path or script (house rule: the
paper body carries none), that every citation key resolves in corpus.bib or must_cite.bib, that two
runs are byte-identical, and that the committed outputs are what the script produces now.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import make_layer_exemplars as mle

COMMITTED_TEX = ROOT / "paper/tables/layer_exemplars.tex"
COMMITTED_BIB = ROOT / "paper/references/corpus.bib"
MUST_CITE = ROOT / "paper/references/must_cite.bib"


def _run(outdir: Path, monkeypatch) -> tuple[bytes, bytes]:
    outdir.mkdir(parents=True, exist_ok=True)
    tex, bib = outdir / "layer_exemplars.tex", outdir / "corpus.bib"
    monkeypatch.setattr(mle, "OUT_TEX", tex)
    monkeypatch.setattr(mle, "OUT_BIB", bib)
    monkeypatch.setattr(sys, "argv", ["make_layer_exemplars.py"])
    mle.main()
    return tex.read_bytes(), bib.read_bytes()


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    try:
        base = tmp_path_factory.mktemp("exemplars")
        first = _run(base / "a", mp)
        second = _run(base / "b", mp)
    finally:
        mp.undo()
    return first, second


def _caption(tex: str) -> str:
    m = re.search(r"\\caption\{(.*)\}\s*\n\\label\{tab:layer-exemplars\}", tex)
    assert m, "no caption before the table label"
    return m.group(1)


def _bib_keys(p: Path) -> set[str]:
    return set(re.findall(r"^@\w+\{([^,\s]+),", p.read_text(encoding="utf-8"), re.MULTILINE))


def test_script_is_deterministic(runs):
    first, second = runs
    assert first[0] == second[0], "layer_exemplars.tex differs between two runs"
    assert first[1] == second[1], "corpus.bib differs between two runs"


def test_committed_outputs_are_current(runs):
    tex, bib = runs[0]
    assert tex == COMMITTED_TEX.read_bytes()
    assert bib == COMMITTED_BIB.read_bytes()


def test_table_has_one_row_per_requested_value(runs):
    tex = runs[0][0].decode("utf-8")
    body = tex.split("\\midrule", 1)[1].split("\\bottomrule", 1)[0]
    rows = [ln for ln in body.splitlines() if ln.rstrip().endswith("\\tabularnewline")]
    assert len(rows) == sum(n for *_, n in mle.DIMENSIONS)
    assert all("\\citep{" in ln for ln in rows), "a row has no cited exemplar"


def test_caption_names_no_file_path_or_script(runs):
    cap = _caption(runs[0][0].decode("utf-8"))
    assert "\\texttt{" not in cap
    assert "\\path{" not in cap and "\\url{" not in cap
    assert not re.search(r"\w/\w|\.(py|csv|json|bib|tex)\b|scripts|data/", cap), cap


def test_every_citation_key_resolves(runs):
    tex = runs[0][0].decode("utf-8")
    cited = {k.strip() for group in re.findall(r"\\citep\{([^}]*)\}", tex) for k in group.split(",")}
    assert cited
    known = _bib_keys(COMMITTED_BIB) | _bib_keys(MUST_CITE)
    missing = sorted(cited - known)
    assert not missing, f"cited but not in corpus.bib or must_cite.bib: {missing}"
