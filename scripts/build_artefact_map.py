"""Generate paper/sections/S_artefact_map.tex (Supplement S5) and check it is complete.

Completeness checks, all fatal:
  1. every file reference found in paper/sections/*.tex by scan_refs.py (refs.json) is mapped;
  2. every source file named in docs/headline_findings.md and docs/count_reconciliation.md is mapped;
  3. every figure file \\includegraphics'd by the manuscript is mapped;
  4. every artefact and every script named in the table exists on disk.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # repository root
HERE = pathlib.Path(__file__).parent
OUT = ROOT / "paper" / "sections" / "S_artefact_map.tex"

DOC = "document"          # hand-written document, no generating script
FROZEN = "frozen"         # superseded snapshot kept as evidence, not regenerated
PENDING = "pending"       # v2 figure referenced by the rewrite whose file/script is not yet in the package

# (quantity reported, where, [artefacts], [scripts] | DOC | FROZEN | str note)
# "where": \S<n> is the main paper (v2 numbering); S<n> is this supplement.
GROUPS = [
("Search, screening and the flow of records", "tab:artefacts-flow", [
 ("Query issued to each source, its per-source translation, search dates, per-source hit counts",
  r"\S4 (sources); S3 item~7", ["data/raw/search_log.md"], ["scripts/harvest/"]),
 ("Records identified: 37,899 from databases and registers, 12,825 by other methods (grey, snowball, awesome lists)",
  r"\S4 flow diagram", ["data/raw/arxiv.jsonl", "data/raw/s2.jsonl", "data/raw/openalex.jsonl", "data/raw/acl.jsonl",
   "data/raw/openreview.jsonl", "data/raw/github.jsonl", "data/raw/grey.jsonl", "data/raw/leaderboards.jsonl",
   "data/raw/snowball.jsonl", "data/raw/snowball_surveys.jsonl", "data/raw/awesome.jsonl"], ["scripts/harvest/"]),
 ("Duplicates removed (22,977) and unique records screened (27,747)",
  r"\S4 flow diagram", ["data/raw/candidates.csv"], ["scripts/dedupe.py"]),
 (r"Title-and-abstract votes and triage; model--model agreement 0.716 ($\kappa$ 0.564), binarised 0.821 ($\kappa$ 0.616); 13,483 records to a third vote",
  r"\S4 (selection)", ["data/screening/triage.csv", "data/screening/triage_report.md"], ["scripts/screen_triage.py", "scripts/screen_merge.py"]),
 ("Reports sought for retrieval (9,967 distinct records) and not retrieved (1,532)",
  r"\S4 flow diagram", ["data/screening/fulltext_queue.csv"], ["scripts/phase3_autopilot.py"]),
 ("Full-text decisions: 8,435 assessed, 1,350 excluded by code, 7,085 included; escalation coverage 2,073 of 7,085",
  r"\S4 (selection); flow diagram", ["data/screening/fulltext_final_pass1.csv"], ["scripts/fulltext_screen.py", "scripts/phase3_autopilot.py"]),
 ("Every stage count of the PRISMA flow, including 6,504 included systems",
  r"\S4 flow diagram; S3 item~16a; S4, Table~\ref{tab:release-counts}", ["data/prisma_counts.json"],
  ["scripts/phase3_autopilot.py", "scripts/screen_merge.py"]),
 ("Every full-text decision with its deciding step and the quotes behind it",
  r"\S4 (selection); S3 item~16b", ["screening/fulltext_audit.html", "data/screening/fulltext_audit.js"], ["scripts/validate_screening.py"]),
 (r"Independent-pipeline cross-check: agreement 0.843, $\kappa$ 0.664; external recall 308 of its 411 includes (75\%), 103 absent from the candidates; 62 title-stage disagreements covering 61 records",
  r"\S4 (sources) and screening-checks table; \S9", ["data/screening/elicit_crosscheck.json", "data/screening/elicit_disagreement_queue.csv"], ["scripts/elicit_crosscheck.py"]),
 ("Supplementary arm (amendment 7): 987 screened, 411 included, 103 sought, 63 assessed, 37 included",
  r"\S4 flow diagram, right column", ["data/raw/candidates_supplementary.csv", "data/screening/fulltext_votes_supplementary.csv"],
  ["scripts/supplementary_arm.py", "scripts/fulltext_screen.py"]),
 ("Grouping of the 7,085 included papers into 6,504 systems (407 with several member records)",
  r"\S4 (grouping)", ["data/systems_candidates.csv"], ["scripts/system_registry.py"]),
 ("Derivation of every flow count; the 6,172 / 6,501 / 6,504 census reconciliation",
  r"\S4 (grouping)", ["docs/count_reconciliation.md"], DOC),
 ("\\emph{Superseded}: flow counts before the grouping repair (6,172 systems)",
  r"\S4 (grouping); S4", ["data/prisma_counts_pre_regroup.json"], FROZEN),
 ("\\emph{Superseded}: the census before and after the first repair pass (6,172; 6,501)",
  r"\S4 (grouping)", ["data/coded/_pre_regroup_systems_candidates.csv", "data/coded/_pre_regroup2_systems.csv"], FROZEN),
]),
("Protocol, definition, coding frame and coded release", "tab:artefacts-coding", [
 ("Registered protocol (working copy), the eleven accepted amendments, and the pending twelfth with its dated revision (12a)",
  r"\S4 (registration); S2; S3 items~24a--24c", ["docs/protocol_prisma_p.md"], DOC),
 ("Definition of a harness; eligibility criterion (a)",
  r"\S2; \S4 (eligibility); \S3 crosswalk", ["docs/definition.md"], DOC),
 ("Positioning against the seven prior works; layer-level mappings for two prior schemes",
  r"\S3; \S3 crosswalk", ["docs/positioning.md"], DOC),
 ("The coding frame: 9 layers, 38 dimensions, permitted values, multi-valued flags, crosswalk fields",
  r"\S3 crosswalk; \S5 dimension table and taxonomy figure; S1", ["schema/dimensions.json"], "source; checked by \\path{scripts/validate.py}"),
 ("JSON Schema the validator enforces",
  r"S4", ["schema/harness_db.schema.json"], ["scripts/build_schema.py"]),
 ("Schema v1.0.0 freeze; every change from the freeze onward",
  r"\S4 (coding); \S5", ["docs/schema_changelog.md"], DOC),
 ("Coding rules, rule~5 (absence), the 26-entry ambiguity list",
  r"\S4 (coding); \S5; S1", ["docs/coding_manual.md"], DOC),
 ("Two worked examples coded end to end",
  r"S1", ["data/examples/swe-agent-1x.json", "data/examples/openhands.json"], "model pre-fill; see \\path{data/examples/README.md}"),
 ("Sampling frame of 6,504 systems; strata H 984, P 683, O 4,837; weights 1, 4.5533, 48.37; seed",
  r"\S4 (coding); S4", ["data/coding_frame.csv", "data/coding_frame.json"], ["scripts/coding_strata.py"]),
 ("Per-system codings on disk (1,257 systems coded)",
  r"\S4 (coding)", ["data/coded/json/"], ["scripts/code_system.py"]),
 ("Released coded set: 1,256 systems, 47,728 cells; 24,228 valued (50.8\\%), 23,337 \\texttt{not\\_reported} (48.9\\%), 163 \\texttt{unresolved} (0.3\\%)",
  r"\S4 (coding); \S6; S4, Table~\ref{tab:release-counts}; S4, Table~\ref{tab:systems-extract}", ["data/systems.json"], ["scripts/build_tables.py"]),
 ("Release-gate trade-off: a 38-of-38 gate would have admitted 77 of 1,116 systems",
  r"\S4 (coding)", ["scripts/build_tables.py"], "console report of \\path{scripts/build_tables.py}"),
 ("Bibliographic records with inclusion decision and exclusion code",
  r"S4", ["data/papers.csv"], ["scripts/build_tables.py"]),
 ("Per-cell audit: quote, locator, verbatim check (all 24,228 valued released cells pass, by construction: a cell that fails is released as \\texttt{unresolved}), validation flags, provenance",
  r"\S4 (coding); S4", ["data/coded/cells.csv"], ["scripts/code_system.py", "scripts/reclassify_locators.py"]),
 ("Second, independent reading of the double-coded sample",
  r"S4", ["data/coded/cells_pass2.csv", "data/coded/json_pass2/"], ["scripts/code_system.py"]),
 ("Double-coding draw: 245 systems drawn (seed \\texttt{code-2026-09-20}), 247 double-coded",
  r"\S4 (reliability)", ["data/coded/double_sample.json"], ["scripts/code_system.py"]),
 ("Reliability: macro $\\kappa$ 0.784 [0.765, 0.800], AC1 0.855, agreement 0.870; 37 of 38 at $\\kappa \\ge 0.6$; 9,386 cells; per-dimension $\\kappa$ with bootstrap intervals",
  r"\S4 reliability table; \S9; S4, Tables~\ref{tab:release-counts}, \ref{tab:reliability-AE}, \ref{tab:reliability-FM}",
  ["data/coded/reliability_final.json"], ["scripts/kappa.py"]),
 ("Absence-rule experiment: agreement 0.597 to 0.872, stacked $\\kappa$ 0.564 to 0.832; \\texttt{not\\_reported} share 26.9\\% to 48.3\\%",
  r"\S4 reliability table; \S6; \S9; S2", ["data/coded/rule5_experiment.json", "docs/coding_reliability.md"], "none in the package; see note"),
 ("Unweighted \\texttt{not\\_reported} rate per dimension (highest: \\texttt{replayability} 85.1\\%)",
  r"S1", ["data/coded/not_reported_by_dimension.csv"], "reproduced by \\path{scripts/analyse_descriptives.py}"),
 ("\\emph{Superseded}: the complete coding under the pre-amendment-9 absence rule",
  r"\S4 (reliability); \S6; \S9; S4", ["data/coded/v1_rule5_ambiguous/"], FROZEN),
 ("Licences of the code and of the data",
  r"S4", ["LICENSE-CODE", "LICENSE-DATA"], DOC),
]),
("Landscape of the coded systems", "tab:artefacts-landscape", [
 ("Weighted and unweighted value distributions; \\texttt{primary\\_artifact} inversion (867 of 1,252, 69.2\\%, coded; 33.3\\% weighted); seven modal changes; MCP 400 of 487",
  r"\S6 (weighting) and modal-change table; S6 value-distribution figure", ["data/analysis/value_distributions.csv"], ["scripts/analyse_descriptives.py"]),
 ("Per-dimension \\texttt{not\\_reported} rate, weighted and unweighted (\\texttt{network\\_policy} 93.3\\%)",
  r"\S6 layer table; \S8 checklist table; S6 under-reporting figure and full checklist", ["data/analysis/under_reporting_by_dimension.csv"], ["scripts/analyse_descriptives.py"]),
 ("Layer-level silence rates with system-clustered design standard errors (G 81.6\\% $\\pm$ 1.8, C 24.9\\% $\\pm$ 1.2)",
  r"\S6 layer table", ["data/analysis/summary_one_screen.csv", "data/analysis/summary_one_screen.md"], ["scripts/analyse_descriptives.py"]),
 ("Silence by layer and year",
  r"replication package only", ["data/analysis/under_reporting_layer_year.csv"], ["scripts/analyse_descriptives.py"]),
 ("Entropy by dimension and year; the stratum mix of each cohort (H 65.2\\% to 83.8\\% of the 2023--2026 cohorts)",
  r"\S4 (synthesis); \S6 (convergence); S6 entropy-trajectory figure", ["data/analysis/entropy_by_dimension_year.csv"], ["scripts/analyse_descriptives.py"]),
 ("Convergence verdicts (coded set, unweighted): 10 of 34 intervals exclude zero, 9 survive Benjamini--Hochberg (3 converged, 6 diversified), 25 stable",
  r"\S6 (convergence)", ["data/analysis/convergence_summary.csv"], ["scripts/analyse_descriptives.py"]),
 ("Design-family clustering: $k = 8$, silhouette 0.120, stability 0.540, verdict negative; three provisional clusters",
  r"\S6 (families), bars table and dendrogram; \S8", ["data/analysis/family_summary.json", "data/analysis/family_cluster_summary.csv"], ["scripts/analyse_families.py"]),
 ("Pairwise association: mean corrected Cram\\'er's V 0.167 on 666 pairs; 385 against 648 significant; 265 pairs significant only with silence as a level",
  r"\S6 (associations) and association table; S6 association-change figure", ["data/analysis/family_associations.csv", "data/analysis/family_nr_flips.csv"], ["scripts/analyse_families.py"]),
]),
("Design choices against outcomes", "tab:artefacts-outcomes", [
 ("Extracted scores: 5,863 result rows, 1,138 distinct benchmark values, 646 systems reporting any score",
  r"\S4 (reliability); \S7 (comparable set); S3 item~19", ["data/results.csv"],
  ["scripts/extract_results.py", "scripts/leaderboards_to_results.py", "scripts/mark_comparable.py"]),
 ("Comparable set: 53 systems (4.2\\%) sharing a key, 36 keys, 106 observations",
  r"\S3; \S7 (comparable set)", ["paper/tables/outcomes_comparable_set.csv"], ["scripts/analyse_outcomes.py"]),
 ("Five pre-specified contrasts; \\texttt{multi\\_agent\\_topology} $+0.877$ [$+0.379$, $+1.313$], permutation $p = 0.0013$, 18 keys, 38 systems; minimum detectable effects",
  r"\S7 (comparable set), in prose; abstract; \S1; \S10", ["paper/tables/outcomes_contrasts.csv"], ["scripts/analyse_outcomes.py"]),
 ("Coverage funnel from coded systems to systems sharing a comparable key (1,256; 646; 100; 53)",
  r"\S7 (comparable set), in prose", ["paper/tables/outcomes_summary.json"], ["scripts/analyse_outcomes.py"]),
 ("Coded-set ablation harvest: 75 contrasts over 42 papers and 14 dimensions; 67 of 75 favour the authors' component",
  r"\S7 (published ablations; publication bias); \S9", ["data/analysis/ablation_contrasts.csv"], ["scripts/analyse_ablations.py"]),
 ("Coded-set harvest only: pooled effects with CI, prediction interval, $I^2$ and discount (\\texttt{self\\_verification} $+0.139$ to $+0.069$)",
  r"\S7 (published ablations), in prose", ["data/analysis/ablation_pooled.csv", "data/analysis/ablation_credible.csv"], ["scripts/analyse_ablations.py"]),
 ("Coded-set publication-bias diagnostics: trim-and-fill, Egger, size-based test, null-fill count",
  r"replication package only; the discount they feed is in \S7", ["data/analysis/ablation_bias.csv"], ["scripts/analyse_ablations.py"]),
 ("Coded-set harvest losses: 1,008 labels classified, 545 labels unmapped, 353 rows model or training variants, each drop with its reason",
  r"replication package only", ["data/analysis/ablation_drops.csv"], ["scripts/analyse_ablations.py"]),
 ("Sensitivity to assumed benchmark size and confidence floor",
  r"replication package only", ["data/analysis/ablation_sensitivity_n.csv", "data/analysis/ablation_sensitivity_confidence.csv"], ["scripts/analyse_ablations.py"]),
 ("Coded-set ablation coverage by layer (secondary): zero contrasts in F, G, H; Spearman $\\rho = \\rqCodedCoverageRho$, exact one-sided $p = \\rqCodedCoverageP$",
  r"\S7 (where the field ablates), in prose; \S1; \S8", ["data/analysis/ablation_coverage_by_layer.csv", "data/analysis/ablation_coverage_summary.json"], ["scripts/analyse_ablation_coverage.py"]),
 ("Own-arm test on the corrected baseline: 42 of 75 ($p = 0.061$; paper-clustered $p = 0.21$), 5+-arm blocks 14 of 17 against 6.95",
  r"\S7 (publication bias), in prose", ["data/analysis/blocks_own_arm_test.csv", "data/analysis/ablation_coverage_summary.json"], ["scripts/analyse_ablation_coverage.py"]),
 ("Baseline blocks: 324 estimable from 131 papers; 784 of 819 comparator arms unattributable; minimum detectable effects 1.39--3.27",
  r"\S7 (within-paper comparisons), in prose", ["data/analysis/blocks_summary.json", "data/analysis/blocks_attribution.csv"], ["scripts/analyse_blocks.py"]),
 ("Comparator alias table: 555 (label, paper) pairs judged; 15 accepted mappings with corroborating offsets, 1,684 refusals with reasons",
  r"\S7 (within-paper comparisons); \S4 implementation table", ["data/comparator_aliases.csv", "data/comparator_aliases_refused.csv"], ["scripts/build_alias_table.py"]),
 ("Controlled ablation, pilot: nine suite-and-tier cells against the 25--70\\% band",
  r"\S7 (controlled ablation); inset of the design figure", ["data/tier3/pilot/pilot_summary.json"], ["scripts/tier3_ablation.py"]),
 ("Controlled ablation, arm-B diagnostics: 56 runs, first attempt accepted 50 times, three of those scored 0.00",
  r"\S7 (controlled ablation); \S1", ["data/tier3/diagnostic/"], ["scripts/tier3_ablation.py"]),
 ("Controlled-ablation design, frozen 2026-09-24 (amendment 12), and its dated revision of 2026-09-25 (amendment 12a)",
  r"\S4 (registration); \S7; \S8; \S9; S2", ["docs/tier3_ablation_protocol.md"], DOC),
 ("Controlled-ablation pilot under amendment 12a: B-fixed and B-ext arms, arms A and B only; the original arm accepted its first attempt in 41 of 48 runs; 22 clean confirmatory instances against 93 required",
  r"\S7 (controlled ablation); \S1; \S8; \S10", ["data/tier3/pilot_v2/"], ["scripts/tier3_ablation.py"]),
 ("Visible (public-example) checks for the v2 B-ext arm, disjoint from the hidden tests by construction",
  r"\S7 (controlled ablation)", ["data/tier3/suites/visible/"], ["scripts/tier3_ablation.py"]),
 ("Corpus-wide ablation harvest: prefilter, windows, proposed rows, guard funnel and per-paper outcomes",
  r"\S7 (published ablations)", ["data/analysis/corpus_ablation_prefilter.csv", "data/analysis/corpus_ablation_rows.csv",
   "data/analysis/corpus_ablation_contrasts.csv", "data/analysis/corpus_ablation_guard_funnel.csv",
   "data/analysis/corpus_ablation_outcomes.csv", "data/analysis/corpus_ablation_summary.json"],
  ["scripts/harvest_ablations_corpus.py"]),
 ("Report-time mapping guards: every row a rule remapped or dropped, with the rule named",
  r"\S7 (where the field ablates)", ["data/analysis/corpus_ablation_guard_audit.csv"], ["scripts/harvest_ablations_corpus.py"]),
 ("Pooled ablations over both harvests, with Hartung-Knapp intervals and provenance: \\rqDiscountSurviveZ{} of \\rqPoolableDims{} dimensions pass the discount; \\texttt{self\\_verification} \\rqSVPooled{}, discounted \\rqSVDiscounted{}",
  r"\S7 pooled-ablation table; abstract; \S1; \S8; \S10", ["data/analysis/ablation_contrasts_corpus.csv", "data/analysis/ablation_pooled_corpus.csv",
   "data/analysis/ablation_credible_corpus.csv", "data/analysis/ablation_bias_corpus.csv", "data/analysis/ablation_summary_corpus.json"],
  ["scripts/analyse_ablations.py"]),
 ("Ablation density by layer over both harvests: zero contrasts only in layer G; \\rqZeroDimCount{} of \\rqAblatableDimCount{} dimensions without a contrast; Spearman $\\rho = \\rqCoverageRho$, exact one-sided $p = \\rqCoverageP$",
  r"\S7 coverage table; \S1; \S8; \S10", ["data/analysis/ablation_coverage_by_layer_corpus.csv", "data/analysis/ablation_coverage_summary_corpus.json"],
  ["scripts/analyse_ablation_coverage.py"]),
 ("RQ3 build-time fragments and macros: every corpus-derived number in section 7 and the abstract",
  r"\S7 tables; abstract; \S1; \S8--\S10", ["paper/tables/rq3_macros.tex", "paper/tables/rq3_pooled.tex",
   "paper/tables/rq3_coverage.tex", "paper/tables/rq3_designs.tex"], ["scripts/make_rq3_tables.py"]),
 ("Section 5 dimension table and the S1 per-layer coding sheet, generated from the schema",
  r"\S5 dimension table; S1", ["paper/sections/05_unified_taxonomy.tex", "paper/sections/A1_coding_sheet.tex"],
  ["scripts/taxonomy_tables/gen_taxonomy_tables.py", "scripts/taxonomy_tables/verify_taxonomy.py"]),
 ("This artefact map",
  r"S5", ["paper/sections/S_artefact_map.tex"], ["scripts/build_artefact_map.py", "scripts/scan_refs.py"]),
 ("The five cross-cutting benchmark caveats and their directions",
  r"\S4 (reporting bias); \S8; \S9; S3 item~11", ["docs/benchmark_caveats.md"], DOC),
]),
("Figures", "tab:artefacts-figures", [
 ("Pipeline overview with the count at each stage (teaser)", r"\S1", ["paper/figures/pipeline_overview.pdf"], ["scripts/plot_frameworks.py"]),
 ("PRISMA 2020 flow diagram", r"\S4", ["paper/figures/prisma_flow.pdf"], ["scripts/prisma_diagram.py"]),
 ("Screening framework", r"\S4", ["paper/figures/screening_framework.pdf"], ["scripts/plot_frameworks.py"]),
 ("Coding framework and the three-state cell contract", r"\S4", ["paper/figures/coding_framework.pdf"], ["scripts/plot_frameworks.py"]),
 ("Compute-matched ablation design with the pilot inset", r"\S7", ["paper/figures/tier3_design.pdf"], ["scripts/plot_frameworks.py"]),
 ("RQ3 triangulation: three designs by what each identifies", r"\S7", ["paper/figures/rq3_triangulation.pdf"], ["scripts/plot_frameworks.py"]),
 ("Unified taxonomy map", r"\S5", ["paper/figures/taxonomy_map.pdf"], ["scripts/plot_taxonomy.py"]),
 ("Value distributions under weighting; under-reporting by dimension; entropy trajectories",
  r"S6", ["paper/figures/descriptives_value_distributions.pdf", "paper/figures/descriptives_under_reporting_by_dimension.pdf",
   "paper/figures/descriptives_entropy_trajectories.pdf"], ["scripts/analyse_descriptives.py"]),
 ("Under-reporting by layer and year; entropy by year",
  r"replication package only", ["paper/figures/descriptives_under_reporting_layer_year.pdf",
   "paper/figures/descriptives_entropy_by_year.pdf"], ["scripts/analyse_descriptives.py"]),
 ("Dendrogram with the silhouette curve against its null",
  r"\S6 (families)", ["paper/figures/family_dendrogram.pdf"], ["scripts/analyse_families.py"]),
 ("Pair-by-pair association change when silence is a level",
  r"S6", ["paper/figures/family_association_delta.pdf"], ["scripts/analyse_families.py"]),
 ("MDS map of the provisional clusters; association matrix",
  r"replication package only", ["paper/figures/family_clusters_mds.pdf", "paper/figures/family_association_matrix.pdf"],
  ["scripts/analyse_families.py"]),
 ("Comparable-set coverage, comparable set and contrasts",
  r"replication package only", ["paper/figures/outcomes_coverage.pdf", "paper/figures/outcomes_comparable_set.pdf", "paper/figures/outcomes_contrasts.pdf"],
  ["scripts/analyse_outcomes.py"]),
 ("Forest plot per pooled dimension, coded-set and corpus-wide, and the ablation funnels",
  r"replication package only", ["paper/figures/ablation_forest_*.pdf", "paper/figures/ablation_funnel.pdf",
   "paper/figures/ablation_funnel_corpus.pdf"], ["scripts/analyse_ablations.py"]),
 ("Own-arm rank, block contrasts and block funnel",
  r"replication package only", ["paper/figures/blocks_own_arm_rank.pdf", "paper/figures/blocks_contrasts.pdf", "paper/figures/blocks_funnel.pdf"],
  ["scripts/analyse_blocks.py"]),
]),
]

# Scanned references that do not name the artefact's real path.
ALIASES = {
    "ablation_coverage_summary.json": "data/analysis/ablation_coverage_summary.json",
    "ablation_credible.csv": "data/analysis/ablation_credible.csv",
    "data/screening/fulltext_audit.html": "screening/fulltext_audit.html",
    # per-system coding files named by basename in docs/count_reconciliation.md; con.json is named
    # there as the file that could NOT be written (Windows reserved name), stored as con-sys.json
    "agent-s-v2.json": "data/coded/json/agent-s-v2.json",
    "agentk.json": "data/coded/json/agentk.json",
    "con.json": "data/coded/json/con-sys.json",
    "con-sys.json": "data/coded/json/con-sys.json",
}


def exists(p):
    if "*" in p:
        return any(ROOT.glob(p))
    return (ROOT / p.rstrip("/")).exists()


def covered(path, artefacts, scripts):
    path = ALIASES.get(path, path)
    if path in artefacts or path in scripts:
        return True
    if path.endswith("/"):  # a directory reference is mapped if any artefact lives under it
        return any(a.startswith(path) for a in artefacts)
    for a in artefacts:  # a file under a mapped directory is mapped by that row
        if a.endswith("/") and path.startswith(a):
            return True
    if path.startswith("paper/figures/"):
        return any(pathlib.PurePath(path).match(a) for a in artefacts if "*" in a)
    return False


def main():
    artefacts, scripts, rows = set(), set(), 0
    pending = []
    problems = []
    for _, _, items in GROUPS:
        for q, where, arts, scr in items:
            rows += 1
            for a in arts:
                artefacts.add(a)
                if scr == PENDING:
                    pending.append(a if not exists(a) else a + " (file now exists: give it its script)")
                    continue
                if not exists(a):
                    problems.append(f"artefact missing on disk: {a}")
            if isinstance(scr, list):
                for s in scr:
                    scripts.add(s)
                    if not exists(s):
                        problems.append(f"script missing on disk: {s}")
    # 1. manuscript references
    refs = json.loads((HERE / "refs.json").read_text())
    ms_files = sorted({r["file"] for r in refs})
    unmapped = [f for f in ms_files if not covered(f, artefacts, scripts)]
    # 2. headline / reconciliation sources
    doc_files = set()
    for d in ("docs/headline_findings.md", "docs/count_reconciliation.md"):
        for m in re.finditer(r"`([A-Za-z0-9_./\-*]+\.(?:csv|json|jsonl|md|py|html))`", (ROOT / d).read_text(encoding="utf-8")):
            doc_files.add(m.group(1))
    def resolve(name):
        if "/" in name and exists(name):
            return name
        hits = [a for a in artefacts | scripts if a.endswith("/" + name) or a == name]
        return hits[0] if hits else name
    doc_unmapped = []
    for f in sorted(doc_files):
        r = resolve(f)
        if r in ("docs/headline_findings.md",):
            continue  # the memo itself
        if not covered(r, artefacts, scripts) and not any(a.endswith(pathlib.PurePath(f).name) for a in artefacts):
            doc_unmapped.append(f)
    # 3. figures
    figs = set()
    for tex in (ROOT / "paper" / "sections").glob("*.tex"):
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex.read_text(encoding="utf-8")):
            figs.add("paper/figures/" + m.group(1) + ".pdf")
    fig_unmapped = [f for f in sorted(figs) if not covered(f, artefacts, scripts)]
    print(f"rows: {rows}; distinct artefacts: {len(artefacts)}; scripts: {len(scripts)}")
    print(f"manuscript file refs: {len(ms_files)} distinct; unmapped: {unmapped}")
    print(f"doc-named sources: {len(doc_files)}; unmapped: {doc_unmapped}")
    print(f"figures included: {len(figs)}; unmapped: {fig_unmapped}")
    print("aliased (manuscript names a path that is not the artefact's):", ALIASES)
    for p in problems:
        print("PROBLEM:", p)
    for p in pending:
        print("PENDING (not fatal):", p)
    write_tex()
    if unmapped or doc_unmapped or fig_unmapped or problems:
        sys.exit(1)


def cell_paths(paths):
    return r" \newline ".join(rf"\path{{{p}}}" for p in paths)


def cell_script(s):
    if s == DOC:
        return r"\emph{document}"
    if s == PENDING:
        return r"\emph{pending: figure of the v2 rewrite, not yet in the package}"
    if s == FROZEN:
        return r"\emph{frozen, superseded}"
    if isinstance(s, str):
        return rf"\emph{{{s}}}"
    return cell_paths(s)


INTRO = r"""\section{Artefact map}
\label{app:artefacts}

