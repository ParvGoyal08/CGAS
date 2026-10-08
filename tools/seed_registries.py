r"""
WP-01 — seed the programme registries (master plan v4.0 Parts AG3, AK1, AI2).

    python tools/seed_registries.py ../Plan_SSOT15_v4_0.md ../computational_gastronomy_master_ssot_v15_0.md

Writes (all deterministic, idempotent):
    registry/experiments.csv      every SSOT ID + SX + RS + phase/track item, with the
                                  AK1 fields (scope_lane, dependency_ids, priority, owner,
                                  reviewer, data_requirement, compute_class,
                                  human_requirement, course_relevance, paper_relevance,
                                  status, restart_condition)
    registry/gates.csv            G13 / G14 / G15 / G16 / G13E + Level-12 §183.B gates,
                                  with the definition text quoted from the SSOT
    registry/scope_registry.csv   blocks B00–B17, DEL-1…5, Lane-C items, missing inputs
    registry/research_spawns.csv  all 190 Part-P questions + 80 Part-Z questions
    registry/work_packages.csv    K1–K17, P1–P15, J1–J8 (Part AJ) + WP-01…07

Statuses use the Part AG3 enum only. Every row whose status is not ACTIVE_* or
COMPLETE carries a restart condition. The script exits non-zero if any SSOT ID,
Part-P RS ID or SX ID is missing or duplicated, so it can gate CI.

Status assignments encode the approved delta plan (Lanes A/B/C). They are
DECISIONS, not facts: change them here, re-run, and record the change in
DECISIONS.md.
"""
from __future__ import annotations

import csv
import importlib.util
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "registry"

STATUSES = {"ACTIVE_COURSE", "ACTIVE_PARALLEL", "BLOCKED_HUMAN", "BLOCKED_EXTERNAL", "BLOCKED_GATE",
            "BLOCKED_COMPUTE", "PARKED_POST_COURSE", "DROPPED_BY_EXPERIMENT", "COMPLETE"}
# BLOCKED_COMPUTE is used by v4.0 Part AR3 alongside the AG3 list.
LANE = {"ACTIVE_COURSE": "A", "ACTIVE_PARALLEL": "B"}

# Owners per master prompt Part S2, with the Part AJ overrides
# (B03-lite = K15 Kush; B08 foundation = P14 Parv).
OWNER = {
    "B00": ("Kush", "Parv"), "B01": ("Parv", "Kush"), "B02": ("Kush", "Parv"),
    "B03": ("Kush", "Parv"), "B04": ("Kush", "Parv"), "B05": ("Parv", "Kush"),
    "B06": ("Kush", "Parv"), "B07": ("Parv", "Kush"), "B08": ("Parv", "Kush"),
    "B09": ("Parv", "Kush"), "B10": ("Kush", "Parv"), "B11": ("Parv", "Kush"),
    "B12": ("Kush", "Parv"), "B13": ("Parv", "Kush"), "B14": ("Parv", "Kush"),
    "B15": ("Parv", "Kush"), "B16": ("Kush", "Parv"), "B16W": ("Parv", "Kush"),
    "B17": ("Joint", "Joint"), "X": ("Joint", "Joint"),
}
PAPER = {  # SSOT §253.3–253.6 paper angles
    "B07": "dataset", "B08": "dataset", "B09": "dataset", "B10": "dataset", "B11": "dataset",
    "B16": "RAG", "B06": "transition", "B13": "transition", "B12": "transition",
    "B14": "FlavorTwin/L13", "B15": "L13E", "B04": "L12", "B03": "classical",
}
COMPUTE = {  # Part R2 job classes
    "B04": "C0/C3", "B07": "C4", "B08": "C3", "B12": "C0", "B13": "C0",
    "B16": "C0/C4", "B06": "C2/C4", "B02": "C2", "B15": "C0",
}


