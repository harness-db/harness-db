"""Tests for scripts/plot_frameworks.py (the five framework figures of the v2 manuscript).

A framework figure is wrong in exactly one way that matters: it prints a number the data no longer
support. So these tests run against the REAL data files and assert three things:

1. every number a figure prints is registered on its layout object with the file it came from, and
   is the value an INDEPENDENT reading of that file gives (the tests parse the files themselves,
   with their own code, rather than calling the script's parsers);
2. no figure prints a digit that was not registered - a count typed into a label fails here;
3. the geometry holds: every line of text fits the box it is in, nothing leaves the page, sibling
   boxes do not overlap, fonts are legible at print width, and no colour carries information.

They read layout objects, never rendered pixels. Nothing renders to a screen: matplotlib is forced
onto Agg, and the rendering test writes to ``tmp_path``.
"""

import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plot_frameworks as pf

PRISMA = ROOT / "data/prisma_counts.json"
FRAME = ROOT / "data/coding_frame.json"
RECON = ROOT / "docs/count_reconciliation.md"
SCHEMA = ROOT / "schema/dimensions.json"
REPORT = ROOT / "data/screening/fulltext_report.md"
TRIAGE = ROOT / "data/screening/triage.csv"
FINAL1 = ROOT / "data/screening/fulltext_final_pass1.csv"
FINAL2 = ROOT / "data/screening/fulltext_final_pass2.csv"
PILOT = ROOT / "data/tier3/pilot/pilot_summary.json"
OUTCOMES = ROOT / "paper/tables/outcomes_summary.json"
CREDIBLE = ROOT / "data/analysis/ablation_credible.csv"
POOLED = ROOT / "data/analysis/ablation_pooled.csv"
ABL_SUMMARY = ROOT / "data/analysis/ablation_summary.json"

csv.field_size_limit(10 ** 8)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def rows(p):
    with p.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(md: str, pattern: str) -> float:
    m = re.search(pattern, md)
    assert m, f"test could not find {pattern!r}"
    return float(m.group(1).replace(",", ""))


@pytest.fixture(scope="module")
def no_corpus(tmp_path_factory):
    """Paths with the corpus-wide file pointed at a file that does not exist."""
    missing = tmp_path_factory.mktemp("nocorpus") / "ablation_pooled_corpus.csv"
    return pf.Paths(corpus=missing)


@pytest.fixture(scope="module")
def figs(no_corpus):
    return {name: pf.build(name, no_corpus) for name in pf.FIGURES}


@pytest.fixture(scope="module")
def recon():
    """The reconciliation's counts, read by this test's own patterns."""
    md = RECON.read_text(encoding="utf-8")
    ival = lambda s: int(s.replace(",", ""))
    if re.search(r"\*\*Superseding note, \d{4}-\d{2}-\d{2}\.\*\*", md):
        # The release was rebuilt after the base note: read the bold "current release" column.
        m = re.search(r"\|\s*released systems\s*\|[^|\n]*\|\s*\*\*([\d,]+)\*\*", md)
        assert m
        c = re.search(r"\|\s*released cells\s*\|[^|\n]*\|\s*\*\*([\d,]+)\*\*\s*\|\s*([\d,]+)\s*×\s*(\d+)", md)
        assert c
        out = {"released": ival(m.group(1)), "dims": int(c.group(3)), "cells": ival(c.group(1))}
        for label, k in (("coded with a value and evidence", "coded"), ("`not_reported`", "nr"),
                         ("`unresolved`", "un")):
            mm = re.search(re.escape(label) + r"\s*\|[^|\n]*\|\s*\*\*([\d,]+)\s*\(([\d.]+)%\)\*\*", md)
            assert mm, label
            out[f"n_{k}"] = ival(mm.group(1))
            out[f"pct_{k}"] = float(mm.group(2))
    else:
        m = re.search(r"\|\s*released\s*\|\s*\*\*([\d,]+)\*\*.*?([\d,]+)\s*×\s*(\d+)\s*=\s*([\d,]+)",
                      md)
        assert m
        out = {"released": ival(m.group(1)), "dims": int(m.group(3)), "cells": ival(m.group(4))}
        for label, k in (("coded with a value and evidence", "coded"), ("`not_reported`", "nr"),
                         ("`unresolved`", "un")):
            mm = re.search(re.escape(label) + r"\s*\|\s*([\d,]+)\s*\|\s*\*\*([\d.]+)%", md)
            assert mm
            out[f"n_{k}"] = ival(mm.group(1))
            out[f"pct_{k}"] = float(mm.group(2))
    out["double"] = num(md, r"\*\*(\d+)\*\* double-coded")
    m = re.search(r"\*\*(\d+) of (\d+)\*\* dimensions at or above ([\d.]+)", md)
    out["pass"], out["of"], out["floor"] = int(m.group(1)), int(m.group(2)), float(m.group(3))
    out["mean_kappa"] = num(md, r"kappa \*\*([\d.]+)\*\*")
    return out


