"""Tests for scripts/build_explorer.py - the single-file static explorer (explorer/index.html).

The page is built once from the real release into a temporary directory (it never touches
explorer/index.html), then checked three ways: the embedded payload decoded in Python, the HTML
parsed as one self-contained document, and - when node is on the PATH - the page's own JavaScript
data layer run against the embedded payload, through the same DecompressionStream path a browser
uses.
"""
from __future__ import annotations

import base64
import gzip
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_explorer as be

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
        "track", "wbr"}


@pytest.fixture(scope="module")
def release():
    return json.loads((ROOT / "data" / "systems.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dims():
    return json.loads((ROOT / "schema" / "dimensions.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("explorer") / "index.html"
    info = be.build(out_path=out)
    return {"info": info, "path": out, "html": out.read_text(encoding="utf-8")}


def _payload(page: str) -> dict:
    m = re.search(r'<script id="hdb-data" type="application/octet-stream" '
                  r'data-encoding="gzip\+base64">([A-Za-z0-9+/=]+)</script>', page)
    assert m, "embedded payload not found"
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))).decode("utf-8"))


@pytest.fixture(scope="module")
def payload(built):
    return _payload(built["html"])


# ------------------------------------------------------------------------------ the build


def test_build_succeeds_and_embeds(built):
    info = built["info"]
    assert info["mode"] == "embedded"
    assert info["payload_b64_bytes"] <= be.EMBED_LIMIT
    assert built["path"].stat().st_size == info["bytes"] < 8_500_000
    assert not (built["path"].parent / "data.json").exists()


def test_rebuild_is_byte_identical_and_not_rewritten(built):
    again = be.build(out_path=built["path"])
    assert again["changed"] is False
    assert built["path"].read_text(encoding="utf-8") == built["html"]


def test_main_cli(tmp_path, capsys):
    assert be.main(["--out", str(tmp_path / "index.html")]) == 0
    assert "data embedded" in capsys.readouterr().out
    assert (tmp_path / "index.html").stat().st_size > 1_000_000


# ------------------------------------------------------------------------------ the payload


def test_embedded_record_count_equals_release(payload, release):
    assert len(payload["systems"]) == len(release) == payload["meta"]["n_systems"]
    assert [s["i"] for s in payload["systems"]] == [s["id"] for s in release]


def test_every_dimension_key_is_a_facet(payload, dims):
    keys = [d["key"] for d in dims["dimensions"]]
    assert [d["key"] for d in payload["dims"]] == keys
    assert len(keys) == 38
    handled = {"enum", "integer", "date", "string"}
    assert all(d["type"] in handled for d in payload["dims"])
    # every system carries one cell per facet, in schema order
    assert all(len(s["c"]) == len(keys) for s in payload["systems"])
    assert {la["id"] for la in payload["layers"]} == {d["layer"] for d in payload["dims"]}


def test_cell_states_survive_the_encoding(payload, release, dims):
    keys = [d["key"] for d in dims["dimensions"]]
    want = {0: 0, 1: 0, 2: 0}
    for s in release:
        for k in keys:
            c = s["coding"][k]
            want[2 if c.get("unresolved") else 1 if c.get("not_reported") else 0] += 1
    got = {0: 0, 1: 0, 2: 0}
    for s in payload["systems"]:
        for cell in s["c"]:
            got[cell[0]] += 1
    assert got == want
    assert want[2] > 0 and want[1] > 0  # all three states really occur in the release


def test_values_quotes_and_locators_round_trip(payload, release, dims):
    keys = [d["key"] for d in dims["dimensions"]]
    for src, enc in zip(release, payload["systems"]):
        for k, cell in zip(keys, enc["c"]):
            c = src["coding"][k]
            if cell[0] == 0:
                assert cell[1] == c["value"], (src["id"], k)
            ev = c.get("evidence") or ""
            quote = cell[3] if len(cell) > 3 else None
            loc = cell[4] if len(cell) > 4 else None
            if ev:
                rebuilt = f'"{quote}" ({loc})' if loc else quote
                assert rebuilt == ev.strip(), (src["id"], k)


def test_split_evidence():
    assert be.split_evidence('"a (b)" said" (README.md:3@abc1234)') == ('a (b)" said',
                                                                         "README.md:3@abc1234")
    assert be.split_evidence("README.md") == ("README.md", "")
    assert be.split_evidence("") == ("", "")


def test_pinned_sha_and_repo_link(payload, release):
    by_id = {s["i"]: s for s in payload["systems"]}
    with_sha = [s for s in payload["systems"] if s.get("sha")]
    assert len(with_sha) > 900
    for s in with_sha:
        assert re.fullmatch(r"[0-9a-f]{7,40}", s["sha"])
    one = next(s for s in release if s["id"] == "1code")
    assert by_id["1code"]["sha"] in one["coding"]["pinned_version"]["value"]
    assert be.pinned_sha({"coding": {"pinned_version": {"not_reported": True}},
                          "version_label": "main@82709de050e1"}) == ("82709de050e1",
                                                                     "main@82709de050e1")
    assert be.pinned_sha({"coding": {}, "version_label": "v1.2.0"}) == (None, None)


