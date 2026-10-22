r"""
K7 — unit map v0 (block B10, master prompt Part J2), built as DATA with sources.

    .venv/bin/python tools/build_unit_map_v0.py

Outputs
    ledgers/units/unit_map_v0.csv          one row per (unit, locale convention)
    ledgers/units/unit_surface_v0.csv      surface form → unit_id
    ledgers/units/recipedb_unit_terms_v0.csv   all RecipeDB S4 terms → class → unit

Value status:
  EXACT_DEFINITION   follows exactly from a legal definition (derived deterministically)
  REGULATORY         fixed by regulation for a stated purpose (21 CFR 101.9 labeling)
  CONVENTION         a national/metric convention ([C] unless verified)
  UNKNOWN            no authoritative value found → no number is stored (law B1)
Verification tags follow the research briefs: [V] primary page fetched, [C] secondary, [U].
"""
from __future__ import annotations

import csv
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "ledgers" / "units"
SEED = ROOT / "data/seeds/recipedb_units_bagler2022.txt"

GAL_US_ML = 231 * 2.54 ** 3          # US gallon = 231 in³; inch = 2.54 cm exactly
FLOZ_US = GAL_US_ML / 128            # 29.5735295625 mL
GAL_IMP_ML = 4546.09                 # imperial gallon = 4.54609 L exactly
FLOZ_IMP = GAL_IMP_ML / 160
LB_G = 453.59237                     # international pound = 0.45359237 kg exactly

S_US = "US customary: gallon = 231 in³, inch = 2.54 cm (NIST Handbook 44 App. C) [C]; derived exactly"
S_CFR = "21 CFR 101.9(b)(5)(viii), nutrition labeling only [V 2026-10-08]"
S_IMP = "imperial gallon = 4.54609 L (UK Weights and Measures Act 1985) [C]; derived exactly"
S_MET = "international metric culinary convention (tsp 5 mL, tbsp 15 mL, cup 250 mL) [C]"
S_AU = "Australian convention (National Measurement Institute): tbsp 20 mL [C, secondary source only]"
S_INTL = "international yard and pound agreement (1959): lb = 0.45359237 kg [C]; derived exactly"
S_SI = "SI definition"