# ---------------------------------------------------------------------------- every figure

def test_five_figures_are_built_at_print_width(figs):
    assert set(figs) == set(pf.FIGURES) == {"pipeline_overview", "coding_framework",
                                            "screening_framework", "tier3_design",
                                            "rq3_triangulation"}
    for d in figs.values():
        assert d.width == pytest.approx(5.95)       # \linewidth of the acmart manuscript format
        assert 2.0 < d.height < 5.5


@pytest.mark.parametrize("name", pf.FIGURES)
def test_geometry_fits(figs, name):
    assert pf.check_fit(figs[name]) == []


@pytest.mark.parametrize("name", pf.FIGURES)
def test_fonts_legible_at_print_width(figs, name):
    # laid out at 1:1 for \linewidth, so the point size set is the point size printed
    sizes = {pf.SIZE[lb.style] for lb in figs[name].labels}
    assert min(sizes) >= 5.9


@pytest.mark.parametrize("name", pf.FIGURES)
def test_colour_carries_nothing(figs, name):
    """Every fill, edge and ink is a grey, so a greyscale print loses nothing."""
    def grey(c):
        if c in (None, "none"):
            return True
        r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
        return r == g == b
    d = figs[name]
    colours = ([s.fill for s in d.shapes] + [s.edge for s in d.shapes]
               + [lk.color for lk in d.links] + [pf.INK, pf.WHITE])
    assert all(grey(c) for c in colours), sorted(set(colours))


WHITELIST = re.compile(r"95%|\bRQ\d\b|\btier[- ]\d\b|\bTier[- ]\d\b|\bStage \d\b")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


@pytest.mark.parametrize("name", pf.FIGURES)
def test_no_unregistered_number_is_printed(figs, name):
    """Every digit on the page belongs to a number registered with its source file."""
    d = figs[name]
    registered = {t for n in d.numbers for t in NUMBER.findall(n.text)}
    for lb in d.labels:
        found = NUMBER.findall(WHITELIST.sub("", lb.text))
        if lb.structural:
            # stage numerals, arm and try indices, axis ticks: never data
            assert set(found) <= {"0", "0.5", "1", "2", "3", "4", "5", "6", "7"}, lb.text
            continue
        stray = [t for t in found if t not in registered]
        assert not stray, f"{name}: {lb.text!r} prints unregistered {stray}"


@pytest.mark.parametrize("name", pf.FIGURES)
def test_every_registered_number_is_printed_where_it_says(figs, name):
    d = figs[name]
    assert d.numbers
    for n in d.numbers:
        assert (ROOT / n.source).exists(), n.source
        if n.text:
            assert n.text in d.text_of(n.key), (n.name, n.text, n.key)


# ------------------------------------------------------------------------ Fig. 1 pipeline

