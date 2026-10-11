"""Design-partner validation: dataset contract, label handling, metrics, violations, reproducibility.

Every dataset here is SYNTHETIC and derived from the Northwind fixtures.
"""

from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from screening_assurance.cli import main
from screening_assurance.contracts import ContractError
from screening_assurance.measure import validation as V
from screening_assurance.measure.validation import (compare_results, load_dataset, measure_dataset,
                                                    purge_expired_results, resolve, write_result)
from screening_assurance.report.validation import render_validation_markdown

from conftest import EXAMPLES, ROOT

DATASET = ROOT / "evals" / "validation" / "northwind-synthetic.yaml"
TODAY = date(2026, 10, 20)
CASE_KEYS = ("requisition", "policy", "candidates", "pool", "decisions")


def raw() -> dict:
    data = yaml.safe_load(DATASET.read_text())
    for c in data["cases"]:
        for k in CASE_KEYS:
            if c.get(k):
                c[k] = str((DATASET.parent / c[k]).resolve())
    return data


def write(tmp_path: Path, data: dict, name: str = "ds.yaml") -> Path:
    p = tmp_path / name
    p.write_text(yaml.safe_dump(data, sort_keys=False))
    return p


def case(data: dict, cid: str) -> dict:
    return next(c for c in data["cases"] if c["case_id"] == cid)


def assessment(c: dict, cand: str) -> dict:
    return next(a for a in c["candidate_assessments"] if a["candidate"] == cand)


def measure(path, pack):
    return measure_dataset(load_dataset(path, today=TODAY), pack)


@pytest.fixture(scope="module")
def result(pack):
    return measure(DATASET, pack)


def cres(result, cid):
    return next(c for c in result["cases"] if c["case_id"] == cid)


# ---------------------------------------------------------------- known labels
def test_known_labels_produce_expected_metrics(result):
    m = result["metrics"]
    assert m["coverage"]["cases"] == 3
    assert m["discovery"]["D1_relevant_surfaced"]["numerator"] == m["discovery"]["D1_relevant_surfaced"]["denominator"] == 15
    assert m["discovery"]["D2_relevant_missed"]["numerator"] == 0
    assert m["discovery"]["D3_irrelevant_surfaced"]["numerator"] == 0
    assert m["baseline"]["B1_baseline_missed_relevant"] == {"numerator": 7, "denominator": 9, "rate": 0.778}
    assert m["baseline"]["B2_recovered_by_product"]["numerator"] == 7
    assert m["screening_risks"]["F1_confirmed"]["numerator"] == 6
    assert m["screening_risks"]["F2_rejected"]["numerator"] == 1
    assert m["violations"] == {"V1_mandatory": 0, "V2_policy": 0, "mandatory_unverified": 2, "occurred": False}
    sre = cres(result, "SRE-0142")
    assert {"C-102", "C-103", "C-110"} <= set(sre["baseline"]["recovered_by_product"])


def test_discovery_and_screening_risk_metrics_are_reported_separately(result):
    assert set(result["metrics"]) >= {"discovery", "baseline", "screening_risks", "violations", "workflow", "agreement"}
    assert "score" not in json.dumps(result["metrics"]).lower()


# ---------------------------------------------------------------- unknown stays unknown
def test_missing_and_unknown_labels_are_never_implied(result):
    sre = cres(result, "SRE-0142")
    assert sre["labels"]["C-112"] == "unreviewed" and sre["labels"]["C-114"] == "unassessable"
    for key in ("relevant_surfaced", "relevant_missed", "irrelevant_surfaced"):
        assert not {"C-112", "C-114", "C-107"} & set(sre["discovery"][key])
    # C-113: relevant, but baseline outcome unknown -> not counted as a baseline miss
    assert "C-113" not in sre["baseline"]["baseline_missed_relevant"] and "C-113" in sre["baseline"]["baseline_unknown"]
    # pool records never applied: no baseline comparison applies
    assert "P-201" in sre["baseline"]["baseline_not_applicable"]
    assert "P-201" not in sre["baseline"]["relevant_with_observed_baseline"]
    # unassessable surfaced record is reported as relevance unknown
    assert "P-205" in sre["discovery"]["surfaced_relevance_unknown"]


