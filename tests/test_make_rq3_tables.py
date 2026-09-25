"""Tests for scripts/make_rq3_tables.py - the build-time RQ3 LaTeX fragments.

The fixture is a complete, self-consistent miniature of every input: contrasts with provenance, the
coverage outputs produced by the real `analyse_ablation_coverage.py --corpus` from them, and pooled /
credible / bias tables and summaries whose counts agree with those contrasts.
"""
from __future__ import annotations

import csv
import dataclasses
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import analyse_ablation_coverage as coverage
import analyse_ablations
import make_rq3_tables as mod

REQUIRED_MACROS = [
    "rqCorpusPapersExtracted", "rqCorpusPapersWithContrast", "rqCorpusContrasts",
    "rqCodedContrasts", "rqCodedPapers", "rqPoolableDims", "rqSignSharePct",
    "rqPIIncludesZeroCount", "rqPIExcludesZeroDims", "rqDiscountSurviveZ", "rqDiscountSurviveHK",
    "rqMedianDiscountPct", "rqSVPapers", "rqSVPooled", "rqSVDiscounted", "rqSVPI", "rqSVCIz",
    "rqCoverageRho", "rqCoverageP", "rqZeroDimCount", "rqZeroDimList", "rqZeroLayerList",
    "rqHarvestTierCoverage", "rqHarvestDate",
    # added at the section writer's request
    "rqEffectRangeSurviving", "rqEffectIQRSurviving", "rqPIExcludesZeroLower",
    "rqEggerFlaggedDims", "rqFGHPaperCounts",
    # what the sign share rests on (review, fix 3)
    "rqSignDenom", "rqPolarityStatedN", "rqPolarityStatedFavour", "rqPolarityStatedFavourPct",
    "rqPolarityAssumedN", "rqPolarityAssumedFavour", "rqPolarityAssumedFavourPct",
    "rqVarAssumedN",
]
#: the two sensitivity analyses; computed from the real harvest and outcome data only
SENSITIVITY_MACROS = [
    "rqPreRuleRho", "rqPreRuleP", "rqPreRuleGContrasts", "rqPreRuleGRemapped", "rqPreRuleGDropped",
    "rqDCLDropped", "rqDCLAgainst", "rqSignShareWithDCLPct", "rqXPBaselineKeys", "rqXPOtherKeys",
    "rqXPOtherEffect", "rqXPOtherCI", "rqXPOtherP",
]

DIMENSIONS = {
    "layers": [{"id": "A", "name": "Context assembly"}, {"id": "E", "name": "Verification"},
               {"id": "F", "name": "Budget"}, {"id": "G", "name": "Sandbox"},
               {"id": "M", "name": "Meta"}],
    "dimensions": [
        {"key": "context_compaction", "layer": "A", "name": "Context compaction", "id": "A1"},
        {"key": "observation_format", "layer": "A", "name": "Observation formatting", "id": "A2"},
        {"key": "self_verification", "layer": "E", "name": "Self-verification", "id": "E1"},
        {"key": "multi_agent_topology", "layer": "A", "name": "Multi-agent topology", "id": "A3"},
        {"key": "termination_condition", "layer": "F", "name": "Termination", "id": "F1"},
        {"key": "network_policy", "layer": "G", "name": "Network policy", "id": "G1"},
        {"key": "open_source", "layer": "M", "name": "Open source", "id": "M1"},
    ],
}

