"""Tests for scripts/system_card.py (the per-system Markdown cell card).

Run against the real release in data/. The tests check that the swe-agent card has one table row
per dimension (38), that every coded row carries its quote, that commit-pinned locators become links
into the repository at that commit, that not_reported rows show the state and nothing in the quote or
locator columns, that the wrong-cell link is prefilled with the system and dimension, that rendering
is byte-identical across runs, and that --top ranks by stars with one card per repository.
"""

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import system_card as sc

from harnessdb.core import cell_state, split_evidence

ROW = re.compile(r"^\| (?P<id>[A-HM]\d) \| `(?P<key>[a-z_]+)` \|")


@pytest.fixture(scope="module")
def data():
    dims, layers = sc.load_schema()
    return dims, layers, sc.load_systems(), sc.load_frame(), sc.load_field_silence()


def _card(data, sid):
    dims, layers, systems, frame, silence = data
    return sc.render_card(systems[sid], dims, layers, frame.get(sid), silence)


def _rows(card):
    out = {}
    for line in card.splitlines():
        m = ROW.match(line)
        if m:
            # split on unescaped pipes only
            cols = [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]
            out[m.group("key")] = cols
    return out


def test_swe_agent_card_has_38_rows(data):
    rows = _rows(_card(data, "swe-agent"))
    assert len(rows) == 38
    assert set(rows) == {d["key"] for d in data[0]}


def test_every_coded_row_has_its_quote(data):
    dims, _, systems, _, _ = data
    s = systems["swe-agent"]
    rows = _rows(_card(data, "swe-agent"))
    n_coded = 0
    for d in dims:
        cell = s["coding"][d["key"]]
        if cell_state(cell) != "coded":
            continue
        n_coded += 1
        quote, _ = split_evidence(cell["evidence"])
        assert quote, d["key"]
        assert rows[d["key"]][4] == f"“{sc.md(quote)}”"
    assert n_coded > 0


def test_commit_locators_become_links_at_the_pinned_commit(data):
    rows = _rows(_card(data, "swe-agent"))
    loc = rows["execution_isolation"][5]
    full = "0f3acafacabc0def8cc76b4e48acb4b6cf302cb9"
    assert loc == ("[docs/background/architecture.md@0f3acafacabc](https://github.com/swe-agent/"
                   f"swe-agent/blob/{full}/docs/background/architecture.md)")


def test_locator_forms():
    repo = ("o", "r", "")
    sha = "f14a9c065ca8" + "0" * 28
    assert sc.locator_link("src/sandbox/config.py:66@f14a9c065ca8", repo, sha) == (
        f"[src/sandbox/config.py:66@f14a9c065ca8](https://github.com/o/r/blob/{sha}/"
        "src/sandbox/config.py#L66)")
    assert sc.locator_link("a/b.py:5-9@abcdef1", repo, None).endswith("/blob/abcdef1/a/b.py#L5-L9)")
    assert sc.locator_link("README.md (Tools)@abcdef1", repo, None).endswith("/blob/abcdef1/README.md)")
    bare = sc.locator_link("README.md", repo, sha)
    assert bare.endswith(sc.DAGGER) and f"/blob/{sha}/README.md" in bare
    assert sc.locator_link("README.md", repo, None) == "README.md"          # no commit known: no link
    assert sc.locator_link("paper Sec. 3.2", repo, sha) == "paper Sec. 3.2"  # never invented
    assert sc.locator_link("paper arXiv:2308.08155 Sec. 2.1", None, None).endswith(
        "(https://arxiv.org/abs/2308.08155)")
    assert sc.locator_link("repo metadata@eb41269", repo, sha) == "repo metadata@eb41269"


def test_not_reported_rows_show_state_and_nothing_else(data):
    dims, _, systems, _, _ = data
    s = systems["swe-agent"]
    rows = _rows(_card(data, "swe-agent"))
    silent = [d["key"] for d in dims if cell_state(s["coding"][d["key"]]) == "not_reported"]
    assert silent
    for key in silent:
        cols = rows[key]
        assert cols[2] == "`not_reported`"
        assert cols[3] == cols[4] == cols[5] == ""        # confidence, quote, locator
        note = s["coding"][key].get("note")
        assert cols[6] == (sc.md(note) if note else "")   # only the release's own note


def test_wrong_cell_link_is_prefilled(data):
    rows = _rows(_card(data, "swe-agent"))
    url = re.search(r"\((https://github\.com/[^)]+)\)", rows["execution_isolation"][7]).group(1)
    q = parse_qs(urlparse(url).query)
    assert urlparse(url).path == "/harness-db/harness-db/issues/new"
    assert q["template"] == ["wrong_cell.yml"]
    assert q["system"] == ["swe-agent"]
    assert q["dimension"] == ["G1 execution_isolation"]
    assert q["current"] == ["container"]
    card = _card(data, "swe-agent")
    assert "https://harness-db.github.io/harness-db/#system=swe-agent" in card
    assert "Is a cell wrong? Open a *wrong cell* issue:" in card


def test_deterministic(data):
    assert _card(data, "swe-agent") == _card(data, "swe-agent")


def test_top_by_stars(data):
    _, _, systems, frame, _ = data
    top = sc.top_systems(systems, frame, 20)
    ids = [sid for sid, _ in top]
    assert len(ids) == 20 == len(set(ids))
    stars = [sc.stars_of(systems[i], frame.get(i)) for i in ids]
    assert stars == sorted(stars, reverse=True)
    for i in ids:
        assert sc.weight_of(frame.get(i)) > 0
        assert sc.parse_repo(sc.repo_url(systems[i], frame.get(i)))
    repos = [sc._norm_repo(sc.repo_url(systems[i], frame.get(i))) for i in ids]
    assert len(repos) == len(set(repos))
    assert top == sc.top_systems(systems, frame, 20)


def test_parse_pinned():
    assert sc.parse_pinned("v1.1.0 @ 0f3acafacabc0def8cc76b4e48acb4b6cf302cb9 (2025-05-22)") == (
        "v1.1.0", "0f3acafacabc0def8cc76b4e48acb4b6cf302cb9", "2025-05-22")
    assert sc.parse_pinned("tag:v2.1.252 f275fa282e76 2026-08-31") == (
        "v2.1.252", "f275fa282e76", "2026-08-31")
    assert sc.parse_pinned(None) == (None, None, None)
