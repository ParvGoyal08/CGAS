r"""
P2 — record schemas for the prefixes that had none: STUDY- MEAS- COND- SVAR- CLM- WARN- SPLIT- MODEL- DATASET-.
Pydantic v2, frozen, extra fields forbidden. Every rule encodes a project law:
  * UNKNOWN is a first-class status, never a value;           * no value without a source;
  * no claim is SUPPORTED without experiment + artefact hash + gate verdict (v4.0 AI9);
  * no warning without an authority source (B16, AH3);        * splits are frozen by hash.
"""
from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..ids import is_valid

F = ConfigDict(frozen=True, extra="forbid")


def _ids(values, prefix, field):
    bad = [v for v in values if not is_valid(v, prefix)]
    if bad:
        raise ValueError(f"{field}: not {prefix}- ids: {bad}")


class StudyDesign(str, enum.Enum):
    PRIMARY_CONTROLLED = "PRIMARY_CONTROLLED"
    PRIMARY_OBSERVATIONAL = "PRIMARY_OBSERVATIONAL"
    REVIEW = "REVIEW"
    DATABASE = "DATABASE"
    UNKNOWN = "UNKNOWN"


class Study(BaseModel):
    model_config = F
    study_id: str = Field(pattern=r"^STUDY-\d{6}$")
    source_id: str
    snapshot_id: Optional[str] = None
    doi: Optional[str] = Field(default=None, pattern=r"^10\.\d{4,9}/\S+$")
    pmcid: Optional[str] = Field(default=None, pattern=r"^PMC\d+$")
    title: str = Field(min_length=1)
    year: Optional[int] = Field(default=None, ge=1800, le=2100)
    design: StudyDesign
    source_family_id: str = Field(min_length=1)       # lineage: same lab/dataset/series → same family
    licence: str = Field(min_length=1)

    @model_validator(mode="after")
    def _r(self):
        _ids([self.source_id], "SRC", "source_id")
        if self.snapshot_id:
            _ids([self.snapshot_id], "SNAP", "snapshot_id")
        return self


class SdType(str, enum.Enum):
    SD = "SD"
    SE = "SE"
    CI95 = "CI95"
    UNKNOWN = "UNKNOWN"


class Measurement(BaseModel):
    model_config = F
    meas_id: str = Field(pattern=r"^MEAS-\d{6}$")
    study_id: str
    analyte: str = Field(min_length=1)
    method: str = "UNKNOWN"                           # assay as named in Methods, or UNKNOWN
    unit: Optional[str] = None
    basis: str = "UNSPECIFIED"                        # WET | DRY | UNSPECIFIED
    replicates: Optional[int] = Field(default=None, ge=1)
    dispersion: SdType = SdType.UNKNOWN
    method_quote: Optional[str] = None

    @model_validator(mode="after")
    def _r(self):
        _ids([self.study_id], "STUDY", "study_id")
        if self.basis not in ("WET", "DRY", "UNSPECIFIED"):
            raise ValueError("basis must be WET, DRY or UNSPECIFIED")
        if self.method != "UNKNOWN" and not self.method_quote:
            raise ValueError("a named method needs a verbatim method_quote")
        return self


class CondStatus(str, enum.Enum):
    MEASURED = "MEASURED"
    RANGE = "RANGE"
    QUALITATIVE = "QUALITATIVE"
    UNKNOWN = "UNKNOWN"


COND_AXES = ("T", "t", "pH", "aw", "moisture", "pressure", "oxygen", "medium", "water_handling", "salt", "sugar", "fat",
             "particle_size", "geometry", "mixing", "tool_material", "power", "frequency", "T_profile")


class Condition(BaseModel):
    model_config = F
    cond_id: str = Field(pattern=r"^COND-\d{6}$")
    axis: str
    status: CondStatus
    value: Optional[float] = None
    lo: Optional[float] = None
    hi: Optional[float] = None
    unit: Optional[str] = None
    text: Optional[str] = None                        # qualitative wording, verbatim
    source_quote: Optional[str] = None

    @model_validator(mode="after")
    def _r(self):
        if self.axis not in COND_AXES:
            raise ValueError(f"axis must be one of {COND_AXES}")
        s = self.status
        if s is CondStatus.UNKNOWN and any(x is not None for x in (self.value, self.lo, self.hi, self.text)):
            raise ValueError("UNKNOWN carries no value")
        if s is CondStatus.MEASURED and (self.value is None or not self.unit and self.axis not in ("pH", "aw")):
            raise ValueError("MEASURED needs a value (and a unit unless dimensionless)")
        if s is CondStatus.RANGE and (self.lo is None or self.hi is None or self.lo > self.hi):
            raise ValueError("RANGE needs lo <= hi")
        if s is CondStatus.QUALITATIVE and not self.text:
            raise ValueError("QUALITATIVE needs the verbatim text")
        if s is not CondStatus.UNKNOWN and not self.source_quote:
            raise ValueError("a stated condition needs a source_quote")
        return self


