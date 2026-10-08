import pytest
from pydantic import ValidationError

from culinarystate.ledger.reaction import MechanismBasis, ReactionRow, Relation

BASE = dict(rxn_id="RXN-000001", evidence_ids=("EVD-000123",), ingredient_id="ING-broccoli",
            process_ids=("PROC-boil",), subject="vitamin C")


def test_measured_change_without_mechanism_is_unknown_transformation():
    r = ReactionRow(**BASE, relation=Relation.UNKNOWN_TRANSFORMATION, mechanism_basis=MechanismBasis.NONE)
    assert r.relation is Relation.UNKNOWN_TRANSFORMATION


def test_named_relation_needs_a_quoted_mechanism():
    with pytest.raises(ValidationError):
        ReactionRow(**BASE, relation=Relation.LEACHED, mechanism_basis=MechanismBasis.NONE)
    with pytest.raises(ValidationError):
        ReactionRow(**BASE, relation=Relation.LEACHED, mechanism_basis=MechanismBasis.SOURCE_STATED)
    ok = ReactionRow(**BASE, relation=Relation.LEACHED, mechanism_basis=MechanismBasis.SOURCE_STATED,
                     mechanism_quote="losses were attributed to leaching into the cooking water")
    assert ok.relation is Relation.LEACHED


def test_no_reaction_without_evidence():
    with pytest.raises(ValidationError):
        ReactionRow(**{**BASE, "evidence_ids": ()}, relation=Relation.UNKNOWN_TRANSFORMATION,
                    mechanism_basis=MechanismBasis.NONE)


def test_product_only_for_formation_like_relations():
    with pytest.raises(ValidationError):
        ReactionRow(**BASE, relation=Relation.LEACHED, mechanism_basis=MechanismBasis.SOURCE_STATED,
                    mechanism_quote="q", product="something")
