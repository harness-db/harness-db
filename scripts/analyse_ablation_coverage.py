"""Two derived statistics for finding 7 that no other script owns.

1. `ablation_coverage_by_layer.csv` - ablation density per HARNESS-DB layer against that layer's
   weighted `not_reported` rate, with a Spearman rank correlation and an EXACT permutation p.
   Layer M is excluded from the correlation: metadata dimensions (`open_source`, `first_release_date`)
   cannot be ablated, so a zero there carries no information. `analyse_ablations.py` enforces the same
   exclusion when it demotes layer-M classifications.

2. `blocks_own_arm_test.csv` - the own-arm-ranks-first share against the chance baseline implied by
   each block's RIVAL arm count. The baseline VARIES BY BLOCK, so a plain binomial test is wrong;
   this computes the exact Poisson-binomial tail by DP. The baseline is one over the arms that are
   NOT the reporting paper's own switched-off configurations (`1 / max(n_arms - n_ablation_arms, 1)`),
   because an ablation arm was never an independently chosen comparator; the superseded `1 / n_arms`
   version is reported beside it, labelled, and the paper-clustered p from `analyse_blocks.py` is
   carried through because 75 blocks from 37 papers are not independent Bernoullis.

Both are absence-of-evidence statistics. They say what this corpus published, not what is true of
harnesses.

`--corpus` recomputes statistic 1 only, over `ablation_contrasts_corpus.csv` - the coded-set harvest
UNION the corpus-wide full-text harvest (`scripts/harvest_ablations_corpus.py`, pooled by
`scripts/analyse_ablations.py --corpus`), whose `provenance` column says which harvest each contrast
came from. It writes `ablation_coverage_by_layer_corpus.csv` (the same layer table plus the
per-provenance contrast counts and the paper count) and `ablation_coverage_summary_corpus.json`,
which adds the per-DIMENSION zero list (every ablatable dimension with no contrast at all, whether or
not the rest of its layer is touched) to the per-layer one. The own-arm test is about the coded-set
comparison blocks and is not re-run. The default outputs are not touched by `--corpus`.

Run: python scripts/analyse_ablation_coverage.py
     python scripts/analyse_ablation_coverage.py --corpus
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from collections import Counter
from collections.abc import Sequence
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIMENSIONS = ROOT / "schema" / "dimensions.json"
CONTRASTS = ROOT / "data" / "analysis" / "ablation_contrasts.csv"
CONTRASTS_CORPUS = ROOT / "data" / "analysis" / "ablation_contrasts_corpus.csv"
BLOCKS_SUMMARY = ROOT / "data" / "analysis" / "blocks_summary.json"
NR_BY_DIM = ROOT / "data" / "analysis" / "under_reporting_by_dimension.csv"  # regenerated with every release
#: Layer rows of the one-screen summary: the weighted silence share over cells per layer, which is what
#: the landscape table prints. Preferred over averaging per-dimension rates, so the two tables agree.
LAYER_SUMMARY = ROOT / "data" / "analysis" / "summary_one_screen.csv"
OUT_DIR = ROOT / "data" / "analysis"

#: Layer M is metadata: nothing can be ablated from it, so it is excluded from the correlation.
NON_ABLATABLE_LAYER = "M"

#: `--corpus`: the provenance value `analyse_ablations.py` gives the coded-set harvest's contrasts.
PROVENANCE_CODED = "coded_harvest"
CORPUS_SUFFIX = "_corpus"

#: Above this many layers the exact permutation enumeration is refused rather than silently sampled.
MAX_EXACT_N = 10

log = logging.getLogger("ablation_coverage")


# --------------------------------------------------------------------------- stats


def ranks(values: Sequence[float]) -> list[float]:
    """Average ranks, ties shared - the tie handling Spearman requires."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = shared
        i = j + 1
    return out


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    rx, ry = ranks(xs), ranks(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    if den == 0:
        return 0.0
    return num / den


def spearman_exact_p(xs: Sequence[float], ys: Sequence[float], *, negative: bool) -> float:
    """Exact one-sided permutation p for Spearman: enumerate every relabelling of y.

    With <= 10 layers this is at most 3.6M orderings, so the p-value is exact rather than
    approximated from a t-distribution that a sample of 8 does not justify.
    """
    n = len(xs)
    if n > MAX_EXACT_N:
        raise ValueError(f"exact enumeration refused for n={n} (> {MAX_EXACT_N})")
    rho = spearman(xs, ys)
    rx = ranks(xs)
    ry = ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    if den == 0:
        return 1.0
    hits = total = 0
    for perm in permutations(ry):
        stat = sum((a - mx) * (b - my) for a, b in zip(rx, perm)) / den
        if (stat <= rho) if negative else (stat >= rho):
            hits += 1
        total += 1
    return hits / total


def poisson_binomial_tail(probs: Sequence[float], observed: int) -> tuple[float, float]:
    """Exact P(X >= observed) for independent Bernoullis with DIFFERENT probabilities.

    Returns (expected, p). Each block contributes its own success probability - one over its rival
    arms - so the ordinary binomial test does not apply. Independence is the assumption this tail
    cannot repair; that is what the paper-clustered Monte Carlo beside it is for.
    """
    dist = [1.0]
    for p in probs:
        nxt = [0.0] * (len(dist) + 1)
        for i, mass in enumerate(dist):
            nxt[i] += mass * (1.0 - p)
            nxt[i + 1] += mass * p
        dist = nxt
    return sum(probs), sum(dist[observed:])


# --------------------------------------------------------------------------- inputs


def load_layers(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("dimensions", raw) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        records = list(records.values())
    return {d["key"]: d["layer"] for d in records}


def load_layer_silence_from_summary(path: Path) -> dict[str, float]:
    """Weighted not_reported share per layer (percent) from the one-screen summary's layer rows.

    Returns an empty dict when the file or its layer rows are absent, so the caller can fall back.
    """
    if not path.exists():
        return {}
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: dict[str, float] = {}
    for r in rows:
        if (r.get("level") or "").strip().lower() != "layer":
            continue
        layer = (r.get("layer") or "").strip()
        raw = r.get("rate_not_reported_weighted")
        if not layer or raw in (None, ""):
            continue
        try:
            val = float(raw)
        except ValueError:
            continue
        out[layer] = val * 100.0 if val <= 1.0 else val
    if out:
        log.info("layer silence from %s (layer rows, weighted share over cells)", path.name)
    return out


def load_nr_by_layer(path: Path, key_to_layer: dict[str, str]) -> dict[str, float]:
    """Weighted not_reported rate per layer, averaged over that layer's dimensions.

    Falls back to the unweighted column when the weighted one is absent, and says which it used.
    """
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise ValueError(f"{path} is empty")
    cols = rows[0].keys()
    col = next(
        (c for c in ("rate_weighted", "weighted_not_reported_rate", "weighted_rate", "not_reported_rate", "rate")
         if c in cols),
        None,
    )
    if col is None:
        raise ValueError(f"{path} has no recognisable rate column; saw {sorted(cols)}")
    keycol = next((c for c in ("dimension", "key", "dimension_key") if c in cols), None)
    if keycol is None:
        raise ValueError(f"{path} has no dimension column; saw {sorted(cols)}")
    log.info("layer silence from %s column %r", path.name, col)
    acc: dict[str, list[float]] = {}
    for r in rows:
        layer = key_to_layer.get(r[keycol])
        if layer is None:
            continue
        try:
            val = float(r[col])
        except (TypeError, ValueError):
            continue
        acc.setdefault(layer, []).append(val * 100.0 if val <= 1.0 else val)
    return {k: sum(v) / len(v) for k, v in acc.items() if v}


# --------------------------------------------------------------------------- analyses


def coverage_by_layer(
    key_to_layer: dict[str, str],
    contrast_counts: Counter,
    nr_by_layer: dict[str, float],
) -> tuple[list[dict], dict]:
    dims: Counter = Counter()
    ablated: Counter = Counter()
    contrasts: Counter = Counter()
    for key, layer in key_to_layer.items():
        dims[layer] += 1
        if contrast_counts.get(key):
            ablated[layer] += 1
            contrasts[layer] += contrast_counts[key]

    rows = []
    for layer in sorted(dims):
        rows.append({
            "layer": layer,
            "not_reported_pct": round(nr_by_layer.get(layer, float("nan")), 1),
            "dimensions": dims[layer],
            "dimensions_ablated": ablated[layer],
            "contrasts": contrasts[layer],
            "contrasts_per_dimension": round(contrasts[layer] / dims[layer], 3),
            "in_correlation": layer != NON_ABLATABLE_LAYER,
        })

    usable = [r for r in rows if r["in_correlation"] and not math.isnan(r["not_reported_pct"])]
    xs = [r["not_reported_pct"] for r in usable]
    ys = [r["contrasts_per_dimension"] for r in usable]
    rho = spearman(xs, ys)
    pval = spearman_exact_p(xs, ys, negative=True)
    zero = [r["layer"] for r in usable if r["contrasts"] == 0]
    zero_dims = [k for k, lay in sorted(key_to_layer.items()) if lay in zero]
    stats = {
        "layers_in_correlation": [r["layer"] for r in usable],
        "excluded_layers": [r["layer"] for r in rows if not r["in_correlation"]],
        "exclusion_reason": "metadata dimensions cannot be ablated",
        "spearman_rho": round(rho, 4),
        "exact_permutation_p_one_sided": round(pval, 6),
        "permutations": math.factorial(len(usable)),
        "zero_contrast_layers": zero,
        "zero_contrast_dimensions": zero_dims,
        "n_zero_contrast_dimensions": len(zero_dims),
        "reading": (
            "Ablation density falls as a layer's silence rises. Layers with no published ablation at "
            "all are an absence of evidence about the literature, not evidence those components do "
            "not matter."
        ),
    }
    return rows, stats


def load_corpus_contrasts(path: Path) -> list[dict[str, str]]:
    """Rows of `ablation_contrasts_corpus.csv`; refuses a file without the columns it needs."""
    if not path.exists():
        raise SystemExit(f"{path} not found: run scripts/analyse_ablations.py --corpus first")
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in ("record_id", "dimension", "provenance")
                   if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"{path}: missing column(s) {missing}")
        rows = list(reader)
    if not rows:
        raise SystemExit(f"{path} has no contrasts")
    return rows


def corpus_coverage(
    key_to_layer: dict[str, str],
    contrast_rows: Sequence[dict[str, str]],
    nr_by_layer: dict[str, float],
) -> tuple[list[dict], dict]:
    """`coverage_by_layer` over the coded-set + corpus-wide union, with the provenance split.

    The layer table and the Spearman statistic come from `coverage_by_layer` itself, so the two
    modes cannot drift apart; this adds the per-provenance counts, the paper count per layer, and
    the per-dimension zero list. The per-LAYER zero list (`zero_contrast_layers`) only names layers
    where nothing at all was ablated: once a harvest touches one dimension of a layer the layer drops
    out of it while its other dimensions may still be empty, so the dimension list is the one to
    quote.
    """
    counts = Counter(r["dimension"] for r in contrast_rows)
    rows, stats = coverage_by_layer(key_to_layer, counts, nr_by_layer)

    coded: Counter = Counter()
    papers: dict[str, set[str]] = {}
    for r in contrast_rows:
        layer = key_to_layer[r["dimension"]]
        if r["provenance"] == PROVENANCE_CODED:
            coded[layer] += 1
        papers.setdefault(layer, set()).add(r["record_id"])
    for row in rows:
        layer = row["layer"]
        row["contrasts_coded_harvest"] = coded[layer]
        row["contrasts_other_harvests"] = row["contrasts"] - coded[layer]
        row["papers"] = len(papers.get(layer, ()))

    ablatable = {k: lay for k, lay in key_to_layer.items() if lay != NON_ABLATABLE_LAYER}
    zero_dims = sorted(k for k in ablatable if not counts.get(k))
    zero_by_layer: dict[str, list[str]] = {}
    for k in zero_dims:
        zero_by_layer.setdefault(ablatable[k], []).append(k)
    provenances = sorted({r["provenance"] for r in contrast_rows})
    rho, pval = stats["spearman_rho"], stats["exact_permutation_p_one_sided"]
    direction = "falls" if rho < 0 else "does not fall"
    stats |= {
        "mode": "corpus: coded-set harvest + corpus-wide full-text harvest",
        "total_contrasts": len(contrast_rows),
        "total_papers": len({r["record_id"] for r in contrast_rows}),
        "contrasts_by_provenance": {
            prov: sum(1 for r in contrast_rows if r["provenance"] == prov) for prov in provenances
        },
        "papers_by_provenance": {
            prov: len({r["record_id"] for r in contrast_rows if r["provenance"] == prov})
            for prov in provenances
        },
        "contrasts_by_dimension": {k: counts.get(k, 0) for k in sorted(ablatable)},
        "dimensions_without_contrast": zero_dims,
        "n_dimensions_without_contrast": len(zero_dims),
        "n_ablatable_dimensions": len(ablatable),
        "dimensions_without_contrast_by_layer": zero_by_layer,
        "reading": (
            f"Corpus-wide, ablation density {direction} as a layer's silence rises "
            f"(Spearman rho = {rho:+.3f}, exact one-sided p = {pval:.4g}). "
            f"{len(zero_dims)} of {len(ablatable)} ablatable dimensions have no published ablation "
            "in either harvest - an absence of evidence about the literature, not evidence those "
            "components do not matter."
        ),
    }
    return rows, stats


def _detail_probs(detail: list[dict], corrected: bool, min_arms: int = 0) -> tuple[list[float], int]:
    """Per-block chance probabilities and own-arm wins, from `blocks_detail` in blocks_summary.json."""
    key = "chance" if corrected else "chance_uncorrected"
    kept = [b for b in detail if int(b["n_arms"]) >= min_arms]
    return [float(b[key]) for b in kept], sum(1 for b in kept if b["own_first"])


def own_arm_test(summary: dict) -> tuple[list[dict], dict]:
    """The own-arm-ranks-first share against its chance baseline, corrected two ways.

    The baseline is `1 / max(n_arms - n_ablation_arms, 1)`: a block's arms include the reporting
    paper's own switched-off configurations, and those are not independently chosen rival
    comparators, so counting them inflates the test. The superseded `1 / n_arms` version is
    recomputed here too and reported under `uncorrected`, so the correction is auditable. The exact
    Poisson-binomial tail also assumes independent blocks, which 75 blocks from 37 papers are not;
    the paper-clustered Monte-Carlo p and the one-block-per-paper exact p computed by
    `scripts/analyse_blocks.py` are carried through beside it.
    """
    block = summary["own_arm_ranks_first"]
    by_arms = block["by_arms"]
    detail = block.get("blocks_detail") or []
    rows: list[dict] = []
    probs: list[float] = []
    probs_unc: list[float] = []
    for arms in sorted(by_arms, key=int):
        v = by_arms[arms]
        chance = v.get("chance_share", 1.0 / int(arms))
        chance_unc = v.get("chance_share_uncorrected", 1.0 / int(arms))
        rows.append({
            "arms": int(arms),
            "blocks": v["blocks"],
            "own_first": v["own_first"],
            "share_first": round(v["share_first"], 4),
            "chance_share": round(chance, 4),
            "chance_share_uncorrected": round(chance_unc, 4),
            "ablation_arms": v.get("ablation_arms", 0),
            "excess": round(v["share_first"] - chance, 4),
            "excess_uncorrected": round(v["share_first"] - chance_unc, 4),
        })
        probs.extend([chance] * v["blocks"])
        probs_unc.extend([chance_unc] * v["blocks"])

    observed = block["own_first"]
    # `blocks_detail` gives the exact per-block probabilities; the by_arms means are only a fallback
    # for a summary written before the correction, and they average away within-size variation.
    if detail:
        probs, observed = _detail_probs(detail, corrected=True)
        probs_unc, _ = _detail_probs(detail, corrected=False)
    expected, pval = poisson_binomial_tail(probs, observed)
    exp_unc, p_unc = poisson_binomial_tail(probs_unc, observed)

    big = [r for r in rows if r["arms"] >= 5]
    big_blocks = sum(r["blocks"] for r in big)
    big_obs = sum(r["own_first"] for r in big)
    big_probs = [p for r in big for p in [r["chance_share"]] * r["blocks"]]
    big_probs_unc = [p for r in big for p in [r["chance_share_uncorrected"]] * r["blocks"]]
    if detail:
        big_probs, big_obs = _detail_probs(detail, corrected=True, min_arms=5)
        big_probs_unc, _ = _detail_probs(detail, corrected=False, min_arms=5)
        big_blocks = len(big_probs)
    big_exp, big_p = poisson_binomial_tail(big_probs, big_obs) if big_probs else (0.0, 1.0)
    big_exp_unc, big_p_unc = (poisson_binomial_tail(big_probs_unc, big_obs) if big_probs_unc
                              else (0.0, 1.0))

    two = next((r for r in rows if r["arms"] == 2), None)

    stats = {
        "blocks": block["blocks_with_own_arm"],
        "own_first": observed,
        "share_first": round(block["share_first"], 4),
        "chance_baseline": block.get("chance_baseline", "1 / max(n_arms - n_ablation_arms, 1)"),
        "ablation_arms": block.get("n_ablation_arms"),
        "expected_by_chance": round(expected, 2),
        "exact_poisson_binomial_p": pval,
        "paper_clustered": block.get("paper_clustered"),
        "one_block_per_paper": block.get("one_block_per_paper"),
        "mean_own_rank": round(block["mean_own_rank"], 3),
        "mean_own_z": round(block["mean_own_z"], 4),
        "five_plus_arms": {
            "blocks": big_blocks,
            "own_first": big_obs,
            "share": round(big_obs / big_blocks, 4) if big_blocks else None,
            "expected_by_chance": round(big_exp, 2),
            "exact_poisson_binomial_p": big_p,
        },
        "two_arms_only": None if two is None else {
            "blocks": two["blocks"],
            "own_first": two["own_first"],
            "share": two["share_first"],
            "chance": two["chance_share"],
            "above_chance": two["share_first"] > two["chance_share"],
        },
        "uncorrected": {
            "chance_baseline": "1 / n_arms (counts the paper's own ablation arms as rivals)",
            "expected_by_chance": round(exp_unc, 2),
            "exact_poisson_binomial_p": p_unc,
            "five_plus_arms": {
                "expected_by_chance": round(big_exp_unc, 2),
                "exact_poisson_binomial_p": big_p_unc,
            },
            "why_superseded": (
                "An ablation arm is the reporting paper's own system with a component switched off, "
                "not a comparator chosen from the field; a full system beating its own ablation is "
                "the premise of the ablation analysis, so 1/n_arms understates the chance share."
            ),
        },
        "reading": (
            "Once the chance baseline stops counting the paper's own ablation arms as rivals, the "
            "OVERALL own-arm advantage does not survive, and it survives the paper clustering even "
            "less. What survives is the subgroup of tables with five or more arms. The reading is "
            "that a large arm table in this literature is largely the paper's own ablation table - a "
            "finding about what these tables are, not a second independent measurement of selective "
            "comparator choice."
        ),
    }
    return rows, stats


# --------------------------------------------------------------------------- io


def shortpath(path: Path) -> str:
    """Repo-relative when it can be, absolute otherwise - an out-dir outside the repo is legal."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    log.info("wrote %s (%d rows)", shortpath(path), len(rows))


def main_corpus(a: argparse.Namespace) -> int:
    """`--corpus`: statistic 1 over the coded-set + corpus-wide union, written with `_corpus`."""
    contrasts_path = a.contrasts if a.contrasts is not None else CONTRASTS_CORPUS
    key_to_layer = load_layers(a.dimensions)
    contrast_rows = load_corpus_contrasts(contrasts_path)
    unknown = {r["dimension"] for r in contrast_rows} - set(key_to_layer)
    if unknown:
        raise SystemExit(f"contrasts name dimensions absent from the schema: {sorted(unknown)}")
    nr_by_layer = load_layer_silence_from_summary(a.layer_summary)
    if not nr_by_layer:
        nr_by_layer = load_nr_by_layer(a.nr_by_dimension, key_to_layer)
    rows, stats = corpus_coverage(key_to_layer, contrast_rows, nr_by_layer)
    stats["source"] = Path(shortpath(contrasts_path)).as_posix()
    write_csv(a.out_dir / f"ablation_coverage_by_layer{CORPUS_SUFFIX}.csv", rows)
    dest = a.out_dir / f"ablation_coverage_summary{CORPUS_SUFFIX}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"coverage_by_layer": stats}, indent=2) + "\n", encoding="utf-8")
    log.info("wrote %s", shortpath(dest))

    print(f"corpus-wide: {stats['total_contrasts']} contrasts from {stats['total_papers']} papers "
          f"{stats['contrasts_by_provenance']}")
    for r in rows:
        print(f"  {r['layer']}  silence {r['not_reported_pct']:5.1f}%  dims {r['dimensions']}  "
              f"ablated {r['dimensions_ablated']}  contrasts {r['contrasts']:4d} "
              f"(coded {r['contrasts_coded_harvest']})  per dim {r['contrasts_per_dimension']}")
    print(f"Spearman rho = {stats['spearman_rho']}  exact p = "
          f"{stats['exact_permutation_p_one_sided']}")
    print(f"zero-contrast layers {stats['zero_contrast_layers']}; "
          f"{stats['n_dimensions_without_contrast']} of {stats['n_ablatable_dimensions']} ablatable "
          f"dimensions without a contrast: {stats['dimensions_without_contrast']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dimensions", type=Path, default=DIMENSIONS)
    p.add_argument("--contrasts", type=Path, default=None,
                   help=f"default {CONTRASTS.name}; {CONTRASTS_CORPUS.name} with --corpus")
    p.add_argument("--corpus", action="store_true",
                   help="layer coverage over the coded-set + corpus-wide union; writes "
                        "*_corpus outputs and leaves the default ones untouched")
    p.add_argument("--blocks-summary", type=Path, default=BLOCKS_SUMMARY)
    p.add_argument("--nr-by-dimension", type=Path, default=NR_BY_DIM)
    p.add_argument("--layer-summary", type=Path, default=LAYER_SUMMARY,
                   help="one-screen summary whose layer rows give the weighted silence share")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--log-level", default="INFO")
    a = p.parse_args(argv)
    logging.basicConfig(level=a.log_level, format="%(levelname)s %(message)s")

    if a.corpus:
        return main_corpus(a)
    contrasts_path = a.contrasts if a.contrasts is not None else CONTRASTS

    key_to_layer = load_layers(a.dimensions)
    counts = Counter(
        r["dimension"] for r in csv.DictReader(contrasts_path.open(encoding="utf-8"))
    )
    unknown = set(counts) - set(key_to_layer)
    if unknown:
        raise SystemExit(f"contrasts name dimensions absent from the schema: {sorted(unknown)}")
    nr_by_layer = load_layer_silence_from_summary(a.layer_summary)
    if not nr_by_layer:
        nr_by_layer = load_nr_by_layer(a.nr_by_dimension, key_to_layer)

    rows, cov_stats = coverage_by_layer(key_to_layer, counts, nr_by_layer)
    write_csv(a.out_dir / "ablation_coverage_by_layer.csv", rows)

    out = {"coverage_by_layer": cov_stats}
    if a.blocks_summary.exists():
        summary = json.loads(a.blocks_summary.read_text(encoding="utf-8"))
        arm_rows, arm_stats = own_arm_test(summary)
        write_csv(a.out_dir / "blocks_own_arm_test.csv", arm_rows)
        out["own_arm_test"] = arm_stats
    else:
        log.warning("%s absent; skipping the own-arm test", a.blocks_summary)

    dest = a.out_dir / "ablation_coverage_summary.json"
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    log.info("wrote %s", shortpath(dest))

    print(f"layers correlated: {len(cov_stats['layers_in_correlation'])} "
          f"(excluded {cov_stats['excluded_layers']})")
    print(f"Spearman rho = {cov_stats['spearman_rho']}  exact p = "
          f"{cov_stats['exact_permutation_p_one_sided']}")
    print(f"zero-ablation layers {cov_stats['zero_contrast_layers']} "
          f"covering {cov_stats['n_zero_contrast_dimensions']} dimensions")
    if "own_arm_test" in out:
        o = out["own_arm_test"]
        print(f"own arm first {o['own_first']}/{o['blocks']} vs {o['expected_by_chance']} expected "
              f"({o['chance_baseline']}), exact p = {o['exact_poisson_binomial_p']:.3e}")
        pc = o.get("paper_clustered") or {}
        if pc.get("p") is not None:
            print(f"  paper-clustered Monte Carlo p = {pc['p']:.4g} "
                  f"({pc.get('draws')} draws, seed {pc.get('seed')})")
        obp = o.get("one_block_per_paper") or {}
        if obp:
            print(f"  one block per paper: {obp['own_first']}/{obp['blocks']} vs "
                  f"{obp['expected_by_chance']} expected, exact p = "
                  f"{obp['exact_poisson_binomial_p']:.4g}")
        f = o["five_plus_arms"]
        print(f"  5+ arms: {f['own_first']}/{f['blocks']} vs {f['expected_by_chance']} expected, "
              f"exact p = {f['exact_poisson_binomial_p']:.3e}   <- the one result that survives")
        u = o["uncorrected"]
        print(f"  uncorrected (1/n_arms, superseded): {u['expected_by_chance']} expected, exact p = "
              f"{u['exact_poisson_binomial_p']:.3e}; 5+ arms "
              f"{u['five_plus_arms']['expected_by_chance']} expected, exact p = "
              f"{u['five_plus_arms']['exact_poisson_binomial_p']:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
