r"""
P10 — DEL-5 decision layer (SSOT §7 relevance gate, §243 decisions; v4.0 AO4, AI8).

  relevance_gate(question)        simple step lookup vs process-sensitive question (§7)
  route(question, ...)            one of ANSWER | COMPARE | ASK | DIAGNOSE | RECOVER | RECOMMEND | ABSTAIN
  feasibility(candidates, ctx)    HARD filters: tools, allergens (FSSAI authority, AH3), time
  value_of_information(...)       ASK only when the missing fact changes the feasible set (AO4)
  diagnose / recover              proposer → verifier; hypotheses without evidence are never
                                  stated as fact (§243.6–7, laws B1/B8)

Safety stance: an ingredient whose allergen status is unknown is "NEEDS_CHECK", never "safe".
"""
from __future__ import annotations

import csv
import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
MODES = ("ANSWER", "COMPARE", "ASK", "DIAGNOSE", "RECOVER", "RECOMMEND", "ABSTAIN")

PROCESS_CUES = r"\b(boil|boiled|steam|steamed|fry|fried|roast|roasted|bake|baked|simmer|grill|saute|sauté|" \
               r"microwave|pressure|blanch|poach|braise|stew|ferment|marinate|cook|cooked|heat|heated|reheat)\w*"
SCIENCE_CUES = r"\b(vitamin|nutrient|retain|retention|lose|loss|mineral|antioxidant|protein|denature|" \
               r"maillard|brown(ing)?|acrylamide|ph|acid|temperature|°c|°f|degrees|minutes?|hours?|texture|colou?r)\b"
DIAG_CUES = r"\b(why|what went wrong|what happened|turned|became|split|curdled|burnt|burned|soggy|rubbery|" \
            r"bitter|grainy|sunk|didn'?t rise|too (salty|thick|thin|dry))\b"
REC_CUES = r"\b(fix|rescue|save|salvage|still|recover|can i still|instead of|accidentally)\b"
COMPARE_CUES = r"\b(vs\.?|versus|compared|better|or)\b.*\b(boil|steam|fry|bake|roast|microwave|grill)"
RECOMMEND_CUES = r"\b(how should i|what should i|best way|recommend|suggest|how do i finish)\b"


def relevance_gate(q: str) -> dict:
    t = q.lower()
    reasons = [n for n, rx in (("process", PROCESS_CUES), ("science", SCIENCE_CUES),
                               ("diagnosis", DIAG_CUES), ("recovery", REC_CUES)) if re.search(rx, t)]
    return {"process_sensitive": bool(reasons), "reasons": reasons}


# ------------------------------------------------------------------ allergens (AH3)
class Allergens:
    def __init__(self):
        self.classes = {}
        with (ROOT / "ledgers/authority/allergen_v0.csv").open() as fh:
            for r in csv.DictReader(fh):
                self.classes[r["allergen_id"]] = r
        self.lex = []
        with (ROOT / "ledgers/authority/allergen_lexicon_v0.csv").open() as fh:
            for r in csv.DictReader(fh):
                self.lex.append((r["term"].lower(), r["allergen_id"], r["provenance"]))
        self.lex.sort(key=lambda x: -len(x[0]))
        self.by_name = {r["class"]: aid for aid, r in self.classes.items()}

    def classify(self, ingredient: str) -> dict:
        t = ingredient.lower()
        hits = {}
        for term, aid, prov in self.lex:
            if re.search(rf"\b{re.escape(term)}\b", t):
                hits.setdefault(aid, prov)
        return hits


