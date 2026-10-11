"""Diagnostic engine orchestration: Normalize -> Interpret -> Evaluate -> Explain -> Measure."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import ENGINE_VERSION
from ..contracts import ContractError, load
from ..knowledge.pack import KnowledgePack
from ..measure import measure
from .candidates import assess_candidates, opportunity_findings, unexplained_finding
from .checks import active_patches, requirement_views, run_design_checks
from .interpret import Context
from .model import DiagnosticResult, RuleView, finding_id
from .rules import apply_patches

CATEGORY_ORDER = {
    "confirmed_inconsistency": 0,
    "design_risk": 1,
    "unverified_assumption": 2,
    "candidate_review_opportunity": 3,
    "input_limitation": 4,
    "measured_impact": 5,
}


@dataclass
class RequisitionBundle:
    path: Path | None
    requisition: dict[str, Any]
    policy: dict[str, Any]
    candidates: dict[str, Any] | None = None
    decisions: dict[str, Any] | None = None
    outcomes: dict[str, Any] | None = None
    pool: dict[str, Any] | None = None


def _find_upwards(start: Path, name: str, levels: int = 3) -> Path | None:
    p = start
    for _ in range(levels + 1):
        if (p / name).exists():
            return p / name
        p = p.parent
    return None


def load_bundle(path: str | Path, *, policy: str | Path | None = None) -> RequisitionBundle:
    """Load a requisition directory: requisition.yaml [+ candidates.yaml, decisions.yaml, outcomes.yaml].

    policy.yaml is taken from the directory or the nearest parent (employer level) unless given.
    """
    root = Path(path)
    req = load("requisition", root / "requisition.yaml")
    policy_path = Path(policy) if policy else _find_upwards(root, "policy.yaml")
    if not policy_path:
        raise ContractError(root, ["no policy.yaml found for this requisition (employer policy is required)"])
    pol = load("policy", policy_path)
    if pol["employer_id"] != req["employer_id"]:
        raise ContractError(policy_path, [f"policy is for {pol['employer_id']}, requisition is for {req['employer_id']}"])
    bundle = RequisitionBundle(path=root, requisition=req, policy=pol)
    for name, attr in (("candidates", "candidates"), ("decisions", "decisions"), ("outcomes", "outcomes")):
        p = root / f"{name}.yaml"
        if p.exists():
            data = load(name, p)
            if data["requisition_id"] != req["id"]:
                raise ContractError(p, [f"{name} is for {data['requisition_id']}, expected {req['id']}"])
            setattr(bundle, attr, data)
    pool_path = root / "candidate-pool.yaml"
    if pool_path.exists():
        bundle.pool = load("candidate_pool", pool_path)
    return bundle


def diagnose(bundle: RequisitionBundle, pack: KnowledgePack, *, run_at: str | None = None) -> DiagnosticResult:
    decisions = {d["finding_id"]: d for d in (bundle.decisions or {}).get("decisions", [])}
    req, reclassified = _apply_classification_decisions(bundle.requisition, decisions)
    ctx = Context(requisition=req, policy=bundle.policy, pack=pack, decisions=decisions, original=bundle.requisition)

    # Stage 1-4: design checks over requirements and rules.
    checks = run_design_checks(ctx)
    for f in checks.findings:
        _apply_decision(f, decisions)
    by_id = {f.id: f for f in checks.findings}
    patches = active_patches(checks, by_id)

    # Candidate pool assurance (only with authorized candidate evidence).
    assessments = []
    findings = list(checks.findings)
    candidates = (bundle.candidates or {}).get("candidates", [])
    if candidates:
        assessments, affected, related, unexplained = assess_candidates(ctx, candidates, checks, patches)
        for fid, cids in affected.items():
            by_id[fid].affected_candidates = sorted(set(cids))
        opp = opportunity_findings(ctx, assessments, checks, related)
        for f in opp:
            _apply_decision(f, decisions)
        findings += opp
        unexp = unexplained_finding(ctx, unexplained)
        if unexp:
            _apply_decision(unexp, decisions)
            findings.append(unexp)
        for a in assessments:
            if not a.surfaced and a.ats_status in ("rejected", "deprioritized") and "protected" in a.reason:
                checks.suppressed.append({"kind": "candidate", "id": a.candidate_id, "reason": a.reason})

    # Stage 5: measurement.
    measurement = None
    if bundle.outcomes:
        measurement, level3 = measure(bundle.outcomes, findings)
        findings += level3

    findings.sort(key=lambda f: (CATEGORY_ORDER[f.category], f.rule_id or "", f.requirement_id or "", f.candidate_id or "", f.id))
    for f in findings:
        f.unlocked_candidates = sorted(set(f.unlocked_candidates))

    rule_views = []
    for rule in req["screening_rules"]:
        fids = [f.id for f in findings if f.rule_id == rule["id"]]
        corrected = apply_patches(rule, [p for _, p in patches.get(rule["id"], [])]) if rule["id"] in patches else None
        linked = ctx.linked_requirement(rule)
        status = "protected" if rule["id"] in checks.protected_rules else ("correction_proposed" if corrected else "no_issue_found")
        rule_views.append(RuleView(
            id=rule["id"], type=rule["type"], text=rule["text"], action=rule["action"],
            linked_requirement=linked["id"] if linked else None, concepts=ctx.rule_concepts(rule),
            status=status, corrected=corrected, finding_ids=fids,
        ))
        if status == "protected":
            checks.suppressed.append({"kind": "rule", "id": rule["id"], "reason": checks.protected_rules[rule["id"]]})

    inputs = dict(req["inputs_received"])
    limitations = _limitations(req, bundle, decisions, findings)
    for rid, cls, fid in reclassified:
        limitations.insert(0, f"Requirement {rid} treated as '{cls}' because of human decision on {fid}.")
    return DiagnosticResult(
        requisition=req,
        policy=bundle.policy,
        knowledge={"pack": pack.pack_id, "version": pack.version, "fingerprint": pack.fingerprint,
                   "status": pack.manifest.get("status"), "path": str(pack.path)},
        engine_version=ENGINE_VERSION,
        run_at=run_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        inputs=inputs,
        limitations=limitations,
        requirements=requirement_views(ctx),
        rules=rule_views,
        findings=findings,
        candidates=assessments,
        suppressed=_dedupe_suppressed(checks.suppressed),
        measurement=measurement,
    )


def _apply_classification_decisions(requisition: dict[str, Any], decisions: dict[str, dict[str, Any]]):
    """Step 2 (Define): human classification decisions on unverified requirements feed back into the analysis."""
    req = copy.deepcopy(requisition)
    applied = []
    for r in req["requirements"]:
        fid = finding_id(req["id"], "unverified_necessity", r["id"])
        d = decisions.get(fid)
        if not d or r.get("employer_classification"):
            continue
        if d["disposition"] == "reclassified_preferred":
            r["employer_classification"] = "preferred"
            r["stated_as"] = "preferred"
            applied.append((r["id"], "preferred", fid))
        elif d["disposition"] == "confirmed_necessary":
            r["employer_classification"] = "essential"
            r["necessity_rationale"] = r.get("necessity_rationale") or d["rationale"]
            applied.append((r["id"], "essential", fid))
    return req, applied


def _apply_decision(f, decisions: dict[str, dict[str, Any]]) -> None:
    d = decisions.get(f.id)
    if d:
        f.disposition = {"status": d["disposition"], "rationale": d["rationale"],
                         "decided_by": d["decided_by"], "decided_at": d["decided_at"]}


def _limitations(req: dict[str, Any], bundle: RequisitionBundle, decisions: dict, findings) -> list[str]:
    out = []
    cfg = req["inputs_received"]["screening_configuration"]
    if cfg == "recruiter_documentation":
        out.append("Screening rules were supplied as recruiter documentation, not verified ATS configuration. "
                   "Findings describe the documented rules; the live ATS may differ.")
    elif cfg == "not_supplied":
        out.append("No screening configuration was supplied; only the job description was audited.")
    if not bundle.candidates:
        out.append("No authorized candidate evidence was supplied; candidate-pool assurance was not performed.")
    elif req["inputs_received"]["candidate_evidence"] == "authorized_sample":
        out.append("Candidate evidence is a sample; candidate counts do not represent the full applicant pool.")
    known = {f.id for f in findings}
    stale = sorted(set(decisions) - known)
    if stale:
        out.append(f"Recorded decisions reference findings no longer produced: {', '.join(stale)}.")
    out.append("Candidate evidence is matched deterministically against the knowledge pack; language-model "
               "interpretation is not used in this run.")
    return out


def _dedupe_suppressed(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen, out = set(), []
    for it in items:
        k = (it["kind"], it["id"], it.get("rule"))
        if k not in seen:
            seen.add(k)
            out.append(it)
    return out