# --------------------------------------------------------------------- SSOT IDs
def ssot_rows():
    """(id, family, block, status, restart, course, data, human, deps, title)"""
    out = {}

    course_rq16 = {1: "DEL-5", 2: "DEL-4", 3: "DEL-4", 4: "DEL-4", 5: "DEL-4", 6: "DEL-4",
                   14: "DEL-3", 15: "DEL-3", 16: "DEL-5", 17: "DEL-5", 18: "DEL-5",
                   19: "DEL-5", 21: "DEL-4", 22: "DEL-4", 24: "DEL-3", 28: "DEL-2/DEL-5",
                   29: "DEL-5", 30: "DEL-5"}
    rq16_block = {1: "B16", 2: "B16", 3: "B16", 4: "B16", 5: "B16", 6: "B16", 7: "B10",
                  8: "B09", 9: "B07", 10: "B07", 11: "B07", 12: "B07", 13: "B07",
                  14: "B11", 15: "B11", 16: "B16W", 17: "B16W", 18: "B16W", 19: "B16W",
                  20: "B13", 21: "B13", 22: "B16", 23: "B10", 24: "B11", 25: "B14",
                  26: "B14", 27: "B16W", 28: "B17", 29: "B17", 30: "B17"}
    other_rq16 = {
        7: ("ACTIVE_PARALLEL", "", "B10 CQPO runs in Lane B; DEL-3 consumes its symbolic quantities"),
        8: ("ACTIVE_PARALLEL", "", "B09 vocabulary growth audit (P12)"),
        9: ("BLOCKED_GATE", "10k Silver pilot report says 'scale' and 25k/60k subsets exist", ""),
        10: ("PARKED_POST_COURSE", "an unlabelled Silver pool exists and a Gold-Light budget is approved", ""),
        11: ("BLOCKED_GATE", "W3 §257P gate = GO; runs inside the 10k pilot as SX-07-02", ""),
        12: ("BLOCKED_GATE", "W3 §257P gate = GO; runs inside the 10k pilot as SX-07-03", ""),
        13: ("BLOCKED_GATE", "a Silver corpus ≥10k with duplicate groups exists", ""),
        20: ("BLOCKED_GATE", "DEL-2 passes the relevant G15 gates and G16-TRANS", ""),
        23: ("PARKED_POST_COURSE", "Level-13 tasks with a quantity-rich subset exist", ""),
        25: ("BLOCKED_GATE", "G16-FT: static FlavorTwin baselines exist and process inputs are calibrated", ""),
        26: ("BLOCKED_GATE", "G16-FT + a substitution benchmark", ""),
        27: ("PARKED_POST_COURSE", "a small sensory study is approved (ethics + design)", ""),
    }
    for n in range(1, 31):
        i = f"RQ16-{n:02d}"
        blk = rq16_block[n]
        if n in course_rq16:
            out[i] = ("RQ16", blk, "ACTIVE_COURSE", "", course_rq16[n])
        else:
            st, restart, _ = other_rq16[n]
            out[i] = ("RQ16", blk, st, restart, "—")

    e16 = {"A": ("B08", "ACTIVE_PARALLEL", "", "—"), "B": ("B10", "ACTIVE_PARALLEL", "", "DEL-3"),
           "C": ("B09", "ACTIVE_PARALLEL", "", "DEL-1"), "D": ("B11", "ACTIVE_COURSE", "", "DEL-3"),
           "E": ("B16", "ACTIVE_COURSE", "", "DEL-4"), "F": ("B16", "ACTIVE_COURSE", "", "DEL-4"),
           "G": ("B16", "ACTIVE_COURSE", "", "DEL-4"), "H": ("B16W", "ACTIVE_COURSE", "", "DEL-5"),
           "I": ("B16W", "ACTIVE_COURSE", "", "DEL-5"),
           "J": ("B13", "BLOCKED_GATE", "G16-TRANS passes after DEL-2", "DEL-5 (B6)"),
           "K": ("B14", "BLOCKED_GATE", "G16-FT", "stretch"),
           "L": ("B17", "ACTIVE_COURSE", "", "DEL-5")}
    for k, (blk, st, restart, crs) in e16.items():
        out[f"E16-{k}"] = ("E16", blk, st, restart, crs)

    g16_course = {"CAL": "DEL-4", "CONFLICT": "DEL-4", "EVID": "DEL-4", "OOD": "DEL-4",
                  "PROV": "DEL-4/5", "GRAPH": "DEL-3", "DEC": "DEL-5", "REC": "DEL-5",
                  "TRANS": "DEL-5"}
    for g in ["CAL", "CONFLICT", "DATA", "DEC", "EVID", "FT", "GRAPH", "OOD", "PROV",
              "QTY", "REC", "SEM", "TRANS", "VOCAB"]:
        if g in g16_course:
            out[f"G16-{g}"] = ("G16", "B16", "ACTIVE_COURSE", "", g16_course[g])
        elif g == "FT":
            out["G16-FT"] = ("G16", "B14", "BLOCKED_GATE", "static FlavorTwin baselines exist", "stretch")
        else:
            blk = {"DATA": "B07", "SEM": "B08", "VOCAB": "B09", "QTY": "B10"}[g]
            out[f"G16-{g}"] = ("G16", blk, "ACTIVE_PARALLEL", "", "—")

    for n in range(1, 13):
        out[f"G14-{n}"] = ("G14", "B06" if n <= 2 else "B13", "ACTIVE_COURSE", "",
                           "DEL-1" if n <= 2 else "DEL-2")
    g15_course = {"1", "2", "3", "6", "7", "8", "9", "R", "H", "I"}
    g15_restart = {
        "4": "a focused kinetic dataset curated in B06 (SX-06-04) supports a fit",
        "5": "G15-4 passed",
        "10": "real-only study-disjoint baseline exists; ratio-sweep card approved",
        "11": "D-C/D-D data with true intermediate states exist",
        "12": "a validated forward model + G15-11",
        "HYB": "G15-4 + a mechanistic baseline exist",
        "INV": "G15-12 prerequisites",
        "RXN": "a measured reaction system with sufficient species/time points",
    }
    for g in [str(i) for i in range(1, 13)] + ["H", "HYB", "I", "INV", "R", "RXN"]:
        if g in g15_course:
            out[f"G15-{g}"] = ("G15", "B13", "ACTIVE_COURSE", "", "DEL-2" if g != "I" else "DEL-5")
        else:
            out[f"G15-{g}"] = ("G15", "B13", "BLOCKED_GATE", g15_restart[g], "—")

    for n in range(0, 5):
        out[f"G13-{n}"] = ("G13", "B14", "PARKED_POST_COURSE",
                           "B04-lite registry + B11 graph outputs frozen", "—")

    rq13e_active = {2: "E13E-01", 3: "E13E-02"}
    rq13e_ext = {4: "RecipeDB/Indian corpus access (E13E-03)",
                 12: "FlavorDB compound data for pairing nulls (E13E-04)"}
    for n in range(1, 23):
        i = f"RQ13E-{n:02d}"
        if n in rq13e_active:
            out[i] = ("RQ13E", "B15", "ACTIVE_PARALLEL", "", "—")
        elif n in rq13e_ext:
            out[i] = ("RQ13E", "B15", "BLOCKED_EXTERNAL", rq13e_ext[n], "—")
        else:
            out[i] = ("RQ13E", "B15", "PARKED_POST_COURSE",
                      "historical-corpus licence audit (RS-15-01) + humans make L13E a paper (§279.8)", "—")
    for n in range(1, 19):
        i = f"E13E-{n:02d}"
        if n in (1, 2):
            out[i] = ("E13E", "B15", "ACTIVE_PARALLEL", "", "—")
        elif n == 3:
            out[i] = ("E13E", "B15", "BLOCKED_EXTERNAL", "RecipeDB/Indian corpus access", "—")
        elif n == 4:
            out[i] = ("E13E", "B15", "BLOCKED_EXTERNAL", "FlavorDB compound data", "—")
        else:
            out[i] = ("E13E", "B15", "PARKED_POST_COURSE",
                      "historical-corpus licence audit (RS-15-01) + G13E-01 DATA", "—")
    for n in range(1, 16):
        i = f"G13E-{n:02d}"
        if n in (3, 4):
            out[i] = ("G13E", "B15", "ACTIVE_PARALLEL", "", "—")
        elif n in (5, 6):
            out[i] = ("G13E", "B15", "BLOCKED_EXTERNAL", "data for E13E-03/E13E-04", "—")
        else:
            out[i] = ("G13E", "B15", "PARKED_POST_COURSE", "the corresponding E13E experiment is activated", "—")
    for n in range(1, 13):
        out[f"RISK-E{n}"] = ("RISK-E", "B15", "PARKED_POST_COURSE",
                             "tracked with B15; reviewed when any E13E experiment activates", "—")
    for n in range(1, 21):
        out[f"R13E-{n:02d}"] = ("R13E", "B15", "COMPLETE",
                                "n/a — bibliographic reference, no work item", "—")

    t = {0: ("ACTIVE_PARALLEL", "", "B04-lite shares the data/evaluation spine"),
         2: ("ACTIVE_PARALLEL", "", "B04-lite RDKit fingerprints/descriptors"),
         8: ("ACTIVE_COURSE", "", "process-chemistry data acquisition = DEL-1 (SSOT L13244)"),
         1: ("PARKED_POST_COURSE", "B04-lite registry + §183.B gate 2", ""),
         3: ("BLOCKED_COMPUTE", "GPU access + §183.B gate 1", ""),
         4: ("BLOCKED_COMPUTE", "GPU access + §183.B gates 1/8", ""),
         5: ("PARKED_POST_COURSE", "§183.B gate 4", ""),
         6: ("PARKED_POST_COURSE", "mixture-perception data source identified", ""),
         7: ("PARKED_POST_COURSE", "§183.B gates 3–5", ""),
         9: ("BLOCKED_GATE", "Level-14 gates (G14) pass on DEL-1 v1", "")}
    for n, (st, restart, _) in t.items():
        out[f"T{n}"] = ("T-thread", "B04", st, restart, "DEL-1" if n == 8 else "—")

    for n in range(0, 12):
        if n <= 7:
            out[f"D{n}"] = ("D-transition", "B13", "ACTIVE_COURSE", "", "DEL-2")
        else:
            out[f"D{n}"] = ("D-transition", "B13", "BLOCKED_GATE",
                            {8: "G15-4", 9: "G15-4 + G15-HYB", 10: "G15-11 data",
                             11: "G15-11 + G15-RXN"}[n], "—")

    epic = {"A": ("B00", "ACTIVE_COURSE", "", "all"), "B": ("B09", "ACTIVE_PARALLEL", "", "DEL-1"),
            "C": ("B10", "ACTIVE_PARALLEL", "", "DEL-3"), "D": ("B11", "ACTIVE_COURSE", "", "DEL-3"),
            "E": ("B07", "BLOCKED_GATE", "W3 §257P gate = GO", "—"),
            "F": ("B11", "ACTIVE_COURSE", "", "DEL-3"), "G": ("B06", "ACTIVE_COURSE", "", "DEL-1"),
            "H": ("B16", "ACTIVE_COURSE", "", "DEL-4"), "I": ("B16", "ACTIVE_COURSE", "", "DEL-4"),
            "J": ("B16W", "ACTIVE_COURSE", "", "DEL-5"), "K": ("B16W", "ACTIVE_COURSE", "", "DEL-5"),
            "L": ("B14", "BLOCKED_GATE", "G16-FT", "stretch"),
            "M": ("B17", "ACTIVE_COURSE", "", "all")}
    for k, (blk, st, restart, crs) in epic.items():
        out[f"Epic {k}"] = ("Epic", blk, st, restart, crs)
    for n in range(1, 6):
        out[f"R{n}"] = ("R-report", "B01", "COMPLETE", "n/a — existing research report (§135, PART III)", "—")
    return out


