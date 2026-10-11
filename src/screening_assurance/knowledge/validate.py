"""Schema plus referential validation of a knowledge pack."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..contracts import ContractError
from ..text import normalize
from .pack import KnowledgePack, load_pack


@dataclass
class ValidationReport:
    path: str
    version: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "version": self.version,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "counts": self.counts,
        }


def _overlap(a: list[str], b: list[str]) -> bool:
    return "*" in a or "*" in b or bool(set(a) & set(b))


def validate_pack(path: str | Path) -> ValidationReport:
    report = ValidationReport(path=str(path))
    try:
        pack = load_pack(path, strict=True)
    except ContractError as exc:
        report.errors.extend(exc.errors)
        return report
    report.version = pack.version
    report.counts = {
        "synonyms": len(pack.synonyms),
        "skills": len(pack.skills),
        "combinations": len(pack.combinations),
        "equivalencies": len(pack.equivalencies),
    }
    _check(pack, report)
    return report


def _check(pack: KnowledgePack, r: ValidationReport) -> None:
    E, W = r.errors.append, r.warnings.append

    # Unique ids across the three documents.
    seen: dict[str, str] = {}
    for doc, ids in (
        ("synonyms", [s["id"] for s in pack.synonyms]),
        ("skills", [s["id"] for s in pack.raw["skills"].get("records", [])]),
        ("combinations", [c["id"] for c in pack.combinations]),
        ("equivalencies", [e["id"] for e in pack.raw["equivalencies"].get("records", [])]),
    ):
        for rid in ids:
            if rid in seen:
                E(f"duplicate id {rid} in {doc} (already defined in {seen[rid]})")
            seen[rid] = doc

    # Status warnings: only approved records are used by the engine.
    for rec in list(pack.synonyms) + list(pack.skills.values()) + list(pack.equivalencies.values()) + pack.combinations:
        if rec.get("review_status") != "approved":
            W(f"{rec['id']} has review_status={rec.get('review_status')} and will be ignored by the engine")

    # Synonyms
    for syn in pack.synonyms:
        concept = syn.get("concept")
        if concept and concept not in pack.skills:
            E(f"{syn['id']}: concept {concept} is not a defined skill")
        variant_terms = [normalize(v["term"]) for v in syn["variants"]]
        if len(set(variant_terms)) != len(variant_terms):
            E(f"{syn['id']}: duplicate variants")
        if normalize(syn["canonical"]) in variant_terms:
            E(f"{syn['id']}: canonical term repeated as a variant")
        known = set(variant_terms) | {normalize(syn["canonical"])}
        for ex in syn.get("exclusions", []):
            if normalize(ex["term"]) not in known:
                E(f"{syn['id']}: exclusion term '{ex['term']}' is not one of the record's terms")
        if syn["confidence"] == "low" and syn["relationship"] == "equivalent_terminology":
            W(f"{syn['id']}: low-confidence record asserts equivalent_terminology; consider closely_related")

    # Skills
    for sk in pack.skills.values():
        rels = defaultdict(set)
        for rel in sk.get("relationships", []):
            if rel["target"] not in pack.skills:
                E(f"{sk['id']}: relationship target {rel['target']} is not a defined skill")
            if rel["target"] == sk["id"]:
                E(f"{sk['id']}: relationship to itself")
            rels[rel["type"]].add(rel["target"])
        contradictory = rels["not_equivalent"] & (rels["transferable"] | rels["closely_related"] | rels["supports"])
        for target in sorted(contradictory):
            E(f"{sk['id']}: {target} is declared both not_equivalent and related/transferable/supporting")

    # Equivalencies
    for eq in pack.equivalencies.values():
        target = pack.skills.get(eq["target"])
        if not target:
            E(f"{eq['id']}: target {eq['target']} is not a defined skill")
        elif target["kind"] == "regulated_credential":
            E(
                f"{eq['id']}: targets regulated credential {eq['target']}. Adjacent experience is never "
                "equivalent to a legally required license or certification."
            )
        ind_ids = [i["id"] for i in eq["indicators"]]
        if len(set(ind_ids)) != len(ind_ids):
            E(f"{eq['id']}: duplicate indicator ids")
        missing = set(eq["required_indicators"]) - set(ind_ids)
        if missing:
            E(f"{eq['id']}: required_indicators not defined: {sorted(missing)}")
        if eq["min_indicators"] > len(ind_ids):
            E(f"{eq['id']}: min_indicators ({eq['min_indicators']}) exceeds number of indicators")
        if eq["min_indicators"] < len(eq["required_indicators"]):
            E(f"{eq['id']}: min_indicators is lower than the number of required indicators")
        if eq["min_indicators"] < 2 and eq["confidence"] != "high":
            W(f"{eq['id']}: a single indicator is weak evidence for a non-high-confidence equivalency")
        if not eq.get("disqualifying_terms"):
            W(f"{eq['id']}: no disqualifying_terms; participation-only evidence may be counted")

    # Combinations
    for combo in pack.combinations:
        for comp in combo["components"]:
            if comp not in pack.skills:
                E(f"{combo['id']}: component {comp} is not a defined skill")
        if combo["supports"] not in pack.skills:
            E(f"{combo['id']}: supports {combo['supports']} is not a defined skill")
        if combo["min_components"] > len(combo["components"]):
            E(f"{combo['id']}: min_components exceeds number of components")
        if pack.skills.get(combo["supports"], {}).get("kind") == "regulated_credential":
            E(f"{combo['id']}: a skill combination cannot stand in for a regulated credential")

    # Term collisions: one surface term mapping to different concepts in overlapping contexts.
    by_term: dict[str, list[tuple[str, str, list[str], set[str]]]] = defaultdict(list)
    for sk in pack.skills.values():
        for t in [sk["name"], *sk.get("alternate_names", [])]:
            by_term[normalize(t)].append((sk["id"], sk["id"], sk["contexts"], set()))
    for syn in pack.synonyms:
        amb = {normalize(a["term"]) for a in syn.get("ambiguities", [])}
        concept = syn.get("concept") or syn["id"]
        for t in [syn["canonical"], *[v["term"] for v in syn["variants"]]]:
            by_term[normalize(t)].append((concept, syn["id"], syn["contexts"], amb))
    for term, uses in by_term.items():
        for i in range(len(uses)):
            for j in range(i + 1, len(uses)):
                ci, ri, xi, ai = uses[i]
                cj, rj, xj, aj = uses[j]
                if ci != cj and _overlap(xi, xj) and term not in ai and term not in aj:
                    E(
                        f"term '{term}' maps to {ci} ({ri}) and {cj} ({rj}) in overlapping contexts "
                        "without a documented ambiguity"
                    )
