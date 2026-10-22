r"""WP-06 / K2 / K5 tests — evidence schema rules and the USDA R6 ingestion."""
from __future__ import annotations

import json
import pathlib

import pytest
from pydantic import ValidationError

from culinarystate.ingest.usda_r6 import ingest, parse_desc
from culinarystate.ledger.schema import Condition, EvidenceRow, Verification

ROOT = pathlib.Path(__file__).resolve().parents[2]
R6 = ROOT / "data/raw/usda_r6/NutrientRetention.csv"

GOOD = dict(evidence_id="EVD-000001", source_id="SRC-0001", source_family_id="F",
            origin_type="DATABASE_AGGREGATE", source_record="x", ingredient_raw="beef",
            ingredient_id="ING-beef", process_raw="boiled", process_ids=("PROC-boil",),
            target_type="NUTRIENT", target_variable="Thiamin", value_kind="RETENTION_PERCENT",
            value=80.0, unit="%", tier="E3", provenance="EXPLICIT_SOURCE")


def test_good_row_validates():
    assert EvidenceRow(**GOOD).evaluable


@pytest.mark.parametrize("patch,why", [
    (dict(value=None), "no value, no direction, no defect"),
    (dict(lo=90.0, hi=95.0), "value outside interval"),
    (dict(unit=None), "value without unit"),
    (dict(origin_type="PRIMARY_STUDY"), "primary study without study ids"),
    (dict(tier="E4"), "E4 without human verification"),
    (dict(tier="E5"), "E5 must be UNVERIFIED"),
    (dict(provenance="MODEL_ESTIMATED"), "model estimate holding tier E3"),
    (dict(process_ids=("boil",)), "process id without PROC- prefix"),
    (dict(process_ids=(), process_alternatives=("PROC-boil",)), "single 'alternative'"),
    (dict(ingredient_id="beef"), "ingredient without ING- prefix"),
    (dict(value=80.0, direction="INCREASE"), "direction contradicts value"),
    (dict(defect="X"), "defective row carrying a value"),
])
def test_broken_rows_are_rejected(patch, why):           # SX-00-01
    with pytest.raises(ValidationError):
        EvidenceRow(**{**GOOD, **patch})


def test_condition_rules():
    with pytest.raises(ValidationError):
        Condition(status="UNKNOWN", value=100.0)
    with pytest.raises(ValidationError):
        Condition(status="RANGE", lo=10.0, unit="min")
    with pytest.raises(ValidationError):
        Condition(status="MEASURED", value=10.0)               # no unit
    assert Condition(status="QUALITATIVE", raw="medium heat").value is None


def test_e4_needs_verified_span():
    ok = EvidenceRow(**{**GOOD, "tier": "E4", "origin_type": "PRIMARY_STUDY", "study_ids": ("STUDY-0001",),
                        "verification": Verification(status="VERIFIED", verifier="P", span_locator="Table 2")})
    assert ok.evaluable


@pytest.fixture(scope="module")
def r6():
    return ingest(R6)


def test_r6_counts(r6):
    rows, rep = r6
    assert rep["rows"] == 7018 and rep["codes"] == 270
    assert rep["unparsed"] == {}
    assert rep["defects"] == 24                                   # code 5005: factor missing in source
    assert sum(r.defect is not None for r in rows) == 24
    assert {r.source_record.split(";")[0] for r in rows if r.defect} == {"Retn_Code=5005"}
    assert len({r.evidence_id for r in rows}) == 7018


def test_r6_censoring_and_rounding(r6):
    rows, _ = r6
    for r in rows:
        if r.defect:
            continue
        assert r.rounding_resolution == 5.0
        if r.value >= 100:
            assert r.censoring.value == "RIGHT" and r.lo == 97.5 and r.hi is None
        else:
            assert r.censoring.value == "NONE" and r.hi - r.lo == 5.0


def test_del1_acceptance_fields_present_on_every_row(r6):
    rows, _ = r6
    for r in rows:
        assert r.source_id and r.tier and r.censoring is not None
        assert "T" in r.conditions and r.conditions["T"].status.value == "UNKNOWN"   # R6 states no temperatures
        assert r.process_ids or r.process_alternatives
        assert r.source_imputation_possible


@pytest.mark.parametrize("desc,seq,alt,state,form", [
    ("PORK,FRESH,ROAST,SIMMERED WO/DRIP", ["simmer"], [], "fresh", ["roast cut", "without drippings"]),
    ("BEEF,ROASTED", ["roast"], [], None, []),
    ("BACON,BROILED/FRIED", [], ["broil", "fry"], None, []),
    ("LEGUMES,CKD 2/2.5HRS,BOILED+BAKED", ["boil", "bake"], [], None, []),
    ("FRUITS,FROZEN", ["freeze"], [], None, []),
    ("POTATOES,CANNED,BOILED,WATER USED", ["boil"], [], "canned", []),
    ("VEG,OTHER,CKD FROM FRZN(BLD,DRAIND)", ["cook", "boil", "drain"], [], "frozen", []),
    ("SWEETPOTATOES,BOILED (PARED)DRAINED", ["peel", "boil", "drain"], [], None, []),
])
def test_r6_parse_semantics(desc, seq, alt, state, form):
    P = parse_desc(desc)
    assert (P.processes, P.alternatives, P.state_in, P.forms) == (seq, alt, state, form)


def test_r6_times_are_ranges_not_inventions():
    P = parse_desc("LEGUMES,CKD 2/2.5HRS,BOILED+BAKED")
    assert (P.time.status.value, P.time.lo, P.time.hi, P.time.unit) == ("RANGE", 120.0, 150.0, "min")
    assert parse_desc("BEEF,ROASTED").time is None                      # nothing stated → nothing filled


def test_ledger_build_is_reproducible():
    rows1, _ = ingest(R6)
    rows2, _ = ingest(R6)
    dump = lambda rs: [json.dumps(r.model_dump(mode="json"), sort_keys=True) for r in rs]
    assert dump(rows1) == dump(rows2)
