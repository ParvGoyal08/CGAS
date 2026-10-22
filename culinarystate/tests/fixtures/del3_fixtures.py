r"""
Ten self-written fixture recipes for the DEL-3 state engine (WP-07).

The recipe texts are our own, written for these tests, so they carry no
third-party licence. Together they exercise every operation and every §233.5
relation: TRANSFORM, MERGE, SPLIT, RESERVE, DISCARD, RECOMBINE, TRANSFER,
SET_FIELD, OBSERVE, and the omitted-step candidate lifecycle.

IDs follow the three-identity rule (v4.0 AN1):
    ING-…     concept      ENTITY-…  physical lot      STATE-…  version (engine-made)
"""
from __future__ import annotations

from culinarystate.state_graph.model import (Amount, Belief, Event, NewLot, Op, Provenance,
                                             Quantity, Trajectory)


def A(raw, unit=None, value=None, lo=None, hi=None) -> Amount:
    return Amount(raw=raw, unit=unit, value=value, lo=lo, hi=hi)


def Q(a: Amount) -> Quantity:
    return Quantity.of(a)


def lot(eid, concept, label, q=None, fraction=None) -> NewLot:
    return NewLot(entity_id=eid, concept_id=concept, label=label, quantity=q, fraction=fraction)


def planned(field, value, eid, unit=None) -> Belief:
    return Belief(field, value, Trajectory.PLANNED, Provenance.EXPLICIT_SOURCE, eid, unit=unit)


def observed(field, value, eid) -> Belief:
    return Belief(field, value, Trajectory.OBSERVED_SESSION, Provenance.EXPLICIT_SOURCE, eid)


def predicted(field, value, eid) -> Belief:
    return Belief(field, value, Trajectory.PREDICTED, Provenance.MODEL_ESTIMATED, eid)


def E(eid, order, op, **kw) -> Event:
    return Event(event_id=eid, order=order, op=op, **kw)


# --------------------------------------------------------------------- F01
F01_TEXT = ("Melt 50 g butter. Reserve 1 tbsp of the melted butter. Cook 2 chopped garlic "
            "cloves in the rest until fragrant. Toss with 200 g cooked pasta and the "
            "reserved butter.")


def f01():
    return [
        E("EVT-F01-01", 1, Op.CREATE, outputs=(
            lot("ENTITY-F01-butter", "ING-butter", "butter", Q(A("50 g", "g", 50))),
            lot("ENTITY-F01-garlic", "ING-garlic", "garlic", Q(A("2 cloves", "clove", 2))),
            lot("ENTITY-F01-pasta", "ING-pasta", "cooked pasta", Q(A("200 g", "g", 200))))),
        E("EVT-F01-02", 2, Op.TRANSFORM, inputs=("ENTITY-F01-butter",), process_raw="melt",
          belief=planned("phase", "melted", "EVT-F01-02")),
        E("EVT-F01-03", 3, Op.RESERVE, inputs=("ENTITY-F01-butter",), outputs=(
            lot("ENTITY-F01-butter-res", "ING-butter", "reserved butter", Q(A("1 tbsp", "tbsp", 1))),
            lot("ENTITY-F01-butter-rest", "ING-butter", "rest of butter"))),
        E("EVT-F01-04", 4, Op.TRANSFORM, inputs=("ENTITY-F01-garlic",), process_raw="chop",
          belief=planned("form", "chopped", "EVT-F01-04")),
        E("EVT-F01-05", 5, Op.MERGE, inputs=("ENTITY-F01-garlic", "ENTITY-F01-butter-rest"),
          outputs=(lot("ENTITY-F01-garlic-butter", None, "garlic butter"),), process_raw="cook"),
        E("EVT-F01-06", 6, Op.SET_FIELD, inputs=("ENTITY-F01-garlic-butter",),
          belief=planned("aroma_endpoint", "fragrant", "EVT-F01-06")),
        E("EVT-F01-07", 7, Op.OBSERVE, inputs=("ENTITY-F01-butter-res",),
          belief=observed("phase", "solid", "EVT-F01-07")),
        E("EVT-F01-08", 8, Op.RECOMBINE,
          inputs=("ENTITY-F01-garlic-butter", "ENTITY-F01-pasta", "ENTITY-F01-butter-res"),
          outputs=(lot("ENTITY-F01-dish", None, "garlic butter pasta"),), process_raw="toss"),
    ]


