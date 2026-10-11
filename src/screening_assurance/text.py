"""Deterministic text normalization and phrase matching.

Matching is intentionally literal and explainable: a term matches when its
normalized token sequence appears in the normalized text on token boundaries.
Every match returns the source sentence so conclusions stay traceable.
"""

from __future__ import annotations

import re
from functools import lru_cache

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[+#][+#]?)?")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+|\n+")


@lru_cache(maxsize=65536)
def tokens(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.lower().replace("&", " and ")))


def normalize(text: str) -> str:
    return " ".join(tokens(text))


def sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENT_SPLIT_RE.split(text or "")]
    return [p for p in parts if p]


def contains_term(text: str, term: str) -> bool:
    return _contains(tokens(text), tokens(term))


def _contains(hay: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    if not needle or len(needle) > len(hay):
        return False
    n = len(needle)
    first = needle[0]
    for i, tok in enumerate(hay):
        if tok == first and hay[i : i + n] == needle:
            return True
    return False


def _stem(tok: str) -> str:
    changed = True
    while changed:
        changed = False
        for suf in ("ing", "er", "s"):
            if tok.endswith(suf) and len(tok) - len(suf) >= 4:
                tok, changed = tok[: -len(suf)], True
                break
    return tok


def contains_term_family(text: str, term: str) -> bool:
    """Like contains_term, but tolerant of inflection. Used only to label evidence, never to match rules."""
    hay = tuple(_stem(t) for t in tokens(text))
    needle = tuple(_stem(t) for t in tokens(term))
    return _contains(hay, needle)


def find_terms(text: str, terms: list[str] | tuple[str, ...]) -> list[str]:
    """Return the terms (original spelling) that occur in text."""
    hay = tokens(text)
    return [t for t in terms if _contains(hay, tokens(t))]


def shorten(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
