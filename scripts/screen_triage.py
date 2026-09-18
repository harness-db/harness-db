#!/usr/bin/env python
"""Title/abstract triage: two model votes (+ a decisive third) -> tiers -> the smallest possible human queue.

Implements protocol Amendment 3 (docs/protocol_prisma_p.md, Amendments table, 2026-09-17):
every record gets two independent model votes; the single human screener decides conflicts,
unresolved 'unsure' records, and a random verification sample of model-agreed decisions.
Records the two-vote triage would send to the human as `unsure` or `conflict` get a decisive
third model vote (`scripts/screen_llm.py --mode tiebreak`, include/exclude only, with a
confidence) and are re-tiered as T5; the human keeps only the three-way splits, the
low-confidence contradictions and a verification sample.

Inputs (read only):
    data/raw/candidates.csv                 one row per candidate (id, title, abstract, year, ...)
    data/screening/llm_votes.csv            first vote per record (Opus 5, Sonnet 5 fallback)
    data/screening/llm_votes_second.csv     second vote per record (Sonnet 5), still being written
    data/screening/llm_votes_tiebreak.csv   third vote (Opus 5 tiebreak) for the unsure/conflict records

Outputs:
    data/screening/triage.csv               one row per candidate with tier, rule, auto decision
    data/screening/triage_report.md         counts, workload, model-model kappa
    data/screening/human_queue.json         needs_human=1 rows for screening/screen.html
    data/screening/human_queue.js           same content as `window.HUMAN_QUEUE` (file:// safe)

Tiers (applied in order; the first that fires wins):
    T0  hard rule, no model needed (date, bare model name on a leaderboard, non-English, no title)
    T1  both models exclude                     -> exclude; verification sample (amendment 3, 200 excludes in total)
    T2  both models include                     -> full text; verification sample (amendment 3, 200 includes in total)
    T3  include vs exclude                      -> human (conflict)
    T4  at least one unsure                     -> rule R4 (see `apply_r4`); rest to the human
    T5  a tiebreak vote exists                  -> rule T5 (see `apply_t5`): the tiebreak decides unless
                                                   the three votes split three ways or a low-confidence
                                                   tiebreak contradicts a definite prior vote; 3 %
                                                   verification sample of the automatic decisions
    pending  second vote not yet available      -> re-run when coverage grows

T5 is checked before T1-T4: a record with a tiebreak vote is one that T3/T4 had sent to the
human, so the tiebreak rule replaces that outcome.

Re-runnable: verification samples are chosen by a per-record hash of (seed, record_id), so a
record's sample membership never changes when the script is re-run on more coverage, and human
decisions already made stay attached to the right records.

Usage:
    python scripts/screen_triage.py [--candidates ...] [--votes1 ...] [--votes2 ...] [--votes3 ...] [--out-dir ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from kappa import cohen_kappa

SEED = 20260917
TIEBREAK_SEED = 20260916      # separate hash stream for the T5 verification sample
# Verification sample sized to protocol amendment 3 (n = 400, stratified 200 / 200): rates are the
# stratum target divided by the size of the automatically decided pool at full coverage
# (17,817 automatic excludes, 9,114 automatic includes; T1/T2/T4/T5 pooled, T0 hard rules excluded).
VERIFY_TARGET_PER_STRATUM = 200
VERIFY_EXCLUDE_RATE = VERIFY_TARGET_PER_STRATUM / 17817   # every automatic exclude (T1, R4a, T5)
VERIFY_INCLUDE_RATE = VERIFY_TARGET_PER_STRATUM / 9114    # every automatic include (T2, R4b, T5)
TIERS = ["T0", "T1", "T2", "T3", "T4", "T5", "pending"]
WINDOW_START_YEAR = 2022     # criterion (c): first public release 2022-10-01 .. 2026-08-31
WINDOW_START_YYMM = "2210"   # arXiv id month prefix of the window start
WINDOW_END_YEAR = 2026
ASCII_LETTER_FRACTION = 0.6
ABSTRACT_CHARS = 1500

OUT_COLUMNS = [
    "record_id", "title", "year", "source", "url",
    "vote_1", "model_1", "reason_1", "step_1", "vote_2", "model_2", "reason_2", "step_2",
    "vote_3", "model_3", "reason_3", "confidence_3",
    "tier", "tier_rule", "auto_decision", "needs_human", "human_sample_type",
]

# --- T0: bare model names on leaderboards -------------------------------------------------
# A leaderboard row whose title is just a model (vendor's model name + version) and carries no
# agent vocabulary is a model entry, not a harness entry (protocol section 3: "not the model").
MODEL_FAMILY = (
    r"(gpt|chatgpt|claude|gemini|llama|qwen|o1|o3|o4|mistral|mixtral|grok|deepseek|"
    r"amazon nova|nova|minicpm|xai|palm|phi)"
)
BARE_MODEL_RE = re.compile(
    r"^\s*" + MODEL_FAMILY + r"([-_ .]?[a-z0-9.]+)*"        # family + version/variant tokens
    r"(\s*\([^)]*\))?\s*$",                                 # optional "(Vendor)"
    re.IGNORECASE,
)
AGENT_VOCAB_RE = re.compile(
    r"agent|harness|scaffold|tool|swe|cua|operator|pilot|assistant|coder|dev\b|use\b|"
    r"mentor|bench|search|browser|computer|research|orchestr|workflow|framework|\+",
    re.IGNORECASE,
)

# --- T4 rule R4: negative and hedge signals in model reasons -------------------------------
# Negative signals are the step 1-3 exclusions of the decision procedure (section 3): the record
# is a survey / benchmark-only / dataset / position paper (step 1: no named system that runs a
# model), or it has no loop (step 2) or no executed actions (step 3).
NEG_PATTERNS: dict[str, re.Pattern[str]] = {
    "survey": re.compile(
        r"\bsurvey\b|\bsystematic (literature )?review\b|\bliterature review\b|\bscoping review\b|"
        r"\breview (of|paper|article)\b|\boverview of\b|\btaxonomy of\b|\btutorial\b|"
        r"\bmapping study\b|\bbibliometric", re.IGNORECASE),
    "benchmark_only": re.compile(
        r"\bbenchmark|\btestbed\b|\bevaluation (suite|instrument|study|protocol)\b|"
        r"\bevaluat\w* (existing|off-the-shelf|commercial)\b", re.IGNORECASE),
    "dataset": re.compile(
        r"\bdataset\b|\bcorpus\b|\bdata collection\b|\bannotation (scheme|framework)\b",
        re.IGNORECASE),
    "position_paper": re.compile(
        r"\bposition paper\b|\bperspective\b|\bvision paper\b|\bopinion\b|\bessay\b|\broadmap\b|"
        r"\bcommentary\b|\beditorial\b", re.IGNORECASE),
    "no_loop": re.compile(
        r"\bno loop\b|\bwithout a loop\b|\bsingle[- ](call|turn|shot|step|pass|prompt|query|inference)\b|"
        r"\bone[- ]shot\b|\bnon-iterative\b|\bnot iterative\b|\bno (environment|external|tool) feedback\b|"
        r"\bno feedback loop\b", re.IGNORECASE),
    "no_actions": re.compile(
        r"\bno (tool|action|executed|execution|external)\b|\bno operation executed\b|\bnot executed\b|"
        r"\bdoes not execute\b|\bonly (produces|generates|outputs) text\b|\btext[- ]only\b|"
        r"\bno environment\b|\bprompting (method|technique|strategy|approach)\b|\bprompt engineering\b|"
        r"\bchain[- ]of[- ]thought\b", re.IGNORECASE),
}
# A hedge means the model itself saw a possible in-scope system or lacked information; any hedge
# in either reason blocks the rule exclusion and sends the record to the human.
HEDGE_RE = re.compile(
    r"\breference\b|\bbaseline (agent|harness|system)\b|\bship|\bdefault agent\b|"
    r"\bmay\b|\bmight\b|\bpossibl|\bcould\b|\bperhaps\b|\blikely\b|\bseems?\b|\bappears?\b|"
    r"\bunclear\b|\bnot clear\b|\bundeterm|\bcannot\b|\bcan't\b|\binsufficient\b|\bno abstract\b|"
    r"\bneeds? (the )?full[- ]text\b|\bcheck(ed)? at full[- ]text\b|\brequires? full[- ]text\b|"
    r"\bfull[- ]text (needed|required|check)\b|\bdecid\w* at full[- ]text\b|"
    r"\btitle[- ]only\b|\bfrom (the )?title\b|\bunless\b|\bif (it|the|this)\b|\bwhether\b",
    re.IGNORECASE,
)
# Phrases such as "sent to full text" / "route to step 10" are the models restating the prompt's
# instruction for surveys and are not treated as hedges.
STEPS_1_3 = {"1", "2", "3"}


# "evaluated on benchmark X" describes a system's evaluation, not a benchmark paper.
BENCHMARK_CONTEXT_RE = re.compile(r"\b(evaluated|tested|assessed|validated|scores?|results?) (in|on|against|across)\b", re.IGNORECASE)


def neg_signals(reason: str) -> list[str]:
    reason = reason or ""
    out = []
    for name, pat in NEG_PATTERNS.items():
        if not pat.search(reason):
            continue
        if name == "benchmark_only" and BENCHMARK_CONTEXT_RE.search(reason):
            continue
        out.append(name)
    return out


def has_hedge(reason: str) -> bool:
    return bool(HEDGE_RE.search(reason or ""))


def ascii_letter_fraction(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 1.0
    return sum(ch.isascii() for ch in letters) / len(letters)


def sample_hash(record_id: str, seed: int = SEED) -> float:
    """Deterministic uniform number in [0, 1) for one record; stable across re-runs."""
    h = hashlib.sha1(f"{seed}:{record_id}".encode()).hexdigest()
    return int(h[:12], 16) / float(16 ** 12)


def arxiv_yymm(arxiv_id: str) -> str | None:
    m = re.match(r"^(\d{2})(\d{2})\.\d{4,5}", (arxiv_id or "").strip())
    if not m or not (1 <= int(m.group(2)) <= 12):
        return None
    return m.group(1) + m.group(2)


# --- tier logic ----------------------------------------------------------------------------

def t0_rule(row: pd.Series) -> str | None:
    """Return the T0 rule name that fires, or None."""
    title = (row.get("title") or "").strip()
    if not title:
        return "empty_title"
    year = (row.get("year") or "").strip()
    if year.isdigit():
        y = int(year)
        if y < WINDOW_START_YEAR:
            return "date_year_before_window"
        if y > WINDOW_END_YEAR:
            return "date_year_after_window"
    yymm = arxiv_yymm(row.get("arxiv_id") or "")
    if yymm is not None and yymm < WINDOW_START_YYMM:
        return "date_arxiv_before_window"
    # Upper bound is not applied from the paper date: a paper posted after 2026-08-31 can still
    # describe a system first released inside the window (criterion c is about the system).
    if (row.get("source") or "") == "leaderboard" and BARE_MODEL_RE.match(title) and not AGENT_VOCAB_RE.search(title):
        return "leaderboard_bare_model_name"
    text = title + " " + (row.get("abstract") or "")
    if ascii_letter_fraction(text) < ASCII_LETTER_FRACTION:
        return "non_english_text"
    return None


T0_DECISIONS = {
    "empty_title": "exclude",
    "date_year_before_window": "exclude",
    "date_year_after_window": "exclude",
    "date_arxiv_before_window": "exclude",
    "leaderboard_bare_model_name": "exclude",
    "non_english_text": "exclude",
}


def apply_r4(v1: str, s1: str, r1: str, v2: str, s2: str, r2: str, source: str = "") -> tuple[str, str]:
    """Rule R4 for pairs with at least one 'unsure' and no include/exclude conflict.

    Returns (auto_decision, rule) where auto_decision is 'exclude', 'include' or '' (human).

    R4a exclude-lean: BOTH votes carry a step 1-3 negative signal and NEITHER reason hedges.
        A vote carries a negative signal when it is `exclude` with decision_step in {1,2,3}, or
        `unsure` with decision_step in {1,2,3} and its reason matches one of NEG_PATTERNS
        (survey, benchmark_only, dataset, position_paper, no_loop, no_actions).
    R4b include-lean: one vote is `include` (the model names a system with a loop; decision_step
        'none') and the other is `unsure` whose reason has NO negative signal. The record goes to
        full text, where the human decides.
    Everything else (unsure+unsure without two clean negatives, exclude at step 8 + unsure,
        include + unsure-with-negative-signal, any hedge, any leaderboard record) is left to
        the human.
    """
    if source == "leaderboard":
        # A leaderboard row is a pseudo-record for a system with no paper (protocol 4.3); the
        # models' "leaderboard entry, no harness detail" is lack of information, not a negative.
        return "", "R4_human_leaderboard_record"
    votes = [(v1, s1, r1 or ""), (v2, s2, r2 or "")]
    if any(has_hedge(r) for _, _, r in votes):
        return "", "R4_human_hedge"

    def negative(v: str, s: str, r: str) -> bool:
        if v == "exclude":
            return s in STEPS_1_3
        if v == "unsure":
            return s in STEPS_1_3 and bool(neg_signals(r))
        return False

    if all(negative(*x) for x in votes):
        tags = {t for v, _, r in votes if v == "unsure" for t in neg_signals(r)}
        if "exclude" in (v1, v2):
            tags.add("exclude_vote")
        return "exclude", "R4a_both_negative:" + "+".join(sorted(tags))
    inc = [x for x in votes if x[0] == "include"]
    uns = [x for x in votes if x[0] == "unsure"]
    if len(inc) == 1 and len(uns) == 1 and inc[0][1] == "none" and not neg_signals(uns[0][2]):
        return "include", "R4b_include_plus_unsure_no_negative"
    return "", "R4_human_unresolved"


def apply_t5(v1: str, v2: str, v3: str, conf3: str) -> tuple[str, str]:
    """Rule T5 for records with a tiebreak vote (v3 in {include, exclude}, conf3 in {high, medium, low}).

    Returns (auto_decision, rule) where auto_decision is 'include', 'exclude' or '' (human).

    A prior vote *supports* the tiebreak when it equals v3 and *opposes* it when it is the other
    definite vote (`unsure` neither supports nor opposes). The human gets the record iff
      (a) three-way split: a definite prior vote opposes the tiebreak and none supports it
          (include / exclude / unsure with no two agreeing), or
      (b) low-confidence contradiction: the tiebreak is low-confidence and a definite prior vote
          opposes it (even though the other prior vote supports it).
    Otherwise the tiebreak decides: `T5_majority_<v3>` when a prior vote supports it (two of
    three agree), `T5_tiebreak_<v3>` when both priors were unsure. The rule string carries the
    confidence after a colon for the report.
    """
    priors = (v1, v2)
    supported = v3 in priors
    opposed = any(v in ("include", "exclude") and v != v3 for v in priors)
    if opposed and not supported:
        return "", f"T5_human_three_way_split:{conf3}"
    if opposed and conf3 == "low":
        return "", f"T5_human_low_confidence_contradiction:{conf3}"
    return v3, f"T5_{'majority' if supported else 'tiebreak'}_{v3}:{conf3}"


def assign_tiers(cands: pd.DataFrame, votes1: pd.DataFrame, votes2: pd.DataFrame, votes3: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per candidate with tier, tier_rule, auto_decision, needs_human, human_sample_type."""
    cands = cands.fillna("").astype(str)
    v1 = votes1.fillna("").astype(str).drop_duplicates("record_id", keep="last")
    v2 = votes2.fillna("").astype(str).drop_duplicates("record_id", keep="last")
    v1 = v1.rename(columns={"vote": "vote_1", "model": "model_1", "reason": "reason_1", "decision_step": "step_1"})
    v2 = v2.rename(columns={"vote": "vote_2", "model": "model_2", "reason": "reason_2", "decision_step": "step_2"})
    if votes3 is None or votes3.empty:
        votes3 = pd.DataFrame(columns=["record_id", "vote", "model", "reason", "confidence"])
    v3 = votes3.fillna("").astype(str).drop_duplicates("record_id", keep="last")
    v3 = v3.rename(columns={"vote": "vote_3", "model": "model_3", "reason": "reason_3", "confidence": "confidence_3"})
    df = cands.rename(columns={"id": "record_id"}).merge(
        v1[["record_id", "vote_1", "model_1", "reason_1", "step_1"]], on="record_id", how="left"
    ).merge(v2[["record_id", "vote_2", "model_2", "reason_2", "step_2"]], on="record_id", how="left"
    ).merge(v3[["record_id", "vote_3", "model_3", "reason_3", "confidence_3"]], on="record_id", how="left").fillna("")

    tiers, rules, autos, needs, samples = [], [], [], [], []
    for row in df.itertuples(index=False):
        r = row._asdict()
        tier = rule = auto = sample = ""
        need = 0
        t0 = t0_rule(pd.Series(r))
        v1_, v2_ = r["vote_1"], r["vote_2"]
        same_model = bool(r["model_1"]) and r["model_1"] == r["model_2"]
        if t0:
            tier, rule, auto = "T0", t0, T0_DECISIONS[t0]
        elif not v1_ or not v2_ or same_model:
            tier, rule = "pending", ("same_model_second_vote" if same_model else "second_vote_missing" if v1_ else "first_vote_missing")
        elif r["vote_3"] in ("include", "exclude"):
            tier = "T5"
            auto, rule = apply_t5(v1_, v2_, r["vote_3"], r["confidence_3"])
            if auto and sample_hash(r["record_id"], TIEBREAK_SEED) < (VERIFY_EXCLUDE_RATE if auto == "exclude" else VERIFY_INCLUDE_RATE):
                need, sample = 1, f"verify_{auto}"
            elif not auto:
                need, sample = 1, "tiebreak"
        elif v1_ == "exclude" and v2_ == "exclude":
            tier, rule, auto = "T1", "both_exclude", "exclude"
            if sample_hash(r["record_id"]) < VERIFY_EXCLUDE_RATE:
                need, sample = 1, "verify_exclude"
        elif v1_ == "include" and v2_ == "include":
            tier, rule, auto = "T2", "both_include", "include"
            if sample_hash(r["record_id"]) < VERIFY_INCLUDE_RATE:
                need, sample = 1, "verify_include"
        elif {v1_, v2_} == {"include", "exclude"}:
            tier, rule, need, sample = "T3", "include_vs_exclude", 1, "conflict"
        else:
            tier = "T4"
            auto, rule = apply_r4(v1_, r["step_1"], r["reason_1"], v2_, r["step_2"], r["reason_2"], r.get("source", ""))
            if auto == "exclude" and sample_hash(r["record_id"]) < VERIFY_EXCLUDE_RATE:
                need, sample = 1, "verify_exclude"
            elif auto == "include" and sample_hash(r["record_id"]) < VERIFY_INCLUDE_RATE:
                need, sample = 1, "verify_include"
            elif not auto:
                need, sample = 1, "unsure"
        tiers.append(tier); rules.append(rule); autos.append(auto); needs.append(need); samples.append(sample)
    df["tier"], df["tier_rule"], df["auto_decision"], df["needs_human"], df["human_sample_type"] = tiers, rules, autos, needs, samples
    return df