The main paper names no files. This supplement restores the traceability that choice removes:
Tables~\ref{tab:artefacts-flow}--\ref{tab:artefacts-figures} map each quantity the paper reports to
the place it is reported, the artefact in the replication package that carries it, and the script that
regenerates that artefact. A section sign (\S) refers to the main paper and S1--S6 to this supplement;
display items of the main paper are named by what they show rather than by number, a quantity the paper
states only in its text is marked \emph{in prose}, and an artefact no display item of either document
shows is marked \emph{replication package only}. The table was
generated by a script from the manuscript itself: every file reference in the drafted text and every
source named by the project's headline-findings memo and count reconciliation is mapped to a row, and
the generator fails if any is left over or if any artefact or script it names is absent from the
package.

Every figure in the paper, and every number drawn from an analysis output, regenerates from the
released data with one command, \texttt{make figures}, which runs the eight figure-generating scripts
in the last table, \path{scripts/analyse_ablation_coverage.py}, \path{scripts/make_rq3_tables.py} and
\path{scripts/build_explorer.py}; \texttt{make verify} validates the
released data against its schema and runs the test suite. The upstream artefacts those scripts read
--- the flow counts, the coded set and the reliability file --- are regenerated by the scripts named in
their own rows. A row marked \emph{document} is a hand-written record (the protocol, the coding manual,
the definition) that is released as it stands. A row marked \emph{frozen, superseded} is an artefact
that the current pipeline no longer produces and that is published because it is the evidence for an
amendment: the coding under the pre-amendment-9 absence rule
(\path{data/coded/v1_rule5_ambiguous/}), and the PRISMA counts and census from before the
system-grouping repair of amendment~10 (\path{data/prisma_counts_pre_regroup.json} and the two
\path{_pre_regroup} census files). Neither may be merged with the current release; each is kept so that
a reader can check the amendment against the data it changed.
"""

NOTE = r"""
\begin{sloppypar}
One quantity has no regenerating script in the package: the absence-rule experiment
(\path{data/coded/rule5_experiment.json}) records the agreement of the trial recoding under the old and
the rewritten rule~5, and its derivation is described in \path{docs/coding_reliability.md} rather than
scripted. The full-text audit page is \path{screening/fulltext_audit.html}; its data file is written to
\path{data/screening/}.
\end{sloppypar}
"""

CAPTIONS = {
    "tab:artefacts-flow": "Artefact map, part 1: search, screening and the flow of records.",
    "tab:artefacts-coding": "Artefact map, part 2: protocol, definition, coding frame and the coded release.",
    "tab:artefacts-landscape": "Artefact map, part 3: the landscape of the coded systems.",
    "tab:artefacts-outcomes": "Artefact map, part 4: design choices against outcomes.",
    "tab:artefacts-figures": "Artefact map, part 5: the figures and the script that draws each from the data.",
}
MAX_ROWS = 12  # rows per float before a table part is split


def write_tex():
    out = [
        "% GENERATED by build_artefact_map.py (replication package) from a scan of",
        "% paper/sections/*.tex, docs/headline_findings.md and docs/count_reconciliation.md.",
        "% Do not hand-edit rows; regenerate. Section numbers follow the v2 outline (1 intro ... 10 conclusion).",
        INTRO,
        NOTE,
    ]
    for title, label, items in GROUPS:
        n_parts = -(-len(items) // MAX_ROWS)  # balanced split, never a stub table
        size = -(-len(items) // n_parts)
        chunks = [items[i:i + size] for i in range(0, len(items), size)]
        for k, chunk in enumerate(chunks):
            cap = CAPTIONS[label] + ("" if len(chunks) == 1 else f" ({k + 1} of {len(chunks)})")
            lab = label if k == 0 else f"{label}-{k + 1}"
            out.append(r"\begin{table}[htbp]")
            out.append(rf"\caption{{{cap}}}")
            out.append(rf"\label{{{lab}}}")
            out.append(r"\footnotesize")
            out.append(r"\begin{tabular}{@{}p{0.28\linewidth} p{0.17\linewidth} p{0.26\linewidth} p{0.20\linewidth}@{}}")
            out.append(r"\toprule")
            out.append(r"quantity reported & where reported & artefact & regenerating script \\")
            out.append(r"\midrule")
            for q, where, arts, scr in chunk:
                out.append(rf"\raggedright {q} & \raggedright {where} & \raggedright {cell_paths(arts)} & \raggedright {cell_script(scr)} \tabularnewline")
            out.append(r"\bottomrule")
            out.append(r"\end{tabular}")
            out.append(r"\end{table}")
            out.append("")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
