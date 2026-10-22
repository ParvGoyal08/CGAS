r"""
T10 / SSOT P10 — prioritised research cells: ingredient × process × target class.

    .venv/bin/python tools/build_research_cells.py

NOT a dense Cartesian scrape plan: the output is a ranked agenda for literature search
(T05) — each cell becomes 1 Europe PMC query, top cells first.

  score = demand × gap × target_weight × safety_boost
    demand        log1p(recipe mentions of the ingredient concept)   [A1 corpus, local only]
    process prior FLAT (=1) — process frequency needs RecipeDB instructions; A1 has ingredients only
    gap           1.0  no evidence for (ingredient, process, target class)
                  0.5  only USDA R6 CATEGORY-level evidence (e.g. onion → VEG,OTHER)
                  0.15 concept-level R6 evidence exists
                  ×0.5 if an AI-pre-checked literature cell already covers it (after T01/T02)
    target_weight vitamins/carotenoids/polyphenols 1.0, minerals 0.6 (rarely process-sensitive except leaching)
    safety_boost  1.5 for heuristic safety cells: starchy × high-heat dry (acrylamide);
                  frying oil × fry/deep-fry (oxidation products). PROPOSED heuristic, not evidence.
Applicability (which targets/processes are plausible for which ingredient class) is a PROPOSED
heuristic table below — it only orders searches; nothing becomes evidence from it.
"""
from __future__ import annotations

import json
import math
import pathlib
import re

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "research/cells"

WET = ["PROC-boil", "PROC-steam", "PROC-simmer", "PROC-blanch", "PROC-pressure-cook", "PROC-microwave", "PROC-poach"]
DRY = ["PROC-roast", "PROC-bake", "PROC-grill", "PROC-broil"]
FAT = ["PROC-fry", "PROC-deep-fry", "PROC-stir-fry", "PROC-saute"]
SPICE = ["PROC-temper-spices", "PROC-saute", "PROC-roast", "PROC-boil"]

# ingredient class → (processes, target classes, starchy?)
CLASS_RULES = {
    "ING-vegetable-other": (WET + FAT + DRY, ["water-soluble vitamin", "carotenoid", "polyphenol", "mineral"], False),
    "ING-vegetable-greens": (WET + FAT, ["water-soluble vitamin", "carotenoid", "polyphenol", "mineral"], False),
    "ING-vegetable-roots": (WET + DRY + FAT, ["water-soluble vitamin", "carotenoid", "polyphenol", "mineral"], False),
    "ING-tomato": (WET + DRY + FAT, ["water-soluble vitamin", "carotenoid", "polyphenol"], False),
    "ING-potato": (WET + DRY + FAT, ["water-soluble vitamin", "mineral", "polyphenol", "acrylamide"], True),
    "ING-sweet-potato": (WET + DRY + FAT, ["water-soluble vitamin", "carotenoid", "acrylamide"], True),
    "ING-flour-meal": (["PROC-bake", "PROC-fry", "PROC-deep-fry", "PROC-boil", "PROC-steam"], ["water-soluble vitamin", "mineral", "acrylamide"], True),
    "ING-rice": (["PROC-boil", "PROC-pressure-cook", "PROC-steam", "PROC-fry"], ["water-soluble vitamin", "mineral"], True),
    "ING-pasta": (["PROC-boil", "PROC-bake"], ["water-soluble vitamin", "mineral"], True),
    "ING-legume": (["PROC-boil", "PROC-pressure-cook", "PROC-steam", "PROC-fry"], ["water-soluble vitamin", "mineral", "polyphenol"], False),
    "ING-fruit-citrus": (["PROC-boil", "PROC-bake"], ["water-soluble vitamin", "polyphenol"], False),
    "ING-fruit-non-citrus": (["PROC-bake", "PROC-boil", "PROC-microwave"], ["water-soluble vitamin", "polyphenol", "carotenoid"], False),
    "ING-egg": (["PROC-boil", "PROC-fry", "PROC-bake", "PROC-poach", "PROC-microwave"], ["water-soluble vitamin", "fat-soluble vitamin", "carotenoid"], False),
    "ING-chicken": (WET[:3] + DRY + FAT, ["water-soluble vitamin", "mineral"], False),
    "ING-beef": (WET[:3] + DRY + FAT, ["water-soluble vitamin", "mineral"], False),
    "ING-pork": (WET[:3] + DRY + FAT, ["water-soluble vitamin", "mineral"], False),
    "ING-lamb": (WET[:3] + DRY + FAT, ["water-soluble vitamin", "mineral"], False),
    "ING-finfish": (["PROC-steam", "PROC-poach", "PROC-bake", "PROC-grill", "PROC-fry", "PROC-microwave"], ["water-soluble vitamin", "fat-soluble vitamin", "mineral"], False),
    "ING-shellfish": (["PROC-boil", "PROC-steam", "PROC-fry", "PROC-grill"], ["water-soluble vitamin", "mineral"], False),
    "ING-milk": (["PROC-boil", "PROC-simmer", "PROC-microwave"], ["water-soluble vitamin", "fat-soluble vitamin"], False),
    "ING-cheese": (["PROC-bake", "PROC-grill"], ["water-soluble vitamin", "fat-soluble vitamin"], False),
    "ING-nut": (["PROC-roast", "PROC-boil", "PROC-fry"], ["fat-soluble vitamin", "polyphenol", "mineral"], False),
}
SPICE_TARGETS = ["polyphenol", "volatile"]
MIN_MENTIONS = 20          # concepts rarer than this are long tail; they stay out of the agenda
OIL_TARGETS = ["oxidation-products", "fat-soluble vitamin", "polyphenol"]
TARGET_W = {"water-soluble vitamin": 1.0, "carotenoid": 1.0, "polyphenol": 1.0, "fat-soluble vitamin": 1.0,
            "mineral": 0.6, "volatile": 0.8, "acrylamide": 1.0, "oxidation-products": 1.0}