# (record_id, dimension, provenance)
CONTRASTS = (
    [(f"sv{i}", "self_verification", "coded_harvest" if i < 2 else "corpus_fulltext")
     for i in range(5)]
    + [("sv0", "self_verification", "coded_harvest")]
    + [(f"cc{i}", "context_compaction", "corpus_fulltext") for i in range(3)]
    + [(f"of{i}", "observation_format", "corpus_fulltext") for i in range(4)]
    + [("tc0", "termination_condition", "corpus_fulltext")] * 2
)
# per contrast, in the same order: (polarity, rel_effect, var_method). On the 13 contrasts of the
# three pooled dimensions: 12 favour the component; 4 take their direction by assumption (3 of
# them favouring); 5 carry an assumed variance.
DETAIL = (
    [("higher", 0.2, "binomial_delta")] * 4 + [("higher_assumed", -0.1, "assumed_rel_se")]
    + [("higher", 0.1, "binomial_delta")]
    + [("lower", 0.05, "assumed_rel_se")] * 3
    + [("higher_assumed", 0.3, "assumed_rel_se")] * 3 + [("higher", 0.2, "binomial_delta")]
    + [("higher", -0.01, "binomial_delta")] * 2
)
SIGN_SHARE = 12 / 13

POOLED = [
    # dimension, pooled, papers, contrasts, papers coded, papers corpus, mu, ci, hk, pi, i2
    ("self_verification", 1, 5, 6, 2, 3, 0.15, (0.10, 0.20), (0.09, 0.21), (-0.10, 0.40), 80.0),
    ("observation_format", 1, 4, 4, 0, 4, 0.12, (0.03, 0.21), (-0.01, 0.25), (-0.05, 0.30), 40.0),
    ("context_compaction", 1, 3, 3, 0, 3, 0.11, (0.06, 0.16), (0.05, 0.17), (0.02, 0.20), 10.0),
    ("termination_condition", 0, 1, 2, 0, 1, None, None, None, None, None),
]


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _nan(x):
    return "" if x is None else x


