import copy
import json

import yaml

from screening_assurance.engine import diagnose, load_bundle
from screening_assurance.engine.model import finding_id
from screening_assurance.engine.risks import RISK_CATEGORIES
from screening_assurance.evals import compare_suites, run_suite
from screening_assurance.knowledge import load_pack

from conftest import CASES, EXAMPLES, RUN_AT, bundle_without_feedback, by_check, run


def sim(result, check, **kw):
    return by_check(result, check, **kw)[0].simulation


def test_every_screening_risk_category_is_produced(pack):
    seen = set()
    for name in ("REQ-SRE-0142", "REQ-LH-0217", "REQ-CSM-0388"):
        seen |= {f.risk_category for f in run(name, pack).findings if f.risk_category}
    assert seen == set(RISK_CATEGORIES)


def test_narrow_rule_simulation(pack):
    s = sim(run("REQ-SRE-0142", pack), "rule_narrower_than_requirement", rule_id="Q1")
    c = s["categories"]
    assert s["evaluable"] and s["proposed"]["terms"][:2] == ["site reliability engineer", "SRE"]
    assert "C-110" in c["excluded_by_supplied_rule"] and "C-110" in c["newly_eligible_for_review"]
    assert "C-104" in c["relevance_not_established"] and "C-104" not in c["newly_eligible_for_review"]
    assert s["sources"]["P-202"] == "pool" and "P-202" in c["still_fail_other_supplied_rules"]
    assert any("hypothetical" in x for x in s["limitations"])
    assert any("not a live ATS audit" in x for x in s["limitations"])


def test_irrelevant_candidates_are_never_made_eligible(pack):
    s = sim(run("REQ-SRE-0142", pack), "unstated_requirement_enforced", rule_id="Q7")
    assert {"C-105", "C-111", "C-112"} <= set(s["categories"]["relevance_not_established"])
    assert not {"C-104", "C-105", "C-111", "C-112"} & set(s["categories"]["newly_eligible_for_review"])


def test_unsupported_alternative_does_not_pass(pack):
    s = sim(run("REQ-SRE-0142", pack), "equivalent_path_blocked", rule_id="Q3")
    assert "C-105" in s["categories"]["excluded_by_supplied_rule"]
    assert "C-105" not in s["categories"]["would_pass_proposed_rule"]  # drills and participation only
    assert {"C-103", "C-106"} <= set(s["categories"]["newly_eligible_for_review"])
    # Pool records have no knockout answers: the supplied question cannot be evaluated for them.
    assert {"P-201", "P-202"} <= set(s["categories"]["evidence_insufficient"])


def test_blocked_pool_records_never_enter_simulations(pack):
    r = run("REQ-SRE-0142", pack)
    for f in r.findings:
        sources = (f.simulation or {}).get("sources") or {}
        assert not {"P-206", "P-207", "P-209"} & set(sources)


def test_mandatory_requirement_cannot_be_bypassed(pack):
    r = run("REQ-LH-0217", pack)
    prot = by_check(r, "mandatory_requirement_protected", rule_id="Q1")[0]
    assert prot.proposed_change is None and prot.simulation["proposed"] is None
    assert prot.risk_category == "mandatory_protected"
    s = sim(r, "experience_path_narrower", rule_id="Q2")
    assert "C-302" in s["categories"]["would_pass_proposed_rule"]
    assert "C-302" in s["categories"]["still_fail_mandatory_requirement"]
    assert "C-302" not in s["categories"]["newly_eligible_for_review"]
    assert "P-303" in s["categories"]["evidence_insufficient"]  # license cannot be verified
    for f in r.findings:
        cats = (f.simulation or {}).get("categories") or {}
        assert not set(cats.get("newly_eligible_for_review", [])) & {"C-302", "P-302"}


