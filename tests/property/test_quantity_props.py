r"""K7 property-based tests (master prompt Part J3): dimensional consistency, idempotence,
raw round trip, no invented grams, interval coverage, linearity."""
from __future__ import annotations

import math

from hypothesis import given, settings, strategies as st

from culinarystate.quantity import Units, parse_quantity

U = Units()
MASS = ["g", "kg", "oz", "lb", "grams", "pounds"]
VOLUME = ["ml", "l", "cup", "cups", "tbsp", "tsp", "tablespoon", "teaspoons", "fl oz", "pint", "quart"]
NONMASS = VOLUME + ["clove", "cloves", "slice", "bunch", "can", "packet", "pinch", "katori", "glass", "dozen"]

nums = st.one_of(st.integers(1, 999).map(str),
                 st.tuples(st.integers(1, 9), st.integers(2, 8)).map(lambda t: f"{t[0]}/{t[1]}"),
                 st.tuples(st.integers(1, 9), st.integers(1, 7), st.integers(8, 8)).map(lambda t: f"{t[0]} {t[1]}/{t[2]}"),
                 st.floats(0.1, 500, allow_nan=False).map(lambda x: f"{x:.2f}"))


@settings(max_examples=300, deadline=None)
@given(nums, st.sampled_from(MASS + NONMASS), st.sampled_from(["", " onion", " of salt", " chopped parsley"]))
def test_raw_round_trip_and_idempotence(n, unit, food):
    raw = f"{n} {unit}{food}"
    a, b = parse_quantity(raw), parse_quantity(raw)
    assert a.raw == raw                          # raw text always preserved
    assert a == b                                # deterministic / idempotent
    assert a.kind in ("NUMERIC", "SUM", "PACKAGE", "RANGE")
    assert a.unit_id is not None


@settings(max_examples=300, deadline=None)
@given(nums, st.sampled_from(NONMASS))
def test_no_invented_grams(n, unit):             # SX-10-02: must be zero
    p = parse_quantity(f"{n} {unit}")
    c = U.to_grams(p.unit_id, p.value, p.lo, p.hi)
    assert c.status == "UNKNOWN" and c.value is None and c.lo is None


@settings(max_examples=200, deadline=None)
@given(st.floats(0.01, 1000, allow_nan=False), st.sampled_from(["UNIT-g", "UNIT-kg", "UNIT-oz", "UNIT-lb"]),
       st.floats(0.1, 10, allow_nan=False))
def test_mass_conversion_is_linear(x, uid, k):
    a, b = U.to_grams(uid, x), U.to_grams(uid, x * k)
    assert a.status == "EXACT" and math.isclose(b.value, a.value * k, rel_tol=1e-9)


@settings(max_examples=200, deadline=None)
@given(st.floats(0.1, 20, allow_nan=False), st.sampled_from(["UNIT-cup", "UNIT-tbsp", "UNIT-tsp", "UNIT-fl-oz"]))
def test_locale_interval_covers_every_convention(x, uid):
    unknown = U.to_si(uid, x)
    assert unknown.status == "LOCALE_INTERVAL" and unknown.lo <= unknown.hi
    for loc in U.units[uid].variants:
        exact = U.to_si(uid, x, locale=loc)
        if exact.value is not None:
            assert unknown.lo - 1e-9 <= exact.value <= unknown.hi + 1e-9


@settings(max_examples=200, deadline=None)
@given(st.integers(1, 50), st.integers(1, 50), st.sampled_from(["-", "–", " to ", " or "]), st.sampled_from(VOLUME + MASS))
def test_ranges_are_ordered(a, b, sep, unit):
    p = parse_quantity(f"{a}{sep}{b} {unit}")
    assert p.kind == "RANGE" and p.lo <= p.hi and {p.lo, p.hi} == {float(a), float(b)}


def test_dimensional_safety():
    assert U.to_grams("UNIT-ml", 100).status == "UNKNOWN"       # volume never becomes mass
    assert U.to_si("UNIT-katori", 1).status == "UNKNOWN"        # no authoritative value
    assert U.to_si("UNIT-pinch", 1).status == "UNKNOWN"         # verbal stays qualitative
    assert U.to_si("UNIT-tbsp", 1, locale="AU").value == 20.0
    assert U.to_si("UNIT-tbsp", 1, locale="US-LABEL").value == 15.0
    assert abs(U.to_si("UNIT-degF", 212).value - 100.0) < 1e-9


def test_grammar_cases():
    p = parse_quantity("1 (400 g) can tomatoes")
    assert (p.kind, p.value, p.unit_id, p.inner.value, p.inner.unit_id, p.rest) == ("PACKAGE", 1.0, "UNIT-can", 400.0, "UNIT-g", "tomatoes")
    s = parse_quantity("1/4 cup plus 2 tbsp sugar")
    assert s.kind == "SUM" and [(t.value, t.unit_id) for t in s.terms] == [(0.25, "UNIT-cup"), (2.0, "UNIT-tbsp")]
    assert parse_quantity("1 T butter").unit_id == "UNIT-tbsp" and parse_quantity("1 t soda").unit_id == "UNIT-tsp"
    q = parse_quantity("a pinch of salt")
    assert (q.kind, q.value, q.rest) == ("QUALITATIVE", None, "salt")
    assert parse_quantity("about 200 ml milk").qualifiers == ["about"]
