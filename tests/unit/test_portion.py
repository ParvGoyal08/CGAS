r"""POR- rules with TEST rows (numbers here are test fixtures, not food data)."""
import pytest

from culinarystate.quantity.portion import PorRow, Portions

ROWS = [PorRow(por_id="POR-000001", ingredient_id="ING-test-flour", state="UNSPECIFIED", basis="ml",
               descriptor="SIFTED", grams_per_basis=0.5, source_id="SRC-TEST", source_quote="test fixture"),
        PorRow(por_id="POR-000002", ingredient_id="ING-test-egg", state="WHOLE", basis="UNIT-egg",
               descriptor="LARGE", grams_per_basis=10.0, source_id="SRC-TEST", source_quote="test fixture")]


@pytest.fixture(scope="module")
def por():
    return Portions(ROWS)


def test_exact_match_converts_and_unknown_locale_stays_interval(por):
    c = por.to_grams("ING-test-flour", "UNSPECIFIED", "UNIT-cup", 1.0, qualifiers=("sifted",))
    assert c.status == "LOCALE_INTERVAL" and c.lo < c.hi and c.unit == "g"
    c2 = por.to_grams("ING-test-flour", "UNSPECIFIED", "UNIT-cup", 1.0, qualifiers=("sifted",), locale="METRIC")
    assert c2.status == "EXACT" and abs(c2.value - 125.0) < 1e-9


def test_descriptor_and_state_must_match_exactly(por):
    assert por.to_grams("ING-test-flour", "UNSPECIFIED", "UNIT-cup", 1.0).status == "UNKNOWN"          # no 'sifted'
    assert por.to_grams("ING-test-flour", "UNSPECIFIED", "UNIT-cup", 1.0, qualifiers=("packed",)).status == "UNKNOWN"
    assert por.to_grams("ING-test-flour", "GROUND", "UNIT-cup", 1.0, qualifiers=("sifted",)).status == "UNKNOWN"


def test_count_units_and_no_borrowing_between_foods(por):
    assert por.to_grams("ING-test-egg", "WHOLE", "UNIT-egg", 2, qualifiers=("large",)).value == 20.0
    assert por.to_grams("ING-test-egg", "WHOLE", "UNIT-egg", 2).status == "UNKNOWN"                    # size unstated
    assert por.to_grams("ING-other", "WHOLE", "UNIT-egg", 2, qualifiers=("large",)).status == "UNKNOWN"


def test_mass_units_need_no_por_and_empty_ledger_never_invents(por):
    assert por.to_grams("ING-anything", "RAW", "UNIT-kg", 1.0).value == 1000.0
    assert Portions().to_grams("ING-onion", "CHOPPED", "UNIT-cup", 1.0).status == "UNKNOWN"


def test_conflicting_descriptors_are_unknown(por):
    assert por.to_grams("ING-test-flour", "UNSPECIFIED", "UNIT-cup", 1.0, qualifiers=("heaped", "level")).status == "UNKNOWN"
