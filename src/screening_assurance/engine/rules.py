"""Deterministic simulation of screening rules against candidate evidence.

Used to answer "could this candidate have been excluded by this rule?" and
"would this candidate become eligible for review under the proposed correction?".
The simulator never changes the employer's configuration.
"""

from __future__ import annotations

import copy
from typing import Any

from ..text import find_terms
from .interpret import Context, candidate_entries, concept_evidence, equivalency_evidence
from .model import RuleOutcome


def _field_text(cand: dict[str, Any], field: str) -> list[str]:
    entries = candidate_entries(cand)
    if field == "titles":
        return [e.title for e in entries if e.kind == "experience"]
    if field == "skills":
        return list(cand.get("skills") or [])
    return [e.text for e in entries]


def evaluate_rule(ctx: Context, rule: dict[str, Any], spec: dict[str, Any], cand: dict[str, Any]) -> RuleOutcome:
    """Evaluate one rule (with logic `spec`, which may be a corrected copy) against a candidate."""
    rid = rule["id"]
    if spec.get("removed"):
        return RuleOutcome(rid, True, "rule not applied under proposed correction")
    rtype = rule["type"]

    if rtype == "keyword_filter":
        texts = _field_text(cand, spec.get("field", "resume"))
        joined = "\n".join(texts)
        found = find_terms(joined, spec.get("terms", []))
        ok = bool(found) if spec.get("match", "any") == "any" else len(found) == len(spec.get("terms", []))
        if ok:
            return RuleOutcome(rid, True, f"matched {found}")
        for eq_id in spec.get("equivalencies", []) if spec.get("allows_equivalent") else []:
            eq = ctx.pack.equivalencies.get(eq_id)
            if eq and equivalency_evidence(ctx, cand, eq).satisfied:
                return RuleOutcome(rid, True, f"equivalent path: {eq_id} satisfied")
        return RuleOutcome(rid, False, "no listed term found")

    if rtype in ("minimum_experience", "title_filter"):
        field = spec.get("field", "titles")
        terms = spec.get("terms") or spec.get("titles") or []
        months = 0
        matched_sources: set[str] = set()
        for e in candidate_entries(cand):
            if e.kind != "experience":
                continue
            hay = e.title if field == "titles" else e.text
            if find_terms(hay, terms):
                months += e.months
                matched_sources.add(e.source)
        for eq_id in spec.get("equivalencies", []):
            eq = ctx.pack.equivalencies.get(eq_id)
            if not eq:
                continue
            m = equivalency_evidence(ctx, cand, eq)
            if not m.missing_required:
                for e in candidate_entries(cand):
                    if e.source in m.entries and e.source not in matched_sources and e.kind == "experience":
                        months += e.months
                        matched_sources.add(e.source)
        if rtype == "title_filter" and "years" not in spec:
            ok = bool(matched_sources)
            return RuleOutcome(rid, ok, "matching title found" if ok else "no matching title")
        need = float(spec.get("years", 0)) * 12
        return RuleOutcome(rid, months >= need, f"{months} relevant months vs {int(need)} required")

    if rtype == "credential_filter":
        creds = "\n".join(cand.get("credentials") or [])
        found = find_terms(creds, spec.get("credentials", []))
        if found:
            return RuleOutcome(rid, True, f"holds {found}")
        alt = spec.get("evidence_concepts")
        if alt:
            ev = concept_evidence(ctx, cand, alt, allow_supporting=True)
            if ev.items:
                return RuleOutcome(rid, True, "credential absent; capability evidenced under proposed correction")
        return RuleOutcome(rid, False, "listed credential not held")

    if rtype == "knockout_question":
        answer = (cand.get("knockout_answers") or {}).get(rid)
        required = spec.get("required_answer", "yes")
        if answer == required:
            return RuleOutcome(rid, True, f"answered '{answer}'")
        if spec.get("allows_equivalent") and spec.get("evidence_concepts"):
            ev = concept_evidence(ctx, cand, spec["evidence_concepts"], allow_supporting=True)
            if ev.items:
                return RuleOutcome(rid, True, "equivalent path: capability evidenced directly")
            for eq_id in spec.get("equivalencies", []):
                eq = ctx.pack.equivalencies.get(eq_id)
                if eq and equivalency_evidence(ctx, cand, eq).satisfied:
                    return RuleOutcome(rid, True, f"equivalent path: {eq_id} satisfied")
        if answer is None:
            return RuleOutcome(rid, None, "no recorded answer")
        return RuleOutcome(rid, False, f"answered '{answer}', rule requires '{required}'")

    return RuleOutcome(rid, None, f"unsupported rule type {rtype}")


def apply_patches(rule: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge correction patches into a copy of the rule's logic."""
    spec = copy.deepcopy(rule["logic"])
    for p in patches:
        if p.get("removed"):
            return {"removed": True}
        for key, val in p.items():
            if key in ("add_terms",):
                target = "credentials" if "credentials" in spec else "terms"
                base = spec.get(target) or spec.get("titles") or []
                merged = list(base)
                for t in val:
                    if t.lower() not in {m.lower() for m in merged}:
                        merged.append(t)
                spec[target] = merged
                spec.pop("titles", None)
            elif key in ("equivalencies", "evidence_concepts"):
                spec[key] = sorted(set(spec.get(key, [])) | set(val))
            else:
                spec[key] = val
    return spec