def test_pipeline_counts_equal_the_files(figs, recon):
    d = figs["pipeline_overview"]
    pc, fr = load(PRISMA), load(FRAME)
    v = {n.name: n.value for n in d.numbers}
    ids = pc["identified_by_source"]
    assert v["identified"] == sum(ids.values())
    for k, n in ids.items():
        assert v[f"source_{k}"] == n
    assert v["duplicates"] == pc["duplicates_removed"]
    assert v["unique"] == v["screened_ta"] == pc["screened_title_abstract"]
    assert v["identified"] - v["duplicates"] == v["unique"]
    assert v["sought"] == pc["sought_full_text"]
    assert v["excluded_ta"] == pc["excluded_title_abstract"]
    assert v["assessed"] == pc["assessed_full_text"]
    assert v["not_retrieved"] == pc["not_retrieved"]
    assert v["excluded_ft"] == sum(pc["excluded_full_text"].values())
    assert v["included_papers"] == v["included_papers_g"] == pc["included_papers"]
    assert v["assessed"] - v["excluded_ft"] == v["included_papers"]
    assert v["systems"] == pc["included_systems"] == fr["systems_total"]
    assert v["coded_total"] == fr["coded_total"]
    for s in ("H", "P", "O"):
        assert v[f"stratum_{s}_size"] == fr["strata"][s]["size"]
        assert v[f"stratum_{s}_coded"] == fr["strata"][s]["coded"]
        assert v[f"stratum_{s}_weight"] == fr["strata"][s]["weight"]
    assert sum(fr["strata"][s]["size"] for s in "HPO") == fr["systems_total"]
    assert v["h_min_stars"] == fr["h_min_stars"]
    assert v["released"] == recon["released"]
    assert v["dimensions"] == recon["dims"] == len(load(SCHEMA)["dimensions"])
    assert v["cells"] == recon["cells"] == recon["released"] * recon["dims"]
    assert (v["pct_coded"], v["pct_not_reported"], v["pct_unresolved"]) == \
        (recon["pct_coded"], recon["pct_nr"], recon["pct_un"])
    assert v["dims_passing"] == recon["pass"] and v["dims_total_kappa"] == recon["of"]
    assert v["kappa_floor"] == recon["floor"] and v["double_coded"] == recon["double"]


def test_pipeline_state_split_is_consistent(recon):
    assert recon["n_coded"] + recon["n_nr"] + recon["n_un"] == recon["cells"]
    for k in ("coded", "nr", "un"):
        assert round(100 * recon[f"n_{k}"] / recon["cells"], 1) == recon[f"pct_{k}"]


def test_pipeline_has_seven_stages_in_order(figs):
    d = figs["pipeline_overview"]
    keys = ["search", "dedupe", "screen", "group", "frame", "coding", "analyses"]
    boxes = [d.shape(k) for k in keys]
    titles = [next(lb.text for lb in d.labels if lb.key == k and lb.style == "title")
              for k in keys]
    assert [t.split()[0] for t in titles] == [str(i) for i in range(1, 8)]
    assert "Two-Tier" in titles[2] and "Evidence-Anchored" in " ".join(
        lb.text for lb in d.labels if lb.key == "coding" and lb.style == "title")
    # left to right within each row, records row above systems row
    assert boxes[0].x < boxes[1].x < boxes[2].x and boxes[3].x < boxes[4].x < boxes[5].x
    assert max(b.bottom for b in boxes[:3]) < min(b.y for b in boxes[3:])


# ---------------------------------------------------------------- Fig. 2 coding framework

def test_coding_counts_equal_the_reconciliation(figs, recon):
    v = {n.name: n.value for n in figs["coding_framework"].numbers}
    assert v["cells_total"] == recon["cells"]
    assert (v["cells_coded"], v["cells_not_reported"], v["cells_unresolved"]) == \
        (recon["n_coded"], recon["n_nr"], recon["n_un"])
    assert v["double_coded"] == recon["double"] and v["mean_kappa"] == recon["mean_kappa"]
    assert v["dims_s1"] == len(load(SCHEMA)["dimensions"])


def test_three_state_contract_is_three_distinguishable_boxes(figs):
    d = figs["coding_framework"]
    states = {k: d.shape(k) for k in ("s_nr", "s_val", "s_un")}
    assert all(s.parent == "contract" for s in states.values())
    assert len({s.ls for s in states.values()}) == 3     # border style, not colour
    assert "not_reported" in d.text_of("s_nr")
    assert "value + evidence" in d.text_of("s_val")
    assert "unresolved" in d.text_of("s_un") and "excluded from every rate" in d.text_of("s_un")


