"""Record-level comparison of two knowledge packs."""

from __future__ import annotations

from typing import Any

from .pack import KnowledgePack


def _records(pack: KnowledgePack) -> dict[str, tuple[str, dict[str, Any]]]:
    out: dict[str, tuple[str, dict[str, Any]]] = {}
    for s in pack.synonyms:
        out[s["id"]] = ("synonyms", s)
    for s in pack.skills.values():
        out[s["id"]] = ("skills", s)
    for c in pack.combinations:
        out[c["id"]] = ("skills.combinations", c)
    for e in pack.equivalencies.values():
        out[e["id"]] = ("equivalencies", e)
    return out


def diff_packs(old: KnowledgePack, new: KnowledgePack) -> dict[str, Any]:
    a, b = _records(old), _records(new)
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    modified = []
    warnings = []
    for rid in sorted(set(a) & set(b)):
        ra, rb = a[rid][1], b[rid][1]
        if ra == rb:
            continue
        fields = sorted(k for k in set(ra) | set(rb) if ra.get(k) != rb.get(k))
        modified.append({"id": rid, "document": b[rid][0], "fields": fields,
                         "version": [ra.get("version"), rb.get("version")]})
        if (rb.get("version") or 0) <= (ra.get("version") or 0):
            warnings.append(f"{rid} changed but its record version was not incremented")
    return {
        "from": old.fingerprint,
        "to": new.fingerprint,
        "added": [{"id": r, "document": b[r][0]} for r in added],
        "removed": [{"id": r, "document": a[r][0]} for r in removed],
        "modified": modified,
        "warnings": warnings,
    }


def format_diff(d: dict[str, Any]) -> str:
    lines = [f"Knowledge diff {d['from']} -> {d['to']}"]
    if not (d["added"] or d["removed"] or d["modified"]):
        lines.append("  (no record changes)")
    for x in d["added"]:
        lines.append(f"  + {x['id']}  [{x['document']}]")
    for x in d["removed"]:
        lines.append(f"  - {x['id']}  [{x['document']}]")
    for x in d["modified"]:
        lines.append(f"  ~ {x['id']}  [{x['document']}] v{x['version'][0]}->v{x['version'][1]}: {', '.join(x['fields'])}")
    for w in d["warnings"]:
        lines.append(f"  ! {w}")
    return "\n".join(lines)
