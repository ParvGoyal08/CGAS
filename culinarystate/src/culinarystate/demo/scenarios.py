r"""
P11 — DEL-5 demo scenarios (v4.0 AI9: ≥ 8 course scenarios covering task types and evidence
regimes). Each scenario calls the REAL components — state engine, retrieval, B5 routing,
decision layer, unit engine — and returns a plain dict, so the demo is testable and the
Streamlit app (app/demo.py) only renders.

Inputs here are our own scripted examples; they are NOT benchmark items and never enter
dev/test sets. Verbalisation defaults to a deterministic template (no LLM); the app can switch
to the local Ollama model.
"""
from __future__ import annotations

import functools
import pathlib
import re

from ..decision.core import (Allergens, Candidate, Hypothesis, UserContext, diagnosis_answer, feasibility, pareto,
                             route, tool_requirements, value_of_information, verify)
from ..eval.ladder import Item, answer
from ..llm.client import TemplateVerbaliser
from ..quantity.grammar import parse_quantity
from ..quantity.units import Units
from ..retrieval.core import EvidenceIndex, Query, load_atoms
from ..state_graph.engine import replay
from ..state_graph.gold import load_gold

ROOT = pathlib.Path(__file__).resolve().parents[3]


TemplateLLM = TemplateVerbaliser   # demo name kept


@functools.lru_cache(maxsize=1)
def ctx():
    return {"index": EvidenceIndex(load_atoms()), "allergens": Allergens(), "tools": tool_requirements(), "units": Units()}


F01 = ROOT / "gold/fixtures/F01.A.yaml"


def _gold_f01():
    return load_gold(F01)


def _step_text(n):
    import yaml
    return next((s["text"] for s in yaml.safe_load(F01.read_text())["steps"] if s["step"] == n), None)


def _upto(g, step):
    return replay([e for e in g.events if g.step_of[e.event_id] <= step])


def _evidence(question, query, llm):
    c = ctx()
    r = answer("B5", Item("DEMO", "process_effect", question, query), c["index"], llm)
    return {"mode": r["mode"], "evidence_class": r.get("evidence_class"), "answer": r["answer"], "cited": r["cited"]}


# ------------------------------------------------------------------ scenarios
def s01_state(llm=None):
    g = _gold_f01()
    graph = _upto(g, 3)
    ents = {k: v for k, v in graph.entities.items() if k in graph.active()}
    return {"mode": "ANSWER", "answer": "After step 3 — " + "; ".join(f"{e.label}: {e.quantity.render() if e.quantity else 'amount unknown'}"
                                                   for e in ents.values()),
            "detail": {k: e.to_dict()["fields"] for k, e in ents.items()},
            "note": "the reserved butter stays '1 tbsp' (volume); the rest is '50 g − 1 tbsp', unresolved — no density invented"}


def s02_next_action(llm=None):
    g = _gold_f01()
    done_steps = 2
    graph = _upto(g, done_steps)
    nxt = min((g.step_of[e.event_id] for e in g.events if g.step_of[e.event_id] > done_steps), default=None)
    text = _step_text(nxt) if nxt else None
    return {"mode": "ANSWER", "answer": f"Next: step {nxt} — {text}" if text else f"Next: step {nxt}",
            "detail": {"active_lots": graph.active(), "state_digest": graph.digest()[:16]}}


def s03_constraints(llm=None):
    c = ctx()
    cands = [Candidate("Roast the cauliflower", ("PROC-roast",), ("cauliflower", "oil")),
             Candidate("Pan-fry cauliflower with cashews", ("PROC-fry",), ("cauliflower", "cashew", "oil")),
             Candidate("Steam the cauliflower", ("PROC-steam",), ("cauliflower",))]
    u = UserContext(None, {"nut"})
    q = value_of_information(cands, u, c["allergens"], c["tools"])
    known = feasibility(cands, UserContext({"hob", "steamer or pot with lid"}, {"nut"}), c["allergens"], c["tools"])
    return {"mode": "ASK" if q else "RECOMMEND", "answer": q or "see feasible set",
            "detail": {"tools_unknown": feasibility(cands, u, c["allergens"], c["tools"]), "if_no_oven": known},
            "note": "allergen classes from FSSAI Labelling & Display Regs (verbatim); unknown status → NEEDS_CHECK"}