@pytest.fixture
def world(tmp_path):
    a = tmp_path / "data" / "analysis"
    a.mkdir(parents=True)
    (tmp_path / "paper" / "tables").mkdir(parents=True)
    tier3 = tmp_path / "data" / "tier3"
    (tier3 / "pilot").mkdir(parents=True)
    (tmp_path / "schema").mkdir()
    dims = tmp_path / "schema" / "dimensions.json"
    dims.write_text(json.dumps(DIMENSIONS), encoding="utf-8")

    # coverage outputs, from the real script
    nr = tmp_path / "nr.csv"
    nr.write_text("dimension,weighted_rate\ncontext_compaction,0.2\nobservation_format,0.3\n"
                  "self_verification,0.5\ntermination_condition,0.6\nnetwork_policy,0.8\n"
                  "open_source,0.1\n", encoding="utf-8")
    union = a / "ablation_contrasts_corpus.csv"
    _write_csv(union, ["record_id", "dimension", "provenance", "polarity", "rel_effect",
                       "var_method"],
               [list(r) + list(x) for r, x in zip(CONTRASTS, DETAIL, strict=True)])
    coded = a / "ablation_contrasts.csv"
    _write_csv(coded, ["dimension"], [[r[1]] for r in CONTRASTS if r[2] == "coded_harvest"])
    base = ["--dimensions", str(dims), "--nr-by-dimension", str(nr), "--out-dir", str(a),
            "--blocks-summary", str(tmp_path / "absent.json")]
    assert coverage.main(base + ["--contrasts", str(coded)]) == 0
    assert coverage.main(base + ["--corpus", "--contrasts", str(union)]) == 0

    pooled_header = ["dimension", "pooled", "n_papers", "n_contrasts", "n_papers_coded",
                     "n_papers_corpus", "mu_rel", "ci_low", "ci_high", "hk_ci_low", "hk_ci_high",
                     "pi_low", "pi_high", "i2"]
    _write_csv(a / "ablation_pooled_corpus.csv", pooled_header, [
        [d, p, n, c, nc, nk, _nan(mu),
         _nan(ci and ci[0]), _nan(ci and ci[1]), _nan(hk and hk[0]), _nan(hk and hk[1]),
         _nan(pi and pi[0]), _nan(pi and pi[1]), _nan(i2)]
        for d, p, n, c, nc, nk, mu, ci, hk, pi, i2 in POOLED])
    _write_csv(a / "ablation_credible_corpus.csv",
               ["dimension", "mu_rel", "mu_discounted", "discount_factor", "survives_discount",
                "survives_discount_hk", "pi_excludes_zero"],
               [["self_verification", 0.15, 0.075, 0.5, 1, 1, 0],
                ["observation_format", 0.12, 0.06, 0.5, 0, 0, 0],
                ["context_compaction", 0.11, 0.055, 0.5, 1, 1, 1]])
    _write_csv(a / "ablation_bias_corpus.csv", ["dimension", "egger_intercept", "egger_p"],
               [["self_verification", 1.2, 0.01], ["observation_format", -0.7, 0.05],
                ["context_compaction", 0.3, 0.6]])
    snapshot = {
        "harvest_updated_at": "2026-09-25T15:00:00+00:00", "papers_extracted": 3,
        "contrasts_after_guards": 12, "contrast_rows_read": 12, "consistent": True,
        "tier_status": {"T10": {"extracted": 3, "pending": 7}, "T3": {"pending": 20}},
        "tier_coverage": {
            "T10": {"papers": 10, "extracted": 3, "share_extracted": 0.3, "pct_extracted": 30.0},
            "T3": {"papers": 20, "extracted": 0, "share_extracted": 0.0, "pct_extracted": 0.0}},
    }
    summary = {
        "funnel": {"contrasts": len(CONTRASTS), "papers": len({r[0] for r in CONTRASTS})},
        "provenance": {"contrasts": {"coded_harvest": 3, "corpus_fulltext": 12},
                       "papers": {"coded_harvest": 2, "corpus_fulltext": 11},
                       "corpus_rows_in_file": 12, "already_in_coded_harvest": 0},
        "settings": {"min_papers": 3},
        "bias_verdict": {"overall_sign_share": SIGN_SHARE, "discount": 0.4876,
                         "egger_flagged_dimensions": ["self_verification", "observation_format"]},
        "harvest_snapshot": snapshot,
    }
    (a / "ablation_summary_corpus.json").write_text(json.dumps(summary), encoding="utf-8")
    (a / "corpus_ablation_summary.json").write_text(json.dumps({
        "updated_at": snapshot["harvest_updated_at"], "papers_extracted": 3,
        "contrasts_after_guards": 12}), encoding="utf-8")
    (tmp_path / "paper" / "tables" / "outcomes_summary.json").write_text(json.dumps({
        "comparable_set": {"keys": 36, "systems": 53},
        "contrasts": [{"name": "executable_verification", "dimension": "self_verification",
                       "n_keys": 3, "n_systems": 11, "estimable": True, "effect": -0.734,
                       "ci_low": -1.414, "ci_high": -0.258, "permutation": {"p_two_sided": 0.3056},
                       "detected": False, "fragile": True},
                      {"name": "multi_agent", "dimension": "multi_agent_topology",
                       "n_keys": 17, "n_systems": 36, "estimable": True, "effect": 1.0116,
                       "ci_low": 0.5253, "ci_high": 1.3731, "permutation": {"p_two_sided": 0.0003},
                       "detected": True, "fragile": False}],
    }), encoding="utf-8")
    (tier3 / "pilot" / "pilot_summary.json").write_text(
        '{"selected": "s@haiku", "target_effect": 0.07, "suites": {"s@haiku": {"suite": "s_hard",'
        ' "model_requested": "haiku", "n_instances": 23, "seeds_per_instance": [3],'
        ' "sd_run_within_instance": NaN, "power": {"rho=0.5": {"n_instances_80pct": 146},'
        ' "rho=0.7": {"n_instances_80pct": 93}}}, "t@sonnet": {"suite": "t"}}}',
        encoding="utf-8")
    # 12 instances: 8 fall in the confirmatory pool by the tier-3 hash, and two of those (0, 1)
    # have been piloted, so 6 are clean
    (tier3 / "suites").mkdir()
    (tier3 / "suites" / "s_hard.json").write_text(json.dumps(
        {"name": "s_hard", "instances": [{"id": f"s_hard/{i}"} for i in range(12)]}),
        encoding="utf-8")
    (tier3 / "pilot" / "runs.jsonl").write_text(
        "".join(json.dumps({"instance_id": f"s_hard/{i}"}) + "\n" for i in (0, 1, 2)),
        encoding="utf-8")
    (tier3 / "pilot_v2").mkdir()
    (tier3 / "pilot_v2" / "pilot_v2_summary.json").write_text(json.dumps(
        {"cells": {"s_hard@haiku:B": {"n_rows": 23}, "s_hard@haiku:Bfix": {"n_rows": 23},
                   "s@haiku:B": {"n_rows": 25}, "s@haiku:Bfix": {"n_rows": 25}}}),
        encoding="utf-8")
    # the sensitivity analyses read the real harvest and outcome data; see the real-data tests
    inputs = dataclasses.replace(mod.Inputs.default(tmp_path), sensitivity=False)
    return inputs, tmp_path / "out"


