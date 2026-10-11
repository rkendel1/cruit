"""Stage 3-4: deterministic design checks over requirements and screening rules.

Each check emits explainable findings. Where a finding implies a concrete
configuration correction, it carries a *patch* used only to simulate the
consequences (which candidates would become eligible for review). Patches are
never applied to the employer's configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..text import normalize, shorten
from .interpret import Context
from .model import Finding, RequirementView, SourceRef, finding_id

REJECTING_DISPOSITIONS = {"rejected", "confirmed_necessary"}


@dataclass
class CheckOutput:
    findings: list[Finding] = field(default_factory=list)
    patches: dict[str, list[tuple[str, dict[str, Any]]]] = field(default_factory=dict)  # rule_id -> [(finding_id, patch)]
    protected_rules: dict[str, str] = field(default_factory=dict)
    suppressed: list[dict[str, Any]] = field(default_factory=list)

    def add(self, f: Finding, patch: dict[str, Any] | None = None) -> None:
        self.findings.append(f)
        if patch is not None and f.rule_id:
            f.proposed_change = patch
            self.patches.setdefault(f.rule_id, []).append((f.id, patch))


def _ref_rule(rule: dict[str, Any]) -> SourceRef:
    return SourceRef("rule", rule["id"], rule["text"])


def _ref_req(req: dict[str, Any]) -> SourceRef:
    return SourceRef("requirement", req["id"], req["text"])


def _new(ctx: Context, check: str, keys: list[str], **kw: Any) -> Finding:
    return Finding(
        id=finding_id(ctx.req_id, check, *keys),
        check=check,
        requisition_id=ctx.req_id,
        knowledge_version=ctx.pack.fingerprint,
        **kw,
    )


def _rule_terms_desc(ctx: Context, rule: dict[str, Any]) -> str:
    terms = ctx.rule_terms(rule)
    return ", ".join(f"'{t}'" for t in terms) if terms else "(question)"


def run_design_checks(ctx: Context) -> CheckOutput:
    out = CheckOutput()
    for rule in ctx.requisition["screening_rules"]:
        _check_rule(ctx, rule, out)
    for req in ctx.requisition["requirements"]:
        _check_requirement(ctx, req, out)
    return out


# ------------------------------------------------------------------------ rules
def _check_rule(ctx: Context, rule: dict[str, Any], out: CheckOutput) -> None:
    req = ctx.linked_requirement(rule)
    rule_concepts = ctx.rule_concepts(rule)
    req_concepts = ctx.requirement_concepts(req) if req else []
    protected = None
    for c in rule_concepts + req_concepts:
        protected = protected or ctx.protected_reason(c)
    if protected:
        out.protected_rules[rule["id"]] = protected
    rtype, logic = rule["type"], rule["logic"]
    terms = ctx.rule_terms(rule)

    # Terminology variants are checked even for protected rules: recognizing a
    # spelling variant of a license never lowers the bar.
    if rtype in ("keyword_filter", "minimum_experience", "title_filter", "credential_filter") and terms:
        _check_variants(ctx, rule, rule_concepts, terms, out)

    if protected:
        return

    if req is None:
        f = _new(
            ctx, "unstated_requirement_enforced", [rule["id"]],
            title=f"Rule {rule['id']} enforces a requirement the job description does not state",
            category="confirmed_inconsistency", evidence_level=1,
            observation=(
                f"Screening rule {rule['id']} ({rule['type']}, action: {rule['action']}) screens on "
                f"{_rule_terms_desc(ctx, rule)}, but no posted requirement corresponds to it."
            ),
            source_refs=[_ref_rule(rule)],
            evidence=[{"source": f"rule:{rule['id']}", "text": rule["text"]}],
            confidence="high",
            limitations=["The requirement may be genuine but undocumented; only the employer can confirm."],
            proposed_action=(
                "Confirm whether this is a genuine job requirement. If it is, add it to the posted requirements "
                "with its rationale; if not, remove the rule or convert it to a preference."
            ),
            expected_benefit="Applicants are screened only on requirements they were told about.",
            tradeoffs="If the requirement is genuine, removing the rule would admit unqualified applicants; confirm first.",
            rule_id=rule["id"],
        )
        out.add(f, {"removed": True})
        return

    stated_pref = req["stated_as"] == "preferred" or req.get("employer_classification") == "preferred"
    if stated_pref and rule["action"] == "reject":
        f = _new(
            ctx, "preferred_enforced_as_knockout", [rule["id"], req["id"]],
            title=f"Preferred qualification {req['id']} is enforced as a knockout by {rule['id']}",
            category="confirmed_inconsistency", evidence_level=1,
            observation=(
                f"Requirement {req['id']} is stated as preferred, but rule {rule['id']} rejects applicants who do not meet it."
            ),
            source_refs=[_ref_req(req), _ref_rule(rule)],
            evidence=[{"source": f"requirement:{req['id']}", "text": f"stated_as: preferred — {req['text']}"},
                      {"source": f"rule:{rule['id']}", "text": f"action: reject — {rule['text']}"}],
            confidence="high",
            limitations=[],
            proposed_action="Convert the rule into a scoring or ranking signal, or reclassify the requirement as essential with a documented rationale.",
            expected_benefit="Applicants who meet all essential requirements are no longer rejected for lacking a preference.",
            tradeoffs="More applicants reach review; ranking should still favour the preferred qualification.",
            rule_id=rule["id"], requirement_id=req["id"],
        )
        out.add(f, {"removed": True})

    if rtype == "minimum_experience" and req.get("min_years") is not None and logic.get("years", 0) > req["min_years"]:
        f = _new(
            ctx, "threshold_inconsistency", [rule["id"], req["id"]],
            title=f"{rule['id']} requires {logic['years']:g} years; the posting asks for {req['min_years']:g}",
            category="confirmed_inconsistency", evidence_level=1,
            observation=(
                f"Requirement {req['id']} states {req['min_years']:g}+ years, but rule {rule['id']} enforces "
                f"{logic['years']:g} years."
            ),
            source_refs=[_ref_req(req), _ref_rule(rule)],
            evidence=[{"source": f"requirement:{req['id']}", "text": req["text"]},
                      {"source": f"rule:{rule['id']}", "text": f"years: {logic['years']:g} — {rule['text']}"}],
            confidence="high", limitations=[],
            proposed_action=f"Align the rule threshold with the posted requirement ({req['min_years']:g} years), or update the posting if the higher threshold is genuinely required.",
            expected_benefit="Applicants who meet the posted threshold are no longer silently excluded.",
            tradeoffs="None if the posting reflects the real need.",
            rule_id=rule["id"], requirement_id=req["id"],
        )
        out.add(f, {"years": req["min_years"]})

    evidence_concepts, eq_ids, basis = _equivalent_path(ctx, req, req_concepts)
    blocks_equivalents = (
        rtype in ("knockout_question", "credential_filter")
        or (rtype == "keyword_filter" and eq_ids)  # literal match with no route for recognized equivalents
    )
    if (
        req.get("accepts_equivalent")
        and blocks_equivalents
        and not logic.get("allows_equivalent")
        and rule["action"] == "reject"
    ):
        f = _new(
            ctx, "equivalent_path_blocked", [rule["id"], req["id"]],
            title=f"{req['id']} accepts equivalent experience, but {rule['id']} has no equivalent path",
            category="confirmed_inconsistency", evidence_level=1,
            observation=(
                f"The posting accepts equivalent experience for {req['id']}, but rule {rule['id']} "
                + ("only recognizes the listed terms and has no route for recognized equivalent experience."
                   if rtype == "keyword_filter" else
                   "rejects applicants who answer or hold otherwise, regardless of equivalent evidence.")
            ),
            source_refs=[_ref_req(req), _ref_rule(rule)],
            evidence=[{"source": f"requirement:{req['id']}", "text": req["text"]},
                      {"source": f"rule:{rule['id']}", "text": rule["text"]}],
            confidence="high",
            limitations=[basis] if basis else [],
            proposed_action=(
                "Add an equivalent-evidence path (e.g. a follow-up question or recruiter review route) so "
                "applicants with equivalent experience are reviewed rather than rejected."
            ),
            expected_benefit="Restores the equivalency the employer already committed to in the posting.",
            tradeoffs="Equivalent-path applicants need recruiter verification time.",
            rule_id=rule["id"], requirement_id=req["id"], knowledge_refs=eq_ids,
        )
        patch = {"allows_equivalent": True, "equivalencies": eq_ids}
        if rtype != "keyword_filter":
            patch["evidence_concepts"] = evidence_concepts
        out.add(f, patch)

    if rtype == "credential_filter":
        cred_kinds = {"credential", "regulated_credential"}
        if not any((ctx.pack.skill(c) or {}).get("kind") in cred_kinds for c in req_concepts):
            f = _new(
                ctx, "credential_stricter_than_requirement", [rule["id"], req["id"]],
                title=f"{rule['id']} requires a credential where {req['id']} asks for proficiency",
                category="confirmed_inconsistency", evidence_level=1,
                observation=(
                    f"Requirement {req['id']} asks for a capability ('{shorten(req['text'], 90)}'), but rule {rule['id']} "
                    f"requires the credential {_rule_terms_desc(ctx, rule)}."
                ),
                source_refs=[_ref_req(req), _ref_rule(rule)],
                evidence=[{"source": f"requirement:{req['id']}", "text": req["text"]},
                          {"source": f"rule:{rule['id']}", "text": rule["text"]}],
                confidence="high", limitations=[],
                proposed_action="Accept demonstrated proficiency as well as the credential, or document why the credential itself is required.",
                expected_benefit="Proficient applicants without the specific certification are reviewed.",
                tradeoffs="Proficiency claims need verification during review.",
                rule_id=rule["id"], requirement_id=req["id"],
            )
            out.add(f, {"evidence_concepts": req_concepts})

    if rtype in ("keyword_filter", "minimum_experience", "title_filter"):
        missing = [c for c in req_concepts if c not in rule_concepts]
        if missing:
            add_terms = ctx.recognized_terms(missing)
            if req.get("accepts_equivalent"):
                for c in missing:
                    add_terms += ctx.recognized_terms(ctx.supporting_skills(c))
            names = [ctx.pack.concept_name(c) for c in missing]
            f = _new(
                ctx, "rule_narrower_than_requirement", [rule["id"], req["id"]],
                title=f"{rule['id']} is narrower than {req['id']}: it ignores {', '.join(names)}",
                category="confirmed_inconsistency", evidence_level=1,
                observation=(
                    f"Requirement {req['id']} can be met through {', '.join(names)}, but rule {rule['id']} only "
                    f"recognizes {_rule_terms_desc(ctx, rule)}."
                ),
                source_refs=[_ref_req(req), _ref_rule(rule)],
                evidence=[{"source": f"requirement:{req['id']}", "text": req["text"]},
                          {"source": f"rule:{rule['id']}", "text": rule["text"]}],
                confidence="high",
                limitations=["Concept recognition uses the knowledge pack; review the proposed terms before adopting them."],
                proposed_action=f"Extend the rule to recognize: {', '.join(_dedupe_terms(add_terms))}.",
                expected_benefit="Applicants who meet the requirement as written are no longer filtered out.",
                tradeoffs="Broader matching may increase review volume; terms are limited to the posted requirement.",
                rule_id=rule["id"], requirement_id=req["id"], knowledge_refs=missing,
            )
            out.add(f, {"add_terms": _dedupe_terms(add_terms)})

    if rtype in ("minimum_experience", "title_filter") and logic.get("field", "titles") == "titles":
        concepts = sorted(set(rule_concepts) | set(req_concepts))
        eqs = [eq["id"] for c in concepts for eq in ctx.pack.equivalencies_for(c, ctx.job_family)
               if ctx.equivalency_status(eq["id"])[0]]
        for c in concepts:
            for eq in ctx.pack.equivalencies_for(c, ctx.job_family):
                ok, why = ctx.equivalency_status(eq["id"])
                if not ok:
                    out.suppressed.append({"kind": "equivalency", "id": eq["id"], "rule": rule["id"], "reason": why})
        f = _new(
            ctx, "experience_path_narrower", [rule["id"]],
            title=f"{rule['id']} counts experience only under specific job titles",
            category="design_risk", evidence_level=2,
            observation=(
                f"Rule {rule['id']} only counts experience held under the titles {_rule_terms_desc(ctx, rule)}. "
                "The underlying capability can be demonstrated under other titles and in other domains."
            ),
            source_refs=[_ref_rule(rule)] + ([_ref_req(req)] if req else []),
            evidence=[{"source": f"rule:{rule['id']}", "text": rule["text"]}],
            confidence="medium",
            limitations=[
                "Whether alternative experience is equivalent must be judged by a recruiter or hiring manager.",
                "Title-based counting may reflect a deliberate employer choice; confirm intent.",
            ],
            proposed_action=(
                "Count relevant experience by responsibilities, not titles: match recognized terminology across "
                "the full résumé and route equivalency evidence to recruiter review."
            ),
            expected_benefit="Candidates whose titles differ from the conventional path reach human review.",
            tradeoffs="Responsibility-based matching needs recruiter verification; expect modest extra review time.",
            rule_id=rule["id"], requirement_id=req["id"] if req else None, knowledge_refs=eqs,
        )
        out.add(f, {"field": "resume", "add_terms": ctx.recognized_terms(concepts), "equivalencies": eqs})


def _equivalent_path(ctx: Context, req: dict[str, Any], req_concepts: list[str]) -> tuple[list[str], list[str], str]:
    """What evidence would satisfy 'or equivalent' for this requirement."""
    is_credential = any((ctx.pack.skill(c) or {}).get("kind") == "credential" for c in req_concepts)
    if is_credential:
        exp_reqs = [r for r in ctx.requisition["requirements"]
                    if r["stated_as"] == "required" and r.get("min_years") is not None]
        concepts = sorted({c for r in exp_reqs for c in ctx.requirement_concepts(r)})
        basis = ("Equivalent practical experience is interpreted as meeting the posted experience requirement(s) "
                 f"{', '.join(r['id'] for r in exp_reqs)}.") if exp_reqs else ""
        eq_ids = sorted({eq["id"] for c in concepts for eq in ctx.pack.equivalencies_for(c, ctx.job_family)
                         if ctx.equivalency_status(eq["id"])[0]})
        return concepts, eq_ids, basis
    eq_ids = sorted({eq["id"] for c in req_concepts for eq in ctx.pack.equivalencies_for(c, ctx.job_family)
                     if ctx.equivalency_status(eq["id"])[0]})
    return req_concepts, eq_ids, ""


def _check_variants(ctx: Context, rule: dict[str, Any], rule_concepts: list[str], terms: list[str], out: CheckOutput) -> None:
    have = {normalize(t) for t in terms}
    missing: list[str] = []
    records: set[str] = set()
    ambiguities: list[str] = []
    related: list[str] = []
    for c in rule_concepts:
        for e in ctx.pack.recognized_terms(c, ctx.job_family):
            if normalize(e.term) not in have and e.term not in missing:
                missing.append(e.term)
                records.add(e.record_id)
        for e in ctx.pack.term_entries(ctx.job_family):
            if e.concept == c and e.relationship == "closely_related" and e.term not in related:
                related.append(e.term)
    if not missing:
        return
    for syn in ctx.pack.synonyms:
        if syn["id"] in records:
            ambiguities += [f"'{a['term']}': {a['note']}" for a in syn.get("ambiguities", [])]
            ambiguities.append(syn["constraint"])
    names = ", ".join(ctx.pack.concept_name(c) for c in rule_concepts)
    limitations = ["Synonyms improve recognition; they do not establish competence."] + ambiguities
    if related:
        limitations.append(
            f"Closely related (not equivalent) terms not proposed: {', '.join(related)}. Verify case by case."
        )
    f = _new(
        ctx, "literal_term_missing_variants", [rule["id"]],
        title=f"{rule['id']} matches literally and misses recognized variants of {names}",
        category="design_risk", evidence_level=2,
        observation=(
            f"Rule {rule['id']} matches only {_rule_terms_desc(ctx, rule)}. The knowledge base records "
            f"{len(missing)} equivalent term(s) for {names} that the rule does not recognize."
        ),
        source_refs=[_ref_rule(rule)] + [SourceRef("knowledge", r) for r in sorted(records)],
        evidence=[{"source": f"knowledge:{r}", "text": f"recognized variant(s): {', '.join(missing)}"} for r in sorted(records)[:1]],
        confidence="high" if all(
            (next((s for s in ctx.pack.synonyms if s["id"] == r), None) or ctx.pack.skill(r) or {}).get("confidence") == "high"
            for r in records
        ) else "medium",
        limitations=limitations,
        proposed_action=f"Add recognized variants to the rule: {', '.join(missing)}.",
        expected_benefit="Applicants describing the same work in different words are no longer filtered out.",
        tradeoffs="Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.",
        rule_id=rule["id"], knowledge_refs=sorted(records),
    )
    out.add(f, {"add_terms": missing})


# ------------------------------------------------------------------ requirements
def _check_requirement(ctx: Context, req: dict[str, Any], out: CheckOutput) -> None:
    concepts = ctx.requirement_concepts(req)
    if any(ctx.protected_reason(c) for c in concepts):
        return
    orig = ctx.original_requirement(req["id"])
    if (
        orig["stated_as"] == "required"
        and not orig.get("employer_classification")
        and not orig.get("necessity_rationale")
        and not orig.get("linked_objectives")
    ):
        f = _new(
            ctx, "unverified_necessity", [req["id"]],
            title=f"Business necessity of required qualification {req['id']} is undocumented",
            category="unverified_assumption", evidence_level=2,
            observation=(
                f"{req['id']} ('{shorten(req['text'], 100)}') is marked required, but has no documented rationale "
                "and is not linked to any stated job objective."
            ),
            source_refs=[_ref_req(req)],
            evidence=[{"source": f"requirement:{req['id']}", "text": req["text"]}],
            confidence="medium",
            limitations=["The requirement may be genuinely necessary; this finding asks for clarification, not removal."],
            proposed_action=(
                "Classify the requirement: essential (document the rationale), preferred, or demonstrable "
                "through alternatives."
            ),
            expected_benefit="Required qualifications reflect what the job actually needs, and the rationale is auditable.",
            tradeoffs="Requires a short hiring-manager conversation.",
            requirement_id=req["id"],
        )
        out.add(f)
    if req["stated_as"] != "required" or req.get("employer_classification"):
        return
    if not req.get("accepts_equivalent"):
        eqs = [eq for c in concepts for eq in ctx.pack.equivalencies_for(c, ctx.job_family)
               if ctx.equivalency_status(eq["id"])[0]]
        if eqs:
            f = _new(
                ctx, "alternatives_not_considered", [req["id"]],
                title=f"{req['id']} could be demonstrated through recognized alternative experience",
                category="design_risk", evidence_level=2,
                observation=(
                    f"{req['id']} does not state whether equivalent experience is accepted. The knowledge base "
                    f"records {len(eqs)} conditional equivalenc{'y' if len(eqs) == 1 else 'ies'} for it."
                ),
                source_refs=[_ref_req(req)] + [SourceRef("knowledge", e["id"], e["summary"]) for e in eqs],
                evidence=[{"source": f"knowledge:{e['id']}", "text": e["summary"]} for e in eqs],
                confidence="medium",
                limitations=[l for e in eqs for l in e["limitations"]],
                proposed_action="Decide whether this requirement is demonstrable through alternatives and record the decision.",
                expected_benefit="Makes the employer's position on alternative paths explicit and consistent across rules.",
                tradeoffs="Accepting alternatives adds verification work for those candidates.",
                requirement_id=req["id"], knowledge_refs=[e["id"] for e in eqs],
            )
            out.add(f)


def requirement_views(ctx: Context) -> list[RequirementView]:
    views = []
    for req in ctx.requisition["requirements"]:
        concepts = ctx.requirement_concepts(req)
        protected = next((ctx.protected_reason(c) for c in concepts if ctx.protected_reason(c)), None)
        if req.get("employer_classification"):
            by_decision = not ctx.original_requirement(req["id"]).get("employer_classification")
            cls = req["employer_classification"]
            basis = "set by recorded human decision" if by_decision else "confirmed by employer in the requisition"
        elif protected:
            cls, basis = "essential", protected
        elif req["stated_as"] == "preferred":
            cls, basis = "preferred", "stated as preferred in the posting"
        elif req.get("accepts_equivalent"):
            cls, basis = "demonstrable_through_alternatives", "posting accepts equivalent experience"
        elif not req.get("necessity_rationale") and not req.get("linked_objectives"):
            cls, basis = "unverified_assumption", "required without documented rationale or linked objective"
        else:
            cls, basis = "essential", req.get("necessity_rationale") or f"linked to objectives {req.get('linked_objectives')}"
        views.append(RequirementView(
            id=req["id"], text=req["text"], stated_as=req["stated_as"], concepts=concepts,
            concept_names=[ctx.pack.concept_name(c) for c in concepts],
            proposed_classification=cls, classification_basis=basis,
            employer_classification=req.get("employer_classification"), protected=bool(protected),
            accepts_equivalent=bool(req.get("accepts_equivalent")), min_years=req.get("min_years"),
        ))
    return views


def active_patches(out: CheckOutput, findings_by_id: dict[str, Finding]) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    """Patches whose findings have not been rejected or confirmed-necessary by a human."""
    result: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for rule_id, items in out.patches.items():
        kept = [(fid, p) for fid, p in items
                if findings_by_id[fid].disposition.get("status") not in REJECTING_DISPOSITIONS]
        if kept:
            result[rule_id] = kept
    return result


def _dedupe_terms(terms: list[str]) -> list[str]:
    seen, out = set(), []
    for t in terms:
        k = normalize(t)
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out