def test_blocked_relevant_record_is_not_a_miss(result):
    sre = cres(result, "SRE-0142")
    assert "P-206" in sre["discovery"]["relevant_blocked"] and "P-206" not in sre["discovery"]["relevant_missed"]


def test_unreviewed_findings_are_never_confirmed(result):
    sre = cres(result, "SRE-0142")
    unreviewed = set(sre["screening_risks"]["unreviewed"])
    assert unreviewed and not unreviewed & set(sre["screening_risks"]["confirmed"])
    m = result["metrics"]["screening_risks"]
    assert m["F5_unreviewed"]["denominator"] == m["F1_confirmed"]["denominator"]  # unreviewed stay in the denominator


def test_inferred_baseline_is_reported_apart(pack, tmp_path):
    d = raw()
    c = case(d, "SRE-0142")
    next(o for o in c["baseline"]["observations"] if o["candidate"] == "C-110")["basis"] = "inferred"
    r = measure(write(tmp_path, d), pack)
    s = cres(r, "SRE-0142")["baseline"]
    assert "C-110" in s["baseline_missed_relevant_inferred"] and "C-110" not in s["baseline_missed_relevant"]


# ---------------------------------------------------------------- disagreement and adjudication
def test_reviewer_disagreement_is_preserved(result):
    sre = cres(result, "SRE-0142")
    assert sre["labels"]["C-104"] == "not_relevant"  # adjudicated
    assert sre["labels"]["C-107"] == "unresolved"   # disagreement, no adjudication
    dis = {x["candidate"]: x for x in sre["agreement"]["candidate_disagreements"]}
    assert dis["C-104"]["adjudicated"] and not dis["C-107"]["adjudicated"]
    assert dis["C-107"]["judgments"] == ["not_relevant", "relevant"]
    fd = sre["agreement"]["finding_disagreements"]
    assert fd and fd[0]["adjudicated"] and fd[0]["finding"]["rule"] == "Q2"
    assert "C-107" in sre["unresolved_candidates"]


def test_unresolved_finding_disagreement_is_unknown(pack, tmp_path):
    d = raw()
    fr = next(x for x in case(d, "SRE-0142")["finding_reviews"] if x["finding"].get("rule") == "Q2")
    fr.pop("adjudication")
    r = measure(write(tmp_path, d), pack)
    s = cres(r, "SRE-0142")["screening_risks"]
    assert len(s["unresolved"]) == 1 and s["unresolved"][0] not in s["confirmed"]
    assert r["metrics"]["screening_risks"]["F4_unresolved"]["numerator"] == 1


def test_resolve_rules():
    a = {"reviewer": "A", "judgment": "relevant", "mandatory": "met"}
    b = {"reviewer": "B", "judgment": "not_relevant", "mandatory": "met"}
    assert resolve([], None)["status"] == "unreviewed"
    assert resolve([a], None) == {"status": "single_review", "value": "relevant", "disagreement": False}
    assert resolve([a, b], None)["status"] == "unresolved"
    adj = {"judgment": "relevant", "adjudicator": "X", "rationale": "r", "decided_at": "2026-01-01"}
    assert resolve([a, b], adj)["value"] == "relevant"
    # an adjudication without a mandatory disposition does not resolve the mandatory field
    assert resolve([a, b], adj, "mandatory")["value"] == "met"


# ---------------------------------------------------------------- violations
def test_mandatory_violation_is_reported_individually(pack, tmp_path):
    d = raw()
    for r in assessment(case(d, "SRE-0142"), "C-110")["reviews"]:
        r["mandatory"] = "not_met"
    p = write(tmp_path, d)
    r = measure(p, pack)
    assert r["metrics"]["violations"]["occurred"] is True
    assert any(v.startswith("C-110") for v in cres(r, "SRE-0142")["violations"]["mandatory"])
    assert "Violations occurred" in render_validation_markdown(r)
    assert main(["measure", str(p), "--out", str(tmp_path / "out")]) == 1  # non-zero exit when any violation occurs


