"""Tests for the automated full-text screening: condenser, output schema, registry, validation matching.

No network and no LLM calls.
"""
import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fulltext_screen as fs
import system_registry as sr
import validate_screening as vs

# ---------------------------------------------------------------- helpers


def filler(n_words: int, word: str = "lorem") -> str:
    return " ".join([word] * n_words)


def long_paper(n_sections: int = 12, per_section: int = 1200) -> str:
    parts = ["Abstract", "We propose AgentX, a framework whose agent runs in a loop. " + filler(150)]
    parts += ["1 Introduction", filler(1400, "intro")]
    for k in range(2, n_sections + 2):
        parts.append(f"{k} Section Number {k}")
        parts.append(filler(per_section // 2, f"plain{k}"))  # no signal terms
        parts.append(f"In section {k} the agent calls a tool and observes the environment. " + filler(80, f"sig{k}"))
    parts += ["References", "[1] Some agent paper with tools and loops. " + filler(40, "ref")]
    parts += ["A Prompt Templates", "The system prompt of the agent sets max steps to 30 and the sandbox is a docker container. " + filler(30, "app")]
    return "\n\n".join(parts)


# ---------------------------------------------------------------- full-text file parsing


def test_safe_id_and_header_parse(tmp_path):
    assert fs.safe_id("arxiv:2405.15793") == "arxiv__2405.15793"
    assert fs.safe_id("github:SWE-agent/SWE-agent") == "github__SWE-agent__SWE-agent"
    raw = ("record_id: arxiv:1\nsource_used: arxiv_pdf\nfetched_url: https://arxiv.org/pdf/1\n"
           "fetched_title: A: B\nfetched_at: 2026-09-18T00:00:00Z\n\nBody text here.\n")
    header, text = fs.parse_fulltext(raw)
    assert header == {"record_id": "arxiv:1", "source_used": "arxiv_pdf", "fetched_url": "https://arxiv.org/pdf/1",
                      "fetched_title": "A: B", "fetched_at": "2026-09-18T00:00:00Z"}
    assert text.strip() == "Body text here."


# ---------------------------------------------------------------- condenser


def test_condense_respects_cap_and_keeps_headings():
    doc = long_paper()
    ex = fs.condense(doc, title="AgentX: a test", cap_words=3000)
    assert not ex.whole
    assert ex.words <= 3000
    assert ex.fulltext_words > 3000
    heads = ex.text.split("[Section headings]", 1)[1].split("[High-signal paragraphs", 1)[0]
    for k in range(2, 14):
        assert f"{k} Section Number {k}" in heads  # every heading kept even when its section is cut
    assert "1 Introduction" in heads and "References" in heads


def test_condense_opening_signal_order_and_references_skipped():
    doc = long_paper()
    ex = fs.condense(doc, title="AgentX", cap_words=3000)
    t = ex.text
    assert t.startswith("[Title as fetched] AgentX")
    assert t.index("[Opening") < t.index("[Section headings]") < t.index("[High-signal paragraphs")
    assert "We propose AgentX" in t.split("[Section headings]")[0]  # abstract in the opening
    body = t.split("[High-signal paragraphs", 1)[1]
    # signal paragraphs, no plain paragraphs, in document order
    assert "plain3" not in body
    positions = [body.index(f"In section {k} ") for k in range(2, 14) if f"In section {k} " in body]
    assert positions == sorted(positions) and len(positions) >= 5
    assert "[1] Some agent paper" not in t  # references skipped
    assert "max steps to 30" in body  # appendix after references is back in scope


def test_condense_ranks_dense_paragraphs_when_space_is_short():
    parts = ["Abstract", filler(1600, "intro")]
    parts += [f"The agent step {k}. " + filler(100, f"weak{k}") for k in range(30)]  # 2 terms each
    parts += ["The agent runs a loop with tools in a docker sandbox, retries failed tests, and stops at max steps. " + filler(50, "dense")]
    ex = fs.condense("\n\n".join(parts), cap_words=2300)
    assert "dense dense" in ex.text  # the densest late paragraph beats earlier weak ones
    assert ex.words <= 2300


def test_condense_short_document_is_sent_whole():
    doc = "Abstract\n\nWe introduce TinyAgent, which loops over tools.\n\n2 Method\n\nIt runs bash in a container."
    ex = fs.condense(doc, title="TinyAgent")
    assert ex.whole and "[Full text, complete]" in ex.text
    assert ex.text.index("We introduce TinyAgent") < ex.text.index("It runs bash")


def test_long_paragraph_is_split():
    ps = fs._split_long(". ".join([f"Sentence number {i} has words" for i in range(200)]) + ".")
    assert len(ps) > 1 and all(len(p.split()) <= 2 * fs.CHUNK_WORDS for p in ps)


def test_readme_moved_first_and_tree_capped():
    bundle = ("# owner/repo\nref: v1.0\n\n### docs/guide.md\nGuide about the agent loop and tools.\n\n"
              "## README (README.md)\nRepoAgent runs an agent loop with tools.\n")
    out = fs.readme_first(bundle)
    assert out.index("RepoAgent runs") < out.index("Guide about")
    already = "# owner/repo\n\n## README (README.md)\nFirst.\n\n### docs/a.md\nSecond."
    assert fs.readme_first(already) == already
    tree = "\n".join(f"src/agent/tools/tool_{i}.py" for i in range(2000))
    doc = "## README (README.md)\n" + filler(2000, "readme") + " agent loop tools\n\n## File tree (first 2000 of 2000 paths)\n" + tree
    ex = fs.condense(doc, cap_words=3000, repo_bundle=True)
    assert ex.text.count("src/agent/tools/tool_") <= fs.TREE_MAX_WORDS


def test_heading_detection():
    assert fs.is_heading("3.2 Tool interface design")
    assert fs.is_heading("## Installation")
    assert fs.is_heading("A.1 Prompt Templates")
    assert fs.is_heading("INTRODUCTION")
    assert not fs.is_heading("A model that can only emit text becomes a system")
    assert not fs.is_heading("We run the agent for 30 steps and then stop the loop because the budget is spent.")


# ---------------------------------------------------------------- output schema


def fake_vote(**over):
    v = {
        "record_id": "arxiv:1", "document_title_seen": "AgentX: a harness", "decision": "include", "exclusion_code": None,
        "exclusion_subreason": None, "deciding_step": 12,
        "step_evidence": [{"step": s, "verdict": "pass", "quote": "the agent calls a tool"} for s in (1, 2, 3, 7, 12)],
        "system_name": "AgentX", "system_version": None, "repo_url": "https://github.com/o/agentx", "release_date": "2025-03",
        "codable_dimensions": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "E1", "F1", "G1", "H1", "M1", "M2", "M3", "M4"],
        "codable_count": 19, "layers_covered": ["A", "B", "C", "D", "E", "F", "G", "H"], "systems_mentioned": ["SWE-agent"],
        "confidence": "high",
    }
    v.update(over)
    return v


def test_schema_accepts_valid_and_rejects_invalid():
    schema = fs.batch_schema()
    jsonschema.validate({"votes": [fake_vote()]}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"votes": [fake_vote(decision="maybe")]}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"votes": [fake_vote(codable_dimensions=["Z9"])]}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"votes": [fake_vote(deciding_step=13)]}, schema)
    bad = fake_vote()
    del bad["confidence"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"votes": [bad]}, schema)
    json.dumps(schema)  # serialisable for --json-schema


