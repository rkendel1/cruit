"""Stage 1-2: normalize inputs and interpret them through the versioned knowledge.

Everything here is deterministic. Each piece of evidence carries the source
location and original sentence it came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from ..knowledge.pack import KnowledgePack
from ..text import contains_term_family, find_terms, normalize, sentences, shorten

WEAK_RELATIONSHIPS = {"closely_related"}


@dataclass
class Entry:
    """A normalized unit of candidate evidence (an experience entry, or skills/credentials/learning)."""

    source: str
    title: str
    summary: str
    months: int
    domain: str | None
    kind: str  # experience | skills | credentials | learning | education

    @property
    def text(self) -> str:
        return f"{self.title}. {self.summary}" if self.title else self.summary

    def units(self) -> list[tuple[str, str]]:
        """(source, sentence) pairs, title first."""
        out = []
        if self.title:
            out.append((f"{self.source}.title", self.title))
        for i, s in enumerate(sentences(self.summary)):
            out.append((f"{self.source}.s{i + 1}", s))
        return out


def candidate_entries(cand: dict[str, Any]) -> list[Entry]:
    cid = cand["id"]
    entries = [
        Entry(f"candidate:{cid}/experience[{i}]", e["title"], e["summary"], e["months"], e.get("domain"), "experience")
        for i, e in enumerate(cand.get("experience", []))
    ]
    for kind in ("skills", "credentials", "learning", "education"):
        items = cand.get(kind) or []
        if items:
            entries.append(Entry(f"candidate:{cid}/{kind}", "", ". ".join(items), 0, None, kind))
    return entries


def resume_text(cand: dict[str, Any]) -> str:
    return "\n".join(e.text for e in candidate_entries(cand))


@dataclass
class Context:
    requisition: dict[str, Any]
    policy: dict[str, Any]
    pack: KnowledgePack
    decisions: dict[str, dict[str, Any]] = field(default_factory=dict)
    original: dict[str, Any] | None = None  # requisition as supplied, before human classification decisions

    def original_requirement(self, rid: str) -> dict[str, Any]:
        src = self.original or self.requisition
        return next(r for r in src["requirements"] if r["id"] == rid)

    @property
    def job_family(self) -> str:
        return self.requisition["job_family"]

    @property
    def req_id(self) -> str:
        return self.requisition["id"]

    def requirement(self, rid: str | None) -> dict[str, Any] | None:
        if not rid:
            return None
        return next((r for r in self.requisition["requirements"] if r["id"] == rid), None)

    # ---------------------------------------------------------------- policy
    def protected_reason(self, concept: str) -> str | None:
        if self.pack.is_regulated(concept):
            return f"{self.pack.concept_name(concept)} is a regulated credential in the knowledge base"
        for nn in self.policy.get("non_negotiable", []):
            if nn["concept"] == concept and self.pack.applies(nn.get("job_families"), self.job_family):
                return f"employer policy marks {self.pack.concept_name(concept)} non-negotiable ({nn['basis']}): {nn['rationale']}"
        return None

    def equivalency_status(self, eq_id: str) -> tuple[bool, str]:
        for rej in self.policy.get("rejected_equivalencies", []):
            if rej["id"] == eq_id and self.pack.applies(rej.get("job_families"), self.job_family):
                return False, f"rejected by employer policy ({rej['approved_by']}): {rej['rationale']}"
        for acc in self.policy.get("accepted_equivalencies", []):
            if acc["id"] == eq_id and self.pack.applies(acc.get("job_families"), self.job_family):
                return True, f"approved by employer policy ({acc['approved_by']})"
        return True, "general knowledge (not yet confirmed by employer policy)"

    # ---------------------------------------------------------------- concepts
    def strong_concepts(self, text: str) -> list[str]:
        hits = self.pack.concepts_in(text, self.job_family)
        return [c for c, es in hits.items() if any(e.relationship not in WEAK_RELATIONSHIPS for e in es)]

    def requirement_concepts(self, req: dict[str, Any]) -> list[str]:
        if req.get("concepts"):
            return list(req["concepts"])
        return sorted(self.strong_concepts(req["text"]))

    def rule_terms(self, rule: dict[str, Any]) -> list[str]:
        logic = rule["logic"]
        return list(logic.get("terms") or logic.get("titles") or logic.get("credentials") or [])

    def rule_concepts(self, rule: dict[str, Any]) -> list[str]:
        if rule.get("concepts"):
            return list(rule["concepts"])
        terms = self.rule_terms(rule)
        if terms:
            hits = self.pack.concepts_for_terms(terms, self.job_family)
            found = [c for c, es in hits.items() if any(e.relationship not in WEAK_RELATIONSHIPS for e in es)]
            if found:
                return sorted(found)
        return sorted(self.strong_concepts(rule["text"]))

    def linked_requirement(self, rule: dict[str, Any]) -> dict[str, Any] | None:
        if rule.get("linked_requirement"):
            return self.requirement(rule["linked_requirement"])
        rc = set(self.rule_concepts(rule))
        for req in self.requisition["requirements"]:
            if rc & set(self.requirement_concepts(req)):
                return req
        return None

    def supporting_skills(self, concept: str, kinds: tuple[str, ...] = ("tool", "credential")) -> list[str]:
        """Tools/credentials that support a capability (Terraform -> infrastructure as code).

        Component skills (renewals -> customer success) are deliberately excluded: one component
        is partial evidence, handled by equivalencies and combinations instead.
        """
        return sorted(
            sid for sid, sk in self.pack.skills.items()
            if self.pack.active(sk) and sk["kind"] in kinds
            and any(r["type"] == "supports" and r["target"] == concept for r in sk.get("relationships", []))
        )

    def recognized_terms(self, concepts: Iterable[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for c in concepts:
            for e in self.pack.recognized_terms(c, self.job_family):
                key = normalize(e.term)
                if key not in seen:
                    seen.add(key)
                    out.append(e.term)
        return out


# -------------------------------------------------------------------- candidate evidence
@dataclass
class ConceptEvidence:
    items: list[dict[str, str]]
    entries: set[str]  # entry sources that contributed
    paths: set[str]


def concept_evidence(
    ctx: Context,
    cand: dict[str, Any],
    concepts: list[str],
    *,
    requirement_text: str = "",
    allow_supporting: bool = False,
) -> ConceptEvidence:
    """Direct, variant and (optionally) supporting-skill evidence for any of the concepts."""
    supporting: dict[str, str] = {}
    if allow_supporting:
        for c in concepts:
            for s in ctx.supporting_skills(c):
                if s not in concepts:
                    supporting[s] = c
    wanted = set(concepts) | set(supporting)
    items: list[dict[str, str]] = []
    entries: set[str] = set()
    paths: set[str] = set()
    for entry in candidate_entries(cand):
        for src, sent in entry.units():
            hits = ctx.pack.concepts_in(sent, ctx.job_family)
            for concept, es in hits.items():
                if concept not in wanted:
                    continue
                strong = [e for e in es if e.relationship not in WEAK_RELATIONSHIPS]
                if not strong:
                    continue
                term = strong[0].term
                if concept in supporting:
                    path = "supporting_skill"
                elif requirement_text and contains_term_family(requirement_text, term):
                    path = "direct"
                elif requirement_text:
                    path = "terminology_variant"
                else:
                    path = "direct"
                paths.add(path)
                entries.add(entry.source)
                items.append({
                    "source": src,
                    "text": shorten(sent),
                    "path": path,
                    "matched": term,
                    "concept": concept,
                    "record": strong[0].record_id,
                })
    return ConceptEvidence(_dedupe(items), entries, paths)


def related_only_evidence(ctx: Context, cand: dict[str, Any], concepts: list[str]) -> list[dict[str, str]]:
    """Closely-related terminology hits: shown to reviewers, never counted as satisfying a requirement."""
    out = []
    for entry in candidate_entries(cand):
        for src, sent in entry.units():
            for concept, es in ctx.pack.concepts_in(sent, ctx.job_family).items():
                if concept in concepts and all(e.relationship in WEAK_RELATIONSHIPS for e in es):
                    out.append({"source": src, "text": shorten(sent), "path": "closely_related", "matched": es[0].term,
                                "concept": concept, "record": es[0].record_id})
    return _dedupe(out)


@dataclass
class EquivalencyMatch:
    eq_id: str
    satisfied: bool
    matched_indicators: list[str]
    missing_required: list[str]
    months: int
    items: list[dict[str, str]]
    entries: set[str]
    reason: str


def equivalency_evidence(ctx: Context, cand: dict[str, Any], eq: dict[str, Any]) -> EquivalencyMatch:
    disq = eq.get("disqualifying_terms", [])
    matched: dict[str, list[dict[str, str]]] = {}
    entry_months: dict[str, int] = {}
    required = set(eq["required_indicators"])
    required_entries: set[str] = set()
    for entry in candidate_entries(cand):
        for src, sent in entry.units():
            if disq and find_terms(sent, disq):
                continue
            for ind in eq["indicators"]:
                if all(find_terms(sent, group) for group in ind["all_of"]):
                    matched.setdefault(ind["id"], []).append({
                        "source": src, "text": shorten(sent), "path": f"equivalency:{eq['id']}",
                        "indicator": ind["id"], "matched": ind["description"],
                    })
                    entry_months[entry.source] = entry.months
                    if ind["id"] in required:
                        required_entries.add(entry.source)
    months = sum(entry_months[s] for s in required_entries) if required else sum(entry_months.values())
    missing_required = sorted(required - set(matched))
    enough = len(matched) >= eq["min_indicators"]
    long_enough = months >= eq.get("min_months", 0)
    satisfied = enough and not missing_required and long_enough
    if satisfied:
        reason = f"{len(matched)} of {len(eq['indicators'])} indicators present; {months} months of relevant experience"
    else:
        parts = []
        if missing_required:
            parts.append(f"missing required indicator(s) {missing_required}")
        if not enough:
            parts.append(f"only {len(matched)} of required {eq['min_indicators']} indicators")
        if not long_enough:
            parts.append(f"{months} months is below the {eq.get('min_months', 0)}-month minimum")
        reason = "; ".join(parts)
    items = [i for ind_items in matched.values() for i in ind_items]
    return EquivalencyMatch(eq["id"], satisfied, sorted(matched), missing_required, months,
                            _dedupe(items), set(entry_months), reason)


def months_for_entries(cand: dict[str, Any], sources: set[str]) -> int:
    return sum(e.months for e in candidate_entries(cand) if e.source in sources and e.kind == "experience")


def _dedupe(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    out = []
    for it in items:
        key = (it["source"], it.get("indicator") or it.get("concept"))
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out