# --- kappa ---------------------------------------------------------------------------------

def binarise(v: str) -> str:
    return "exclude" if v == "exclude" else "forward"


def model_kappa(df: pd.DataFrame) -> dict:
    ov = df[(df.vote_1 != "") & (df.vote_2 != "") & (df.model_1 != df.model_2)]
    k3, po3, n = cohen_kappa(ov.vote_1.tolist(), ov.vote_2.tolist())
    k2, po2, _ = cohen_kappa(ov.vote_1.map(binarise).tolist(), ov.vote_2.map(binarise).tolist())
    xt = pd.crosstab(ov.vote_1, ov.vote_2) if n else pd.DataFrame()
    return {"n_overlap": int(n), "kappa_3class": k3, "agreement_3class": po3, "kappa_binary": k2, "agreement_binary": po2,
            "crosstab": xt}


# --- report ---------------------------------------------------------------------------------

def build_report(df: pd.DataFrame, kap: dict, n_second_pass_target: int | None) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    n = len(df)
    L = ["# Title/abstract triage report", "", f"Generated {now} by `scripts/screen_triage.py` (seed {SEED}).", "",
         (f"Candidates: {n:,}. First votes present: {(df.vote_1 != '').sum():,}. Second votes present: {(df.vote_2 != '').sum():,} "
          f"(second-vote coverage among non-T0 records: {((df.vote_2 != '') & (df.tier != 'T0')).sum():,} of {(df.tier != 'T0').sum():,}). "
          f"Tiebreak votes present: {(df.vote_3 != '').sum():,}."), ""]
    L += ["## Tiers", "", "| tier | rule | n | auto_decision | to human |", "|---|---|---:|---|---:|"]
    for tier in TIERS:
        sub = df[df.tier == tier]
        if sub.empty:
            L.append(f"| {tier} | - | 0 | | 0 |")
            continue
        rule_key = sub.tier_rule.str.replace(r":.*$", "", regex=True)
        for rule, g in sub.groupby(rule_key, sort=False):
            autos = ",".join(sorted(x for x in g.auto_decision.unique() if x)) or "-"
            L.append(f"| {tier} | {rule} | {len(g):,} | {autos} | {int(g.needs_human.sum()):,} |")
        L.append(f"| **{tier} total** | | **{len(sub):,}** | | **{int(sub.needs_human.sum()):,}** |")
    L += ["", "Rule definitions:", "",
          "- T0 `empty_title`: no title. `date_year_before_window`: year < 2022 (the window starts 2022-10-01; year-only dates cannot resolve the month, so 2022 is kept). `date_year_after_window`: year > 2026. `date_arxiv_before_window`: validated arXiv id YYMM < 2210. No upper date bound from the paper date: a paper posted after 2026-08-31 may describe a system first released inside the window (criterion c is about the system). `leaderboard_bare_model_name`: source = leaderboard and the title is a bare model name (family + version, optional vendor in parentheses) with no agent vocabulary. `non_english_text`: fraction of ASCII letters in title+abstract < 0.6.",
          f"- T1 `both_exclude`: both models vote exclude -> exclude; verification sample = records with hash(seed, record_id) < {VERIFY_EXCLUDE_RATE:.0%}.",
          f"- T2 `both_include`: both models vote include -> forwarded to full text; verification sample = hash < {VERIFY_INCLUDE_RATE:.0%}.",
          "- T3 `include_vs_exclude`: the human decides (sample type `conflict`).",
          "- T4 (at least one unsure, no include/exclude conflict), rule R4 applied to the two reasons and decision steps:",
          "    - `R4_human_leaderboard_record`: source = leaderboard (a pseudo-record for a system without a paper, protocol 4.3): human.",
          "    - `R4_human_hedge`: any reason contains a hedge (reference, ship, default agent, may, might, could, likely, unclear, cannot, insufficient, no abstract, needs full text, title only, whether, ...): human.",
          f"    - `R4a_both_negative`: both votes carry a step 1-3 negative signal (an `exclude` at step 1-3, or an `unsure` at step 1-3 whose reason matches survey / benchmark_only / dataset / position_paper / no_loop / no_actions) and no hedge -> exclude; a {VERIFY_EXCLUDE_RATE:.0%} verification sample goes to the human.",
          f"    - `R4b_include_plus_unsure_no_negative`: one `include` (decision_step none) + one `unsure` whose reason has no negative signal -> forwarded to full text; a {VERIFY_INCLUDE_RATE:.0%} verification sample goes to the human.",
          "    - `R4_human_unresolved`: everything else (unsure+unsure without two clean negatives, exclude at step 8 + unsure, include + unsure with a negative signal): human.",
          ("- T5 (a tiebreak vote exists; checked before T1-T4): the records T3/T4 had sent to the human as `conflict` / `unsure` got a decisive third vote (`scripts/screen_llm.py --mode tiebreak`, prompt ta-v2-tiebreak-2026-09-17, include/exclude only, with a confidence high/medium/low). A prior vote supports the tiebreak when it is the same vote and opposes it when it is the other definite vote; `unsure` does neither. The human gets the record iff no two of the three votes agree on include or exclude (`T5_human_three_way_split`: include / exclude / unsure), or the tiebreak is low-confidence and contradicts a definite prior vote (`T5_human_low_confidence_contradiction`); sample type `tiebreak`. Otherwise the tiebreak decides: `T5_majority_include` / `T5_majority_exclude` (a prior vote agrees with it) or `T5_tiebreak_include` / `T5_tiebreak_exclude` (both priors were unsure); "
          f"a verification sample of the automatic decisions (same per-stratum rates as T1/T2: {VERIFY_EXCLUDE_RATE:.2%} of excludes, {VERIFY_INCLUDE_RATE:.2%} of includes) (hash(seed {TIEBREAK_SEED}, record_id)) goes to the human as `verify_include` / `verify_exclude`."),
          "- `pending`: the second vote is not available yet (or came from the same model as the first); re-run after the second pass advances.",
          ""]
    # human workload
    hq = df[df.needs_human == 1]
    L += ["## Human workload (current coverage)", "", "| sample_type | n |", "|---|---:|"]
    for st, cnt in hq.human_sample_type.value_counts().items():
        L.append(f"| {st} | {cnt:,} |")
    L.append(f"| **total** | **{len(hq):,}** |")
    L += ["", f"At 15 s per title/abstract decision: {len(hq) * 15 / 3600:.1f} h; at 30 s: {len(hq) * 30 / 3600:.1f} h.", ""]
    # projection
    two = df[df.tier.isin(["T1", "T2", "T3", "T4", "T5"])]
    if len(two):
        rate_h = two.needs_human.mean()
        rate_ft = (two.auto_decision == "include").mean()
        n_pending = int((df.tier == "pending").sum())
        n_second_target = n_second_pass_target if n_second_pass_target is not None else n_pending + len(two)
        remaining_second = max(n_second_target - len(two), 0)
        beyond = max(n_pending - remaining_second, 0)
        proj_h_second = round(rate_h * remaining_second)
        proj_h_all = round(rate_h * n_pending)
        L += ["## Projection at full coverage", "",
              (f"Per-record rates on the {len(two):,} two-vote records: human title decision {rate_h:.1%}, auto-forward to full text {rate_ft:.1%}, "
               f"auto-exclude {(two.auto_decision == 'exclude').mean():.1%}."), "",
              (f"- Pending records now: {n_pending:,}. The running second pass targets {n_second_target:,} records "
               f"({remaining_second:,} still to come); {beyond:,} records (first vote by the fallback model) need a further Opus pass to get two different-model votes."),
              (f"- Projected human title decisions: {len(hq):,} now + {proj_h_second:,} when the second pass completes = **{len(hq) + proj_h_second:,}**; "
               f"+ {proj_h_all - proj_h_second:,} more if every pending record gets a second vote = {len(hq) + proj_h_all:,} "
               f"(~{(len(hq) + proj_h_all) * 20 / 3600:.0f} h at 20 s each)."),
              f"- Projected records forwarded to full text: {int((df.auto_decision == 'include').sum()):,} now + ~{round(rate_ft * n_pending):,} from pending records + whatever the human forwards.",
              ""]
    # kappa
    L += ["## Model-model agreement on the overlap", "",
          f"n = {kap['n_overlap']:,} records with two different-model votes.", "",
          f"- 3-class (include / exclude / unsure): kappa = {kap['kappa_3class']:.3f}, observed agreement = {kap['agreement_3class']:.3f}",
          f"- binarised (exclude vs forward = include or unsure): kappa = {kap['kappa_binary']:.3f}, observed agreement = {kap['agreement_binary']:.3f}", ""]
    if len(kap["crosstab"]):
        xt = kap["crosstab"]
        L += ["| vote_1 \\ vote_2 | " + " | ".join(xt.columns) + " |", "|---|" + "---:|" * len(xt.columns)]
        for idx, r in xt.iterrows():
            L.append(f"| {idx} | " + " | ".join(f"{int(x):,}" for x in r.values) + " |")
        L.append("")
    # T0 listing for eyeballing
    t0 = df[df.tier == "T0"]
    L += ["## T0 records (all listed so the human can eyeball the hard rules)", "", "| rule | record_id | title | year | source |", "|---|---|---|---|---|"]
    for r in t0.itertuples(index=False):
        L.append(f"| {r.tier_rule} | {r.record_id} | {str(r.title)[:80].replace('|', '/')} | {r.year} | {r.source} |")
    L.append("")
    # T5 confidence breakdown
    t5 = df[df.tier == "T5"]
    if len(t5):
        L += ["## T5 tiebreak: rule x confidence", "", "| rule | high | medium | low | total | to human |", "|---|---:|---:|---:|---:|---:|"]
        rule_key = t5.tier_rule.str.replace(r":.*$", "", regex=True)
        for rule, g in t5.groupby(rule_key, sort=False):
            c = g.confidence_3.value_counts()
            L.append(f"| {rule} | {int(c.get('high', 0)):,} | {int(c.get('medium', 0)):,} | {int(c.get('low', 0)):,} | {len(g):,} | {int(g.needs_human.sum()):,} |")
        L += ["", "Tiebreak vote vs prior votes: " + ", ".join(f"{k[0]}/{k[1]} -> {k[2]}: {n:,}" for k, n in t5.groupby(['vote_1', 'vote_2', 'vote_3']).size().items()), ""]
    # R4 / T5 samples for auditing
    audits = (("R4a", "R4a rule excludes (random 25 for audit)", 25), ("R4b", "R4b rule includes (random 15 for audit)", 15),
              ("T5_majority_exclude", "T5 majority excludes (random 15 for audit)", 15), ("T5_tiebreak_exclude", "T5 tiebreak excludes, both priors unsure (random 15 for audit)", 15),
              ("T5_majority_include", "T5 majority includes (random 10 for audit)", 10), ("T5_tiebreak_include", "T5 tiebreak includes, both priors unsure (random 10 for audit)", 10))
    for rule_prefix, label, k in audits:
        sub = df[df.tier_rule.str.startswith(rule_prefix)]
        if sub.empty:
            continue
        L += [f"## {label}", "", "| record_id | title | vote_1 / reason | vote_2 / reason | vote_3 / reason |", "|---|---|---|---|---|"]
        for r in sub.sample(min(len(sub), k), random_state=SEED).itertuples(index=False):
            v3 = f"{r.vote_3} ({r.confidence_3}): {str(r.reason_3)[:110].replace('|', '/')}" if r.vote_3 else "-"
            L.append(f"| {r.record_id} | {str(r.title)[:70].replace('|', '/')} | {r.vote_1}: {str(r.reason_1)[:110].replace('|', '/')} | {r.vote_2}: {str(r.reason_2)[:110].replace('|', '/')} | {v3} |")
        L.append("")
    return "\n".join(L)


