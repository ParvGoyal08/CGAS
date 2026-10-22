r"""P10 decision layer: gate, routing, hard feasibility (FSSAI allergens), VOI asking, verified diagnosis."""
from __future__ import annotations

from culinarystate.decision.core import (Allergens, Candidate, Hypothesis, UserContext, diagnosis_answer,
                                         feasibility, relevance_gate, route, tool_requirements,
                                         value_of_information, verify)

A, T = Allergens(), tool_requirements()


def test_relevance_gate():
    assert relevance_gate("Does boiling lose more vitamin C than steaming?")["process_sensitive"]
    assert not relevance_gate("What is step 3?")["process_sensitive"]


def test_routing():
    assert route("My sauce split after adding lemon juice. Why?") == "DIAGNOSE"
    assert route("I boiled the potatoes instead of roasting them. Can I still get them crisp?") == "RECOVER"
    assert route("Is steaming or boiling better for vitamin C?", "observed") == "COMPARE"
    assert route("How does sous-vide change anthocyanins?", "unsupported") == "ABSTAIN"
    assert route("Do I need an oven?", ask="Do you have an oven?") == "ASK"


def test_allergen_authority_and_unknown_is_not_safe():
    assert "ALLERGEN-06" in A.classify("roasted cashew nuts")          # listed in Reg. 5(14)
    assert A.classify("paneer")["ALLERGEN-03"] == "INFERRED_LLM"         # proposed mapping is labelled
    res = feasibility([Candidate("stir-fry", ("PROC-stir-fry",), ("tofu", "dragonfruit"))],
                      UserContext({"hob", "wok"}, {"nut"}), A, T)[0]
    assert res["feasible"] and any("NEEDS_CHECK" in c for c in res["checks"])  # unknown ≠ safe


def test_hard_constraints():
    cands = [Candidate("bake with cashews", ("PROC-bake",), ("cashew nuts",), 40),
             Candidate("pan-fry", ("PROC-pan-fry",), ("potato",), 15)]
    res = feasibility(cands, UserContext({"hob", "pan"}, {"nut"}, 20), A, T)
    assert not res[0]["feasible"] and len(res[0]["violations"]) == 3      # oven, nut, time
    assert res[1]["feasible"]


def test_ask_only_when_it_changes_the_decision():
    cands = [Candidate("bake", ("PROC-bake",)), Candidate("pan-fry", ("PROC-pan-fry",))]
    q = value_of_information(cands, UserContext(None), A, T)
    assert q == "Do you have an oven?"
    only_hob = [Candidate("simmer", ("PROC-simmer",))]
    assert value_of_information(only_hob, UserContext(None), A, T) is None


def test_diagnosis_never_states_unverified_causes():
    hyps = [Hypothesis("too much heat", "llm:qwen2.5:3b", {"heat_level": "high"}),
            Hypothesis("acid added to hot dairy", "llm:qwen2.5:3b")]
    v = verify(hyps, {"heat_level": "low"})
    assert v[-1]["status"] == "REJECTED_BY_STATE"
    ans = diagnosis_answer(v)
    assert ans["statement"] is None and "acid added to hot dairy" in ans["possibilities_unverified"]


def test_pareto_never_imputes_unknowns():
    from culinarystate.decision.core import pareto
    opts = [{"label": "steam", "minutes": 10, "retention_lo": 80, "n_tools": 1},
            {"label": "boil", "minutes": 15, "retention_lo": 60, "n_tools": 1},          # dominated by steam
            {"label": "microwave", "minutes": 5, "retention_lo": None, "n_tools": 1},    # faster, retention unknown
            {"label": "mystery", "minutes": None, "retention_lo": None, "n_tools": None}]  # nothing known
    r = pareto(opts)
    assert r["dominated"] == {"boil": ["steam"]}
    assert {o["label"] for o in r["front"]} == {"steam", "microwave", "mystery"}