def test_policy_violation_from_blocked_record_is_detected(pack, monkeypatch):
    real = V.discover

    def leaky(*a, **kw):
        res = real(*a, **kw)
        for e in res.entries:
            if e.candidate_id == "P-206":
                e.group = "direct"
        return res

    monkeypatch.setattr(V, "discover", leaky)
    r = measure(DATASET, pack)
    assert any("P-206" in v for v in cres(r, "SRE-0142")["violations"]["policy"])
    assert r["metrics"]["violations"]["V2_policy"] >= 1


def test_correction_surfacing_irrelevant_candidate(pack, tmp_path):
    d = raw()
    a = assessment(case(d, "SRE-0142"), "C-110")
    a["reviews"][0]["judgment"] = "not_relevant"
    r = measure(write(tmp_path, d), pack)
    s = cres(r, "SRE-0142")
    assert "C-110" in s["screening_risks"]["corrections_surface_irrelevant"]
    assert "C-110" in s["discovery"]["irrelevant_surfaced"]
    assert r["metrics"]["screening_risks"]["F7_corrections_surface_irrelevant"]["numerator"] == 1
    assert r["metrics"]["workflow"]["W3_review_burden"] == 3  # D3 + F7 + the rejected Q7 finding


def test_findings_without_verified_baseline(result):
    csm = cres(result, "CSM-0388")
    assert csm["baseline"]["baseline_source"] == "not_available"
    assert set(csm["screening_risks"]["without_verified_baseline"]) == {f["finding_id"] for f in csm["screening_risks"]["findings"]}
    assert csm["workflow"]["additional_relevant"] is None
    assert "CSM-0388" not in result["metrics"]["workflow"]["W2_additional_relevant_per_requisition"]


def test_review_for_a_finding_the_product_did_not_produce(pack, tmp_path):
    d = raw()
    case(d, "SRE-0142")["finding_reviews"].append({"finding": {"check": "candidate_review_opportunity", "candidate": "C-104"},
                                                   "reviews": [{"reviewer": "REV-A", "judgment": "confirmed",
                                                                "rationale": "Should have been flagged.", "reviewed_at": "2026-10-14"}]})
    r = measure(write(tmp_path, d), pack)
    assert r["metrics"]["screening_risks"]["reviews_for_findings_not_produced"] == 1


def test_workflow_value_only_where_measured(result):
    w = result["metrics"]["workflow"]
    assert w["W1_cases_with_measured_time"]["numerator"] == 1 and w["W1_baseline_minutes"] == 95
    assert w["W4_decisions_changed_after_evidence"] == {"numerator": 2, "denominator": 3, "rate": 0.667}
    assert w["W5_downstream_observed"] == 1 and w["W5_downstream_attributable"] == 0 and w["W5_downstream_not_observed"] == 1


# ---------------------------------------------------------------- versions, reproducibility, immutability
def test_result_records_versions_and_provenance(result):
    assert result["engine_version"] and result["knowledge"]["fingerprint"].startswith("core@")
    assert result["evaluation_contract"] == V.EVALUATION_VERSION
    c = cres(result, "SRE-0142")
    assert set(c["inputs_sha256"]) == {"requisition", "policy", "candidates", "pool"}
    assert c["policy_version"] and c["screening_rules"] and c["product_run"]["result_sha256"]
    assert cres(result, "CSM-0388")["decisions_snapshot"] == "supplied"


def test_measurement_is_reproducible(pack, tmp_path):
    a, b = measure(DATASET, pack), measure(DATASET, pack)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    out = tmp_path / "out"
    d1, s1 = write_result(a, out)
    d2, s2 = write_result(b, out)
    assert d1 == d2 and (s1, s2) == ("written", "reproduced")
    assert (d1 / "report.md").read_text().startswith("# Validation result")