def _lands_on(link, box):
    x, y = link.points[-1]
    return box.x <= x <= box.right and abs(y - box.y) < 0.03


def test_absence_test_routes_yes_to_value_and_no_to_not_reported(figs):
    d = figs["coding_framework"]
    dia = d.shape("absence")
    assert dia.kind == "diamond"
    vertices = [(dia.x, dia.cy), (dia.right, dia.cy), (dia.cx, dia.bottom)]
    out_of = [lk for lk in d.links if lk.arrow and any(
        abs(lk.points[0][0] - vx) < 0.02 and abs(lk.points[0][1] - vy) < 0.02
        for vx, vy in vertices)]
    targets = {k for k in ("s_nr", "s_val") for lk in out_of if _lands_on(lk, d.shape(k))}
    assert targets == {"s_nr", "s_val"}
    assert any(lb.text.startswith("yes") for lb in d.labels)
    assert any(lb.text.startswith("no: not_reported") for lb in d.labels)


def test_every_module_feeds_a_state(figs):
    d = figs["coding_framework"]
    for src, dst in (("check", "s_val"), ("stage2", "s_un")):
        s, t = d.shape(src), d.shape(dst)
        assert any(abs(lk.points[0][1] - s.bottom) < 0.02 and _lands_on(lk, t)
                   for lk in d.links), (src, dst)


# ------------------------------------------------------------- Fig. 3 screening framework

def test_screening_counts_equal_the_files(figs):
    d = figs["screening_framework"]
    v = {n.name: n.value for n in d.numbers}
    md = REPORT.read_text(encoding="utf-8")
    pc = load(PRISMA)
    assert v["kappa"] == num(md, r"Cohen's kappa \(sample as drawn\): ([\d.]+)")
    assert v["read_twice"] == num(md, r"Records read twice: (\d+)")
    assert v["agreement"] == num(md, r"observed agreement \d+/\d+ = ([\d.]+)%")
    assert v["ref_n"] == num(md, r"Positive set: (\d+) known")
    stages = re.findall(r"^- \w+: (\d+)/(\d+) = ", md.split("Recall by stage:")[1].split("\n\n")[1],
                        re.MULTILINE)
    assert v["ref_found"] == min(int(a) for a, _ in stages)
    assert v["included"] == pc["included_papers"]
    assert v["excluded_ft"] == sum(pc["excluded_full_text"].values())
    assert v["sought"] == pc["sought_full_text"] and v["excluded_ta"] == pc["excluded_title_abstract"]
    assert v["not_retrieved"] == pc["not_retrieved"]
    assert v["assessed"] == v["assessed_h"] == pc["assessed_full_text"]

    tri = rows(TRIAGE)
    auto = Counter(r["auto_decision"] for r in tri)
    assert v["ta_records"] == len(tri) == pc["screened_title_abstract"]
    assert v["tiebreak"] == sum(1 for r in tri if r["vote_3"])
    assert v["no_decision"] == v["no_decision_4"] == auto[""]
    assert v["auto_include"] == auto["include"]
    assert v["auto_include"] + v["no_decision"] + v["by_rule"] == v["sought"]
    assert v["sought"] + v["excluded_ta"] == v["ta_records"]


def test_screening_reader_split_equals_the_decision_files(figs):
    v = {n.name: n.value for n in figs["screening_framework"].numbers}
    f1, f2 = rows(FINAL1), rows(FINAL2)
    no_read = sum(1 for r in f1 if r["model"] == "none")
    tier1 = [r for r in f1 if r["decided_by"] == "tier1"]
    assert {r["decision"] for r in tier1} == {"include"}      # the note "tier 1 alone never excludes"
    assert v["tier2_decided"] == v["tier2_decided_4"] == sum(
        1 for r in f1 if r["decided_by"] == "opus" and r["model"] != "none")
    assert v["tier1_stands"] == len(tier1)
    assert v["no_read"] == no_read
    assert v["tier1_read"] == len(tier1) + sum(1 for r in f2 if r["model"] != "none")
    assert v["tier2_decided"] + v["tier1_stands"] + v["no_read"] == len(f1) == v["assessed"]
    assert v["tier1_read"] + v["tier2_only"] + v["no_read"] == v["assessed"]
    assert len(f2) == v["read_twice"]          # the second-reading file is the report's sample


