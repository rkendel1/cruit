"""Versioned, externally editable knowledge: synonyms, equivalencies, and skills.

Knowledge is data, not code. The engine reads it; administrators edit,
validate, diff, release, promote and roll it back without code changes.
"""

from .pack import KnowledgePack, TermEntry, load_pack
from .validate import validate_pack, ValidationReport
from .diff import diff_packs
from .registry import KnowledgeRegistry

__all__ = [
    "KnowledgePack",
    "TermEntry",
    "load_pack",
    "validate_pack",
    "ValidationReport",
    "diff_packs",
    "KnowledgeRegistry",
]