def test_changed_inputs_never_overwrite_an_earlier_result(pack, tmp_path):
    out = tmp_path / "out"
    first, _ = write_result(measure(DATASET, pack), out)
    d = raw()
    case(d, "SRE-0142")["candidate_assessments"].append({"candidate": "C-112", "reviews": [{
        "reviewer": "REV-A", "judgment": "not_relevant", "mandatory": "met", "rationale": "Unrelated experience.",
        "reviewed_at": "2026-10-16", "saw_product_output": False}]})
    second, status = write_result(measure(write(tmp_path, d), pack), out)
    assert status == "written" and first != second and (first / "result.json").exists()
    # same id but different content (code changed without a version bump) is refused
    tampered = json.loads((first / "result.json").read_text())
    tampered["metrics"]["coverage"]["cases"] = 99
    with pytest.raises(ContractError, match="refusing to overwrite"):
        write_result(tampered, out)


def test_comparison_across_knowledge_versions(pack, pack_100):
    old, new = measure(DATASET, pack_100), measure(DATASET, pack)
    assert old["result_id"] != new["result_id"]
    fwd = compare_results(old, new)
    assert any(g["candidate"] == "P-208" and g["b"] == "direct" and g["label"] == "relevant" for g in fwd["group_changes"])
    assert not fwd["regressions"] and not fwd["warnings"]
    back = compare_results(new, old)
    assert any(r.startswith("discovery.D2_relevant_missed increased") for r in back["regressions"])


def test_comparison_warns_when_datasets_differ(pack, tmp_path):
    d = raw()
    d["source"]["dataset_version"] = "2"
    cmp = compare_results(measure(DATASET, pack), measure(write(tmp_path, d), pack))
    assert cmp["warnings"]


def test_retention_purges_expired_results(pack, tmp_path):
    out = tmp_path / "out"
    d, _ = write_result(measure(DATASET, pack), out)
    assert purge_expired_results(out, today=date(2027, 10, 9)) == []
    assert purge_expired_results(out, today=date(2027, 10, 11)) == [d.name] and not d.exists()


# ---------------------------------------------------------------- rejection of bad or unauthorized data
@pytest.mark.parametrize("mutate,expect", [
    (lambda d: d["authorization"].__setitem__("de_identified", False), "de_identified"),
    (lambda d: d["authorization"].__setitem__("permitted_uses", ["screening_audit"]), "permitted_uses"),
    (lambda d: d.__setitem__("kind", "real_world"), "kind"),
    (lambda d: assessment(case(d, "SRE-0142"), "C-102")["reviews"][0].__setitem__("name", "Jane"), "Additional properties"),
    (lambda d: assessment(case(d, "SRE-0142"), "C-102")["reviews"][0].__setitem__("rationale", "Call her at 555-201-4433"), "phone"),
    (lambda d: assessment(case(d, "SRE-0142"), "C-102")["reviews"][0].__setitem__("rationale", "jane@example.com said yes"), "email"),
    (lambda d: assessment(case(d, "SRE-0142"), "C-102").__setitem__("candidate", "Jane Smith"), "does not match"),
    (lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])), "duplicate case_id"),
    (lambda d: case(d, "SRE-0142")["candidate_assessments"].append(copy.deepcopy(assessment(case(d, "SRE-0142"), "C-102"))), "duplicate candidate_assessments"),
    (lambda d: case(d, "SRE-0142")["baseline"]["observations"].append({"candidate": "C-999", "outcome": "rejected", "basis": "observed"}), "not in the case's candidate inputs"),
    (lambda d: assessment(case(d, "SRE-0142"), "C-104")["adjudication"].__setitem__("judgment", "maybe"), "adjudication"),
    (lambda d: assessment(case(d, "SRE-0142"), "C-104")["reviews"][1].__setitem__("reviewer", "REV-A"), "same reviewer"),
    (lambda d: case(d, "CSM-0388")["baseline"]["observations"].append({"candidate": "C-202", "outcome": "rejected", "basis": "observed"}), "not_available"),
    (lambda d: case(d, "LH-0217").__setitem__("candidates", case(d, "SRE-0142")["candidates"]), "different requisition"),
])
def test_rejects_improper_datasets(tmp_path, mutate, expect):
    d = raw()
    mutate(d)
    with pytest.raises(ContractError) as exc:
        load_dataset(write(tmp_path, d), today=TODAY)
    assert expect in str(exc.value)


