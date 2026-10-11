import csv
import http.client
import io
import json
import shutil
import threading
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from screening_assurance.workbench.server import make_server
from screening_assurance.workbench.workspace import Workspace, WorkbenchError

from conftest import EXAMPLES, ROOT

REVIEWER = "recruiter.lee@northwind.example"


@pytest.fixture
def ws(tmp_path):
    return Workspace(tmp_path / "ws", knowledge_root=ROOT / "knowledge", examples_root=ROOT / "examples",
                     evals_root=ROOT / "evals")


@pytest.fixture
def sre(ws):
    meta = ws.create_session_from_example("REQ-SRE-0142", actor=REVIEWER)
    run = ws.run(meta["id"], "env:production", actor=REVIEWER)
    return ws, meta["id"], run["run_id"]


def _texts(name):
    d = EXAMPLES / name
    out = {"requisition": (d / "requisition.yaml").read_text(), "policy": (ROOT / "examples/northwind/policy.yaml").read_text(),
           "candidates": (d / "candidates.yaml").read_text()}
    if (d / "candidate-pool.yaml").exists():
        out["candidate_pool"] = (d / "candidate-pool.yaml").read_text()
    return out


# ------------------------------------------------------------------ intake and validation
def test_validation_distinguishes_configuration_sources(ws):
    v = ws.validate_inputs(_texts("REQ-CSM-0388"))
    assert v.ok
    s = ws.input_summary(v.data)
    assert s["screening_configuration"] == "recruiter_documentation"
    assert "not verified" in s["screening_configuration_label"]
    assert s["pool"] is None


def test_validation_rejects_bad_inputs(ws):
    t = _texts("REQ-SRE-0142")
    pool = yaml.safe_load(t["candidate_pool"])
    pool["candidates"][0]["full_name"] = "Someone"
    t["candidate_pool"] = yaml.safe_dump(pool)
    v = ws.validate_inputs(t)
    assert not v.ok and next(r for r in v.report if r["kind"] == "candidate_pool")["status"] == "invalid"

    v = ws.validate_inputs({"requisition": _texts("REQ-SRE-0142")["requisition"]})
    assert not v.ok and next(r for r in v.report if r["kind"] == "policy")["status"] == "missing"

    t = _texts("REQ-SRE-0142")
    t["candidates"] = (EXAMPLES / "REQ-CSM-0388" / "candidates.yaml").read_text()
    v = ws.validate_inputs(t)
    assert any("is for requisition" in e for r in v.report for e in r["errors"])

    v = ws.validate_inputs({"requisition": "x: [unclosed", "policy": "{}"})
    assert not v.ok

    big = "# " + "x" * (2 * 1024 * 1024 + 10)
    v = ws.validate_inputs({"requisition": big, "policy": _texts("REQ-SRE-0142")["policy"]})
    assert "limit" in next(r for r in v.report if r["kind"] == "requisition")["errors"][0]

    with pytest.raises(WorkbenchError):
        ws.validate_inputs({"resume.pdf": "x"})


def test_upload_session_matches_example_session(ws):
    meta = ws.create_session(_texts("REQ-SRE-0142"), source="upload", actor=REVIEWER)
    assert meta["retention"]["days"] == 90
    assert set(meta["inputs"]) == {"requisition", "policy", "candidates", "candidate_pool"}


# ------------------------------------------------------------------ runs, decisions, carry-over
def test_run_records_provenance(sre):
    ws, sid, rid = sre
    run = ws.load_run(sid, rid)["run"]
    assert run["knowledge"]["fingerprint"].startswith("core@1.1.0+")
    assert set(run["inputs"]) >= {"requisition", "policy", "candidates", "candidate_pool"}
    assert run["outputs"]["result_sha256"] and run["engine_version"]


def test_decisions_are_validated_and_attributed(sre):
    ws, sid, rid = sre
    res = ws.load_run(sid, rid)["result"]
    unv = next(f for f in res["findings"] if f["check"] == "unverified_necessity")
    with pytest.raises(WorkbenchError):
        ws.record_finding_decision(sid, rid, unv["id"], "accepted", "x", REVIEWER)  # not allowed for this check
    with pytest.raises(WorkbenchError):
        ws.record_finding_decision(sid, rid, unv["id"], "reclassified_preferred", "   ", REVIEWER)  # rationale required
    with pytest.raises(WorkbenchError):
        ws.record_finding_decision(sid, rid, unv["id"], "reclassified_preferred", "ok", "")  # reviewer required
    e = ws.record_finding_decision(sid, rid, unv["id"], "reclassified_preferred", "Industry is a nice-to-have", REVIEWER)
    assert e["decided_by"] == REVIEWER
    audit = (ws.sessions_dir / sid / "audit.jsonl").read_text()
    assert "finding_decision" in audit and "nice-to-have" not in audit  # rationale text not logged


