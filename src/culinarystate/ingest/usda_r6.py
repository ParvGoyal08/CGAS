r"""
K2/K5 — USDA Table of Nutrient Retention Factors, Release 6 (SRC-0001) → EvidenceRow.

Parsing RetnDesc ("PORK,FRSH,CHOPS,BRWN,SIMMRD,W/DRIP") is a curated, auditable rule
table (every token class is explicit; unknown tokens fail the parse, so coverage is
asserted, not assumed). Semantics preserved from retn06.pdf (v4.0 AM2):

  * values are percent, reported to the nearest 5 → rounding_resolution 5, interval ±2.5
  * "factors calculated above 100 percent are reported as 100" → a reported 100 is
    RIGHT-censored (true ≥ 97.5)
  * mostly true retention, some apparent retention, per row unspecified →
    retention_method UNSPECIFIED
  * some factors imputed by USDA, rows unidentified → source_imputation_possible
  * times stated in the description (e.g. "CKD 2/2.5HRS") become RANGE/MEASURED
    conditions; nothing else is filled in — temperature stays UNKNOWN
  * "A/B" in a preparation means either A or B (process_relation ALTERNATIVES);
    "A+B" means A then B (SEQUENCE)
"""
from __future__ import annotations

import csv
import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional

from ..ledger.schema import (Basis, Censoring, Condition, ConditionStatus, EvidenceRow, OriginType,
                             Provenance, RetentionMethod, TargetType, Tier, ValueKind)

SOURCE_ID, FAMILY, SNAP = "SRC-0001", "USDA-R6-2007", "SNAP-0001"

# ------------------------------------------------------------------ food categories
# first description token(s) → (internal ING- slug, granularity note)
FOOD = {
    "CHEESE": "cheese", "EGGS": "egg", "FRUITS": "fruit", "FRUITS(DRIED)": "fruit",
    "FLOUR/MEAL": "flour-meal", "OATMEAL": "oatmeal", "CEREAL": "cereal", "PASTA": "pasta",
    "RICE": "rice", "LEGUMES": "legume", "BEEF": "beef", "CHICKEN": "chicken", "LAMB": "lamb",
    "LIVER": "liver", "ORGAN MEATS(NOTLIVER)": "organ-meat-non-liver", "PORK": "pork",
    "BACON": "bacon", "HAM/PICNIC": "ham", "SAUSAGE": "sausage", "TURKEY": "turkey",
    "VEAL": "veal", "MILK": "milk", "NUTS": "nut", "FINFISH": "finfish",
    "FINFISH(FROZEN)": "finfish", "SHELLFISH": "shellfish", "SEAFOOD": "frog-turtle",
    "POTATOES": "potato", "SWEETPOTATOES": "sweet-potato", "SWEETPOTAOTES": "sweet-potato",
    "TOMATOES": "tomato", "VEG": "vegetable", "ALC BEV": "alcoholic-beverage",
}
FOOD_SUB = {  # tokens that refine the food category
    "GREENS": "greens", "ROOTS": "roots", "ETC": None, "OTHER": "other", "FROG": None,
    "TURTLE": None, "CITRUS": "citrus", "FRESH(NOT CITRUS)": "non-citrus", "FRANKS": "franks",
    "WHITE/BROWN": None,
}
CATEGORY_FOODS = {"fruit", "flour-meal", "cereal", "legume", "organ-meat-non-liver", "sausage",
                  "nut", "finfish", "shellfish", "frog-turtle", "vegetable", "alcoholic-beverage"}
FORM = {
    "GROUND": "ground", "SLICES": "slices", "SLICE": "slices", "CHOPS": "chops",
    "ROAST": "roast cut",              # a cut of meat — NOT the process "roasted"
    "<5%FAT": "lean (<5% fat)", ">5%FAT": "fatty (>5% fat)", "W/SHELL": "with shell",
    "WO/SHELL": "without shell", "INST": "instant", "REG/QUICK": "regular/quick",
}
STATE_IN = {"FRESH": "fresh", "FRSH": "fresh", "CURED": "cured", "RAW": "raw",
            "RTE": "ready-to-eat", "PORK": None}