def s04_diagnosis(llm=None):
    """Only OBSERVED_SESSION beliefs and the user's own report can falsify a hypothesis —
    a PLANNED value ('until fragrant') says what should have happened, not what did."""
    g = _gold_f01()
    graph = _upto(g, 3)
    obs = {f"{e.label}.{k}": b.value for e in graph.entities.values() for k, b in e.fields.items()
           if b.trajectory.value == "OBSERVED_SESSION"}
    obs["garlic butter.taste"] = "bitter"                       # the user's report
    hyps = [Hypothesis("garlic scorched while cooking in the butter", "rule:demo", {"garlic butter.taste": "bitter"}),
            Hypothesis("garlic was undercooked (raw pungency)", "rule:demo", {"garlic butter.taste": "pungent"})]
    v = verify(hyps, obs)
    return {"mode": "DIAGNOSE", "answer": diagnosis_answer(v), "detail": {"verified": v, "observed_state": obs},
            "note": "the verifier rejects the hypothesis the report contradicts; the survivor has no evidence row yet, "
                    "so it is offered as a possibility to check, never as a finding"}


def s05_recovery(llm=None):
    q = "I accidentally used all the butter for the garlic — can I still finish the dish?"
    g = _gold_f01()
    res = g.graph.entity("ENTITY-FIX-F01-butter-res") if "ENTITY-FIX-F01-butter-res" in g.graph.entities else None
    return {"mode": route(q), "answer": "The reserved 1 tbsp butter was meant for the final toss; recovery options "
                                       "cannot be evidence-backed yet (no recovery evidence source), so none is asserted.",
            "detail": {"reserved_lot": res.to_dict() if res else None}}


def s06_process_effect_observed(llm=None):
    c = ctx()
    a = next(x for x in c["index"].atoms if x.record["ingredient_raw"] == "BEEF,ROASTED" and x.target_code == "USDA-Nutr-404")
    q = Query("How much thiamin is kept when beef is roasted?", "ING-beef", a.food_group, None, ("PROC-roast",),
              "USDA-Nutr-404", a.nclass)
    return _evidence(q.text, q, llm or TemplateLLM())


def s07_process_effect_near(llm=None):
    q = Query("How much vitamin C is kept when okra is boiled?", "ING-okra", "USDA-FdGrp-11", None, ("PROC-boil",),
              "USDA-Nutr-401", "water-soluble vitamin")
    out = _evidence(q.text, q, llm or TemplateLLM())
    out["note"] = "okra is not in USDA R6 → answered as a RANGE from other boiled vegetables, labelled 'near'"
    return out


def s08_abstain(llm=None):
    q = Query("How much lycopene is kept when tomato is cooked sous vide?", "ING-tomato", None, None,
              ("PROC-sous-vide",), None, None)
    return _evidence(q.text, q, llm or TemplateLLM())


def s09_quantity(llm=None):
    u = ctx()["units"]
    p = parse_quantity("1 cup")
    uid = u.lookup("cup")
    return {"mode": "ANSWER", "answer": "1 cup is a volume; converting flour to grams needs a measured density "
                                       "(POR-), which we do not have — so no gram value is given.",
            "detail": {"parsed": repr(p), "si": repr(u.to_si(uid, 1.0)), "grams": repr(u.to_grams(uid, 1.0))}}


def s10_conflict(llm=None):
    return {"mode": "BLOCKED", "answer": "Conflict handling needs two independent sources for the same food × process × "
                                        "nutrient. Only USDA R6 is ingested (Phenol-Explorer awaits H2; literature rows await "
                                        "human verification), so no real conflict can be shown yet.", "detail": {}}


