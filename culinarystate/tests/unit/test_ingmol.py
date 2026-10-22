import pytest
from pydantic import ValidationError

from culinarystate.ledger.ingmol import IngMolRelation as R, IngMolRow

B = dict(imap_id="IMAP-IM-000001", ingredient_id="ING-tomato", mol_id="MOL-OAIJSZIZWZSQBC-GYZMGTAESA-N",
         source_ids=("SRC-0101",), provenance="EXPLICIT_SOURCE")


def test_presence_has_no_value():
    assert IngMolRow(**B, relation=R.PRESENCE).relation is R.PRESENCE
    with pytest.raises(ValidationError):
        IngMolRow(**B, relation=R.PRESENCE, value=3.0)


def test_concentration_needs_value_unit_basis():
    with pytest.raises(ValidationError):
        IngMolRow(**B, relation=R.CONCENTRATION, value=3.0, unit="mg/100 g")
    assert IngMolRow(**B, relation=R.CONCENTRATION, value=3.0, unit="mg/100 g", basis="WET").value == 3.0


def test_sensory_needs_descriptor_and_quote_and_is_never_inferred_from_presence():
    with pytest.raises(ValidationError):
        IngMolRow(**B, relation=R.SENSORY_ASSOCIATION, descriptor="green")
    with pytest.raises(ValidationError):
        IngMolRow(**B, relation=R.PRESENCE, descriptor="green")


def test_process_transition_points_to_evidence():
    with pytest.raises(ValidationError):
        IngMolRow(**B, relation=R.PROCESS_TRANSITION)
    assert IngMolRow(**{**B, "source_ids": ("EVD-000001",)}, relation=R.PROCESS_TRANSITION)
