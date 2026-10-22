r"""
Evidence ledger schema v1 (DEL-1, WP-06) — SSOT §203.2 trimmed to the proposal's
DEL-1 fields, with master plan v4.0 corrections:

  AH1  origin_type + required source_family_id; study_ids optional for aggregates,
       required (and never fabricated) for PRIMARY_STUDY rows
  AH2  internal ING- identity first; external links optional (UNRESOLVED_EXTERNAL ok)
  AM2  retention semantics preserved: method (true/apparent), basis, yield factor,
       SD/range/n, censoring, rounding resolution; RF > 1 is never clipped

Every row validates on construction; a broken row raises (SX-00-01).
"""
from __future__ import annotations

import enum
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Provenance(str, enum.Enum):
    EXPLICIT_SOURCE = "EXPLICIT_SOURCE"
    EXTERNAL_VERIFIED = "EXTERNAL_VERIFIED"
    DERIVED_DETERMINISTIC = "DERIVED_DETERMINISTIC"
    INFERRED_LLM = "INFERRED_LLM"
    MODEL_ESTIMATED = "MODEL_ESTIMATED"
    IMPUTED = "IMPUTED"
    SIMULATED = "SIMULATED"
    UNKNOWN = "UNKNOWN"


class Tier(str, enum.Enum):
    E1 = "E1"; E2 = "E2"; E3 = "E3"; E4 = "E4"; E5 = "E5"; E6 = "E6"; E7 = "E7"  # noqa: E702


class OriginType(str, enum.Enum):
    PRIMARY_STUDY = "PRIMARY_STUDY"
    DATABASE_AGGREGATE = "DATABASE_AGGREGATE"
    REVIEW_AGGREGATE = "REVIEW_AGGREGATE"
    AUTHORITY_STANDARD = "AUTHORITY_STANDARD"
    PROJECT_MEASUREMENT = "PROJECT_MEASUREMENT"


class ConditionStatus(str, enum.Enum):
    MEASURED = "MEASURED"
    RANGE = "RANGE"
    QUALITATIVE = "QUALITATIVE"
    UNKNOWN = "UNKNOWN"


class TargetType(str, enum.Enum):
    NUTRIENT = "NUTRIENT"
    POLYPHENOL = "POLYPHENOL"
    VOLATILE = "VOLATILE"
    PHYSICAL = "PHYSICAL"
    SENSORY = "SENSORY"
    SAFETY_MARKER = "SAFETY_MARKER"
    OTHER = "OTHER"


class ValueKind(str, enum.Enum):
    RETENTION_PERCENT = "RETENTION_PERCENT"
    RETENTION_FRACTION = "RETENTION_FRACTION"
    CONCENTRATION = "CONCENTRATION"
    DELTA = "DELTA"
    DIRECTION_ONLY = "DIRECTION_ONLY"


class RetentionMethod(str, enum.Enum):
    TRUE_RETENTION = "TRUE_RETENTION"
    APPARENT_RETENTION = "APPARENT_RETENTION"
    UNSPECIFIED = "UNSPECIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Basis(str, enum.Enum):
    WET = "WET"
    DRY = "DRY"
    UNSPECIFIED = "UNSPECIFIED"


class Censoring(str, enum.Enum):
    NONE = "NONE"
    RIGHT = "RIGHT"     # true value ≥ reported (e.g. R6 caps at 100)
    LEFT = "LEFT"       # true value ≤ reported (non-detect / < LOD)
    INTERVAL = "INTERVAL"


class Direction(str, enum.Enum):
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    NO_CHANGE = "NO_CHANGE"


class Condition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    status: ConditionStatus = ConditionStatus.UNKNOWN
    value: Optional[float] = None
    lo: Optional[float] = None
    hi: Optional[float] = None
    unit: Optional[str] = None
    raw: Optional[str] = None          # the source text the condition came from

    @model_validator(mode="after")
    def _consistent(self):
        nums = (self.value, self.lo, self.hi)
        if self.status == ConditionStatus.UNKNOWN and any(v is not None for v in nums):
            raise ValueError("an UNKNOWN condition carries no numbers")
        if self.status == ConditionStatus.MEASURED and self.value is None:
            raise ValueError("MEASURED needs a value")
        if self.status == ConditionStatus.RANGE and (self.lo is None or self.hi is None):
            raise ValueError("RANGE needs lo and hi")
        if self.lo is not None and self.hi is not None and self.lo > self.hi:
            raise ValueError("lo > hi")
        if self.status in (ConditionStatus.MEASURED, ConditionStatus.RANGE) and not self.unit:
            raise ValueError("a numeric condition needs a unit")
        return self


class Verification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    status: str = "NOT_APPLICABLE"     # VERIFIED | UNVERIFIED | NOT_APPLICABLE
    verifier: Optional[str] = None
    span_locator: Optional[str] = None  # e.g. "Table 2, row 'broccoli boiled', p. 4"

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        if v not in ("VERIFIED", "UNVERIFIED", "NOT_APPLICABLE"):
            raise ValueError(f"bad verification status {v}")
        return v


CONDITION_KEYS = ("T", "t", "pH", "aw", "moisture", "pressure", "medium", "water_handling")


class EvidenceRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str = Field(pattern=r"^EVD-\d{6}$")
    source_id: str = Field(pattern=r"^SRC-\d{4}$")
    source_family_id: str = Field(min_length=1)
    origin_type: OriginType
    study_ids: tuple[str, ...] = ()
    snapshot_id: Optional[str] = Field(default=None, pattern=r"^SNAP-\d{4}$")
    source_record: str = Field(min_length=1)          # locator inside the source

    ingredient_raw: str = Field(min_length=1)
    ingredient_id: str = Field(pattern=r"^ING-[a-z0-9]+(-[a-z0-9]+)*$")
    ingredient_link_status: str = "UNRESOLVED_EXTERNAL"
    ingredient_xrefs: tuple[str, ...] = ()
    ingredient_granularity: str = "INGREDIENT"   # INGREDIENT | CATEGORY (e.g. R6 "VEG,ROOTS,ETC")
    food_group: Optional[str] = None
    food_form: Optional[str] = None
    state_in: Optional[str] = None
    state_out: Optional[str] = None

    process_raw: str = Field(min_length=1)
    process_ids: tuple[str, ...] = ()            # definite steps, in order; PROC-UNMAPPED allowed
    process_alternatives: tuple[str, ...] = ()   # one further step that is EITHER of these (R6 "BROILED/FRIED")
    conditions: dict[str, Condition] = Field(default_factory=dict)

    target_type: TargetType
    target_variable: str = Field(min_length=1)
    target_code: Optional[str] = None
    target_molecule_id: Optional[str] = Field(default=None, pattern=r"^MOL-[A-Z0-9-]+$")

    value_kind: ValueKind
    value: Optional[float] = None
    lo: Optional[float] = None
    hi: Optional[float] = None
    unit: Optional[str] = None
    direction: Optional[Direction] = None
    retention_method: RetentionMethod = RetentionMethod.NOT_APPLICABLE
    basis: Basis = Basis.UNSPECIFIED
    yield_factor: Optional[float] = None
    sd: Optional[float] = None
    n_aggregated: Optional[int] = None
    censoring: Censoring = Censoring.NONE
    lod: Optional[float] = None
    rounding_resolution: Optional[float] = None
    source_imputation_possible: bool = False

    tier: Tier
    provenance: Provenance
    verification: Verification = Verification()
    defect: Optional[str] = None
    notes: Optional[str] = None
    ledger_version: str = "v0"

    @field_validator("process_ids", "process_alternatives")
    @classmethod
    def _procs(cls, v):
        for p in v:
            if not re.fullmatch(r"PROC-[a-z0-9]+(-[a-z0-9]+)*", p):
                raise ValueError(f"bad process id {p}")
        return v

    @field_validator("ingredient_granularity")
    @classmethod
    def _gran(cls, v):
        if v not in ("INGREDIENT", "CATEGORY"):
            raise ValueError(f"bad ingredient_granularity {v}")
        return v

    @field_validator("conditions")
    @classmethod
    def _conds(cls, v):
        for k in v:
            if k not in CONDITION_KEYS:
                raise ValueError(f"unknown condition key {k}")
        return v

    @model_validator(mode="after")
    def _rules(self):
        if not self.process_ids and len(self.process_alternatives) < 1:
            raise ValueError("a row needs at least one process (definite or alternative)")
        if len(self.process_alternatives) == 1:
            raise ValueError("process_alternatives needs ≥2 options (else it is a definite step)")
        # value / direction / defect
        if self.defect is None and self.value is None and self.direction is None:
            raise ValueError("a row needs a value or a direction (or a recorded defect)")
        if self.defect is not None and self.value is not None:
            raise ValueError("a defective row cannot carry a value")
        if self.value_kind == ValueKind.DIRECTION_ONLY and self.value is not None:
            raise ValueError("DIRECTION_ONLY rows carry no value")
        if self.value is not None and self.lo is not None and self.hi is not None:
            if not (self.lo <= self.value <= self.hi):
                raise ValueError("value outside [lo, hi]")
        if self.value is not None and self.unit is None:
            raise ValueError("a value needs a unit")
        # value and direction must not contradict for retention values
        if (self.value is not None and self.direction is not None
                and self.value_kind == ValueKind.RETENTION_PERCENT):
            implied = (Direction.DECREASE if self.value < 100 else
                       Direction.NO_CHANGE if self.value == 100 else Direction.INCREASE)
            if implied != self.direction and self.censoring == Censoring.NONE:
                raise ValueError("direction contradicts the retention value")
        # lineage (AH1)
        if self.origin_type == OriginType.PRIMARY_STUDY and not self.study_ids:
            raise ValueError("PRIMARY_STUDY rows need study_ids (never fabricated)")
        # tiers (Part I1) and verification (G15-H)
        if self.tier == Tier.E4 and (self.verification.status != "VERIFIED"
                                     or not self.verification.span_locator):
            raise ValueError("E4 rows must be human-verified with a span locator")
        if self.tier == Tier.E5 and self.verification.status != "UNVERIFIED":
            raise ValueError("E5 rows are LLM-extracted and UNVERIFIED")
        if self.tier == Tier.E6 and self.provenance != Provenance.MODEL_ESTIMATED:
            raise ValueError("E6 rows are MODEL_ESTIMATED")
        if self.tier == Tier.E7 and self.provenance != Provenance.SIMULATED:
            raise ValueError("E7 rows are SIMULATED")
        if self.provenance in (Provenance.MODEL_ESTIMATED, Provenance.SIMULATED, Provenance.IMPUTED) \
                and self.tier in (Tier.E1, Tier.E2, Tier.E3, Tier.E4):
            raise ValueError("model/simulated/imputed values cannot hold an evidence tier E1–E4")
        # censoring sanity
        if self.censoring == Censoring.LEFT and self.lod is None and self.value is None:
            raise ValueError("a left-censored row needs a LOD or a reported value")
        return self

    @property
    def evaluable(self) -> bool:
        """May enter test/calibration sets (Part I1: only E1–E4, never defects)."""
        return self.tier in (Tier.E1, Tier.E2, Tier.E3, Tier.E4) and self.defect is None
