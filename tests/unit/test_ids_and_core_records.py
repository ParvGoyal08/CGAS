import pytest
from pydantic import ValidationError

from culinarystate.ids import is_valid, prefix_of
from culinarystate.ledger.core_records import (Claim, ClaimStatus, CondStatus, Condition, Measurement, Model, Split,
                                               StateVariable, SvarKind, Warning_)

H = "a" * 64


@pytest.mark.parametrize("i,p", [("EVD-000123", "EVD"), ("ING-sweet-potato", "ING"), ("SNAP-FDC-0001", "SNAP"),
                                 ("LITC1-000001", "LITC"), ("MOL-ZNOVTXRBGFNYRX-ABLWVSNPSA-N", "MOL"),
                                 ("IMAP-IM-000001", "IMAP"), ("STATE-ENTITY-F01-butter-v2", "STATE"), ("RS-08-02", "RS")])
def test_prefixes(i, p):
    assert prefix_of(i) == p


@pytest.mark.parametrize("bad", ["EVD-12", "ING-Sweet Potato", "FOO-1", "evd-000001", "MOL-abc", ""])
def test_malformed(bad):
    assert not is_valid(bad)


def test_condition_unknown_carries_nothing_and_stated_needs_quote():
    assert Condition(cond_id="COND-000001", axis="T", status=CondStatus.UNKNOWN).value is None
    with pytest.raises(ValidationError):
        Condition(cond_id="COND-000002", axis="T", status=CondStatus.UNKNOWN, value=100)
    with pytest.raises(ValidationError):
        Condition(cond_id="COND-000003", axis="T", status=CondStatus.MEASURED, value=100, unit="degC")
    Condition(cond_id="COND-000004", axis="T", status=CondStatus.MEASURED, value=100, unit="degC", source_quote="boiled at 100 °C")
    with pytest.raises(ValidationError):
        Condition(cond_id="COND-000005", axis="colour", status=CondStatus.UNKNOWN)


def test_claim_needs_experiment_artefact_and_verdict():
    Claim(clm_id="CLM-0001", text="x", status=ClaimStatus.DRAFT)
    with pytest.raises(ValidationError):
        Claim(clm_id="CLM-0002", text="x", status=ClaimStatus.SUPPORTED, experiment_id="EXP-del2")
    Claim(clm_id="CLM-0003", text="x", status=ClaimStatus.UNDERPOWERED, experiment_id="EXP-del2",
          artefact_path="experiments/DEL2/runs/x/verdicts.json", artefact_sha256=H, gate_verdict="card §X")


def test_warning_needs_authority_and_valid_targets():
    with pytest.raises(ValidationError):
        Warning_(warn_id="WARN-0001", warn_class="allergen", text="t", authority_source_id="flavordb",
                 authority_quote="q", applies_to=("ING-cashew",))
    Warning_(warn_id="WARN-0002", warn_class="allergen", text="t", authority_source_id="SNAP-0004",
             authority_quote="Tree nut and their products", applies_to=("ALLERGEN-03",))


def test_measurement_method_needs_quote_and_model_never_selected_on_test():
    with pytest.raises(ValidationError):
        Measurement(meas_id="MEAS-000001", study_id="STUDY-000001", analyte="vitamin C", method="HPLC")
    with pytest.raises(ValidationError):
        Model(model_id="MODEL-deberta-base", name="x", version="1", licence="MIT", selection="test")


def test_svar_and_split():
    with pytest.raises(ValidationError):
        StateVariable(svar_id="SVAR-colour", name="colour", kind=SvarKind.SENSORY, definition="d")
    StateVariable(svar_id="SVAR-onion-colour", name="onion colour", kind=SvarKind.SENSORY,
                  allowed_values=("raw", "translucent", "golden", "brown"), definition="d")
    with pytest.raises(ValidationError):
        Split(split_id="SPLIT-x", dataset_id="EVD-000001", kind="pair", seed=1, group_key="code",
              assignment_sha256=H, frozen_utc="t")