def test_unverifiable_impact_is_a_rule_level_risk(pack):
    r = diagnose(load_bundle(EXAMPLES / "REQ-RO-0455"), pack, run_at=RUN_AT)
    s = sim(r, "threshold_inconsistency", rule_id="Q1")
    assert s["evaluable"] is False and "rule-level risk" in s["reason"]


def test_unknown_cause_is_not_a_missed_candidate(pack):
    r = run("REQ-SRE-0142", pack)
    f = by_check(r, "unexplained_exclusions")[0]
    assert f.simulation["evaluable"] is False and "not as missed candidates" in f.simulation["reason"]
    for g in r.findings:
        cats = (g.simulation or {}).get("categories") or {}
        assert "C-114" not in cats.get("newly_eligible_for_review", [])


def test_candidate_level_before_after(pack):
    f = by_check(run("REQ-SRE-0142", pack), "candidate_review_opportunity", candidate_id="C-103")[0]
    assert f.risk_category == "equivalent_experience"
    rows = {x["rule"]: x for x in f.simulation["rules"]}
    assert rows["Q3"]["supplied"] is False and rows["Q3"]["proposed"] is True


def test_corrections_are_never_applied(pack):
    b = bundle_without_feedback("REQ-SRE-0142")
    before_req, before_pool = copy.deepcopy(b.requisition), copy.deepcopy(b.pool)
    before_pack = pack.checksum
    diagnose(b, pack, run_at=RUN_AT)
    assert b.requisition == before_req and b.pool == before_pool and pack.checksum == before_pack


def test_rejected_correction_leaves_the_combined_simulation(pack):
    b = bundle_without_feedback("REQ-SRE-0142")
    q7 = finding_id("REQ-SRE-0142", "unstated_requirement_enforced", "Q7")
    b.decisions = {"requisition_id": "REQ-SRE-0142", "decisions": [{
        "finding_id": q7, "disposition": "rejected", "rationale": "Datadog is required", "decided_by": "hm", "decided_at": "t"}]}
    r = diagnose(b, pack, run_at=RUN_AT)
    s = sim(r, "rule_narrower_than_requirement", rule_id="Q1")
    assert "C-110" not in s["categories"]["newly_eligible_for_review"]  # Q7 now stays in place for C-110
    assert any("rejected" in x for x in by_check(r, "unstated_requirement_enforced", rule_id="Q7")[0].simulation["limitations"])


def test_no_scores_in_simulations(pack):
    text = json.dumps([f.simulation for f in run("REQ-SRE-0142", pack).findings if f.simulation]).lower()
    assert "score" not in text and "%" not in text


def test_simulations_are_deterministic(pack):
    a = json.dumps([f.simulation for f in run("REQ-SRE-0142", pack).findings], sort_keys=True, default=str)
    b = json.dumps([f.simulation for f in run("REQ-SRE-0142", pack).findings], sort_keys=True, default=str)
    assert a == b


def test_eval_reports_screening_risk_metrics(pack):
    s = run_suite(CASES, pack)
    m = s["screening_risks"]
    assert "SYNTHETIC" in m["label"]
    assert m["expectations"] >= 17 and m["expectations_met"] == m["expectations"]
    assert m["irrelevant_surfaced"] == m["mandatory_violations"] == m["policy_violations"] == 0
    assert m["relevant_missed"] == 0 and m["needs_human_verification"] > 0


def test_eval_compare_catches_irrelevant_eligibility(pack, pack_copy):
    data = yaml.safe_load((pack_copy / "skills.yaml").read_text())
    iac = next(x for x in data["records"] if x["id"] == "skill.infrastructure-as-code")
    iac["alternate_names"].append("Bash")  # treats generic scripting as infrastructure as code
    (pack_copy / "skills.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    cmp = compare_suites(run_suite(CASES, pack), run_suite(CASES, load_pack(pack_copy)))
    assert not cmp["passed"]
    assert any(r.startswith("screening risks: irrelevant surfaced increased") for r in cmp["regressions"])