def test_candidate_decisions_only_for_actionable_records(sre):
    ws, sid, rid = sre
    for cid in ("P-206", "P-207", "C-101", "P-204"):
        with pytest.raises(WorkbenchError):
            ws.record_candidate_decision(sid, rid, cid, "review_in_ats", "x", REVIEWER)
    with pytest.raises(WorkbenchError):
        ws.record_candidate_decision(sid, rid, "P-203", "contact_candidate", "x", REVIEWER)
    e = ws.record_candidate_decision(sid, rid, "P-203", "review_in_ats", "Verify automation depth", REVIEWER, 15)
    assert e["review_minutes"] == 15 and e["knowledge"].startswith("core@")


def test_decisions_carry_over_and_stale_ones_are_reported(sre):
    ws, sid, rid = sre
    res = ws.load_run(sid, rid)["result"]
    thr = next(f for f in res["findings"] if f["check"] == "threshold_inconsistency")
    ws.record_finding_decision(sid, rid, thr["id"], "accepted", "Five years is the bar", REVIEWER)
    ws.record_candidate_decision(sid, rid, "P-208", "review_in_ats", "Title variant", REVIEWER)
    again = ws.run(sid, "env:production", actor=REVIEWER)
    assert thr["id"] in again["carried_over"]["finding_decisions_applied"]
    assert "P-208" in again["carried_over"]["candidate_decisions_applied"]
    applied = next(f for f in ws.load_run(sid, again["run_id"])["result"]["findings"] if f["id"] == thr["id"])
    assert applied["disposition"]["status"] == "accepted"
    # Under knowledge 1.0.0, P-208 is no longer surfaced: its decision is kept but reported as stale.
    old = ws.run(sid, "release:1.0.0", actor=REVIEWER)
    assert "P-208" in old["carried_over"]["candidate_decisions_stale"]


def test_prior_run_remains_reproducible_after_knowledge_changes(tmp_path):
    kroot = tmp_path / "knowledge"
    shutil.copytree(ROOT / "knowledge", kroot)
    ws = Workspace(tmp_path / "ws", knowledge_root=kroot, examples_root=ROOT / "examples", evals_root=ROOT / "evals")
    sid = ws.create_session_from_example("REQ-SRE-0142", actor=REVIEWER)["id"]
    first = ws.run(sid, "pack", actor=REVIEWER)
    # A knowledge administrator edits a document in the working pack.
    syn = kroot / "pack" / "synonyms.yaml"
    data = yaml.safe_load(syn.read_text())
    data["records"][0]["variants"].append({"term": "reliability operations engineer", "kind": "variant"})
    syn.write_text(yaml.safe_dump(data, sort_keys=False))
    second = ws.run(sid, "pack", actor=REVIEWER)
    assert second["knowledge"]["fingerprint"] != first["knowledge"]["fingerprint"]
    v = ws.verify_run(sid, first["run_id"])
    assert v["reproduced"], v["checks"]
    # The evaluation suite can be run and compared against production for the edited pack.
    cmp = ws.compare("env:production", "pack")
    assert "Knowledge comparison" in cmp["markdown"] and "SYNTHETIC" in cmp["markdown"]


def test_tampered_inputs_are_detected(sre):
    ws, sid, rid = sre
    p = ws.sessions_dir / sid / "inputs" / "candidate-pool.yaml"
    p.write_text(p.read_text().replace("P-201", "P-299"))
    v = ws.verify_run(sid, rid)
    assert not v["reproduced"]
    with pytest.raises(WorkbenchError):
        ws.run(sid, "env:production", actor=REVIEWER)


