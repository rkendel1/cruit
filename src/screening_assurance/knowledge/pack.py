"""In-memory representation of a knowledge pack and its lookup indexes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..contracts import ContractError, read_yaml, schema_errors
from ..text import find_terms, normalize

ACTIVE_STATUS = "approved"


@dataclass(frozen=True)
class TermEntry:
    """One recognizable surface term and the concept it expresses."""

    term: str
    concept: str            # skill id (or term.* id when a synonym has no skill concept)
    record_id: str          # knowledge record that contributed this term
    relationship: str       # canonical | equivalent_terminology | closely_related | skill_name | alternate_name
    confidence: str


@dataclass
class KnowledgePack:
    path: Path
    manifest: dict[str, Any]
    synonyms: list[dict[str, Any]]
    skills: dict[str, dict[str, Any]]
    combinations: list[dict[str, Any]]
    equivalencies: dict[str, dict[str, Any]]
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    # ------------------------------------------------------------------ identity
    @property
    def pack_id(self) -> str:
        return self.manifest["pack"]

    @property
    def version(self) -> str:
        return self.manifest["version"]

    @property
    def checksum(self) -> str:
        canonical = json.dumps(
            {k: self.raw.get(k) for k in ("synonyms", "equivalencies", "skills")},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    @property
    def fingerprint(self) -> str:
        """Stable identifier recorded on every finding for reproducibility."""
        return f"{self.pack_id}@{self.version}+{self.checksum[:10]}"

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def applies(contexts: Iterable[str] | None, job_family: str) -> bool:
        contexts = list(contexts or ["*"])
        return "*" in contexts or job_family in contexts

    def active(self, record: dict[str, Any]) -> bool:
        return record.get("review_status") == ACTIVE_STATUS

    def skill(self, concept: str) -> dict[str, Any] | None:
        return self.skills.get(concept)

    def concept_name(self, concept: str) -> str:
        sk = self.skills.get(concept)
        if sk:
            return sk["name"]
        for syn in self.synonyms:
            if syn["id"] == concept:
                return syn["canonical"]
        return concept

    def is_regulated(self, concept: str) -> bool:
        sk = self.skills.get(concept)
        return bool(sk and sk.get("kind") == "regulated_credential")

    # ------------------------------------------------------------------ term index
    def term_entries(self, job_family: str) -> list[TermEntry]:
        cache = self.__dict__.setdefault("_term_cache", {})
        if job_family in cache:
            return cache[job_family]
        entries: list[TermEntry] = []
        for sk in self.skills.values():
            if not self.active(sk) or not self.applies(sk["contexts"], job_family):
                continue
            entries.append(TermEntry(sk["name"], sk["id"], sk["id"], "skill_name", sk["confidence"]))
            for alt in sk.get("alternate_names", []):
                entries.append(TermEntry(alt, sk["id"], sk["id"], "alternate_name", sk["confidence"]))
        for syn in self.synonyms:
            if not self.active(syn) or not self.applies(syn["contexts"], job_family):
                continue
            concept = syn.get("concept") or syn["id"]
            excluded = {
                normalize(ex["term"])
                for ex in syn.get("exclusions", [])
                if self.applies(ex["contexts"], job_family)
            }
            if normalize(syn["canonical"]) not in excluded:
                # A closely-related record's canonical term is itself only closely related to the concept.
                rel = "canonical" if syn["relationship"] == "equivalent_terminology" else syn["relationship"]
                entries.append(TermEntry(syn["canonical"], concept, syn["id"], rel, syn["confidence"]))
            for var in syn["variants"]:
                if "contexts" in var and not self.applies(var["contexts"], job_family):
                    continue
                if normalize(var["term"]) in excluded:
                    continue
                entries.append(TermEntry(var["term"], concept, syn["id"], syn["relationship"], syn["confidence"]))
        cache[job_family] = entries
        return entries

    def concepts_in(self, text: str, job_family: str) -> dict[str, list[TermEntry]]:
        """Concepts whose recognized terms appear in text, with the matching entries."""
        hits: dict[str, list[TermEntry]] = {}
        hay_terms = self.term_entries(job_family)
        found = set(find_terms(text, [e.term for e in hay_terms]))
        for entry in hay_terms:
            if entry.term in found:
                hits.setdefault(entry.concept, []).append(entry)
        return hits

    def concepts_for_terms(self, terms: list[str], job_family: str) -> dict[str, list[TermEntry]]:
        """Concepts that a list of rule terms refers to (exact normalized match on a term)."""
        wanted = {normalize(t) for t in terms}
        hits: dict[str, list[TermEntry]] = {}
        for entry in self.term_entries(job_family):
            if normalize(entry.term) in wanted:
                hits.setdefault(entry.concept, []).append(entry)
        return hits

    def recognized_terms(
        self, concept: str, job_family: str, relationships: tuple[str, ...] = ("canonical", "equivalent_terminology", "skill_name", "alternate_name")
    ) -> list[TermEntry]:
        seen: set[str] = set()
        out = []
        for e in self.term_entries(job_family):
            if e.concept == concept and e.relationship in relationships:
                key = normalize(e.term)
                if key not in seen:
                    seen.add(key)
                    out.append(e)
        return out

    def equivalencies_for(self, concept: str, job_family: str) -> list[dict[str, Any]]:
        return [
            eq
            for eq in self.equivalencies.values()
            if eq["target"] == concept and self.active(eq) and self.applies(eq["applicable_contexts"], job_family)
        ]

    def combinations_supporting(self, concept: str) -> list[dict[str, Any]]:
        return [c for c in self.combinations if c["supports"] == concept and self.active(c)]

    def related(self, concept: str, rel_type: str) -> list[str]:
        sk = self.skills.get(concept) or {}
        return [r["target"] for r in sk.get("relationships", []) if r["type"] == rel_type]

    def not_equivalent(self, a: str, b: str) -> bool:
        return b in self.related(a, "not_equivalent") or a in self.related(b, "not_equivalent")


def _doc_path(root: Path, rel: str) -> Path:
    p = (root / rel).resolve()
    if root.resolve() not in p.parents and p != root.resolve():
        raise ContractError(root / rel, ["document path escapes the knowledge pack directory"])
    return p


def load_pack(path: str | Path, *, strict: bool = True) -> KnowledgePack:
    """Load a knowledge pack directory (manifest.yaml + three documents).

    With strict=True, schema errors raise ContractError. Referential checks
    live in validate_pack().
    """
    root = Path(path)
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        raise ContractError(manifest_path, ["manifest.yaml not found; not a knowledge pack"])
    manifest = read_yaml(manifest_path)
    errors = [f"manifest: {e}" for e in schema_errors("manifest", manifest)]
    raw: dict[str, Any] = {}
    if not errors:
        for doc in ("synonyms", "equivalencies", "skills"):
            doc_path = _doc_path(root, manifest["documents"][doc])
            data = read_yaml(doc_path)
            raw[doc] = data
            errors += [f"{doc}: {e}" for e in schema_errors(doc, data)]
    if errors and strict:
        raise ContractError(root, errors)
    syn = (raw.get("synonyms") or {}).get("records", [])
    eqs = (raw.get("equivalencies") or {}).get("records", [])
    skills_doc = raw.get("skills") or {}
    return KnowledgePack(
        path=root,
        manifest=manifest,
        synonyms=syn,
        skills={s["id"]: s for s in skills_doc.get("records", [])},
        combinations=skills_doc.get("combinations", []),
        equivalencies={e["id"]: e for e in eqs},
        raw=raw,
    )

