"""Candidate rediscovery: evidence-based grouping of applicants and an authorized candidate pool.

This extends the diagnostic engine from "candidates affected by supplied screening rules" to
"candidates whose supplied evidence relates to this requisition's requirements". It reuses the
same deterministic requirement-evidence logic and knowledge pack; it does not rank or score.

Groups
  direct            every required requirement is evidenced without an alternative path
  transferable      every required requirement is covered, at least one through an alternative path
                    (equivalency or skill combination) that needs human review
  insufficient      some required evidence exists, but the record is partial or a mandatory
                    requirement cannot be verified from what was supplied
  not_surfaced      a mandatory requirement is not met, required evidence is missing from a complete
                    record, or there is no relevant evidence (the last is counted, not listed)
  blocked           the record may not be used for action: not authorized for rediscovery,
                    authorization expired, or evidence older than the permitted age
  active_workflow   already in active review for this requisition in the ATS

Nothing here grants permission to contact anyone; a prior application is context only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .candidates import requirement_evidence
from .engine import RequisitionBundle, _apply_classification_decisions
from .interpret import Context
from .pool import DEFAULT_MAX_AGE_DAYS, _d, default_as_of, pool_block_reason
from .model import DiagnosticResult
from ..knowledge.pack import KnowledgePack

GROUPS = ("direct", "transferable", "insufficient", "not_surfaced", "blocked", "active_workflow")
ACTIONABLE = ("direct", "transferable", "insufficient")
ACTIVE_STATUSES = {"in_review", "advanced"}

CONFIG_BASIS = {
    "ats_export_verified": "simulated against the supplied ATS configuration export (not a live ATS audit)",
    "ats_api_verified": "simulated against the configuration as read from the ATS at export time (not a live audit)",
    "recruiter_documentation": "simulated against recruiter-documented rules (not verified ATS configuration)",
    "not_supplied": "no screening configuration was supplied",
}


@dataclass
class DiscoveryEntry:
    candidate_id: str
    source: dict[str, Any]
    group: str
    why: list[str] = field(default_factory=list)
    requirements: list[dict[str, Any]] = field(default_factory=list)
    supported: list[str] = field(default_factory=list)
    unverified: list[dict[str, str]] = field(default_factory=list)
    mandatory_issues: list[dict[str, str]] = field(default_factory=list)
    screening: dict[str, Any] = field(default_factory=dict)
    prior_applications: list[dict[str, Any]] = field(default_factory=list)
    freshness: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    verify_next: list[str] = field(default_factory=list)
    reason: str = ""
    listable: bool = True  # False: counted only, never listed (disposition not explainable beyond "no evidence")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiscoveryResult:
    requisition_id: str
    knowledge: str
    as_of: str
    inputs: dict[str, Any]
    entries: list[DiscoveryEntry]
    limitations: list[str]

    def counts(self) -> dict[str, int]:
        return {g: sum(1 for e in self.entries if e.group == g) for g in GROUPS}

    def as_dict(self) -> dict[str, Any]:
        return {
            "requisition_id": self.requisition_id,
            "knowledge": self.knowledge,
            "as_of": self.as_of,
            "inputs": self.inputs,
            "counts": self.counts(),
            "limitations": self.limitations,
            "entries": [e.as_dict() for e in self.entries],
        }


def _paths_label(paths: list[str]) -> str:
    out = []
    for p in paths:
        if p.startswith("equivalency:"):
            out.append("transferable experience")
        elif p.startswith("combination:"):
            out.append("combination of skills")
        elif p == "terminology_variant":
            out.append("different terminology")
        elif p == "supporting_skill":
            out.append("equivalent tool or credential")
        else:
            out.append("same terminology")
    return ", ".join(dict.fromkeys(out))


def discover(
    bundle: RequisitionBundle,
    pack: KnowledgePack,
    diag: DiagnosticResult,
    *,
    pool: dict[str, Any] | None = None,
    as_of: str | None = None,
) -> DiscoveryResult:
    """Group current applicants and authorized pool records by the evidence supporting review.

    `diag` must be the DiagnosticResult for the same bundle and knowledge pack; discovery reuses
    its screening-rule simulation and finding identifiers rather than recomputing them.
    """
    pool = pool if pool is not None else getattr(bundle, "pool", None)
    decisions = {d["finding_id"]: d for d in (bundle.decisions or {}).get("decisions", [])}
    req, _ = _apply_classification_decisions(bundle.requisition, decisions)
    ctx = Context(requisition=req, policy=bundle.policy, pack=pack, decisions=decisions, original=bundle.requisition)
    as_of = as_of or default_as_of(pool, diag.run_at)
    as_of_d = _d(as_of)

    unverified_ids = {f.requirement_id for f in diag.findings if f.check == "unverified_necessity"
                      and f.disposition.get("status") in ("pending", "deferred", "requested_evidence")}
    req_by_id = {r["id"]: r for r in req["requirements"]}
    required_ids = [r["id"] for r in req["requirements"] if r["stated_as"] == "required"]
    protected_ids = {rv.id for rv in diag.requirements if rv.protected}
    opp_by_candidate = {f.candidate_id: f.id for f in diag.findings if f.check == "candidate_review_opportunity"}
    assessments = {a.candidate_id: a for a in diag.candidates}
    cfg = req["inputs_received"]["screening_configuration"]

    entries: list[DiscoveryEntry] = []
    seen: set[str] = set()

    # ------------------------------------------------------------- current applicants
    for cand in (bundle.candidates or {}).get("candidates", []):
        cid = cand["id"]
        seen.add(cid)
        a = assessments.get(cid)
        source = {"kind": "current_application", "system": req.get("ats") or "ats-export",
                  "record_ref": f"{req['id']}/{cid}", "evidence_provenance": "application_resume"}
        if cand["ats_status"] in ACTIVE_STATUSES:
            entries.append(DiscoveryEntry(cid, source, "active_workflow",
                                          reason=f"Already in active review in the ATS (status: {cand['ats_status']}).",
                                          listable=False))
            continue
        screening = {
            "applied_to_requisition": True,
            "ats_status": cand["ats_status"],
            "recorded_rule": cand.get("ats_exclusion_rule"),
            "excluded_by": [{"rule": o.rule_id, "reason": o.reason} for o in (a.current_rules if a else []) if o.passed is False],
            "basis": CONFIG_BASIS[cfg],
            "established": cfg in ("ats_export_verified", "ats_api_verified"),
            "related_findings": [opp_by_candidate[cid]] if cid in opp_by_candidate else [],
        }
        if not screening["excluded_by"]:
            screening["note"] = ("The supplied rules do not explain this exclusion; it may be a manual decision "
                                 "or configuration that was not supplied.")
        entry = _evaluate(ctx, cand, source, req_by_id, required_ids, protected_ids, unverified_ids,
                          coverage={"experience": "complete", "credentials": "complete"})
        entry.screening = screening
        entry.freshness = {"status": "current_application", "note": "Evidence is from the application to this requisition."}
        entry.constraints = ["Applied to this requisition; follow your normal applicant process."]
        rules = ", ".join(x["rule"] for x in screening["excluded_by"])
        lead = (f"Applied to this requisition and was {cand['ats_status']}"
                + (f"; excluded by {rules} ({screening['basis']})." if rules else "; the supplied rules do not explain the exclusion."))
        entry.why.insert(0, lead)
        entries.append(entry)

    # ------------------------------------------------------------- authorized pool
    pool_meta: dict[str, Any] = {}
    if pool:
        max_age = pool.get("max_evidence_age_days", DEFAULT_MAX_AGE_DAYS)
        pool_uses = pool["authorization"]["permitted_uses"]
        pool_meta = {"pool_id": pool["pool_id"], "source_system": pool["source_system"], "exported_at": pool["exported_at"],
                     "max_evidence_age_days": max_age, "permitted_uses": pool_uses,
                     "retention_days": pool["authorization"]["retention_days"], "deletion": pool["authorization"]["deletion"]}
        for cand in pool["candidates"]:
            cid = cand["id"]
            source = {"kind": "candidate_pool", "system": pool["source_system"], "record_ref": cand["source_record_ref"],
                      "pool_id": pool["pool_id"], "evidence_provenance": cand["evidence_provenance"]}
            if cid in seen:
                entries.append(DiscoveryEntry(cid, source, "blocked",
                                              reason="Duplicate of a current applicant id; the application record is used instead.",
                                              listable=True))
                continue
            seen.add(cid)
            blocked, freshness = pool_block_reason(cand, pool, as_of_d)
            if blocked:
                entries.append(DiscoveryEntry(cid, source, "blocked", reason=blocked, freshness=freshness))
                continue
            entry = _evaluate(ctx, cand, source, req_by_id, required_ids, protected_ids, unverified_ids,
                              coverage=cand["evidence_coverage"])
            entry.freshness = freshness
            entry.prior_applications = cand.get("prior_applications", [])
            entry.screening = {
                "applied_to_requisition": False,
                "excluded_by": [],
                "basis": "No supplied screening rule applies: this record is not an application to this requisition.",
                "established": False,
                "related_findings": [],
            }
            if entry.prior_applications:
                pa = entry.prior_applications[0]
                lead = (f"Prior applicant ({pa['requisition_ref']}, {pa['applied_at']}, outcome: {pa['outcome']}); "
                        "record authorized for rediscovery review. The prior disposition is not explained by any supplied rule.")
            else:
                lead = f"Record from {pool['source_system']} ({cand['evidence_provenance'].replace('_', ' ')}), authorized for rediscovery review."
            entry.why.insert(0, lead)
            entry.constraints = _constraints(cand)
            entries.append(entry)

    limitations = [
        "Groups describe the supplied evidence, not qualification. Every surfaced candidate needs human review.",
        "No ranking or match score is produced; order within a group is by candidate id.",
        "Prior applications are context only and do not establish permission to contact anyone.",
    ]
    if not pool:
        limitations.append("No candidate pool was supplied; only applicants to this requisition were considered.")
    if cfg not in ("ats_export_verified", "ats_api_verified"):
        limitations.append("Screening exclusions are " + CONFIG_BASIS[cfg] + ".")
    order = {g: i for i, g in enumerate(GROUPS)}
    entries.sort(key=lambda e: (order[e.group], e.candidate_id))
    return DiscoveryResult(
        requisition_id=req["id"],
        knowledge=pack.fingerprint,
        as_of=as_of,
        inputs={"current_applicants": len((bundle.candidates or {}).get("candidates", [])),
                "pool": pool_meta or None, "screening_configuration": cfg},
        entries=entries,
        limitations=limitations,
    )


def _constraints(cand: dict[str, Any]) -> list[str]:
    out = []
    status = cand.get("contact_status")
    if status == "do_not_contact":
        out.append("Do not contact (supplied by the source system).")
    elif status == "opted_in_talent_community":
        out.append("Opted in to the talent community (supplied). Confirm current consent in your own system before any contact.")
    else:
        out.append("Contact permission is not established by this record.")
    exp = (cand.get("authorization") or {}).get("expires_at")
    if exp:
        out.append(f"Authorization for this record expires {exp}.")
    return out


def _evaluate(
    ctx: Context,
    cand: dict[str, Any],
    source: dict[str, Any],
    req_by_id: dict[str, dict[str, Any]],
    required_ids: list[str],
    protected_ids: set[str],
    unverified_ids: set[str],
    *,
    coverage: dict[str, str],
) -> DiscoveryEntry:
    cid = cand["id"]
    rvs = {r["id"]: requirement_evidence(ctx, cand, r, unverified_ids) for r in ctx.requisition["requirements"]}
    entry = DiscoveryEntry(cid, source, "not_surfaced")
    for rid, r in req_by_id.items():
        rv = rvs[rid]
        entry.requirements.append({
            "id": rid, "text": r["text"], "stated_as": r["stated_as"], "protected": rid in protected_ids,
            "status": rv.status, "paths": rv.paths, "path_label": _paths_label(rv.paths),
            "evidence": _unique_sources(rv.evidence)[:4], "months": rv.relevant_months, "notes": rv.notes,
        })
        entry.verify_next += rv.verify_next
    entry.verify_next = list(dict.fromkeys(entry.verify_next))

    partial_experience = coverage.get("experience") != "complete"
    partial_credentials = coverage.get("credentials") != "complete"
    evidenced_required = [rid for rid in required_ids if rvs[rid].status in ("evidenced", "alternative_path")]
    entry.supported = [rid for rid, rv in rvs.items() if rv.status in ("evidenced", "alternative_path")]
    gaps: list[str] = []
    mandatory_unmet = False
    unverifiable = False
    for rid in required_ids:
        rv = rvs[rid]
        if rv.status in ("evidenced", "alternative_path"):
            continue
        if rv.status == "pending_clarification":
            entry.unverified.append({"requirement": rid, "reason": "Not evidenced; the employer has not yet confirmed this requirement is necessary."})
            continue
        if rv.status == "protected_missing":
            if partial_credentials:
                unverifiable = True
                entry.mandatory_issues.append({"requirement": rid, "issue": "cannot_verify",
                                               "detail": "Mandatory credential cannot be verified: credentials were not supplied completely for this record."})
            else:
                mandatory_unmet = True
                entry.mandatory_issues.append({"requirement": rid, "issue": "not_satisfied",
                                               "detail": "Mandatory credential is not among the credentials supplied for this complete record."})
            continue
        if partial_experience:
            unverifiable = True
            entry.mandatory_issues.append({"requirement": rid, "issue": "cannot_verify",
                                           "detail": "Not evidenced in a partial record; cannot be supported or ruled out."})
        else:
            gaps.append(rid)
            detail = "; ".join(rv.notes) if rv.notes else "No supporting evidence in the supplied record."
            entry.mandatory_issues.append({"requirement": rid, "issue": "not_evidenced" if rv.status != "insufficient" else "below_threshold",
                                           "detail": detail})
    for rid, rv in rvs.items():
        if req_by_id[rid]["stated_as"] == "preferred" and rv.status not in ("evidenced", "alternative_path"):
            entry.unverified.append({"requirement": rid, "reason": "Preferred qualification not evidenced."})

    alt = any(p.startswith(("equivalency:", "combination:")) for rid in required_ids for p in rvs[rid].paths)
    desc = "; ".join(f"{rid} ({_paths_label(rvs[rid].paths)})" for rid in evidenced_required)
    if not evidenced_required:
        entry.group, entry.listable = "not_surfaced", False
        entry.reason = "No supplied evidence supports any required requirement."
    elif mandatory_unmet:
        entry.group = "not_surfaced"
        entry.reason = "A mandatory requirement is not met: " + "; ".join(
            f"{m['requirement']} — {m['detail']}" for m in entry.mandatory_issues if m["issue"] == "not_satisfied")
    elif gaps:
        entry.group = "not_surfaced"
        entry.reason = "Required evidence missing from a complete record: " + "; ".join(
            f"{m['requirement']} — {m['detail']}" for m in entry.mandatory_issues if m["requirement"] in gaps)
    elif unverifiable:
        entry.group = "insufficient"
        entry.why.append(f"Evidence supports {desc}; other mandatory requirements cannot be verified from the supplied record.")
    else:
        entry.group = "transferable" if alt else "direct"
        entry.why.append(f"Evidence supports every required requirement: {desc}.")
        if alt:
            entry.why.append("At least one requirement is supported through an alternative path that a recruiter must verify.")
    entry.signals = _signals(rvs)
    return entry


def _unique_sources(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One evidence quote per source sentence (several indicators can cite the same sentence)."""
    seen, out = set(), []
    for it in items:
        if it["source"] not in seen:
            seen.add(it["source"])
            out.append(it)
    return out


def _signals(rvs: dict[str, Any]) -> list[str]:
    out = []
    for rid, rv in rvs.items():
        for p in rv.paths:
            if p.startswith("equivalency:"):
                out.append(f"{rid}: transferable experience ({p.split(':', 1)[1]})")
            elif p.startswith("combination:"):
                out.append(f"{rid}: skill combination ({p.split(':', 1)[1]})")
            elif p == "terminology_variant":
                terms = sorted({e["matched"] for e in rv.evidence if e.get("path") == "terminology_variant"})
                out.append(f"{rid}: described as {', '.join(terms)}")
    return list(dict.fromkeys(out))