def _rows(fragment: str) -> list[str]:
    body = fragment.split("% BEGIN ROWS\n", 1)[1].split("% END ROWS", 1)[0]
    return [line for line in body.splitlines() if line.strip()]


def _macros(fragment: str) -> dict[str, str]:
    out = {}
    for line in fragment.splitlines():
        if not line or line.startswith("%"):
            continue
        m = re.fullmatch(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}", line)
        assert m, f"not a macro definition: {line!r}"
        value = m.group(2)
        depth = 0
        for ch in value.replace(r"\{", "").replace(r"\}", ""):
            depth += {"{": 1, "}": -1}.get(ch, 0)
            assert depth >= 0, f"unbalanced braces in {line!r}"
        assert depth == 0, f"unbalanced braces in {line!r}"
        assert m.group(1) not in out, f"{m.group(1)} defined twice"
        out[m.group(1)] = value
    return out


# --------------------------------------------------------------------------- happy path


def test_every_fragment_is_written_with_a_source_header(world):
    inputs, out = world
    assert mod.main(["--out-dir", str(out)], inputs=inputs) == 0
    for name in ("rq3_pooled.tex", "rq3_coverage.tex", "rq3_designs.tex", "rq3_macros.tex"):
        text = (out / name).read_text(encoding="utf-8")
        assert text.startswith("% RQ3 ")
        assert "% generated: " in text
        assert "ablation_summary_corpus.json" in text or "ablation_coverage" in text
        assert re.search(r"% +\S+ +\(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\)", text), "source mtime"
        assert "nan" not in text.lower()


def test_pooled_table_has_one_row_per_poolable_dimension(world):
    inputs, _ = world
    frags = mod.build(inputs)
    rows = _rows(frags["rq3_pooled.tex"])
    assert len(rows) == sum(1 for r in POOLED if r[1] == 1)
    # sorted by papers, descending; the unpooled dimension is not a row
    assert rows[0].startswith(mod.RAGGED + "Self-verification (E1)")
    assert not any("Termination" in r for r in rows)
    assert r"\label{tab:ablations}" in frags["rq3_pooled.tex"]


def test_pooled_table_bolds_only_prediction_intervals_that_exclude_zero(world):
    inputs, _ = world
    rows = _rows(mod.build(inputs)["rq3_pooled.tex"])
    bold = [r for r in rows if r"\textbf{" in r]
    assert len(bold) == 1 and bold[0].startswith(mod.RAGGED + "Context compaction")
    assert "yes/yes" in bold[0]
    assert "90 (" not in rows[0] and "5 (2+3)" in rows[0]


def test_coverage_and_designs_row_counts_match_their_sources(world):
    inputs, _ = world
    frags = mod.build(inputs)
    layers = list(csv.DictReader(inputs.coverage_corpus_csv.open(encoding="utf-8")))
    assert len(_rows(frags["rq3_coverage.tex"])) == len(layers)
    designs = _rows(frags["rq3_designs.tex"])
    # three designs; the cross-paper one carries a second (continuation) line
    named = [r for r in designs if not r.startswith(mod.RAGGED + " &")]
    assert len(named) == 3
    assert len(designs) == 4
    assert r"\label{tab:coverage}" in frags["rq3_coverage.tex"]
    assert r"\label{tab:rq3-bounds}" in frags["rq3_designs.tex"]