class SvarKind(str, enum.Enum):
    PHYSICAL = "PHYSICAL"
    CHEMICAL = "CHEMICAL"
    MOLECULAR = "MOLECULAR"
    SENSORY = "SENSORY"
    PROCEDURAL = "PROCEDURAL"


class StateVariable(BaseModel):
    model_config = F
    svar_id: str = Field(pattern=r"^SVAR-[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    kind: SvarKind
    dimension: Optional[str] = None                   # e.g. mass, temperature; None for categorical
    allowed_values: tuple[str, ...] = ()              # categorical states (e.g. raw, translucent, golden)
    definition: str = Field(min_length=1)

    @model_validator(mode="after")
    def _r(self):
        if not self.dimension and not self.allowed_values:
            raise ValueError("a state variable is either dimensional or categorical")
        return self


class ClaimStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    UNDERPOWERED = "UNDERPOWERED"
    WITHDRAWN = "WITHDRAWN"


class Claim(BaseModel):
    model_config = F
    clm_id: str = Field(pattern=r"^CLM-\d{4}$")
    text: str = Field(min_length=1)
    status: ClaimStatus
    experiment_id: Optional[str] = None               # EXP-/registry id
    artefact_path: Optional[str] = None
    artefact_sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    gate_verdict: Optional[str] = None
    evidence_ids: tuple[str, ...] = ()
    scope_note: str = ""                              # e.g. "dev only", "USDA R6 only"

    @model_validator(mode="after")
    def _r(self):
        if self.status in (ClaimStatus.SUPPORTED, ClaimStatus.NOT_SUPPORTED, ClaimStatus.UNDERPOWERED):
            if not (self.experiment_id and self.artefact_path and self.artefact_sha256 and self.gate_verdict):
                raise ValueError("a decided claim needs experiment_id, artefact_path, artefact_sha256 and gate_verdict")
        return self


class Warning_(BaseModel):
    model_config = F
    warn_id: str = Field(pattern=r"^WARN-\d{4}$")
    warn_class: str                                   # e.g. allergen, undercooking, acrylamide
    text: str = Field(min_length=1)
    authority_source_id: str                          # SNAP-/SRC- of an authority document
    authority_quote: str = Field(min_length=1)
    applies_to: tuple[str, ...] = Field(min_length=1)  # ING-/PROC-/ALLERGEN- ids

    @model_validator(mode="after")
    def _r(self):
        if not (is_valid(self.authority_source_id, "SNAP") or is_valid(self.authority_source_id, "SRC")):
            raise ValueError("authority_source_id must be a SNAP- or SRC- id")
        bad = [a for a in self.applies_to if not any(is_valid(a, p) for p in ("ING", "PROC", "ALLERGEN"))]
        if bad:
            raise ValueError(f"applies_to must be ING-/PROC-/ALLERGEN- ids: {bad}")
        return self


class Split(BaseModel):
    model_config = F
    split_id: str = Field(pattern=r"^SPLIT-[a-z0-9]+(-[a-z0-9]+)*$")
    dataset_id: str
    kind: str                                         # pair | ingredient | study | source_family | random | duplicate_safe
    seed: int
    group_key: str                                    # column(s) defining groups that never straddle a split
    assignment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frozen_utc: str

    @model_validator(mode="after")
    def _r(self):
        _ids([self.dataset_id], "DATASET", "dataset_id")
        if self.kind not in ("pair", "ingredient", "study", "source_family", "random", "duplicate_safe", "process"):
            raise ValueError("unknown split kind")
        return self


class Model(BaseModel):
    model_config = F
    model_id: str = Field(pattern=r"^MODEL-[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    version: str
    licence: str
    source_url: Optional[str] = None
    weights_sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    trained_on: tuple[str, ...] = ()                  # DATASET-/SPLIT- ids; empty for off-the-shelf
    selection: str = "dev"                            # where hyperparameters/checkpoints were chosen

    @model_validator(mode="after")
    def _r(self):
        if self.selection == "test":
            raise ValueError("model selection on test is not allowed for our models (DEC-040)")
        return self


class Dataset(BaseModel):
    model_config = F
    dataset_id: str = Field(pattern=r"^DATASET-[a-z0-9]+(-[a-z0-9]+)*$")
    path: str
    version: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rows: int = Field(ge=0)
    licence: str
    source_ids: tuple[str, ...] = Field(min_length=1)
