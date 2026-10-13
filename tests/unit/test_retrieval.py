r"""DEL-4 core rules: UNKNOWN is neutral, near needs the same process, abstain without evidence,
output precision never exceeds evidence precision."""
from __future__ import annotations

import pytest

from culinarystate.retrieval.core import (MATCH, MISMATCH, NEAR, UNKNOWN, EvidenceIndex, Query,
                                          compatibility, compatible, evidence_class, load_atoms,
                                          precision_policy)


@pytest.fixture(scope="module")
def idx():
    return EvidenceIndex(load_atoms())


def _atom(idx, raw, code):
    return next(a for a in idx.atoms if a.record["ingredient_raw"] == raw and a.target_code == code)


def test_unknown_is_never_a_mismatch(idx):
    a = _atom(idx, "BEEF,ROASTED", "USDA-Nutr-404")
    q = Query("thiamin roast beef", "ING-beef", None, None, ("PROC-roast",), "USDA-Nutr-404", None, time_min=45)
    v = compatibility(q, a, idx.fam)
    assert v["time"] == UNKNOWN and v["temperature"] == UNKNOWN      # R6 has no conditions
    assert compatible(v, strict=True)


def test_observed_for_exact_match_and_censored_wording(idx):
    a = _atom(idx, "BEEF,ROASTED", "USDA-Nutr-404")
    q = Query("thiamin roast beef", "ING-beef", a.food_group, None, ("PROC-roast",), "USDA-Nutr-404", a.nclass)
    hits = [(x, compatibility(q, x, idx.fam)) for x in idx.atoms if x.target_code == "USDA-Nutr-404"]
    cls, sup = evidence_class(q, hits)
    assert cls == "observed"
    text = precision_policy(cls, sup)
    assert "nearest 5%" in text or "at least" in text                 # precision ≤ evidence precision


def test_near_requires_the_same_process(idx):
    q = Query("vitamin c vegetables sous vide", "ING-vegetable-other", "USDA-FdGrp-11", None,
              ("PROC-sous-vide",), "USDA-Nutr-401", "water-soluble vitamin")
    hits = [(x, compatibility(q, x, idx.fam)) for x in idx.atoms if x.target_code == "USDA-Nutr-401"]
    assert any(v["process"] == NEAR for _, v in hits)                # family-level similarity exists…
    cls, _ = evidence_class(q, hits)
    assert cls == "unsupported"                                      # …but is not enough to answer


def test_unsupported_target_abstains(idx):
    q = Query("anthocyanins in steamed broccoli", "ING-broccoli", None, None, ("PROC-steam",), None, None)
    ranked = idx.search(q, k=10)
    hits = [(idx.atoms[i], compatibility(q, idx.atoms[i], idx.fam)) for i, _ in ranked]
    cls, _ = evidence_class(q, hits)
    assert cls == "unsupported"


def test_mismatch_excludes_evidence(idx):
    a = _atom(idx, "BEEF,ROASTED", "USDA-Nutr-404")
    q = Query("x", "ING-pork", None, None, ("PROC-roast",), "USDA-Nutr-404", None)
    v = compatibility(q, a, idx.fam)
    assert v["food"] == MISMATCH and not compatible(v, strict=False)
    assert v["process"] == MATCH and v["target"] == MATCH


def test_interpolated_brackets_and_never_extrapolates(idx):
    from culinarystate.retrieval.core import interpolation
    milk = [a for a in idx.atoms if a.ingredient_id == "ING-milk" and a.target_code == "USDA-Nutr-404"
            and "PROC-heat" in a.processes]
    times = sorted({a.conditions["t"]["value"] for a in milk if "t" in a.conditions and a.conditions["t"]["status"] == "MEASURED"})
    assert len(times) >= 2
    mid = (times[0] + times[1]) / 2
    q = Query("thiamin milk heated", "ING-milk", milk[0].food_group, None, ("PROC-heat",), "USDA-Nutr-404",
              milk[0].nclass, time_min=mid)
    hits = [(a, compatibility(q, a, idx.fam)) for a in milk]
    cls, sup = evidence_class(q, hits)
    assert cls == "interpolated" and sup[0]["lower_at"] == times[0] and sup[0]["upper_at"] == times[1]
    assert "range, not a point" in precision_policy(cls, sup)
    q_out = Query("x", "ING-milk", milk[0].food_group, None, ("PROC-heat",), "USDA-Nutr-404", milk[0].nclass,
                  time_min=times[-1] * 3)
    assert interpolation(q_out, [(a, compatibility(q_out, a, idx.fam)) for a in milk]) is None   # no extrapolation


def test_model_estimated_is_gated_off_until_a_model_is_promoted(idx):
    from culinarystate.retrieval import core
    q = Query("lycopene tomato sous vide", "ING-tomato", None, None, ("PROC-sous-vide",), None, None)
    est = lambda q: {"model_id": "MODEL-d7-fm", "lo": 60.0, "hi": 90.0}   # noqa: E731
    assert evidence_class(q, [], estimator=est)[0] == "unsupported"            # D7 not promoted (DEC-032)
    core.PROMOTED_MODELS["MODEL-d7-fm"] = "test only"
    try:
        cls, sup = evidence_class(q, [], estimator=est)
        assert cls == "model-estimated" and sup[0]["tier"] == "E6" and "not evidence" in precision_policy(cls, sup)
    finally:
        core.PROMOTED_MODELS.clear()