def test_cross_paper_design_shows_the_headline_then_the_focal_dimension(world):
    inputs, _ = world
    head, focal, within, tier3 = _rows(mod.build(inputs)["rq3_designs.tex"])
    assert head.startswith(mod.RAGGED + "Cross-paper association")
    assert "multi-agent topology (A3): $d = +1.012$" in head
    assert "headline contrast" not in head and "multi agent" not in head
    assert r"\ensuremath{[+0.525, +1.373]}" in head
    assert "17 keys, 36 systems (of 36 keys, 53 systems)" in head
    assert head.count("lower (") == 1
    assert focal.startswith(mod.RAGGED + " & " + mod.RAGGED + " & ")
    assert ("self-verification (E1), executable checks vs none; fragile (3 keys): "
            "$d = -0.734$") in focal
    assert "$p = 0.306$; fragile" in focal
    assert "self-verification (E1)" in within
    assert "not yet estimated" in tier3
    # the registered row: every count read, no suite or model identifier leaked into the table
    assert ("pilot: 2 suite--model cells, arm A; revision: 48 runs, arms A and B; 93 instances "
            r"needed at $\rho = 0.7$, 6 available") in tier3
    assert "filed, amendment pending; pilot failed its band; not runnable on available suites" in tier3
    assert "s\\_hard" not in tier3 and "haiku" not in tier3


def test_registered_row_refuses_once_the_suite_can_supply_the_plan(world, capsys):
    inputs, out = world
    pilot = json.loads(inputs.pilot_summary.read_text(encoding="utf-8").replace("NaN", "null"))
    pilot["suites"]["s@haiku"]["power"]["rho=0.7"]["n_instances_80pct"] = 6
    inputs.pilot_summary.write_text(json.dumps(pilot), encoding="utf-8")
    _assert_refuses(inputs, out, capsys, "no longer holds")


def test_cross_paper_bound_names_baseline_keys_when_there_are_any(world):
    inputs, _ = world
    o = json.loads(inputs.outcomes_summary.read_text(encoding="utf-8"))
    o["contrasts"][1]["baseline_asymmetry"] = {"reference_all_recurring_keys": 7}
    inputs.outcomes_summary.write_text(json.dumps(o), encoding="utf-8")
    head, focal, _, _ = _rows(mod.build(inputs)["rq3_designs.tex"])
    assert "in 7 of its 17 keys baseline selection can inflate it" in head
    assert "baseline selection" not in focal


def test_refuses_when_the_cross_paper_headline_is_no_longer_robust(world, capsys):
    inputs, out = world
    o = json.loads(inputs.outcomes_summary.read_text(encoding="utf-8"))
    o["contrasts"][1]["fragile"] = True
    inputs.outcomes_summary.write_text(json.dumps(o), encoding="utf-8")
    _assert_refuses(inputs, out, capsys, "no longer detected and robust")