def test_check_vote_flags():
    item_schema = fs.record_schema()
    dims = fs.dimension_ids()
    excerpt = "Intro. The agent calls a tool and reads the result."
    chk = fs.check_vote(fake_vote(), excerpt, dims, item_schema)
    assert chk["flags"] == [] and chk["rule_pass"] and chk["quotes_verbatim"] == chk["quotes_total"] == 5
    low = fake_vote(codable_dimensions=["A1", "B1", "M1"], codable_count=19,
                    step_evidence=[{"step": 12, "verdict": "pass", "quote": "not in the text at all"}])
    chk = fs.check_vote(low, excerpt, dims, item_schema)
    assert {"count_mismatch", "include_fails_codability_rule", "quote_not_in_excerpt"} <= set(chk["flags"])
    ex = fake_vote(decision="exclude", exclusion_code=None, deciding_step=7)
    assert "exclude_without_code" in fs.check_vote(ex, excerpt, dims, item_schema)["flags"]


def test_protocol_prompt_has_all_twelve_steps():
    b = fs.protocol_blocks()
    for k in range(1, 13):
        assert f"Step {k}." in b["steps"]
    sp = fs.system_prompt(b)
    assert "19 of 38" in sp and "H4 Guardrails" in sp and "goto_10" in sp


def test_pass2_selection_takes_all_includes_and_a_tenth_of_excludes():
    rows = [{"record_id": f"r{i}", "decision": "include" if i < 20 else "exclude",
             "exclusion_code": "" if i < 20 else ("not_retrievable" if i % 7 == 0 else "out_of_scope")} for i in range(2020)]
    sel = set(fs.pass2_selection(rows))
    assert {f"r{i}" for i in range(20)} <= sel
    ex_sel = [r for r in rows[20:] if r["record_id"] in sel]
    assert all(r["exclusion_code"] != "not_retrievable" for r in ex_sel)
    assert 0.06 < len(ex_sel) / sum(r["exclusion_code"] != "not_retrievable" for r in rows[20:]) < 0.14
    assert sel == set(fs.pass2_selection(rows))  # deterministic


