"""The outside-contributor path: the system template, the --system gate, and COVERAGE_WANTED."""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import coverage_wanted as cw
from validate import check_evidence, validate_system_file

DIMS = json.loads((ROOT / "schema" / "dimensions.json").read_text(encoding="utf-8"))
TEMPLATE = ROOT / "contrib" / "TEMPLATE_system.json"
COMMIT = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"


def template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def filled(sid: str = "example-contrib-agent") -> dict:
    """The template filled the way a contributor would: two values, the rest silent."""
    s = template()
    s.update(id=sid, name="Example Contrib Agent", papers=["arxiv:2405.15793"],
             urls={"repo": "https://github.com/example/agent"})
    for cell in s["coding"].values():
        cell.update(value=None, not_reported=True, coder="gh:octocat",
                    note="no config surface in the pinned repository")
    s["coding"]["pinned_version"].update(
        value=f"v2.4.6 @ {COMMIT} (2026-07-23)", not_reported=False, confidence="high",
        evidence=f'"ref: tag:v2.4.6 {COMMIT}" (git tag v2.4.6@{COMMIT[:7]})', note="")
    s["coding"]["execution_isolation"].update(
        value="subprocess", not_reported=False, confidence="high", note="",
        evidence='"actions are executed as `subprocess.run`" (docs/faq.md:41@a83fcae)')
    return s


def write(tmp_path: Path, system: dict) -> Path:
    p = tmp_path / f"{system['id']}.json"
    p.write_text(json.dumps(system), encoding="utf-8")
    return p


def test_template_is_current_with_the_schema():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_contrib_template.py"),
                        "--check"], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stdout + r.stderr


def test_template_has_every_dimension_unfilled():
    coding = template()["coding"]
    assert list(coding) == [d["key"] for d in DIMS["dimensions"]]
    for key, cell in coding.items():
        assert cell["value"] is None and cell["not_reported"] is False, key
        assert cell["evidence"] == "", key


def test_gate_rejects_the_unfilled_template():
    errors, _ = validate_system_file(TEMPLATE)
    unfilled = [e for e in errors if "not filled" in e]
    assert len(unfilled) == len(DIMS["dimensions"])


def test_gate_accepts_a_filled_system(tmp_path):
    errors, warnings = validate_system_file(write(tmp_path, filled()))
    assert errors == []
    assert not [w for w in warnings if "commit" in w]


def test_gate_requires_quote_and_locator(tmp_path):
    s = filled()
    s["coding"]["execution_isolation"]["evidence"] = "runs actions with subprocess.run"
    errors, _ = validate_system_file(write(tmp_path, s))
    assert any("verbatim quote" in e for e in errors)


def test_gate_requires_a_pinned_commit_for_a_repository(tmp_path):
    s = filled()
    s["coding"]["pinned_version"].update(value=None, not_reported=True, evidence="")
    errors, _ = validate_system_file(write(tmp_path, s))
    assert any("pinned_version" in e and "commit" in e for e in errors)


def test_gate_rejects_value_outside_the_schema(tmp_path):
    s = filled()
    s["coding"]["execution_isolation"]["value"] = "chroot"
    errors, _ = validate_system_file(write(tmp_path, s))
    assert any(e.startswith("schema:") for e in errors)


def test_gate_unresolved_needs_a_note(tmp_path):
    s = filled()
    s["coding"]["rollback"].update(value=None, not_reported=False, unresolved=True, note="")
    errors, _ = validate_system_file(write(tmp_path, s))
    assert any("unresolved" in e for e in errors)


def test_check_evidence_locators():
    assert check_evidence('"x" (src/a.py:12@abc1234)', "abc1234def")[0] == []
    assert check_evidence('"x" (arXiv:2405.15793 Sec. 3)', None)[0] == []
    errs, warns = check_evidence('"x" (https://example.org/docs)', None)
    assert errs == [] and warns
    assert check_evidence('"x" (somewhere)', None)[0]
    _, warns = check_evidence('"x" (src/a.py:12@fffffff)', "abc1234def")
    assert any("not the pinned commit" in w for w in warns)


def test_gate_cli_exit_codes(tmp_path):
    script = str(ROOT / "scripts" / "validate.py")
    ok = subprocess.run([sys.executable, script, "--system", str(write(tmp_path, filled()))],
                        capture_output=True, text=True, check=False)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    bad = subprocess.run([sys.executable, script, "--system", str(TEMPLATE)],
                         capture_output=True, text=True, check=False)
    assert bad.returncode == 1 and "not filled" in bad.stdout


# --- coverage_wanted -------------------------------------------------------------------------

FRAME = [
    {"system_id": "a", "name": "A", "stars": "900", "stratum": "H", "coded": "1", "repo_url": "u"},
    {"system_id": "b", "name": "B", "stars": "400", "stratum": "P", "coded": "0", "repo_url": "u"},
    {"system_id": "c", "name": "C", "stars": "450", "stratum": "O", "coded": "0", "repo_url": ""},
    {"system_id": "d", "name": "D", "stars": "", "stratum": "O", "coded": "0", "repo_url": ""},
    {"system_id": "e", "name": "E", "stars": "999", "stratum": "O", "coded": "0", "repo_url": ""},
]


def _systems():
    dims = DIMS["dimensions"]
    silent = {d["key"]: {"value": None, "not_reported": True} for d in dims}
    a = {"id": "a", "name": "A", "coding": copy.deepcopy(silent)}
    e = {"id": "e", "name": "E", "coding": copy.deepcopy(silent)}
    e["coding"]["tracing"] = {"value": "logs", "not_reported": False, "evidence": '"x" (y@abc1234)'}
    e["coding"]["rollback"] = {"value": None, "not_reported": False, "unresolved": True}
    return [a, e]


def test_uncoded_by_stars_skips_coded_released_and_starless():
    rows = cw.uncoded_by_stars(FRAME, {"a", "e"}, top=10)
    assert [r["system_id"] for r in rows] == ["c", "b"]


def test_not_reported_rates_exclude_unresolved_from_the_base():
    rates = {r["key"]: r for r in cw.not_reported_rates(_systems(), DIMS["dimensions"])}
    assert rates["tracing"]["rate"] == 0.5
    assert rates["rollback"]["unresolved"] == 1 and rates["rollback"]["rate"] == 1.0


def test_outside_draw_lists_released_but_not_drawn():
    out = cw.outside_draw(_systems(), FRAME)
    assert [(r["id"], r["stratum"]) for r in out] == [("e", "O")]


def test_render_has_the_three_sections():
    text = cw.render(FRAME, _systems(), DIMS, {}, set(), top=5)
    for heading in ("## 1.", "## 2.", "## 3."):
        assert heading in text
    assert "field-weighted" not in text  # no analysis file given


def test_coverage_script_runs_on_repo_data(tmp_path):
    out = tmp_path / "COVERAGE_WANTED.md"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "coverage_wanted.py"),
                        "--out", str(out), "--top", "5"], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "| 5 |" in out.read_text(encoding="utf-8")