def test_screening_overturn_rates_equal_the_raw_files(figs):
    """The escalation box prints how often tier 2 overturned tier 1, read from the raw files.

    Independent reading: merge the decision of record (pass-1 file) with the tier-1 reading
    (pass-2 file) on ``record_id`` and cross-tabulate; then check the same four cells against the
    report's section-5 confusion matrix, whose rows are the decision of record and whose columns
    are the tier-1 reading.
    """
    d = figs["screening_framework"]
    v = {n.name: n.value for n in d.numbers}
    record = {r["record_id"]: r["decision"] for r in rows(FINAL1)}
    cross = Counter((r["decision"], record[r["record_id"]]) for r in rows(FINAL2))
    assert v["exclude_escalated"] == cross["exclude", "include"] + cross["exclude", "exclude"]
    assert v["exclude_overturned"] == cross["exclude", "include"]
    assert v["include_escalated"] == cross["include", "include"] + cross["include", "exclude"]
    assert v["include_overturned"] == cross["include", "exclude"]
    assert v["exclude_overturn_rate"] == pytest.approx(v["exclude_overturned"] / v["exclude_escalated"])
    assert v["include_overturn_rate"] == pytest.approx(v["include_overturned"] / v["include_escalated"])
    # the twice-read sample is exactly the two escalated groups, and agreement is their diagonal
    assert v["exclude_escalated"] + v["include_escalated"] == v["read_twice"]
    md = REPORT.read_text(encoding="utf-8")
    m = re.search(r"\| pass 1 include \| (\d+) \| (\d+) \|\s*\n\| pass 1 exclude \| (\d+) \| (\d+) \|", md)
    assert m, "the report's section-5 confusion matrix changed shape"
    ii, ie, ei, ee = (int(g) for g in m.groups())
    assert (v["exclude_overturned"], v["exclude_escalated"]) == (ie, ie + ee)
    assert (v["include_overturned"], v["include_escalated"]) == (ei, ii + ei)
    agree = num(md, r"observed agreement (\d+)/\d+")
    assert agree == ii + ee == v["read_twice"] - v["exclude_overturned"] - v["include_overturned"]
    # the old coverage rows (includes/excludes of record "read twice") are gone
    text = " ".join(lb.text for lb in d.labels)
    assert "read twice" not in text.replace("records read twice", "")
    assert not {"inc_read_twice", "exc_read_twice", "inc_share", "exc_share"} & set(v)


def test_tiebreak_sits_at_title_abstract_not_after_tier_two(figs):
    d = figs["screening_framework"]
    tie = d.shape("ta2")
    assert "Third-vote tiebreak" in d.text_of("ta2")
    assert tie.bottom < min(d.shape(f"ft{i}").y for i in range(1, 5))
    assert "no third vote" in d.text_of("ft3")


# ------------------------------------------------------------------- Fig. 4 tier-3 design

def test_pilot_inset_equals_the_pilot_file(figs):
    d = figs["tier3_design"]
    pilot = load(PILOT)
    v = {n.name: n.value for n in d.numbers}
    suites = pilot["suites"]
    assert v["n_cells"] == len(suites)
    assert v["n_in_band_point"] == sum(1 for s in suites.values() if s["in_band"])
    assert (v["band_low"], v["band_high"]) == tuple(pilot["band"])
    assert v["target"] == pilot["target_effect"]
    ax0, ax1 = d.meta["x_of"]
    marks = {m.key.split(":", 1)[1]: m for m in d.marks if m.key.startswith("pilot:")}
    assert set(marks) == set(suites)
    for key, s in suites.items():
        assert v[f"pilot_n_{key}"] == s["n_instances"]
        assert marks[key].x == pytest.approx(ax0 + (ax1 - ax0) * s["arm_a_continuous"])
        assert marks[key].filled == bool(s["in_band"])


