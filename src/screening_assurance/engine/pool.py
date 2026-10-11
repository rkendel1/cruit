"""Shared rules for using an authorized candidate pool: authorization, expiry and evidence freshness."""

from __future__ import annotations

from datetime import date
from typing import Any

DEFAULT_MAX_AGE_DAYS = 730


def _d(s: str) -> date:
    return date.fromisoformat(s[:10])


def pool_block_reason(cand: dict[str, Any], pool: dict[str, Any], as_of_d: date) -> tuple[str | None, dict[str, Any]]:
    """Why a pool record may not be used for action (or None), plus its freshness facts."""
    max_age = pool.get("max_evidence_age_days", DEFAULT_MAX_AGE_DAYS)
    age = (as_of_d - _d(cand["evidence_updated_at"])).days
    freshness = {"evidence_updated_at": cand["evidence_updated_at"], "age_days": age, "max_age_days": max_age,
                 "status": "fresh" if age <= max_age else "stale", "provenance": cand["evidence_provenance"]}
    auth = cand.get("authorization") or {}
    uses = auth.get("permitted_uses", pool["authorization"]["permitted_uses"])
    if "rediscovery_review" not in uses:
        return "Not authorized for rediscovery review (permitted uses: " + ", ".join(uses) + ").", freshness
    if auth.get("expires_at") and _d(auth["expires_at"]) < as_of_d:
        return f"Authorization expired on {auth['expires_at']}.", freshness
    if age > max_age:
        return (f"Evidence last updated {cand['evidence_updated_at']} ({age} days ago) exceeds the {max_age}-day limit.",
                freshness)
    return None, freshness


def default_as_of(pool: dict[str, Any] | None, run_at: str) -> str:
    return pool["exported_at"][:10] if pool else run_at[:10]


