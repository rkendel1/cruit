"""Forward screening assurance: screening-risk categories and before/after correction simulation.

Built entirely on existing mechanisms:
  * design findings and their correction patches (checks.py)
  * deterministic rule simulation (rules.evaluate_rule / apply_patches)
  * requirement evidence and the protected-requirement guardrail (candidates.requirement_evidence)
  * the combined-correction candidate assessment (candidates.assess_candidates)
  * pool authorization and freshness (pool.py)

Nothing here changes the requisition, the knowledge pack or any ATS configuration. Simulations
report categories of candidates; they never call anyone qualified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .candidates import requirement_evidence
from .checks import CheckOutput
from .interpret import Context
from .model import CandidateAssessment, Finding, SourceRef, finding_id
from .pool import pool_block_reason
from .rules import apply_patches, evaluate_rule

# The six screening-risk categories, mapped onto the engine's existing checks.
RISK_CATEGORIES = {
    "preferred_as_knockout": "Preferred criterion enforced as a knockout",
    "rule_narrower": "Rule narrower than the requirement",
    "terminology": "Terminology not recognized",
    "equivalent_experience": "Potentially equivalent experience",
    "mandatory_protected": "Mandatory requirement protected",
    "insufficient_or_unknown": "Insufficient evidence or unknown cause",
}
CHECK_RISK = {
    "preferred_enforced_as_knockout": "preferred_as_knockout",
    "rule_narrower_than_requirement": "rule_narrower",
    "threshold_inconsistency": "rule_narrower",
    "experience_path_narrower": "rule_narrower",
    "credential_stricter_than_requirement": "rule_narrower",
    "unstated_requirement_enforced": "rule_narrower",
    "literal_term_missing_variants": "terminology",
    "equivalent_path_blocked": "equivalent_experience",
    "alternatives_not_considered": "equivalent_experience",
    "mandatory_requirement_protected": "mandatory_protected",
    "unexplained_exclusions": "insufficient_or_unknown",
    "unverified_necessity": "insufficient_or_unknown",
}
SIM_CATEGORIES = (
    "excluded_by_supplied_rule",
    "would_pass_proposed_rule",
    "still_fail_mandatory_requirement",
    "evidence_insufficient",
    "relevance_not_established",
    "still_fail_other_supplied_rules",
    "newly_eligible_for_review",
)
SIM_LABELS = {
    "excluded_by_supplied_rule": "Excluded by the supplied rule",
    "would_pass_proposed_rule": "Would pass the proposed rule",
    "still_fail_mandatory_requirement": "Still fail a mandatory requirement",
    "evidence_insufficient": "Evidence insufficient to tell",
    "relevance_not_established": "Pass the rule, but relevance not established",
    "still_fail_other_supplied_rules": "Relevant evidence, but still fail other supplied rules",
    "newly_eligible_for_review": "Newly eligible for human review",
}
COVERED = ("evidenced", "alternative_path", "pending_clarification")


@dataclass
class Subject:
    """A candidate record that supplied rules can be simulated against (no evidence text is stored)."""

    id: str
    source: str  # applicant | pool
    cand: dict[str, Any]
    mandatory: str | None = None          # unmet | unverifiable | None
    mandatory_detail: str = ""
    relevant: bool = False
    partial: bool = False
    gaps: list[str] = field(default_factory=list)
    assessment: CandidateAssessment | None = None


def build_population(
    ctx: Context,
    checks: CheckOutput,
    applicants: list[dict[str, Any]],
    assessments: list[CandidateAssessment],
    pool: dict[str, Any] | None,
    as_of: date,
) -> list[Subject]:
    unverified = {f.requirement_id for f in checks.findings if f.check == "unverified_necessity"
                  and f.disposition.get("status") in ("pending", "deferred", "requested_evidence")}
    by_assessment = {a.candidate_id: a for a in assessments}
    out: list[Subject] = []
    seen: set[str] = set()
    for cand in applicants:
        seen.add(cand["id"])
        out.append(_subject(ctx, cand, "applicant", {"experience": "complete", "credentials": "complete"},
                            unverified, by_assessment.get(cand["id"])))
    for cand in (pool or {}).get("candidates", []):
        if cand["id"] in seen:
            continue
        blocked, _ = pool_block_reason(cand, pool, as_of)
        if blocked:  # blocked records never enter simulations
            continue
        out.append(_subject(ctx, cand, "pool", cand["evidence_coverage"], unverified, None))
    return out


def _subject(ctx: Context, cand: dict[str, Any], source: str, coverage: dict[str, str], unverified: set[str],
             assessment: CandidateAssessment | None) -> Subject:
    s = Subject(id=cand["id"], source=source, cand=cand, assessment=assessment,
                partial=coverage.get("experience") != "complete")
    for req in ctx.requisition["requirements"]:
        if req["stated_as"] != "required":
            continue
        rv = requirement_evidence(ctx, cand, req, unverified)
        if rv.status == "protected_missing":
            if coverage.get("credentials") == "complete":
                s.mandatory, s.mandatory_detail = "unmet", f"{req['id']} (protected) not among the supplied credentials"
            elif s.mandatory != "unmet":
                s.mandatory, s.mandatory_detail = "unverifiable", f"{req['id']} (protected) cannot be verified: credentials not supplied"
        elif rv.status not in COVERED:
            s.gaps.append(req["id"])
    s.relevant = not s.gaps
    return s


def _config_note(ctx: Context) -> str:
    cfg = ctx.requisition["inputs_received"]["screening_configuration"]
    return {
        "ats_export_verified": "Rules come from a supplied ATS configuration export; this is not a live ATS audit.",
        "ats_api_verified": "Rules were supplied as read from the ATS at export time; this is not a continuous live audit.",
        "recruiter_documentation": "Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.",
        "not_supplied": "No screening configuration was supplied.",
    }[cfg]


def simulate_correction(ctx: Context, rule: dict[str, Any], patch: dict[str, Any] | None,
                        population: list[Subject], other_proposed: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Compare the supplied rule with one proposed correction across the population. Never applies anything."""
    if not population:
        return {"evaluable": False, "reason": "No candidate evidence was supplied, so candidate impact cannot be "
                "verified. This remains a rule-level risk.", "limitations": [_config_note(ctx)]}
    spec = apply_patches(rule, [patch]) if patch is not None else None
    cats: dict[str, list[str]] = {k: [] for k in SIM_CATEGORIES}
    notes: dict[str, str] = {}
    basis: dict[str, str] = {}
    other_rules = [r for r in ctx.requisition["screening_rules"] if r["id"] != rule["id"]]
    for s in population:
        cur = evaluate_rule(ctx, rule, rule["logic"], s.cand)
        if cur.passed is True:
            continue
        if cur.passed is None:
            cats["evidence_insufficient"].append(s.id)
            notes[s.id] = f"supplied rule cannot be evaluated: {cur.reason}"
            continue
        cats["excluded_by_supplied_rule"].append(s.id)
        notes[s.id] = f"supplied rule: {cur.reason}"
        if spec is None:
            if s.mandatory == "unmet":
                cats["still_fail_mandatory_requirement"].append(s.id)
                notes[s.id] += f"; {s.mandatory_detail}"
            continue
        prop = evaluate_rule(ctx, rule, spec, s.cand)
        if prop.passed is None:
            cats["evidence_insufficient"].append(s.id)
            notes[s.id] += f"; proposed rule cannot be evaluated: {prop.reason}"
            continue
        if prop.passed is False:
            continue
        cats["would_pass_proposed_rule"].append(s.id)
        notes[s.id] += f"; proposed rule: {prop.reason}"
        if s.mandatory == "unmet":
            cats["still_fail_mandatory_requirement"].append(s.id)
            notes[s.id] += f"; {s.mandatory_detail}"
        elif s.mandatory == "unverifiable" or (s.gaps and s.partial):
            cats["evidence_insufficient"].append(s.id)
            notes[s.id] += "; " + (s.mandatory_detail or f"partial record; {', '.join(s.gaps)} cannot be assessed")
        elif s.gaps:
            cats["relevance_not_established"].append(s.id)
            notes[s.id] += f"; required evidence missing for {', '.join(s.gaps)}"
        else:
            failing = [r["id"] for r in other_rules if evaluate_rule(ctx, r, r["logic"], s.cand).passed is not True]
            combined_ok = (s.source == "applicant" and s.assessment is not None and s.assessment.surfaced)
            if not failing:
                cats["newly_eligible_for_review"].append(s.id)
                basis[s.id] = "this correction alone"
            elif combined_ok:
                cats["newly_eligible_for_review"].append(s.id)
                basis[s.id] = "together with the proposed corrections to " + ", ".join(
                    r for r in failing if r in other_proposed)
            else:
                cats["still_fail_other_supplied_rules"].append(s.id)
                notes[s.id] += "; still fails or cannot be evaluated against " + ", ".join(failing)
    sources = {s.id: s.source for s in population if any(s.id in v for v in cats.values())}
    limitations = [_config_note(ctx), "Passing a rule does not mean a candidate is qualified; eligible candidates need human review."]
    if any(v == "pool" for v in sources.values()):
        limitations.append("Pool records did not apply to this requisition. Their results are hypothetical: they show how "
                           "the supplied rule would treat them, not an exclusion that happened.")
    if rule["type"] == "knockout_question" and any(s.source == "pool" for s in population):
        limitations.append("Pool records have no recorded answers to knockout questions, so the supplied question cannot "
                           "be evaluated for them.")
    limitations.append("Each correction is simulated on its own. 'Together with the proposed corrections' uses the same "
                       "combined simulation as candidate-review opportunities, including corrections no human has decided yet.")
    return {
        "evaluable": True,
        "rule": rule["id"],
        "supplied": rule["logic"],
        "proposed": spec,
        "categories": cats,
        "counts": {k: len(v) for k, v in cats.items()},
        "sources": sources,
        "notes": notes,
        "eligibility_basis": basis,
        "population": {"applicants": sum(1 for s in population if s.source == "applicant"),
                       "pool_records": sum(1 for s in population if s.source == "pool")},
        "limitations": limitations,
    }


