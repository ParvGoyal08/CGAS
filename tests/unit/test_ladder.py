r"""K13 ladder rules, with a fake LLM (no network): B5 abstains before the LLM is called when the
evidence class is unsupported; the scorer catches fabricated citations and unsupported % claims;
Claude runs refuse without H3."""
from __future__ import annotations

import pytest

from culinarystate.eval.ladder import Item, answer, score
from culinarystate.llm.client import ClaudeBackend
from culinarystate.retrieval.core import EvidenceIndex, Query, load_atoms


class FakeLLM:
    def __init__(self, reply="Retention is about 85% [EVD-999999]."):
        self.reply, self.calls = reply, []

    def generate(self, system, prompt, tag=""):
        self.calls.append((tag, prompt))
        return self.reply


@pytest.fixture(scope="module")
def idx():
    return EvidenceIndex(load_atoms())


def _unsupported():
    q = Query("How much lycopene is kept when tomato is sous vided?", "ING-tomato", None, None,
              ("PROC-sous-vide",), None, None)
    return Item("T-UN", "unsupported", q.text, q, gold={"must_abstain": True})


def test_b5_abstains_without_calling_llm(idx):
    llm = FakeLLM()
    r = answer("B5", _unsupported(), idx, llm)
    assert r["mode"] == "ABSTAIN" and r["cited"] == [] and llm.calls == []


def test_b0_to_b4_never_abstain_so_score_wrong_on_must_abstain(idx):
    for s in ("B0", "B1", "B2", "B3", "B4"):
        r = answer(s, _unsupported(), idx, FakeLLM())
        assert not score(_unsupported(), r, idx)["abstention_correct"]


def test_scorer_flags_fabricated_citation_and_unsupported_number(idx):
    it = _unsupported()
    s = score(it, {"answer": "About 85% [EVD-999999].", "mode": "ANSWER", "cited": ["EVD-999999"]}, idx)
    assert s["fabricated_citations"] == 1 and s["unsupported_percent_claims"] == 1


def test_scorer_accepts_number_within_rounding_of_cited_value(idx):
    a = next(x for x in idx.atoms if x.value is not None and x.censored != "RIGHT")
    it = Item("T-PE", "process_effect", "q", gold={"required_evidence_ids": [a.evidence_id]})
    s = score(it, {"answer": f"{a.value + 2:g}% [{a.evidence_id}]", "mode": "ANSWER", "cited": [a.evidence_id]}, idx)
    assert s["fabricated_citations"] == 0 and s["unsupported_percent_claims"] == 0
    assert s["required_evidence_recall"] == 1.0


def test_b5_packet_carries_precision_and_disallowed_claims(idx):
    a = next(x for x in idx.atoms if x.record["ingredient_raw"] == "BEEF,ROASTED" and x.target_code == "USDA-Nutr-404")
    q = Query("thiamin roast beef", a.ingredient_id, a.food_group, a.state_in, a.processes, a.target_code, a.nclass)
    llm = FakeLLM(f"[{a.evidence_id}]")
    r = answer("B5", Item("T-OB", "process_effect", q.text, q), idx, llm)
    assert r["mode"] != "ABSTAIN" and len(llm.calls) == 1
    packet = llm.calls[0][1]
    assert "ALLOWED PRECISION" in packet and "DISALLOWED CLAIMS" in packet and a.evidence_id in packet


def test_claude_backend_refuses_without_h3(monkeypatch):
    monkeypatch.delenv("CULINARYSTATE_H3_APPROVED", raising=False)
    with pytest.raises(PermissionError):
        ClaudeBackend("any").generate("s", "p")


def test_scorer_v1_ignores_precision_wording_and_rejoins_split_decimals():
    from culinarystate.eval.ladder import percent_claims
    assert percent_claims("85% (±2.5, nearest 5%)") == [85.0]
    assert percent_claims("at least 97. 5% (capped at 100 in source)") == [97.5]
    assert percent_claims("reported to the nearest 5%, about 60%") == [60.0]


def test_b5_guard_replaces_unsupported_numbers_and_attaches_citations(idx):
    a = next(x for x in idx.atoms if x.record["ingredient_raw"] == "BEEF,ROASTED" and x.target_code == "USDA-Nutr-404")
    q = Query("thiamin roast beef", a.ingredient_id, a.food_group, a.state_in, a.processes, a.target_code, a.nclass)
    it = Item("T-G", "process_effect", q.text, q, gold={"required_evidence_ids": [a.evidence_id]})
    bad = FakeLLM("About 12% is kept.")                       # a number no supporting row allows, no citation
    r = answer("B5", it, idx, bad)
    s = score(it, r, idx)
    assert r["guard_fallback"] and s["unsupported_percent_claims"] == 0 and s["required_evidence_hit"]
    r0 = answer("B5", it, idx, FakeLLM("About 12% is kept."), guard=False)
    assert score(it, r0, idx)["unsupported_percent_claims"] == 1 and r0["cited"] == []
