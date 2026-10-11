"""Rendering of candidate rediscovery results (Markdown, HTML fragment, review list rows)."""

from __future__ import annotations

from html import escape
from typing import Any

GROUP_TITLE = {
    "direct": "Direct evidence",
    "transferable": "Potentially transferable — needs human review",
    "insufficient": "Insufficient evidence",
    "not_surfaced": "Not surfaced",
    "blocked": "Not available for action",
    "active_workflow": "Already in active review",
}
GROUP_HELP = {
    "direct": "Supplied evidence directly supports every required requirement.",
    "transferable": "Every required requirement is covered, at least one through an alternative path a recruiter must verify.",
    "insufficient": "Some required evidence exists, but the record is partial or a mandatory requirement cannot be verified.",
    "not_surfaced": "A mandatory requirement is not met or required evidence is missing from a complete record. Records with no relevant evidence are counted, not listed.",
    "blocked": "Not authorized for rediscovery, authorization expired, or evidence too old. Evidence is not shown.",
    "active_workflow": "Already in active review in the ATS.",
}
ACTIONABLE = ("direct", "transferable", "insufficient")


def review_rows(discovery: dict[str, Any], review_decisions: dict[str, Any] | None, run_id: str = "") -> list[dict[str, Any]]:
    """One row per actionable candidate, for CSV/YAML export."""
    dec = {d["candidate_id"]: d for d in (review_decisions or {}).get("decisions", [])}
    rows = []
    for e in discovery["entries"]:
        if e["group"] not in ACTIONABLE:
            continue
        d = dec.get(e["candidate_id"], {})
        rows.append({
            "candidate_id": e["candidate_id"],
            "source_kind": e["source"]["kind"],
            "source_record_ref": e["source"]["record_ref"],
            "group": e["group"],
            "why": " ".join(e["why"]),
            "requirements_supported": ", ".join(e["supported"]),
            "unverified": "; ".join(f"{u['requirement']}: {u['reason']}" for u in e["unverified"]),
            "mandatory_issues": "; ".join(f"{m['requirement']} ({m['issue']}): {m['detail']}" for m in e["mandatory_issues"]),
            "excluded_by_supplied_rule": ", ".join(x["rule"] for x in e["screening"].get("excluded_by", [])),
            "exclusion_basis": e["screening"].get("basis", ""),
            "evidence_updated_at": e["freshness"].get("evidence_updated_at", e["freshness"].get("status", "")),
            "constraints": " ".join(e["constraints"]),
            "verify_next": " ".join(e["verify_next"]),
            "disposition": d.get("disposition", "pending"),
            "rationale": d.get("rationale", ""),
            "decided_by": d.get("decided_by", ""),
            "decided_at": d.get("decided_at", ""),
            "knowledge": discovery["knowledge"],
            "run_id": run_id,
        })
    return rows


def render_discovery_markdown(discovery: dict[str, Any], review_decisions: dict[str, Any] | None = None) -> str:
    dec = {d["candidate_id"]: d for d in (review_decisions or {}).get("decisions", [])}
    c = discovery["counts"]
    L = ["", "## Candidate rediscovery", "",
         f"Knowledge `{discovery['knowledge']}` · evidence assessed as of {discovery['as_of']}. "
         "Groups describe the supplied evidence, not qualification; there is no ranking or match score.", ""]
    L.append("| Group | Candidates |")
    L.append("|---|---|")
    for g in ("direct", "transferable", "insufficient", "not_surfaced", "blocked", "active_workflow"):
        L.append(f"| {GROUP_TITLE[g]} | {c[g]} |")
    L.append("")
    L += [f"- {x}" for x in discovery["limitations"]]
    L.append("")
    for g in ACTIONABLE:
        items = [e for e in discovery["entries"] if e["group"] == g]
        if not items:
            continue
        L.append(f"### {GROUP_TITLE[g]}")
        L.append("")
        L.append(f"_{GROUP_HELP[g]}_")
        L.append("")
        for e in items:
            d = dec.get(e["candidate_id"])
            L.append(f"#### {e['candidate_id']} · {e['source']['kind'].replace('_', ' ')} · `{e['source']['record_ref']}`")
            L.append("")
            L += [f"- **Why:** {w}" for w in e["why"]]
            L.append(f"- **Supported:** {', '.join(e['supported']) or '—'}")
            if e["unverified"]:
                L.append("- **Unverified:** " + "; ".join(f"{u['requirement']} — {u['reason']}" for u in e["unverified"]))
            if e["mandatory_issues"]:
                L.append("- **Mandatory requirement issues:** " + "; ".join(f"{m['requirement']} ({m['issue'].replace('_', ' ')}) — {m['detail']}" for m in e["mandatory_issues"]))
            ex = e["screening"].get("excluded_by") or []
            L.append("- **Supplied screening rules:** " + (
                f"excluded by {', '.join(x['rule'] for x in ex)} — {e['screening']['basis']}" if ex else e["screening"].get("basis", "—")))
            if e["freshness"].get("evidence_updated_at"):
                L.append(f"- **Evidence updated:** {e['freshness']['evidence_updated_at']} ({e['freshness']['age_days']} days before assessment)")
            L += [f"- **Constraint:** {x}" for x in e["constraints"]]
            if e["verify_next"]:
                L.append("- **Verify next:** " + " ".join(e["verify_next"]))
            L.append("- **Recruiter decision:** " + (f"{d['disposition']} by {d['decided_by']} — {d['rationale']}" if d else "pending"))
            L.append("")
    listed = [e for e in discovery["entries"] if e["group"] in ("not_surfaced", "blocked") and e["listable"]]
    if listed:
        L.append("### Not surfaced or not available for action (explainable dispositions only)")
        L.append("")
        L.append("| Candidate | Group | Reason |")
        L.append("|---|---|---|")
        for e in listed:
            L.append(f"| {e['candidate_id']} | {e['group'].replace('_', ' ')} | {e['reason'].replace('|', '/')} |")
        L.append("")
    unlisted = sum(1 for e in discovery["entries"] if e["group"] == "not_surfaced" and not e["listable"])
    if unlisted:
        L.append(f"_{unlisted} record(s) had no supplied evidence for any required requirement and are counted, not listed._")
        L.append("")
    return "\n".join(L)


