"""Portfolio overview across requisitions (blueprint §9.1): actionable work, not raw warning counts."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def build_portfolio(results: list[dict[str, Any]]) -> dict[str, Any]:
    checks_by_req: dict[str, set[str]] = defaultdict(set)
    family_checks: dict[str, Counter] = defaultdict(Counter)
    totals = Counter()
    work = []
    measured = []
    for r in results:
        rid = r["requisition"]["id"]
        fam = r["requisition"]["job_family"]
        totals["requisitions"] += 1
        for f in r["findings"]:
            st = f["disposition"].get("status", "pending")
            if f["category"] == "confirmed_inconsistency":
                totals["confirmed_inconsistencies"] += 1
            if f["category"] == "candidate_review_opportunity":
                totals["candidate_review_opportunities"] += 1
            if f["category"] == "measured_impact":
                measured.append({"requisition": rid, "title": f["title"]})
            if st == "pending":
                totals["awaiting_decision"] += 1
            if st == "accepted" and f.get("proposed_change"):
                totals["approved_corrections"] += 1
            if f["category"] in ("confirmed_inconsistency", "design_risk", "unverified_assumption"):
                checks_by_req[f["check"]].add(rid)
                family_checks[fam][f["check"]] += 1
            if st == "pending" and f["category"] in ("confirmed_inconsistency", "candidate_review_opportunity"):
                work.append({
                    "requisition": rid,
                    "finding": f["id"],
                    "level": f["evidence_level"],
                    "category": f["category"],
                    "title": f["title"],
                    "unlocks": len(f.get("unlocked_candidates", [])),
                })
    work.sort(key=lambda w: (w["category"] != "confirmed_inconsistency", -w["unlocks"], w["requisition"]))
    recurring = sorted(
        ({"check": c, "requisitions": sorted(reqs)} for c, reqs in checks_by_req.items() if len(reqs) > 1),
        key=lambda x: -len(x["requisitions"]),
    )
    return {
        "totals": dict(totals),
        "priority_work": work,
        "recurring_defects": recurring,
        "by_job_family": {fam: dict(cnt) for fam, cnt in family_checks.items()},
        "measured_outcomes": measured,
        "requisitions": [
            {"id": r["requisition"]["id"], "title": r["requisition"]["title"], "job_family": r["requisition"]["job_family"],
             "knowledge": r["knowledge"]["fingerprint"], **r["summary"]}
            for r in results
        ],
    }


def render_portfolio_markdown(p: dict[str, Any]) -> str:
    t = p["totals"]
    L = ["# Screening assurance — portfolio overview", ""]
    L.append(f"- Requisitions reviewed: **{t.get('requisitions', 0)}**")
    L.append(f"- Findings awaiting decisions: **{t.get('awaiting_decision', 0)}**")
    L.append(f"- Confirmed screening inconsistencies: **{t.get('confirmed_inconsistencies', 0)}**")
    L.append(f"- Approved corrections: **{t.get('approved_corrections', 0)}**")
    L.append(f"- Candidate-review opportunities: **{t.get('candidate_review_opportunities', 0)}**")
    L.append(f"- Measured outcomes: **{len(p['measured_outcomes'])}**")
    L.append("")
    L.append("## Requisitions")
    L.append("")
    L.append("| Requisition | Job family | L1 | L2 | L3 | Surfaced | Pending | Knowledge |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in p["requisitions"]:
        lv = r["by_level"]
        L.append(f"| {r['id']} {r['title']} | {r['job_family']} | {lv['level_1']} | {lv['level_2']} | {lv['level_3']} | "
                 f"{r['candidates_surfaced']}/{r['candidates_assessed']} | {r['pending_decisions']} | `{r['knowledge']}` |")
    L.append("")
    L.append("## Priority work")
    L.append("")
    L.append("Confirmed inconsistencies first (ordered by how many candidate-review opportunities depend on them), then candidates awaiting review.")
    L.append("")
    for w in p["priority_work"][:25]:
        extra = f" — unlocks {w['unlocks']} candidate(s)" if w["unlocks"] else ""
        L.append(f"- **{w['requisition']}** `{w['finding']}` (L{w['level']}) {w['title']}{extra}")
    L.append("")
    L.append("## Recurring screening defects")
    L.append("")
    if not p["recurring_defects"]:
        L.append("_No defect type recurs across requisitions yet._")
    for d in p["recurring_defects"]:
        L.append(f"- `{d['check']}` in {len(d['requisitions'])} requisitions: {', '.join(d['requisitions'])}")
    L.append("")
    L.append("## Patterns by job family")
    L.append("")
    for fam, checks in p["by_job_family"].items():
        L.append(f"- **{fam}**: " + ", ".join(f"{c} ×{n}" for c, n in sorted(checks.items(), key=lambda x: -x[1])))
    L.append("")
    if p["measured_outcomes"]:
        L.append("## Measured outcomes")
        L.append("")
        L += [f"- {m['requisition']}: {m['title']}" for m in p["measured_outcomes"]]
        L.append("")
    return "\n".join(L)
