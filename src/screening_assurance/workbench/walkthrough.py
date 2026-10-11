"""What the recruiter sees first: a plain-language summary of one run, and the examples the guided demo opens.

Pure functions over a stored run (diagnostic result + discovery result). Nothing here computes new findings,
scores or rankings; it only selects and counts what the deterministic engine already produced, so the guided
demo always shows the product's actual behaviour.
"""

from __future__ import annotations

from typing import Any

ACTIONABLE = ("direct", "transferable", "insufficient")
# Checks whose correction is easiest to read as "the rule is narrower than the job"; earlier = preferred.
TOUR_CHECK_ORDER = ("rule_narrower_than_requirement", "preferred_enforced_as_knockout", "experience_path_narrower",
                    "equivalent_path_blocked", "threshold_inconsistency", "credential_stricter_than_requirement",
                    "unstated_requirement_enforced", "literal_term_missing_variants")


def _newly(f: dict[str, Any]) -> list[str]:
    sim = f.get("simulation") or {}
    return list((sim.get("categories") or {}).get("newly_eligible_for_review", []))


def rule_level(f: dict[str, Any]) -> bool:
    """A risk about a supplied rule as a whole, as opposed to one candidate's result."""
    return bool(f.get("rule_id") or f.get("requirement_id")) and not f.get("candidate_id")


def evaluable_correction(f: dict[str, Any]) -> bool:
    sim = f.get("simulation") or {}
    return bool(sim.get("evaluable") and sim.get("proposed") and sim.get("kind") != "candidate")


def value_summary(result: dict[str, Any], discovery: dict[str, Any]) -> dict[str, Any]:
    """Answer 'what might we be missing for this role?' from one run, in counts the recruiter can check."""
    entries = discovery["entries"]
    surfaced = [e for e in entries if e["group"] in ACTIONABLE]
    excluded_applicants = [e for e in surfaced if e["source"]["kind"] == "current_application"
                           and (e["screening"].get("ats_status") in ("rejected", "deprioritized"))]
    by_rule = [e for e in excluded_applicants if e["screening"].get("excluded_by")]
    risks = [f for f in result["findings"] if f.get("risk_category")]
    rule_risks = [f for f in risks if rule_level(f)]
    corrections = [f for f in rule_risks if evaluable_correction(f)]
    newly = sorted({c for f in corrections for c in _newly(f)})
    protected = [f for f in risks if f["risk_category"] == "mandatory_protected"]
    unexplained = sorted({c for f in risks if f["check"] == "unexplained_exclusions" for c in f.get("affected_candidates", [])})
    top = sorted(corrections, key=lambda f: (-len(_newly(f)), _check_rank(f["check"]), f["id"]))[:3]
    return {
        "candidates_considered": len(entries),
        "counts": discovery["counts"],
        "surfaced": len(surfaced),
        "surfaced_from_pool": sum(1 for e in surfaced if e["source"]["kind"] == "candidate_pool"),
        "excluded_applicants_with_evidence": [e["candidate_id"] for e in excluded_applicants],
        "excluded_by_supplied_rules": [e["candidate_id"] for e in by_rule],
        "needs_verification": [e["candidate_id"] for e in surfaced if e["group"] in ("transferable", "insufficient")],
        "rule_risks": len(rule_risks),
        "corrections_simulated": len(corrections),
        "newly_eligible_any_correction": newly,
        "protected_requirements": [f.get("rule_id") or f.get("requirement_id") for f in protected],
        "unexplained_exclusions": unexplained,
        "top_rule_risks": [{"finding_id": f["id"], "title": f["title"], "rule": f.get("rule_id"),
                            "requirement": f.get("requirement_id"), "risk_category": f["risk_category"],
                            "newly_eligible": _newly(f)} for f in top],
        "screening_configuration": result["inputs"]["screening_configuration"],
    }


def _check_rank(check: str) -> int:
    return TOUR_CHECK_ORDER.index(check) if check in TOUR_CHECK_ORDER else len(TOUR_CHECK_ORDER)


def tour_selection(result: dict[str, Any], discovery: dict[str, Any]) -> dict[str, Any]:
    """Pick a representative candidate and a rule-level finding that concern each other.

    Preference: an applicant the supplied rules rejected whose evidence supports review through an alternative
    path (so the recruiter sees both evidence and what to verify), and the rule-level finding with an evaluable
    correction that makes that candidate eligible for review. Falls back gracefully; returns None for parts that
    the run does not support (for example a requisition without candidate evidence).
    """
    surfaced = [e for e in discovery["entries"] if e["group"] in ACTIONABLE]
    corrections = sorted((f for f in result["findings"] if f.get("risk_category") and rule_level(f) and evaluable_correction(f)),
                         key=lambda f: (_check_rank(f["check"]), -len(_newly(f)), f["id"]))
    group_rank = {"transferable": 0, "direct": 1, "insufficient": 2}

    def cand_rank(e: dict[str, Any]) -> tuple:
        applicant = e["source"]["kind"] == "current_application"
        rejected = bool(e["screening"].get("excluded_by"))
        linked = any(e["candidate_id"] in _newly(f) for f in corrections)
        return (not (applicant and rejected and linked), group_rank[e["group"]], e["candidate_id"])

    cand = min(surfaced, key=cand_rank) if surfaced else None
    finding = None
    if cand:
        finding = next((f for f in corrections if cand["candidate_id"] in _newly(f)), None)
    if finding is None and corrections:
        finding = corrections[0]
    if finding is None:
        finding = next((f for f in result["findings"] if f.get("risk_category") and rule_level(f)), None)
    return {
        "candidate_id": cand["candidate_id"] if cand else None,
        "finding_id": finding["id"] if finding else None,
        "finding_has_correction": bool(finding and evaluable_correction(finding)),
    }


def guide(result: dict[str, Any], discovery: dict[str, Any]) -> dict[str, Any]:
    return {"summary": value_summary(result, discovery), "tour": tour_selection(result, discovery)}