# --------------------------------------------------------------------- SX IDs
def sx_rows():
    A, B, X, G, P, C, D = ("ACTIVE_COURSE", "ACTIVE_PARALLEL", "BLOCKED_EXTERNAL",
                           "BLOCKED_GATE", "PARKED_POST_COURSE", "BLOCKED_COMPUTE", "COMPLETE")
    m = {
        "00-01": (A, "", "all"), "00-02": (X, "cluster details provided (startup Q3)", "—"),
        "01-01": (D, "", "all"),
        "02-01": (X, "CoSyLab API keys received", "DEL-3/5"), "02-02": (A, "", "all"),
        "02-03": (G, "H2 approval per source", "DEL-1"),
        "03-01": (X, "FlavorDB compound data", "—"), "03-02": (X, "Indian regional data + FlavorDB", "—"),
        "03-03": (P, "B03-lite regression substrate complete", "—"),
        "03-04": (X, "FlavorDB + FlavorDB2 access", "—"), "03-05": (B, "", "—"),
        "04-01": (B, "", "—"), "04-02": (P, "odour/taste label source licensed", "—"),
        "04-03": (P, "§183.B gate 3", "—"), "04-04": (P, "ingredient embeddings exist", "—"),
        "04-05": (C, "GPU access", "—"),
        "05-01": (X, "RecipeDB recipe sample available", "DEL-1/3"), "05-02": (B, "", "DEL-1"),
        "05-03": (A, "", "DEL-3"), "05-04": (G, "B12 conditioning experiments active", "—"),
        "06-01": (B, "", "—"), "06-02": (A, "", "DEL-1"), "06-03": (A, "", "DEL-1"),
        "06-04": (B, "", "—"), "06-05": (B, "", "—"), "06-06": (B, "", "—"),
        "06-07": (P, "evidence + authority sources per warning class", "—"), "06-08": (A, "", "DEL-1"),
        "07-01": (A, "", "DEL-3"), "07-02": (G, "W3 §257P gate = GO", "—"),
        "07-03": (G, "W3 §257P gate = GO", "—"), "07-04": (G, "Silver ≥10k with duplicate groups", "—"),
        "07-05": (G, "Silver at ≥2 scales", "—"), "07-06": (P, "unlabelled Silver pool exists", "—"),
        "08-01": (X, "RecipeDB3 artefact permission + licence check (H2)", "—"),
        "08-02": (X, "same as SX-08-01", "—"), "08-03": (C, "GPU access", "—"),
        "08-04": (C, "GPU access", "—"), "08-05": (P, "SX-08-01 reproduced", "—"),
        "08-06": (P, "Archana's Kitchen licence audit", "—"), "08-07": (P, "SX-08-01 reproduced", "—"),
        "08-08": (G, "Silver corpus exists", "—"),
        "09-01": (B, "", "DEL-1"), "09-02": (P, "challenge set budget approved", "—"),
        "09-03": (P, "external crosswalk access", "—"), "09-04": (B, "", "—"),
        "09-05": (P, "two ontology versions available", "—"),
        "10-01": (B, "", "DEL-3"), "10-02": (A, "", "DEL-3"),
        "10-03": (P, "POR- evidence records exist", "—"),
        "10-04": (X, "RecipeDB2 access", "—"), "10-05": (P, "Indian household-measure sources", "—"),
        "10-06": (A, "", "DEL-3"), "10-07": (P, "L13 tasks exist", "—"),
        "11-01": (A, "", "DEL-3"), "11-02": (P, "graph Gold ≥100 recipes", "—"),
        "11-03": (A, "", "DEL-3"), "11-04": (A, "", "DEL-3"), "11-05": (A, "", "DEL-3"),
        "12-01": (A, "", "DEL-2"), "12-02": (A, "", "DEL-2"),
        "12-03": (G, "G14 data gates on DEL-1 v1", "—"), "12-04": (G, "G14 data gates", "—"),
        "12-05": (A, "", "DEL-2/4"),
        "13-01": (A, "", "DEL-2"), "13-02": (G, "focused kinetic dataset (SX-06-04)", "—"),
        "13-03": (A, "", "DEL-2"), "13-04": (A, "", "DEL-2"),
        "13-05": (G, "G15-10 prerequisites", "—"), "13-06": (G, "G15-11", "—"),
        "13-07": (G, "G15-12", "—"),
        "14-01": (P, "B04-lite + B11 frozen", "—"), "14-02": (P, "sensory labels exist", "—"),
        "14-03": (P, "identity Gold exists", "—"), "14-04": (P, "cuisine corpus exists", "—"),
        "14-05": (P, "substitution benchmark exists", "—"),
        "16-01": (A, "", "DEL-4"), "16-02": (A, "", "DEL-4"), "16-03": (A, "", "DEL-4"),
        "16-04": (A, "", "DEL-5"), "16-05": (A, "", "DEL-5"),
        "16-06": (G, "G16-TRANS", "DEL-5 (B6)"), "16-07": (G, "G16-FT", "stretch"),
        "16-08": (A, "", "DEL-5"),
        "16-09": (X, "UNDEFINED in master prompt (range 01–12 names only 10) — humans define or drop", "—"),
        "16-10": (X, "UNDEFINED in master prompt (range 01–12 names only 10) — humans define or drop", "—"),
        "16-11": (P, "evidence + authority sources per warning class", "—"),
        "16-12": (A, "", "DEL-5"),
    }
    e16_map = dict(zip([f"16-0{i}" for i in range(1, 9)], "EFGHIJKL", strict=True))
    return m, e16_map