def annotate_risks(
    ctx: Context,
    checks: CheckOutput,
    findings: list[Finding],
    patches: dict[str, list[tuple[str, dict[str, Any]]]],
    population: list[Subject],
    assessments: list[CandidateAssessment],
) -> list[Finding]:
    """Attach risk categories and correction simulations; return any new protected-requirement findings."""
    rules = {r["id"]: r for r in ctx.requisition["screening_rules"]}
    all_patches = {fid: p for items in checks.patches.values() for fid, p in items}
    by_id = {f.id: f for f in findings}
    for f in findings:
        if f.check in CHECK_RISK:
            f.risk_category = CHECK_RISK[f.check]
        if f.check == "candidate_review_opportunity":
            f.risk_category = _candidate_category(f, by_id)
            f.simulation = _candidate_simulation(f, assessments)
        elif f.check == "measured_impact":
            continue
        elif f.rule_id and f.id in all_patches:
            other = {rid: [p for _, p in items] for rid, items in patches.items() if rid != f.rule_id}
            f.simulation = simulate_correction(ctx, rules[f.rule_id], all_patches[f.id], population, other)
            if f.disposition.get("status") in ("rejected", "confirmed_necessary") and f.simulation.get("evaluable"):
                f.simulation["limitations"].insert(0, "A reviewer rejected this correction; it is excluded from the combined simulation.")
        elif f.check == "unexplained_exclusions":
            f.simulation = {"evaluable": False, "reason": "The supplied rules do not establish why these candidates were "
                            "excluded, so no correction can be simulated. Treat as unknown, not as missed candidates.",
                            "limitations": [_config_note(ctx)]}
            _enrich_unexplained(f, assessments)
        elif f.check in ("unverified_necessity", "alternatives_not_considered"):
            f.simulation = {"evaluable": False, "reason": "No configuration correction is proposed: this finding asks the "
                            "employer to classify the requirement. Its effect appears after a recorded decision and a re-run.",
                            "limitations": [_config_note(ctx)]}
    return _protected_findings(ctx, checks, population, rules)


