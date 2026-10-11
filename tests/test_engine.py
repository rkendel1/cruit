import copy
import json

from screening_assurance.engine import diagnose, load_bundle
from screening_assurance.engine.model import finding_id

from conftest import EXAMPLES, RUN_AT, bundle_without_feedback, by_check, run


def surfaced(result):
    return sorted(c.candidate_id for c in result.candidates if c.surfaced)


# ------------------------------------------------------------------ design checks
def test_sre_level1_inconsistencies(pack):
    r = run("REQ-SRE-0142", pack)
    lvl1 = {(f.check, f.rule_id) for f in r.findings if f.evidence_level == 1}
    assert ("threshold_inconsistency", "Q2") in lvl1
    assert ("preferred_enforced_as_knockout", "Q4") in lvl1
    assert ("preferred_enforced_as_knockout", "Q6") in lvl1
    assert ("equivalent_path_blocked", "Q3") in lvl1
    assert ("unstated_requirement_enforced", "Q7") in lvl1
    assert ("rule_narrower_than_requirement", "Q5") in lvl1
    # Knowledge-based findings are never Level 1
    assert all(f.evidence_level == 2 for f in r.findings if f.check in ("literal_term_missing_variants", "experience_path_narrower"))


def test_every_finding_is_traceable(pack):
    r = run("REQ-SRE-0142", pack)
    for f in r.findings:
        assert f.source_refs, f.id
        assert f.knowledge_version == pack.fingerprint
        assert f.proposed_action and f.expected_benefit and f.tradeoffs
        assert f.confidence in ("high", "medium", "low")
        assert f.disposition["status"] == "pending"


def test_threshold_correction_is_simulated_not_applied(pack):
    b = bundle_without_feedback("REQ-SRE-0142")
    before = copy.deepcopy(b.requisition)
    r = diagnose(b, pack, run_at=RUN_AT)
    assert b.requisition == before, "engine must never modify the employer's configuration"
    f = by_check(r, "threshold_inconsistency", rule_id="Q2")[0]
    assert f.proposed_change == {"years": 5}
    assert set(f.affected_candidates) == {"C-108", "C-109"}


def test_variants_respect_ambiguity_notes(pack):
    r = run("REQ-CSM-0388", pack)
    f = by_check(r, "literal_term_missing_variants", rule_id="Q1")[0]
    assert "client success" in f.proposed_action
    assert any("Certified ScrumMaster" in l for l in f.limitations)


def test_unverified_requirement_flagged_not_removed(pack):
    r = run("REQ-SRE-0142", pack)
    f = by_check(r, "unverified_necessity", requirement_id="R6")[0]
    assert f.category == "unverified_assumption" and f.proposed_change is None


# ------------------------------------------------------------------ candidates
def test_sre_candidates_surfaced(pack):
    r = run("REQ-SRE-0142", pack)
    assert surfaced(r) == ["C-102", "C-103", "C-106", "C-108", "C-109", "C-110"]


def test_nontraditional_candidate_uses_equivalency_with_conditions(pack):
    r = run("REQ-SRE-0142", pack)
    c = next(c for c in r.candidates if c.candidate_id == "C-103")
    r2 = next(rv for rv in c.requirements if rv.requirement_id == "R2")
    assert r2.status == "alternative_path"
    assert r2.paths == ["equivalency:eq.incident-management.operational-crisis-response"]
    assert r2.verify_next, "equivalency validation steps must be passed to the recruiter"
    opp = by_check(r, "candidate_review_opportunity", candidate_id="C-103")[0]
    assert opp.confidence == "medium"
    assert any("Qualification has not been established" in l for l in opp.limitations)


def test_participation_only_evidence_does_not_count(pack):
    r = run("REQ-SRE-0142", pack)
    c = next(c for c in r.candidates if c.candidate_id == "C-105")
    assert not c.surfaced
    r2 = next(rv for rv in c.requirements if rv.requirement_id == "R2")
    assert r2.status == "not_evidenced"


def test_transferable_skills_are_not_over_applied(pack):
    r = run("REQ-SRE-0142", pack)
    c104 = next(c for c in r.candidates if c.candidate_id == "C-104")
    assert not c104.surfaced and "Q5" in c104.reason  # strong incident lead, but no IaC
    c107 = next(c for c in r.candidates if c.candidate_id == "C-107")
    assert not c107.surfaced  # conventional title, below the posted threshold