# ----------------------------------------------------------- phases/tracks/misc
EXTRA = [
    # id, family, block, status, restart, course, title
    ("M1", "M-sparsity", "B13", "ACTIVE_COURSE", "", "DEL-1/2", "§226.3 data audit + D0–D6"),
    ("M2", "M-sparsity", "B13", "ACTIVE_COURSE", "", "DEL-2", "§226.4 evidence-aware completion"),
    ("M3", "M-sparsity", "B06", "ACTIVE_PARALLEL", "", "—",
     "§226.5 kinetics — evidence curation only; simulators BLOCKED_GATE until G15-4"),
    ("M4", "M-sparsity", "B13", "BLOCKED_GATE", "G15-4 + one real D-C target", "—", "§226.6 hybrid + synthetic prior"),
    ("M5", "M-sparsity", "B13", "BLOCKED_GATE", "G15-11", "—", "§226.7 procedural engine / rollout"),
    ("M6", "M-sparsity", "B13", "BLOCKED_GATE", "G15-12", "—", "§226.8 conservative inverse design"),
    ("L13-P0", "L13-phase", "B14", "PARKED_POST_COURSE", "B04-lite + B11 outputs frozen", "—", "§193.1 data spine + explicit baselines"),
    ("L13-P1", "L13-phase", "B14", "PARKED_POST_COURSE", "G13-0", "—", "§193.2 recipe-set encoder bake-off"),
    ("L13-P2", "L13-phase", "B14", "PARKED_POST_COURSE", "G13-1", "—", "§193.3 objective bake-off"),
    ("L13-P3", "L13-phase", "B14", "PARKED_POST_COURSE", "G13-2", "—", "§193.4 structured/process representation"),
    ("L13-P4", "L13-phase", "B14", "PARKED_POST_COURSE", "G13-3", "—", "§193.5 cuisine representation"),
    ("L14-DF-A", "L14-do-first", "B06", "ACTIVE_COURSE", "", "DEL-1", "§204.2 A process-event table + provenance + tiers"),
    ("L14-DF-B", "L14-do-first", "B13", "ACTIVE_COURSE", "", "DEL-2", "§204.2 B cold/grouped splits + shortcut baselines"),
    ("L14-DF-C", "L14-do-first", "B13", "ACTIVE_COURSE", "", "DEL-2",
     "§204.2 C physics/condition features — only where conditions are reported"),
    ("L14-DF-D", "L14-do-first", "B13", "ACTIVE_COURSE", "", "DEL-2", "§204.2 D strong tabular baselines"),
    ("L14-DF-E", "L14-do-first", "B13", "ACTIVE_COURSE", "", "DEL-2", "§204.2 E mixed targets"),
    ("L14-DF-F", "L14-do-first", "B16", "ACTIVE_COURSE", "", "DEL-4", "§204.2 F calibrated abstention"),
    ("L14-DF-G", "L14-do-first", "B11", "ACTIVE_COURSE", "", "DEL-3", "§204.2 G recipe-state graph schema"),
    ("L14-MVP", "L14-mvp", "B12", "BLOCKED_GATE", "G14 data gates on DEL-1 v1", "—",
     "§204.3 MVP-ablation components (concat MLP, FiLM, DeepSets, GRU)"),
    ("L15-BROAD", "L15-track", "B13", "ACTIVE_COURSE", "", "DEL-2", "§216.8 broad endpoint/retention track"),
    ("L15-FOCUSED", "L15-track", "B13", "BLOCKED_GATE", "focused kinetic dataset curated (SX-06-04)", "—",
     "§216.8 focused kinetic track"),
] + [(f"E{n}", "compiler-E", "X", "BLOCKED_EXTERNAL",
      "CulinaryState_Recipe_Compiler_FINAL_MERGED_PLAN.md provided", "—",
      "merged-plan experiment (source document not provided)") for n in range(0, 15)] + [
     (f"J{n}", "JEPA", "X", "BLOCKED_EXTERNAL",
      "source document defining JEPA J1–J5 provided (no such IDs in SSOT v15)", "—",
      "JEPA experiment (Part AK1; undefined in available documents)") for n in range(1, 6)]

DATA_REQ = {
    "B06": "public retention DBs + literature (DEL-1)", "B13": "DEL-1 v1 ledger",
    "B11": "RecipeDB recipes + RecipeDB3 annotations; fixtures", "B16": "DEL-1 ledger + benchmark",
    "B16W": "benchmark + state graph + authority tables", "B10": "unit/portion sources",
    "B09": "ingredient names + crosswalks", "B07": "licensed recipe corpus",
    "B08": "RecipeDB3 artefacts", "B04": "PubChem + FlavorDB", "B14": "recipe corpus + z_i",
    "B15": "historical corpora / A2 frequency data", "B03": "A1/A2 local data; FlavorDB",
    "B17": "all", "B00": "none", "B01": "SSOT", "B02": "source manifests", "B05": "process vocabularies",
    "B12": "DEL-1 v1 ledger", "X": "missing source document",
}
HUMAN_REQ = {
    "B11": "double annotation + adjudication", "B06": "verification against source span",
    "B16W": "human claim review", "B16": "human claim review", "B07": "Gold audit",
    "B17": "review", "B09": "alias review",
}