# preservation tokens: a state of the product, or the process itself if no other process
PRESERVE = {"FROZEN": "freeze", "CANNED": "can", "DRIED": "dehydrate"}
MODIFIER = [  # (regex, food_form text)
    (r"^W/DRIP(PINGS|PINGS|PING|PNGS|PNG)?$", "with drippings"),
    (r"^WO/DRIP(PINGS|PING|PNGS|PNG)?$", "without drippings"),
    (r"^W/COAT(ING)?$", "with coating"),
    (r"^(WO|W/O)/?\s?COAT(ING)?$", "without coating"),
]
WATER = [  # (regex, water_handling text, extra processes)
    (r"^WATER USED$", "cooking water consumed", []),
    (r"^LITTLE (WATER|WTR)$", "little water", []),
    (r"^(WATER|WTR) COVER$", "water to cover", []),
    (r"^LITTLE WATER DRAIN$", "little water", ["drain"]),
    (r"^WATER COVER DRAIN$", "water to cover", ["drain"]),
    (r"^NOT DRAINED$", "not drained", []),
]
PROC = {  # single process words (incl. USDA abbreviations and typos seen in R6)
    "BAKED": "bake", "BKD": "bake", "BROILED": "broil", "BRLD": "broil", "COOKED": "cook",
    "CKD": "cook", "REHEATED": "reheat", "FRIED": "fry", "FRYD": "fry", "SCRAMBLED": "scramble",
    "POACHED": "poach", "SAUTEED": "saute", "STEWED": "stew", "TOASTED": "toast",
    "BOILED": "boil", "BLD": "boil", "BOILD": "boil", "STEAMED": "steam", "SIMMERED": "simmer",
    "SIMMER": "simmer", "SIMMRD": "simmer", "SIMMR": "simmer", "SIMR": "simmer", "SIMRD": "simmer",
    "SIMM": "simmer", "BRWN": "brown", "BROWN": "brown", "BROWNED": "brown", "BRAISED": "braise",
    "BRAIS": "braise", "BRSD": "braise", "ROASTED": "roast", "DRAINED": "drain", "DRND": "drain",
    "DRAIND": "drain", "DRAIN": "drain", "STIR FRY": "stir-fry", "MASHED": "mash",
    "FRENCH FRY": "deep-fry", "HASH BROWN": "fry", "STIRRED": "stir", "FLAMED": "flambe",
    "STORED": "store", "HEATED": "heat", "HARD COOKED": "boil", "PARED": "peel",
}
TIME = re.compile(r"(\d+(?:\.\d+)?)(?:/(\d+(?:\.\d+)?))?\s*(MIN|HRS|HR|HOUR)", re.I)


def _minutes(x: float, unit: str) -> float:
    return x * 60.0 if unit.upper().startswith(("HR", "HOUR")) else x


@dataclass
class Parsed:
    food_slug: str
    food_tokens: list = field(default_factory=list)
    granularity: str = "INGREDIENT"
    forms: list = field(default_factory=list)
    state_in: Optional[str] = None
    processes: list = field(default_factory=list)
    alternatives: list = field(default_factory=list)
    duration_class_cook: bool = False
    time: Optional[Condition] = None
    water: list = field(default_factory=list)
    medium: Optional[str] = None
    notes: list = field(default_factory=list)
    unparsed: list = field(default_factory=list)


def _normalise(desc: str) -> list[str]:
    d = desc.upper().replace("VEAL.SLICES", "VEAL,SLICES")
    d = re.sub(r"\(BLD,DRAIND\)", ",BLD,DRAIND", d)                  # CKD FROM FRZN(BLD,DRAIND)
    d = re.sub(r"^(ORGAN MEATS\(NOTLIVER\))\s*", r"\1,", d)          # glued food + process
    return [t.strip() for t in d.split(",") if t.strip()]


