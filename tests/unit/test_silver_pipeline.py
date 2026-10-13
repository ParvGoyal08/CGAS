import json

import pytest
import yaml

from culinarystate.silver.pipeline import (FixtureAdapter, StageGateError, check_stage, duplicate_families, run_stage,
                                           vocabulary_growth)


class EchoGoldLLM:
    """Test double: returns the fixture's own gold YAML (a perfect annotator) — exercises the plumbing only."""

    def __init__(self):
        self.docs = {r["recipe_id"]: r["_gold"] for r in FixtureAdapter().iter_recipes()}

    def generate(self, system, prompt, tag=""):
        rid = tag.split(":")[1]
        return "```yaml\n" + yaml.safe_dump(self.docs[rid]) + "```"


def test_stage_gates(tmp_path):
    check_stage(1000, tmp_path)
    with pytest.raises(StageGateError):
        check_stage(5000, tmp_path)                       # no audit of the 1k stage
    (tmp_path / "stage_1000.json").write_text(json.dumps({"decision": "REPAIR"}))
    with pytest.raises(StageGateError):
        check_stage(5000, tmp_path)                       # audit says REPAIR, not GO
    (tmp_path / "stage_1000.json").write_text(json.dumps({"decision": "GO"}))
    check_stage(5000, tmp_path)
    with pytest.raises(StageGateError):
        check_stage(60000, tmp_path)                      # beyond 10k refused


def test_real_stage_needs_h3(tmp_path):
    with pytest.raises(StageGateError):
        run_stage(1000, FixtureAdapter(), EchoGoldLLM(), approved_h3=False, out_dir=tmp_path)


def test_dry_run_plumbing(tmp_path):
    rep = run_stage(1000, FixtureAdapter(), EchoGoldLLM(), approved_h3=False, out_dir=tmp_path, dry_run_limit=5)
    assert rep["recipes"] == 5 and rep["validity_rate"] == 1.0 and rep["decision"] == "PENDING_HUMAN_AUDIT"


def test_duplicate_families_and_growth():
    rs = [{"recipe_id": "a", "steps": ["boil the potatoes in salted water for twenty minutes then drain"]},
          {"recipe_id": "b", "steps": ["boil the potatoes in salted water for twenty minutes then drain"]},
          {"recipe_id": "c", "steps": ["whisk the eggs"]}]
    fam = duplicate_families(rs)
    assert fam["b"] == "a" and fam["c"] == "c"
    g = vocabulary_growth([{"steps": [{"events": [{"op": "CREATE", "outputs": [{"id": "x", "concept": "egg"}]}]}]}])
    assert g == [(1, 1, 0)]