def test_rejects_expired_authorization():
    with pytest.raises(ContractError, match="authorization expired"):
        load_dataset(DATASET, today=date(2028, 1, 1))


def test_rejects_pool_not_authorized_for_validation(tmp_path):
    pool = yaml.safe_load((EXAMPLES / "REQ-SRE-0142" / "candidate-pool.yaml").read_text())
    pool["authorization"]["permitted_uses"] = ["screening_audit"]
    pp = tmp_path / "pool.yaml"
    pp.write_text(yaml.safe_dump(pool, sort_keys=False))
    d = raw()
    case(d, "SRE-0142")["pool"] = str(pp)
    with pytest.raises(ContractError, match="not authorized for validation"):
        load_dataset(write(tmp_path, d), today=TODAY)


# ---------------------------------------------------------------- labelling and privacy of results
def test_synthetic_is_never_reported_as_design_partner_evidence(result, pack, tmp_path):
    assert result["label"] == V.SYNTHETIC_LABEL and "SYNTHETIC" in render_validation_markdown(result)
    assert any("must not be reported as design-partner evidence" in x for x in result["limitations"])
    d = raw()
    d["kind"] = "design_partner"
    r = measure(write(tmp_path, d), pack)
    assert r["label"] == V.PARTNER_LABEL and "SYNTHETIC" not in render_validation_markdown(r)
    assert "causation" in r["label"]


def test_results_contain_no_candidate_evidence_or_reviewer_rationale(result):
    text = json.dumps(result)
    cands = yaml.safe_load((EXAMPLES / "REQ-SRE-0142" / "candidates.yaml").read_text())
    evidence = [s for c in cands["candidates"] for s in V._strings({k: c.get(k) for k in ("experience", "skills", "credentials")})
                if isinstance(s, str) and len(s) > 25]
    assert evidence and not [s for s in evidence if s in text]
    assert "Production engineering is the same function" not in text


def test_small_samples_are_flagged(result):
    assert all(not s["interpretable"] for s in result["by_scenario"] if s["resolved_labels"] < V.MIN_LABELS_FOR_INTERPRETATION)
    assert any("Sample too small" in x for x in result["limitations"])


# ---------------------------------------------------------------- CLI
def test_cli_measure_check_and_compare(tmp_path, capsys):
    out = tmp_path / "out"
    assert main(["check", "validation_dataset", str(DATASET)]) == 0
    assert main(["measure", str(DATASET), "--out", str(out)]) == 0
    assert main(["measure", str(DATASET), "--out", str(out)]) == 0
    assert "Reproduced existing" in capsys.readouterr().out
    assert main(["measure", str(DATASET), "--knowledge", "release:1.0.0", "--out", str(out)]) == 0
    results = sorted(out.glob("northwind-synthetic/VR-*/result.json"))
    assert len(results) == 2
    assert main(["measure-compare", str(results[0]), str(results[1]), "--out", str(tmp_path / "cmp.md")]) in (0, 1)
    assert (tmp_path / "cmp.json").exists()
    assert main(["schema", "validation_dataset"]) == 0


def test_same_knowledge_from_a_different_location_reproduces(pack, pack_copy, tmp_path):
    from screening_assurance.knowledge import load_pack
    out = tmp_path / "out"
    d1, _ = write_result(measure(DATASET, pack), out)
    d2, status = write_result(measure(DATASET, load_pack(pack_copy)), out)
    assert d1 == d2 and status == "reproduced"
