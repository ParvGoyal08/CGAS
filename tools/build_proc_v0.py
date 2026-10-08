r"""
P2 — build the process ontology v0 (block B05) from cited seeds.

    python tools/build_proc_v0.py

Inputs
    data/seeds/recipedb_processing_actions_bagler2022.txt   270 RecipeDB terms (brief RS-05-01)
Outputs
    ledgers/process/process_families_v0.csv    family hierarchy (RS-05-02)
    ledgers/process/proc_v0.csv                canonical PROC- records
    ledgers/process/recipedb_term_map_v0.csv   every RecipeDB term → class → PROC- (or why not)

Rules (master prompt §B05, law B1/B10, v4.0 AH2):
  * every classification is PROPOSED (LLM-assisted semantic judgement); the SX-05-02
    human audit decides. Nothing here is a scientific claim.
  * parameters, mechanism links and safety text are UNKNOWN by construction: they
    come only from B06 evidence and authority sources. A `safety_review_required`
    flag marks processes whose warnings need an authority source.
  * external crosswalks are optional (AH2): UNRESOLVED_EXTERNAL unless verified in
    brief RS-05-01.
  * IDs are slugs (PROC-stir-fry): stable, readable, never renumbered.
Exit code 1 if any check fails.
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "data/seeds/recipedb_processing_actions_bagler2022.txt"
OUT = ROOT / "ledgers/process"

# ------------------------------------------------------------- family hierarchy
FAMILY_GROUP = {
    "THERMAL_WET": "THERMAL", "THERMAL_DRY": "THERMAL", "THERMAL_FAT": "THERMAL",
    "THERMAL_GENERAL": "THERMAL", "THERMAL_DIELECTRIC": "THERMAL", "SMOKE": "THERMAL_CHEMICAL",
    "COLD": "COLD", "SIZE_REDUCTION": "MECHANICAL", "SURFACE_REMOVAL": "MECHANICAL",
    "PIERCE_SCORE": "MECHANICAL", "MIXING": "MECHANICAL", "SEPARATION": "MECHANICAL",
    "SHAPING": "MECHANICAL", "MANIPULATION": "MECHANICAL", "COATING": "SURFACE_APPLICATION",
    "SEASON_FLAVOUR": "SURFACE_APPLICATION", "ASSEMBLY": "ASSEMBLY_TRANSFER",
    "TRANSFER": "ASSEMBLY_TRANSFER", "PORTION_SPLIT": "ASSEMBLY_TRANSFER",
    "SERVE": "ASSEMBLY_TRANSFER", "CONTAINER": "CONTAINER_TOOL", "TOOL_STATE": "CONTAINER_TOOL",
    "STORAGE": "CONTAINER_TOOL", "CHEMICAL": "CHEMICAL", "BIOLOGICAL": "BIOLOGICAL",
    "REST_HOLD": "REST_HOLD", "LIQUID_HOLD": "REST_HOLD", "CLEAN_PREP": "HYGIENE",
}
FAMILY_NOTE = {
    "THERMAL_WET": "heat transferred through water, steam or another aqueous liquid",
    "THERMAL_DRY": "heat by hot air, radiant or contact heat without a fat medium",
    "THERMAL_FAT": "heat transferred through a fat/oil medium",
    "THERMAL_GENERAL": "heating where the medium is not specified by the verb",
    "THERMAL_DIELECTRIC": "microwave (dielectric) heating",
    "SMOKE": "exposure to smoke; hot vs cold smoking is a condition, not a separate verb here",
    "COLD": "cooling, chilling, freezing, thawing",
    "SIZE_REDUCTION": "cutting, comminution, pureeing",
    "SURFACE_REMOVAL": "removing peel, skin, veins or trim",
    "PIERCE_SCORE": "piercing or scoring without dividing",
    "MIXING": "combining or agitating materials",
    "SEPARATION": "separating phases or particles (drain, strain, sift, skim)",
    "SHAPING": "changing shape without dividing",
    "MANIPULATION": "moving or orienting a food or vessel (flip, rotate, invert)",
    "COATING": "applying a layer to a surface",
    "SEASON_FLAVOUR": "adding seasoning or dressing",
    "ASSEMBLY": "building a composite item (stuff, layer, thread)",
    "TRANSFER": "moving material between vessels/locations",
    "PORTION_SPLIT": "dividing into portions or reserving part",
    "SERVE": "plating/serving",
    "CONTAINER": "operations on lids, wraps, seals",
    "TOOL_STATE": "changing the state of a tool (preheat, adjust heat)",
    "STORAGE": "holding food for later use",
    "CHEMICAL": "acid, salt, alkali or solvent treatment",
    "BIOLOGICAL": "fermentation, proofing, sprouting",
    "REST_HOLD": "letting food stand/rest/hold over time",
    "LIQUID_HOLD": "holding in a liquid without stated heat (soak, steep)",
    "CLEAN_PREP": "washing, drying, sorting",
}

# --------------------------------------------- canonical processes (PROPOSED)
# slug: (family, parent_slug|None, axis, encodes_tool, encodes_endpoint, engine_op, source, safety, synonyms)
M, O, C = "MECHANISM", "OBJECTIVE", "COMPOSITE"
R, B5, ST = "RECIPEDB_S2", "MASTER_PROMPT_B05_ESCAPE", "STANDARD_CULINARY"
T, MR, SP, RS, TR, DI = "TRANSFORM", "MERGE", "SPLIT", "RESERVE", "TRANSFER", "DISCARD"
P = {
    # thermal — wet
    "boil": ("THERMAL_WET", None, M, "", "", T, R, "", ""),
    "simmer": ("THERMAL_WET", None, M, "", "", T, R, "", ""),
    "poach": ("THERMAL_WET", None, M, "", "", T, R, "", ""),
    "blanch": ("THERMAL_WET", None, M, "", "", T, R, "", ""),
    "parboil": ("THERMAL_WET", "boil", M, "", "", T, R, "", ""),
    "steam": ("THERMAL_WET", None, M, "", "", T, R, "", ""),
    "stew": ("THERMAL_WET", None, M, "", "", T, R, "", ""),
    "braise": ("THERMAL_WET", None, C, "", "", T, R, "", ""),
    "scald": ("THERMAL_WET", None, O, "", "yes", T, R, "", ""),
    "deglaze": ("THERMAL_WET", None, C, "", "", MR, R, "", ""),
    "sterilize": ("THERMAL_WET", None, O, "", "yes", T, R, "yes", ""),
    "can": ("THERMAL_WET", None, C, "sealed container", "", T, ST, "yes", "canning|canned"),
    "pressure-cook": ("THERMAL_WET", None, C, "pressure cooker", "", T, B5, "yes", ""),
    "sous-vide": ("THERMAL_WET", None, C, "water bath + sealed bag", "", T, B5, "yes", ""),
    # thermal — dry
    "bake": ("THERMAL_DRY", None, M, "", "", T, R, "", ""),
    "roast": ("THERMAL_DRY", None, M, "", "", T, R, "", ""),
    "broil": ("THERMAL_DRY", None, M, "", "", T, R, "", ""),
    "grill": ("THERMAL_DRY", None, M, "grill", "", T, ST, "", ""),
    "barbecue": ("THERMAL_DRY", "grill", M, "barbecue", "", T, R, "", ""),
    "griddle": ("THERMAL_DRY", None, M, "griddle", "", T, R, "", ""),
    "toast": ("THERMAL_DRY", None, O, "", "yes", T, R, "", ""),
    "char": ("THERMAL_DRY", None, O, "", "yes", T, R, "", ""),
    "air-fry": ("THERMAL_DRY", None, M, "air fryer", "", T, B5, "", ""),
    # thermal — fat
    "fry": ("THERMAL_FAT", None, M, "", "", T, R, "yes", ""),
    "deep-fry": ("THERMAL_FAT", "fry", M, "", "", T, ST, "yes", ""),
    "pan-fry": ("THERMAL_FAT", "fry", M, "pan", "", T, R, "yes", ""),
    "stir-fry": ("THERMAL_FAT", "fry", C, "", "", T, R, "yes", ""),
    "saute": ("THERMAL_FAT", None, M, "", "", T, R, "", "sauté"),
    "sweat": ("THERMAL_FAT", None, O, "", "yes", T, R, "", ""),
    "confit": ("THERMAL_FAT", None, C, "", "", T, B5, "yes", ""),
    "temper-spices": ("THERMAL_FAT", None, M, "", "", MR, B5, "",
                      "tadka|tarka|chhaunk|baghar|tempering (spices)"),
    "bloom-spices": ("THERMAL_FAT", None, M, "", "", T, B5, "", "blooming (spices in fat)"),
    "bhuno": ("THERMAL_FAT", None, O, "", "yes", T, B5, "", "bhunao|bhunna"),
    # thermal — general / endpoint-defined
    "heat": ("THERMAL_GENERAL", None, M, "", "", T, R, "", ""),
    "cook": ("THERMAL_GENERAL", None, M, "", "", T, R, "", ""),
    "warm": ("THERMAL_GENERAL", None, M, "", "", T, R, "", ""),
    "reheat": ("THERMAL_GENERAL", None, M, "", "", T, R, "yes", ""),
    "melt": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", ""),
    "caramelize": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", "caramelise"),
    "reduce-liquid": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", "reduce (a liquid)"),
    "evaporate": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", ""),
    "thicken": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", ""),
    "soften": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", ""),
    "wilt": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", ""),
    "sear": ("THERMAL_GENERAL", None, O, "", "yes", T, R, "", ""),
    "brown": ("THERMAL_GENERAL", None, O, "", "yes", T, ST, "", "browned|brwn"),
    "scramble": ("THERMAL_GENERAL", None, C, "", "", T, R, "", ""),
    "flambe": ("THERMAL_GENERAL", None, C, "", "", T, B5, "yes", "flambé"),
    "dum": ("THERMAL_GENERAL", None, C, "sealed pot", "", T, B5, "", "dum pukht"),
    "temper-chocolate": ("THERMAL_GENERAL", None, O, "", "yes", T, B5, "",
                         "tempering (chocolate)"),
    "microwave": ("THERMAL_DIELECTRIC", None, M, "microwave oven", "", T, B5, "yes", ""),
    "smoke": ("SMOKE", None, M, "", "", T, R, "yes", ""),
    # cold
    "cool": ("COLD", None, M, "", "", T, R, "", ""),
    "chill": ("COLD", None, M, "", "", T, R, "", ""),
    "refrigerate": ("COLD", None, M, "refrigerator", "", T, R, "", ""),
    "freeze": ("COLD", None, M, "freezer", "", T, B5, "", ""),
    "thaw": ("COLD", None, M, "", "", T, R, "yes", "defrost"),
    # mechanical
    "cut": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "chop": ("SIZE_REDUCTION", "cut", M, "", "", T, R, "", ""),
    "dice": ("SIZE_REDUCTION", "cut", M, "", "", T, R, "", ""),
    "mince": ("SIZE_REDUCTION", "cut", M, "", "", T, R, "", ""),
    "slice": ("SIZE_REDUCTION", "cut", M, "", "", T, R, "", ""),
    "carve": ("SIZE_REDUCTION", "cut", M, "", "", T, R, "", ""),
    "shred": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "grate": ("SIZE_REDUCTION", None, M, "grater", "", T, R, "", ""),
    "grind": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "crush": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "mash": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "puree": ("SIZE_REDUCTION", None, O, "", "yes", T, R, "", "purée"),
    "crumble": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "flake": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "tear": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "break": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "muddle": ("SIZE_REDUCTION", None, M, "", "", T, R, "", ""),
    "peel": ("SURFACE_REMOVAL", None, M, "", "", T, R, "", ""),
    "trim": ("SURFACE_REMOVAL", None, M, "", "", T, R, "", ""),
    "zest": ("SURFACE_REMOVAL", None, M, "", "", SP, R, "", ""),
    "devein": ("SURFACE_REMOVAL", None, M, "", "", T, R, "", ""),
    "strip": ("SURFACE_REMOVAL", None, M, "", "", SP, R, "", ""),
    "scrape": ("SURFACE_REMOVAL", None, M, "", "", T, R, "", ""),
    "pierce": ("PIERCE_SCORE", None, M, "", "", T, R, "", "poke"),
    "prick": ("PIERCE_SCORE", None, M, "", "", T, R, "", ""),
    "slit": ("PIERCE_SCORE", None, M, "", "", T, R, "", ""),
    "score": ("PIERCE_SCORE", None, M, "", "", T, ST, "", "slash"),
    "mix": ("MIXING", None, M, "", "", MR, R, "", ""),
    "stir": ("MIXING", None, M, "", "", T, R, "", ""),
    "combine": ("MIXING", None, M, "", "", MR, R, "", ""),
    "beat": ("MIXING", None, M, "", "", T, R, "", ""),
    "whisk": ("MIXING", None, M, "whisk", "", T, R, "", ""),
    "whip": ("MIXING", None, O, "", "yes", T, R, "", ""),
    "fold": ("MIXING", None, M, "", "", MR, R, "", ""),
    "cream": ("MIXING", None, O, "", "yes", MR, R, "", ""),
    "toss": ("MIXING", None, M, "", "", MR, R, "", ""),
    "knead": ("MIXING", None, M, "", "", T, R, "", ""),
    "swirl": ("MIXING", None, M, "", "", T, R, "", ""),
    "shake": ("MIXING", None, M, "", "", T, R, "", ""),
    "blend": ("MIXING", None, M, "", "", MR, R, "", "whirl|blitz"),
    "dissolve": ("MIXING", None, O, "", "yes", MR, R, "", ""),
    "drain": ("SEPARATION", None, M, "", "", SP, R, "", "drip"),
    "strain": ("SEPARATION", None, M, "", "", SP, R, "", ""),
    "sift": ("SEPARATION", None, M, "sifter", "", T, R, "", ""),
    "skim": ("SEPARATION", None, M, "", "", SP, R, "", ""),
    "squeeze": ("SEPARATION", None, M, "", "", SP, R, "", ""),
    "press": ("SEPARATION", None, M, "", "", T, R, "", ""),
    "shape": ("SHAPING", None, M, "", "", T, R, "", ""),
    "roll": ("SHAPING", None, M, "", "", T, R, "", ""),
    "flatten": ("SHAPING", None, M, "", "", T, R, "", ""),
    "stretch": ("SHAPING", None, M, "", "", T, R, "", ""),
    "twist": ("SHAPING", None, M, "", "", T, R, "", ""),
    "crimp": ("SHAPING", None, M, "", "", T, R, "", ""),
    "smooth": ("SHAPING", None, M, "", "", T, R, "", ""),
    "deflate": ("SHAPING", None, M, "", "", T, R, "", "punch down"),
    "flip": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "invert": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "rotate": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "tilt": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "unmold": ("MANIPULATION", None, M, "", "", TR, R, "", ""),
    "unroll": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "unfold": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "pull": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    "push": ("MANIPULATION", None, M, "", "", T, R, "", ""),
    # surface application
    "coat": ("COATING", None, M, "", "", MR, R, "", ""),
    "dredge": ("COATING", None, M, "", "", MR, R, "", ""),
    "dust": ("COATING", None, M, "", "", MR, R, "", ""),
    "sprinkle": ("COATING", None, M, "", "", MR, R, "", "scatter"),
    "drizzle": ("COATING", None, M, "", "", MR, R, "", ""),
    "brush": ("COATING", None, M, "brush", "", MR, R, "", ""),
    "baste": ("COATING", None, C, "", "", MR, R, "", ""),
    "grease": ("COATING", None, M, "", "", T, R, "", ""),
    "spread": ("COATING", None, M, "", "", MR, R, "", "smear|slather"),
    "rub": ("COATING", None, M, "", "", MR, R, "", ""),
    "glaze": ("COATING", None, M, "", "", MR, R, "", ""),
    "frost": ("COATING", None, M, "", "", MR, R, "", ""),
    "spray": ("COATING", None, M, "", "", MR, R, "", ""),
    "dip": ("COATING", None, M, "", "", MR, R, "", ""),
    "moisten": ("COATING", None, M, "", "", MR, R, "", ""),
    "massage": ("COATING", None, M, "", "", T, R, "", ""),
    "top": ("COATING", None, M, "", "", MR, R, "", ""),
    "season": ("SEASON_FLAVOUR", None, M, "", "", MR, R, "", ""),
    "sweeten": ("SEASON_FLAVOUR", None, M, "", "", MR, R, "", ""),
    "dress": ("SEASON_FLAVOUR", None, M, "", "", MR, R, "", ""),
    # assembly / transfer / portioning / serving
    "assemble": ("ASSEMBLY", None, M, "", "", MR, R, "", ""),
    "stack": ("ASSEMBLY", None, M, "", "", MR, R, "", ""),
    "stuff": ("ASSEMBLY", None, M, "", "", MR, R, "", ""),
    "fill": ("ASSEMBLY", None, M, "", "", MR, R, "", ""),
    "thread": ("ASSEMBLY", None, M, "skewer", "", MR, R, "", ""),
    "tie": ("ASSEMBLY", None, M, "string", "", T, R, "", ""),
    "tuck": ("ASSEMBLY", None, M, "", "", T, R, "", ""),
    "mound": ("ASSEMBLY", None, M, "", "", T, R, "", ""),
    "arrange": ("ASSEMBLY", None, M, "", "", T, R, "", ""),
    "decorate": ("ASSEMBLY", None, M, "", "", MR, R, "", ""),
    "garnish": ("ASSEMBLY", None, M, "", "", MR, R, "", ""),
    "insert": ("ASSEMBLY", None, M, "", "", T, R, "", ""),
    "add": ("TRANSFER", None, M, "", "", MR, R, "", "throw in|dump"),
    "place": ("TRANSFER", None, M, "", "", TR, R, "", "put"),
    "pour": ("TRANSFER", None, M, "", "", TR, R, "", "stream in"),
    "transfer": ("TRANSFER", None, M, "", "", TR, R, "", "move"),
    "remove": ("TRANSFER", None, M, "", "", TR, R, "", ""),
    "ladle": ("TRANSFER", None, M, "ladle", "", TR, R, "", ""),
    "scoop": ("TRANSFER", None, M, "", "", TR, R, "", ""),
    "drop": ("TRANSFER", None, M, "", "", TR, R, "", ""),
    "distribute": ("TRANSFER", None, M, "", "", TR, R, "", ""),
    "immerse": ("TRANSFER", None, M, "", "", TR, R, "", "submerge"),
    "dollop": ("TRANSFER", None, M, "", "", TR, R, "", ""),
    "discard": ("TRANSFER", None, M, "", "", DI, ST, "", ""),
    "divide": ("PORTION_SPLIT", None, M, "", "", SP, R, "", ""),
    "split": ("PORTION_SPLIT", None, M, "", "", SP, R, "", ""),
    "separate-portions": ("PORTION_SPLIT", None, M, "", "", SP, R, "", "separate (eggs, mixtures)"),
    "reserve": ("PORTION_SPLIT", None, M, "", "", RS, R, "", "save|set aside"),
    "serve": ("SERVE", None, M, "", "", TR, R, "", ""),
    # container / tool state / storage
    "cover": ("CONTAINER", None, M, "lid", "", T, R, "", ""),
    "uncover": ("CONTAINER", None, M, "lid", "", T, R, "", ""),
    "seal": ("CONTAINER", None, M, "", "", T, R, "", ""),
    "open": ("CONTAINER", None, M, "", "", T, R, "", ""),
    "wrap": ("CONTAINER", None, M, "", "", T, R, "", ""),
    "unwrap": ("CONTAINER", None, M, "", "", T, R, "", ""),
    "pack": ("CONTAINER", None, M, "", "", TR, R, "", ""),
    "preheat": ("TOOL_STATE", None, O, "oven/pan", "yes", T, R, "", "pre-heat"),
    "adjust-heat": ("TOOL_STATE", None, M, "hob/oven", "", T, ST, "", "raise heat|reduce heat|lower heat"),
    "store": ("STORAGE", None, M, "", "", TR, R, "yes", ""),
    # chemical / biological
    "marinate": ("CHEMICAL", None, M, "", "", MR, R, "", ""),
    "cure": ("CHEMICAL", None, M, "", "", T, B5, "yes", ""),
    "brine": ("CHEMICAL", None, M, "", "", T, B5, "yes", ""),
    "nixtamalize": ("CHEMICAL", None, C, "", "", T, B5, "", "nixtamalization"),
    "curdle-milk": ("CHEMICAL", None, O, "", "yes", SP, R, "", "curdle (deliberate, e.g. paneer)"),
    "temper-eggs": ("MIXING", None, C, "", "", MR, B5, "", "tempering (eggs)"),
    "proof": ("BIOLOGICAL", None, O, "", "yes", T, B5, "", "prove|let rise"),
    "sprout": ("BIOLOGICAL", None, M, "", "", T, R, "", "sprouting"),
    "ferment": ("BIOLOGICAL", None, M, "", "", T, ST, "yes", ""),
    "bloom-gelatin": ("LIQUID_HOLD", None, O, "", "yes", T, B5, "", "blooming (gelatin)"),
    # rest / hold / liquid hold
    "rest": ("REST_HOLD", None, M, "", "", T, R, "", "stand|sit|settle|wait"),
    "hold": ("REST_HOLD", None, M, "", "", T, R, "yes", ""),
    "soak": ("LIQUID_HOLD", None, M, "", "", T, R, "", ""),
    "steep": ("LIQUID_HOLD", None, M, "", "", T, R, "", ""),
    # hygiene / prep
    "wash": ("CLEAN_PREP", None, M, "", "", T, R, "", ""),
    "rinse": ("CLEAN_PREP", None, M, "", "", T, R, "", ""),
    "clean": ("CLEAN_PREP", None, M, "", "", T, R, "", ""),
    "scrub": ("CLEAN_PREP", None, M, "", "", T, R, "", ""),
    "wipe": ("CLEAN_PREP", None, M, "", "", T, R, "", ""),
    "pat-dry": ("CLEAN_PREP", None, O, "", "yes", T, R, "", "pat|blot"),
    "dehydrate": ("CLEAN_PREP", None, O, "", "yes", T, ST, "", "dry (preservation)"),
    "pick-over": ("CLEAN_PREP", None, M, "", "", T, R, "", "pick|sort"),
}

# --------------------------------------------- RecipeDB term classification
# class codes
PR, IN, SY, EN, FO, TL, NG, PC, NP, QT, AM = (
    "PROCESS", "INFLECTION", "SYNONYM", "ENDPOINT_STATE", "FORM_DESCRIPTOR", "TOOL",
    "INGREDIENT_OR_INTERMEDIATE", "PROCEDURAL_CONTROL", "NON_PROCESS", "QUANTITY_TERM",
    "AMBIGUOUS")
# term: (class, target_slug or "", note). For AMBIGUOUS, note lists senses as "a | b".
TERM = {
    "add": (PR, "add", ""), "heat": (PR, "heat", ""), "cook": (PR, "cook", ""),
    "stir": (PR, "stir", ""), "place": (PR, "place", ""), "mix": (PR, "mix", ""),
    "cover": (PR, "cover", ""), "remove": (PR, "remove", ""), "serve": (PR, "serve", ""),
    "boil": (PR, "boil", ""), "simmer": (PR, "simmer", ""), "bake": (PR, "bake", ""),
    "stirring": (IN, "stir", ""), "sprinkle": (PR, "sprinkle", ""), "cool": (PR, "cool", ""),
    "preheat": (PR, "preheat", ""), "cut": (PR, "cut", ""), "combine": (PR, "combine", ""),
    "drain": (PR, "drain", ""), "pour": (PR, "pour", ""),
    "set": (AM, "", "set aside → reserve | set (gel/firm) → endpoint | set oven → adjust-heat"),
    "season": (PR, "season", ""), "beat": (PR, "beat", ""), "spread": (PR, "spread", ""),
    "transfer": (PR, "transfer", ""), "whisk": (PR, "whisk", ""), "smooth": (PR, "smooth", ""),
    "top": (PR, "top", ""), "blend": (PR, "blend", "may imply a blender (size reduction)"),
    "refrigerate": (PR, "refrigerate", ""), "put": (SY, "place", ""), "fry": (PR, "fry", ""),
    "melt": (PR, "melt", ""), "fold": (PR, "fold", ""),
    "reduce": (AM, "", "reduce a liquid → reduce-liquid | reduce heat → adjust-heat"),
    "dry": (AM, "", "pat dry → pat-dry | dry/dehydrate (preservation) → dehydrate"),
    "slice": (PR, "slice", ""), "coat": (PR, "coat", ""),
    "cream": (PR, "cream", "noun sense (dairy cream) is an ingredient"),
    "chop": (PR, "chop", ""), "taste": (PC, "", "sensory check, e.g. 'taste and adjust'"),
    "peel": (PR, "peel", ""), "garnish": (PR, "garnish", ""), "brush": (PR, "brush", ""),
    "press": (PR, "press", "also 'press into a tin' (shaping)"), "drizzle": (PR, "drizzle", ""),
    "roll": (PR, "roll", "also 'roll in sugar' (coating)"), "grease": (PR, "grease", ""),
    "chill": (PR, "chill", ""), "saute": (PR, "saute", ""),
    "prepare": (PC, "", "generic ('prepare the sauce'); refers to a sub-recipe"),
    "knead": (PR, "knead", ""), "stand": (SY, "rest", "'let stand'"),
    "process": (AM, "", "process in a food processor → blend | generic/industrial processing"),
    "divide": (PR, "divide", ""), "toss": (PR, "toss", ""), "strain": (PR, "strain", ""),
    "puree": (PR, "puree", ""), "rinse": (PR, "rinse", ""), "spray": (PR, "spray", ""),
    "seasoning": (AM, "", "gerund of season → season | noun: a seasoning (ingredient)"),
    "wash": (PR, "wash", ""), "arrange": (PR, "arrange", ""), "store": (PR, "store", ""),
    "sift": (PR, "sift", ""), "seal": (PR, "seal", ""),
    "rise": (SY, "proof", "'let rise' instructs proofing; 'risen' is the endpoint"),
    "note": (NP, "", "recipe annotation ('Note: …')"), "shape": (PR, "shape", ""),
    "wrap": (PR, "wrap", "also 'wrap around' (assembly)"), "soak": (PR, "soak", ""),
    "fill": (PR, "fill", ""), "roast": (PR, "roast", ""), "broil": (PR, "broil", ""),
    "stir-fry": (PR, "stir-fry", ""), "dust": (PR, "dust", ""), "drop": (PR, "drop", ""),
    "dip": (PR, "dip", ""), "marinate": (PR, "marinate", ""), "ladle": (PR, "ladle", ""),
    "scoop": (PR, "scoop", ""), "dice": (PR, "dice", ""), "mash": (PR, "mash", ""),
    "uncover": (PR, "uncover", ""), "dissolve": (PR, "dissolve", ""),
    "separate": (AM, "", "separate eggs/portions → separate-portions | a sauce separating (defect endpoint)"),
    "dressing": (AM, "", "noun: salad dressing (intermediate) | gerund of dress → dress"),
    "uncovered": (EN, "uncover", "vessel condition: lid off"),
    "pat": (SY, "pat-dry", "also 'pat into shape' (shaping)"), "shake": (PR, "shake", ""),
    "turn": (AM, "", "turn over → flip | turn off/down heat → adjust-heat | turn out → unmold"),
    "take": (NP, "", "generic verb"), "break": (PR, "break", "'break eggs' = crack open"),
    "grind": (PR, "grind", ""), "toast": (PR, "toast", ""),
    "evaporated": (FO, "", "'evaporated milk' (ingredient form); also endpoint of evaporate"),
    "steam": (PR, "steam", ""), "squeeze": (PR, "squeeze", ""), "crumble": (PR, "crumble", ""),
    "scrape": (PR, "scrape", ""), "shred": (PR, "shred", ""), "trim": (PR, "trim", ""),
    "scatter": (SY, "sprinkle", ""), "reheat": (PR, "reheat", ""), "flip": (PR, "flip", ""),
    "crush": (PR, "crush", ""), "dredge": (PR, "dredge", ""), "clean": (PR, "clean", ""),
    "check": (PC, "", "doneness/consistency check"), "stuff": (PR, "stuff", ""),
    "grate": (PR, "grate", ""), "whip": (PR, "whip", ""),
    "bubbling": (EN, "boil", "visual endpoint: bubbling"), "punch": (SY, "deflate", "'punch down' dough"),
    "warm": (PR, "warm", ""), "skim": (PR, "skim", ""),
    "smoking": (AM, "", "smoking (process) → smoke | 'until smoking' (oil endpoint; safety-relevant)"),
    "thread": (PR, "thread", ""), "wipe": (PR, "wipe", ""), "decorate": (PR, "decorate", ""),
    "marinade": (AM, "", "noun: a marinade (intermediate) | variant of marinate → marinate"),
    "zest": (PR, "zest", ""),
    "handle": (AM, "", "'handle gently' (manipulation) | noun: tool part"),
    "rub": (PR, "rub", ""), "flatten": (PR, "flatten", ""), "pull": (PR, "pull", "'pulled pork' = shred"),
    "push": (PR, "push", ""), "reserve": (PR, "reserve", ""), "mince": (PR, "mince", ""),
    "prick": (PR, "prick", ""), "open": (PR, "open", ""), "pre-heat": (IN, "preheat", ""),
    "butter": (AM, "", "verb: butter a tin → grease | noun: ingredient"),
    "sear": (PR, "sear", ""), "measure": (PC, "", "measuring out quantities"),
    "pressure": (AM, "", "pressure-cook → pressure-cook | noun (pressure level/whistles)"),
    "wok": (TL, "", "tool: wok"), "split": (PR, "split", ""), "rest": (PR, "rest", ""),
    "baste": (PR, "baste", ""), "bubble": (EN, "boil", "visual endpoint: bubbles"),
    "burn": (EN, "cook", "defect endpoint: burnt (diagnosis/recovery relevant)"),
    "skin": (AM, "", "verb: remove skin → peel | noun: skin of fish/poultry | 'a skin forms' (state)"),
    "pop": (AM, "", "'until kernels pop' (endpoint) | 'pop in the oven' (colloquial transfer)"),
    "squash": (AM, "", "verb: squash → crush | noun: the vegetable"),
    "move": (SY, "transfer", ""), "soften": (PR, "soften", "thermal or at room temperature"),
    "blanch": (PR, "blanch", ""), "raise": (SY, "adjust-heat", "'raise the heat'"),
    "deglaze": (PR, "deglaze", ""), "pierce": (PR, "pierce", ""),
    "absorbed": (EN, "simmer", "endpoint: liquid absorbed"), "stream": (SY, "pour", "'stream in' while mixing"),
    "assemble": (PR, "assemble", ""), "stack": (PR, "stack", ""),
    "ice": (AM, "", "ice a cake → frost | chill on ice → chill | noun: ice (ingredient)"),
    "moisten": (PR, "moisten", ""), "replace": (NP, "", "'replace the lid' etc."),
    "pack": (AM, "", "pack into a jar → pack | 'packed' (quantity convention, e.g. packed brown sugar)"),
    "foil": (TL, "", "material/tool: foil"), "tear": (PR, "tear", ""),
    "square": (FO, "", "shape/form ('cut into squares')"),
    "caramelized": (EN, "caramelize", "endpoint or form ('caramelized onions')"),
    "smoke": (PR, "smoke", ""), "throw": (SY, "add", "'throw in'"),
    "yield": (NP, "", "recipe yield"), "save": (SY, "reserve", ""),
    "pick": (SY, "pick-over", "also 'pick leaves'"), "tie": (PR, "tie", ""),
    "invert": (PR, "invert", ""), "swirl": (PR, "swirl", ""),
    "sieve": (AM, "", "dry ingredients → sift | liquids → strain"),
    "hold": (PR, "hold", "holding temperature is food-safety relevant"),
    "poke": (SY, "pierce", ""), "charred": (EN, "char", "endpoint"),
    "floured": (FO, "", "'floured surface/tin' (form/condition)"),
    "sizzle": (EN, "fry", "sensory endpoint: sizzling"),
    "wet": (AM, "", "'wet ingredients' (category) | 'wet your hands' (prep)"),
    "mound": (PR, "mound", ""), "dump": (SY, "add", ""), "frost": (PR, "frost", ""),
    "test": (PC, "", "doneness test (skewer, finger)"), "distribute": (PR, "distribute", ""),
    "thaw": (PR, "thaw", ""), "wait": (SY, "rest", "'wait N minutes'"), "sit": (SY, "rest", ""),
    "glaze": (PR, "glaze", ""), "scrub": (PR, "scrub", ""), "carve": (PR, "carve", ""),
    "drip": (SY, "drain", ""), "stew": (PR, "stew", ""),
    "overcook": (EN, "cook", "defect endpoint (diagnosis/recovery relevant)"),
    "start": (PC, "", ""), "style": (NP, "", ""), "select": (NP, "", ""),
    "griddle": (PR, "griddle", ""), "unroll": (PR, "unroll", ""), "insert": (PR, "insert", "incl. inserting a thermometer"),
    "sweat": (PR, "sweat", ""), "tuck": (PR, "tuck", ""),
    "meld": (EN, "rest", "endpoint: flavours meld"), "unwrap": (PR, "unwrap", ""),
    "scorching": (EN, "cook", "defect endpoint"), "caramelize": (PR, "caramelize", ""),
    "defrost": (SY, "thaw", ""), "splutter": (EN, "fry", "sensory state: spluttering"),
    "scramble": (PR, "scramble", ""), "thicken": (PR, "thicken", ""),
    "scald": (PR, "scald", "also 'scald' as injury (safety)"), "twist": (PR, "twist", ""),
    "barbecue": (PR, "barbecue", ""), "unmold": (PR, "unmold", ""), "poach": (PR, "poach", ""),
    "presentation": (NP, "", ""), "dress": (PR, "dress", ""), "smear": (SY, "spread", ""),
    "overmix": (EN, "mix", "defect endpoint (overmixed)"),
    "crockpot": (TL, "", "tool: slow cooker (implies slow cooking)"), "smash": (SY, "crush", ""),
    "devein": (PR, "devein", ""), "moist": (EN, "", "state: moist"),
    "powdered": (FO, "", "'powdered sugar' (form)"), "evaporate": (PR, "evaporate", ""),
    "flake": (PR, "flake", ""), "roux": (NG, "", "intermediate (fat + flour)"),
    "slit": (PR, "slit", ""),
    "dripping": (AM, "", "noun: drippings (intermediate) | state: dripping"),
    "repeat": (PC, "", ""), "parboil": (PR, "parboil", ""), "sprout": (PR, "sprout", ""),
    "unfold": (PR, "unfold", ""), "rising": (IN, "proof", "gerund of rise"),
    "stretch": (PR, "stretch", ""), "steep": (PR, "steep", ""),
    "condensed": (FO, "", "'condensed milk' (form)"), "braise": (PR, "braise", ""),
    "whirl": (SY, "blend", "'whirl in a blender'"), "minced": (FO, "mince", "form ('minced garlic')"),
    "tilt": (PR, "tilt", ""),
    "lard": (AM, "", "verb: larding meat (inserting fat) | noun: ingredient"),
    "deflate": (PR, "deflate", ""), "strip": (PR, "strip", ""), "sort": (SY, "pick-over", ""),
    "dollop": (PR, "dollop", "also a verbal quantity ('a dollop')"),
    "submerge": (SY, "immerse", ""), "rotate": (PR, "rotate", ""),
    "splash": (AM, "", "verbal quantity ('a splash of') | verb"),
    "pan-fry": (PR, "pan-fry", ""), "stop": (PC, "", ""),
    "curdle": (AM, "", "deliberate (paneer, chhena) → curdle-milk | defect endpoint (split sauce)"),
    "char": (PR, "char", ""), "freezing": (IN, "freeze", ""), "slash": (SY, "score", ""),
    "muddle": (PR, "muddle", ""), "crimp": (PR, "crimp", ""), "sterilize": (PR, "sterilize", ""),
    "blot": (SY, "pat-dry", ""), "flavoring": (NG, "", "noun: a flavouring (ingredient)"),
    "foam": (EN, "", "state: foamy"), "touch": (PC, "", "doneness test by touch"),
    "snap": (SY, "break", "'snap the ends'"), "dash": (QT, "", "verbal quantity ('a dash')"),
    "immerse": (PR, "immerse", ""), "settle": (SY, "rest", "'let settle'"),
    "blitz": (SY, "blend", "colloquial; implies a blender"), "massage": (PR, "massage", ""),
    "sweeten": (PR, "sweeten", ""), "wilt": (PR, "wilt", ""), "slather": (SY, "spread", ""),
    "mould": (AM, "", "verb: mould/shape → shape | noun: fungus (food-safety relevant)"),
}

CLASSES = {PR, IN, SY, EN, FO, TL, NG, PC, NP, QT, AM}
ESCAPE = ["sous-vide", "smoke", "pressure-cook", "air-fry", "microwave", "nixtamalize",
          "sprout", "cure", "brine", "temper-spices", "dum", "bhuno", "bloom-spices",
          "bloom-gelatin", "flambe", "confit", "freeze", "chill", "rest", "proof"]
VERIFIED_XREF = {"cook": ("FOODON_03450002 food cooking", "RS-05-01"),
                 "blanch": ("FOODON:03470175 food blanching", "RS-05-01")}
ENGINE_OPS = {"TRANSFORM", "MERGE", "SPLIT", "RESERVE", "TRANSFER", "DISCARD"}


def main() -> int:
    terms = [l.strip() for l in SEED.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    problems = []

    # -- seed coverage
    if len(terms) != 270 or len(set(terms)) != 270:
        problems.append(f"seed has {len(terms)} terms ({len(set(terms))} unique), expected 270")
    missing = [t for t in terms if t not in TERM]
    extra = [t for t in TERM if t not in terms]
    if missing:
        problems.append(f"RecipeDB terms without a classification: {missing}")
    if extra:
        problems.append(f"classified terms not in the seed: {extra}")

    # -- process records
    for slug, rec in P.items():
        fam, parent, axis, _tool, _end, op, src, _saf, _syn = rec
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            problems.append(f"bad slug {slug}")
        if fam not in FAMILY_GROUP:
            problems.append(f"{slug}: unknown family {fam}")
        if parent and parent not in P:
            problems.append(f"{slug}: parent {parent} missing")
        if axis not in (M, O, C):
            problems.append(f"{slug}: bad axis {axis}")
        if op not in ENGINE_OPS:
            problems.append(f"{slug}: bad engine op {op}")
    for slug in P:                       # no parent cycles
        seen, cur = set(), slug
        while cur:
            if cur in seen:
                problems.append(f"parent cycle at {slug}")
                break
            seen.add(cur)
            cur = P[cur][1]
    for e in ESCAPE:
        if e not in P:
            problems.append(f"escape process missing: {e}")

    # -- term map targets
    for t, (cls, target, note) in TERM.items():
        if cls not in CLASSES:
            problems.append(f"{t}: bad class {cls}")
        if cls in (PR, IN, SY) and target not in P:
            problems.append(f"{t}: {cls} target {target!r} is not a PROC")
        if cls == PR and target != t and t in P:
            problems.append(f"{t}: PROCESS must target itself")
        if cls == AM and note.count("|") < 1:
            problems.append(f"{t}: AMBIGUOUS needs ≥2 senses separated by '|'")
        for link in re.findall(r"→ ([a-z0-9-]+)", note):
            if link not in P and link not in ("endpoint",):
                problems.append(f"{t}: sense links to unknown PROC {link!r}")

    # -- write
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "process_families_v0.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["family_id", "family", "group", "scope_note", "status"])
        for fam, grp in FAMILY_GROUP.items():
            w.writerow([f"PROC-FAM-{fam}", fam, grp, FAMILY_NOTE[fam], "PROPOSED"])

    seed_set = set(terms)
    for slug in list(P):
        rec = list(P[slug])
        if rec[6] == R and slug not in seed_set:
            rec[6] = "RECIPEDB_S2_SENSE"      # a disambiguated sense of an ambiguous S2 term
            P[slug] = tuple(rec)

    rdb_terms_for = {}
    for t, (cls, target, _n) in TERM.items():
        if cls in (PR, IN, SY):
            rdb_terms_for.setdefault(target, []).append(t)
    with (OUT / "proc_v0.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["proc_id", "label", "family_id", "family_group", "parent_id", "axis",
                    "encodes_tool", "encodes_endpoint", "engine_op_hint", "synonyms",
                    "recipedb_surface_terms", "source", "safety_review_required",
                    "parameters", "mechanism_links", "xref_foodon", "xref_foodex2",
                    "xref_langual", "status"])
        for slug in sorted(P):
            fam, parent, axis, tool, end, op, src, saf, syn = P[slug]
            xf = VERIFIED_XREF.get(slug)
            w.writerow([f"PROC-{slug}", slug.replace("-", " "), f"PROC-FAM-{fam}",
                        FAMILY_GROUP[fam], f"PROC-{parent}" if parent else "", axis,
                        tool, "yes" if end else "", op, syn,
                        "|".join(sorted(rdb_terms_for.get(slug, []))), src,
                        "yes" if saf else "", "UNKNOWN", "UNKNOWN",
                        f"{xf[0]} [V {xf[1]}]" if xf else "UNRESOLVED_EXTERNAL",
                        "UNRESOLVED_EXTERNAL", "UNRESOLVED_EXTERNAL", "PROPOSED"])

    with (OUT / "recipedb_term_map_v0.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["order_in_table_s2", "recipedb_term", "term_class", "target_proc_id",
                    "senses_or_note", "status", "proposed_by"])
        for k, t in enumerate(terms, 1):
            if t not in TERM:
                continue
            cls, target, note = TERM[t]
            tgt = f"PROC-{target}" if (cls in (PR, IN, SY) or (cls in (EN, FO) and target in P)) and target else ""
            w.writerow([k, t, cls, tgt, note, "PROPOSED", "claude (needs SX-05-02 human audit)"])

    # -- report
    cc = Counter(TERM[t][0] for t in terms if t in TERM)
    mapped = sum(cc[c] for c in (PR, IN, SY))
    src = Counter(v[6] for v in P.values())
    fam = Counter(v[0] for v in P.values())
    print(f"seed terms: {len(terms)}  |  PROC records: {len(P)}  |  families: {len(FAMILY_GROUP)}")
    print("term classes: " + ", ".join(f"{k}={cc[k]}" for k in sorted(cc)))
    print(f"terms resolving to a PROC (process/inflection/synonym): {mapped}/{len(terms)} "
          f"= {mapped/len(terms):.1%}; ambiguous (need context): {cc[AM]}")
    print("PROC sources: " + ", ".join(f"{k}={v}" for k, v in sorted(src.items())))
    print(f"escape processes present: {sum(e in P for e in ESCAPE)}/{len(ESCAPE)}; "
          f"safety-review flags: {sum(1 for v in P.values() if v[7])}")
    print("largest families: " + ", ".join(f"{k}={v}" for k, v in fam.most_common(6)))
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print("PASS: every RecipeDB term classified once; all targets, parents, families, ops valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