def test_retention_deletes_candidate_data(sre):
    ws, sid, rid = sre
    meta_path = ws.sessions_dir / sid / "session.json"
    meta = json.loads(meta_path.read_text())
    meta["retention"]["delete_after"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    meta_path.write_text(json.dumps(meta))
    assert ws.purge_expired() == [sid]
    d = ws.sessions_dir / sid
    assert not (d / "inputs" / "candidate-pool.yaml").exists() and not (d / "runs").exists()
    assert ws.session(sid)["candidate_data_deleted"] is True
    with pytest.raises(WorkbenchError):
        ws.run(sid, "env:production", actor=REVIEWER)


def test_delete_session(sre):
    ws, sid, _ = sre
    ws.delete_session(sid, actor=REVIEWER, reason="test")
    assert not (ws.sessions_dir / sid).exists()
    assert "session_deleted" in (ws.root / "audit.jsonl").read_text()


# ------------------------------------------------------------------ exports
def test_exports(sre):
    ws, sid, rid = sre
    ws.record_candidate_decision(sid, rid, "P-203", "review_in_ats", "=HYPERLINK(\"x\")", REVIEWER)
    data, ctype, name = ws.export(sid, rid, "review-list.csv")
    rows = list(csv.DictReader(io.StringIO(data.decode())))
    ids = {r["candidate_id"] for r in rows}
    assert {"P-201", "P-203", "P-205"} <= ids and not ids & {"P-206", "P-207", "P-209", "P-204", "C-101"}
    p203 = next(r for r in rows if r["candidate_id"] == "P-203")
    assert p203["rationale"].startswith("'=")  # formula injection neutralized
    assert p203["knowledge"].startswith("core@") and p203["run_id"] == rid
    md = ws.export(sid, rid, "report.md")[0].decode()
    assert rid in md and "## Candidate rediscovery" in md and "## 8. Outcome measurements" in md
    z = zipfile.ZipFile(io.BytesIO(ws.export(sid, rid, "bundle.zip")[0]))
    names = set(z.namelist())
    assert {"MANIFEST.json", "review-list.csv", "report.html", "knowledge/manifest.yaml"} <= names
    with pytest.raises(WorkbenchError):
        ws.export(sid, rid, "../../etc/passwd")


def test_identifiers_cannot_escape_workspace(ws):
    for bad in ("../x", "S-../../etc", "x"):
        with pytest.raises(WorkbenchError):
            ws.session(bad)


# ------------------------------------------------------------------ HTTP server safety
@pytest.fixture
def server(ws):
    srv = make_server(ws, "127.0.0.1", 0, quiet=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def call(srv, method, path, body=None, token=True, host=None, ctype="application/json", raw=None):
    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=30)
    headers = {"Host": host or f"127.0.0.1:{srv.server_address[1]}"}
    if token:
        headers["X-SA-Token"] = srv.token
    payload = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if payload is not None:
        headers["Content-Type"] = ctype
    conn.request(method, path, body=payload, headers=headers)
    r = conn.getresponse()
    data = r.read()
    out = (r.status, dict(r.getheaders()), data)
    conn.close()
    return out


def test_refuses_non_loopback_bind(ws):
    with pytest.raises(WorkbenchError):
        make_server(ws, "0.0.0.0", 0)


def test_index_carries_token_and_strict_headers(server):
    status, headers, body = call(server, "GET", "/", token=False)
    assert status == 200 and server.token.encode() in body
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Frame-Options"] == "DENY" and headers["Cache-Control"] == "no-store"


def test_api_requires_token_and_loopback_host(server):
    assert call(server, "GET", "/api/state", token=False)[0] == 403
    assert call(server, "GET", "/api/state", host="evil.example:80")[0] == 403
    assert call(server, "GET", "/api/state")[0] == 200


def test_api_rejects_non_json_and_oversized(server):
    assert call(server, "POST", "/api/validate", raw=b"files=x", ctype="application/x-www-form-urlencoded")[0] == 415
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=30)
    conn.putrequest("POST", "/api/validate", skip_host=True)
    conn.putheader("Host", f"127.0.0.1:{server.server_address[1]}")
    conn.putheader("X-SA-Token", server.token)
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", str(64 * 1024 * 1024))
    conn.endheaders()
    assert conn.getresponse().status == 413  # rejected from the header, before reading the body
    conn.close()


def test_full_workflow_over_http(server):
    st, _, b = call(server, "POST", "/api/sessions", {"example": "REQ-SRE-0142", "actor": REVIEWER})
    assert st == 201
    sid = json.loads(b)["id"]
    st, _, b = call(server, "POST", f"/api/sessions/{sid}/runs", {"knowledge": "env:production", "actor": REVIEWER})
    rid = json.loads(b)["run_id"]
    st, _, b = call(server, "GET", f"/api/sessions/{sid}/runs/{rid}")
    run = json.loads(b)
    assert run["discovery"]["counts"]["transferable"] >= 1
    st, _, b = call(server, "POST", f"/api/sessions/{sid}/runs/{rid}/candidate-decisions",
                    {"candidate_id": "P-203", "disposition": "review_in_ats", "rationale": "verify", "actor": REVIEWER})
    assert st == 201
    st, _, b = call(server, "POST", f"/api/sessions/{sid}/runs/{rid}/candidate-decisions",
                    {"candidate_id": "P-206", "disposition": "review_in_ats", "rationale": "x", "actor": REVIEWER})
    assert st == 400
    st, headers, b = call(server, "GET", f"/api/sessions/{sid}/runs/{rid}/export/review-list.csv")
    assert st == 200 and "attachment" in headers["Content-Disposition"] and b"P-203" in b
    st, _, b = call(server, "POST", f"/api/sessions/{sid}/runs/{rid}/verify", {"actor": REVIEWER})
    assert json.loads(b)["reproduced"] is True
    assert call(server, "GET", f"/api/sessions/{sid}/runs/R-nope")[0] == 404


def test_request_log_contains_no_candidate_evidence(ws, capsys):
    srv = make_server(ws, "127.0.0.1", 0, quiet=False)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        texts = _texts("REQ-SRE-0142")
        call(srv, "POST", "/api/validate", {"files": texts})
    finally:
        srv.shutdown()
        srv.server_close()
    err = capsys.readouterr().err
    assert "/api/validate" in err
    assert "incident commander" not in err and "P-201" not in err