def _proc_words(tok: str, P: Parsed) -> bool:
    """Parse a token that names one or more processes, with optional times."""
    t = tok
    for rx, txt, extra in WATER:
        if re.fullmatch(rx, t):
            P.water.append(txt)
            P.processes += extra
            return True
    m = TIME.search(t)
    if m:
        lo, hi, unit = float(m.group(1)), m.group(2), m.group(3)
        approx = "APPROX" in t
        if hi:
            P.time = Condition(status=ConditionStatus.RANGE, lo=_minutes(lo, unit),
                               hi=_minutes(float(hi), unit), unit="min", raw=tok)
        else:
            P.time = Condition(status=ConditionStatus.MEASURED, value=_minutes(lo, unit),
                               unit="min", raw=tok + (" (approximate)" if approx else ""))
        t = TIME.sub("", t).replace("APPROX", "").strip()
        if not t:
            return True
        if t in ("CKD", "COOKED"):          # "CKD 15/20MIN": a cooking-time class, not an extra step
            P.duration_class_cook = True
            return True
    if t in ("CKD FROM FRZN", "CKD FROM FRN", "COOKED FROM FROZEN"):
        P.state_in = "frozen"
        P.processes.append("cook")
        return True
    if t == "COOKED W/LIQUID":
        P.processes.append("cook")
        P.medium = "liquid"
        return True
    if t in ("NO HEAT",):
        P.notes.append("no heat applied")
        return True
    if t in ("STORED OVERNIGHT",):
        P.processes.append("store")
        P.time = Condition(status=ConditionStatus.QUALITATIVE, raw="overnight")
        return True
    if t in ("STIRRED INTO HOT LIQ",):
        P.processes.append("stir")
        P.medium = "hot liquid"
        return True
    if t == "NOT STIRRED IN":
        P.notes.append("not stirred in")
        return True
    m = re.fullmatch(r"(BAKED|BOILED|BLD) IN (SKIN|CASSEROLE)", t)
    if m:
        P.processes.append(PROC[m.group(1)])
        (P.forms if m.group(2) == "SKIN" else P.notes).append(
            "in skin" if m.group(2) == "SKIN" else "in casserole")
        return True
    if t == "BAKED STUFFD":
        P.processes += ["stuff", "bake"]
        return True
    if t == "BAKED W/DRIPPINGS":
        P.processes.append("bake")
        P.forms.append("with drippings")
        return True
    if t in ("BROILED CUT", "BROILED GROUND"):
        P.processes.append("broil")
        P.forms.append("cut" if t.endswith("CUT") else "ground")
        return True
    if t.startswith("SIMMERED W"):            # "SIMMERED WO/DRIP", "SIMMERED W/DRIPPNG"
        P.processes.append("simmer")
        return _modifier(t.split(" ", 1)[1], P)
    m = re.fullmatch(r"(BOILED|BLD|BOILED )\s?\(PARED\)\s?(DRAIN|DRAINED|WATER USED)", t)
    if m:
        P.processes += ["peel", "boil"]
        if m.group(2).startswith("DRAIN"):
            P.processes.append("drain")
        else:
            P.water.append("cooking water consumed")
        return True
    if "+" in t:
        parts = t.split("+")
        if all(x in PROC for x in parts):
            P.processes += [PROC[x] for x in parts]          # sequence
            return True
    if "/" in t and t not in PROC:
        parts = t.split("/")
        if all(x in PROC for x in parts):
            P.alternatives = [PROC[x] for x in parts]       # either/or, not a sequence
            return True
    if t in PROC:
        P.processes.append(PROC[t])
        return True
    return False


def _modifier(t: str, P: Parsed) -> bool:
    for rx, txt in MODIFIER:
        if re.fullmatch(rx, t.strip()):
            P.forms.append(txt)
            return True
    return False


def parse_desc(desc: str) -> Parsed:
    toks = _normalise(desc)
    head = toks[0]
    if head not in FOOD:
        return Parsed(food_slug="", unparsed=toks)
    P = Parsed(food_slug=FOOD[head], food_tokens=[head])
    if head == "FRUITS(DRIED)":
        P.state_in = "dried"
    if head == "FINFISH(FROZEN)":
        P.state_in = "frozen"
    sub = []
    preserve_seen = []
    for tok in toks[1:]:
        if tok in FOOD_SUB:
            P.food_tokens.append(tok)
            if FOOD_SUB[tok]:
                sub.append(FOOD_SUB[tok])
        elif tok in FORM:
            P.forms.append(FORM[tok])
        elif tok in STATE_IN and not (tok == "PORK" and P.food_slug != "sausage"):
            if STATE_IN[tok]:
                P.state_in = STATE_IN[tok]
            else:
                sub.append("pork")
        elif tok in PRESERVE:
            preserve_seen.append(tok)
        elif _modifier(tok, P) or _proc_words(tok, P):
            pass
        else:
            P.unparsed.append(tok)
    if P.duration_class_cook and not P.processes and not P.alternatives:
        P.processes.append("cook")          # the time class was the only process information
    for tok in preserve_seen:            # preservation = process only if nothing else was done
        if P.processes or P.alternatives:
            P.state_in = {"FROZEN": "frozen", "CANNED": "canned", "DRIED": "dried"}[tok]
        else:
            P.processes.append(PRESERVE[tok])
    if sub:
        P.food_slug = P.food_slug + "-" + "-".join(sub)
    if FOOD[head] in CATEGORY_FOODS:
        P.granularity = "CATEGORY"
    return P


