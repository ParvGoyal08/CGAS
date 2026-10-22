r"""
Data model for the event-sourced recipe/session state graph (DEL-3, block B11).

Contracts implemented (SSOT §233, master plan v4.0 Part AN):

* AN1 — three identities are never collapsed:
      concept_id  ING-…     the canonical food concept ("butter")
      entity_id   ENTITY-…  one physical lot in this session ("this 50 g of butter")
      version_id  STATE-…   one state of that lot ("ENTITY-0001 after melting")
* AN2 — quantities are symbolic first. Amounts carry their raw text and their own
  unit. The engine NEVER converts between units: "50 g − 1 tbsp" stays symbolic.
  Only same-unit arithmetic is evaluated, because that is deterministic (law B10).
* AN3 — every state field carries trajectory PLANNED | OBSERVED_SESSION | PREDICTED.
* AN4 — omitted steps are candidates, never applied unless accepted.

Everything here is immutable (frozen dataclasses). Corrections are new events.
"""
from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Any, Optional


class Trajectory(str, enum.Enum):
    PLANNED = "PLANNED"
    OBSERVED_SESSION = "OBSERVED_SESSION"
    PREDICTED = "PREDICTED"


class Provenance(str, enum.Enum):
    """Master prompt Part B3. The last five may never be promoted to observed/Gold."""
    EXPLICIT_SOURCE = "EXPLICIT_SOURCE"
    EXTERNAL_VERIFIED = "EXTERNAL_VERIFIED"
    DERIVED_DETERMINISTIC = "DERIVED_DETERMINISTIC"
    INFERRED_LLM = "INFERRED_LLM"
    MODEL_ESTIMATED = "MODEL_ESTIMATED"
    IMPUTED = "IMPUTED"
    SIMULATED = "SIMULATED"
    UNKNOWN = "UNKNOWN"


class Relation(str, enum.Enum):
    """SSOT §233.5 edge types."""
    TRANSFORMS_INTO = "TRANSFORMS_INTO"
    MERGES_INTO = "MERGES_INTO"
    SPLITS_INTO = "SPLITS_INTO"
    RESERVED_AS = "RESERVED_AS"
    DISCARDED_FROM = "DISCARDED_FROM"
    RECOMBINED_WITH = "RECOMBINED_WITH"
    TRANSFERRED_TO = "TRANSFERRED_TO"
    PART_OF = "PART_OF"
    LOCATED_IN = "LOCATED_IN"
    OBSERVED_AS = "OBSERVED_AS"


class Op(str, enum.Enum):
    CREATE = "CREATE"            # introduce a physical lot of a concept
    TRANSFORM = "TRANSFORM"      # same lot, new version (melt, chop, brown)
    MERGE = "MERGE"              # ≥2 lots → one new intermediate lot
    SPLIT = "SPLIT"              # one lot → ≥2 new lots with allocations
    RESERVE = "RESERVE"          # SPLIT where one child is set aside for later
    DISCARD = "DISCARD"          # a lot leaves the recipe
    RECOMBINE = "RECOMBINE"      # a reserved lot rejoins another lot
    TRANSFER = "TRANSFER"        # move a lot to a location/vessel
    SET_FIELD = "SET_FIELD"      # planned or predicted belief about a field
    OBSERVE = "OBSERVE"          # direct observation of a field (overrides belief)
    OMITTED_STEP_CANDIDATE = "OMITTED_STEP_CANDIDATE"
    ACCEPT_CANDIDATE = "ACCEPT_CANDIDATE"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"


# ------------------------------------------------------------------ quantities
@dataclass(frozen=True)
class Amount:
    """
    One quantity as stated. `value` or the interval `[lo, hi]` may be None.
    `unit` is the unit token as written ("g", "tbsp", "egg"); never converted here.
    """
    raw: str
    unit: Optional[str] = None
    value: Optional[float] = None
    lo: Optional[float] = None
    hi: Optional[float] = None

    def __post_init__(self):
        if self.lo is not None and self.hi is not None and self.lo > self.hi:
            raise ValueError(f"interval lo > hi in {self.raw!r}")
        if self.value is not None and self.lo is not None and self.hi is not None:
            if not (self.lo <= self.value <= self.hi):
                raise ValueError(f"value outside interval in {self.raw!r}")

    @property
    def bounds(self) -> Optional[tuple[float, float]]:
        if self.lo is not None and self.hi is not None:
            return (self.lo, self.hi)
        if self.value is not None:
            return (self.value, self.value)
        return None

    def scaled(self, f: float) -> "Amount":
        """Exact proportional scaling (a stated fraction such as 'half')."""
        if not (0.0 <= f <= 1.0):
            raise ValueError("fraction must be in [0, 1]")
        return Amount(raw=f"{f:g} × ({self.raw})", unit=self.unit,
                      value=None if self.value is None else self.value * f,
                      lo=None if self.lo is None else self.lo * f,
                      hi=None if self.hi is None else self.hi * f)

    def to_dict(self) -> dict:
        return {"raw": self.raw, "unit": self.unit, "value": self.value,
                "lo": self.lo, "hi": self.hi}