def write_queue(df: pd.DataFrame, cands: pd.DataFrame, json_path: Path, js_path: Path) -> int:
    abstracts = cands.set_index("id")["abstract"].fillna("").astype(str)
    hq = df[df.needs_human == 1]
    records = []
    for r in hq.itertuples(index=False):
        records.append({
            "record_id": r.record_id, "title": r.title, "abstract": abstracts.get(r.record_id, "")[:ABSTRACT_CHARS],
            "year": r.year, "source": r.source, "url": r.url, "tier": r.tier, "tier_rule": r.tier_rule,
            "sample_type": r.human_sample_type,
            "vote_1": r.vote_1, "model_1": r.model_1, "reason_1": r.reason_1,
            "vote_2": r.vote_2, "model_2": r.model_2, "reason_2": r.reason_2,
            "vote_3": r.vote_3, "model_3": r.model_3, "reason_3": r.reason_3, "confidence_3": r.confidence_3,
        })
    payload = {"generated_at": datetime.now(UTC).isoformat(timespec="seconds"), "seed": SEED, "n": len(records),
               "sample_types": {k: int(v) for k, v in hq.human_sample_type.value_counts().items()}, "records": records}
    text = json.dumps(payload, ensure_ascii=False, indent=0)
    json_path.write_text(text, encoding="utf-8")
    js_path.write_text("window.HUMAN_QUEUE = " + text + ";\n", encoding="utf-8")
    return len(records)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidates", default=str(REPO / "data/raw/candidates.csv"))
    p.add_argument("--votes1", default=str(REPO / "data/screening/llm_votes.csv"))
    p.add_argument("--votes2", default=str(REPO / "data/screening/llm_votes_second.csv"))
    p.add_argument("--votes3", default=str(REPO / "data/screening/llm_votes_tiebreak.csv"), help="tiebreak votes (screen_llm.py --mode tiebreak); optional")
    p.add_argument("--second-pass-list", default=str(REPO / "data/screening/candidates_second_pass.csv"), help="records targeted by the running second pass (for the projection)")
    p.add_argument("--out-dir", default=str(REPO / "data/screening"))
    args = p.parse_args(argv)

    cands = pd.read_csv(args.candidates, dtype=str, keep_default_na=False)
    v1 = pd.read_csv(args.votes1, dtype=str, keep_default_na=False)
    v2 = pd.read_csv(args.votes2, dtype=str, keep_default_na=False) if Path(args.votes2).exists() else pd.DataFrame(columns=v1.columns)
    v3 = pd.read_csv(args.votes3, dtype=str, keep_default_na=False) if Path(args.votes3).exists() else None
    target = None
    if Path(args.second_pass_list).exists():
        target = len(pd.read_csv(args.second_pass_list, dtype=str, keep_default_na=False, usecols=["id"]))

    df = assign_tiers(cands, v1, v2, v3)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df[OUT_COLUMNS].to_csv(out_dir / "triage.csv", index=False, encoding="utf-8", lineterminator="\n")
    kap = model_kappa(df)
    (out_dir / "triage_report.md").write_text(build_report(df, kap, target), encoding="utf-8")
    nq = write_queue(df, cands, out_dir / "human_queue.json", out_dir / "human_queue.js")

    print(f"candidates {len(df):,}; tiers: " + ", ".join(f"{t}={int((df.tier == t).sum()):,}" for t in TIERS))
    print(f"human queue {nq:,}: " + ", ".join(f"{k}={v}" for k, v in df[df.needs_human == 1].human_sample_type.value_counts().items()))
    print(f"model-model kappa on n={kap['n_overlap']:,}: 3-class {kap['kappa_3class']:.3f}, binary {kap['kappa_binary']:.3f}")
    print(f"wrote {out_dir / 'triage.csv'}, {out_dir / 'triage_report.md'}, {out_dir / 'human_queue.json'}, {out_dir / 'human_queue.js'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