# unit_id: (type, dimension, si_unit, [(locale, value, status, source)])
U = {
    "g": ("PHYSICAL", "mass", "g", [("ANY", 1.0, "EXACT_DEFINITION", S_SI)]),
    "kg": ("PHYSICAL", "mass", "g", [("ANY", 1000.0, "EXACT_DEFINITION", S_SI)]),
    "mg": ("PHYSICAL", "mass", "g", [("ANY", 0.001, "EXACT_DEFINITION", S_SI)]),
    "oz": ("PHYSICAL", "mass", "g", [("ANY", LB_G / 16, "EXACT_DEFINITION", S_INTL),
                                     ("US-LABEL", 28.0, "REGULATORY", S_CFR)]),
    "lb": ("PHYSICAL", "mass", "g", [("ANY", LB_G, "EXACT_DEFINITION", S_INTL)]),
    "ml": ("PHYSICAL", "volume", "ml", [("ANY", 1.0, "EXACT_DEFINITION", S_SI)]),
    "cl": ("PHYSICAL", "volume", "ml", [("ANY", 10.0, "EXACT_DEFINITION", S_SI)]),
    "dl": ("PHYSICAL", "volume", "ml", [("ANY", 100.0, "EXACT_DEFINITION", S_SI)]),
    "l": ("PHYSICAL", "volume", "ml", [("ANY", 1000.0, "EXACT_DEFINITION", S_SI)]),
    "fl-oz": ("CULINARY_VOLUME", "volume", "ml", [("US", FLOZ_US, "EXACT_DEFINITION", S_US),
                                                  ("US-LABEL", 30.0, "REGULATORY", S_CFR),
                                                  ("UK", FLOZ_IMP, "EXACT_DEFINITION", S_IMP)]),
    "tsp": ("CULINARY_VOLUME", "volume", "ml", [("US", FLOZ_US / 6, "EXACT_DEFINITION", S_US),
                                                ("US-LABEL", 5.0, "REGULATORY", S_CFR),
                                                ("METRIC", 5.0, "CONVENTION", S_MET),
                                                ("AU", 5.0, "CONVENTION", S_AU)]),
    "tbsp": ("CULINARY_VOLUME", "volume", "ml", [("US", FLOZ_US / 2, "EXACT_DEFINITION", S_US),
                                                 ("US-LABEL", 15.0, "REGULATORY", S_CFR),
                                                 ("METRIC", 15.0, "CONVENTION", S_MET),
                                                 ("AU", 20.0, "CONVENTION", S_AU)]),
    "cup": ("CULINARY_VOLUME", "volume", "ml", [("US", FLOZ_US * 8, "EXACT_DEFINITION", S_US),
                                                ("US-LABEL", 240.0, "REGULATORY", S_CFR),
                                                ("METRIC", 250.0, "CONVENTION", S_MET),
                                                ("AU", 250.0, "CONVENTION", S_AU)]),
    "pint": ("CULINARY_VOLUME", "volume", "ml", [("US", FLOZ_US * 16, "EXACT_DEFINITION", S_US),
                                                 ("UK", FLOZ_IMP * 20, "EXACT_DEFINITION", S_IMP)]),
    "quart": ("CULINARY_VOLUME", "volume", "ml", [("US", FLOZ_US * 32, "EXACT_DEFINITION", S_US),
                                                  ("UK", FLOZ_IMP * 40, "EXACT_DEFINITION", S_IMP)]),
    "gallon": ("CULINARY_VOLUME", "volume", "ml", [("US", GAL_US_ML, "EXACT_DEFINITION", S_US),
                                                   ("UK", GAL_IMP_ML, "EXACT_DEFINITION", S_IMP)]),
    "dessert-spoon": ("CULINARY_VOLUME", "volume", "ml", [("ANY", None, "UNKNOWN", "no authoritative value found (RS-10-01)")]),
    "glass": ("CULINARY_VOLUME", "volume", "ml", [("ANY", None, "UNKNOWN", "no standard glass volume")]),
    "katori": ("CULINARY_VOLUME", "volume", "ml", [("IN", None, "UNKNOWN", "Indian bowl; no authoritative standard found (RS-10-01)")]),
    "scoop": ("CULINARY_VOLUME", "volume", "ml", [("ANY", None, "UNKNOWN", "scoop sizes vary by tool")]),
    "inch": ("PHYSICAL", "length", "cm", [("ANY", 2.54, "EXACT_DEFINITION", S_INTL)]),
    "cm": ("PHYSICAL", "length", "cm", [("ANY", 1.0, "EXACT_DEFINITION", S_SI)]),
    "dozen": ("COUNT_MULTIPLIER", "count", "count", [("ANY", 12.0, "EXACT_DEFINITION", "definition")]),
    # count units: one item each; mass/volume grounding needs POR- evidence (Q-ladder)
    **{u: ("COUNT", "count", "count", [("ANY", 1.0, "EXACT_DEFINITION", "count of items")])
       for u in ("clove", "slice", "piece", "bunch", "sprig", "stalk", "pod", "leaf", "head", "ear",
                 "stem", "stick", "strip", "ball", "cube", "fillet", "egg", "loaf", "sheet", "chip")},
    # packages: count of packages; inner amount only if the text states it
    **{u: ("PACKAGE", "count", "count", [("ANY", 1.0, "EXACT_DEFINITION", "count of packages")])
       for u in ("can", "package", "jar", "box", "bag", "bottle", "packet", "envelope", "carton",
                 "container")},
    # verbal quantities stay QUALITATIVE: no number is stored (Part J2, §235.5)
    **{u: ("VERBAL", "none", "", [("ANY", None, "UNKNOWN", "verbal quantity; qualitative by policy")])
       for u in ("pinch", "dash", "smidgen", "drop", "splash", "handful", "sprinkle", "to-taste",
                 "as-needed", "few", "some")},
    "degC": ("TEMPERATURE", "temperature", "degC", [("ANY", 1.0, "EXACT_DEFINITION", S_SI)]),
    "degF": ("TEMPERATURE", "temperature", "degC", [("ANY", None, "EXACT_DEFINITION",
                                                     "affine: (F − 32) × 5/9; handled in code")]),
}

