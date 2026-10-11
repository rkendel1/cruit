"""Recruiter value walkthrough: guided demo, session separation, plain-language summary, decision and export."""

from __future__ import annotations

import json
import threading
import time

import pytest

from screening_assurance.workbench.server import make_server
from screening_assurance.workbench.walkthrough import guide
from screening_assurance.workbench.workspace import Workspace, WorkbenchError, session_mode

from conftest import ROOT
from test_workbench import REVIEWER, _texts, call


@pytest.fixture
def ws(tmp_path):
    return Workspace(tmp_path / "ws", knowledge_root=ROOT / "knowledge", examples_root=ROOT / "examples",
                     evals_root=ROOT / "evals")


@pytest.fixture
def server(ws):
    srv = make_server(ws, "127.0.0.1", 0, quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def demo_run(ws, example="REQ-SRE-0142"):
    out = ws.start_demo(example)
    return out["session_id"], ws.load_run(out["session_id"], out["run_id"])


# ------------------------------------------------------------------ one obvious starting point
def test_demo_runs_from_included_synthetic_data_with_production_knowledge(ws):
    sid, run = demo_run(ws)
    meta = ws.session(sid)
    assert meta["mode"] == "demo" and meta["source"] == "demo:REQ-SRE-0142"
    assert run["run"]["knowledge"]["spec"] == "env:production"
    assert run["run"]["run_by"] == "demo visitor"
    assert "outcomes" not in meta["inputs"]  # no fictional outcome figures in the demo
    assert run["discovery"]["counts"]["transferable"] >= 1


def test_demo_only_offers_samples_that_support_the_full_journey(ws):
    ids = {e["id"] for e in ws.demo_examples()}
    assert "REQ-SRE-0142" in ids and "REQ-RO-0455" not in ids  # requisition-only sample has no candidates
    with pytest.raises(WorkbenchError):
        ws.start_demo("REQ-RO-0455")
    with pytest.raises(WorkbenchError):
        ws.start_demo("../../etc")


def test_demo_and_real_sessions_are_kept_apart(ws):
    sid, _ = demo_run(ws)
    real = ws.create_session(_texts("REQ-SRE-0142"), source="upload", actor=REVIEWER)
    ex = ws.create_session_from_example("REQ-LH-0217", actor=REVIEWER)
    modes = {s["id"]: s["mode"] for s in ws.sessions()}
    assert modes == {sid: "demo", real["id"]: "real", ex["id"]: "demo"}
    assert session_mode("upload") == "real" and session_mode("example:X") == "demo"
    # the same sample content uploaded by a recruiter is a real session; it is never relabelled as a demo
    assert ws.session(real["id"])["mode"] == "real"


# ------------------------------------------------------------------ lead with the value delivered
def test_summary_answers_what_we_might_be_missing(ws):
    _, run = demo_run(ws)
    s = guide(run["result"], run["discovery"])["summary"]
    c = run["discovery"]["counts"]
    assert s["surfaced"] == c["direct"] + c["transferable"] + c["insufficient"]
    assert {"C-103", "C-110"} <= set(s["excluded_by_supplied_rules"])
    assert s["corrections_simulated"] >= 1 and s["newly_eligible_any_correction"]
    assert s["top_rule_risks"][0]["newly_eligible"]
    # unknowns stay unknown: unexplained exclusions are reported, never counted as candidates to recover
    assert set(s["unexplained_exclusions"]) == {"C-113", "C-114"}
    assert not set(s["unexplained_exclusions"]) & set(s["newly_eligible_any_correction"])
    text = json.dumps(s).lower()
    assert "score" not in text and "qualified" not in text and "%" not in text


def test_tour_picks_a_candidate_and_the_rule_that_kept_them_out(ws):
    _, run = demo_run(ws)
    t = guide(run["result"], run["discovery"])["tour"]
    f = next(x for x in run["result"]["findings"] if x["id"] == t["finding_id"])
    e = next(x for x in run["discovery"]["entries"] if x["candidate_id"] == t["candidate_id"])
    assert e["group"] == "transferable" and e["screening"]["excluded_by"]   # rejected, evidence needs verifying
    assert not f.get("candidate_id") and f["rule_id"]                      # rule-level, not candidate-specific
    assert t["candidate_id"] in f["simulation"]["categories"]["newly_eligible_for_review"]
    assert t["finding_has_correction"] and f["simulation"]["evaluable"]


def test_mandatory_requirements_stay_protected_in_the_walkthrough(ws):
    _, run = demo_run(ws, "REQ-LH-0217")
    g = guide(run["result"], run["discovery"])
    assert g["summary"]["protected_requirements"] == ["Q1"]
    f = next(x for x in run["result"]["findings"] if x["id"] == g["tour"]["finding_id"])
    cats = f["simulation"]["categories"]
    assert not set(cats["newly_eligible_for_review"]) & set(cats["still_fail_mandatory_requirement"])
    assert "C-302" not in g["summary"]["newly_eligible_any_correction"]  # lacks the legally required licence


def test_empty_state_without_candidate_evidence(ws):
    meta = ws.create_session_from_example("REQ-RO-0455", actor=REVIEWER)
    r = ws.run(meta["id"], "env:production", actor=REVIEWER)
    run = ws.load_run(meta["id"], r["run_id"])
    g = guide(run["result"], run["discovery"])
    assert g["summary"]["candidates_considered"] == 0 and g["summary"]["surfaced"] == 0
    assert g["tour"]["candidate_id"] is None


# ------------------------------------------------------------------ the whole journey over HTTP
def test_guided_journey_over_http(server):
    st, _, b = call(server, "POST", "/api/demo", {})
    assert st == 201
    out = json.loads(b)
    sid, rid = out["session_id"], out["run_id"]
    st, _, b = call(server, "GET", "/api/state")
    state = json.loads(b)
    assert state["default_demo"] == "REQ-SRE-0142" and [s["mode"] for s in state["sessions"]] == ["demo"]
    run = json.loads(call(server, "GET", f"/api/sessions/{sid}/runs/{rid}")[2])
    fid = run["guide"]["tour"]["finding_id"]
    inputs_before = json.loads(call(server, "GET", f"/api/sessions/{sid}")[2])["inputs"]

    # step 5: a human decision needs a rationale and a name
    assert call(server, "POST", f"/api/sessions/{sid}/runs/{rid}/finding-decisions",
                {"finding_id": fid, "disposition": "accepted", "rationale": "", "actor": REVIEWER})[0] == 400
    assert call(server, "POST", f"/api/sessions/{sid}/runs/{rid}/finding-decisions",
                {"finding_id": fid, "disposition": "accepted", "rationale": "R1 accepts it", "actor": ""})[0] == 400
    st, _, b = call(server, "POST", f"/api/sessions/{sid}/runs/{rid}/finding-decisions",
                    {"finding_id": fid, "disposition": "accepted", "rationale": "R1 accepts production operations", "actor": REVIEWER})
    assert st == 201

    # step 6: the decision is linked to its run and inputs, and appears in the exports
    sess = json.loads(call(server, "GET", f"/api/sessions/{sid}")[2])
    h = sess["decision_history"][-1]
    assert h["id"] == fid and h["run_id"] == rid and h["decided_by"] == REVIEWER and h["inputs_sha256"]
    st, _, b = call(server, "GET", f"/api/sessions/{sid}/runs/{rid}/export/decision-history.jsonl")
    assert st == 200 and fid.encode() in b
    st, _, b = call(server, "GET", f"/api/sessions/{sid}/runs/{rid}/export/review-list.csv")
    assert st == 200 and b"C-103" in b
    st, _, b = call(server, "GET", f"/api/sessions/{sid}/runs/{rid}/export/screening-risks.yaml")
    assert st == 200 and b"R1 accepts production operations" in b

    # updating the analysis applies the decision; supplied inputs are unchanged (corrections are never applied)
    st, _, b = call(server, "POST", f"/api/sessions/{sid}/runs", {"knowledge": "env:production", "actor": REVIEWER})
    assert fid in json.loads(b)["carried_over"]["finding_decisions_applied"]
    assert json.loads(call(server, "GET", f"/api/sessions/{sid}")[2])["inputs"] == inputs_before


def test_demo_endpoint_errors_and_security(server):
    assert call(server, "POST", "/api/demo", {}, token=False)[0] == 403
    assert call(server, "POST", "/api/demo", {}, host="evil.example")[0] == 403
    st, _, b = call(server, "POST", "/api/demo", {"example": "REQ-RO-0455"})
    assert st == 404 and "guided demo" in json.loads(b)["error"]


def test_validation_sample_is_labelled_synthetic(server):
    st, _, b = call(server, "GET", "/api/validation-sample")
    v = json.loads(b)
    assert st == 200 and v["kind"] == "synthetic" and v["label"].startswith("SYNTHETIC")
    assert "real-world" in v["label"] and v["metrics"]["F1_confirmed"]["denominator"] > 0
    assert any("must not be reported as design-partner evidence" in x for x in v["limitations"])
    assert call(server, "GET", "/api/validation-sample", token=False)[0] == 403


def test_ui_renders_data_safely_and_keeps_labels_plain():
    js = (ROOT / "src/screening_assurance/workbench/static/app.js").read_text()
    assert ".innerHTML" not in js and "eval(" not in js
    for phrase in ("Try the guided demo", "Review my requisition", "What might we be missing for this role?",
                   "Observed", "Simulated", "Needs verification", "Protected requirement", "not a live ATS audit"):
        assert phrase in js
    html = (ROOT / "src/screening_assurance/workbench/static/index.html").read_text()
    assert "style=" not in html and "<script>" not in html  # CSP: no inline styles or scripts


# ------------------------------------------------------------------ in a real browser (skipped where unavailable)
def test_walkthrough_in_a_browser(server, tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - no browser installed in this environment
            pytest.skip(f"chromium unavailable: {exc}")
        errors: list[str] = []
        pg = b.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(server.url)
        pg.get_by_role("button", name="Start the guided demo").click()
        pg.wait_for_selector("text=What might we be missing for this role?")
        for nxt in ("Start: understand the role →", "Next: discover candidates →", "Next: inspect a screening risk →",
                    "Next: compare the correction →", "Next: make a human decision →"):
            pg.get_by_role("button", name=nxt).click()
            time.sleep(0.1)
        pg.get_by_role("button", name="← Back").click()
        pg.wait_for_selector("text=Before and after")
        pg.get_by_role("button", name="Next: make a human decision →").click()
        pg.select_option(".decision select", "accepted")
        pg.fill(".decision textarea", "The posting accepts production operations.")
        pg.fill(".decision .name-input", "Lee Morgan")
        pg.get_by_role("button", name="Record decision").click()
        pg.wait_for_selector("text=Recorded decision")
        with pg.expect_download() as dl:
            pg.get_by_role("button", name="Download candidate review list").click()
        assert dl.value.suggested_filename.endswith("review-list.csv")
        pg.get_by_role("button", name="Explore this sample on my own").click()
        pg.wait_for_selector("text=Resume guided tour")
        pg.get_by_role("button", name="Leave demo").click()
        pg.wait_for_selector("text=Previous demo sessions")
        b.close()
    assert not errors
