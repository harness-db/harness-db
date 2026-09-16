import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from kappa import cohen_kappa  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "harness_db.schema.json").read_text(encoding="utf-8"))
DIMS = json.loads((ROOT / "schema" / "dimensions.json").read_text(encoding="utf-8"))


def example_system(**overrides):
    coding = {}
    for d in DIMS["dimensions"]:
        if d["type"] == "enum":
            v = [d["values"][0]] if d["multi"] else d["values"][0]
        elif d["type"] == "integer":
            v = 3
        elif d["type"] == "date":
            v = "2024-04-01"
        else:
            v = "v1.0.0"
        coding[d["key"]] = {"value": v, "evidence": "README.md:12@abc123", "confidence": "high",
                            "not_reported": False, "coder": "c1"}
    s = {"id": "example-agent", "name": "Example Agent", "papers": ["p1"], "coding": coding}
    s.update(overrides)
    return s


def errors_for(systems):
    return [e.message for e in Draft202012Validator(SCHEMA).iter_errors(systems)]


def test_schema_accepts_fully_coded_system():
    assert errors_for([example_system()]) == []


def test_schema_rejects_value_without_evidence():
    s = example_system()
    s["coding"]["edit_primitive"] = {"value": ["search_replace"], "not_reported": False}
    assert errors_for([s])


def test_schema_accepts_not_reported_without_evidence():
    s = example_system()
    s["coding"]["edit_primitive"] = {"value": None, "not_reported": True}
    assert errors_for([s]) == []


def test_schema_rejects_unknown_enum_value():
    s = example_system()
    s["coding"]["retry_policy"]["value"] = "sometimes"
    assert errors_for([s])


def test_schema_requires_every_dimension():
    s = example_system()
    del s["coding"]["tracing"]
    assert errors_for([s])


def test_kappa_perfect_and_chance():
    assert cohen_kappa(["a", "b", "a"], ["a", "b", "a"])[0] == 1.0
    k, po, n = cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])
    assert n == 4 and po == 0.5 and abs(k) < 1e-9


def test_validate_script_passes_on_repo_data():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