def _candidate_category(f: Finding, by_id: dict[str, Finding]) -> str:
    """Primary risk category for a candidate, in order of how specific the evidence is."""
    related = [by_id[x] for x in f.related_findings if x in by_id]
    paths = " ".join(e.get("path", "") for e in f.evidence)
    if "equivalency:" in paths or "combination:" in paths:
        return "equivalent_experience"
    if any(r.check == "literal_term_missing_variants" and f.candidate_id in r.affected_candidates for r in related):
        return "terminology"
    if any(r.check == "preferred_enforced_as_knockout" for r in related):
        return "preferred_as_knockout"
    return "rule_narrower"


def _candidate_simulation(f: Finding, assessments: list[CandidateAssessment]) -> dict[str, Any] | None:
    a = next((x for x in assessments if x.candidate_id == f.candidate_id), None)
    if not a:
        return None
    rows = []
    for cur, cor in zip(a.current_rules, a.corrected_rules):
        if cur.passed is True and cor.passed is True:
            continue
        rows.append({"rule": cur.rule_id, "supplied": cur.passed, "supplied_reason": cur.reason,
                     "proposed": cor.passed, "proposed_reason": cor.reason})
    return {"evaluable": True, "kind": "candidate", "rules": rows,
            "result": "passes every rule under the proposed corrections" if a.passes_corrected else "still excluded",
            "limitations": ["Combined effect of all proposed corrections that a human has not rejected.",
                            "Passing the rules does not mean the candidate is qualified."]}


