"""Candidate pool assurance: who may have been excluded, and what evidence exists.

A candidate is surfaced for human review only when ALL of these hold:
  * the ATS excluded or deprioritized them,
  * the simulated current rules explain the exclusion,
  * they pass every rule once proposed (not human-rejected) corrections are applied,
  * every required requirement has evidence (direct, terminology variant, or an
    employer-permitted alternative path) or is pending employer clarification,
  * no protected (legal / licensing / non-negotiable) requirement is unmet.

Surfacing is a request for human review. It is never a claim the candidate is qualified.
"""

from __future__ import annotations

from typing import Any

from .checks import CheckOutput
from .interpret import (
    Context,
    candidate_entries,
    concept_evidence,
    equivalency_evidence,
    months_for_entries,
    related_only_evidence,
)
from .model import CandidateAssessment, Finding, RequirementEvidence, SourceRef, finding_id
from .rules import apply_patches, evaluate_rule

EXCLUDED_STATUSES = {"rejected", "deprioritized"}
COVERED = {"evidenced", "alternative_path", "pending_clarification"}


def requirement_evidence(ctx: Context, cand: dict[str, Any], req: dict[str, Any], unverified: set[str]) -> RequirementEvidence:
    concepts = ctx.requirement_concepts(req)
    protected = next((ctx.protected_reason(c) for c in concepts if ctx.protected_reason(c)), None)
    alternatives_ok = bool(req.get("accepts_equivalent")) or req.get("employer_classification") == "demonstrable_through_alternatives"
    allow_supporting = alternatives_ok or any((ctx.pack.skill(c) or {}).get("kind") in ("capability",) for c in concepts)
    rv = RequirementEvidence(requirement_id=req["id"], status="not_evidenced")

    direct = concept_evidence(ctx, cand, concepts, requirement_text=req["text"], allow_supporting=allow_supporting and not protected)
    if protected:
        if direct.items:
            rv.status, rv.paths, rv.evidence = "evidenced", sorted(direct.paths), direct.items
        else:
            rv.status = "protected_missing"
            rv.notes.append(f"Protected requirement not evidenced: {protected}. No alternative path is considered.")
        return rv

    entries = set(direct.entries)
    rv.evidence = list(direct.items)
    rv.paths = sorted(direct.paths)
    eq_matches = []
    for c in concepts:
        for eq in ctx.pack.equivalencies_for(c, ctx.job_family):
            allowed, why = ctx.equivalency_status(eq["id"])
            m = equivalency_evidence(ctx, cand, eq)
            if not allowed:
                if m.satisfied:
                    rv.notes.append(f"{eq['id']} would apply but is {why}.")
                continue
            eq_matches.append((eq, m))

    if direct.items:
        rv.status = "evidenced"
        for eq, m in eq_matches:  # equivalency evidence can add relevant duration
            if m.satisfied and alternatives_ok:
                entries |= m.entries
    else:
        satisfied = [(eq, m) for eq, m in eq_matches if m.satisfied]
        if satisfied and alternatives_ok:
            rv.status = "alternative_path"
            for eq, m in satisfied:
                rv.paths.append(f"equivalency:{eq['id']}")
                rv.evidence += m.items
                entries |= m.entries
                rv.verify_next += eq["validation_steps"]
                rv.notes.append(f"{eq['id']}: {m.reason}. Conditions: " + " ".join(eq["conditions"]))
        elif satisfied:
            rv.notes.append(
                f"Alternative evidence present ({', '.join(eq['id'] for eq, _ in satisfied)}), but {req['id']} "
                "does not currently accept equivalent experience."
            )
            rv.verify_next.append(f"Ask the hiring manager whether {req['id']} can be demonstrated through alternatives.")
        else:
            for eq, m in eq_matches:
                if m.matched_indicators:
                    rv.notes.append(f"Partial evidence for {eq['id']}: {m.reason}.")
        if rv.status == "not_evidenced" and alternatives_ok:
            for c in concepts:
                for combo in ctx.pack.combinations_supporting(c):
                    hits = []
                    items = []
                    for comp in combo["components"]:
                        ev = concept_evidence(ctx, cand, [comp])
                        if ev.items:
                            hits.append(comp)
                            items.append(ev.items[0])
                    if len(hits) >= combo["min_components"]:
                        rv.status = "alternative_path"
                        rv.paths.append(f"combination:{combo['id']}")
                        rv.evidence += items
                        rv.notes.append(f"{combo['name']}: {combo['rationale'].strip()}")
                        rv.verify_next += combo["limitations"]
                    elif hits:
                        rv.notes.append(f"Partial combination {combo['id']}: {len(hits)} of {combo['min_components']} components.")

    related = related_only_evidence(ctx, cand, concepts)
    if related:
        rv.notes.append("Closely related (not equivalent) terminology found: "
                        + "; ".join(f"'{r['matched']}' in {r['source']}" for r in related[:3]))
        if rv.status == "not_evidenced":
            rv.verify_next.append("Verify whether the closely related experience meets the requirement.")

    if req.get("min_years") is not None and rv.status in ("evidenced", "alternative_path"):
        months = months_for_entries(cand, entries)
        rv.relevant_months = months
        if months < req["min_years"] * 12:
            rv.status = "insufficient"
            rv.notes.append(f"{months} months of relevant experience found; requirement states {req['min_years']:g} years.")

    if rv.status == "not_evidenced" and req["id"] in unverified:
        rv.status = "pending_clarification"
        rv.notes.append("Not evidenced, but the requirement's necessity is unverified; awaiting employer classification.")
    return rv