# ------------------------------------------------------------------ tools
def tool_requirements() -> dict:
    """process → required tool. From proc_v0 'encodes_tool' plus definitional requirements
    (bake/roast/broil need an oven). PROPOSED, not science."""
    req = {"PROC-bake": "oven", "PROC-roast": "oven", "PROC-broil": "oven or grill",
           "PROC-grill": "grill", "PROC-steam": "steamer or pot with lid"}
    with (ROOT / "ledgers/process/proc_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            if r["encodes_tool"] and r["proc_id"] not in req:
                req[r["proc_id"]] = r["encodes_tool"]
    return req


@dataclass
class Candidate:
    label: str
    processes: tuple = ()
    ingredients: tuple = ()
    minutes: Optional[float] = None          # None = not stated (never guessed)
    evidence_ids: tuple = ()


@dataclass
class UserContext:
    tools_available: Optional[set] = None     # None = unknown
    allergens_avoid: set = field(default_factory=set)   # allergen class names, e.g. {"nut"}
    minutes_budget: Optional[float] = None


def feasibility(cands: list[Candidate], ctx: UserContext, allergens: Allergens, tools: dict) -> list[dict]:
    out = []
    avoid_ids = {allergens.by_name[a] for a in ctx.allergens_avoid if a in allergens.by_name}
    for c in cands:
        violations, checks = [], []
        for p in c.processes:
            need = tools.get(p)
            if need:
                if ctx.tools_available is None:
                    checks.append(f"tool unknown: needs {need}")
                elif not any(opt.strip() in ctx.tools_available for opt in need.split(" or ")):
                    violations.append(f"needs {need}")
        for ing in c.ingredients:
            hits = allergens.classify(ing)
            bad = set(hits) & avoid_ids
            if bad:
                violations.append(f"{ing}: contains {', '.join(allergens.classes[b]['class'] for b in sorted(bad))}")
            elif avoid_ids and not hits:
                checks.append(f"{ing}: allergen status unknown (NEEDS_CHECK)")
        if ctx.minutes_budget is not None:
            if c.minutes is None:
                checks.append("time not stated")
            elif c.minutes > ctx.minutes_budget:
                violations.append(f"takes {c.minutes:g} min > budget {ctx.minutes_budget:g}")
        out.append({"candidate": c.label, "feasible": not violations, "violations": violations, "checks": checks})
    return out


def value_of_information(cands, ctx: UserContext, allergens, tools) -> Optional[str]:
    """Return a question ONLY if answering it would change which candidates are feasible."""
    if ctx.tools_available is None:
        needed = sorted({tools[p] for c in cands for p in c.processes if p in tools})
        for t in needed:
            opts = set(t.split(" or "))
            with_t = feasibility(cands, UserContext(opts | {"hob"}, ctx.allergens_avoid, ctx.minutes_budget), allergens, tools)
            without = feasibility(cands, UserContext({"hob"}, ctx.allergens_avoid, ctx.minutes_budget), allergens, tools)
            if [x["feasible"] for x in with_t] != [x["feasible"] for x in without]:
                art = "an" if t[:1].lower() in "aeiou" else "a"
                return f"Do you have {art} {t}?"
    return None


def route(question: str, evidence_class: Optional[str] = None, ask: Optional[str] = None) -> str:
    t = question.lower()
    if re.search(DIAG_CUES, t) and not re.search(r"\b(fix|rescue|salvage|recover|still)\b", t):
        return "DIAGNOSE"
    if re.search(REC_CUES, t):
        return "RECOVER"
    if ask:
        return "ASK"
    if re.search(COMPARE_CUES, t):
        return "COMPARE" if evidence_class not in (None, "unsupported") else "ABSTAIN"
    if re.search(RECOMMEND_CUES, t):
        return "RECOMMEND"
    if evidence_class == "unsupported":
        return "ABSTAIN"
    return "ANSWER"


# ------------------------------------------------------------------ diagnosis / recovery
@dataclass
class Hypothesis:
    cause: str
    proposer: str                      # "rule:<id>" | "llm:<model>"
    requires_state: dict = field(default_factory=dict)   # field → value that must hold
    evidence_ids: tuple = ()           # EVD-/authority ids supporting the causal link


def verify(hyps: list[Hypothesis], observed_state: dict) -> list[dict]:
    """Keep hypotheses consistent with the observed session state. A hypothesis with no
    evidence is returned as UNVERIFIED — never as a stated cause."""
    out = []
    for h in hyps:
        conflict = [f for f, v in h.requires_state.items() if f in observed_state and observed_state[f] != v]
        if conflict:
            status = "REJECTED_BY_STATE"
        elif h.evidence_ids:
            status = "SUPPORTED"
        else:
            status = "UNVERIFIED"
        out.append({"cause": h.cause, "status": status, "proposer": h.proposer,
                    "conflicts": conflict, "evidence": list(h.evidence_ids)})
    rank = {"SUPPORTED": 0, "UNVERIFIED": 1, "REJECTED_BY_STATE": 2}
    return sorted(out, key=lambda x: rank[x["status"]])


def diagnosis_answer(verified: list[dict]) -> dict:
    sup = [v for v in verified if v["status"] == "SUPPORTED"]
    unv = [v for v in verified if v["status"] == "UNVERIFIED"]
    if sup:
        return {"mode": "DIAGNOSE", "statement": sup[0]["cause"], "support": sup[0]["evidence"]}
    if unv:
        return {"mode": "DIAGNOSE", "statement": None, "possibilities_unverified": [u["cause"] for u in unv],
                "note": "no evidence links these causes; presented as possibilities to check, not as findings"}
    return {"mode": "ABSTAIN", "statement": None, "note": "no hypothesis survived the state check"}