def test_integer_bins_match_the_descriptives(payload, release):
    ad = pytest.importorskip("analyse_descriptives")
    for dim in (d for d in payload["dims"] if d["type"] == "integer"):
        raw = [s["coding"][dim["key"]]["value"] for s in release
               if s["coding"][dim["key"]].get("value") is not None
               and not s["coding"][dim["key"]].get("not_reported")
               and not s["coding"][dim["key"]].get("unresolved")]
        theirs = ad._numeric_bin_labels([float(x) for x in raw])
        assert {k: v for k, v in dim["bins"].items()} == {str(int(k)): v for k, v in theirs.items()}
        assert set(dim["binOrder"]) == set(theirs.values())


def test_every_paper_resolves_to_a_title(payload, release):
    titles = {p[0]: p[1] for p in payload["papers"]}
    for s in release:
        for pid in s["papers"]:
            assert titles[pid].strip(), pid


def test_footer_metadata(built, payload):
    page, meta = built["html"], payload["meta"]
    assert "CC BY 4.0" in page and "creativecommons.org/licenses/by/4.0" in page
    assert f"HARNESS-DB v{meta['version']}" in page
    for key in ("card_url", "paper_url", "repo_url"):
        assert f'href="{meta[key]}"' in page
    assert "Cite:" in page and "Gurram" in page
    # the legend defines the two silent states once, in the wording of the coding manual
    assert page.count("= sources read and silent") == 1
    assert page.count("= the coder could not settle it (excluded from rates)") == 1


# ------------------------------------------------------------------------------ the document


class _Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.counts: dict[str, int] = {}
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.decl: list[str] = []
        self.first = None
        self.external: list[str] = []
        self.style = ""
        self._in_style = False

    def handle_decl(self, decl):
        self.decl.append(decl)
        self.first = self.first or "decl"

    def handle_starttag(self, tag, attrs):
        self.first = self.first or tag
        a = dict(attrs)
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "script" and a.get("src"):
            self.external.append(a["src"])
        if tag == "link" and "stylesheet" in (a.get("rel") or ""):
            self.external.append(a.get("href", ""))
        if tag in ("img", "iframe", "source") and a.get("src"):
            self.external.append(a["src"])
        self._in_style = tag == "style"
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        self._in_style = False
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"</{tag}> closes <{self.stack[-1] if self.stack else None}>")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
            return
        self.stack.pop()

    def handle_data(self, data):
        if self._in_style:
            self.style += data


def test_html_is_one_self_contained_document(built):
    doc = _Doc()
    doc.feed(built["html"])
    doc.close()
    assert doc.first == "decl" and doc.decl == ["DOCTYPE html"]
    for tag in ("html", "head", "body", "title", "main", "style"):
        assert doc.counts.get(tag) == 1, tag
    assert doc.counts["script"] == 3  # data, core, ui
    assert not doc.errors, doc.errors[:5]
    assert doc.stack == [], f"unclosed: {doc.stack}"
    assert len(doc.ids) == len(set(doc.ids)), "duplicate ids"
    assert doc.external == [], f"external resources: {doc.external}"
    assert "@import" not in doc.style and not re.search(r"url\(\s*['\"]?https?:", doc.style)
    assert built["html"].rstrip().endswith("</html>")
    assert "<meta name=\"viewport\"" in built["html"]


def test_sidecar_mode_when_payload_is_too_large(tmp_path, release, dims):
    small = tmp_path / "systems.json"
    small.write_text(json.dumps(release[:5]), encoding="utf-8")
    out = tmp_path / "site" / "index.html"
    info = be.build(systems_path=small, out_path=out, embed_limit=0)
    assert info["mode"] == "sidecar" and info["n_systems"] == 5
    page = out.read_text(encoding="utf-8")
    assert 'data-src="data.json"' in page and "gzip+base64" not in page
    side = json.loads((out.parent / "data.json").read_text(encoding="utf-8"))
    assert len(side["systems"]) == 5
    # going back under the limit removes the stale sidecar
    assert be.build(systems_path=small, out_path=out)["mode"] == "embedded"
    assert not (out.parent / "data.json").exists()


def test_uncoded_cell_fails_loudly(tmp_path, release):
    bad = json.loads(json.dumps(release[:1]))
    bad[0]["coding"]["tool_count"] = {"value": None, "not_reported": False, "coder": "x"}
    p = tmp_path / "systems.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="tool_count"):
        be.build(systems_path=p, out_path=tmp_path / "index.html")


# ------------------------------------------------------------------------------ the Makefile