@dataclass(frozen=True)
class Term:
    sign: int            # +1 or -1
    amount: Amount


@dataclass(frozen=True)
class Quantity:
    """
    A signed sum of amounts, e.g. 50 g − 1 tbsp. `resolved()` returns a single
    Amount only when every term shares one unit and has numeric bounds;
    otherwise the quantity stays symbolic. No unit conversion, ever.
    """
    terms: tuple[Term, ...]

    @staticmethod
    def of(a: Amount) -> "Quantity":
        return Quantity((Term(+1, a),))

    def minus(self, *others: Amount) -> "Quantity":
        return Quantity(self.terms + tuple(Term(-1, o) for o in others))

    def scaled(self, f: float) -> "Quantity":
        return Quantity(tuple(Term(t.sign, t.amount.scaled(f)) for t in self.terms))

    def units(self) -> set[Optional[str]]:
        return {t.amount.unit for t in self.terms}

    def resolved(self) -> Optional[Amount]:
        units = self.units()
        if len(units) != 1 or None in units:
            return None
        lo = hi = 0.0
        for t in self.terms:
            b = t.amount.bounds
            if b is None:
                return None
            # interval arithmetic: subtracting [a,b] adds [-b,-a]
            lo += t.sign * (b[0] if t.sign > 0 else b[1])
            hi += t.sign * (b[1] if t.sign > 0 else b[0])
        unit = next(iter(units))
        raw = self.render()
        if math.isclose(lo, hi, rel_tol=0, abs_tol=1e-12):
            return Amount(raw=raw, unit=unit, value=lo)
        return Amount(raw=raw, unit=unit, lo=lo, hi=hi)

    def render(self) -> str:
        out = []
        for k, t in enumerate(self.terms):
            sym = "" if (k == 0 and t.sign > 0) else (" + " if t.sign > 0 else " − ")
            out.append(f"{sym}{t.amount.raw}")
        return "".join(out)

    def to_dict(self) -> dict:
        r = self.resolved()
        return {"expr": self.render(),
                "resolved": r.to_dict() if r is not None else None,
                "units": sorted(u for u in self.units() if u is not None)}


# ------------------------------------------------------------------- beliefs
@dataclass(frozen=True)
class Belief:
    """One state-field value as believed at a point in the session (§233.2)."""
    field: str
    value: Any
    trajectory: Trajectory
    provenance: Provenance
    event_id: str
    unit: Optional[str] = None
    lo: Optional[float] = None
    hi: Optional[float] = None
    evidence_ref: Optional[str] = None
    unknown: bool = False

    def to_dict(self) -> dict:
        return {"field": self.field, "value": self.value, "trajectory": self.trajectory.value,
                "provenance": self.provenance.value, "event_id": self.event_id,
                "unit": self.unit, "lo": self.lo, "hi": self.hi,
                "evidence_ref": self.evidence_ref, "unknown": self.unknown}


# -------------------------------------------------------------------- events
@dataclass(frozen=True)
class NewLot:
    """Specification of a lot an event creates."""
    entity_id: str
    concept_id: Optional[str]            # None for intermediates without a concept
    label: str
    quantity: Optional[Quantity] = None
    fraction: Optional[float] = None     # SPLIT: share of the parent, if stated


@dataclass(frozen=True)
class Event:
    event_id: str
    order: int
    op: Op
    inputs: tuple[str, ...] = ()
    outputs: tuple[NewLot, ...] = ()
    process_id: Optional[str] = None
    process_raw: Optional[str] = None
    location: Optional[str] = None
    belief: Optional[Belief] = None          # SET_FIELD / OBSERVE
    candidate_id: Optional[str] = None       # candidate events
    proposed: Optional["Event"] = None       # OMITTED_STEP_CANDIDATE payload
    rationale: Optional[str] = None          # rule / precedent / evidence for a candidate
    trajectory: Trajectory = Trajectory.PLANNED
    provenance: Provenance = Provenance.EXPLICIT_SOURCE
    source_span: Optional[str] = None        # recipe text this event came from
