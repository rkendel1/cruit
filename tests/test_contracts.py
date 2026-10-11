import pytest
import yaml

from screening_assurance.contracts import ContractError, SCHEMA_NAMES, load, schema_errors, validator

from conftest import EXAMPLES, ROOT


def test_all_schemas_are_valid_json_schema():
    for name in SCHEMA_NAMES:
        validator(name).check_schema(validator(name).schema)


@pytest.mark.parametrize("contract,path", [
    ("requisition", EXAMPLES / "REQ-SRE-0142" / "requisition.yaml"),
    ("candidates", EXAMPLES / "REQ-SRE-0142" / "candidates.yaml"),
    ("decisions", EXAMPLES / "REQ-SRE-0142" / "decisions.yaml"),
    ("outcomes", EXAMPLES / "REQ-SRE-0142" / "outcomes.yaml"),
    ("policy", ROOT / "examples" / "northwind" / "policy.yaml"),
])
def test_examples_satisfy_contracts(contract, path):
    load(contract, path)


def test_candidate_contract_rejects_protected_characteristics(tmp_path):
    data = yaml.safe_load((EXAMPLES / "REQ-SRE-0142" / "candidates.yaml").read_text())
    data["candidates"][0]["gender"] = "x"
    p = tmp_path / "candidates.yaml"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(ContractError) as exc:
        load("candidates", p)
    assert "protected-characteristic" in str(exc.value)


def test_candidate_contract_rejects_unknown_fields_and_requires_deidentification(tmp_path):
    data = yaml.safe_load((EXAMPLES / "REQ-SRE-0142" / "candidates.yaml").read_text())
    data["authorization"]["de_identified"] = False
    data["candidates"][0]["linkedin_url"] = "https://example.com"
    errs = schema_errors("candidates", data)
    assert any("de_identified" in e for e in errs)
    assert any("linkedin_url" in e for e in errs)


def test_requisition_must_declare_inputs_received():
    data = yaml.safe_load((EXAMPLES / "REQ-SRE-0142" / "requisition.yaml").read_text())
    del data["inputs_received"]
    assert any("inputs_received" in e for e in schema_errors("requisition", data))


def test_decisions_require_rationale():
    data = {"requisition_id": "R", "decisions": [{"finding_id": "x", "disposition": "accepted", "rationale": "",
                                                    "decided_by": "a", "decided_at": "t"}]}
    assert schema_errors("decisions", data)