# --------------------------------------------------------------------- F02
F02_TEXT = "Divide 500 g dough into 4 equal pieces."


def f02():
    return [
        E("EVT-F02-01", 1, Op.CREATE, outputs=(lot("ENTITY-F02-dough", "ING-dough", "dough",
                                                   Q(A("500 g", "g", 500))),)),
        E("EVT-F02-02", 2, Op.SPLIT, inputs=("ENTITY-F02-dough",), process_raw="divide",
          outputs=tuple(lot(f"ENTITY-F02-piece{k}", "ING-dough", f"piece {k}", fraction=0.25)
                        for k in range(1, 5))),
    ]


# --------------------------------------------------------------------- F03
F03_TEXT = ("Boil 300 g pasta in 2 L water. Drain, reserving 100 ml of the cooking water; "
            "discard the rest of the water.")


def f03():
    return [
        E("EVT-F03-01", 1, Op.CREATE, outputs=(
            lot("ENTITY-F03-pasta", "ING-pasta", "dry pasta", Q(A("300 g", "g", 300))),
            lot("ENTITY-F03-water", "ING-water", "water", Q(A("2 L", "L", 2))))),
        E("EVT-F03-02", 2, Op.MERGE, inputs=("ENTITY-F03-pasta", "ENTITY-F03-water"),
          outputs=(lot("ENTITY-F03-pot", None, "pasta in water"),), process_raw="boil"),
        E("EVT-F03-03", 3, Op.SPLIT, inputs=("ENTITY-F03-pot",), process_raw="drain", outputs=(
            lot("ENTITY-F03-cooked-pasta", "ING-pasta", "cooked pasta"),
            lot("ENTITY-F03-cooking-water", "ING-water", "cooking water"))),
        E("EVT-F03-04", 4, Op.RESERVE, inputs=("ENTITY-F03-cooking-water",), outputs=(
            lot("ENTITY-F03-water-res", "ING-water", "reserved cooking water",
                Q(A("100 ml", "ml", 100))),
            lot("ENTITY-F03-water-rest", "ING-water", "rest of cooking water"))),
        E("EVT-F03-05", 5, Op.DISCARD, inputs=("ENTITY-F03-water-rest",), process_raw="discard"),
    ]


# --------------------------------------------------------------------- F04
F04_TEXT = "Slice 2 onions and cook them in oil over medium heat until golden."


def f04():
    return [
        E("EVT-F04-01", 1, Op.CREATE, outputs=(lot("ENTITY-F04-onion", "ING-onion", "onions",
                                                   Q(A("2 onions", "onion", 2))),)),
        E("EVT-F04-02", 2, Op.TRANSFORM, inputs=("ENTITY-F04-onion",), process_raw="slice",
          belief=planned("form", "sliced", "EVT-F04-02")),
        # "medium heat" is qualitative: stored as a label, never as a temperature (v4.0 W2 rule 2)
        E("EVT-F04-03", 3, Op.TRANSFORM, inputs=("ENTITY-F04-onion",), process_raw="cook",
          belief=planned("heat_level", "medium", "EVT-F04-03")),
        E("EVT-F04-04", 4, Op.SET_FIELD, inputs=("ENTITY-F04-onion",),
          belief=planned("colour_endpoint", "golden", "EVT-F04-04")),
        E("EVT-F04-05", 5, Op.OBSERVE, inputs=("ENTITY-F04-onion",),
          belief=observed("colour_endpoint", "pale", "EVT-F04-05")),
        E("EVT-F04-06", 6, Op.SET_FIELD, inputs=("ENTITY-F04-onion",),
          belief=predicted("colour_endpoint", "golden", "EVT-F04-06")),
    ]