def _enrich_unexplained(f: Finding, assessments: list[CandidateAssessment]) -> None:
    by_id = {a.candidate_id: a for a in assessments}
    evidence = []
    for cid in f.affected_candidates:
        a = by_id.get(cid)
        if not a:
            continue
        unknown = [f"{o.rule_id} ({o.reason})" for o in a.current_rules if o.passed is None]
        text = "no supplied rule fails"
        if unknown:
            text += "; cannot be evaluated: " + ", ".join(unknown)
        evidence.append({"source": f"candidate:{cid}", "text": text})
    f.evidence = evidence


def _protected_findings(ctx: Context, checks: CheckOutput, population: list[Subject],
                        rules: dict[str, dict[str, Any]]) -> list[Finding]:
    out = []
    for rid, reason in sorted(checks.protected_rules.items()):
        rule = rules[rid]
        sim = simulate_correction(ctx, rule, None, population, {})
        if not sim.get("evaluable") or not sim["categories"]["still_fail_mandatory_requirement"]:
            continue
        excluded = sim["categories"]["excluded_by_supplied_rule"]
        unmet = sim["categories"]["still_fail_mandatory_requirement"]
        others = [c for c in excluded if c not in unmet]
        sim["reason"] = "No correction is proposed for a protected requirement."
        linked = ctx.linked_requirement(rule)
        f = Finding(
            id=finding_id(ctx.req_id, "mandatory_requirement_protected", rid),
            check="mandatory_requirement_protected",
            title=f"{rid} enforces a protected requirement; no correction is proposed",
            category="mandatory_protected",
            evidence_level=1,
            requisition_id=ctx.req_id,
            knowledge_version=ctx.pack.fingerprint,
            observation=(
                f"Rule {rid} enforces a protected requirement: {reason}. {len(unmet)} candidate record(s) in the supplied "
                "data do not meet it, and excluding them is expected."
                + (f" {len(others)} other excluded record(s) either show the credential under another spelling or cannot "
                   "be verified; see the terminology finding for this rule." if others else "")
            ),
            source_refs=[SourceRef("rule", rid, rule["text"])] + ([SourceRef("requirement", linked["id"], linked["text"])] if linked else []),
            evidence=[{"source": f"candidate:{c}", "text": sim["notes"].get(c, "")} for c in unmet],
            confidence="high",
            limitations=[
                "Only spelling variants of the credential itself may be recognized (see any terminology finding for this rule).",
                "Candidates whose credentials were not supplied are 'cannot verify', not 'does not meet'.",
                _config_note(ctx),
            ],
            proposed_action="Keep the rule. Do not route around it with alternative experience.",
            expected_benefit="Confirms the screen protects a legal, licensing or employer non-negotiable requirement.",
            tradeoffs="None: relaxing it is out of scope for screening assurance.",
            rule_id=rid,
            requirement_id=linked["id"] if linked else None,
            affected_candidates=sorted(unmet),
        )
        f.risk_category = "mandatory_protected"
        f.simulation = sim
        out.append(f)
    return out