def test_protected_license_is_never_relaxed(pack):
    r = run("REQ-LH-0217", pack)
    assert surfaced(r) == ["C-303"]
    q1 = {f.check for f in r.findings if f.rule_id == "Q1" and f.proposed_change}
    assert q1 == {"literal_term_missing_variants"}  # spelling variants are the only correction proposed
    protected = by_check(r, "mandatory_requirement_protected", rule_id="Q1")[0]
    assert protected.proposed_change is None and "C-302" in protected.affected_candidates
    assert "C-303" not in protected.affected_candidates  # holds the license under another spelling
    rule = next(x for x in r.rules if x.id == "Q1")
    assert rule.status == "protected"
    c302 = next(c for c in r.candidates if c.candidate_id == "C-302")
    assert not c302.surfaced and "protected" in c302.reason


def test_employer_policy_overrides_general_knowledge(pack):
    r = run("REQ-CSM-0388", pack)
    c208 = next(c for c in r.candidates if c.candidate_id == "C-208")
    assert not c208.surfaced
    notes = " ".join(n for rv in c208.requirements for n in rv.notes)
    assert "rejected by employer policy" in notes


def test_skill_combination_alone_does_not_surface(pack):
    r = run("REQ-CSM-0388", pack)
    c205 = next(c for c in r.candidates if c.candidate_id == "C-205")
    r5 = next(rv for rv in c205.requirements if rv.requirement_id == "R5")
    assert r5.paths == ["combination:combo.cross-functional-problem-solving"]
    assert not c205.surfaced


def test_unexplained_exclusions_are_disclosed(pack):
    r = run("REQ-SRE-0142", pack)
    f = by_check(r, "unexplained_exclusions")[0]
    assert f.affected_candidates == ["C-113", "C-114"] and f.category == "input_limitation"
    c114 = next(e for e in f.evidence if e["source"] == "candidate:C-114")
    assert "Q3" in c114["text"]  # the rule that could not be evaluated is named
    assert f.simulation["evaluable"] is False and f.risk_category == "insufficient_or_unknown"


def test_documented_rules_are_disclosed_as_unverified(pack):
    r = run("REQ-CSM-0388", pack)
    assert any("not verified ATS configuration" in l for l in r.limitations)


def test_prepublication_mode_without_candidates(pack):
    b = load_bundle(EXAMPLES / "REQ-RO-0455")
    r = diagnose(b, pack, run_at=RUN_AT)
    assert not r.candidates
    assert not by_check(r, "candidate_review_opportunity")
    assert by_check(r, "threshold_inconsistency", rule_id="Q1")
    assert any("candidate-pool assurance was not performed" in l for l in r.limitations)


# ------------------------------------------------------------------ human review loop
def test_finding_ids_are_stable_across_knowledge_versions(pack, pack_100):
    a = {f.id for f in run("REQ-SRE-0142", pack).findings}
    b = {f.id for f in run("REQ-SRE-0142", pack_100).findings}
    assert finding_id("REQ-SRE-0142", "threshold_inconsistency", "Q2", "R1") in a & b


def test_results_are_reproducible(pack):
    a = json.dumps(run("REQ-SRE-0142", pack).as_dict(), sort_keys=True, default=str)
    b = json.dumps(run("REQ-SRE-0142", pack).as_dict(), sort_keys=True, default=str)
    assert a == b


def test_rejecting_a_finding_withdraws_its_correction(pack):
    b = bundle_without_feedback("REQ-SRE-0142")
    fid = finding_id("REQ-SRE-0142", "unstated_requirement_enforced", "Q7")
    b.decisions = {"requisition_id": "REQ-SRE-0142", "decisions": [{
        "finding_id": fid, "disposition": "rejected", "rationale": "Datadog is genuinely required",
        "decided_by": "hm", "decided_at": "t"}]}
    r = diagnose(b, pack, run_at=RUN_AT)
    assert "C-110" not in surfaced(r)  # C-110 was only unlocked by removing Q7
    assert next(f for f in r.findings if f.id == fid).disposition["status"] == "rejected"


def test_reclassification_decision_feeds_back(pack):
    r = run("REQ-CSM-0388", pack, with_feedback=True)
    assert "C-207" in surfaced(r)
    assert by_check(r, "preferred_enforced_as_knockout", rule_id="Q3")
    assert any("R4 treated as 'preferred'" in l for l in r.limitations)
    # The original finding remains, carrying the human decision
    f = by_check(r, "unverified_necessity", requirement_id="R4")[0]
    assert f.disposition["status"] == "reclassified_preferred"


def test_measurement_separates_measured_and_estimated(pack):
    r = run("REQ-SRE-0142", pack, with_feedback=True)
    m = r.measurement
    assert m["measured"]["additional_reviews"] == 5
    assert m["measured"]["confirmed_meets_requirements"] == 4
    assert m["estimated"]["label"].startswith("ESTIMATED")
    assert m["comparison_method"]
    level3 = by_check(r, "measured_impact")
    assert len(level3) == 1 and level3[0].evidence_level == 3
    assert not m["unknown_finding_refs"]