# --------------------------------------------------------------------- F05
F05_TEXT = ("Simmer 400 g chopped tomatoes with 1 cooked onion for 20 minutes. "
            "Freeze half of the sauce.")


def f05():
    return [
        E("EVT-F05-01", 1, Op.CREATE, outputs=(
            lot("ENTITY-F05-tomato", "ING-tomato", "chopped tomatoes", Q(A("400 g", "g", 400))),
            lot("ENTITY-F05-onion", "ING-onion", "cooked onion", Q(A("1 onion", "onion", 1))))),
        E("EVT-F05-02", 2, Op.MERGE, inputs=("ENTITY-F05-tomato", "ENTITY-F05-onion"),
          outputs=(lot("ENTITY-F05-sauce", None, "tomato sauce"),), process_raw="simmer"),
        E("EVT-F05-03", 3, Op.SET_FIELD, inputs=("ENTITY-F05-sauce",),
          belief=planned("duration", 20, "EVT-F05-03", unit="min")),
        E("EVT-F05-04", 4, Op.SPLIT, inputs=("ENTITY-F05-sauce",), outputs=(
            lot("ENTITY-F05-sauce-freeze", None, "sauce to freeze", fraction=0.5),
            lot("ENTITY-F05-sauce-rest", None, "sauce to serve"))),
        E("EVT-F05-05", 5, Op.TRANSFER, inputs=("ENTITY-F05-sauce-freeze",), location="freezer"),
    ]


# --------------------------------------------------------------------- F06
F06_TEXT = "Separate 2 eggs. Whisk the whites to stiff peaks."


def f06():
    return [
        E("EVT-F06-01", 1, Op.CREATE, outputs=(lot("ENTITY-F06-eggs", "ING-egg", "eggs",
                                                   Q(A("2 eggs", "egg", 2))),)),
        E("EVT-F06-02", 2, Op.SPLIT, inputs=("ENTITY-F06-eggs",), process_raw="separate", outputs=(
            lot("ENTITY-F06-yolks", "ING-egg-yolk", "yolks"),
            lot("ENTITY-F06-whites", "ING-egg-white", "whites"))),
        E("EVT-F06-03", 3, Op.TRANSFORM, inputs=("ENTITY-F06-whites",), process_raw="whisk",
          belief=planned("texture_endpoint", "stiff peaks", "EVT-F06-03")),
    ]


# --------------------------------------------------------------------- F07
F07_TEXT = ("Mix 150 g yogurt with 1 tsp chilli powder and a pinch of salt. Add 500 g chicken "
            "and leave to marinate in the fridge.")


def f07():
    return [
        E("EVT-F07-01", 1, Op.CREATE, outputs=(
            lot("ENTITY-F07-yogurt", "ING-yogurt", "yogurt", Q(A("150 g", "g", 150))),
            lot("ENTITY-F07-chilli", "ING-chilli-powder", "chilli powder", Q(A("1 tsp", "tsp", 1))),
            # verbal quantity stays qualitative: no numeric value (master prompt J2)
            lot("ENTITY-F07-salt", "ING-salt", "salt", Q(A("a pinch", "pinch"))))),
        E("EVT-F07-02", 2, Op.MERGE,
          inputs=("ENTITY-F07-yogurt", "ENTITY-F07-chilli", "ENTITY-F07-salt"),
          outputs=(lot("ENTITY-F07-marinade", None, "marinade"),), process_raw="mix"),
        E("EVT-F07-03", 3, Op.CREATE, outputs=(lot("ENTITY-F07-chicken", "ING-chicken", "chicken",
                                                   Q(A("500 g", "g", 500))),)),
        E("EVT-F07-04", 4, Op.MERGE, inputs=("ENTITY-F07-marinade", "ENTITY-F07-chicken"),
          outputs=(lot("ENTITY-F07-marinating", None, "chicken in marinade"),), process_raw="add"),
        E("EVT-F07-05", 5, Op.TRANSFER, inputs=("ENTITY-F07-marinating",), location="fridge"),
    ]