def test_pilot_interval_is_the_protocols_t_interval(figs):
    from scipy import stats

    pilot = load(PILOT)
    lo, hi = pilot["band"]
    cells = {c["key"]: c for c in figs["tier3_design"].meta["pilot_cells"]}
    n_inside = 0
    for key, s in pilot["suites"].items():
        n = s["n_instances"]
        half = stats.t.ppf(0.975, n - 1) * s["sd_between_instances"] / math.sqrt(n)
        assert cells[key]["ci_low"] == pytest.approx(s["arm_a_continuous"] - half)
        assert cells[key]["ci_high"] == pytest.approx(s["arm_a_continuous"] + half)
        n_inside += lo <= s["arm_a_continuous"] - half and s["arm_a_continuous"] + half <= hi
    v = {n.name: n.value for n in figs["tier3_design"].numbers}
    assert v["n_in_band_interval"] == n_inside
    # the method reproduces the interval the protocol notes state for this cell (0.852 [0.757, 0.948])
    c = cells["bigcodebench_instruct@haiku"]
    assert (round(c["ci_low"], 3), round(c["ci_high"], 3)) == (0.757, 0.948)


def test_arm_c_is_matched_to_arm_b_per_instance(figs):
    d = figs["tier3_design"]
    counter, first_c = d.shape("B_counter"), d.shape("C_try0")
    match = [lk for lk in d.links if lk.key == "match"]
    assert len(match) == 1 and match[0].ls == "dashed"
    (x0, y0), (x1, y1) = match[0].points[0], match[0].points[-1]
    assert counter.x <= x0 <= counter.right and abs(y0 - counter.bottom) < 0.03
    assert first_c.x <= x1 <= first_c.right and abs(y1 - first_c.y) < 0.03
    assert "matched per instance" in d.text_of("match")
    assert "B − C" in d.text_of("contrasts")


def test_confirmatory_status_follows_the_runs_file(figs):
    ran = (ROOT / "data/tier3/runs.jsonl").exists()
    text = figs["tier3_design"].text_of("inset")
    assert ("not run" in text) is (not ran)


# ---------------------------------------------------------------- Fig. 5 RQ3 triangulation

def test_rq3_numbers_equal_the_files(figs):
    v = {n.name: n.value for n in figs["rq3_triangulation"].numbers}
    out = load(OUTCOMES)
    ma = next(c for c in out["contrasts"] if c["dimension"] == "multi_agent_topology")
    assert v["keys"] == out["comparable_set"]["keys"]
    assert v["key_systems"] == out["comparable_set"]["systems"]
    assert (v["ma_effect"], v["ma_ci_low"], v["ma_ci_high"], v["ma_keys"]) == \
        (ma["effect"], ma["ci_low"], ma["ci_high"], ma["n_keys"])
    funnel = load(ABL_SUMMARY)["funnel"]
    assert (v["contrasts"], v["papers"]) == (funnel["contrasts"], funnel["papers"])
    sv = {r["dimension"]: r for r in rows(POOLED)}["self_verification"]
    cr = {r["dimension"]: r for r in rows(CREDIBLE)}["self_verification"]
    assert v["sv_mu"] == float(sv["mu_rel"]) == pytest.approx(float(cr["mu_rel"]))
    assert v["sv_disc"] == float(cr["mu_discounted"])
    assert (v["sv_pi_low"], v["sv_pi_high"]) == (float(sv["pi_low"]), float(sv["pi_high"]))
    assert (v["sv_contrasts"], v["sv_papers"]) == (int(sv["n_contrasts"]), int(sv["n_papers"]))
    # "crosses zero" is printed exactly when the credible table says the PI does not exclude zero
    crosses = float(sv["pi_low"]) < 0 < float(sv["pi_high"])
    assert crosses == (cr["pi_excludes_zero"] == "0")
    assert ("crosses zero" in figs["rq3_triangulation"].text_of("within")) is crosses
    pilot = load(PILOT)
    assert v["abl_cells"] == len(pilot["suites"])
    assert v["abl_in_band_point"] == sum(1 for s in pilot["suites"].values() if s["in_band"])


