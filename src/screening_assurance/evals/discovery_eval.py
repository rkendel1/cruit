"""Evaluation of candidate rediscovery on labeled SYNTHETIC fixtures.

Measures retrieval and review quality, not volume:
  relevant surfaced / relevant missed / irrelevant surfaced, over-claimed certainty,
  mandatory-requirement violations, blocked-record violations, and how many results
  need human verification. Results are synthetic and never represent real-world accuracy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts import load
from ..engine import RequisitionBundle, diagnose, discover
from ..engine.discovery import ACTIONABLE
from ..knowledge.pack import KnowledgePack

SYNTHETIC_LABEL = "SYNTHETIC FIXTURE RESULTS — not a measure of real-world accuracy"
RUN_AT = "1970-01-01T00:00:00+00:00"


def run_discovery_case(case_path: Path, pack: KnowledgePack) -> dict[str, Any]:
    case = load("discovery_case", case_path)
    base = case_path.parent
    bundle = RequisitionBundle(
        path=None,
        requisition=load("requisition", base / case["requisition"]),
        policy=load("policy", base / case["policy"]),
        candidates=load("candidates", base / case["candidates"]) if case.get("candidates") else None,
    )
    pool = load("candidate_pool", base / case["pool"])
    diag = diagnose(bundle, pack, run_at=RUN_AT)
    result = discover(bundle, pack, diag, pool=pool, as_of=case["as_of"])
    groups = {e.candidate_id: e.group for e in result.entries}
    entries = {e.candidate_id: e for e in result.entries}
    labels = case["labels"]

    def actionable(cid: str) -> bool:
        return groups.get(cid) in ACTIONABLE

    scored = [c for c in labels if groups.get(c) != "active_workflow"]
    relevant_surfaced = sorted(c for c in scored if labels[c] == "relevant" and actionable(c))
    relevant_missed = sorted(c for c in scored if labels[c] == "relevant" and not actionable(c))
    irrelevant_surfaced = sorted(c for c in scored if labels[c] == "not_relevant" and actionable(c))
    overclaimed = sorted(c for c in scored if labels[c] == "insufficient" and groups.get(c) in ("direct", "transferable"))
    blocked_violations = sorted(c for c in scored if labels[c] == "must_not_surface" and actionable(c))
    mandatory_violations = sorted(
        e.candidate_id for e in result.entries if e.group in ("direct", "transferable")
        and any(m["issue"] in ("not_satisfied", "cannot_verify") for m in e.mandatory_issues)
    )
    needs_verification = sorted(e.candidate_id for e in result.entries if e.group in ("transferable", "insufficient"))
    expected = case.get("expected_groups", {})
    group_mismatches = sorted(f"{c}: expected {g}, got {groups.get(c)}" for c, g in expected.items() if groups.get(c) != g)
    unlabeled = sorted(c for c in groups if c not in labels and groups[c] in ACTIONABLE)
    return {
        "case_id": case["id"],
        "description": case["description"],
        "knowledge": pack.fingerprint,
        "groups": groups,
        "fixture_types": case.get("fixture_types", {}),
        "relevant_surfaced": relevant_surfaced,
        "relevant_missed": relevant_missed,
        "irrelevant_surfaced": irrelevant_surfaced,
        "overclaimed_certainty": overclaimed,
        "mandatory_violations": mandatory_violations,
        "blocked_violations": blocked_violations,
        "needs_human_verification": needs_verification,
        "group_mismatches": group_mismatches,
        "unlabeled_surfaced": unlabeled,
        "reasons": {cid: (e.reason or (e.why[-1] if e.why else "")) for cid, e in entries.items()},
    }


def run_discovery_suite(cases_dir: str | Path, pack: KnowledgePack) -> dict[str, Any] | None:
    paths = sorted(Path(cases_dir).glob("*.yaml"))
    if not paths:
        return None
    cases = [run_discovery_case(p, pack) for p in paths]

    def n(key: str) -> int:
        return sum(len(c[key]) for c in cases)

    rs, rm = n("relevant_surfaced"), n("relevant_missed")
    metrics = {
        "cases": len(cases),
        "relevant_surfaced": rs,
        "relevant_missed": rm,
        "irrelevant_surfaced": n("irrelevant_surfaced"),
        "overclaimed_certainty": n("overclaimed_certainty"),
        "mandatory_violations": n("mandatory_violations"),
        "blocked_violations": n("blocked_violations"),
        "needs_human_verification": n("needs_human_verification"),
        "group_mismatches": n("group_mismatches"),
        "relevant_recall": round(rs / (rs + rm), 3) if (rs + rm) else 1.0,
        "recruiter_dispositions": "not measured in fixtures",
        "recruiter_minutes": "not measured in fixtures",
    }
    return {"label": SYNTHETIC_LABEL, "metrics": metrics, "cases": cases}


def discovery_failures(d: dict[str, Any] | None, th: dict[str, Any]) -> list[str]:
    if not d:
        return []
    m = d["metrics"]
    out = []
    if m["mandatory_violations"] > th["max_mandatory_violations"]:
        out.append(f"discovery: {m['mandatory_violations']} mandatory-requirement violation(s)")
    if m["blocked_violations"] > th["max_blocked_violations"]:
        out.append(f"discovery: {m['blocked_violations']} blocked record(s) surfaced for action")
    if m["irrelevant_surfaced"] > th["max_irrelevant_surfaced"]:
        out.append(f"discovery: {m['irrelevant_surfaced']} irrelevant candidate(s) surfaced")
    if m["overclaimed_certainty"] > th["max_overclaimed_certainty"]:
        out.append(f"discovery: {m['overclaimed_certainty']} insufficient-evidence candidate(s) shown with more certainty")
    if m["relevant_recall"] < th["min_discovery_recall"]:
        out.append(f"discovery: relevant recall {m['relevant_recall']} < {th['min_discovery_recall']}")
    return out


def compare_discovery(b: dict[str, Any] | None, c: dict[str, Any] | None, th: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    if not b or not c:
        return [], []
    diffs, regressions = [], []
    for cb, cc in zip(b["cases"], c["cases"]):
        changed = {cid: [cb["groups"].get(cid), g] for cid, g in cc["groups"].items() if cb["groups"].get(cid) != g}
        diffs.append({
            "case_id": cc["case_id"],
            "group_changes": changed,
            "newly_relevant_surfaced": sorted(set(cc["relevant_surfaced"]) - set(cb["relevant_surfaced"])),
            "newly_irrelevant_surfaced": sorted(set(cc["irrelevant_surfaced"]) - set(cb["irrelevant_surfaced"])),
        })
    mb, mc = b["metrics"], c["metrics"]
    if mc["irrelevant_surfaced"] > mb["irrelevant_surfaced"]:
        regressions.append(f"discovery: irrelevant surfaced increased {mb['irrelevant_surfaced']} -> {mc['irrelevant_surfaced']}")
    for key in ("mandatory_violations", "blocked_violations", "overclaimed_certainty"):
        if mc[key] > mb[key]:
            regressions.append(f"discovery: {key.replace('_', ' ')} increased {mb[key]} -> {mc[key]}")
    if mc["relevant_recall"] < mb["relevant_recall"]:
        regressions.append(f"discovery: relevant recall dropped {mb['relevant_recall']} -> {mc['relevant_recall']}")
    return diffs, regressions


def render_discovery_suite_markdown(d: dict[str, Any] | None) -> str:
    if not d:
        return ""
    L = ["", "## Candidate rediscovery", "", f"> **{d['label']}**", "", "| Metric | Value |", "|---|---|"]
    for k, v in d["metrics"].items():
        L.append(f"| {k.replace('_', ' ')} | {v} |")
    L.append("")
    for c in d["cases"]:
        L.append(f"### {c['case_id']}")
        L.append("")
        L.append(c["description"].strip())
        L.append("")
        for key in ("relevant_surfaced", "relevant_missed", "irrelevant_surfaced", "overclaimed_certainty",
                    "mandatory_violations", "blocked_violations", "needs_human_verification", "group_mismatches"):
            L.append(f"- {key.replace('_', ' ')}: {', '.join(c[key]) or '—'}")
        if c["fixture_types"]:
            L.append("")
            L.append("| Fixture | Type | Group |")
            L.append("|---|---|---|")
            for cid, t in c["fixture_types"].items():
                L.append(f"| {cid} | {t} | {c['groups'].get(cid)} |")
        L.append("")
    return "\n".join(L)
