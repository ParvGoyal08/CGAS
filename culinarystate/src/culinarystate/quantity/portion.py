r"""
T15 / SSOT P4 — POR- portion records: the ONLY route from volume or count to grams.

A POR- row says: for THIS ingredient, in THIS state, measured THIS way, one basis unit weighs
`grams_per_basis` grams — and cites where that number comes from. Lookup is EXACT on
(ingredient_id, state, basis, descriptor). No nearest state, no default descriptor, no density
borrowed from a "similar" food: a mismatch returns UNKNOWN with the reason.

  basis        "ml"  → grams_per_basis is a density (g/ml); the volume comes from Units.to_si, so an
                       unknown locale stays an INTERVAL in grams
               UNIT-<count unit> (UNIT-egg, UNIT-clove, UNIT-fillet …) → grams per one item
  state        WHOLE RAW CHOPPED DICED SLICED MINCED GRATED GROUND MELTED COOKED DRAINED UNSPECIFIED
  descriptor   NONE LEVEL HEAPED PACKED LOOSE SIFTED SCANT GENEROUS ROUNDED SMALL MEDIUM LARGE

Data: ledgers/units/por_v0.csv (empty until a sourced portion table is approved — USDA FoodData
Central portions, CC0, needs gate H2).
"""
from __future__ import annotations

import csv
import pathlib
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .units import Converted, Units

ROOT = pathlib.Path(__file__).resolve().parents[3]
STATES = ("WHOLE", "RAW", "CHOPPED", "DICED", "SLICED", "MINCED", "GRATED", "GROUND", "MELTED", "COOKED",
          "DRAINED", "UNSPECIFIED")
DESCRIPTORS = ("NONE", "LEVEL", "HEAPED", "PACKED", "LOOSE", "SIFTED", "SCANT", "GENEROUS", "ROUNDED",
               "SMALL", "MEDIUM", "LARGE")
QUALIFIER_TO_DESCRIPTOR = {"heaped": "HEAPED", "heaping": "HEAPED", "level": "LEVEL", "packed": "PACKED",
                           "scant": "SCANT", "generous": "GENEROUS", "rounded": "ROUNDED", "large": "LARGE",
                           "small": "SMALL", "medium": "MEDIUM", "sifted": "SIFTED", "loose": "LOOSE"}


class PorRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    por_id: str = Field(pattern=r"^POR-\d{6}$")
    ingredient_id: str = Field(pattern=r"^ING-[a-z0-9]+(-[a-z0-9]+)*$")
    state: str
    basis: str                                     # "ml" or a count UNIT- id
    descriptor: str = "NONE"
    grams_per_basis: float = Field(gt=0)
    source_id: str = Field(min_length=1)           # SRC-/SNAP- id
    source_quote: str = Field(min_length=1)        # verbatim row/label from the source
    n: Optional[int] = None
    sd: Optional[float] = None

    @field_validator("state")
    @classmethod
    def _state(cls, v):
        if v not in STATES:
            raise ValueError(f"state must be one of {STATES}")
        return v

    @field_validator("descriptor")
    @classmethod
    def _desc(cls, v):
        if v not in DESCRIPTORS:
            raise ValueError(f"descriptor must be one of {DESCRIPTORS}")
        return v


class Portions:
    def __init__(self, rows: Optional[list[PorRow]] = None, units: Optional[Units] = None,
                 ledger: pathlib.Path = ROOT / "ledgers/units/por_v0.csv"):
        self.units = units or Units()
        if rows is None:
            rows = []
            if ledger.exists():
                with ledger.open(encoding="utf-8") as fh:
                    for r in csv.DictReader(fh):
                        rows.append(PorRow(**{k: (v if v != "" else None) for k, v in r.items()
                                              if k in PorRow.model_fields}))
        self.index = {}
        for r in rows:
            key = (r.ingredient_id, r.state, r.basis, r.descriptor)
            if key in self.index:
                raise ValueError(f"duplicate POR key {key}")
            self.index[key] = r

    def to_grams(self, ingredient_id: str, state: str, unit_id: str, value: Optional[float] = None,
                 lo: Optional[float] = None, hi: Optional[float] = None, qualifiers: tuple = (),
                 locale: Optional[str] = None) -> Converted:
        mass = self.units.to_grams(unit_id, value, lo, hi)
        if mass.status != "UNKNOWN":
            return mass                                           # already a mass unit: no POR needed
        descs = {QUALIFIER_TO_DESCRIPTOR[q.lower()] for q in qualifiers if q.lower() in QUALIFIER_TO_DESCRIPTOR}
        if len(descs) > 1:
            return Converted("UNKNOWN", reason=f"conflicting descriptors {sorted(descs)}")
        desc = descs.pop() if descs else "NONE"
        u = self.units.units.get(unit_id)
        if u is None:
            return Converted("UNKNOWN", reason=f"unknown unit {unit_id}")
        basis = "ml" if u.dimension == "volume" else unit_id
        row = self.index.get((ingredient_id, state, basis, desc))
        if row is None:
            near = [k for k in self.index if k[0] == ingredient_id and k[2] == basis]
            why = "no POR- record for this ingredient and unit" if not near else \
                f"POR- exists only for {[(k[1], k[3]) for k in near]} — state/descriptor must match exactly"
            return Converted("UNKNOWN", reason=why)
        if basis == "ml":
            vol = self.units.to_si(unit_id, value, lo, hi, locale)
            if vol.status == "UNKNOWN":
                return Converted("UNKNOWN", reason=vol.reason)
            k = row.grams_per_basis
            return Converted(vol.status, "g", *(None if x is None else x * k for x in (vol.value, vol.lo, vol.hi)),
                             reason=f"{row.por_id} ({row.source_id}); {vol.reason}".strip("; "))
        nums = [x for x in (value, lo, hi) if x is not None]
        if not nums:
            return Converted("UNKNOWN", reason="no number stated")
        k = row.grams_per_basis
        return Converted("EXACT", "g", *(None if x is None else x * k for x in (value, lo, hi)),
                         reason=f"{row.por_id} ({row.source_id})")
