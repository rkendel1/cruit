"""Result types produced by the diagnostic engine."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any

EVIDENCE_LEVELS = {
    1: "Demonstrable inconsistency",
    2: "Plausible missed-talent risk",
    3: "Measured impact",
}

CATEGORIES = (
    "confirmed_inconsistency",       # level 1
    "mandatory_protected",           # level 1: a protected requirement is correctly enforced; nothing to relax
    "design_risk",                   # level 2: knowledge-based design risk in rules
    "unverified_assumption",         # level 2: requirement whose necessity needs clarification
    "candidate_review_opportunity",  # level 2: specific candidate(s) worth human review
    "input_limitation",              # level 2: what the supplied inputs cannot establish
    "measured_impact",               # level 3
)


def finding_id(requisition_id: str, check: str, *keys: str) -> str:
    """Stable id: independent of knowledge version so human decisions carry across reruns."""
    digest = hashlib.sha1("|".join([requisition_id, check, *keys]).encode()).hexdigest()[:8]
    return f"SA-{requisition_id}-{digest}"


@dataclass
class SourceRef:
    kind: str   # requirement | rule | candidate | knowledge | policy | requisition | outcome
    id: str
    text: str = ""


@dataclass
class Finding:
    id: str
    check: str
    title: str
    category: str
    evidence_level: int
    requisition_id: str
    knowledge_version: str
    observation: str
    source_refs: list[SourceRef]
    evidence: list[dict[str, str]]
    confidence: str
    limitations: list[str]
    proposed_action: str
    expected_benefit: str
    tradeoffs: str
    rule_id: str | None = None
    requirement_id: str | None = None
    candidate_id: str | None = None
    affected_candidates: list[str] = field(default_factory=list)
    unlocked_candidates: list[str] = field(default_factory=list)
    proposed_change: dict[str, Any] | None = None
    knowledge_refs: list[str] = field(default_factory=list)
    related_findings: list[str] = field(default_factory=list)
    disposition: dict[str, Any] = field(default_factory=lambda: {"status": "pending"})
    risk_category: str | None = None
    simulation: dict[str, Any] | None = None

    @property
    def evidence_label(self) -> str:
        return EVIDENCE_LEVELS[self.evidence_level]

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence_label"] = self.evidence_label
        return d


@dataclass
class RuleOutcome:
    rule_id: str
    passed: bool | None  # None = cannot be determined from supplied inputs
    reason: str


@dataclass
class RequirementEvidence:
    requirement_id: str
    status: str  # evidenced | alternative_path | insufficient | not_evidenced | pending_clarification | protected_missing
    paths: list[str] = field(default_factory=list)          # direct | terminology_variant | supporting_skill | equivalency:<id> | combination:<id>
    evidence: list[dict[str, str]] = field(default_factory=list)
    relevant_months: int | None = None
    notes: list[str] = field(default_factory=list)
    verify_next: list[str] = field(default_factory=list)


@dataclass
class CandidateAssessment:
    candidate_id: str
    ats_status: str
    current_rules: list[RuleOutcome]
    corrected_rules: list[RuleOutcome]
    requirements: list[RequirementEvidence]
    excluded_by: list[str]
    passes_corrected: bool
    evidence_coverage: str  # complete | partial | none
    nontraditional_signals: list[str]
    surfaced: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RequirementView:
    id: str
    text: str
    stated_as: str
    concepts: list[str]
    concept_names: list[str]
    proposed_classification: str
    classification_basis: str
    employer_classification: str | None
    protected: bool
    accepts_equivalent: bool
    min_years: float | None


@dataclass
class RuleView:
    id: str
    type: str
    text: str
    action: str
    linked_requirement: str | None
    concepts: list[str]
    status: str  # protected | inspected | corrected-proposal
    corrected: dict[str, Any] | None
    finding_ids: list[str]


@dataclass
class DiagnosticResult:
    requisition: dict[str, Any]
    policy: dict[str, Any]
    knowledge: dict[str, Any]
    engine_version: str
    run_at: str
    inputs: dict[str, Any]
    limitations: list[str]
    requirements: list[RequirementView]
    rules: list[RuleView]
    findings: list[Finding]
    candidates: list[CandidateAssessment]
    suppressed: list[dict[str, Any]]
    measurement: dict[str, Any] | None = None

    def findings_by_category(self, category: str) -> list[Finding]:
        return [f for f in self.findings if f.category == category]

    def as_dict(self) -> dict[str, Any]:
        return {
            "requisition": {k: self.requisition.get(k) for k in ("id", "title", "job_family", "employer_id", "ats")},
            "policy": {k: self.policy.get(k) for k in ("employer_id", "policy_version")},
            "knowledge": self.knowledge,
            "engine_version": self.engine_version,
            "run_at": self.run_at,
            "inputs": self.inputs,
            "limitations": self.limitations,
            "requirements": [asdict(r) for r in self.requirements],
            "rules": [asdict(r) for r in self.rules],
            "findings": [f.as_dict() for f in self.findings],
            "candidates": [c.as_dict() for c in self.candidates],
            "suppressed": self.suppressed,
            "measurement": self.measurement,
            "summary": self.summary(),
        }

    def summary(self) -> dict[str, Any]:
        by_cat: dict[str, int] = {}
        for f in self.findings:
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        pending = sum(1 for f in self.findings if f.disposition.get("status") == "pending" and f.category != "measured_impact")
        return {
            "findings": len(self.findings),
            "by_category": by_cat,
            "by_level": {f"level_{lvl}": sum(1 for f in self.findings if f.evidence_level == lvl) for lvl in (1, 2, 3)},
            "pending_decisions": pending,
            "candidates_assessed": len(self.candidates),
            "candidates_surfaced": sum(1 for c in self.candidates if c.surfaced),
        }
