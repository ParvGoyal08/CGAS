r"""J2 validator rules (in-memory items; nothing written)."""
import json
import pathlib

from tools.benchmark import stats, tier, validate

ROOT = pathlib.Path(__file__).resolve().parents[2]
EVD = json.loads((ROOT / "ledgers/evidence/evidence_v0.jsonl").read_text().splitlines()[0])["evidence_id"]


def item(**kw):
    base = dict(item_id="BM-T-1", task_type="process_effect", question="How much folate survives when I boil lentils for ages?",
                gold_mode="ANSWER", gold_answer="x", evidence_regime="observed", must_abstain=False, difficulty="easy",
                author="Parv", reviewer="Kush", required_evidence_ids=[EVD], _file="t#0")
    base.update(kw)
    return base


def test_valid_item_passes():
    assert validate([item()]) == []


def test_rules_fire():
    errs = "\n".join(validate([
        item(item_id="A", reviewer="Parv"),
        item(item_id="B", required_evidence_ids=["EVD-999999"]),
        item(item_id="C", task_type="abstain", must_abstain=True, gold_mode="ANSWER", required_evidence_ids=[]),
        item(item_id="D", task_type="state", session={"recipe_id": "FIX-F01"}),
        item(item_id="E", question="Thiamin kept when beef is roasted?"),          # demo S06 copy
    ]))
    for frag in ("reviewer must differ", "unknown evidence ids", "need gold_mode ABSTAIN", "contamination", "duplicates demo:S06"):
        assert frag in errs, frag


def test_tiers():
    assert tier(103) == "below_minimum" and tier(104) == "minimum" and tier(320) == "target" and tier(440) == "stretch"
    assert stats([item()])["achieved_tier"] == "below_minimum"


def test_ai_draft_cannot_enter_authoring_without_promotion():
    errs = "\n".join(validate([item(item_id="AI1", origin="AI_DRAFT", status="UNVERIFIED")]))
    assert "AI_DRAFT item in authoring/ without promotion" in errs
    ok = validate([item(item_id="AI2", origin="AI_DRAFT", status="BENCHMARK_CANDIDATE", human_reviewer="Kush",
                        rewrite_note="tightened wording")])
    assert not any("AI_DRAFT" in e for e in ok)