def test_rq3_designs_climb_one_axis_with_their_bounds(figs):
    d = figs["rq3_triangulation"]
    assert d.meta["rows"] == ["cross", "within", "ablation"]
    lv = d.meta["levels"]
    assert lv["cross"] < lv["within"] < lv["ablation"]
    assert d.meta["bounds"] == {"cross": "lower", "within": "upper", "ablation": "unbiased"}
    bars = {s.key: s for s in d.shapes if s.kind == "rect"}
    assert bars["cross"].w < bars["within"].w < bars["ablation"].w
    # the bound direction is carried by fill and hatching, not colour
    assert len({(bars[k].fill, bars[k].hatch) for k in ("cross", "within", "ablation")}) == 3
    assert "lower bound" in d.text_of("cross") and "upper bound" in d.text_of("within")


def _write_corpus(path, rows_):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_[0]))
        w.writeheader()
        w.writerows(rows_)


def test_rq3_draws_the_corpus_row_only_when_the_file_exists(tmp_path):
    f = tmp_path / "ablation_pooled_corpus.csv"
    _write_corpus(f, [
        {"dimension": "planning_granularity", "n_contrasts": 9, "n_papers": 7, "mu_rel": 0.2,
         "ci_low": 0.1, "ci_high": 0.3, "pi_low": -0.1, "pi_high": 0.5},
        {"dimension": "self_verification", "n_contrasts": 212, "n_papers": 131,
         "mu_rel": 0.0913, "ci_low": 0.0501, "ci_high": 0.1325, "pi_low": -0.2104,
         "pi_high": 0.3931}])
    summary = tmp_path / "ablation_summary_corpus.json"
    summary.write_text(json.dumps({"funnel": {"contrasts": 1234, "papers": 321}}),
                       encoding="utf-8")
    d = pf.build("rq3_triangulation", pf.Paths(corpus=f, corpus_summary=summary))
    assert d.meta["rows"] == ["cross", "within", "corpus", "ablation"]
    assert d.meta["levels"]["corpus"] == d.meta["levels"]["within"]
    assert d.meta["bounds"]["corpus"] == "upper"
    v = {n.name: n.value for n in d.numbers}
    # the subtitle is the pooled total from the run summary; the focal counts follow it
    assert (v["corpus_total_contrasts"], v["corpus_total_papers"]) == (1234, 321)
    assert (v["corpus_contrasts"], v["corpus_papers"]) == (212, 131)
    assert "1,234 contrasts from 321" in d.text_of("corpus")
    assert (v["corpus_mu"], v["corpus_ci_low"], v["corpus_ci_high"]) == (0.0913, 0.0501, 0.1325)
    assert "corpus-wide" in d.text_of("corpus")
    assert pf.check_fit(d) == []
    for n in d.numbers:
        if n.text:
            assert n.text in d.text_of(n.key)


MACROS = ROOT / "paper/tables/rq3_macros.tex"


def _macro_values() -> dict[str, list[float]]:
    """Every number inside each `\\newcommand` of the manuscript's RQ3 macro file, parsed by this
    test's own pattern (thousands separators `{,}` removed, signs kept)."""
    out = {}
    for line in MACROS.read_text(encoding="utf-8").splitlines():
        m = re.fullmatch(r"\\newcommand\{\\(\w+)\}\{(.*)\}", line)
        if m:
            text = m.group(2).replace("{,}", "")
            out[m.group(1)] = [float(x) for x in re.findall(r"[+-]?\d+(?:\.\d+)?", text)]
    return out


def _fig_value(text: str) -> float:
    return float(text.replace("−", "-").replace(",", ""))


