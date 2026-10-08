r"""K6 crosswalk rules: products are not their food, spices are not vegetables, first match wins."""
import pytest

from tools.build_ing_crosswalk_v0 import classify

CASES = [
    ("olive oil", "DERIVED_PRODUCT", None), ("chicken stock", "DERIVED_PRODUCT", None),
    ("tomato purée", "DERIVED_PRODUCT", None), ("coconut milk", "DERIVED_PRODUCT", None),
    ("peanut butter", "DERIVED_PRODUCT", None), ("lemon juice", "DERIVED_PRODUCT", None),
    ("black pepper", "NO_R6_CLASS", None), ("wine vinegar", "NO_R6_CLASS", None), ("butter", "NO_R6_CLASS", None),
    ("red pepper", "MAPPED_CATEGORY", "ING-vegetable-other"), ("red wine", "MAPPED_CATEGORY", "ING-alcoholic-beverage"),
    ("egg yolk", "MAPPED_CONCEPT", "ING-egg"), ("cherry tomato", "MAPPED_CONCEPT", "ING-tomato"),
    ("sweet potato", "MAPPED_CONCEPT", "ING-sweet-potato"), ("potato", "MAPPED_CONCEPT", "ING-potato"),
    ("pork sausage", "MAPPED_CATEGORY", "ING-sausage"), ("goat's cheese", "MAPPED_CATEGORY", "ING-cheese"),
    ("chif", "A1_ARTEFACT", None), ("custard", "UNRESOLVED", None), ("pepper", "NO_R6_CLASS", None),
]


@pytest.mark.parametrize("name,outcome,ing", CASES)
def test_rules(name, outcome, ing):
    _, o, t = classify(name)
    assert o == outcome, (name, o, t)
    if ing:
        assert t == ing


@pytest.mark.parametrize("name,ing", [("green beans", "ING-vegetable-other"), ("chestnut mushroom", "ING-vegetable-other"),
                                      ("kidney beans", "ING-legume"), ("banana shallot", "ING-vegetable-other"),
                                      ("beef tomato", "ING-tomato"), ("lamb's lettuce", "ING-vegetable-greens"),
                                      ("lamb kidney", "ING-organ-meat-non-liver")])
def test_preemption(name, ing):
    assert classify(name)[2] == ing


@pytest.mark.parametrize("name", ["egg noodles", "rice noodles", "lime leaves"])
def test_not_mapped_to_food_they_mention(name):
    assert classify(name)[1] == "NO_R6_CLASS"


@pytest.mark.parametrize("name,expect", [
    ("tuna steak", "ING-finfish"), ("salmon steak", "ING-finfish"), ("artichoke heart", "ING-vegetable-other"),
    ("celery heart", "ING-vegetable-other"), ("gem lettuce heart", "ING-vegetable-greens"),
    ("oyster mushroom", "ING-vegetable-other"), ("water chestnut", "ING-vegetable-other"),
    ("orange pepper", "ING-vegetable-other"), ("cherry pepper", "ING-vegetable-other"), ("rice flour", "ING-flour-meal"),
    ("lamb' lettuce", "ING-vegetable-greens"), ("pork steak", "ING-pork"), ("lamb steak", "ING-lamb"),
    ("ginger beer", "beverage_non_alcoholic"), ("bourbon biscuit", "product"), ("chocolate mini egg", "sweetener_or_confection"),
    ("brown rice miso", "spice_or_seasoning"), ("allspice berries", "spice_or_seasoning"),
    ("pomegranate molasses", "product"), ("coconut cream", "product"), ("glacé cherry", "sweetener_or_confection")])
def test_second_band(name, expect):
    assert classify(name)[2] == expect, classify(name)
