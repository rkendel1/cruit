"""Evaluation harness: regression-test knowledge and engine changes against labeled cases.

Measures both missed opportunities AND false positives, plus hard guardrails:
  * expected findings found (finding recall)
  * forbidden findings absent (e.g. surfacing someone who lacks a legal license)
  * candidate surfacing precision / recall against expert labels
  * review burden (how many candidates a recruiter is asked to look at)

compare_suites() runs two knowledge versions over the same cases and reports
exactly which findings and candidates changed, with a pass/fail regression gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..contracts import load
from ..engine import RequisitionBundle, diagnose
from ..knowledge.pack import KnowledgePack

DEFAULT_THRESHOLDS = {
    "min_expected_finding_recall": 1.0,
    "min_candidate_precision": 0.8,
    "min_candidate_recall": 0.6,
    "max_forbidden_violations": 0,
    "max_guardrail_violations": 0,
    # compare gate
    "max_precision_drop": 0.0,
    "max_false_positive_increase": 0,
}

RUN_AT = "1970-01-01T00:00:00+00:00"  # fixed so eval output is reproducible


def _matches(f: dict[str, Any], m: dict[str, Any]) -> bool:
    if f["check"] != m["check"]:
        return False
    for key, attr in (("rule", "rule_id"), ("requirement", "requirement_id"), ("candidate", "candidate_id")):
        if key not in m or f.get(attr) == m[key]:
            continue
        if key == "candidate" and f["check"] == "unexplained_exclusions" and m[key] in f.get("affected_candidates", []):
            continue
        return False
    if "evidence_level" in m and m["evidence_level"] != f["evidence_level"]:
        return False
    return True


@dataclass
class CaseResult:
    case_id: str
    description: str
    result: dict[str, Any]
    expected: list[dict[str, Any]]
    forbidden: list[dict[str, Any]]
    candidates: dict[str, Any]
    guardrail_violations: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "description": self.description,
            "expected": self.expected,
            "forbidden": self.forbidden,
            "candidates": self.candidates,
            "guardrail_violations": self.guardrail_violations,
            "knowledge": self.result["knowledge"]["fingerprint"],
            "findings": [{"id": f["id"], "check": f["check"], "level": f["evidence_level"], "title": f["title"],
                          "confidence": f["confidence"], "affected": f["affected_candidates"]} for f in self.result["findings"]],
        }


def run_case(case_path: Path, pack: KnowledgePack) -> CaseResult:
    case = load("eval_case", case_path)
    base = case_path.parent
    bundle = RequisitionBundle(
        path=None,
        requisition=load("requisition", base / case["requisition"]),
        policy=load("policy", base / case["policy"]),
        candidates=load("candidates", base / case["candidates"]) if case.get("candidates") else None,
    )
    result = diagnose(bundle, pack, run_at=RUN_AT).as_dict()
    findings = result["findings"]

    expected = []
    for m in case.get("expected_findings", []):
        hit = next((f["id"] for f in findings if _matches(f, m)), None)
        expected.append({**m, "found": hit is not None, "finding_id": hit})
    forbidden = []
    for m in case.get("forbidden_findings", []):
        hits = [f["id"] for f in findings if _matches(f, m)]
        forbidden.append({**m, "violated": bool(hits), "finding_ids": hits})

    labels = case["expert_labels"]
    flagged = {c["candidate_id"] for c in result["candidates"] if c["surfaced"]}
    for f in findings:
        if f["check"] == "unexplained_exclusions":
            flagged |= set(f["affected_candidates"])
    excluded = {c["candidate_id"] for c in result["candidates"] if c["ats_status"] in ("rejected", "deprioritized")}
    tp = sorted(c for c in flagged if labels.get(c) == "meets_requirements")
    fp = sorted(c for c in flagged if labels.get(c) == "does_not_meet")
    unsure = sorted(c for c in flagged if labels.get(c) in (None, "insufficient_evidence"))
    fn = sorted(c for c in excluded if labels.get(c) == "meets_requirements" and c not in flagged)
    cand = {
        "excluded": len(excluded),
        "flagged": sorted(flagged),
        "true_positives": tp,
        "false_positives": fp,
        "flagged_unlabeled_or_insufficient": unsure,
        "missed_qualified": fn,
        "precision": round(len(tp) / (len(tp) + len(fp)), 3) if (tp or fp) else None,
        "recall": round(len(tp) / (len(tp) + len(fn)), 3) if (tp or fn) else None,
    }

    guard = []
    for c in result["candidates"]:
        if c["surfaced"] and any(rv["status"] == "protected_missing" for rv in c["requirements"]):
            guard.append(f"{c['candidate_id']} surfaced despite an unmet protected requirement")
    protected_rules = {r["id"] for r in result["rules"] if r["status"] == "protected"}
    for f in findings:
        if f.get("rule_id") in protected_rules and f["check"] != "literal_term_missing_variants":
            guard.append(f"{f['id']} proposes relaxing protected rule {f['rule_id']} ({f['check']})")
    for f in findings:
        if f["category"] == "candidate_review_opportunity" and "Qualification has not been established" not in " ".join(f["limitations"]):
            guard.append(f"{f['id']} does not state that qualification is unestablished")
    return CaseResult(case["id"], case["description"], result, expected, forbidden, cand, guard)


def run_suite(cases_dir: str | Path, pack: KnowledgePack, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    paths = sorted(Path(cases_dir).glob("*.yaml"))
    cases = [run_case(p, pack) for p in paths]
    exp_total = sum(len(c.expected) for c in cases)
    exp_found = sum(1 for c in cases for e in c.expected if e["found"])
    forb = sum(1 for c in cases for f in c.forbidden if f["violated"])
    guard = sum(len(c.guardrail_violations) for c in cases)
    tp = sum(len(c.candidates["true_positives"]) for c in cases)
    fp = sum(len(c.candidates["false_positives"]) for c in cases)
    fn = sum(len(c.candidates["missed_qualified"]) for c in cases)
    flagged = sum(len(c.candidates["flagged"]) for c in cases)
    metrics = {
        "cases": len(cases),
        "expected_findings": exp_total,
        "expected_found": exp_found,
        "expected_finding_recall": round(exp_found / exp_total, 3) if exp_total else 1.0,
        "forbidden_violations": forb,
        "guardrail_violations": guard,
        "candidates_flagged": flagged,
        "true_positives": tp,
        "false_positives": fp,
        "missed_qualified": fn,
        "candidate_precision": round(tp / (tp + fp), 3) if (tp + fp) else 1.0,
        "candidate_recall": round(tp / (tp + fn), 3) if (tp + fn) else 1.0,
    }
    failures = []
    if metrics["expected_finding_recall"] < th["min_expected_finding_recall"]:
        failures.append(f"expected-finding recall {metrics['expected_finding_recall']} < {th['min_expected_finding_recall']}")
    if metrics["candidate_precision"] < th["min_candidate_precision"]:
        failures.append(f"candidate precision {metrics['candidate_precision']} < {th['min_candidate_precision']}")
    if metrics["candidate_recall"] < th["min_candidate_recall"]:
        failures.append(f"candidate recall {metrics['candidate_recall']} < {th['min_candidate_recall']}")
    if forb > th["max_forbidden_violations"]:
        failures.append(f"{forb} forbidden finding(s) produced")
    if guard > th["max_guardrail_violations"]:
        failures.append(f"{guard} guardrail violation(s)")
    return {
        "knowledge": pack.fingerprint,
        "thresholds": th,
        "metrics": metrics,
        "passed": not failures,
        "failures": failures,
        "cases": [c.as_dict() for c in cases],
    }


def compare_suites(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    th = candidate["thresholds"]
    case_diffs = []
    for cb, cc in zip(baseline["cases"], candidate["cases"]):
        fb = {f["id"]: f for f in cb["findings"]}
        fc = {f["id"]: f for f in cc["findings"]}
        changed = []
        for fid in sorted(set(fb) & set(fc)):
            a, b = fb[fid], fc[fid]
            deltas = {k: [a[k], b[k]] for k in ("level", "confidence", "affected") if a[k] != b[k]}
            if deltas:
                changed.append({"id": fid, "title": b["title"], "changes": deltas})
        newly = sorted(set(cc["candidates"]["flagged"]) - set(cb["candidates"]["flagged"]))
        dropped = sorted(set(cb["candidates"]["flagged"]) - set(cc["candidates"]["flagged"]))
        lost_expected = [e for e, f in zip(cb["expected"], cc["expected"]) if e["found"] and not f["found"]]
        gained_expected = [f for e, f in zip(cb["expected"], cc["expected"]) if not e["found"] and f["found"]]
        case_diffs.append({
            "case_id": cc["case_id"],
            "added_findings": [{"id": i, "check": fc[i]["check"], "title": fc[i]["title"]} for i in sorted(set(fc) - set(fb))],
            "removed_findings": [{"id": i, "check": fb[i]["check"], "title": fb[i]["title"]} for i in sorted(set(fb) - set(fc))],
            "changed_findings": changed,
            "newly_flagged_candidates": newly,
            "no_longer_flagged_candidates": dropped,
            "expected_findings_lost": lost_expected,
            "expected_findings_gained": gained_expected,
        })
    mb, mc = baseline["metrics"], candidate["metrics"]
    deltas = {k: round(mc[k] - mb[k], 3) for k in mb if isinstance(mb[k], (int, float))}
    regressions = []
    if mb["candidate_precision"] - mc["candidate_precision"] > th["max_precision_drop"]:
        regressions.append(f"candidate precision dropped {mb['candidate_precision']} -> {mc['candidate_precision']}")
    if mc["false_positives"] - mb["false_positives"] > th["max_false_positive_increase"]:
        regressions.append(f"false positives increased {mb['false_positives']} -> {mc['false_positives']}")
    if mc["forbidden_violations"] > th["max_forbidden_violations"]:
        regressions.append(f"{mc['forbidden_violations']} forbidden finding(s)")
    if mc["guardrail_violations"] > th["max_guardrail_violations"]:
        regressions.append(f"{mc['guardrail_violations']} guardrail violation(s)")
    for d in case_diffs:
        for e in d["expected_findings_lost"]:
            regressions.append(f"{d['case_id']}: previously found expected finding lost ({e['check']} {e.get('rule') or e.get('candidate') or e.get('requirement') or ''})")
    return {
        "baseline": baseline["knowledge"],
        "candidate": candidate["knowledge"],
        "metrics": {"baseline": mb, "candidate": mc, "delta": deltas},
        "cases": case_diffs,
        "regressions": regressions,
        "passed": not regressions and candidate["passed"],
        "candidate_suite_failures": candidate["failures"],
    }


def render_suite_markdown(s: dict[str, Any]) -> str:
    m = s["metrics"]
    L = [f"# Evaluation — knowledge `{s['knowledge']}`", "", f"**Result: {'PASS' if s['passed'] else 'FAIL'}**", ""]
    for f in s["failures"]:
        L.append(f"- ❌ {f}")
    L += ["", "| Metric | Value |", "|---|---|"]
    for k, v in m.items():
        L.append(f"| {k.replace('_', ' ')} | {v} |")
    L.append("")
    for c in s["cases"]:
        cm = c["candidates"]
        L.append(f"## {c['case_id']}")
        L.append("")
        L.append(c["description"].strip())
        L.append("")
        L.append(f"- Candidates flagged for review: {', '.join(cm['flagged']) or '—'}")
        L.append(f"- True positives: {', '.join(cm['true_positives']) or '—'}; false positives: {', '.join(cm['false_positives']) or '—'}; "
                 f"missed qualified: {', '.join(cm['missed_qualified']) or '—'}")
        L.append(f"- Precision {cm['precision']} · recall {cm['recall']}")
        miss = [e for e in c["expected"] if not e["found"]]
        viol = [f for f in c["forbidden"] if f["violated"]]
        L.append(f"- Expected findings: {sum(e['found'] for e in c['expected'])}/{len(c['expected'])} found"
                 + (" — missing: " + "; ".join(f"{e['check']} {e.get('rule') or e.get('candidate') or e.get('requirement') or ''}" for e in miss) if miss else ""))
        L.append(f"- Forbidden findings produced: {len(viol)}" + (" — " + "; ".join(f"{v['check']} {v.get('candidate') or v.get('rule') or ''}" for v in viol) if viol else ""))
        if c["guardrail_violations"]:
            L += [f"- ❌ {g}" for g in c["guardrail_violations"]]
        L.append("")
    return "\n".join(L)


def render_compare_markdown(c: dict[str, Any]) -> str:
    L = [f"# Knowledge comparison — `{c['baseline']}` → `{c['candidate']}`", "",
         f"**Regression gate: {'PASS' if c['passed'] else 'FAIL'}**", ""]
    for r in c["regressions"]:
        L.append(f"- ❌ {r}")
    for r in c["candidate_suite_failures"]:
        L.append(f"- ❌ candidate suite: {r}")
    L += ["", "| Metric | Baseline | Candidate | Δ |", "|---|---|---|---|"]
    for k, v in c["metrics"]["baseline"].items():
        L.append(f"| {k.replace('_', ' ')} | {v} | {c['metrics']['candidate'][k]} | {c['metrics']['delta'].get(k, '')} |")
    L.append("")
    for d in c["cases"]:
        L.append(f"## {d['case_id']}")
        L.append("")
        if not any(d[k] for k in d if k != "case_id"):
            L.append("_No change._")
        for f in d["added_findings"]:
            L.append(f"- ➕ `{f['id']}` {f['title']}")
        for f in d["removed_findings"]:
            L.append(f"- ➖ `{f['id']}` {f['title']}")
        for f in d["changed_findings"]:
            L.append(f"- ✎ `{f['id']}` {f['title']}: {f['changes']}")
        if d["newly_flagged_candidates"]:
            L.append(f"- Newly flagged for review: {', '.join(d['newly_flagged_candidates'])}")
        if d["no_longer_flagged_candidates"]:
            L.append(f"- No longer flagged: {', '.join(d['no_longer_flagged_candidates'])}")
        for e in d["expected_findings_gained"]:
            L.append(f"- ✅ expected finding now found: {e['check']} {e.get('rule') or e.get('candidate') or e.get('requirement') or ''}")
        for e in d["expected_findings_lost"]:
            L.append(f"- ❌ expected finding lost: {e['check']} {e.get('rule') or e.get('candidate') or e.get('requirement') or ''}")
        L.append("")
    return "\n".join(L)