def assess_candidates(
    ctx: Context,
    candidates: list[dict[str, Any]],
    checks: CheckOutput,
    patches: dict[str, list[tuple[str, dict[str, Any]]]],
) -> tuple[list[CandidateAssessment], dict[str, list[str]], dict[str, list[str]], list[str]]:
    """Returns (assessments, finding_id -> candidates that finding's correction alone lets pass its rule,
    candidate_id -> findings responsible for unlocking them, unexplained exclusions)."""
    rules = ctx.requisition["screening_rules"]
    rules_by_id = {r["id"]: r for r in rules}
    corrected_specs = {r["id"]: apply_patches(r, [p for _, p in patches.get(r["id"], [])]) for r in rules}
    unverified = {f.requirement_id for f in checks.findings if f.check == "unverified_necessity"
                  and f.disposition.get("status") in ("pending", "deferred", "requested_evidence")}
    finding_affected: dict[str, list[str]] = {}
    candidate_related: dict[str, list[str]] = {}
    unexplained: list[str] = []
    out = []
    for cand in candidates:
        current = [evaluate_rule(ctx, r, r["logic"], cand) for r in rules]
        corrected = [evaluate_rule(ctx, r, corrected_specs[r["id"]], cand) for r in rules]
        excluded_by = [o.rule_id for o in current if o.passed is False]
        related: list[str] = []
        for cur, cor in zip(current, corrected):
            if not (cur.passed is False and cor.passed is not False and cur.rule_id in patches):
                continue
            rule = rules_by_id[cur.rule_id]
            solo = [fid for fid, p in patches[cur.rule_id]
                    if evaluate_rule(ctx, rule, apply_patches(rule, [p]), cand).passed is not False]
            for fid in solo:
                finding_affected.setdefault(fid, []).append(cand["id"])
            # If no single correction suffices, the corrections on this rule are jointly responsible.
            related += solo or [fid for fid, _ in patches[cur.rule_id]]
        candidate_related[cand["id"]] = sorted(set(related))
        protected_fail = [o.rule_id for o in corrected if o.passed is False and o.rule_id in checks.protected_rules]
        passes_corrected = all(o.passed is not False for o in corrected)
        reqs = [requirement_evidence(ctx, cand, r, unverified) for r in ctx.requisition["requirements"]]
        required = [rv for rv, r in zip(reqs, ctx.requisition["requirements"]) if r["stated_as"] == "required"]
        covered = [rv for rv in required if rv.status in COVERED]
        coverage = "complete" if len(covered) == len(required) else ("partial" if covered else "none")
        status = cand["ats_status"]
        if status in EXCLUDED_STATUSES and not excluded_by:
            unexplained.append(cand["id"])
        surfaced = False
        if status not in EXCLUDED_STATUSES:
            reason = f"Not excluded by the ATS (status: {status})."
        elif not excluded_by:
            reason = "Excluded, but the supplied rules do not explain the exclusion."
        elif protected_fail or any(rv.status == "protected_missing" for rv in reqs):
            reason = "Does not meet a protected requirement; not surfaced."
        elif not passes_corrected:
            still = [o.rule_id for o in corrected if o.passed is False]
            reason = f"Still excluded after proposed corrections by {', '.join(still)}."
        elif coverage != "complete":
            gaps = [rv.requirement_id for rv in required if rv.status not in COVERED]
            reason = f"Evidence gaps on required requirement(s) {', '.join(gaps)}; not surfaced."
        else:
            surfaced = True
            reason = "Excluded by rules the proposed corrections address; every required requirement has evidence."
        out.append(CandidateAssessment(
            candidate_id=cand["id"], ats_status=status, current_rules=current, corrected_rules=corrected,
            requirements=reqs, excluded_by=excluded_by, passes_corrected=passes_corrected,
            evidence_coverage=coverage, nontraditional_signals=_signals(ctx, cand, reqs),
            surfaced=surfaced, reason=reason,
        ))
    return out, finding_affected, candidate_related, unexplained


