r"""
DEL-4 development evaluation on ledger-derived synthetic queries.

    .venv/bin/python tools/eval_del4_dev.py

NOT the locked benchmark (that is the human-authored DEL-5 set, J2). This measures
the retrieval/compatibility/abstention machinery while the benchmark is being written:
  DIRECT       (food, process, nutrient) present in the ledger → expect class "observed"
  NEAR         combination absent, a sibling food in the same group has it → expect "near"
  UNSUPPORTED  target or process absent from the ledger → expect abstention
Metrics: condition-compatible Recall@5/10, MRR, evidence-class accuracy, abstention
recall, false-abstain rate, retrieval ablation, calibration (ECE) and risk–coverage
(AURC) vs an always-answer baseline. Seeded; writes experiments/DEL4/dev/metrics.json.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys
from collections import defaultdict

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.retrieval.core import (EvidenceIndex, Policy, Query, compatibility, compatible,  # noqa: E402
                                          confidence_vector, evidence_class, load_atoms)

SEED = 20261008
PAST = {"boil": "boiled", "bake": "baked", "fry": "fried", "simmer": "simmered", "roast": "roasted",
        "broil": "broiled", "steam": "steamed", "braise": "braised", "reheat": "reheated", "stew": "stewed",
        "saute": "sautéed", "drain": "drained", "brown": "browned", "cook": "cooked", "stir-fry": "stir-fried",
        "poach": "poached", "toast": "toasted", "mash": "mashed", "peel": "peeled", "freeze": "frozen",
        "can": "canned", "dehydrate": "dried", "scramble": "scrambled", "stir": "stirred", "store": "stored",
        "heat": "heated", "flambe": "flambéed", "deep-fry": "deep-fried", "stuff": "stuffed"}


def words(pid):
    return PAST.get(pid.replace("PROC-", ""), pid.replace("PROC-", "").replace("-", " "))


def make_queries(atoms, rng):
    by_combo = defaultdict(list)
    for a in atoms:
        by_combo[(a.ingredient_id, a.processes, a.target_code)].append(a)
    combos = sorted(by_combo)
    qs = []
    for c in rng.sample(combos, 150):
        a = by_combo[c][0]
        food = a.ingredient_id.replace("ING-", "").replace("-", " ")
        proc = " and ".join(words(p) for p in a.processes) or " or ".join(words(p) for p in a.alternatives)
        qs.append(("DIRECT", Query(f"how much {a.target} is retained when {food} is {proc}", a.ingredient_id,
                                   a.food_group, a.state_in, a.processes or a.alternatives[:1], a.target_code, a.nclass)))
    # NEAR: same group + same process + target, but this food never had that process
    by_group_proc = defaultdict(set)
    foods_in_group = defaultdict(set)
    for a in atoms:
        by_group_proc[(a.food_group, a.processes, a.target_code)].add(a.ingredient_id)
        foods_in_group[a.food_group].add(a.ingredient_id)
    cands = []
    for (g, procs, t), foods in sorted(by_group_proc.items(), key=lambda kv: str(kv[0])):
        if not procs:
            continue
        for f in sorted(foods_in_group[g] - foods):
            cands.append((f, g, procs, t))
    nclass = {a.target_code: (a.target, a.nclass) for a in atoms}
    for f, g, procs, t in rng.sample(cands, min(100, len(cands))):
        food = f.replace("ING-", "").replace("-", " ")
        proc = " and ".join(words(p) for p in procs)
        qs.append(("NEAR", Query(f"how much {nclass[t][0]} is retained when {food} is {proc}", f, g, None,
                                 procs, t, nclass[t][1])))
    for target in ("anthocyanins", "acrylamide", "allicin", "glucosinolates", "vitamin K", "vitamin E",
                   "chlorophyll", "omega-3 fatty acids", "capsaicin", "curcumin"):
        for food, proc in (("broccoli", "PROC-steam"), ("potato", "PROC-deep-fry"), ("garlic", "PROC-saute")):
            qs.append(("UNSUPPORTED", Query(f"how much {target} is retained when {food} is {words(proc)}",
                                            f"ING-{food}", None, None, (proc,), None, None)))
    for proc in ("PROC-sous-vide", "PROC-air-fry", "PROC-nixtamalize", "PROC-ferment", "PROC-microwave"):
        for t, tn in (("USDA-Nutr-401", "Vitamin C, total ascorbic acid"), ("USDA-Nutr-404", "Thiamin")):
            qs.append(("UNSUPPORTED", Query(f"how much {tn} is retained when vegetables are {words(proc)}",
                                            "ING-vegetable-other", "USDA-FdGrp-11", None, (proc,), t,
                                            nclass[t][1])))
    return qs


def gold_ok(kind, q, a, v):
    if kind == "DIRECT":
        return compatible(v, strict=True) and v["food"] == "MATCH" and v["process"] == "MATCH" and v["target"] == "MATCH"
    if kind == "NEAR":
        return compatible(v, strict=False) and v["target"] == "MATCH" and v["process"] == "MATCH"
    return False


def run(index, qs, use):
    atoms = index.atoms
    foods = {a.ingredient_id for a in atoms}
    procs = {p for a in atoms for p in a.processes + a.alternatives}
    out = []
    for kind, q in qs:
        ranked = index.search(q, k=10, use=use)
        hits = [(atoms[i], compatibility(q, atoms[i], index.fam)) for i, _ in ranked]
        ecls, support = evidence_class(q, hits)
        vec = confidence_vector(q, ranked, support or hits, ecls,
                                {"food": q.ingredient_id in foods, "process": set(q.processes) <= procs})
        first = next((r for r, (a, v) in enumerate(hits, 1) if gold_ok(kind, q, a, v)), None)
        out.append({"kind": kind, "class": ecls, "first_gold_rank": first, "vec": vec,
                    "top_supported": bool(first is not None and first <= 3)})
    return out


def summarise(res):
    s = {}
    for kind in ("DIRECT", "NEAR"):
        r = [x for x in res if x["kind"] == kind]
        s[kind] = {"n": len(r),
                   "recall@5": float(np.mean([x["first_gold_rank"] is not None and x["first_gold_rank"] <= 5 for x in r])),
                   "recall@10": float(np.mean([x["first_gold_rank"] is not None for x in r])),
                   "mrr": float(np.mean([1 / x["first_gold_rank"] if x["first_gold_rank"] else 0 for x in r]))}
    expect = {"DIRECT": {"observed", "conflict"}, "NEAR": {"near"}, "UNSUPPORTED": {"unsupported"}}
    s["class_accuracy"] = {k: float(np.mean([x["class"] in expect[k] for x in res if x["kind"] == k]))
                           for k in expect}
    return s


def ece(p, y, bins=10):
    p, y = np.array(p), np.array(y)
    e = 0.0
    for b in range(bins):
        m = (p >= b / bins) & (p < (b + 1) / bins if b < bins - 1 else p <= 1)
        if m.any():
            e += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(e)


def aurc(p, y):
    order = np.argsort(-np.array(p))
    yy = np.array(y)[order]
    risks = [1 - yy[: k].mean() for k in range(1, len(yy) + 1)]
    return float(np.mean(risks)), [{"coverage": (k) / len(yy), "risk": risks[k - 1]} for k in range(1, len(yy) + 1, max(1, len(yy) // 10))]


def main():
    rng = random.Random(SEED)
    atoms = load_atoms()
    index = EvidenceIndex(atoms)
    qs = make_queries(atoms, rng)
    out_dir = ROOT / "experiments/DEL4/dev"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "queries.jsonl").write_text("".join(json.dumps({"kind": k, "text": q.text}) + "\n" for k, q in qs))
    results = {"note": "synthetic dev queries from the ledger; NOT the locked DEL-5 benchmark",
               "n_queries": len(qs), "atoms": len(atoms), "retrieval_ablation": {}}
    full = None
    for name, use in (("structured", ("structured",)), ("bm25", ("bm25",)), ("dense_lsa", ("dense",)),
                      ("bm25+dense", ("bm25", "dense")), ("hybrid_all", ("structured", "bm25", "dense"))):
        res = run(index, qs, use)
        results["retrieval_ablation"][name] = summarise(res)
        if name == "hybrid_all":
            full = res
    # calibration on the hybrid system: supported = gold evidence in top 3 and class not 'unsupported'
    idx = list(range(len(full)))
    rng.shuffle(idx)
    half = len(idx) // 2
    fit_i, ev_i = idx[:half], idx[half:]
    y = [1 if (r["kind"] != "UNSUPPORTED" and r["top_supported"]) else 0 for r in full]
    pol = Policy().fit([full[i]["vec"] for i in fit_i], [y[i] for i in fit_i])
    p_ev = [pol.prob(full[i]["vec"]) for i in ev_i]
    y_ev = [y[i] for i in ev_i]
    a_ours, curve = aurc(p_ev, y_ev)
    decisions = [pol.decide(full[i]["vec"], full[i]["class"]) for i in ev_i]
    unsupported_ev = [i for i in ev_i if full[i]["kind"] == "UNSUPPORTED"]
    direct_ev = [i for i in ev_i if full[i]["kind"] == "DIRECT"]
    results["calibration_heldout_half"] = {
        "ece": ece(p_ev, y_ev), "aurc": a_ours, "risk_coverage_curve": curve,
        "always_answer_risk": float(1 - np.mean(y_ev)),
        "abstention_recall_on_unsupported": float(np.mean([pol.decide(full[i]["vec"], full[i]["class"]) == "ABSTAIN" for i in unsupported_ev])) if unsupported_ev else None,
        "false_abstain_on_direct": float(np.mean([pol.decide(full[i]["vec"], full[i]["class"]) == "ABSTAIN" for i in direct_ev])) if direct_ev else None,
        "decision_counts": {d: decisions.count(d) for d in sorted(set(decisions))},
    }
    out = ROOT / "experiments/DEL4/dev"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(results, indent=2))
    for name, s in results["retrieval_ablation"].items():
        print(f"{name:<12} DIRECT R@5={s['DIRECT']['recall@5']:.2f} R@10={s['DIRECT']['recall@10']:.2f} MRR={s['DIRECT']['mrr']:.2f} | "
              f"NEAR R@5={s['NEAR']['recall@5']:.2f} R@10={s['NEAR']['recall@10']:.2f} | class acc {s['class_accuracy']}")
    c = results["calibration_heldout_half"]
    print(f"calibration: ECE={c['ece']:.3f} AURC={c['aurc']:.3f} vs always-answer risk={c['always_answer_risk']:.3f} | "
          f"abstain on unsupported={c['abstention_recall_on_unsupported']} false-abstain on direct={c['false_abstain_on_direct']}")


if __name__ == "__main__":
    main()
