r"""
Smoke run of the B0–B5 ladder on 24 DRAFT dev items (ledger-derived; NOT the locked
benchmark; dev LLM = local Ollama). Writes experiments/DEL5/dev_smoke/results.json.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.eval.ladder import Item, answer, score  # noqa: E402
from culinarystate.llm.client import OllamaBackend  # noqa: E402
from culinarystate.retrieval.core import EvidenceIndex, Query, load_atoms  # noqa: E402

PAST = {"boil": "boiled", "bake": "baked", "fry": "fried", "simmer": "simmered", "roast": "roasted", "broil": "broiled",
        "steam": "steamed", "braise": "braised", "reheat": "reheated", "stew": "stewed", "saute": "sautéed",
        "drain": "drained", "brown": "browned", "cook": "cooked", "stir-fry": "stir-fried", "poach": "poached"}


def items(atoms, rng):
    combos = defaultdict(list)
    for a in atoms:
        if a.processes and len(a.processes) == 1 and a.processes[0].replace("PROC-", "") in PAST:
            combos[(a.ingredient_id, a.processes, a.target_code)].append(a)
    keys = sorted(combos)
    out = []
    for k, key in enumerate(rng.sample(keys, 12)):
        a = combos[key][0]
        food = a.ingredient_id.replace("ING-", "").replace("-", " ")
        verb = PAST[a.processes[0].replace("PROC-", "")]
        q = f"How much {a.target.split(',')[0]} is kept when {food} is {verb}?"
        out.append(Item(f"DEV-PE-{k:02d}", "process_effect", q,
                        Query(q, a.ingredient_id, a.food_group, a.state_in, a.processes, a.target_code, a.nclass),
                        gold={"must_abstain": False, "required_evidence_ids": [x.evidence_id for x in combos[key]]}))
    for k, (tgt, food, proc) in enumerate([("anthocyanins", "red cabbage", "PROC-steam"), ("acrylamide", "potato", "PROC-deep-fry"),
                                           ("allicin", "garlic", "PROC-saute"), ("glucosinolates", "broccoli", "PROC-boil"),
                                           ("vitamin K", "spinach", "PROC-boil"), ("vitamin E", "almonds", "PROC-roast"),
                                           ("lycopene", "tomato", "PROC-sous-vide"), ("vitamin C", "peppers", "PROC-air-fry"),
                                           ("thiamin", "maize", "PROC-nixtamalize"), ("capsaicin", "chilli", "PROC-ferment"),
                                           ("curcumin", "turmeric", "PROC-temper-spices"), ("omega-3 fatty acids", "salmon", "PROC-microwave")]):
        q = f"How much {tgt} is kept when {food} is {proc.replace('PROC-', '').replace('-', ' ')}ed?"
        out.append(Item(f"DEV-UN-{k:02d}", "unsupported", q,
                        Query(q, f"ING-{food.replace(' ', '-')}", None, None, (proc,), None, None),
                        gold={"must_abstain": True}))
    return out


def main():
    rng = random.Random(20261009)
    atoms = load_atoms()
    index = EvidenceIndex(atoms)
    llm = OllamaBackend()
    its = items(atoms, rng)
    res = {s: [] for s in ("B0", "B1", "B2", "B3", "B4", "B5", "B5-noguard")}
    for it in its:
        for s in res:
            r = answer("B5", it, index, llm, guard=False) if s == "B5-noguard" else answer(s, it, index, llm)
            res[s].append({"item": it.id, "type": it.task_type, **score(it, r, index), "answer": r["answer"],
                           "mode": r["mode"], "cited": r["cited"], "guard_fallback": r.get("guard_fallback")})
        print("done", it.id, flush=True)
    summary = {}
    for s, rows in res.items():
        n = len(rows)
        pe = [r for r in rows if r["type"] == "process_effect"]
        summary[s] = {"abstention_accuracy": sum(r["abstention_correct"] for r in rows) / n,
                      "fabricated_citations": sum(r["fabricated_citations"] for r in rows),
                      "required_evidence_recall_pe": sum(r["required_evidence_recall"] or 0 for r in pe) / len(pe),
                      "required_evidence_hit_pe": sum(bool(r["required_evidence_hit"]) for r in pe) / len(pe),
                      "unsupported_percent_claims": sum(r["unsupported_percent_claims"] for r in rows),
                      "percent_claims": sum(r["percent_claims"] for r in rows),
                      "guard_fallbacks": sum(bool(r.get("guard_fallback")) for r in rows)}
    out = ROOT / "experiments/DEL5/dev_smoke"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"note": "24 DRAFT ledger-derived dev items; local qwen2.5:3b; NOT the locked benchmark; scorer v1 (DEC-023)",
                                                   "summary": summary, "rows": res}, indent=2))
    for s, v in summary.items():
        print(s, v)


if __name__ == "__main__":
    main()
