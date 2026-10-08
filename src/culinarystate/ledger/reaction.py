r"""
T18 / SSOT P11 — reaction ledger (RXN-). A typed, MEASURED relation between a molecule (or
molecule class) and a food under a process, populated ONLY from verified evidence rows.

What it is NOT: a balanced chemical network. Complex food processes are recorded as observed
transformations of named analytes; mechanism claims need their own evidence (§242.7, law B1).

  relation         FORMED | DEGRADED | LEACHED | VOLATILIZED | OXIDIZED | ISOMERIZED |
                   DENATURED | GELATINIZED | FERMENTED | UNKNOWN_TRANSFORMATION
  direction_only   the evidence shows the direction (e.g. 'decreased') but not the mechanism
                   → relation must be UNKNOWN_TRANSFORMATION unless the source names it
"""
from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Relation(str, enum.Enum):
    FORMED = "FORMED"
    DEGRADED = "DEGRADED"
    LEACHED = "LEACHED"
    VOLATILIZED = "VOLATILIZED"
    OXIDIZED = "OXIDIZED"
    ISOMERIZED = "ISOMERIZED"
    DENATURED = "DENATURED"
    GELATINIZED = "GELATINIZED"
    FERMENTED = "FERMENTED"
    UNKNOWN_TRANSFORMATION = "UNKNOWN_TRANSFORMATION"


class MechanismBasis(str, enum.Enum):
    SOURCE_STATED = "SOURCE_STATED"        # the cited source names the mechanism for this food/process
    SOURCE_SUGGESTED = "SOURCE_SUGGESTED"  # the source hedges ("may be due to")
    NONE = "NONE"                          # only a measured change; no mechanism claimed


class ReactionRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rxn_id: str = Field(pattern=r"^RXN-\d{6}$")
    evidence_ids: tuple[str, ...] = Field(min_length=1)            # EVD- rows that measured the change
    ingredient_id: str = Field(pattern=r"^ING-[a-z0-9]+(-[a-z0-9]+)*$")
    process_ids: tuple[str, ...] = Field(min_length=1)
    subject: str = Field(min_length=1)                             # analyte as named in the source
    subject_mol_id: Optional[str] = Field(default=None, pattern=r"^MOL-[A-Z0-9-]+$")
    product: Optional[str] = None                                  # only for FORMED/ISOMERIZED/OXIDIZED when measured
    product_mol_id: Optional[str] = Field(default=None, pattern=r"^MOL-[A-Z0-9-]+$")
    relation: Relation
    mechanism_basis: MechanismBasis
    mechanism_quote: Optional[str] = None                          # verbatim span when SOURCE_STATED/SUGGESTED
    conditions_ref: Optional[str] = None                           # pointer to the evidence row's condition block
    notes: str = ""

    @model_validator(mode="after")
    def _rules(self):
        if not all(e.startswith("EVD-") for e in self.evidence_ids):
            raise ValueError("evidence_ids must be EVD- ids")
        if self.relation is not Relation.UNKNOWN_TRANSFORMATION and self.mechanism_basis is MechanismBasis.NONE:
            raise ValueError("a named relation needs a source-stated or source-suggested mechanism; "
                             "use UNKNOWN_TRANSFORMATION for a measured change without one")
        if self.mechanism_basis is not MechanismBasis.NONE and not self.mechanism_quote:
            raise ValueError("mechanism_basis other than NONE requires a verbatim mechanism_quote")
        if (self.product or self.product_mol_id) and self.relation not in (
                Relation.FORMED, Relation.ISOMERIZED, Relation.OXIDIZED):
            raise ValueError("a product is only recorded for FORMED / ISOMERIZED / OXIDIZED")
        return self