NUTRIENT_CLASS = {
    "221": "alcohol", "301": "mineral", "303": "mineral", "304": "mineral", "305": "mineral",
    "306": "mineral", "307": "mineral", "309": "mineral", "312": "mineral",
    "318": "fat-soluble vitamin", "392": "fat-soluble vitamin", "321": "carotenoid",
    "322": "carotenoid", "334": "carotenoid", "337": "carotenoid", "338": "carotenoid",
    "401": "water-soluble vitamin", "404": "water-soluble vitamin", "405": "water-soluble vitamin",
    "406": "water-soluble vitamin", "415": "water-soluble vitamin", "417": "water-soluble vitamin",
    "418": "water-soluble vitamin", "431": "water-soluble vitamin", "432": "water-soluble vitamin",
    "421": "choline",
}


def ingest(csv_path: pathlib.Path, first_id: int = 1) -> tuple[list[EvidenceRow], dict]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    out: list[EvidenceRow] = []
    report = {"rows": len(rows), "codes": 0, "unparsed": {}, "defects": 0, "censored_right": 0}
    cache: dict[str, Parsed] = {}
    for k, r in enumerate(rows):
        desc = r["RetnDesc"]
        if desc not in cache:
            cache[desc] = parse_desc(desc)
            if cache[desc].unparsed or not (cache[desc].processes or cache[desc].alternatives):
                report["unparsed"][desc] = cache[desc].unparsed or ["<no process found>"]
        P = cache[desc]
        raw_val = r["Retn_Factor"].strip()
        conds = {"T": Condition()}
        if P.time is not None:
            conds["t"] = P.time
        if P.water:
            conds["water_handling"] = Condition(status=ConditionStatus.QUALITATIVE,
                                                raw="; ".join(P.water))
        if P.medium:
            conds["medium"] = Condition(status=ConditionStatus.QUALITATIVE, raw=P.medium)
        common = dict(
            evidence_id=f"EVD-{first_id + k:06d}", source_id=SOURCE_ID, source_family_id=FAMILY,
            origin_type=OriginType.DATABASE_AGGREGATE, snapshot_id=SNAP,
            source_record=f"Retn_Code={r['Retn_Code']};Nutr_No={r['Nutr_No']}",
            ingredient_raw=desc, ingredient_id=f"ING-{P.food_slug}",
            ingredient_granularity=P.granularity, food_group=f"USDA-FdGrp-{r['FdGrp_CD']}",
            food_form="; ".join(P.forms) or None, state_in=P.state_in,
            process_raw=desc, process_ids=tuple(f"PROC-{p}" for p in P.processes),
            process_alternatives=tuple(f"PROC-{p}" for p in P.alternatives), conditions=conds,
            target_type=TargetType.OTHER if r["Nutr_No"] == "221" else TargetType.NUTRIENT,
            target_variable=r["NutrDesc"], target_code=f"USDA-Nutr-{r['Nutr_No']}",
            value_kind=ValueKind.RETENTION_PERCENT, retention_method=RetentionMethod.UNSPECIFIED,
            basis=Basis.UNSPECIFIED, rounding_resolution=5.0, source_imputation_possible=True,
            tier=Tier.E3, provenance=Provenance.EXPLICIT_SOURCE,
            notes="; ".join(P.notes + [f"nutrient_class={NUTRIENT_CLASS.get(r['Nutr_No'], 'other')}"]))
        if not re.fullmatch(r"\d+", raw_val):
            report["defects"] += 1
            out.append(EvidenceRow(**common, defect=f"MISSING_VALUE_IN_SOURCE (field holds {raw_val!r})"))
            continue
        v = float(raw_val)
        if v >= 100:
            report["censored_right"] += 1
            out.append(EvidenceRow(**common, value=v, unit="%", lo=97.5, hi=None,
                                   censoring=Censoring.RIGHT))
        else:
            out.append(EvidenceRow(**common, value=v, unit="%", lo=max(0.0, v - 2.5), hi=v + 2.5))
    report["codes"] = len({r["Retn_Code"] for r in rows})
    return out, report
