from screening_assurance.contracts import ContractError, load, validate_data
from screening_assurance.engine import diagnose, discover, load_bundle
from screening_assurance.evals.discovery_eval import run_discovery_suite

import pytest
import yaml

from conftest import EXAMPLES, ROOT, RUN_AT

DISCOVERY_CASES = ROOT / "evals" / "discovery"


def run_discovery(name, pack, as_of="2026-10-10"):
    b = load_bundle(EXAMPLES / name)
    b.decisions = None
    b.outcomes = None
    d = diagnose(b, pack, run_at=RUN_AT)
    return discover(b, pack, d, as_of=as_of)


def groups(res):
    return {e.candidate_id: e.group for e in res.entries}


def entry(res, cid):
    return next(e for e in res.entries if e.candidate_id == cid)


def test_fixture_groups(pack):
    g = groups(run_discovery("REQ-SRE-0142", pack))
    assert g["P-201"] == "direct"            # direct evidence
    assert g["P-202"] == "direct"            # different title, relevant evidence
    assert g["P-203"] == "transferable"      # plausibly transferable, needs review
    assert g["P-204"] == "not_surfaced"      # looks similar, lacks necessary evidence
    assert g["P-205"] == "insufficient"      # partial record
    assert g["P-206"] == "blocked"           # stale
    assert g["P-207"] == "blocked"           # unauthorized use
    assert g["P-209"] == "blocked"           # authorization expired
    assert g["C-101"] == "active_workflow"


def test_blocked_records_expose_no_evidence(pack):
    res = run_discovery("REQ-SRE-0142", pack)
    for cid in ("P-206", "P-207", "P-209"):
        e = entry(res, cid)
        assert e.requirements == [] and e.why == [] and e.reason


def test_mandatory_requirement_never_relaxed(pack):
    res = run_discovery("REQ-LH-0217", pack)
    p302 = entry(res, "P-302")
    assert p302.group == "not_surfaced"
    assert p302.mandatory_issues[0]["issue"] == "not_satisfied"
    p303 = entry(res, "P-303")  # credentials not supplied: cannot verify, so only 'insufficient'
    assert p303.group == "insufficient"
    assert p303.mandatory_issues[0]["issue"] == "cannot_verify"
    for e in res.entries:
        if e.group in ("direct", "transferable"):
            assert not e.mandatory_issues


def test_surfaced_entries_explain_themselves(pack):
    res = run_discovery("REQ-SRE-0142", pack)
    for e in res.entries:
        if e.group in ("direct", "transferable", "insufficient"):
            assert e.why and e.source["record_ref"] and e.supported
            assert e.screening["basis"]
            assert e.constraints
    c102 = entry(res, "C-102")
    assert [x["rule"] for x in c102.screening["excluded_by"]] == ["Q1", "Q2", "Q5"]
    assert c102.screening["established"] is True
    p201 = entry(res, "P-201")
    assert p201.screening["applied_to_requisition"] is False and p201.screening["excluded_by"] == []
    assert any("not established" in c for c in p201.constraints)


def test_prior_application_is_not_permission_to_contact(pack):
    res = run_discovery("REQ-SRE-0142", pack)
    assert any("Do not contact" in c for c in entry(res, "P-208").constraints)
    assert any("Confirm current consent" in c for c in entry(res, "P-202").constraints)
    assert "permission to contact" in " ".join(res.limitations)


def test_knowledge_upgrade_improves_discovery_without_relaxing_mandatory(pack, pack_100):
    old, new = run_discovery("REQ-SRE-0142", pack_100), run_discovery("REQ-SRE-0142", pack)
    assert groups(old)["P-208"] == "not_surfaced" and groups(new)["P-208"] == "direct"
    lh_old, lh_new = run_discovery("REQ-LH-0217", pack_100), run_discovery("REQ-LH-0217", pack)
    assert groups(lh_old)["P-302"] == groups(lh_new)["P-302"] == "not_surfaced"


def test_no_scores_or_rankings(pack):
    d = run_discovery("REQ-SRE-0142", pack).as_dict()
    text = str(d).lower()
    assert "score" not in text.replace("no ranking or match score", "")
    assert "%" not in str([e["why"] for e in d["entries"]])


def test_discovery_is_deterministic(pack):
    assert run_discovery("REQ-SRE-0142", pack).as_dict() == run_discovery("REQ-SRE-0142", pack).as_dict()


def test_freshness_depends_on_assessment_date(pack):
    later = groups(run_discovery("REQ-SRE-0142", pack, as_of="2028-03-01"))
    assert later["P-203"] == "blocked"  # evidence from 2026-02-20 exceeds 730 days by then


def test_synthetic_suite_reports_required_metrics(pack):
    s = run_discovery_suite(DISCOVERY_CASES, pack)
    assert "SYNTHETIC" in s["label"]
    m = s["metrics"]
    for key in ("relevant_surfaced", "relevant_missed", "irrelevant_surfaced", "mandatory_violations",
                "needs_human_verification", "recruiter_dispositions", "recruiter_minutes"):
        assert key in m
    assert m["mandatory_violations"] == m["blocked_violations"] == m["irrelevant_surfaced"] == 0
    assert m["group_mismatches"] == 0


def test_pool_contract_rejects_identity_and_contact_details():
    data = yaml.safe_load((EXAMPLES / "REQ-SRE-0142" / "candidate-pool.yaml").read_text())
    bad = yaml.safe_load(yaml.safe_dump(data))
    bad["candidates"][0]["email"] = "x@example.com"
    with pytest.raises(ContractError):
        validate_data("candidate_pool", bad)
    bad = yaml.safe_load(yaml.safe_dump(data))
    bad["candidates"][0]["experience"][0]["summary"] += " Reach me at 401-555-0199."
    with pytest.raises(ContractError) as exc:
        validate_data("candidate_pool", bad)
    assert "phone" in str(exc.value)
    bad = yaml.safe_load(yaml.safe_dump(data))
    bad["authorization"]["de_identified"] = False
    with pytest.raises(ContractError):
        validate_data("candidate_pool", bad)


def test_example_pools_satisfy_contract():
    for name in ("REQ-SRE-0142", "REQ-LH-0217"):
        load("candidate_pool", EXAMPLES / name / "candidate-pool.yaml")