# --------------------------------------------------------------------- F08
F08_TEXT = "Add 200 g dried chickpeas to the onion-tomato base and cook."


def f08():
    soak = E("EVT-F08-P1", 0, Op.TRANSFORM, inputs=("ENTITY-F08-chickpeas",), process_raw="soak",
             belief=planned("hydration", "soaked", "EVT-F08-P1"))
    return [
        E("EVT-F08-01", 1, Op.CREATE, outputs=(
            lot("ENTITY-F08-chickpeas", "ING-chickpea", "dried chickpeas", Q(A("200 g", "g", 200))),
            lot("ENTITY-F08-base", None, "onion-tomato base"))),
        E("EVT-F08-02", 2, Op.OMITTED_STEP_CANDIDATE, candidate_id="CAND-F08-1", proposed=soak,
          rationale="dried legumes are normally soaked before cooking "
                    "(rule R-SOAK-01; precision to be measured, AN4)"),
        E("EVT-F08-03", 3, Op.ACCEPT_CANDIDATE, candidate_id="CAND-F08-1"),
        E("EVT-F08-04", 4, Op.MERGE, inputs=("ENTITY-F08-chickpeas", "ENTITY-F08-base"),
          outputs=(lot("ENTITY-F08-stew", None, "chickpea stew"),), process_raw="cook"),
    ]


# --------------------------------------------------------------------- F09
F09_TEXT = "Shape the dough and bake it for 30 minutes."


def f09():
    proof = E("EVT-F09-P1", 0, Op.TRANSFORM, inputs=("ENTITY-F09-dough",), process_raw="proof")
    return [
        E("EVT-F09-01", 1, Op.CREATE, outputs=(lot("ENTITY-F09-dough", "ING-dough", "dough"),)),
        E("EVT-F09-02", 2, Op.TRANSFORM, inputs=("ENTITY-F09-dough",), process_raw="shape"),
        E("EVT-F09-03", 3, Op.OMITTED_STEP_CANDIDATE, candidate_id="CAND-F09-1", proposed=proof,
          rationale="yeasted doughs are usually proofed after shaping (rule R-PROOF-01)"),
        E("EVT-F09-04", 4, Op.REJECT_CANDIDATE, candidate_id="CAND-F09-1"),
        E("EVT-F09-05", 5, Op.TRANSFORM, inputs=("ENTITY-F09-dough",), process_raw="bake",
          belief=planned("duration", 30, "EVT-F09-05", unit="min")),
    ]


# --------------------------------------------------------------------- F10
F10_TEXT = "Heat 2–3 tbsp oil. Use half of it to fry the spices and keep the rest."


def f10():
    return [
        E("EVT-F10-01", 1, Op.CREATE, outputs=(lot("ENTITY-F10-oil", "ING-oil", "oil",
                                                   Q(A("2–3 tbsp", "tbsp", lo=2, hi=3))),)),
        E("EVT-F10-02", 2, Op.TRANSFORM, inputs=("ENTITY-F10-oil",), process_raw="heat",
          belief=planned("temperature_state", "hot", "EVT-F10-02")),
        E("EVT-F10-03", 3, Op.SPLIT, inputs=("ENTITY-F10-oil",), outputs=(
            lot("ENTITY-F10-oil-use", "ING-oil", "oil for spices", fraction=0.5),
            lot("ENTITY-F10-oil-rest", "ING-oil", "oil kept back"))),
    ]


FIXTURES = {
    "F01": (F01_TEXT, f01), "F02": (F02_TEXT, f02), "F03": (F03_TEXT, f03),
    "F04": (F04_TEXT, f04), "F05": (F05_TEXT, f05), "F06": (F06_TEXT, f06),
    "F07": (F07_TEXT, f07), "F08": (F08_TEXT, f08), "F09": (F09_TEXT, f09),
    "F10": (F10_TEXT, f10),
}