def test_macros_parse_and_carry_every_required_name(world):
    inputs, _ = world
    macros = _macros(mod.build(inputs)["rq3_macros.tex"])
    assert set(REQUIRED_MACROS) <= set(macros)
    assert macros["rqPoolableDims"] == "3"
    assert macros["rqCodedContrasts"] == "3"
    assert macros["rqCorpusContrasts"] == "12"
    assert macros["rqSVPooled"] == r"\ensuremath{+0.150}"
    assert macros["rqSVCIz"] == r"\ensuremath{[+0.100, +0.200]}"
    assert macros["rqSVPI"] == r"\ensuremath{[-0.100, +0.400]}"
    # *Pct macros are bare numbers; the sentence adds the percent sign
    assert macros["rqSignSharePct"] == "92.3"
    # the warrant under it: same denominator, split by how the metric's direction was obtained
    assert macros["rqSignDenom"] == "13"
    assert (macros["rqPolarityStatedN"], macros["rqPolarityStatedFavour"]) == ("9", "9")
    assert macros["rqPolarityStatedFavourPct"] == "100.0"
    assert (macros["rqPolarityAssumedN"], macros["rqPolarityAssumedFavour"]) == ("4", "3")
    assert macros["rqPolarityAssumedFavourPct"] == "75.0"
    assert macros["rqVarAssumedN"] == "7"
    assert not set(SENSITIVITY_MACROS) & set(macros)
    assert macros["rqMedianDiscountPct"] == "48.8"
    assert macros["rqPIIncludesZeroCount"] == "2"
    assert macros["rqPIExcludesZeroDims"] == "context compaction (A1)"
    assert macros["rqPIExcludesZeroLower"] == r"context\_compaction (\ensuremath{+0.020})"
    assert macros["rqDiscountSurviveZ"] == "2"
    assert macros["rqEffectRangeSurviving"] == r"\ensuremath{+0.110} to \ensuremath{+0.150}"
    assert macros["rqEggerFlaggedDims"] == (r"observation\_format (\ensuremath{-}), "
                                            r"self\_verification (\ensuremath{+})")
    assert macros["rqFGHPaperCounts"] == r"termination\_condition (1/2)"
    assert macros["rqZeroLayerList"] == "G (sandbox)"
    # multi_agent_topology is in the fixture schema only as the cross-paper headline: no contrast
    assert macros["rqZeroDimList"] == "multi-agent topology (A3) and network policy (G1)"
    assert macros["rqHarvestTierCoverage"] == r"30.0\% of the top-signal tier and none of the second"
    assert macros["rqHarvestDate"] == "25 September 2026"
    assert macros["rqCoverageRho"].startswith(r"\ensuremath{")


def test_zero_layer_list_says_empty_when_every_layer_is_touched(world):
    inputs, _ = world
    cov = json.loads(inputs.coverage_corpus_json.read_text(encoding="utf-8"))
    cov["coverage_by_layer"]["zero_contrast_layers"] = []
    inputs.coverage_corpus_json.write_text(json.dumps(cov), encoding="utf-8")
    assert _macros(mod.build(inputs)["rq3_macros.tex"])["rqZeroLayerList"] == "empty"


def test_rerun_with_the_same_inputs_rewrites_nothing(world):
    inputs, out = world
    first = mod.write_all(out, mod.build(inputs, stamp="2026-01-01T00:00:00Z"))
    assert len(first) == 4
    again = mod.write_all(out, mod.build(inputs, stamp="2026-01-02T00:00:00Z"))
    assert again == []


# --------------------------------------------------------------------------- refusals


def _assert_refuses(inputs, out, capsys, match):
    assert mod.main(["--out-dir", str(out)], inputs=inputs) == 2
    assert not out.exists() or not any(out.iterdir()), "a refusal must not write anything"
    assert re.search(match, capsys.readouterr().err)


def test_refuses_on_a_missing_column(world, capsys):
    inputs, out = world
    rows = list(csv.DictReader(inputs.pooled.open(encoding="utf-8")))
    header = [c for c in rows[0] if c != "hk_ci_low"]
    _write_csv(inputs.pooled, header, [[r[c] for c in header] for r in rows])
    _assert_refuses(inputs, out, capsys, r"missing column\(s\) \['hk_ci_low'\]")


def test_refuses_when_the_contrast_file_is_not_the_one_pooled(world, capsys):
    inputs, out = world
    summary = json.loads(inputs.ablation_summary.read_text(encoding="utf-8"))
    summary["bias_verdict"]["overall_sign_share"] = 0.9
    inputs.ablation_summary.write_text(json.dumps(summary), encoding="utf-8")
    _assert_refuses(inputs, out, capsys, "sign share")


def test_refuses_on_a_missing_input_file(world, capsys):
    inputs, out = world
    inputs.credible.unlink()
    _assert_refuses(inputs, out, capsys, "missing input")