def priority(status: str) -> str:
    return {"ACTIVE_COURSE": "P0", "ACTIVE_PARALLEL": "P1"}.get(status, "P2")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    prompt = pathlib.Path(argv[1]).read_text(encoding="utf-8").split("\n")
    ssot = pathlib.Path(argv[2]).read_text(encoding="utf-8").split("\n")

    # ---- inputs
    with (REG / "ssot_ids.csv").open(encoding="utf-8") as fh:
        ssot_ids = list(csv.DictReader(fh))
    first_line = {r["id"]: r["first_line"] for r in ssot_ids}

    # titles from SSOT headings
    titles = {}
    for ln in ssot:
        m = re.match(r"^#{2,4} (?:\d+\.\d+ )?(RQ16-\d\d|RQ13E-\d\d|E13E-\d\d|E16-[A-L])\b\s*[—-]?\s*(.*)", ln)
        if m and m.group(1) not in titles:
            titles[m.group(1)] = m.group(2).strip()
        m = re.match(r"^### Thread (T\d) — (.*)", ln)
        if m:
            titles[m.group(1)] = m.group(2).strip()
        m = re.match(r"^## Epic ([A-M]) — (.*)", ln)
        if m:
            titles[f"Epic {m.group(1)}"] = m.group(2).strip()
        m = re.match(r"^### (D(?:1[01]|\d)) — (.*)", ln)
        if m:
            titles[m.group(1)] = m.group(2).strip()

    # ---- RS bank from the master prompt
    grp, part_p, part_z, in_z, zsec = None, [], [], False, None
    for ln in prompt:
        if ln.startswith("# PART Z"):
            in_z = True
        if ln.startswith("# PART AA"):
            in_z = False
        m = re.match(r"^### (RS-[0-9A-Z]+) (.*)", ln)
        if m:
            grp = m.group(1)
            continue
        if in_z:
            m = re.match(r"^## (Z\d)\. (.*)", ln)
            if m:
                zsec = m.group(1)
            m = re.match(r"^(\d+)\.\s+(.*)", ln)
            if m and zsec:
                part_z.append((f"RS-Z-{int(m.group(1)):02d}", zsec, m.group(2).strip()))
            continue
        m = re.match(r"^(\d+)\.\s+\((P[012])\)\s+(.*)", ln)
        if m and grp:
            part_p.append((f"{grp}-{int(m.group(1)):02d}", m.group(2), grp, m.group(3).strip()))

    # P0 node assignments: import the DAG definition (single source of truth)
    spec = importlib.util.spec_from_file_location("dag", ROOT / "tools" / "build_p0_dag.py")
    dag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dag)
    node_of = {r: n for n in dag.NODES for r in n[2]}

    # ---- research_spawns.csv (all 190 Part P + 80 Part Z)
    def toks(s):
        return {w for w in re.findall(r"[a-z]{4,}", s.lower())} - {
            "which", "what", "should", "how", "with", "from", "into", "that", "this", "their",
            "evidence", "food", "foods", "recipe", "recipes"}
    p_tok = {i: toks(q) for i, _, _, q in part_p}
    # briefs written so far (status lifecycle: QUEUED → RUNNING → BRIEFED → REVIEWED → INTEGRATED)
    BRIEFED = {"RS-08-01": "research/briefs/RS-08-ner-landscape.md", "RS-08-02": "research/briefs/RS-08-ner-landscape.md",  # DEC-039/040
               "RS-05-01": "research/briefs/RS-05-01.md", "RS-05-02": "research/briefs/RS-05-01.md",
               "RS-07-05": "research/briefs/RS-07-05.md"}
    rs_rows = []
    for i, pr, grp_, q in part_p:
        n = node_of.get(i)
        if n:
            node, wave, status, role, srcs, serves, budget = (n[0], n[1], n[9], n[5], n[6], n[7], n[8])
        else:
            node, wave, status, role, srcs, serves, budget = ("-", "-", "QUEUED-LATER", "", "", "", "")
        brief = BRIEFED.get(i, f"research/briefs/{i}.md")
        if i in BRIEFED:
            status = "BRIEFED"
        rs_rows.append([i, pr, grp_, node, wave, q, status, role, srcs, serves, budget,
                        brief, "", ""])
    for i, zsec, q in part_z:
        zt = toks(q)
        best, score = "", 0.0
        for pid, pt in p_tok.items():
            if zt and pt:
                j = len(zt & pt) / len(zt | pt)
                if j > score:
                    best, score = pid, j
        dup = f"{best} (jaccard {score:.2f})" if score >= 0.25 else ""
        rs_rows.append([i, "UNSET", f"Part {zsec}", "-", "-", q, "TRIAGE", "", "", "", "",
                        f"research/briefs/{i}.md", dup, ""])
    with (REG / "research_spawns.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rs_id", "priority", "group", "node", "wave", "question", "status",
                    "agent_role", "source_classes", "serves", "budget", "brief_path",
                    "candidate_duplicate_of", "outcome"])
        w.writerows(rs_rows)

    # ---- experiments.csv
    sr = ssot_rows()
    sxm, e16_map = sx_rows()
    sx_title = {}
    for ln in prompt:
        for m in re.finditer(r"\*\*(SX-\d\d-\d\d)\*\* ([^*\n]+)", ln):
            sx_title.setdefault(m.group(1), m.group(2).strip().rstrip("."))
    rows = []

    def add(item_id, item_type, family, block, status, restart, course, title, line, deps=""):
        assert status in STATUSES, (item_id, status)
        if status not in ("ACTIVE_COURSE", "ACTIVE_PARALLEL", "COMPLETE"):
            assert restart, f"{item_id} {status} needs a restart condition"
        own, rev = OWNER.get(block, ("Joint", "Joint"))
        rows.append([
            item_id, item_type, family, title, block, LANE.get(status, "C" if status != "COMPLETE" else "-"),
            deps, priority(status), own, rev, DATA_REQ.get(block, ""), COMPUTE.get(block, "C0"),
            HUMAN_REQ.get(block, "review"), course, PAPER.get(block, "—"), status, restart, line])

    for r in ssot_ids:
        i = r["id"]
        fam, blk, st, restart, crs = sr[i]
        itype = {"RQ16": "RESEARCH_QUESTION", "RQ13E": "RESEARCH_QUESTION", "E16": "EXPERIMENT_FAMILY",
                 "E13E": "EXPERIMENT", "G13": "GATE", "G14": "GATE", "G15": "GATE", "G16": "GATE",
                 "G13E": "GATE", "RISK-E": "RISK", "R13E": "REFERENCE", "T-thread": "THREAD",
                 "D-transition": "BASELINE_RUNG", "Epic": "EPIC", "R-report": "REPORT"}[fam]
        add(i, itype, fam, blk, st, restart, crs, titles.get(i, ""), first_line[i])
    for k, (st, restart, crs) in sxm.items():
        sid = f"SX-{k}"
        blk = f"B{k[:2]}"
        deps = f"E16-{e16_map[k]}" if k in e16_map else ""
        title = f"maps to E16-{e16_map[k]}" if k in e16_map else ""
        title = sx_title.get(sid, title)
        if k in ("16-09", "16-10"):
            title = "UNDEFINED in master prompt v4.0 — see restart_condition"
        add(sid, "SUB_EXPERIMENT", "SX", "B16W" if blk == "B16" and k in ("16-04", "16-05", "16-11") else blk,
            st, restart, crs, title, "", deps)
    for (i, fam, blk, st, restart, crs, title) in EXTRA:
        add(i, "PHASE_OR_TRACK" if fam not in ("compiler-E", "JEPA") else "EXPERIMENT",
            fam, blk, st, restart, crs, title, "")
    for rsr in rs_rows:
        rid, pr, grp_, node, wave, q, rs_status = rsr[0], rsr[1], rsr[2], rsr[3], rsr[4], rsr[5], rsr[6]
        blk = "B" + grp_.split("-")[1] if re.match(r"RS-\d\d", grp_ or "") else "X"
        if rs_status in ("QUEUED", "BRIEFED") and str(wave) in ("1", "2"):
            st, restart = ("ACTIVE_COURSE" if "DEL" in rsr[9] else "ACTIVE_PARALLEL"), ""
        elif rs_status.startswith("CONDITIONAL"):
            st, restart = "BLOCKED_EXTERNAL", "Q5 rejects A1 reuse and RecipeDB is delayed"
        elif rs_status.startswith("BLOCKED-ON-HUMAN"):
            st, restart = "BLOCKED_EXTERNAL", "cluster details provided (Q3)"
        elif rs_status.startswith("DEFERRED") or rs_status == "OPTIONAL":
            st, restart = "PARKED_POST_COURSE", f"{rs_status}; pulled when a WP needs it (Part AC)"
        elif rid == "RS-17-05":
            st, restart = "BLOCKED_EXTERNAL", "answered by the humans/professor"
        else:
            st, restart = "PARKED_POST_COURSE", "pulled only when a work package needs the fact (Part AC/AT1)"
        add(rid, "RESEARCH_SPAWN", "RS", blk if blk in OWNER else "X", st, restart,
            rsr[9] or "—", q[:120], "", "")

    with (REG / "experiments.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "item_type", "family", "title", "block", "scope_lane",
                    "dependency_ids", "priority", "owner", "reviewer", "data_requirement",
                    "compute_class", "human_requirement", "course_relevance",
                    "paper_relevance", "status", "restart_condition", "ssot_line"])
        w.writerows(rows)

    # ---- gates.csv with SSOT definition text
    gates = []

    def gate(gid, fam, text, line, applies, status):
        gates.append([gid, fam, re.sub(r"\s+", " ", text).strip()[:220], line, applies, status])

    st_of = {r[0]: r[15] for r in rows}
    crs_of = {r[0]: r[13] for r in rows}
    for idx, ln in enumerate(ssot, 1):
        m = re.match(r"^- \[ \] \*\*(G14-\d+)\*\* (.*)", ln)
        if m:
            gate(m.group(1), "G14", m.group(2), idx, crs_of[m.group(1)], st_of[m.group(1)])
        m = re.match(r"^\| \*\*(G15-[0-9A-Z]+) ([^*]+)\*\* \| (.*?) \|", ln)
        if m:
            gate(m.group(1), "G15", f"{m.group(2)}: {m.group(3)}", idx, crs_of[m.group(1)], st_of[m.group(1)])
        m = re.match(r"^### (G15-(?:RXN|HYB|INV)) — (.*)", ln)
        if m:
            body = " ".join(x.strip() for x in ssot[idx:idx + 6] if x.strip() and not x.startswith("#"))
            gate(m.group(1), "G15", f"{m.group(2)}: {body}", idx, crs_of[m.group(1)], st_of[m.group(1)])
        m = re.match(r"^### (G16-[A-Z]+)\s*$", ln)
        if m:
            nxt = next((x for x in ssot[idx:idx + 4] if x.strip()), "")
            gate(m.group(1), "G16", nxt, idx, crs_of[m.group(1)], st_of[m.group(1)])
        m = re.match(r"^\*\*Gate (G13-\d):\*\* (.*)", ln)
        if m:
            gate(m.group(1), "G13", m.group(2), idx, "—", st_of[m.group(1)])
        m = re.match(r"^\| (G13E-\d\d) ([A-Z-]+) \| (.*?) \| (.*?) \|", ln)
        if m:
            gate(m.group(1), "G13E", f"{m.group(2)}: {m.group(3)} → {m.group(4)}", idx, "—", st_of[m.group(1)])
    l12 = [l for l in ssot[13147:13160] if re.match(r"^\d+\. ", l)]
    for k, l in enumerate(l12, 1):
        gate(f"L12-G{k}", "L12-183B", re.sub(r"^\d+\. ", "", l), 13147 + k, "—",
             "ACTIVE_PARALLEL" if k in (1, 9) else "PARKED_POST_COURSE")
    gdef = {g[0]: g[2] for g in gates}
    for r in rows:
        if r[1] == "GATE" and not r[3]:
            r[3] = gdef.get(r[0], "")[:120]
    with (REG / "experiments.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "item_type", "family", "title", "block", "scope_lane",
                    "dependency_ids", "priority", "owner", "reviewer", "data_requirement",
                    "compute_class", "human_requirement", "course_relevance",
                    "paper_relevance", "status", "restart_condition", "ssot_line"])
        w.writerows(rows)
    with (REG / "gates.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["gate_id", "family", "definition_from_ssot", "ssot_line", "applies_to", "status"])
        w.writerows(gates)

    # ---- scope_registry.csv
    blocks = [
        ("B00", "Governance/repo/CI", "ACTIVE_COURSE", ""),
        ("B01", "SSOT index/registries", "ACTIVE_COURSE", ""),
        ("B02", "Sources/APIs/licences", "ACTIVE_COURSE", ""),
        ("B03", "Classical replication — B03-lite", "ACTIVE_PARALLEL", ""),
        ("B04", "Molecules/ingredients — B04-lite", "ACTIVE_PARALLEL", ""),
        ("B05", "Process ontology v0", "ACTIVE_PARALLEL", ""),
        ("B06", "State-change evidence (DEL-1)", "ACTIVE_COURSE", ""),
        ("B07", "Recipe corpus factory — 10k pilot", "BLOCKED_GATE", "W3 §257P gate = GO"),
        ("B08", "NER — foundation only", "BLOCKED_EXTERNAL", "RecipeDB3 artefact permission"),
        ("B09", "Canonical vocabulary", "ACTIVE_PARALLEL", ""),
        ("B10", "Quantity system (CQPO)", "ACTIVE_PARALLEL", ""),
        ("B11", "Event/state graph (DEL-3)", "ACTIVE_COURSE", ""),
        ("B12", "Process-conditioned representation (L14)", "BLOCKED_GATE", "G14 data gates on DEL-1 v1"),
        ("B13", "Transition/kinetics/sparsity (DEL-2)", "ACTIVE_COURSE", ""),
        ("B14", "Recipe/cuisine representation (L13)", "PARKED_POST_COURSE", "B04-lite + B11 frozen"),
        ("B15", "L13E cultural evolution — bounded chain", "ACTIVE_PARALLEL", ""),
        ("B16", "CulinaryState-RAG (DEL-4/5)", "ACTIVE_COURSE", ""),
        ("B17", "Evaluation/papers/course/release", "ACTIVE_COURSE", ""),
    ]
    dels = [("DEL-1", "Process-Effect Evidence Ledger + data card"),
            ("DEL-2", "Sparsity-aware completion + cold-split benchmark"),
            ("DEL-3", "Event-sourced state-tracking engine"),
            ("DEL-4", "Evidence-aware retrieval + calibrated abstention"),
            ("DEL-5", "End-to-end CulinaryState-RAG + benchmark + demo")]
    lane_c = [
        ("LC-SILVER-100K", "25k → 60k → 100k Silver", "BLOCKED_GATE", "10k pilot says 'scale'; §257P; licence; H3"),
        ("LC-EVID-100K", "≥100k tiered evidence rows", "PARKED_POST_COURSE", "sources genuinely support it; VOI-ranked"),
        ("LC-ING-10K", "10k+ coverage-gated ingredient concepts", "PARKED_POST_COURSE", "B09 growth audit + crosswalk access"),
        ("LC-MOL", "Broader molecule master / sensory evidence", "PARKED_POST_COURSE", "B04-lite complete"),
        ("LC-ENCODERS", "Advanced L12–L15 encoders", "BLOCKED_COMPUTE", "GPU access + level gates"),
        ("LC-KINETICS", "Learned transition + kinetic hybrids / simulators", "BLOCKED_GATE", "G15-4/5/10"),
        ("LC-NER-SOTA", "NER SOTA programme", "BLOCKED_COMPUTE", "GPU + AW10 conditions"),
        ("LC-L13E", "Full Level-13E programme", "PARKED_POST_COURSE", "historical-corpus licence audit"),
        ("LC-FLAVORTWIN", "FlavorTwin V2", "BLOCKED_GATE", "G16-FT"),
        ("LC-L17", "Level-17 multimodal / sensors", "PARKED_POST_COURSE", "core gates pass"),
        ("LC-RELEASE", "Publication/release programme", "PARKED_POST_COURSE", "H6/H7 + CLM- ledger complete"),
        ("LC-WARNINGS", "Warnings layer (SX-16-11)", "PARKED_POST_COURSE", "authority sources per warning class"),
        ("LC-DEPLOY", "Deployment (FastAPI + DB + vector index)", "PARKED_POST_COURSE", "DEL-5 complete"),
    ]
    missing = [
        ("DOC-RND-PLAN-V2", "CulinaryState_Detailed_RnD_Execution_Plan_v2.md (AG4 rank 4)", "BLOCKED_EXTERNAL", "file provided"),
        ("DOC-PROMPT-V3", "…Final_Execution_Plan_v3_0.md (Part AU)", "BLOCKED_EXTERNAL", "file provided"),
        ("DOC-MERGED-PLAN", "CulinaryState_Recipe_Compiler_FINAL_MERGED_PLAN.md (E0–E14)", "BLOCKED_EXTERNAL", "file provided"),
    ]
    with (REG / "scope_registry.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["scope_id", "kind", "title", "lane", "status", "owner", "reviewer", "restart_condition"])
        for b, t, st, restart in blocks:
            assert st in STATUSES
            own, rev = OWNER[b]
            w.writerow([b, "BLOCK", t, LANE.get(st, "C"), st, own, rev, restart])
        for d, t in dels:
            w.writerow([d, "DELIVERABLE", t, "A", "ACTIVE_COURSE", "per WP", "per WP", ""])
        for i, t, st, restart in lane_c:
            assert st in STATUSES
            w.writerow([i, "LANE_C", t, "C", st, "Joint", "Joint", restart])
        for i, t, st, restart in missing:
            w.writerow([i, "MISSING_INPUT", t, "-", st, "Joint", "Joint", restart])

    # ---- work_packages.csv (Part AJ + this session's WP-01…07)
    wps = [
        ("K1", "CI / validators / gate harness", "Kush", "Parv", "W1", "A"),
        ("K2", "USDA/source snapshot ingestion", "Kush", "Parv", "W1", "A"),
        ("K3", "schemas + provenance + condition contracts", "Kush", "Parv", "W1", "A"),
        ("K4", "Phenol-Explorer / alternative acquisition ADR", "Kush", "Parv", "W1", "A"),
        ("K5", "evidence ingestion v0", "Kush", "Parv", "W2", "A"),
        ("K6", "internal canonical names + external crosswalks", "Kush", "Parv", "W2", "A"),
        ("K7", "CQPO / unit + symbolic quantity v0", "Kush", "Parv", "W1–W3", "A/B"),
        ("K8", "verified literature evidence", "Kush", "Parv", "W3–W5", "A/B"),
        ("K9", "DEL-1 freeze + EDA", "Kush", "Parv", "W3", "A"),
        ("K10", "retrieval B1–B3", "Kush", "Parv", "W4", "A"),
        ("K11", "compatibility/confidence/calibration", "Kush", "Parv", "W5", "A"),
        ("K12", "DEL-4 locked evaluation", "Kush", "Parv", "W6", "A"),
        ("K13", "DEL-5 ladder wiring", "Kush", "Parv", "W6", "A"),
        ("K14", "locked final model/API runs", "Kush", "Parv", "W7", "A"),
        ("K15", "B03-lite classical regression substrate", "Kush", "Parv", "W1–W2", "B"),
        ("K16", "B04-lite molecule/fingerprint registry", "Kush", "Parv", "W1–W3", "B"),
        ("K17", "10k Silver pipeline support / batch validators", "Kush", "Parv", "W3–W5", "B"),
        ("P1", "registries / traceability / gates", "Parv", "Kush", "W0–W1", "A"),
        ("P2", "process ontology", "Parv", "Kush", "W1–W3", "A/B"),
        ("P3", "event/state graph core", "Parv", "Kush", "W1–W2", "A"),
        ("P4", "Gold guideline / agreement", "Parv", "Kush", "W1–W2", "A"),
        ("P5", "DEL-2 mask/split/cards", "Parv", "Kush", "W3", "A"),
        ("P6", "RecipeDB adapter / candidate pool", "Parv", "Kush", "W3", "A"),
        ("P7", "DEL-2 D0–D7 runs", "Parv", "Kush", "W4", "A"),
        ("P8", "DEL-2 results/gates", "Parv", "Kush", "W5", "A"),
        ("P9", "sessions / DEL-3 evaluation", "Parv", "Kush", "W5", "A"),
        ("P10", "decision/diagnosis/recovery", "Parv", "Kush", "W6", "A"),
        ("P11", "UI/demo", "Parv", "Kush", "W7", "A"),
        ("P12", "vocabulary/alias growth audit", "Parv", "Kush", "W3–W6", "B"),
        ("P13", "10k Silver semantic/event audit", "Parv", "Kush", "W5", "B"),
        ("P14", "B08 reproduction/scorer hygiene", "Parv", "Kush", "W2–W4", "B"),
        ("P15", "B15 bounded evolution/null reproduction if capacity", "Parv", "Kush", "W5+", "B"),
        ("J1", "research briefs and source verification", "Joint", "Joint", "W0–W2", "A"),
        ("J2", "benchmark creation/locking", "Joint", "Joint", "W2–W4", "A"),
        ("J3", "independent Gold annotation/adjudication", "Joint", "Joint", "W2–W4", "A"),
        ("J4", "human/chef review", "Joint", "Joint", "W7", "A"),
        ("J5", "final report/cards/release", "Joint", "Joint", "W8", "A"),
        ("J6", "weekly adversarial audit", "Joint", "Joint", "weekly", "A"),
        ("J7", "claim/novelty audit", "Joint", "Joint", "W7–W8", "A"),
        ("J8", "programme-scale backlog/gate review", "Joint", "Joint", "W8", "C"),
    ]
    next7 = {"P1": "WP-01", "J1": "", "P3": "WP-07"}
    # status: TODO | ACTIVE_PARALLEL | IN_PROGRESS | DONE_PENDING_REVIEW | COMPLETE | BLOCKED_HUMAN | BLOCKED_EXTERNAL | BLOCKED_GATE (DEC-034)
    # updated 2026-10-08 (DEC-020: Kush packages built in Parv's session; DEC-028)
    wp_status = {
        "K1": ("DONE_PENDING_REVIEW", "gate.py runs locally; CI executes only once the repo exists (H7)"),
        "K2": ("DONE_PENDING_REVIEW", ""), "K3": ("DONE_PENDING_REVIEW", ""),
        "K4": ("BLOCKED_EXTERNAL", "no export; terms allow non-commercial research use; maintainer request drafted (H1) — DEC-035"),
        "K5": ("DONE_PENDING_REVIEW", ""),
        "K6": ("DONE_PENDING_REVIEW", "ING v0 + A1 crosswalk are PROPOSED; stratified human audit (≥200 aliases) pending"),
        "K7": ("DONE_PENDING_REVIEW", ""),
        "K8": ("BLOCKED_HUMAN", "5,919 verbatim cells (v1) + AI pre-check (DEC-033); ≥40 HUMAN verifications needed"),
        "K9": ("IN_PROGRESS", "v0 data card done; DEL-1 v1 freeze waits on K8 verified rows"),
        "K10": ("DONE_PENDING_REVIEW", "dev only"), "K11": ("DONE_PENDING_REVIEW", "dev only"),
        "K12": ("BLOCKED_HUMAN", "locked evaluation needs the frozen benchmark (J2)"),
        "K13": ("DONE_PENDING_REVIEW", "ladder wired; dev smoke on local Ollama only"),
        "K14": ("BLOCKED_GATE", "needs H3 (Claude API spend) and the frozen benchmark"),
        "K15": ("DONE_PENDING_REVIEW", ""), "K16": ("DONE_PENDING_REVIEW", ""),
        "K17": ("BLOCKED_EXTERNAL", "10k Silver pilot needs RecipeDB access, then §257P checklist and H3"),
        "P1": ("DONE_PENDING_REVIEW", ""), "P2": ("DONE_PENDING_REVIEW", ""), "P3": ("DONE_PENDING_REVIEW", ""),
        "P4": ("DONE_PENDING_REVIEW", ""), "P5": ("DONE_PENDING_REVIEW", "card frozen, sha in preregistration.csv"),
        "P6": ("BLOCKED_EXTERNAL", "RecipeDB access (WP-03 email, H1)"),
        "P7": ("COMPLETE", "full run 20261008-004800"),
        "P8": ("COMPLETE", "results.md + verdicts.json; H2 UNDERPOWERED by card §X (DEC-032)"),
        "P9": ("BLOCKED_EXTERNAL", "RecipeDB recipes for the 20-recipe pilot and Gold"),
        "P10": ("DONE_PENDING_REVIEW", ""), "P11": ("DONE_PENDING_REVIEW", ""),
        "P12": ("DONE_PENDING_REVIEW", "audit on A1 vocabulary; rerun on RecipeDB when available"),
        "P13": ("BLOCKED_EXTERNAL", "Silver pilot not launched (see K17)"),
        "P14": ("ACTIVE_PARALLEL", "scorer + leakage audit done; resource landscape cards running; matched reproduction needs RecipeDB3 artefacts"),
        "P15": ("ACTIVE_PARALLEL", "CSN fit + null done; Kinouchi source approved (DEC-035), card in progress"),
        "J1": ("IN_PROGRESS", ""), "J2": ("BLOCKED_HUMAN", "humans author items (target 320, floor 104)"),
        "J3": ("BLOCKED_EXTERNAL", "RecipeDB recipes"), "J4": ("TODO", "after locked runs"),
        "WP-01": ("DONE_PENDING_REVIEW", ""), "WP-02": ("DONE_PENDING_REVIEW", ""),
        "WP-03": ("BLOCKED_HUMAN", "Kush sends (H1) — brief published"), "WP-04": ("BLOCKED_HUMAN", "Parv creates the GitHub repo and invites kushiiitd05 (H7)"),
        "WP-05": ("DONE_PENDING_REVIEW", "R6 downloaded and counted (SNAP-0001…0003)"),
        "WP-06": ("DONE_PENDING_REVIEW", ""), "WP-07": ("DONE_PENDING_REVIEW", ""),
    }
    with (REG / "work_packages.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["wp_id", "title", "owner", "reviewer", "weeks", "lane", "next7_id", "status", "blocker"])
        for r in wps:
            w.writerow(list(r) + [next7.get(r[0], ""), *wp_status.get(r[0], ("TODO", ""))])
        for wid, t, o, rv in [
            ("WP-01", "seed registries (P1)", "Parv", "Kush"),
            ("WP-02", "DECISIONS.md: D-1 revised, D-2…D-6, AH1–AH15, X1–X3", "Parv", "Kush"),
            ("WP-03", "edit + send Part AS email (H1)", "Kush", "Parv"),
            ("WP-04", "repo + collaborators (H7), CI skeleton, gate.py stub", "Kush", "Parv"),
            ("WP-05", "SNAP-/API- re-verification; R6 download + count", "Kush", "Parv"),
            ("WP-06", "evidence schema v1 (AH1/AH2/AM2) + broken-row CI test", "Kush", "Parv"),
            ("WP-07", "state-engine core: 3 identities, trajectory, replay, fixtures", "Parv", "Kush"),
        ]:
            w.writerow([wid, t, o, rv, "W0", "A", wid, *wp_status.get(wid, ("TODO", ""))])

    # ---- completeness assertions
    ids = Counter(r[0] for r in rows)
    dup = [k for k, v in ids.items() if v > 1]
    missing_ssot = [r["id"] for r in ssot_ids if ids[r["id"]] != 1]
    rs_ids = Counter(r[0] for r in rs_rows)
    missing_rs = [i for i, *_ in part_p if rs_ids[i] != 1]
    sx_in_prompt = set(re.findall(r"SX-\d\d-\d\d", "\n".join(prompt)))
    sx_unmapped = sorted(s for s in sx_in_prompt if s[3:] not in sxm)
    problems = []
    if dup:
        problems.append(f"duplicate experiment ids: {dup[:10]}")
    if missing_ssot:
        problems.append(f"SSOT ids not exactly once: {missing_ssot[:10]}")
    if len(part_p) != 190 or missing_rs:
        problems.append(f"Part-P RS: {len(part_p)} found, missing {missing_rs[:10]}")
    if len(part_z) != 80:
        problems.append(f"Part-Z: {len(part_z)} found (expected 80)")
    if sx_unmapped:
        problems.append(f"SX in prompt without status: {sx_unmapped}")

    st = Counter(r[15] for r in rows)
    print(f"experiments.csv  {len(rows)} rows  ({len(ssot_ids)} SSOT ids, {len(sxm)} SX, "
          f"{len(EXTRA)} phase/track/external, {len(rs_rows)} RS)")
    for k in sorted(st):
        print(f"   {k:<20} {st[k]}")
    print(f"gates.csv        {len(gates)} gates")
    print(f"research_spawns  {len(part_p)} Part P + {len(part_z)} Part Z "
          f"({sum(1 for r in rs_rows if r[12])} Z items flagged as candidate duplicates)")
    print(f"scope_registry   {len(blocks)} blocks, {len(dels)} DELs, {len(lane_c)} Lane-C, {len(missing)} missing inputs")
    print(f"work_packages    {len(wps) + 7} rows")
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print("PASS: every SSOT id, Part-P RS id and SX id appears exactly once with a valid status")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