def test_makefile_rebuilds_the_explorer_with_figures():
    raw = (ROOT / "Makefile").read_bytes()
    assert b"\r\n" in raw and raw.count(b"\n") == raw.count(b"\r\n"), "Makefile must stay CRLF"
    mk = raw.decode("utf-8")
    block = mk.split("ANALYSIS_SCRIPTS =")[1].split("\r\n\r\n")[0]
    lines = [ln.rstrip("\r") for ln in block.splitlines()[1:]]
    assert any(ln.strip().rstrip(" \\") == "scripts/build_explorer.py" for ln in lines)
    assert all(ln.startswith("\t") for ln in lines)
    assert all(ln.endswith(" \\") for ln in lines[:-1]) and not lines[-1].endswith("\\")


# ------------------------------------------------------------------------------ the JavaScript

SMOKE_JS = r"""
const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const grab = id => {
  const a = html.indexOf('<script id="' + id + '"');
  if (a < 0) throw new Error('missing script ' + id);
  const b = html.indexOf('>', a) + 1;
  return html.slice(b, html.indexOf('</script>', b));
};
const ctx = vm.createContext({atob, Blob, Response, DecompressionStream, URLSearchParams});
vm.runInContext(grab('hdb-core'), ctx);
new Function(grab('hdb-ui'));   // the UI script must at least parse
const HDB = ctx.HDB;
(async () => {
  const d = HDB.prepare(await HDB.decode(grab('hdb-data')));
  const all = HDB.filter(d, HDB.parseHash('', d));
  const hash = '#q=agent&f.multi_agent_topology=single&f.multi_agent_topology=!not_reported'
    + '&f.execution_isolation=!unresolved&sort=-%23silent&p=2&cols=tool_count,%23repo';
  const st = HDB.parseHash(hash, d);
  const some = HDB.filter(d, st);
  const again = HDB.filter(d, HDB.parseHash('#' + HDB.stateToHash(st), d));
  const nr = HDB.filter(d, HDB.parseHash('#f.network_policy=!not_reported', d)).length;
  const sil = HDB.silence(d, all);
  const csv = HDB.toCSV(d, all).trim().split('\r\n');
  const facets = {};
  d.dims.forEach(dim => { facets[dim.key] = dim.facetOrder; });
  const counts = HDB.facetCounts(d, HDB.parseHash('', d), 'multi_agent_topology');
  process.stdout.write(JSON.stringify({
    n: d.systems.length, all: all.length, some: some.length,
    sameAfterRoundTrip: JSON.stringify(some.map(s => s.i)) === JSON.stringify(again.map(s => s.i)),
    cols: st.cols, sort: st.sort, page: st.page, nr: nr,
    total: sil.total, layers: sil.layers.map(l => l.id), csvRows: csv.length,
    csvHead: csv[0].split(','), facets: facets,
    countSum: Object.values(counts).reduce((a, b) => a + b, 0),
    system: HDB.parseHash('#system=1code', d).system,
    pin: HDB.pinUrl(d.byId['1code']),
    loc: HDB.locatorUrl(d.byId['1code'], 'src/a.ts:3-9@9f1bc76')
  }));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
def test_node_smoke(built, tmp_path, release, dims):
    script = tmp_path / "smoke.js"
    script.write_text(SMOKE_JS, encoding="utf-8")
    run = subprocess.run(["node", str(script), str(built["path"])], capture_output=True,
                         text=True, encoding="utf-8", timeout=120, check=False)
    assert run.returncode == 0, run.stderr
    r = json.loads(run.stdout)
    keys = [d["key"] for d in dims["dimensions"]]
    assert r["n"] == r["all"] == len(release)
    assert 0 < r["some"] < len(release) and r["sameAfterRoundTrip"]
    assert r["cols"] == ["tool_count", "#repo"] and r["sort"] == {"key": "#silent", "dir": -1}
    assert r["page"] == 2
    assert r["nr"] == sum(1 for s in release if s["coding"]["network_policy"].get("not_reported"))
    assert sorted(r["facets"]) == sorted(keys)
    for key, order in r["facets"].items():
        assert order[-2:] == ["!not_reported", "!unresolved"], key
        assert len(order) > 2, key
    want_nr = sum(1 for s in release for k in keys if s["coding"][k].get("not_reported")
                  and not s["coding"][k].get("unresolved"))
    want_un = sum(1 for s in release for k in keys if s["coding"][k].get("unresolved"))
    assert r["total"]["nr"] == want_nr and r["total"]["un"] == want_un
    assert r["total"]["base"] == len(release) * len(keys) - want_un
    assert r["layers"] == [la["id"] for la in dims["layers"]]
    assert r["csvRows"] == len(release) + 1 and r["csvHead"][-len(keys):] == keys
    assert r["countSum"] == len(release)  # single-valued: one facet token per system
    assert r["system"] == "1code"
    assert r["pin"].startswith("https://github.com/21st-dev/1code/tree/")
    assert r["loc"] == "https://github.com/21st-dev/1code/blob/9f1bc76/src/a.ts#L3-L9"