def test_refuses_on_a_missing_value_rather_than_printing_a_placeholder(world, capsys):
    inputs, out = world
    rows = list(csv.DictReader(inputs.pooled.open(encoding="utf-8")))
    rows[0]["pi_high"] = ""
    _write_csv(inputs.pooled, list(rows[0]), [list(r.values()) for r in rows])
    _assert_refuses(inputs, out, capsys, "pi_high")


def test_refuses_when_the_harvester_has_moved_on_unless_allowed(world, capsys):
    inputs, out = world
    live = json.loads(inputs.harvest_summary.read_text(encoding="utf-8"))
    live |= {"updated_at": "2026-09-25T16:00:00+00:00", "contrasts_after_guards": 40}
    inputs.harvest_summary.write_text(json.dumps(live), encoding="utf-8")
    _assert_refuses(inputs, out, capsys, "moved on")
    assert mod.main(["--out-dir", str(out), "--allow-stale"], inputs=inputs) == 0
    # and the numbers are the analysed snapshot's, never the live ones
    macros = _macros((out / "rq3_macros.tex").read_text(encoding="utf-8"))
    assert macros["rqCorpusContrasts"] == "12"


def test_refuses_a_mixed_snapshot_even_with_allow_stale(world, capsys):
    inputs, out = world
    summary = json.loads(inputs.ablation_summary.read_text(encoding="utf-8"))
    summary["harvest_snapshot"]["consistent"] = False
    inputs.ablation_summary.write_text(json.dumps(summary), encoding="utf-8")
    assert mod.main(["--out-dir", str(out), "--allow-stale"], inputs=inputs) == 2
    assert "different snapshots" in capsys.readouterr().err


def test_refuses_coverage_outputs_from_another_run(world, capsys):
    inputs, out = world
    cov = json.loads(inputs.coverage_corpus_json.read_text(encoding="utf-8"))
    cov["coverage_by_layer"]["total_contrasts"] += 1
    inputs.coverage_corpus_json.write_text(json.dumps(cov), encoding="utf-8")
    _assert_refuses(inputs, out, capsys, "analyse_ablation_coverage.py --corpus")


def test_refuses_once_the_confirmatory_tier3_run_exists(world, capsys):
    inputs, out = world
    (inputs.tier3_dir / "runs.jsonl").write_text("{}\n", encoding="utf-8")
    _assert_refuses(inputs, out, capsys, "confirmatory")


# --------------------------------------------------------------------------- the snapshot


def test_harvest_snapshot_flags_a_contrast_file_the_summary_does_not_describe(tmp_path):
    contrasts = tmp_path / "corpus_ablation_contrasts.csv"
    contrasts.write_text("x\n", encoding="utf-8")
    assert analyse_ablations.harvest_snapshot(contrasts, 5) is None  # no harvester beside it
    (tmp_path / "corpus_ablation_summary.json").write_text(json.dumps(
        {"updated_at": "2026-09-25T15:00:00+00:00", "papers_extracted": 2,
         "contrasts_after_guards": 5}), encoding="utf-8")
    (tmp_path / "corpus_ablation_outcomes.csv").write_text(
        "record_id,tier,status\na,T10,extracted\nb,T10,extracted\nc,T3,pending\n",
        encoding="utf-8")
    snap = analyse_ablations.harvest_snapshot(contrasts, 5)
    assert snap["consistent"] is True
    assert snap["tier_status"] == {"T10": {"extracted": 2}, "T3": {"pending": 1}}
    assert analyse_ablations.harvest_snapshot(contrasts, 6)["consistent"] is False


# --------------------------------------------------------------------------- real outputs


