r"""
T17 / SSOT P3 — ingredient ↔ molecule relations (IMAP- rows of kind INGREDIENT_MOLECULE).

The existing imap_v0.csv maps USDA *targets* to molecules (identity). This schema covers
ingredient ↔ molecule EVIDENCE joins, with four relation types kept strictly separate:

  PRESENCE              the molecule was detected in the food (qualitative)
  CONCENTRATION         a measured amount (value + unit + basis), from a source table
  SENSORY_ASSOCIATION   a source links the molecule to an aroma/taste IN THIS FOOD
  PROCESS_TRANSITION    the amount changes under a process (points to EVD-/RXN- rows)

A sensory association is never inferred from presence, and presence never from a database
category; each row cites its own source (SRC-/EVD-) and provenance.
"""
from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IngMolRelation(str, enum.Enum):
    PRESENCE = "PRESENCE"
    CONCENTRATION = "CONCENTRATION"
    SENSORY_ASSOCIATION = "SENSORY_ASSOCIATION"
    PROCESS_TRANSITION = "PROCESS_TRANSITION"


class IngMolRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    imap_id: str = Field(pattern=r"^IMAP-IM-\d{6}$")
    ingredient_id: str = Field(pattern=r"^ING-[a-z0-9]+(-[a-z0-9]+)*$")
    mol_id: str = Field(pattern=r"^(MOL-[A-Z0-9-]+|MOLCLASS-[a-z0-9-]+)$")   # class = e.g. 'total phenolics'
    relation: IngMolRelation
    source_ids: tuple[str, ...] = Field(min_length=1)                       # SRC-/EVD-/RXN- ids
    provenance: str                                                          # EXPLICIT_SOURCE | EXTERNAL_VERIFIED | INFERRED_LLM …
    value: Optional[float] = None
    unit: Optional[str] = None
    basis: Optional[str] = None                                              # WET | DRY | UNSPECIFIED
    descriptor: Optional[str] = None                                         # sensory term, only for SENSORY_ASSOCIATION
    source_quote: Optional[str] = None

    @model_validator(mode="after")
    def _rules(self):
        if self.relation is IngMolRelation.CONCENTRATION:
            if self.value is None or not self.unit or not self.basis:
                raise ValueError("CONCENTRATION needs value, unit and basis")
        elif self.value is not None:
            raise ValueError("only CONCENTRATION rows carry a value")
        if self.relation is IngMolRelation.SENSORY_ASSOCIATION and not (self.descriptor and self.source_quote):
            raise ValueError("SENSORY_ASSOCIATION needs a descriptor and a verbatim source quote")
        if self.descriptor and self.relation is not IngMolRelation.SENSORY_ASSOCIATION:
            raise ValueError("descriptor is only for SENSORY_ASSOCIATION")
        if self.relation is IngMolRelation.PROCESS_TRANSITION and not any(
                s.startswith(("EVD-", "RXN-")) for s in self.source_ids):
            raise ValueError("PROCESS_TRANSITION must point to EVD- or RXN- rows")
        return self
