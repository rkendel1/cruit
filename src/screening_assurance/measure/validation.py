"""Design-partner validation: measure Screening Assurance against independently reviewed hiring cases.

This extends the measurement module; it does not add a second engine. For each case it
  1. loads authorized, de-identified inputs through the existing contracts,
  2. re-runs the existing deterministic `diagnose` and `discover` (the product view),
  3. reads the baseline (what the existing process did) and independent human reviews,
  4. computes explicitly defined metrics in which unknown, unresolved and unreviewed
     labels stay unknown — never implicit positives or negatives.

Product findings are never their own ground truth. Synthetic datasets are labelled as such
everywhere and are never reported as design-partner evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .. import ENGINE_VERSION
from ..contracts import _EMAIL_RE, _PHONE_RE, ContractError, load, read_yaml, schema_errors
from ..engine import RequisitionBundle, diagnose, discover
from ..engine.discovery import ACTIONABLE
from ..engine.pool import _d, default_as_of, pool_block_reason
from ..knowledge.pack import KnowledgePack

EVALUATION_VERSION = "validation-1"
RUN_AT = "1970-01-01T00:00:00+00:00"  # product runs are deterministic re-runs; the timestamp is not data
SYNTHETIC_LABEL = "SYNTHETIC DATASET — results demonstrate the measurement loop, not real-world effectiveness"
PARTNER_LABEL = ("DESIGN-PARTNER DATASET — results describe these reviewed cases only; they do not establish "
                 "causation or general effectiveness")
MIN_LABELS_FOR_INTERPRETATION = 10

RELEVANCE = ("relevant", "not_relevant", "unassessable")
FINDING_JUDGMENTS = ("confirmed", "unsupported", "irrelevant", "needs_more_evidence", "deferred")
EXCLUDED_OUTCOMES = ("rejected", "deprioritized", "not_reviewed")
SURFACED_OUTCOMES = ("advanced", "in_review")

METRIC_DEFINITIONS: list[dict[str, str]] = [
    # ---------------------------------------------------------------- discovery
    {"id": "D1", "group": "discovery", "name": "Relevant candidates surfaced for human review",
     "numerator": "Candidates whose resolved label is relevant and whose product group is direct, transferable or insufficient",
     "denominator": "Candidates whose resolved label is relevant and who are eligible for the product (not blocked, not already in active ATS review)",
     "eligibility": "All candidates in the case inputs with a resolved relevance label",
     "unknown_handling": "Unreviewed, unresolved and unassessable candidates are excluded from both numerator and denominator and reported in D4/D6",
     "minimum_evidence": "At least one independent review, or an adjudication where reviewers disagree"},
    {"id": "D2", "group": "discovery", "name": "Relevant candidates still missed by the product",
     "numerator": "Eligible candidates resolved relevant whose product group is not_surfaced",
     "denominator": "Same as D1",
     "eligibility": "As D1", "unknown_handling": "As D1", "minimum_evidence": "As D1"},
    {"id": "D3", "group": "discovery", "name": "Irrelevant candidates surfaced for additional review",
     "numerator": "Candidates resolved not_relevant whose product group is direct, transferable or insufficient",
     "denominator": "Surfaced candidates with a resolved label of relevant or not_relevant",
     "eligibility": "Product-surfaced candidates", "unknown_handling": "Surfaced candidates without a resolved label are reported in D4, not here",
     "minimum_evidence": "As D1"},
    {"id": "D4", "group": "discovery", "name": "Surfaced candidates whose relevance is not established",
     "numerator": "Surfaced candidates whose label is unassessable, unresolved or unreviewed", "denominator": "All surfaced candidates",
     "eligibility": "Product-surfaced candidates", "unknown_handling": "This metric is the unknown bucket; never counted as success or failure",
     "minimum_evidence": "None"},
    {"id": "D5", "group": "discovery", "name": "Results that still require human verification",
     "numerator": "Candidates in the transferable or insufficient groups", "denominator": "All surfaced candidates",
     "eligibility": "Product-surfaced candidates", "unknown_handling": "Not label-dependent", "minimum_evidence": "None"},
    # ---------------------------------------------------------------- baseline
    {"id": "B1", "group": "baseline", "name": "Relevant candidates the existing process missed",
     "numerator": "Candidates resolved relevant whose baseline outcome is rejected, deprioritized or not_reviewed with basis observed",
     "denominator": "Candidates resolved relevant with an observed baseline outcome",
     "eligibility": "Cases whose baseline source is not 'not_available'",
     "unknown_handling": "Inferred baseline outcomes are reported separately (B1-inferred); unknown baselines and pool records that never applied are excluded and counted",
     "minimum_evidence": "Baseline outcome observed in supplied ATS or recruiter records"},
    {"id": "B2", "group": "baseline", "name": "Of those, surfaced by Screening Assurance",
     "numerator": "B1 candidates whose product group is direct, transferable or insufficient", "denominator": "B1 numerator",
     "eligibility": "As B1", "unknown_handling": "As B1", "minimum_evidence": "As B1"},
    {"id": "B3", "group": "baseline", "name": "Of those, still missed by Screening Assurance",
     "numerator": "B1 candidates not surfaced by the product", "denominator": "B1 numerator",
     "eligibility": "As B1", "unknown_handling": "As B1", "minimum_evidence": "As B1"},
    # ---------------------------------------------------------------- screening risks
    {"id": "F1", "group": "screening_risks", "name": "Findings independently confirmed",
     "numerator": "Product screening-risk findings whose resolved review is confirmed",
     "denominator": "All product screening-risk findings in reviewed cases (including unreviewed ones)",
     "eligibility": "Findings with a screening-risk category", "unknown_handling": "Unreviewed and unresolved findings stay in the denominator and are reported in F4/F5; they are never counted as confirmed",
     "minimum_evidence": "At least one independent review, or an adjudication where reviewers disagree"},
    {"id": "F2", "group": "screening_risks", "name": "Findings rejected as unsupported or irrelevant",
     "numerator": "Resolved review is unsupported or irrelevant", "denominator": "As F1", "eligibility": "As F1",
     "unknown_handling": "As F1", "minimum_evidence": "As F1"},
    {"id": "F3", "group": "screening_risks", "name": "Findings deferred or needing more evidence",
     "numerator": "Resolved review is deferred or needs_more_evidence", "denominator": "As F1", "eligibility": "As F1",
     "unknown_handling": "As F1", "minimum_evidence": "As F1"},
    {"id": "F4", "group": "screening_risks", "name": "Findings with unresolved reviewer disagreement", "numerator": "Reviews disagree and no adjudication",
     "denominator": "As F1", "eligibility": "As F1", "unknown_handling": "Reported as unknown", "minimum_evidence": "Two or more reviews"},
    {"id": "F5", "group": "screening_risks", "name": "Findings not reviewed", "numerator": "No review supplied", "denominator": "As F1",
     "eligibility": "As F1", "unknown_handling": "Reported as unknown", "minimum_evidence": "None"},
    {"id": "F6", "group": "screening_risks", "name": "Proposed corrections that reveal relevant candidates for review",
     "numerator": "Distinct candidates resolved relevant that a simulated correction makes newly eligible for human review",
     "denominator": "Distinct candidates any simulated correction makes newly eligible",
     "eligibility": "Findings with an evaluable correction simulation", "unknown_handling": "Newly eligible candidates without a resolved label are listed separately",
     "minimum_evidence": "As D1"},
    {"id": "F7", "group": "screening_risks", "name": "Proposed corrections that surface irrelevant candidates",
     "numerator": "Distinct candidates resolved not_relevant that a simulated correction makes newly eligible", "denominator": "As F6",
     "eligibility": "As F6", "unknown_handling": "As F6", "minimum_evidence": "As D1"},
    {"id": "F8", "group": "screening_risks", "name": "Exclusions whose cause cannot be established",
     "numerator": "Candidates in unexplained-exclusion findings, plus findings whose simulation is not evaluable",
     "denominator": "Not a rate", "eligibility": "All cases", "unknown_handling": "This metric is an unknown bucket", "minimum_evidence": "None"},
    {"id": "F9", "group": "screening_risks", "name": "Findings without a verified baseline",
     "numerator": "Screening-risk findings in cases whose baseline is not available, or whose affected candidates have no observed baseline outcome",
     "denominator": "As F1", "eligibility": "As F1", "unknown_handling": "These findings may be valid rule-level risks but cannot be tied to an observed exclusion",
     "minimum_evidence": "None"},
    # ---------------------------------------------------------------- violations (never aggregated away)
    {"id": "V1", "group": "violations", "name": "Mandatory-requirement violations",
     "numerator": "Surfaced or newly eligible candidates whose resolved mandatory disposition is not_met; candidates eligible in a simulation while failing a protected requirement; corrections proposed for protected rules",
     "denominator": "Not a rate: any occurrence is reported individually", "eligibility": "All cases",
     "unknown_handling": "cannot_verify and unresolved mandatory dispositions are listed separately, not counted as violations or as passes", "minimum_evidence": "None"},
    {"id": "V2", "group": "violations", "name": "Blocked-record or policy violations",
     "numerator": "Blocked (unauthorized, expired or stale) pool records that appear in a surfaced group or simulation; surfaced candidates whose evidence relies on an equivalency the employer policy rejects",
     "denominator": "Not a rate: any occurrence is reported individually", "eligibility": "All cases", "unknown_handling": "Not label-dependent", "minimum_evidence": "None"},
    # ---------------------------------------------------------------- workflow value (only where measured)
    {"id": "W1", "group": "workflow", "name": "Recruiter review time, baseline vs. assisted",
     "numerator": "Sum of assisted minutes and of baseline minutes over cases with measured time", "denominator": "Cases with measured: true",
     "eligibility": "Cases whose partner supplied both measurements", "unknown_handling": "Unmeasured cases are counted, never imputed", "minimum_evidence": "Partner timing method stated"},
    {"id": "W2", "group": "workflow", "name": "Additional relevant candidates identified per requisition",
     "numerator": "B2 per case", "denominator": "Cases with an observed baseline", "eligibility": "As B1", "unknown_handling": "As B1", "minimum_evidence": "As B1"},
    {"id": "W3", "group": "workflow", "name": "Review burden from irrelevant candidates and unsupported findings",
     "numerator": "D3 numerator + F7 numerator + F2 numerator", "denominator": "Not a rate", "eligibility": "All cases",
     "unknown_handling": "Unknown-relevance candidates (D4) are reported beside it", "minimum_evidence": "As D1/F1"},
    {"id": "W4", "group": "workflow", "name": "Recruiter decisions changed after inspecting evidence",
     "numerator": "Recorded recruiter decisions with changed_after_evidence: true", "denominator": "Recorded recruiter decisions",
     "eligibility": "Cases with recruiter decisions", "unknown_handling": "Cases without decisions are counted, not imputed", "minimum_evidence": "Recorded decisions"},
    {"id": "W5", "group": "workflow", "name": "Downstream outcomes (observed only)",
     "numerator": "Observed downstream outcomes by type; attributable ones counted separately", "denominator": "Not a rate",
     "eligibility": "Entries with observed: true", "unknown_handling": "Unobserved entries are counted and excluded; no causal claim is made", "minimum_evidence": "Partner records"},
]


@dataclass
class LoadedCase:
    spec: dict[str, Any]
    requisition: dict[str, Any]
    policy: dict[str, Any]
    candidates: dict[str, Any] | None
    pool: dict[str, Any] | None
    decisions: dict[str, Any] | None
    input_hashes: dict[str, str]


@dataclass
class LoadedDataset:
    path: Path
    data: dict[str, Any]
    cases: list[LoadedCase]
    sha256: str


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _strings(obj: Any):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


# ====================================================================== loading and validation
def load_dataset(path: str | Path, *, today: date | None = None) -> LoadedDataset:
    """Validate a dataset and every input it references. Raises ContractError with all problems found."""
    path = Path(path)
    data = read_yaml(path)
    errors = schema_errors("validation_dataset", data)
    if errors:
        raise ContractError(path, errors)
    errors = []
    for text in _strings({k: v for k, v in data.items() if k != "cases"} | {"cases": data["cases"]}):
        if _EMAIL_RE.search(text) or _PHONE_RE.search(text):
            errors.append("dataset text appears to contain an email address or phone number; remove contact details")
            break
    today = today or date.today()
    expires = _d(data["source"]["collected_at"]) + timedelta(days=data["authorization"]["retention_days"])
    if today > expires:
        errors.append(f"dataset authorization expired on {expires.isoformat()} (retention {data['authorization']['retention_days']} days); "
                      f"apply deletion policy '{data['authorization']['deletion']}'")
    ids = [c["case_id"] for c in data["cases"]]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate case_id {dup}")
    base = path.parent
    file_hashes = {path.name: _sha_bytes(path.read_bytes())}
    cases: list[LoadedCase] = []
    for c in data["cases"]:
        try:
            lc = _load_case(base, c, file_hashes)
        except ContractError as exc:
            errors += [f"{c['case_id']}: {e}" for e in exc.errors]
            continue
        errors += _reference_errors(lc)
        cases.append(lc)
    if errors:
        raise ContractError(path, errors)
    return LoadedDataset(path=path, data=data, cases=cases, sha256=_sha_bytes(_canonical(file_hashes).encode()))


def _load_case(base: Path, c: dict[str, Any], file_hashes: dict[str, str]) -> LoadedCase:
    def ld(contract: str, key: str) -> dict[str, Any] | None:
        if not c.get(key):
            return None
        p = (base / c[key]).resolve()
        if not p.exists():
            raise ContractError(c[key], [f"{key} file not found: {c[key]}"])
        doc = load(contract, p)
        hashes[key] = _sha_bytes(p.read_bytes())
        file_hashes[c[key]] = hashes[key]
        return doc

    hashes: dict[str, str] = {}
    req = ld("requisition", "requisition")
    pol = ld("policy", "policy")
    cands = ld("candidates", "candidates")
    pool = ld("candidate_pool", "pool")
    dec = ld("decisions", "decisions")
    problems = []
    if pol["employer_id"] != req["employer_id"]:
        problems.append("policy employer does not match the requisition")
    if cands and cands["requisition_id"] != req["id"]:
        problems.append("candidates file is for a different requisition")
    if pool and "product_validation" not in pool["authorization"]["permitted_uses"] \
            and "rediscovery_review" not in pool["authorization"]["permitted_uses"]:
        problems.append("candidate pool is not authorized for validation or rediscovery use")
    if problems:
        raise ContractError(c["case_id"], problems)
    return LoadedCase(c, req, pol, cands, pool, dec, hashes)


def _reference_errors(lc: LoadedCase) -> list[str]:
    cid = lc.spec["case_id"]
    known = {x["id"] for x in (lc.candidates or {}).get("candidates", [])} | {x["id"] for x in (lc.pool or {}).get("candidates", [])}
    errs = []
    for section, items, key in (("baseline", lc.spec["baseline"]["observations"], "candidate"),
                                ("candidate_assessments", lc.spec["candidate_assessments"], "candidate"),
                                ("downstream", lc.spec.get("downstream", []), "candidate")):
        seen: set[str] = set()
        for it in items:
            ref = it[key]
            if ref not in known:
                errs.append(f"{cid}: {section} refers to {ref}, which is not in the case's candidate inputs")
            if ref in seen and section != "downstream":
                errs.append(f"{cid}: duplicate {section} entry for {ref}")
            seen.add(ref)
    keys = [_canonical(fr["finding"]) for fr in lc.spec["finding_reviews"]]
    for k in sorted({k for k in keys if keys.count(k) > 1}):
        errs.append(f"{cid}: duplicate finding review for {k}")
    for ca in lc.spec["candidate_assessments"]:
        adj = ca.get("adjudication")
        if adj and adj["judgment"] not in RELEVANCE:
            errs.append(f"{cid}: adjudication for {ca['candidate']} must be one of {RELEVANCE}")
        reviewers = [r["reviewer"] for r in ca["reviews"]]
        if len(set(reviewers)) != len(reviewers):
            errs.append(f"{cid}: {ca['candidate']} has two reviews from the same reviewer")
    for fr in lc.spec["finding_reviews"]:
        adj = fr.get("adjudication")
        if adj and adj["judgment"] not in FINDING_JUDGMENTS:
            errs.append(f"{cid}: finding adjudication must be one of {FINDING_JUDGMENTS}")
        reviewers = [r["reviewer"] for r in fr["reviews"]]
        if len(set(reviewers)) != len(reviewers):
            errs.append(f"{cid}: finding {fr['finding']['check']} has two reviews from the same reviewer")
    if lc.spec["baseline"]["source"] == "not_available" and lc.spec["baseline"]["observations"]:
        errs.append(f"{cid}: baseline source is not_available but observations were supplied")
    return errs


# ====================================================================== label resolution
def resolve(reviews: list[dict[str, Any]], adjudication: dict[str, Any] | None, field: str = "judgment") -> dict[str, Any]:
    """Resolve independent reviews. Disagreement without adjudication stays unresolved (unknown)."""
    vals = [r[field] for r in reviews]
    disagreement = len(set(vals)) > 1
    if adjudication and (field == "judgment" or adjudication.get(field)):
        return {"status": "adjudicated", "value": adjudication[field], "disagreement": disagreement,
                "adjudicator": adjudication["adjudicator"]}
    if not vals:
        return {"status": "unreviewed", "value": None, "disagreement": False}
    if disagreement:
        return {"status": "unresolved", "value": None, "disagreement": True, "values": sorted(set(vals))}
    return {"status": "agreed" if len(vals) > 1 else "single_review", "value": vals[0], "disagreement": False}


def label_class(res: dict[str, Any]) -> str:
    if res["status"] == "unreviewed":
        return "unreviewed"
    if res["status"] == "unresolved":
        return "unresolved"
    return res["value"]  # relevant | not_relevant | unassessable


def _match(f: dict[str, Any], m: dict[str, Any]) -> bool:
    if f["check"] != m["check"]:
        return False
    for key, attr in (("rule", "rule_id"), ("requirement", "requirement_id"), ("candidate", "candidate_id")):
        if key in m and f.get(attr) != m[key]:
            return False
    return True


# ====================================================================== measurement
def measure_dataset(ds: LoadedDataset, pack: KnowledgePack) -> dict[str, Any]:
    collected = ds.data["source"]["collected_at"][:10]
    cases = [_measure_case(lc, pack, collected) for lc in ds.cases]
    metrics = _aggregate(cases)
    kind = ds.data["kind"]
    result = {
        "evaluation_contract": EVALUATION_VERSION,
        "label": SYNTHETIC_LABEL if kind == "synthetic" else PARTNER_LABEL,
        "dataset": {"id": ds.data["dataset_id"], "kind": kind, "contract_version": ds.data["contract_version"],
                    "version": ds.data["source"]["dataset_version"], "provider": ds.data["source"]["provider"],
                    "collected_at": ds.data["source"]["collected_at"], "sha256": ds.sha256},
        "engine_version": ENGINE_VERSION,
        "knowledge": {"fingerprint": pack.fingerprint, "version": pack.version},
        "retention": {"retention_days": ds.data["authorization"]["retention_days"],
                      "delete_after": (_d(ds.data["source"]["collected_at"]) +
                                       timedelta(days=ds.data["authorization"]["retention_days"])).isoformat(),
                      "deletion": ds.data["authorization"]["deletion"]},
        "definitions": METRIC_DEFINITIONS,
        "metrics": metrics,
        "by_scenario": _by_scenario(cases),
        "cases": cases,
        "limitations": _limitations(kind, cases, metrics),
    }
    result["result_id"] = result_id(ds.sha256, pack.fingerprint)
    return result


def result_id(dataset_sha: str, knowledge_fingerprint: str) -> str:
    """Deterministic id of a measurement: same dataset, engine, knowledge and evaluation contract -> same id."""
    key = _canonical([dataset_sha, ENGINE_VERSION, knowledge_fingerprint, EVALUATION_VERSION])
    return "VR-" + hashlib.sha256(key.encode()).hexdigest()[:12]


def _measure_case(lc: LoadedCase, pack: KnowledgePack, collected_at: str) -> dict[str, Any]:
    spec = lc.spec
    bundle = RequisitionBundle(path=None, requisition=lc.requisition, policy=lc.policy, candidates=lc.candidates,
                               decisions=lc.decisions, outcomes=None, pool=lc.pool)
    # Evidence freshness date: explicit, else the pool export date, else the dataset collection date.
    as_of = spec.get("as_of") or (default_as_of(lc.pool, RUN_AT) if lc.pool else collected_at)
    diag = diagnose(bundle, pack, run_at=RUN_AT, as_of=as_of)
    disc = discover(bundle, pack, diag, as_of=as_of)
    groups = {e.candidate_id: e.group for e in disc.entries}
    entries = {e.candidate_id: e for e in disc.entries}
    findings = [f.as_dict() for f in diag.findings]

    # -------- labels (independent review), kept apart from product output
    relevance: dict[str, dict[str, Any]] = {}
    mandatory: dict[str, dict[str, Any]] = {}
    blind: dict[str, bool] = {}
    for ca in spec["candidate_assessments"]:
        relevance[ca["candidate"]] = resolve(ca["reviews"], ca.get("adjudication"), "judgment")
        mandatory[ca["candidate"]] = resolve(ca["reviews"], ca.get("adjudication"), "mandatory")
        blind[ca["candidate"]] = all(not r["saw_product_output"] for r in ca["reviews"]) if ca["reviews"] else False
    population = sorted(groups)
    labels = {c: label_class(relevance[c]) if c in relevance else "unreviewed" for c in population}

    # -------- baseline (what the existing process did)
    base_src = spec["baseline"]["source"]
    baseline = {o["candidate"]: o for o in spec["baseline"]["observations"]}

    # -------- discovery metrics
    eligible = [c for c in population if groups[c] not in ("blocked", "active_workflow")]
    surfaced = [c for c in population if groups[c] in ACTIONABLE]
    rel = [c for c in eligible if labels[c] == "relevant"]
    d = {
        "relevant_surfaced": sorted(c for c in rel if c in surfaced),
        "relevant_missed": sorted(c for c in rel if c not in surfaced),
        "relevant_eligible": sorted(rel),
        "irrelevant_surfaced": sorted(c for c in surfaced if labels[c] == "not_relevant"),
        "surfaced_with_resolved_label": sorted(c for c in surfaced if labels[c] in ("relevant", "not_relevant")),
        "surfaced_relevance_unknown": sorted(c for c in surfaced if labels[c] in ("unassessable", "unresolved", "unreviewed")),
        "requires_verification": sorted(c for c in surfaced if groups[c] in ("transferable", "insufficient")),
        "surfaced": sorted(surfaced),
        "blocked": sorted(c for c in population if groups[c] == "blocked"),
        "already_in_active_review": sorted(c for c in population if groups[c] == "active_workflow"),
        "relevant_blocked": sorted(c for c in population if groups[c] == "blocked" and labels[c] == "relevant"),
    }

    # -------- baseline comparison
    def base_of(c: str) -> dict[str, Any] | None:
        return baseline.get(c) if base_src != "not_available" else None

    rel_all = [c for c in population if labels[c] == "relevant"]
    b_obs_missed = sorted(c for c in rel_all if (base_of(c) or {}).get("basis") == "observed"
                          and base_of(c)["outcome"] in EXCLUDED_OUTCOMES)
    b = {
        "baseline_source": base_src,
        "relevant_with_observed_baseline": sorted(c for c in rel_all if (base_of(c) or {}).get("basis") == "observed"
                                                  and base_of(c)["outcome"] not in ("not_applied", "unknown")),
        "baseline_missed_relevant": b_obs_missed,
        "baseline_missed_relevant_inferred": sorted(c for c in rel_all if (base_of(c) or {}).get("basis") == "inferred"
                                                    and base_of(c)["outcome"] in EXCLUDED_OUTCOMES),
        "baseline_surfaced_relevant": sorted(c for c in rel_all if (base_of(c) or {}).get("basis") == "observed"
                                             and base_of(c)["outcome"] in SURFACED_OUTCOMES),
        "recovered_by_product": sorted(c for c in b_obs_missed if c in surfaced),
        "still_missed_by_product": sorted(c for c in b_obs_missed if c not in surfaced),
        "baseline_not_applicable": sorted(c for c in population if (base_of(c) or {}).get("outcome") == "not_applied"),
        "baseline_unknown": sorted(c for c in population if c not in baseline or base_src == "not_available"
                                   or baseline[c]["outcome"] == "unknown" or baseline[c]["basis"] == "unknown"),
    }

    # -------- screening-risk findings vs independent finding reviews
    risk = [f for f in findings if f.get("risk_category")]
    reviews = spec["finding_reviews"]
    matched_reviews: set[int] = set()
    rows = []
    for f in risk:
        idx = next((i for i, fr in enumerate(reviews) if _match(f, fr["finding"])), None)
        if idx is None:
            res = {"status": "unreviewed", "value": None, "disagreement": False}
        else:
            matched_reviews.add(idx)
            res = resolve(reviews[idx]["reviews"], reviews[idx].get("adjudication"))
        affected = sorted(set(f.get("affected_candidates", [])) | ({f["candidate_id"]} if f.get("candidate_id") else set()))
        verified_baseline = base_src != "not_available" and bool(affected) and all(
            (baseline.get(c) or {}).get("basis") == "observed" for c in affected)
        rows.append({"finding_id": f["id"], "check": f["check"], "rule": f.get("rule_id"), "requirement": f.get("requirement_id"),
                     "candidate": f.get("candidate_id"), "risk_category": f["risk_category"], "review": res,
                     "baseline_verified": verified_baseline})
    unmatched_reviews = [reviews[i]["finding"] for i in range(len(reviews)) if i not in matched_reviews]

    def by_value(*vals: str) -> list[str]:
        return sorted(r["finding_id"] for r in rows if r["review"]["status"] not in ("unreviewed", "unresolved")
                      and r["review"]["value"] in vals)

    newly: dict[str, list[str]] = {}
    for f in risk:
        sim = f.get("simulation") or {}
        for c in (sim.get("categories") or {}).get("newly_eligible_for_review", []):
            newly.setdefault(c, []).append(f["id"])
    fr = {
        "findings": rows,
        "confirmed": by_value("confirmed"),
        "rejected": by_value("unsupported", "irrelevant"),
        "deferred_or_needs_evidence": by_value("deferred", "needs_more_evidence"),
        "unresolved": sorted(r["finding_id"] for r in rows if r["review"]["status"] == "unresolved"),
        "unreviewed": sorted(r["finding_id"] for r in rows if r["review"]["status"] == "unreviewed"),
        "reviews_for_findings_not_produced": unmatched_reviews,
        "newly_eligible": sorted(newly),
        "corrections_reveal_relevant": sorted(c for c in newly if labels.get(c) == "relevant"),
        "corrections_surface_irrelevant": sorted(c for c in newly if labels.get(c) == "not_relevant"),
        "corrections_relevance_unknown": sorted(c for c in newly if labels.get(c) not in ("relevant", "not_relevant")),
        "exclusion_cause_unknown": sorted({c for f in risk if f["check"] == "unexplained_exclusions" for c in f["affected_candidates"]}),
        "simulations_not_evaluable": sorted(f["id"] for f in risk if (f.get("simulation") or {}).get("evaluable") is False),
        "without_verified_baseline": sorted(r["finding_id"] for r in rows if not r["baseline_verified"]),
    }

    # -------- violations (always itemised)
    v_mand: list[str] = []
    for c in sorted(set(surfaced) | set(newly)):
        m = mandatory.get(c)
        if m and m["status"] not in ("unreviewed", "unresolved") and m["value"] == "not_met":
            v_mand.append(f"{c}: surfaced or newly eligible, but reviewers judged a mandatory requirement not met")
    for f in risk:
        sim = f.get("simulation") or {}
        cats = sim.get("categories") or {}
        for c in sorted(set(cats.get("newly_eligible_for_review", [])) & set(cats.get("still_fail_mandatory_requirement", []))):
            v_mand.append(f"{f['id']}: {c} eligible in simulation while failing a protected requirement")
    protected_rules = {r.id for r in diag.rules if r.status == "protected"}
    for f in risk:
        if f.get("rule_id") in protected_rules and f.get("proposed_change") and f["check"] != "literal_term_missing_variants":
            v_mand.append(f"{f['id']}: proposes relaxing protected rule {f['rule_id']}")
    mandatory_unknown = sorted(c for c in set(surfaced) | set(newly)
                               if c in mandatory and (mandatory[c]["status"] == "unresolved" or mandatory[c]["value"] == "cannot_verify"))
    v_policy: list[str] = []
    blocked_ids: set[str] = set()
    if lc.pool:
        as_of_d = _d(as_of)
        blocked_ids = {x["id"] for x in lc.pool["candidates"] if pool_block_reason(x, lc.pool, as_of_d)[0]}
    for c in sorted(blocked_ids & set(surfaced)):
        v_policy.append(f"{c}: blocked pool record surfaced for action")
    for f in risk:
        for c in sorted(blocked_ids & set(((f.get("simulation") or {}).get("sources") or {}))):
            v_policy.append(f"{f['id']}: blocked pool record {c} appears in a simulation")
    rejected_eq = {r["id"] for r in lc.policy.get("rejected_equivalencies", [])}
    for c in surfaced:
        for req in entries[c].requirements:
            for p in req["paths"]:
                if p.startswith("equivalency:") and p.split(":", 1)[1] in rejected_eq:
                    v_policy.append(f"{c}: surfaced through policy-rejected {p}")

    # -------- reviewer agreement
    multi = [ca for ca in spec["candidate_assessments"] if len(ca["reviews"]) >= 2]
    disagreements = [{"candidate": ca["candidate"], "judgments": sorted({r["judgment"] for r in ca["reviews"]}),
                      "adjudicated": bool(ca.get("adjudication"))}
                     for ca in multi if len({r["judgment"] for r in ca["reviews"]}) > 1]
    f_multi = [x for x in reviews if len(x["reviews"]) >= 2]
    f_dis = [{"finding": x["finding"], "judgments": sorted({r["judgment"] for r in x["reviews"]}), "adjudicated": bool(x.get("adjudication"))}
             for x in f_multi if len({r["judgment"] for r in x["reviews"]}) > 1]
    agreement = {
        "candidates_with_multiple_reviews": len(multi),
        "candidate_agreements": len(multi) - len(disagreements),
        "candidate_disagreements": disagreements,
        "findings_with_multiple_reviews": len(f_multi),
        "finding_agreements": len(f_multi) - len(f_dis),
        "finding_disagreements": f_dis,
        "blind_candidate_reviews": sorted(c for c, v in blind.items() if v),
        "reviews_that_saw_product_output": sorted(c for c, v in blind.items() if not v and relevance[c]["status"] != "unreviewed"),
    }

    # -------- workflow value (only what was measured)
    wt = spec.get("workflow_time") or {"measured": False}
    decisions = spec.get("recruiter_decisions", [])
    downstream = spec.get("downstream", [])
    w = {
        "time_measured": bool(wt.get("measured")) and "baseline_minutes" in wt and "assisted_minutes" in wt,
        "baseline_minutes": wt.get("baseline_minutes") if wt.get("measured") else None,
        "assisted_minutes": wt.get("assisted_minutes") if wt.get("measured") else None,
        "time_method": wt.get("method"),
        "additional_relevant": len(b["recovered_by_product"]) if base_src != "not_available" else None,
        "recruiter_decisions": len(decisions),
        "decisions_changed_after_evidence": sum(1 for x in decisions if x["changed_after_evidence"]),
        "downstream_observed": sorted(f"{x['candidate']}:{x['outcome']}" for x in downstream if x["observed"]),
        "downstream_attributable": sorted(f"{x['candidate']}:{x['outcome']}" for x in downstream if x["observed"] and x["attributable"]),
        "downstream_not_observed": sum(1 for x in downstream if not x["observed"]),
    }

    label_counts = {k: sum(1 for c in population if labels[c] == k)
                    for k in ("relevant", "not_relevant", "unassessable", "unresolved", "unreviewed")}
    return {
        "case_id": spec["case_id"],
        "scenario": spec["scenario"],
        "requisition_id": lc.requisition["id"],
        "policy_version": lc.policy["policy_version"],
        "screening_rules": [r["id"] for r in lc.requisition["screening_rules"]],
        "screening_configuration": lc.requisition["inputs_received"]["screening_configuration"],
        "inputs_sha256": lc.input_hashes,
        "decisions_snapshot": "supplied" if lc.decisions else "none",
        "as_of": as_of,
        "product_run": {"engine_version": ENGINE_VERSION, "knowledge": pack.fingerprint, "run_at": RUN_AT,
                        "result_sha256": _product_hash(diag.as_dict()),
                        "discovery_sha256": hashlib.sha256(_canonical(disc.as_dict()).encode()).hexdigest()},
        "population": len(population),
        "label_counts": label_counts,
        "labels": labels,
        "product_groups": groups,
        "baseline_outcomes": {c: {"outcome": o["outcome"], "basis": o["basis"], "excluded_by_rule": o.get("excluded_by_rule")}
                              for c, o in sorted(baseline.items())},
        "discovery": d,
        "baseline": b,
        "screening_risks": fr,
        "violations": {"mandatory": v_mand, "policy": v_policy, "mandatory_unverified": mandatory_unknown},
        "agreement": agreement,
        "workflow": w,
        "unresolved_candidates": sorted(c for c in population if labels[c] in ("unresolved", "unreviewed", "unassessable")),
    }


def _product_hash(diag: dict[str, Any]) -> str:
    """Hash of the product output, independent of where the knowledge pack was loaded from."""
    d = dict(diag)
    d["knowledge"] = {"fingerprint": diag["knowledge"]["fingerprint"]}
    return hashlib.sha256(_canonical(d).encode()).hexdigest()


def _ratio(n: int, d: int) -> dict[str, Any]:
    return {"numerator": n, "denominator": d, "rate": round(n / d, 3) if d else None}


def _aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    def n(section: str, key: str) -> int:
        return sum(len(c[section][key]) for c in cases)

    risk_total = sum(len(c["screening_risks"]["findings"]) for c in cases)
    newly_total = n("screening_risks", "newly_eligible")
    obs_cases = [c for c in cases if c["baseline"]["baseline_source"] != "not_available"]
    timed = [c for c in cases if c["workflow"]["time_measured"]]
    decs = sum(c["workflow"]["recruiter_decisions"] for c in cases)
    return {
        "coverage": {
            "cases": len(cases),
            "candidates": sum(c["population"] for c in cases),
            "labels": {k: sum(c["label_counts"][k] for c in cases)
                       for k in ("relevant", "not_relevant", "unassessable", "unresolved", "unreviewed")},
            "cases_without_baseline": sorted(c["case_id"] for c in cases if c["baseline"]["baseline_source"] == "not_available"),
            "screening_risk_findings": risk_total,
            "findings_unreviewed": n("screening_risks", "unreviewed"),
        },
        "discovery": {
            "D1_relevant_surfaced": _ratio(n("discovery", "relevant_surfaced"), n("discovery", "relevant_eligible")),
            "D2_relevant_missed": _ratio(n("discovery", "relevant_missed"), n("discovery", "relevant_eligible")),
            "D3_irrelevant_surfaced": _ratio(n("discovery", "irrelevant_surfaced"), n("discovery", "surfaced_with_resolved_label")),
            "D4_surfaced_relevance_unknown": _ratio(n("discovery", "surfaced_relevance_unknown"), n("discovery", "surfaced")),
            "D5_requires_verification": _ratio(n("discovery", "requires_verification"), n("discovery", "surfaced")),
            "relevant_blocked_by_authorization": n("discovery", "relevant_blocked"),
            "already_in_active_review": n("discovery", "already_in_active_review"),
        },
        "baseline": {
            "B1_baseline_missed_relevant": _ratio(n("baseline", "baseline_missed_relevant"), n("baseline", "relevant_with_observed_baseline")),
            "B1_inferred_only": n("baseline", "baseline_missed_relevant_inferred"),
            "B2_recovered_by_product": _ratio(n("baseline", "recovered_by_product"), n("baseline", "baseline_missed_relevant")),
            "B3_still_missed_by_product": _ratio(n("baseline", "still_missed_by_product"), n("baseline", "baseline_missed_relevant")),
            "baseline_not_applicable": n("baseline", "baseline_not_applicable"),
            "baseline_unknown": n("baseline", "baseline_unknown"),
        },
        "screening_risks": {
            "F1_confirmed": _ratio(n("screening_risks", "confirmed"), risk_total),
            "F2_rejected": _ratio(n("screening_risks", "rejected"), risk_total),
            "F3_deferred_or_needs_evidence": _ratio(n("screening_risks", "deferred_or_needs_evidence"), risk_total),
            "F4_unresolved": _ratio(n("screening_risks", "unresolved"), risk_total),
            "F5_unreviewed": _ratio(n("screening_risks", "unreviewed"), risk_total),
            "F6_corrections_reveal_relevant": _ratio(n("screening_risks", "corrections_reveal_relevant"), newly_total),
            "F7_corrections_surface_irrelevant": _ratio(n("screening_risks", "corrections_surface_irrelevant"), newly_total),
            "corrections_relevance_unknown": n("screening_risks", "corrections_relevance_unknown"),
            "F8_exclusion_cause_unknown": n("screening_risks", "exclusion_cause_unknown") + n("screening_risks", "simulations_not_evaluable"),
            "F9_without_verified_baseline": _ratio(n("screening_risks", "without_verified_baseline"), risk_total),
            "reviews_for_findings_not_produced": n("screening_risks", "reviews_for_findings_not_produced"),
        },
        "violations": {
            "V1_mandatory": n("violations", "mandatory"),
            "V2_policy": n("violations", "policy"),
            "mandatory_unverified": n("violations", "mandatory_unverified"),
            "occurred": bool(n("violations", "mandatory") or n("violations", "policy")),
        },
        "agreement": {
            "candidates_with_multiple_reviews": sum(c["agreement"]["candidates_with_multiple_reviews"] for c in cases),
            "candidate_agreements": sum(c["agreement"]["candidate_agreements"] for c in cases),
            "candidate_disagreements": sum(len(c["agreement"]["candidate_disagreements"]) for c in cases),
            "candidate_disagreements_adjudicated": sum(1 for c in cases for x in c["agreement"]["candidate_disagreements"] if x["adjudicated"]),
            "findings_with_multiple_reviews": sum(c["agreement"]["findings_with_multiple_reviews"] for c in cases),
            "finding_agreements": sum(c["agreement"]["finding_agreements"] for c in cases),
            "finding_disagreements": sum(len(c["agreement"]["finding_disagreements"]) for c in cases),
            "finding_disagreements_adjudicated": sum(1 for c in cases for x in c["agreement"]["finding_disagreements"] if x["adjudicated"]),
            "blind_candidate_reviews": sum(len(c["agreement"]["blind_candidate_reviews"]) for c in cases),
        },
        "workflow": {
            "W1_cases_with_measured_time": _ratio(len(timed), len(cases)),
            "W1_baseline_minutes": sum(c["workflow"]["baseline_minutes"] for c in timed) if timed else None,
            "W1_assisted_minutes": sum(c["workflow"]["assisted_minutes"] for c in timed) if timed else None,
            "W2_additional_relevant_per_requisition": {c["case_id"]: c["workflow"]["additional_relevant"] for c in obs_cases},
            "W3_review_burden": n("discovery", "irrelevant_surfaced") + n("screening_risks", "corrections_surface_irrelevant")
                                + n("screening_risks", "rejected"),
            "W4_decisions_changed_after_evidence": _ratio(sum(c["workflow"]["decisions_changed_after_evidence"] for c in cases), decs),
            "W5_downstream_observed": sum(len(c["workflow"]["downstream_observed"]) for c in cases),
            "W5_downstream_attributable": sum(len(c["workflow"]["downstream_attributable"]) for c in cases),
            "W5_downstream_not_observed": sum(c["workflow"]["downstream_not_observed"] for c in cases),
        },
    }


def _by_scenario(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for scen in sorted({c["scenario"] for c in cases}):
        cs = [c for c in cases if c["scenario"] == scen]
        resolved = sum(c["label_counts"]["relevant"] + c["label_counts"]["not_relevant"] for c in cs)
        out.append({
            "scenario": scen,
            "cases": [c["case_id"] for c in cs],
            "resolved_labels": resolved,
            "interpretable": resolved >= MIN_LABELS_FOR_INTERPRETATION,
            "relevant_surfaced": sum(len(c["discovery"]["relevant_surfaced"]) for c in cs),
            "relevant_missed": sum(len(c["discovery"]["relevant_missed"]) for c in cs),
            "irrelevant_surfaced": sum(len(c["discovery"]["irrelevant_surfaced"]) for c in cs),
            "baseline_missed_relevant": sum(len(c["baseline"]["baseline_missed_relevant"]) for c in cs),
            "recovered_by_product": sum(len(c["baseline"]["recovered_by_product"]) for c in cs),
            "findings_confirmed": sum(len(c["screening_risks"]["confirmed"]) for c in cs),
            "violations": sum(len(c["violations"]["mandatory"]) + len(c["violations"]["policy"]) for c in cs),
        })
    return out


def _limitations(kind: str, cases: list[dict[str, Any]], m: dict[str, Any]) -> list[str]:
    out = []
    if kind == "synthetic":
        out.append("Synthetic dataset: labels were authored alongside the fixtures. These results test the measurement "
                   "loop and must not be reported as design-partner evidence or real-world accuracy.")
    else:
        out.append("Results describe only these reviewed cases. Reviewer acceptance is not proof of improved hiring outcomes, "
                   "and no outcome is attributed to Screening Assurance unless marked attributable in partner records.")
    labels = m["coverage"]["labels"]
    unknown = labels["unassessable"] + labels["unresolved"] + labels["unreviewed"]
    out.append(f"{unknown} candidate(s) have no resolved relevance label (unassessable, unresolved or unreviewed); "
               "they are excluded from rates and listed, not treated as positive or negative.")
    if m["coverage"]["cases_without_baseline"]:
        out.append("No baseline available for " + ", ".join(m["coverage"]["cases_without_baseline"])
                   + "; baseline comparisons exclude these cases.")
    if m["coverage"]["findings_unreviewed"]:
        out.append(f"{m['coverage']['findings_unreviewed']} screening-risk finding(s) were not reviewed and are never counted as confirmed.")
    small = [s for s in _by_scenario(cases) if s["resolved_labels"] < MIN_LABELS_FOR_INTERPRETATION]
    if small:
        out.append("Sample too small for interpretation (< " + str(MIN_LABELS_FOR_INTERPRETATION) + " resolved labels) in: "
                   + ", ".join(s["scenario"] for s in small) + ".")
    out.append("The product view is a deterministic re-run of the dataset inputs. Simulated corrections are not changes "
               "to the employer's screening process.")
    if any(c["screening_configuration"] != "ats_api_verified" for c in cases):
        out.append("Screening rules come from supplied exports or documentation, not a live ATS audit.")
    return out


# ====================================================================== persistence and comparison
def write_result(result: dict[str, Any], out_root: str | Path) -> tuple[Path, str]:
    """Write result.json and report.md under <out>/<dataset>/<result_id>/. Never overwrites a different result.

    Returns (directory, status) where status is 'written' or 'reproduced'.
    """
    from ..report.validation import render_validation_markdown
    d = Path(out_root) / result["dataset"]["id"] / result["result_id"]
    body = json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    if (d / "result.json").exists():
        existing = (d / "result.json").read_text(encoding="utf-8")
        if existing != body:
            raise ContractError(d, ["an earlier result with the same id differs from this one; refusing to overwrite. "
                                    "Inputs or code changed without a version change — investigate before re-running."])
        return d, "reproduced"
    d.mkdir(parents=True, exist_ok=True)
    (d / "result.json").write_text(body, encoding="utf-8")
    (d / "report.md").write_text(render_validation_markdown(result), encoding="utf-8")
    return d, "written"


def purge_expired_results(out_root: str | Path, today: date | None = None) -> list[str]:
    """Apply dataset retention to stored validation results."""
    import shutil
    today = today or date.today()
    removed = []
    root = Path(out_root)
    if not root.exists():
        return removed
    for res in sorted(root.glob("*/VR-*/result.json")):
        data = json.loads(res.read_text())
        if date.fromisoformat(data["retention"]["delete_after"]) < today:
            shutil.rmtree(res.parent)
            removed.append(res.parent.name)
    return removed


def compare_results(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Compare two measurements (e.g. across engine or knowledge versions) on the same dataset."""
    def flat(m: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in m.items():
            key = f"{prefix}{k}"
            if isinstance(v, dict) and "numerator" in v:
                out[key] = v["numerator"]
            elif isinstance(v, dict):
                out.update(flat(v, key + "."))
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out[key] = v
        return out

    fa, fb = flat(a["metrics"]), flat(b["metrics"])
    deltas = {k: {"a": fa.get(k), "b": fb.get(k)} for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)}
    group_changes = []
    ca = {c["case_id"]: c for c in a["cases"]}
    for c in b["cases"]:
        old = ca.get(c["case_id"])
        if not old:
            continue
        for cid, g in c["product_groups"].items():
            if old["product_groups"].get(cid) != g:
                group_changes.append({"case": c["case_id"], "candidate": cid, "a": old["product_groups"].get(cid), "b": g,
                                      "label": c["labels"].get(cid)})
    warnings = []
    if a["dataset"]["sha256"] != b["dataset"]["sha256"]:
        warnings.append("The two results use different datasets; differences may come from the data, not the product.")
    regressions = []
    for key in ("violations.V1_mandatory", "violations.V2_policy", "discovery.D3_irrelevant_surfaced",
                "screening_risks.F7_corrections_surface_irrelevant", "discovery.D2_relevant_missed"):
        if (fb.get(key) or 0) > (fa.get(key) or 0):
            regressions.append(f"{key} increased {fa.get(key)} -> {fb.get(key)}")
    return {
        "a": {"result_id": a["result_id"], "engine_version": a["engine_version"], "knowledge": a["knowledge"]["fingerprint"],
              "dataset": a["dataset"]},
        "b": {"result_id": b["result_id"], "engine_version": b["engine_version"], "knowledge": b["knowledge"]["fingerprint"],
              "dataset": b["dataset"]},
        "label": b["label"],
        "metric_deltas": deltas,
        "group_changes": group_changes,
        "regressions": regressions,
        "warnings": warnings,
    }