def s11_recovery_boiled_not_browned(llm=None):
    """Brief D5 example. Plan said 'brown the onions'; the cook reports they were boiled. The observation overrides
    the planned state (prediction kept in the audit trail); recovery options are feasibility-filtered, then
    Pareto-ranked on what is KNOWN — nothing about flavour chemistry is asserted without an evidence row."""
    from ..state_graph.engine import replay
    from ..state_graph.model import Amount, Belief, Event, NewLot, Op, Provenance, Quantity, Trajectory
    ev = [Event("EVT-R11-01", 1, Op.CREATE, outputs=(NewLot("ENTITY-R11-onion", "ING-onion", "onion",
                                                                Quantity.of(Amount("2 onions", "piece", 2))),)),
          Event("EVT-R11-02", 2, Op.TRANSFORM, inputs=("ENTITY-R11-onion",), process_raw="brown",
                belief=Belief("colour", "browned", Trajectory.PLANNED, Provenance.EXPLICIT_SOURCE, "EVT-R11-02")),
          Event("EVT-R11-03", 3, Op.OBSERVE, inputs=("ENTITY-R11-onion",),
                belief=Belief("colour", "pale, boiled", Trajectory.OBSERVED_SESSION, Provenance.EXPLICIT_SOURCE, "EVT-R11-03"))]
    g = replay(ev)
    onion = g.entity("ENTITY-R11-onion")
    c = ctx()
    cands = [Candidate("Drain, then sauté in oil until browned", ("PROC-drain", "PROC-saute"), ("onion", "oil")),
             Candidate("Drain and continue the recipe with the boiled onions", ("PROC-drain",), ("onion",)),
             Candidate("Start again with fresh onions, browned in a pan", ("PROC-saute",), ("onion", "oil"))]
    feas = feasibility(cands, UserContext({"hob", "pan"}, set(), None), c["allergens"], c["tools"])
    ok = [x["candidate"] for x in feas if x["feasible"]]
    opts = [{"label": lab, "minutes": None, "retention_lo": None, "n_tools": len({c["tools"].get(p) for p in cd.processes} - {None})}
            for lab, cd in ((cd.label, cd) for cd in cands) if lab in ok]
    front = pareto(opts)
    return {"mode": route("I accidentally boiled the onions instead of browning them — can I still fix it?"),
            "answer": "Your onions are recorded as boiled (your observation overrides the plan to brown them). Feasible "
                      "options: " + "; ".join(o["label"] for o in front["front"]) + ". Times and flavour effects are "
                      "not stated because no evidence row covers them here.",
            "detail": {"current_colour": onion.fields["colour"].to_dict(), "audit": onion.to_dict()["audit"],
                       "feasibility": feas, "pareto": front}}


SCENARIOS = [
    ("S01", "state", "What's in the pan, and how much butter is left?", s01_state),
    ("S02", "next_action", "I've done steps 1–2. What next?", s02_next_action),
    ("S03", "constraints", "Nut-free cauliflower — I'm not sure what equipment I have", s03_constraints),
    ("S04", "diagnosis", "Why does my garlic butter taste bitter?", s04_diagnosis),
    ("S05", "recovery", "I used all the butter for the garlic — can I still finish?", s05_recovery),
    ("S06", "process_effect / observed", "Thiamin kept when beef is roasted?", s06_process_effect_observed),
    ("S07", "process_effect / near", "Vitamin C kept when okra is boiled?", s07_process_effect_near),
    ("S08", "abstain / unsupported", "Lycopene kept in sous-vide tomato?", s08_abstain),
    ("S09", "quantity", "How many grams is 1 cup of flour?", s09_quantity),
    ("S10", "conflict", "Two sources disagree — what then?", s10_conflict),
    ("S11", "recovery / Pareto", "I boiled the onions instead of browning them — can I fix it?", s11_recovery_boiled_not_browned),
]


def run_all(llm=None) -> list[dict]:
    return [{"id": sid, "task_type": t, "question": q, **fn(llm)} for sid, t, q, fn in SCENARIOS]


def cited_ok(r: dict) -> bool:
    """Every EVD- id in the answer text exists in the ledger."""
    ids = {a.evidence_id for a in ctx()["index"].atoms}
    return all(c in ids for c in re.findall(r"EVD-\d{6}", str(r.get("answer", ""))))
