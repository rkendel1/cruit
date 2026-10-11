"""Requisition assurance report (Markdown) and change proposals."""

from __future__ import annotations

from typing import Any

import yaml

from .common import (
    CLASSIFICATION_LABEL,
    LEVEL_LABEL,
    SECTIONS,
    STATUS_LABEL,
    candidate_review_answers,
)


def _esc(s: Any) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def _disp(f: dict[str, Any]) -> str:
    d = f["disposition"]
    if d.get("status") == "not_required":
        return "_No decision required (measured outcome)._"
    if d.get("status", "pending") == "pending":
        return "**Pending human decision**"
    return f"**{d['status']}** by {d.get('decided_by')} ({d.get('decided_at')}): {d.get('rationale')}"


def _finding_block(result: dict[str, Any], f: dict[str, Any]) -> list[str]:
    out = [f"### {f['title']}", "", f"`{f['id']}` · {LEVEL_LABEL[f['evidence_level']]} · confidence **{f['confidence']}** · check `{f['check']}`", ""]
    out.append(f["observation"])
    out.append("")
    if f["category"] == "candidate_review_opportunity":
        out += _candidate_block(result, f)
    elif f["evidence"]:
        out.append("**Evidence**")
        for e in f["evidence"]:
            out.append(f"- `{e.get('source')}` — {e.get('text')}")
        out.append("")
    if f["category"] != "candidate_review_opportunity":
        if f["category"] != "measured_impact" and (f.get("affected_candidates") or f.get("unlocked_candidates")):
            out.append(
                f"**Consequence in the supplied candidate sample:** {len(f['affected_candidates'])} candidate(s) "
                f"would pass this rule under this correction alone"
                + (f" ({', '.join(f['affected_candidates'])})" if f["affected_candidates"] else "")
                + f"; {len(f['unlocked_candidates'])} candidate-review opportunit"
                + ("y depends" if len(f["unlocked_candidates"]) == 1 else "ies depend")
                + " on it"
                + (f" ({', '.join(f['unlocked_candidates'])})." if f["unlocked_candidates"] else ".")
            )
            out.append("")
        out.append(f"**Proposed action:** {f['proposed_action']}")
        out.append("")
        out.append(f"**Expected benefit:** {f['expected_benefit']}  ")
        out.append(f"**Trade-off:** {f['tradeoffs']}")
        out.append("")
        if f["limitations"]:
            out.append("**Limitations**")
            out += [f"- {l}" for l in f["limitations"]]
            out.append("")
    refs = ", ".join(f"{r['kind']}:{r['id']}" for r in f["source_refs"])
    out.append(f"<sub>Sources: {refs}. Knowledge: `{f['knowledge_version']}`"
               + (f"; records: {', '.join(f['knowledge_refs'])}" if f["knowledge_refs"] else "") + ".</sub>")
    out.append("")
    out.append(f"Decision: {_disp(f)}")
    out.append("")
    return out


def _candidate_block(result: dict[str, Any], f: dict[str, Any]) -> list[str]:
    a = candidate_review_answers(result, f)
    out = ["**What requirements might this person satisfy, and what evidence supports it?**", ""]
    out.append("| Req | Stated | Status | Path | Evidence |")
    out.append("|---|---|---|---|---|")
    for r in a["requirements"]:
        ev = "<br>".join(f"`{e['source'].split('/')[-1]}` {_esc(e['text'])}" for e in r["evidence"][:2]) or "—"
        months = f" ({r['months']} mo)" if r["months"] is not None else ""
        out.append(f"| {r['id']} | {r['stated_as']} | {STATUS_LABEL[r['status']]}{months} | "
                   f"{_esc(', '.join(r['paths']) or '—')} | {ev} |")
    out.append("")
    out.append("**Excluded by:** " + "; ".join(f"{o['rule_id']} — {o['reason']}" for o in a["excluded_by"]))
    out.append("")
    if a["differs"]:
        out.append("**How their path differs from the conventional one**")
        out += [f"- {d}" for d in a["differs"]]
        out.append("")
    out.append("**What remains unproven**")
    out += [f"- {u}" for u in a["unproven"]]
    out.append("")
    out.append("**What the recruiter should verify next**")
    out += [f"- {v}" for v in a["verify"]]
    out.append("")
    return out


def render_markdown(result: dict[str, Any], discovery: dict[str, Any] | None = None,
                    review_decisions: dict[str, Any] | None = None) -> str:
    from .discovery import render_discovery_markdown
    body = _render_markdown(result)
    if discovery:
        body = body.rstrip() + "\n" + render_discovery_markdown(discovery, review_decisions) + "\n"
    return body