def render_discovery_html(discovery: dict[str, Any], review_decisions: dict[str, Any] | None = None) -> str:
    e_ = lambda s: escape("" if s is None else str(s))  # noqa: E731
    dec = {d["candidate_id"]: d for d in (review_decisions or {}).get("decisions", [])}
    c = discovery["counts"]
    parts = ['<h2 id="s9">Candidate rediscovery</h2>',
             f'<p class="meta">Knowledge <code>{e_(discovery["knowledge"])}</code> · evidence assessed as of {e_(discovery["as_of"])}. '
             "Groups describe the supplied evidence, not qualification. No ranking or match score.</p>",
             '<div class="stats">' + "".join(f'<div class="stat"><b>{c[g]}</b><span>{e_(GROUP_TITLE[g])}</span></div>'
                                              for g in ("direct", "transferable", "insufficient", "not_surfaced", "blocked")) + "</div>"]
    for g in ACTIONABLE:
        for e in [x for x in discovery["entries"] if x["group"] == g]:
            d = dec.get(e["candidate_id"])
            rows = "".join(
                f'<tr><td><b>{e_(r["id"])}</b><br><span class="meta">{e_(r["stated_as"])}</span></td><td>{e_(r["text"])}</td>'
                f'<td class="st-{e_(r["status"])}">{e_(r["status"].replace("_", " "))}<br><span class="meta">{e_(r["path_label"])}</span></td>'
                f'<td>{"".join(f"<div class=ev><span class=src>{e_(x["source"].split("/")[-1])}</span> {e_(x["text"])}</div>" for x in r["evidence"][:2]) or "—"}</td></tr>'
                for r in e["requirements"])
            parts.append(
                f'<article class="card"><div class="head"><span class="chip">{e_(GROUP_TITLE[g])}</span>'
                f'<span class="chip">{e_(e["source"]["kind"].replace("_", " "))}</span><span class="chip"><code>{e_(e["source"]["record_ref"])}</code></span></div>'
                f'<h3>{e_(e["candidate_id"])}</h3>' + "".join(f"<p>{e_(w)}</p>" for w in e["why"]) +
                f'<div class="tbl"><table><thead><tr><th>Req</th><th>Requirement</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div>' +
                ("<p><b>Mandatory requirement issues:</b> " + e_("; ".join(f"{m['requirement']}: {m['detail']}" for m in e["mandatory_issues"])) + "</p>" if e["mandatory_issues"] else "") +
                ("<p><b>Unverified:</b> " + e_("; ".join(f"{u['requirement']}: {u['reason']}" for u in e["unverified"])) + "</p>" if e["unverified"] else "") +
                "<p><b>Constraints:</b> " + e_(" ".join(e["constraints"])) + "</p>" +
                f'<p class="meta">Recruiter decision: {e_(d["disposition"] + " by " + d["decided_by"] + " — " + d["rationale"]) if d else "pending"}</p></article>')
    listed = [x for x in discovery["entries"] if x["group"] in ("not_surfaced", "blocked") and x["listable"]]
    if listed:
        parts.append('<details><summary>Not surfaced or not available for action</summary><div class="tbl"><table><tbody>' +
                     "".join(f"<tr><td><b>{e_(x['candidate_id'])}</b></td><td>{e_(x['group'])}</td><td>{e_(x['reason'])}</td></tr>" for x in listed) +
                     "</tbody></table></div></details>")
    return "".join(parts)