SURFACE = {
    "g": ["g", "gm", "gms", "gram", "grams", "gr"], "kg": ["kg", "kgs", "kilogram", "kilograms"],
    "mg": ["mg", "milligram", "milligrams"], "oz": ["oz", "ounce", "ounces"],
    "lb": ["lb", "lbs", "pound", "pounds"], "ml": ["ml", "mls", "milliliter", "milliliters", "millilitre", "millilitres"],
    "cl": ["cl"], "dl": ["dl"], "l": ["l", "liter", "liters", "litre", "litres", "ltr"],
    "fl-oz": ["fl oz", "fl. oz", "fluid ounce", "fluid ounces", "fl.oz"],
    "tsp": ["tsp", "tsps", "teaspoon", "teaspoons", "t", "tsp."],
    "tbsp": ["tbsp", "tbsps", "tablespoon", "tablespoons", "tbs", "tbl", "tbls", "T", "tbsp."],
    "cup": ["cup", "cups", "c"], "pint": ["pint", "pints", "pt"], "quart": ["quart", "quarts", "qt"],
    "gallon": ["gallon", "gallons", "gal"], "dessert-spoon": ["dessertspoon", "dessert spoon", "dsp"],
    "glass": ["glass", "glasses"], "katori": ["katori", "katoris", "bowl"], "scoop": ["scoop", "scoops"],
    "inch": ["inch", "inches", "in"], "cm": ["cm", "centimeter", "centimetre", "centimeters", "centimetres"],
    "dozen": ["dozen"], "clove": ["clove", "cloves"], "slice": ["slice", "slices"],
    "piece": ["piece", "pieces", "pc", "pcs"], "bunch": ["bunch", "bunches"], "sprig": ["sprig", "sprigs"],
    "stalk": ["stalk", "stalks"], "pod": ["pod", "pods"], "leaf": ["leaf", "leaves"],
    "head": ["head", "heads"], "ear": ["ear", "ears"], "stem": ["stem", "stems"],
    "stick": ["stick", "sticks"], "strip": ["strip", "strips"], "ball": ["ball", "balls"],
    "cube": ["cube", "cubes"], "fillet": ["fillet", "fillets"], "egg": ["egg", "eggs"],
    "loaf": ["loaf", "loaves"], "sheet": ["sheet", "sheets"], "chip": ["chip", "chips"],
    "can": ["can", "cans", "tin", "tins"], "package": ["package", "packages", "pkg", "pack", "packs"],
    "jar": ["jar", "jars"], "box": ["box", "boxes"], "bag": ["bag", "bags"],
    "bottle": ["bottle", "bottles"], "packet": ["packet", "packets", "sachet", "sachets"],
    "envelope": ["envelope", "envelopes"], "carton": ["carton", "cartons"],
    "container": ["container", "containers", "tub", "tubs"], "pinch": ["pinch", "pinches"],
    "dash": ["dash", "dashes"], "smidgen": ["smidgen", "smidgens"], "drop": ["drop", "drops"],
    "splash": ["splash", "splashes"], "handful": ["handful", "handfuls"],
    "sprinkle": ["sprinkle", "sprinkles"], "to-taste": ["to taste"],
    "as-needed": ["as needed", "as required", "as per taste", "as per requirement"],
    "few": ["few", "a few"], "some": ["some"], "degC": ["°c", "c", "degc", "celsius"],
    "degF": ["°f", "f", "degf", "fahrenheit"],
}