# ---------------------------------------------------------------- registry


def rec(rid, name, repo="", version="", title="", cc=20, release=""):
    return {"record_id": rid, "system_name": name, "repo_url": repo, "system_version": version, "document_title_seen": title or name,
            "codable_count_computed": cc, "release_date": release}


def test_registry_merges_by_repo_and_name():
    recs = [
        rec("arxiv:2405.15793", "SWE-agent", "https://github.com/SWE-agent/SWE-agent"),
        rec("github:SWE-agent/SWE-agent", "swe agent", "https://github.com/swe-agent/swe-agent.git", cc=25),
        rec("arxiv:2407.16741", "OpenHands", "https://github.com/All-Hands-AI/OpenHands"),
        rec("s2:x", "OpenHands (CodeAct agent)"),
        rec("arxiv:2501.00001", "Totally Different Agent"),
    ]
    rows = sr.group_records(recs)
    by = {r["system_id"]: r for r in rows}
    assert set(by) == {"swe-agent", "openhands", "totally-different-agent"}
    assert by["swe-agent"]["n_members"] == 2 and by["swe-agent"]["max_codable_count"] == 25
    assert by["openhands"]["n_members"] == 2


def test_registry_monorepo_subpaths_stay_apart():
    recs = [rec("l:1", "OS-Symphony", "https://github.com/xlang-ai/OSWorld/tree/main/mm_agents/os_symphony"),
            rec("l:2", "UiPath Screen Agent", "https://github.com/xlang-ai/OSWorld/tree/main/mm_agents/uipath"),
            rec("l:3", "OSWorld reference agent", "https://github.com/xlang-ai/OSWorld")]
    assert len(sr.group_records(recs)) == 3


def test_registry_fuzzy_threshold():
    assert sr.names_match("MetaGPT", "Meta-GPT")
    assert sr.names_match("AutoCodeRover", "AutoCodeRovers")
    assert not sr.names_match("CodeAgent", "CodeActAgent")
    assert not sr.names_match("Pi", "Pix")  # short names must match exactly


def test_registry_version_rule():
    assert sr.split_version("Agent S2") == ("agent s", 2)
    assert sr.split_version("Mobile-Agent-v2") == ("mobile-agent", 2)
    assert sr.split_version("OpenHands") == ("openhands", None)
    # major version in the name AND stated by the document -> its own row
    recs = [rec("arxiv:2410.08164", "Agent S", "https://github.com/simular-ai/Agent-S"),
            rec("arxiv:2504.00906", "Agent S2", "https://github.com/simular-ai/Agent-S", title="Agent S2: A Compositional Generalist-Specialist Framework")]
    ids = {r["system_id"] for r in sr.group_records(recs)}
    assert ids == {"agent-s", "agent-s-v2"}
    # version only in a stray name, not stated by the document -> one row
    recs = [rec("a:1", "AutoGen"), rec("a:2", "AutoGen 2", title="Evaluating multi-agent chat")]
    assert [r["system_id"] for r in sr.group_records(recs)] == ["autogen"]
    # minor / 0.x / 1.x versions never split
    recs = [rec("a:1", "OpenHands"), rec("a:2", "OpenHands 1.0", version="1.0", title="OpenHands 1.0")]
    assert len(sr.group_records(recs)) == 1


def test_registry_canonical_is_first_source_repo_on_tie():
    cands = {"arxiv:2405.15793": {"arxiv_id": "2405.15793"}, "github:o/r": {"source": "github", "year": "2024", "url": "https://github.com/o/r"},
             "arxiv:2501.00002": {"arxiv_id": "2501.00002"}}
    recs = [rec("arxiv:2501.00002", "RepoAgent", "https://github.com/o/r"), rec("arxiv:2405.15793", "RepoAgent", "https://github.com/o/r"),
            rec("github:o/r", "RepoAgent", "https://github.com/o/r", release="2024-05")]
    row = sr.group_records(recs, cands)[0]
    assert row["canonical_record_id"] == "github:o/r"  # same month as the paper: the repository wins


