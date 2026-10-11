"""Shared helpers for report renderers. Renderers take the result dict (DiagnosticResult.as_dict())."""

from __future__ import annotations

from typing import Any

LEVEL_LABEL = {1: "Level 1 · Demonstrable inconsistency", 2: "Level 2 · Plausible missed-talent risk", 3: "Level 3 · Measured impact"}
CATEGORY_TITLE = {
    "confirmed_inconsistency": "Confirmed inconsistency",
    "design_risk": "Screening design risk",
    "unverified_assumption": "Unverified assumption",
    "candidate_review_opportunity": "Candidate-review opportunity",
    "input_limitation": "Input limitation",
    "measured_impact": "Measured impact",
}
CLASSIFICATION_LABEL = {
    "essential": "Essential",
    "preferred": "Preferred",
    "demonstrable_through_alternatives": "Demonstrable through alternatives",
    "unverified_assumption": "Unverified assumption",
}
STATUS_LABEL = {
    "evidenced": "Evidenced",
    "alternative_path": "Evidenced via alternative path",
    "insufficient": "Partially evidenced (below threshold)",
    "not_evidenced": "Not evidenced",
    "pending_clarification": "Pending employer clarification",
    "protected_missing": "Protected requirement not met",
}
PATH_LABEL = {
    "direct": "same terminology",
    "terminology_variant": "different terminology",
    "supporting_skill": "equivalent tool / credential",
    "closely_related": "closely related only",
}
DISPOSITIONS = [
    ("accepted", "Accept"),
    ("rejected", "Reject"),
    ("deferred", "Defer"),
    ("requested_evidence", "Request evidence"),
    ("confirmed_necessary", "Confirm requirement is necessary"),
    ("reclassified_preferred", "Reclassify as preferred"),
    ("approved_candidate_review", "Approve candidate review"),
]

SECTIONS = [
    ("design", "Confirmed inconsistencies", lambda f: f["category"] == "confirmed_inconsistency"),
    ("risks", "Potential missed-talent risks", lambda f: f["category"] in ("design_risk", "unverified_assumption", "input_limitation")),
    ("candidates", "Candidate-review opportunities", lambda f: f["category"] == "candidate_review_opportunity"),
    ("measured", "Measured impact", lambda f: f["category"] == "measured_impact"),
]


def path_label(p: str) -> str:
    if p.startswith("equivalency:"):
        return f"transferable experience ({p.split(':', 1)[1]})"
    if p.startswith("combination:"):
        return f"skill combination ({p.split(':', 1)[1]})"
    return PATH_LABEL.get(p, p)


def requirement_text(result: dict[str, Any], rid: str) -> str:
    for r in result["requirements"]:
        if r["id"] == rid:
            return r["text"]
    return rid


def candidate(result: dict[str, Any], cid: str) -> dict[str, Any] | None:
    return next((c for c in result["candidates"] if c["candidate_id"] == cid), None)


def finding(result: dict[str, Any], fid: str) -> dict[str, Any] | None:
    return next((f for f in result["findings"] if f["id"] == fid), None)


def candidate_review_answers(result: dict[str, Any], f: dict[str, Any]) -> dict[str, Any]:
    """The five questions from the recruiter's candidate-evidence view (blueprint §9.3)."""
    c = candidate(result, f["candidate_id"]) or {}
    req_rows = []
    for rv in c.get("requirements", []):
        req = next(r for r in result["requirements"] if r["id"] == rv["requirement_id"])
        req_rows.append({
            "id": rv["requirement_id"],
            "text": req["text"],
            "stated_as": req["stated_as"],
            "status": rv["status"],
            "paths": [path_label(p) for p in rv["paths"]],
            "evidence": rv["evidence"][:4],
            "months": rv["relevant_months"],
            "notes": rv["notes"],
        })
    unproven = []
    for rv in c.get("requirements", []):
        if rv["status"] not in ("evidenced",):
            unproven += [f"{rv['requirement_id']}: {n}" for n in rv["notes"]] or [f"{rv['requirement_id']}: {STATUS_LABEL[rv['status']]}"]
    unproven.append("Qualification has not been established by this analysis.")
    verify = list(dict.fromkeys(v for rv in c.get("requirements", []) for v in rv["verify_next"]))
    if not verify:
        verify = ["Confirm the depth and recency of the experience cited for each required requirement."]
    return {
        "requirements": req_rows,
        "differs": c.get("nontraditional_signals", []),
        "excluded_by": [o for o in c.get("current_rules", []) if o["passed"] is False],
        "unproven": list(dict.fromkeys(unproven)),
        "verify": verify,
    }