SAFETY = {("acrylamide", p) for p in DRY + ["PROC-fry", "PROC-deep-fry"]} | {("oxidation-products", p) for p in ["PROC-fry", "PROC-deep-fry"]}


def concept(alias: str) -> str:
    """Light, explicit normalisation of a recipe ingredient name to a search concept."""
    a = re.sub(r"\b(fresh|dried|ground|chopped|large|small|medium|baby|ripe|frozen|tinned|raw|whole|red|white|"
               r"green|yellow|brown|golden|light|dark|extra virgin|unsalted|salted)\b", " ", alias.lower())
    return re.sub(r"\s+", " ", a).strip() or alias.lower()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    al = pd.read_csv(ROOT / "ledgers/ingredients/alias_a1_v0.csv")
    ev = pd.read_parquet(ROOT / "ledgers/evidence/evidence_v0.parquet")
    ev = ev[ev["defect"].isna()].copy()
    ev["nclass"] = ev["notes"].str.extract(r"nutrient_class=([^;]+)")[0]
    r6 = set()
    for ing, procs, alts, ncl in zip(ev["ingredient_id"], ev["process_ids"], ev["process_alternatives"], ev["nclass"], strict=True):
        for p in (procs.split(";") if procs else []) + (alts.split(";") if alts else []):
            r6.add((ing, p, ncl))
    gran = ev.groupby("ingredient_id")["ingredient_granularity"].first().to_dict()

    rows = []
    mapped = al[al["outcome"].str.startswith("MAPPED")]
    for (c, ing), g in mapped.assign(concept=mapped["alias"].map(concept)).groupby(["concept", "ingredient_id"]):
        if ing not in CLASS_RULES:
            continue
        mentions = int(g["mentions"].sum())
        if mentions < MIN_MENTIONS:
            continue
        procs, targets, starchy = CLASS_RULES[ing]
        for p in dict.fromkeys(procs):
            for t in targets:
                if (ing, p, t) in r6:
                    gap = 0.15 if gran.get(ing) == "INGREDIENT" and c.split()[-1] in ing else 0.5
                else:
                    gap = 1.0
                boost = 1.5 if (t, p) in SAFETY else 1.0
                rows.append({"ingredient_concept": c, "r6_ing": ing, "process_id": p, "target_class": t,
                             "recipe_mentions": mentions, "gap": gap, "safety_heuristic": boost > 1,
                             "score": round(math.log1p(mentions) * gap * TARGET_W[t] * boost, 4)})
    spice = al[al["class"].isin(["herb_or_seed_spice", "spice_or_seasoning"])]
    for c, g in spice.assign(concept=spice["alias"].map(concept)).groupby("concept"):
        mentions = int(g["mentions"].sum())
        if mentions < 30:
            continue
        for p in SPICE:
            for t in SPICE_TARGETS:
                rows.append({"ingredient_concept": c, "r6_ing": "", "process_id": p, "target_class": t,
                             "recipe_mentions": mentions, "gap": 1.0, "safety_heuristic": False,
                             "score": round(math.log1p(mentions) * TARGET_W[t], 4)})
    oils = al[(al["outcome"] == "DERIVED_PRODUCT") & al["alias"].str.contains(r"\boil\b")]
    for c, g in oils.assign(concept=oils["alias"].map(concept)).groupby("concept"):
        mentions = int(g["mentions"].sum())
        if mentions < 30:
            continue
        for p in ["PROC-fry", "PROC-deep-fry", "PROC-stir-fry"]:
            for t in OIL_TARGETS:
                boost = 1.5 if (t, p) in SAFETY else 1.0
                rows.append({"ingredient_concept": c, "r6_ing": "", "process_id": p, "target_class": t,
                             "recipe_mentions": mentions, "gap": 1.0, "safety_heuristic": boost > 1,
                             "score": round(math.log1p(mentions) * TARGET_W[t] * boost, 4)})
    df = pd.DataFrame(rows).sort_values(["score", "recipe_mentions"], ascending=False).reset_index(drop=True)
    df.insert(0, "cell_id", [f"CELL-{i + 1:05d}" for i in range(len(df))])
    # diversified search agenda: round-robin over food classes; per class take the best unseen
    # (concept, target) cell; at most 2 cells per concept among the first 100
    df["group"] = df["r6_ing"].where(df["r6_ing"] != "", "class:" + df["target_class"].map(
        lambda t: "oil" if t == "oxidation-products" else "spice"))
    order, used, per_concept = [], set(), {}
    queues = {g: list(sub.index) for g, sub in df.groupby("group", sort=False)}
    while len(order) < 100 and any(queues.values()):
        for g in sorted(queues, key=lambda g: -df.loc[queues[g][0], "score"] if queues[g] else 0):
            while queues[g]:
                i = queues[g].pop(0)
                key = (df.at[i, "ingredient_concept"], df.at[i, "target_class"])
                if key in used or per_concept.get(df.at[i, "ingredient_concept"], 0) >= 2:
                    continue
                used.add(key)
                per_concept[df.at[i, "ingredient_concept"]] = per_concept.get(df.at[i, "ingredient_concept"], 0) + 1
                order.append(i)
                break
            if len(order) >= 100:
                break
    df["agenda_rank"] = pd.NA
    df.loc[order, "agenda_rank"] = range(1, len(order) + 1)
    df["query"] = [f'"{c}" AND ({p.replace("PROC-", "").replace("-", " ")}) AND ({t.replace("-", " ")})'
                   for c, p, t in zip(df["ingredient_concept"], df["process_id"], df["target_class"], strict=True)]
    df.to_csv(OUT / "priority_cells_v0.csv", index=False)
    rep = {"cells": len(df), "ingredient_concepts": int(df["ingredient_concept"].nunique()),
           "gap_distribution": df["gap"].value_counts().to_dict(),
           "safety_cells": int(df["safety_heuristic"].sum()),
           "agenda_top25": df.sort_values("agenda_rank").head(25)[["agenda_rank", "ingredient_concept", "process_id", "target_class", "recipe_mentions", "gap"]].values.tolist(),
           "agenda_groups_in_top100": int(df.loc[df["agenda_rank"].notna(), "group"].nunique()),
           "note": "ordering heuristic only; process prior flat until RecipeDB; applicability table PROPOSED"}
    (OUT / "priority_cells_v0.report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("cells", "ingredient_concepts", "gap_distribution", "safety_cells")}))
    print("groups in agenda top-100:", rep["agenda_groups_in_top100"])
    for r in rep["agenda_top25"]:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