# RecipeDB S4 terms: class + target
CLS = {
    "UNIT": None, "SIZE_DESCRIPTOR": None, "FORM_DESCRIPTOR": None, "NON_UNIT": None,
}
TERMS = {
    "cup": ("UNIT", "cup"), "teaspoon": ("UNIT", "tsp"), "tablespoon": ("UNIT", "tbsp"),
    "ounce": ("UNIT", "oz"), "can": ("UNIT", "can"), "lb": ("UNIT", "lb"),
    "package": ("UNIT", "package"), "clove": ("UNIT", "clove"), "pinch": ("UNIT", "pinch"),
    "slice": ("UNIT", "slice"), "gm": ("UNIT", "g"), "pound": ("UNIT", "lb"), "bunch": ("UNIT", "bunch"),
    "dash": ("UNIT", "dash"), "pods": ("UNIT", "pod"), "jar": ("UNIT", "jar"), "stalks": ("UNIT", "stalk"),
    "ml": ("UNIT", "ml"), "quart": ("UNIT", "quart"), "sprig": ("UNIT", "sprig"),
    "halved": ("FORM_DESCRIPTOR", ""), "piece": ("UNIT", "piece"), "inch": ("UNIT", "inch"),
    "pint": ("UNIT", "pint"), "box": ("UNIT", "box"), "bag": ("UNIT", "bag"), "bottle": ("UNIT", "bottle"),
    "loaf": ("UNIT", "loaf"), "packet": ("UNIT", "packet"), "drop": ("UNIT", "drop"),
    "envelope": ("UNIT", "envelope"), "kg": ("UNIT", "kg"), "sheet": ("UNIT", "sheet"),
    "fluid ounce": ("UNIT", "fl-oz"), "leaves": ("UNIT", "leaf"), "head": ("UNIT", "head"),
    "cubes": ("UNIT", "cube"), "carton": ("UNIT", "carton"), "gallon": ("UNIT", "gallon"),
    "stick": ("UNIT", "stick"), "scoop": ("UNIT", "scoop"), "bottles": ("UNIT", "bottle"),
    "thin": ("SIZE_DESCRIPTOR", ""), "glass": ("UNIT", "glass"), "container": ("UNIT", "container"),
    "square": ("FORM_DESCRIPTOR", ""), "ear": ("UNIT", "ear"), "liters": ("UNIT", "l"),
    "dozen": ("UNIT", "dozen"), "scotch": ("NON_UNIT", ""), "cup halved": ("NON_UNIT", ""),
    "strip": ("UNIT", "strip"), "can bottle": ("NON_UNIT", ""), "thick": ("SIZE_DESCRIPTOR", ""),
    "cm": ("UNIT", "cm"), "long": ("SIZE_DESCRIPTOR", ""), "handful": ("UNIT", "handful"),
    "round": ("FORM_DESCRIPTOR", ""), "splash": ("UNIT", "splash"),
    "thick slices": ("FORM_DESCRIPTOR", ""), "chips": ("UNIT", "chip"), "big": ("SIZE_DESCRIPTOR", ""),
    "slightly": ("NON_UNIT", ""), "thin slices": ("FORM_DESCRIPTOR", ""), "stems": ("UNIT", "stem"),
    "cloves": ("UNIT", "clove"), "sprinkles": ("UNIT", "sprinkle"), "balls": ("UNIT", "ball"),
    "few": ("UNIT", "few"),
}
MUST_INCLUDE = ["tsp", "tbsp", "dessert-spoon", "cup", "fl-oz", "glass", "katori", "pinch", "dash",
                "smidgen", "drop", "splash", "handful", "clove", "fillet", "slice", "head", "bunch",
                "sprig", "stick", "can", "packet", "g", "kg", "oz", "lb", "ml", "l"]   # Part J2


def main() -> int:
    problems = []
    seed = [l.strip() for l in SEED.read_text().splitlines() if l.strip() and not l.startswith("#")]
    uniq = list(dict.fromkeys(seed))
    for t in uniq:
        if t not in TERMS:
            problems.append(f"RecipeDB unit term unclassified: {t!r}")
        elif TERMS[t][0] == "UNIT" and TERMS[t][1] not in U:
            problems.append(f"{t!r} → unknown unit {TERMS[t][1]}")
    for u in MUST_INCLUDE:
        if u not in U:
            problems.append(f"Part J2 unit missing: {u}")
    for u in SURFACE:
        if u not in U:
            problems.append(f"surface map for unknown unit {u}")
    for u, (_t, _d, _s, variants) in U.items():
        for loc, val, st, src in variants:
            if st == "UNKNOWN" and val is not None:
                problems.append(f"{u}/{loc}: UNKNOWN must not carry a value")
            if not src:
                problems.append(f"{u}/{loc}: no source")

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "unit_map_v0.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["unit_id", "type", "dimension", "si_unit", "locale", "si_value", "value_status", "source"])
        for u, (typ, dim, si, variants) in U.items():
            for loc, val, st, src in variants:
                w.writerow([f"UNIT-{u}", typ, dim, si, loc, "" if val is None else repr(val), st, src])
    with (OUT / "unit_surface_v0.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["surface", "unit_id", "case_sensitive"])
        for u, forms in SURFACE.items():
            for f in forms:
                w.writerow([f, f"UNIT-{u}", "yes" if f in ("T", "t", "c") else "no"])
    with (OUT / "recipedb_unit_terms_v0.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["recipedb_term", "class", "unit_id", "status"])
        for t in uniq:
            cls, tgt = TERMS.get(t, ("UNCLASSIFIED", ""))
            w.writerow([t, cls, f"UNIT-{tgt}" if tgt else "", "PROPOSED"])
    cc = Counter(TERMS[t][0] for t in uniq if t in TERMS)
    print(f"RecipeDB S4: {len(seed)} printed cells, {len(uniq)} unique (table title says 71) | classes {dict(cc)}")
    print(f"units: {len(U)} | variant rows: {sum(len(v[3]) for v in U.values())} | surfaces: {sum(map(len, SURFACE.values()))}")
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print("PASS: every RecipeDB unit term classified; Part J2 list complete; UNKNOWN carries no number")
    return 0


if __name__ == "__main__":
    sys.exit(main())
