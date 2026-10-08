r"""
Unit resolution and deterministic conversion (block B10, master prompt Part J1–J3).

Three problems are never collapsed (§235.1):
  1. physical conversion (g↔kg, mL↔L, °F→°C)            → exact, same dimension only
  2. culinary volume by locale (cup, tbsp, tsp, fl oz)    → exact per locale; unknown
                                                            locale → interval over conventions
  3. volume/count → mass                                  → NEVER here; needs POR- evidence,
                                                            so the answer is UNKNOWN
"""
from __future__ import annotations

import csv
import pathlib
from dataclasses import dataclass
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEDGER = ROOT / "ledgers" / "units"


@dataclass(frozen=True)
class UnitInfo:
    unit_id: str
    type: str
    dimension: str
    si_unit: str
    variants: dict  # locale → (value or None, status, source)


@dataclass(frozen=True)
class Converted:
    status: str                    # EXACT | LOCALE_INTERVAL | UNKNOWN
    unit: Optional[str] = None
    value: Optional[float] = None
    lo: Optional[float] = None
    hi: Optional[float] = None
    reason: str = ""


class Units:
    def __init__(self, ledger: pathlib.Path = LEDGER):
        self.units: dict[str, UnitInfo] = {}
        with (ledger / "unit_map_v0.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                u = self.units.get(r["unit_id"])
                val = float(r["si_value"]) if r["si_value"] else None
                if u is None:
                    u = UnitInfo(r["unit_id"], r["type"], r["dimension"], r["si_unit"], {})
                    self.units[r["unit_id"]] = u
                u.variants[r["locale"]] = (val, r["value_status"], r["source"])
        self.surface_cs: dict[str, str] = {}
        self.surface_ci: dict[str, str] = {}
        with (ledger / "unit_surface_v0.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["case_sensitive"] == "yes":
                    self.surface_cs[r["surface"]] = r["unit_id"]
                else:
                    self.surface_ci[r["surface"].lower()] = r["unit_id"]

    def lookup(self, surface: str) -> Optional[str]:
        s = surface.strip().rstrip(".")
        if s in self.surface_cs:          # "T" = tablespoon, "t" = teaspoon, "c" = cup
            return self.surface_cs[s]
        return self.surface_ci.get(s.lower())

    def to_si(self, unit_id: str, value: Optional[float] = None, lo: Optional[float] = None,
              hi: Optional[float] = None, locale: Optional[str] = None) -> Converted:
        u = self.units.get(unit_id)
        if u is None:
            return Converted("UNKNOWN", reason=f"unknown unit {unit_id}")
        if u.type in ("VERBAL",):
            return Converted("UNKNOWN", reason="verbal quantity stays qualitative")
        if u.unit_id == "UNIT-degF":
            f = (lambda x: None if x is None else (x - 32.0) * 5.0 / 9.0)
            return Converted("EXACT", "degC", f(value), f(lo), f(hi))
        nums = [x for x in (value, lo, hi) if x is not None]
        if not nums:
            return Converted("UNKNOWN", reason="no number stated")
        vals = {loc: v for loc, (v, st, _s) in u.variants.items() if v is not None and st != "UNKNOWN"}
        if not vals:
            return Converted("UNKNOWN", reason=f"{unit_id} has no authoritative value")
        if locale is not None and locale in vals:
            k = vals[locale]
            return Converted("EXACT", u.si_unit, *(None if x is None else x * k for x in (value, lo, hi)))
        if "ANY" in vals:
            k = vals["ANY"]
            return Converted("EXACT", u.si_unit, *(None if x is None else x * k for x in (value, lo, hi)))
        # locale unknown: the honest answer is the interval over all recorded conventions
        kmin, kmax = min(vals.values()), max(vals.values())
        base_lo = min(nums) if lo is None else lo
        base_hi = max(nums) if hi is None else hi
        return Converted("LOCALE_INTERVAL", u.si_unit, None, base_lo * kmin, base_hi * kmax,
                         reason=f"locale unknown; conventions {sorted(vals)}")

    def to_grams(self, unit_id: str, value=None, lo=None, hi=None) -> Converted:
        """Mass only from mass units. Volume/count/package → UNKNOWN (needs POR- evidence)."""
        u = self.units.get(unit_id)
        if u is None or u.dimension != "mass":
            return Converted("UNKNOWN", reason="not a mass unit: grams need portion/density evidence (POR-)")
        c = self.to_si(unit_id, value, lo, hi)
        return c