def test_rq3_corpus_row_prints_what_the_manuscript_macros_say():
    """The figure and the prose must quote one snapshot: the corpus-wide row's pooled total and
    self-verification estimate equal the values in `paper/tables/rq3_macros.tex`."""
    paths = pf.Paths()
    if not (paths.corpus.exists() and paths.corpus_summary.exists() and MACROS.exists()):
        pytest.skip("corpus-wide analysis outputs or the generated macro file are absent")
    d = pf.build("rq3_triangulation", paths)
    fig = {n.name: n for n in d.numbers if n.key == "corpus"}
    mac = _macro_values()
    pairs = {
        "corpus_total_contrasts": mac["rqTotalContrasts"][0],
        "corpus_total_papers": mac["rqTotalPapers"][0],
        "corpus_contrasts": mac["rqSVContrasts"][0],
        "corpus_papers": mac["rqSVPapers"][0],
        "corpus_mu": mac["rqSVPooled"][0],
        "corpus_ci_low": mac["rqSVCIz"][0], "corpus_ci_high": mac["rqSVCIz"][1],
        "corpus_pi_low": mac["rqSVPI"][0], "corpus_pi_high": mac["rqSVPI"][1],
    }
    for name, want in pairs.items():
        assert name in fig, f"the corpus-wide row does not print {name}"
        assert _fig_value(fig[name].text) == pytest.approx(want, abs=5e-4), (name, fig[name].text)
        assert fig[name].text in d.text_of("corpus")


def test_rq3_omits_a_corpus_file_without_a_usable_row(tmp_path, no_corpus):
    f = tmp_path / "ablation_pooled_corpus.csv"
    _write_corpus(f, [{"dimension": "tool_count", "n_contrasts": 3, "mu_rel": 0.1}])
    d = pf.build("rq3_triangulation", pf.Paths(corpus=f))
    assert "corpus" not in d.meta["rows"]
    assert pf.build("rq3_triangulation", no_corpus).meta["rows"] == ["cross", "within",
                                                                     "ablation"]


# ------------------------------------------------------------------------- parsers, CLI, build

def test_reconciliation_parser_fails_loudly_on_a_changed_document():
    with pytest.raises(ValueError, match="released row"):
        pf.parse_reconciliation("| sampling frame | **6,504** |\n| released | 1,253 |\n")


def test_release_drift_is_reported_not_hidden(tmp_path):
    rec = pf.parse_reconciliation(RECON.read_text(encoding="utf-8"))
    systems = [{"id": f"s{i}", "coding": {"a": {"value": "x"}, "b": {"not_reported": True,
                                                                    "value": None}}}
               for i in range(3)]
    p = tmp_path / "systems.json"
    p.write_text(json.dumps(systems), encoding="utf-8")
    drift = pf.release_drift(pf.Paths(systems=p), rec)
    assert drift["checked"] and drift["systems"] == 3 and drift["cells"] == 6
    assert drift["states"] == {"coded": 3, "not_reported": 3}
    assert drift["matches"] is False


def test_makefile_regenerates_the_framework_figures():
    mk = (ROOT / "Makefile").read_bytes().decode("utf-8")
    block = mk.split("ANALYSIS_SCRIPTS =")[1].split("\n\n")[0].split("\r\n\r\n")[0]
    lines = [ln.rstrip("\r") for ln in block.splitlines()[1:]]
    assert "\tscripts/plot_frameworks.py \\" in lines
    assert all(ln.startswith("\t") for ln in lines)
    assert all(ln.endswith(" \\") for ln in lines[:-1]) and not lines[-1].endswith("\\")


def test_render_writes_svg_and_pdf(tmp_path, figs):
    for name in pf.FIGURES:
        paths = pf.render(figs[name], tmp_path / name)
        assert [p.suffix for p in paths] == [".svg", ".pdf"]
        assert all(p.stat().st_size > 5000 for p in paths)


def test_main_no_render_exits_clean(capsys):
    assert pf.main(["--no-render"]) == 0
    out = capsys.readouterr().out
    for name in pf.FIGURES:
        assert name in out
    assert "FIT:" not in out