def test_combine_pass_agreement():
    p1 = [{"record_id": "a", "decision": "include", "exclusion_code": "", "exclusion_subreason": "", "deciding_step": "12", "system_name": "A"},
          {"record_id": "b", "decision": "include", "exclusion_code": "", "exclusion_subreason": "", "deciding_step": "12", "system_name": "B"},
          {"record_id": "c", "decision": "exclude", "exclusion_code": "out_of_scope", "exclusion_subreason": "no_loop", "deciding_step": "2", "system_name": ""}]
    p2 = [dict(p1[0]), {**p1[1], "decision": "exclude", "exclusion_code": "no_harness_description", "deciding_step": "7"}]
    reg, final = sr.combine(p1, p2)
    fd = {r["record_id"]: r["final_decision"] for r in final}
    assert fd == {"a": "include", "b": "disputed", "c": "exclude"}
    assert [r["record_id"] for r in reg] == ["a"]


# ---------------------------------------------------------------- validation matching


def ref(**over):
    base = {"ref_id": "swe-agent", "set": "positive", "expected": "include", "name": "SWE-agent", "aliases": ["SWE agent"],
            "arxiv": "2405.15793", "urls": ["https://github.com/SWE-agent/SWE-agent"], "source": "", "note": ""}
    base.update(over)
    r = vs.Ref(**base)
    r.repos = {sr.repo_key(u) for u in r.urls}
    r.url_keys = {vs.url_key(u) for u in r.urls}
    r.name_keys = [sr.key_of(n) for n in r.names]
    return r


def test_validation_matches_candidates():
    r = ref()
    f = vs.cand_features
    assert vs.match_candidate(r, f("s2:1", {"arxiv_id": "2405.15793v2", "title": "Something else"})) == "arxiv"
    assert vs.match_candidate(r, f("github:x", {"url": "https://github.com/swe-agent/swe-agent", "title": "x/y"})) == "repo"
    assert vs.match_candidate(r, f("arxiv:9", {"title": "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering"})) == "name"
    assert vs.match_candidate(r, f("leaderboard:x", {"title": "SWE-agent Multimodal"})) == ""
    cline = ref(name="Cline", aliases=[], arxiv="", urls=[])
    assert vs.match_candidate(cline, f("arxiv:1", {"title": "Understanding eGFR Trajectories and Kidney Function Decline"})) == ""
    assert vs.match_candidate(cline, f("grey:cline", {"title": "Cline"})) == "name"


def test_validation_matches_votes_and_mentions():
    r = ref()
    row = {"record_id": "arxiv:2501.1", "system_name": "SWE agent", "repo_url": "", "systems_mentioned": "[]", "document_title_seen": ""}
    assert vs.match_vote(r, row, {}) == "name"
    row = {"record_id": "arxiv:2501.1", "system_name": "X", "repo_url": "https://github.com/SWE-agent/SWE-agent/tree/main", "systems_mentioned": "[]"}
    assert vs.match_vote(r, row, {}) == "repo"
    row = {"record_id": "arxiv:2501.1", "system_name": "X", "repo_url": "", "systems_mentioned": json.dumps(["OpenHands", "SWE-Agent"])}
    assert vs.match_vote(r, row, {}) == "" and vs.mentioned(r, row)
    neg = ref(ref_id="swe-bench", set="negative", name="SWE-bench", aliases=["SWE-bench: Can Language Models Resolve Real-World GitHub Issues?"],
              arxiv="2310.06770", urls=[])
    row = {"record_id": "s2:z", "system_name": "", "repo_url": "", "systems_mentioned": "[]",
           "document_title_seen": "SWE-bench: Can Language Models Resolve Real-World GitHub Issues"}
    assert vs.match_vote(neg, row, {}) == "title"


def test_wilson_interval():
    p, lo, hi = vs.wilson(9, 10)
    assert p == 0.9 and 0.55 < lo < 0.6 and 0.98 < hi <= 1.0
    k, po = vs.weighted_kappa([("include", "include"), ("exclude", "exclude")], [1, 10])
    assert k == 1.0 and po == 1.0


def test_reference_file_is_well_formed():
    refs = vs.load_refs()
    assert len({r.ref_id for r in refs}) == len(refs)
    pos = [r for r in refs if r.set == "positive"]
    neg = [r for r in refs if r.set == "negative"]
    assert len(neg) == 13 and len(pos) >= 20
    assert all(r.expected == "include" for r in pos) and all(r.expected == "exclude" for r in neg)
    for must in ("2210.03629", "2303.11366", "2402.01030", "2405.15793", "2407.16741", "2308.08155", "2308.00352", "2410.08164", "2402.07456"):
        assert any(r.arxiv == must for r in pos), must
