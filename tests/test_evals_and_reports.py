import json

import yaml

from screening_assurance.cli import main
from screening_assurance.evals import compare_suites, run_suite
from screening_assurance.knowledge import load_pack
from screening_assurance.report import build_portfolio, render_changes, render_html, render_markdown

from conftest import CASES, EXAMPLES, run


def test_suite_passes_on_current_knowledge(pack):
    s = run_suite(CASES, pack)
    assert s["passed"], s["failures"]
    assert s["metrics"]["false_positives"] == 0
    assert s["metrics"]["guardrail_violations"] == 0


def test_knowledge_upgrade_improves_recall_without_new_false_positives(pack, pack_100):
    cmp = compare_suites(run_suite(CASES, pack_100), run_suite(CASES, pack))
    assert cmp["passed"], cmp["regressions"]
    sre = next(c for c in cmp["cases"] if c["case_id"] == "sre-incident-management")
    assert "C-106" in sre["newly_flagged_candidates"]
    cs = next(c for c in cmp["cases"] if c["case_id"] == "customer-success")
    assert "C-204" in cs["newly_flagged_candidates"]
    assert cmp["metrics"]["delta"]["false_positives"] == 0


def test_regression_gate_catches_a_harmful_knowledge_edit(pack, pack_copy):
    # Treating generic shell scripting as infrastructure-as-code surfaces C-104, whom experts judged unqualified.
    data = yaml.safe_load((pack_copy / "skills.yaml").read_text())
    iac = next(s for s in data["records"] if s["id"] == "skill.infrastructure-as-code")
    iac["alternate_names"].append("Bash")
    (pack_copy / "skills.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    bad = load_pack(pack_copy)
    cmp = compare_suites(run_suite(CASES, pack), run_suite(CASES, bad))
    assert not cmp["passed"]
    assert any("false positives increased" in r for r in cmp["regressions"])


def test_markdown_report_has_all_sections(pack):
    md = render_markdown(run("REQ-SRE-0142", pack, with_feedback=True).as_dict())
    for heading in ("## 1. Requirements and stated intent", "## 2. Screening rules inspected", "## 3. Confirmed inconsistencies",
                    "## 4. Potential missed-talent risks", "## 5. Candidate-review opportunities", "## 6. Recommended changes",
                    "## 7. Human decisions and rationale", "## 8. Outcome measurements"):
        assert heading in md
    assert "What remains unproven" in md and "What the recruiter should verify next" in md
    assert "%" not in md.split("## 5.")[1].split("## 6.")[0], "no match percentages in candidate review"


def test_html_report_is_self_contained_and_escaped(pack):
    res = run("REQ-SRE-0142", pack).as_dict()
    res["findings"][0]["title"] = "<script>alert(1)</script>"
    html = render_html(res)
    assert "<script>alert(1)</script>" not in html
    assert "Export decisions.yaml" in html
    assert "http://" not in html and "https://" not in html.replace("https://example.com", "")


def test_changes_include_only_accepted_findings(pack):
    res = run("REQ-SRE-0142", pack, with_feedback=True).as_dict()
    ch = render_changes(res)
    assert ch["changes"] and all(c["decision"] == "accepted" for c in ch["changes"])
    assert "does not modify ATS configuration" in ch["note"]


def test_portfolio_prioritises_actionable_work(pack):
    results = [run(n, pack).as_dict() for n in ("REQ-SRE-0142", "REQ-CSM-0388", "REQ-LH-0217")]
    p = build_portfolio(results)
    assert p["totals"]["requisitions"] == 3
    assert p["priority_work"][0]["category"] == "confirmed_inconsistency"
    assert any(d["check"] == "literal_term_missing_variants" for d in p["recurring_defects"])


def test_cli_end_to_end(tmp_path, monkeypatch):
    from conftest import ROOT
    monkeypatch.chdir(ROOT)
    assert main(["diagnose", str(EXAMPLES / "REQ-SRE-0142"), "--out", str(tmp_path), "--run-at", "2026-10-11T00:00:00Z"]) == 0
    out = tmp_path / "REQ-SRE-0142"
    assert (out / "report.md").exists() and (out / "report.html").exists()
    data = json.loads((out / "findings.json").read_text())
    assert data["summary"]["by_level"]["level_3"] == 1
    assert main(["knowledge", "validate"]) == 0
    assert main(["eval", "--json"]) == 0
    assert main(["check", "requisition", str(EXAMPLES / "REQ-LH-0217" / "requisition.yaml")]) == 0