def _signals(ctx: Context, cand: dict[str, Any], reqs: list[RequirementEvidence]) -> list[str]:
    signals = []
    for rv in reqs:
        for p in rv.paths:
            if p.startswith("equivalency:"):
                signals.append(f"{rv.requirement_id} evidenced through transferable experience ({p.split(':', 1)[1]})")
            elif p.startswith("combination:"):
                signals.append(f"{rv.requirement_id} evidenced through a combination of skills ({p.split(':', 1)[1]})")
            elif p == "terminology_variant":
                terms = sorted({e['matched'] for e in rv.evidence if e.get("path") == "terminology_variant"})
                signals.append(f"{rv.requirement_id} described in different terminology: {', '.join(terms)}")
            elif p == "supporting_skill":
                terms = sorted({e['matched'] for e in rv.evidence if e.get("path") == "supporting_skill"})
                signals.append(f"{rv.requirement_id} evidenced through an equivalent tool or skill: {', '.join(terms)}")
    domains = sorted({e.domain for e in candidate_entries(cand) if e.domain})
    if domains:
        signals.append(f"Experience domains: {', '.join(domains)}")
    return list(dict.fromkeys(signals))


def opportunity_findings(
    ctx: Context,
    assessments: list[CandidateAssessment],
    checks: CheckOutput,
    candidate_related: dict[str, list[str]],
) -> list[Finding]:
    by_id = {f.id: f for f in checks.findings}
    findings = []
    for a in assessments:
        if not a.surfaced:
            continue
        related = candidate_related.get(a.candidate_id, [])
        for fid in related:
            by_id[fid].unlocked_candidates.append(a.candidate_id)
        alt = any(p.startswith(("equivalency:", "combination:")) for rv in a.requirements for p in rv.paths)
        low = any(
            p.startswith("equivalency:") and ctx.pack.equivalencies[p.split(":", 1)[1]]["confidence"] == "low"
            for rv in a.requirements for p in rv.paths
        )
        confidence = "low" if low else ("medium" if alt else "high")
        evidence = [dict(e, requirement=rv.requirement_id) for rv in a.requirements for e in rv.evidence[:3]]
        unproven = [f"{rv.requirement_id}: {n}" for rv in a.requirements for n in rv.notes]
        verify = list(dict.fromkeys(v for rv in a.requirements for v in rv.verify_next))
        f = Finding(
            id=finding_id(ctx.req_id, "candidate_review_opportunity", a.candidate_id),
            check="candidate_review_opportunity",
            title=f"Candidate {a.candidate_id} may meet the requirements through a path the current rules do not recognize",
            category="candidate_review_opportunity",
            evidence_level=2,
            requisition_id=ctx.req_id,
            knowledge_version=ctx.pack.fingerprint,
            observation=(
                f"{a.candidate_id} was {a.ats_status} by {', '.join(a.excluded_by)}. Under the proposed corrections "
                f"they pass every rule, and each required requirement has supporting evidence."
            ),
            source_refs=[SourceRef("candidate", a.candidate_id)] + [SourceRef("rule", r) for r in a.excluded_by],
            evidence=evidence,
            confidence=confidence,
            limitations=[
                "Qualification has not been established; this is a request for human review.",
                *unproven,
            ],
            proposed_action="Recruiter review of this candidate. Verify: " + (" ".join(verify) if verify else "the evidence listed."),
            expected_benefit="A potentially qualified applicant already in the pipeline receives human review instead of being lost.",
            tradeoffs="Recruiter review time (typically 10–20 minutes).",
            candidate_id=a.candidate_id,
            affected_candidates=[a.candidate_id],
            related_findings=related,
            knowledge_refs=sorted({p.split(":", 1)[1] for rv in a.requirements for p in rv.paths if ":" in p}),
        )
        findings.append(f)
    return findings


def unexplained_finding(ctx: Context, ids: list[str]) -> Finding | None:
    if not ids:
        return None
    return Finding(
        id=finding_id(ctx.req_id, "unexplained_exclusions", *ids),
        check="unexplained_exclusions",
        title=f"{len(ids)} exclusion(s) are not explained by the supplied screening rules",
        category="input_limitation",
        evidence_level=2,
        requisition_id=ctx.req_id,
        knowledge_version=ctx.pack.fingerprint,
        observation=(
            f"Candidates {', '.join(ids)} were rejected or deprioritized, but pass every supplied rule. Either the "
            "supplied configuration is incomplete, or the exclusions were manual decisions."
        ),
        source_refs=[SourceRef("candidate", i) for i in ids],
        evidence=[],
        confidence="high",
        limitations=["The engine can only audit configuration it was given; it does not claim a complete audit."],
        proposed_action="Supply the complete ATS screening configuration, or confirm these were manual decisions.",
        expected_benefit="A complete audit, and visibility into undocumented screening criteria.",
        tradeoffs="None.",
        affected_candidates=ids,
    )

