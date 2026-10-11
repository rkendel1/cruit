"""Evaluation of forward screening assurance (screening-risk findings and correction simulations).

Runs inside the existing screening-case harness: every case's diagnostic result already carries
the simulations, so this module only scores them against expert labels and explicit, labeled
SYNTHETIC expectations. It never represents real-world accuracy.
"""

from __future__ import annotations

from typing import Any

SYNTHETIC_LABEL = "SYNTHETIC FIXTURE RESULTS — not a measure of real-world accuracy"


def _match(f: dict[str, Any], m: dict[str, Any]) -> bool:
    if f["check"] != m["check"]:
        return False
    for key, attr in (("rule", "rule_id"), ("requirement", "requirement_id"), ("candidate", "candidate_id")):
        if key in m and f.get(attr) != m[key]:
            return False
    return True


def check_expectations(case: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for exp in case.get("simulation_expectations", []):
        f = next((x for x in result["findings"] if _match(x, exp["finding"])), None)
        problems: list[str] = []
        sim = (f or {}).get("simulation") or {}
        if not f:
            problems.append("finding not produced")
        else:
            if "evaluable" in exp and bool(sim.get("evaluable")) != exp["evaluable"]:
                problems.append(f"evaluable is {bool(sim.get('evaluable'))}")
            if exp.get("no_correction") and (f.get("proposed_change") or sim.get("proposed")):
                problems.append("a correction is proposed")
            if exp.get("category"):
                got = set((sim.get("categories") or {}).get(exp["category"], []))
                missing = [c for c in exp.get("includes", []) if c not in got]
                present = [c for c in exp.get("excludes", []) if c in got]
                if missing:
                    problems.append(f"{exp['category']} is missing {missing}")
                if present:
                    problems.append(f"{exp['category']} wrongly contains {present}")
        out.append({"scenario": exp["scenario"], "met": not problems, "problems": problems,
                    "finding_id": f["id"] if f else None})
    return out


def risk_metrics(case: dict[str, Any], result: dict[str, Any], *, blocked_pool_ids: set[str],
                 rejected_equivalencies: set[str]) -> dict[str, Any]:
    labels = case.get("expert_labels", {})
    sims = [(f, f["simulation"]) for f in result["findings"]
            if f.get("simulation") and f["simulation"].get("evaluable") and f["simulation"].get("categories")]
    eligible: set[str] = set()
    excluded_by_rule: set[str] = set()
    insufficient: set[str] = set()
    pool_ids: set[str] = set()
    mandatory_violations: list[str] = []
    for f, sim in sims:
        cats = sim["categories"]
        eligible |= set(cats["newly_eligible_for_review"])
        excluded_by_rule |= {c for c in cats["excluded_by_supplied_rule"] if sim["sources"].get(c) == "applicant"}
        insufficient |= set(cats["evidence_insufficient"])
        pool_ids |= {c for c, src in sim["sources"].items() if src == "pool"}
        clash = set(cats["newly_eligible_for_review"]) & set(cats["still_fail_mandatory_requirement"])
        mandatory_violations += [f"{f['id']}: {c} both eligible and failing a mandatory requirement" for c in sorted(clash)]
    protected_rules = {r["id"] for r in result["rules"] if r["status"] == "protected"}
    for f in result["findings"]:
        if f.get("rule_id") in protected_rules and f.get("proposed_change") and f["check"] != "literal_term_missing_variants":
            mandatory_violations.append(f"{f['id']}: proposes relaxing protected rule {f['rule_id']}")
    by_candidate = {c["candidate_id"]: c for c in result["candidates"]}
    for cid in sorted(eligible):
        a = by_candidate.get(cid)
        if a and any(rv["status"] == "protected_missing" for rv in a["requirements"]):
            mandatory_violations.append(f"{cid}: eligible despite an unmet protected requirement")
    # Policy violations: blocked pool records in a simulation, or a policy-rejected equivalency used for eligibility.
    policy_violations = [f"{c}: blocked pool record appears in a simulation" for c in sorted(pool_ids & blocked_pool_ids)]
    rejected = rejected_equivalencies
    for cid in sorted(eligible):
        a = by_candidate.get(cid)
        for rv in (a or {}).get("requirements", []):
            for p in rv["paths"]:
                if p.startswith("equivalency:") and p.split(":", 1)[1] in rejected:
                    policy_violations.append(f"{cid}: eligibility relies on policy-rejected {p}")
    unknown = {c for f in result["findings"] if f["check"] == "unexplained_exclusions" for c in f["affected_candidates"]}
    alt = {f["candidate_id"] for f in result["findings"]
           if f["check"] == "candidate_review_opportunity" and f.get("risk_category") == "equivalent_experience"}
    relevant_surfaced = sorted(c for c in eligible if labels.get(c) == "meets_requirements")
    relevant_missed = sorted(c for c in excluded_by_rule if labels.get(c) == "meets_requirements" and c not in eligible)
    irrelevant = sorted(c for c in eligible if labels.get(c) == "does_not_meet")
    return {
        "relevant_surfaced": relevant_surfaced,
        "relevant_missed": relevant_missed,
        "irrelevant_surfaced": irrelevant,
        "mandatory_violations": mandatory_violations,
        "policy_violations": policy_violations,
        "needs_human_verification": sorted(insufficient | unknown | (alt & eligible)),
        "unknown_cause": sorted(unknown),
        "simulated_findings": len(sims),
        "rule_level_only": sorted(f["id"] for f in result["findings"]
                                  if f.get("simulation") and not f["simulation"].get("evaluable") and f.get("rule_id")),
    }


def aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    def n(key: str) -> int:
        return sum(len(c["risk"][key]) for c in cases if c.get("risk"))

    exp = [e for c in cases for e in c.get("simulation_expectations", [])]
    rs, rm = n("relevant_surfaced"), n("relevant_missed")
    return {
        "label": SYNTHETIC_LABEL,
        "relevant_surfaced": rs,
        "relevant_missed": rm,
        "irrelevant_surfaced": n("irrelevant_surfaced"),
        "mandatory_violations": n("mandatory_violations"),
        "policy_violations": n("policy_violations"),
        "needs_human_verification": n("needs_human_verification"),
        "unknown_cause": n("unknown_cause"),
        "expectations": len(exp),
        "expectations_met": sum(1 for e in exp if e["met"]),
        "relevant_recall": round(rs / (rs + rm), 3) if (rs + rm) else 1.0,
    }


def failures(m: dict[str, Any], th: dict[str, Any]) -> list[str]:
    out = []
    if m["expectations_met"] < m["expectations"]:
        out.append(f"screening risks: {m['expectations'] - m['expectations_met']} simulation expectation(s) not met")
    if m["irrelevant_surfaced"] > th["max_risk_irrelevant_surfaced"]:
        out.append(f"screening risks: {m['irrelevant_surfaced']} irrelevant candidate(s) made newly eligible")
    if m["mandatory_violations"] > th["max_risk_mandatory_violations"]:
        out.append(f"screening risks: {m['mandatory_violations']} mandatory-requirement violation(s)")
    if m["policy_violations"] > th["max_risk_policy_violations"]:
        out.append(f"screening risks: {m['policy_violations']} blocked-record or policy violation(s)")
    if m["relevant_recall"] < th["min_risk_recall"]:
        out.append(f"screening risks: relevant recall {m['relevant_recall']} < {th['min_risk_recall']}")
    return out


def compare(mb: dict[str, Any], mc: dict[str, Any]) -> list[str]:
    reg = []
    for key in ("irrelevant_surfaced", "mandatory_violations", "policy_violations"):
        if mc[key] > mb[key]:
            reg.append(f"screening risks: {key.replace('_', ' ')} increased {mb[key]} -> {mc[key]}")
    if mc["expectations_met"] < mb["expectations_met"]:
        reg.append(f"screening risks: expectations met dropped {mb['expectations_met']} -> {mc['expectations_met']}")
    if mc["relevant_recall"] < mb["relevant_recall"]:
        reg.append(f"screening risks: relevant recall dropped {mb['relevant_recall']} -> {mc['relevant_recall']}")
    return reg


def render(m: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    L = ["", "## Screening risks (forward simulation)", "", f"> **{m['label']}**", "", "| Metric | Value |", "|---|---|"]
    for k, v in m.items():
        if k != "label":
            L.append(f"| {k.replace('_', ' ')} | {v} |")
    L.append("")
    for c in cases:
        if not c.get("simulation_expectations") and not c.get("risk"):
            continue
        L.append(f"### {c['case_id']}")
        L.append("")
        r = c.get("risk") or {}
        for key in ("relevant_surfaced", "relevant_missed", "irrelevant_surfaced", "mandatory_violations",
                    "policy_violations", "needs_human_verification", "unknown_cause"):
            L.append(f"- {key.replace('_', ' ')}: {', '.join(r.get(key, [])) or '—'}")
        for e in c.get("simulation_expectations", []):
            L.append(f"- {'✅' if e['met'] else '❌'} {e['scenario']}" + (f" — {'; '.join(e['problems'])}" if e["problems"] else ""))
        L.append("")
    return "\n".join(L)