def _render_markdown(result: dict[str, Any]) -> str:
    req = result["requisition"]
    s = result["summary"]
    L = [f"# Requisition assurance report — {req['title']} ({req['id']})", ""]
    L.append(f"Job family `{req['job_family']}` · employer `{req['employer_id']}` · knowledge `{result['knowledge']['fingerprint']}` "
             f"({result['knowledge']['status']}) · engine {result['engine_version']} · run {result['run_at']}")
    L.append("")
    L.append("> This report recommends changes and human review. It does not reject, advance or hire anyone, "
             "and it does not claim any candidate was wrongly excluded. Level 1 findings are established by the "
             "supplied materials; Level 2 findings are risks that need human judgement; Level 3 findings are measured outcomes.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- **{s['by_level']['level_1']}** demonstrable inconsistencies (Level 1)")
    L.append(f"- **{s['by_level']['level_2']}** missed-talent risks and review opportunities (Level 2), "
             f"including **{s['candidates_surfaced']}** candidate(s) of {s['candidates_assessed']} assessed surfaced for human review")
    L.append(f"- **{s['by_level']['level_3']}** measured outcomes (Level 3)")
    L.append(f"- **{s['pending_decisions']}** findings awaiting a human decision")
    L.append("")
    L.append("**Inputs received:** " + ", ".join(f"{k.replace('_', ' ')}: `{v}`" for k, v in result["inputs"].items() if k != "notes"))
    L.append("")
    if result["limitations"]:
        L.append("**Limitations of this run**")
        L += [f"- {l}" for l in result["limitations"]]
        L.append("")

    L.append("## 1. Requirements and stated intent")
    L.append("")
    L.append("| ID | Requirement | Stated as | Proposed classification | Basis |")
    L.append("|---|---|---|---|---|")
    for r in result["requirements"]:
        cls = CLASSIFICATION_LABEL[r["proposed_classification"]] + (" 🔒" if r["protected"] else "")
        L.append(f"| {r['id']} | {_esc(r['text'])} | {r['stated_as']} | {cls} | {_esc(r['classification_basis'])} |")
    L.append("")
    L.append("🔒 = protected (legal, licensing or employer non-negotiable). No alternative path is ever proposed for protected requirements.")
    L.append("")

    L.append("## 2. Screening rules inspected")
    L.append("")
    L.append("| Rule | Type | Action | Linked requirement | Status | Findings |")
    L.append("|---|---|---|---|---|---|")
    for r in result["rules"]:
        L.append(f"| {r['id']} | {r['type']} | {r['action']} | {r['linked_requirement'] or '— (none)'} | "
                 f"{r['status'].replace('_', ' ')} | {len(r['finding_ids'])} |")
    L.append("")

    for idx, (key, title, pred) in enumerate(SECTIONS, start=3):
        if key == "measured":
            continue
        items = [f for f in result["findings"] if pred(f)]
        L.append(f"## {idx}. {title}")
        L.append("")
        if not items:
            L.append("_None found._")
            L.append("")
        for f in items:
            L += _finding_block(result, f)

    L.append("## 6. Recommended changes")
    L.append("")
    L.append("Suggested configuration changes, for the employer to implement in the ATS. Nothing is applied automatically.")
    L.append("")
    changes = [r for r in result["rules"] if r["corrected"]]
    if not changes:
        L.append("_No configuration changes proposed._")
    for r in changes:
        rule_findings = [f for f in result["findings"] if f["id"] in r["finding_ids"] and f.get("proposed_change")]
        L.append(f"**{r['id']}** — {r['text']}  ")
        L.append("Proposed by: " + ", ".join(f"`{f['id']}` ({f['disposition'].get('status')})" for f in rule_findings))
        L.append("")
        L.append("```yaml")
        L.append(yaml.safe_dump({"suggested_logic": r["corrected"]}, sort_keys=False).rstrip())
        L.append("```")
        L.append("")

    L.append("## 7. Human decisions and rationale")
    L.append("")
    decided = [f for f in result["findings"] if f["disposition"].get("status", "pending") not in ("pending", "not_required")]
    if not decided:
        L.append("_No decisions recorded yet. Record them in `decisions.yaml` (or export from the HTML report) and re-run._")
    else:
        L.append("| Finding | Decision | By | Rationale |")
        L.append("|---|---|---|---|")
        for f in decided:
            d = f["disposition"]
            L.append(f"| `{f['id']}` {_esc(f['title'])} | {d['status']} | {d.get('decided_by')} | {_esc(d.get('rationale'))} |")
    L.append("")

    L.append("## 8. Outcome measurements")
    L.append("")
    L += _measurement(result)

    L.append("## Appendix A — Candidates assessed but not surfaced")
    L.append("")
    rows = [c for c in result["candidates"] if not c["surfaced"]]
    if rows:
        L.append("| Candidate | ATS status | Excluded by | Reason |")
        L.append("|---|---|---|---|")
        for c in rows:
            L.append(f"| {c['candidate_id']} | {c['ats_status']} | {', '.join(c['excluded_by']) or '—'} | {_esc(c['reason'])} |")
    else:
        L.append("_None._")
    L.append("")
    if result["suppressed"]:
        L.append("## Appendix B — Protected and suppressed items")
        L.append("")
        for sup in result["suppressed"]:
            L.append(f"- {sup['kind']} `{sup['id']}`{' (rule ' + sup['rule'] + ')' if sup.get('rule') else ''}: {sup['reason']}")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def _measurement(result: dict[str, Any]) -> list[str]:
    m = result.get("measurement")
    L: list[str] = []
    if not m:
        L.append("_No outcome data supplied yet. Add `outcomes.yaml` with a documented baseline after corrections are implemented._")
        L.append("")
        return L
    L.append(f"Comparison method: **{m['comparison_method']}**")
    L.append("")
    me = m["measured"]
    L.append("**Measured**")
    L.append("")
    L.append("| Metric | Value |")
    L.append("|---|---|")
    for k, label in (
        ("additional_reviews", "Additional candidates receiving human review"),
        ("confirmed_meets_requirements", "Confirmed to meet requirements"),
        ("confirmed_does_not_meet", "Confirmed not to meet requirements (false positives)"),
        ("insufficient_evidence", "Insufficient evidence"),
        ("advanced_to_next_stage", "Advanced to next stage"),
        ("review_minutes", "Recruiter minutes spent on additional review"),
        ("surfacing_precision", "Share of additional reviews confirmed qualified"),
        ("incremental_qualified_per_recruiter_hour", "Incremental qualified candidates per recruiter hour"),
    ):
        L.append(f"| {label} | {me.get(k) if me.get(k) is not None else '—'} |")
    L.append("")
    if m.get("baseline"):
        L.append("| Period metric | Baseline | After change | Δ |")
        L.append("|---|---|---|---|")
        b, a, d = m["baseline"], m.get("after_change") or {}, m.get("deltas") or {}
        for k in ("applicants", "recruiter_reviewed", "qualified_candidates", "recruiter_hours", "qualified_yield",
                  "recruiter_hours_per_qualified", "days_to_qualified_shortlist"):
            L.append(f"| {k.replace('_', ' ')} | {b.get(k, '—')} | {a.get(k, '—')} | {d.get(k, '—')} |")
        L.append("")
    if m.get("estimated"):
        e = m["estimated"]
        L.append(f"**{e['label']}**")
        L.append("")
        for k, v in e.items():
            if k not in ("label", "assumptions"):
                L.append(f"- {k.replace('_', ' ')}: {v}")
        L.append(f"- assumptions: {e['assumptions']}")
        L.append("")
    if m.get("attribution"):
        L.append("**Attribution: which corrections the reviewed candidates depended on**")
        L.append("")
        L.append("| Finding | Reviewed | Met requirements | Minutes |")
        L.append("|---|---|---|---|")
        for a in m["attribution"]:
            L.append(f"| `{a['finding_id']}` {_esc(a['title'])} | {a['reviewed']} | {a['meets_requirements']} | {a['review_minutes']:g} |")
        L.append("")
    if m.get("new_risks_observed"):
        L.append("**New risks observed**")
        L += [f"- {r}" for r in m["new_risks_observed"]]
        L.append("")
    L.append(f"_{m['attribution_note']}_")
    L.append("")
    level3 = [f for f in result["findings"] if f["category"] == "measured_impact"]
    for f in level3:
        L += _finding_block(result, f)
    return L


def render_changes(result: dict[str, Any], *, include_pending: bool = False) -> dict[str, Any]:
    """Change proposals for ACCEPTED findings (optionally pending ones). Never applied automatically."""
    rules = {r["id"]: r for r in result["rules"]}
    out = []
    for f in result["findings"]:
        st = f["disposition"].get("status", "pending")
        if not f.get("proposed_change") or not (st == "accepted" or (include_pending and st == "pending")):
            continue
        out.append({
            "finding_id": f["id"],
            "rule": f["rule_id"],
            "decision": st,
            "change": f["proposed_change"],
            "instruction": f["proposed_action"],
            "current_rule_text": rules.get(f["rule_id"], {}).get("text"),
        })
    return {
        "requisition_id": result["requisition"]["id"],
        "knowledge": result["knowledge"]["fingerprint"],
        "note": "Suggested changes for the employer to implement in the ATS. Screening Assurance does not modify ATS configuration.",
        "changes": out,
    }