def test_real_outputs_build_and_match_their_sources():
    inputs = mod.Inputs.default()
    if not all(p.exists() for p in inputs.files()):
        pytest.skip("run the RQ3 analysis pipeline first")
    try:
        # the harvester may have moved on since the last analysis run; that is not this test's
        # business, a mixed snapshot is
        frags = mod.build(inputs, allow_stale=True)
    except mod.RQ3InputError as exc:
        pytest.skip(f"real inputs not buildable right now: {exc}")
    pooled = list(csv.DictReader(inputs.pooled.open(encoding="utf-8")))
    assert len(_rows(frags["rq3_pooled.tex"])) == sum(r["pooled"] == "1" for r in pooled)
    macros = _macros(frags["rq3_macros.tex"])
    assert set(REQUIRED_MACROS) <= set(macros)
    assert set(SENSITIVITY_MACROS) <= set(macros)
    assert macros["rqPoolableDims"] == str(sum(r["pooled"] == "1" for r in pooled))
    # the sign-share denominator is the pooled dimensions' contrasts, and its two halves add up
    num = lambda k: int(macros[k].replace("{,}", ""))
    assert num("rqPolarityStatedN") + num("rqPolarityAssumedN") == num("rqSignDenom")
    assert num("rqSignDenom") <= int(macros["rqTotalContrasts"].replace("{,}", ""))


def test_pre_rule_reconstruction_on_the_real_snapshot():
    """With the seven rules undone, the sandbox layer is no longer empty and the rule-applied
    counts reproduce the published rho (the function refuses otherwise)."""
    inputs = mod.Inputs.default()
    if not all(p.exists() for p in inputs.files()):
        pytest.skip("run the RQ3 analysis pipeline first")
    try:
        d = mod.load(inputs)
        res = mod.pre_rule_sensitivity(d, inputs)
    except mod.RQ3InputError as exc:
        pytest.skip(f"the harvester has moved past the pooled snapshot: {exc}")
    assert res["g_contrasts"] > 0 and "G" not in res["zero_layers"]
    assert res["g_contrasts"] == sum(res["moved_out_of_g"].values())
    assert -1.0 <= res["rho"] <= 1.0 and 0.0 < res["p"] <= 1.0
    assert res["dcl"]["against"] <= res["dcl"]["pooled"] <= res["dcl"]["dropped"]


def test_rule_switch_off_changes_only_the_rules():
    """`without_rules` must leave a row no rule touches exactly as the harvester decided it."""
    import analyse_ablations as aa

    keys = aa.design_dimension_keys(aa.load_dimensions())
    row = {"system": "X", "full_arm": "Full X", "ablated_arm": "w/o sandbox",
           "component": "sandbox execution", "category": "ablation",
           "dimension": "execution_isolation", "direction": "component_removed",
           "benchmark": "B", "split": "", "metric": "Accuracy", "base_model": "m",
           "same_base_model": "true", "full_score": "60.0", "ablated_score": "50.0",
           "confidence": "0.8", "evidence": "Full X 60.0 w/o sandbox 50.0", "reason": "r"}
    reason, out = mod.without_rules(row, keys)
    assert reason == "" and out["norm_dimension"] == "execution_isolation"
    # and the real guard (rules on) reassigns the same row to self-verification
    import harvest_ablations_corpus as hv
    reason_on, out_on = hv.guard_row(row, "Full X 60.0 w/o sandbox 50.0", keys)
    assert reason_on == "" and out_on["norm_dimension"] == "self_verification"


def test_non_baseline_keys_on_the_real_outcomes():
    inputs = mod.Inputs.default()
    if not all(p.exists() for p in inputs.files()):
        pytest.skip("run the RQ3 analysis pipeline first")
    d = mod.load(inputs)
    res = mod.non_baseline_sensitivity(d, inputs, mod.CROSS_PAPER_HEADLINE)
    c = next(x for x in d.outcomes["contrasts"] if x["dimension"] == mod.CROSS_PAPER_HEADLINE)
    assert res["n_baseline_keys"] == c["baseline_asymmetry"]["reference_all_recurring_keys"]
    assert res["n_keys"] + res["n_baseline_keys"] == c["n_keys"]
    assert res["ci_low"] <= res["effect"] <= res["ci_high"]
