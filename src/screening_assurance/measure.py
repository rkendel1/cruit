"""Stage 5: outcome and investment measurement.

Measured results and estimates are always reported separately, and every
comparison states its method. Nothing is attributed to the product without a
documented baseline.
"""

from __future__ import annotations

from typing import Any

from .engine.model import Finding, SourceRef, finding_id


def _ratio(a: float, b: float) -> float | None:
    return round(a / b, 3) if b else None


def _period_metrics(p: dict[str, Any] | None) -> dict[str, Any] | None:
    if not p:
        return None
    return {
        **p,
        "qualified_yield": _ratio(p["qualified_candidates"], p["recruiter_reviewed"]),
        "recruiter_hours_per_qualified": _ratio(p["recruiter_hours"], p["qualified_candidates"]),
        "review_rate": _ratio(p["recruiter_reviewed"], p["applicants"]),
    }


def measure(outcomes: dict[str, Any], findings: list[Finding]) -> tuple[dict[str, Any], list[Finding]]:
    by_id = {f.id: f for f in findings}
    reviews = outcomes.get("candidate_reviews", [])
    unknown = sorted({r["finding_id"] for r in reviews if r["finding_id"] not in by_id})
    n = len(reviews)
    meets = sum(1 for r in reviews if r["outcome"] == "meets_requirements")
    not_meet = sum(1 for r in reviews if r["outcome"] == "does_not_meet")
    insufficient = sum(1 for r in reviews if r["outcome"] == "insufficient_evidence")
    minutes = sum(r["review_minutes"] for r in reviews)
    advanced = sum(1 for r in reviews if r.get("advanced_to"))
    hours = minutes / 60

    baseline = _period_metrics(outcomes["baseline"])
    after = _period_metrics(outcomes.get("after_change"))
    deltas = None
    if baseline and after:
        deltas = {}
        for k in ("qualified_candidates", "recruiter_reviewed", "recruiter_hours", "qualified_yield",
                  "recruiter_hours_per_qualified", "days_to_qualified_shortlist"):
            a, b = baseline.get(k), after.get(k)
            if a is not None and b is not None:
                deltas[k] = round(b - a, 3)

    measured = {
        "additional_reviews": n,
        "confirmed_meets_requirements": meets,
        "confirmed_does_not_meet": not_meet,
        "insufficient_evidence": insufficient,
        "advanced_to_next_stage": advanced,
        "review_minutes": minutes,
        "surfacing_precision": _ratio(meets, n),
        "false_positive_rate": _ratio(not_meet, n),
        "incremental_qualified_per_recruiter_hour": _ratio(meets, hours),
    }
    estimated = None
    a = outcomes.get("estimation_assumptions")
    if a:
        estimated = {"label": "ESTIMATED — based on supplied assumptions, not observed", "assumptions": a}
        if a.get("recruiter_hourly_cost") is not None:
            estimated["additional_review_cost"] = round(hours * a["recruiter_hourly_cost"], 2)
        if a.get("cost_per_sourcing_cycle") is not None and a.get("qualified_candidates_needed_per_cycle"):
            cycles = meets / a["qualified_candidates_needed_per_cycle"]
            estimated["sourcing_cycles_potentially_avoided"] = round(cycles, 2)
            estimated["sourcing_cost_potentially_avoided"] = round(cycles * a["cost_per_sourcing_cycle"], 2)
            if "additional_review_cost" in estimated:
                estimated["net_estimated_value"] = round(
                    estimated["sourcing_cost_potentially_avoided"] - estimated["additional_review_cost"], 2)

    measurement = {
        "comparison_method": outcomes["comparison_method"],
        "baseline": baseline,
        "after_change": after,
        "deltas": deltas,
        "measured": measured,
        "estimated": estimated,
        "new_risks_observed": outcomes.get("new_risks_observed", []),
        "unknown_finding_refs": unknown,
        "attribution_note": (
            "Measured values come from recorded recruiter reviews and supplied period data. Changes between "
            "periods are associated with, not proven to be caused by, approved corrections unless the "
            "comparison method controls for other factors."
        ),
    }

    # Attribution: which design findings the reviewed candidates depended on.
    attribution: dict[str, dict[str, Any]] = {}
    for r in reviews:
        f = by_id.get(r["finding_id"])
        if not f:
            continue
        for t in f.related_findings or [f.id]:
            src = by_id.get(t)
            row = attribution.setdefault(t, {"finding_id": t, "title": src.title if src else t, "reviewed": 0,
                                             "meets_requirements": 0, "review_minutes": 0})
            row["reviewed"] += 1
            row["meets_requirements"] += r["outcome"] == "meets_requirements"
            row["review_minutes"] += r["review_minutes"]
    measurement["attribution"] = sorted(attribution.values(), key=lambda x: (-x["meets_requirements"], x["finding_id"]))

    level3: list[Finding] = []
    linked = [r for r in reviews if r["finding_id"] in by_id]
    if linked:
        req_id = outcomes["requisition_id"]
        first = by_id[linked[0]["finding_id"]]
        level3.append(Finding(
            id=finding_id(req_id, "measured_impact", *sorted({r["finding_id"] for r in linked})),
            check="measured_impact",
            title=f"Measured: {meets} of {n} additionally reviewed candidates met the role's requirements",
            category="measured_impact",
            evidence_level=3,
            requisition_id=req_id,
            knowledge_version=first.knowledge_version,
            observation=(
                f"After human review, {meets} of {n} candidate(s) surfaced by this analysis were confirmed to meet the "
                f"role's requirements ({not_meet} did not, {insufficient} had insufficient evidence), using {minutes:g} "
                f"recruiter minutes — {measured['incremental_qualified_per_recruiter_hour']} incremental qualified "
                "candidates per recruiter hour."
            ),
            source_refs=[SourceRef("outcome", r["candidate_id"], r["outcome"]) for r in linked],
            evidence=[{"source": f"outcome:{r['candidate_id']}",
                       "text": f"{r['outcome']} after {r['review_minutes']:g} min"
                               + (f"; advanced to {r['advanced_to']}" if r.get("advanced_to") else "")} for r in linked],
            confidence="high",
            limitations=[outcomes["comparison_method"], "Small sample; confirm across more requisitions before generalizing."],
            proposed_action="Keep the corrections whose candidates were confirmed; submit confirmed equivalencies as knowledge proposals.",
            expected_benefit=f"{meets} confirmed qualified candidate(s) recovered from the existing applicant pool.",
            tradeoffs=f"{minutes:g} recruiter minutes; {not_meet + insufficient} reviewed candidate(s) not (yet) confirmed.",
            related_findings=sorted({r["finding_id"] for r in linked}),
            affected_candidates=[r["candidate_id"] for r in linked],
            disposition={"status": "not_required"},
        ))
    return measurement, level3
